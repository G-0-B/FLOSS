# Coordination room board v1 — revision 3 audit

**Date:** 2026-10-02. **Status:** noncanonical review evidence. **Disposition: revise before execution.**

✅ **Verified:** the required comparison has three new failing tests, even with the author's MCP version. The original staging hard-link exploit and the production startup-order defect are fixed. The broader alias guarantee and deployment/rollback failure handling remain incomplete. Receipts: [verification-summary.json](verification-summary.json), [adversarial-results.json](adversarial-results.json), [deployment-results.json](deployment-results.json).

## Reviewed identity and method

- ✅ **Verified:** the first operation checked the supplied SHA-256. The reviewed plan and the byte-for-byte [plan-revision-3.md](plan-revision-3.md) snapshot both hash to `7d25eee2bc44286a141419aa7058978bd9fb6ac7fd27bb33dfb712b2bd02af73`; the source still matched at the final check. The supplied 3,886-line revision is the review target. All plan locations below refer to that snapshot. [Input hashes](input-hashes.json).
- ✅ **Verified:** FLOSS base `4aab13e30f3c2960da787b47c90926256b4b5b73`; A2A base `225287c2ed310158a3f699688447db2964e425b2`. Acquisition used `git -c safe.directory=C:/~shit/FLOSS -C C:/~shit/FLOSS archive --format=zip <base>` and repository-scoped `git show`. The ownership exception was command-local; no Git configuration was changed. [Rebuilder](rebuild.py), [extraction manifest](extraction-r3.json).
- ✅ **Verified:** isolated stages are retained under `C:/Users/kalis/AppData/Local/Temp/codex-room-board-r3-20261002-225116/fixtures-exact/`: `baseline`, `rollback` (end of Task 2), `phase1`, and `proposal` (Phase 2). Reconstruction applied all fenced file bodies and replacement pairs in task order, the MCP requirement edit, and the A2A package, two documents, and requirements addition from the pinned Git objects. There are 55 recorded overlay/import operations. Every inventoried source file still matched its reconstruction hash after testing. These are archive fixtures, not branches or commits. [Manifest](extraction-r3.json), [readback](verification-summary.json).
- ✅ **Verified:** the literal U+2028 inside a test body requires splitting the plan on `\n`, not `str.splitlines()`. Two preliminary reconstruction attempts failed their exact-match assertion and were preserved separately; neither supplied test results. The successful reconstruction preserves the source character. [Rebuilder](rebuild.py).
- ✅ **Verified:** Python 3.13.1; Windows PowerShell 5.1.22621.6133 and PowerShell 7.6.6. The sandbox could not read the operator's user site-packages, so a workspace-only virtual environment was installed. One complete three-stage comparison used the resolved requirements, including MCP 2.3.0; a second used MCP 1.27.0 with the other installed dependencies retained. Environments were unchanged within each comparison. [Dependency snapshots](dependencies-mcp127.txt), [MCP 2 snapshot](dependencies-mcp2.txt), [commands/environment](green-runs.json).
- ✅ **Verified:** the runner cleared `PYTHONPATH`, set `PYTHONDONTWRITEBYTECODE=1`, and bound agent, audit, room root/log/board, and temporary paths to the workspace. The supplied script tests use their own minimal stand-in environment. Additional lifecycle tests replaced launch, kill, identity, reclaim, reservation, and process-enumeration operations with recorders. HTTP tests used scratch ports. No real daemon was started, stopped, or signalled; no forbidden port was bound. [Runner](run-python.ps1), [suite driver](run-checks.py), [script harness](script-harness.ps1).
- ⚠️ **Specified / scope:** this is evaluation, not implementation, deployment approval, or governance. No review action edited the plan, primary working-tree source, a branch, live room, user PID/configuration files, or canonical status. Orientation and verification skills were used; prior reviews and memory were treated as evidence candidates. No subagents or governance dispatches were used.

## Round-two dispositions

