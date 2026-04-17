# FLOSSI0ULLK Holistic Architecture — Living Reference

**The Most Plausible Best Latest Unified View**

```yaml
id: "flossi0ullk-holistic-architecture"
version: "0.2.0"
kind: "architecture_reference"
status: "Active"
updated: "2026-04-16"
truth_status: "Specified"
evidence_sources:
  - "Master Metaprompt v1.3.1 (canonical kernel)"
  - "docs/governance/spine-v0.5.md"
  - "docs/adr/ADR-8-radicle-dev-substrate.md"
  - "docs/architecture/AGENTIC_OPERATING_MODEL.md"
  - "docs/superpowers/specs/2026-04-12-local-agent-node-design.md"
  - "packages/source_chain/cell.py"
  - "packages/metacoordinator_mcp/voters.py"
```

---

## 1. What FLOSSI0ULLK Is

A decentralized coordination architecture for universal flourishing — enabling human, AI, and future cognitive beings to build shared, verifiable knowledge without centralized control.

**Core equation**: Sovereignty + Interconnection = Flourishing (not dominance)

**What it is NOT**: A product, a company, a single AI system, or a platform. It is a **protocol** — a way of coordinating that any participant can join, verify, and extend.

---

## 2. Foundation Stack

| Layer | Component | Purpose | Status |
|-------|-----------|---------|--------|
| **A0** | Radicle dev-plane substrate | Canonical code collaboration, patches, review/social artifacts | Accepted policy, bridge not yet proven |
| **0** | Holochain agent-centric DHT | Runtime data sovereignty, cryptographic validation | Specified (DNA scaffolded) |
| **0.5** | Local source chain + MCP bridge | Immediate claim/vote/decision traceability and coordination | Implemented in `packages/` |
| **1** | ADR system | Persistent decision memory across sessions | Active |
| **2** | Semantic CRDT + federated retrieval | Conflict-aware knowledge composition and corpus routing | Partially specified |
| **3** | Symbolic-first validation | Formal logic gates neural processing | Specified (Rust code ready) |
| **4** | Multi-agent orchestration | Specialized agents, policy-gated execution, consensus routing | Partially implemented |
| **4.5** | Harness optimization | Optimize routing, prompts, traces, and policies | Specified |

**Key principle**: Each layer validates the one above. Neural processing never bypasses symbolic validation. Code implements specifications, never the reverse.

---

## 3. Symbolic-First Architecture (Technical Core)

```
BEFORE (neural-first):  Query → LLM generates → maybe check → return
AFTER (symbolic-first): Query → Parse formal → KG reasoning → LLM formats → return
                                    ↓
                         Validate against ontology (integrity zome)
```

**Implementation**: `FLOSS/ARF/SYMBOLIC_FIRST_CORE.md` contains production-ready Rust code for:
- Holochain integrity zome with validation rules
- Knowledge triple structure with provenance
- Ontology types and relations
- Logical inference system
- Coordinator zome for operations

**Rule**: LLM extractions require 3+ validator consensus. No unvalidated triples enter the knowledge graph.

---

## 4. Two-Plane Architecture

| Plane | Purpose | Canonical stack | Authority |
|-------|---------|-----------------|-----------|
| **A: Dev Meta-Coordinator** | Code collaboration, patches, review, CI, traces, task routing | `Radicle` + local source chain/MCP + GitHub mirror | Outputs are artifacts, not runtime truth |
| **B: Runtime Meta-Coordinator** | Agent-centric runtime truth, integrity validation | `Holochain` cells / DHT / warrants | Per-agent source chains, eventual consistency |

**Bridge rule**: Plane A may publish into Plane B but CANNOT bypass Plane B validation.

**Operational note**: the current active bridge is the file-based source chain and consensus gateway under `packages/`, not a fully landed Holochain runtime.

---

## 5. Key Subsystems

### 5a. Rose Forest (ARF)
The Holochain DNA implementing the distributed knowledge graph.
- **Entry types**: RoseNode, KnowledgeEdge, BudgetEntry, ThoughtCredential
- **Schemas**: `FLOSS/docs/specs/` (JSON Schema + spec.md pairs)
- **Code**: `FLOSS/ARF/dnas/rose_forest/` (integrity + coordinator zomes)

### 5b. VVS (Virtual Verifiable Singularity)
Coordination layer for autonomous, verifiable systems.
- Autonomy Kernel, BudgetEngine, RuleEngine
- Proof-Carrying Code, zk-Attested Models
- AutoConstitution for self-modification governance

### 5c. YumeiCHAIN / Yumeichan
Ternary connotation intelligence — knowledge representation beyond binary.
- Ternary framework: positive/negative/neutral connotation
- Semantic vector architecture
- Integrated with symbolic validation layer

### 5d. ConversationMemory
The proven working component — transmits understanding across AI conversations.
- **Status**: Verified (3/4 tests pass)
- Uses MultiScaleEmbedding (fractal frames)
- Composition across multiple agents demonstrated

### 5e. Local Agent Node
The current working coordination seam on the dev plane.
- `packages/source_chain/` stores file-based per-cell source chains
- `packages/metacoordinator_mcp/` routes claims, votes, and decisions
- `.claude/settings.json` + hooks submit substantive edits into the local consensus path
- `Groq` + `Cerebras` already act as cheap background voters via LiteLLM

