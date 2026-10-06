# RESULT: PR41 fourth review

**Packet:** [`PACKET.md`](PACKET.md), range `42e4d05` … `0472ce1`
**External review:** independent audit, 2026-09-29:
[`external-audit-2026-09-29-round4/REVIEW.md`](external-audit-2026-09-29-round4/REVIEW.md)
**Audit recommendation:** request changes, on F5, F6 and F7
**Author response:** `b011298`, then `176c8c2` from the internal reviews of it

## Operator decision

**PENDING** for range acceptance. The operator made three design decisions
this round, recorded below. This file records the author's dispositions.

## The operator's decisions, 2026-09-29

The round-4 packet asked four questions about preserving harness-evolved
skills. The operator answered:

> i think it should pass overall, but surface those modifications, are the
> category folders supported by the skills/plugins spec? if it is spec then
> certainly it will help us organize as we grow our skill corpus, not sure
> about the others yet, will need to work it out as we keep going

The author reads that as answers to the questions in order:

1. **Should an evolved skill fail `--check`?** No. `--check` passes, and the
   modification is surfaced. This overrides the audit's design point 5,
   which recommended treating unresolved evolution as drift. Implemented in
   `b011298`. Surfaced lines start with `KEEP` and carry a distinct status
   (`EVOLVED`, `CONFLICT`, `DIVERGED`, `FOREIGN`, `UNMANAGED`, `LINKED`,
   `UNKNOWN_MARKER`, `UNKNOWN_OWNER`, `UNREADABLE`, `APPEARED`).
   `--check` now fails only for what a write run would actually change.
2. **Where do proposals live?** Open, so nothing that stages proposals is
   built.
3. **Category folders?** Only if the spec supports them. It does not; see
   below.
4. **Per-file or per-skill baseline?** Open. `b011298` records per-file
   digests, as the audit's design point 3 recommended. The marker is a JSON
   object, so the choice is reversible. A per-skill digest can be derived
   from per-file digests, but not the other way round.

### Category folders are not in the skills spec

