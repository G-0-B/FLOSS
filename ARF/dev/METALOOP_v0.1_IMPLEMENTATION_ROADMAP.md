# MetaLoop v0.1 Implementation Roadmap

**Status**: Implementation Plan
**Author**: Meta-Reflexive Planning Initiative
**Date**: 2025-11-16
**Session ID**: 014eqDXY8HcJxqNfejD8zK37
**Branch**: `claude/meta-reflexive-planning-014eqDXY8HcJxqNfejD8zK37`
**Epistemic Status**: `working` (grounded in existing patterns)
**Confidence**: 0.82

---

## Executive Summary

This roadmap implements **MetaLoop v0.1**—the meta-reflexive planning layer that enables FLOSSIOULLK to evolve itself systematically.

**Key Deliverables:**
1. Plan DNA (Holochain) for versioned, critiqued, executable plans
2. Epistemic Tag Schema integrated across all knowledge structures
3. Meta-Loop operational process (6-step iteration cycle)
4. CLI tooling (`arf plan` commands)
5. First dogfooding iteration: using MetaLoop to improve MetaLoop

**Timeline**: ~60-80 hours sequential, ~20-30 hours wall time with parallelization
**Completion Target**: 2-3 weeks from kickoff

---

## Phase 0: Foundation (Hours 0-8)

**Goal**: Get organized and validate approach.

### Tasks

#### 0.1 Specification Review & Refinement
- **What**: Review `PLAN_DNA_SPECIFICATION_v0.1.md` and `EPISTEMIC_TAG_SCHEMA_v0.1.md`
- **Who**: 2+ reviewers (mix of human + AI)
- **Output**: Reviewed specs with feedback incorporated
- **Success**: ≥2 approvals, no blocking critiques
- **Time**: 4 hours
- **Parallelizable**: Yes (multiple reviewers)

#### 0.2 Test Plan Creation
- **What**: Write comprehensive test plan following SDD methodology
- **Based on**: Both specifications
- **Output**: `PLAN_DNA_TEST_PLAN_v0.1.md`
- **Success**: Covers all entry types, validation rules, coordinator functions
- **Time**: 4 hours
- **Dependencies**: 0.1 complete

---

## Phase 1: Core Plan DNA (Hours 8-28)

**Goal**: Implement Plan DNA Holochain code.

### Tasks

#### 1.1 DNA Scaffolding
- **What**: Create DNA directory structure
- **Commands**:
  ```bash
  cd ARF/dnas
  hc dna init plan_dna
  cd plan_dna
  hc zome init integrity plan_integrity
  hc zome init coordinator plan_coordinator
  ```
- **Output**: Empty DNA with zomes
- **Time**: 1 hour
- **Parallelizable**: No

#### 1.2 Entry Type Definitions (Integrity Zome)
- **What**: Implement all 6 entry types:
  - `PlanVersion`
  - `Critique`
  - `Distillation`
  - `Proposal`
  - `Vote`
  - `Experiment`
- **File**: `ARF/dnas/plan_dna/zomes/integrity/src/lib.rs`
- **Also Define**: Shared types (`EpistemicTag`, `CritiqueSeverity`, `ProposalStatus`, etc.)
- **Success**: Compiles, all types defined as per spec
- **Time**: 4 hours
- **Parallelizable**: Could split by entry type (2 people × 2 hours each)
- **Dependencies**: 1.1

#### 1.3 Validation Rules (Integrity Zome)
- **What**: Implement validation functions for each entry type
- **Key Rules**:
  - Confidence bounds [0.0, 1.0]
  - Semantic versioning format
  - Hash references validity
  - Author must be creator
  - Status transition state machines
- **Success**: All validation tests pass
- **Time**: 6 hours
- **Parallelizable**: Split by entry type
- **Dependencies**: 1.2

#### 1.4 Coordinator Functions (Plan Management)
- **What**: Implement CRUD operations for plans
- **Functions**:
  - `create_plan`
  - `get_plan`
  - `get_plan_history`
  - `get_latest_plan_version`
- **File**: `ARF/dnas/plan_dna/zomes/coordinator/src/plan.rs`
- **Success**: Can create, retrieve, and version plans
- **Time**: 3 hours
- **Dependencies**: 1.3

#### 1.5 Coordinator Functions (Critique & Distillation)
- **What**: Implement critique and distillation operations
- **Functions**:
  - `add_critique`
  - `get_critiques_for`
  - `create_distillation`
  - `get_distillations_by_topic`
