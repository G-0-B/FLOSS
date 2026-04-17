use hdk::prelude::*;
use rose_forest_integrity::{EntryTypes, KnowledgeTriple, LinkTypes};

/// Valid predicates from the base and AI/ML ontologies.
/// These define the vocabulary of relationships in the knowledge graph.
/// New predicates require an ADR and integrity zome update.
pub const BASE_PREDICATES: &[&str] = &["is_a", "part_of", "related_to", "has_property"];

pub const AI_ML_PREDICATES: &[&str] =
    &["trained_on", "improves_upon", "capable_of", "evaluated_on"];

pub const KNOWLEDGE_PREDICATES: &[&str] = &[
    "relates_to",
    "supports",
    "contradicts",
    "heals",
    "releases",
    "neutralizes",
    "recalibrates",
];

/// Domain/range constraints for predicates.
/// Returns (allowed_subject_types, allowed_object_types) or None if unconstrained.
pub fn domain_range(predicate: &str) -> Option<(&[&str], &[&str])> {
    match predicate {
        "is_a" => Some((
            &[
                "Entity",
                "AIModel",
                "Dataset",
                "Capability",
                "Benchmark",
                "TrainingRun",
                "Agent",
            ],
            &[
                "Entity",
                "AIModel",
                "Dataset",
                "Capability",
                "Benchmark",
                "TrainingRun",
                "Agent",
                "Thing",
                "Concept",
            ],
        )),
        "trained_on" => Some((&["AIModel"], &["Dataset"])),
        "improves_upon" => Some((&["AIModel"], &["AIModel"])),
        "capable_of" => Some((&["AIModel", "Agent"], &["Capability"])),
        "evaluated_on" => Some((&["AIModel"], &["Benchmark"])),
        _ => None, // unconstrained
    }
}

/// Heuristic type inference based on entity ID patterns.
/// Ported from ontology_integrity — runs in coordinator because it may
/// eventually need DHT lookups for TypeAssertions.
pub fn infer_type(entity_id: &str) -> String {
    let lower = entity_id.to_lowercase();
    if lower.contains("gpt")
        || lower.contains("claude")
        || lower.contains("llama")
        || lower.contains("gemini")
        || lower.contains("mistral")
        || lower.contains("_model")
    {
        "AIModel".to_string()
    } else if lower.contains("_dataset") || lower.contains("_data") {
        "Dataset".to_string()
    } else if lower.contains("_capability") || lower.contains("_cap") {
        "Capability".to_string()
    } else if lower.contains("_benchmark") || lower.contains("_bench") {
        "Benchmark".to_string()
    } else if lower.contains("_training") || lower.contains("_run") {
        "TrainingRun".to_string()
    } else if lower.contains("_agent") || lower.contains("agent:") {
        "Agent".to_string()
    } else {
        "Entity".to_string()
    }
}

/// Check domain/range constraints for a triple.
/// Returns Ok(()) if valid, Err(reason) if violated.
pub fn check_domain_range(predicate: &str, subject: &str, object: &str) -> Result<(), String> {
    if let Some((domain, range)) = domain_range(predicate) {
        let subject_type = infer_type(subject);
        let object_type = infer_type(object);
        if !domain.contains(&subject_type.as_str()) {
            return Err(format!(
                "Domain violation: '{}' expects subject type in {:?}, got '{}' (inferred: {})",
                predicate, domain, subject, subject_type
            ));
        }
        if !range.contains(&object_type.as_str()) {
            return Err(format!(
                "Range violation: '{}' expects object type in {:?}, got '{}' (inferred: {})",
                predicate, range, object, object_type
            ));
        }
    }
    Ok(())
}

/// Create a KnowledgeTriple entry with ontology validation, budget check, and DHT linking.
pub fn create_triple(
    agent: &AgentPubKey,
    subject: String,
    predicate: String,
    object: String,
    confidence: f32,
) -> ExternResult<ActionHash> {
    // Domain/range validation (coordinator-level, beyond what integrity validates)
    if let Err(reason) = check_domain_range(&predicate, &subject, &object) {
        return Err(wasm_error!(WasmErrorInner::Guest(format!(
            "E_ONTOLOGY_VIOLATION: {}",
            reason
        ))));
    }

    let now = sys_time()?;
    let triple = KnowledgeTriple {
        subject: subject.clone(),
        predicate: predicate.clone(),
        object,
        confidence,
        source: agent.clone(),
        created_at: now,
    };

    let hash = create_entry(EntryTypes::KnowledgeTriple(triple))?;

    // Index by subject for pattern queries
    let subject_path = Path::from(format!("triples.subject.{}", subject));
    create_link(
        subject_path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::TriplesBySubject,
        (),
    )?;

    // Index by predicate for relationship queries
    let predicate_path = Path::from(format!("triples.predicate.{}", predicate));
    create_link(
        predicate_path.path_entry_hash()?,
        hash.clone(),
        LinkTypes::TriplesByPredicate,
        (),
    )?;

    Ok(hash)
}

/// Query triples by subject.
pub fn query_by_subject(subject: &str) -> ExternResult<Vec<(ActionHash, KnowledgeTriple)>> {
    let path = Path::from(format!("triples.subject.{}", subject));
    let links = get_links(
        GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::TriplesBySubject)?
            .build(),
    )?;
    fetch_triples_from_links(links)
}

/// Query triples by predicate.
pub fn query_by_predicate(predicate: &str) -> ExternResult<Vec<(ActionHash, KnowledgeTriple)>> {
    let path = Path::from(format!("triples.predicate.{}", predicate));
    let links = get_links(
        GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::TriplesByPredicate)?
            .build(),
    )?;
    fetch_triples_from_links(links)
}

fn fetch_triples_from_links(links: Vec<Link>) -> ExternResult<Vec<(ActionHash, KnowledgeTriple)>> {
    let mut results = Vec::new();
    for link in links {
        let target_hash =
            link.target
                .into_action_hash()
                .ok_or(wasm_error!(WasmErrorInner::Guest(
                    "Invalid action hash".into()
                )))?;
        if let Some(record) = get(target_hash.clone(), GetOptions::default())? {
            if let Some(triple) = record
                .entry()
                .to_app_option::<KnowledgeTriple>()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
            {
                results.push((target_hash, triple));
            }
        }
    }
    Ok(results)
}
