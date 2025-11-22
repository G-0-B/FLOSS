use hdk::prelude::*;
use serde::{Deserialize, Serialize};
use ontology_integrity::{KnowledgeTriple, validate_triple};
use sha2::{Sha256, Digest};
use rose_forest_integrity::BudgetEntry;

mod budget;
use budget::{consume_budget, get_budget_state, BudgetState};
use budget::{COST_TRANSMIT_UNDERSTANDING, COST_RECALL_UNDERSTANDINGS, COST_COMPOSE_MEMORIES, COST_VALIDATE_TRIPLE};

/// Entry types for the memory coordinator zome
#[hdk_entry_defs]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    Understanding(Understanding),
    ADR(ADR),
    MemoryComposition(MemoryComposition),
    KnowledgeTriple(KnowledgeTriple),
    BudgetEntry(BudgetEntry),
}

/// Link types for memory queries
#[hdk_link_types]
pub enum LinkTypes {
    AgentToUnderstanding,
    TripleToUnderstanding,
    ADRToUnderstanding,
    AgentBudget,
    /// Link from AD4M perspective to understanding
    PerspectiveToUnderstanding,
    /// Link from semantic context to understanding
    SemanticContextToUnderstanding,
}

/// Represents a moment of coherent understanding transmitted by an agent.
///
/// This is the atomic unit of memory in the FLOSSI0ULLK coordination system.
/// It contains the content of the understanding, its context, and a structured
/// `KnowledgeTriple` that has been extracted and validated against the shared
/// ontology.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Understanding {
    /// Content of the understanding
    pub content: String,

    /// Optional context
    pub context: Option<String>,

    /// Extracted knowledge triple
    pub triple: KnowledgeTriple,

    /// When this was created
    pub created_at: Timestamp,

    /// Agent who transmitted this
    pub agent: AgentPubKey,

    /// Content hash for deduplication
    pub content_hash: String,

    // === AD4M SEMANTIC LAYER ===
    /// Links to AD4M perspectives for semantic interoperability
    pub perspectives: Vec<PerspectiveHash>,

    /// Shared semantic context for interpretation
    pub semantic_context: Option<SemanticContext>,

    /// Which AD4M language this understanding uses
    pub language_address: Option<LanguageAddress>,
}

/// AD4M Perspective Hash
///
/// References an AD4M Perspective (agent's semantic view)
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct PerspectiveHash {
    /// Hash/ID of the perspective
    pub hash: String,

    /// Optional human-readable name
    pub name: Option<String>,
}

/// AD4M Language Address
///
/// Points to an AD4M Language for semantic interoperability
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct LanguageAddress {
    /// DNA hash of the AD4M language
    pub dna_hash: String,

    /// Specific expression hash within that language
    pub expression_hash: String,
}

/// Semantic Context for AD4M integration
///
/// Defines how to interpret metadata and establish shared meaning
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct SemanticContext {
    /// Schema definition (RDF, JSON-LD, SHACL, etc.)
    pub schema: String,

    /// References to shared ontologies
    pub ontology_refs: Vec<String>,

    /// Interpretation rules (how to parse metadata)
    pub interpretation_rules: Vec<InterpretationRule>,
}

/// Rule for interpreting semantic data
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct InterpretationRule {
    /// Rule identifier
    pub id: String,

    /// Rule type (validation, transformation, inference)
    pub rule_type: String,

    /// Rule content (executable or declarative)
    pub content: String,
}

/// Represents an Architecture Decision Record (ADR).
///
/// ADRs are a key component of "Specification-Driven Development" (SDD),
/// providing a verifiable and auditable history of the system's design
/// decisions.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ADR {
    /// ADR identifier
    pub id: String,

    /// Title/summary
    pub title: String,

    /// Full content
    pub content: String,

    /// Status (proposed, accepted, rejected, superseded)
    pub status: String,

    /// When decided
    pub decided_at: Timestamp,

    /// Who decided
    pub decided_by: AgentPubKey,
}

