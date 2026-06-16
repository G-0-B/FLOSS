"""Unified review queue roll-up for metaharness staging surfaces.

Scans staged artifacts without mutating them. This is the U4 read-only roll-up
from `docs/research/2026-05-18-metaharness-unification.md`.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent


class ReviewItem:
    """One staged artifact awaiting or carrying review."""

    __slots__ = (
        "item_id",
        "kind",
        "status",
        "path",
        "provenance_path",
        "review_paths",
        "metadata",
        "size_bytes",
        "updated_at",
    )

    def __init__(
        self,
        *,
        item_id: str,
        kind: str,
        status: str,
        path: str,
        provenance_path: str | None,
        review_paths: list[str],
        metadata: dict[str, Any],
        size_bytes: int,
        updated_at: str,
    ) -> None:
        self.item_id = item_id
        self.kind = kind
        self.status = status
        self.path = path
        self.provenance_path = provenance_path
        self.review_paths = review_paths
        self.metadata = metadata
        self.size_bytes = size_bytes
        self.updated_at = updated_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "kind": self.kind,
            "status": self.status,
            "path": self.path,
            "provenance_path": self.provenance_path,
            "review_paths": self.review_paths,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes,
            "updated_at": self.updated_at,
        }


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _parse_simple_yaml(path: Path) -> dict[str, str]:
    """Parse simple top-level `key: value` fields from draft YAML.

    The harvest drafts are intentionally simple ledger-entry candidates. Avoid a
    PyYAML dependency here because the roll-up should stay lightweight.
    """
    metadata: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {"read_error": str(exc)}

    block_indent: int | None = None
    for line in lines:
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if block_indent is not None:
            if not stripped:
                continue
            if indent > block_indent:
                continue
            block_indent = None
        if indent > 2:
            continue
        if stripped.startswith("- "):
            stripped = stripped[2:].lstrip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if value in {">", "|", ">-", "|-"}:
            block_indent = indent
            continue
        if key and value and key not in metadata:
            metadata[key] = value
    return metadata


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"read_error": str(exc)}
    return payload if isinstance(payload, dict) else {"payload_type": type(payload).__name__}


def _harvest_items(workspace_root: Path) -> list[ReviewItem]:
    staging_dir = workspace_root / ".agent-surface" / "harvest" / "staging"
    if not staging_dir.exists():
        return []

    items: list[ReviewItem] = []
    for draft in sorted(staging_dir.glob("*_draft.yaml")):
        item_id = draft.stem.removesuffix("_draft")
        provenance = staging_dir / f"{item_id}_provenance.json"
        review_paths = sorted(staging_dir.glob(f"{item_id}_review_*.json"))
        metadata = _parse_simple_yaml(draft)
        if provenance.exists():
            provenance_data = _read_json(provenance)
            source_url = provenance_data.get("source_url") or provenance_data.get("url")
            if source_url:
                metadata["source_url"] = str(source_url)

        items.append(
            ReviewItem(
                item_id=item_id,
                kind="harvest_draft",
                status="reviewed" if review_paths else "needs_review",
                path=_relative(draft, workspace_root),
                provenance_path=_relative(provenance, workspace_root) if provenance.exists() else None,
                review_paths=[_relative(path, workspace_root) for path in review_paths],
                metadata=metadata,
                size_bytes=draft.stat().st_size,
                updated_at=_mtime_iso(draft),
            )
        )
    return items


def _synthesis_items(workspace_root: Path) -> list[ReviewItem]:
    staging_dir = workspace_root / "FLOSS" / "docs" / "knowledge_log" / "staging"
    if not staging_dir.exists():
        return []

    items: list[ReviewItem] = []
    for draft in sorted(staging_dir.glob("*_draft.json")):
        item_id = draft.stem.removesuffix("_draft")
        payload = _read_json(draft)
        source_file = str(payload.get("file_path", "")).replace("\\", "/")
        metadata = {
            "source_file": source_file,
            "model": payload.get("model"),
            "staged_at": payload.get("staged_at"),
            "insights_chars": len(str(payload.get("insights", ""))),
        }
        if "read_error" in payload:
            metadata["read_error"] = payload["read_error"]

        items.append(
            ReviewItem(
                item_id=item_id,
                kind="synthesis_draft",
                status="needs_review",
                path=_relative(draft, workspace_root),
                provenance_path=None,
                review_paths=[],
                metadata=metadata,
                size_bytes=draft.stat().st_size,
                updated_at=_mtime_iso(draft),
            )
        )
    return items


def collect_review_items(workspace_root: Path | str = WORKSPACE_ROOT) -> list[ReviewItem]:
    """Collect staged review items from known metaharness staging surfaces."""
    root = Path(workspace_root).resolve()
    return [*_harvest_items(root), *_synthesis_items(root)]


def summarize(items: list[ReviewItem]) -> dict[str, Any]:
    by_kind = Counter(item.kind for item in items)
    by_status = Counter(item.status for item in items)
    return {
        "total": len(items),
        "by_kind": dict(sorted(by_kind.items())),
        "by_status": dict(sorted(by_status.items())),
    }


def render_json(items: list[ReviewItem], limit: int | None = None) -> str:
    selected = items[:limit] if limit is not None else items
    payload = {
        **summarize(items),
        "items": [item.to_dict() for item in selected],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def render_markdown(items: list[ReviewItem], limit: int | None = None) -> str:
    selected = items[:limit] if limit is not None else items
    summary = summarize(items)
    lines = [
        "# Review Queue",
        "",
        f"Total queued: {summary['total']}",
        "",
        "## Counts By Kind",
    ]
    for kind, count in summary["by_kind"].items():
        lines.append(f"- {kind}: {count}")
    lines.extend(["", "## Counts By Status"])
    for status, count in summary["by_status"].items():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Items"])
    if not selected:
        lines.append("No staged review items found.")
        return "\n".join(lines) + "\n"

    for index, item in enumerate(selected, start=1):
        lines.append(f"{index}. `{item.item_id}` - {item.kind} - {item.status}")
        lines.append(f"   Path: `{item.path}`")
        if item.provenance_path:
            lines.append(f"   Provenance: `{item.provenance_path}`")
        if item.review_paths:
            lines.append(f"   Reviews: {', '.join(f'`{path}`' for path in item.review_paths)}")
        if item.metadata.get("license_status"):
            lines.append(f"   License: {item.metadata['license_status']}")
        if item.metadata.get("decision_hint"):
            lines.append(f"   Decision: {item.metadata['decision_hint']}")
        if item.metadata.get("source_file"):
            lines.append(f"   Source: `{item.metadata['source_file']}`")
    return "\n".join(lines) + "\n"


def render_triage(items: list[ReviewItem], workspace_root: Path | str = WORKSPACE_ROOT) -> str:
    """Classify staged drafts by source survival, size, and area.

    Merged from the former `triage_review_queue.py` (metaharness-inventory
    decision D6 consolidation pass, 2026-06-12), extended to cover harvest
    drafts as well as synthesis drafts.
    """
    root = Path(workspace_root).resolve()
    lines = ["# Review Queue Triage", ""]

    synthesis = [item for item in items if item.kind == "synthesis_draft"]
    harvest = [item for item in items if item.kind == "harvest_draft"]

    lines.append(f"Synthesis drafts: {len(synthesis)}")
    if synthesis:
        exists_in_canon = 0
        orphans: list[tuple[str, str]] = []
        sizes: list[int] = []
        by_area: Counter[str] = Counter()
        for item in synthesis:
            source = str(item.metadata.get("source_file", ""))
            rel = source
            for prefix in ("C:/~shit/", "c:/~shit/"):
                if rel.startswith(prefix):
                    rel = rel[len(prefix):]
                    break
            by_area[rel.split("/")[0] if rel else "?"] += 1
            sizes.append(int(item.metadata.get("insights_chars", 0) or 0))
            if rel and (root / rel).exists():
                exists_in_canon += 1
            elif len(orphans) < 8:
                orphans.append((item.item_id, rel or "<no source recorded>"))
        missing = len(synthesis) - exists_in_canon
        lines.append(f"  Source still in canon: {exists_in_canon}")
        lines.append(f"  Source missing (moved/deleted): {missing}")
        if sizes:
            ordered = sorted(sizes)
            mid = len(ordered) // 2
            median = (
                ordered[mid]
                if len(ordered) % 2
                else (ordered[mid - 1] + ordered[mid]) / 2
            )
            lines.append(
                f"  Insights total: {sum(sizes) / 1024:.1f} KB  "
                f"median={median:.0f}  max={max(sizes)}"
            )
        lines.extend(["", "  By source area:"])
        for area, count in by_area.most_common():
            lines.append(f"    {count:>4}  {area}")
        if orphans:
            lines.extend(["", "  Sample missing-source drafts (orphans):"])
            for item_id, rel in orphans:
                lines.append(f"    {item_id[:70]}")
                lines.append(f"        <- {rel[:90]}")

    lines.extend(["", f"Harvest drafts: {len(harvest)}"])
    if harvest:
        reviewed = sum(1 for item in harvest if item.status == "reviewed")
        lines.append(f"  Reviewed: {reviewed}")
        lines.append(f"  Needs review: {len(harvest) - reviewed}")
        with_source = sum(1 for item in harvest if item.metadata.get("source_url"))
        lines.append(f"  With source_url provenance: {with_source}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Roll up staged metaharness review items.")
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limit displayed items.")
    parser.add_argument(
        "--triage",
        action="store_true",
        help="Classify staged drafts by source survival, size, and area.",
    )
    parser.add_argument(
        "--workspace-root",
        default=str(WORKSPACE_ROOT),
        help="Workspace root containing .agent-surface and FLOSS/.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    items = collect_review_items(Path(args.workspace_root))
    if args.triage:
        print(render_triage(items, Path(args.workspace_root)), end="")
    elif args.format == "json":
        print(render_json(items, args.limit))
    else:
        print(render_markdown(items, args.limit), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
