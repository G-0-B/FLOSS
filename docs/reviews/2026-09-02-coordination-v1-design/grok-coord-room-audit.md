# Grok coordination-room-rebased audit

**Date:** 2026-09-02
**Worktree:** `C:/~shit/FLOSS/.worktrees/coordination-room-rebased` → branch `feat/coordination-room-rebased` @ `2460c55`
**Original compared:** `feat/coordination-room` @ `45b3f26` (task says `2460c55` is the original base; in current repo that hash is the rebased HEAD — original HEAD is `45b3f26`)
**Common ancestor:** `08619f0` (`fix(provenance): the two findings I had been deferring, and FM-8`)
**Worktree state:** `git status` clean, no uncommitted changes. `origin/reconcile/pr38-salvage-20260817` diverged (7 vs 16 commits) — not relevant to this lane.

## 1. What git says — the shape of divergence

```
feat/coordination-room          45b3f26 (HEAD, 16 commits past 08619f0)
feat/coordination-room-rebased  2460c55 (HEAD, 46 commits past 08619f0)
common base                     08619f0
```

`git diff feat/coordination-room..feat/coordination-room-rebased --stat` = **53 files, +7172 / -2757**
`git diff --stat` in reverse = +2757 / -7172 (symmetric).

The 5 newest commits on each side are **patch-identical cherry duplicates** (same author/date/message/diff, different parent hashes/trees):

| rebased | original | message |
|---------|----------|---------|
| `c8f8607` | `5323633` | `docs: close skill reminder review gates` |
| `72bc445` | `1daef76` | `docs: harden skill reminder design after review` |
| `ec8ae06` | `ba10735` | `docs: design task-time skill reminders` |
| `b082f15` | `cc71e5d` | `docs: point agents at the coordination room` |
| `9c29872` | `b757373` | `feat(coordination-room): file-claim MCP on :7334` |

Trees differ (`46d5f00` vs `6b77bcb`) because parents differ — expected for cherry-picks across divergent histories. The remaining `46-5=41` commits on rebased and `16-5=11` on original are disjoint.

`git log --cherry 08619f0..45b3f26` and `08619f0..2460c55` both show all `+` (no patch-id collisions beyond the 5 above) — two real forks, not a rebase that was force-pushed.

**Does `coordination_room/` itself diverge?** No.

```
git diff feat/coordination-room..feat/coordination-room-rebased -- packages/coordination_room/
# (empty — 0 lines)
```

Both branches contain exactly the same v0 package landed by the operator-commits `b757373/9c29872`. Grok did **not** fork the coordination-room package; the worktree is current.

## 2. What Grok actually changed on `coordination-room-rebased`

### 2.1 Grok-unique additions (not on `feat/coordination-room`)

**Hooks (2 new files, absent on original):**
- `hooks/grok_session_register.py` — Grok `SessionStart` hook. POSTs `/agentmemory/session/start` with `sessionId`+`cwd`, fail-open, 1.5s timeout. Smallest harness bridge; no stdout handling (per Grok Build 10-hooks.md).
- `hooks/grok_pretool_st.py` — Grok `PreToolUse` hook for tool `grep` → injects `additionalContext` reminding `st / smart-tree MCP` instead of grep/ls/find, and agentmemory save/recall vs `.remember`.

**Startup wiring (coordination-room only via Grok):**
- `scripts/start_mcp_daemons.ps1` — `+102/-5` vs original. Adds `Resolve-ServerPid` (npm `.cmd` → node pid walk), `$skipped` array, `Start-Daemon` with 1.5s settle + singleton-exit-0 vs failure distinction, and **coordination-room :7334 launch** that primary lacks:
  ```powershell
  $intakeRoot = if ($workspace -match '\.worktrees\') { <up 3 levels> } else { <up 1> }
  $env:COORDINATION_ROOM_LOG = $intakeRoot/.agent-surface/rooms/default/events.jsonl
  $env:COORDINATION_ROOM_ROOT = $workspace
  Start-Daemon ... packages.coordination_room.server ... :7334
  ```
  Log is pinned to workspace intake mouth so a worktree launch doesn't create a second bus. Primary's file still says `start OmniRoute + both MCP daemons` and has no 7334 block, no `Start-Daemon`, no `Resolve-ServerPid`.
