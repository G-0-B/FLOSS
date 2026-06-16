<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# The Living Context Daemon: Architecture for a Continuously-Evolving Shared Agentic Operating Context

**FLOSSI0ULLK Collective Intelligence Research Report**
*Compiled: April 17, 2026 | Node: External Reality Scout*
*Classification: Harvest Packet — Composable / SDD-Ready*

***

## Executive Summary

The central problem facing any multi-agent, multi-model collaborative system is **context decay**: as agents work in parallel, as files change, as decisions accumulate, no individual participant — human or AI — holds a coherent, current picture of what the collective knows and has decided. Periodic manual context dumps (e.g., reading a static CONTEXT.md at session start) are neither scalable nor sufficient. What is needed is a **Living Context Daemon** — a continuously monitoring, semantically aware, resource-efficient middleware layer that serves as the shared sensory nervous system of the collective.

This report theorizes, researches, and debates the architecture of exactly such a system, grounding the design in the FLOSSI0ULLK project's existing infrastructure (Sourcechain, MetaCoordinator MCP, ADRs, Boulder persistence), the lessons of Meta Harness and Oh-My-OpenAgent, the leaked KAIROS/autoDream memory design, and a survey of the most relevant open-source tools available in 2026. The conclusion is that the optimal architecture is a **five-layer, event-driven, CRDT-backed, graph-rooted system** served through a single MCP gateway — designed for local-first operation, provenance-tracked updates, and model-specific context rendering.

***

## Part I: Framing the Problem — Why Static Context Fails

### 1.1 The Context Decay Problem

Modern agentic workflows typically work as follows: at the start of a session, an agent reads a bundle of context files (CLAUDE.md, INDEX.md, CONTEXT.md), builds a mental model of the project, then acts. This approach has a fundamental flaw — it is a **snapshot**, not a stream. Between sessions, and within long sessions, the following happens:

- Files are modified by other agents or humans
- Architectural decisions (ADRs) are made and superseded
- Claims move between epistemic states (Unverified → Verified → Deprecated)
- New agents join the collective with no knowledge of prior decisions
- Errors and contradictions accumulate in the notepad files without reconciliation

The Stanford Meta Harness paper (arXiv:2603.28052, March 2026) provides empirical evidence of the cost of this problem: agents receiving only score-based summaries scored 34.6 on TerminalBench-2, those receiving summaries plus text scored 34.9, and those with full filesystem access to all prior traces scored significantly higher — a **gap that represents the ceiling of local optimization under compressed feedback**. The conclusion is architectural: **full traces, never summaries**. A Living Context Daemon must be designed around this principle.[^1]

### 1.2 The Resource-Comprehension Tradeoff

The opposing force is resource intensity. LLM-powered swarm systems carry roughly **300% more computational overhead** than classical counterparts, making naive "send everything to everyone always" untenable. The resolution is not to compress context, but to **tier it**:[^2]

- **L0** — 150-character summary (topic index, always in memory)
- **L1** — Paragraph-level description (fetched on topic match)
- **L2** — Full content (fetched on explicit request or write operation)

This tiered model, inspired by the KAIROS three-layer memory architecture (lightweight index → topic files → raw transcripts, with nightly autoDream distillation), allows agents to pay only for the context they actually need.[^1]

### 1.3 The Carrier Equivalence Principle Applied

Evaluated through the Carrier Equivalence Principle: a healthy context system should allow knowledge to **flow like water**, not pool in silos. Centralized context stores (a single shared database controlled by one process) are dams. The architecture proposed here routes context through:

- **Delta-CRDTs** for conflict-free distributed state[^3]
- **AD4M Perspectives** for semantic spanning across substrates[^2]
- **Holochain Sourcechain** for provenance and sovereign agent history[^2]
- **MCP as the open transport layer** — callable, hookable, composable

***

## Part II: Prior Art and Competitive Landscape

### 2.1 Existing MCP Context Servers (2025–2026)

The MCP ecosystem has produced several relevant implementations, each solving a slice of the problem:


| Tool | Core Mechanism | Strengths | Gaps |
| :-- | :-- | :-- | :-- |
| **document-mcp** (yairwein, 2025) [^4] | Watchdog + LanceDB + Ollama | Incremental re-embedding, SHA-256 fingerprinting, debouncing | No graph, no provenance |
| **DeepContext** (Wildcard AI, 2026) [^5] | tree-sitter AST + pre-index | Symbol-aware, instant query | Code-only, no docs/ADRs |
| **Code Context Manager MCP** [^6] | Redis RediSearch + SQLite + AST | Fast hybrid search | Not local-first, no delta-sync |
| **kairos-context-keeper** (turtir-ai, 2025) [^7] | Neo4j + ChromaDB + FastAPI | Knowledge graph + vector, proactive daemon | Centralized, heavy dependencies |
| **Graphiti** (getzep, 2024–2026) [^8] | Bi-temporal knowledge graph | Incremental updates, no full recomputation, MCP server | Requires external Neo4j |
| **memX** (MehulG, 2025) [^9] | CRDT-style shared state + pub/sub | Real-time multi-agent sync, JSON Schema enforcement | No semantic layer |
| **DeltaStream** (2026) [^10] | Apache Flink + ClickHouse + MCP | Stateful stream processing, full lineage | Enterprise/cloud-focused |
| **neuledge/context** (2026) [^11][^12] | Local-first doc layer | Lightweight, local-first design | Early-stage |

**Synthesis:** No single tool provides the full stack. The optimal solution is a **composed pipeline** drawing from document-mcp's incremental watching pattern, Graphiti's bi-temporal graph model, memX's CRDT-backed shared state, and the FLOSSI0ULLK project's ADR governance and ternary consensus engine.

### 2.2 KAIROS and autoDream: The Template for Distillation

The leaked Claude Code internal design (as analyzed in the oh-my-meta.md integration report) reveals a **three-layer persistent memory** architecture that is the most production-battle-tested design available:[^1]

1. **Lightweight index** (MEMORY.md, ~150 chars/entry, always-loaded)
2. **Topic files** (fetched on-demand when topic matches)
3. **Raw transcripts** (grep-only; full execution traces stored flat)

The `autoDream` nightly consolidation process is the engine that keeps this coherent: it reconciles contradictions, promotes tentative `Unverified` observations to `Verified` facts, and prunes stale entries. This maps exactly onto the FLOSSI0ULLK **Claim Truth Model** (Verified / Specified / Aspirational / Unverified).[^1]

The open-source community reverse-engineered KAIROS within days of the Claude Code source leak, producing at least one open reimplementation (`turtir-ai/kairos-context-keeper`). This validates the architecture and provides a starting point for implementation.[^7]

### 2.3 CRDTs as the Synchronization Primitive

A 2026 analysis from Zylos AI  establishes the case for CRDTs (Conflict-free Replicated Data Types) as the foundation for distributed multi-agent state. Key findings:[^3]

- **Delta-CRDTs** (pioneered by CBaquero ) exchange only the *diff* since last sync, not full replicas — directly addressing the resource intensity concern[^13][^14]
- **AWORSet (Add-Wins Observed-Remove Set)** is ideal for shared task queues where multiple agents may add entries
- **ORMap (Observed-Remove Map)** works for shared capability registries
- **LWW-Register (Last-Write-Wins)** suffices for current plan/status
- FOSDEM 2026 hosted its first dedicated "Local First, sync engines and CRDTs" devroom, signaling mainstream adoption[^3]
- Hybrid architecture recommended: **CRDTs for structural convergence** + **LLMs for semantic conflict resolution** — the CRDT resolves "who wrote what when" while the LLM resolves "what does this contradiction mean for our shared understanding"

This maps cleanly to FLOSSI0ULLK's existing infrastructure: the Holochain Sourcechain is already an append-only agent-centric log that serves a similar convergence function. CRDTs can operate *above* the Sourcechain as the working-memory synchronization layer.

### 2.4 Graphiti: Bi-Temporal Knowledge for Agent Memory

Graphiti (getzep, Apache 2.0, 2024–2026)  is the most architecturally sophisticated open-source solution for agent memory management. Its key properties:[^8][^15]

- Stores facts as **bi-temporal graph edges**: event time (when the fact was true in the world) + ingestion time (when the agent learned it)
- **Incremental updates** — new information is reconciled against existing nodes without full recomputation, making it viable for continuous operation
- **Hybrid retrieval**: semantic similarity + BM25 full-text + graph traversal, combined to return the most relevant and recent context
- Ships an **MCP server** for direct agent integration
- Tracks **fact validity windows** — automatically marks facts as expired when contradicted by newer information

