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
import io
import json
import os
from pathlib import Path
import subprocess
import textwrap
from typing import Any
from urllib import error, request

from materialize_shared_context_surface import (
    materialize as materialize_context_surface,
)
from materialize_shared_hook_surface import materialize as materialize_hook_surface
from materialize_shared_skill_surface import materialize as materialize_skill_surface
from materialize_shared_agent_memory import materialize as materialize_memory_surface
from materialize_shared_ai_roster import materialize as materialize_ai_roster_surface

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-agent-surface.json"
DEFAULT_CONTEXT_MANIFEST_PATH = REPO_ROOT / "shared-context-surface.json"
DEFAULT_HOOK_MANIFEST_PATH = REPO_ROOT / "shared-hook-surface.json"
DEFAULT_SKILL_MANIFEST_PATH = REPO_ROOT / "shared-skill-surface.json"
DEFAULT_MEMORY_MANIFEST_PATH = REPO_ROOT / "shared-agent-memory-surface.json"
DEFAULT_AI_ROSTER_MANIFEST_PATH = REPO_ROOT / "shared-ai-roster-surface.json"


class SharedSurfaceError(Exception):
    """Raised for manifest, source, or target projection problems."""


def require_module(module_name: str, target: str) -> Any:
    """Import a round-trip serializer, failing loudly for one target only.

    Never fall back to a non-round-trip writer -- that would silently strip
    comments and reorder keys in large hand-maintained configs.
    """
    import importlib

    try:
        return importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SharedSurfaceError(
            f"Target {target!r} requires the {module_name!r} package "
            f"(pip install {module_name.split('.')[0]})"
        ) from exc


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


