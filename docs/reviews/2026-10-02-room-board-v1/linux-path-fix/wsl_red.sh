set -euo pipefail
SRC=/home/kalis/room-board-linux-20261006-MSAjEM
DST=/home/kalis/room-board-linux-claude-pathfix
PY=$SRC/venv/bin/python
BUNDLE="/mnt/c/Users/kalis/AppData/Local/Temp/claude/C---shit--claude-worktrees-coordination-room-a2a-board-52f403/65c498a8-9fc5-4cc9-b4dd-9d13f2820568/scratchpad/pathfix/red.bundle"
WT="/mnt/c/~shit/FLOSS/.worktrees/coordination-room-rebased"
test ! -e "$DST/red" || { echo "red clone exists"; exit 3; }
git clone -q -b feat/coordination-room-rebased "$BUNDLE" "$DST/red"
cd "$DST/red"
echo "linux clone at: $(git log --oneline -1)"
cp "$WT/packages/coordination_room/tests/test_path_separators.py" packages/coordination_room/tests/
git status --short
echo "== Linux RED: the test on the real head, no fix"
"$PY" -m pytest -q -p no:cacheprovider packages/coordination_room/tests/test_paths.py packages/coordination_room/tests/test_path_separators.py 2>&1 | grep -E "^(FAILED|ERROR)|^E  +(assert|Failed|packages)|passed|failed" || true
