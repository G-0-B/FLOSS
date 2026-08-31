"""File locking shared by the provenance chain and the intake watcher.

STANDARD LIBRARY ONLY, deliberately. `packages/activity_log/__init__.py` keeps
`provenance` lazily imported so lean consumers do not pull blake3, jcs and
PyNaCl; importing the lock from `provenance` defeated that and broke
`watch_intake.py --help` on installs without the provenance extras. The lock
never needed them.

## Why the OS holds this lock and not a file's existence

The first eight versions of this module treated "a file exists at this path" as
the lock. Everything that went wrong followed from that one decision, because a
holder that dies leaves its marker behind, so the module had to decide when a
marker was abandoned and then remove it:

  * age alone reclaimed locks whose holders were merely slow;
  * owner liveness fixed that and made a lock immortal once its pid was reused;
  * a process-creation token fixed THAT and left the removal itself racy;
  * an atomic rename fixed the removal and made the ROLLBACK racy, because
    putting a live holder's lock back requires the path to be free, and any
    moment the path is free is a moment another contender can take it.

That last one has no fix at this layer. Reclamation cannot be made safe when
the thing being reclaimed must be removed from the namespace to be examined.

An OS lock has no marker to abandon. The kernel drops it when the holding
process exits, however it exits, so there is nothing to expire, nothing to
reclaim, and no window in which the resource looks free while an owner is still
inside the critical section. The lock FILE is never unlinked -- it is a handle,
not a claim -- which removes the last operation that could race.

`fcntl.flock` on POSIX, `msvcrt.locking` on Windows; both are standard library.
Advisory, so every participant must come through this module. Not safe over
NFS, which this workspace does not use.
"""

from __future__ import annotations

import base64
import os
import sys
import time
from pathlib import Path

# How long an acquirer waits for a live holder before giving up.
_LOCK_TIMEOUT_SECONDS = 5.0

# Retained for callers that still pass it. There is no staleness to configure:
# the kernel releases the lock when its holder dies. Accepting and ignoring it
# keeps watch_intake and provenance unchanged; it is documented as ignored
# rather than quietly dropped, because a parameter that looks like it does
# something is worse than one that says it does not.
_LOCK_STALE_SECONDS = 60.0

_POLL_SECONDS = 0.05

# OWNER ONLY. The lock file carries a pid and a random token, and every process
# that takes it runs as the workspace's operator -- there is no cross-user
# sharing to preserve here, so world-readable is permission this file has no
# use for. 0o644 was a copied default rather than a decision, which is what
# CodeQL flagged.
_LOCK_FILE_MODE = 0o600

# The byte the OS lock is taken on, far past any diagnostic content.
#
# Windows msvcrt locks are MANDATORY, not advisory: locking byte 0 made the
# pid/token line unreadable to every other opener, including this module's own
# _lock_token. Locking a byte beyond the content leaves the file readable while
# held, which is the whole reason the content is written.
_LOCK_BYTE = 1 << 20

# token -> (fd, path). The fd IS the lock: closing it releases, and the process
# exiting closes it. Holding it here keeps it alive for the critical section.
_HELD: dict[str, tuple[int, Path]] = {}


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


if sys.platform == "win32":  # pragma: no cover - platform split
    import msvcrt

    def _try_lock(fd: int) -> bool:
        os.lseek(fd, _LOCK_BYTE, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        os.lseek(fd, _LOCK_BYTE, os.SEEK_SET)
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass

else:  # pragma: no cover - platform split
    import fcntl

    def _try_lock(fd: int) -> bool:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def _unlock(fd: int) -> None:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except OSError:
            pass


def _lock_token(lock_path: Path) -> str | None:
    """The token a lock file carries, for diagnostics and for release checks.

    Historical formats -- token alone, pid+token, pid+start+token -- all put the
    token last, and so does this one.
    """

    try:
        lines = lock_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return None
    if not lines:
        return None
    return lines[-1].strip() if len(lines) > 1 else lines[0].strip()


def _acquire_lock(
    lock_path: Path,
    *,
    timeout_seconds: float | None = None,
    stale_seconds: float | None = None,
) -> str:
    """Take the lock, waiting up to `timeout_seconds`. Returns a release token.

    `stale_seconds` is accepted and IGNORED. Nothing goes stale here: the kernel
    releases the lock when the holder's process exits, including a kill -9 or a
    power loss, so there is no abandoned state to expire. The parameter stays so
    callers that pass a scan-sized window keep working unchanged.

    Raises TimeoutError if a live holder keeps it for the whole window.
    """

    timeout = _LOCK_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    deadline = time.monotonic() + timeout
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # O_CREAT, never O_EXCL: the file is a handle, not a claim. Two processes
    # opening it is expected and harmless; the lock is what one of them holds.
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, _LOCK_FILE_MODE)
    try:
        while True:
            if _try_lock(fd):
                break
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"timed out acquiring {lock_path} after {timeout:.0f}s; "
                    f"another process holds it"
                )
            time.sleep(_POLL_SECONDS)
    except BaseException:
        os.close(fd)
        raise

    token = _b64url_encode(os.urandom(18))
    try:
        # Diagnostics only. Nothing reads this to decide ownership any more --
        # that is the point of moving to an OS lock -- but `who holds this` is
        # the first question an operator asks.
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n{token}".encode("utf-8"))
    except OSError:
        pass

    _HELD[token] = (fd, lock_path)
    return token


def _release_lock(lock_path: Path, token: str) -> None:
    """Release a lock taken by this process. Best-effort, never raises.

    The file is NOT unlinked. Removing it was the operation every earlier
    version raced on, and it buys nothing: an unlocked lock file is not a lock,
    and the next acquirer opens the same path and locks it.
    """

    held = _HELD.pop(token, None)
    if held is None:
        return
    fd, _path = held
    try:
        _unlock(fd)
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


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
                fd = os.open(
                    path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _LOCK_FILE_MODE
                )
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
