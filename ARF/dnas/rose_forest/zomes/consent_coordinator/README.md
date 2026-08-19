# consent_coordinator zome

**Purpose:** Application-call surface for ADR-12 ConsentPayload / ConsentDecision records. Wraps [`consent_integrity`](../consent_integrity/) entry creation + link creation + the cross-entry `scope_granted ⊆ consent_scope` check (which requires resolving the linked payload — cannot live in pure-deterministic validate).

**Why a separate coordinator (and not just an extension of [`coordinator`](../coordinator/)):** linking two integrity crates into one coordinator produced duplicate Holochain export symbols. Each integrity zome gets its own coordinator dependency.

**Crate name vs zome name:** the Cargo crate is named `consent` (per `Cargo.toml`); the DNA-level zome name is `consent` (per `dna.yaml`). Holonix `hc app pack` emits `consent.wasm`. The `consent_coordinator/` folder name reflects role, not crate name.

**Status:** ⚠️ Specified with verified implementation slices
**Truth status — verified 2026-05-26:** crate compiles clean to `wasm32-unknown-unknown`; integrates cleanly with [`consent_integrity`](../consent_integrity/) in the DNA bundle.
**SDD references:** [spec](../../../../docs/specs/consent-payload.spec.md) · [ADR-12](../../../../docs/adr/ADR-12-consent-gate-protocol.md)

## Public externs (5)

| Fn | Input | Returns | Purpose |
|---|---|---|---|
| `create_consent_payload` | `CreateConsentPayloadInput` (all ConsentPayload fields, with `refusal_modes` defaulted + `submitted_at` defaulted to `sys_time()`) | `ActionHash` | Creates a ConsentPayload entry + links from `consent_pattern:<hash>` anchor for reverse lookup. |
| `get_consent_payload` | `ActionHash` | `Option<ConsentPayload>` | Read by hash. |
| `create_consent_decision` | `CreateConsentDecisionInput` (includes `payload_action_hash` reference) | `ActionHash` | Enforces `scope_granted ⊆ consent_scope` via `ensure_scope_subset()` after resolving the referenced ConsentPayload. Creates ConsentDecision entry + links from payload → decision + from `consent_decider:<did>` anchor → decision. |
| `get_consent_decision` | `ActionHash` | `Option<ConsentDecision>` | Read by hash. |
| `get_consent_decisions_for_payload` | `ActionHash` (of payload) | `Vec<ConsentDecision>` | List all decisions linked to a payload via `PayloadToDecision`. |

## Default values applied

- `refusal_modes` defaults to all four: `[Reject, BoundedAccept, TouristObserve, CounterPropose]`.
- `submitted_at` / `decided_at` default to `sys_time()` if not provided by caller.

## Error semantics

| Error | Condition |
|---|---|
| `E_SCOPE_NOT_REQUESTED` | `create_consent_decision`: `scope_granted` contains a scope the referenced ConsentPayload did not list in its `consent_scope`. Fail-fast before the entry is even constructed. |
| `WasmErrorInner::Guest(...)` from `consent_integrity::validate` | Any of the 10 single-entry invariants (see [`consent_integrity README`](../consent_integrity/README.md)). |

## Cross-zome dependencies

- [`consent_integrity`](../consent_integrity/) — re-exports `EntryTypes`, `LinkTypes`, enums (`BlastRadius`, `ConsentScope`, `Outcome`, `PatternType`, `RefusalMode`), and structs (`ConsentPayload`, `ConsentDecision`).
- `hdk` workspace dependency (HDK 0.6.1).

The DNA wiring at [`dnas/rose_forest/workdir/dna.yaml`](../../workdir/dna.yaml) declares the coordinator's dependency on `consent_integrity` so the integrity-zome ops are available in the cell.

## Tests

No native unit tests in this zome — the validation surface is upstream in [`consent_integrity`](../consent_integrity/) (10/10 pass). End-to-end coverage via Tryorama at [`ARF/tests/tryorama/consent_gate.test.ts`](../../../../tests/tryorama/consent_gate.test.ts) is currently blocked (see M13 — no compatible `@holochain/tryorama` version for hc 0.6.1).

## Pending work

- Action-time gating: when a governed-pattern transmission (kernel injection, voter-persona import, etc.) attempts to land, the responsible coordinator should look up a valid ConsentDecision for the recipient_did before allowing the transmission. Not yet wired.
- DID ↔ action-header binding: the `proposer_did` / `recipient_did` / `decider_did` strings are currently treated as opaque. A future pass should bind them to verified Holochain agent pubkeys at the action header for non-repudiation.
- Cross-frame validation with the consensus gateway (`packages/metacoordinator_mcp/`).
