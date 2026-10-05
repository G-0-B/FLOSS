"""Append-only JSONL event log. The only durable mutator."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_MAX = 4096


class EventLog:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._seq = 0
        # Lines the last load() could not use: a write torn by a kill, or
        # anything that is not a JSON object with an integer seq. They are
        # skipped and counted, never rewritten: the log is append-only.
        self.skipped = 0
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            for event in self.load():
                self._seq = max(self._seq, int(event["seq"]))

    def load(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            self.skipped = 0
            return []
        events: list[dict[str, Any]] = []
        skipped = 0
        # Split on "\n" only: str.splitlines() also breaks on U+2028, U+2029
        # and U+0085, which append() writes raw inside string values.
        for line in self._path.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            seq = row.get("seq") if isinstance(row, dict) else None
            if isinstance(seq, bool) or not isinstance(seq, int):
                skipped += 1
                continue
            events.append(row)
        self.skipped = skipped
        return events

    def _ends_mid_line(self) -> bool:
        """True if the file's last byte is not a newline: the previous write was torn."""
        try:
            with self._path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    return False
                handle.seek(-1, os.SEEK_END)
                return handle.read(1) != b"\n"
        except FileNotFoundError:
            return False

    def append(self, event_type: str, agent_id: str, **fields: Any) -> dict[str, Any]:
        seq = self._seq + 1
        record: dict[str, Any] = {
            "seq": seq,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": event_type,
            "agent_id": agent_id,
        }
        record.update(fields)
        # A torn tail must not swallow this row: start it on its own line.
        lead = "\n" if self._ends_mid_line() else ""
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(lead + json.dumps(record, ensure_ascii=False) + "\n")
        # Only a row that was written consumes its number.
        self._seq = seq
        return record
