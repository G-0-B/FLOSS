# Plan DNA Specification v0.1

**Status**: Draft Specification (SDD Phase 1)
**Author**: Meta-Reflexive Planning Initiative
**Date**: 2025-11-16
**Session ID**: 014eqDXY8HcJxqNfejD8zK37
**Epistemic Status**: `hypothesis` → `design` (moving toward implementation)

---

## Purpose

The **Plan DNA** implements the meta-reflexive layer of FLOSSIOULLK, enabling the system itself to evolve through:
- Versioned, auditable plans
- Critique and distillation mechanisms
- Consensus-based governance
- Provenance-rich knowledge evolution

This DNA is the Holochain implementation of the **Darwin Module's** "versioned context playbook" concept described in `ARF/docs/architecture.md`.

---

## Core Principles

### 1. Plan-as-Living-Entity
Plans are NOT static documents. They are:
- **Versioned** - track evolution over time
- **Critiqued** - subject to systematic review
- **Distilled** - synthesized into actionable knowledge
- **Executed** - tracked through implementation

### 2. Meta-Reflexivity
The Plan DNA treats itself as subject to planning:
- Plans can be about improving the planning process
- Distillations inform future plan structure
- Failure modes become explicit plan considerations

### 3. Epistemic Humility
Every entry carries explicit uncertainty:
- Confidence scores (0.0-1.0)
- Epistemic tags (`hypothesis`, `working`, `robust`, `validated`)
- Unknown/contradiction tracking

### 4. ULLK Alignment
- **Unconditional Love**: Compassionate critique, not combative
- **Light**: Full transparency and auditability
- **Knowledge**: Truth-seeking through collective intelligence

---

## Entry Types

### 1. PlanVersion

**Purpose**: Represents a snapshot of a plan at a point in time.

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct PlanVersion {
    // Identity
    pub plan_id: String,              // Persistent ID across versions (UUID)
    pub version: String,              // Semantic version (e.g., "0.1.0")
    pub title: String,                // Human-readable title

    // Content
    pub content: String,              // Markdown specification
    pub objective: String,            // What this plan aims to achieve
    pub success_criteria: Vec<String>, // How we know it worked

    // Provenance
    pub author: AgentPubKey,          // Who created this version
    pub created_at: Timestamp,        // When it was created
    pub context: String,              // Which holon/neighborhood/phase

    // Epistemic
    pub epistemic_status: EpistemicTag,
    pub confidence: f32,              // 0.0-1.0

    // Relationships
    pub supersedes: Option<ActionHash>, // Previous version (if any)
    pub derived_from: Vec<ActionHash>,  // Source plans/distillations
}
```

**Validation Rules**:
- `confidence` must be in [0.0, 1.0]
- `version` must follow semantic versioning
- If `supersedes` is Some, must point to valid prior PlanVersion
- `author` must be the entry creator (cryptographic integrity)

---

### 2. Critique

**Purpose**: Systematic assessment of a Plan, Proposal, or Distillation.

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Critique {
    // Target
    pub target: ActionHash,           // Plan/Proposal/Distillation being critiqued
    pub target_type: CritiqueTargetType, // enum: Plan, Proposal, Distillation

    // Content
    pub content: String,              // Markdown critique
    pub dimensions: Vec<CritiqueDimension>, // Multi-dimensional assessment

    // Provenance
    pub author: AgentPubKey,
    pub created_at: Timestamp,

    // Epistemic
    pub severity: CritiqueSeverity,   // enum: Minor, Major, Blocking
    pub confidence: f32,              // Confidence in this critique
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct CritiqueDimension {
    pub aspect: String,               // e.g., "correctness", "completeness", "ULLK-alignment"
    pub score: f32,                   // 0.0-1.0
    pub reasoning: String,            // Why this score
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub enum CritiqueSeverity {
    Minor,      // Suggestions for improvement
    Major,      // Significant concerns
    Blocking,   // Must be addressed before approval
}
```

