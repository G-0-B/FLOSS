"""Shared daemon bootstrap for FLOSSIØULLK Python MCP servers.

Converts per-client stdio spawns into one persistent PID-guarded HTTP daemon.
Bind 127.0.0.1 ONLY (native Windows; never expose to the network). Carries the
former JanuScope lens instruction injection (passed into FastMCP) and appends a
per-tool-call audit line to the same janus-*-audit.jsonl sink the lens used.

This module is transport-only — it does not touch consensus/ensemble domain logic.
"""

from __future__ import annotations

import atexit
import functools
import inspect
import json
import os
import signal
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# A blank reservation older than this is a launcher that died between
# --reserve-slot and --record-identity. Deliberately far longer than the
# milliseconds a real launcher needs in between, because the failure modes are
# asymmetric: reclaiming too early starts a duplicate daemon on a bound port,
# while reclaiming too late costs one more run.
_RESERVATION_STALE_SECONDS = 60.0

# How long any claim transition waits for another one to finish. Short: a
# daemon that cannot claim its slot must fail fast rather than hang at
# startup, and a shutdown must never block on it at all.
_CLAIM_GUARD_SECONDS = 5.0


# A reservation carries a unique token so two of them are never identical.
#
# --reserve-slot used to write an EMPTY file, which made every reservation
# byte-identical -- and identity by (st_dev, st_ino) does not save it, because
# inode numbers are RECYCLED: on ext4 a reservation reclaimed and immediately
# recreated at the same path gets the same inode, so a loser comparing what it
# inspected found both the identity and the (empty) contents equal and deleted
# the winner's reservation. Windows does not reuse the index that eagerly,
# which is why this only ever failed on Linux.
#
# A token in the file makes two reservations distinguishable by construction,
# which no filesystem property can undo.
_RESERVATION_MARKER = "RESERVED"


class ClaimUnavailable(RuntimeError):
    """The slot could not be judged, as distinct from being occupied.

    claim_singleton returns False for "someone else holds this", and the
    OSError/ImportError paths returned the same False -- so a missing shared
    helper or an unwritable agent directory was indistinguishable from a
    healthy running daemon. run_http_daemon then printed "already running" and
    exited 0, and the PowerShell launcher reads a clean exit as a live daemon,
    so the startup summary reported success with the port unserved. An
    infrastructure failure has to be able to say so.
    """


def _reservation_token() -> str:
    """A value no other reservation will carry."""

    import base64

    return base64.urlsafe_b64encode(os.urandom(12)).decode("ascii").rstrip("=")


def _is_reservation(raw: str) -> bool:
    """True for a slot claimed but not yet recorded.

    Empty counts, and must: claim_singleton creates its pid file with O_EXCL
    and writes the pid immediately after, so a concurrent reader can see it
    empty in between, and reservations written before the marker existed are
    empty on disk.
    """

    return raw == "" or raw.startswith(_RESERVATION_MARKER)


def _reservation_token_of(raw: str):
    """The token carried by a marked reservation, or None if it carries none.

    None means "this claim cannot prove which launcher made it": either it is
    not a reservation at all, or it is one of the empty pre-marker
    reservations. Both are the states --record-identity is allowed to overwrite
    unconditionally, which is why they share a return value here.
    """

    if not raw.startswith(_RESERVATION_MARKER):
        return None
    rest = raw[len(_RESERVATION_MARKER) :].strip()
    return rest or None


@contextmanager
def _claim_guard(pid_path: Path, *, timeout_seconds: float | None = None):
    """Hold the shared mutation guard across a whole claim transition.

    Every mutation here is really a PAIR -- an identity sidecar and the claim
    beside it -- and each half was snapshotted at the moment it was about to be
    touched rather than with the other. A contender replacing the record in
    between got its sidecar deleted by a caller that then discovered it was not
    allowed to touch the claim, leaving a live daemon whose --check-identity
    returns UNKNOWN and which both scripts refuse to manage.

    Fails CLOSED. Without the shared helper there is no way to serialise the
    pair, and proceeding unserialised is how the sidecar gets deleted out from
    under a live owner, so the transition does not happen at all.
    """

    from packages.activity_log.filelock import guarded

    with guarded(pid_path, timeout_seconds=timeout_seconds):
        yield


def _inspect_claim(path: Path):
    """Capture identity + contents so a later reclaim can prove it is the same.

    Bytes alone cannot tell two blank reservations apart, and blank is exactly
    what --reserve-slot writes: two launchers inspecting one abandoned empty
    claim would both reclaim, because both files contained b"". Delegates so
    there is one definition of what "the same instance" means.
    """

    try:
        from packages.activity_log.filelock import inspect_for_reclaim

        return inspect_for_reclaim(path)
    except ImportError:
        return None


def _reclaim_claim_if_unchanged(pid_path: Path, observed) -> bool:
    """Remove a claim only if it is still the file the checks inspected.

    Delegates to the shared filelock implementation rather than growing a third
    copy of rename-then-verify here. Falls back to a plain unlink only if that
    module cannot be imported, which keeps the daemon runnable on its own.
    """

    try:
        from packages.activity_log.filelock import reclaim_if_unchanged
    except ImportError:
        # FAIL CLOSED. The fallback used to unlink by pathname, which is the
        # exact removal every caller here was changed to stop doing -- and
        # applied to the identity sidecar it deletes a replacement's token. A
        # daemon that cannot import a stdlib-only module from its own tree is a
        # broken install, and refusing to reclaim leaves a stale record for an
        # operator to clear; deleting the wrong one cannot be undone.
        return False
    return reclaim_if_unchanged(pid_path, observed)


