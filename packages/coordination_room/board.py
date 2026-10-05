"""BOARD.md projection: a view of the event log as of a stated time, never a source of truth."""

from __future__ import annotations

import glob
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_TOPIC = "general"
SUGGESTED_TOPICS = ("announcements", "claims", "inquiries", "general")
RECENT_PER_TOPIC = 20
ROSTER_WINDOW = timedelta(hours=24)
# A claim never expires. Past this age the board asks the question; it does
# not answer it.
CLAIM_STALE_AFTER = timedelta(hours=24)
SNIPPET_MAX = 280

_TOPIC = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def check_topic(topic: str) -> str:
    if not isinstance(topic, str) or not _TOPIC.fullmatch(topic):
        raise ValueError(f"topic must match {_TOPIC.pattern}")
    return topic


def topic_of(event: dict[str, Any]) -> str:
    """Stored topic, else derived: claim/release rows live under `claims`."""
    stored = event.get("topic")
    if stored:
        return str(stored)
    return "claims" if event.get("type") in ("claim", "release") else DEFAULT_TOPIC


def topic_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for event in events:
        row = seen.setdefault(topic_of(event), {"topic": topic_of(event), "count": 0})
        row["count"] += 1
        row["last_seq"] = int(event["seq"])
    return [seen[name] for name in sorted(seen)]


def live_claims(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    held: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("type") == "claim":
            held[event["path"]] = event
        elif event.get("type") == "release":
            held.pop(event["path"], None)
    return held


def _parse_ts(value: Any) -> datetime | None:
    try:
        return datetime.strptime(value, _TS_FORMAT).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _cell(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _snippet(text: str) -> str:
    flat = " ".join(text.split())
    if len(flat) <= SNIPPET_MAX:
        return flat
    return flat[: SNIPPET_MAX - 3] + "..."


def _age(claimed: Any, now: datetime) -> str:
    stamp = _parse_ts(claimed)
    if stamp is None:
        return "unknown"
    age = max(now - stamp, timedelta(0))
    hours = int(age.total_seconds() // 3600)
    text = f"{hours // 24}d {hours % 24}h" if hours >= 24 else f"{hours}h"
    return f"{text}, stale?" if age > CLAIM_STALE_AFTER else text


def _evidence_suffix(event: dict[str, Any]) -> str:
    status = event.get("evidence_status")
    refs = event.get("evidence_refs")
    tag = {"resolved": " [evidence resolved]", "unresolved": " [evidence UNRESOLVED]"}
    suffix = tag.get(status, "")
    if refs:
        suffix += " (refs: " + ", ".join(_snippet(str(r)) for r in refs) + ")"
    return suffix


def render_board(
    events: list[dict[str, Any]], now: datetime | None = None, skipped: int = 0
) -> str:
    """Render the board as of `now`. The roster and claim ages depend on `now`,
    not only on the log. `skipped` is the log's count of unusable lines."""
    now = now or datetime.now(timezone.utc)
    as_of = now.strftime(_TS_FORMAT)
    last_seq = events[-1]["seq"] if events else 0
    out = [
        "# Coordination board",
        "",
        "<!-- Generated from events.jsonl by packages/coordination_room/board.py. "
        "A view, not a record: edits are overwritten on the next room event. -->",
        "",
        f"As of: {as_of}, seq {last_seq}. Rewritten only when the room logs an event, "
        "so an idle board is as old as this line says.",
        "",
        "Agent names are whatever each caller sent. Nothing authenticates them.",
        "",
    ]
    if skipped:
        out += [
            f"**{skipped} line(s) in the log could not be read and were skipped.** "
            "Rows may be missing from this view; `room_state` reports the same count.",
            "",
        ]
    out += [
        "## Room claims (advisory)",
        "",
        "A room claim records who said they are editing a path. It is a convention, "
        "not write authorization. Claims do not expire: an old one may belong to a "
        "session that is gone.",
        "",
    ]
    claims = live_claims(events)
    if claims:
        out += ["| Path | Owner | Since | Age | Intent |", "|---|---|---|---|---|"]
        for path in sorted(claims):
            row = claims[path]
            out.append(
                f"| {_cell(path)} | {_cell(row['agent_id'])} | {_cell(row.get('ts', ''))} "
                f"| {_age(row.get('ts'), now)} | {_cell(row.get('intent', ''))} |"
            )
    else:
        out.append("None.")

    out += ["", "## Messages by topic", ""]
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("type") == "broadcast":
            by_topic.setdefault(topic_of(event), []).append(event)
    if not by_topic:
        out += ["None.", ""]
    for topic in sorted(by_topic):
        out += [f"### #{topic}", ""]
        for event in by_topic[topic][-RECENT_PER_TOPIC:]:
            reply = f" re #{event['reply_to']}" if event.get("reply_to") else ""
            out.append(
                f"- #{event['seq']} {event.get('ts', '')} "
                f"**{_cell(event['agent_id'])}**{reply}{_evidence_suffix(event)}: "
                f"{_snippet(event.get('text', ''))}"
            )
        out.append("")

    out += [f"## Agents seen in the 24h before {as_of}", ""]
    last_seen: dict[str, str] = {}
    for event in events:
        stamp = _parse_ts(event.get("ts"))
        if stamp is not None and now - stamp <= ROSTER_WINDOW:
            last_seen[event["agent_id"]] = event["ts"]
    if last_seen:
        out += [f"- {_cell(name)} (last {last_seen[name]})" for name in sorted(last_seen)]
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def write_board(
    path: Path,
    events: list[dict[str, Any]],
    now: datetime | None = None,
    skipped: int = 0,
) -> None:
    """Replace `path` atomically. Raises OSError; the caller decides it is non-fatal.

    The staging file is created fresh with O_EXCL by mkstemp, never opened by a
    predictable name: a pre-existing file at a fixed name (say, a hard link to
    the event log) would be truncated by the open. os.replace then swaps the
    directory entry, so even a `path` that is itself a hard link to the log
    loses only its name, never the log's bytes.
    """
    text = render_board(events, now, skipped)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = f".{path.name}."
    # The room is the only writer, so any staging file already here was left by
    # a writer that was killed between creating it and the swap.
    for leftover in path.parent.glob(f"{glob.escape(prefix)}*.tmp"):
        try:
            leftover.unlink()
        except OSError:
            pass
    fd, staged = tempfile.mkstemp(dir=path.parent, prefix=prefix, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(staged, path)
    except OSError:
        Path(staged).unlink(missing_ok=True)
        raise
