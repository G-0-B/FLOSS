# Coordination room board v1 — revision 2 audit

**Date:** 2026-10-02. **Status:** noncanonical review evidence; no implementation, merge, precedence, or deployment approval is implied.

**Assessment:** revision 2 materially improves the plan and passes the required green-set comparison in this Windows environment. It remains **not deployment-ready**. A reproducible log-corruption case remains in the proposed board writer, and the new deployment recipe loses existing process-safety guarantees.

## Exact inputs and scope

- ✅ Verified: `../round-2/plan-revision-2.md` is an exact snapshot of `C:/~shit/FLOSS/docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md`: **3,093 lines**, SHA-256 `6dabb8e6a6ef9f353af7d5f52f2765cf63746a34f69a493e8e7019be635ca635`. The live plan was untracked and was not edited by this audit.
- ✅ Verified: the preserved `../plan-revision-1.md` hashes to `eaa3d75065d8d3582cdcaff1e017d5b214c083ef794a72ba09c583e0462886ff`, matching the first review.
- ✅ Verified bases: FLOSS `4aab13e30f3c2960da787b47c90926256b4b5b73`; A2A `225287c2ed310158a3f699688447db2964e425b2`.
- Tests used a detached review checkout at `C:/Users/kalis/AppData/Local/Temp/codex-room-board-r2-20261002-175609/FLOSS`. Baseline was clean before testing. The proposed source/test blocks, spec/schema/registry changes, requirements, agent how-to and launcher edits were reconstructed there without committing or merging. The two A2A documents and package files came from their exact Git objects. This is a test fixture, not a landed implementation.
- Requested orientation/shared-surface skills and the review/debugging verification disciplines were used. Prior context remained advisory. Current code and the pinned plan supplied the findings. No subagents, governance dispatch, production daemon operations, or live room posts were used.

## Round-one dispositions

| ID | Round-two disposition | Evidence / remaining boundary |
|---|---|---|
| B1 | **Closed for this plan by removing the unsafe action** | Plan 80 and 2196 remove worktree regeneration. The underlying materializer defect remains explicitly separate work. This is an adequate scope reduction; building a new materializer is not required here. |
| B2 | **Original failure closed** | The proposed server tests pass: construction/import and a rejected duplicate startup no longer overwrite log/board. Broader startup-state safety is narrower than the prose; see inherited observation I1. |
| B3 | **Coherent specification, operator decision still pending** | Plan 205, 120–123 and 3081 distinguish room convention from enforced ownership and require a decision before execution. Coordination-v1 design line 156 explicitly calls Git-ref precedence a proposal in its operator questions. This is a supported interpretation, not an already-ratified precedence rule. |
| B4 | **Unsafe task command removed; deployment closure incomplete** | Scratch HTTP acceptance passes and `room_state` exposes the bus paths. The replacement live recipe has R2-02 through R2-04 below. |
| B5 | **Partially closed** | Direct path aliases and inherited environment cases are tested successfully; hard-linked staging aliases still corrupt the log (R2-01). |
| B6 | **Original timing/identity overclaim addressed** | Lookup timing is distinguished from append timing, file digests and full commit OIDs are recorded. A full OID identifies the commit object; repository location is useful for retrieval/context but is not necessary to name that object. The stated large-file digest omission remains a limitation, not a hidden guarantee. |
| B7 | **Closed** | The board now displays an as-of timestamp and sequence and defines the roster window relative to that timestamp. The idle-day test passes. |

These are dispositions of the exact revision, not retrospective implementation status. The supplied package checks appear in `proposed-green.xml`: 91 room tests passed and 36 A2A tests passed with two expected A2A skips.

## R2-01 — P1: the staging-path guard misses a hard link to the event log

**Location:** plan 1451–1462 (`_same_file`, `_check_board_path`) and 953–965 (`write_board`). **Relation:** B5 remains partly open.

✅ Verified by `reproduce-r2.py`, output in `reproduce-r2-output.txt`. The setup creates a real hard link from `BOARD.md.tmp` to the log in a fresh scratch directory. These are distinct resolved path strings but the same underlying file. Construction succeeds; `tmp.write_text` truncates the shared file before replacement.

```text
R2-01 hardlink samefile= True
R2-01 broadcast= {'ok': True, 'seq': 2, 'topic': 'general'} log_first_line= '# Coordination board'
R2-01 next_read= JSONDecodeError
```

The post reports success even though the record is corrupted. This is not an observation of damage to the live room; all affected files were created by the test.