# Distinguishes "no sidecar was there when we looked" from "there was one we
# could not read". Both used to arrive as None and had to be pulled apart twice.
_SIDECAR_ABSENT = object()


def _inspect_sidecar(pid_path: Path):
    """Snapshot the sidecar at the SAME instant as the claim it belongs to.

    Returns _SIDECAR_ABSENT if nothing was there, None if something was there
    and could not be read, otherwise an Inspection.
    """

    sidecar = _identity_path(pid_path)
    # EXISTENCE IS lstat's QUESTION. A read failing with FileNotFoundError does
    # not prove the path is empty: a dangling symlink is a directory entry
    # whose target is missing and raises exactly that.
    try:
        sidecar.lstat()
    except FileNotFoundError:
        return _SIDECAR_ABSENT
    except OSError:
        return None
    return _inspect_claim(sidecar)


def _sidecar_cleared(pid_path: Path, seen) -> bool:
    """True when the sidecar belonging to the INSPECTED claim is gone.

    `seen` is what the caller saw at the moment it snapshotted the claim, and
    the removal is bound to it. Re-inspecting instead -- asking what sidecar
    exists NOW -- deleted a replacement's live identity: a launcher that took
    the freed slot after our snapshot wrote its own token, this removed it, and
    then the claim reclaim correctly refused. The daemon stayed alive with no
    identity, --check-identity returned UNKNOWN, and the stop script would not
    manage it.

    So the three answers are about what we SAW, not about what is there:

      * nothing was there -- nothing of ours to clear. If something is there
        now it is someone else's, and freeing the slot under it is the
        non-conservative failure this file keeps warning about.
      * something was there we could not read -- we cannot tell whose it is.
      * something we inspected -- remove exactly that instance, or nothing.
    """

    sidecar = _identity_path(pid_path)
    if seen is _SIDECAR_ABSENT:
        try:
            sidecar.lstat()
        except FileNotFoundError:
            return True
        except OSError:
            return False
        # Appeared since we looked: a replacement's, not ours.
        return False
    if seen is None:
        return False
    return _reclaim_claim_if_unchanged(sidecar, seen)


def _blank_claim_is_stale(pid_path: Path) -> bool:
    """True when an empty claim file is old enough to be a crashed reserver."""

    try:
        age = time.time() - pid_path.stat().st_mtime
    except OSError:
        return False
    return age >= _RESERVATION_STALE_SECONDS


def _pid_alive(pid: int) -> bool:
    """Return True if `pid` is a running process.

    On Windows, ``os.kill(pid, 0)`` is unreliable (raises WinError 87 or
    SystemError for various PID values). We use ``ctypes.OpenProcess`` with
    a zero access mask — it succeeds if the process exists (even if owned by
    another user) and fails with ERROR_INVALID_PARAMETER (87) if the PID
    is not in use.
    """
    if pid <= 0:
        return False
    if sys.platform == "win32":
        import ctypes

        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            # OpenProcess SUCCEEDING IS NOT LIVENESS. A terminated process
            # remains openable while any handle to it persists, so this returned
            # True for daemons that had already exited -- measured: kill a
            # process, reap it, and OpenProcess still hands back a handle whose
            # GetExitCodeProcess reports the real exit code rather than
            # STILL_ACTIVE. claim_singleton then reported "already running" when
            # nothing was, permanently, and --check-identity said OURS about a
            # corpse.
            #
            # A live process can legitimately exit with 259 later, which would
            # read as alive here. That is the documented ambiguity of this API
            # and it errs toward "alive", which is the conservative direction
            # for a singleton guard.
            STILL_ACTIVE = 259
            code = ctypes.c_ulong()
            got = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            kernel32.CloseHandle(handle)
            if not got:
                return True  # cannot tell; stay conservative
            return code.value == STILL_ACTIVE
        # ERROR_INVALID_PARAMETER (87) = PID not in use
        # ERROR_ACCESS_DENIED (5) = exists but owned by another user
        err = kernel32.GetLastError()
        return err == 5  # access denied means it exists
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except ValueError:
        return False
    except PermissionError:
        return True  # exists, owned by someone else
    except (OSError, SystemError):
        return False


def _process_start_token(pid: int) -> str | None:
    """Return a stable per-PID process-creation token, or None if unavailable.

    A PID alone does not identify a process. After a crash or a reboot the PID
    file survives, the OS reassigns that number to something unrelated, and
    `_pid_alive()` then reports the daemon as running while port 7331/7332 goes
    unserved -- the launcher exits successfully and the stop script is aimed at
    an innocent process.

    Process creation time is the standard disambiguator and needs no new
    dependency: GetProcessTimes on Windows, field 22 of /proc/<pid>/stat on
    Linux. Anywhere else this returns None, and the caller keeps the old
    conservative behaviour rather than guessing.
    """

    if pid <= 0:
        return None
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            creation = wintypes.FILETIME()
            exited = wintypes.FILETIME()
            kernel = wintypes.FILETIME()
            user = wintypes.FILETIME()
            ok = kernel32.GetProcessTimes(
                handle,
                ctypes.byref(creation),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            )
            if not ok:
                return None
            return f"{creation.dwHighDateTime}:{creation.dwLowDateTime}"
        finally:
            kernel32.CloseHandle(handle)
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return None
    # The comm field is parenthesised and may itself contain spaces and
    # parens, so split after its LAST ')' rather than tokenising the whole
    # line. starttime is field 22 overall, i.e. index 19 of what follows.
    try:
        fields = stat[stat.rindex(")") + 1 :].split()
        return fields[19]
    except (ValueError, IndexError):
        return None