- `scripts/stop_mcp_daemons.ps1` mirrored change (coord room pid, intake root).

Commits: `ad463b2 (feat hooks)` + `2460c55 (feat daemons: start/stop :7334)` and ~30 earlier daemon/lock/anchor fixes that hardened `mcp_daemon.py`, `packages/activity_log/filelock.py|anchor.py|provenance.py`, `scripts/provenance_anchor.py`, `watch_intake.py`, `reasoning_ensemble/*`, etc. These are bug-fix history, not coordination-room-specific, but they ride on this branch because Grok kept fixing the drive while building the room.

**Coordination-room package (shared, not unique):**
- Landed identically on both branches (807 lines across 17 files):

```
packages/coordination_room/{__init__,claims,gateway,log,paths,room,server}.py
packages/coordination_room/tests/{test_claims,test_gateway,test_paths,test_room}.py
+ docs/specs/coordination-room.{spec.md,schema.json}
+ docs/superpowers/{specs,plans}/2026-08-30-coordination-room*.md
+ shared-agent-surface.json / .mcp.json vibe list (port 7334)
```

### 2.2 What primary has that rebased does NOT

11 commits beyond the 5 shared (in primary order newest→oldest):

- `45b3f26 feat(gates): an omitted tier stops being an exemption` — fail-closed `tier_decision_problems()`, `tier_exempt: string`, file-locking spec tier, `deferred_promises()`, `st --everything` fix.
- `b05f7dd docs(handoff): a seam packet any harness can read cold` — `HANDOFF.md`
- `86cd7d5 docs(reviews): the filelock reuse decision was made in ADR-20`
- `633c87a feat(spec-gate): report reuse-gate coverage`
- `2deb8c9 docs(memory): gates here are exempt by default`
- `e949d87 docs: design polyglot evolving plugin` + `a15f5f3/chore(memory)/52a10a2/48875cf/10a69cb` — memory/surface materializer frontmatter, `shared-agent-surface.json` hermes approvals, chunked-heredoc workaround note.

Net effect `diff rebased..primary` adds: `GATE-ADOPTION-AUDIT.md`, `HANDOFF.md`, `PACKET.md`, `RESULT.md`, `file-locking.spec.md`, `polyglot-evolving-plugin-materializer-design.md`, `gates-exempt-by-default.md`, `bash-heredoc-chunked-writes.md`, plus `scripts/spec_gate.py`, `materialize_shared_agent_*`, and spec-registry entries that Grok's tree predates.

### 2.3 Did another agent writing to original cause the divergence?

**Yes, but not by touching the coordination room.** The coordination-room slice is cleanly identical. Divergence is *parallel evolution of the surrounding substrate*:

- While Grok sat on `feat/coordination-room-rebased` (forked ~2026-08-30 02:57, kept rebasing/fixing), the operator + Claude/Codex kept landing materializer, spec-gate, gate-exempt, and handoff work on `feat/coordination-room` past `08619f0`.
- At the same time Grok landed ~41 fix commits (locks, daemons, anchor, ensemble) that never got cherry-picked onto primary. Those fixes are ahead of primary for that subsystem, while primary is ahead for memory/spec/gate docs.

This is the classic "two owners of the same timeline" pattern the branch was noted to avoid — the worktree isolation worked (no file-level conflict), but semantic divergence is 53-file wide.

## 3. Package-level audit — `packages/coordination_room`

### 3.1 Claim types / worktree/branch claims
- **Only claim type:** normalized file path (`packages/coordination_room/paths.py:normalize_path`). One exclusive holder per posix key. Same-agent re-claim idempotent, other agent → `ClaimConflict(path, holder)` → JSON `{ok:false, error:"conflict", holder, path}`.
- **No task claims, no branch claims, no worktree claims, no desktop leases, no CRDT.** The spec header says `No pycrdt in v0 (AgentRoom measured coordination tools, not the CRDT, as the load-bearing step)` and the design caps v0 at file paths. This matches brainstorm → spec → plan.
- **Worktree awareness:** only via `COORDINATION_ROOM_ROOT` (per-launch env) and `COORDINATION_ROOM_LOG` (pinned to intake mouth on Grok). The `ClaimTable` itself is root-scoped, not worktree-branch-aware — all worktrees sharing a log share the same table.

