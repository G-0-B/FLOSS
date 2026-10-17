# FLOSS/scripts/AGENTS.md — Scoped Operational Invariants for Scripts & Digestion (v1.2)

> **Scope:** This guidance applies specifically to agents operating on `FLOSS/scripts/` (intake daemons, digestion workers, scrapers, model evaluation harnesses, metadata lookups, and maintenance scripts). It provides progressive, domain-specific invariants without bloating the workspace-root rules.

---

## 1. Epistemic Trust Boundary & Staged Authority
- **Candidate Generator Rule:** Scripts and ingestion pipelines (`digest_worker.py`, batch intake, LLM claim extractors) are strictly **candidate generators**, never publishers.
- **Capability Confinement:** Untrusted intake scripts MUST run without source-chain or DHT write credentials. They MUST NEVER call `CellDirectory.append_entry()`, `GatewayTools.submit_claim()`, or DHT publishing methods directly.
- **Staged Execution Authority:** Only Phases 0–3 (substrate, schemas, evaluation suite hardening) are approved to proceed. Model tournaments (Phase 4), shadow canary deployment (Phase 5), and authoritative knowledge promotion (Phase 6) remain strictly **BLOCKED** until all evaluation, evidence grounding, and epistemic contracts pass review.
- **Non-Authoritative Staging:** All candidate proposals land in inspectable, content-addressed, non-authoritative staging areas (`.stage/` or `.agent-surface/knowledge_log/digests/`).
- **Governed Promotion:** Promotion from staged candidate to the local source chain or consensus gateway requires an explicit, separately governed Consensus / Challenge / Steward action (ADR-10, ADR-17).

---

## 2. Decoupled Epistemic Grounding & Pre-Parse Rights
- **Pre-Parse Rights Quarantine:** Rights, copyright, retention, and consent classification (`RightsEnvelope`) must occur **before parsing and model exposure**, not as an afterthought.
- **Separation of Concerns:** External publication metadata (`reference_resolution`) must be decoupled from proposition truth assessment (`claim_assessment`).
- **Retraction Semantics:** Retraction of a source publication weakens or invalidates reference authority, but does NOT constitute formal logical negation of every statement within the paper.
  - A claim extracted from a retracted source must NOT be marked `CONTRADICT (-0.900)`.
  - It must be recorded as `reference_resolution.status: "RETRACTED"`, with proposition confidence unassessed (`signed_confidence: 0.0`, `assessed: false`), accompanied by an epistemic notice.
- **Directional Metadata Semantics:** In Crossref and related APIs, relationship directionality must be honored. An article is retracted if it was updated by a retraction notice (`updated-by`). An update notice itself points to the target (`update-to`); checking `update-to` directionless misclassifies active retraction notices as retracted.
- **Fail-Closed Reference Attribution:** If an extracted claim specifies a citation identifier that does not match cited references in the document, it must fail closed (`source_ref: null, reference_status: "UNMATCHED"`). It must NEVER fall back to unrelated primary DOIs or arbitrary bibliography entries.

---

## 3. Evidence Grounding & Coordinate System (`EvidenceSet`)
- **Typed Evidence Set:** Claims must not rely solely on scalar text quotations. Evidence is represented as an array of typed atoms: `text_span`, `table_cells`, `figure_region`, `equation`, `metadata_field`.
- **Coordinate Grounding:** Character spans (`char_start`, `char_end`) are zero-based, half-open Unicode scalar offsets grounded strictly in `canonical_text_sha256` of `DocumentIR`.
- **Typed Grounding Classes (Replacing Universal Raw-Byte Replay for OCR):**
  - `RAW_BYTE_EXACT`: Exact byte-slice match on immutable raw source bytes.
  - `SOURCE_TEXT_EXACT`: Exact code-point interval in extracted native text stream.
  - `CANONICAL_CHAR_EXACT`: Exact Unicode scalar match on canonical text (`canonical_text[start:end] == literal_content`).
  - `TRANSFORM_MAPPED`: Match validated through replayable `transform_map` (e.g. dehyphenated).
  - `OCR_REGION_GROUNDED`: Grounded to page image hash, bounding box (`bbox`), OCR engine, and recognized text.
  - `STRUCTURE_GROUNDED`: Grounded to stable table cell ID, figure region, or equation object.
  - `APPROXIMATE`: Levenshtein similarity $>0.90$; flagged for review (fails strict promotion gate).
  - `UNALIGNED`: Content not found in document (`null` offsets; fails strict promotion gate).
- **Multi-Candidate Disambiguation:** For repeated strings, `MULTIPLE_CANDIDATES` retains ALL matching intervals and uses block IDs and page numbers for layout disambiguation rather than discarding all offsets.

---