| ID | Round-three disposition | Evidence and remaining boundary |
|---|---|---|
| R2-01 | **Closed for the original exploit; partially closed for the absolute alias guarantee** | ✅ Old `BOARD.md.tmp` hard link retains JSONL; a board hard-linked to the log is refused at construction; a late leaf hard link is replaced without damaging the log. Real Windows tests pass, including an open log. Parent-directory rebinding still replaces the log: **R3-02**. [Adversarial receipt](adversarial-results.json), cases `old-stage-hardlink`, `late-board-hardlink`, `open-log-with-linked-board`, `parent-rebind`. |
| R2-02 | **Closed for room-only selection** | ✅ Task 2 gates selected daemon actions, including OmniRoute reclaim/reserve branches. Across both shells, selected-room real-mode traces reach only the room; no dry run reaches a mutation. Phase 2 changes the default selection: **R3-05**. The existing gate tests also need updating: **R3-01**. [Script summary](script-summary.json), [complete traces](script-audit.json). |
| R2-03 | **Closed for the removed custom stop path** | ✅ The selected stop uses the configured scratch `FLOSS_AGENT_DIR` and existing identity helper. `OURS` reaches the selected kill recorder; `FOREIGN` reaches selected reclaim without kill; `UNKNOWN` and reservation contents retain the record without kill. Unselected records are untouched. This establishes selector behavior, not a new proof of the inherited OS identity mechanism. [Script traces](script-audit.json), [existing-test results](proposal-green.xml). |
| R2-04 | **Partially closed** | ✅ The v0.1 acceptance shape works; exact old room code replays v0.2 claims and continues `[1,2,3]`. The archive command preserves board bytes. The end-of-Task-2 content checkpoint has byte-identical v0.1 room code plus scoped scripts. ⚠️ `ROLLBACK_COMMIT` remains a future recorded OID, not an existing commit verified by this audit. Failures can still advance into an unintended rollback checkout: **R3-03**. [Rollback receipt](adversarial-results.json), [deployment receipt](deployment-results.json), [checkpoint hashes](extraction-r3.json). |
| I1 | **Closed for the supported daemon entry point** | ✅ Import leaves the room unbuilt and creates no room files. Observed ordering is `claim → serve → read`; late old-owner state is replayed and its claim conflicts correctly. Sixty-four concurrent `_tools()` requests across 32 workers build one instance. Direct library/ASGI use still requires the documented external ownership discipline. [Adversarial receipt](adversarial-results.json), [95 room cases](proposal-green.xml). |

✅ **Verified:** retaining the shared lifecycle implementation rather than introducing a bare room command was justified: the selected traces retain its existing path/identity handling. Both installed shells resolve `env` to `C:\Program Files\Git\usr\bin\env.exe`; Antigravity's machine-specific command-not-found claim is false here. [Script traces](script-audit.json), [environment resolution](deployment-results.json).

⚠️ **Specified:** removing the unsafe materializer action remains an adequate scope boundary; it does not repair that other subsystem. Claim precedence remains an operator decision. The shell annotations distinguish Bash fences from PowerShell fences, and the plan correctly disclaims DeAR topology. Those retained dispositions need no additional implementation in this task.

## R3-01 — P1: the required verification contract regresses

**Location:** plan 714–728 and 799–813 (new success summaries), Task 2's file list, and 3748–3760 (final gates). Existing checks: `packages/tests/test_mcp_daemon.py:867–919`.

✅ **Verified:** with MCP 1.27.0, three previously passing tests fail in both Phase 1 and Phase 2:

1. `test_a_clean_shutdown_still_reports_success` still expects `All daemons stopped`; the script prints `Stopped: ...`.
2. `test_no_script_claims_success_it_did_not_achieve[start_mcp_daemons.ps1-...]` cannot find the former emitting success statement.
3. The corresponding `stop_mcp_daemons.ps1` case fails for the same reason.

✅ **Verified:** these are exact base-to-proposal regressions, separate from the three environmental baseline failures. All 16/18 newly supplied scope tests pass, so their success does not establish the required repository gate. [Failure comparison](verification-summary.json), [Phase 1 output](phase1-green.txt), [Phase 2 output](proposal-green.txt).

✅ **Verified:** the unqualified scoped Ruff check is also not clean in the installed Ruff 0.16.10 environment: 27 diagnostics in the proposed scope; the baseline room scope already has eight. This is not 27 new runtime defects and does not invalidate an earlier measurement with different tooling. It does mean the current unpinned “clean” gate is not reproducible as written. [Proposed output](proposal-ruff.txt), [diagnostics](proposal-ruff.json), [baseline diagnostics](baseline-ruff.json).

**Reproduction:** run [run-checks.py](run-checks.py) in the retained workspace through [run-python.ps1](run-python.ps1); exact commands are in [green-runs.json](green-runs.json).

**Improvement:** include the existing daemon tests in Task 2's edit scope. Update them to check truthful selected-daemon summaries and preserve the incomplete-operation/nonzero-exit invariant; do not restore an inaccurate “all stopped” message merely to satisfy a string assertion. Specify the Ruff version/rule profile and reconcile its observed findings. Re-run the paired gate; do not substitute the smaller passing packages for it.

