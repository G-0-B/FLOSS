# Seam Packet — PR41 lineage and merge state, 2026-09-02

**For any agentic reader** — human, AI, synthetic, hybrid, or otherwise, in any
harness. Written to be read cold, with no access to the thread that produced it.

**Kind:** thread-seam handoff. Plane A evidence. Promotes nothing to canon.
**Written:** 2026-09-02 from branch `reconcile/pr38-salvage-20260817`.
**Companion packet:** `docs/reviews/2026-09-01-polyglot-plugin-materializer-spec/HANDOFF.md`
(written the same day from `feat/coordination-room`). Read that one for
repository topology, tooling traps, and concurrency hazards; this one does not
repeat them. Read this one for branch state, the merge blocker, and what is
left on PR41.

**Truth labels:** ✅ Verified / ⚠️ Specified / 🔮 Aspirational / ❌ Blocked.
Every ✅ carries the command that reproduces it. Re-run rather than trust.

---

## 1. Branch topology, and which branch holds what ✅ Verified

```
git -C FLOSS rev-list --left-right --count origin/main...<branch>
```

| Branch | Ahead of `main` | Holds | PR |
|---|---|---|---|
| `main` | — | tip `2d5e647` | — |
| `reconcile/pr38-salvage-20260817` | 230 | the provenance/anchor/daemon line, 32+ review rounds | #41 |
| `feat/coordination-room` | 233+ | coordination room MCP, skill reminders, gate-coverage work, the companion packet | none |
| `feat/coordination-room-rebased` | 233 | the same five commits rebased onto `reconcile` | none |
| `feat/preservation-spine-standalone` | 40 | preservation + verification spine | #43 |
| `fix/pr43-unclassified-durability` | 43 | durability fixes stacked on #43 | #59 |
| `codex/sweettest-substrate-bridge` | 11 | the Rust Sweettest substrate bridge — the Phase-1 gate | #61 |

**`main` is contained in all of them**, so none needs a rebase, and
`git merge-tree` reports **zero conflicts** between #41, #43 and #61. They are
independent and can land in any order.

`feat/coordination-room` and `reconcile` are **forks of each other**, not a
line. `coordination-room` carries work that exists nowhere else;
`feat/coordination-room-rebased` is the reconciliation of that fork and is the
branch to merge, not the original.

## 2. The duplication hazard, measured ✅ Verified

Three separate fixes were written twice, independently, by different agents on
different branches, for the same defects, within 48 hours:

| Defect | Fix A | Fix B |
|---|---|---|
| `infer_surface()` had no Hermes case | `reconcile` | branch `fix/pr41-surface-threads` (deleted) |
| Four HTTP projections dropped `headers` | `reconcile` | same deleted branch |
| Skill materializer never pruned withdrawn skills | `reconcile` | same deleted branch |
| Memory note missing YAML frontmatter | `48875cf` on `coordination-room` (2 days ago) | `616deaa` on `reconcile` (today) |

The frontmatter pair is the instructive one: the two frontmatter blocks are
**byte-identical**, produced two days apart by agents who never saw each
other's work. Convergence, not conflict — but the fix sat on `coordination-room`
for two days while `reconcile` stayed broken, because the branches had forked
and nothing carried it across.

The duplicate implementation branch was deleted rather than merged: `reconcile`'s
versions were better (its Codex projection actually implements `http_headers`
against Codex's documented config reference, where the duplicate only refused
to project them). **The rule this yields: before writing a fix for a review
thread, check whether another branch already has it.** `git log --all --oneline
-S'<a distinctive token from the fix>'` is the cheap check.

## 3. Merge state — structurally blocked ❌ Blocked

All four substantive PRs report **zero failing checks** and
`reviewDecision: REVIEW_REQUIRED`. Reproduce:

```
gh pr view <n> --json reviewDecision,mergeStateStatus,statusCheckRollup
```

Ruleset `safety rulez` (id `9980168`, enforcement `active`) targets
`~DEFAULT_BRANCH` with rules `deletion`, `non_fast_forward`,
`copilot_code_review`, `pull_request`, `required_status_checks`, and a single
bypass actor: user `37503662` (`kalisam`), mode `always`.

**Nothing on any PR is `APPROVED`** — every review across #41, #43, #59 and #61
is `COMMENTED` (CodeRabbit, Codex connector, GitHub Advanced Security, the
operator). **Copilot has never reviewed any of them, and cannot be requested:**

```
gh api -X POST repos/G-0-B/FLOSS/pulls/61/requested_reviewers \
  -f 'reviewers[]=copilot-pull-request-reviewer[bot]'
```

returns success and adds no reviewer; `reviewRequests` stays empty. So the
`copilot_code_review` rule is **unsatisfiable on this repository as configured**,
and every merge — including a merge into a feature branch — requires the owner
bypass (`--admin`).

