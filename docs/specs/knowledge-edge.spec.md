# KnowledgeEdge Specification

**Version:** 1.0.0
**Status:** Specified
**Truth Status:** Specified (code exists in integrity zome; not yet compiled/validated)
**Last Updated:** 2026-03-05

---

## 1. Purpose

A `KnowledgeEdge` represents a typed, confidence-scored relationship between two entities in the Rose Forest knowledge graph. It enables graph-based reasoning over the vector-indexed knowledge commons.

---

## 2. Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | ActionHash | Yes | Source entity hash |
| `to` | ActionHash | Yes | Target entity hash |
| `relationship` | String | Yes | Type of relationship (from allowed set) |
| `confidence` | f32 | Yes | Confidence score in [0.0, 1.0] |

---

## 3. Invariants

1. **INV-KE-001:** `confidence` MUST be in closed interval [0.0, 1.0]
2. **INV-KE-002:** `relationship` MUST be one of: `relates_to`, `supports`, `contradicts`, `heals`, `releases`, `neutralizes`, `recalibrates`
3. **INV-KE-003:** `from` and `to` MUST be valid ActionHashes (enforced by Holochain type system)

---

## 4. Validation Rules

```
VALIDATE knowledge_edge:
  REQUIRE 0.0 <= confidence <= 1.0
  REQUIRE relationship IN ["relates_to", "supports", "contradicts", "heals", "releases", "neutralizes", "recalibrates"]
```

---

## 5. Links

| Link Type | From | To | Purpose |
|-----------|------|----|---------|
| `Edge` | from ActionHash | KnowledgeEdge ActionHash | Graph traversal from source |

---

## 6. Implementation Reference

- **Integrity zome:** `ARF/dnas/rose_forest/zomes/integrity/src/lib.rs`
- **Coordinator zome:** `ARF/dnas/rose_forest/zomes/coordinator/src/lib.rs` (link_edge)

---

## 7. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-05 | Initial specification extracted from integrity zome code |