For FLOSSI0ULLK, Graphiti can serve as the implementation substrate for the Claim Truth Model's temporal dimension: a Claim's `Verified` status is not just a boolean but a **fact with a validity window** that expires if not reinforced.

***

## Part III: The Five-Layer Architecture

### 3.1 Overview

The Living Context Daemon is composed of five layers, each with a distinct responsibility. All layers are exposed to agents through a single **flossi0ullk-context MCP server** that acts as the unified callable interface.

```
┌─────────────────────────────────────────────────────────┐
│          flossi0ullk-context MCP Gateway                │
│   query_context | watch_changes | claim_context         │
│   get_adr | schedule_consolidation | get_agent_view     │
└─────────────────┬───────────────────────────────────────┘
                  │
     ┌────────────▼───────────────────────────────────┐
     │  Layer 4: AutoDream Curator (Nightly + Triggered)│
     │  Orient → Gather → Consolidate → Prune          │
     └────────────┬───────────────────────────────────┘
                  │
     ┌────────────▼──────────────────────────────────────┐
     │  Layer 3: CRDT-Backed Shared State (memX pattern) │
     │  AWORSet (tasks) | ORMap (agents) | LWW (status)  │
     └────────────┬──────────────────────────────────────┘
                  │
     ┌────────────▼──────────────────────────────────────┐
     │  Layer 2: Bi-Temporal Knowledge Graph (Graphiti)  │
     │  Claims | ADRs | Agents | Artifacts | Decisions   │
     └────────────┬──────────────────────────────────────┘
                  │
     ┌────────────▼──────────────────────────────────────┐
     │  Layer 1: Semantic Index (document-mcp pattern)   │
     │  LanceDB + nomic-embed-text + BM25                │
     └────────────┬──────────────────────────────────────┘
                  │
     ┌────────────▼──────────────────────────────────────┐
     │  Layer 0: Observer (Watchdog + Hashline)          │
     │  inotify/FSEvents → normalized change events      │
     └───────────────────────────────────────────────────┘
                  ▲
     ┌────────────┴──────────────────────────────────────┐
     │           FLOSSI0ULLK Workspace                   │
     │  FLOSS/ | _reference/ | ai-conversations/          │
     └───────────────────────────────────────────────────┘
```


### 3.2 Layer 0: The Observer

**Responsibility:** Detect file system changes with minimum latency and maximum efficiency.

**Mechanism:**

- Use `watchdog` (Python) or `chokidar` (Node.js) for cross-platform filesystem events
- Apply **Hashline-inspired SHA-256 fingerprinting**: when a file modification event fires, compute the hash of the changed content. If the hash matches the stored fingerprint, **skip all downstream processing** — no re-embedding, no graph update, no CRDT propagation. This single gate eliminates the vast majority of spurious events (auto-saves, formatter touches, git checkout artifacts)
- **Tiered notification policy:**

| File Category | Update Policy | Rationale |
| :-- | :-- | :-- |
| INDEX.md, CLAUDE.md, ADRs | Immediate push (< 1s) | Critical path; agents blocked on current state |
| FLOSS/docs/, FLOSS/specs/ | Batched (5-minute windows) | Frequent small edits; batch reduces downstream churn |
| _reference/, ai-conversations/ | Batched (15-minute windows) | Background corpus; rarely time-sensitive |
| node_modules/, .git/ | Ignored entirely | No semantic value |

- Output: normalized `ChangeEvent { path, type: CREATE|MODIFY|DELETE|RENAME, content_hash, timestamp }` pushed to an internal event bus

**Resource profile:** Near-zero CPU at rest (inotify is kernel-level). SHA-256 on typical markdown files: microseconds.

### 3.3 Layer 1: The Semantic Indexer

**Responsibility:** Maintain a queryable, semantically-aware index of all workspace content.

**Mechanism:**

- **Embedding model:** `nomic-embed-text` via Ollama (local, ~80MB, no API calls required)
- **Storage:** LanceDB (embedded, no separate server, Rust-based for speed)
- **SHA gate:** Only re-embed if content hash changed since last indexing run (document-mcp pattern )[^4]
- **Chunking strategy:**
    - ADRs, specs → paragraph-level chunks with frontmatter preserved
    - Source code → function-level chunks via tree-sitter AST parsing (DeepContext pattern )[^5]
    - Conversations → turn-level chunks
