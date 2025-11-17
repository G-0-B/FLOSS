use hdk::prelude::*;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

#[hdk_entry_helper]
#[derive(Clone)]
pub struct ModelUpdate {
    pub weights: Vec<f32>,
    pub bias: f32,
    pub version: u32,
    pub metadata: ModelMetadata,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ModelMetadata {
    pub timestamp: u64,
    pub metrics: ModelMetrics,
    pub agent_id: AgentPubKey,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ModelMetrics {
    pub loss: f32,
    pub accuracy: f32,
    pub samples_count: u32,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct AggregationResult {
    pub global_model: ModelUpdate,
    pub participating_agents: Vec<AgentPubKey>,
}

// Define entry types
#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    ModelUpdate(ModelUpdate),
}

// Define link types
#[hdk_link_types]
pub enum LinkTypes {
    GlobalModelHistory,
    ModelUpdateToGlobal,
}

#[hdk_extern]
pub fn hash_model_update(update: ModelUpdate) -> ExternResult<String> {
    let mut hasher = Sha256::new();
    hasher.update(update.weights.iter().flat_map(|x| x.to_le_bytes()).collect::<Vec<_>>());
    hasher.update(update.bias.to_le_bytes());
    hasher.update(update.version.to_le_bytes());
    hasher.update(update.metadata.timestamp.to_le_bytes());
    hasher.update(update.metadata.metrics.loss.to_le_bytes());
    hasher.update(update.metadata.metrics.accuracy.to_le_bytes());
    hasher.update(update.metadata.metrics.samples_count.to_le_bytes());
    hasher.update(update.metadata.agent_id.clone().into_raw_bytes());
    Ok(format!("{:x}", hasher.finalize()))
}

#[hdk_extern]
pub fn validate_model_update(update: ModelUpdate) -> ExternResult<()> {
    if update.weights.is_empty() {
        return Err(wasm_error!(WasmErrorInner::Guest("Empty weights not allowed".to_string())));
    }
    if let Some(latest_model) = get_latest_global_model()? {
        if update.version <= latest_model.version {
            return Err(wasm_error!(WasmErrorInner::Guest("Invalid version number".to_string())));
        }
    }
    Ok(())
}

#[hdk_extern]
pub fn aggregate_model_updates(updates: Vec<ModelUpdate>) -> ExternResult<AggregationResult> {
    if updates.is_empty() {
        return Err(wasm_error!(WasmErrorInner::Guest("No updates to aggregate".to_string())));
    }
    
    let mut global_model = ModelUpdate {
        weights: vec![0.0; updates[0].weights.len()],
        bias: 0.0,
        version: updates.iter().map(|u| u.version).max().unwrap_or(0),
        metadata: ModelMetadata {
            timestamp: sys_time()?.as_millis() as u64,
            metrics: ModelMetrics {
                loss: updates.iter().map(|u| u.metadata.metrics.loss).sum::<f32>() / updates.len() as f32,
                accuracy: updates.iter().map(|u| u.metadata.metrics.accuracy).sum::<f32>() / updates.len() as f32,
                samples_count: updates.iter().map(|u| u.metadata.metrics.samples_count).sum::<u32>(),
            },
            agent_id: agent_info()?.agent_initial_pubkey,
        },
    };

    // Aggregate weights and bias
    for update in &updates {
        for (i, weight) in update.weights.iter().enumerate() {
            global_model.weights[i] += weight;
        }
        global_model.bias += update.bias;
    }

    // Normalize weights and bias
    for weight in global_model.weights.iter_mut() {
        *weight /= updates.len() as f32;
    }
    global_model.bias /= updates.len() as f32;

    // Create result with participating agents
    let participating_agents = updates.iter()
        .map(|u| u.metadata.agent_id.clone())
        .collect::<Vec<_>>();

    Ok(AggregationResult {
        global_model,
        participating_agents,
    })
}

#[hdk_extern]
pub fn get_latest_global_model() -> ExternResult<Option<ModelUpdate>> {
    let path = Path::from("global_model");
    let path_hash = path.path_entry_hash()?;
    
    // Check if the path exists, if not create it
    ensure_path_exists(&path)?;
    
    let links = get_links(path_hash, LinkTypes::GlobalModelHistory, None)?;
    if let Some(latest_link) = links.last() {
        let element = get(latest_link.target.clone(), GetOptions::default())?
            .ok_or(wasm_error!(WasmErrorInner::Guest("Global model not found".to_string())))?;
        let model_update: ModelUpdate = element
            .entry()
            .to_app_option()?
            .ok_or(wasm_error!(WasmErrorInner::Guest("Invalid model update entry".to_string())))?;
        Ok(Some(model_update))
    } else {
        Ok(None)
    }
}

#[hdk_extern]
pub fn submit_model_update(update: ModelUpdate) -> ExternResult<ActionHash> {
    // Validate the model update
    validate_model_update(update.clone())?;
    
    // Create the entry
    let action_hash = create_entry(&EntryTypes::ModelUpdate(update.clone()))?;
    
    // Ensure the global_model path exists
    let path = Path::from("global_model");
    ensure_path_exists(&path)?;
    
    // Create link from path to model update
    create_link(
        path.path_entry_hash()?,
        action_hash.clone(),
        LinkTypes::GlobalModelHistory,
        (),
    )?;
    
    Ok(action_hash)
}

// Helper function to ensure path exists
fn ensure_path_exists(path: &Path) -> ExternResult<()> {
    let path_hash = path.path_entry_hash()?;
    let maybe_path = get(path_hash.clone(), GetOptions::default())?;
    
    if maybe_path.is_none() {
        path.ensure()?;
    }
    
    Ok(())
}

// Validation callback for the DNA
#[hdk_extern]
fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op {
        Op::StoreEntry(store_entry) => {
            match store_entry.entry_type {
                EntryType::App(app_entry_type) => {
                    // Validate ModelUpdate entry
                    if let Some(entry) = store_entry.entry {
                        if let Entry::App(entry_bytes) = entry {
                            if let Ok(model_update) = ModelUpdate::try_from(&entry_bytes) {
                                if model_update.weights.is_empty() {
                                    return Ok(ValidateCallbackResult::Invalid("Empty weights not allowed".to_string()));
                                }
                            }
                        }
                    }
                    Ok(ValidateCallbackResult::Valid)
                }
                _ => Ok(ValidateCallbackResult::Valid),
            }
        }
        Op::RegisterCreateLink { link_type, .. } => {
            // Validate links
            if link_type.0 == LinkTypes::GlobalModelHistory as u8 {
                // Additional validation for GlobalModelHistory links could go here
            }
            Ok(ValidateCallbackResult::Valid)
        }
        _ => Ok(ValidateCallbackResult::Valid),
    }
}