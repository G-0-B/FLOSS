# Rust Sweettest Substrate Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the six substrate-bridge criteria and separate consent-zome behavior against a freshly built four-zome Rose Forest DNA using Rust Sweettest and two distinct agents.

**Architecture:** Add one standalone native-only Rust child workspace at `ARF/tests/sweettest`. Two integration-test binaries share typed wire representations and a two-conductor fixture but create independent conductor state; production zomes remain unchanged.

**Tech Stack:** Rust 2021, Holochain/Sweettest from the official immutable Git pin resolving to the 0.6.1 line, parent HDK `=0.6.1`, Tokio multi-thread runtime, Serde, Holonix `main-0.6`.

**As-executed deviation:** the approved member-workspace sketch was replaced by a standalone child workspace at `ARF/tests/sweettest` so native conductor dependencies cannot enter the parent guest/WASM workspace. The child manifest pins the official Holochain Git request revision `b1d40b24ab19d81f7563b0cf66b933a138f556a0`; its committed child lock resolves the immutable source commit `3bdeaccd1c54fa351e76f7347601dfbc061d5bd4`. Use the locked serial `run.sh` interface below, not parent `cargo test -p` commands.

## Global Constraints

- Do not modify `ARF/dnas/rose_forest/zomes/integrity/` or `consent_integrity/`; those are governed Layer 0 surfaces.
- Do not modify coordinator-zome behavior, ADRs, canonical status, consensus-gateway logic, or unrelated user files.
- Load only a freshly packed `ARF/dnas/rose_forest/workdir/rose_forest.dna` built from all four current release WASM files.
- Use two distinct agent keys and assert they differ before provenance or privilege checks.
- Call `exchange_peer_info` and `await_consistency` before every cross-agent read.
- Add no arbitrary sleep; use Holochain's condition-based convergence helper.
- Treat test output as evidence only for local two-conductor Holochain 0.6.1 behavior.
- From this Windows-created worktree, enter Holonix with `nix develop path:.` from `ARF/`.
- Run the native child through `./tests/sweettest/run.sh`; it defaults `RUST_TEST_THREADS=1` for serial conductor isolation. Set `RUST_TEST_THREADS=N` only as an explicit operator override.

## File Structure

- Create `ARF/tests/sweettest/Cargo.toml`: standalone native child-workspace boundary, pinned to official Holochain Git revision `b1d40b24ab19d81f7563b0cf66b933a138f556a0`.
- Create `ARF/tests/sweettest/Cargo.lock`: child-only native Sweettest resolution (the lock resolves the requested Git revision to immutable source commit `3bdeaccd1c54fa351e76f7347601dfbc061d5bd4`).
- Create `ARF/tests/sweettest/run.sh`: locked parent WASM build, fresh pack, and locked serial child-test runner.
- Create `ARF/tests/sweettest/src/lib.rs`: shared bundle path, two-agent fixture, wire mirrors, and test-only helpers.
- Create `ARF/tests/sweettest/tests/substrate_bridge_test.rs`: six criteria plus missing-hash negative verification.
- Create `ARF/tests/sweettest/tests/consent_zome_test.rs`: independent consent happy path, cross-agent visibility, and exact rejection/no-side-effect test.

ReviewZome result: no zome source file changes are planned. Sweettest requirements are satisfied by `#[tokio::test(flavor = "multi_thread")]`, `holochain` with the `sweettest` feature, peer exchange, and `await_consistency` before cross-agent reads. No ReviewZome blocker applies.

---

### Task 1: Native Sweettest Package and Two-Agent Fixture

**Files:**
- Create: `ARF/tests/sweettest/Cargo.toml`
- Create: `ARF/tests/sweettest/Cargo.lock`
- Create: `ARF/tests/sweettest/run.sh`
- Create: `ARF/tests/sweettest/src/lib.rs`
- Create: `ARF/tests/sweettest/tests/substrate_bridge_test.rs`

