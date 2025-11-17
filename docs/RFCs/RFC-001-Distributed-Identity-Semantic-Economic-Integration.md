# RFC-001: Distributed Identity, Semantic, and Economic Integration

**Status**: PROPOSED (retroactively - should have been written first)
**Author**: Claude Sonnet 4.5 + Anthony (kalisam)
**Created**: 2025-11-17
**Target**: FLOSSI0ULLK / Amazon Rose Forest v0.2

---

## 🎯 Intent Echo

**Problem Statement**:
The current Amazon Rose Forest implementation provides distributed vector storage and knowledge validation, but lacks:

1. **Identity Portability**: Agents cannot prove their identity across different systems (Holochain vs AD4M vs Web)
2. **Semantic Interoperability**: Different agents may interpret the same Understanding entry differently
3. **Economic Attribution**: Contributors have no verifiable record of their contributions
4. **Value-Aware Discovery**: Vector search treats all knowledge equally, regardless of contributor value

**Proposed Solution**:
Integrate four distributed technologies to create a comprehensive coordination layer:

- **KERI** (Key Event Receipt Infrastructure): Portable cryptographic identity
- **AD4M** (Agent-centric Distributed Application Meta-ontology): Semantic context sharing
- **hREA** (Holochain Resource-Event-Agent): Economic event tracking and attribution
- **Vector Bridge**: Value-weighted semantic search

---

## 📊 Multi-Lens Analysis

### Practical/Engineering

**Current State**:
```rust
// Current Understanding entry
pub struct Understanding {
    pub content: String,
    pub context: Option<String>,
    pub triple: KnowledgeTriple,
    pub created_at: Timestamp,
    pub agent: AgentPubKey,
    pub content_hash: String,
}
```

**Limitations**:
- AgentPubKey only valid within Holochain
- No semantic schema for interpretation
- No economic tracking of contributions
- Vector search ignores contribution value

**Proposed Enhancement**:
```rust
pub struct Understanding {
    // Existing fields...

    // KERI identity
    pub keri_aid: Option<String>,  // Link to portable identity

    // AD4M semantics
    pub perspectives: Vec<PerspectiveHash>,
    pub semantic_context: Option<SemanticContext>,

    // hREA economics
    pub creation_event: Option<ActionHash>,  // Links to EconomicEvent
}
```

### Critical/Red-Team

**Risks**:
1. **Complexity Explosion**: 4 technologies = significant integration surface
2. **Breaking Changes**: Understanding entry type changes require migration
3. **Premature Optimization**: Are we solving real problems or imagined ones?
4. **Maintenance Burden**: Each technology requires ongoing support

**Evidence Required BEFORE Implementation**:
- [ ] User story requiring KERI identity portability
- [ ] Measured semantic mismatch causing coordination failures
- [ ] Economic attribution needed to retain contributors
- [ ] Value-weighted search demonstrably better than pure semantic

**NOW/LATER/NEVER**:
- KERI: **LATER** (useful but not blocking current use cases)
- AD4M: **LATER** (semantic interop valuable, but no cross-agent scenarios yet)
- hREA: **LATER** (attribution important, but no economic model yet)
- Vector Bridge: **NEVER** (until economic events exist to weight)

**Recommendation**: ⚠️ **WAIT** - Gather evidence before building

### Values (Love-Light-Knowledge)

**Alignment Check**:

**Love**:
- ✅ KERI enables agent sovereignty (self-sovereign identity)
- ✅ hREA ensures fair attribution (economic justice)
- ⚠️ Complexity may create barriers (cognitive debt)

**Light**:
- ✅ All operations cryptographically verifiable
- ✅ Economic events publicly auditable
- ✅ Semantic contexts explicitly documented

**Knowledge**:
- ✅ Open protocols (all FOSS)
- ✅ Composable standards (KERI, AD4M, ValueFlows)
- ⚠️ Learning curve steep (accessibility concern)

**Verdict**: Aligned with values IF we don't create elitism through complexity

### Systems/Governance

