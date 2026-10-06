# RESULT — PR41 fix-sweep review

**Packet:** [`PACKET.md`](PACKET.md), range `2a55711` … `303b1f9`
**External review:** independent audit, 2026-09-18 —
[`external-audit-2026-09-18/REVIEW.md`](external-audit-2026-09-18/REVIEW.md)
**Audit recommendation:** request changes, on two reproduced findings
**Author response:** `e747a75` — both findings fixed, two residuals fixed, one deferred.
The deferred one was fixed in `65d040e` after the operator challenged how it was framed.
**Second external audit:** 2026-09-27, of `e747a75` … `5a1a2b1` —
[`external-audit-2026-09-27/REVIEW.md`](external-audit-2026-09-27/REVIEW.md).
Request changes on one finding (F3, the pruner fix was incomplete).
**Author response:** `1f42f7d`, `0980176`; see [the second audit](#second-external-audit-2026-09-27).

## Operator decision

**PENDING.** This file records the author's dispositions. It is not the
operator's decision, and the audit states explicitly that it is not one either.
Whether the range is accepted is for the operator to write here. The one item
deferred to the operator has since been fixed; see the dispositions below.

## Dispositions

| Item | Audit | Author disposition |
|---|---|---|
| **F1** — survivor independence read raw model ids, admission read transport-aware routes | P1, reproduced | **Fixed** in `e747a75`. Survivors now go through the same `_independence_route`, keyed on each response's `transport_name`. Regression drives `synthesize()` with the shipped local pool and two failed online voters, and requires `degraded` plus an unsuccessful audit record. |
| **F2** — `hermes_gateway_alive` raising reached one caller of two | P2, reproduced | **Fixed** in `e747a75`. The hook materializer's path translates the refusal to a local `GatewayStateUnknown` and reports `REFUSED`. Tested through the YAML target, the standalone hook materializer, and the parent `materialize()` running the real hook sub-step. |
| Malformed `gateway.pid` shapes (`[]`, `null`, invalid UTF-8) escaped as unhandled types | residual, reproduced | **Fixed** in `e747a75`. All shapes, plus bare strings, numbers and `true`, now raise the handled type. |
| Stale-skill pruner checked a marker's existence, not its owner | residual, dry-run reproduced | **Partially fixed** in `e747a75`, which said "fixed". Removal required the marker's `source_path` to resolve under this workspace. That protected sibling workspaces but not a workspace nested inside another, whose sources all resolve under the outer root. The second audit reproduced the outer workspace pruning a nested one's live projection (F3). **Completed** in `0980176`: markers record the installing workspace, and only an exact match may prune. |
| Survivor helper treats an exception from the independence checker as `None` | residual, pre-existing | **Fixed** in `65d040e`. First deferred as an operator decision, on the grounds that changing it "trades availability for correctness". The operator rejected that framing, and the code supports them. Not aborting a run and not vouching for its roster are separate decisions, and `None` made both at once. The degraded path already returns every response, writes them into the synthesis and stages the draft, so availability was never at stake. A crash now returns `IndependenceUnknown`: the run is degraded, keeps its responses, and says independence is *unknown*, not *failed*. Admission already failed closed on the same crash, so survival now agrees with it. |
| Linux behaviour, installed Antigravity/Hermes header support, real harness invocation, authenticated MCP delivery, daemon readiness | unverified | **Remain unverified.** Nothing in this sweep closes them. |

## Internal review of the response

`e747a75` was reviewed by a subagent before this file was written. It returned
a bare "no issues" rather than the per-area report requested, which is weaker
evidence than a structured clean result, so the question it was most likely to
get wrong was checked directly: whether any skill's source lives outside the
workspace root, which would make this workspace's *own* projections
unprunable under the new ownership rule. Against the real workspace
(`C:/~shit`), all 27 manifest skills resolve under the root; none are outside
and none are unresolvable.

That check surfaced one pre-existing behaviour worth recording, not changed
here: `WORKSPACE_ROOT` is `REPO_ROOT.parent`, so a materializer run from a
worktree under `FLOSS/.worktrees/` resolves against `.worktrees/` rather than
the workspace. It fails loudly — every skill becomes unresolvable before any
pruning — so it cannot cause a silent deletion, but it means the skill
materializer should be run from the main checkout.

### What that review found and did not report

After the above was written, the reviewer's reasoning showed it *had* examined
the PID shapes the prompt listed: zero and negative ids reach `_pid_alive`,
which fails closed, so the write is refused — but the refusal then reads
"gateway PID 0 is live; stop it and re-run", which is false, and for 0 (or 4
on Windows, the System process) directs an operator to kill a system process.
It judged this safe and not introduced by the commit, and so did not report it,
because the prompt asked only for introduced defects. The fault is the prompt.

Fixed in the commit after this file first landed: any id outside
`0 < pid < 2**32` is now reported as an unknown gateway state. **Not fixed:**
a *possible* PID that belongs to some other process — 4 on Windows, or any
reused id from a stale `gateway.pid` — still reads as a live gateway.
Existence is not identity; the daemon side solved that with process-start
tokens, and Hermes' pid file carries none. Recorded as open.

The prompting rule this taught is in [`../README.md`](../README.md).

### The re-review, unfiltered

Re-run on `e747a75` and `26c4ff8` with the three-bucket prompt. The filtered
prompt on the same commit had returned "No issues"; this one returned two
defect-section items, five observations and seven checked-and-clean lines.

| Item | Reviewer | Disposition |
|---|---|---|
| Survivor check treats a crashing checker as independent | defect, pre-existing | Fixed in `65d040e`; see the dispositions table. The reviewer called it a defect, while the author had called it a policy question. The reviewer was right. |
| `projection_owned_by` resolves twice | nit | No action; negligible and safe. |
| The `synthesize()` regression mocks dispatch, so nothing checks a *real* dispatch stamps `transport_name` the way survival reads it | observation | Guard added: every voter shape is dispatched through the real `_dispatch_voter` with only the network stubbed, and its survivor route must equal its admission route. It passes before and after `e747a75` — a guard on the join, not a regression test. |
| The `0 < pid < 2**32` bound is "conservative on Linux" | observation | **Inverted, and a real defect.** The bound was too *permissive* for POSIX: `pid_t` is signed 32-bit, so ids from `2**31` to `2**32-1` reached `os.kill`, which raises `OverflowError` — not an `OSError`, so it escaped every handler above it. Bound tightened to `2**31`; `_pid_alive` now also fails closed on `OverflowError`/`ValueError`. |
| `GatewayStateUnknown` only wraps `SharedSurfaceError`, "safe given the implementation" | observation | This is where the overflow escaped. It was not safe; fixed as above. |
| Pathological `source_path` values | observation | Reviewer concluded safe; agreed. |
| A marker from an earlier version might not be recognised | observation | No action: the constant replaced a literal with the same value and the keys are unchanged, and reinstalling rewrites the marker. |

The real defect this round came out of the observations bucket, and the
reviewer rated it safe. The three-bucket prompt surfaced the lead, but someone
still has to judge it. The filtered prompt would have hidden it entirely.

## Where the audit corrected the packet

The packet made claims the audit tested. Four did not hold as stated:

- **"ruff reports 9 errors."** It is **8** code diagnostics under ruff 0.15.11.
  The packet was wrong. (Carrying the auditor's scripts into this directory adds
  5 more to a repo-wide `ruff check .`, since the repository has no ruff
  config and CI does not lint. Report code-only counts in future packets:
  `ruff check packages scripts tests hooks`.)
- **"`--check` must survive whatever it finds on disk"**, asserted in `303b1f9`.
  False when written: `[]`, `null` and invalid UTF-8 all escaped. Fixed in
  `e747a75`.
- **"1054 passed."** True on the author's machine. The audit's run was
  1051 passed with 3 environment failures (sandboxed `tasklist`, an archive
  without a Git index), each shown to pass outside that environment. Not one
  all-green run in a second environment.
- **A test that proved nothing.** `test_a_corrupt_pid_file_is_reported_not_
  raised_through_materialize` grepped the source for a `try` and an `except`
  around one call site. It could not see the second caller where the defect
  was. Removed in `e747a75` and replaced by the three behavioural tests above.

And two uncertainties it closed in the packet's favour:

- **The Codex `http_headers` key** is confirmed by a Codex CLI readback and the
  official documentation. This closes the key-name question only — not
  authenticated delivery over the network.
- **The PowerShell dispatch** was executed for all 12 combinations of verdict,
  path existence and reservation status, and every one matches the intended
  dispatch. The author's pushback on the double-message finding is supported.

## Test discrimination

The audit ran the 45 new test functions against pre-sweep production code:
36 failed, 9 passed. The 9 largely pin unchanged behaviour and were labelled
as complements. It also noted that several failures only show a new name is
missing, which is weaker evidence than observing the old wrong behaviour.

`e747a75` was red-checked differently from the rest of the sweep: every test
was written and run red **before** its fix. Earlier commits in this range
red-checked with `git stash push` / `pop`, and the stash stack in this
repository is shared with other sessions' worktrees — so those checks could
have popped another session's entry. That practice is retired.

## Second external audit, 2026-09-27

The audit covered `e747a75` … `5a1a2b1`, and separately checked `65d040e` at
`5e52d40`. It asked for changes on one finding.

| Item | Audit | Author disposition |
|---|---|---|
| **F3** — pruner ownership by source ancestry lets an outer workspace prune a nested workspace's live projections, and accepts a relative `source_path: "."` | P2, reproduced through `materialize()` | **Accepted, fixed** in `0980176`. Markers record `workspace_root`, the resolved root of the workspace that installed them, and only an exact match may prune. A relative or missing identity proves nothing. Markers from before the field existed are never removed and are reported as `KEEP` lines rather than drift. That is the conservative legacy policy the audit asked for, made visible because a withdrawn skill lingering silently is the defect the pruner exists for. The test the audit asked for is included: two nested workspaces share one user-scope root and are each refreshed through `materialize()`. **Migration cost:** every installed marker changes, so `--check` reports each projection as drift until the next write refresh. Measured read-only against this workspace's repo-scope targets, that is 83 against 2 before the change. |
| A JSON `gateway.pid` with a 5,000-digit integer escapes as `ValueError` | P3, reproduced | **Fixed** in `1f42f7d`, together with a case found while fixing it: nesting past the recursion limit escapes as `RecursionError`. Both are valid JSON syntax that fails inside `json.loads` with something other than `JSONDecodeError`. |
| PID liveness is not Hermes process identity | open, by inspection | **Agreed; remains open.** |
| F1, F2, the malformed PID shapes, the POSIX overflow repair | closed | Agreed. Real POSIX execution of the overflow path is still unverified. |
| Crashing independence checker | open at `5a1a2b1`, closed at `5e52d40` | Agreed. The audit's probe keeps real dispatch and moves the result from `tier2`, `success=true` to `degraded` and `independence_unknown`. That is stronger evidence than the author's own test, which stubs dispatch. |
| Evidence normalization count in this file | not reproduced | **Corrected** in the Evidence section: two files, not four. |
| Internal reviews are summarized, not carried | limitation | **Carried** in [`internal-reviews.md`](internal-reviews.md), prompts and returns verbatim. |
| Four ownership tests failed only on a missing API or on source text | weaker evidence | The source-text test is gone, replaced by a guard that withdraws a skill through the real `materialize()`. The new nested-workspace test fails on the old code by removing the projection, not by missing a name. |
| Harness invocation, installed header support, authenticated delivery, daemon readiness | unverified | Remain unverified. |

**Where this audit corrected the author.** "Fixed" was claimed for the pruner
residual; it was a sibling-only fix. The evidence paragraph miscounted
normalized files. Both are corrected in place, and each correction quotes what
was claimed before.

### Internal review of this response

Two reviews of `1f42f7d` and `0980176` ran in parallel, both with the
three-bucket prompt. One was a subagent with the repository; the other was a
different model family through OmniRoute, given a condensed diff. Both are in
[`internal-reviews.md`](internal-reviews.md), entries 4 and 5.

| Item | Reviewer | Disposition |
|---|---|---|
| The same narrow `except json.JSONDecodeError` at `load_json`, `load_jsonc`, the skill `load_manifest` and `fetch_agentmemory_status` | subagent, defect | **Accepted, fixed** in `5df214c`. It is the P3 gap at every other loader in the two modules. Two sites had consequences beyond the exception type. `read_roster_summary` catches only `SharedSurfaceError`, so an unreadable roster crashed the doctor. `fetch_agentmemory_status` parses a local service's reply and called `.get` on `[]` or `null`; the reviewer missed that shape. About thirty sites outside these modules have the same handler, several of them parsing model replies. They are out of this PR's scope and filed as a separate task. |
| A run from a worktree records `.worktrees` as its identity, orphaning projections | subagent, defect | **Not a defect.** From a worktree the default root cannot resolve any skill, and the run fails before it writes a marker: `SkillSurfaceError: Skill path is not a directory`, reproduced. With an explicit `--workspace-root`, both sides resolve the same root. The pre-existing quirk is recorded above. |
| The new tests pass an explicit workspace and never exercise the default root | subagent, observation | True; see the row above for why the default path cannot write a mismatched marker. No change. |
| Install deletes the old projection before copying the new one, so a failure mid-copy loses it | OmniRoute, defect | **Real, pre-existing, not fixed here.** The source stays, and the next run restores the projection. It matters more now because the marker migration puts every installed projection through this path once. Recorded. |
| `UnicodeDecodeError` escapes `read_managed_marker` | OmniRoute, defect | **False.** `UnicodeDecodeError` is a `ValueError` subclass; checked. |
| `Path(...).resolve()` raises for paths that do not exist | OmniRoute, defect | **False** on Python 3.6 and later; a non-existent path resolves. Checked. |
| `Path` not imported, `results` undefined, `json.loads` given a non-string | OmniRoute, defects | **False.** The first two were elided from the condensed diff. `raw` comes from `read_text` and is always a `str`. |
| Trailing separators, UNC and junctions could make the writer's and reader's strings differ | OmniRoute, observation; subagent, clean | Both sides go through the same `resolve()` + `normcase`. Equality needs them consistent, not canonical in any wider sense. Neither reviewer found a case where they differ. |
| A marker whose directory entry is a symlink fails `is_file()` and is skipped | OmniRoute, defect | Pre-existing, and it errs toward keeping. No action. |

Six of the eight "defects" from the diff-only review were false or pointed at
code the condensed diff had left out. The one real finding was pre-existing.
The subagent had the repository, and it found the only new class of defect.
A reviewer given a snippet flags what the snippet leaves out.

**Gates after `5df214c`:** 1099 passed, 7 skipped, 1 deselected. Lint over
code paths is unchanged at 8, and spec_gate is OK.

## Evidence

`external-audit-2026-09-18/` carries the review and every evidence file it
links to, content-identical to the auditor's output and checked for
credentials before commit. Not byte-identical: the repository's line-ending
rules normalize **two** of them on commit, the JUnit files
`baseline-tests-final.xml` and `full-suite-final.xml`, from CRLF to LF.
Their content is otherwise unchanged. An earlier version of this paragraph
said four files, three to LF and the PowerShell harness to CRLF. The second
audit could not reproduce that count, and a byte comparison of the committed
blobs against `_audit/` shows two. The originals are unchanged at `_audit/` if
byte equality matters (the header probe used `X-Audit: nonsecret` against
`example.invalid`). Every relative link in `REVIEW.md` resolves inside the
repository.

`external-audit-2026-09-27/` carries the second audit's 46 top-level files
the same way: credential-scanned and content-identical. Three of the files
differ byte-wise once committed: the JUnit files `delta-baseline.xml`,
`focused.xml` and `full-suite.xml`, normalized from CRLF to LF. That count
was checked by comparing each staged blob against `_audit/`. Three links in its `REVIEW.md` point into
`snapshot-5a1a2b1/`, the auditor's export of that commit, which is not
carried. The same files are in Git:
`git show 5a1a2b1:scripts/materialize_shared_skill_surface.py`,
`git show 5a1a2b1:scripts/materialize_shared_agent_surface.py`, and the
environment receipt at
[`external-audit-2026-09-18/environment.json`](external-audit-2026-09-18/environment.json).

Not carried, and still at `_audit/pr41-fix-sweep-20260918/` and
`_audit/pr41-response-20260927/` in the workspace: the exported snapshots
(273 MB each), the dependency cache, the pytest temporary directories, the
probe fixtures and the supplement's source copy. They reproduce the evidence
rather than being it.
