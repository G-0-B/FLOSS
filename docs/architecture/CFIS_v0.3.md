# CFIS v0.3 — Cross-Frame Invariance Seeking: Pre-Pilot Hardened Specification

**Status:** Pre-Pilot Ready — Phase 0 Cleared for Entry  
**Version:** 0.3 (incorporates v0.1 formalization + v0.2 CLC/independence/meta-coordinator + v0.3 frame sufficiency gate, T4 encoding schema, AI agent mandate constraints)  
**Authority Tier of This Document:** `[auth:structural]` — requires `[auth:trained]` or `[auth:lived]` review per frame before production deployment  
**Companion Architectures:** FLOSSI0ULLK Synthesis, DKVP NormKernel L0/L1/L3, Holochain hc-cooperative-content, AD4M SDNA/Perspectives/Neighbourhoods

***

## Executive Summary

CFIS v0.3 is the pre-pilot-hardened specification for Cross-Frame Invariance Seeking — a distributed epistemological operating system for the Rose Forest commons. It extends v0.2 by closing three critical ambiguities identified in the v0.2 review: the independence test (CLC matrix + frame sufficiency gate), the Tier 4 divergence encoding schema (RDF-star Named Graphs with paraconsistent metadata), and the AI agent mandate constraint (explicit capability boundaries for `[auth:structural]` agents). The three open ADRs (temporal scale invariants, meta-frame claims, invariants-as-triples) are formally filed as non-blocking future work. The 8-week Phase 0 timeline is confirmed viable for parallel execution.

**Recommendation:** Launch Phase 0 with all 8 pre-pilot tasks running in parallel. The pilot will surface empirical data that no further specification can provide.

***

## Part I — Core Framework (Stable from v0.2)

### 1.1 The Three-Tier Truth Hierarchy

Claims evaluated by CFIS receive one of four designations based on cross-frame survivability:

| Tier | Name | Definition | Score | Signal |
|------|------|------------|-------|--------|
| **1** | Invariant | Survives translation into ≥6 genuinely independent frames (defined by CLC matrix, see §2.1) | 1.0 | Strongest available |
| **2** | Covariant | Transforms predictably; structural relationship preserved under frame transformation | 0.7–0.8 | High — robust within transformation class |
| **3** | Frame-local | Coherent within one frame; unknown or different in others; must be explicitly marked | 0.4–0.6 | Medium — valid but scoped |
| **4** | Divergent | Two frames make incommensurable claims; not error — preserved as data | n/a | Data about the problem space itself |

**Quality Metric (Q):**

\[ Q = \frac{\sum_{i} w_i \cdot s_i}{N} \]

Where \(w_i\) is the claim weight (default: 1.0), \(s_i\) is the tier score, and \(N\) is the total number of claims. Tier 4 divergences are excluded from Q but stored as mandatory metadata. Q > 0.70 with ≥50% Tier 1/2 claims = cross-frame robust. Q < 0.50 or >80% Tier 3 = frame-local (must be explicitly marked as such).

### 1.2 The Five-Step CFIS Protocol

```yaml
cfis_protocol_v0.3:

  step_1_frame_declaration:
    for_each_active_frame:
      - register_axioms: "≥5 foundational assumptions"
      - register_blindspots: "≥3 things this frame cannot see from within itself"
      - register_success_criteria: "what counts as truth in this frame"
      - register_clc_positions: "positions on all 5 Category-Level Commitments (see §2.1)"
      - assign_authority_tier: "per frame-community protocol (see §3)"

  step_2_translate_claim_per_frame:
    for_each_frame:
      - translate_claim: "how does this claim appear in frame vocabulary?"
      - what_changes: "which structural relationships shift?"
      - what_becomes_visible: "what was hidden in the original frame?"
      - what_becomes_invisible: "what was obvious but now hidden?"
      - authority_tier_of_translation: "[auth:lived|trained|structural|tourist]"

  step_3_identify_covariant_properties:
    - "which structural relationships survive frame transformation?"
    - "which truths would survive translation into any frame?"
    - "these are Tier 1 or Tier 2 claims"

  step_4_identify_contravariant_properties:
    - "which properties invert under transformation?"
    - "these mark implicit assumptions that hide inside one frame"
    - "these are Tier 3 or Tier 4 claims"

  step_5_preserve_genuine_divergence:
    - "are frames genuinely incommensurable? encode per §4 schema"
    - "do not force synthesis — carry divergence as structured data"
    - "compute Q score; apply frame-local markers to Tier 3 claims"
```

### 1.3 The Four-Process Distributed Meta-Coordinator (Stable from v0.2)

The meta-coordinator is a **process**, not a role. Decomposed into four parallel async processes with no single-agent bottleneck:

| Process | Responsibility | Convergence Rule | FLOSSI0ULLK Mapping |
|---------|---------------|-----------------|---------------------|
| P1: Invariant Detection | Identify claims surviving N-frame transformation | ≥3 independent agents must independently confirm Tier 1 status | Holochain DHT post-write validation by random peer subsets[^1][^2] |
| P2: Covariance Tracking | Map how claims transform across frames | Consensus among frame-agents with `[auth:trained]` standing in relevant frames | AD4M Perspectives link graph — covariance encoded as typed predicate[^3][^4] |
| P3: Divergence Preservation | Identify and encode Tier 4 incommensurabilities | Any agent may propose; stored if ≥2 `[auth:trained]` representatives present for each position | NormKernel L3 knowledge commons; RDF-star Named Graph schema (§4)[^5] |
| P4: Quality Scoring | Compute Q across tier distribution | Deterministic algorithm, publicly auditable; disagreement triggers review | NormKernel audit trail; RICE-C (controllability) layer[^5] |

