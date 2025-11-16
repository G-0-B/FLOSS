use hdk::prelude::*;
use identity_integrity::{
    AutonomousIdentifier, KeyEventLog, KeyEvent, KeyEventType, IdentitySeal,
    EntryTypes, LinkTypes,
};

/// Identity Coordinator Zome
///
/// Implements the KERI-Holochain identity bridge, enabling agents to:
/// 1. Register KERI AIDs
/// 2. Create cryptographic seals binding AIDs to Holochain agents
/// 3. Verify identity across systems
/// 4. Query identities by AID or AgentPubKey
/// 5. Rotate keys while maintaining identity continuity

#[hdk_extern]
pub fn register_aid(aid_input: RegisterAIDInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;

    // Create the AID entry
    let aid = AutonomousIdentifier {
        aid: aid_input.aid.clone(),
        current_public_key: aid_input.public_key.clone(),
        inception_public_key: aid_input.inception_public_key.clone(),
        sequence: 1, // Initial state
        kel_hash: None, // Will be updated after KEL creation
        created_at: sys_time()?,
    };

    let aid_hash = create_entry(EntryTypes::AutonomousIdentifier(aid.clone()))?;

    // Create initial Key Event Log
    let inception_event = KeyEvent {
        event_type: KeyEventType::Inception,
        sequence: 0,
        previous_event_digest: None,
        keys: vec![aid_input.public_key.clone()],
        witness_signatures: vec![], // Would be populated by KERI witness network
        timestamp: sys_time()?,
        data: aid_input.metadata.unwrap_or_default(),
    };

    let kel = KeyEventLog {
        aid: aid_input.aid.clone(),
        events: vec![inception_event],
        updated_at: sys_time()?,
    };

    let kel_hash = create_entry(EntryTypes::KeyEventLog(kel))?;

    // Link AID to KEL
    create_link(
        aid_hash.clone(),
        kel_hash.clone(),
        LinkTypes::AIDToKEL,
        (),
    )?;

    // Create anchor path for AID lookup
    let aid_anchor = Path::from(format!("aid:{}", aid_input.aid));
    aid_anchor.ensure()?;

    // Link from anchor to AID entry for efficient lookup
    create_link(
        aid_anchor.path_entry_hash()?,
        aid_hash.clone(),
        LinkTypes::AIDPathToEntry,
        (),
    )?;

    Ok(aid_hash)
}

#[hdk_extern]
pub fn create_identity_seal(seal_input: CreateSealInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;

    // Verify the agent creating the seal matches the one in the seal
    if agent != seal_input.agent_pubkey {
        return Err(wasm_error!(WasmErrorInner::Guest(
            "Agent mismatch: only the agent can seal their own identity".to_string()
        )));
    }

    // Verify AID exists
    let aid_hash = get_aid_hash(&seal_input.aid)?;

    // Create the seal
    let seal = IdentitySeal {
        aid: seal_input.aid.clone(),
        agent_pubkey: seal_input.agent_pubkey.clone(),
        keri_signature: seal_input.keri_signature.clone(),
        agent_signature: seal_input.agent_signature.clone(),
        sealed_at: sys_time()?,
        authorizing_event: aid_hash.clone(),
    };

    let seal_hash = create_entry(EntryTypes::IdentitySeal(seal))?;

    // Create bidirectional links
    create_link(
        agent.clone().into(),
        seal_hash.clone(),
        LinkTypes::AgentToSeal,
        (),
    )?;

    // Link from AID to seal (using AID string as anchor)
    let aid_anchor = Path::from(format!("aid:{}", seal_input.aid));
    aid_anchor.ensure()?;

    create_link(
        aid_anchor.path_entry_hash()?,
        seal_hash.clone(),
        LinkTypes::AIDToSeal,
        (),
    )?;

    // Link seal to AID
    create_link(
        seal_hash.clone(),
        aid_hash,
        LinkTypes::SealToAID,
        (),
    )?;

    Ok(seal_hash)
}

#[hdk_extern]
pub fn get_aid_for_agent(agent: AgentPubKey) -> ExternResult<Option<AutonomousIdentifier>> {
    // Get seal for this agent
    let links = get_links(
        GetLinksInputBuilder::try_new(agent.into(), LinkTypes::AgentToSeal)?.build(),
    )?;

    if links.is_empty() {
        return Ok(None);
    }

    // Get the seal
    let seal_hash: ActionHash = links[0].target.clone().into();
    let seal_record = get(seal_hash.clone(), GetOptions::default())?;

    let seal = match seal_record {
        Some(record) => {
            let seal: IdentitySeal = record.entry().to_app_option()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                .ok_or(wasm_error!(WasmErrorInner::Guest("Expected IdentitySeal".to_string())))?;
            seal
        }
        None => return Ok(None),
    };

    // Get the AID through the seal
    let aid_links = get_links(
        GetLinksInputBuilder::try_new(seal_hash, LinkTypes::SealToAID)?.build(),
    )?;

    if aid_links.is_empty() {
        return Ok(None);
    }

    let aid_hash: ActionHash = aid_links[0].target.clone().into();
    let aid_record = get(aid_hash, GetOptions::default())?;

    match aid_record {
        Some(record) => {
            let aid: AutonomousIdentifier = record.entry().to_app_option()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                .ok_or(wasm_error!(WasmErrorInner::Guest("Expected AutonomousIdentifier".to_string())))?;
            Ok(Some(aid))
        }
        None => Ok(None),
    }
}

