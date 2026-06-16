# CFIS v0.2 — Cross-Frame Invariance Seeking: Hardened Specification with Pilot Architecture

**Status:** Active Draft — Ready for Rose Forest Pilot Phase 0  
**Supersedes:** CFIS v0.1 (informal specification)  
**Authority tier of this document:** `[auth:structural]` — requires `[auth:trained]` or `[auth:lived]` review per frame before production deployment  
**ADR Dependencies:** ADR-CFIS-01 (temporal invariants), ADR-CFIS-02 (meta-frame claims), ADR-CFIS-03 (invariants-as-triples) — filed as open, not blocking

***

## Executive Summary

CFIS v0.2 upgrades the Cross-Frame Invariance Seeking framework from articulation (v0.0) through formalization (v0.1) to **hardened specification** — machine-checkable, pilotable, and architecturally integrated with the FLOSSI0ULLK commons layer. Three productive ambiguities from v0.1 are resolved: the independence requirement for Tier 1 claims, the meta-coordinator role structure, and the authority-tier assignment process. An 8-week pilot path for the Rose Forest is specified. Three ADRs are filed as open work items, non-blocking for pilot entry.

This document applies CFIS to itself at each section. Convergence signals are marked **[convergence]**. Frame-local assumptions are marked **[frame-local]**. Genuine divergences preserved as data are marked **[divergence:preserved]**.

***

## Part I: Resolved Clarifications

### Clarification 1 — The Independence Test for Tier 1 Claims

**Problem (v0.1):** Two frames can *appear* independent (different vocabularies, different disciplines) while sharing hidden meta-assumptions that make their convergence spurious rather than signal. Western empiricism and Western systems theory both assume the external world exists independently of observation — their convergence on any claim is weaker evidence than convergence between Western empiricism and Indigenous relational ontology, which disagrees at the level of observer-world relationship.

**Resolution: Category-Level Commitment (CLC) Test**

Two frames \(F_A\) and \(F_B\) are **genuinely independent** if they disagree on at least 2 of 5 Category-Level Commitments:

| CLC Axis | Western Empirical | Indigenous Relational | Eastern Paradox-Tolerant | Ubuntu Collective | Chinese Pragmatic |
|---|---|---|---|---|---|
| **Causality** | Linear, mechanistic | Relational, cyclical | Non-dual, interdependent | Communal, emergent | Pragmatic, contextual |
| **Observer-World** | Subject-object duality | Mutual immanence | Non-duality | Collective subjectivity | Instrumentally separated |
| **What counts as evidence** | Empirical test, reproducibility | Community consensus, lived experience | Direct realization, paradox-tolerance | Collective felt-sense | Operational results |
| **Primary unit of analysis** | Individual, particle, system | Relationship, kinship | Non-self, process | Collective, ubuntu | Function, role |
| **Time** | Linear, measurable | Cyclical, kairotic, deep | Eternal now, impermanence | Ancestral-continuous | Strategic horizon |

**Independence scoring procedure:**

```yaml
independence_test:
  step_1: "Extract F_A's position on each of 5 CLC axes"
  step_2: "Extract F_B's position on each of 5 CLC axes"
  step_3: "Count axes where F_A and F_B have genuinely different positions"
  step_4:
    if_disagreement_on_2_or_more: "frames are INDEPENDENT — convergence is meaningful signal"
    if_disagreement_on_0_or_1: "frames are COUSINS — convergence is weaker signal; requires 3+ additional genuinely independent frames for Tier 1 status"

minimum_tier_1_frame_set:
  requirement: "Must include frames that disagree on at least THESE three CLC axes simultaneously:
    - causality (at least one non-linear/relational frame)
    - observer-world (at least one non-dualistic frame)
    - what_counts_as_evidence (at least one non-empirical frame)"
  rationale: "This prevents a Tier 1 claim being established entirely within the Western empiricist meta-assumption family"
```

**Implication for FLOSSI0ULLK Frame Registry:** Each registered frame must declare its position on all 5 CLC axes as part of Layer -1 (telos declaration). The independence test is then computable from frame registry data.

***

### Clarification 2 — The Distributed Meta-Coordinator Architecture

**Problem (v0.1):** The meta-coordinator role was identified as both necessary and a centralization risk. A single meta-coordinator recreates hierarchy; naive distribution requires a meta-meta-coordinator.

