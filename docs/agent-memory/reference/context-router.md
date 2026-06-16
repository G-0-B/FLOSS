---
id: reference-context-router
type: reference
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: reference_context_router.md
title: Context router for cheap re-orientation
legacy_description: FLOSS/scripts/context_router.py ranks canon/architecture/skills/code/etc
  by query keywords — use it before opening directories
origin_session_id: 567c823f-3cba-4d75-866d-600bd4286e6f
---

The FLOSSI0ULLK workspace has a working context-routing tool that returns ranked corpus roots for a query, defined by `shared-context-surface.json`.

**How to invoke:**
```bash
python FLOSS/scripts/context_router.py "<query>" --format markdown --limit 4
```

Returns scored corpora (canon, architecture, skills, code, serena-memory, source-chain, traces, research, reference) with matched roots. Cheaper than opening directories blind.

**When to use:**
- After any context loss or session compaction.
- When the task is unclear and you need to find the right corpus root.
- Before opening broad `FLOSS/docs/` subtrees — route first, then retrieve inside the chosen corpus.

**Companion files:**
- `.agent-surface/context/CONTEXT_L0.md` — cheapest briefing; load first when present
- `.agent-surface/context/CONTEXT_L1.md` — load when L0 isn't enough
- `FLOSS/scripts/watch_intake.py` + `FLOSS/scripts/process_intake_events.py` — filewatch + consolidation skeleton (see `docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`)

**Rule from the metaharness doctrine:** route corpus first, then retrieve inside the chosen corpus. Don't open `_reference/` or `FLOSS/docs/` blindly.
