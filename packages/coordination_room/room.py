"""Coordination room: claim table + event log + board projection under one lock."""

from __future__ import annotations

import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.coordination_room.board import (
    DEFAULT_TOPIC,
    SUGGESTED_TOPICS,
    check_topic,
    topic_of,
    topic_summary,
    write_board,
)
from packages.coordination_room.claims import ClaimTable
from packages.coordination_room.evidence import resolve_all
from packages.coordination_room.log import TEXT_MAX, EventLog
from packages.coordination_room.paths import normalize_path

INTENT_MAX = 256


class BoardPathError(ValueError):
    """The board path names the event log."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_board_path(log_path: Path, board_path: Path) -> None:
    """Refuse a board path that names the event log, by path or by file identity.

    Pure check: opens nothing. Staging is not checked here because write_board
    stages through a fresh mkstemp file and swaps names; it never opens an
    existing file for writing.
    """
    same_name = os.path.normcase(str(board_path.resolve())) == os.path.normcase(
        str(log_path.resolve())
    )
    same_file = board_path.exists() and log_path.exists() and os.path.samefile(
        board_path, log_path
    )
    if same_name or same_file:
        raise BoardPathError(f"board_path {board_path} is the event log {log_path}")


class CoordinationRoom:
    def __init__(
        self, root: Path, log_path: Path, board_path: Path | None = None
    ) -> None:
        if board_path is not None:
            check_board_path(log_path, board_path)
        self._root = root.resolve()
        self._log_path = log_path
        self._table = ClaimTable()
        self._log = EventLog(log_path)
        self._board_path = board_path
        # What the last projection did, for room_state: the daemon's stderr
        # goes to a hidden console, so nobody would see it there.
        self._board_as_of: str | None = None
        self._board_error: str | None = None
        self._lock = threading.Lock()
        self._replay()

    def _replay(self) -> None:
        for event in self._log.load():
            kind = event.get("type")
            if kind == "claim":
                self._table.force_set(event["path"], event["agent_id"])
            elif kind == "release":
                self._table.force_drop(event["path"])

    def _project(self) -> None:
        """Rewrite BOARD.md after a logged event. Never at construction: a process
        that has not won the daemon slot must not write. A failed view must not
        fail a post; the failure is kept for room_state.

        The board path is checked again here, not only at construction: a
        directory on the board's path can be re-pointed (junction, symlink)
        while the room runs, and the stored path would then name the log. This
        closes that for any alias present when a projection starts. It is not
        a defence against something racing to re-point a directory between
        this check and the rename.
        """
        if self._board_path is None:
            return
        now = _utc_now()
        try:
            check_board_path(self._log_path, self._board_path)
            events = self._log.load()
            write_board(self._board_path, events, skipped=self._log.skipped)
        except BoardPathError as exc:
            self._board_error = f"refused at {now}: {exc}"
        except OSError as exc:
            self._board_error = f"failed at {now}: {exc}"
        else:
            self._board_as_of, self._board_error = now, None
            return
        print(f"[coordination_room] BOARD.md projection {self._board_error}", file=sys.stderr)

    def _find_broadcast(self, seq: int) -> dict[str, Any]:
        for event in self._log.load():
            if int(event["seq"]) == seq and event.get("type") == "broadcast":
                return event
        raise ValueError(f"reply_to {seq} is not a broadcast")

    def claim(self, agent_id: str, path: str, intent: str = "") -> dict[str, Any]:
        if not isinstance(intent, str):
            raise ValueError("intent must be a string")
        if len(intent.encode("utf-8")) > INTENT_MAX:
            raise ValueError(f"intent exceeds {INTENT_MAX} bytes")
        key = normalize_path(self._root, path)
        with self._lock:
            if self._table.snapshot().get(key) == agent_id:
                return {"ok": True, "path": key, "agent_id": agent_id, "seq": self._log._seq}
            self._table.claim(agent_id, key)
            fields: dict[str, Any] = {"path": key}
            if intent.strip():
                fields["intent"] = intent.strip()
            try:
                event = self._log.append("claim", agent_id, **fields)
            except OSError:
                # No row, no claim: otherwise a retry would be told "ok" for a
                # claim the log never recorded and a restart would forget.
                self._table.force_drop(key)
                raise
            self._project()
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def release(self, agent_id: str, path: str) -> dict[str, Any]:
        key = normalize_path(self._root, path)
        with self._lock:
            if key not in self._table.snapshot():
                # Nothing to release: say so without adding a row.
                return {"ok": True, "path": key, "agent_id": agent_id, "seq": self._log._seq}
            self._table.release(agent_id, key)
            try:
                event = self._log.append("release", agent_id, path=key)
            except OSError:
                self._table.force_set(key, agent_id)
                raise
            self._project()
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def broadcast(
        self,
        agent_id: str,
        text: str,
        *,
        topic: str | None = None,
        evidence_refs: list[str] | None = None,
        reply_to: int | None = None,
    ) -> dict[str, Any]:
        if not agent_id.strip():
            raise ValueError("empty agent_id")
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if len(text.encode("utf-8")) > TEXT_MAX:
            raise ValueError(f"broadcast text exceeds {TEXT_MAX} bytes")
        if topic is not None:
            topic = check_topic(topic)
        # Looked up before the lock: a commit probe is a subprocess, and the lock
        # guards the log, not the filesystem. So the label describes the lookup
        # at `evidence_checked_at`, not the state at the moment of the append.
        checked_at = _utc_now()
        status, checked = resolve_all(self._root, evidence_refs)
        with self._lock:
            fields: dict[str, Any] = {}
            if reply_to is not None:
                parent = self._find_broadcast(reply_to)
                parent_topic = topic_of(parent)
                if topic is not None and topic != parent_topic:
                    raise ValueError(
                        f"reply topic must match parent topic {parent_topic!r}"
                    )
                topic = parent_topic
                fields["reply_to"] = reply_to
                fields["thread_id"] = parent.get("thread_id", parent["seq"])
            fields["topic"] = topic or DEFAULT_TOPIC
            if checked:
                fields["evidence_refs"] = [c["ref"] for c in checked]
                fields["evidence_status"] = status
                fields["evidence_checked"] = checked
                fields["evidence_checked_at"] = checked_at
            event = self._log.append("broadcast", agent_id, text=text, **fields)
            self._project()
            result: dict[str, Any] = {
                "ok": True,
                "seq": event["seq"],
                "topic": fields["topic"],
            }
            if checked:
                result["evidence_status"] = status
            return result

    def read(
        self,
        since_seq: int = 0,
        *,
        topic: str | None = None,
        thread_id: int | None = None,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            events = [e for e in self._log.load() if int(e["seq"]) > since_seq]
        if topic is not None:
            events = [e for e in events if topic_of(e) == topic]
        if thread_id is not None:
            events = [
                e
                for e in events
                if e.get("thread_id") == thread_id or e["seq"] == thread_id
            ]
        if limit > 0:
            events = events[:limit]
        return events

    def topics(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
        return {"topics": topic_summary(events), "suggested": list(SUGGESTED_TOPICS)}

    def state(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
            last = events[-1]["seq"] if events else 0
            speakers = sorted({e["agent_id"] for e in events})
            return {
                "claims": self._table.snapshot(),
                "last_seq": last,
                "speakers": speakers,
                # Which bus this is. A caller checks these before a live post.
                "root": str(self._root),
                "log": str(self._log_path),
                "board": str(self._board_path) if self._board_path else None,
                # Health a caller can see: when the board was last written, why
                # the last write failed if it did, and how many log lines were
                # unreadable and skipped.
                "board_as_of": self._board_as_of,
                "board_last_error": self._board_error,
                "log_skipped_lines": self._log.skipped,
            }