**Improvement:** create a fresh, exclusively owned staging file rather than opening a predictable preexisting sibling for truncation. Check existing-file identity as well as normalized path identity where aliases are forbidden. Account for replacement of an alias after construction; a construction-only string check cannot establish ownership of a later staging open. Add the hard-link case to the log-preservation tests. Keep the remedy confined to the projection boundary.

## R2-02 — P1: the “room-only restart” invokes the all-daemon launcher

**Location:** plan 3037–3051; Task 8 launcher edits 2956–2961.

✅ Verified with an inert execution trace of the reconstructed launcher. `Start-Daemon` was replaced with a recorder and the entire OmniRoute section was excluded before evaluation. `audit-deployment.ps1` and `deployment-audit-output.txt` preserve the exact method and output:

```text
WOULD_START packages.metacoordinator_mcp.server
WOULD_START packages.reasoning_ensemble.mcp_server
WOULD_START packages.coordination_room.server
WOULD_START packages.a2a_mesh.room_bridge
```

Existing daemons may be skipped by their PID guards. A daemon intentionally stopped is instead eligible to be started. Thus “starts only what is down” does not make this room-scoped. The original launcher also contains OmniRoute startup; the inert trace deliberately did not execute that branch.

**Improvement:** provide a selectable room-only lifecycle operation that reuses the existing interpreter, path, identity and environment handling. Start/stop the optional bridge separately. Prove unrelated daemon/PID state remains unchanged when those daemons are both running and intentionally absent. Do not interpret room deployment approval as permission to enable the rest of the runtime.

## R2-03 — P1: the custom stop recipe drops PID-directory and process-identity protections

**Location:** plan 3042–3050. Compare base `scripts/stop_mcp_daemons.ps1` and `packages/mcp_daemon.py` identity helpers.

✅ Verified in an inert run with `FLOSS_AGENT_DIR` set to a scratch directory. The plan still reads the default user directory and proceeds from a numerical PID and command-line display to `Stop-Process`:

```text
R2-03 CONFIGURED_AGENT_DIR=C:\Users\kalis\AppData\Local\Temp\room-r2-inert-agent-path
READ_PID_PATH=C:\Users\kalis\.floss_agent\coordination_room.pid
WOULD_STOP_PID=4242
```

No actual PID file was read and no process was stopped: file/process operations were replaced by inert functions. Source inspection confirms the snippet never invokes the existing creation-token identity check. The shared helper distinguishes `OURS`, `FOREIGN`, and `UNKNOWN`; the established stop implementation refuses to kill unverified holders. Identical `python -m packages.coordination_room.server` command lines also do not identify which checkout supplied the process.

**Improvement:** honor `FLOSS_AGENT_DIR`, use the existing identity-check helper immediately before any stop, and stop only a positively identified instance. Handle absent, reserved, malformed and unverifiable slots explicitly; preserve fail-closed behavior. Capture the intended checkout/interpreter and running instance before stopping, then wait for exit. Do not reconstruct a less safe stop path just to narrow the daemon list.

## R2-04 — P2: rollback asks the old API for new fields and calls for deleting the board

**Location:** plan 3076, which says to repeat all four checks from 3058–3061.

✅ Verified against the exact old room implementation reading a log produced by revision 2:

```text
R2-04 rollback state= {"claims": {"x.py": "a"}, "last_seq": 2, "speakers": ["a"]}
R2-04 missing_required_fields= ['board', 'log', 'root']
R2-04 rollback append= {'ok': True, 'seq': 3} all_seqs= [1, 2, 3]
```

Log compatibility works in this bounded check. The rollback acceptance recipe does not: v0.1 cannot report the three new path fields. A healthy rollback cannot satisfy those checks. The same paragraph says to delete `BOARD.md`; preservation/archival must be explicit under the workspace's no-deletion rule.

**Improvement:** give each version a workable acceptance path. For the old daemon, bind the previously captured process/configuration identity to the retained log, verify replay and sequence continuity, and retire the stale board through a preserved, dated snapshot rather than deleting it. Record what happens to a bridge already running during rollback; do not assume an old launcher manages it.

## I1 — inherited startup ordering still permits stale state at takeover

✅ Verified deterministic interleaving, reproduced in `reproduce-r2.py`: construct the new server's room while an old room owns a log at seq 1; let the old room append seq 2 before it exits; then let the newly constructed room append its first event. The resulting sequence is `[1, 2, 2]`.

This was a sequential simulation of the preload/takeover boundary, not a real competing production-daemon experiment. The underlying ordering already exists in v0.1: `_tools` constructs the room and caches/replays state before `run_http_daemon` acquires the slot. Revision 2 fixes the pre-guard board write but retains this ordering. Do not present I1 as a newly introduced regression.

