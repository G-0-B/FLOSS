# Delta-plan-2 — residual defects after `a43f59c`

**Target:** `docs/superpowers/plans/2026-09-02-coordination-v1.md` @ `a43f59c`
**Companion:** `DELTA.md` (design D1–D9), `DELTA-PLAN.md` (B1–B3, C1–C4, H1–H2, T1–T2, S1–S2)
**Reviewer:** independent `/review` 2026-09-03 — verdict **do not execute**. “Plan is now runnable” at `a43f59c` was false.

Verified live 2026-09-03 on `feat/coordination-room` @ `a43f59c`:
- 55 dirty porcelain rows; `scripts/orient_probe.py` +41/−11 vs HEAD
- no `scripts/coord_status.py`, `coord_claim.py`, `scripts/__init__.py`
- `git commit -F- -- untracked.txt` → `pathspec did not match any file(s) known to git` (B10)
- no `packages/metacoordinator_mcp/client.py`; real API is `server.submit_claim(proposer, proposal_type, summary, body, blast_radius, evidence=...)`
- `hook_pre_write.finish()` always returns 0; docstring “Exit 0 without blocking”
- probe argparse: `--query/--root/--limit/--json`; **no `--online`**
- `.agent-surface` is `C:/~shit/.agent-surface`, not under FLOSS
- `scripts/start_mcp_daemons.ps1` has 0 hits for `7334`

---

## B10 — `git commit -F- -- <paths>` cannot create files

H1 dropped `git add`. New files in Tasks 1 and 3 are untracked; `commit -- path` only works for already-indexed paths.

**Fix (every task that creates files):**

```bash
git -C C:/~shit/FLOSS add -- scripts/coord_status.py scripts/tests/test_coord_status.py
git -C C:/~shit/FLOSS commit -F- -- scripts/coord_status.py scripts/tests/test_coord_status.py <<'EOF'
feat(coord): ...
EOF
```

`add --` then `commit -F- --` still scopes the commit to those paths (does not sweep other staged files **if those paths are the only ones passed to commit**). Do **not** run bare `git commit -m` after a broad `git add`.

## B11 — H1 still sweeps foreign edits on already-dirty paths

`scripts/orient_probe.py` is dirty (+41/−11) in the shared checkout. Task 1 `commit -- scripts/orient_probe.py` would take whoever else’s probe hunks.

**Fix:** execute M1–M5 from an **isolated worktree** created from `feat/coordination-room` (`git worktree add .worktrees/coord-v1 -b feat/coord-v1 feat/coordination-room`). Do not implement in `C:/~shit/FLOSS` while it has 55 foreign dirty files. Probe wiring lands only in that worktree.

## B12 — Task 0 cannot run

No `client.py`. `...` is a writing-plans placeholder. “or note waiver” lets an implementer skip the gate.

**Fix:** Task 0 uses `packages.metacoordinator_mcp.server.submit_claim` **or** MCP `submit_claim` with `evidence` array of `{type, ref}` (not `path`/`url`). System/SpecChange fail-closed without provenance (`E_GOVERNED_PROVENANCE_REQUIRED`). Operator must supply `consent_ref` **or** a written waiver in this directory. No silent skip.

## C5 — `claim()` last-writer-wins

Reading current SHA then `update-ref new current` **replaces** the holder. Exclusive create must use `old=ZERO`. Same-holder refresh CAS-updates with current SHA. Other holder → fail, do not steal.

## C6 — TTL / `force_drop` vs 2×ttl

Status flags `expired` at `age > ttl`. Non-force `force_drop` only after `age >= 2×ttl`. `force=True` always allowed + audit. Parse `created` as UTC (`datetime.strptime(..., "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)`), never `time.mktime` on a Z timestamp.

## C7 — D9 fixture vs classifier

Design: `ABANDONED-DIRTY` = dirty AND no git activity **30d**. `ORPHAN` = detached AND parent merged (not merely dirty). 18-day `_codex_pr38_cleanup` is **not** abandoned-dirty. Tests must match those thresholds.

## C8 — Task 2 implementation was comments

`render_sections_fixture`, live `divergence_rows()`, mtime prefilter, propagation metric must be real functions. Hotspot collapse emits one HOTSPOT row **for that file** and keeps other non-hotspot pairs — does not replace the whole panel.

## C9 — Task 4 will not block writes

- One `normalize_repo_rel(path) -> posix` used by claim, hook, and tests.
- `git -C REPO_ROOT` (hook cwd is the agent’s).
- Call `is_claim_blocked` from `main()` as real code, not a comment.
- Deny contract: `finish()` is the **allow** path (exit 0). Deny writes Claude/Hermes JSON `permissionDecision: deny` (or equivalent) to stdout when `--stdout-json`, and `main()` returns **2**. Empty `{}` + exit 0 is not a deny.
- Do not swallow `coord_status` import errors if the file exists.

## C10 — audit log in the wrong tree

`Path(__file__).parents[1] / ".agent-surface/..."` → `FLOSS/.agent-surface` (does not exist). Shared surface is `C:/~shit/.agent-surface` = `FLOSS` parent. Use workspace root (`REPO_ROOT.parent`) or `COORDINATION_ROOM` intake-mouth pin.

## Design drift (patch in same commit)

- §4.3 still says widen `SUBSTANTIVE_PATH_SEGMENTS` — contradicts H2 / plan. Replace with separate claim predicate.
- §9 M3 still `Generated from hermes status` — D1 forbade that alias. Use `orient_probe.py`.
- §8 still requires live `45+ → 4` assertion — T1 forbade live counts. Fixtures only.
- Header still “awaiting writing-plans”; plan exists.

## Execution gate

Do **not** start Task 1–5 until: this delta applied to plan+design, operator LGTM, Task 0 APPROVED or written waiver, isolated worktree.
