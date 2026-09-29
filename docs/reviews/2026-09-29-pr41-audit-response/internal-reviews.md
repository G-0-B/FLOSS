# Internal reviews of this round's response: verbatim

Per [`../README.md`](../README.md): the prompt as sent and the return as
received, taken from the session transcript. The only edits are removing the
harness wrapper (task-notification tags, usage counters and agent ids) and
reversing its XML escaping. Nothing inside a prompt or a return is altered,
including claims in the return that did not hold; `RESULT.md` gives each
item's disposition.

A parallel review of the same commit through OmniRoute was attempted. It did
not run: `MCP server "omniroute" session expired`.

## 1. `9a23477`, 2026-09-29

The fix for the third audit's F4, with O1 and O4.

Reviewer: `caveman:cavecrew-reviewer`.

### Prompt

````text
Review commit `9a23477` in the git worktree C:/~shit/FLOSS/.worktrees/pr41-salvage (use `git -C "C:/~shit/FLOSS/.worktrees/pr41-salvage"`; `git show 9a23477`). Do not modify any file, do not use git stash, do not commit or push. Python: `C:/Python313/python.exe` with PYTHONPATH cleared, run from the worktree, e.g. `PYTHONPATH= C:/Python313/python.exe -m pytest -q -p no:cacheprovider scripts/tests/test_shared_skill_surface_scope.py`. Scratch files only under C:/Users/kalis/AppData/Local/Temp/claude/C---shit/9c834986-63b7-46f0-83a1-33a7c558f045/scratchpad/rev.

What the commit does, in `scripts/materialize_shared_skill_surface.py`: skill projections installed into shared roots carry a marker JSON naming the installing workspace (`workspace_root`). A pruner removes projections whose skill left this workspace's manifest, only if the marker names this workspace exactly.
1. F4 (from an external audit): `projection_owned_by` resolved the recorded root under `except OSError` only; on POSIX a NUL in the path raises ValueError from resolve(), aborting the whole materializer. Resolution moved to new `recorded_workspace()`, which catches OSError and ValueError and returns None for unusable identities.
2. O4: `prune_stale_projections` now emits `KEEP` lines (never removes, not drift) for markers with no usable identity (missing, relative, empty, non-string, unresolvable) and for markers naming a workspace root that no longer exists (`os.path.exists`). A live foreign workspace's projection stays silent.
3. O1: `install_skill_projection`: when installed files equal the source and only the marker differs, rewrite only the marker (plain write) instead of delete-then-copy.

