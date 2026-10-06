LINUX: PASS — No regression relative to base; the required test set is still red on both revisions with the same pre-existing failure.

Date: 2026-10-06. Noncanonical verification receipts. PASS uses the comparison rule in [HANDOFF.md](HANDOFF.md); it does not mean the required CI test command passed.

## Verified comparison

✅ Verified from [base.xml](base.xml), [head.xml](head.xml), [compare.json](compare.json), and [runs.json](runs.json):

| Revision | Passed | Failed | Errors | Skipped | Deselected | Pytest exit |
|---|---:|---:|---:|---:|---:|---:|
| Base | 990 | 1 | 0 | 9 | 1 | 1 |
| Head | 1,083 | 1 | 0 | 24 | 1 | 1 |

All 1,000 existing cases retain their outcome and diagnostic message. No base-pass regression, missing case, changed existing outcome, or new failure/error was found. Head adds 108 collected cases: 93 pass and 15 skip for the platform reasons listed below. The v0.1 compatibility case ran and passed. [verification.json](verification.json) records an independent readback of the JUnit comparison.

❌ Blocked: the required test set is not green. Both runs fail `packages/coordination_room/tests/test_paths.py::test_backslash_collapses_to_same_key` with the same assertion:

```text
assert normalize_path(tmp_path, "packages\\foo.py") == "packages/foo.py"
AssertionError: assert 'packages\\foo.py' == 'packages/foo.py'
```

The actual commands, exits, and unabridged failure output are in [commands.txt](commands.txt), [command-results.json](command-results.json), [base.txt](base.txt), and [head.txt](head.txt). This reproduces the reported baseline failure under the environment below. It is not a regression introduced by head, and no fix was made.

## Environment and exact revisions

✅ Verified by [environment.json](environment.json), [pip-freeze.txt](pip-freeze.txt), and the [command journal](commands.txt):

- Base: `4aab13e30f3c2960da787b47c90926256b4b5b73`.
- Head pinned at start: `806a99936d1dd752641d4b7d1f01e8085e156c5e`.
- Last non-document checkpoint: `0281a47cd817efb2f2426886e3a1058c157b33eb`. The diff from checkpoint to tested head excluding `docs/` exited 0 on Windows and Linux; [checkpoint-diff.txt](checkpoint-diff.txt) is intentionally empty.
- Ubuntu 24.04.2 LTS, x86_64, WSL kernel `6.18.33.2-microsoft-standard-WSL2`.
- Tested interpreter: Python 3.13.13, created using `uv 0.11.6 venv --python 3.13 --seed`. System Python 3.12.3 ran only the orchestration helper.
- One fresh environment for both test runs, with dependencies installed once from head's `requirements-ci.txt`; resolved `mcp==1.30.0`, `pytest==9.1.1`, `pytest-asyncio==1.4.0`. Full install output: [dependency-install.txt](dependency-install.txt).
- Linux root: `/home/kalis/room-board-linux-20261006-MSAjEM`; clones `base/` and `head/`, environment `venv/`, original receipts `receipts/`, and runtime scratch under `runtime/` remain available.
- The verified Git bundle retains base history, enabling the compatibility test. Setup and exact commands are in [commands.txt](commands.txt); the executed helper is [run-linux.py](run-linux.py).

Each checkout was tested once, from its Linux root, with this command (using the same private interpreter):

```bash
python -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ \
  --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded \
  --junitxml=<stage.xml>
```

The selected paths and deselection match the required job in [python-ci.yml](../../../../.github/workflows/python-ci.yml). JUnit excludes the one explicitly deselected test. Runtime overrides and exact absolute commands are retained in [runs.json](runs.json) and [commands.txt](commands.txt).

## Every newly skipped case

✅ Verified in [head.xml](head.xml) and [compare.json](compare.json). These 15 skips are not passes:

| Case | Reason |
|---|---|
| `packages.coordination_room.tests.test_deploy_helpers::test_every_helper_check_holds[]` | Windows deployment helpers |
| `packages.coordination_room.tests.test_message_board::test_board_path_that_is_the_log_is_refused_before_any_write[EVENTS.JSONL]` | a case-distinct name is a different file off Windows |
| `scripts.tests.test_daemon_scope::test_a_real_run_writes_nothing_where_pytest_was_started[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_a_second_bare_name_is_an_error_not_a_silent_drop[start_mcp_daemons.ps1-]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_a_second_bare_name_is_an_error_not_a_silent_drop[stop_mcp_daemons.ps1-]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_real_start_only_room_attempts_only_the_room[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_real_stop_only_room_leaves_other_records_alone[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_real_stop_with_no_arguments_keeps_its_original_success_line[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_several_names_go_in_one_comma_separated_argument[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_start_default_still_considers_every_daemon[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_start_only_room_considers_nothing_but_the_room[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_stop_default_still_considers_every_daemon[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_stop_only_room_considers_nothing_but_the_room[]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_unknown_daemon_name_is_refused_before_anything_runs[start_mcp_daemons.ps1-]` | Windows daemon scripts |
| `scripts.tests.test_daemon_scope::test_unknown_daemon_name_is_refused_before_anything_runs[stop_mcp_daemons.ps1-]` | Windows daemon scripts |

Linux collected 108 additional cases, versus the handoff's historical Windows count of 122. Collection is environment-dependent: the daemon/deployment tests parametrize over installed PowerShell interpreters and use one empty-shell placeholder when none is found. The Linux receipt contains 14 such placeholder cases (13 daemon cases and one deployment-helper case), plus the case-insensitive path-alias skip. See [daemon test parametrization](../../../../scripts/tests/test_daemon_scope.py) and [deployment test parametrization](../../../../packages/coordination_room/tests/test_deploy_helpers.py). Windows was not rerun here.

## Spec gate and checkout state

✅ Verified: base and head both exit 1, with byte-identical output matching the three findings described in the handoff: [base-spec-gate.txt](base-spec-gate.txt), [head-spec-gate.txt](head-spec-gate.txt), [spec-gate-comparison.json](spec-gate-comparison.json).

```text
SPEC-GATE MISSING FLOSS/hooks/grok_pretool_st.py
SPEC-GATE MISSING FLOSS/hooks/grok_session_register.py
SPEC-GATE STALE   FLOSS/scripts/research_log.py (registered but absent — prune or restore)
```

❌ Blocked: the spec gate remains failed on both revisions; this receipt does not close those findings.

✅ Verified: both Linux checkouts were clean before tests, after tests, and after the spec gate. The six `*-status-{before,after,final}.txt` files are intentionally empty. Windows HEAD was still the pinned revision before receipt finalization; all Windows worktree changes were confined to this folder. [verification.json](verification.json) records these checks and the unchanged handoff SHA256. Commit identity is reported separately after commit, avoiding a self-referential receipt.

## Deviations and limits

- Two ordinary Linux clones were used instead of a clone plus linked worktree. Both retain complete Git history and valid Linux Git metadata; no tests run in /mnt/c.
- HOME was left unchanged. FLOSS_AGENT_DIR, FLOSS_AUDIT_DIR, FLOSS_MCP_AUDIT_DIR, COORDINATION_ROOM_ROOT/LOG, and TMPDIR are set to fresh per-stage paths under the owned Linux root. PYTHONPATH and COORDINATION_ROOM_BOARD are unset. Overrides are recorded in runs.json.
- Subprocess exit codes are captured directly instead of relying on the pytest-to-tee pipeline. Raw stdout/stderr and JUnit are retained byte for byte.
- The comparison intentionally uses the head requirements for the base too. This verifies code differences under one current environment, not the historical base dependency resolution.
- Ubuntu under WSL is a Linux verification environment, not a GitHub-hosted ubuntu-latest runner. Windows-only skips and every new skip are listed rather than counted as passes.
- No source, test, plan, runtime configuration, or primary checkout changes; no fixes, live Windows daemon actions, push, pull, rebase, or PR. Only this receipt directory is authorized for the final project commit.
- Linux clones and environment are retained for reruns. Expected heartbeat ticks may be written under the owned clone parent; checkout status does not establish that no external scratch files were created.
- Not tested: advisory ARF suite, production deployment/rollback, live Hermes, load/soak, or Windows behaviour beyond the already existing receipts.

✅ Verified: the staged whitespace check flags four lines emitted by pytest in the raw stdout/JUnit failure receipts; [receipt-whitespace-check.txt](receipt-whitespace-check.txt) preserves the diagnostics. All other staged files pass that check. Raw bytes are retained as required by the handoff.