def _identity_path(pid_path: Path) -> Path:
    """Sidecar holding the holder's creation token.

    Deliberately a sidecar rather than a richer PID-file format: the PID file
    is read by scripts/start_mcp_daemons.ps1 and by existing callers that
    expect a bare integer, and changing that format to carry identity would
    break them for a guard they do not use.
    """

    return pid_path.with_name(pid_path.name + ".identity")


def _holder_is_really_ours(pid_path: Path, pid: int) -> bool:
    """True unless we can PROVE the live PID is a different process.

    Unverifiable cases -- a legacy PID file with no sidecar, an unsupported
    platform, a process we cannot open -- deliberately return True and keep the
    old blocking behaviour. A false "stale" verdict starts a second daemon on a
    bound port, which is worse than a false "live" verdict that a human can
    clear by deleting the file.
    """

    try:
        recorded = _identity_path(pid_path).read_text(encoding="utf-8").strip()
    except OSError:
        return True
    if not recorded:
        return True
    current = _process_start_token(pid)
    if current is None:
        return True
    return current == recorded


def claim_singleton(pid_filename: str) -> bool:
    """Return True if this process now owns the daemon slot, False if one is live.

    Writes a PID file under ``FLOSS_AGENT_DIR`` (default ``~/.floss_agent``).
    Stale PID files (dead process) are overwritten. Live PID files block.
    Registers atexit + signal handlers to clean up the PID file on exit.
    """
    pid_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_path = pid_dir / pid_filename
    me = os.getpid()

    # Claimed with O_CREAT|O_EXCL rather than exists()-then-write. The old
    # check-then-write left a window where two launchers both saw no live PID,
    # both wrote, and both proceeded; one then lost the port bind and its
    # atexit handler deleted the SURVIVOR's pid file, so duplicate prevention
    # was defeated for every later start too. O_EXCL makes exactly one creator
    # win at the filesystem level.
    # UNDER THE SAME GUARD AS EVERY OTHER MUTATION OF THIS PATH.
    #
    # This creator sat outside the guard added for the reclaimers, which makes
    # the guard not mutual exclusion but a convention half the writers follow.
    # A reclaimer that inspected an old claim could have it replaced here, move
    # the LIVE replacement aside, and lose it to a rollback that could not get
    # the pathname back. Taken with a short budget because a daemon that cannot
    # claim its slot must fail fast rather than hang at startup.
    try:
        with _claim_guard(pid_path, timeout_seconds=_CLAIM_GUARD_SECONDS):
            claimed = _claim_singleton_guarded(pid_path, me)
    except TimeoutError:
        # Someone is mid-transition on this slot. Occupied is the conservative
        # reading and the one that prevents a duplicate daemon, and it is a
        # genuine occupancy answer rather than a failure to produce one.
        return False
    except ImportError as exc:
        raise ClaimUnavailable(
            f"the shared file-lock helper is unavailable ({exc}); the slot for "
            f"{pid_path} cannot be claimed or judged"
        ) from exc
    except OSError as exc:
        raise ClaimUnavailable(
            f"the slot for {pid_path} could not be claimed "
            f"({type(exc).__name__}: {exc})"
        ) from exc
    if not claimed:
        return False

    def _release() -> None:
        """Remove the pid file only while it still names this process.

        Unconditional unlink is what let a losing racer delete the winner's
        claim.
        """
        try:
            with _claim_guard(pid_path, timeout_seconds=_CLAIM_GUARD_SECONDS):
                _release_guarded(pid_path, me)
        except (TimeoutError, OSError, ImportError, ValueError):
            # Leaving the record is the conservative failure: it blocks the
            # next start rather than freeing a slot we may not own. Never hang
            # a shutdown on it.
            pass

    atexit.register(_release)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (_release(), sys.exit(0)))
    return True


def _release_guarded(pid_path: Path, me: int) -> None:
    # Identity captured with the contents, so the reclaims below prove
    # they are removing the same files this ownership test read.
    mine = _inspect_claim(pid_path)
    identity_seen = _inspect_claim(_identity_path(pid_path))
    if mine is None or mine.data.decode("utf-8", "replace").strip() != str(me):
        return
    # SIDECAR FIRST, exactly as the stale-reclaim path does. Unlinking the
    # PID file first opens a window in which a replacement launcher claims
    # the freed slot and writes ITS identity -- which this callback then
    # deletes. The replacement stays alive but unverifiable, so the stop
    # script refuses to terminate it and every later launch stays blocked.
    _reclaim_claim_if_unchanged(_identity_path(pid_path), identity_seen)
    _reclaim_claim_if_unchanged(pid_path, mine)


