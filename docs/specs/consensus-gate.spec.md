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

6. **INV-006:** `Decision.outcome == APPROVED` requires the blast-radius quorum to be met, all votes ≥ 0, and:
   - `Local`: at least 1 vote = +1
   - `Module` / `System`: at least 2 votes = +1
   - `Substrate`: all votes = +1 (unanimous)
7. **INV-007:** `Decision.outcome == REJECTED` requires at least 1 vote = -1
8. **INV-008:** `Decision.outcome == DEFERRED` means quorum reached with mix of 0 and +1 but insufficient +1 for approval
9. **INV-009:** `Decision.outcome == OVERRIDDEN` requires `override_by` to be a registered human identity
10. **INV-010:** No Claim may be decided twice; a DEFERRED decision MAY be superseded by an override, which replaces (not appends to) the lifecycle state

### 3.3 Provenance

11. **INV-011:** Every Vote MUST carry voter identity
12. **INV-012:** Every Decision MUST record all Votes that were considered
13. **INV-013:** When `adr_ref` is set, the ADR file MUST exist at that path

---

## 4. Decision Rules

### 4.1 Tallying Logic

```text
TALLY votes, claim:
  IF any vote == -1:
    RETURN REJECTED
  IF claim.blast_radius == Substrate:
    IF all votes == +1 AND len(votes) >= quorum_min(Substrate):
      RETURN APPROVED
    RETURN DEFERRED
  IF len(votes) < quorum_min(claim.blast_radius):
    RETURN DEFERRED (insufficient quorum)
  IF count(votes == +1) >= 2 AND all votes >= 0:
    RETURN APPROVED
  IF claim.blast_radius == Local AND count(votes == +1) >= 1:
    RETURN APPROVED
  RETURN DEFERRED
```

### 4.2 Override Path

Override is a **superseding transition** on a `DEFERRED` decision, not a second decision on the same claim (see INV-010). A registered human voter supplies an override rationale and the gate emits a new `Decision` with `outcome=OVERRIDDEN` that replaces the prior `DEFERRED` record in the claim's lifecycle state:

```text
OVERRIDE prior_decision, claim, human_voter, rationale:
  REQUIRE prior_decision.claim_id == claim.id        # E_OVERRIDE_CLAIM_MISMATCH
  REQUIRE prior_decision.outcome == DEFERRED         # E_OVERRIDE_INVALID_STATE
  REQUIRE OVERRIDE_ALLOWED[claim.blast_radius]       # E_OVERRIDE_NOT_ALLOWED (non-substrate only)
  REQUIRE human_voter, rationale non-empty           # E_OVERRIDE_NOT_HUMAN
  REQUIRE human_voter not in prior_decision.votes    # E_OVERRIDE_DUPLICATE
  EMIT superseding Decision with outcome=OVERRIDDEN, override_by=human_voter,
       votes=prior_decision.votes + [override_vote]
```

`Substrate` blast radius never exposes an override path; any attempt raises `E_OVERRIDE_NOT_ALLOWED`. Override is itself recorded as its own ADR for provenance.

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
- **E_OVERRIDE_NOT_HUMAN:** Override attempted by non-human voter (missing `human_voter`/`rationale`)
- **E_OVERRIDE_INVALID_STATE:** Override attempted on non-DEFERRED decision
- **E_OVERRIDE_NOT_ALLOWED:** Override attempted on a blast radius that disallows it (e.g. `Substrate`)
- **E_OVERRIDE_CLAIM_MISMATCH:** `prior_decision.claim_id` does not match `claim.id`
- **E_OVERRIDE_DUPLICATE:** Override voter has already cast a vote on this claim
- **E_VOTE_DUPLICATE:** Two voters with the same identity in one `decide()` call
- **E_QUORUM_INSUFFICIENT:** Blast radius requires more voters than available

---

## 6. Test Vectors

### 6.1 Unanimous Approval

```text
Claim: { proposal_type: "CodeChange", blast_radius: "Module", summary: "fix typo" }
Votes: [+1, +1, +1]
Expected: outcome=APPROVED
```

### 6.2 Single Rejection Vetoes

```text
Claim: { proposal_type: "SpecChange", blast_radius: "System", summary: "remove invariant" }
Votes: [+1, +1, -1]
Expected: outcome=REJECTED (INV-007)
```

### 6.3a Approval With One Abstention

```text
Claim: { proposal_type: "AdrChange", blast_radius: "System", summary: "promote to Accepted" }
Votes: [+1, +1, 0]
Expected: outcome=APPROVED (quorum=3 met, 2 votes = +1, all votes ≥ 0 — INV-006)
```

### 6.3b Deferred Via Too Many Abstentions

```text
Claim: { proposal_type: "AdrChange", blast_radius: "System", summary: "promote to Accepted" }
Votes: [+1, 0, 0]
Expected: outcome=DEFERRED (quorum met but only 1 vote = +1)
```

### 6.4 Substrate Change Requires Unanimous

```text
Claim: { proposal_type: "CodeChange", blast_radius: "Substrate", summary: "change DNA entry format" }
Votes: [+1, +1, 0]
Expected: outcome=DEFERRED (substrate requires all +1, no override)
```

### 6.5 Human Override on Deferred

```text
Claim: { proposal_type: "ConfigChange", blast_radius: "Module" }
Votes: [+1, 0]
Decision: outcome=DEFERRED
Override: { override_by: "human-anthony", rationale: "time-sensitive fix" }
Expected: outcome=OVERRIDDEN, adr_ref recorded
```

### 6.6 Insufficient Quorum

```text
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
