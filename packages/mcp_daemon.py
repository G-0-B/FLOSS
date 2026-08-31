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
from datetime import datetime, timezone
from pathlib import Path

# A blank reservation older than this is a launcher that died between
# --reserve-slot and --record-identity. Deliberately far longer than the
# milliseconds a real launcher needs in between, because the failure modes are
# asymmetric: reclaiming too early starts a duplicate daemon on a bound port,
# while reclaiming too late costs one more run.
_RESERVATION_STALE_SECONDS = 60.0


def _reclaim_claim_if_unchanged(pid_path: Path, observed: bytes | None) -> bool:
    """Remove a claim only if it is still the file the checks inspected.

    Delegates to the shared filelock implementation rather than growing a third
    copy of rename-then-verify here. Falls back to a plain unlink only if that
    module cannot be imported, which keeps the daemon runnable on its own.
    """

    try:
        from packages.activity_log.filelock import reclaim_if_unchanged

        return reclaim_if_unchanged(pid_path, observed)
    except ImportError:
        try:
            pid_path.unlink(missing_ok=True)
        except OSError:
            return False
        return True


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
    claimed = False
    for _ in range(5):
        try:
            fd = os.open(pid_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raw = ""
            # Captured before every check below, so the reclaim can prove it is
            # removing the same claim those checks inspected.
            try:
                observed = pid_path.read_bytes()
            except OSError:
                observed = None
            try:
                raw = pid_path.read_text(encoding="utf-8").strip()
            except OSError:
                raw = ""
            if not raw:
                # AN EMPTY CLAIM IS AN IN-PROGRESS CLAIM, NOT A STALE ONE.
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
                if not raw:
                    # A BLANK CLAIM THAT IS OLD IS A CRASHED RESERVER.
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
                        # THE PID FILE GOES FIRST NOW, and the sidecar only if
                        # we won it. Removing the sidecar up front was correct
                        # when the reclaim was an unconditional unlink; with an
                        # instance-checked reclaim that can REFUSE, deleting it
                        # first destroys the winner's freshly written identity
                        # whenever we lose -- and --check-identity then reports
                        # UNKNOWN, so the stop script refuses to manage a live
                        # daemon. Losing the race must cost us nothing.
                        if _reclaim_claim_if_unchanged(pid_path, observed):
                            try:
                                _identity_path(pid_path).unlink(missing_ok=True)
                            except OSError:
                                pass
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
            # Sidecar AFTER, and only if the reclaim was ours. See the blank
            # branch above: an instance-checked reclaim can refuse, and a
            # sidecar removed before that answer is known is the winner's.
            if _reclaim_claim_if_unchanged(pid_path, observed):
                try:
                    _identity_path(pid_path).unlink(missing_ok=True)
                except OSError:
                    pass
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
    if not claimed:
        return False

    def _release() -> None:
        """Remove the pid file only while it still names this process.

        Unconditional unlink is what let a losing racer delete the winner's
        claim.
        """
        try:
            if pid_path.read_text(encoding="utf-8").strip() == str(me):
                # SIDECAR FIRST, exactly as the stale-reclaim path does.
                # Unlinking the PID file first opens a window in which a
                # replacement launcher claims the freed slot and writes ITS
                # identity -- which this callback then deletes. The replacement
                # stays alive but unverifiable, so the stop script refuses to
                # terminate it and every later launch stays blocked.
                _identity_path(pid_path).unlink(missing_ok=True)
                pid_path.unlink(missing_ok=True)
        except (OSError, ValueError):
            pass

    atexit.register(_release)
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (_release(), sys.exit(0)))
    return True


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
    if not claim_singleton(pid_filename):
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
        print("usage: --record-identity <pid_file> <pid>", file=sys.stderr)
        return 2
    pid_path = Path(sys.argv[2])
    try:
        pid = int(sys.argv[3])
    except ValueError:
        return 2
    if not _pid_alive(pid):
        print("NOT_RUNNING")
        return 1
    token = _process_start_token(pid)
    try:
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(str(pid), encoding="utf-8")
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
            observed = pid_path.read_bytes()
            if not observed.strip():
                if _blank_claim_is_stale(pid_path):
                    # Same ordering as claim_singleton: win the slot, then take
                    # the sidecar. Losing must leave the winner's record intact.
                    reclaimed = _reclaim_claim_if_unchanged(pid_path, observed)
                    if reclaimed:
                        _identity_path(pid_path).unlink(missing_ok=True)
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
    os.close(fd)
    print("RESERVED")
    return 0


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
    try:
        observed = pid_path.read_bytes()
    except FileNotFoundError:
        print("RECLAIMED")
        return 0
    except OSError:
        print("NOT_RECLAIMED")
        return 1
    if _reclaim_claim_if_unchanged(pid_path, observed):
        try:
            _identity_path(pid_path).unlink(missing_ok=True)
        except OSError:
            pass
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
    if "--reclaim-claim" in sys.argv:
        raise SystemExit(_reclaim_claim_cli())
    if "--reserve-slot" in sys.argv:
        raise SystemExit(_reserve_slot_cli())
    if "--check-identity" in sys.argv:
        raise SystemExit(_identity_cli())
    if "--record-identity" in sys.argv:
        raise SystemExit(_record_identity_cli())
    raise SystemExit(0)
