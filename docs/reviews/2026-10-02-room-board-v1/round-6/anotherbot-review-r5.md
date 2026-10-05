# Adversarial review of the room board v1 plan, revision 5

- Plan: `/workspace/plan-review/plan-r5.md`, 4,271 lines. SHA-256 `f2a8392e874a6f90c6818657fccc0050625da518fb09860dff0d58c68b8d1752` (**Verified**: matches).
- Reviewer: Grok Bot (executor). Read-only: nothing was written to any repo, branch, or user machine. All runs happened in box scratch dirs under `/workspace/plan-review/` (`sandbox/`, `sg/`, `v01/`, `probe/`, `venv*/`).
- Labels: **Verified** = I ran it or checked it against code. **Specified** = read in docs or source, not run. **Unverified** = inferred, could not check.
- Out of scope: the six items the first reviewer already found (unpushed base / no PR target, DNS rebinding on :7335, `file:` sha256 leak, plan bloat, advisory-only claims, :7334 rebinding default). An item below touches one of them only where I found something materially different.

## How it was exercised

1. **Code base.** I cloned `G-0-B/FLOSS` and extracted `origin/feat/coordination-room-rebased` @ `2460c55`. That is one commit behind the plan's local-only `4aab13e`. 4aab13e adds 4 line-separator tests, so the baseline here is 17 tests, not 21.
2. **Phase 1.** I pulled every Phase 1 file body out of the plan by fence line: evidence/board/room/gateway/server, the 7 test files, and the schema. Run on Python 3.13.5 Linux with mcp 1.27.0, jsonschema 4.26, pytest 9.1.1, ruff 0.15.11. **75 new tests: 74 pass and 1 skips** (the Windows-only case-folding case). The only failure is the *base* test `test_paths.py::test_backslash_collapses_to_same_key`, which fails on Linux at 2460c55. `ruff check --isolated` is clean.
3. **Phase 2.** I merged `packages/a2a_mesh` from `feat/a2a-harness-mesh`@225287c and installed `a2a-sdk[http-server]==1.1.2`. Combined result: **183 passed, 3 skipped, 1 failed** (the same base test). A fresh `pip install 'mcp>=1.27,<2'` resolves to **mcp 1.30.0** and gives the same result.
4. **Task 1 and the spec gate.** I applied Task 1 (spec, schema, registry) to a clean 2460c55 tree. The JSON validates, and `spec_gate.py --check` shows exactly the plan's three findings, before and after. The new `scripts/tests/test_daemon_scope.py` is not flagged (tests are exempt).
5. **Script edit anchors.** All 11 Task 2 anchors occur exactly once in the base `.ps1` files, but only after CRLF→LF normalisation (see m8).
6. **Deployment helpers.** Extracted from lines 3973-4101 and run in **PowerShell 7.4.6 on Linux**. Not Windows PowerShell 5.1, not Windows.
7. **Probes I wrote.** Event-loop blocking, torn line, claim-append failure, impersonated release, v0.1-reads-v0.2, and a mutation run.

---

## Blockers

None beyond item (1) already reported. Measured on Linux, the Phase 1 code does what its tests say. The problems below are about failure paths, operations, and tests that cannot fail. They are not wrong happy-path behaviour.

## Major

### M1. One post's evidence lookup freezes the whole room for every harness
- **Plan:** lines 2200-2204 (`resolve_all` is called inside the sync tool), 1097-1103 (`git rev-parse`, `timeout=5` per ref), 1081-1082 (reads up to 16 MiB per file), 920 (`MAX_REFS = 16`).
- **Evidence:**
  - mcp 1.27.0 `fastmcp/utilities/func_metadata.py:92-95` calls sync tools inline on the event loop (`return fn(**arguments_parsed_dict)`).
  - The base `packages/mcp_daemon.py` `audited()` keeps sync tools sync.
  - Probe (`probe/block_probe.py`): real FastMCP room over HTTP, a fake `git` that sleeps 3 s, one post with 2 `commit:` refs. The post took 6.0 s. A concurrent `room_state` from a second client took **5.6 s end-to-end** instead of about 0.
  - Worst case by construction: 16 refs × 5 s = 80 s of a dead :7334 for all three harnesses, or about 256 MiB hashed on the loop.
- **Label:** Verified (Linux, mcp 1.27.0).
- **Fix:** make the room tools `async` and run lookup, append and projection through `anyio.to_thread.run_sync`, with one overall deadline (for example 2 s total, then mark the rest `unresolved`). Alternatively, drop evidence resolution from Phase 1 (see Scope).

