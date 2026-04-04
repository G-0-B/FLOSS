# Consensus Gate Specification (Seam 1)

**Version:** 0.1.0
**Status:** Draft
**Last Updated:** 2026-04-04
**ADR:** ADR-6 Seam 1
**Authors:** FLOSSI0ULLK collective

---

## 1. Purpose

The Consensus Gate intercepts proposed structural changes from external agents (omo, OMX, Claude Code, etc.) and routes them through FLOSSI0ULLK's ternary consensus protocol before allowing execution. It is the first integration seam from ADR-6 because it establishes the MCP communication channel that Seams 2-5 also depend on.

**Design principles:**
- **Reversible:** Disabling the gate must not break the hosting agent
- **Symbolic-first:** Every Claim validates against JSON Schema before vote routing
- **Provenance-mandatory:** Every Decision records voter identity, vote, and rationale
- **Ternary-native:** Votes are {+1, 0, -1}; decisions are {APPROVED, DEFERRED, REJECTED}

---

## 2. Structure

### 2.1 Claim

A Claim is a proposed change submitted to the gate. It wraps the proposal with metadata sufficient for ternary evaluation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID v7 | Yes | Unique identifier (time-sortable) |
| `proposer` | String | Yes | Agent public key or identifier |
| `proposal_type` | Enum | Yes | One of: `CodeChange`, `ConfigChange`, `SpecChange`, `AdrChange`, `Other` |
| `summary` | String | Yes | Human-readable one-line summary (max 200 chars) |
| `body` | String | Yes | Full proposal content (diff, config, prose) |
| `truth_status` | Enum | Yes | Initial label: `Unverified` (always, until consensus) |
| `blast_radius` | Enum | Yes | One of: `Local`, `Module`, `System`, `Substrate` |
| `evidence` | Vec<EvidenceRef> | No | Links to supporting specs, tests, prior ADRs |
| `submitted_at` | Timestamp | Yes | ISO 8601 |

### 2.2 Vote

A Vote is a single voter's ternary evaluation of a Claim.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `voter` | String | Yes | Voter public key or identifier |
| `vote` | Integer | Yes | One of: `+1` (approve), `0` (abstain/defer), `-1` (reject) |
| `rationale` | String | Yes | Why this vote (max 1000 chars) |
| `voted_at` | Timestamp | Yes | ISO 8601 |

### 2.3 Decision

A Decision is the aggregated outcome of all Votes for a Claim.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim_id` | UUID v7 | Yes | Claim being decided |
| `outcome` | Enum | Yes | One of: `APPROVED`, `DEFERRED`, `REJECTED`, `OVERRIDDEN` |
| `votes` | Vec<Vote> | Yes | All votes received |
| `decided_at` | Timestamp | Yes | ISO 8601 |
| `adr_ref` | String | No | Path to ADR stub recording this decision |
| `override_by` | String | No | Human identity if `outcome == OVERRIDDEN` |

---

## 3. Invariants

### 3.1 Structural

1. **INV-001:** `Claim.id` MUST be UUID v7
2. **INV-002:** `Vote.vote` MUST be in set {-1, 0, +1}
3. **INV-003:** `Claim.truth_status` MUST be `Unverified` on submission
4. **INV-004:** `Claim.summary` MUST be ≤ 200 characters
5. **INV-005:** `Vote.rationale` MUST be non-empty and ≤ 1000 characters

### 3.2 Semantic

6. **INV-006:** `Decision.outcome == APPROVED` requires at least 3 votes AND all votes ≥ 0 AND at least 2 votes = +1
7. **INV-007:** `Decision.outcome == REJECTED` requires at least 1 vote = -1
8. **INV-008:** `Decision.outcome == DEFERRED` means quorum reached with mix of 0 and +1 but insufficient +1 for approval
9. **INV-009:** `Decision.outcome == OVERRIDDEN` requires `override_by` to be a registered human identity
10. **INV-010:** No Claim may be decided twice (decisions are immutable)

### 3.3 Provenance

11. **INV-011:** Every Vote MUST carry voter identity
12. **INV-012:** Every Decision MUST record all Votes that were considered
13. **INV-013:** When `adr_ref` is set, the ADR file MUST exist at that path

---

## 4. Decision Rules

### 4.1 Tallying Logic

```
TALLY votes:
  IF any vote == -1:
    RETURN REJECTED
  IF len(votes) < quorum_min (default 3):
    RETURN DEFERRED (insufficient quorum)
  IF count(votes == +1) >= 2 AND all votes >= 0:
    RETURN APPROVED
  ELSE:
    RETURN DEFERRED
```

### 4.2 Override Path

When `outcome == DEFERRED` due to +1/+1/0 pattern, a registered human voter may issue an override:

```
OVERRIDE claim:
  REQUIRE human_identity(override_voter)
  REQUIRE prior_decision.outcome == DEFERRED
  REQUIRE override_rationale non-empty
  RECORD new Decision with outcome=OVERRIDDEN, override_by=human_id
