# Branch Containment Ladder — Ancestor Matrix Report

**Date:** 2026-09-02 (UTC)  
**Repo:** `C:/~shit/FLOSS` (FLOSS project repo; not `C:/~shit` workspace root)  
**Task:** Verify `docs/research/2026-05-15-working-todo-list.md` §0 claim of a clean containment ladder vs. brainstorm claim that ladder is now false (mutually non-ancestral).  
**Verdict:** **LADDER IS FALSE — falsified.** The brainstorm claim is correct.

---

## 1. Claim under test

`FLOSS/docs/research/2026-05-15-working-todo-list.md` §0 — "Branch & PR topology (verified 2026-08-18)":

```
main  ──  origin/main  ──  PR38 branch  ──  PR41 branch  ──  feat/preservation-spine (HEAD)
                            (+120 to HEAD)  (+32 to HEAD)     == origin/  (0 ahead, 0 behind)
```

> "`feat/preservation-spine` is a strict superset of both PR branches and is fully pushed, yet has no PR of its own. PR38 and PR41 are therefore reviewing *subsets* of a line that has already moved past them. Confirmed via `git merge-base --is-ancestor` for both."

Section 0.1c (2026-08-21) later records that this entanglement was *intentionally broken*: merge `c7c62d0` ("bring the salvage/preservation spine onto the reconciled line") was dropped; 31 spine commits were cherry-picked onto `origin/main` as `feat/preservation-spine-standalone` (PR #43). That section already declares row 0.3 "RESOLVED" — the ladder it describes is historical, not current.

The falsifier to verify now: **`reconcile/pr38-salvage-20260817` (PR41) and `feat/preservation-spine` are mutually non-ancestral** — neither contains the other — so no clean ladder exists.

---

## 2. Branch tips at time of check

| Branch | SHA (short) | SHA (full) | Subject |
|---|---|---|---|
| `main` (local) | `ec195d7` | `ec195d7dc94f16439ee02b2eb98fa9f53876a616` | Merge pull request #33 from G-0-B/kalisam-codeql-workflow |
| `origin/main` | `2d5e647` | `2d5e6479083bf2962fe22e67525f562934d5bb50` | Merge pull request #55 from G-0-B/chore/dependabot-hardening |
| `reconcile/pr38-salvage-20260817` | `e2d02af` | `e2d02af226fc7dc769b628fda8cefa12a763bf3b` | docs(seam): the branch state, the merge blocker, and what got built twice |
| `feat/preservation-spine` | `802b3e7` | `802b3e7691ce12e748d792e6a1ae1120c4605296` | refactor: salvage_spine -> preservation_spine; register under ADR-18 tier 2 |
| `feat/preservation-spine-standalone` | `5af1a80` | `5af1a80c8dd64a038ede16331b4800f124373783` | refactor: salvage_spine -> preservation_spine; register under ADR-18 tier 2 |
| `feat/preservation-spine-standalone-work` | `4daefa0` | `4daefa0c74d706e58b6af7b90ac06e1064d97149` | fix(preservation-spine): fail closed on stem substring for secret markers |
| `feat/coordination-room` | `45b3f26` | `45b3f2638a6b856d74cbd15f3b2bcdfb04a2c0b1` | feat(gates): an omitted tier stops being an exemption, and three more remedies |
| `feat/coordination-room-rebased` | `2460c55` | `2460c557116ad1641a359cde0b58a25ca0356142` | feat(daemons): start/stop coordination room on :7334 |

`origin/feat/preservation-spine` tracks `feat/preservation-spine` (same SHA). `origin/reconcile/pr38-salvage-20260817` tracks `reconcile/pr38-salvage-20260817`. `origin/feat/preservation-spine-standalone` tracks `feat/preservation-spine-standalone-work` at `4daefa0` (standalone-work is ahead of standalone).

---

## 3. `merge-base --is-ancestor` matrix

Command: `git -C C:/~shit/FLOSS merge-base --is-ancestor <A> <B>` — exit 0 = YES (A is ancestor of B), exit 1 = NO.

| A \ B | main | origin/main | reconcile | spine | spine-standalone | spine-standalone-work | coord-room | coord-room-rebased |
|---|---|---|---|---|---|---|---:|---|
| **main** | — | **YES (0)** | **YES (0)** | **YES (0)** | **YES (0)** | **YES (0)** | **YES (0)** | **YES (0)** |
| **origin/main** | NO (1) | — | **YES (0)** | NO (1) | NO (1) | **YES (0)** | **YES (0)** | **YES (0)** |
| **reconcile** | NO (1) | NO (1) | — | **NO (1)** | **NO (1)** | **NO (1)** | NO (1) | NO (1) |
| **spine** | NO (1) | NO (1) | **NO (1)** | — | NO (1) | NO (1) | NO (1) | NO (1) |
| **spine-standalone** | NO (1) | NO (1) | NO (1) | NO (1) | — | NO (1) | NO (1) | NO (1) |
| **spine-standalone-work** | NO (1) | NO (1) | NO (1) | NO (1) | NO (1) | — | NO (1) | NO (1) |
| **coord-room** | NO (1) | NO (1) | NO (1) | NO (1) | NO (1) | NO (1) | — | **NO (1)** |
| **coord-room-rebased** | NO (1) | NO (1) | NO (1) | NO (1) | NO (1) | NO (1) | **NO (1)** | — |

Raw reproduction:

```
for a in main origin/main reconcile/pr38-salvage-20260817 feat/preservation-spine feat/preservation-spine-standalone feat/preservation-spine-standalone-work feat/coordination-room feat/coordination-room-rebased; do
  for b in ...; do git merge-base --is-ancestor "$a" "$b"; echo "exit $?"; done
done
```

All 56 ordered pairs tested; no errors (no exit 128).

---

## 4. Key falsifier pairs (with merge-base)

| Pair | `is-ancestor A->B` | `is-ancestor B->A` | `merge-base` | Interpretation |
|---|---|---|---|---|
| `reconcile` ↔ `spine` | NO (1) | NO (1) | `31bcad07098cc57fda704e6a6a4153770e6a76e1` | **Mutually non-ancestral — ladder break** |
| `reconcile` ↔ `spine-standalone` | NO / NO | — | `31bcad07098...` vs `77cd9eb22bd...` respectively | Mutually non-ancestral |
| `reconcile` ↔ `spine-standalone-work` | NO / NO | — | diverges at `2d5e647` vs `31bcad0` | Mutually non-ancestral |
| `origin/main` ↔ `spine` | NO / NO | — | `77cd9eb22bd387e6ce87fc6f90e0dedd22486834` | Spine forked from older main; not descendant of current origin/main |
| `origin/main` → `reconcile` | YES | NO | `2d5e647` (origin/main itself) | Reconcile *is* descendant of origin/main (as expected post `f2618a0` merge) |
| `origin/main` → `coord-room` | YES | NO | `2d5e647` | coord-room descends from origin/main |
| `origin/main` → `coord-room-rebased` | YES | NO | `2d5e647` | rebased also descends from origin/main |
| `coord-room` ↔ `coord-room-rebased` | NO / NO | — | `08619f09ea5bf99e7fe2f55c9ba28a7bc52b192c` | **Mutually non-ancestral — second ladder break** |
| `spine` ↔ `spine-standalone` | NO / NO | — | `77cd9eb22bd...` | Different cherry-pick histories, same fork point, mutually non-ancestral |
| `spine` ↔ `spine-standalone-work` | NO / NO | — | — | Mutually non-ancestral |
| `main` → `origin/main` | YES | NO | — | Local main is 241 commits behind origin/main |

---

## 5. Divergence counts (`rev-list --left-right --count A...B` → "A-only<TAB>B-only")

| A...B | A-only | B-only |
|---|---|---|
| `origin/main...reconcile` | 0 | 242 |
| `origin/main...spine` | 24 | 127 |
| `origin/main...spine-standalone` | 15 | 31 |
| `origin/main...spine-standalone-work` | 0 | 40 |
| `origin/main...coord-room` | 0 | 203 |
| `origin/main...coord-room-rebased` | 0 | 233 |
| `reconcile...spine` | 171 | 32 |
| `reconcile...spine-standalone` | 257 | 31 |
| `reconcile...spine-standalone-work` | 242 | 40 |
| `reconcile...coord-room` | 55 | 16 |
| `reconcile...coord-room-rebased` | 16 | 7 |
| `spine...spine-standalone` | 127 | 40 |
| `spine...spine-standalone-work` | 127 | 64 |
| `coord-room...coord-room-rebased` | 16 | 46 |
| `main...origin/main` | 0 | 241 |

---

## 6. `git log --decorate --graph` (focused)

```
* 45b3f26 (HEAD -> feat/coordination-room) feat(gates): ...
* b05f7dd docs(handoff): ...
...
* b757373 feat(coordination-room): file-claim MCP on :7334
| * e2d02af (origin/reconcile/pr38-salvage-20260817, reconcile/...) docs(seam): ...
| * 616deaa fix(memory): ...
  ... (242 commits on reconcile line)
| | * 4daefa0 (origin/feat/preservation-spine-standalone, feat/preservation-spine-standalone-work)
| | * 2460c55 (feat/coordination-room-rebased) feat(daemons): ...
| | * 32577b8 (hermes-local-orchestrator) ...
* | f2618a0 merge: bring main into the reconciliation line (CI config from #44, deps from #42)
|/|
| | * 2d5e647 (origin/main, origin/HEAD) Merge pull request #55 ...
...
* 802b3e7 (feat/preservation-spine) refactor: salvage_spine -> ...
*   c7c62d0 merge: bring the salvage/preservation spine onto the reconciled line
|\ 
| * ce26338 fix: isolate Git bundle inspection
  ... (spine commits)
| * 31bcad0 merge: reconcile pr/38 into the salvage line
```

Full graph captured via:

```
git -C C:/~shit/FLOSS log --oneline --decorate --graph --all -50
git -C C:/~shit/FLOSS log --oneline --decorate --graph --all --simplify-by-decoration
```

Key topology notes:

- `feat/preservation-spine` tip `802b3e7` sits on top of merge `c7c62d0`, which joined the old reconciled line at `31bcad0`. Its fork point vs `origin/main` is `77cd9eb22bd387e6ce87fc6f90e0dedd22486834` — **not** `origin/main` tip.
- `feat/preservation-spine-standalone` fork point is `c1f51aca2edd95f50c5a8820eac30db68b4b10f8` (Merge PR #30); `spine-standalone-work` was rebased forward to `2d5e647` (current origin/main).
- `reconcile` includes merge `f2618a0` bringing `origin/main` in — hence origin/main is its ancestor.
- `coord-room` and `coord-room-rebased` share base `08619f09ea5bf99e7fe2f55c9ba28a7bc52b192c` but have diverged (16 vs 46 commits) with no ancestry in either direction.

---

## 7. Worktree list

```
C:/~shit/FLOSS                                      45b3f26 [feat/coordination-room]        ← main worktree, HEAD
C:/pr38t1                                           a152134 [codex/pr38-prior-decision-task1]
C:/Users/kalis/.ao/data/worktrees/floss/floss-1     c9bb0fd [ao/floss-1/root]
C:/Users/kalis/AppData/Local/Temp/claude/pr41-wt    e2d02af [reconcile/pr38-salvage-20260817]
C:/~shit/_ci_config                                 97174d6 [chore/github-ci-config]
C:/~shit/_codex_pr38_cleanup                        77cd9eb [codex/pr38-review-cleanup]
C:/~shit/_codex_pr38_salvage_design                 ce26338 [codex/pr38-salvage-design]
C:/~shit/_codex_sweettest_substrate_bridge          c925ed1 [codex/sweettest-substrate-bridge]
C:/~shit/_dep46                                     cfb1cfc (detached HEAD)
C:/~shit/_dep46base                                 c9bb0fd (detached HEAD)
C:/~shit/_dephard                                   da7e61a [chore/dependabot-hardening]
C:/~shit/_pr25fix                                   5b5cefd (detached HEAD)
C:/~shit/_pr43                                      073c85e [fix/pr43-review]
C:/~shit/_pr43_fresh                                4daefa0 [feat/preservation-spine-standalone-work]
C:/~shit/_pr59_fresh                                7edd1c8 [fix/pr43-unclassified-durability-work]
C:/~shit/FLOSS/.claude/worktrees/quirky-mcnulty     a5ef2b7 [claude/quirky-mcnulty]
C:/~shit/FLOSS/.worktrees/a2a-harness-mesh          225287c [feat/a2a-harness-mesh]
C:/~shit/FLOSS/.worktrees/coordination-room-rebased 2460c55 [feat/coordination-room-rebased]  ← coord-room-rebase worktree
C:/~shit/FLOSS/.worktrees/digestion-actions         35a0687 [chore/digestion-actions]
C:/~shit/FLOSS/.worktrees/hermes-local-orchestrator 32577b8 [hermes-local-orchestrator]
```

Coord-room-rebase worktree at `C:/~shit/FLOSS/.worktrees/coordination-room-rebased` is clean, on `feat/coordination-room-rebased` at `2460c55`, diverged from `origin/reconcile/pr38-salvage-20260817` by 7/16 commits (per `git status`).

---

## 8. Verdict — exact falsifier

**The §0 clean ladder claim is FALSE as of 2026-09-02.**

Exact falsifier, with commands and exit codes:

```
$ git -C C:/~shit/FLOSS merge-base --is-ancestor reconcile/pr38-salvage-20260817 feat/preservation-spine; echo $?
1   # reconcile is NOT ancestor of spine — ladder requires YES

$ git -C C:/~shit/FLOSS merge-base --is-ancestor feat/preservation-spine reconcile/pr38-salvage-20260817; echo $?
1   # spine is NOT ancestor of reconcile — mutually non-ancestral, not just reversed

$ git -C C:/~shit/FLOSS merge-base reconcile/pr38-salvage-20260817 feat/preservation-spine
31bcad07098cc57fda704e6a6a4153770e6a76e1   # common ancestor is 31bcad0, deep in history

$ git -C C:/~shit/FLOSS rev-list --left-right --count reconcile/pr38-salvage-20260817...feat/preservation-spine
171    32   # 171 reconcile-only, 32 spine-only — two distinct lines, not a superset
```

**What happened:** §0.1c (2026-08-21) deliberately broke the ladder by dropping merge `c7c62d0` and re-creating the spine as `feat/preservation-spine-standalone` on `origin/main`. The old `feat/preservation-spine` branch was left untouched at `802b3e7` as a historical artifact. The todo list itself records this split — the "clean ladder" diagram is explicitly dated 2026-08-18 and superseded by 0.1c. The current truth is:

- `main` → `origin/main` → `reconcile` is a valid chain (YES, YES).
- `reconcile` ↮ `spine` (all three spine variants) — **no ancestry either way**.
- `origin/main` ↮ `spine` / `spine-standalone` — **no ancestry either way** (spine forked from an older main).
- `origin/main` → `spine-standalone-work` is YES (the only spine variant rebased onto current origin/main).
- `coord-room` ↮ `coord-room-rebased` — **no ancestry either way** (16 vs 46 diverged commits).
- Local `main` is 241 commits behind `origin/main` — also not a clean ladder tip.

**Secondary falsifier:** `feat/coordination-room` ↔ `feat/coordination-room-rebased` mutually non-ancestral (both exit 1, merge-base `08619f0`), so even the coordination-room line is not a ladder.

**Action implication:** Do not use `feat/preservation-spine` (the `802b3e7` line) as "HEAD / superset of everything." The current spine is `feat/preservation-spine-standalone-work` (`4daefa0`, tracked as PR #43) on top of `origin/main`. Any doc or script still citing `feat/preservation-spine` as HEAD/superset is stale and must be updated to `feat/preservation-spine-standalone-work` or `origin/main` as appropriate.

---

## 9. Commands run (for reproducibility)

```bash
cd C:/~shit/FLOSS

# Branch enumeration
git branch -a
git worktree list --verbose
git rev-parse --verify main origin/main reconcile/pr38-salvage-20260817 feat/preservation-spine feat/preservation-spine-standalone feat/preservation-spine-standalone-work feat/coordination-room feat/coordination-room-rebased

# Full ancestor matrix (56 ordered pairs)
for a in main origin/main reconcile/pr38-salvage-20260817 feat/preservation-spine feat/preservation-spine-standalone feat/preservation-spine-standalone-work feat/coordination-room feat/coordination-room-rebased; do
  for b in main origin/main reconcile/pr38-salvage-20260817 feat/preservation-spine feat/preservation-spine-standalone feat/preservation-spine-standalone-work feat/coordination-room feat/coordination-room-rebased; do
    [ "$a" = "$b" ] && continue
    git merge-base --is-ancestor "$a" "$b"; echo "is-ancestor $a -> $b exit $?"
  done
done

# Merge-bases
git merge-base reconcile/pr38-salvage-20260817 feat/preservation-spine
git merge-base feat/coordination-room feat/coordination-room-rebased
git merge-base origin/main reconcile/pr38-salvage-20260817
git merge-base feat/preservation-spine origin/main
git merge-base feat/preservation-spine feat/coordination-room
git merge-base feat/preservation-spine feat/preservation-spine-standalone

# Divergence counts
git rev-list --left-right --count origin/main...reconcile/pr38-salvage-20260817
git rev-list --left-right --count reconcile/pr38-salvage-20260817...feat/preservation-spine
git rev-list --left-right --count feat/coordination-room...feat/coordination-room-rebased
# (and all other pairs listed in §5)

# Graph
git log --oneline --decorate --graph --all -50
git log --oneline --decorate --graph --all --simplify-by-decoration
git log --oneline --decorate --graph feat/preservation-spine -15
git log --oneline feat/preservation-spine -5
git log --oneline reconcile/pr38-salvage-20260817 -5
git worktree list --verbose
```

---

*Report written to `C:/~shit/.hermes/plans/ancestor-matrix-report.md` — all exit codes and SHAs are live `git` output from 2026-09-02, not reconstructed.*
