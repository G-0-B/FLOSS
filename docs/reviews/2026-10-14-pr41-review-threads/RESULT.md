# RESULT: PR41 review threads, 2026-10-14

**Source:** the Codex review threads on PR #41 that were open and live on
2026-10-14, relayed by the desktop app's Auto-fix monitor, plus the internal
review of the first set of fixes
([`internal-reviews.md`](internal-reviews.md)).
**Order of work:** spec, then the tests the spec defines, then code, as the
project's spec-driven rule requires. The first pass inverted it (test, then code,
no spec) and was corrected before anything was committed or pushed; the history
shows the corrected order.

| Step | Commits |
|---|---|
| Clauses written | `332bc6e`, backfill `1c25856` |
| Tests, red on the old code | `c02c735` |
| Code | `6809053` |
| Clauses amended from the internal review | `a631f4a`, `1d99fd8` |
| Tests for the amendments | `327cad3` |
| Code for the amendments | `f4c2d5f` |

Clauses: [`docs/specs/local-surface-invariants.spec.md`](../../specs/local-surface-invariants.spec.md)
(LSI-A1..A6, LSI-B1), the synthesizer spec section 2.10 (SYN-D1..D4) and the
review protocol (MRP-K1).

## The review threads

| Thread | Finding | Disposition |
|---|---|---|
| `synthesizer.py`, truncation | `DEGENERATE_TRUNCATION_RATIO` was declared and never applied | **Fixed**, SYN-D2 |
| `review_independence.py`, Kish | a mean phi of exactly zero returned NaN | **Fixed**, MRP-K1 |
| `materialize_shared_hook_surface.py`, event map | two events mapped to one native name, the second silently replacing the first | **Fixed**, LSI-A2 |
| `materialize_shared_agent_surface.py`, repo scope | a `scope: "repo"` target could resolve outside the workspace | **Fixed**, LSI-A1 |
| `mcp_daemon.py`, reclaim | the two snapshots were taken outside the claim guard | **Fixed**, LSI-B1 |
| `materialize_shared_skill_surface.py`, pruner | a harness write between the digest and the removal was deleted | **Fixed**, LSI-A4. Moved aside, verified there, then deleted or put back |
| `synthesizer.py`, mixed-mode transport route | the survivor check passed bare model tags | **Already fixed** in `e747a75`; `test_survivor_independence.py` covers it |
| `hook_post_write.py`, Hermes `patch` verification (two threads) | no deterministic verification of V4A patch payloads | **Not changed.** Answered in the threads on 2026-08-25 and 2026-08-31 as left open on purpose: a V4A parser that is subtly wrong writes a false `VERIFIED` into a permanent chain |
| five threads already resolved on GitHub | | none needed |

## The internal review of the first fixes

One review, `332bc6e..6809053`: 1 red, 19 yellow, 1 open question, plus
observations. Each is dispositioned below.

