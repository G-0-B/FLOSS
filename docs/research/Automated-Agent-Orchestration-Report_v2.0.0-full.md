---
id: "research-report-agent-orchestration"
version: "2.0.0"
kind: "technical_report"
status: "active"
supersedes: ["1.0.0"]
truth_status: "verified"
updated: "2026-03-23"
evidence_sources:
  - "Perplexity Deep Research task (March 2026) — primary source for v2.0.0"
  - "Silo-Bench (arxiv 2603.01045v1) — coordination overhead empirical data"
  - "AMRO-S (arxiv 2603.12933) — ACO agent routing at scale"
  - "CodeCRDT (arxiv 2510.18893) — CRDT concurrent agent coding"
  - "MAS-ProVe (arxiv 2602.03053) — process verification limits"
  - "Holochain roadmap (holochain.org/roadmap) — 0.6.1/0.7.x status"
  - "FOSS AI personal assistant landscape scan (Claude, March 2026)"
  - "Project knowledge cross-validation against v1.0.0"
upgrade_path:
  - step: "refresh_sources_and_leaderboards"
    required: false
    cadence: "quarterly"
  - step: "validate_silo_bench_replication"
    required: false
    cadence: "when new scaling studies publish"
rollback_plan:
  trigger_metric: "source_obsolescence_ratio"
  trigger_threshold: 0.5
  action: "revert to v1.0.0; mark deprecated claims"
capability_truth_model:
  verified: "implemented + tested (or externally validated) with links"
  specified: "designed; may exist; not validated"
  aspirational: "vision/research direction"
  unverified: "lacks evidence or attribution"
license: "Compassion Clause + Apache-2.0 compatible"
friction_tier: "medium"
---

# Automated Agent Orchestration for Decentralized, Open-Source AI Development v2.0.0

**A Technical Synthesis — Updated March 23, 2026**

**Scope:** Technically grounded patterns you can build *now*, plus honest limitations, a substrate-first plan, and an integrated FOSS personal assistant landscape.

---

## What Changed from v1.0.0

### Critical New Findings

| Finding | Source | Impact on FLOSSI0ULLK |
|---------|--------|----------------------|
| At k=50 agents, coordination overhead eliminates ALL parallelization gains | Silo-Bench (March 2026) | Design constraint: small coordinated teams (k≤5), not swarms |
| Process-level verification does NOT consistently improve LLM agent performance | MAS-ProVe (Feb 2026) | Shift Definition of Done toward output verification, not trajectory verification |
| ACO-based LLM routing achieves 4.7x speedup at 1,000 concurrent agents | AMRO-S (March 2026) | Applicable to MetaCoordinator multi-LLM model selection |
| CRDT concurrent coding: 100% convergence, zero merge failures across 600 trials | CodeCRDT (Oct 2025) | Validates CRDT layer for agent task allocation |
| IPFS peer availability declined from 60% to 40%; 50% of peers online <4 days | IFIP 2025 study | Reinforces ADR-N multi-pinning requirement |
| SourceCred effectively discontinued — gaming proved persistent | sourcecred.io | Remove from consideration; Colony.io reputation survives |
| All decentralized agent tokens declined dramatically | Market data Feb 2026 | Validates FLOSSI0ULLK's non-token economic approach |
| Ocean Protocol exited ASI Alliance (Oct 2025) — token mergers fracture on identity | Ocean blog | Validates "forks are first-class" principle |
| Holochain 0.6.1 at 64% completion; 0.7.x at 37%; Wind Tunnel production-ready | holochain.org/roadmap | More precise planning for walking skeleton |
| AD4M v0.10.1 integrates local AI inference (DeepSeek, Qwen, Whisper, Ollama) | coasys/ad4m releases | Plane B can run LLMs locally — privacy-preserving coordination |
| OWASP Top 10 for Agentic Apps + 82:1 agent-to-human ratio with 45.6% shared API keys | OWASP/ISACA 2026 | Security posture of deployed agent systems is deeply concerning |

### Corrections to v1.0.0 Assumptions

