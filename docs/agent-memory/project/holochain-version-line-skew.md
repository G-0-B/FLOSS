---
id: project-holochain-version-line-skew
type: project
created: '2026-05-19'
status: resolved
resolved_at: '2026-05-19'
resolution_claim: '019e4220-d40c-7c41-b8d6-af8dc9304d58'
applies_to:
- any-agent-doing-rust-hdk-work
- any-agent-evaluating-holochain-skill-adoption
- any-agent-considering-zome-migration
source: claude_session_with_user_verification
title: Substrate WAS holochain-0.4; migrated to holochain-0.6 (2026-05-19) aligned with skill canonical reference
---

## Status: RESOLVED 2026-05-19

User-explicit directive ("def worth it now rather than later we dont have
substantial codebase yert so get to it") drove the migration to landed work in
a single session. System-class consensus claim
`019e4220-d40c-7c41-b8d6-af8dc9304d58` APPROVED mean +0.72 variance 0.024
(cerebras +0.80, gpt-oss-20b +0.85, qwen3-32b +0.50).

Workspace now pins `hdi = "=0.7.1"` + `hdk = "=0.6.1"`, `flake.nix` is on
`holonix?ref=main-0.6`. The active workspace members are
`dnas/rose_forest/zomes/integrity`, `coordinator`, `consent_integrity`, and
`consent_coordinator`; all compile clean. 10/10 consent_integrity unit tests
pass on the new HDI line.

Excluded Holochain folders (`dnas/rose_forest/zomes/hrea_*`, `identity_*`,
`memory_coordinator`, `ontology_integrity`, and `dnas/infinity_bridge`) are
pre-migration dev artifacts. Their stale HDI/HDK pins are not current build
blockers; migrate each excluded zome before adding it back to
`FLOSS/ARF/Cargo.toml` workspace members.

Original gap documented below for historical reference.

---

## The fact (historical — pre-migration)

The FLOSSI0ULLK Holochain substrate ran **holochain-0.4 line** until 2026-05-19:

- `FLOSS/ARF/Cargo.toml` workspace pins: `hdi = "=0.5.1"` / `hdk = "=0.4.1"`
- `FLOSS/ARF/flake.lock` pins: holonix `main-0.4`, holochain `0.4.4`
- All 8 existing zomes (rose_forest_integrity, rose_forest coordinator, hrea_*, identity_*, memory_coordinator, ontology_integrity) + the new `consent_integrity` + `consent` coordinator are on this line.

The `holochain-agent-skill` (Soushi888 upstream, registered in Claude Code skills, reuse-ledger entry 0013) canonical reference is the **holochain-0.6 line**:

- Quick Reference: `hdk = "=0.6.1"` / `hdi = "=0.7.1"` / holonix `main-0.6`
- Patterns.md teaches: `delete_link(hash, GetOptions::default())`, `LinkQuery::try_new()`, `op.flattened::<EntryTypes, LinkTypes>()`, `GetStrategy::Local`/`Network` split
- Pitfalls Checklist assumes the 0.6 API surface

The substrate is **two minor versions behind** what the skill teaches.

## Why this matters

The skill's `Common Pitfalls Checklist` is calibrated to 0.6 conventions. When applied to 0.4 code, three things happen:

1. **False-positive findings**: skill flags absence of `op.flattened` dispatch as a pattern violation when the actual 0.4 API is `op.to_type()` and the code is correct for its line.
2. **True-positive findings get under-credited**: the version-line skew itself shows up as a finding, but treating it as "fix this code" rather than "decide whether to migrate the substrate" misframes the cost.
3. **Adapter_test status ambiguous**: ledger entry 0013 currently sits at `adopt` based on `consent_integrity` compile-clean evidence. The skill *did* shape the code (no action-header-as-entry-field, `#[serde(default)]` discipline, deterministic validate, link-type enum structure), but those patterns are version-line-agnostic. Version-line-specific guidance (the API renames) didn't apply.

## What is NOT happening (historical — superseded 2026-05-19)

~~A migration to holochain-0.6 is **not in flight**.~~ **Superseded**: migration
executed and landed via consensus claim `019e4220-d40c-7c41-b8d6-af8dc9304d58`.

This section is preserved for historical context. Future agents reading this
memory should rely on the **Status: RESOLVED** header at the top, not the
historical text below.

## What COULD happen later

A substrate-line decision Claim at **System** or **Substrate** blast radius asking the voter pool:

- Whether the 8-zome rewrite cost is worth the move to 0.6
- Whether 0.4 is acceptable indefinitely given holonix `main-0.4` is still in active maintenance
- Whether to migrate `consent_*` first as a smaller-scope proof, leaving older zomes on 0.4

That Claim has not been submitted. Decision-pending surface, not decided work.

## Where this gets surfaced

- **Canonical**: `FLOSS/docs/specs/consent-payload.spec.md` validation-status table, row "Holochain runtime version line" — reads every time anyone opens that spec.
- **Working-todo**: `FLOSS/docs/research/2026-05-15-working-todo-list.md` §I 2026-05-19 entry "Holochain runtime version-line skew tracked durably".
- **Reuse-ledger entry 0013** evidence: skill is adopted, but on the 0.4 line — the gap is not a deadlock.

## Provenance

- User verification: 2026-05-19 in-session, after Codex's WSL pack/Tryorama run. User explicit: "codex did stuff, they dont have the holochain skill and did stuff to tyhe rose forest code goot it compiling in wsl using hc and stuff buut pretty sure it used an old version of hdi n stuff still"
- Substrate state verified via Bash inspection of Cargo.toml + flake.lock + per-zome Cargo.toml at 2026-05-19 ~21:00 UTC.
- Two related consensus claims for the consent-gate substrate slice (both APPROVED Module-class mean +0.60): `019e41d3-0672-75a9-a266-f3b4f631aac5` (implementation slice) + `019e41ef-d1ed-70b1-aeef-0c2fb5048300` (WSL Tryorama pass). Neither claim covers the version-line decision — that is deliberately separate.

## Standing instruction for future agents (POST-MIGRATION)

If you are doing Rust HDK work in this workspace as of 2026-05-19 or later:

1. **Default**: write code for the 0.6 line. Match the current workspace pins (`hdi = "=0.7.1"` / `hdk = "=0.6.1"`).
2. **Apply skill patterns directly**: the `holochain-agent-skill` Patterns.md and Pitfalls Checklist now align 1:1 with workspace versions. No translation layer needed.
3. **0.6-specific API to use**: `LinkQuery::try_new(base, link_type)?` (not `GetLinksInputBuilder::try_new(...).build()`), `get_links(query, GetStrategy::default())`, `agent_info()?.agent_initial_pubkey` (not `agent_latest_pubkey`), `delete_link(hash, GetOptions::default())`, `op.flattened::<EntryTypes, LinkTypes>()` (already in place).
4. **wasm32-unknown-unknown target**: the workspace `.cargo/config.toml` sets `--cfg getrandom_backend="wasm_js"`. Each zome that targets wasm32 also pins `getrandom = { version = "0.3", features = ["wasm_js"] }` under `[target.'cfg(target_arch = "wasm32")'.dependencies]`. New zomes need to follow this pattern.
5. **`#[hdk_entry_helper]` macro lookup**: HDI 0.7 requires `holochain_serialized_bytes` to be a direct dep, not just transitive. Integrity zomes add `holochain_serialized_bytes = { workspace = true }`.
6. **Orphan zomes** (hrea_*, identity_*, memory_coordinator, ontology_integrity, and infinity_bridge) are NOT migrated and remain excluded pre-migration dev artifacts, not workspace members. If you bring one back into active substrate, migrate it first before adding it to `FLOSS/ARF/Cargo.toml`.
