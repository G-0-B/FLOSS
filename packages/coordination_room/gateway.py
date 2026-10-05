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


def _write_failed(exc: OSError) -> str:
    # The row was not written and nothing was changed. Said in the reply,
    # because a raised exception would reach the caller as a protocol error.
    return _error(f"log write failed, nothing was recorded: {exc}")


class CoordinationRoomTools:
    def __init__(
        self,
        root: Path,
        log_path: Path,
        room: CoordinationRoom | None = None,
        board_path: Path | None = None,
    ) -> None:
        self._room = room or CoordinationRoom(
            root=root, log_path=log_path, board_path=board_path
        )

    def room_claim(self, agent_id: str, path: str, intent: str = "") -> str:
        try:
            return _ok(self._room.claim(agent_id, path, intent=intent))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))
        except OSError as exc:
            return _write_failed(exc)

    def room_release(self, agent_id: str, path: str) -> str:
        try:
            return _ok(self._room.release(agent_id, path))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))
        except OSError as exc:
            return _write_failed(exc)

    def room_broadcast(
        self,
        agent_id: str,
        text: str,
        topic: str | None = None,
        evidence_refs: list[str] | None = None,
        reply_to: int | None = None,
    ) -> str:
        try:
            return _ok(
                self._room.broadcast(
                    agent_id,
                    text,
                    topic=topic,
                    evidence_refs=evidence_refs,
                    reply_to=reply_to,
                )
            )
        except ValueError as exc:
            return _error(str(exc))
        except OSError as exc:
            return _write_failed(exc)

    def room_read(
        self,
        since_seq: int = 0,
        topic: str | None = None,
        thread_id: int | None = None,
        limit: int = 0,
    ) -> str:
        events = self._room.read(
            since_seq=since_seq, topic=topic, thread_id=thread_id, limit=limit
        )
        return _ok({"events": events})

    def room_topics(self) -> str:
        return _ok(self._room.topics())

    def room_state(self) -> str:
        return _ok(self._room.state())
