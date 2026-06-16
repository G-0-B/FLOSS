---
id: project-itmd-shipped-parallel-session
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_itmd_shipped_parallel_session.md
title: ITMD (idle-time metaharness driver) shipped via parallel Claude session
legacy_description: A parallel Claude session designed + course-corrected + shipped
  working heartbeat.py and heartbeat_slate.py in FLOSS/scripts/ around 2026-05-07.
  The session ran the ancestry-sweep + doc-budget patterns autonomously. Two root
  .md drops from that session (idle-time-metaharness-driver-v0.1.md, strategic-context-memo-ecosystem-signals-v0.1.md)
  are explicitly intake-material-that-served-its-purpose, not new canon.
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

A parallel Claude session, working ~2026-05-07, designed and shipped an idle-time metaharness driver (ITMD) without this main session's involvement. Key facts to load when relevant:

## What shipped
- `FLOSS/scripts/heartbeat.py` — scheduler that subprocess-invokes existing scripts in rotation; STOP-file check; per-script cost ceiling; updates `RESUMPTION.md`
- `FLOSS/scripts/heartbeat_slate.py` — dynamic-slate generator that replaces hardcoded list in `poll_high_roi_actions.py` with one assembled from real backlog sources
- `.agent-surface/heartbeat/` — runtime state (daily_state.json, next_slate.json, ticks.log) confirms the loop is running
- STOP gate: `.agent-surface/heartbeat/STOP` halts within one heartbeat cycle

## What was *not* shipped (and why)
- The 24KB `idle-time-metaharness-driver-v0.1.md` spec at workspace root was explicitly self-superseded by the parallel session as a doc-explosion violation of the just-added CLAUDE.md doc-budget rule. **Treat that file as intake material that served its purpose, not new canon.** Disposition per the parallel session: extract a short heartbeat section into `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`, then archive the standalone spec
- `strategic-context-memo-ecosystem-signals-v0.1.md` at root is related intake from the same parallel session; same disposition logic applies after content review
- The parallel session refused to silently patch `poll_high_roi_actions.py` to read `next_slate.json` — left it as an explicit decision point requiring user authorization

## Meta-positive signal — patterns self-propagating
The parallel session **autonomously ran the ancestry-sweep pattern** before I codified it: discovered `poll_high_roi_actions.py` already existed, refused to rebuild, noted the doc-budget rule on its own, ran the universal-flourishing test honestly ("substrate-enabling, not directly advancing"). This is empirical evidence the new CLAUDE.md conventions are working at the workflow level across parallel sessions, not just in the session where they were written.

## How to apply
- Don't redesign idle-compute/metacoordination from scratch — the loop exists and is running
- When updating the cull triage, mark `idle-time-metaharness-driver-v0.1.md` as ARCHIVE-with-note (superseded by code, not canon)
- The hook system (`hook_post_write.py` → `hook_bg_round.py`) is the event-driven coordination layer; ITMD is the idle-compute layer; both run independently
- Phase 0 priority is the runtime invariant that outranks ITMD's own usefulness — if work generation drifts from Rose Forest compile / Tryorama / ConversationMemory↔MultiScaleEmbedding, the loop is doing the wrong thing well
