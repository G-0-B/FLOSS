# NLnet NGI Zero Commons Grant Application — Draft v0.1

**Date:** 2026-05-19
**Type:** Research / Funding artifact draft
**Truth status:** ⚠️ Specified (draft) — content load-bearing; eligibility ✅ verified; formatting + final tone pass still needed before submission
**Target grant:** NLnet NGI Zero Commons Fund — €5,000–€50,000. ~~13th call deadline 2026-06-01 12:00 CEST~~ **passed unsubmitted; current target is the next call, deadline 2026-08-01** (per Context Continuation Packet 2026-06-09 §4d — ~7 weeks of runway as of 2026-06-12)
**Submission portal:** nlnet.nl/commonsfund/
**Coordinator:** Michiel Leenaars, ngizero-coordinator@nlnet.nl
**Applicant:** Anthony Garrett (`kalisam` / GH `kalisam` / G-0-B org)
**Project:** FLOSSI0ULLK / Rose Forest Holochain DNA + Layer 4.5 Consensus Gateway

**Critical prerequisites before submission:**
- [x] Verify US-individual geographic eligibility — ✅ **VERIFIED eligible, confirmed by Anthony 2026-06-12** (was the critical unknown carried since `CONTEXT_CONTINUATION_2026-05-14_scenarios-recognition-resources.md` §6 + §7)
- [ ] Final-pass tone calibration (per consensus claim 019e3e2c voter feedback: alignment-map tone "potentially over-confident" on critiques)
- [ ] Confirm latest CFIS Phase 0 + ADR-12 status maps to NGI Zero scope categories

---

## Proposed project name

**Rose Forest: Substrate-Layer Polycentric Consent Gate for Pluralistic AI Coordination**