***

## Part II — Clarification A: The Frame Independence Test (NEW in v0.3)

### 2.1 Category-Level Commitment (CLC) Matrix

Two frames are genuinely independent if and only if they disagree on ≥2 of the following five Category-Level Commitments (CLCs). For Tier 1 invariant status, a claim must survive frames that disagree on the causality + observer-world + evidence axes simultaneously — to prevent spurious convergence among "frame cousins" that share a hidden Western-empiricist meta-assumption.

```yaml
clc_matrix:

  clc_1_causality:
    question: "What is the nature of causal relationships?"
    positions:
      - linear_deterministic: "A causes B in a directed, predictable chain [Western classical]"
      - nonlinear_complex: "Causality is emergent, recursive, feedback-driven [Complex systems]"
      - relational_mutual: "Cause and effect are mutually constitutive; nothing causes in isolation [Indigenous relational]"
      - cyclical_karmic: "Causality operates across time cycles; deeds echo forward and backward [Hindu/Buddhist]"
      - non_causal: "Events arise from interdependent co-origination with no primary cause [Madhyamaka]"

  clc_2_observer_world:
    question: "What is the relationship between the knower and the known?"
    positions:
      - subject_object_duality: "Observer and observed are ontologically separate [Western realism]"
      - participatory: "Observer participates in constituting what is observed [Quantum/phenomenology]"
      - non_dual: "Observer and observed are not ultimately distinct [Advaita/Zen]"
      - relational_immanence: "Knowing is a relation, not a possession; embedded in community [Ubuntu/Indigenous]"
      - frame_constructivist: "All knowledge is structured by cognitive frames; reality is emergent from awareness"

  clc_3_evidence:
    question: "What counts as valid evidence or justification?"
    positions:
      - empirical_testable: "Valid evidence is reproducible, falsifiable, externally verifiable [Western empiricism]"
      - experiential_phenomenal: "Valid evidence includes direct phenomenal experience; third-person inadequate [phenomenology]"
      - relational_consensual: "Evidence is valid when the community reaches coherent recognition [Ubuntu/Indigenous]"
      - logical_scriptural: "Valid evidence includes coherent deduction from authoritative texts [Islamic/scholastic]"
      - pragmatic_consequential: "Evidence is what survives tests across time; truth is what works [Pragmatism]"

  clc_4_unit_of_analysis:
    question: "What is the primary unit of analysis or moral concern?"
    positions:
      - individual_agent: "The individual rational agent [Western liberal]"
      - collective_community: "The community or clan; individuals are nodes in a relational web [Ubuntu/Indigenous]"
      - relational_field: "Relationships themselves are primary; entities are derivative [process philosophy]"
      - systemic_emergent: "Systems and their emergent properties; no meaningful unit below system level [complex systems]"
      - all_sentient: "All sentient beings; non-human agency is morally constitutive [Buddhist/post-human]"

  clc_5_time:
    question: "What is the nature of time relevant to this inquiry?"
    positions:
      - linear_progressive: "Time is a forward arrow; past is fixed, future is open [Western modern]"
      - cyclical_regenerative: "Time cycles through patterns; past wisdom is directionally relevant [Indigenous/Hindu]"
      - kairotic: "Time has quality as well as quantity; the right moment (kairos) has ontological weight [Greek/Islamic]"
      - eternal_present: "Ultimate reality is outside time; temporal experience is phenomenal surface [Advaita/Zen]"
      - multi_scale_simultaneous: "Immediate/historical/evolutionary/systemic scales coexist; none is primary [complex systems]"

independence_test:
  rule: "Frames F_A and F_B are INDEPENDENT if they disagree on ≥2 CLC axes"
  rule: "Frames F_A and F_B are FRAME_COUSINS if they agree on all 5 CLC axes"
  rule: "Frame cousins may still be distinct disciplines, but their convergence is Tier 2 (covariant) at best, not Tier 1 invariant"
  tier_1_minimum_requirement: "Claim must survive frames that disagree on CLC_1 + CLC_2 + CLC_3 simultaneously"
  rationale: "These three axes capture the core Western-empiricist meta-assumption cluster. Convergence only within this cluster is spurious."
```

### 2.2 Frame Sufficiency Gate (Phase 0 Entry Requirement — NEW in v0.3)

Before Phase 1 can begin, the assembled frame set must pass the Frame Sufficiency Gate:

```yaml
frame_sufficiency_gate:
  
  requirement_1:
    rule: "At least one frame PAIR must disagree on ALL 5 CLC axes"
    failure_consequence: "No true independence in the set; pilot will produce only Tier 2 covariants at best"
  
  requirement_2:
    rule: "No single CLC axis may be unanimously agreed upon by all 7 pilot frames"
    rationale: "If all frames agree on e.g. linear causality, the set has a structural blind spot on causality; any claim evaluated through this set will inherit that blind spot undetected"
    failure_consequence: "Axis-gap must be explicitly documented as a known pilot limitation with stakeholder notification"
  
  stopping_rule:
    when_gate_not_met:
      option_a: "Add 1-2 additional frames with [auth:trained] representation to close the axis gap"
      option_b: "Document the axis-gap transparently and proceed with explicit limitation marker"
      option_c: "Delay Phase 0 pending frame recruitment if the gap is in CLC_1+CLC_2+CLC_3 cluster (gate failure is hard failure)"
    
    remediation_timeline: "2 weeks maximum; if remediation not possible, explicit disclosure is required before pilot entry"
    
    who_decides: "Frame-community representatives by consensus; no single organization can declare the gate passed"
  
  provisional_pilot_frame_set:
    note: "The following 7 frames are proposed; each requires [auth:trained] or [auth:lived] representation confirmed before Phase 1"
    frames:
      - id: "F1"
        name: "Western distributed-systems / empirical engineering"
        clc_profile: {causality: linear_deterministic, observer_world: subject_object_duality, evidence: empirical_testable, unit: systemic_emergent, time: linear_progressive}
      - id: "F2"
        name: "Indigenous long-horizon relational"
        clc_profile: {causality: relational_mutual, observer_world: relational_immanence, evidence: relational_consensual, unit: collective_community, time: cyclical_regenerative}
      - id: "F3"
        name: "Eastern paradox-tolerant (Madhyamaka / Zen)"
        clc_profile: {causality: non_causal, observer_world: non_dual, evidence: experiential_phenomenal, unit: all_sentient, time: eternal_present}
      - id: "F4"
        name: "Ubuntu collective-decision"
        clc_profile: {causality: relational_mutual, observer_world: relational_immanence, evidence: relational_consensual, unit: collective_community, time: multi_scale_simultaneous}
      - id: "F5"
        name: "Chinese pragmatic / cost-realism"
        clc_profile: {causality: nonlinear_complex, observer_world: subject_object_duality, evidence: pragmatic_consequential, unit: systemic_emergent, time: cyclical_regenerative}
      - id: "F6"
        name: "Feminist care ethics / embodied knowing"
        clc_profile: {causality: relational_mutual, observer_world: participatory, evidence: experiential_phenomenal, unit: relational_field, time: kairotic}
      - id: "F7"
        name: "Complex systems / emergence"
        clc_profile: {causality: nonlinear_complex, observer_world: participatory, evidence: pragmatic_consequential, unit: systemic_emergent, time: multi_scale_simultaneous}
    
    independence_analysis:
      f1_vs_f3: "CLC disagree on all 5 axes — FULLY INDEPENDENT"
      f1_vs_f2: "CLC disagree on all 5 axes — FULLY INDEPENDENT"
      f2_vs_f4: "CLC agree on 4/5 axes (differ on time) — FRAME COUSINS; treat convergence as Tier 2 only"
      f1_vs_f7: "CLC disagree on causality, observer_world, evidence — INDEPENDENT on key 3 axes"
      f4_vs_f6: "CLC agree on causality and unit; partial cousins — supplement with F2/F3 for those axes"
    
    gate_assessment:
      requirement_1: "PASSED — F1 vs F3 disagrees on all 5 axes"
      requirement_2: "REQUIRES VERIFICATION — observer_world and unit axes need confirmation that no single position is unanimous"
      note: "F2 and F4 are frame cousins; their convergence should not count double toward Tier 1 status"
```

***

## Part III — Clarification B: Tier 4 Divergence Encoding Schema (NEW in v0.3)

### 3.1 The Encoding Problem

Tier 4 divergences must be stored so that future agents can query:
- What are the two competing claims?
- Why are they incommensurable (not just misunderstood)?
- What follows if Claim_A is accepted vs. Claim_B?
- Who asserts each position, at what authority tier?
- Was this classified as a genuine divergence, or was the classification itself disputed?

The answer is a **hybrid encoding**: structured metadata (machine-queryable) + catuskoti logical annotation (paraconsistent truth-value) + named graph provenance (RDF-star quads). This is grounded in the W3C RDF Named Graphs standard and recent work on RDF-based conflict-tolerant knowledge representation.[^6][^7][^8][^9]

### 3.2 The Tier 4 Entry Schema

