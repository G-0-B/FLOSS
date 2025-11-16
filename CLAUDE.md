# CLAUDE.md - AI Assistant Guide to FLOSS Repository

**Last Updated**: 2025-11-16
**Repository**: FLOSS (Free Libre Open Source Singularity)
**Purpose**: Guide for AI assistants working with the ARF FLOSSIOULLK ecosystem

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Codebase Structure](#codebase-structure)
3. [Core Principles & Philosophy](#core-principles--philosophy)
4. [Development Workflows](#development-workflows)
5. [Key Technologies & Dependencies](#key-technologies--dependencies)
6. [Testing & Validation](#testing--validation)
7. [Common Patterns & Conventions](#common-patterns--conventions)
8. [Important Files & Locations](#important-files--locations)
9. [Git & CI/CD Practices](#git--cicd-practices)
10. [How to Contribute](#how-to-contribute)

---

## Repository Overview

### What is FLOSS?

FLOSS (Free Libre Open Source Singularity) is the ARF FLOSSIOULLK ecosystem - an iterative development architecture for the **Decentralized Knowledge Verification Protocol (DKVP)**. It's an agent-centric, verifiable knowledge system embodying the core principles of Unconditional Love, Light, and Knowledge (ULLK).

### Primary Applications

- **Scientific Discovery Acceleration**: Verifiable knowledge graphs and federated reasoning
- **Ethical AI Alignment**: Policy-as-code and transparent AI behavior tracking
- **Cognitive Debt Reduction**: Tools for researchers, collaborative groups, and AI developers

### Key Components

1. **ARF (Agent Runtime Framework)**: Python-based CLI and libraries for agent operations
2. **Holochain DNAs**: Distributed data integrity for knowledge verification
3. **Infinity Bridge**: Cross-substrate coordination layer
4. **Pwnies (Desktop Pony Swarm)**: Multi-agent swarm intelligence system
5. **Validation Framework**: LLM committee-based knowledge validation

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
│   │       │   ├── swarm.py    # Main swarm orchestrator
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
│   │   └── templates/          # Code templates
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

1. **Unconditional Love**: Compassionate design, cognitive debt healing
2. **Light**: Transparency, verifiable provenance, auditability
3. **Knowledge**: Collective intelligence, federated reasoning, truth-seeking

### Architectural Foundations

#### 1. Agent-Centricity
- **Identity, not servers** is the organizing principle
- Every participant (human and AI) has sovereign identity
- Composable capabilities and verifiable actions

#### 2. Specification-Driven Development (SDD)
From `INSTRUCTIONS_FOR_CODE.md`:
- **Write specification FIRST**
- Get it reviewed
- Write test plan based on specification
- Write tests based on test plan
- Correct specification based on errors
- Write documentation
- **THEN** implement the software

#### 3. Verifiable Provenance (NormKernel)
- All actions are traceable and auditable
- Cryptographic integrity (SHA256 + BLAKE3)
- Immutable history via Holochain

#### 4. Federated Reasoning
- Collaborative knowledge synthesis
- Provenance tracking across diverse sources
- LLM committee validation (≥3/5 consensus)

#### 5. Distributed Compute (AGI@Home)
- Democratized AI development
- Pooled resources via WASM + TEEs
- Reduces centralization risks

---

## Development Workflows

### Specification-Driven Development Process

**CRITICAL**: Always follow this order (from `INSTRUCTIONS_FOR_CODE.md`):

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

#### Testing
- Test at multiple layers: unit, integration, system, reality validation
- Reality validation includes:
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
- Integrity zomes: Entry validation, cryptographic rules
- Coordinator zomes: Business logic, queries, links
- Testing with Tryorama framework

**Key Holochain Concepts**:
- Entry types: FileArtifact, PinningProof, etc.
- Validation rules: FOSS licenses, CID format, hash verification
- Links: Path-based indexing for queries
- Agent-centric: Data lives on agent's source chain

### Infrastructure

- **IPFS**: Content-addressed storage for large files
- **Git**: Version control (with pointer files for IPFS content)
- **GitHub Actions**: CI/CD workflows
- **WebAssembly (WASM)**: Portable compute
- **Trusted Execution Environments (TEEs)**: Secure compute

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

**Usage**:
```python
from validation import TripleValidationCommittee

committee = TripleValidationCommittee(use_mock=True)
triple = ("GPT-4", "is_a", "LLM")
context = "GPT-4 is a large language model."
result = await committee.validate(triple, context)

print(f"Accepted: {result.accepted}")
print(f"Confidence: {result.confidence:.2f}")
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

### Holochain Entry Patterns

**Standard Entry Type**:
```rust
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct FileArtifact {
    pub filename: String,
    pub ipfs_cid: String,
    pub sha256: String,
    pub blake3: String,
    pub license: String,
    pub uploader: AgentPubKey,
    pub uploaded_at: Timestamp,
}
```

**Validation Pattern**:
```rust
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store_entry) => {
            // Validation logic here
            // Return Ok(ValidateCallbackResult::Valid) or Invalid
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
| `Week-1-Quick-Start-Guide.md` | IPFS integration tutorial | IPFS work |
| `ADR-N-IPFS-Integration-VVS.md` | IPFS architecture decision | IPFS architecture |
| `FLOSSIOULLK-Alignment-Verification.md` | Compliance verification | Ensuring ULLK alignment |
| `Fractal-Coordination-Patterns.md` | Design patterns | Scalable architecture |

### Key Source Files

| File | Purpose | Lines | Key Classes/Functions |
|------|---------|-------|----------------------|
| `ARF/conversation_memory.py` | Memory persistence | ~800 | ConversationMemory |
| `ARF/validation/committee.py` | LLM committee validation | ~300 | TripleValidationCommittee |
| `ARF/pwnies/desktop_pony_swarm/core/swarm.py` | Swarm orchestration | ~400 | DesktopPonySwarm |
| `ARF/cli/main.py` | CLI entry point | ~150 | cli_main |

---

## Git & CI/CD Practices

### Branch Strategy

**Working on features**:
- Develop on feature branches: `claude/claude-md-<session-id>`
- NEVER push to main directly
- CRITICAL: Branch must start with 'claude/' and end with matching session ID

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
Add IPFS integration with VVS compliance

Implements cryptographic verification and budget accounting
to prevent spam and ensure data integrity.
EOF
)"
```

**Pre-commit validation**:
- Validate IPFS pointer files (JSON format, required fields, valid licenses)
- Check for secrets (.env, credentials.json)
- Run linters (black, ruff for Python)

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

**Git ignore patterns**:
```
# Ignore binaries
large_files/*.bin
large_files/*.h5
large_files/*.safetensors

# Track pointers
!large_files/*.ipfs
```

---

## How to Contribute

### For AI Assistants

When working on this codebase:

1. **Read INSTRUCTIONS_FOR_CODE.md first** - Follow SDD methodology
2. **Understand ULLK principles** - Ensure changes align with core values
3. **Check existing patterns** - Look at similar code before implementing
4. **Write tests first** - Follow TDD/SDD approach
5. **Document extensively** - Comments explain WHY, code shows HOW
6. **Validate against reality** - Consider edge cases and adversarial scenarios

### Common Tasks

#### Adding a new memory operation
1. Read specification from docs
2. Add function to `ARF/conversation_memory.py`
3. Add CLI command to `ARF/cli/memory.py`
4. Write tests in `ARF/tests/test_conversation_memory.py`
5. Update CLI README: `ARF/cli/README.md`

#### Adding a new validation rule
1. Define validation criteria (specification)
2. Implement in `ARF/validation/committee.py`
3. Add test cases in `ARF/tests/test_committee_validation.py`
4. Update validation README: `ARF/validation/README.md`

#### Adding a new Holochain entry type
1. Define in integrity zome (`lib.rs`)
2. Add validation rules
3. Add coordinator functions (create, get, query)
4. Write Rust unit tests
5. Add tryorama integration tests
6. Document in DNA README

### Code Review Checklist

Before submitting changes:

- [ ] Specification exists and is reviewed
- [ ] Tests written and passing
- [ ] Code follows SDD methodology
- [ ] Comments explain WHY, not WHAT
- [ ] Descriptive variable/function names
- [ ] No magic numbers or unexplained constants
- [ ] Error handling is comprehensive
- [ ] Documentation updated
- [ ] ULLK principles maintained
- [ ] No introduction of centralization risks
- [ ] Verifiable provenance maintained

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
2. Search existing issues on GitHub
3. Review specification documents (ADRs)
4. Examine similar code patterns in codebase
5. Consult ULLK principles for architectural guidance

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-16 | Initial comprehensive CLAUDE.md creation |

---

## License

This project uses the Compassion Clause or compatible FOSS licenses. All code must be Free/Libre Open Source Software (FLOSS) compliant. See `LICENSE` file for details.

---

**Remember**: This codebase embodies ULLK principles. Every change should enhance transparency, agency, liberation, and evolution. Code with compassion. Build with love. 💜