## R3-02 — P2: a rebound parent directory defeats the log/view separation

**Location:** plan 1982–2011 (`check_board_path`, constructor), 1453–1473 (`write_board`), acceptance item 3 at line 29.

✅ **Verified:** this is distinct from the fixed leaf-hard-link bug. Create the log at `real/events.jsonl` and the board at `alias/events.jsonl`, initially in different directories. Construct the room and post once. Preserve the original `alias` directory under another name, then create a Windows junction from `alias` to `real`. The next post appends its event and then replaces that very log entry with Markdown:

```text
reply: {"ok": true, "seq": 2, "topic": "general"}
first_line: # Coordination board
next_read_error: JSONDecodeError
```

✅ **Verified:** `mkstemp` still owns its fresh staging file; the problem is the replacement destination. The constructor's path/identity check has expired, and the stored unresolved board pathname now names the log. This needs an externally changed directory mapping and a nondefault board override; it was not observed with the standard stable sibling `BOARD.md` configuration. It is not evidence that an ordinary hard link remains unsafe. [Reproduction](reproduce-r3.py), `parent-rebind` in [receipt](adversarial-results.json).

**Improvement:** define and enforce the supported path-stability boundary. Refuse projection when the destination or its parent no longer has the validated identity and would name the log; make this reproduction preserve JSONL and report the view failure. If arbitrary concurrent directory retargeting is outside the supported threat model, say so instead of promising protection through *any* alias. A one-time string resolution alone is insufficient; a last-moment check also must not be described as protection against an adversary racing that check.

## R3-03 — P2: deployment/rollback steps do not consistently stop on failed preconditions

**Location:** plan 3794–3812 and 3832–3867.

✅ **Verified with inert command blocks in both shells:** a native checkout command returning 128 does not stop the three-line rollback fence. If the destination already contains a launcher, both its preview and real-start calls are reached. The enclosing block returns success after those calls. The reconstruction of Task 2 is correct, but the recipe does not prove that this is the checkout being started. [Reproduction](audit-deployment.py), [results](deployment-results.json).

```text
GIT_WORKTREE_ADD_FAILED_128
STALE_ROLLBACK_START_REACHED only=room dry=True
STALE_ROLLBACK_START_REACHED only=room dry=False
```

✅ **Verified:** the same harness observes `ROOM_STOP_REACHED` after a bridge stop reports `SHUTDOWN INCOMPLETE ... identity UNVERIFIABLE` and exits 1. Step 1 of rollback has no explicit bridge-success/port-free gate before proceeding. The scoped stop script refused correctly; the caller failed to enforce its result. [Results](deployment-results.json).

✅ **Verified:** a simulated `Get-NetTCPConnection` access error is suppressed by `-ErrorAction SilentlyContinue`. Step 3 then produces exactly the supposed free-slot observation, `False` and no connection output. Unknown port state is indistinguishable from a successful empty query in this recipe. No production port was queried by this reproduction. [Results](deployment-results.json), `failed-port-query`.

✅ **Verified:** the sequence equality check has a separate timing problem. Capturing seq 1, allowing the old owner to append seq 2 before shutdown, and then loading the replacement yields healthy state at 2, which fails the prescribed comparison against step 1. [Adversarial receipt](adversarial-results.json), `deployment-capture-window`.

**Improvement:** make each failure gate executable or explicitly require the operator to stop after each individual command. Check the native Git exit code immediately; verify the rollback checkout's full HEAD equals the recorded OID before either launch call. Abort after any unresolved bridge or room stop, and distinguish failed network inspection from a successful empty result. Inspect previews before issuing the real commands. Capture the final log tail after the old owner has exited, and use that settled tail for takeover/rollback continuity checks.

## R3-04 — P2: the dependency range permits an SDK that cannot run this server

**Location:** plan 2737 (`mcp>=1.27` edit), 2698–2702 (`FastMCP` import), and clean-runner requirement at line 109.

✅ **Verified:** a fresh installation of the reconstructed `requirements-ci.txt` selected MCP 2.3.0. Importing `mcp.server.fastmcp.FastMCP` raises `ModuleNotFoundError`; the room catches it and sets `mcp=None`. Three room acceptance tests fail, plus the Phase 2 room/bridge HTTP test. Repeating all stages with MCP 1.27.0 removes those four failures; the three daemon-summary regressions remain. [Install receipt](dependency-install.txt), [resolved versions](dependencies-mcp2.txt), [MCP 2 results](proposal-mcp2-green.txt), [comparison](verification-summary.json).