- v1.0.0 warned about scaling limits qualitatively → v2.0.0 has Silo-Bench empirical data (k=50 wall)
- v1.0.0 assumed process verification beneficial → v2.0.0 corrects: MAS-ProVe shows inconsistent/high variance
- v1.0.0 referenced reputation systems generically → v2.0.0 confirms Colony.io strongest, SourceCred dead
- v1.0.0 noted IPFS concerns → v2.0.0 adds quantitative availability decline data
- v1.0.0 referenced token economics cautiously → v2.0.0 documents universal token decline across space

---

## Executive Summary

Full-stack "agent-centric, decentralized, value-aligned orchestration" is still frontier work, but building blocks have matured significantly since v1.0.0. The most important new constraint: **Silo-Bench proves coordination overhead kills parallelization gains at k=50 agents.** Only sublinear-communication approaches — stigmergy, CRDTs (zero coordination at runtime), and gossip protocols (O(n log n)) — can plausibly scale to hundreds or thousands of agents.

The evidence-supported layered architecture is:

1. **Trust — Holochain:** DNA validation, Warrants, membrane proofs, source chains
2. **State Sync — CRDTs:** Zero-coordination convergence (CodeCRDT validated at 100%)
3. **Discovery — Gossip Protocols:** O(n log n) via libp2p GossipSub
4. **Task Allocation — Contract Net + ACO:** CNP for heterogeneous tasks; ACO pheromone routing at 1,000+ scale
5. **Governance — Reputation-Weighted:** Colony.io model (domain-specific, non-transferable, decaying)
6. **Semantic Interop — AD4M:** Perspectives, Languages, Social DNA across protocols
7. **Identity — KERI:** Self-certifying identifiers with pre-rotation
8. **Persistence — IPFS + Filecoin:** Content-addressed storage with economic persistence incentives

---

## Part 1: Multi-Agent Coordination Algorithms

### Comparative Analysis

| Algorithm | Decentralization | Fault Tolerance | Scalability | Comm. Overhead | FLOSSI0ULLK Fit |
|-----------|-----------------|-----------------|-------------|----------------|-----------------|
| Contract Net / Auction | Moderate | High | High — O(n) per task | O(n) per announcement | High: dynamic heterogeneous agents |
| BDI Architecture | Low–Moderate | High | Moderate (<100) | Low | High for explainability + auditability |
| ACO / Swarm (AMRO-S) | Very High | Very High | Very High (1000+) | Low (environment only) | Excellent for LLM routing |
| MARL (CTDE) | Execution only | High | High | Zero at execution | Poor: agent replacement breaks coordination |
| Blackboard | Low (shared state) | Moderate | Limited | Low (indirect) | Good for complex problem-solving |
| Stigmergy | Very High | Very High | Very High | Very Low | Excellent for massive async networks |
| Market-Based | High | Moderate | High | Moderate | Good with payment infrastructure |
| AgentNet++ Hierarchical | High | High | 1000+ agents | Low | 23% higher task completion |
| Gossip-Based | Very High | Very High | High | O(n log n) | Excellent under uncertainty |
| CRDTs | Full | Partition-tolerant | Very High (1000+ nodes) | Zero coordination | Ideal for concurrent shared state |

### Key New Patterns

> **Truth status note**: Each pattern is `Specified` externally (published paper with reference benchmarks) and `Unverified` in FLOSSI0ULLK context (not adopted or tested in this repo).

**AMRO-S (March 2026)** [External: Specified | FLOSSI0ULLK: Unverified]**:** Applies Ant Colony Optimization directly to LLM multi-agent routing. Models agent pool as layered directed graph, uses task-specific pheromone matrices + quality-gated async updates + semantic SLM router. 4.7x speedup at 1,000 concurrent processes. Directly applicable to MetaCoordinator model selection.

**CodeCRDT (Oct 2025)** [External: Specified (600-trial benchmark) | FLOSSI0ULLK: Unverified]**:** Multiple LLM agents code in parallel on shared Yjs CRDT document. TODO-claim protocol with LWW semantics resolves concurrent claims deterministically. 100% convergence, zero merge failures across 600 trials, median propagation latency 50ms.

**AgentNet++ (NeurIPS 2025 extension)** [External: Specified (peer-reviewed) | FLOSSI0ULLK: Unverified]**:** Hierarchical DAG-structured agent network achieving 23% higher task completion rates and 40% less communication overhead at 1,000+ scale. Addresses the Silo-Bench wall through pre-designed hierarchy.

