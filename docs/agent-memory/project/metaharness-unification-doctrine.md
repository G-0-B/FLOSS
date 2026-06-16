---
id: project-metaharness-unification-doctrine
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_metaharness_unification_doctrine.md
title: Build the unifier, not yet-another-harness — duplicated scaffolding IS the
  failure mode
legacy_description: User-named architectural pattern 2026-05-18 — FLOSSI0ULLK has
  8+ executable harnesses, each correct in isolation but each invented with different
  staging dir/activity-log/LLM-path/provenance conventions. The repeated work is the
  SCAFFOLDING, not the function. The fix is unification via shared conventions, NOT
  a new overseer class. Future agents proposing new harnesses must first check whether
  the work fits inside an existing harness with the unified Action schema (`FLOSS/packages/activity_log/`).
origin_session_id: a04c9df9-7bf3-4c48-8305-871bc29b680d
---

When the user expresses an architectural intuition like "we need an overarching metaharness overseer orchestrator centralized agent-centric thing," the correct response is **NOT to build a new overseer**. The literal version of that intuition would reproduce the failure mode being named — yet another script with yet another staging dir and yet another activity-log shape.

**The pattern as of 2026-05-18:**
- 8+ executable harnesses live under `FLOSS/scripts/` and `FLOSS/packages/` (heartbeat, poll_high_roi_actions, autonomous_synthesis_loop, harvest_reuse_ledger, watch_intake, process_intake_events, router, synthesizer, …)
- Each works in isolation
- Each invented with different staging convention, different activity-log shape (or none), different LLM call path (consensus gateway / LiteLLM direct / Gemini CLI subprocess / Ollama HTTP), different provenance pattern
- The duplicated work is the SCAFFOLDING around each harness, not the function each performs
- This is the same shape as the `project_doc_explosion_acknowledged.md` failure pattern, but at the executable layer instead of the document layer

**Canonical reference doc:** `FLOSS/docs/research/2026-05-18-metaharness-unification.md`

**Three unification abstractions (per the doc §3):**
1. **Atomic interface:** shared `Action` dataclass (`FLOSS/packages/activity_log/schema.py`). Every agentic action across any harness emits one record in this shape.
2. **Holistic surface:** single canonical activity log at `.agent-surface/activity.jsonl`. Per-subsystem logs (`.agent-surface/heartbeat/ticks.log`, `.agent-surface/harvest/activity.jsonl`, `.agent-surface/reasoning/activity.jsonl`) stay as debugging projections; the global log is the canonical write target.
3. **Routing convention:** every LLM call goes through `router.classify()` first to select pass_through / single_strong / ensemble mode. Existing scripts that bypass the Router (autonomous_synthesis_loop's direct LiteLLM call, harvest_reuse_ledger's Gemini-CLI subprocess) are refactor candidates per the migration path.

**How to apply going forward:**
- **Before proposing a new harness/script**, check whether the work fits inside an existing harness PLUS shared schema. The default answer is "extend existing, don't create new."
- **When writing a new harness IS justified** (genuine new function), the harness MUST: (a) import `from FLOSS.packages.activity_log import Action, append_action`, (b) emit one Action per logical unit of work, (c) route LLM calls through the Router (or document why not), (d) place drafts in `.agent-surface/<task>/staging/<id>_<descriptor>_draft.<ext>` with paired `_provenance.json` sidecar.
- **When refactoring an existing harness**, the refactor steps in the unification doc §4 are additive (each script keeps its current behavior + adds the global activity log tee). Plane A discipline preserved — no forced rewrites.
- **Anti-pattern guard:** "We need a centralized agent-centric orchestrator" → reframe as "We need the existing harnesses to conform to a shared atomic interface." The centralized P5-violating shape is the wrong answer to a real problem.

**Connection to existing canon:**
- `FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md` (the abstract six-harness composition: Canon/Context/Execution/Consensus/Reflection/Publish) — the unification is the implementation layer under that operating model
- `2026-05-17-inline-reasoning-ensemble.md` — the Router pattern at the atomic primitive; the metaharness unification extends Router-as-gate from Claude session prompts to all script LLM calls
- ADR-Suite v2.0 §13 governance-gap backlog — the unified Action schema enforces Spine v0.5 §7 provenance-per-action by construction rather than by convention
- `project_metaharness_doctrine.md` — the six-harness DOCTRINE; this new memory is the operational discipline under that doctrine

**Open promotion path:** the unification + Inline Reasoning Ensemble together are the candidate ADR-14 content. Pilot for 7 days collecting global activity log data → consensus claim through Layer 4.5 gateway → ADR promotion. Don't promote prematurely; the 7-day data is the evidence gate.
