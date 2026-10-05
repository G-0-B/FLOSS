# Coordination room board v1: critical review

Review date: 2026-10-02. Disposition: **revise before implementation/deployment approval**. The message-board direction is useful; the supplied package tests do not establish the claimed shared-state safety.

This is an evaluation, not authorization to execute the plan. No repository source, plan, branch, live coordination log, production daemon, protected configuration, or canonical status was changed by this review. Test servers ran only on scratch ports. Artifacts below are noncanonical review evidence.

## Reviewed identity and method

- Plan: `C:/~shit/FLOSS/docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md`, 2,610 lines.
- SHA-256 at initial and final read: `eaa3d75065d8d3582cdcaff1e017d5b214c083ef794a72ba09c583e0462886ff`.
- FLOSS base: `4aab13e30f3c2960da787b47c90926256b4b5b73`.
- A2A base: `225287c2ed310158a3f699688447db2964e425b2`.
- Primary FLOSS checkout: `27445786d7aaa0e01c92b9eb726b7cb3d9da479e`, dirty. It was inspected, not used for implementation.
- Python 3.13, installed MCP 1.27.0, A2A SDK 1.1.2, pytest 9.0.2, jsonschema 4.23.0.
- Extracted base package files from Git objects into an isolated temporary fixture tree; overlaid exact fenced source/test bodies and four exact server substitutions. `extraction.json` records source lines and identities.
- Orientation escalated to T3 because this plan embeds a complete implementation. Read the requested skills, L0, operator primer, index/ADR index, relevant operating instructions, ADR-18, coordination-v1 design/plan, and the exact affected implementations. No `_reference/` reads, event-queue changes, source-chain writes, or project dispatches.

## What is worth retaining

The plan supports shared understanding in the commons by making discussions discoverable, preserving messages, and distinguishing evidence lookup from truth validation. It is correctly scoped to Plane A; it proposes no bypass of Holochain integrity validation. Extending existing MCP tools, retaining old log rows, using deterministic A2A commands, and making the bridge an MCP client are sensible reuse choices. Phase 1 can stand without A2A. The baseline spec-gate debt is disclosed rather than represented as a pass.

These are design strengths, not proof of runtime safety or universal-flourishing outcomes. Success should mean better shared context, fewer conflicting writes, preserved provenance, visible dissent, and bounded operator burden, rather than feature count or delivery speed.

## Findings and closure conditions

### B1 — P1: The regeneration instruction can overwrite user-wide memory with an empty index

Locations: plan 1755–1764 and 2578; base `scripts/materialize_shared_agent_memory.py` 412–480, 485–493; base `shared-agent-memory-surface.json`.

**Verified:** Task 5 assumes omitting `--include-user-scope` makes regeneration repository-scoped. This materializer has no such flag or scope gate. Its Claude target is an enabled absolute user-directory path. Its default workspace root is the script checkout's parent. Under the prescribed worktree layout, that resolves the canonical source to `FLOSS/.worktrees/FLOSS/docs/agent-memory`, which is absent; zero entries are collected.

Read-only reproduction:

```powershell
$env:PYTHONPATH = ''
& C:\Python313\python.exe C:\~shit\FLOSS\.worktrees\coordination-room-rebased\scripts\materialize_shared_agent_memory.py --check
```

Observed, among the five findings:

```text
CHECK DRIFT C:\~shit\FLOSS\.worktrees\FLOSS\docs\agent-memory\MEMORY.md
CHECK DRIFT C:\Users\kalis\.claude\projects\C---shit\memory\MEMORY.md
```

An additional dry-run against the same base reported `PLAN WRITE` for the user index and a generated index containing only its heading and preamble. No actual regeneration was run.

**Consequence:** following the plan's prescribed remedy for drift would create projections under the wrong tree and replace the user's Claude index with an empty one. With the root corrected but the target policy unchanged, user-wide writes still occur.

**Closure:** use an explicit worktree-aware source/output mapping and an actual output-target restriction; enumerate intended destinations before mutation. Test the exact worktree invocation with sentinel user files. Do not import the hook/skill materializer's scope semantics by analogy. Do not commit unrelated drift.

### B2 — P1: A rejected duplicate startup writes BOARD.md before the singleton check

Locations: plan 1214–1224, 1596–1598; inherited server main and `packages/mcp_daemon.py::run_http_daemon`.

**Verified:** constructing the module-global tools invokes `CoordinationRoom.__init__`, which immediately projects the board. The PID guard runs later, inside `run_http_daemon`. In an isolated reproduction with `claim_singleton` returning False, executing the server's main path produced:

```text
[FLOSS MCP] already running on :7334; exiting.
R1 rejected-start exit= 0 guard_called= True board_changed= True
```

This deterministically violates the plan's single-writer promise for the board. It does not demonstrate a second event-log append. Concurrent starts can also contend for the same fixed `BOARD.md.tmp`; a stale projection write is possible without acquiring daemon ownership.

**Closure:** acquire ownership before constructing any mutating room/projection. Keep import and duplicate rejection free of persistent writes. Add a test that rejects a second startup and checks unchanged board/log bytes, plus an overlap test involving an active write.

### B3 — P1: “Disjoint files” does not reconcile the competing claim authorities

Locations: plan 82, 164, 1720–1724; `2026-09-02-coordination-v1.md` 5–7, Task 4; its design sections 3 and 4.4.

**Verified document conflict; future coexistence remains Specified:** this plan calls the room claim table the authority and teaches `room_claim` before writing. Coordination-v1 explicitly replaces daemon-dependent ownership with Git-ref claims checked by write hooks. Neither proposed ownership path consults or updates the other. Its design retains the room as a reference/routing option, not a liveness dependency.

**Consequence if both land as described:** an agent can see a successful room claim while the hook sees no Git-ref reservation, or see a board reservation that disagrees with enforced ownership. A waiver to edit the package does not decide precedence, identity mapping, migration, or conflict handling. The code can merge textually while the protocol remains inconsistent.

**Closure:** explicitly choose the authority and transition contract. Either make room reservations explicitly legacy/advisory and label them accordingly, or route both interfaces through the chosen claim primitive under an approved design. Test the disagreeing-owner scenario. The message-board work itself need not wait for an invented new authority.

### B4 — P1: The Phase 1 live command selects a shadow bus from the required worktree

Locations: plan 40, 1775–1781; inherited server `_WORKSPACE_ROOT` and `_log_path`.

**Verified path calculation:** with the prescribed worktree root and no preexisting overrides, the bare `python -m packages.coordination_room.server` resolves:

```text
C:\~shit\FLOSS\.worktrees\.agent-surface\rooms\default\events.jsonl
```

The plan expects:

```text
C:\~shit\.agent-surface\rooms\default\events.jsonl
```

The PowerShell launcher pins the shared log, but the plan presents the bare command as an equivalent option. The bare command lacks that environment setup. This can start an empty, separate room after the old daemon is stopped and produce a misleading successful smoke check.

**Closure:** provide one exact startup contract with explicit interpreter, checkout, log, board, audit, and process identity. Assert paths and source revision before any live post. Phase 1 should have the same explicit runtime authorization boundary as Task 8. Include a scoped rollback that preserves the log and restores the intended previous process; avoid using all-daemon stop/start as a casual room restart.

### B5 — P2: The new board override is neither protected from log aliasing nor isolated by tests

Locations: plan 1566–1570, 1522–1531, 2138–2144, 800–812.

**Verified:** creating a room with `board_path == log_path` replaces the JSONL record with Markdown during construction. A second construction fails:

```text
R2 board/log alias first_line= '# Coordination board'
R2 restart= JSONDecodeError
```

Also, the server and e2e fixtures redirect ROOT, LOG, and audit but inherit `COORDINATION_ROOM_BOARD`. Running the supplied server tests with that variable set to an isolated sentinel path yielded `1 failed, 1 passed`; the sentinel was overwritten with a board outside pytest's redirected root. This was reproduced only against a scratch sentinel.

**Closure:** validate distinct resolved source/output/temp paths before opening or writing; test aliases. Explicitly redirect or clear every new path override in test fixtures. A test that observes its output elsewhere must not mutate an operator's configured board.

### B6 — P2: The evidence label promises a stronger time relationship than it records

Locations: plan 43, 182–186, 1295–1315.

**Verified:** resolution runs before the lock and append. In a deterministic interleaving, the file was renamed after the lookup and before append; the returned status was still `resolved` while the referenced path no longer existed. The label therefore establishes a lookup result, not existence at event-write time. This does not mean the lookup result itself was incorrect.

The event also stores no lookup timestamp, content digest, full resolved Git OID, or repository/checkout identity. Later file edits and switching which worktree serves the shared log can make the same short reference describe different evidence.

**Closure:** minimally change the contract to “resolved during admission lookup” and record the lookup context/time. If historical evidence must be reproducible, capture immutable identity (file digest and full Git OID with repository identity). Continue distinguishing resolution from truth; no reason to introduce truth gating in this router.

### B7 — P2: The 24-hour roster silently becomes stale while idle

Locations: plan 190, 743–752, 787–797, 1234–1244.

