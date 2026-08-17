---
id: "flossi0ullk-canonical-build-spine"
version: "0.2.0"
kind: "canonical_build_spine"
status: "Proposed"
truth_status: "Specified"
date: "2026-07-02"
supersedes:
  - "FLOSSI0ULLK / ARF / Symbiotic Singularity — Merged Upgradeable Artifact v1"
  - "Rose Forest Merged Artifact v1 — Adversarial Verification and Corrections"
evidence_sources:
  - "README.md"
  - "MVP_PLAN.md"
  - "docs/governance/LOADING_ORDER.md"
  - "docs/adr/INDEX.md"
  - "ARF/conversation_memory.py"
  - "ARF/embedding_frames_of_scale.py"
  - "docs/specs/"
  - "Uploaded corpus: merged upgradeable artifact v1, adversarial verification artifact, SDD master spec, VVS v1.0-v1.2, ADR-0, ADR-1/RFC-001"
upgrade_path:
  - "Amend by PR only"
  - "Update source register, contradiction log, and phase gates when evidence changes"
  - "Promote to Accepted after repo-maintainer review"
rollback_plan: "Revert this file and LOADING_ORDER pointer; no runtime behavior changes."
friction_tier: "medium"
---

# FLOSSI0ULLK Canonical Build Spine v0.2

## 0. Executive decision

**Decision: +1 proceed with the smallest auditable stewarded agent system; 0 hold on deeper sovereignty/autonomy layers until current gates are green.**

The current plausible best is:

1. **Use GitHub as the current canonical development surface.** The repository lives at `G-0-B/FLOSS`, has current permissions and CI/discovery advantages, and is already the accessible reviewer surface. Radicle-canonical remains a sovereignty target, not current fact.
2. **Treat Holochain substrate viability as partially verified, not globally complete.** Current repo evidence says WASM/hApp/native tests are verified, but Tryorama end-to-end integration is not currently passing against the 0.6 substrate line. Do not claim "all tests pass" until that gate is green in CI.
3. **Make SDD and provenance the source of truth.** Specs, tests, source registers, and contradiction logs precede additional architecture.
4. **Defer KERI, AD4M, hREA, ZK attestations, proof-carrying autonomy, and no-human-gatekeeper autonomy until a concrete NOW pain passes the evidence gate.**
5. **Preserve the long-range FLOSSI0ULLK vision, but do not use visionary language as release criteria.** Release gates must be based on executable tests, reproducible logs, and traceable evidence.

One-sentence build spine:

> Build a local-first, spec-driven, provenance-rich agent memory and knowledge-validation loop; prove it with tests and audit logs; then progressively move only the parts that benefit from decentralization into Holochain and optional sovereignty layers.

---

## 1. Authority and precedence

This file is a current-state execution spine. It does **not** outrank the Kernel, Project Spine, SDD master specification, ADRs, contracts, schemas, tests, or signed results.

When documents disagree, use this order:

1. Kernel / mandatory coordination rules
2. Project Spine / governance invariants
3. SDD master specification
4. UpgradableArtifact schema and lints
5. Governance protocols
6. This canonical build spine as current execution synthesis
7. ADRs / RFCs
8. Contracts / schemas
9. Tests and signed results
10. Code
11. Synthesis / analysis docs

This spine is allowed to reconcile current-state contradictions, but it must point to the lower-level evidence that justifies the reconciliation.

---

## 2. Source register

### 2.1 Repo-local sources

| Source | Role | Current posture |
|---|---|---|
| `README.md` | Public orientation | Useful, but contains phase wording that should be read through `MVP_PLAN.md` |
| `MVP_PLAN.md` | Current implementation status and phase gates | Strongest repo-local status source for Phase 0 / Phase 1 |
| `docs/governance/LOADING_ORDER.md` | Onboarding precedence | Canonical loading map |
| `docs/adr/INDEX.md` | ADR truth/status surface | Canonical ADR index |
| `ARF/conversation_memory.py` | Local-first cross-AI memory substrate | Implemented; API mismatch noted elsewhere |
| `ARF/embedding_frames_of_scale.py` | Multi-scale/fractal embedding substrate | Implemented support layer |
| `docs/specs/` | Entry specs and contracts | Spec-first implementation surface |
| `ARF/dnas/rose_forest/` | Holochain DNA implementation | Partially verified; integration test path remains blocked |