**DecentLLMs (July 2025)** [External: Specified | FLOSSI0ULLK: Unverified]**:** Leaderless BFT for LLM multi-agent systems using Geometric Median algorithm for Byzantine-robust evaluation without leader nodes. Eliminates leader-targeted attacks.

### The Silo-Bench Constraint (Critical)

Silo-Bench (March 2026) provides the most rigorous empirical evidence:

- At **k=2**, multi-agent systems lose **15–49%** of single-agent performance
- At **k=50**, coordination overhead **eliminates all parallelization gains entirely**
- Spontaneous leader emergence actively hurts at scale (aggregator overwhelmed)

**Design implication:** Walking skeleton should target k≤5 active coordinating agents. RSA (Recursive Self-Aggregation) across Claude + ChatGPT + Grok is correctly sized. Larger agent pools require hierarchical decomposition (AgentNet++ pattern) or stigmergic/CRDT coordination to avoid the overhead wall.

---

## Part 2: Infrastructure Layer

### Holochain Status (March 2026)

| Version | Status | Key Features |
|---------|--------|--------------|
| 0.5.0 | Released April 2025 | Kitsune2 networking rewrite, Wind Tunnel |
| 0.6.0 | Released Nov 2025 | Warrants, memproof security, coordinator updates |
| 0.6.1 | In progress (64%) | Performance improvements, per-app networking |
| 0.7.x | In progress (37%) | Data model consistency, HDK stability, DNA migration |

Kitsune2 fixed DHT sync from 30+ minutes to reliable. Wind Tunnel (production-ready Jan 2026) enables automated scale testing. Unyt pricing oracle launching as first production-grade hApp (March 2026). Team delivers 30 story points per sprint.

**Limitations:** Still beta; APIs change between major versions. No native token layer (intentional). 4 MB entry size limit. Small production hApp ecosystem. DHT sharding behind experimental flags.

### AD4M v0.10.1 (February 2025)

Three core primitives: Agents (sovereign DID-identified instances), Languages (protocol abstractions), Links (signed RDF triples in Perspectives).

**Critical new capability:** Local AI inference — AD4M apps can run DeepSeek, Qwen, Whisper, Ollama-compatible models with CUDA/Metal GPU support. Preserves privacy while enabling AI-augmented coordination.

Social DNA encodes community rules in Prolog, evaluated locally. Different Neighbourhoods can have different rules (pluralistic alignment).

**Limitations:** Pre-1.0; Windows binary not yet available. Synergy Engine not production-ready. Small developer community.

### IPFS / IPLD / Filecoin

DASL initiative improved cross-implementation interop. IETF Internet Draft submitted.

**Critical data:** 2025 IFIP study found peer availability declined from 60% to 40%, with 50% of peers online <4 days. This validates ADR-N's multi-pinning and multi-gateway approach.

Filecoin: 3.0 EiB capacity at ~$0.19/TB/month. F3 Fast Finality upgrade makes it viable for faster confirmation. Strongest decentralized persistence guarantees.

### Supporting Infrastructure

| System | Role | Status | License |
|--------|------|--------|---------|
| libp2p | Networking substrate (IPFS, ETH, Polkadot, Holochain tx5) | Production | MIT/Apache-2.0 |
| GunDB | Offline-first CRDT graph database in browsers | Production | SEE LICENSE |
| Ceramic | Mutable DID-authenticated data streams | Production | MIT |
| Nostr | Key-sovereign censorship-resistant messaging | Active | Public domain |
| Matrix | Federated DAG-based E2E encrypted rooms | Production (gov deployments) | Apache-2.0 |
| SSB/PZP | Offline-capable identity-centric gossip | Active | Various FOSS |
| KERI | Self-certifying identifiers, pre-rotation, witnesses | Production (KERIpy 1.1.17+) | Apache-2.0 |

---

## Part 3: FOSS AI Personal Assistant Landscape (March 2026)

### Tier 1: Strongest FLOSSI0ULLK Alignment

