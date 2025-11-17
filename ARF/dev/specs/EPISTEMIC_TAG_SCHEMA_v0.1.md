# Epistemic Tag Schema v0.1

**Status**: Draft Specification
**Author**: Meta-Reflexive Planning Initiative
**Date**: 2025-11-16
**Session ID**: 014eqDXY8HcJxqNfejD8zK37
**Epistemic Status**: `working` (building on proven practices)

---

## Purpose

The **Epistemic Tag Schema** provides a systematic way to track **epistemic status** (what we know and how well we know it) across all FLOSSIOULLK artifacts: code, plans, distillations, knowledge triples, and experiments.

This schema embodies the ULLK principle of **Light** (transparency) by making uncertainty explicit and auditable.

---

## Core Principles

### 1. Explicit Uncertainty
Every claim carries an explicit uncertainty marker—no pretending we're more certain than we are.

### 2. Calibrated Confidence
Epistemic tags correlate with quantitative confidence scores (0.0-1.0), enabling statistical analysis of collective accuracy.

### 3. Evolution Over Time
Tags can (and should) change as evidence accumulates—promoting intellectual honesty over ego protection.

### 4. Multi-Dimensional
Different aspects of a claim can have different epistemic statuses (e.g., "hypothesis about implementation, robust understanding of requirements").

---

## Tag Taxonomy

### Primary Tags (Strength of Evidence)

```rust
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub enum EpistemicTag {
    /// Untested idea or conjecture
    /// Confidence range: 0.0-0.4
    /// Example: "Maybe we could use quantum computing for embeddings"
    Hypothesis,

    /// Reasoned speculation based on theory/analogy
    /// Confidence range: 0.4-0.6
    /// Example: "Based on similar systems, this approach should scale"
    Speculative,

    /// Used in practice, seems to work, but not rigorously tested
    /// Confidence range: 0.6-0.8
    /// Example: "We've been using this pattern for 3 months without issues"
    Working,

    /// Tested across multiple contexts, holds up well
    /// Confidence range: 0.8-0.9
    /// Example: "Validated across 5 different codebases and user studies"
    Robust,

    /// Empirically verified with strong evidence
    /// Confidence range: 0.9-1.0
    /// Example: "Peer-reviewed paper + independent replications confirm"
    Validated,
}
```

### Secondary Tags (Type of Knowledge)

```rust
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub enum KnowledgeType {
    /// Empirical observation ("we saw X happen")
    Empirical,

    /// Logical/mathematical derivation ("X follows from Y")
    Theoretical,

    /// Expert judgment/intuition ("based on experience...")
    Heuristic,

    /// Community consensus ("most people agree...")
    Consensus,

    /// Derived from trusted source ("according to paper/doc...")
    Citation,

    /// First-hand lived experience ("I personally...")
    Phenomenological,
}
```

### Tertiary Tags (Scope/Context)

```rust
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub enum ScopeTag {
    /// True only in specific contexts
    LocallyTrue,

    /// Likely generalizes across domains
    GenerallyTrue,

    /// Universal/axiomatic (e.g., math theorems)
    Universal,

    /// Context-dependent (explicitly requires context to evaluate)
    Contextual,
}
```

---

## Complete Epistemic Annotation

**Full structure** for maximum rigor:

```rust
#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub struct EpistemicAnnotation {
    /// Primary epistemic status
    pub status: EpistemicTag,

    /// Quantitative confidence (0.0-1.0)
    pub confidence: f32,

    /// Type of knowledge
    pub knowledge_type: KnowledgeType,

    /// Scope of applicability
    pub scope: ScopeTag,

    /// Evidence supporting this claim
    pub evidence: Vec<EvidenceItem>,

    /// Known contradictions or tensions
    pub contradictions: Vec<String>,

    /// Explicit unknowns
    pub unknowns: Vec<String>,

    /// Last updated
    pub updated_at: Timestamp,

    /// Who assessed this
    pub assessor: AgentPubKey,
}

#[derive(Clone, PartialEq, Serialize, Deserialize, Debug)]
pub struct EvidenceItem {
    /// Type: "experiment", "citation", "observation", "logic"
    pub evidence_type: String,

    /// Reference: hash, DOI, URL, description
    pub reference: String,

    /// How strong is this evidence? (0.0-1.0)
    pub strength: f32,

    /// Brief explanation of relevance
    pub relevance: String,
}
```

