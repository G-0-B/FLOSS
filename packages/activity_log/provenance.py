"""KERI-shaped provenance packet helpers.

This is the Plane A provenance spine: self-addressing packet IDs, Ed25519
signatures, RFC 8785 canonical bytes, and a walkable per-agent chain. It is not
full KERI; it intentionally uses KERI field conventions so witness/rotation
support can be added later without changing packet shape.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import blake3
import jcs
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from packages.orchestrator.claim_schema import EVIDENCE_TYPES

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

VERSION_PREFIX = "FLOSSI10JSON"
VERSION_PLACEHOLDER = f"{VERSION_PREFIX}000000_"
SAID_PLACEHOLDER = "#" * 44
SIGNATURE_PLACEHOLDER = "0B" + ("A" * 86)

_AUTO_PRIOR = object()
_LOCK_TIMEOUT_SECONDS = 5.0
# A lock older than this is treated as abandoned and reclaimed. The critical
# section it guards is a couple of small local file writes -- milliseconds -- so
# an order of magnitude above the acquire timeout cannot be a live slow holder.
_LOCK_STALE_SECONDS = 60.0


@dataclass
class Identity:
    """Local Ed25519 identity material used for packet signing."""

    signing_key: SigningKey
    verify_key: VerifyKey
    aid: str


@dataclass
class PacketValidation:
    """Structured result returned by :func:`validate_packet`."""

    ok: bool
    errors: list[str] = field(default_factory=list)
    packet_digest: str | None = None
    narrative_lines: list[str] = field(default_factory=list)
    packet: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    """Non-fatal findings, chiefly from ANCESTOR packets.

    A packet attests to a state that was true when it was signed. Requiring an
    ancestor's artifact to still exist conflates history with current state: it
    means deleting or renaming any file that was ever hook-touched permanently
    poisons every later packet in that agent's chain. Ancestor artifact-absence
    and unreachable ancestors are therefore recorded here rather than in
    `errors`. A HASH MISMATCH stays fatal at any depth — a file that still
    exists but differs is a real tamper signal, not history.
    """


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def canonical_bytes(value: dict[str, Any]) -> bytes:
    """Return RFC 8785 JCS canonical UTF-8 bytes."""

    return jcs.canonicalize(value)


def sha256_file(path: Path | str) -> str:
    """Return the SHA-256 hex digest of a file's current bytes."""

    import hashlib

    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact_ref(
    path: Path | str, *, workspace_root: Path | str | None = None
) -> dict[str, str]:
    """Build an artifact reference with a workspace-relative path and SHA-256."""

    root = Path(workspace_root or WORKSPACE_ROOT).resolve()
    artifact = Path(path).resolve()
    try:
        ref_path = artifact.relative_to(root).as_posix()
    except ValueError:
        ref_path = str(artifact)
    return {"path": ref_path, "sha256": sha256_file(artifact)}


def load_or_create_identity(identity_dir: Path | str) -> Identity:
    """Load or bootstrap the local Ed25519 identity."""

    root = Path(identity_dir)
    root.mkdir(parents=True, exist_ok=True)
    private_path = root / "private.key"
    public_path = root / "public.key"
    aid_path = root / "aid"
    lock_path = root / ".identity.lock"
    token = _acquire_lock(lock_path)
    try:
        if private_path.exists():
            seed = _b64url_decode(private_path.read_text(encoding="utf-8").strip())
            signing_key = SigningKey(seed)
        else:
            signing_key = SigningKey.generate()
            private_path.write_text(
                _b64url_encode(bytes(signing_key)) + "\n", encoding="utf-8"
            )
            try:
                os.chmod(private_path, 0o600)
            except OSError:
                pass

        verify_key = signing_key.verify_key
        aid = "D" + _b64url_encode(bytes(verify_key))
        public_path.write_text(
            _b64url_encode(bytes(verify_key)) + "\n", encoding="utf-8"
        )
        aid_path.write_text(aid + "\n", encoding="utf-8")
        return Identity(signing_key=signing_key, verify_key=verify_key, aid=aid)
    finally:
        _release_lock(lock_path, token)


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
                try:
                    lock_path.unlink(missing_ok=True)
                except (FileNotFoundError, PermissionError):
                    pass
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


def _state_path(identity_dir: Path, aid: str) -> Path:
    return identity_dir / f"{aid}.chain.json"


def _load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"next_sequence": 0, "head": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"next_sequence": 0, "head": None}
    return {
        "next_sequence": int(data.get("next_sequence", 0)),
        "head": data.get("head"),
    }


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(state, separators=(",", ":"), sort_keys=True), encoding="utf-8"
    )
    os.replace(tmp, path)


@contextmanager
def _sequence_lock(identity_dir: Path):
    """Hold the per-identity sequence lock for an entire critical section.

    Reserving a sequence and committing the new chain head must be atomic
    relative to other writers: if the lock is dropped between reserve and
    commit, a second writer can reserve the next sequence while `head` still
    points at the old packet, producing a wrong `p` back-link or letting one
    commit clobber the other's head. Holding the lock across reserve → write →
    commit serializes writers per identity and keeps the chain linear.
    """
    lock_path = identity_dir / ".sequence.lock"
    token = _acquire_lock(lock_path)
    try:
        yield
    finally:
        _release_lock(lock_path, token)


def _reserve_sequence_locked(
    identity_dir: Path, aid: str, prior_digest: str | None | object
) -> tuple[int, str | None, dict[str, Any]]:
    """Reserve the next sequence number. Caller MUST hold `_sequence_lock`."""
    path = _state_path(identity_dir, aid)
    state = _load_state(path)
    sequence = int(state["next_sequence"])
    prior = state.get("head") if prior_digest is _AUTO_PRIOR else prior_digest
    state["next_sequence"] = sequence + 1
    _write_state(path, state)
    return sequence, prior, state


def _commit_sequence_head_locked(
    identity_dir: Path, aid: str, packet_digest: str
) -> None:
    """Set the chain head. Caller MUST hold `_sequence_lock`."""
    path = _state_path(identity_dir, aid)
    state = _load_state(path)
    state["head"] = packet_digest
    _write_state(path, state)


def _reserve_sequence(
    identity_dir: Path, aid: str, prior_digest: str | None | object
) -> tuple[int, str | None, dict[str, Any]]:
    """Reserve the next monotonic sequence number under its own file lock.

    Standalone wrapper retained for back-compat. `create_packet` does NOT use
    this — it holds the lock across reserve+commit via `_sequence_lock`.
    """
    with _sequence_lock(identity_dir):
        return _reserve_sequence_locked(identity_dir, aid, prior_digest)


def _commit_sequence_head(identity_dir: Path, aid: str, packet_digest: str) -> None:
    with _sequence_lock(identity_dir):
        _commit_sequence_head_locked(identity_dir, aid, packet_digest)