- **File**: `ARF/dnas/plan_dna/zomes/coordinator/src/critique.rs`, `distillation.rs`
- **Success**: Can critique plans and create distillations
- **Time**: 3 hours
- **Parallelizable**: Yes (2 people, 1.5 hours each)
- **Dependencies**: 1.3

#### 1.6 Coordinator Functions (Proposals & Voting)
- **What**: Implement governance operations
- **Functions**:
  - `create_proposal`
  - `vote_on_proposal`
  - `get_proposal_votes`
  - `compute_proposal_outcome`
  - `finalize_proposal`
- **File**: `ARF/dnas/plan_dna/zomes/coordinator/src/proposal.rs`
- **Special**: Integrate with committee validation logic
- **Success**: Can propose, vote, and finalize with consensus
- **Time**: 4 hours
- **Dependencies**: 1.3

#### 1.7 Budget Integration
- **What**: Integrate with existing Rose Forest budget system
- **Pattern**: Reuse `ARF/dnas/rose_forest/zomes/coordinator/src/budget.rs`
- **Costs**: As specified in `PLAN_DNA_SPECIFICATION_v0.1.md`
- **File**: `ARF/dnas/plan_dna/zomes/coordinator/src/budget.rs`
- **Success**: All operations consume appropriate RU
- **Time**: 2 hours
- **Dependencies**: 1.4, 1.5, 1.6

#### 1.8 DNA Packaging & Deployment
- **What**: Build and test DNA
- **Commands**:
  ```bash
  cd ARF/dnas/plan_dna
  hc dna pack workdir/dna
  hc sandbox generate workdir/
  hc sandbox run -p 8889 workdir/
  ```
- **Output**: Runnable DNA on local sandbox
- **Time**: 1 hour
- **Dependencies**: 1.7

---

## Phase 2: Epistemic Integration (Hours 28-36)

**Goal**: Integrate epistemic tags across existing systems.

### Tasks

#### 2.1 Update Knowledge Triple Schema
- **What**: Add `EpistemicAnnotation` to `KnowledgeTriple`
- **Files**:
  - `ARF/dnas/rose_forest/zomes/ontology_integrity/src/lib.rs`
  - `ARF/conversation_memory.py`
- **Migration**: Create migration path for existing triples
- **Success**: Triples have epistemic metadata
- **Time**: 3 hours
- **Parallelizable**: Rust + Python in parallel (2 people × 1.5 hours)

#### 2.2 Extend Committee Validation
- **What**: Map validation results to epistemic tags
- **File**: `ARF/validation/committee.py`
- **New Function**: `to_epistemic_tag(result: ValidationResult)`
- **Success**: Validation results automatically tagged
- **Time**: 2 hours
- **Dependencies**: 2.1

#### 2.3 Epistemic Query Functions
- **What**: Add query capabilities for epistemic metadata
- **Functions**:
  - `get_knowledge_by_confidence(min_confidence)`
  - `get_plans_by_status(epistemic_tag)`
  - `get_contradicted_claims()`
  - `get_unknowns_by_topic(topic)`
- **Files**: Coordinator zomes in Rose Forest and Plan DNA
- **Success**: Can filter/search by epistemic properties
- **Time**: 3 hours
- **Dependencies**: 2.1

---

## Phase 3: CLI & Python Integration (Hours 36-48)

**Goal**: Make Plan DNA accessible via `arf plan` commands.

### Tasks

#### 3.1 Python-Holochain Bridge (Plan DNA)
- **What**: Create Python client for Plan DNA calls
- **Pattern**: Reuse existing bridge from `ARF/tests/integration/test_holochain_python_bridge.py`
- **File**: `ARF/plan_dna_client.py`
- **Functions**: Mirror all coordinator functions
- **Success**: Can call Plan DNA from Python
- **Time**: 3 hours

#### 3.2 CLI: Plan Management
- **What**: Implement `arf plan` subcommands
- **File**: `ARF/cli/plan.py`
- **Commands**:
  ```bash
  arf plan create <file>          # Create plan from markdown
  arf plan list                   # List all plans
  arf plan show <plan_id>         # Show plan details
  arf plan history <plan_id>      # Show version history
  arf plan critique <plan_id>     # Add critique
  ```
- **Output**: Rich formatted output + JSON mode
- **Success**: All commands work, human-readable
- **Time**: 4 hours
- **Dependencies**: 3.1

