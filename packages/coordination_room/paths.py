"""Normalize room-root-relative file paths to a posix claim key."""

from __future__ import annotations

from pathlib import Path, PurePosixPath


class PathEscape(ValueError):
    """Path is empty or escapes the room root."""


def normalize_path(root: Path, path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise PathEscape("empty path")
    root_resolved = root.resolve()
    raw = Path(path.strip())
    candidate = raw if raw.is_absolute() else (root_resolved / raw)
    resolved = candidate.resolve()
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise PathEscape(f"path escapes room root: {path}") from exc
    key = PurePosixPath(*relative.parts).as_posix()
    if key in {"", "."}:
        raise PathEscape("path resolves to room root")
    return key
