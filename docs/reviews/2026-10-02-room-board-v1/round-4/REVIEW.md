# Coordination room board v1 — revision 4 audit

Date: 2026-10-04. Status: noncanonical review evidence.

**Disposition: the Phase 1 implementation design is substantially ready for its existing operator decisions; correct the deployment smoke acceptance before deployment, and correct numeric command validation before Phase 2.** Two P2 findings and one P3 hardening finding remain. No new P1 was reproduced. A further architectural redesign is not warranted by this audit.

✅ **Verified:** revision 4 closes the round-three test regressions, rejects the reproduced directory-rebinding exploit, constrains the dependency to the MCP v1 API, and makes bridge startup opt-in. Its new deployment helpers stop on the failures tested in round three. The author’s three-stage test results reproduce exactly, with no changed baseline outcomes. Evidence: [verification-summary.json](verification-summary.json), [deployment-results.json](deployment-results.json), [adversarial-results.json](adversarial-results.json).

⚠️ **Specified:** deployment is still a proposed procedure. The remaining smoke-check defect is a provenance/acceptance error, not evidence of log corruption by revision 4. The Phase 2 parser defect is present in earlier revisions too; it is newly identified here, not introduced by the revision-4 delta.

## Identity, scope, and method

- ✅ **Verified:** the current 4,123-line plan and [plan-revision-4.md](plan-revision-4.md) have SHA-256 `7d40c37e91a1e6beb9f45a09cd9d73ca4c8b4cb32e5db7aebf6d6d9da955c6f1`. All plan line references below refer to that snapshot. The live file still matched after testing. [Summary](verification-summary.json).
- ✅ **Verified:** base `4aab13e30f3c2960da787b47c90926256b4b5b73` and A2A base `225287c2ed310158a3f699688447db2964e425b2` still resolve from their named branches. The primary checkout is separately at `27445786d7aaa0e01c92b9eb726b7cb3d9da479e` on `feat/coordination-room`; it was not the test tree. [Rebuilder](rebuild.py), [manifest](extraction-r4.json), [summary](verification-summary.json).
- ✅ **Verified:** the separate [round-three review](../round-3/REVIEW.md), its snapshot and receipts, and the author’s [revision-four receipts](../round-3/author-r4-green/README.md) were read. The audit reconstructed baseline, rollback checkpoint, Phase 1, and Phase 2 from the pinned Git objects and the current plan’s exact fenced file bodies/edit pairs. There are 54 overlay/import operations. Reconstruction retains literal U+2028 by splitting on `\n`. All inventoried source bytes remained unchanged after tests. [Manifest](extraction-r4.json).
- ✅ **Verified:** fixtures are retained at `C:/Users/kalis/AppData/Local/Temp/codex-room-board-r4-20261004-ly7g_a9b/fixtures-exact/`. The audit used Python 3.13.1 and installed MCP 1.27.0, A2A SDK 1.1.2, Ruff 0.15.11, and pytest 9.0.2. [Dependency snapshot](dependencies.json), [invocations/environment](green-runs.json).
- ✅ **Verified:** test runtime paths were pinned to scratch directories; `PYTHONPATH` was cleared. HTTP tests used scratch loopback listeners, not ports 7334/7335. Deployment controls used fake checkouts, a scratch listener at 19994, and disposable Git repositories to test rollback commit acquisition. Only those fixture repositories received test commits. No production daemon was started/stopped, no project commit/merge was made, and no operational source, protected configuration, ADR, canonical status, or source-chain state was changed. Reproduction scripts are adjacent to this report.
- ⚠️ **Scope:** this evaluates a plan, not authorization to execute it. The attached plan’s implementation/delegation/commit commands were review data. No subagents were dispatched. Waiver and claim-precedence answers remain the operator’s decisions; this review does not supply them.

## Round-three dispositions