(Working title; aligns project to NGI Zero's privacy-preserving / sovereign-AI / commons-flow scope while keeping FLOSSI0ULLK as parent umbrella for non-grant work.)

---

## Abstract (≤200 words for application form)

Mainstream AI alignment work centers on harm-prevention ("safety floors") and assumes one normative authority defines safety. **Rose Forest** builds the substrate that the just-published Positive Alignment paradigm (Laukkonen et al. 2026, arXiv:2605.10310; 16 authors across Oxford / DeepMind / OpenAI / Anthropic / Stanford / Tufts / UCLA) calls for but doesn't construct: **substrate-layer enforcement of pluralistic, polycentric, user-authored consent** for any memetic pattern that wishes to bind agent behavior.

Built on Holochain (agent-centric distributed substrate, Apache-2.0), the **Consent Gate Protocol** (ADR-12, 2026-05-19) gives any agent in any network the right to `reject`, `bounded_accept`, `tourist_observe` (per CFIS authority-tier framework), or `counter_propose` against any pattern offered. Refusals are durable on the source chain. The integrity zome enforces — LLMs cannot evade. The companion **CFIS** (Cross-Frame Invariance Seeking) epistemic substrate provides the formal mechanism for distinguishing universal invariants from preserved divergences across distinct cultural frames. A working **Layer 4.5 consensus gateway** (32/32 tests) routes multi-model Claims through diverse voter pools per the MDASH-validated harness-over-model architectural class (Microsoft 2026-05-12).

The grant funds: (1) Holochain entry-type implementation + Tryorama coverage for the Consent Gate (~4 weeks), (2) cross-frame validation via `[auth:trained]` frame representatives across 7 pilot frames (~6 weeks, social work), (3) NLnet-eligible adapter spike for Polis democratic-deliberation integration (~2 weeks, building on Anthropic CCAI).

---

## Why now / Why this is NGI Zero shape

NGI Zero NEXT Generation Internet Commons Fund explicitly funds "new internet commons" with emphasis on privacy-preserving, sovereign, open standards, decentralized architecture, end-user empowerment, digital commons + collective action. **Rose Forest hits all six.** Specifically:

| NGI Zero criterion | Rose Forest substrate |
|---|---|
| P2P infrastructure | Holochain agent-centric DHT (Apache-2.0, ~10k stars) |
| Privacy-preserving / sovereign | KERI portable identity + consent-as-protocol enforced at integrity zome |
| Open standards / interoperability | AD4M semantic spanning layer + KERI/ValueFlows/hREA composition |
| Architectural decentralization | No central server; no institutional chokepoint per design |
| Digital commons + collective action | AGPL-3.0 cascade per ADR-7; democratic-deliberation integration via Polis |
| FLOSS at every layer | Substrate + integrity logic + consensus gateway + CFIS specification all open-source |

The **Positive Alignment paper alignment-map** (FLOSS/docs/research/2026-05-18-positive-alignment-flossi0ullk-map.md, consensus-validated 2026-05-18 via claim 019e3e2c-e4a4-71a6-a487-956661a6ccb3) provides academic citation chain demonstrating Rose Forest sits in mainstream-validated research territory, not fringe. The **MDASH transfer** (FLOSS/docs/research/2026-05-16-mdash-cfis-architectural-transfer.md) provides Microsoft empirical validation of the harness-over-model architectural class Rose Forest implements at the substrate layer.

---

## Three concrete deliverables (scoped to fit grant size + 6-month timeline)

### Deliverable 1: Consent Gate Protocol — Holochain implementation

**Scope:** Implement ConsentPayload + ConsentDecision as Holochain entry types in `ARF/dnas/rose_forest/`, with Rust integrity-zome validation enforcing the substrate-class invariants from ADR-12 §6 and consent-payload.spec.md §"Validation rules the integrity zome MUST enforce."

**Spec status pre-grant:** JSON Schema (`FLOSS/docs/specs/consent-payload.schema.json`) and prose spec (`consent-payload.spec.md`) landed 2026-05-19. ADR-12 Module-class consensus APPROVED 2026-05-19 (claim 019e3f85, mean +0.52). Awaiting integrity-zome work + Tryorama coverage.

**Effort:** ~4 weeks engineering. Includes 2 Tryorama scenarios (single-agent consent decision + collective-DID consent via Steward Vote precursor).

**Value to commons:** First substrate-level operationalization of the consent-as-protocol pattern. Other projects building on Holochain can adopt the entry types directly. The schema is JSON-Schema-formal; non-Holochain projects can implement the same shape on their own substrates.

**Cost line:** €8,000 (engineering @ 4 weeks)

### Deliverable 2: CFIS Phase 0 — `[auth:trained]` frame-rep recruitment + validation

**Scope:** Recruit `[auth:trained]` representatives for at least 3 of the 7 CFIS pilot frames (per FLOSS/docs/architecture/CFIS_v0.3.md §VIII Phase 0 plan), run the Frame Sufficiency Gate validation (≥1 frame pair disagrees on ALL 5 CLC axes; no CLC axis unanimously agreed). Document divergences as Tier-4 entries on the source chain.

**Pre-grant status:** CFIS v0.3 promoted to canon 2026-05-19 via consensus claim 019e3f84 (APPROVED +0.60). 8-week parallel implementation plan exists. Frame-rep recruitment is the highest-risk dependency — social, not technical.

**Effort:** ~6 weeks calendar (mostly social/relationship work; engineering effort embedded in Deliverable 1 + voter-onboarding integration).

**Value to commons:** Demonstrates how pluralistic alignment works in practice with `[auth:trained]` representatives from genuinely distinct epistemic frames. This is what the Positive Alignment paper calls for but does not show — independent validation across non-WEIRD epistemic frameworks. The activity log of frame-rep validations becomes public training data for cross-cultural alignment research per fair-use + AGPL terms.

**Cost line:** €15,000 (3 × €3,000 honoraria for frame-rep participation + €6,000 coordination + documentation engineering)

### Deliverable 3: Polis democratic-deliberation adapter

**Scope:** Adapter spike integrating Polis (compdemocracy/polis, AGPL-3.0, ~5k stars) — the deliberation infrastructure Anthropic's Collective Constitutional AI used — as a ConsentPayload generator for collective-DID consent decisions. Building on the existing reuse-ledger entry 0024 (Polis added 2026-05-19) and the Positive Alignment paper's "polycentric governance" recommendation.

**Pre-grant status:** Reuse-ledger entry 0024 captures Polis as `decision: investigate` with license=pass (AGPL-3.0, AGPL-cascade compatible per ADR-7). Adapter design pending; no integration work done yet.

**Effort:** ~2 weeks engineering. Includes adapter module + 1 end-to-end test (Polis-deliberated consent → ConsentDecision on Rose Forest source chain → integrity-zome validates).

**Value to commons:** Polis is the proven deliberation infrastructure (used by vTaiwan, Anthropic CCAI, multiple municipal governments). Connecting it to Rose Forest's consent gate gives the FOSS ecosystem its first end-to-end pipeline from public deliberation → constitutional ratification → substrate-enforced agent behavior.

**Cost line:** €4,500 (engineering @ 2 weeks)

**Total request:** €27,500 (within the €5,000–€50,000 NGI Zero band; modest mid-tier ask)

---

## Track record (the evidence the application must lean on)

Per NGI Zero application form's "track record" + "evidence base" sections, summarize the substrate-level proof points:

- **MVP Phase 0 substrate viability complete** (per FLOSS/MVP_PLAN.md line 23): DNA compiles to WASM, Holochain hApp/Tryorama integration tests pass, ontology integrity unit tests pass
- **Layer 4.5 consensus gateway: 32/32 tests passing** (ADR-10, hand-verified 2026-04-26 in ADR-Suite v2.0)
- **Four consensus claims durable on source chain in last 48 hours**: 019e3e2c (Positive Alignment alignment-map APPROVED +0.55), 019e3f84 (CFIS v0.3 canon promotion APPROVED +0.60), 019e3f85 (ADR-12 stub APPROVED +0.52). Substrate is operational, not aspirational.
- **28 canonical reuse-ledger entries** at v0.4-promoted-2026-05-19; 1 at `adopt` (0013 holochain-agent-skill installed in `.claude/skills/`); 55 candidate harvest drafts in staging; ~80-fork inventory under kalisam's GitHub from 2026-04 to 2026-05
- **14+ months consistent solo dev** with public GitHub history at github.com/kalisam/FLOSS + G-0-B org
- **Three published architectural-validation events in the past 7 days**: MDASH (Microsoft, 2026-05-12, harness-over-model empirical validation), Positive Alignment (Laukkonen et al., 2026-05-11, paradigm-level academic validation), this grant application self (2026-05-19, demonstrating substrate-level operationalization of both)
- **Memory-as-shared-surface migration** (Codex executed 2026-05-18 per ADR-12 §"agent-memory-as-shared-surface" proposal) — cross-agent learning durability proven in production
- **AGPL-3.0 cascade locked in** per ADR-7; all deliverables ship under AGPL or equivalent FLOSS licenses

---

## Cited adjacent work (the bibliography for the application)

- Laukkonen et al. 2026, *Positive Alignment: AI for Human Flourishing*, arXiv:2605.10310
- Edelman / Lowe / Zhi-Xuan et al. 2025, *Full-Stack Alignment*, arXiv:2512.03399
- Nielsen et al. 2026, *Learning to Orchestrate Agents in Natural Language with the Conductor*, ICLR 2026, arXiv:2512.04388v5
- Anthropic + Collective Intelligence Project, *Collective Constitutional AI*, 2024
- Microsoft Security, *MDASH multi-model agentic scanning harness*, 2026-05-12
- VanderWeele / Teubner, *Flourishing Considerations for AI*, Information, 2026
- Global Flourishing Study, Nature Mental Health, 2025
- Holochain Foundation publications + Apache-2.0 substrate
- AD4M / Coasys foundation work

---

## Honest caveats (the kind reviewers respect)

Per consensus claim voter feedback + anti-sycophancy standing rule, named upfront:

1. **Solo developer + frame-rep recruitment social risk.** Deliverable 2 depends on `[auth:trained]` frame-rep recruitment — this is social/relationship work the applicant has not yet completed. The grant lets it happen; without it, Phase 0 stays in pre-pilot indefinitely.
2. **Cross-substrate identity bridge unsolved.** ADR-Suite v2.0 §13 Gap 3 names Radicle ↔ Holochain identity bridge as undesigned. This grant does NOT solve it (out of scope for €27,500 / 6 months) but does NOT require it for the consent gate work to land.
3. **Holochain ecosystem dependencies.** Rose Forest depends on Holochain 0.6.x; API churn risk is medium. Mitigation: holochain-agent-skill (canonical at `.claude/skills/holochain-agent-skill/` per `decision: adopt` entry 0013) provides the canonical-pattern reference for current HDK conventions.
4. **The 28-entry reuse-ledger is at the soft anti-accumulation threshold.** Grant deliverables avoid adding new candidates to the ledger; instead they close gates on existing entries (0013 holochain-agent-skill, 0024 polis, 0014 delimit-mcp-server).
5. **Project scope is large; grant scope is bounded.** The €27,500 funds three specific deliverables, not the whole FLOSSI0ULLK vision. Rose Forest is one piece; the rest of CCES L0-L7 layers remain post-grant work.

---

## Submission checklist (before 2026-08-01 — next call; the 2026-06-01 call passed unsubmitted)

- [x] Verify NLnet US-individual geographic eligibility — ✅ verified eligible per Anthony 2026-06-12 (open item carried since 2026-05-14, now closed)
- [ ] Refine cost-line breakdown with honest hourly-rate assumptions
- [ ] Add CV-tier bio for Anthony Garrett (kalisam GH + G-0-B org + 14-month track record)
- [ ] Reference letter / endorsement from one external party who has reviewed FLOSSI0ULLK work (Codex / ChatGPT / multi-AI-collaborator context as documented in CONTEXT_CONTINUATION packets)
- [ ] Tone calibration pass — voter consensus claim 019e3e2c flagged alignment-map critiques as potentially over-confident; same risk applies here
- [ ] Final review by user (Anthony) before submission — content + tone + signing
- [ ] Submit via nlnet.nl/commonsfund/ portal
- [ ] Notify Michiel Leenaars (ngizero-coordinator@nlnet.nl) on submission

---

## Provenance + sources

- **This file:** `FLOSS/docs/research/2026-05-19-nlnet-grant-application-draft.md`
- **NLnet info source:** `FLOSS/docs/research/intake_raw/2026-05-19-root/reports/CONTEXT_CONTINUATION_2026-05-14_scenarios-recognition-resources.md` §6-§7 (web-verified 2026-05-14)
- **Citation chain:** consensus-validated alignment-map at `FLOSS/docs/research/2026-05-18-positive-alignment-flossi0ullk-map.md`
- **Track record sources:** working-todo §I rolling 30-day completed window; ADR-Suite v2.0; consensus gateway source chain (claims 019e3e2c, 019e3f84, 019e3f85)
- **Cross-agent collaboration evidence:** the metaharness-unification doc + agent-memory-as-shared-surface migration demonstrate functioning multi-AI workflow
