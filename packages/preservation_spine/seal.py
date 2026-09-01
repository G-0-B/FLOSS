"""Deterministic local sealing for preserve-first salvage capsules."""

from __future__ import annotations

from contextlib import contextmanager
import ctypes
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import secrets
import stat
from typing import BinaryIO, Iterator

from .models import canonical_json_bytes

_SEAL_ARTIFACTS = frozenset(
    {"checksums.sha256", "provenance-root.json", "verification.json"}
)


class CapsuleVerificationError(RuntimeError):
    """The capsule cannot be authenticated or violates the sealed contract."""


def _is_reparse(metadata: os.stat_result) -> bool:
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _node_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return (metadata.st_dev, metadata.st_ino, metadata.st_mode)


def _file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _path_handle_mode_identity(metadata: os.stat_result) -> tuple[int, ...]:
    if os.name != "nt":
        return (metadata.st_mode,)
    # Windows lstat() synthesizes executable permission bits from a .exe suffix,
    # while fstat() on the same handle reports 0o666. File type, attributes, and
    # reparse tag are stable across both stat surfaces and retain the safety state.
    return (
        stat.S_IFMT(metadata.st_mode),
        getattr(metadata, "st_file_attributes", 0),
        getattr(metadata, "st_reparse_tag", 0),
    )


def _path_handle_node_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        *_path_handle_mode_identity(metadata),
    )


def _path_handle_file_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        *_path_handle_node_identity(metadata),
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
    )


def _assert_regular_metadata(metadata: os.stat_result) -> None:
    if stat.S_ISLNK(metadata.st_mode):
        raise CapsuleVerificationError("capsule symlink is not supported")
    if _is_reparse(metadata):
        raise CapsuleVerificationError("capsule reparse point is not supported")
    if not stat.S_ISREG(metadata.st_mode):
        raise CapsuleVerificationError("capsule entry is not a regular file")
    if metadata.st_nlink != 1:
        raise CapsuleVerificationError("capsule hardlink is not supported")


@contextmanager
def _open_regular_nofollow(path: Path) -> Iterator[BinaryIO]:
    """Open only the named entry, never a final symlink or reparse target."""

    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | os.O_NOFOLLOW
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise CapsuleVerificationError(
                "capsule payload cannot be opened safely"
            ) from exc
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
            0x80000000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x00200000 | 0x08000000,
            None,
        )
        invalid_handle = ctypes.c_void_p(-1).value
        if handle == invalid_handle:
            raise CapsuleVerificationError(
                "capsule payload cannot be opened safely"
            ) from ctypes.WinError()
        try:
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        except OSError as exc:
            ctypes.windll.kernel32.CloseHandle(handle)
            raise CapsuleVerificationError(
                "capsule payload cannot be opened safely"
            ) from exc
    try:
        stream = os.fdopen(descriptor, "rb", closefd=True)
    except OSError as exc:
        os.close(descriptor)
        raise CapsuleVerificationError(
            "capsule payload cannot be opened safely"
        ) from exc
    try:
        yield stream
    finally:
        stream.close()


def _validated_file_state(path: Path) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapsuleVerificationError("capsule entry is unavailable") from exc
    _assert_regular_metadata(metadata)
    return metadata


def _consume_regular_file(path: Path, *, return_bytes: bool) -> bytes | str:
    path_before = _validated_file_state(path)
    digest = hashlib.sha256()
    content = bytearray() if return_bytes else None
    with _open_regular_nofollow(path) as stream:
        handle_before = os.fstat(stream.fileno())
        _assert_regular_metadata(handle_before)
        if _path_handle_node_identity(path_before) != _path_handle_node_identity(
            handle_before
        ):
            raise CapsuleVerificationError("capsule payload changed before hashing")
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            if content is not None:
                content.extend(chunk)
        handle_after = os.fstat(stream.fileno())
    path_after = _validated_file_state(path)
    if (
        _path_handle_file_identity(path_before)
        != _path_handle_file_identity(handle_before)
        or _file_identity(handle_before) != _file_identity(handle_after)
        or _path_handle_file_identity(handle_after)
        != _path_handle_file_identity(path_after)
    ):
        raise CapsuleVerificationError("capsule payload changed while hashing")
    return bytes(content) if content is not None else digest.hexdigest()