**Interfaces:**
- Produces: `pub async fn setup_two_agent_app() -> TestApp`
- Produces: `pub struct TestApp { pub conductors: SweetConductorBatch, pub alice: SweetCell, pub bob: SweetCell }`
- Produces: `pub fn rose_zome(cell: &SweetCell) -> SweetZome`
- Produces: `pub fn consent_zome(cell: &SweetCell) -> SweetZome`
- Produces: `AssertTripleInput` and `KnowledgeTriple` Serde wire mirrors.

- [ ] **Step 1: Write the first failing integration test**

Create `ARF/tests/sweettest/tests/substrate_bridge_test.rs` with the first observable criterion:

```rust
use holochain::prelude::{ActionHash, Record};
use rose_forest_sweettest::{rose_zome, setup_two_agent_app, AssertTripleInput, KnowledgeTriple};

#[tokio::test(flavor = "multi_thread")]
async fn criterion_1_publish_returns_resolvable_action_hash() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new(
                "holochain",
                "is_a",
                "distributed_framework",
                0.95,
            ),
        )
        .await;
    let record: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", hash.clone())
        .await;
    let record = record.expect("published triple must resolve by returned action hash");
    let triple = record
        .entry()
        .to_app_option::<KnowledgeTriple>()
        .expect("published entry must decode")
        .expect("published entry must be present");

    assert_eq!(record.action_address(), &hash);
    assert_eq!(triple.subject, "holochain");
    assert_eq!(triple.predicate, "is_a");
    assert_eq!(triple.object, "distributed_framework");
    assert!((triple.confidence - 0.95).abs() < f32::EPSILON);
}
```

- [ ] **Step 2: Run the target and verify RED**

Run from `ARF/`:

```bash
nix develop path:. --command ./tests/sweettest/run.sh --test substrate_bridge_test criterion_1_publish_returns_resolvable_action_hash -- --exact
```

Expected: FAIL because the child manifest and harness are not yet present. This proves the new native harness is absent.

- [ ] **Step 3: Add the standalone native child workspace**

Create `ARF/tests/sweettest/Cargo.toml` with its own `[workspace]` boundary and child `Cargo.lock`:

```toml
[package]
name = "rose_forest_sweettest"
version = "0.1.0"
edition = "2021"
publish = false

[dependencies]
holochain = { git = "https://github.com/holochain/holochain", rev = "b1d40b24ab19d81f7563b0cf66b933a138f556a0", features = ["sweettest"] }
serde = { version = "1", features = ["derive"] }
tokio = { version = "1", features = ["macros", "rt-multi-thread"] }
```

- [ ] **Step 4: Implement the minimal shared fixture and wire mirrors**

Create `ARF/tests/sweettest/src/lib.rs` with:

```rust
use holochain::prelude::{AgentPubKey, DnaFile, Timestamp};
use holochain::sweettest::{SweetCell, SweetConductorBatch, SweetDnaFile, SweetZome};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

pub const ROSE_ZOME: &str = "rose_forest";
pub const CONSENT_ZOME: &str = "consent";

pub struct TestApp {
    pub conductors: SweetConductorBatch,
    pub alice: SweetCell,
    pub bob: SweetCell,
}

pub async fn setup_two_agent_app() -> TestApp {
    let bundle_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../dnas/rose_forest/workdir/rose_forest.dna");
    assert!(bundle_path.is_file(), "fresh DNA bundle missing: {}", bundle_path.display());
    let dna: DnaFile = SweetDnaFile::from_bundle(&bundle_path)
        .await
        .expect("fresh four-zome DNA bundle must load");
    let mut conductors = SweetConductorBatch::from_standard_config_rendezvous(2).await;
    let apps = conductors
        .setup_app("rose-forest-sweettest", &[dna])
        .await
        .expect("four-zome DNA must install on both conductors");
    let ((alice,), (bob,)) = apps.into_tuples();
    assert_ne!(alice.agent_pubkey(), bob.agent_pubkey(), "agents must be distinct");
    conductors.exchange_peer_info().await;
    TestApp { conductors, alice, bob }
}

pub fn rose_zome(cell: &SweetCell) -> SweetZome {
    cell.zome(ROSE_ZOME)
}

pub fn consent_zome(cell: &SweetCell) -> SweetZome {
    cell.zome(CONSENT_ZOME)
}

#[derive(Clone, Debug, Serialize)]
pub struct AssertTripleInput {
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
}

impl AssertTripleInput {
    pub fn new(subject: &str, predicate: &str, object: &str, confidence: f32) -> Self {
        Self {
            subject: subject.into(),
            predicate: predicate.into(),
            object: object.into(),
            confidence,
        }
    }
}

#[derive(Clone, Debug, Deserialize, PartialEq)]
pub struct KnowledgeTriple {
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub source: AgentPubKey,
    pub created_at: Timestamp,
}
```