- **Search:** Hybrid BM25 + vector similarity, with MMR (Maximal Marginal Relevance) re-ranking to reduce redundancy in results
- **Throughput throttle:** Maximum 100 files/minute re-embedded to prevent resource spikes during large git operations

**Debate Point — Local vs. API Embeddings:**
*For:* Local embeddings (nomic-embed-text) are free, private, and always available offline. *Against:* Quality is lower than `text-embedding-3-large` or similar; context window is 8192 tokens vs 32768. *Resolution:* Use local by default. Add a configurable upgrade path where files in `FLOSS/docs/adr/` (the most semantically critical corpus) use API embeddings if a key is configured, and local for everything else. This hybrid approach minimizes cost while maximizing quality on the highest-value content.

### 3.4 Layer 2: The Bi-Temporal Knowledge Graph

**Responsibility:** Store structured, provenance-tracked, temporally-aware facts about the project state.

**Mechanism (Graphiti-inspired ):**[^8]

**Node types:**

- `ADR { id, status: Proposed|Accepted|Deprecated|Superseded, content_hash }`
- `Claim { id, truth_model: Verified|Specified|Aspirational|Unverified, valid_from, valid_until }`
- `Agent { id, type: Human|Claude|GPT|LocalLLM, capabilities[] }`
- `Artifact { path, content_hash, last_modified }`
- `Decision { id, context, rationale, consequences }`

**Edge types:**

- `SUPERSEDES(ADR → ADR)`
- `SUPPORTS(Claim → Claim)`
- `CONTRADICTS(Claim → Claim)` — triggers autoDream consolidation
- `PRODUCED_BY(Artifact → Agent)`
- `GOVERNED_BY(Artifact → ADR)`

**Bi-temporal model:** Every edge carries `(event_time, ingestion_time)`. This allows queries like "What did agent Claude-Opus believe about the consensus protocol as of 3 days ago?" — critical for debugging multi-agent disagreements.

**Incremental updates:** New information is reconciled against existing nodes using Graphiti's entity resolution algorithm — no full recomputation. A new `CONTRADICTS` edge is a signal, not a failure: it queues a semantic reconciliation task for the Curator.

**Why not a flat vector store?** A purely vector-based store answers "what is similar to this?" but cannot answer "what decisions are currently active?", "what did we believe before we learned X?", or "which agent produced this artifact?" The knowledge graph answers all three. The Semantic Index (Layer 1) handles similarity search; the Knowledge Graph handles relational and temporal reasoning. They complement rather than replace each other.

### 3.5 Layer 3: The CRDT-Backed Shared State

**Responsibility:** Provide conflict-free, real-time-synchronizable shared state for active multi-agent coordination.

**Mechanism:**


| State Object | CRDT Type | Contents |
| :-- | :-- | :-- |
| Active Task Queue | AWORSet | `{ task_id, assigned_to, status, priority }` |
| Agent Registry | ORMap | `{ agent_id → capabilities, last_seen, current_task }` |
| Current Plan | LWW-Register | Active Prometheus plan JSON |
| Consensus Votes | AWORSet | `{ claim_id, agent_id, vote: +1|0|-1 }` |
| Boulder Checkpoints | ORMap | `{ plan_name → { learnings, decisions, issues } }` |

**Delta-sync protocol:** Agents exchange only the *delta* since their last vector clock timestamp. An agent that goes offline and reconnects receives only the changes that occurred during its absence — not a full state dump. This is the fundamental efficiency gain over broadcast architectures.[^13][^3]

**Gossip convergence:** Following the Honeybee Byzantine-tolerant peer sampling model, agents gossip state updates through a random subset of peers rather than broadcasting to all. This scales sublinearly with agent count.[^2]

**Integration with Holochain Sourcechain:** The CRDT layer operates as the *working memory* (fast, ephemeral, volatile). The Holochain Sourcechain serves as the *long-term source chain* (immutable, agent-sovereign, auditable). At configurable intervals, the Curator promotes stable CRDT state into signed Sourcechain entries — the "commit to history" operation.

### 3.6 Layer 4: The AutoDream Curator