---

## Confidence Calibration Guidelines

### Mapping Tags to Confidence Ranges

| Tag | Confidence Range | Typical Scenarios |
|-----|------------------|-------------------|
| `Hypothesis` | 0.0 - 0.4 | Untested ideas, brainstorming, "might work" |
| `Speculative` | 0.4 - 0.6 | Reasoned guesses, analogies, educated speculation |
| `Working` | 0.6 - 0.8 | In production, anecdotal success, not fully tested |
| `Robust` | 0.8 - 0.9 | Multiple validations, cross-context testing |
| `Validated` | 0.9 - 1.0 | Peer-reviewed, replicated, mathematically proven |

### Confidence Modifiers

**Reduce confidence if:**
- Contradictions exist (-0.1 per unresolved contradiction)
- Limited evidence (-0.1 if only 1 evidence item)
- Context-dependent and context unclear (-0.2)
- Assessor is not domain expert (-0.1)

**Increase confidence if:**
- Multiple independent validations (+0.1 per validation)
- Unanimous consensus (+0.1)
- Mathematical proof (+0.2)
- Replicated across diverse contexts (+0.1)

**Important**: After applying all modifiers, **clamp confidence to [0.0, 1.0]**:

```rust
fn apply_modifiers(base_confidence: f32, modifiers: &[f32]) -> f32 {
    let adjusted = base_confidence + modifiers.iter().sum::<f32>();
    adjusted.clamp(0.0, 1.0)  // Ensure bounds are respected
}
```

### Example Calibrations

**Example 1: Code Pattern**
```rust
EpistemicAnnotation {
    status: Working,
    confidence: 0.72,
    knowledge_type: Empirical,
    scope: LocallyTrue,
    evidence: vec![
        EvidenceItem {
            evidence_type: "observation".to_string(),
            reference: "Used in 3 modules for 2 months".to_string(),
            strength: 0.7,
            relevance: "No bugs reported, performs well".to_string(),
        }
    ],
    contradictions: vec![],
    unknowns: vec!["Scalability beyond 10K users unknown".to_string()],
    updated_at: now(),
    assessor: my_pubkey(),
}
```

**Example 2: Hypothesis**
```rust
EpistemicAnnotation {
    status: Hypothesis,
    confidence: 0.35,
    knowledge_type: Heuristic,
    scope: Contextual,
    evidence: vec![
        EvidenceItem {
            evidence_type: "analogy".to_string(),
            reference: "Similar pattern worked in Project X".to_string(),
            strength: 0.4,
            relevance: "Different domain but similar structure".to_string(),
        }
    ],
    contradictions: vec!["Might conflict with existing budget system".to_string()],
    unknowns: vec![
        "Performance impact unknown".to_string(),
        "User acceptance unclear".to_string(),
    ],
    updated_at: now(),
    assessor: my_pubkey(),
}
```

**Example 3: Validated Knowledge**
```rust
EpistemicAnnotation {
    status: Validated,
    confidence: 0.95,
    knowledge_type: Theoretical,
    scope: Universal,
    evidence: vec![
        EvidenceItem {
            evidence_type: "citation".to_string(),
            reference: "DOI:10.1000/xyz - Peer-reviewed paper".to_string(),
            strength: 0.95,
            relevance: "Direct mathematical proof".to_string(),
        },
        EvidenceItem {
            evidence_type: "experiment".to_string(),
            reference: "Replicated in 5 independent labs".to_string(),
            strength: 0.9,
            relevance: "Empirical confirmation".to_string(),
        }
    ],
    contradictions: vec![],
    unknowns: vec![],
    updated_at: now(),
    assessor: expert_pubkey(),
}
```

