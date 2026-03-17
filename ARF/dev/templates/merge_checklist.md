# Phase Merge Checklist

Use this checklist when merging completed tasks from a phase.

---

## Pre-Merge Verification

### For Each Task in Phase:
- [ ] Task completion report exists (`ARF/dev/completion/phase{N}_task{M}.md`)
- [ ] Branch exists and is pushed to remote
- [ ] All tests reported as passing in completion report
- [ ] Code coverage ≥80% confirmed
- [ ] No known blockers or issues

### Example Verification:
```bash
# Check all Phase 1 tasks
ls ARF/dev/completion/phase1_task*.md
# Should show: task1.md, task2.md, task3.md

# Check branches exist
git branch -r | grep parallel/phase1
# Should show all task branches

# Review completion reports
for f in ARF/dev/completion/phase1_task*.md; do
    echo "=== $f ==="
    grep -A 5 "Test Results" "$f"
done
```

---

## Merge Process

### Step 1: Create Merge Target Branch
```bash
# Example for Phase 1
git checkout claude/evaluate-repo-actions-011CV2uSRqRAxAe8xAAdvhPc
git pull origin claude/evaluate-repo-actions-011CV2uSRqRAxAe8xAAdvhPc
git checkout -b dev/phase{N}-complete
```

### Step 2: Merge Tasks Sequentially

**Important**: Merge one at a time, test after each merge!

```bash
# Get list of task branches
git branch -r | grep "parallel/phase{N}-task" > /tmp/branches.txt

# For each branch:
for branch in $(cat /tmp/branches.txt); do
    echo "Merging $branch..."

    # Merge with no-ff to preserve history
    git merge --no-ff $branch -m "Merge $(basename $branch)"

    # Run tests
    echo "Running tests after merge..."
    pytest ARF/tests/ -v || {
        echo "ERROR: Tests failed after merging $branch"
        echo "Fix conflicts and re-run tests before continuing"
        exit 1
    }

    # Check for merge artifacts
    git diff --check || {
        echo "WARNING: Whitespace issues detected"
    }
done
```

### Step 3: Integration Testing

After all tasks merged:

```bash
# Run full test suite
pytest ARF/tests/ -v --cov=ARF --cov-report=term-missing

# Check coverage
# Should be ≥80% for all modified files

# Run integration tests
pytest ARF/tests/integration/ -v

# Check for common issues
grep -r "TODO" ARF/*.py  # Should be minimal
grep -r "import pdb" ARF/*.py  # Should be none
grep -r "print(" ARF/*.py  # Should be minimal (use logging)
```

### Step 4: Manual Verification

Test key functionality manually:

**For Phase 1 (Embeddings + Composition):**
```python
from conversation_memory import ConversationMemory
import numpy as np

# Test real embeddings
m = ConversationMemory(agent_id="test")
ref = m.transmit({"content": "Test understanding"})
assert ref is not None

# Test from_dict
state = m.embeddings.to_dict()
from embedding_frames_of_scale import MultiScaleEmbedding
restored = MultiScaleEmbedding.from_dict(state)
assert len(restored) == len(m.embeddings)

# Test composition
m2 = ConversationMemory(agent_id="test2")
m2.transmit({"content": "Another understanding"})
export = m2.export_for_composition()
m.import_and_compose(export)
assert len(m.understandings) == 2
```

**For Phase 2 (Ontology):**
```bash
cd ARF/dnas/rose_forest/zomes/ontology_integrity
cargo test
cargo clippy
```

**For Phase 3 (Migration + Holochain):**
```bash
python ARF/scripts/migrate_to_symbolic.py
cat ARF/dev/reports/migration_report.md
# Verify ≥80% success rate
```

---

## Conflict Resolution

### Common Conflicts:

**1. Import Conflicts**
- Multiple tasks added imports
- **Resolution**: Merge all imports, remove duplicates, sort

**2. Test File Conflicts**
- Multiple tasks added tests to same file
- **Resolution**: Keep all tests, ensure unique names

**3. Documentation Conflicts**
- README or docstring updates
- **Resolution**: Merge content logically, prefer more detail

**4. Dependency Conflicts**
- requirements.txt or Cargo.toml changes
- **Resolution**: Include all dependencies, update to latest compatible versions

### Conflict Resolution Process:
```bash
# When merge conflict occurs:
git status  # See conflicted files

# For each file:
# 1. Open in editor
# 2. Resolve conflicts (remove <<<< ==== >>>> markers)
# 3. Test that file works
# 4. Mark as resolved
git add <file>

# Run tests before continuing
pytest ARF/tests/ -v

# Complete merge
git commit
```

---

## Post-Merge Verification

### Checklist:
- [ ] All tests pass
- [ ] No merge conflict markers in code
- [ ] No broken imports
- [ ] No duplicate functions/classes
- [ ] Code coverage ≥80%
- [ ] No linting errors
- [ ] Documentation up to date
- [ ] CHANGELOG updated (if exists)

### Verification Commands:
```bash
# Search for conflict markers (should return nothing)
grep -r "<<<<<<" ARF/
grep -r ">>>>>>" ARF/

# Run linters
flake8 ARF/ --max-line-length=100
cd ARF/dnas/rose_forest/zomes && cargo clippy

# Check imports work
python -c "from conversation_memory import ConversationMemory; print('OK')"
python -c "from embedding_frames_of_scale import MultiScaleEmbedding; print('OK')"

# Run full test suite one more time
pytest ARF/tests/ -v --cov=ARF
```

---

## Create Merge Summary

Document what was merged:

```bash
# Create summary
cat > ARF/dev/merge_summary_phase{N}.md <<EOF
# Phase {N} Merge Summary

**Date**: $(date)
**Merged By**: [Name]
**Target Branch**: dev/phase{N}-complete

## Tasks Merged
1. Task {N}.1: [Name] - Commit [hash]
2. Task {N}.2: [Name] - Commit [hash]
3. Task {N}.3: [Name] - Commit [hash]

## Test Results
- All tests passing: ✅
- Coverage: XX%
- No linting errors: ✅

## Known Issues
- [List any issues or TODOs]

## Next Steps
- [What comes after this phase]
EOF
```

---

## Push Merged Branch

```bash
# Final check
git log --oneline --graph -20

# Push to remote
git push -u origin dev/phase{N}-complete

# Tag the merge
git tag -a "phase{N}-complete" -m "Phase {N} complete: [summary]"
git push origin "phase{N}-complete"
```

---

## Rollback Plan

If something goes wrong:

```bash
# Find commit before merge started
git log --oneline

# Reset to that commit
git reset --hard <commit-before-merge>

# Or use reflog
git reflog
git reset --hard HEAD@{N}

# Fix issues and try again
```

---

## Success Criteria

Phase merge is successful when:
- ✅ All task branches merged cleanly
- ✅ All tests pass
- ✅ Coverage ≥80%
- ✅ No regressions in functionality
- ✅ Integration tests pass
- ✅ Manual verification complete
- ✅ Merge summary documented
- ✅ Branch pushed to remote

---

## Notes

- **Take your time** - rushing leads to mistakes
- **Test after each merge** - easier to fix issues early
- **Document issues** - help future merges
- **Ask for help** - if stuck, create an issue

🌹 Careful merging for robust integration 🌹
