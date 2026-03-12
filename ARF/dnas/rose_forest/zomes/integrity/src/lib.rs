use hdi::prelude::*;
use std::collections::BTreeMap;

#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct RoseNode {
    pub content: String,
    pub embedding: Vec<f32>,
    pub license: String,
    pub metadata: BTreeMap<String, String>,
}

#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeEdge {
    pub from: ActionHash,
    pub to: ActionHash,
    pub relationship: String,
    pub confidence: f32,
}

#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct BudgetEntry {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}

#[hdk_link_types]
pub enum LinkTypes { AllNodes, ShardMember, Edge, AgentBudget }

#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    RoseNode(RoseNode),
    KnowledgeEdge(KnowledgeEdge),
    BudgetEntry(BudgetEntry),
    ThoughtCredential(ThoughtCredential),
}

#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store) => match store {
            OpEntry::CreateEntry { app_entry, .. } | OpEntry::UpdateEntry { app_entry, .. } => {
                match app_entry {
                    EntryTypes::RoseNode(node) => validate_rose_node(&node),
                    EntryTypes::KnowledgeEdge(edge) => validate_knowledge_edge(&edge),
                    EntryTypes::BudgetEntry(_) => Ok(ValidateCallbackResult::Valid),
                    EntryTypes::ThoughtCredential(credential) => validate_thought_credential(&credential),
                }
            }
            _ => Ok(ValidateCallbackResult::Valid),
        },
        _ => Ok(ValidateCallbackResult::Valid),
    }
}

fn validate_thought_credential(credential: &ThoughtCredential) -> ExternResult<ValidateCallbackResult> {
    let dim = credential.content.len();
    if dim < 32 || dim > 4096 {
        return Ok(ValidateCallbackResult::Invalid(format!("E_THOUGHT_CONTENT_DIM: {} out of [32,4096]", dim)));
    }
    if !(-1..=1).contains(&credential.connotation) {
        return Ok(ValidateCallbackResult::Invalid(format!("E_CONNOTATION: {} out of [-1,1]", credential.connotation)));
    }
    if !(0.0..=1.0).contains(&credential.impact) {
        return Ok(ValidateCallbackResult::Invalid(format!("E_IMPACT: {} out of [0,1]", credential.impact)));
    }
    // Further validation could include checking provenance signature or resonance thresholds
    Ok(ValidateCallbackResult::Valid)
}

fn validate_rose_node(node: &RoseNode) -> ExternResult<ValidateCallbackResult> {
    const VALID_LICENSES: &[&str] = &["MIT","Apache-2.0","BSD-3-Clause","MPL-2.0","CC-BY-4.0"];
    if !VALID_LICENSES.contains(&node.license.as_str()) {
        return Ok(ValidateCallbackResult::Invalid(format!("E_LICENSE: '{}' not allowed", node.license)));
    }
    let dim = node.embedding.len();
    if dim < 32 || dim > 4096 {
        return Ok(ValidateCallbackResult::Invalid(format!("E_EMBED_DIM: {} out of [32,4096]", dim)));
    }
    match (node.metadata.get("model_id"), node.metadata.get("model_card_hash")) {
        (Some(_), Some(hash)) if hash.starts_with("sha256:") => Ok(ValidateCallbackResult::Valid),
        _ => Ok(ValidateCallbackResult::Invalid("E_MODEL_CARD_MISSING".into())),
    }
}

fn validate_knowledge_edge(edge: &KnowledgeEdge) -> ExternResult<ValidateCallbackResult> {
    if !(0.0..=1.0).contains(&edge.confidence) {
        return Ok(ValidateCallbackResult::Invalid(format!("E_CONFIDENCE: {} out of [0,1]", edge.confidence)));
    }
    // New relationship types reflecting the manifesto
    const VALID_RELATIONSHIPS: &[&str] = &["relates_to", "supports", "contradicts", "heals", "releases", "neutralizes", "recalibrates"];
    if !VALID_RELATIONSHIPS.contains(&edge.relationship.as_str()) {
        return Ok(ValidateCallbackResult::Invalid(format!("E_RELATIONSHIP: '{}' not allowed", edge.relationship)));
    }
    Ok(ValidateCallbackResult::Valid)
}




#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ThoughtCredential {
    pub content: Vec<f32>, // SemanticVector
    pub connotation: i8, // TernaryScore: -1, 0, 1
    pub provenance: AgentPubKey, // AgentSignature
    pub resonance: Vec<AgentPubKey>, // AgentEndorsement
    pub impact: f32, // WisdomMetric
}