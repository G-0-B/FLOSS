# Yumeichan Heartbeat Bridge — Local Implementation Packet

**Date:** 2026-06-20  
**Audience:** Claude Code / local FLOSSI0ULLK implementation agent  
**Authoring context:** Generated from the Quests planning/cockpit session. This file is a handoff packet, not canon.

## 0. Intent

Build the first local implementation layer for **Yumeichan v0.1**, the always-on FLOSSI0ULLK meta-steward.

This is **not** full PC control. This is the safe, read-only / low-write foundation that lets Anthony see:

- whether the heartbeat is running, stopped, or degraded,
- why it is stopped,
- what the next safe actions are,
- what requires Anthony,
- what agents/harnesses should be used next,
- and what must not happen automatically.

The goal is to create a reliable local state surface that future Quests dashboards, OpenHuman capsules, Claude Code sessions, Gemini/Antigravity/Grok adapters, and the FLOSSI0ULLK heartbeat can all read.

---

## 1. Source authority

Before making changes, verify against the live local repo.

Authority order:

1. live repo / branch state,
2. current canonical docs/specs/ADRs,
3. working todo,
4. heartbeat/source-chain/activity logs,
5. uploaded/handoff/context-continuation packets,
6. conversation summaries,
7. this packet.

If this packet conflicts with live repo state, the repo wins. Report the conflict rather than blending claims.

---

## 2. Non-negotiable safety rules

### 2.1 STOP-file discipline

If a STOP file or equivalent stop condition exists:

- do **not** remove it automatically,
- do **not** dispatch agents,
- do **not** run autonomous write loops,
- do **not** edit canon,
- do **not** restart heartbeat blindly.

Instead, emit state showing:

```yaml
status: stopped
stop_file:
  present: true
  reason: "verified reason if discoverable, otherwise unknown"
needs_anthony:
  - "Approve removing STOP file or explain why it should remain."
```

### 2.2 Yumeichan v0.1 is read-only first

Allowed in v0.1:

- inspect heartbeat status,
- inspect git/repo status,
- inspect PR/check status if existing local tooling supports it,
- inspect working todo,
- inspect activity logs,
- inspect source-chain/consensus queues,
- emit a local Yumeichan state file,
- emit a local Yumeichan activity/status log,
- prepare task packets for other agents.

Blocked in v0.1 unless Anthony explicitly approves:

- merging PRs,
- pushing branches,
- editing canon / ADRs / specs,
- modifying substrate code,
- installing system packages,
- contacting external humans,
- spending money,
- ingesting raw OpenHuman/private memory,
- running unbounded autonomous loops,
- controlling desktop apps.

---

## 3. First deliverable

Create a local generated state artifact:

```text
.agent-surface/yumeichan/state.json
```

Optional human-readable mirror:

```text
.agent-surface/yumeichan/STATE.md
```

Append-only log:

```text
.agent-surface/yumeichan/activity.jsonl
```

If the repo already has a preferred generated surface convention, follow it instead and report the chosen path.

---

## 4. `state.json` schema v0.1

Implement a minimal state object with these fields:

```json
{
  "schema_version": "yumeichan-state-v0.1",
  "generated_at": "ISO-8601 timestamp",
  "status": "running | stopped | degraded | unknown",
  "confidence": "verified | specified | unknown",
  "heartbeat": {
    "status": "running | stopped | degraded | unknown",
    "last_tick": "ISO-8601 timestamp | null",
    "evidence": ["paths or observations used"]
  },
  "stop_file": {
    "present": true,
    "path": "relative path if known",
    "reason": "string | null",
    "evidence": ["paths or observations used"]
  },
  "repo": {
    "branch": "string | unknown",
    "dirty": true,
    "ahead_behind": "string | unknown",
    "open_prs": [
      {
        "id": "#38",
        "title": "string",
        "status": "open | merged | closed | unknown",
        "needs_human": true
      }
    ]
  },
  "now_queue": [
    {
      "id": "P0.1",
      "title": "Merge or verify PR #38",
      "owner": "Anthony",
      "risk": "medium",
      "status": "pending | active | blocked | done | unknown",
      "why": "Reconverges local/main before stacking new work."
    }
  ],
  "needs_anthony": [
    {
      "question": "Should the STOP file be removed?",
      "why": "Heartbeat dispatch must not resume without human confirmation.",
      "urgency": "high"
    }
  ],
  "safe_afk_actions": [
    "summarize status",
    "prepare task packets",
    "classify intake"
  ],
  "blocked_afk_actions": [
    "merge PRs",
    "edit canon",
    "contact external humans",
    "install packages",
    "ingest raw private memory"
  ],
  "recommended_next_action": {
    "title": "Inspect STOP reason and report restart condition",
    "owner": "Claude Code",
    "requires_human": true
  }
}
```

Keep v0.1 small. Add fields only if they are needed for current work.

