from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_surface_module():
    if str(FLOSS_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "shared_agent_surface_under_test",
        FLOSS_ROOT / "scripts" / "materialize_shared_agent_surface.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["shared_agent_surface_under_test"] = module
    spec.loader.exec_module(module)
    return module


def test_vibe_config_exposes_workspace_agent_path_and_default_agent(tmp_path):
    surface = load_surface_module()
    config = surface.build_vibe_config(
        tmp_path,
        {},
        {
            "active_model": "devstral-small",
            "default_agent": "flossi0ullk-align",
            "include_project_context": True,
            "agent_paths": [".vibe/agents"],
        },
    )

    assert 'default_agent = "flossi0ullk-align"' in config
    assert "include_project_context = true" in config
    assert f'agent_paths = ["{(tmp_path / ".vibe/agents").as_posix()}"]' in config


def test_vibe_launcher_seeds_startup_prompt_when_no_prompt_args():
    surface = load_surface_module()
    launcher = surface.build_vibe_launcher(
        {
            "env_path": "FLOSS/.env",
            "startup_prompt_path": ".agent-surface/VIBE_STARTUP.md",
        }
    )

    assert ".agent-surface\\VIBE_STARTUP.md" in launcher
    assert "$hasPromptArg = $false" in launcher
    assert "$argList.Add((Get-Content $startupPromptPath -Raw))" in launcher


def test_vibe_launcher_distinguishes_agent_values_from_prompt_values():
    surface = load_surface_module()
    launcher = surface.build_vibe_launcher({})

    assert '$promptValueOptions = @("-p", "--prompt")' in launcher
    assert (
        '$valueOnlyOptions = @("--agent", "--workdir", "--add-dir", "--max-turns", "--max-price", "--enabled-tools", "--output")'
        in launcher
    )
    assert (
        '$utilityOptions = @("-h", "--help", "-v", "--version", "--setup", "--resume", "-c")'
        in launcher
    )


def test_vibe_startup_prompt_names_current_phase_and_budget_state():
    surface = load_surface_module()
    prompt = surface.build_vibe_startup_prompt(
        {
            "startup_context_pointers": [
                ".agent-surface/context/CONTEXT_L0.md",
                "FLOSS/docs/architecture/OPERATOR_PRIMER.md",
                ".agent-surface/context/RESUMPTION.md",
            ]
        }
    )

    assert "MVP Phase 0 substrate viability is complete" in prompt
    assert "Do not restart old Tryorama/Phase 0 work" in prompt
    assert "heartbeat STOP file is intentionally present" in prompt
    assert "FLOSS/docs/architecture/OPERATOR_PRIMER.md" in prompt


def test_vibe_config_projects_reasoning_ensemble_mcp_with_cold_start_budget(tmp_path):
    surface = load_surface_module()
    config = surface.build_vibe_config(
        tmp_path,
        {
            "flossiullk-reasoning-ensemble": {
                "command": "npx",
                "args": [
                    "-y",
                    "januscope@latest",
                    "--config",
                    "C:/~shit/.mcp/lenses/flossiullk-reasoning-ensemble.yaml",
                ],
            }
        },
        {
            "mcp_servers": ["flossiullk-reasoning-ensemble"],
            "server_overrides": {
                "flossiullk-reasoning-ensemble": {
                    "startup_timeout_sec": 120,
                    "tool_timeout_sec": 240,
                    "sampling_enabled": False,
                }
            },
        },
    )

    assert 'name = "flossiullk-reasoning-ensemble"' in config
    assert "C:/~shit/.mcp/lenses/flossiullk-reasoning-ensemble.yaml" in config
    assert "startup_timeout_sec = 120.0" in config
    assert "tool_timeout_sec = 240.0" in config
    assert "sampling_enabled = false" in config


def test_openwork_instruction_projection_names_shared_packet_and_provenance():
    surface = load_surface_module()
    content = surface.build_opencode_agent_instruction(
        {
            "default_agent": "openwork",
            "agent_description": "OpenWork default FLOSSI0ULLK worker.",
            "startup_context_pointers": [
                ".agent-surface/context/CONTEXT_L0.md",
                ".agent-surface/harness/HARNESS_UPDATE_PACKET.md",
                ".agent-surface/harness/AI_ROSTER.md",
                ".agent-surface/memory/AGENT_MEMORY.md",
                "AGENTMEMORY.md",
            ],
        }
    )

    assert "You are OpenWork" in content
    assert ".agent-surface/harness/HARNESS_UPDATE_PACKET.md" in content
    assert "agentmemory" in content
    assert "provenance packet" in content
    assert "Repository canon wins" in content


def test_umbrella_materializer_refreshes_memory_before_context(tmp_path, monkeypatch):
    surface = load_surface_module()
    workspace = tmp_path
    floss = workspace / "FLOSS"
    floss.mkdir()
    manifest = floss / "shared-agent-surface.json"
    manifest.write_text(
        """
        {
          "manifest_version": "0.1.0",
          "workspace_id": "flossi0ullk",
          "workspace_name": "FLOSSI0ULLK",
          "mcp_source": ".mcp.json",
          "targets": {}
        }
        """,
        encoding="utf-8",
    )
    (workspace / ".mcp.json").write_text('{"mcpServers": {}}\n', encoding="utf-8")

    roster_manifest = floss / "shared-ai-roster-surface.json"
    memory_manifest = floss / "shared-agent-memory-surface.json"
    context_manifest = floss / "shared-context-surface.json"
    for path in (roster_manifest, memory_manifest, context_manifest):
        path.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(surface, "DEFAULT_AI_ROSTER_MANIFEST_PATH", roster_manifest)
    monkeypatch.setattr(surface, "DEFAULT_MEMORY_MANIFEST_PATH", memory_manifest)
    monkeypatch.setattr(surface, "DEFAULT_CONTEXT_MANIFEST_PATH", context_manifest)
    monkeypatch.setattr(surface, "DEFAULT_HOOK_MANIFEST_PATH", floss / "missing-hooks.json")
    monkeypatch.setattr(surface, "DEFAULT_SKILL_MANIFEST_PATH", floss / "missing-skills.json")

    calls: list[str] = []

    def fake_roster(**_kwargs):
        calls.append("roster")
        return ["OK roster"], False

    def fake_memory(**_kwargs):
        calls.append("memory")
        return ["OK memory"]

    def fake_context(**_kwargs):
        calls.append("context")
        return ["OK context"], False

    monkeypatch.setattr(surface, "materialize_ai_roster_surface", fake_roster)
    monkeypatch.setattr(surface, "materialize_memory_surface", fake_memory)
    monkeypatch.setattr(surface, "materialize_context_surface", fake_context)

    surface.materialize(workspace, manifest, check=False, dry_run=False)

    assert calls == ["roster", "memory", "context"]


def test_doctor_report_summarizes_surface_memory_provenance_and_heartbeat():
    surface = load_surface_module()

    report = surface.build_doctor_report(
        workspace_root=Path("C:/~shit"),
        surface_drift=False,
        roster_summary={
            "provider_count": 12,
            "model_count": 382,
            "mcp_server_count": 11,
        },
        agentmemory_status="healthy",
        heartbeat_stop_present=True,
        audit_counts={"valid": 8, "superseded": 2, "invalid": 1},
    )

    assert "Workspace: `C:/~shit`" in report
    assert "- Shared surface: `clean`" in report
    assert "- agentmemory: `healthy`" in report
    assert "- Heartbeat STOP: `present`" in report
    assert "- Providers: `12`" in report
    assert "- Provenance: `8 valid`, `2 superseded`, `1 invalid`" in report
