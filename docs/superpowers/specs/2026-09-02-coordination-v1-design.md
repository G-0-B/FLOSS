# Coordination v1 — Derived Status + Git-REF Claims — Design

> Status: Draft — awaiting operator approval before `writing-plans` cuts tasks
> Scope: Architectural. Restructures how agents coordinate; changes an interface others depend on.
> Decision gate: `flossi0ullk-consensus` System claim required before implementation (blast radius: Module/System).
> ADR-18: adopt → extend → compose → build checked — see §7.

## 0. Evidence envelope (why this shape)

**CWD:** `C:/~shit/FLOSS` · **Probed:** `orient_probe.py` + 4 parallel verifications 2026-09-02
**Facts [V]:**
- Coordination room `packages/coordination_room/` — 17 tests pass 2026-08-30, binds `127.0.0.1:7334`, was `ConnectionRefused` whole window it existed. Not in `scripts/start_mcp_daemons.ps1` (grep 7334 = 0 hits).
- `git update-ref refs/agent-claims/<name> <new> <old>` CAS on Windows 11/NTFS/git 2.54.0 — 8-way Popen race → 1 win / 7 blocked, `rc=128 is at <winner> but expected <old>`, lock `*.lock` held only during write, no stale locks. Report: `.hermes/plans/cas-proof-report.md`.
- Work Board §0 clean ladder falsified: `reconcile/pr38-salvage` ↔ `feat/preservation-spine` mutually non-ancestral (`merge-base 31bcad0`, exit 1 both ways), `coord-room` ↔ `coord-room-rebased` (`08619f0`, 16 vs 46 past base). Ladder intentionally broken §0.1c. Report: `.hermes/plans/ancestor-matrix-report.md`.
- Grok `coord-room-rebased@2460c55` vs `coord-room@45b3f26` — `packages/coordination_room/` diff 0 lines (identical v0). Grok added `hooks/grok_session_register.py`, `hooks/grok_pretool_st.py`, `:7334` wiring via `Start-Daemon` + `Resolve-ServerPid` + `COORDINATION_ROOM_LOG` pin. Divergence 53 files +7172/-2757 is parallel substrate evolution, not room conflict. Report: `.hermes/plans/grok-coord-room-audit.md`.
- Derived view sketch: 6 sections making 4 scoped failures seconds-visible, zero stored state. Report: `.hermes/plans/derived-status-sketch.md`.
**Falsifier:** If a successful `git update-ref` CAS can be shown non-linearizable on NTFS, or if `coordination_room` startup liveness is proven supervised, re-evaluate claim-primitive choice.

---

## 1. Problem and non-goals

