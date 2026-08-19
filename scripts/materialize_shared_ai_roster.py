"""Materialize the shared FLOSSI0ULLK AI and harness roster.

Canonical source of truth:
  - `FLOSS/shared-ai-roster-surface.json`

Generated artifacts:
  - `.agent-surface/harness/ai-roster.json`
  - `.agent-surface/harness/AI_ROSTER.md`
  - `.agent-surface/harness/HARNESS_UPDATE_PACKET.md`

The JSON artifact is the comprehensive inventory. The markdown artifact is the
operator-facing summary and points back to the JSON when the model list is too
large to read in-line.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-ai-roster-surface.json"
DEFAULT_NAMED_MODEL_FAMILIES = [
    {
        "id": "openai",
        "label": "OpenAI / ChatGPT",
        "patterns": ["openai/", "gpt-", "/o1", "/o3", "/o4"],
    },
    {
        "id": "claude",
        "label": "Claude / Anthropic",
        "patterns": ["anthropic/", "claude"],
    },
    {
        "id": "gemini",
        "label": "Gemini / Google",
        "patterns": ["google/gemini", "gemini"],
    },
    {"id": "kimi", "label": "Kimi / Moonshot", "patterns": ["moonshotai/", "kimi"]},
    {"id": "grok", "label": "Grok / x.ai", "patterns": ["xai/", "grok"]},
    {
        "id": "mistral",
        "label": "Mistral",
        "patterns": ["mistral", "codestral", "devstral", "magistral"],
    },
    {"id": "groq", "label": "Groq-hosted", "patterns": ["groq/"]},
    {"id": "deepseek", "label": "DeepSeek", "patterns": ["deepseek"]},
    {"id": "qwen", "label": "Qwen / Alibaba", "patterns": ["qwen", "alibaba/"]},
]


class AIRosterError(Exception):
    """Raised for manifest, source, or projection errors."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_jsonc_comments(text: str) -> str:
    """Remove JSONC comments while preserving string literals."""
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


def load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AIRosterError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AIRosterError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AIRosterError(f"Expected JSON object in {path}")
    return payload


