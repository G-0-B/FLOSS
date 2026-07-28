# ADR-15: Enforce Author–Provenance Binding in the Integrity Zome

## Status
Accepted — ✅ Verified at unit level: R2–R4 implemented and tested; ⚠️
Specified/deferred: two-agent conductor/Tryorama enforcement and R5.

## Date
2026-06-13

## Truth Status
✅ Verified — R2–R4 are implemented in
`ARF/dnas/rose_forest/zomes/integrity/src/lib.rs` and pass the integrity-crate unit tests:

- R2: `validate_budget_entry`; `budget_rejects_author_mismatch`,
  `budget_accepts_self_authored`, `budget_rejects_negative_balance`,
  `budget_rejects_nan_balance`, `budget_rejects_infinite_balance`,
  `budget_accepts_window_start_at_future_skew_boundary`,
  `budget_rejects_window_start_one_microsecond_beyond_future_skew_boundary`, and
  `budget_rejects_when_future_skew_boundary_overflows`.
- R3: `validate_thought_credential`; `thought_rejects_provenance_mismatch` and
  `thought_accepts_self_authored`.
- R4: `validate_knowledge_triple`; `triple_rejects_source_mismatch` and
  `triple_accepts_self_authored`.

⚠️ Specified — the two-agent conductor/Tryorama enforcement proof and R5 analog
data-model migration remain deferred. The unit evidence above does not establish complete
runtime, conductor, or cross-agent enforcement.

## Context

The project's non-negotiables include `provenance_first` and "logic validates, neural assists —
truth is established by symbolic validation in Holochain integrity zomes, which cannot be
bypassed." A 2026-06-07 Semgrep scan (two HIGH true-positives) and direct review of
`ARF/dnas/rose_forest/zomes/integrity/src/lib.rs` found that the integrity zome at that time did
**not** enforce that an entry's identity field (`agent`, `provenance`) matched the action's
author:

- `BudgetEntry` validation was an unconditional `Ok(Valid)`.
- `ThoughtCredential` provenance was not bound to the author.
- `KnowledgeTriple` provenance was unenforced; `KnowledgeEdge` has no author/provenance field
  and is outside the current author-binding rule.

The independent Lovable synthesis (2026-06-13) flagged the same gap architecturally:
"permeability without capability gates is just a hole."

This was a contradiction between **doctrine** (`provenance_first`, ✅-able verification) and
**code** (no author binding). ✅ Verified — R2–R4 now resolve that contradiction at the validator
unit-test level. ⚠️ Specified — provenance claims requiring running-conductor or cross-agent
enforcement remain unverified until the two-agent Tryorama gate passes.

## Decision

⚠️ Specified — the accepted general decision is that the integrity zome **will enforce
author–provenance binding** for every entry type that carries an identity field, rejecting any
op where the field ≠ the action author. Detailed rules live in
`docs/specs/integrity-provenance-validation.spec.md` (R1–R5).

✅ Verified — R2–R4 implement and unit-test that decision for `BudgetEntry`,
`ThoughtCredential`, and `KnowledgeTriple`.

⚠️ Specified — the two-agent conductor/Tryorama enforcement proof remains a separate gate; unit
tests do not establish complete runtime or cross-agent enforcement.

⚠️ Specified — the connotation field will migrate from integer ternary to analog
`f32 [-1.0, +1.0]` to remove the drift against ADR-10/ADR-13 (R5), gated behind its own test pass
as it is a data-model change.

## Consequences

### Positive
- ✅ Verified — R2–R4 reject mismatched author/provenance in focused validator unit tests.
- ✅ Verified — ADR-15 now names traceable validator and unit-test evidence instead of retaining
  the stale “unimplemented and untested” status.
- ⚠️ Specified — runtime and cross-agent provenance claims remain gated on the two-agent
  conductor/Tryorama proof.

### Negative / Risks
- ⚠️ Specified — R5 (ternary→analog) is a breaking data-model change; existing
  `ThoughtCredential` data and ontology tests may need migration/update.
- ✅ Verified — current action-author and action-timestamp access compiles against the pinned
  `hdi 0.7.1` in the passing integrity-crate unit-test command.
- ⚠️ Specified — validation adds per-op cost; runtime cost has not been measured.

## References
- `docs/specs/integrity-provenance-validation.spec.md`
- `Semgrep_Code_Combined_Findings_2026_06_07.csv` (findings 813527874, 813527875)
- ADR-10 (analog vote model), ADR-12 (Consent Gate), ADR-13 (Yumeichan Watch — depends on this)
- Lovable Grand Synthesis 2026-06-13, ROI item 14 / Play 5
