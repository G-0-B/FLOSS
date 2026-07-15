"""Append-only continuation checkpoints for PR38 salvage capsules."""

from __future__ import annotations

from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import BinaryIO, Iterator, Mapping, Sequence

from .models import canonical_json_bytes
from .seal import (
    CapsuleVerificationError,
    _assert_regular_metadata,
    _file_identity,
    _locked_directory,
    _node_identity,
    _validated_file_state,
)

_HEX_40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA_VERSION = "1.0.0"
_RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "sequence",
        "previous_digest",
        "digest",
        "state_id",
        "phase",
        "input_shas",
        "capsule_root",
        "manifest_digest",
        "completed_actions",
        "blockers",
        "human_decisions",
        "next_safe_command",
        "recovery_command",
    }
)


class CheckpointIntegrityError(RuntimeError):
    """The checkpoint chain is missing, unsafe, or internally inconsistent."""


@dataclass(frozen=True)
class Checkpoint:
    """One append-only continuation record bound to one salvage state."""

    schema_version: str
    sequence: int
    previous_digest: str | None
    state_id: str
    phase: str
    input_shas: Mapping[str, str]
    capsule_root: str
    manifest_digest: str | None
    completed_actions: Sequence[str]
    blockers: Sequence[str]
    human_decisions: Sequence[str]
    next_safe_command: str
    recovery_command: str
    digest: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != _SCHEMA_VERSION:
            raise ValueError(f"schema_version must be {_SCHEMA_VERSION}")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool):
            raise ValueError("sequence must be an integer")
        if self.sequence < 0:
            raise ValueError("sequence must be >= 0")
        if self.sequence == 0:
            if self.previous_digest is not None:
                raise ValueError("genesis checkpoint previous_digest must be null")
        elif not _is_hex_digest(self.previous_digest):
            raise ValueError("previous_digest must be lowercase SHA-256")
        _require_nonempty_string("state_id", self.state_id)
        _require_nonempty_string("phase", self.phase)
        object.__setattr__(self, "input_shas", _normalize_input_shas(self.input_shas))
        if not _is_hex_digest(self.capsule_root):
            raise ValueError("capsule_root must be lowercase SHA-256")
        if self.manifest_digest is not None and not _is_hex_digest(self.manifest_digest):
            raise ValueError("manifest_digest must be null or lowercase SHA-256")
        object.__setattr__(
            self,
            "completed_actions",
            _normalize_string_sequence("completed_actions", self.completed_actions),
        )
        object.__setattr__(
            self,
            "blockers",
            _normalize_string_sequence("blockers", self.blockers),
        )
        object.__setattr__(
            self,
            "human_decisions",
            _normalize_string_sequence("human_decisions", self.human_decisions),
        )
        _require_nonempty_string("next_safe_command", self.next_safe_command)
        _require_nonempty_string("recovery_command", self.recovery_command)
        expected_digest = _checkpoint_digest(_payload_dict(self))
        if self.digest is None:
            object.__setattr__(self, "digest", expected_digest)
        elif not _is_hex_digest(self.digest):
            raise ValueError("digest must be lowercase SHA-256")
        elif self.digest != expected_digest:
            raise ValueError("digest does not match checkpoint payload")


def append_checkpoint(path: Path, checkpoint: Checkpoint) -> None:
    """Append *checkpoint* to *path* or create a new genesis chain."""

    if not isinstance(checkpoint, Checkpoint):
        raise TypeError("checkpoint must be a Checkpoint")
    target = Path(path)
    parent = _parent_directory(target)
    try:
        with _locked_directory(parent):
            if target.exists():
                with _open_checkpoint_stream(target, create=False) as stream:
                    existing = _read_stream_bytes(stream, target)
                    chain = _parse_chain(existing)
                    _assert_append_allowed(chain[-1], checkpoint)
                    _append_bytes(
                        stream,
                        target,
                        canonical_json_bytes(checkpoint),
                        expected_size=len(existing),
                    )
                    after = _parse_chain(_read_stream_bytes(stream, target))
                    if len(after) != len(chain) + 1 or after[-1] != checkpoint:
                        raise CheckpointIntegrityError(
                            "checkpoint append verification failed"
                        )
                return

            if checkpoint.sequence != 0 or checkpoint.previous_digest is not None:
                raise CheckpointIntegrityError(
                    "genesis append requires sequence 0 and null previous_digest"
                )
            with _open_checkpoint_stream(target, create=True) as stream:
                _append_bytes(
                    stream,
                    target,
                    canonical_json_bytes(checkpoint),
                    expected_size=0,
                )
                after = _parse_chain(_read_stream_bytes(stream, target))
                if after != [checkpoint]:
                    raise CheckpointIntegrityError(
                        "genesis checkpoint append verification failed"
                    )
    except CapsuleVerificationError as exc:
        raise CheckpointIntegrityError(str(exc)) from exc


