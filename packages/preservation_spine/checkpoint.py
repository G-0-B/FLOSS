"""Append-only continuation checkpoints for preservation capsules.

Built for the PR38 salvage in 2026-07, but nothing here is PR-specific:
the six-plane contract applies to any risky repository operation.
"""

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
    _read_regular_bytes,
    _validated_file_state,
)

_HEX_40_OR_64 = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
_SCHEMA_VERSION = "1.0.0"
_INTENT_NAME_TEMPLATE = ".{name}.append-intent.json"
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
        "verification_digest",
        "completed_actions",
        "blockers",
        "human_decisions",
        "next_safe_command",
        "recovery_command",
    }
)
_INTENT_FIELDS = frozenset(
    {
        "schema_version",
        "checkpoint_file",
        "committed_size",
        "committed_sha256",
        "pending_record",
        "pending_record_sha256",
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
    verification_digest: str | None
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
        _require_operator_string("state_id", self.state_id)
        _require_operator_string("phase", self.phase)
        object.__setattr__(self, "input_shas", _normalize_input_shas(self.input_shas))
        if not _is_hex_digest(self.capsule_root):
            raise ValueError("capsule_root must be lowercase SHA-256")
        if self.manifest_digest is not None and not _is_hex_digest(
            self.manifest_digest
        ):
            raise ValueError("manifest_digest must be null or lowercase SHA-256")
        if self.verification_digest is not None and not _is_hex_digest(
            self.verification_digest
        ):
            raise ValueError("verification_digest must be null or lowercase SHA-256")
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
        _require_operator_string("next_safe_command", self.next_safe_command)
        _require_operator_string("recovery_command", self.recovery_command)
        expected_digest = _checkpoint_digest(_payload_dict(self))
        if self.digest is None:
            object.__setattr__(self, "digest", expected_digest)
        elif not _is_hex_digest(self.digest):
            raise ValueError("digest must be lowercase SHA-256")
        elif self.digest != expected_digest:
            raise ValueError("digest does not match checkpoint payload")


@dataclass(frozen=True)
class _PendingAppendIntent:
    schema_version: str
    checkpoint_file: str
    committed_size: int
    committed_sha256: str
    pending_checkpoint: Checkpoint
    pending_record_sha256: str


def append_checkpoint(path: Path, checkpoint: Checkpoint) -> None:
    """Append *checkpoint* to *path* or create a new genesis chain."""

    if not isinstance(checkpoint, Checkpoint):
        raise TypeError("checkpoint must be a Checkpoint")
    target = Path(path)
    parent = _parent_directory(target)
    try:
        with _locked_directory(parent):
            _recover_pending_append(target)
            if target.exists():
                with _open_checkpoint_stream(target, create=False) as stream:
                    existing = _read_stream_bytes(stream, target)
                    chain = _parse_chain(existing)
                    _assert_append_allowed(chain[-1], checkpoint)
                    _append_with_intent(
                        stream,
                        target,
                        checkpoint,
                        committed_bytes=existing,
                    )
                    return

            if checkpoint.sequence != 0 or checkpoint.previous_digest is not None:
                raise CheckpointIntegrityError(
                    "genesis append requires sequence 0 and null previous_digest"
                )
            with _open_checkpoint_stream(target, create=True) as stream:
                _append_with_intent(
                    stream,
                    target,
                    checkpoint,
                    committed_bytes=b"",
                )
    except CapsuleVerificationError as exc:
        raise CheckpointIntegrityError(str(exc)) from exc


def load_latest_checkpoint(path: Path) -> Checkpoint:
    """Load and verify the latest record from a checkpoint JSONL file."""

    target = Path(path)
    parent = _parent_directory(target)
    try:
        with _locked_directory(parent):
            _recover_pending_append(target)
            if not target.exists():
                raise FileNotFoundError(target)
            with _open_checkpoint_stream(target, create=False) as stream:
                return _parse_chain(_read_stream_bytes(stream, target))[-1]
    except CapsuleVerificationError as exc:
        raise CheckpointIntegrityError(str(exc)) from exc


def _append_with_intent(
    stream: BinaryIO,
    path: Path,
    checkpoint: Checkpoint,
    *,
    committed_bytes: bytes,
) -> None:
    intent = _build_intent(path, committed_bytes, checkpoint)
    _write_pending_intent(path, intent)
    content = canonical_json_bytes(checkpoint)
    try:
        _append_bytes(
            stream,
            path,
            content,
            expected_size=len(committed_bytes),
        )
        after = _parse_chain(_read_stream_bytes(stream, path))
        if len(after) == 0 or after[-1] != checkpoint:
            raise CheckpointIntegrityError("checkpoint append verification failed")
    except Exception as exc:
        rollback_error = None
        try:
            _restore_boundary(
                stream,
                path,
                expected_size=intent.committed_size,
                committed_sha256=intent.committed_sha256,
            )
        except Exception as restore_exc:  # pragma: no cover - exercised indirectly
            rollback_error = restore_exc
        if rollback_error is not None:
            raise CheckpointIntegrityError(
                "checkpoint append failed and rollback did not restore committed boundary"
            ) from rollback_error
        raise _coerce_integrity_error(exc) from exc
    _clear_pending_intent(path)


def _coerce_integrity_error(exc: Exception) -> CheckpointIntegrityError:
    if isinstance(exc, CheckpointIntegrityError):
        return exc
    return CheckpointIntegrityError("checkpoint append failed")


def _parent_directory(path: Path) -> Path:
    parent = path.parent if path.parent != Path("") else Path(".")
    if not parent.exists():
        raise FileNotFoundError(parent)
    return parent


def _require_operator_string(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a non-empty printable string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank or whitespace-only")
    if not value.isprintable():
        raise ValueError(f"{field_name} must not contain control characters")


def _normalize_input_shas(value: object) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("input_shas must be an object")
    normalized: dict[str, str] = {}
    for key, digest in value.items():
        if not isinstance(key, str) or not key:
            raise ValueError("input_shas keys must be non-empty strings")
        if not isinstance(digest, str) or not _HEX_40_OR_64.fullmatch(digest):
            raise ValueError(
                "input_shas values must be lowercase git or SHA-256 digests"
            )
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
        "verification_digest": checkpoint.verification_digest,
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


def _json_record_dict(checkpoint: Checkpoint) -> dict[str, object]:
    value = json.loads(canonical_json_bytes(checkpoint).decode("utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("checkpoint JSON must decode to an object")
    return value


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
            verification_digest=record["verification_digest"],
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
    verification_binding: str | None = None
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
            verification_binding = checkpoint.verification_digest
        else:
            previous = checkpoints[-1]
            if checkpoint.previous_digest != previous.digest:
                raise CheckpointIntegrityError(
                    "checkpoint previous_digest does not match prior digest"
                )
            assert bindings is not None
            if checkpoint.state_id != bindings["state_id"]:
                raise CheckpointIntegrityError(
                    "checkpoint state_id drifted across chain"
                )
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
            if verification_binding is None:
                if checkpoint.verification_digest is not None:
                    verification_binding = checkpoint.verification_digest
            elif checkpoint.verification_digest is None:
                raise CheckpointIntegrityError(
                    "checkpoint verification_digest regressed to null"
                )
            elif checkpoint.verification_digest != verification_binding:
                raise CheckpointIntegrityError(
                    "checkpoint verification_digest changed after binding"
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
    if previous.verification_digest is None:
        return
    if candidate.verification_digest is None:
        raise CheckpointIntegrityError(
            "checkpoint verification_digest cannot regress to null"
        )
    if candidate.verification_digest != previous.verification_digest:
        raise CheckpointIntegrityError(
            "checkpoint verification_digest cannot change after binding"
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
        except OSError as exc:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise CheckpointIntegrityError(
                "checkpoint file cannot be opened safely"
            ) from exc
    try:
        stream = os.fdopen(descriptor, "r+b", closefd=True)
    except OSError as exc:
        os.close(descriptor)
        raise CheckpointIntegrityError(
            "checkpoint file cannot be opened safely"
        ) from exc
    try:
        handle_state = os.fstat(stream.fileno())
        _assert_regular_metadata(handle_state)
        if create:
            created = _validated_file_state(path)
            if _node_identity(created) != _node_identity(handle_state):
                raise CheckpointIntegrityError(
                    "checkpoint file changed while acquiring append handle"
                )
            _fsync_parent_directory(path)
        else:
            before = _validated_file_state(path)
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
    _write_exact(stream, content)
    try:
        stream.flush()
    except OSError as exc:
        raise CheckpointIntegrityError("checkpoint append flush failed") from exc
    try:
        _fsync_descriptor(stream.fileno())
    except OSError as exc:
        raise CheckpointIntegrityError("checkpoint append fsync failed") from exc
    handle_after = os.fstat(stream.fileno())
    if handle_after.st_size != expected_size + len(content):
        raise CheckpointIntegrityError("checkpoint append was partial")
    path_after = _validated_file_state(path)
    if _file_identity(handle_after) != _file_identity(path_after):
        raise CheckpointIntegrityError("checkpoint file changed during append")


def _write_exact(stream: BinaryIO, content: bytes) -> None:
    view = memoryview(content)
    offset = 0
    while offset < len(content):
        try:
            written = stream.write(view[offset:])
        except OSError as exc:
            raise CheckpointIntegrityError("checkpoint append write failed") from exc
        if written is None:
            written = len(view[offset:])
        if not isinstance(written, int):
            raise CheckpointIntegrityError("checkpoint append write result is invalid")
        if written <= 0:
            raise CheckpointIntegrityError("checkpoint append made no write progress")
        offset += written


def _restore_boundary(
    stream: BinaryIO,
    path: Path,
    *,
    expected_size: int,
    committed_sha256: str,
) -> None:
    try:
        stream.truncate(expected_size)
    except OSError as exc:
        raise CheckpointIntegrityError("checkpoint rollback truncate failed") from exc
    try:
        stream.flush()
    except OSError as exc:
        raise CheckpointIntegrityError("checkpoint rollback flush failed") from exc
    try:
        _fsync_descriptor(stream.fileno())
    except OSError as exc:
        raise CheckpointIntegrityError("checkpoint rollback fsync failed") from exc
    restored = _read_stream_bytes(stream, path)
    if len(restored) != expected_size:
        raise CheckpointIntegrityError("checkpoint rollback size mismatch")
    if hashlib.sha256(restored).hexdigest() != committed_sha256:
        raise CheckpointIntegrityError(
            "checkpoint rollback did not restore committed boundary"
        )


def _fsync_descriptor(fd: int) -> None:
    os.fsync(fd)


def _fsync_parent_directory(path: Path) -> None:
    """Make a create or unlink durable by fsyncing the parent directory.

    POSIX requires a directory fsync after creating or unlinking a name;
    Windows does not expose an equivalent, so this is a no-op there.
    """

    if os.name == "nt":
        return
    parent = _parent_directory(path)
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(parent, flags)
    except OSError as exc:
        raise CheckpointIntegrityError(
            "checkpoint parent directory fsync failed"
        ) from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise CheckpointIntegrityError(
            "checkpoint parent directory fsync failed"
        ) from exc
    finally:
        os.close(descriptor)


def _intent_path(path: Path) -> Path:
    return path.with_name(_INTENT_NAME_TEMPLATE.format(name=path.name))


def _build_intent(
    path: Path,
    committed_bytes: bytes,
    checkpoint: Checkpoint,
) -> _PendingAppendIntent:
    record = _json_record_dict(checkpoint)
    return _PendingAppendIntent(
        schema_version=_SCHEMA_VERSION,
        checkpoint_file=path.name,
        committed_size=len(committed_bytes),
        committed_sha256=hashlib.sha256(committed_bytes).hexdigest(),
        pending_checkpoint=checkpoint,
        pending_record_sha256=hashlib.sha256(canonical_json_bytes(record)).hexdigest(),
    )


def _intent_payload(intent: _PendingAppendIntent) -> dict[str, object]:
    return {
        "schema_version": intent.schema_version,
        "checkpoint_file": intent.checkpoint_file,
        "committed_size": intent.committed_size,
        "committed_sha256": intent.committed_sha256,
        "pending_record": _json_record_dict(intent.pending_checkpoint),
        "pending_record_sha256": intent.pending_record_sha256,
    }


def _write_pending_intent(path: Path, intent: _PendingAppendIntent) -> None:
    """Write the append intent, or leave nothing behind.

    A HALF-written intent is not recoverable information, and leaving one on
    disk wedged the checkpoint permanently: both public entry points call
    `_recover_pending_append` first, which calls `_read_pending_intent`, which
    fails the field-set or digest check on a truncated file and raises. From
    that point `append_checkpoint` and `load_latest_checkpoint` both failed for
    that path until an operator deleted the file by hand.

    So the intent is all-or-nothing. Any failure between create and verify
    removes it, and the caller sees the original error rather than a chain
    frozen by a fragment of one.
    """
    pending = _intent_path(path)
    payload = canonical_json_bytes(_intent_payload(intent))
    descriptor = _open_exclusive_output_descriptor(pending)
    try:
        try:
            _write_exact_descriptor(descriptor, payload)
            _fsync_descriptor(descriptor)
        finally:
            os.close(descriptor)
        written = _read_regular_bytes(pending)
        if written != payload:
            raise CheckpointIntegrityError(
                "checkpoint append intent verification failed"
            )
        _fsync_parent_directory(pending)
    except BaseException:
        # Best-effort cleanup, including on KeyboardInterrupt: an interrupted
        # write is exactly the case that used to leave the wedging fragment.
        try:
            pending.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            _fsync_parent_directory(pending)
        except Exception:
            pass
        raise


def _open_exclusive_output_descriptor(path: Path) -> int:
    flags = getattr(os, "O_BINARY", 0) | os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if os.name != "nt":
        flags |= getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
        try:
            return os.open(path, flags, 0o600)
        except OSError as exc:
            raise CheckpointIntegrityError(
                "checkpoint append intent cannot be created safely"
            ) from exc
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
        0x40000000,
        0x00000001,
        None,
        1,
        0x00200000 | 0x08000000,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        raise CheckpointIntegrityError(
            "checkpoint append intent cannot be created safely"
        ) from ctypes.WinError()
    try:
        return msvcrt.open_osfhandle(handle, getattr(os, "O_BINARY", 0))
    except OSError as exc:
        ctypes.windll.kernel32.CloseHandle(handle)
        raise CheckpointIntegrityError(
            "checkpoint append intent cannot be created safely"
        ) from exc


def _write_exact_descriptor(descriptor: int, content: bytes) -> None:
    offset = 0
    while offset < len(content):
        try:
            written = os.write(descriptor, content[offset:])
        except OSError as exc:
            raise CheckpointIntegrityError(
                "checkpoint append intent write failed"
            ) from exc
        if written <= 0:
            raise CheckpointIntegrityError(
                "checkpoint append intent made no write progress"
            )
        offset += written


def _clear_pending_intent(path: Path) -> None:
    pending = _intent_path(path)
    if not pending.exists():
        return
    _validated_file_state(pending)
    try:
        os.unlink(pending)
    except OSError as exc:
        raise CheckpointIntegrityError(
            "checkpoint append intent could not be cleared"
        ) from exc
    _fsync_parent_directory(pending)


def _recover_pending_append(path: Path) -> None:
    intent = _read_pending_intent(path)
    if intent is None:
        return
    pending_bytes = canonical_json_bytes(intent.pending_checkpoint)
    if not path.exists():
        if intent.committed_size != 0:
            raise CheckpointIntegrityError(
                "checkpoint recovery cannot find the committed prefix"
            )
        _clear_pending_intent(path)
        return
    remove_target = False
    with _open_checkpoint_stream(path, create=False) as stream:
        raw = _read_stream_bytes(stream, path)
        if len(raw) < intent.committed_size:
            raise CheckpointIntegrityError(
                "checkpoint recovery lost bytes before the committed boundary"
            )
        prefix = raw[: intent.committed_size]
        if hashlib.sha256(prefix).hexdigest() != intent.committed_sha256:
            raise CheckpointIntegrityError(
                "checkpoint recovery committed prefix does not match intent"
            )
        tail = raw[intent.committed_size :]
        if not tail:
            remove_target = intent.committed_size == 0
        elif tail == pending_bytes:
            chain = _parse_chain(raw)
            if chain[-1] != intent.pending_checkpoint:
                raise CheckpointIntegrityError(
                    "checkpoint recovery full append does not match intent"
                )
        elif pending_bytes.startswith(tail):
            _restore_boundary(
                stream,
                path,
                expected_size=intent.committed_size,
                committed_sha256=intent.committed_sha256,
            )
            remove_target = intent.committed_size == 0
        else:
            raise CheckpointIntegrityError(
                "checkpoint recovery trailing bytes are unauthenticated"
            )
    if remove_target:
        _remove_empty_checkpoint_file(path)
    _clear_pending_intent(path)


def _remove_empty_checkpoint_file(path: Path) -> None:
    if not path.exists():
        return
    metadata = _validated_file_state(path)
    if metadata.st_size != 0:
        raise CheckpointIntegrityError(
            "checkpoint recovery refused to remove a non-empty file"
        )
    try:
        os.unlink(path)
    except OSError as exc:
        raise CheckpointIntegrityError(
            "checkpoint recovery could not clear the empty target"
        ) from exc
    _fsync_parent_directory(path)


def _read_pending_intent(path: Path) -> _PendingAppendIntent | None:
    pending = _intent_path(path)
    if not pending.exists():
        return None
    try:
        payload = json.loads(_read_regular_bytes(pending).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointIntegrityError("checkpoint append intent is malformed") from exc
    if not isinstance(payload, dict) or set(payload) != _INTENT_FIELDS:
        raise CheckpointIntegrityError("checkpoint append intent fields are invalid")
    if payload.get("schema_version") != _SCHEMA_VERSION:
        raise CheckpointIntegrityError(
            "checkpoint append intent schema version is invalid"
        )
    if payload.get("checkpoint_file") != path.name:
        raise CheckpointIntegrityError(
            "checkpoint append intent targets the wrong file"
        )
    committed_size = payload.get("committed_size")
    committed_sha256 = payload.get("committed_sha256")
    pending_record = payload.get("pending_record")
    pending_record_sha256 = payload.get("pending_record_sha256")
    if not isinstance(committed_size, int) or isinstance(committed_size, bool):
        raise CheckpointIntegrityError(
            "checkpoint append intent committed_size is invalid"
        )
    if committed_size < 0:
        raise CheckpointIntegrityError(
            "checkpoint append intent committed_size is invalid"
        )
    if not _is_hex_digest(committed_sha256):
        raise CheckpointIntegrityError(
            "checkpoint append intent committed_sha256 is invalid"
        )
    if not _is_hex_digest(pending_record_sha256):
        raise CheckpointIntegrityError(
            "checkpoint append intent pending_record_sha256 is invalid"
        )
    if not isinstance(pending_record, dict):
        raise CheckpointIntegrityError(
            "checkpoint append intent pending_record is invalid"
        )
    if (
        hashlib.sha256(canonical_json_bytes(pending_record)).hexdigest()
        != pending_record_sha256
    ):
        raise CheckpointIntegrityError(
            "checkpoint append intent pending_record digest does not match"
        )
    pending_checkpoint = _checkpoint_from_record(pending_record)
    return _PendingAppendIntent(
        schema_version=_SCHEMA_VERSION,
        checkpoint_file=path.name,
        committed_size=committed_size,
        committed_sha256=committed_sha256,
        pending_checkpoint=pending_checkpoint,
        pending_record_sha256=pending_record_sha256,
    )


__all__ = [
    "Checkpoint",
    "CheckpointIntegrityError",
    "append_checkpoint",
    "load_latest_checkpoint",
]