**Validation Rules**:
- `target` must point to valid entry
- All `score` values in [0.0, 1.0]
- At least one dimension required
- Blocking critiques require detailed reasoning (min 100 chars)

---

### 3. Distillation

**Purpose**: Synthesized knowledge extracted from experiences, critiques, and experiments.

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Distillation {
    // Identity
    pub topic: String,                // What this distillation is about
    pub title: String,                // Short title

    // Content
    pub synthesis: String,            // 1-2 paragraphs: what we now understand
    pub rationale: String,            // Why we believe this
    pub unknowns: Vec<String>,        // What we still don't know
    pub contradictions: Vec<String>,  // Unresolved tensions

    // Evidence
    pub evidence: Vec<EvidenceLink>,  // Links to experiments, code, discussions

    // Provenance
    pub author: AgentPubKey,
    pub created_at: Timestamp,
    pub context: String,

    // Epistemic
    pub epistemic_status: EpistemicTag,
    pub confidence: f32,

    // Relationships
    pub supersedes: Option<ActionHash>, // Previous distillation on this topic
    pub sources: Vec<ActionHash>,       // Plans, critiques, experiments used
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct EvidenceLink {
    pub source: ActionHash,           // Link to evidence entry
    pub source_type: String,          // "experiment", "code", "discussion"
    pub relevance: String,            // Why this evidence matters
}
```

**Validation Rules**:
- `synthesis` max 1000 chars (force conciseness)
- Must have at least one evidence link OR explicit unknowns
- Confidence must decrease if contradictions exist

---

### 4. Proposal

**Purpose**: Suggested modification to a plan or the planning process itself.

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Proposal {
    // Identity
    pub title: String,

    // Content
    pub description: String,          // What is being proposed
    pub rationale: String,            // Why this change
    pub plan_delta: PlanDelta,        // Structured change description

    // Target
    pub targets: Vec<ActionHash>,     // Plans or processes being modified

    // Provenance
    pub author: AgentPubKey,
    pub created_at: Timestamp,

    // Governance
    pub status: ProposalStatus,
    pub vote_threshold: f32,          // Required consensus (e.g., 0.6 = 60%)
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct PlanDelta {
    pub delta_type: DeltaType,        // Add, Modify, Remove, Meta
    pub changes: Vec<ChangeSpec>,     // Structured change specification
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub enum DeltaType {
    Add,          // Add new plan/feature
    Modify,       // Modify existing plan
    Remove,       // Deprecate plan
    Meta,         // Change planning process itself
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub enum ProposalStatus {
    Draft,        // Being refined
    Open,         // Open for voting
    Accepted,     // Passed vote threshold
    Rejected,     // Failed vote
    Withdrawn,    // Author withdrew
}
```

**Validation Rules**:
- `vote_threshold` in [0.5, 1.0] (require at least majority)
- Only author can transition Draft→Open or any→Withdrawn
- Status transitions must follow state machine

---

### 5. Vote

**Purpose**: Cast vote on a Proposal (reuses existing validation/committee.py model).

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Vote {
    // Target
    pub proposal: ActionHash,

    // Vote
    pub decision: VoteDecision,       // Approve, Reject, Abstain
    pub confidence: f32,              // 0.0-1.0
    pub reasoning: Option<String>,    // Why this vote

    // Provenance
    pub voter: AgentPubKey,
    pub created_at: Timestamp,
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub enum VoteDecision {
    Approve,
    Reject,
    Abstain,
}
```

**Validation Rules**:
- One vote per agent per proposal
- Cannot vote on your own proposal
- Confidence required for Approve/Reject (can be 0 for Abstain)

---

### 6. Experiment

**Purpose**: Track execution of a plan or test of a hypothesis.

```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct Experiment {
    // Identity
    pub title: String,
    pub plan: ActionHash,             // Plan being executed

    // Execution
    pub hypothesis: String,           // What we expected
    pub methodology: String,          // How we tested
    pub results: String,              // What actually happened
    pub artifacts: Vec<ArtifactLink>, // Code, data, logs

    // Outcome
    pub success: bool,                // Did it work?
    pub learnings: Vec<String>,       // What we learned
    pub failures: Vec<String>,        // What broke/surprised us

    // Provenance
    pub executor: AgentPubKey,
    pub started_at: Timestamp,
    pub completed_at: Option<Timestamp>,
}

#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub struct ArtifactLink {
    pub artifact_type: String,        // "code", "data", "log", "benchmark"
    pub location: String,             // IPFS CID, git commit, file path
    pub description: String,
}
```

**Validation Rules**:
- If `completed_at` is Some, must have results
- If `success == false`, must have at least one failure entry
- All artifacts must have valid locations (CID format for IPFS)

---

## Shared Types

### EpistemicTag

```rust
#[derive(Clone, PartialEq, Serialize, Deserialize)]
pub enum EpistemicTag {
    Hypothesis,      // Untested idea
    Speculative,     // Reasoned conjecture
    Working,         // Used in practice, seems to work
    Robust,          // Tested across multiple contexts
    Validated,       // Empirically verified with evidence
}
```

**Confidence Calibration**:
- `Hypothesis`: confidence typically < 0.4
- `Speculative`: confidence 0.4-0.6
- `Working`: confidence 0.6-0.8
- `Robust`: confidence 0.8-0.9
- `Validated`: confidence > 0.9

---

## Coordinator Functions

### Plan Management

```rust
pub fn create_plan(plan: PlanVersion) -> ExternResult<ActionHash>
pub fn get_plan(plan_hash: ActionHash) -> ExternResult<Option<PlanVersion>>
pub fn get_plan_history(plan_id: String) -> ExternResult<Vec<PlanVersion>>
pub fn get_latest_plan_version(plan_id: String) -> ExternResult<Option<PlanVersion>>
```

### Critique & Feedback

```rust
pub fn add_critique(critique: Critique) -> ExternResult<ActionHash>
pub fn get_critiques_for(target: ActionHash) -> ExternResult<Vec<Critique>>
pub fn get_blocking_critiques(target: ActionHash) -> ExternResult<Vec<Critique>>
```

### Distillation

```rust
pub fn create_distillation(distillation: Distillation) -> ExternResult<ActionHash>
pub fn get_distillations_by_topic(topic: String) -> ExternResult<Vec<Distillation>>
pub fn get_latest_distillation(topic: String) -> ExternResult<Option<Distillation>>
```

### Proposals & Voting

```rust
pub fn create_proposal(proposal: Proposal) -> ExternResult<ActionHash>
pub fn vote_on_proposal(vote: Vote) -> ExternResult<ActionHash>
pub fn get_proposal_votes(proposal: ActionHash) -> ExternResult<Vec<Vote>>
pub fn compute_proposal_outcome(proposal: ActionHash) -> ExternResult<ProposalOutcome>
pub fn finalize_proposal(proposal: ActionHash) -> ExternResult<ProposalStatus>
```

### Experiments

```rust
pub fn start_experiment(experiment: Experiment) -> ExternResult<ActionHash>
pub fn complete_experiment(experiment_hash: ActionHash, results: ExperimentResults) -> ExternResult<()>
pub fn get_experiments_for_plan(plan: ActionHash) -> ExternResult<Vec<Experiment>>
```

---

## Governance Rules

### Budget Integration

All operations consume Resource Units (RU) from the existing budget system:

| Operation | RU Cost | Rationale |
|-----------|---------|-----------|
| `create_plan` | 50 | Major cognitive work |
| `add_critique` | 10 | Thoughtful review |
| `create_distillation` | 33 | Synthesis is expensive |
| `create_proposal` | 25 | Serious governance action |
| `vote_on_proposal` | 5 | Democratic participation |
| `start_experiment` | 15 | Real-world execution |

### Consensus Thresholds

Adapted from existing `validation/committee.py`:
- **Standard Proposal**: ≥60% approval (0.6 threshold)
- **Meta Proposal** (changes to planning process): ≥80% approval (0.8 threshold)
- **Minimum Voters**: ≥5 votes required for proposals to pass

### Auto-Finalization

Proposals auto-finalize if:
- Vote threshold met + minimum voters reached
- 7 days elapsed since last vote
- No blocking critiques unresolved

---

## Integration with Existing Systems

### 1. Committee Validation
Reuse `ARF/validation/` for voting logic:
```python
# Python side can coordinate voting
from validation import TripleValidationCommittee

# Validate proposals use same consensus model
committee = TripleValidationCommittee(use_mock=False)
result = await committee.validate(
    proposal_triple=("ProposalXYZ", "should_be_accepted", "true"),
    context=proposal_content
)
```

### 2. Budget System
All plan operations integrated with `ARF/dnas/rose_forest/zomes/coordinator/src/budget.rs`:
```rust
// Check budget before plan operation
check_budget(agent, operation_cost)?;
// Deduct on success
deduct_budget(agent, operation_cost)?;
```

### 3. Memory & Ontology
Plans can reference knowledge from Rose Forest:
```rust
// Link plan to relevant knowledge nodes
create_link(plan_hash, knowledge_hash, LinkTag::new("references"))?;
```

### 4. IPFS Artifacts
Experiments link to IPFS for large artifacts:
```rust
// Store artifact metadata in Holochain
// Actual file on IPFS via existing upload tools
artifact: ArtifactLink {
    artifact_type: "model".to_string(),
    location: "QmXYZ...".to_string(), // IPFS CID
    description: "Fine-tuned embedding model".to_string(),
}
```

---

## Success Criteria

This specification is **ready for implementation** when:

1. ✅ All entry types defined with clear validation rules
2. ✅ Coordinator functions specified
3. ✅ Integration points with existing systems identified
4. ✅ Governance rules established
5. ✅ Budget costs calibrated
6. 🔲 Peer review completed (minimum 2 reviewers)
7. 🔲 Test plan written (SDD Phase 3)
8. 🔲 Security audit for governance attacks

---

## Open Questions / Unknowns

1. **Spam Prevention**: Should there be a reputation system to prevent low-quality critiques?
   - Current mitigation: RU costs + community norms
   - Future: Consider trust vectors from `infinity_bridge`

2. **Conflict Resolution**: How to handle deadlocked votes?
   - Current: Require supermajority for meta-proposals
   - Future: Escalation to higher-level governance body?

3. **Distillation Automation**: Can we use LLMs to auto-generate distillations?
   - Risk: Quality degradation
   - Mitigation: Human-in-loop approval required

4. **Cross-DNA Coordination**: How does Plan DNA interact with other DNAs (Rose Forest, Infinity Bridge)?
   - Current: Via links and external indexing
   - Future: AD4M perspectives for semantic queries

---

## Next Steps (SDD Process)

1. **Review this spec** (get ≥2 reviewers)
2. **Write test plan** based on this spec
3. **Review test plan**
4. **Write tests** based on test plan
5. **Correct spec** based on test insights
6. **Write documentation** (tutorials, examples)
7. **Implement** the Rust code
8. **Correct spec** based on implementation errors
9. **Run test suite** and iterate

---

## Provenance

- **Created by**: Meta-Reflexive Planning Initiative
- **Session ID**: `014eqDXY8HcJxqNfejD8zK37`
- **Branch**: `claude/meta-reflexive-planning-014eqDXY8HcJxqNfejD8zK37`
- **Date**: 2025-11-16
- **Sources**:
  - `ARF/docs/architecture.md` (Darwin Module vision)
  - `ARF/validation/models.py` (Vote model)
  - `ARF/dnas/rose_forest/BUDGET_SYSTEM.md` (Governance)
  - User prompt (Meta-Loop v0.1 design)
- **Epistemic Status**: `hypothesis` → `design`
- **Confidence**: 0.75 (high confidence in structure, uncertainty in parameter calibration)

---

**License**: Compassion Clause / FLOSS-compatible
**Version**: 0.1.0
**Status**: Draft Specification (awaiting review)