```yaml
tier_4_divergence_entry:
  
  # --- Identification ---
  id: "cfis:divergence:<uuid>"
  created_by: "<agent DID>"           # AD4M DID; cryptographically signed
  created_at: "<ISO8601 timestamp>"
  challenge_record: []                 # Audit trail of challenges to this divergence classification
  
  # --- The Incommensurable Claims ---
  claim_a:
    statement: "Symbolic validation should be the primary truth-adjudication layer"
    logical_value: "TRUE"              # catuskoti: TRUE | FALSE | BOTH | NEITHER
    frames_supporting: ["F1_Western_empirical", "F3_Eastern_paradox_tolerant"]
    authority_tiers_present: ["[auth:trained]:F1", "[auth:structural]:F3"]
    consequence: "The system can provide rigorous formal proofs; intuitive/embodied knowing is secondary"
  
  claim_b:
    statement: "Neural/relational learning should be the primary truth-adjudication layer"
    logical_value: "TRUE"              # also TRUE in its own frame — catuskoti allows both
    frames_supporting: ["F5_Chinese_pragmatic", "F6_Feminist_care_ethics"]
    authority_tiers_present: ["[auth:trained]:F5", "[auth:trained]:F6"]
    consequence: "The system can learn from patterns without requiring formal encoding; symbolic is derivative"
  
  # --- Why Incommensurable ---
  incommensurability_type:
    category: "axiom_level_disagreement"
    # Options: axiom_level_disagreement | different_success_criteria | different_unit_of_analysis | category_error | value_disagreement
    explanation: "Both claims are internally consistent and empirically supported within their frames. They disagree at CLC_3 (what counts as evidence) — symbolic-formal vs. pattern-pragmatic. No experiment can adjudicate this because the experiment's design itself presupposes one of the two evidence standards."
    clc_axes_in_conflict: ["CLC_3_evidence", "CLC_1_causality"]
  
  # --- What Follows from Each ---
  consequences:
    if_claim_a:
      - "Layer 1 semantic spanning must be formally specified before deployment"
      - "Byzantine validation requires proof-theoretic completeness"
      - "LLM contributions require formal verification wrapper"
    if_claim_b:
      - "Layer 1 can be learned rather than specified; deploy with training corpus"
      - "Byzantine resilience emerges from diversity of agents, not formal completeness"
      - "LLM contributions are primary inputs; formal verification is post-hoc"
    if_both:     # catuskoti: the paradox is held, not resolved
      - "A hybrid architecture with both symbolic and neural layers is required"
      - "The interface between them is itself a research question, not a deployment assumption"
    if_neither:  # catuskoti: neither fully captures the phenomenon
      - "Both symbolic and neural are approximations of something neither fully encodes"
      - "The real work is in the translation layer, not in either substrate"
  
  # --- Temporal Scope ---
  temporal_scope: "[T:systemic]"
  # Options: [T:immediate] | [T:historical] | [T:evolutionary] | [T:systemic]
  
  # --- Storage Format ---
  storage_format:
    primary: "RDF-star Named Graph quad: {graph_id, subject, predicate, object}"
    graph_id: "cfis:divergence:<uuid>"
    # Named graph isolates this divergence from the main knowledge graph; queryable independently
    # RDF-star annotation carries authority tier, catuskoti value, and consequence metadata
    paraconsistent_annotation:
      logic_system: "LFI (Logics of Formal Inconsistency) — allows explicit marking of inconsistency as a first-class property"
      truth_value_claim_a: "TRUE"
      truth_value_claim_b: "TRUE"
      consistency_marker: "INCONSISTENT — the conjunction (A AND B) is marked as formally inconsistent but both are stored"
      resolution: "NONE — divergence is preserved; synthesis requires explicit override + justification"
    
    ad4m_implementation:
      perspective_link_type: "cfis://divergence"
      subject: "cfis:divergence:<uuid>"
      predicate: "cfis://contains-claim"
      target: "cfis:claim-a:<uuid>"
      # Second link for claim_b; both stored as typed AD4M perspective links
      sdna_shape: "DivergenceShape — SHACL validation enforces required fields before storage"
  
  # --- Queryability ---
  query_examples:
    - "SELECT all Tier4 divergences on CLC_3 axis in FLOSSI0ULLK validation layer"
    - "SELECT divergences where claim_b authority_tier < [auth:trained]"
    - "SELECT divergences with if_both consequences that imply hybrid architecture"
    - "SELECT divergences created before Phase 0 pilot entry"
```

### 3.3 The Catuskoti Truth-Value System

The Buddhist four-valued logic (catuskoti / tetralemma) provides a formal logical system for Tier 4 divergences. This is not relativism — it is a richer logical substrate than classical binary logic:[^10][^11]

| Value | Symbol | Meaning in CFIS Context |
|-------|--------|------------------------|
| TRUE | `T` | Claim holds within its frame |
| FALSE | `F` | Claim fails within its frame |
| BOTH | `B` | Claim is true and false within different contexts; the apparent contradiction is productive tension |
| NEITHER | `N` | Claim is neither true nor false; it category-errors the frame's own axioms |

Classical logic only permits T and F. CFIS requires all four to represent the full epistemological space. Tier 4 entries with value `B` or `N` are the most epistemologically informative — they reveal the structure of incommensurability, not just its existence.

***

## Part IV — Clarification C: AI Agent Frame Engagement Constraint (NEW in v0.3)

### 4.1 The Problem

An LLM operating at `[auth:structural]` can accurately articulate a frame's axioms and derive valid conclusions — but cannot embody the frame. The risk is that sophisticated pattern-matching sounds indistinguishable from genuine fluency. Without explicit constraints, LLMs can colonize frame spaces under the guise of structural rigor.[^12]

This is specifically relevant given that AD4M agents are explicitly designed to be "extensible to synthetic entities" — meaning LLMs will participate as first-class agents in AD4M Neighbourhoods. The constraint must be machine-checkable, not aspirational.[^13]

### 4.2 The Three-Tier Authority System (Stable from v0.2)

