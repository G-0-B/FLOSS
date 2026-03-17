# Task 2.1: Implement Base Ontology in Holochain Integrity Zome

**Phase**: 2 (Foundation)
**Estimated Time**: 8 hours
**Complexity**: MEDIUM-HIGH
**Dependencies**: None (but Phase 1 should complete first)
**Parallelizable**: NO - Tasks 2.2 and 2.3 depend on this
**CRITICAL**: This is a blocking task for Phase 2

---

## 🎯 Objective

Implement the foundational symbolic ontology layer in a Holochain integrity zome that enforces semantic validation for ALL knowledge entering the system. This is the cornerstone of the symbolic-first architecture.

---

## 📍 Context

From ACTION_PLAN_AND_VIDEO_RESPONSE.md (Week 1 goals):
> Deploy base ontology that validates ALL knowledge entry. No embedding can be stored without a valid triple.

This implements the neurosymbolic AI vision where:
- **Symbolic layer** (this task) = formal correctness, ontology validation
- **Neural layer** (Phase 1) = embeddings, semantic search

**Key Principle** (from docs):
> "LLMs approximate semantics; you ENFORCE semantics."

---

## ✅ Acceptance Criteria

1. **Create base ontology integrity zome**
   - New Rust zome: `ARF/dnas/rose_forest/zomes/ontology_integrity/`
   - Define core types: Entity, Concept, Relation
   - Define base relations: is_a, part_of, related_to

2. **Implement validation rules**
   - Type checking for all triples
   - Axiom enforcement (transitivity, symmetry, etc.)
   - Reject invalid triples at DHT entry level

3. **Bootstrap minimal ontology**
   - Root type: Thing
   - Basic types: Entity, Concept, Agent, Event
   - Basic relations with domain/range constraints

4. **Entry structures**
   - OntologyType entry
   - OntologyRelation entry
   - TypeAssertion entry (for runtime type checking)

5. **Validation functions**
   - `validate_triple(subject, predicate, object) -> Result<(), OntologyError>`
   - `infer_type(entity_id) -> Result<TypeId, OntologyError>`
   - `check_domain_range(relation, subject_type, object_type) -> bool`

6. **Tests**
   - Valid triples accepted
   - Invalid triples rejected
   - Type inference works correctly
   - Axioms applied correctly
   - Coverage ≥80%

7. **Documentation**
   - Ontology schema documented
   - Validation rules explained
   - Examples of valid/invalid triples

---

## 🔧 Implementation Guidance

### Step 1: Create Zome Structure

```bash
cd /home/user/FLOSS/ARF/dnas/rose_forest/zomes
cargo new ontology_integrity --lib
cd ontology_integrity
```

Update `Cargo.toml`:
```toml
[package]
name = "ontology_integrity"
version = "0.1.0"
edition = "2021"

[dependencies]
hdk = "0.2"
serde = { version = "1.0", features = ["derive"] }
thiserror = "1.0"

[lib]
crate-type = ["cdylib", "rlib"]
```

### Step 2: Define Core Data Structures

Create `src/lib.rs`:

```rust
use hdk::prelude::*;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Errors that can occur during ontology validation
#[derive(Error, Debug)]
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

/// Represents a type in the ontology
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

/// Represents a relation in the ontology
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

/// A knowledge triple to be validated
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

/// Type assertion for runtime type checking
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
```

### Step 3: Implement Validation Logic

```rust
/// Validate a knowledge triple against ontology constraints
pub fn validate_triple(triple: &KnowledgeTriple) -> Result<(), OntologyError> {
    // 1. Check that relation exists
    let relation = get_relation(&triple.predicate)?;

    // 2. Infer subject type
    let subject_type = infer_type(&triple.subject)?;

    // 3. Infer object type
    let object_type = infer_type(&triple.object)?;

    // 4. Validate domain constraint
    if !relation.domain.is_empty() && !relation.domain.contains(&subject_type) {
        return Err(OntologyError::DomainViolation {
            relation: relation.name.clone(),
            required: relation.domain.join(" | "),
            actual: subject_type,
        });
    }

    // 5. Validate range constraint
    if !relation.range.is_empty() && !relation.range.contains(&object_type) {
        return Err(OntologyError::RangeViolation {
            relation: relation.name.clone(),
            required: relation.range.join(" | "),
            actual: object_type,
        });
    }

    // 6. Validate confidence bounds
    if triple.confidence < 0.0 || triple.confidence > 1.0 {
        return Err(OntologyError::ValidationError(
            format!("Confidence must be in [0,1], got {}", triple.confidence)
        ));
    }

    Ok(())
}

/// Infer the type of an entity
pub fn infer_type(entity_id: &str) -> Result<String, OntologyError> {
    // Query DHT for type assertions about this entity
    // For now, use simple heuristics or cached types

    // Check for explicit type assertion
    match query_type_assertion(entity_id) {
        Some(type_id) => Ok(type_id),
        None => {
            // Default to "Entity" type if no assertion found
            // In production, this might be more sophisticated
            Ok("Entity".to_string())
        }
    }
}

/// Get a relation definition from the ontology
fn get_relation(relation_id: &str) -> Result<OntologyRelation, OntologyError> {
    // Query DHT for relation definition
    // For bootstrap, use hardcoded base relations
    match relation_id {
        "is_a" => Ok(OntologyRelation {
            relation_id: "is_a".into(),
            name: "is a".into(),
            domain: vec![],  // Any type
            range: vec!["Type".into(), "Concept".into()],
            is_transitive: true,
            is_symmetric: false,
            is_reflexive: true,
            description: "Type hierarchy relation".into(),
            created_at: Timestamp::now(),
        }),
        "part_of" => Ok(OntologyRelation {
            relation_id: "part_of".into(),
            name: "part of".into(),
            domain: vec![],  // Any entity
            range: vec![],   // Any entity
            is_transitive: true,
            is_symmetric: false,
            is_reflexive: false,
            description: "Parthood relation".into(),
            created_at: Timestamp::now(),
        }),
        _ => Err(OntologyError::UnknownRelation(relation_id.to_string())),
    }
}

/// Query for type assertion (stub for now)
fn query_type_assertion(entity_id: &str) -> Option<String> {
    // TODO: Query DHT for TypeAssertion entries
    // For now, return None to use default
    None
}
```

