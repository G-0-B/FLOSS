"""RED tests for PathNorm.

Production change that would make these fail: `..` escape accepted,
or Windows separators not collapsing to one key.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.paths import PathEscape, normalize_path  # noqa: E402


def test_relative_path_becomes_posix_key(tmp_path: Path):
    assert normalize_path(tmp_path, "packages/foo.py") == "packages/foo.py"


def test_backslash_collapses_to_same_key(tmp_path: Path):
    assert normalize_path(tmp_path, "packages\\foo.py") == "packages/foo.py"


def test_dotdot_escape_is_rejected(tmp_path: Path):
    with pytest.raises(PathEscape):
        normalize_path(tmp_path, "../secret.txt")


def test_absolute_inside_root_is_accepted(tmp_path: Path):
    inner = tmp_path / "a" / "b.py"
    inner.parent.mkdir()
    inner.write_text("x", encoding="utf-8")
    assert normalize_path(tmp_path, str(inner)) == "a/b.py"


def test_absolute_outside_root_is_rejected(tmp_path: Path, tmp_path_factory):
    other = tmp_path_factory.mktemp("outside")
    with pytest.raises(PathEscape):
        normalize_path(tmp_path, str(other / "x.py"))