#### 3.3 CLI: Governance
- **What**: Implement proposal and voting commands
- **File**: `ARF/cli/plan.py` (extend)
- **Commands**:
  ```bash
  arf plan propose <description>  # Create proposal
  arf plan vote <proposal_id> <approve|reject> --confidence 0.8
  arf plan proposals              # List open proposals
  arf plan finalize <proposal_id> # Finalize proposal
  ```
- **Success**: Can participate in governance via CLI
- **Time**: 3 hours
- **Dependencies**: 3.1

#### 3.4 CLI: Distillation
- **What**: Implement distillation commands
- **File**: `ARF/cli/plan.py` (extend)
- **Commands**:
  ```bash
  arf plan distill <topic> <synthesis> --evidence <hash> --unknowns "..."
  arf plan distillations <topic>  # Show distillation history for topic
  ```
- **Success**: Can create and view distillations
- **Time**: 2 hours
- **Dependencies**: 3.1

---

## Phase 4: Meta-Loop Process Implementation (Hours 48-56)

**Goal**: Operationalize the 6-step Meta-Loop iteration cycle.

### Tasks

#### 4.1 Meta-Loop Orchestrator
- **What**: Implement Meta-Loop coordinator
- **File**: `ARF/meta_loop.py`
- **Functions**:
  - `start_iteration(focus_question)` → creates iteration plan
  - `collect_annotations(iteration_id)` → gathers inputs
  - `run_critique_pass(iteration_id)` → orchestrates critics
  - `run_distillation_pass(iteration_id)` → synthesizes
  - `create_plan_update(iteration_id)` → proposes changes
  - `finalize_iteration(iteration_id)` → closes loop
- **Success**: Can run full iteration cycle programmatically
- **Time**: 5 hours

#### 4.2 Iteration Templates
- **What**: Create templates for common iteration types
- **Templates**:
  - `feature_planning.md` (planning new features)
  - `architecture_refinement.md` (improving architecture)
  - `meta_improvement.md` (improving the planning process itself)
- **Location**: `ARF/dev/templates/iterations/`
- **Success**: Users can start iterations from templates
- **Time**: 2 hours
- **Parallelizable**: Yes (3 templates × 40 min each)

#### 4.3 CLI: Meta-Loop Commands
- **What**: Implement iteration management commands
- **File**: `ARF/cli/metaloop.py`
- **Commands**:
  ```bash
  arf metaloop start <focus_question> --template <name>
  arf metaloop status <iteration_id>
  arf metaloop collect <iteration_id> <input_file>
  arf metaloop critique <iteration_id>
  arf metaloop distill <iteration_id>
  arf metaloop finalize <iteration_id>
  ```
- **Success**: Can manage full iteration lifecycle via CLI
- **Time**: 3 hours
- **Dependencies**: 4.1, 4.2

---

## Phase 5: Testing & Validation (Hours 56-68)

**Goal**: Ensure everything works correctly.

### Tasks

#### 5.1 Unit Tests (Rust)
- **What**: Write Rust unit tests for all entry types and validations
- **File**: `ARF/dnas/plan_dna/zomes/integrity/src/lib.rs` (inline tests)
- **Coverage**: All validation rules, edge cases
- **Success**: `cargo test` passes with >90% coverage
- **Time**: 4 hours
- **Parallelizable**: Split by entry type

#### 5.2 Integration Tests (Python)
- **What**: Write integration tests for CLI and Python client
- **File**: `ARF/tests/integration/test_plan_dna.py`
- **Scenarios**:
  - Create plan, add critique, propose change, vote, finalize
  - Run full meta-loop iteration
  - Epistemic tag queries
- **Success**: All scenarios pass
- **Time**: 4 hours
- **Dependencies**: All prior phases

#### 5.3 Tryorama Scenario Tests (Holochain)
- **What**: Write multi-agent scenario tests
- **File**: `ARF/tests/tryorama/plan_dna.test.ts`
- **Scenarios**:
  - Multiple agents proposing and voting
  - Conflict resolution
  - Budget enforcement
- **Success**: All scenarios pass
- **Time**: 4 hours
- **Dependencies**: Phase 1 complete

---

## Phase 6: Documentation & Dogfooding (Hours 68-80)

**Goal**: Document system and use it on itself.

### Tasks

#### 6.1 User Documentation
- **What**: Write comprehensive user guide
- **File**: `ARF/docs/PLAN_DNA_USER_GUIDE.md`
- **Sections**:
  - Getting started
  - Creating plans
  - Critique and distillation
  - Governance participation
  - Meta-Loop iterations
- **Success**: New users can onboard independently
- **Time**: 4 hours