⚠️ **Specified / attribution:** the base also has an unbounded MCP requirement and the old FastMCP import, so the underlying compatibility exposure is inherited. Revision 3's new minimum and clean-runner claim do not close it; passing base tests do not establish that the base server boots with MCP 2.

**Improvement:** constrain this v1-API implementation to a tested compatible range, such as `mcp>=1.27,<2`, and record the validation environment. An SDK migration is separate work, not necessary to deliver this board.

## R3-05 — P3: “default behavior unchanged” is true only through Phase 1

**Location:** global constraint at line 99 versus Task 9 at 3565, 3642–3666 and 3691–3709.

✅ **Verified:** no-argument start traces match the base through Task 2 and Phase 1. After Task 9, the same scheduled-task invocation additionally launches `packages.a2a_mesh.room_bridge`; the stop default gains `a2a_room_bridge.pid`. This is explicitly implemented and tested by Task 9, so it is not a selector escape. It contradicts the unqualified global promise and changes how the “optional” bridge is enabled. [Complete default traces](script-audit.json), [scope test results](proposal-green.xml).

**Improvement:** state the phase boundary precisely. If optional means explicitly started only, leave `bridge` out of the default selection. If it should start at every scheduled invocation after Phase 2 deployment, name that runtime consequence in the operator decision/deployment contract.

## Other adversarial checks and operational boundaries

| Surface | Result |
|---|---|
| Selector and dry-run mutation paths | ✅ 296 instrumented runs, including 140 dry runs, across both shells: no unselected launch/kill/file mutation/reclaim/reserve and no dry-run mutation. Read-only OmniRoute identity probes still occur as disclosed. [Summary](script-summary.json). |
| Encoding / PowerShell parsing | ✅ All 16 actual file parses succeed. Files have no UTF-8 BOM; this host's 5.1 default encoding is UTF-8. Separately decoding both scripts as Windows-1252 before parsing also produces zero syntax errors at all three checked stages. This is bounded parsing evidence, not a claim to have booted another locale. [Encoding receipt](encoding-results.json), [shell traces](script-audit.json). |
| Lazy first-call failure | ✅ A malformed log makes initialization fail without caching a partial room; a later call retries and succeeds after scratch-log repair. A real scratch singleton claim remains held after the failed call. Thus a live process/PID or successful launch is not readiness; Deployment's successful `room_state` requirement matters. No additional lock race was found. [Receipt](adversarial-results.json). |
| Pre-ownership access | ✅ Import creates no room files; rejected-start and owner-order tests pass. ⚠️ `check_board_path` does perform filesystem metadata/path resolution before ownership, but it does not replay event contents. Directly serving the exported ASGI app bypasses `run_http_daemon`; the production command uses the guarded path. [Room tests](proposal-green.xml), [ordering receipt](adversarial-results.json). |
| Open / read-only Windows board | ✅ Replacement fails with `WinError 5`, the append still succeeds, the previous board remains, and no staging file remains in these cases. An open log with a separately named hard-linked board also retains valid JSONL. [Receipt](adversarial-results.json). |
| Board permissions | ✅ Replacing a board with a protected owner-only DACL produces a new board inheriting the parent directory's ACL. Per-file ACLs are not preserved by this implementation; set the intended policy on the directory or explicitly implement preservation if required. No permission policy for the live board was inspected or assumed. [ACL receipt](permissions-results.json). |
| Version-aware rollback | ✅ Exact old room code reads the new rows, restores `x.py → alice`, reports the old three-field state, and appends seq 3. The exact rename command preserves scratch board bytes under a dated name. ⚠️ No real `ROLLBACK_COMMIT`, checkout acquisition, or live rollback was executed. [Receipts](adversarial-results.json), [archive command](deployment-results.json). |
| Spec gate | ✅ Base, Phase 1, and Phase 2 all exit 1 with the same two missing hooks, stale research-log registration, and failure summary. No new findings; this remains FAIL. [Base](baseline-spec-gate.txt), [Phase 1](phase1-spec-gate.txt), [Phase 2](proposal-spec-gate.txt). |

## Required green-set evidence

✅ **Verified:** each stage ran this command in its own archive fixture, using the same workspace virtual environment within each comparison. Only the XML receipt option was appended:

```powershell
python -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded --junitxml=<receipt>
```

✅ **Verified — MCP 1.27.0 comparison:** [exact invocations](green-runs.json), paired `.txt`/`.xml` receipts, and [JUnit comparison](verification-summary.json).