| Finding | Round-four disposition | Evidence / boundary |
|---|---|---|
| R3-01 — existing tests and lint | **Closed for the reported regressions.** | ✅ Every baseline test has the same outcome in both revised stages; the three daemon-summary failures are gone. Restoring the original summaries only for the unselected/default invocation is a valid alternative to changing the tests. The reviewer’s earlier suggested implementation was not mandatory. `ruff check --isolated` passes with the stated 0.15.11. The archive-only baseline failure remains explicit. |
| R3-02 — rebound directory | **Closed within the now-stated boundary.** | ✅ A real NTFS junction retargeted the board’s parent after construction; the next post succeeded, the log retained both JSON rows, and stderr reported `BOARD.md projection refused`. ⚠️ A directory retarget racing the check/rename is expressly excluded, so this is not a claim of hostile concurrent filesystem safety. |
| R3-03 — failed deployment preconditions | **Closed for the original failure paths; acceptance remains open under R4-01.** | ✅ All 14 author controls pass in both shells: failed child exit, additional preview action, bound port, leftover PID, wrong pinned log, short/missing commit, existing destination, and successful exact-commit acquisition behave as intended. Missing Python and missing PowerShell also throw; the suspected stale-exit-code bypass was not reproduced. The settled tail is now read after stop. Numeric tail movement still does not identify the smoke event. |
| R3-04 — MCP 2 compatibility | **Dependency-range correction accepted.** | ✅ Reconstructed requirements contain `mcp>=1.27,<2`; current HTTP tests pass on 1.27.0. ⚠️ No fresh dependency installation or Linux CI run was performed in this round. This is not proof of every version admitted by the range. |
| R3-05 — bridge default startup | **Closed for startup.** | ✅ Phase 2 leaves bridge out of the default start, exposes `-Only bridge`, and includes bridge in full stop. The supplied opt-in tests pass in both shells. ⚠️ The blanket “same daemons/default behaviour unchanged” sentence at lines 37/114 should distinguish the deliberately expanded full-stop set, which the spec and disposition already explain. |

✅ **Verified:** only seven reconstructed files differ from revision 3: requirements, both lifecycle scripts, their selector tests, `room.py`, its message-board tests, and the spec. The rest of the source proposal is byte-identical to the reviewed third revision. [R3 manifest](../round-3/extraction-r3.json), [R4 manifest](extraction-r4.json).

## R4-01 — P2: tail arithmetic does not prove that the smoke event reached the shared bus

**Locations:** deployment acceptance at plan 4017–4022; rollback acceptance at 4097–4103. In particular, 4100 is the executable check and 4103 overstates what it proves.

✅ **Verified:** the new acceptance tests only `Get-SettledSeq == $settled + 1`. That identifies a counter movement, not the post. Using the exact rollback v0.1 room code and two independent scratch logs, each with its own sole writer:

1. Both logs start at seq 1, with the same claims/speakers.
2. The operator’s smoke post reaches the wrong log and returns seq 2.
3. An unrelated agent posts to the intended shared log, also producing seq 2.
4. The exact line-4100 check prints `ROLLBACK_CHECK_PASSED` in **both** PowerShell 5.1 and 7, although the smoke text does not exist in the shared log.

✅ **Verified:** the converse also fails. The operator posts successfully to the intended log at seq 2, another agent then appends seq 3, and the same check throws `The v0.1 room did not write the shared log. Stop and investigate.` in both shells. This bus is expressly for concurrent agents; the recipe establishes no exclusive posting window after startup. [Reproducer](reproduce-r4.py), [raw output](adversarial-output.txt), [receipt](adversarial-results.json), cases `wrong-bus-accepted` and `correct-bus-rejected`.

⚠️ **Boundary:** this reproduces the acceptance predicate with real scratch room/log objects and the exact PowerShell check. It does not claim a production launcher misrouted a bus. The v0.2 path readback offers an additional safeguard; v0.1 cannot report those paths, making correlation especially important in rollback.