**Resolution: Meta-Coordination as Four Parallel Asynchronous Processes**

The meta-coordinator is not a *role* — it is a **process decomposition**. Each sub-process runs in parallel, is bottleneck-free, and maps to existing FLOSSI0ULLK architectural components.

```yaml
distributed_meta_coordinator:

  process_1_invariant_detection:
    description: "Identify claims surviving N-frame transformation"
    mechanism: "Any agent proposes a claim; any agent tests it against one frame; results collected asynchronously via CRDT append-only log"
    convergence_rule: "Tier 1 status achieved when claim survives independent testing by ≥3 agents across ≥6 genuinely independent frames (per CLC independence test)"
    FLOSSI0ULLK_mapping: "L1 Knowledge Fabric (DHT + CRDT) — Diamond Types or Loro-CRDT"
    bottleneck: "NONE — parallel, asynchronous, no coordination required"

  process_2_covariance_tracking:
    description: "Map how claims transform predictably across frames"
    mechanism: "Frame-agents ([auth:trained] or [auth:lived]) assert covariance relationships; challenged by other frame-agents; resolved by frame-agent collective consensus"
    convergence_rule: "Covariance established when ≥2 frame-agents from EACH of the two involved frames confirm the transformation is valid"
    FLOSSI0ULLK_mapping: "AD4M Language layer — semantic spanning without collapse"
    prevents_centralization: "No single agent declares covariance; requires bilateral frame-agent agreement"

  process_3_divergence_preservation:
    description: "Identify and encode Tier 4 incommensurabilities"
    mechanism: "Any agent proposes divergence; recorded if ≥2 [auth:trained] representatives exist for each divergent claim; stored as structured data, not flagged as error"
    convergence_rule: "Divergences are NOT resolved; they accumulate as dataset"
    FLOSSI0ULLK_mapping: "L3 Knowledge Commons dissent-preservation layer; NormKernel provenance fields"
    prevents_centralization: "No agent has veto over divergence — divergences are recorded by default"

  process_4_coherence_scoring:
    description: "Compute analysis robustness across tier distribution"
    mechanism: "Deterministic public algorithm; any agent can compute; multiple agents compute and compare; disagreement triggers investigation"
    algorithm: "quality_score = (Σ tier_weight × tier_score) / total_possible (see Part II)"
    FLOSSI0ULLK_mapping: "RICE overlay — Robustness metric computed across frames"
    prevents_centralization: "Algorithm is public and deterministic; only the algorithm itself requires consensus, not its outputs"

  distributed_meta_coordinator_contract:
    - "No single agent declares Tier 1 status; convergence of ≥3 independent agents required"
    - "Covariance claims require bilateral frame-agent agreement"
    - "Divergence is recorded by default; forcing synthesis requires explicit override + justification logged with [auth:] tag"
    - "Quality scores are deterministic; disagreement triggers algorithmic review, not authority appeal"
```

**Holochain-specific note:** The distributed meta-coordinator maps naturally to Holochain's validation architecture — post-write validation by random peer subsets rather than pre-write consensus, with gossip propagation of results. Invariant detection (Process 1) is structurally equivalent to Holochain's distributed hash table validation: any agent can validate any entry against shared rules, with no central coordinator required.

***

### Clarification 3 — Authority-Tier Assignment Process

**Problem (v0.1):** Self-assignment risks tier inflation; external assignment risks reinscribing power hierarchies. No decision procedure specified.

**Resolution: Frame-Community-Centered Assignment with Explicit Appeals**