| System | What It Does | License | Truth Status | Integration Surface |
|--------|-------------|---------|-------------|-------------------|
| **OpenClaw** | Self-hosted autonomous AI assistant, 68K+ GitHub stars, persistent markdown memory, 50+ integrations, MCP support | MIT | Verified | MCP server/client, local inference via any OpenAI-compatible backend, markdown memory maps to ADR artifacts |
| **OVOS + HiveMind** | Privacy-first voice assistant OS with distributed satellite network | Apache-2.0 (OVOS) / AGPL-3.0 (HiveMind v4+) | Verified | HiveMind distributed topology maps to agent-centric design, plugin architecture extensible |
| **LocalAI** | Open-source inference engine with P2P federation via libp2p, MCP support, built-in agents | MIT | Verified | P2P inference substrate sharing IPFS's libp2p, MCP tool provider, agent system with RAG |
| **Khoj** | Self-hostable AI second brain with RAG, custom agents, scheduled automations | AGPL-3.0 | Verified | Knowledge RAG over personal docs, proactive automation, Obsidian/Emacs plugins |

### Tier 2: Good Foundation, Bridge Work Required

| System | What It Does | License | Truth Status | Notes |
|--------|-------------|---------|-------------|-------|
| **PAI (Daniel Miessler)** | Goal-oriented persistent AI with identity-as-files | MIT | Verified | Claude Code-centric (Plane A), identity files map to seed packets |
| **PicoClaw** | Ultra-lightweight Go assistant, <10MB, runs on $10 hardware | MIT | Specified | Maps to Infinity Bridge edge nodes |
| **OpenJarvis** | Local-first agent framework, efficiency-focused | Unknown | Specified | Intelligence Per Watt research, learning loops from local traces |
| **Leon AI** | Node.js/Python personal assistant with NLP/TTS/STT | MIT | Specified | Extended development cycles, unclear production readiness |

### Integration Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│  OpenClaw (messaging bridge) ←→ OVOS (voice)        │
├─────────────────────────────────────────────────────┤
│              Coordination (Plane A)                  │
│  LangGraph / OpenClaw orchestration                  │
│  MCP ←→ A2A protocols                                │
├─────────────────────────────────────────────────────┤
│              Knowledge & Automation                  │
│  Khoj (RAG + agents + scheduling)                    │
│  Amazon Rose Forest (distributed vector DB)          │
├─────────────────────────────────────────────────────┤
│              Inference Substrate                     │
│  LocalAI (P2P federation via libp2p)                 │
│  AD4M local inference (DeepSeek/Qwen/Whisper)        │
├─────────────────────────────────────────────────────┤
│           Runtime Truth (Plane B)                    │
│  Holochain (validation, warrants, source chains)     │
│  AD4M (semantic interop, Social DNA)                 │
│  KERI (identity, delegation chains)                  │
│  IPFS/Filecoin (persistence)                         │
└─────────────────────────────────────────────────────┘