**Verified:** the same event log renders different rosters at two different `now` values, but the persisted view refreshes only on startup or mutation. An idle board can continue displaying expired agents under “last 24h,” with no generated-at timestamp to qualify the heading. It is a function of `(events, now)`, not just the log.

**Closure:** include an explicit as-of timestamp and last processed sequence, with the window defined relative to that timestamp; or specify a refresh-on-read/timed refresh policy. Test an idle interval crossing the 24-hour boundary. A durable-looking stale status view was already a problem in the predecessor design.

## Inherited limitations, not new regressions

**Verified bounded failure injection:** the existing claim implementation changes its in-memory table before append. With append forced to raise an OSError, the running room retained `{'x.py': 'a'}` while a reconstructed room had `{}`. This behavior is also in the base implementation; it must not be reported as a new board defect. The new board makes the distinction between RAM, log, and projection more visible. Preserve it in the risk ledger and define the supported failure/recovery contract before making strong durability claims.

The base log has no explicit fsync or torn-tail recovery, and the bridge has no documented ambiguous-ack/idempotency contract. Those are inspection observations and missing guarantees, not reproduced crash/retry failures in this review. An append-only API on its own is not evidence of crash durability, exactly-once delivery, or authenticated authorship.

A2A sender prefixes are useful attribution labels, not authentication or permission. Loopback and deterministic grammar do not establish identity. The plan acknowledges unauthenticated identities; avoid expanding that into stronger “peer handshake” assurances.

## Validation results and limits

Commands ran from the extracted baseline or proposed fixture roots, using `C:/Python313/python.exe`, cleared PYTHONPATH, and `-p no:cacheprovider` for pytest:

| Check | Observed result |
|---|---|
| Base coordination-room package | **21 passed** |
| Exact proposed coordination-room package | **75 passed** |
| Proposed coordination-room + A2A packages | **111 passed, 2 skipped**, 102 dependency deprecation warnings |
| Ruff on coordination package and new bridge/tests | **All checks passed!** |
| Supplied server tests with scratch board override | **1 failed, 1 passed**, sentinel overwritten |
| Memory materializer check / dry-run | Wrong worktree paths and user-memory write target reproduced; no writes applied |

The two combined-run skips are the optional live Hermes probe and the inherited `.mcp.json` ancestry check, because that machine-local file is absent in the isolated fixture. This explains the difference from the plan's `112 passed, 1 skipped`; it is not evidence of a new regression. The real FastMCP/A2A scratch integration test passed.

Not performed: whole-repository green-set comparison, clean-runner dependency installation, production daemon start/stop or smoke posts, actual memory regeneration, live Hermes integration, crash/power-loss tests, load/soak testing, consensus/governance dispatch, Holochain validation, or external-paper benchmark verification. No claim here upgrades those checks to PASS. The plan's exact three-line spec-gate baseline was not independently rerun in this review.

## Suggested revision order

1. **NOW:** close B1–B5 before treating the plan as safe to execute. Resolve scope/authority and fix deterministic runtime path and writer-order defects.
2. **NOW:** tighten evidence and freshness contracts (B6–B7), then add adversarial acceptance checks next to existing happy-path tests. Preserve the baseline and full reviewer dispositions.
3. **LATER:** keep A2A optional until Phase 1 proves one authoritative bus, correct ownership semantics, safe projections, observable failure, and reversible deployment. Define acceptance by those behaviors rather than fixed test totals.
4. **NEVER:** treat a room claim as write authorization unless the chosen enforcement mechanism actually honors it; treat resolved evidence as truth; treat a file-edit waiver as broad runtime/merge/governance permission; or auto-regenerate shared/user surfaces just because a check reports drift.

No new broker, database, agent framework, or competing board is needed to close these findings. Tightening the existing boundaries is the useful next step.

## Evidence files

- `extraction.json`: exact plan hash, base commits, source block line ranges.
- `baseline-tests.txt`: baseline test result.
- `proposed-tests.txt`: combined test output.
- `adversarial-output.txt`: rejected-start, alias, evidence-interleaving, roster, inherited append-failure outputs.
- `launch-and-materializer-output.txt`: default launch paths and materializer dry-run output.
- `inherited-board-override-tests.txt`: actual failing fixture test.
- `FLOSS/`: extracted proposal and tests used for this review; `baseline/`: extracted base package fixture.

Re-run the isolated adversarial cases with: C:/Python313/python.exe C:/Users/kalis/AppData/Local/Temp/codex-room-board-review-20261002-162041/reproduce.py. The actual run is retained in reproduce-output.txt; each run preserves its own unique fixture directory.

