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
