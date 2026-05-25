---
name: flossi0ullk-orient
description: Use when starting work in the FLOSSI0ULLK workspace, re-orienting after context loss, or deciding which canonical docs and corpora to load first before deeper research or code changes.
---

# FLOSSI0ULLK Orientation

Use this skill to regain orientation without spraying tokens across the whole repo.

## Core workflow

1. Start with the canon:
   - `.agent-surface/context/CONTEXT_L0.md` when present for cheap re-orientation
   - `INDEX.md`
   - `FLOSS/CLAUDE.md`
   - `FLOSS/MVP_PLAN.md` when checking phase status or substrate progress
   - `FLOSS/SDD-Master-Spec-0.22.md` and `FLOSS/INSTRUCTIONS_FOR_CODE.md` when the task touches implementation order or evidence gates
   - `FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` when the task touches governing principles
2. Route the task through the shared context surface before loading deeper files:
   - `python FLOSS/scripts/context_router.py "<query>" --format markdown --limit 4`
3. Load `.agent-surface/context/CONTEXT_L1.md` when present if `L0` is not enough.
4. Open only the top-routed corpus roots.
5. Prefer current code, source-chain artifacts, and ADR-backed docs over stale summaries or `_reference/`.
6. If the task is about intake, filewatch, consolidation, or cross-agent update flow, load:
   - `FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`
   - `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`
   - `FLOSS/scripts/watch_intake.py`
   - `FLOSS/scripts/process_intake_events.py`

## Rules

- Treat `_reference/` as a last-resort published research library, not as the live canon.
- Disambiguate "MVP Phase 0" from "orchestration Phase 0": MVP Phase 0 substrate viability is complete per `MVP_PLAN.md`; the separate substrate-bridge validation remains specified in `FLOSS/docs/specs/phase0-substrate-bridge.spec.md`.
- If the task changes architecture or governance, read the relevant ADRs before editing.
- If the task changes code, use the routed skill or code corpus before opening broad directories.
- Treat `.agent-surface/events/*` as runtime queue state, not as canon.

## References

Open only what you need:

- `references/entry-points.md`
