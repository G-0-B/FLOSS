"""Test helper: serve the real FastMCP room on a free loopback port, under a temp directory."""

from __future__ import annotations

import contextlib
import importlib
import socket
import threading
import time
from pathlib import Path

ROOM_ENV = (
    "COORDINATION_ROOM_ROOT",
    "COORDINATION_ROOM_LOG",
    "COORDINATION_ROOM_BOARD",
    "FLOSS_AUDIT_DIR",
    "FLOSS_AGENT_DIR",
)


def free_port() -> int:
    """A port nothing is listening on right now. Not reserved: bind it soon."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def pin_room_env(monkeypatch, tmp_path: Path) -> Path:
    """Clear every room variable, then pin root, log and audit under tmp_path.

    Cleared, not inherited: an operator's COORDINATION_ROOM_BOARD or
    FLOSS_AGENT_DIR must never be written to by a test. Returns the log path.
    """
    for name in ROOM_ENV:
        monkeypatch.delenv(name, raising=False)
    log = tmp_path / "rooms" / "events.jsonl"
    monkeypatch.setenv("COORDINATION_ROOM_ROOT", str(tmp_path))
    monkeypatch.setenv("COORDINATION_ROOM_LOG", str(log))
    monkeypatch.setenv("FLOSS_AUDIT_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path / "agent"))
    return log


def reload_server():
    """The server module, re-imported under the current environment."""
    import packages.coordination_room.server as module

    return importlib.reload(module)


@contextlib.contextmanager
def serving(app, port: int):
    """Run an ASGI app on 127.0.0.1:port in a thread until the block exits."""
    import httpx
    import uvicorn

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while True:
        try:
            httpx.get(f"http://127.0.0.1:{port}/", timeout=1)
            break
        except httpx.HTTPError:
            if time.monotonic() > deadline:
                raise AssertionError(f"port {port} never came up") from None
            time.sleep(0.1)
    try:
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=5)