A second, separate blocker on #59: GitHub refuses to merge it through either
`gh pr merge` or `PUT /pulls/59/merge`, because it is a stacked PR (base is
#43's branch, not `main`) and demands an "asynchronous merge REST API" endpoint
that is not reachable through `gh api` by any documented path. The workable
route is a local `git merge` of the two branches followed by a push.

**This is an operator decision, not an agent one.** Merging here means using the
bypass on the project's own gate, and this project's thesis is that gates are
not bypassed.

## 4. PR41 — four live threads left ✅ Verified

222 of 269 review threads resolved; 47 unresolved, of which 43 are `isOutdated`
(superseded by later diffs). **Four are live:**

```
gh api graphql --paginate -f query='...reviewThreads...' \
  --jq '...select(.isResolved==false and .isOutdated==false)...'
```

| Thread | State |
|---|---|
| `hook_post_write.py:121` ×2 — deterministic verification of Hermes `patch` | **Declined with reason, unrefuted.** See §5 |
| `hook_post_write.py:300` — Codex edits labelled `claude-code` | **Real, unfixed.** Design in §6 |
| `synthesizer.py:511` — mixed-mode survivors not rechecked for independence | **Real, unfixed.** See §7 |

## 5. Hermes `patch` verification — deliberately not implemented ⚠️ Specified

The false-evidence half is closed: `_verification_evidence_ref()` types any
non-`VERIFIED` hashline result as `log`, not `test`, so a SKIPPED verification is
no longer emitted as test evidence.

The substantive half stands. Hermes's `patch` carries **V4A patch text**
(`*** Update File:` / `*** Add File:` / `*** Delete File:` /
`*** Move File: src -> dst`, multi-file), confirmed against
`C:/Users/kalis/AppData/Local/hermes/hermes-agent/tools/file_tools.py`.
`hashline.verify_tool_edit()` handles only edit/replace, write/write_file and
multiedit, so every Hermes patch returns `SKIPPED` and the pre-write checkpoint
cannot derive an exact post-image.

**Why it was left open rather than fixed:** verifying V4A needs a diff parser,
and a subtly wrong parser produces a false `VERIFIED` in an append-only
provenance chain — the worst outcome available here, and not something to write
without a reviewer. A partial path exists if someone wants it: `*** Add File:`
hunks carry full content and map exactly onto the existing write-like
verification, and `*** Delete File:` is an existence check; only
`*** Update File:` needs real diff logic.

## 6. Codex provenance label — design, not yet built ⚠️ Specified

`infer_surface()` labels `Write|Edit|MultiEdit` as `claude-code` unconditionally,
and that label reaches the Claim summary and the signed packet `source_systems`.
The Codex target registers **the same three tool names, the same `PostToolUse`
event, and a byte-identical command**:

```
python -c "import json; d=json.load(open('shared-hook-surface.json')); ..."
# claude_user  PostToolUse  Write|Edit|MultiEdit => "${PYTHON}" "${FLOSS_HOOKS}/hook_post_write.py"
# codex        PostToolUse  Write|Edit|MultiEdit => "${PYTHON}" "${FLOSS_HOOKS}/hook_post_write.py"
```

**Nothing in the payload can separate them.** This is unlike the Hermes case,
which was fixable from the payload because Hermes sends
`hook_event_name: pre_tool_call|post_tool_call` (see
`agent/shell_hooks.py::_serialize_payload`).

The only place that knows which harness is calling is the manifest. So the fix
is a `--surface <label>` argument appended to the command in each target's
registration, with `infer_surface()` preferring an explicit label over
inference and the current behaviour as the default when absent.

**Why it was not landed:** the change is in `shared-hook-surface.json`, which
regenerates six projections into machine-wide configuration outside the
repository. That is a blast radius that wants the operator in the loop and a
reviewer on the diff, not a quiet P2 fix.

## 7. Mixed-mode survivor recheck — unassessed ⚠️ Specified

`synthesizer.py:511`: when a `mixed` run begins with an independent
online-plus-local pool and provider or embedding failures leave three or more
voters drawn from too few surfaces or families, an exemption skips the survivor
independence check and clustering reports a normal consensus tier. The reviewer
notes this conflicts with `resolve_voter_pool()`, which applies
`assert_roster_is_independent()` to the combined mixed pool, and that only the
deliberately narrow `local` mode should bypass the recheck.

Not investigated in this thread. It is the highest-value of the three remaining,
because its failure mode is an outage silently converting an independent
ensemble into a correlated one while still reporting consensus — the exact
defect class the ensemble exists to prevent.

## 8. What landed on `reconcile` from this thread ✅ Verified

| Commit | What |
|---|---|
| `616deaa` | the memory note's missing frontmatter, plus a guard test |

The guard is the part worth keeping. Every pre-existing test in
`scripts/tests/test_shared_agent_memory.py` builds fixtures in `tmp_path`, so
nothing in CI had ever read the real `docs/agent-memory/` tree — which is why a
docs-only commit could take the whole agent-surface projection down for four
days with the green set staying green. The new test mirrors the materializer's
own `canonical_root.glob("*/*.md")` exactly, and was verified by planting a
frontmatter-less note and confirming it fails and names the file.

Green set at `616deaa`:

```
python -m pytest -q packages/ tests/ scripts/tests/ --deselect \
  scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
# 1037 passed, 7 skipped, 1 deselected
```

## 9. Next actions, in the order that unblocks the most

1. **Operator:** decide whether the ruleset bypass is used to merge, or whether
   `copilot_code_review` is removed from `safety rulez` so PRs can merge on the
   checks that actually run. As configured, nothing can ever merge without the
   bypass — that is a standing condition, not a backlog item.
2. **Merge order once decided,** all conflict-free: #61 (Phase-1 gate) → #43
   with #59 folded in locally → #41 → `feat/coordination-room-rebased`.
3. **#61 has had no adversarial review at all** — one `COMMENTED` pass from the
   Codex connector. It is the Phase-1 substrate gate; merging it declares the
   bridge covered. It is the single best target for review spend.
4. Take `synthesizer.py:511` (§7), then the Codex label (§6) as an
   operator-supervised manifest change.
5. Carry `feat/coordination-room-rebased` forward rather than
   `feat/coordination-room`.
