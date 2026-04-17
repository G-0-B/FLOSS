"""Materialize the shared FLOSSI0ULLK context surface into generated artifacts.

Canonical source of truth:
  - `FLOSS/shared-context-surface.json`

Generated artifacts:
  - `.agent-surface/context/CONTEXT_BOOTSTRAP.md`
  - `.agent-surface/context/context-registry.json`
  - optional generated context views declared by the manifest, such as:
    - `.agent-surface/context/CONTEXT_L0.md`
    - `.agent-surface/context/CONTEXT_L1.md`
    - `.agent-surface/context/context-view-registry.json`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-context-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "context"
WORD_RE = re.compile(r"\S+")


class ContextSurfaceError(Exception):
    """Raised for manifest or output-shape errors."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContextSurfaceError(f"Missing manifest: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContextSurfaceError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise ContextSurfaceError(f"Expected JSON object in {path}")
    if not isinstance(payload.get("corpora"), list):
        raise ContextSurfaceError(f"{path} must contain a list-valued `corpora` field")
    return payload


def resolve_root(workspace_root: Path, raw_path: str) -> str:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return str(candidate)
    return str((workspace_root / raw_path).resolve())


def build_registry(manifest: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    registry = {
        "manifest_version": manifest.get("manifest_version", "?"),
        "workspace_id": manifest.get("workspace_id", "workspace"),
        "workspace_name": manifest.get("workspace_name", "workspace"),
        "default_route_order": manifest.get("default_route_order", []),
        "rules": manifest.get("rules", []),
        "corpora": [],
    }
    for corpus in manifest["corpora"]:
        if not isinstance(corpus, dict):
            raise ContextSurfaceError("Every corpus entry must be a JSON object")
        roots = corpus.get("roots", [])
        if not isinstance(roots, list) or not all(
            isinstance(item, str) for item in roots
        ):
            raise ContextSurfaceError(
                f"Corpus {corpus.get('id', '<unknown>')!r} must provide string roots"
            )
        resolved = dict(corpus)
        resolved["resolved_roots"] = [
            resolve_root(workspace_root, item) for item in roots
        ]
        registry["corpora"].append(resolved)
    return registry


def resolve_output_path(
    workspace_root: Path, output_dir: Path, raw_path: str | None, default_name: str
) -> Path:
    if isinstance(raw_path, str) and raw_path.strip():
        candidate = Path(raw_path)
        if candidate.is_absolute():
            return candidate
        return (workspace_root / candidate).resolve()
    return output_dir / default_name


def strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return text
    return parts[2]


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def clean_markdown_fragment(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^\s*>+\s?", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    cleaned = cleaned.replace("**", "").replace("__", "")
    cleaned = cleaned.strip(" *_")
    return normalize_whitespace(cleaned)


def truncate(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    compact = normalize_whitespace(text)
    if len(compact) <= limit:
        return compact
    clipped = compact[: max(1, limit - 1)]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.rstrip(" ,;:") + "…"


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


def extract_markdown_view(
    workspace_root: Path, source: dict[str, Any]
) -> dict[str, Any]:
    raw_path = source.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ContextSurfaceError("Context view source entries must define `path`")

    path = (workspace_root / raw_path).resolve()
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ContextSurfaceError(f"Missing context view source: {path}") from exc

    body = strip_frontmatter(text)
    lines = body.splitlines()
    title = path.stem
    headings: list[str] = []
    bullets: list[str] = []
    paragraphs: list[str] = []
    paragraph_lines: list[str] = []
    in_code_block = False

    max_headings = int(source.get("max_headings", 4))
    max_bullets = int(source.get("max_bullets", 4))
    summary_chars = int(source.get("summary_chars", 240))

    def flush_paragraph() -> None:
        if not paragraph_lines:
            return
        paragraph = normalize_whitespace(" ".join(paragraph_lines))
        if paragraph:
            paragraphs.append(paragraph)
        paragraph_lines.clear()

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = clean_markdown_fragment(stripped[level:].strip())
            if level == 1 and heading_text:
                title = heading_text
            elif heading_text and len(headings) < max_headings:
                headings.append(heading_text)
            continue
        if stripped.startswith(("-", "*", "+")):
            flush_paragraph()
            bullet_text = clean_markdown_fragment(stripped[1:].strip())
            if (
                bullet_text
                and bullet_text not in {"-", "--"}
                and len(bullets) < max_bullets
            ):
                bullets.append(bullet_text)
            continue
        if stripped[0].isdigit() and ". " in stripped:
            flush_paragraph()
            bullet_text = clean_markdown_fragment(stripped.split(". ", 1)[1])
            if (
                bullet_text
                and bullet_text not in {"-", "--"}
                and len(bullets) < max_bullets
            ):
                bullets.append(bullet_text)
            continue
        paragraph_lines.append(clean_markdown_fragment(stripped))

    flush_paragraph()

    summary = ""
    for paragraph in paragraphs:
        if paragraph:
            summary = truncate(paragraph, summary_chars)
            break

    label = source.get("label", title)
    if not isinstance(label, str) or not label.strip():
        label = title

    l0_line = f"`{label}`: {summary}"
    if headings:
        l0_line += f" Heads: {'; '.join(headings[:3])}."
    l0_line = truncate(l0_line, 260)

    l1_lines = [
        f"## `{label}`",
        f"- Path: `{raw_path}`",
        f"- Title: {title}",
    ]
    if summary:
        l1_lines.append(f"- Summary: {summary}")
    if headings:
        l1_lines.append(f"- Key sections: {'; '.join(headings)}")
    if bullets:
        l1_lines.append("- Key bullets:")
        for bullet in bullets:
            l1_lines.append(f"  - {bullet}")
    l1_text = "\n".join(l1_lines)

    return {
        "id": source.get("id", path.stem),
        "label": label,
        "path": raw_path,
        "resolved_path": str(path),
        "title": title,
        "summary": summary,
        "headings": headings,
        "bullets": bullets,
        "source_word_count": word_count(body),
        "l0_line": l0_line,
        "l0_word_count": word_count(l0_line),
        "l1_text": l1_text,
        "l1_word_count": word_count(l1_text),
    }


def build_context_views(
    manifest: dict[str, Any], workspace_root: Path, output_dir: Path
) -> dict[str, Any] | None:
    raw_views = manifest.get("context_views")
    if raw_views is None:
        return None
    if not isinstance(raw_views, dict):
        raise ContextSurfaceError("Manifest `context_views` must be a JSON object")

    raw_sources = raw_views.get("sources", [])
    if not isinstance(raw_sources, list):
        raise ContextSurfaceError("Manifest `context_views.sources` must be a list")

    outputs = raw_views.get("outputs", {})
    if outputs is not None and not isinstance(outputs, dict):
        raise ContextSurfaceError("Manifest `context_views.outputs` must be an object")

    resolved_outputs = {
        "registry": str(
            resolve_output_path(
                workspace_root,
                output_dir,
                outputs.get("registry") if isinstance(outputs, dict) else None,
                "context-view-registry.json",
            )
        ),
        "l0": str(
            resolve_output_path(
                workspace_root,
                output_dir,
                outputs.get("l0") if isinstance(outputs, dict) else None,
                "CONTEXT_L0.md",
            )
        ),
        "l1": str(
            resolve_output_path(
                workspace_root,
                output_dir,
                outputs.get("l1") if isinstance(outputs, dict) else None,
                "CONTEXT_L1.md",
            )
        ),
    }

    sources = []
    for source in raw_sources:
        if not isinstance(source, dict):
            raise ContextSurfaceError(
                "Manifest `context_views.sources` entries must be objects"
            )
        sources.append(extract_markdown_view(workspace_root, source))

    return {
        "note": raw_views.get("note", ""),
        "outputs": resolved_outputs,
        "sources": sources,
    }


def build_context_l0(registry: dict[str, Any], context_views: dict[str, Any]) -> str:
    lines = [
        "# Context L0",
        "",
        "Generated additive briefing for fast re-orientation.",
        "Canon stays rich. This file stays cheap.",
        "",
        f"Workspace: `{registry['workspace_name']}`",
        f"Manifest version: `{registry['manifest_version']}`",
        "",
        "## Route Order",
        "",
        " -> ".join(f"`{item}`" for item in registry.get("default_route_order", [])),
        "",
        "## Source Briefings",
        "",
    ]
    for source in context_views["sources"]:
        lines.append(f"- {source['l0_line']}")
    return "\n".join(lines) + "\n"


def build_context_l1(registry: dict[str, Any], context_views: dict[str, Any]) -> str:
    lines = [
        "# Context L1",
        "",
        "Generated additive briefing derived from selected canonical docs.",
        "Use this before loading full source documents when a task needs more than L0.",
        "",
        f"Workspace: `{registry['workspace_name']}`",
        f"Manifest version: `{registry['manifest_version']}`",
        "",
        "## Operating Rules",
        "",
    ]
    for rule in registry.get("rules", []):
        lines.append(f"- {rule}")
    lines.append("")
    for source in context_views["sources"]:
        lines.extend([source["l1_text"], ""])
    return "\n".join(lines).rstrip() + "\n"


def build_bootstrap(
    registry: dict[str, Any], context_views: dict[str, Any] | None = None
) -> str:
    lines = [
        "# Shared Context Bootstrap",
        "",
        f"Workspace: `{registry['workspace_name']}`",
        f"Workspace ID: `{registry['workspace_id']}`",
        f"Manifest version: `{registry['manifest_version']}`",
        "",
        "## Operating Rules",
        "",
    ]
    for rule in registry.get("rules", []):
        lines.append(f"- {rule}")
    lines.extend(
        [
            "",
            "## Default Route Order",
            "",
        ]
    )
    for item in registry.get("default_route_order", []):
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Corpora",
            "",
        ]
    )
    for corpus in registry["corpora"]:
        lines.extend(
            [
                f"### `{corpus['id']}` (`{corpus['uri']}`)",
                f"- Tier: `{corpus['tier']}`",
                f"- Priority: `{corpus['priority']}`",
                f"- Summary: {corpus['summary']}",
                "- Roots:",
            ]
        )
        for root in corpus["resolved_roots"]:
            lines.append(f"  - `{root}`")
        lines.append("- Keywords:")
        for keyword in corpus.get("keywords", []):
            lines.append(f"  - `{keyword}`")
        lines.append("")
    if context_views is not None:
        lines.extend(
            [
                "## Generated Context Views",
                "",
                f"- L0: `{context_views['outputs']['l0']}`",
                f"- L1: `{context_views['outputs']['l1']}`",
                f"- View registry: `{context_views['outputs']['registry']}`",
                "",
            ]
        )
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check_or_write(
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
        write_text(path, content)
        return (f"WROTE {path}", changed)
    return (f"OK    {path}", changed)


def check_or_write_json(
    path: Path, payload: dict[str, Any], *, check: bool, dry_run: bool
) -> tuple[str, bool]:
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return check_or_write(path, content, check=check, dry_run=dry_run)


def materialize(
    workspace_root: Path,
    manifest_path: Path,
    output_dir: Path,
    *,
    check: bool,
    dry_run: bool,
) -> tuple[list[str], bool]:
    manifest = load_manifest(manifest_path)
    registry = build_registry(manifest, workspace_root)
    context_views = build_context_views(manifest, workspace_root, output_dir)
    bootstrap = build_bootstrap(registry, context_views)

    results: list[str] = []
    drift_found = False

    registry_path = output_dir / "context-registry.json"
    message, changed = check_or_write_json(
        registry_path, registry, check=check, dry_run=dry_run
    )
    results.append(message)
    drift_found = drift_found or changed

    bootstrap_path = output_dir / "CONTEXT_BOOTSTRAP.md"
    message, changed = check_or_write(
        bootstrap_path, bootstrap, check=check, dry_run=dry_run
    )
    results.append(message)
    drift_found = drift_found or changed

    if context_views is not None:
        view_registry = {
            "manifest_version": registry["manifest_version"],
            "workspace_id": registry["workspace_id"],
            "workspace_name": registry["workspace_name"],
            "note": context_views.get("note", ""),
            "outputs": context_views["outputs"],
            "sources": context_views["sources"],
        }

        registry_path = Path(context_views["outputs"]["registry"])
        message, changed = check_or_write_json(
            registry_path, view_registry, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

        l0_path = Path(context_views["outputs"]["l0"])
        l0_content = build_context_l0(registry, context_views)
        message, changed = check_or_write(
            l0_path, l0_content, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

        l1_path = Path(context_views["outputs"]["l1"])
        l1_content = build_context_l1(registry, context_views)
        message, changed = check_or_write(
            l1_path, l1_content, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    return results, drift_found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize the FLOSSI0ULLK shared context surface"
    )
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results, drift_found = materialize(
        workspace_root=args.workspace_root.resolve(),
        manifest_path=args.manifest.resolve(),
        output_dir=args.output_dir.resolve(),
        check=args.check,
        dry_run=args.dry_run,
    )
    for line in results:
        print(line)
    if args.check and drift_found:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
