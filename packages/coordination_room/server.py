"""FastMCP server for the coordination room.

Router, not controller. File claims + append-only log. Binds 127.0.0.1:7334.

Usage:
    python -m packages.coordination_room.server
"""

from __future__ import annotations

import os
from pathlib import Path

from packages.coordination_room.gateway import CoordinationRoomTools

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


def _audit_sink_path(filename: str) -> str:
    override = os.environ.get("FLOSS_AUDIT_DIR")
    base = (
        Path(override).expanduser()
        if override
        else _WORKSPACE_ROOT / ".agent-surface" / "heartbeat"
    )
    return str(base / filename)


_tools = CoordinationRoomTools(root=_room_root(), log_path=_log_path())
_SERVER_INSTRUCTIONS = (
    "FLOSSI0ULLK coordination room. Router, not controller. "
    "Claim a file path before writing it. Second claim on a held path is a "
    "system conflict, not a chat parse. Broadcast is append-only. "
    "Does not write workspace files. No pycrdt in v0."
)


def room_claim(agent_id: str, path: str) -> str:
    """Exclusive claim on a room-root-relative file path."""
    return _tools.room_claim(agent_id=agent_id, path=path)


def room_release(agent_id: str, path: str) -> str:
    """Release a path you hold."""
    return _tools.room_release(agent_id=agent_id, path=path)


def room_broadcast(agent_id: str, text: str) -> str:
    """Append a note to the room log. Does not require a claim."""
    return _tools.room_broadcast(agent_id=agent_id, text=text)


def room_read(since_seq: int = 0) -> str:
    """Read log events with seq > since_seq."""
    return _tools.room_read(since_seq=since_seq)


def room_state() -> str:
    """Current claims, last seq, speakers."""
    return _tools.room_state()


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