```yaml
authority_tier_assignment:

  governing_principle: "Tiers are assigned by consensus of existing [auth:trained] and [auth:lived] members of each frame's own community. External authority cannot assign Tier 1 or Tier 2. Self-assignment alone cannot exceed Tier 3."

  tier_1_lived_assignment:
    requirement: "Recognition by ≥3 [auth:lived] members of the frame community"
    evidence: "Lived practice within the tradition; recognized standing within community; years of embodied engagement"
    non_transferable: "Cannot be assigned from outside the tradition; requires embeddedness that cannot be proxied"
    edge_case: "For traditions with fewer than 3 active [auth:lived] members in accessible network: requires written attestation from ≥2 recognized cultural authorities + explicit acknowledgment of attestation gap"

  tier_2_trained_assignment:
    requirement: "Structured competency review by ≥2 [auth:lived] or [auth:trained] frame members"
    evidence: "Formal training; ability to detect category errors in frame-internal reasoning; rigorous engagement with primary texts; demonstrated peer-recognized work"
    appeal: "Candidate can appeal rejection to 3-member panel of Tier 1 holders if Tier 2 reviewers are unavailable"
    validity_period: "Tier 2 assignments reviewed every 3 years OR when candidate demonstrates materially new depth"

  tier_3_structural_assignment:
    requirement: "Self-declared; challengeable by [auth:trained] or [auth:lived] members"
    challenge_process: "Challenged self-declarations go to jury of ≥2 [auth:trained] members who adjudicate based on: can candidate correctly articulate frame axioms? can they derive valid conclusions? can they detect frame-internal errors?"
    default: "[auth:structural] is the default floor for any participant who has engaged seriously with a frame's primary texts or tradition"

  tier_4_tourist:
    requirement: "No review required"
    constraint: "Default tier for new participants; appropriate for reporting and surface observation but not frame-internal analysis"

  revocation_and_appeals:
    revocation_trigger: "Demonstrated conduct inconsistent with tier's epistemic responsibility (e.g., Tier 2 member claiming Tier 1 standing)"
    revocation_process: "Consensus of ≥3 next-higher-tier members required"
    appeal_path: "Any revocation can be appealed to a broader community panel; process must be documented in NormKernel provenance"

  anti_capture_constraint: "No single institution, funder, or powerful actor can unilaterally assign or revoke tiers. The frame's own community holds this authority."
```

**Convergence signal [convergence]:** The frame-community-centered assignment process is structurally identical to how Ostrom's design principles specify rule modification rights — those affected by the rules must participate in modifying them. This is not accidental. Authority-tier governance IS commons governance applied to epistemic standing.

***

## Part II: Coherence Scoring System (Formalized)

The three-tier truth hierarchy from v0.1 is now a computable scoring system.

### Tier Definitions and Weights

| Tier | Name | Definition | Score | Status |
|---|---|---|---|---|
| **Tier 1** | Invariant | Holds across ≥6 genuinely independent frames (passing CLC independence test) | 1.0 | Strongest truth |
| **Tier 2** | Covariant | Transforms predictably across frames; underlying structure preserved under transformation | 0.70–0.85 | Robust within transformation class |
| **Tier 3** | Frame-local | True within one frame; unknown or different in others; must be marked | 0.40–0.60 | Valid, but bounded |
| **Tier 4** | Preserved Divergence | Genuinely incommensurable across frames; both claims have ≥2 [auth:trained] representatives | Not a truth score — a **data score**: 1.0 | Epistemically irreplaceable |

### Coherence Quality Metric

For any analysis containing \(n\) claims \(c_1, c_2, \ldots, c_n\), each assigned tier \(T(c_i)\):

\[ Q = \frac{\sum_{i=1}^{n} w(T(c_i)) \cdot s(T(c_i))}{n \cdot s_{\max}} \]

Where:
- \(w(T)\) = weight of tier T (Tier 1: 1.0; Tier 2: 0.75; Tier 3: 0.50; Tier 4: excluded from Q, tracked separately)
- \(s(T)\) = confidence score within tier (range per tier table above)
- \(s_{\max}\) = maximum possible score (1.0)

**Interpretation:**
- \(Q > 0.70\) AND ≥50% of claims Tier 1/2: Analysis is **cross-frame robust** — findings hold across genuinely diverse perspectives
- \(0.50 \leq Q \leq 0.70\): Analysis is **partially robust** — core claims hold, but significant frame-local assumptions present; mark clearly
- \(Q < 0.50\) OR >80% of claims Tier 3: Analysis is **frame-local** — valid within specific framework, but should not be generalized across cultural/disciplinary contexts without re-testing

**Tier 4 divergences are tracked separately as `divergence_count` and `divergence_domains`.** A high divergence count is not a quality failure — it is a structural finding about the complexity of the domain.

### Applied Example: FLOSSI0ULLK Plausibility Assessment