**Problem:** Agents duplicate work and miss existing fixes because coordination state is maintained manually (Work Board §0, room claims for one checkout's file paths) or lives behind a daemon that wasn't running. All failures measured happened outside the room's claim unit — different worktrees/branches, no path collision.

**Non-goals (v1):** No CRDT/MELD merge, no A2A task handshake, no controller that writes files, no new daemon to supervise. No pycrdt.

## 2. Reframe — derive, don't maintain

Split state along derivability:

- **Derivable (never write, recompute on demand):** branch topology, ahead/behind, divergence, worktree list+HEADs, claim refs list, open PRs, “fix already exists elsewhere” (`git log --all -S`). All four scoped failures are in this set.
- **Not derivable (must write):** intent — “I am about to take this worktree/branch/path.” Exclusive half only.

Work Board §0 is a typed snapshot — stale by design. The room needed `:7334` up — wasn't. `.git/refs/` cannot be down and is already shared across all 20 worktrees via common dir.

## 3. Approaches considered

| # | Approach | Trade |
|---|----------|-------|
| **1** | **Derived status + claims as git refs** — status computed, claims are `refs/agent-claims/*` via `git update-ref <new> <old>` CAS. Enforcement via existing `hook_pre_write.py` (already fires). No daemon. | **Recommended.** Needs hook materialization + TTL/GC. Reuses git, adopt-before-build. |
| 2 | Extend room, actually run it | Fixes room scope but not its liveness; needs supervision work first. |
| 3 | Convention only (derived view, no claims) | Smallest artifact; catches failures as visibility but doesn't stop worktree borrow. Graceful fallback of 1. |

## 4. Recommended architecture — Approach 1

### 4.1 Derived status command

Single entry: `hermes status` (alias `floss status --derived`, Python `FLOSS/scripts/coord_status.py`). No file written. One screen, `--all` expands, `--json` for machines, `--show-patch <sha>` to diff fix elsewhere.

**Sections and sources:**

1. **Worktree table** — `git worktree list --porcelain` + `git status --porcelain` per worktree + `stat` mtime + `rev-list --left-right --count HEAD...origin/main`.
2. **Branch containment matrix** — `git branch --contains HEAD` + `git merge-base --is-ancestor` (exit 0/1) across live branches.
3. **Divergence alerts** — `rev-list --left-right --count A...B`, flag if `base age > 24h` or `behind > N`.
4. **Claim refs** — `git for-each-ref refs/agent-claims/ --format='%(refname:short) %(objectname:short) %(committerdate:iso)'` + reflog parse for holder.
5. **Open PRs** — `gh pr list --repo G-0-B/FLOSS`, 5s timeout, cached 60s flagged `[cached]`.
6. **Already-fixed elsewhere** — last 20 `fix:` tokens → `git log --all -S <token> --oneline`, highlight branches missing the fix.

**Why cannot go stale:** zero stored file. Every cell recomputed. Worst case is slow `gh` (cached, flagged). No manual row to forget.

### 4.2 Claim primitive — git refs as intent

- **Namespace:** `refs/agent-claims/<kind>/<id>` where `kind ∈ {worktree, branch, path}` and `id` is normalized (posix path for path, `worktree/<sanitized>` for worktree, `branch/<sanitized>` for branch).
- **Value:** blob SHA of JSON `{"holder": "<agent_id>", "kind": "...", "id": "...", "created": "iso", "ttl": 3600, "branch": "<current HEAD>", "worktree": "<path>"}` — written via `git hash-object -w`.
- **CAS:** `git update-ref refs/agent-claims/<kind>/<id> <new_sha> <expected_old>` where `expected_old` is `000...0` for create, current `rev-parse` for update, or delete via `update-ref -d <ref> <old>`. Exactly 1/8 wins on NTFS — proven.
- **Release:** `git update-ref -d refs/agent-claims/<kind>/<id> <old>` only by holder (enforced in hook, not git ACL). `force_drop` requires `--force` + audit log entry.
- **TTL/GC:** Claims carry `created + ttl`. `hermes status` flags `expired` (age > ttl). GC: `git for-each-ref` scan + `reflog` age check; expired claims auto-prunable by holder or by any agent after `2×ttl` with broadcast `room_broadcast`-style log to `.agent-surface/coord/claims.jsonl` (append-only, not the room's bus). No packed-refs surprise — loose refs, no reflog file after delete is expected.
- **Lock:** `.git/refs/agent-claims/<name>.lock` — git handles. No hand-rolled lock. Rate: single `update-ref` per claim, no busy loop.

### 4.3 Enforcement — reuse existing surfaces

- **Primary:** `hooks/hook_pre_write.py` already intercepts `Write|Edit|MultiEdit` (Claude), `write_file|replace` (Gemini), `patch` (Hermes), `write_to_file` (Antigravity). Today only Gemini wires it (`.gemini/settings.json` BeforeTool). **Fix:** materialize `shared-hook-surface.json` so Claude/Codex/Hermes get same `PreToolUse` hook. Current filter `SUBSTANTIVE_PATH_SEGMENTS = ("/packages/",)` + canon `"/docs/adr/"` must widen to include claimed `kind` paths or enforcement only covers substantive edits.
- **Secondary:** git hook `pre-commit`/`pre-push` checking `refs/agent-claims/*` for current `HEAD` worktree/branch — installed via `shared-hook-surface` (today `core.hooksPath` unset, hooks only `*.sample`).
- **Out of scope:** OpenCode has no `PreToolUse` surface — declared advisory-only for OpenCode agents until wired.

### 4.4 What Grok built and how we keep it

- Keep identical `packages/coordination_room/` (0-line diff) as v0 reference/routing option — not retired, but not required for liveness. Its 17 tests remain green.
- Cherry-pick Grok's `:7334` wiring pattern onto primary's portable startup: merge `Start-Daemon`/`Resolve-ServerPid`/`$skipped`/`settle` onto existing `$PSScriptRoot`/`$FLOSS_PYTHON`/`venv` portability fixes — don't overwrite. Pin `COORDINATION_ROOM_LOG` to workspace intake mouth so worktree launches share one bus.
- Take Grok's `grok_pretool_st.py` (smart-tree reminder) as-is; `grok_session_register.py` is Grok-specific — keep behind Grok harness only.

## 5. Data flow and interfaces

```
git worktree list --porcelain ─┐
git for-each-ref refs/agent-claims/ ─┼─→ coord_status.py ─→ stdout (human / --json)
gh pr list (cached) ───────────┘   ↑
                                    └─ claim: git hash-object + update-ref CAS
                                    └─ release: update-ref -d
hook_pre_write.py ──→ check refs/agent-claims/* for target worktree/branch/path ─→ block with holder id
```

Claim JSON schema: see `docs/specs/coordination-claims.schema.json` (to be added). Fields: `holder`, `kind`, `id`, `created`, `ttl`, `worktree`, `branch`, `reason`.

## 6. Error handling and failure modes

- **Stale claim (holder crashed):** flagged `expired` in status; any agent may `force_drop` after `2×ttl` with audit broadcast. No silent GC before ttl.
- **Lock contention (AV/indexer):** `update-ref` returns `File exists / Another git process`. Retry 3× with 50ms jitter, then surface `conflict: holder`.
- **Race (two agents claim same id):** exactly 1 wins, 7 get `is at <winner> but expected <old>` → converted to `conflict` with holder id.
- **OpenCode/no-hook harness:** advisory only; `hermes status` still shows claim — visibility without enforcement.
- **Detached/orphan worktree:** status flags `ORPHAN` — suggests `git worktree remove` after confirming `rev-list` 0 unique / parent merged.

## 7. ADR-18 reuse check

Adopt `git` refs + `update-ref` CAS and `git worktree list / merge-base / rev-list / for-each-ref / log -S` (all present, NTFS-verified). Extend `hook_pre_write.py` filter, compose with `shared-hook-surface.json` materializer. Build only `coord_status.py` + `coord_claim.py` thin wrappers and the JSON schema. No new daemon, no new lock impl, no CRDT.

## 8. Testing

- **CAS proof:** committed as `.hermes/plans/cas-proof-report.md` — re-run in CI as `pytest packages/tests/test_agent_claim_cas.py` (8-way Popen, asserted 1 win).
- **Derived view:** golden-output test against fixture `git worktree list --porcelain` sample; divergence math via `rev-list --left-right --count`.
- **Claims:** unit: create/delete/re-claim idempotent/force_drop; integration: two-process `update-ref` race (the CAS proof); hook: `hook_pre_write` blocks writes to claimed path/branch.
- **Room v0 unchanged:** `pytest packages/coordination_room/tests -v` 17 pass.

## 9. Rollout (no code until approved)

1. **M1 — Derived view only (Approach 3):** ship `hermes status`, replace Work Board §0 reads with `status` output. Verify in one operator session.
2. **M2 — Claims as refs:** add `coord_claim.py`, schema, `hook_pre_write` widen, `pre-commit` guard, `status` claim section, GC. Cherry-pick Grok's daemon wiring onto startup scripts in same PR or preceding.
3. **M3 — Retire Work Board §0 as manual surface:** keep file for history, but §0 becomes `Generated from hermes status — do not hand-edit`.

## 10. Open questions for operator

- Claim TTL default: 1h, 4h, or 24h? (proposal: 4h worktree/branch, 1h path).
- Who may `force_drop` non-expired? (proposal: only holder + operator, others wait for expiry).
- Keep room `:7334` as parallel bus or declare `refs/agent-claims` the canonical exclusive table? (proposal: refs canonical for exclusivity; room remains as broadcast/log, not source of truth).

---

*Next step on approval: invoke `writing-plans` to cut `docs/superpowers/plans/2026-09-02-coordination-v1.md` with tasks M1→M3.*