def _claim_singleton_guarded(pid_path: Path, me: int) -> bool:
    claimed = False
    for _ in range(5):
        try:
            fd = os.open(pid_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raw = ""
            # Captured before every check below, so the reclaim can prove it is
            # removing the same claim those checks inspected.
            try:
                observed = _inspect_claim(pid_path)
                observed_sidecar = _inspect_sidecar(pid_path)
            except OSError:
                observed = None
            try:
                raw = pid_path.read_text(encoding="utf-8").strip()
            except OSError:
                raw = ""
            if _is_reservation(raw):
                # A RESERVATION IS AN IN-PROGRESS CLAIM, NOT A STALE ONE.
                #
                # O_EXCL creates the file before its PID is written, so a second
                # launcher can read it in that window. Converting the empty read
                # to -1 made it "stale", so the second launcher unlinked the
                # FIRST launcher's valid claim and both returned success --
                # defeating the guarantee O_EXCL was introduced to provide. The
                # one that later loses the port bind then removes the survivor's
                # record on exit, leaving a live daemon untracked.
                #
                # Wait for the writer instead of reclaiming from it. Still
                # blank after that is a crashed writer, and the stale-reclaim
                # path below handles it on a later pass.
                time.sleep(0.05)
                try:
                    raw = pid_path.read_text(encoding="utf-8").strip()
                except OSError:
                    raw = ""
                if _is_reservation(raw):
                    # A RESERVATION THAT IS OLD IS A CRASHED RESERVER.
                    #
                    # The comment above says the stale path "handles it on a
                    # later pass". It does not -- this returned False, so the
                    # reclaim below was never reached and a blank file blocked
                    # the slot forever. --reserve-slot made that reachable in
                    # normal operation: it creates the file empty and leaves it
                    # empty until --record-identity runs, so a launcher killed
                    # in between disabled the daemon until a human deleted the
                    # file by hand.
                    #
                    # Age is the only signal available with no PID to probe, and
                    # it must stay long enough that a live reserver is never
                    # mistaken for a dead one: a FRESH blank file still blocks,
                    # which is the property the wait above was added to protect.
                    if _blank_claim_is_stale(pid_path):
                        # THE SIDECAR GOES FIRST AGAIN -- but content-checked.
                        #
                        # Taking it after a successful reclaim still had a
                        # window: the pid file is free the instant we rename it
                        # aside, so a new claimant can appear and write ITS
                        # identity before our unlink lands, and we delete
                        # theirs. Taking it first was the original order and was
                        # only unsafe because it deleted by pathname. Routed
                        # through the same instance check, it is safe in both
                        # directions: we only ever remove the sidecar we
                        # inspected, and a winner's fresh one is left alone.
                        if not _sidecar_cleared(pid_path, observed_sidecar):
                            # Someone else's identity, or one we cannot read.
                            # Freeing the slot under it is the dangerous half.
                            continue
                        _reclaim_claim_if_unchanged(pid_path, observed)
                        continue
                    return False
            try:
                existing = int(raw)
            except ValueError:
                existing = -1
            # A live holder blocks us even when that holder is THIS process: a
            # second claim on one slot means a double-start, and reporting
            # success for it would defeat the very guarantee this function
            # exists to provide (see test_live_pid_blocks_second_claim).
            if _pid_alive(existing) and _holder_is_really_ours(pid_path, existing):
                return False
            # Stale holder: drop it and race for the exclusive create again
            # rather than overwriting, so a concurrent launcher that wins the
            # retry still blocks us instead of both proceeding.
            #
            # THE SIDECAR GOES FIRST. Unlinking only the PID file leaves the old
            # identity token on disk, and the window between the two unlinks is
            # exploitable: launcher A wins the exclusive create and writes its
            # new PID, launcher B still sees the STALE token beside it, judges
            # A's valid claim stale, unlinks it, and claims the slot too. Both
            # then return success and race for the same port. Removing the
            # identity first means the worst case is an unverifiable holder,
            # which blocks, rather than a mismatched one, which does not.
            #
            # BY INSTANCE, not by pathname. Two launchers can both judge the
            # same stale claim dead; the first unlinks and recreates it, and the
            # second then deletes THAT -- so both return success and both start
            # a daemon on one port. The rename is the atomic part: exactly one
            # caller moves a given file aside and the rest retry.
            #
            # Sidecar first and content-checked, as in the blank branch above:
            # after the pid file is renamed aside the slot is free, so a taker
            # can write its identity before our unlink would land.
            if not _sidecar_cleared(pid_path, observed_sidecar):
                continue
            _reclaim_claim_if_unchanged(pid_path, observed)
            continue
        else:
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(str(me))
                token = _process_start_token(me)
                if token:
                    _identity_path(pid_path).write_text(token, encoding="utf-8")
                else:
                    # No token means the next claimant cannot disprove us, so
                    # leave no stale sidecar from a previous holder behind to
                    # be compared against the wrong process.
                    try:
                        _identity_path(pid_path).unlink(missing_ok=True)
                    except OSError:
                        pass
            except OSError:
                try:
                    pid_path.unlink(missing_ok=True)
                except OSError:
                    pass
                return False
            claimed = True
            break
    return claimed


def audit_appender(sink: str):
    """Return callable(tool_name, payload) that appends one JSONL audit line.

    Audit is best-effort defense-in-depth — it must never raise.
    """
    sink_path = Path(sink)

    def _append(tool_name: str, payload: dict) -> None:
        try:
            sink_path.parent.mkdir(parents=True, exist_ok=True)
            row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "tool": tool_name,
                "payload": payload,
            }
            with sink_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass  # audit is best-effort, never fatal

    return _append


_AUDIT_VALUE_MAX_CHARS = 500


def _safe_payload(func, args: tuple, kwargs: dict) -> dict:
    """Render one call's arguments as a bounded, JSON-safe dict.

    Binds positional args to their parameter names so the audit row is readable
    regardless of how the caller invoked the tool, and truncates every value so
    a large Claim body cannot turn the audit sink into a copy of the source
    chain. Never raises: an unbindable signature or an unrepresentable value
    degrades to a marker rather than losing the audit line entirely.
    """

    def clip(v):
        try:
            s = v if isinstance(v, (str, int, float, bool, type(None))) else repr(v)
        except Exception:  # noqa: BLE001 - a hostile __repr__ must not break audit
            return "<unrepresentable>"
        if isinstance(s, str) and len(s) > _AUDIT_VALUE_MAX_CHARS:
            return s[:_AUDIT_VALUE_MAX_CHARS] + "…<truncated>"
        return s

    try:
        bound = inspect.signature(func).bind_partial(*args, **kwargs)
        return {k: clip(v) for k, v in bound.arguments.items()}
    except Exception:  # noqa: BLE001 - fall back rather than drop the row
        return {
            "args": [clip(a) for a in args],
            "kwargs": {k: clip(v) for k, v in kwargs.items()},
        }