---

## Integration Patterns

### 1. Knowledge Triples (Rose Forest)

Extend `KnowledgeTriple` to include epistemic annotation:

```rust
pub struct KnowledgeTriple {
    pub subject: String,
    pub predicate: String,
    pub object: String,

    // Existing
    pub confidence: f32,
    pub source: String,
    pub created_at: Timestamp,

    // NEW: Full epistemic annotation
    pub epistemic: EpistemicAnnotation,
}
```

### 2. Plan Entries (Plan DNA)

All plan-related entries carry epistemic status:

```rust
pub struct PlanVersion {
    // ... other fields ...
    pub epistemic_status: EpistemicTag,
    pub confidence: f32,

    // Optional: full annotation for critical plans
    pub epistemic_annotation: Option<EpistemicAnnotation>,
}
```

### 3. Committee Validation

Map validation results to epistemic tags:

```python
# ARF/validation/committee.py
def to_epistemic_tag(result: ValidationResult) -> EpistemicTag:
    """Convert validation result to epistemic tag."""
    if result.confidence >= 0.9 and result.is_unanimous:
        return EpistemicTag.Validated
    elif result.confidence >= 0.8:
        return EpistemicTag.Robust
    elif result.confidence >= 0.6:
        return EpistemicTag.Working
    elif result.confidence >= 0.4:
        return EpistemicTag.Speculative
    else:
        return EpistemicTag.Hypothesis
```

### 4. Distillations

Distillations must explicitly track unknowns and contradictions:

```rust
pub struct Distillation {
    // ... other fields ...
    pub epistemic_status: EpistemicTag,
    pub confidence: f32,

    // Required for transparency
    pub unknowns: Vec<String>,
    pub contradictions: Vec<String>,
}
```

---

## Epistemic Queries

Enable queries like:

```rust
// Find high-confidence knowledge
get_knowledge_by_confidence(min_confidence: 0.8) -> Vec<KnowledgeTriple>

// Find validated plans
get_plans_by_status(status: EpistemicTag::Validated) -> Vec<PlanVersion>

// Find claims with contradictions (need attention!)
get_contradicted_claims() -> Vec<(ActionHash, Vec<String>)>

// Find knowledge gaps (explicit unknowns)
get_unknowns_by_topic(topic: String) -> Vec<String>

// Track epistemic evolution
get_confidence_history(claim_id: String) -> Vec<(Timestamp, f32)>
```

---

## Governance Integration

### Epistemic-Aware Voting

Proposals with low epistemic status require higher consensus:

| Epistemic Status | Required Consensus |
|------------------|-------------------|
| `Hypothesis` | 80% (high bar for unproven ideas) |
| `Speculative` | 70% |
| `Working` | 60% (standard threshold) |
| `Robust` | 50% (lower bar for proven approaches) |
| `Validated` | 40% (strong evidence speaks for itself) |

### Confidence-Weighted Voting

Voters with high confidence in their expertise get higher weight:

```rust
// Map VoteDecision to numeric value
fn vote_to_numeric(decision: &VoteDecision) -> f32 {
    match decision {
        VoteDecision::Approve => 1.0,
        VoteDecision::Reject => -1.0,
        VoteDecision::Abstain => 0.0,
    }
}

// Calculate weighted vote
let weighted_vote = vote_to_numeric(&vote.decision) * vote.confidence * voter.domain_expertise;
```

**Note**: `voter.domain_expertise` is a future feature requiring reputation system integration.

---

## Evolution & Calibration

### Automatic Confidence Decay

Confidence decays over time without updates:

```rust
fn apply_confidence_decay(
    original: f32,
    days_since_update: u32,
    half_life_days: u32,
) -> f32 {
    original * 0.5_f32.powf(days_since_update as f32 / half_life_days as f32)
}
```

