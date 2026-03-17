# Task 2.2: Implement AI/ML Domain Ontology

**Phase**: 2 (Foundation)
**Estimated Time**: 6 hours
**Complexity**: MEDIUM
**Dependencies**: Task 2.1 (Base Ontology) MUST complete first
**Parallelizable**: Yes (with Task 2.3 after 2.1 completes)

---

## 🎯 Objective

Extend the base ontology with AI/ML domain-specific types and relations. Enable automatic inference of capabilities (e.g., if Model A improves Model B, and B can do X, then A can do X).

---

## 📍 Context

From ACTION_PLAN (Week 2):
> Add AI/ML specific knowledge structure. Define AIModel, LLM, Dataset types. Write axioms for capability inheritance. Test with real data and verify inference works.

This builds on Task 2.1's foundation to create a practical domain ontology for AI systems coordination.

---

## ✅ Acceptance Criteria

1. **Define AI/ML types**
   - AIModel, LLM, Dataset, Training Run, Capability
   - Agent (human, AI assistant, autonomous agent)
   - Extends base "Entity" type from Task 2.1

2. **Define AI/ML relations**
   - trained_on(Model, Dataset)
   - improves_upon(Model, Model)
   - capable_of(Model, Capability)
   - has_capability(Agent, Capability)
   - evaluated_on(Model, Benchmark)

3. **Implement inference axioms**
   - **Transitivity**: If A improves B and B improves C, then A improves C
   - **Capability Inheritance**: If A improves B and B capable_of X, then A capable_of X
   - **Type Propagation**: If A trained_on Dataset of type T, then A has_capability(T-tasks)

4. **Add validation constraints**
   - Models can only be trained_on Datasets
   - Only Models can improve_upon other Models
   - Capabilities must exist in capability ontology

5. **Bootstrap domain ontology**
   - Add real examples: GPT-4, Claude, common datasets
   - Verify inference generates correct conclusions

6. **Tests**
   - Test each relation validates correctly
   - Test inference rules produce correct inferences
   - Test invalid domain/range rejected
   - Coverage ≥80%

---

## 🔧 Implementation Guidance

### Step 1: Extend OntologyType Definitions

Add to `ARF/dnas/rose_forest/zomes/ontology_integrity/src/lib.rs`:

```rust
/// Bootstrap AI/ML domain ontology
pub fn bootstrap_ai_ml_ontology() -> ExternResult<()> {
    let ai_ml_types = vec![
        OntologyType {
            type_id: "AIModel".into(),
            name: "AI Model".into(),
            parent: Some("Agent".into()),
            description: "Artificial intelligence model".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "LLM".into(),
            name: "Large Language Model".into(),
            parent: Some("AIModel".into()),
            description: "Large language model".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "Dataset".into(),
            name: "Dataset".into(),
            parent: Some("Entity".into()),
            description: "Training or evaluation dataset".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "Capability".into(),
            name: "Capability".into(),
            parent: Some("Concept".into()),
            description: "A capability or skill".into(),
            created_at: Timestamp::now(),
        },
        OntologyType {
            type_id: "Benchmark".into(),
            name: "Benchmark".into(),
            parent: Some("Entity".into()),
            description: "Evaluation benchmark".into(),
            created_at: Timestamp::now(),
        },
    ];

    // Store types (in real implementation, commit to DHT)
    for ai_type in ai_ml_types {
        debug!("Bootstrapped AI/ML type: {}", ai_type.name);
    }

    Ok(())
}
```

### Step 2: Define AI/ML Relations

