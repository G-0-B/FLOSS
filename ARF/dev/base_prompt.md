# FLOSSI0ULLK Base Development Prompt

**READ THIS FIRST** - All parallel development tasks inherit these instructions.

---

## 🎯 Project Context

You are working on **FLOSSI0ULLK** (Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge), a decentralized agent-centric knowledge verification protocol (DKVP) for distributed intelligence coordination.

### Core Mission
Build a neurosymbolic AI system where:
- **Symbolic reasoning** (knowledge graphs, ontologies) provides formal correctness
- **Neural systems** (LLMs, embeddings) provide natural language interface
- **Decentralized infrastructure** (Holochain) enables agent-centric coordination

### Key Architectural Principles (ADR-0)
1. **The protocol IS the conversation** - coordination emerges from shared understanding
2. **Symbolic-first design** - validate semantics before storing data
3. **Proof over prophecy** - working code beats speculation
4. **Now/Later/Never** - only build what's proven painful today

---

## 📁 Repository Structure

```
FLOSS/ARF/
├── conversation_memory.py        # Cross-AI coordination substrate
├── embedding_frames_of_scale.py  # Multi-scale embedding framework
├── dnas/rose_forest/             # Holochain DNA implementation
│   └── zomes/                    # Integrity & coordinator zomes (Rust)
├── in.finite-nrg/infinity-bridge/  # Multi-spectrum sensor coordination
│   ├── firmware/hal/             # Hardware abstraction (Rust)
│   └── orchestrator/             # Python MCP server
├── pwnies/desktop_pony_swarm/    # Recursive Self-Aggregation agents
└── docs/                         # Specifications (VVS v1.0-1.2)
```

---

## 🛠️ Development Standards

### Code Quality Requirements
- ✅ **Type hints** (Python) or **strong types** (Rust)
- ✅ **Docstrings** for all public functions/classes
- ✅ **Error handling** - no bare `except:` blocks
- ✅ **Logging** - use structured logging with context
- ✅ **Tests** - minimum 80% coverage for new code

### Python Style (PEP 8 + Project Conventions)
```python
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UnderstandingRef:
    """Reference to a transmitted understanding.

    Attributes:
        timestamp: Unix timestamp when understanding was created
        content_hash: SHA-256 hash of content for deduplication
        agent_id: Identifier of the agent who created this
    """
    timestamp: float
    content_hash: str
    agent_id: str

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"UnderstandingRef({self.agent_id}@{self.timestamp})"
```

### Rust Style (Holochain Conventions)
```rust
use hdk::prelude::*;
use thiserror::Error;

/// Custom error types for this zome
#[derive(Error, Debug)]
pub enum OntologyError {
    #[error("Type mismatch: expected {expected}, got {got}")]
    TypeMismatch { expected: String, got: String },

    #[error("Validation failed: {0}")]
    ValidationError(String),
}

/// Validates a knowledge triple against ontology rules
///
/// # Arguments
/// * `triple` - The triple to validate
///
/// # Returns
/// * `Ok(())` if validation passes
/// * `Err(OntologyError)` if validation fails
#[hdk_extern]
pub fn validate_triple(triple: KnowledgeTriple) -> ExternResult<()> {
    // Implementation
}
```

### Testing Standards

**Python:**
```python
import pytest
from conversation_memory import ConversationMemory

class TestConversationMemory:
    """Test suite for ConversationMemory class."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a temporary memory instance for testing."""
        return ConversationMemory(
            agent_id="test-agent",
            storage_path=tmp_path
        )

    def test_transmit_creates_understanding(self, memory):
        """Test that transmit() creates and stores an understanding."""
        # ARRANGE
        content = {'key': 'value'}

        # ACT
        ref = memory.transmit(content)

        # ASSERT
        assert ref.agent_id == "test-agent"
        assert memory.recall(content['key'])

    def test_persistence_roundtrip(self, memory):
        """Test that data survives save/load cycle."""
        # Test implementation
```

