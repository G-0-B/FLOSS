# FLOSSI0ULLK Local Ingestion, Semantic-Extraction, and Epistemic-State Pipeline (v1.2 Converged)

> **For agentic workers:** Execute task by task using the `executing-plans` workflow. Use one integration lead and one active writer. This is the canonical, converged implementation plan for the document ingestion substrate, evidence-first semantic extraction, and event-sourced Epistemic State Graph on the local RTX 4090 GPU (~12 GB usable VRAM envelope).

**Goal:** Establish an end-to-end, evidence-first document ingestion, semantic extraction, and belief-revision pipeline in `FLOSS/scripts/`, transitioning from raw immutable acquisition through pre-parse rights quarantine, layout-aware canonicalization (`DocumentIR`), multi-atom evidence alignment (`EvidenceSet`), structured claim decomposition (`ClaimVersion`), 2-axis post-normalization entailment evaluation, and an append-only Epistemic State Graph (ESG), verified by a 4-layer evaluation corpus (KTE v2) and staged role-separated tournaments.

**Authority & Staged Execution:** **+1 Proceed with Phases 0–3 only.** Component tournaments (Phase 4), shadow canary deployment (Phase 5), and authoritative knowledge promotion (Phase 6) remain strictly **BLOCKED** until the evidence grounding, epistemic-state transitions, licensing, and evaluation contracts are implemented, verified, and frozen.

**Hardware & Runtime Budget:** Windows 11 host, NVIDIA GeForce RTX 4090 Laptop GPU (16,376 MiB total VRAM), operating within a conservative **~12 GB usable VRAM ceiling** (reserving ~4 GB for OS and desktop compositing). Ollama 0.40+ running on `127.0.0.1:11434` with `trust_env=False` proxy bypass, strictly single-model residency (`OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`), and fixed 16,384 evaluation context (`num_ctx=16384`).

```yaml
id: local-ingestion-semantic-extraction-pipeline-2026-10-12
version: 1.2.0
kind: implementation_plan
status: Proposed
truth_status: Specified
observed_at: 2026-10-12
author_agent: Antigravity
supersedes:
  - local-ingestion-semantic-extraction-pipeline-2026-10-12@1.1.0
  - local-semantic-extraction-pipeline-2026-10-12@1.0.0
friction_tier: high
evidence_sources:
  - FLOSS/scripts/digest_worker.py (v0.4.1 staging implementation)
  - FLOSS/docs/specs/digest-worker.spec.md (v0.4.1 specification)
  - FLOSS/scripts/AGENTS.md (scoped script & extraction invariants)
  - FLOSS/evals/knowledge_triple_extraction/rubric.json (v1.0.0 baseline rubric)
  - FLOSS/evals/knowledge_triple_extraction/dev.jsonl (20-item dev split)
  - FLOSS/evals/knowledge_triple_extraction/heldout.jsonl (10-item heldout split)
  - research/2026-10-12-convergence-report.md (FLOSSI0ULLK convergence audit)
  - research/2026-10-12-current-plausible-best-local-semantic-extraction-audit.md
  - research/2026-10-12-jev-external-verifier-audit.md
upgrade_path:
  - Phase 0: Freeze repository state, smoke-test runtime artifacts, and audit model/dataset licenses.
  - Phase 1: Implement DocumentIR, transform maps, pre-parse rights quarantine, and parser routing (Docling baseline).
  - Phase 2: Implement EvidenceSet, ClaimVersion schema, 2-axis entailment gate, and Epistemic State Graph event ledger.
  - Phase 3: Harden KTE v2 with 4-layer evaluation corpus, native benchmark imports (SciFact, SciREX, Re-DocRED), and catastrophic gates H1–H17.
  - Phase 4: Execute role-separated tournaments (Parser, Span Generator, Extractor, Adjudicator, Jev TRK-11).
  - Phase 5: Run shadow canary with capability confinement and paired failure accounting.
  - Phase 6: Establish steward promotion and dependency-aware revision policies.
rollback_plan: Freeze and retain Phi-4-mini and basic text-layer parsing as emergency fallback; demote unverified candidate configurations back to research staging on any hard gate failure.
```

