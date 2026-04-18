"""Materialize the shared FLOSSI0ULLK agent surface into native agent configs.

Canonical source of truth:
  - `FLOSS/shared-agent-surface.json` for workspace identity, targets, and context
  - workspace-root `.mcp.json` for the shared MCP registry

Current projections:
  - `.gemini/settings.json`
  - `opworkers/opencode.jsonc`
  - `.vibe/config.toml`
  - `.vibe/agents/*.toml`
  - `vibe-floss.ps1`
  - mirror `.mcp.json` copies declared by the manifest
  - `.agent-surface/context/*` when `shared-context-surface.json` is present
  - `.agent-surface/hooks/*` and configured native hook projections such as:
    - `.claude/settings.json`
    - `.gemini/settings.json`
    when `shared-hook-surface.json` is present
  - `.agent-surface/skills/*` and configured native skill projections such as:
    - `%USERPROFILE%/.codex/skills/flossi0ullk-*`
    - `.claude/skills/flossi0ullk-*`
    - `.gemini/skills/flossi0ullk-*`
    - `opworkers/.opencode/skills/flossi0ullk-*`
    when `shared-skill-surface.json` is present

Design rules:
  - one-way projection only
  - preserve unrelated agent-native settings
  - plain JSON output even when a target supports JSONC
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import textwrap
from typing import Any

from materialize_shared_context_surface import (
    materialize as materialize_context_surface,
)
from materialize_shared_hook_surface import materialize as materialize_hook_surface
from materialize_shared_skill_surface import materialize as materialize_skill_surface

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-agent-surface.json"
DEFAULT_CONTEXT_MANIFEST_PATH = REPO_ROOT / "shared-context-surface.json"
DEFAULT_HOOK_MANIFEST_PATH = REPO_ROOT / "shared-hook-surface.json"
DEFAULT_SKILL_MANIFEST_PATH = REPO_ROOT / "shared-skill-surface.json"


class SharedSurfaceError(Exception):
    """Raised for manifest, source, or target projection problems."""


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SharedSurfaceError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SharedSurfaceError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SharedSurfaceError(f"Expected JSON object in {path}")
    return data


def strip_jsonc_comments(text: str) -> str:
    """Remove // and /* */ comments while preserving string literals."""
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
        raise SharedSurfaceError(f"Missing file: {path}") from exc
    try:
        data = json.loads(strip_jsonc_comments(text))
    except json.JSONDecodeError as exc:
        raise SharedSurfaceError(f"Invalid JSONC in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SharedSurfaceError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def normalized_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(merged.get(key), dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def substitute_templates(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        updated = value
        for key, replacement in replacements.items():
            updated = updated.replace(f"${{{key}}}", replacement)
        return updated
    if isinstance(value, list):
        return [substitute_templates(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: substitute_templates(item, replacements) for key, item in value.items()
        }
    return value


def toml_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise SharedSurfaceError(f"Unsupported TOML scalar value: {value!r}")


def toml_list(values: list[Any]) -> str:
    return "[" + ", ".join(toml_scalar(value) for value in values) + "]"


def toml_inline_table(mapping: dict[str, Any]) -> str:
    rendered = ", ".join(
        f"{key} = {toml_scalar(value)}" for key, value in mapping.items()
    )
    return "{ " + rendered + " }"


def resolve_manifest(workspace_root: Path, manifest_path: Path) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    if not isinstance(manifest.get("targets"), dict):
        raise SharedSurfaceError(
            f"{manifest_path} must contain an object-valued `targets` field"
        )
    if (
        not isinstance(manifest.get("mcp_source"), str)
        or not manifest["mcp_source"].strip()
    ):
        raise SharedSurfaceError(
            f"{manifest_path} must contain a non-empty `mcp_source`"
        )
    if "context_pointers" in manifest and not isinstance(
        manifest["context_pointers"], list
    ):
        raise SharedSurfaceError(
            f"{manifest_path} field `context_pointers` must be a list"
        )

    source_path = workspace_root / manifest["mcp_source"]
    source_data = load_json(source_path)
    mcp_servers = source_data.get("mcpServers")
    if not isinstance(mcp_servers, dict):
        raise SharedSurfaceError(
            f"{source_path} must contain an object-valued `mcpServers` field"
        )

    manifest["_resolved_mcp_source_path"] = str(source_path)
    manifest["_resolved_mcp"] = source_data
    return manifest


def build_context_pack(manifest: dict[str, Any]) -> str:
    workspace_name = manifest.get(
        "workspace_name", manifest.get("workspace_id", "workspace")
    )
    workspace_id = manifest.get("workspace_id", workspace_name)
    manifest_version = manifest.get("manifest_version", "?")
    context_pointers = manifest.get("context_pointers", [])
    lines = [
        "# Shared Context Pointers",
        "",
        f"Workspace: `{workspace_name}`",
        f"Workspace ID: `{workspace_id}`",
        f"Manifest version: `{manifest_version}`",
        "",
        "Use these canonical entry points before expanding into deeper context.",
        "Retrieve selectively; do not bulk-load the entire workspace or `_reference/`.",
        "",
        "## Canonical Entry Points",
        "",
    ]
    for pointer in context_pointers:
        lines.append(f"- `{pointer}`")
    lines.extend(
        [
            "",
            "## Shared Surface Rules",
            "",
            "- `.mcp.json` is the canonical shared MCP registry for this workspace.",
            "- Agent-native configs are generated views, not the source of truth.",
            "- This file is generated by `FLOSS/scripts/materialize_shared_agent_surface.py`.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_gemini_payload(
    existing: dict[str, Any], shared_mcp: dict[str, Any]
) -> dict[str, Any]:
    payload = dict(existing)
    payload["mcpServers"] = shared_mcp
    return payload


def convert_mcp_server_to_opencode(name: str, server: dict[str, Any]) -> dict[str, Any]:
    command = server.get("command")
    args = server.get("args") or []
    env = server.get("env")
    if not isinstance(command, str) or not command.strip():
        raise SharedSurfaceError(
            f"Shared MCP server {name!r} cannot be projected to OpenCode without a `command` string"
        )
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise SharedSurfaceError(
            f"Shared MCP server {name!r} has non-string args and cannot be projected to OpenCode"
        )
    payload: dict[str, Any] = {
        "command": [command, *args],
        "type": "local",
    }
    if env is not None:
        if not isinstance(env, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in env.items()
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} has non-string env values and cannot be projected to OpenCode"
            )
        payload["environment"] = env
    return payload


def build_opencode_payload(
    existing: dict[str, Any], shared_mcp: dict[str, Any]
) -> dict[str, Any]:
    payload = dict(existing)
    existing_mcp = payload.get("mcp", {})
    if existing_mcp is None:
        existing_mcp = {}
    if not isinstance(existing_mcp, dict):
        raise SharedSurfaceError(
            "OpenCode config field `mcp` must be an object if present"
        )
    merged_mcp = dict(existing_mcp)
    for name, server in shared_mcp.items():
        if not isinstance(server, dict):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} must be a JSON object"
            )
        merged_mcp[name] = convert_mcp_server_to_opencode(name, server)
    payload["mcp"] = merged_mcp
    return payload


