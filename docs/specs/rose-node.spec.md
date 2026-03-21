# RoseNode Specification

**Version:** 1.0.0
**Status:** Specified
**Truth Status:** Specified (code exists in integrity zome; not yet compiled/validated)
**Last Updated:** 2026-03-05

---

## 1. Purpose

A `RoseNode` is the atomic unit of knowledge in the Rose Forest knowledge commons. It represents a signed, embedded piece of content with mandatory provenance metadata, stored as a Holochain entry in the agent's source chain and replicated via DHT.

**Design principles:**
- **Provenance-mandatory:** Every node must declare the embedding model that produced its vector
- **License-enforced:** Only OSI-approved or CC-BY licenses accepted (validation at the edge)
- **Embedding-required:** Content must carry a vector embedding for semantic search

---

## 2. Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | String | Yes | The knowledge content (text) |
| `embedding` | Vec\<f32\> | Yes | Vector embedding of the content |
| `license` | String | Yes | OSI license identifier or CC-BY-4.0 |
| `metadata` | BTreeMap\<String, String\> | Yes | Key-value metadata (must include `model_id` and `model_card_hash`) |

---

## 3. Invariants

1. **INV-RN-001:** `license` MUST be one of: `MIT`, `Apache-2.0`, `BSD-3-Clause`, `MPL-2.0`, `CC-BY-4.0`
2. **INV-RN-002:** `embedding` length MUST be in range [32, 4096]
3. **INV-RN-003:** `metadata` MUST contain key `model_id` with a non-empty value
4. **INV-RN-004:** `metadata` MUST contain key `model_card_hash` with a value starting with `sha256:`

---

## 4. Validation Rules

```
VALIDATE rose_node:
  REQUIRE license IN ["MIT", "Apache-2.0", "BSD-3-Clause", "MPL-2.0", "CC-BY-4.0"]
  REQUIRE 32 <= embedding.length <= 4096
  REQUIRE metadata["model_id"] IS NOT NULL AND NOT EMPTY
  REQUIRE metadata["model_card_hash"] STARTS WITH "sha256:"
```

---

## 5. Links

| Link Type | From | To | Purpose |
|-----------|------|----|---------|
| `AllNodes` | Path("all_nodes") | RoseNode ActionHash | Global discovery |
| `ShardMember` | Path("shard.\<prefix\>") | RoseNode ActionHash | Semantic neighborhood |

---

## 6. Implementation Reference

- **Integrity zome:** `ARF/dnas/rose_forest/zomes/integrity/src/lib.rs` (struct + validation)
- **Coordinator zome:** `ARF/dnas/rose_forest/zomes/coordinator/src/lib.rs` (add_knowledge, vector_search)

---

## 7. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-05 | Initial specification extracted from integrity zome code |