### Step 4: Implement HDK Entry Points

```rust
#[hdk_extern]
pub fn init(_: ()) -> ExternResult<InitCallbackResult> {
    // Bootstrap base ontology on init
    bootstrap_base_ontology()?;
    Ok(InitCallbackResult::Pass)
}

#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op {
        Op::StoreEntry { entry, .. } => {
            // Validate based on entry type
            match entry {
                Entry::App(app_entry) => {
                    // Try to deserialize as KnowledgeTriple
                    if let Ok(triple) = KnowledgeTriple::try_from(app_entry) {
                        match validate_triple(&triple) {
                            Ok(()) => Ok(ValidateCallbackResult::Valid),
                            Err(e) => Ok(ValidateCallbackResult::Invalid(e.to_string())),
                        }
                    } else {
                        // Not a triple, allow other entry types
                        Ok(ValidateCallbackResult::Valid)
                    }
                }
                _ => Ok(ValidateCallbackResult::Valid),
            }
        }
        _ => Ok(ValidateCallbackResult::Valid),
    }
}

/// Bootstrap base ontology with minimal types and relations
fn bootstrap_base_ontology() -> ExternResult<()> {
    // Define base types
    let base_types = vec![
        OntologyType {
            type_id: "Thing".into(),
            name: "Thing".into(),
            parent: None,
            description: "Root of all types".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "Entity".into(),
            name: "Entity".into(),
            parent: Some("Thing".into()),
            description: "Physical or abstract entities".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "Concept".into(),
            name: "Concept".into(),
            parent: Some("Thing".into()),
            description: "Abstract concepts".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "Agent".into(),
            name: "Agent".into(),
            parent: Some("Entity".into()),
            description: "Acting agents (human or AI)".into(),
            created_at: Timestamp::now(),
        },
    ];

    // Store base types (would commit to DHT in real implementation)
    // For now, just log
    for base_type in base_types {
        debug!("Bootstrapped type: {}", base_type.name);
    }

    Ok(())
}
```

### Step 5: Add Tests

Create `src/tests.rs`:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_valid_triple() {
        let triple = KnowledgeTriple {
            subject: "Sonnet-4.5".into(),
            predicate: "is_a".into(),
            object: "LLM".into(),
            confidence: 1.0,
            source: fake_agent_pub_key(),
            created_at: Timestamp::now(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_ok());
    }

    #[test]
    fn test_validate_invalid_confidence() {
        let triple = KnowledgeTriple {
            subject: "Test".into(),
            predicate: "is_a".into(),
            object: "Thing".into(),
            confidence: 1.5,  // Invalid!
            source: fake_agent_pub_key(),
            created_at: Timestamp::now(),
        };

        let result = validate_triple(&triple);
        assert!(result.is_err());
    }

    #[test]
    fn test_unknown_relation() {
        let relation = get_relation("invalid_relation");
        assert!(relation.is_err());
    }

    #[test]
    fn test_is_a_relation_transitive() {
        let relation = get_relation("is_a").unwrap();
        assert!(relation.is_transitive);
        assert!(!relation.is_symmetric);
    }

    fn fake_agent_pub_key() -> AgentPubKey {
        // Create fake key for testing
        AgentPubKey::from_raw_36(vec![0u8; 36])
    }
}
```

---

## 🧪 Testing Checklist

```bash
cd /home/user/FLOSS/ARF/dnas/rose_forest/zomes/ontology_integrity
cargo test
cargo clippy
cargo build
```

Expected results:
- All tests pass
- No clippy warnings
- Clean build

---

## 📝 Completion Checklist

Before reporting done:
- [ ] Zome structure created
- [ ] Core data structures defined (OntologyType, OntologyRelation, KnowledgeTriple)
- [ ] Validation logic implemented
- [ ] Base ontology bootstrap function created
- [ ] HDK entry points implemented (init, validate)
- [ ] Tests written and passing
- [ ] No clippy warnings
- [ ] Documentation complete
- [ ] Example valid/invalid triples documented
- [ ] Completion report created
- [ ] Code pushed to branch

---

## 🚫 Out of Scope

- ❌ Full ontology reasoner (keep it simple)
- ❌ SPARQL query support
- ❌ OWL/RDF import
- ❌ GraphQL API
- ❌ UI for ontology editing
- ❌ Performance optimization (brute force is fine)

---

## 📋 Files to Create/Modify

- `ARF/dnas/rose_forest/zomes/ontology_integrity/Cargo.toml` (new)
- `ARF/dnas/rose_forest/zomes/ontology_integrity/src/lib.rs` (new)
- `ARF/dnas/rose_forest/zomes/ontology_integrity/src/tests.rs` (new)
- `ARF/dev/completion/phase2_task1.md` (completion report)

---

## 🎓 Success Metrics

Task is successful when:
1. ✅ Base ontology types defined and bootstrapped
2. ✅ Validation rejects invalid triples
3. ✅ Validation accepts valid triples
4. ✅ Type inference works
5. ✅ Axioms (transitivity, etc.) encoded
6. ✅ All tests pass
7. ✅ Ready for Tasks 2.2 and 2.3 to build on

---

**This is a BLOCKING task. Tasks 2.2 and 2.3 cannot start until this completes! 🚀**
