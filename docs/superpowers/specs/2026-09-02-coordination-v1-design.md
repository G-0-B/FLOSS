# Coordination v1 — Derived Status + Git-REF Claims — Design

> Status: Draft — DELTA D1–D9 + DELTA-PLAN + DELTA-PLAN-2 applied; DELTA-3 adjudicated (N1–N5/N7 accepted, N6 CAS-path accepted, `SHARED-INDEX` rejected after live falsification). **❌ Implementation blocked:** ADR-12 has no ratified `consent_ref.decision_action_hash` anchor, so the required System claim cannot be validly submitted. Plan: `docs/superpowers/plans/2026-09-02-coordination-v1.md`.
> Scope: Architectural. Restructures how agents coordinate; changes an interface others depend on.
> Decision gate: `flossi0ullk-consensus` System claim required before implementation (blast radius: Module/System).
> ADR-18: adopt → extend → compose → build checked — see §7.
> Delta: `FLOSS/docs/reviews/2026-09-02-coordination-v1-design/DELTA.md` (Opus 5) — nine changes, all applied below.

## 0. Evidence envelope (why this shape)

**CWD:** `C:/~shit/FLOSS` · **Probed:** `orient_probe.py` + 4 parallel verifications 2026-09-02
**Facts [V]:**
- Coordination room `packages/coordination_room/` — 17 tests pass 2026-08-30, binds `127.0.0.1:7334`, was `ConnectionRefused` the window it existed. On `feat/coordination-room` HEAD, `start_mcp_daemons.ps1` has **0** `7334` hits. On `feat/coordination-room-rebased` (implementation base, N2) Grok already wired `:7334`.
- `git update-ref refs/agent-claims/<name> <new> <old>` CAS on Windows 11/NTFS/git 2.54.0 — 8-way Popen race → 1 win / 7 blocked, `rc=128 is at <winner> but expected <old>`, lock `*.lock` held only during write, no stale locks. Report: `docs/reviews/2026-09-02-coordination-v1-design/cas-proof-report.md`.
- Work Board §0 clean ladder falsified: `reconcile/pr38-salvage` ↔ `feat/preservation-spine` mutually non-ancestral (`merge-base 31bcad0`, exit 1 both ways), `coord-room` ↔ `coord-room-rebased` (`08619f0`, 16 vs 46 past base). Ladder intentionally broken §0.1c. Report: `docs/reviews/2026-09-02-coordination-v1-design/ancestor-matrix-report.md`.
- Grok `coord-room-rebased@2460c55` vs `coord-room@45b3f26` — `packages/coordination_room/` diff 0 lines (identical v0). Grok added `hooks/grok_session_register.py`, `hooks/grok_pretool_st.py`, `:7334` wiring via `Start-Daemon` + `Resolve-ServerPid` + `COORDINATION_ROOM_LOG` pin. Divergence 53 files +7172/-2757 is parallel substrate evolution, not room conflict. Report: `docs/reviews/2026-09-02-coordination-v1-design/grok-coord-room-audit.md`.
- Derived view sketch: 6 sections making 4 scoped failures seconds-visible, zero stored state. Report: `docs/reviews/2026-09-02-coordination-v1-design/derived-status-sketch.md`.
**Falsifier:** If a successful `git update-ref` CAS can be shown non-linearizable on NTFS, or if `coordination_room` startup liveness is proven supervised, re-evaluate claim-primitive choice.

---

## 1. Problem and non-goals

