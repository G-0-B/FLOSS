# ADR-18: Prior-Art & Reuse Gate (before_build_check, enforced)

```yaml
adr: 18
title: "Prior-Art & Reuse Gate — adopt/extend/compose/build evidence, fail-closed"
decision_status: "Accepted (operator-approved 2026-07-16: shape B+C, 120-day window)"
truth_status: "Specified; --check enforcement Verified on landing"
friction: "Low (Tier 1: one JSON block) / Medium (Tier 2: adversarial review)"
date: "2026-07-16"
generator: "claude-fable-5"
supersedes: []
relates_to: ["ADR-4 (SDD)", "ADR-10 (consensus gateway)", "ADR-17 (open-review field convention)", "D7 spec_gate 2026-06-12"]
design_record: "C:/~shit/2026-07-16-prior-art-reuse-gate-design-proposal.md + 2026-07-16-prior-art-reuse-gate-continuation.md (root intake)"
```

## Context

The reuse principle ("search before building") existed in three unenforced forms: spec_gate (D7), SDD constitutional gates, and the `before_build_check` concept. PR38 demonstrated the cost of non-enforcement: a working bespoke preservation capsule built in territory plausibly covered by BagIt/OCFL/restic/in-toto. Repo history (ADR-1/RFC-001: KERI/AD4M/hREA built too early) shows this is a recurring failure mode, second only to doc-explosion.

## Decision

Unify and enforce, adding no new machinery:

1. **Evidence (Tier 1):** spec-registry entries may carry `"tier": 1|2`; tiered entries must carry a `reuse` block (schema: `docs/specs/reuse-gate.schema.json`) recording capability, dated search, candidates with per-claim truth status, an adopt→extend→compose→build verdict (adopt is default; burden of proof increases rightward), and a testable irreducible delta.
2. **Enforcement:** `spec_gate.py --check` fails closed on missing/stale/invalid blocks (120-day evidence window). Advisory (never-blocking) runtime path rides the existing `hook_post_write` → `advisory_note()` wiring.
3. **Review (Tier 2):** architecture-class work (needs-an-ADR heuristic) additionally requires adversarial reuse review via consensus-gateway voter profile `reuse-review` (Ollama gemma3-12b local/Google + Groq qwen3-32b/Alibaba + Mistral devstral — three surfaces, three families, none from the usual proposer families). `compose`/`build` verdicts require ≥1 direct probe; unprobed incompatibility claims cannot justify `build`.
4. **Emergency exception:** `"emergency": true` downgrades to a warning; the gate fires at promotion/generalization, never at preserve-first action.
5. **Guideline loop:** the search protocol and Reinvention Risk Register in `reuse-gate.spec.md` are ACON-style natural-language-optimizable guidelines; every gate miss becomes a failure trace that refines them.

## Consequences

- PR38/`salvage_spine` generalization is Tier 2 pending; blocking probe: restic on Windows (authorized, not yet run). Retrospective audit recorded as gate-miss trace #1 in the spec.
- The gate retires to a plain checklist if its falsifiers fire (<5 uses in ~6 months, verdict-changed rate ≈ 0, record cost >10% of implementation effort, or hook logs show search-first is already reliable).
- Prime directive preserved: the gate is symbolic validation (JSON + date arithmetic in spec_gate); LLM reviewers assist and dissent but do not decide — `--check` does.

## Compliance note

This ADR and the reuse-gate spec/schema are themselves registered in spec-registry.json; the spec carries the gate's own reuse block (verdict: `extend` — extending spec_gate rather than building new machinery).