def _read_regular_bytes(path: Path) -> bytes:
    result = _consume_regular_file(path, return_bytes=True)
    if not isinstance(result, bytes):
        raise AssertionError("regular byte reader returned a digest")
    return result


def _capsule_root(root: Path) -> Path:
    root = Path(root)
    try:
        root_stat = root.lstat()
    except OSError as exc:
        raise CapsuleVerificationError("capsule root is unavailable") from exc
    if stat.S_ISLNK(root_stat.st_mode):
        raise CapsuleVerificationError("capsule root must not be a symlink")
    if _is_reparse(root_stat):
        raise CapsuleVerificationError("capsule root must not be a reparse point")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise CapsuleVerificationError("capsule root must be a directory")
    resolved = root.resolve(strict=True)
    resolved_stat = resolved.lstat()
    if _node_identity(root_stat) != _node_identity(resolved_stat):
        raise CapsuleVerificationError("capsule root alias is not supported")
    return resolved


def _validated_directory_state(path: Path) -> os.stat_result:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CapsuleVerificationError("directory is unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or _is_reparse(metadata):
        raise CapsuleVerificationError("directory alias is not supported")
    if not stat.S_ISDIR(metadata.st_mode):
        raise CapsuleVerificationError("directory entry is not a directory")
    return metadata


@contextmanager
def _locked_directory(path: Path) -> Iterator[Path]:
    """Retain directory identity; Windows additionally blocks path replacement."""

    directory = Path(path)
    before = _validated_directory_state(directory)
    if os.name == "nt":
        from ctypes import wintypes

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
        close_handle = ctypes.windll.kernel32.CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL
        handle = create_file(
            str(directory),
            0x80000000,  # GENERIC_READ; READ_ATTRIBUTES alone permits rename here
            0x00000001 | 0x00000002,  # deliberately omit FILE_SHARE_DELETE
            None,
            3,  # OPEN_EXISTING
            0x00200000 | 0x02000000,  # OPEN_REPARSE_POINT | BACKUP_SEMANTICS
            None,
        )
        invalid_handle = ctypes.c_void_p(-1).value
        if handle == invalid_handle:
            raise CapsuleVerificationError(
                "directory cannot be retained safely"
            ) from ctypes.WinError()
        try:
            after = _validated_directory_state(directory)
            if _node_identity(before) != _node_identity(after):
                raise CapsuleVerificationError(
                    "directory changed while acquiring containment"
                )
            yield directory
        finally:
            close_handle(handle)
        return

    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | os.O_NOFOLLOW
    )
    try:
        descriptor = os.open(directory, flags)
    except OSError as exc:
        raise CapsuleVerificationError("directory cannot be retained safely") from exc
    try:
        handle_state = os.fstat(descriptor)
        if _node_identity(before) != _node_identity(handle_state):
            raise CapsuleVerificationError(
                "directory changed while acquiring containment"
            )
        yield directory
    finally:
        os.close(descriptor)


# Transient write files: `.{name}.pending-{32 hex}` at the capsule root, created
# by the atomic-output path and renamed into place on success. The docstring
# there says a FAILED write deliberately leaves one behind.
#
# `_walk_regular_files` excluded only the exact `_SEAL_ARTIFACTS` names, so such
# a leftover was walked into `checksums.sha256` on the next successful seal --
# becoming authenticated capsule payload that `verify_checksums` then requires
# to be present forever. A failed write must not be able to promote itself into
# the sealed universe.
_PENDING_OUTPUT_RE = re.compile(r"^\.[^/]+\.pending-[0-9a-f]{32}$")


def _is_pending_output(relative: str) -> bool:
    return _PENDING_OUTPUT_RE.match(relative) is not None


