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

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

VERSION_PREFIX = "FLOSSI10JSON"
VERSION_PLACEHOLDER = f"{VERSION_PREFIX}000000_"
SAID_PLACEHOLDER = "#" * 44
SIGNATURE_PLACEHOLDER = "0B" + ("A" * 86)

_AUTO_PRIOR = object()
_LOCK_TIMEOUT_SECONDS = 5.0


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
    public_path.write_text(_b64url_encode(bytes(verify_key)) + "\n", encoding="utf-8")
    aid_path.write_text(aid + "\n", encoding="utf-8")
    return Identity(signing_key=signing_key, verify_key=verify_key, aid=aid)


def _acquire_lock(lock_path: Path) -> str:
    deadline = time.monotonic() + _LOCK_TIMEOUT_SECONDS
    while True:
        token = _b64url_encode(os.urandom(18))
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            with lock_path.open("x", encoding="utf-8") as f:
                f.write(token)
            return token
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"timed out acquiring provenance lock {lock_path}")
            time.sleep(0.05)


def _release_lock(lock_path: Path, token: str) -> None:
    try:
        if lock_path.read_text(encoding="utf-8") == token:
            lock_path.unlink(missing_ok=True)
    except FileNotFoundError:
        pass


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
        packet_path.write_bytes(canonical_bytes(packet) + b"\n")
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


def _public_key_from_aid(aid: str) -> VerifyKey:
    if not isinstance(aid, str) or not aid.startswith(("D", "B")):
        raise ValueError("E_PROVENANCE_BAD_AID")
    return VerifyKey(_b64url_decode(aid[1:]))


def _signature_bytes(signature: str) -> bytes:
    if not isinstance(signature, str) or not signature.startswith("0B"):
        raise ValueError("E_PROVENANCE_BAD_SIGNATURE")
    return _b64url_decode(signature[2:])


def _artifact_errors(packet: dict[str, Any], workspace_root: Path) -> list[str]:
    errors: list[str] = []
    for entry in packet.get("a", []):
        for ref in entry.get("artifact_refs", []) or []:
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
    for entry in packet.get("a", []):
        for ref in entry.get("evidence_refs", []) or []:
            if isinstance(ref, dict) and ref.get("type") != "provenance_packet":
                return True
    return False


def _recursive_evidence_errors(
    packet: dict[str, Any],
    *,
    workspace_root: Path,
    provenance_root: Path | None,
    seen: set[str],
    depth: int,
    max_depth: int,
) -> list[str]:
    errors: list[str] = []
    if depth > max_depth:
        return ["E_PROVENANCE_RECURSION_DEPTH_EXCEEDED"]
    for entry in packet.get("a", []):
        for ref in entry.get("evidence_refs", []) or []:
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
            )
            if not child.ok:
                errors.extend(child.errors)
    if not _has_non_packet_evidence(packet):
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
) -> PacketValidation:
    """Validate packet signature, SAID, artifacts, prior chain, and evidence DAG."""

    root = Path(workspace_root or WORKSPACE_ROOT).resolve()
    packet_path: Path | None = None
    if isinstance(packet_or_path, dict):
        packet = packet_or_path
    else:
        packet_path = Path(packet_or_path)
        try:
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return PacketValidation(
                ok=False, errors=[f"E_PROVENANCE_PACKET_UNREADABLE: {exc}"]
            )

    errors: list[str] = []
    digest = packet.get("d")
    seen = _seen if _seen is not None else set()
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

    errors.extend(_artifact_errors(packet, root))

    prov_root = (
        Path(provenance_root)
        if provenance_root is not None
        else _infer_provenance_root(packet_path)
    )
    prior_digest = packet.get("p")
    if prior_digest is not None:
        prior_path = _find_packet_by_digest(prov_root, str(prior_digest))
        if prior_path is None:
            errors.append("E_PROVENANCE_PRIOR_NOT_FOUND")
        else:
            prior_result = validate_packet(
                prior_path,
                workspace_root=root,
                provenance_root=prov_root,
                _seen=seen,
                _depth=_depth,
                max_depth=max_depth,
            )
            if not prior_result.ok:
                errors.extend(prior_result.errors)

    errors.extend(
        _recursive_evidence_errors(
            packet,
            workspace_root=root,
            provenance_root=prov_root,
            seen=seen,
            depth=_depth,
            max_depth=max_depth,
        )
    )

    return PacketValidation(
        ok=not errors,
        errors=sorted(set(errors)),
        packet_digest=digest if isinstance(digest, str) else None,
        narrative_lines=narrative_lines(packet) if not errors else [],
        packet=packet,
    )


def entry_has_consent(entry: dict[str, Any]) -> bool:
    """Return True when a payload entry carries a consent decision reference."""

    consent_ref = entry.get("consent_ref")
    if not isinstance(consent_ref, dict):
        return False
    decision_hash = consent_ref.get("decision_action_hash")
    return isinstance(decision_hash, str) and bool(decision_hash.strip())


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