**Responsibility:** Maintain coherence, reduce noise, promote epistemic certainty, and generate model-specific context views.

**Trigger conditions (any one is sufficient):**

- Scheduled: nightly at 03:00 local time
- Session-count: after every 5 completed agent sessions
- Conflict-detected: when a new `CONTRADICTS` edge is added to the knowledge graph
- Manual: via `schedule_consolidation()` MCP call

**Four-phase cycle (KAIROS-inspired ):**[^1]

1. **Orient** — Load the diff of changes since last consolidation from Layer 0 event log. Build a summary of what happened.
2. **Gather** — For each changed entity, retrieve its current state from the Knowledge Graph + Semantic Index. Fetch all `CONTRADICTS` edges added since last run.
3. **Consolidate** — Run a bounded LLM call (Sonnet-class, not Opus — cost vs. quality tradeoff) with the gathered context. The prompt asks:
    - "Which `Unverified` claims have been reinforced enough to promote to `Verified`?"
    - "Which `Verified` claims are contradicted by recent evidence and should be downgraded to `Unverified` or `Deprecated`?"
    - "Which decisions in decisions.md should be promoted to formal ADRs?"
    - "What is the L0 summary (≤150 chars) for each modified artifact?"
4. **Prune** — Remove ephemeral CRDT state older than 30 days. Archive raw conversation logs to `_reference/`. Regenerate the per-agent CONTEXT views.

**Dual-prompt rendering (omo pattern ):**[^1]
The Curator generates two canonical context view files:

- `CONTEXT-CLAUDE.md` — mechanics-driven, detailed checklists, full ADR references, explicit verification chains
- `CONTEXT-GPT.md` — principle-driven, concise XML-structured, key decisions with rationale, minimal boilerplate

This resolves the core architectural problem identified in oh-my-meta.md: giving a 1,100-line Claude prompt to a GPT model causes self-contradiction. The Curator's translator role ensures every model receives context in its native cognitive format.[^1]

***

## Part IV: The MCP Gateway API

The `flossi0ullk-context` MCP server exposes six primary tools:

### Tool Specifications

```typescript
// Semantic search across all layers with model-aware rendering
query_context(
  question: string,
  agent_type?: "claude" | "gpt" | "local" | "human",
  scope?: "all" | "adrs" | "claims" | "code" | "conversations",
  depth?: "L0" | "L1" | "L2"  // tiered retrieval
) → RankedContextBundle

// Subscribe to real-time file system deltas via SSE
watch_changes(
  paths: string[],
  callback: (event: ChangeEvent) => void,
  batch_window_ms?: number  // 0 = immediate, 300000 = 5 min
) → EventStream

// Add a new claim to the shared knowledge graph
claim_context(
  claim: string,
  truth_model: "Verified" | "Specified" | "Aspirational" | "Unverified",
  evidence?: string[],  // paths or claim IDs that support this
  agent_id: string
) → ClaimID

// Retrieve ADRs relevant to a topic
get_adr(
  topic?: string,  // semantic search; null = all active ADRs
  status?: "Proposed" | "Accepted" | "Deprecated" | "Superseded"
) → ADR[]

// Trigger an immediate Curator cycle
schedule_consolidation(
  reason: string,
  priority?: "normal" | "urgent"
) → JobID

// Get model-specific rendered context for an agent
get_agent_view(
  agent_id: string,
  sections?: string[]  // e.g. ["current_plan", "active_adrs", "recent_decisions"]
) → AgentContextView
```


### Hook Integration (omo Seam 1 )[^1]

The MCP gateway registers as a **consensus-gate hook** in the omo five-tier hook hierarchy, positioned between `tool-guard` and `continuation` hooks. When any agent proposes a structural code change (detected via AST diff exceeding a configurable threshold), the hook:

1. Serializes the proposed change as an `Unverified` Claim
2. Sends it to the MetaCoordinator for ternary consensus voting (+1 / 0 / -1)
3. Blocks execution until consensus is reached (1,1,1 or 1,1,0 with human override)
4. Logs the vote as a `Decision` node in the Knowledge Graph with full provenance

This makes FLOSSI0ULLK's governance **ambient rather than bolted on** — it fires automatically as part of the normal coding workflow, not as a separate approval ceremony.

***

## Part V: Scheduling Philosophy and Resource Budget