### M2. A torn or undecodable line takes down the whole bus, and the live room writes onto the fragment
- **Plan:** line 329 ("a torn last line is not recovered"), 2116 (`_replay` → `load()`), 2139-2144 (`_project` catches `ValueError`, which includes `JSONDecodeError`, and prints "projection **refused**"), 2243/2258/2263 (every read path calls `load()`). Base `log.py` `load()` calls `json.loads` on every line, and `append()` writes without first checking for a trailing newline.
- **Evidence** (probe `probe/torn_probe.py`):
  - After a torn tail, the *running* room's next post returned `{'ok': True, 'seq': 3}`. The new row was concatenated onto the fragment, so the tail became `..."seq": 3, ..."after tear"...}\n` on the same physical line.
  - stderr said "BOARD.md projection refused: Expecting ',' delimiter", which reads as an alias problem.
  - A restarted room (the lazy `_tools()` build) raises `JSONDecodeError` on every tool call, permanently.
  - In pwsh, `Get-SettledSeq` and `Assert-SmokeEvent` throw on the same tail (fail-closed, but with no next step).
  - The stop path that Deployment uses force-kills the writer (base `stop_mcp_daemons.ps1`: `Stop-Process -Id $daemonPid -Force`). Appends are not fsynced (line 329).
- **Label:** Verified (behaviour). The probability of a torn write is Unverified.
- **Why it matters:** the "Not guaranteed" text says one row may be lost. What actually happens is that the room cannot start at all until someone hand-edits the shared log, and no runbook step covers that.
- **Fix:**
  - (a) `load()` treats an undecodable **final** line as torn: skip it, report it in `room_state`, and never rewrite the log.
  - (b) `append()` writes a leading `\n` if the file does not end in one.
  - (c) Separate `JSONDecodeError` from the alias refusal in `_project`.
  - (d) Add a Deployment "log won't parse" stop with an operator-approved recovery that copies the log first.
  - Two small tests cover (a) and (b).

### M3. Every failure signal the plan relies on goes to a console nobody can see
- **Plan:** lines 131, 299, 301, 2140-2149 (failures "logged to stderr"), 1539-1541.
- **Evidence:** the base `Start-Daemon` launches `Start-Process -WindowStyle Hidden -PassThru ...` with no stdout/stderr redirection, so the room's stderr goes to a hidden console. "Refuses that projection and says so on stderr" (the R3-02 safeguard, line 301) and "projection failed" are therefore invisible in production. On Windows, `os.replace` onto a `BOARD.md` that a reader holds open without `FILE_SHARE_DELETE` fails, so the board can silently go stale.
- **Label:** Verified for the redirection (read). Windows replace-while-open is Unverified (Win32 semantics, not run).
- **Fix:** add `board_as_of`, `board_last_error` and `log_tail_ok` to `room_state()`, and/or redirect daemon stderr to `$flossAgent\coordination_room.err.log`. Acceptance 5 should require the error to be visible through `room_state`.

### M4. The deployment won't survive a logon, and it serves from the worktree where Phase 2 is still being written
- **Plan:** line 3975 (`$serve = ...\.worktrees\room-board-v1`), 126 (the same worktree is the implementation worktree), 164/2960 (Phase 2 starts after Phase 1 is deployed, same branch and worktree), 38/128 (acceptance 10: the no-argument start is unchanged).
- **Evidence:**
  - The scheduled task runs `C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1` (line 642).
  - The primary checkout is on `feat/coordination-room` (snapshot META: head `2744578`). That branch's start script contains **no** `coordination_room`/`7334` block (`git show origin/feat/coordination-room:scripts/start_mcp_daemons.ps1 | grep 7334` returns nothing). The script does not exist on `main`.
  - So after the next logon the room is not restarted. Acceptance 10 protects a script the scheduled task does not run.
  - Any room restart during Phase 2 (crash or manual) would import half-written Task 7 or Task 8 code from that worktree.
- **Label:** Verified (git), Specified (consequence).
- **Fix:** deploy from a dedicated detached worktree at a recorded `DEPLOY_COMMIT`. `New-RollbackCheckout` already does exactly this and can be reused. Add one line stating what happens at logon and who decides whether the scheduled task should start the room.

### M5. Steering (c): a failed claim leaves a phantom claim, and a retry reports success
- **Plan:** line 330 (disclosed), 1574 ("inherited and deliberately left"), 2163-2173 (`self._table.claim` runs before `self._log.append`), 2316-2322 (the gateway does not catch `OSError`).
- **Evidence** (probe, `EventLog.append` made to raise `OSError(28)` once):
  1. The first claim raised to the MCP layer.
  2. The **retry** returned `{"ok": true, ..., "seq": 0}`, because the idempotent path returns `self._log._seq` without logging.
  3. Other agents got `conflict`.
  4. The log has 0 rows.
  5. After a restart the claim is gone and `claude` gets the path.
