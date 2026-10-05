"""HTTP-level acceptance: a real MCP client against the real FastMCP room.

Runs on a free loopback port with every path under tmp_path, so it proves the
deployed surface without touching the live bus on :7334.

Production change that would make these fail: a board argument lost between
the MCP schema and the log, `room_state` not naming the bus it serves, the
board not following a post made over HTTP, the room answering a request whose
Host header is not loopback, or the command-line client mis-reporting a reply.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytest.importorskip("mcp")
httpx = pytest.importorskip("httpx")
pytest.importorskip("uvicorn")

from packages.coordination_room.client import call_tool  # noqa: E402
from packages.coordination_room.tests.room_server import (  # noqa: E402
    free_port,
    pin_room_env,
    reload_server,
    serving,
)


@pytest.fixture
def room(tmp_path: Path, monkeypatch):
    log = pin_room_env(monkeypatch, tmp_path)
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    port = free_port()
    with serving(reload_server().mcp.streamable_http_app(), port):
        yield f"http://127.0.0.1:{port}/mcp", log


def _call(url: str, tool: str, arguments: dict) -> dict:
    return asyncio.run(call_tool(url, tool, arguments))


def test_board_round_trip_over_http(room):
    url, log = room
    state = _call(url, "room_state", {})
    assert state["log"] == str(log)
    assert state["board"] == str(log.parent / "BOARD.md")
    assert state["board_as_of"] is None and state["log_skipped_lines"] == 0

    post = _call(
        url,
        "room_broadcast",
        {
            "agent_id": "claude",
            "text": "landed",
            "topic": "announcements",
            "evidence_refs": ["file:proof.md"],
        },
    )
    assert post == {
        "ok": True,
        "seq": 1,
        "topic": "announcements",
        "evidence_status": "resolved",
    }
    reply = _call(url, "room_broadcast", {"agent_id": "grok", "text": "seen", "reply_to": 1})
    assert reply["topic"] == "announcements"
    assert [e["seq"] for e in _call(url, "room_read", {"thread_id": 1})["events"]] == [1, 2]
    assert _call(url, "room_topics", {})["topics"] == [
        {"topic": "announcements", "count": 2, "last_seq": 2}
    ]
    after = _call(url, "room_state", {})
    assert after["board_as_of"] is not None and after["board_last_error"] is None

    board = (log.parent / "BOARD.md").read_text(encoding="utf-8")
    assert "**claude** [evidence resolved] (refs: file:proof.md): landed" in board
    assert "**grok** re #1: seen" in board
    assert len([line for line in log.read_text(encoding="utf-8").split("\n") if line.strip()]) == 2


def test_a_request_with_a_foreign_host_header_is_refused(room):
    """DNS rebinding: a web page can make a browser send requests here under
    its own host name. FastMCP refuses a non-loopback Host for a loopback
    server; this pins that the room is built in a way that keeps it on."""
    url, log = room
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    refused = httpx.post(url, json=body, headers={**headers, "Host": "evil.example:7334"}, timeout=5)
    assert refused.status_code in (403, 421)
    assert not log.exists()


def test_the_command_line_client_prints_the_reply_and_sets_the_exit_code(room):
    url, _ = room
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    client = [sys.executable, "-m", "packages.coordination_room.client", "--url", url]

    posted = subprocess.run(
        [*client, "room_broadcast", "-"],
        input=json.dumps({"agent_id": "cli", "text": "from the client"}),
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60,
    )
    assert posted.returncode == 0, posted.stderr
    assert json.loads(posted.stdout) == {"ok": True, "seq": 1, "topic": "general"}

    state = subprocess.run(
        [*client, "room_state"], capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60
    )
    assert state.returncode == 0 and json.loads(state.stdout)["last_seq"] == 1

    refused = subprocess.run(
        [*client, "room_broadcast", json.dumps({"agent_id": "cli", "text": "x", "topic": "Bad Topic"})],
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60,
    )
    assert refused.returncode == 2
    assert json.loads(refused.stdout)["ok"] is False

    nobody = subprocess.run(
        [sys.executable, "-m", "packages.coordination_room.client", "--url", "http://127.0.0.1:9/mcp", "room_state"],
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60,
    )
    assert nobody.returncode == 1
    assert "room call failed" in nobody.stderr
