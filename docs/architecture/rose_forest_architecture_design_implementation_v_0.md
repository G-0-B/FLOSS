# Rose Forest — Architecture & Design Implementation v0.2 (Holochain‑native)

_Last updated: 29 Aug 2025_

> **North Star**  
> A forkable, verifiable **superintelligence commons**—run by people, not platforms—where every datum, model, and decision carries provenance, and anyone can self‑host a **Rose** node that collaborates in a global mesh to accelerate **Love (ethics), Light (clarity), and Knowledge (capability)**.

---

## 1) System Map (at a glance)
```mermaid
flowchart TB
  subgraph Substrate[Holochain Substrate]
    DHT[Kitsune2 DHT + Gossip]
    Conductor[Holochain Conductor]
  end

  subgraph DNA[Rose Forest DNA]
    direction TB
    IZ[Integrity Zome\n(entries + validation)]
    CZ[Coordinator Zome\n(app logic + search)]
  end

  subgraph AuxDNAs[Auxiliary DNAs]
    REA[Holo‑REA Value Flow]
    KPI[KPI/Telemetry DNA (optional)]
  end

  UX[Critique‑first UX (TUI/Web)]
  Agents[Local Agents / Tools]

  UX<-->CZ
  Agents<-- zome calls / signals -->CZ
  CZ<-->REA
  KPI-. optional .-CZ
  Conductor---DNA
  Conductor---AuxDNAs
  DNA<-->DHT
```

---

## 2) Core Components & Intended Function

### 2.1 Holochain Substrate
- **Conductor**: Hosts DNAs (apps) per agent; secures keys; executes Wasm; persists source chains.  
- **Kitsune2 DHT**: Peer discovery, NAT traversal (incl. WebRTC), gossip, and eventual consistency.  
**Why**: We inherit **signatures, provenance, conflict handling,** and **networking**—deleting custom libp2p/CRDT code and focusing on intelligence.

### 2.2 Rose Forest DNA
**Integrity Zome (law):**
- **Entries**
  - `RoseNode { content, embedding<Vec<f32>>, license, metadata }`: a signed knowledge atom with an embedding.
  - `KnowledgeEdge { from, to, relationship, confidence }`: typed relations: `supports|contradicts|cites|extends`.
- **Links**
  - `AllNodes`: `Path("rose_nodes") → RoseNode` (global discovery).
  - `ShardMember`: `Path("shard.<prefix>") → RoseNode` (semantic neighborhood).
  - `Edge`: `from → to` (optional materialization for faster traversals).
- **Validation (NormKernel v0)**
  - OSI license allowlist; embedding dimension bounds; confidence in `[0,1]`.
  - Extensible: add *citation‑required* for claims, privacy tags, content size quotas.  
**Why**: Validation is **executable policy** (not advisory). Every node enforces it, raising the trust floor without central moderators.

**Coordinator Zome (logic):**
- **Externs**
  - `add_knowledge({content, license, metadata}) -> ActionHash`: embeds → stores a `RoseNode` → links to AllNodes & Shard.
  - `vector_search({text, k}) -> [(ActionHash, score)]`: local cosine over current DHT view (v0 naive; see v1 below).
  - `link_edge({from, to, relationship, confidence})`: asserts a `KnowledgeEdge` + link materialization.
- **Local Intelligence**
  - **Embedder**: start with deterministic toy; plug‑replace with ONNX/gguf later (declared model/version in metadata).
  - **ANN index**: v0 on‑the‑fly scan; v1 private snapshot entry for incremental ANN; v2 HNSW/IVF‑PQ compiled to Wasm or host‑side service.
- **Sharding & Discovery**
  - Quantize first 8 dims → `Path("shard.<hex_prefix>")`.  
  - Agents optionally **join shards** by linking their contributions; cross‑shard search composes by expanding prefixes.  
