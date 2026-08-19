# Ternary/Signed Gradient Compatibility Map

**Date:** 2026-03-31
**Status:** Specified

FLOSSI0ULLK uses ternary logic (-1/0/+1) and signed gradients [-1.0, +1.0] as the native value orientation. This document maps where ternary ranges apply and where external constraints prevent adoption.

---

## Ternary-Native Fields ([-1.0, +1.0])

| Field | Type | Entry Type | Notes |
|-------|------|-----------|-------|
| `confidence` | `f32` | KnowledgeTriple | Signed gradient: -1.0 = actively false, 0 = unknown, +1.0 = verified |
| `confidence` | `f32` | KnowledgeEdge | Same semantics as Triple confidence |
| `connotation` | `i8` | ThoughtCredential | Discrete ternary: -1 (negative), 0 (neutral), +1 (positive) |
| `cosine_similarity` | `f32` | SearchResult (score) | Mathematical property of cosine, naturally [-1, 1] |

## Cannot Be Ternary (flagged)

| Field | Type | Entry Type | Reason |
|-------|------|-----------|--------|
| `impact` | `f32` | ThoughtCredential | **Magnitude metric** [0, 1]. "How much impact" has no negative direction. Negative impact is a connotation concern, not an impact-amount concern. Would require semantic redesign. |
| `remaining_ru` | `f32` | BudgetEntry | **Quantity** [0, 100]. Resource units are a count, not a gradient. Negative budget has no meaning in the consumption model. |
| `embedding` dimensions | `usize` | RoseNode, ThoughtCredential | **Size constraint** [32, 4096]. Array length is a positive integer. |
| `embedding` values | `f32[]` | RoseNode, ThoughtCredential | **Unconstrained floats**. Embedding values are determined by external ML models (sentence-transformers, etc.) and naturally span arbitrary ranges. No constraint to change. |
| Holochain `Timestamp` | `(i64, u32)` | All entry types | **External SDK type**. Seconds + nanoseconds since epoch. Cannot modify. |
| msgpack wire format | bytes | Conductor protocol | **External standard**. Serialization is range-agnostic. No constraint exists here to change. |

## Design Rationale

The signed gradient aligns with:

- **Yumeichan Ternary Connotation Framework** (ADR-002 in FLOSSI U): emotional valence as -/0/+
- **Dancing Epistemology** (ADR-016 in FLOSSI U): decisions as directional movement
- **Voluntary Convergence Manifesto**: convergence and divergence as symmetric operations
- **Cosine similarity**: the mathematical foundation already lives in [-1, 1]

The key insight: `confidence: -0.8` on a `contradicts` predicate means "I'm fairly confident this contradiction holds" — the negative confidence indicates *directional certainty away from the object*, not uncertainty.
