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

/// A single atomic fact in the knowledge graph: subject-predicate-object.
///
/// Captures a relationship between two entities with mandatory provenance
/// tracking. This is the core unit of structured knowledge in the commons,
/// enabling symbolic-first validation against ontology rules.
///
/// See: docs/specs/knowledge-triple.spec.md
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeTriple {
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub source: AgentPubKey,
    pub created_at: Timestamp,
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
pub enum LinkTypes {
    AllNodes,
    Edge,
    TriplesBySubject,
    TriplesByPredicate,
}

#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    RoseNode(RoseNode),
    KnowledgeEdge(KnowledgeEdge),
    BudgetEntry(BudgetEntry),
    ThoughtCredential(ThoughtCredential),
    KnowledgeTriple(KnowledgeTriple),
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
        // ADR-15 R1: bind every identity-bearing entry to the action's author.
        // `action.author` (hdi 0.7.1) is the author-of-record; an entry whose own
        // identity field disagrees with it must be rejected. Create and Update carry
        // distinct action types (Create / Update), so each arm extracts the author
        // from its own action field rather than sharing one binding.
        FlatOp::StoreEntry(store) => match store {
            OpEntry::CreateEntry { app_entry, action } => {
                validate_app_entry(app_entry, &action.author)
            }
            OpEntry::UpdateEntry { app_entry, action, .. } => {
                validate_app_entry(app_entry, &action.author)
            }
            _ => Ok(ValidateCallbackResult::Valid),
        },
        _ => Ok(ValidateCallbackResult::Valid),
    }
}

/// ADR-15: dispatch an entry to its per-type validator, passing the action author
/// so identity-bearing entries can be bound to their author-of-record.
fn validate_app_entry(
    app_entry: EntryTypes,
    author: &AgentPubKey,
) -> ExternResult<ValidateCallbackResult> {
    match app_entry {
        EntryTypes::RoseNode(node) => validate_rose_node(&node),
        EntryTypes::KnowledgeEdge(edge) => validate_knowledge_edge(&edge),
        EntryTypes::BudgetEntry(budget) => validate_budget_entry(&budget, author),
        EntryTypes::ThoughtCredential(credential) => {
            validate_thought_credential(&credential, author)
        }
        EntryTypes::KnowledgeTriple(triple) => validate_knowledge_triple(&triple, author),
    }
}

fn validate_thought_credential(
    credential: &ThoughtCredential,
    author: &AgentPubKey,
) -> ExternResult<ValidateCallbackResult> {
    // ADR-15 R3: provenance is the verifiable author-of-record, not a free-form claim.
    if &credential.provenance != author {
        return Ok(ValidateCallbackResult::Invalid(
            "E_THOUGHT_PROVENANCE: provenance must equal the action author".into(),
        ));
    }
    let dim = credential.content.len();
    if dim < 32 || dim > 4096 {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_THOUGHT_CONTENT_DIM: {} out of [32,4096]",
            dim
        )));
    }
    if !(-1..=1).contains(&credential.connotation) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_CONNOTATION: {} out of [-1,1]",
            credential.connotation
        )));
    }
    if !(0.0..=1.0).contains(&credential.impact) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_IMPACT: {} out of [0,1]",
            credential.impact
        )));
    }
    // NOTE (ADR-15 R5, deferred to PR-B): `connotation` remains integer ternary (i8, -1..=1)
    // here. Migration to the analog f32 [-1.0, +1.0] model (ADR-10 v2.0 / ADR-13) is a breaking
    // data-model change with migration impact on existing data + ontology tests, handled separately.
    Ok(ValidateCallbackResult::Valid)
}

fn validate_rose_node(node: &RoseNode) -> ExternResult<ValidateCallbackResult> {
    const VALID_LICENSES: &[&str] = &["MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0", "CC-BY-4.0"];
    if !VALID_LICENSES.contains(&node.license.as_str()) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_LICENSE: '{}' not allowed",
            node.license
        )));
    }
    let dim = node.embedding.len();
    if dim < 32 || dim > 4096 {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_EMBED_DIM: {} out of [32,4096]",
            dim
        )));
    }
    match (
        node.metadata.get("model_id"),
        node.metadata.get("model_card_hash"),
    ) {
        (Some(_), Some(hash)) if hash.starts_with("sha256:") => Ok(ValidateCallbackResult::Valid),
        _ => Ok(ValidateCallbackResult::Invalid(
            "E_MODEL_CARD_MISSING".into(),
        )),
    }
}

fn validate_knowledge_triple(
    triple: &KnowledgeTriple,
    author: &AgentPubKey,
) -> ExternResult<ValidateCallbackResult> {
    // ADR-15 R4: the triple's `source` is provenance and must equal the action author.
    if &triple.source != author {
        return Ok(ValidateCallbackResult::Invalid(
            "E_TRIPLE_SOURCE: source must equal the action author".into(),
        ));
    }
    if triple.subject.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_TRIPLE_SUBJECT: subject must not be empty".into(),
        ));
    }
    if triple.predicate.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_TRIPLE_PREDICATE: predicate must not be empty".into(),
        ));
    }
    if triple.object.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_TRIPLE_OBJECT: object must not be empty".into(),
        ));
    }
    // Signed gradient: negative = movement away from truth, positive = toward truth.
    // Aligns with ternary logic (-1/0/+1) and Yumeichan connotation framework.
    if !(-1.0..=1.0).contains(&triple.confidence) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_TRIPLE_CONFIDENCE: {} out of [-1,1]",
            triple.confidence
        )));
    }
    // Predicate must be from a registered ontology namespace.
    // Base predicates + AI/ML predicates from the ontology_integrity module.
    const VALID_PREDICATES: &[&str] = &[
        "is_a",
        "part_of",
        "related_to",
        "has_property",
        "trained_on",
        "improves_upon",
        "capable_of",
        "evaluated_on",
        // Knowledge graph relationship predicates (same as KnowledgeEdge)
        "relates_to",
        "supports",
        "contradicts",
        "heals",
        "releases",
        "neutralizes",
        "recalibrates",
    ];
    if !VALID_PREDICATES.contains(&triple.predicate.as_str()) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_TRIPLE_PREDICATE_UNKNOWN: '{}' not in registered ontology",
            triple.predicate
        )));
    }
    Ok(ValidateCallbackResult::Valid)
}