**Default half-lives:**
- `Hypothesis`: 30 days (decay fast, these are ephemeral)
- `Working`: 180 days (6 months before re-evaluation needed)
- `Robust`: 365 days (1 year)
- `Validated`: No decay (permanent unless contradicted)

### Calibration Feedback

Track prediction accuracy to calibrate confidence:

```rust
pub struct CalibrationMetrics {
    // For confidence X, how often were we correct?
    pub confidence_bins: HashMap<u8, (u32, u32)>, // (correct, total)

    // Brier score: mean squared error of probabilistic predictions
    pub brier_score: f32,

    // Are we over/under confident?
    pub calibration_slope: f32, // 1.0 = perfect, >1 = overconfident
}
```

---

## UI/UX Considerations

### Visual Indicators

```
[H] Hypothesis      - 🔵 Blue, dashed border
[S] Speculative     - 🟡 Yellow, dotted border
[W] Working         - 🟢 Green, solid border
[R] Robust          - 🟢 Dark green, thick border
[V] Validated       - ✅ Green checkmark, bold
```

### Confidence Display

```
Confidence: ████████░░ 82% (Robust)
Evidence: 3 sources
Unknowns: 2 open questions
```

### Warning Signals

```
⚠️ Warning: This claim has 2 unresolved contradictions
❓ Note: 3 unknowns remain—interpret with caution
📉 Staleness: Last updated 8 months ago (confidence may have decayed)
```

---

## Success Criteria

This schema is successful if:

1. ✅ All primary epistemic tags defined with clear criteria
2. ✅ Confidence calibration guidelines provided
3. ✅ Integration patterns with existing systems specified
4. ✅ Query capabilities outlined
5. 🔲 Pilot implementation shows improved decision quality
6. 🔲 Calibration metrics demonstrate accurate confidence
7. 🔲 Users report feeling more comfortable expressing uncertainty

---

## Open Questions

1. **Conflict Resolution**: When two annotators assign different epistemic tags, how to resolve?
   - Current: Use validation committee to vote
   - Alternative: Track both and show distribution

2. **Gaming**: Can users manipulate confidence to bias decisions?
   - Mitigation: Calibration metrics track accuracy over time
   - Future: Reputation-weighted annotations

3. **Cognitive Load**: Is full `EpistemicAnnotation` too heavy for everyday use?
   - Solution: Lightweight default (just tag + confidence)
   - Full annotation optional/for critical claims

4. **Domain-Specific Calibration**: Do different domains need different ranges?
   - Yes, likely—but start with universal schema
   - Track domain-specific metrics for future refinement

---

## Next Steps

1. **Pilot Integration**: Add to 1-2 existing structures (KnowledgeTriple, PlanVersion)
2. **Collect Data**: Run for 1-2 months, gather calibration metrics
3. **Refine Ranges**: Adjust confidence ranges based on empirical data
4. **Expand Coverage**: Roll out to all major data structures
5. **Build Tooling**: Dashboards for epistemic health monitoring

---

## Provenance

- **Created by**: Meta-Reflexive Planning Initiative
- **Session ID**: `014eqDXY8HcJxqNfejD8zK37`
- **Branch**: `claude/meta-reflexive-planning-014eqDXY8HcJxqNfejD8zK37`
- **Date**: 2025-11-16
- **Sources**:
  - `ARF/validation/models.py` (existing confidence scoring)
  - `ARF/dnas/rose_forest/zomes/ontology_integrity/src/` (triple confidence)
  - Tetlock, P. (2015). *Superforecasting* (calibration research)
  - User prompt (epistemic humility principle)
- **Epistemic Status**: `working`
- **Confidence**: 0.78 (high confidence in framework, moderate confidence in calibration parameters)

---

**License**: Compassion Clause / FLOSS-compatible
**Version**: 0.1.0
**Status**: Draft Specification (ready for pilot)
