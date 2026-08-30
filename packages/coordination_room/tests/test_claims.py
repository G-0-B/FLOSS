"""RED tests for ClaimTable.

Production change that would make these fail: two exclusive holders
on one path, or same-agent re-claim treated as conflict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.claims import ClaimConflict, ClaimTable  # noqa: E402


def test_second_agent_on_same_path_conflicts():
    table = ClaimTable()
    table.claim("grok", "packages/foo.py")
    with pytest.raises(ClaimConflict) as exc:
        table.claim("claude", "packages/foo.py")
    assert exc.value.holder == "grok"
    assert exc.value.path == "packages/foo.py"


def test_same_agent_reclaim_is_idempotent():
    table = ClaimTable()
    table.claim("grok", "packages/foo.py")
    table.claim("grok", "packages/foo.py")
    snap = table.snapshot()
    assert snap == {"packages/foo.py": "grok"}


def test_release_frees_path_for_next_holder():
    table = ClaimTable()
    table.claim("grok", "packages/foo.py")
    table.release("grok", "packages/foo.py")
    table.claim("claude", "packages/foo.py")
    assert table.snapshot()["packages/foo.py"] == "claude"


def test_release_by_non_holder_denied():
    table = ClaimTable()
    table.claim("grok", "packages/foo.py")
    with pytest.raises(ClaimConflict):
        table.release("claude", "packages/foo.py")


def test_two_paths_do_not_conflict():
    table = ClaimTable()
    table.claim("grok", "a.py")
    table.claim("claude", "b.py")
    assert table.snapshot() == {"a.py": "grok", "b.py": "claude"}
