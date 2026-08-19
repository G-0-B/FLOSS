# coordinator zome (`rose_forest`)

**Purpose:** Application-call surface for the Rose Forest knowledge graph. Wraps [`integrity`](../integrity/) entry creation + link creation + vector search + budget enforcement + ontology dispatch.

**Crate name vs zome name:** Cargo crate `rose_forest`; DNA zome `rose_forest` per [`dna.yaml`](../../workdir/dna.yaml); holonix `hc app pack` emits `rose_forest.wasm`.

**Status:** ⚠️ Specified with verified implementation slices
**Truth status — verified 2026-05-26:** crate compiles clean to `wasm32-unknown-unknown`; **vector_ops 8/8 native unit tests pass**; budget engine compiles; ontology dispatch compiles.
**Truth status — NOT verified end-to-end:** Tryorama integration (blocked on M13).
**SDD references:** [knowledge-edge spec](../../../../docs/specs/knowledge-edge.spec.md) · [knowledge-triple spec](../../../../docs/specs/knowledge-triple.spec.md) · [budget-entry spec](../../../../docs/specs/budget-entry.spec.md)

## Public externs (9)

| Fn | Input | Returns | Purpose |
|---|---|---|---|
| `add_knowledge` | `AddNodeInput` (content + embedding + license + metadata) | `ActionHash` | Creates a RoseNode; consumes 33 RU from caller's budget; links into `AllNodes` anchor. |
| `vector_search` | `SearchInput` (query embedding + top-k) | `Vec<SearchResult>` | Cosine-similarity search across all RoseNodes; returns top-k results with scores. Powered by `vector_ops.rs` (8/8 tests). |
| `link_edge` | `AddEdgeInput` (from, to, relationship, confidence) | `ActionHash` | Creates a KnowledgeEdge between two nodes; links from source node. |
| `budget_status` | `()` | `BudgetState` (remaining_ru, window_start, etc.) | Reports caller's current budget. |
| `create_thought_credential` | `CreateThoughtCredentialInput` (connotation + embedding + provenance) | `ActionHash` | Ternary-connotation attestation per Yumeichan framework. |
| `assert_triple` | `AssertTripleInput` (subject, predicate, object, confidence) | `ActionHash` | Creates a `KnowledgeTriple`; consumes 2 RU; links into `TriplesBySubject` + `TriplesByPredicate` anchors. |
| `query_triples` | `QueryTriplesInput` (by subject / by predicate / by both) | `Vec<TripleResult>` | Symbolic-first query — returns triples matching criteria. |
| `get_triple_record` | `ActionHash` | `Option<Record>` | Raw record fetch by hash. |
| `get_predicates` | `()` | `Vec<PredicateInfo>` | Lists all registered ontology predicates (currently hardcoded in `integrity`; future ADR target for data-driven registration). |

## Budget enforcement

`budget.rs` implements Resource Unit (RU) accounting with rolling 24-hour windows:

- Default cap: 100 RU per agent per 24h
- `add_knowledge` costs 33 RU; `assert_triple` costs 2 RU
- Window rolls when `sys_time() - window_start > 24h`
- Operations fail with `E_BUDGET_EXHAUSTED` when remaining RU < cost

The validation invariants for budget entries themselves live in [`integrity`](../integrity/); enforcement at call time lives here.

## Vector ops (`vector_ops.rs` — **8/8 tests pass**)

| Test | Covers |
|---|---|
| `test_cosine_identical_vectors` | dot product symmetric path |
| `test_cosine_orthogonal_vectors` | zero-similarity edge |
| `test_cosine_opposite_vectors` | -1 similarity edge |
| `test_cosine_zero_vector_returns_zero` | zero-vector safety |
| `test_distance` | Euclidean distance |
| `test_normalize` | unit-vector projection |
| `test_cosine_*` | additional coverage |

Run: `cargo test -p rose_forest`.

## Ontology dispatch (`ontology.rs`)

Routes `assert_triple` calls through the registered predicate whitelist (defined in [`integrity`](../integrity/)). Future ADR target: shift from hardcoded const slice to data-driven ontology registration via a separate ontology entry type.

## Cross-zome dependencies

- [`integrity`](../integrity/) — imports `EntryTypes`, `LinkTypes`, all 5 structs (`RoseNode`, `KnowledgeEdge`, `KnowledgeTriple`, `BudgetEntry`, `ThoughtCredential`).
- `hdk` workspace dependency (HDK 0.6.1).

DNA wiring at [`dnas/rose_forest/workdir/dna.yaml`](../../workdir/dna.yaml) declares this coordinator's dependency on `rose_forest_integrity`.

## Module layout

```
src/
├── lib.rs           # 9 hdk_extern fns + input/output structs
├── budget.rs        # RU accounting + 24h window engine
├── ontology.rs      # Predicate dispatch + ontology helpers
└── vector_ops.rs    # Cosine similarity, distance, normalize (8 tests)
```

## Pending work

- Make ontology predicate registration data-driven (currently hardcoded const slice in `integrity::validate_knowledge_triple`).
- Wire ThoughtCredential creation to consume budget (currently free).
- Tryorama end-to-end coverage of all 9 externs once M13 substrate decision lands. Test scaffolding exists at [`ARF/tests/tryorama/rose_forest.test.ts`](../../../../tests/tryorama/rose_forest.test.ts) but currently fails at `installApp` due to client/conductor version mismatch.