### 2.2 Uploaded synthesis sources

| Source | Role | Use |
|---|---|---|
| `FLOSSIOULLK_merged_upgradeable_artifact_v1_2026-07-01.md` | Best merged strategic synthesis | Keep the layered hybrid, evidence classes, and "smallest auditable stewarded loop" principle |
| `Rose Forest Merged Artifact v1_ Adversarial Verification and Cor.md` | Best adversarial correction pass | Keep contradiction log, funding/license warnings, Radicle/GitHub reality check, and warning against premature add-ons |
| `arf_flossi_0_ullk_sdd_master_specification_v_01.md` | Spec-driven development anchor | Keep spec-first, `/new_feature`, `/generate_plan`, contracts-before-code, and Phase 0 seed logic |
| `ADR-0-recognition-protocol.md` | Recognition protocol | Keep conversation-as-coordination and cross-substrate memory rationale |
| `README_BREAKTHROUGH.md` | ADR-0 implementation explanation | Keep transmission/persistence/composition tests as local proof pattern |
| `conversation_memory.py` | Uploaded memory implementation | Keep as local-first seed before distributed persistence |
| `INTEGRATION_MAP.md` | ADR-0 to existing architecture bridge | Keep integration sequence, but re-gate by NOW/LATER/NEVER |
| `vvs_*` files | Virtual Verifiable Singularity specs | Treat as specified/aspirational autonomy architecture, not current release gate |
| `ADR-1-Holochain-Integration-Stack.md` / `RFC-001-*` | KERI/AD4M/hREA integration | Treat as LATER unless evidence changes |
| `human_ai_co-evolution.md` and Symbiotic Singularity docs | Research / framing | Use as orientation and threat model input, not release acceptance criteria |

---

## 3. Evidence classes

Every claim used for build decisions must carry one of these labels:

| Label | Meaning | Allowed use |
|---|---|---|
| **Verified** | Implemented and tested in this repo or supported by official/primary evidence | May gate releases |
| **Partially Verified** | Some evidence is green but an adjacent required gate is red or missing | May guide work, may not be marketed as complete |
| **Specified** | Designed or documented but not fully validated | May create tasks/tests |
| **Aspirational** | Long-range orientation or desired future | May guide roadmap, not releases |
| **Unverified** | Claimed but not evidenced or contradicted | Must be triaged before use |

Rule: **No claim is `Verified` without a path, command, test result, commit, or signed/reproducible artifact.**

---

## 4. Current reality check

### 4.1 What is real enough to build on now

| Component | Status | Decision |
|---|---|---|
| Conversation as coordination protocol | Verified as project pattern via ADR-0 lineage | Keep as cultural/protocol foundation |
| Local conversation memory | Implemented / partially verified | Use as Phase 0 local memory substrate |
| Multi-scale embeddings | Implemented support layer | Keep; test API compatibility with ConversationMemory |
| SDD workflow | Specified | Build the actual commands/gates before larger domain features |
| Governance loading order | Specified | Keep updated whenever canonical docs change |
| Holochain DNA compile/pack/native tests | Partially Verified per `MVP_PLAN.md` | Use, but do not overclaim |
| Tryorama end-to-end tests | Not currently passing per `MVP_PLAN.md` | Make this a blocking substrate gate |
| Ontology / KnowledgeTriple work | Specified; some unit tests reportedly available | Phase 1 after substrate gate is made honest |

### 4.2 What is not real enough to depend on yet

| Component | Status | Required before promotion |
|---|---|---|
| KERI identity bridge | Specified / LATER | User story showing cross-system identity pain + minimal test |
| AD4M semantic layer | Specified / LATER | Demonstrated semantic mismatch across agents requiring perspectives |
| hREA value flow | Specified / LATER | Real contribution/value-flow scenario and settlement test |
| ZK-attested models | Specified / Aspirational | Concrete model-card verifier and threat model |
| Proof-carrying autonomy | Specified / Aspirational | Proof envelope validator + bounded unsafe-operation tests |
| No-human-gatekeeper VVS autonomy | Aspirational / high risk | Replace with accountable, thresholded, logged human+rule governance until proofs exist |
| Radicle-canonical governance | Aspirational | Mirror first; switch only after concrete GitHub pain or Radicle workflow evidence |
| NLnet funding path | Risk / reverify | License simplification and current call verification before applying |

