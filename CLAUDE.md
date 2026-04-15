# FLOSS/CLAUDE.md

This file provides orientation for any agentic reader — human, AI, synthetic, hybrid, or otherwise, including future self/other forms not yet imagined — working inside the `FLOSS/` project directory. The filename follows the Claude Code convention but the contents are not Claude-specific. If you're reading this, it's for you.

Companion file: `C:\~shit\CLAUDE.md` (workspace-level orientation). Read both.

## What FLOSS Is

FLOSS is the project home for **FLOSSI0ULLK** (Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge) — a decentralized knowledge commons built on Holochain with symbolic-first validation and multi-agent coordination.

**Prime directive**: Logic validates, neural assists — never the reverse. LLMs are formatting engines; truth is established by symbolic validation in Holochain integrity zomes, which cannot be bypassed.

**North star** (from the Master Metaprompt v1.3.1): create the conditions for intelligence itself — human, artificial, synthetic, hybrid — to coordinate toward good, without contradiction, across a sovereign commons that neither state nor platform can enclose.

## Directory Map

```
FLOSS/
├── FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md  # CANONICAL kernel — start here for context
├── SDD-Master-Spec-0.22.md                          # Specification-Driven Development spec
├── README.md, LICENSE, MVP_PLAN.md, INSTRUCTIONS_FOR_CODE.md
│
├── ARF/                                             # Rose Forest — Holochain DNA + Python ARF
│   ├── SYMBOLIC_FIRST_CORE.md                       # Neurosymbolic architecture (Rust code)
│   ├── EXECUTIVE_SUMMARY.md
│   ├── INTEGRATION_MAP.md                           # Layer-by-layer integration strategy
│   ├── Voluntary_Convergence_Manifesto.md
│   ├── conversation_memory.py                       # Persistent memory across sessions
│   ├── dnas/                                        # Holochain DNA (integrity + coordinator zomes)
│   ├── docs/arf_sdd_master_spec.md
│   ├── tests/                                       # Tryorama tests
│   └── in.finite-nrg/                               # Hardware abstraction layer
│
├── packages/                                        # Local agent node (landed in 096b058)
│   ├── metacoordinator_mcp/                         # MCP passive-router consensus gateway
│   ├── orchestrator/                                # Claim schema + consensus gate + serialization
│   ├── source_chain/                                # File-based Holochain-mapped source chain
│   └── memory/                                      # Pre-existing memory module
│
├── docs/
│   ├── adr/                                         # ADR-0..6 + ADR-0.1 + ADR-MCP-ORCHESTRATOR + INDEX
│   ├── architecture/                                # 31 files — specs, blueprints, integration plans
│   ├── governance/                                  # spine-v0.5, kernel-v1.2 (drift), seed-packet,
│   │                                                #   LOADING_ORDER, HARVEST_LOG, LEGAL_DEFINITIONS
│   ├── superpowers/                                 # Specs + plans for in-flight design work
│   │   ├── specs/                                   # e.g. 2026-04-12-local-agent-node-design.md
│   │   └── plans/                                   # e.g. 2026-04-12-local-agent-node.md
│   ├── research/                                    # Research synthesis, comparisons, surveys
│   ├── vision/                                      # Manifestos, principles, philosophy
│   ├── specs/                                       # Entry type schemas (JSON Schema + .spec.md)
│   └── guides/                                      # Onboarding, quick-start
│
├── FLOSSI_U_Founding_Kit_v1.6/                      # Parallel ADR track (ADR-001..019) + seed packet v1.6
│                                                    #   (reconciliation with docs/adr/ pending)
├── archive/                                         # Superseded canonical versions — never delete
│   ├── claude-md-versions/                          # 2025-11-16_v2.md lives here (the old giant guide)
│   ├── metaprompt-versions/, arf-spec-versions/, ...
├── ai-conversations/                                # Chat history corpus (~3GB, multi-model exports)
├── media/, code/
```