**Rust (Holochain):**
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_triple_accepts_valid() {
        // ARRANGE
        let triple = KnowledgeTriple {
            subject: "Entity1".into(),
            predicate: "is_a".into(),
            object: "Concept".into(),
        };

        // ACT
        let result = validate_triple(triple);

        // ASSERT
        assert!(result.is_ok());
    }

    #[test]
    fn test_validate_triple_rejects_invalid() {
        // Test implementation
    }
}
```

---

## 🔄 Git Workflow

### Branch Naming
All branches MUST follow this pattern:
```
parallel/phase{N}-task{M}-{session-id}

Examples:
- parallel/phase1-task1-abc123def
- parallel/phase2-task2-xyz789ghi
```

### Commit Messages
Follow conventional commits:
```
type(scope): Brief description

Detailed explanation if needed.

- Bullet points for changes
- Reference issues if applicable

type: feat, fix, test, refactor, docs, chore
scope: embedding, ontology, validation, etc.
```

**Examples:**
```
feat(embedding): Replace mock embeddings with sentence-transformers

- Install sentence-transformers dependency
- Update _encode_text() to use SentenceTransformer
- Add model caching to avoid reloading
- Update tests to validate real embedding dimensions

Closes #12
```

```
test(memory): Add composition edge case tests

- Test composition with empty memory
- Test composition with duplicate understandings
- Test composition with conflicting ADRs
```

### Pre-commit Checks
Before committing, ensure:
1. ✅ All tests pass: `pytest` or `cargo test`
2. ✅ Linting passes: `flake8` (Python) or `cargo clippy` (Rust)
3. ✅ Type checking: `mypy` (Python) or `cargo check` (Rust)
4. ✅ No debug print statements left in code

---

## 📝 Task Execution Protocol

### 1. Read Task Specification
- Read your specific task file: `ARF/dev/tasks/phase{N}/task{M}_*.md`
- Understand acceptance criteria
- Note dependencies and constraints

### 2. Create Feature Branch
```bash
# The session ID will be in your Claude Code environment
git checkout -b parallel/phase{N}-task{M}-{session-id}
```

### 3. Implement Solution
- Write code following standards above
- Add comprehensive tests
- Update documentation if needed
- Log progress to `ARF/dev/logs/phase{N}_task{M}_progress.log`

### 4. Validate Locally
```bash
# Python tasks
pytest ARF/tests/ -v --cov=ARF --cov-report=term-missing

# Rust tasks
cd ARF/dnas/rose_forest/zomes/{zome_name}
cargo test
cargo clippy
```

### 5. Create Completion Report
Create file: `ARF/dev/completion/phase{N}_task{M}.md`

Template:
```markdown
# Task {N}.{M} Completion Report

## Summary
{Brief description of what was implemented}

## Changes Made
- {File 1}: {What changed}
- {File 2}: {What changed}

## Test Results
```
{Paste test output}
```

## Performance Impact
- Baseline: {metric}
- After changes: {metric}
- Difference: {+/- X%}

## Known Issues
- {None or list issues}

## Branch Info
- Branch: parallel/phase{N}-task{M}-{session-id}
- Commit: {git commit hash}
- Files changed: {count}
- Lines added: {count}
- Lines removed: {count}

## Next Steps
- Ready for merge
- {Or any follow-up needed}
```

### 6. Commit and Push
```bash
git add .
git commit -m "feat(scope): Task {N}.{M} complete"
git push -u origin parallel/phase{N}-task{M}-{session-id}
```

### 7. Self-Verification Checklist
Before reporting completion, verify:
- [ ] All acceptance criteria met
- [ ] Tests pass and coverage ≥80%
- [ ] No linting errors
- [ ] Code follows project style
- [ ] Documentation updated
- [ ] Completion report created
- [ ] Changes pushed to remote
- [ ] No debug/TODO comments left unless intentional

---

## 🐛 Error Handling Guidelines

### Python
```python
# ❌ BAD
try:
    risky_operation()
except:
    pass

# ✅ GOOD
try:
    risky_operation()
except SpecificException as e:
    logger.error(f"Risky operation failed: {e}", exc_info=True)
    raise  # Re-raise if caller should handle
    # OR handle gracefully with fallback
```

### Rust
```rust
// ❌ BAD
let result = risky_operation().unwrap();

