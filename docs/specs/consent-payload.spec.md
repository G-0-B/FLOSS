# Consent Payload Spec

**ADR:** ADR-12 Consent Gate Protocol
**Schema:** `consent-payload.schema.json` (this directory)
**Status:** ⚠️ Partially verified — schema, Holochain entry types, consent coordinator, DNA wiring, Rust unit tests, static wiring tests, release WASMs, hApp packing, and consent Tryorama scenarios passed 2026-05-19
**Truth status:** ⚠️ Specified with verified implementation slices — deterministic entry-shape rules, coordinator scope-subset enforcement, and create/retrieve/refusal hApp behavior are verified locally; full Substrate-class action enforcement is still pending
**Blast radius:** Substrate (invariants below cannot be overridden once accepted)

---

## What this spec does

Defines two Holochain entry types — `ConsentPayload` and `ConsentDecision` — that implement the Consent Gate Protocol from ADR-12. Together they let any agent in the FLOSSI0ULLK network refuse, bound, observe-as-tourist, or counter-propose against any memetic pattern offered to them, with refusal preserved on chain as durable provenance.

Target Substrate-layer enforcement: no entry with `pattern_type ∈ {kernel, adr, constitution}` and `blast_radius ∈ {System, Substrate}` may be acted upon by an agent without a corresponding `ConsentDecision` in that agent's source chain with `outcome ≠ rejected` and `scope_granted` matching the action.

Current implementation slice: `consent_integrity` defines the Holochain entry/link types and deterministic validation rules; the separate `consent` coordinator creates/retrieves entries, links payloads to decisions, and enforces `scope_granted ⊆ consent_scope` on the decision-create path. The action-time gate is still a follow-up integration, so do not treat this as full Substrate-class ratification yet.

LLMs operating as `[auth:structural]` agents per CFIS v0.3 cannot bypass the rules that have reached WASM validation. Rules that require downstream action context are still specified rather than fully enforced.

---

## Why two entry types, not one

A single combined `Consent` entry would mix proposer state with decider state. Separating them gives:

1. **Append-only correctness** — both writers are different agents; both signatures must be verifiable independently
2. **Multiple decisions per request** — for collective DIDs (steward vote, constitutional ratification), N decisions reference one payload
3. **Refusal preservation** — if a request is rejected by one agent and accepted by another, the divergence is on-chain provenance for CFIS Tier-4 analysis
4. **Time-bounded consent** — `expires_at` lives on the decision, not the payload; an agent can re-consent without the proposer re-asking

---

## The four refusal modes (load-bearing)

Per ADR-12 §4:

| Mode | Use case | Substrate effect |
|---|---|---|
| `reject` | Pattern is incompatible / unwanted | Pattern logged; not loaded; no future `bind` is valid |
| `bounded_accept` | Pattern useful but scope-narrowed | Subset of `consent_scope` granted; integrity zome enforces the bound |
| `tourist_observe` | CFIS `[auth:tourist]` — read without claiming authority | `read_only` granted; `integrate`/`propagate`/`bind` blocked at zome level |
| `counter_propose` | Acknowledge input + attach counter-frame | Original logged + counter routed through consensus gateway as new Claim. CFIS Tier-4 becomes a substrate operation, not just data |

`counter_propose` is the most-architecturally-interesting mode: it converts what would be an unresolved disagreement into a structured deliberation. Two agents with `counter_propose` chains against each other have produced a Tier-4 divergence on the source chain that CFIS LSM-Override can adjudicate at frame level.

---

## What the schema does NOT do

- Does NOT specify how patterns get *offered* (proposer-side discovery mechanism) — that's an MCP or gateway-tool concern
- Does NOT specify how recipients are notified — push notification, polling, gateway subscription are all viable
- Does NOT define cross-substrate consent translation (Holochain ↔ Radicle ↔ AD4M) — open question #5 in ADR-12 §7
- Does NOT define revocation forward-propagation semantics — open question #4 in ADR-12 §7
- Does NOT mandate Substrate-class blast radius for `kernel`/`constitution` — defaults named in schema, override possible via explicit governance ADR (likely ADR-13 Steward Vote)

---

## Validation rules and current enforcement status

| # | Rule | Current status |
|---|---|---|
| 1 | `payload_id` / `decision_id` are UUID v7, time-sortable, unique on chain | ⚠️ Specified; schema constrains shape, uniqueness not yet enforced in WASM |
| 2 | `pattern_hash` matches SHA-256 of the actual payload content the agent is asked to consent to | ⚠️ Partially verified; integrity zome enforces 64-char lowercase hex, content-hash recomputation still pending |
| 3 | `recipient_did` / `decider_did` match the agent whose chain receives the entry | ⚠️ Specified; non-empty DID fields enforced, DID ↔ action-header binding pending |
| 4 | `ConsentDecision.payload_action_hash` references an existing `ConsentPayload` | ✅ Verified in coordinator create path via `get_consent_payload`; still needs integrity-level `must_get_action` hardening |
| 5 | `ConsentDecision.scope_granted` is a subset of `ConsentPayload.consent_scope` | ✅ Verified in coordinator create path; integrity zome enforces only contradiction-free local shape |
| 6 | `ConsentDecision.outcome=rejected` ⟹ `scope_granted=[]` | ✅ Verified in integrity zome + Rust unit tests |
| 7 | `ConsentDecision.outcome=counter_propose` ⟹ `counter_frame_ref` non-null + resolvable as a Claim on chain | ⚠️ Partially verified; non-null enforced, chain resolvability pending |
| 8 | `ConsentDecision.outcome != accepted` ⟹ `rationale` non-empty | ✅ Verified in integrity zome + Rust unit tests |
| 9 | `pattern_type ∈ {kernel, constitution}` with `blast_radius < Substrate` is rejected | ✅ Verified in integrity zome + Rust unit tests |
| 10 | Subsequent action on the pattern with a stronger scope than `scope_granted` is rejected regardless of initiating app | ⏸ Pending; requires downstream governed-pattern action integration |