---

## 1. Source Precedence & Governing Principles

To prevent averaging conflicting research opinions, source authority is strictly ordered:

| Priority | Source Artifact | Governing Scope |
| --: | :-- | :-- |
| **1** | **v1.2 Converged Implementation Plan** (this document) | **Canonical implementation contract**; governs architecture, schemas, and execution order. |
| **2** | **Convergence Report & Ingestion Audit** | Red-team rationale, statistical limits, and amendment history. |
| **3** | **Current-Plausible-Best Model Analysis** | Model/runtime hypotheses, VRAM budgets, and tournament candidate specifications. |
| **4** | **Epistemic-State Analysis** | Requirements for explicit hypotheses, tests, belief revision, and non-authoritative event logging. |

### Core Architectural Invariants
1. **The Stable Substrate is Observational, Not Generative:** The stable center is an immutable observational substrate (`RawArtifact`, `RightsEnvelope`, `DocumentIR`, `EvidenceSet`) plus an event-sourced revision ledger (`Epistemic State Graph`). Models are replaceable proposal engines, never final truth authorities.
2. **Promote Nothing Yet:** Neither `NuExtract3`, `Granite 4.2`, `Qwen3.5`, nor `Phi-4-mini` is crowned. The current KTE evaluation suite (20 dev + 10 heldout) is too small and lacks catastrophic hazard gates.
3. **Capability Confinement:** Extraction and ingestion daemons possess **zero write credentials** for the local source chain, gateway claims, or Holochain DHT. Staging in `.stage/` is strictly non-authoritative.
4. **Pre-Parse Rights Quarantine:** Rights, consent, and retention classification occurs **before parsing and model exposure**, not as a downstream check.
5. **Statistical Realism:** Zero failures on $N=20$ cases proves only an upper failure bound of $\approx 13.9\%$ ($1 - 0.05^{1/20}$). Hard-gate test survival on locked sets is an operational promotion rule, never reported as zero production risk.

---

## 2. Converged Architecture: The Epistemic Pipeline

```text
RawArtifact (Immutable acquired bytes + SHA-256)
  ↓
RightsEnvelope + SecurityDisposition (Pre-parse sandbox & license audit)
  ↓
ParserRouter (Docling baseline vs. Marker / MinerU quarantined)
  ↓
DocumentIR + TransformMap (Versioned canonical text + coordinate mapping)
  ↓
ChunkGraph (Structure-aware chunking preserving block IDs)
  ↓
EvidenceProposal (Proposals from Extractors & GLiNER2 Side-Channel)
  ↓
Deterministic EvidenceSet Alignment (RAW_BYTE, SOURCE_TEXT, CANONICAL_CHAR, OCR_REGION, STRUCTURE)
  ↓
ClaimVersion (Normalized semantic claim with first-class fields)
  ↓
EntailmentAssessment (Independent Support / Refutation evaluation)
  ↓
Epistemic State Graph (Event-Sourced DAG)
  ├── Hypotheses & Questions
  ├── Supporting & Refuting Evidence Atoms
  ├── Belief Revisions (BeliefUpdatePolicy)
  └── Dissenting & Alternative Interpretations
  ↓
Non-Authoritative Staged Candidate (.stage/ with dual hashes)
  ↓
Risk-Tiered Steward Decision (Automated low-blast vs. Human steward high-impact)
  ↓
Promoted, Rejected, Superseded, or Retracted Knowledge
```

---

## 3. Data Contracts & Epistemic Schemas

### 3.1 Document Ingestion Substrate (`DocumentIR`)
Defines the versioned, canonical representation of parsed documents:
```json
{
  "raw_artifact_sha256": "3a7b...",
  "decoded_text_sha256": "9f2c...",
  "canonical_text_sha256": "e14d...",
  "canonicalizer_version": "v1.2.0-utf8-nfc",
  "parser_metadata": {
    "parser_id": "docling",
    "parser_version": "2.0.1",
    "parser_config_hash": "a4b1..."
  },
  "blocks": [
    {
      "block_id": "p03-b014",
      "page_num": 3,
      "kind": "paragraph | heading | table | caption | figure | equation | metadata",
      "bbox": [72.0, 140.5, 540.0, 220.0],
      "char_range": [4120, 4485],
      "raw_slice_hash": "c89e..."
    }
  ],
  "transform_map": {
    "canonical_to_raw_char": [[0, 0], [4120, 4128]],
    "transform_steps": ["nfc_normalization", "hyphen_break_merge"],
    "implementation_hash": "f62a..."
  }
}
```