def _walk_regular_files(
    root: Path, *, excluded_root_names: frozenset[str] = _SEAL_ARTIFACTS
) -> Iterator[Path]:
    """Yield regular files without following symlinks or special entries."""

    root_metadata = Path(root).lstat()
    if stat.S_ISLNK(root_metadata.st_mode):
        raise CapsuleVerificationError("capsule tree root is a symlink")
    if _is_reparse(root_metadata):
        raise CapsuleVerificationError("capsule tree root is a reparse point")
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise CapsuleVerificationError("capsule tree root is not a directory")
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise CapsuleVerificationError("capsule directory is unreadable") from exc
        entries.sort(key=lambda item: os.fsencode(item.name))
        child_directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise CapsuleVerificationError("capsule entry is unreadable") from exc
            mode = metadata.st_mode
            if stat.S_ISLNK(mode):
                raise CapsuleVerificationError("capsule symlink is not supported")
            if _is_reparse(metadata):
                raise CapsuleVerificationError("capsule reparse point is not supported")
            if stat.S_ISDIR(mode):
                child_directories.append(path)
            elif stat.S_ISREG(mode):
                if metadata.st_nlink != 1:
                    raise CapsuleVerificationError("capsule hardlink is not supported")
                relative = path.relative_to(root).as_posix()
                if relative in excluded_root_names or _is_pending_output(relative):
                    continue
                yield path
            else:
                raise CapsuleVerificationError(
                    "capsule contains an unsupported special file"
                )
        pending.extend(reversed(child_directories))


def _relative_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root).as_posix()
    encoded = relative.encode("utf-8")
    if not encoded or relative in _SEAL_ARTIFACTS:
        raise CapsuleVerificationError("invalid capsule payload path")
    return relative


def _hash_regular_file(path: Path) -> str:
    result = _consume_regular_file(path, return_bytes=False)
    if not isinstance(result, str):
        raise AssertionError("regular file hasher returned bytes")
    return result


def _validate_fixed_output(root: Path, name: str) -> os.stat_result | None:
    path = root / name
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise CapsuleVerificationError("fixed output is unavailable") from exc
    _assert_regular_metadata(metadata)
    return metadata


def _atomic_write_fixed(root: Path, name: str, content: bytes) -> None:
    """Atomically replace a validated fixed output; failed pending files remain."""

    capsule = _capsule_root(root)
    with _locked_directory(capsule) as retained_capsule:
        root_before = capsule.lstat()
        existing = _validate_fixed_output(retained_capsule, name)
        pending = retained_capsule / f".{name}.pending-{secrets.token_hex(16)}"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        try:
            descriptor = os.open(pending, flags, 0o600)
        except OSError as exc:
            raise CapsuleVerificationError(
                "fixed output pending file cannot be created"
            ) from exc
        try:
            stream = os.fdopen(descriptor, "wb", closefd=True)
        except OSError as exc:
            os.close(descriptor)
            raise CapsuleVerificationError(
                "fixed output pending file cannot be created"
            ) from exc
        with stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
            pending_handle = os.fstat(stream.fileno())
        _assert_regular_metadata(pending_handle)
        pending_path = _validated_file_state(pending)
        if _path_handle_file_identity(pending_handle) != _path_handle_file_identity(
            pending_path
        ):
            raise CapsuleVerificationError("fixed output pending file changed")
        root_now = _capsule_root(capsule).lstat()
        if _node_identity(root_before) != _node_identity(root_now):
            raise CapsuleVerificationError("capsule root changed during output write")
        current = _validate_fixed_output(retained_capsule, name)
        if (existing is None) != (current is None) or (
            existing is not None
            and current is not None
            and _file_identity(existing) != _file_identity(current)
        ):
            raise CapsuleVerificationError("fixed output changed before replacement")
        try:
            os.replace(pending, retained_capsule / name)
        except OSError as exc:
            raise CapsuleVerificationError(
                "fixed output atomic replacement failed"
            ) from exc
        written = _validated_file_state(retained_capsule / name)
        if _path_handle_node_identity(written) != _path_handle_node_identity(
            pending_handle
        ):
            raise CapsuleVerificationError(
                "fixed output identity changed after replacement"
            )
        if _node_identity(_capsule_root(capsule).lstat()) != _node_identity(
            root_before
        ):
            raise CapsuleVerificationError("capsule root changed after output write")


def _checksum_entries(root: Path) -> list[dict[str, str]]:
    files = list(_walk_regular_files(root))
    files.sort(key=lambda path: _relative_name(root, path).encode("utf-8"))
    return [
        {"path": _relative_name(root, path), "sha256": _hash_regular_file(path)}
        for path in files
    ]


def _listing_bytes(entries: list[dict[str, str]]) -> bytes:
    return b"".join(canonical_json_bytes(entry) for entry in entries)


