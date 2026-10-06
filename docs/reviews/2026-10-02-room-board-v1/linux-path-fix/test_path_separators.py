"""One file has one claim key on every platform, however its separators are written.

Found by the first Linux run of this package (2026-10-06). On POSIX a backslash
is an ordinary filename character, so a path written with backslashes and the
same path written with slashes were two keys: two agents could each hold "the
same file", and a dot-dot written with a backslash was accepted as a file name
inside the root.

Production change that would make these fail: treating a backslash as part of
a name, instead of as a separator, on any platform.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.claims import ClaimConflict  # noqa: E402
from packages.coordination_room.evidence import resolve_ref  # noqa: E402
from packages.coordination_room.paths import PathEscape, normalize_path  # noqa: E402
from packages.coordination_room.room import CoordinationRoom  # noqa: E402

BACKSLASH = chr(92)  # spelled out, so no shell or tool can eat the escape


def test_mixed_separators_collapse_to_one_key(tmp_path: Path):
    assert normalize_path(tmp_path, f"a{BACKSLASH}b/c.py") == "a/b/c.py"


def test_backslash_dotdot_escape_is_rejected(tmp_path: Path):
    with pytest.raises(PathEscape):
        normalize_path(tmp_path, f"..{BACKSLASH}secret.txt")


def test_one_file_written_two_ways_has_one_holder(tmp_path: Path):
    room = CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")
    assert room.claim("windows-agent", f"packages{BACKSLASH}foo.py")["path"] == "packages/foo.py"
    with pytest.raises(ClaimConflict):
        room.claim("linux-agent", "packages/foo.py")


def test_a_file_ref_resolves_with_either_separator(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("x", encoding="utf-8")
    assert resolve_ref(tmp_path, f"file:docs{BACKSLASH}x.md")["ok"] is True
    assert resolve_ref(tmp_path, "file:docs/x.md")["ok"] is True