Directions, not a filter — report anything you find, introduced or pre-existing, inside or outside these:
- `recorded_workspace` / `projection_owned_by`: any other exception `Path(...)`, `is_absolute()`, `resolve()`, `os.path.normcase`, `os.path.exists` can raise on hostile marker contents (non-str already filtered; think long paths, odd unicode, surrogates, drive-relative `C:foo`, `\\?\` prefixes, UNC)? On Windows is `Path("C:foo").is_absolute()` False? Does `os.path.exists` on the resolved path ever raise?
- The KEEP for "no longer exists": could a live workspace ever be reported as gone (unmounted drive, network path timeouts, permission-denied parent making exists() False)? Is reporting-only safe in all those cases?
- Marker-only rewrite: the snapshot compares file TEXT read with `read_text(encoding="utf-8")`. Could two different installed payloads compare equal (binary files, newline translation, files the source lacks but the installed dir has, or vice versa)? Does a directory present in the install but empty in the source matter? What happens if the installed dir has the marker but the marker belongs to ANOTHER workspace (foreign, valid, existing) and content is identical — does the marker-only path silently take ownership? Compare with what the old delete-then-copy path did in the same case.
- Tests added in `scripts/tests/test_shared_skill_surface_scope.py` (search for "Third external audit"): `_posix_realpath` patches `os.path.realpath` globally — does `Path.resolve()` on this Python actually go through it, so the F4 tests are genuinely exercising the new except? For each new test, name the production change that would make it fail. Could any pass while the behaviour is broken?
- Any caller or message consumer depending on the old KEEP wording ("not removed") or the old `WROTE` line format?

Report in three buckets; all three are required; a bare "no issues" is not a result.
1. DEFECTS — one line each: `path:line: severity: problem. fix.`
2. OBSERVATIONS — unsure, or judged safe with the reason, so the judgement can be checked.
3. CHECKED AND CLEAN — each area checked, one line on how.
````

### Return

````text
Perfect. Let me write my findings in the three requested buckets.

## Review of Commit 9a23477

**DEFECTS**

No defects identified.

**OBSERVATIONS**

1. `Path.resolve()` platform consistency: The `_posix_realpath` patch in tests patches `os.path.realpath` to reject NUL bytes globally, but Python 3.12's `Path.resolve()` may not call `os.path.realpath` directly. If the internal implementation diverges between versions or platforms, the F4 test might not exercise the actual production code path. However, the code is defensive—it catches both `OSError` and `ValueError`—so the test passes and production behavior is correct regardless. Verify on POSIX with Python 3.12 that NUL-byte paths actually raise `ValueError` from `Path.resolve()` before concluding the test genuinely covers the real failure mode (see L486 in materialize_shared_skill_surface.py, L618 in test file).

2. `os.path.exists()` on unreachable network paths: The "no longer exists" KEEP line (L554) uses `os.path.exists(recorded)`, which returns `False` for unmounted drives, network timeouts, or permission-denied parents. A workspace temporarily unreachable from this run is reported as "no longer exists." The behavior is conservative (keep the file), but the message may mislead an operator into believing the workspace is permanently gone. Safe from a data-loss perspective; log readability is a separate concern.

3. Marker-only rewrite does not check ownership: The marker-only path (L616-630) applies if content is identical, regardless of which workspace originally installed the projection. If a foreign workspace's skill has identical content, ownership silently transfers to the current workspace. This mirrors pre-existing delete-then-copy behavior (L632-637), so it is not a regression. However, if a live shared-root scenario ever has concurrent marker rewrites from different workspaces, only the last writer's workspace_root persists. Tests do not cover this race (single-threaded); production use should rely on the source chain's mutex semantics if concurrent writes occur (see L623-625 comment about torn writes being recoverable).

4. Snapshot encoding does not flag newline mode differences: All files are read with `read_text(encoding="utf-8")` using universal newlines mode, converting `\r\n` ↔ `\n` transparently. If a source file's line endings change without content change, the snapshot comparison sees no difference, and a marker-only rewrite skips the copy. This preserves old line endings; it does not introduce new drift. Pre-existing pattern, not introduced by O1.

**CHECKED AND CLEAN**

1. **Exception handling (`recorded_workspace` / `projection_owned_by`, L472-488)**: Both functions correctly catch `OSError` and `ValueError` from `Path.resolve()`. The guard `if not isinstance(recorded, str) or not Path(recorded).is_absolute()` short-circuits safely—`is_absolute()` is only called if `recorded` is a string. No other `Path()` operations or `os.path` calls in the exception path raise uncaught exceptions. Edge cases (surrogates, very long paths, drive-relative paths on Windows) either fail safely (return None) or are rejected by the guards.

2. **KEEP logic for missing or unusable identities (L545-559)**: Empty dict check is implicit (if marker is None, handled L544); missing `workspace_root`, relative paths, non-strings, and unresolvable paths all return None from `recorded_workspace()` and trigger KEEP message. A live foreign workspace's projection stays silent (no message). The test suite covers all four parametrized cases (L593–606 in test file) plus the moved-workspace case (L608–622). Logic is clean.

3. **Marker-only snapshot comparison (L616-630)**: The `without_marker()` helper correctly filters the MANAGED_MARKER key from both dicts before comparison. Dict equality is reflexive and transitive; if `without_marker(actual) == without_marker(expected)`, only the marker differs. The plain `write_text()` is safe—a torn marker mid-write is unowned on the next read (L623 comment), and the marker is atomically flushed by the OS before function return. The test mocks `remove_path` and `copytree` to verify they are not called (L641–657 in test file).

4. **Tests (L585–768 in test file)**: All new tests pass. F4 tests (NUL byte, abort recovery) validate the ValueError catch. O4 tests cover five unusable identities and the moved-workspace case; foreign-workspace test now creates the other workspace to confirm silence is correct. O1 test patches both mutation functions and verifies marker-only path is taken. The existing test was updated to expect silence (not KEEP message) for live foreign workspaces. No test breaks; behavior is backward compatible with one message-format clarification ("left in place" vs "not removed").

---

**Absolute paths for reference:**  
C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py  
C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/tests/test_shared_skill_surface_scope.py
````