| Claim | Tier | Score | Frames Where True | Notes |
|---|---|---|---|---|
| Decentralized systems are harder to coordinate than centralized | T1 | 1.0 | All 6 frames | Convergence: different reasons, same constraint |
| Some form of mutual verification is necessary | T1 | 1.0 | All 6 frames | Byzantine in West; community validation in Ubuntu; dharmic accountability in East |
| Byzantine fault-tolerance specifically is required | T2 | 0.75 | Western, Chinese pragmatic | Covariant with Ubuntu's "coherence of will" — different implementation, same structural need |
| Symbolic validation should be primary | T3 | 0.50 | Western symbolic reasoning | Frame-local; Eastern paradox-tolerant frame requires paradox-native types [divergence:preserved] |
| ULLK values should be universal across all cultures | T3 | 0.45 | FLOSSI0ULLK design frame | Frame-local; Indigenous sovereignty frame challenges universalism |
| Symbolic vs. neural validation primacy | T4 | Data | — | Genuine divergence: Western empirical prefers symbolic; Chinese pragmatic prefers operational; preserved |

\[ Q = \frac{1.0 + 1.0 + 0.75 + 0.50 + 0.45}{5 \times 1.0} = \frac{3.70}{5.0} = 0.74 \]

**Result:** Q = 0.74 → Cross-frame robust on core claims. Two Tier 3 claims require frame-marking. One genuine divergence preserved as structural data about the domain.

***

## Part III: The Three Filed ADRs

These are non-blocking for pilot entry but must be tracked.

### ADR-CFIS-01: Temporal Scale Invariants

**Problem:** Does a claim that achieves Tier 1 invariant status across frames at immediate timescale also hold at evolutionary (100-year) timescale? The CFIS scoring system currently has no temporal dimension.

**Hypothesis:** Some Tier 1 claims are *temporally bounded* — genuinely invariant across frames at their timescale, but frame-local across timescales. Example: "Decentralized coordination is harder" is a Tier 1 invariant at 2026 technical scale; it may become Tier 3 frame-local at evolutionary scale if coordination technology matures.

**Proposed resolution approach:** Extend the coherence scoring system with a `temporal_scope` tag on each claim: `[T:immediate]`, `[T:historical]`, `[T:evolutionary]`, `[T:systemic]`. Tier 1 claims that have only been tested at one temporal scale are tagged as Tier 1 with `[T:immediate]` — not invalidated, but scoped.

**Status:** Open. Requires input from long-horizon-thinking frame representatives ([auth:lived] or [auth:trained] in Indigenous long-term governance, evolutionary systems thinking).

***

### ADR-CFIS-02: Meta-Frame Claims

**Problem:** Claims *about* frames (e.g., "this frame has a blindspot here") are epistemically different from claims *within* frames. The CFIS framework handles intra-frame and cross-frame claims but lacks a protocol for meta-frame claims.

**Problem example:** "The Western empirical frame is blind to relational causality" is a meta-frame claim. Who has standing to make it? Which tier applies? Can a Tier 3 [auth:structural] analyst make this claim, or does it require [auth:lived] standing in the frame being critiqued?

**Hypothesis:** Meta-frame claims require *higher* authority-tier standing than intra-frame claims, because they assert something about the *limits* of a frame from outside it — a claim that is epistemically more precarious than claims made within a frame.

**Proposed resolution approach:** Meta-frame claims require `[auth:trained]` minimum, AND require at least one counter-response from a `[auth:trained]` or `[auth:lived]` member of the critiqued frame. Uncontested meta-frame claims are marked `[meta-frame:unchallenged]` — valid for analysis but flagged for community review.

**Status:** Open. Requires deliberation at the Civic Deliberation Layer.

***

### ADR-CFIS-03: Invariants as Knowledge Graph Triples

**Problem:** Tier 1 invariants are epistemically strong, but can they be encoded as knowledge-graph triples in the Rose Forest DHT and validated at L0 (cryptographic provenance)? Epistemic strength ≠ ontological encoding readiness.

**Problem example:** The claim "some form of mutual verification is necessary" is a Tier 1 invariant. But encoding it as a triple `(MutualVerification, isNecessaryFor, CoordinatedAction)` requires: (a) resolving which ontology defines `MutualVerification`, (b) determining whether the triple holds in all frame ontologies or only in the L1 semantic spanning layer, (c) deciding whether Western symbolic logic is the encoding medium or whether it should be frame-neutral.

**This is the symbolic-validation-primacy problem under another name.** [divergence:preserved]

