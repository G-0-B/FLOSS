# Phase 1 execution receipts (2026-10-04)

Author evidence for the execution record at the top of
`docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md`. Not a review.

`run_green.py` runs the required green set in the worktree
`C:/~shit/FLOSS/.worktrees/room-board-v1` with the agent directory, audit
directory, room root and room log pinned under a temp directory, and writes the
output with the commit it ran on as the first line.

| File | Commit | Result |
|---|---|---|
| `base.txt` | `4aab13e` (the base, before any change) | 993 passed, 7 skipped, 1 deselected |
| `phase1.txt` | `0281a47` (after Task 6) | 1,115 passed, 7 skipped, 1 deselected |
| `head.txt` | `6e38f6f` (after the execution record) | 1,115 passed, 7 skipped, 1 deselected |

Windows, Python 3.13, this machine's installed dependencies (MCP 1.27.0). Compared
per test case from the JUnit output of the first two runs: nothing regressed,
nothing went missing, the same seven skips, 122 new cases, all passing.

Not here: a Linux run. The commit that adds this folder changes nothing outside it.
