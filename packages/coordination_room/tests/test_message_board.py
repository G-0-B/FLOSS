"""RED tests for topics, threads, evidence and the BOARD.md hook on CoordinationRoom.

Production change that would make these fail: an unresolved ref rejecting the
post (the room labels, it does not gate), a reply landing in another topic, a
default `limit` silently truncating old callers, a failed board write failing
the post, a board path that can replace the log, or construction writing the
board before the caller owns the daemon slot.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import packages.coordination_room.room as room_module  # noqa: E402
from packages.coordination_room.log import EventLog  # noqa: E402
from packages.coordination_room.room import CoordinationRoom  # noqa: E402


def _room(tmp_path: Path, board: bool = False) -> CoordinationRoom:
    return CoordinationRoom(
        root=tmp_path,
        log_path=tmp_path / "events.jsonl",
        board_path=(tmp_path / "BOARD.md") if board else None,
    )


def test_plain_broadcast_defaults_to_general(tmp_path: Path):
    room = _room(tmp_path)
    result = room.broadcast("grok", "hello")
    assert result == {"ok": True, "seq": 1, "topic": "general"}
    assert room.read()[0]["topic"] == "general"


@pytest.mark.parametrize("topic", ["Bad Topic", "", "-x", "a" * 33, "UPPER"])
def test_bad_topic_is_rejected_and_nothing_is_logged(tmp_path: Path, topic: str):
    room = _room(tmp_path)
    with pytest.raises(ValueError):
        room.broadcast("grok", "hi", topic=topic)
    assert room.read() == []


def test_reply_inherits_topic_and_thread(tmp_path: Path):
    room = _room(tmp_path)
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    first = room.broadcast("b", "a1", reply_to=root)
    second = room.broadcast("c", "a2", reply_to=first["seq"])
    events = {e["seq"]: e for e in room.read()}
    assert first["topic"] == "inquiries"
    assert events[first["seq"]]["thread_id"] == root
    assert events[second["seq"]]["thread_id"] == root
    assert events[second["seq"]]["reply_to"] == first["seq"]


def test_reply_with_mismatched_topic_is_rejected(tmp_path: Path):
    room = _room(tmp_path)
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    with pytest.raises(ValueError, match="parent topic"):
        room.broadcast("b", "a1", topic="general", reply_to=root)


def test_reply_to_unknown_or_non_broadcast_is_rejected(tmp_path: Path):
    room = _room(tmp_path)
    claim = room.claim("a", "x.py")["seq"]
    with pytest.raises(ValueError, match="not a broadcast"):
        room.broadcast("b", "hi", reply_to=claim)
    with pytest.raises(ValueError, match="not a broadcast"):
        room.broadcast("b", "hi", reply_to=99)


def test_unresolved_evidence_is_labelled_not_rejected(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    room = _room(tmp_path)
    good = room.broadcast("a", "done", evidence_refs=["file:proof.md"])
    bad = room.broadcast("a", "done", evidence_refs=["file:missing.md"])
    plain = room.broadcast("a", "no refs")
    assert good["evidence_status"] == "resolved"
    assert bad["evidence_status"] == "unresolved"
    assert "evidence_status" not in plain
    rows = {e["seq"]: e for e in room.read()}
    assert rows[bad["seq"]]["evidence_checked"] == [
        {"ref": "file:missing.md", "kind": "file", "ok": False}
    ]
    assert rows[good["seq"]]["evidence_checked"] == [
        {"ref": "file:proof.md", "kind": "file", "ok": True}
    ]
    assert "evidence_refs" not in rows[plain["seq"]]
    assert "evidence_checked_at" not in rows[plain["seq"]]


def test_label_describes_the_lookup_and_says_when_it_ran(tmp_path: Path, monkeypatch):
    """The file can vanish between the lookup and the append. The row must not
    claim more than "this is what the lookup saw, at this time": the time is
    read before the lookup, and the lookup runs before the append. (An
    earlier version of this test compared timestamps at one-second
    resolution and could not fail.)"""
    proof = tmp_path / "proof.md"
    proof.write_text("x", encoding="utf-8")
    order = []
    real_lookup, real_append = room_module.resolve_all, EventLog.append

    def clock():
        order.append("clock")
        return "2001-01-01T00:00:00Z"

    def lookup_then_remove(root, refs):
        order.append("lookup")
        result = real_lookup(root, refs)
        proof.unlink()
        return result

    def append(self, *args, **fields):
        order.append("append")
        return real_append(self, *args, **fields)

    monkeypatch.setattr(room_module, "_utc_now", clock)
    monkeypatch.setattr(room_module, "resolve_all", lookup_then_remove)
    monkeypatch.setattr(EventLog, "append", append)
    room = _room(tmp_path)
    room.broadcast("a", "done", evidence_refs=["file:proof.md"])
    row = room.read()[0]
    assert not proof.exists()
    assert row["evidence_status"] == "resolved"
    assert row["evidence_checked_at"] == "2001-01-01T00:00:00Z"
    assert order == ["clock", "lookup", "append"]


def test_read_filters_by_topic_thread_and_limit(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("a", "x.py")
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "noise")
    room.broadcast("c", "a1", reply_to=root)
    assert [e["seq"] for e in room.read(topic="inquiries")] == [2, 4]
    assert [e["seq"] for e in room.read(topic="claims")] == [1]
    assert [e["seq"] for e in room.read(thread_id=root)] == [2, 4]
    assert [e["seq"] for e in room.read(limit=2)] == [1, 2]
    assert [e["seq"] for e in room.read(since_seq=2, limit=1)] == [3]
    assert len(room.read()) == 4


def test_legacy_rows_without_topic_read_as_general(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    EventLog(path).append("broadcast", "grok", text="old")
    room = CoordinationRoom(root=tmp_path, log_path=path)
    assert [e["text"] for e in room.read(topic="general")] == ["old"]
    assert room.topics()["topics"] == [{"topic": "general", "count": 1, "last_seq": 1}]


def test_topics_lists_counts_and_suggestions(tmp_path: Path):
    room = _room(tmp_path)
    room.broadcast("a", "x", topic="announcements")
    room.broadcast("a", "y")
    out = room.topics()
    assert [t["topic"] for t in out["topics"]] == ["announcements", "general"]
    assert out["suggested"] == ["announcements", "claims", "inquiries", "general"]


def test_claim_intent_is_logged_once_and_capped(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py", intent="  refactor  ")
    room.claim("grok", "a.py", intent="ignored on idempotent re-claim")
    rows = room.read()
    assert len(rows) == 1
    assert rows[0]["intent"] == "refactor"
    with pytest.raises(ValueError, match="intent exceeds"):
        room.claim("grok", "b.py", intent="x" * 257)


def test_claim_without_intent_logs_the_same_row_as_before(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py")
    row = room.read()[0]
    assert "intent" not in row
    assert set(row) == {"seq", "ts", "type", "agent_id", "path"}


def test_state_names_the_bus_it_serves(tmp_path: Path):
    state = _room(tmp_path, board=True).state()
    assert Path(state["root"]) == tmp_path.resolve()
    assert state["log"] == str(tmp_path / "events.jsonl")
    assert state["board"] == str(tmp_path / "BOARD.md")
    assert (state["board_as_of"], state["board_last_error"], state["log_skipped_lines"]) == (
        None,
        None,
        0,
    )
    assert _room(tmp_path).state()["board"] is None


def test_construction_writes_no_board(tmp_path: Path):
    """Building a room is what a duplicate daemon does before it loses the PID
    guard. It must not touch the board."""
    first = _room(tmp_path, board=True)
    board = tmp_path / "BOARD.md"
    assert not board.exists()
    first.broadcast("grok", "hello board")
    before = (board.read_bytes(), board.stat().st_mtime_ns)
    _room(tmp_path, board=True)
    assert (board.read_bytes(), board.stat().st_mtime_ns) == before


def test_board_is_rewritten_on_every_mutation(tmp_path: Path):
    room = _room(tmp_path, board=True)
    board = tmp_path / "BOARD.md"
    room.claim("grok", "a.py", intent="work")
    assert "| a.py | grok |" in board.read_text(encoding="utf-8")
    room.release("grok", "a.py")
    assert "a.py" not in board.read_text(encoding="utf-8")
    room.broadcast("grok", "hello board", topic="announcements")
    assert "hello board" in board.read_text(encoding="utf-8")
    board.unlink()
    _room(tmp_path, board=True).broadcast("grok", "after restart")
    text = board.read_text(encoding="utf-8")
    assert "hello board" in text and "after restart" in text


@pytest.mark.parametrize("board_name", ["events.jsonl", "EVENTS.JSONL"])
def test_board_path_that_is_the_log_is_refused_before_any_write(tmp_path: Path, board_name: str):
    log = tmp_path / "events.jsonl"
    EventLog(log).append("broadcast", "grok", text="keep me")
    before = log.read_bytes()
    if board_name != "events.jsonl" and not sys.platform.startswith("win"):
        pytest.skip("a case-distinct name is a different file off Windows")
    with pytest.raises(ValueError, match="event log"):
        CoordinationRoom(root=tmp_path, log_path=log, board_path=tmp_path / board_name)
    assert log.read_bytes() == before


def test_board_hard_linked_to_the_log_is_refused(tmp_path: Path):
    """Review round 2, R2-01: distinct path strings, one file."""
    log = tmp_path / "events.jsonl"
    EventLog(log).append("broadcast", "grok", text="keep me")
    before = log.read_bytes()
    os.link(log, tmp_path / "BOARD.md")
    with pytest.raises(ValueError, match="event log"):
        CoordinationRoom(root=tmp_path, log_path=log, board_path=tmp_path / "BOARD.md")
    assert log.read_bytes() == before


def test_hard_link_to_the_log_at_the_old_staging_name_survives_posts(tmp_path: Path):
    """Review round 2, R2-01, end to end: construction passes (the board path is
    a real, separate file), and posting must not truncate the log through the
    link."""
    log = tmp_path / "events.jsonl"
    EventLog(log).append("broadcast", "grok", text="keep me")
    os.link(log, tmp_path / "BOARD.md.tmp")
    room = _room(tmp_path, board=True)
    assert room.broadcast("grok", "second")["seq"] == 2
    assert [e["text"] for e in CoordinationRoom(root=tmp_path, log_path=log).read()] == [
        "keep me",
        "second",
    ]


def _link_directory(target: Path, link: Path) -> None:
    """A directory alias: a symlink where allowed, else an NTFS junction."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if sys.platform.startswith("win"):
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
        return
    pytest.skip("cannot create a directory alias here")