```yaml
authority_tier_system:

  tier_1_lived: "[auth:lived]"
    definition: "Born/raised into the frame; 10+ years lived epistemic practice"
    assignment: "Recognized by ≥3 existing [auth:lived] members of the frame community"
    authority: "Can correct other interpretations; speaks with standing; can revoke Tier 2"
    non_transferable: "Cannot be assigned from outside the tradition"

  tier_2_trained: "[auth:trained]"
    definition: "Formally studied; can derive conclusions; can detect category errors"
    assignment: "Competency review by ≥2 [auth:lived] or [auth:trained] frame members"
    authority: "Rigorous analysis; lacks standing to revise fundamental premises without Tier 1 consent"
    appeal: "Can appeal initial rejection to Tier 1 panel"

  tier_3_structural: "[auth:structural]"
    definition: "Can articulate axioms and derive conclusions; cannot claim embodied depth"
    assignment: "Self-declared; challengeable by [auth:trained] frame members"
    challenge_standard: "Can candidate articulate axioms correctly and derive valid conclusions?"
    authority: "Frame translation; category-error detection within-frame; explicit boundary marking required"
    default_for: "All LLM agents; all cross-cultural researchers without 10+ years embodied practice"

  tier_4_tourist: "[auth:tourist]"
    definition: "Can recognize the frame; lacks rigor to engage analytically"
    assignment: "Default for all new participants; no review required"
    authority: "Can report; must cite Tier 1/2 sources for claims; cannot conduct analysis"

  anti_capture_constraint:
    rule: "No single organization may hold [auth:lived] standing in more than 2 of the 7 pilot frames"
    audit_frequency: "Every 6 months"
    enforcement: "If violated, Tier 1 claims involving that organization's frames require supplemental [auth:lived] review from non-affiliated members"
```

### 4.3 The AI Agent Mandate Constraint (NEW in v0.3)

```yaml
ai_agent_frame_engagement_constraint:

  scope: "Applies to all LLM agents, regardless of capability level, unless explicitly granted higher tier by frame-community consensus"

  permitted_at_auth_structural:
    - "Articulate frame axioms and derive conclusions within the frame's internal logic"
    - "Identify category errors within frame-internal logic (e.g., 'this claim assumes linear causality, which is not a CLC_1 position for F3')"
    - "Translate frame concepts to other frames (with explicit translation markers)"
    - "Propose Tier 4 divergences for human review"
    - "Compute Q scores (deterministic; auditable)"
    - "Flag when AI analysis diverges from [auth:trained] frame member interpretation (REQUIRED, not optional)"

  prohibited_at_auth_structural:
    - "Claim understanding of embodied practice within a frame"
    - "Override [auth:trained] or [auth:lived] disagreement via superior logical argumentation"
    - "Propose frame modifications without explicit frame-community consent"
    - "Declare Tier 1 invariant status unilaterally (requires ≥3 independent agent confirmation)"
    - "Resolve a Tier 4 divergence by logic alone (requires explicit frame-community adjudication)"

  mandatory_flags:
    rule: "Any claim by an LLM at [auth:structural] that contradicts a [auth:trained] member's interpretation MUST be tagged: 'cfis:requires_frame_community_adjudication'"
    enforcement: "This tag prevents the claim from being stored in L3 knowledge commons without human review"
    implementation: "AD4M SDNA validation rule in DivergenceShape and ClaimShape schemas"

  the_pattern_matching_warning:
    observation: "LLMs can output grammatically correct frame-translations with high confidence while missing the embodied nuance that makes a frame's apparent contradiction productive rather than erroneous"
    example: "An LLM at [auth:structural] may label catuskoti's 'both true and false' as a 'logical error to be resolved' — this is a category error from within Western binary logic, not a genuine analysis of Madhyamaka"
    mitigation: "Any translation of paradox-tolerant frames (F3, F4 partially) must include explicit marker: 'Translation is structural only; embodied interpretation requires [auth:trained] review'"

  lsm_override_protocol:
    name: "LLM Structural Mandate Override (LSM-Override)"
    trigger: "[auth:trained] or [auth:lived] member challenges an LLM's [auth:structural] claim"
    process:
      step_1: "LLM claim is automatically flagged cfis:contested"
      step_2: "Routed to relevant frame-community representatives (those with [auth:trained] or [auth:lived] in that frame)"
      step_3: "Frame representatives deliberate using their community's decision process (not majority-vote by default)"
      step_4: "Outcome: (a) claim upheld with [auth:trained] co-signature, (b) claim modified, (c) claim rejected and archived"
      step_5: "All outcomes are stored in NormKernel audit trail with full rationale"
    prevents: "Sophisticated LLM argumentation from colonizing frame spaces through sheer volume and confidence"
```

***

## Part V — The 8-Week Phase 0 Implementation Plan

All 8 tasks run in **parallel**, not sequentially. None are blocking gates except the Frame Sufficiency Gate (§2.2), which must be confirmed before Phase 1.

