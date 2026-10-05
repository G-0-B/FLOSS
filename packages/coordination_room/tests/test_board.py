"""RED tests for the BOARD.md projection.

Production change that would make these fail: a released claim still listed,
an unresolved evidence ref rendered as resolved, a pipe or newline in message
text breaking the claims table, a board with no as-of time (so a stale roster
reads as current), room claims presented as write authorization, or staging
through a predictable file name that a hard link could aim at the log.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.board import (  # noqa: E402
    render_board,
    topic_of,
    topic_summary,
    write_board,
)

NOW = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
ROSTER = "## Agents seen in the 24h before "


def _event(seq: int, kind: str, agent: str, ts: str = "2026-10-02T11:00:00Z", **fields):
    return {"seq": seq, "ts": ts, "type": kind, "agent_id": agent, **fields}


def test_board_states_its_as_of_time_and_seq():
    events = [_event(4, "broadcast", "a", text="x", topic="general")]
    board = render_board(events, NOW)
    assert "As of: 2026-10-02T12:00:00Z, seq 4." in board
    assert ROSTER + "2026-10-02T12:00:00Z" in board


def test_claims_are_labelled_advisory_not_authorization():
    board = render_board([_event(1, "claim", "grok", path="a.py")], NOW)
    assert "## Room claims (advisory)" in board
    assert "not write authorization" in board


def test_active_claim_row_shows_owner_and_intent():
    events = [_event(1, "claim", "grok", path="a.py", intent="fix the | pipe")]
    board = render_board(events, NOW)
    assert "| a.py | grok | 2026-10-02T11:00:00Z | 1h | fix the \\| pipe |" in board


def test_released_claim_is_absent():
    events = [
        _event(1, "claim", "grok", path="a.py"),
        _event(2, "release", "grok", path="a.py"),
    ]
    board = render_board(events, NOW)
    assert "a.py" not in board
    claims = board.split("## Room claims (advisory)")[1].split("## Messages by topic")[0]
    assert claims.rstrip().endswith("None.")


def test_messages_group_by_topic_and_legacy_rows_read_as_general():
    events = [
        _event(1, "broadcast", "grok", text="legacy row, no topic"),
        _event(2, "broadcast", "claude", text="shipped", topic="announcements"),
    ]
    board = render_board(events, NOW)
    assert board.index("### #announcements") < board.index("### #general")
    assert "- #1 2026-10-02T11:00:00Z **grok**: legacy row, no topic" in board
    assert "**claude**: shipped" in board


def test_evidence_tags_never_say_verified():
    events = [
        _event(
            1, "broadcast", "a", text="ok", topic="general",
            evidence_refs=["file:x.md"], evidence_status="resolved",
        ),
        _event(
            2, "broadcast", "b", text="bad", topic="general",
            evidence_refs=["file:y.md"], evidence_status="unresolved",
        ),
    ]
    board = render_board(events, NOW)
    assert "[evidence resolved] (refs: file:x.md)" in board
    assert "[evidence UNRESOLVED] (refs: file:y.md)" in board
    assert "VERIFIED" not in board.upper()


def test_reply_marks_parent():
    events = [
        _event(1, "broadcast", "a", text="q?", topic="inquiries"),
        _event(2, "broadcast", "b", text="a.", topic="inquiries", reply_to=1, thread_id=1),
    ]
    assert "**b** re #1: a." in render_board(events, NOW)


def test_newlines_and_unicode_separators_in_text_are_flattened():
    events = [_event(1, "broadcast", "a", text="one\ntwo\u2028three", topic="general")]
    board = render_board(events, NOW)
    assert "one two three" in board


def test_long_text_is_truncated():
    events = [_event(1, "broadcast", "a", text="x" * 1000, topic="general")]
    rows = render_board(events, NOW).split("\n")
    line = next(row for row in rows if row.startswith("- #1"))
    assert line.endswith("...")
    assert len(line) < 400


def test_roster_window_excludes_stale_agents():
    events = [
        _event(1, "broadcast", "old", ts="2026-10-01T11:59:00Z", text="x", topic="general"),
        _event(2, "broadcast", "fresh", ts="2026-10-02T11:30:00Z", text="y", topic="general"),
    ]
    roster = render_board(events, NOW).split(ROSTER)[1]
    assert "fresh" in roster
    assert "old" not in roster


def test_same_log_rendered_after_an_idle_day_drops_the_roster_and_says_when():
    events = [_event(1, "broadcast", "a", ts="2026-10-02T11:30:00Z", text="x", topic="general")]
    fresh = render_board(events, NOW)
    idle = render_board(events, NOW + timedelta(hours=24, minutes=31))
    assert "- a (last 2026-10-02T11:30:00Z)" in fresh.split(ROSTER)[1]
    assert idle.split(ROSTER)[1].strip().endswith("None.")
    assert "As of: 2026-10-03T12:31:00Z, seq 1." in idle
    # The board on disk is whichever of these was written last: its own header
    # is the only thing that says how old the roster is.
    assert fresh != idle


def test_topic_of_derives_claims_for_claim_and_release_rows():
    assert topic_of({"type": "claim"}) == "claims"
    assert topic_of({"type": "release"}) == "claims"
    assert topic_of({"type": "broadcast"}) == "general"
    assert topic_of({"type": "broadcast", "topic": "inquiries"}) == "inquiries"


def test_topic_summary_counts_and_last_seq():
    events = [
        _event(1, "claim", "a", path="p"),
        _event(2, "broadcast", "a", text="x", topic="general"),
        _event(3, "broadcast", "a", text="y", topic="general"),
    ]
    assert topic_summary(events) == [
        {"topic": "claims", "count": 1, "last_seq": 1},
        {"topic": "general", "count": 2, "last_seq": 3},
    ]


def test_write_board_replaces_atomically_and_leaves_no_staging_file(tmp_path: Path):
    target = tmp_path / "rooms" / "BOARD.md"
    write_board(target, [_event(1, "broadcast", "a", text="x", topic="general")], NOW)
    first = target.read_text(encoding="utf-8")
    write_board(target, [], NOW)
    assert target.read_text(encoding="utf-8") != first
    assert [p.name for p in target.parent.iterdir()] == ["BOARD.md"]
    assert "\r" not in target.read_text(encoding="utf-8")


def test_a_hard_link_at_the_old_staging_name_is_never_opened(tmp_path: Path):
    """Review round 2, R2-01: a predictable `BOARD.md.tmp` hard-linked to the log
    was opened for writing and truncated the log."""
    log = tmp_path / "events.jsonl"
    log.write_bytes(b'{"seq": 1}\n')
    os.link(log, tmp_path / "BOARD.md.tmp")
    write_board(tmp_path / "BOARD.md", [], NOW)
    assert log.read_bytes() == b'{"seq": 1}\n'


def test_a_board_replaced_by_a_hard_link_to_the_log_loses_only_its_name(tmp_path: Path):
    """An alias created after any construction-time check: the swap replaces the
    directory entry, so the log keeps its bytes."""
    log = tmp_path / "events.jsonl"
    log.write_bytes(b'{"seq": 1}\n')
    board = tmp_path / "BOARD.md"
    os.link(log, board)
    write_board(board, [_event(1, "broadcast", "a", text="x", topic="general")], NOW)
    assert log.read_bytes() == b'{"seq": 1}\n'
    assert board.read_text(encoding="utf-8").startswith("# Coordination board")


def test_an_old_claim_is_questioned_not_expired():
    """Review round 6 (Grok), M6: claims never expire, and a crashed session's
    claim looked exactly like a live one."""
    events = [
        _event(1, "claim", "gone", ts="2026-09-30T09:00:00Z", path="old.py"),
        _event(2, "claim", "here", ts="2026-10-02T11:30:00Z", path="new.py"),
    ]
    board = render_board(events, NOW)
    assert "| old.py | gone | 2026-09-30T09:00:00Z | 2d 3h, stale? |" in board
    assert "| new.py | here | 2026-10-02T11:30:00Z | 0h |" in board
    assert "Claims do not expire" in board


def test_board_says_names_are_not_authenticated():
    assert "Nothing authenticates them." in render_board([], NOW)


def test_skipped_log_lines_are_announced_on_the_board():
    assert "could not be read" not in render_board([], NOW)
    assert "**2 line(s) in the log could not be read and were skipped.**" in render_board(
        [], NOW, skipped=2
    )


def test_a_staging_file_left_by_a_killed_writer_is_cleared(tmp_path: Path):
    target = tmp_path / "BOARD.md"
    leftover = tmp_path / ".BOARD.md.abc123.tmp"
    leftover.write_text("half a board", encoding="utf-8")
    unrelated = tmp_path / "notes.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    write_board(target, [], NOW)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["BOARD.md", "notes.tmp"]
