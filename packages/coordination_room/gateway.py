"""JSON tool router for the coordination room. Does not write workspace files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.coordination_room.claims import ClaimConflict
from packages.coordination_room.paths import PathEscape
from packages.coordination_room.room import CoordinationRoom


def _error(message: str, **extra: Any) -> str:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    return json.dumps(payload)


def _ok(payload: dict[str, Any]) -> str:
    payload.setdefault("ok", True)
    return json.dumps(payload)


class CoordinationRoomTools:
    def __init__(
        self,
        root: Path,
        log_path: Path,
        room: CoordinationRoom | None = None,
    ) -> None:
        self._room = room or CoordinationRoom(root=root, log_path=log_path)

    def room_claim(self, agent_id: str, path: str) -> str:
        try:
            return _ok(self._room.claim(agent_id, path))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))

    def room_release(self, agent_id: str, path: str) -> str:
        try:
            return _ok(self._room.release(agent_id, path))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))

    def room_broadcast(self, agent_id: str, text: str) -> str:
        try:
            return _ok(self._room.broadcast(agent_id, text))
        except ValueError as exc:
            return _error(str(exc))

    def room_read(self, since_seq: int = 0) -> str:
        events = self._room.read(since_seq=since_seq)
        return _ok({"events": events})

    def room_state(self) -> str:
        return _ok(self._room.state())
