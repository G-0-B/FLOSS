# Delta — `2026-09-02-coordination-v1.md` (implementation plan)

**Target:** `docs/superpowers/plans/2026-09-02-coordination-v1.md`
**Reviewer:** Claude Opus 5, Claude Code session, 2026-09-02
**Companion:** [`DELTA.md`](DELTA.md) — the delta on the design this plan implements.

**The design delta landed well.** D1 (extend `orient_probe.py`), D2/D3 (active+shared filter,
hotspot), D4 (mtime prefilter), D5 (3/6 hook coverage, Codex uncovered), D6 (evidence path), D7
(`--online`), D8 (propagation metric) are all carried into Global Constraints and tasks. This
delta is about execution defects, not direction.

Three findings stop the plan from running at all. Ranked accordingly.

---

## BLOCKING — the plan fails on first execution

### B1. Every commit step uses a path that does not resolve ✅ Verified

All five tasks commit with `git -C C:/~shit/FLOSS add FLOSS/scripts/...`. With `-C` pointing at
the FLOSS repo, pathspecs are relative to that repo, so the `FLOSS/` prefix is one level too deep:

```
$ git -C C:/~shit/FLOSS ls-files --error-unmatch FLOSS/scripts/orient_probe.py
error: pathspec 'FLOSS/scripts/orient_probe.py' did not match any file(s) known to git
$ git -C C:/~shit/FLOSS ls-files --error-unmatch scripts/orient_probe.py
scripts/orient_probe.py
```

**Fix:** drop the `FLOSS/` prefix from every `git add` in Tasks 1–5. Same applies to the `pytest`
paths in the Run lines when they are executed from inside `FLOSS/`. This is the two-repo hazard
again — the same one that made the design's `[V]` citations unresolvable (D6).

### B2. `import scripts.coord_status` will not resolve ✅ Verified

`FLOSS/scripts/__init__.py` does not exist, so `scripts` is not an importable package. The repo's
established pattern is explicit file loading — **19 of 20** test files in `scripts/tests/` use
`importlib.util.spec_from_file_location`; exactly one uses a `scripts.` import.

**Fix:** follow the existing pattern rather than adding `__init__.py` (which changes how every
other script resolves). Replace the test preamble in Tasks 1–4 with:

```python
import importlib.util, sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]

def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, FLOSS_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

cs = load("coord_status_under_test", "scripts/coord_status.py")
```

The same applies to Task 1 Step 5's `from scripts.coord_status import render_sections` inside
`orient_probe.py`. The probe is invoked as a bare script from several working directories; a
package-relative import there is the same failure with a wider blast radius, because it breaks
the probe for every caller, not just the new tests.

### B3. Task 4 tests a function that does not exist and is never created ✅ Verified

The test calls `hp.is_write_allowed(path, agent)`. `hooks/hook_pre_write.py` defines
`is_substantive`, `is_mutating_tool`, `extract_session_id` and `main` — there is no
`is_write_allowed`, and no step in Task 4 says to add one.

**Fix:** Task 4 Step 3 must name the new function, its signature, and where it is called from
inside `main()`. Without that the step is "widen a constant", which does not implement enforcement.

---

## CORRECTNESS — steps that run but produce a wrong or empty result

### C1. `race_claim` does not test CAS, and its assertion is nondeterministic

Each racer reads its own `old` with `rev-parse` **immediately before** its own `update-ref`. Once
the first racer wins, a later racer reads the *new* value as `old` and its update legitimately
succeeds. `assert sum(1 for r in results if r[0]) == 1` therefore fails whenever any racer's read
lands after another's write — which is the normal case under real concurrency.

The property the CAS proof established is that **N writers holding the same expected-old produce
exactly one winner**. That requires capturing `expected_old` once, before launching, and passing
the identical value to all racers.

```python
def race_claim(kind, base_id, ttl=60, racers=8):
    ref = f"refs/agent-claims/{kind}/{base_id}"
    r = _run("rev-parse", "--verify", ref)
    expected = r.stdout.strip() if r.returncode == 0 else ZERO   # captured ONCE
    shas = [claim_json(f"racer-{i}", kind, base_id, ttl) for i in range(racers)]
    procs = [subprocess.Popen(["git", "update-ref", ref, sha, expected],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
             for sha in shas]                                    # all launched before any waits
    return [(p.wait() == 0, p.communicate()[1]) for p in procs]
```

Also remove the dead `one(i)` closure and `f"{base_id}-{i%1}"` — `i % 1` is always `0`.

### C2. `claim()` reads the ref twice and the expected-old line is a no-op

```python
old = _run("rev-parse","--verify",ref).stdout.strip() if _run("rev-parse","--verify",ref).returncode==0 else ZERO
expected = ZERO if old==ZERO else old       # this is `expected = old`
```

Two separate `rev-parse` invocations means the value tested is not the value read. Call once, keep
the result. The `expected` line can go.

### C3. TTL is written and never read — and the self-review says otherwise

`claim_json` stores `ttl`; no task reads it, flags expiry, or implements GC. The design's §4.2
specified expiry flagging in status and `2×ttl` force-drop with an audit entry. The plan's
Self-Review checkbox asserts *"claim TTL/GC in Task 3"* — it is not in Task 3.

**Fix:** either add the GC step to Task 3 (status flags `expired` when `created + ttl < now`;
`force_drop` requires `--force` plus an append to the audit log) or move it to a Task 6 and
correct the Self-Review. A checked box for absent work is worse than an unchecked one.

### C4. D9 has a test but no implementation

