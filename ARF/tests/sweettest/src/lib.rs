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
        "DNA bundle missing: {}",
        bundle_path.display()
    );
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
    await_consistency([&app.alice, &app.bob])
        .await
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
