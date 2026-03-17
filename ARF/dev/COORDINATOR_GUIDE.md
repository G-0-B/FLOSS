# FLOSSI0ULLK Parallel Development Coordinator Guide

**Version**: 1.0
**Last Updated**: 2025-11-11
**Purpose**: Orchestrate autonomous parallel Claude Code development

---

## 🎯 Overview

This guide coordinates parallel autonomous development across multiple Claude Code instances. Each phase contains tasks that can run simultaneously, with clear merge points between phases.

**Total Development Pipeline**: 3 Phases, 8 Parallel Tasks, ~2-3 weeks wall time

---

## 📊 Parallelization Strategy

```
PHASE 1: Quick Wins (Run in Parallel - No Dependencies)
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Task 1.1        │  │ Task 1.2        │  │ Task 1.3        │
│ Real Embeddings │  │ from_dict()     │  │ Composition     │
│ ~4 hours        │  │ ~3 hours        │  │ Logic ~6 hours  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                        MERGE PHASE 1
                              │
                              ▼
PHASE 2: Foundation (Sequential + Parallel)
┌─────────────────┐
│ Task 2.1        │  ← MUST COMPLETE FIRST
│ Base Ontology   │
│ ~8 hours        │
└────────┬────────┘
         │
         ├─────────────┐
         ▼             ▼
┌────────────────┐  ┌────────────────┐  ← RUN IN PARALLEL
│ Task 2.2       │  │ Task 2.3       │
│ Domain Ontology│  │ Validation     │
│ ~6 hours       │  │ Integration    │
└────────────────┘  │ ~5 hours       │
         │          └────────────────┘
         └─────────────┼
                       ▼
                 MERGE PHASE 2
                       │
                       ▼
PHASE 3: Integration (Run in Parallel - Independent)
┌─────────────────┐  ┌─────────────────┐
│ Task 3.1        │  │ Task 3.2        │
│ Vector Migration│  │ Holochain Port  │
│ ~10 hours       │  │ ~12 hours       │
└─────────────────┘  └─────────────────┘
         │                    │
         └────────────────────┘
                   ▼
             MERGE PHASE 3
                   ▼
          🎉 COMPLETE 🎉
```

---

## 🚀 Quick Start Instructions

### Step 1: Prepare Repository
```bash
cd /path/to/FLOSS
git checkout -b parallel-dev-2025-11-11
git pull origin claude/evaluate-repo-actions-011CV2uSRqRAxAe8xAAdvhPc
```

### Step 2: Launch Phase 1 (3 Parallel Claude Instances)

**Instance 1:**
```bash
claude-code
# In Claude: "Read ARF/dev/base_prompt.md and ARF/dev/tasks/phase1/task1_embeddings.md and execute the task"
```

**Instance 2:**
```bash
claude-code
# In Claude: "Read ARF/dev/base_prompt.md and ARF/dev/tasks/phase1/task2_from_dict.md and execute the task"
```

**Instance 3:**
```bash
claude-code
# In Claude: "Read ARF/dev/base_prompt.md and ARF/dev/tasks/phase1/task3_composition.md and execute the task"
```

### Step 3: Monitor Progress
Each Claude instance will:
1. Read base prompt + task prompt
2. Create feature branch: `parallel/phase1-task{N}-{session-id}`
3. Implement and test
4. Push to remote
5. Report completion

### Step 4: Merge Phase 1
```bash
# Wait for all 3 instances to complete
./ARF/dev/scripts/merge_phase.sh phase1
```

### Step 5: Repeat for Phase 2 and Phase 3

---

## 📋 Task Selection Criteria

Tasks were selected based on:
- ✅ **Autonomous Development**: Can be implemented without human decisions
- ✅ **Autonomous Evaluation**: Can be tested programmatically
- ✅ **Clear Specification**: Unambiguous requirements
- ✅ **Isolated Scope**: Minimal inter-task dependencies
- ✅ **Measurable Success**: Concrete acceptance criteria

### Tasks NOT Included (Require Human Oversight)
- ❌ Test #4: Human coherence validation
- ❌ KERI/ACDC security integration (needs security review)
- ❌ Proof-carrying code (too experimental)
- ❌ Self-modification system (needs oversight)
- ❌ Multi-AI coordination testing (needs external systems)

---

## 📦 Phase Details

### **PHASE 1: Quick Wins** (Wall Time: 6 hours)
**Dependencies**: None - all tasks are independent
**Parallelization**: 3 simultaneous instances
**Impact**: Unblocks downstream work, immediate quality improvements

