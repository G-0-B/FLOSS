"""RED tests for JSON gateway.

Production change that would make these fail: conflict returned as
free text without holder, or read missing seq.
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


def _load(raw: str) -> dict:
    data = json.loads(raw)
    assert isinstance(data, dict)
    return data


def test_claim_conflict_json_includes_holder(tmp_path: Path):
    tools = CoordinationRoomTools(root=tmp_path, log_path=tmp_path / "events.jsonl")
    ok = _load(tools.room_claim(agent_id="grok", path="a.py"))
    assert ok["ok"] is True
    conflict = _load(tools.room_claim(agent_id="claude", path="a.py"))
    assert conflict["ok"] is False
    assert conflict["error"] == "conflict"
    assert conflict["holder"] == "grok"


def test_broadcast_then_read_round_trip(tmp_path: Path):
    tools = CoordinationRoomTools(root=tmp_path, log_path=tmp_path / "events.jsonl")
    _load(tools.room_broadcast(agent_id="grok", text="hello"))
    payload = _load(tools.room_read())
    assert payload["events"][0]["text"] == "hello"
    assert payload["events"][0]["seq"] == 1


def test_state_lists_live_claims(tmp_path: Path):
    tools = CoordinationRoomTools(root=tmp_path, log_path=tmp_path / "events.jsonl")
    _load(tools.room_claim(agent_id="grok", path="a.py"))
    state = _load(tools.room_state())
    assert state["claims"]["a.py"] == "grok"
    assert state["last_seq"] == 1
