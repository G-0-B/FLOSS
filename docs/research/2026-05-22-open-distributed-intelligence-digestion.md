# Open Distributed Intelligence Research - Intake Digestion

```yaml
id: "2026-05-22-open-distributed-intelligence-digestion"
date: "2026-05-22"
type: "research_distillation"
source_intake: "FLOSS/docs/research/intake_raw/2026-05-22-root/reports/Recent Open Distributed Intelligence Research.md"
status: "Partial live verification; not canon promotion"
truth_status:
  intake_read: "Verified"
  primary_source_spot_check: "Verified"
  comprehensive_literature_review: "Not performed"
  architecture_decisions: "Not promoted"
```

## Executive Digest

The raw report is useful as a seed map, but its value is not "here is a list of
cool decentralized AI things." The useful pattern for FLOSSI0ULLK is that the
field is converging on five separable layers:

1. Agent-centric substrate and social graph: Holochain plus AD4M/ADAM.
2. Decentralized coordination and memory: AgentNet, DecentMem, DAMCS, KARMA.
3. Federated retrieval: RAGRoute and adjacent federated RAG work.
4. Open distributed compute and verification: INTELLECT-2 / PRIME-RL / TOPLOC.
5. Agent interoperability: MCP, A2A, AGNTCY ACP/OASF.

This reinforces the existing FLOSSI0ULLK direction: do not build a single
central orchestrator; compose peer-capable agents through explicit identity,
source-chain provenance, routed retrieval, and symbolic validation gates.

## Source Boundary

This pass did not verify every item in the raw report. It spot-checked
architecture-relevant claims against primary or near-primary sources available
on 2026-05-22. Items not listed below remain seed leads, not evidence.

## Corrections And Drift From The Raw Report

| Raw-report claim area | Digested state |
|---|---|
| Holochain latest stable | The report's Holochain 0.6 line is directionally right, but current developer guidance says Holochain 0.6.1 is recommended for general use. Treat exact version numbers as live-check required. |
| AD4M Social DNA | Current AD4M docs describe Social DNA around SHACL shapes in Perspectives/Neighbourhoods and also expose an MCP server. Existing local notes mention Prolog-style inference examples. Before implementing against AD4M, verify the exact current rule-engine/API path in `coasys/ad4m`. |
| RAGRoute metrics | The arXiv v2 abstract reports up to 80.65% communication-volume reduction and 52.50% latency reduction while matching query-all accuracy. The raw report's older figures should not be reused without version pinning. |
| "OpenCLAW-P2P" | There is a 2026 arXiv preprint line, but it should stay watchlist-only until code, license, maintainership, and reproducibility are checked. Do not treat it like a mature substrate. |
| AntSeed | Official site supports the broad P2P inference-marketplace claim, but security, routing, settlement, and actual node behavior still need an implementation audit before architectural use. |

## High-Signal Findings

