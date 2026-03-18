use hdi::prelude::*;
use std::collections::BTreeMap;

/// Represents a node in the Rose-Forest knowledge graph.
///
/// Each `RoseNode` is an atomic unit of knowledge, containing a piece of
/// content, its semantic embedding, and associated metadata. These nodes form
/// the vertices of the decentralized knowledge graph, which is a core component
/// of the "Federated Knowledge Commons."
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct RoseNode {
    pub content: String,
    pub embedding: Vec<f32>,
    pub license: String,
    pub metadata: BTreeMap<String, String>,
}

/// Represents a directed, weighted edge between two `RoseNode`s.
///
/// `KnowledgeEdge`s define the relationships between nodes in the knowledge
/// graph, allowing for the creation of complex semantic networks. The
/// `relationship` and `confidence` fields provide a rich way to express the
/// nature and strength of the connection between two pieces of knowledge.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeEdge {
    pub from: ActionHash,
    pub to: ActionHash,
    pub relationship: String,
    pub confidence: f32,
}

/// Tracks the computational budget for an agent.
///
/// This entry is part of the system's resource management and incentive
/// mechanism. It ensures that agents have a defined "autonomy budget,"
/// preventing any single agent from consuming an undue amount of computational
/// resources.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct BudgetEntry {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}

#[hdk_link_types]
pub enum LinkTypes { AllNodes, Edge }

#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    RoseNode(RoseNode),
    KnowledgeEdge(KnowledgeEdge),
    BudgetEntry(BudgetEntry),
    ThoughtCredential(ThoughtCredential),
}

/// The primary validation callback for this integrity zome.
///
/// This function is called by the Holochain conductor for every operation that
/// attempts to modify the DHT. It acts as the guardian of the shared knowledge
/// graph, enforcing the validation rules for `RoseNode`s, `KnowledgeEdge`s, and
/// `ThoughtCredential`s. This is a critical component of the "Verifiable
/// Provenance" system.
///
/// TODO: Needs refinement by a human expert.
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



/// A verifiable credential representing a moment of "thought" or insight.
///
/// This struct is a more abstract and fine-grained representation of knowledge
/// than a `RoseNode`. It captures the semantic essence of a thought, its emotional
/// connotation, its provenance (who thought it), and its perceived impact.
/// This is a key data structure for enabling "Cognitive Liberation" and the
/// fine-grained tracking of memetic evolution.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ThoughtCredential {
    pub content: Vec<f32>, // SemanticVector
    pub connotation: i8, // TernaryScore: -1, 0, 1
    pub provenance: AgentPubKey, // AgentSignature
    pub resonance: Vec<AgentPubKey>, // AgentEndorsement
    pub impact: f32, // WisdomMetric
}