def _packet_date(entries: list[dict[str, Any]]) -> str:
    for entry in entries:
        created_at = entry.get("created_at")
        if isinstance(created_at, str) and len(created_at) >= 10:
            return created_at[:10]
    return datetime.now(timezone.utc).date().isoformat()


def _with_empty_sigs(packet: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(packet, separators=(",", ":"), sort_keys=True))
    clone["sigs"] = []
    return clone


def _said_digest(packet: dict[str, Any]) -> str:
    clone = _with_empty_sigs(packet)
    clone["d"] = SAID_PLACEHOLDER
    return "E" + _b64url_encode(blake3.blake3(canonical_bytes(clone)).digest())


def _version_with_size(packet: dict[str, Any]) -> str:
    return f"{VERSION_PREFIX}{len(canonical_bytes(packet)):06x}_"


def _signing_bytes(packet: dict[str, Any]) -> bytes:
    return canonical_bytes(_with_empty_sigs(packet))


def create_packet(
    entries: list[dict[str, Any]],
    *,
    identity_dir: Path | str,
    output_root: Path | str,
    prior_digest: str | None | object = _AUTO_PRIOR,
) -> tuple[dict[str, Any], Path]:
    """Create, sign, serialize, and write a provenance packet.

    ``prior_digest`` defaults to the current per-agent chain head. Pass ``None``
    explicitly to start a genesis packet.
    """

    if not entries:
        raise ValueError(
            "E_PROVENANCE_EMPTY_PACKET: at least one payload entry required"
        )

    identity_path = Path(identity_dir)
    identity = load_or_create_identity(identity_path)

    # Hold the sequence lock across reserve → sign → write → commit-head so a
    # concurrent writer for the same identity cannot reserve the next sequence
    # against a stale head (which would fork/misorder the per-agent chain).
    with _sequence_lock(identity_path):
        sequence, prior, _state = _reserve_sequence_locked(
            identity_path, identity.aid, prior_digest
        )

        packet: dict[str, Any] = {
            "v": VERSION_PLACEHOLDER,
            "t": "prov",
            "d": SAID_PLACEHOLDER,
            "i": identity.aid,
            "s": str(sequence),
            "p": prior,
            "a": entries,
            "sigs": [],
        }

        packet["d"] = _said_digest(packet)
        packet["sigs"] = [SIGNATURE_PLACEHOLDER]
        packet["v"] = _version_with_size(packet)
        packet["sigs"] = []
        packet["d"] = _said_digest(packet)
        signature = identity.signing_key.sign(_signing_bytes(packet)).signature
        packet["sigs"] = ["0B" + _b64url_encode(signature)]

        packet_path = Path(output_root) / _packet_date(entries) / f"{packet['d']}.json"
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        # ATOMIC: temp file then os.replace, the same idiom _write_state uses.
        #
        # A direct write_bytes leaves the packet observable half-written. The
        # anchor scan enumerates this tree holding a lock no writer takes, so it
        # read torn packets and recorded them as unreadable damage in a signed
        # anchor -- damage to a store that was fine. Under os.replace a reader
        # sees the old state or the new one, never a prefix, which fixes it for
        # every reader of this tree rather than for the one that complained.
        tmp_path = packet_path.with_suffix(".json.tmp")
        tmp_path.write_bytes(canonical_bytes(packet) + b"\n")
        os.replace(tmp_path, packet_path)
        _commit_sequence_head_locked(identity_path, identity.aid, packet["d"])
    return packet, packet_path


def _resolve_workspace_ref(ref: str, workspace_root: Path) -> Path:
    path = Path(ref)
    if path.is_absolute():
        return path
    return workspace_root / ref


def _infer_provenance_root(packet_path: Path | None) -> Path | None:
    if packet_path is None:
        return None
    parent = packet_path.parent
    name = parent.name
    if len(name) == 10 and name[4] == "-" and name[7] == "-":
        return parent.parent
    return parent


def _find_packet_by_digest(provenance_root: Path | None, digest: str) -> Path | None:
    if provenance_root is None or not provenance_root.exists():
        return None
    direct = provenance_root / f"{digest}.json"
    if direct.exists():
        return direct
    matches = list(provenance_root.rglob(f"{digest}.json"))
    return matches[0] if matches else None


def _build_packet_index(provenance_root: Path | None) -> dict[str, Path]:
    """Map digest -> packet path in one directory scan.

    `_find_packet_by_digest` falls back to a full `rglob` whenever a packet is
    not directly under `provenance_root`, which is the normal case since packets
    are filed into dated subdirectories. One scan per lookup is fine for a
    single call and quadratic for a chain walk: measured at 10 s to validate a
    200-link chain and 90 s for 600 links — 3x the length for 9x the cost.
    Building the index once turns the walk's lookups into O(1) each.

    Deliberately not cached across calls: a stale index would silently fail to
    find a packet written since the last scan, which for a chain walk means a
    spurious `E_PROVENANCE_PRIOR_UNAVAILABLE` on a chain that is actually
    intact. Rebuilding per walk keeps the cost linear without that risk.
    """
    if provenance_root is None or not provenance_root.exists():
        return {}
    try:
        return {p.stem: p for p in provenance_root.rglob("*.json")}
    except OSError:
        return {}


def _build_position_index(
    provenance_root: Path | None,
) -> dict[tuple[Any, Any, Any], list[tuple[Path, Any]]]:
    """Map chain position (i, p, s) -> [(path, digest)] in one pass.

    The fork check needs "is there another packet at my exact chain position",
    which previously meant reading EVERY packet on EVERY check. Since the check
    runs once per validated packet, walking an n-link chain read n packets n
    times: profiling a 300-link chain showed 90 000 file reads and 28.2 s of a
    29.1 s validation — 97 % of total runtime — and the cost is quadratic, so
    600 links took 90 s and 1200 took 365 s.

    Packets are content-addressed and immutable once written, so indexing them
    once per validation is safe and turns each check into a dict lookup.
    """
    index: dict[tuple[Any, Any, Any], list[tuple[Path, Any]]] = {}
    if provenance_root is None or not provenance_root.exists():
        return index
    try:
        candidates = sorted(
            provenance_root.rglob("*.json"), key=lambda path: path.as_posix()
        )
    except OSError:
        return index
    for candidate_path in candidates:
        try:
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(candidate, dict):
            continue
        position = (candidate.get("i"), candidate.get("p"), candidate.get("s"))
        # A packet is arbitrary JSON until it has been validated, and this index
        # is built BEFORE validation. A list or dict in `i`, `p` or `s` makes the
        # tuple unhashable, so one malformed or half-written file under the
        # provenance root would raise TypeError out of setdefault and take every
        # chain validation down with it. Skip it instead — it will be reported
        # as invalid on its own account if anything references it.
        try:
            index.setdefault(position, []).append((candidate_path, candidate.get("d")))
        except TypeError:
            continue
    return index