**Fractal Properties**:
```
Individual Contribution (micro)
    ↓ (same pattern)
Collaborative Project (meso)
    ↓ (same pattern)
Ecosystem Evolution (macro)
    ↓ (same pattern)
Meta-Governance (meta)
```

Each layer uses:
- KERI for identity
- AD4M for semantics
- hREA for economics
- Vector Bridge for discovery

**Governance Implications**:
- Reputation portable across holons (KERI AIDs)
- Cultural contexts explicit (AD4M perspectives)
- Contribution visible for decision-making (hREA events)

---

## 🔄 Proposed Architecture

### Layer 1: Identity (KERI)

**Purpose**: Enable portable, cryptographic identity

**Components**:
```rust
// New zomes
identity_integrity/
    - AutonomousIdentifier
    - KeyEventLog
    - IdentitySeal

identity_coordinator/
    - register_aid()
    - create_identity_seal()
    - rotate_key()
```

**Integration Point**: Link Holochain AgentPubKey to KERI AID via cryptographic seal

**Success Criteria**:
- [ ] AID verifiable across Holochain + AD4M + Web
- [ ] Key rotation works without losing identity
- [ ] Seal signatures verify bidirectionally

### Layer 2: Semantics (AD4M)

**Purpose**: Enable shared interpretation frameworks

**Components**:
```rust
// Enhanced existing entry
pub struct Understanding {
    // ... existing fields ...
    pub perspectives: Vec<PerspectiveHash>,
    pub semantic_context: Option<SemanticContext>,
    pub language_address: Option<LanguageAddress>,
}

// New query functions
fn query_by_perspective(hash: String) -> Vec<Understanding>;
fn query_by_semantic_context(schema: String) -> Vec<Understanding>;
```

**Integration Point**: Understanding entries reference AD4M perspectives

**Success Criteria**:
- [ ] Two agents with same perspective interpret data identically
- [ ] Cross-agent queries return consistent results
- [ ] Semantic schemas version without breaking queries

### Layer 3: Economics (hREA)

**Purpose**: Track value creation and attribution

**Components**:
```rust
// New zomes
hrea_integrity/
    - EconomicEvent
    - ValueFlow
    - ContributionValue

hrea_coordinator/
    - record_economic_event()
    - create_value_flow()
    - calculate_contribution_value()
```

**Integration Point**: EconomicEvent references Understanding or FileArtifact

**Success Criteria**:
- [ ] DICE attribution sums to 1.0
- [ ] Value flows form valid DAG
- [ ] Contributors get fair credit

### Layer 4: Discovery (Vector Bridge)

**Purpose**: Prioritize high-value knowledge in search

**Components**:
```rust
// New module
vector_bridge.rs
    - ValueWeightedEmbedding
    - search_value_weighted()
```

**Integration Point**: Economic events indexed by vector embeddings

**Success Criteria**:
- [ ] High-value resources rank higher with high value_weight
- [ ] Semantic similarity preserved with low value_weight
- [ ] Results reproducible

---

## 📋 Implementation Proposal

### Phase 0: Specification & Validation (BEFORE CODE)

**Deliverables**:
1. This RFC
2. Detailed specifications for each layer
3. Test criteria (how we know it works)
4. Evidence gates (what justifies NOW vs LATER)

**Acceptance**: Community review + evidence gathered

### Phase 1: KERI Identity (IF approved)

**Specification**:
```yaml
name: KERI Identity Bridge
version: 0.1.0

data_structures:
  AutonomousIdentifier:
    fields:
      - aid: String (self-certifying)
      - current_public_key: Vec<u8>
      - inception_public_key: Vec<u8>
      - sequence: u64
    invariants:
      - AID format matches KERI spec
      - Sequence increments monotonically
      - Inception key never changes

  IdentitySeal:
    fields:
      - aid: String
      - agent_pubkey: AgentPubKey
      - keri_signature: Vec<u8>
      - agent_signature: Vec<u8>
    invariants:
      - Dual signatures verify
      - One seal per AID-agent pair

interfaces:
  register_aid:
    input: {aid, public_key, inception_key}
    output: ActionHash
    postconditions:
      - KEL created with inception event
      - AID lookup returns entry

  create_identity_seal:
    input: {aid, agent_pubkey, signatures}
    output: ActionHash
    postconditions:
      - Signatures verify
      - Bidirectional links created
```