NONE of the Tier 1/2 systems implement Plane B.
That is FLOSSI0ULLK's unique contribution.
```

---

## Part 4: Case Studies (Honest Assessment)

| Project | What Worked | What Failed | Status | Key Lesson |
|---------|------------|------------|--------|-----------|
| **Autonolas** | 9.9M A2A transactions; Mech Marketplace; real audits | DeFi-concentrated; OLAS token ~$0.03 | Alive, shipping | On-chain metrics matter; hasn't escaped DeFi |
| **ElizaOS** | 50K+ agents; strong OSS adoption; Stanford partnership | AI VC was theater; weak decentralization | Alive, active | Framework value > token speculation |
| **SingularityNET** | Functional marketplace; 40 partnerships | ASI Alliance fracture; AGIX down 90%+ | Alive, diminished | Token mergers fragment on identity |
| **Fetch.ai** | First AI-to-AI payment demo (Dec 2025) | Financial difficulties; acquired by Assembl.ai | Alive, struggling | Demos ≠ production deployments |
| **Ocean Protocol** | C2D innovation; 1.4M nodes; GPU partnerships | ASI Alliance exit; no marketplace flywheel | Alive, pivoting | Privacy tech needs demand-side |
| **Colony.io** | Reputation governance mechanism (non-transferable, decaying) | No killer use case; limited adoption | Alive, niche | Solutions need problems |
| **Gitcoin** | $50M+ distributed; QF proven at scale; 270K supporters | GTC ~$0.10; governance "hectic, confusing" | Alive, impactful | QF works; token value ≠ impact |
| **Holochain** | Kitsune2 fixed reliability; Warrants; Wind Tunnel | 7+ years, no mainstream adoption; HoloFuel delays | Alive, maturing | Technical excellence ≠ adoption |
| **LangGraph** | Production standard; checkpointing; time-travel debugging | Single-machine; not decentralized | Dominant | Centralized works until it doesn't |

---

## Part 5: Unsolved Problems (Claim Truth Model: Unverified)

1. **Scalability wall** — Only sublinear-communication approaches can plausibly scale beyond k=50. Hierarchical decomposition (AgentNet++) needs validation at 50–100 scale.

2. **LLM non-determinism in consensus** — Process verification doesn't work (MAS-ProVe). Novel failure modes when LLM agents participate in BFT consensus.

3. **Cross-membrane agent migration** — Agent reputation/credential transfer between Holochain DNAs or AD4M Neighbourhoods lacks production validation despite KERI/DID theoretical support.

4. **Economic sustainability without tokens** — Every decentralized token has declined. Service fees, subscriptions, or QF for public goods remain untested alternatives at scale.

5. **Centralization gravity** — All major agent frameworks use centralized LLM APIs. IPFS availability declines without economic incentives. Even open-source projects maintain centralized control. AD4M's local AI is a partial answer but local models underperform centralized APIs.

6. **CI/CD for decentralized agent behavior** — No mature purpose-built framework exists. Wind Tunnel is closest for Holochain-specific testing.

7. **FLOSSI0ULLK integration path** — Bridging Holochain Rust validation with AD4M Deno/V8 Language runtime at scale; validating full stack under adversarial conditions using Wind Tunnel.

---

## Part 6: Actionable Recommendations

### Walking Skeleton Design Constraints (Updated)

- **Team size cap: k≤5** active coordinating agents (Silo-Bench empirical constraint)
- **Testing strategy:** Output verification > process verification (MAS-ProVe correction)
- **IPFS strategy:** Multi-pinning mandatory; ≥2 pinning proofs per artifact (availability decline data)
- **Governance mechanism:** Colony.io-style reputation (non-transferable, domain-specific, temporally decaying)
- **No token economics** — service model or QF; avoid speculative token dependency
- **Hierarchical decomposition** for scaling beyond k=5 (AgentNet++ pattern)

### FOSS Personal Assistant Integration Path

1. **Immediate:** Complete OpenClaw evaluation (installed in WSL2) — test MCP integration, assess as MetaCoordinator orchestration layer
2. **Short-term:** Validate LocalAI P2P on local hardware — 2-node federation test, confirm libp2p interop
3. **Short-term:** Evaluate Khoj self-hosted as knowledge layer — test against document corpus, compare to Pieces LTM
4. **Medium-term:** OVOS + HiveMind for voice interface + distributed satellite network
5. **All phases:** None of these solve Plane B — FLOSSI0ULLK's Holochain + AD4M + KERI stack is the unique contribution

### Phase 0 Gate (Unchanged, Reinforced)

Validate substrate bridge before scaling orchestration:
1. Publish ADR/decision artifact to code substrate
2. Emit provenance entry referencing its hash + signatures
3. Verify independently from another node
4. Query: Agent B discovers the entry via `query_triples` without knowing the hash

Pass criteria: convergence across ≥3 nodes; conflict produces visible fork; verification requires no privileged access; content-based discovery works without prior hash knowledge.

If Phase 0 fails, **pivot substrate**.

---

## Open Research Questions

1. How do pre-designed hierarchical architectures (AgentNet++) perform at k=50–100?
2. Can AMRO-S ACO routing be applied to MetaCoordinator multi-LLM backend selection?
3. Can CodeCRDT TODO-claim protocol be adapted for FLOSSI0ULLK agent task allocation?
4. What verification approaches provide probabilistic guarantees for LLM non-determinism in BFT?
5. Can decentralized networks sustain without tokens via QF, service fees, or subscription?
6. Does coordination mechanism choice measurably affect values expressed by resulting agent network?
7. Can Social DNA encode ethical constraints that meaningfully constrain LLM agent behavior?

---

## Appendix A: How to Cite

```yaml
evidence_sources:
  - "research-report-agent-orchestration@2.0.0"
```

## Appendix B: Full Perplexity Source Report

The complete unedited Perplexity deep research output (455 lines, fully cited) is preserved as the primary evidence source for this synthesis. All claims in this document trace to citations in that source or to project knowledge cross-validation.
