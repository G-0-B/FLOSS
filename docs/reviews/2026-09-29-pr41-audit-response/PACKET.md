# External review handoff: FLOSSI0ULLK PR #41, third round

**Repository:** `G-0-B/FLOSS`
**Branch:** `reconcile/pr38-salvage-20260817`
**Range under review:** `5a1a2b1` … `42e4d05` (six commits: four code, two docs)
**Base:** `5a1a2b1`, the endpoint of the second external audit
**Status:** committed, **not pushed**. Nothing in this range is on the remote.
The worktree is `C:\~shit\FLOSS\.worktrees\pr41-salvage`.

## Where this sits

This is the third review of one fix sweep. The first two rounds' records live
in [`../2026-09-05-pr41-fix-sweep/`](../2026-09-05-pr41-fix-sweep/):

- `PACKET.md`: the first handoff (`2a55711` … `303b1f9`).
- `external-audit-2026-09-18/`: the first audit, which found F1 and F2.
- `external-audit-2026-09-27/`: the second audit, of `e747a75` … `5a1a2b1`,
  which found F3 and a P3.
- `RESULT.md`: the author's dispositions for every item in both audits. The
  operator decision is still **PENDING**.
- `internal-reviews.md`: every internal review of the responses, with prompt
  and return verbatim. Entries 3 to 5 cover the code in this range.

This range is the response to the second audit, plus one fix it reported as
already verified in a focused supplement (`65d040e`).

## What I want from you

Report in three buckets, and fill all three:

1. **Defects.** Anything wrong, whether this range introduced it or it was
   already there.
2. **Observations.** Things below that bar: risks, untested cases, anything
   misleading even if safe. When you judge something safe, say why, so the
   judgement can be checked.
3. **Checked and clean.** Each area you examined and found nothing in, with
   the evidence.

A bare "no issues" is not a result. The priorities below say where to look
first; they are not a limit on what to report. A reviewer on this PR once
found a real problem and did not report it, because the prompt asked only for
defects the commit introduced. The story is in `../README.md`, under
"Prompting a reviewer".

Where I would look first:

1. **Identity semantics for skill ownership (`0980176`).** Ownership moved from
   *where a projection's source lives* to *which workspace recorded itself as
   installing it*, compared as resolved, `normcase`d strings. Can the writer
   and the reader of one workspace disagree? Can two workspaces agree? Is the
   legacy policy right: markers without the field are never removed and are
   reported as `KEEP`, not as drift?
2. **The migration it forces.** Every installed marker changes, so every
   projection is rewritten once. Install deletes the old directory before
   copying the new one. That ordering predates this range, but this range puts
   every projection through it. How bad is an interrupted run?
3. **A three-state return (`65d040e`).** `_survivor_independence_problem`
   now returns `None` (independent), a string (not independent) or
   `IndependenceUnknown`, a `str` subclass for "the check could not run".
   Check every consumer. Does anything lose the distinction, or treat
   "degraded" in a way that throws away the responses the fix exists to keep?
4. **Widened exception classes (`1f42f7d`, `5df214c`).** Several handlers went
   from `JSONDecodeError` to `(ValueError, RecursionError)`. Does anything
   inside those `try` blocks raise `ValueError` for a reason that should *not*
   be reported as unreadable input?
5. **Tests that cannot fail.** The table below says which tests failed on the
   unfixed code and which are guards. Check that it is honest.

## Files

| File | Contents |
|---|---|
| `PACKET.md` | this document |
| `source-changes.patch` | production changes only, one section per code commit |
| `test-changes.patch` | test changes only, same commits |
| `<reviewer>/` or `<reviewer>.md` | your output and evidence, as it arrives |
| `RESULT.md` | dispositions and the operator's decision, written after your review |

Read the source patch first and decide what the tests *should* assert. Then
read the test patch and see whether they do.

## Commits, in order

| Commit | Kind | Subject |
|---|---|---|
| `65d040e` | code | a survivor check that cannot run no longer vouches for the roster |
| `5e52d40` | docs | the deferred survivor-check item was a trade that did not exist |
| `1f42f7d` | code | two gateway.pid shapes that are valid JSON still escaped as unhandled |
| `0980176` | code | skill ownership is who installed a projection, not where its source lives |
| `5df214c` | code | the gateway.pid JSON gap was at every loader in both materializers |
| `42e4d05` | docs | the second external audit, its evidence, and the response |

**Provenance.** All six were written in one session, authored as `kalisam`
with a Claude co-author line. No other author or session committed in this
range. A separate session is now working on the same class of bug elsewhere in
the repository (see "Out of scope" below). It works in its own worktree and
has not committed to this branch.

The docs commits are not in the patches. `5e52d40` corrects a disposition and
adds FM-18 to `docs/research/2026-08-31-review-loop-session-learnings.md`.
`42e4d05` carries the second audit's evidence and adds `internal-reviews.md`.
Review them if a claim in them matters to you.

## What the changes do

