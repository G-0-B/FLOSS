from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_roster_module():
    script_path = FLOSS_ROOT / "scripts" / "materialize_shared_ai_roster.py"
    spec = importlib.util.spec_from_file_location("shared_ai_roster", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["shared_ai_roster"] = module
    spec.loader.exec_module(module)
    return module


def test_materializes_comprehensive_roster_and_update_packet(tmp_path):
    roster = load_roster_module()
    workspace = tmp_path
    floss = workspace / "FLOSS"
    floss.mkdir()

    (workspace / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "agentmemory": {"command": "npx", "args": ["@agentmemory/mcp"]},
                    "flossiullk-consensus": {
                        "command": "python",
                        "args": ["gateway.py"],
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (workspace / "opencode.jsonc").write_text(
        """
        {
          // root OpenWork provider import
          "provider": {
            "openai": {
              "id": "openai",
              "name": "OpenAI",
              "models": {
                "openai/gpt-5.4": {"id": "openai/gpt-5.4", "name": "GPT 5.4"},
                "openai/gpt-5.4-mini": {"id": "openai/gpt-5.4-mini", "name": "GPT 5.4 Mini"}
              }
            },
            "xai": {
              "id": "xai",
              "name": "x.ai",
              "models": {
                "xai/grok-4": {"id": "xai/grok-4", "name": "Grok 4"}
              }
            }
          }
        }
        """,
        encoding="utf-8",
    )
    openwork_dir = workspace / "opworkers" / ".opencode"
    openwork_dir.mkdir(parents=True)
    (openwork_dir / "openwork.json").write_text(
        json.dumps(
            {
                "cloudImports": {
                    "providers": {
                        "moonshot": {
                            "name": "Moonshot",
                            "sourceProviderId": "moonshotai",
                            "modelIds": [
                                "moonshotai/kimi-k2.6",
                                "moonshotai/kimi-k2-thinking",
                            ],
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (workspace / "opworkers" / "opencode.jsonc").write_text(
        json.dumps({"mcp": {"agentmemory": {"type": "local"}}}),
        encoding="utf-8",
    )
    (workspace / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (workspace / "AGENTMEMORY.md").write_text("# agentmemory\n", encoding="utf-8")

    manifest = floss / "shared-ai-roster-surface.json"
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": "0.1.0",
                "workspace_id": "flossi0ullk",
                "workspace_name": "FLOSSI0ULLK",
                "outputs": {
                    "registry": ".agent-surface/harness/ai-roster.json",
                    "markdown": ".agent-surface/harness/AI_ROSTER.md",
                    "update_packet": ".agent-surface/harness/HARNESS_UPDATE_PACKET.md",
                },
                "mcp_sources": [".mcp.json"],
                "provider_sources": [
                    {
                        "id": "root-openwork",
                        "kind": "opencode",
                        "path": "opencode.jsonc",
                    },
                    {
                        "id": "openwork-cloud",
                        "kind": "openwork_cloud",
                        "path": "opworkers/.opencode/openwork.json",
                    },
                ],
                "instruction_surfaces": [
                    {"id": "agents", "path": "AGENTS.md"},
                    {"id": "agentmemory", "path": "AGENTMEMORY.md"},
                ],
                "invariants": [
                    "Repository canon wins over agentmemory recall.",
                    "Load-bearing cross-agent handoffs require provenance packet evidence.",
                ],
                "named_model_families": [
                    {
                        "id": "openai",
                        "label": "OpenAI / ChatGPT",
                        "patterns": ["openai/", "gpt-"],
                    },
                    {
                        "id": "grok",
                        "label": "Grok / x.ai",
                        "patterns": ["xai/", "grok"],
                    },
                    {
                        "id": "kimi",
                        "label": "Kimi / Moonshot",
                        "patterns": ["moonshotai/", "kimi"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    messages, drift = roster.materialize(
        workspace_root=workspace,
        manifest_path=manifest,
        check=False,
        dry_run=False,
    )

    assert drift is True
    assert any(message.startswith("WROTE") for message in messages)
    registry = json.loads(
        (workspace / ".agent-surface" / "harness" / "ai-roster.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["summary"]["provider_count"] == 3
    assert registry["summary"]["model_count"] == 5
    model_ids = {
        model["id"]
        for provider in registry["providers"]
        for model in provider["models"]
    }
    assert {
        "openai/gpt-5.4",
        "openai/gpt-5.4-mini",
        "xai/grok-4",
        "moonshotai/kimi-k2.6",
        "moonshotai/kimi-k2-thinking",
    } <= model_ids
    assert registry["model_families"]["openai"]["model_count"] == 2
    assert registry["model_families"]["grok"]["model_count"] == 1
    assert registry["model_families"]["kimi"]["model_count"] == 2
    packet = (
        workspace / ".agent-surface" / "harness" / "HARNESS_UPDATE_PACKET.md"
    ).read_text(encoding="utf-8")
    assert "agentmemory" in packet
    assert "provenance packet" in packet
