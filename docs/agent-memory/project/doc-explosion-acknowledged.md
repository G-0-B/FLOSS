---
id: project-doc-explosion-acknowledged
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_doc_explosion_acknowledged.md
title: Doc-explosion pattern acknowledged + aggressive cull approved
legacy_description: User has self-named the cross-iteration pattern (massive doc mountains
  + scope creep before code ships) and approved aggressive culling of current state.
  Updates the consolidation-pending memory with concrete approval.
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

User explicitly acknowledged on 2026-05-10 that the doc-explosion pattern is bigger than they realized and approved aggressive culling. Direct quote: "yea might need a bit more aggressive culling of this even more insane overgrowth than i realized. I saw it and knew it was there but just ignored it and kept reepeating it."

**Why:** Code-level audit of `amazon_rose_forest` (1st iteration) and `amazon_rose_forest_01` (2nd iteration) showed the pattern is reproducing in current `FLOSS/` at the largest scale yet — `docs/architecture/` 31 files, `docs/research/` 51 files, `docs/adr/` 10+, 30+ root intake `.md`, 3GB ai-conversations corpus. Findings landed in `FLOSS/docs/research/2026-05-09-ad4m-coasys-audit-delta.md` §K.

**How to apply:**
- Cull triage in progress at `FLOSS/docs/research/2026-05-10-doc-cull-triage-v1.md` (when written) — categorizes existing docs as Keep / Update / Archive / Dispose
- New docs from this point forward must justify themselves against universal-flourishing north star + length budgets
- Ancestry sweep (per `FLOSS/docs/governance/ancestry-sweep-v1.0.md`) prevents the from-scratch-restart trigger that historically initiates doc explosions
- Personal meta-harness (`FLOSS/docs/governance/personal-meta-harness-v1.0.md`) carries the length-budget discipline at the cognition layer
- Default position when in doubt: don't add a doc; update an existing one or accept that the thought is durable enough not to need a doc
