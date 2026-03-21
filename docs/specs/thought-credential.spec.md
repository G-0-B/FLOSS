# ThoughtCredential Specification

**Version:** 1.0.0
**Status:** Specified
**Truth Status:** Specified (code exists in integrity zome; not yet compiled/validated)
**Last Updated:** 2026-03-05

---

## 1. Purpose

A `ThoughtCredential` represents a signed cognitive artifact — an agent's semantic output with ternary connotation scoring, peer endorsements, and impact measurement. It bridges the YumeiCHAIN concept of "thoughtforms" into the Holochain substrate.

---

## 2. Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | Vec\<f32\> | Yes | Semantic vector (embedding of the thought) |
| `connotation` | i8 | Yes | Ternary score: -1 (negative), 0 (neutral), 1 (positive) |
| `provenance` | AgentPubKey | Yes | Creating agent's public key |
| `resonance` | Vec\<AgentPubKey\> | Yes | Endorsing agents' public keys |
| `impact` | f32 | Yes | Wisdom metric in [0.0, 1.0] |

---

## 3. Invariants

1. **INV-TC-001:** `content` (semantic vector) length MUST be in range [32, 4096]
2. **INV-TC-002:** `connotation` MUST be one of: -1, 0, 1
3. **INV-TC-003:** `impact` MUST be in closed interval [0.0, 1.0]

---

## 4. Validation Rules

```
VALIDATE thought_credential:
  REQUIRE 32 <= content.length <= 4096
  REQUIRE connotation IN [-1, 0, 1]
  REQUIRE 0.0 <= impact <= 1.0
```

---

## 5. Budget Cost

Creating a ThoughtCredential costs 10 RU (Resource Units) from the agent's 24-hour budget of 100 RU.

---

## 6. Implementation Reference

- **Integrity zome:** `ARF/dnas/rose_forest/zomes/integrity/src/lib.rs`
- **Coordinator zome:** `ARF/dnas/rose_forest/zomes/coordinator/src/lib.rs` (create_thought_credential)

---

## 7. Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-05 | Initial specification extracted from integrity zome code |