---

## Cross-references

- **ADR-12 Consent Gate Protocol:** `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md` (full motivation + cross-ADR implications + open questions)
- **CFIS v0.3 4-tier authority + LSM-Override:** `FLOSS/docs/architecture/CFIS_v0.3.md` (the `tourist_observe` mode operationalizes the `[auth:tourist]` tier)
- **Resonance kernel P1-P5:** `resonance_mechanism_v2.md` §P3 (selective coupling function is the substrate-physics analog of consent)
- **Positive Alignment paper §"Paternalism Problem":** `FLOSS/docs/research/2026-05-18-positive-alignment-flossi0ullk-map.md` §4.2 (citation anchor for the consented-guidance-vs-technocratic-imposition distinction)
- **ADR-10 Consensus Gateway:** `FLOSS/docs/adr/ADR-MCP-ORCHESTRATOR.md` (gateway routes ConsentPayloads same as Claims; both are append-only entry types)
- **Companion ADR-13 Steward Vote:** named-but-undrafted; structurally a special case of ADR-12 with collective `decider_did`

---

## Validation status

| Gate | Status |
|---|---|
| JSON Schema landed | ✅ 2026-05-19 |
| Spec doc landed | ✅ 2026-05-19 (this file) |
| ADR-12 stub Module-class consensus | ✅ APPROVED 2026-05-19, claim `019e3f85-25fd-700c-9b25-4cbfede6aed3` mean +0.52 |
| Holochain entry-type implementation in `ARF/dnas/rose_forest/` | ✅ `consent_integrity` landed + unit-tested |
| Coordinator zome call surface | ✅ `consent` landed with create/get/list functions + scope-subset enforcement |
| DNA wiring | ✅ `workdir/dna.yaml` includes `consent_integrity` + separate `consent` coordinator |
| Release WASM build | ✅ `cargo build -p rose_forest_integrity -p consent_integrity -p rose_forest -p consent --release --target wasm32-unknown-unknown` passed on **holochain-0.6 line** 2026-05-19 17:22 UTC-4 (previous 0.4-line build also passed) |
| hApp packaging | ⚠️ Was ✅ on holochain-0.4 line (Codex WSL run 2026-05-19 16:22). Invalidated by the 0.4→0.6 migration; stale bundles removed. Re-pack in WSL on the new `main-0.6` nix shell required. |
| Tryorama scenario coverage | ⚠️ Was ✅ on holochain-0.4 line (`npx vitest run consent_gate.test.ts` 2/2). Invalidated by the 0.4→0.6 migration; `@holochain/client` and `@holochain/tryorama` bumped in `package.json` (^0.20.0 / ^0.19.0). Re-run in WSL after re-pack. |
| Holochain runtime version line | ✅ Migrated 2026-05-19 from holochain-0.4 (HDI 0.5.1 / HDK 0.4.1) to holochain-0.6 line: workspace pins now `hdi = "=0.7.1"` + `hdk = "=0.6.1"`, `flake.nix` `holonix?ref=main-0.6`, `ARF/.cargo/config.toml` enables `getrandom_backend="wasm_js"` for wasm32. All 4 active zomes compile clean (`cargo check -p rose_forest_integrity -p consent_integrity -p rose_forest -p consent --target wasm32-unknown-unknown` passed). All 10 `consent_integrity` unit tests pass on HDI 0.7.1. Release WASMs built. API migrations applied: `agent_latest_pubkey → agent_initial_pubkey` (5 sites), `GetLinksInputBuilder::try_new(...).build() → LinkQuery::try_new(...)?` (4 sites), `get_links(_) → get_links(_, GetStrategy::default())` (4 sites). Added direct `holochain_serialized_bytes = "=0.0.57"` dep to integrity zomes (HDI 0.7 macro requires crate to be resolvable directly, not just transitively). Old `rose_forest.dna` and `rose_forest.happ` removed — must be re-packed in WSL on the 0.6 nix shell. Aligns workspace with `holochain-agent-skill` canonical reference. |
| Cross-frame validation via `[auth:trained]` frame reps | ⏸ Pending (CFIS Phase 0 §T5) |
| Substrate-class consensus ratification (0.85 threshold) | ⏸ Blocked on action-time gate, DID/header hardening, and cross-frame validation |
| Voter onboarding integration | ⏸ Pending |