def test_board_directory_re_pointed_at_the_log_after_startup_is_refused(tmp_path: Path, capsys):
    """Review round 3, R3-02: board `alias/events.jsonl`, log `real/events.jsonl`.
    After construction, `alias` is replaced by a link to `real`, so the stored
    board path now names the log. The next projection must refuse, not replace
    the log with Markdown."""
    real, alias = tmp_path / "real", tmp_path / "alias"
    real.mkdir()
    alias.mkdir()
    log = real / "events.jsonl"
    room = CoordinationRoom(root=tmp_path, log_path=log, board_path=alias / "events.jsonl")
    room.broadcast("grok", "first")
    alias.rename(tmp_path / "alias-original")
    _link_directory(real, alias)
    assert room.broadcast("grok", "second")["seq"] == 2
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").split("\n") if line]
    assert [r["text"] for r in rows] == ["first", "second"]
    assert "BOARD.md projection refused" in capsys.readouterr().err


def test_board_failure_does_not_fail_the_post(tmp_path: Path, capsys):
    # board_path is a directory: os.replace raises OSError on every platform.
    # A directory inside tmp_path, so the staging file stays inside it too.
    blocked = tmp_path / "adir"
    blocked.mkdir()
    room = CoordinationRoom(
        root=tmp_path, log_path=tmp_path / "events.jsonl", board_path=blocked
    )
    result = room.broadcast("grok", "still logged")
    assert result["ok"] is True
    # The daemon's stderr goes to a hidden console; the state is where a
    # caller can see that the board is not being written.
    assert room.state()["board_last_error"].startswith("failed at ")
    assert room.state()["board_as_of"] is None
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")] == []
    rows = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").split("\n")
        if line
    ]
    assert rows[0]["text"] == "still logged"
    assert "BOARD.md projection failed" in capsys.readouterr().err


