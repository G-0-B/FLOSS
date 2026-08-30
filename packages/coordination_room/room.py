"""Coordination room: claim table + event log under one lock."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from packages.coordination_room.claims import ClaimConflict, ClaimTable
from packages.coordination_room.log import TEXT_MAX, EventLog
from packages.coordination_room.paths import normalize_path


class CoordinationRoom:
    def __init__(self, root: Path, log_path: Path) -> None:
        self._root = root.resolve()
        self._table = ClaimTable()
        self._log = EventLog(log_path)
        self._lock = threading.Lock()
        self._replay()

    def _replay(self) -> None:
        for event in self._log.load():
            kind = event.get("type")
            if kind == "claim":
                self._table.force_set(event["path"], event["agent_id"])
            elif kind == "release":
                self._table.force_drop(event["path"])

    def claim(self, agent_id: str, path: str) -> dict[str, Any]:
        key = normalize_path(self._root, path)
        with self._lock:
            already = self._table.snapshot().get(key) == agent_id
            self._table.claim(agent_id, key)
            if already:
                return {"ok": True, "path": key, "agent_id": agent_id, "seq": self._log._seq}
            event = self._log.append("claim", agent_id, path=key)
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def release(self, agent_id: str, path: str) -> dict[str, Any]:
        key = normalize_path(self._root, path)
        with self._lock:
            self._table.release(agent_id, key)
            event = self._log.append("release", agent_id, path=key)
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def broadcast(self, agent_id: str, text: str) -> dict[str, Any]:
        if not agent_id.strip():
            raise ValueError("empty agent_id")
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if len(text.encode("utf-8")) > TEXT_MAX:
            raise ValueError(f"broadcast text exceeds {TEXT_MAX} bytes")
        with self._lock:
            event = self._log.append("broadcast", agent_id, text=text)
            return {"ok": True, "seq": event["seq"]}

    def read(self, since_seq: int = 0) -> list[dict[str, Any]]:
        with self._lock:
            return [e for e in self._log.load() if int(e["seq"]) > since_seq]

    def state(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
            last = events[-1]["seq"] if events else 0
            speakers = sorted({e["agent_id"] for e in events})
            return {
                "claims": self._table.snapshot(),
                "last_seq": last,
                "speakers": speakers,
            }