---

## 5. Implementation plan

### Step 1 — Recon only

Inspect, do not mutate:

- heartbeat script/service status,
- STOP file or stop condition,
- working todo current NOW items,
- existing `.agent-surface` layout,
- git branch/dirty state,
- PR #38 status if accessible,
- recent activity/source-chain logs.

Report findings first.

### Step 2 — Create Yumeichan surface

Create the smallest additive implementation:

```text
.agent-surface/yumeichan/state.json
.agent-surface/yumeichan/activity.jsonl
```

If adding a script, prefer a small script in the existing scripts area, named along the lines of:

```text
scripts/yumeichan_state.py
```

or, if the repo already uses a different language/style for this layer, follow the repo convention.

### Step 3 — Implement collectors

Collector order:

1. `collect_stop_state()`
2. `collect_heartbeat_state()`
3. `collect_repo_state()`
4. `collect_todo_now_queue()`
5. `collect_pr_state()` if local tooling allows
6. `derive_safe_afk_actions()`
7. `derive_blocked_afk_actions()`
8. `derive_needs_anthony()`

Collectors should fail soft. Unknown is acceptable. Guessing is not.

### Step 4 — Emit state

Write `state.json` atomically if the repo has an atomic-write convention. Otherwise write normally but keep the script simple.

Append an activity line like:

```json
{"schema_version":"yumeichan-activity-v0.1","type":"state_emit","status":"stopped","generated_at":"...","summary":"STOP present; dispatch blocked pending Anthony."}
```

### Step 5 — Optional markdown mirror

Generate a short `STATE.md` for human reading:

```markdown
# Yumeichan State

Status: stopped
Reason: STOP file present
Needs Anthony:
- approve restart or keep STOP
NOW:
1. PR #38
2. ADR-15 PR-A
3. NLnet polish
```

### Step 6 — Do not wire dispatch yet

Do not create autonomous dispatch in this PR. v0.1 is status only.

Dispatch can be v0.2 after Anthony confirms the state packet is useful.

---

## 6. Current strategic NOW queue to encode

Use live repo state to verify, but the current planning session identified this order:

1. **PR #38** — merge/review/verify reconvergence PR.
2. **ADR-15 PR-A** — author/provenance binding enforcement only.
3. **Heartbeat/STOP** — diagnose and restore safely.
4. **Yumeichan v0.1 state packet** — this task.
5. **NLnet grant polish** — tone, cost lines, Anthony bio, endorsement ask, final review.
6. **Quests cockpit** — static/read-only first, later wired to `state.json`.
7. **OpenHuman context capsule** — consented projection only, never raw memory sync.

---

## 7. ADR-15 reminder

The next engineering thread after heartbeat/state is likely ADR-15 PR-A.

Scope split:

- **PR-A:** R1–R4 author/provenance binding enforcement.
- **PR-B:** R5 `i8` ternary to analog `f32 [-1,+1]` migration.

Do not mix these.

PR-A acceptance criteria:

- capture action author with pinned HDI/HDK API,
- validate relevant create paths,
- validate update paths if those entries can be updated,
- reject provenance mismatch unless delegated authority proof exists,
- tests for self-authored valid and mismatched invalid,
- human review and green tests before truth status becomes Verified.

---

## 8. Quests bridge note

Quests is currently the planning/cockpit surface used to generate this packet. It is sandboxed from the live local FLOSSI0ULLK runtime.

Recommended bridge pattern:

```text
local repo emits .agent-surface/yumeichan/state.json
Anthony uploads or exposes that state to Quests
Quests renders dashboard / helps synthesize next packets
Claude Code executes local changes
```

Do not assume Quests can directly control the local heartbeat.

---

## 9. Future v0.2 dispatch shape

After v0.1 is validated, add bounded dispatch templates:

```yaml
dispatch_templates:
  - id: summarize_prs
    risk: low
    allowed_while_afk: true
  - id: draft_task_packet
    risk: low
    allowed_while_afk: true
  - id: run_tests
    risk: medium
    allowed_while_afk: only_if_explicitly_enabled
  - id: create_branch_and_commit
    risk: high
    allowed_while_afk: false
  - id: merge_pr
    risk: high
    allowed_while_afk: false
```

Yumeichan should become capable slowly by earning each key.

---

## 10. Done criteria for this packet

This implementation packet is complete when:

- the live STOP/heartbeat state has been inspected,
- no STOP has been removed automatically,
- `state.json` exists or an equivalent repo-conventional state surface exists,
- the state reports NOW / needs-Anthony / safe-AFK / blocked-AFK,
- an append-only activity entry is written,
- Anthony can read the result and decide whether to proceed to v0.2.

---

## 11. One-line doctrine

**Yumeichan coordinates momentum; FLOSSI0ULLK governs authority; Anthony remains the consent root.**
