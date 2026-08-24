# Rust Sweettest Substrate Bridge Design

**Date:** 2026-08-23
**Status:** Approved for implementation
**Truth status:** Specified until the tests execute successfully

## Purpose

Replace the unusable Tryorama execution path for the Phase 0 substrate bridge with Rust-native Sweettest coverage on the pinned Holochain 0.6.1 line. The tests must exercise a freshly built and packed Rose Forest DNA containing exactly the four active zomes, while keeping the KnowledgeTriple and consent domains independently diagnosable.

This work validates observed local two-node DHT behavior. It does not prove WAN resilience, network-partition recovery, production deployment behavior, or global truth.

## Scope

The implementation adds one native Rust test package under `ARF/tests/sweettest/` with two independent integration-test binaries:

- `substrate_bridge_test.rs` exercises the six criteria from `docs/specs/phase0-substrate-bridge.spec.md` through the `rose_forest` coordinator and `rose_forest_integrity` validation layer.
- `consent_zome_test.rs` separately exercises consent payloads and decisions through the `consent` coordinator and `consent_integrity` validation layer.

Both binaries load the same freshly packed DNA artifact, but each creates its own conductors, agents, cells, and DHT state. Shared code is limited to typed wire representations and deterministic fixture construction.

No coordinator or integrity-zome logic changes are in scope. No ADR changes, canonical promotion, harvest-log claim, or consensus-gateway changes are in scope.

## Architecture

`ARF/tests/sweettest` is a workspace member and native-only test package. Its Cargo manifest pins `holochain = "=0.6.1"` with `test_utils`, uses Tokio's multi-thread runtime, and depends on the existing zome crates only for serializable public types where that does not introduce duplicate export symbols.

Each test binary performs the following setup:

1. Load `dnas/rose_forest/workdir/rose_forest.dna`, produced immediately before the test command from current release WASM artifacts.
2. Start two `SweetConductor` instances with the standard Holochain 0.6.1 test configuration.
3. Install one app per conductor. `SweetConductorBatch::setup_app` creates a distinct agent key for each conductor.
4. Assert the two agent pubkeys differ before testing authorization or provenance.
5. Exchange peer information explicitly.
6. Call the relevant coordinator zome.
7. Use `await_consistency` before every cross-agent read. In Holochain 0.6.1 this waits until every op published by each tested cell is integrated by every tested node.

The build-and-run sequence is explicit rather than hidden inside test code:

```text
cargo build --workspace --exclude rose_forest_sweettest --release --target wasm32-unknown-unknown
hc dna pack dnas/rose_forest/workdir/
cargo test -p rose_forest_sweettest --test substrate_bridge_test
cargo test -p rose_forest_sweettest --test consent_zome_test
```

The native Sweettest package is excluded from the WASM build because it depends on the conductor runtime and is not a zome. Inside a Windows-created Git worktree, WSL invokes the flake as `nix develop path:.` so Nix does not try to resolve the worktree's Windows-form Git metadata path.

## Substrate Bridge Test

The substrate binary implements six named tests with isolated fixtures:

1. **Publish:** Alice calls `assert_triple` and receives an `ActionHash` that resolves to the authored triple.
2. **Provenance:** Alice calls `get_triple_record`; the returned record contains a signature, Alice's author key, a recent action timestamp, and matching entry content.
3. **Verify:** after DHT consistency, Bob retrieves Alice's record by hash and observes identical content, action hash, author, timestamp, and signature.
4. **Query:** without receiving the hash, Bob discovers Alice's triple by subject and predicate; results contain the expected hash plus lightweight author and creation-time provenance.
5. **Fork-visible:** Alice and Bob publish different objects for the same subject and predicate; after consistency, both distinct action hashes and both author identities remain query-visible. Here "fork" means preserved conflicting knowledge claims, not a simulated network partition.
6. **No privilege:** both distinct agents use the same public coordinator functions, can publish, query, and retrieve each other's records, and observe the same result set. The test makes no claim about ordering or authority beyond equal call access and visibility.

A negative verification case also checks that `get_triple_record` returns `None` for a validly shaped but nonexistent action hash.

Assertions compare full result sets by stable identity rather than relying on DHT return order. Timestamps are checked against a bounded test-start/test-end interval instead of exact equality with wall-clock time. Floating-point confidence comparisons use an explicit tolerance.

## Consent Zome Test

The consent binary independently covers both active consent zomes:

- Alice creates a valid `ConsentPayload`, retrieves it, and verifies its stored fields.
- After consistency, Bob retrieves Alice's payload.
- Bob creates a valid `Accepted` decision granting the complete requested scope.
- After consistency, Alice retrieves Bob's decision and discovers it through `get_consent_decisions_for_payload`.
- An invalid decision is rejected with the specific `E_SCOPE_NOT_REQUESTED` contract and produces no discoverable decision record or link.
- Agent keys are asserted distinct so cross-agent visibility cannot collapse into same-agent behavior.

The negative path uses `call_fallible` and checks the domain error code, not merely the presence of any error.

## Fresh-Bundle Gate

The DNA manifest already names exactly these zomes:

- `rose_forest_integrity`
- `consent_integrity`
- `rose_forest`
- `consent`

Tests load the packed DNA created after the release WASM build. Acceptance output records the four compiled WASM filenames, successful `hc dna pack`, and the exact test commands. A committed historical `.dna` file alone is not acceptable evidence.

## Failure Handling

- Setup failure names the missing artifact or failed conductor step.
- DHT convergence uses Sweettest's condition-based `await_consistency`; tests add no arbitrary sleeps.
- Cross-agent assertions run only after explicit peer exchange and convergence.
- Invalid zome calls preserve and inspect the returned error text for the expected stable domain code.
- Every test receives fresh conductor state, preventing one criterion from satisfying another through leftover records.

## Auditor Reconciliation

An external ensemble supplied five non-empty audits across GPT, Qwen, DeepSeek, and Mistral model families; one Llama-family voter returned no content. Adopted concerns were clean-worktree execution, distinct-agent assertions, exact negative-path errors, independent test binaries, fresh bundle evidence, and explicit proof limits.

Two unanimous-looking synthesis claims were rejected against the Holochain 0.6.1 source and the governing spec:

- `await_consistency` does not merely wait for one gossip round; it compares tested DHT databases until published ops are integrated everywhere.
- the specified fork-visible criterion is concurrent conflicting-entry preservation, not network-partition simulation.

Ensemble output remains advisory and noncanonical.

## Acceptance Gates

Implementation is complete only when all gates pass from the isolated worktree:

1. Existing four-zome workspace unit tests pass unchanged.
2. All four active zomes compile for `wasm32-unknown-unknown` in release mode.
3. `hc dna pack` succeeds using those four current WASM files.
4. Six substrate criteria plus the missing-hash negative case pass against two distinct agents.
5. Separate consent tests pass, including cross-agent payload/decision visibility and exact invalid-decision rejection.
6. A second complete run passes without arbitrary sleeps or reuse of conductor state.
7. `cargo fmt --check` passes for the Rust workspace.
8. Git diff contains no zome logic, ADR, canonical-status, consensus-gateway, or unrelated user-file changes.

Passing these gates supports only this claim: the freshly built four-zome Rose Forest DNA demonstrated the specified KnowledgeTriple and consent behaviors across two local Sweettest conductors on Holochain 0.6.1.
