use holochain::prelude::{AgentPubKey, DnaFile, SerializedBytes, Timestamp};
use holochain::sweettest::{
    await_consistency, SweetCell, SweetConductorBatch, SweetDnaFile, SweetZome,
};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

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

    let wasm_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../target/wasm32-unknown-unknown/release");
    let dna: DnaFile = SweetDnaFile::from_bundle(&bundle_path)
        .await
        .expect("DNA bundle must load");
    verify_release_wasms(&dna, &wasm_dir).unwrap_or_else(|error| panic!("{error}"));
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

fn verify_release_wasms(dna: &DnaFile, wasm_dir: &Path) -> Result<(), String> {
    let expected_zomes = [
        "rose_forest_integrity",
        ROSE_ZOME,
        "consent_integrity",
        CONSENT_ZOME,
    ];
    for zome_name in expected_zomes {
        let wasm_path = wasm_dir.join(format!("{zome_name}.wasm"));
        let release_bytes = std::fs::read(&wasm_path).map_err(|error| {
            format!(
                "release WASM missing or unreadable: {} ({error}) — run ./tests/sweettest/run.sh to build+pack fresh DNA, not bare cargo test",
                wasm_path.display()
            )
        })?;
        if release_bytes.is_empty() {
            return Err(format!(
                "release WASM is empty: {} — rebuild via ./tests/sweettest/run.sh",
                wasm_path.display()
            ));
        }
        let packed_wasm = dna
            .get_wasm_for_zome(&zome_name.into())
            .map_err(|error| format!("DNA bundle WASM unavailable for {zome_name}: {error}"))?;
        // Both integrity and coordinator code must match, including when tests
        // are invoked directly against an existing gitignored DNA bundle.
        if packed_wasm.code.as_ref() != release_bytes.as_slice() {
            return Err(format!(
                "DNA bundle WASM differs from release WASM for {zome_name}: {} — repack via ./tests/sweettest/run.sh",
                wasm_path.display()
            ));
        }
    }
    Ok(())
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
    let mut bytes = real.get_raw_32().to_vec();
    for byte in &mut bytes {
        *byte ^= 0xa5;
    }
    holochain::prelude::ActionHash::from_raw_32(bytes)
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

#[cfg(test)]
mod tests {
    use super::*;
    use holochain::prelude::{
        ActionHash, CoordinatorZome, DnaWasm, IntegrityZome, WasmHash, WasmZome, ZomeDef,
    };

    const ZOME_NAMES: [&str; 4] = [
        "rose_forest_integrity",
        "consent_integrity",
        "rose_forest",
        "consent",
    ];

    async fn bundle_fixture() -> (DnaFile, PathBuf) {
        let unique = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let wasm_dir =
            std::env::temp_dir().join(format!("rose-sweettest-{}-{unique}", std::process::id()));
        std::fs::create_dir_all(&wasm_dir).unwrap();
        let mut wasms = Vec::new();
        let mut definitions = Vec::new();
        for (index, name) in ZOME_NAMES.iter().enumerate() {
            // Minimal valid WASM, with a distinct custom-section name per zome.
            let bytes = vec![0, 97, 115, 109, 1, 0, 0, 0, 0, 2, 1, b'a' + index as u8];
            std::fs::write(wasm_dir.join(format!("{name}.wasm")), &bytes).unwrap();
            let wasm = DnaWasm::from(bytes);
            let hash = WasmHash::with_data(&wasm).await;
            definitions.push(ZomeDef::Wasm(WasmZome::new(hash, None)));
            wasms.push(wasm);
        }
        let integrity: Vec<IntegrityZome> = (0..2)
            .map(|index| {
                IntegrityZome::new(ZOME_NAMES[index].into(), definitions[index].clone().into())
            })
            .collect();
        let coordinator: Vec<CoordinatorZome> = (2..4)
            .map(|index| {
                CoordinatorZome::new(ZOME_NAMES[index].into(), definitions[index].clone().into())
            })
            .collect();
        let (dna, _, _) = SweetDnaFile::unique_from_zomes(integrity, coordinator, wasms).await;
        (dna, wasm_dir)
    }

    #[tokio::test]
    async fn matching_bundle_and_release_wasms_are_accepted() {
        let (dna, wasm_dir) = bundle_fixture().await;
        assert_eq!(verify_release_wasms(&dna, &wasm_dir), Ok(()));
    }

    #[tokio::test]
    async fn stale_bundle_is_rejected_for_each_integrity_and_coordinator_zome() {
        for name in ZOME_NAMES {
            let (dna, wasm_dir) = bundle_fixture().await;
            let path = wasm_dir.join(format!("{name}.wasm"));
            let mut updated = std::fs::read(&path).unwrap();
            *updated.last_mut().unwrap() = b'z';
            std::fs::write(&path, updated).unwrap();
            let error = verify_release_wasms(&dna, &wasm_dir)
                .expect_err("stale packed WASM must fail before conductor startup");
            assert!(
                error.contains(name),
                "diagnostic must identify {name}: {error}"
            );
        }
    }

    #[test]
    fn missing_hash_recomputes_canonical_dht_location() {
        let real = ActionHash::from_raw_32(vec![0; 32]);
        let missing = mutated_missing_hash(&real);
        assert_eq!(real.get_raw_32(), &[0; 32]);
        assert_eq!(missing.get_raw_32(), &[0xa5; 32]);
        assert_eq!(&missing.get_raw_39()[..3], &real.get_raw_39()[..3]);
        // Independent known vector: BLAKE2b-128([0xa5; 32]), XOR-folded to four bytes.
        assert_eq!(&missing.get_raw_39()[35..], &[0x12, 0xa5, 0x20, 0xbf]);
    }
}