**Problem:** Agents duplicate work and miss existing fixes because coordination state is maintained manually (Work Board §0, room claims for one checkout's file paths) or lives behind a daemon that wasn't running. All failures measured happened outside the room's claim unit — different worktrees/branches, no path collision.

**Non-goals (v1):** No CRDT/MELD merge, no A2A task handshake, no controller that writes files, no new daemon to supervise. No pycrdt.

## 2. Reframe — derive, don't maintain

Split state along derivability:

- **Derivable (never write, recompute on demand):** branch topology, ahead/behind, divergence, worktree list+HEADs, claim refs list, open PRs, "fix already exists elsewhere" (`git log --all -S`). All four scoped failures are in this set.
- **Not derivable (must write):** intent — "I am about to take this worktree/branch/path." Exclusive half only.

Work Board §0 is a typed snapshot — stale by design. The room needed `:7334` up — wasn't. `.git/refs/` cannot be down and is already shared across all 20 worktrees via common dir.

## 3. Approaches considered

| # | Approach | Trade |
|---|----------|-------|
| **1** | **Derived status + claims as git refs** — status computed, claims are `refs/agent-claims/*` via `git update-ref <new> <old>` CAS. Enforcement via existing `hook_pre_write.py`. No daemon. | **Recommended.** Needs hook materialization + TTL/GC. Reuses git, adopt-before-build. |
| 2 | Extend room, actually run it | Fixes room scope but not its liveness; needs supervision work first. |
| 3 | Convention only (derived view, no claims) | Smallest artifact; catches failures as visibility but doesn't stop worktree borrow. Graceful fallback of 1. |

## 4. Recommended architecture — Approach 1 (delta-applied)

### 4.1 Derived status via `orient_probe.py` extension (D1, D4, D7, D8)

Do **not** build a new entry point. `scripts/orient_probe.py` already emits a deterministic markdown packet (`## Section` + pipe tables), is stdlib-only, no-network, no-mutation, 322 lines, and is **the mandatory Step 0 of the `flossi0ullk-orient` skill** — agents already run it. Adoption, not design, killed the room and Work Board §0. A new command must earn adoption from zero; the probe has it. On the adopt → extend ladder this is **extend**, not build.

**Shape:** `scripts/coord_status.py` exists as a module with `render_sections() -> str` returning markdown sections, imported by `scripts/orient_probe.py` and rendered as additional sections. `coord_status.py` remains runnable standalone for `--json` / `--online`. `orient_probe.py` stays under ~500 lines; no mutation, no network by default. Do not name the universal view after one harness — no `hermes status` as primary alias.

**Propagation metric (D8):** first line of status output, free to compute alongside the panels:

```
## Coordination                    10 commits/24h, 10 on exactly 1 of 8 active branches
```

Of 10 commits landed across all refs in last 24h, 10 exist on exactly 1 of 8 active branches — zero propagation. Computed from `for-each-ref` + `rev-list`.

**Sections and sources (all pure-git unless flagged `--online`):**

1. **Worktree table — exceptions, not inventory (D4).** Source `git worktree list --porcelain` + `<common-dir>/worktrees/<name>/index` mtime pre-filter + `git status --porcelain` only for recent/dirty worktrees (D4 cost fix — status across 20 worktrees dominated runtime). Presentation: active + anomalous rows only; rest collapsed to `13 more — idle, clean`. Flags: `TEMP-DIR` (worktree under temp), `ABANDONED-DIRTY` (uncommitted, no activity 30d), `ORPHAN` (detached/merged). **DELTA-3's `SHARED-INDEX` request is rejected after live falsification:** pure Git shows dirty state but cannot identify “another agent active in this same checkout,” and Git normally prevents the same branch in two worktrees. Do not fabricate it from a caller-supplied boolean; surface active holders separately from claim refs once identity exists.
2. **Branch containment matrix** — `git branch --contains HEAD` + `merge-base --is-ancestor`.
3. **Divergence alerts — active + shared-file filter (D2) with hotspot collapse (D3).** Naive filter (any two branches with unique commits both ways) produced 45+ rows, truncated. Filter: (a) **active branches only** — commit in last 7 days (28 → 8), (b) **both sides must have modified the same file** — `git diff --name-only <merge-base> A` intersect `git diff --name-only <merge-base> B`; empty intersection = disjoint fork, no stranding risk. Result on 2026-09-02: 45+ → 4 rows. Verified rediscovery: `chore/digestion-actions` ↔ `reconcile/pr38-salvage-20260817`, shared files `scripts/start_mcp_daemons.ps1`, `scripts/stop_mcp_daemons.ps1`, `docs/agent-memory/project/commitment-built-witness-improvised.md`. Hotspot collapse (D3): when one file (e.g. `docs/specs/spec-registry.json` on 5 of 8 pairs) appears on both sides of ≥3 pairs, emit once as `HOTSPOT` row.
4. **Claim refs** — `git for-each-ref refs/agent-claims/ --format='%(refname:short) %(objectname:short) %(committerdate:iso)'` + reflog parse for holder.
5. **Open PRs — offline by default (D7).** `gh pr list --repo G-0-B/FLOSS` only with `--online` flag. `orient_probe.py` promises "No mutation. No network. Stdlib only." — a cached-60s `gh` call is reasonable alone but violates the probe's contract when silently imported. Pure-git panels in 1–4,6 need no network. With `--online`: 5s timeout, cached 60s flagged `[cached]`.
6. **Already-fixed elsewhere** — last 20 `fix:` tokens → `git log --all -S <token> --oneline`, highlight branches missing the fix.

**Why cannot go stale:** zero stored file. Every cell recomputed. Worst case is slow `gh` (behind flag, offline default). No manual row to forget.

### 4.2 Claim primitive — git refs as intent

- **Namespace:** `refs/agent-claims/<kind>/<encoded-id>` where `kind ∈ {worktree, branch, path}`. **`encoded-id` is not the raw path.** One implementation in `scripts/coord_claim.py`, imported by `hook_pre_write.py` (N1/N3):
  - `repo_relative_path(path, root)` resolves repository paths (relative inputs are repo-root-relative for the claim CLI), returns lowercase POSIX relative path **without a leading slash**, and returns `None` outside that worktree. The user-scope hook first resolves the edited path's actual FLOSS worktree by comparing Git common-dir identity, resolves relative tool paths against `Path.cwd()`, then delegates with that target root; `is_substantive` prepends `/` locally for segment checks. This avoids anchoring every sibling-worktree edit to the hook script's primary checkout.
  - `encode_claim_id(kind, raw_id, root)` percent-encodes every UTF-8 byte except ASCII alphanumeric, `_`, and `-`, component by component. Path and worktree ids are filesystem paths: lowercase on Windows (NTFS case-insensitive). Branch ids preserve exact case (git refs are case-sensitive: `Feature/X` != `feature/x`). **Do not use Unicode `casefold()`** on any kind: it collapses distinct names such as `Straße` and `Strasse`. **Do not use `urllib.parse.quote(..., safe="")`**: RFC-unreserved `.` remains unescaped, leaving `.lock` and `..` illegal. Encoding `.` as `%2E`, `%` as `%25`, spaces as `%20`, and `:` as `%3A` keeps the encoded map injective within each kind's canonicalization. Path claims require `repo_relative_path != None`; branch/worktree ids canonicalize then encode.
- **Authority note:** every operation validates the finished ref using `git check-ref-format` — necessary but NOT sufficient on Windows. Raw `scripts/foo.lock`, `docs/a b.md`, `docs/x..y.md`, `C:/other/foo.py` are illegal as ref names (verified 2026-09-03); outside-repo path claim → no id (fail closed). Reserved device basenames (`CON`/`PRN`/`AUX`/`NUL`/`COM1-9`/`LPT1-9`, case-insensitive, with or without extension) pass check-ref-format yet fail `update-ref` with `Invalid argument`, so `claim_ref` rejects them explicitly (M1).
- **Illegal id vs conflict:** `claim()` returns `(False, "E_ILLEGAL_ID")` when `check-ref-format` fails or `_repo_relative` is `None`. Never report that as `conflict`. `is_claim_blocked()` **fails closed** (treat as blocked / raise) if it cannot form a legal ref — never `(False, "")` meaning "not claimed".
- **Holder identity (N8, decision required):** the hook payload and current manifest provide no stable `agent_id`; the prior plan referenced an undefined variable. Proposed contract: a unique, opaque `FLOSS_AGENT_ID` inherited by one harness process/session; `coord_claim.py` defaults `holder` from it, and the in-repo hook denies with `E_AGENT_ID_MISSING` when absent. Static harness labels (`hermes`, `codex`) and worktree-only identity are rejected as defaults because concurrent agents can share both. Task 0 must record approval or an alternative identity contract before M2/Task 4; do not infer identity from a generic session id without a claim-side way to obtain the same value.
- **Value:** blob SHA of JSON `{"holder": "<agent_id>", "kind": "...", "raw_id": "...", "encoded_id": "...", "created": "iso", "ttl": 3600, "branch": "<current HEAD>", "worktree": "<path>"}` — written via `git hash-object -w`.
- **CAS:** `git update-ref refs/agent-claims/<kind>/<encoded-id> <new_sha> <expected_old>` where `expected_old` is `000...0` for create, current `rev-parse` for same-holder refresh, or delete via `update-ref -d <ref> <old>`. Exactly 1/8 wins on NTFS — proven (§0).
- **Release:** `git update-ref -d ...` only by holder (enforced in hook, not git ACL). `force_drop(kind, raw_id, actor, force=False, expected_sha=None)` distinguishes the acting identity from the blob's `old_holder`; it requires explicit `force=True` from an authorized actor (`actor == old_holder` or Task-0-approved force list; unauthorized `force=True` is denied and audited) or age ≥ `2×ttl`, and always deletes with the read/explicit expected SHA.
- **TTL/GC:** Status flags `expired` (age > ttl). Silent auto-expiry before `2×ttl` is forbidden. **`claim()` reclaim flow (N5):** if a different holder exists and age ≥ `2×ttl`, `claim()` `force_drop`s (audit) then creates — do not require a four-step notice/expire/drop/reclaim. Before `2×ttl`, steal still fails. Status output next to `expired` still suggests `force_drop`.
- **Lock:** `.git/refs/agent-claims/<name>.lock` — git handles. No hand-rolled lock. Single `update-ref` per claim, retry 3× 50ms jitter on `File exists` (AV/indexer).

### 4.3 Enforcement — reuse existing surfaces (D5 corrected)

- **Coverage today:** **3 of 6 harnesses wire `hook_pre_write`/`hook_post_write` today** — verified 2026-09-02 by grepping each materialized config:

| config | wired |
|---|---|
| `.gemini/settings.json` | yes |
| `C:/Users/kalis/.claude/settings.json` (user scope) | yes |
| `C:/Users/kalis/AppData/Local/hermes/config.yaml` | yes |
| `.claude/settings.json` (repo) | no |
| `.codex/config.toml` (repo + `C:/Users/kalis/.codex/config.toml`) | no |
| `opencode.jsonc` | no |

The count is not the point — **Codex is uncovered**, and Codex is the most active agent in this repo (majority of PR41's 248 threads, four `codex/*` branches). Any enforcement routed through harness hooks misses the main contender. Materialization closes Claude, leaves Codex and OpenCode outside. This strengthens §9's M1-first sequencing: the derived view reaches every agent that can shell `git` (all six); enforcement reaches at best four. Reach, not liveness, is the constraint driving order.

- **Primary fix:** materialize `shared-hook-surface.json` for Claude/Codex/Hermes `PreToolUse`. Add a **separate** `is_claim_blocked(path, agent_id, repo_root)` predicate with `repo_root` REQUIRED (no default — a defaulted hook-checkout root silently checks the wrong worktree) — do **not** widen `is_substantive()` / `SUBSTANTIVE_PATH_SEGMENTS` (those gate provenance-chain submission, not exclusivity). `main()` resolves the target worktree FIRST via `resolve_floss_worktree(path, REPO_ROOT)`: None → allow (outside every FLOSS checkout; this replaces the old `_is_inside_repo` path-containment guard on the claim path, which fail-opened sibling worktrees outside the checkout); crash → deny 2. Then holder identity (missing → deny 2 in-repo) → worktree claim → branch claim (skip verified detached HEAD) → path claim → substantive/provenance gate. Unparseable claim blobs deny with `E_CLAIM_DATA`, never "not claimed". Any malformed ref, Git execution error, or unexpected claim exception denies. Deny must be a real harness block (`permissionDecision: deny` + non-zero exit); `finish()` remains the allow path (exit 0).
- **Secondary:** git hook `pre-commit`/`pre-push` checking `refs/agent-claims/*` for current HEAD worktree/branch — installed via `shared-hook-surface` (today `core.hooksPath` unset, hooks only `*.sample`).
- **Out of scope:** OpenCode has no `PreToolUse` — advisory-only until wired.

### 4.4 What Grok built and how we keep it

- Keep identical `packages/coordination_room/` (0-line diff) as v0 reference/routing option — not retired, but not required for liveness. Its 17 tests remain green.
- Inherit Grok's `:7334` wiring from the `feat/coordination-room-rebased` base (verify-only): carry `Start-Daemon`/`Resolve-ServerPid`/`$skipped`/`settle` with the existing `$PSScriptRoot`/`$FLOSS_PYTHON`/`venv` portability fixes — don't overwrite, do not cherry-pick a second copy. Pin `COORDINATION_ROOM_LOG` to workspace intake mouth so worktree launches share one bus.
- Take Grok's `grok_pretool_st.py` (smart-tree reminder) as-is; `grok_session_register.py` is Grok-specific — keep behind Grok harness only.

## 5. Data flow and interfaces

```
git worktree list --porcelain ─┐
git for-each-ref refs/agent-claims/ ─┼─→ scripts/coord_status.py:render_sections() ─┐
rev-list / merge-base (D2/D3) ───────┘   ↑                                    ├─→ orient_probe.py stdout
gh pr list --online (D7, optional) ─────┘   claim: git hash-object + update-ref CAS
                                            release: update-ref -d
hook_pre_write.py ──→ check refs/agent-claims/* for target worktree/branch/path ─→ block with holder id
```

Claim JSON schema: see `docs/specs/coordination-claims.schema.json` (to be added). Required fields: `holder`, `kind`, `raw_id`, `encoded_id`, `created`, `ttl`; optional context: `worktree`, `branch`, `reason`. There is no ambiguous standalone `id` field.

## 6. Error handling and failure modes

- **Stale claim (holder crashed):** flagged `expired` in status; any agent may `force_drop` after `2×ttl` with audit broadcast. `force=True` before `2×ttl` requires the current holder or a name on the Task-0-approved force list (read at runtime from `FLOSS_CLAIM_FORCE_LIST`, launcher-populated from the decision doc, documented in `RUNTIME_SURFACES.md`); anyone else is denied and audited. No silent GC before ttl.
- **Corrupt claim blob:** `claim()` returns `(False, "E_CLAIM_DATA")`; `force_drop` returns `False` and audits the denial with the `E_CLAIM_DATA` code — never "not claimed", never steal-able. (`force_drop` keeps its `-> bool` channel; the code travels in the audit record.)
- **Lock contention (AV/indexer):** `update-ref` returns `File exists / Another git process`. Retry 3× with 50ms jitter, then surface `conflict: holder`.
- **Race (two agents claim same id):** exactly 1 wins, 7 get `is at <winner> but expected <old>` → `conflict` with holder id.
- **OpenCode/no-hook harness:** advisory only; status still shows claim — visibility without enforcement.
- **Detached/orphan worktree:** status flags `ORPHAN` — suggests `git worktree remove` after confirming `rev-list` 0 unique / parent merged.
- **Abandoned-dirty (D9):** uncommitted work rotting in untracked worktree — flag `ABANDONED-DIRTY` when dirty + no git activity 30d. Found 2026-09-02: `_codex_pr38_cleanup` (1 file, 18d), `_codex_pr38_salvage_design` (30 files, 48d), `_pr25fix` (17 files, 80d), `quirky-mcnulty` (4 files, 181d). None known before reported. Triage is separate task; design change is that status flags the class so it cannot accumulate silently again.

## 7. ADR-18 reuse check

Adopt `git` refs + `update-ref` CAS and `git worktree list / merge-base / rev-list / for-each-ref / log -S` (all present, NTFS-verified). Extend `scripts/orient_probe.py` with `coord_status.render_sections()` (D1). Add a separate claim predicate on `hook_pre_write.py` without widening `is_substantive`. Compose with `shared-hook-surface.json` materializer. Build only `scripts/coord_status.py` + `scripts/coord_claim.py` wrappers and the JSON schema. No new daemon, no new lock impl, no CRDT.

## 8. Testing

- **CAS proof:** committed as `docs/reviews/2026-09-02-coordination-v1-design/cas-proof-report.md` — re-run in CI as `pytest scripts/tests/test_coord_claim_cas.py` (8-way Popen, asserted 1 win; green-set path). Also `git check-ref-format` over the N1 table (legal vs `.lock` / space / `..` / `:`).
- **Derived view:** golden-output / fixture-driven tests (injected `worktree list --porcelain`, `for-each-ref`, `diff --name-only`). Assert filter *behaviour*: disjoint fork emits none; hotspot in ≥3 pairs emits one HOTSPOT row for that file and keeps other pairs; naive N pairs collapse to M. Do **not** assert live-repo row counts (45→4 is historical evidence in DELTA.md, not a CI assertion). One live smoke: sections render, not what they contain. No wall-clock budget asserts.
- **Claims:** unit: create/delete/re-claim idempotent/force_drop, path/branch/worktree encoding legality and collision cases, stale-reclaimer vs same-holder refresh CAS; integration: two-process `update-ref` race; hook: real stdin fixtures prove worktree → branch → path enforcement, outside-repo allow, missing-identity deny, lookup-exception deny.
- **Room v0 unchanged:** `pytest packages/coordination_room/tests -v` 17 pass.

## 9. Rollout (no code until approved)

1. **M1 — Derived view only (Approach 3):** ship `scripts/coord_status.py` as `render_sections()` imported by `orient_probe.py`; wire `--online` separately. Replace Work Board §0 reads with probe output. Verify in one operator session. Reach (all six harnesses) drives this first, not liveness (D5).
2. **M2 — Claims as refs:** add `coord_claim.py`, schema, `encode_claim_id` + fail-closed `is_claim_blocked` (not `is_substantive` widen), `pre-commit` guard, status claim section, TTL/GC with reclaim on `claim()` after `2×ttl`. Implementation worktree bases on `feat/coordination-room-rebased` (has `_repo_relative` and `:7334`); do not cherry-pick Grok daemon wiring in M3.
3. **M3 — Retire Work Board §0 as manual surface:** keep file for history. Replace **branch/worktree half only** with `Generated from orient_probe.py + coord_status.render_sections() — do not hand-edit`. Keep the PR table until `--online` exists and is verified (D7/S2). No `hermes status` alias.

## 10. Open questions for operator

- Claim-holder identity contract: approve unique per-session `FLOSS_AGENT_ID`, or specify an alternative that both `coord_claim.py` and the hook can derive identically? Static harness/worktree labels are insufficient for agents sharing a checkout. **This blocks M2/Task 4, not M1.**
- Claim TTL default: 1h, 4h, or 24h? (proposal: 4h worktree/branch, 1h path).
- Who may `force_drop` non-expired? (proposal: only holder + operator, others wait for expiry).
- Keep room `:7334` as parallel bus or declare `refs/agent-claims` the canonical exclusive table? (proposal: refs canonical for exclusivity; room remains as broadcast/log, not source of truth).

---

*Next step: resolve and ratify ADR-12's consent action-hash anchor, then create a validated provenance packet and run Task 0. No M1–M3 implementation before an APPROVED governed consensus decision.*
