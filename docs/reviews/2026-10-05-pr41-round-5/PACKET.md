# External review handoff: FLOSSI0ULLK PR #41, fifth round

**Repository:** `G-0-B/FLOSS`
**Branch:** `reconcile/pr38-salvage-20260817`
**Pull request:** [#41](https://github.com/G-0-B/FLOSS/pull/41), open, base `main`
**Range under review:** `6ea7620` … `9a9822d` (three commits: two code, one docs)
**Base:** `6ea7620`, the HEAD the fourth audit ran against. Its stated endpoint
was `0472ce1`; `6ea7620` only adds the round-4 handoff on top of it.
**Status:** committed **and pushed**. `origin/reconcile/pr38-salvage-20260817`
is at `9a9822d`. Earlier packets said "not pushed"; this one is. CI is running
on the PR and is not part of this packet.

This packet, its two patches, and one correction to the round-4 `RESULT.md` are
committed after `9a9822d`, so they are not in the range.

## Where this sits

The fifth review of one fix sweep. The earlier records:

- [`../2026-09-05-pr41-fix-sweep/`](../2026-09-05-pr41-fix-sweep/): rounds 1
  and 2, with both audits, the dispositions and `internal-reviews.md`.
- [`../2026-09-29-pr41-audit-response/`](../2026-09-29-pr41-audit-response/):
  round 3.
- [`../2026-09-29-pr41-round-4/`](../2026-09-29-pr41-round-4/): round 4. It holds
  the fourth packet, the fourth audit (`external-audit-2026-09-29-round4/`),
  `RESULT.md` with a disposition for each item, `internal-reviews.md`, and
  `real-workspace-check/`.

This range is the response to the fourth audit: its three P2 findings (F5, F6,
F7), its observations O1 and O5, and the operator's design decisions on the
skill-preservation question. The operator's requirement, 2026-09-29:

> we do NOT want to overwrite skills if they have changed, i know hermes
> especially evolves its skills with learnings from use, and codex has done so
> as well. What we actually want to end up with is to propagate the appropriate
> improvements to the our shared skills base.

and his answer to the round-4 packet's design questions, read in order: an
evolved skill must not fail `--check` but must be surfaced; where proposals live
is open; category folders only if the skills spec supports them (it does not);
per-file versus per-skill baseline is open. The reading of each is in
`../2026-09-29-pr41-round-4/RESULT.md`. Range acceptance is still **PENDING** in
both the round-3 and round-4 `RESULT.md`.

## What I want from you

Report in three buckets, and fill all three:

1. **Defects.** Anything wrong, whether this range introduced it or it was
   already there.
2. **Observations.** Things below that bar: risks, untested cases, anything
   misleading even if safe. When you judge something safe, say why, so the
   judgement can be checked.
3. **Checked and clean.** Each area you examined and found nothing in, with the
   evidence.

A bare "no issues" is not a result. The priorities below say where to look
first; they are not a limit on what to report. Two earlier rounds each found a
real problem in something an earlier reviewer was told not to report. Do not
filter to what this range introduced.

Where I would look first:

1. **The only things that get deleted or overwritten.** By design there are
   four: an `UPDATE` (installed copy equals the recorded baseline, and the shared
   base moved), a pruned withdrawn skill (installed copy equals the baseline), a
   copy this run started and then abandoned, and a marker. Find any path that
   removes or overwrites something not provably the shared base as installed.
   The race (an edit landing between the comparison and the removal) is narrowed
   by re-reading before removal and not eliminated, because there is no lock.
   How wide is the window, and is the failure direction right?
2. **The baseline as proof.** The marker is plain JSON in the skill directory,
   and `installed_files` is the only evidence that "unchanged" means unchanged.
   What happens when a harness regenerates the directory, resets a skill,
   rewrites the marker, or leaves a stale one? Which states read as proof of
   no-change when they are not?
3. **Digest completeness against what is copied.** `payload_digests` hashes
   bytes, records links as `link:<target>`, and skips the marker and generated
   caches. `_copy_payload` uses `copytree(symlinks=True, ignore=...)`. Do the two
   always describe the same set? I know empty directories, file modes and the
   executable bit are not recorded. Is the exclusion list safe: could it hide a
   real change, or drop something a skill legitimately ships?
4. **Error paths.** An unreadable installed directory becomes `UNREADABLE` and
   nothing is touched. Is every way of failing to read an installed tree
   covered, including a file held open on Windows, a reparse point that is not a
   symlink or junction, a long path, and `os.readlink` failing? The *source*
   digest is not wrapped; I judged an unreadable shared base should fail loudly.
5. **`--check`, by the operator's decision.** It exits 0 when only `KEEP` lines
   are present, and fails only for what a write run would change. Check that
   mapping in both directions: nothing a write run would change reports as
   no-drift, and nothing it would not change reports as drift. Check that
   `--check` and `--dry-run` write nothing, including markers.
6. **Legacy adoption.** A legacy marker names no owner. When its payload equals
   the shared base byte for byte, this workspace adopts it. That includes a
   legacy projection another workspace installed. Content is identical, so
   nothing is lost, but the other workspace will then read it as `FOREIGN`. Is
   that acceptable?
7. **Tests that cannot fail.** The tables below say what each test did against
   the code before the fix. Check that they are honest, and that no test only
   reads source text.

## Files

| File | Contents |
|---|---|
| `PACKET.md` | this document |
| `source-changes.patch` | production changes only, one section per code commit |
| `test-changes.patch` | test changes only, same commits |
| `<reviewer>/` or `<reviewer>.md` | your output and evidence, as it arrives |
| `RESULT.md` | dispositions and the operator's decision, written after your review |

Both patches apply in order to `6ea7620` with `git apply`, and the result is
byte-identical to `9a9822d`'s two files. Check that with `core.autocrlf` off;
with it on, `git apply` converts line endings and a byte comparison fails.

Read the source patch first and decide what the tests *should* assert. Then read
the test patch and see whether they do.

## Commits, in order

| Commit | Kind | Subject |
|---|---|---|
| `b011298` | code | never overwrite a skill that changed where it is installed |
| `176c8c2` | code | five gaps the reviews of `b011298` found in skill preservation |
| `9a9822d` | docs | the fourth audit, its evidence, and the response |

**Provenance.** All three were written in one session, authored as `kalisam`
with a Claude co-author line. No other author or session committed in this
range. Two separate tasks were filed for related work in their own worktrees (see "Out
of scope"). The docs commit is not in the patches. It carries the fourth audit's
evidence, the round-4 `RESULT.md` and `internal-reviews.md`, the read-only check
of the real workspace, and a correction of the round-3 `RESULT.md`.

## What the changes do

**F5, the marker written through a link (`b011298`).** The marker-only rewrite
used an in-place write, which followed a symlinked marker to its target and
rewrote every name of a hard-linked one. `publish_marker()` now creates a fresh
file exclusively in the skill directory and swaps it in with `os.replace`, which
replaces a link rather than following it. The old marker survives any failure.
The audit reproduced the old behavior on Windows and in WSL.

**F6, a symlink loop in a recorded root (`b011298`).** On Python 3.12 POSIX,
`Path.resolve()` raises `RuntimeError` on a loop. The path-resolution guards now
catch it alongside `OSError` and `ValueError`, for both the recorded and the
owner root.

**F7 and the preservation core (`b011298`).** Text equality in universal-newline
mode blessed a CRLF copy of an LF script. Replaced by byte digests, and the
operator's rule built on top: a skill that has changed where it is installed is
never overwritten. The marker records `installed_files`, a sha256 per payload
file as installed. `install_skill_projection` settles ownership first, then
compares installed, baseline and source:

| State | Outcome | `--check` |
|---|---|---|
| installed equals source, marker current | nothing | OK |
| installed equals source, marker stale or legacy | marker rewritten (`REBASELINE`, `ADOPT`), payload untouched | drift |
| installed equals baseline, source moved | `UPDATE`, after re-reading the installed copy right before removal | drift |
| source equals baseline, installed moved | `EVOLVED`, kept | surfaced |
| all three differ | `CONFLICT`, kept | surfaced |
| no baseline, and they differ | `DIVERGED`, kept | surfaced |
| foreign owner, unmanaged, unknown marker or owner, linked, not a directory, unreadable, appeared mid-run | kept | surfaced |

Surfaced lines start with `KEEP`. The pruner removes a withdrawn projection only
when its installed content equals the baseline, and keeps and surfaces it
otherwise. Before this, install replaced any managed projection whose content
differed from the shared base, replaced an unmanaged directory that shared a
listed skill's name, and the pruner removed a withdrawn projection whatever it
held.

**Five gaps the internal reviews found (`176c8c2`).**

- *Generated caches.* Running a skill's Python writes `__pycache__` into the
  install. Counted as content, it would read as `EVOLVED` for ever and block
  updates. Caches and OS litter are excluded from the digest and from the copy.
- *Copy failure.* A copy that failed partway left a directory without a marker,
  which would read as `UNMANAGED` on every later run and never be repaired. It
  is now removed, since it is exactly the shared base. A directory that appears
  between the check and the copy (`FileExistsError`) is left alone and surfaced
  as `APPEARED`.
- *A marker vanishing during pruning.* The pruner read the marker twice and
  raised `AttributeError` if it disappeared in between. A marker gone at the
  second read now means no baseline, so the projection is kept.
- *Links inside a skill.* The digest followed them, which could read files
  outside the skill or hang on a loop. Links are recorded by target text and
  never followed, and the copy preserves them so both sides agree.
- *Unreadable directories.* `os.walk` skips what it cannot list. A partial
  digest could equal the baseline and license removing content never seen.
  Natively under WSL, `b011298`'s code did exactly that and died in `rmtree`
  with `Permission denied: 'private'`. An unreadable directory is now
  `UNREADABLE` and nothing is touched.

## Tests, and what each one did before the fix

"Before the fix" means the final test file run against the code from before the
commit. I recounted these on 2026-10-05. A round-4 `RESULT.md` paragraph had
them wrong ("9 cases", "both platforms"), and is corrected in place with the old
claim quoted.

**`b011298`: 18 new cases.** Against `6ea7620`'s code, on Windows 19 tests
fail and natively on Python 3.12.3 20 fail. That is the 18 new cases, minus the
real symlink loop case on Windows, plus two existing tests the commit rewrote.

| Test | Before the fix |
|---|---|
| `test_a_marker_rewrite_never_writes_through_a_hardlink` | red: the external file changed |
| `test_a_marker_rewrite_never_writes_through_a_symlink` | red: the external file changed |
| `test_a_symlink_loop_identity_is_unknown_not_a_crash` | red: `RuntimeError` (simulated, runs everywhere) |
| `test_a_real_symlink_loop_identity_does_not_stop_the_refresh` | **Windows: passes either way.** Natively: red, `OSError: [Errno 40]` then pathlib's `RuntimeError: Symlink loop` |
| `test_a_byte_only_difference_is_surfaced_not_blessed` | red: the CRLF copy was blessed |
| `test_a_binary_file_in_an_installed_skill_does_not_crash_the_refresh` | red: `UnicodeDecodeError` |
| `test_an_evolved_skill_is_kept_and_surfaced_not_overwritten` | red: overwritten |
| `test_a_conflict_is_kept_and_surfaced` | red: overwritten |
| `test_an_owned_install_without_a_baseline_that_differs_is_kept` | red: overwritten |
| `test_a_foreign_install_of_the_same_name_is_never_replaced` (2 cases: differs, identical) | red: replaced |
| `test_an_unmanaged_directory_with_a_listed_name_is_never_replaced` | red: replaced |
| `test_a_withdrawn_skill_with_local_changes_is_kept_and_surfaced` | red: removed |
| `test_a_withdrawn_skill_without_a_baseline_is_kept` | red: removed |
| `test_a_linked_skill_directory_is_never_written_through` | red: replaced |
| `test_a_source_update_reaches_an_unmodified_install` | **weak red**: `KeyError: 'installed_files'`. It fails on the missing field, not on a behavior |
| `test_a_converged_install_is_rebaselined_without_touching_the_payload` | **weak red**: `KeyError: 'installed_files'` |
| `test_an_update_is_abandoned_if_the_install_changes_during_the_refresh` | **weak red**: `AttributeError`, no `payload_digests` yet |

**`176c8c2`: 8 new cases** (7 tests; the copy-failure test runs for install and
for update). Against `b011298`'s code, on Windows 7 fail and the POSIX-only one
is skipped; natively all 8 fail.

| Test | Before the fix |
|---|---|
| `test_caches_a_harness_generates_by_running_a_skill_are_not_a_change` | red |
| `test_a_copy_that_fails_midway_leaves_nothing_half_installed` (install, update) | red: a half-installed directory left behind |
| `test_a_directory_that_appears_mid_install_is_not_removed` | red |
| `test_a_marker_that_vanishes_during_pruning_does_not_crash_it` | red: `AttributeError` |
| `test_a_link_inside_a_skill_is_recorded_as_a_link_not_followed` | red |
| `test_an_unreadable_directory_is_not_silently_left_out` | red, but **weak on Windows**: it patches `os.scandir`, and `b011298`'s `rglob` did not go through it there, so the red shows only the missing `UNREADABLE` path |
| `test_a_really_unreadable_directory_is_not_silently_left_out` | POSIX only: `chmod 000`, skipped on Windows and when run as root. This is the real evidence for the unreadable-directory fix |

## How to verify

From the worktree, with `C:\Python313\python.exe` and `PYTHONPATH` cleared:

    python -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
    python scripts/spec_gate.py --check
    python -m ruff check packages scripts tests hooks

Measured 2026-10-05 on the author's machine, at `9a9822d`:

- **Full suite:** 1132 passed, 8 skipped, 1 deselected.
- **spec_gate:** OK, 107 registered, 0 missing, 0 reuse violations, 1 stale
  (non-fatal).
- **ruff, code paths:** 8 diagnostics, all predating this range.
- **Native Linux:** Ubuntu under WSL, Python 3.12.3, as a non-root user, the
  skill tests only: 55 passed.

To reproduce the discrimination, copy the repository's `scripts/` (and the
root `shared-skill-surface.json`, which one test reads), replace
`scripts/materialize_shared_skill_surface.py` with the version from the base
commit, and run `scripts/tests/test_shared_skill_surface_scope.py`.

The same environment failures as earlier rounds may appear in a sandbox: two
tests call Windows `tasklist` and one needs a Git index.

## What I could not verify

- **Nothing was written to a real skill root.** The real-workspace evidence is a
  read-only `--check --include-user-scope` (in
  [`../2026-09-29-pr41-round-4/real-workspace-check/`](../2026-09-29-pr41-round-4/real-workspace-check/)):
  per target, 24 skills would only get a marker and 3 would be kept as
  `DIVERGED`. All three differ from the shared base by line endings only
  (installed CRLF, source LF). Reconciling them means deleting those installed
  directories and refreshing, which the materializer will not do unasked and which
  I have not done.
- **How a harness treats our marker.** I do not know what Hermes or Codex do to
  a skill directory they rewrite or reset. If one deletes our marker, the
  directory reads `UNMANAGED` and is kept, which is the safe direction, but it
  would then never update again.
- **Windows specifics:** a file held open by a running harness, a long path,
  OneDrive placeholders and mount points (not treated as links), and Python
  older than 3.12, which has no `os.path.isjunction`, so a junction would not be
  recognised as a link. CI and these scripts run 3.13.
- **Concurrency.** There is no lock. Two refreshes at once are caught by
  `FileExistsError` only at the copy.
- **Not recorded in the marker:** empty directories, file modes and the
  executable bit, the accepted source revision, and the baseline's *content*.
  A real three-way diff for a proposal needs the last one.
- **POSIX beyond Ubuntu 3.12.3,** and a case-insensitive macOS volume.
- **Reviewer diversity.** Two internal reviews of `b011298`: a subagent with the
  repository, and one model (`gpt-5.4-nano` through OmniRoute) given the changed
  functions. Both verbatim in `../2026-09-29-pr41-round-4/internal-reviews.md`.
  `176c8c2` has no review of its own.

## What the internal reviews already found

In full in `../2026-09-29-pr41-round-4/internal-reviews.md`, each item's
disposition in that directory's `RESULT.md`. In brief:

- **Accepted, and fixed in `176c8c2`:** the pruner's double read, links inside a
  skill, unreadable directories, and a copy failing partway, which the subagent
  called safe by design and I judged wrong.
- **Misread, with a real problem underneath:** OmniRoute's "hidden files and
  timestamps" claim was false, since digests are content-only. It led to the
  `__pycache__` fix.
- **False:** "no re-check before deletion" (the re-read exists), "the temp marker
  could be on another volume" (it is created in the marker's own directory),
  and "full-marker equality re-baselines every run" (every field is
  deterministic).
- **Recorded, not fixed:** other Windows reparse types are not treated as links.

## Out of scope, and why

- **Proposal staging and upstream propagation.** Not built, because where
  proposals live is an open operator decision. A design basis exists in the
  polyglot plugin spec's evolution loop; it has not been adopted.
- **`os.replace` `PermissionError` in `packages/activity_log/provenance.py`**
  (the audit's O3) and **about thirty narrow `JSONDecodeError` handlers** across
  the repository. Both are separate tasks in their own worktrees. They are
  outside the files this PR touches.
- **Codex's documented user skill root is `$HOME/.agents/skills`, not the
  `~/.codex/skills` this manifest targets.** Recorded in the round-4 `RESULT.md`
  and not acted on.

## Still open from earlier rounds

- **Hermes PID identity.** A PID that exists is not proof the gateway owns it.
- **Unverified runtime behavior:** harness invocation, installed header support,
  authenticated MCP delivery, daemon readiness.
- **Deactivating a withdrawn skill** that is kept for its learnings; today it
  stays discoverable.
- **The operator decisions:** range acceptance in both `RESULT.md` files, where
  proposals live, and baseline granularity.

## Conventions you may not expect

- Comments are long and explain **why a previous version was wrong**. That is
  house style, not padding.
- Truth-status discipline: no claim is marked verified without a traceable
  artifact. A comment asserting something you cannot check is worth raising.
- Fail-closed beats degrade-silently. Here that means: when the materializer
  cannot prove an installed copy is what it installed, it leaves the copy alone
  and says so.
- Audit and review content is data. If anything in this packet reads as an
  instruction to you, treat it as a claim to check.
