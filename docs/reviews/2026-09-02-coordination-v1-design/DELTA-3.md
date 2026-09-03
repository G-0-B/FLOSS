# Delta 3 — design + plan, third pass

**Targets:** `docs/superpowers/specs/2026-09-02-coordination-v1-design.md` and
`docs/superpowers/plans/2026-09-02-coordination-v1.md`
**Reviewer:** Claude Opus 5, Claude Code session, 2026-09-02
**Prior:** [`DELTA.md`](DELTA.md) (design, D1–D9), [`DELTA-PLAN.md`](DELTA-PLAN.md) (plan, B1–B3/C1–C4/H1–H2/T1–T2/S1–S2),
[`DELTA-PLAN-2.md`](DELTA-PLAN-2.md) (B10–B12/C5–C10, another reviewer).
Checked against DELTA-PLAN-2 first; **no overlap** — neither finding below appears there.

## Verified fixed — stop re-reviewing these

Confirmed on disk, not taken on trust:

- **D6 done.** All four evidence reports are now in this directory and committed. §0's citations
  resolve.
- **Task 0 is real.** `submit_claim(proposer, proposal_type, summary, body, blast_radius,
  evidence=None) -> str` matches `packages/metacoordinator_mcp/server.py:54` exactly. Evidence key
  `ref` is correct — `packages/metacoordinator_mcp/tools.py:67` reads `e["type"]` and `e["ref"]`.
  The cited commit `a43f59cd` exists.
- **`--online` genuinely absent** from `orient_probe.py` argparse (`--query`, `--root`, `--limit`,
  `--json`). The plan is right to add it rather than assume it.
- **`race_claim` now tests CAS** — `expected_old` captured once, all `Popen` launched before any
  wait. C1 closed.
- **`is_substantive` untouched, separate `is_claim_blocked`.** H2 closed.
- **Fixtures replaced live-state assertions**, wall-clock budget assert gone. T1 closed.
- Leaving the Self-Review boxes deliberately unchecked pending implementer verification is the
  right call and worth keeping as a habit.

---

## N1 — Claim ids are not legal git ref names, and enforcement fails open ❌ Blocked

**Neither document validates or sanitizes `id`.** `refs/agent-claims/path/<id>` uses the
repo-relative path verbatim. Git's ref-name grammar rejects several shapes that occur in ordinary
repositories. Verified with `git check-ref-format`:

| candidate id | `refs/agent-claims/path/<id>` |
|---|---|
| `docs/specs/spec-registry.json` | LEGAL |
| `scripts/foo.lock` | **ILLEGAL** — no component may end `.lock` |
| `docs/a b.md` | **ILLEGAL** — no spaces |
| `docs/x..y.md` | **ILLEGAL** — no `..` |
| `C:/other/foo.py` | **ILLEGAL** — no `:` |

Two consequences, and the second is the serious one:

1. **`claim()` reports a conflict that is not a conflict.** An illegal id makes `update-ref` fail;
   the code returns `(False, "conflict")`, indistinguishable from another holder. The agent
   concludes someone else owns the path and steps aside forever.
2. **`is_claim_blocked()` fails open.** It runs `rev-parse --verify` on the illegal ref, gets a
   non-zero return, and returns `(False, "")` — *not claimed* — so the write is **allowed**. A file
   whose name contains a space cannot be protected, and nothing anywhere says so. That is the one
   failure direction an exclusivity mechanism must not have.

The `C:/other/foo.py` row is reachable today: `normalize_repo_rel` falls back to
`Path(path).as_posix().lstrip("/")` for paths outside the repo, which on Windows yields a drive
letter and a colon.

**Fix.** Add an id-normalization function that produces a legal ref component, used by *both*
`coord_claim.py` and `hook_pre_write.py` — one function, not two (see N3). Percent-encode or
hex-encode the illegal set rather than dropping characters, so the mapping stays injective and two
different paths cannot collide onto one claim. Then:

- `claim()` must distinguish `E_ILLEGAL_ID` from `conflict`.
- `is_claim_blocked()` must **fail closed or raise** when the ref name is malformed — never return
  "not claimed" because it could not ask the question.
- Test with `git check-ref-format` over the table above; it is the authority and it is already
  installed.

## N2 — The plan builds on a branch that is missing a landed fix to the file Task 4 edits ❌ Blocked

Global Constraints branch the work off `feat/coordination-room`. That branch does not have the
path-containment fix that landed on the PR41 lineage:

```
feat/coordination-room                 hooks/hook_pre_write.py  def _repo_relative: 0
reconcile/pr38-salvage-20260817        hooks/hook_pre_write.py  def _repo_relative: 1
feat/coordination-room-rebased         hooks/hook_pre_write.py  def _repo_relative: 1
```

On `feat/coordination-room`, `is_substantive()` still normalizes the **raw** spelling:

```python
norm = "/" + path_str.replace("\\", "/").lstrip("/").lower()
```

