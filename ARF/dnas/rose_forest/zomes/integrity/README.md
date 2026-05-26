# integrity zome (`rose_forest_integrity`)

**Purpose:** Core Rose Forest integrity zome. Defines the substrate knowledge-graph entry types and enforces all single-entry validation invariants. This is the original Layer-3 symbolic validation surface ([ADR-2](../../../../docs/adr/ADR-2-holochain-substrate.md), [ADR-Suite v2.0](../../../../docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md)).

**Status:** ⚠️ Specified with verified implementation slices
**Truth status — verified 2026-05-26:** crate compiles clean to `wasm32-unknown-unknown`; integrates with the [`coordinator`](../coordinator/) zome; vector_ops in coordinator has 8/8 native unit tests passing.
**Truth status — NOT verified end-to-end:** Tryorama integration (blocked on M13).
**SDD references:** [knowledge-edge spec](../../../../docs/specs/knowledge-edge.spec.md) · [knowledge-triple spec](../../../../docs/specs/knowledge-triple.spec.md) · [rose-node spec](../../../../docs/specs/rose-node.spec.md) · [budget-entry spec](../../../../docs/specs/budget-entry.spec.md)

## Entry types (5)

| Type | Fields | Purpose |
|---|---|---|
| `RoseNode` | `content: String`, `embedding: Vec<f32>`, `license: String`, `metadata: BTreeMap<String, String>` | A knowledge node — text content plus its embedding for vector search. Metadata must carry `model_id` + `model_card_hash` for provenance. |
| `KnowledgeEdge` | `from: ActionHash`, `to: ActionHash`, `relationship: String`, `confidence: f32` | Directed, weighted, typed edge between two `RoseNode`s. |
| `KnowledgeTriple` | `subject`, `predicate`, `object: String`; `confidence: f32`; `source: AgentPubKey`; `created_at: Timestamp` | Atomic subject–predicate–object fact with mandatory provenance. Core unit of symbolic-first knowledge per [`SYMBOLIC_FIRST_CORE.md`](../../../../ARF/SYMBOLIC_FIRST_CORE.md). |
| `BudgetEntry` | `agent: AgentPubKey`, `remaining_ru: f32`, `window_start: Timestamp` | Tracks an agent's autonomy budget (Resource Units / 24h windows). Prevents single-agent resource monopolization. |
| `ThoughtCredential` | (in coordinator-adjacent module) connotation + ternary attestation | Ternary connotation attestation (Yumeichan framework integration). |

## Link types (4)

| Link | From → To | Use |
|---|---|---|
| `AllNodes` | DNA anchor → RoseNode | Enumerate all nodes |
| `Edge` | RoseNode → KnowledgeEdge | Outgoing edges from a node |
| `TriplesBySubject` | subject anchor → KnowledgeTriple | Query by subject string |
| `TriplesByPredicate` | predicate anchor → KnowledgeTriple | Query by predicate string |

## Validation invariants

### `RoseNode` (`validate_rose_node`)

1. **License whitelist.** Must be one of `MIT`, `Apache-2.0`, `BSD-3-Clause`, `MPL-2.0`, `CC-BY-4.0`. Other licenses rejected with `E_LICENSE`.
2. **Embedding dimension.** `embedding.len() ∈ [32, 4096]`. Else `E_EMBED_DIM`.
3. **Model card required.** `metadata` must include both `model_id` AND `model_card_hash`; hash must start with `sha256:`. Else `E_MODEL_CARD_MISSING`.

### `KnowledgeTriple` (`validate_knowledge_triple`)

1. **Non-empty.** `subject`, `predicate`, `object` each non-empty.
2. **Confidence range.** `confidence ∈ [-1.0, +1.0]` (signed gradient — negative = movement away from truth, aligns with ternary `-1/0/+1` per Yumeichan).
3. **Predicate whitelist.** Predicate must be in the registered ontology namespace: `is_a`, `part_of`, `related_to`, `has_property`, `trained_on`, `improves_upon`, `capable_of`, `evaluated_on`, `relates_to`, `supports`, `contradicts`, `heals`, `releases`, `neutralizes`, `recalibrates`. Else `E_TRIPLE_PREDICATE_UNKNOWN`.

### `KnowledgeEdge` (`validate_knowledge_edge`)

1. **Relationship type whitelist** (same as triple-predicate whitelist).
2. **Confidence range** in `[-1, +1]`.
3. **`from != to`** — self-loops rejected.

### `ThoughtCredential` (validated via `validate_thought_credential`)

- Connotation in valid range; embedding dimension ≥ 32; provenance fields present.

### `BudgetEntry`

- Shape validation only; budget enforcement (cap, refill, consumption) happens in the [`coordinator`](../coordinator/) zome via `budget.rs`.

## Cross-zome dependencies

- **At integrity layer:** none — pure deterministic shape validation.
- **At coordinator layer:** [`coordinator`](../coordinator/) imports `EntryTypes`, `LinkTypes`, and all 5 structs.

## Tests

- Native unit tests in this crate: 0 currently. The validation logic is exercised through `coordinator`'s tests (vector_ops 8/8 pass) and through integration via [`consent_integrity`](../consent_integrity/) test coverage for shared patterns.
- Holochain integration via Tryorama: blocked on M13.
- The earlier "38 passing unit tests in `ontology_integrity`" claim ([MVP_PLAN.md](../../../../MVP_PLAN.md)) refers to a separate, pre-migration zome currently excluded from the workspace per [zomes/README.md](../README.md).

## Pending work

- Add native unit tests covering each `validate_*` branch (parallel to consent_integrity's 10/10 pattern).
- Wire ontology-namespace registration to be data-driven rather than hardcoded const slice (separate ADR target).
- Tryorama coverage once M13 substrate decision lands.
