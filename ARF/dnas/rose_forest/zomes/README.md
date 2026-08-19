# Rose Forest zomes

Index of all zome folders under `ARF/dnas/rose_forest/zomes/`. **Per [`FLOSS/CLAUDE.md`](../../../../CLAUDE.md) and [`ARF/Cargo.toml`](../../../Cargo.toml), only 4 zomes are active in the current workspace.** The other 6 folders exist on disk as excluded pre-migration dev artifacts and do NOT participate in the current build.

## Active workspace members (4)

These are the four zomes listed in `ARF/Cargo.toml` `[workspace] members`. They inherit `hdi = "=0.7.1"` / `hdk = "=0.6.1"` from the workspace and pack into [`workdir/rose_forest.dna`](../workdir/) → [`ARF/workdir/rose_forest.happ`](../../../workdir/).

| Folder | DNA zome name | Layer | Doc |
|---|---|---|---|
| [`integrity/`](integrity/) | `rose_forest_integrity` | Integrity (substrate) | [README](integrity/README.md) — RoseNode + KnowledgeEdge + KnowledgeTriple + BudgetEntry + ThoughtCredential validation |
| [`coordinator/`](coordinator/) | `rose_forest` | Coordinator | [README](coordinator/README.md) — 9 externs (add_knowledge, vector_search, link_edge, budget_status, create_thought_credential, assert_triple, query_triples, get_triple_record, get_predicates) + RU budget + ontology dispatch + vector ops (8/8 tests) |
| [`consent_integrity/`](consent_integrity/) | `consent_integrity` | Integrity (substrate) | [README](consent_integrity/README.md) — ConsentPayload + ConsentDecision per [ADR-12](../../../../docs/adr/ADR-12-consent-gate-protocol.md); 10/10 native unit tests |
| [`consent_coordinator/`](consent_coordinator/) | `consent` | Coordinator | [README](consent_coordinator/README.md) — 5 externs wrapping consent_integrity + cross-entry `scope_granted ⊆ consent_scope` check |

## Excluded pre-migration zome folders (6)

These folders exist on disk from the pre-2026-05-19 Holochain 0.4 line. They are NOT in the workspace `members` list — they do not compile against the current `hdi 0.7.1 / hdk 0.6.1` pinning and must be migrated before re-adding.

| Folder | Original intent | Status | Migration prerequisite |
|---|---|---|---|
| [`hrea_integrity/`](hrea_integrity/) | hREA economic-coordination integrity | Excluded | HDI 0.7 migration + spec re-derivation |
| [`hrea_coordinator/`](hrea_coordinator/) | hREA coordinator | Excluded | Depends on `hrea_integrity` migration |
| [`identity_integrity/`](identity_integrity/) | KERI/ACDC identity integrity | Excluded | HDI 0.7 migration + DID schema decision |
| [`identity_coordinator/`](identity_coordinator/) | Identity coordinator | Excluded | Depends on `identity_integrity` migration |
| [`memory_coordinator/`](memory_coordinator/) | Persistent memory coordinator (Layer 1) | Excluded | HDK 0.6 migration; coordinator without paired integrity is unusual — confirm intent |
| [`ontology_integrity/`](ontology_integrity/) | Standalone ontology integrity (the 38-passing-tests note in [`MVP_PLAN.md`](../../../../MVP_PLAN.md)) | Excluded | HDI 0.7 migration; in current build the ontology dispatch is folded into the main `integrity` zome's `validate_knowledge_triple` predicate whitelist |

The sibling folder [`ARF/dnas/infinity_bridge/`](../../infinity_bridge/) is a separate DNA (not a zome in this DNA) and is similarly excluded pre-migration.

## Why the split

Linking two integrity crates into one coordinator produced duplicate Holochain export symbols (the `validate` extern collides). Each integrity zome therefore gets its own coordinator dependency. That's why `consent_coordinator` exists as a separate folder rather than being absorbed into `coordinator`.

## Building + packing

From a holonix `main-0.6` dev shell (WSL on Windows):

```sh
cd FLOSS/ARF
cargo build --release --target wasm32-unknown-unknown   # ~38s incremental, ~5min cold
hc dna pack dnas/rose_forest/workdir/                    # emits rose_forest.dna (~2.0 MB)
hc app pack workdir/                                     # emits rose_forest.happ (~2.0 MB)
```

DNA manifest: [`workdir/dna.yaml`](../workdir/) (manifest_version `"0"`, `path:` fields per holochain 0.6 schema).
hApp manifest: [`../../workdir/happ.yaml`](../../../workdir/happ.yaml).

## Native unit tests

```sh
cargo test -p consent_integrity   # 10/10 pass
cargo test -p rose_forest         # 8/8 pass (vector_ops)
cargo test -p rose_forest_integrity   # 0 tests currently
cargo test -p consent             # 0 tests currently (coordinator)
```

## Holochain integration tests

Tryorama scenarios at [`ARF/tests/tryorama/`](../../../tests/tryorama/) currently fail at `AdminWebsocket.installApp` — no `@holochain/tryorama` version pairs cleanly with `hc 0.6.1`. See [`MVP_PLAN.md`](../../../../MVP_PLAN.md) §"#1 blocker RESOLVED (partially)" and the M13 path-forward options.

## Cross-refs

- Substrate architecture: [`docs/architecture/HOLISTIC_ARCHITECTURE.md`](../../../../docs/architecture/HOLISTIC_ARCHITECTURE.md)
- Symbolic-first design: [`ARF/SYMBOLIC_FIRST_CORE.md`](../../../SYMBOLIC_FIRST_CORE.md)
- ADRs: [`ADR-2 Holochain Substrate`](../../../../docs/adr/ADR-2-holochain-substrate.md), [`ADR-12 Consent Gate`](../../../../docs/adr/ADR-12-consent-gate-protocol.md), [`ADR-Suite v2.0`](../../../../docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md)
- Specs: [`docs/specs/`](../../../../docs/specs/) (rose-node, knowledge-edge, knowledge-triple, budget-entry, consent-payload, provenance-packet, etc.)
- MVP plan: [`MVP_PLAN.md`](../../../../MVP_PLAN.md)
