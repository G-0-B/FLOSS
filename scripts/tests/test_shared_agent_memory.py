from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_memory_module():
    script_path = FLOSS_ROOT / "scripts" / "materialize_shared_agent_memory.py"
    spec = importlib.util.spec_from_file_location("shared_agent_memory", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["shared_agent_memory"] = module
    spec.loader.exec_module(module)
    return module


def test_imports_legacy_claude_memory_into_canonical_tree(tmp_path):
    memory = load_memory_module()
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    (legacy_dir / "MEMORY.md").write_text("# Memory Index\n", encoding="utf-8")
    (legacy_dir / "feedback_pressure_helps.md").write_text(
        "\n".join(
            [
                "---",
                "name: Pressure Helps",
                "description: Direct pressure: useful context.",
                "type: feedback",
                "originSessionId: test-session",
                "---",
                "# Pressure Helps",
                "",
                "The user benefits from direct pressure.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    imported = memory.import_legacy_claude_memory(
        legacy_dir=legacy_dir,
        canonical_root=tmp_path / "FLOSS" / "docs" / "agent-memory",
    )

    assert [entry.path.as_posix() for entry in imported] == [
        (tmp_path / "FLOSS" / "docs" / "agent-memory" / "feedback" / "pressure-helps.md").as_posix()
    ]
    text = imported[0].path.read_text(encoding="utf-8")
    assert "id: feedback-pressure-helps" in text
    assert "type: feedback" in text
    assert "title: Pressure Helps" in text
    assert "legacy_description: 'Direct pressure: useful context.'" in text
    assert "origin_session_id: test-session" in text
    assert text.splitlines().count("---") == 2
    assert "# Pressure Helps" in text


def test_materializes_registry_shared_index_and_claude_projection(tmp_path):
    memory = load_memory_module()
    workspace = tmp_path
    canonical_root = workspace / "FLOSS" / "docs" / "agent-memory"
    feedback_dir = canonical_root / "feedback"
    feedback_dir.mkdir(parents=True)
    (feedback_dir / "pressure-helps.md").write_text(
        "\n".join(
            [
                "---",
                "id: feedback-pressure-helps",
                "type: feedback",
                "status: active",
                "applies_to:",
                "  - any-agent",
                "---",
                "",
                "# Pressure Helps",
                "",
                "Direct pressure helps avoid analysis paralysis.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = workspace / "FLOSS" / "shared-agent-memory-surface.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": "0.1.0",
                "workspace_id": "flossi0ullk",
                "workspace_name": "FLOSSI0ULLK",
                "canonical_root": "FLOSS/docs/agent-memory",
                "targets": {
                    "claude": {
                        "enabled": True,
                        "memory_dir": ".claude/projects/C---shit/memory",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    messages = memory.materialize(
        workspace_root=workspace,
        manifest_path=manifest,
        output_dir=workspace / ".agent-surface" / "memory",
        check=False,
        dry_run=False,
    )

    assert any(message.startswith("WROTE") for message in messages)
    registry = json.loads(
        (workspace / ".agent-surface" / "memory" / "memory-registry.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["entries"][0]["id"] == "feedback-pressure-helps"
    shared_index = (
        workspace / ".agent-surface" / "memory" / "AGENT_MEMORY.md"
    ).read_text(encoding="utf-8")
    assert "Pressure Helps" in shared_index
    claude_memory = (
        workspace
        / ".claude"
        / "projects"
        / "C---shit"
        / "memory"
        / "feedback_pressure_helps.md"
    ).read_text(encoding="utf-8")
    assert "Direct pressure helps" in claude_memory
    assert "feedback-pressure-helps" in (
        workspace / ".claude" / "projects" / "C---shit" / "memory" / "MEMORY.md"
    ).read_text(encoding="utf-8")
