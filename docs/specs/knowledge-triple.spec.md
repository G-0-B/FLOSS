# Knowledge Triple Specification

**Version:** 1.0.0  
**Status:** Draft  
**Last Updated:** 2025-12-15  
**Authors:** Anthony (Human), Claude (AI)  

---

## 1. Purpose

A `KnowledgeTriple` represents a single atomic fact in the FLOSSI0ULLK knowledge graph. It captures a relationship between two entities (subject and object) via a predicate, with mandatory provenance tracking to ensure all knowledge is traceable to its source.

**Design principles:**
- **Symbolic-first:** Every triple must be formally validatable against ontology rules
- **Provenance-mandatory:** No knowledge without attribution
- **Confidence-explicit:** Uncertainty is a first-class property, not hidden

---

## 2. Structure

### 2.1 Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID v7 | Yes | Unique identifier (time-sortable) |
| `subject` | URI | Yes | Entity the fact is about |
| `predicate` | URI | Yes | Relationship type (must be from registered ontology) |
| `object` | String | Yes | Value or entity URI |
| `confidence` | Float | Yes | Certainty score in range [0.0, 1.0] |
| `provenance` | Provenance | Yes | Source attribution (see §2.2) |
| `created_at` | Timestamp | Yes | When triple was created (ISO 8601) |
| `embedding` | Vec<f32> | No | Optional vector embedding for semantic search |

### 2.2 Provenance Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_type` | Enum | Yes | One of: `LlmExtraction`, `ManualEntry`, `Inference`, `Import` |
| `source_id` | String | Yes | Identifier of source (model name, user ID, rule ID, import batch) |
| `agent` | String | Yes | Agent public key who created this triple |
| `timestamp` | Timestamp | Yes | When source generated this knowledge |
| `parent_triples` | Vec<UUID> | No | For inferred triples: IDs of premise triples |

---

## 3. Invariants

These MUST hold for all valid `KnowledgeTriple` instances:

### 3.1 Structural Invariants

1. **INV-001:** `subject` MUST be a valid URI or blank node identifier (prefix `_:`)
2. **INV-002:** `predicate` MUST be a URI from a registered ontology namespace
3. **INV-003:** `confidence` MUST be in closed interval [0.0, 1.0]
4. **INV-004:** `created_at` MUST be ≤ current system time
5. **INV-005:** `provenance.timestamp` MUST be ≤ `created_at`

### 3.2 Semantic Invariants

6. **INV-006:** If `source_type` = `LlmExtraction`, then `confidence` MUST be < 1.0
7. **INV-007:** If `source_type` = `Inference`, then `parent_triples` MUST be non-empty
8. **INV-008:** For inferred triples, `confidence` ≤ min(confidence of all parent triples)
9. **INV-009:** `predicate` domain/range constraints must match `subject`/`object` types

### 3.3 Uniqueness Invariants

10. **INV-010:** No two triples may have identical (subject, predicate, object, provenance.source_id)

---

## 4. Validation Rules

### 4.1 On Creation

```
VALIDATE triple:
  REQUIRE valid_uri(triple.subject) OR blank_node(triple.subject)
  REQUIRE ontology_contains(triple.predicate)
  REQUIRE 0.0 <= triple.confidence <= 1.0
  REQUIRE triple.provenance IS NOT NULL
  
  IF triple.provenance.source_type == LlmExtraction:
    REQUIRE triple.confidence < 1.0
    
  IF triple.provenance.source_type == Inference:
    REQUIRE triple.provenance.parent_triples.length > 0
    FOR EACH parent_id IN triple.provenance.parent_triples:
      parent = GET_TRIPLE(parent_id)
      REQUIRE parent EXISTS
      REQUIRE triple.confidence <= parent.confidence
```

### 4.2 On Query

Queries may filter by:
- Subject/predicate/object patterns (SPARQL-like)
- Confidence threshold
- Provenance source type
- Time range (created_at)
- Semantic similarity (if embedding present)

---

## 5. Serialization

### 5.1 JSON Representation

```json
{
  "id": "01939abc-def0-7000-8000-000000000001",
  "subject": "urn:entity:alice",
  "predicate": "http://xmlns.com/foaf/0.1/knows",
  "object": "urn:entity:bob",
  "confidence": 0.85,
  "provenance": {
    "source_type": "LlmExtraction",
    "source_id": "claude-sonnet-4-5-20250929",
    "agent": "uhCAk...",
    "timestamp": "2025-12-15T10:30:00Z",
    "parent_triples": null
  },
  "created_at": "2025-12-15T10:30:05Z",
  "embedding": null
}
```

### 5.2 Holochain Entry

Stored as `hdk_entry_helper` struct with:
- Content-addressable hash as entry ID
- Linked to source chain of creating agent
- DHT-replicated with validation by random peers

---

## 6. Examples

### 6.1 LLM-Extracted Triple

```json
{
  "id": "01939abc-def0-7000-8000-000000000001",
  "subject": "urn:paper:arxiv.2501.12941",
  "predicate": "http://purl.org/dc/terms/subject",
  "object": "Recursive Self-Aggregation",
  "confidence": 0.92,
  "provenance": {
    "source_type": "LlmExtraction",
    "source_id": "claude-sonnet-4-5-20250929",
    "agent": "uhCAkXyz123...",
    "timestamp": "2025-12-15T10:30:00Z"
  },
  "created_at": "2025-12-15T10:30:05Z"
}
```

### 6.2 Manual Entry Triple

```json
{
  "id": "01939abc-def0-7000-8000-000000000002",
  "subject": "urn:person:anthony",
  "predicate": "http://xmlns.com/foaf/0.1/name",
  "object": "Anthony",
  "confidence": 1.0,
  "provenance": {
    "source_type": "ManualEntry",
    "source_id": "user:anthony",
    "agent": "uhCAkAbc456...",
    "timestamp": "2025-12-15T11:00:00Z"
  },
  "created_at": "2025-12-15T11:00:00Z"
}
```

### 6.3 Inferred Triple

```json
{
  "id": "01939abc-def0-7000-8000-000000000003",
  "subject": "urn:person:anthony",
  "predicate": "http://example.org/relatedTo",
  "object": "urn:topic:distributed-systems",
  "confidence": 0.78,
  "provenance": {
    "source_type": "Inference",
    "source_id": "rule:transitive-topic-relation",
    "agent": "uhCAkSystem...",
    "timestamp": "2025-12-15T12:00:00Z",
    "parent_triples": [
      "01939abc-def0-7000-8000-000000000001",
      "01939abc-def0-7000-8000-000000000004"
    ]
  },
  "created_at": "2025-12-15T12:00:05Z"
}
```

---

## 7. Related Specifications

- `provenance.spec.md` - Detailed provenance types
- `ontology.spec.md` - Ontology namespace registration
- `inference-rules.spec.md` - How inference generates new triples
- `vector-embedding.spec.md` - Embedding generation and similarity

---

## 8. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-15 | Initial specification |

---

## 9. ADR References

- **ADR-N-knowledge-triple-structure:** Decision to use S-P-O with mandatory provenance
- **ADR-N-spec-driven-development:** Why spec is source of truth
- **ADR-N-symbolic-first-validation:** Why formal validation gates neural processing