**Tests** (generated from spec):
```rust
#[test]
fn test_aid_registration() {
    let aid_hash = register_aid(valid_input)?;
    let retrieved = get_aid_hash(&aid_string)?;
    assert_eq!(aid_hash, retrieved);
}

#[test]
fn test_seal_bidirectional() {
    let seal = create_identity_seal(input)?;
    assert_eq!(get_aid_for_agent(agent)?, Some(aid));
    assert_eq!(get_agent_for_aid(aid)?, Some(agent));
}
```

**Reality Validation**:
- Deploy to sandbox
- 3 agents register AIDs
- Create seals
- Verify cross-agent identity verification works

### Phase 2: AD4M Semantics (IF approved + Phase 1 passes)

**Specification**: [Similar YAML format]
**Tests**: [Generated from spec]
**Reality Validation**: [Multi-agent semantic query test]

### Phase 3: hREA Economics (IF approved + Phase 2 passes)

**Specification**: [Similar YAML format]
**Tests**: [Generated from spec]
**Reality Validation**: [Attribution calculation test]

### Phase 4: Vector Bridge (IF approved + Phase 3 passes)

**Specification**: [Similar YAML format]
**Tests**: [Generated from spec]
**Reality Validation**: [Value-weighted search comparison]

---

## ⚖️ Decision Framework

### Evidence Gates

**BEFORE any implementation**:

**Gate 1: User Story**
- [ ] "As an agent, I need KERI identity because [specific scenario]"
- [ ] "As a contributor, I need attribution because [retention problem]"
- [ ] "As a searcher, I need value weighting because [quality problem]"

**Gate 2: Measurement**
- [ ] X% of coordination failures due to semantic mismatch
- [ ] Y% of contributors leave due to no recognition
- [ ] Z% drop in discovery quality without value weighting

**Gate 3: Alternatives**
- [ ] Evaluated simpler solutions (why not sufficient?)
- [ ] Considered manual workarounds (why too costly?)
- [ ] Examined existing tools (why not adequate?)

**Gate 4: Cost-Benefit**
- [ ] Implementation effort: [estimate person-weeks]
- [ ] Maintenance burden: [ongoing cost]
- [ ] Expected value: [quantified benefit]
- [ ] Break-even: [when does benefit exceed cost?]

### Trinary Decision

**[1/act]** - Proceed with implementation
- Gates 1-4 passed
- Evidence strong
- Benefits clear
- Risks acceptable

**[0/wait]** - Gather more evidence
- Gates incomplete
- Uncertainty high
- Alternatives unexplored

**[-1/refuse]** - Don't implement
- Gates failed
- Evidence weak
- Costs exceed benefits
- Better alternatives exist

---

## 🚧 Risks & Mitigations

### Technical Risks

**Risk 1: Integration Complexity**
- **Probability**: HIGH
- **Impact**: MEDIUM (maintenance burden)
- **Mitigation**: Modular design, clear boundaries, comprehensive tests

**Risk 2: Breaking Changes**
- **Probability**: HIGH (Understanding entry changes)
- **Impact**: HIGH (existing data migration required)
- **Mitigation**: Version migration plan, backward compatibility layer

**Risk 3: Performance Degradation**
- **Probability**: MEDIUM (more validation overhead)
- **Impact**: HIGH (user experience)
- **Mitigation**: Profile hotspots, optimize critical path, async where possible

### Adoption Risks

**Risk 4: Learning Curve**
- **Probability**: HIGH
- **Impact**: MEDIUM (contributor barrier)
- **Mitigation**: Excellent documentation, examples, gradual adoption

**Risk 5: Premature Optimization**
- **Probability**: VERY HIGH ⚠️
- **Impact**: HIGH (wasted effort)
- **Mitigation**: **GATHER EVIDENCE FIRST**