| Lane | Verified evidence | FLOSSI0ULLK relevance | Action |
|---|---|---|---|
| Holochain 0.6.x | Holochain's compatibility table recommends 0.6.1 for general use. | Confirms the substrate is live and version-sensitive; do not preserve stale "when Holochain is live" language. | Keep Holochain version checks explicit in any substrate-bridge work. |
| AD4M / ADAM | AD4M docs describe local agent-owned data, GraphQL plus MCP exposure, Perspectives as RDF-like graphs with cryptographic provenance, and Neighbourhoods as shared graph spaces. Coasys describes DID-based agents and signed Expressions. | Strongest anti-duplication pressure against hand-rolling identity, semantic graph, and shared-neighbourhood runtime under `packages/`. | Before new source-chain/semantic graph work, run an AD4M fit check. |
| AgentNet | arXiv paper verifies decentralized RAG-based agents in dynamic DAGs with no central orchestrator, adaptive graph topology, and retrieval-based skill memory. | Supports the existing "router, not controller" posture and the inline reasoning ensemble's selective mode routing. | Use as design reference for peer graph topology, not as a drop-in dependency. |
| DecentMem | Live search surfaced a new 2026-05-21 arXiv paper on per-agent decentralized memory pools, claiming token reduction and accuracy gains across MAS frameworks including AgentNet. | Highly relevant to FLOSSI0ULLK memory harness and `agentmemory`/shared-memory boundary discipline. | Add to next memory-harness research queue; do not adopt until paper/code are inspected. |
| DAMCS | arXiv verifies decentralized adaptive knowledge graph memory plus structured communication for multi-agent cooperative planning. | Directly maps to semantic memory, KnowledgeTriple, and structured communication between agents. | Treat as a design pattern for local knowledge graph memory, especially around what to share vs keep local. |
| KARMA | OpenReview verifies a NeurIPS 2025 spotlight multi-agent KG enrichment system with nine specialized agents and conflict-resolution roles. | Useful for knowledge-ingestion workflows and autonomous synthesis review, but needs symbolic validation before any automatic canon writes. | Reuse role decomposition ideas; keep LLM output below validation gates. |
| RAGRoute | arXiv v2 verifies federated RAG source routing with lightweight classification rather than querying all sources. | Strong fit for Context Daemon and corpus router: route first, retrieve second. | Prototype routing policies over local corpora before vector-store expansion. |
| INTELLECT-2 | Prime Intellect verifies permissionless distributed RL infrastructure with decentralized rollout workers, TOPLOC validation, GRPO training workers, and Shardcast weight broadcast. | Long-horizon relevance to open compute and verifier design; not immediate for Phase 1. | Track verification mechanisms, especially TOPLOC-style untrusted-worker validation. |
| MCP | Official MCP docs define it as an open standard for connecting AI apps to external systems, tools, data, and workflows, with broad client/server support. | Current FLOSSI0ULLK MCP surfaces are aligned; MCP is the right tool/context plane. | Continue exposing local gateway and shared surfaces through MCP. |
| A2A | Google announced A2A as an open protocol for agent-to-agent communication, using HTTP/SSE/JSON-RPC and complementing MCP. | A2A is a possible future inter-agent handshake plane, not a replacement for MCP or source-chain validation. | Watch for production maturity and bridge only after concrete interop need. |
| AGNTCY ACP/OASF | AGNTCY docs verify ACP for agent runs/threads/interrupts and OASF for agent schemas/capability discovery. | Strong discovery/schema complement to FLOSSI0ULLK skill and voter manifests. | Track as a schema/discovery layer; avoid overfitting until local manifests stabilize. |

## FLOSSI0ULLK Implications

### 1. AD4M stays the main duplication checkpoint

The report reinforces the prior AD4M audit: FLOSSI0ULLK's genuinely novel work
is analog multi-model consensus, hashline verification, blast-radius-conditioned
quorum, CFIS, and metaharness discipline. The at-risk duplication zone is still
identity, shared semantic graph, neighbourhood runtime, and protocol adapter
plumbing.

Concrete rule: before expanding `packages/source_chain/`, `packages/memory/`, or
semantic graph runtime code, check whether AD4M already provides the substrate
shape and whether FLOSSI0ULLK should be an AD4M Language/Social-DNA/sidecar
rather than another local runtime.

### 2. Memory should become decentralized by default

AgentNet, DecentMem, and DAMCS all push against a single central memory store.
The emerging pattern is per-agent memory with selective sharing, routing, and
knowledge-graph structure. That fits FLOSSI0ULLK's memory boundary:

- repo canon wins for load-bearing truth;
- `agentmemory` is useful retrieval/federation infrastructure;
- per-agent memories should remain local unless promoted through validated
  markdown/spec/ADR/source-chain paths.

2026-05-23 follow-on: the DecentMem/DAMCS comparison landed at
`FLOSS/docs/research/2026-05-23-decentmem-damcs-memory-harness-delta.md`.
Result: add a memory-boundary contract and selective-sharing gate as spec
candidates; keep `agentmemory` as Plane A recall/federation infrastructure and
keep repo canon/source-chain validation as the promotion path.

### 3. Federated retrieval belongs in the Context Daemon path