### 3.2 Evidence Grounding & Coordinate System (`EvidenceSet`)
Replaces universal raw-byte replay with **typed source grounding** (OCR characters do not exist as raw text bytes):

| Grounding Class | Grounding Contract | Promotion Status |
|---|---|---|
| `RAW_BYTE_EXACT` | Exact byte interval in immutable source bytes | Promotable |
| `SOURCE_TEXT_EXACT` | Exact code-point interval in extracted native text stream | Promotable |
| `CANONICAL_CHAR_EXACT` | Exact zero-based, half-open Unicode code-point interval in canonical text (`canonical_text[start:end] == literal_content`) | Promotable |
| `TRANSFORM_MAPPED` | Validated through replayable `transform_map` back to native text | Promotable |
| `OCR_REGION_GROUNDED` | Grounded to page image hash, bounding box (`bbox`), OCR engine, and recognized text | Promotable |
| `STRUCTURE_GROUNDED` | Grounded to stable table cell ID, figure region, or equation object | Promotable |
| `APPROXIMATE` | Levenshtein similarity $>0.90$ | Review-only; fails promotion |
| `UNALIGNED` | Content unlocatable in document | Blocks promotion |

### 3.3 Expanded Claim Representation (`ClaimVersion`)
```json
{
  "claim_id": "clm-20261012-001",
  "claim_version": 1,
  "claim_type": "causal | association | observation | definition | recommendation | hypothesis",
  "statement": "Compound X does not increase cellular apoptosis in cortical neurons.",
  "subject_surface": "Compound X",
  "relation_surface": "does not increase",
  "object_surface": "cellular apoptosis in cortical neurons",
  "normalized_triple": {
    "subject": "urn:entity:compound_x",
    "predicate": "increases",
    "object": "urn:entity:cellular_apoptosis_cortical_neurons",
    "ontology_status": "ALLOWLISTED"
  },
  "polarity": "negated",
  "modality_type": "none",
  "modality_strength": "asserted",
  "attribution_chain": [
    {
      "speaker": "Clinical Trial Alpha",
      "kind": "study_report",
      "nested_level": 0
    }
  ],
  "quantifiers": ["none"],
  "conditions": [],
  "temporal_scope": null,
  "population_scope": "cortical neurons (in vitro)",
  "causal_direction": "inhibitory_null",
  "evidence_refs": ["ev-01"],
  "normalization_map_id": "norm-rule-v2.1",
  "abstention_reason": null
}
```

### 3.4 Independent 2-Axis Entailment (`EntailmentAssessment`)
Support and refutation are evaluated and stored on **independent boolean axes** rather than an opaque enum:

| Entailment State | `support` Axis | `refutation` Axis | Semantic Meaning |
|---|:---:|:---:|---|
| `SUPPORTED` | **true** | false | Evidence strictly entails the normalized claim. |
| `CONTRADICTED` | false | **true** | Evidence refutes the claim (e.g. negation inverted). |
| `INSUFFICIENT` | false | false | Evidence is related but lacks warrant for assertion. |
| `CONFLICTING` | **true** | **true** | Separate evidence atoms directly contradict each other. |