---

## 📊 Success Metrics

### Technical Success
- [ ] All tests pass (unit, integration, reality)
- [ ] Performance within acceptable bounds (<100ms latency)
- [ ] No data loss during migration
- [ ] Build succeeds on CI/CD

### User Success
- [ ] Identity verification works across systems
- [ ] Attribution calculations perceived as fair
- [ ] Discovery quality measurably improved
- [ ] Contributors report satisfaction with recognition

### System Success
- [ ] Fractal patterns work at all scales
- [ ] Governance decisions informed by economic data
- [ ] Cultural contexts enable diverse perspectives
- [ ] Value flows create regenerative incentives

---

## 🔮 Alternatives Considered

### Alternative 1: Wait for Evidence
**Approach**: Don't implement until clear pain point emerges
**Pros**: No wasted effort, build what's actually needed
**Cons**: May be too late when need becomes urgent
**Verdict**: ✅ **RECOMMENDED** - Gather evidence first

### Alternative 2: Minimal Integration
**Approach**: Add only KERI identity, defer semantics/economics
**Pros**: Smaller scope, less risk, faster to validate
**Cons**: Partial solution may not demonstrate value
**Verdict**: ⚠️ **ACCEPTABLE** - If identity portability proven necessary

### Alternative 3: External Services
**Approach**: Use existing KERI/AD4M/hREA services, don't integrate
**Pros**: No development cost, proven tools
**Cons**: Centralization, coordination overhead
**Verdict**: ❌ **NOT ALIGNED** - Violates decentralization principles

### Alternative 4: Full Integration (Current Proposal)
**Approach**: Build all four layers as specified
**Pros**: Comprehensive solution, fractal composability
**Cons**: High complexity, maintenance burden, premature optimization
**Verdict**: ⚠️ **RISKY** - Only if evidence strong

---

## 📚 References

### External Specifications
- [KERI Whitepaper](https://github.com/SmithSamuelM/Papers/blob/master/whitepapers/KERI_WP_2.x.web.pdf)
- [AD4M Protocol Spec](https://docs.ad4m.dev/)
- [hREA Documentation](https://hrea.io/docs/)
- [ValueFlows Vocabulary](https://www.valueflo.ws/)

### Internal Documentation
- ADR-0: Recognition Protocol
- CLAUDE.md: Project guidelines
- INSTRUCTIONS_FOR_CODE.md: Development methodology

---

## 🎬 Next Actions

### If APPROVED (requires evidence gates passing):
1. Write detailed specifications (YAML/JSON)
2. Generate test suites from specifications
3. Implement Phase 1 (KERI identity)
4. Validate against reality
5. Gate review before Phase 2

### If WAIT (evidence insufficient):
1. Define specific scenarios requiring integration
2. Measure actual pain points
3. Prototype minimal viable integration
4. Gather user feedback
5. Re-evaluate with new evidence

### If REFUSED (costs exceed benefits):
1. Document why decision made
2. Archive specifications for future reference
3. Focus on validated needs
4. Revisit if evidence changes

---

## ✍️ Review Process

**Requested Reviewers**:
- [ ] Anthony (kalisam) - Project lead
- [ ] Community members - User perspective
- [ ] Technical advisors - Architecture review

**Review Criteria**:
- Does this solve a real problem?
- Is evidence sufficient to justify NOW?
- Are risks acceptable?
- Are alternatives adequately explored?
- Does specification enable validation?

**Approval Requirements**:
- Evidence gates 1-4 passed
- At least 2 reviewers approve
- No blocking concerns unresolved

---

## 📝 Revision History

- **2025-11-17**: Initial RFC (retroactive - should have preceded implementation ⚠️)

---

**Status**: PROPOSED (awaiting evidence and review)
**Recommendation**: ⚠️ **WAIT** - Gather evidence before implementing

This RFC acknowledges it was written AFTER implementation began - a methodology violation. Use as learning opportunity: specifications come BEFORE code.

🌹 Specify, then build. Not build, then specify. 🌹