| Task | File | Est. Time | Branch Pattern |
|------|------|-----------|----------------|
| 1.1 Real Embeddings | `tasks/phase1/task1_embeddings.md` | 4h | `parallel/phase1-task1-*` |
| 1.2 from_dict() | `tasks/phase1/task2_from_dict.md` | 3h | `parallel/phase1-task2-*` |
| 1.3 Composition Logic | `tasks/phase1/task3_composition.md` | 6h | `parallel/phase1-task3-*` |

**Merge Strategy**: Cherry-pick all three branches sequentially into `dev/phase1-complete`

---

### **PHASE 2: Foundation** (Wall Time: 14 hours)
**Dependencies**: Task 2.1 must complete before 2.2 and 2.3
**Parallelization**: 1 instance, then 2 simultaneous instances
**Impact**: Enables symbolic-first architecture

**Stage 1 (Sequential):**
| Task | File | Est. Time | Branch Pattern |
|------|------|-----------|----------------|
| 2.1 Base Ontology | `tasks/phase2/task1_base_ontology.md` | 8h | `parallel/phase2-task1-*` |

**Stage 2 (Parallel - after 2.1 completes):**
| Task | File | Est. Time | Branch Pattern |
|------|------|-----------|----------------|
| 2.2 Domain Ontology | `tasks/phase2/task2_domain_ontology.md` | 6h | `parallel/phase2-task2-*` |
| 2.3 Validation Integration | `tasks/phase2/task3_validation.md` | 5h | `parallel/phase2-task3-*` |

**Merge Strategy**:
1. Merge 2.1 into `dev/phase2-base`
2. Create two branches from `dev/phase2-base` for 2.2 and 2.3
3. Merge both into `dev/phase2-complete`

---

### **PHASE 3: Integration** (Wall Time: 12 hours)
**Dependencies**: Requires Phase 2 completion
**Parallelization**: 2 simultaneous instances
**Impact**: Production-ready system

| Task | File | Est. Time | Branch Pattern |
|------|------|-----------|----------------|
| 3.1 Vector Migration | `tasks/phase3/task1_migration.md` | 10h | `parallel/phase3-task1-*` |
| 3.2 Holochain Port | `tasks/phase3/task2_holochain.md` | 12h | `parallel/phase3-task2-*` |

**Merge Strategy**: Merge both branches into `dev/phase3-complete`

---

## 🔄 Merge Workflow

### Automated Merge Script
```bash
#!/bin/bash
# ARF/dev/scripts/merge_phase.sh

PHASE=$1  # phase1, phase2, phase3

case $PHASE in
  phase1)
    BRANCHES=$(git branch -r | grep "parallel/phase1-task")
    TARGET="dev/phase1-complete"
    ;;
  phase2)
    BRANCHES=$(git branch -r | grep "parallel/phase2-task")
    TARGET="dev/phase2-complete"
    ;;
  phase3)
    BRANCHES=$(git branch -r | grep "parallel/phase3-task")
    TARGET="dev/phase3-complete"
    ;;
esac

# Create target branch
git checkout -b $TARGET

# Merge each task branch
for BRANCH in $BRANCHES; do
  echo "Merging $BRANCH..."
  git merge --no-ff $BRANCH -m "Merge $(basename $BRANCH)"

  # Run tests after each merge
  ./ARF/dev/scripts/run_tests.sh

  if [ $? -ne 0 ]; then
    echo "ERROR: Tests failed after merging $BRANCH"
    exit 1
  fi
done

echo "Phase $PHASE merge complete!"
git push origin $TARGET
```

### Manual Merge Checklist
See `ARF/dev/templates/merge_checklist.md` for detailed steps.

---

## ✅ Success Criteria

### Phase 1 Complete When:
- [ ] All tests pass with real embeddings (not mocks)
- [ ] ConversationMemory can serialize/deserialize via from_dict/to_dict
- [ ] Multi-agent composition produces correct merged embeddings
- [ ] No performance regressions
- [ ] Code coverage ≥ 80% for new code

### Phase 2 Complete When:
- [ ] Base ontology deployed in Holochain integrity zome
- [ ] Invalid triples are rejected (test with deliberately bad data)
- [ ] Domain ontology infers new knowledge correctly
- [ ] Validation prevents any untyped data from entering system
- [ ] All existing tests still pass

### Phase 3 Complete When:
- [ ] ≥80% of existing vectors migrated with valid triples
- [ ] ConversationMemory ported to Holochain DNA
- [ ] DHT operations work correctly
- [ ] Cross-agent coordination tested
- [ ] Performance benchmarks met

---

## 🐛 Troubleshooting

