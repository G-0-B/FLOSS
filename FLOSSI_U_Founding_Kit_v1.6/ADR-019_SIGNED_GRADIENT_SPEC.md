# ADR-019 — Signed Gradient Specification

**Status:** Accepted
**Date:** February 24 2026

**Context:** The Knowledge Triple schema originally used confidence [0,1]; corrected to signed floats -1.0 to +1.0.

**Decision:** Formally update Knowledge Triple confidence to signed gradient.
All triples must have confidence in [-1.0, +1.0]. Negative values indicate movement away from desired state; positive toward desired state.

**NOTE — EXTERNAL INTERFACE CONSTRAINTS:**
The following fields CANNOT use signed gradients due to external standard conformance:
- `impact` (ThoughtCredential) — magnitude metric [0,1], negative has no semantic meaning
- `remaining_ru` (BudgetEntry) — quantity [0,100], not a gradient
- Embedding dimensions — size constraints determined by external ML models
- Holochain Timestamp — external SDK type, immutable

See `docs/specs/TERNARY_COMPATIBILITY.md` in the FLOSS repo for the full compatibility map.

**Consequences:**
- Enables directional feedback.
- Integrates with ONEDIM engine and Dancing Decision.
- Signed Confidence: +1.0
- Provenance: User correction, this thread