def _slot_is_genuinely_occupied(
    occupant_paths: list[Path] | None,
    *,
    workspace_root: Path,
    provenance_root: Path | None,
    seen: set[str],
    depth: int,
    max_depth: int,
    ignored_chain_position: tuple[Any, Any, Any] | None,
    position_index: dict[tuple[Any, Any, Any], list[tuple[Path, Any]]] | None,
) -> bool:
    """True only when a VALID signed packet holds the sequence slot.

    `_build_position_index` reads every JSON file under the provenance root
    before anything has been validated, so an unsigned object that merely names
    an identity and a sequence lands in the index. Declaring a fork on that
    basis let unrelated corruption -- or one hand-written file -- convert an
    enumerable gap into a fatal error on every later packet of a chain that is
    otherwise sound.

    A fork is a claim that someone signed a competing history. Only a signature
    can establish it.
    """
    for occupant_path in occupant_paths or []:
        if _packet_validates(
            occupant_path,
            workspace_root=workspace_root,
            provenance_root=provenance_root,
            seen=seen,
            depth=depth,
            max_depth=max_depth,
            ignored_chain_position=ignored_chain_position,
            position_index=position_index,
        ):
            return True
    return False


def _packet_validates(
    occupant_path: Path,
    *,
    workspace_root: Path,
    provenance_root: Path | None,
    seen: set[str],
    depth: int,
    max_depth: int,
    ignored_chain_position: tuple[Any, Any, Any] | None,
    position_index: dict[tuple[Any, Any, Any], list[tuple[Path, Any]]] | None,
) -> bool:
    try:
        result = validate_packet(
            occupant_path,
            workspace_root=workspace_root,
            provenance_root=provenance_root,
            # A copy: this is a side probe, and marking digests in the caller's
            # traversal set would make a later legitimate visit look like a cycle.
            _seen=set(seen),
            _depth=depth,
            max_depth=max_depth,
            _is_ancestor=True,
            _ignored_chain_position=ignored_chain_position,
            _follow_prior=False,
            _position_index=position_index,
        )
    except (OSError, ValueError):
        return False
    return result.ok


def _walk_sequence(value: Any) -> int | None:
    """Parse a chain position for the walk, or None if it cannot be trusted.

    `int()` accepts any decimal, and the walk sizes loops and gap lists from
    what it parses -- so an implausible `s` turns "produce a verdict" into
    "iterate a trillion times". The bound was added to the missing-predecessor
    branch and NOT to the non-adjacent-predecessor branch beside it, which
    reaches the same expansion by a different route. One parser, every site,
    so the next branch that reads a sequence cannot miss it.
    """

    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    if number < 0 or number > MAX_SEQUENCE:
        return None
    return number


def _sequence_index(
    position_index: dict[tuple[Any, Any, Any], list[tuple[Path, Any]]] | None,
) -> tuple[dict[Any, dict[int, list[Path]]], dict[Any, dict[int, list[Any]]]]:
    """Per-identity sequence -> (path, digest) maps, from the position index.

    Used by the prior walk to tell a genuine gap (nothing occupies the expected
    sequence number) from a fork or rewrite (something does, and the child
    points elsewhere). Derived rather than rescanned: the position index has
    already read every packet once.
    """
    paths: dict[Any, dict[int, list[Path]]] = {}
    digests: dict[Any, dict[int, list[Any]]] = {}
    for (identity, _prior, sequence), entries in (position_index or {}).items():
        try:
            slot = int(sequence)
        except (TypeError, ValueError):
            continue
        if slot > MAX_SEQUENCE or slot < 0:
            # Same bound as the walk above and the anchor scan. An implausible
            # slot is not indexed, so nothing downstream can be sized by it.
            continue
        for path, digest in entries:
            # EVERY occupant, not the first one found. The index walks candidates
            # in path order, so keeping one entry per slot let an unsigned file
            # whose name sorts earlier become the sole occupant: the validity
            # probe then checked only the decoy, the slot read as empty, and a
            # child bypassing the real signed packet escaped the fork check. The
            # question is whether ANY valid packet holds the slot.
            paths.setdefault(identity, {}).setdefault(slot, []).append(path)
            digests.setdefault(identity, {}).setdefault(slot, []).append(digest)
    return paths, digests


def _has_valid_same_position_competitor(
    packet: dict[str, Any],
    *,
    packet_path: Path | None,
    workspace_root: Path,
    provenance_root: Path | None,
    max_depth: int,
    position_index: dict[tuple[Any, Any, Any], list[tuple[Path, Any]]] | None = None,
) -> bool:
    """Return whether another independently valid packet occupies this position."""

    if provenance_root is None or not provenance_root.exists():
        return False

    current_path = packet_path.resolve() if packet_path is not None else None
    chain_position = (packet.get("i"), packet.get("p"), packet.get("s"))
    packet_digest = packet.get("d")

    if position_index is None:
        position_index = _build_position_index(provenance_root)
    # Only packets sharing this exact position can possibly compete; everything
    # else was filtered by the index rather than by reading it again here.
    for candidate_path, candidate_digest in position_index.get(chain_position, ()):
        try:
            if current_path is not None and candidate_path.resolve() == current_path:
                continue
        except OSError:
            continue
        if candidate_digest == packet_digest:
            # Exact-digest copies are duplicate evidence, not competing successors.
            continue
        competitor = validate_packet(
            candidate_path,
            workspace_root=workspace_root,
            provenance_root=provenance_root,
            max_depth=max_depth,
            _ignored_chain_position=chain_position,
            _position_index=position_index,
        )
        if competitor.ok:
            return True
    return False


def _public_key_from_aid(aid: str) -> VerifyKey:
    if not isinstance(aid, str) or not aid.startswith(("D", "B")):
        raise ValueError("E_PROVENANCE_BAD_AID")
    return VerifyKey(_b64url_decode(aid[1:]))


def _signature_bytes(signature: str) -> bytes:
    if not isinstance(signature, str) or not signature.startswith("0B"):
        raise ValueError("E_PROVENANCE_BAD_SIGNATURE")
    return _b64url_decode(signature[2:])


def _payload_entries(packet: dict[str, Any]) -> list[Any]:
    """Return payload entries only when the signed field has the required shape."""
    entries = packet.get("a")
    return entries if isinstance(entries, list) else []


def _entry_list_field(entry: Any, field_name: str) -> list[Any]:
    """Return a list field without iterating malformed signed payload values."""
    if not isinstance(entry, dict):
        return []
    value = entry.get(field_name)
    return value if isinstance(value, list) else []


def _artifact_errors(packet: dict[str, Any], workspace_root: Path) -> list[str]:
    errors: list[str] = []
    for entry in _payload_entries(packet):
        for ref in _entry_list_field(entry, "artifact_refs"):
            if not isinstance(ref, dict):
                errors.append("E_PROVENANCE_ARTIFACT_REF_INVALID")
                continue
            path_value = ref.get("path")
            expected = ref.get("sha256")
            if not path_value or not expected:
                errors.append("E_PROVENANCE_ARTIFACT_REF_INVALID")
                continue
            path = _resolve_workspace_ref(str(path_value), workspace_root)
            if not path.exists():
                errors.append("E_PROVENANCE_ARTIFACT_MISSING")
                continue
            if sha256_file(path) != expected:
                errors.append("E_PROVENANCE_ARTIFACT_HASH_MISMATCH")
    return errors


