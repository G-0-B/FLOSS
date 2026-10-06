# External review handoff: FLOSSI0ULLK PR #41, fourth round

**Repository:** `G-0-B/FLOSS`
**Branch:** `reconcile/pr38-salvage-20260817`
**Range under review:** `42e4d05` … `0472ce1` (five commits: two code, three docs)
**Base:** `42e4d05`, the endpoint of the third external audit
**Status:** committed, **not pushed**. The worktree is
`C:\~shit\FLOSS\.worktrees\pr41-salvage`.

## Where this sits

This is the fourth review of one fix sweep. The earlier records:

- [`../2026-09-05-pr41-fix-sweep/`](../2026-09-05-pr41-fix-sweep/): rounds 1
  and 2. It holds the first packet, both earlier audits, the dispositions and
  `internal-reviews.md`.
- [`../2026-09-29-pr41-audit-response/`](../2026-09-29-pr41-audit-response/):
  round 3. It holds the third packet, the third audit
  (`external-audit-2026-09-29/`), `RESULT.md` with a disposition for each of
  its items, `internal-reviews.md`, `posix-f4-check/` and
  `o2-skill-inventory/`.

This range is the response to the third audit, plus a decision the operator
made on its O2. Both operator decisions, one per `RESULT.md`, are still
**PENDING** for range acceptance.

## What I want from you

Report in three buckets, and fill all three:

1. **Defects.** Anything wrong, whether this range introduced it or it was
   already there.
2. **Observations.** Things below that bar. When you judge something safe,
   say why, so the judgement can be checked.
3. **Checked and clean.** Each area examined, with the evidence.

A bare "no issues" is not a result. The priorities below are where to look
first, not a limit on what to report.

1. **F4's fix (`9a23477`).** `recorded_workspace()` now catches `ValueError`
   as well as `OSError` when resolving a marker's recorded root. Is there any
   other way a hostile but parseable marker can raise out of
   `projection_owned_by` or the pruner, on POSIX or Windows? The tests mirror
   POSIX `realpath` by patching `os.path.realpath`. Running
   `scripts/tests/test_shared_skill_surface_scope.py` natively on Linux would
   check that mirror against the real thing.
2. **The KEEP reporting (`9a23477`, `69c4cbd`).** Unusable identities, and
   identities naming a root that `os.path.exists` cannot see, produce `KEEP`
   lines. They are never drift and never removed. Is the classification right?
   Is the "cannot be found" wording safe for an unmounted drive or a network
   path?
3. **The marker-only rewrite (`9a23477`).** When the installed files equal the
   source apart from the marker, only the marker is rewritten. Equality is
   decided on text read in universal-newline mode. Could it treat two
   different payloads as the same?
4. **The operator's decision, and the design it needs.** See the last two
   sections. It is the largest open question, and critique of the proposed
   direction is wanted *before* it is built.
5. **Tests that cannot fail.** The table below says what each test raised on
   the unfixed code. Check that it is honest.

## Files

| File | Contents |
|---|---|
| `PACKET.md` | this document |
| `source-changes.patch` | production changes only, one section per code commit |
| `test-changes.patch` | test changes only, same commits |
| `<reviewer>/` or `<reviewer>.md` | your output and evidence, as it arrives |
| `RESULT.md` | dispositions and the operator's decision, after your review |

Read the source patch first and decide what the tests *should* assert, then
read the test patch.

## Commits, in order

| Commit | Kind | Subject |
|---|---|---|
| `17948dc` | docs | the third-round handoff you reviewed last round |
| `9a23477` | code | a marker the OS cannot resolve aborted the refresh on POSIX |
| `69c4cbd` | code | a missing workspace is "cannot be found", not "no longer exists" |
| `1227781` | docs | the third audit, its evidence, and the response |
| `0472ce1` | docs | the operator's O2 decision: preserve evolved skills, propagate upstream |

**Provenance.** All five were written in one session, authored as `kalisam`
with a Claude co-author line. Two other sessions are working on problems this
review surfaced. One is widening narrow `JSONDecodeError` handlers across the
repository; the other is hardening `os.replace` in
`packages/activity_log/provenance.py`, the third audit's O3. Each works in its
own worktree, and neither has committed to this branch.

## What the changes do

All code changes are in `scripts/materialize_shared_skill_surface.py`.

**F4 (`9a23477`).** Resolving a marker's recorded `workspace_root` caught only
`OSError`. On POSIX an absolute path containing a NUL raises `ValueError` from
`resolve()`, so one malformed marker aborted the pruner and the materializer
around it, `--check` included. Resolution now lives in `recorded_workspace()`,
which catches both and returns `None` for any identity that cannot be used.
Ownership is still an exact match, not ancestry.