#### 6.2 Developer Documentation
- **What**: Write developer reference
- **File**: `ARF/docs/PLAN_DNA_DEVELOPER_GUIDE.md`
- **Sections**:
  - Architecture overview
  - Entry type reference
  - Extending the system
  - Testing guidelines
- **Success**: Developers can contribute to Plan DNA
- **Time**: 3 hours
- **Parallelizable**: Yes (with 6.1)

#### 6.3 First Dogfooding Iteration: MetaLoop Improvement
- **What**: Use MetaLoop v0.1 to improve itself
- **Focus Question**: "How can we improve the Meta-Loop process based on v0.1 implementation experience?"
- **Process**:
  1. Start iteration: `arf metaloop start "MetaLoop Improvement"`
  2. Collect: Implementation learnings, test results, user feedback
  3. Critique: What worked? What didn't? What's missing?
  4. Distill: Extract lessons into distillation
  5. Propose: Concrete improvements for v0.2
  6. Finalize: Document and commit
- **Output**: `MetaLoop_v0.2_Proposal.md` + distillation entry
- **Success**: We've eaten our own dog food!
- **Time**: 5 hours
- **Dependencies**: All prior phases

---

## Phase 7: Release & Iteration (Hours 80+)

**Goal**: Ship v0.1 and start iteration cycle.

### Tasks

#### 7.1 Release Preparation
- **What**: Package for release
- **Checklist**:
  - [ ] All tests passing
  - [ ] Documentation complete
  - [ ] Example iterations included
  - [ ] CLI help text comprehensive
  - [ ] CHANGELOG.md updated
- **Output**: Tagged release `metaloop-v0.1.0`
- **Time**: 2 hours

#### 7.2 Announcement & Onboarding
- **What**: Announce to community and onboard users
- **Channels**: GitHub, Discord, mailing list
- **Content**: Release notes, tutorial video, sample iteration
- **Success**: ≥5 community members try it
- **Time**: 2 hours

#### 7.3 Ongoing Iteration Schedule
- **What**: Establish regular Meta-Loop cadence
- **Proposal**:
  - **Iteration 1**: Weeks 1-2 (bi-weekly cadence)
  - **Focus**: Immediate usability improvements
  - **Iteration 2**: Weeks 3-4
  - **Focus**: Governance refinements
  - **Iteration 3**: Weeks 5-6
  - **Focus**: Epistemic calibration
- **Success**: Calendar invites sent, first iteration scheduled
- **Time**: 1 hour

---

## Parallelization Strategy

**Sequential Critical Path** (~60 hours):
```
0.1 → 0.2 → 1.1 → 1.2 → 1.3 → 1.4 → 1.7 → 1.8 → 3.1 → 4.1 → 5.2 → 6.3 → 7.1
```

**Parallel Work Streams**:

| Stream | Tasks | Hours | Team Member |
|--------|-------|-------|-------------|
| Core DNA | 1.1-1.8 | 24 | Dev 1 (backend) |
| Epistemic | 2.1-2.3 | 8 | Dev 2 (data) |
| CLI | 3.1-3.4 | 12 | Dev 3 (CLI/UX) |
| Meta-Loop | 4.1-4.3 | 10 | Dev 4 (orchestration) |
| Testing | 5.1-5.3 | 12 | Dev 5 (QA) |
| Docs | 6.1-6.2 | 7 | Tech Writer |

**Wall Time Estimate**: 20-30 hours (with 4-6 contributors)

---

## Success Metrics

### Quantitative Metrics

1. **Code Coverage**: ≥90% for Plan DNA
2. **Test Pass Rate**: 100% (all tests must pass)
3. **CLI Command Count**: ≥15 functional commands
4. **Dogfooding Iterations**: ≥1 successful meta-loop run
5. **Community Adoption**: ≥5 external users within first month

### Qualitative Metrics

1. **Epistemic Transparency**: Users report feeling comfortable expressing uncertainty
2. **Governance Participation**: ≥60% proposal approval rate (healthy balance)
3. **Meta-Learning**: Evidence of system improving itself via distillations
4. **Developer Experience**: New contributors onboard in <2 hours
5. **ULLK Alignment**: Community confirms compassionate, transparent, knowledge-seeking culture

---

## Risk Mitigation

### Risk 1: Complexity Overload
- **Symptom**: Users find system too complex
- **Mitigation**: Start with minimal viable workflow, hide advanced features
- **Fallback**: Provide "simple mode" CLI aliases

### Risk 2: Governance Deadlock
- **Symptom**: Proposals stall due to insufficient votes
- **Mitigation**: Auto-finalize after 7 days if threshold met
- **Fallback**: Escalation to trusted maintainers for urgent decisions

