"""File locking shared by the provenance chain and the intake watcher.

STANDARD LIBRARY ONLY, deliberately. `packages/activity_log/__init__.py`
already goes out of its way to keep `provenance` lazily imported so lean
consumers do not pull blake3, jcs and PyNaCl -- and importing the lock from
`provenance` defeated exactly that, breaking `watch_intake.py --help` on any
install without the provenance extras. The lock itself never needed them.

One implementation, two callers. The behaviour here was written against
observed failures and each rule is load-bearing:

  * O_EXCL creation, so exactly one acquirer wins at the filesystem level.
  * Windows raises PermissionError, not FileExistsError, while a deleted lock
    sits in DELETE_PENDING -- both are contention.
  * A holder that has gone is reclaimed, or one crash wedges the resource
    forever.
  * Age alone does NOT authorise reclamation: a long critical section is not a
    dead one. The owner pid and its process-creation token decide, and age only
    bounds how long we keep believing a holder we can no longer see.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

# Defaults. Both are parameters on _acquire_lock: a packet write is
# milliseconds, while the intake watcher holds its lock across a recursive scan.
_LOCK_TIMEOUT_SECONDS = 5.0
_LOCK_STALE_SECONDS = 60.0


def _b64url_encode(raw: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _lock_token(lock_path: Path) -> str | None:
    """The token a lock file carries, independent of the owner line above it."""

    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    if not lines:
        return None
    # One line is a pre-owner-pid lock: the whole content is the token.
    return lines[-1].strip() if len(lines) > 1 else lines[0].strip()


def _owner_start_token() -> str:
    """This process's creation token, or "" where the platform has none."""

    try:
        from packages.mcp_daemon import _process_start_token

        return _process_start_token(os.getpid()) or ""
    except Exception:  # noqa: BLE001 -- absence degrades to pid-only ownership
        return ""


def _lock_owner_is_alive(lock_path: Path) -> bool | None:
    """True if the recorded owner still runs, False if it is gone, None if
    the lock does not say who owns it.

    A lock older than the stale window is only evidence that its holder has had
    it a long time; across a long critical section that is normal, so age alone
    must not authorise reclaiming it. Where an owner IS recorded, liveness
    decides and a running holder is never reclaimed however old the lock is.

    None matters: a lock written by an older build carries only a token, and
    treating that as "alive" would make every pre-existing lock on disk
    permanently unreclaimable -- turning a fix for abandoned locks into a way
    to strand them. Unknown falls back to the age-only policy those locks were
    written under.
    """

    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return True
    if len(lines) < 2:
        return None
    try:
        owner = int(lines[0].strip())
    except ValueError:
        return None
    # A PID IS NOT AN IDENTITY.
    #
    # After a crash the lock file survives, the OS reassigns that number, and a
    # liveness probe then reports the holder as running forever -- so the lock
    # is never reclaimed however old it is, and every later write to that chain
    # times out until someone deletes the file. That is the failure the age
    # window existed to prevent, reintroduced by the ownership check added to
    # fix a different one.
    #
    # mcp_daemon already disambiguates PID reuse by process creation time, for
    # its own pid files, against the same failure. Recorded locks carry that
    # token; a mismatch is a reused pid and the holder is gone.
    recorded_start = lines[1].strip() if len(lines) > 2 else ""
    if recorded_start:
        try:
            from packages.mcp_daemon import _process_start_token

            current_start = _process_start_token(owner)
        except Exception:  # noqa: BLE001 -- unknown identity stays conservative
            current_start = None
        if current_start is not None and current_start != recorded_start:
            return False

    # Checked AFTER the token, deliberately. A short-circuit here on "the owner
    # is me" hid the case the token exists for: our own pid, reused, holding a
    # lock written by a process that is gone.
    if owner == os.getpid():
        return True

    # REUSE the daemon's probe. os.kill(pid, 0) does not distinguish a dead pid
    # on Windows -- it raises a plain OSError, which a conservative handler
    # reads as "alive", so liveness could never disprove a holder there and the
    # whole check silently degraded to "never reclaim". mcp_daemon._pid_alive
    # already solves that with OpenProcess plus GetExitCodeProcess, written
    # against an observed failure. Imported lazily: nothing in mcp_daemon
    # imports this module, so there is no cycle, and a missing daemon module
    # must not break chain writes.
    try:
        from packages.mcp_daemon import _pid_alive
    except Exception:  # noqa: BLE001 -- unknown liveness stays conservative
        return True
    return _pid_alive(owner)


