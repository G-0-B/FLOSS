"""The rollback promise, as a test: v0.1 code can serve a log this version wrote.

v0.1 is loaded from git (the commit this work is based on), run in its own
process against a log written here, and must replay the claims, read every
row and continue the sequence. Skipped where that commit is not available, a
shallow clone for instance.

Production change that would make this fail: a row shape v0.1 cannot load, or
a claim or release recorded in a way v0.1 replays differently.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.room import CoordinationRoom  # noqa: E402

V01_COMMIT = "4aab13e30f3c2960da787b47c90926256b4b5b73"
V01_FILES = ("__init__.py", "claims.py", "log.py", "paths.py", "room.py")

_V01_SCRIPT = """
import json, sys
from pathlib import Path
from packages.coordination_room.room import CoordinationRoom
root = Path(sys.argv[1])
room = CoordinationRoom(root=root, log_path=root / "events.jsonl")
state = room.state()
print(json.dumps({
    "keys": sorted(state),
    "claims": state["claims"],
    "last_seq": state["last_seq"],
    "rows": len(room.read()),
    "next": room.broadcast("v01", "written by v0.1")["seq"],
}))
"""


def _v01_package(target: Path) -> None:
    package = target / "packages" / "coordination_room"
    package.mkdir(parents=True)
    (target / "packages" / "__init__.py").write_text("", encoding="utf-8")
    for name in V01_FILES:
        shown = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "show", f"{V01_COMMIT}:packages/coordination_room/{name}"],
            capture_output=True,
        )
        if shown.returncode != 0:
            pytest.skip(f"v0.1 source not available from git ({V01_COMMIT[:7]})")
        (package / name).write_bytes(shown.stdout)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_v01_code_serves_a_log_written_by_this_version(tmp_path: Path):
    root = tmp_path / "room"
    root.mkdir()
    (root / "proof.md").write_text("x", encoding="utf-8")
    room = CoordinationRoom(root=root, log_path=root / "events.jsonl", board_path=root / "BOARD.md")
    room.claim("grok", "a.py", intent="work")
    question = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "answer", reply_to=question, evidence_refs=["file:proof.md", "wat"])
    room.claim("claude", "b.py")
    room.release("grok", "a.py")

    old = tmp_path / "v01"
    _v01_package(old)
    done = subprocess.run(
        [sys.executable, "-c", _V01_SCRIPT, str(root)],
        capture_output=True, text=True, cwd=old, timeout=60,
        env={"SystemRoot": __import__("os").environ.get("SystemRoot", ""), "PATH": ""},
    )
    assert done.returncode == 0, done.stderr
    seen = json.loads(done.stdout)
    assert seen == {
        "keys": ["claims", "last_seq", "speakers"],
        "claims": {"b.py": "claude"},
        "last_seq": 5,
        "rows": 5,
        "next": 6,
    }

    # And this version reads what v0.1 then wrote.
    back = CoordinationRoom(root=root, log_path=root / "events.jsonl")
    assert back.read()[-1]["text"] == "written by v0.1"
    assert back.state()["claims"] == {"b.py": "claude"}
    assert back.state()["log_skipped_lines"] == 0
