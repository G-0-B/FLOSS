"""RED tests tying coordination-room.schema.json to what the room really writes.

Production change that would make these fail: the room logging a field the
schema forbids by type, or the schema dropping a field the room relies on.
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

jsonschema = pytest.importorskip("jsonschema")

from packages.coordination_room.room import CoordinationRoom  # noqa: E402

_SCHEMA = _REPO_ROOT / "docs" / "specs" / "coordination-room.schema.json"


def _validator():
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_every_row_the_room_writes_validates(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    room = CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")
    room.claim("grok", "a.py", intent="work")
    room.claim("claude", "b.py")
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "a1", reply_to=root, evidence_refs=["file:proof.md"])
    room.broadcast("b", "a2", evidence_refs=["file:missing.md", "wat"])
    room.release("grok", "a.py")
    validator = _validator()
    rows = room.read()
    assert len(rows) == 6
    for row in rows:
        validator.validate(row)


def test_legacy_rows_still_validate():
    validator = _validator()
    validator.validate({"seq": 1, "ts": "t", "type": "claim", "agent_id": "g", "path": "a"})
    validator.validate({"seq": 2, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "hi"})


_BASE = {"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "x"}


@pytest.mark.parametrize(
    "extra",
    [
        {"topic": "Bad Topic"},
        {"reply_to": 1},
        {"evidence_refs": ["file:a"]},
        {"evidence_status": "verified"},
        {
            "evidence_refs": ["file:a"],
            "evidence_status": "resolved",
            "evidence_checked": [{"ref": "file:a", "kind": "file", "ok": True}],
        },
        {
            "evidence_refs": ["file:a"],
            "evidence_status": "resolved",
            "evidence_checked_at": "t",
            "evidence_checked": [{"ref": "file:a", "kind": "file", "ok": True, "sha256": "short"}],
        },
    ],
)
def test_schema_rejects_malformed_board_rows(extra):
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate({**_BASE, **extra})