### Issue: Merge Conflicts
**Symptom**: Git reports conflicts during merge
**Solution**:
1. Check if tasks overlapped in scope (shouldn't happen with proper planning)
2. Review conflict markers - usually in imports or test files
3. Prioritize: Phase order determines precedence (later phases win)
4. Re-run tests after manual resolution

### Issue: Tests Fail After Merge
**Symptom**: Individual branches pass, merged branch fails
**Solution**:
1. Check for integration assumptions (e.g., API changes in one task break another)
2. Run `git log --all --oneline --graph` to see merge history
3. Use `git bisect` to find breaking commit
4. Add integration tests to prevent future issues

### Issue: Claude Instance Gets Stuck
**Symptom**: Instance stops making progress
**Solution**:
1. Check if task has hidden human-decision requirement
2. Review last few messages for clarifying questions
3. If truly stuck, abort and reassess task scope
4. Update task prompt with more specific guidance

### Issue: Performance Degradation
**Symptom**: Tests pass but system is slower
**Solution**:
1. Run benchmark suite: `./ARF/dev/scripts/benchmark.sh`
2. Compare before/after metrics
3. Profile with `py-spy` (Python) or `cargo flamegraph` (Rust)
4. Identify bottleneck and optimize

---

## 📞 Communication Protocol

### Each Claude Instance Should:
1. **Start**: Log to `ARF/dev/logs/phase{N}_task{M}_start.log`
2. **Progress**: Update every 30 mins or at major milestones
3. **Completion**: Create `ARF/dev/completion/phase{N}_task{M}.md` with:
   - Summary of changes
   - Test results
   - Known issues
   - Branch name
   - Commit hash
4. **Failure**: Create `ARF/dev/issues/phase{N}_task{M}_blocked.md` with:
   - What was attempted
   - Why it failed
   - Suggested next steps

### Coordinator Should:
1. Monitor completion files
2. Trigger merges when phase completes
3. Resolve blockers
4. Update this guide with lessons learned

---

## 📈 Progress Tracking

### Current Status Dashboard
```markdown
## PHASE 1: Quick Wins
- [ ] Task 1.1: Real Embeddings (Status: Not Started)
- [ ] Task 1.2: from_dict() (Status: Not Started)
- [ ] Task 1.3: Composition Logic (Status: Not Started)

## PHASE 2: Foundation
- [ ] Task 2.1: Base Ontology (Status: Blocked - Waiting for Phase 1)
- [ ] Task 2.2: Domain Ontology (Status: Blocked - Waiting for 2.1)
- [ ] Task 2.3: Validation Integration (Status: Blocked - Waiting for 2.1)

## PHASE 3: Integration
- [ ] Task 3.1: Vector Migration (Status: Blocked - Waiting for Phase 2)
- [ ] Task 3.2: Holochain Port (Status: Blocked - Waiting for Phase 2)

## Overall Progress: 0/8 tasks complete (0%)
```

Update this section as tasks complete.

---

## 🎓 Lessons Learned (Update After Each Phase)

### Phase 1 Retrospective
- What went well:
- What could improve:
- Adjustments for Phase 2:

### Phase 2 Retrospective
- What went well:
- What could improve:
- Adjustments for Phase 3:

### Phase 3 Retrospective
- What went well:
- What could improve:
- Future parallelization ideas:

---

## 🔗 Related Documentation

- `ARF/dev/base_prompt.md` - Base instructions for all Claude instances
- `ARF/dev/tasks/` - Individual task specifications
- `ARF/dev/templates/` - Reusable templates
- `ARF/INTEGRATION_MAP.md` - Overall project roadmap
- `ARF/ADR-0-recognition-protocol.md` - Core architectural decisions

---

## 📝 Notes for Future Parallelization

Tasks identified but deferred for later:
1. **Performance Optimization Suite** (Phase 4)
   - Infinity Bridge correlation optimization
   - Desktop Pony RSA parameter tuning
   - Can run as 2 parallel instances

2. **Documentation & Examples** (Phase 4)
   - API documentation generation
   - Tutorial creation
   - Example notebooks
   - Can run as 3 parallel instances

3. **Advanced Features** (Phase 5 - needs more design)
   - LLM committee validation
   - Advanced query parsing
   - Real-time collaboration features

---

**Next Steps for Coordinator:**
1. Review and approve this guide
2. Create base_prompt.md
3. Create all task prompts
4. Set up monitoring infrastructure
5. Launch Phase 1

**Estimated Total Wall Time**: 2-3 weeks (vs 6-8 weeks sequential)

🌹 Parallel development for faster flourishing 🌹