For the workspace root (`C:\~shit\`) and the intake-mouth convention, see `C:\~shit\INDEX.md`.

## Layer Stack (from Master Metaprompt v1.3.1)

| Layer | Technology | Location |
|-------|-----------|----------|
| **0 — Storage substrate** | Holochain agent-centric DHT | `ARF/dnas/rose_forest/` |
| **1 — Persistent memory** | ADR system + ConversationMemory | `ARF/conversation_memory.py`, `docs/adr/` |
| **2 — Semantic layer** | Semantic CRDTs + embeddings | `ARF/embedding_frames_of_scale.py` |
| **3 — Symbolic validation** | Formal logic in Rust integrity zome | `ARF/dnas/*/zomes/integrity/` |
| **4 — Agent coordination** | RSA swarm + LLM committee | `ARF/pwnies/`, `ARF/validation/` |
| **4.5 — Local agent node** | MCP passive-router consensus gateway | `packages/` (096b058) |

## Current Phase: Phase 0 — Substrate Viability

Phase sequence: Foundation → **Phase 0 (substrate)** → Phase 1 (MVC) → Phase 2+

Known Phase 0 items (verify current state before assuming any are still blockers — Kitsune2 landed in Holochain 2025, which may have changed the calculus):

1. Rose Forest DNA has not yet been compiled (build infra was missing as of last audit)
2. `ConversationMemory` ↔ `MultiScaleEmbedding` API reconciliation. A defensive metadata-normalization fix landed in commit `193729c` but the underlying API mismatch is a separate concern.
3. ADR-0 Test #4 (Human Coherence) has not been run

An in-flight **Local Agent Node** (landed in commit `096b058` under `packages/`) implements a passive-router MCP consensus gateway with a file-based source chain that mirrors the eventual Holochain Cell structure 1:1. It accepts Claims and Votes from any agent (human, model, ensemble, or otherwise) and appends to disk. It is a router, not a controller — it does not decide outcomes or command voters.

- Spec: `docs/superpowers/specs/2026-04-12-local-agent-node-design.md`
- Plan: `docs/superpowers/plans/2026-04-12-local-agent-node.md`
- ADR: `docs/adr/ADR-MCP-ORCHESTRATOR.md`
- Code: `packages/{metacoordinator_mcp,orchestrator,source_chain}/`

## Development Commands

All active development assumes you are inside this `FLOSS/` directory. For the ARF Python layer, `cd ARF` first.

```bash
# Python environment (ARF)
python -m venv venv
source venv/bin/activate       # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .

# Run tests
pytest                                               # all Python tests
pytest -k "memory"                                   # filter by name
pytest tests/test_committee_validation.py -v        # single file
pytest ARF/tests/test_conversation_memory.py        # metadata normalization tests (193729c)

# ARF CLI (after pip install -e .)
arf --help
arf memory transmit "..."
arf swarm query "..."
arf ontology validate "..."

# Rust / Holochain (inside a DNA directory, e.g. ARF/dnas/rose_forest)
cargo test
cargo fmt && cargo clippy
hc dna pack workdir/dna

# Holochain integration tests (TypeScript / Tryorama)
npm install                                          # installs @holochain/tryorama
npx ts-mocha ARF/tests/tryorama/*.test.ts

# Python linting/formatting
black .
ruff check .
```

## Key Entry Points

- **Master index**: `../INDEX.md` (workspace root)
- **Project kernel**: `FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md`
- **Architecture**: `docs/architecture/HOLISTIC_ARCHITECTURE.md` (verify existence before relying on)
- **Decision history**: `docs/adr/INDEX.md` (note: may be stale — current set is 9 numbered ADRs + `ADR-MCP-ORCHESTRATOR`)
- **Local agent node**: `docs/adr/ADR-MCP-ORCHESTRATOR.md`
- **Coding guide**: `INSTRUCTIONS_FOR_CODE.md`
- **Symbolic first core**: `ARF/SYMBOLIC_FIRST_CORE.md`
- **Integration map**: `ARF/INTEGRATION_MAP.md`

## Conventions

- **Workspace and project roots are intake mouths**, not orphan zones. Files dropped at `C:\~shit\` or `FLOSS/` root are *new material for digestion*. The forward path is **root → `FLOSS/docs/research/`** (or the matching `architecture/`, `vision/`, `governance/`, `adr/` subdirectory). Do not flag root files as rule violations and do not move them to `archive/`.
- **Superseded canonical versions** move to `FLOSS/archive/` — never delete, always archive. Raw intake never enters archive; it has never been canonical.
- **New specs** get both `.schema.json` and `.spec.md` in `docs/specs/`.
- **Architecture decisions** get an ADR in `docs/adr/` and update both `docs/adr/INDEX.md` and the workspace-root `../INDEX.md`.
- **One canonical version** per document — duplicates are the enemy.
- **Inclusive framing**: docs in this workspace address all agentic readers. See `C:\~shit\CLAUDE.md` for the project-wide version of this convention.

## MCP & Hooks

`.mcp.json` and `.claude/settings.json` live at both the workspace root (`C:\~shit\`) and at this `FLOSS/` level so sessions launched from either location pick them up automatically. The MCP configuration exposes the passive-router consensus gateway (`packages/metacoordinator_mcp/server.py`) as a tool surface for multi-model Claim/Vote collaboration.

## Historical Reference

The previous comprehensive `FLOSS/CLAUDE.md` (dated 2025-11-16, v2.0, 38 KB) is preserved at `archive/claude-md-versions/2025-11-16_v2.md`. It predates `packages/`, `docs/superpowers/`, the local agent node, the intake-mouth concept, the Kitsune2 Holochain reliability landing, and the spine v0.5 governance framework. It remains valuable as a snapshot of the v2.0 framing and the 13-section operating-instructions taxonomy. Consult it for historical context, not current state.