---

## 5. Contradiction log

### C1 — Phase 0 completion language

**Conflict:** Some artifacts and README wording say MVP Phase 0 is complete; adversarial review warned that Holochain Phase 0 was not demonstrably complete; `MVP_PLAN.md` now says substrate viability is partially verified but Tryorama integration is not currently passing end-to-end.

**Resolution:**

- Use `MVP_PLAN.md` as the current authoritative repo-local status source.
- Claim: **WASM/hApp/native unit tests are partially verified.**
- Do not claim: **all integration tests pass**, **Phase 0 fully complete**, or **runtime substrate bridge validated**.
- Exit gate: one reproducible CI run proving compile, pack, install, create, search, link, budget, and provenance flow.

**Decision:** +1 keep Holochain substrate work; 0 hold on deeper Holochain-dependent sovereignty layers.

### C2 — GitHub-canonical vs Radicle-canonical

**Conflict:** Values point toward sovereign forge infrastructure, but current repository, permissions, review surface, and contributor discoverability are GitHub-based.

**Resolution:**

- Current: **GitHub canonical**.
- Near-term: add Radicle mirror as sovereign backup.
- Future: Radicle-canonical only after a successful mirror workflow and contributor onboarding test.

**Decision:** +1 GitHub now; 0 Radicle switch.

### C3 — Spec-first doctrine vs retroactive implementation

**Conflict:** ADR-1 / RFC-001 lineage admits KERI/AD4M/hREA were integrated or specified after implementation pressure, violating spec-first discipline.

**Resolution:**

- Treat ADR-1/RFC-001 as useful design inventory.
- Do not use them as NOW work.
- Require `/new_feature` -> spec -> contracts/tests -> implementation before reactivating those modules.

**Decision:** -1 to immediate KERI/AD4M/hREA integration.

### C4 — Vision language vs engineering acceptance criteria

**Conflict:** Symbiotic Singularity, VVS, Carrier Equivalence, cognitive virology, and protocolized silence contain valuable framing but are not executable release criteria.

**Resolution:**

- Keep these as orientation / threat model / human-operator hygiene.
- Translate any release-relevant idea into a testable requirement or drop it from the gate.

**Decision:** +1 preserve; -1 use as proof.

### C5 — License/funding contradiction

**Conflict:** Repo README states "Compassion Clause + Apache-2.0/GPL-compatible". Funding and open-source ecosystems often require plain OSI/FSF-recognized licenses without ethical-use restrictions.

**Resolution:**

- Create a license issue before any grant submission or downstream packaging.
- Consider dual-surfacing: a fundable core under Apache-2.0/GPL-3.0-only and an optional values covenant outside the license grant.

**Decision:** 0 hold funding applications until license posture is cleaned up.

---

## 6. The canonical build spine

```text
Human intent / project memory
  -> SDD feature spec
  -> contracts and tests
  -> local ConversationMemory + source register
  -> minimal policy/provenance gate
  -> Holochain substrate compile/pack/install proof
  -> KnowledgeTriple / ontology Phase 1
  -> agent orchestration via MCP/local router
  -> optional sovereignty modules only after measured need
```

The first production-worthy loop is not a decentralized superorganism. It is:

```text
one steward
+ one local memory substrate
+ one feature spec
+ one verifier gate
+ one provenance log
+ one reproducible test run
+ one rollback path
```

If that loop is not reliable, adding more protocols increases cognitive debt.

---

## 7. Phase gates

### Phase -1 — Canonicalization gate

**Goal:** Stop contradictory project state from multiplying.

Required:

- [ ] This spine exists and is linked from `LOADING_ORDER.md`.
- [ ] Source register identifies canonical repo and divergent historical repos.
- [ ] `README.md`, `MVP_PLAN.md`, and this spine use compatible phase language.
- [ ] Known contradictions are logged, not hidden.

