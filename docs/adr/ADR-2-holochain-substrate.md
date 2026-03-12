# ADR-2: Holochain as Runtime Substrate

**Date:** 2026-03-05
**Status:** PROPOSED
**Truth Status:** Specified
**Participants:** Anthony (Human), Claude (Architect), Multi-AI Collective

## Context

FLOSSIOULLK requires a runtime substrate (Plane B per Spine v0.5 Section 5) that provides:
- Agent-centric identity (not server-centric)
- Validation at the edge (not central moderation)
- Content-addressable storage with provenance
- Eventual consistency without global consensus
- Offline-first operation
- Fork visibility

Multiple substrates were evaluated over 13+ months of iteration, including custom libp2p stacks, blockchain approaches, and centralized databases.

## Decision

**Adopt Holochain (hdi/hdk 0.5.x) as the Plane B runtime substrate.**

### Rationale

1. **Agent-centric DHT** aligns with Carrier Equivalence (ADR-1): distributed authority, no central dispatcher
2. **Validation zomes** implement executable policy (NormKernel v0) — validation is law, not afterthought
3. **Source chains** provide per-agent provenance without global ledger
4. **Warrants** enable misbehavior evidence and immune-system-like responses
5. **Gossip protocol** achieves O(log n) eventual consistency matching the "voluntary resonance" principle
6. **No blockchain consensus overhead** — avoids Proof-of-Work / Proof-of-Stake centralization pressures

### Implementation

The Rose Forest DNA (`ARF/dnas/rose_forest/`) implements the substrate:
- **Integrity zome**: RoseNode, KnowledgeEdge, BudgetEntry, ThoughtCredential entry types with validation
- **Coordinator zome**: add_knowledge, vector_search, link_edge, budget management
- **Semantic sharding**: Quantized embedding paths for distributed discovery

### Version Pinning

- Target: hdi/hdk 0.5.x (latest stable as of 2026-03)
- Previous codebase (`code/project/`) used hdk 0.1.0 — deprecated and incompatible
- Version drift between 0.5.x releases managed via Cargo.toml pinning + holonix flake

## Consequences

### Positive
- Inherits signatures, CRDTs, networking — deletes custom code
- Validation-as-law raises trust floor without central moderators
- Agent-centric model supports sovereignty and offline-first
- Existing Rose Forest zome code is architecturally aligned

### Negative
- Holochain ecosystem is smaller than Ethereum/Solana; fewer libraries
- Development requires nix (holonix) which complicates Windows development (WSL2 required)
- API stability between 0.5.x releases not guaranteed
- Debugging distributed Holochain apps is harder than centralized alternatives

### Mitigations
- WSL2 + holonix for Windows development; CI on Linux
- Pin exact crate versions in Cargo.toml
- Phase 0 substrate viability spike validates compilation before building further

## Phase 0 Gate

Per Spine v0.5 Section 9, this decision is validated by the Phase 0 substrate viability spike:
- Rose Forest DNA compiles to WASM
- Tryorama tests pass (create, search, validate, budget)
- Code-provenance linkage proven
- Python-Holochain round-trip works

**If Phase 0 fails, pivot substrate.** This ADR would be superseded.

## Related Decisions

- ADR-0: Recognition Protocol (conversation as coordination substrate)
- ADR-1: Carrier Equivalence (distributed flow geometry)
- ADR-4: Spec-Driven Development (spec constrains implementation)
- Spine v0.5 Section 5: Two-Plane Architecture
- Spine v0.5 Section 9: Substrate-First Gating
