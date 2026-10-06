# Handoff to Codex: run the room message board on Linux (WSL)

From: Claude (author of the change), 2026-10-06. For: Codex. Operator: kalisam.

## The one thing asked

Run the repository's required test set on Linux, once on the base commit and once on the merged change, compare the two per test case, and save the result in this folder.

Why: the required CI job (`green-set` in `.github/workflows/python-ci.yml`) runs on `ubuntu-latest` with Python 3.13. The change was built and tested on Windows only. Nobody has run this revision on Linux, and nothing is pushed, so CI has not run it either.

Not asked: a design review, a code review, or fixes. If a test fails, report it. Do not change code, tests, or the plan.

**Write `REPORT.md` early.** As soon as the first run finishes, write it with a provisional verdict and keep it current. If your budget ends mid-run, what is on disk is what the operator gets.

## Where things are

- Repository: `C:/~shit/FLOSS`. Its primary checkout is on another branch and holds other agents' uncommitted work. Do not edit, check out, stash, clean or commit there.
- The change: branch `feat/coordination-room-rebased`, checked out in the worktree `C:/~shit/FLOSS/.worktrees/coordination-room-rebased`. Local only: `origin/feat/coordination-room-rebased` is still `2460c55`.
- Base: `4aab13e30f3c2960da787b47c90926256b4b5b73`.
- Head: the tip of `feat/coordination-room-rebased` when you start. Record its full hash. The last commit that changed anything outside `docs/` is `0281a47cd817efb2f2426886e3a1058c157b33eb`; `git diff --quiet 0281a47cd817efb2f2426886e3a1058c157b33eb HEAD -- . ":(exclude)docs"` must exit 0. If it does not, say so first in the report.
- Background, only if you need it: `docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md`, section "Execution record" near the top. Windows receipts: `../execution-phase1/`.

## What is known about the Linux side

Checked from Windows on 2026-10-05, nothing more:

- `wsl -l -q` lists `Ubuntu` and `docker-desktop`.
- In `Ubuntu`: Python 3.12.3, `venv`/`ensurepip` not importable, `pytest` not installed, git 2.43.0, ample disk.

So you have to create a Python environment. Any of these is acceptable; record which you used:

1. `uv` with a Python 3.13 virtual environment (matches CI).
2. `sudo apt-get install python3.12-venv`, then a venv. Needs sudo, and gives 3.12.
3. A `python:3.13` container through Docker.

Prefer 3.13. If you run 3.12, say so in the verdict line.

Install with `pip install -r requirements-ci.txt` taken from the **head** checkout, into one environment, and use that same environment for both runs. Head's file differs from the base's in one line (`mcp` became `mcp>=1.27,<2`); using one environment keeps the comparison about code, not about which `mcp` got resolved. Save `pip freeze`.

## The checkout must be a Linux one

Do not run the tests under `/mnt/c/`. The worktree's `.git` file names a Windows path that Linux git cannot follow, so tests that call git would quietly behave differently; the tests would also write into the Windows checkout.

Make a clone inside the Linux filesystem, in a directory you own, for example `~/room-board-linux/`. Either route is fine:

- a bundle: on Windows, `git -C C:/~shit/FLOSS bundle create <a temp path of yours>/room-board.bundle feat/coordination-room-rebased` (reads the repository, changes nothing), then in WSL `git clone -b feat/coordination-room-rebased /mnt/c/<that path>/room-board.bundle ~/room-board-linux/head`;
- or a direct clone: `git -c safe.directory='*' clone -b feat/coordination-room-rebased "/mnt/c/~shit/FLOSS" ~/room-board-linux/head`. Do not write to the Windows repository's config to get past an ownership warning.

Then the base beside it: `git -C ~/room-board-linux/head worktree add ../base 4aab13e30f3c2960da787b47c90926256b4b5b73`.

`git status --porcelain` must be empty in both before each run and after it. Anything there after a run is a finding: a test wrote into the checkout. (One such bug was found and fixed on Windows; deviation 3 in the execution record.)

One write outside the checkout is expected and is not a finding: on the base and on the head, `scripts/tests/test_heartbeat_budget.py` appends to `<parent of the checkout>/.agent-surface/heartbeat/ticks.log`. That is why the parent directory should be yours.

## The runs

Same shell, same environment, from the root of each checkout:

```bash
unset PYTHONPATH COORDINATION_ROOM_BOARD
export PYTHONDONTWRITEBYTECODE=1
export HOME="$(mktemp -d)"     # the daemons' default agent directory is ~/.floss_agent
python -m pytest -q -p no:cacheprovider packages/ tests/ scripts/tests/ \
  --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded \
  --junitxml="$OUT/base.xml" 2>&1 | tee "$OUT/base.txt"      # then head.xml / head.txt
```

That is the CI command plus `-p no:cacheprovider` and the JUnit file. If setting `HOME` breaks your Python environment, drop that line and say so.

Then compare:

