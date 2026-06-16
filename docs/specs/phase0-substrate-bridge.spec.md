# Phase 0: Substrate Bridge Validation Spec

**Version:** 0.1.0
**Status:** Specified
**Truth Status:** Specified
**Date:** 2026-03-25
**Related:** ADR-0 (Recognition Protocol), ADR-2 (Holochain Substrate), ADR-5 (Cognitive Virology Pattern)
**Friction Tier:** Low (validation only, no new infrastructure)

---

## 1. Purpose

Validate that the Holochain substrate can serve as a trust/provenance layer for cross-agent knowledge coordination. This is the narrowest irreversible test that proves the architecture works end-to-end — from knowledge creation through provenance emission to independent verification.

**This spec does NOT:**
- Build the full orchestration stack
- Integrate AD4M, KERI, hREA, or any LATER-tier component
- Require any new infrastructure beyond what already exists

**This spec DOES:**
- Exercise the existing Rose Forest DNA in a realistic scenario
- Prove that knowledge entries carry verifiable provenance
- Demonstrate independent retrieval from a second agent/node
- Confirm fork-visible conflict resolution

---

## 2. Success Criteria

The substrate bridge is validated when ALL of the following pass:

| # | Criterion | Measurable Gate |
|---|-----------|----------------|
| 1 | **Publish** | Agent A creates a KnowledgeTriple via `assert_triple` and receives an ActionHash |
| 2 | **Provenance** | The created entry's full provenance (agent pubkey, timestamp, signature) is retrievable via `get_triple_record` |
| 3 | **Verify** | Agent B (different agent, same DNA) retrieves the full record by hash via `get_triple_record` and confirms content + provenance match |
| 4 | **Query** | Agent B discovers the entry via `query_triples` (by subject or predicate) without knowing the hash; query results include lightweight provenance (`author`, `created_at`) |
| 5 | **Fork-visible** | Two agents creating conflicting triples (same subject+predicate, different objects) both persist — no silent overwrite |
| 6 | **No privilege** | Neither agent has special authority; both can publish, both can verify |

---

## 3. Test Implementation

### 3.1 Prerequisites

- Holochain conductor running (holonix main-0.4)
- Rose Forest hApp installed with 2 agents (Tryorama handles this)
- Entry types: `KnowledgeTriple` (integrity zome)
- Extern functions: `assert_triple`, `query_triples`, `get_triple_record` (coordinator zome)

### 3.2 Test: Publish + Provenance

```typescript
Agent A calls assert_triple({
  subject: "holochain",
  predicate: "is_a",
  object: "distributed_framework",
  confidence: 0.95
})

ASSERT: returns ActionHash (not error)
ASSERT: get_triple_record(action_hash) returns Record with:
  - entry content matching input
  - action.author == Agent A's pubkey
  - action.timestamp is recent (within 30s)
```

### 3.3 Test: Independent Verification

```typescript
Agent B calls get_triple_record(action_hash) using hash from 3.2

ASSERT: returns same Record
ASSERT: entry content matches what Agent A wrote
ASSERT: provenance (author pubkey) == Agent A (not Agent B)
```

### 3.4 Test: Discovery via Query

```typescript
Agent B calls query_triples({ subject: "holochain", predicate: None })

ASSERT: results contain the triple from 3.2
ASSERT: result includes action_hash, subject, predicate, object, confidence, author, created_at
```

### 3.5 Test: Fork Visibility

```typescript
Agent A calls assert_triple({
  subject: "flossi0ullk",
  predicate: "is_a",
  object: "coordination_protocol",
  confidence: 0.9
})

Agent B calls assert_triple({
  subject: "flossi0ullk",
  predicate: "is_a",
  object: "memetic_system",
  confidence: 0.85
})

Agent A (or B) calls query_triples({ subject: "flossi0ullk" })

ASSERT: results contain BOTH triples (not just one)
ASSERT: both have distinct action_hashes
ASSERT: both query results preserve correct lightweight provenance (different authors)
```

### 3.6 Test: No Privilege

```typescript
ASSERT: Agent A and Agent B use identical zome calls (no admin-only functions)
ASSERT: Neither agent's entries are prioritized in query results by authority
```

---

## 4. Implementation Notes

### What Already Exists

- `KnowledgeTriple` entry type with validation (integrity zome)
- `assert_triple` extern with ontology validation + budget check (coordinator zome)
- `query_triples` extern with subject/predicate query (coordinator zome)
- `TriplesBySubject` and `TriplesByPredicate` link types for DHT discovery
- Tryorama test scaffold (`ARF/tests/tryorama/`)
- Budget system tracking RU consumption per agent

### What Needs To Be Written

1. **Tryorama 2-agent test file** — `ARF/tests/tryorama/substrate_bridge.test.ts`
   - Spawns 2 agents in same DNA
   - Runs tests 3.2 through 3.6 sequentially
   - Reports pass/fail for each criterion

2. **Provenance retrieval helper** — `get_triple_record` is the canonical full-record retrieval API for Criteria 2 and 3 because it returns the signed action, entry, author, and timestamp in a single authoritative record. `query_triples` still needs lightweight provenance for Criteria 4 and 5, so `TripleResult` must expose `author: AgentPubKey` and `created_at: Timestamp`, mapped from the existing `KnowledgeTriple.source` and `KnowledgeTriple.created_at` fields that the integrity zome already persists. Rejected option `get_triple_with_provenance` because `get_triple_record` already covers the full-record path and adding another retrieval extern would increase maintenance without improving verifiability.

   Mapping:

   ```text
   KnowledgeTriple.source      -> TripleResult.author
   KnowledgeTriple.created_at  -> TripleResult.created_at
   ```

   (`get_triple_record` is the full-record verification path; `query_triples` is the discovery path that returns lightweight provenance without requiring a second round-trip.)

### What This Does NOT Require

- No new entry types
- No new link types
- No AD4M, KERI, hREA, IPFS, or any LATER-tier integration
- No new infrastructure or conductor configuration
- No changes to the integrity zome validation rules

---

## 5. Constraints (from v2.0.0 Landscape Report)

- **k<=5 agents** — This test uses k=2, well within the Silo-Bench safe zone
- **Output verification > process verification** — Tests verify outputs (entry content, provenance fields), not agent reasoning trajectories
- **SDD constitution** — This spec exists before code. Tests will be written before implementation of any new helpers.

---

## 6. Definition of Done

- [ ] Provenance retrieval implemented: `TripleResult` extended with `author` and `created_at` fields (option b from §4) — prerequisite for Criteria 3, 4, and 5, and for ADR-2 acceptance evidence in HARVEST_LOG.md
- [ ] `substrate_bridge.test.ts` written with all 6 criteria as test cases
- [ ] All 6 tests pass against running Holochain conductor
- [ ] Results logged in `docs/governance/HARVEST_LOG.md` as substrate bridge validation
- [ ] ADR-2 (Holochain Substrate) updated from Proposed to Accepted (evidence: this test passing)

---

## 7. What This Unlocks

When this spec passes:
- **ADR-2 moves to Accepted** — Holochain is confirmed as substrate, not just proposed
- **Phase 1 ontology work is validated end-to-end** — KnowledgeTriples work across agents
- **HARVEST Protocol has a concrete first measurement** — substrate bridge as HARVEST Cycle 1
- **ADR-5 Evidence Gate item 2** gets partial credit (HARVEST cycle with measurable output)
