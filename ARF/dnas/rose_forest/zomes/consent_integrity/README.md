# consent_integrity zome

**Purpose:** First substrate-side enforcement slice for the **Consent Gate Protocol** ([ADR-12](../../../../docs/adr/ADR-12-consent-gate-protocol.md)). Registers `ConsentPayload` + `ConsentDecision` entries and enforces deterministic single-entry shape rules the LLM layer cannot evade.

**Status:** ⚠️ Specified with verified implementation slices
**Truth status — verified 2026-05-26:** Rust crate compiles to `wasm32-unknown-unknown` clean; native unit tests **10/10 pass**; hApp packs in holonix dev shell.
**Truth status — NOT verified end-to-end:** Tryorama integration ([see ADR-12 truth-status](../../../../docs/adr/ADR-12-consent-gate-protocol.md) + [MVP_PLAN.md](../../../../MVP_PLAN.md) — no `@holochain/tryorama` version pairs with hc 0.6.1; substrate-decision tracked as M13).
**SDD references:** [spec](../../../../docs/specs/consent-payload.spec.md) · [schema](../../../../docs/specs/consent-payload.schema.json) · [ADR-12](../../../../docs/adr/ADR-12-consent-gate-protocol.md)

## Entry types

| Type | Purpose |
|---|---|
| `ConsentPayload` | Offer of a memetic pattern (kernel / ADR / frame translation / voter persona / constitution / claim / skill / memory / other) for a recipient's consent. Includes `pattern_id`, `pattern_type`, `pattern_hash` (sha256 hex lowercase, 64 chars), `proposer_did`, `recipient_did`, `blast_radius`, `consent_scope` (non-empty), optional `refusal_modes`, optional `parent_consent_id` chain, rationale. |
| `ConsentDecision` | Decision that answers a payload — `outcome` (Accept / BoundedAccept / Reject / TouristObserve / CounterPropose), `scope_granted` (must be ⊆ payload's `consent_scope`), optional `counter_frame_ref`, rationale, expiry. |

Both struct shapes deliberately omit `agent_pub_key` + `created_at` — those live in the action header per the holochain-agent-skill patterns guide.

## Link types

| Link | From → To | Use |
|---|---|---|
| `PatternHashToPayload` | anchor `consent_pattern:<hash>` → ConsentPayload | "who has been offered this pattern?" reverse query |
| `PayloadToDecision` | ConsentPayload → ConsentDecision | the decision answers the payload |
| `DeciderToDecision` | anchor `consent_decider:<did>` → ConsentDecision | "what has this agent consented to?" reverse-index |

Link creation happens in the [`consent_coordinator`](../consent_coordinator/) zome; this integrity zome only validates the types.

## Validation invariants (10 covered by unit tests)

Per `consent-payload.spec.md §"Validation rules and current enforcement status"`. All are deterministic, single-entry — no DHT reads from `validate()`.

### ConsentPayload

1. **DIDs required.** `proposer_did` + `recipient_did` non-empty.
2. **Scope non-empty.** `consent_scope` array length ≥ 1.
3. **Hash format.** `pattern_hash` is exactly 64 lowercase hex chars.
4. **Kernel/Constitution → Substrate.** `pattern_type == Kernel | Constitution` forces `blast_radius == Substrate` per ADR-12 §6 (non-overridable once consent given).

### ConsentDecision

5. **Shape valid for accepted outcomes** — `Accept`, `BoundedAccept`, `TouristObserve`, `CounterPropose` pass shape validation.
6. **Non-accepted outcomes require rationale.** `Reject` etc. must provide non-empty `rationale`.
7. **Rejected outcomes grant no scope.** `outcome == Reject` ⇒ `scope_granted` empty.
8. **Non-rejected outcomes grant some scope.** `outcome ∈ {Accept, BoundedAccept, ...}` ⇒ `scope_granted` non-empty.
9. **CounterPropose requires counter_frame_ref.** `outcome == CounterPropose` ⇒ `counter_frame_ref` set.

Plus #10 (top-level dispatch):

10. **`scope_granted ⊆ consent_scope`** — enforced at coordinator (`ensure_scope_subset`) since it requires resolving the linked payload via `must_get_action`. Documented here for completeness.

## Cross-zome dependencies

- **None at integrity layer.** Pure deterministic shape validation.
- **At coordinator layer:** [`consent_coordinator`](../consent_coordinator/) imports `EntryTypes`, `LinkTypes`, all enums, and both structs.

## Tests

`cargo test -p consent_integrity` — 10/10 pass:

| Test | Invariant covered |
|---|---|
| `payload_requires_dids` | #1 |
| `payload_rejects_empty_scope` | #2 |
| `payload_rejects_non_lowercase_sha256_hash` | #3 |
| `kernel_payload_must_be_substrate_class` | #4 |
| `valid_payload_passes_shape_validation` | end-to-end #1–4 |
| `valid_accepted_decision_passes_shape_validation` | #5 |
| `non_accepted_decision_requires_rationale` | #6 |
| `rejected_decision_must_not_grant_scope` | #7 |
| `non_rejected_decision_must_grant_some_scope` | #8 |
| `counter_proposal_requires_counter_frame_ref` | #9 |

## Pending work (documented in ADR-12 truth-status)

- Action-time gating for downstream governed-pattern operations (requires coordinator integration)
- DID ↔ action-header binding
- Cross-frame validation between this zome and the consensus gateway (`packages/metacoordinator_mcp/`)
- Tryorama end-to-end scenarios (blocked on M13 — no compatible tryorama version for hc 0.6.1)
