"""RED tests for CoordinationRoom log replay.

Production change that would make these fail: conflict written to the
log, a restarted room forgetting a live claim, or a row cut in two at a
U+2028, U+2029 or U+0085 inside a string value.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.claims import ClaimConflict  # noqa: E402
from packages.coordination_room.log import EventLog  # noqa: E402
from packages.coordination_room.room import CoordinationRoom  # noqa: E402


def _room(tmp_path: Path) -> CoordinationRoom:
    return CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")


def _rows(path: Path) -> list[str]:
    # Split on "\n" only: str.splitlines() also breaks on U+2028, U+2029
    # and U+0085, which json.dumps(ensure_ascii=False) writes raw.
    return [line for line in path.read_text(encoding="utf-8").split("\n") if line]


def test_claim_appends_event(tmp_path: Path):
    room = _room(tmp_path)
    result = room.claim("grok", "a.py")
    assert result["ok"] is True
    assert result["seq"] == 1
    lines = _rows(tmp_path / "events.jsonl")
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["type"] == "claim"
    assert event["path"] == "a.py"
    assert event["agent_id"] == "grok"


def test_conflict_does_not_append(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py")
    with pytest.raises(ClaimConflict):
        room.claim("claude", "a.py")
    lines = _rows(tmp_path / "events.jsonl")
    assert len(lines) == 1


def test_replay_restores_claims(tmp_path: Path):
    first = _room(tmp_path)
    first.claim("grok", "a.py")
    first.broadcast("grok", "working a.py")
    second = _room(tmp_path)
    assert second.state()["claims"] == {"a.py": "grok"}
    read = second.read(since_seq=0)
    assert len(read) == 2
    assert read[1]["type"] == "broadcast"
    assert read[1]["text"] == "working a.py"


def test_broadcast_text_cap(tmp_path: Path):
    room = _room(tmp_path)
    with pytest.raises(ValueError):
        room.broadcast("grok", "x" * 4097)


@pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\u0085"])
def test_unicode_line_separator_in_text_survives_reload(tmp_path: Path, separator: str):
    path = tmp_path / "events.jsonl"
    EventLog(path).append("broadcast", "grok", text=f"a{separator}b")
    assert len(_rows(path)) == 1

    reloaded = EventLog(path)
    events = reloaded.load()
    assert len(events) == 1
    assert events[0]["text"] == f"a{separator}b"
    assert reloaded.append("broadcast", "grok", text="next")["seq"] == 2


def test_plain_rows_and_blank_lines_load_as_before(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    first = {"seq": 1, "type": "claim", "agent_id": "grok", "path": "a.py"}
    second = {"seq": 2, "type": "broadcast", "agent_id": "grok", "text": "hi"}
    raw = json.dumps(first) + "\r\n\r\n   \r\n" + json.dumps(second) + "\r\n"
    path.write_bytes(raw.encode("utf-8"))

    log = EventLog(path)
    assert log.load() == [first, second]
    assert log.append("broadcast", "grok", text="next")["seq"] == 3