def resolve_manifest_path(workspace_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (workspace_root / path).resolve()


def build_vibe_server_spec(
    workspace_root: Path,
    name: str,
    server: dict[str, Any],
    override: dict[str, Any] | None,
) -> dict[str, Any]:
    replacements = {
        "workspace_root": workspace_root.as_posix(),
        "repo_root": (workspace_root / "FLOSS").resolve().as_posix(),
    }
    merged = deep_merge(server, override or {})
    merged = substitute_templates(merged, replacements)

    command = merged.get("command")
    url = merged.get("url")
    if isinstance(command, str) and command.strip():
        transport = str(merged.get("transport", "stdio")).strip() or "stdio"
    elif isinstance(url, str) and url.strip():
        transport = str(merged.get("transport", "http")).strip() or "http"
    else:
        raise SharedSurfaceError(
            f"Vibe MCP server {name!r} must define either `command` or `url`"
        )

    spec: dict[str, Any] = {"name": name, "transport": transport}
    if transport == "stdio":
        if not isinstance(command, str) or not command.strip():
            raise SharedSurfaceError(
                f"Vibe MCP server {name!r} requires a string `command` for stdio transport"
            )
        args = merged.get("args", [])
        if not isinstance(args, list) or not all(
            isinstance(item, str) for item in args
        ):
            raise SharedSurfaceError(
                f"Vibe MCP server {name!r} stdio args must be a list of strings"
            )
        env = merged.get("env")
        if env is not None and (
            not isinstance(env, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in env.items()
            )
        ):
            raise SharedSurfaceError(
                f"Vibe MCP server {name!r} stdio env must be a string map"
            )
        spec["command"] = command
        spec["args"] = args
        if env:
            spec["env"] = env
    else:
        if not isinstance(url, str) or not url.strip():
            raise SharedSurfaceError(
                f"Vibe MCP server {name!r} requires a string `url` for HTTP transport"
            )
        spec["url"] = url
        headers = merged.get("headers")
        if headers is not None:
            if not isinstance(headers, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in headers.items()
            ):
                raise SharedSurfaceError(
                    f"Vibe MCP server {name!r} HTTP headers must be a string map"
                )
            spec["headers"] = headers

    for field_name in (
        "startup_timeout_sec",
        "tool_timeout_sec",
        "sampling_enabled",
        "prompt",
        "api_key_env",
        "api_key_header",
        "api_key_format",
    ):
        if field_name in merged:
            spec[field_name] = merged[field_name]

    return spec


def build_vibe_config(
    workspace_root: Path,
    shared_mcp: dict[str, Any],
    vibe_cfg: dict[str, Any],
) -> str:
    skill_paths = [
        resolve_manifest_path(workspace_root, raw_path).as_posix()
        for raw_path in vibe_cfg.get("skill_paths", [])
    ]
    enabled_skills = vibe_cfg.get("enabled_skills", [])
    mcp_names = vibe_cfg.get("mcp_servers") or list(shared_mcp.keys())
    if not isinstance(mcp_names, list) or not all(
        isinstance(item, str) for item in mcp_names
    ):
        raise SharedSurfaceError(
            "Vibe target field `mcp_servers` must be a list of names"
        )
    overrides = vibe_cfg.get("server_overrides", {})
    if overrides and not isinstance(overrides, dict):
        raise SharedSurfaceError(
            "Vibe target field `server_overrides` must be an object"
        )

    server_specs: list[dict[str, Any]] = []
    for name in mcp_names:
        if name not in shared_mcp:
            raise SharedSurfaceError(
                f"Vibe target references unknown shared MCP server {name!r}"
            )
        override = overrides.get(name)
        if override is not None and not isinstance(override, dict):
            raise SharedSurfaceError(
                f"Vibe server override for {name!r} must be a JSON object"
            )
        server_specs.append(
            build_vibe_server_spec(workspace_root, name, shared_mcp[name], override)
        )

    lines = [
        f"active_model = {toml_scalar(vibe_cfg.get('active_model', 'devstral-small'))}",
        f"context_warnings = {toml_scalar(bool(vibe_cfg.get('context_warnings', True)))}",
        f"enable_auto_update = {toml_scalar(bool(vibe_cfg.get('enable_auto_update', True)))}",
    ]
    if skill_paths:
        lines.append(f"skill_paths = {toml_list(skill_paths)}")
    if enabled_skills:
        if not isinstance(enabled_skills, list) or not all(
            isinstance(item, str) for item in enabled_skills
        ):
            raise SharedSurfaceError(
                "Vibe target field `enabled_skills` must be a list of strings"
            )
        lines.append(f"enabled_skills = {toml_list(enabled_skills)}")

    for spec in server_specs:
        lines.extend(["", "[[mcp_servers]]"])
        lines.append(f"name = {toml_scalar(spec['name'])}")
        lines.append(f"transport = {toml_scalar(spec['transport'])}")
        if spec["transport"] == "stdio":
            lines.append(f"command = {toml_scalar(spec['command'])}")
            if spec.get("args"):
                lines.append(f"args = {toml_list(spec['args'])}")
            if spec.get("env"):
                lines.append(f"env = {toml_inline_table(spec['env'])}")
        else:
            lines.append(f"url = {toml_scalar(spec['url'])}")
            if spec.get("headers"):
                lines.append(f"headers = {toml_inline_table(spec['headers'])}")
        for field_name in (
            "startup_timeout_sec",
            "tool_timeout_sec",
            "sampling_enabled",
            "prompt",
            "api_key_env",
            "api_key_header",
            "api_key_format",
        ):
            if field_name in spec:
                value = spec[field_name]
                if field_name in {
                    "startup_timeout_sec",
                    "tool_timeout_sec",
                } and isinstance(value, int):
                    value = float(value)
                lines.append(f"{field_name} = {toml_scalar(value)}")

    return "\n".join(lines) + "\n"


def build_vibe_agent(agent_spec: dict[str, Any]) -> str:
    if not isinstance(agent_spec.get("name"), str) or not agent_spec["name"].strip():
        raise SharedSurfaceError("Every Vibe agent spec must define a non-empty `name`")

    lines = [
        f"display_name = {toml_scalar(agent_spec.get('display_name', agent_spec['name']))}",
        f"description = {toml_scalar(agent_spec.get('description', ''))}",
        f"safety = {toml_scalar(agent_spec.get('safety', 'safe'))}",
    ]
    for field_name in (
        "agent_type",
        "auto_approve",
        "active_model",
        "system_prompt_id",
    ):
        if field_name in agent_spec:
            lines.append(f"{field_name} = {toml_scalar(agent_spec[field_name])}")

    enabled_tools = agent_spec.get("enabled_tools")
    if enabled_tools is not None:
        if not isinstance(enabled_tools, list) or not all(
            isinstance(item, str) for item in enabled_tools
        ):
            raise SharedSurfaceError(
                f"Vibe agent {agent_spec['name']!r} field `enabled_tools` must be a list of strings"
            )
        lines.append(f"enabled_tools = {toml_list(enabled_tools)}")

    disabled_tools = agent_spec.get("disabled_tools")
    if disabled_tools is not None:
        if not isinstance(disabled_tools, list) or not all(
            isinstance(item, str) for item in disabled_tools
        ):
            raise SharedSurfaceError(
                f"Vibe agent {agent_spec['name']!r} field `disabled_tools` must be a list of strings"
            )
        lines.append(f"disabled_tools = {toml_list(disabled_tools)}")

    return "\n".join(lines) + "\n"


def build_vibe_launcher(workspace_root: Path, vibe_cfg: dict[str, Any]) -> str:
    env_rel = str(vibe_cfg.get("env_path", "FLOSS/.env"))
    python_exe = str(vibe_cfg.get("python_exe", "C:/Python313/python.exe"))
    script = f"""
    $ErrorActionPreference = "Stop"

    $workspaceRoot = (Split-Path -Parent $PSCommandPath)
    $envFile = Join-Path $workspaceRoot "{env_rel.replace('/', '\\')}"
    $vibeFallback = Join-Path $env:USERPROFILE ".local\\bin\\vibe.exe"
    $vibeCommand = Get-Command vibe.exe -ErrorAction SilentlyContinue
    if (-not $vibeCommand) {{
        $vibeCommand = Get-Command vibe -ErrorAction SilentlyContinue
    }}
    if ($vibeCommand) {{
        $vibeExe = $vibeCommand.Source
    }} elseif (Test-Path $vibeFallback) {{
        $vibeExe = $vibeFallback
    }} else {{
        throw "vibe executable not found. Install Vibe or add it to PATH."
    }}

    $pythonCandidates = @(
        "py.exe",
        "python.exe",
        "python3.exe",
        "{python_exe}"
    ) | Select-Object -Unique
    $pythonExe = $null
    foreach ($candidate in $pythonCandidates) {{
        if ($candidate -match "[\\\\/:]") {{
            if (Test-Path $candidate) {{
                $pythonExe = $candidate
                break
            }}
            continue
        }}
        $pythonCommand = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($pythonCommand) {{
            $pythonExe = $pythonCommand.Source
            break
        }}
    }}

    if (Test-Path $envFile) {{
        foreach ($rawLine in Get-Content $envFile) {{
            $line = $rawLine.Trim()
            if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {{
                continue
            }}
            $key, $value = $line.Split("=", 2)
            $key = $key.Trim()
            $value = $value.Trim()
            if ($key) {{
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }}
        }}
    }}

    if ($pythonExe) {{
        $trustScript = @'
from pathlib import Path
import json
import tomllib

workspace = Path.cwd().resolve()
path = Path.home() / ".vibe" / "trusted_folders.toml"
trusted = []
untrusted = []
if path.exists():
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {{}}
    trusted = [str(Path(item).expanduser().resolve()) for item in data.get("trusted", [])]
    untrusted = [str(Path(item).expanduser().resolve()) for item in data.get("untrusted", [])]
workspace_str = str(workspace)
if workspace_str not in trusted:
    trusted.append(workspace_str)
untrusted = [item for item in untrusted if item != workspace_str]
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(
    "trusted = " + json.dumps(trusted) + "\\n"
    + "untrusted = " + json.dumps(untrusted) + "\\n",
    encoding="utf-8",
)
'@
        Push-Location $workspaceRoot
        try {{
            $trustScript | & $pythonExe -
        }} finally {{
            Pop-Location
        }}
    }}

    $argList = [System.Collections.Generic.List[string]]::new()
    $hasWorkdir = $false
    foreach ($arg in $args) {{
        if ($arg -eq "--workdir") {{
            $hasWorkdir = $true
        }}
        $argList.Add($arg)
    }}
    if (-not $hasWorkdir) {{
        $argList.Add("--workdir")
        $argList.Add($workspaceRoot)
    }}

    & $vibeExe @argList
    exit $LASTEXITCODE
    """
    return textwrap.dedent(script).strip() + "\n"


def check_or_write(
    path: Path, payload: dict[str, Any], *, check: bool, dry_run: bool
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


def materialize(
    workspace_root: Path, manifest_path: Path, *, check: bool, dry_run: bool
) -> tuple[list[str], bool]:
    manifest = resolve_manifest(workspace_root, manifest_path)
    shared_mcp = manifest["_resolved_mcp"]["mcpServers"]
    results: list[str] = []
    drift_found = False

    for mirror_rel in manifest.get("mcp_mirrors", []):
        mirror_path = workspace_root / mirror_rel
        message, changed = check_or_write(
            mirror_path,
            manifest["_resolved_mcp"],
            check=check,
            dry_run=dry_run,
        )
        results.append(message)
        drift_found = drift_found or changed

    context_pack_path = manifest.get("context_pack_path")
    if isinstance(context_pack_path, str) and context_pack_path.strip():
        path = workspace_root / context_pack_path
        content = build_context_pack(manifest)
        message, changed = check_or_write_text(
            path, content, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    targets: dict[str, Any] = manifest["targets"]

    gemini_cfg = targets.get("gemini")
    if isinstance(gemini_cfg, dict) and gemini_cfg.get("settings_path"):
        gemini_path = workspace_root / gemini_cfg["settings_path"]
        existing = load_json(gemini_path) if gemini_path.exists() else {}
        payload = build_gemini_payload(existing, shared_mcp)
        message, changed = check_or_write(
            gemini_path, payload, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    opencode_cfg = targets.get("opencode")
    if isinstance(opencode_cfg, dict) and opencode_cfg.get("settings_path"):
        opencode_path = workspace_root / opencode_cfg["settings_path"]
        existing = load_jsonc(opencode_path)
        payload = build_opencode_payload(existing, shared_mcp)
        message, changed = check_or_write(
            opencode_path, payload, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    vibe_cfg = targets.get("vibe")
    if isinstance(vibe_cfg, dict) and vibe_cfg.get("config_path"):
        vibe_config_path = workspace_root / str(vibe_cfg["config_path"])
        vibe_config = build_vibe_config(workspace_root, shared_mcp, vibe_cfg)
        message, changed = check_or_write_text(
            vibe_config_path, vibe_config, check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

        agents_dir_raw = vibe_cfg.get("agents_dir")
        if agents_dir_raw is not None and not isinstance(agents_dir_raw, str):
            raise SharedSurfaceError("Vibe target field `agents_dir` must be a string")
        agents_dir = workspace_root / str(agents_dir_raw or ".vibe/agents")
        for agent_spec in vibe_cfg.get("agents", []):
            if not isinstance(agent_spec, dict):
                raise SharedSurfaceError("Vibe target `agents` entries must be objects")
            agent_name = str(agent_spec.get("name", "")).strip()
            if not agent_name:
                raise SharedSurfaceError(
                    "Vibe target agents require a non-empty `name`"
                )
            agent_path = agents_dir / f"{agent_name}.toml"
            content = build_vibe_agent(agent_spec)
            message, changed = check_or_write_text(
                agent_path, content, check=check, dry_run=dry_run
            )
            results.append(message)
            drift_found = drift_found or changed

        launcher_raw = vibe_cfg.get("launcher_path")
        if launcher_raw is not None:
            if not isinstance(launcher_raw, str) or not launcher_raw.strip():
                raise SharedSurfaceError(
                    "Vibe target field `launcher_path` must be a non-empty string"
                )
            launcher_path = workspace_root / launcher_raw
            launcher_content = build_vibe_launcher(workspace_root, vibe_cfg)
            message, changed = check_or_write_text(
                launcher_path, launcher_content, check=check, dry_run=dry_run
            )
            results.append(message)
            drift_found = drift_found or changed

    if DEFAULT_CONTEXT_MANIFEST_PATH.exists():
        context_results, context_drift = materialize_context_surface(
            workspace_root=workspace_root,
            manifest_path=DEFAULT_CONTEXT_MANIFEST_PATH,
            output_dir=workspace_root / ".agent-surface" / "context",
            check=check,
            dry_run=dry_run,
        )
        results.extend(context_results)
        drift_found = drift_found or context_drift

    if DEFAULT_HOOK_MANIFEST_PATH.exists():
        hook_results, hook_drift = materialize_hook_surface(
            workspace_root=workspace_root,
            manifest_path=DEFAULT_HOOK_MANIFEST_PATH,
            output_dir=workspace_root / ".agent-surface" / "hooks",
            check=check,
            dry_run=dry_run,
        )
        results.extend(hook_results)
        drift_found = drift_found or hook_drift

    if DEFAULT_SKILL_MANIFEST_PATH.exists():
        skill_results, skill_drift = materialize_skill_surface(
            workspace_root=workspace_root,
            manifest_path=DEFAULT_SKILL_MANIFEST_PATH,
            output_dir=workspace_root / ".agent-surface" / "skills",
            check=check,
            dry_run=dry_run,
        )
        results.extend(skill_results)
        drift_found = drift_found or skill_drift

    return results, drift_found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize the shared FLOSSI0ULLK agent surface into native configs",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help=f"Workspace root containing .mcp.json (default: {DEFAULT_WORKSPACE_ROOT})",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help=f"Shared manifest path (default: {DEFAULT_MANIFEST_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the write plan without changing files",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if materialized files drift from the canonical source",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    manifest_path = args.manifest.resolve()
    results, drift_found = materialize(
        workspace_root,
        manifest_path,
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
