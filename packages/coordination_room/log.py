"""Append-only JSONL event log. The only durable mutator."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_MAX = 4096


class EventLog:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._seq = 0
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            for event in self.load():
                self._seq = max(self._seq, int(event["seq"]))

    def load(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        events: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            events.append(json.loads(line))
        return events

    def append(self, event_type: str, agent_id: str, **fields: Any) -> dict[str, Any]:
        self._seq += 1
        record: dict[str, Any] = {
            "seq": self._seq,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": event_type,
            "agent_id": agent_id,
        }
        record.update(fields)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