### 5.1 The Three Tempos

Effective continuous context management operates at **three distinct tempos**, each with different latency requirements and resource costs:


| Tempo | Trigger | Latency Target | Resource Budget |
| :-- | :-- | :-- | :-- |
| **Reactive** | File change detected (critical path) | < 1 second | Hash check: microseconds; no embedding unless hash differs |
| **Rhythmic** | Batch window elapsed (bulk files) | 5–15 minutes | Incremental embedding: 10-100 files at most |
| **Reflective** | Nightly / session-count / conflict | Minutes to hours | Full Curator cycle: 1 LLM call + graph reconciliation |

The key insight is that **most events should flow through the Reactive tempo at near-zero cost** because the SHA-256 hash gate will pass them through as "no content change." Only genuine semantic changes trigger downstream processing. In practice, an active development session might generate hundreds of file-system events but only a dozen actual content changes worth re-indexing.

### 5.2 Resource Envelope

Targeting a minimal footprint suitable for running on a developer laptop alongside primary tools:


| Component | Idle CPU | Active CPU | RAM |
| :-- | :-- | :-- | :-- |
| Watchdog observer | < 0.1% | < 0.5% | 20 MB |
| LanceDB index | 0% | 2–5% (query) | 50–200 MB |
| Graphiti graph | 0% | 1–3% (query) | 100–500 MB |
| CRDT state (memX) | < 0.1% | < 1% | 10–50 MB |
| Ollama (nomic-embed) | 0% (unloaded) | 15–30% (embedding) | 500 MB (loaded) |
| Curator (LLM call) | 0% | API call only | Negligible local |

**Total idle footprint:** approximately 200–800 MB RAM, < 0.5% CPU. This is compatible with concurrent IDE, browser, and coding agent operation.

### 5.3 Debate: Polling vs. Event-Driven

*Polling camp:* Simpler to implement, predictable resource usage, no risk of missing events. A 30-second poll of changed files via `git status` costs almost nothing. *Event-driven camp:* Lower latency for critical files, no unnecessary cycles when nothing changes, enables true reactive architectures.

*Resolution:* **Hybrid**. Use event-driven (watchdog/inotify) for the reactive tempo because the latency improvement for critical files (INDEX.md, ADRs) is operationally significant — an agent that reads a 30-second-stale ADR and makes a contradictory decision creates more corrective work than the marginal resource cost of inotify. Use polling as a **fallback and reconciliation mechanism** — a 5-minute poll of `git diff HEAD` catches any events the watcher may have missed (network filesystem edge cases, IDE behavior, git operations).

***

## Part VI: Integration Seams with FLOSSI0ULLK

The five integration seams identified in oh-my-meta.md map directly to the Living Context Daemon's layers:[^1]


| Seam | Description | Daemon Layer | Priority |
| :-- | :-- | :-- | :-- |
| **Seam 1** | Consensus-gate hook (MCP transport) | MCP Gateway + Layer 3 CRDT votes | **Immediate** — foundational transport |
| **Seam 1.5** | `flossi0ullk-context` MCP server | All layers | **Immediate** — this document IS the spec |
| **Seam 3** | Boulder → CRDT-backed checkpoint with ADR labels | Layer 3 CRDT state | **Near-term** — structured memory |
| **Seam 4** | KAIROS autoDream → Knowledge Graph + Claim promotion | Layer 4 Curator | **Near-term** — coherence engine |
| **Seam 5** | Auto-generated FLOSSI0ULLK-aware AGENTS.md | Layer 4 Curator output | **Medium-term** — ambient governance |

### ADR Proposal: ADR-CONTEXT-DAEMON

This document constitutes a **Proposed ADR** for the Living Context Daemon. It should be filed as `FLOSS/docs/adr/ADR-CONTEXT-DAEMON.md` with the following metadata:

```yaml
id: ADR-CONTEXT-DAEMON
title: Living Context Daemon Architecture
status: Proposed
date: 2026-04-17
deciders: [Human Operator, Claude-Opus, ExternalRealityScout-Perplexity]
context: >
  The FLOSSI0ULLK collective requires a continuously-updating, resource-efficient
  shared context platform to prevent context decay across multi-agent sessions.
decision: >
  Implement a five-layer, event-driven, CRDT-backed, graph-rooted context daemon
  served through a unified flossi0ullk-context MCP gateway.
consequences: >
  Positive: Eliminates context decay; enables ambient governance; reduces
  token cost via tiered retrieval; provides provenance for all context updates.
  Negative: Adds infrastructure complexity; requires Ollama for local embeddings;
  Graphiti requires a graph backend (SQLite for local, Neo4j for distributed).
```