**Why**: Keeps query latency low, supports **offline‑first**, and avoids global indexes. Paths give **hierarchical, semantic** neighborhoods.

### 2.3 Auxiliary DNAs
- **Holo‑REA (Value Flow)**: Offers/needs, commitments, mutual credit, bounties (pay for answers/replications).  
**Why**: Don’t reinvent economy; reuse battle‑tested patterns to reward contributions.
- **KPI/Telemetry (optional)**: Aggregated, privacy‑aware counters (MAU, VRR, OC72).  
**Why**: Makes impact measurable without central logs; can be local‑only or federated with DP.

### 2.4 UX: Critique‑First Interface
- **Primary view**: evidence + counter‑evidence side‑by‑side; uncertainty; provenance; shard context.  
- **Sycophancy Resistance**: disagree/ask‑for‑evidence when claims are weak; show alternative hypotheses.  
**Why**: Design away addiction & flattery. Promote **epistemic resilience** and critical thinking.

### 2.5 Local Agents & Tools
- **Tool runners** (code, math, retrieval) invoked via zome calls or host‑callbacks; outputs return as signed entries/edges.  
- **Multi‑agent orchestration** is **host‑side** (not Wasm heavy): agents add notes/edges; coordinator validates and persists.  
**Why**: Keep Wasm light/deterministic; heavy compute lives outside but writes **verifiable** results into the DHT.

---

## 3) Data Model & Lifecycle
1. **Ingest**: `add_knowledge` embeds text → `RoseNode` entry; license & size validated; links added.  
2. **Discover**: peers gossip; others find via `AllNodes` and shard paths.  
3. **Relate**: edges (`cites/supports/contradicts`) form the **Vector‑Graph**; materialized links enable traversals.  
4. **Query**: local ANN → top‑k hashes; fetch entries; (optionally) follow edges for explanations.  
5. **Evolve**: agents propose edits/new nodes; validation enforces rules; provenance ensures lineage; KPIs summarize effects.

---

## 4) Observability & Governance
- **Metrics/KPIs** (local first, share aggregates):
  - **PC (Provenance Coverage)**: 100% by default.  
  - **VRR (Verified Reasoning Rate)**: % answers with citations + uncertainty; enforced by integrity rules and logged denials.
  - **MAU‑RN**: unique agents adding nodes monthly.  
  - **OC72**: outage drill survival (get success rate after 72h partition).  
- **Governance**
  - Policy = integrity validation; changes require DNA version bump + transparent ballots (documented).  
  - **Ethical Escalation**: near‑violations trigger host‑side human review flows.

---

## 5) CI/CD & Reproducibility
- **Deterministic Wasm builds**; `hc dna pack` as a CI gate.  
- **Tryorama** multi‑agent smoke: add → gossip → search.  
- **Model Cards**: any embedder/model update publishes card + hash; entries reference `model_id` in metadata.  
**Why**: Reproducibility and provenance are table‑stakes for trust.

---

## 6) Privacy Modes
- **STRICT**: local only; no telemetry; encrypted private snapshots.  
- **FEDERATED**: DP aggregates for KPIs.  
- **OPEN**: public artifacts only.  
**Why**: Aligns with sovereignty: users opt into sharing, not the reverse.

---

## 7) Security & Safety
- **Validation** blocks risky/invalid content at the edge.  
- **Content quotas** per agent to prevent spam; stake/bounty integration with Holo‑REA for economic friction.  
- **Sycophancy‑resistant prompts** and rate‑limits to avoid dependency patterns.  
- **Incident workflow**: signed reports as entries; red‑team playbooks; public postmortems.

---

## 8) Versioning & Interop
- **Schema evolution** via DNA versioning; migration scripts for entries/links where feasible.  
- **Cross‑DNA registry**: a small app indexing which DNAs (domains) exist; agents subscribe to relevant domains rather than a monolith.  
- **APIs**: zome externs (Rust), conductor admin interfaces, and host‑side agent SDK (TypeScript/Rust) for tool builders.

