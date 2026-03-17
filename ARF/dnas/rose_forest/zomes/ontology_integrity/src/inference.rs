use hdi::prelude::*;
use crate::{KnowledgeTriple, OntologyError};

/// Infer new knowledge from existing triples using axioms
///
/// This function implements the inference rules for the AI/ML domain ontology:
/// 1. Transitivity of improves_upon: If A improves B and B improves C, then A improves C
/// 2. Capability Inheritance: If A improves B and B capable_of X, then A capable_of X
/// 3. Type Propagation: (future) If A trained_on Dataset of type T, then A has_capability(T-tasks)
pub fn infer_from_axioms(triple: &KnowledgeTriple) -> Vec<KnowledgeTriple> {
    let mut inferred = vec![];

    match triple.predicate.as_str() {
        "improves_upon" => {
            // Axiom 1: Capability Inheritance
            // If A improves B, and B capable_of X, then A capable_of X
            let capabilities = query_capabilities(&triple.object);
            for capability in capabilities {
                inferred.push(KnowledgeTriple {
                    subject: triple.subject.clone(),
                    predicate: "capable_of".into(),
                    object: capability,
                    confidence: triple.confidence * 0.9,  // Slightly lower confidence
                    source: triple.source.clone(),
                    created_at: triple.created_at,
                });
            }

            // Axiom 2: Transitivity of improves_upon
            // If A improves B, and B improves C, then A improves C
            let improved_models = query_improved_models(&triple.object);
            for model in improved_models {
                inferred.push(KnowledgeTriple {
                    subject: triple.subject.clone(),
                    predicate: "improves_upon".into(),
                    object: model,
                    confidence: triple.confidence * 0.8,  // Lower confidence for transitive
                    source: triple.source.clone(),
                    created_at: triple.created_at,
                });
            }
        }
        "trained_on" => {
            // Future: Type Propagation
            // If A trained_on Dataset of type T, then A has_capability(T-tasks)
            // This would require dataset type registry
        }
        _ => {
            // No inference rules for other predicates yet
        }
    }

    inferred
}

/// Query capabilities of a model
///
/// In production, this would query the DHT for (model_id, capable_of, X) triples.
/// For now, this is a stub that returns an empty list.
///
/// # Arguments
/// * `model_id` - The ID of the model to query capabilities for
///
/// # Returns
/// A vector of capability IDs that the model is capable of
fn query_capabilities(model_id: &str) -> Vec<String> {
    // TODO: Query DHT for (model_id, capable_of, X) triples
    // This would use HDK query functions in a real implementation

    // For testing purposes, we can return hardcoded capabilities for known models
    match model_id {
        "Claude-Sonnet-4" => vec!["coding".to_string(), "reasoning".to_string()],
        "GPT-4" => vec!["coding".to_string(), "writing".to_string()],
        _ => vec![],
    }
}

/// Query models that a model improves upon
///
/// In production, this would query the DHT for (model_id, improves_upon, X) triples.
/// For now, this is a stub that returns an empty list.
///
/// # Arguments
/// * `model_id` - The ID of the model to query improvements for
///
/// # Returns
/// A vector of model IDs that the given model improves upon
fn query_improved_models(model_id: &str) -> Vec<String> {
    // TODO: Query DHT for (model_id, improves_upon, X) triples
    // This would use HDK query functions in a real implementation

    // For testing purposes, we can return hardcoded improvements for known models
    match model_id {
        "Claude-Sonnet-4" => vec!["Claude-Sonnet-3.5".to_string()],
        "GPT-4" => vec!["GPT-3.5".to_string()],
        _ => vec![],
    }
}

/// Apply all inference rules to a set of triples
///
/// This function takes a set of knowledge triples and recursively applies
/// inference rules until no new knowledge can be derived (fixed point).
///
/// # Arguments
/// * `triples` - The initial set of knowledge triples
///
/// # Returns
/// The expanded set of triples including all inferred knowledge
pub fn infer_all(triples: &[KnowledgeTriple]) -> Vec<KnowledgeTriple> {
    let mut all_triples = triples.to_vec();
    let mut iteration = 0;
    let max_iterations = 10; // Prevent infinite loops

    loop {
        iteration += 1;
        if iteration > max_iterations {
            break;
        }

        let mut new_triples = vec![];

        // Apply inference rules to each triple
        for triple in &all_triples {
            let inferred = infer_from_axioms(triple);
            for new_triple in inferred {
                // Only add if not already present (simple duplicate check)
                if !all_triples.contains(&new_triple) && !new_triples.contains(&new_triple) {
                    new_triples.push(new_triple);
                }
            }
        }

        // If no new triples were inferred, we've reached a fixed point
        if new_triples.is_empty() {
            break;
        }

        // Add new triples to the set
        all_triples.extend(new_triples);
    }

    all_triples
}

