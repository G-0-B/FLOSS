"""RED tests for CoordinationRoom log replay.

Production change that would make these fail: conflict written to the
log, or a restarted room forgetting a live claim.
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
from packages.coordination_room.room import CoordinationRoom  # noqa: E402


def _room(tmp_path: Path) -> CoordinationRoom:
    return CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")


def test_claim_appends_event(tmp_path: Path):
    room = _room(tmp_path)
    result = room.claim("grok", "a.py")
    assert result["ok"] is True
    assert result["seq"] == 1
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
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
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").strip().splitlines()
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
