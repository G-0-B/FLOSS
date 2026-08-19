---
id: project-consolidation-pending
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_consolidation_pending.md
title: Major discovery + documentation consolidation pass pending
legacy_description: After the local agent node commit lands, the next large effort
  is consolidating ~2 years of disparate prior research and architecture work scattered
  across the workspace.
origin_session_id: 7a8fdf1c-cf5f-4d01-a344-82a0dec070b6
---

After the 2026-04-12 local agent node commit (096b058), the user's declared next major effort is a **discovery + documentation consolidation pass** over approximately 2 years of prior research, architecture designs, and AI-collaborative building — much of it scattered, partially forgotten, or only encoded in conversations that were lost to context resets.

Why: The user has been researching and imagining architecture for this project across many sessions and many collaborators. A lot of it exists only as fragments in `_reference/` (2300+ files), under `FLOSS/docs/`, in ADR stubs, and in the `FLOSSI_U_Founding_Kit_v1.6/` directory. Without consolidation, each new session re-derives context from scratch and duplicates prior thinking.

How to apply:
- When consolidation work starts, expect breadth over depth in the first sweep: inventory what exists, where, and what it claims to be. Don't try to unify everything in one pass.
- Favor the existing conventions: ADRs in `FLOSS/docs/adr/`, specs in `FLOSS/docs/specs/` or `FLOSS/docs/superpowers/specs/`, INDEX.md as the canonical registry, `FLOSS/archive/` for superseded files (never delete).
- Treat `INDEX.md` and ADR cross-links as the primary artifacts of consolidation — they are how a future reset-self will rediscover this work.
- The user is likely to be the bottleneck on semantic decisions (what's canonical vs. superseded, what was a dead end vs. a pinned future direction). Surface those as explicit questions rather than guessing.
- Do not start this work without an explicit go-ahead. The commit that closes out the gateway session does not authorize starting the consolidation pass.
