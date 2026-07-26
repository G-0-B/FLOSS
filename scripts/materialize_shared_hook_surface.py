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
import io
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-hook-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "hooks"


class HookSurfaceError(Exception):
    """Raised for manifest, target, or projection errors."""


def require_module(module_name: str, target: str) -> Any:
    """Import a round-trip serializer, failing loudly for one target only.

    Never fall back to a non-round-trip writer -- that would silently strip
    comments and reorder keys in large hand-maintained configs. Imported
    lazily (only when a `format: "yaml"` target is actually processed) so a
    missing package fails just that target, not every target -- mirrors
    `require_module` in `materialize_shared_agent_surface.py`.
    """
    import importlib

    try:
        return importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise HookSurfaceError(
            f"Target {target!r} requires the {module_name!r} package "
            f"(pip install {module_name.split('.')[0]})"
        ) from exc


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


def resolve_target_hooks(target_cfg: dict[str, Any]) -> dict[str, Any]:
    """Return a target's hook block after applying its `event_map`, if any.

    A target may declare `event_map: {"PreToolUse": "pre_tool_call", ...}`
    to rename manifest event names into its own native vocabulary (e.g.
    Hermes's snake_case events vs. Claude/Codex's PascalCase). Events
    present in the manifest but ABSENT from a target's `event_map` are
    OMITTED for that target rather than passed through raw -- emitting an
    event name a harness doesn't understand is a silently broken hook, and
    omission is the honest behavior. When no `event_map` is declared,
    events pass through unchanged (existing behavior, preserved for every
    target that predates this capability).
    """
    target_hooks = target_cfg.get("hooks", {})
    if not isinstance(target_hooks, dict):
        raise HookSurfaceError("Target `hooks` field must be an object if present")
    for event_name, definitions in target_hooks.items():
        if not isinstance(definitions, list):
            raise HookSurfaceError(
                f"Hook event {event_name!r} must contain a list of definitions"
            )

    event_map = target_cfg.get("event_map")
    if event_map is None:
        return dict(target_hooks)
    if not isinstance(event_map, dict):
        raise HookSurfaceError("Target `event_map` field must be an object if present")

    mapped: dict[str, Any] = {}
    for event_name, definitions in target_hooks.items():
        mapped_name = event_map.get(event_name)
        if mapped_name is None:
            continue
        mapped[mapped_name] = definitions
    return mapped


def merge_hook_payload(
    existing: dict[str, Any],
    target_cfg: dict[str, Any],
    mapped_hooks: dict[str, Any],
) -> dict[str, Any]:
    payload = dict(existing)

    existing_hooks = payload.get("hooks", {})
    if existing_hooks is None:
        existing_hooks = {}
    if not isinstance(existing_hooks, dict):
        raise HookSurfaceError("Existing `hooks` field must be an object if present")
    merged_hooks = dict(existing_hooks)

    for event_name, definitions in mapped_hooks.items():
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


def build_target_payload(
    existing: dict[str, Any], target_cfg: dict[str, Any]
) -> dict[str, Any]:
    """Build the on-disk payload for a hook target.

    Most targets (`claude`, `gemini`) live in a settings file shared with
    unrelated agent-native keys, so their payload is produced by merging
    managed hook events into whatever already exists on disk.

    Targets marked `payload_shape: "hooks_only"` own a settings file whose
    *entire* content is the hook definitions (e.g. Codex's `.codex/hooks.json`,
    which Codex pins by content hash). For those, the payload is built fresh
    from the manifest only -- `existing` is intentionally ignored so no
    incidental keys ever get carried forward into a file Codex re-hashes.
    """
    mapped_hooks = resolve_target_hooks(target_cfg)
    if target_cfg.get("payload_shape") == "hooks_only":
        return {"hooks": mapped_hooks}
    return merge_hook_payload(existing, target_cfg, mapped_hooks)


def hermes_gateway_alive_for(target_path: Path) -> int | None:
    """Return the PID of a live Hermes gateway guarding `target_path`, else None.

    Delegates to `hermes_gateway_alive` in the sibling
    `materialize_shared_agent_surface` module rather than reimplementing the
    liveness check -- a running Hermes gateway rewrites its own config.yaml
    on shutdown, which would clobber a write made underneath it, and both
    the MCP surface and this hook surface write into the same file for the
    `hermes_workspace` case. Imported lazily, and only via `sys.path`
    manipulation (both scripts live in the same `scripts/` directory but
    this module is not part of a package), so a plain claude/gemini/codex
    JSON-only run never pays for importing the much larger agent-surface
    module.
    """
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from materialize_shared_agent_surface import hermes_gateway_alive

    return hermes_gateway_alive(target_path.parent)