***

## Part VII: Open Debates and Unresolved Questions

This section surfaces the genuine tensions in the design — areas where the collective should debate before implementation.

### Debate 1: SQLite vs. Neo4j for the Knowledge Graph

**SQLite path (local-first):** Lower dependencies, zero setup, sufficient for single-developer or small-team deployments. Graphiti supports SQLite. Aligns with FLOSSI0ULLK's local-first philosophy. *Risk:* Performance degrades beyond ~100k nodes.

**Neo4j path (distributed-first):** Full graph query power (Cypher), native clustering, production-grade at scale. Maps to FLOSSI0ULLK's multi-agent, multi-node vision. *Risk:* Adds JVM dependency, heavier operationally.

**Proposed resolution:** Start with SQLite. Define a storage adapter interface from day one. Migrate to Neo4j when the graph exceeds 50k nodes or when multi-node deployment is required. This is a concrete ADR decision point.

### Debate 2: Who Triggers the Curator?

**Agent-triggered (pull model):** Any agent can call `schedule_consolidation()` when it detects incoherence. Distributed, no single point of authority. *Risk:* Agents may over-trigger, causing resource spikes.

**Daemon-triggered (push model):** The Daemon decides when to consolidate based on internal metrics (contradiction count, session count, time elapsed). Agents are not burdened with this decision. *Risk:* Consolidation may lag behind critical decisions.

**Proposed resolution:** **Both, with rate limiting.** The Daemon runs on its schedule. Agents can request consolidation but are rate-limited to one triggered consolidation per hour per agent. A `CONTRADICTS` edge always triggers consolidation immediately, regardless of rate limits — because contradictions in the shared knowledge base are the highest-priority coherence failure mode.

### Debate 3: What Is the Boundary of "Shared Context"?

Should the daemon index **all** files in the workspace, or only explicitly designated "context files"? Indexing everything maximizes comprehension but risks polluting the context with irrelevant build artifacts, generated files, or sensitive data.

**Proposed resolution:** Adopt an **allowlist with opt-in expansion** model. The default corpus is:

- `FLOSS/docs/` (ADRs, specs, architecture)
- `FLOSS/packages/*/README.md` (package-level context)
- `INDEX.md`, `CLAUDE.md`, `CONTEXT*.md` (root context files)
- `ai-conversations/` (session history)
- `_reference/` (curated external knowledge)

Code in `FLOSS/packages/*/src/` is indexed by the Semantic Indexer (Layer 1) but **not** by the Knowledge Graph (Layer 2) — code is queried via symbol search, not represented as first-class graph nodes (except for function signatures, which become `Artifact` nodes).

### Debate 4: The AD4M Integration Horizon

AD4M's Perspectives (private local graph databases that can link data across protocols) are an **architectural natural fit** for Layer 2's Knowledge Graph[^2]

<div align="center">⁂</div>

[^1]: oh-my-meta.md

[^2]: Open-Access-Research-Landscape-Distributed-Agent-Centric-Collective-Intelligence-Systems-2023-202.md

[^3]: https://zylos.ai/research/2026-03-17-crdts-distributed-state-sync-multi-agent-systems

[^4]: https://github.com/yairwein/document-mcp

[^5]: https://mcpdir.dev/servers/deepcontext-semantic-code-search

[^6]: https://lobehub.com/de/mcp/theraaz-code-context-manager-mcp

[^7]: https://github.com/turtir-ai/kairos-context-keeper

[^8]: https://github.com/getzep/graphiti

[^9]: https://github.com/MehulG/memX

[^10]: https://www.deltastream.io/blog/deltastream-the-real-time-context-engine-for-agents/

[^11]: https://neuledge.com/context/

[^12]: https://github.com/neuledge/context

[^13]: https://github.com/CBaquero/delta-enabled-crdts

[^14]: https://github.com/CBaquero/delta-enabled-crdts/blob/master/README.md

[^15]: https://github.com/getzep/graphiti/blob/main/README.md