---

## 9) Execution Plan (v0 → v2)

### v0 (MVP — already scaffolded)
- `add_knowledge`, `vector_search`; AllNodes + ShardMember paths; OSI‑license validation; tryorama smoke; deterministic pack.
- **Definition of Done**: two agents; one adds, the other finds via vector_search; invalid license rejected.

### v1 (Usability & Performance)
- **Private ANN snapshot entry** + incremental maintenance signals.  
- **Edge materialization** and `explain` query (follow `cites/supports/contradicts`).  
- **Embedder plug‑in** (ONNX/gguf) with model card + hash.  
- **Critique‑first UX** (local web/TUI) with uncertainty and counter‑evidence panes.  
- **KPI** counters (local) with optional DP federation.

### v2 (Economy & Multi‑Agent)
- Holo‑REA integration: bounties, mutual credit, budget proposals.  
- Host‑side multi‑agent orchestration; tool outputs written as signed `RoseNode/KnowledgeEdge`.  
- **Shard expansion** queries: progressive prefix widening; caching.  
- **Safety**: content quotas, rate‑limits, incident zome.

---

## 10) Design Rationale (Why these choices)
- **Holochain vs. DIY P2P**: We avoid rebuilding signatures, CRDTs, and routing. Agent‑centric DHT aligns with sovereignty & offline‑first.
- **Validation (law) over moderation (afterthought)**: Executable policy in integrity zome reduces harm surface and increases predictability.
- **Local ANN over Global Index**: Performance, privacy, and failure isolation. Shards compose when needed, not by default.
- **Paths for Sharding**: Simple, hierarchical discovery that maps cleanly to quantized embedding space and human domains.
- **Host‑side Agents**: Keep Wasm deterministic/light; heavy compute outside while preserving **verifiable results** inside the DHT.
- **Holo‑REA integration**: Economic primitives already exist; leverage them so incentives match contributions early.
- **Critique‑first UX**: Aligns with anti‑sycophancy and raises epistemic quality.

---

## 11) Risks & Counters (Trinary framing)
- **Complexity creep**  
  +1: strict module boundaries; quarterly subtractive refactors.  
  0: guardrails exist but occasional drift.  
  −1: monolith DNA and ad‑hoc features → stop‑the‑line.

- **Network scale limits**  
  +1: multiple domain DNAs; shard‑aware queries.  
  0: hotspots appear; add read‑through caches.  
  −1: single DNA overloaded → split & migrate.

- **Safety theater**  
  +1: validation + incidents + red‑team budget.  
  0: checklists without postmortems.  
  −1: hidden failures, trust erosion.

- **Capture (corp/state)**  
  +1: legal forkability, mirrored infra, diverse funding.  
  0: soft dependencies on single vendors.  
  −1: closed services required; hard fork.

---

## 12) Interfaces (for builders)
- **Externs**
  - `add_knowledge(AddNodeInput) -> ActionHash`
  - `vector_search(QueryInput) -> Vec<(ActionHash, f32)>`
  - `link_edge({from,to,relationship,confidence}) -> ActionHash`
- **Signals (future)**
  - `IndexUpdated`, `ShardExpanded`, `PolicyViolation`
- **Host SDK stubs**
  - Rust/TS helpers for embedding, ANN updates, and Holo‑REA calls.

---

## 13) Minimal Code References (indicative)
- Integrity & Coordinator zome templates are in the **Greenfield Bootstrap v0** document. Use those files verbatim to start, then iterate per v1 features.

---

### Summary
This design replaces custom networking/CRDTs with Holochain’s **agent‑centric substrate**, turns governance into **code via validation**, keeps intelligence **local & verifiable**, and composes global knowledge through **semantic sharding**. It’s intentionally boring in the right places—so we can move fast where it matters: **explanatory power, safety, and real‑world impact**.

