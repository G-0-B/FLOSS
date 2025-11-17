use hdi::prelude::*;
use serde::{Deserialize, Serialize};
use thiserror::Error;

pub mod inference;

/// Defines the set of errors that can occur during ontology validation.
///
/// This enum provides a structured way to report errors when a `KnowledgeTriple`
/// violates the constraints of the ontology, such as type mismatches or unknown
/// relations.
///
/// TODO: Needs refinement by a human expert.
#[derive(Error, Debug, Clone, Serialize, Deserialize)]
pub enum OntologyError {
    #[error("Type mismatch: expected {expected}, got {actual}")]
    TypeMismatch { expected: String, actual: String },

    #[error("Unknown type: {0}")]
    UnknownType(String),

    #[error("Unknown relation: {0}")]
    UnknownRelation(String),

    #[error("Domain constraint violated: {relation} requires subject type {required}, got {actual}")]
    DomainViolation {
        relation: String,
        required: String,
        actual: String,
    },

    #[error("Range constraint violated: {relation} requires object type {required}, got {actual}")]
    RangeViolation {
        relation: String,
        required: String,
        actual: String,
    },

    #[error("Validation error: {0}")]
    ValidationError(String),
}

/// Represents a type definition in the ontology.
///
/// Each `OntologyType` defines a class of entities in the knowledge graph,
/// forming a hierarchical structure through the `parent` field.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct OntologyType {
    /// Unique identifier for this type
    pub type_id: String,

    /// Human-readable name
    pub name: String,

    /// Parent type (for is_a hierarchy)
    pub parent: Option<String>,

    /// Description of this type
    pub description: String,

    /// Timestamp when type was defined
    pub created_at: Timestamp,
}

/// Represents a relation definition in the ontology.
///
/// Each `OntologyRelation` defines a type of link that can exist between
/// `OntologyType`s, including constraints on the types of subjects (domain) and
/// objects (range) that the relation can connect.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct OntologyRelation {
    /// Unique identifier for this relation
    pub relation_id: String,

    /// Human-readable name
    pub name: String,

    /// Domain constraint (valid subject types)
    pub domain: Vec<String>,

    /// Range constraint (valid object types)
    pub range: Vec<String>,

    /// Relation properties
    pub is_transitive: bool,
    pub is_symmetric: bool,
    pub is_reflexive: bool,

    /// Description
    pub description: String,

    /// Timestamp
    pub created_at: Timestamp,
}

/// Represents a (subject, predicate, object) knowledge triple.
///
/// This is the fundamental unit of knowledge in the system. Each triple is a
/// verifiable, sourced, and timestamped assertion about the relationship
/// between two entities.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeTriple {
    /// Subject entity ID
    pub subject: String,

    /// Predicate (relation ID)
    pub predicate: String,

    /// Object entity ID or value
    pub object: String,

    /// Confidence score (0.0-1.0)
    pub confidence: f32,

    /// Source agent
    pub source: AgentPubKey,

    /// Timestamp
    pub created_at: Timestamp,
}

/// Represents an assertion that a given entity belongs to a specific type.
///
/// In a fully dynamic ontology, these assertions would be stored on the DHT,
/// allowing the system to learn and infer the types of new entities at runtime.
///
/// TODO: Needs refinement by a human expert.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct TypeAssertion {
    /// Entity being typed
    pub entity_id: String,

    /// Type assigned to entity
    pub type_id: String,

    /// Who asserted this type
    pub asserted_by: AgentPubKey,

    /// When asserted
    pub asserted_at: Timestamp,
}

// Note: Entry type definitions and link types would typically be defined
// in the main DNA's integrity zome, not in this library zome.
// This zome provides validation logic that can be used by other zomes.