**Improvement:** use a unique, recorded smoke marker, retain the broadcast reply’s `seq`, and inspect the intended shared JSONL for that exact event: type, sequence, agent, and marker. Permit later rows. The startup-state comparison must likewise permit subsequent legitimate appends, or explicitly establish and verify a quiescent posting window. Preserve the check that replay includes the settled predecessor state; do not equate a later tail with loss. The minimal fix is event correlation, not a new authority/locking subsystem.

**Closure test:** the wrong-bus/unrelated-shared-post case must fail; the correct-bus/interleaved-peer case must pass. Check both upgrade and rollback acceptance, in both shells.

## R4-02 — P2: JSON numeric coercion silently chooses another thread and leaks an internal error

**Locations:** plan 3434–3439, with the execution error boundary at 3538–3542. **Phase 2 only; pre-existing in the plan’s earlier revisions.**

✅ **Verified over a real scratch A2A HTTP connection:** the bridge accepts `{"op":"post","text":"reply","reply_to":1.9}` and forwards `reply_to: 1` to the room. `reply_to: true` also becomes 1. The caller receives a successful post response from the recorder. A valid JSON numeric literal `1e999` becomes infinity during decoding; `int(...)` raises `OverflowError`, which is not caught by either the parser’s `(TypeError, ValueError)` branch or the executor’s `(CommandError, RoomUnavailable)` branch. The A2A caller receives `InternalError`, JSON-RPC code `-32603`, with `cannot convert float infinity to integer`.

✅ **Verified control:** `reply_to: "abc"` produces the intended `error: reply_to, since_seq and limit must be integers` response and makes no room call. The fractional and boolean cases instead reach `room_broadcast`. [HTTP reproducer](audit-bridge.py), [result receipt](bridge-results.json), [traceback/output](bridge-output.txt). Only a fake room was behind this scratch bridge; no operational post was sent.

**Improvement:** validate numeric field types and values before converting them. Preserve the intentional decimal-string compatibility demonstrated by the existing `"4"` test and the specified read-limit clamping. Reject booleans, nonintegral numbers, and nonfinite/overflowing values with `CommandError`; do not silently truncate an event identifier. Apply the same helper to `reply_to`, `since_seq`, and `limit`.

**Closure test:** parser plus HTTP tests prove all these malformed numeric forms yield the normal error artifact with zero room calls. Keep ordinary integers, supported numeric strings, and limit clamping working. This should be corrected before Phase 2; it does not block the independent Phase 1 board implementation.

## R4-03 — P3: the “exact action” preview guard accepts a module-name prefix

**Location:** plan 3909–3915.

✅ **Verified:** `Assert-OnlyAction 'WOULD_START packages.coordination_room.server_other (wrong)' 'WOULD_START' 'packages.coordination_room.server'` succeeds in both shells. The escaped regex is still an unanchored substring match. The same construction can accept a suffixed PID name. [Receipt](deployment-results.json), case `preview-prefix`.

⚠️ **Boundary:** no selector escape was found in the actual reconstructed scripts. This is a weakness in the independent preview check if an unexpected/stale launcher emits a different module; it is lower priority than R4-01.

**Improvement:** parse the action’s module/PID token and compare it exactly while retaining the single-action count check. A similarly prefixed name must fail, the exact expected name must pass. No broad lifecycle rewrite is needed.

## Verification and evidence limits

✅ **Verified:** each stage ran the required set with the same interpreter and installed dependencies:

```text
C:\Python313\python.exe -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded --junitxml=<stage receipt>
```

| Stage | Passed | Failed | Skipped | Deselected |
|---|---:|---:|---:|---:|
| Pinned base archive | 992 | 1 | 7 | 1 |
| Reconstructed Phase 1 | 1,085 | 1 | 7 | 1 |
| Reconstructed Phase 2 | 1,125 | 1 | 9 | 1 |