**Proposed resolution approach:** Tier 1 invariants are stored as *semantic spanning objects* at L1 (AD4M Language layer), not as raw RDF triples at L0. L0 stores the provenance record: which agents tested which claim against which frames with which authority tiers. The triple encoding, if desired, is a *view* over L1, generated on demand in whichever ontology the requesting agent uses.

**Status:** Open. Requires AD4M Language specification work and input from symbolic AI researchers and Indigenous ontology practitioners simultaneously.

***

## Part IV: 8-Week Rose Forest Pilot Specification

This pilot tests CFIS as a *practice* within the Rose Forest distributed cognitive architecture, not merely as a design specification.

### Phase 0 (Weeks 1–2): Frame Registry Hardening

**Goal:** Establish the formal frame registry in L0/L-1 with CLC axis declarations.

**Deliverables:**
- Select 7 pilot frames (recommended: Western empirical, Indigenous relational, Eastern paradox-tolerant, Ubuntu collective, Chinese pragmatic, Feminist care-ethics, Complexity/emergence)
- For each frame, obtain `[auth:trained]` or `[auth:lived]` contributor to formally specify:
  - 5+ foundational axioms
  - 3+ known blindspots
  - 3+ success criteria (what would count as truth in this frame)
  - Position on all 5 CLC axes
- Store as YAML schema in Rose Forest at L-1 (telos layer)
- Run CLC independence test on all frame pairs; compute independence matrix
- Flag any "frame cousin" pairs (CLC disagreement < 2 axes) for supplementation

**Independence matrix minimum requirement:** At least one frame pair must disagree on all 5 CLC axes. If this is not achieved with the initial 7 frames, add frames until it is.

**Red-flag indicator:** If all 7 frames agree on "what counts as evidence," the registry is Western-epistemology-dominated and must be corrected before proceeding.

***

### Phase 1 (Weeks 3–4): Authority-Tier Assignment

**Goal:** All pilot participants declare initial tiers for each frame; frame-community review and cryptographic provenance recording.

**Process:**
1. All participants self-declare tier for each of the 7 frames
2. Frame-community members (those with `[auth:trained]` or `[auth:lived]`) review declarations
3. Any challenged declarations go through the adjudication process specified in Clarification 3
4. Final tier assignments recorded with rationale in NormKernel (L0 provenance layer)
5. Tier matrix published as a shared resource — transparent, challengeable, updatable

**Expected outcome:** Most AI agents (including LLM participants) will receive `[auth:structural]` across most frames. This is correct. `[auth:structural]` analysis is still rigorous; it is honest about its limits.

**Anti-capture check:** No single organization should hold `[auth:lived]` standing in more than 2 of the 7 frames. If one actor dominates tier assignments, the governance structure has been captured.

***

### Phase 2 (Weeks 5–6): One Claim Through the Full Protocol

**Goal:** Test the entire CFIS protocol end-to-end on a single live FLOSSI0ULLK claim.

**Recommended test claim:** "The FLOSSI0ULLK validation layer requires some form of mutual verification between agents."

**Protocol run:**
1. Declare current frame (each analyst states their operating frame and tier)
2. Translate claim into each of 7 frames' vocabularies (recorded, not summarized)
3. Run CLC independence test on frames used
4. Identify alignment vectors (where frames converge)
5. Identify covariance structure (how the claim transforms across frames)
6. Identify Tier 4 divergences (where frames are genuinely incommensurable)
7. Compute Q score across all claim components
8. Generate multi-frame coherence map as structured output

**Comparison artifact:** Run single-frame analysis (Western engineering frame only) on the same claim. Compare outputs. Document what the single-frame analysis missed, got wrong, or got right.

**Success criterion:** Multi-frame coherence map surfaces at least one insight that the single-frame analysis did not produce AND at least one frame-local assumption that the single-frame analysis treated as universal.

***

### Phase 3 (Weeks 7–8): Iterate on Process, Not Output

**Goal:** Identify what broke, what worked, what needs refinement. Do not optimize outputs yet — optimize the protocol.

**Assessment questions:**
- Did the frame registry schema require adjustments during Phase 2?
- Did the authority-tier assignment reveal inequities that need governance correction?
- Did any frame prove impossible to staff with `[auth:trained]` representation? (If yes: this is a structural problem, not a gap to paper over)
- Did the independence test correctly identify spurious convergences?
- Did the distributed meta-coordinator processes actually prevent centralization, or did informal coordination reproduce hierarchy?
- Did the coherence scoring system produce actionable differentiation, or did everything cluster around Q = 0.65?