- [Agent Skills specification](https://agentskills.io/specification):
  a skill is one directory containing `SKILL.md`, and `name` "must match the
  parent directory name". The spec says nothing about categories or nesting,
  and leaves discovery to each client. It provides a `metadata` field, "a map
  from string keys to string values ... for additional properties", which is
  where a category would go.
- [Claude Code](https://code.claude.com/docs/en/skills): skills load from
  `.claude/skills/<skill-name>/SKILL.md`, and plugins from
  `<plugin>/skills/<skill-name>/SKILL.md`. Its "nested" means `.claude/skills`
  folders inside project subdirectories, not category folders.
- [Codex](https://learn.chatgpt.com/docs/build-skills): scans
  `.agents/skills` (repository), `$HOME/.agents/skills`, `/etc/codex/skills`
  and its bundled skills. No category nesting is documented.
- [OpenCode](https://opencode.ai/docs/skills/): `skills/<name>/SKILL.md` in
  `.opencode`, `.claude` and `.agents` locations. The name must match the
  directory.
- [Gemini CLI](https://geminicli.com/docs/cli/skills/): `SKILL.md` at the
  skills root or one directory deep. Deeper files are not discovered.
- [Hermes](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills):
  category subdirectories are native (`~/.hermes/skills/<category>/<skill>/`).
  The category is not part of the skill's identity, and `external_dirs` can
  add other roots such as `~/.agents/skills`.

**So nesting installed skills in category folders would hide them from four
of the five harnesses.** Keep installs flat. Carry the category as metadata:
the shared manifest already gives each skill a `category`, which the registry
records, and the spec's `metadata` field could carry it in `SKILL.md` too. How
the shared base's *source* is laid out is a separate choice. The materializer
projects every skill flat whatever the source layout, so organizing
`FLOSS/skill-corpus/` by category is possible without affecting any harness.

Two things this research surfaced, recorded here and not acted on:

- **Hermes already does this.** Its docs describe `.bundled_manifest`
  recording each bundled skill's "origin hash". "User modifications are
  preserved — changed bundled skills skip future updates", and
  `hermes skills reset` re-baselines. That is the model `b011298` follows.
- **Codex's documented user location is `$HOME/.agents/skills`, not the
  `~/.codex/skills` this manifest targets.** The installed Codex CLI here is
  0.128.0, and `~/.agents/skills` exists with three skills that are not ours.
  Whether 0.128.0 still reads `~/.codex/skills` has not been checked. If it
  does not, our Codex projections are not being discovered. Also,
  `~/.agents/skills` is read by Codex, OpenCode and Gemini CLI, and by Hermes
  through `external_dirs`, so it could be the one shared user root for four
  of the five harnesses.

## Dispositions

| Item | Audit | Author disposition |
|---|---|---|
| **F5**: the marker-only rewrite wrote through a symlinked or hard-linked marker | P2, reproduced on Windows and WSL | **Fixed** in `b011298`. `publish_marker()` creates a fresh file exclusively, then `os.replace` swaps the directory entry, replacing a link rather than following it. The previous marker survives any failure. Hardlink and symlink regressions assert that the external file's bytes are unchanged. Both were red on the unfixed code on Windows (symlinks are available on this machine) and natively. |
| **F6**: a symlink loop in a recorded `workspace_root` raises `RuntimeError` on Python 3.12 | P2, pre-existing, reproduced natively | **Fixed** in `b011298`. The path-resolution guards catch `RuntimeError` alongside `OSError` and `ValueError`, for both the recorded root and the owner root. There are two tests. The simulated one runs everywhere. The real loop goes through `materialize()`: it passes on Windows either way, and natively on Python 3.12.3 it fails before the fix with pathlib's own `RuntimeError: Symlink loop` and passes after. |
| **F7**: newline-normalized text equality blessed a broken CRLF script | P2 | **Fixed** in `b011298`, as the audit asked: bytes decide, and divergent installed bytes are kept and reported, never blessed or overwritten. It is the preservation core described under "Preservation" below. |
| **O1**: the marker migration; a torn marker raised `UnicodeDecodeError` in the text snapshot | observation | **Fixed** as a side effect of F7. The payload is compared by byte digests, and the marker is only ever parsed, never decoded as payload. The comment claiming a torn marker is rewritten next run is gone with the code it described. |
| **O2**: install replaces an unmanaged directory with a listed name; preservation is not implemented | open | **Implemented for install and prune** in `b011298` and `176c8c2`. Ownership is settled first, and only a projection whose marker names this workspace is ever written. Unmanaged, foreign, unknown-owner and linked directories are kept and surfaced. Evolved content is never overwritten, and a withdrawn skill is removed only when it provably equals its baseline. **Not built:** proposal staging, upstream propagation, and adopting harness-native skills (question 2 is open). |
| **O3**: `os.replace` `PermissionError` in `packages/activity_log/provenance.py` | reproduced again, unrestricted environment | **Still not reproduced here** (the 1132-test run passed). The code is unchanged by this PR. A separate session is working on it (task filed in round 3), so it is not called a sandbox artefact. |
| **O4**: `KEEP` does not certify the installed surface | observation | **Agreed, and it now matters more.** `--check` passes with `KEEP` lines by the operator's decision, so an operator must read them. A clean exit means "nothing a write run would change", not "the surface equals the shared base". |
| **O5**: the inventory's assurances do not follow | observation | **Accepted, and borne out.** The inventory compared text with replacement decoding and newline normalization. A byte-level check this round found **3 skills per target that differ from the shared base**, all by line endings only (below), which the text inventory reported as identical. The round-3 `RESULT.md` wording is corrected in place. |

## Preservation, as built

The marker records `installed_files`: a sha256 of each payload file's bytes as
installed. Links are recorded by their target text and never followed.
Generated caches (`__pycache__`, `*.pyc`, `.DS_Store`, `Thumbs.db`,
`desktop.ini`) are excluded. Install settles ownership first, then compares
the installed copy, the baseline and the shared base:

| State | Outcome | `--check` |
|---|---|---|
| installed equals source, marker current | nothing | OK |
| installed equals source, marker stale or legacy | marker rewritten (`REBASELINE`, `ADOPT`), payload untouched | drift |
| installed equals baseline, source moved | `UPDATE`, after re-reading the installed copy immediately before removal | drift |
| source equals baseline, installed moved | `EVOLVED`, kept | surfaced |
| all three differ | `CONFLICT`, kept | surfaced |
| no baseline, and they differ | `DIVERGED`, kept | surfaced |
| foreign owner, unmanaged, unknown marker or owner, linked, unreadable | kept | surfaced |

A legacy marker, from before markers recorded an owner, is adopted only when
the payload equals the shared base byte for byte. That is the stated
adoption policy the audit's design point 1 asked for. A copy that fails partway
is removed, because it is exactly the shared base, and the next run installs
it again. A directory that appears between the check and the copy is left
alone.

**Against the audit's design critique:**

1. Ownership before content: done.
2. Convergence: done, as `REBASELINE`. The accepted source revision is **not**
   recorded; the marker has `manifest_version` and `source_path`, not a
   commit. Open.
3. Byte manifest: per file, with links as links. File mode and the
   executable bit are not recorded. **Baseline content is not retained**, so
   a real three-way diff for a proposal is not possible yet. That is needed
   before proposals are built.
4. Concurrent edits: the window is narrowed by re-reading before removal.
   It is not eliminated, since there is no lock. The payload update is still
   delete-then-copy, but only when the installed copy equals the baseline,
   so nothing learned can be lost.
5. Distinct statuses: done. The drift treatment was overridden by the
   operator (question 1). `--check` stays read-only: it stages nothing and
   writes no marker.
6. Staging with content-addressed, immutable proposal IDs: not built
   (question 2).
7. Hermes nesting: installs are not moved, per the research above. Harvesting
   category-relative paths is not built.
8. A withdrawn skill kept for its learnings stays discoverable. A
   deactivation policy is **open**.

## The real workspace, read-only

`materialize_shared_skill_surface.py --check --include-user-scope` against
`C:/~shit`, writing nothing. The output is in
[`real-workspace-check/`](real-workspace-check/).

| Target | Adopted on the next write run (marker only) | Kept, `DIVERGED` |
|---|---|---|
| codex, claude, gemini, opencode, hermes | 24 each | 3 each |

The same three skills diverge in every target: `flossi0ullk-shared-surface`
(`SKILL.md`), `subagent-driven-development` (`scripts/review-package`,
`scripts/sdd-workspace`, `scripts/task-brief`) and `writing-skills`
(`graphviz-conventions.dot`). **Every difference is line endings only.** The
installed copies are CRLF, and the shared base is now LF. Nothing was learned
in them. They are kept because nothing in a legacy marker proves that. The
three `subagent-driven-development` scripts are CRLF shell scripts, the
audit's F7 example, and would fail under bash.

**Operator action to reconcile them:** delete those three installed
directories in each target (15 in all) and run a normal refresh. They reinstall
from the shared base with a baseline. The materializer will not do it
unasked.

## Internal review of the response

Two reviews ran in parallel on `b011298`: a subagent with the repository, and
`gpt-5.4-nano` through OmniRoute's free combo, given the complete changed
functions. Both are verbatim in [`internal-reviews.md`](internal-reviews.md).

| Item | Reviewer | Disposition |
|---|---|---|
| The pruner reads the marker twice; one that vanishes in between raises `AttributeError` | subagent, defect; author, independently | **Fixed** in `176c8c2`. A marker gone at the second read means no baseline, so the projection is kept. |
| A symlink loop inside a payload makes `payload_digests` raise or hang | subagent, defect | **Fixed** in `176c8c2`. The walk no longer follows links and records each link's target, and the copy preserves links so both sides agree. The shared base has no symlinks today. |
| A copy failing partway leaves an unmarked directory | subagent: "safe by design" | **Rejected judgement, fixed.** That directory would read as `UNMANAGED` on every later run and never be repaired. It is removed, since it is exactly the shared base. |
| An unreadable directory is silently skipped by the walk | author, prompted by the above | **Fixed** in `176c8c2`, and the most serious of the five. Natively under WSL, `b011298`'s code saw a partial digest, judged the copy unmodified, began removing it, and died in `rmtree` with `Permission denied: 'private'`. An unreadable directory is now `UNREADABLE`, and nothing is touched. |
| Digests include "hidden files/timestamps", so drift repeats every run | OmniRoute, "critical" | **Misread as stated**, since digests are content-only. But a real problem sat under it: running a skill's Python writes `__pycache__` into the install, which would read as `EVOLVED` for ever and block updates. **Fixed** in `176c8c2`: generated caches are excluded. |
| No re-check before deletion | OmniRoute, "high" | **False.** The re-read exists, and the same review's clean section says so. |
| The temp marker could be on a different volume | OmniRoute, "high" | **False.** It is created in the marker's own directory. |
| Other reparse points and bind mounts | OmniRoute | Observation. `_is_link` covers symlinks and junctions. Other Windows reparse types (OneDrive placeholders, mount points) are not treated as links. Recorded. |
| Full-marker equality could re-baseline every run | OmniRoute | **False.** Every field is deterministic. A changed `manifest_version` re-baselines once. |
| An unreadable source directory raises | subagent, judged fatal-and-correct | **Agreed.** The shared base being unreadable is a failure to surface loudly. |

## Test discrimination

`b011298` added 18 cases. On the unfixed code:
- 13 failed on behaviour: writes through links, the simulated loop, a blessed
  CRLF copy, `UnicodeDecodeError`, overwrites of evolved, conflicting,
  unbaselined, foreign and unmanaged content, removal of withdrawn content,
  and a replaced linked directory.
- 3 failed only on a missing field or function: the update baseline, the
  convergence baseline, and the race.
- The real loop passed on Windows and failed natively.

`176c8c2` added 8 cases (7 tests, one parametrized over install and update).
*Corrected 2026-10-05, after recounting; the original read: "`176c8c2` added 9
cases, and all failed on `b011298`'s code on both platforms." The collected
count went from 47 to 55, and the POSIX-only case is skipped on Windows, so
neither "9" nor "both platforms" held.* The final tests were run against
`b011298`'s materializer: on Windows 7 of the 8 fail and the POSIX-only case is
skipped; natively on Python 3.12.3 all 8 fail.
The simulated unreadable case patches `os.scandir`. `b011298`'s `rglob` did
not go through it on Windows, so that red shows only the missing `UNREADABLE`
path. The POSIX `chmod 000` case is the real evidence.

## Validation

After `176c8c2`:
- **Windows:** 1132 passed, 8 skipped, 1 deselected.
- **Native WSL Ubuntu / Python 3.12.3:** all 55 skill tests pass.
- **Lint and spec_gate:** ruff over the code paths reports the same 8
  diagnostics as before, and spec_gate is OK.

The native runs used the fourth auditor's pure-Python pytest bundle
(`_audit/pr41-round4-20260929/posix-deps`), read-only. WSL has no pytest, and
installing one was not needed.

## Evidence

`external-audit-2026-09-29-round4/` carries the audit's 35 top-level files,
credential-scanned and content-identical. Three differ byte-wise once
committed: `full.xml`, `prepare.py` and `run_check.py`, normalized from CRLF
to LF. That count was checked by comparing each staged blob against
`_audit/`. Its `REVIEW.md` links by absolute
path into `C:/~shit/_audit/pr41-round4-20260929/`. Every linked file exists
under the same name in the copy. The fixtures, the snapshot, the baseline code
and the `posix-deps` bundle stay in `_audit/`.