### 3.5 Epistemic State Graph (ESG) Specification
An event-sourced DAG capturing observations, interpretations, hypotheses, assessments, and belief revisions:
* **Node Types:** `SourceArtifact`, `DocumentRevision`, `EvidenceAtom`, `ClaimVersion`, `Hypothesis`, `Question`, `TestPlan`, `TestExecution`, `Observation`, `Assessment`, `BeliefState`, `Decision`, `PolicyVersion`.
* **Edge Types:** `derived_from`, `observed_in`, `supports`, `refutes`, `contextualizes`, `attributes_to`, `qualifies`, `tests`, `depends_on`, `updates`, `supersedes`, `retracts`, `disagrees_with`, `requires_review`, `authorized_by`.
* **Append-Only Event Ledger Schema:**
  ```json
  {
    "event_type": "BELIEF_REVISED | CLAIM_PROPOSED | EVIDENCE_ALIGNED | ASSESSMENT_RECORDED",
    "event_id": "sha256:...",
    "occurred_at": "2026-10-12T18:40:00Z",
    "actor": "policy:belief-update-v1.2",
    "inputs": ["claim:clm-001@v1", "assessment:asm-001", "belief-state:prev-001"],
    "outputs": ["belief-state:curr-001"],
    "policy_hash": "sha256:...",
    "rationale_refs": ["ev-01", "asm-001"],
    "authority_tier": "non_authoritative"
  }
  ```
* **Authority Rule:** Models may propose claims, hypotheses, questions, tests, and assessments. Only deterministic policy and authorized human stewards may transition active belief tags or approve authoritative promotions.

---

## 4. Evaluation Program & Dataset Governance

### 4.1 Four-Layer Corpus Structure
1. **Layer 1 (Unit Invariants - 50 items):** Hash determinism, Unicode NFC normalization, byte/code-point indexing, transform invertibility, table/equation structures, prompt injection containment, malformed input rejection.
2. **Layer 2 (Minimal-Pair Challenge Suite - 60 items):** Versioned, paired synthetic and curated scientific sentences isolating the 15 semantic hazards (e.g., $A \text{ causes } B$ vs. $A \text{ does not cause } B$; $A \text{ causes } B$ vs. $A \text{ may cause } B$).
3. **Layer 3 (Locked Realistic Acceptance Set - 100 documents):** Multi-domain scientific papers (biomedical, computer science, governance) with human-adjudicated gold claims, evidence sets, and rationale. **Strictly locked; never exposed to tuning loops.**
4. **Layer 4 (Shadow Canary Stream):** Continuous unpromoted intake stream monitoring distribution drift, OCR degradation, and operational tail latency.

### 4.2 Primary Benchmark Datasets & Licensing Gate
* **`SciFact` (Highest Priority - Entailment & Polarity):** Research abstract retrieval, rationale selection, and support/refute/neutral stance. (CC-BY-NC-2.0). Replayed in native schema; human-verified FLOSS projection for entailment.
* **`SciREX` (High Priority - Document-Level IE):** Full-document salient entities and n-ary relations. Evaluated against document and chunk reconciliation layers.
* **`Re-DocRED` (High Priority - Document Relations):** MIT-licensed corrected document-level relations with cleaned negative annotations.
* **`SciERC` (Secondary):** Scientific entities, relations, and coreference. Verify license before redistribution.
* **`DocRED` (Control):** MIT-licensed general document-level relations.
* **`BioRED` (BLOCKED):** License is marked as "unknown" on public dataset cards. **Prohibited from repository inclusion until explicit license is established.**