/// Records the event of composing memories from multiple agents.
///
/// This entry provides a verifiable record of "Federated Reasoning" in action,
/// capturing which agents' memories were composed, what strategy was used, and
_summary_of_the_outcome />
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct MemoryComposition {
    /// Agents involved in composition
    pub agents: Vec<AgentPubKey>,

    /// Composition strategy used
    pub strategy: String,

    /// Statistics from composition
    pub stats: CompositionStats,

    /// When composed
    pub composed_at: Timestamp,
}

#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct CompositionStats {
    pub total_understandings: u32,
    pub new_understandings: u32,
    pub duplicate_skipped: u32,
}

/// Input for transmitting an understanding
#[derive(Serialize, Deserialize, Debug)]
pub struct UnderstandingInput {
    pub content: String,
    pub context: Option<String>,

    // AD4M semantic layer fields
    pub perspectives: Option<Vec<PerspectiveHash>>,
    pub semantic_context: Option<SemanticContext>,
    pub language_address: Option<LanguageAddress>,
}

/// Query for recalling understandings
#[derive(Serialize, Deserialize, Debug)]
pub struct RecallQuery {
    pub agent: Option<AgentPubKey>,
    pub content_contains: Option<String>,
    pub after_timestamp: Option<Timestamp>,
    pub limit: Option<usize>,
}

/// Statistics about validation
#[derive(Serialize, Deserialize, Debug)]
pub struct ValidationStats {
    pub total_understandings: usize,
    pub valid_triples: usize,
    pub invalid_triples: usize,
}

/// Transmits a new `Understanding` to the DHT.
///
/// This is the core "write" operation for an agent's memory. It performs several
/// key steps to ensure the integrity and verifiability of the knowledge:
/// 1.  Checks and consumes the agent's computational budget.
/// 2.  Extracts a structured `KnowledgeTriple` from the unstructured content.
/// 3.  Validates the triple against the shared ontology.
/// 4.  Creates and stores the `Understanding` entry.
/// 5.  Creates links to enable efficient querying by agent and by semantic triple.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn transmit_understanding(input: UnderstandingInput) -> ExternResult<ActionHash> {
    // Get agent info early for budget check
    let agent_info = agent_info()?;
    let agent_key = agent_info.agent_latest_pubkey;

    // Check and consume budget (transmit + validate costs)
    let total_cost = COST_TRANSMIT_UNDERSTANDING + COST_VALIDATE_TRIPLE;
    consume_budget(&agent_key, total_cost)?;

    // Extract triple from content
    let triple = extract_triple(&input.content)?;

    // Validate triple against ontology
    validate_triple(&triple)
        .map_err(|e| wasm_error!(WasmErrorInner::Guest(format!("Ontology validation failed: {:?}", e))))?;

    // Create Understanding entry
    let understanding = Understanding {
        content: input.content.clone(),
        context: input.context,
        triple: triple.clone(),
        created_at: sys_time()?,
        agent: agent_key.clone(),
        content_hash: hash_content(&input.content),
        // AD4M semantic layer
        perspectives: input.perspectives.unwrap_or_default(),
        semantic_context: input.semantic_context,
        language_address: input.language_address,
    };

    // Commit Understanding to DHT
    let understanding_hash = create_entry(EntryTypes::Understanding(understanding.clone()))?;

    // Create link from agent to understanding (for recall by agent)
    create_link(
        agent_key.clone(),
        understanding_hash.clone(),
        LinkTypes::AgentToUnderstanding,
        ()
    )?;

    // Create the triple entry
    let triple_hash = create_entry(EntryTypes::KnowledgeTriple(triple.clone()))?;

    // Link triple to understanding (for semantic queries)
    create_link(
        triple_hash,
        understanding_hash.clone(),
        LinkTypes::TripleToUnderstanding,
        ()
    )?;

    // Create links from AD4M perspectives to understanding (if provided)
    for perspective in &understanding.perspectives {
        // Use Path as anchor for perspective hash
        let perspective_anchor = Path::from(format!("perspective:{}", perspective.hash));
        perspective_anchor.ensure()?;

        create_link(
            perspective_anchor.path_entry_hash()?,
            understanding_hash.clone(),
            LinkTypes::PerspectiveToUnderstanding,
            ()
        )?;
    }

    // Create link from semantic context to understanding (if provided)
    if let Some(ref context) = understanding.semantic_context {
        let context_anchor = Path::from(format!("context:{}", context.schema));
        context_anchor.ensure()?;

        create_link(
            context_anchor.path_entry_hash()?,
            understanding_hash.clone(),
            LinkTypes::SemanticContextToUnderstanding,
            ()
        )?;
    }

    debug!("Transmitted understanding with triple: subject={}, predicate={}, object={}, perspectives={}, semantic_context={}",
           triple.subject, triple.predicate, triple.object,
           understanding.perspectives.len(),
           understanding.semantic_context.is_some());

    Ok(understanding_hash)
}

