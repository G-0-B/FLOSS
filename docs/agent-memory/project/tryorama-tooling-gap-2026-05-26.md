---
id: project-tryorama-tooling-gap-2026-05-26
type: project
created: '2026-05-26'
status: active
applies_to:
- any-agent
title: No @holochain/tryorama version pairs with hc 0.6.1 (M13 finding)
---

## What's actually true

Investigated 2026-05-26 in WSL holonix `main-0.6` (hc 0.6.1). No `@holochain/tryorama` version pairs cleanly with the 0.6 conductor line:

- **tryorama 0.17.x** + client 0.18.x → fails with `Failed to run external subcommand: NotFound` because it expects a separate `hc-sandbox` binary (gone in hc 0.6.x monorepo).
- **tryorama 0.18.x** + client 0.19.x → fails with `unrecognized subcommand 'webrtc'` and `'undefined/conductor-config.yaml'`. Expects `hc sandbox network webrtc` (hc 0.6.1 only supports `mem`/`quic`) and `ConfigRootPath(...)` stdout (hc 0.6.1 emits `DataRootPath(...)`).
- **tryorama 0.19.x** + client 0.20.x → fails with `deserialization: Failed to deserialize request` at `AdminWebsocket.installApp`. Sends a request shape conductor 0.6.1 cannot deserialize.

`crates.io` latest `holochain_cli` is `0.7.0-dev.26` as of 2026-05-26 — the 0.6 line is EOL upstream.

## How to apply

**Do NOT claim Tryorama end-to-end verification against hc 0.6.1.** The substrate confidence at the 0.6 line is real but bounded:

| Layer | Verified | Evidence |
|---|---|---|
| Rust validation logic | ✅ | 10/10 `consent_integrity` native tests, 8/8 `rose_forest` vector_ops |
| Wasm compilability | ✅ | 4/4 zomes clean to `wasm32-unknown-unknown` in holonix |
| DNA/hApp packing | ✅ | `hc dna pack` + `hc app pack` succeed with `manifest_version: "0"` + `path:` schema |
| Tryorama end-to-end | ❌ | Blocked on tooling pin — see above |

The ADR-12 truth-status table and the MVP_PLAN Phase 0 note were corrected in commits `f4a70cf` + `5969d09` to reflect this honestly.

## Path forward

Operator chose **option (a) of three** on 2026-05-26: migrate substrate to `holonix main-0.7-dev` so tryorama 0.18+ pairs cleanly. Full plan: [`docs/superpowers/plans/2026-05-26-holochain-0.7-migration.md`](../../superpowers/plans/2026-05-26-holochain-0.7-migration.md) (M14).

Options not chosen (preserved for reference):
- (b) custom test harness on `@holochain/client 0.19.3` (which DOES install against conductor 0.6.1) — bypass tryorama Scenario class.
- (c) wait for upstream tryorama-0.6 backport (no public timeline).