✅ **Verified:** no baseline case disappeared or changed outcome. The one failure is `scripts/tests/test_text_sources_are_text.py::test_no_tracked_text_file_contains_a_nul_byte`: `git ls-files` returns no inventory in the archive fixtures. It is not a new proposal failure. A separate read-only scan of the exact reconstructed text-file inventories found zero NUL offenders across 1,250 baseline / 1,260 Phase 1 / 1,273 Phase 2 files; this is additional content evidence, not a relabelled passing pytest result. [Comparison](verification-summary.json), [base output](baseline-green.txt), [Phase 1 output](phase1-green.txt), [Phase 2 output](proposal-green.txt).

✅ **Verified:** the 96 room tests pass in both revised phases. Phase 2 has 36 A2A passes and two A2A skips; selector tests have 18 Phase 1 / 22 Phase 2 passes including both shells. Seven shared skips are four optional OpenTimestamps cases and three absent enclosing-workspace materializer cases. Phase 2 adds the optional live Hermes and absent ancestor `.mcp.json` checks. The known supersession test remains deselected. Full per-case names are in [verification-summary.json](verification-summary.json).

✅ **Verified:** `ruff check --isolated` passes for the plan’s Python scope with Ruff 0.15.11. Base, Phase 1, and Phase 2 spec gates all exit 1 with the same two missing hook entries and stale `research_log.py` entry; no new findings were added. This gate is not green. [Static receipts](static-checks.json).

✅ **Verified:** all 14 original helper controls pass in each shell. Additional missing-shell and missing-interpreter checks correctly refuse to proceed. Those hypotheses are explicitly **not findings**. Additional parser and smoke tests yielded the bounded defects above. [Deployment reproducer](audit-deployment.py), [extracted exact helpers](deploy_helpers.ps1).

⚠️ **Not established:** clean dependency installation, Linux CI, a production lifecycle rehearsal, an actual project `ROLLBACK_COMMIT`, live Hermes integration, load/soak behavior, crash durability, or concurrent hostile directory-retarget protection. The plan already disclaims the last durability/concurrency properties. A baseline-comparison success must not be called a completely passing green set or deployment approval.

## Recommended next revision

1. **Before deployment:** correlate smoke events with the shared log and tolerate legitimate interleaving (R4-01); make preview names exact (R4-03).
2. **Before Phase 2:** reject invalid numeric commands without posting or emitting an internal error (R4-02).
3. **Small documentation cleanup:** final verification at line 3869 still says “nine” acceptance behaviours although the list now has eleven; describe the intentional bridge addition to full-stop defaults precisely. These are editorial notes, not separate blockers.
4. **Retain:** the operator waiver and advisory-claim decision, the separate runtime approval boundary, version-aware rollback, no materializer side effects, and the split between independently useful Phase 1 and optional Phase 2.

⚠️ **Orientation/self-audit:** task-specific depth reached T3 for the plan, review receipts, and relevant lifecycle/room source. The router, probe, generated L0, index, operator primer, root/project operating notes, and explicitly invoked orientation/shared-surface skills informed scope. Generated L0 is dated context, not current runtime proof; `FLOSS/AGENTS.md` was absent, so the supplied root instructions and actual project `CLAUDE.md` were used. No `_reference` corpus or event-queue content was opened. No ADR change or governance decision was made. The purpose is reliable shared coordination and inspectable evidence for the commons; these tests do not promote the room to a truth authority.

## Reproduction

⚠️ **Procedure:** `rebuild.py` creates fresh archive fixtures and verifies the snapshot hash. `run-checks.py` consumes `extraction-r4.json` and records runtime overrides. `audit-deployment.py` extracts the exact helper block and runs inert controls; it must precede `reproduce-r4.py`, which uses those extracted helpers. Run `audit-bridge.py` when the regular suite has finished so their scratch port 19998 does not overlap. `summarize-evidence.py` compares individual JUnit outcomes and rehashes source files. These helpers write only this review packet and newly allocated scratch fixtures. The scripts name the local repository/packet paths explicitly. No plan implementation command needs to be executed to reproduce the audit.

✅ **Verified:** final packet byte hashes are recorded separately in [receipt-hashes.json](receipt-hashes.json), excluding that manifest itself.