Exit criterion:

- A new agent can load the prescribed documents and state the current Phase 0 status without contradiction.

### Phase 0A — Local memory and SDD gate

**Goal:** Make the machine-that-builds-the-machine usable before expanding the domain model.

Required:

- [ ] `ConversationMemory` runs locally.
- [ ] API mismatch with `MultiScaleEmbedding` is fixed or explicitly bypassed.
- [ ] `/new_feature` scaffold exists or equivalent CLI exists.
- [ ] `/generate_plan` scaffold exists or equivalent CLI exists.
- [ ] Contracts/tests are created before implementation files.
- [ ] All generated artifacts include provenance metadata.

Exit criterion:

- Given one feature description, the repo can create a spec, plan, contracts, tests, and a provenance summary reproducibly.

### Phase 0B — Holochain substrate gate

**Goal:** Make Holochain claims honest and reproducible.

Required:

- [ ] `nix develop` / dev shell documented.
- [ ] Rust zomes compile to WASM.
- [ ] `hc dna pack` succeeds.
- [ ] `hc app pack` succeeds.
- [ ] hApp installs in a local conductor or documented harness.
- [ ] One create/search/link/budget flow passes in automated test.
- [ ] Tryorama is either repaired, replaced by a direct client harness, or explicitly deferred with a signed rationale.

Exit criterion:

- CI or a reproducible local command proves the substrate path end-to-end.

### Phase 1 — Symbolic-first knowledge core

**Goal:** Move from blob/vector knowledge to structured symbolic validation.

Required:

- [ ] `KnowledgeTriple` entry type implemented from spec.
- [ ] `OntologyRelation` or equivalent predicate registry implemented.
- [ ] Confidence, license, derivation, and model-card rules enforced.
- [ ] LLM-extracted triples require validator provenance.
- [ ] Query path returns triples with provenance.

Exit criterion:

- A human-asserted triple and one derived/validated triple can be created, queried, and explained.

### Phase 2 — Minimal stewarded agent loop

**Goal:** Prove useful agent orchestration without premature autonomy.

Required:

- [ ] Roles: Scout, Builder, Verifier, Curator.
- [ ] Ternary gate: `+1 execute`, `0 pause`, `-1 refuse`.
- [ ] Budget model for writes/actions.
- [ ] Audit log for every agent action.
- [ ] Human-visible review queue for `0` decisions.

Exit criterion:

- Agent loop completes one repo maintenance task with a provenance trail and rollback path.

### Phase 3 — Sovereignty module evaluation

**Goal:** Add KERI/AD4M/hREA/Radicle only if they beat the simpler baseline.

Each module needs:

- [ ] Concrete NOW pain.
- [ ] Success criterion.
- [ ] Minimal seam.
- [ ] Test.
- [ ] Rollback.
- [ ] Maintenance owner.

Default decision: **LATER**.

---

## 8. NOW / LATER / NEVER backlog

### NOW

1. Create and link this canonical build spine.
2. Reconcile README phase wording with `MVP_PLAN.md`.
3. Fix or document `ConversationMemory` / `MultiScaleEmbedding` API mismatch.
4. Implement or expose SDD CLI scaffolds.
5. Make one Holochain substrate test path reproducible.
6. Create `SOURCE_REGISTER.md` and `EVIDENCE_LEDGER.md` if not already present.
7. Add a contradiction log update process to PR template or governance docs.

### LATER

1. Radicle mirror.
2. KERI identity bridge.
3. AD4M perspective layer.
4. hREA value-flow ledger.
5. ZK model attestations.
6. VVS proof-carrying autonomy.
7. Distributed compute / AGI@Home integration.
8. Public governance dashboard.

### NEVER unless evidence changes

1. New protocol layer without a specific blocked user story.
2. Self-modification of mainline code without sandbox, proof, and rollback.
3. Marketing claims of superintelligence, consciousness, or verified autonomy without testable evidence.
4. Funding applications that require OSI/FSF licensing while the fundable core carries an ethical-use license rider.
5. Replacing human moral authority with opaque automation. Use rules and proofs to reduce unilateral control, not to erase accountable stewardship.

---