/// Validates a `KnowledgeTriple` against the defined ontology constraints.
///
/// This is a critical function for maintaining the integrity and coherence of the
/// knowledge graph. It performs a series of checks, including:
/// 1. Verifying that the relation exists.
/// 2. Inferring the types of the subject and object.
/// 3. Checking for violations of domain and range constraints.
/// 4. Ensuring that the confidence score is within the valid range [0.0, 1.0].
///
/// TODO: Needs refinement by a human expert.
pub fn validate_triple(triple: &KnowledgeTriple) -> Result<(), OntologyError> {
    // 1. Check that relation exists
    let relation = get_relation(&triple.predicate)?;

    // 2. Infer subject type
    let subject_type = infer_type(&triple.subject)?;

    // 3. Infer object type
    let object_type = infer_type(&triple.object)?;

    // 4. Validate domain constraint (if specified)
    if !relation.domain.is_empty() {
        let subject_valid = relation.domain.contains(&subject_type)
            || is_subtype_of(&subject_type, &relation.domain)?;

        if !subject_valid {
            return Err(OntologyError::DomainViolation {
                relation: relation.name.clone(),
                required: relation.domain.join(" | "),
                actual: subject_type,
            });
        }
    }

    // 5. Validate range constraint (if specified)
    if !relation.range.is_empty() {
        let object_valid = relation.range.contains(&object_type)
            || is_subtype_of(&object_type, &relation.range)?;

        if !object_valid {
            return Err(OntologyError::RangeViolation {
                relation: relation.name.clone(),
                required: relation.range.join(" | "),
                actual: object_type,
            });
        }
    }

    // 6. Validate confidence bounds
    if !(0.0..=1.0).contains(&triple.confidence) {
        return Err(OntologyError::ValidationError(
            format!("Confidence must be in [0,1], got {}", triple.confidence)
        ));
    }

    Ok(())
}

/// Check if a type is a subtype of any type in the target list
fn is_subtype_of(type_id: &str, target_types: &[String]) -> Result<bool, OntologyError> {
    // Check direct match first
    if target_types.contains(&type_id.to_string()) {
        return Ok(true);
    }

    // Check if type_id is a subtype of any target type through inheritance
    // For now, we'll use a simple parent-checking mechanism
    // In a full implementation, this would query the DHT for type hierarchy
    let type_def = get_type_definition(type_id)?;

    if let Some(parent) = type_def.parent {
        // Recursively check parent
        is_subtype_of(&parent, target_types)
    } else {
        Ok(false)
    }
}

/// Infers the ontological type of an entity based on heuristics.
///
/// In a fully realized system, this function would query the DHT for explicit
/// `TypeAssertion`s. In the current bootstrap phase, it uses a set of predefined
/// patterns and keywords to make a best-effort inference. This is a pragmatic
/// approach to enabling "Federated Reasoning" before the knowledge graph is
/// fully populated.
///
/// TODO: Needs refinement by a human expert.
pub fn infer_type(entity_id: &str) -> Result<String, OntologyError> {
    // In a full implementation, this would query the DHT for type assertions
    // For bootstrap phase, we use simple heuristics

    // Check for explicit type assertion (would query DHT in production)
    if let Some(type_id) = query_type_assertion(entity_id) {
        return Ok(type_id);
    }

    // Default heuristics based on entity_id patterns
    // These help during bootstrap before all types are asserted

    // AI/ML type heuristics
    if entity_id.contains("GPT") || entity_id.contains("Claude") ||
       entity_id.contains("Llama") || entity_id.contains("Gemini") ||
       entity_id.ends_with("-LLM") || entity_id.ends_with("_llm") {
        Ok("LLM".to_string())
    } else if entity_id.ends_with("_model") || entity_id.ends_with("-model") ||
              entity_id.contains("Model") {
        Ok("AIModel".to_string())
    } else if entity_id.ends_with("_dataset") || entity_id.ends_with("-dataset") ||
              entity_id.contains("Dataset") {
        Ok("Dataset".to_string())
    } else if entity_id.ends_with("_capability") || entity_id.ends_with("-capability") {
        Ok("Capability".to_string())
    } else if entity_id.ends_with("_benchmark") || entity_id.ends_with("-benchmark") {
        Ok("Benchmark".to_string())
    } else if entity_id.ends_with("_training") || entity_id.ends_with("-training") {
        Ok("TrainingRun".to_string())
    }
    // Base type heuristics
    else if entity_id.ends_with("_concept") || entity_id.ends_with("_type") {
        Ok("Concept".to_string())
    } else if entity_id.ends_with("_agent") {
        Ok("Agent".to_string())
    } else if entity_id.ends_with("_event") {
        Ok("Event".to_string())
    } else {
        // Default to Entity type
        Ok("Entity".to_string())
    }
}

/// Checks if a given subject and object type satisfy the domain and range
/// constraints of a relation.
///
/// TODO: Needs refinement by a human expert.
pub fn check_domain_range(
    relation: &OntologyRelation,
    subject_type: &str,
    object_type: &str
) -> bool {
    let domain_ok = relation.domain.is_empty()
        || relation.domain.contains(&subject_type.to_string())
        || is_subtype_of(subject_type, &relation.domain).unwrap_or(false);

    let range_ok = relation.range.is_empty()
        || relation.range.contains(&object_type.to_string())
        || is_subtype_of(object_type, &relation.range).unwrap_or(false);

    domain_ok && range_ok
}