def merge_hook_payload_into_yaml_doc(
    doc: Any, target_cfg: dict[str, Any], mapped_hooks: dict[str, Any]
) -> None:
    """Mutate a parsed YAML document in place, merging managed hook events.

    Same merge semantics as `merge_hook_payload` (managed events overwrite
    same-named existing events; unrelated keys are left untouched), but
    mutates the already-parsed ruamel node in place instead of returning a
    fresh dict. Mirrors `apply_hermes_mcp` in
    `materialize_shared_agent_surface.py`: YAML mappings have no
    positional/header hazard, so there is no need to rebuild the node, and
    mutating in place is what lets ruamel preserve comments, key order, and
    unrelated top-level content.
    """
    existing_hooks = doc.get("hooks")
    if existing_hooks is None:
        doc["hooks"] = {}
        existing_hooks = doc["hooks"]
    if not hasattr(existing_hooks, "items"):
        raise HookSurfaceError("Existing `hooks` field must be a mapping if present")
    for event_name, definitions in mapped_hooks.items():
        existing_hooks[event_name] = definitions

    target_hooks_config = target_cfg.get("hooksConfig")
    if target_hooks_config is not None:
        if not isinstance(target_hooks_config, dict):
            raise HookSurfaceError(
                "Target `hooksConfig` field must be an object if present"
            )
        existing_hooks_config = doc.get("hooksConfig")
        if existing_hooks_config is None:
            doc["hooksConfig"] = {}
            existing_hooks_config = doc["hooksConfig"]
        if not hasattr(existing_hooks_config, "items"):
            raise HookSurfaceError(
                "Existing `hooksConfig` field must be a mapping if present"
            )
        for key, value in target_hooks_config.items():
            existing_hooks_config[key] = value


def apply_yaml_target(
    target_path: Path,
    target_cfg: dict[str, Any],
    *,
    check: bool,
    dry_run: bool,
) -> tuple[str, bool]:
    """Materialize a `format: "yaml"` hook target.

    A missing file is SKIPPED rather than fabricated -- mirroring how the
    MCP Hermes target guards with `.exists()` in
    `materialize_shared_agent_surface.py`. Round-tripping requires an
    existing document to preserve comments/structure against; nothing here
    owns creating a fresh YAML config from scratch.

    Before reading, this also refuses to write if a live Hermes gateway is
    guarding `target_path`'s directory (a `gateway.pid` naming a running
    process) -- a running gateway rewrites its own config.yaml on shutdown
    and would clobber anything written underneath it. This check runs
    unconditionally, even under `--check`/`--dry-run`, the same way and for
    the same reason `materialize_shared_agent_surface.py`'s Hermes MCP block
    does: `--check` exists so an operator learns about a blocker *before*
    attempting a real write. For a target whose directory has no
    `gateway.pid` at all (claude/gemini/codex today), this is a fast no-op.

    Uses the exact ruamel configuration established for Hermes's
    `config.yaml` (`apply_hermes_mcp`'s caller): `preserve_quotes = True`,
    `indent(mapping=2, sequence=4, offset=2)`, `width = 4096`. A bare
    `ruamel.yaml.YAML()` reflows an entire hand-maintained document on a
    no-op change (measured on the real Hermes config: a 398-line diff for
    zero semantic change); this configuration is required to keep a true
    no-op round-trip byte-identical.
    """
    if not target_path.exists():
        return (f"SKIP  {target_path} (no config at {target_path})", False)

    live_pid = hermes_gateway_alive_for(target_path)
    if live_pid is not None:
        return (
            f"REFUSED {target_path} (gateway PID {live_pid} is live; "
            "stop it and re-run, or the config is clobbered on shutdown)",
            True,
        )

    ruamel_yaml = require_module("ruamel.yaml", str(target_path))
    yaml_rt = ruamel_yaml.YAML()
    yaml_rt.preserve_quotes = True
    yaml_rt.indent(mapping=2, sequence=4, offset=2)
    yaml_rt.width = 4096

    try:
        with target_path.open("r", encoding="utf-8") as handle:
            doc = yaml_rt.load(handle)
    except HookSurfaceError:
        raise
    except Exception as exc:  # noqa: BLE001 - surfaced as one actionable error
        raise HookSurfaceError(
            f"Could not read/parse YAML hook target at {target_path}: {exc}"
        ) from exc
    if doc is None:
        raise HookSurfaceError(f"YAML hook target at {target_path} is empty")
    if not hasattr(doc, "items"):
        raise HookSurfaceError(
            f"YAML hook target at {target_path} must parse to a mapping"
        )

    mapped_hooks = resolve_target_hooks(target_cfg)
    merge_hook_payload_into_yaml_doc(doc, target_cfg, mapped_hooks)

    buffer = io.StringIO()
    yaml_rt.dump(doc, buffer)
    return check_or_write_text(
        target_path, buffer.getvalue(), check=check, dry_run=dry_run
    )


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

        target_format = target_cfg.get("format", "json")
        if target_format not in ("json", "yaml"):
            raise HookSurfaceError(
                f"Target {target_name!r} has unsupported `format` "
                f"{target_format!r} (expected 'json' or 'yaml')"
            )

        if target_format == "yaml":
            message, changed = apply_yaml_target(
                target_path, target_cfg, check=check, dry_run=dry_run
            )
            results.append(message)
            drift_found = drift_found or changed
            continue

        existing = (
            load_jsonc(target_path)
            if target_path.exists() and target_path.suffix == ".jsonc"
            else (load_json(target_path) if target_path.exists() else {})
        )
        payload = build_target_payload(existing, target_cfg)
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
    # A REFUSED write (currently only a live-gateway-blocked Hermes target)
    # is a failure to converge, not routine drift -- it must exit non-zero
    # regardless of --check/--dry-run, mirroring
    # `materialize_shared_agent_surface.py`'s main(), whose orchestrator
    # (`refresh_agent_surfaces.py`) keys its ok/fail summary off the process
    # exit code alone.
    refused = [line for line in results if line.startswith("REFUSED")]
    if refused:
        return 1
    if args.check and drift_found:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
