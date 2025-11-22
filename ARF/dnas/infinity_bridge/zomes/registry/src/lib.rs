use hdk::prelude::*;

/// Represents the registration of a "bridge" in the decentralized network.
///
/// A bridge is a hardware or software component that provides sensory data or
/// computational capabilities to the multi-agent system. This entry in the DHT
/// makes the bridge discoverable by other agents, enabling the "AGI@Home" vision
/// of a distributed, democratized compute and sensor network.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct BridgeRegistration {
    pub bridge_id: String,
    pub capabilities: Vec<String>,  // ["acoustic_20hz_20khz", "fft_1024"]
    pub transport: Vec<String>,     // ["usb_hid", "tcp"]
    pub endpoint: String,
    pub signature: Vec<u8>,         // Cryptographic signature
    pub timestamp: Timestamp,
}

/// Defines the metadata for a specific data stream provided by a bridge.
///
/// This entry provides the necessary technical details for an agent to connect
/// to and interpret a data stream, such as its type, sample rate, and data format.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct StreamMetadata {
    pub bridge_id: String,
    pub stream_type: String,        // "acoustic/spectrum", "vibration/time_series"
    pub sample_rate_hz: u32,
    pub data_format: String,        // "float32", "int16", etc.
    pub buffer_size: u32,
}

#[hdk_link_types]
pub enum LinkTypes {
    AllBridges,
    BridgeStreams,
    CapabilityIndex,
}

#[hdk_entry_defs]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    BridgeRegistration(BridgeRegistration),
    StreamMetadata(StreamMetadata),
}

/// Registers a new bridge, making it discoverable to other agents in the network.
///
/// This function creates a `BridgeRegistration` entry in the DHT and links it
/// from a global anchor ("all_bridges") as well as from capability-specific
/// anchors. This allows for efficient discovery of bridges by their capabilities.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn register_bridge(registration: BridgeRegistration) -> ExternResult<ActionHash> {
    // Validate signature (simplified for now)
    if registration.signature.is_empty() {
        return Err(wasm_error!(WasmErrorInner::Guest(
            "Invalid signature".to_string()
        )));
    }

    // Create entry
    let hash = create_entry(&EntryTypes::BridgeRegistration(registration.clone()))?;

    // Create link for discovery
    let path = Path::from("all_bridges");
    path.ensure()?;
    create_link(
        path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::AllBridges,
        LinkTag::new(registration.bridge_id.as_bytes()),
    )?;

    // Index by capabilities
    for capability in &registration.capabilities {
        let cap_path = Path::from(format!("capability:{}", capability));
        cap_path.ensure()?;
        create_link(
            cap_path.path_entry_hash()?,
            hash.clone(),
            LinkTypes::CapabilityIndex,
            LinkTag::new(registration.bridge_id.as_bytes()),
        )?;
    }

    Ok(hash)
}

/// Discovers all registered bridges in the network.
///
/// This function queries the "all_bridges" anchor in the DHT to retrieve a list
/// of all `BridgeRegistration` entries.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn discover_bridges(_: ()) -> ExternResult<Vec<BridgeRegistration>> {
    let path = Path::from("all_bridges");
    let links = get_links(GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::AllBridges)?.build())?;

    let mut bridges = Vec::new();
    for link in links {
        if let Some(registration) = get_bridge_by_hash(link.target.into())? {
            bridges.push(registration);
        }
    }

    Ok(bridges)
}

/// Discovers registered bridges that provide a specific capability.
///
/// This function allows agents to find bridges that are relevant to their
/// current task, for example, by querying for "acoustic" or "vibration"
/// capabilities.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn discover_by_capability(capability: String) -> ExternResult<Vec<BridgeRegistration>> {
    let cap_path = Path::from(format!("capability:{}", capability));
    let links = get_links(GetLinksInputBuilder::try_new(cap_path.path_entry_hash()?, LinkTypes::CapabilityIndex)?.build())?;

    let mut bridges = Vec::new();
    for link in links {
        if let Some(registration) = get_bridge_by_hash(link.target.into())? {
            bridges.push(registration);
        }
    }

    Ok(bridges)
}

