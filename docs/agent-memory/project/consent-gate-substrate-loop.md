---
id: project-consent-gate-substrate-loop
type: project
created: '2026-05-19'
status: active
applies_to:
- any-agent
source: codex_session
title: ADR-12 consent gate has an implementation-backed substrate slice
---

ADR-12 Consent Gate is no longer only a stub/schema. As of 2026-05-19,
`consent_integrity` defines `ConsentPayload` and `ConsentDecision` entry/link
types, and a separate `consent` coordinator zome exposes create/get/list calls.

The coordinator must stay separate from the existing `rose_forest` coordinator:
linking both integrity crates into one coordinator caused duplicate Holochain
export symbols. The DNA now packages `rose_forest_integrity` + `rose_forest`
and `consent_integrity` + `consent` as separate integrity/coordinator pairs.

Verified locally:

- `python -m pytest scripts\tests\test_consent_gate_wiring.py -q`
- `cargo test -p consent_integrity`
- `cargo check -p consent -p rose_forest --target wasm32-unknown-unknown`
- `cargo build -p rose_forest_integrity -p consent_integrity -p rose_forest -p consent --release --target wasm32-unknown-unknown`
- WSL/Nix shell `hc dna pack dnas/rose_forest/workdir/`
- WSL/Nix shell `hc app pack workdir/`
- WSL/Nix shell `cd tests/tryorama && npx vitest run consent_gate.test.ts`
  (`2/2` passed)

Source-chain provenance: status claim `019e41d3-0672-75a9-a266-f3b4f631aac5`
covered the implementation slice. Follow-up claim
`019e41ef-d1ed-70b1-aeef-0c2fb5048300` records the WSL/Nix hApp packing +
Tryorama pass. Codex did not run voter rounds for either claim, intentionally
conserving tokens after the heartbeat budget correction.

Do not claim full Substrate-class ratification yet. Remaining gates:

- implement action-time governed-pattern enforcement
- harden DID ↔ action-header binding and counter-frame resolvability
- run cross-frame validation with `[auth:trained]` frame representatives
