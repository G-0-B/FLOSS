"""TDD tests for the shared MCP daemon bootstrap module.

Tests PID-singleton enforcement and audit-append functionality.
Run: C:\\Python313\\python.exe -m pytest FLOSS/packages/tests/test_mcp_daemon.py -v
"""
import os
import sys
from pathlib import Path

# Ensure workspace root is on sys.path so `from packages import mcp_daemon` works
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def test_stale_pid_is_overwritten(tmp_path, monkeypatch):
    """A stale (dead) PID file should be overwritten and claim succeed."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "x.pid").write_text("999999999")  # almost-certainly-dead pid
    assert mcp_daemon.claim_singleton("x.pid") is True
    assert (tmp_path / "x.pid").read_text().strip() == str(os.getpid())


def test_live_pid_blocks_second_claim(tmp_path, monkeypatch):
    """Our own PID is alive — a second claim for the same slot must fail."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "y.pid").write_text(str(os.getpid()))  # our pid = alive
    assert mcp_daemon.claim_singleton("y.pid") is False


def test_audit_appender_writes_jsonl(tmp_path, monkeypatch):
    """audit_appender should write one JSONL line per call."""
    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))
    append("submit_claim", {"claim_id": "test-123"})
    append("cast_vote", {"weight": 0.5})

    lines = sink.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    import json
    row0 = json.loads(lines[0])
    assert row0["tool"] == "submit_claim"
    assert row0["payload"]["claim_id"] == "test-123"
    assert "ts" in row0
    row1 = json.loads(lines[1])
    assert row1["tool"] == "cast_vote"


def test_audit_appender_best_effort_no_crash(tmp_path):
    """audit_appender must never raise — audit is defense-in-depth, not fatal."""
    from packages import mcp_daemon

    # Point sink at a path that can't be created (under a file, not a dir)
    sink = tmp_path / "not_a_dir"  # missing_ok but parent exists — try impossible path
    # Make parent a file to trigger OSError
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    impossible_sink = blocker / "audit.jsonl"  # blocker is a file, not a dir
    append = mcp_daemon.audit_appender(str(impossible_sink))
    # Should not raise
    append("some_tool", {"key": "val"})