/// Recalls `Understanding`s from the DHT based on a set of query criteria.
///
/// This is the core "read" operation for an agent's memory. It allows for the
/// retrieval of past knowledge by agent, content, or time. The function also
/// consumes the agent's computational budget based on the number of results
/// returned, creating an economic incentive for precise queries.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn recall_understandings(query: RecallQuery) -> ExternResult<Vec<Understanding>> {
    // Get agent info for budget check
    let current_agent = agent_info()?.agent_latest_pubkey;

    let mut results = vec![];

    // Query by agent
    if let Some(agent) = query.agent {
        let links = get_links(
            GetLinksInputBuilder::try_new(agent, LinkTypes::AgentToUnderstanding)?
                .build()
        )?;

        for link in links {
            if let Some(understanding) = get_understanding(link.target.into())? {
                // Apply filters
                if matches_query(&understanding, &query) {
                    results.push(understanding);
                }
            }
        }
    } else {
        // If no agent specified, search the current agent's understandings
        let agent_info = agent_info()?;
        let links = get_links(
            GetLinksInputBuilder::try_new(agent_info.agent_latest_pubkey, LinkTypes::AgentToUnderstanding)?
                .build()
        )?;

        for link in links {
            if let Some(understanding) = get_understanding(link.target.into())? {
                if matches_query(&understanding, &query) {
                    results.push(understanding);
                }
            }
        }
    }

    // Limit results
    if let Some(limit) = query.limit {
        results.truncate(limit);
    }

    // Charge budget based on number of results (0.1 RU per result)
    let recall_cost = COST_RECALL_UNDERSTANDINGS * results.len() as f32;
    consume_budget(&current_agent, recall_cost)?;

    Ok(results)
}

