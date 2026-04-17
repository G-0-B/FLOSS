---
name: flossi0ullk-orient
description: Use when starting work in the FLOSSI0ULLK workspace, re-orienting after context loss, or deciding which canonical docs and corpora to load first before deeper research or code changes.
---

# FLOSSI0ULLK Orientation

Use this skill to regain orientation without spraying tokens across the whole repo.

## Core workflow

1. Start with the canon:
   - `INDEX.md`
   - `FLOSS/CLAUDE.md`
   - `FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` when the task touches governing principles
2. Route the task through the shared context surface before loading deeper files:
   - `python FLOSS/scripts/context_router.py "<query>" --format markdown --limit 4`
3. Open only the top-routed corpus roots.
4. Prefer current code, source-chain artifacts, and ADR-backed docs over stale summaries or `_reference/`.

## Rules

- Treat `_reference/` as last-resort prior art.
- If the task changes architecture or governance, read the relevant ADRs before editing.
- If the task changes code, use the routed skill or code corpus before opening broad directories.

## References

Open only what you need:

- `references/entry-points.md`

