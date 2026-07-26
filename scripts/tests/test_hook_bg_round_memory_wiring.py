"""Tests for the agentmemory wiring added to scripts/hook_bg_round.py.

hook_bg_round.py is the DETACHED consensus-round runner spawned by
hook_post_write.py -- it is already slow (~10s, network calls to Groq /
Cerebras), so a ~240ms agentmemory save is free here. These tests exercise
the two save helpers directly, with a fake `agentmemory_client` module
injected into sys.modules so nothing here ever touches a real MCP child
process or a live agentmemory instance.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_bg_round_module():
    spec = importlib.util.spec_from_file_location(
        "hook_bg_round_under_test", FLOSS_ROOT / "scripts" / "hook_bg_round.py"
    )
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["hook_bg_round_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def fake_agentmemory_client(monkeypatch):
    calls: list[dict] = []
    fake_module = types.ModuleType("agentmemory_client")

    def fake_save(text, concepts=None, timeout=5.0):
        calls.append({"text": text, "concepts": concepts, "timeout": timeout})
        return True

    fake_module.save = fake_save
    monkeypatch.setitem(sys.modules, "agentmemory_client", fake_module)
    return calls


def test_save_consensus_outcome_records_claim_outcome_mean_variance_and_roster(
    tmp_path, monkeypatch, fake_agentmemory_client
):
    module = load_bg_round_module()
    module.LOG_FILE = tmp_path / "hook.log"

    result = {
        "outcome": "APPROVED",
        "tally_mean": 0.612,
        "tally_variance": 0.043,
        "votes": [
            {"voter": "groq-a", "weight": 0.7},
            {"voter": "cerebras-b", "weight": 0.5},
        ],
    }
    roster = [
        {"name": "groq-a", "enabled": True},
        {"name": "cerebras-b", "enabled": True},
    ]

    module.save_consensus_outcome_to_memory("claim_abc123", result, roster)

    assert len(fake_agentmemory_client) == 1
    call = fake_agentmemory_client[0]
    assert "claim_abc123" in call["text"]
    assert "APPROVED" in call["text"]
    assert "0.612" in call["text"]
    assert "0.043" in call["text"]
    assert "groq-a" in call["text"]
    assert "cerebras-b" in call["text"]
    assert "groq-a" in call["concepts"]
    assert "cerebras-b" in call["concepts"]
    assert "consensus" in call["concepts"]


def test_save_consensus_outcome_never_raises_when_agentmemory_broken(
    tmp_path, monkeypatch
):
    module = load_bg_round_module()
    module.LOG_FILE = tmp_path / "hook.log"

    broken_module = types.ModuleType("agentmemory_client")

    def broken_save(*args, **kwargs):
        raise RuntimeError("agentmemory unreachable")

    broken_module.save = broken_save
    monkeypatch.setitem(sys.modules, "agentmemory_client", broken_module)

    # Must not raise.
    module.save_consensus_outcome_to_memory(
        "claim_x", {"outcome": "REJECTED", "votes": []}, []
    )


def test_save_edit_accepted_records_claim_id_and_note(
    tmp_path, fake_agentmemory_client
):
    module = load_bg_round_module()
    module.LOG_FILE = tmp_path / "hook.log"

    module.save_edit_accepted_to_memory(
        "claim_def456", "claude-code:edit:verified → foo.py"
    )

    assert len(fake_agentmemory_client) == 1
    call = fake_agentmemory_client[0]
    assert "claim_def456" in call["text"]
    assert "claude-code:edit:verified" in call["text"]
    assert "accepted" in call["concepts"]


def test_save_edit_accepted_is_noop_for_empty_note(tmp_path, fake_agentmemory_client):
    module = load_bg_round_module()
    module.LOG_FILE = tmp_path / "hook.log"

    module.save_edit_accepted_to_memory("claim_ghi789", "")

    assert fake_agentmemory_client == []


def test_save_edit_accepted_never_raises_when_agentmemory_broken(tmp_path, monkeypatch):
    module = load_bg_round_module()
    module.LOG_FILE = tmp_path / "hook.log"

    broken_module = types.ModuleType("agentmemory_client")

    def broken_save(*args, **kwargs):
        raise RuntimeError("agentmemory unreachable")

    broken_module.save = broken_save
    monkeypatch.setitem(sys.modules, "agentmemory_client", broken_module)

    # Must not raise.
    module.save_edit_accepted_to_memory("claim_y", "some note")


def test_main_parses_optional_edit_note_argv(
    tmp_path, monkeypatch, fake_agentmemory_client
):
    """argv[2], when present, must reach save_edit_accepted_to_memory via
    main()'s dispatch -- not just via the helper called directly.
    """
    module = load_bg_round_module()
    module.LOG_FILE = tmp_path / "hook.log"
    module.TRACE_DIR = tmp_path / "traces"

    # Short-circuit everything past the edit-note save so this stays a
    # narrow unit test of the argv wiring, not a full consensus-round test.
    def fake_gateway_tools_import_failure(*args, **kwargs):
        raise ImportError("stubbed: not exercising the consensus path here")

    monkeypatch.setattr(
        sys, "argv", ["hook_bg_round.py", "claim_argv_test", "note-from-argv"]
    )

    # Force the GatewayTools import to fail immediately after the edit-note
    # save runs, so main() exits early without needing the full gateway.
    import builtins

    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name == "packages.metacoordinator_mcp.tools":
            raise ImportError("stubbed for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module.main()

    assert len(fake_agentmemory_client) == 1
    assert "note-from-argv" in fake_agentmemory_client[0]["text"]
    assert "claim_argv_test" in fake_agentmemory_client[0]["text"]
