"""Materialize the shared FLOSSI0ULLK context surface into generated artifacts.

Canonical source of truth:
  - `FLOSS/shared-context-surface.json`

Generated artifacts:
  - `.agent-surface/context/CONTEXT_BOOTSTRAP.md`
  - `.agent-surface/context/context-registry.json`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-context-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "context"


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
        if not isinstance(roots, list) or not all(isinstance(item, str) for item in roots):
            raise ContextSurfaceError(
                f"Corpus {corpus.get('id', '<unknown>')!r} must provide string roots"
            )
        resolved = dict(corpus)
        resolved["resolved_roots"] = [resolve_root(workspace_root, item) for item in roots]
        registry["corpora"].append(resolved)
    return registry


def build_bootstrap(registry: dict[str, Any]) -> str:
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
    lines.extend([
        "",
        "## Default Route Order",
        "",
    ])
    for item in registry.get("default_route_order", []):
        lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Corpora",
        "",
    ])
    for corpus in registry["corpora"]:
        lines.extend([
            f"### `{corpus['id']}` (`{corpus['uri']}`)",
            f"- Tier: `{corpus['tier']}`",
            f"- Priority: `{corpus['priority']}`",
            f"- Summary: {corpus['summary']}",
            "- Roots:",
        ])
        for root in corpus["resolved_roots"]:
            lines.append(f"  - `{root}`")
        lines.append("- Keywords:")
        for keyword in corpus.get("keywords", []):
            lines.append(f"  - `{keyword}`")
        lines.append("")
    return "\n".join(lines)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check_or_write(path: Path, content: str, *, check: bool, dry_run: bool) -> tuple[str, bool]:
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


def check_or_write_json(path: Path, payload: dict[str, Any], *, check: bool, dry_run: bool) -> tuple[str, bool]:
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
    bootstrap = build_bootstrap(registry)

    results: list[str] = []
    drift_found = False

    registry_path = output_dir / "context-registry.json"
    message, changed = check_or_write_json(registry_path, registry, check=check, dry_run=dry_run)
    results.append(message)
    drift_found = drift_found or changed

    bootstrap_path = output_dir / "CONTEXT_BOOTSTRAP.md"
    message, changed = check_or_write(bootstrap_path, bootstrap, check=check, dry_run=dry_run)
    results.append(message)
    drift_found = drift_found or changed
    return results, drift_found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize the FLOSSI0ULLK shared context surface")
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