**Survivor independence (`65d040e`),** `packages/reasoning_ensemble/synthesizer.py`.
After voters run, the synthesizer checks the survivors again against the
independence bar of three provider surfaces and four model families. When the
checker itself raised, the helper returned `None`, the value a *passing* check
returns. The run then reported a consensus tier over a roster nobody had
checked. The second audit reproduced this with real dispatch: `tier2`,
`success=true`. Now a crash returns `IndependenceUnknown`. The run is
`degraded` and keeps every response. The writeup and the audit record say
independence is *unknown* (`independence_unknown: …`), not that the roster
*failed* (`roster_not_independent: …`). Admission already failed closed on
the same crash, so the two now agree. I deferred this one at first as an
"availability versus correctness" trade. The operator pointed out that the
degraded path already keeps the responses, so there was no trade.

**`gateway.pid` parsing (`1f42f7d`),** `scripts/materialize_shared_agent_surface.py`.
Two inputs are valid JSON syntax but still fail inside `json.loads` with
something other than `JSONDecodeError`: an integer longer than CPython's
4,300-digit limit, which raises `ValueError`, and nesting past the recursion
limit, which raises `RecursionError`. Both escaped as unhandled types and
aborted the hook materializer before its later targets. The handler now
catches both, and the message says "not readable JSON".

**Skill projection ownership (`0980176`),** `scripts/materialize_shared_skill_surface.py`.
User-scope install roots such as `~/.codex/skills` are shared by every
checkout on the machine. The pruner removes projections whose skill left this
workspace's manifest, so it has to know which projections are this
workspace's. It decided by source ancestry: ours if the marker's `source_path`
resolved under our root. That separates sibling workspaces but not nested
ones. The second audit showed an outer workspace selecting a nested
workspace's live projection for removal. Ancestry also accepted a relative
`source_path: "."` whenever the current directory was inside the root.

Markers now record `workspace_root`, the resolved root of the installing
workspace, and only an exact match may prune. A relative or missing identity
proves nothing. Markers written before the field existed are never removed.
Each one produces a `KEEP` line: a withdrawn skill lingering in silence is the
defect the pruner exists for, and a legacy marker may be this workspace's own.
A `KEEP` is not drift, because this workspace cannot resolve it without a
human.

**The same JSON gap at every other loader (`5df214c`),** both materializers.
The internal review of `1f42f7d` found the same narrow handler in `load_json`,
`load_jsonc`, the skill `load_manifest` and `fetch_agentmemory_status`. Two of
these had consequences beyond the exception type. `read_roster_summary`
catches only `SharedSurfaceError`, so an unreadable roster crashed the doctor
report. `fetch_agentmemory_status` parses a local service's HTTP reply and
called `.get` on `[]` or `null`; the reviewer missed that shape. A bad reply
now yields `error:<type>-reply`.

## Tests, and what each one proves

Every test marked red was written first and run against the unfixed code. The
failure named is what it raised there.

| Commit | Test | Unfixed code |
|---|---|---|
| `65d040e` | `test_a_check_that_cannot_run_does_not_abort_the_deliberation` (rewritten) | red: returned `None` |
| `65d040e` | `test_a_run_whose_check_crashed_is_degraded_and_keeps_its_responses` | red: tier `unmeasured` |
| `65d040e` | `test_a_crashed_check_reports_independence_unknown_not_failed` | red: no `error` logged, the success path |
| `1f42f7d` | two new cases in `test_every_malformed_gateway_pid_shape_is_a_handled_refusal` | red: `ValueError`, `RecursionError` |
| `1f42f7d` | `test_a_corrupt_hermes_pid_file_refuses_the_write` | message match changed from "not valid JSON" to "not readable JSON"; not new coverage |
| `0980176` | `test_refreshing_either_of_two_nested_workspaces_keeps_the_others_projections` | red: the nested projection was removed |
| `0980176` | `test_a_relative_workspace_identity_proves_nothing` | red: the relative marker was claimed |
| `0980176` | `test_a_marker_without_workspace_identity_is_kept_and_reported` | red: the legacy marker was pruned |
| `0980176` | `test_a_marker_this_materializer_writes_is_one_it_recognises_as_owned` (extended) | red, but first on the new `serialize_marker` signature, the weak kind of red. Its new assertion, that the installing workspace's *parent* does not own the projection, was checked separately against the old functions: the old code says the parent owns it. |
| `0980176` | `test_a_workspace_still_prunes_its_own_withdrawn_projection` | **guard**: passes before and after. It replaces a test that read `materialize()`'s source for the text `owner_root=workspace_root`. |
| `5df214c` | `test_every_json_loader_reports_unreadable_input_as_its_own_error` (6 cases) | red: `UnicodeDecodeError`, `ValueError`, `RecursionError` |
| `5df214c` | `test_an_unreadable_roster_does_not_crash_the_doctor_summary` | red: `UnicodeDecodeError` |
| `5df214c` | `test_a_malformed_agentmemory_reply_is_reported_not_raised` (5 cases) | red: `AttributeError` ×2, then the three above |
| `5df214c` | `test_an_unreadable_manifest_is_a_skill_surface_error` (3 cases) | red: same three |