RAGRoute is the clearest direct hit for the retrieval harness. FLOSSI0ULLK
already says corpus routing comes before vector retrieval. RAGRoute gives a
paper-backed version of that same posture: select relevant sources before
querying everything.

Near-term use: do not add one huge vector database as the first retrieval
upgrade. First improve `context_router.py` and local corpus labels so a query
can choose between canon, architecture, code, research, source-chain, memory,
and reference surfaces.

2026-05-22 implementation note: this prototype landed in
`FLOSS/scripts/context_router.py`, `FLOSS/shared-context-surface.json` v0.3.0,
and `FLOSS/docs/research/2026-05-22-context-router-routing-policy.md`. The next
step is retrieval-inside-corpus, not a global vector DB.

### 4. Protocols should be layered, not merged

The raw report risks blending MCP, A2A, AGNTCY, and NANDA into one generic
"agent protocol" bucket. The digest should keep them separate:

- MCP: tool/context/app access.
- A2A: agent-to-agent task and artifact exchange.
- AGNTCY ACP/OASF: agent run protocol plus capability/schema discovery.
- NANDA: watchlist; not enough primary-source verification in this pass.

FLOSSI0ULLK should expose MCP now, track A2A and AGNTCY for bridges, and never
let any protocol bypass symbolic validation or source-chain provenance.

### 5. Open distributed compute is future-relevant but not current gating

INTELLECT-2 matters because it proves a real open effort around permissionless
distributed RL with explicit validation of untrusted workers. This is relevant
to eventual FLOSSI0ULLK open compute/verifier design, but it should not distract
from the current substrate bridge and KnowledgeTriple path.

## Watchlist / Verification Gaps

| Item | Why it stays watchlist |
|---|---|
| AgentNet++ | Needs direct paper/code quality review and comparison to AgentNet; raw report metrics should not be adopted yet. |
| PrivateDFL / FedAnil | Relevant to privacy-preserving learning, but not immediately actionable until FLOSSI0ULLK has a concrete training/federated-learning lane. |
| Vector DB comparison table | Too generic. FLOSSI0ULLK needs corpus routing and provenance first; vector DB choice is downstream. |
| CIP / Weval / MIT collective intelligence | Governance-relevant, but this pass did not verify operational details deeply enough to affect CFIS or ADRs. |
| II-Commons | Potentially adjacent to layered knowledge infrastructure; needs source and code audit. |
| OpenCLAW-P2P | Interesting but evidence maturity unclear; keep below adoption threshold. |
| AntSeed | Marketplace direction is relevant, but implementation/security audit is required before use. |
| MIT NANDA | The report's NANDA claim was not primary-source verified here. Keep as a protocol watchlist item. |

## Sources Checked 2026-05-22

- [Holochain 0.6 compatibility table](https://developer.holochain.org/resources/compatibility/holochain-0.6/)
- [AD4M docs introduction](https://docs.ad4m.dev/)
- [ADAM / Coasys overview](https://coasys.org/adam)
- [AgentNet arXiv:2504.00587](https://arxiv.org/abs/2504.00587)
- [DecentMem arXiv:2605.22721](https://arxiv.org/abs/2605.22721)
- [DAMCS arXiv:2502.05453](https://arxiv.org/abs/2502.05453)
- [KARMA OpenReview](https://openreview.net/forum?id=k0wyi4cOGy)
- [RAGRoute arXiv:2502.19280](https://arxiv.org/abs/2502.19280)
- [INTELLECT-2 official Prime Intellect blog](https://www.primeintellect.ai/blog/intellect-2)
- [MCP official introduction](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Google A2A announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [AGNTCY Agent Connect Protocol docs](https://docs.agntcy.org/syntactic/connect/)
- [AGNTCY ACP spec](https://spec.acp.agntcy.org/)
- [AGNTCY OASF docs](https://docs.agntcy.org/pages/oasf.html)
- [AntSeed official site](https://antseed.com/)
- [OpenCLAW-P2P arXiv:2604.19792](https://arxiv.org/abs/2604.19792)
