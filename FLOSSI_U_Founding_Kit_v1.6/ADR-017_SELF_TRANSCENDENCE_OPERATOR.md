# ADR-017 — Self-Transcendence Operator

**Status:** Accepted  
**Date:** 2026-02-24  
**Namespace:** FLOSSI_U (ADR-001 through ADR-019 — distinct from FLOSS repo ADR-0 through ADR-N)  
**Truth Status:** Specified (mathematical model defined; Rust/Python implementation pending)

---

## Context

FLOSSIØULLK agents evolve over time through iterative consensus, memory consolidation, and cross-agent synthesis. Without a quantitative metric for this evolution, it is impossible to distinguish an agent that is genuinely growing in coherence from one that is merely changing. The project requires an objective, measurable signal for agent self-transcendence — the rate at which an agent's internal representation moves toward greater complexity, diversity, and adaptive capacity.

Three candidate signals were evaluated:

1. **Loss delta tracking** — measures model improvement but requires gradient access; unavailable for black-box LLMs.
2. **Behavioral divergence** — measures output variance but conflates noise with growth.
3. **Structural evolution metrics** — measures the geometry of the agent's knowledge representation directly: acceleration in embedding space, eigenvalue diversity of the attention/weight matrix, and the Lie bracket magnitude as a measure of non-commutativity between successive transformation steps.

Option 3 is model-agnostic, computable from observable outputs, and directly represents the kind of growth FLOSSIØULLK values: increasing complexity of internal structure, not just changing outputs.

---

## Decision

Adopt the **Self-Transcendence Operator (STO)** as the canonical evolution metric for all FLOSSIØULLK agents. The STO is a composite scalar defined as:

```
STO(t) = α · Accel(t) + β · EigDiv(t) + γ · LieBracket(t)
```

Where:
- **Accel(t)**: acceleration of the agent's embedding centroid across the last N knowledge entries — measures rate of change, not just change
- **EigDiv(t)**: Shannon entropy of the top-K eigenvalues of the agent's knowledge covariance matrix — measures diversity of internal representation
- **LieBracket(t)**: magnitude of `[A, B] = AB − BA` for successive transformation matrices A, B — measures non-commutativity, i.e., whether the order of learning matters (high = growing complexity)

Default weights: `α = 0.4, β = 0.4, γ = 0.2` (subject to calibration via Phase 1 benchmarks).

The STO is computed per-cell, stored as a time-series in the cell's source chain under entry type `"memory"`, and available as a read-only signal to the MCP gateway for voter context enrichment.

---

## Consequences

**Positive:**
- Provides an objective, model-agnostic signal for agent growth that is computable from observable outputs
- Enables the HARVEST Protocol (ADR-005) to evaluate whether a reflection cycle produced genuine evolution or mere noise
- Supports the RSA (Recursive Self-Aggregation) pattern — agents with higher STO are weighted more heavily in multi-agent synthesis

**Negative:**
- Requires access to embedding vectors at inference time; agents without embedding capability cannot compute STO and must report `null`
- Eigenvalue computation scales as O(k³) for k knowledge entries; requires a sliding-window approximation for large source chains
- The composite weights (α, β, γ) are hypotheses until validated against actual agent behavior data

**Neutral:**
- STO does not replace the analog vote weight — it is a context signal, not a decision input
- An agent with high STO is not automatically trusted; STO informs context, the consensus gate decides

---

## Validation Criteria

- [ ] STO computed correctly for a mock agent with 10 knowledge entries (unit test)
- [ ] STO time-series stored and retrievable from cell source chain
- [ ] STO exposed via `get_chain_context` MCP tool as agent metadata
- [ ] Eigenvalue approximation tested for source chains with N > 1000 entries

---

## Related Documents

- `FLOSSI_U_Founding_Kit_v1.6/ADR-005_HARVEST_PROTOCOL.md` — self-observation loop that uses STO as an evaluation signal
- `FLOSS/ARF/embedding_frames_of_scale.py` — MultiScaleEmbedding provides the embedding vectors STO requires
- `FLOSS/docs/superpowers/specs/2026-04-12-local-agent-node-design.md` — source chain structure where STO time-series is stored