- [ ] **Step 5: Build and pack all four current zomes**

Run:

```bash
nix develop path:. --command cargo build --workspace --locked --release --target wasm32-unknown-unknown
nix develop path:. --command hc dna pack dnas/rose_forest/workdir/
```

Expected: four release WASM files compile and `rose_forest.dna` packs successfully.

- [ ] **Step 6: Run the first test and verify GREEN**

Run the Step 2 command again. Expected: one test passes against a real conductor and freshly packed DNA.

- [ ] **Step 7: Commit the harness slice**

```bash
git add ARF/tests/sweettest
git commit -m "test: add native four-zome Sweettest harness"
```

---

### Task 2: Port the Six Substrate Criteria

**Files:**
- Modify: `ARF/tests/sweettest/src/lib.rs`
- Modify: `ARF/tests/sweettest/tests/substrate_bridge_test.rs`

**Interfaces:**
- Consumes: `setup_two_agent_app`, `rose_zome`, `AssertTripleInput`, `KnowledgeTriple`.
- Produces: `QueryTriplesInput`, `TripleResult`, `query_by_subject`, `query_by_predicate`, `decode_triple`, `await_two_agent_consistency`, and `mutated_missing_hash` test helpers.

- [ ] **Step 1: Add all missing criteria before adding their support types**

Add six tests named exactly:

```text
criterion_2_provenance_returns_author_timestamp_and_signature
criterion_3_bob_verifies_alices_content_and_provenance
criterion_3b_missing_hash_returns_none
criterion_4_bob_discovers_by_subject_and_predicate_without_hash
criterion_5_conflicting_triples_remain_fork_visible
criterion_6_distinct_agents_have_equal_publish_query_and_verify_access
```

Each test creates a fresh `TestApp`. Criterion 2 bounds `record.action().timestamp()` between timestamps captured before and after the zome call, asserts `record.action().author() == alice.agent_pubkey()`, asserts `record.signed_action().signature.0.len() == 64`, and decodes exact entry content. Criterion 3 calls `await_consistency` before Bob's read and compares Bob's record action hash, action author, action timestamp, signature, and decoded content to Alice's record. Criterion 3b XOR-mutates bytes `3..35` of a real hash via `ActionHash::from_raw_39` and expects `None` for the mutation while the real hash still resolves.

Criterion 4 discards the create return from its assertion, converges, queries Bob first by subject and then by predicate, and finds the expected `TripleResult` by `(subject, predicate, object)` rather than position. Criterion 5 has Alice and Bob publish different objects for identical subject and predicate, converges, requires two distinct hashes, and compares an object-to-author map containing both claims. Criterion 6 has both agents publish with identical `related_to` calls, converges, compares result sets as `BTreeSet<ActionHash>`, and retrieves each record from the opposite conductor.

- [ ] **Step 2: Run the complete target and verify RED**

Run:

```bash
nix develop path:. --command ./tests/sweettest/run.sh --test substrate_bridge_test
```