def audited(tool, append):
    """Wrap one MCP tool so every invocation appends an audit row.

    `functools.wraps` copies `__name__`/`__doc__`/annotations and sets
    `__wrapped__`, which `inspect.signature` follows by default — so FastMCP
    still derives the same tool schema from the wrapper as it did from the bare
    function. Without that the wrapper would register as `(*args, **kwargs)`
    and silently destroy every tool's parameter schema.

    Async and sync tools are wrapped separately: returning a coroutine from a
    sync wrapper (or awaiting a sync function) would break registration.
    """
    if inspect.iscoroutinefunction(tool):

        @functools.wraps(tool)
        async def _async_wrapper(*args, **kwargs):
            append(tool.__name__, _safe_payload(tool, args, kwargs))
            return await tool(*args, **kwargs)

        return _async_wrapper

    @functools.wraps(tool)
    def _sync_wrapper(*args, **kwargs):
        append(tool.__name__, _safe_payload(tool, args, kwargs))
        return tool(*args, **kwargs)

    return _sync_wrapper


def register_audited_tools(app, tools, sink: str) -> None:
    """Register each tool on `app` with audit instrumentation attached.

    This is the production caller `audit_appender` previously lacked. Before
    this existed the appender was defined, unit-tested, and never invoked
    outside tests, so `_AUDIT_SINK` was dead config and every consensus /
    ensemble MCP invocation bypassed the JSONL audit trail that replacing
    JanuScope was justified by.
    """
    append = audit_appender(sink)
    for tool in tools:
        app.tool()(audited(tool, append))