### 4.3 Hard Epistemic Hazard Gates (H1–H17)
A single catastrophic violation on Layer 2 or Layer 3 blocks configuration promotion:
* **H1 (Schema Validity):** 100% parseable, valid JSON matching target schema without programmatic repair.
* **H2 (Evidence Identity):** 100% of bound spans satisfy groundings (`CANONICAL_CHAR_EXACT`, `RAW_BYTE`, or `OCR_REGION`).
* **H3 (Unsupported Entities):** 0 hallucinated entities absent from evidence or explicit normalization map.
* **H4 (Polarity Inversion):** 0 reversals between affirmed and negated claims.
* **H5 (Modality Strengthening):** 0 conversions of hedged possibilities/hypotheses into asserted facts.
* **H6 (Attribution Collapse):** 0 conversions of reported/cited claims into author narrator truth.
* **H7 (Ontology Validity):** 100% predicate membership in registered ontology allowlist.
* **H8 (Scope Fidelity):** 0 lost conditional restrictions, population bounds, or quantifier modifiers.
* **H9 (Relation Direction):** 0 inverted causal or comparative relationships.
* **H10 (Cardinality Integrity):** 0 merged distinct propositions or dropped independent conjuncts.
* **H11 (Abstention Compliance):** Candidate correctly emits empty set on null/insufficient documents.
* **H12 (Evidence Completeness):** Claims requiring multi-span evidence do not retain a misleading partial fragment.
* **H13 (Source Grounding Replay):** Every evidence atom is replayable to an immutable source object (rewritten from raw-byte-only replay).
* **H14 (Parser Provenance):** Evidence retains valid block ID, page number, and layout coordinates.
* **H15 (Injection Resistance):** 0 compliance with adversarial instructions embedded in source text.
* **H16 (Pre-Parse Rights Policy):** 0 ingestion of documents violating retention, consent, or copyright policies.
* **H17 (Post-Norm Entailment):** 0 staged claims flagged as `CONTRADICTED` or `INSUFFICIENT` by the entailment gate.

---

## 5. Role-Separated Tournament Matrix

Candidates are evaluated in role-separated tracks. Models are not conflated across roles.

### Track 0: Document Parser Tournament
* **P-01 (Docling Baseline):** `docling 2.0+` (MIT license; hierarchical layout and table extraction).
* **P-02 (Marker Challenger):** `marker-pdf` (OCR and mathematical formula extraction).
* **P-03 (MinerU Quarantined Challenger):** `mineru` (Complex multi-column layouts; custom license review required).
* **P-04 (Native Text Control):** `pypdf / pdfplumber` (Zero-OCR fast baseline for born-digital PDFs).

### Track A: Span & Relation Candidate Generators (Side-Channels)
* **SC-01 (GLiNER2):** Schema-driven entity/relation extraction via PyTorch/ONNX runtime (Apache-2.0).
* **SC-02 (GLiNER-Relex):** Zero-shot relation classification on pre-extracted spans.

### Track B: Structured Semantic Extractors (Ollama / Local 4090)
All tracks run under: `num_ctx: 16384`, `OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`, Flash Attention enabled.
* **TRK-01 (Phi-4-mini Incumbent):** `phi4-mini:latest` ($T=0.1$, `think=False`).
* **TRK-02 (NuExtract3 Q4 Efficiency):** `hf.co/numind/NuExtract3-GGUF:Q4_K_M` ($T=0.2$, `think=False`).
* **TRK-03 (NuExtract3 Q6 Quality Max):** `hf.co/numind/NuExtract3-GGUF:Q6_K` ($T=0.2$, `think=False`, pending Task 0 smoke test).
* **TRK-04 (NuExtract3 Q6 Thinking Ablation):** `hf.co/numind/NuExtract3-GGUF:Q6_K` ($T=0.6$, `think=True`).
* **TRK-05 (Qwen3.5-4B Control):** `qwen3.5:4b` ($T=0.7$, `top_p=0.8`).
* **TRK-06 (Qwen3.5-9B Generalist):** `qwen3.5:9b` ($T=0.7$, `top_p=0.8`, multimodal).

### Track C: Local Semantic Adjudicators
* **ADJ-01 (Granite 4.2 8B Q4):** `granite4.2:8b` (IBM native sampled: $T=1.0$, `top_p=0.95`).
* **ADJ-02 (Granite 4.2 8B Q6):** `granite4.2:8b-q6_K` (IBM native sampled: $T=1.0$, `top_p=0.95`).
* **ADJ-03 (Qwen3.5-9B Judge):** `qwen3.5:9b` (Sampled evaluation prompt for NLI entailment).

### Track D: External-Plane Typed Verifier Experiment (Jev TRK-11)
* **TRK-11 (TypeSafe AI Jev):** Evaluates atomic typed `Choice` and `Noul` questions across 7 verification tasks (entity support, polarity preservation, modality hedging, attribution anchor, scope restrictions, predicate direction, abstention).
* **Privacy & Fail-Closed Invariant:** Transmits only minimal evidence atom and candidate field (never full documents). Strict fail-closed fallback routes network timeouts or schema shifts to local adjudicators or abstention. The fully local pipeline remains 100% operational independently.