def _has_non_packet_evidence(packet: dict[str, Any]) -> bool:
    for entry in _payload_entries(packet):
        for ref in _entry_list_field(entry, "evidence_refs"):
            if isinstance(ref, dict) and ref.get("type") != "provenance_packet":
                return True
    return False


# Per-entry contract from provenance-packet.spec.md "Payload Entry". Validated
# here so a governed claim cannot pass the System/Substrate hard block with a
# packet whose `a[]` entry omits the required v1.4 fields while still carrying a
# consent_ref and a non-packet evidence root.
# Full v1.4 entry contract per docs/specs/provenance-packet.schema.json.
_ENTRY_REQUIRED_STR_FIELDS = (
    "claim_type",
    "truth_status",
    "created_at",
    "human_collision_node",
    "next_action",
)
_ENTRY_REQUIRED_LIST_FIELDS = (
    "source_systems",
    "artifact_refs",
    "evidence_refs",
    "risks",
    "benefits",
)
_SHA256_RE = re.compile(r"^[a-f0-9]{64}\Z")
_SEQUENCE_RE = re.compile(r"^(?:0|[1-9][0-9]*)\Z")
# The envelope's SAID shape: 'E' plus 43 base64url characters. `d` is checked
# against its own recomputation, but `p` was only ever tested for `is None` --
# so a schema-invalid prior like "bogus" or 123 was stringified into the lookup,
# missed, and handed to GAP RECOVERY, which resumed further down the chain and
# could return ok=True carrying only E_PROVENANCE_CHAIN_GAP. A pointer that is
# not a digest is not a hole in the chain; it is a packet that does not name a
# prior at all.
_SAID_RE = re.compile(r"^E[A-Za-z0-9_-]{43}\Z")

# A per-identity chain position, not an arbitrary integer. `int()` accepts any
# decimal, and both this module's gap walk and the anchor's summary enumerate
# the span below the value they are handed -- so a single validly signed packet
# claiming s=1000000000000 turns "produce a verdict" into "iterate a trillion
# times". The live store's deepest chain is single digits.
#
# Defined HERE, in the lower layer, and imported by anchor.py: bounding the
# anchor scan and leaving this walk unbounded is how the same defect got found
# twice in two files.
MAX_SEQUENCE = 1_000_000
# D-A1 (ADR-20). This used to restate the evidence vocabulary as a literal, which
# made it a fourth allow-list nobody knew existed: the v1.5 D3 widening was applied
# to the spec, the schema and claim_schema.EVIDENCE_TYPES, but not here — and this
# is the set actually enforced, so schema-valid packets were rejected. One
# authority now. Widen EVIDENCE_TYPES and every enforcement point follows.
_EVIDENCE_REF_TYPES = EVIDENCE_TYPES


def _payload_entry_errors(entries: list[Any]) -> list[str]:
    errors: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("E_PROVENANCE_ENTRY_INVALID")
            continue
        for field_name in _ENTRY_REQUIRED_STR_FIELDS:
            value = entry.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"E_PROVENANCE_ENTRY_FIELD_MISSING:{field_name}")
        for field_name in _ENTRY_REQUIRED_LIST_FIELDS:
            if not isinstance(entry.get(field_name), list):
                errors.append(f"E_PROVENANCE_ENTRY_FIELD_MISSING:{field_name}")
        # artifactRef shape: {path: non-empty str, sha256: 64-hex}
        for ref in _entry_list_field(entry, "artifact_refs"):
            if (
                not isinstance(ref, dict)
                or not isinstance(ref.get("path"), str)
                or not ref["path"].strip()
                or not isinstance(ref.get("sha256"), str)
                or not _SHA256_RE.match(ref["sha256"])
            ):
                errors.append("E_PROVENANCE_ARTIFACT_REF_INVALID")
        # evidenceRef shape: {type ∈ enum, ref: non-empty str, sha256?: 64-hex}
        for ref in _entry_list_field(entry, "evidence_refs"):
            if (
                not isinstance(ref, dict)
                or ref.get("type") not in _EVIDENCE_REF_TYPES
                or not isinstance(ref.get("ref"), str)
                or not ref["ref"].strip()
            ):
                errors.append("E_PROVENANCE_EVIDENCE_REF_INVALID")
            else:
                sha = ref.get("sha256")
                if sha is not None and not (
                    isinstance(sha, str) and _SHA256_RE.match(sha)
                ):
                    errors.append("E_PROVENANCE_EVIDENCE_REF_INVALID")
    return errors


def _recursive_evidence_errors(
    packet: dict[str, Any],
    *,
    workspace_root: Path,
    provenance_root: Path | None,
    seen: set[str],
    depth: int,
    max_depth: int,
    ignored_chain_position: tuple[Any, Any, Any] | None,
) -> list[str]:
    errors: list[str] = []
    if depth > max_depth:
        return ["E_PROVENANCE_RECURSION_DEPTH_EXCEEDED"]
    # The root requirement is across the whole evidence DAG, not per node: a
    # packet satisfies it if it carries a direct non-packet evidence root OR it
    # references a valid child packet. A child that validates ok necessarily
    # carries a non-packet root in its own subtree (this same check runs for it),
    # so chained/cross-agent handoffs (derived -> prior -> test/spec) are valid.
    subtree_has_root = _has_non_packet_evidence(packet)
    for entry in _payload_entries(packet):
        for ref in _entry_list_field(entry, "evidence_refs"):
            if not isinstance(ref, dict) or ref.get("type") != "provenance_packet":
                continue
            ref_value = ref.get("ref")
            if not ref_value:
                errors.append("E_PROVENANCE_EVIDENCE_REF_INVALID")
                continue
            packet_path = _resolve_workspace_ref(str(ref_value), workspace_root)
            child = validate_packet(
                packet_path,
                workspace_root=workspace_root,
                provenance_root=provenance_root,
                _seen=seen,
                _depth=depth + 1,
                max_depth=max_depth,
                _ignored_chain_position=ignored_chain_position,
            )
            if child.ok:
                subtree_has_root = True
            else:
                errors.extend(child.errors)
    if not subtree_has_root:
        errors.append("E_PROVENANCE_ROOT_REQUIRED")
    return errors


