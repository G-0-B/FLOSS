# ObjectGraph Spike — typed node-level projection over skill-corpus (N6)

```yaml
id: "2026-06-12-objectgraph-spike"
status: "Spike — GO per Anthony 2026-06-12 (N6); prerequisites N1-N3 met"
truth_status: "Specified -> Verified on landing (tests + live build)"
decision_lineage: "OVCA audit D2 (concept-not-import, 2026-06-09) -> D5 spike paused -> N6 resume gate -> GO 2026-06-12"
code: "FLOSS/scripts/objectgraph_spike.py"
output: ".agent-surface/context/objectgraph/skill-corpus.json (non-canonical projection)"
pilot_corpus: "FLOSS/skill-corpus/ (one corpus only, per N6)"
```

## What this is (and is not)

A **concept-not-import** re-expression of ObjectGraph progressive-disclosure
traversal (arXiv 2604.27820) over FLOSSI0ULLK's own substrate. Nothing from the
paper's code is imported (none was released). The OVCA report that carried it
was REJECTED (D1); this primitive alone was approved (D2).

Per the N2 materializer analysis: the existing CONTEXT_L0/L1 emitter already
produces flat typed nodes at **document** granularity with **zero edges**. This
spike generalizes exactly the two missing dimensions, on one pilot corpus:

1. **Node granularity** — per-section nodes (heading-split), not per-document.
2. **Edges** — `contains` (doc→section), `next` (sibling order), `refs`
   (markdown links between corpus files).

Index holds **summaries only**; full section text is fetched from the source
file on demand (`--expand`). That is the progressive disclosure: a query costs
the subgraph, not the corpus.

## Known risks, probed first (per the resume gate)

- **Risk 1 — cross-node synthesis regression.** The ObjectGraph paper's own
  eval loses on cross-node reasoning (77.9 vs 82.1 full-doc). Mitigation built
  in: when top hits spread across ≥3 documents with near-equal scores, `resolve`
  emits a synthesis-query advisory recommending full-doc reads of the listed
  files instead of node-level assembly.
- **Risk 2 — adversarial routing.** A poisoned node could steer retrieval.
  Mitigations: the projection is read-only and marked non-canonical; it never
  feeds canon writes; source paths are always printed so a reader verifies at
  the artifact, not the index; rebuild is deterministic from sources (no LLM in
  the loop — keyword scoring only, same posture as context_router.py).

## Out of scope (LATER, each gated on spike evidence)

- Other corpora (architecture/, adr/) — only after the pilot proves retrieval
  quality on skill-corpus.
- DHT-backed node storage (the "typed projection over DHT" target) — Phase 1+.
- Embedding/LLM scoring — symbolic-first; keyword scoring until evidence says
  otherwise.
- Edge types beyond contains/next/refs.

## Success criteria

- Deterministic, idempotent build (re-run on unchanged sources writes nothing).
- Node count > document count (section granularity real).
- `resolve` answers a known-answer query (e.g. "token budget" → orient SKILL
  budget section) with correct provenance path.
- Synthesis advisory fires on a deliberately broad query.
- Tests green; spec-gate green with the script registered.
