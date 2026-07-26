# Spec: Integrity Zome Provenance & Authorization Validation

**Status:** ⚠️ Specified (fix not yet implemented or tested)
**Severity:** P1 — security / core-invariant
**Backs:** ADR-15
**Date:** 2026-06-13

## Problem

A 2026-06-07 Semgrep scan (HIGH, true-positive) plus direct code review found that the
`rose_forest` integrity zome — the layer the project's "logic validates, neural assists"
and `provenance_first` non-negotiables depend on — **does not enforce authorship/provenance
binding.** Confirmed in `ARF/dnas/rose_forest/zomes/integrity/src/lib.rs`:

1. **`BudgetEntry` needs complete deterministic action-time validation** — its contract must bind
   `agent` to the action author, require a finite non-negative `remaining_ru`, and reject a
   `window_start` more than **300 seconds (5 minutes)** after the deterministic action timestamp.
   This rule is ⚠️ Specified until the Rust task supplies test evidence.
2. **`ThoughtCredential.provenance` is not bound to the author** — `validate_thought_credential`
   checks content dimension, connotation, and impact ranges, but never verifies
   `credential.provenance == <action author>`. The code comment admits it ("Further validation
   could include checking provenance signature"). Any agent can publish a credential attributed
   to another agent.
3. **`KnowledgeTriple.source` is author-bound.** `KnowledgeEdge` has no author/provenance field
   and is outside the current author-binding rule; it must not be described as though it carried
   provenance requiring this comparison.
4. **Connotation drift** — `connotation` is validated as **integer ternary** `(-1..=1)`, which
   contradicts the analog `[-1.0, +1.0]` model adopted in ADR-10 v2.0 and required by ADR-13.

The independent Lovable synthesis (2026-06-13) reached the same conclusion from the architecture
side: *"permeability without capability gates is just a hole"* (ROI item 14 / Play 5).

This is the exact failure the symbolic-first architecture exists to prevent: truth being
asserted without verifiable provenance. Until fixed, **no `✅ Verified` provenance claim that
relies on the integrity zome is accurate.**

## Decision / Validation Rules

**R1 — Author binding (general).** For every entry type carrying an identity field
(`agent` / `provenance` / author-of-record), `validate()` MUST extract the action author
and reject the op unless that field equals the author.

**R2 — BudgetEntry.** `entry.agent == action.author`; `remaining_ru` is finite and `>= 0.0`;
`window_start <= action_timestamp + 300 seconds (5 minutes)`. The validator receives the
deterministic action timestamp, not wall-clock time. ⚠️ Specified until the Rust task supplies
test evidence.

**R3 — ThoughtCredential.** `credential.provenance == action.author`. Keep existing
dimension/impact range checks.

**R4 — KnowledgeTriple.** `triple.source == action.author`. `KnowledgeEdge` has no
provenance/author field and is outside this rule.

**R5 — Connotation analog migration (linked, may land separately).** Migrate `connotation`
from integer ternary to `f32` clamped `[-1.0, +1.0]` to match ADR-10/ADR-13. Flag: this is a
data-model change with migration implications; gate behind its own test pass.

## Implementation sketch (verify against `hdi = 0.7.1`)

In `validate()`, the `OpEntry::CreateEntry { app_entry, action }` /
`UpdateEntry { app_entry, action }` variants carry the `EntryCreationAction`; obtain the author
via its `.author()` accessor and thread it into each `validate_*` helper:

```rust
OpEntry::CreateEntry { app_entry, action } => {
    let author = action.author;
    match app_entry {
        EntryTypes::BudgetEntry(b)        => validate_budget_entry(&b, &author, action.timestamp()),
        EntryTypes::ThoughtCredential(c)  => validate_thought_credential(&c, &author),
        EntryTypes::KnowledgeTriple(t)    => validate_knowledge_triple(&t, &author),
        // ...
    }
}
OpEntry::UpdateEntry { app_entry, action, .. } => {
    let author = action.author;
    match app_entry {
        EntryTypes::BudgetEntry(b)        => validate_budget_entry(&b, &author, action.timestamp()),
        EntryTypes::ThoughtCredential(c)  => validate_thought_credential(&c, &author),
        EntryTypes::KnowledgeTriple(t)    => validate_knowledge_triple(&t, &author),
        // ...
    }
}
```
⚠️ The exact author accessor on `EntryCreationAction` must be confirmed against hdi 0.7.1
(the repo's pinned version) — do not lift a 0.5-era pattern (tripwire T6).

The `validate_budget_entry` sketch accepts `action_timestamp` as its third argument. It
must use that deterministic timestamp (not wall-clock time) to reject a `window_start` more
than 300 seconds (5 minutes) in the future, and must reject non-finite or negative balances.
This remains ⚠️ Specified pending the protected Rust task's tests.

## Test plan (gate before any `Verified` claim)

- Unit test: a `ThoughtCredential` with `provenance != author` → `Invalid`.
- Unit test: a `BudgetEntry` with `agent != author`, non-finite/negative balance, or a
  `window_start` more than 300 seconds after the deterministic action timestamp → `Invalid`;
  legitimate self-authored entries within the window → `Valid`.
- Unit test: legitimate author-bound entries still `Valid` (no regression on existing 38 ontology tests).
- Tryorama: two agents; agent A cannot publish an entry attributed to agent B.

## Process note

This fix touches the validation core. Per the standing anti-sycophancy / review discipline
surfaced in the 2026-06-13 audit, the Rust change must land via `cargo test` + human review —
**not** an unreviewed agent edit. This spec is the reviewable unit; the code PR implements it.