```

Override is itself recorded as its own ADR for provenance.

### 4.3 Blast Radius Gates

| Blast Radius | Min Voters | Override Allowed |
|---|---|---|
| `Local` | 1 | Yes |
| `Module` | 2 | Yes |
| `System` | 3 | Yes |
| `Substrate` | 3 | No (substrate changes require unanimous +1) |

---

## 5. Error Codes

- **E_CLAIM_INVALID_SCHEMA:** Claim fails JSON Schema validation
- **E_CLAIM_DUPLICATE:** Claim with this ID already exists
- **E_VOTE_INVALID_RANGE:** Vote value not in {-1, 0, +1}
- **E_VOTE_UNKNOWN_VOTER:** Voter not in registered voter set
- **E_DECISION_IMMUTABLE:** Attempt to re-decide an already-decided claim
- **E_OVERRIDE_NOT_HUMAN:** Override attempted by non-human voter
- **E_OVERRIDE_INVALID_STATE:** Override attempted on non-DEFERRED decision
- **E_QUORUM_INSUFFICIENT:** Blast radius requires more voters than available

---

## 6. Test Vectors

### 6.1 Unanimous Approval

```
Claim: { proposal_type: "CodeChange", blast_radius: "Module", summary: "fix typo" }
Votes: [+1, +1, +1]
Expected: outcome=APPROVED
```

### 6.2 Single Rejection Vetoes

```
Claim: { proposal_type: "SpecChange", blast_radius: "System", summary: "remove invariant" }
Votes: [+1, +1, -1]
Expected: outcome=REJECTED (INV-007)
```

### 6.3 Deferred via Abstention

```
Claim: { proposal_type: "AdrChange", blast_radius: "System", summary: "promote to Accepted" }
Votes: [+1, +1, 0]
Expected: outcome=DEFERRED (no -1, but also not 2+ votes = +1 with all non-negative AND satisfying approval rule? Wait: all >= 0, 2 are +1 -> APPROVED per INV-006)
```

Correction: `[+1, +1, 0]` IS approved per INV-006 (2 votes = +1, all votes ≥ 0). Deferred requires fewer than 2 votes = +1.

```
Claim: { proposal_type: "AdrChange", blast_radius: "System", summary: "promote to Accepted" }
Votes: [+1, 0, 0]
Expected: outcome=DEFERRED (only 1 vote = +1)
```

### 6.4 Substrate Change Requires Unanimous

```
Claim: { proposal_type: "CodeChange", blast_radius: "Substrate", summary: "change DNA entry format" }
Votes: [+1, +1, 0]
Expected: outcome=DEFERRED (substrate requires all +1, no override)
```

### 6.5 Human Override on Deferred

```
Claim: { proposal_type: "ConfigChange", blast_radius: "Module" }
Votes: [+1, 0]
Decision: outcome=DEFERRED
Override: { override_by: "human-anthony", rationale: "time-sensitive fix" }
Expected: outcome=OVERRIDDEN, adr_ref recorded
```

### 6.6 Insufficient Quorum

```
Claim: { proposal_type: "CodeChange", blast_radius: "System" }
Votes: [+1, +1]  # Only 2 voters, System requires 3
Expected: outcome=DEFERRED (E_QUORUM_INSUFFICIENT context)
```

---

## 7. Integration with omo Hook System

The gate is invoked by omo's tool-guard hook tier (see ADR-6 Seam 1). Hook signature:

```typescript
createConsensusGateHook({
  endpoint: "mcp://localhost:PORT/consensus-gate",
  quorum: { local: 1, module: 2, system: 3, substrate: 3 },
  blocking: true,  // Block tool execution until decision
  on_decision: (decision) => { /* log, notify, etc */ }
})
```

When a tool execution is intercepted:
1. Hook constructs Claim from tool call args + AST diff
2. Hook POSTs Claim to MCP endpoint
3. Hook blocks (up to timeout) awaiting Decision
4. If `APPROVED` or `OVERRIDDEN`: tool proceeds
5. If `REJECTED`: tool call cancelled, rationale returned to agent
6. If `DEFERRED`: tool call queued, agent notified

---

## 8. Implementation Path

1. `packages/orchestrator/claim_schema.py` — Pydantic models
2. `packages/orchestrator/consensus_gate.py` — Gate logic (tally, override, ADR write)
3. `packages/orchestrator/test_consensus_gate.py` — All 6 test vectors + error cases
4. `docs/specs/consensus-gate.schema.json` — JSON Schema for Claim/Vote/Decision

---

## 9. Open Questions

- **Voter registration:** How are voters (AI or human) registered? Deferred to Seam 5 (OpenClaw gateway handles identity).
- **Timeout behavior:** If quorum not reached within T seconds, default to DEFERRED. T configurable per blast radius.
- **Vote collection mechanism:** Synchronous (all voters respond before decision) vs streaming (decide as votes arrive, early-exit on -1). Start synchronous.
- **ADR path for decision records:** `docs/adr/decisions/YYYY-MM-DD-<claim-id>.md` proposed. Confirm in prototype.
