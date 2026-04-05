# Code Style & Conventions

## Rust (Holochain Zomes)

- **Entry types**: Defined in integrity zome with `#[hdk_entry_helper]` + `#[derive(Clone, PartialEq)]`
- **Validation**: In integrity zome's `validate()` — returns `ValidateCallbackResult::Valid` or `Invalid(reason)`
- **Error codes**: Prefixed with `E_` (e.g., `E_BUDGET_EXCEEDED`, `E_LICENSE`, `E_EMBED_DIM`)
- **Link types**: Minimal — only `AllNodes` and `Edge` (removed ShardMember and AgentBudget as Holochain-native alternatives exist)
- **Budget state**: Queried from local source chain via `ChainQueryFilter`, NOT from DHT links
- **Constants**: SCREAMING_SNAKE_CASE with doc comments explaining the "why"
- **Paths**: Used for DHT discovery (e.g., `Path::from("all_nodes")`)

## Python

- **Type hints**: Expected but not enforced everywhere yet
- **Async**: Used in orchestrator (asyncio + websockets)
- **Testing**: pytest, with offline and integration test separation
- **Serialization**: msgpack for Holochain wire protocol
- **Naming**: snake_case for functions/variables, PascalCase for classes

## TypeScript (Tests)

- **Framework**: Vitest + Tryorama 0.17
- **AJV import**: `import Ajv from "ajv/dist/2020.js"` (NOT `"ajv"` — draft 2020-12)
- **libsodium fix**: Postinstall symlink script (`fix-libsodium-esm.mjs`)

## JSON Schema

- Draft 2020-12 (`$schema: "https://json-schema.org/draft/2020-12/schema"`)
- Located in `docs/specs/`
- Spec-code linkage: RoseNode's `model_card_hash` records **both** SHA-256 and BLAKE3 digests of the spec prose; provenance records MUST include both digests for verifiable integrity (per FLOSS provenance requirements)

## General

- Comments explain WHY, not WHAT
- Spec-first: specification before code
- Now/Later/Never filter for all new work
- No magic numbers — constants with explanatory comments