`test_abandoned_dirty_flag` asserts `ABANDONED-DIRTY` / `ORPHAN` / `TEMP-DIR` appears in the
output. Task 2 Step 3 implements `_active_branches`, `divergence_rows`, the propagation metric and
a prose note about mtime — no flag classification anywhere. The Self-Review claims
*"abandoned-dirty in Task 2"*.

---

## HAZARD — correct-looking steps with a large blast radius

### H1. Unscoped `git commit -m` in a checkout two agents share

Every task does `git add <paths>` then `git commit -m "..."`, which commits **everything already
staged**, not just the added paths. `C:/~shit/FLOSS` currently carries 54 dirty files belonging to
another agent. This is the hazard documented in
[`../2026-09-01-polyglot-plugin-materializer-spec/HANDOFF.md`](../2026-09-01-polyglot-plugin-materializer-spec/HANDOFF.md)
§5.1, where commit `7bbc725` swept in two unrelated files staged by a different agent.

**Fix:** use the mitigation that handoff prescribes, in every task:

```bash
git -C C:/~shit/FLOSS commit -F- -- scripts/coord_status.py scripts/tests/test_coord_status.py <<'EOF'
feat(coord): ...
EOF
```

The staging area was empty at review time, so this is a race rather than a certainty — which is
exactly why it needs the deterministic form.

### H2. Widening `SUBSTANTIVE_PATH_SEGMENTS` to `/FLOSS/` changes what enters the provenance chain

Task 4 Step 3 proposes `("/packages/","/docs/","/FLOSS/")`. That predicate does not merely decide
whether a claim is *checked* — `is_substantive()` gates whether an edit is **submitted as a Claim
to the durable append-only chain and opens a consensus round**. `/FLOSS/` matches essentially every
path in the workspace. Current value is `("/packages/",)` plus the three canon directories.

**Fix:** do not widen `is_substantive`. Add a separate predicate for claim enforcement — an edit
can be claim-checked without being claim-worthy provenance. If widening is genuinely wanted it is
its own decision with its own blast radius, not a line item inside an enforcement task.

---

## TEST QUALITY — the plan's tests assert against live repository state

### T1. Fixtures were specified in the design and dropped in the plan

Design §8 says *"golden-output test against fixture `git worktree list --porcelain` sample"*. The
plan's tests instead read the real repo. Three consequences:

- `assert len(rows) <= 8` is a claim about this repository on this day. As branches age past the
  7-day window it passes vacuously; as agents add branches it fails for reasons unrelated to the
  code.
- `test_abandoned_dirty_flag` carries its own refutation in a comment — *"may be 0 if cleaned"*. It
  will break shortly: a triage task to clean exactly those four worktrees is already running.
- `assert time.time() - t0 < 1.5` is a wall-clock assertion in CI, and its own docstring says
  `<0.5s` while asserting `1.5`. On a machine with 20 worktrees and antivirus in the path this is
  a flake generator.

**Fix:** drive `divergence_rows()` and the worktree panel from injected git output in tests
(fixture strings for `worktree list --porcelain`, `for-each-ref`, `diff --name-only`), and assert
the *filter behaviour* — naive input of N pairs collapses to M rows, a hotspot appearing in ≥3
pairs emits one row, a fork with disjoint files emits none. Keep at most one live smoke test that
asserts the sections render, not what they contain.

### T2. The CI green set is never run

The repo's green set is:

```
pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
```

New files land in `scripts/tests/`, so they join it automatically — which is precisely why T1
matters. Add a green-set run to each task's verify step, not only the targeted test.

---

## SCOPE

### S1. The design's own decision gate is missing

The design header states *"Decision gate: `flossi0ullk-consensus` System claim required before
implementation (blast radius: Module/System)."* The plan goes from Global Constraints to Task 1
with no such step, and the Execution Handoff offers only subagent-vs-inline.

Either add the gate as Task 0, or record in the plan why it was waived. Silently dropping a gate
the design declared is the failure class the reuse-gate audit was written about.

### S2. Task 5 retires Work Board §0 before the replacement covers it

§0 carries PR topology — numbers, mergeability, review state. Under D7 (correctly adopted) `gh`
stays behind `--online`, so the default derived view has none of it. Replacing §0 with
*"Generated from orient_probe"* therefore loses information the generator does not produce by
default.

**Fix:** make `--online` coverage a precondition of the retirement, or retire only §0's
branch/worktree half and leave the PR table until the online section exists.

---

## Summary

| # | Finding | Severity |
|---|---|---|
| B1 | commit pathspecs do not resolve (all 5 tasks) | blocking |
| B2 | `import scripts.x` unresolvable; 19/20 tests use importlib | blocking |
| B3 | Task 4 tests `is_write_allowed`, which does not exist | blocking |
| C1 | `race_claim` does not test CAS; assertion nondeterministic | correctness |
| C2 | `claim()` double-reads the ref; `expected` line is a no-op | correctness |
| C3 | TTL written, never enforced; Self-Review says otherwise | correctness |
| C4 | D9 has a test and no implementation | correctness |
| H1 | unscoped commit in a checkout with 54 foreign dirty files | hazard |
| H2 | widening `is_substantive` changes what enters the provenance chain | hazard |
| T1 | tests read live repo state; design specified fixtures | test quality |
| T2 | green set never run | test quality |
| S1 | consensus decision gate declared in design, absent from plan | scope |
| S2 | Work Board §0 retired before `--online` covers its PR data | scope |

B1–B3 are one editing pass. C1 and H2 are the two worth slowing down for: the first would ship a
test that proves nothing about the primitive the whole design rests on, and the second would route
every documentation edit into the durable provenance chain.