**Improvement:** initialize/reload sequence and claim state only after acquiring ownership, or explicitly restrict and prove the supported startup transition. Add an acquisition-after-an-intervening-append test. Record this separately from the already disclosed append-failure atomicity limitation.

## Required green-set evidence

✅ Verified using Python 3.13 on this Windows host with installed dependencies. The same command ran first on the clean base checkout, then on the reconstructed proposal:

```powershell
C:\Python313\python.exe -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded --junitxml=../<baseline-or-proposed>-green.xml
```

`PYTHONPATH` was cleared; `PYTHONDONTWRITEBYTECODE=1` was set; `FLOSS_AGENT_DIR`, audit, room root, log and board paths were bound to the scratch tree. The test run used the existing dependency environment, not a fresh installation.

| Check | Observed result | Receipt |
|---|---|---|
| Clean pinned base, required green set | **993 passed, 7 skipped, 1 deselected**, 67.32 s | `baseline-green.txt`, `baseline-green.xml` |
| Reconstructed revision 2, same green set | **1099 passed, 9 skipped, 1 deselected**, 90.10 s | `proposed-green.txt`, `proposed-green.xml` |
| Room cases within proposed run | **91 passed** | JUnit class names `packages.coordination_room.*` |
| A2A cases within proposed run | **36 passed, 2 skipped** | JUnit class names `packages.a2a_mesh.*` |
| Other cases unchanged | **972 passed, 7 skipped** in both runs | JUnit comparison |
| Scoped Ruff | **All checks passed!** | Run against room plus new bridge/test files |
| Inherited board override, server/HTTP/A2A fixtures | **7 passed**, sentinel remained `OPERATOR` | `sentinel-tests.txt`; executed with `COORDINATION_ROOM_BOARD` naming a separate scratch sentinel |
| Proposed spec gate | Exit 1, exactly the three named debt findings plus its summary | Existing missing hooks and stale research-log entry; not PASS |
| Deployment PowerShell snippets | **0 parse errors** | `deployment-audit-output.txt`; syntax only |

The two added skips are optional Hermes integration and the machine-local `.mcp.json` ancestry invariant. Seven baseline skips are four missing OpenTimestamps dependency cases and three missing enclosing-workspace materializer cases. The same known supersession test remains deselected. None is promoted to PASS.

**Conclusion from this check:** no new failures in the plan's required green set in this environment. This is not the full ARF advisory suite, a clean Linux CI install, a load/soak/crash test, or production deployment evidence. The existing broad tests do not cover R2-01 through R2-04.

## Practical revision sequence

1. **NOW:** close R2-01 with an adversarial regression and a safely owned staging write.
2. **NOW:** replace the deployment/rollback draft with one scoped, version-aware lifecycle contract that composes existing identity/path logic. Keep live execution separately gated.
3. **NOW:** retain the B3 question as an actual operator decision. The advisory interpretation is reasonable; this review cannot supply the missing human decision. Label it Specified until confirmed.
4. **LATER:** proceed with optional A2A only after Phase 1 acceptance and the intended runtime authorization. A paired baseline/proposal green-set run is now available; do not replace that evidence with an undifferentiated fixed test count.
5. **NEVER:** infer truth from evidence resolution, enforcement from a room reservation, or deployment authority from a file-edit waiver. No new central controller or competing coordination system is needed for these repairs.

## Reproduction and artifact use

From this directory:

```powershell
C:\Python313\python.exe .\rebuild-focused.py
# Use the printed fresh fixture root:
C:\Python313\python.exe .\reproduce-r2.py --source-root <printed-root>
```

The rebuild reads the adjacent revision-2 snapshot and the pinned Git objects in `C:/~shit/FLOSS`; it writes only a new temporary fixture. `reproduce-r2.py` creates fresh temporary cases and does not delete them. `extraction-r2.json` maps source blocks to plan line numbers. The full review checkout is retained at the path above for inspecting the exact tested overlay. It has no commits from this review.

The original managed-worktree tool could not resolve the FLOSS commit from the enclosing chat repository. A repository-scoped manual detached worktree was used after that failure. Its first checkout attempt hit two Windows long-path errors; retrying with process-local `git -c core.longpaths=true` succeeded and the baseline was verified clean. These were acquisition failures, not plan/test defects. Two reviewer helper-command formatting attempts failed before execution and were corrected; their parse errors are not attributed to the plan, whose quoted deployment snippets parsed successfully.

Only new round-two review evidence was added to the primary repository. The reviewed plan, existing round-one receipts, live coordination log, production processes, shared configuration and governance state were not changed by this audit.