def test_board_health_is_visible_in_state_and_recovers(tmp_path: Path):
    room = _room(tmp_path, board=True)
    room.broadcast("grok", "one")
    healthy = room.state()
    assert healthy["board_as_of"] is not None and healthy["board_last_error"] is None
    board = tmp_path / "BOARD.md"
    board.unlink()
    board.mkdir()  # now the swap cannot succeed
    room.broadcast("grok", "two")
    assert room.state()["board_last_error"].startswith("failed at ")
    board.rmdir()
    room.broadcast("grok", "three")
    assert room.state()["board_last_error"] is None
    assert "three" in board.read_text(encoding="utf-8")


def _fail_next_append(monkeypatch) -> None:
    real = EventLog.append
    state = {"failed": False}

    def append(self, *args, **fields):
        if not state["failed"]:
            state["failed"] = True
            raise OSError(28, "No space left on device")
        return real(self, *args, **fields)

    monkeypatch.setattr(EventLog, "append", append)


def test_a_claim_whose_row_was_not_written_does_not_exist(tmp_path: Path, monkeypatch):
    """Review round 6 (Grok), M5: the table was set before the append, so after
    a failed write a retry was told "ok, seq 0", others got "conflict", and a
    restart forgot the claim."""
    room = _room(tmp_path)
    _fail_next_append(monkeypatch)
    with pytest.raises(OSError):
        room.claim("grok", "a.py")
    assert room.state()["claims"] == {}
    assert room.claim("claude", "a.py")["seq"] == 1
    assert [e["agent_id"] for e in room.read()] == ["claude"]


