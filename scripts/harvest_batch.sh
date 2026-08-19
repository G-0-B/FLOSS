#!/usr/bin/env bash
# Reuse-Ledger Harvest Batch Runner
#
# Drives FLOSS/scripts/harvest_reuse_ledger.py against a long list of fork URLs
# sequentially. Failure-tolerant: one bad fork doesn't stop the batch.
# Writes activity events to .agent-surface/harvest/activity.jsonl via the
# inner script — which is the durable cross-agent provenance trail.
#
# Designed for background execution. Tail the activity log to watch progress:
#   tail -f .agent-surface/harvest/activity.jsonl | jq .
#
# Anti-accumulation guard: REMOVED. Per user instruction 2026-05-17, pressure
# on the human-review queue is desired, not avoided. Promotion to canonical
# ledger remains human-gated; staging queue depth is unrestricted.

set -u

WORKSPACE="C:/~shit"
PY="C:/Python313/python.exe"
HARVESTER="${WORKSPACE}/FLOSS/scripts/harvest_reuse_ledger.py"
ACTIVITY_LOG="${WORKSPACE}/.agent-surface/harvest/activity.jsonl"

# Pace between invocations. Pro tier is ~60 RPM. We run at ~1/min with the
# inner script taking ~60s anyway, so this is mostly defensive.
INTER_INVOCATION_SLEEP_SECONDS="${INTER_INVOCATION_SLEEP_SECONDS:-5}"

# Model override propagates to the inner script via env.
export FLOSS_HARVEST_GEMINI_MODEL="${FLOSS_HARVEST_GEMINI_MODEL:-gemini-3.1-pro-preview}"

batch_id="batch-$(date -u +%Y%m%dT%H%M%SZ)"
total=0
ok=0
fail=0

log_batch_event() {
  local event="$1"
  local extra="$2"
  python3 -c "
import json, sys
from datetime import datetime, timezone
with open(r'${ACTIVITY_LOG}', 'a', encoding='utf-8') as f:
    entry = {'timestamp': datetime.now(timezone.utc).isoformat(),
             'event': '${event}', 'batch_id': '${batch_id}'}
    entry.update(${extra:-\{\}})
    f.write(json.dumps(entry) + '\n')
" 2>/dev/null || true
}

log_batch_event "batch_start" "{'model': '${FLOSS_HARVEST_GEMINI_MODEL}', 'target_count': $#}"

for url in "$@"; do
  total=$((total + 1))
  echo "===== [${total}] $url ====="
  # Capture rc BEFORE the tail pipe — pipefail-style without globally enabling
  # pipefail which can break other tooling.
  "$PY" "$HARVESTER" "$url" > /tmp/harvest_invocation_${total}.out 2>&1
  rc=$?
  tail -3 /tmp/harvest_invocation_${total}.out
  if [ "$rc" -eq 0 ]; then
    ok=$((ok + 1))
  else
    fail=$((fail + 1))
    echo "WARN: harvest failed for $url (exit=$rc); continuing batch"
  fi
  rm -f /tmp/harvest_invocation_${total}.out
  sleep "$INTER_INVOCATION_SLEEP_SECONDS"
done

log_batch_event "batch_end" "{'total': $total, 'ok': $ok, 'fail': $fail}"
echo ""
echo "===== BATCH DONE: ${ok}/${total} succeeded, ${fail} failed ====="
echo "Activity log: ${ACTIVITY_LOG}"
echo "Staging dir:  ${WORKSPACE}/.agent-surface/harvest/staging/"