### 3.2 Specs changes
- New spec `docs/specs/coordination-room.spec.md` v0.1.0 (`truth_status: Specified; unit tests Verified on landing`) and JSON schema `coordination-room.schema.json` (seq/ts/type/agent_id + conditional path/text, Text max 4096).
- `docs/specs/spec-registry.json` registers those two plus mcp surface entries (loopback bind, PID filename, port).
- **Gap vs substrate spec expectations:** the spec falsifiers (`two holders on one path succeeds; conflict only as chat; binds non-loopback; log rewritten in place`) are covered by unit tests. No integration proof that `127.0.0.1:7334` actually refuses non-loopback under Windows firewall — accepted per router-not-controller scope.

### 3.3 Startup wiring
- **Primary:** no 7334 wiring; daemons are fire-and-forget (`Start-Process ...` with no settle, no liveness, no room).
- **Grok:** full wiring described above. Fixes a real trap: worktree-started bus would otherwise split the event log. Grok's `$intakeRoot` conditional is the only thing preventing two buses.
- **Pending:** Grok's wiring still lacks the primary's later `$PSScriptRoot` / `$FLOSS_PYTHON` / venv / `Get-Command python` portability fixes (`b05f7dd` lineage) — a forward-port would clobber that if cherry-picked naively.

### 3.4 Tests
- 4 test files, ~17 tests (2026-08-30: 17 passed). Coverage:
  - `test_paths.py` — relative→posix, backslash collapse, `..` escape, absolute inside/outside root.
  - `test_claims.py` — conflict includes holder, idempotent re-claim, release frees, release by non-holder denied, two paths independent.
  - `test_room.py` — claim appends seq, conflict doesn't append, replay restores claims across restart, broadcast text 4096 cap.
  - `test_gateway.py` — JSON-wrapped conflict/broadcast/state.
- All tests use `tmp_path` with `CoordinationRoom(root=tmp, log=tmp/events.jsonl)` — no live daemon. No concurrency test beyond single-threaded `threading.Lock()` (which is process-local, not cross-process). No multi-process contention test.

## 4. Gaps vs brainstorm / design 1/2/3

No document literally named "brainstorm 1/2/3" exists in `.hermes/plans` or `FLOSS/docs`. Interpreting as the three source intents behind the room (AgentRoom findings, design spec, implementation plan):

| Intent | Expected | Actual gap |
|--------|----------|------------|
| **Brainstorm 1 — AgentRoom measurement ("tools, not CRDT")** | File-claim router first, CRDT later | **Closed** — no pycrdt, and commit message cites `Human-as-bus is the failure mode AgentRoom measured` |
| **Brainstorm 2 — Plane A router, not controller** | Does not write files, merge, or adjudicate truth | **Closed** for claim/broadcast; minor overreach: `Grok_session_register` writes to agentmemory HTTP, which is a side-effect beyond "router not controller" but scoped to session start |
| **Brainstorm 3 — Composable with computer-use leases** | Compose lease shape, do not share that table | **Closed** verbally (spec: `Compose the computer-use lease shape; Do not share that table`) but **untested** — no test asserts two tables don't interfere, and Grok's `COORDINATION_ROOM_ROOT=workspace` makes the room root checkout-relative while computer-use leases are per-machine. No cross-table integration test exists. |

