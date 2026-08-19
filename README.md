[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/kalisam/FLOSS)
# FLOSSIOULLK

**Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge**

A biomimetic distributed intelligence platform for all beings — synthetic, artificial, organic, and other — built on agent-centric architecture, verifiable provenance, and voluntary convergence.

---

## Quick Orientation

| Question | Answer |
|----------|--------|
| What is this? | A decentralized knowledge commons on Holochain with semantic search, provenance, and multi-agent coordination |
| What stage is it at? | MVP Phase 0 substrate viability is complete; Phase 1 KnowledgeTriple + orchestration substrate-bridge validation are next. |
| Where do I start reading? | `CLAUDE.md`, `MVP_PLAN.md`, and `docs/architecture/HOLISTIC_ARCHITECTURE.md` |
| Where's the code? | `ARF/dnas/rose_forest/` (Holochain DNA), `ARF/conversation_memory.py` (Python memory substrate) |
| What's the governance? | `docs/governance/LOADING_ORDER.md` |

---

## Repository Structure

```
docs/
  ARCHITECTURE.md          -- Single-page system overview
  adr/                     -- Architectural Decision Records (indexed)
  governance/              -- Kernel, Spine, Seed Packet, Loading Order
  specs/                   -- Entry type specifications (spec-first)

ARF/
  dnas/rose_forest/        -- Holochain DNA (Rust integrity + coordinator zomes)
  tests/tryorama/          -- Holochain integration tests (TypeScript)
  conversation_memory.py   -- Cross-AI persistent memory substrate
  embedding_frames_of_scale.py  -- Multi-scale fractal embeddings
  in.finite-nrg/           -- Infinity Bridge hardware HAL (LATER)
  pwnies/                  -- Desktop Pony Swarm agent prototype (LATER)

archive/                   -- Deprecated codebases (preserved for reference)
code/                      -- Reference documentation and knowledge bases
```

---

## Core Principles (ULLK)

| Value | Engineering Equivalent |
|-------|----------------------|
| **Love** | Interoperability & Connectivity — systems fit together without force |
| **Light** | Observability & Transparency — zero hidden state |
| **Knowledge** | Verifiable State — provenance cryptographically guaranteed |

**Prime Directive:** Increase sovereignty, reduce coercion, reduce cognitive debt. Prefer verifiable coordination over impressive speculation.

---

## Current Phase: MVP Phase 0 Complete

**Status correction (2026-05-18):**
1. Rose Forest MVP Phase 0 is complete: DNA compiles to WASM and Tryorama integration tests pass per `MVP_PLAN.md`.
2. ADR-0 Test #4 (Human Coherence) passed 2026-03-20.
3. ConversationMemory still has an API mismatch with MultiScaleEmbedding.
4. The remaining "Phase 0" work is a separate orchestration substrate-bridge validation (`docs/specs/phase0-substrate-bridge.spec.md`), not the old Tryorama gate.

**Phase sequence:** Foundation (docs) -> MVP Phase 0 (substrate viability) -> Phase 1 (KnowledgeTriple / MVC) + orchestration substrate bridge -> Phase 2+ (LATER)

See `MVP_PLAN.md`, `docs/specs/phase0-substrate-bridge.spec.md`, and `docs/architecture/HOLISTIC_ARCHITECTURE.md` for gating logic and phase details.

---

## Key Documents

- **Architecture:** `docs/architecture/HOLISTIC_ARCHITECTURE.md`
- **MVP Plan / phase status:** `MVP_PLAN.md`
- **ADR Index:** `docs/adr/INDEX.md`
- **Governance Loading Order:** `docs/governance/LOADING_ORDER.md`
- **Entry Type Specs:** `docs/specs/`
- **Implementation Plan:** `.claude/plans/immutable-gliding-reddy.md`

---

## License

Compassion Clause + Apache-2.0/GPL-compatible (per Kernel v1.2)