def validate_packet(
    packet_or_path: Path | str | dict[str, Any],
    *,
    workspace_root: Path | str | None = None,
    provenance_root: Path | str | None = None,
    max_depth: int = 8,
    _seen: set[str] | None = None,
    _depth: int = 0,
    # Two independent recursion flags kept side by side (merge 2026-08-17):
    #   _is_ancestor            — ours: this packet is a `p` ancestor, not the one
    #                             under validation. Skips the artifact pass
    #                             entirely per D-B3 (ADR-20); see the note there.
    #   _ignored_chain_position — PR38's: exclude one chain position from the
    #                             duplicate-position check.
    _is_ancestor: bool = False,
    _ignored_chain_position: tuple[Any, Any, Any] | None = None,
    #   _follow_prior           — internal. False validates this packet alone and
    #                             leaves the prior chain to the caller's loop.
    #                             Set only by that loop; see the note there.
    _follow_prior: bool = True,
    #   _position_index         — internal. Chain-position index shared across a
    #                             whole validation so the fork check does not
    #                             re-read every packet per link.
    _position_index: dict[tuple[Any, Any, Any], list[tuple[Path, Any]]] | None = None,
) -> PacketValidation:
    """Validate packet signature, SAID, artifacts, prior chain, and evidence DAG."""

    root = Path(workspace_root or WORKSPACE_ROOT).resolve()
    explicit_provenance_root = (
        Path(provenance_root).resolve() if provenance_root is not None else None
    )
    packet_path: Path | None = None
    if isinstance(packet_or_path, dict):
        packet = packet_or_path
    else:
        packet_path = Path(packet_or_path).resolve()
        if explicit_provenance_root is not None:
            try:
                packet_path.relative_to(explicit_provenance_root)
            except ValueError:
                return PacketValidation(
                    ok=False,
                    errors=["E_PROVENANCE_PACKET_OUTSIDE_ROOT"],
                )
        try:
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return PacketValidation(
                ok=False, errors=[f"E_PROVENANCE_PACKET_UNREADABLE: {exc}"]
            )

    errors: list[str] = []
    warnings: list[str] = []
    digest = packet.get("d")
    # Branch-local copy of the traversal path: cycle detection must reject only
    # cycles on the CURRENT path, not shared evidence reached via sibling
    # branches (two entries citing the same child packet, or a child that is
    # both the `p` prior and an evidence ref). A shared mutable set would leave a
    # sibling's digest behind and mis-flag E_PROVENANCE_CYCLE_DETECTED.
    seen = set(_seen) if _seen is not None else set()
    if isinstance(digest, str):
        if digest in seen:
            return PacketValidation(ok=False, errors=["E_PROVENANCE_CYCLE_DETECTED"])
        seen.add(digest)

    try:
        verify_key = _public_key_from_aid(packet.get("i", ""))
        signatures = packet.get("sigs") or []
        if len(signatures) != 1:
            raise ValueError("E_PROVENANCE_SIGNATURE_COUNT")
        verify_key.verify(_signing_bytes(packet), _signature_bytes(signatures[0]))
    except (BadSignatureError, ValueError, TypeError):
        return PacketValidation(
            ok=False,
            errors=["E_PROVENANCE_SIGNATURE_INVALID"],
            packet_digest=digest if isinstance(digest, str) else None,
            packet=packet,
        )

    expected_digest = _said_digest(packet)
    if digest != expected_digest:
        errors.append("E_PROVENANCE_DIGEST_MISMATCH")

    if not isinstance(packet.get("v"), str) or not packet["v"].startswith(
        VERSION_PREFIX
    ):
        errors.append("E_PROVENANCE_VERSION_INVALID")
    else:
        try:
            expected_len = int(packet["v"][-7:-1], 16)
            if expected_len != len(canonical_bytes(packet)):
                errors.append("E_PROVENANCE_VERSION_LENGTH_MISMATCH")
        except (ValueError, IndexError):
            errors.append("E_PROVENANCE_VERSION_INVALID")

    if packet.get("t") != "prov":
        errors.append("E_PROVENANCE_TYPE_INVALID")
    if not isinstance(packet.get("a"), list) or not packet["a"]:
        errors.append("E_PROVENANCE_PAYLOAD_EMPTY")
    elif not _is_ancestor:
        # Per-entry field contract is checked on the packet under validation
        # only — see the D-B3 note below. A signed ancestor cannot be repaired:
        # correcting a malformed field would break its signature, so enforcing
        # this contract against history means one bad packet blocks its whole
        # chain forever. Found in the wild at chain position 51, which carries a
        # 63-character sha256 (a dropped leading zero) and by itself accounted
        # for every remaining rejection after the artifact pass was scoped.
        errors.extend(_payload_entry_errors(packet["a"]))

    # D-B3 (ADR-20). Artifact refs are checked on the packet under validation
    # only, never on a `p` ancestor.
    #
    # The spec's obligation for `p` is existence and continuity — it says
    # explicitly that the prior pointer "does not consume the evidence-DAG
    # recursion budget" — while this code used to run the full artifact pass on
    # every ancestor, downgrading a missing artifact to a warning but keeping a
    # hash mismatch fatal. That asymmetry killed the spine: editing any file
    # twice permanently invalidated every earlier packet naming it, those
    # packets stayed in the chain, and so every future packet from the same
    # agent failed too. 100% of pilot submissions were rejected this way.
    #
    # An ancestor's artifact refs describe the workspace as it was. The
    # descendant makes no claim about their current state, and nothing
    # downstream reads them as current evidence. Historical artifact state is
    # the audit view's job (D-B1, spec "Audit Disposition"), not the gate's.
    # Ancestors are still validated for signature, SAID, payload shape,
    # evidence DAG and chain continuity — see the walk below.
    if not _is_ancestor:
        errors.extend(_artifact_errors(packet, root))

    prov_root = explicit_provenance_root or _infer_provenance_root(packet_path)
    prior_digest = packet.get("p")
    sequence = packet.get("s")
    sequence_valid = (
        isinstance(sequence, str) and _SEQUENCE_RE.fullmatch(sequence) is not None
    )
    if not sequence_valid:
        errors.append("E_PROVENANCE_SEQUENCE_INVALID")
    elif prior_digest is None and sequence != "0":
        errors.append("E_PROVENANCE_SEQUENCE_DISCONTINUOUS")

    # Shape-check `p` BEFORE anything downstream can interpret its absence as a
    # gap. Ordering matters: gap recovery treats a lookup miss as evidence that
    # the named prior is missing, which is only meaningful if the name was a
    # well-formed digest in the first place.
    prior_shape_invalid = prior_digest is not None and (
        not isinstance(prior_digest, str) or _SAID_RE.fullmatch(prior_digest) is None
    )
    if prior_shape_invalid:
        errors.append("E_PROVENANCE_PRIOR_INVALID")

    if (
        prior_digest is not None
        and _follow_prior
        and not prior_shape_invalid
        and _position_index is None
    ):
        # Build once per validation, here rather than at function entry so a
        # single-packet validation with no chain never pays for the scan.
        # Reused by every ancestor below AND by the fork check; building it per
        # call was what kept the walk quadratic after the recursion fix.
        _position_index = _build_position_index(prov_root)

    if prior_digest is not None and _follow_prior and not prior_shape_invalid:
        # D-B3 addendum (ADR-20, operator-approved 2026-08-24). A hole in the
        # prior chain is DETECTED AND ENUMERATED - not silently truncated, and
        # not blanket-fatal.
        #
        # Both earlier behaviours were wrong in opposite directions. Truncating
        # on an unreachable ancestor let anyone hide a packet by deleting it:
        # remove the file and every descendant validates again, with nothing in
        # the result saying anything was gone. Making it fatal at every depth
        # made concealment impossible but also made an honest chain with a hole
        # permanently unable to submit - and a hole cannot be repaired, because
        # the missing packets are signed and cannot be re-derived. This
        # workspace already had four (identity DkuYPguG98HM2nyR, sequence
        # numbers 3, 36, 37 and 39 absent from a 0..98 range), so the fatal rule
        # rejected 100% of submissions the day it landed.
        #
        # What actually matters for concealment is that the hole be UNDENIABLE.
        # Sequence numbers are per-agent and monotonic, so a deleted packet
        # leaves an arithmetically visible gap whether or not its file exists.
        # The walk therefore consults the per-identity sequence index at every
        # break:
        #
        #   * another packet already occupies the expected position - the child
        #     points somewhere else, which is a fork or a rewrite, and stays
        #     FATAL (E_PROVENANCE_CHAIN_FORK);
        #   * the position is empty - a genuine gap. It is recorded by exact
        #     sequence number, the walk RESUMES below it, and the rest of
        #     history is still verified down to genesis.
        #
        # The chain must still reach sequence 0. A gap plus an unreachable
        # remainder is a truncated chain and stays fatal. What this buys is the
        # honest middle: the deleted content cannot be recovered, but its
        # absence is enumerated in the validation result instead of passing
        # unmentioned, and a chain with a known hole can still carry current
        # work.
        seq_paths, seq_digests = _sequence_index(_position_index)
        gap_sequences: list[int] = []
        reached_genesis = False
        # Derived from the position index above -- no second scan.
        # EVERY path per digest, for the same reason the sequence index keeps
        # every occupant per slot. This was a dict comprehension, so it was
        # last-write-wins: a malformed file copying a genuine ancestor's `d` and
        # sorting after it replaced that ancestor's path, and the walk validated
        # the decoy while the correctly named signed packet sat untouched on
        # disk. Two readers of one scan; fixing only the first was the same
        # mistake twice.
        chain_index: dict[str, list[Path]] = {}
        for entries in (_position_index or {}).values():
            for path, digest in entries:
                if isinstance(digest, str):
                    chain_index.setdefault(digest, []).append(path)

        # The prior chain is walked ITERATIVELY, not recursively.
        #
        # `_depth` is deliberately not incremented for prior links -
        # `max_depth` bounds the evidence DAG, while a linear prior chain is
        # bounded by cycle detection - but that left the chain bounded only by
        # Python's own stack. Measured: ~1.1 stack frames per link, so a
        # ~900-link chain exhausted the default 1000 limit, and a 1000-link
        # honest chain reproducibly raised RecursionError instead of returning
        # a PacketValidation. Provenance validation gates substrate claims, so
        # past that length the gate stopped returning verdicts at all rather
        # than returning a negative one.
        #
        # Each ancestor is validated with `_follow_prior=False` so it checks
        # its own signature/SAID/evidence but leaves its prior to this loop.
        def _cursor_for(digest: str) -> Path | None:
            """Pick the packet for `digest`, preferring one that validates.

            A digest is a SAID over the packet's own content, so a file merely
            claiming one cannot also satisfy it -- which is what makes
            validation the right tiebreaker when several files claim the same
            digest. Fall back to the first claimant so a genuinely broken
            ancestor still reports its own errors instead of vanishing, and to
            the filename lookup for a packet the index never saw.

            This exists as a function because it was written once, for the
            loop's later hops, while the INITIAL cursor kept using the bare
            filename lookup -- and that lookup prefers a root-level
            `<digest>.json` deterministically, so a decoy placed there won the
            first hop every time and an otherwise valid child inherited the
            decoy's errors. One reader of a structure fixed and not its
            sibling, for the third time in this module; the shared helper is
            the fix, not another copy of the selection logic.
            """

            candidates = chain_index.get(digest) or []
            return next(
                (
                    candidate
                    for candidate in candidates
                    if _packet_validates(
                        candidate,
                        workspace_root=root,
                        provenance_root=prov_root,
                        seen=seen,
                        depth=_depth,
                        max_depth=max_depth,
                        ignored_chain_position=_ignored_chain_position,
                        position_index=_position_index,
                    )
                ),
                candidates[0] if candidates else None,
            ) or _find_packet_by_digest(prov_root, digest)

        child_packet: dict[str, Any] = packet
        child_sequence: Any = sequence
        cursor: Path | None = _cursor_for(str(prior_digest))
        walked: set[str] = {str(prior_digest)}
        # True for the one link immediately after a gap, where the adjacency
        # assertion must not fire: non-adjacency IS the gap, already recorded.
        skip_adjacency = False

        while True:
            if cursor is None:
                identity = child_packet.get("i")
                child_number = _walk_sequence(child_sequence)
                if child_number is None:
                    # Refuse before materialising any span. A chain position
                    # that will not parse, or one large enough to size a loop,
                    # is damage or a hostile signer -- and either way the honest
                    # answer is a verdict, not an allocation.
                    errors.append("E_PROVENANCE_SEQUENCE_INVALID")
                    break
                expected_sequence = child_number - 1
                if expected_sequence < 0:
                    # Sequence 0 is genesis and must carry `p: null`. A packet
                    # that names a prior while sitting at 0 is pointing at
                    # something that cannot exist, not reaching the bottom.
                    errors.append("E_PROVENANCE_PRIOR_NOT_FOUND")
                    break
                occupants = seq_digests.get(identity, {}).get(expected_sequence)
                occupant_paths = seq_paths.get(identity, {}).get(expected_sequence)
                if occupants and _slot_is_genuinely_occupied(
                    occupant_paths,
                    workspace_root=root,
                    provenance_root=prov_root,
                    seen=seen,
                    depth=_depth,
                    max_depth=max_depth,
                    ignored_chain_position=_ignored_chain_position,
                    position_index=_position_index,
                ):
                    # Something VALID is signed into that slot and the child
                    # does not point at it. A rewrite or a fork, never a prune.
                    errors.append("E_PROVENANCE_CHAIN_FORK")
                    break
                below = [
                    s for s in seq_paths.get(identity, {}) if s < expected_sequence
                ]
                if not below:
                    # Nothing survives beneath the gap: the chain is truncated
                    # rather than holed, and genesis is unreachable.
                    gap_sequences.append(expected_sequence)
                    errors.append("E_PROVENANCE_PRIOR_NOT_FOUND")
                    break
                resume_sequence = max(below)
                # The WHOLE skipped span, not just its first slot. Consecutive
                # holes (this workspace has 36 and 37 adjacent) otherwise
                # collapsed into a single report and under-stated the loss.
                gap_sequences.extend(range(resume_sequence + 1, expected_sequence + 1))
                # A slot can hold several files now that the index retains every
                # occupant. Resume on one that actually validates; fall back to
                # the first so the walk still reports its errors rather than
                # silently stopping.
                resume_candidates = seq_paths[identity][resume_sequence]
                cursor = next(
                    (
                        candidate
                        for candidate in resume_candidates
                        if _packet_validates(
                            candidate,
                            workspace_root=root,
                            provenance_root=prov_root,
                            seen=seen,
                            depth=_depth,
                            max_depth=max_depth,
                            ignored_chain_position=_ignored_chain_position,
                            position_index=_position_index,
                        )
                    ),
                    resume_candidates[0],
                )
                child_packet = {"i": identity, "s": resume_sequence + 1}
                child_sequence = resume_sequence + 1
                skip_adjacency = True
                continue

            prior_result = validate_packet(
                cursor,
                workspace_root=root,
                provenance_root=prov_root,
                _seen=seen,
                _depth=_depth,
                max_depth=max_depth,
                _is_ancestor=True,
                _ignored_chain_position=_ignored_chain_position,
                _follow_prior=False,
                _position_index=_position_index,
            )
            if not prior_result.ok:
                errors.extend(prior_result.errors)
            warnings.extend(prior_result.warnings)

            # Per-agent chain continuity: the prior must belong to the same
            # author and its sequence must directly precede its child. Without
            # this, a signed packet could point at another agent's packet or
            # skip/fork its sequence while still validating.
            prior_packet = prior_result.packet or {}
            if prior_packet.get("i") != child_packet.get("i"):
                errors.append("E_PROVENANCE_PRIOR_AGENT_MISMATCH")
            if skip_adjacency:
                skip_adjacency = False
            else:
                prior_sequence = _walk_sequence(prior_packet.get("s"))
                child_number = _walk_sequence(child_sequence)
                if prior_sequence is None or child_number is None:
                    # Same parser as the branch above. This one reaches the very
                    # same expansion -- range(prior + 1, child) -- by a different
                    # route, and the bound had been added only to the other.
                    errors.append("E_PROVENANCE_SEQUENCE_INVALID")
                else:
                    if prior_sequence >= child_number:
                        # Sequence must strictly decrease toward genesis. A
                        # prior at or above its child is a loop or a rewrite,
                        # and no amount of enumeration makes that walkable.
                        errors.append("E_PROVENANCE_SEQUENCE_DISCONTINUOUS")
                    elif prior_sequence < child_number - 1:
                        # The prior EXISTS but sits further back than one step.
                        # Whether that is acceptable turns on ONE question: are
                        # the skipped slots empty, or occupied?
                        #
                        # Empty means those packets are gone. Nothing can point
                        # at what does not exist, so this is the same
                        # unavoidable loss as an unreachable prior: enumerate it
                        # and keep walking.
                        #
                        # Occupied means the child skipped a packet sitting
                        # right there on disk. There is no honest reason to do
                        # that -- the link was available and was not taken --
                        # and accepting it would turn the chain into a partial
                        # order any writer could route around. Fatal, and
                        # deliberately so. The rule is: enumerate what is LOST,
                        # refuse what is merely BYPASSED.
                        skipped = range(prior_sequence + 1, child_number)
                        # Same standard as the gap branch: a slot counts as
                        # occupied only if something VALID sits in it.
                        occupied = [
                            s
                            for s in skipped
                            if _slot_is_genuinely_occupied(
                                seq_paths.get(child_packet.get("i"), {}).get(s),
                                workspace_root=root,
                                provenance_root=prov_root,
                                seen=seen,
                                depth=_depth,
                                max_depth=max_depth,
                                ignored_chain_position=_ignored_chain_position,
                                position_index=_position_index,
                            )
                        ]
                        if occupied:
                            errors.append("E_PROVENANCE_SEQUENCE_DISCONTINUOUS")
                        else:
                            gap_sequences.extend(skipped)

            next_digest = prior_packet.get("p")
            if next_digest is None:
                # Genesis has no prior. It must also be sequence 0, or the
                # chain claims to start somewhere it did not.
                # Third reader of a sequence in this walk. It only compares
                # against 0, so it cannot size a loop -- but routing it through
                # the same parser is the point: a branch that parses its own is
                # exactly where the bound went missing the first two times.
                genesis_sequence = _walk_sequence(prior_packet.get("s"))
                if genesis_sequence is None:
                    errors.append("E_PROVENANCE_SEQUENCE_INVALID")
                elif genesis_sequence != 0:
                    errors.append("E_PROVENANCE_SEQUENCE_DISCONTINUOUS")
                else:
                    reached_genesis = True
                break
            key = str(next_digest)
            if key in walked:
                # Defensive: a cycle among priors would otherwise spin forever
                # now that the stack no longer bounds this walk.
                errors.append("E_PROVENANCE_PRIOR_CYCLE")
                break
            walked.add(key)
            child_packet = prior_packet
            child_sequence = prior_packet.get("s")
            cursor = _cursor_for(key)

        if gap_sequences:
            # Enumerated, not summarised. An auditor reading this result can
            # name exactly which packets are missing and go looking for them.
            warnings.append(
                "E_PROVENANCE_CHAIN_GAP:"
                + ",".join(str(s) for s in sorted(gap_sequences))
            )
        if not reached_genesis and not errors:
            errors.append("E_PROVENANCE_PRIOR_NOT_FOUND")

    # Evidence-DAG recursion, likewise depth-0 only (D-B3). An ancestor's
    # evidence DAG resolves packet files that may since have been pruned,
    # relocated, or written before a contract change; walking it from a
    # descendant re-litigates history the descendant is not asserting.
    if not _is_ancestor:
        errors.extend(
            _recursive_evidence_errors(
                packet,
                workspace_root=root,
                provenance_root=prov_root,
                seen=seen,
                depth=_depth,
                max_depth=max_depth,
                ignored_chain_position=_ignored_chain_position,
            )
        )
        # Depth 0 only: an ancestor's consent state is history, and re-reporting
        # it on every descendant would bury the packet actually under
        # submission. A governed claim now carries a visible marker that its
        # consent reference was never resolved, instead of the gate silently
        # accepting any non-empty string.
        warnings.extend(consent_resolution_problems(packet))

    chain_position = (packet.get("i"), packet.get("p"), packet.get("s"))
    if (
        not errors
        and chain_position != _ignored_chain_position
        and _has_valid_same_position_competitor(
            packet,
            packet_path=packet_path,
            workspace_root=root,
            provenance_root=prov_root,
            max_depth=max_depth,
            position_index=_position_index,
        )
    ):
        errors.append("E_PROVENANCE_CHAIN_FORK")

    return PacketValidation(
        ok=not errors,
        errors=sorted(set(errors)),
        warnings=sorted(set(warnings)),
        packet_digest=digest if isinstance(digest, str) else None,
        narrative_lines=narrative_lines(packet) if not errors else [],
        packet=packet,
    )