def reclaim_if_unchanged(path: Path, observed: bytes | None) -> bool:
    """Remove `path` only if it is still the exact file that was inspected.

    Check-then-unlink-by-pathname is not reclamation, it is a race. Two writers
    can both judge the same abandoned holder dead; the first unlinks it and
    takes a fresh lock, and the second then unlinks THAT -- deleting a live
    owner's lock. Both proceed, and for the provenance chain that means two
    writers inside the sequence critical section: duplicate reservations and
    forked heads, the exact corruption the lock exists to prevent.

    Renaming is the atomic part. Exactly one caller can move a given file aside,
    so everyone else's rename fails and they simply retry the exclusive create.
    The content check then covers the remaining window -- the holder released
    and a NEW one took the slot between inspection and rename -- by putting back
    anything that is not what we looked at.

    Returns True when this caller is the one that removed it.
    """

    quarantine = path.with_name(f"{path.name}.reclaim-{_b64url_encode(os.urandom(9))}")
    try:
        os.rename(path, quarantine)
    except OSError:
        # Gone, or another reclaimer moved it first. Either way it is not ours
        # to delete and the caller should just retry.
        return False

    if observed is not None:
        try:
            current = quarantine.read_bytes()
        except OSError:
            current = None
        if current != observed:
            # A different instance: released and re-taken while we looked, so
            # what we moved aside was a LIVE lock. Put it back.
            #
            # Not with rename. POSIX rename REPLACES an existing destination
            # silently, so a contender that acquired the momentarily-free path
            # while we were comparing would have its lock overwritten by our
            # rollback -- two owners in the sequence section, which is the
            # failure this whole function exists to prevent, reintroduced by its
            # own recovery path. O_EXCL cannot overwrite anything: either the
            # slot is still free and we restore, or someone holds it and the
            # copy in our hand is superseded.
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except OSError:
                # Someone holds the slot now. The copy in our hand is
                # superseded, so dropping it destroys nothing live.
                fd = None
            if fd is not None:
                try:
                    with os.fdopen(fd, "wb") as handle:
                        handle.write(current if current is not None else b"")
                except OSError:
                    pass
            try:
                quarantine.unlink(missing_ok=True)
            except OSError:
                pass
            # Either way this caller did NOT reclaim: a live lock stands.
            return False

    try:
        quarantine.unlink(missing_ok=True)
    except OSError:
        pass
    return True


def _lock_age_seconds(lock_path: Path) -> float | None:
    """Seconds since the lock file was created, or None if it is gone."""
    try:
        return max(0.0, time.time() - lock_path.stat().st_mtime)
    except (FileNotFoundError, PermissionError, OSError):
        return None


