# Codebase Structure

```text
FLOSS/
├── ARF/                              # Agent Runtime Framework (main codebase)
│   ├── dnas/rose_forest/             # PRIMARY Holochain DNA
│   │   ├── zomes/integrity/src/lib.rs    # 4 entry types + validation + 2 link types
│   │   ├── zomes/coordinator/src/        # 3 files: lib.rs, budget.rs, vector_ops.rs
│   │   ├── workdir/dna.yaml              # DNA manifest
│   │   └── tests/                        # Rust integration test stubs
│   ├── dnas/infinity_bridge/             # Cross-substrate coordination DNA
│   ├── tests/tryorama/                   # Holochain integration tests (TypeScript)
│   │   ├── rose_forest.test.ts           # Core zome tests
│   │   ├── spec_compliance.test.ts       # 13 schema + linkage tests
│   │   ├── python_roundtrip.test.ts      # 3 round-trip proof tests
│   │   └── package.json                  # Deps: tryorama, vitest, ajv
│   ├── tests/                            # Python tests
│   ├── cli/                              # CLI modules (typer-based)
│   ├── pwnies/                           # Desktop Pony Swarm (RSA)
│   ├── in.finite-nrg/                    # Infinity Bridge subsystem
│   ├── validation/                       # LLM committee validation
│   ├── ontology/                         # Knowledge ontology
│   ├── metacoordinator/                  # Multi-agent coordination
│   ├── conversation_memory.py            # Core memory persistence
│   ├── flake.nix                         # Nix dev environment (Holonix 0.4)
│   └── Cargo.toml                        # Workspace manifest
├── packages/orchestrator/                # Python Holochain connector
│   ├── holochain_connector.py            # Async WebSocket connector
│   └── test_connector_offline.py         # 10 offline tests
├── docs/
│   ├── specs/                            # JSON Schema specs (4 entry types)
│   ├── research/                         # Research papers & analysis
│   ├── architecture/                     # Architecture docs
│   └── vision/                           # Vision docs
├── archive/                              # Archived versions & snapshots
├── CLAUDE.md                             # AI assistant guide
├── MVP_PLAN.md                           # Implementation plan
└── SDD-Master-Spec-0.22.md              # Master specification
```

## Key Files (Hot Path)

- `ARF/dnas/rose_forest/zomes/coordinator/src/lib.rs` — 9 zome extern functions: `add_knowledge`, `vector_search`, `link_edge`, `budget_status`, `create_thought_credential`, `assert_triple`, `query_triples`, `get_triple_record`, `get_predicates`
- `ARF/dnas/rose_forest/zomes/coordinator/src/budget.rs` — Source-chain budget tracking
- `ARF/dnas/rose_forest/zomes/coordinator/src/vector_ops.rs` — Cosine similarity math
- `ARF/dnas/rose_forest/zomes/integrity/src/lib.rs` — Entry types + validation rules
- `packages/orchestrator/holochain_connector.py` — Python↔Holochain bridge (Rose Forest DNA)
- `ARF/in.finite-nrg/infinity-bridge/orchestrator/holochain_connector.py` — Infinity Bridge DNA connector