- **Label:** Verified.
- **Is the disclosure enough?** No. Task 5 replaces `room.py` whole, so fixing this is about 4 lines (check the conflict, append, then `force_set`, all under the lock), plus `except OSError` returning a JSON error in the gateway. The retry-says-ok behaviour is worse than what line 330 describes.

### M6. Steering (b) and (a): claims never expire, and the only way to clear one is to impersonate its holder
- **Plan:**
  - grep for `lease|expir|ttl` finds only line 260 ("lease shape"). There is **no** expiry, lease, TTL, heartbeat, or force-release.
  - Replay (2115-2121) restores claims forever.
  - The how-to (2888) tells agents "Do not write. Pick another path or wait."
  - Identity is disclosed at line 332 ("`agent_id` is whatever the caller sends").
- **Evidence** (probe):
  - The conflict reply names the holder (2320).
  - `room_release(agent_id="grok", ...)` sent by an intruder succeeds.
  - A release of a path nobody holds still appends a row and rewrites the board (`ClaimTable.release` returns early when there is no holder, and `room.release` still appends).
- **Label:** Verified.
- **Assessment:**
  - (a) The identity disclosure is adequate for a loopback, advisory v1 *only if* the already-reported rebinding fix lands. Add "agent names are self-asserted" to the BOARD.md header.
  - (b) This is the material gap. A crashed harness's claim blocks cooperative agents indefinitely, and the sanctioned remedy is spoofing.
- **Fix** (read-only, no new authority):
  - render claim age, and mark claims older than N hours `stale?` in `room_state` and on the board;
  - document an operator force-release (`room_release` as the holder, with a reason broadcast);
  - do not log no-op releases.

### M7. Tests that cannot fail, and acceptance criteria with no test
Mutation run (`mutate.py` and `mutate2.py`, full Phase 1 suite, base Linux failure deselected):

| Mutation | Result | Plan lines |
|---|---|---|
| `read()` default `limit` 0→50 in room, gateway and server | **SURVIVED** (90 passed) | 55, 273, 1698-1709, 1937-1943 |
| `evidence_checked_at` taken **after** the append | **SURVIVED** | 1676-1695 (assert at 1694 is `<=` at 1-second resolution) |
| `_tools_lock` removed | SURVIVED (moot: FastMCP runs sync tools on one thread) | 2721, 2735 |
| `_project` skips the board re-check | killed | 2138 |
| `write_board` opens the target directly | killed | 1534 |
| no `normalize_path` in evidence | killed | 1078 |
| idempotent re-claim appends | killed | 2166 |
| U+2028 not flattened in the snippet | killed | 1279 |

Other gaps:
- **Acceptance 6** ("v0.1 code can read a v0.2 log", line 34) has no automated test, only a recorded observation (4250). I checked it by hand: v0.1 (2460c55) gateway on a v0.2 log replayed `claims {"a.py":"g"}`, read 5 rows, refused the conflicting claim, and continued at seq 6. **Verified, and it holds.** It should still be a test.
- **Deployment helpers.** "26 inert checks" (21, 3967, 4267) are cited, but their harness is not in the plan, and no task commits it. An implementer cannot reproduce them. The snapshot holds only the revision-4 `round-3/author-r4-green/deploy_harness.ps1`. I re-ran a few by hand in pwsh 7 and they behave as described: interleaved peer passes; wrong marker, prefixed module and torn tail all throw.
- **Acceptance 9 is manual.** Steps 5, 6 and rollback step 4 say "From an MCP client, call ..." without naming the client, and need `<seq from the reply>` typed in by hand (4144, 4159-4162, 4244-4247).
- **Fix:**
  - add a default-limit test with more than 50 rows;
  - assert `evidence_checked_at` against a frozen clock that advances between lookup and append;
  - add a v0.1-compat test that loads `room.py` from `git show $ROLLBACK_COMMIT` (or from 2460c55) and replays a v0.2 log;
  - commit the inert harness as a `scripts/tests` file;
  - add a tiny `scripts/room_call.py` client (reuse `_call` from `test_server_http.py`) so Deployment is scriptable.