```rust
/// Get AI/ML domain relations
pub fn get_ai_ml_relations() -> Vec<OntologyRelation> {
    vec![
        OntologyRelation {
            relation_id: "trained_on".into(),
            name: "trained on".into(),
            domain: vec!["AIModel".into(), "LLM".into()],
            range: vec!["Dataset".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Model was trained on dataset".into(),
            created_at: Timestamp::now(),
        },
        OntologyRelation {
            relation_id: "improves_upon".into(),
            name: "improves upon".into(),
            domain: vec!["AIModel".into(), "LLM".into()],
            range: vec!["AIModel".into(), "LLM".into()],
            is_transitive: true,  // Important for inference!
            is_symmetric: false,
            is_reflexive: false,
            description: "Model improves upon another model".into(),
            created_at: Timestamp::now(),
        },
        OntologyRelation {
            relation_id: "capable_of".into(),
            name: "capable of".into(),
            domain: vec!["AIModel".into(), "LLM".into(), "Agent".into()],
            range: vec!["Capability".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Model or agent has capability".into(),
            created_at: Timestamp::now(),
        },
        OntologyRelation {
            relation_id: "evaluated_on".into(),
            name: "evaluated on".into(),
            domain: vec!["AIModel".into(), "LLM".into()],
            range: vec!["Benchmark".into()],
            is_transitive: false,
            is_symmetric: false,
            is_reflexive: false,
            description: "Model evaluated on benchmark".into(),
            created_at: Timestamp::now(),
        },
    ]
}
```

### Step 3: Implement Inference Engine

```rust
/// Infer new knowledge from existing triples using axioms
pub fn infer_from_axioms(triple: &KnowledgeTriple) -> Vec<KnowledgeTriple> {
    let mut inferred = vec![];

    match triple.predicate.as_str() {
        "improves_upon" => {
            // Axiom: Capability Inheritance
            // If A improves B, and B capable_of X, then A capable_of X
            let capabilities = query_capabilities(&triple.object);
            for capability in capabilities {
                inferred.push(KnowledgeTriple {
                    subject: triple.subject.clone(),
                    predicate: "capable_of".into(),
                    object: capability,
                    confidence: triple.confidence * 0.9,  // Slightly lower confidence
                    source: triple.source.clone(),
                    created_at: Timestamp::now(),
                });
            }

            // Axiom: Transitivity of improves_upon
            // If A improves B, and B improves C, then A improves C
            let improved_models = query_improved_models(&triple.object);
            for model in improved_models {
                inferred.push(KnowledgeTriple {
                    subject: triple.subject.clone(),
                    predicate: "improves_upon".into(),
                    object: model,
                    confidence: triple.confidence * 0.8,  // Lower confidence for transitive
                    source: triple.source.clone(),
                    created_at: Timestamp::now(),
                });
            }
        }
        _ => {
            // No inference rules for other predicates yet
        }
    }

    inferred
}

/// Query capabilities of a model (stub)
fn query_capabilities(model_id: &str) -> Vec<String> {
    // TODO: Query DHT for (model_id, capable_of, X) triples
    vec![]
}

/// Query models that a model improves upon (stub)
fn query_improved_models(model_id: &str) -> Vec<String> {
    // TODO: Query DHT for (model_id, improves_upon, X) triples
    vec![]
}
```

### Step 4: Add Real Examples

```rust
/// Bootstrap with real AI/ML examples
pub fn bootstrap_ai_examples() -> ExternResult<()> {
    // Example models
    let examples = vec![
        // GPT-4 is a LLM
        ("GPT-4", "is_a", "LLM"),
        // Claude Sonnet 4.5 is a LLM
        ("Claude-Sonnet-4.5", "is_a", "LLM"),
        // Sonnet 4.5 improves upon Sonnet 4
        ("Claude-Sonnet-4.5", "improves_upon", "Claude-Sonnet-4"),
        // Sonnet 4 is capable of coding
        ("Claude-Sonnet-4", "capable_of", "coding"),
        // (Inference should derive: Sonnet 4.5 capable_of coding)
    ];

    for (s, p, o) in examples {
        debug!("Bootstrapped example: ({}, {}, {})", s, p, o);
    }

    Ok(())
}
```

### Step 5: Update get_relation() Function

Update the `get_relation()` function from Task 2.1 to include AI/ML relations:

```rust
fn get_relation(relation_id: &str) -> Result<OntologyRelation, OntologyError> {
    // Check base relations first (from Task 2.1)
    match relation_id {
        "is_a" | "part_of" => {
            // Return base relations
        }
        _ => {
            // Check AI/ML relations
            let ai_ml_rels = get_ai_ml_relations();
            for rel in ai_ml_rels {
                if rel.relation_id == relation_id {
                    return Ok(rel);
                }
            }
            Err(OntologyError::UnknownRelation(relation_id.to_string()))
        }
    }
}
```