```python
"""usage: python compare.py base.xml head.xml > compare.json

Reads only the two JUnit files pytest wrote in this run, so the standard-library parser is enough.
"""
import json, sys, xml.etree.ElementTree as ET
from collections import Counter

def cases(path):
    out = {}
    for tc in ET.parse(path).getroot().iter("testcase"):
        marks = [c for c in tc if c.tag in ("failure", "error", "skipped")]
        out[f'{tc.get("classname")}::{tc.get("name")}'] = (
            (marks[0].tag, (marks[0].get("message") or "")[:300]) if marks else ("passed", ""))
    return out

base, head = cases(sys.argv[1]), cases(sys.argv[2])
new = sorted(k for k in head if k not in base)
print(json.dumps({
    "base_counts": Counter(v[0] for v in base.values()),
    "head_counts": Counter(v[0] for v in head.values()),
    "failing_on_base": sorted(k for k, v in base.items() if v[0] in ("failure", "error")),
    "regressed": sorted(k for k, v in base.items() if v[0] == "passed" and k in head and head[k][0] != "passed"),
    "missing_on_head": sorted(k for k in base if k not in head),
    "new_cases": len(new),
    "new_not_passing": {k: head[k] for k in new if head[k][0] in ("failure", "error")},
    "new_skipped": {k: head[k][1] for k in new if head[k][0] == "skipped"},
}, indent=2))
```

Last, in each checkout: `python scripts/spec_gate.py --check`. On Windows both print the same three findings and exit 1 (two `MISSING FLOSS/hooks/grok_*.py`, one `STALE FLOSS/scripts/research_log.py`). Report whether Linux agrees and whether base and head agree with each other.

## What to expect, so surprises stand out

- Windows, same command: base 993 passed, 7 skipped; head 1,115 passed, 7 skipped; no failures; 122 new cases.
- On Linux the new Windows-only tests skip: everything in `scripts/tests/test_daemon_scope.py` and in `packages/coordination_room/tests/test_deploy_helpers.py` (they drive PowerShell), and one alias case in `packages/coordination_room/tests/test_message_board.py`. Expect fewer new passes and more skips than on Windows. List every skipped new case with its reason.
- `packages/coordination_room/tests/test_v01_compat.py` must run, not skip, in a clone that contains `4aab13e`. A skip there is a finding.
- A Grok-family reviewer reported that on Linux, at `2460c55` (the base's parent), `packages/coordination_room/tests/test_paths.py::test_backslash_collapses_to_same_key` fails. The author has not verified that. If it fails on the base here too, it is pre-existing, and it also means the required CI job is red on the base: say that plainly. It is a regression only if it passes on the base and fails on the head.

## Verdict rule

- `LINUX: PASS`: nothing that passes on the base fails, errors or disappears on the head, and every new case passes or skips for a stated platform reason.
- `LINUX: FAIL`: anything else. Do not soften it.
- `LINUX: INCOMPLETE`: you could not finish (sudo password, blocked network, budget). Say exactly what is missing.

## What to leave here

In this folder, `C:/~shit/FLOSS/.worktrees/coordination-room-rebased/docs/reviews/2026-10-02-room-board-v1/linux-run/`:

- `REPORT.md`. First line: the verdict and one sentence. Then: the environment (distribution, kernel, Python version, how the environment was made, the `mcp` version that resolved); base and head full hashes; passed, failed, skipped per stage; tests failing on the base; regressions; new cases not passing; new cases skipped, with reasons; the spec gate result; `git status` after the runs; anything you did differently from this handoff; what you did not do; where the Linux clone and environment are.
- `base.txt`, `head.txt`, `base.xml`, `head.xml`, `compare.json`, `pip-freeze.txt`, and `commands.txt` (what you ran, in order).

Files in this folder are stored byte for byte (`../.gitattributes`).

Then commit only this folder, from the Windows worktree, and do not push:

```bash
git -C C:/~shit/FLOSS/.worktrees/coordination-room-rebased add -- docs/reviews/2026-10-02-room-board-v1/linux-run
git -C C:/~shit/FLOSS/.worktrees/coordination-room-rebased commit -F- -- docs/reviews/2026-10-02-room-board-v1/linux-run
```

If `git status --short` in that worktree shows anything outside this folder, stop and say so instead of committing. If you cannot commit, leave the files and say so in your final message.

Leave the Linux clone and the environment where they are; a rerun should be cheap.

## Do not

- push, pull, rebase, or open a pull request;
- change anything outside this folder;
- touch the working tree of `C:/~shit/FLOSS` or of any other worktree;
- start, stop or signal the Windows daemons (ports 7331, 7332, 7334, 7335, 20128), or touch `C:/Users/kalis/.floss_agent` or `C:/~shit/.agent-surface`;
- run `scripts/start_mcp_daemons.ps1` or `scripts/stop_mcp_daemons.ps1` yourself (the tests run them with stand-ins; that is fine);
- run `scripts/materialize_shared_agent_memory.py` or `scripts/refresh_agent_surfaces.py`.
