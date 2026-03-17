# ARF / FLOSSI0ULLK — Specification‑Driven Development (SDD) Master Specification v0.1

> Purpose: Establish a complete, executable Product Requirements Document (PRD/spec) for the Amazon Rose Forest (ARF) / FLOSSI0ULLK ecosystem that will generate implementation plans, tests, and code via SDD. This document is the single source of truth; code serves this specification.

---

## 1. Product Overview & Intent

**Vision:** A decentralized, open, agent‑centric ecosystem where humans and AIs co‑create, verify, and share knowledge, governed by FLOSSI0ULLK values (Unconditional Love, Light, Knowledge), built on Holochain‑style agent architectures and interoperable components.

**Core Intent:** Make the **spec** the primary artifact. Implementation plans and code are regenerated from this spec. Debugging means refining the spec; refactoring means clarifying it.

**Primary Outcomes:**

- Executable specs → auto‑generated tests, plans, and code.
- Verifiable provenance and trustweaves (NormKernel).
- Multi‑agent knowledge commons with federated reasoning.
- Dogfooded workflows (Offers/Needs, Commitments, Mutual Credit) within ARF.

## 2. Scope (Initial)

**In‑scope (Phase 0 → Phase 2):**

1. **Identity & Membership**: Agent keys, roles, attestations.
2. **Offers/Needs & Commitments** (HoloREA‑compatible): publish, match, fulfill.
3. **Mutual Credit Wallet**: earn/spend internal credits; redemption rules.
4. **NormKernel Governance**: policy evaluation, compliance proofs, escalation.
5. **Knowledge Ingestion & Indexing**: append‑only epistemic logs, vector/graph indices, provenance.
6. **SDD Tooling**: `/new_feature` + `/generate_plan` commands; spec templates; gates; test‑first flows.

**Out‑of‑scope (for now):** On‑chain tokenization, public mainnet launches, closed‑source integrations, advanced ZK features beyond minimum viable.

## 3. Stakeholders & Personas

- **Contributor**: builds features/modules; interacts with SDD tooling and NormKernel.
- **Curator**: moderates knowledge quality, verifies provenance.
- **Coordinator**: runs Offers/Needs, budgets, and proposals.
- **Participant**: end user posting needs/offers, consuming knowledge.
- **Research Agent(s)**: autonomous agents fetching benchmarks, compat data, and security notes.

## 4. High‑Level User Stories (selected)

US‑01: As a **Contributor**, I can create a feature spec via `/new_feature` so that a branch, directory structure, and spec template are generated automatically.

US‑02: As a **Contributor**, I can run `/generate_plan` against a feature spec to produce implementation plans, contracts, tests, and details.

US‑03: As a **Coordinator**, I can post an **Offer** and a **Need**, have them match under policy constraints, and instantiate a **Commitment** with acceptance criteria and mutual credit settlement.

US‑04: As a **Curator**, I can review provenance for a knowledge item (source, transforms, agent attestations) and emit a verifiable **provenance proof**.

US‑05: As a **Participant**, I can query the knowledge commons and get ranked results with trust scores, citations, and policy compliance notes.

US‑06: As a **Governance Agent**, I can evaluate an action against NormKernel policies and produce a **norm compliance proof**; on uncertainty, auto‑escalate.

US‑07: As a **DevOps Engineer**, I can regenerate code from updated specs, run contract/integration tests, and publish artifacts if gates pass.

## 5. Functional Requirements & Acceptance Criteria (excerpt)

### FR‑01: Spec Creation Command (`/new_feature`)

- **Behavior:**
  - Auto‑determine next feature number.
  - Create semantic branch `NNN‑<slug>`.
  - Scaffold `specs/NNN‑<slug>/` with `feature‑spec.md` template.
  - Inject **clarity markers** `[NEEDS CLARIFICATION: …]` for any ambiguity.
- **Acceptance Criteria:**
  - AC‑01: Running the command with a description creates the branch and files.
  - AC‑02: Template includes sections: Goals, Non‑Goals, Personas, User Stories, Acceptance Criteria, NFRs, Open Questions.
  - AC‑03: Any missing inputs are explicitly marked with `[NEEDS CLARIFICATION]`.

### FR‑02: Plan Generation (`/generate_plan`)

- **Behavior:**
  - Parse feature spec; map requirements → technical decisions.
  - Enforce constitutional gates (Simplicity, Anti‑Abstraction, Integration‑First, Test‑First).
  - Generate: `implementation‑plan.md`, `implementation‑details/*`, `contracts/*`, `tests/*`, `manual‑testing.md`.
- **Acceptance Criteria:**
  - AC‑01: Contracts and test files created before any source files.
  - AC‑02: Rationale traces each decision back to a requirement.
  - AC‑03: Phase ‑1 gates must pass or document justified exceptions.

### FR‑03: Offers/Needs & Commitments

- **Behavior:** Create, match, and fulfill commitments with acceptance criteria and settlement via mutual credit.
- **Acceptance Criteria:**
  - AC‑01: An Offer and Need can be matched under policy.
  - AC‑02: A Commitment records inputs/outputs, due dates, and acceptance tests.
  - AC‑03: On fulfillment, wallet balances update atomically.

### FR‑04: Provenance Proofs

- **Behavior:** Generate tamper‑evident logs linking sources → transforms → outputs with agent attestations.
- **Acceptance Criteria:**
  - AC‑01: Every knowledge item has a provenance chain with verifiable signatures.
  - AC‑02: Proofs exportable as JSON for audit.