Expected: compile failure for missing query/result/helper interfaces named above. The failure must be interface absence, not a syntax error.

- [ ] **Step 3: Add minimal wire types and helpers**

Implement these exact public wire shapes in `src/lib.rs`:

```rust
#[derive(Clone, Debug, Serialize)]
pub struct QueryTriplesInput {
    pub subject: Option<String>,
    pub predicate: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
pub struct TripleResult {
    pub hash: ActionHash,
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub author: AgentPubKey,
    pub created_at: Timestamp,
}

pub async fn await_two_agent_consistency(app: &TestApp) {
    await_consistency([&app.alice, &app.bob])
        .await
        .expect("both DHT databases must integrate every published op");
}

pub fn mutated_missing_hash(real: &ActionHash) -> ActionHash {
    let mut bytes = real.get_raw_39().to_vec();
    for byte in &mut bytes[3..35] {
        *byte ^= 0xa5;
    }
    ActionHash::from_raw_39(bytes)
}
```

Add `subject` and `predicate` constructors for `QueryTriplesInput`. Keep query assertions in the integration test so shared helpers cannot reproduce the production query logic.

- [ ] **Step 4: Run substrate tests and resolve only observed harness/API defects**

Run the Step 2 command until all seven tests pass. If a zome behavior fails, stop and report it; do not modify governed zome logic under this plan.

- [ ] **Step 5: Mutation-check the assertions**

Confirm mentally and through narrow temporary edits that tests fail for wrong author, wrong hash, missing conflicting result, missing signature comparison, and same-agent setup. Revert temporary mutations before commit.

- [ ] **Step 6: Commit the substrate criteria**

```bash
git add ARF/tests/sweettest/src/lib.rs ARF/tests/sweettest/tests/substrate_bridge_test.rs
git commit -m "test: port six substrate criteria to Sweettest"
```

---

### Task 3: Add Separate Consent-Zome Sweettests

**Files:**
- Modify: `ARF/tests/sweettest/src/lib.rs`
- Create: `ARF/tests/sweettest/tests/consent_zome_test.rs`

**Interfaces:**
- Consumes: `setup_two_agent_app`, `consent_zome`, `await_two_agent_consistency`.
- Produces: Serde mirrors for `PatternType`, `BlastRadius`, `ConsentScope`, `RefusalMode`, `Outcome`, `CreateConsentPayloadInput`, `ConsentPayload`, `CreateConsentDecisionInput`, and `ConsentDecision`.

- [ ] **Step 1: Write failing consent integration tests**

Create two `#[tokio::test(flavor = "multi_thread")]` tests:

```text
consent_payload_and_accepted_decision_are_cross_agent_visible
consent_rejects_unrequested_scope_without_creating_a_decision
```

The happy-path test performs this exact sequence: Alice creates a System/Adr payload requesting `[ReadOnly, Integrate]`; Alice reads it back; both cells converge; Bob reads it; Bob creates an `Accepted` decision granting both requested scopes; both cells converge; Alice retrieves the decision; Alice lists decisions for the payload and finds Bob's action hash and exact decision fields.

The negative test creates a payload requesting only `[ReadOnly]`, converges, then calls `create_consent_decision` through `call_fallible::<_, ActionHash>` with `[ReadOnly, Bind]`. It asserts the rendered error contains `E_SCOPE_NOT_REQUESTED`, converges again, and asserts `get_consent_decisions_for_payload` returns an empty vector.

- [ ] **Step 2: Run consent target and verify RED**

Run:

```bash
nix develop path:. --command ./tests/sweettest/run.sh --test consent_zome_test
```

Expected: compile failure because the consent wire mirrors do not yet exist.

- [ ] **Step 3: Implement exact consent wire mirrors**