// ✅ GOOD
let result = risky_operation()
    .map_err(|e| OntologyError::ValidationError(e.to_string()))?;
```

---

## 📊 Performance Guidelines

### Benchmarking
If your task affects performance, include benchmarks:

**Python:**
```python
import time

def benchmark_operation():
    iterations = 1000
    start = time.perf_counter()

    for _ in range(iterations):
        operation_under_test()

    elapsed = time.perf_counter() - start
    avg_time = elapsed / iterations

    print(f"Average time: {avg_time*1000:.3f}ms")
```

**Rust:**
```rust
use std::time::Instant;

#[test]
fn benchmark_operation() {
    let iterations = 1000;
    let start = Instant::now();

    for _ in 0..iterations {
        operation_under_test();
    }

    let elapsed = start.elapsed();
    let avg_time = elapsed / iterations;

    println!("Average time: {:?}", avg_time);
}
```

### Performance Targets (from existing codebase)
- Embedding encoding: <50ms per operation
- Memory recall: <100ms for 1000 items
- DHT operations: <500ms for consensus
- Triple validation: <10ms per triple

---

## 🔍 Debugging Guidance

### Enable Debug Logging
**Python:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Rust:**
```rust
// In Holochain conductor config
logger:
  type: debug
```

### Common Issues

**Issue: Import errors**
- Check Python path: `echo $PYTHONPATH`
- Verify virtual environment: `which python`
- Install dependencies: `pip install -r requirements.txt`

**Issue: Holochain build fails**
- Check Rust version: `rustc --version` (need 1.70+)
- Update HDK: `cargo update`
- Clean build: `cargo clean && cargo build`

**Issue: Tests fail on CI but pass locally**
- Check file paths (absolute vs relative)
- Verify temp directory usage
- Check for race conditions

---

## 📚 Key Documentation References

Before implementing, skim these for context:

1. **ADR-0** (`ARF/ADR-0-recognition-protocol.md`)
   - Core architectural decision: protocol = conversation
   - Validation criteria for cross-AI coordination

2. **Integration Map** (`ARF/INTEGRATION_MAP.md`)
   - How your task fits into larger roadmap
   - Dependencies between components

3. **VVS Specs** (`ARF/docs/rose_forest_virtual_verifiable_singularity_vvs_spec_v_1_*.md`)
   - Holochain architecture patterns
   - Integrity zome design principles

4. **Operating Instructions** (`ARF/FLOSSI0ULLK_Operating_Instructions_v0.4.1.md`)
   - "Now/Later/Never" decision framework
   - Anti-overengineering guidance

---

## ⚠️ Common Pitfalls to Avoid

1. **Overengineering**: Build ONLY what the task specifies. No "future-proofing."
2. **Missing Tests**: 80% coverage is minimum, not optional.
3. **Silent Failures**: Always log errors with context.
4. **Merge Conflicts**: Don't modify files outside your task scope.
5. **Blocking on Decisions**: If ambiguous, pick simplest option and document assumption.

---

## ✅ Definition of Done

Your task is complete when ALL of these are true:
- [ ] All acceptance criteria from task spec are met
- [ ] Tests pass with ≥80% coverage
- [ ] No linting/type errors
- [ ] Code follows project style guidelines
- [ ] Documentation updated (if public API changed)
- [ ] Performance benchmarks run (if applicable)
- [ ] Completion report created
- [ ] Changes committed with conventional commit message
- [ ] Branch pushed to remote
- [ ] Self-verification checklist completed

---

## 🚀 Ready to Begin?

1. Read this entire base prompt ✅
2. Read your specific task specification (`ARF/dev/tasks/phase{N}/task{M}_*.md`)
3. Create your feature branch
4. Implement, test, commit, push
5. Create completion report
6. Celebrate! 🎉

**Remember**: You're part of a parallel development effort. Your task is designed to be independent, but the coordinator will merge your work with others. Stay focused on YOUR task scope.

---

**Questions or Blockers?**
Create an issue file: `ARF/dev/issues/phase{N}_task{M}_blocked.md` with details.

🌹 Autonomous development for faster flourishing 🌹