### M8. The consent waiver doesn't cover every file the plan edits
- **Plan:** line 175. The waiver question lists `room.py`, `gateway.py`, `server.py`, `board.py`, `evidence.py` and the two scripts, then says "**The waiver is for those file edits on that branch and nothing else.**" But the plan also edits:
  - `packages/coordination_room/README.md` (Task 6, inside the protected package);
  - seven new test files in `packages/coordination_room/tests/`;
  - `requirements-ci.txt`;
  - `docs/agent-memory/project/coordination-room-v0.md`, a canonical agent-memory source projected into the user-wide Claude index (2920). This edit changes every harness's instructions once regenerated;
  - the spec, schema and registry;
  - the Task 7 merge.
- **Label:** Verified (read).
- **Fix:** list every path, including the agent-memory edit, as its own line the operator approves.

## Minor

- **m1. Test writes outside its temp dir** (acceptance 7, line 35). `test_board_failure_does_not_fail_the_post` (1855-1859) passes `board_path=tmp_path`, so `write_board` creates its `mkstemp` file in `tmp_path.parent` before unlinking it. Probe printed `mkstemp dir = <parent of tmp>`. **Verified.** Fix: use `board_path=tmp_path / "adir"` with `adir` made a directory.
- **m2. The documented comma syntax doesn't work under `-File`.** `-Only consensus,ensemble,room,omniroute` (line 452) fails `ValidateSet` under `-File` (schtasks and `Invoke-DaemonScript` both use `-File`). `-Only room ensemble` silently selects only `room`. **Verified** in pwsh 7.4.6/Linux; 5.1 is Specified (same documented `-File` string binding). Deployment passes single names, so it is not broken today. Fix: document single-name use, or accept `[string]$Only` and split on `,`.
- **m3. The plan never ran Linux CI.** The required `green-set` job is `runs-on: ubuntu-latest` (`.github/workflows/python-ci.yml:72`, paths `packages/ tests/ scripts/tests/`). The paired green set (line 21) was Windows-only. On 2460c55 the base test `test_backslash_collapses_to_same_key` fails on Linux, so the required job is likely red before this plan starts; 4aab13e is Unverified. Positive: every new Phase 1 and Phase 2 test passes on Linux (**Verified**). Fix: make acceptance 11 name the CI job and run the paired comparison on Linux too.
- **m4. Fixed test ports collide.** Ports 19995-19998 (138, 2577) will clash when two harnesses run suites at once on the shared machine, giving flaky failures. Fix: bind port 0.
- **m5. Internal contradictions (Verified):**
  - 3957 says "The authoring run for revision 4 is under Truth status"; line 21 is now revision 5.
  - 104 says Deployment "dot-sources one helper block"; 3971 says "Paste once per session". Dot-sourcing a `.ps1` would also run into execution policy.
  - 2416 says `_create_mcp` is "the base file's, unchanged"; 2833 adds `room_topics` to it.
  - 59 says "4 line-separator tests"; 2378 says "the three Unicode line-separator cases" (Unverified, 4aab13e is not public).
- **m6. Raw U+2028 in the plan.** Line 1279 has a literal U+2028 inside a Python string (the only one in the file). My own file reader rendered it as a space. An agent or editor copy can turn it into a newline (SyntaxError) or a space (the test becomes weaker). **Verified.** Fix: write `"\u2028"`.
- **m7. Material addition to known item (1).** On the pushed base 2460c55, one broadcast containing U+2028 makes the next reload raise `JSONDecodeError`, because `log.py` uses `splitlines()` (**Verified**). Building from origin silently drops the 4aab13e fix, and Task 0 Step 2's `4aab13e` check is the only guard.
- **m8. Line endings in the edit anchors.** `.ps1` files are `text eol=crlf` (`.gitattributes`; `git ls-files --eol` shows `w/crlf`), but the plan's anchors are LF. A byte-exact replacer will report 0 matches. **Verified.** Fix: say "match after normalising line endings, keep CRLF".
- **m9. Leftovers and removal wording.**
  - A kill between `mkstemp` and `os.replace` (1534-1541) leaves `.BOARD.md.*.tmp`, and nothing ever cleans it up.
  - The worktrees `room-board-v1` and `room-rollback` have no retention statement.
  - `New-RollbackCheckout`'s message "remove it deliberately" (4088) should point to the standing removal-approval rule.
  - No step deletes a worktree, branch or dir. BOARD.md is archived by rename (4205). PID and identity files are removed by the existing stop script.
  - No step touches hooks, `.claude/settings.json`, `AGENTS.md` or the root `plugin.json` (grep, **Verified**).
