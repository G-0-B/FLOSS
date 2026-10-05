"""RED tests for the board tools on the JSON gateway.

Production change that would make these fail: a bad topic raising instead of
returning a JSON error, `room_read` ignoring its filters, or `room_topics`
missing from the gateway.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.gateway import CoordinationRoomTools  # noqa: E402


def _tools(tmp_path: Path) -> CoordinationRoomTools:
    return CoordinationRoomTools(
        root=tmp_path,
        log_path=tmp_path / "events.jsonl",
        board_path=tmp_path / "BOARD.md",
    )


def _load(raw: str) -> dict:
    data = json.loads(raw)
    assert isinstance(data, dict)
    return data


def test_broadcast_with_topic_and_evidence_round_trips(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    tools = _tools(tmp_path)
    out = _load(
        tools.room_broadcast(
            agent_id="claude",
            text="landed",
            topic="announcements",
            evidence_refs=["file:proof.md"],
        )
    )
    assert out == {
        "ok": True,
        "seq": 1,
        "topic": "announcements",
        "evidence_status": "resolved",
    }
    events = _load(tools.room_read(topic="announcements"))["events"]
    assert events[0]["evidence_refs"] == ["file:proof.md"]


def test_bad_topic_and_bad_reply_return_json_errors(tmp_path: Path):
    tools = _tools(tmp_path)
    bad_topic = _load(tools.room_broadcast(agent_id="a", text="x", topic="Bad Topic"))
    assert bad_topic["ok"] is False
    assert "topic" in bad_topic["error"]
    bad_reply = _load(tools.room_broadcast(agent_id="a", text="x", reply_to=9))
    assert bad_reply["ok"] is False


def test_read_filters_and_old_call_shape_still_works(tmp_path: Path):
    tools = _tools(tmp_path)
    tools.room_broadcast(agent_id="a", text="one", topic="inquiries")
    tools.room_broadcast(agent_id="a", text="two")
    assert len(_load(tools.room_read())["events"]) == 2
    assert [e["text"] for e in _load(tools.room_read(topic="inquiries"))["events"]] == ["one"]
    assert len(_load(tools.room_read(limit=1))["events"]) == 1


def test_topics_tool(tmp_path: Path):
    tools = _tools(tmp_path)
    tools.room_broadcast(agent_id="a", text="one", topic="inquiries")
    out = _load(tools.room_topics())
    assert out["topics"] == [{"topic": "inquiries", "count": 1, "last_seq": 1}]
    assert "general" in out["suggested"]


def test_claim_with_intent_appears_on_the_board(tmp_path: Path):
    tools = _tools(tmp_path)
    assert _load(tools.room_claim(agent_id="grok", path="a.py", intent="refactor"))["ok"]
    assert "refactor" in (tmp_path / "BOARD.md").read_text(encoding="utf-8")
    conflict = _load(tools.room_claim(agent_id="claude", path="a.py", intent="mine"))
    assert conflict["error"] == "conflict"
    assert conflict["holder"] == "grok"


def test_a_failed_log_write_is_a_json_error_not_an_exception(tmp_path: Path, monkeypatch):
    """Review round 6 (Grok), M5: raised to the MCP layer it reached the caller
    as a protocol error; the caller needs to know nothing was recorded."""
    from packages.coordination_room.log import EventLog

    def no_space(self, *args, **fields):
        raise OSError(28, "No space left on device")

    tools = _tools(tmp_path)
    monkeypatch.setattr(EventLog, "append", no_space)
    for reply in (
        tools.room_claim(agent_id="grok", path="a.py"),
        tools.room_broadcast(agent_id="grok", text="x"),
    ):
        out = _load(reply)
        assert out["ok"] is False
        assert "nothing was recorded" in out["error"]
    assert _load(tools.room_state())["claims"] == {}
