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
    hasher.update(update.metadata.agent_id.clone().into_bytes());
    Ok(format!("{:x}", hasher.finalize()))
}

#[hdk_extern]
pub fn validate_model_update(update: ModelUpdate) -> ExternResult<()> {
    if update.weights.is_empty() {
        return Err(WasmError::Guest("Empty weights not allowed".into()));
    }
    if let Some(latest_model) = get_latest_global_model()? {
        if update.version <= latest_model.version {
            return Err(WasmError::Guest("Invalid version number".into()));
        }
    }
    Ok(())
}

#[hdk_extern]
pub fn aggregate_model_updates(updates: Vec<ModelUpdate>) -> ExternResult<AggregationResult> {
    let mut global_model = ModelUpdate {
        weights: vec![0.0; updates[0].weights.len()],
        bias: 0.0,
        version: updates.iter().map(|u| u.version).max().unwrap(),
        metadata: ModelMetadata {
            timestamp: updates.iter().map(|u| u.metadata.timestamp).max().unwrap(),
            metrics: ModelMetrics {
                loss: updates.iter().map(|u| u.metadata.metrics.loss).sum::<f32>() / updates.len() as f32,
                accuracy: updates.iter().map(|u| u.metadata.metrics.accuracy).sum::<f32>() / updates.len() as f32,
                samples_count: updates.iter().map(|u| u.metadata.metrics.samples_count).sum::<u32>(),
            },
            agent_id: updates[0].metadata.agent_id.clone(),
        },
    };

    for update in updates {
        for (i, weight) in update.weights.iter().enumerate() {
            global_model.weights[i] += weight;
        }
        global_model.bias += update.bias;
    }

    for weight in global_model.weights.iter_mut() {
        *weight /= updates.len() as f32;
    }
    global_model.bias /= updates.len() as f32;

    Ok(AggregationResult {
        global_model,
        participating_agents: updates.iter().map(|u| u.metadata.agent_id.clone()).collect(),
    })
}

#[hdk_extern]
pub fn get_latest_global_model() -> ExternResult<Option<ModelUpdate>> {
    let path = Path::from("global_model");
    let links = get_links(path.path_entry_hash()?, LinkTypes::GlobalModelHistory, None)?;
    if let Some(latest_link) = links.last() {
        let element = get(latest_link.target.clone(), GetOptions::default())?
            .ok_or(WasmError::Guest("Global model not found".into()))?;
        let model_update: ModelUpdate = element
            .entry()
            .to_app_option()?
            .ok_or(WasmError::Guest("Invalid model update entry".into()))?;
        Ok(Some(model_update))
    } else {
        Ok(None)
    }
}

#[hdk_extern]
pub fn submit_model_update(update: ModelUpdate) -> ExternResult<ActionHash> {
    validate_model_update(update.clone())?;
    let action_hash = create_entry(&EntryTypes::ModelUpdate(update.clone()))?;
    let path = Path::from("global_model");
    create_link(
        path.path_entry_hash()?,
        action_hash.clone(),
        LinkTypes::ModelUpdateToGlobal,
        (),
    )?;
    Ok(action_hash)
}