- **m10. Schema and spec drift.** The schema's `maxLength` (356-357) counts characters, while the spec says bytes (264, 272). The top level allows unknown properties, so typos validate. Uppercase commit hex is silently `unresolved` (1070).
- **m11. Misleading bridge error.** `McpRoomPort` turns any room-side tool error (non-JSON `isError` text) into "room ... did not answer" (3587-3591). Specified.
- **m12. Board cost grows with the log.** Projection re-reads the whole log on the loop: one post took 10 ms at 1k rows, 72 ms at 10k, 347 ms at 50k (Linux, **Verified**). Acknowledged at 4258; fine for now, but it adds to M1.
- **m13. Dependencies.** `mcp>=1.27,<2` is a range. A clean install picks 1.30.0, not the 1.27.0 that was measured; it passed here. `a2a-sdk[http-server]==1.1.2` exists on PyPI (uploaded 2026-07-22 UTC; latest is 1.2.1). There is no lock file or hashes, so supply-chain integrity rests on PyPI alone. **Verified** (PyPI JSON plus installs).

## Concurrency and atomicity: what checks out
- **One writer.** Repo grep: only the room daemon references `COORDINATION_ROOM_LOG`/`rooms/default`. No hook writes the log. Specified.
- **Board races.** The projection runs under the room lock in a single process, so there are no board-vs-board races. Staging through `mkstemp` plus `os.replace` is killed by mutation M3 (see M7). Verified.
- **Slot and PID reuse.** These rely on the base `mcp_daemon.claim_singleton` (O_EXCL plus creation-token identity) and the stop script's OURS/FOREIGN/UNKNOWN handling. Specified (read), not exercised on Windows.

## Scope versus observed need (smallest valuable version)
The stated need is "a continuously saved message board". The smallest version that delivers it:
- `topic`/`reply_to`/`thread_id` and `room_topics`;
- the `room_state` paths;
- the dated `BOARD.md` with the staging and alias guard;
- `-Only`/`-DryRun` for a safe deploy.

Evidence lookup is the source of M1, the already-reported fingerprint leak, and much of the review churn. Phase 1 could store `evidence_refs` as plain, unchecked strings and add lookup later. Phase 2 (the A2A bridge) has no named consumer in the plan, so defer it until one exists.

## Steering leads (a), (b), (c) against revision 5
- **(a) Identity: present.** Disclosed at line 332, also 315 and 2997. Impersonated release was demonstrated (M6). The disclosure is adequate for v1 *if* the rebinding fix lands; add a self-asserted-names line to the board.
- **(b) No lease or expiry: present.** Nothing exists (grep plus code, Verified). Fix before shipping with the read-only "stale?" marking plus a documented operator force-release (M6).
- **(c) Claim before append: present.** Disclosed at 330 and 1574, code at 2163-2171. The disclosure is **not** adequate, because the retry returns ok with `seq: 0` (M5). Fix before shipping; it is about 4 lines.

## Could not verify
- Anything Windows-specific: PowerShell 5.1, NTFS junctions, `os.replace` while a reader holds the file, TerminateProcess tearing, 8.3/long paths, execution policy, `Invoke-DaemonScript` piping, the `test_daemon_scope.py` runs.
- Commit 4aab13e and its 4 extra tests.
- The revision-5 "26 inert checks" harness and the round-4 review files. The snapshot is revision 4 (hash `7d40c37e…`, matching line 18) and has no `round-4/`.
- Any live deployment, rollback, or Hermes. The green-set figures on the authoring machine.

## Verdict: **0, hold**
Phase 1 code is close: 74 of 75 new tests pass on Linux and 1 skips, ruff is clean, Task 1 applies and the gate holds. It is not ready because:
- the failure paths (M2, M5) and observability (M3) are weaker than the spec claims;
- the room blocks under load (M1);
- the deploy is not durable (M4);
- several acceptance criteria are untested or manual (M7).

### Smallest changes that would make Phase 1 ready (besides pushing the base and naming the PR target)
1. **Harden `room.py` and `log.py` (about 20 lines plus 4 tests):**
   - append first, then set the claim, and return a JSON error on `OSError`;
   - tolerate and report an undecodable final line, and newline-guard `append`;
   - put `board_last_error`/`log_tail_ok` in `room_state`;
   - add the default-limit and v0.1-compat tests.
2. **Take evidence lookup off the event loop with one overall deadline,** or drop lookup from Phase 1 and store refs unchecked.
3. **Deploy from a pinned `DEPLOY_COMMIT` detached worktree,** state the logon behaviour, and widen the Task 0 waiver to every path the plan edits (including the agent-memory how-to).
