use holochain::prelude::{AgentPubKey, DnaFile, SerializedBytes, Timestamp};
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
    assert!(
        bundle_path.is_file(),
        "fresh DNA bundle missing: {}",
        bundle_path.display()
    );
    let dna: DnaFile = SweetDnaFile::from_bundle(&bundle_path)
        .await
        .expect("fresh four-zome DNA bundle must load");
    let mut conductors = SweetConductorBatch::from_standard_config_rendezvous(2).await;
    let apps = conductors
        .setup_app("rose-forest-sweettest", &[dna])
        .await
        .expect("four-zome DNA must install on both conductors");
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