fn validate_knowledge_edge(edge: &KnowledgeEdge) -> ExternResult<ValidateCallbackResult> {
    // Signed gradient: same range as KnowledgeTriple confidence.
    if !(-1.0..=1.0).contains(&edge.confidence) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_CONFIDENCE: {} out of [-1,1]",
            edge.confidence
        )));
    }
    // New relationship types reflecting the manifesto
    const VALID_RELATIONSHIPS: &[&str] = &[
        "relates_to",
        "supports",
        "contradicts",
        "heals",
        "releases",
        "neutralizes",
        "recalibrates",
    ];
    if !VALID_RELATIONSHIPS.contains(&edge.relationship.as_str()) {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_RELATIONSHIP: '{}' not allowed",
            edge.relationship
        )));
    }
    Ok(ValidateCallbackResult::Valid)
}

/// ADR-15 R2: `BudgetEntry` was previously accepted unconditionally (`Ok(Valid)`), letting any
/// agent mint a budget naming any other agent. Bind it to the author and reject negative balances.
fn validate_budget_entry(
    budget: &BudgetEntry,
    author: &AgentPubKey,
) -> ExternResult<ValidateCallbackResult> {
    if &budget.agent != author {
        return Ok(ValidateCallbackResult::Invalid(
            "E_BUDGET_AUTHOR: agent must equal the action author".into(),
        ));
    }
    if budget.remaining_ru < 0.0 {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_BUDGET_RU: {} must be >= 0.0",
            budget.remaining_ru
        )));
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
    pub content: Vec<f32>,           // SemanticVector
    pub connotation: i8,             // TernaryScore: -1, 0, 1
    pub provenance: AgentPubKey,     // AgentSignature
    pub resonance: Vec<AgentPubKey>, // AgentEndorsement
    pub impact: f32,                 // WisdomMetric
}

#[cfg(test)]
mod tests {
    //! ADR-15 R1–R4 author/provenance-binding tests (unit level).
    //!
    //! These exercise the pure validator helpers directly (no `Op` construction needed).
    //! Cross-agent rejection at the conductor level is covered by the Tryorama test
    //! `ARF/tests/tryorama/provenance_validation.test.ts`.
    use super::*;

    /// Two distinct, deterministic agent keys. Pattern mirrors `consent_integrity` tests.
    fn agent(seed: u8) -> AgentPubKey {
        AgentPubKey::from_raw_36(vec![seed; 36])
    }

    fn ts() -> Timestamp {
        Timestamp::from_micros(1_000_000)
    }

    #[test]
    fn budget_rejects_author_mismatch() {
        let b = BudgetEntry { agent: agent(1), remaining_ru: 10.0, window_start: ts() };
        assert!(matches!(
            validate_budget_entry(&b, &agent(2)).unwrap(),
            ValidateCallbackResult::Invalid(_)
        ));
    }

    #[test]
    fn budget_accepts_self_authored() {
        let b = BudgetEntry { agent: agent(1), remaining_ru: 10.0, window_start: ts() };
        assert_eq!(
            validate_budget_entry(&b, &agent(1)).unwrap(),
            ValidateCallbackResult::Valid
        );
    }

    #[test]
    fn budget_rejects_negative_balance() {
        let b = BudgetEntry { agent: agent(1), remaining_ru: -1.0, window_start: ts() };
        assert!(matches!(
            validate_budget_entry(&b, &agent(1)).unwrap(),
            ValidateCallbackResult::Invalid(_)
        ));
    }

    #[test]
    fn thought_rejects_provenance_mismatch() {
        let c = ThoughtCredential {
            content: vec![0.0; 64],
            connotation: 0,
            provenance: agent(1),
            resonance: vec![],
            impact: 0.5,
        };
        assert!(matches!(
            validate_thought_credential(&c, &agent(2)).unwrap(),
            ValidateCallbackResult::Invalid(_)
        ));
    }

    #[test]
    fn thought_accepts_self_authored() {
        let c = ThoughtCredential {
            content: vec![0.0; 64],
            connotation: 0,
            provenance: agent(1),
            resonance: vec![],
            impact: 0.5,
        };
        assert_eq!(
            validate_thought_credential(&c, &agent(1)).unwrap(),
            ValidateCallbackResult::Valid
        );
    }

    #[test]
    fn triple_rejects_source_mismatch() {
        let t = KnowledgeTriple {
            subject: "a".into(),
            predicate: "is_a".into(),
            object: "b".into(),
            confidence: 0.5,
            source: agent(1),
            created_at: ts(),
        };
        assert!(matches!(
            validate_knowledge_triple(&t, &agent(2)).unwrap(),
            ValidateCallbackResult::Invalid(_)
        ));
    }

    #[test]
    fn triple_accepts_self_authored() {
        let t = KnowledgeTriple {
            subject: "a".into(),
            predicate: "is_a".into(),
            object: "b".into(),
            confidence: 0.5,
            source: agent(1),
            created_at: ts(),
        };
        assert_eq!(
            validate_knowledge_triple(&t, &agent(1)).unwrap(),
            ValidateCallbackResult::Valid
        );
    }
}
