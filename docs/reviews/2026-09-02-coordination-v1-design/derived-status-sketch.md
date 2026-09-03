# Derived Workspace Status — Single-Screen Sketch (replaces Work Board §0)

> Command: `hermes status` (or `floss status --derived`) — one screen, no board file, no manual edits.
> Data sources only; nothing is typed by a human. If `git` knows it, this shows it.

## Why it cannot go stale

Manual Work Board §0 is a typed snapshot: it drifts the instant a branch moves, a worktree is added/removed, or a PR merges. The derived view has **zero stored state** — every section is computed at invocation from `git worktree list --porcelain`, `git for-each-ref`, `git merge-base`/`rev-list`, `gh pr list`, and `git log -S`. There is nothing to update, no file to forget. Staleness is structurally impossible; the worst case is a slow `gh` call (cached 60s, flagged `[cached]`).

---

## Example output (realistic — FLOSS repo, 2026-09-02 snapshot, 20 worktrees)

```
FLOSSI0ULLK derived status  @ 2026-09-02T14:20Z  base=origin/main (45b3f26)
                            20 worktrees  24 branches  9 open PRs  gen: 1.2s

── 1. WORKTREE TABLE (derived: git worktree list --porcelain) ──────────────
 PATH                                      BRANCH                          HEAD     DIRTY  AHEAD/BEHIND origin/main
 C:/~shit/FLOSS                             feat/coordination-room          45b3f26  clean  +18/-2
 C:/~shit/_codex_sweettest_substrate_bridge codex/sweettest-substrate-bridge c925ed1  clean  +12/-0  PR#61
 C:/~shit/_pr43_fresh                       feat/preservation-spine-standalone-work 4daefa0 clean +40/-0 PR#43
 C:/~shit/_pr59_fresh                       fix/pr43-unclassified-durability-work 7edd1c8 clean +2/-0  PR#59 (stacked on PR43)
 C:/worktrees/~shit/able-rampart/~shit     (detached HEAD)                 18bdcc1  dirty  —         ORPHAN
 C:/~shit/_dep46                            (detached HEAD)                 cfb1cfc  clean  —         ORPHAN  ← FAILURE 1
 C:/~shit/FLOSS/.worktrees/coordination-room-rebased feat/coordination-room-rebased 2460c55 clean +6/-4  stale base
 ... (13 more, collapsed — ` --all` to expand)

── 2. BRANCH CONTAINMENT MATRIX (derived: git branch --contains HEAD + merge-base) ──
                    contains →  main  PR43  PR59  PR61  coord-room  coord-room-rebased
 main (origin/main)              ●     ·     ·     ·      ·           ·
 feat/coordination-room          ·     ·     ·     ·      ●           ·
 codex/sweettest-substrate-bridge·     ·     ·     ●      ·           ·
 feat/preservation-spine-standalone-work · ●   ●     ·      ·           ·
 fix/pr43-unclassified-durability-work   · ●   ●     ·      ·           ·  ← stacked: PR59 ⊂ PR43
 chore/dependabot-hardening      ·     ·     ·     ·      ·           ·  ← isolated, no overlap
 [!] codex/pr38-review-cleanup CONTAINS 77cd9eb already in feat/coordination-room (duplicate — see §6)

── 3. DIVERGENCE ALERTS (derived: git rev-list --left-right --count A...B) ──
 [!] feat/coordination-room-rebased  +6/-4 vs origin/main  base=3f22ec3 (871 commits behind HEAD)
 [!] C:/~shit/_dep46  detached cfb1cfc  base=4daefa0  0 commits unique, parent already merged — delete worktree
 [~] codex/improve_gates (operator surface)  +5/-0 vs 18bdcc1 — no remote, local-only
  ok  PR43, PR59, PR61  all rebased ≤24h (merge-base age <1d)

── 4. CLAIM REFS (derived: packages/source_chain + git log --grep=claim) ────
 branch                              last claim                  vote/decision
 feat/coordination-room              2026-08-24 claim: gates     no open vote
 codex/sweettest-substrate-bridge    —                           —  (harness-only, no claim)
 fix/pr43-unclassified-durability    —                           —  (durability fix)

── 5. OPEN PRs (derived: gh pr list --repo G-0-B/FLOSS, 5s timeout) ────────
 #61  codex/sweettest-substrate-bridge       OPEN  2026-08-30  Rust Sweettest substrate bridge
 #59  fix/pr43-unclassified-durability       OPEN  2026-08-23  stacked on #43 — merge after #43
 #43  feat/preservation-spine-standalone     OPEN  2026-08-21  40 commits, needs rebase on main
 #41  reconcile/pr38-salvage-20260817        OPEN  2026-08-17  BLOCKED: merge conflict with feat/coordination-room
 ... 5 dependabot PRs omitted
 [!] worktree C:/~shit/_pr43 (old) points to 073c85e — PR43 head is now 4daefa0 — stale worktree  ← FAILURE 2

── 6. ALREADY-FIXED ELSEWHERE (derived: git log --all -S <token> --oneline) ─
 token searched: from last 20 fix: commits (git log --all --oneline --grep=fix)
  "CheckpointIntegrityError"  → 43-A fixed in PR43/59 (commit 7e759e9) — still open in codex/pr38-review-cleanup:77cd9eb  ← FAILURE 3
  "--no-ext-diff"             → 43-C fixed in PR43 (89187d0) — missing in chore/dependabot-hardening:da7e61a
  "_remove_empty_checkpoint_file" → 59-A fixed in PR59 (7edd1c8) — not in main, expected
  "opaque-preservation-ineligible"→ 43-B fixed in PR43 (b5722c4) — absent from old worktree C:/~shit/_pr43
  tip: `hermes status --show-patch <sha>` to diff the fix into current branch

── FOOTER ───────────────────────────────────────────────────────────────────
 4 failures seconds-visible: [1] orphan detached worktree  [2] stale PR worktree  [3] duplicate already-fixed branch  [4] rebased-behind base
 Run: `hermes status --all` (full 20 rows)  `hermes status --json` (machine-readable)
 Sources: worktree list --porcelain | for-each-ref + merge-base | rev-list --left-right --count | gh pr list | log -S
