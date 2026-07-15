"""Deterministic local sealing for preserve-first salvage capsules."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Iterator

from .models import canonical_json_bytes

_SEAL_ARTIFACTS = frozenset(
    {"checksums.sha256", "provenance-root.json", "verification.json"}
)


class CapsuleVerificationError(RuntimeError):
    """The capsule cannot be authenticated or violates the sealed contract."""


def _capsule_root(root: Path) -> Path:
    root = Path(root)
    try:
        root_stat = root.lstat()
    except OSError as exc:
        raise CapsuleVerificationError("capsule root is unavailable") from exc
    if stat.S_ISLNK(root_stat.st_mode):
        raise CapsuleVerificationError("capsule root must not be a symlink")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise CapsuleVerificationError("capsule root must be a directory")
    return root.resolve(strict=True)


def _walk_regular_files(root: Path) -> Iterator[Path]:
    """Yield regular files without following symlinks or special entries."""

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
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise CapsuleVerificationError("capsule entry is unreadable") from exc
            mode = metadata.st_mode
            if stat.S_ISLNK(mode):
                raise CapsuleVerificationError("capsule symlink is not supported")
            if stat.S_ISDIR(mode):
                child_directories.append(path)
            elif stat.S_ISREG(mode):
                relative = path.relative_to(root).as_posix()
                if relative not in _SEAL_ARTIFACTS:
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
    try:
        before = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode):
            raise CapsuleVerificationError("capsule payload changed type while hashing")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
        after = path.stat(follow_symlinks=False)
    except OSError as exc:
        raise CapsuleVerificationError("capsule payload is unreadable") from exc
    identity_before = (
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        getattr(before, "st_ctime_ns", None),
        before.st_dev,
        before.st_ino,
    )
    identity_after = (
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        getattr(after, "st_ctime_ns", None),
        after.st_dev,
        after.st_ino,
    )
    if identity_before != identity_after:
        raise CapsuleVerificationError("capsule payload changed while hashing")
    return digest.hexdigest()


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
    entries = _checksum_entries(capsule)
    listing = _listing_bytes(entries)
    provenance_root = hashlib.sha256(listing).hexdigest()
    (capsule / "checksums.sha256").write_bytes(listing)
    (capsule / "provenance-root.json").write_bytes(
        canonical_json_bytes(_provenance_record(provenance_root))
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
    try:
        listing = (capsule / "checksums.sha256").read_bytes()
        provenance_bytes = (capsule / "provenance-root.json").read_bytes()
    except OSError as exc:
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
    value = json.loads((capsule / "provenance-root.json").read_text(encoding="utf-8"))
    return str(value["provenance_root"])