#[hdk_extern]
pub fn get_agent_for_aid(aid: String) -> ExternResult<Option<AgentPubKey>> {
    // Get seal for this AID
    let aid_anchor = Path::from(format!("aid:{}", aid));
    let aid_hash = aid_anchor.path_entry_hash()?;

    let links = get_links(
        GetLinksInputBuilder::try_new(aid_hash, LinkTypes::AIDToSeal)?.build(),
    )?;

    if links.is_empty() {
        return Ok(None);
    }

    // Get the seal
    let seal_hash: ActionHash = links[0].target.clone().into();
    let seal_record = get(seal_hash, GetOptions::default())?;

    match seal_record {
        Some(record) => {
            let seal: IdentitySeal = record.entry().to_app_option()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                .ok_or(wasm_error!(WasmErrorInner::Guest("Expected IdentitySeal".to_string())))?;
            Ok(Some(seal.agent_pubkey))
        }
        None => Ok(None),
    }
}

#[hdk_extern]
pub fn get_key_event_log(aid: String) -> ExternResult<Option<KeyEventLog>> {
    let aid_hash = get_aid_hash(&aid)?;

    let links = get_links(
        GetLinksInputBuilder::try_new(aid_hash, LinkTypes::AIDToKEL)?.build(),
    )?;

    if links.is_empty() {
        return Ok(None);
    }

    let kel_hash: ActionHash = links[0].target.clone().into();
    let kel_record = get(kel_hash, GetOptions::default())?;

    match kel_record {
        Some(record) => {
            let kel: KeyEventLog = record.entry().to_app_option()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                .ok_or(wasm_error!(WasmErrorInner::Guest("Expected KeyEventLog".to_string())))?;
            Ok(Some(kel))
        }
        None => Ok(None),
    }
}

#[hdk_extern]
pub fn rotate_key(rotation_input: RotateKeyInput) -> ExternResult<ActionHash> {
    // Get existing AID
    let aid_hash = get_aid_hash(&rotation_input.aid)?;
    let aid_record = get(aid_hash.clone(), GetOptions::default())?
        .ok_or(wasm_error!(WasmErrorInner::Guest("AID not found".to_string())))?;

    let mut aid: AutonomousIdentifier = aid_record.entry().to_app_option()
        .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
        .ok_or(wasm_error!(WasmErrorInner::Guest("Expected AutonomousIdentifier".to_string())))?;

    // Get existing KEL
    let kel_links = get_links(
        GetLinksInputBuilder::try_new(aid_hash.clone(), LinkTypes::AIDToKEL)?.build(),
    )?;

    let kel_hash: ActionHash = kel_links[0].target.clone().into();
    let kel_record = get(kel_hash, GetOptions::default())?
        .ok_or(wasm_error!(WasmErrorInner::Guest("KEL not found".to_string())))?;

    let mut kel: KeyEventLog = kel_record.entry().to_app_option()
        .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
        .ok_or(wasm_error!(WasmErrorInner::Guest("Expected KeyEventLog".to_string())))?;

    // Create rotation event
    let previous_digest = compute_event_digest(&kel.events.last().unwrap());
    let rotation_event = KeyEvent {
        event_type: KeyEventType::Rotation,
        sequence: aid.sequence + 1,
        previous_event_digest: Some(previous_digest),
        keys: vec![rotation_input.new_public_key.clone()],
        witness_signatures: rotation_input.witness_signatures,
        timestamp: sys_time()?,
        data: rotation_input.metadata.unwrap_or_default(),
    };

    // Update KEL
    kel.events.push(rotation_event);
    kel.updated_at = sys_time()?;

    let new_kel_hash = update_entry(kel_hash, EntryTypes::KeyEventLog(kel))?;

    // Update AID
    aid.current_public_key = rotation_input.new_public_key;
    aid.sequence += 1;
    aid.kel_hash = Some(new_kel_hash);

    let new_aid_hash = update_entry(aid_hash, EntryTypes::AutonomousIdentifier(aid))?;

    Ok(new_aid_hash)
}

// Helper functions

fn get_aid_hash(aid: &str) -> ExternResult<ActionHash> {
    // Use Path anchor to find AID entry
    let aid_anchor = Path::from(format!("aid:{}", aid));

    // Get links from anchor to AID entry
    let links = get_links(
        GetLinksInputBuilder::try_new(
            aid_anchor.path_entry_hash()?,
            LinkTypes::AIDPathToEntry
        )?.build(),
    )?;

    // Should only be one AID entry per anchor
    if links.is_empty() {
        return Err(wasm_error!(WasmErrorInner::Guest(
            format!("AID not found: {}", aid)
        )));
    }

    // Return the first link target (the AID entry hash)
    Ok(links[0].target.clone().into())
}

fn compute_event_digest(event: &KeyEvent) -> String {
    use sha2::{Sha256, Digest};
    let serialized = serde_json::to_string(event).unwrap_or_default();
    let hash = Sha256::digest(serialized.as_bytes());
    format!("{:x}", hash)
}

// Input structures

#[derive(Serialize, Deserialize, Debug)]
pub struct RegisterAIDInput {
    pub aid: String,
    pub public_key: Vec<u8>,
    pub inception_public_key: Vec<u8>,
    pub metadata: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateSealInput {
    pub aid: String,
    pub agent_pubkey: AgentPubKey,
    pub keri_signature: Vec<u8>,
    pub agent_signature: Vec<u8>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct RotateKeyInput {
    pub aid: String,
    pub new_public_key: Vec<u8>,
    pub witness_signatures: Vec<String>,
    pub metadata: Option<String>,
}
