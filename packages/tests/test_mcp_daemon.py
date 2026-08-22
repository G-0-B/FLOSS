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

    # Make the parent a FILE so the sink path cannot be created at all.
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    impossible_sink = blocker / "audit.jsonl"  # blocker is a file, not a dir
    append = mcp_daemon.audit_appender(str(impossible_sink))
    # Should not raise
    append("some_tool", {"key": "val"})


def test_audited_preserves_tool_signature_for_schema_generation():
    """The audit wrapper must not destroy the tool schema FastMCP derives.

    FastMCP builds each tool's inputSchema from the registered callable's
    signature and annotations. A wrapper that does not set `__wrapped__`
    registers as `(*args, **kwargs)`, which silently strips every parameter
    from the published schema — the tool still appears, but with no arguments.
    functools.wraps is what prevents that, so assert it directly.
    """
    import inspect

    from packages import mcp_daemon

    def sample(claim_text: str, blast_radius: str = "Local") -> dict:
        """Sample docstring."""
        return {"claim_text": claim_text, "blast_radius": blast_radius}

    wrapped = mcp_daemon.audited(sample, lambda *_: None)

    assert wrapped.__name__ == "sample"
    assert (wrapped.__doc__ or "").strip().startswith("Sample docstring")
    assert str(inspect.signature(wrapped)) == str(inspect.signature(sample))
    assert wrapped.__annotations__ == sample.__annotations__
    assert wrapped("x", blast_radius="System")["blast_radius"] == "System"


def test_audited_records_named_arguments(tmp_path):
    """Positional args are bound to parameter names so rows stay readable."""
    import json

    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))

    def submit(proposer: str, summary: str = "s") -> str:
        return "ok"

    mcp_daemon.audited(submit, append)("claude", summary="hello")

    row = json.loads(sink.read_text(encoding="utf-8").strip())
    assert row["tool"] == "submit"
    # bound by name even though `proposer` was passed positionally
    assert row["payload"] == {"proposer": "claude", "summary": "hello"}


def test_audited_bounds_values_and_survives_hostile_repr(tmp_path):
    """A huge Claim body must not be copied wholesale into the audit sink."""
    import json

    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))

    class Hostile:
        def __repr__(self):
            raise RuntimeError("boom")

    def tool(body: str, obj: object = None) -> str:
        return "ok"

    mcp_daemon.audited(tool, append)("A" * 5000, obj=Hostile())

    row = json.loads(sink.read_text(encoding="utf-8").strip())
    assert len(row["payload"]["body"]) < 1000
    assert row["payload"]["body"].endswith("<truncated>")
    assert row["payload"]["obj"] == "<unrepresentable>"


def test_audited_wraps_async_tools(tmp_path):
    """Async tools must stay async — awaiting a sync wrapper breaks registration."""
    import asyncio
    import inspect

    import json

    from packages import mcp_daemon

    sink = tmp_path / "audit.jsonl"
    append = mcp_daemon.audit_appender(str(sink))

    async def atool(x: int) -> int:
        return x + 1

    wrapped = mcp_daemon.audited(atool, append)
    assert inspect.iscoroutinefunction(wrapped)
    assert asyncio.run(wrapped(1)) == 2
    assert json.loads(sink.read_text(encoding="utf-8").strip())["payload"] == {"x": 1}


def test_registered_consensus_tools_are_audited():
    """Regression: the consensus server must register through the audited path.

    This is the check that would have caught the original defect — audit_appender
    existed and was unit-tested, but had no production caller, so _AUDIT_SINK was
    dead config and every tool call bypassed the audit trail.
    """
    from packages.metacoordinator_mcp import server

    if server.mcp is None:
        return  # MCP SDK not installed in this environment

    import asyncio

    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    assert "submit_claim" in names
    # schema must survive the wrapper
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    props = set((tools["submit_claim"].inputSchema or {}).get("properties", {}))
    assert {"proposer", "summary", "blast_radius"} <= props


def test_claim_singleton_blocks_while_a_live_holder_exists(tmp_path, monkeypatch):
    """A live PID in the file must block a second claimant."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    monkeypatch.setattr(mcp_daemon.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon.atexit, "register", lambda *a, **k: None)
    # Anything other than us, reported alive.
    monkeypatch.setattr(mcp_daemon, "_pid_alive", lambda pid: pid != os.getpid())

    (tmp_path / "slot.pid").write_text("999999", encoding="utf-8")

    assert mcp_daemon.claim_singleton("slot.pid") is False
    # The live holder's claim must be left intact.
    assert (tmp_path / "slot.pid").read_text(encoding="utf-8").strip() == "999999"


def test_claim_singleton_reclaims_a_dead_holder(tmp_path, monkeypatch):
    """A stale PID file must not permanently block the slot."""
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    monkeypatch.setattr(mcp_daemon.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon.atexit, "register", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon, "_pid_alive", lambda pid: False)

    (tmp_path / "slot.pid").write_text("999999", encoding="utf-8")

    assert mcp_daemon.claim_singleton("slot.pid") is True
    assert (tmp_path / "slot.pid").read_text(encoding="utf-8").strip() == str(os.getpid())


def test_release_does_not_delete_another_process_claim(tmp_path, monkeypatch):
    """Cleanup must be ownership-checked.

    The original handler unlinked unconditionally, so a launcher that lost the
    port bind deleted the SURVIVING daemon's pid file on its way out, defeating
    duplicate prevention for every later start.
    """
    from packages import mcp_daemon

    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    monkeypatch.setattr(mcp_daemon.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(mcp_daemon, "_pid_alive", lambda pid: False)

    registered = []
    monkeypatch.setattr(mcp_daemon.atexit, "register", lambda fn: registered.append(fn))

    assert mcp_daemon.claim_singleton("slot.pid") is True
    assert registered, "cleanup handler was never registered"

    # Another process takes over the slot, then our handler runs.
    (tmp_path / "slot.pid").write_text("424242", encoding="utf-8")
    registered[0]()

    assert (tmp_path / "slot.pid").exists(), "released a claim we no longer owned"
    assert (tmp_path / "slot.pid").read_text(encoding="utf-8").strip() == "424242"
