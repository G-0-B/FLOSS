"""RED tests for the FastMCP surface of the coordination room.

Production change that would make these fail: a new parameter dropped from the
registered tool schema (the audit wrapper hiding it), `room_topics` not
registered, importing the server reading or writing the log, a duplicate start
rewriting the board before it loses the PID guard, a new owner acting on room
state cached before the previous owner stopped, one slow lookup stalling every
other caller, a default read limit, or a fixture leaving an operator's
`COORDINATION_ROOM_BOARD` in force.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import runpy
import sys
import time
import warnings
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytest.importorskip("mcp")

from packages.coordination_room.tests.room_server import pin_room_env, reload_server  # noqa: E402


@pytest.fixture
def server(tmp_path: Path, monkeypatch):
    # The module reads its paths at import time, so they are pinned first.
    pin_room_env(monkeypatch, tmp_path)
    return reload_server()


def _call(coroutine) -> dict:
    return json.loads(asyncio.run(coroutine))


def test_board_tools_are_registered_with_their_parameters(server):
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    assert {"room_topics", "room_broadcast", "room_read", "room_claim"} <= set(tools)
    assert {"topic", "evidence_refs", "reply_to"} <= set(
        tools["room_broadcast"].inputSchema["properties"]
    )
    assert {"topic", "thread_id", "limit"} <= set(
        tools["room_read"].inputSchema["properties"]
    )
    assert "intent" in tools["room_claim"].inputSchema["properties"]


def test_import_touches_nothing_and_builds_no_room(server, tmp_path: Path):
    assert server._board_path() == tmp_path / "rooms" / "BOARD.md"
    assert server._tools_instance is None
    assert not (tmp_path / "rooms").exists()


def test_room_state_is_loaded_by_the_owner_not_at_import(server, tmp_path: Path):
    """Review round 2, I1: the previous owner appends and claims after the new
    daemon was imported but before it serves. The new daemon must see both:
    no reused seq, no second holder."""
    from packages.coordination_room.room import CoordinationRoom

    previous = CoordinationRoom(root=tmp_path, log_path=tmp_path / "rooms" / "events.jsonl")
    previous.broadcast("previous", "one")
    previous.claim("previous", "x.py")

    conflict = _call(server.room_claim(agent_id="new", path="x.py"))
    assert conflict["error"] == "conflict"
    assert conflict["holder"] == "previous"
    assert _call(server.room_broadcast(agent_id="new", text="three"))["seq"] == 3


def test_a_slow_lookup_does_not_stall_other_callers(server, monkeypatch):
    """Review round 6 (Grok), M1: FastMCP runs a synchronous tool on its event
    loop, so one post waiting on `git` froze the room for everyone. The tools
    are coroutines that do their work on a worker thread."""
    import packages.coordination_room.room as room_module

    def slow_lookup(root, refs):
        time.sleep(1.5)
        return "unresolved", [{"ref": refs[0], "kind": "commit", "ok": False}]

    monkeypatch.setattr(room_module, "resolve_all", slow_lookup)

    async def scenario() -> tuple[float, dict]:
        post = asyncio.create_task(
            server.room_broadcast(agent_id="a", text="slow", evidence_refs=["commit:" + "a" * 40])
        )
        await asyncio.sleep(0.2)  # the post is now inside its lookup
        started = time.monotonic()
        state = json.loads(await server.room_state())
        waited = time.monotonic() - started
        await post
        return waited, state

    waited, state = asyncio.run(scenario())
    assert state["ok"] is True
    assert waited < 0.8, f"room_state waited {waited:.2f}s behind another caller's lookup"


def test_read_has_no_default_limit(server):
    """Review round 6 (Grok), M7: a default of 50 survived every earlier test."""
    for n in range(60):
        _call(server.room_broadcast(agent_id="a", text=f"row {n}"))
    assert len(_call(server.room_read())["events"]) == 60
    assert len(_call(server.room_read(limit=7))["events"]) == 7


def test_board_defaults_beside_the_log_and_honours_the_override(server, tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_ROOM_BOARD", str(tmp_path / "elsewhere" / "B.md"))
    assert server._board_path() == tmp_path / "elsewhere" / "B.md"


def test_board_override_that_is_the_log_stops_the_import(server, tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_ROOM_BOARD", str(tmp_path / "rooms" / "events.jsonl"))
    with pytest.raises(ValueError, match="event log"):
        importlib.reload(server)


def test_rejected_duplicate_start_leaves_board_and_log_untouched(server, tmp_path, monkeypatch):
    """A second `python -m packages.coordination_room.server` loses the PID
    guard. Nothing durable may change on its way there."""
    _call(server.room_broadcast(agent_id="owner", text="seed"))
    log = tmp_path / "rooms" / "events.jsonl"
    board = tmp_path / "rooms" / "BOARD.md"
    before = (log.read_bytes(), board.read_bytes(), board.stat().st_mtime_ns)

    import packages.mcp_daemon as daemon

    monkeypatch.setattr(daemon, "claim_singleton", lambda pid_filename: False)
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings(), pytest.raises(SystemExit) as stopped:
        # runpy notes the module is already imported; that is the point here.
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("packages.coordination_room.server", run_name="__main__")

    assert stopped.value.code == 0
    assert (log.read_bytes(), board.read_bytes(), board.stat().st_mtime_ns) == before
    assert sorted(p.name for p in log.parent.iterdir()) == ["BOARD.md", "events.jsonl"]
