use holochain::prelude::{AgentPubKey, DnaFile, SerializedBytes, Timestamp};
use holochain::sweettest::{
    await_consistency, SweetCell, SweetConductorBatch, SweetDnaFile, SweetZome,
};
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
    assert!(
        bundle_path.is_file(),
        "DNA bundle missing: {} — build and pack via ./tests/sweettest/run.sh, not bare cargo test",
        bundle_path.display()
    );

    // Verify the four release WASMs exist and are nonzero.  Without this
    // check, a stale gitignored .dna bundle silently passes tests against
    // outdated zome code.  The WASMs are built by run.sh before packing.
    let wasm_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../../target/wasm32-unknown-unknown/release");
    let expected_wasms = [
        "rose_forest_integrity.wasm",
        "rose_forest.wasm",
        "consent_integrity.wasm",
        "consent.wasm",
    ];
    for wasm_name in &expected_wasms {
        let wasm_path = wasm_dir.join(wasm_name);
        let metadata = std::fs::metadata(&wasm_path).unwrap_or_else(|_| {
            panic!(
                "release WASM missing: {} — run ./tests/sweettest/run.sh to build+pack fresh DNA, not bare cargo test",
                wasm_path.display()
            )
        });
        assert!(
            metadata.len() > 0,
            "release WASM is empty: {} — rebuild via ./tests/sweettest/run.sh",
            wasm_path.display()
        );
    }

    let dna: DnaFile = SweetDnaFile::from_bundle(&bundle_path)
        .await
        .expect("DNA bundle must load");
    let integrity_zomes: Vec<_> = dna
        .dna_def()
        .integrity_zomes
        .iter()
        .map(|(name, _)| name.to_string())
        .collect();
    let coordinator_zomes: Vec<_> = dna
        .dna_def()
        .coordinator_zomes
        .iter()
        .map(|(name, _)| name.to_string())
        .collect();
    assert_eq!(
        integrity_zomes,
        ["rose_forest_integrity", "consent_integrity"]
    );
    assert_eq!(coordinator_zomes, [ROSE_ZOME, CONSENT_ZOME]);
    let mut conductors = SweetConductorBatch::from_standard_config_rendezvous(2).await;
    let apps = conductors
        .setup_app("rose-forest-sweettest", &[dna])
        .await
        .expect("DNA must install on both conductors");
    let ((alice,), (bob,)) = apps.into_tuples();
    assert_ne!(
        alice.agent_pubkey(),
        bob.agent_pubkey(),
        "agents must be distinct"
    );
    conductors.exchange_peer_info().await;
    TestApp {
        conductors,
        alice,
        bob,
    }
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

#[derive(Clone, Debug, Serialize)]
pub struct QueryTriplesInput {
    pub subject: Option<String>,
    pub predicate: Option<String>,
}

impl QueryTriplesInput {
    pub fn subject(subject: &str) -> Self {
        Self {
            subject: Some(subject.into()),
            predicate: None,
        }
    }

    pub fn predicate(predicate: &str) -> Self {
        Self {
            subject: None,
            predicate: Some(predicate.into()),
        }
    }
}

#[derive(Clone, Debug, Deserialize)]
pub struct TripleResult {
    pub hash: holochain::prelude::ActionHash,
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub author: AgentPubKey,
    pub created_at: Timestamp,
}

pub async fn await_two_agent_consistency(app: &TestApp) {
    tokio::time::timeout(
        std::time::Duration::from_secs(300),
        await_consistency([&app.alice, &app.bob]),
    )
    .await
    .unwrap_or_else(|_| {
        panic!("DHT consistency not reached in 300s — run via ./tests/sweettest/run.sh, not bare cargo test")
    })
    .expect("both DHT databases must integrate every published op");
}

pub fn mutated_missing_hash(
    real: &holochain::prelude::ActionHash,
) -> holochain::prelude::ActionHash {
    let mut bytes = real.get_raw_39().to_vec();
    for byte in &mut bytes[3..35] {
        *byte ^= 0xa5;
    }
    holochain::prelude::ActionHash::from_raw_39(bytes)
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

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize, SerializedBytes)]
pub struct KnowledgeTriple {
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub source: AgentPubKey,
    pub created_at: Timestamp,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PatternType {
    Kernel,
    Adr,
    FrameTranslation,
    VoterPersona,
    Constitution,
    Claim,
    Skill,
    MemoryEntry,
    Other,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
pub enum BlastRadius {
    Local,
    Module,
    System,
    Substrate,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ConsentScope {
    ReadOnly,
    Integrate,
    Propagate,
    Bind,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RefusalMode {
    Reject,
    BoundedAccept,
    TouristObserve,
    CounterPropose,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Outcome {
    Accepted,
    BoundedAccept,
    TouristObserve,
    CounterPropose,
    Rejected,
}

#[derive(Clone, Debug, Serialize)]
pub struct CreateConsentPayloadInput {
    pub payload_id: String,
    pub pattern_id: String,
    pub pattern_type: PatternType,
    pub pattern_hash: String,
    pub proposer_did: String,
    pub recipient_did: String,
    pub blast_radius: BlastRadius,
    pub consent_scope: Vec<ConsentScope>,
    pub refusal_modes: Option<Vec<RefusalMode>>,
    pub refusable_until: Option<Timestamp>,
    pub parent_consent_id: Option<holochain::prelude::ActionHash>,
    pub rationale: Option<String>,
    pub submitted_at: Option<Timestamp>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
pub struct ConsentPayload {
    pub payload_id: String,
    pub pattern_id: String,
    pub pattern_type: PatternType,
    pub pattern_hash: String,
    pub proposer_did: String,
    pub recipient_did: String,
    pub blast_radius: BlastRadius,
    pub consent_scope: Vec<ConsentScope>,
    pub refusal_modes: Vec<RefusalMode>,
    pub refusable_until: Option<Timestamp>,
    pub parent_consent_id: Option<holochain::prelude::ActionHash>,
    pub rationale: Option<String>,
    pub submitted_at: Timestamp,
}

#[derive(Clone, Debug, Serialize)]
pub struct CreateConsentDecisionInput {
    pub decision_id: String,
    pub payload_action_hash: holochain::prelude::ActionHash,
    pub decider_did: String,
    pub outcome: Outcome,
    pub scope_granted: Vec<ConsentScope>,
    pub rationale: Option<String>,
    pub counter_frame_ref: Option<holochain::prelude::ActionHash>,
    pub expires_at: Option<Timestamp>,
    pub decided_at: Option<Timestamp>,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Eq)]
pub struct ConsentDecision {
    pub decision_id: String,
    pub payload_action_hash: holochain::prelude::ActionHash,
    pub decider_did: String,
    pub outcome: Outcome,
    pub scope_granted: Vec<ConsentScope>,
    pub rationale: Option<String>,
    pub counter_frame_ref: Option<holochain::prelude::ActionHash>,
    pub expires_at: Option<Timestamp>,
    pub decided_at: Timestamp,
}
