"""FastMCP server for the coordination room.

Router, not controller. File claims + append-only log. Binds 127.0.0.1:7334.

Usage:
    python -m packages.coordination_room.server
"""

from __future__ import annotations

import functools
import os
import threading
from pathlib import Path
from typing import Any

import anyio

from packages.coordination_room.gateway import CoordinationRoomTools
from packages.coordination_room.room import check_board_path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
_WORKSPACE_ROOT = _REPO_ROOT.parent


def _room_root() -> Path:
    override = os.environ.get("COORDINATION_ROOM_ROOT")
    return Path(override).expanduser() if override else _REPO_ROOT


def _log_path() -> Path:
    override = os.environ.get("COORDINATION_ROOM_LOG")
    if override:
        return Path(override).expanduser()
    return _WORKSPACE_ROOT / ".agent-surface" / "rooms" / "default" / "events.jsonl"


def _board_path() -> Path:
    override = os.environ.get("COORDINATION_ROOM_BOARD")
    if override:
        return Path(override).expanduser()
    return _log_path().parent / "BOARD.md"


def _audit_sink_path(filename: str) -> str:
    override = os.environ.get("FLOSS_AUDIT_DIR")
    base = (
        Path(override).expanduser()
        if override
        else _WORKSPACE_ROOT / ".agent-surface" / "heartbeat"
    )
    return str(base / filename)


# A board path that would overwrite the log stops the daemon here, before it
# serves anything. This is a path check only: nothing is opened or created.
check_board_path(_log_path(), _board_path())

_tools_instance: CoordinationRoomTools | None = None
_tools_lock = threading.Lock()


def _tools() -> CoordinationRoomTools:
    """The room, built on the first tool call rather than at import.

    A tool call can only arrive after run_http_daemon has won the PID slot, and
    the slot is only won once any previous owner has exited. So the log is
    replayed, the seq counter cached and the claim table rebuilt by the owner,
    from a log nobody else is still appending to. Building the room at import
    let a starting daemon cache a seq that the exiting one then reused, and
    grant a path the exiting one had just claimed.
    """
    global _tools_instance
    with _tools_lock:
        if _tools_instance is None:
            _tools_instance = CoordinationRoomTools(
                root=_room_root(), log_path=_log_path(), board_path=_board_path()
            )
        return _tools_instance


async def _in_thread(method: str, **arguments: Any) -> str:
    """Run one room call on a worker thread.

    FastMCP calls a synchronous tool directly on its event loop, so one post
    waiting on a `git` lookup would stall every other caller of the room. The
    room serialises its own writes with a lock, so a worker thread is safe.
    """

    def call() -> str:
        return getattr(_tools(), method)(**arguments)

    return await anyio.to_thread.run_sync(functools.partial(call))


_SERVER_INSTRUCTIONS = (
    "FLOSSI0ULLK coordination room. Router, not controller. "
    "Claim a file path before writing it. Second claim on a held path is a "
    "system conflict, not a chat parse. A room claim is a coordination "
    "convention, not write authorization; it does not expire, and agent names "
    "are not authenticated. Broadcast is append-only and may carry "
    "a topic, a reply_to, and evidence_refs (file:<path> or commit:<sha>); "
    "evidence is labelled resolved or unresolved by a lookup, never verified. "
    "BOARD.md is a generated view of the log. room_state names the root, log "
    "and board this room serves, and reports board and log health. "
    "Does not write workspace files. No pycrdt in v0."
)


async def room_claim(agent_id: str, path: str, intent: str = "") -> str:
    """Exclusive claim on a room-root-relative file path. Optional short intent."""
    return await _in_thread("room_claim", agent_id=agent_id, path=path, intent=intent)


async def room_release(agent_id: str, path: str) -> str:
    """Release a path you hold."""
    return await _in_thread("room_release", agent_id=agent_id, path=path)


async def room_broadcast(
    agent_id: str,
    text: str,
    topic: str | None = None,
    evidence_refs: list[str] | None = None,
    reply_to: int | None = None,
) -> str:
    """Append a note to the room log. Does not require a claim.

    topic: lowercase slug, default general (suggested: announcements, claims,
    inquiries, general). reply_to: seq of an earlier broadcast; the reply joins
    its topic and thread. evidence_refs: file:<path> or commit:<sha>; labelled
    resolved or unresolved, the post is admitted either way.
    """
    return await _in_thread(
        "room_broadcast",
        agent_id=agent_id,
        text=text,
        topic=topic,
        evidence_refs=evidence_refs,
        reply_to=reply_to,
    )


async def room_read(
    since_seq: int = 0,
    topic: str | None = None,
    thread_id: int | None = None,
    limit: int = 0,
) -> str:
    """Read log events with seq > since_seq, oldest first. limit 0 means all."""
    return await _in_thread(
        "room_read", since_seq=since_seq, topic=topic, thread_id=thread_id, limit=limit
    )


async def room_topics() -> str:
    """Topics in use with counts, plus the suggested defaults."""
    return await _in_thread("room_topics")


async def room_state() -> str:
    """Claims, last seq, speakers, the root, log and board paths served, and board and log health."""
    return await _in_thread("room_state")


_AUDIT_SINK = _audit_sink_path("janus-coordination-room-audit.jsonl")


def _create_mcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    app = FastMCP(
        "FLOSSI0ULLK Coordination Room",
        instructions=_SERVER_INSTRUCTIONS,
    )
    from packages.mcp_daemon import register_audited_tools

    register_audited_tools(
        app,
        (
            room_claim,
            room_release,
            room_broadcast,
            room_read,
            room_topics,
            room_state,
        ),
        _AUDIT_SINK,
    )
    return app


mcp = _create_mcp()


if __name__ == "__main__":
    if mcp is None:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    from packages.mcp_daemon import run_http_daemon

    os.chdir(_REPO_ROOT)
    run_http_daemon(mcp, pid_filename="coordination_room.pid", port=7334)