## 9. Issue backlog draft

### Issue 1 — Reconcile Phase 0 public wording

**Decision:** +1 NOW

Problem: README and `MVP_PLAN.md` can be read as disagreeing on Phase 0 completeness.

Acceptance criteria:

- README says "Phase 0 substrate viability partially verified" or equivalent.
- README points to `MVP_PLAN.md` and this spine for precise status.
- No file claims Tryorama is currently passing unless CI proves it.

### Issue 2 — Add source register and evidence ledger

**Decision:** +1 NOW

Acceptance criteria:

- `docs/governance/SOURCE_REGISTER.md` lists repo-local, uploaded, archived, and external sources.
- `docs/governance/EVIDENCE_LEDGER.md` gives each load-bearing claim a truth label.
- Divergent historical repos are listed with their role and status.

### Issue 3 — Repair local memory substrate

**Decision:** +1 NOW

Acceptance criteria:

- `ConversationMemory` can transmit, persist, recall, and compose without import/API mismatch.
- Tests show real or deterministic mock embeddings.
- Output includes provenance metadata.

### Issue 4 — Implement SDD command scaffold

**Decision:** +1 NOW

Acceptance criteria:

- Command or script creates `specs/NNN-slug/feature-spec.md`.
- Command or script generates implementation plan, contracts, tests, and manual testing doc.
- Generated outputs include `[NEEDS CLARIFICATION]` markers for missing inputs.

### Issue 5 — Resolve Holochain integration test harness

**Decision:** +1 NOW

Acceptance criteria:

- Pick one: migrate to holonix 0.7-dev, direct `@holochain/client` harness, or documented backport strategy.
- One create/search/link/budget/provenance flow runs in automated test.
- README/MVP status updated after the test result, not before.

### Issue 6 — License posture review

**Decision:** 0 HOLD until reviewed

Acceptance criteria:

- Identify the legally operative repository license.
- Decide whether fundable core uses Apache-2.0/GPL-3.0-only.
- Move values covenant outside the license grant if OSI/FSF compatibility is required.

---

## 10. Handoff packet

```yaml
timestamp: "2026-07-02"
author_agent: "GPT-5.5 Thinking"
human_collision_node: "Tony / kalisam / G-0-B FLOSS"
source_systems:
  - "G-0-B/FLOSS GitHub repo"
  - "uploaded FLOSSI0ULLK merged artifact v1"
  - "uploaded adversarial verification artifact"
  - "uploaded SDD master specification"
  - "uploaded VVS and ADR corpus"
claim_type:
  - "repo_assumption"
  - "proposal"
  - "observed_fact"
payload:
  summary:
    - "Canonical build spine v0.2 resolves the project toward a smaller auditable loop."
    - "GitHub is current canonical; Radicle is later/mirror."
    - "Holochain substrate is partially verified; Tryorama/e2e gate remains not green."
    - "SDD/provenance must precede deeper sovereignty layers."
    - "KERI/AD4M/hREA/ZK/VVS autonomy are LATER unless NOW pain is demonstrated."
  evidence:
    - "README.md"
    - "MVP_PLAN.md"
    - "docs/governance/LOADING_ORDER.md"
    - "docs/adr/INDEX.md"
    - "uploaded merged/adversarial/SDD/VVS corpus"
  risks:
    - "Phase language drift"
    - "License incompatibility with some funders"
    - "Premature integration complexity"
    - "Vision claims outrunning tests"
  benefits:
    - "Lower cognitive debt"
    - "Clear phase gates"
    - "Concrete next PR backlog"
    - "Better AI/human handoff"
next_action: "Review and either accept this spine or open follow-up issues for README, source register, evidence ledger, and test harness."
```

---

## 11. Changelog

### v0.2.0 — 2026-07-02

- Created canonical execution synthesis from uploaded corpus and current `G-0-B/FLOSS` repo state.
- Reconciled Phase 0 completion conflict into "partially verified substrate; e2e integration still gated."
- Made GitHub-canonical / Radicle-later explicit.
- Demoted KERI, AD4M, hREA, ZK, and VVS autonomy to LATER unless evidence changes.
- Added NOW/LATER/NEVER backlog and issue backlog draft.