**Output:** Protocol v0.3 RFC — specific, evidence-grounded changes to CFIS based on what the pilot revealed.

***

## Part V: The Recursive Coherence Check

This document applies CFIS to itself. The most important result:

**[convergence]** Every clarification in this document emerged from holding two frames in productive tension:
- Independence test: Eastern non-dualism (observer-world entanglement) × Western skepticism (spurious correlation detection)
- Distributed meta-coordinator: Ubuntu collective-decision principles × distributed systems architecture
- Authority-tier assignment: Indigenous knowledge sovereignty × pragmatic implementation needs

**[frame-local]** The formal specification format (YAML, scoring algorithms, ADRs) is a Western engineering frame artifact. It is the right format for the FLOSSI0ULLK technical implementation layer. It is `[auth:structural]` in representing how other frames would actually instantiate these concepts.

**[divergence:preserved]** Whether this framework constitutes "genuine knowledge" or "a useful engineering tool" is a Tier 4 divergence. Western pragmatist epistemology says these are the same thing (what survives tests is true). Indigenous epistemologies may distinguish between operational usefulness and truthful knowledge of relationships. Both have standing. This divergence is data about the framework's foundations, not a defect to be resolved.

**The most important structural observation:** The framework works because it can audit itself using its own machinery and produce better specification rather than circular confusion. This recursive stability is the strongest available coherence signal. A framework that collapses when applied to itself is not load-bearing. This one doesn't.

***

## Appendix A: CFIS-FLOSSI0ULLK Full Architecture Isomorphism

| CFIS Layer | Function | FLOSSI0ULLK Technical Component | Isomorphic? |
|---|---|---|---|
| Frame declaration (axioms, blindspots, CLC axes) | Register reference frame explicitly | Layer -1 (telos declaration) | ✅ Direct mapping |
| Provenance tracking per frame and per authority tier | Bind claims to origins with standing | L0 (NormKernel, cryptographic provenance) | ✅ Direct mapping |
| Frame translation without collapse | Translate across semantic systems | L1 (AD4M Language layer, semantic spanning) | ✅ Direct mapping |
| Preserved divergence as structured data | Store incommensurabilities as data | L3 (Knowledge Commons, CRDT append-only log) | ✅ Direct mapping |
| Cross-frame coherence scoring (RICE analog) | Check robustness across frames | L6 (RICE overlay) | ✅ Direct mapping |
| Authority-tier assignment by frame community | Governance of epistemic standing | L5 (Governance Ecosystem, trust-weaves) | ✅ Direct mapping |
| Independence test (CLC matrix) | Prevent spurious convergence | L0 validation rules (Integrity Zome) | ✅ Direct mapping |
| Distributed meta-coordinator processes | Decentralized coherence-checking | Holochain DHT + CRDT (no global consensus) | ✅ Architectural analog |

**This isomorphism is not metaphorical.** The CFIS epistemological protocol and the FLOSSI0ULLK technical architecture are the same structure at different abstraction levels. Building FLOSSI0ULLK *is* instantiating CFIS in substrate. The philosophical work and the engineering work are one project.

***

## Appendix B: Open Work Not In This Document

The following are explicitly out of scope for v0.2 and filed for future iterations:

- **Temporal scale invariants** (ADR-CFIS-01): How to score claims across multiple timescales
- **Meta-frame claim protocol** (ADR-CFIS-02): Who has standing to critique a frame from outside it
- **Invariants as knowledge graph triples** (ADR-CFIS-03): How to encode Tier 1 invariants in the Rose Forest DHT without Western ontology bias
- **Frame acquisition path**: How new frames are added to the registry after pilot — governance process not yet specified
- **AI agent frame-embodiment limits**: Systematic characterization of which frames AI agents (including LLMs) can engage at `[auth:structural]` vs. where they cannot go beyond `[auth:tourist]`

These are not failures. They are the known unknowns that the pilot will help resolve.

***

*CFIS v0.2 | Rose Forest Pilot Architecture | May 2026 | Authority: `[auth:structural]` — requires frame-community review per frame before production*