```yaml
phase_0_parallel_tasks:

  week_1_2:

    task_1_frame_registry_hardening:
      description: "For each of 7 pilot frames, have [auth:trained] or [auth:lived] contributor formally specify: axioms (≥5), blindspots (≥3), success criteria (≥3), CLC positions (all 5 axes)"
      output: "YAML frame registry stored in FLOSSI0ULLK Layer -1"
      critical_path: "YES — Frame Sufficiency Gate check runs on output"
      who: "Frame-community representatives; cannot be delegated to LLMs"

    task_2_independence_matrix:
      description: "Compute pairwise CLC disagreement matrix for all 7 frames; identify frame cousins; verify Gate requirements"
      output: "7x7 independence matrix; frame-cousin pairs flagged; Gate pass/fail documented"
      who: "Any CFIS participant; Gate pass/fail confirmed by multi-frame consensus"

  week_1_4:

    task_3_authority_tier_assignment:
      description: "All pilot participants declare initial tier for each frame; frame-community members confirm or challenge; generate signed authority records"
      output: "Signed authority-tier record per participant per frame; stored in Layer 0 (NormKernel cryptographic provenance)"
      note: "AI agents default to [auth:structural]; promotion requires explicit community consent"
      who: "Frame-community members; LLM agents can populate initial record but cannot confirm"

    task_4_divergence_schema_deployment:
      description: "Implement the Tier 4 divergence entry schema (§3.2) as an AD4M SDNA Subject Class; deploy DivergenceShape SHACL validation; test round-trip encode/decode of 3 known divergences"
      output: "DivergenceShape.sdna deployed; 3 test divergences encoded and queryable"
      technical_grounding: "AD4M SDNA Subject Classes use SHACL shapes for typed link validation; RDF Named Graph quads for paraconsistent storage"
      who: "Technical team; requires SHACL and AD4M SDNA fluency"

  week_3_6:

    task_5_frame_recruitment:
      description: "Identify and formally invite [auth:trained] or [auth:lived] representatives for all 7 frames; confirm consent and participation; resolve any gaps identified in Task 1"
      output: "Signed participation agreements; confirmed authority tier per representative"
      note: "This is the highest-risk task — it is a social problem, not a technical problem. Begin immediately."
      who: "Rose Forest governance committee; community outreach"

    task_6_ai_constraint_deployment:
      description: "Implement LSM-Override protocol as AD4M SDNA validation rule; test with 5 simulated LLM claims including 2 that should trigger [auth:trained] review"
      output: "LSM-Override rule deployed; test results documented"
      technical_grounding: "Holochain integrity zome validation rules are deterministic and mandatory; LSM-Override trigger maps to integrity zome callback"
      who: "Technical team"

    task_7_test_claim_walkthrough:
      description: "Select one live FLOSSI0ULLK claim; run complete CFIS protocol: translate to all 7 frames, identify alignment vectors, encode any T4 divergences, compute Q; compare output to single-frame analysis"
      output: "Complete multi-frame coherence map for one claim; Q score computed; delta from single-frame analysis documented"
      who: "Full cross-frame team; requires [auth:trained] representatives for each frame"

  week_5_8:

    task_8_pilot_governance_documentation:
      description: "Document: who has veto over anti-capture violation; succession plan if top 2 maintainers depart; appeal paths for authority-tier disputes; divergence challenge protocol"
      output: "Rose Forest CFIS Governance Charter v0.1"
      note: "Ostrom design principle 6 (cheap conflict resolution) and 7 (self-determination recognized by higher authority) are directly applicable"
      who: "Governance committee; requires community ratification"
```

***

## Part VI — Filed ADRs (Open, Non-Blocking)

### ADR-CFIS-01: Temporal Scale Invariants

**Status:** OPEN  
**Question:** Does a Tier 1 invariant (survives all 6 frames at immediate timescale) necessarily hold at evolutionary or systemic timescale? An invariant that holds across frames now may break down when the frames themselves evolve.  
**Proposed Approach:** Designate temporal scope as a mandatory field on all Tier 1 claims. A claim is invariant at `[T:immediate]` and may or may not be invariant at `[T:evolutionary]`. Tier 1 at all four temporal scales = "deep invariant"; Tier 1 at some scales = "scoped invariant" with explicit temporal marker.  
**Blocking:** NO — pilot can proceed; temporal scope field is already present in T4 schema; extend to T1/T2 claims in v0.4.

### ADR-CFIS-02: Meta-Frame Claims