| # | Finding | Disposition |
|---|---|---|
| 1 | whitespace-only response flagged as truncated at 0 chars | **Fixed**, SYN-D4 |
| 2 | reclaim test never reached the removals, and two failure branches were untested | **Fixed.** `test_reclaim_removes_both_records_while_holding_the_guard`, and OSError and ImportError cases |
| 3 | LSI-A1 tests used absolute paths only | **Fixed.** Relative, `~` and environment-variable forms |
| 4 | agent surface wrote mirrors, context pack, gemini, opencode and vibe before the codex and hermes checks | **Fixed.** One pre-pass resolves and checks every target first |
| 5 | those same targets had no containment check at all | **Fixed.** Pre-existing. Treated as repo scope (LSI-A1 b). The real agent manifest passes |
| 6 | an empty event list raised a collision | **Fixed**, LSI-A2 |
| 7 | the hook scope check returned when it could not resolve | **Fixed.** It refuses |
| 8 | the hook materializer wrote the registry before checking | **Fixed.** Pre-pass |
| 9 | skill `name` used as a path component without validation | **Fixed**, LSI-A5. All 27 real skills pass |
| 10 | a stranded aside of a listed skill was reported as withdrawn and a fresh copy installed beside it | **Fixed**, LSI-A4 d. Put back before install; `--check` reports it and moves nothing |
| 11 | an unreadable renamed copy was called "changed", and a refused rename on update was called `EVOLVED` | **Fixed.** Changed, in use, unreadable and stuck are distinct |
| 12 | an undeletable aside aborted the run, and a non-OSError skipped the restore | **Fixed**, LSI-A4 e |
| 13 | the docstring said the window is a rename and a read | **Fixed.** It is narrowed, not closed; stated in the docstring and LSI-A4 f |
| 14 | the pruner's re-read marker was not re-checked for ownership | **Fixed** |
| 15 | `--check` reports drift a write run may keep because the rename is blocked | **Not changed.** `--check` cannot know without renaming, which is a write. Documented in LSI-A4 f |
| 16 | **red:** the UPDATE comment said history holds the removed copy, and an uncommitted source revision is lost | **Comment corrected; severity not accepted.** Baseline equality proves no harness changed the copy, which is what the preservation rule is about. A revision the operator replaced in the source without committing was replaced by the operator, as with any editor save. LSI-A3 now says so. Behavior is unchanged and predates this work |
| 17 | cleanup after a failed install could delete a harness's file | **Fixed in part**, LSI-A6. After a failed marker publish the directory is removed only if every file equals the shared base. After a failed copy it is still removed whole, because a failed write can leave a truncated file that is the install's own. An existing test showed the first draft was too broad |
| 18 | the update-comparison test passes on the old code | **Not changed.** The commit message labelled it a guard. The old doctored-digest version could not model taking the copy aside, so it was replaced |
| 19 | the stranded-copy test is red only on a missing constant | **Acknowledged.** It characterizes behavior that already existed |
| 20 | restore failure, update plus blocked rename, check/dry-run never renaming, stranded listed skill untested | **Fixed.** Tests added; the first two are guards on behavior already written |
| 21 | a float mean of -2.8e-17 refused | **Fixed**, MRP-K1 tolerance of 1e-12 |
| ❓ | which scanners skip dot-prefixed skill directories | **Answered.** Only Codex's, read in `rust-v0.128.0`. The others were not read; the docstring and LSI-A4 g now say so |

Observations, recorded and not acted on: the worktree layout puts the
containment boundary one level above a worktree; the aside name adds 39
characters to every path; `payload_digests` reads whole files; there is no lock
between materializer runs, and locking is on a separate branch
(`feat/materializer-file-locking`); an even-count median takes the upper middle;
the guard waits 5 seconds by default; `_reclaim_claim_guarded` is unguarded if
called directly; a refusal aborts the whole step; and the generated vibe
launcher writes to a machine-wide trusted-folders file, which is generated
output and outside LSI-A1 as written.

## Test discrimination

- `c02c735` against the code before `6809053`: 13 failed, 312 passed, 1
  skipped. The weak reds and the one guard are named in the commit message.
- `327cad3` against `6809053`: 23 failed, 335 passed, 1 skipped. A count in that
  commit's first message said 26 and was corrected to 23 after recounting.
- One test passed for the wrong reason and was fixed before it was committed: the
  opencode case stopped on a missing file before it could write.

## Validation

After `f4c2d5f` on the author's machine: **1179 passed, 8 skipped, 1
deselected**. spec_gate OK (108 registered, one non-fatal stale entry). ruff
over the code paths reports the same 8 diagnostics as before. Native Linux
(Ubuntu under WSL, Python 3.12.3): 112 passed, 9 skipped across the skill, hook
and review-independence tests. The real skill, agent and hook manifests were
checked read-only against the new name and containment rules and pass.

## Operator decision

**PENDING**, as in the earlier rounds. This file records the author's
dispositions only.