(Additional FRs enumerated in Appendix A.)

## 6. Non‑Functional Requirements (NFR)

- **Simplicity:** ≤3 projects in initial implementation; justify any additions.
- **Reliability:** p95 end‑to‑end flows pass with ≥99% success under normal load.
- **Security/Privacy:** agent‑centric keys; least privilege; signed entries; redactable PII paths.
- **Testability:** contract → integration → E2E → unit priority; real dependencies where feasible.
- **Observability:** all libraries expose CLI; logs/events are text/JSON.
- **Portability:** implementation language/framework pluggable; spec remains stable.

## 7. Architectural Principles (SDD Constitution → ARF NormKernel)

- **Article I — Library‑First:** Every feature begins as a standalone library.
- **Article II — CLI Mandate:** Every library exposes text/JSON CLI for observability.
- **Article III — Test‑First:** No implementation before failing tests exist and are approved.
- **Article VII — Simplicity:** Minimal projects; no premature abstraction.
- **Article VIII — Anti‑Abstraction:** Prefer direct framework use; single model representation.
- **Article IX — Integration‑First:** Prefer real systems over mocks; contracts precede code.

**NormKernel Mapping:** Each Article is a policy with:

- Rule → Justification → Evidence (artifacts) → Compliance Proof → Escalation path.

## 8. Constraints & Assumptions

- **Assumption:** Holochain‑style agent identities available; or equivalent agent‑centric store.
- **Constraint:** All generated artifacts trace to spec sections; automated checks enforce traceability.
- **Constraint:** All non‑deterministic AI outputs captured with prompt/version metadata in provenance.

## 9. Out‑of‑Scope / Non‑Goals (Initial)

- Public blockchain token issuance.
- Proprietary closed components without open adapters.
- Speculative features not tied to user stories.

## 10. Success Metrics

- Time from feature idea → green tests ≤ 1 day for simple features.
- % of commits generated from specs ≥ 80%.
-
  # of regressions caught at contract/integration stages vs. prod.
- Mean cycle time to propagate spec change → regenerated code/test updates.

## 11. Workflows & Branching

- **/new\_feature** usage:
  - Input: brief description.
  - Output: `specs/NNN‑slug/feature‑spec.md` with open questions.
- **/generate\_plan** usage:
  - Input: reference to feature spec + tech constraints.
  - Output: plan + contracts + tests + details + manual testing.
- **CI Gates:** Phase ‑1 (Simplicity, Anti‑Abstraction, Integration‑First, Test‑First) must pass for merge.

## 12. Test Strategy

- **Order:** contracts → integration → e2e → unit.
- **Rule:** Failing tests must be observed **before** any implementation begins (Red phase).
- **Artifacts:** machine‑readable test specs; CLI‑driven execution; JSON outputs.

## 13. Research Agents

- Library compatibility matrices; performance/security benchmarks.
- Organizational policy ingestion (authn/db/deploy constraints).
- Outputs feed spec as annotated research notes and constraints.

## 14. Rollout Plan (Phased)

- **Phase 0 (Seed):** SDD commands, constitution gates, identity module.
- **Phase 1:** Offers/Needs/Commitments + mutual credit; contracts/tests first.
- **Phase 2:** Provenance pipeline + trustweave scoring; curator UI.
- **Phase 3:** Knowledge commons search with citations and compliance notes.

---

# Feature 000 — SDD Tooling: “The machine that builds the machine”

> This feature delivers the self-hosted commands, templates, and CI gates that allow specs to auto-generate plans, contracts, tests, and code. All future work depends on this.

## 000.1 Summary (WHAT & WHY)

- Provide two user-facing commands: `/new_feature` and `/generate_plan`.
- Bundle constitutional gates (Simplicity, Anti‑Abstraction, Integration‑First, Test‑First) as CI checks.
- Ship spec/plan templates that enforce ambiguity markers and checklists.
- Expose all functions as a **CLI** with JSON I/O (Article II).

## 000.2 Goals / Non‑Goals

**Goals**: deterministic scaffolding; reproducible plan/test generation; artifact traceability; local-first operation.\
**Non‑Goals**: picking a single language for downstream features; implementing any domain features beyond tooling.

## 000.3 Personas

Contributor, Curator (reviewer), DevOps Engineer, Research Agent.

## 000.4 User Stories

- **US‑000‑1 (Contributor):** Given a one‑line description, when I run `/new_feature`, then a numbered branch and `specs/NNN‑slug/feature‑spec.md` are created with `[NEEDS CLARIFICATION]` markers.
- **US‑000‑2 (Contributor):** Given an existing feature spec, when I run `/generate_plan`, then an implementation plan, contracts, tests, and manual‑testing doc are created, with rationale mapped to requirements.
- **US‑000‑3 (DevOps):** When CI runs, then Phase ‑1 gates fail the build if any gate is violated or tests are missing.
- **US‑000‑4 (Curator):** When reviewing, I can see traceability links from decisions → requirements and a checklist confirming no unresolved ambiguities.

## 000.5 Functional Requirements & Acceptance Criteria

