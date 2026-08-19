---
id: feedback-parallel-agent-discipline
type: feedback
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: feedback_parallel_agent_discipline.md
title: Parallel-agent discipline — git as sync point, verify at commit boundaries
legacy_description: When another agent (Gemini/OpenCode) is working the same repo
  in parallel, use git as the authoritative sync point and verify at sampled boundaries
  not blindly
origin_session_id: 7a8fdf1c-cf5f-4d01-a344-82a0dec070b6
---

Multiple agents share this workspace (Claude Code, Gemini CLI, OpenCode). Concurrent work on the same git tree is the default, not the exception.

**Rules:**
1. **Git is the sync point.** Before any edit, run `git log -1` + `git status --short` to detect the other agent's recent activity. Don't rely on your own in-context recall of "what the tree looks like" — it can be stale by minutes.
2. **Trust-but-verify at commit boundaries.** When resuming after a parallel agent's work, verify the *claims* of its commit messages against the actual files. Don't re-read everything (that's ceremony and wastes context) — sample the load-bearing pieces: ADRs, entry points, anything the user will rely on.
3. **File-size check is the cheapest truth-gate.** Gemini once committed a 0-byte file while claiming the content was "finalized" (Python one-liner `open(w).write(open(r).read())` truncation trap). One `ls -la` on the target file would have caught it. Do this for any agent-generated artifact.
4. **Atomic commits across agents.** Don't mix governance/ADR changes with formatting/cleanup sweeps in the same commit — the user flagged this specifically. If another agent did mix them, read the diff stat and read_file the important hunks before treating the commit as canon.
5. **Shell awareness.** I'm in bash on Windows; Gemini was hitting PowerShell. PS rejects `&&` as a statement separator. If I'm invoking PS explicitly, use `;`. If I'm in bash (my default), `&&` is fine.

**Why:** The user called out that lost work in the unstable environment was partly environmental (mixed shells, compactions, auto-accept edits, concurrent agents) but mostly *workflow discipline failures*. Tighter execution constraints fix the workflow half; git as sync point fixes the concurrency half. User's own words: "tighter execution constraints, not replacing your machine."

**How to apply:** Run the git check at the start of any non-trivial turn after a compaction or after the user drops a "what another agent did" context injection. Sample verify load-bearing artifacts. Don't re-verify everything — let git's commit hashes do the state-tracking for you.
