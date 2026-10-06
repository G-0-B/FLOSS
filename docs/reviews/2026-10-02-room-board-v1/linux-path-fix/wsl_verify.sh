set -euo pipefail
SRC=/home/kalis/room-board-linux-20261006-MSAjEM
DST=/home/kalis/room-board-linux-claude-pathfix
PY=$SRC/venv/bin/python
test ! -e "$DST" || { echo "DST exists, refusing to reuse"; exit 3; }
mkdir -p "$DST/out" "$DST/runtime/agent" "$DST/runtime/audit" "$DST/runtime/room" "$DST/runtime/tmp"
git clone -q "$SRC/head" "$DST/head"
cd "$DST/head"
echo "clone at: $(git log --oneline -1)"

"$PY" - <<'PY'
import pathlib
q = chr(34) * 3
test = f'''{q}One file has one claim key on every platform, however its separators are written.

Found by the first Linux run of this package (2026-10-06). On POSIX a backslash
is an ordinary filename character, so a path written with backslashes and the
same path written with slashes were two keys: two agents could each hold "the
same file", and a dot-dot written with a backslash was accepted as a file name
inside the root.

Production change that would make these fail: treating a backslash as part of
a name, instead of as a separator, on any platform.
{q}

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
    assert normalize_path(tmp_path, f"a{{BACKSLASH}}b/c.py") == "a/b/c.py"


def test_backslash_dotdot_escape_is_rejected(tmp_path: Path):
    with pytest.raises(PathEscape):
        normalize_path(tmp_path, f"..{{BACKSLASH}}secret.txt")


def test_one_file_written_two_ways_has_one_holder(tmp_path: Path):
    room = CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")
    assert room.claim("windows-agent", f"packages{{BACKSLASH}}foo.py")["path"] == "packages/foo.py"
    with pytest.raises(ClaimConflict):
        room.claim("linux-agent", "packages/foo.py")


def test_a_file_ref_resolves_with_either_separator(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "x.md").write_text("x", encoding="utf-8")
    assert resolve_ref(tmp_path, f"file:docs{{BACKSLASH}}x.md")["ok"] is True
    assert resolve_ref(tmp_path, "file:docs/x.md")["ok"] is True
'''
pathlib.Path("packages/coordination_room/tests/test_path_separators.py").write_text(test, encoding="utf-8", newline="\n")
PY

T="packages/coordination_room/tests/test_paths.py packages/coordination_room/tests/test_path_separators.py"
echo "== RED (before the fix)"
"$PY" -m pytest -q -p no:cacheprovider $T 2>&1 | grep -E "^(FAILED|ERROR)|passed|failed" || true

"$PY" - <<'PY'
import pathlib
BS = chr(92)
p = pathlib.Path("packages/coordination_room/paths.py")
t = p.read_text(encoding="utf-8")
old = "    raw = Path(path.strip())\n"
new = (
    "    # A backslash is a separator here on every platform, as it already is on\n"
    "    # Windows. On POSIX it is otherwise an ordinary filename character, which\n"
    f"    # made `a{BS}b.py` and `a/b.py` two claim keys for one file.\n"
    f"    raw = Path(path.strip().replace(\"{BS}{BS}\", \"/\"))\n"
)
assert t.count(old) == 1
p.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
PY

echo "== GREEN (after the fix)"
"$PY" -m pytest -q -p no:cacheprovider $T 2>&1 | tail -1
echo "== room package"
"$PY" -m pytest -q -p no:cacheprovider packages/coordination_room/tests 2>&1 | tail -1

echo "== required green set"
unset PYTHONPATH COORDINATION_ROOM_BOARD
export PYTHONDONTWRITEBYTECODE=1 FLOSS_AGENT_DIR=$DST/runtime/agent FLOSS_AUDIT_DIR=$DST/runtime/audit FLOSS_MCP_AUDIT_DIR=$DST/runtime/audit
export COORDINATION_ROOM_ROOT=$DST/runtime/room COORDINATION_ROOM_LOG=$DST/runtime/room/events.jsonl TMPDIR=$DST/runtime/tmp
set +e
"$PY" -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ \
  --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded \
  --junitxml="$DST/out/fix.xml" > "$DST/out/fix.txt" 2>&1
echo "pytest exit: $?"
set -e
tail -1 "$DST/out/fix.txt"

"$PY" - "$SRC/receipts/head.xml" "$DST/out/fix.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
from collections import Counter
def cases(path):
    out = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        marks = [c.tag for c in tc if c.tag in ("failure", "error", "skipped")]
        out[tc.get("classname") + "::" + tc.get("name")] = marks[0] if marks else "passed"
    return out
head, fix = cases(sys.argv[1]), cases(sys.argv[2])
print("codex head:", dict(Counter(head.values())), "| with fix:", dict(Counter(fix.values())))
print("changed outcomes:", {k: (head[k], fix[k]) for k in head if k in fix and head[k] != fix[k]})
print("missing with fix:", [k for k in head if k not in fix])
print("new with fix:", {k: fix[k] for k in fix if k not in head})
PY
echo "== checkout state"
git status --short
git diff