**O4 (`9a23477`).** Only a *missing* identity used to produce a `KEEP` line.
Now any unusable identity does, whether missing, relative, empty, not a string
or unresolvable. So does one naming a workspace root that cannot be found.
Both kinds are kept, reported, and not counted as drift. A live foreign
workspace's projection stays silent.

**O1 (`9a23477`).** Adding `workspace_root` changed every installed marker, and
install replaced a projection by deleting it and copying the source back. The
migration therefore put every unchanged skill through a window where an
interrupted run left it missing. When only the marker differs, only the marker
is rewritten now. Delete-then-copy for real content changes is unchanged.

**Wording (`69c4cbd`).** The `KEEP` line for a root that cannot be found said
the workspace "no longer exists" and invited deleting the skill by hand. But
`os.path.exists` is also False for an unmounted drive or an unreachable network
path. The line now says "cannot be found from here (moved, deleted, or not
mounted)", and to remove the skill only once that workspace is known to be
gone.

## Tests, and what each one proves

Every test here was written first and run against the unfixed code.

| Commit | Test | Unfixed code |
|---|---|---|
| `9a23477` | `test_an_identity_the_os_cannot_resolve_is_unknown_not_a_crash` | red: `ValueError: embedded null byte` |
| `9a23477` | `test_a_marker_the_os_cannot_resolve_does_not_stop_the_refresh`, through `materialize()`; the bad marker sorts before a withdrawn projection that must still be pruned | red: `ValueError` |
| `9a23477` | `test_a_marker_with_an_unusable_identity_is_kept_and_reported` (relative, number, empty, null) | red ×4: no `KEEP` line |
| `9a23477` | `test_a_marker_from_a_workspace_that_no_longer_exists_is_kept_and_reported` | red: no `KEEP` line |
| `9a23477` | `test_a_marker_only_change_never_takes_the_installed_skill_away`; `remove_path` and `copytree` are patched to fail if called | red: the skill was taken down |
| `9a23477` | `test_a_projection_owned_by_another_workspace_is_never_removed` (changed) | Now creates the other workspace, since a missing one is reported, and asserts silence outright. Before, it asserted only that nothing was removed. A tightening, not new coverage. |
| `69c4cbd` | the moved-workspace test, now requiring the new wording and rejecting the old invitation | red: old wording |

The F4 tests patch `os.path.realpath` to raise on a NUL, as POSIX does. On
Python 3.12 `Path.resolve()` calls `self._flavour.realpath`, where `_flavour`
is the `os.path` module looked up at call time; on 3.13 it calls
`os.path.realpath` directly. Either way the patch is reached. Separately,
[`../2026-09-29-pr41-audit-response/posix-f4-check/`](../2026-09-29-pr41-audit-response/posix-f4-check/)
runs the fixture natively under WSL Ubuntu / Python 3.12.3 with no patch.
Before the fix it raises `ValueError: embedded null byte` from
`posixpath.realpath`. After it, the run reports `KEEP` then `DRIFT`.

## How to verify

From the worktree, with `C:\Python313\python.exe` and `PYTHONPATH` cleared:

    python -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
    python scripts/spec_gate.py --check
    python -m ruff check packages scripts tests hooks

Expected on the author's machine: **1107 passed, 7 skipped, 1 deselected**.
spec_gate should be OK with one non-fatal stale entry, and ruff should report 8
pre-existing diagnostics. The known environment failures still apply: two
`tasklist` tests fail in a sandbox, and one test needs a Git index. The third
audit's O3 (`os.replace`, `PermissionError`) did not reproduce in 12 local
runs. If you hit it, record it; it is being worked on separately.

## What I could not verify, or noticed and did not fix

- **POSIX beyond this one fixture.** The native check covers F4's fixture
  only. `normcase` is a no-op on POSIX, so on a case-insensitive macOS volume
  two spellings of one root would read as two workspaces. Not tested.
- **UNC and 8.3 short-name aliases.** Not tested. The third audit showed that
  a real junction resolves to one owner.
- **`os.path.exists` on slow network paths.** It may block rather than return
  False. The pruner calls it once per foreign marker.
- **A binary file inside a managed projection crashes install.** Install reads
  every installed file with `read_text(encoding="utf-8")`. If a harness adds a
  binary file (an image, say) to a managed skill, the refresh raises
  `UnicodeDecodeError`, `--check` included. Reproduced; it predates this PR.
  The source snapshot has the same text-only assumption. Not fixed here: the
  proposed design below replaces text comparison with byte digests.
- **Delete-then-copy for real content changes** is unchanged. After the
  operator's decision below, it is not just a rollout risk. It is the
  mechanism that would overwrite an evolved skill.