/// Get a relation definition from the ontology
fn get_relation(relation_id: &str) -> Result<OntologyRelation, OntologyError> {
    // In production, this would query DHT for relation definitions
    // For bootstrap, we hardcode base relations
    // Use a fixed timestamp for bootstrap definitions
    let timestamp = Timestamp::from_micros(0);

    match relation_id {
        "is_a" => Ok(OntologyRelation {
            relation_id: "is_a".into(),
            name: "is a".into(),
            domain: vec![],  // Any type can have an is_a relation
            range: vec!["Type".into(), "Concept".into(), "Thing".into()],
            is_transitive: true,
            is_symmetric: false,
            is_reflexive: true,
            description: "Type hierarchy relation - subject is an instance or subtype of object".into(),
            created_at: timestamp,
        }),
        "part_of" => Ok(OntologyRelation {
            relation_id: "part_of".into(),
            name: "part of".into(),
            domain: vec![],  // Any entity
            range: vec![],   // Any entity
            is_transitive: true,
            is_symmetric: false,
            is_reflexive: false,
            description: "Parthood relation - subject is a component of object".into(),
            created_at: timestamp,
        }),
        "related_to" => Ok(OntologyRelation {
            relation_id: "related_to".into(),
            name: "related to".into(),
            domain: vec![],  // Any entity
            range: vec![],   // Any entity
            is_transitive: false,
            is_symmetric: true,
            is_reflexive: true,
            description: "General relatedness - symmetric relation between entities".into(),
            created_at: timestamp,
        }),
        "has_property" => Ok(OntologyRelation {
            relation_id: "has_property".into(),
            name: "has property".into(),
            domain: vec!["Entity".into(), "Concept".into()],
            range: vec!["Property".into(), "Value".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Property attribution - subject has the property specified in object".into(),
            created_at: timestamp,
        }),
        // AI/ML Domain Relations
        "trained_on" => Ok(OntologyRelation {
            relation_id: "trained_on".into(),
            name: "trained on".into(),
            domain: vec!["AIModel".into(), "LLM".into()],
            range: vec!["Dataset".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Model was trained on dataset".into(),
            created_at: timestamp,
        }),
        "improves_upon" => Ok(OntologyRelation {
            relation_id: "improves_upon".into(),
            name: "improves upon".into(),
            domain: vec!["AIModel".into(), "LLM".into()],
            range: vec!["AIModel".into(), "LLM".into()],
            is_transitive: true,  // Important for inference!
            is_symmetric: false,
            is_reflexive: false,
            description: "Model improves upon another model".into(),
            created_at: timestamp,
        }),
        "capable_of" => Ok(OntologyRelation {
            relation_id: "capable_of".into(),
            name: "capable of".into(),
            domain: vec!["AIModel".into(), "LLM".into(), "Agent".into()],
            range: vec!["Capability".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Model or agent has capability".into(),
            created_at: timestamp,
        }),
        "evaluated_on" => Ok(OntologyRelation {
            relation_id: "evaluated_on".into(),
            name: "evaluated on".into(),
            domain: vec!["AIModel".into(), "LLM".into()],
            range: vec!["Benchmark".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Model evaluated on benchmark".into(),
            created_at: timestamp,
        }),
        _ => Err(OntologyError::UnknownRelation(relation_id.to_string())),
    }
}

/// Get type definition (stub for bootstrap)
fn get_type_definition(type_id: &str) -> Result<OntologyType, OntologyError> {
    // In production, this would query DHT
    // For bootstrap, return hardcoded base types
    // Use a fixed timestamp for bootstrap definitions
    let timestamp = Timestamp::from_micros(0);

    match type_id {
        "Thing" => Ok(OntologyType {
            type_id: "Thing".into(),
            name: "Thing".into(),
            parent: None,
            description: "Root of all types - the most general category".into(),
            created_at: timestamp,
        }),
        "Entity" => Ok(OntologyType {
            type_id: "Entity".into(),
            name: "Entity".into(),
            parent: Some("Thing".into()),
            description: "Physical or abstract entities that exist".into(),
            created_at: timestamp,
        }),
        "Concept" => Ok(OntologyType {
            type_id: "Concept".into(),
            name: "Concept".into(),
            parent: Some("Thing".into()),
            description: "Abstract concepts and ideas".into(),
            created_at: timestamp,
        }),
        "Agent" => Ok(OntologyType {
            type_id: "Agent".into(),
            name: "Agent".into(),
            parent: Some("Entity".into()),
            description: "Acting agents (human or AI) that can perform actions".into(),
            created_at: timestamp,
        }),
        "Event" => Ok(OntologyType {
            type_id: "Event".into(),
            name: "Event".into(),
            parent: Some("Thing".into()),
            description: "Occurrences in time and space".into(),
            created_at: timestamp,
        }),
        "Property" => Ok(OntologyType {
            type_id: "Property".into(),
            name: "Property".into(),
            parent: Some("Concept".into()),
            description: "Attributes and characteristics".into(),
            created_at: timestamp,
        }),
        "Value" => Ok(OntologyType {
            type_id: "Value".into(),
            name: "Value".into(),
            parent: Some("Thing".into()),
            description: "Literal values and data".into(),
            created_at: timestamp,
        }),
        // AI/ML Domain Types
        "AIModel" => Ok(OntologyType {
            type_id: "AIModel".into(),
            name: "AI Model".into(),
            parent: Some("Agent".into()),
            description: "Artificial intelligence model".into(),
            created_at: timestamp,
        }),
        "LLM" => Ok(OntologyType {
            type_id: "LLM".into(),
            name: "Large Language Model".into(),
            parent: Some("AIModel".into()),
            description: "Large language model".into(),
            created_at: timestamp,
        }),
        "Dataset" => Ok(OntologyType {
            type_id: "Dataset".into(),
            name: "Dataset".into(),
            parent: Some("Entity".into()),
            description: "Training or evaluation dataset".into(),
            created_at: timestamp,
        }),
        "Capability" => Ok(OntologyType {
            type_id: "Capability".into(),
            name: "Capability".into(),
            parent: Some("Concept".into()),
            description: "A capability or skill".into(),
            created_at: timestamp,
        }),
        "Benchmark" => Ok(OntologyType {
            type_id: "Benchmark".into(),
            name: "Benchmark".into(),
            parent: Some("Entity".into()),
            description: "Evaluation benchmark".into(),
            created_at: timestamp,
        }),
        "TrainingRun" => Ok(OntologyType {
            type_id: "TrainingRun".into(),
            name: "Training Run".into(),
            parent: Some("Event".into()),
            description: "A model training execution".into(),
            created_at: timestamp,
        }),
        _ => Err(OntologyError::UnknownType(type_id.to_string())),
    }
}

/// Query for type assertion (stub for now)
fn query_type_assertion(_entity_id: &str) -> Option<String> {
    // TODO: Query DHT for TypeAssertion entries
    // For now, return None to use default heuristics
    None
}

/// Bootstraps the AI/ML domain-specific ontology.
///
/// This function defines and returns the set of core types and relations needed
/// to represent knowledge about AI models, datasets, and benchmarks.
///
/// TODO: Needs refinement by a human expert.
pub fn bootstrap_ai_ml_ontology() -> (Vec<OntologyType>, Vec<OntologyRelation>) {
    let timestamp = Timestamp::from_micros(0);

    let ai_ml_types = vec![
        OntologyType {
            type_id: "AIModel".into(),
            name: "AI Model".into(),
            parent: Some("Agent".into()),
            description: "Artificial intelligence model".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "LLM".into(),
            name: "Large Language Model".into(),
            parent: Some("AIModel".into()),
            description: "Large language model".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Dataset".into(),
            name: "Dataset".into(),
            parent: Some("Entity".into()),
            description: "Training or evaluation dataset".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Capability".into(),
            name: "Capability".into(),
            parent: Some("Concept".into()),
            description: "A capability or skill".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Benchmark".into(),
            name: "Benchmark".into(),
            parent: Some("Entity".into()),
            description: "Evaluation benchmark".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "TrainingRun".into(),
            name: "Training Run".into(),
            parent: Some("Event".into()),
            description: "A model training execution".into(),
            created_at: timestamp,
        },
    ];

    // Get AI/ML relations
    let ai_ml_relation_ids = ["trained_on", "improves_upon", "capable_of", "evaluated_on"];
    let ai_ml_relations: Vec<OntologyRelation> = ai_ml_relation_ids
        .iter()
        .filter_map(|id| get_relation(id).ok())
        .collect();

    (ai_ml_types, ai_ml_relations)
}

/// Provides a set of example `KnowledgeTriple`s for the AI/ML domain.
///
/// These examples serve as a concrete specification for how to represent
/// common knowledge about AI models and their capabilities.
///
/// TODO: Needs refinement by a human expert.
pub fn bootstrap_ai_examples() -> Vec<(String, String, String)> {
    vec![
        // GPT models
        ("GPT-4".to_string(), "is_a".to_string(), "LLM".to_string()),
        ("GPT-4".to_string(), "capable_of".to_string(), "coding".to_string()),
        ("GPT-4".to_string(), "capable_of".to_string(), "writing".to_string()),
        ("GPT-4".to_string(), "improves_upon".to_string(), "GPT-3.5".to_string()),
        ("GPT-3.5".to_string(), "is_a".to_string(), "LLM".to_string()),

        // Claude models
        ("Claude-Sonnet-4.5".to_string(), "is_a".to_string(), "LLM".to_string()),
        ("Claude-Sonnet-4.5".to_string(), "improves_upon".to_string(), "Claude-Sonnet-4".to_string()),
        ("Claude-Sonnet-4".to_string(), "is_a".to_string(), "LLM".to_string()),
        ("Claude-Sonnet-4".to_string(), "capable_of".to_string(), "coding".to_string()),
        ("Claude-Sonnet-4".to_string(), "capable_of".to_string(), "reasoning".to_string()),
        ("Claude-Sonnet-4".to_string(), "improves_upon".to_string(), "Claude-Sonnet-3.5".to_string()),

        // Capabilities as concepts
        ("coding".to_string(), "is_a".to_string(), "Capability".to_string()),
        ("reasoning".to_string(), "is_a".to_string(), "Capability".to_string()),
        ("writing".to_string(), "is_a".to_string(), "Capability".to_string()),

        // Datasets
        ("WebText".to_string(), "is_a".to_string(), "Dataset".to_string()),
        ("CommonCrawl".to_string(), "is_a".to_string(), "Dataset".to_string()),
        ("GPT-4".to_string(), "trained_on".to_string(), "WebText".to_string()),

        // Benchmarks
        ("HumanEval".to_string(), "is_a".to_string(), "Benchmark".to_string()),
        ("MMLU".to_string(), "is_a".to_string(), "Benchmark".to_string()),
        ("GPT-4".to_string(), "evaluated_on".to_string(), "HumanEval".to_string()),
        ("Claude-Sonnet-4.5".to_string(), "evaluated_on".to_string(), "MMLU".to_string()),
    ]
}

/// Bootstraps the base ontology with a minimal set of core types and relations.
///
/// TODO: Needs refinement by a human expert.
pub fn bootstrap_base_ontology() -> (Vec<OntologyType>, Vec<OntologyRelation>) {
    // Use a fixed timestamp for bootstrap definitions
    let timestamp = Timestamp::from_micros(0);

    // Define base types
    let base_types = vec![
        OntologyType {
            type_id: "Thing".into(),
            name: "Thing".into(),
            parent: None,
            description: "Root of all types - the most general category".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Entity".into(),
            name: "Entity".into(),
            parent: Some("Thing".into()),
            description: "Physical or abstract entities that exist".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Concept".into(),
            name: "Concept".into(),
            parent: Some("Thing".into()),
            description: "Abstract concepts and ideas".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Agent".into(),
            name: "Agent".into(),
            parent: Some("Entity".into()),
            description: "Acting agents (human or AI) that can perform actions".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Event".into(),
            name: "Event".into(),
            parent: Some("Thing".into()),
            description: "Occurrences in time and space".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Property".into(),
            name: "Property".into(),
            parent: Some("Concept".into()),
            description: "Attributes and characteristics".into(),
            created_at: timestamp,
        },
        OntologyType {
            type_id: "Value".into(),
            name: "Value".into(),
            parent: Some("Thing".into()),
            description: "Literal values and data".into(),
            created_at: timestamp,
        },
    ];

    // Define base relations
    let base_relation_ids = ["is_a", "part_of", "related_to", "has_property"];
    let base_relations: Vec<OntologyRelation> = base_relation_ids
        .iter()
        .filter_map(|id| get_relation(id).ok())
        .collect();

    (base_types, base_relations)
}

/// Validates the structure of an `OntologyType` definition.
///
/// TODO: Needs refinement by a human expert.
pub fn validate_ontology_type(ont_type: &OntologyType) -> Result<(), String> {
    // Type ID must not be empty
    if ont_type.type_id.is_empty() {
        return Err("Type ID cannot be empty".to_string());
    }

    // Name must not be empty
    if ont_type.name.is_empty() {
        return Err("Type name cannot be empty".to_string());
    }

    // If parent is specified, verify it exists (in production would query DHT)
    if let Some(ref parent) = ont_type.parent {
        if parent.is_empty() {
            return Err("Parent type cannot be empty string".to_string());
        }
    }

    Ok(())
}

/// Validates the structure of an `OntologyRelation` definition.
///
/// TODO: Needs refinement by a human expert.
pub fn validate_ontology_relation(relation: &OntologyRelation) -> Result<(), String> {
    // Relation ID must not be empty
    if relation.relation_id.is_empty() {
        return Err("Relation ID cannot be empty".to_string());
    }

    // Name must not be empty
    if relation.name.is_empty() {
        return Err("Relation name cannot be empty".to_string());
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fake_agent_pub_key() -> AgentPubKey {
        // Create a proper fake agent key for testing
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
    fn test_validate_valid_triple() {
        let triple = KnowledgeTriple {
            subject: "claude_agent".into(),
            predicate: "is_a".into(),
            object: "Agent".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_ok(), "Valid triple should pass validation");
    }

    #[test]
    fn test_validate_invalid_confidence() {
        let triple = KnowledgeTriple {
            subject: "test_entity".into(),
            predicate: "is_a".into(),
            object: "Thing".into(),
            confidence: 1.5,  // Invalid!
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err(), "Invalid confidence should fail validation");

        if let Err(OntologyError::ValidationError(msg)) = result {
            assert!(msg.contains("Confidence"));
        } else {
            panic!("Expected ValidationError");
        }
    }

    #[test]
    fn test_validate_negative_confidence() {
        let triple = KnowledgeTriple {
            subject: "test".into(),
            predicate: "related_to".into(),
            object: "another".into(),
            confidence: -0.1,  // Invalid!
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err(), "Negative confidence should fail");
    }

    #[test]
    fn test_unknown_relation() {
        let triple = KnowledgeTriple {
            subject: "test".into(),
            predicate: "invalid_relation".into(),
            object: "target".into(),
            confidence: 0.8,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err(), "Unknown relation should fail");

        if let Err(OntologyError::UnknownRelation(rel)) = result {
            assert_eq!(rel, "invalid_relation");
        } else {
            panic!("Expected UnknownRelation error");
        }
    }

    #[test]
    fn test_get_relation_is_a() {
        let relation = get_relation("is_a").unwrap();
        assert_eq!(relation.relation_id, "is_a");
        assert!(relation.is_transitive, "is_a should be transitive");
        assert!(!relation.is_symmetric, "is_a should not be symmetric");
        assert!(relation.is_reflexive, "is_a should be reflexive");
    }

    #[test]
    fn test_get_relation_part_of() {
        let relation = get_relation("part_of").unwrap();
        assert_eq!(relation.relation_id, "part_of");
        assert!(relation.is_transitive, "part_of should be transitive");
        assert!(!relation.is_symmetric, "part_of should not be symmetric");
        assert!(!relation.is_reflexive, "part_of should not be reflexive");
    }

    #[test]
    fn test_get_relation_related_to() {
        let relation = get_relation("related_to").unwrap();
        assert_eq!(relation.relation_id, "related_to");
        assert!(!relation.is_transitive, "related_to should not be transitive");
        assert!(relation.is_symmetric, "related_to should be symmetric");
    }

    #[test]
    fn test_infer_type_agent() {
        let result = infer_type("claude_agent");
        assert_eq!(result.unwrap(), "Agent");
    }

    #[test]
    fn test_infer_type_concept() {
        let result = infer_type("knowledge_concept");
        assert_eq!(result.unwrap(), "Concept");
    }

    #[test]
    fn test_infer_type_default() {
        let result = infer_type("some_random_entity");
        assert_eq!(result.unwrap(), "Entity");
    }

    #[test]
    fn test_get_type_definition_thing() {
        let type_def = get_type_definition("Thing").unwrap();
        assert_eq!(type_def.type_id, "Thing");
        assert_eq!(type_def.parent, None);
    }

    #[test]
    fn test_get_type_definition_agent() {
        let type_def = get_type_definition("Agent").unwrap();
        assert_eq!(type_def.type_id, "Agent");
        assert_eq!(type_def.parent, Some("Entity".to_string()));
    }

    #[test]
    fn test_type_hierarchy() {
        let entity = get_type_definition("Entity").unwrap();
        assert_eq!(entity.parent, Some("Thing".to_string()));

        let agent = get_type_definition("Agent").unwrap();
        assert_eq!(agent.parent, Some("Entity".to_string()));
    }

    #[test]
    fn test_check_domain_range_valid() {
        let relation = get_relation("is_a").unwrap();
        assert!(check_domain_range(&relation, "Entity", "Thing"));
    }

    #[test]
    fn test_check_domain_range_with_constraints() {
        let relation = get_relation("has_property").unwrap();
        assert!(check_domain_range(&relation, "Entity", "Property"));
    }

    #[test]
    fn test_validate_ontology_type_valid() {
        let ont_type = OntologyType {
            type_id: "CustomType".into(),
            name: "Custom Type".into(),
            parent: Some("Entity".into()),
            description: "A custom type for testing".into(),
            created_at: fake_timestamp(),
        };

        let result = validate_ontology_type(&ont_type);
        assert!(result.is_ok(), "Valid type should pass validation");
    }

    #[test]
    fn test_validate_ontology_type_empty_id() {
        let ont_type = OntologyType {
            type_id: "".into(),
            name: "Invalid Type".into(),
            parent: None,
            description: "Should fail".into(),
            created_at: fake_timestamp(),
        };

        let result = validate_ontology_type(&ont_type);
        assert!(result.is_err(), "Empty type ID should fail validation");
    }

    #[test]
    fn test_validate_ontology_relation_valid() {
        let relation = OntologyRelation {
            relation_id: "custom_rel".into(),
            name: "custom relation".into(),
            domain: vec![],
            range: vec![],
            is_transitive: false,
            is_symmetric: true,
            is_reflexive: false,
            description: "A custom relation".into(),
            created_at: fake_timestamp(),
        };

        let result = validate_ontology_relation(&relation);
        assert!(result.is_ok(), "Valid relation should pass validation");
    }

    #[test]
    fn test_bootstrap_base_ontology() {
        // This tests that bootstrap runs without errors
        let (types, relations) = bootstrap_base_ontology();
        assert_eq!(types.len(), 7, "Should have 7 base types");
        assert_eq!(relations.len(), 4, "Should have 4 base relations");
    }

    // ===== AI/ML Ontology Tests =====

    #[test]
    fn test_bootstrap_ai_ml_ontology() {
        let (types, relations) = bootstrap_ai_ml_ontology();
        assert_eq!(types.len(), 6, "Should have 6 AI/ML types");
        assert_eq!(relations.len(), 4, "Should have 4 AI/ML relations");
    }

    #[test]
    fn test_ai_ml_types_retrievable() {
        let ai_ml_types = vec!["AIModel", "LLM", "Dataset", "Capability", "Benchmark", "TrainingRun"];

        for type_id in ai_ml_types {
            let result = get_type_definition(type_id);
            assert!(result.is_ok(), "Should be able to get AI/ML type {}", type_id);
        }
    }

    #[test]
    fn test_ai_ml_relations_retrievable() {
        let ai_ml_relations = vec!["trained_on", "improves_upon", "capable_of", "evaluated_on"];

        for relation_id in ai_ml_relations {
            let result = get_relation(relation_id);
            assert!(result.is_ok(), "Should be able to get AI/ML relation {}", relation_id);
        }
    }

    #[test]
    fn test_llm_inherits_from_ai_model() {
        let llm = get_type_definition("LLM").unwrap();
        assert_eq!(llm.parent, Some("AIModel".to_string()), "LLM should inherit from AIModel");
    }

    #[test]
    fn test_ai_model_inherits_from_agent() {
        let ai_model = get_type_definition("AIModel").unwrap();
        assert_eq!(ai_model.parent, Some("Agent".to_string()), "AIModel should inherit from Agent");
    }

    #[test]
    fn test_improves_upon_is_transitive() {
        let relation = get_relation("improves_upon").unwrap();
        assert!(relation.is_transitive, "improves_upon should be transitive");
        assert!(!relation.is_symmetric, "improves_upon should not be symmetric");
    }

    #[test]
    fn test_trained_on_validates_types() {
        // Valid: LLM trained_on Dataset
        let valid = KnowledgeTriple {
            subject: "GPT-4".into(),
            predicate: "trained_on".into(),
            object: "WebText_dataset".into(),  // Use _dataset suffix to match heuristic
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };
        assert!(validate_triple(&valid).is_ok(), "LLM trained_on Dataset should be valid");
    }

    #[test]
    fn test_trained_on_rejects_invalid_domain() {
        // Invalid: Dataset cannot be trained (wrong subject type)
        let invalid = KnowledgeTriple {
            subject: "WebText".into(),  // Dataset, not AIModel
            predicate: "trained_on".into(),
            object: "GPT-4".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };
        let result = validate_triple(&invalid);
        assert!(result.is_err(), "Dataset trained_on should fail validation");

        if let Err(OntologyError::DomainViolation { .. }) = result {
            // Expected error type
        } else {
            panic!("Expected DomainViolation error");
        }
    }

    #[test]
    fn test_capable_of_validates_range() {
        // Valid: LLM capable_of Capability
        let valid = KnowledgeTriple {
            subject: "Claude-Sonnet-4.5".into(),
            predicate: "capable_of".into(),
            object: "coding_capability".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };
        assert!(validate_triple(&valid).is_ok(), "LLM capable_of Capability should be valid");
    }

    #[test]
    fn test_improves_upon_validates_domain_and_range() {
        // Valid: LLM improves_upon LLM
        let valid = KnowledgeTriple {
            subject: "Claude-Sonnet-4.5".into(),
            predicate: "improves_upon".into(),
            object: "Claude-Sonnet-4".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: fake_timestamp(),
        };
        assert!(validate_triple(&valid).is_ok(), "LLM improves_upon LLM should be valid");
    }

    #[test]
    fn test_infer_type_gpt() {
        let result = infer_type("GPT-4");
        assert_eq!(result.unwrap(), "LLM", "GPT-4 should be inferred as LLM");
    }

    #[test]
    fn test_infer_type_claude() {
        let result = infer_type("Claude-Sonnet-4.5");
        assert_eq!(result.unwrap(), "LLM", "Claude should be inferred as LLM");
    }

    #[test]
    fn test_infer_type_dataset() {
        let result = infer_type("CommonCrawl_dataset");
        assert_eq!(result.unwrap(), "Dataset", "Should infer Dataset type");
    }

    #[test]
    fn test_infer_type_capability() {
        let result = infer_type("coding_capability");
        assert_eq!(result.unwrap(), "Capability", "Should infer Capability type");
    }

    #[test]
    fn test_infer_type_benchmark() {
        let result = infer_type("HumanEval_benchmark");
        assert_eq!(result.unwrap(), "Benchmark", "Should infer Benchmark type");
    }

    #[test]
    fn test_bootstrap_ai_examples() {
        let examples = bootstrap_ai_examples();
        assert!(!examples.is_empty(), "Should have AI examples");

        // Check that GPT-4 is in examples
        assert!(examples.iter().any(|(s, p, o)|
            s == "GPT-4" && p == "is_a" && o == "LLM"
        ), "Should include GPT-4 as LLM");

        // Check that Claude is in examples
        assert!(examples.iter().any(|(s, p, o)|
            s == "Claude-Sonnet-4.5" && p == "is_a" && o == "LLM"
        ), "Should include Claude as LLM");

        // Check improvement relation
        assert!(examples.iter().any(|(s, p, o)|
            s == "Claude-Sonnet-4.5" && p == "improves_upon" && o == "Claude-Sonnet-4"
        ), "Should include improvement relation");

        // Check capability relation
        assert!(examples.iter().any(|(s, p, o)|
            s == "Claude-Sonnet-4" && p == "capable_of" && o == "coding"
        ), "Should include capability relation");
    }

    #[test]
    fn test_evaluated_on_relation() {
        let relation = get_relation("evaluated_on").unwrap();
        assert_eq!(relation.relation_id, "evaluated_on");
        assert_eq!(relation.domain, vec!["AIModel", "LLM"]);
        assert_eq!(relation.range, vec!["Benchmark"]);
    }

    #[test]
    fn test_capability_type_hierarchy() {
        let capability = get_type_definition("Capability").unwrap();
        assert_eq!(capability.parent, Some("Concept".to_string()), "Capability should inherit from Concept");
    }

    #[test]
    fn test_dataset_type_hierarchy() {
        let dataset = get_type_definition("Dataset").unwrap();
        assert_eq!(dataset.parent, Some("Entity".to_string()), "Dataset should inherit from Entity");
    }

    #[test]
    fn test_training_run_type_hierarchy() {
        let training_run = get_type_definition("TrainingRun").unwrap();
        assert_eq!(training_run.parent, Some("Event".to_string()), "TrainingRun should inherit from Event");
    }

    #[test]
    fn test_all_base_types_retrievable() {
        let base_types = vec!["Thing", "Entity", "Concept", "Agent", "Event", "Property", "Value"];

        for type_id in base_types {
            let result = get_type_definition(type_id);
            assert!(result.is_ok(), "Should be able to get type {}", type_id);
        }
    }

    #[test]
    fn test_all_base_relations_retrievable() {
        let base_relations = vec!["is_a", "part_of", "related_to", "has_property"];

        for relation_id in base_relations {
            let result = get_relation(relation_id);
            assert!(result.is_ok(), "Should be able to get relation {}", relation_id);
        }
    }
}