---

## 🧪 Testing Checklist

### Test 1: Domain/Range Validation
```rust
#[test]
fn test_trained_on_validates_types() {
    // Valid: LLM trained_on Dataset
    let valid = KnowledgeTriple {
        subject: "GPT-4".into(),
        predicate: "trained_on".into(),
        object: "WebText".into(),
        confidence: 1.0,
        source: fake_agent(),
        created_at: Timestamp::now(),
    };
    assert!(validate_triple(&valid).is_ok());

    // Invalid: Dataset trained_on LLM (wrong direction)
    let invalid = KnowledgeTriple {
        subject: "WebText".into(),  // Dataset can't be trained
        predicate: "trained_on".into(),
        object: "GPT-4".into(),
        confidence: 1.0,
        source: fake_agent(),
        created_at: Timestamp::now(),
    };
    assert!(validate_triple(&invalid).is_err());
}
```

### Test 2: Capability Inference
```rust
#[test]
fn test_capability_inheritance() {
    // Given: Sonnet-4 capable_of coding
    // Given: Sonnet-4.5 improves_upon Sonnet-4
    let improves = KnowledgeTriple {
        subject: "Claude-Sonnet-4.5".into(),
        predicate: "improves_upon".into(),
        object: "Claude-Sonnet-4".into(),
        confidence: 1.0,
        source: fake_agent(),
        created_at: Timestamp::now(),
    };

    // When: Infer new knowledge
    let inferred = infer_from_axioms(&improves);

    // Then: Should infer Sonnet-4.5 capable_of coding
    assert!(inferred.iter().any(|t|
        t.subject == "Claude-Sonnet-4.5" &&
        t.predicate == "capable_of" &&
        t.object == "coding"
    ));
}
```

### Test 3: Transitivity
```rust
#[test]
fn test_improves_upon_transitivity() {
    // A improves B, B improves C => A improves C
    let a_improves_b = KnowledgeTriple {
        subject: "Model-A".into(),
        predicate: "improves_upon".into(),
        object: "Model-B".into(),
        confidence: 1.0,
        source: fake_agent(),
        created_at: Timestamp::now(),
    };

    let inferred = infer_from_axioms(&a_improves_b);

    // Should include transitive improvements
    // (test depends on query_improved_models returning Model-C)
}
```

---

## 📝 Completion Checklist

- [ ] AI/ML types defined (AIModel, LLM, Dataset, Capability, Benchmark)
- [ ] AI/ML relations defined (trained_on, improves_upon, capable_of, evaluated_on)
- [ ] Inference axioms implemented
- [ ] Capability inheritance works
- [ ] Transitivity implemented
- [ ] Real examples bootstrapped (GPT-4, Claude, etc.)
- [ ] Domain/range validation works
- [ ] All tests pass
- [ ] Coverage ≥80%
- [ ] Completion report created

---

## 🚫 Out of Scope

- ❌ Complete LLM model registry
- ❌ Automatic capability detection
- ❌ Benchmark score tracking
- ❌ Performance optimization
- ❌ Web scraping for model data

---

## 📋 Files to Modify

- `ARF/dnas/rose_forest/zomes/ontology_integrity/src/lib.rs` - Add AI/ML ontology
- `ARF/dnas/rose_forest/zomes/ontology_integrity/src/inference.rs` - Inference engine (new file)
- `ARF/dnas/rose_forest/zomes/ontology_integrity/src/tests.rs` - Add tests
- `ARF/dev/completion/phase2_task2.md` - Completion report

---

## 🎓 Success Metrics

1. ✅ Real-world example works: "Sonnet-4.5 improves Sonnet-4" → infers capabilities
2. ✅ Invalid triples rejected (e.g., Dataset improving LLM)
3. ✅ Transitive inference works
4. ✅ Capability inheritance works
5. ✅ Ready for Task 2.3 integration

---

**Wait for Task 2.1 to complete before starting! 🚀**