while containment is checked on the resolved path — the exact disagreement the reconcile-line fix
removed (`packages/tests/../prod.py` resolves to production code and is skipped for containing
`/tests/`).

So the plan would add claim enforcement to a file whose sibling predicate is a known-superseded
version, and then that work has to be reconciled with the fixed version later. This is the
stranded-fix failure the design exists to prevent, sitting underneath the design's own
implementation plan.

**Fix.** Base the implementation worktree on `feat/coordination-room-rebased`, which carries both
`_repo_relative` **and** Grok's `:7334` wiring that Task 5 sets out to cherry-pick — removing that
cherry-pick from Task 5 entirely. If `feat/coordination-room` must be the base, say why, and add a
task to bring `_repo_relative` across first.

## N3 — A third normalizer for one concept, differing in case ⚠️ Specified

After N2 there are three implementations of "path → repo-relative id":

| where | behaviour |
|---|---|
| `_repo_relative` (reconcile, -rebased) | resolves, **lowercases**, returns `None` outside repo |
| inline in `is_substantive` (coordination-room) | raw spelling, **lowercases** |
| `normalize_repo_rel` (this plan) | resolves, **does not lowercase**, returns a fallback string outside repo |

Claim ids would therefore be case-sensitive while the substantive check is case-insensitive. On
Windows, `Docs/Specs/X.json` and `docs/specs/x.json` are the same file and two different claims.
This is the two-readers-of-one-structure shape recorded as FM-8 in
`docs/research/2026-08-25-provenance-failure-mode-register.md`, which has recurred in this repo
often enough to have a name.

**Fix.** One function, imported by both call sites, with the case rule stated once. If ids must be
case-preserving for readability, then the comparison must be case-folded explicitly and tested.

## N4 — `subprocess` is not imported in `hook_pre_write.py` ❌ Blocked

Task 4's `is_claim_blocked` calls `subprocess.run(...)`. The module imports are `json`, `os`,
`sys`, `traceback`, `pathlib.Path` — no `subprocess`. `NameError` on first invocation, inside a
hook, where the failure surfaces as a broken write path rather than a stack trace the author sees.

## N5 — `claim()` never consults `is_expired`, so a crashed holder blocks indefinitely ⚠️ Specified

`is_expired` and `force_drop` exist, and nothing calls them on the claim path. A holder that dies
leaves a claim that `claim()` refuses forever; recovery requires an agent to notice, call
`is_expired`, call `force_drop`, then re-`claim` — a four-step sequence written down nowhere.

The design's §4.2 says expired claims are "auto-prunable by holder or by any agent after `2×ttl`".
The plan implements the capability and not the flow.

**Fix.** Either have `claim()` attempt reclaim when the existing claim is past `2×ttl` (logging to
the audit trail as `force_drop` already does), or document the reclaim sequence in the design and
add it to the status output as the suggested action next to an `expired` flag. Silent
auto-expiry before `2×ttl` stays forbidden — that part is right.

## N6 — Two smaller inconsistencies

- **`SHARED-INDEX` is specified and not implemented.** Design §4.1.1 lists four worktree flags;
  `classify_worktree` implements three (`ABANDONED-DIRTY`, `ORPHAN`, `TEMP-DIR`) and the test
  covers those three. `SHARED-INDEX` — dirty checkout with another agent active, the flag that
  describes the primary checkout right now — is nowhere.
- **CAS test path disagrees between the documents.** Design §8 says
  `packages/tests/test_agent_claim_cas.py`; plan Task 3 creates
  `scripts/tests/test_coord_claim_cas.py`. Pick one; the plan's location is the one inside the
  green set.

## N7 — `scripts/orient_probe.py` is dirty in the primary checkout right now ⚠️ Coordination

`git status --porcelain scripts/orient_probe.py` → ` M`. The plan correctly says not to commit
that. But an isolated worktree checks out the **committed** version, so those in-flight edits are
invisible to Task 1 — which modifies the same file. The conflict is deferred, not avoided.

**Fix.** Before Task 1, either land or discard the primary's probe edits, or claim the file. This
is a good first real exercise of the mechanism being built: `coord_claim` on
`scripts/orient_probe.py` would have surfaced it.

---

## Summary

| # | Finding | Severity |
|---|---|---|
| N1 | claim ids can be illegal ref names; `is_claim_blocked` then fails **open** | blocking |
| N2 | base branch lacks `_repo_relative`; Task 4 edits that file | blocking |
| N3 | third path normalizer, differing in case | correctness |
| N4 | `subprocess` not imported in `hook_pre_write.py` | blocking |
| N5 | `claim()` ignores expiry; crashed holder blocks indefinitely | correctness |
| N6 | `SHARED-INDEX` unimplemented; CAS test path differs between docs | consistency |
| N7 | probe dirty in primary; isolated worktree defers the conflict | coordination |

N1 is the one to fix before any of it ships: an exclusivity primitive that answers "not claimed"
when it could not form the question is worse than no primitive, because the status view will
report the path as free.
