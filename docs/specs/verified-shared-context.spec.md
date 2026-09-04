<!-- PROVENANCE BANNER -- read before treating anything below as canon. -->

> **Status: Proposed / Specified. Nothing here is implemented.**
> Promoted 2026-09-04 from the v0.4 continuation bundle
> (`.toilet/flossi0ullk_v0_4_continuation_package/`) after a reuse check
> against repo canon.
>
> **Registered at tier 1, which means the reuse block is recorded but NOT
> validated.** Tier 2 requires an independent review across at least three
> provider surfaces and four model families; this was one reviewer on one
> surface, and the consensus gateway was unreachable throughout. **Promote to
> tier 2 with a real adversarial review before implementing any schema here.**
>
> Four schemas changed during that check -- a rename, an added enum, a
> re-notated verdict, and a reused risk vocabulary. Evidence and rationale:
> [`REUSE-MAP.md`](../reviews/2026-09-04-v04-continuation-bundle/REUSE-MAP.md).
> Schemas live in [`verified-shared-context/`](verified-shared-context/).

---

---
id: "verified-shared-context-runtime"
version: "0.1.0"
kind: "architecture_design_spec"
status: "Proposed"
truth_status: "Specified"
updated: "2026-09-03"
evidence_sources:
  - "DELM"
  - "LedgerMind"
  - "DECENTMEM"
  - "Agentic P2P"
  - "Offline Evidence Bundles"
  - "Drop Hierarchy and Roles"
  - "Textual Backpropagation"
  - "FLOSSI0ULLK provenance-packet.spec v1.4"
rollback_plan: "Do not implement or remove experimental adapters; existing room/runtime remains authoritative."
friction_tier: "high"
---

# Design Spec v0.1 — Verified Shared Context Runtime

## 1. Purpose

Define the minimum interfaces needed for asynchronous multi-agent coordination where useful progress can be shared without a central cognitive bottleneck, while preventing unsupported claims from becoming reusable collective truth.

## 2. Non-goals

This spec does **not** define:

- a new identity system;
- a replacement for Provenance Packet v1.4;
- a replacement for consent/source-chain contracts;
- a global persistent memory for all agents;
- a full WAN P2P transport;
- a self-modifying runtime;
- a claim that cryptographic provenance implies semantic correctness.

## 3. Components

### 3.1 Task Queue

Stores pending/claimed/completed work.

Required properties:

- atomic claim/lease semantics;
- release/retry;
- dependency-aware readiness where needed;
- bounded lease expiry/recovery;
- no task can be silently owned by two agents unless multi-owner semantics are explicit.

### 3.2 Shared Context

Contains only **admitted reusable problem state**, not arbitrary chat history.

Entry type: `SharedGist`.

A gist MUST:

- be compact;
- reference one or more admitted claims;
- be unfoldable to supporting evidence or a deeper summary;
- carry lifecycle status;
- preserve qualifiers needed to avoid distortion;
- never be admitted merely because an agent said it confidently.

### 3.3 Structured Evidence Ledger

Per task/session ledger containing evidence and dependencies.

`LedgerEntry.kind` SHOULD distinguish at least:

- `perception`
- `retrieval`
- `tool_result`
- `derivation`

Lifecycle:

- `active`
- `stale`
- `conflicted`
- `dropped`

Invariants:

**E1 Evidence origination:** non-derivation evidence has a traceable source/tool/artifact origin.

**E2 Citation validity:** state/decision claims cite active evidence.

**E3 Claim containment:** cited evidence must actually support the key entities/numbers/typed values of the conclusion.

**E4 Derivation transparency:** derived evidence recursively resolves to non-derived leaves.

**E5 Repair locality:** repair cannot append unsupported authoritative content.

### 3.4 Claims

Claim types:

- `observation`: direct normalized observation.
- `state`: aggregate/inference used as reusable problem state.
- `decision`: proposition that drives finalization, action, or governance.

A claim is not authoritative by construction.

### 3.5 Admission Gate

Input:

- `Claim`
- supporting `LedgerEntry[]`
- policy/risk context

Output: `AdmissionDecision` with ternary state.

```text
+1 = admitted to reusable shared truth
 0 = unresolved/contested; visible but not authoritative
-1 = rejected/quarantined
```

Validation layers for MVP:

1. schema/reference validity;
2. evidence lifecycle validity;
3. source/content hash checks where available;
4. simple deterministic entity/numeric containment for structured claims;
5. domain/test/tool verifier hooks where available;
6. policy/consent checks for decision/action claims.