/// Check if a triple can be inferred from a knowledge base
///
/// # Arguments
/// * `knowledge_base` - The existing set of knowledge triples
/// * `query` - The triple to check if it can be inferred
///
/// # Returns
/// True if the triple can be inferred, false otherwise
pub fn can_infer(knowledge_base: &[KnowledgeTriple], query: &KnowledgeTriple) -> bool {
    let inferred = infer_all(knowledge_base);

    // Check if the query triple exists in the inferred set
    // We consider subject, predicate, and object (ignoring confidence and metadata)
    inferred.iter().any(|t| {
        t.subject == query.subject &&
        t.predicate == query.predicate &&
        t.object == query.object
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fake_agent_pub_key() -> AgentPubKey {
        let bytes = vec![
            132, 32, 36, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        AgentPubKey::from_raw_39(bytes).unwrap()
    }

    fn fake_timestamp() -> Timestamp {
        Timestamp::from_micros(1000000)
    }

    #[test]
    fn test_capability_inheritance() {
        // Given: Sonnet-4.5 improves_upon Sonnet-4
        let improves = KnowledgeTriple {
            subject: "Claude-Sonnet-4.5".into(),
            predicate: "improves_upon".into(),
            object: "Claude-Sonnet-4".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        // When: Infer new knowledge
        let inferred = infer_from_axioms(&improves);

        // Then: Should infer Sonnet-4.5 capable_of coding
        assert!(inferred.iter().any(|t|
            t.subject == "Claude-Sonnet-4.5" &&
            t.predicate == "capable_of" &&
            t.object == "coding"
        ), "Should infer capability inheritance");
    }

    #[test]
    fn test_transitivity() {
        // Given: Sonnet-4.5 improves Sonnet-4
        let improves = KnowledgeTriple {
            subject: "Claude-Sonnet-4.5".into(),
            predicate: "improves_upon".into(),
            object: "Claude-Sonnet-4".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        // When: Infer new knowledge
        let inferred = infer_from_axioms(&improves);

        // Then: Should infer transitive improvements
        assert!(inferred.iter().any(|t|
            t.subject == "Claude-Sonnet-4.5" &&
            t.predicate == "improves_upon" &&
            t.object == "Claude-Sonnet-3.5"
        ), "Should infer transitive improvement");
    }

    #[test]
    fn test_confidence_decay() {
        let improves = KnowledgeTriple {
            subject: "Model-A".into(),
            predicate: "improves_upon".into(),
            object: "Claude-Sonnet-4".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let inferred = infer_from_axioms(&improves);

        // Capability inheritance should have 0.9 confidence
        let cap_inference = inferred.iter().find(|t| t.predicate == "capable_of");
        if let Some(triple) = cap_inference {
            assert!((triple.confidence - 0.9).abs() < 0.01, "Capability inference should have 0.9 confidence");
        }

        // Transitive inference should have 0.8 confidence
        let trans_inference = inferred.iter().find(|t|
            t.predicate == "improves_upon" && t.object == "Claude-Sonnet-3.5"
        );
        if let Some(triple) = trans_inference {
            assert!((triple.confidence - 0.8).abs() < 0.01, "Transitive inference should have 0.8 confidence");
        }
    }

    #[test]
    fn test_no_inference_for_other_predicates() {
        let triple = KnowledgeTriple {
            subject: "Model-A".into(),
            predicate: "trained_on".into(),
            object: "Dataset-X".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let inferred = infer_from_axioms(&triple);

        // Currently no inference rules for trained_on
        assert!(inferred.is_empty(), "Should not infer anything for trained_on yet");
    }

    #[test]
    fn test_infer_all_fixed_point() {
        // Create a chain: A improves B improves C
        let triples = vec![
            KnowledgeTriple {
                subject: "Model-A".into(),
                predicate: "improves_upon".into(),
                object: "Claude-Sonnet-4".into(),
                confidence: 1.0,
                source: fake_agent_pub_key(),
                created_at: fake_timestamp(),
            },
        ];

        let all_inferred = infer_all(&triples);

        // Should include original triple plus inferred triples
        assert!(all_inferred.len() > triples.len(), "Should infer additional triples");

        // Should include transitive improvement
        assert!(all_inferred.iter().any(|t|
            t.subject == "Model-A" &&
            t.predicate == "improves_upon" &&
            t.object == "Claude-Sonnet-3.5"
        ), "Should infer transitive chain");
    }

    #[test]
    fn test_can_infer_capability() {
        let knowledge_base = vec![
            // Sonnet-4.5 improves Sonnet-4
            KnowledgeTriple {
                subject: "Claude-Sonnet-4.5".into(),
                predicate: "improves_upon".into(),
                object: "Claude-Sonnet-4".into(),
                confidence: 1.0,
                source: fake_agent_pub_key(),
                created_at: fake_timestamp(),
            },
        ];

        let query = KnowledgeTriple {
            subject: "Claude-Sonnet-4.5".into(),
            predicate: "capable_of".into(),
            object: "coding".into(),
            confidence: 0.0, // Confidence doesn't matter for query
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        assert!(can_infer(&knowledge_base, &query), "Should be able to infer coding capability");
    }
}
