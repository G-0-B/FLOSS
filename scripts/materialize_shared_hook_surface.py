"""Materialize the shared FLOSSI0ULLK hook surface into generated artifacts.

Canonical source of truth:
  - `FLOSS/shared-hook-surface.json`
  - repo-owned hook scripts in `FLOSS/scripts/`

Generated artifacts:
  - `.agent-surface/hooks/HOOK_INDEX.md`
  - `.agent-surface/hooks/hook-registry.json`
  - native hook settings merged into configured agent settings
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-hook-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "hooks"


class HookSurfaceError(Exception):
    """Raised for manifest, target, or projection errors."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HookSurfaceError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise HookSurfaceError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HookSurfaceError(f"Expected JSON object in {path}")
    return payload


def strip_jsonc_comments(text: str) -> str:
    out: list[str] = []
    i = 0
    in_string = False
    escape = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_string:
            out.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            i += 2
            while i < len(text) and text[i] not in "\r\n":
                i += 1
            continue

        if ch == "/" and nxt == "*":
            i += 2
            while i + 1 < len(text) and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def load_jsonc(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise HookSurfaceError(f"Missing file: {path}") from exc
    try:
        payload = json.loads(strip_jsonc_comments(text))
    except json.JSONDecodeError as exc:
        raise HookSurfaceError(f"Invalid JSONC in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HookSurfaceError(f"Expected JSON object in {path}")
    return payload


def normalized_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def check_or_write_json(
    path: Path,
    payload: dict[str, Any],
    *,
    check: bool,
    dry_run: bool,
) -> tuple[str, bool]:
    changed = True
    if path.exists():
        current = load_jsonc(path) if path.suffix == ".jsonc" else load_json(path)
        changed = normalized_json(current) != normalized_json(payload)
    if check:
        return (f"CHECK {'DRIFT' if changed else 'OK'} {path}", changed)
    if dry_run:
        return (f"PLAN  {'WRITE' if changed else 'KEEP'} {path}", changed)
    if changed:
        write_json(path, payload)
        return (f"WROTE {path}", changed)
    return (f"OK    {path}", changed)


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
        write_text(path, content)
        return (f"WROTE {path}", changed)
    return (f"OK    {path}", changed)


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    if not isinstance(manifest.get("targets"), dict):
        raise HookSurfaceError(f"{path} must contain an object-valued `targets` field")
    if not isinstance(manifest.get("rules"), list):
        raise HookSurfaceError(f"{path} must contain a list-valued `rules` field")
    hook_scripts = manifest.get("hook_scripts", [])
    if not isinstance(hook_scripts, list):
        raise HookSurfaceError(f"{path} field `hook_scripts` must be a list")
    return manifest


def validate_hook_scripts(
    manifest: dict[str, Any], workspace_root: Path
) -> list[dict[str, str]]:
    scripts: list[dict[str, str]] = []
    for raw_path in manifest.get("hook_scripts", []):
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise HookSurfaceError("Each hook script path must be a non-empty string")
        resolved = (workspace_root / raw_path).resolve()
        if not resolved.exists():
            raise HookSurfaceError(f"Hook script missing: {resolved}")
        scripts.append(
            {
                "path": raw_path,
                "resolved_path": str(resolved),
            }
        )
    return scripts


def merge_hook_payload(
    existing: dict[str, Any], target_cfg: dict[str, Any]
) -> dict[str, Any]:
    payload = dict(existing)

    existing_hooks = payload.get("hooks", {})
    if existing_hooks is None:
        existing_hooks = {}
    if not isinstance(existing_hooks, dict):
        raise HookSurfaceError("Existing `hooks` field must be an object if present")
    merged_hooks = dict(existing_hooks)

    target_hooks = target_cfg.get("hooks", {})
    if not isinstance(target_hooks, dict):
        raise HookSurfaceError("Target `hooks` field must be an object if present")
    for event_name, definitions in target_hooks.items():
        if not isinstance(definitions, list):
            raise HookSurfaceError(
                f"Hook event {event_name!r} must contain a list of definitions"
            )
        merged_hooks[event_name] = definitions
    payload["hooks"] = merged_hooks

    target_hooks_config = target_cfg.get("hooksConfig")
    if target_hooks_config is not None:
        if not isinstance(target_hooks_config, dict):
            raise HookSurfaceError(
                "Target `hooksConfig` field must be an object if present"
            )
        existing_hooks_config = payload.get("hooksConfig", {})
        if existing_hooks_config is None:
            existing_hooks_config = {}
        if not isinstance(existing_hooks_config, dict):
            raise HookSurfaceError(
                "Existing `hooksConfig` field must be an object if present"
            )
        merged_hooks_config = dict(existing_hooks_config)
        merged_hooks_config.update(target_hooks_config)
        payload["hooksConfig"] = merged_hooks_config

    return payload


def build_registry(manifest: dict[str, Any], workspace_root: Path) -> dict[str, Any]:
    registry_targets: dict[str, Any] = {}
    for target_name, target_cfg in manifest["targets"].items():
        if not isinstance(target_cfg, dict):
            raise HookSurfaceError(f"Target {target_name!r} must be a JSON object")
        resolved_cfg = dict(target_cfg)
        settings_path = target_cfg.get("settings_path")
        if isinstance(settings_path, str) and settings_path.strip():
            resolved_cfg["resolved_settings_path"] = str(
                (workspace_root / settings_path).resolve()
            )
        registry_targets[target_name] = resolved_cfg

    return {
        "manifest_version": manifest.get("manifest_version", "?"),
        "workspace_id": manifest.get("workspace_id", "workspace"),
        "workspace_name": manifest.get("workspace_name", "workspace"),
        "rules": manifest.get("rules", []),
        "hook_scripts": validate_hook_scripts(manifest, workspace_root),
        "targets": registry_targets,
    }


def build_index(registry: dict[str, Any]) -> str:
    lines = [
        "# Shared Hook Index",
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
            "## Hook Scripts",
            "",
        ]
    )
    for script in registry.get("hook_scripts", []):
        lines.append(f"- `{script['path']}` -> `{script['resolved_path']}`")

    lines.extend(
        [
            "",
            "## Targets",
            "",
        ]
    )
    for target_name, target_cfg in registry.get("targets", {}).items():
        enabled = bool(target_cfg.get("enabled"))
        lines.append(f"### `{target_name}`")
        lines.append(f"- Enabled: `{str(enabled).lower()}`")
        if target_cfg.get("resolved_settings_path"):
            lines.append(f"- Settings: `{target_cfg['resolved_settings_path']}`")
        if target_cfg.get("reason"):
            lines.append(f"- Reason: {target_cfg['reason']}")
        hooks = target_cfg.get("hooks", {})
        if isinstance(hooks, dict) and hooks:
            events = ", ".join(sorted(hooks.keys()))
            lines.append(f"- Managed events: `{events}`")
        hooks_config = target_cfg.get("hooksConfig")
        if isinstance(hooks_config, dict) and hooks_config:
            lines.append(
                f"- Hooks config keys: `{', '.join(sorted(hooks_config.keys()))}`"
            )
        lines.append("")

    lines.extend(
        [
            "## Generated By",
            "",
            "- `FLOSS/scripts/materialize_shared_hook_surface.py`",
            "",
        ]
    )
    return "\n".join(lines)


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
    index = build_index(registry)

    results: list[str] = []
    drift_found = False

    registry_path = output_dir / "hook-registry.json"
    message, changed = check_or_write_json(
        registry_path, registry, check=check, dry_run=dry_run
    )
    results.append(message)
    drift_found = drift_found or changed

    index_path = output_dir / "HOOK_INDEX.md"
    message, changed = check_or_write_text(
        index_path, index, check=check, dry_run=dry_run
    )
    results.append(message)
    drift_found = drift_found or changed

    for target_name, target_cfg in manifest["targets"].items():
        if not isinstance(target_cfg, dict):
            raise HookSurfaceError(f"Target {target_name!r} must be a JSON object")
        if not target_cfg.get("enabled"):
            continue
        settings_path = target_cfg.get("settings_path")
        if not isinstance(settings_path, str) or not settings_path.strip():
            raise HookSurfaceError(
                f"Enabled target {target_name!r} must define `settings_path`"
            )
        target_path = (workspace_root / settings_path).resolve()
        existing = (
            load_jsonc(target_path)
            if target_path.exists() and target_path.suffix == ".jsonc"
            else (load_json(target_path) if target_path.exists() else {})
        )
        payload = merge_hook_payload(existing, target_cfg)
        message, changed = check_or_write_json(
            target_path, payload, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    return results, drift_found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize the FLOSSI0ULLK shared hook surface"
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