An LLM verifier MAY assist but MUST NOT be the only validator for invariants that can be checked symbolically.

### 3.6 Capability Descriptor

Soft-state advertisement used for candidate routing.

Descriptor is signed and expires unless refreshed.

Core fields:

- identity;
- capability schema/version;
- compatible input/output contract hash;
- policy posture;
- TTL/freshness;
- availability;
- optional semantic representation;
- QoS hints;
- competence/evidence refs;
- evidence commitments.

Discovery output is a **candidate set**, not trusted assignment.

### 3.7 Agent-local memory

Persistent learned experience stays local by default.

Candidate `PrivateMemoryPiece` contains:

- task/context prototype;
- strategy/action prototype;
- coordination trajectory summary;
- outcome/evaluation;
- provenance refs;
- privacy/sharing policy.

A later experiment may separate exploit and explore pools.

### 3.8 Provenance Packet adapter

Cross-agent governed handoffs MUST continue to use the existing v1.4 contract where it applies.

This design may reference Provenance Packet digests from evidence or handoff metadata but MUST NOT redefine its signature/envelope/sequence semantics.

### 3.9 Evidence Bundle adapter

For events requiring later offline accountability, an adapter may preserve:

- canonical event/message commitment;
- sender authentication;
- log/checkpoint/inclusion evidence;
- delegation/authorization evidence;
- explicit receipt only when actually issued;
- continuity/witness evidence where policy requires;
- relevant artifact/evidence refs.

Acceptance means only that the selected evidence predicates passed. It does not imply semantic correctness or successful downstream execution.

## 4. Separation of concerns

| Data | Shared? | Persistent? | Authoritative? |
|---|---:|---:|---:|
| coordination chatter | maybe | optional | no |
| task queue event | yes | yes/logged | operational only |
| raw LedgerEntry | task/session scoped | yes | evidence, not conclusion |
| proposed Claim | visible if useful | yes | no |
| admitted SharedGist | yes | yes | reusable task truth within scope |
| private memory | no by default | yes | local prior only |
| CapabilityDescriptor | yes | TTL-bound | candidate routing evidence only |
| ProvenancePacket | shared by handoff | yes | governed handoff evidence |
| EvidenceBundle | shared for audit | yes | policy-relative evidence sufficiency |

## 5. Typed repair

Allowed MVP repair operators:

- `drop_evidence`
- `refresh_evidence`
- `retry_tool`
- `switch_tool`
- `acquire_more_evidence`
- `stop_and_answer`
- `abstain`

Any repair that adds new evidence MUST point to a new source/tool/artifact observation.

Free-form critique may recommend a repair but cannot itself write an admitted fact.

## 6. Contradictions

Contradictions are first-class.

Process:

```text
claim A conflicts claim B
 -> scope conflict
 -> preserve both claim/evidence chains
 -> mark affected entries conflicted/contested
 -> generate repair/acquisition options
 -> apply policy/ownership/evidence filters
 -> resolve only if current task needs resolution
```

A contradiction is not automatically an error to delete.

## 7. Capability routing

Initial version SHOULD retain familiar role priors as tags, e.g. `review`, `build`, `research`, `verify`.

Routing score may later combine:

- semantic relevance;
- recent measured competence;
- evidence freshness;
- policy compatibility;
- cost/latency;
- current load/availability;
- risk tier;
- voluntary abstention.

No single scalar score should become immutable global reputation without abuse analysis.

## 8. Risk tiers

Suggested MVP:

- **R0 coordination-only:** schema + identity/logging.
- **R1 low-risk factual:** evidence refs + admission checks.
- **R2 moderate delegated work:** canary/test or independent verification + signed receipt/result.
- **R3 side-effect/high-risk:** current consent gate + stronger execution evidence; attestation only if concrete need exists.

## 9. Success properties

S1. Unsupported factual broadcasts cannot become admitted SharedGists.

S2. Every admitted gist can be unfolded to claim/evidence lineage.

S3. A stale/conflicted evidence item cannot silently support a new decision claim.

S4. Repair cannot introduce provenance-less authoritative facts.

S5. Agents can coordinate without every update transiting a single LLM coordinator.

S6. Agents retain private memory without blocking selective knowledge sharing.

S7. Capability advertisements expire and cannot be mistaken for permanent competence.

S8. Existing Provenance Packet and consent contracts remain valid and singular.

S9. A cryptographically valid audit artifact never upgrades its claim beyond its defined evidence semantics.

