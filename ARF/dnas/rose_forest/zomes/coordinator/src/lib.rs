use hdk::prelude::*;
use rose_forest_integrity::*;

mod budget;
mod ontology;
mod vector_ops;

use budget::{consume_budget, get_budget_state, BudgetEngine, BudgetState};
use budget::{
    COST_ADD_KNOWLEDGE, COST_CREATE_THOUGHT_CREDENTIAL, COST_LINK_EDGE, COST_VALIDATE_TRIPLE,
};
pub use budget::{COST_COMPOSE_MEMORIES, COST_RECALL_UNDERSTANDINGS, COST_TRANSMIT_UNDERSTANDING};
use std::collections::BTreeMap;
use vector_ops::Vector;

#[derive(Serialize, Deserialize, Debug)]
pub struct AddNodeInput {
    pub content: String,
    pub embedding: Vec<f32>,
    pub license: String,
    pub metadata: BTreeMap<String, String>,
}
#[derive(Serialize, Deserialize, Debug)]
pub struct SearchInput {
    pub query_embedding: Vec<f32>,
    pub k: usize,
}
#[derive(Serialize, Deserialize, Debug)]
pub struct SearchResult {
    pub hash: ActionHash,
    pub score: f32,
    pub content: String,
}
#[derive(Serialize, Deserialize, Debug)]
pub struct AddEdgeInput {
    pub from: ActionHash,
    pub to: ActionHash,
    pub relationship: String,
    pub confidence: f32,
}

#[hdk_extern]
pub fn add_knowledge(input: AddNodeInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;
    consume_budget(&agent, COST_ADD_KNOWLEDGE)?;
    let node = RoseNode {
        content: input.content.clone(),
        embedding: input.embedding,
        license: input.license,
        metadata: input.metadata,
    };
    let hash = create_entry(EntryTypes::RoseNode(node))?;
    // Link into the all_nodes discovery path — the DHT handles distribution
    // across neighborhoods automatically, no manual sharding needed.
    let all_nodes_path = Path::from("all_nodes");
    create_link(
        all_nodes_path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::AllNodes,
        (),
    )?;
    Ok(hash)
}

#[hdk_extern]
pub fn vector_search(input: SearchInput) -> ExternResult<Vec<SearchResult>> {
    let query = Vector::new(input.query_embedding);
    let all_nodes_path = Path::from("all_nodes");
    let links = get_links(
        GetLinksInputBuilder::try_new(all_nodes_path.path_entry_hash()?, LinkTypes::AllNodes)?
            .build(),
    )?;
    let mut results: Vec<SearchResult> = Vec::new();
    for link in links {
        let target_hash =
            link.target
                .into_action_hash()
                .ok_or(wasm_error!(WasmErrorInner::Guest(
                    "Invalid action hash".into()
                )))?;
        if let Some(record) = get(target_hash.clone(), GetOptions::default())? {
            if let Some(node) = record
                .entry()
                .to_app_option::<RoseNode>()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
            {
                let node_vec = Vector::new(node.embedding);
                // Skip embeddings with mismatched dimensions rather than
                // trapping the entire search — the DHT may contain embeddings
                // of varying sizes from different models.
                match query.cosine_similarity(&node_vec) {
                    Ok(score) => results.push(SearchResult {
                        hash: target_hash,
                        score,
                        content: node.content,
                    }),
                    Err(_) => continue,
                }
            }
        }
    }
    results.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    results.truncate(input.k);
    Ok(results)
}

#[hdk_extern]
pub fn link_edge(input: AddEdgeInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;
    consume_budget(&agent, COST_LINK_EDGE)?;
    let edge = KnowledgeEdge {
        from: input.from.clone(),
        to: input.to.clone(),
        relationship: input.relationship,
        confidence: input.confidence,
    };
    let hash = create_entry(EntryTypes::KnowledgeEdge(edge))?;
    create_link(input.from, hash.clone(), LinkTypes::Edge, ())?;
    Ok(hash)
}

#[hdk_extern]
pub fn budget_status(_: ()) -> ExternResult<BudgetState> {
    get_budget_state(&agent_info()?.agent_latest_pubkey)
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateThoughtCredentialInput {
    pub content: Vec<f32>,
    pub connotation: i8,
    pub resonance: Vec<AgentPubKey>,
    pub impact: f32,
}

#[hdk_extern]
pub fn create_thought_credential(input: CreateThoughtCredentialInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;
    consume_budget(&agent, COST_CREATE_THOUGHT_CREDENTIAL)?;

    let thought_credential = ThoughtCredential {
        content: input.content,
        connotation: input.connotation,
        provenance: agent.clone(),
        resonance: input.resonance,
        impact: input.impact,
    };

    let hash = create_entry(EntryTypes::ThoughtCredential(thought_credential))?;
    let thoughtforms_path = Path::from("all_thought_credentials");
    create_link(
        thoughtforms_path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::AllNodes,
        (),
    )?;

    Ok(hash)
}

// --- Phase 1: Knowledge Triples ---

#[derive(Serialize, Deserialize, Debug)]
pub struct AssertTripleInput {
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct TripleResult {
    pub hash: ActionHash,
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub author: AgentPubKey,
    pub created_at: Timestamp,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct QueryTriplesInput {
    pub subject: Option<String>,
    pub predicate: Option<String>,
}

#[hdk_extern]
pub fn assert_triple(input: AssertTripleInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;
    consume_budget(&agent, COST_VALIDATE_TRIPLE)?;
    ontology::create_triple(
        &agent,
        input.subject,
        input.predicate,
        input.object,
        input.confidence,
    )
}

#[hdk_extern]
pub fn query_triples(input: QueryTriplesInput) -> ExternResult<Vec<TripleResult>> {
    let results = match (&input.subject, &input.predicate) {
        (Some(subject), _) => ontology::query_by_subject(subject)?,
        (_, Some(predicate)) => ontology::query_by_predicate(predicate)?,
        (None, None) => {
            return Err(wasm_error!(WasmErrorInner::Guest(
                "E_QUERY: must specify subject or predicate".into()
            )))
        }
    };
    Ok(results
        .into_iter()
        .map(|(hash, t)| TripleResult {
            hash,
            subject: t.subject,
            predicate: t.predicate,
            object: t.object,
            confidence: t.confidence,
            author: t.source,
            created_at: t.created_at,
        })
        .collect())
}

#[derive(Serialize, Deserialize, Debug)]
pub struct PredicateInfo {
    pub name: String,
    pub category: String,
}

/// Retrieve a triple's full Record (entry + signed action with provenance).
/// Used by substrate bridge validation to verify author pubkey and timestamp.
#[hdk_extern]
pub fn get_triple_record(hash: ActionHash) -> ExternResult<Option<Record>> {
    get(hash, GetOptions::default())
}

#[hdk_extern]
pub fn get_predicates(_: ()) -> ExternResult<Vec<PredicateInfo>> {
    let mut predicates = Vec::new();
    for p in ontology::BASE_PREDICATES {
        predicates.push(PredicateInfo {
            name: p.to_string(),
            category: "base".into(),
        });
    }
    for p in ontology::AI_ML_PREDICATES {
        predicates.push(PredicateInfo {
            name: p.to_string(),
            category: "ai_ml".into(),
        });
    }
    for p in ontology::KNOWLEDGE_PREDICATES {
        predicates.push(PredicateInfo {
            name: p.to_string(),
            category: "knowledge".into(),
        });
    }
    Ok(predicates)
}