def _acquire_lock(
    lock_path: Path,
    *,
    timeout_seconds: float | None = None,
    stale_seconds: float | None = None,
) -> str:
    """Take the lock, reclaiming one whose holder is gone. Returns the token.

    Both windows are parameters because this is now used for two very different
    critical sections. A packet write is milliseconds, so a 60s holder is dead.
    The intake watcher holds its lock across a recursive scan of the workspace
    and thousands of event writes, which can legitimately exceed 60s -- and a
    fixed window then let a second watcher DELETE a live holder's lock and enter
    the same critical section, which is worse than the abandoned lock the
    reclamation was added to fix.

    Age alone is therefore not proof the holder died. The owner's pid is
    recorded beside the token, and a holder that is still running is never
    reclaimed however old the lock is; age only decides when to stop believing a
    holder we can no longer see.
    """

    timeout = _LOCK_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    stale = _LOCK_STALE_SECONDS if stale_seconds is None else stale_seconds
    deadline = time.monotonic() + timeout
    # Real stale reclamation, because there was none. `_release_lock` gives up
    # on a Windows PermissionError, and a crashed writer never releases at all;
    # in both cases the lock file simply stays, and an acquire loop that only
    # retried until its deadline wedged every later write to that chain
    # permanently after one transient sharing violation.
    while True:
        token = _b64url_encode(os.urandom(18))
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("x", encoding="utf-8") as f:
                # pid first, token second: the reader wants the owner and a
                # partial line must not be mistaken for a token.
                # pid, process-creation token, lock token -- one per line,
                # lock token LAST so _lock_token stays a last-line read
                # across all three formats this file has had.
                f.write(f"{os.getpid()}\n{_owner_start_token()}\n{token}")
            return token
        except (FileExistsError, PermissionError):
            # PermissionError is contention too, on Windows.
            #
            # POSIX gives a clean FileExistsError when the lock is held. Windows
            # does not: while another writer's unlink is in flight the file
            # enters DELETE_PENDING, and an O_EXCL create against it raises
            # PermissionError (WinError 5 / errno 13) rather than FileExistsError.
            # Catching only FileExistsError therefore let that escape and kill
            # the caller mid-chain, instead of retrying like any other contended
            # acquire.
            #
            # Observed as an intermittent failure of
            # test_concurrent_first_packet_creation_converges_on_one_identity --
            # it looked like a chain-integrity flake (two writers both believing
            # they were genesis) and was in fact this. It reproduced only under
            # full-suite CPU load on Windows, and never on the Linux CI runner,
            # which is why the required gate stayed green while local runs did not.
            # Captured BEFORE the age and owner checks, so the reclaim below
            # can prove it is removing the same file those checks looked at.
            try:
                observed = lock_path.read_bytes()
            except OSError:
                observed = None
            age = _lock_age_seconds(lock_path)
            if (
                age is not None
                and age >= stale
                # Not `not alive`: unknown ownership must reclaim on age, which
                # is the policy the locks that lack an owner were written under.
                and _lock_owner_is_alive(lock_path) is not True
            ):
                # Nothing ever touches a lock file after creation, so its mtime
                # age IS the time the current holder has held it. Past the stale
                # window that holder is gone -- a crashed writer, or a release
                # whose unlink lost to a Windows sharing violation -- and the
                # lock is reclaimed here instead of wedging the chain forever.
                #
                # By INSTANCE, not by pathname: an unlink here deleted whatever
                # sat at this path, including a fresh lock a faster reclaimer had
                # just taken.
                reclaim_if_unchanged(lock_path, observed)
                continue
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"timed out acquiring provenance lock {lock_path} after "
                    f"{timeout:.0f}s; holder age "
                    f"{'unknown' if age is None else format(age, '.1f') + 's'}, "
                    f"stale reclamation at {stale:.0f}s"
                )
            time.sleep(0.05)


def _release_lock(lock_path: Path, token: str) -> None:
    # Retry the unlink before giving up. Same Windows sharing semantics as the
    # acquire side: another process may hold a transient handle on the lock
    # file, and a single PermissionError here used to be swallowed outright --
    # which left the lock in place with nothing to remove it, because the
    # acquire side only retried until its deadline and then raised. One
    # transient sharing violation therefore wedged every later write to that
    # chain. Releasing stays best-effort rather than raising into a completed
    # chain write, but a lock this fails to remove is now genuinely reclaimed by
    # _acquire_lock's stale-age path instead of nominally.
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    while True:
        try:
            # The lock file is `pid` then `token`. Comparing the WHOLE file to
            # the token stopped matching the moment the owner pid was added, so
            # every release would have silently declined to unlink and left the
            # lock for the stale path -- read the token line.
            if _lock_token(lock_path) == token:
                lock_path.unlink(missing_ok=True)
            return
        except FileNotFoundError:
            return
        except PermissionError:
            if time.monotonic() >= deadline:
                return
            time.sleep(0.05)