def validated_non_packet_evidence_refs(
    packet_or_path: Path | str | dict[str, Any],
    *,
    workspace_root: Path | str | None = None,
    provenance_root: Path | str | None = None,
    max_depth: int = 8,
    max_refs: int = 32,
) -> tuple[list[dict[str, str]], bool]:
    """Return stable validated non-packet metadata and whether it was truncated."""

    root = Path(workspace_root or WORKSPACE_ROOT).resolve()
    root_path = None if isinstance(packet_or_path, dict) else Path(packet_or_path)
    result = validate_packet(
        packet_or_path,
        workspace_root=root,
        provenance_root=provenance_root,
        max_depth=max_depth,
    )
    if not result.ok:
        raise ValueError("; ".join(result.errors))

    packet = result.packet or {}
    resolved_provenance_root = (
        Path(provenance_root)
        if provenance_root is not None
        else _infer_provenance_root(root_path)
    )
    refs: list[dict[str, str]] = []
    seen_refs: set[tuple[str, str, str]] = set()
    truncated = False
    active_digests: set[str] = set()
    visited_packets: set[str] = set()
    ref_limit = max(0, max_refs)

    def walk(current: dict[str, Any], current_path: Path | None, depth: int) -> None:
        nonlocal truncated
        if depth > max_depth:
            raise ValueError("E_PROVENANCE_RECURSION_DEPTH_EXCEEDED")
        digest = current.get("d")
        if not isinstance(digest, str):
            raise ValueError("E_PROVENANCE_DIGEST_MISMATCH")
        if digest in active_digests:
            raise ValueError("E_PROVENANCE_CYCLE_DETECTED")
        if digest in visited_packets:
            return

        active_digests.add(digest)
        visited_packets.add(digest)
        try:
            for entry in current.get("a", []) or []:
                for evidence_ref in entry.get("evidence_refs", []) or []:
                    if not isinstance(evidence_ref, dict):
                        continue
                    if evidence_ref.get("type") != "provenance_packet":
                        metadata = {
                            "type": str(evidence_ref["type"]),
                            "ref": str(evidence_ref["ref"]),
                        }
                        if isinstance(evidence_ref.get("sha256"), str):
                            metadata["sha256"] = evidence_ref["sha256"]
                        metadata_key = (
                            metadata["type"],
                            metadata["ref"],
                            metadata.get("sha256", ""),
                        )
                        if metadata_key in seen_refs:
                            continue
                        seen_refs.add(metadata_key)
                        if len(refs) >= ref_limit:
                            truncated = True
                            continue
                        refs.append(metadata)
                        continue

                    child_path = _resolve_workspace_ref(str(evidence_ref["ref"]), root)
                    child_result = validate_packet(
                        child_path,
                        workspace_root=root,
                        provenance_root=resolved_provenance_root,
                        max_depth=max_depth,
                    )
                    if not child_result.ok:
                        raise ValueError("; ".join(child_result.errors))
                    walk(child_result.packet or {}, child_path, depth + 1)
        finally:
            active_digests.remove(digest)

    walk(packet, root_path, 0)
    return refs, truncated


