# Candidate fix for the one Linux failure (not applied)

Author evidence, 2026-10-06. Nothing in this folder is collected by the test set, and nothing here has been applied to the code.

## The failure

Codex's Linux run (`../linux-run/REPORT.md`) found the required test set red on the base `4aab13e` and on this branch alike, with one failing test:
`packages/coordination_room/tests/test_paths.py::test_backslash_collapses_to_same_key`.

Cause: `normalize_path` in `packages/coordination_room/paths.py` (v0.1, commit `9c29872`) builds a `pathlib.Path` from the caller's string. On Windows a backslash is a separator. On POSIX it is an ordinary filename character, so a path written with backslashes stays one component. On a POSIX host that is more than a test failure:

- a path written with backslashes and the same path written with slashes are two claim keys, so two agents can each hold "the same file" (the spec lists that as a reason to retire the room);
- a dot-dot written with a backslash is accepted as a file name inside the root instead of being refused;
- a `file:` evidence ref written with backslashes is `unresolved` although the file exists.

The room on this machine runs on Windows, so none of that is live here. The required CI job runs on Linux, so it fails on any pull request that carries this package.

## The candidate

`paths.patch`: one line, treating a backslash as a separator on every platform. `test_path_separators.py`: four tests, written to live in `packages/coordination_room/tests/`.

## What was run

`wsl_verify.sh`, fed to WSL on standard input, in a throwaway clone of Codex's Linux head checkout (`/home/kalis/room-board-linux-claude-pathfix/`), using the Python 3.13.13 environment Codex left (`mcp` 1.30.0). Output: `wsl_verify.out.txt`.

| Where | Before the fix | After the fix |
|---|---|---|
| Linux, the five path tests plus the four new ones | 5 failed, 4 passed | 9 passed |
| Linux, `packages/coordination_room/tests` | | 118 passed, 2 skipped |
| Linux, the required test set | 1,083 passed, 1 failed, 24 skipped (Codex) | 1,088 passed, 24 skipped, exit 0 |
| Windows, the same nine tests, in an export of this branch | 9 passed | 9 passed |
| Windows, `packages/coordination_room/tests`, same export | | 120 passed, 1 skipped (the compatibility test needs git history) |

Per test case on Linux, against Codex's head run: one outcome changed (the failing test now passes), nothing went missing, four cases were added and pass. `ruff check --isolated` is clean on both files.

## Why it is not applied

`packages/coordination_room/paths.py` is not among the paths the operator approved for this work (the plan's Task 0 Step 1). Applying it is the operator's call.

Not checked: a file whose name really contains a backslash can no longer be claimed on POSIX. Git cannot check such a file out on Windows either, so the room treats it as out of scope; say so if that is wrong for this repository.
