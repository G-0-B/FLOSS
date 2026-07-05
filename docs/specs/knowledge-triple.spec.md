# Knowledge Triple Specification

**Version:** 1.1.0  
**Status:** Draft  
**Last Updated:** 2026-07-04  
**Authors:** Anthony (Human), Claude (AI)  
**Canonical copy:** `FLOSS/docs/specs/knowledge-triple.spec.md` (the former `docs/architecture/` duplicate is now a pointer stub)  

> ⚠️ **KNOWN DIVERGENCE (2026-07-04, unresolved — ADR-tier decision pending).**
> This spec.md and its siblings disagree on the core contract:
>
> | Aspect | This spec.md | `knowledge-triple.schema.json` + live integrity zome (`rose_forest/zomes/integrity/src/lib.rs`) |
> |---|---|---|
> | `confidence` domain | `[0.0, 1.0]` (INV-003) | **`[-1.0, +1.0]` signed gradient** (zome-validated; aligned with the analog vote model, ADR-10 v2.0, and the Yumeichan ternary framework) |
> | `predicate` form | registered ontology **URIs** (foaf/dcterms/…) | **short-name enum** (`is_a`, `part_of`, `trained_on`, …) |
> | provenance | structured object (§2.2) | flat `source` AgentPubKey string |
> | `created_at` | ISO 8601 | Holochain Timestamp `[secs, nanos]` |
>
> The implementation + schema represent the *decided* analog-model direction for
> confidence; the predicate form (URI registry vs enum seed vocabulary) is genuinely
> open. Until an ADR reconciles this, treat the **zome as authoritative for the
> confidence domain** and this spec.md as authoritative for extraction semantics
> (what to extract; hedging/negation/dedup rules). Do **not** launch the Pioneer
> fine-tune (WS3) until the predicate-form decision lands — the seed data's URI
> predicates remap mechanically to the enum if that side wins, but the trained
> model's output vocabulary must match the final contract.

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
| `agent` | String | Yes | Creating agent's identifier: a raw agent public key (e.g. Holochain `uhCAk…`) **or a DID URI** (e.g. `did:key:…`). DID form is preferred for new writers — it is the normal form shared with AD4M link authorship and the ADR-12 DID-hardening path; `did:key` wraps the same Ed25519 material as a raw key |
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

### 5.3 Identity: content address vs `id` (normative clarification, v1.1)

The **content address is the truth identity** of a triple wherever a
content-addressed substrate holds it (Holochain entry hash; AD4M expression
address). The `id` field (UUID v7) is a **client-side handle**: time-sortable,
assigned at creation, useful for `parent_triples` references, dedup checks
(INV-010), and pre-publication workflows where no content hash exists yet.
On conflict, the content address wins; two records with different UUIDs but
identical (subject, predicate, object, provenance) content violate INV-010
regardless of their handles.

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

## 6b. Interop Mappings (non-normative, v1.1)

How a `KnowledgeTriple` projects onto plausible integration targets. These are
documentation of compatibility, **not** integration commitments — the
anti-duplication gate (2026-05-09 AD4M/coasys audit delta) still governs any
build decision.

### 6b.1 AD4M

The natural AD4M shape is **not** a bare link but an `Ad4mModel`/SHACL
**subject class** `KnowledgeTriple` with properties for all core fields —
the same pattern the audit delta recommends for Claim/Vote/Decision. Rationale:
bare `LinkExpression`s (`{source, predicate, target}` + author DID + timestamp
+ proof) have no native slot for `confidence` or structured provenance.

| KT field | AD4M slot |
|---|---|
| `subject` / `predicate` / entity `object` | link `source` / `predicate` / `target` (URIs pass through) |
| literal `object` | `literal://` expression, or a typed property on the subject class |
| `confidence`, `provenance.*` | properties on the subject class |
| `provenance.agent` | link/expression `author` (DID — see §2.2) |
| signature | LinkExpression `proof` (AD4M signs at the link layer; FLOSSI0ULLK signs at the provenance-packet layer — same guarantee, different layer) |
| `parent_triples` + INV-007/008 | links + Social-DNA (SHACL preferred, Prolog fallback) inference rules |

### 6b.2 RDF / RDF-star / SPARQL

Core fields serialize directly to an RDF triple (predicates in this spec are
already foaf/dcterms/schema.org URIs). `confidence` and `provenance` are
triple-level metadata: use **RDF-star quoted triples** (or named graphs where
RDF-star is unavailable). Blank-node subjects (`_:`) carry over unchanged.

### 6b.3 W3C PROV-O

| KT provenance | PROV-O |
|---|---|
| `agent` | `prov:wasAttributedTo` |
| `parent_triples` | `prov:wasDerivedFrom` |
| `timestamp` | `prov:generatedAtTime` |
| `source_type`/`source_id` | `prov:Activity` typing + identifier |

(The provenance-packet spec v1.4 already reserves `prov_o_activity_id`;
these two mappings are intentionally aligned.)

### 6b.4 SHACL as the convergence representation

INV-002 (registered predicates) and INV-009 (domain/range) are shape
constraints. The ontology registry SHOULD be compilable to SHACL shapes,
yielding one constraint source enforceable by (a) the Rust integrity zome —
authoritative, (b) AD4M's model layer, and (c) any standard RDF validator.

### 6b.5 Known frictions (accepted for now)

- **Atomic Data** requires typed values; `object` here is an untyped string.
  If the atomic-data hold (seed pack file 03) ever lifts, add an optional
  `object_datatype` field — do not retrofit typing before then.
- **Agent-key encodings**: Holochain raw keys, provenance-packet `D`+43
  base64url, and DIDs coexist across the stack. §2.2's DID preference is the
  convergence direction; existing raw-key records remain valid.

## 7. Related Specifications

- `provenance.spec.md` - Detailed provenance types
- `ontology.spec.md` - Ontology namespace registration
- `inference-rules.spec.md` - How inference generates new triples
- `vector-embedding.spec.md` - Embedding generation and similarity

---

## 8. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-07-04 | Interop patch (generator: claude-fable-5, Fable 5 sprint follow-up): `agent` MAY be a DID URI (§2.2); content-address-vs-UUID identity clarified (§5.3); non-normative interop mappings for AD4M/RDF-star/PROV-O/SHACL + known frictions (§6b); `docs/architecture/` duplicate replaced with pointer stub. No changes to core fields, invariants, or the extraction contract — WS1 evals and WS3 seed data unaffected. |
| 1.0.0 | 2025-12-15 | Initial specification |

---

## 9. ADR References

- **ADR-N-knowledge-triple-structure:** Decision to use S-P-O with mandatory provenance
- **ADR-N-spec-driven-development:** Why spec is source of truth
- **ADR-N-symbolic-first-validation:** Why formal validation gates neural processing