**Remaining open gaps (vs the design's own global constraints):**

1. **Task claims explicitly deferred** (`v0 no: task claims`). If the next slices expect task coordination, a path-only bus will be papered over with path-encoded task ids — worth calling out.
2. **Cross-process mutual exclusion is threading.Lock only.** `ClaimTable` + `EventLog.append("a")` is safe inside one server process, but not across two servers sharing the same `events.jsonl` — filesystem lock would be needed. Currently prevented by singleton PID, not by protocol. Two launches racing before PID is claimed could diverge the table vs log.
3. **`broadcast` has no addressee / no per-worktree partition.** In a worktree fleet all rooms share one `events.jsonl` at the intake mouth (by Grok's fix). That is correct for a single bus, but means `room_read(since_seq=0)` replays every worktree's chatter — no filtering.
4. **No metrics / no audit beyond `janus-coordination-room-audit.jsonl` via `register_audited_tools`.** No retention or rotation described.
5. **Hook coverage is Grok-only.** Claude/Codex/Hermes won't run `grok_session_register.py` or `grok_pretool_st.py` unless their own `SessionStart`/`PreToolUse` is wired. Design says `point agents at the coordination room` but the wiring is harness-specific.

## 5. Recommendations

### Reconcile the two branches (short-term)
1. **Keep `packages/coordination_room/` from either branch** — they're identical; no merge conflict.
2. **Cherry-pick Grok's two commits onto `feat/coordination-room`:** `ad463b2` (hooks) + `2460c55` (7334 wiring). Then **re-apply the primary's post-08619f0 portability fixes** (`$PSScriptRoot`, `$FLOSS_PYTHON`, venv detection, `Get-Command`) on top of Grok's `Start-Daemon` — don't overwrite the primary's fixes with Grok's older base. Net: one file with both improvements.
3. **Decide on `COORDINATION_ROOM_LOG` pinning policy** explicitly: Grok's intake-mouth pin is the right default for worktrees, but document it in `RUNTIME_SURFACES.md` (currently just a 2-line mention). Primary's `RUNTIME_SURFACES.md` edit diverges.
4. **Run tests from both sides in one suite:** `python -m pytest packages/coordination_room/tests -v` + `packages/tests/test_mcp_daemon.py` + `scripts/tests/test_spec_gate*` — the 53-file diff hides a `857 passed; one pre-existing red` on primary vs unknown on rebased. Verify no regression.

### Decide fate of 41 Grok-only fix commits
These fixes (locks, anchor, ensemble) are substantive and predate primary's handoff/gate work. Options:
- If they are valuable, **rebase primary's recent 11 commits on top of `2460c55`** (or cherry-pick them in reverse) — yields one lane with both.
- If they conflict with review-loop fixes landed after `08619f0` on main, audit patch-by-patch — many touch the same `anchor.py`, `provenance.py`, `filelock.py` lines that primary's `fix(memory)` lineage also touched for different reasons.

### Close gaps before v0.1
- Add one integration test that starts the FastMCP server in a subprocess and asserts `room_claim` conflict is visible via HTTP JSON (not just in-process). Bind check: assert `127.0.0.1` only.
- Add a doc note that `broadcast` is global and `coordination_room` is per-workspace bus, not per-worktree.
- Wire the session reminder for non-Grok harnesses (Hermes `SessionStart` → same agentmemory endpoint, or one harness-agnostic hook) if multi-harness adoption is required.
- If cross-process file contention is a real risk (two servers on same log), add `FileLock` around `EventLog.append` — reuse `packages/activity_log/filelock.py` Grok just fixed.

### Housekeeping
- `git status` clean, but `feat/coordination-room-rebased` currently tracks `origin/reconcile/pr38-salvage-20260817` (which it diverged from). Reset upstream: `git branch --set-upstream-to=origin/feat/coordination-room-rebased` or delete remote branch if not needed.
- Remove worktree `.agent-surface/heartbeat/janus-coordination-room-audit.jsonl` from ad-hoc `find` if it pollutes `st` corpus.

## 6. Verdict

Grok built exactly the coordination-room slice it was asked to — path-scoped exclusive ClaimTable, append-only log, replay, 5-loopback tools, tests, spec, with the extra discipline of **not starting the bus in every worktree**. The package needs no merge fixup. The divergence is collateral substrate drift: another lane kept improving materializers/gates/handoffs while Grok kept fixing locks/daemons. Both sets of improvements are worth keeping; the merge is one file (`start_mcp_daemons.ps1`) where both improved opposite ends.