### Risk 3: Low Adoption
- **Symptom**: Community doesn't use Plan DNA
- **Mitigation**: Lead by example—use it for all internal planning
- **Fallback**: Gamification (reputation points for participation)

### Risk 4: Epistemic Tag Inflation
- **Symptom**: Everything marked "Validated" without evidence
- **Mitigation**: Calibration metrics track accuracy over time
- **Fallback**: Require evidence links for high-confidence tags

### Risk 5: Meta-Loop Overhead
- **Symptom**: Iterations take too long, feel bureaucratic
- **Mitigation**: Timebox each phase (e.g., 2 days max per critique pass)
- **Fallback**: Reduce iteration frequency for low-priority topics

---

## Dependencies & Prerequisites

### Technical Dependencies
- [x] Holochain installed (`hc` CLI)
- [x] Rust toolchain (cargo, rustc)
- [x] Python 3.9+ with ARF dependencies
- [x] Existing Rose Forest DNA (for budget integration)
- [x] Existing validation committee code

### Knowledge Prerequisites
- [ ] Read `PLAN_DNA_SPECIFICATION_v0.1.md`
- [ ] Read `EPISTEMIC_TAG_SCHEMA_v0.1.md`
- [ ] Understand SDD methodology (CLAUDE.md)
- [ ] Familiar with Holochain DNA development
- [ ] Understand ULLK principles

### Social Prerequisites
- [ ] ≥2 reviewers committed for spec review
- [ ] ≥3 developers available for parallel work
- [ ] Community informed and excited about Meta-Loop

---

## Iteration Checkpoints

### Week 1 Checkpoint (after Phase 2)
- **Deliverable**: Working Plan DNA + Epistemic integration
- **Demo**: Create plan, critique it, query by epistemic tag
- **Decision**: Go/no-go for CLI development

### Week 2 Checkpoint (after Phase 4)
- **Deliverable**: Full CLI + Meta-Loop orchestrator
- **Demo**: Run complete iteration cycle via CLI
- **Decision**: Ready for testing phase?

### Week 3 Checkpoint (after Phase 6)
- **Deliverable**: Tested, documented, dogfooded system
- **Demo**: Show MetaLoop improving itself
- **Decision**: Ready for release?

---

## Post-v0.1 Roadmap (Future Iterations)

### v0.2 (Iteration 2-3)
- **Focus**: Usability improvements from v0.1 feedback
- **Features**:
  - Rich terminal UI (TUI) for plan browsing
  - Automatic distillation suggestions (LLM-powered)
  - Email notifications for proposal voting

### v0.3 (Iteration 4-6)
- **Focus**: Advanced governance
- **Features**:
  - Reputation-weighted voting
  - Delegation mechanisms
  - Quadratic voting experiments

### v0.4 (Iteration 7-10)
- **Focus**: AI-assisted meta-learning
- **Features**:
  - Automated pattern extraction from experiments
  - LLM-powered critique generation
  - Predictive analytics for plan success

### v1.0 (Iteration 10+)
- **Milestone**: Production-ready Meta-Reflexive System
- **Criteria**:
  - Proven track record (≥50 successful iterations)
  - Community-driven (≥20 active contributors)
  - Self-improving (measurable improvements over time)
  - Fully integrated with all FLOSSIOULLK subsystems

---

## Provenance

- **Created by**: Meta-Reflexive Planning Initiative
- **Session ID**: `014eqDXY8HcJxqNfejD8zK37`
- **Branch**: `claude/meta-reflexive-planning-014eqDXY8HcJxqNfejD8zK37`
- **Date**: 2025-11-16
- **Sources**:
  - `PLAN_DNA_SPECIFICATION_v0.1.md`
  - `EPISTEMIC_TAG_SCHEMA_v0.1.md`
  - `META_REFLEXIVE_PLANNING_ANALYSIS.md`
  - `ARF/dev/ROADMAP_PHASE4_PLUS.md` (existing pattern)
  - User prompt (Meta-Loop v0.1 design)
- **Epistemic Status**: `working`
- **Confidence**: 0.82 (high confidence in approach, moderate uncertainty in time estimates)
- **Unknowns**:
  - Actual implementation time (estimates may vary by ±30%)
  - Community adoption rate
  - Performance at scale (>1000 plans)
- **Contradictions**: None known

---

**License**: Compassion Clause / FLOSS-compatible
**Version**: 0.1.0
**Status**: Implementation Plan (ready to execute)