def classify_transport(name: str, server: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Classify a shared MCP server entry as `stdio` or `http`.

    Returns `(transport, spec)`. For stdio, `spec` has `command` (str),
    `args` (list[str]) and `env` (dict[str, str] | None). For http, `spec`
    has `url` (str) and `headers` (dict[str, str] | None).

    This is the single source of transport dispatch for every target. Do not
    reimplement it per target -- divergent copies are what broke the surface
    on 2026-07-17.

    Precedence when a server entry defines both `command` and `url`: stdio
    wins and `url` is silently ignored. This is intentional, existing
    behavior -- documented here so downstream targets (OpenCode, Codex,
    Hermes, ...) don't each reinvent a different tie-break.
    """
    if not isinstance(server, dict):
        raise SharedSurfaceError(f"Shared MCP server {name!r} must be a JSON object")

    command = server.get("command")
    url = server.get("url")

    if isinstance(command, str) and command.strip():
        args = server.get("args") or []
        if not isinstance(args, list) or not all(
            isinstance(item, str) for item in args
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} stdio `args` must be a list of strings"
            )
        env = server.get("env")
        if env is not None and (
            not isinstance(env, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in env.items()
            )
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} stdio `env` must be a string map"
            )
        return "stdio", {
            "command": command,
            "args": list(args),
            "env": dict(env) if env else None,
        }

    if isinstance(url, str) and url.strip():
        headers = server.get("headers")
        if headers is not None and (
            not isinstance(headers, dict)
            or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in headers.items()
            )
        ):
            raise SharedSurfaceError(
                f"Shared MCP server {name!r} HTTP `headers` must be a string map"
            )
        return "http", {"url": url, "headers": dict(headers) if headers else None}

    raise SharedSurfaceError(
        f"Shared MCP server {name!r} must define either `command` or `url`"
    )


def convert_mcp_server_to_opencode(name: str, server: dict[str, Any]) -> dict[str, Any]:
    """Project a shared MCP server into OpenCode's config shape.

    OpenCode uses `{"type": "local", "command": [...]}` for stdio and
    `{"type": "remote", "url": ...}` for HTTP (the shape its own
    `openwork-browser`/`chrome` entries already use).
    """
    transport, spec = classify_transport(name, server)

    if transport == "http":
        return {"type": "remote", "url": spec["url"]}

    payload: dict[str, Any] = {
        "command": [spec["command"], *spec["args"]],
        "type": "local",
    }
    if spec["env"]:
        payload["environment"] = spec["env"]
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


# Transport fields the propagator owns on a managed server. Everything else
# on that server (tools tables, timeouts, approval modes) is preserved.
MANAGED_TRANSPORT_FIELDS = ("type", "command", "args", "url")


def ensure_no_name_map_collisions(
    shared_mcp: dict[str, Any], name_map: dict[str, str], target: str
) -> None:
    """Raise if two shared servers would collide on one target name.

    Two shared servers silently colliding on one target name would
    last-write-win and lose a server's config with no warning -- and this
    comes from a manifest file, so that's silent data loss. Shared by every
    writer (Codex, Hermes, ...) that accepts a `name_map`.
    """
    target_to_shared: dict[str, list[str]] = {}
    for shared_name in shared_mcp:
        target_name = name_map.get(shared_name, shared_name)
        target_to_shared.setdefault(target_name, []).append(shared_name)
    for target_name, shared_names in target_to_shared.items():
        if len(shared_names) > 1:
            raise SharedSurfaceError(
                f"{target} name_map collision: shared servers {shared_names!r} "
                f"all map to target name {target_name!r}"
            )


def apply_codex_mcp(
    doc: Any,
    shared_mcp: dict[str, Any],
    name_map: dict[str, str],
    overrides: dict[str, Any],
) -> Any:
    """Merge shared MCP servers into a parsed Codex config.toml document.

    Codex requires an explicit transport discriminator: `type = "stdio"` with
    command/args, or `type = "streamable_http"` with url. A bare `url` key is
    rejected with `url is not supported for stdio`.

    `env` is treated as managed only when the shared entry defines it, so a
    target-local templated env block survives.

    Precedence, low to high: managed transport fields, then whatever already
    existed on the target entry, then manifest `overrides` -- overrides beat
    everything, including pre-existing file content. This matches the
    contract the Hermes writer (Task 6) uses.

    Scalar transport keys are written into a fresh table before any preserved
    sub-tables are re-attached (overrides land last, per the precedence rule
    above, and may be scalars or tables). On tomlkit 0.15.0
    this ordering is not load-bearing -- `Container` reliably bubbles scalar
    keys ahead of sub-tables at render time regardless of assignment order
    (verified empirically: assigning a table then a scalar into the same
    `tomlkit.table()` still renders the scalar inside `[mcp_servers.<name>]`,
    not the sub-table). We keep the ordering anyway as cheap defense-in-depth
    against a future tomlkit behavior change, not because today's output
    depends on it.
    """
    tomlkit = require_module("tomlkit", "codex")

    # Detect name_map collisions up front (shared with the Hermes writer).
    ensure_no_name_map_collisions(shared_mcp, name_map, "Codex")

    if "mcp_servers" not in doc:
        doc["mcp_servers"] = tomlkit.table(is_super_table=True)
    servers = doc["mcp_servers"]

    for shared_name, server in shared_mcp.items():
        target_name = name_map.get(shared_name, shared_name)
        transport, spec = classify_transport(shared_name, server)

        existing = servers.get(target_name)
        preserved_scalars: dict[str, Any] = {}
        preserved_tables: dict[str, Any] = {}
        preserved_env: Any = None
        if existing is not None:
            if not hasattr(existing, "items"):
                raise SharedSurfaceError(
                    f"Codex mcp_servers.{target_name!r} exists but is not a "
                    f"table (got {type(existing).__name__}); refusing to "
                    "merge into it"
                )
            for key, value in existing.items():
                if key in MANAGED_TRANSPORT_FIELDS:
                    continue
                if key == "env":
                    preserved_env = value
                elif isinstance(
                    value,
                    (tomlkit.items.Table, tomlkit.items.AoT, tomlkit.items.InlineTable),
                ):
                    preserved_tables[key] = value
                else:
                    preserved_scalars[key] = value

        entry = tomlkit.table()

        # 1. managed scalars
        if transport == "http":
            entry["type"] = "streamable_http"
            entry["url"] = spec["url"]
        else:
            entry["type"] = "stdio"
            entry["command"] = spec["command"]
            entry["args"] = spec["args"]

        # 2. preserved scalars (startup_timeout_sec, enabled, ...)
        for key, value in preserved_scalars.items():
            entry[key] = value

        # 3. tables, or TOML re-parents every later scalar into them (see
        #    docstring above -- defense-in-depth, not load-bearing today).
        #    `env` is managed only when the shared entry defines one.
        if transport == "stdio" and spec["env"] is not None:
            entry["env"] = spec["env"]
        elif preserved_env is not None:
            entry["env"] = preserved_env
        for key, value in preserved_tables.items():
            entry[key] = value

        # 4. manifest overrides go LAST -- overrides beat everything,
        #    including pre-existing file content.
        for key, value in (overrides.get(shared_name) or {}).items():
            entry[key] = value

        servers[target_name] = entry

    return doc


def _pid_alive(pid: int) -> bool:
    """Return True if `pid` is a live process, or if liveness cannot be
    determined.

    This is a liveness *guard*, not a liveness *report*: its only purpose is
    to stop a config write while a Hermes gateway might still be running and
    about to clobber the file on shutdown. So an inability to determine
    liveness (`tasklist` missing or blocked by policy, an unexpected
    non-zero exit, empty output) must fail CLOSED -- treated as "alive" so
    the caller refuses to write -- rather than fail open into the exact
    silent data loss this guard exists to prevent.
    """
    if os.name == "nt":
        try:
            completed = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return True  # could not even invoke tasklist -- fail closed
        if completed.returncode != 0 or not completed.stdout.strip():
            return True  # no usable output to judge liveness -- fail closed
        # `tasklist /FI "PID eq N"` does exact PID filtering server-side, so
        # this substring check is belt-and-suspenders, not the actual safety
        # mechanism (verified: "PID eq 122" does not match a running pid
        # 1220 -- tasklist's own filter already disambiguates that).
        return str(pid) in completed.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True  # e.g. PermissionError -- process exists, fail closed
    return True


def hermes_gateway_alive(home: Path) -> int | None:
    """Return the PID of a live Hermes gateway for `home`, else None.

    A running gateway rewrites its own config.yaml on shutdown and would
    clobber anything written underneath it, so writes must be refused while
    it is alive.
    """
    pid_file = home / "gateway.pid"
    if not pid_file.exists():
        return None
    try:
        payload = json.loads(pid_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    pid = payload.get("pid")
    if not isinstance(pid, int):
        return None
    return pid if _pid_alive(pid) else None


def apply_hermes_mcp(
    data: Any,
    shared_mcp: dict[str, Any],
    name_map: dict[str, str],
    overrides: dict[str, Any],
) -> Any:
    """Merge shared MCP servers into a parsed Hermes config.yaml document.

    Hermes supports Streamable HTTP natively via `type: http` + `url`, and
    stdio via `command`/`args`/`env`.

    Precedence matches `apply_codex_mcp`: managed transport fields, then
    whatever already existed on the entry, then manifest `overrides` last --
    overrides beat everything. `env` follows the same rule as Codex: the
    shared entry's `env` replaces any existing `env` when it defines one;
    otherwise a target-local `env` block survives untouched for a stdio
    entry, and is dropped as stale if the entry is converted to http.

    Unlike the Codex writer this mutates the existing mapping in place. YAML
    mappings have no positional/header hazard, so there is no need to rebuild
    the node, and mutating in place is what lets ruamel preserve comments.

    Only the fields belonging to the transport being *vacated* are cleared
    before the managed fields are (re)assigned -- never every managed field
    unconditionally. `CommentedMap.__setitem__` preserves an existing key's
    position; it is `del` followed by re-add that moves a key to the end of
    the mapping. Deleting unconditionally therefore reordered every touched
    entry on every run, including a true no-op merge where nothing actually
    changed -- which breaks Task 9's fidelity gate (regenerating must
    produce no spurious diff against a verified-good config).

    A `target_name` that exists but isn't a mapping (including a YAML null,
    e.g. `serena:` with nothing after it) raises `SharedSurfaceError` rather
    than being silently coerced or merged into -- consistent with the
    non-mapping guard `apply_codex_mcp` applies to malformed TOML tables.

    Callers are responsible for checking `hermes_gateway_alive()` and
    importing `ruamel.yaml` (via `require_module`) before calling this --
    this function operates on an already-parsed document and needs neither.
    """
    ensure_no_name_map_collisions(shared_mcp, name_map, "Hermes")

    servers = data.get("mcp_servers")
    if servers is None:
        data["mcp_servers"] = {}
        servers = data["mcp_servers"]

    for shared_name, server in shared_mcp.items():
        target_name = name_map.get(shared_name, shared_name)
        transport, spec = classify_transport(shared_name, server)

        # `.get()` can't distinguish "key absent" from "key present with a
        # YAML null value" -- both come back None. Check membership
        # explicitly so a present-but-null entry hits the malformed-entry
        # guard instead of silently becoming `entry = None` and crashing
        # later with a TypeError.
        if target_name in servers:
            existing = servers[target_name]
            if not hasattr(existing, "items"):
                raise SharedSurfaceError(
                    f"Hermes mcp_servers.{target_name!r} exists but is not a "
                    f"mapping (got {type(existing).__name__}); refusing to "
                    "merge into it"
                )
        else:
            servers[target_name] = {}
        entry = servers[target_name]

        if transport == "http":
            for key in ("command", "args", "env"):
                entry.pop(key, None)
            entry["type"] = "http"
            entry["url"] = spec["url"]
        else:
            for key in ("type", "url"):
                entry.pop(key, None)
            entry["command"] = spec["command"]
            entry["args"] = spec["args"]
            if spec["env"] is not None:
                entry["env"] = spec["env"]

        for key, value in (overrides.get(shared_name) or {}).items():
            entry[key] = value

    return data


def build_opencode_agent_instruction(opencode_cfg: dict[str, Any]) -> str:
    agent_name = (
        str(opencode_cfg.get("default_agent", "openwork")).strip() or "openwork"
    )
    display_name = (
        "OpenWork"
        if agent_name.lower() == "openwork"
        else agent_name[:1].upper() + agent_name[1:]
    )
    description = str(
        opencode_cfg.get(
            "agent_description",
            "OpenWork default FLOSSI0ULLK worker generated from the shared surface.",
        )
    )
    pointers = opencode_cfg.get("startup_context_pointers", [])
    if not isinstance(pointers, list) or not all(
        isinstance(item, str) for item in pointers
    ):
        raise SharedSurfaceError(
            "OpenCode target field `startup_context_pointers` must be a list of strings"
        )
    if not pointers:
        pointers = [
            ".agent-surface/context/CONTEXT_L0.md",
            ".agent-surface/harness/HARNESS_UPDATE_PACKET.md",
            ".agent-surface/memory/AGENT_MEMORY.md",
            "AGENTMEMORY.md",
        ]

    lines = [
        "---",
        f"description: {description}",
        "mode: primary",
        "temperature: 0.2",
        "---",
        "",
        f"You are {display_name}.",
        "",
        'When the user refers to "you", they mean the OpenWork app and the current workspace.',
        "",
        "## Mandatory Startup",
        "",
        "Load these surfaces first, selectively and in order:",
        "",
    ]
    for pointer in pointers:
        lines.append(f"- `{pointer}`")
    lines.extend(
        [
            "",
            "## Shared Invariants",
            "",
            "- Repository canon wins over generated projections, agentmemory recall, and pasted status reports.",
            "- agentmemory is a recall/federation surface; promote load-bearing conclusions through repo memory, working todo, specs, ADRs, or source-chain claims.",
            "- Every load-bearing cross-agent handoff should cite or generate provenance packet evidence.",
            "- Use `.agent-surface/harness/AI_ROSTER.md` for the current aggregated AI/provider/harness roster.",
            "- Do not hand-edit generated projections when the shared manifest can be updated instead.",
            "- Use one primary writer for a concrete change set; use other models as critics, voters, or evidence sources.",
            "",
            "## Work Loop",
            "",
            "- Route context before bulk-loading files.",
            "- Make the smallest useful change against canon.",
            "- Run focused verification before claiming success.",
            "- Append durable traces or update shared memory when a finding must survive this session.",
            "",
            "## Privacy Boundary",
            "",
            "- Never copy private memory, secrets, tokens, or credentials into repo files.",
            "- Store only redacted summaries, schemas, stable pointers, and reproducible commands.",
            "",
        ]
    )
    return "\n".join(lines)


def resolve_manifest_path(workspace_root: Path, raw_path: str) -> Path:
    """Resolve a manifest-declared path against the workspace root.

    Expands both `~` (user home, e.g. `~/.codex/config.toml`) and
    environment-variable references such as `%LOCALAPPDATA%` on Windows or
    `$HOME` on POSIX (e.g. `%LOCALAPPDATA%/hermes/config.yaml`). This is the
    single path resolver every target should route through -- do not
    hand-roll a second one for a new writer.
    """
    path = Path(os.path.expandvars(raw_path)).expanduser()
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
        f"default_agent = {toml_scalar(vibe_cfg.get('default_agent', 'default'))}",
        f"include_project_context = {toml_scalar(bool(vibe_cfg.get('include_project_context', True)))}",
        f"context_warnings = {toml_scalar(bool(vibe_cfg.get('context_warnings', True)))}",
        f"enable_auto_update = {toml_scalar(bool(vibe_cfg.get('enable_auto_update', True)))}",
    ]

    agent_paths = [
        resolve_manifest_path(workspace_root, raw_path).as_posix()
        for raw_path in vibe_cfg.get("agent_paths", [])
    ]
    if agent_paths:
        lines.append(f"agent_paths = {toml_list(agent_paths)}")

    enabled_agents = vibe_cfg.get("enabled_agents", [])
    if enabled_agents:
        if not isinstance(enabled_agents, list) or not all(
            isinstance(item, str) for item in enabled_agents
        ):
            raise SharedSurfaceError(
                "Vibe target field `enabled_agents` must be a list of strings"
            )
        lines.append(f"enabled_agents = {toml_list(enabled_agents)}")

    disabled_agents = vibe_cfg.get("disabled_agents", [])
    if disabled_agents:
        if not isinstance(disabled_agents, list) or not all(
            isinstance(item, str) for item in disabled_agents
        ):
            raise SharedSurfaceError(
                "Vibe target field `disabled_agents` must be a list of strings"
            )
        lines.append(f"disabled_agents = {toml_list(disabled_agents)}")

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


def build_vibe_startup_prompt(vibe_cfg: dict[str, Any]) -> str:
    """Build the orientation prompt passed to new interactive Vibe sessions."""
    pointers = vibe_cfg.get("startup_context_pointers", [])
    if not isinstance(pointers, list) or not all(
        isinstance(item, str) for item in pointers
    ):
        raise SharedSurfaceError(
            "Vibe target field `startup_context_pointers` must be a list of strings"
        )
    if not pointers:
        pointers = [
            ".agent-surface/context/CONTEXT_L0.md",
            ".agent-surface/context/RESUMPTION.md",
            ".agent-surface/memory/AGENT_MEMORY.md",
            ".agent-surface/CONTEXT_POINTERS.md",
        ]

    lines = [
        "# FLOSSI0ULLK Vibe Startup",
        "",
        "Before proposing work, read the current shared surfaces below and align to them.",
        "",
        "## Current Hard Corrections",
        "",
        "- MVP Phase 0 substrate viability is complete. DNA/WASM/Tryorama are not the current gate.",
        "- Do not restart old Tryorama/Phase 0 work unless explicitly asked to audit evidence drift.",
        "- Current gate is orchestration substrate-bridge validation plus Phase 1 KnowledgeTriple/MVC work.",
        "- The heartbeat STOP file is intentionally present after the 2026-05-19 Groq token-burn fix.",
        "- Routine background consensus uses `balanced`; `diverse-max` is intentional spend, not default health checking.",
        "- Specs and tests lead code changes: update `FLOSS/docs/specs/` before runtime behavior changes.",
        "",
        "## Read First",
        "",
    ]
    lines.extend(f"- `{pointer}`" for pointer in pointers)
    lines.extend(
        [
            "",
            "After reading, answer with:",
            "",
            "1. current phase status in one sentence;",
            "2. any detected drift or uncertainty;",
            "3. one highest-leverage next action, if the user asks for action.",
            "",
            "This file is generated by `FLOSS/scripts/materialize_shared_agent_surface.py`.",
        ]
    )
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


def build_vibe_launcher(vibe_cfg: dict[str, Any]) -> str:
    """Build the PowerShell launcher for the local Vibe workspace projection."""
    env_rel = str(vibe_cfg.get("env_path", "FLOSS/.env"))
    python_exe = str(vibe_cfg.get("python_exe", "C:/Python313/python.exe"))
    startup_prompt_rel = str(
        vibe_cfg.get("startup_prompt_path", ".agent-surface/VIBE_STARTUP.md")
    )
    script = f"""
    $ErrorActionPreference = "Stop"

    $workspaceRoot = (Split-Path -Parent $PSCommandPath)
    $envFile = Join-Path $workspaceRoot "{env_rel.replace('/', '\\')}"
    $startupPromptPath = Join-Path $workspaceRoot "{startup_prompt_rel.replace('/', '\\')}"
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
    $hasPromptArg = $false
    $promptValueOptions = @("-p", "--prompt")
    $valueOnlyOptions = @("--agent", "--workdir", "--add-dir", "--max-turns", "--max-price", "--enabled-tools", "--output")
    $utilityOptions = @("-h", "--help", "-v", "--version", "--setup", "--resume", "-c")
    $expectingValueOnly = $false
    foreach ($arg in $args) {{
        if ($expectingValueOnly) {{
            $expectingValueOnly = $false
            $argList.Add($arg)
            continue
        }}
        if ($arg -eq "--workdir") {{
            $hasWorkdir = $true
        }}
        if ($utilityOptions -contains $arg) {{
            $hasPromptArg = $true
        }} elseif ($promptValueOptions -contains $arg) {{
            $hasPromptArg = $true
        }} elseif ($valueOnlyOptions -contains $arg) {{
            $expectingValueOnly = $true
        }} elseif (-not $arg.StartsWith("-")) {{
            $hasPromptArg = $true
        }}
        $argList.Add($arg)
    }}
    if (-not $hasWorkdir) {{
        $argList.Add("--workdir")
        $argList.Add($workspaceRoot)
    }}
    if (-not $hasPromptArg -and (Test-Path $startupPromptPath)) {{
        $argList.Add((Get-Content $startupPromptPath -Raw))
    }}

    & $vibeExe @argList
    exit $LASTEXITCODE
    """
    return textwrap.dedent(script).strip() + "\n"


def count_audit_statuses(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"valid": 0, "superseded": 0, "invalid": 0}
    for record in records:
        status = record.get("audit_status", "invalid")
        if status not in counts:
            status = "invalid"
        counts[status] += 1
    return counts


def read_roster_summary(workspace_root: Path) -> dict[str, Any]:
    roster_path = workspace_root / ".agent-surface" / "harness" / "ai-roster.json"
    try:
        roster = load_json(roster_path)
    except SharedSurfaceError:
        return {}
    summary = roster.get("summary")
    return summary if isinstance(summary, dict) else {}


def fetch_agentmemory_status(
    url: str = "http://localhost:3111/agentmemory/health",
) -> str:
    try:
        with request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return f"error:{type(exc).__name__}"
    status = payload.get("status")
    if isinstance(status, str) and status.strip():
        return status
    health = payload.get("health")
    if isinstance(health, dict) and isinstance(health.get("status"), str):
        return health["status"]
    return "unknown"


def build_doctor_report(
    *,
    workspace_root: Path,
    surface_drift: bool,
    roster_summary: dict[str, Any],
    agentmemory_status: str,
    heartbeat_stop_present: bool,
    audit_counts: dict[str, int],
) -> str:
    surface_status = "drift" if surface_drift else "clean"
    heartbeat_status = "present" if heartbeat_stop_present else "absent"
    provider_count = roster_summary.get("provider_count", "unknown")
    model_count = roster_summary.get("model_count", "unknown")
    mcp_count = roster_summary.get("mcp_server_count", "unknown")
    valid_count = audit_counts.get("valid", 0)
    superseded_count = audit_counts.get("superseded", 0)
    invalid_count = audit_counts.get("invalid", 0)

    lines = [
        "# Shared Agent Surface Doctor",
        "",
        f"Workspace: `{workspace_root.as_posix()}`",
        "",
        "## Status",
        "",
        f"- Shared surface: `{surface_status}`",
        f"- agentmemory: `{agentmemory_status}`",
        f"- Heartbeat STOP: `{heartbeat_status}`",
        "",
        "## Harness Roster",
        "",
        f"- Providers: `{provider_count}`",
        f"- Unique models: `{model_count}`",
        f"- MCP servers: `{mcp_count}`",
        "",
        "## Provenance",
        "",
        (
            f"- Provenance: `{valid_count} valid`, "
            f"`{superseded_count} superseded`, `{invalid_count} invalid`"
        ),
    ]
    return "\n".join(lines) + "\n"


def run_doctor(workspace_root: Path, manifest_path: Path) -> tuple[str, int]:
    surface_results, surface_drift = materialize(
        workspace_root,
        manifest_path,
        check=True,
        dry_run=False,
    )
    from audit_provenance_packets import audit_packets

    _invalid_count, audit_records, _audit_lines = audit_packets(
        workspace_root / ".agent-surface" / "provenance",
        workspace_root=workspace_root,
    )
    audit_counts = count_audit_statuses(audit_records)
    report = build_doctor_report(
        workspace_root=workspace_root,
        surface_drift=surface_drift,
        roster_summary=read_roster_summary(workspace_root),
        agentmemory_status=fetch_agentmemory_status(),
        heartbeat_stop_present=(
            workspace_root / ".agent-surface" / "heartbeat" / "STOP"
        ).exists(),
        audit_counts=audit_counts,
    )
    report += "\n## Shared Surface Check\n\n"
    report += "\n".join(f"- {line}" for line in surface_results) + "\n"

    exit_code = 1 if surface_drift or audit_counts.get("invalid", 0) else 0
    if not report:
        exit_code = 1
    return report, exit_code


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


def target_in_scope(target_cfg: dict[str, Any], include_user_scope: bool) -> bool:
    """Repo-scope targets always run; user-scope needs an explicit opt-in.

    User-scope targets write outside the repo (e.g. `~/.codex/config.toml`,
    `%LOCALAPPDATA%/hermes/config.yaml`), which affects every project on the
    machine, not just this workspace -- so they only run when the caller
    explicitly opts in via `--include-user-scope`.
    """
    scope = str(target_cfg.get("scope", "repo")).strip().lower()
    if scope not in {"repo", "user"}:
        raise SharedSurfaceError(
            f"Target `scope` must be 'repo' or 'user', got {scope!r}"
        )
    return scope == "repo" or include_user_scope


def materialize(
    workspace_root: Path,
    manifest_path: Path,
    *,
    check: bool,
    dry_run: bool,
    include_user_scope: bool = False,
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

        agent_instruction_raw = opencode_cfg.get("agent_instruction_path")
        if agent_instruction_raw is not None:
            if (
                not isinstance(agent_instruction_raw, str)
                or not agent_instruction_raw.strip()
            ):
                raise SharedSurfaceError(
                    "OpenCode target field `agent_instruction_path` must be a non-empty string"
                )
            agent_instruction_path = workspace_root / agent_instruction_raw
            message, changed = check_or_write_text(
                agent_instruction_path,
                build_opencode_agent_instruction(opencode_cfg),
                check=check,
                dry_run=dry_run,
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

        startup_prompt_raw = vibe_cfg.get("startup_prompt_path")
        if startup_prompt_raw is not None:
            if (
                not isinstance(startup_prompt_raw, str)
                or not startup_prompt_raw.strip()
            ):
                raise SharedSurfaceError(
                    "Vibe target field `startup_prompt_path` must be a non-empty string"
                )
            startup_prompt_path = workspace_root / startup_prompt_raw
            startup_prompt = build_vibe_startup_prompt(vibe_cfg)
            message, changed = check_or_write_text(
                startup_prompt_path, startup_prompt, check=check, dry_run=dry_run
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
            launcher_content = build_vibe_launcher(vibe_cfg)
            message, changed = check_or_write_text(
                launcher_path, launcher_content, check=check, dry_run=dry_run
            )
            results.append(message)
            drift_found = drift_found or changed

    for codex_key in ("codex", "codex_user"):
        codex_cfg = targets.get(codex_key)
        if not (isinstance(codex_cfg, dict) and codex_cfg.get("config_path")):
            continue
        if not target_in_scope(codex_cfg, include_user_scope):
            results.append(f"SKIP  {codex_key} (user scope; pass --include-user-scope)")
            continue
        codex_path = resolve_manifest_path(
            workspace_root, str(codex_cfg["config_path"])
        )
        tomlkit = require_module("tomlkit", codex_key)
        existing_text = (
            codex_path.read_text(encoding="utf-8") if codex_path.exists() else ""
        )
        doc = tomlkit.parse(existing_text)
        apply_codex_mcp(
            doc,
            shared_mcp,
            codex_cfg.get("name_map") or {},
            codex_cfg.get("overrides") or {},
        )
        message, changed = check_or_write_text(
            codex_path, tomlkit.dumps(doc), check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    # Whether a REFUSED Hermes write should also fire under `--check`:
    # decided YES. `--check` never writes either way, so refusing isn't
    # strictly necessary to prevent data loss here -- but `--check` exists
    # so an operator can learn about drift/blockers *before* attempting a
    # real write, and "a live gateway will clobber this on shutdown" is
    # exactly that kind of actionable, pre-write-discoverable fact. Reporting
    # it only during a real write attempt would mean the first time an
    # operator learns the gateway is blocking is when their write already
    # failed, which defeats the point of having a dry, inspectable `--check`
    # pass. So the liveness guard runs unconditionally, before the
    # check/dry_run branch, same as every other check in this block.
    for hermes_key in ("hermes_workspace", "hermes_user"):
        hermes_cfg = targets.get(hermes_key)
        if not (isinstance(hermes_cfg, dict) and hermes_cfg.get("config_path")):
            continue
        if not target_in_scope(hermes_cfg, include_user_scope):
            results.append(
                f"SKIP  {hermes_key} (user scope; pass --include-user-scope)"
            )
            continue
        hermes_path = resolve_manifest_path(
            workspace_root, str(hermes_cfg["config_path"])
        )
        if not hermes_path.exists():
            results.append(f"SKIP  {hermes_key} (no config at {hermes_path})")
            continue
        live_pid = hermes_gateway_alive(hermes_path.parent)
        if live_pid is not None:
            results.append(
                f"REFUSED {hermes_key}: gateway PID {live_pid} is live; "
                "stop it and re-run, or the config is clobbered on shutdown"
            )
            drift_found = True
            continue
        ruamel_yaml = require_module("ruamel.yaml", hermes_key)
        yaml_rt = ruamel_yaml.YAML()
        yaml_rt.preserve_quotes = True
        yaml_rt.indent(mapping=2, sequence=4, offset=2)
        yaml_rt.width = 4096
        with hermes_path.open("r", encoding="utf-8") as handle:
            data = yaml_rt.load(handle)
        apply_hermes_mcp(
            data,
            shared_mcp,
            hermes_cfg.get("name_map") or {},
            hermes_cfg.get("overrides") or {},
        )
        buffer = io.StringIO()
        yaml_rt.dump(data, buffer)
        message, changed = check_or_write_text(
            hermes_path, buffer.getvalue(), check=check, dry_run=dry_run
        )
        results.append(message)
        drift_found = drift_found or changed

    if DEFAULT_AI_ROSTER_MANIFEST_PATH.exists():
        roster_results, roster_drift = materialize_ai_roster_surface(
            workspace_root=workspace_root,
            manifest_path=DEFAULT_AI_ROSTER_MANIFEST_PATH,
            check=check,
            dry_run=dry_run,
        )
        results.extend(roster_results)
        drift_found = drift_found or roster_drift

    if DEFAULT_MEMORY_MANIFEST_PATH.exists():
        memory_results = materialize_memory_surface(
            workspace_root=workspace_root,
            manifest_path=DEFAULT_MEMORY_MANIFEST_PATH,
            output_dir=workspace_root / ".agent-surface" / "memory",
            check=check,
            dry_run=dry_run,
        )
        results.extend(memory_results)
        drift_found = drift_found or any(
            message.startswith(("WROTE", "PLAN  WRITE", "CHECK DRIFT"))
            for message in memory_results
        )

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
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Read-only status report for shared surfaces, harness roster, agentmemory, heartbeat, and provenance",
    )
    parser.add_argument(
        "--include-user-scope",
        action="store_true",
        help=(
            "Also materialize user-scope targets (e.g. ~/.codex/config.toml, "
            "%%LOCALAPPDATA%%/hermes/config.yaml) that affect this machine "
            "beyond this repo. Repo-scope targets always run."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    manifest_path = args.manifest.resolve()
    if args.doctor:
        report, exit_code = run_doctor(workspace_root, manifest_path)
        print(report, end="")
        return exit_code
    results, drift_found = materialize(
        workspace_root,
        manifest_path,
        check=args.check,
        dry_run=args.dry_run,
        include_user_scope=args.include_user_scope,
    )
    for line in results:
        print(line)
    if args.check and drift_found:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