- **Reviewer diversity.** Only one internal review ran, a subagent. OmniRoute's
  session had expired. The review and its dispositions are in the round-3
  `internal-reviews.md` and `RESULT.md`.

## The operator's decision on O2

The third audit's O2 was about two workspaces installing the same skill name
into a shared root. The operator did not choose among the three options
offered. They set the requirement instead:

> we do NOT want to overwrite skills if they have changed, i know hermes
> especially evolves its skills with learnings from use, and codex has done so
> as well. What we actually want to end up with is to propagate the
> appropriate improvements to the our shared skills base.

That reaches beyond collisions. **Today the code contradicts it in two
places, both predating this PR.** Install overwrites any managed projection
whose content differs from the shared base. Prune removes a withdrawn managed
projection whatever it contains.

What is on disk now, read-only
([`o2-skill-inventory/`](../2026-09-29-pr41-audit-response/o2-skill-inventory/)):

- **Managed projections:** 27 of 27 identical to the shared base in every
  target (`codex`, `claude`, `gemini`, `opencode`, `hermes`). None has
  diverged, so nothing evolved has been overwritten yet.
- **Harness-evolved skills:** these live beside the managed ones as
  **unmanaged** directories, which install and prune never touch: 33 in
  Hermes, 6 in Codex, 6 in OpenCode and 3 in Claude. They include Hermes's own
  `flossi0ullk/flossi0ullk-plan-and-ledger` and
  `flossi0ullk/flossi0ullk-mcp-infrastructure`. Hermes nests skills by
  category; our projections are flat.
- **User-scope writes:** no automation passes `--include-user-scope`, so
  `~/.codex/skills` and the Hermes skills root are written only by a manual
  run.

## Proposed direction, not built and not yet approved

Offered for critique. The operator has set the goal but not approved a design,
and nothing below exists in code.

**Record a baseline.** The marker gains an `installed_digest`: a hash over
each file's relative path and **bytes**, as installed, excluding the marker.
It is the idea Hermes already uses. `.bundled_manifest` in its skills root
records `name:hash` for each bundled skill, which lets it tell a skill the user
modified from one that is simply out of date.

**Reconcile three ways** on refresh, for each listed skill with a managed
projection, comparing *base* (the marker's digest), *installed* (the files now)
and *source* (the shared base):

| Installed vs base | Source vs base | Action |
|---|---|---|
| same | same | nothing |
| same | changed | update from source: only the shared base moved |
| changed | same | **keep the installed copy**; report `EVOLVED`; stage a proposal |
| changed | changed | **keep the installed copy**; report `CONFLICT`; stage both sides |
| no baseline (legacy marker) | n/a | if installed equals source, record the baseline; otherwise keep it, report, and stage |

**Prune** keeps a withdrawn projection whose installed content differs from its
baseline, reports it, and stages it. Learnings in a retracted skill are still
learnings.

**Propagate upward, never automatically.** Each evolved or conflicting
projection is staged as a proposal: the evolved files, plus a diff against the
shared base. It goes to an intake location such as
`.agent-surface/skills/proposals/<target>/<skill>/`. Nothing is merged into
`FLOSS/skill-corpus/` automatically, consistent with canon promotion being
advisory-only elsewhere in this repository. A reviewer, human or a consensus
Claim, applies the appropriate parts to the shared base. The next refresh then
sees installed equal to source and re-baselines. Harness-native skills such as
Hermes's `flossi0ullk-*` are listed in the same report as adoption candidates,
not copied.

Questions this leaves, where your view is wanted:

1. Should `EVOLVED` count as `--check` drift? It would make `--check` fail
   until someone reviews, which is a signal but also noise.
2. Where should proposals live? `.agent-surface/` is gitignored and outside
   the repository. `docs/` is reviewable but grows with every harness session.
3. Hermes nests skills by category (`skills/<category>/<skill>`), and our
   projections are flat. Should harvesting follow Hermes's layout, or should
   projections move into a category?
4. Is a byte digest the right baseline, or does per-file granularity matter,
   so that a proposal can say which file evolved?

## Still open from earlier rounds

- Hermes PID identity. A PID that exists is not proof the gateway owns it.
- Unverified runtime behaviour: harness invocation, installed header support,
  authenticated MCP delivery, daemon readiness.
- The narrow JSON handlers outside this PR's files, and the O3 `os.replace`
  failures. Both are filed and being worked on separately.
- Both operator decisions on range acceptance.

## Conventions you may not expect

- Comments are long and explain **why a previous version was wrong**. That is
  house style, not padding.
- Truth-status discipline: no claim is marked verified without a traceable
  artifact.
- Refusing a claim is not refusing the run. A check that cannot answer keeps
  the output and withholds the verdict. The same principle now applies to
  skills: keep what a harness learned, and withhold only the overwrite.