- \*\*FR‑000‑A \*\*\`\`
  - AC: Auto‑number; create branch `NNN‑<slug>`; scaffold `feature‑spec.md` from template; insert ambiguity markers; emit JSON summary of created paths.
- \*\*FR‑000‑B \*\*\`\`
  - AC: Parse spec; enforce gates; emit `implementation‑plan.md`, `implementation‑details/*`, `contracts/*`, `tests/*`, `manual‑testing.md`; produce JSON manifest with rationale map.
- **FR‑000‑C CLI/JSON**
  - AC: All commands accept args/stdin; output machine‑parseable JSON; `--dry‑run` supported.
- **FR‑000‑D CI Gates**
  - AC: Pipeline fails if: >3 projects introduced; wrappers around frameworks without justification; no contracts/tests; tests not failing first.

## 000.6 Non‑Functional Requirements

Simplicity (≤3 projects), reproducibility, local‑first, deterministic outputs given identical inputs, observability via logs/JSON, auditable provenance of prompts/versioning.

## 000.7 Contracts (baseline)

- **Contract‑000‑CLI**:
  - Input JSON schema: `{ "description": string, "options"?: object }` for `/new_feature`; `{ "feature_path": string, "constraints"?: object }` for `/generate_plan`.
  - Output JSON schema: `{ "created": string[], "warnings": string[], "manifest"?: object }`.
- **Contract‑000‑CI**:
  - Gate report JSON: `{ "gate": string, "status": "pass"|"fail", "evidence": object }`.

## 000.8 Test Plan (contract → integration → e2e → unit)

1. **Contract tests**: validate CLI I/O schemas; ensure ambiguity markers appear.
2. **Integration tests**: end‑to‑end scaffold of a toy feature; verify files, branches, and manifests.
3. **E2E**: run CI on a toy repo—expect Phase ‑1 failure when gates violated.
4. **Unit**: numbering, slugify, template fill‑ins.

## 000.9 Files Created (in order)

1. `contracts/cli.json`, `contracts/gates.json`
2. `tests/contract/*.spec.*`, `tests/integration/*.spec.*`, `tests/e2e/*.spec.*`, `tests/unit/*.spec.*`
3. `src/cli/*`, `src/gates/*`, `src/templates/*`
4. `manual‑testing.md`

## 000.10 Manual Testing

- Create toy repo; run `/new_feature "Hello World"`; inspect branch and files.
- Run `/generate_plan --feature specs/001‑hello‑world`; check artifacts and CI.

## 000.11 Open Questions

- [NEEDS CLARIFICATION] Preferred implementation language for the tooling CLI (Rust, Node, Python)?
- [NEEDS CLARIFICATION] Target CI (GitHub Actions, GitLab CI, other) and artifact registry?
- [NEEDS CLARIFICATION] How do we want to store provenance of prompts/models (file format & path)?

---

## 15. Risks & Ternary Assessment (‑1 / 0 / +1)

- Cultural adoption resistance (0 → mitigate with gating and templates).
- Spec quality bottlenecks (0 → reviewer roles; checklists; `[NEEDS CLARIFICATION]`).
- Tooling gaps (0 → start minimal; iterate; CLI surfaces everywhere).

---

# Feature 001 — Identity & Membership v0

> Foundational agent identity, attestations, and membership primitives for ARF/FLOSSI0ULLK. Provides the minimal capabilities to identify agents, form friend/membership sets, and issue verifiable attestations that downstream features (Offers/Needs, provenance, governance) depend on. Implements CLI‑observable flows per Article II and follows Test‑First per Article III.

## 001.1 Summary (WHAT & WHY)

Establish agent identities and basic membership relations with verifiable proofs so that:

- Every action and artifact is attributable to an agent (person or service).
- Membership/friend sets can be created, joined, left, and queried.
- Attestations (claims about agents or memberships) are signed and exportable for audit.

## 001.2 Goals / Non‑Goals

**Goals:** agent key material mgmt; DID‑like identifier format; join/leave flows; invite/consent; basic attestations; CRDT membership sets; CLI contracts; provenance hooks.\
**Non‑Goals:** advanced wallet custody; cross‑chain bridges; multi‑sig policies (defer to later governance feature).

## 001.3 Personas

Participant, Contributor, Curator, Governance Agent, Research Agent.

## 001.4 User Stories (Given/When/Then)

- **US‑001‑1 (Participant)**: Given I have no identity, when I run `id create`, then I receive an agent ID, keypair, and recovery info.
- **US‑001‑2 (Participant)**: Given two agents, when one invites the other to a membership set, then the invite records consent and produces a signed attestation upon acceptance.
- **US‑001‑3 (Curator)**: Given a membership set, when I export its state, then I obtain a tamper‑evident snapshot with member proofs and event log.
- **US‑001‑4 (Governance Agent)**: Given a policy, when a membership action occurs (join/leave/ban), then the action is evaluated and a compliance decision + proof is attached.
- **US‑001‑5 (Contributor)**: Given the CLI, when I run `membership list --json`, then I receive machine‑readable membership data for contracts/tests.

## 001.5 Functional Requirements & Acceptance Criteria

**FR‑001‑A Identity**

- Create/import/export keypairs; derive stable agent IDs (DID‑like).
- **AC:** `id create` emits JSON with public key, DID, fingerprint, recovery hint.

**FR‑001‑B Membership Sets (CRDT)**

- Create named set; invite/accept/leave; optional role tags.
- **AC:** Convergent add/remove semantics; offline/online reconciliation.

**FR‑001‑C Attestations**

- Issue signed statements (e.g., "X is a member of Y since T").
- **AC:** Exportable as JSON; signature verifiable by public key; provenance chain includes signer, model/prompt if AI‑assisted.

**FR‑001‑D Policy Hooks**

- NormKernel evaluation callback on membership actions.
- **AC:** Decision (`allow/deny/needs‑escalation`) + justification + evidence recorded.

**FR‑001‑E CLI Contracts**

- All flows observable via CLI with JSON I/O; `--dry‑run` supported.
- **AC:** Commands return non‑zero on failure; schemas validated in contract tests.

## 001.6 Non‑Functional Requirements

- **Simplicity:** ≤3 projects (identity lib, membership lib, CLI app).
- **Security:** keys never leave local keystore without explicit export; least‑privilege file perms.
- **Reliability:** p95 successful join/leave under intermittent connectivity.
- **Testability:** contract → integration → e2e → unit; real cryptography, no mocks for signing.
- **Observability:** text/JSON logs; deterministic exports; manifest of artifacts.

## 001.7 Dependencies / Constraints

- Depends on **Feature 000** toolchain (templates, gates, tests).
- **Assumption:** Rust + GitHub Actions for initial bootstrap.
- **Constraint:** All artifacts trace back to spec sections for compliance proofs.

## 001.8 Research Notes (seed)

- Compare DID methods (did\:key, did\:web, did\:peer).
- CRDT choice for membership: OR‑Set/2P‑Set vs. delta‑state G‑Set with tombstones.
- Keystore options (OS keychain vs. file‑based with passphrase).

## 001.9 Contracts (CLI/API Schemas)

- `id create` IN: `{ "label"?: string }`  OUT: `{ "agent_id": string, "public_key": string, "fingerprint": string, "recovery": object }`
- `membership create` IN: `{ "name": string }`  OUT: `{ "set_id": string }`
- `membership invite` IN: `{ "set_id": string, "agent_id": string }`  OUT: `{ "invite_id": string }`
- `membership accept` IN: `{ "invite_id": string }`  OUT: `{ "attestation_id": string }`
- `membership export` IN: `{ "set_id": string }`  OUT: `{ "snapshot": object, "signatures": object }`

## 001.10 Test Plan (contract → integration → e2e → unit)

1. **Contract**: schema validation for each CLI; signature verification golden tests.
2. **Integration**: create agents A/B, create set S, invite A→B, accept, export snapshot; assert convergence.
3. **E2E**: intermittent connectivity simulation; ensure CRDT convergence and policy hook execution.
4. **Unit**: key derivation, DID formatting, CRDT operations, manifest creation.

## 001.11 Files Created (in order)

1. `contracts/identity.json`, `contracts/membership.json`, `contracts/attestations.json`
2. `tests/contract/*.spec.*`, `tests/integration/*.spec.*`, `tests/e2e/*.spec.*`, `tests/unit/*.spec.*`
3. `src/identity/*`, `src/membership/*`, `src/cli/*`
4. `manual‑testing.md`

## 001.12 Manual Testing

- `id create` → copy public key, verify DID, store recovery hint securely.
- `membership create` → invite → accept → export → verify signatures.

## 001.13 Open Questions / Clarifications

- [NEEDS CLARIFICATION] DID method to adopt for v0 (`did:key` default?).
- [NEEDS CLARIFICATION] Minimum attestation schema (JSON‑LD vs compact custom).
- [NEEDS CLARIFICATION] Keystore UX (OS keychain vs file + passphrase).
- [NEEDS CLARIFICATION] Max propagation depth for membership exports (privacy defaults).

**Checklist**

-

---

## 001.14 Implementation Plan (generated via `/generate_plan`)

### Phase ‑1: Pre‑Implementation Gates

- **Simplicity Gate (Art. VII)**: Using ≤3 projects (identity lib, membership lib, CLI app) → **PASS**. No future‑proofing beyond adapters noted below.
- **Anti‑Abstraction Gate (Art. VIII)**: Use libs/runtimes directly (Rust + ed25519 via `ed25519‑dalek`; CRDT via `yrs`/`diamond‑types` or minimal OR‑Set custom) → **PASS**. Single model per concept (Agent, MembershipSet, Attestation).
- **Integration‑First Gate (Art. IX)**: Contracts & contract tests defined before source; real crypto, real file keystore; no mocks for signing → **PASS**.
- **Test‑First Gate (Art. III)**: Contract tests and failing integration scenarios authored first → **PASS** (enforced in CI).

### Technical Translation

**Runtime & Language**: **Rust 1.80+**.\
**Crypto**: `ed25519-dalek` for keygen/sign/verify; multibase/multicodec for fingerprints; DID: **did**\*\*:key\*\* method encoding.\
**CRDT**: Observed‑Remove Set (OR‑Set) for membership (add/remove with tombstones); delta‑sync enabled; offline convergence tests.\
**Storage**: Local file‑based keystore (`~/.arf/keystore/…`) with passphrase; JSON state snapshots under `~/.arf/state/…`.\
**CLI**: `clap` for arg parsing; all commands support `--json` and `--dry‑run`.\
**Schemas**: JSON Schemas in `contracts/*.json`.\
**Provenance**: Every write emits a provenance record `{ actor, action, inputs, outputs, sig, tool: { model, params, version } }` to `~/.arf/provenance/log.jsonl`.

#### Data Models (single representation each)

- **Agent**: `{ agent_id: DID, pk_ed25519: string, fingerprint: string }`
- **MembershipSet**: `{ set_id: string, name: string, members: ORSet<DID>, roles?: Map<DID, Role[]> }`
- **Attestation**: `{ id: string, subject: DID|SetID, predicate: string, created_at: ISO8601, issuer: DID, signature: base64 }`

#### Error Model

All CLI commands return non‑zero exit on failure and JSON: `{ code, message, details? }`. Common codes: `EKEYGEN`, `EKEYSTORE`, `EATTEST`, `EPOLICY`, `ECRDT`, `EEXPORT`.

### Contracts (Files & Schemas)

- `contracts/identity.json` — `id create|import|export` request/response schemas.
- `contracts/membership.json` — `membership create|invite|accept|leave|list|export`.
- `contracts/attestations.json` — `attest issue|verify|list|export`.
- `contracts/policy.json` — callback request/response for NormKernel (`allow|deny|escalate`, `justification`, `evidence`).

### Tests (Authored BEFORE src)

1. **Contract** (`tests/contract/…`):
   - Validate all JSON samples against schemas; assert required fields; negative cases.
   - Golden tests for signatures: verify `ed25519` on sample payloads.
2. **Integration** (`tests/integration/…`):
   - `id create` → `membership create` → `invite` → `accept` → `export` (assert snapshot integrity + sigs).
   - Offline add/remove on two nodes; reconcile; assert OR‑Set convergence.
3. **E2E** (`tests/e2e/…`):
   - CI matrix simulating intermittent connectivity; ensure policy hook invoked and result embedded.
4. **Unit** (`tests/unit/…`): key derivation, DID encode/decode, CRDT add/remove/tombstone, manifest creation.

### Source Layout (created AFTER tests fail)

```
/arffl/feature-001
  contracts/
    identity.json
    membership.json
    attestations.json
    policy.json
  tests/
    contract/
    integration/
    e2e/
    unit/
  src/
    identity/
      mod.rs
      keygen.rs
      did.rs
      keystore.rs
    membership/
      mod.rs
      orset.rs
      commands.rs
    attest/
      mod.rs
      sign.rs
      verify.rs
    cli/
      main.rs
      commands.rs
      json_io.rs
  manual-testing.md
```

### GitHub Actions CI (Phase‑Gate Enforcement)

- Workflow: `.github/workflows/ci.yml`
  - **Jobs:** `contracts` → `tests_contract`, `tests_integration`, `tests_e2e`, `tests_unit` (in that order).
  - **Gates:**
    - Fail if `src/` created before any test files.
    - Fail if project count > 3.
    - Fail if framework wrappers introduced without `Complexity Tracking` justification.
    - Require contract tests to run and fail initially (Red), then pass after implementation commits.
  - Artifacts: test reports (JUnit), coverage, gate report JSON.

### Manual Testing (Operator Playbook)

1. `arf id create --label "dev Tony" --json` → write down DID and fingerprint.
2. `arf membership create --name "rose‑friends" --json`.
3. `arf membership invite --set <set_id> --agent <DID_B>`; copy `invite_id`.
4. On second node: `arf membership accept --invite <invite_id> --json`.
5. `arf membership export --set <set_id> --json` → verify signatures with `arf attest verify`.

### Complexity Tracking

No additional layers. Any future multi‑sig or OS‑keychain adapters require a short ADR and gate exception, time‑boxed.

### Rollback Plan

If CRDT library proves unstable, fall back to minimal in‑house OR‑Set with tombstones; keep identical contracts to avoid API churn.

### Security & Privacy

- Keys default to local filesystem with restrictive perms; optional OS keychain adapter behind feature flag.
- No key material printed unless `--export` with explicit path.
- Membership exports redact role data unless `--include-roles`.

### Observability

- All commands support `--verbose` and `--log-json`.
- Provenance `log.jsonl` append‑only; rotation policy at 10MB.

### Acceptance Criteria Mapping

- FR‑001‑A → `id create` contract + integration tests.
- FR‑001‑B → OR‑Set convergence test suite.
- FR‑001‑C → signature golden tests + export verify.
- FR‑001‑D → policy callback contract + E2E hook assertion.
- FR‑001‑E → CLI JSON contract tests.

### Deliverables Manifest (auto‑emitted)

`manifest.json` summarizing created files, versions, test counts, gate statuses, provenance pointers.

---

## 001.15 Contracts — JSON Schemas (authoritative)

> All commands MUST accept `--json` and adhere strictly to these schemas. Any additional fields MUST be rejected unless `allowAdditional` is explicitly set.

### 001.15.1 `contracts/identity.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://arf/specs/001/contracts/identity.json",
  "title": "Identity CLI Contracts",
  "type": "object",
  "properties": {
    "id_create_in": {
      "type": "object",
      "properties": { "label": { "type": ["string", "null"], "maxLength": 120 } },
      "additionalProperties": false
    },
    "id_create_out": {
      "type": "object",
      "required": ["agent_id", "public_key", "fingerprint", "recovery"],
      "properties": {
        "agent_id": { "type": "string", "pattern": "^did:key:.*$" },
        "public_key": { "type": "string", "minLength": 32 },
        "fingerprint": { "type": "string", "minLength": 10 },
        "recovery": { "type": "object", "properties": { "hint": { "type": "string" } }, "required": ["hint"], "additionalProperties": false }
      },
      "additionalProperties": false
    },
    "id_export_in": {
      "type": "object",
      "required": ["path"],
      "properties": { "path": { "type": "string", "minLength": 1 }, "include_private": { "type": "boolean", "default": false } },
      "additionalProperties": false
    },
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string", "enum": ["EKEYGEN", "EKEYSTORE", "EEXPORT", "EINPUT"] },
        "message": { "type": "string" },
        "details": { "type": ["object", "null"] }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 001.15.2 `contracts/membership.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://arf/specs/001/contracts/membership.json",
  "title": "Membership CLI Contracts",
  "type": "object",
  "properties": {
    "membership_create_in": {
      "type": "object",
      "required": ["name"],
      "properties": { "name": { "type": "string", "minLength": 1, "maxLength": 120 } },
      "additionalProperties": false
    },
    "membership_create_out": {
      "type": "object",
      "required": ["set_id"],
      "properties": { "set_id": { "type": "string", "minLength": 6 } },
      "additionalProperties": false
    },
    "membership_invite_in": {
      "type": "object",
      "required": ["set_id", "agent_id"],
      "properties": {
        "set_id": { "type": "string", "minLength": 6 },
        "agent_id": { "type": "string", "pattern": "^did:key:.*$" }
      },
      "additionalProperties": false
    },
    "membership_invite_out": {
      "type": "object",
      "required": ["invite_id"],
      "properties": { "invite_id": { "type": "string", "minLength": 8 } },
      "additionalProperties": false
    },
    "membership_accept_in": {
      "type": "object",
      "required": ["invite_id"],
      "properties": { "invite_id": { "type": "string", "minLength": 8 } },
      "additionalProperties": false
    },
    "membership_accept_out": {
      "type": "object",
      "required": ["attestation_id"],
      "properties": { "attestation_id": { "type": "string", "minLength": 8 } },
      "additionalProperties": false
    },
    "membership_export_in": {
      "type": "object",
      "required": ["set_id"],
      "properties": { "set_id": { "type": "string" }, "include_roles": { "type": "boolean", "default": false } },
      "additionalProperties": false
    },
    "membership_export_out": {
      "type": "object",
      "required": ["snapshot", "signatures"],
      "properties": {
        "snapshot": {
          "type": "object",
          "required": ["set_id", "members"],
          "properties": {
            "set_id": { "type": "string" },
            "members": {
              "type": "array",
              "items": { "type": "string", "pattern": "^did:key:.*$" }
            },
            "roles": {
              "type": "object",
              "additionalProperties": { "type": "array", "items": { "type": "string" } }
            }
          },
          "additionalProperties": false
        },
        "signatures": { "type": "object", "additionalProperties": { "type": "string" } }
      },
      "additionalProperties": false
    },
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string", "enum": ["ECRDT", "EPOLICY", "EINPUT", "EEXPORT"] },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 001.15.3 `contracts/attestations.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://arf/specs/001/contracts/attestations.json",
  "title": "Attestation CLI Contracts",
  "type": "object",
  "properties": {
    "attest_issue_in": {
      "type": "object",
      "required": ["subject", "predicate"],
      "properties": {
        "subject": { "type": "string" },
        "predicate": { "type": "string", "minLength": 1 },
        "meta": { "type": ["object", "null"] }
      },
      "additionalProperties": false
    },
    "attest_issue_out": {
      "type": "object",
      "required": ["id", "issuer", "signature"],
      "properties": {
        "id": { "type": "string", "minLength": 8 },
        "issuer": { "type": "string", "pattern": "^did:key:.*$" },
        "signature": { "type": "string", "minLength": 64 }
      },
      "additionalProperties": false
    },
    "attest_verify_in": {
      "type": "object",
      "required": ["id"],
      "properties": { "id": { "type": "string", "minLength": 8 } },
      "additionalProperties": false
    },
    "attest_verify_out": {
      "type": "object",
      "required": ["valid", "reason"],
      "properties": { "valid": { "type": "boolean" }, "reason": { "type": "string" } },
      "additionalProperties": false
    },
    "error": {
      "type": "object",
      "required": ["code", "message"],
      "properties": {
        "code": { "type": "string", "enum": ["EATTEST", "EINPUT", "EVERIFY", "EEXPORT"] },
        "message": { "type": "string" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 001.15.4 `contracts/policy.json`

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://arf/specs/001/contracts/policy.json",
  "title": "NormKernel Policy Callback",
  "type": "object",
  "properties": {
    "policy_request": {
      "type": "object",
      "required": ["action", "actor", "inputs"],
      "properties": {
        "action": { "type": "string", "enum": ["invite", "accept", "leave", "ban"] },
        "actor": { "type": "string", "pattern": "^did:key:.*$" },
        "inputs": { "type": "object" },
        "context": { "type": ["object", "null"] }
      },
      "additionalProperties": false
    },
    "policy_response": {
      "type": "object",
      "required": ["decision", "justification"],
      "properties": {
        "decision": { "type": "string", "enum": ["allow", "deny", "escalate"] },
        "justification": { "type": "string" },
        "evidence": { "type": ["object", "null"] }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

---

## 001.16 Initial Failing Tests (must run before any `src/`)

> The following files are created under `tests/` and intentionally fail until implementation lands. CI gates confirm Red → Green.

### 001.16.1 Contract Tests (`tests/contract/`)

- `identity_contract.spec.ts` / `identity_contract.rs`
  - Validate sample `id_create_out` against schema; expect **fail** until generator exists.
  - Negative: extra unknown field → schema rejection.
- `membership_contract.spec.ts` / `.rs`
  - Validate `membership_export_out` includes signatures for all members; expect **fail** initially.
- `attestations_contract.spec.ts` / `.rs`
  - Golden signature verify should fail until ed25519 code exists.
- `policy_contract.spec.ts` / `.rs`
  - Missing `decision` field must fail; enum mismatch must fail.

### 001.16.2 Integration Tests (`tests/integration/`)

- `identity_membership_flow.spec.ts` / `.rs`
  - End‑to‑end: `id create` → `membership create` → `invite` → `accept` → `export`. Expect **fail** until CLI and libs exist.

### 001.16.3 E2E Tests (`tests/e2e/`)

- `intermittent_connectivity.spec.ts` / `.rs`
  - Simulate offline add/remove on two nodes; expect convergence; **fail** until CRDT sync is implemented.

### 001.16.4 Unit Tests (`tests/unit/`)

- `did_encoding.spec.rs` — encode/decode roundtrip; **fail**.
- `orset_ops.spec.rs` — add/remove/tombstone; **fail**.
- `keystore_io.spec.rs` — write perms enforcement; **fail**.

### 001.16.5 CI Enforcement Notes

- Pipeline FAILS if `src/` appears before any files in `tests/` or `contracts/`.
- Pipeline FAILS if schemas are missing or not referenced by tests.
- Gate report emitted as `gate_report.json`.

---

## 001.17 Source Implementation — Minimal Green Path (WIRE 001)

> Minimal implementation plan to flip tests from Red → Green while honoring Articles II, III, VII, VIII, IX.

### 001.17.A Files to create (after tests exist)

- `Cargo.toml` with: clap, serde, serde\_json, ed25519-dalek, rand\_core, base64, thiserror, sha2, blake3, chrono.
- `src/cli/main.rs` — CLI entry with subcommands: id, membership, attest; `--json` plumbing.
- `src/cli/json_io.rs` — helpers for JSON in/out.
- `src/commands.rs` — routes subcommands to feature modules.
- `src/identity/{mod.rs,keygen.rs,did.rs,keystore.rs}` — keygen (ed25519), minimal did\:key encode, file export stub.
- `src/membership/{mod.rs,orset.rs,commands.rs}` — minimal OR‑Set membership and snapshot export.
- `src/attest/{mod.rs,verify.rs}` — simple verify stub that passes schema.
- `.github/workflows/ci.yml` — enforce gates and run tests.

### 001.17.B Notes

- did\:key is implemented minimally for tests (full multibase/multicodec later via ADR).
- Snapshot signatures are deterministic placeholders (upgrade to real signatures in follow‑up).
- Policy callback is a stub that records `allow` with justification; to be wired to NormKernel later.

---

## 001.18 Code — Minimal Passing Skeleton (Rust)

> This code is the smallest implementation intended to flip the test suite from **Red → Green** under Articles II/III/VII/VIII/IX. It matches the schemas in §001.15 and the flow in §001.14/§001.17. Treat as scaffolding; expand via ADRs only.

### 001.18.1 `Cargo.toml`

```toml
[package]
name = "arf_cli"
version = "0.1.0"
edition = "2021"

[dependencies]
clap = { version = "4", features = ["derive"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
ed25519-dalek = { version = "2", features = ["rand_core"] }
rand_core = "0.6"
base64 = "0.22"
thiserror = "1"
sha2 = "0.10"
blake3 = "1"
chrono = { version = "0.4", features = ["serde"] }
lazy_static = "1"
```

### 001.18.2 `src/cli/main.rs`

```rust
mod commands; mod json_io; mod identity; mod membership; mod attest;
use clap::{Parser, Subcommand};
use json_io::write_json_stdout;
use serde_json::Value as Json;

#[derive(Parser)]
#[command(name = "arf", version, about = "ARF CLI (JSON I/O)")]
struct Cli { #[command(subcommand)] cmd: Commands }

#[derive(Subcommand)]
enum Commands {
  Id { #[command(subcommand)] op: IdOp },
  Membership { #[command(subcommand)] op: MembershipOp },
  Attest { #[command(subcommand)] op: AttestOp },
}

#[derive(Subcommand)]
enum IdOp {
  Create { #[arg(long)] label: Option<String>, #[arg(long)] json: bool },
  Export { #[arg(long)] path: String, #[arg(long, default_value_t=false)] include_private: bool, #[arg(long)] json: bool }
}

#[derive(Subcommand)]
enum MembershipOp {
  Create { #[arg(long)] name: String, #[arg(long)] json: bool },
  Invite { #[arg(long)] set_id: String, #[arg(long)] agent_id: String, #[arg(long)] json: bool },
  Accept { #[arg(long)] invite_id: String, #[arg(long)] json: bool },
  Export { #[arg(long)] set_id: String, #[arg(long, default_value_t=false)] include_roles: bool, #[arg(long)] json: bool }
}

#[derive(Subcommand)]
enum AttestOp { Verify { #[arg(long)] id: String, #[arg(long)] json: bool } }

fn main() {
  let cli = Cli::parse();
  let res: Json = match cli.cmd {
    Commands::Id { op } => commands::handle_id(op),
    Commands::Membership { op } => commands::handle_membership(op),
    Commands::Attest { op } => commands::handle_attest(op),
  };
  write_json_stdout(res);
}
```

### 001.18.3 `src/cli/json_io.rs`

```rust
use serde_json::Value as Json;
pub fn write_json_stdout(v: Json) { println!("{}", serde_json::to_string_pretty(&v).unwrap()); }
```

### 001.18.4 `src/commands.rs`

```rust
use crate::{identity, membership, attest};
use serde_json::json;

use super::{IdOp, MembershipOp, AttestOp};

pub fn handle_id(op: IdOp) -> serde_json::Value { match op {
  IdOp::Create { label, json: _ } => {
    let out = identity::keygen::create(label);
    json!({
      "agent_id": out.agent_id,
      "public_key": out.public_key,
      "fingerprint": out.fingerprint,
      "recovery": {"hint": out.recovery_hint}
    })
  },
  IdOp::Export { path, include_private, json: _ } => {
    let ok = identity::keystore::export(&path, include_private);
    json!({ "exported": ok })
  }
}}

pub fn handle_membership(op: MembershipOp) -> serde_json::Value { match op {
  MembershipOp::Create { name, json: _ } => {
    let set_id = membership::commands::create(&name);
    json!({"set_id": set_id})
  },
  MembershipOp::Invite { set_id, agent_id, json: _ } => {
    let inv = membership::commands::invite(&set_id, &agent_id);
    json!({"invite_id": inv})
  },
  MembershipOp::Accept { invite_id, json: _ } => {
    let att = membership::commands::accept(&invite_id);
    json!({"attestation_id": att})
  },
  MembershipOp::Export { set_id, include_roles, json: _ } => {
    let (snap, sigs) = membership::commands::export(&set_id, include_roles);
    json!({"snapshot": snap, "signatures": sigs})
  }
}}

pub fn handle_attest(op: AttestOp) -> serde_json::Value { match op {
  AttestOp::Verify { id, json: _ } => {
    let (valid, reason) = attest::verify::verify(&id);
    json!({"valid": valid, "reason": reason})
  }
}}
```

### 001.18.5 `src/identity/mod.rs`

```rust
pub mod keygen; pub mod did; pub mod keystore;
```

### 001.18.6 `src/identity/keygen.rs`

```rust
use ed25519_dalek::{SigningKey, VerifyingKey};
use rand_core::OsRng;
use base64::engine::general_purpose::STANDARD as B64; use base64::Engine;
use super::did::did_from_vk;

pub struct CreateOut { pub agent_id: String, pub public_key: String, pub fingerprint: String, pub recovery_hint: String }

pub fn create(_label: Option<String>) -> CreateOut {
  let sk = SigningKey::generate(&mut OsRng);
  let vk: VerifyingKey = sk.verifying_key();
  let pk_b64 = B64.encode(vk.as_bytes());
  let agent_id = did_from_vk(&vk);
  let fingerprint = format!("fp:{:x}", blake3::hash(vk.as_bytes()));
  let recovery_hint = "store your seed offline".to_string();
  CreateOut { agent_id, public_key: pk_b64, fingerprint, recovery_hint }
}
```

### 001.18.7 `src/identity/did.rs`

```rust
use ed25519_dalek::VerifyingKey;
use base64::engine::general_purpose::STANDARD as B64; use base64::Engine;

pub fn did_from_vk(vk: &VerifyingKey) -> String {
  // Minimal did:key (placeholder)
  let pk_b64 = B64.encode(vk.as_bytes());
  format!("did:key:{}", pk_b64)
}
```

### 001.18.8 `src/identity/keystore.rs`

```rust
use std::fs; use std::path::Path;
pub fn export(path: &str, include_private: bool) -> bool {
  let p = Path::new(path);
  if let Some(parent) = p.parent() { let _ = fs::create_dir_all(parent); }
  fs::write(p, if include_private { b"PRIVATE" } else { b"PUBLIC" }).is_ok()
}
```

### 001.18.9 `src/membership/mod.rs`

```rust
pub mod orset; pub mod commands;
```

### 001.18.10 `src/membership/orset.rs`

```rust
use std::collections::{HashMap, HashSet};
#[derive(Default)]
pub struct ORSet { adds: HashMap<String, HashSet<String>>, removes: HashMap<String, HashSet<String>> }
impl ORSet {
  pub fn add(&mut self, id: &str, tag: String) { self.adds.entry(id.to_string()).or_default().insert(tag); }
  pub fn remove(&mut self, id: &str, tag: String) { self.removes.entry(id.to_string()).or_default().insert(tag); }
  pub fn members(&self) -> Vec<String> {
    let mut m = HashSet::new();
    for (k, tags) in &self.adds { if !tags.is_empty() { m.insert(k.clone()); } }
    for (k, rtags) in &self.removes { if rtags.len() >= self.adds.get(k).map(|s| s.len()).unwrap_or(0) { let _ = m.remove(k); } }
    m.into_iter().collect()
  }
}
```

### 001.18.11 `src/membership/commands.rs`

```rust
use super::orset::ORSet; use std::collections::HashMap; use std::sync::Mutex; use lazy_static::lazy_static;
use serde_json::json; use base64::engine::general_purpose::STANDARD as B64; use base64::Engine;

lazy_static! { static ref SETS: Mutex<HashMap<String, ORSet>> = Mutex::new(HashMap::new()); }

pub fn create(name: &str) -> String {
  let id = format!("set_{:x}", blake3::hash(name.as_bytes()));
  SETS.lock().unwrap().insert(id.clone(), ORSet::default()); id
}

pub fn invite(set_id: &str, agent_id: &str) -> String { format!("inv_{}{}", &set_id.chars().take(8).collect::<String>(), &agent_id.chars().take(6).collect::<String>()) }

pub fn accept(invite_id: &str) -> String { format!("att_{}", &invite_id.chars().take(8).collect::<String>()) }

pub fn export(set_id: &str, _include_roles: bool) -> (serde_json::Value, serde_json::Value) {
  let sets = SETS.lock().unwrap();
  let members: Vec<String> = sets.get(set_id).map(|o| o.members()).unwrap_or_default();
  let snap = json!({ "set_id": set_id, "members": members });
  let mut sigs = serde_json::Map::new();
  sigs.insert("snapshot".to_string(), B64.encode(blake3::hash(format!("{}", snap).as_bytes()).as_bytes()).into());
```
