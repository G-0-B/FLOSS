# Fix for the one Linux failure (applied in `dff1884`)

Author evidence, 2026-10-06 and 2026-10-07. Nothing in this folder is collected by the test set. The candidate below was applied on 2026-10-07 as commit `dff1884dc1e7f508a996fa8a3464b2d1da147b82`; see "Applied" at the end.

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

## Applied

The candidate was tried while `paths.py` was outside the paths the operator had approved, so it was first saved here unapplied. The operator then approved it ("yes", 2026-10-07, to "Apply the path fix to `feat/coordination-room-rebased`?"). The commit message of `dff1884` gives that date as 2026-10-06; that is the day the question was asked, and the message is wrong by a day.

What was done, in order, on the real tree:

1. The test file went into `packages/coordination_room/tests/`, byte-identical to the copy here.
2. Linux, a clone of the then-current head `7b1bfee` plus that test file, no fix (`wsl_red.sh`, `wsl_red.out.txt`): 5 failed, 4 passed. On Windows the same nine tests pass without the fix, because Windows already treats a backslash as a separator; the fault is POSIX-only.
3. The one line went into `paths.py`, identical to `paths.patch`, and one sentence into the spec's "Claim unit".
4. Windows, the worktree with the fix: room package 121 passed; the required test set 1,119 passed, 7 skipped, no failures (`windows-required-set.txt`; it ran just before the commit, so its first line names the previous head, and the tree it ran on is the one that was committed).
5. Commit `dff1884`.
6. Linux, a clone of `dff1884` (`wsl_green.sh`, `wsl_green.out.txt`, `linux-required-set.txt`): the required test set exits 0 with 1,088 passed, 24 skipped. Against Codex's head run, one outcome changed (the failing test passes), nothing is missing, four cases are new and pass; against Codex's base run nothing regressed. The checkout was clean before and after, and the spec gate printed the same three findings.

✅ Verified on this machine: with `dff1884` the required test set is green on Linux (WSL, Python 3.13.13, `mcp` 1.30.0) and on Windows. Not verified: the GitHub-hosted runner itself; nothing is pushed.

Not checked: a file whose name really contains a backslash can no longer be claimed on POSIX. Git cannot check such a file out on Windows either, so the room treats it as out of scope; say so if that is wrong for this repository.