Mirror every coordinator input and integrity output field in source order with default Serde enum variant names. Use `Option<Vec<RefusalMode>>` for payload input, `Option<Timestamp>` for submitted/decided times, and `Option<ActionHash>` for parent/counter references. Derive `Clone`, `Debug`, `Serialize` on inputs and `Clone`, `Debug`, `Deserialize`, `PartialEq`, `Eq` where field types permit on outputs/enums.

Use fixed payload and decision IDs, lowercase 64-character SHA-256 strings, distinct proposer/recipient/decider DIDs, and literal scope vectors. Do not import either integrity crate into the native test binary; the local mirrors avoid duplicate Holochain export symbols.

- [ ] **Step 4: Run consent tests and verify GREEN**

Run the Step 2 command. Expected: both tests pass; invalid decision returns the exact error code and leaves no decision link.

- [ ] **Step 5: Commit consent coverage**

```bash
git add ARF/tests/sweettest/src/lib.rs ARF/tests/sweettest/tests/consent_zome_test.rs
git commit -m "test: cover consent zomes with Sweettest"
```

---

### Task 4: Fresh-Bundle and Repeatability Verification

**Files:**
- Modify only if generated child resolution changed: `ARF/tests/sweettest/Cargo.lock`

**Interfaces:**
- Consumes all earlier test targets.
- Produces terminal evidence for four current WASM files, fresh DNA packing, two consecutive integration passes, existing unit tests, formatting, and scoped diff.

- [ ] **Step 1: Format and check the workspace**

Run:

```bash
nix develop path:. --command cargo fmt --all -- --check
nix develop path:. --command cargo check --workspace
```

Expected: both exit 0. Existing coordinator warnings may remain; no new test-package warning is accepted.

- [ ] **Step 2: Rebuild all four active WASM zomes from source**

Run:

```bash
nix develop path:. --command cargo build --workspace --locked --release --target wasm32-unknown-unknown
```

Verify these files exist and have nonzero length:

```text
target/wasm32-unknown-unknown/release/rose_forest_integrity.wasm
target/wasm32-unknown-unknown/release/rose_forest.wasm
target/wasm32-unknown-unknown/release/consent_integrity.wasm
target/wasm32-unknown-unknown/release/consent.wasm
```

- [ ] **Step 3: Pack current DNA and run both targets twice**

Run:

```bash
nix develop path:. --command RUST_TEST_THREADS=1 ./tests/sweettest/run.sh --test substrate_bridge_test --test consent_zome_test
nix develop path:. --command RUST_TEST_THREADS=1 ./tests/sweettest/run.sh --test substrate_bridge_test --test consent_zome_test
```

Expected: each runner invocation performs a locked parent build and fresh pack, then passes the isolated child suite serially with identical test counts.

- [ ] **Step 4: Run all existing four-zome unit tests**

Run:

```bash
nix develop path:. --command cargo test --workspace
```

Expected: the parent workspace's original 40 unit tests pass. The standalone child suite is not a parent workspace member; it is separately expected to pass 2 consent and 7 substrate tests through the serial runner.

- [ ] **Step 5: Verify diff scope and artifact policy**

Run:

```bash
git diff --check origin/main...HEAD
git status --short
git diff --name-only origin/main...HEAD
```

Expected changed paths: design/plan docs, `ARF/.cargo/config.toml`, and `ARF/tests/sweettest/**`. The parent workspace manifest and lock remain unchanged by the child workspace. The packed `.dna` artifact should not be committed unless it was already tracked and changed by the required pack; if changed, report it separately and leave it unstaged pending operator direction.

- [ ] **Step 6: Commit final generated resolution if needed**

If `ARF/tests/sweettest/Cargo.lock` changed after the last feature commit:

```bash
git add ARF/tests/sweettest/Cargo.lock
git commit -m "chore: lock Sweettest dependencies"
```

- [ ] **Step 7: Request independent code review**

Use `superpowers:requesting-code-review` on the complete commit range from `origin/main` to `HEAD`. Resolve only findings within the approved test-harness scope; governed zome findings require a separate operator decision.