def run_http_daemon(mcp, *, pid_filename: str, port: int) -> None:
    """Claim the singleton slot, then serve FastMCP over streamable-http on loopback.

    Binds to 127.0.0.1 ONLY (native Windows; never expose to the network).
    If a daemon is already running for this slot, prints a message and exits 0.

    Note: FastMCP's run() method does not accept host/port kwargs. The host and
    port must be set on the FastMCP instance's settings before calling run().
    This function patches ``mcp.settings.port`` in-place before serving.
    """
    try:
        claimed = claim_singleton(pid_filename)
    except ClaimUnavailable as exc:
        # NONZERO, and on stderr. Exiting 0 here told Start-Daemon that a
        # healthy daemon already held the port, so a machine that simply could
        # not write its agent directory reported a successful startup.
        print(f"[FLOSS MCP] cannot claim :{port}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not claimed:
        print(f"[FLOSS MCP] already running on :{port}; exiting.", file=sys.stderr)
        sys.exit(0)
    # FastMCP stores host/port in settings; run() reads them from there.
    mcp.settings.port = port
    mcp.settings.host = "127.0.0.1"
    mcp.run(transport="streamable-http")


def _record_identity_cli() -> int:
    """`--record-identity <pid_file> <pid>` -> write the pair for another process.

    OmniRoute is launched by the PowerShell start script, not by this module, so
    nothing was recording its identity. Both scripts therefore identified it by
    matching `omniroute` in every node.exe command line on the host -- which
    killed other projects' processes on stop, and let another project's process
    satisfy the duplicate guard on start.

    Scoping that match to the checkout does not work either: the start script
    runs `omniroute --no-open`, so the child's command line references the
    globally installed package and never the working directory. A filter written
    on that assumption classifies our own process as foreign and leaves it
    running -- which is what happened.

    The answer is to stop matching command lines and record identity at launch,
    the same way claim_singleton does. One mechanism, a third caller.
    """

    if len(sys.argv) < 4:
        print(
            "usage: --record-identity <pid_file> <pid> [<reservation_token>]",
            file=sys.stderr,
        )
        return 2
    pid_path = Path(sys.argv[2])
    try:
        pid = int(sys.argv[3])
    except ValueError:
        return 2
    presented = sys.argv[4].strip() if len(sys.argv) > 4 else ""

    try:
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        with _claim_guard(pid_path):
            return _record_identity_guarded(pid_path, pid, presented)
    except TimeoutError:
        # Another mutation of this claim is in flight. Reporting a state we did
        # not reach is the failure this file has made three times; the caller
        # stops the server it launched, which is correct.
        print("STALE_RESERVATION")
        return 1
    except OSError:
        print("UNKNOWN")
        return 2
    except ImportError:
        # Fails closed, like every other path that needs the shared helper.
        print("UNKNOWN")
        return 2


def _record_identity_guarded(pid_path: Path, pid: int, presented: str) -> int:
    # RECORD INTO THE RESERVATION WE MADE, NOT WHATEVER IS THERE NOW.
    #
    # This wrote unconditionally. A launcher suspended past
    # _RESERVATION_STALE_SECONDS has its reservation correctly reclaimed by a
    # second launcher -- that recovery is deliberate -- and then resumes and
    # records its PID over the second launcher's live claim. Both OmniRoute
    # servers are up; the tracked PID belongs to whichever recorded last, so
    # stop kills one and leaves the other listening and untracked.
    #
    # Fail closed on a token mismatch, including a caller that presents none:
    # a marked reservation belongs to a specific launcher, and a recorder that
    # cannot name it is not that launcher. Absent, empty and PID-bearing claims
    # Absent and empty claims are untouched: an empty claim is a pre-marker
    # reservation that cannot be attributed either way. A PID-bearing claim is
    # accepted only when it already names the PID being recorded, which is a
    # genuine re-record; any other PID belongs to a launcher that beat us.
    #
    # BOTH HALVES SNAPSHOTTED HERE, TOGETHER. The sidecar used to be inspected
    # at the moment it was about to be deleted, which is after the token check
    # and after two process probes. A launcher that replaced the reservation
    # and recorded its own PID in that gap had ITS sidecar captured and deleted
    # by this call, and only then did the claim check reject the write -- so
    # the winner kept its claim, lost its identity, and became an UNKNOWN that
    # neither script will manage. One snapshot, one guard, one transition.
    existing = _inspect_claim(pid_path)
    existing_sidecar = _inspect_sidecar(pid_path)

    if existing is not None:
        raw = existing.data.decode("utf-8", "replace").strip()
        held = _reservation_token_of(raw)
        if held is not None:
            if held != presented:
                print("STALE_RESERVATION")
                return 1
        elif raw and raw != str(pid):
            # A PID-BEARING CLAIM IS NOT A FREE PASS.
            #
            # The token test only rejected when the record was still a
            # RESERVATION, so a launcher whose reservation had been reclaimed
            # AND already converted to a PID claim by the winner sailed
            # through: _reservation_token_of returns None for a pid, the
            # branch did not fire, and the code below deleted the winner's
            # claim and sidecar and recorded the loser's PID. The comment here
            # used to call that "a re-record, which was always allowed" -- true
            # only when the pid is OURS, which is the case this now tests.
            #
            # Moving a slot to a different PID is a release followed by a
            # record, and has to be asked for in those words.
            print("STALE_RESERVATION")
            return 1

    if not _pid_alive(pid):
        print("NOT_RUNNING")
        return 1
    token = _process_start_token(pid)

    # Nothing can have moved under the guard, so these removals act on exactly
    # what was snapshotted above. Sidecar first, as everywhere else: if this
    # process dies between the two, the survivor is an unverifiable holder,
    # which blocks -- rather than a claim with a stranger's identity beside it,
    # which is read as proof the holder is foreign.
    if existing is not None:
        if not _sidecar_cleared(pid_path, existing_sidecar):
            print("STALE_RESERVATION")
            return 1
        if not _reclaim_claim_if_unchanged(pid_path, existing):
            print("STALE_RESERVATION")
            return 1

    try:
        fd = os.open(pid_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print("STALE_RESERVATION")
        return 1
    except OSError:
        print("UNKNOWN")
        return 2
    try:
        os.write(fd, str(pid).encode("utf-8"))
    except OSError:
        os.close(fd)
        print("UNKNOWN")
        return 2
    os.close(fd)
    try:
        if token:
            _identity_path(pid_path).write_text(token, encoding="utf-8")
        else:
            # No token means the next reader cannot disprove this PID, so leave
            # no stale sidecar from a previous holder to be compared against it.
            _identity_path(pid_path).unlink(missing_ok=True)
    except OSError:
        print("UNKNOWN")
        return 2
    print("RECORDED")
    return 0


def _reserve_slot_cli() -> int:
    """`--reserve-slot <pid_file>` -> claim the slot atomically before launching.

    OmniRoute is started by the PowerShell script, so nothing claimed its slot
    until `--record-identity` ran AFTER the server was already up. Two copies of
    the start script with no pid file could therefore both pass the guard, both
    launch, and both record -- the one that lost the port bind recording last,
    then exiting, leaving the bound server live and untracked.

    O_CREAT|O_EXCL at the filesystem level, the same primitive claim_singleton
    uses, so exactly one launcher wins. Prints RESERVED / OCCUPIED on stdout
    (verdict on stdout, not in the exit code, for the same reason
    --check-identity does: PowerShell cannot catch a native command's failure).
    The reservation is a placeholder: the caller overwrites it with the real
    server PID via --record-identity once the process exists.
    """

    if len(sys.argv) < 3:
        print("usage: --reserve-slot <pid_file>", file=sys.stderr)
        return 2
    pid_path = Path(sys.argv[2])
    try:
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        with _claim_guard(pid_path):
            return _reserve_slot_guarded(pid_path)
    except TimeoutError:
        # Another mutation of this claim is in flight; it will either leave a
        # live claim or a fresh reservation, and both mean OCCUPIED here.
        print("OCCUPIED")
        return 1
    except (OSError, ImportError):
        print("OCCUPIED")
        return 1


def _reserve_slot_guarded(pid_path: Path) -> int:
    # THE CREATORS HAVE TO JOIN THE GUARD, NOT ONLY THE RECLAIMERS.
    #
    # The guard was added to reclaim_if_unchanged and to the two transitions
    # that remove records, and this exclusive create -- the thing those
    # reclaimers race against -- was left outside it. A guard only some
    # mutators take is not mutual exclusion: a slow reclaimer that inspected an
    # old claim could still have it replaced here before it entered the
    # guarded helper, then move that LIVE reservation aside, and a second
    # unguarded create could occupy the momentarily free pathname so the
    # rollback discarded the displaced claim. Exactly the window the guard was
    # added to close, still open through the door that was not fitted.
    #
    # This is the right lock around the wrong span, which is the shape this
    # session has now produced more than any other.
    try:
        fd = os.open(pid_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        # THE RECLAMATION HAS TO BE ON THIS PATH, NOT ONLY IN claim_singleton.
        #
        # A launcher killed between --reserve-slot and --record-identity leaves
        # this file empty forever. The blank-claim recovery added to
        # claim_singleton cannot help: the OmniRoute path never calls it, and it
        # never reaches this function again either, because the file exists and
        # O_EXCL refuses. So the recovery sat in the function I was looking at
        # while the path that actually strands was left alone -- and OmniRoute
        # stayed disabled until an operator deleted the file by hand.
        #
        # Only a BLANK reservation past the stale window is reclaimed here. A
        # file with a pid in it belongs to --record-identity and the identity
        # checks, which know how to probe it.
        reclaimed = False
        try:
            observed = _inspect_claim(pid_path)
            observed_sidecar = _inspect_sidecar(pid_path)
            # _is_reservation, not emptiness. Marking reservations with a
            # token made this predicate permanently false, so an abandoned
            # marked claim reported OCCUPIED forever -- the token was added to
            # let two reservations be told apart and it disabled the recovery
            # that tells a dead one from a live one. claim_singleton's two
            # branches and the PowerShell reader were updated; this one, in the
            # command that WRITES the marker, was not.
            if observed is not None and _is_reservation(
                observed.data.decode("utf-8", "replace").strip()
            ):
                if _blank_claim_is_stale(pid_path):
                    # Same ordering as claim_singleton: the sidecar first and
                    # content-checked, then the claim.
                    reclaimed = _sidecar_cleared(pid_path, observed_sidecar) and (
                        _reclaim_claim_if_unchanged(pid_path, observed)
                    )
        except OSError:
            reclaimed = False
        if not reclaimed:
            print("OCCUPIED")
            return 1
        try:
            fd = os.open(pid_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except OSError:
            print("OCCUPIED")
            return 1
    except OSError:
        print("OCCUPIED")
        return 1
    # An EMPTY claim file is read as in-progress (not stale) by claim_singleton
    # and by --check-identity, which is exactly the state we want between the
    # reservation and the recording: occupied, unverifiable, and therefore
    # blocking rather than reclaimable.
    # THE TOKEN IS A CAPABILITY, SO IT HAS TO REACH THE CALLER.
    #
    # It was generated inline and thrown away, which left --record-identity
    # with nothing to check: a launcher suspended past the 60-second stale
    # window has its reservation legitimately reclaimed by a second launcher,
    # then wakes and records its PID over the winner's live claim. Both servers
    # start and the surviving one is tracked under the wrong PID. Printing it
    # is what turns "a marker that distinguishes reservations" into "a marker
    # the holder can present".
    token = _reservation_token()
    try:
        os.write(fd, f"{_RESERVATION_MARKER} {token}".encode("utf-8"))
    except OSError:
        # The reservation exists but is empty -- the pre-marker state, still
        # occupied and still blocking. Claiming a token the file does not carry
        # would make every later --record-identity refuse, so say what is true.
        token = ""
    os.close(fd)
    print(f"{_RESERVATION_MARKER} {token}".strip())
    return 0


def _release_claim_cli() -> int:
    """`--release-claim <pid_file> token|pid <value>` -> release a claim we own.

    Four PowerShell sites released claims with `Remove-Item <path>`: the start
    script when it could not record a launched server and when a launch failed,
    and the stop script's two OURS branches. Every one of them deleted whatever
    occupied the pathname rather than the record it had just acted on.

    That is a real race in both directions. On stop: a start script running
    immediately after Stop-Process reads the record as FOREIGN, reclaims it,
    and reserves the slot -- and then these deletions remove the NEW launcher's
    claim, so a later start launches a duplicate. On start: --record-identity
    returns STALE_RESERVATION precisely because another launcher now owns the
    slot, and the cleanup that follows deletes that winner's files, leaving it
    live and untracked.

    So the release has to name what it expects to find:

      token <t>   release only a reservation still marked `RESERVED <t>`
      pid <n>     release only a claim whose contents are exactly <n>

    Removal is instance-checked through the same shared helper every other path
    here uses, sidecar first, so losing the race costs nothing: NOT_RELEASED
    means someone else already owns the slot, which is the state the caller
    wanted to reach anyway.
    """

    if len(sys.argv) < 5:
        print(
            "usage: --release-claim <pid_file> token|pid <value>",
            file=sys.stderr,
        )
        return 2
    pid_path = Path(sys.argv[2])
    kind = sys.argv[3].strip().lower()
    value = sys.argv[4].strip()
    if kind not in {"token", "pid"}:
        print("usage: --release-claim <pid_file> token|pid <value>", file=sys.stderr)
        return 2

    try:
        with _claim_guard(pid_path):
            return _release_claim_guarded(pid_path, kind, value)
    except TimeoutError:
        # Could not act. NOT the same as "someone else owns it" -- see below.
        print("NOT_RELEASED")
        return 1
    except (OSError, ImportError):
        print("NOT_RELEASED")
        return 1


def _release_claim_guarded(pid_path: Path, kind: str, value: str) -> int:
    # THREE VERDICTS, BECAUSE THE CALLER'S NEXT MOVE DIFFERS FOR EACH.
    #
    # This printed NOT_RELEASED both for "another launcher owns the slot now"
    # and for "the record is unreadable and still there". The scripts treated
    # both as the benign first case, dropped the boolean, and went on to print
    # an unconditional success line -- so a stale record that will block the
    # next start was reported as a clean shutdown. Fourth instance in these
    # scripts of announcing a state they did not reach.
    #
    #   RELEASED    we removed the record we named
    #   SUPERSEDED  someone else owns the slot; nothing to do, nothing wrong
    #   NOT_RELEASED we could not act, and the record is still there
    #
    # BOTH HALVES SNAPSHOTTED TOGETHER, under the guard, for the same reason
    # --record-identity does it: inspecting the sidecar at deletion time meant
    # capturing a replacement's identity and deleting it before the claim check
    # refused to remove the replacement's claim.
    observed = _inspect_claim(pid_path)
    observed_sidecar = _inspect_sidecar(pid_path)

    if observed is None:
        # ABSENT IS SUCCESS; UNREADABLE IS NOT -- decided the same way
        # --reclaim-claim decides it, because _inspect_claim returns None for
        # both and the caller's next move differs completely.
        try:
            pid_path.lstat()
        except FileNotFoundError:
            print("RELEASED")
            return 0
        except OSError:
            pass
        print("NOT_RELEASED")
        return 1

    raw = observed.data.decode("utf-8", "replace").strip()
    if kind == "token":
        if _reservation_token_of(raw) != value:
            print("SUPERSEDED")
            return 0
    elif raw != value:
        print("SUPERSEDED")
        return 0

    if _sidecar_cleared(pid_path, observed_sidecar) and _reclaim_claim_if_unchanged(
        pid_path, observed
    ):
        print("RELEASED")
        return 0
    print("NOT_RELEASED")
    return 1


def _reclaim_claim_cli() -> int:
    """`--reclaim-claim <pid_file>` -> instance-checked removal of a dead claim.

    Exists so the PowerShell start script stops reclaiming by pathname. Two
    scripts can both read the same record as FOREIGN; the first deletes it and
    reserves, and the second then deletes THAT reservation and reserves too --
    both launch a server on one port, and the loser overwrites the winner's
    identity record. One implementation, four callers.

    Prints RECLAIMED / NOT_RECLAIMED on stdout for the same reason the other
    verdicts live there: PowerShell cannot catch a native command's failure.
    """

    if len(sys.argv) < 3:
        print("usage: --reclaim-claim <pid_file>", file=sys.stderr)
        return 2
    pid_path = Path(sys.argv[2])
    observed = _inspect_claim(pid_path)
    observed_sidecar = _inspect_sidecar(pid_path)
    if observed is None:
        # ABSENT IS SUCCESS; UNREADABLE IS NOT -- the same distinction
        # _sidecar_cleared makes, decided the same way. _inspect_claim
        # returns None for both, and the try/except that used to separate
        # them stopped firing the moment it stopped raising: a third place
        # this one None had to be pulled back apart.
        try:
            pid_path.lstat()
        except FileNotFoundError:
            print("RECLAIMED")
            return 0
        except OSError:
            pass
        print("NOT_RECLAIMED")
        return 1
    if _sidecar_cleared(pid_path, observed_sidecar) and _reclaim_claim_if_unchanged(
        pid_path, observed
    ):
        print("RECLAIMED")
        return 0
    print("NOT_RECLAIMED")
    return 1


def _identity_cli() -> int:
    """`python -m packages.mcp_daemon --check-identity <pid_file>`.

    Exists so the stop script does not reimplement the creation-token format in
    PowerShell. ONE implementation, two callers. An identity check written twice
    in two languages is the drift this repository keeps recording as FM-4 -- and
    a stop path computing the token slightly differently would either refuse to
    stop real daemons or agree to kill innocent processes. A first attempt at the
    PowerShell version already produced a different token for the same PID,
    because `-band 0xFFFFFFFF` does not mask an int64 there.

    THE VERDICT IS ON STDOUT, not in the exit code. A caller that read only the
    exit status could not distinguish "provably not ours" (1) from "the
    interpreter could not import this module" (also 1) -- and PowerShell does not
    enter `catch` for a failed external command, it just records the status. The
    stop script therefore treated a wrong-interpreter launch as a proven
    mismatch, deleted the PID files, and left live daemons running and
    unfindable: precisely the outcome the identity check was added to prevent.

    So the contract is a single token on stdout -- OURS / FOREIGN / UNKNOWN --
    and anything else, including no output at all, means UNKNOWN. Exit codes are
    kept (0/1/2) for shell use but are advisory; a startup failure cannot forge a
    token it never printed.

    UNKNOWN must never authorise a kill, for the same reason claim_singleton
    treats an unverifiable holder as still blocking.
    """

    def verdict(token: str, code: int) -> int:
        print(token)
        return code

    if len(sys.argv) < 3:
        print("usage: --check-identity <pid_file>", file=sys.stderr)
        return verdict("UNKNOWN", 2)
    pid_path = Path(sys.argv[2])
    try:
        pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return verdict("UNKNOWN", 2)
    if not _pid_alive(pid):
        return verdict("FOREIGN", 1)
    try:
        recorded = _identity_path(pid_path).read_text(encoding="utf-8").strip()
    except OSError:
        return verdict("UNKNOWN", 2)
    if not recorded:
        return verdict("UNKNOWN", 2)
    current = _process_start_token(pid)
    if current is None:
        return verdict("UNKNOWN", 2)
    return verdict("OURS", 0) if current == recorded else verdict("FOREIGN", 1)


if __name__ == "__main__":
    if "--release-claim" in sys.argv:
        raise SystemExit(_release_claim_cli())
    if "--reclaim-claim" in sys.argv:
        raise SystemExit(_reclaim_claim_cli())
    if "--reserve-slot" in sys.argv:
        raise SystemExit(_reserve_slot_cli())
    if "--check-identity" in sys.argv:
        raise SystemExit(_identity_cli())
    if "--record-identity" in sys.argv:
        raise SystemExit(_record_identity_cli())
    raise SystemExit(0)