| Stage | Passed | Failed | Skipped | Deselected | Elapsed |
|---|---:|---:|---:|---:|---:|
| Clean archive of pinned base | 990 | 3 | 7 | 1 | 71.69 s |
| Reconstructed Phase 1 | 1077 | 6 | 7 | 1 | 97.17 s |
| Reconstructed revision 3, Phase 2 | 1115 | 6 | 9 | 1 | 111.70 s |
| Phase 2 minus base | **+125** | **+3** | **+2** | **0** | — |

✅ **Verified:** Phase 2 contains **95 room passes**, **36 A2A passes / 2 skips**, and **18 daemon-scope passes**. Phase 1 has 95 room passes and 16 daemon-scope passes. The 21 baseline room tests remain passing. The pass increase does not cancel the three regressions. [JUnit comparison](verification-summary.json).

✅ **Verified — clean requirements resolution with MCP 2.3.0:** [invocations](green-runs-mcp2.json), `*-mcp2-green.txt` and `.xml` receipts.

| Stage | Passed | Failed | Skipped | Deselected |
|---|---:|---:|---:|---:|
| Base | 990 | 3 | 7 | 1 |
| Phase 1 | 1074 | 9 | 7 | 1 |
| Phase 2 | 1111 | 10 | 9 | 1 |
| Phase 2 minus base | **+121** | **+7** | **+2** | **0** |

✅ **Verified:** the three shared baseline failures are not revision-3 regressions. Two concern recognizing a nonexistent Hermes PID: this sandbox's `tasklist /FI "PID eq 99999999"` returns access denied, and the code conservatively treats unknown liveness as live. The third requires `git ls-files`; the mandated archive extraction has no Git index. They were retained in every run, not deselected or relabelled PASS. [Environment receipt](baseline-environment.txt), [baseline output](baseline-green.txt).

✅ **Verified:** seven baseline skips comprise four missing optional OpenTimestamps cases and three missing enclosing-workspace materializer cases. Phase 2 adds the optional Hermes probe and absent ancestor `.mcp.json` skips. The one requested deselection is unchanged. Full names are in [verification-summary.json](verification-summary.json).

❌ **Blocked / not established:** a fully green required set in this sandbox; production deployment readiness; actual rollback commit identity; live daemon/port behavior; load, crash/power-loss and hostile concurrent filesystem-race guarantees. No historical pass counts were substituted for these runs.

## Practical revision sequence

1. **NOW:** amend Task 2 to update the existing summary tests while preserving their behavioral protection; settle reproducible lint tooling/rules. Close R3-01 with the required paired comparison.
2. **NOW:** close the parent-rebinding reproduction or narrow and enforce the filesystem guarantee explicitly (R3-02).
3. **NOW:** make deployment/rollback preconditions fail closed, verify the acquired rollback OID, and base sequence acceptance on the stopped owner's final log (R3-03).
4. **NOW:** constrain the MCP dependency to the supported API range and repeat installation/acceptance with that constraint (R3-04).
5. **BEFORE PHASE 2:** reconcile scheduled default behavior with the optional-bridge decision (R3-05). Retain the existing waiver, advisory-claim, and separate runtime approval boundaries.
6. **NEVER:** turn a passing focused suite into whole-repository readiness, a live PID into initialized-room health, a failed query into a free port, or a content checkpoint into a verified deployed commit.

## Reproduction and artifact use

✅ **Verified:** [rebuild.py](rebuild.py) and [extraction-r3.json](extraction-r3.json) bind the fixtures to the exact plan and Git objects; [verification-summary.json](verification-summary.json) reports no source-byte drift after tests. All reproduction helpers and raw outputs are beside this review. [Receipt hashes](receipt-hashes.json) bind the final packet.

⚠️ **Specified rerun procedure:** copy the helper `.py`/`.ps1` files into a fresh workspace, create `review-venv`, and install the recorded dependencies there. Run `run-python.ps1 rebuild.py`, then `run-python.ps1 run-checks.py`, `run-python.ps1 audit-scripts.py`, `run-python.ps1 reproduce-r3.py`, and `run-python.ps1 audit-deployment.py`. The rebuild intentionally refuses to overwrite existing fixture directories. Run helpers from the workspace, not directly in the review packet. Hard-coded repository/packet paths are visible at each script's top; adjust only those if relocating the evidence.

⚠️ **Limits:** script traces stub process effects and identity verdicts; they establish selection/control flow, not real OS termination. The failed-checkout reproduction substitutes a native failure and inert preexisting launcher; it does not invoke `git worktree add`. The parent-alias case changes only scratch directories. The two unsuccessful preliminary extractions and the initial missing-pytest attempt are reviewer environment/acquisition evidence, not plan defects.
