# ADR-15: Enforce Author–Provenance Binding in the Integrity Zome

## Status
Accepted (fix specified; implementation P1, cargo-test-gated)

## Date
2026-06-13

## Truth Status
⚠️ Specified — decision made; integrity-zome code change not yet implemented or tested.
Until the code lands and passes tests, provenance enforcement is **aspirational in code**
despite being a core invariant in doctrine.

## Context

The project's non-negotiables include `provenance_first` and "logic validates, neural assists —
truth is established by symbolic validation in Holochain integrity zomes, which cannot be
bypassed." A 2026-06-07 Semgrep scan (two HIGH true-positives) and direct review of
`ARF/dnas/rose_forest/zomes/integrity/src/lib.rs` found the integrity zome does **not** actually
enforce that an entry's identity field (`agent`, `provenance`) matches the action's author:

- `BudgetEntry` validation is an unconditional `Ok(Valid)`.
- `ThoughtCredential` provenance is never bound to the author.
- `KnowledgeEdge`/`KnowledgeTriple` provenance is unenforced.

The independent Lovable synthesis (2026-06-13) flagged the same gap architecturally:
"permeability without capability gates is just a hole."

This is a contradiction between **doctrine** (`provenance_first`, ✅-able verification) and
**code** (no author binding). Per truth-status discipline, the contradiction must be resolved in
favor of the code: until fixed, provenance claims resting on this zome are not Verified.

## Decision

The integrity zome **will enforce author–provenance binding** for every entry type that carries
an identity field, rejecting any op where the field ≠ the action author. Detailed rules and the
implementation sketch live in `docs/specs/integrity-provenance-validation.spec.md` (R1–R5).

The connotation field will migrate from integer ternary to analog `f32 [-1.0, +1.0]` to remove
the drift against ADR-10/ADR-13 (R5), gated behind its own test pass as it is a data-model change.

The Rust change lands via a reviewed PR with `cargo test` green — not an unreviewed agent edit.

## Consequences

### Positive
- Closes the gap between the `provenance_first` invariant and the actual validator.
- Makes ADR-13's Yumeichan-watch security model real (it depends on `ThoughtCredential` provenance).
- Removes a HIGH-severity finding; unblocks honest `✅ Verified` provenance claims.

### Negative / Risks
- R5 (ternary→analog) is a breaking data-model change; existing `ThoughtCredential` data and the
  38 ontology tests may need migration/update.
- Author-accessor API must be confirmed against `hdi 0.7.1` (tripwire T6: no 0.5-era patterns).
- Adds validation cost per op (negligible vs. the integrity benefit).

## References
- `docs/specs/integrity-provenance-validation.spec.md`
- `Semgrep_Code_Combined_Findings_2026_06_07.csv` (findings 813527874, 813527875)
- ADR-10 (analog vote model), ADR-12 (Consent Gate), ADR-13 (Yumeichan Watch — depends on this)
- Lovable Grand Synthesis 2026-06-13, ROI item 14 / Play 5