/// Registers a new data stream provided by a bridge.
///
/// This function creates a `StreamMetadata` entry in the DHT and links it to the
/// specified `bridge_id`. This allows other agents to discover the data streams
/// that a particular bridge offers.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn register_stream(stream: StreamMetadata) -> ExternResult<ActionHash> {
    let hash = create_entry(&EntryTypes::StreamMetadata(stream.clone()))?;

    // Link stream to bridge
    let bridge_path = Path::from(format!("bridge:{}", stream.bridge_id));
    bridge_path.ensure()?;
    create_link(
        bridge_path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::BridgeStreams,
        LinkTag::new(stream.stream_type.as_bytes()),
    )?;

    Ok(hash)
}

/// Retrieves the list of data streams for a specific bridge.
///
/// This function queries the DHT for `StreamMetadata` entries that are linked to
/// the given `bridge_id`.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn get_bridge_streams(bridge_id: String) -> ExternResult<Vec<StreamMetadata>> {
    let bridge_path = Path::from(format!("bridge:{}", bridge_id));
    let links = get_links(GetLinksInputBuilder::try_new(bridge_path.path_entry_hash()?, LinkTypes::BridgeStreams)?.build())?;

    let mut streams = Vec::new();
    for link in links {
        if let Some(record) = get(link.target.into(), GetOptions::default())? {
            if let Some(EntryTypes::StreamMetadata(stream)) = record.entry().to_app_option()? {
                streams.push(stream);
            }
        }
    }

    Ok(streams)
}

/// Unregisters a bridge from the network.
///
/// This function removes the links that make a bridge discoverable, effectively
/// taking it offline from the perspective of the multi-agent system.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn unregister_bridge(bridge_id: String) -> ExternResult<()> {
    let path = Path::from("all_bridges");
    let links = get_links(GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::AllBridges)?.build())?;

    for link in links {
        if String::from_utf8_lossy(link.tag.as_ref()) == bridge_id {
            delete_link(link.create_link_hash)?;
        }
    }

    Ok(())
}

// Helper functions

fn get_bridge_by_hash(hash: ActionHash) -> ExternResult<Option<BridgeRegistration>> {
    if let Some(record) = get(hash, GetOptions::default())? {
        if let Some(EntryTypes::BridgeRegistration(registration)) = record.entry().to_app_option()? {
            return Ok(Some(registration));
        }
    }
    Ok(None)
}

#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store) => match store {
            OpEntry::CreateEntry { app_entry, .. } | OpEntry::UpdateEntry { app_entry, .. } => {
                match app_entry {
                    EntryTypes::BridgeRegistration(registration) => validate_bridge_registration(&registration),
                    EntryTypes::StreamMetadata(stream) => validate_stream_metadata(&stream),
                }
            }
            _ => Ok(ValidateCallbackResult::Valid),
        },
        _ => Ok(ValidateCallbackResult::Valid),
    }
}

fn validate_bridge_registration(registration: &BridgeRegistration) -> ExternResult<ValidateCallbackResult> {
    // Bridge ID must not be empty
    if registration.bridge_id.is_empty() {
        return Ok(ValidateCallbackResult::Invalid("Bridge ID cannot be empty".to_string()));
    }

    // Must have at least one capability
    if registration.capabilities.is_empty() {
        return Ok(ValidateCallbackResult::Invalid("Must have at least one capability".to_string()));
    }

    // Must have at least one transport
    if registration.transport.is_empty() {
        return Ok(ValidateCallbackResult::Invalid("Must have at least one transport".to_string()));
    }

    // Endpoint must not be empty
    if registration.endpoint.is_empty() {
        return Ok(ValidateCallbackResult::Invalid("Endpoint cannot be empty".to_string()));
    }

    Ok(ValidateCallbackResult::Valid)
}

fn validate_stream_metadata(stream: &StreamMetadata) -> ExternResult<ValidateCallbackResult> {
    // Sample rate must be reasonable
    if stream.sample_rate_hz == 0 || stream.sample_rate_hz > 1_000_000 {
        return Ok(ValidateCallbackResult::Invalid("Invalid sample rate".to_string()));
    }

    // Buffer size must be positive
    if stream.buffer_size == 0 {
        return Ok(ValidateCallbackResult::Invalid("Buffer size must be positive".to_string()));
    }

    Ok(ValidateCallbackResult::Valid)
}