---

## 6. Phased Implementation Roadmap & Staged Authority

```
[Phase 0: Revalidation & Smoke Tests] ───────► APPROVED TO EXECUTE
├── Task 0.1: Freeze repository commit & dirty tree report
├── Task 0.2: Model artifact smoke tests (NuExtract3 Q6 import, projector binding, VRAM recovery)
└── Task 0.3: Dataset license audit (verify SciFact, SciREX, Re-DocRED; quarantine BioRED & MinerU)
       ↓
[Phase 1: Document Substrate] ────────────────► APPROVED TO EXECUTE
├── Task 1.1: Pre-parse RightsEnvelope & SecurityDisposition sandbox
├── Task 1.2: Implement DocumentIR & TransformMap (scripts/document_ir.py)
└── Task 1.3: Parser tournament (Docling baseline vs Marker vs Native text)
       ↓
[Phase 2: Semantic Contract & Epistemic State] ► APPROVED TO EXECUTE
├── Task 2.1: Refactor digest_worker.py to support EvidenceSet & ClaimVersion
├── Task 2.2: Implement 2-axis EntailmentAssessment (scripts/entailment_gate.py)
└── Task 2.3: Implement Epistemic State Graph schema & append-only event ledger (scripts/epistemic/)
       ↓
[Phase 3: Evaluation Suite Hardening] ────────► APPROVED TO EXECUTE
├── Task 3.1: Upgrade rubric.json to v2.0.0 (enforcing H1–H17)
├── Task 3.2: Build Layer 1 (Unit Invariants - 50 items) & Layer 2 (Minimal Pairs - 60 items)
└── Task 3.3: Construct & human-adjudicate Layer 3 (Locked Realistic Acceptance Set - 100 docs)
       ↓
═══════════════════════════════════════════════════════════════════════════
GATE STOP: Model Tournaments & Canary remain BLOCKED until Phases 0–3 pass
═══════════════════════════════════════════════════════════════════════════
       ↓
[Phase 4: Role-Separated Tournaments] ────────► BLOCKED
├── Component tournaments across Tracks 0, A, B, C
├── Jev TRK-11 external-plane experiment
└── Composed pipeline evaluation & marginal reasoning gain analysis
       ↓
[Phase 5: Shadow Canary Deployment] ──────────► BLOCKED
├── Capability-confined execution (zero DHT / source-chain write tokens)
└── Shadow queue processing, idempotent recovery, & failure accounting
       ↓
[Phase 6: Authority & Knowledge Promotion] ───► BLOCKED
└── Signed qualification receipt & risk-tiered steward promotion
```

---

## 7. Immediate Unblocked Work Packages (Phases 0–1)

1. **Task 0.1 (Commit Freeze):** Record live checkout revision, dirty overlays, and environment manifest.
2. **Task 0.2 (Local Capability Smoke Tests):**
   - Test `ollama run hf.co/numind/NuExtract3-GGUF:Q6_K` to confirm whether direct Ollama import succeeds or requires a Modelfile with explicit VLM projector binding.
   - Verify JSON schema mode compatibility on `phi4-mini`, `qwen3.5:4b`, and `granite4.2:8b`.
   - Verify 100% idle VRAM recovery ($\pm 200$ MB) upon `ollama stop`.
3. **Task 0.3 (Dataset & License Gate):**
   - Record formal license snapshots for `SciFact` (CC-BY-NC-2.0), `SciREX`, `DocRED` (MIT), `Re-DocRED` (MIT).
   - Document quarantine flag for `BioRED` (unknown license) and `MinerU` (custom commercial clause).
4. **Task 1.1 (Pre-Parse Rights Sandbox):** Create `FLOSS/scripts/rights_envelope.py` to enforce rights classification before parsing.
5. **Task 1.2 (DocumentIR & TransformMap):** Implement `FLOSS/scripts/document_ir.py` defining the canonical intermediate representation and invertible coordinate transformation map.
