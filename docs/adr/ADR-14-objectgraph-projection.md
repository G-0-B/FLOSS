# ADR-14: ObjectGraph Projection over Corpus (Typed Node-Level Retrieval)

## Status
Accepted (spike GO, evidence-gated to LATER for expansion)

## Date
2026-06-13 (formalizes `docs/superpowers/specs/2026-06-12-objectgraph-spike.md`, GO 2026-06-12)

## Truth Status
⚠️ Specified → ✅ Verified on landing (tests + live build). Pilot corpus only.

## Note
Retroactive ADR closing the governance gap for the objectgraph spike spec, which landed
without one (2026-06-13 review-bypass audit). The spike itself was human-gated
("GO per Anthony 2026-06-12, N6").

## Context

The existing `CONTEXT_L0`/`L1` emitter produces flat typed nodes at **document**
granularity with **zero edges**. Retrieval therefore costs whole documents. The
ObjectGraph paper (arXiv 2604.27820) describes progressive-disclosure traversal over a
typed node graph; its code was never released. An earlier audit (OVCA) that carried the
paper was **rejected (D1)**; only this single primitive was approved (D2,
"concept-not-import").

## Decision

Adopt a **concept-not-import** re-expression of ObjectGraph progressive disclosure over
FLOSSI0ULLK's own substrate, on **one pilot corpus** (`FLOSS/skill-corpus/`).

1. **Node granularity** — per-section nodes (heading-split), not per-document.
2. **Edges** — `contains` (doc→section), `next` (sibling order), `refs` (markdown links between corpus files).
3. **Progressive disclosure** — the index holds **summaries only**; full section text is
   fetched from source on demand (`--expand`). A query costs the subgraph, not the corpus.
4. **Symbolic-first** — deterministic keyword scoring only, no LLM in the loop (same posture
   as `context_router.py`). Rebuild is deterministic from sources.
5. **Non-canonical, read-only** — output is `.agent-surface/context/objectgraph/skill-corpus.json`,
   explicitly marked non-canonical; it **never feeds canon writes**.

Code of record: `scripts/objectgraph_spike.py`.

## Consequences

### Positive
- Cheaper retrieval (subgraph, not corpus) without adding a vector DB or LLM dependency.
- Preserves the "logic validates, neural assists" invariant — scoring is deterministic.

### Negative / Risks (probed first, per the resume gate)
- **Cross-node synthesis regression** — the paper's own eval loses on cross-node reasoning
  (77.9 vs 82.1 full-doc). Mitigation: when top hits spread across ≥3 documents with
  near-equal scores, `resolve` emits a synthesis-query advisory recommending full-doc reads.
- **Adversarial routing** — a poisoned node could steer retrieval. Mitigations: read-only +
  non-canonical + source paths always printed (verify at the artifact, not the index) +
  deterministic rebuild.

### Out of scope (LATER — each gated on pilot evidence)
- Other corpora (`architecture/`, `adr/`) — only after the pilot proves retrieval quality.
- DHT-backed node storage — Phase 1+.
- Embedding/LLM scoring — only if symbolic evidence demands it.

## References
- `docs/superpowers/specs/2026-06-12-objectgraph-spike.md`
- `scripts/objectgraph_spike.py`, `scripts/context_router.py`
- Decision lineage: OVCA audit D1 (reject) → D2 (concept-only approve) → N6 resume gate → GO 2026-06-12