def load_latest_checkpoint(path: Path) -> Checkpoint:
    """Load and verify the latest record from a checkpoint JSONL file."""

    target = Path(path)
    parent = _parent_directory(target)
    try:
        with _locked_directory(parent):
            if not target.exists():
                raise FileNotFoundError(target)
            with _open_checkpoint_stream(target, create=False) as stream:
                return _parse_chain(_read_stream_bytes(stream, target))[-1]
    except CapsuleVerificationError as exc:
        raise CheckpointIntegrityError(str(exc)) from exc


def _parent_directory(path: Path) -> Path:
    parent = path.parent if path.parent != Path("") else Path(".")
    if not parent.exists():
        raise FileNotFoundError(parent)
    return parent


def _require_nonempty_string(field_name: str, value: object) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")


def _normalize_input_shas(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("input_shas must be an object")
    normalized: dict[str, str] = {}
    for key, digest in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("input_shas keys must be non-empty strings")
        if not isinstance(digest, str) or not _HEX_40_OR_64.fullmatch(digest):
            raise ValueError("input_shas values must be lowercase git or SHA-256 digests")
        normalized[key] = digest
    return normalized


def _normalize_string_sequence(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be an array of strings")
    normalized = tuple(value)
    if any(not isinstance(item, str) for item in normalized):
        raise ValueError(f"{field_name} must be an array of strings")
    return normalized


def _is_hex_digest(value: object) -> bool:
    return isinstance(value, str) and _HEX_64.fullmatch(value) is not None


def _payload_dict(checkpoint: Checkpoint) -> dict[str, object]:
    return {
        "schema_version": checkpoint.schema_version,
        "sequence": checkpoint.sequence,
        "previous_digest": checkpoint.previous_digest,
        "state_id": checkpoint.state_id,
        "phase": checkpoint.phase,
        "input_shas": dict(checkpoint.input_shas),
        "capsule_root": checkpoint.capsule_root,
        "manifest_digest": checkpoint.manifest_digest,
        "completed_actions": checkpoint.completed_actions,
        "blockers": checkpoint.blockers,
        "human_decisions": checkpoint.human_decisions,
        "next_safe_command": checkpoint.next_safe_command,
        "recovery_command": checkpoint.recovery_command,
    }


def _record_dict(checkpoint: Checkpoint) -> dict[str, object]:
    record = _payload_dict(checkpoint)
    record["digest"] = checkpoint.digest
    return record


def _checkpoint_digest(payload: dict[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def _checkpoint_from_record(record: dict[str, object]) -> Checkpoint:
    if set(record) != _RECORD_FIELDS:
        raise CheckpointIntegrityError("checkpoint record fields do not match contract")
    try:
        return Checkpoint(
            schema_version=record["schema_version"],
            sequence=record["sequence"],
            previous_digest=record["previous_digest"],
            state_id=record["state_id"],
            phase=record["phase"],
            input_shas=record["input_shas"],
            capsule_root=record["capsule_root"],
            manifest_digest=record["manifest_digest"],
            completed_actions=record["completed_actions"],
            blockers=record["blockers"],
            human_decisions=record["human_decisions"],
            next_safe_command=record["next_safe_command"],
            recovery_command=record["recovery_command"],
            digest=record["digest"],
        )
    except (TypeError, ValueError) as exc:
        raise CheckpointIntegrityError(str(exc)) from exc


def _parse_chain(raw: bytes) -> list[Checkpoint]:
    if not raw:
        raise CheckpointIntegrityError("checkpoint file is empty")
    if not raw.endswith(b"\n"):
        raise CheckpointIntegrityError("checkpoint file is truncated")
    checkpoints: list[Checkpoint] = []
    bindings: dict[str, object] | None = None
    for index, line in enumerate(raw.splitlines(keepends=True)):
        if line == b"\n":
            raise CheckpointIntegrityError("checkpoint file contains a blank line")
        if not line.endswith(b"\n"):
            raise CheckpointIntegrityError("checkpoint file is truncated")
        try:
            parsed = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CheckpointIntegrityError(
                "checkpoint record is not valid canonical JSON"
            ) from exc
        if not isinstance(parsed, dict):
            raise CheckpointIntegrityError("checkpoint record must be a JSON object")
        checkpoint = _checkpoint_from_record(parsed)
        if canonical_json_bytes(_record_dict(checkpoint)) != line:
            raise CheckpointIntegrityError("checkpoint record is not canonical JSON")
        if checkpoint.sequence != index:
            raise CheckpointIntegrityError("checkpoint sequence is not contiguous")
        if index == 0:
            if checkpoint.previous_digest is not None:
                raise CheckpointIntegrityError(
                    "genesis checkpoint previous_digest must be null"
                )
            bindings = {
                "state_id": checkpoint.state_id,
                "input_shas": dict(checkpoint.input_shas),
                "capsule_root": checkpoint.capsule_root,
                "manifest_digest": checkpoint.manifest_digest,
            }
        else:
            previous = checkpoints[-1]
            if checkpoint.previous_digest != previous.digest:
                raise CheckpointIntegrityError(
                    "checkpoint previous_digest does not match prior digest"
                )
            assert bindings is not None
            if checkpoint.state_id != bindings["state_id"]:
                raise CheckpointIntegrityError("checkpoint state_id drifted across chain")
            if dict(checkpoint.input_shas) != bindings["input_shas"]:
                raise CheckpointIntegrityError(
                    "checkpoint input_shas drifted across chain"
                )
            if checkpoint.capsule_root != bindings["capsule_root"]:
                raise CheckpointIntegrityError(
                    "checkpoint capsule_root drifted across chain"
                )
            if checkpoint.manifest_digest != bindings["manifest_digest"]:
                raise CheckpointIntegrityError(
                    "checkpoint manifest_digest drifted across chain"
                )
        checkpoints.append(checkpoint)
    return checkpoints


def _assert_append_allowed(previous: Checkpoint, candidate: Checkpoint) -> None:
    expected_sequence = previous.sequence + 1
    if candidate.sequence != expected_sequence:
        raise CheckpointIntegrityError("checkpoint sequence does not extend the chain")
    if candidate.previous_digest != previous.digest:
        raise CheckpointIntegrityError(
            "checkpoint previous_digest does not extend the chain"
        )
    for field_name in ("state_id", "capsule_root", "manifest_digest"):
        if getattr(candidate, field_name) != getattr(previous, field_name):
            raise CheckpointIntegrityError(
                f"checkpoint {field_name} cannot drift across a chain"
            )
    if dict(candidate.input_shas) != dict(previous.input_shas):
        raise CheckpointIntegrityError(
            "checkpoint input_shas cannot drift across a chain"
        )


@contextmanager
def _open_checkpoint_stream(path: Path, *, create: bool) -> Iterator[BinaryIO]:
    if not create:
        _validated_file_state(path)
    flags = getattr(os, "O_BINARY", 0)
    if os.name != "nt":
        flags |= os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
        if create:
            flags |= os.O_CREAT | os.O_EXCL
        descriptor = os.open(path, flags, 0o600)
        try:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX)
        except Exception:
            os.close(descriptor)
            raise
    else:
        from ctypes import wintypes
        import msvcrt

        create_file = ctypes.windll.kernel32.CreateFileW
        create_file.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        create_file.restype = wintypes.HANDLE
        handle = create_file(
            str(path),
            0x80000000 | 0x40000000,
            0x00000001,
            None,
            1 if create else 3,
            0x00200000 | 0x08000000,
            None,
        )
        invalid_handle = ctypes.c_void_p(-1).value
        if handle == invalid_handle:
            raise CheckpointIntegrityError(
                "checkpoint file cannot be opened safely"
            ) from ctypes.WinError()
        try:
            descriptor = msvcrt.open_osfhandle(handle, getattr(os, "O_BINARY", 0))
        except OSError:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise
    stream = os.fdopen(descriptor, "r+b", closefd=True)
    try:
        if create:
            created = _validated_file_state(path)
            handle_state = os.fstat(stream.fileno())
            _assert_regular_metadata(handle_state)
            if _node_identity(created) != _node_identity(handle_state):
                raise CheckpointIntegrityError(
                    "checkpoint file changed while acquiring append handle"
                )
        else:
            before = _validated_file_state(path)
            handle_state = os.fstat(stream.fileno())
            _assert_regular_metadata(handle_state)
            if _node_identity(before) != _node_identity(handle_state):
                raise CheckpointIntegrityError(
                    "checkpoint file changed while acquiring append handle"
                )
        yield stream
    finally:
        stream.close()


def _read_stream_bytes(stream: BinaryIO, path: Path) -> bytes:
    path_before = _validated_file_state(path)
    stream.seek(0)
    handle_before = os.fstat(stream.fileno())
    _assert_regular_metadata(handle_before)
    if _node_identity(path_before) != _node_identity(handle_before):
        raise CheckpointIntegrityError("checkpoint file changed before read")
    payload = stream.read()
    handle_after = os.fstat(stream.fileno())
    path_after = _validated_file_state(path)
    if (
        _file_identity(path_before) != _file_identity(handle_before)
        or _file_identity(handle_before) != _file_identity(handle_after)
        or _file_identity(handle_after) != _file_identity(path_after)
    ):
        raise CheckpointIntegrityError("checkpoint file changed while reading")
    return payload


def _append_bytes(
    stream: BinaryIO,
    path: Path,
    content: bytes,
    *,
    expected_size: int,
) -> None:
    handle_before = os.fstat(stream.fileno())
    _assert_regular_metadata(handle_before)
    if handle_before.st_size != expected_size:
        raise CheckpointIntegrityError("checkpoint file size changed before append")
    stream.seek(0, os.SEEK_END)
    if stream.tell() != expected_size:
        raise CheckpointIntegrityError("checkpoint file changed before append")
    stream.write(content)
    stream.flush()
    os.fsync(stream.fileno())
    handle_after = os.fstat(stream.fileno())
    if handle_after.st_size != expected_size + len(content):
        raise CheckpointIntegrityError("checkpoint append was partial")
    path_after = _validated_file_state(path)
    if _file_identity(handle_after) != _file_identity(path_after):
        raise CheckpointIntegrityError("checkpoint file changed during append")


__all__ = [
    "Checkpoint",
    "CheckpointIntegrityError",
    "append_checkpoint",
    "load_latest_checkpoint",
]