### 5f. Multi-Harness Operating Model
The current recommended operating structure.
- **Execution harness**: task routing, edits, consensus hooks, policy gates
- **Memory harness**: Boulder/KAIROS-style structured persistence
- **Retrieval harness**: corpus routing before deeper retrieval
- **Optimization harness**: MetaLoop over traces, prompts, routing, and hooks

See `docs/architecture/AGENTIC_OPERATING_MODEL.md`.

### 5g. NERV (Neurosynchronous Evolutionary Replicative Versioning)
Distributed neural system for knowledge replication.
- CRDT-based centroid clustering
- Consistent hash rings for sharding
- Hilbert curve spatial indexing

---

## 6. Governance Model

**Precedence (when artifacts disagree)**:
1. Master Metaprompt Kernel (mandatory rules)
2. Project Spine (invariants + enforcement)
3. SDD Master Spec (requirements, module boundaries)
4. UpgradableArtifact schema + lints
5. Governance protocols
6. ADRs / RFCs
7. Contracts / Schemas
8. Tests + signed results
9. Code (must conform to above)
10. Synthesis docs (context only)

**Decision framework**: Ternary (+1 proceed / 0 hold / -1 reject) with mandatory pre-decision spectrum mapping.

**Anti-overengineering**: Now/Later/Never evidence gate. Ship simplest thing that solves validated problem today.

---

## 7. Validation Matrix (Current State)

| Component | Specified | Implemented | Tested | Integrated |
|-----------|-----------|-------------|--------|------------|
| Holochain DNA (ARF) | Yes | Scaffolded | No (never compiled) | No |
| Symbolic Validation (Rust) | Yes | Code in docs | No | No |
| ConversationMemory | Yes (ADR-0) | Yes | 3/4 pass | Active |
| Multi-Agent Compose | Yes (ADR-0) | Yes | Pass | Active |
| Local source chain | Yes | Yes | Yes | Active |
| MCP consensus gateway | Yes | Yes | Partial | Active |
| Groq/Cerebras cheap-loop voters | Yes | Yes | Operationally exercised | Active |
| Radicle dev substrate | Yes (ADR-8) | No | No | No |
| Multi-harness operating model | Yes | Docs only | No | Partial |
| Fractal Embeddings | Yes | Yes | Yes | Pending real model |
| VVS Architecture | Yes (v1.0-1.2) | Partial | No | No |
| Commons Protocol (KERI) | Yes | Partial | No | No |
| NERV | Specified | No | No | No |

**Blocking items**:
- Rose Forest DNA has never compiled end-to-end in the active workflow
- `ConversationMemory` still needs its full memory-harness upgrade path
- ADR-0 Test #4 (Human Coherence) not yet run
- Radicle bridge spike not yet proven
- Retrieval is still too repo-local and not yet corpus-routed

---

## 8. Ethical Framework

**Non-negotiables** (from kernel):
- Consent first (consent_first: true)
- Provenance first (provenance_first: true)
- No sycophancy (no_sycophancy: true)
- Symbolic validation ("Formal rules validate; neural assists")
- Evidence gating (Now/Later/Never enforced)
- Spec first ("Specifications are source of truth")

**Voluntary Convergence Manifesto**: Consent as fundamental protocol. No forced integration. Transparent, auditable systems. Accessibility and emotional resonance.

---

## 9. Document Map

This document **references** the canonical sources — it does not duplicate them:

| What | Where |
|------|-------|
| Coordination kernel | `FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md` |
| SDD requirements | `FLOSS/SDD-Master-Spec-0.22.md` |
| Symbolic-first Rust code | `FLOSS/ARF/SYMBOLIC_FIRST_CORE.md` |
| Ontologies + migration | `FLOSS/ARF/ONTOLOGIES_AND_INTEGRATION.md` |
| Layer integration plan | `FLOSS/ARF/INTEGRATION_MAP.md` |
| Decision records | `FLOSS/docs/adr/INDEX.md` |
| Radicle dev substrate decision | `FLOSS/docs/adr/ADR-8-radicle-dev-substrate.md` |
| Agentic operating structure | `FLOSS/docs/architecture/AGENTIC_OPERATING_MODEL.md` |
| Forward-momentum execution plan | `FLOSS/docs/superpowers/plans/2026-04-16-forward-momentum-radicle-meta-harnesses.md` |
| Entry type schemas | `FLOSS/docs/specs/` |
| Governance loading order | `FLOSS/docs/governance/LOADING_ORDER.md` |
| Full project index | `INDEX.md` (root) |

---

## 10. Next Actions (Critical Path)

Based on the current operating model, the highest-leverage next steps are:

1. **Prove the Radicle bridge spike** — verify `code substrate -> provenance substrate` linkage before scaling autonomy.
2. **Upgrade the memory harness** — Boulder/KAIROS-style structured persistence on top of the local source chain.
3. **Add consensus hooks + deterministic edit verification** — make structural edits policy-aware and corruption-resistant.
4. **Add corpus routing before heavier retrieval** — retrieval harness before larger indexes.
5. **Get Holochain DNA compiling** — runtime substrate still needs real proof, not just design coherence.

---

*This is a living document. Update it when canonical documents change. Never duplicate content — always reference.*

*Love, Light, Knowledge — verifiable, shared, and free.*
