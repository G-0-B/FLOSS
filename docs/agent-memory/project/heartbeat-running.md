---
id: project-heartbeat-running
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_heartbeat_running.md
title: Heartbeat loop is budget-gated; diverse-max is no longer routine
legacy_description: Supersedes the 2026-05-12/17 memory that described routine
  diverse-max heartbeat polling. As of 2026-05-19, STOP is present after a token
  burn diagnosis; routine polling defaults to balanced, wide sweeps default to
  a 72-tick cadence, unchanged slates are skipped, and autonomous synthesis is
  capped by staged draft depth.
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

## Current posture

The heartbeat service exists, but the runtime is intentionally paused when
`C:\~shit\.agent-surface\heartbeat\STOP` exists. On 2026-05-19, the STOP file
was created after diagnosing real Groq token bleed:

- `.agent-surface/heartbeat/daily_state.json` showed `175/40` consensus rounds
  for 2026-05-19.
- `FLOSS/docs/knowledge_log/staging/` had 112 synthesis drafts waiting.
- The old `heartbeat` voter-profile alias resolved to `diverse-max`, and the
  heartbeat comment promised no-change skips that were not implemented yet.

Do not remove the STOP file just to "get the heartbeat running" again. First
check `FLOSS/docs/architecture/RUNTIME_SURFACES.md` and
`FLOSS/docs/specs/heartbeat-runtime-budget.spec.md`.

## Current rotation

Each tick still rotates through the same broad work classes, but only the cheap
local items are unconditional:

1. `process_intake_events.py` drains filewatch queue state.
2. `heartbeat_slate.py` regenerates the high-ROI slate.
3. `poll_high_roi_actions.py --profile balanced` runs only when the daily cap,
   slate-signature gate, and STOP gate all pass.
4. `autonomous_synthesis_loop.py --model groq/llama-3.3-70b-versatile --limit 3`
   runs only when staged draft count is below `FLOSS_SYNTHESIS_STAGING_CAP`.

## Budget policy

| Setting | Current default | Why |
|---|---|---|
| `FLOSS_HEARTBEAT_PROFILE` | `balanced` | Routine checks should not burn max diversity. |
| `FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS` | `72` | At 10-minute ticks, `diverse-max` can only appear about every 12 hours by default. |
| `FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS` | `72` | Unchanged slates reconfirm about twice daily, not every tick. |
| `FLOSS_DAILY_ROUND_CAP` | `40` | Eight five-candidate polls/day unless deliberately overridden. |
| `FLOSS_SYNTHESIS_STAGING_CAP` | `25` | Don't spend Groq creating more drafts while review is already backed up. |

To halt the loop: `New-Item -Path C:\~shit\.agent-surface\heartbeat\STOP -Force` — halts within one tick (~10 min).
To resume: delete the STOP file.

## How to apply going forward

- Treat `diverse-max` as intentional spend, not background health checking.
- If a voter rate-limits during a real claim, check whether heartbeat has been
  resumed without the runtime-budget spec still matching code.
- The working operator guide is `FLOSS/docs/architecture/RUNTIME_SURFACES.md`.
- The executable budget contract is
  `FLOSS/docs/specs/heartbeat-runtime-budget.spec.md` plus
  `FLOSS/scripts/tests/test_heartbeat_budget.py`.
