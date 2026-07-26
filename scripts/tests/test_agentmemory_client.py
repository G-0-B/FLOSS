"""Tests for scripts/agentmemory_client.py -- the minimal MCP-stdio client
used by the hook scripts.

Every test runs against a stubbed/fake stdio MCP server
(scripts/tests/fixtures/fake_mcp_server.py, spawned via `sys.executable`
instead of node) -- no test here ever talks to a live agentmemory instance.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SERVER = Path(__file__).resolve().parent / "fixtures" / "fake_mcp_server.py"


def load_client_module(tmp_path: Path, mode: str = "ok"):
    spec = importlib.util.spec_from_file_location(
        "agentmemory_client_under_test",
        FLOSS_ROOT / "scripts" / "agentmemory_client.py",
    )
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["agentmemory_client_under_test"] = module
    spec.loader.exec_module(module)

    # Point the client at the fake server via `python fake_mcp_server.py`
    # instead of `node bin.mjs` -- the client only cares that something
    # speaks MCP-over-stdio on the other end.
    module.NODE_PATH = Path(sys.executable)
    module.MCP_SERVER_PATH = FIXTURE_SERVER

    # Isolate hook.log under tmp_path so tests don't touch the real
    # FLOSS_AGENT_DIR / ~/.floss_agent.
    module.AGENT_DIR = tmp_path
    module.LOG_FILE = tmp_path / "hook.log"

    import os

    os.environ["AGENTMEMORY_FAKE_MODE"] = mode

    return module


def _spy_on_popen(monkeypatch, module):
    """Wrap module.subprocess.Popen to record every spawned child so tests
    can assert on it after the call returns (e.g. that it was killed).
    """
    spawned: list[subprocess.Popen] = []
    real_popen = subprocess.Popen

    def fake_popen(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        spawned.append(proc)
        return proc

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)
    return spawned


# ---------------------------------------------------------------------------
# Successful save + recall
# ---------------------------------------------------------------------------


def test_successful_save_returns_true(tmp_path):
    module = load_client_module(tmp_path, mode="ok")

    result = module.save("a durable observation", concepts=["consensus", "code-change"])

    assert result is True


def test_successful_recall_returns_list_of_strings(tmp_path):
    module = load_client_module(tmp_path, mode="ok")

    result = module.recall("some query", limit=3)

    assert isinstance(result, list)
    assert result  # fake server returns 2 fixture results
    assert all(isinstance(item, str) for item in result)
    assert "fake recalled memory one" in result[0]


def test_recall_respects_limit(tmp_path):
    module = load_client_module(tmp_path, mode="ok")

    result = module.recall("some query", limit=1)

    assert len(result) <= 1


def test_save_empty_text_returns_false_without_spawning(tmp_path, monkeypatch):
    module = load_client_module(tmp_path, mode="ok")
    spawned = _spy_on_popen(monkeypatch, module)

    assert module.save("") is False
    assert module.save("   ") is False
    assert spawned == []


# ---------------------------------------------------------------------------
# Timeout: must return cleanly and kill the child
# ---------------------------------------------------------------------------


def test_timeout_returns_cleanly_and_kills_child(tmp_path, monkeypatch):
    module = load_client_module(tmp_path, mode="hang")
    spawned = _spy_on_popen(monkeypatch, module)

    started = time.monotonic()
    result = module.recall("anything", timeout=0.5)
    elapsed = time.monotonic() - started

    assert result == []
    # Bounded by the timeout, not by the fake server's 120s sleep.
    assert elapsed < 5.0

    assert len(spawned) == 1
    proc = spawned[0]
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and proc.poll() is None:
        time.sleep(0.05)
    assert proc.poll() is not None, "child process was not killed after timeout"


def test_save_timeout_returns_false(tmp_path):
    module = load_client_module(tmp_path, mode="hang")

    started = time.monotonic()
    result = module.save("something", timeout=0.5)
    elapsed = time.monotonic() - started

    assert result is False
    assert elapsed < 5.0


# ---------------------------------------------------------------------------
# Unreachable / missing binary
# ---------------------------------------------------------------------------


def test_missing_node_binary_returns_cleanly(tmp_path):
    module = load_client_module(tmp_path, mode="ok")
    module.NODE_PATH = tmp_path / "definitely-does-not-exist-node.exe"

    assert module.save("hello") is False
    assert module.recall("hello") == []


def test_missing_server_bin_returns_cleanly(tmp_path):
    module = load_client_module(tmp_path, mode="ok")
    module.MCP_SERVER_PATH = tmp_path / "no-such-bin.mjs"

    # NODE_PATH is real; node will exit immediately with "file not found".
    module.NODE_PATH = Path(sys.executable)

    assert module.save("hello") is False
    assert module.recall("hello") == []


# ---------------------------------------------------------------------------
# Malformed JSON response
# ---------------------------------------------------------------------------


def test_malformed_response_returns_cleanly(tmp_path):
    module = load_client_module(tmp_path, mode="malformed")

    assert module.save("hello") is False
    assert module.recall("hello") == []


# ---------------------------------------------------------------------------
# stdout must never be touched
# ---------------------------------------------------------------------------


def test_save_and_recall_never_write_to_stdout(tmp_path, capsys):
    module = load_client_module(tmp_path, mode="ok")

    module.save("hello", concepts=["x"])
    module.recall("hello")

    captured = capsys.readouterr()
    assert captured.out == ""


def test_failure_paths_never_write_to_stdout(tmp_path, capsys):
    module = load_client_module(tmp_path, mode="malformed")

    module.save("hello")
    module.recall("hello")

    captured = capsys.readouterr()
    assert captured.out == ""


def test_timeout_path_never_writes_to_stdout(tmp_path, capsys):
    module = load_client_module(tmp_path, mode="hang")

    module.recall("hello", timeout=0.3)

    captured = capsys.readouterr()
    assert captured.out == ""