One test was deleted: `test_the_materializer_passes_its_own_workspace_as_owner`.
It read source text, and both audits noted that kind of test proves nothing.

## How to verify

From the worktree, with `C:\Python313\python.exe` and `PYTHONPATH` cleared:

    python -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
    python scripts/spec_gate.py --check
    python -m ruff check packages scripts tests hooks

Expected on the author's machine: **1099 passed, 7 skipped, 1 deselected**.
spec_gate should report OK with one non-fatal stale entry. ruff should report
8 diagnostics, all predating this range. A repo-wide `ruff check .` counts
more, because it includes auditor scripts carried into `docs/reviews/`.

Both audits hit the same environment failures, and you may too. Two tests call
Windows `tasklist`, which returns "Access denied" in a sandbox. One test needs
a Git index, which an exported archive does not have. Both audits showed these
pass outside those conditions.

**If you reuse the second audit's probe:** `audit_probes.py` calls
`serialize_marker(entry, 'audit')` with two arguments. The function now takes a
third, `workspace_root`, so the probe raises `TypeError` before reaching the
ownership check. Pass the workspace as the third argument.

## What I could not verify

- **Real user-scope roots.** The migration was measured read-only against this
  workspace's repo-scope targets only: 83 projections reported as drift, against
  2 before the change. User-scope roots (`~/.codex/skills`, the Hermes skills
  directory) were not refreshed or counted. I don't know how many legacy
  markers from *other* workspaces are on this machine, or how noisy the `KEEP`
  lines will be.
- **A moved workspace.** Markers record the old path, so after a move they
  belong to nobody. They are never pruned and, because they do carry a
  `workspace_root`, they are silent rather than reported as `KEEP`. That is
  the conservative direction, but an operator would not see them. Judge
  whether it should say something.
- **Junctions, symlinks, 8.3 short names and UNC paths.** Both sides go
  through the same `resolve()` and `normcase`, and two paths to one directory
  resolve as one workspace. I believe that is correct, but it has not been
  tried on a real junction, a short-name path or a UNC path.
- **POSIX.** Everything ran on Windows. `normcase` is a no-op on POSIX, so a
  case-insensitive macOS volume could see two spellings of one root as two
  workspaces. Not tested. The POSIX `OverflowError` path from the previous
  round is still exercised only by simulation.
- **The install ordering.** Delete-then-copy is pre-existing and not fixed.
  The source survives, and rerunning restores the projection.
- **Reviewer diversity.** Two internal reviews: a subagent with the repository,
  and one model through OmniRoute given a condensed diff. `mistral-small`
  was rate-limited and the `groq` qwen model was missing from the live catalog.
  The diff-only reviewer mostly produced false positives from what the snippet
  left out.

## What the internal review already found

In full in `../2026-09-05-pr41-fix-sweep/internal-reviews.md`, entries 4 and
5, with each item's disposition in that directory's `RESULT.md`. In brief:

- **Accepted:** the narrow JSON handler at four more loaders. That review
  produced `5df214c`.
- **Rejected, so you can overrule it:** the subagent called it a defect that a
  run from a worktree records `.worktrees` as its identity, orphaning
  projections. I hold that it cannot happen. From a worktree the default root
  resolves no skills, and the run fails before it writes any marker
  (reproduced: `SkillSurfaceError: Skill path is not a directory`). With an
  explicit `--workspace-root`, both sides resolve the same root. If you find a
  path that writes a marker from a worktree without `--workspace-root`, the
  rejection is wrong.
- **Recorded, not fixed:** delete-then-copy on install (above).
- **False:** six of the diff-only reviewer's eight "defects". For example, it
  said `UnicodeDecodeError` escapes a `ValueError` handler, but it is a
  subclass; and it said `resolve()` raises on missing paths, which it does not
  on Python 3.6 and later.

## Out of scope, and why

About thirty other call sites in the repository catch only `JSONDecodeError`.
Several of them parse model replies (`packages/metacoordinator_mcp/voters.py`)
or router output. They are outside the files this PR touches, so they are
filed as a separate task, which another session is working on now. If you
think any of them belongs in this PR, say which and why.

## Still open from earlier rounds

- **Hermes PID identity.** A PID that exists is not proof the gateway owns
  it. PID 4 on Windows, or any reused id in a stale `gateway.pid`, still reads
  as a live gateway.
- **Unverified runtime behaviour:** harness invocation, installed header
  support, authenticated MCP delivery, daemon readiness.
- **The operator decision** in the previous `RESULT.md`.

## Conventions you may not expect

- Comments are long and explain **why a previous version was wrong**. That is
  house style, not padding.
- Truth-status discipline: no claim is marked verified without a traceable
  artifact. A comment asserting something you cannot check is worth raising.
- Fail-closed beats degrade-silently, but refusing a claim is not the same as
  refusing the run. `65d040e` keeps the output and withholds the verdict, and
  that distinction is deliberate.
