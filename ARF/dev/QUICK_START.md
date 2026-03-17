# Quick Start: Parallel Claude Development

**TL;DR**: How to launch parallel autonomous Claude Code instances for FLOSS development.

---

## 🎯 Goal

Run 3-8 Claude Code instances in parallel to complete development tasks autonomously, then merge results.

---

## 📋 Prerequisites

- [ ] Claude Code CLI installed
- [ ] Git repository cloned: `/home/user/FLOSS`
- [ ] Branch created: `claude/evaluate-repo-actions-011CV2uSRqRAxAe8xAAdvhPc`
- [ ] All documentation in `ARF/dev/` directory reviewed

---

## 🚀 Launch Phase 1 (Example)

### Terminal 1: Task 1.1 (Real Embeddings)
```bash
cd /home/user/FLOSS
claude-code
```

In Claude Code prompt:
```
Read ARF/dev/base_prompt.md and ARF/dev/tasks/phase1/task1_embeddings.md and execute the task autonomously. When complete, create the completion report and push your branch.
```

### Terminal 2: Task 1.2 (from_dict)
```bash
cd /home/user/FLOSS
claude-code
```

In Claude Code prompt:
```
Read ARF/dev/base_prompt.md and ARF/dev/tasks/phase1/task2_from_dict.md and execute the task autonomously. When complete, create the completion report and push your branch.
```

### Terminal 3: Task 1.3 (Composition)
```bash
cd /home/user/FLOSS
claude-code
```

In Claude Code prompt:
```
Read ARF/dev/base_prompt.md and ARF/dev/tasks/phase1/task3_composition.md and execute the task autonomously. When complete, create the completion report and push your branch.
```

---

## 📊 Monitor Progress

Watch for completion reports:
```bash
watch -n 30 'ls -lt ARF/dev/completion/phase1_task*.md 2>/dev/null | head -10'
```

Check branch status:
```bash
git branch -r | grep parallel/phase1
```

View logs:
```bash
tail -f ARF/dev/logs/phase1_task*.log
```

---

## ✅ When All Tasks Complete

Run merge script:
```bash
./ARF/dev/scripts/merge_phase.sh phase1
```

Or manual merge following: `ARF/dev/templates/merge_checklist.md`

---

## 🔄 Repeat for Phase 2 and Phase 3

**Phase 2**: Task 2.1 first, then 2.2 and 2.3 in parallel
**Phase 3**: Tasks 3.1 and 3.2 in parallel

---

## 🆘 Troubleshooting

### Issue: Claude instance gets stuck
- Check last few messages in that terminal
- Review task specification for ambiguity
- Kill and restart with more specific guidance

### Issue: Tests failing
- Check logs in `ARF/dev/logs/`
- Review completion report for error details
- May need manual intervention

### Issue: Merge conflicts
- Follow `ARF/dev/templates/merge_checklist.md`
- Resolve conflicts manually
- Re-run tests after resolution

---

## 📚 Full Documentation

- **Coordinator Guide**: `ARF/dev/COORDINATOR_GUIDE.md`
- **Base Prompt**: `ARF/dev/base_prompt.md`
- **Tasks**: `ARF/dev/tasks/phase{N}/task{M}_*.md`
- **Merge Checklist**: `ARF/dev/templates/merge_checklist.md`

---

## ⚡ Pro Tips

1. **Use tmux** for managing multiple terminals
2. **Create shell aliases** for common commands
3. **Monitor resource usage** (Claude instances use CPU)
4. **Review completion reports** before merging
5. **Keep COORDINATOR_GUIDE.md** open for reference

---

**Estimated Time Savings**: 2-3 weeks (parallel) vs 6-8 weeks (sequential)

🌹 Happy parallel developing! 🌹
