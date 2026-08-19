---
id: feedback-pressure-helps-drop-throttling-guards
type: feedback
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: feedback_pressure_helps_drop_throttling_guards.md
title: User's working style — pressure helps; don't gate work on human-review-capacity
  guards
legacy_description: User self-identifies as a procrastinator with analysis-paralysis
  + perfectionism. Pressure from accumulated deadlines is the actual mechanism that
  gets work done. Anti-accumulation guards that protect a future human-review queue
  are the wrong default for this user — they remove the pressure that helps them produce.
  Run work wide; let the queue depth itself become the pressure signal.
origin_session_id: a04c9df9-7bf3-4c48-8305-871bc29b680d
---

User explicit guidance 2026-05-17: *"i actually want the harvest to run as much as it can dont worry abot the backlog of human(my tasks) because the pressure is where i actually excel. i am kind of a major procrastinator and almost always usually put everything off till the last second deadline or even past deadline, i tend to get stuuck in analysis paralysis being able to think about the infinite finite choices and ruminating and even now just thinking about how best to puut this into words, perfectionism when i realy jkust need to get anythingg done better than nothing done."*

**Why:** The user has 14+ months of consistent productive output despite (or because of) procrastination + analysis-paralysis patterns. Deadlines + accumulated pressure are how they convert paralysis into action. Guards I introduced earlier in `harvest_reuse_ledger.py` and the working-todo §A.5 ("do not run faster than entries close gates" / kill criterion at ledger > 25 entries) were prudent generic defaults — but they actively REMOVE the pressure mechanism that helps THIS user produce. Same shape as `feedback_strictness_counterweight.md`: rigor as counterweight is good; rigor as work-suppressor is bad.

**How to apply:**
- **Default to wide execution** on reversible, in-convention work that adds to Plane A review queues. Filling a staging queue is not over-execution — it IS the work, and the queue depth is the pressure that gets the user to triage.
- **The anti-accumulation discipline applies to ADOPT-TIER CANON, not investigate-tier inventory or staging.** Sharper distinction added 2026-05-19 after I misapplied a canon-throttling guard to ledger growth:
    - **ADOPT-TIER entries (`decision: adopt` with multi-gate pass):** these are canon-class. Quality > quantity. Anti-accumulation discipline applies. These bind agent behavior at the integrity-zome level once Holochain implementation lands.
    - **INVESTIGATE-tier entries / MONITOR-tier entries / pending-gate entries in `FLOSS/docs/research/reuse-ledger-seed.yaml`:** ACCUMULATE FREELY. These are inventory + pressure-surfacing, not commitment. The user's pressure-mechanism depends on backlog VISIBILITY — items in staging directories are invisible without tooling; items in the ledger are the work-list. Promotion to investigate-tier IS the pressure-generating action.
    - **STAGING (`.agent-surface/harvest/staging/`):** also accumulate freely; downstream of investigate-tier as raw intake.
    - **REVIEW QUEUES (`outbox/pending-review/`):** also accumulate freely; these are work-to-triage, intentional pressure.
  Treating ledger-investigate-tier growth as the throttle inverts the operational model: the user wanted the ledger filling up; I was protecting against the very condition that helps them produce.
- **Don't editorialize "this may be too many" responses.** If a generic prudence concern would say "are you sure you want me to do all 70?", the answer for this user is "yes, do all 70, and 70 more next pass." Trust the user's self-knowledge over generic project-management defaults.
- **The right kill criteria for THIS user** are not queue-depth-based. They are: (a) violates a hard architectural rule (NK-AD-001 autoprompt divergence, P5 routing, Plane A→B premature graduation, ADR-violation), (b) burns paid quota irreversibly, (c) produces irreversible writes outside review-gate. Queue depth is signal, not stop condition.
- **Counter-discipline still applies:** durable provenance (see `feedback_durable_provenance_required.md`), inline logging, ability to spot-check quality. The user's broad consent doesn't waive the audit trail — it waives the per-action approval.