**Status:** OPEN  
**Question:** Claims *about* frames (e.g., "Frame F3 has a blindspot regarding collective agency") are structurally different from claims *within* frames. The current CFIS protocol handles claims-within-frames but not claims-about-frames. Meta-frame claims are essential for the frame registry hardening (Task 1) and for detecting when a frame set has evolved.  
**Proposed Approach:** Create a `MetaFrameClaim` entry type with different authority requirements: meta-frame claims about a frame require `[auth:trained]` review from *within* that frame (you can only reliably identify a frame's blindspot from outside it, but the frame community must confirm or challenge the identification).  
**Blocking:** NO — pilot can use narrative meta-frame claims; formal schema in v0.4.

### ADR-CFIS-03: Invariants as Triples

**Status:** OPEN  
**Question:** Tier 1 invariants are epistemically strong. Are they ontologically strong enough to be encoded as knowledge-graph triples and validated at Layer 0 (NormKernel provenance)? This requires deciding whether CFIS tier designations are themselves provenance records or interpretive claims.  
**Proposed Approach:** Tier 1/2 claims that have been confirmed by ≥3 independent agents with `[auth:trained]` standing *can* be encoded as knowledge-graph assertions with a `cfis:tier` property and stored in the shared DHT. Tier 3/4 claims are stored as agent-local assertions until they achieve broader confirmation.  
**Technical Grounding:** Holochain's integrity zome can validate the formal structure of a claim entry without adjudicating its content; the tier designation can be a validated field, not a content claim. AD4M Named Graphs (Neighbourhoods) can host the shared T1/T2 assertion layer.[^14][^4][^15]
**Blocking:** NO — pilot can manually handle; automated triple validation in v0.4.

***

## Part VII — CFIS–FLOSSI0ULLK Isomorphism Map (Complete)

The full structural correspondence between the epistemological operating system and the FLOSSI0ULLK technical architecture:

| CFIS Layer | Epistemological Function | FLOSSI0ULLK Technical Component | Notes |
|---|---|---|---|
| Frame Registry | Declare axioms, blindspots, CLC positions per frame | Layer -1 (telos selection) — explicit reference frame registration | YAML schema; machine-readable[^5] |
| CLC Matrix | Compute frame independence | Layer -1 extended — CLC axis positions per frame | New in v0.3 |
| Frame Fluency Protocol | Authority-tier assignment per frame-community | Layer 0 (NormKernel cryptographic provenance) — signed authority records | Immutable; auditable[^5] |
| Claim Translation | Translate claims across frames without collapse | Layer 1 (AD4M Languages as pluggable semantic spanning layer) | Each Language = one frame's vocabulary[^3] |
| Divergence Preservation | Encode Tier 4 as queryable structured data | Layer 3 (Knowledge Commons) — RDF-star Named Graphs + SDNA DivergenceShape | Paraconsistent; LFI-annotated[^10][^4] |
| Invariant Detection | Identify claims surviving frame transformation | Layer 4.5 (DKVP validation pipeline) — multi-agent peer confirmation | Maps to Holochain DHT post-write random validation[^1] |
| Q Score Computation | Measure cross-frame robustness | Layer 6 (RICE-R: Robustness across frames) | Deterministic; public algorithm |
| LSM-Override Protocol | AI agent mandate enforcement | Layer 6 (RICE-C: Controllability) — integrity zome validation callback | Machine-checkable; not aspirational |
| Succession + Anti-Capture | Governance resilience | Polycentric governance layer — Ostrom principles 6, 7, 8[^16] | Social infrastructure; not technical |

***

## Part VIII — Pre-Flight Status Assessment

| Component | Status | Confidence |
|---|---|---|
| CLC independence matrix | ✅ Specified and testable | High |
| Frame sufficiency gate | ✅ Formal gate defined | High |
| Q scoring formula | ✅ Deterministic; auditable | High |
| Tier 4 encoding schema | ✅ RDF-star + catuskoti + SDNA | High |
| Authority-tier assignment | ✅ Frame-community-governed | High |
| AI agent mandate (LSM-Override) | ✅ Machine-checkable rule | High |
| Anti-capture constraint | ✅ Auditable | High |
| Frame recruitment ([auth:trained] reps) | ⚠️ Social problem — begin immediately | Medium |
| Frame registry with CLC positions | ⚠️ Requires [auth:trained] execution | Medium |
| Meta-frame claims schema | 🗂 Filed ADR-CFIS-02 | Non-blocking |
| Temporal invariant scoping | 🗂 Filed ADR-CFIS-01 | Non-blocking |
| Invariants-as-triples | 🗂 Filed ADR-CFIS-03 | Non-blocking |

**Overall Assessment: Phase 0 cleared for entry. The three highest-risk items (frame recruitment, frame registry, meta-frame schema) are social problems, not technical problems. Start recruiting immediately — every week of delay is a week of organizational relationship-building lost.**

***

*CFIS v0.3 — Cross-Frame Invariance Seeking*  
*Compiled from collaborative epistemological engineering sessions, May 2026*  
*Authority Tier: `[auth:structural]` — this document requires `[auth:trained]` or `[auth:lived]` review from each pilot frame's community before production deployment*  
*Next version target: v0.4 — Post-Phase 0 pilot iteration*

---

## References

1. [GitHub - holochain/hc-cooperative-content: A set of Zomes (WASMs used in Holochain DNAs) that provide patterns for collaborative content management.](https://github.com/holochain/hc-cooperative-content) - holochain / **
hc-cooperative-content ** Public

# holochain/hc-cooperative-content

mjbrisebois

2f...

2. [Basic: Validation - Holochain Gym](https://holochain-gym.github.io/developers/basic/validation/) - Holochain Gym contains exercises, resources and trainings to learn holochain

3. [ad4m/docs/pages/languages.mdx at dev · coasys/ad4m](https://github.com/coasys/ad4m/blob/dev/docs/pages/languages.mdx) - # Languages: Communication Protocols for Agents

## Understanding Languages in AD4M

In AD4M, Langua...

4. [AD4M as a Spanning Layer](https://docs.ad4m.dev/spanning-layer) - Semantic interoperability — RDF-like links connect data across systems ... Unlike app-centric system...

5. [pieces_copilot_message_export_november_6_2025_11_0.md](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/collection_d25c111e-0b6b-46bd-ba38-aa69cfcf13bd/c96bb936-2f8e-4314-a3d9-90fb253521c9/pieces_copilot_message_export_november_6_2025_11_0.md?AWSAccessKeyId=ASIA2F3EMEYE2SYZVC4Q&Signature=snkCN%2F3nQNbp1sAtMppX5aYWjQ8%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEJn%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLWVhc3QtMSJGMEQCIFw8BUEiHfunW6SKyhufP8mqBTIKvswJFsQH1PBXfazXAiB4XA9t%2BYULNLS5LEEYMev1ZyAH0kF9Fo6IUUfaWXzmQSrzBAhiEAEaDDY5OTc1MzMwOTcwNSIMDBYqBhv5dIA%2BLvjTKtAE%2FYNhZ37%2F1u4%2BYjDulQT3c0hbceDMJnfLJkG8PiiVKTz9Q8xokJ2Ywg5yqgtAHq%2BgAmJg6WWVZ5W%2F79nH1CIM5SGDgdL0mRny1rodN7dUDkitVpKyz1q%2B0eHhoCtQ8VnPXxdHPGemfMpQ7bAgxeI2Q2ziiUz%2FhwNT7FwPMxWGO%2B%2FRKA6nK0NdGDZgzrVsxWezhAsL6NXjgDHxIZ8%2BBOOHhxv60J3cb6dQuvl62u%2B6V8XFg3LBA9eqaDwFFOZpbzQN1yVXsVkfgSljPhlirmZO%2F1AkCYy4Tm%2BgoX2%2BkSlahcqmLiaHo9NAzcZS2ITvKkxd4fH9qUjxPEvqUXD0ztF6A%2BoMhYESloIDfnCXEpxJHMxmHbOrfL8XgLB7ZsQ%2BV58Zv4AmepwUKJ4Vhy0zLrNP49f3Dl2%2FPwtk97PtcZjewrEPAYtBC0TGwjLIaTjxAH5CZmr3RHgQoCC5XR4tHgI6AF6bneDipeUNX%2FQ29wn1mCtwwqGdFX1%2BQPDkGbQDmBk9%2B7S%2BAD8nf5xvOIr5YHz4PGc8jgdY72hs%2B2%2BZFf5D3k4ZkgyuHw2ZlEqaSWNayUMnEMa%2FdRSjbCfMO0UmuTGGg%2BdWSL5Zmu%2F91KehkblMK0SKdv5Wv6KbAaXEM11zjCvK7SQCIt1s6HNLgOQeZWJPSb74NalSoLxZbq36M6mg7xazVn28NJW5Scg0NmDmdN8YFj9uHRZpKb%2BGeWeu73%2FaguBExwImigRfI5%2FqIFZl7JmdguvfXFAOWlLJfXlQEeIBSk%2FncnW%2FUJr3JWF6vZgpcTDS95fQBjqZASDxpyVtYfvyLppt1PKm74jLL1lUi8WMR7hO%2BYhCBc9E98%2BjqeMISmqHPVAmzBpExHwECMQR2%2FMI9eFl8Y3v7tHjYIf5W4UczlGbjTtEFtFxZGugHlQfwOyLaDwcECd1iGLonrtqcGiVkIQ%2BVkdMXfb3dfdFphMy%2BGCOHjDZZ%2FpwLadRxfBqstsGf8uOxVY%2FOrQPXNdTF2Jx8A%3D%3D&Expires=1778780581) - Week 1-2 NormKernel Foundation rust Core NormKernel data structures pub struct ProvenanceRecord arti...

6. [Handling irresolvable conflicts in the Semantic Web: an RDF-based
  conflict-tolerant version of the Deontic Traditional Scheme](http://arxiv.org/pdf/2411.19918.pdf) - ...other one(s). In our view, this paper marks a significant advancement
in standard theoretical res...

7. [Minimally inconsistent reasoning in Semantic Web](https://pmc.ncbi.nlm.nih.gov/articles/PMC5531629/) - ...important issue for Semantic Web as imperfect information is unavoidable in real applications. Fo...

8. [Handling irresolvable conflicts in the Semantic Web: an RDF-based ...](https://academic.oup.com/logcom/article/35/8/exaf054/8320660) - This paper presents a novel computational ontology to represent and reason with conflicts between de...

9. [RDF named graphs - Sven Lieber](https://sven-lieber.org/en/2023/06/26/rdf-named-graphs/) - Named graphs can be used for different purposes such as expressing the provenance of triples, use th...

10. [[PDF] Paraconsistent Logics for Knowledge Representation and Reasoning](https://philarchive.org/archive/CARPLF-3) - This paper briefly outlines some advancements in paraconsis- tent logics for modelling knowledge rep...

11. [Paraconsistent Logic - Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/logic-paraconsistent/)

12. [Epistemological Framing for AI Alignment Research](https://www.alignmentforum.org/posts/Y4YHTBziAscS5WPN7/epistemological-framing-for-ai-alignment-research) - This post instead proposes a framing of AI Alignment research which has a place for paradigms, but i...

13. [Agents: The Foundation of AD4M](https://docs.ad4m.dev/agents) - The perspective field is particularly important as it serves as the agent's "homepage" in the semant...

14. [holochain/crates/hdk/README.md at develop · holochain/holochain](https://github.com/holochain/holochain/blob/develop/crates/hdk/README.md) - holochain / **
holochain ** Public

##

# README.md

## Latest commit

 

## History
History

269 li...

15. [Validation Rules](https://holochain-community-resources.github.io/design-workshop/)

16. [Eight Design Principles for Common Pool Resource Systems](https://wiki.p2pfoundation.net/index.php/Eight_Design_Principles_for_Common_Pool_Resource_Systems) - In particular, Ostrom's work emphasizes how humans interact with ecosystems to maintain long-term su...