def load_jsonc(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AIRosterError(f"Missing file: {path}") from exc
    try:
        payload = json.loads(strip_jsonc_comments(text))
    except json.JSONDecodeError as exc:
        raise AIRosterError(f"Invalid JSONC in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise AIRosterError(f"Expected JSON object in {path}")
    return payload


def normalized_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def resolve_path(workspace_root: Path, raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (workspace_root / path).resolve()


def source_id(source: str | dict[str, Any], fallback: str) -> str:
    if isinstance(source, str):
        return fallback
    raw = source.get("id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return fallback


def source_kind(source: str | dict[str, Any], default: str) -> str:
    if isinstance(source, str):
        return default
    raw = source.get("kind")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return default


def source_path(workspace_root: Path, source: str | dict[str, Any]) -> Path:
    if isinstance(source, str):
        return resolve_path(workspace_root, source)
    raw = source.get("path")
    if not isinstance(raw, str) or not raw.strip():
        raise AIRosterError("Source entries must define `path`")
    return resolve_path(workspace_root, raw)


def compact_model(raw_id: str, raw_model: Any) -> dict[str, Any]:
    if isinstance(raw_model, dict):
        model_id = str(raw_model.get("id") or raw_id)
        record: dict[str, Any] = {
            "id": model_id,
            "name": str(raw_model.get("name") or model_id),
        }
        for field in (
            "family",
            "release_date",
            "reasoning",
            "tool_call",
            "attachment",
            "temperature",
            "limit",
            "modalities",
            "cost",
        ):
            if field in raw_model:
                record[field] = raw_model[field]
        return record
    return {"id": raw_id, "name": raw_id}


def collect_opencode_providers(
    source_name: str, path: Path, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    providers = payload.get("provider", {})
    if not isinstance(providers, dict):
        return []

    out: list[dict[str, Any]] = []
    for provider_key, provider in sorted(providers.items()):
        if not isinstance(provider, dict):
            continue
        models_raw = provider.get("models", {})
        if not isinstance(models_raw, dict):
            models_raw = {}
        models = [
            compact_model(str(model_key), raw_model)
            for model_key, raw_model in sorted(models_raw.items())
        ]
        out.append(
            {
                "source": source_name,
                "source_path": path.as_posix(),
                "provider_key": provider_key,
                "id": str(provider.get("id") or provider_key),
                "name": str(provider.get("name") or provider.get("id") or provider_key),
                "env": provider.get("env", []),
                "model_count": len(models),
                "models": models,
            }
        )
    return out


def collect_openwork_cloud_providers(
    source_name: str, path: Path, payload: dict[str, Any]
) -> list[dict[str, Any]]:
    cloud = payload.get("cloudImports", {})
    if not isinstance(cloud, dict):
        return []
    providers = cloud.get("providers", {})
    if not isinstance(providers, dict):
        return []

    out: list[dict[str, Any]] = []
    for provider_key, provider in sorted(providers.items()):
        if not isinstance(provider, dict):
            continue
        model_ids = provider.get("modelIds", [])
        if not isinstance(model_ids, list):
            model_ids = []
        models = [
            {"id": str(model_id), "name": str(model_id), "source": "cloud_model_id"}
            for model_id in model_ids
        ]
        provider_id = (
            provider.get("sourceProviderId")
            or provider.get("providerId")
            or provider.get("cloudProviderId")
            or provider_key
        )
        out.append(
            {
                "source": source_name,
                "source_path": path.as_posix(),
                "provider_key": provider_key,
                "id": str(provider_id),
                "name": str(provider.get("name") or provider_id),
                "updated_at": provider.get("updatedAt"),
                "model_count": len(models),
                "models": models,
            }
        )
    return out


def collect_provider_sources(
    workspace_root: Path, sources: list[Any]
) -> list[dict[str, Any]]:
    providers: list[dict[str, Any]] = []
    for index, source in enumerate(sources):
        if not isinstance(source, (str, dict)):
            raise AIRosterError("Provider source entries must be strings or objects")
        path = source_path(workspace_root, source)
        kind = source_kind(source, "opencode")
        name = source_id(source, f"provider-source-{index + 1}")
        payload = load_jsonc(path) if path.suffix == ".jsonc" else load_json(path)
        if kind == "opencode":
            providers.extend(collect_opencode_providers(name, path, payload))
        elif kind == "openwork_cloud":
            providers.extend(collect_openwork_cloud_providers(name, path, payload))
        else:
            raise AIRosterError(f"Unsupported provider source kind: {kind}")
    return providers


def collect_mcp_sources(
    workspace_root: Path, sources: list[Any]
) -> list[dict[str, Any]]:
    servers: list[dict[str, Any]] = []
    for index, source in enumerate(sources):
        if not isinstance(source, (str, dict)):
            raise AIRosterError("MCP source entries must be strings or objects")
        path = source_path(workspace_root, source)
        kind = source_kind(source, "mcp_json")
        name = source_id(source, f"mcp-source-{index + 1}")
        payload = load_jsonc(path) if path.suffix == ".jsonc" else load_json(path)
        server_map = payload.get("mcp" if kind == "opencode" else "mcpServers", {})
        if not isinstance(server_map, dict):
            continue
        for server_name, server in sorted(server_map.items()):
            if not isinstance(server, dict):
                continue
            record: dict[str, Any] = {
                "source": name,
                "source_path": path.as_posix(),
                "name": str(server_name),
                "type": str(server.get("type") or "stdio"),
            }
            if "command" in server:
                record["command"] = server["command"]
            if "args" in server:
                record["args"] = server["args"]
            if "url" in server:
                record["url"] = server["url"]
            servers.append(record)
    return servers


def first_heading(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return None


def collect_instruction_surfaces(
    workspace_root: Path, surfaces: list[Any]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, surface in enumerate(surfaces):
        if not isinstance(surface, dict):
            raise AIRosterError("Instruction surface entries must be objects")
        raw_path = surface.get("path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise AIRosterError("Instruction surface entries must define `path`")
        path = resolve_path(workspace_root, raw_path)
        exists = path.exists()
        text = path.read_text(encoding="utf-8") if exists else ""
        out.append(
            {
                "id": str(surface.get("id") or f"instruction-{index + 1}"),
                "path": raw_path,
                "exists": exists,
                "title": first_heading(text) or path.stem,
                "sha256": sha256_text(text) if exists else None,
            }
        )
    return out


def collect_agent_sources(
    workspace_root: Path, sources: list[Any]
) -> list[dict[str, Any]]:
    agents: list[dict[str, Any]] = []
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise AIRosterError("Agent source entries must be objects")
        base_id = str(source.get("id") or f"agent-source-{index + 1}")
        raw_path = source.get("path")
        raw_glob = source.get("glob")
        paths: list[Path]
        if isinstance(raw_path, str) and raw_path.strip():
            paths = [resolve_path(workspace_root, raw_path)]
        elif isinstance(raw_glob, str) and raw_glob.strip():
            paths = sorted(workspace_root.glob(raw_glob))
        else:
            raise AIRosterError("Agent sources must define `path` or `glob`")
        for path in paths:
            exists = path.exists()
            text = path.read_text(encoding="utf-8") if exists and path.is_file() else ""
            agents.append(
                {
                    "source": base_id,
                    "path": (
                        path.relative_to(workspace_root).as_posix()
                        if path.is_relative_to(workspace_root)
                        else path.as_posix()
                    ),
                    "exists": exists,
                    "title": first_heading(text) or path.stem,
                    "sha256": sha256_text(text) if exists and path.is_file() else None,
                }
            )
    return agents


def collect_memory_targets(
    workspace_root: Path, raw_path: str | None
) -> dict[str, Any]:
    if not raw_path:
        return {}
    path = resolve_path(workspace_root, raw_path)
    if not path.exists():
        return {"path": raw_path, "exists": False, "targets": {}}
    payload = load_json(path)
    targets = payload.get("targets", {})
    return {
        "path": raw_path,
        "exists": True,
        "canonical_root": payload.get("canonical_root"),
        "targets": targets if isinstance(targets, dict) else {},
    }


def unique_model_count(providers: list[dict[str, Any]]) -> int:
    return len(
        {
            str(model.get("id"))
            for provider in providers
            for model in provider.get("models", [])
            if isinstance(model, dict) and model.get("id")
        }
    )


def all_models(providers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for provider in providers:
        for model in provider.get("models", []):
            if not isinstance(model, dict):
                continue
            record = dict(model)
            record["provider_id"] = provider["id"]
            record["provider_name"] = provider["name"]
            record["provider_source"] = provider["source"]
            out.append(record)
    return out


def model_matches(model: dict[str, Any], patterns: list[str]) -> bool:
    haystack = " ".join(
        str(model.get(field, ""))
        for field in ("id", "name", "family", "provider_id", "provider_name")
    ).lower()
    return any(pattern.lower() in haystack for pattern in patterns)


def build_model_family_summary(
    manifest: dict[str, Any], providers: list[dict[str, Any]]
) -> dict[str, Any]:
    families = manifest.get("named_model_families", DEFAULT_NAMED_MODEL_FAMILIES)
    if not isinstance(families, list):
        raise AIRosterError("Manifest `named_model_families` must be a list")

    models = all_models(providers)
    summary: dict[str, Any] = {}
    for family in families:
        if not isinstance(family, dict):
            raise AIRosterError("Named model family entries must be objects")
        family_id = str(family.get("id") or "").strip()
        if not family_id:
            raise AIRosterError("Named model family entries require `id`")
        patterns = family.get("patterns", [])
        if not isinstance(patterns, list) or not all(
            isinstance(pattern, str) for pattern in patterns
        ):
            raise AIRosterError(
                f"Named model family {family_id!r} requires string `patterns`"
            )
        matched = [model for model in models if model_matches(model, patterns)]
        unique_ids = sorted({str(model.get("id")) for model in matched})
        providers_for_family = sorted(
            {
                str(model.get("provider_name") or model.get("provider_id"))
                for model in matched
            }
        )
        summary[family_id] = {
            "label": str(family.get("label") or family_id),
            "patterns": patterns,
            "model_count": len(unique_ids),
            "providers": providers_for_family,
            "models": unique_ids,
        }
    return summary


def build_registry(
    manifest: dict[str, Any],
    workspace_root: Path,
    *,
    generated_at: str,
) -> dict[str, Any]:
    provider_sources = manifest.get("provider_sources", [])
    if not isinstance(provider_sources, list):
        raise AIRosterError("Manifest `provider_sources` must be a list")
    mcp_sources = manifest.get("mcp_sources", [])
    if not isinstance(mcp_sources, list):
        raise AIRosterError("Manifest `mcp_sources` must be a list")
    instruction_surfaces = manifest.get("instruction_surfaces", [])
    if not isinstance(instruction_surfaces, list):
        raise AIRosterError("Manifest `instruction_surfaces` must be a list")
    agent_sources = manifest.get("agent_sources", [])
    if not isinstance(agent_sources, list):
        raise AIRosterError("Manifest `agent_sources` must be a list")

    providers = collect_provider_sources(workspace_root, provider_sources)
    mcp_servers = collect_mcp_sources(workspace_root, mcp_sources)
    instructions = collect_instruction_surfaces(workspace_root, instruction_surfaces)
    agents = collect_agent_sources(workspace_root, agent_sources)
    memory_manifest_raw = manifest.get("memory_manifest")
    memory_targets = collect_memory_targets(
        workspace_root,
        memory_manifest_raw if isinstance(memory_manifest_raw, str) else None,
    )

    return {
        "manifest_version": manifest.get("manifest_version", "?"),
        "workspace_id": manifest.get("workspace_id", "workspace"),
        "workspace_name": manifest.get("workspace_name", "workspace"),
        "generated_at": generated_at,
        "rules": manifest.get("rules", []),
        "invariants": manifest.get("invariants", []),
        "summary": {
            "provider_count": len(providers),
            "model_count": unique_model_count(providers),
            "mcp_server_count": len(mcp_servers),
            "instruction_surface_count": len(instructions),
            "agent_surface_count": len(agents),
        },
        "model_families": build_model_family_summary(manifest, providers),
        "providers": providers,
        "mcp_servers": mcp_servers,
        "instruction_surfaces": instructions,
        "agent_surfaces": agents,
        "memory_targets": memory_targets,
    }


def build_markdown(registry: dict[str, Any], markdown_model_limit: int) -> str:
    summary = registry["summary"]
    lines = [
        "# AI Harness Roster",
        "",
        "Generated from `FLOSS/shared-ai-roster-surface.json`.",
        "The JSON companion `.agent-surface/harness/ai-roster.json` is the full machine inventory.",
        "",
        "## Summary",
        "",
        f"- Providers: {summary['provider_count']}",
        f"- Unique models: {summary['model_count']}",
        f"- MCP servers: {summary['mcp_server_count']}",
        f"- Instruction surfaces: {summary['instruction_surface_count']}",
        f"- Agent surfaces: {summary['agent_surface_count']}",
        "",
    ]

    invariants = registry.get("invariants", [])
    if invariants:
        lines.extend(["## Shared Invariants", ""])
        for invariant in invariants:
            lines.append(f"- {invariant}")
        lines.append("")

    providers = registry.get("providers", [])
    if providers:
        lines.extend(["## Providers And Models", ""])
        for provider in providers:
            lines.append(
                f"### {provider['name']} (`{provider['id']}`) - {provider['model_count']} models"
            )
            lines.append(f"- Source: `{provider['source_path']}`")
            models = provider.get("models", [])
            visible = models[:markdown_model_limit]
            for model in visible:
                bits = [f"`{model['id']}`"]
                if model.get("family"):
                    bits.append(f"family `{model['family']}`")
                if model.get("reasoning") is True:
                    bits.append("reasoning")
                if model.get("tool_call") is True:
                    bits.append("tools")
                lines.append(f"- {', '.join(bits)}")
            if len(models) > len(visible):
                lines.append(
                    f"- ... {len(models) - len(visible)} more in `ai-roster.json`"
                )
            lines.append("")

    if registry.get("model_families"):
        lines.extend(["## Named AI Family Coverage", ""])
        for family in registry["model_families"].values():
            providers_text = ", ".join(family.get("providers", [])) or "none"
            lines.append(
                f"- {family['label']}: {family['model_count']} models via {providers_text}"
            )
        lines.append("")

    if registry.get("mcp_servers"):
        lines.extend(["## MCP Servers", ""])
        for server in registry["mcp_servers"]:
            location = server.get("url") or server.get("command") or "configured"
            lines.append(
                f"- `{server['name']}` from `{server['source']}`: `{location}`"
            )
        lines.append("")

    if registry.get("instruction_surfaces"):
        lines.extend(["## Instruction Surfaces", ""])
        for surface in registry["instruction_surfaces"]:
            status = "present" if surface["exists"] else "missing"
            lines.append(f"- `{surface['path']}` ({status})")
        lines.append("")

    if registry.get("agent_surfaces"):
        lines.extend(["## Agent Surfaces", ""])
        for agent in registry["agent_surfaces"]:
            status = "present" if agent["exists"] else "missing"
            lines.append(f"- `{agent['path']}` ({status})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_update_packet(registry: dict[str, Any]) -> str:
    lines = [
        "# Cross-Harness Update Packet",
        "",
        "Generated from `FLOSS/shared-ai-roster-surface.json`.",
        "",
        "## Startup Contract",
        "",
        "- Load `.agent-surface/context/CONTEXT_L0.md` before expanding context.",
        "- Load `.agent-surface/memory/AGENT_MEMORY.md` for repo-owned shared memory.",
        "- Treat `AGENTMEMORY.md` and `agentmemory` as recall/federation surfaces, not canon.",
        "- Repository canon wins over source-chain evidence, verified provenance packets, and agentmemory recall.",
        "- Every load-bearing cross-agent handoff should cite or generate provenance packet evidence.",
        "- Ordinary work should append a unified Action row to `.agent-surface/activity.jsonl` when practical.",
        "",
        "## Current Roster",
        "",
        f"- Providers: {registry['summary']['provider_count']}",
        f"- Unique models: {registry['summary']['model_count']}",
        f"- MCP servers: {registry['summary']['mcp_server_count']}",
        "",
        "## Required Shared Tools",
        "",
    ]
    for server_name in sorted(
        {str(server["name"]) for server in registry.get("mcp_servers", [])}
    ):
        lines.append(f"- `{server_name}`")
    lines.extend(
        [
            "",
            "## Durable Promotion Rule",
            "",
            "Recalled or pasted cross-agent claims are evidence candidates. Promote load-bearing conclusions through `FLOSS/docs/agent-memory/`, working todo, specs, ADRs, or source-chain claims before treating them as current truth.",
            "",
        ]
    )
    return "\n".join(lines)


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
        except AIRosterError:
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


def output_path(
    workspace_root: Path, outputs: dict[str, Any], key: str, default: str
) -> Path:
    raw_path = outputs.get(key, default)
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise AIRosterError(f"Output path `{key}` must be a non-empty string")
    return resolve_path(workspace_root, raw_path)


def materialize(
    *,
    workspace_root: Path,
    manifest_path: Path,
    check: bool,
    dry_run: bool,
) -> tuple[list[str], bool]:
    manifest = load_json(manifest_path)
    generated_at = str(manifest.get("updated") or "manifest-controlled")
    registry = build_registry(manifest, workspace_root, generated_at=generated_at)
    outputs = manifest.get("outputs", {})
    if not isinstance(outputs, dict):
        raise AIRosterError("Manifest `outputs` must be an object")
    markdown_model_limit = int(manifest.get("markdown_model_limit_per_provider", 50))

    writers = [
        check_or_write_json(
            output_path(
                workspace_root,
                outputs,
                "registry",
                ".agent-surface/harness/ai-roster.json",
            ),
            registry,
            check=check,
            dry_run=dry_run,
        ),
        check_or_write_text(
            output_path(
                workspace_root,
                outputs,
                "markdown",
                ".agent-surface/harness/AI_ROSTER.md",
            ),
            build_markdown(registry, markdown_model_limit),
            check=check,
            dry_run=dry_run,
        ),
        check_or_write_text(
            output_path(
                workspace_root,
                outputs,
                "update_packet",
                ".agent-surface/harness/HARNESS_UPDATE_PACKET.md",
            ),
            build_update_packet(registry),
            check=check,
            dry_run=dry_run,
        ),
    ]
    return [message for message, _changed in writers], any(
        changed for _message, changed in writers
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize shared AI roster")
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    manifest_path = args.manifest
    if not manifest_path.is_absolute():
        manifest_path = (workspace_root / manifest_path).resolve()
    messages, drift = materialize(
        workspace_root=workspace_root,
        manifest_path=manifest_path,
        check=args.check,
        dry_run=args.dry_run,
    )
    for message in messages:
        print(message)
    if args.check and drift:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
