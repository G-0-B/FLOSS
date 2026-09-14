---
id: "flossi0ullk-research-register"
version: "1.0.0"
kind: "research_register"
status: "Accepted"
updated: "2026-07-30"
supersedes:
  - "Cryptographically_Verifiable_Context_Artifacts_for_AI-to-AI_and_Human-AI-Human_Co-Evolution.md"
  - "Rose_Forest_Merged_Artifact_v1__Adversarial_Verification_and_Cor.md"
  - "FLOSSIOULLK_merged_upgradeable_artifact_v1_2026-07-01.md (citation register §11)"
truth_status: "mixed"
truth_status_breakdown:
  verified: "Radicle, MCP spec version, RICE attribution, MAST, METR, C2PA"
  refuted: "Holochain 0.6.1 date, MCP governance framing, NLnet window, Phase 0 status"
  aspirational: "F5/F6 Syntellect corpus, YumeiCHAIN, ContextNest selector grammar"
  unverified: "MCP 2026-07-28 stateless RC; NLnet post-summer terms; several 2026 arXiv IDs"
upgrade_path: "Re-verify dated claims quarterly; anything older than 6 months is Unverified by default"
rollback_plan: "N/A — reference material"
friction_tier: "low"
---

# Research Register — Corrected

**Cite from here. Do not load into agent context whole.** This absorbs the 41K
research survey and the 25K adversarial verification. The verification's
corrections are applied inline rather than left in a parallel document — the
prior failure was that the refutation existed alongside the claim it refuted
and never merged into it.

**Staleness rule:** every entry carries a check date. Anything unchecked for
6+ months reverts to Unverified regardless of how confident it reads.

---

## 1. External Facts — corrected

| Claim | Status | Correction / note | Checked |
|---|---|---|---|
| Radicle 1.9.1, p2p signed git forge | **Verified** | Announced 2026-05-22. ~12 devs, ~8000 repos, 600+ nodes/wk. Discovery self-described WIP. | 2026-07 |
| Radicle + GitHub Actions CI pattern | **Verified** | Blog 2025-05-30; broker + adapters mature (Wirzenius, 2025-07-23) | 2026-07 |
| Holochain 0.6.1, Iroh replaces tx5 | **Verified**, date **Refuted** | holochain.org says **2026-05-12**, not June 11. tx5 behind compile flag, removal next release. | 2026-07 |
| MCP spec 2025-11-25 | **Verified** | Async Tasks, OAuth 2.1 resource-server, URL-mode elicitation | 2026-07 |
| MCP "Linux Foundation trajectory" | **Refuted** | Concretely **donated to Agentic AI Foundation** (LF directed fund) Dec 2025. Accomplished fact, not trajectory. | 2026-07 |
| MCP 2026-07-28 stateless RC | **Unverified** | Statelessness is a roadmap priority; no dated RC confirmed | 2026-07 |
| RICE (Robustness/Interp/Control/Ethicality) | **Verified**, framing **corrected** | Ji et al., arXiv 2310.19852, PKU. **One survey's organizing scheme — not an industry standard.** Compare HHH (Askell 2021), NIST AI RMF. | 2026-07 |
| NLnet NGI0 Commons open | **Refuted** | 13th and **final** call closed 2026-06-01. Only NGI Taler + Fediversity remain (2026-08-01). Regular call "reopens after summer" — terms unpublished. | 2026-07 |
| NLnet license policy | **Verified** | Requires OSI/FSF-recognized license *in its entirety*. Ethical-use riders fail OSD §6. | 2026-07 |
| MAST failure taxonomy | **Verified** | Cemri et al., arXiv 2503.13657, NeurIPS 2025. 1,642 traces, κ=0.88. Failures: **Specification 41.8% / Inter-agent 36.9% / Verification 21.3%**. Range 41–86.7%. | 2026-07 |
| METR time horizons | **Verified** | Kwa et al., arXiv 2503.14499. 50% horizon; doubling ~7 months since 2019. **80% horizon ≈ 5× shorter.** CIs ~2× each direction. | 2026-07 |
| C2PA | **Verified** | Leading open provenance standard; recognized in California AB 853 as a compliance mechanism | 2026-07 |
| CVE-2025-6514 (mcp-remote), CVE-2025-49596 (Inspector) | **Verified** | CVSS 9.6 / 9.4; fixed v0.1.16 / <0.14.1 | 2026-07 |
| F5/F6 Syntellect / SUPERALIGNMENT corpus | **Verified as self-published** | Ecstadelic Media Group, not peer-reviewed. **Orientation only [E0/E1]. Never a release criterion.** | 2026-07 |

---

## 2. Compose-Before-Build — the finding that matters most

**Mature standards already cover "signed provenance sidecars for artifacts."**
Verify against these before writing bespoke format code:

- **in-toto attestations (ITE-6)** — signed statement/subject/predicate envelope; the substrate under Sigstore and SLSA
- **SLSA provenance** — expressed as an in-toto predicate. SLSA v1.0 "Distributing provenance" **explicitly recommends sidecar files** with names derived from the artifact
- **Sigstore / Cosign** — keyless signing + Rekor transparency log
- **C2PA** — content provenance; pulled into regulation (EU AI Act Art. 50 enforceable **2026-08-02**; California SB 942 effective 2026-01-01, AB 853 watermarking **2026-08-02**)

**Threshold to justify bespoke format:** a concrete requirement demonstrably
unmet by an in-toto predicate — per-edit granularity, offline Holochain-native
operation, or no external transparency-log dependency. State which one, or use
the standard.

Also relevant: **KERI shaping ≠ KERI.** `t="prov"` is not a registered ilk;
KERI does not use RFC 8785/JCS. A translation step is required regardless, so
"additive migration" is not a valid rationale.

---

## 3. Format & Efficiency

| Approach | Note | Status |
|---|---|---|
| ObjectGraph N6 | Highest token efficiency of surveyed formats; 14 docs → 112 nodes / 182 edges, traversal operational | Verified (working branch) |
| Context caching / KV preservation | Rationale for the stable/delta split in CONTEXT.yaml — stable section stays cache-warm | Specified |
| ContextNest selector grammar | Deterministic replacement for keyword scoring | Aspirational |
| MAIF | AI-native artifact container | Specified |
| Atlas | ML pipeline provenance | Specified |
| Cross-lingual token arbitrage | Surveyed; no adoption case made | Aspirational |

---

## 4. Co-Evolution Methods (surveyed, none adopted)

NOVA (generate-verify-accumulate-retrain) · EvoSkills (cross-model portable
skill packages) · Data-prompt co-evolution / living test set · Dual-Helix
prompt optimization · Multi-Agent Evolve.

**Adoption gate:** none of these enters the build until a NOW-tier pain exists.
The `evals/provenance_packet_validation/` held-out set is the closest thing to
an actual living test set and it already exists — use it before adopting a
methodology paper.

---

## 5. Calibrated Timelines (replaces 30/60/90)

Original phases were unrealistic for a solo developer given MAST failure rates.

| Phase | Original | Calibrated | Exit criterion |
|---|---|---|---|
| 0 — walking skeleton | 30d | **8–12 wk** | DNA compiles to WASM **and** one Tryorama test green **in CI** |
| 1 — safety shell | 30d | **6–10 wk** | Policy gate coverage measurable |
| 2 — MetaLoop | 30d | **6–8 wk** | KnowledgeTriple round-trip |
| 3 — sovereignty | 90d+ | **open-ended, pain-gated** | Named concrete pain |

Compression threshold: demonstrated agent reliability >90% on the held-out
benchmark. Keep the gate structure; stretch the calendar.

---

## 6. RICE + K Operationalization

| Letter | Metric | Tool |
|---|---|---|
| Robustness | Red-team pass rate vs. tool-poisoning | AISI Inspect, AgentDojo, AgentHarm |
| Interpretability | Audit-trail completeness % | Signed append-only logs |
| Controllability | Policy-gate coverage %, rollback MTTR | OPA/Rego + canary timing |
| Ethicality | Refusal consistency | promptfoo, Inspect |
| K = log10(τ_blind/τ_agent) | Report **both 50% and 80%** thresholds, with CIs | METR-style harness |

---

## 7. MCP Security Gate (Phase 0)

OAuth 2.1 resource-server with audience validation, no token passthrough ·
RFC 8707 resource indicators · TLS 1.3 + DNS-rebinding protection for local
HTTP · pin and verify server package versions · OWASP MCP Top 10 + Agentic
Top 10 · NSA MCP Security Design Considerations (2026-05).

**Cite specific studies, not blended ranges.** Astrix (5,200+ servers): 88%
require credentials, only 8.5% OAuth, 53% static keys/PATs, 79% of keys via
env vars. Equixly (2025-03): ~43% command injection / 30% SSRF / 22% path
traversal. Do not report these as one "30–82%" figure.

---

## 8. Precedent for `before_build_check`

Not novel — maps to ADRs, IETF/RFC design review, premortems (Klein/Kahneman),
Google design/readability review. Cite precedent rather than claiming invention.

---

## 9. Unresolved

- Two divergent codebases (`kalisam/Amazon_Rose_Forest_01` MIT vs `G-0-B/FLOSS`
  GPL-3.0+Compassion) with conflicting completion claims. **Pick one canonical
  and document the relationship.** This is the provenance contradiction the
  Constitution layer exists to fix.
- Compassion Clause OSI status — legal question, blocks funding eligibility.
- NLnet post-summer call terms unpublished.
- Graph store for Layer B: SQLite+shim (recommended, solo-friendly) vs KùzuDB
  (verify maintenance — archived/forked late 2025) vs git-markdown graph.