def _provenance_record(provenance_root: str) -> dict[str, str]:
    return {
        "algorithm": "sha256",
        "authentication": "local-unanchored",
        "checksum_listing": "checksums.sha256",
        "provenance_root": provenance_root,
        "schema_version": "1",
    }


def seal_capsule(root: Path) -> str:
    """Write an idempotent local-unanchored seal and return its root digest."""

    capsule = _capsule_root(root)
    with _locked_directory(capsule) as retained_capsule:
        for name in _SEAL_ARTIFACTS:
            _validate_fixed_output(retained_capsule, name)
        entries = _checksum_entries(retained_capsule)
        listing = _listing_bytes(entries)
        provenance_root = hashlib.sha256(listing).hexdigest()
        _atomic_write_fixed(capsule, "checksums.sha256", listing)
        _atomic_write_fixed(
            capsule,
            "provenance-root.json",
            canonical_json_bytes(_provenance_record(provenance_root)),
        )
        verify_checksums(capsule)
        return provenance_root


def _safe_listed_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise CapsuleVerificationError("checksum path must be a non-empty string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CapsuleVerificationError("checksum path is not valid UTF-8") from exc
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or value != pure.as_posix():
        raise CapsuleVerificationError("checksum path is unsafe")
    if value in _SEAL_ARTIFACTS:
        raise CapsuleVerificationError("seal artifact cannot checksum itself")
    return value


def _parse_listing(listing: bytes) -> list[dict[str, str]]:
    if listing and not listing.endswith(b"\n"):
        raise CapsuleVerificationError("checksum listing is not newline terminated")
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_line in listing.splitlines(keepends=True):
        try:
            value = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CapsuleVerificationError("checksum listing is malformed") from exc
        if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
            raise CapsuleVerificationError("checksum entry has unexpected fields")
        path = _safe_listed_path(value["path"])
        digest = value["sha256"]
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise CapsuleVerificationError("checksum digest is invalid")
        entry = {"path": path, "sha256": digest}
        if raw_line != canonical_json_bytes(entry):
            raise CapsuleVerificationError("checksum entry is not canonical JSON")
        if path in seen:
            raise CapsuleVerificationError("checksum listing contains duplicate paths")
        seen.add(path)
        entries.append(entry)
    if [entry["path"].encode("utf-8") for entry in entries] != sorted(
        entry["path"].encode("utf-8") for entry in entries
    ):
        raise CapsuleVerificationError(
            "checksum listing is not deterministically sorted"
        )
    return entries


def verify_checksums(root: Path) -> None:
    """Verify provenance, exact file universe, and every sealed payload byte."""

    capsule = _capsule_root(root)
    for name in _SEAL_ARTIFACTS:
        _validate_fixed_output(capsule, name)
    try:
        listing = _read_regular_bytes(capsule / "checksums.sha256")
        provenance_bytes = _read_regular_bytes(capsule / "provenance-root.json")
    except CapsuleVerificationError as exc:
        raise CapsuleVerificationError("capsule seal artifacts are missing") from exc
    entries = _parse_listing(listing)
    provenance_root = hashlib.sha256(listing).hexdigest()
    expected_provenance = _provenance_record(provenance_root)
    try:
        provenance = json.loads(provenance_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleVerificationError("provenance root is malformed") from exc
    if provenance_bytes != canonical_json_bytes(expected_provenance):
        raise CapsuleVerificationError("provenance root does not authenticate listing")
    if provenance != expected_provenance:
        raise CapsuleVerificationError("provenance metadata is inconsistent")

    actual_files = list(_walk_regular_files(capsule))
    actual = {_relative_name(capsule, path): path for path in actual_files}
    expected_names = {entry["path"] for entry in entries}
    if set(actual) != expected_names:
        raise CapsuleVerificationError("sealed capsule file universe changed")
    for entry in entries:
        if _hash_regular_file(actual[entry["path"]]) != entry["sha256"]:
            raise CapsuleVerificationError("sealed capsule payload checksum mismatch")


def provenance_root(root: Path) -> str:
    """Return the authenticated local provenance root after full verification."""

    verify_checksums(root)
    capsule = _capsule_root(root)
    value = json.loads(
        _read_regular_bytes(capsule / "provenance-root.json").decode("utf-8")
    )
    return str(value["provenance_root"])
