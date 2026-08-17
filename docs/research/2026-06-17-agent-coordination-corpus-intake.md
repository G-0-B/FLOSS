# 2026-06-17 Agent-Coordination Corpus Intake + Deferred Ingestion Plan

```yaml
id: "2026-06-17-agent-coordination-corpus-intake"
status: "Records staged; binaries pending local fetch; distillation/ingestion deferred to live-substrate"
truth_status:
  records: "Verified (metadata + abstracts pulled from arXiv/HF search 2026-06-17)"
  pdf_binaries: "Unverified — downloaded via arXiv MCP into a tool sandbox not bridgeable to repo; local fetch command provided below"
  relevance_mapping: "Specified (analyst read against current layer stack, not yet committee-reviewed)"
  ingestion: "Aspirational — does not begin until the Orchestration Phase 0 substrate bridge is live ('heartbeat')"
raw_holding_area: "FLOSS/docs/research/intake_raw/2026-06-17-arxiv/"
source_run: "daily-research-task-digest 2026-06-17, Section 1"
companion_adr: "ADR-16 (Omnigent execution surface) — same session"
```

## Why these two

Surfaced by the 2026-06-17 research scan as the work most relevant to FLOSSI0ULLK's
Layer 4 (agent coordination) and Layer 4.6 (harness composition). Both are
multi-agent-coordination papers that bear directly on the analog-vote roster and
the diversity policy. Staged here as a digestion batch; full distillation and
substrate ingestion are deferred (see plan §3).

## Records

### 1. SwarmSys: Decentralized Swarm-Inspired Agents for Scalable and Adaptive Reasoning
- **arXiv:** 2510.10047 · **HF:** https://hf.co/papers/2510.10047
- **Authors:** Ruohao Li, Hongjun Liu, Leyi Zhao, Zisu Li, Jiawei Li, Jiajun Jiang, Linning Xu, Chen Zhao, et al.
- **Published:** 2025-10-11 (label: not new as of this run — standing reference, not 48h-fresh)
- **Relevance:** Distributed multi-agent framework with explicit Explorer / Worker /
  **Validator** roles, embedding-based probabilistic matching, and a pheromone-inspired
  reinforcement loop for self-organizing convergence. Maps almost directly onto the RSA-swarm
  + LLM-committee design (Layer 4) and the role separation the consensus gateway assumes. Read
  against: does its "Validator" role stay advisory (neural-assists) or is it allowed to decide
  truth? Our prime directive forbids the latter — note the distinction during distillation.

### 2. Towards a Science of Scaling Agent Systems
- **arXiv:** 2512.08296 · **HF:** https://hf.co/papers/2512.08296
- **Authors:** Yubin Kim, Ken Gu, Chanwoo Park, Chunjong Park, Samuel Schmidgall, A. Ali Heydari, Yao Yan, Zhihan Zhang, et al. (+11)
- **Published:** 2025-12-09 (label: not new as of this run — standing reference)
- **Relevance:** Empirical coordination metrics across Single / Independent / Centralized /
  Decentralized / Hybrid topologies; identifies **topology-dependent error amplification**,
  redundancy, and coordination overhead. Direct evidence base for the ≥3-provider / ≥4-family
  diversity policy and for choosing the gateway's topology. Candidate to cite in ADR-10 (vote
  model) and the METAHARNESS operating model when those are next revised.

## §3 Deferred ingestion plan ("begins once our heart's beating again")

Ingestion is gated on the **Orchestration Phase 0 substrate bridge** being live
(publish → provenance → independent verify → query → fork-visible → no privileged
verifier). Until that heartbeat passes, these stay staged records, not committed knowledge.

**Step 0 — acquire binaries (run locally now; my sanctioned downloader landed them in a
sandbox I can't bridge to the repo):**

```bash
mkdir -p FLOSS/docs/research/intake_raw/2026-06-17-arxiv
curl -L -o "FLOSS/docs/research/intake_raw/2026-06-17-arxiv/2510.10047-swarmsys.pdf"                      https://arxiv.org/pdf/2510.10047
curl -L -o "FLOSS/docs/research/intake_raw/2026-06-17-arxiv/2512.08296-science-of-scaling-agent-systems.pdf" https://arxiv.org/pdf/2512.08296
# then checkpoint:
sha256sum FLOSS/docs/research/intake_raw/2026-06-17-arxiv/*.pdf > FLOSS/docs/research/intake_raw/2026-06-17-arxiv/SHA256SUMS
```

**Step 1 (heartbeat live) — distill:** extract claims as KnowledgeTriples; label each
Verified / Specified / Aspirational against the paper's own evidence, not our hopes for it.

**Step 2 — submit as Claims** through `metacoordinator_mcp` with provenance packets citing
the typed arXiv identifier and canonical URL as the non-packet evidence root (add a DOI only
when independently verified); let the source chain + (eventually) the
Holochain integrity zome validate. No claim enters canon on LLM consensus alone — one
primary-source check outweighs model agreement.

**Step 3 — promote** only what passes the evidence gate (observed need / ≥3-case pattern /
dated milestone). Default on doubt: leave staged, do not promote.

## Anti-sycophancy note
Neither paper is new since the last run; both are 2025 standing references re-surfaced for
relevance, not fresh signal. Logged as such so the corpus doesn't inflate their novelty.
