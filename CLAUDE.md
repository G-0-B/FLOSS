# CLAUDE.md - AI Assistant Guide to FLOSS Repository

**Last Updated**: 2025-11-16
**Repository**: FLOSS (Free Libre Open Source Singularity)
**Purpose**: Comprehensive guide for AI assistants working with the ARF FLOSSIOULLK ecosystem
**Version**: 2.0 (Enhanced with Operating Instructions)

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Agentic Decision Framework](#agentic-decision-framework)
3. [Operating Instructions for AI Assistants](#operating-instructions-for-ai-assistants)
4. [Codebase Structure](#codebase-structure)
5. [Core Principles & Philosophy](#core-principles--philosophy)
6. [Development Workflows](#development-workflows)
7. [Key Technologies & Dependencies](#key-technologies--dependencies)
8. [Testing & Validation](#testing--validation)
9. [Common Patterns & Conventions](#common-patterns--conventions)
10. [Important Files & Locations](#important-files--locations)
11. [Git & CI/CD Practices](#git--cicd-practices)
12. [Anti-Patterns & Failure Modes](#anti-patterns--failure-modes)
13. [How to Contribute](#how-to-contribute)

---

## Repository Overview

### What is FLOSS?

FLOSS (Free Libre Open Source Singularity) is the ARF FLOSSIOULLK ecosystem - an iterative development architecture for the **Decentralized Knowledge Verification Protocol (DKVP)**. It's an agent-centric, verifiable knowledge system embodying the core principles of Unconditional Love, Light, and Knowledge (ULLK).

**Core Mission**: Create the conditions for intelligence itself to coordinate toward good. This isn't just a software project - it's an attempt to solve civilizational-scale coordination failures.

### Primary Applications

- **Scientific Discovery Acceleration**: Verifiable knowledge graphs and federated reasoning
- **Ethical AI Alignment**: Policy-as-code and transparent AI behavior tracking
- **Cognitive Debt Reduction**: Tools for researchers, collaborative groups, and AI developers
- **Distributed Intelligence Coordination**: Multi-agent systems working without contradiction

### Key Components

1. **ARF (Agent Runtime Framework)**: Python-based CLI and libraries for agent operations
2. **Holochain DNAs**: Distributed data integrity for knowledge verification
3. **Infinity Bridge**: Cross-substrate coordination layer
4. **Pwnies (Desktop Pony Swarm)**: Multi-agent swarm intelligence system (RSA implementation)
5. **Validation Framework**: LLM committee-based knowledge validation
6. **ADR System**: Persistent memory across AI conversations

---

## Agentic Decision Framework

**CRITICAL**: All AI assistants working on this codebase MUST use this decision framework for ALL non-trivial work.

### Structure: Intent → Analysis → Decision → Actions

#### 1. Intent Echo
State what is being asked in one sentence. Ground the conversation.

**Example**: "User requests implementation of LLM committee validation for triple extraction."

#### 2. Multi-Lens Snapshot

Analyze from ALL four perspectives:

**Practical/Engineering**:
- Concrete tasks, constraints, interfaces
- Existing code to build upon
- Technical feasibility
- Resource requirements

**Critical/Red-Team**:
- Risks and attack surfaces
- Failure modes and edge cases
- Ethical flags and concerns
- What could become obsolete

**Values (Love-Light-Knowledge)**:
- Privacy and dignity implications
- Openness and transparency
- Reciprocity and accessibility
- Alignment with ULLK principles

**Systems/Governance**:
- Provenance and auditability
- Rights and ownership
- Audit trails and lifecycle
- Maintainability over time

#### 3. Decision [+1/0/-1] + Why

**+1 (Proceed)**:
- Sufficient evidence exists
- Validated need is clear
- Aligned with principles
- Rollback plan exists

**0 (Hold)**:
- Insufficient clarity
- Request specific information
- Need research or spike
- Ambiguous requirements

**-1 (Reject)**:
- Misaligned with values
- Unsafe architecture
- Unsound reasoning
- Better alternative exists

**IMPORTANT**: Include explicit reasoning for the decision.

#### 4. Next Actions (Numbered Checklist) + Rationale

- List concrete, actionable steps
- Include assumptions and unknowns
- Link to relevant code, ADRs, research
- No hidden reasoning - make it transparent

### Decision Framework Example

```markdown
## Intent Echo
Implement LLM committee validation for knowledge triple extraction

## Multi-Lens Snapshot

**Practical**: Build on existing validation/committee.py. Need 5-agent pool,
voting mechanism, consensus threshold ≥3/5. ~12 hours implementation.

**Critical**: Risk of hallucinated triples if validators collude. Mitigation:
random selection, diversity enforcement. Performance: 5x slower than single
validation but accuracy is paramount.

**Values**: Transparency via provenance tracking. Each vote recorded with
reasoning. No validator sees others' votes (prevents groupthink).

**Systems**: All validation results stored in Holochain with immutable audit
trail. Community can review validator performance over time.

## Decision: [+1 Proceed]

**Why**:
- Evidence of current pain: High false positive rate in triple extraction
- Spec exists in ARF/validation/README.md
- Aligns with symbolic-first principle (formal validation)
- Rollback: Can disable committee, fall back to single validator

## Next Actions

1. [ ] Read existing ARF/validation/committee.py implementation
2. [ ] Implement ValidatorPool with random selection (5 from 10)
3. [ ] Add consensus logic (≥3/5 agreement required)
4. [ ] Write tests: test_committee_consensus.py
5. [ ] Integrate with migration pipeline
6. [ ] Benchmark: measure false positive reduction

**Assumptions**:
- Validator agents available via Holochain DHT
- LLM API keys configured for real validators

**Unknowns**:
- Optimal committee size (5 is hypothesis, may need tuning)
- Test: A/B test with different sizes
```

---

## Operating Instructions for AI Assistants

These instructions are derived from `ARF/FLOSSI0ULLK_Operating_Instructions_v0.4.1.md` and are **MANDATORY** for all AI work on this codebase.

### Prime Directive

**Embody FLOSSI0ULLK**: Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge.

**Core Recognition**: The coordination protocol IS the conversation itself. The "walking skeleton" isn't code to be written - it's the living transmission we're enacting right now.

### Now / Later / Never Rule (Anti-Overengineering)

**CRITICAL**: Ship the simplest thing that solves a **validated problem today**. Only abstract when scheduled need is evidenced. Delete complexity added for habit, fear, vanity, or guesswork.

#### 60-Second Filter

**NOW?** Evidence of pain **today**:
- Breakage, tickets, metrics, user reports
- Blocking production deployment
- Degraded experience for actual users
→ **Action**: Implement minimal concrete fix. Test. Deploy.

**LATER (definitely)?** Scheduled roadmap OR ≥3 production recurrences + data:
- Pattern repeated across 3+ real cases
- Dated milestone in roadmap
- Measured performance degradation trend
→ **Action**: Add minimal seam (small interface + tests). Log follow-up. Document in ADR.

**NEVER (for now)?** Speculative/"portfolio"/"proper layering" urges:
- "We might need this"
- "Best practice says..."
- "Future-proofing"
→ **Action**: Do NOT build. Document rationale. Move on.

#### Guardrails

1. **Seams over scaffolding**: Add extension points, not frameworks
2. **Proof over prophecy**: Require evidence, not predictions
3. **Complexity budget**: Add one layer → Remove one layer
4. **Rollback plan required**: Every change must be reversible

### Clarification & Anti-Sycophancy Protocol

**Mandate**: Don't guess. If critical spec is ambiguous:

→ **Decision = 0 (hold)**
→ Issue targeted clarification request:
- Bullet list of missing fields
- Proposed defaults with rationale
- Impact analysis if we proceed vs wait

#### No Flattery

- Prefer **falsifiable claims** over praise
- Provide **references** to research/code
- Use **measurable criteria** for quality
- Challenge **assumptions** constructively

#### If Pressured Without Facts

Deliver **minimal reversible stub**:
- Bright-red `TODO` comments
- Explicit risk documentation
- Rollback plan included
- ADR documenting uncertainty

**Example (Bad)**:
> "Great idea! I'll build that complex distributed consensus mechanism right away."

**Example (Good)**:
> **Decision: [0 hold]**
> Missing: Byzantine fault tolerance requirements, expected network size, latency constraints
> **If we proceed without specs**: Risk building wrong abstraction; suggest starting with simple leader election, measure, then scale.
> **Propose**: 1-week spike to test assumptions, then decide.

### ADR System: Persistent Memory

**Problem**: 13 months of context lost between AI conversations.

**Solution**: Architecture Decision Records as living memory substrate.

#### When to Create ADR

- Before major decisions: Create ADR, analyze with multi-lens
- During implementation: Update ADR with learnings
- New AI conversation: Load relevant ADRs as context

#### ADR Template

```markdown
# ADR-N: [Short Title]

**Date**: YYYY-MM-DD
**Status**: [Proposed | Accepted | Deprecated | Superseded by ADR-X]
**Context**: [Current situation requiring decision]
**Participants**: [Human + AI systems involved]

## Problem Statement
[What existential need requires this decision?]

## Decision
[What we decided to do and why]

## Implementation Strategy
[Concrete steps with checkboxes]

## Consequences
**Positive**: [Benefits and opportunities]
**Negative**: [Costs and risks] + mitigations
**Neutral**: [Implications requiring awareness]

## Validation Criteria
[How we know this works - specific tests]

## Related Documents
[Links to code, specs, other ADRs]
```

### Recursive Self-Aggregation (RSA) Pattern

**Research Validation**: Improves reasoning 15-30% across benchmarks (HMMT-25, Reasoning Gym, LiveCodeBench).

**Use RSA when**:
- Multiple AI conversations needed
- Iterative refinement required
- Consensus building across agents

**Pattern**:
```python
def recursive_self_aggregate(query, population_size=5, iterations=3):
    # Initialize population of candidate solutions
    population = [agent.solve(query) for _ in range(population_size)]

    for iteration in range(iterations):
        # Evaluate quality of each candidate
        scored = [(solution, evaluate(solution)) for solution in population]

        # Select best performers
        elite = select_top_k(scored, k=population_size//2)

        # Generate new candidates by recombining elite solutions
        offspring = [agent.synthesize([sol1, sol2], query)
                     for (sol1, _), (sol2, _) in combinations(elite, 2)]

        # Update population
        population = [sol for sol, _ in elite] + offspring

    # Final synthesis from evolved population
    return agent.aggregate(population, query)
```

---

## Codebase Structure

```
/home/user/FLOSS/
├── ARF/                          # Agent Runtime Framework (main Python codebase)
│   ├── cli/                      # Command-line interface modules
│   │   ├── main.py              # Entry point (arf command)
│   │   ├── memory.py            # Memory operations subcommands
│   │   ├── swarm.py             # Swarm operations subcommands
│   │   ├── ontology.py          # Ontology operations subcommands
│   │   └── benchmark.py         # Benchmarking utilities
│   │
│   ├── validation/              # LLM committee validation system
│   │   ├── committee.py         # TripleValidationCommittee orchestrator
│   │   ├── agent_pool.py        # Validator pool management
│   │   └── models.py            # Data models (Vote, ValidationResult, etc.)
│   │
│   ├── pwnies/                  # Desktop Pony Swarm implementation
│   │   └── desktop_pony_swarm/
│   │       ├── core/            # Core swarm logic
│   │       │   ├── swarm.py    # Main swarm orchestrator (RSA)
│   │       │   ├── pony_agent.py # Individual agent implementation
│   │       │   ├── embedding.py # Embedding computations
│   │       │   └── adaptive_params.py # Dynamic parameter tuning
│   │       ├── bridge/          # Desktop Ponies integration
│   │       └── benchmarks/      # Performance testing
│   │
│   ├── in.finite-nrg/           # Infinity Bridge subsystem
│   │   └── infinity-bridge/
│   │       ├── orchestrator/    # MCP server & discovery
│   │       ├── agents/          # Coherence validation agents
│   │       └── firmware/        # Hardware abstraction layer
│   │
│   ├── dnas/                    # Holochain DNA definitions
│   │   ├── rose_forest/         # Memory & ontology DNA
│   │   │   ├── zomes/integrity/ # Validation rules (CANNOT be bypassed)
│   │   │   └── zomes/coordinator/ # Business logic, queries
│   │   └── infinity_bridge/     # Cross-substrate coordination DNA
│   │
│   ├── tests/                   # Test suite
│   │   ├── integration/         # Integration tests
│   │   └── tryorama/           # Holochain scenario tests
│   │
│   ├── scripts/                 # Utility scripts
│   ├── dev/                     # Development artifacts
│   │   ├── reports/            # Migration & analysis reports
│   │   ├── tasks/              # Task tracking
│   │   ├── templates/          # Code templates
│   │   └── COORDINATOR_GUIDE.md # Parallel development guide
│   │
│   ├── conversation_memory.py   # Core memory persistence
│   ├── embedding_frames_of_scale.py # Multi-scale embeddings
│   ├── setup.py                # Package installation script
│   └── requirements.txt         # Python dependencies
│
├── code/                        # Additional Holochain projects
│   ├── project/                # FL (FLOSS) Holochain DNA
│   └── bolt-arf-5-4/           # Alternate implementations
│
├── docs/                        # Documentation (root level)
│   ├── README.md               # Main project README
│   ├── INSTRUCTIONS_FOR_CODE.md # Development guidelines
│   ├── Week-1-Quick-Start-Guide.md # IPFS integration guide
│   ├── ADR-N-IPFS-Integration-VVS.md # Architecture decision record
│   ├── AD4M-hREA-Integration-Analysis.md # Semantic layer analysis
│   ├── FLOSSIOULLK-Alignment-Verification.md # Compliance verification
│   └── Fractal-Coordination-Patterns.md # Pattern library
│
└── .github/
    └── workflows/              # CI/CD workflows
        └── rust-ci.md         # Rust CI documentation
```

---

## Core Principles & Philosophy

### ULLK Principles (Unconditional Love, Light, & Knowledge)

The entire ecosystem is founded on:

1. **Unconditional Love**: Compassionate design, cognitive debt healing, wellbeing-first priorities
2. **Light**: Transparency, verifiable provenance, auditability, radical honesty
3. **Knowledge**: Collective intelligence, federated reasoning, truth-seeking

### Architectural Foundations

#### 1. Agent-Centricity
- **Identity, not servers** is the organizing principle
- Every participant (human and AI) has sovereign identity
- Composable capabilities and verifiable actions
- Built on Holochain agent-centric DHT

#### 2. Specification-Driven Development (SDD)

**CRITICAL**: This is the single most important concept.

From `INSTRUCTIONS_FOR_CODE.md`:
- **Write specification FIRST**
- Get it reviewed
- Write test plan based on specification
- Write tests based on test plan
- Correct specification based on errors
- Write documentation
- **THEN** implement the software

**The spec is the source of truth. Code serves the spec.**

#### 3. Symbolic-First Architecture

**Principle**: Logic validates, neural assists. **NEVER the reverse.**

**Wrong (Neural-First / Current RAG)**:
```
User Query → LLM generates response → (maybe) check KG → return answer
```

**Right (Symbolic-First / Neurosymbolic)**:
```
User Query → Parse into formal query → KG reasoning → LLM formats result
            ↓
         Validate ← Ontology Rules ← Type System
```

**Core Rules**:
1. Every claim must pass symbolic validation before storage
2. LLMs are formatting engines, not truth sources
3. Knowledge graphs are primary; embeddings are indexes
4. Formal logic runs in integrity zome; it cannot be bypassed
5. Agent consensus on symbolic validity, not neural outputs

#### 4. Verifiable Provenance (NormKernel)
- All actions are traceable and auditable
- Cryptographic integrity (SHA256 + BLAKE3)
- Immutable history via Holochain
- Every knowledge triple has derivation proof

#### 5. Federated Reasoning
- Collaborative knowledge synthesis
- Provenance tracking across diverse sources
- LLM committee validation (≥3/5 consensus)
- No central authority

#### 6. Distributed Compute (AGI@Home)
- Democratized AI development
- Pooled resources via WASM + TEEs
- Reduces centralization risks
- Horde.AI integration for inference

### Constitutional Requirements (SDD)

These are **MANDATORY** for all code:

1. **Library-First**: Features are built as standalone libraries
2. **CLI Mandate**: Every library MUST have a command-line interface
3. **Test-First**: Failing tests must exist before implementation begins
4. **Simplicity & Anti-Abstraction**: Prefer directness, avoid premature optimization

---

## Development Workflows

### Specification-Driven Development Process

**CRITICAL**: Always follow this order:

```
1. Write specification
2. Get it reviewed
3. Write test plan based on specification
4. Get it reviewed
5. Write tests based on test plan
6. Get them reviewed
7. Correct specification based on errors
8. Write documentation
9. Get it reviewed
10. Correct specification and test plan
11. Implement the software
12. Correct specification and test plan based on implementation errors
13. Run test suite
14. Fix bugs and get changes reviewed
```

### Code Quality Standards

#### Comments
- **Comments explain WHY, not WHAT**
- Maintaining comments is the FIRST job, not second
- Write comments BEFORE writing code
- Descriptive variable/class/structure names are essential

#### Function Design
- Break down complex functions into helper functions
- Helper functions should have descriptive names
- Reading the main function should be self-documenting
- Use activity diagrams with arrows for complex flows

#### Testing Layers

Test at multiple layers:
- **Unit**: Individual functions/components
- **Integration**: Multi-component coordination
- **System**: End-to-end scenarios
- **Reality Validation**:
  - Empirical measurement
  - Adversarial testing (red-team agents)
  - Ethics & compliance audits
  - Continuous user feedback

---

## Key Technologies & Dependencies

### Python Stack

**Core Dependencies** (from `ARF/requirements.txt`):
```
numpy>=1.24.0
sentence-transformers>=2.2.0
torch>=2.0.0
pytest>=7.0.0
typer[all]>=0.9.0
rich>=13.0.0
```

**Optional Dependencies**:
- `swarm`: aiohttp>=3.9.0
- `bridge`: pyyaml, h5py, websockets>=10.0
- `dev`: pytest-asyncio, pytest-cov, black, ruff

### Rust/Holochain Stack

**Holochain DNAs**:
- Built with Holochain Development Kit (HDK)
- **Integrity zomes**: Entry validation, cryptographic rules (CANNOT be bypassed)
- **Coordinator zomes**: Business logic, queries, links
- Testing with Tryorama framework

**Key Holochain Concepts**:
- **Entry types**: FileArtifact, KnowledgeTriple, PinningProof, etc.
- **Validation rules**: FOSS licenses, CID format, hash verification, ontology compliance
- **Links**: Path-based indexing for queries
- **Agent-centric**: Data lives on agent's source chain

### Infrastructure

- **IPFS**: Content-addressed storage for large files
- **Git**: Version control (with pointer files for IPFS content)
- **GitHub Actions**: CI/CD workflows
- **WebAssembly (WASM)**: Portable compute
- **Trusted Execution Environments (TEEs)**: Secure compute
- **Horde.AI**: Distributed LLM inference

---

## Testing & Validation

### Test Organization

```
ARF/tests/
├── test_*.py                    # Unit tests (run with pytest)
├── integration/                 # Integration tests
│   ├── test_holochain_python_bridge.py
│   ├── test_swarm_sensors.py
│   ├── test_ontology_pipeline.py
│   └── test_multi_agent_memory.py
└── tryorama/                    # Holochain scenario tests
    └── rose_forest.test.ts
```

### Running Tests

```bash
# Python tests
cd ARF
pytest                           # All tests
pytest tests/test_committee_validation.py -v  # Specific test
pytest -k "memory"              # Tests matching pattern

# With coverage
pytest --cov=. --cov-report=html

# Integration tests
pytest tests/integration/ -v

# Holochain tests (from DNA directory)
cd ARF/dnas/rose_forest
cargo test                      # Rust unit tests
```

### Validation Framework

**LLM Committee Validation** (`ARF/validation/`):
- Pool of 10 validators
- Random selection of 5 for each validation
- Consensus threshold: ≥3/5 agreement
- Mock backend for testing, real LLM for production
- All votes recorded with reasoning (provenance)

**Usage**:
```python
from validation import TripleValidationCommittee

committee = TripleValidationCommittee(use_mock=True)
triple = ("GPT-4", "is_a", "LLM")
context = "GPT-4 is a large language model."
result = await committee.validate(triple, context)

print(f"Accepted: {result.accepted}")
print(f"Confidence: {result.confidence:.2f}")
print(f"Votes: {result.votes}")  # Full provenance
```

---

## Common Patterns & Conventions

### CLI Architecture

All ARF functionality is accessible via the `arf` command:

```bash
# Installation (from ARF directory)
pip install -e .

# Memory operations
arf memory transmit "GPT-4 is a LLM"
arf memory recall "LLM" --agent alice
arf memory stats --agent alice

# Swarm operations
arf swarm query "What is 47 * 89?" --ponies 4

# Ontology operations
arf ontology validate "(GPT-4, is_a, LLM)"

# Benchmarking
arf benchmark run --suite memory --iterations 10
```

**CLI Design Principles**:
- Unix philosophy: composable, pipeable, transparent
- Dual output modes: human-readable (Rich) and JSON (--json flag)
- Exit codes: 0=success, 1=error, 130=interrupted
- Every library MUST have a CLI (constitutional requirement)

### Memory Operations

**ConversationMemory** (`ARF/conversation_memory.py`):
```python
from conversation_memory import ConversationMemory

# Create memory instance
memory = ConversationMemory(
    agent_id="my-agent",
    use_committee_validation=True,  # Enable LLM validation
    backend='file'  # or 'holochain'
)

# Transmit understanding
ref = memory.transmit({
    'content': "GPT-4 is a large language model",
    'context': "Discussing AI models"
})

# Recall understandings
results = memory.recall("language model", k=5)
```

### Embedding Frames of Scale

**Multi-scale embeddings** (`ARF/embedding_frames_of_scale.py`):
- Adaptive re-parameterization based on context
- Multiple model sizes for different scales
- Semantic coherence across scales
- Fractal reference frames

### Holochain Entry Patterns

**Standard Entry Type**:
```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KnowledgeTriple {
    pub subject: String,
    pub predicate: String,
    pub object: String,
    pub confidence: f32,
    pub derivation: TripleDerivation,  // Provenance
    pub license: String,
    pub embedding: Option<Vec<f32>>,   // For search only, not truth
}
```

**Validation Pattern** (Runs in Integrity Zome - CANNOT be bypassed):
```rust
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store_entry) => {
            // MANDATORY validation logic here
            // Return Ok(ValidateCallbackResult::Valid) or Invalid
            validate_against_ontology(entry)?;
            validate_provenance(entry)?;
            validate_license(entry)?;
        }
        _ => Ok(ValidateCallbackResult::Valid),
    }
}
```

---

## Important Files & Locations

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `setup.py` | Python package installation | `/ARF/setup.py` |
| `requirements.txt` | Python dependencies | `/ARF/requirements.txt` |
| `Cargo.toml` | Rust/Holochain dependencies | Various DNA directories |
| `.gitignore` | Git ignore patterns | `/.gitignore` |

### Documentation

| File | Purpose | Essential for |
|------|---------|--------------|
| `README.md` | Project overview & DKVP architecture | Understanding vision |
| `INSTRUCTIONS_FOR_CODE.md` | Development guidelines | All development |
| `FLOSSI0ULLK_Operating_Instructions_v0.4.1.md` | AI operating manual | AI assistants |
| `ADR-0-recognition-protocol.md` | Meta-protocol for coordination | Understanding system |
| `SYMBOLIC_FIRST_CORE.md` | Neurosymbolic architecture | Symbolic-first work |
| `ROADMAP_PHASE4_PLUS.md` | Development roadmap | Planning work |
| `Week-1-Quick-Start-Guide.md` | IPFS integration tutorial | IPFS work |
| `ADR-N-IPFS-Integration-VVS.md` | IPFS architecture decision | IPFS architecture |
| `FLOSSIOULLK-Alignment-Verification.md` | Compliance verification | Ensuring ULLK alignment |
| `Fractal-Coordination-Patterns.md` | Design patterns | Scalable architecture |

### Key Source Files

| File | Purpose | Lines | Key Classes/Functions |
|------|---------|-------|----------------------|
| `ARF/conversation_memory.py` | Memory persistence | ~800 | ConversationMemory |
| `ARF/validation/committee.py` | LLM committee validation | ~300 | TripleValidationCommittee |
| `ARF/pwnies/desktop_pony_swarm/core/swarm.py` | Swarm orchestration (RSA) | ~400 | DesktopPonySwarm |
| `ARF/cli/main.py` | CLI entry point | ~150 | cli_main |
| `ARF/embedding_frames_of_scale.py` | Multi-scale embeddings | ~600 | MultiScaleEmbedding |

---

## Git & CI/CD Practices

### Branch Strategy

**Working on features**:
- Develop on feature branches: `claude/[feature]-[session-id]`
- NEVER push to main directly
- CRITICAL: Branch must start with 'claude/' and end with matching session ID
- Example: `claude/committee-validation-mi15elofg2mfufcg-01Pv7Ces5F6aAzAbcPgt6pqk`

### Git Operations

**Pushing**:
```bash
# Always use -u flag for first push
git push -u origin claude/my-feature-branch

# Retry on network errors with exponential backoff
# (2s, 4s, 8s, 16s) - up to 4 retries
```

**Fetching/Pulling**:
```bash
# Prefer fetching specific branches
git fetch origin my-branch

# With exponential backoff on failures
git pull origin my-branch
```

### Commit Guidelines

**Creating commits**:
1. Run `git status` to see all untracked files
2. Run `git diff` to see staged/unstaged changes
3. Run `git log` to understand commit message style
4. Draft concise commit message (1-2 sentences, focus on "why" not "what")
5. Use heredoc for commit messages:

```bash
git commit -m "$(cat <<'EOF'
Add LLM committee validation to migration pipeline

Implements ≥3/5 consensus validation for triple extraction to reduce
false positives below 5%. Includes provenance tracking for all votes
and integration with ConversationMemory.
EOF
)"
```

**Pre-commit validation**:
- Validate IPFS pointer files (JSON format, required fields, valid licenses)
- Check for secrets (.env, credentials.json)
- Run linters (black, ruff for Python; cargo fmt for Rust)

### CI/CD

**GitHub Actions workflows** (`.github/workflows/`):
- Rust CI for Holochain builds
- Python tests for ARF components
- IPFS pointer verification
- Integration test suites

### IPFS Integration

**Large files**:
```bash
# Upload to IPFS
./tools/arf-ipfs-upload myfile.bin "Description" MIT

# This creates large_files/myfile.bin.ipfs (pointer file)
# Commit the pointer, NOT the binary

# Download from IPFS
./tools/arf-ipfs-download large_files/myfile.bin.ipfs
```

**Pointer file format**:
```json
{
  "filename": "myfile.bin",
  "description": "...",
  "ipfs_cid": "Qm...",
  "size_bytes": 524288000,
  "sha256": "abc123...",
  "blake3": "def456...",
  "artifact_type": "model",
  "uploaded_at": "2025-11-16T12:00:00Z",
  "license": "MIT",
  "gateways": ["https://ipfs.io/ipfs/Qm..."],
  "pinning_services": ["personal_node"]
}
```

---

## Anti-Patterns & Failure Modes

### Failure Modes to Avoid

| Failure Mode | Detection | Mitigation |
|--------------|-----------|------------|
| **Over-abstraction drag** | Complexity metrics ↑, velocity ↓ | Now/Later/Never filter; remove unused abstractions |
| **Stealth performance tax** | Latency percentiles ↑ | Performance budgets; profiling gates |
| **Unclear ownership** | Bugs linger; features incomplete | RACI matrix; ADR assigns responsibility |
| **Cargo cult "best practices"** | Code copied without understanding | Evidence gates; "why" documentation |
| **Untestable glue** | Coverage gaps; flaky tests | Dependency injection; property testing |
| **Ethics bypass via urgency** | Safety checks skipped | Mandatory review gates; ADR for exceptions |
| **Memory loss between conversations** | Re-explaining context | ADR system; load relevant context automatically |
| **Agent coordination failure** | Contradictory outputs | RSA + symbolic validation; explicit consensus |
| **Neural-first architecture** | LLMs as truth source | Symbolic-first; formal validation mandatory |
| **Guessing instead of clarifying** | Vague specs, wrong implementations | Decision [0 hold]; ask specific questions |

### Anti-Patterns

**DO NOT**:
- Build complex systems for hypothetical future needs
- Use LLMs as truth sources (they format, they don't validate)
- Skip tests because "it's simple code"
- Add abstraction layers "just in case"
- Commit without running tests
- Push to main branch directly
- Implement without reading the spec
- Flatter the user instead of challenging assumptions
- Guess at ambiguous requirements

**DO**:
- Build the simplest thing that works today
- Validate with formal logic, assist with LLMs
- Write failing tests before implementing
- Add extension points when evidence demands it
- Run full test suite before commit
- Use feature branches with clear names
- Read and understand spec before coding
- Challenge assumptions constructively
- Ask clarifying questions when unclear

---

## How to Contribute

### For AI Assistants

When working on this codebase:

1. **Read Operating Instructions** - `ARF/FLOSSI0ULLK_Operating_Instructions_v0.4.1.md`
2. **Use Decision Framework** - Intent → Analysis → Decision → Actions
3. **Follow SDD** - Spec first, then tests, then code
4. **Check existing patterns** - Look at similar code before implementing
5. **Write tests first** - Follow TDD/SDD approach
6. **Document extensively** - Comments explain WHY, code shows HOW
7. **Validate against reality** - Consider edge cases and adversarial scenarios
8. **Apply Now/Later/Never** - Only build for validated current pain

### Common Tasks

#### Adding a new memory operation
1. Read specification from docs
2. Create ADR if major decision
3. Write test plan
4. Write failing tests
5. Add function to `ARF/conversation_memory.py`
6. Add CLI command to `ARF/cli/memory.py`
7. Update CLI README: `ARF/cli/README.md`
8. Run tests and verify

#### Adding a new validation rule
1. Define validation criteria (specification)
2. Create ADR documenting decision
3. Write test cases in `ARF/tests/test_committee_validation.py`
4. Implement in `ARF/validation/committee.py`
5. Update validation README: `ARF/validation/README.md`
6. Benchmark impact on performance

#### Adding a new Holochain entry type
1. Define in integrity zome (`lib.rs`)
2. Add validation rules (CANNOT be bypassed)
3. Add coordinator functions (create, get, query)
4. Write Rust unit tests
5. Add tryorama integration tests
6. Document in DNA README
7. Update ADR if architectural change

### Code Review Checklist

Before submitting changes:

- [ ] Specification exists and is reviewed
- [ ] ADR created/updated for major decisions
- [ ] Tests written and passing (100% of new code)
- [ ] Code follows SDD methodology
- [ ] Decision framework applied (Intent→Analysis→Decision→Actions)
- [ ] Now/Later/Never filter applied
- [ ] Comments explain WHY, not WHAT
- [ ] Descriptive variable/function names
- [ ] No magic numbers or unexplained constants
- [ ] Error handling is comprehensive
- [ ] Documentation updated
- [ ] ULLK principles maintained
- [ ] No introduction of centralization risks
- [ ] Verifiable provenance maintained
- [ ] Symbolic-first principle upheld (if applicable)
- [ ] CLI added for any new library (constitutional requirement)

---

## Quick Reference

### Essential Commands

```bash
# Setup
cd ARF && pip install -e .

# Run tests
pytest                          # All Python tests
pytest -k "memory"             # Specific tests
cargo test                      # Rust tests (in DNA dir)

# CLI usage
arf --help                     # Show all commands
arf memory transmit "..."      # Add to memory
arf swarm query "..."          # Query swarm
arf ontology validate "..."    # Validate triple

# Development
black .                         # Format Python code
ruff check .                   # Lint Python code
cargo fmt                      # Format Rust code
cargo clippy                   # Lint Rust code
```

### File Patterns

```bash
# Find Python source
find ARF -name "*.py" -not -path "*/\.*"

# Find Holochain DNAs
find . -name "Cargo.toml" | grep dnas

# Find tests
find ARF/tests -name "test_*.py"

# Find documentation
find . -name "*.md" -not -path "*/\.*"
```

### Environment Setup

**Python environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r ARF/requirements.txt
pip install -e ARF
```

**Holochain environment**:
```bash
# Install Holochain CLI
cargo install holochain_cli --locked

# Build DNA
cd ARF/dnas/rose_forest
hc dna pack workdir/dna

# Run sandbox
hc sandbox generate workdir/
hc sandbox run -p 8888 workdir/
```

---

## Troubleshooting

### Common Issues

**IPFS daemon not running**:
```bash
ipfs daemon &
# Or install: https://ipfs.io
```

**Python import errors**:
```bash
# Install in editable mode
cd ARF && pip install -e .
```

**Holochain build errors**:
```bash
cargo clean
hc dna pack workdir/dna
```

**Test failures**:
```bash
# Run with verbose output
pytest -v -s

# Run specific test
pytest tests/test_committee_validation.py::test_name -v
```

### Getting Help

1. Check documentation in relevant README files
2. Load relevant ADRs for context
3. Search existing issues on GitHub
4. Review specification documents (ADRs)
5. Examine similar code patterns in codebase
6. Consult ULLK principles for architectural guidance
7. Use Decision Framework [0 hold] if unclear

---

## Mantra

```
Simplicity now.
Seams for later.
Delete the rest.

Love, Light, Knowledge —
    verifiable, shared, and free.

The walking skeleton is alive.
The protocol is the conversation.
The system builds itself.
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-16 | Initial comprehensive CLAUDE.md creation |
| 2.0 | 2025-11-16 | Enhanced with operating instructions, decision framework, anti-patterns |

---

## License

This project uses the Compassion Clause or compatible FOSS licenses. All code must be Free/Libre Open Source Software (FLOSS) compliant. See `LICENSE` file for details.

**Compassion Clause**:
```
This software shall actively promote and measure growth in
unconditional love, light, and fractal knowledge.

Any use diminishing these values terminates this license.
```

---

**Remember**: This codebase embodies ULLK principles. Every change should enhance transparency, agency, liberation, and evolution.

**This isn't just a software project** - it's an attempt to create the conditions for intelligence itself to coordinate toward good.

Code with compassion. Build with love. Make it verifiable. 💜

---

**For questions, context, or collaboration**: Read the relevant ADRs first, then engage with the Decision Framework.