CONSENT_UNRESOLVED = "E_CONSENT_GATE_UNRESOLVED"


def entry_has_consent(entry: dict[str, Any]) -> bool:
    """Return True when a payload entry carries a consent decision reference.

    WHAT THIS DOES NOT DO: resolve the hash. It checks that
    `consent_ref.decision_action_hash` is a non-empty string and nothing more.
    Any non-empty string satisfies it -- there is no lookup against a real
    `ConsentDecision` action, no existence check, no signature check.

    That is the whole consent gate today. A governed System/Substrate claim is
    admitted on the strength of a string somebody typed. Four independent audits
    rated this Critical; it is ADR-12's to close, and until it is closed the
    word "governed" in this codebase means "carries a consent-shaped field",
    not "was consented to".

    The boolean contract is deliberately unchanged -- packages/metacoordinator_mcp
    depends on it and is under a do-not-modify rule. `consent_resolution_problems`
    below is the honest companion: it reports the unresolved state so a caller
    that wants to know can, rather than the hole staying silent.
    """

    consent_ref = entry.get("consent_ref")
    if not isinstance(consent_ref, dict):
        return False
    decision_hash = consent_ref.get("decision_action_hash")
    return isinstance(decision_hash, str) and bool(decision_hash.strip())


def consent_resolution_problems(packet: dict[str, Any]) -> list[str]:
    """Report that a packet's consent references were never resolved.

    Returns one `E_CONSENT_GATE_UNRESOLVED` marker per entry claiming consent.
    Emitted as a WARNING rather than an error on purpose: making it fatal today
    would block every governed claim in the repository, which is the same
    mistake as `b0de2fe` -- correct by the letter of the contract, and it bricks
    the system. The point is that the hole stops being invisible.

    Remove this function when ADR-12 lands real resolution. Its presence in a
    validation result is the marker that ADR-12 has NOT landed.
    """

    problems: list[str] = []
    for index, entry in enumerate(packet.get("a", []) or []):
        if not entry_has_consent(entry):
            continue
        consent_ref = entry.get("consent_ref") or {}
        digest = str(consent_ref.get("decision_action_hash", "")).strip()
        problems.append(
            f"{CONSENT_UNRESOLVED}: a[{index}].consent_ref.decision_action_hash "
            f"{digest[:24]!r} was accepted without being resolved against any "
            f"ConsentDecision record (ADR-12 unimplemented)"
        )
    return problems


def packet_has_consent(packet: dict[str, Any]) -> bool:
    """Return True when any payload entry carries a consent decision reference."""

    return any(entry_has_consent(entry) for entry in packet.get("a", []) or [])


def narrative_lines(packet: dict[str, Any]) -> list[str]:
    """Project packet entries into concise human-audit lines."""

    lines: list[str] = []
    agent = str(packet.get("i", "unknown-agent"))
    for entry in packet.get("a", []) or []:
        created_at = entry.get("created_at", "unknown-time")
        claim_type = entry.get("claim_type", "unknown")
        artifacts = entry.get("artifact_refs") or []
        if artifacts and isinstance(artifacts[0], dict):
            target = artifacts[0].get("path", "<no-artifact>")
        else:
            target = "<no-artifact>"
        evidence_count = len(entry.get("evidence_refs") or [])
        governed = "yes" if entry_has_consent(entry) else "no"
        lines.append(
            f"[{created_at}] {agent} \u25c7 {claim_type} -> {target} "
            f"\u00b7 evidence: {evidence_count} refs "
            f"\u00b7 governed: {governed} \u00b7 signature: ok"
        )
    return lines
