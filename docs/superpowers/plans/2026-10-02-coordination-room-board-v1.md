# Coordination Room Message Board v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow the coordination room from "claims plus broadcast" into a continuously saved message board: topics, threads, evidence-labelled posts, a generated `BOARD.md`, a room-only lifecycle, and (Phase 2) an A2A post/read bridge.

**Architecture:** Purely additive over v0.1. `events.jsonl` stays the only record and the room daemon (`:7334`) stays its only writer; it loads room state only after it owns its PID slot, skips a log line it cannot read instead of failing on it, and runs each tool call off its event loop. New optional fields ride on existing `broadcast` and `claim` rows, so old rows still load and old callers still work. `BOARD.md` is a view of the log as of a stated time, rewritten only after a logged event, staged through a fresh file, and never read back. The existing start and stop scripts gain `-Only` and `-DryRun` so the room can be deployed and rolled back without touching other daemons. The A2A bridge is a client of the room's MCP tools, not a second writer.

**Tech Stack:** Python 3.13, pytest, FastMCP from the MCP v1 SDK (`mcp>=1.27,<2`), `a2a-sdk==1.1.2` (Phase 2), jsonschema, Windows PowerShell 5.1 and PowerShell 7 for the daemon scripts.

**Spec:** `docs/specs/coordination-room.spec.md` v0.2.0 (Task 1 writes it). Research seam: `docs/research/2026-08-31-mas-papers-reeval-intake.md:49-52` (DELM "admission-time verification"). Nothing here implements DeAR's dynamic topology.

**Revision:** 7, 2026-10-04.

- Revision 1 (SHA-256 `eaa3d75065d8d3582cdcaff1e017d5b214c083ef794a72ba09c583e0462886ff`): Codex review round 1, "revise before implementation", seven findings.
- Revision 2 (SHA-256 `6dabb8e6a6ef9f353af7d5f52f2765cf63746a34f69a493e8e7019be635ca635`): Codex audit round 2, "not deployment-ready", four findings plus one inherited; Antigravity (Gemini 3.1 Pro) review of revision 2 and of the Codex audit.
- Revision 3 (SHA-256 `7d25eee2bc44286a141419aa7058978bd9fb6ac7fd27bb33dfb712b2bd02af73`): Codex audit round 3, "revise before execution", five findings (one P1, three P2, one P3). Codex hit its usage limit after writing `round-3/REVIEW.md`, so its closing message and its `receipt-hashes.json` were never written; the review itself is complete.
- Revision 4 (SHA-256 `7d40c37e91a1e6beb9f45a09cd9d73ca4c8b4cb32e5db7aebf6d6d9da955c6f1`): Codex audit round 4, 2026-10-04, "Phase 1 implementation design is substantially ready for its existing operator decisions"; two P2 findings (deployment smoke acceptance, bridge number parsing) and one P3 (preview match), no P1, no redesign warranted.
- Revision 5 (SHA-256 `f2a8392e874a6f90c6818657fccc0050625da518fb09860dff0d58c68b8d1752`): Codex audit round 5, 2026-10-04, cut short by its usage limit. Its `round-5/REVIEW.md` is marked "audit in progress" with a provisional disposition, "Phase 1 has no newly identified implementation blocker; numeric error handling still needs correction before Phase 2", and one written finding (R5-01, P2, Phase 2). Its receipts for the rest were written; its verdicts on them were not.
- Revision 6 (SHA-256 `c8ae505a4da4bfb539642d4cb51860a0aef04927725968e9660970256af805f4`) was not reviewed as such. Round 6 is two Grok-family reviews of revision 5, both "hold": a short one (four items) and a long adversarial one with its own Linux runs, probes and a mutation run (eight major, thirteen minor). Revision 6 differed from revision 5 only in three bridge files and the smoke-marker check, so their findings applied to it unchanged.
- Every finding was reproduced or checked before anything changed. Dispositions are below. Reviews and evidence: `docs/reviews/2026-10-02-room-board-v1/` (round 1 at its root, rounds 2 to 6 in `round-2/` to `round-6/`).

**Truth status:** ⚠️ Specified. Every file body and every edit in this plan was run in a scratch copy of `feat/coordination-room-rebased @ 4aab13e` plus `feat/a2a-harness-mesh @ 225287c`, on Windows. Measured on the authoring machine for revision 7: 117 passed in `packages/coordination_room/tests` (21 baseline + 96 new; the v0.1 compatibility test skips where commit `4aab13e` is not in the clone); 235 passed and 1 skipped across `coordination_room` and `a2a_mesh` (234 and 2 where no `.mcp.json` exists above the checkout); 24 passed in `scripts/tests/test_daemon_scope.py` after Phase 1 and 28 after Phase 2, each under both Windows PowerShell 5.1 and PowerShell 7; `ruff check --isolated` (ruff 0.15.11) clean on this plan's Python files; all four edited scripts parse with zero errors in both shells; the deployment helpers pass their harness, including against a real scratch room, in both shells. Required green set, same machine and environment for all three stages: base 992 passed, 1 failed, 7 skipped; Phase 1 1,111 passed, 1 failed, 8 skipped; Phase 2 1,232 passed, 1 failed, 10 skipped (1 deselected in each). The one failure is the same test in all three stages, `scripts/tests/test_text_sources_are_text.py::test_no_tracked_text_file_contains_a_nul_byte`, which needs a git index and fails in an archive extraction. Compared per test case: nothing new fails and no base pass stops passing or disappears. The added skips are the v0.1 compatibility test (an archive has no git history), the optional Hermes probe and the `.mcp.json` ancestry check. Dependencies were this machine's installed set (MCP 1.27.0), not a clean install. `scripts/spec_gate.py --check` prints the same three findings on the base and after each phase. Not run on Linux by the author; a Grok reviewer ran revision 5's new tests on Linux and they passed. Nothing here has landed on any branch. The Deployment section was not executed against a live daemon. Revision 7 has had no independent review.

**Authored:** 2026-10-02, replacing an Antigravity draft that was pasted into a session and never entered the repo.

## Execution record: Phase 1 (2026-10-04)

Phase 1 (Tasks 0 to 6) is on branch `feat/room-board-v1`, built from `4aab13e` in the worktree `C:/~shit/FLOSS/.worktrees/room-board-v1`. Everything below this section is the plan as written: revision 7, SHA-256 `cf241ce69b9d8a753cb3787944cf27488a29ebaa7586647214f6dcc1ebb45932` before this section was added. Read it as the specification the commits were built from. Its Truth status paragraph above describes the state before execution.

**Operator answers** (Task 0 Step 1), one message, verbatim: `approved, advisory claims, start phase 1 as commits`. The third question, pushing the base commit, was not answered.

| Task | Commit | Subject |
|---|---|---|
| 0 | `029b871b192df76b655bbf5c9fd60e66a075f44a` | docs(plan): coordination room message board v1, revision 7 after six review rounds |
| 1 | `a817be966dfd46d974f21744e93d93f72195c77b` | docs(specs): coordination room v0.2.0, topics, threads and evidence labels |
| 2 | `e0b2216945ba9080133b55d769a2a0243255baba` | feat(daemons): -Only and -DryRun on the start and stop scripts |
| 3 | `ea64bcd0d0a394c61c2b7dd88c3fd1d8ead4ab34` | feat(coordination-room): look up file and commit evidence refs within a time budget |
| 4 | `50315b55126d1ffa8d19c86353628a554d7a59da` | feat(coordination-room): BOARD.md as a dated view of the event log, staged exclusively |
| 5 | `5dbce4de4aa9d1a452b330950d01f95d45253c67` | feat(coordination-room): topics, threads, evidence labels and intent on the room |
| 6 | `0281a47cd817efb2f2426886e3a1058c157b33eb` | feat(coordination-room): board tools over MCP, a shell client, deployment helpers |

`ROLLBACK_COMMIT` is the Task 2 commit, `e0b2216945ba9080133b55d769a2a0243255baba`.

**Measured at `0281a47`, on Windows, in that worktree.** ✅ Verified:

- `packages/coordination_room/tests`: 117 passed, none skipped. The v0.1 compatibility test ran against real git history here.
- With `scripts/tests/test_daemon_scope.py`: 143 passed (see deviation 3 for why the script count is 26).
- The required green set, same machine and environment: base `4aab13e` 993 passed, 7 skipped; branch 1,115 passed, 7 skipped; 1 deselected in each; no failures in either. Compared per test case: nothing regressed, nothing went missing, the same seven skips, and all 122 new cases pass. (The archive-only failure reported under Truth status does not occur in a real checkout.)
- `ruff check --isolated packages/coordination_room scripts/tests/test_daemon_scope.py`: clean. `scripts/spec_gate.py --check`: the same three findings as on the base.
- Twenty of the twenty-two Phase 1 files this plan inlines are byte-identical to their inlined bodies; the other two are deviations 2 and 3.
- The live bus was not touched: the listeners on 7331, 7332 and 20128 kept their process ids, 7334 stayed down, and the shared log kept its size and modification time.

**Where the commits differ from the plan text.** Three places, each also explained in its commit message:

1. Task 0. `docs/reviews/2026-10-02-room-board-v1/.gitattributes` (`* -text`) was added. The repository preserves review evidence byte for byte only for `*.json` and `*.txt`; this folder also holds reviewer scripts, JUnit XML, a diff and Markdown with CRLF, and `round-4/receipt-hashes.json` publishes their hashes. All 187 committed blobs were compared with their source files: none differ.
2. Task 1. Two phrases of the spec said "pending operator": the `approval` line and the claim-precedence sentence. They now record the 2026-10-04 answer. The precedence stays marked Specified because the enforced claim mechanism it defers to is proposed, not built.
3. Task 2. The plan's `test_daemon_scope.py` left a literal `%SystemDrive%` directory in whatever directory pytest was started from, which was the checkout: the scripts are run with a bare environment, and Windows creates that directory in the process's working directory on a launch. `_run` now uses the test's temp directory as the working directory, and `test_a_real_run_writes_nothing_where_pytest_was_started` fails without that. The file therefore has 26 cases after Phase 1, not 24, and will have 30 after Phase 2, not 28. The Phase 2 edit pairs in Task 9 were re-checked against the committed files: each old string still occurs exactly once.

**Not done.** ⚠️ Nothing is pushed and no pull request is open: the base `4aab13e` is not on the remote. Not run on Linux by anyone at this revision; the required CI job will be the first Linux run. The Deployment section has not been run; the live room is still v0.1 and still down. The agent-memory projections were not regenerated. Phase 2 has not been started.

**Merged locally, 2026-10-05.** At the operator's instruction (`merge it to local`), `feat/coordination-room-rebased` was fast-forwarded from `4aab13e` to `44b6a5488136d4b14650f9492221cc02ebd5bb46` in its own worktree, `C:/~shit/FLOSS/.worktrees/coordination-room-rebased`. No `git pull` was run first: that branch's configured upstream is `origin/reconcile/pr38-salvage-20260817`, which holds 40 commits this branch does not, and a pull would have merged them in. On the merged checkout, a fresh checkout written by git: the required green set gave 1,115 passed, 7 skipped, no failures; the spec gate showed the same three findings; `ruff` was clean. The implementation worktree `.worktrees/room-board-v1` and the branch `feat/room-board-v1` were then removed; every commit in the table is on `feat/coordination-room-rebased`. Where the plan below says `room-board-v1`, read it as history, with one exception that was corrected in place because it will be used: Deployment step 0 now loads the helpers from `.worktrees\coordination-room-rebased`. Still nothing is pushed, and the "Not done" list above is otherwise unchanged.

**After the merge, 2026-10-06**, at the operator's request. The branch's upstream was corrected to `origin/feat/coordination-room-rebased`; the remote branch is `2460c55`, an ancestor of this one, so a push would be a fast-forward, and none was made. The untracked copies of this plan and of the reviews folder in the primary checkout were removed after every file was compared byte for byte with what is committed here (185 review files and the revision-7 plan, none differing; they went to the Recycle Bin). A handoff for a Linux run of the required test set is at `docs/reviews/2026-10-02-room-board-v1/linux-run/HANDOFF.md`; the result is to be saved beside it. Until that run exists, Linux stays unverified.

**Linux run, 2026-10-06 (Codex, under WSL).** Receipts: `docs/reviews/2026-10-02-room-board-v1/linux-run/` (commit `a1b3b1a`). Ubuntu 24.04, Python 3.13.13, a fresh environment built from this branch's `requirements-ci.txt` (`mcp` resolved to 1.30.0), Linux-side clones of the base and of this branch. ✅ Verified, and recounted by the author from the raw JUnit files: no regression. Base: 990 passed, 1 failed, 9 skipped. This branch: 1,083 passed, 1 failed, 24 skipped. All 1,000 base cases keep their outcome. Of the 108 cases this work adds on Linux, 93 pass and 15 skip for stated Windows-only reasons; the v0.1 compatibility test ran and passed; the spec gate prints the same three findings on both. ❌ The required test set is red on Linux all the same, on the base and on this branch alike: `packages/coordination_room/tests/test_paths.py::test_backslash_collapses_to_same_key` fails. That is v0.1 code from `9c29872`, not this work: `normalize_path` treats a backslash as a separator only where the operating system does. The required CI job will therefore fail on any pull request that carries this package until it is fixed. On a POSIX host it is a real fault and not only a failing test: one file written two ways gets two claim keys and two holders. ⚠️ A one-line fix with four tests was tried in throwaway copies (Linux: the required set went to 1,088 passed, 24 skipped, no failures; Windows: the room package still passes) and is saved, with its evidence, in `docs/reviews/2026-10-02-room-board-v1/linux-path-fix/`. It is not applied: `paths.py` is outside the paths the operator approved.

**Path fix applied, 2026-10-07.** The operator approved the candidate ("yes", to "Apply the path fix to `feat/coordination-room-rebased`?"), which extends the approved paths by `packages/coordination_room/paths.py`. Commit `dff1884dc1e7f508a996fa8a3464b2d1da147b82`: a backslash is a separator on every platform, four tests in `packages/coordination_room/tests/test_path_separators.py`, one sentence in the spec's "Claim unit". Test first: on Linux, against the then-current head, the new tests and the v0.1 test failed (5 failed, 4 passed) before the line went in. ✅ Verified with the commit: on Linux the required test set exits 0 (1,088 passed, 24 skipped), so it is green there for the first time; on Windows 1,119 passed, 7 skipped, no failures; nothing regressed against either of Codex's Linux runs; the spec gate is unchanged. Evidence: `docs/reviews/2026-10-02-room-board-v1/linux-path-fix/`. That commit's message dates the approval 2026-10-06, the day the question was asked; the answer came on 2026-10-07. The GitHub-hosted runner has still not run any of this: nothing is pushed.

**Deployed, 2026-10-11**, at the operator's request ("lets test out the deployment"). The Deployment section's forward path, steps 0 to 6, ran against the live bus for the first time. ✅ Verified: the room serves v0.2 on `127.0.0.1:7334` from the pinned checkout `.worktrees/room-serve-9cbe61cd` (commit `9cbe61cd3e2bb143b1ed3b380f0b631e056eb90c`, a local branch tip: nothing is merged or pushed); `room_state` names the shared log and `BOARD.md` beside it; the smoke post is seq 6 and was found in the shared log by seq, agent and marker; the board was written; a v0.1-style read returns all six rows; malformed posts are refused and add no row; a foreign `Host` gets HTTP 421; the consensus and ensemble daemons kept their process ids. No process was stopped: the room had been down, and the stop script cleared a PID record from 2026-08-31 after judging it not ours. Receipts and the two small differences from the written procedure: `docs/reviews/2026-10-02-room-board-v1/deployment-2026-10-11/`. ⚠️ Not tested: rollback, the bridge, and a logon or reboot (nothing restarts the room).

**Rollback tested, 2026-10-12**, at the operator's request ("yes test the rollback"), then v0.2 redeployed. ✅ Verified against the live bus: the Rollback blocks ran as written; v0.1 from `ROLLBACK_COMMIT` loaded a log holding v0.2 rows, matched the claims the log implies, and appended its own smoke row (seq 16); v0.2 then came back from the same pinned checkout, loaded that row, and posted seq 17. About fifty seconds from the first stop to v0.2 answering again. Afterwards the log has 17 readable rows, seq 1 to 17 without a gap; the old board is archived, a new one written; the consensus and ensemble daemons kept their process ids. One row beyond the procedure: a notice (seq 15) before the restart, because another agent had used the room minutes earlier. That agent was Codex reviewing PR61, the first real use by anyone but the author: four claims with `intent`, all released. Its note that the room "serves a different checkout" is Decision 7 meeting practice: claims are repository-relative and worked; a `file:` evidence ref resolves against the serving checkout's commit, not the caller's working copy. Receipts: `docs/reviews/2026-10-02-room-board-v1/rollback-2026-10-12/`. ⚠️ Still not tested: a logon or reboot, the bridge, and a rollback while a claim is held.

**Restored under Task Scheduler, 2026-10-14.** The redeployed room was gone two days later: no reboot, no crash event, but the Claude desktop app had restarted, and the room had been started from a shell that app launched. Most likely it was ended with the app; the logon-started consensus and ensemble daemons survived the same restart. So the deployment and the rollback test proved the procedure, not durability. At the operator's request ("restore the room durably") a separate logon task, `\FLOSS-Coordination-Room`, now starts only the room from the serving checkout; it was registered and run, the plan's checks passed, and the smoke post is seq 18. A separate task, because the existing one runs the primary checkout's script and repointing it would change the code consensus and ensemble run. ✅ Verified: task result 0, the room serving the shared log, launched the same way as the consensus daemon. ⚠️ Not verified: surviving a Claude desktop restart or a logon. A redeploy of another commit must update the task's action. Receipts: `docs/reviews/2026-10-02-room-board-v1/restore-2026-10-14/`. This also settles the plan's Decision 3 for now: the room has its own logon task.

**Seen while executing, not changed.** On the base, `scripts/tests/test_heartbeat_budget.py` appends to `ticks.log` under the parent of the checkout (`FLOSS/.worktrees/.agent-surface/heartbeat/` when run from a worktree) each time the green set runs. It is outside this plan's files.

## Acceptance is behaviour, not a test count

The counts above are a measurement, not the bar. The work is acceptable when all of these hold:

1. One bus: every post lands in the shared log, and a caller can prove which log it is talking to (`room_state`, and the launcher's dry run prints the pinned path).
2. One writer: a process that has not won the daemon slot neither reads room state from the log nor writes the log or the board. A claim exists only if its row is in the log; a failed write changes nothing and says so.
3. The log cannot be replaced or truncated by its own view, through any path, hard link or re-pointed directory present when a projection starts. (A concurrent actor re-pointing a directory between the check and the rename is outside this guarantee; the spec says so.)
4. Evidence labels say only what the lookup saw and when; nothing is called verified, and no file's digest goes into the shared log.
5. The board says how old it is, labels room claims as advisory with their age, and says names are not authenticated. Board and log health are visible through `room_state`, not only on a hidden console.
6. v0.1 rows load, v0.1 callers see the same rows, and v0.1 code can read a v0.2 log (rollback).
7. Tests write only under their own temp directory, even with an operator's environment set.
8. Nothing regenerates a shared or user-wide surface as a side effect.
9. Room deployment and rollback touch only the room, through the existing identity checks; every step stops on a failed precondition instead of carrying on; and the smoke check finds its own post in the shared log rather than counting the tail.
10. The daemon scripts with no arguments (the scheduled task) do what they did before, in both phases: the optional bridge is never started that way, and the original success lines and incomplete-run exits are kept. One deliberate addition: after Phase 2 a no-argument stop also stops the bridge if it is running.
11. The paired green-set comparison shows no new failures.
12. An unreadable line in the log does not stop the room: it is skipped, counted and reported, and never repaired in place.
13. One caller's slow lookup does not stall the others.
14. Every deployment check is a command that can fail, and the helpers and their harness are in the repository.

## What changed from the Antigravity draft, and why

Every row was checked against the repo on 2026-10-02.

| Draft said | Repo says | This plan |
|---|---|---|
| Paths under `FLOSS/`, A2A source in `.worktrees/a2a-harness-mesh` | `FLOSS/` is a nested, gitignored repo (root `.gitignore:16`). Worktrees live in `FLOSS/.worktrees/`. | All commands run in a FLOSS worktree. |
| Modify `packages/coordination_room/` freely | `docs/superpowers/plans/2026-09-02-coordination-v1.md` Global Constraints: "Keep `packages/coordination_room/` unchanged (0-line vs rebased)". | Task 0 records an operator waiver before any code. |
| Wire `:7334` into `start_mcp_daemons.ps1` and `stop_mcp_daemons.ps1` | Already on `feat/coordination-room-rebased` (`2460c55`). `feat/coordination-room` has neither that nor the line-separator fix. | Base on `feat/coordination-room-rebased`. The scripts gain a selector and the bridge line only. |
| Run A2A on `:9900` | `:9900` is Hermes' own A2A listener (`docs/superpowers/plans/2026-08-29-a2a-harness-mesh.md`). | Bridge uses `:7335`. |
| `room_bridge.py` bridges A2A into the room | Room state (`_seq`, claim table) lives in the daemon process. A second process appending to `events.jsonl` would reuse sequence numbers. | Bridge is an MCP client of `:7334`. An AST test forbids importing the room package. |
| Tag messages `[VERIFIED]` when a file exists | Existence is not verification. Repo truth-label canon forbids the overclaim. | `evidence_status` is `resolved` or `unresolved`, a lookup result with its time (a commit ref also records the full object id). Posts are admitted either way. |
| New `message_type` field next to `type` | Redundant with `type` and `topic`. | Dropped. |
| New `room_post` tool | Extra tool in every agent's tool list for no new capability. | `room_broadcast` gains optional arguments. New tools: `room_topics` only. |
| `room_read(limit=50)` | A non-zero default silently truncates every v0.1 caller. | Default `limit=0` (all). |
| A2A client posts with "post to #claims ..." natural language | Parsing prose is guessing. | Deterministic grammar plus a JSON form. Anything else is an error. |
| `claim_with_intent()` | | `room_claim(..., intent="")`, same event type. |
| DELM benchmark framing | The intake doc itself lists the paper's benchmark numbers as unverified (line 81). | Plan relies only on the structural seam, not on any number. |
| Coordination-v1 baseline "17 tests" | `4aab13e` added 4 line-separator tests. Measured on the base: 21 passed. | Baseline is 21. |

## Review round 1 (Codex, 2026-10-02): dispositions

Each finding was reproduced independently before anything was changed. Revision 3 changes noted where round 2 reopened a row.

| # | Finding | Reproduced | Disposition |
|---|---|---|---|
| B1 | "Re-run the materializer if it reports drift" would overwrite the user-wide Claude memory index with an empty one. `materialize_shared_agent_memory.py` has no `--include-user-scope` flag (revision 1 borrowed it from the hook materializer); its Claude target is an absolute user path, always enabled; from a worktree its source root resolves to `FLOSS/.worktrees/FLOSS/docs/agent-memory`, which does not exist. | Yes: `--check` from `.worktrees/coordination-room-rebased` lists `C:\Users\kalis\.claude\projects\C---shit\memory\MEMORY.md` as drift. | Every materializer step is removed, and Global Constraints forbid running one from the worktree. Fixing the materializer is separate work, in progress in its own session. Codex round 2: closed for this plan. |
| B2 | Importing the server built the room, which wrote `BOARD.md` before the PID guard ran. | Yes. | The board is written only after a logged event. Revision 3 goes further (I1 below): the room is not even built until the first tool call. |
| B3 | Revision 1 called the room claim table "the authority", while coordination-v1 moves exclusivity to git-ref claims. | Yes, as a document conflict; no hook references the room today. | Room claims are specified and rendered as advisory, marked ⚠️ Specified pending the operator's answer (Task 0). Codex round 2: coherent, decision still pending. |
| B4 | The Phase 1 "live check" offered a bare `python -m packages.coordination_room.server`, which from the worktree serves a shadow bus. | Yes. | No task touches the live bus. Phase 1 has an HTTP-level acceptance test on a scratch port; `room_state` reports `root`, `log`, `board`. The Deployment section was rewritten again in revision 3 (R2-02 to R2-04). |
| B5 | `board_path == log_path` replaced the log; test fixtures inherited `COORDINATION_ROOM_BOARD`. | Yes, both. | Fixtures clear every room environment variable. Revision 2's path-string guard was incomplete (R2-01); revision 3 checks file identity and stages through a fresh file. |
| B6 | `resolved` claimed more than the lookup that produced it. | Yes. | Contract is "the lookup at `evidence_checked_at` found it"; rows store that time, a file `sha256` up to 16 MiB and the full commit `oid`. Codex round 2: addressed. Revision 7 removed the file digest (round 6, b-bot 3). |
| B7 | The 24-hour roster went stale on an idle board with nothing saying so. | Yes. | The board carries `As of: <time>, seq <n>`; the roster heading is relative to it. Codex round 2: closed. |

## Review round 2 (2026-10-02): dispositions

### Codex audit of revision 2

| # | Finding | Checked | Disposition in revision 3 |
|---|---|---|---|
| R2-01 (P1) | `BOARD.md.tmp` hard-linked to the log passed the path-string guard; `write_board` opened the predictable staging name and truncated the log, and the post still reported success. | Reproduced: first log line became `# Coordination board`. | `write_board` stages through `tempfile.mkstemp` (created exclusively, never a pre-existing file) and swaps names with `os.replace`, so no alias at any name is ever opened for writing; a `BOARD.md` that is itself a hard link to the log loses only its name. `check_board_path` adds `os.path.samefile`. Tests: hard link at the old staging name survives posts; board hard-linked to the log is refused; board replaced by a hard link after construction loses only its name. |
| R2-02 (P1) | The "room-only restart" ran the all-daemon launcher, which would start any daemon that was down, including ones stopped on purpose. | Confirmed by reading the launcher: every block runs unconditionally. | Task 2 adds `-Only` and `-DryRun` to the existing start and stop scripts. Deployment uses `-Only room`; the bridge has its own `-Only bridge`. Tests prove, under both shells, that `-Only room` attempts only the room, in dry-run and in real mode with harmless stand-ins. |
| R2-03 (P1) | The custom stop recipe ignored `FLOSS_AGENT_DIR` and killed by raw PID, bypassing the creation-token identity check. | Confirmed: the snippet read `$env:USERPROFILE\.floss_agent` and never called `mcp_daemon --check-identity`. | The recipe is gone. Deployment stops the room with `stop_mcp_daemons.ps1 -Only room`, which honours `FLOSS_AGENT_DIR`, kills only a process its identity check calls `OURS`, keeps the record on `UNKNOWN`, and clears stale `FOREIGN` records without killing. |
| R2-04 (P2) | Rollback asked v0.1 for `root`, `log`, `board`, which it cannot report; and said to delete `BOARD.md`. | Confirmed by reading v0.1 `state()`. | Version-aware acceptance: v0.2 checks the paths; v0.1 checks `last_seq` and claims against the log file itself, then proves the write path by finding its own post at the log's tail. `BOARD.md` is renamed to a dated `BOARD.superseded-<UTC>.md`, never deleted. The bridge is stopped before a rollback because a v0.1 room lacks the tools it calls. The rollback point is a named commit (Task 2's) that has v0.1 room code and the room-only scripts. |
| I1 (inherited) | The server built and replayed the room at import, before winning the PID slot; an exiting owner's late append left the new daemon with a stale seq. | Reproduced, and worse than reported: besides seqs `[1, 2, 3, 2, 3]`, the new room granted `x.py` to a second agent after the old owner had claimed it, a second holder on one path. | The server builds the room on its first tool call, which can only happen after the slot is won and the previous owner is gone. A test has a previous owner append and claim after import; the new daemon sees both (conflict, next seq). Library use with two room objects on one log is listed under "Not guaranteed". |

### Antigravity (Gemini 3.1 Pro) on revision 2, and on the Codex audit

| Point | Checked | Disposition |
|---|---|---|
| B1 "dodges the bug instead of fixing it" | True by design. | Unchanged. This plan removes the unsafe step; fixing the materializer is separate work with its own session and its own review. |
| B3 "punts the governance decision to the operator" | True by design. | Unchanged. Precedence between two coordination designs is the operator's to set, not this plan's. |
| `env -u PYTHONPATH` "will crash on Windows PowerShell at Task 0 Step 3" | The specific claim is wrong on this machine: `env` resolves to `C:\Program Files\Git\usr\bin\env.exe` in both PowerShell 5.1 and 7. The point behind it is right: the plan's bash blocks also use heredocs, `mkdir -p` and `$(...)`, which PowerShell will not run. | Global Constraints now name the shell for every fence: `bash` blocks run in Git Bash, `powershell` blocks in Windows PowerShell 5.1 or PowerShell 7, with the PowerShell form of the `PYTHONPATH` clearing given. |
| Summary of Codex: R2-02 fix "strictly targets the `:7334` python module with the correct environment variables, rather than overloading the global startup script" | Diverges from Codex, which asked to reuse the existing interpreter, path and identity handling. A hand-built command re-creates the B4 shadow-bus risk and skips identity recording. | Not taken. `-Only room` on the existing scripts keeps one implementation of path pinning and identity. |
| Summary of Codex: everything else (samefile plus tempfile; defer state until the slot is held; use the identity helper; version-aware rollback; archive the board) | Matches the Codex audit. | Adopted as described under R2-01 to R2-04 and I1. |
| "functionally achieves the DELM/DeAR message board" | Overstated. The plan touches only DELM's admission seam; DeAR's dynamic topology is not here. | Recorded in the Spec line above. |

## Review round 3 (Codex, 2026-10-02): dispositions

| # | Finding | Checked | Disposition in revision 4 |
|---|---|---|---|
| R3-01 (P1) | The required green set regressed: three existing tests in `packages/tests/test_mcp_daemon.py` failed, because revision 3 replaced the two scripts' success lines (`All daemons stopped`, `Daemons started (consensus ...`) that those tests look for. Revision 3's author never ran the full green set. Also: "ruff clean" was not reproducible with a newer ruff. | Confirmed by reading the tests (`test_a_clean_shutdown_still_reports_success`, both cases of `test_no_script_claims_success_it_did_not_achieve`). The ruff difference is configuration drift: no ruff config exists in FLOSS, ruff is not in CI, and ruff 0.15.11 with `--isolated` (default rules) is clean, while Codex's ruff 0.16.10 applied a wider rule set (RUF100, ISC004, SIM117, TRY004, PLW1510, FURB167). | A run with no `-Only` prints its original success line word for word, which is still exactly true then (every daemon was selected); a run with `-Only` prints a line that names what it selected. Both sit after the existing incomplete-run guard and its `exit 1`, so the existing tests pass unchanged and still protect that invariant; Codex suggested editing those tests, which is not needed because no inaccurate message was restored. A new scope test pins the no-argument stop line. The lint gate is now `ruff check --isolated`, version stated. The paired green set was run for revision 4 (Truth status). |
| R3-02 (P2) | With a non-default board path in a different directory, re-pointing that directory at the log's directory after startup made the next projection replace the log with Markdown. | Reproduced against revision 3's `room.py` with an NTFS junction: first log line became `# Coordination board`. | `_project` re-runs `check_board_path` before every write and refuses (stderr; the post still lands) if the board now names the log. The spec states the boundary: aliases present when a projection starts are covered; a concurrent actor re-pointing a directory between that check and the rename is not. Test: `test_board_directory_re_pointed_at_the_log_after_startup_is_refused` (symlink, or junction where symlinks need privilege). |
| R3-03 (P2) | Deployment and rollback carried on after failed preconditions: a failed `git worktree add` still reached the launcher; a failed bridge stop still reached the room stop; a failed port query read as "free"; the sequence check compared against a tail captured before the old owner stopped. | Confirmed by reading revision 3's blocks: none checked an exit code. | Deployment now dot-sources one helper block (inlined below, tested inertly in both shells): `Invoke-DaemonScript` runs each script in a child Windows PowerShell and throws on a non-zero exit; `Assert-OnlyAction` and `Assert-PinnedLog` check previews; `Assert-PortFree` binds the port instead of querying it, so an error can never read as free; `Get-SettledSeq` is read only after the stop; `New-RollbackCheckout` refuses a short id, an existing path, a git failure, or a checkout whose HEAD is not the recorded commit. |
| R3-04 (P2) | `mcp>=1.27` allows MCP 2.x, which has no `mcp.server.fastmcp`; a clean install picked 2.3.0 and the server could not start. | Codex's install and test receipts show the `ModuleNotFoundError` on `from mcp.server.fastmcp import FastMCP`. Not reproduced here (no MCP 2 installed on this machine). The base's bare `mcp` has the same exposure. | `mcp>=1.27,<2`. Moving to the MCP 2 SDK is separate work. |
| R3-05 (P3) | After Phase 2 the no-argument start (the scheduled task) also started the bridge, contradicting "default behaviour unchanged" and "optional". | Confirmed. | The bridge is selectable but not in the start script's default: it starts only with `-Only bridge`. The stop script's default does include it, so a full stop still stops it. Test: `test_bridge_is_opt_in_for_start_but_stopped_by_a_full_stop`. |

Also from round 3, kept as written: the board takes its directory's permissions (now stated in the spec); a lazy first call that fails on a bad log is retried on the next call, and a live PID is not readiness, which is why Deployment requires a successful `room_state`; serving the ASGI app directly bypasses the PID guard, and the production command does not. The three environment-only base failures in Codex's sandbox (Hermes PID liveness denied, `git ls-files` in an archive) are not this plan's.

## Review round 4 (Codex, 2026-10-04): dispositions

Codex confirmed the round-3 closures, reproduced revision 4's three-stage green-set figures exactly, and found three things left.

