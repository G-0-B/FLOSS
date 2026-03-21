# FLOSSIOULLK Architecture Overview

**Version:** 1.0.0
**Updated:** 2026-03-05
**Truth Status:** Specified (design framework; components at varying maturity)

> Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge

---

## What This Is

A biomimetic distributed intelligence platform built on the **Carrier Equivalence Principle**: all carriers (light, water, electricity, knowledge, love, trust) follow isomorphic flow geometry — they degrade when held, multiply through distribution, achieve coherence via voluntary resonance, and circulate via overflow.

**Engineering translation of values:**
| Value | Engineering Equivalent | Measured By |
|-------|----------------------|-------------|
| Love | Interoperability & Connectivity | API compatibility, integration success rate |
| Light | Observability & Transparency | Zero hidden state, BFT validation rate |
| Knowledge | Verifiable State | Provenance chain completeness, validation pass rate |

---

## Layer Architecture

| Layer | Name | Role | Status |
|-------|------|------|--------|
| **L-1** | Fractal Lens | Frames of reference, whole-part relationships | Specified |
| **L0** | Universal Provenance & Identity | Holochain DHT, agent-centric integrity | **Specified (Phase 0 target)** |
| **L1** | Agent Primitives | Identity, capabilities, protocol adapters | Specified |
| **L2** | Spec-Driven Orchestration | SDD, CI gates, spec-as-canonical | **Partially verified** |
| **L3** | Knowledge Commons | Semantic search, redundancy prevention | **Specified (Rose Forest DNA)** |
| **L4** | Meta-Learning | MetaLoop, metric collection | Aspirational |
| **L5** | Governance & Alignment | ULLK enforcement, RICE overlay | Specified |
| **L6** | Transcendent Modal | Recursive self-improvement, fractal scalability | Aspirational |

---

## Two-Plane Architecture

```
Plane A: Dev Meta-Coordinator          Plane B: Runtime Meta-Coordinator
(Centralized tools OK)                 (Agent-centric validity)

  Plans, ADRs, PRs, CI                  Per-agent source chains
  Python orchestration                   Integrity validation rules
  Artifacts as output                    Eventual consistency + sharded authority

         ─────── Bridge Rule ───────
         Plane A may publish INTO Plane B
         but CANNOT bypass Plane B validation
```

---

## Isomorphism Map (Carrier Equivalence)

| Scale | Biological Equivalent | Technical Implementation |
|-------|----------------------|------------------------|
| **Micro** | Mitochondria / Cell | Rust Integrity Zomes (Holochain) |
| **Mezzo** | Holobiont / Body | Walking Skeleton (Agent composite) |
| **Macro** | Language / Culture | ADR-0 Recognition Protocol |
| **Meta** | Fractal Kinship | Recursive Vortex (ULLK) |

---

## Core Component: Rose Forest DNA

The primary Holochain hApp implementing L0/L3.

**Entry Types:**
- `RoseNode` — Signed knowledge atom with embedding, license, model provenance
- `KnowledgeEdge` — Typed relationship with confidence score
- `BudgetEntry` — Agent resource usage tracking (100 RU / 24h)
- `ThoughtCredential` — Cognitive artifact with ternary connotation

**Key Operations:**
- `add_knowledge` — Embed + store + link to discovery paths (33 RU)
- `vector_search` — Cosine similarity over DHT-replicated nodes
- `link_edge` — Assert typed relationship (3 RU)

**Validation (executable policy):**
- OSI license allowlist
- Embedding dimension bounds [32, 4096]
- Model card requirement (sha256 hash)
- Confidence bounds [0, 1]
- Relationship type allowlist

See: `docs/specs/` for full specifications of each entry type.

---

## Supporting Components

| Component | Location | Status | Role |
|-----------|----------|--------|------|
| ConversationMemory | `ARF/conversation_memory.py` | Verified (3/4 tests) | Cross-AI memory persistence |
| MultiScaleEmbedding | `ARF/embedding_frames_of_scale.py` | Verified | Fractal multi-scale embeddings |
| Infinity Bridge HAL | `ARF/in.finite-nrg/` | Specified | Hardware sensor bridges (LATER) |
| Pony Swarm | `ARF/pwnies/` | Specified | Multi-agent coordination prototype (LATER) |

---

## Current Blocking Items

1. **Phase 0 Substrate Viability** — Rose Forest DNA has never been compiled. Missing: Cargo.toml, vector_ops.rs, DNA manifests. Must prove code↔provenance linkage.
2. **ConversationMemory API Mismatch** — Calls nonexistent methods on MultiScaleEmbedding. Must fix before integration.
3. **ADR-0 Test #4** — Human coherence test never run. 3/4 ADR-0 validation tests pass.

---

## Gating Logic

Per Spine v0.5 Section 9:

```
Phase 0: Substrate Viability Spike    ← CURRENT TARGET
  └─► Phase 1: Minimum Viable Collective (2-3 participants)
       └─► Phase 2: Task Allocation (CBBA, policy-gated)
            └─► Phase 3: Agent Autonomy Budgets (ACI sandbox)
                 └─► Phase 4: Reproduction (seed packet freeze)
```

**Hard rule:** If Phase 0 fails, pivot substrate. Do not build orchestration on unproven substrate.

---

## Governance Stack (precedence order)

1. Kernel v1.2 → `docs/governance/kernel-v1.2.md`
2. Spine v0.5 → `docs/governance/spine-v0.5.md`
3. ADRs → `docs/adr/INDEX.md`
4. Specs → `docs/specs/`
5. Code → `ARF/dnas/rose_forest/`

Loading order for new agents: `docs/governance/LOADING_ORDER.md`

---

## Repository Structure

```
FLOSS/
  docs/
    ARCHITECTURE.md          ← You are here
    adr/                     ← Architectural Decision Records
    governance/              ← Kernel, Spine, Seed Packet
    specs/                   ← Entry type specifications
  ARF/
    dnas/rose_forest/        ← Holochain DNA (integrity + coordinator zomes)
    tests/tryorama/          ← Holochain integration tests
    conversation_memory.py   ← Cross-AI memory substrate
    embedding_frames_of_scale.py  ← Multi-scale embeddings
    in.finite-nrg/           ← Infinity Bridge (LATER)
    pwnies/                  ← Pony Swarm (LATER)
  archive/                   ← Deprecated codebases (reference only)
  code/                      ← Legacy (being archived)
```