def test_a_release_whose_row_was_not_written_keeps_the_holder(tmp_path: Path, monkeypatch):
    room = _room(tmp_path)
    room.claim("grok", "a.py")
    _fail_next_append(monkeypatch)
    with pytest.raises(OSError):
        room.release("grok", "a.py")
    assert room.state()["claims"] == {"a.py": "grok"}
    assert room.release("grok", "a.py")["seq"] == 2


def test_releasing_a_path_nobody_holds_adds_no_row(tmp_path: Path):
    room = _room(tmp_path, board=True)
    room.broadcast("grok", "one")
    before = (tmp_path / "events.jsonl").read_bytes()
    assert room.release("anyone", "nobody.py") == {
        "ok": True,
        "path": "nobody.py",
        "agent_id": "anyone",
        "seq": 1,
    }
    assert (tmp_path / "events.jsonl").read_bytes() == before


def test_a_torn_last_line_does_not_take_the_room_down(tmp_path: Path):
    """Review round 6 (Grok), M2: a writer killed mid-line left a fragment. The
    running room then glued its next row onto it, and a restarted room could
    not load the log at all."""
    log = tmp_path / "events.jsonl"
    room = _room(tmp_path, board=True)
    room.broadcast("a", "one")
    room.claim("a", "x.py")
    with log.open("a", encoding="utf-8") as handle:
        handle.write('{"seq": 3, "ts": "x", "type": "broadcast", "agent_id": "a", "te')

    assert room.broadcast("a", "after the tear")["seq"] == 3
    lines = [line for line in log.read_text(encoding="utf-8").split("\n") if line.strip()]
    assert json.loads(lines[-1])["text"] == "after the tear"  # on a line of its own

    restarted = _room(tmp_path, board=True)
    assert [e["seq"] for e in restarted.read()] == [1, 2, 3]
    state = restarted.state()
    assert state["claims"] == {"x.py": "a"}
    assert state["log_skipped_lines"] == 1
    assert restarted.broadcast("a", "next")["seq"] == 4
    assert "1 line(s) in the log could not be read" in (tmp_path / "BOARD.md").read_text(
        encoding="utf-8"
    )


def test_rows_that_are_not_events_are_skipped_and_counted(tmp_path: Path):
    log = tmp_path / "events.jsonl"
    log.write_text(
        '{"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "a", "text": "ok"}\n'
        "[1, 2, 3]\n"
        '{"no": "seq"}\n'
        '{"seq": true, "type": "broadcast", "agent_id": "a", "text": "bool"}\n',
        encoding="utf-8",
    )
    room = _room(tmp_path)
    assert [e["seq"] for e in room.read()] == [1]
    assert room.state()["log_skipped_lines"] == 3
    assert room.broadcast("a", "next")["seq"] == 2


def test_a_failed_append_does_not_use_up_a_seq(tmp_path: Path, monkeypatch):
    room = _room(tmp_path)
    room.broadcast("a", "one")
    _fail_next_append(monkeypatch)
    with pytest.raises(OSError):
        room.broadcast("a", "lost")
    assert room.broadcast("a", "two")["seq"] == 2


def test_read_returns_every_row_by_default(tmp_path: Path):
    room = _room(tmp_path)
    for n in range(60):
        room.broadcast("a", f"row {n}")
    assert len(room.read()) == 60