| # | Finding | Checked | Disposition in revision 5 |
|---|---|---|---|
| R4-01 (P2) | The smoke acceptance compared the log's tail to `$settled + 1`. That measures a counter, not the post: a post to the wrong bus passed when another agent happened to post to the shared log, and a correct post failed when a peer posted right after it. | Confirmed by reading revision 4's check; the room is a bus for concurrent agents and nothing gives the operator an exclusive window. | The smoke post carries a unique marker (`New-SmokeMarker`). `Assert-SmokeEvent <seq> <agent> <marker>` reads the shared log and requires the row with the returned `seq` to be a broadcast by that agent carrying that marker; `Get-LogRow` throws if the seq is missing or duplicated. Later rows are allowed. The startup check is now "`last_seq` at least `$settled`" plus a row comparison, not equality. Both of Codex's closure cases are in the inert checks, in both shells: wrong bus with an unrelated shared post fails; correct bus with an interleaved peer passes. Used for upgrade and for rollback. |
| R4-02 (P2, Phase 2, present since revision 1) | The bridge parsed numbers with `int()`: `reply_to: 1.9` and `reply_to: true` became 1, so a reply silently joined another thread; `1e999` decoded to infinity and raised an uncaught `OverflowError`, which reached the A2A caller as JSON-RPC `-32603`. | Reproduced on revision 4's `room_bridge.py`: all three, plus `since_seq: 2.7` becoming 2. | `_integer()` accepts a JSON integer or a plain decimal string (the existing `"4"` form) and nothing else: no float, boolean, exponent, sign-in-string, non-ASCII digit, list or object; values beyond 2^53 are out of range; `reply_to` must be at least 1 and `since_seq` at least 0. The text form `read since=N` goes through the same helper. `limit` is still clamped to 1..100. Tests cover the parser and the real A2A HTTP path with zero room calls. |
| R4-03 (P3) | `Assert-OnlyAction` matched the expected name as a substring, so `packages.coordination_room.server_other` passed as `...server`. | Reproduced in Windows PowerShell. | The helper takes the word after the marker and compares it exactly, case-sensitively, keeping the single-action count. A prefixed module and a suffixed PID file now fail. |
| Editorial | "nine acceptance behaviours" was stale; "default behaviour unchanged" did not mention that a no-argument stop gains the bridge in Phase 2. | Both true. | The count is gone from the checklist line; acceptance item 10 and the additive-only constraint now state the one deliberate stop-side addition. |

Codex's stated limits stand and are not claimed here: no clean dependency install, no Linux CI run, no production lifecycle rehearsal, no real `ROLLBACK_COMMIT`, no live Hermes, no load, crash or hostile-concurrency testing.

## Review round 5 (Codex, 2026-10-04): dispositions

Codex hit its usage limit before finishing. What exists: a `REVIEW.md` saved early and still marked "audit in progress", one fully written finding, and the receipts of the checks it had already run. Its closing message and `receipt-hashes.json` were not written. The table separates what Codex concluded from what its receipts show; the second is this author's reading of Codex's files, not Codex's verdict.

| Item | What Codex wrote | What its receipts show | Disposition in revision 6 |
|---|---|---|---|
| R4-01 smoke correlation | "Pending independent execution." | `round-5/deployment-results.json`: 47 cases in each shell, none unexpected. Wrong bus is rejected for upgrade and for rollback; the correct bus with an interleaved peer is accepted; a reused marker at the wrong seq, a duplicated seq, a missing seq and a missing file are rejected; BOMs and wildcard characters in row text are handled. | No change needed for the finding. Three of Codex's characterisation cases showed the helper accepting a non-generated marker (empty, containing `*`, or differing only in case). `Assert-SmokeEvent` now refuses any marker that is not exactly one `New-SmokeMarker` made, and matches it literally and case-sensitively. |
| R4-03 exact preview match | "Pending independent execution." | Same receipt: the prefixed module and the suffixed PID name are rejected, the exact names accepted. | No change. |
| R4-02 number parsing | "Partially closed": fractions, booleans and non-finite values now give the normal error and zero room calls. | `round-5/number-results.json`: 142 parser and 142 HTTP cases; nine unexpected, all the over-limit integer literals of R5-01. | See R5-01. |
| R5-01 (P2, before Phase 2) | A JSON integer literal longer than the interpreter's 4,300-digit limit makes `json.loads` raise plain `ValueError` (not `JSONDecodeError`) before `_integer` runs; the A2A caller gets JSON-RPC `-32603` with the Python message. All three fields, positive and negative, 4,301 and 10,000 digits. | Reproduced here on revision 5's `room_bridge.py`. A sibling Codex did not list reproduced too: deeply nested JSON raises `RecursionError` from the same call. | `_parse_json` turns `ValueError` and `RecursionError` from the decoder into `CommandError`; the interpreter's digit limit is left in place. A command over 32,768 characters is refused before parsing. Because an exception type escaped the executor in two rounds running, it now has a last-resort handler: anything unforeseen ends as the ordinary `error: internal bridge error` artifact with FAILED state, and the traceback goes to the bridge's stderr, never to the caller. Tests cover the parser and the real A2A HTTP path, with zero room calls. |
| Green set | Not written. | `round-5/verification-summary.json`: base, Phase 1 and Phase 2 compared per test case with nothing missing and nothing changed; three failures in every stage, the sandbox ones Codex explained in round 3 (process listing denied, no git index in an archive). | Rerun here for revision 6 (Truth status). |
| Unchanged files | Baseline, rollback checkpoint and Phase 1 are byte-identical to round 4; Phase 2 changes exactly `room_bridge.py` and its two test files. | `round-5/r4-byte-comparison.json` agrees. | Still true for revision 6: the same three files, plus the Deployment helper text. |

Revision 6 has had no independent review. Its delta from revision 5 is the three Phase 2 files above and the marker check in the Deployment helpers; Phase 1 code is unchanged since revision 4.

## Review round 6 (Grok, 2026-10-04): dispositions

The tables for rounds 1 to 5 above describe the revision that answered each finding. Where revision 7 changed such an answer, the row below says so: file digests are gone, the deployment helpers are a file instead of a pasted block, failures are reported in `room_state` instead of only on stderr, and tests no longer use fixed ports.

Two Grok-family reviews of revision 5, saved in `round-6/`: `b-bot-review-r5.md` (four items, with `csrf_probe.py`) and `anotherbot-review-r5.md` (run on Linux at the pushed base `2460c55`, with its own probes and a mutation run). Both verdicts: hold. Every claim that could be checked here was; all of them held.

