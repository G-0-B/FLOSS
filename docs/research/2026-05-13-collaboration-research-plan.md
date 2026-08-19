---
title: "FLOSSI0ULLK Collaboration Research Plan"
subtitle: "Anti-Duplication Ledger, FLOSS Reuse Survey, and Pilot Sprint"
artifact_type: "research_plan"
version: "1.0"
status: "living artifact"
parent_packet: "context_continuation_packet_v4.0"
created_on: "2026-05-13"
author: "Tony Barrettay / FLOSSI0ULLK"
scope: "Identify existing FLOSS projects to compose with rather than rebuild; produce a reuse ledger and pilot integration path"
---

# FLOSSI0ULLK Collaboration Research Plan

## 0. Purpose and Scope

This document is the operationalization of Layer 3 ("Knowledge Commons and Redundancy Prevention") from Context Continuation Packet v4.0. Its single function is to answer: **what already exists that can be composed with instead of rebuilt?**

It does not produce new architectural decisions. It produces evidence. Every entry in the reuse ledger is a decision gate: before writing a single new module, there must be a completed ledger entry proving the module is not already available under an acceptable FLOSS license.

The plan applies the packet's "before-build gate" to the first seven architectural domains of the FLOSSI0ULLK stack, consistent with the packet's pilot scope targeting: one canonical repo, one AD4M perspective, one agent registry, one capability registry, one Plan Graph, one hREA contribution flow, and one RICE check suite.

---

## 1. Evidence Gate — The Hard Standard

A project counts as a **usable component** only after all five gates pass:

| Gate | Requirement |
|---|---|
| **License check** | Verified FLOSS license (AGPL, MIT, Apache 2.0, MPL, or equivalent), not just "open source" branding |
| **Minimal adapter test** | A working proof-of-concept integration or adapter stub exists in the local codebase |
| **Provenance record** | A signed `provenance_events.jsonl` entry records the integration decision, author, date, and version |
| **Rollback path** | The integration can be removed without breaking other layers |
| **Named collaboration path** | A specific GitHub issue, discussion thread, forum post, or direct contact has been initiated |

A project with architectural resonance but no passing gates is logged as **status: investigate**, not **status: adopt**.

---

## 2. Research Method

For each of the seven domains below, produce:

1. One `research/<domain>.md` note answering the structured project template
2. One entry in `research/reuse-ledger.yaml`
3. One entry in `knowledge_index.md`
4. One entry in `pattern_library.yaml` if a reusable pattern is found

### 2.1 Project Research Template

Every `research/<domain>.md` must fill this structure before any integration decision is made:

```yaml
project:
  name:
  url:
  license:                      # Exact SPDX identifier
  governance_model:             # Who controls merges, releases, roadmap?
  active_status:                # last commit date, open issues trend, maintainer responsiveness
  core_function:                # One sentence. What problem does it solve?
  overlap_with_ARF:             # Which FLOSSIULLK layer or pilot component does it address?
  reuse_mode:                   # One of: direct-dependency | adapter | protocol-alignment | collaboration | reject
  risks:                        # Technical, governance, license compatibility, dependency capture
  first_contact:                # URL to specific issue, discussion, forum, or maintainer
  minimal_test:                 # Describe the smallest proof-of-concept that would validate reuse
  decision:                     # One of: +1 proceed | 0 hold | -1 reject
  decision_rationale:
  next_action:
  next_action_owner:
  next_action_deadline:
```

### 2.2 Reuse Ledger Schema

`research/reuse-ledger.yaml` is the canonical anti-duplication record. No new module may be created without a corresponding ledger entry that either confirms no duplicate exists or documents why the found candidate was rejected.

```yaml
- id: reuse-ledger-XXXX
  domain:
  candidate_project:
  function_needed:
  reuse_level:             # direct | adapter | protocol | collaboration | none
  license_status:          # verified | pending | incompatible
  maturity:                # active | maintained | stale | archived
  integration_risk:        # low | medium | high
  contact_path:
  gate_status:             # evidence-gate fields: license, adapter_test, provenance, rollback, contact
    license: pass|fail|pending
    adapter_test: pass|fail|pending
    provenance: pass|fail|pending
    rollback: pass|fail|pending
    contact: pass|fail|pending
  decision:                # adopt | adapt | collaborate | monitor | reject
  notes:
```

---

## 3. First Seven Research Domains

These seven domains are derived directly from the packet's one-sentence continuation summary. They cover every declared primitive in the v4.0 pilot scope.

### Domain 1: Agent-Centric P2P Substrate — Holochain

