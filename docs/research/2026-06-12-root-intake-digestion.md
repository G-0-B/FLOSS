# 2026-06-12 Root Intake Digestion Map

```yaml
id: "2026-06-12-root-intake-digestion"
status: "Relocated raw intake; classification complete; distillation pending"
truth_status:
  relocation: "Verified (pre/post-move sha256 checkpoints match, 17 files + 1 directory)"
  classification: "Specified (15 parallel classifier agents, 2026-06-12)"
  canon_promotion: "Not performed"
move_log: ".agent-surface/intake/root-intake-moves-2026-06-12.json"
raw_holding_area: "FLOSS/docs/research/intake_raw/2026-06-12-root/"
companion_record: "N-queue closure (Ember seed pack file 01 §5), recorded in §4 below"
```

## What changed

A root-intake digestion pass classified and relocated 17 loose files plus the
`mcps/` directory from the workspace root into a dated raw holding area:

- `FLOSS/docs/research/intake_raw/2026-06-12-root/reports/` (8 files)
- `FLOSS/docs/research/intake_raw/2026-06-12-root/reference/` (8 files + mcps snapshot, 60 files)
- `FLOSS/docs/research/intake_raw/2026-06-12-root/vision/` (1 file)

All moves are hash-recorded (pre-move checkpoint, post-move verification) in
`.agent-surface/intake/root-intake-moves-2026-06-12.json`. Three opaque
filenames were renamed for findability (`BASEDPROper.md`, `plate.md`, and the
two PDFs' Unicode punctuation normalized); the ledger records every rename.

**Intentionally left at root (live artifacts):** the Ember seed pack
(`00_MASTER_SEED.md`, files 01/02/03/05, `ember_seed_pack_v1_0_0.zip`,
`SHA256SUMS`) — its install-order steps 3–4 are still in flight — and
`FLOSSI0ULLK_Context_Continuation_Packet_2026-06-09.md` (active continuation
packet; supersede at next session boundary per its own upgrade path).
Config surfaces (`.claude/launch.json`, `.serena/`) are session/tooling state,
not intake.

## Classification verdicts (15 classifiers, parallel pass)

| File (destination) | Kind | Vintage | Truth | Keeper insight |
|---|---|---|---|---|
| `reports/flossioullk_REVISED_…` + `_old_…` pair | report | 2026-04 / 2025 | U | REVISED supersedes old; OSAID 1.0 terminology discipline + "bounded openness" asymptotic reading of the project name |
| `reports/warp_Log_6-8-26.md` | log | 2026-06-08 | U | Transcript wrapper; deliverables already canonical in the two 2026-06-08 research docs — do not re-distill |
| `reports/Automated Agent Orchestration…` | report | 2026-04 | U | Holochain validation-as-alignment corroboration; MCP supply-chain threat data for ADR-10. **NEVER-flag** (see below) |
| `reports/Cryptographically Verifiable Context Artifacts…` (OVCA) | report | 2026-06 | U | **REJECTED as integration target per seed-pack file 01 D1**; D2 approved 3 primitives concept-not-import; kept as evaluated-and-rejected provenance record |
| `reports/automating-flossioullk.md` | report | 2025-12 | U | Unit-of-autonomy decision (signed entry + validation rules); integrity-zome "law churn" discipline. Soft **NEVER-flag** |
| `reports/human_ai_co-evolution.md` | report | 2025-12 | U | Vaccaro/Almaatouq/Malone 2024 meta-analysis + neuro-symbolic ranking = external corroboration for the prime directive |
| `reports/context_continuation_orient_skill_handoff_v1_0_0.md` | seed (consumed) | 2026-06-09 | V | Consumed 2026-06-11 (orient v0.2.0 landing); byte-identical twin of seed-pack file 05 |
| `reference/pieces-export-p1-p5-kernel-metrics-2026-03-02.md` (was BASEDPROper.md) | reference | 2026-03 | S | P1–P5 operationalization metrics + Compatible/Degraded/Incompatible labels — absorb into `resonance_mechanism_v2.md` §0.5 |
| `reference/FLOSSI0ULLK_Knowledge_Interchange_v2.0.md` | reference | 2026-03 | U | KnowledgeTriple→RDF 1.2 provenance upgrade path; RICE-as-SHACL idea. Codebase claims describe prior iterations. **NEVER-flag** |
| `reference/FLOSSI0ULLK_Verified_Foundations_v0.1.md` | reference | 2026-02 | S | Critch bounded-Löb (arXiv 1602.04184) as formal grounding for "logic validates, neural assists" — one canonical citation home would consolidate three loose references |
| `reference/FLOSSIOULLK_ADRs_ALL_v1.0.0.md` | reference | 2026-02 | A | Fully superseded by ADR-Suite v2.0; do not resolve bare ADR numbers against it; ADR-0009 governance organs + ADR-0000 upgrade/rollback convention are the salvage |
| `reference/{query-routing-flow,vector-db-components}.mermaid` | duplicate/ref | rose_forest era | S | Flowchart is verbatim-recoverable from the Amazon_Rose_Forest repomix doc; Layer-2 routing pattern only if Phase 2+ reactivates it |
| `reference/Full-Stack-Alignment_…pdf` | reference | 2025 | U | Thick-models-of-value = scholarly support for structured value representation over free-text; cite into HOLISTIC_ARCHITECTURE / CCES L5 |
| `reference/Internet-Voting-Maturity-Framework_…pdf` | reference | 2026-03 | U | Trust-assumption enumeration method maps onto truth-status discipline; election machinery mostly does not transfer to ADR-10's agent-consensus model |
| `reference/mcps-tool-schema-snapshot-2026-06-05/` (60 files) | reference | 2026-06-05 | V | Tool-surface drift baseline; `submit_claim.json` embeds gateway thresholds — cross-check against ADR-10 text; server is source of truth |
| `vision/axioms-of-immanence-flowith-2026-01-19.md` (was plate.md) | vision | 2026-01 | A | Single-shot Flowith manifesto; do not canonize its physics claims; at most a one-line cross-ref in CCES vision material |

## NEVER-list flags (filter at distillation time)

1. **Automated Agent Orchestration** — recommends Tendermint/CometBFT for "governance votes, audit logs, token transactions"; endorses token-weighted/quadratic on-chain voting; Fetch.ai FET token case study.
2. **Knowledge_Interchange v2.0** — recommends OriginTrail DKG (TRAC-token-incentivized) as a core integration pathway and Phase 1 roadmap item.
3. **OVCA report** — flags Web3 "Incentivized Symbiosis" as a next-iteration resource; SCP log-proportional revenue model is incentive-adjacent.
4. **automating-flossioullk** — Holo-REA bounty/credit/"RiskUnits" mechanics brush the token-incentives pillar (soft collision; REA accounting, not literal tokens).

None of these block holding the documents; all block uncritical distillation.

## Priority queue: next highest-value distillations

1. **Critch bounded-Löb citation consolidation** (Verified_Foundations → one citation home in HOLISTIC_ARCHITECTURE or ADR-Suite rationale; three loose references collapse to one).
2. **P1–P5 metrics + three-tier labels** (pieces-export → `resonance_mechanism_v2.md` §0.5; smallest concrete edit with new measurable content).
3. **MCP supply-chain threat data** (Agent Orchestration → ADR-10 / local-agent-node security posture; treat every tool response as untrusted input).
4. **mcps snapshot threshold cross-check** (submit_claim.json blast-radius thresholds vs ADR-10 text; server wins on conflict).
5. **OSAID 1.0 terminology + license-stack delta** (REVISED deep-research → ADR-7 territory; record only the delta).
6. **Vaccaro meta-analysis + cognitive-debt citations** (human_ai_co-evolution → METAHARNESS_OPERATING_MODEL / personal-meta-harness evidence sections).

Per doc-budget discipline every item above lands in an EXISTING doc.

## §4 — N-queue closure record (Ember seed pack file 01 §5, executed 2026-06-12)

| N | Outcome |
|---|---|
| **N1** | ✅ Script-layer inventory folded into `INDEX.md` (new "Metaharness Script Layer" section; live tree = 31 scripts vs the packet's 20; additions reconciled). No new doc. |
| **N2** | ✅ Closed via materializer analysis: `CONTEXT_L0/L1` are script-generated projections of `FLOSS/shared-context-surface.json` (19 sources, per-document typed nodes, content-diffed writes, no mtime bump on no-op). ObjectGraph-spike notes: emission is already a flat typed-node projection at document granularity, zero edges, corpus roots parallel-but-disjoint — the spike would generalize `extract_markdown_view` into per-type projections plus edges. Spike resume (N6) remains gated. |
| **N3** | ✅ `poll_high_roi_actions.py` CLI default flipped `balanced` → `diverse` (4 provider surfaces / 6 model families, meets the ≥3-surface/≥4-family policy). Heartbeat spend unaffected — `heartbeat.py` always pins `--profile` explicitly (env default `balanced` per `heartbeat-runtime-budget.spec.md`, unchanged). `balanced` (2 surfaces / 3 families) confirmed NOT diversity-compliant — risk (i) closed by routing, not by roster growth. |
| **N4** | ✅ Pair merged: `triage_review_queue.py`'s unique orphan/size/area analysis ported into `review_queue.py --triage` (extended to cover harvest drafts, which the original claimed but never implemented); old entry point kept as a deprecation shim. Verified live: 36 queued items (25 synthesis + 11 harvest), 0 orphans. |
| **N5** | ⏳ Spec-gate (D7) — still needs Anthony's adoption + wiring decision (materializer `--check` vs post-write hook vs both). |
| **N6** | ⏳ ObjectGraph spike resume — gated on Anthony go; N1–N3 prerequisites now met. |

## Follow-on constraints

- Treat all files in `intake_raw/2026-06-12-root/` as non-canonical until
  distillation lands in existing canon and load-bearing claims are promoted
  through ADR/spec pathways.
- Every quantitative claim in the relocated reports is Unverified (dead
  "citeturn" tokens, unverifiable arXiv IDs) until independently re-sourced.
- The OVCA report must not be re-evaluated for integration without first
  reading the D1 rejection record (Ember seed pack file 01 §1–2).