/// Composes the memories of two agents.
///
/// This function implements the "Federated Reasoning" principle by merging the
/// `Understanding`s from another agent into the current agent's memory. It
/// deduplicates the knowledge based on content hashes and records the
/// composition event in a `MemoryComposition` entry for auditability.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn compose_memories(other_agent: AgentPubKey) -> ExternResult<MemoryComposition> {
    let agent_info = agent_info()?;
    let my_agent = agent_info.agent_latest_pubkey;

    // Check and consume budget for composition
    consume_budget(&my_agent, COST_COMPOSE_MEMORIES)?;

    // Get my understandings
    let my_understandings = recall_understandings(RecallQuery {
        agent: Some(my_agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Get other agent's understandings
    let other_understandings = recall_understandings(RecallQuery {
        agent: Some(other_agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Build set of my content hashes for quick lookup
    let my_hashes: std::collections::HashSet<String> = my_understandings
        .iter()
        .map(|u| u.content_hash.clone())
        .collect();

    // Merge (simple: add non-duplicates)
    let mut new_count = 0;
    let mut dup_count = 0;

    for understanding in other_understandings.iter() {
        // Check if duplicate
        if my_hashes.contains(&understanding.content_hash) {
            dup_count += 1;
        } else {
            // Import understanding (create entry for current agent)
            let new_understanding = Understanding {
                content: understanding.content.clone(),
                context: understanding.context.clone(),
                triple: understanding.triple.clone(),
                created_at: sys_time()?,
                agent: my_agent.clone(),
                content_hash: understanding.content_hash.clone(),
                // Preserve AD4M semantic layer
                perspectives: understanding.perspectives.clone(),
                semantic_context: understanding.semantic_context.clone(),
                language_address: understanding.language_address.clone(),
            };

            let hash = create_entry(EntryTypes::Understanding(new_understanding))?;

            // Create link from current agent to understanding
            create_link(
                my_agent.clone(),
                hash,
                LinkTypes::AgentToUnderstanding,
                ()
            )?;

            new_count += 1;
        }
    }

    // Create composition entry
    let composition = MemoryComposition {
        agents: vec![my_agent.clone(), other_agent],
        strategy: "merge".to_string(),
        stats: CompositionStats {
            total_understandings: (my_understandings.len() + new_count) as u32,
            new_understandings: new_count as u32,
            duplicate_skipped: dup_count as u32,
        },
        composed_at: sys_time()?,
    };

    create_entry(EntryTypes::MemoryComposition(composition.clone()))?;

    debug!("Composed memories: {} new, {} duplicates skipped", new_count, dup_count);

    Ok(composition)
}

/// Retrieves the current computational budget status for the calling agent.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn budget_status(_: ()) -> ExternResult<BudgetState> {
    let agent_key = agent_info()?.agent_latest_pubkey;
    get_budget_state(&agent_key)
}

/// Retrieves statistics on the validation of knowledge triples.
///
/// This function provides insight into the quality and coherence of the knowledge
/// being transmitted into the system, aligning with the "Light" principle.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn get_validation_stats(_: ()) -> ExternResult<ValidationStats> {
    let agent_info = agent_info()?;

    // Get all understandings for current agent
    let understandings = recall_understandings(RecallQuery {
        agent: Some(agent_info.agent_latest_pubkey),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    let total = understandings.len();
    let valid = understandings.len(); // All stored understandings passed validation

    Ok(ValidationStats {
        total_understandings: total,
        valid_triples: valid,
        invalid_triples: 0,
    })
}

/// Creates a new Architecture Decision Record (ADR) in the DHT.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn create_adr(adr: ADR) -> ExternResult<ActionHash> {
    let hash = create_entry(EntryTypes::ADR(adr))?;
    Ok(hash)
}

/// Retrieves an ADR by its `ActionHash`.
///
/// TODO: Needs refinement by a human expert.
#[hdk_extern]
pub fn get_adr(hash: ActionHash) -> ExternResult<Option<ADR>> {
    let record = get(hash, GetOptions::default())?;
    match record {
        Some(rec) => {
            let adr: Option<ADR> = rec.entry().to_app_option()?;
            Ok(adr)
        }
        None => Ok(None),
    }
}

// ===== AD4M Semantic Query Functions =====

/// Query understandings by AD4M perspective
///
/// Enables semantic interoperability by finding all understandings
/// that share a common perspective (semantic view)
#[hdk_extern]
pub fn query_by_perspective(perspective_hash: String) -> ExternResult<Vec<Understanding>> {
    let agent = agent_info()?.agent_latest_pubkey;

    // Use Path anchor for perspective
    let perspective_anchor = Path::from(format!("perspective:{}", perspective_hash));

    // Get links from perspective to understandings
    let links = get_links(
        GetLinksInputBuilder::try_new(
            perspective_anchor.path_entry_hash()?,
            LinkTypes::PerspectiveToUnderstanding
        )?.build()
    )?;

    let mut understandings = Vec::new();

    for link in links {
        if let Some(understanding) = get_understanding(link.target.into())? {
            understandings.push(understanding);
        }
    }

    // Charge budget based on results (0.1 RU per result)
    let cost = COST_RECALL_UNDERSTANDINGS * understandings.len() as f32;
    consume_budget(&agent, cost)?;

    Ok(understandings)
}

/// Query understandings by semantic context
///
/// Find understandings that share a semantic schema or ontology
#[hdk_extern]
pub fn query_by_semantic_context(schema: String) -> ExternResult<Vec<Understanding>> {
    let agent = agent_info()?.agent_latest_pubkey;

    // Use Path anchor for semantic context
    let context_anchor = Path::from(format!("context:{}", schema));

    // Get links from context to understandings
    let links = get_links(
        GetLinksInputBuilder::try_new(
            context_anchor.path_entry_hash()?,
            LinkTypes::SemanticContextToUnderstanding
        )?.build()
    )?;

    let mut understandings = Vec::new();

    for link in links {
        if let Some(understanding) = get_understanding(link.target.into())? {
            understandings.push(understanding);
        }
    }

    // Charge budget
    let cost = COST_RECALL_UNDERSTANDINGS * understandings.len() as f32;
    consume_budget(&agent, cost)?;

    Ok(understandings)
}

/// Query understandings by AD4M language
///
/// Find understandings expressed in a specific AD4M language
#[hdk_extern]
pub fn query_by_language(language_dna_hash: String) -> ExternResult<Vec<Understanding>> {
    let agent = agent_info()?.agent_latest_pubkey;

    // Get all understandings for current agent and filter by language
    let all_understandings = recall_understandings(RecallQuery {
        agent: Some(agent.clone()),
        content_contains: None,
        after_timestamp: None,
        limit: None,
    })?;

    // Filter by language address
    let filtered: Vec<Understanding> = all_understandings
        .into_iter()
        .filter(|u| {
            if let Some(ref lang) = u.language_address {
                lang.dna_hash == language_dna_hash
            } else {
                false
            }
        })
        .collect();

    // Note: Budget already charged by recall_understandings

    Ok(filtered)
}

/// Publish understanding with AD4M perspective
///
/// Convenience function that combines transmit_understanding with perspective linking
/// as described in the AD4M-hREA integration spec
#[hdk_extern]
pub fn publish_with_perspective(input: PublishWithPerspectiveInput) -> ExternResult<ActionHash> {
    // Create the understanding with AD4M fields
    let understanding_input = UnderstandingInput {
        content: input.content,
        context: input.context,
        perspectives: Some(vec![input.perspective]),
        semantic_context: input.semantic_context,
        language_address: input.language_address,
    };

    // Transmit the understanding (this creates all the links)
    transmit_understanding(understanding_input)
}

/// Input for publishing with perspective
#[derive(Serialize, Deserialize, Debug)]
pub struct PublishWithPerspectiveInput {
    pub content: String,
    pub context: Option<String>,
    pub perspective: PerspectiveHash,
    pub semantic_context: Option<SemanticContext>,
    pub language_address: Option<LanguageAddress>,
}

// ===== Helper Functions =====

/// Get an understanding by hash
fn get_understanding(hash: ActionHash) -> ExternResult<Option<Understanding>> {
    let record = get(hash, GetOptions::default())?;
    match record {
        Some(rec) => {
            let understanding: Option<Understanding> = rec.entry().to_app_option()?;
            Ok(understanding)
        }
        None => Ok(None),
    }
}

/// Check if an understanding matches the query criteria
fn matches_query(understanding: &Understanding, query: &RecallQuery) -> bool {
    // Filter by content
    if let Some(ref contains) = query.content_contains {
        if !understanding.content.to_lowercase().contains(&contains.to_lowercase()) {
            return false;
        }
    }

    // Filter by timestamp
    if let Some(after) = query.after_timestamp {
        if understanding.created_at < after {
            return false;
        }
    }

    true
}

/// Extract a knowledge triple from content using pattern matching
///
/// This is a simplified version that uses regex patterns.
/// In production, this could use LLM-based extraction.
fn extract_triple(content: &str) -> ExternResult<KnowledgeTriple> {
    let agent_info = agent_info()?;
    let agent_key = agent_info.agent_latest_pubkey;

    // Pattern 1: "X is a Y" or "X is an Y"
    if let Some((subject, object)) = extract_is_a_pattern(content) {
        return Ok(KnowledgeTriple {
            subject,
            predicate: "is_a".to_string(),
            object,
            confidence: 1.0,
            source: agent_key,
            created_at: sys_time()?,
        });
    }

    // Pattern 2: "X improves Y" or "X improves upon Y"
    if let Some((subject, object)) = extract_improves_pattern(content) {
        return Ok(KnowledgeTriple {
            subject,
            predicate: "improves_upon".to_string(),
            object,
            confidence: 0.9,
            source: agent_key,
            created_at: sys_time()?,
        });
    }

    // Pattern 3: "X can do Y" / "X is capable of Y"
    if let Some((subject, object)) = extract_capable_pattern(content) {
        return Ok(KnowledgeTriple {
            subject,
            predicate: "capable_of".to_string(),
            object,
            confidence: 0.8,
            source: agent_key,
            created_at: sys_time()?,
        });
    }

    // Default: treat as statement
    // Subject = agent, predicate = stated, object = content hash
    Ok(KnowledgeTriple {
        subject: format!("agent_{}", &agent_key.to_string()[..8]),
        predicate: "stated".to_string(),
        object: format!("content_{}", hash_content(content)),
        confidence: 1.0,
        source: agent_key,
        created_at: sys_time()?,
    })
}

/// Extract "X is a Y" pattern
fn extract_is_a_pattern(content: &str) -> Option<(String, String)> {
    // Simple pattern matching for "X is a/an Y"
    let words: Vec<&str> = content.split_whitespace().collect();

    for i in 0..words.len().saturating_sub(3) {
        if words[i + 1] == "is" && (words[i + 2] == "a" || words[i + 2] == "an") {
            let subject = words[i].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');
            let object = words[i + 3].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');

            if !subject.is_empty() && !object.is_empty() {
                return Some((subject.to_string(), object.to_string()));
            }
        }
    }

    None
}

/// Extract "X improves Y" pattern
fn extract_improves_pattern(content: &str) -> Option<(String, String)> {
    let words: Vec<&str> = content.split_whitespace().collect();

    for i in 0..words.len().saturating_sub(2) {
        if words[i + 1] == "improves" {
            let subject = words[i].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');

            // Check if next word is "upon"
            let obj_idx = if i + 2 < words.len() && words[i + 2] == "upon" {
                i + 3
            } else {
                i + 2
            };

            if obj_idx < words.len() {
                let object = words[obj_idx].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');
                if !subject.is_empty() && !object.is_empty() {
                    return Some((subject.to_string(), object.to_string()));
                }
            }
        }
    }

    None
}

/// Extract "X capable of Y" pattern
fn extract_capable_pattern(content: &str) -> Option<(String, String)> {
    let words: Vec<&str> = content.split_whitespace().collect();

    for i in 0..words.len().saturating_sub(3) {
        if words[i + 1] == "is" && words[i + 2] == "capable" && i + 3 < words.len() && words[i + 3] == "of" {
            let subject = words[i].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');

            if i + 4 < words.len() {
                let object = words[i + 4].trim_matches(|c: char| !c.is_alphanumeric() && c != '-');
                if !subject.is_empty() && !object.is_empty() {
                    return Some((subject.to_string(), object.to_string()));
                }
            }
        }
    }

    None
}

/// Hash content using SHA-256
fn hash_content(content: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(content.as_bytes());
    format!("{:x}", hasher.finalize())[..16].to_string()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_is_a_pattern() {
        let result = extract_is_a_pattern("GPT-4 is a LLM");
        assert!(result.is_some());
        let (subject, object) = result.unwrap();
        assert_eq!(subject, "GPT-4");
        assert_eq!(object, "LLM");
    }

    #[test]
    fn test_extract_improves_pattern() {
        let result = extract_improves_pattern("Claude-4.5 improves Claude-4");
        assert!(result.is_some());
        let (subject, object) = result.unwrap();
        assert_eq!(subject, "Claude-4.5");
        assert_eq!(object, "Claude-4");
    }

    #[test]
    fn test_hash_content() {
        let hash1 = hash_content("test content");
        let hash2 = hash_content("test content");
        let hash3 = hash_content("different content");

        assert_eq!(hash1, hash2);
        assert_ne!(hash1, hash3);
        assert_eq!(hash1.len(), 16);
    }
}
