"""Tests for the agentmemory recall wired into scripts/session_start_inject.py.

This hook is on the critical path (session start), so the spec requires:
  - hard-capped added latency (<=1s total)
  - silent degrade to the pre-existing behavior on timeout/failure
  - a small injected addition (the file's own docstring: output is
    intentionally small)

All tests use a fake `agentmemory_client` module injected into
sys.modules -- no live agentmemory, no real MCP child process.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
import time
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_session_start_module(tmp_path: Path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "session_start_inject_under_test",
        FLOSS_ROOT / "scripts" / "session_start_inject.py",
    )
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["session_start_inject_under_test"] = module
    spec.loader.exec_module(module)

    contract_path = tmp_path / "STARTUP_CONTRACT.md"
    contract_path.write_text(
        "# Startup Contract\nSome orientation text.\n", encoding="utf-8"
    )
    module.CONTRACT = contract_path
    return module


@pytest.fixture()
def fake_agentmemory_client(monkeypatch):
    calls: list[dict] = []
    fake_module = types.ModuleType("agentmemory_client")

    def fake_recall(query, limit=3, timeout=5.0):
        calls.append({"query": query, "limit": limit, "timeout": timeout})
        return ["recent decision one", "recent decision two"]

    fake_module.recall = fake_recall
    monkeypatch.setitem(sys.modules, "agentmemory_client", fake_module)
    return calls


def test_recall_recent_memories_calls_client_with_bounded_timeout(
    tmp_path, monkeypatch, fake_agentmemory_client
):
    module = load_session_start_module(tmp_path, monkeypatch)

    items = module.recall_recent_memories()

    assert items == ["recent decision one", "recent decision two"]
    assert len(fake_agentmemory_client) == 1
    call = fake_agentmemory_client[0]
    assert call["timeout"] <= 1.0
    assert call["limit"] <= 5


def test_main_injects_memory_section_into_additional_context(
    tmp_path, monkeypatch, fake_agentmemory_client, capsys
):
    module = load_session_start_module(tmp_path, monkeypatch)

    module.main()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "# Startup Contract" in payload["additionalContext"]
    assert "recent decision one" in payload["additionalContext"]
    assert "recent decision two" in payload["additionalContext"]


def test_memory_outage_degrades_silently_to_original_contract_only(
    tmp_path, monkeypatch, capsys
):
    broken_module = types.ModuleType("agentmemory_client")

    def broken_recall(*args, **kwargs):
        raise RuntimeError("agentmemory down")

    broken_module.recall = broken_recall
    monkeypatch.setitem(sys.modules, "agentmemory_client", broken_module)

    module = load_session_start_module(tmp_path, monkeypatch)

    exit_code = module.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["continue"] is True
    assert "# Startup Contract" in payload["additionalContext"]
    # Nothing memory-shaped leaked into the context on failure.
    assert "recent decision" not in payload["additionalContext"]


def test_memory_timeout_degrades_silently_within_latency_budget(
    tmp_path, monkeypatch, capsys
):
    def slow_recall(query, limit=3, timeout=5.0):
        # Simulate the client's own internal timeout handling: it must
        # return promptly (never actually sleep past `timeout`), so a well
        # behaved client returns [] quickly. This test's job is to confirm
        # session_start_inject's *own* budget (module constant) stays small
        # and that main() still finishes fast and degrades cleanly.
        time.sleep(0.05)
        return []

    slow_module = types.ModuleType("agentmemory_client")
    slow_module.recall = slow_recall
    monkeypatch.setitem(sys.modules, "agentmemory_client", slow_module)

    module = load_session_start_module(tmp_path, monkeypatch)

    started = time.monotonic()
    exit_code = module.main()
    elapsed = time.monotonic() - started

    assert exit_code == 0
    assert elapsed < 1.0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "# Startup Contract" in payload["additionalContext"]


def test_recall_timeout_constant_is_within_one_second_budget(tmp_path, monkeypatch):
    module = load_session_start_module(tmp_path, monkeypatch)
    assert module.MEMORY_RECALL_TIMEOUT_SECONDS <= 1.0


def test_memory_section_is_small_and_bounded(tmp_path, monkeypatch):
    module = load_session_start_module(tmp_path, monkeypatch)

    huge_item = "x" * 10_000
    section = module.render_memory_section([huge_item, huge_item, huge_item])

    # The docstring's own promise -- output stays small even if recall
    # returns something unexpectedly large.
    assert len(section) < 1000


def test_no_memories_found_produces_empty_section(tmp_path, monkeypatch):
    module = load_session_start_module(tmp_path, monkeypatch)
    assert module.render_memory_section([]) == ""


def test_contract_missing_still_exits_cleanly_without_touching_memory(
    tmp_path, monkeypatch
):
    """When the contract file itself is missing, main() takes its pre-
    existing early-return path -- confirms the memory wiring didn't get
    inserted ahead of that guard in a way that would call agentmemory
    before we even know whether the contract loaded.
    """
    calls = []
    fake_module = types.ModuleType("agentmemory_client")

    def fake_recall(*args, **kwargs):
        calls.append(1)
        return []

    fake_module.recall = fake_recall
    monkeypatch.setitem(sys.modules, "agentmemory_client", fake_module)

    module = load_session_start_module(tmp_path, monkeypatch)
    module.CONTRACT = tmp_path / "does-not-exist.md"

    exit_code = module.main()

    assert exit_code == 0
    assert calls == []