**Function needed:** Distributed peer-to-peer application substrate with integrity/coordinator zomes, source chain provenance, budgeted writes, vector search, edge linking, and Tryorama tests for the Rose Forest seed DNA.

**Known candidate:** Holochain (https://github.com/holochain/holochain), Apache 2.0

**Initial reuse assessment:**
- Current Holochain 0.6 beta work covers coordinator updates, memproof security, K2 maintenance, and bootstrap improvements
- Holochain DNAs are the declared substrate for the pilot holon. This is not a "should we use it?" question — it is "what is the current API, what has changed since the Rose Forest spec was written, and what Tryorama test patterns are already community-standard?"
- Risk: API churn between 0.5.x and 0.6.x; check existing community hApps before writing custom zomes

**Research tasks:**
- [ ] Verify current HDK/HDI API version and breaking changes since Rose Forest spec
- [ ] Survey [Holochain project database](https://www.holochain.org/projects/) for existing Neighbourhoods, groupware, or coordination hApps that overlap with pilot scope
- [ ] Check Tryorama test patterns in existing hApps to reuse test scaffolding
- [ ] Document minimum viable DNA layout for pilot holon in `research/holochain.md`

---

### Domain 2: Semantic Spanning Layer — AD4M

**Function needed:** Agent-centric semantic bus providing perspectives (subjective RDF graphs), links, languages, Social DNA (Prolog-based validation), DID-based identity, and protocol adapters across heterogeneous backends.

**Known candidate:** AD4M / coasys (https://github.com/coasys/ad4m), GPL-3.0

**Initial reuse assessment:**
- AD4M is already a declared architectural primitive. Research task is not "should we use it?" but "what AD4M Languages already exist for our coordination patterns and what is their maintenance status?"
- Flux/Perspect3vism provides a production reference for AD4M + Holochain in a social app
- Social DNA Prolog validation is the mechanism for encoding ULLK principles as distributed protocol — this is high-value and needs a feasibility note
- Risk: GPL-3.0 copyleft implications on adapter layers; check compatibility with AGPL project license

**Research tasks:**
- [ ] Survey existing AD4M languages in the coasys ecosystem for identity, coordination, and knowledge-sharing patterns
- [ ] Review Flux hApp as a reference pilot for AD4M + Holochain integration
- [ ] Write a one-page Social DNA feasibility note: what Prolog rules would encode consent, sovereignty, and ULLK values as validation logic?
- [ ] Document in `research/ad4m.md`

---

### Domain 3: Portable Agent Identity — KERI / WebOfTrust

**Function needed:** Self-certifying portable identifiers, signed key event logs, multi-sig delegation, and identity bindings that work across Holochain, AD4M, Radicle, and external systems without a central ledger.

**Known candidate:** KERI / WebOfTrust (https://github.com/WebOfTrust/keripy), Apache 2.0; KERI Suite specifications achieved standardization milestone in January 2026

**Initial reuse assessment:**
- KERI AIDs are declared as a required binding in the v4.0 identity schema (`agent_identity.keri_aid`)
- The KERI Foundation maintains the core spec; WebOfTrust hosts the Python implementation; vLEI documentation uses KERI/ACDC/CESR
- Risk: KERI is a spec-heavy system; the integration path is an adapter layer, not a direct dependency — a KERI adapter stub is the minimum viable test
- Collaboration path: KERI Foundation GitHub discussions and vLEI ecosystem

**Research tasks:**
- [ ] Confirm current KERI specification version and implementation maturity in keripy and kerijs
- [ ] Write a minimal KERI AID generation and key event log stub in Python or JS for the pilot identity binding
- [ ] Map the `identity_bindings.yaml` schema fields to KERI primitives (AID, KEL, ACDC credentials)
- [ ] Document in `research/keri.md`

---

### Domain 4: Value-Flow Accounting — hREA / ValueFlows

**Function needed:** Transparent, distributed accounting of resource flows, contribution events, and economic coordination between agents without a central ledger; maps directly to pilot success criteria step 7 (hREA records contribution).

**Known candidates:**
- hREA (https://github.com/h-REA/hREA), GPL-3.0 — Holochain backend for ValueFlows
- ValueFlows vocabulary (https://www.valueflo.ws), CCo/Apache 2.0

**Initial reuse assessment:**
- hREA is the most direct match: it is a Holochain-based implementation of ValueFlows specifically designed for decentralized economic coordination
- Sensorica uses hREA/NRP-CAS for open-value accounting in open-source hardware projects — a strong reference implementation
- Risk: GPL-3.0 copyleft; hREA maintenance cadence; GraphQL API surface may change
- Collaboration path: h-REA GitHub org, Happenings Community Substack, Sensorica community

**Research tasks:**
- [ ] Check current hREA release and API stability; review GraphQL schema
- [ ] Write a minimal hREA contribution event stub that records a patch acceptance as an economic event
- [ ] Map the pilot success criterion (step 7: "hREA records contribution") to specific hREA resource/process/event types
- [ ] Review Sensorica's NRP-CAS integration as a collaboration reference
- [ ] Document in `research/hrea.md`

---

### Domain 5: Multi-Agent Orchestration — LangGraph / AG2 / CrewAI

**Function needed:** Stateful, long-running agent workflow orchestration that can route tasks to specialized agents, separate planning from execution, support sandboxed test runs, and emit explanation objects — consistent with Layer 5 (Agent Capability and Execution Fabric).

**Known candidates:**
- LangGraph (https://github.com/langchain-ai/langgraph), MIT — stateful graph-based agent workflows
- AG2/AutoGen (https://github.com/microsoft/autogen), CC-BY-4.0 / Apache 2.0 — cooperating multi-agent workflows
- CrewAI (https://github.com/crewAIInc/crewAI), MIT — role-based multi-agent crews

**Initial reuse assessment:**
- These are not architectural primitives in the packet — they are execution layer candidates. The question is which framework best supports the packet's requirements: capability registration, task routing, human-in-the-loop gates, explanation objects, and sandboxed execution
- Risk: LangChain ecosystem churn; framework lock-in; none of these are natively agent-sovereign (they are centralized orchestration tools — require careful adapter design to preserve sovereignty)
- The packet's Layer 5 can use these as execution engines while the AD4M/Holochain layers handle identity and provenance

**Research tasks:**
- [ ] Produce a comparison table: LangGraph vs. AG2 vs. CrewAI across: human-in-the-loop support, explanation object emission, sandboxed execution, license, maintenance, and sovereignty/adapter complexity
- [ ] Determine which framework best supports the pilot: one agent, one task, one provenance record
- [ ] Document in `research/agent-orchestration.md`

---

### Domain 6: Offline Knowledge Commons — Kolibri / Kiwix

**Function needed:** Offline-first or low-bandwidth access to structured educational and reference content; relevant to the "knowledge access for all enabling systems" dimension of ULLK and to the Layer 3 knowledge commons.

**Known candidates:**
- Kolibri (https://github.com/learningequality/kolibri), MIT — offline-first learning for low-resource environments
- Kiwix (https://github.com/kiwix/kiwix-tools), GPL-3.0 — offline access to Wikipedia and educational content via ZIM files

**Initial reuse assessment:**
- These are LATER targets, not NOW — they do not reduce pilot risk but they are strong candidates for "non-sentient enabling systems" integration in the Layer 8 expanded scope
- Logging them now prevents re-discovering them later and prevents building custom content distribution when these projects already serve that function
- First contact path: both have active GitHub orgs with contributor guides

**Research tasks:**
- [ ] Log both in `reuse-ledger.yaml` as status: monitor
- [ ] Note the ZIM file format and Kolibri content channel API as potential AD4M Language targets for later
- [ ] Document in `research/knowledge-commons.md`

---

### Domain 7: Environmental / Energy Sensing Systems — Safecast / OpenEMS / OSeMOSYS / OpenBCI

**Function needed:** Integration of non-sentient but life-enabling systems (environmental sensors, energy management, biosensing) as participants in the intelligence commons — consistent with the packet's vision of "all systems that enable shared existence."

**Known candidates:**
- Safecast (https://safecast.org) — CC0 radiation/environmental data, open hardware sensors
- OpenEMS (https://github.com/OpenEMS/openems), Apache 2.0 — open energy management platform
- OSeMOSYS (https://github.com/OSeMOSYS/OSeMOSYS) — open-source energy planning model
- OpenBCI (https://github.com/OpenBCI) — open-source biosensing hardware and software, MIT

**Initial reuse assessment:**
- All four are LATER targets. OpenBCI in particular is a hardware dependency — the packet explicitly says "custom hardware before software provenance works" is a NEVER/not-now item
- Safecast's CC0 data and open API is the easiest near-term integration candidate for demonstrating non-sentient system participation
- Logging them now creates a collaboration map for future integration without blocking the pilot

**Research tasks:**
- [ ] Log all four in `reuse-ledger.yaml` as status: monitor
- [ ] Note Safecast API endpoints and CC0 data access for a future "environmental sensing as AD4M Language" feasibility note
- [ ] Document in `research/sensing-systems.md`

---

## 4. Sovereign Code and Artifact Layer — Radicle

**Function needed:** Canonical peer-to-peer code hosting with signed refs, delegate authority, patch review, issues/discussions, and release governance — replacing GitHub as source of truth while preserving GitHub as mirror/CI surface.

**Known candidate:** Radicle (https://radicle.xyz), MIT / Apache 2.0

**Radicle is a declared architectural primitive.** The research task here is operational:
- [ ] Initialize one Radicle repository as the canonical FLOSSI0ULLK seed repo
- [ ] Configure mirror policy: Radicle canonical, GitHub mirror
- [ ] Document CI bridge (GitHub Actions as execution surface for Radicle patches)
- [ ] Confirm current Radicle CLI version and any API changes since the packet was written
- [ ] Log in `reuse-ledger.yaml` as status: adopt (already declared, needs operational confirmation)

---

## 5. Pilot Integration — The One Concrete First Move

Consistent with the packet's immediate next action and the NOW/LATER/NEVER framework, the first pilot integration is:

> **Replace mock embeddings in ConversationMemory with a local sentence-transformers embedding model and record provenance.**

This pilot:
- Proves the spec → test → provenance → collaboration-discovery loop end-to-end
- Is bounded, reversible, and has a clear rollback path (revert to mock embeddings)
- Produces a real provenance record and a real reuse ledger entry (sentence-transformers is MIT licensed, mature, and well-documented)
- Does not depend on Holochain, KERI, hREA, or AD4M being integrated yet

### Pilot Steps

1. **Intent record:** create `intents/intent-001-embeddings.yaml` with issuer, summary, desired outputs, constraints, response mode, expiry
2. **Before-build gate:** check `reuse-ledger.yaml` — does a local embedding solution already exist? (It does not; log sentence-transformers as the candidate)
3. **Implement:** swap mock embeddings for `sentence-transformers` in ConversationMemory; add unit tests
4. **Provenance record:** write a signed `provenance_events.jsonl` entry recording the change, author, timestamp, and model version
5. **CI gate:** ensure tests pass, including the integration tests already specified in the ADR-0 / ConversationMemory spec
6. **Review:** one human review of the diff before merge
7. **Explanation object:** emit a structured explanation of what changed and why
8. **hREA stub:** create a minimal contribution event record (even if just a YAML stub pre-full-hREA-integration)
9. **Changelog:** update `CHANGELOG.md`
10. **Next packet:** generate v4.1 continuation packet with updated pilot status

---

## 6. Repo Skeleton

Create these directories and seed files before any implementation work:

```
flossiullk/
├── CHANGELOG.md
├── README.md                        <- "What is this, what is in scope, what is out"
├── context_continuation_packet_v4_0.md  <- Canonical seed governance
├── adr/
│   └── ADR-0.md                     <- First architectural decision record
├── spec/
│   ├── current.md
│   ├── current.yaml
│   └── tests/
├── research/
│   ├── reuse-ledger.yaml            <- Anti-duplication canonical record
│   ├── holochain.md
│   ├── ad4m.md
│   ├── keri.md
│   ├── hrea.md
│   ├── agent-orchestration.md
│   ├── knowledge-commons.md
│   └── sensing-systems.md
├── provenance/
│   └── provenance_events.jsonl
├── governance/
│   ├── values.md
│   ├── risk_register.md
│   ├── consent_policy.md
│   ├── high_impact_action_policy.md
│   └── alignment_claims.md
├── ontology/
├── contracts/                       <- JSON contracts for SDD tooling (Feature 000)
├── tests/
├── src/
│   └── feature-000/                 <- /new_feature + /generate_plan CLI
├── collaboration-map/
│   └── contact_queue.md
└── intents/
    └── intent-001-embeddings.yaml
```

---

## 7. Sprint Plan — Five Days to Evidence

The goal is not to "find everything." It is to produce enough evidence to choose the first external collaboration target and the first reused component before writing new integration code.

| Day | Focus | Output |
|---|---|---|
| **Day 1** | Repo skeleton + reuse ledger schema + context packet commit | Skeleton created; packet committed as seed; ledger initialized with 10 placeholder entries |
| **Day 2** | hREA and ValueFlows deep survey | `research/hrea.md` complete; ledger entry with all 5 gates assessed; minimal contribution event stub |
| **Day 3** | KERI/WebOfTrust identity survey | `research/keri.md` complete; ledger entry; minimal AID generation stub |
| **Day 4** | Holochain project database + AD4M language survey | `research/holochain.md` and `research/ad4m.md` complete; existing hApps and Languages catalogued |
| **Day 5** | Agent orchestration comparison + pilot embeddings | Orchestration comparison table; pilot embeddings PR open; one provenance record written; one contact_queue entry filed |

---

## 8. NOW / LATER / NEVER Enforcement

The packet's NOW/LATER/NEVER framework is enforced at the reuse ledger level:

| Status | Meaning | Action |
|---|---|---|
| **NOW** | Directly reduces pilot risk; unblocks Feature 000 or the embeddings pilot | Must have a ledger entry and a named next action before implementation |
| **LATER** | Coherent with architecture; does not unblock the pilot | Logged in ledger as `status: monitor`; no implementation until pilot story proves need |
| **NEVER (for now)** | Increases integration surface without proof; broad framework docs with no repo change | Logged as `decision: -1 reject`; explicit rationale required |

Anything not in the ledger is implicitly NEVER until a ledger entry is filed.

---

## 9. Anti-Patterns to Reject

Consistent with the packet's anti-patterns and the hard critique applied to the prior research response:

- **"The infrastructure already exists"** is not sufficient. Architectural resonance ≠ working interoperability. Every candidate needs a passing evidence gate.
- **Vision accumulation** — adding new candidate projects to the map without completing ledger entries for existing ones. The ledger is a queue with a maximum depth. Do not add to it faster than you close entries.
- **New framework documents that produce no repo change, test, issue, adapter, or collaboration contact** — every research output must produce at least one concrete artifact.
- **Treating philosophical alignment as integration proof** — a project that shares ULLK values is a collaboration candidate, not a working component.
- **Starting any new module before the before-build gate is documented** — no exceptions.

---

## 10. Open Questions

These must be answered before the first external collaboration outreach:

1. What is the current Radicle CLI version, and does it support the mirror policy described in the packet?
2. What is the GPL-3.0 / AGPL compatibility profile for the project? Can hREA and AD4M be used as adapters without copyleft propagation concerns?
3. Does the ConversationMemory transmission/persistence/composition spec from ADR-0 already document the embedding interface, or does that interface need to be specified first?
4. Who is the named human steward responsible for high-impact action authorization in the pilot scope?
5. What is the governance threshold for the first Radicle patch merge — single-delegate approval or broader review?

---

## 11. Collaboration Contact Queue (Initial)

Initiate contact only after the relevant `research/<domain>.md` is complete and the ledger entry passes the license and contact gates.

| Priority | Project | Contact Path | Ask |
|---|---|---|---|
| 1 | hREA / h-REA org | GitHub Discussions on h-REA/hREA | Integration feasibility; existing contribution event patterns |
| 2 | Holochain community | https://forum.holochain.org | Current Neighbourhoods projects; Tryorama test reuse |
| 3 | AD4M / coasys | GitHub Issues on coasys/ad4m | Existing Languages for coordination/identity; Social DNA pattern examples |
| 4 | KERI Foundation | https://keri.foundation contact + WebOfTrust GitHub | Lightweight AID binding adapter; JS/Python library status |
| 5 | Safecast | https://safecast.org + GitHub | Data API and CC0 reuse for environmental sensing integration |

---

## 12. Changelog

### v1.0 — 2026-05-13

- Initial research plan derived from Context Continuation Packet v4.0 and the NOW/LATER/NEVER framework
- Seven research domains mapped to packet architectural primitives
- Evidence gate defined with five required criteria
- Reuse ledger schema specified
- Pilot integration identified: ConversationMemory real embeddings + provenance
- Repo skeleton specified
- Five-day sprint plan established
- Anti-patterns from prior research response incorporated as explicit rejection criteria

---

## 13. Next Agent Prompt

```
You are continuing FLOSSI0ULLK collaboration research under Context Continuation Packet v4.0 governance.

Your task: complete one or more of the seven research domain notes listed in this plan. For each domain, fill the project research template (Section 2.1), write a `reuse-ledger.yaml` entry (Section 2.2), and assess the five evidence gates (Section 1).

Do not create new domains until all seven are documented with at least a status:investigate ledger entry.
Do not write new integration code until at least one domain has a passing evidence gate.
Do not add new candidate projects without filing a ledger entry.

Current pilot: ConversationMemory real embeddings. Current blocker: ledger entry for sentence-transformers not yet filed.

Preserve Radicle-as-canonical. Apply RICE. Preserve ULLK. Update this document's changelog when substantial changes are made and emit a v1.1 replacement.
```