## 4. Two-Stage Semantic Architecture & Epistemic State Graph
- **Separation of Extraction Stages:** Generative extraction must decouple verbatim surface identification from ontology normalization:
  1. *Stage 1 (Surface Extraction):* Extract exact surface phrases (`subject_surface`, `relation_surface`, `object_surface`, `evidence_atoms`).
  2. *Stage 2 (Ontology Normalization):* Map surface entities and relations into canonical knowledge triples (`subject`, `predicate`, `object`).
- **First-Class Semantic Fields:** `ClaimVersion` must explicitly represent: `claim_type`, `polarity` (affirmed, negated, denied-evidence, mixed, unresolved), `modality_type` & `modality_strength`, `attribution_chain` (nested speakers/citations), `quantifiers`, `conditions`, `temporal_scope`, and `population_scope`.
- **Independent 2-Axis Entailment Gate:** The entailment gate evaluates whether the normalized claim is licensed by its evidence atoms along independent `support` and `refutation` boolean axes:
  - `SUPPORTED`: `support: true, refutation: false`
  - `CONTRADICTED`: `support: false, refutation: true`
  - `INSUFFICIENT`: `support: false, refutation: false`
  - `CONFLICTING`: `support: true, refutation: true`
- **Epistemic State Graph (ESG):** Connects immutable observations (`SourceArtifact`, `EvidenceAtom`) to defeasible claims (`ClaimVersion`), judgments (`EntailmentAssessment`), and revisions (`BeliefRevision`) via an append-only event ledger.
- **Catastrophic Hazard Gates (H1–H17):** A single fatal error on Layer 2 (Minimal Pairs) or Layer 3 (Acceptance) blocks candidate promotion:
  - Evidence identity, unsupported entities, polarity reversal, unhedged modal strengthening, attribution collapse, scope loss, inverted relation direction, cardinality merging, abstention failure, transformation replay failure, prompt injection compliance.

---

## 5. Local LLM Execution & Benchmarking Protocol
- **Strict Single-Model Sequential Lifecycle:** Models must never be executed concurrently. Local execution scripts must enforce single residency (`OLLAMA_MAX_LOADED_MODELS=1`, `OLLAMA_NUM_PARALLEL=1`). Before loading a new model:
  1. Explicitly evict the active model via `ollama stop <model>`.
  2. Poll and verify absence in `ollama ps`.
  3. Confirm GPU VRAM has returned to baseline before initiating the next model.
- **Native Sampling Profiles Required:** Models evaluated for local extraction or reasoning must be tested under their author-specified sampling parameters. Standardized low-temperature runs on thinking models represent artificial degeneration ablations, not representative capability evaluations:
  - `NuExtract3`: Native template tokens (`【task】structured`, `【template_start】`, etc.), $T=0.2$ (`think=False`) for deterministic; $T=0.6$ (`think=True`) for reasoning escalation.
  - `Agents-A1-4B`: `temp: 0.85, top_p: 0.95, top_k: 20, presence_penalty: 1.1`.
  - `IBM Granite 4.2`: `temp: 1.0, top_p: 0.95`.
  - `Gemma 4 E4B`: `temp: 1.0, top_p: 0.95, top_k: 64`.
- **Prohibition of Oracle Cardinality:** Prompts must not leak the gold cardinality (*"Extract $N$ claims"*) during comparative evaluation or production extraction. Determining the number of independent propositions supported by text is an intrinsic part of the semantic extraction task.
- **External Verifier Experiment (Jev TRK-11):** When testing Jev as an external typed verifier:
  - Transmit only the minimal evidence atom and candidate field (never full documents).
  - Strict fail-closed policy: network timeouts or schema changes route to local adjudicators or abstention.
  - Fully local pipeline remains 100% operational independently.
- **HTTP Proxy Discipline:** When communicating with local Ollama (`127.0.0.1:11434`) via Python `httpx`, always instantiate `httpx.Client(trust_env=False)` to prevent environment proxies (`HTTP_PROXY`) from intercepting loopback calls and returning HTTP 400.

---

## 6. Daemon Budget & Reliability Discipline
- **Parent Budget Headroom:** Any worker invoked by a parent daemon (such as `heartbeat.py` with a 300-second budget) must operate under a strictly smaller total budget (e.g., 240 seconds) to ensure clean termination, resource cleanup, and receipt emission before parent cutoff.
- **Dynamic Remaining-Budget Check:** Queue consumers must calculate elapsed time before launching each item. If `remaining_time < per_item_timeout`, the worker must defer remaining queue items to subsequent ticks rather than risking interrupted writes.
- **Retry Bounds & Quarantine:** Repeated processing failures must be bounded by a retry counter (`MAX_RETRIES = 3`). Persistent failures must quarantine the artifact rather than blocking the intake queue indefinitely.
- **Dual Content-Addressing for Neural Pipelines:** Pipelines utilizing generative models must distinguish:
  1. `invocation_key`: `SHA256(source_bytes + parser + schema_version + model_id + backend + config)` — identifies the input configuration and cache eligibility.
  2. `output_artifact_hash`: `SHA256(canonical_json(output_bytes))` — identifies the immutable bytes actually produced by the run.
