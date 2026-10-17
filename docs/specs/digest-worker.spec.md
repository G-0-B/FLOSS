# Digest Worker Specification

**Version:** 0.4.1  
**Status:** Specified  
**Truth Status:** Specified  
**Last Updated:** 2026-10-07

## 1. Purpose
The Digest Worker (`digest_worker.py`) implements the candidate-generation and epistemological bridge between raw unverified intake text and the FLOSSI0ULLK knowledge commons. It is strictly a **nonauthoritative candidate extraction and staging worker**. It does NOT have authority to publish directly to the local source chain or Holochain DHT.

## 2. Pipeline Stages & Execution Flow
The pipeline executes sequentially in `process_file`:
`PARSE -> DEDUP -> DIGEST -> RESOLVE_AND_ASSESS -> STAGE`

1. **PARSE:**
   - Reads raw document content, extracts text, computes content hash (SHA-256).
   - Enforces workspace root containment and rejects symlink traversal or secret-bearing paths.
   - Parses frontmatter metadata (`doi`, `arxiv`, `id`) using multiline regex matching.
2. **DEDUP:**
   - Compares SHA-256 and MinHash against the corpus. If exact duplicate, returns status `"EXACT_DUPLICATE_SKIPPED"` while preserving occurrence records.
   - Uses word 3-grams (shingles) for MinHash calculation, backed by a persistent corpus cache versioned by signature algorithm, seed, normalization scheme, mtime, and file size.
   - *Fidelity Invariant:* MinHash is an approximation that estimates Jaccard similarity. The cache preserves bit-identical sketch/hashvalues fidelity and stable estimated similarity across cold/warm reloads; it does not compute exact set-theoretic Jaccard similarity.
3. **DIGEST:**
   - Extracts atomic candidate claims distinguishing the normalized claim (`statement`) from its supporting quotation (`source_quote`).
   - Binds exact source text spans (`char_start`, `char_end`) to the verbatim `source_quote`.
   - *Alignment Policy:*
     - If LangExtract provides `char_interval`, validates interval against source text.
     - Fallback to exact quotation search in source text.
     - If `source_quote` is uniquely found verbatim -> `alignment: "EXACT"`.
     - If `source_quote` matches multiple locations in the source text -> `alignment: "AMBIGUOUS"` (`char_start: null`, `char_end: null`; never silently picks an arbitrary occurrence).
     - If `source_quote` is not found verbatim -> `alignment: "UNALIGNED"` (`char_start: null`, `char_end: null`).
   - Supports backends (`auto`, `ollama`, `omniroute`, `gemini`), defaulting to `auto` (detects local Ollama endpoint before cloud).
   - Outputs explicit `extraction_metadata` recording truncation, token counts, model ID, backend, and error fields.
4. **RESOLVE_AND_ASSESS (Decoupled Epistemic Contract):**
   - Strictly separates publication metadata from claim-level truth value:
     - `reference_resolution`:
       - `status`: `"ACTIVE" | "RETRACTED" | "UNKNOWN" | "UNREFERENCED"`
       - `provider`: `"crossref" | "arxiv" | "local"`
       - `notice_ref`: optional DOI of retraction notice.
       - *Crossref Directional Rule:* Retraction is detected strictly via `updated-by` relationships with `type: "retraction"`. The presence of `update-to` indicates that the record is an update notice, NOT that the current record is retracted.
     - `claim_assessment`:
       - `status`: `"UNRESOLVED" | "INSUFFICIENT_EVIDENCE"` (Note: `SUPPORT` and `CONTRADICT` require independent formal symbolic or verified NLI evaluation).
       - `signed_confidence`: float in `[-0.999, +0.999]`. Unassessed/unverified propositions MUST carry `0.0` with `assessed: false`.
       - *Retraction Rule:* Retraction of a source marks `reference_resolution.status: "RETRACTED"`, but leaves extracted claims with `claim_assessment.status: "UNRESOLVED"`, `signed_confidence: 0.0`, and `assessed: false` (with an epistemic notice), rather than manufacturing false logical contradiction.
   - Reference pairing: Claims without explicit `source_ref` matching a cited reference fail closed (`source_ref: null, reference_status: "UNMATCHED"`). The pipeline MUST NEVER fall back to arbitrary citations.
5. **STAGE (Nonauthoritative Persistence):**
   - Encapsulates proposals as `StagedCandidate` artifacts.
   - Generates dual content-addressed identities:
     - `invocation_key`: `SHA256(source_sha256 + parser + schema_version + model_id + backend)`
     - `output_artifact_hash`: `SHA256(canonical_json(output_result))`
   - Does NOT invoke `CellDirectory.append_entry()` or `GatewayTools.submit_claim()`.
   - Returns staged candidates for downstream consensus, challenge, or human steward promotion.

## 3. Grounding & Confidence Policy (ADR-10, ADR-17)
Analog confidence in `[-0.999, +0.999]` reflects epistemic certainty of candidate proposals:
- `UNASSESSED` (Proposition extracted but unverified, including retracted sources): `0.0` with `assessed: false`
- `INSUFFICIENT_EVIDENCE` / `NO_REFERENCE`: `-0.300` with `assessed: true`
- `UNRESOLVED` (Bibliographic presence verified, semantic assessment unverified): `+0.100` with `assessed: true`
- `SUPPORT` (Reserved for formal symbolic or verified NLI evaluation): `+0.850` with `assessed: true`
- `CONTRADICT` (Reserved for formal symbolic or verified NLI contradiction): `-0.900` with `assessed: true`

## 4. Architectural & Safety Invariants
1. **Zero Unauthorized Source-Chain Writes:** Digestion untrusted execution NEVER writes to `CellDirectory.append_entry()`.
2. **Crossref Retraction Accuracy & Directionality:** Retraction status must be detected strictly via Crossref `updated-by` relationships with update types matching `retraction`.
3. **Fail-Closed Reference Attribution:** If a claim does not explicitly cite a valid reference, it must NOT be bound to unrelated bibliography entries.
4. **Queue Time-Budget Composition:** `consume_digest_queue.py` operates under a strict total execution budget (240s) that fits comfortably within the parent heartbeat deadline (300s). Before launching each artifact, it verifies that remaining time exceeds the per-artifact budget (75s).
5. **Retry Bounds & Quarantine:** Repeated extraction failures are tracked with a retry counter (`retry_count >= 3` transitions to quarantine to prevent queue blockage).
6. **Path Containment & Security:** File inputs outside approved workspace roots or resolving via symlinks/secrets are rejected prior to inference dispatch.

## 5. Acceptance Criteria
- Unit tests verify `propose()` produces staged payloads without calling `cell_directory.append_entry()`.
- Retracted publications update reference metadata to `RETRACTED` while setting claim `signed_confidence: 0.0` and `assessed: false`.
- Crossref parser recognizes directional `updated-by` retraction structures without false-positive flags on `update-to` notices.
- Ambiguous quotation matches set `alignment: "AMBIGUOUS"` and `char_start: null, char_end: null`.
- Output envelope provides distinct `invocation_key` and `output_artifact_hash`.
- Queue consumer enforces total remaining budget checks and caps retry counts.
