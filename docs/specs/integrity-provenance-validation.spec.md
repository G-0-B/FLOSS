# Spec: Integrity Zome Provenance & Authorization Validation

**Status:** ✅ Verified — the R2-R4 integrity validators are implemented and unit-tested at
this head. ⚠️ Specified — the two-agent Tryorama validation and R5 analog migration remain.
**Severity:** P1 — security / core-invariant
**Backs:** ADR-15
**Date:** 2026-06-13

## Problem

A 2026-06-07 Semgrep scan (HIGH, true-positive) plus direct code review found missing
authorship/provenance binding in the `rose_forest` integrity zome — the layer the project's
"logic validates, neural assists" and `provenance_first` non-negotiables depend on. The
follow-on implementation has this status:

1. ✅ **Verified — `BudgetEntry` deterministic validation is implemented and unit-tested.**
   `validate` threads each Create or Update action's own author and timestamp through
   `validate_app_entry` into `validate_budget_entry`. The validator binds `agent` to the action
   author, requires finite non-negative `remaining_ru`, accepts equality at the exact 300-second
   future-skew boundary, rejects one microsecond beyond it, and fails closed if constructing the
   boundary would overflow.
2. ✅ **Verified — `ThoughtCredential.provenance` is author-bound and unit-tested.**
   Evidence: `validate_thought_credential`, `thought_rejects_provenance_mismatch`, and
   `thought_accepts_self_authored`.
3. ✅ **Verified — `KnowledgeTriple.source` is author-bound and unit-tested.**
   Evidence: `validate_knowledge_triple`, `triple_rejects_source_mismatch`, and
   `triple_accepts_self_authored`. `KnowledgeEdge` has no author/provenance field and is outside
   the current author-binding rule.
4. ⚠️ **Specified — connotation analog migration remains unimplemented.** `connotation` is
   currently validated as integer ternary `(-1..=1)` rather than the analog `[-1.0, +1.0]`
   model adopted in ADR-10 v2.0 and required by ADR-13.
5. ⚠️ **Specified — two-agent Tryorama validation remains unimplemented.** Unit tests establish
   validator behavior, but do not yet demonstrate that agent A cannot publish an entry attributed
   to agent B through a running conductor.

The independent Lovable synthesis (2026-06-13) reached the same conclusion from the architecture
side: *"permeability without capability gates is just a hole"* (ROI item 14 / Play 5).

This is the exact failure the symbolic-first architecture exists to prevent: truth being
asserted without verifiable provenance. ✅ The current Verified claim is bounded to the
implemented validators and their unit-test evidence; ⚠️ end-to-end multi-agent enforcement
remains Specified until the Tryorama gate passes.

## Decision / Validation Rules

✅ **R1 — Author binding (general).** For every current entry type carrying an identity field
(`agent` / `provenance` / author-of-record), `validate()` MUST extract the action author
and reject the op unless that field equals the author. This is implemented for `BudgetEntry`,
`ThoughtCredential`, and `KnowledgeTriple`.

✅ **R2 — BudgetEntry.** `entry.agent == action.author`; `remaining_ru` is finite and `>= 0.0`;
`window_start <= action_timestamp + 300 seconds (5 minutes)`. The validator receives the
deterministic Create or Update action timestamp, not wall-clock time. `validate_budget_entry`
implements the rule with `BUDGET_ENTRY_FUTURE_SKEW_SECONDS`, and fails closed when
`Timestamp::checked_add` overflows.

✅ **R3 — ThoughtCredential.** `credential.provenance == action.author`. Keep existing
dimension/impact range checks.

✅ **R4 — KnowledgeTriple.** `triple.source == action.author`. `KnowledgeEdge` has no
provenance/author field and is outside this rule.

⚠️ **R5 — Connotation analog migration (linked, may land separately).** Migrate `connotation`
from integer ternary to `f32` clamped `[-1.0, +1.0]` to match ADR-10/ADR-13. Flag: this is a
data-model change with migration implications; it remains Specified and must be gated behind
its own test pass.

## Implementation evidence

✅ `validate` handles both `OpEntry::CreateEntry` and `OpEntry::UpdateEntry` and passes each
action's `author` and `timestamp` to `validate_app_entry`. This confirms the pinned
`hdi = 0.7.1` field access in compiled code.

✅ `validate_app_entry` dispatches identity-bearing entries to
`validate_budget_entry`, `validate_thought_credential`, and `validate_knowledge_triple`.

✅ `validate_budget_entry` checks author binding first, then finite/non-negative balance, then
the deterministic future-skew boundary using
`Timestamp::checked_add(Duration::from_secs(BUDGET_ENTRY_FUTURE_SKEW_SECONDS))`.

## Test evidence and remaining gates

- ✅ **Verified — BudgetEntry unit evidence:** `budget_rejects_author_mismatch`,
  `budget_accepts_self_authored`, `budget_rejects_negative_balance`,
  `budget_rejects_nan_balance`, `budget_rejects_infinite_balance`,
  `budget_accepts_window_start_at_future_skew_boundary`,
  `budget_rejects_window_start_one_microsecond_beyond_future_skew_boundary`, and
  `budget_rejects_when_future_skew_boundary_overflows`.
- ✅ **Verified — author-binding unit evidence:** `thought_rejects_provenance_mismatch`,
  `thought_accepts_self_authored`, `triple_rejects_source_mismatch`, and
  `triple_accepts_self_authored`.
- ⚠️ **Specified — Tryorama gate:** two agents; agent A cannot publish an entry attributed to
  agent B.
- ⚠️ **Specified — R5 migration gate:** analog connotation representation, migration behavior,
  and boundary tests must land in a separate reviewed change.

## Process note

✅ The current Rust implementation is evidenced by integrity-crate unit tests. Per the standing
anti-sycophancy / review discipline surfaced in the 2026-06-13 audit, future validation-core
changes must continue to land through focused tests, the integrity-crate suite, and human review.
⚠️ The missing two-agent Tryorama gate and R5 migration remain separate reviewable work.
