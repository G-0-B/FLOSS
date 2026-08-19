"""Materialize FLOSSI0ULLK shared agent memory.

Canonical source of truth:
  - `FLOSS/shared-agent-memory-surface.json`
  - `FLOSS/docs/agent-memory/{feedback,user,project,reference}/*.md`

Generated artifacts:
  - `.agent-surface/memory/memory-registry.json`
  - `.agent-surface/memory/AGENT_MEMORY.md`
  - `FLOSS/docs/agent-memory/MEMORY.md`
  - configured agent-native projections, currently Claude memory files
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-agent-memory-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "memory"
MEMORY_TYPES = {"feedback", "user", "project", "reference"}


class AgentMemoryError(Exception):
    """Raised for manifest, canonical memory, or projection errors."""


@dataclass
class ImportedMemory:
    path: Path
    memory_id: str
    memory_type: str


@dataclass
class MemoryEntry:
    memory_id: str
    memory_type: str
    status: str
    title: str
    path: Path
    relative_path: str
    applies_to: list[str]
    body: str

    @property
    def projection_filename(self) -> str:
        slug = self.memory_id.removeprefix(f"{self.memory_type}-")
        return f"{self.memory_type}_{slug.replace('-', '_')}.md"


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AgentMemoryError(f"Missing manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AgentMemoryError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AgentMemoryError(f"Expected JSON object in {path}")
    return payload


def normalized_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", text.lower()).strip("-")
    return cleaned or "memory"


def split_legacy_name(path: Path) -> tuple[str, str]:
    stem = path.stem
    if "_" not in stem:
        return "project", slugify(stem)
    prefix, rest = stem.split("_", 1)
    if prefix not in MEMORY_TYPES:
        return "project", slugify(stem)
    return prefix, slugify(rest)


def extract_title(body: str, fallback: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return fallback.replace("-", " ").title()


def split_optional_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    raw_metadata = parts[1]
    body = parts[2].lstrip("\n")
    try:
        metadata = yaml.safe_load(raw_metadata) or {}
    except yaml.YAMLError:
        metadata = {}
        for line in raw_metadata.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            if key in {"name", "title", "description", "type", "originSessionId"}:
                metadata[key] = value.strip()
    if not isinstance(metadata, dict):
        metadata = {}
    return metadata, body


def frontmatter_for_import(
    memory_id: str,
    memory_type: str,
    legacy_filename: str,
    legacy_metadata: dict[str, Any],
) -> str:
    metadata: dict[str, Any] = {
        "id": memory_id,
        "type": memory_type,
        "created": utc_date(),
        "status": "active",
        "applies_to": ["any-agent"],
        "source": "legacy_claude_memory",
        "legacy_filename": legacy_filename,
    }
    title = legacy_metadata.get("name") or legacy_metadata.get("title")
    if isinstance(title, str) and title.strip():
        metadata["title"] = title.strip()
    description = legacy_metadata.get("description")
    if isinstance(description, str) and description.strip():
        metadata["legacy_description"] = description.strip()
    origin_session_id = legacy_metadata.get("originSessionId") or legacy_metadata.get(
        "origin_session_id"
    )
    if isinstance(origin_session_id, str) and origin_session_id.strip():
        metadata["origin_session_id"] = origin_session_id.strip()
    return (
        "---\n"
        + yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
        + "---\n\n"
    )


def import_legacy_claude_memory(
    legacy_dir: Path, canonical_root: Path
) -> list[ImportedMemory]:
    """Import existing Claude memory files into the canonical memory tree."""
    if not legacy_dir.exists():
        raise AgentMemoryError(f"Legacy Claude memory dir not found: {legacy_dir}")

    imported: list[ImportedMemory] = []
    for source in sorted(legacy_dir.glob("*.md")):
        if source.name == "MEMORY.md":
            continue
        memory_type, slug = split_legacy_name(source)
        memory_id = f"{memory_type}-{slug}"
        dest = canonical_root / memory_type / f"{slug}.md"
        legacy_metadata, body = split_optional_frontmatter(
            source.read_text(encoding="utf-8")
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            frontmatter_for_import(
                memory_id,
                memory_type,
                source.name,
                legacy_metadata,
            )
            + body,
            encoding="utf-8",
        )
        imported.append(ImportedMemory(dest, memory_id, memory_type))
    return imported


def split_frontmatter(text: str, path: Path) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        raise AgentMemoryError(f"Missing YAML frontmatter: {path}")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise AgentMemoryError(f"Unclosed YAML frontmatter: {path}")
    try:
        metadata = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        raise AgentMemoryError(f"Invalid YAML frontmatter in {path}: {exc}") from exc
    if not isinstance(metadata, dict):
        raise AgentMemoryError(f"Frontmatter must be a mapping: {path}")
    return metadata, parts[2].lstrip("\n")


def collect_memory_entries(workspace_root: Path, canonical_root: Path) -> list[MemoryEntry]:
    entries: list[MemoryEntry] = []
    if not canonical_root.exists():
        return entries
    for path in sorted(canonical_root.glob("*/*.md")):
        if path.parent.name not in MEMORY_TYPES:
            continue
        metadata, body = split_frontmatter(path.read_text(encoding="utf-8"), path)
        memory_type = str(metadata.get("type") or path.parent.name)
        if memory_type not in MEMORY_TYPES:
            raise AgentMemoryError(f"Invalid memory type {memory_type!r} in {path}")
        memory_id = str(metadata.get("id") or f"{memory_type}-{path.stem}")
        applies_to = metadata.get("applies_to", ["any-agent"])
        if isinstance(applies_to, str):
            applies_to = [applies_to]
        if not isinstance(applies_to, list):
            raise AgentMemoryError(f"`applies_to` must be a list in {path}")
        metadata_title = metadata.get("title")
        if isinstance(metadata_title, str) and metadata_title.strip():
            title = metadata_title.strip()
        else:
            title = extract_title(body, path.stem)
        entries.append(
            MemoryEntry(
                memory_id=memory_id,
                memory_type=memory_type,
                status=str(metadata.get("status", "active")),
                title=title,
                path=path,
                relative_path=path.relative_to(workspace_root).as_posix(),
                applies_to=[str(item) for item in applies_to],
                body=body,
            )
        )
    return entries


def build_registry(
    manifest: dict[str, Any], workspace_root: Path, entries: list[MemoryEntry]
) -> dict[str, Any]:
    return {
        "manifest_version": manifest.get("manifest_version", "?"),
        "workspace_id": manifest.get("workspace_id", "workspace"),
        "workspace_name": manifest.get("workspace_name", "workspace"),
        "canonical_root": manifest.get("canonical_root", "FLOSS/docs/agent-memory"),
        "rules": manifest.get("rules", []),
        "entries": [
            {
                "id": entry.memory_id,
                "type": entry.memory_type,
                "status": entry.status,
                "title": entry.title,
                "path": entry.relative_path,
                "applies_to": entry.applies_to,
            }
            for entry in entries
        ],
        "targets": manifest.get("targets", {}),
    }


def build_shared_index(entries: list[MemoryEntry]) -> str:
    lines = [
        "# Shared Agent Memory",
        "",
        "Canonical source: `FLOSS/docs/agent-memory/`",
        "Generated projection: `.agent-surface/memory/AGENT_MEMORY.md`",
        "",
    ]
    for memory_type in ("feedback", "user", "project", "reference"):
        typed = [entry for entry in entries if entry.memory_type == memory_type]
        if not typed:
            continue
        lines.extend([f"## {memory_type.title()}", ""])
        for entry in typed:
            first_line = next(
                (line.strip() for line in entry.body.splitlines() if line.strip()),
                "",
            )
            if first_line.startswith("#"):
                first_line = ""
            suffix = f" — {first_line}" if first_line else ""
            lines.append(f"- `{entry.memory_id}`: {entry.title}{suffix}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_claude_memory_index(entries: list[MemoryEntry]) -> str:
    lines = [
        "# Claude Memory Index",
        "",
        "Generated from `FLOSS/docs/agent-memory/`. Do not hand-edit this projection.",
        "",
    ]
    for entry in entries:
        lines.append(f"- `{entry.memory_id}` -> `{entry.projection_filename}`")
    return "\n".join(lines).rstrip() + "\n"


def build_claude_memory_file(entry: MemoryEntry) -> str:
    return "\n".join(
        [
            "---",
            f"id: {entry.memory_id}",
            f"type: {entry.memory_type}",
            f"status: {entry.status}",
            "source: FLOSS/docs/agent-memory",
            "---",
            "",
            entry.body.rstrip(),
            "",
        ]
    )


def check_or_write_text(
    path: Path, content: str, *, check: bool, dry_run: bool
) -> tuple[str, bool]:
    changed = True
    if path.exists():
        changed = path.read_text(encoding="utf-8") != content
    if check:
        return (f"CHECK {'DRIFT' if changed else 'OK'} {path}", changed)
    if dry_run:
        return (f"PLAN  {'WRITE' if changed else 'KEEP'} {path}", changed)
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return (f"WROTE {path}", changed)
    return (f"OK    {path}", changed)


def check_or_write_json(
    path: Path, payload: dict[str, Any], *, check: bool, dry_run: bool
) -> tuple[str, bool]:
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    changed = True
    if path.exists():
        try:
            changed = normalized_json(load_json(path)) != normalized_json(payload)
        except AgentMemoryError:
            changed = True
    if check:
        return (f"CHECK {'DRIFT' if changed else 'OK'} {path}", changed)
    if dry_run:
        return (f"PLAN  {'WRITE' if changed else 'KEEP'} {path}", changed)
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return (f"WROTE {path}", changed)
    return (f"OK    {path}", changed)


def resolve_path(workspace_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (workspace_root / path).resolve()


def materialize(
    *,
    workspace_root: Path,
    manifest_path: Path,
    output_dir: Path,
    check: bool,
    dry_run: bool,
) -> list[str]:
    manifest = load_json(manifest_path)
    canonical_raw = manifest.get("canonical_root", "FLOSS/docs/agent-memory")
    if not isinstance(canonical_raw, str):
        raise AgentMemoryError("Manifest `canonical_root` must be a string")
    canonical_root = resolve_path(workspace_root, canonical_raw)
    entries = collect_memory_entries(workspace_root, canonical_root)
    registry = build_registry(manifest, workspace_root, entries)

    messages: list[str] = []
    writers = [
        check_or_write_json(
            output_dir / "memory-registry.json",
            registry,
            check=check,
            dry_run=dry_run,
        ),
        check_or_write_text(
            output_dir / "AGENT_MEMORY.md",
            build_shared_index(entries),
            check=check,
            dry_run=dry_run,
        ),
        check_or_write_text(
            canonical_root / "MEMORY.md",
            build_shared_index(entries),
            check=check,
            dry_run=dry_run,
        ),
        check_or_write_text(
            canonical_root / "CHATGPT_MEMORY_EXPORT.md",
            build_shared_index(entries),
            check=check,
            dry_run=dry_run,
        ),
    ]
    messages.extend(message for message, _changed in writers)

    targets = manifest.get("targets", {})
    if not isinstance(targets, dict):
        raise AgentMemoryError("Manifest `targets` must be an object")
    claude_cfg = targets.get("claude", {})
    if isinstance(claude_cfg, dict) and claude_cfg.get("enabled"):
        memory_dir_raw = claude_cfg.get("memory_dir")
        if not isinstance(memory_dir_raw, str) or not memory_dir_raw.strip():
            raise AgentMemoryError("Claude target requires `memory_dir`")
        memory_dir = resolve_path(workspace_root, memory_dir_raw)
        message, _changed = check_or_write_text(
            memory_dir / "MEMORY.md",
            build_claude_memory_index(entries),
            check=check,
            dry_run=dry_run,
        )
        messages.append(message)
        for entry in entries:
            message, _changed = check_or_write_text(
                memory_dir / entry.projection_filename,
                build_claude_memory_file(entry),
                check=check,
                dry_run=dry_run,
            )
            messages.append(message)

    return messages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize shared agent memory")
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--import-claude-dir", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = (workspace_root / manifest_path).resolve()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = (workspace_root / output_dir).resolve()

    if args.import_claude_dir:
        manifest = load_json(manifest_path)
        canonical_root = resolve_path(
            workspace_root,
            str(manifest.get("canonical_root", "FLOSS/docs/agent-memory")),
        )
        imported = import_legacy_claude_memory(
            legacy_dir=args.import_claude_dir.resolve(),
            canonical_root=canonical_root,
        )
        for entry in imported:
            print(f"IMPORTED {entry.path}")

    messages = materialize(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        output_dir=output_dir,
        check=args.check,
        dry_run=args.dry_run,
    )
    for message in messages:
        print(message)
    if args.check and any("DRIFT" in message for message in messages):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
