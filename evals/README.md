# FLOSSI0ULLK Eval Golden Sets

```yaml
# --- UpgradableArtifact Header ---
id: "evals-golden-sets"
version: "1.0.0"
kind: "eval_suite"
status: "Proposed"
updated: "2026-07-03"
supersedes: []
truth_status: "Specified"   # golden labels authored + machine-checked; ≥80% weaker-model agreement check pending
evidence_sources:
  - "FLOSS/docs/specs/knowledge-triple.spec.md v1.0.0"
  - "FLOSS/packages/orchestrator/claim_schema.py + consensus_gate.py (live code, 147/147 tests passing 2026-07-03)"
  - "FLOSS/docs/specs/provenance-packet.spec.md v1.4"
  - "2 real claims lifted from the local source chain (derived-from-repo items in claim_verification)"
generator: "claude-fable-5"
sprint: "FLOSS/docs/superpowers/plans/2026-07-03-fable5-sprint-handoff.md (WS1)"
upgrade_path: "add items via PR; bump minor per module extended; never edit heldout items in place — supersede them"
rollback_plan: "delete FLOSS/evals/ (self-contained directory)"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
friction_tier: "low"
```

## What this is

Versioned fitness functions for three modules. Every downstream optimization —
prompt sweeps (WS2), Pioneer fine-tunes (WS3), consensus-jury tuning, regression
detection — scores against these sets instead of vibes.

| Module | Dir | Items | Task under eval |
|---|---|---|---|
| KnowledgeTriple extraction | `knowledge_triple_extraction/` | 20 dev + 10 heldout | Text → spec-conformant triples (registered predicates, confidence bands, negation/hedge/dedup discipline) |
| Claim verification (voter) | `claim_verification/` | 20 dev + 10 heldout | Claim JSON → defect codes + vote bucket. The symbolic tally stays in `consensus_gate.tally()` — logic validates, neural assists |
| Provenance-packet validation | `provenance_packet_validation/` | 20 dev + 10 heldout | Packet + precomputed `crypto_facts` → valid/superseded/invalid + defect codes per spec v1.4 |

## File contract

Each module dir contains:

- `dev.jsonl` — development split. Optimizers may look at these.
- `heldout.jsonl` — **never shown to any optimizer** (prompt sweeps, GEPA, Pioneer
  training or adaptive inference). Grading eyes only. Violating this burns the split.
- `rubric.json` — self-contained: candidate task prompt, defect/predicate taxonomy,
  hard/soft grading criteria a *weaker* model can apply, scoring rule, success criterion.

Item schema (one JSON object per line):

```json
{"id": "…", "module": "…", "split": "dev|heldout",
 "input": {…}, "golden": {…}, "rationale": "why this golden is right",
 "provenance": {"generator": "claude-fable-5", "date": "2026-07-03",
                 "source": "synthetic|derived-from-repo"}}
```

Some items carry `golden.alt_golden` — a second acceptable answer where two
behaviors are defensible (graders accept either).

## How goldens were quality-controlled

Golden labels were authored by Fable 5 and then **machine-validated** by the
generator scripts (invariant checks in code, not by eye):

- KTE: INV-001/002/003/006/010 enforced on every golden triple (URI shapes,
  registered-predicate membership, confidence bands < 1.0, dedup).
- CV: defect codes closed over the taxonomy; bucket names closed over the bucket
  table; D-NONE items must carry non-empty, type-valid evidence.
- PPV: identifier shapes (E+43 / D+43 / 0B+86 / v 6-hex) generated
  programmatically to exact length; defect-vs-shape consistency cross-checked.

Generator scripts live in session scratchpad (not repo canon); the JSONL files
are the artifacts of record.

## Success criterion (per sprint packet)

A retained (non-frontier) model applying each rubric to a candidate sample must
agree with golden labels on **≥ 80%** of items. Below that, the rubric is
ambiguous — revise the rubric, not the model. Status: **pending** — this check
is the immediate next action after authoring; until it runs, this suite's
truth_status stays `Specified`.

## Running an eval (harness-agnostic sketch)

1. For each line in `dev.jsonl`: send `rubric.candidate_task_prompt` + `input`
   to the candidate model; collect JSON output.
2. For each candidate output: send `rubric.grading_rubric` + candidate output +
   `golden` (+ `alt_golden` if present) to the grader model; collect pass/fail
   per hard criterion.
3. Score = passed / total. Track per-module and per-defect-code confusion.
4. `heldout.jsonl` only for final acceptance runs — never inside an
   optimization loop.

## ToS note (WS3 boundary)

These items are Claude-origin. Using them to train/fine-tune **narrow
extractors/classifiers** (GLiNER/Qwen-class via Pioneer) sits inside Anthropic's
non-competing carve-out. Do **not** feed them into general-model fine-tuning or
any adaptive-inference loop that lacks provenance-tag filtering.