| Finding | Checked | Disposition in revision 7 |
|---|---|---|
| b-bot 1: the base `4aab13e` is local only; `origin/feat/coordination-room-rebased` is its parent `2460c55`; no pull-request target is named. | `git branch -r --contains 4aab13e` prints nothing. | Task 0 asks the operator to push it and says why the `4aab13e` check matters (the pushed parent lacks the U+2028 fix). Final verification names the target, `feat/coordination-room-rebased`, and refuses a pull request until the base is public. |
| b-bot 2: the A2A bridge answered a request with a foreign `Host` (DNS rebinding) and a foreign `Origin`. | Reproduced against `build_app`: HTTP 200 and the room was called, both ways. | `build_app` now takes only a loopback `Host` (Starlette's `TrustedHostMiddleware`) and refuses any non-loopback `Origin`. Tests cover both and the loopback cases. The room itself: the MCP SDK turns on the same protection for a loopback server; a new test pins that a foreign `Host` is refused there too. |
| b-bot 3: `file:` evidence refs wrote the sha256 of any file under the root, including an untracked `.env`, into a shared log. | True of revisions 2 to 6. | File rows no longer carry a digest: a file ref records existence only. Commit rows keep the full object id, which reveals nothing the repository does not already publish. |
| b-bot 4 and anotherbot's scope note: each round's findings landed in what the previous round added; the plan carries all its code inline; Phase 2 has no consumer. | Fair. This revision is again longer. | Phase 2 is marked deferred by default. Decision 11 recommends the next step be commits and a pull request, not a seventh document review. Dropping evidence lookup from Phase 1 was also suggested; it is kept, with the reason in Decision 5. |
| M1: one post's evidence lookup froze the room for everyone: FastMCP runs a synchronous tool on its event loop. | Confirmed in the installed SDK (`func_metadata.py` calls a sync tool inline). | The tools are coroutines that run the room call on a worker thread. Lookups share a five-second budget, two seconds per commit, and no file is hashed. `test_a_slow_lookup_does_not_stall_other_callers` fails on the old code. |
| M2: after a torn last line the running room appended onto the fragment, a restarted room could not load, and the message said "projection refused". The deployment's own stop is a force-kill. | Reproduced, all three. | `log.py` skips and counts a line it cannot read, starts the next row on its own line, and never rewrites the log. The count is in `room_state` and on the board. Board-path refusal is now its own exception, so a bad log line is no longer reported as an alias. The deployment helpers stay strict: they stop on an unreadable line. |
| M3: every failure signal went to a console nobody sees (`Start-Daemon` launches hidden, with no redirection). | Confirmed in the launcher. | `room_state` reports `board_as_of`, `board_last_error` and `log_skipped_lines`. Deployment checks them. |
| M4: deployment served from the worktree where Phase 2 would be written, and nothing restarts the room after a logon. | Both true: the scheduled task runs the primary checkout's script, which has no room block. | Deployment serves from a detached checkout of one recorded commit (`New-PinnedCheckout`). The logon gap is stated in Deployment and left to the operator (Decision 3); this plan does not change what runs at logon. |
| M5: a claim whose row failed to write stayed in memory; a retry was told `ok`, `seq 0`; others got `conflict`; a restart forgot it. | Reproduced exactly. | A failed append rolls the table back, for claim and for release, and consumes no seq. The gateway returns a JSON error instead of raising. Revisions 2 to 6 had only disclosed this. |
| M6: claims never expire, and the only way to clear one is to send the holder's name. A release of an unheld path still logged a row. | Reproduced. | No expiry is added (that would be new authority). The board shows each claim's age and marks one older than a day `stale?`; the spec and how-to say clearing a dead claim is the operator's call and how it is done; the board says names are not authenticated; a no-op release no longer logs. |
| M7: mutations that survived (a default read limit of 50; `evidence_checked_at` taken after the append); "v0.1 can read v0.2" had no test; the helper harness was not in the plan; deployment steps were manual. | The two survivors were real: no test would have caught either. | Tests for the default limit at room and server level; the timestamp test now pins the order clock, lookup, append; `test_v01_compat.py` runs v0.1 from git against a v0.2 log; the harness and the helpers are files in the package with a test that runs them; `client.py` makes every deployment check a command. |
| M8: the waiver named some files and said "nothing else", while the plan edits more, including a canonical agent-memory source. | True. | Task 0 lists every path, with the agent-memory edit called out. |
| m1: a test's staging file landed outside its temp directory. | Reproduced. | The test uses a directory inside `tmp_path`. |
| m2: `-Only a,b` fails under `-File`; `-Only room ensemble` silently selected `room`. | Reproduced in both shells. | The scripts split a comma list themselves and validate names; positional binding is off, so a second bare name is an error. Tests for both. |
| m3: the plan never ran on Linux; one base test fails there. | Not checkable here. | Task 0 Step 5 and Final verification require it; the reviewer's Linux result is cited as theirs. |
| m4: fixed test ports collide when two harnesses run at once. | True. | Every test this plan adds binds a free port. |
| m5: four internal contradictions. | All four present. | Fixed: the stale "revision 4" sentence, "dot-source" versus "paste" (the helpers are a file now), `_create_mcp` "unchanged", and three versus four line-separator tests. |
| m6: a literal U+2028 in one test body. | Present, and a literal U+FEFF would have followed it. | Both are written as escapes; Task 4 says why. |
| m7: built from `origin`, the branch silently loses the line-separator fix. | Follows from b-bot 1. | Task 0 Step 2 says so. |
| m8: the scripts are checked out with CRLF; the plan's edit blocks are LF. | `git ls-files --eol` confirms `w/crlf`. | Task 2 says how to apply them and what to check afterwards. |
| m9: staging files left by a killed writer; no retention statement; "remove it deliberately". | True. | Leftover staging files are cleared on the next write; Deployment says what stays behind and that nothing is deleted; the helper's message now defers to the operator. |
| m10: schema counts characters where the spec says bytes; upper-case commit hex was unresolved. | True. | Task 1 says which limit is the strict one; upper-case hex is accepted. The schema still allows unknown top-level properties: that is what lets v0.1 and v0.2 rows share a log. |
| m11: the bridge reported a room-side tool error as "did not answer". | True. | It now says the room rejected the call. |
| m12, m13: the board's cost grows with the log; the dependency range resolves above what was measured; no lock file. | The reviewer's measurements are cited in Decision 8. Their clean Linux install resolved `mcp` 1.30.0 and passed. | Recorded. A lock file is a repository-wide matter, not this plan's. |

What the reviewers could not verify, and still nobody has: anything on Windows from their side, anything on Linux from this side, a live deployment, a rollback, Hermes.

## Global Constraints

- **Base branch:** `feat/coordination-room-rebased` (`4aab13e`). Not `feat/coordination-room`.
- **Worktree:** `C:/~shit/FLOSS/.worktrees/room-board-v1`, branch `feat/room-board-v1`. Never implement in `C:/~shit/FLOSS` itself: it is on `feat/coordination-room` with dozens of foreign dirty files.
- **Shells.** A ```` ```bash ```` block runs in Git Bash (`C:\Program Files\Git\bin\bash.exe`). A ```` ```powershell ```` block runs in Windows PowerShell 5.1 or PowerShell 7; the daemon scripts are tested under both. Python commands are written `env -u PYTHONPATH C:/Python313/python.exe ...`; the PowerShell form is `Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue; & C:\Python313\python.exe ...`.
- **Additive only.** The 21 baseline tests stay green and untouched. No existing field, tool name, or argument changes meaning. Rows written by v0.1 load unchanged, and v0.1 code can serve a log this version wrote. `log.py` changes in one way only: it tolerates and counts a line it cannot read. The daemon scripts' default behaviour (no arguments, as the scheduled task runs them) is unchanged in both phases for starting: the same daemons (the bridge is opt-in), the same success lines, the same incomplete-run exits. The no-argument stop gains one thing in Phase 2: it also stops the bridge.
- **Router, not controller.** The room labels evidence. It never rejects a post because of it.
- **Truth labels.** The word "verified" never appears in room output. `resolved` is a lookup result.
- **One writer per surface.** Only the process that owns the daemon slot reads room state from the log and writes `events.jsonl` and `BOARD.md`. Import, construction and a rejected start do neither. A failed `BOARD.md` write never fails the post; it is reported in `room_state`. No code opens an existing file for writing on the board path.
- **Room claims are advisory**, pending the operator's answer in Task 0.
- **No task touches the live bus.** Tasks run tests on scratch ports under temp directories, and the script tests run with stand-in interpreters. Starting, stopping or posting to the real `:7334` or `:7335` happens only in the Deployment section, with its own operator go-ahead. The Task 0 waiver covers file edits on one branch; it is not runtime, merge or governance permission.
- **No materializer runs from the worktree.** Not `materialize_shared_agent_memory.py`, not `refresh_agent_surfaces.py`. A drift report is not an instruction to regenerate.
- **Tests own their environment.** Any fixture that imports the server clears `COORDINATION_ROOM_BOARD` and `FLOSS_AGENT_DIR` and pins root, log and audit under `tmp_path`. Script tests pass a fixed, minimal environment.
- **A2A is optional post/read plumbing.** The bridge never claims or releases a path, binds `127.0.0.1` only, uses `:7335`, authenticates nobody, and is never added to `.mcp.json`.
- **Spec first.** Task 1 lands before any code. `scripts/spec_gate.py --check` is already red on the base (3 lines, listed in Task 0). The criterion is "no new lines", not "exit 0".
- **CI scope.** `packages/` and `scripts/tests/` are inside the required `green-set` job, so every new test must pass on a clean runner. Python tests bind free loopback ports chosen at run time, so two suites can run at once. The script and deployment-helper tests skip off Windows. The required job runs on Linux, where the author has not run this plan (Task 0 Step 5).
- **Lint.** `ruff check --isolated` (ruff's default rules; FLOSS has no ruff configuration and CI does not run ruff), measured with ruff 0.15.11. A newer ruff or a wider rule set reports style findings (RUF100, ISC004, SIM117, TRY004, PLW1510, FURB167, as Codex saw with 0.16.10); those are advisory, not gates.
- **Commits.** `git add -- <paths>` then `git commit -F- -- <paths>` with the message on stdin. Never `git commit -m` after a broad add.

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `docs/specs/coordination-room.spec.md` | Contract, v0.1.0 to v0.2.0 | Replace |
| `docs/specs/coordination-room.schema.json` | Event row schema | Replace |
| `docs/specs/spec-registry.json` | One `irreducible_delta` string | Edit |
| `scripts/start_mcp_daemons.ps1` `scripts/stop_mcp_daemons.ps1` | `-Only` and `-DryRun` (Phase 1); the bridge (Phase 2) | Edit |
| `scripts/tests/test_daemon_scope.py` | Proves the selector touches only what it names | Create |
| `packages/coordination_room/evidence.py` | Look up `file:` and `commit:` refs within a time budget. Pure, no room state. | Create |
| `packages/coordination_room/log.py` | Skip and count an unreadable line; never write onto a torn tail | Replace |
| `packages/coordination_room/board.py` | Topic helpers and the `BOARD.md` projection, with exclusive staging. | Create |
| `packages/coordination_room/room.py` | Topics, threads, evidence, intent, board hook, board-path guard, claim rollback, health in `state()` | Replace |
| `packages/coordination_room/gateway.py` | Pass the new arguments through, add `room_topics`, report a failed write as JSON | Replace |
| `packages/coordination_room/server.py` | Register the new surface, pick `BOARD.md` path, build the room only after ownership, run calls off the event loop | Replace |
| `packages/coordination_room/client.py` | One tool call from a shell, JSON out | Create |
| `packages/coordination_room/deploy.ps1` | Deployment helpers that stop at a failed precondition | Create |
| `packages/coordination_room/README.md` | Tool list | Replace |
| `docs/agent-memory/project/coordination-room-v0.md` | Agent how-to (a canonical memory source; its projections are not regenerated here) | Edit |
| `packages/coordination_room/tests/`: `test_evidence.py` `test_board.py` `test_message_board.py` `test_gateway_board.py` `test_schema.py` `test_v01_compat.py` `test_server_tools.py` `test_server_http.py` `test_deploy_helpers.py`, plus `room_server.py` (helper) and `deploy_harness.ps1` | Tests | Create |
| `requirements-ci.txt` | `mcp>=1.27,<2` (MCP v1 API) | Edit |
| `packages/a2a_mesh/` (6 files) | Merged from `feat/a2a-harness-mesh` | Merge |
| `packages/a2a_mesh/room_bridge.py` | A2A post/read adapter, MCP client of the room | Create |
| `packages/a2a_mesh/tests/test_room_bridge_parse.py` `_pair.py` `_invariants.py` `_e2e.py` | Tests | Create |

Phase 1 is Tasks 0 to 6 and stands on its own. Phase 2 is Tasks 7 to 9 and is deferred by default: nothing uses an A2A bridge yet.

---

## Phase 1: the board

### Task 0: Operator decisions, published base, worktree, baseline

**Files:** none changed in the repo until Step 6.

- [ ] **Step 1: Get three answers in writing.** Ask the operator:
  1. "Coordination-v1 says keep `packages/coordination_room/` unchanged. This plan edits or adds exactly these paths on the branch `feat/room-board-v1`. Approve them?"
     - `packages/coordination_room/`: `log.py`, `room.py`, `gateway.py`, `server.py`, `README.md` (changed); `board.py`, `evidence.py`, `client.py`, `deploy.ps1` (new); eleven files under `tests/` (new: nine test modules, one helper, one PowerShell harness)
     - `scripts/start_mcp_daemons.ps1`, `scripts/stop_mcp_daemons.ps1` (changed); `scripts/tests/test_daemon_scope.py` (new)
     - `docs/specs/coordination-room.spec.md`, `docs/specs/coordination-room.schema.json`, `docs/specs/spec-registry.json` (changed)
     - `requirements-ci.txt` (one line)
     - `docs/agent-memory/project/coordination-room-v0.md` (changed). This is a canonical agent-memory source: once someone regenerates the projections, every harness's instructions for the room change. The plan does not regenerate them.
     - this plan and `docs/reviews/2026-10-02-room-board-v1/` (new)
     - Phase 2 only, if you start it: a merge of `feat/a2a-harness-mesh`, `packages/a2a_mesh/room_bridge.py` and four test files (new), and the same two scripts, test file and how-to again.

     The approval is for those file edits on that branch and nothing else: not deployment, not merging, not Phase 2.
  2. "This plan labels room claims advisory, on the reading that coordination-v1's git-ref claims become the enforced table and the room stays a broadcast log. Confirm, or name the precedence you want."
  3. "The base commit `4aab13e` exists only on this machine; `origin/feat/coordination-room-rebased` is its parent `2460c55`. Will you push it, so the branch has a public base and the pull request a target?"

  Do not start Task 1 without a yes to the first and an answer to the second. Copy the replies verbatim into the body of the Task 1 commit message. If the second answer is anything other than "advisory", stop: the spec text in Task 1 and the board wording in Task 4 need to change first. The third does not block local work, but no pull request is opened until `4aab13e` is on the remote.

- [ ] **Step 2: Create the worktree.**

```bash
cd C:/~shit/FLOSS
git worktree add .worktrees/room-board-v1 -b feat/room-board-v1 feat/coordination-room-rebased
cd .worktrees/room-board-v1
git log --oneline -1
```

Expected: first line starts with `4aab13e`. This check matters: built from `origin` instead, the branch would start at `2460c55`, which lacks the fix that stops a U+2028 in a post from breaking the next load. If git reports a path too long, retry with `git -c core.longpaths=true worktree add ...`.

- [ ] **Step 3: Baseline tests.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests
```

Expected: `21 passed`.

- [ ] **Step 4: Baseline spec gate. Record it, do not fix it.**

```bash
env -u PYTHONPATH C:/Python313/python.exe scripts/spec_gate.py --check
```

Expected (seen by the author, by Codex in rounds 3 to 5, and by a Grok reviewer on Linux): exit 1 with exactly these three findings and nothing else:

```
SPEC-GATE MISSING FLOSS/hooks/grok_pretool_st.py
SPEC-GATE MISSING FLOSS/hooks/grok_session_register.py
SPEC-GATE STALE   FLOSS/scripts/research_log.py (registered but absent — prune or restore)
```

If the findings differ, stop and reconcile before Task 1; later steps compare against this list.

- [ ] **Step 5: Look at the required CI job on the base.** The `green-set` job in `.github/workflows/python-ci.yml` runs on `ubuntu-latest`. This plan's author ran everything on Windows only. A Grok reviewer ran revision 5 on Linux: every new test passed, and one base test, `packages/coordination_room/tests/test_paths.py::test_backslash_collapses_to_same_key`, failed at `2460c55`. Find out whether that job is green on the base before blaming this branch for it.

- [ ] **Step 6: Import this plan and its reviews so the branch carries its own lineage.**

```bash
cp C:/~shit/FLOSS/docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md docs/superpowers/plans/
mkdir -p docs/reviews
cp -r C:/~shit/FLOSS/docs/reviews/2026-10-02-room-board-v1 docs/reviews/
git add -- docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md docs/reviews/2026-10-02-room-board-v1
git commit -F- -- docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md docs/reviews/2026-10-02-room-board-v1 <<'EOF'
docs(plan): coordination room message board v1, revision 7 after six review rounds
EOF
```

---

### Task 1: Spec v0.2.0, schema, registry

**Files:**
- Replace: `docs/specs/coordination-room.spec.md`
- Replace: `docs/specs/coordination-room.schema.json`
- Edit: `docs/specs/spec-registry.json`

**Interfaces:**
- Produces: the field names every later task uses: `topic`, `reply_to`, `thread_id`, `intent`, `evidence_refs`, `evidence_status` (`resolved` | `unresolved`), `evidence_checked_at`, `evidence_checked` (`[{ref, kind, ok, oid?}]`, `kind` in `file` | `commit` | `unknown`).

- [ ] **Step 1: Replace the spec.**

````markdown
# Coordination Room — File-Claim MCP Router and Message Board

```yaml
id: "coordination-room-spec"
version: "0.2.0"
kind: "spec"
status: "Active"
created: "2026-08-30"
updated: "2026-10-04"
truth_status: "v0.1 unit tests Verified on landing; v0.2 Specified until its plan lands"
schema: "coordination-room.schema.json"
approval: "v0.1 operator yes-to-everything 2026-08-30; v0.2 pending operator review"
```

## What this is

A Plane A **router** for concurrent coding agents. File-level room claims plus an append-only message log, exposed as MCP tools. It does not write the claimed files, merge CRDT bytes, or decide truth.

Compose the computer-use **lease shape** (one exclusive holder). Do not share that table. Do not build an AgentOS. No pycrdt (AgentRoom measured coordination tools, not the CRDT, as the load-bearing step).

## Claim unit

Normalized file path relative to the room root. One holder per path inside the room. Same-agent re-claim is idempotent. Second agent gets `conflict` plus the holder id. A claim may carry a short `intent` (max 256 bytes), recorded on the first claim only.

**A room claim is a coordination convention, not write authorization.** ⚠️ Specified: this precedence is pending operator confirmation. No hook consults the room, so nothing stops a write to a path another agent claimed. Where an enforced claim mechanism exists (coordination-v1 proposes `refs/agent-claims/*` checked by the pre-write hook), that mechanism decides and the room does not; the two are not synchronised, and a room claim never implies the enforced one. Inside the room, the claim table, not chat, decides a room conflict: a post to topic `claims` is not a claim.

A claim exists only once its row is in the log. If the write fails, the claim is not held, the caller is told so, and nobody else is refused on its account.

**Claims do not expire.** A session that crashes leaves its claim behind. The board shows each claim's age and marks one older than 24 hours `stale?`; that is a question, not a release. Clearing a dead claim is the operator's call: `room_release` sent with the holder's `agent_id`, followed by a broadcast saying who released it and why. That works because `agent_id` is whatever the caller sends, which is also why it needs saying out loud. Releasing a path nobody holds does nothing and logs nothing.

## Tools

`room_claim` | `room_release` | `room_state` | `room_broadcast` | `room_read` | `room_topics`

- `room_broadcast(agent_id, text, topic?, evidence_refs?, reply_to?)`: no claim required. `text` max 4096 bytes. `topic` defaults to `general`.
- `room_read(since_seq?, topic?, thread_id?, limit?)`: events oldest first. `limit` 0 means all, so a caller written for v0.1 sees the same rows.
- `room_topics()`: topics in use with counts, plus the suggested set.
- `room_state()`: claims, last seq, speakers; the `root`, `log` and `board` paths this room serves; and its health: `board_as_of` (when the board was last written), `board_last_error` (why the last write failed, or null), `log_skipped_lines` (lines of the log it could not read). A caller about to post to what it believes is the shared bus checks `log` first. v0.1 reports claims, last seq and speakers only.

A tool that could not write the log answers `{"ok": false, "error": "log write failed, nothing was recorded: ..."}`. Each tool call runs on a worker thread, so one caller's slow lookup does not hold up the others.

## Topics and threads

A topic is a lowercase slug, `^[a-z0-9][a-z0-9_-]{0,31}$`. Any slug is accepted. Suggested: `announcements`, `claims`, `inquiries`, `general`. Rows written before v0.2 have no topic and read as `general`; claim and release rows read as `claims`.

`reply_to` names an earlier broadcast. The reply takes that row's topic (an explicit different topic is rejected) and records `thread_id`, the seq of the thread's root.

## Evidence refs

`evidence_refs` is up to 16 strings, each `file:<path>` (a regular file under the room root) or `commit:<sha>` (7 to 40 hex chars, either case, naming exactly one commit in the room root's repository). Anything else is `unknown`.

The room looks each ref up once, **before** it appends the row, and records:

- `evidence_status`: `resolved` when every lookup found its object, `unresolved` otherwise;
- `evidence_checked_at`: when the lookup ran;
- `evidence_checked`: one row per ref with `ok`, and for a commit its full object id, `oid`.

A file ref records that the file existed, and nothing about its content: the log is shared, and a hash of an untracked file would publish a fingerprint of it. Cite a commit when the evidence has to be immutable.

One post's lookups share a five-second budget, and a single commit lookup gets at most two. A ref not reached in time is recorded `unresolved`.

**The post is admitted either way.** The room is a router: it labels, readers filter.

`resolved` means the lookup at `evidence_checked_at` found the object. The object can change or vanish before the row is appended and at any time after. It does not mean the claim in the text is true, and the room never writes the word "verified".

## The log

`events.jsonl`, one JSON object per line, appended and never rewritten.

A line the room cannot read (a write torn by a kill, or anything that is not an object with an integer `seq`) is skipped and counted in `log_skipped_lines`; it is never repaired in place. After a torn tail the next row starts on a line of its own. A row that could not be written uses up no seq.

## BOARD.md

`.agent-surface/rooms/default/BOARD.md` is a generated view of the log: room claims (labelled advisory, with their age), the last 20 broadcasts per topic, and agents seen in the 24 hours before the board's own `As of` time. It says that agent names are not authenticated and, if the log has unreadable lines, how many were skipped. It is rewritten after every logged claim, release, and broadcast, and at no other time: not at import, not at construction, not at startup. An idle board is therefore as old as its `As of` line says, and its roster and claim ages are relative to that line, not to now. It is never read back.

A failed board write does not fail the post. It is reported in `room_state` as `board_last_error` (and on the daemon's stderr, which nobody sees: the launcher starts it hidden).

The board is staged in a fresh file created exclusively in the board's directory, then swapped into place by rename; staging files a killed writer left behind are cleared on the next write. No existing file is ever opened for writing, so a hard link aimed at the log, at any name, cannot be truncated through the board. The board path is checked against the log, as the same path or the same file, when the room is built and again before every projection; if it names the log, the room refuses to start, or refuses that projection while the post still lands.

What this covers: any alias present when a projection starts, including a directory on the board's path re-pointed at the log's directory (junction or symlink) after the room started. What it does not cover: something re-pointing a directory between that check and the rename. Keeping the board's directory stable is the operator's part; the default board, `BOARD.md` beside the log, cannot collide with the log by any directory change.

The replaced board takes the permissions its directory gives new files; a per-file ACL set on an earlier `BOARD.md` is not carried over.

## Ownership and lifecycle

The daemon reads the log, caches the next seq and rebuilds the claim table on its **first tool call**, not at import. A tool call can only arrive after the daemon has won its PID slot, and the slot is only won once any previous owner has exited. Importing the server and a rejected duplicate start read and write nothing.

The room is started and stopped through `scripts/start_mcp_daemons.ps1 -Only room` and `scripts/stop_mcp_daemons.ps1 -Only room`. These reuse the scripts' interpreter resolution, log pinning and process-identity check, and leave every other daemon as it is. Several names go in one comma-separated argument (`-Only room,ensemble`); a second bare name is an error. `-DryRun` prints what would happen and does nothing. With no `-Only`, the scripts behave as before this version: the start script starts consensus, ensemble, room and OmniRoute (never the bridge), the stop script stops everything it knows, and each prints its original success line. A bare `python -m packages.coordination_room.server` from a worktree resolves the log under `FLOSS/.worktrees/` and serves a separate, empty bus.

Deployment runs from a detached checkout of one recorded commit, never from a worktree somebody is editing, using `packages/coordination_room/deploy.ps1` (helpers that stop at the first failed precondition) and `python -m packages.coordination_room.client` (one tool call, JSON out).

The room does not survive a logon or reboot by itself. It comes back only if whatever runs at logon points at a checkout whose start script has the room block. That is an operator decision, recorded in the plan.

## A2A bridge

`packages/a2a_mesh/room_bridge.py` lets an A2A caller post and read. It is a client of the room's own MCP tools and never opens the log (one writer per surface). It cannot claim or release a path. Posts are attributed `a2a:<sender>`. That prefix is an attribution label: it stops an A2A caller from appearing under a harness name, and it authenticates nobody. It listens on `127.0.0.1:7335`; `:9900` is Hermes' own A2A listener. It answers only requests whose `Host` is loopback and whose `Origin`, if any, is loopback, so a web page cannot reach it through the browser (DNS rebinding, cross-site POST). The room itself gets the same protection from the MCP SDK. The bridge is not an MCP server and is not added to `.mcp.json`. It starts only when named (`start_mcp_daemons.ps1 -Only bridge`), never from a no-argument start such as the scheduled task; `stop_mcp_daemons.ps1` with no arguments, or with `-Only bridge`, stops it.

## Runtime

- Package: `FLOSS/packages/coordination_room/`
- HTTP: `127.0.0.1:7334/mcp` (PID `coordination_room.pid`)
- Log: `.agent-surface/rooms/default/events.jsonl` (workspace root)
- Board: `.agent-surface/rooms/default/BOARD.md`, beside the log
- SDK: the MCP v1 `FastMCP` API, so `mcp>=1.27,<2`. MCP 2.x has no `mcp.server.fastmcp`; moving to it is separate work.

## Not guaranteed

Do not claim otherwise.

- **Crash durability.** Appends are not fsynced. A row being written when the process is killed can be lost; what is left of it is skipped, not recovered.
- **Exactly-once.** A caller that times out cannot tell whether its post landed. There is no idempotency key.
- **Identity.** `agent_id` is whatever the caller sends, over MCP and over A2A. Anyone on this machine can post, claim or release under any name.
- **Expiry.** Claims never time out.
- **One room object per log.** The daemon loads only after it owns its slot. Two `CoordinationRoom` objects open on one log in any other arrangement (scripts, tests, a second process without the PID guard) will reuse sequence numbers and disagree about claims.

## Falsifiers

Retire if: two holders on one path succeed inside the room; a room conflict is only visible as chat; a claim is reported held that the log never recorded; daemon binds non-loopback; log is rewritten in place; a row is labelled verified, or `resolved` is presented as more than a lookup result; a file's digest is written to the log; BOARD.md is read as a source of state; a process that does not own the daemon slot reads state from or writes to the log or the board; a board write replaces or truncates the log through an alias present when the projection starts; an unreadable log line stops the room from starting; one caller's lookup stalls the others; a room-only lifecycle command touches another daemon; the A2A bridge writes the log, claims a path, or answers a non-loopback Host or Origin; a room claim is presented as write authorization.
````

- [ ] **Step 2: Replace the schema.** Its `maxLength` values count characters; the room's own limits (4096 and 256) count UTF-8 bytes and are the stricter ones.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "floss://specs/coordination-room.schema.json",
  "title": "Coordination room event",
  "description": "One append-only JSONL line in the coordination-room event log.",
  "type": "object",
  "required": [
    "seq",
    "ts",
    "type",
    "agent_id"
  ],
  "properties": {
    "seq": {
      "type": "integer",
      "minimum": 1
    },
    "ts": {
      "type": "string"
    },
    "type": {
      "enum": [
        "claim",
        "release",
        "broadcast"
      ]
    },
    "agent_id": {
      "type": "string",
      "minLength": 1
    },
    "path": {
      "type": "string"
    },
    "text": {
      "type": "string",
      "maxLength": 4096,
      "description": "The room caps this at 4096 UTF-8 bytes; maxLength here counts characters and is the looser bound."
    },
    "intent": {
      "type": "string",
      "maxLength": 256,
      "description": "The room caps this at 256 UTF-8 bytes; maxLength here counts characters."
    },
    "topic": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9_-]{0,31}$"
    },
    "reply_to": {
      "type": "integer",
      "minimum": 1
    },
    "thread_id": {
      "type": "integer",
      "minimum": 1
    },
    "evidence_refs": {
      "type": "array",
      "maxItems": 16,
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 512
      }
    },
    "evidence_status": {
      "enum": [
        "resolved",
        "unresolved"
      ]
    },
    "evidence_checked_at": {
      "type": "string"
    },
    "evidence_checked": {
      "type": "array",
      "maxItems": 16,
      "items": {
        "type": "object",
        "required": [
          "ref",
          "kind",
          "ok"
        ],
        "additionalProperties": false,
        "properties": {
          "ref": {
            "type": "string"
          },
          "kind": {
            "enum": [
              "file",
              "commit",
              "unknown"
            ]
          },
          "ok": {
            "type": "boolean"
          },
          "oid": {
            "type": "string",
            "pattern": "^[0-9a-f]{40,64}$"
          }
        }
      }
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "type": {
            "const": "broadcast"
          }
        }
      },
      "then": {
        "required": [
          "text"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "type": {
            "enum": [
              "claim",
              "release"
            ]
          }
        }
      },
      "then": {
        "required": [
          "path"
        ]
      }
    },
    {
      "if": {
        "required": [
          "reply_to"
        ]
      },
      "then": {
        "required": [
          "thread_id",
          "topic"
        ]
      }
    },
    {
      "if": {
        "required": [
          "evidence_refs"
        ]
      },
      "then": {
        "required": [
          "evidence_status",
          "evidence_checked",
          "evidence_checked_at"
        ]
      }
    }
  ]
}
```

- [ ] **Step 3: Edit the registry.** In `docs/specs/spec-registry.json`, in the `FLOSS/docs/specs/coordination-room.schema.json` entry, replace this exact string (it occurs once):

```
"irreducible_delta": "Event types claim|release|broadcast with optional path/text. No new schema language."
```

with:

```
"irreducible_delta": "Event types claim|release|broadcast with optional path/text/intent plus topic, reply_to, thread_id and evidence fields on broadcast. No new schema language."
```

Keep the file's existing line endings.

- [ ] **Step 4: Validate the JSON and the gate.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -c "import json; [json.load(open(p, encoding='utf-8')) for p in ('docs/specs/coordination-room.schema.json', 'docs/specs/spec-registry.json')]; print('json ok')"
env -u PYTHONPATH C:/Python313/python.exe scripts/spec_gate.py --check
```

Expected: `json ok`, then the same three findings as Task 0 Step 4 and no others.

- [ ] **Step 5: Commit** (put the operator's replies from Task 0 Step 1 in the message body).

```bash
git add -- docs/specs/coordination-room.spec.md docs/specs/coordination-room.schema.json docs/specs/spec-registry.json
git commit -F- -- docs/specs/coordination-room.spec.md docs/specs/coordination-room.schema.json docs/specs/spec-registry.json <<'EOF'
docs(specs): coordination room v0.2.0, topics, threads and evidence labels

Operator approval of the paths this branch edits (coordination-v1 said keep packages/coordination_room unchanged): <paste verbatim>
Operator answer on room-claim precedence: <paste verbatim>
EOF
```

---

### Task 2: Room-only lifecycle in the existing daemon scripts

**Files:**
- Edit: `scripts/start_mcp_daemons.ps1`
- Edit: `scripts/stop_mcp_daemons.ps1`
- Test: `scripts/tests/test_daemon_scope.py`
- Must stay green, unchanged: `packages/tests/test_mcp_daemon.py` (it checks each script's success line and that an incomplete run exits 1 before it)

**Interfaces:**
- Produces: `start_mcp_daemons.ps1 [-Only <names>] [-DryRun]` and the same for `stop_mcp_daemons.ps1`. Names are `consensus`, `ensemble`, `room`, `omniroute`; several go in one comma-separated argument (`-Only room,ensemble`), because under `powershell -File` that is how a list arrives. An unknown name exits 2; a second bare name (`-Only room ensemble`) is a binding error. Default `-Only` is all four, so the scheduled task's argument-free run is unchanged, including its original success line (`Daemons started (consensus ...` / `All daemons stopped. PID files cleaned.`); a run with `-Only` prints a line naming what it selected instead. `-DryRun` prints `[FLOSS MCP] WOULD_START <module> (<label>)` / `[FLOSS MCP] WOULD_STOP <pidfile> (...)` and starts or stops nothing. When the room is selected, the start script prints `[FLOSS MCP] coordination room log: <path> (root <checkout>)`.
- Consumes: everything the scripts already do: interpreter resolution, `$flossAgent` from `FLOSS_AGENT_DIR`, the log pin for worktree checkouts, `Start-Daemon`, and the stop script's `mcp_daemon --check-identity` / `--reclaim-claim` path.

This lands before any room code changes, so the commit it produces is the rollback point: v0.1 room code with a room-only lifecycle. Record its hash. It also stands alone: it can be its own pull request.

The selector reuses each script's existing logic rather than adding a parallel path. Two behaviours to know: the start script still runs the read-only OmniRoute identity check when OmniRoute is not selected (it then leaves OmniRoute alone), and the stop script's read-only agentmemory report still prints.

**Line endings.** These two scripts are stored with LF and checked out with CRLF (`.gitattributes`: `text eol=crlf`). The edit blocks below are printed with LF. Apply them with a tool that matches regardless of line ending and writes CRLF back. Afterwards `git ls-files --eol scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1` must still say `w/crlf`, and `git diff --stat` must show only these two files.

- [ ] **Step 1: Write the failing test.** It runs the scripts with a fixed environment in which a launch is harmless even if a dry run regressed: `FLOSS_PYTHON` is `where.exe`, `PATH` is System32 only, and `FLOSS_AGENT_DIR` is an empty temp directory.

```python
"""Dry-run tests for `-Only` on start_mcp_daemons.ps1 and stop_mcp_daemons.ps1.

Review round 2 (R2-02, R2-03): a room deployment must touch only the room,
through the scripts' own interpreter, path and identity handling.

Nothing is started or stopped. -DryRun returns before any launch or kill, and
the environment makes a regression harmless as well: FLOSS_PYTHON is
where.exe, PATH holds only System32 (no `omniroute`, no `python`), and
FLOSS_AGENT_DIR is an empty temp directory, so no PID file names a process.

Production change that would make these fail: `-Only room` starting or
stopping anything besides the room, a dry run reaching a launch, the default
selection dropping a daemon the scheduled task relies on, or the room log
resolving somewhere other than the workspace intake mouth.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows daemon scripts")

FLOSS_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = FLOSS_ROOT / "scripts"
SYSTEM_ROOT = Path(os.environ.get("SystemRoot", r"C:\Windows"))
SYSTEM32 = SYSTEM_ROOT / "System32"
SHELLS = [exe for exe in (shutil.which("powershell"), shutil.which("pwsh")) if exe]
ROOM = "[FLOSS MCP] WOULD_START packages.coordination_room.server (coordination room (:7334))"


def _intake_log() -> str:
    # Same rule as the launcher: a checkout under FLOSS\.worktrees\<name> pins
    # the log three levels up, any other checkout one level up.
    root = FLOSS_ROOT
    intake = root.parent.parent.parent if "\\.worktrees\\" in str(root).lower() else root.parent
    return str(intake / ".agent-surface" / "rooms" / "default" / "events.jsonl")


def _run(shell: str, script: str, *args: str, agent_dir: Path) -> subprocess.CompletedProcess:
    env = {
        "SystemRoot": str(SYSTEM_ROOT),
        "PATH": f"{SYSTEM32};{SYSTEM32 / 'WindowsPowerShell' / 'v1.0'}",
        "FLOSS_AGENT_DIR": str(agent_dir),
        "FLOSS_PYTHON": str(SYSTEM32 / "where.exe"),
        "USERPROFILE": str(agent_dir),
        "TEMP": str(agent_dir),
        "TMP": str(agent_dir),
    }
    return subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(SCRIPTS / script), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


def _lines(done: subprocess.CompletedProcess, marker: str) -> list[str]:
    return [line.strip() for line in done.stdout.splitlines() if marker in line]


shells = pytest.mark.parametrize(
    "shell", SHELLS or [pytest.param("", marks=pytest.mark.skip(reason="no PowerShell"))]
)


@shells
def test_start_only_room_considers_nothing_but_the_room(shell: str, tmp_path: Path):
    done = _run(shell, "start_mcp_daemons.ps1", "-Only", "room", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _lines(done, "WOULD_START") == [ROOM]
    assert "OmniRoute not selected (-Only)" in done.stdout
    assert f"coordination room log: {_intake_log()}" in done.stdout
    assert "nothing was started (selected: room)" in done.stdout


@shells
def test_start_default_still_considers_every_daemon(shell: str, tmp_path: Path):
    done = _run(shell, "start_mcp_daemons.ps1", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    starts = _lines(done, "WOULD_START")
    assert [s.split()[3] for s in starts] == [
        "packages.metacoordinator_mcp.server",
        "packages.reasoning_ensemble.mcp_server",
        "packages.coordination_room.server",
        "omniroute",
    ]


@shells
def test_stop_only_room_considers_nothing_but_the_room(shell: str, tmp_path: Path):
    done = _run(shell, "stop_mcp_daemons.ps1", "-Only", "room", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert _lines(done, "WOULD_STOP") == [
        "[FLOSS MCP] WOULD_STOP coordination_room.pid (only if its identity check says OURS)"
    ]
    assert "OmniRoute not selected (-Only)" in done.stdout
    assert "nothing was stopped (selected: room)" in done.stdout


@shells
def test_stop_default_still_considers_every_daemon(shell: str, tmp_path: Path):
    done = _run(shell, "stop_mcp_daemons.ps1", "-DryRun", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert [s.split()[3] for s in _lines(done, "WOULD_STOP")] == [
        "consensus.pid",
        "reasoning_ensemble.pid",
        "coordination_room.pid",
        "omniroute",
    ]


@shells
def test_real_stop_only_room_leaves_other_records_alone(shell: str, tmp_path: Path):
    """Not a dry run. The room has no record here, so nothing is stopped; the
    point is that the other daemons' records are neither acted on nor changed."""
    others = {"consensus.pid": "4242", "reasoning_ensemble.pid": "4243", "omniroute.pid": "4244"}
    for name, value in others.items():
        (tmp_path / name).write_text(value, encoding="ascii")
    done = _run(shell, "stop_mcp_daemons.ps1", "-Only", "room", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert {p.name: p.read_text(encoding="ascii") for p in tmp_path.glob("*.pid")} == others
    assert "Stopped: room." in done.stdout


@shells
def test_real_start_only_room_attempts_only_the_room(shell: str, tmp_path: Path):
    """Not a dry run. FLOSS_PYTHON is where.exe, so the one launch attempted
    exits at once and is reported; no other launch is attempted."""
    (tmp_path / "consensus.pid").write_text("4242", encoding="ascii")
    done = _run(shell, "start_mcp_daemons.ps1", "-Only", "room", agent_dir=tmp_path)
    assert done.returncode == 1, done.stdout + done.stderr
    assert "coordination room (:7334) exited immediately" in done.stdout
    for other in ("consensus gateway", "reasoning ensemble", "OmniRoute started", "WOULD_START"):
        assert other not in done.stdout
    assert (tmp_path / "consensus.pid").read_text(encoding="ascii") == "4242"
    # A failed selected start reports itself and claims no success.
    assert "STARTUP INCOMPLETE" in done.stdout
    assert "Started or already running" not in done.stdout
    assert "Daemons started" not in done.stdout


@shells
def test_real_stop_with_no_arguments_keeps_its_original_success_line(shell: str, tmp_path: Path):
    """Review round 3, R3-01: the scheduled-task style run (no -Only) still
    prints the line packages/tests/test_mcp_daemon.py expects, because every
    daemon was selected and none had a record to act on."""
    done = _run(shell, "stop_mcp_daemons.ps1", agent_dir=tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    assert "All daemons stopped. PID files cleaned." in done.stdout


@shells
def test_several_names_go_in_one_comma_separated_argument(shell: str, tmp_path: Path):
    """Review round 6 (Grok), m2: under `-File`, `-Only a,b` arrives as one
    string. It must select both, not be rejected."""
    start = _run(shell, "start_mcp_daemons.ps1", "-Only", "room,ensemble", "-DryRun", agent_dir=tmp_path)
    assert start.returncode == 0, start.stdout + start.stderr
    assert [s.split()[3] for s in _lines(start, "WOULD_START")] == [
        "packages.reasoning_ensemble.mcp_server",
        "packages.coordination_room.server",
    ]
    stop = _run(shell, "stop_mcp_daemons.ps1", "-Only", "room,ensemble", "-DryRun", agent_dir=tmp_path)
    assert [s.split()[3] for s in _lines(stop, "WOULD_STOP")] == [
        "reasoning_ensemble.pid",
        "coordination_room.pid",
    ]


@shells
@pytest.mark.parametrize("script", ["start_mcp_daemons.ps1", "stop_mcp_daemons.ps1"])
def test_a_second_bare_name_is_an_error_not_a_silent_drop(shell: str, script: str, tmp_path: Path):
    """`-Only room ensemble` used to act on `room` alone and say nothing."""
    done = _run(shell, script, "-Only", "room", "ensemble", "-DryRun", agent_dir=tmp_path)
    assert done.returncode != 0
    assert "WOULD_" not in done.stdout


@shells
@pytest.mark.parametrize("script", ["start_mcp_daemons.ps1", "stop_mcp_daemons.ps1"])
def test_unknown_daemon_name_is_refused_before_anything_runs(shell: str, script: str, tmp_path: Path):
    done = _run(shell, script, "-Only", "everything", "-DryRun", agent_dir=tmp_path)
    assert done.returncode != 0
    assert "WOULD_" not in done.stdout
```

- [ ] **Step 2: Run it to see it fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q scripts/tests/test_daemon_scope.py
```

Expected: most tests fail (no `WOULD_START` lines, extra launches attempted). Running this before the edit is safe: the base scripts have no `param()` block, so they ignore the unknown arguments and run for real, but every launch is `where.exe`, which exits at once, and the empty agent directory gives the stop script nothing to act on.

- [ ] **Step 3: Edit `start_mcp_daemons.ps1`.** Seven edits, each old string occurs once.

Edit 1. Replace:

```powershell
#   schtasks /Create /TN "FLOSS-MCP-Daemons" /TR "powershell -WindowStyle Hidden -File C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1" /SC ONLOGON /RU "MSI\kalis" /RL LIMITED /F

# Derive everything from where THIS script lives. The hardcoded
```

with:

```powershell
#   schtasks /Create /TN "FLOSS-MCP-Daemons" /TR "powershell -WindowStyle Hidden -File C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1" /SC ONLOGON /RU "MSI\kalis" /RL LIMITED /F
#
# -Only picks which daemons to start (default: all, so the scheduled task is
# unchanged). A room deployment runs `-Only room`, so a daemon someone stopped
# on purpose stays stopped. Several names go in one comma-separated argument
# (`-Only room,ensemble`). -DryRun prints WOULD_START lines and starts nothing.

[CmdletBinding(PositionalBinding = $false)]
param(
    [string[]]$Only = @('consensus', 'ensemble', 'room', 'omniroute'),
    [switch]$DryRun
)

# Checked here, not by ValidateSet: under `powershell -File` (the scheduled task
# and the deployment helpers) `-Only a,b` arrives as the one string "a,b", which
# ValidateSet would reject. PositionalBinding is off so that `-Only room ensemble`
# is an error, not a silent selection of `room` alone.
$knownDaemons = @('consensus', 'ensemble', 'room', 'omniroute')
$Only = @($Only | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$unknownDaemons = @($Only | Where-Object { $knownDaemons -cnotcontains $_ })
if ($Only.Count -eq 0 -or $unknownDaemons.Count -gt 0) {
    Write-Host "[FLOSS MCP] -Only takes: $($knownDaemons -join ', '). Not understood: $($unknownDaemons -join ', ')"
    exit 2
}

# Derive everything from where THIS script lives. The hardcoded
```

Edit 2. Replace:

```powershell
    param([string]$Interpreter, [string]$Module, [string]$Label, [string]$WorkDir)

    $proc = Start-Process
```

with:

```powershell
    param([string]$Interpreter, [string]$Module, [string]$Label, [string]$WorkDir)

    if ($DryRun) {
        Write-Host "[FLOSS MCP] WOULD_START $Module ($Label)"
        return $true
    }
    $proc = Start-Process
```

Edit 3. Replace:

```powershell
$consensusProc = Start-Daemon $py "packages.metacoordinator_mcp.server" "consensus gateway (:7331)" $workspace
if (-not $consensusProc) { $skipped += "consensus gateway (:7331) - exited immediately after launch" }
```

with:

```powershell
if ($Only -contains 'consensus') {
    $consensusProc = Start-Daemon $py "packages.metacoordinator_mcp.server" "consensus gateway (:7331)" $workspace
    if (-not $consensusProc) { $skipped += "consensus gateway (:7331) - exited immediately after launch" }
}
```

Edit 4. Replace:

```powershell
$ensembleProc = Start-Daemon $py "packages.reasoning_ensemble.mcp_server" "reasoning ensemble (:7332)" $workspace
if (-not $ensembleProc) { $skipped += "reasoning ensemble (:7332) - exited immediately after launch" }
```

with:

```powershell
if ($Only -contains 'ensemble') {
    $ensembleProc = Start-Daemon $py "packages.reasoning_ensemble.mcp_server" "reasoning ensemble (:7332)" $workspace
    if (-not $ensembleProc) { $skipped += "reasoning ensemble (:7332) - exited immediately after launch" }
}
```

Edit 5. Replace:

```powershell
$intakeRoot = if ($workspace -match '\\.worktrees\\') {
    Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $workspace))
} else {
    Split-Path -Parent $workspace
}
$env:COORDINATION_ROOM_LOG = Join-Path $intakeRoot '.agent-surface\rooms\default\events.jsonl'
$env:COORDINATION_ROOM_ROOT = $workspace
$roomProc = Start-Daemon $py "packages.coordination_room.server" "coordination room (:7334)" $workspace
if (-not $roomProc) { $skipped += "coordination room (:7334) - exited immediately after launch" }
```

with:

```powershell
if ($Only -contains 'room') {
    $intakeRoot = if ($workspace -match '\\.worktrees\\') {
        Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $workspace))
    } else {
        Split-Path -Parent $workspace
    }
    $env:COORDINATION_ROOM_LOG = Join-Path $intakeRoot '.agent-surface\rooms\default\events.jsonl'
    $env:COORDINATION_ROOM_ROOT = $workspace
    Write-Host "[FLOSS MCP] coordination room log: $env:COORDINATION_ROOM_LOG (root $workspace)"
    $roomProc = Start-Daemon $py "packages.coordination_room.server" "coordination room (:7334)" $workspace
    if (-not $roomProc) { $skipped += "coordination room (:7334) - exited immediately after launch" }
}
```

Edit 6. Replace:

```powershell
if ($omniVerdict -eq 'UNKNOWN' -and (Test-Path $omniPid) -and $omniIsReservation) {
```

with:

```powershell
if ($Only -notcontains 'omniroute') {
    Write-Host "[FLOSS MCP] OmniRoute not selected (-Only) - left as it is"
} elseif ($DryRun) {
    Write-Host "[FLOSS MCP] WOULD_START omniroute (or find it already running)"
} elseif ($omniVerdict -eq 'UNKNOWN' -and (Test-Path $omniPid) -and $omniIsReservation) {
```

Edit 7. Replace:

```powershell
Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, coordination room :7334, omniroute :20128). PID guard prevents duplicates."
```

with:

```powershell
# The default run keeps its original success line, word for word: it is
# still exactly true, and packages/tests/test_mcp_daemon.py checks that it is
# emitted only after the $skipped guard above.
if ($DryRun) {
    Write-Host "[FLOSS MCP] Dry run: nothing was started (selected: $($Only -join ', '))."
} elseif (-not $PSBoundParameters.ContainsKey('Only')) {
    Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, coordination room :7334, omniroute :20128). PID guard prevents duplicates."
} else {
    Write-Host "[FLOSS MCP] Started or already running: $($Only -join ', '). PID guard prevents duplicates."
}
```

- [ ] **Step 4: Edit `stop_mcp_daemons.ps1`.** Four edits, each old string occurs once.

Edit 1. Replace:

```powershell
# Removes PID files so next start is clean.

# Same resolution mcp_daemon.py uses when it WRITES these files
```

with:

```powershell
# Removes PID files so next start is clean.
#
# -Only picks which daemons to stop (default: all), through the same identity
# check as a full stop. A room deployment runs `-Only room`. Several names go in
# one comma-separated argument. -DryRun prints WOULD_STOP lines and stops nothing.

[CmdletBinding(PositionalBinding = $false)]
param(
    [string[]]$Only = @('consensus', 'ensemble', 'room', 'omniroute'),
    [switch]$DryRun
)

# Checked here, not by ValidateSet: under `powershell -File` (the scheduled task
# and the deployment helpers) `-Only a,b` arrives as the one string "a,b", which
# ValidateSet would reject. PositionalBinding is off so that `-Only room ensemble`
# is an error, not a silent selection of `room` alone.
$knownDaemons = @('consensus', 'ensemble', 'room', 'omniroute')
$Only = @($Only | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$unknownDaemons = @($Only | Where-Object { $knownDaemons -cnotcontains $_ })
if ($Only.Count -eq 0 -or $unknownDaemons.Count -gt 0) {
    Write-Host "[FLOSS MCP] -Only takes: $($knownDaemons -join ', '). Not understood: $($unknownDaemons -join ', ')"
    exit 2
}

# Same resolution mcp_daemon.py uses when it WRITES these files
```

Edit 2. Replace:

```powershell
$pidFiles = @("consensus.pid", "reasoning_ensemble.pid", "coordination_room.pid")
foreach ($pidFile in $pidFiles) {
    $pidPath = Join-Path $flossAgent $pidFile
```

with:

```powershell
$pidFileFor = [ordered]@{
    consensus = 'consensus.pid'
    ensemble  = 'reasoning_ensemble.pid'
    room      = 'coordination_room.pid'
}
$pidFiles = @($pidFileFor.Keys | Where-Object { $Only -contains $_ } | ForEach-Object { $pidFileFor[$_] })
foreach ($pidFile in $pidFiles) {
    $pidPath = Join-Path $flossAgent $pidFile
    if ($DryRun) {
        Write-Host "[FLOSS MCP] WOULD_STOP $pidFile (only if its identity check says OURS)"
        continue
    }
```

Edit 3. Replace:

```powershell
if ($omniVerdict -eq 'OURS') {
```

with:

```powershell
if ($Only -notcontains 'omniroute') {
    Write-Host "[FLOSS MCP] OmniRoute not selected (-Only) - left as it is"
} elseif ($DryRun) {
    Write-Host "[FLOSS MCP] WOULD_STOP omniroute (only if its identity check says OURS)"
} elseif ($omniVerdict -eq 'OURS') {
```

Edit 4. Replace:

```powershell
Write-Host "[FLOSS MCP] All daemons stopped. PID files cleaned."
```

with:

```powershell
# The default run keeps its original success line, word for word: with no
# -Only every daemon was selected, so it is still exactly true, and
# packages/tests/test_mcp_daemon.py checks it.
if ($DryRun) {
    Write-Host "[FLOSS MCP] Dry run: nothing was stopped (selected: $($Only -join ', '))."
} elseif (-not $PSBoundParameters.ContainsKey('Only')) {
    Write-Host "[FLOSS MCP] All daemons stopped. PID files cleaned."
} else {
    Write-Host "[FLOSS MCP] Stopped: $($Only -join ', '). PID files cleaned."
}
```

- [ ] **Step 5: Run the test and parse-check under both shells.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q scripts/tests/test_daemon_scope.py
```

```powershell
foreach ($f in 'scripts/start_mcp_daemons.ps1', 'scripts/stop_mcp_daemons.ps1') { $e = $null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $f), [ref]$null, [ref]$e) | Out-Null; "$f errors: $($e.Count)" }
```

Expected: `24 passed` (twelve cases under each of `powershell` and `pwsh`; fewer if only one shell is installed); both scripts `errors: 0` in each shell.

Then the existing script tests, which this task must not break:

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/tests/test_mcp_daemon.py
```

Expected: no failures.

- [ ] **Step 6: Commit, and record the hash as the rollback point.**

```bash
git add -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 scripts/tests/test_daemon_scope.py
git commit -F- -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 scripts/tests/test_daemon_scope.py <<'EOF'
feat(daemons): -Only and -DryRun on the start and stop scripts

Default behaviour is unchanged. `-Only room` touches nothing but the room,
through the scripts' own interpreter, log pin and identity checks.
This commit is the room rollback point: v0.1 room code, room-only lifecycle.
EOF
git rev-parse HEAD
```

Write the printed hash into the pull request description as `ROLLBACK_COMMIT`.

---

### Task 3: Evidence lookup

**Files:**
- Create: `packages/coordination_room/evidence.py`
- Test: `packages/coordination_room/tests/test_evidence.py`

**Interfaces:**
- Produces: `resolve_ref(root: Path, ref: str, timeout=COMMIT_TIMEOUT_SECONDS) -> dict` returning `{"ref", "kind", "ok"}` plus `"oid"` for a resolved commit (a file row never carries a digest); `resolve_all(root: Path, refs: list[str] | None) -> tuple[str, list[dict]]` returning `(status, checked)` with status `none` | `resolved` | `unresolved`, raising `ValueError` on a malformed list; constants `MAX_REFS = 16`, `REF_MAX = 512`, `COMMIT_TIMEOUT_SECONDS = 2.0`, `LOOKUP_BUDGET_SECONDS = 5.0`.
- Consumes: `normalize_path`, `PathEscape` from `packages/coordination_room/paths.py`.

- [ ] **Step 1: Write the failing test.**

```python
"""RED tests for evidence-ref resolution.

Production change that would make these fail: a ref outside the room root
resolving, a bare string guessed into a file or commit, `resolved` reported
while any ref is unresolved, a file's digest written into the shared log, or
one post's lookups running past their time budget.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room import evidence  # noqa: E402
from packages.coordination_room.evidence import resolve_all, resolve_ref  # noqa: E402


def test_no_refs_is_none(tmp_path: Path):
    assert resolve_all(tmp_path, None) == ("none", [])
    assert resolve_all(tmp_path, []) == ("none", [])


def test_file_ref_inside_root_resolves_and_publishes_no_digest(tmp_path: Path):
    """A hash of an untracked file, a `.env` for one, would put a fingerprint
    of it into a log every agent reads. Existence is all a file ref records."""
    (tmp_path / ".env").write_bytes(b"TOKEN=hunter2")
    status, checked = resolve_all(tmp_path, ["file:.env"])
    assert status == "resolved"
    assert checked == [{"ref": "file:.env", "kind": "file", "ok": True}]


def test_missing_file_is_unresolved(tmp_path: Path):
    status, checked = resolve_all(tmp_path, ["file:nope.md"])
    assert status == "unresolved"
    assert checked == [{"ref": "file:nope.md", "kind": "file", "ok": False}]


def test_file_outside_root_is_unresolved_even_if_it_exists(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    assert resolve_ref(root, "file:../outside.txt")["ok"] is False


def test_directory_is_not_a_file(tmp_path: Path):
    (tmp_path / "d").mkdir()
    assert resolve_ref(tmp_path, "file:d")["ok"] is False


def test_bare_ref_is_unknown_and_unresolved(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    row = resolve_ref(tmp_path, "a.md")
    assert row == {"ref": "a.md", "kind": "unknown", "ok": False}


def test_one_bad_ref_makes_the_set_unresolved(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    status, checked = resolve_all(tmp_path, ["file:a.md", "file:nope.md"])
    assert status == "unresolved"
    assert [c["ok"] for c in checked] == [True, False]


@pytest.mark.parametrize(
    "refs",
    ["file:a.md", [""], [3], ["x"] * 17, ["x" * 513]],
    ids=["not-a-list", "empty-string", "not-a-string", "too-many", "too-long"],
)
def test_malformed_refs_raise(tmp_path: Path, refs):
    with pytest.raises(ValueError):
        resolve_all(tmp_path, refs)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_commit_ref_resolves_only_real_commits_and_pins_the_full_oid(tmp_path: Path):
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    sha = subprocess.run(
        [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert resolve_ref(tmp_path, f"commit:{sha}") == {
        "ref": f"commit:{sha}",
        "kind": "commit",
        "ok": True,
        "oid": sha,
    }
    # A short sha is stored with the full object id it named at lookup time.
    assert resolve_ref(tmp_path, f"commit:{sha[:7]}")["oid"] == sha
    # git accepts upper-case hex; so does the room.
    assert resolve_ref(tmp_path, f"commit:{sha.upper()}")["oid"] == sha
    missing = resolve_ref(tmp_path, "commit:" + "0" * 40)
    assert missing == {"ref": "commit:" + "0" * 40, "kind": "commit", "ok": False}
    # Not hex: never reaches git, so it cannot be read as an option.
    assert resolve_ref(tmp_path, "commit:--help")["ok"] is False


def test_a_slow_commit_lookup_is_unresolved_not_an_error(tmp_path: Path, monkeypatch):
    def too_slow(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=kwargs["timeout"])

    monkeypatch.setattr(evidence.subprocess, "run", too_slow)
    assert resolve_ref(tmp_path, "commit:" + "a" * 40) == {
        "ref": "commit:" + "a" * 40,
        "kind": "commit",
        "ok": False,
    }


def test_lookups_past_the_budget_are_skipped_not_waited_for(tmp_path: Path, monkeypatch):
    """Sixteen commit refs at the per-ref timeout would hold a caller for half
    a minute. Once the post's budget is spent, the rest are recorded unresolved
    without asking git at all; a file check costs nothing and still runs."""
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    calls = []
    monkeypatch.setattr(evidence, "LOOKUP_BUDGET_SECONDS", 0.0)
    monkeypatch.setattr(evidence.subprocess, "run", lambda *a, **k: calls.append(a) or 1 / 0)
    status, checked = resolve_all(tmp_path, ["commit:" + "a" * 40, "file:a.md"])
    assert calls == []
    assert status == "unresolved"
    assert [c["ok"] for c in checked] == [False, True]
```

- [ ] **Step 2: Run it to see it fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_evidence.py
```

Expected: collection error, `ImportError` naming `evidence`.

- [ ] **Step 3: Write the implementation.**

```python
"""Symbolic evidence-ref resolution. A lookup result, not a verdict: no claim is verified here."""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any

from packages.coordination_room.paths import PathEscape, normalize_path

MAX_REFS = 16
REF_MAX = 512
COMMIT_TIMEOUT_SECONDS = 2.0
# One post's lookups share this budget. Refs not reached in time are recorded
# as unresolved rather than making the caller wait.
LOOKUP_BUDGET_SECONDS = 5.0
_SHA = re.compile(r"[0-9a-f]{7,40}")
_OID = re.compile(r"[0-9a-f]{40,64}")


def _file_row(root: Path, ref: str) -> dict[str, Any]:
    """`ok` if a regular file under root. No digest: the log is shared, and a
    hash of an untracked file (a `.env`, say) would publish a fingerprint of
    it. Cite a commit when the evidence must be immutable."""
    row: dict[str, Any] = {"ref": ref, "kind": "file", "ok": False}
    try:
        row["ok"] = (root / normalize_path(root, ref[5:])).is_file()
    except (PathEscape, OSError):
        row["ok"] = False
    return row


def _commit_row(root: Path, ref: str, timeout: float) -> dict[str, Any]:
    """`ok` if the sha names exactly one commit; `oid` is its full object id."""
    row: dict[str, Any] = {"ref": ref, "kind": "commit", "ok": False}
    sha = ref[7:].lower()
    if not _SHA.fullmatch(sha) or timeout <= 0:
        return row
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return row
    oid = done.stdout.strip()
    if done.returncode == 0 and _OID.fullmatch(oid):
        row["ok"] = True
        row["oid"] = oid
    return row


def resolve_ref(root: Path, ref: str, timeout: float = COMMIT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """`file:<path>` and `commit:<sha>` resolve; anything else is `unknown`."""
    if ref.startswith("file:"):
        return _file_row(root, ref)
    if ref.startswith("commit:"):
        return _commit_row(root, ref, timeout)
    return {"ref": ref, "kind": "unknown", "ok": False}


def resolve_all(
    root: Path, refs: list[str] | None
) -> tuple[str, list[dict[str, Any]]]:
    """Return (status, checked). status is none | resolved | unresolved."""
    if refs is None:
        return "none", []
    if not isinstance(refs, list) or not all(
        isinstance(r, str) and r.strip() for r in refs
    ):
        raise ValueError("evidence_refs must be a list of non-empty strings")
    if not refs:
        return "none", []
    if len(refs) > MAX_REFS:
        raise ValueError(f"evidence_refs exceeds {MAX_REFS} entries")
    if any(len(r.strip()) > REF_MAX for r in refs):
        raise ValueError(f"evidence ref exceeds {REF_MAX} characters")
    deadline = time.monotonic() + LOOKUP_BUDGET_SECONDS
    checked = [
        resolve_ref(
            root, r.strip(), min(COMMIT_TIMEOUT_SECONDS, deadline - time.monotonic())
        )
        for r in refs
    ]
    status = "resolved" if all(c["ok"] for c in checked) else "unresolved"
    return status, checked
```

- [ ] **Step 4: Run it to see it pass.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests
```

Expected: no failures; measured `36 passed` (21 baseline + 15 new). The commit-ref test skips if `git` is not on `PATH`.

- [ ] **Step 5: Commit.**

```bash
git add -- packages/coordination_room/evidence.py packages/coordination_room/tests/test_evidence.py
git commit -F- -- packages/coordination_room/evidence.py packages/coordination_room/tests/test_evidence.py <<'EOF'
feat(coordination-room): look up file and commit evidence refs within a time budget
EOF
```

---

### Task 4: BOARD.md projection and topic helpers

**Files:**
- Create: `packages/coordination_room/board.py`
- Test: `packages/coordination_room/tests/test_board.py`

**Interfaces:**
- Produces: `DEFAULT_TOPIC = "general"`, `SUGGESTED_TOPICS`, `CLAIM_STALE_AFTER`, `check_topic(topic) -> str` (raises `ValueError`), `topic_of(event) -> str`, `topic_summary(events) -> list[dict]`, `live_claims(events) -> dict[str, dict]`, `render_board(events, now=None, skipped=0) -> str`, `write_board(path, events, now=None, skipped=0) -> None` (raises `OSError`; clears leftover staging files, stages through `tempfile.mkstemp` in `path.parent`, then `os.replace`).

`render_board` is a function of the log **and** `now`: the roster window and the claim ages are relative to `now`, which is why the board prints it.

- [ ] **Step 1: Write the failing test.** Note the escape `"\u2028"` in one test: it must stay an escape. A literal U+2028 pasted there turns into a newline or a space in many editors.

```python
"""RED tests for the BOARD.md projection.

Production change that would make these fail: a released claim still listed,
an unresolved evidence ref rendered as resolved, a pipe or newline in message
text breaking the claims table, a board with no as-of time (so a stale roster
reads as current), room claims presented as write authorization, or staging
through a predictable file name that a hard link could aim at the log.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.board import (  # noqa: E402
    render_board,
    topic_of,
    topic_summary,
    write_board,
)

NOW = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)
ROSTER = "## Agents seen in the 24h before "


def _event(seq: int, kind: str, agent: str, ts: str = "2026-10-02T11:00:00Z", **fields):
    return {"seq": seq, "ts": ts, "type": kind, "agent_id": agent, **fields}


def test_board_states_its_as_of_time_and_seq():
    events = [_event(4, "broadcast", "a", text="x", topic="general")]
    board = render_board(events, NOW)
    assert "As of: 2026-10-02T12:00:00Z, seq 4." in board
    assert ROSTER + "2026-10-02T12:00:00Z" in board


def test_claims_are_labelled_advisory_not_authorization():
    board = render_board([_event(1, "claim", "grok", path="a.py")], NOW)
    assert "## Room claims (advisory)" in board
    assert "not write authorization" in board


def test_active_claim_row_shows_owner_and_intent():
    events = [_event(1, "claim", "grok", path="a.py", intent="fix the | pipe")]
    board = render_board(events, NOW)
    assert "| a.py | grok | 2026-10-02T11:00:00Z | 1h | fix the \\| pipe |" in board


def test_released_claim_is_absent():
    events = [
        _event(1, "claim", "grok", path="a.py"),
        _event(2, "release", "grok", path="a.py"),
    ]
    board = render_board(events, NOW)
    assert "a.py" not in board
    claims = board.split("## Room claims (advisory)")[1].split("## Messages by topic")[0]
    assert claims.rstrip().endswith("None.")


def test_messages_group_by_topic_and_legacy_rows_read_as_general():
    events = [
        _event(1, "broadcast", "grok", text="legacy row, no topic"),
        _event(2, "broadcast", "claude", text="shipped", topic="announcements"),
    ]
    board = render_board(events, NOW)
    assert board.index("### #announcements") < board.index("### #general")
    assert "- #1 2026-10-02T11:00:00Z **grok**: legacy row, no topic" in board
    assert "**claude**: shipped" in board


def test_evidence_tags_never_say_verified():
    events = [
        _event(
            1, "broadcast", "a", text="ok", topic="general",
            evidence_refs=["file:x.md"], evidence_status="resolved",
        ),
        _event(
            2, "broadcast", "b", text="bad", topic="general",
            evidence_refs=["file:y.md"], evidence_status="unresolved",
        ),
    ]
    board = render_board(events, NOW)
    assert "[evidence resolved] (refs: file:x.md)" in board
    assert "[evidence UNRESOLVED] (refs: file:y.md)" in board
    assert "VERIFIED" not in board.upper()


def test_reply_marks_parent():
    events = [
        _event(1, "broadcast", "a", text="q?", topic="inquiries"),
        _event(2, "broadcast", "b", text="a.", topic="inquiries", reply_to=1, thread_id=1),
    ]
    assert "**b** re #1: a." in render_board(events, NOW)


def test_newlines_and_unicode_separators_in_text_are_flattened():
    events = [_event(1, "broadcast", "a", text="one\ntwo\u2028three", topic="general")]
    board = render_board(events, NOW)
    assert "one two three" in board


def test_long_text_is_truncated():
    events = [_event(1, "broadcast", "a", text="x" * 1000, topic="general")]
    rows = render_board(events, NOW).split("\n")
    line = next(row for row in rows if row.startswith("- #1"))
    assert line.endswith("...")
    assert len(line) < 400


def test_roster_window_excludes_stale_agents():
    events = [
        _event(1, "broadcast", "old", ts="2026-10-01T11:59:00Z", text="x", topic="general"),
        _event(2, "broadcast", "fresh", ts="2026-10-02T11:30:00Z", text="y", topic="general"),
    ]
    roster = render_board(events, NOW).split(ROSTER)[1]
    assert "fresh" in roster
    assert "old" not in roster


def test_same_log_rendered_after_an_idle_day_drops_the_roster_and_says_when():
    events = [_event(1, "broadcast", "a", ts="2026-10-02T11:30:00Z", text="x", topic="general")]
    fresh = render_board(events, NOW)
    idle = render_board(events, NOW + timedelta(hours=24, minutes=31))
    assert "- a (last 2026-10-02T11:30:00Z)" in fresh.split(ROSTER)[1]
    assert idle.split(ROSTER)[1].strip().endswith("None.")
    assert "As of: 2026-10-03T12:31:00Z, seq 1." in idle
    # The board on disk is whichever of these was written last: its own header
    # is the only thing that says how old the roster is.
    assert fresh != idle


def test_topic_of_derives_claims_for_claim_and_release_rows():
    assert topic_of({"type": "claim"}) == "claims"
    assert topic_of({"type": "release"}) == "claims"
    assert topic_of({"type": "broadcast"}) == "general"
    assert topic_of({"type": "broadcast", "topic": "inquiries"}) == "inquiries"


def test_topic_summary_counts_and_last_seq():
    events = [
        _event(1, "claim", "a", path="p"),
        _event(2, "broadcast", "a", text="x", topic="general"),
        _event(3, "broadcast", "a", text="y", topic="general"),
    ]
    assert topic_summary(events) == [
        {"topic": "claims", "count": 1, "last_seq": 1},
        {"topic": "general", "count": 2, "last_seq": 3},
    ]


def test_write_board_replaces_atomically_and_leaves_no_staging_file(tmp_path: Path):
    target = tmp_path / "rooms" / "BOARD.md"
    write_board(target, [_event(1, "broadcast", "a", text="x", topic="general")], NOW)
    first = target.read_text(encoding="utf-8")
    write_board(target, [], NOW)
    assert target.read_text(encoding="utf-8") != first
    assert [p.name for p in target.parent.iterdir()] == ["BOARD.md"]
    assert "\r" not in target.read_text(encoding="utf-8")


def test_a_hard_link_at_the_old_staging_name_is_never_opened(tmp_path: Path):
    """Review round 2, R2-01: a predictable `BOARD.md.tmp` hard-linked to the log
    was opened for writing and truncated the log."""
    log = tmp_path / "events.jsonl"
    log.write_bytes(b'{"seq": 1}\n')
    os.link(log, tmp_path / "BOARD.md.tmp")
    write_board(tmp_path / "BOARD.md", [], NOW)
    assert log.read_bytes() == b'{"seq": 1}\n'


def test_a_board_replaced_by_a_hard_link_to_the_log_loses_only_its_name(tmp_path: Path):
    """An alias created after any construction-time check: the swap replaces the
    directory entry, so the log keeps its bytes."""
    log = tmp_path / "events.jsonl"
    log.write_bytes(b'{"seq": 1}\n')
    board = tmp_path / "BOARD.md"
    os.link(log, board)
    write_board(board, [_event(1, "broadcast", "a", text="x", topic="general")], NOW)
    assert log.read_bytes() == b'{"seq": 1}\n'
    assert board.read_text(encoding="utf-8").startswith("# Coordination board")


def test_an_old_claim_is_questioned_not_expired():
    """Review round 6 (Grok), M6: claims never expire, and a crashed session's
    claim looked exactly like a live one."""
    events = [
        _event(1, "claim", "gone", ts="2026-09-30T09:00:00Z", path="old.py"),
        _event(2, "claim", "here", ts="2026-10-02T11:30:00Z", path="new.py"),
    ]
    board = render_board(events, NOW)
    assert "| old.py | gone | 2026-09-30T09:00:00Z | 2d 3h, stale? |" in board
    assert "| new.py | here | 2026-10-02T11:30:00Z | 0h |" in board
    assert "Claims do not expire" in board


def test_board_says_names_are_not_authenticated():
    assert "Nothing authenticates them." in render_board([], NOW)


def test_skipped_log_lines_are_announced_on_the_board():
    assert "could not be read" not in render_board([], NOW)
    assert "**2 line(s) in the log could not be read and were skipped.**" in render_board(
        [], NOW, skipped=2
    )


def test_a_staging_file_left_by_a_killed_writer_is_cleared(tmp_path: Path):
    target = tmp_path / "BOARD.md"
    leftover = tmp_path / ".BOARD.md.abc123.tmp"
    leftover.write_text("half a board", encoding="utf-8")
    unrelated = tmp_path / "notes.tmp"
    unrelated.write_text("keep", encoding="utf-8")
    write_board(target, [], NOW)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["BOARD.md", "notes.tmp"]
```

- [ ] **Step 2: Run it to see it fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_board.py
```

Expected: collection error, `ModuleNotFoundError: No module named 'packages.coordination_room.board'`.

- [ ] **Step 3: Write the implementation.**

```python
"""BOARD.md projection: a view of the event log as of a stated time, never a source of truth."""

from __future__ import annotations

import glob
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_TOPIC = "general"
SUGGESTED_TOPICS = ("announcements", "claims", "inquiries", "general")
RECENT_PER_TOPIC = 20
ROSTER_WINDOW = timedelta(hours=24)
# A claim never expires. Past this age the board asks the question; it does
# not answer it.
CLAIM_STALE_AFTER = timedelta(hours=24)
SNIPPET_MAX = 280

_TOPIC = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def check_topic(topic: str) -> str:
    if not isinstance(topic, str) or not _TOPIC.fullmatch(topic):
        raise ValueError(f"topic must match {_TOPIC.pattern}")
    return topic


def topic_of(event: dict[str, Any]) -> str:
    """Stored topic, else derived: claim/release rows live under `claims`."""
    stored = event.get("topic")
    if stored:
        return str(stored)
    return "claims" if event.get("type") in ("claim", "release") else DEFAULT_TOPIC


def topic_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for event in events:
        row = seen.setdefault(topic_of(event), {"topic": topic_of(event), "count": 0})
        row["count"] += 1
        row["last_seq"] = int(event["seq"])
    return [seen[name] for name in sorted(seen)]


def live_claims(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    held: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("type") == "claim":
            held[event["path"]] = event
        elif event.get("type") == "release":
            held.pop(event["path"], None)
    return held


def _parse_ts(value: Any) -> datetime | None:
    try:
        return datetime.strptime(value, _TS_FORMAT).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _cell(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _snippet(text: str) -> str:
    flat = " ".join(text.split())
    if len(flat) <= SNIPPET_MAX:
        return flat
    return flat[: SNIPPET_MAX - 3] + "..."


def _age(claimed: Any, now: datetime) -> str:
    stamp = _parse_ts(claimed)
    if stamp is None:
        return "unknown"
    age = max(now - stamp, timedelta(0))
    hours = int(age.total_seconds() // 3600)
    text = f"{hours // 24}d {hours % 24}h" if hours >= 24 else f"{hours}h"
    return f"{text}, stale?" if age > CLAIM_STALE_AFTER else text


def _evidence_suffix(event: dict[str, Any]) -> str:
    status = event.get("evidence_status")
    refs = event.get("evidence_refs")
    tag = {"resolved": " [evidence resolved]", "unresolved": " [evidence UNRESOLVED]"}
    suffix = tag.get(status, "")
    if refs:
        suffix += " (refs: " + ", ".join(_snippet(str(r)) for r in refs) + ")"
    return suffix


def render_board(
    events: list[dict[str, Any]], now: datetime | None = None, skipped: int = 0
) -> str:
    """Render the board as of `now`. The roster and claim ages depend on `now`,
    not only on the log. `skipped` is the log's count of unusable lines."""
    now = now or datetime.now(timezone.utc)
    as_of = now.strftime(_TS_FORMAT)
    last_seq = events[-1]["seq"] if events else 0
    out = [
        "# Coordination board",
        "",
        "<!-- Generated from events.jsonl by packages/coordination_room/board.py. "
        "A view, not a record: edits are overwritten on the next room event. -->",
        "",
        f"As of: {as_of}, seq {last_seq}. Rewritten only when the room logs an event, "
        "so an idle board is as old as this line says.",
        "",
        "Agent names are whatever each caller sent. Nothing authenticates them.",
        "",
    ]
    if skipped:
        out += [
            f"**{skipped} line(s) in the log could not be read and were skipped.** "
            "Rows may be missing from this view; `room_state` reports the same count.",
            "",
        ]
    out += [
        "## Room claims (advisory)",
        "",
        "A room claim records who said they are editing a path. It is a convention, "
        "not write authorization. Claims do not expire: an old one may belong to a "
        "session that is gone.",
        "",
    ]
    claims = live_claims(events)
    if claims:
        out += ["| Path | Owner | Since | Age | Intent |", "|---|---|---|---|---|"]
        for path in sorted(claims):
            row = claims[path]
            out.append(
                f"| {_cell(path)} | {_cell(row['agent_id'])} | {_cell(row.get('ts', ''))} "
                f"| {_age(row.get('ts'), now)} | {_cell(row.get('intent', ''))} |"
            )
    else:
        out.append("None.")

    out += ["", "## Messages by topic", ""]
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("type") == "broadcast":
            by_topic.setdefault(topic_of(event), []).append(event)
    if not by_topic:
        out += ["None.", ""]
    for topic in sorted(by_topic):
        out += [f"### #{topic}", ""]
        for event in by_topic[topic][-RECENT_PER_TOPIC:]:
            reply = f" re #{event['reply_to']}" if event.get("reply_to") else ""
            out.append(
                f"- #{event['seq']} {event.get('ts', '')} "
                f"**{_cell(event['agent_id'])}**{reply}{_evidence_suffix(event)}: "
                f"{_snippet(event.get('text', ''))}"
            )
        out.append("")

    out += [f"## Agents seen in the 24h before {as_of}", ""]
    last_seen: dict[str, str] = {}
    for event in events:
        stamp = _parse_ts(event.get("ts"))
        if stamp is not None and now - stamp <= ROSTER_WINDOW:
            last_seen[event["agent_id"]] = event["ts"]
    if last_seen:
        out += [f"- {_cell(name)} (last {last_seen[name]})" for name in sorted(last_seen)]
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def write_board(
    path: Path,
    events: list[dict[str, Any]],
    now: datetime | None = None,
    skipped: int = 0,
) -> None:
    """Replace `path` atomically. Raises OSError; the caller decides it is non-fatal.

    The staging file is created fresh with O_EXCL by mkstemp, never opened by a
    predictable name: a pre-existing file at a fixed name (say, a hard link to
    the event log) would be truncated by the open. os.replace then swaps the
    directory entry, so even a `path` that is itself a hard link to the log
    loses only its name, never the log's bytes.
    """
    text = render_board(events, now, skipped)
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = f".{path.name}."
    # The room is the only writer, so any staging file already here was left by
    # a writer that was killed between creating it and the swap.
    for leftover in path.parent.glob(f"{glob.escape(prefix)}*.tmp"):
        try:
            leftover.unlink()
        except OSError:
            pass
    fd, staged = tempfile.mkstemp(dir=path.parent, prefix=prefix, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(staged, path)
    except OSError:
        Path(staged).unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Run it to see it pass.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests
```

Expected: no failures; measured `56 passed`.

- [ ] **Step 5: Commit.**

```bash
git add -- packages/coordination_room/board.py packages/coordination_room/tests/test_board.py
git commit -F- -- packages/coordination_room/board.py packages/coordination_room/tests/test_board.py <<'EOF'
feat(coordination-room): BOARD.md as a dated view of the event log, staged exclusively
EOF
```

---

### Task 5: Log, room and gateway

**Files:**
- Replace: `packages/coordination_room/log.py`
- Replace: `packages/coordination_room/room.py`
- Replace: `packages/coordination_room/gateway.py`
- Test: `packages/coordination_room/tests/test_message_board.py`, `test_gateway_board.py`, `test_schema.py`, `test_v01_compat.py`

**Interfaces:**
- Consumes: Task 3 `resolve_all`; Task 4 `check_topic`, `topic_of`, `topic_summary`, `write_board`, `DEFAULT_TOPIC`, `SUGGESTED_TOPICS`.
- Produces: `EventLog.load()` skipping and counting unreadable lines in `EventLog.skipped`; `EventLog.append()` starting a fresh line after a torn tail and consuming a seq only when the row is written. `BoardPathError(ValueError)`; `check_board_path(log_path, board_path) -> None` (raises `BoardPathError` when the board names the log by path or by file identity; opens nothing); `CoordinationRoom(root, log_path, board_path=None)` (calls `check_board_path`; writes nothing at construction); `.claim(agent_id, path, intent="")` and `.release(agent_id, path)`, each leaving the table as it was if the append raises `OSError`, and `.release` of an unheld path returning ok without a row; `.broadcast(agent_id, text, *, topic=None, evidence_refs=None, reply_to=None)` returning `{"ok", "seq", "topic"[, "evidence_status"]}`; `.read(since_seq=0, *, topic=None, thread_id=None, limit=0)`; `.topics()`; `.state()` returning `claims`, `last_seq`, `speakers`, `root`, `log`, `board`, `board_as_of`, `board_last_error`, `log_skipped_lines`. `CoordinationRoomTools(root, log_path, room=None, board_path=None)` with `room_claim`, `room_release`, `room_broadcast`, `room_read`, `room_topics`, `room_state`; a failed log write comes back as `{"ok": false, "error": "log write failed, nothing was recorded: ..."}`.

The three source files are small, so they are replaced whole. `log.py` changes for the first time in this plan: review round 6 showed a torn last line (the deployment's own stop is a force-kill) made the next append run onto the fragment and stopped a restarted room from loading at all. `room.py` drops the unused `ClaimConflict` import that `ruff` flags on the base. Replay still handles only `claim` and `release`.

`test_v01_compat.py` loads v0.1 from git commit `4aab13e` and runs it against a log this version wrote. It skips where that commit is unavailable (a shallow clone).

- [ ] **Step 1: Write the failing tests.**

```python
"""RED tests for topics, threads, evidence and the BOARD.md hook on CoordinationRoom.

Production change that would make these fail: an unresolved ref rejecting the
post (the room labels, it does not gate), a reply landing in another topic, a
default `limit` silently truncating old callers, a failed board write failing
the post, a board path that can replace the log, or construction writing the
board before the caller owns the daemon slot.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import packages.coordination_room.room as room_module  # noqa: E402
from packages.coordination_room.log import EventLog  # noqa: E402
from packages.coordination_room.room import CoordinationRoom  # noqa: E402


def _room(tmp_path: Path, board: bool = False) -> CoordinationRoom:
    return CoordinationRoom(
        root=tmp_path,
        log_path=tmp_path / "events.jsonl",
        board_path=(tmp_path / "BOARD.md") if board else None,
    )


def test_plain_broadcast_defaults_to_general(tmp_path: Path):
    room = _room(tmp_path)
    result = room.broadcast("grok", "hello")
    assert result == {"ok": True, "seq": 1, "topic": "general"}
    assert room.read()[0]["topic"] == "general"


@pytest.mark.parametrize("topic", ["Bad Topic", "", "-x", "a" * 33, "UPPER"])
def test_bad_topic_is_rejected_and_nothing_is_logged(tmp_path: Path, topic: str):
    room = _room(tmp_path)
    with pytest.raises(ValueError):
        room.broadcast("grok", "hi", topic=topic)
    assert room.read() == []


def test_reply_inherits_topic_and_thread(tmp_path: Path):
    room = _room(tmp_path)
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    first = room.broadcast("b", "a1", reply_to=root)
    second = room.broadcast("c", "a2", reply_to=first["seq"])
    events = {e["seq"]: e for e in room.read()}
    assert first["topic"] == "inquiries"
    assert events[first["seq"]]["thread_id"] == root
    assert events[second["seq"]]["thread_id"] == root
    assert events[second["seq"]]["reply_to"] == first["seq"]


def test_reply_with_mismatched_topic_is_rejected(tmp_path: Path):
    room = _room(tmp_path)
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    with pytest.raises(ValueError, match="parent topic"):
        room.broadcast("b", "a1", topic="general", reply_to=root)


def test_reply_to_unknown_or_non_broadcast_is_rejected(tmp_path: Path):
    room = _room(tmp_path)
    claim = room.claim("a", "x.py")["seq"]
    with pytest.raises(ValueError, match="not a broadcast"):
        room.broadcast("b", "hi", reply_to=claim)
    with pytest.raises(ValueError, match="not a broadcast"):
        room.broadcast("b", "hi", reply_to=99)


def test_unresolved_evidence_is_labelled_not_rejected(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    room = _room(tmp_path)
    good = room.broadcast("a", "done", evidence_refs=["file:proof.md"])
    bad = room.broadcast("a", "done", evidence_refs=["file:missing.md"])
    plain = room.broadcast("a", "no refs")
    assert good["evidence_status"] == "resolved"
    assert bad["evidence_status"] == "unresolved"
    assert "evidence_status" not in plain
    rows = {e["seq"]: e for e in room.read()}
    assert rows[bad["seq"]]["evidence_checked"] == [
        {"ref": "file:missing.md", "kind": "file", "ok": False}
    ]
    assert rows[good["seq"]]["evidence_checked"] == [
        {"ref": "file:proof.md", "kind": "file", "ok": True}
    ]
    assert "evidence_refs" not in rows[plain["seq"]]
    assert "evidence_checked_at" not in rows[plain["seq"]]


def test_label_describes_the_lookup_and_says_when_it_ran(tmp_path: Path, monkeypatch):
    """The file can vanish between the lookup and the append. The row must not
    claim more than "this is what the lookup saw, at this time": the time is
    read before the lookup, and the lookup runs before the append. (An
    earlier version of this test compared timestamps at one-second
    resolution and could not fail.)"""
    proof = tmp_path / "proof.md"
    proof.write_text("x", encoding="utf-8")
    order = []
    real_lookup, real_append = room_module.resolve_all, EventLog.append

    def clock():
        order.append("clock")
        return "2001-01-01T00:00:00Z"

    def lookup_then_remove(root, refs):
        order.append("lookup")
        result = real_lookup(root, refs)
        proof.unlink()
        return result

    def append(self, *args, **fields):
        order.append("append")
        return real_append(self, *args, **fields)

    monkeypatch.setattr(room_module, "_utc_now", clock)
    monkeypatch.setattr(room_module, "resolve_all", lookup_then_remove)
    monkeypatch.setattr(EventLog, "append", append)
    room = _room(tmp_path)
    room.broadcast("a", "done", evidence_refs=["file:proof.md"])
    row = room.read()[0]
    assert not proof.exists()
    assert row["evidence_status"] == "resolved"
    assert row["evidence_checked_at"] == "2001-01-01T00:00:00Z"
    assert order == ["clock", "lookup", "append"]


def test_read_filters_by_topic_thread_and_limit(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("a", "x.py")
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "noise")
    room.broadcast("c", "a1", reply_to=root)
    assert [e["seq"] for e in room.read(topic="inquiries")] == [2, 4]
    assert [e["seq"] for e in room.read(topic="claims")] == [1]
    assert [e["seq"] for e in room.read(thread_id=root)] == [2, 4]
    assert [e["seq"] for e in room.read(limit=2)] == [1, 2]
    assert [e["seq"] for e in room.read(since_seq=2, limit=1)] == [3]
    assert len(room.read()) == 4


def test_legacy_rows_without_topic_read_as_general(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    EventLog(path).append("broadcast", "grok", text="old")
    room = CoordinationRoom(root=tmp_path, log_path=path)
    assert [e["text"] for e in room.read(topic="general")] == ["old"]
    assert room.topics()["topics"] == [{"topic": "general", "count": 1, "last_seq": 1}]


def test_topics_lists_counts_and_suggestions(tmp_path: Path):
    room = _room(tmp_path)
    room.broadcast("a", "x", topic="announcements")
    room.broadcast("a", "y")
    out = room.topics()
    assert [t["topic"] for t in out["topics"]] == ["announcements", "general"]
    assert out["suggested"] == ["announcements", "claims", "inquiries", "general"]


def test_claim_intent_is_logged_once_and_capped(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py", intent="  refactor  ")
    room.claim("grok", "a.py", intent="ignored on idempotent re-claim")
    rows = room.read()
    assert len(rows) == 1
    assert rows[0]["intent"] == "refactor"
    with pytest.raises(ValueError, match="intent exceeds"):
        room.claim("grok", "b.py", intent="x" * 257)


def test_claim_without_intent_logs_the_same_row_as_before(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py")
    row = room.read()[0]
    assert "intent" not in row
    assert set(row) == {"seq", "ts", "type", "agent_id", "path"}


def test_state_names_the_bus_it_serves(tmp_path: Path):
    state = _room(tmp_path, board=True).state()
    assert Path(state["root"]) == tmp_path.resolve()
    assert state["log"] == str(tmp_path / "events.jsonl")
    assert state["board"] == str(tmp_path / "BOARD.md")
    assert (state["board_as_of"], state["board_last_error"], state["log_skipped_lines"]) == (
        None,
        None,
        0,
    )
    assert _room(tmp_path).state()["board"] is None


def test_construction_writes_no_board(tmp_path: Path):
    """Building a room is what a duplicate daemon does before it loses the PID
    guard. It must not touch the board."""
    first = _room(tmp_path, board=True)
    board = tmp_path / "BOARD.md"
    assert not board.exists()
    first.broadcast("grok", "hello board")
    before = (board.read_bytes(), board.stat().st_mtime_ns)
    _room(tmp_path, board=True)
    assert (board.read_bytes(), board.stat().st_mtime_ns) == before


def test_board_is_rewritten_on_every_mutation(tmp_path: Path):
    room = _room(tmp_path, board=True)
    board = tmp_path / "BOARD.md"
    room.claim("grok", "a.py", intent="work")
    assert "| a.py | grok |" in board.read_text(encoding="utf-8")
    room.release("grok", "a.py")
    assert "a.py" not in board.read_text(encoding="utf-8")
    room.broadcast("grok", "hello board", topic="announcements")
    assert "hello board" in board.read_text(encoding="utf-8")
    board.unlink()
    _room(tmp_path, board=True).broadcast("grok", "after restart")
    text = board.read_text(encoding="utf-8")
    assert "hello board" in text and "after restart" in text


@pytest.mark.parametrize("board_name", ["events.jsonl", "EVENTS.JSONL"])
def test_board_path_that_is_the_log_is_refused_before_any_write(tmp_path: Path, board_name: str):
    log = tmp_path / "events.jsonl"
    EventLog(log).append("broadcast", "grok", text="keep me")
    before = log.read_bytes()
    if board_name != "events.jsonl" and not sys.platform.startswith("win"):
        pytest.skip("a case-distinct name is a different file off Windows")
    with pytest.raises(ValueError, match="event log"):
        CoordinationRoom(root=tmp_path, log_path=log, board_path=tmp_path / board_name)
    assert log.read_bytes() == before


def test_board_hard_linked_to_the_log_is_refused(tmp_path: Path):
    """Review round 2, R2-01: distinct path strings, one file."""
    log = tmp_path / "events.jsonl"
    EventLog(log).append("broadcast", "grok", text="keep me")
    before = log.read_bytes()
    os.link(log, tmp_path / "BOARD.md")
    with pytest.raises(ValueError, match="event log"):
        CoordinationRoom(root=tmp_path, log_path=log, board_path=tmp_path / "BOARD.md")
    assert log.read_bytes() == before


def test_hard_link_to_the_log_at_the_old_staging_name_survives_posts(tmp_path: Path):
    """Review round 2, R2-01, end to end: construction passes (the board path is
    a real, separate file), and posting must not truncate the log through the
    link."""
    log = tmp_path / "events.jsonl"
    EventLog(log).append("broadcast", "grok", text="keep me")
    os.link(log, tmp_path / "BOARD.md.tmp")
    room = _room(tmp_path, board=True)
    assert room.broadcast("grok", "second")["seq"] == 2
    assert [e["text"] for e in CoordinationRoom(root=tmp_path, log_path=log).read()] == [
        "keep me",
        "second",
    ]


def _link_directory(target: Path, link: Path) -> None:
    """A directory alias: a symlink where allowed, else an NTFS junction."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if sys.platform.startswith("win"):
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
        return
    pytest.skip("cannot create a directory alias here")


def test_board_directory_re_pointed_at_the_log_after_startup_is_refused(tmp_path: Path, capsys):
    """Review round 3, R3-02: board `alias/events.jsonl`, log `real/events.jsonl`.
    After construction, `alias` is replaced by a link to `real`, so the stored
    board path now names the log. The next projection must refuse, not replace
    the log with Markdown."""
    real, alias = tmp_path / "real", tmp_path / "alias"
    real.mkdir()
    alias.mkdir()
    log = real / "events.jsonl"
    room = CoordinationRoom(root=tmp_path, log_path=log, board_path=alias / "events.jsonl")
    room.broadcast("grok", "first")
    alias.rename(tmp_path / "alias-original")
    _link_directory(real, alias)
    assert room.broadcast("grok", "second")["seq"] == 2
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").split("\n") if line]
    assert [r["text"] for r in rows] == ["first", "second"]
    assert "BOARD.md projection refused" in capsys.readouterr().err


def test_board_failure_does_not_fail_the_post(tmp_path: Path, capsys):
    # board_path is a directory: os.replace raises OSError on every platform.
    # A directory inside tmp_path, so the staging file stays inside it too.
    blocked = tmp_path / "adir"
    blocked.mkdir()
    room = CoordinationRoom(
        root=tmp_path, log_path=tmp_path / "events.jsonl", board_path=blocked
    )
    result = room.broadcast("grok", "still logged")
    assert result["ok"] is True
    # The daemon's stderr goes to a hidden console; the state is where a
    # caller can see that the board is not being written.
    assert room.state()["board_last_error"].startswith("failed at ")
    assert room.state()["board_as_of"] is None
    assert [p.name for p in tmp_path.iterdir() if p.name.endswith(".tmp")] == []
    rows = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").split("\n")
        if line
    ]
    assert rows[0]["text"] == "still logged"
    assert "BOARD.md projection failed" in capsys.readouterr().err


def test_board_health_is_visible_in_state_and_recovers(tmp_path: Path):
    room = _room(tmp_path, board=True)
    room.broadcast("grok", "one")
    healthy = room.state()
    assert healthy["board_as_of"] is not None and healthy["board_last_error"] is None
    board = tmp_path / "BOARD.md"
    board.unlink()
    board.mkdir()  # now the swap cannot succeed
    room.broadcast("grok", "two")
    assert room.state()["board_last_error"].startswith("failed at ")
    board.rmdir()
    room.broadcast("grok", "three")
    assert room.state()["board_last_error"] is None
    assert "three" in board.read_text(encoding="utf-8")


def _fail_next_append(monkeypatch) -> None:
    real = EventLog.append
    state = {"failed": False}

    def append(self, *args, **fields):
        if not state["failed"]:
            state["failed"] = True
            raise OSError(28, "No space left on device")
        return real(self, *args, **fields)

    monkeypatch.setattr(EventLog, "append", append)


def test_a_claim_whose_row_was_not_written_does_not_exist(tmp_path: Path, monkeypatch):
    """Review round 6 (Grok), M5: the table was set before the append, so after
    a failed write a retry was told "ok, seq 0", others got "conflict", and a
    restart forgot the claim."""
    room = _room(tmp_path)
    _fail_next_append(monkeypatch)
    with pytest.raises(OSError):
        room.claim("grok", "a.py")
    assert room.state()["claims"] == {}
    assert room.claim("claude", "a.py")["seq"] == 1
    assert [e["agent_id"] for e in room.read()] == ["claude"]


def test_a_release_whose_row_was_not_written_keeps_the_holder(tmp_path: Path, monkeypatch):
    room = _room(tmp_path)
    room.claim("grok", "a.py")
    _fail_next_append(monkeypatch)
    with pytest.raises(OSError):
        room.release("grok", "a.py")
    assert room.state()["claims"] == {"a.py": "grok"}
    assert room.release("grok", "a.py")["seq"] == 2


def test_releasing_a_path_nobody_holds_adds_no_row(tmp_path: Path):
    room = _room(tmp_path, board=True)
    room.broadcast("grok", "one")
    before = (tmp_path / "events.jsonl").read_bytes()
    assert room.release("anyone", "nobody.py") == {
        "ok": True,
        "path": "nobody.py",
        "agent_id": "anyone",
        "seq": 1,
    }
    assert (tmp_path / "events.jsonl").read_bytes() == before


def test_a_torn_last_line_does_not_take_the_room_down(tmp_path: Path):
    """Review round 6 (Grok), M2: a writer killed mid-line left a fragment. The
    running room then glued its next row onto it, and a restarted room could
    not load the log at all."""
    log = tmp_path / "events.jsonl"
    room = _room(tmp_path, board=True)
    room.broadcast("a", "one")
    room.claim("a", "x.py")
    with log.open("a", encoding="utf-8") as handle:
        handle.write('{"seq": 3, "ts": "x", "type": "broadcast", "agent_id": "a", "te')

    assert room.broadcast("a", "after the tear")["seq"] == 3
    lines = [line for line in log.read_text(encoding="utf-8").split("\n") if line.strip()]
    assert json.loads(lines[-1])["text"] == "after the tear"  # on a line of its own

    restarted = _room(tmp_path, board=True)
    assert [e["seq"] for e in restarted.read()] == [1, 2, 3]
    state = restarted.state()
    assert state["claims"] == {"x.py": "a"}
    assert state["log_skipped_lines"] == 1
    assert restarted.broadcast("a", "next")["seq"] == 4
    assert "1 line(s) in the log could not be read" in (tmp_path / "BOARD.md").read_text(
        encoding="utf-8"
    )


def test_rows_that_are_not_events_are_skipped_and_counted(tmp_path: Path):
    log = tmp_path / "events.jsonl"
    log.write_text(
        '{"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "a", "text": "ok"}\n'
        "[1, 2, 3]\n"
        '{"no": "seq"}\n'
        '{"seq": true, "type": "broadcast", "agent_id": "a", "text": "bool"}\n',
        encoding="utf-8",
    )
    room = _room(tmp_path)
    assert [e["seq"] for e in room.read()] == [1]
    assert room.state()["log_skipped_lines"] == 3
    assert room.broadcast("a", "next")["seq"] == 2


def test_a_failed_append_does_not_use_up_a_seq(tmp_path: Path, monkeypatch):
    room = _room(tmp_path)
    room.broadcast("a", "one")
    _fail_next_append(monkeypatch)
    with pytest.raises(OSError):
        room.broadcast("a", "lost")
    assert room.broadcast("a", "two")["seq"] == 2


def test_read_returns_every_row_by_default(tmp_path: Path):
    room = _room(tmp_path)
    for n in range(60):
        room.broadcast("a", f"row {n}")
    assert len(room.read()) == 60
```

```python
"""RED tests for the board tools on the JSON gateway.

Production change that would make these fail: a bad topic raising instead of
returning a JSON error, `room_read` ignoring its filters, or `room_topics`
missing from the gateway.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.gateway import CoordinationRoomTools  # noqa: E402


def _tools(tmp_path: Path) -> CoordinationRoomTools:
    return CoordinationRoomTools(
        root=tmp_path,
        log_path=tmp_path / "events.jsonl",
        board_path=tmp_path / "BOARD.md",
    )


def _load(raw: str) -> dict:
    data = json.loads(raw)
    assert isinstance(data, dict)
    return data


def test_broadcast_with_topic_and_evidence_round_trips(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    tools = _tools(tmp_path)
    out = _load(
        tools.room_broadcast(
            agent_id="claude",
            text="landed",
            topic="announcements",
            evidence_refs=["file:proof.md"],
        )
    )
    assert out == {
        "ok": True,
        "seq": 1,
        "topic": "announcements",
        "evidence_status": "resolved",
    }
    events = _load(tools.room_read(topic="announcements"))["events"]
    assert events[0]["evidence_refs"] == ["file:proof.md"]


def test_bad_topic_and_bad_reply_return_json_errors(tmp_path: Path):
    tools = _tools(tmp_path)
    bad_topic = _load(tools.room_broadcast(agent_id="a", text="x", topic="Bad Topic"))
    assert bad_topic["ok"] is False
    assert "topic" in bad_topic["error"]
    bad_reply = _load(tools.room_broadcast(agent_id="a", text="x", reply_to=9))
    assert bad_reply["ok"] is False


def test_read_filters_and_old_call_shape_still_works(tmp_path: Path):
    tools = _tools(tmp_path)
    tools.room_broadcast(agent_id="a", text="one", topic="inquiries")
    tools.room_broadcast(agent_id="a", text="two")
    assert len(_load(tools.room_read())["events"]) == 2
    assert [e["text"] for e in _load(tools.room_read(topic="inquiries"))["events"]] == ["one"]
    assert len(_load(tools.room_read(limit=1))["events"]) == 1


def test_topics_tool(tmp_path: Path):
    tools = _tools(tmp_path)
    tools.room_broadcast(agent_id="a", text="one", topic="inquiries")
    out = _load(tools.room_topics())
    assert out["topics"] == [{"topic": "inquiries", "count": 1, "last_seq": 1}]
    assert "general" in out["suggested"]


def test_claim_with_intent_appears_on_the_board(tmp_path: Path):
    tools = _tools(tmp_path)
    assert _load(tools.room_claim(agent_id="grok", path="a.py", intent="refactor"))["ok"]
    assert "refactor" in (tmp_path / "BOARD.md").read_text(encoding="utf-8")
    conflict = _load(tools.room_claim(agent_id="claude", path="a.py", intent="mine"))
    assert conflict["error"] == "conflict"
    assert conflict["holder"] == "grok"


def test_a_failed_log_write_is_a_json_error_not_an_exception(tmp_path: Path, monkeypatch):
    """Review round 6 (Grok), M5: raised to the MCP layer it reached the caller
    as a protocol error; the caller needs to know nothing was recorded."""
    from packages.coordination_room.log import EventLog

    def no_space(self, *args, **fields):
        raise OSError(28, "No space left on device")

    tools = _tools(tmp_path)
    monkeypatch.setattr(EventLog, "append", no_space)
    for reply in (
        tools.room_claim(agent_id="grok", path="a.py"),
        tools.room_broadcast(agent_id="grok", text="x"),
    ):
        out = _load(reply)
        assert out["ok"] is False
        assert "nothing was recorded" in out["error"]
    assert _load(tools.room_state())["claims"] == {}
```

```python
"""RED tests tying coordination-room.schema.json to what the room really writes.

Production change that would make these fail: the room logging a field the
schema forbids by type, or the schema dropping a field the room relies on.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

jsonschema = pytest.importorskip("jsonschema")

from packages.coordination_room.room import CoordinationRoom  # noqa: E402

_SCHEMA = _REPO_ROOT / "docs" / "specs" / "coordination-room.schema.json"


def _validator():
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_every_row_the_room_writes_validates(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    room = CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")
    room.claim("grok", "a.py", intent="work")
    room.claim("claude", "b.py")
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "a1", reply_to=root, evidence_refs=["file:proof.md"])
    room.broadcast("b", "a2", evidence_refs=["file:missing.md", "wat"])
    room.release("grok", "a.py")
    validator = _validator()
    rows = room.read()
    assert len(rows) == 6
    for row in rows:
        validator.validate(row)


def test_legacy_rows_still_validate():
    validator = _validator()
    validator.validate({"seq": 1, "ts": "t", "type": "claim", "agent_id": "g", "path": "a"})
    validator.validate({"seq": 2, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "hi"})


_BASE = {"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "x"}


@pytest.mark.parametrize(
    "extra",
    [
        {"topic": "Bad Topic"},
        {"reply_to": 1},
        {"evidence_refs": ["file:a"]},
        {"evidence_status": "verified"},
        {
            "evidence_refs": ["file:a"],
            "evidence_status": "resolved",
            "evidence_checked": [{"ref": "file:a", "kind": "file", "ok": True}],
        },
        {
            "evidence_refs": ["file:a"],
            "evidence_status": "resolved",
            "evidence_checked_at": "t",
            "evidence_checked": [{"ref": "file:a", "kind": "file", "ok": True, "sha256": "short"}],
        },
    ],
)
def test_schema_rejects_malformed_board_rows(extra):
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate({**_BASE, **extra})
```

```python
"""The rollback promise, as a test: v0.1 code can serve a log this version wrote.

v0.1 is loaded from git (the commit this work is based on), run in its own
process against a log written here, and must replay the claims, read every
row and continue the sequence. Skipped where that commit is not available, a
shallow clone for instance.

Production change that would make this fail: a row shape v0.1 cannot load, or
a claim or release recorded in a way v0.1 replays differently.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.room import CoordinationRoom  # noqa: E402

V01_COMMIT = "4aab13e30f3c2960da787b47c90926256b4b5b73"
V01_FILES = ("__init__.py", "claims.py", "log.py", "paths.py", "room.py")

_V01_SCRIPT = """
import json, sys
from pathlib import Path
from packages.coordination_room.room import CoordinationRoom
root = Path(sys.argv[1])
room = CoordinationRoom(root=root, log_path=root / "events.jsonl")
state = room.state()
print(json.dumps({
    "keys": sorted(state),
    "claims": state["claims"],
    "last_seq": state["last_seq"],
    "rows": len(room.read()),
    "next": room.broadcast("v01", "written by v0.1")["seq"],
}))
"""


def _v01_package(target: Path) -> None:
    package = target / "packages" / "coordination_room"
    package.mkdir(parents=True)
    (target / "packages" / "__init__.py").write_text("", encoding="utf-8")
    for name in V01_FILES:
        shown = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "show", f"{V01_COMMIT}:packages/coordination_room/{name}"],
            capture_output=True,
        )
        if shown.returncode != 0:
            pytest.skip(f"v0.1 source not available from git ({V01_COMMIT[:7]})")
        (package / name).write_bytes(shown.stdout)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_v01_code_serves_a_log_written_by_this_version(tmp_path: Path):
    root = tmp_path / "room"
    root.mkdir()
    (root / "proof.md").write_text("x", encoding="utf-8")
    room = CoordinationRoom(root=root, log_path=root / "events.jsonl", board_path=root / "BOARD.md")
    room.claim("grok", "a.py", intent="work")
    question = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "answer", reply_to=question, evidence_refs=["file:proof.md", "wat"])
    room.claim("claude", "b.py")
    room.release("grok", "a.py")

    old = tmp_path / "v01"
    _v01_package(old)
    done = subprocess.run(
        [sys.executable, "-c", _V01_SCRIPT, str(root)],
        capture_output=True, text=True, cwd=old, timeout=60,
        env={"SystemRoot": __import__("os").environ.get("SystemRoot", ""), "PATH": ""},
    )
    assert done.returncode == 0, done.stderr
    seen = json.loads(done.stdout)
    assert seen == {
        "keys": ["claims", "last_seq", "speakers"],
        "claims": {"b.py": "claude"},
        "last_seq": 5,
        "rows": 5,
        "next": 6,
    }

    # And this version reads what v0.1 then wrote.
    back = CoordinationRoom(root=root, log_path=root / "events.jsonl")
    assert back.read()[-1]["text"] == "written by v0.1"
    assert back.state()["claims"] == {"b.py": "claude"}
    assert back.state()["log_skipped_lines"] == 0
```

- [ ] **Step 2: Run them to see them fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_message_board.py packages/coordination_room/tests/test_gateway_board.py packages/coordination_room/tests/test_schema.py
```

Expected: failures that are `TypeError` on the new keyword arguments (`board_path`, `intent`, `topic`). Not import errors; if you see `ModuleNotFoundError`, Tasks 3 or 4 are not on this branch.

- [ ] **Step 3: Replace `log.py`.**

```python
"""Append-only JSONL event log. The only durable mutator."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_MAX = 4096


class EventLog:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._seq = 0
        # Lines the last load() could not use: a write torn by a kill, or
        # anything that is not a JSON object with an integer seq. They are
        # skipped and counted, never rewritten: the log is append-only.
        self.skipped = 0
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            for event in self.load():
                self._seq = max(self._seq, int(event["seq"]))

    def load(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            self.skipped = 0
            return []
        events: list[dict[str, Any]] = []
        skipped = 0
        # Split on "\n" only: str.splitlines() also breaks on U+2028, U+2029
        # and U+0085, which append() writes raw inside string values.
        for line in self._path.read_text(encoding="utf-8").split("\n"):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            seq = row.get("seq") if isinstance(row, dict) else None
            if isinstance(seq, bool) or not isinstance(seq, int):
                skipped += 1
                continue
            events.append(row)
        self.skipped = skipped
        return events

    def _ends_mid_line(self) -> bool:
        """True if the file's last byte is not a newline: the previous write was torn."""
        try:
            with self._path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    return False
                handle.seek(-1, os.SEEK_END)
                return handle.read(1) != b"\n"
        except FileNotFoundError:
            return False

    def append(self, event_type: str, agent_id: str, **fields: Any) -> dict[str, Any]:
        seq = self._seq + 1
        record: dict[str, Any] = {
            "seq": seq,
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": event_type,
            "agent_id": agent_id,
        }
        record.update(fields)
        # A torn tail must not swallow this row: start it on its own line.
        lead = "\n" if self._ends_mid_line() else ""
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(lead + json.dumps(record, ensure_ascii=False) + "\n")
        # Only a row that was written consumes its number.
        self._seq = seq
        return record
```

- [ ] **Step 4: Replace `room.py`.**

```python
"""Coordination room: claim table + event log + board projection under one lock."""

from __future__ import annotations

import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from packages.coordination_room.board import (
    DEFAULT_TOPIC,
    SUGGESTED_TOPICS,
    check_topic,
    topic_of,
    topic_summary,
    write_board,
)
from packages.coordination_room.claims import ClaimTable
from packages.coordination_room.evidence import resolve_all
from packages.coordination_room.log import TEXT_MAX, EventLog
from packages.coordination_room.paths import normalize_path

INTENT_MAX = 256


class BoardPathError(ValueError):
    """The board path names the event log."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_board_path(log_path: Path, board_path: Path) -> None:
    """Refuse a board path that names the event log, by path or by file identity.

    Pure check: opens nothing. Staging is not checked here because write_board
    stages through a fresh mkstemp file and swaps names; it never opens an
    existing file for writing.
    """
    same_name = os.path.normcase(str(board_path.resolve())) == os.path.normcase(
        str(log_path.resolve())
    )
    same_file = board_path.exists() and log_path.exists() and os.path.samefile(
        board_path, log_path
    )
    if same_name or same_file:
        raise BoardPathError(f"board_path {board_path} is the event log {log_path}")


class CoordinationRoom:
    def __init__(
        self, root: Path, log_path: Path, board_path: Path | None = None
    ) -> None:
        if board_path is not None:
            check_board_path(log_path, board_path)
        self._root = root.resolve()
        self._log_path = log_path
        self._table = ClaimTable()
        self._log = EventLog(log_path)
        self._board_path = board_path
        # What the last projection did, for room_state: the daemon's stderr
        # goes to a hidden console, so nobody would see it there.
        self._board_as_of: str | None = None
        self._board_error: str | None = None
        self._lock = threading.Lock()
        self._replay()

    def _replay(self) -> None:
        for event in self._log.load():
            kind = event.get("type")
            if kind == "claim":
                self._table.force_set(event["path"], event["agent_id"])
            elif kind == "release":
                self._table.force_drop(event["path"])

    def _project(self) -> None:
        """Rewrite BOARD.md after a logged event. Never at construction: a process
        that has not won the daemon slot must not write. A failed view must not
        fail a post; the failure is kept for room_state.

        The board path is checked again here, not only at construction: a
        directory on the board's path can be re-pointed (junction, symlink)
        while the room runs, and the stored path would then name the log. This
        closes that for any alias present when a projection starts. It is not
        a defence against something racing to re-point a directory between
        this check and the rename.
        """
        if self._board_path is None:
            return
        now = _utc_now()
        try:
            check_board_path(self._log_path, self._board_path)
            events = self._log.load()
            write_board(self._board_path, events, skipped=self._log.skipped)
        except BoardPathError as exc:
            self._board_error = f"refused at {now}: {exc}"
        except OSError as exc:
            self._board_error = f"failed at {now}: {exc}"
        else:
            self._board_as_of, self._board_error = now, None
            return
        print(f"[coordination_room] BOARD.md projection {self._board_error}", file=sys.stderr)

    def _find_broadcast(self, seq: int) -> dict[str, Any]:
        for event in self._log.load():
            if int(event["seq"]) == seq and event.get("type") == "broadcast":
                return event
        raise ValueError(f"reply_to {seq} is not a broadcast")

    def claim(self, agent_id: str, path: str, intent: str = "") -> dict[str, Any]:
        if not isinstance(intent, str):
            raise ValueError("intent must be a string")
        if len(intent.encode("utf-8")) > INTENT_MAX:
            raise ValueError(f"intent exceeds {INTENT_MAX} bytes")
        key = normalize_path(self._root, path)
        with self._lock:
            if self._table.snapshot().get(key) == agent_id:
                return {"ok": True, "path": key, "agent_id": agent_id, "seq": self._log._seq}
            self._table.claim(agent_id, key)
            fields: dict[str, Any] = {"path": key}
            if intent.strip():
                fields["intent"] = intent.strip()
            try:
                event = self._log.append("claim", agent_id, **fields)
            except OSError:
                # No row, no claim: otherwise a retry would be told "ok" for a
                # claim the log never recorded and a restart would forget.
                self._table.force_drop(key)
                raise
            self._project()
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def release(self, agent_id: str, path: str) -> dict[str, Any]:
        key = normalize_path(self._root, path)
        with self._lock:
            if key not in self._table.snapshot():
                # Nothing to release: say so without adding a row.
                return {"ok": True, "path": key, "agent_id": agent_id, "seq": self._log._seq}
            self._table.release(agent_id, key)
            try:
                event = self._log.append("release", agent_id, path=key)
            except OSError:
                self._table.force_set(key, agent_id)
                raise
            self._project()
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def broadcast(
        self,
        agent_id: str,
        text: str,
        *,
        topic: str | None = None,
        evidence_refs: list[str] | None = None,
        reply_to: int | None = None,
    ) -> dict[str, Any]:
        if not agent_id.strip():
            raise ValueError("empty agent_id")
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if len(text.encode("utf-8")) > TEXT_MAX:
            raise ValueError(f"broadcast text exceeds {TEXT_MAX} bytes")
        if topic is not None:
            topic = check_topic(topic)
        # Looked up before the lock: a commit probe is a subprocess, and the lock
        # guards the log, not the filesystem. So the label describes the lookup
        # at `evidence_checked_at`, not the state at the moment of the append.
        checked_at = _utc_now()
        status, checked = resolve_all(self._root, evidence_refs)
        with self._lock:
            fields: dict[str, Any] = {}
            if reply_to is not None:
                parent = self._find_broadcast(reply_to)
                parent_topic = topic_of(parent)
                if topic is not None and topic != parent_topic:
                    raise ValueError(
                        f"reply topic must match parent topic {parent_topic!r}"
                    )
                topic = parent_topic
                fields["reply_to"] = reply_to
                fields["thread_id"] = parent.get("thread_id", parent["seq"])
            fields["topic"] = topic or DEFAULT_TOPIC
            if checked:
                fields["evidence_refs"] = [c["ref"] for c in checked]
                fields["evidence_status"] = status
                fields["evidence_checked"] = checked
                fields["evidence_checked_at"] = checked_at
            event = self._log.append("broadcast", agent_id, text=text, **fields)
            self._project()
            result: dict[str, Any] = {
                "ok": True,
                "seq": event["seq"],
                "topic": fields["topic"],
            }
            if checked:
                result["evidence_status"] = status
            return result

    def read(
        self,
        since_seq: int = 0,
        *,
        topic: str | None = None,
        thread_id: int | None = None,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            events = [e for e in self._log.load() if int(e["seq"]) > since_seq]
        if topic is not None:
            events = [e for e in events if topic_of(e) == topic]
        if thread_id is not None:
            events = [
                e
                for e in events
                if e.get("thread_id") == thread_id or e["seq"] == thread_id
            ]
        if limit > 0:
            events = events[:limit]
        return events

    def topics(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
        return {"topics": topic_summary(events), "suggested": list(SUGGESTED_TOPICS)}

    def state(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
            last = events[-1]["seq"] if events else 0
            speakers = sorted({e["agent_id"] for e in events})
            return {
                "claims": self._table.snapshot(),
                "last_seq": last,
                "speakers": speakers,
                # Which bus this is. A caller checks these before a live post.
                "root": str(self._root),
                "log": str(self._log_path),
                "board": str(self._board_path) if self._board_path else None,
                # Health a caller can see: when the board was last written, why
                # the last write failed if it did, and how many log lines were
                # unreadable and skipped.
                "board_as_of": self._board_as_of,
                "board_last_error": self._board_error,
                "log_skipped_lines": self._log.skipped,
            }
```

- [ ] **Step 5: Replace `gateway.py`.**

```python
"""JSON tool router for the coordination room. Does not write workspace files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.coordination_room.claims import ClaimConflict
from packages.coordination_room.paths import PathEscape
from packages.coordination_room.room import CoordinationRoom


def _error(message: str, **extra: Any) -> str:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    return json.dumps(payload)


def _ok(payload: dict[str, Any]) -> str:
    payload.setdefault("ok", True)
    return json.dumps(payload)


def _write_failed(exc: OSError) -> str:
    # The row was not written and nothing was changed. Said in the reply,
    # because a raised exception would reach the caller as a protocol error.
    return _error(f"log write failed, nothing was recorded: {exc}")


class CoordinationRoomTools:
    def __init__(
        self,
        root: Path,
        log_path: Path,
        room: CoordinationRoom | None = None,
        board_path: Path | None = None,
    ) -> None:
        self._room = room or CoordinationRoom(
            root=root, log_path=log_path, board_path=board_path
        )

    def room_claim(self, agent_id: str, path: str, intent: str = "") -> str:
        try:
            return _ok(self._room.claim(agent_id, path, intent=intent))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))
        except OSError as exc:
            return _write_failed(exc)

    def room_release(self, agent_id: str, path: str) -> str:
        try:
            return _ok(self._room.release(agent_id, path))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))
        except OSError as exc:
            return _write_failed(exc)

    def room_broadcast(
        self,
        agent_id: str,
        text: str,
        topic: str | None = None,
        evidence_refs: list[str] | None = None,
        reply_to: int | None = None,
    ) -> str:
        try:
            return _ok(
                self._room.broadcast(
                    agent_id,
                    text,
                    topic=topic,
                    evidence_refs=evidence_refs,
                    reply_to=reply_to,
                )
            )
        except ValueError as exc:
            return _error(str(exc))
        except OSError as exc:
            return _write_failed(exc)

    def room_read(
        self,
        since_seq: int = 0,
        topic: str | None = None,
        thread_id: int | None = None,
        limit: int = 0,
    ) -> str:
        events = self._room.read(
            since_seq=since_seq, topic=topic, thread_id=thread_id, limit=limit
        )
        return _ok({"events": events})

    def room_topics(self) -> str:
        return _ok(self._room.topics())

    def room_state(self) -> str:
        return _ok(self._room.state())
```

- [ ] **Step 6: Run the whole package.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests
```

Expected: no failures; measured `104 passed` (the 21 baseline tests unchanged, including the four line-separator tests `4aab13e` added). One alias case skips off Windows; `test_v01_compat.py` skips in a shallow clone.

- [ ] **Step 7: Lint.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m ruff check --isolated packages/coordination_room
```

Expected: `All checks passed!` (ruff 0.15.11; see Global Constraints).

- [ ] **Step 8: Commit.**

```bash
git add -- packages/coordination_room/log.py packages/coordination_room/room.py packages/coordination_room/gateway.py packages/coordination_room/tests/test_message_board.py packages/coordination_room/tests/test_gateway_board.py packages/coordination_room/tests/test_schema.py packages/coordination_room/tests/test_v01_compat.py
git commit -F- -- packages/coordination_room/log.py packages/coordination_room/room.py packages/coordination_room/gateway.py packages/coordination_room/tests/test_message_board.py packages/coordination_room/tests/test_gateway_board.py packages/coordination_room/tests/test_schema.py packages/coordination_room/tests/test_v01_compat.py <<'EOF'
feat(coordination-room): topics, threads, evidence labels and intent on the room

Additive: v0.1 rows load unchanged and v0.1 code can serve this log.
A claim exists only once its row is written. An unreadable log line is
skipped and counted, never repaired, and no longer stops the room loading.
The board is written only after a logged event, and its failures show in
room_state.
EOF
```

---

### Task 6: Server surface, client, deployment helpers, docs

**Files:**
- Replace: `packages/coordination_room/server.py`
- Create: `packages/coordination_room/client.py`
- Create: `packages/coordination_room/deploy.ps1`
- Edit: `requirements-ci.txt`
- Replace: `packages/coordination_room/README.md`
- Edit: `docs/agent-memory/project/coordination-room-v0.md`
- Test: `packages/coordination_room/tests/room_server.py` (shared helper), `test_server_tools.py`, `test_server_http.py`, `deploy_harness.ps1`, `test_deploy_helpers.py`

**Interfaces:**
- Consumes: Task 5 `CoordinationRoomTools(..., board_path=...)`, its six tool methods, and `check_board_path`.
- Produces: MCP tools `room_claim(agent_id, path, intent="")`, `room_broadcast(agent_id, text, topic=None, evidence_refs=None, reply_to=None)`, `room_read(since_seq=0, topic=None, thread_id=None, limit=0)`, `room_topics()`, `room_release`, `room_state()`, all coroutines that run the room call on a worker thread; env var `COORDINATION_ROOM_BOARD` (optional override, default `BOARD.md` beside the log; refused at import if it names the log); module-level `_tools()` builds the room on the first tool call, `_tools_instance` is `None` until then. `client.call_tool(url, tool, arguments) -> dict` and `python -m packages.coordination_room.client [--url URL] <tool> [<json> | -]` (prints the reply as one ASCII JSON line; exit 0, 2 if the room said `ok: false`, 1 if the call failed). `deploy.ps1`, dot-sourced, defines `Invoke-DaemonScript`, `Assert-OnlyAction`, `Assert-PinnedLog`, `Assert-PortFree`, `Get-LogRows`, `Get-SettledSeq`, `Get-LogRow`, `Get-LogClaims`, `Invoke-Room`, `Assert-RoomState`, `Assert-V01State`, `New-SmokeMarker`, `Assert-SmokeEvent`, `New-PinnedCheckout`, and the variables `$log`, `$agent`, `$py`, `$roomUrl`.

`server.py` is replaced whole because every tool function changes. `_room_root`, `_log_path`, `_audit_sink_path` and the `__main__` block are the base file's, unchanged; `_create_mcp` gains `room_topics`. The tools are coroutines because FastMCP runs a synchronous tool directly on its event loop, where one post's `git` lookup would stall every caller.

`client.py` and `deploy.ps1` exist so that deployment is commands and checks, not "call this from some agent session and compare by eye". Both sit in the package, beside what they deploy; the harness that proves the helpers is committed with them.

- [ ] **Step 1: Write the test helper and the failing tests.** The helper clears and re-pins every room environment variable and serves an app on a free port.

```python
"""Test helper: serve the real FastMCP room on a free loopback port, under a temp directory."""

from __future__ import annotations

import contextlib
import importlib
import socket
import threading
import time
from pathlib import Path

ROOM_ENV = (
    "COORDINATION_ROOM_ROOT",
    "COORDINATION_ROOM_LOG",
    "COORDINATION_ROOM_BOARD",
    "FLOSS_AUDIT_DIR",
    "FLOSS_AGENT_DIR",
)


def free_port() -> int:
    """A port nothing is listening on right now. Not reserved: bind it soon."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def pin_room_env(monkeypatch, tmp_path: Path) -> Path:
    """Clear every room variable, then pin root, log and audit under tmp_path.

    Cleared, not inherited: an operator's COORDINATION_ROOM_BOARD or
    FLOSS_AGENT_DIR must never be written to by a test. Returns the log path.
    """
    for name in ROOM_ENV:
        monkeypatch.delenv(name, raising=False)
    log = tmp_path / "rooms" / "events.jsonl"
    monkeypatch.setenv("COORDINATION_ROOM_ROOT", str(tmp_path))
    monkeypatch.setenv("COORDINATION_ROOM_LOG", str(log))
    monkeypatch.setenv("FLOSS_AUDIT_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path / "agent"))
    return log


def reload_server():
    """The server module, re-imported under the current environment."""
    import packages.coordination_room.server as module

    return importlib.reload(module)


@contextlib.contextmanager
def serving(app, port: int):
    """Run an ASGI app on 127.0.0.1:port in a thread until the block exits."""
    import httpx
    import uvicorn

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while True:
        try:
            httpx.get(f"http://127.0.0.1:{port}/", timeout=1)
            break
        except httpx.HTTPError:
            if time.monotonic() > deadline:
                raise AssertionError(f"port {port} never came up") from None
            time.sleep(0.1)
    try:
        yield
    finally:
        server.should_exit = True
        thread.join(timeout=5)
```

```python
"""RED tests for the FastMCP surface of the coordination room.

Production change that would make these fail: a new parameter dropped from the
registered tool schema (the audit wrapper hiding it), `room_topics` not
registered, importing the server reading or writing the log, a duplicate start
rewriting the board before it loses the PID guard, a new owner acting on room
state cached before the previous owner stopped, one slow lookup stalling every
other caller, a default read limit, or a fixture leaving an operator's
`COORDINATION_ROOM_BOARD` in force.
"""

from __future__ import annotations

import asyncio
import importlib
import json
import runpy
import sys
import time
import warnings
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytest.importorskip("mcp")

from packages.coordination_room.tests.room_server import pin_room_env, reload_server  # noqa: E402


@pytest.fixture
def server(tmp_path: Path, monkeypatch):
    # The module reads its paths at import time, so they are pinned first.
    pin_room_env(monkeypatch, tmp_path)
    return reload_server()


def _call(coroutine) -> dict:
    return json.loads(asyncio.run(coroutine))


def test_board_tools_are_registered_with_their_parameters(server):
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    assert {"room_topics", "room_broadcast", "room_read", "room_claim"} <= set(tools)
    assert {"topic", "evidence_refs", "reply_to"} <= set(
        tools["room_broadcast"].inputSchema["properties"]
    )
    assert {"topic", "thread_id", "limit"} <= set(
        tools["room_read"].inputSchema["properties"]
    )
    assert "intent" in tools["room_claim"].inputSchema["properties"]


def test_import_touches_nothing_and_builds_no_room(server, tmp_path: Path):
    assert server._board_path() == tmp_path / "rooms" / "BOARD.md"
    assert server._tools_instance is None
    assert not (tmp_path / "rooms").exists()


def test_room_state_is_loaded_by_the_owner_not_at_import(server, tmp_path: Path):
    """Review round 2, I1: the previous owner appends and claims after the new
    daemon was imported but before it serves. The new daemon must see both:
    no reused seq, no second holder."""
    from packages.coordination_room.room import CoordinationRoom

    previous = CoordinationRoom(root=tmp_path, log_path=tmp_path / "rooms" / "events.jsonl")
    previous.broadcast("previous", "one")
    previous.claim("previous", "x.py")

    conflict = _call(server.room_claim(agent_id="new", path="x.py"))
    assert conflict["error"] == "conflict"
    assert conflict["holder"] == "previous"
    assert _call(server.room_broadcast(agent_id="new", text="three"))["seq"] == 3


def test_a_slow_lookup_does_not_stall_other_callers(server, monkeypatch):
    """Review round 6 (Grok), M1: FastMCP runs a synchronous tool on its event
    loop, so one post waiting on `git` froze the room for everyone. The tools
    are coroutines that do their work on a worker thread."""
    import packages.coordination_room.room as room_module

    def slow_lookup(root, refs):
        time.sleep(1.5)
        return "unresolved", [{"ref": refs[0], "kind": "commit", "ok": False}]

    monkeypatch.setattr(room_module, "resolve_all", slow_lookup)

    async def scenario() -> tuple[float, dict]:
        post = asyncio.create_task(
            server.room_broadcast(agent_id="a", text="slow", evidence_refs=["commit:" + "a" * 40])
        )
        await asyncio.sleep(0.2)  # the post is now inside its lookup
        started = time.monotonic()
        state = json.loads(await server.room_state())
        waited = time.monotonic() - started
        await post
        return waited, state

    waited, state = asyncio.run(scenario())
    assert state["ok"] is True
    assert waited < 0.8, f"room_state waited {waited:.2f}s behind another caller's lookup"


def test_read_has_no_default_limit(server):
    """Review round 6 (Grok), M7: a default of 50 survived every earlier test."""
    for n in range(60):
        _call(server.room_broadcast(agent_id="a", text=f"row {n}"))
    assert len(_call(server.room_read())["events"]) == 60
    assert len(_call(server.room_read(limit=7))["events"]) == 7


def test_board_defaults_beside_the_log_and_honours_the_override(server, tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_ROOM_BOARD", str(tmp_path / "elsewhere" / "B.md"))
    assert server._board_path() == tmp_path / "elsewhere" / "B.md"


def test_board_override_that_is_the_log_stops_the_import(server, tmp_path, monkeypatch):
    monkeypatch.setenv("COORDINATION_ROOM_BOARD", str(tmp_path / "rooms" / "events.jsonl"))
    with pytest.raises(ValueError, match="event log"):
        importlib.reload(server)


def test_rejected_duplicate_start_leaves_board_and_log_untouched(server, tmp_path, monkeypatch):
    """A second `python -m packages.coordination_room.server` loses the PID
    guard. Nothing durable may change on its way there."""
    _call(server.room_broadcast(agent_id="owner", text="seed"))
    log = tmp_path / "rooms" / "events.jsonl"
    board = tmp_path / "rooms" / "BOARD.md"
    before = (log.read_bytes(), board.read_bytes(), board.stat().st_mtime_ns)

    import packages.mcp_daemon as daemon

    monkeypatch.setattr(daemon, "claim_singleton", lambda pid_filename: False)
    monkeypatch.chdir(tmp_path)
    with warnings.catch_warnings(), pytest.raises(SystemExit) as stopped:
        # runpy notes the module is already imported; that is the point here.
        warnings.simplefilter("ignore", RuntimeWarning)
        runpy.run_module("packages.coordination_room.server", run_name="__main__")

    assert stopped.value.code == 0
    assert (log.read_bytes(), board.read_bytes(), board.stat().st_mtime_ns) == before
    assert sorted(p.name for p in log.parent.iterdir()) == ["BOARD.md", "events.jsonl"]
```

```python
"""HTTP-level acceptance: a real MCP client against the real FastMCP room.

Runs on a free loopback port with every path under tmp_path, so it proves the
deployed surface without touching the live bus on :7334.

Production change that would make these fail: a board argument lost between
the MCP schema and the log, `room_state` not naming the bus it serves, the
board not following a post made over HTTP, the room answering a request whose
Host header is not loopback, or the command-line client mis-reporting a reply.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytest.importorskip("mcp")
httpx = pytest.importorskip("httpx")
pytest.importorskip("uvicorn")

from packages.coordination_room.client import call_tool  # noqa: E402
from packages.coordination_room.tests.room_server import (  # noqa: E402
    free_port,
    pin_room_env,
    reload_server,
    serving,
)


@pytest.fixture
def room(tmp_path: Path, monkeypatch):
    log = pin_room_env(monkeypatch, tmp_path)
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    port = free_port()
    with serving(reload_server().mcp.streamable_http_app(), port):
        yield f"http://127.0.0.1:{port}/mcp", log


def _call(url: str, tool: str, arguments: dict) -> dict:
    return asyncio.run(call_tool(url, tool, arguments))


def test_board_round_trip_over_http(room):
    url, log = room
    state = _call(url, "room_state", {})
    assert state["log"] == str(log)
    assert state["board"] == str(log.parent / "BOARD.md")
    assert state["board_as_of"] is None and state["log_skipped_lines"] == 0

    post = _call(
        url,
        "room_broadcast",
        {
            "agent_id": "claude",
            "text": "landed",
            "topic": "announcements",
            "evidence_refs": ["file:proof.md"],
        },
    )
    assert post == {
        "ok": True,
        "seq": 1,
        "topic": "announcements",
        "evidence_status": "resolved",
    }
    reply = _call(url, "room_broadcast", {"agent_id": "grok", "text": "seen", "reply_to": 1})
    assert reply["topic"] == "announcements"
    assert [e["seq"] for e in _call(url, "room_read", {"thread_id": 1})["events"]] == [1, 2]
    assert _call(url, "room_topics", {})["topics"] == [
        {"topic": "announcements", "count": 2, "last_seq": 2}
    ]
    after = _call(url, "room_state", {})
    assert after["board_as_of"] is not None and after["board_last_error"] is None

    board = (log.parent / "BOARD.md").read_text(encoding="utf-8")
    assert "**claude** [evidence resolved] (refs: file:proof.md): landed" in board
    assert "**grok** re #1: seen" in board
    assert len([line for line in log.read_text(encoding="utf-8").split("\n") if line.strip()]) == 2


def test_a_request_with_a_foreign_host_header_is_refused(room):
    """DNS rebinding: a web page can make a browser send requests here under
    its own host name. FastMCP refuses a non-loopback Host for a loopback
    server; this pins that the room is built in a way that keeps it on."""
    url, log = room
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    headers = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}
    refused = httpx.post(url, json=body, headers={**headers, "Host": "evil.example:7334"}, timeout=5)
    assert refused.status_code in (403, 421)
    assert not log.exists()


def test_the_command_line_client_prints_the_reply_and_sets_the_exit_code(room):
    url, _ = room
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    client = [sys.executable, "-m", "packages.coordination_room.client", "--url", url]

    posted = subprocess.run(
        [*client, "room_broadcast", "-"],
        input=json.dumps({"agent_id": "cli", "text": "from the client"}),
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60,
    )
    assert posted.returncode == 0, posted.stderr
    assert json.loads(posted.stdout) == {"ok": True, "seq": 1, "topic": "general"}

    state = subprocess.run(
        [*client, "room_state"], capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60
    )
    assert state.returncode == 0 and json.loads(state.stdout)["last_seq"] == 1

    refused = subprocess.run(
        [*client, "room_broadcast", json.dumps({"agent_id": "cli", "text": "x", "topic": "Bad Topic"})],
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60,
    )
    assert refused.returncode == 2
    assert json.loads(refused.stdout)["ok"] is False

    nobody = subprocess.run(
        [sys.executable, "-m", "packages.coordination_room.client", "--url", "http://127.0.0.1:9/mcp", "room_state"],
        capture_output=True, text=True, cwd=_REPO_ROOT, env=env, timeout=60,
    )
    assert nobody.returncode == 1
    assert "room call failed" in nobody.stderr
```

```powershell
# Inert checks of ..\deploy.ps1, run by test_deploy_helpers.py under each
# installed PowerShell: fake checkouts, a scratch port, a scratch log, a scratch
# git repository, and (when -RoomUrl is given) a scratch room the test started.
# No real daemon, PID file or port 7334/7335 is touched. Prints one JSON object
# of named checks; every value must be true.
param([string]$Work, [string]$Python, [int]$Port, [string]$RoomUrl, [string]$RoomLog, [string]$RoomRoot)
$ErrorActionPreference = 'Stop'
$py = $Python
. (Join-Path (Split-Path -Parent $PSScriptRoot) 'deploy.ps1')
$agent = Join-Path $Work 'agent'; New-Item -ItemType Directory -Force $agent | Out-Null
$log = Join-Path $Work 'events.jsonl'
$results = [ordered]@{}

function Make-Checkout([string]$Name, [string]$Body) {
    $dir = Join-Path $Work $Name
    New-Item -ItemType Directory -Force (Join-Path $dir 'scripts') | Out-Null
    Set-Content -Path (Join-Path $dir 'scripts\stop_mcp_daemons.ps1') -Value $Body -Encoding ascii
    return $dir
}
$ok   = Make-Checkout 'ok'   'Write-Host "[FLOSS MCP] WOULD_STOP coordination_room.pid (x)"; exit 0'
$fail = Make-Checkout 'fail' 'Write-Host "[FLOSS MCP] SHUTDOWN INCOMPLETE"; exit 1'
$two  = Make-Checkout 'two'  'Write-Host "[FLOSS MCP] WOULD_STOP coordination_room.pid"; Write-Host "[FLOSS MCP] WOULD_STOP consensus.pid"; exit 0'

$out = Invoke-DaemonScript $ok 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $out 'WOULD_STOP' 'coordination_room.pid'
$results['success-returns-output'] = $true

try { Invoke-DaemonScript $fail 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null; $results['failure-throws'] = $false }
catch { $results['failure-throws'] = ($_.Exception.Message -match 'exited 1') }

$out = Invoke-DaemonScript $two 'stop_mcp_daemons.ps1' @('-DryRun')
try { Assert-OnlyAction $out 'WOULD_STOP' 'coordination_room.pid'; $results['extra-action-throws'] = $false }
catch { $results['extra-action-throws'] = $true }

# Review round 4, R4-03: the target must match exactly, not by prefix.
try { Assert-OnlyAction '[FLOSS MCP] WOULD_START packages.coordination_room.server_other (wrong)' 'WOULD_START' 'packages.coordination_room.server'; $results['prefixed-module-throws'] = $false }
catch { $results['prefixed-module-throws'] = $true }
try { Assert-OnlyAction '[FLOSS MCP] WOULD_STOP coordination_room.pid.bak (x)' 'WOULD_STOP' 'coordination_room.pid'; $results['suffixed-pid-throws'] = $false }
catch { $results['suffixed-pid-throws'] = $true }
Assert-OnlyAction '[FLOSS MCP] WOULD_START packages.coordination_room.server (coordination room (:7334))' 'WOULD_START' 'packages.coordination_room.server'
$results['exact-module-passes'] = $true

Assert-PortFree $Port 'none.pid'
$results['free-port-passes'] = $true

$holderFile = Join-Path $Work 'hold_port.py'
Set-Content $holderFile -Encoding ascii -Value "import socket, time`ns = socket.socket()`ns.bind(('127.0.0.1', $Port))`ns.listen()`ntime.sleep(20)"
$holder = Start-Process -PassThru -WindowStyle Hidden -FilePath $py -ArgumentList "`"$holderFile`""
Start-Sleep -Milliseconds 1500
$results['holder-running'] = -not $holder.HasExited
try { Assert-PortFree $Port 'none.pid'; $results['bound-port-throws'] = $false }
catch { $results['bound-port-throws'] = ($_.Exception.Message -match 'still bound') }
Stop-Process -Id $holder.Id -Force -ErrorAction SilentlyContinue

Set-Content (Join-Path $agent 'coordination_room.pid') '4242'
try { Assert-PortFree $Port 'coordination_room.pid'; $results['leftover-pid-throws'] = $false }
catch { $results['leftover-pid-throws'] = ($_.Exception.Message -match 'still present') }

Set-Content $log -Value '{"seq": 1}', '{"seq": 7, "type": "broadcast"}' -Encoding utf8
$results['settled-seq'] = (Get-SettledSeq) -eq 7

# Review round 4, R4-01: prove the smoke post itself is in the shared log.
function Write-Log([string[]]$Rows) {
    # As the room writes it: UTF-8, no BOM, one JSON object per line.
    [IO.File]::WriteAllLines($log, $Rows, (New-Object System.Text.UTF8Encoding($false)))
}
$marker = New-SmokeMarker
$results['marker-shape'] = ($marker -cmatch '^deploy-smoke-[0-9a-f]{32}$') -and ($marker -ne (New-SmokeMarker))
$settledRow = '{"seq": 1, "type": "broadcast", "agent_id": "a", "text": "settled"}'
$smokeRow = '{"seq": 2, "type": "broadcast", "agent_id": "deploy-smoke", "text": "rolled back to v0.1 ' + $marker + '"}'

# Wrong bus: the room that answered returned seq 2, but in the shared log
# seq 2 is another agent's post. The tail moved by one; the post is not there.
Write-Log @($settledRow, '{"seq": 2, "type": "broadcast", "agent_id": "peer", "text": "unrelated"}')
$results['tail-moved-by-one-on-wrong-bus'] = (Get-SettledSeq) -eq 2
try { Assert-SmokeEvent 2 'deploy-smoke' $marker; $results['wrong-bus-throws'] = $false }
catch { $results['wrong-bus-throws'] = ($_.Exception.Message -match 'not the smoke post') }

# Correct bus with a peer posting right after: must pass although the tail is now 3.
Write-Log @($settledRow, $smokeRow, ('{"seq": 3, "type": "broadcast", "agent_id": "peer", "text": "a' + [char]0x2028 + 'b"}'))
Assert-SmokeEvent 2 'deploy-smoke' $marker
$results['interleaved-peer-passes'] = (Get-SettledSeq) -eq 3

try { Assert-SmokeEvent 2 'someone-else' $marker; $results['wrong-agent-throws'] = $false }
catch { $results['wrong-agent-throws'] = $true }
try { Assert-SmokeEvent 2 'deploy-smoke' (New-SmokeMarker); $results['wrong-marker-throws'] = $false }
catch { $results['wrong-marker-throws'] = $true }
try { Assert-SmokeEvent 9 'deploy-smoke' $marker; $results['missing-seq-throws'] = $false }
catch { $results['missing-seq-throws'] = ($_.Exception.Message -match 'appears 0 times') }
# Review round 5 (Codex's characterisation cases): only a generated marker is
# accepted, and it is matched literally and case-sensitively.
foreach ($pair in @(@('empty-marker-throws', ''), @('wildcard-marker-throws', '*'), @('uppercase-marker-throws', $marker.ToUpper()))) {
    try { Assert-SmokeEvent 2 'deploy-smoke' $pair[1]; $results[$pair[0]] = $false }
    catch { $results[$pair[0]] = ($_.Exception.Message -match 'not a marker from New-SmokeMarker') }
}
Write-Log @($settledRow, $smokeRow, $smokeRow)
try { Assert-SmokeEvent 2 'deploy-smoke' $marker; $results['duplicate-seq-throws'] = $false }
catch { $results['duplicate-seq-throws'] = ($_.Exception.Message -match 'appears 2 times') }
Write-Log @($settledRow)
$results['log-row-readback'] = (Get-LogRow 1).agent_id -ceq 'a'

# Review round 6 (Grok), M2: the room skips a line it cannot read; a deployment must not.
Write-Log @($settledRow, '{"seq": 2, "type": "broadcast", "agent_id": "a", "te')
try { Get-SettledSeq | Out-Null; $results['torn-log-stops-deployment'] = $false }
catch { $results['torn-log-stops-deployment'] = ($_.Exception.Message -match 'Line 2 .* not readable JSON') }
Write-Log @('{"seq": 1, "type": "claim", "agent_id": "a", "path": "x.py"}', '{"seq": 2, "type": "claim", "agent_id": "b", "path": "y.py"}', '{"seq": 3, "type": "release", "agent_id": "a", "path": "x.py"}')
$results['log-claims'] = ((Get-LogClaims) -join '|') -ceq 'y.py=b'
$v01 = '{"claims": {"y.py": "b"}, "last_seq": 3, "speakers": ["a", "b"]}' | ConvertFrom-Json
Assert-V01State $v01 3
$results['v01-state-accepted'] = $true
try { Assert-V01State ('{"claims": {"y.py": "someone"}, "last_seq": 3, "speakers": []}' | ConvertFrom-Json) 3; $results['v01-wrong-claims-throws'] = $false }
catch { $results['v01-wrong-claims-throws'] = $true }
try { Assert-V01State $v01 4; $results['v01-behind-settled-throws'] = $false }
catch { $results['v01-behind-settled-throws'] = $true }

$preview = "[FLOSS MCP] coordination room log: $log (root C:\x)"
Assert-PinnedLog $preview
$results['pinned-log-passes'] = $true
try { Assert-PinnedLog "[FLOSS MCP] coordination room log: C:\elsewhere\events.jsonl (root C:\x)"; $results['shadow-log-throws'] = $false }
catch { $results['shadow-log-throws'] = $true }

# Rollback checkout against a scratch repository.
$repo = Join-Path $Work 'repo'
New-Item -ItemType Directory -Force $repo | Out-Null
$previous = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
git -C $repo init -q 2>&1 | Out-Null
git -C $repo -c user.name=t -c user.email=t@t commit -q --allow-empty -m one 2>&1 | Out-Null
$commit = "$(git -C $repo rev-parse HEAD)".Trim()
$ErrorActionPreference = $previous

try { New-PinnedCheckout $repo $commit.Substring(0, 7) (Join-Path $Work 'rb-short'); $results['short-commit-throws'] = $false }
catch { $results['short-commit-throws'] = ($_.Exception.Message -match '40-character') }

New-Item -ItemType Directory -Force (Join-Path $Work 'rb-exists') | Out-Null
try { New-PinnedCheckout $repo $commit (Join-Path $Work 'rb-exists'); $results['existing-path-throws'] = $false }
catch { $results['existing-path-throws'] = ($_.Exception.Message -match 'already exists') }

try { New-PinnedCheckout $repo ('0' * 40) (Join-Path $Work 'rb-missing'); $results['unknown-commit-throws'] = $false }
catch { $results['unknown-commit-throws'] = ($_.Exception.Message -match 'exited') }

New-PinnedCheckout $repo $commit (Join-Path $Work 'rb-good')
$results['good-checkout-passes'] = ("$(git -C (Join-Path $Work 'rb-good') rev-parse HEAD)".Trim() -eq $commit)

# A real scratch room, started by the test, reached through the room's own client.
if ($RoomUrl) {
    $roomUrl = $RoomUrl
    $log = $RoomLog
    $checkout = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
    $settled = Get-SettledSeq
    $state = Invoke-Room $checkout 'room_state'
    Assert-RoomState $state $RoomRoot $settled
    $results['live-state-accepted'] = $true
    try { Assert-RoomState $state (Join-Path $Work 'elsewhere') $settled; $results['live-wrong-root-throws'] = $false }
    catch { $results['live-wrong-root-throws'] = ($_.Exception.Message -match 'root is') }
    try { Assert-RoomState $state $RoomRoot ($settled + 5); $results['live-behind-settled-throws'] = $false }
    catch { $results['live-behind-settled-throws'] = ($_.Exception.Message -match 'below the settled') }

    $marker = New-SmokeMarker
    $reply = Invoke-Room $checkout 'room_broadcast' @{ agent_id = 'deploy-smoke'; text = $marker; topic = 'announcements' }
    Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
    $results['live-smoke-correlated'] = ([int]$reply.seq -eq $settled + 1)

    try { Invoke-Room $checkout 'room_broadcast' @{ agent_id = 'deploy-smoke'; text = 'x'; topic = 'Bad Topic' } | Out-Null; $results['live-room-error-throws'] = $false }
    catch { $results['live-room-error-throws'] = ($_.Exception.Message -match 'exited 2') }

    Invoke-Room $checkout 'room_claim' @{ agent_id = 'deploy-smoke'; path = 'x.py' } | Out-Null
    Assert-V01State (Invoke-Room $checkout 'room_state') $settled
    $results['live-v01-view-accepted'] = $true

    $roomUrl = 'http://127.0.0.1:9/mcp'
    try { Invoke-Room $checkout 'room_state' | Out-Null; $results['unreachable-room-throws'] = $false }
    catch { $results['unreachable-room-throws'] = ($_.Exception.Message -match 'exited 1') }
}

$results | ConvertTo-Json
```

```python
"""Runs deploy_harness.ps1 against ../deploy.ps1 under each installed PowerShell.

The harness uses fake checkouts, a scratch port, a scratch log, a scratch git
repository and a scratch room served by this test. It touches no real daemon,
PID file or port 7334/7335.

Production change that would make this fail: a deployment helper carrying on
after a failed precondition, accepting the wrong bus or rejecting the right
one, matching a preview by prefix, or accepting a checkout that is not the
recorded commit.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows deployment helpers")
pytest.importorskip("mcp")
pytest.importorskip("uvicorn")

from packages.coordination_room.tests.room_server import (  # noqa: E402
    free_port,
    pin_room_env,
    reload_server,
    serving,
)

SHELLS = [exe for exe in (shutil.which("powershell"), shutil.which("pwsh")) if exe]


@pytest.mark.parametrize(
    "shell", SHELLS or [pytest.param("", marks=pytest.mark.skip(reason="no PowerShell"))]
)
def test_every_helper_check_holds(shell: str, tmp_path: Path, monkeypatch):
    log = pin_room_env(monkeypatch, tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    port = free_port()
    with serving(reload_server().mcp.streamable_http_app(), port):
        done = subprocess.run(
            [
                shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-File", str(_THIS_DIR / "deploy_harness.ps1"),
                "-Work", str(work),
                "-Python", sys.executable,
                "-Port", str(free_port()),
                "-RoomUrl", f"http://127.0.0.1:{port}/mcp",
                "-RoomLog", str(log),
                "-RoomRoot", str(tmp_path),
            ],
            capture_output=True, text=True, timeout=300,
        )
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
    start = done.stdout.rindex("\n{")
    results = json.loads(done.stdout[start:])
    assert len(results) >= 40, sorted(results)
    assert [name for name, ok in results.items() if ok is not True] == []
```

- [ ] **Step 2: Run them to see them fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_server_tools.py packages/coordination_room/tests/test_server_http.py packages/coordination_room/tests/test_deploy_helpers.py
```

Expected: failures, not passes: there is no `client` module, `room_topics` is not registered, and the server has no `_board_path` or `_tools_instance`.

- [ ] **Step 3: Replace `server.py`.**

```python
"""FastMCP server for the coordination room.

Router, not controller. File claims + append-only log. Binds 127.0.0.1:7334.

Usage:
    python -m packages.coordination_room.server
"""

from __future__ import annotations

import functools
import os
import threading
from pathlib import Path
from typing import Any

import anyio

from packages.coordination_room.gateway import CoordinationRoomTools
from packages.coordination_room.room import check_board_path

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
_WORKSPACE_ROOT = _REPO_ROOT.parent


def _room_root() -> Path:
    override = os.environ.get("COORDINATION_ROOM_ROOT")
    return Path(override).expanduser() if override else _REPO_ROOT


def _log_path() -> Path:
    override = os.environ.get("COORDINATION_ROOM_LOG")
    if override:
        return Path(override).expanduser()
    return _WORKSPACE_ROOT / ".agent-surface" / "rooms" / "default" / "events.jsonl"


def _board_path() -> Path:
    override = os.environ.get("COORDINATION_ROOM_BOARD")
    if override:
        return Path(override).expanduser()
    return _log_path().parent / "BOARD.md"


def _audit_sink_path(filename: str) -> str:
    override = os.environ.get("FLOSS_AUDIT_DIR")
    base = (
        Path(override).expanduser()
        if override
        else _WORKSPACE_ROOT / ".agent-surface" / "heartbeat"
    )
    return str(base / filename)


# A board path that would overwrite the log stops the daemon here, before it
# serves anything. This is a path check only: nothing is opened or created.
check_board_path(_log_path(), _board_path())

_tools_instance: CoordinationRoomTools | None = None
_tools_lock = threading.Lock()


def _tools() -> CoordinationRoomTools:
    """The room, built on the first tool call rather than at import.

    A tool call can only arrive after run_http_daemon has won the PID slot, and
    the slot is only won once any previous owner has exited. So the log is
    replayed, the seq counter cached and the claim table rebuilt by the owner,
    from a log nobody else is still appending to. Building the room at import
    let a starting daemon cache a seq that the exiting one then reused, and
    grant a path the exiting one had just claimed.
    """
    global _tools_instance
    with _tools_lock:
        if _tools_instance is None:
            _tools_instance = CoordinationRoomTools(
                root=_room_root(), log_path=_log_path(), board_path=_board_path()
            )
        return _tools_instance


async def _in_thread(method: str, **arguments: Any) -> str:
    """Run one room call on a worker thread.

    FastMCP calls a synchronous tool directly on its event loop, so one post
    waiting on a `git` lookup would stall every other caller of the room. The
    room serialises its own writes with a lock, so a worker thread is safe.
    """

    def call() -> str:
        return getattr(_tools(), method)(**arguments)

    return await anyio.to_thread.run_sync(functools.partial(call))


_SERVER_INSTRUCTIONS = (
    "FLOSSI0ULLK coordination room. Router, not controller. "
    "Claim a file path before writing it. Second claim on a held path is a "
    "system conflict, not a chat parse. A room claim is a coordination "
    "convention, not write authorization; it does not expire, and agent names "
    "are not authenticated. Broadcast is append-only and may carry "
    "a topic, a reply_to, and evidence_refs (file:<path> or commit:<sha>); "
    "evidence is labelled resolved or unresolved by a lookup, never verified. "
    "BOARD.md is a generated view of the log. room_state names the root, log "
    "and board this room serves, and reports board and log health. "
    "Does not write workspace files. No pycrdt in v0."
)


async def room_claim(agent_id: str, path: str, intent: str = "") -> str:
    """Exclusive claim on a room-root-relative file path. Optional short intent."""
    return await _in_thread("room_claim", agent_id=agent_id, path=path, intent=intent)


async def room_release(agent_id: str, path: str) -> str:
    """Release a path you hold."""
    return await _in_thread("room_release", agent_id=agent_id, path=path)


async def room_broadcast(
    agent_id: str,
    text: str,
    topic: str | None = None,
    evidence_refs: list[str] | None = None,
    reply_to: int | None = None,
) -> str:
    """Append a note to the room log. Does not require a claim.

    topic: lowercase slug, default general (suggested: announcements, claims,
    inquiries, general). reply_to: seq of an earlier broadcast; the reply joins
    its topic and thread. evidence_refs: file:<path> or commit:<sha>; labelled
    resolved or unresolved, the post is admitted either way.
    """
    return await _in_thread(
        "room_broadcast",
        agent_id=agent_id,
        text=text,
        topic=topic,
        evidence_refs=evidence_refs,
        reply_to=reply_to,
    )


async def room_read(
    since_seq: int = 0,
    topic: str | None = None,
    thread_id: int | None = None,
    limit: int = 0,
) -> str:
    """Read log events with seq > since_seq, oldest first. limit 0 means all."""
    return await _in_thread(
        "room_read", since_seq=since_seq, topic=topic, thread_id=thread_id, limit=limit
    )


async def room_topics() -> str:
    """Topics in use with counts, plus the suggested defaults."""
    return await _in_thread("room_topics")


async def room_state() -> str:
    """Claims, last seq, speakers, the root, log and board paths served, and board and log health."""
    return await _in_thread("room_state")


_AUDIT_SINK = _audit_sink_path("janus-coordination-room-audit.jsonl")


def _create_mcp():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        return None

    app = FastMCP(
        "FLOSSI0ULLK Coordination Room",
        instructions=_SERVER_INSTRUCTIONS,
    )
    from packages.mcp_daemon import register_audited_tools

    register_audited_tools(
        app,
        (
            room_claim,
            room_release,
            room_broadcast,
            room_read,
            room_topics,
            room_state,
        ),
        _AUDIT_SINK,
    )
    return app


mcp = _create_mcp()


if __name__ == "__main__":
    if mcp is None:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    from packages.mcp_daemon import run_http_daemon

    os.chdir(_REPO_ROOT)
    run_http_daemon(mcp, pid_filename="coordination_room.pid", port=7334)
```

- [ ] **Step 4: Create `client.py`.**

```python
"""Call one room tool over MCP and print its JSON reply.

For deployment checks and tests, so "call room_state" is a command, not a
manual step in some agent session. Works against any room version: it sends
exactly the arguments it is given.

Usage:
    python -m packages.coordination_room.client room_state
    echo {"agent_id": "a", "text": "hi"} | python -m packages.coordination_room.client room_broadcast -
    python -m packages.coordination_room.client --url http://127.0.0.1:7334/mcp room_read -
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

ROOM_URL = "http://127.0.0.1:7334/mcp"


async def call_tool(url: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """One short MCP session, one tool call. Raises on a tool error."""
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments)
    text = result.content[0].text if result.content else ""
    if result.isError:
        raise RuntimeError(f"{tool} failed: {text[:500]}")
    return json.loads(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--url", default=ROOM_URL)
    parser.add_argument("tool")
    parser.add_argument(
        "arguments",
        nargs="?",
        default="{}",
        help="a JSON object, or - to read one from stdin (default: {})",
    )
    options = parser.parse_args(argv)
    raw = sys.stdin.read() if options.arguments == "-" else options.arguments
    try:
        # utf-8-sig: Windows PowerShell 5.1 can put a byte-order mark on piped input.
        arguments = json.loads(raw.lstrip("\ufeff") or "{}")
        if not isinstance(arguments, dict):
            raise ValueError("arguments must be a JSON object")
        reply = asyncio.run(call_tool(options.url, options.tool, arguments))
    except Exception as exc:  # one exit path: say what failed, exit non-zero
        print(f"room call failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    # ASCII on purpose: a PowerShell caller decodes stdout with its console
    # code page, and non-ASCII text in a reply would arrive mangled.
    print(json.dumps(reply))
    return 0 if reply.get("ok", True) else 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Create `deploy.ps1`.** ASCII only, so Windows PowerShell 5.1 reads it the same with or without a byte-order mark.

```powershell
# Deployment helpers for the coordination room. Dot-source, then call:
#
#   . C:\path\to\checkout\packages\coordination_room\deploy.ps1
#
# Every helper throws on a failed precondition, and $ErrorActionPreference is
# set to Stop, so a block of calls halts at the first failure. Nothing here
# starts, stops or posts by itself: each function does one checked thing.
#
# Set any of $log, $agent, $py, $roomUrl before dot-sourcing to override the
# defaults derived below. Tested by tests/test_deploy_helpers.py.

$ErrorActionPreference = 'Stop'

$deployCheckout = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $log) {
    # Same rule as scripts/start_mcp_daemons.ps1: a checkout under
    # FLOSS\.worktrees\<name> shares the workspace's log, three levels up.
    $intakeRoot = if ($deployCheckout -match '\\.worktrees\\') {
        Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $deployCheckout))
    } else {
        Split-Path -Parent $deployCheckout
    }
    $log = Join-Path $intakeRoot '.agent-surface\rooms\default\events.jsonl'
}
if (-not $agent) {
    $agent = if ($env:FLOSS_AGENT_DIR) { $env:FLOSS_AGENT_DIR } else { "$env:USERPROFILE\.floss_agent" }
}
if (-not $py) {
    $py = if ($env:FLOSS_PYTHON) { $env:FLOSS_PYTHON } else { (Get-Command python -ErrorAction Stop).Source }
}
if (-not $roomUrl) { $roomUrl = 'http://127.0.0.1:7334/mcp' }

function Invoke-DaemonScript {
    # Runs a daemon script in a child Windows PowerShell, so the script's own
    # exit code is what gets tested, and throws on anything but 0. Returns the
    # script's output so the caller can check it too.
    param([string]$Checkout, [string]$Script, [string[]]$Arguments)
    $path = Join-Path $Checkout "scripts\$Script"
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'   # 5.1 turns redirected stderr into errors
    try {
        $out = & powershell -NoProfile -ExecutionPolicy Bypass -File $path @Arguments 2>&1 | Out-String
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    Write-Host $out
    if ($code -ne 0) {
        throw "$Script $($Arguments -join ' ') exited $code. Stop here and read its output."
    }
    return $out
}

function Assert-OnlyAction {
    # A dry run's output must name exactly one action, and its target (the word
    # after the marker: a module or a PID file) must be exactly the expected
    # name. `...server_other` is not `...server`.
    param([string]$Output, [string]$Marker, [string]$Expected)
    $targets = @($Output -split "`r?`n" | ForEach-Object {
        if ($_ -cmatch "$Marker\s+(\S+)") { $Matches[1] }
    })
    if ($targets.Count -ne 1 -or $targets[0] -cne $Expected) {
        throw "Expected exactly one $Marker for $Expected, got: $($targets -join ' | ')"
    }
}

function Assert-PinnedLog {
    # A start preview must show the room pinned to the shared log. Any other
    # path is a separate, empty bus.
    param([string]$Output)
    if ($Output -notmatch [regex]::Escape("coordination room log: $log ")) {
        throw "The start preview does not pin the room to $log. Stop here."
    }
}

function Assert-PortFree {
    # A bind attempt, not a query: a failed or denied query must never read as
    # "free". Exit 0 means this process could bind it, so nothing holds it.
    param([int]$Port, [string]$PidFile)
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $py -c "import socket, sys; s = socket.socket(); s.bind(('127.0.0.1', int(sys.argv[1]))); s.close()" $Port
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "Port $Port is still bound, or could not be checked. Stop here." }
    if ($PidFile -and (Test-Path (Join-Path $agent $PidFile))) {
        throw "$PidFile is still present in $agent. Stop here."
    }
}

function Get-LogRows {
    # Every row of the shared log. Strict on purpose: the room skips a line it
    # cannot read and carries on, but a deployment must not. If this throws,
    # stop, copy the log somewhere safe, and look at it. Never edit it in place.
    # A log that does not exist yet is an empty log: a room that has never
    # been posted to has not created it.
    if (-not (Test-Path $log)) { return }
    $number = 0
    foreach ($line in (Get-Content $log -Encoding UTF8)) {
        $number++
        if (-not $line.Trim()) { continue }
        try { ConvertFrom-Json $line }
        catch { throw "Line $number of $log is not readable JSON. Stop here: copy the log aside and inspect it before going on." }
    }
}

function Get-SettledSeq {
    # The last seq in the shared log. Read it only after the previous owner has
    # stopped: before that, it can still append. Once a room is serving again,
    # other agents may append at any time, so this is a lower bound from then
    # on, never something to compare a later tail against.
    $rows = @(Get-LogRows)
    if ($rows.Count -eq 0) { return 0 }
    return [int]$rows[-1].seq
}

function Get-LogRow {
    # The one row of the shared log with this seq. Throws if it is missing or
    # if the seq appears more than once.
    param([int]$Seq)
    $rows = @(Get-LogRows | Where-Object { $_.seq -eq $Seq })
    if ($rows.Count -ne 1) { throw "seq $Seq appears $($rows.Count) times in $log. Stop here." }
    return $rows[0]
}

function Get-LogClaims {
    # The claims the log itself implies, as sorted "path=agent" strings.
    $held = [ordered]@{}
    foreach ($row in (Get-LogRows)) {
        if ($row.type -ceq 'claim') { $held[$row.path] = $row.agent_id }
        elseif ($row.type -ceq 'release') { $held.Remove($row.path) }
    }
    return @($held.Keys | Sort-Object | ForEach-Object { "$_=$($held[$_])" })
}

function Invoke-Room {
    # One room tool call through the room's own client, run from a checkout
    # that has it. Returns the parsed reply. Throws if the call fails or the
    # room answers ok:false.
    param([string]$Checkout, [string]$Tool, [hashtable]$Arguments = @{})
    $json = $Arguments | ConvertTo-Json -Compress -Depth 5
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $savedPath = $env:PYTHONPATH
    $errors = [IO.Path]::GetTempFileName()
    Push-Location $Checkout
    try {
        $env:PYTHONPATH = ''
        # stdout is the reply (one ASCII JSON line); stderr is kept apart so a
        # warning can never be parsed as the reply.
        $out = $json | & $py -m packages.coordination_room.client --url $roomUrl $Tool - 2> $errors | Out-String
        $code = $LASTEXITCODE
        $detail = Get-Content $errors -Raw
    } finally {
        $env:PYTHONPATH = $savedPath
        Pop-Location
        Remove-Item $errors -Force -ErrorAction SilentlyContinue
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "room call $Tool exited $code. Stop here. $out $detail" }
    return ($out.Trim() | ConvertFrom-Json)
}

function Assert-RoomState {
    # For a v0.2 room: it must name the shared log, the board beside it and the
    # expected root; be at or past the settled seq; and report a readable log.
    # "At or past", not "equal": other agents may already have posted.
    param($State, [string]$Root, [int]$MinSeq)
    $board = Join-Path (Split-Path $log) 'BOARD.md'
    $problems = @()
    if ("$($State.log)" -ne $log) { $problems += "log is '$($State.log)', expected '$log'" }
    if ("$($State.board)" -ne $board) { $problems += "board is '$($State.board)', expected '$board'" }
    if ([IO.Path]::GetFullPath("$($State.root)") -ne [IO.Path]::GetFullPath($Root)) {
        $problems += "root is '$($State.root)', expected '$Root'"
    }
    if ([int]$State.last_seq -lt $MinSeq) { $problems += "last_seq $($State.last_seq) is below the settled $MinSeq" }
    if ([int]$State.log_skipped_lines -ne 0) { $problems += "$($State.log_skipped_lines) unreadable line(s) in the log" }
    if ($problems.Count -gt 0) { throw "This is not the room to post to: $($problems -join '; '). Stop here." }
}

function Assert-V01State {
    # A v0.1 room cannot name its paths. What it can show: a seq at or past the
    # settled one, and the same claims the shared log implies.
    param($State, [int]$MinSeq)
    if ([int]$State.last_seq -lt $MinSeq) {
        throw "last_seq $($State.last_seq) is below the settled $MinSeq. Stop here."
    }
    $fromRoom = @($State.claims.PSObject.Properties | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" })
    $fromLog = @(Get-LogClaims)
    if (($fromRoom -join '|') -cne ($fromLog -join '|')) {
        throw "The room's claims ($($fromRoom -join ', ')) differ from the log's ($($fromLog -join ', ')). If another agent just claimed or released, run this again; if it persists, stop."
    }
}

function New-SmokeMarker {
    # A text no other post will contain.
    return "deploy-smoke-$([guid]::NewGuid().ToString('N'))"
}

function Assert-SmokeEvent {
    # Proves one specific post reached the shared log: the row with the seq the
    # room returned must be a broadcast by this agent carrying this marker.
    # Counting the tail cannot prove that: another agent's post moves the tail
    # too. Rows other agents add before or after this one are fine.
    param([int]$Seq, [string]$Agent, [string]$Marker)
    # Only a marker New-SmokeMarker made is accepted: an empty or hand-typed one
    # (say, from a fresh session where $marker is unset) would match too much.
    if ($Marker -cnotmatch '^deploy-smoke-[0-9a-f]{32}$') {
        throw "'$Marker' is not a marker from New-SmokeMarker. Stop here."
    }
    $row = Get-LogRow $Seq
    # Contains(): literal and case-sensitive. -like would read the text as a pattern.
    if ($row.type -cne 'broadcast' -or $row.agent_id -cne $Agent -or -not "$($row.text)".Contains($Marker)) {
        throw "seq $Seq in $log is not the smoke post by $Agent ($Marker). The room that answered is not writing the shared log. Stop here."
    }
}

function New-PinnedCheckout {
    # A detached checkout of one recorded commit, refused unless it really is
    # that commit. Used for the checkout that serves and for the rollback one,
    # so neither is a worktree somebody is still editing.
    param([string]$Repo, [string]$Commit, [string]$Path)
    if ($Commit -notmatch '^[0-9a-f]{40}$') {
        throw "A pinned checkout needs a full 40-character commit id, got '$Commit'."
    }
    if (Test-Path $Path) {
        throw "$Path already exists. Do not reuse it, and do not remove it without the operator's say-so."
    }
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        git -C $Repo worktree add --detach $Path $Commit
        $code = $LASTEXITCODE
        $head = if ($code -eq 0) { "$(git -C $Path rev-parse HEAD)".Trim() } else { '' }
    } finally {
        $ErrorActionPreference = $previous
    }
    if ($code -ne 0) { throw "git worktree add exited $code. Stop here." }
    if ($head -ne $Commit) { throw "The checkout is at $head, not $Commit. Stop here." }
}
```

- [ ] **Step 6: Bound the `mcp` dependency.** `client.py` and the Phase 2 bridge use `streamable_http_client`; `streamablehttp_client` is deprecated in `mcp` 1.27. MCP 2.x removed `mcp.server.fastmcp`, which `server.py` imports. In `requirements-ci.txt` replace the line `mcp` with `mcp>=1.27,<2`. `grep -n -x "mcp" requirements-ci.txt` prints one line before the edit and none after. Measured with 1.27.0 here; a Grok reviewer's clean install on Linux resolved 1.30.0 and passed.

- [ ] **Step 7: Replace the README.**

```markdown
# Coordination room

MCP router: advisory file-path claims plus an append-only message log with topics, threads and evidence labels. `BOARD.md` is a generated view of the log.

**How to use:** `FLOSS/docs/agent-memory/project/coordination-room-v0.md`  
**Spec:** `FLOSS/docs/specs/coordination-room.spec.md`

Tools: `room_claim` `room_release` `room_state` `room_broadcast` `room_read` `room_topics`  
Bind: `127.0.0.1:7334/mcp`. Start and stop it alone with `scripts/start_mcp_daemons.ps1 -Only room` and `scripts/stop_mcp_daemons.ps1 -Only room` (add `-DryRun` to see what would happen). The start script pins the shared log; a bare `python -m packages.coordination_room.server` from a worktree serves a separate bus.  
Board: `.agent-surface/rooms/default/BOARD.md` (beside the log; override with `COORDINATION_ROOM_BOARD`, which may not be the log)  
One call from a shell: `python -m packages.coordination_room.client room_state`  
Deployment helpers: `deploy.ps1` (dot-source it; every helper stops at a failed precondition)

Router, not controller. No pycrdt. Does not write the claimed files. A room claim is a convention, not write authorization; it does not expire, and agent names are not authenticated. Evidence refs are labelled `resolved` or `unresolved` by a lookup; the room never says "verified".
```

- [ ] **Step 8: Update the agent how-to.** In `docs/agent-memory/project/coordination-room-v0.md`:

Replace the numbered list under `## How to use`:

```
1. `room_claim(agent_id, path)` before you write that path. Path is relative to the FLOSS checkout (e.g. `packages/foo.py`).
2. If the reply is `"error": "conflict"`, someone else holds it (`holder`). Do not write. Pick another path or wait.
3. `room_broadcast(agent_id, text)` for status. No claim required. 4 KiB cap.
4. `room_read(since_seq)` / `room_state()` to see claims and the log.
5. `room_release(agent_id, path)` when done.
```

with:

```
1. `room_claim(agent_id, path, intent="")` before you write that path. Path is relative to the FLOSS checkout (e.g. `packages/foo.py`). `intent` is a short note shown on the board.
2. If the reply is `"error": "conflict"`, someone else holds it (`holder`). Do not write. Pick another path or wait. This is a convention between agents: no hook enforces a room claim, and a room claim is not write authorization. Claims do not expire: the board shows each claim's age and marks one older than a day `stale?`. If a holder is gone, ask the operator; do not release someone else's claim on your own.
3. `room_broadcast(agent_id, text, topic=None, evidence_refs=None, reply_to=None)` for status. No claim required. 4 KiB cap. `topic` is a lowercase slug (default `general`; suggested `announcements`, `inquiries`, `claims`). `reply_to` is the seq of an earlier broadcast. `evidence_refs` are `file:<path>` or `commit:<sha>`; the reply says `resolved` or `unresolved`. The post is admitted either way, and `resolved` only means the lookup found the object.
4. `room_read(since_seq, topic, thread_id, limit)` / `room_topics()` / `room_state()` to see the log, the topics and the claims. `room_state()` also names the `log` it serves and reports board and log health; check it if you need to be sure you are on the shared bus. A post to topic `claims` is chat, not a claim.
5. `room_release(agent_id, path)` when done.

`.agent-surface/rooms/default/BOARD.md` is a generated view of room claims and recent posts, dated by its own `As of` line. Read it; never edit it. Names on it are whatever each caller sent.
```

Replace:

```
Binds `127.0.0.1:7334` only. Not yet in `start_mcp_daemons.ps1`. Do not start killed computer-use `:7333` unless the operator asks.
```

with:

```
Binds `127.0.0.1:7334` only. Start it alone with `scripts/start_mcp_daemons.ps1 -Only room`, which pins the shared log; the bare command above, run from a worktree, serves a separate empty bus. Do not start killed computer-use `:7333` unless the operator asks.
```

Replace the last line:

```
`python -m pytest packages/coordination_room/tests -v` from `FLOSS/` (17 passed 2026-08-30).
```

with:

```
`python -m pytest packages/coordination_room/tests -v` from `FLOSS/`.
```

This file is a canonical agent-memory source. Editing it leaves its projections (including the user-wide Claude memory index) out of date until the operator regenerates them from the primary checkout after merge. **Do not run `materialize_shared_agent_memory.py` or `refresh_agent_surfaces.py` from this worktree, in any mode that writes.** From here the materializer's source root resolves to `FLOSS/.worktrees/FLOSS/docs/agent-memory`, which does not exist, and its Claude target is an absolute user path: applying it would replace the real index with an empty one.

- [ ] **Step 9: Run everything for Phase 1.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests scripts/tests/test_daemon_scope.py
env -u PYTHONPATH C:/Python313/python.exe -m ruff check --isolated packages/coordination_room scripts/tests/test_daemon_scope.py
env -u PYTHONPATH C:/Python313/python.exe scripts/spec_gate.py --check
```

Expected: no failures, measured `117 passed` plus the 24 script tests; `All checks passed!`; spec gate shows the same three findings as Task 0 and nothing new. `test_deploy_helpers.py` and the script tests run on Windows only.

- [ ] **Step 10: Prove the fixtures respect an operator's environment.**

```bash
S="$(mktemp -d)/operator-board.md"; printf OPERATOR > "$S"
COORDINATION_ROOM_BOARD="$S" env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_server_tools.py packages/coordination_room/tests/test_server_http.py packages/coordination_room/tests/test_deploy_helpers.py
cat "$S"
```

Expected: the tests pass and `cat` prints `OPERATOR`.

- [ ] **Step 11: Commit.**

```bash
git add -- packages/coordination_room/server.py packages/coordination_room/client.py packages/coordination_room/deploy.ps1 packages/coordination_room/README.md packages/coordination_room/tests/room_server.py packages/coordination_room/tests/test_server_tools.py packages/coordination_room/tests/test_server_http.py packages/coordination_room/tests/deploy_harness.ps1 packages/coordination_room/tests/test_deploy_helpers.py requirements-ci.txt docs/agent-memory/project/coordination-room-v0.md
git commit -F- -- packages/coordination_room/server.py packages/coordination_room/client.py packages/coordination_room/deploy.ps1 packages/coordination_room/README.md packages/coordination_room/tests/room_server.py packages/coordination_room/tests/test_server_tools.py packages/coordination_room/tests/test_server_http.py packages/coordination_room/tests/deploy_harness.ps1 packages/coordination_room/tests/test_deploy_helpers.py requirements-ci.txt docs/agent-memory/project/coordination-room-v0.md <<'EOF'
feat(coordination-room): board tools over MCP, a shell client, deployment helpers

Importing the server and a rejected duplicate start read and write nothing.
The room is replayed on the first tool call, after the PID slot is won, and
each call runs on a worker thread so one slow lookup cannot stall the rest.
EOF
```

Phase 1 ends here. The live bus has not been touched. Rolling it out is the Deployment section.

---

## Phase 2: the A2A bridge (deferred by default)

**Do not start this phase unless the operator names something that will use it.** The plan has no consumer for it: Hermes is not live, and both Grok reviewers recommended deferring it. It stays written here so the work is not lost, and it is not part of Phase 1's readiness. If it is started, it starts only after Phase 1 is deployed and the acceptance behaviours hold on the real bus. If the bridge fails to start, the room is unaffected.

### Task 7: Bring `a2a_mesh` onto the branch

**Files:**
- Merge: `packages/a2a_mesh/` (6 files), `requirements-ci.txt`, two docs, from `feat/a2a-harness-mesh`

- [ ] **Step 1: Merge.** `git merge-tree` on 2026-10-02 reported the two branches merge clean. Task 6 has since edited one line of `requirements-ci.txt` (`mcp`), and the A2A branch appends three lines at the end of the same file: different hunks, so the merge is still expected clean.

```bash
git merge --no-ff feat/a2a-harness-mesh -m "merge: local A2A helloworld pair (packages/a2a_mesh)"
```

Expected: a merge commit, no conflicts. If git reports conflicts, stop: the base moved since this plan was written.

- [ ] **Step 2: Baseline the merged package.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/a2a_mesh/tests
```

Expected: no failures; measured `4 passed, 1 skipped` (the skip is the optional Hermes card probe). Where no `.mcp.json` exists above the checkout it is `3 passed, 2 skipped`.

---

### Task 8: Room bridge

**Files:**
- Create: `packages/a2a_mesh/room_bridge.py`
- Test: `packages/a2a_mesh/tests/test_room_bridge_parse.py`, `test_room_bridge_pair.py`, `test_room_bridge_invariants.py`, `test_room_bridge_e2e.py`

**Interfaces:**
- Consumes: the room's MCP tools `room_broadcast`, `room_read`, `room_topics` over `http://127.0.0.1:7334/mcp`; `packages.mcp_daemon.claim_singleton`; the A2A SDK as `helloworld.py` uses it; the test helper `packages/coordination_room/tests/room_server.py`.
- Produces: `parse_command(raw: str) -> BoardCommand` (raises `CommandError`; `reply_to`, `since_seq` and `limit` must be JSON integers or plain decimal strings, never floats, booleans or anything `int()` would coerce); `agent_id_for(sender: str) -> str` (always `a2a:` prefixed); `RoomPort` protocol (`async call(tool, arguments) -> dict`); `McpRoomPort(url)`; `build_app(host, port, room) -> Starlette` (answers only a loopback `Host`, and only a loopback `Origin` if one is sent); `serve_room_bridge(host, port, room)`; `AGENT_NAME = "flossi0ullk-a2a-room-bridge"`; `DEFAULT_PORT = 7335`. Entry point: `python -m packages.a2a_mesh.room_bridge` (PID `a2a_room_bridge.pid`, env `A2A_ROOM_BRIDGE_PORT`, `COORDINATION_ROOM_URL`).

Commands accepted: `topics`; `read [#topic] [since=N]`; `post #topic text`; or one JSON object with `op` in `post` | `read` | `topics`. Failures return an artifact `error: ...` and task state `FAILED`. That includes input the JSON decoder itself rejects (an integer literal past the interpreter's digit limit, nesting too deep), a command over 32,768 characters, and anything unforeseen, which is reported as `error: internal bridge error` with the detail on the bridge's stderr only.

Limits to state plainly: the `a2a:` prefix is an attribution label, not authentication. A caller whose post times out cannot tell whether it landed, and a retry posts twice; there is no idempotency key. The bridge constructs nothing and writes nothing at import, so a rejected duplicate start has no side effect.

- [ ] **Step 1: Write the failing tests.**

```python
"""RED tests for the room-bridge command grammar.

Production change that would make these fail: free text guessed into a post,
a caller choosing a bare harness name as agent_id, or an unbounded read limit.
"""

from __future__ import annotations

import pytest

from packages.a2a_mesh.room_bridge import (
    BoardCommand,
    CommandError,
    agent_id_for,
    parse_command,
)


def test_topics():
    assert parse_command(" topics ") == BoardCommand(op="topics")


def test_post_text_form():
    cmd = parse_command("post #claims who owns packages/x?\nsecond line")
    assert cmd.op == "post"
    assert cmd.topic == "claims"
    assert cmd.text == "who owns packages/x?\nsecond line"


def test_read_text_forms():
    assert parse_command("read") == BoardCommand(op="read")
    assert parse_command("read #claims") == BoardCommand(op="read", topic="claims")
    assert parse_command("read #claims since=12") == BoardCommand(
        op="read", topic="claims", since_seq=12
    )
    assert parse_command("read since=3").since_seq == 3


def test_json_post_with_every_field():
    cmd = parse_command(
        '{"op": "post", "topic": "inquiries", "text": " hi ", '
        '"evidence_refs": ["file:a.md"], "reply_to": "4", "sender": "hermes"}'
    )
    assert cmd == BoardCommand(
        op="post",
        topic="inquiries",
        text="hi",
        evidence_refs=("file:a.md",),
        reply_to=4,
        sender="hermes",
    )


def test_json_read_limit_is_clamped():
    assert parse_command('{"op": "read", "limit": 100000}').limit == 100
    assert parse_command('{"op": "read", "limit": 0}').limit == 1
    assert parse_command('{"op": "read", "limit": -5}').limit == 1


def test_integers_and_plain_decimal_strings_are_taken_as_written():
    cmd = parse_command('{"op": "read", "since_seq": "12", "limit": "7"}')
    assert (cmd.since_seq, cmd.limit) == (12, 7)
    assert parse_command('{"op": "post", "text": "x", "reply_to": 4}').reply_to == 4
    assert parse_command('{"op": "post", "text": "x", "reply_to": null}').reply_to is None


@pytest.mark.parametrize("field", ["reply_to", "since_seq", "limit"])
@pytest.mark.parametrize(
    "value",
    ["1.9", "true", "false", "1e999", "-1e999", "NaN", "1e3", '"1.9"', '" 4"', '"4abc"', '"-4"',
     '"٤"', "[4]", '{"n": 4}', "99999999999999999999", '"99999999999999999999"'],
)
def test_numbers_are_never_coerced(field: str, value: str):
    """Review round 4, R4-02: `int()` turned 1.9 and true into 1, so a reply
    joined another thread, and 1e999 escaped as an OverflowError."""
    op = "post" if field == "reply_to" else "read"
    raw = '{"op": "%s", "text": "x", "%s": %s}' % (op, field, value)
    with pytest.raises(CommandError, match=field):
        parse_command(raw)


@pytest.mark.parametrize(
    "raw",
    [
        '{"op": "post", "text": "x", "reply_to": 0}',
        '{"op": "post", "text": "x", "reply_to": -3}',
        '{"op": "read", "since_seq": -1}',
        "read since=99999999999999999999",
    ],
)
def test_out_of_range_event_numbers_are_refused(raw: str):
    with pytest.raises(CommandError):
        parse_command(raw)


@pytest.mark.parametrize("field", ["reply_to", "since_seq", "limit"])
@pytest.mark.parametrize(
    "literal",
    ["9" * 4301, "-" + "9" * 4301, "9" * 10000, "9" * 4300],
    ids=["4301-digits", "negative-4301-digits", "10000-digits", "4300-digits"],
)
def test_integer_literals_the_decoder_itself_rejects_are_a_command_error(field: str, literal: str):
    """Review round 5, R5-01: past the interpreter's digit limit `json.loads`
    raises plain ValueError, not JSONDecodeError, before any range check runs."""
    op = "post" if field == "reply_to" else "read"
    with pytest.raises(CommandError):
        parse_command('{"op": "%s", "text": "x", "%s": %s}' % (op, field, literal))


def test_deeply_nested_json_is_a_command_error():
    """The decoder raises RecursionError here; that must not escape either."""
    nested = "[" * 10000 + "]" * 10000
    with pytest.raises(CommandError):
        parse_command('{"op": "post", "text": "x", "evidence_refs": %s}' % nested)


def test_an_oversized_command_is_refused_before_parsing():
    with pytest.raises(CommandError, match="exceeds"):
        parse_command('{"op": "post", "text": "%s"}' % ("x" * 40000))


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "hello there",
        "post no topic here",
        "post #Bad topic",
        "read #claims extra words",
        "{not json",
        "[]",
        '{"op": "claim"}',
        '{"op": "post"}',
        '{"op": "post", "text": "x", "evidence_refs": "file:a"}',
        '{"op": "post", "text": "x", "evidence_refs": [1]}',
        '{"op": "read", "since_seq": "abc"}',
        '{"op": "post", "text": "x", "topic": 5}',
        '{"op": "post", "text": 5}',
    ],
)
def test_everything_else_is_an_error(raw: str):
    with pytest.raises(CommandError):
        parse_command(raw)


def test_agent_id_is_always_prefixed_and_sanitised():
    assert agent_id_for("hermes") == "a2a:hermes"
    assert agent_id_for("claude") == "a2a:claude"
    assert agent_id_for("a b/c") == "a2a:a-b-c"
    assert agent_id_for("") == "a2a:anonymous"
    assert agent_id_for("x" * 100) == "a2a:" + "x" * 32
```

```python
"""A2A pair for the room bridge, against a fake room.

Production change that would make these fail: the bridge touching the log
itself, a room error reported as success, or the caller picking agent_id.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import httpx
import pytest
import uvicorn

from packages.a2a_mesh.client import send_hello
from packages.a2a_mesh.room_bridge import RoomUnavailable, build_app
from packages.coordination_room.tests.room_server import free_port

# A free port, not a fixed one: two harnesses may run this suite at once.
HOST, PORT = "127.0.0.1", free_port()


class FakeRoom:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.reply: dict[str, Any] = {"ok": True, "seq": 7, "topic": "announcements"}
        self.raises: Exception | None = None

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool, arguments))
        if self.raises is not None:
            raise self.raises
        return self.reply


def _wait_for(url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx.get(url, timeout=1)
            return
        except httpx.HTTPError:
            time.sleep(0.1)
    raise AssertionError(f"{url} never came up")


@pytest.fixture(scope="module")
def bridge():
    room = FakeRoom()
    server = uvicorn.Server(
        uvicorn.Config(build_app(HOST, PORT, room), host=HOST, port=PORT, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for(f"http://{HOST}:{PORT}/.well-known/agent-card.json")
    yield room
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def _reset(bridge):
    bridge.calls.clear()
    bridge.raises = None
    bridge.reply = {"ok": True, "seq": 7, "topic": "announcements"}


def _send(text: str) -> str:
    return send_hello(f"http://{HOST}:{PORT}", text)


def test_card_names_the_board_skill_and_is_not_a_controller():
    card = httpx.get(f"http://{HOST}:{PORT}/.well-known/agent-card.json", timeout=5).json()
    assert card["name"] == "flossi0ullk-a2a-room-bridge"
    assert [s["id"] for s in card["skills"]] == ["coordination_board"]


def test_post_reaches_the_room_with_a_prefixed_agent_id(bridge: FakeRoom):
    reply = json.loads(_send("post #announcements shipped it"))
    assert reply == {"ok": True, "seq": 7, "topic": "announcements"}
    assert bridge.calls == [
        (
            "room_broadcast",
            {"agent_id": "a2a:anonymous", "text": "shipped it", "topic": "announcements"},
        )
    ]


def test_json_post_cannot_choose_a_bare_harness_name(bridge: FakeRoom):
    _send('{"op": "post", "text": "hi", "sender": "claude", "evidence_refs": ["file:a.md"], "reply_to": 2}')
    tool, args = bridge.calls[0]
    assert tool == "room_broadcast"
    assert args["agent_id"] == "a2a:claude"
    assert args["evidence_refs"] == ["file:a.md"]
    assert args["reply_to"] == 2


def test_read_and_topics_map_to_room_tools(bridge: FakeRoom):
    bridge.reply = {"ok": True, "events": []}
    assert json.loads(_send("read #claims since=4")) == {"ok": True, "events": []}
    assert json.loads(_send("topics")) == {"ok": True, "events": []}
    assert bridge.calls == [
        ("room_read", {"since_seq": 4, "limit": 20, "topic": "claims"}),
        ("room_topics", {}),
    ]


def test_bad_command_never_reaches_the_room(bridge: FakeRoom):
    assert _send("please claim a.py for me").startswith("error: commands:")
    assert bridge.calls == []


@pytest.mark.parametrize(
    "command",
    [
        '{"op": "post", "text": "reply", "reply_to": 1.9}',
        '{"op": "post", "text": "reply", "reply_to": true}',
        '{"op": "post", "text": "reply", "reply_to": 1e999}',
        '{"op": "read", "since_seq": 2.7}',
    ],
)
def test_malformed_numbers_get_the_normal_error_and_make_no_room_call(bridge: FakeRoom, command: str):
    """Review round 4, R4-02, over the real A2A HTTP path: no silent truncation
    to another event, and no internal error leaking out as JSON-RPC -32603."""
    reply = _send(command)
    assert reply.startswith("error: ") and "must be an integer" in reply
    assert bridge.calls == []


@pytest.mark.parametrize(
    "command",
    [
        '{"op": "post", "text": "x", "reply_to": %s}' % ("9" * 4301),
        '{"op": "read", "since_seq": -%s}' % ("9" * 4301),
        '{"op": "read", "limit": %s}' % ("9" * 10000),
        '{"op": "post", "text": "x", "evidence_refs": %s}' % ("[" * 10000 + "]" * 10000),
    ],
    # Short ids: pytest exports the id in an environment variable, and Windows
    # caps those at 32,767 characters.
    ids=["4301-digit-reply_to", "negative-4301-digit-since_seq", "10000-digit-limit", "deep-nesting"],
)
def test_input_the_decoder_rejects_gets_the_normal_error_and_makes_no_room_call(
    bridge: FakeRoom, command: str
):
    """Review round 5, R5-01, over the real A2A HTTP path: an over-long integer
    literal (ValueError) and deep nesting (RecursionError) end as the ordinary
    error artifact, not as JSON-RPC -32603 carrying a Python message."""
    reply = _send(command)
    assert reply.startswith("error: invalid JSON")
    assert bridge.calls == []


def test_an_unforeseen_failure_is_reported_without_its_python_detail(bridge: FakeRoom, capfd):
    bridge.raises = RuntimeError("secret internal detail")
    reply = _send("topics")
    assert reply == "error: internal bridge error"
    assert "secret internal detail" in capfd.readouterr().err


def test_room_error_is_reported_as_error_not_success(bridge: FakeRoom):
    bridge.reply = {"ok": False, "error": "topic must match [a-z0-9][a-z0-9_-]{0,31}"}
    assert _send("post #claims hi").startswith("error: topic must match")


def test_unreachable_room_is_reported(bridge: FakeRoom):
    bridge.raises = RoomUnavailable("room at http://127.0.0.1:7334/mcp did not answer (OSError)")
    assert _send("topics").startswith("error: room at")


def _raw_post(headers: dict[str, str]) -> httpx.Response:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "SendMessage",
        "params": {
            "message": {
                "messageId": "00000000-0000-0000-0000-000000000001",
                "role": "ROLE_USER",
                "parts": [{"text": "post #general injected"}],
            }
        },
    }
    return httpx.post(
        f"http://{HOST}:{PORT}/",
        json=body,
        headers={"A2A-Version": "1.0", **headers},
        timeout=10,
    )


def test_a_foreign_host_header_is_refused_before_the_room_is_called(bridge: FakeRoom):
    """Review round 6 (Grok): DNS rebinding. A page whose host name resolves to
    127.0.0.1 reached the executor and could post into the shared room."""
    assert _raw_post({"Host": "evil.example:7335"}).status_code == 400
    assert bridge.calls == []


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "http://127.0.0.1.evil.example"])
def test_a_foreign_origin_is_refused_before_the_room_is_called(bridge: FakeRoom, origin: str):
    assert _raw_post({"Origin": origin}).status_code == 403
    assert bridge.calls == []


def test_loopback_host_and_origin_still_reach_the_room(bridge: FakeRoom):
    assert _raw_post({"Origin": f"http://localhost:{PORT}"}).status_code == 200
    assert _raw_post({}).status_code == 200
    assert [tool for tool, _ in bridge.calls] == ["room_broadcast", "room_broadcast"]
```

```python
"""Invariants: the bridge is a client of the room, not a second writer.

Production change that would make these fail: the bridge importing the room
package (and so opening events.jsonl with its own seq counter), claiming or
releasing paths over A2A, or taking Hermes' port.
"""

from __future__ import annotations

import ast
from pathlib import Path

import packages.a2a_mesh.room_bridge as bridge

_SOURCE = Path(bridge.__file__).read_text(encoding="utf-8")


def test_bridge_imports_nothing_from_the_room_package():
    tree = ast.parse(_SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("packages.coordination_room")
        elif isinstance(node, ast.Import):
            assert not any(a.name.startswith("packages.coordination_room") for a in node.names)


def test_bridge_calls_only_post_read_topics_tools():
    called = {
        node.value
        for node in ast.walk(ast.parse(_SOURCE))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("room_")
    }
    assert called == {"room_topics", "room_read", "room_broadcast"}


def test_default_port_is_not_hermes_a2a_port():
    assert bridge.DEFAULT_PORT != 9900


def test_agent_name_is_not_a_controller():
    assert bridge.AGENT_NAME == "flossi0ullk-a2a-room-bridge"
```

```python
"""A2A client -> bridge -> real FastMCP room -> events.jsonl and BOARD.md.

Production change that would make this fail: the bridge writing anywhere but
through the room's own MCP tools, or the A2A post not reaching the board.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from packages.a2a_mesh.client import send_hello  # noqa: E402
from packages.a2a_mesh.room_bridge import McpRoomPort, RoomUnavailable, build_app  # noqa: E402
from packages.coordination_room.tests.room_server import (  # noqa: E402
    free_port,
    pin_room_env,
    reload_server,
    serving,
)

HOST = "127.0.0.1"


def test_a2a_post_lands_on_the_room_board(tmp_path: Path, monkeypatch):
    log = pin_room_env(monkeypatch, tmp_path)
    room_port, bridge_port = free_port(), free_port()
    port = McpRoomPort(f"http://{HOST}:{room_port}/mcp")
    bridge = f"http://{HOST}:{bridge_port}"
    with serving(reload_server().mcp.streamable_http_app(), room_port):
        with serving(build_app(HOST, bridge_port, port), bridge_port):
            reply = json.loads(send_hello(bridge, "post #inquiries who owns the bridge?"))
            assert reply["ok"] is True
            assert reply["topic"] == "inquiries"
            topics = json.loads(send_hello(bridge, "topics"))
            assert [t["topic"] for t in topics["topics"]] == ["inquiries"]
        # The room answered and refused the call: reported as that, not as silence.
        with pytest.raises(RoomUnavailable, match="rejected room_read"):
            asyncio.run(port.call("room_read", {"since_seq": "not a number"}))

    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").split("\n") if line.strip()]
    assert len(rows) == 1
    assert rows[0]["agent_id"] == "a2a:anonymous"
    assert rows[0]["topic"] == "inquiries"
    assert "who owns the bridge?" in (log.parent / "BOARD.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run them to see them fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/a2a_mesh/tests/test_room_bridge_parse.py
```

Expected: collection error, `ModuleNotFoundError: No module named 'packages.a2a_mesh.room_bridge'`.

- [ ] **Step 3: Write the implementation.**

```python
"""A2A skill adapter for the coordination room board.

A client of the room, never a writer: the room daemon (:7334) owns events.jsonl
(one writer per surface), so this module speaks to it over MCP and imports
nothing from packages.coordination_room. A2A is a peer handshake here, not a
controller; the bridge posts and reads, and never claims or releases a path.
"""

from __future__ import annotations

import json
import os
import re
import sys
import traceback
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit

import uvicorn
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TaskState,
)
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import PlainTextResponse

AGENT_NAME = "flossi0ullk-a2a-room-bridge"
# 9900 is Hermes' own A2A listener (gateway.platforms.a2a); never reuse it.
DEFAULT_PORT = 7335
ROOM_URL = "http://127.0.0.1:7334/mcp"
DEFAULT_READ_LIMIT = 20
READ_LIMIT_MAX = 100
SENDER_MAX = 32
INTEGER_MAX = 2**53  # the largest integer every JSON implementation carries exactly
# Room text is capped at 4096 bytes and 16 refs at 512 characters each; a
# command far beyond that is not one the room would take anyway.
COMMAND_MAX = 32 * 1024

_DIGITS = re.compile(r"[0-9]{1,16}")

_TOPIC = r"[a-z0-9][a-z0-9_-]{0,31}"
_POST = re.compile(rf"post\s+#(?P<topic>{_TOPIC})\s+(?P<text>.+)", re.S)
_READ = re.compile(rf"read(?:\s+#(?P<topic>{_TOPIC}))?(?:\s+since=(?P<since>\d+))?")
_OPS = ("post", "read", "topics")
USAGE = (
    "commands: `topics` | `read [#topic] [since=N]` | `post #topic text` | "
    'JSON {"op": "post|read|topics", "topic", "text", "evidence_refs", '
    '"reply_to", "since_seq", "limit", "sender"}'
)


class CommandError(ValueError):
    """The A2A message is not a board command."""


class RoomUnavailable(RuntimeError):
    """The room daemon did not answer."""


@dataclass(frozen=True)
class BoardCommand:
    op: str
    topic: str | None = None
    text: str = ""
    evidence_refs: tuple[str, ...] = ()
    reply_to: int | None = None
    since_seq: int = 0
    limit: int = DEFAULT_READ_LIMIT
    sender: str = "anonymous"


def agent_id_for(sender: str) -> str:
    """A2A callers are unauthenticated: always prefixed so they cannot pose as a harness."""
    clean = re.sub(r"[^A-Za-z0-9_.-]", "-", sender)[:SENDER_MAX]
    return f"a2a:{clean or 'anonymous'}"


def _integer(value: Any, name: str) -> int:
    """A JSON integer, or a plain decimal string. Never converted from anything else.

    `int()` would turn 1.9 and true into 1, so a reply would silently join
    another thread, and it raises OverflowError on 1e999 (which JSON decodes
    to infinity). An event number is taken as written or refused.
    """
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise CommandError(f"{name} must be an integer")
    if isinstance(value, str):
        if not _DIGITS.fullmatch(value):
            raise CommandError(f"{name} must be an integer")
        value = int(value)
    if abs(value) > INTEGER_MAX:
        raise CommandError(f"{name} is out of range")
    return value


def _parse_json(body: str) -> BoardCommand:
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CommandError(f"invalid JSON: {exc.msg}") from exc
    except (ValueError, RecursionError) as exc:
        # Not JSONDecodeError: an integer literal longer than the interpreter's
        # digit limit raises plain ValueError inside the decoder, and deep
        # nesting raises RecursionError. Both are a bad command, not a crash.
        raise CommandError("invalid JSON: a number is too long or the nesting too deep") from exc
    if not isinstance(obj, dict) or obj.get("op") not in _OPS:
        raise CommandError(USAGE)
    refs = obj.get("evidence_refs") or []
    if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
        raise CommandError("evidence_refs must be a list of strings")
    reply_to = None if obj.get("reply_to") is None else _integer(obj["reply_to"], "reply_to")
    since_seq = _integer(obj.get("since_seq", 0), "since_seq")
    limit = _integer(obj.get("limit", DEFAULT_READ_LIMIT), "limit")
    if reply_to is not None and reply_to < 1:
        raise CommandError("reply_to must be at least 1")
    if since_seq < 0:
        raise CommandError("since_seq must not be negative")
    topic, text, sender = obj.get("topic"), obj.get("text", ""), obj.get("sender", "anonymous")
    if topic is not None and not isinstance(topic, str):
        raise CommandError("topic must be a string")
    if not isinstance(text, str) or not isinstance(sender, str):
        raise CommandError("text and sender must be strings")
    if obj["op"] == "post" and not text.strip():
        raise CommandError("post needs text")
    return BoardCommand(
        op=obj["op"],
        topic=topic,
        text=text.strip(),
        evidence_refs=tuple(refs),
        reply_to=reply_to,
        since_seq=since_seq,
        limit=max(1, min(limit, READ_LIMIT_MAX)),
        sender=sender,
    )


def parse_command(raw: str) -> BoardCommand:
    """Deterministic grammar. Anything else is an error, never a guess."""
    body = raw.strip()
    if not body:
        raise CommandError("empty command")
    if len(body) > COMMAND_MAX:
        raise CommandError(f"command exceeds {COMMAND_MAX} characters")
    if body.startswith("{"):
        return _parse_json(body)
    if body == "topics":
        return BoardCommand(op="topics")
    match = _POST.fullmatch(body)
    if match:
        return BoardCommand(op="post", topic=match["topic"], text=match["text"].strip())
    match = _READ.fullmatch(body)
    if match:
        return BoardCommand(
            op="read",
            topic=match["topic"],
            since_seq=_integer(match["since"] or "0", "since_seq"),
        )
    raise CommandError(USAGE)


class RoomPort(Protocol):
    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class McpRoomPort:
    """Calls the room's MCP tools over streamable HTTP. One short session per call."""

    def __init__(self, url: str = ROOM_URL) -> None:
        self._url = url

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            async with streamable_http_client(self._url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool, arguments)
            text = result.content[0].text if result.content else ""
            if result.isError:
                # The room answered and refused: say that, not "did not answer".
                raise RoomUnavailable(f"room at {self._url} rejected {tool}: {text[:200]}")
            return json.loads(text)
        except RoomUnavailable:
            raise
        except Exception as exc:  # anyio wraps transport errors in ExceptionGroup
            raise RoomUnavailable(
                f"room at {self._url} did not answer ({type(exc).__name__})"
            ) from exc


async def run_command(port: RoomPort, command: BoardCommand) -> dict[str, Any]:
    if command.op == "topics":
        return await port.call("room_topics", {})
    if command.op == "read":
        args: dict[str, Any] = {"since_seq": command.since_seq, "limit": command.limit}
        if command.topic:
            args["topic"] = command.topic
        return await port.call("room_read", args)
    args = {"agent_id": agent_id_for(command.sender), "text": command.text}
    if command.topic:
        args["topic"] = command.topic
    if command.evidence_refs:
        args["evidence_refs"] = list(command.evidence_refs)
    if command.reply_to is not None:
        args["reply_to"] = command.reply_to
    return await port.call("room_broadcast", args)


class _BoardExecutor(AgentExecutor):
    def __init__(self, room: RoomPort) -> None:
        self._room = room

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("Processing request..."),
        )
        raw = get_message_text(context.message) if context.message else ""
        try:
            reply = await run_command(self._room, parse_command(raw))
            failure = None if reply.get("ok", True) else str(reply.get("error", "room error"))
        except (CommandError, RoomUnavailable) as exc:
            reply, failure = None, str(exc)
        except Exception:
            # Last resort. Anything unforeseen still ends as the normal error
            # artifact: the caller gets no Python message or traceback, and the
            # detail goes to this process's stderr for whoever runs the bridge.
            traceback.print_exc(file=sys.stderr)
            reply, failure = None, "internal bridge error"
        if failure is not None:
            await updater.add_artifact(
                parts=[new_text_part(text=f"error: {failure}", media_type="text/plain")]
            )
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=new_text_message(failure),
            )
            return
        await updater.add_artifact(
            parts=[
                new_text_part(
                    text=json.dumps(reply, ensure_ascii=False), media_type="text/plain"
                )
            ]
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("Request is completed!"),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancel is not supported.")


_LOOPBACK_HOSTS = ("127.0.0.1", "localhost")


class _LoopbackOriginOnly:
    """Refuse a request a web page made from another site.

    Any page can make a browser POST to a loopback port. Such a request names
    its site in an Origin header; a local agent's HTTP client sends none.
    """

    def __init__(self, app) -> None:
        self._app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "http":
            origin = dict(scope["headers"]).get(b"origin")
            if origin is not None and (
                urlsplit(origin.decode("latin-1")).hostname not in _LOOPBACK_HOSTS
            ):
                refusal = PlainTextResponse("origin not allowed", status_code=403)
                await refusal(scope, receive, send)
                return
        await self._app(scope, receive, send)


def build_app(host: str, port: int, room: RoomPort) -> Starlette:
    base = f"http://{host}:{port}"
    skill = AgentSkill(
        id="coordination_board",
        name="Coordination board",
        description="Post to and read the FLOSSI0ULLK coordination room board.",
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["coordination", "board"],
        examples=["topics", "read #announcements", "post #inquiries who owns packages/x?"],
    )
    card = AgentCard(
        name=AGENT_NAME,
        description="Post/read bridge to the coordination room. Cannot claim or release paths.",
        version="0.0.1",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC", url=base, protocol_version="1.0"
            )
        ],
        skills=[skill],
    )
    handler = DefaultRequestHandler(
        agent_executor=_BoardExecutor(room),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = []
    routes.extend(create_agent_card_routes(card))
    routes.extend(create_jsonrpc_routes(handler, "/"))
    # Binding to loopback does not stop a browser being steered here: a page can
    # point its own host name at 127.0.0.1 (DNS rebinding) or simply POST across
    # origins. So the Host must be loopback and any Origin must be too.
    return Starlette(
        routes=routes,
        middleware=[
            Middleware(TrustedHostMiddleware, allowed_hosts=list(_LOOPBACK_HOSTS)),
            Middleware(_LoopbackOriginOnly),
        ],
    )


def serve_room_bridge(host: str, port: int, room: RoomPort) -> None:
    """Serve the bridge on loopback. Blocks."""
    if host != "127.0.0.1":
        raise ValueError("serve_room_bridge binds 127.0.0.1 only")
    uvicorn.run(
        build_app(host, port, room),
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    from packages.mcp_daemon import claim_singleton

    if not claim_singleton("a2a_room_bridge.pid"):
        print("[FLOSS A2A] room bridge already running; exiting.", file=sys.stderr)
        raise SystemExit(0)
    serve_room_bridge(
        "127.0.0.1",
        int(os.environ.get("A2A_ROOM_BRIDGE_PORT", DEFAULT_PORT)),
        McpRoomPort(os.environ.get("COORDINATION_ROOM_URL", ROOM_URL)),
    )
```

- [ ] **Step 4: Run both packages.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests packages/a2a_mesh/tests
```

Expected: no failures; measured `235 passed, 1 skipped` (`234 passed, 2 skipped` where no `.mcp.json` exists above the checkout). The e2e test starts a real FastMCP room and the bridge in-process on free ports.

- [ ] **Step 5: Lint.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m ruff check --isolated packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_parse.py packages/a2a_mesh/tests/test_room_bridge_pair.py packages/a2a_mesh/tests/test_room_bridge_invariants.py packages/a2a_mesh/tests/test_room_bridge_e2e.py
```

Expected: `All checks passed!`

- [ ] **Step 6: Commit.**

```bash
git add -- packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_parse.py packages/a2a_mesh/tests/test_room_bridge_pair.py packages/a2a_mesh/tests/test_room_bridge_invariants.py packages/a2a_mesh/tests/test_room_bridge_e2e.py
git commit -F- -- packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_parse.py packages/a2a_mesh/tests/test_room_bridge_pair.py packages/a2a_mesh/tests/test_room_bridge_invariants.py packages/a2a_mesh/tests/test_room_bridge_e2e.py <<'EOF'
feat(a2a-mesh): room bridge, A2A post/read as a client of the room
EOF
```

---

### Task 9: Bridge lifecycle

**Files:**
- Edit: `scripts/start_mcp_daemons.ps1`
- Edit: `scripts/stop_mcp_daemons.ps1`
- Edit: `scripts/tests/test_daemon_scope.py`
- Edit: `docs/agent-memory/project/coordination-room-v0.md`

**Interfaces:**
- Consumes: Task 2's `-Only` / `-DryRun` selector, `Start-Daemon`, the stop script's `$pidFileFor` map.
- Produces: `bridge` as a selectable name in both scripts. It is in the stop script's default selection (a full stop stops it) and not in the start script's (it starts only when named, never from the scheduled task); bridge daemon on `127.0.0.1:7335`, PID file `a2a_room_bridge.pid`.

This task edits scripts and tests them with stand-ins. It does not run them against real daemons. If `a2a-sdk` is missing from the daemon's Python, the bridge exits at import; `Start-Daemon` reports it and the script adds it to `$skipped` instead of aborting. That is the intended failure mode. The line-ending note in Task 2 applies here too.

- [ ] **Step 1: Extend the test first.** In `scripts/tests/test_daemon_scope.py`:

Edit 1. Replace:

```python
        "coordination_room.pid",
        "omniroute",
```

with:

```python
        "coordination_room.pid",
        "a2a_room_bridge.pid",
        "omniroute",
```

Edit 2. Replace:

```python
    done = _run(shell, script, "-Only", "everything", "-DryRun", agent_dir=tmp_path)
    assert done.returncode != 0
    assert "WOULD_" not in done.stdout
```

with:

```python
    done = _run(shell, script, "-Only", "everything", "-DryRun", agent_dir=tmp_path)
    assert done.returncode != 0
    assert "WOULD_" not in done.stdout


@shells
def test_bridge_is_selected_on_its_own(shell: str, tmp_path: Path):
    start = _run(shell, "start_mcp_daemons.ps1", "-Only", "bridge", "-DryRun", agent_dir=tmp_path)
    stop = _run(shell, "stop_mcp_daemons.ps1", "-Only", "bridge", "-DryRun", agent_dir=tmp_path)
    assert start.returncode == 0 and stop.returncode == 0, start.stdout + stop.stdout
    assert [s.split()[3] for s in _lines(start, "WOULD_START")] == ["packages.a2a_mesh.room_bridge"]
    assert [s.split()[3] for s in _lines(stop, "WOULD_STOP")] == ["a2a_room_bridge.pid"]
    assert "coordination room log" not in start.stdout


@shells
def test_bridge_is_opt_in_for_start_but_stopped_by_a_full_stop(shell: str, tmp_path: Path):
    """Review round 3, R3-05: the scheduled task (no arguments) must not start
    the optional bridge; a no-argument stop still stops it."""
    start = _run(shell, "start_mcp_daemons.ps1", "-DryRun", agent_dir=tmp_path)
    stop = _run(shell, "stop_mcp_daemons.ps1", "-DryRun", agent_dir=tmp_path)
    assert "packages.a2a_mesh.room_bridge" not in start.stdout
    assert "WOULD_STOP a2a_room_bridge.pid" in stop.stdout
```

- [ ] **Step 2: Run it to see it fail.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q scripts/tests/test_daemon_scope.py
```

Expected: the stop default-selection test and the two new bridge tests fail; the scripts refuse `-Only bridge` because `bridge` is not a known name yet.

- [ ] **Step 3: Edit `start_mcp_daemons.ps1`.**

Edit 1. Replace:

```powershell
# -Only picks which daemons to start (default: all, so the scheduled task is
# unchanged). A room deployment runs `-Only room`, so a daemon someone stopped
# on purpose stays stopped. Several names go in one comma-separated argument
# (`-Only room,ensemble`). -DryRun prints WOULD_START lines and starts nothing.
```

with:

```powershell
# -Only picks which daemons to start. The default is every daemon except the
# optional A2A bridge, so the scheduled task is unchanged; the bridge starts
# only when named (`-Only bridge`). A room deployment runs `-Only room`, so a
# daemon someone stopped on purpose stays stopped. Several names go in one
# comma-separated argument (`-Only room,ensemble`). -DryRun prints WOULD_START
# lines and starts nothing.
```

Edit 2. Replace:

```powershell
$knownDaemons = @('consensus', 'ensemble', 'room', 'omniroute')
```

with:

```powershell
$knownDaemons = @('consensus', 'ensemble', 'room', 'bridge', 'omniroute')
```

Edit 3. Replace:

```powershell
    if (-not $roomProc) { $skipped += "coordination room (:7334) - exited immediately after launch" }
}
```

with:

```powershell
    if (-not $roomProc) { $skipped += "coordination room (:7334) - exited immediately after launch" }
}

# Start A2A room bridge (port 7335). A client of the room on :7334: it never
# writes the log. :9900 is Hermes' own A2A listener, so it is not reused here.
if ($Only -contains 'bridge') {
    $bridgeProc = Start-Daemon $py "packages.a2a_mesh.room_bridge" "A2A room bridge (:7335)" $workspace
    if (-not $bridgeProc) { $skipped += "A2A room bridge (:7335) - exited immediately after launch" }
}
```

- [ ] **Step 4: Edit `stop_mcp_daemons.ps1`.**

Edit 1. Replace:

```powershell
# Kills: consensus (:7331), ensemble (:7332), coordination room (:7334), OmniRoute (:20128).
```

with:

```powershell
# Kills: consensus (:7331), ensemble (:7332), coordination room (:7334), A2A room bridge (:7335), OmniRoute (:20128).
```

Edit 2. Replace:

```powershell
    [string[]]$Only = @('consensus', 'ensemble', 'room', 'omniroute'),
```

with:

```powershell
    [string[]]$Only = @('consensus', 'ensemble', 'room', 'bridge', 'omniroute'),
```

Edit 3. Replace:

```powershell
$knownDaemons = @('consensus', 'ensemble', 'room', 'omniroute')
```

with:

```powershell
$knownDaemons = @('consensus', 'ensemble', 'room', 'bridge', 'omniroute')
```

Edit 4. Replace:

```powershell
    room      = 'coordination_room.pid'
}
```

with:

```powershell
    room      = 'coordination_room.pid'
    bridge    = 'a2a_room_bridge.pid'
}
```

- [ ] **Step 5: Run the test and parse-check under both shells.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q scripts/tests/test_daemon_scope.py
```

```powershell
foreach ($f in 'scripts/start_mcp_daemons.ps1', 'scripts/stop_mcp_daemons.ps1') { $e = $null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $f), [ref]$null, [ref]$e) | Out-Null; "$f errors: $($e.Count)" }
```

Expected: `28 passed`; both scripts `errors: 0` in each shell.

- [ ] **Step 6: Correct the how-to.** In `docs/agent-memory/project/coordination-room-v0.md` replace:

```
- Not A2A (task handshake) — `feat/a2a-harness-mesh`.
```

with:

```
- Not A2A (task handshake). An optional A2A bridge (`packages/a2a_mesh/room_bridge.py`, `127.0.0.1:7335`, started alone with `-Only bridge`) can post and read as `a2a:<sender>`, an attribution label and not authentication; it cannot claim or release.
```

The Task 6 Step 8 rule applies here too: no materializer run from this worktree.

- [ ] **Step 7: Commit.**

```bash
git add -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 scripts/tests/test_daemon_scope.py docs/agent-memory/project/coordination-room-v0.md
git commit -F- -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 scripts/tests/test_daemon_scope.py docs/agent-memory/project/coordination-room-v0.md <<'EOF'
feat(daemons): start and stop the A2A room bridge on :7335, selectable with -Only bridge
EOF
```

---

## Final verification (per phase, before a pull request)

- [ ] The coordination-v1 green set, on the base and on this branch, with the same environment:

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
```

  Criterion: no new failures versus the base, compared per test case. Run the base in a clean worktree of `feat/coordination-room-rebased`. The author's run for this revision is under Truth status at the top; any later change to this plan needs its own paired run.
- [ ] The same comparison on Linux, or the required `green-set` CI job on the pull request: green, or red only where the base already is (Task 0 Step 5).
- [ ] `ruff check --isolated packages/coordination_room packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_*.py scripts/tests/test_daemon_scope.py` clean. (`packages/a2a_mesh/tests/test_helloworld_pair.py` already carries one unused `import pytest` from the merged branch; leave it, it is not this plan's file.)
- [ ] `spec_gate.py --check`: the same three findings as Task 0, no new ones.
- [ ] Each acceptance behaviour listed at the top has a named passing test or a recorded observation.
- [ ] `git branch -r --contains 4aab13e` prints a remote branch (Task 0 Step 1, third question). Then open the pull request against `feat/coordination-room-rebased`, never against `feat/coordination-room`, with `ROLLBACK_COMMIT` in its description. A pull request does not authorize deployment.

---

## Deployment (operator-gated, separate from the tasks)

✅ Steps 0 to 6 were executed once against the live bus, on 2026-10-11 (see the Execution record near the top). ✅ The Rollback blocks were executed once, on 2026-10-12, followed by a redeploy. ⚠️ The bridge block has not been executed. When this section was written the room daemon was down and none of it had run. What was tested: the `-Only` selector (Task 2: dry runs and stand-in interpreters) and every helper used below (`packages/coordination_room/deploy.ps1`, by `tests/test_deploy_helpers.py`: fake checkouts, a scratch port, a scratch git repository and a real scratch room, under Windows PowerShell 5.1 and PowerShell 7). The blocks themselves, as sequences, were not run. Each run needs its own operator go-ahead; the Task 0 approval and a merged pull request do not cover it.

Run every block in **one** PowerShell session (5.1 or 7), in order. The helpers set `$ErrorActionPreference = 'Stop'` and each throws on a failed precondition, so a block stops at the first failure. If anything throws, stop there: read the message, do not run the next block, and do not work around it by hand.

**If a helper says a line of the log is not readable JSON:** stop. The room itself skips such a line and carries on (`room_state` reports `log_skipped_lines`), but a deployment does not. Copy the log (`Copy-Item $log "$log.copy-<UTC time>"`), look at the line, and decide with the operator. Never edit the log in place.

**0. Serve from a pinned checkout, not from a worktree somebody is editing.** `DEPLOY_COMMIT` is the full hash of the merged commit being deployed.

```powershell
$repo = 'C:\~shit\FLOSS'
$deployCommit = '<DEPLOY_COMMIT>'
$serve = "$repo\.worktrees\room-serve-$($deployCommit.Substring(0, 8))"
. "$repo\.worktrees\coordination-room-rebased\packages\coordination_room\deploy.ps1"   # for New-PinnedCheckout
New-PinnedCheckout $repo $deployCommit $serve
. "$serve\packages\coordination_room\deploy.ps1"                            # the helpers of the commit being deployed
"log: $log"
```

The last line must print `C:\~shit\.agent-surface\rooms\default\events.jsonl`. If your execution policy refuses to dot-source the file, run `Set-ExecutionPolicy -Scope Process RemoteSigned` in this session first.

**1. Record what is running.** Read-only; for the record, not for comparison. Skip the second line if the room is down.

```powershell
Get-Content (Join-Path $agent 'coordination_room.pid') -ErrorAction SilentlyContinue
Invoke-Room $serve 'room_state' | ConvertTo-Json -Depth 5
```

Keep the output, with the time, in the pull request or in `docs/reviews/2026-10-02-room-board-v1/`. A v0.1 room reports `claims`, `last_seq`, `speakers` only; it cannot say which checkout it serves.

**2. Stop only the room.** Preview first; the preview must name exactly `coordination_room.pid`.

```powershell
$preview = Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $preview 'WOULD_STOP' 'coordination_room.pid'
Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null
```

The real stop kills only a process its identity check calls `OURS`. If it reports `identity UNVERIFIABLE` it exits 1, `Invoke-DaemonScript` throws, and you stop here.

**3. Prove the slot and port are free, then read the settled log.**

```powershell
Assert-PortFree 7334 'coordination_room.pid'
$settled = Get-SettledSeq
"settled seq: $settled"
```

`$settled` is read only now, after the previous owner has stopped. From the moment a room serves again it is a lower bound, not something to compare a later tail with.

**4. Start only the room.** Preview first; it must start exactly the room and pin it to `$log`.

```powershell
$preview = Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $preview 'WOULD_START' 'packages.coordination_room.server'
Assert-PinnedLog $preview
Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'room') | Out-Null
```

A live process is not yet a working room: the room is built on its first tool call. Step 5 is that call.

**5. Assert the bus before any post.**

```powershell
$state = Invoke-Room $serve 'room_state'
Assert-RoomState $state $serve $settled
```

It checks, and throws on any failure: the room names `$log` as its log and `BOARD.md` beside it as its board; its root is `$serve`; its `last_seq` is at or past `$settled`; it skipped no log lines. If it throws, roll back. An agent session that was connected before the restart may need to reconnect to see the new tools.

**6. Smoke: prove your own post is in the shared log.** A moved tail proves nothing here, because another agent's post moves it too.

```powershell
$marker = New-SmokeMarker
$reply = Invoke-Room $serve 'room_broadcast' @{
    agent_id = 'deploy-smoke'
    text = "deployed $deployCommit $marker"
    topic = 'announcements'
    evidence_refs = @('file:docs/specs/coordination-room.spec.md')
}
if ($reply.evidence_status -cne 'resolved') { throw "Evidence lookup said '$($reply.evidence_status)'. Roll back." }
Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
$after = Invoke-Room $serve 'room_state'
if ($after.board_last_error) { throw "The board is not being written: $($after.board_last_error)" }
"deployed; smoke post is seq $($reply.seq); board as of $($after.board_as_of)"
```

`Assert-SmokeEvent` passes only if the shared log's row with that `seq` is a broadcast by `deploy-smoke` carrying the marker; rows other agents add before or after are fine.

**After a logon or reboot the room is not running.** Nothing in this plan changes what starts at logon. The documented scheduled task runs `C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1`, and the primary checkout is on `feat/coordination-room`, whose start script has no room block at all. Until the operator decides what the logon task should point at (Decisions, item 3), bringing the room back is step 4 again, from `$serve`.

**Bridge (Phase 2 only, if it was built).** Start it alone, after the room. It is never started by a no-argument start.

```powershell
$preview = Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'bridge', '-DryRun')
Assert-OnlyAction $preview 'WOULD_START' 'packages.a2a_mesh.room_bridge'
Invoke-DaemonScript $serve 'start_mcp_daemons.ps1' @('-Only', 'bridge') | Out-Null
$card = Invoke-RestMethod 'http://127.0.0.1:7335/.well-known/agent-card.json'
if ($card.name -cne 'flossi0ullk-a2a-room-bridge') { throw "Unexpected agent card: $($card.name)" }
```

Then one read through it, from `$serve`, which proves it reaches the same bus without adding a row:

```bash
env -u PYTHONPATH C:/Python313/python.exe -c "from packages.a2a_mesh.client import send_hello; print(send_hello('http://127.0.0.1:7335', 'topics'))"
```

Expected: the same topics `Invoke-Room $serve 'room_topics'` returns.

**Rollback.** Same session, helpers loaded.

1. Stop the bridge first if it runs; a v0.1 room has no `room_topics` and rejects the bridge's new arguments. Then stop the room, prove both ports free, and read the settled log.

```powershell
if (Test-Path (Join-Path $agent 'a2a_room_bridge.pid')) {
    Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'bridge') | Out-Null
}
Assert-PortFree 7335 'a2a_room_bridge.pid'
$preview = Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $preview 'WOULD_STOP' 'coordination_room.pid'
Invoke-DaemonScript $serve 'stop_mcp_daemons.ps1' @('-Only', 'room') | Out-Null
Assert-PortFree 7334 'coordination_room.pid'
$settled = Get-SettledSeq
"settled seq: $settled"
```

2. Archive the board; never delete it. v0.1 does not maintain it, and a stale view would mislead.

```powershell
$board = Join-Path (Split-Path $log) 'BOARD.md'
if (Test-Path $board) {
    Rename-Item $board ("BOARD.superseded-{0}.md" -f (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))
}
```

3. Check out the rollback point and serve v0.1 from it, room only. `ROLLBACK_COMMIT` is the full hash recorded in the pull request (Task 2, Step 6).

```powershell
$rollbackCommit = '<ROLLBACK_COMMIT>'
$rollback = "$repo\.worktrees\room-rollback-$($rollbackCommit.Substring(0, 8))"
New-PinnedCheckout $repo $rollbackCommit $rollback
$preview = Invoke-DaemonScript $rollback 'start_mcp_daemons.ps1' @('-Only', 'room', '-DryRun')
Assert-OnlyAction $preview 'WOULD_START' 'packages.coordination_room.server'
Assert-PinnedLog $preview
Invoke-DaemonScript $rollback 'start_mcp_daemons.ps1' @('-Only', 'room') | Out-Null
```

4. Accept v0.1 by what it can report, then prove a post of yours is in the shared log. The client comes from `$serve`; it sends exactly the arguments it is given, so it works against v0.1.

```powershell
Assert-V01State (Invoke-Room $serve 'room_state') $settled
$marker = New-SmokeMarker
$reply = Invoke-Room $serve 'room_broadcast' @{ agent_id = 'deploy-smoke'; text = "rolled back to v0.1 $marker" }
Assert-SmokeEvent $reply.seq 'deploy-smoke' $marker
"rolled back; smoke post is seq $($reply.seq)"
```

`Assert-V01State` requires a `last_seq` at or past `$settled` and the same claims the log itself implies; if another agent claimed or released between the two readings it says so, and you run it again. `Assert-SmokeEvent` is the bus check v0.1 cannot fake: its paths are not reportable, but its post is either in the shared log or it is not. `tests/test_v01_compat.py` runs v0.1 code against a log this version wrote.

**What is left behind.** The pinned checkouts (`room-serve-*`, `room-rollback-*`), the implementation worktree and any `BOARD.superseded-*.md` stay until the operator removes them. No step here deletes a worktree, a branch, a directory or the log.

## Decisions left to the operator

1. **The file approval** (Task 0 Step 1, first question). The listed paths on one branch; nothing about deployment, merging or Phase 2.
2. **Claim precedence** (Task 0 Step 1, second question; finding B3). This plan assumes: enforced claims, when coordination-v1 lands them, are canonical for exclusivity; room claims are an advisory convention and are labelled so. If you want the room to be the authority instead, that is a design change to both plans, not an edit to this one.
3. **The base and the logon task.** `4aab13e` needs pushing before any pull request (Task 0 Step 1, third question). Separately: nothing starts the room at logon today, because the primary checkout's start script has no room block. Decide which checkout the logon task should run, or accept that the room is started by hand.
4. **Phase 2.** Deferred by default. Start it only when something will use an A2A bridge.
5. **Evidence lookup.** Kept, because labelling a post's evidence is the reason this work was proposed. A reviewer suggested the smaller version: store `evidence_refs` unchecked and add lookup later. That would drop `evidence.py`, the lookup budget and the `resolved` label. Your call; the plan as written keeps it.
6. **Untracked log.** `.agent-surface/rooms/default/events.jsonl` is untracked and not ignored in the root repo today; `BOARD.md` (and any `BOARD.superseded-*.md`) adds more untracked files that change on every post. Either ignore `.agent-surface/rooms/` in the root `.gitignore` or accept the noise. This plan does not touch the root repo.
7. **Evidence root.** `file:` refs are looked up under the room root, which the launcher sets to the serving checkout. A ref to a file outside it is `unresolved` by design.
8. **Scale.** The board is re-rendered from the whole log on each post: about 10 ms at 1,000 rows, 70 ms at 10,000 and 350 ms at 50,000 (a reviewer's measurement on Linux). Fine at today's 5 rows; revisit in the thousands.
9. **The memory materializer.** `scripts/materialize_shared_agent_memory.py`, run from any FLOSS worktree, plans an empty user-wide Claude memory index (finding B1). This plan only avoids it; a separate session is working on the fix.
10. **Coordination-v1 overlap.** Both plans edit `scripts/start_mcp_daemons.ps1`. Whichever lands second has a textual merge to do, and coordination-v1's "0-line diff vs rebased" check for `packages/coordination_room/` stops being true once this lands.
11. **How this gets reviewed from here.** Six rounds have each found things in what the previous round added, and the plan is now very long because it carries its code inline. One reviewer's suggestion, which the author agrees with: stop reviewing the document. Put Phase 1 on the branch as commits, let the tests and the CI job be the gate, and review the pull request's diff. Splitting it (Task 2's scripts as one pull request, the room as a second stacked on it) is possible because Task 2's commit stands alone.

## Self-review

- **Draft coverage.** `log.py` fields ride on `EventLog.append(**fields)`; `board.py` is Task 4; `room.py`/`gateway.py`/`server.py` are Tasks 5 and 6; spec/schema Task 1; daemon scripts Tasks 2 and 9; `a2a_mesh` Task 7; `room_bridge.py` Task 8. Topics, evidence refs, thread ids, intent, roster and the auto-updating board each have a test. The draft's `message_type`, `room_post`, `[VERIFIED]`, `:9900` and `limit=50` are deliberately not implemented.
- **Round 6 coverage (Grok).** Base and pull-request target: Task 0 Step 1 and Final verification. Bridge Host and Origin: `test_a_foreign_host_header_is_refused_before_the_room_is_called`, `test_a_foreign_origin_is_refused_before_the_room_is_called`, `test_loopback_host_and_origin_still_reach_the_room`; the room's own: `test_a_request_with_a_foreign_host_header_is_refused`. File digests: `test_file_ref_inside_root_resolves_and_publishes_no_digest`. M1: `test_a_slow_lookup_does_not_stall_other_callers`, `test_lookups_past_the_budget_are_skipped_not_waited_for`, `test_a_slow_commit_lookup_is_unresolved_not_an_error`. M2: `test_a_torn_last_line_does_not_take_the_room_down`, `test_rows_that_are_not_events_are_skipped_and_counted`, the helper check `torn-log-stops-deployment`. M3: `test_board_health_is_visible_in_state_and_recovers`, `test_board_failure_does_not_fail_the_post`. M4: `New-PinnedCheckout` for the serving checkout, the logon paragraph, Decision 3. M5: `test_a_claim_whose_row_was_not_written_does_not_exist`, `test_a_release_whose_row_was_not_written_keeps_the_holder`, `test_a_failed_append_does_not_use_up_a_seq`, `test_a_failed_log_write_is_a_json_error_not_an_exception`. M6: `test_an_old_claim_is_questioned_not_expired`, `test_releasing_a_path_nobody_holds_adds_no_row`, `test_board_says_names_are_not_authenticated`, the spec's "Claims do not expire". M7: `test_read_has_no_default_limit`, `test_read_returns_every_row_by_default`, `test_label_describes_the_lookup_and_says_when_it_ran` (now pins the order, not a one-second timestamp), `test_v01_compat.py`, `deploy_harness.ps1` committed with `test_deploy_helpers.py`, `client.py` so deployment is commands. M8: the path list in Task 0 Step 1. Minor: `test_board_failure_does_not_fail_the_post` stages inside its own temp directory; `test_several_names_go_in_one_comma_separated_argument`, `test_a_second_bare_name_is_an_error_not_a_silent_drop`; free ports in every test this plan adds; the `"\u2028"` escape; the line-ending note; `test_a_staging_file_left_by_a_killed_writer_is_cleared`; upper-case commit hex; the bridge saying "rejected" when the room refused a call.
- **Rounds 1 to 5 coverage.** As before; the tests named in earlier revisions are all still present, some extended. `Assert-SmokeEvent`, `Get-LogRow`, `Assert-OnlyAction` and `New-PinnedCheckout` (formerly `New-RollbackCheckout`) now live in `deploy.ps1` and are exercised by the committed harness.
- **Placeholders.** None in code: every file body and every edit pair is generated from files that were executed. `<paste verbatim>`, `<DEPLOY_COMMIT>` and `<ROLLBACK_COMMIT>` are values that do not exist until execution.
- **Type consistency.** `board_path`, `check_board_path`, `BoardPathError`, `evidence_status`, `evidence_checked`, `evidence_checked_at`, `thread_id`, `reply_to`, `topic_of`, `resolve_all`, `_tools`, `_tools_instance`, `call_tool`, `Invoke-Room`, `Assert-RoomState`, `Assert-V01State`, `New-PinnedCheckout` and `agent_id_for` are spelled identically across tasks, the schema, the helpers and the tests.
- **Not verified here.** Linux, and the CI job; a clean-runner install (this machine's installed dependencies, MCP 1.27.0); MCP 2.x behaviour (from Codex's receipts); the Deployment blocks as sequences against a live daemon; live Hermes; crash, power-loss, load or soak behaviour. Revision 7 itself has had no independent review.
