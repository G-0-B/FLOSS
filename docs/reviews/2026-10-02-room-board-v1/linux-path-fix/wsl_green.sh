set -euo pipefail
SRC=/home/kalis/room-board-linux-20261006-MSAjEM
DST=/home/kalis/room-board-linux-claude-pathfix
PY=$SRC/venv/bin/python
BUNDLE="/mnt/c/Users/kalis/AppData/Local/Temp/claude/C---shit--claude-worktrees-coordination-room-a2a-board-52f403/65c498a8-9fc5-4cc9-b4dd-9d13f2820568/scratchpad/pathfix/green.bundle"
test ! -e "$DST/green" || { echo "green clone exists"; exit 3; }
git clone -q -b feat/coordination-room-rebased "$BUNDLE" "$DST/green"
cd "$DST/green"
echo "linux clone at: $(git rev-parse HEAD)"
echo "status before: [$(git status --porcelain)]"
R=$DST/runtime-green; mkdir -p $R/agent $R/audit $R/room $R/tmp $DST/out
unset PYTHONPATH COORDINATION_ROOM_BOARD
export PYTHONDONTWRITEBYTECODE=1 FLOSS_AGENT_DIR=$R/agent FLOSS_AUDIT_DIR=$R/audit FLOSS_MCP_AUDIT_DIR=$R/audit
export COORDINATION_ROOM_ROOT=$R/room COORDINATION_ROOM_LOG=$R/room/events.jsonl TMPDIR=$R/tmp
set +e
"$PY" -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ \
  --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded \
  --junitxml="$DST/out/committed.xml" > "$DST/out/committed.txt" 2>&1
echo "pytest exit: $?"
set -e
tail -1 "$DST/out/committed.txt"
echo "status after: [$(git status --porcelain)]"
"$PY" - "$SRC/receipts/base.xml" "$SRC/receipts/head.xml" "$DST/out/committed.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
from collections import Counter
def cases(path):
    out = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        marks = [c.tag for c in tc if c.tag in ("failure", "error", "skipped")]
        out[tc.get("classname") + "::" + tc.get("name")] = marks[0] if marks else "passed"
    return out
base, head, fix = (cases(p) for p in sys.argv[1:4])
print("codex base:", dict(Counter(base.values())))
print("codex head:", dict(Counter(head.values())))
print("committed fix:", dict(Counter(fix.values())))
print("vs head, changed outcomes:", {k: (head[k], fix[k]) for k in head if k in fix and head[k] != fix[k]})
print("vs head, missing:", [k for k in head if k not in fix])
print("vs head, new:", {k: fix[k] for k in fix if k not in head})
print("vs base, regressed:", [k for k in base if base[k] == "passed" and fix.get(k) != "passed"])
print("failing now:", [k for k, v in fix.items() if v in ("failure", "error")])
PY
"$PY" scripts/spec_gate.py --check 2>&1 | grep -c "SPEC-GATE MISSING\|SPEC-GATE STALE" || true
