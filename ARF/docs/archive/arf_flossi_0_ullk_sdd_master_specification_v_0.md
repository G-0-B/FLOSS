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
1) **Identity & Membership**: Agent keys, roles, attestations.
2) **Offers/Needs & Commitments** (HoloREA‑compatible): publish, match, fulfill.
3) **Mutual Credit Wallet**: earn/spend internal credits; redemption rules.
4) **NormKernel Governance**: policy evaluation, compliance proofs, escalation.
5) **Knowledge Ingestion & Indexing**: append‑only epistemic logs, vector/graph indices, provenance.
6) **SDD Tooling**: `/new_feature` + `/generate_plan` commands; spec templates; gates; test‑first flows.

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
- # of regressions caught at contract/integration stages vs. prod.
- Mean cycle time to propagate spec change → regenerated code/test updates.


## 11. Workflows & Branching

- **/new_feature** usage:
  - Input: brief description.
  - Output: `specs/NNN‑slug/feature‑spec.md` with open questions.
- **/generate_plan** usage:
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
**Goals**: deterministic scaffolding; reproducible plan/test generation; artifact traceability; local-first operation.  
**Non‑Goals**: picking a single language for downstream features; implementing any domain features beyond tooling.

## 000.3 Personas
Contributor, Curator (reviewer), DevOps Engineer, Research Agent.

## 000.4 User Stories
- **US‑000‑1 (Contributor):** Given a one‑line description, when I run `/new_feature`, then a numbered branch and `specs/NNN‑slug/feature‑spec.md` are created with `[NEEDS CLARIFICATION]` markers.
- **US‑000‑2 (Contributor):** Given an existing feature spec, when I run `/generate_plan`, then an implementation plan, contracts, tests, and manual‑testing doc are created, with rationale mapped to requirements.
- **US‑000‑3 (DevOps):** When CI runs, then Phase ‑1 gates fail the build if any gate is violated or tests are missing.
- **US‑000‑4 (Curator):** When reviewing, I can see traceability links from decisions → requirements and a checklist confirming no unresolved ambiguities.

## 000.5 Functional Requirements & Acceptance Criteria
- **FR‑000‑A `/new_feature`**
  - AC: Auto‑number; create branch `NNN‑<slug>`; scaffold `feature‑spec.md` from template; insert ambiguity markers; emit JSON summary of created paths.
- **FR‑000‑B `/generate_plan`**
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
1) **Contract tests**: validate CLI I/O schemas; ensure ambiguity markers appear.  
2) **Integration tests**: end‑to‑end scaffold of a toy feature; verify files, branches, and manifests.  
3) **E2E**: run CI on a toy repo—expect Phase ‑1 failure when gates violated.  
4) **Unit**: numbering, slugify, template fill‑ins.

## 000.9 Files Created (in order)
1) `contracts/cli.json`, `contracts/gates.json`  
2) `tests/contract/*.spec.*`, `tests/integration/*.spec.*`, `tests/e2e/*.spec.*`, `tests/unit/*.spec.*`  
3) `src/cli/*`, `src/gates/*`, `src/templates/*`  
4) `manual‑testing.md`

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
 Risks & Ternary Assessment (‑1 / 0 / +1)

- Cultural adoption resistance (0 → mitigate with gating and templates).
- Spec quality bottlenecks (0 → reviewer roles; checklists; `[NEEDS CLARIFICATION]`).
- Tooling gaps (0 → start minimal; iterate; CLI surfaces everywhere).


## 16. Open Questions / Clarifications

- [NEEDS CLARIFICATION] Preferred initial runtime(s): Rust/Holochain vs. polyglot adapters?
- [NEEDS CLARIFICATION] Minimal viable identity/attestation format(s)?
- [NEEDS CLARIFICATION] Target infra for CI gates and artifact registry?
- [NEEDS CLARIFICATION] Mutual credit redemption rules and treasury policy?
- [NEEDS CLARIFICATION] Provenance schema baseline (JSON‑LD? custom?) and export format v0?
- [NEEDS CLARIFICATION] Prioritized initial user personas for v0 launch?


## 17. Appendix A — Feature Templates

### A1. Feature Spec Template (generated by `/new_feature`)

**Title**  
**Summary** (WHAT & WHY; avoid HOW)  
**Goals / Non‑Goals**  
**Personas**  
**User Stories** (Given/When/Then)  
**Acceptance Criteria** (testable)  
**NFRs**  
**Dependencies / Constraints**  
**Research Notes**  
**Open Questions** with `[NEEDS CLARIFICATION: …]`

**Checklist**  
- [ ] No remaining `[NEEDS CLARIFICATION]`  
- [ ] Requirements testable & measurable  
- [ ] Success criteria defined  


### A2. Implementation Plan Template (generated by `/generate_plan`)

**Phase ‑1: Pre‑Implementation Gates**  
- **Simplicity Gate (Art. VII):** ≤3 projects? No future‑proofing?  
- **Anti‑Abstraction Gate (Art. VIII):** Framework‑first? Single model?  
- **Integration‑First Gate (Art. IX):** Contracts defined? Contract tests written?  
- **Test‑First Gate (Art. III):** Failing tests approved?

**Technical Translation**  
- Data model(s), API contracts, storage, runtime, error model, observability.  

**Complexity Tracking**  
- Any deviations with justification and rollback plan.  

**Files Created (in order)**  
1) `contracts/*`  
2) `tests/contract|integration|e2e|unit/*`  
3) `src/*` to make tests pass  
4) `manual‑testing.md`

**Manual Testing**  
- Step‑by‑step validation per story.


---

**Governance Note:** The SDD constitution is embedded as NormKernel policies. Every merge must attach compliance proofs (artifacts) or document exceptions with time‑boxed remediation.

**Versioning:** v0.1 (this file). All subsequent changes are amendments with rationale, reviewer sign‑off, and regenerated artifacts.

