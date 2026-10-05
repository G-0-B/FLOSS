# Coordination Room Message Board v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow the coordination room from "claims plus broadcast" into a continuously saved message board: topics, threads, evidence-labelled posts, a generated `BOARD.md`, and (Phase 2) an A2A post/read bridge.

**Architecture:** Purely additive over v0.1. `events.jsonl` stays the only record and the room daemon (`:7334`) stays its only writer. New optional fields ride on existing `broadcast` and `claim` rows, so old rows still load and old callers still work. `BOARD.md` is a pure function of the log, rewritten after each mutation and never read back. The A2A bridge is a client of the room's MCP tools, not a second writer.

**Tech Stack:** Python 3.13, pytest, FastMCP (`mcp>=1.27`), `a2a-sdk==1.1.2` (Phase 2), jsonschema, PowerShell for daemon wiring.

**Spec:** `docs/specs/coordination-room.spec.md` v0.2.0 (Task 1 writes it). Research seam: `docs/research/2026-08-31-mas-papers-reeval-intake.md:49-52` (DELM "admission-time verification").

**Truth status:** ⚠️ Specified. Every file body in this plan was run in a scratch copy of `feat/coordination-room-rebased @ 4aab13e` plus `feat/a2a-harness-mesh @ 225287c`: 75 passed in `packages/coordination_room/tests` (21 baseline + 54 new), 112 passed and 1 skipped across `coordination_room` and `a2a_mesh`, `ruff check` clean, `python -m packages.a2a_mesh.room_bridge` serves its Agent Card and a second launch exits on the PID guard. Nothing here has landed on any branch.

**Authored:** 2026-10-02, replacing an Antigravity draft that was pasted into a session and never entered the repo.

## What changed from the Antigravity draft, and why

Every row was checked against the repo on 2026-10-02.

| Draft said | Repo says | This plan |
|---|---|---|
| Paths under `FLOSS/`, A2A source in `.worktrees/a2a-harness-mesh` | `FLOSS/` is a nested, gitignored repo (root `.gitignore:16`). Worktrees live in `FLOSS/.worktrees/`. | All commands run in a FLOSS worktree. |
| Modify `packages/coordination_room/` freely | `docs/superpowers/plans/2026-09-02-coordination-v1.md` Global Constraints: "Keep `packages/coordination_room/` unchanged (0-line vs rebased)". | Task 0 records an operator waiver before any code. |
| Wire `:7334` into `start_mcp_daemons.ps1` and `stop_mcp_daemons.ps1` | Already on `feat/coordination-room-rebased` (`2460c55`). `feat/coordination-room` has neither that nor the line-separator fix. | Base on `feat/coordination-room-rebased`. Only the bridge line is new. |
| Run A2A on `:9900` | `:9900` is Hermes' own A2A listener (`docs/superpowers/plans/2026-08-29-a2a-harness-mesh.md`). | Bridge uses `:7335`. |
| `room_bridge.py` bridges A2A into the room | Room state (`_seq`, claim table) lives in the daemon process. A second process appending to `events.jsonl` would reuse sequence numbers. | Bridge is an MCP client of `:7334`. An AST test forbids importing the room package. |
| Tag messages `[VERIFIED]` when a file exists | Existence is not verification. Repo truth-label canon forbids the overclaim. | `evidence_status` is `resolved` or `unresolved`, never "verified". Posts are admitted either way. |
| New `message_type` field next to `type` | Redundant with `type` and `topic`. | Dropped. |
| New `room_post` tool | Extra tool in every agent's tool list for no new capability. | `room_broadcast` gains optional arguments. New tools: `room_topics` only. |
| `room_read(limit=50)` | A non-zero default silently truncates every v0.1 caller. | Default `limit=0` (all). |
| A2A client posts with "post to #claims ..." natural language | Parsing prose is guessing. | Deterministic grammar plus a JSON form. Anything else is an error. |
| `claim_with_intent()` | | `room_claim(..., intent="")`, same event type. |
| DELM benchmark framing | The intake doc itself lists the paper's benchmark numbers as unverified (line 81). | Plan relies only on the structural seam, not on any number. |
| Coordination-v1 baseline "17 tests" | `4aab13e` added 4 line-separator tests. Measured on the base: 21 passed. | Baseline is 21. |

## Global Constraints

- **Base branch:** `feat/coordination-room-rebased` (`4aab13e`). Not `feat/coordination-room`.
- **Worktree:** `C:/~shit/FLOSS/.worktrees/room-board-v1`, branch `feat/room-board-v1`. Never implement in `C:/~shit/FLOSS` itself: it is on `feat/coordination-room` with dozens of foreign dirty files.
- **Additive only.** The 21 baseline tests stay green and untouched. No existing field, tool name, or argument changes meaning. Rows written by v0.1 load unchanged. `log.py` is not modified: `EventLog.append(**fields)` already carries the new fields.
- **Router, not controller.** The room labels evidence. It never rejects a post because of it.
- **Truth labels.** The word "verified" never appears in room output. `resolved` means the object existed at post time.
- **One writer per surface.** Only the room daemon writes `events.jsonl` and `BOARD.md`. A failed `BOARD.md` write is logged to stderr and never fails the post.
- **A2A is a peer handshake.** The bridge never claims or releases a path, binds `127.0.0.1` only, uses `:7335`, and is never added to `.mcp.json` (an invariant test on `feat/a2a-harness-mesh` enforces the last point).
- **Spec first.** Task 1 lands before any code. `scripts/spec_gate.py --check` is already red on the base (3 lines, listed in Task 0). The criterion is "no new lines", not "exit 0".
- **CI scope.** `packages/` is inside the required `green-set` job, so every new test must pass on a clean runner. New tests bind loopback ports `19996` to `19998` only.
- **Commands.** Run from the worktree root. `PY` below means `env -u PYTHONPATH C:/Python313/python.exe`.
- **Commits.** `git add -- <paths>` then `git commit -F- -- <paths>` with the message on stdin. Never `git commit -m` after a broad add.

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `docs/specs/coordination-room.spec.md` | Contract, v0.1.0 to v0.2.0 | Replace |
| `docs/specs/coordination-room.schema.json` | Event row schema | Replace |
| `docs/specs/spec-registry.json` | One `irreducible_delta` string | Edit |
| `packages/coordination_room/evidence.py` | Resolve `file:` and `commit:` refs. Pure, no room state. | Create |
| `packages/coordination_room/board.py` | Topic helpers and the `BOARD.md` projection. Pure. | Create |
| `packages/coordination_room/room.py` | Topics, threads, evidence, intent, board hook | Replace |
| `packages/coordination_room/gateway.py` | Pass the new arguments through, add `room_topics` | Replace |
| `packages/coordination_room/server.py` | Register the new surface, pick `BOARD.md` path | Edit |
| `packages/coordination_room/README.md` | Tool list | Replace |
| `docs/agent-memory/project/coordination-room-v0.md` | Agent how-to | Edit |
| `packages/coordination_room/tests/test_evidence.py` `test_board.py` `test_message_board.py` `test_gateway_board.py` `test_schema.py` `test_server_tools.py` | Tests | Create |
| `packages/a2a_mesh/` (6 files) | Merged from `feat/a2a-harness-mesh` | Merge |
| `packages/a2a_mesh/room_bridge.py` | A2A post/read adapter, MCP client of the room | Create |
| `packages/a2a_mesh/tests/test_room_bridge_parse.py` `_pair.py` `_invariants.py` `_e2e.py` | Tests | Create |
| `requirements-ci.txt` | `mcp>=1.27` floor | Edit |
| `scripts/start_mcp_daemons.ps1` `scripts/stop_mcp_daemons.ps1` | Bridge start and stop | Edit |

Phase 1 is Tasks 0 to 5 and stands on its own. Phase 2 is Tasks 6 to 8 and starts only after Phase 1 is verified.

---

## Phase 1: the board

### Task 0: Operator waiver, worktree, baseline

**Files:** none changed in the repo until the final step.

- [ ] **Step 1: Get the waiver in writing.** Ask the operator: "coordination-v1 says keep `packages/coordination_room/` unchanged. This plan changes `room.py`, `gateway.py`, `server.py` and adds `board.py`, `evidence.py`. Waive that constraint for this branch?" Do not start Task 1 without a yes. Copy the reply verbatim into the body of the Task 1 commit message. Coordination-v1 and this plan touch disjoint files except `scripts/start_mcp_daemons.ps1` (a trivial textual merge); either may land first, and if this one lands first coordination-v1's "0-line vs rebased" check becomes "0-line vs the merge base of this branch".

- [ ] **Step 2: Create the worktree.**

```bash
cd C:/~shit/FLOSS
git worktree add .worktrees/room-board-v1 -b feat/room-board-v1 feat/coordination-room-rebased
cd .worktrees/room-board-v1
git log --oneline -1
```

Expected: first line starts with `4aab13e`.

- [ ] **Step 3: Baseline tests.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests`
Expected: `21 passed`.

- [ ] **Step 4: Baseline spec gate. Record it, do not fix it.**

Run: `env -u PYTHONPATH C:/Python313/python.exe scripts/spec_gate.py --check`
Expected (measured 2026-10-02 against a tree extracted from `4aab13e`): exit 1 with exactly these three findings and nothing else:

```
SPEC-GATE MISSING FLOSS/hooks/grok_pretool_st.py
SPEC-GATE MISSING FLOSS/hooks/grok_session_register.py
SPEC-GATE STALE   FLOSS/scripts/research_log.py (registered but absent — prune or restore)
```

If the findings differ, stop and reconcile before Task 1; later steps compare against this list.

- [ ] **Step 5: Import this plan so the branch carries its own lineage.**

```bash
cp C:/~shit/FLOSS/docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md docs/superpowers/plans/
git add -- docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md
git commit -F- -- docs/superpowers/plans/2026-10-02-coordination-room-board-v1.md <<'EOF'
docs(plan): coordination room message board v1, reconciled with coordination-v1
EOF
```

- [ ] **Step 6 (optional, protocol):** if the room daemon is up (`curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7334/mcp` prints anything but `000`), `room_claim` each file listed under a task before editing it. On 2026-10-02 the daemon was down in the authoring session, so claims were not exercised.

---

### Task 1: Spec v0.2.0, schema, registry

**Files:**
- Replace: `docs/specs/coordination-room.spec.md`
- Replace: `docs/specs/coordination-room.schema.json`
- Edit: `docs/specs/spec-registry.json`

**Interfaces:**
- Produces: the field names every later task uses: `topic`, `reply_to`, `thread_id`, `intent`, `evidence_refs`, `evidence_status` (`resolved` | `unresolved`), `evidence_checked` (`[{ref, kind, ok}]`, `kind` in `file` | `commit` | `unknown`).

- [ ] **Step 1: Replace the spec.**

````markdown
# Coordination Room — File-Claim MCP Router and Message Board

```yaml
id: "coordination-room-spec"
version: "0.2.0"
kind: "spec"
status: "Active"
created: "2026-08-30"
updated: "2026-10-02"
truth_status: "v0.1 unit tests Verified on landing; v0.2 Specified until its plan lands"
schema: "coordination-room.schema.json"
approval: "v0.1 operator yes-to-everything 2026-08-30; v0.2 pending operator review"
```

## What this is

A Plane A **router** for concurrent coding agents. File-level exclusive claims plus an append-only message log, exposed as MCP tools. It does not write the claimed files, merge CRDT bytes, or decide truth.

Compose the computer-use **lease shape** (one exclusive holder). Do not share that table. Do not build an AgentOS. No pycrdt (AgentRoom measured coordination tools, not the CRDT, as the load-bearing step).

## Claim unit

Normalized file path relative to the room root. One exclusive holder. Same-agent re-claim is idempotent. Second agent gets `conflict` plus the holder id. A claim may carry a short `intent` (max 256 bytes), recorded on the first claim only.

A post to topic `claims` is chat, not a claim. The claim table is the authority.

## Tools

`room_claim` | `room_release` | `room_state` | `room_broadcast` | `room_read` | `room_topics`

- `room_broadcast(agent_id, text, topic?, evidence_refs?, reply_to?)`: no claim required. `text` max 4096 bytes. `topic` defaults to `general`.
- `room_read(since_seq?, topic?, thread_id?, limit?)`: events oldest first. `limit` 0 means all, so a caller written for v0.1 sees the same rows.
- `room_topics()`: topics in use with counts, plus the suggested set.

## Topics and threads

A topic is a lowercase slug, `^[a-z0-9][a-z0-9_-]{0,31}$`. Any slug is accepted. Suggested: `announcements`, `claims`, `inquiries`, `general`. Rows written before v0.2 have no topic and read as `general`; claim and release rows read as `claims`.

`reply_to` names an earlier broadcast. The reply takes that row's topic (an explicit different topic is rejected) and records `thread_id`, the seq of the thread's root.

## Evidence refs

`evidence_refs` is up to 16 strings, each `file:<path>` (a regular file under the room root) or `commit:<sha>` (7 to 40 hex chars, a commit in the room root's repository). Anything else is `unknown`.

The room records `evidence_status`: `resolved` when every ref exists, `unresolved` otherwise, and the checked rows. **The post is admitted either way.** The room is a router: it labels, readers filter.

`resolved` means the referenced object existed when the post was written. It does not mean the claim in the text is true, and the room never writes the word "verified".

## BOARD.md

`.agent-surface/rooms/default/BOARD.md` is a generated view of the log: live claims, the last 20 broadcasts per topic, agents seen in the last 24 hours. It is rewritten after every claim, release, and broadcast, and at startup. It is never read back. A failed write is logged to stderr and does not fail the post.

## A2A bridge

`packages/a2a_mesh/room_bridge.py` lets an A2A peer post and read. It is a client of the room's own MCP tools and never opens the log (one writer per surface). It cannot claim or release a path. Posts are attributed `a2a:<sender>`, so an unauthenticated caller cannot appear as a harness. It listens on `127.0.0.1:7335`; `:9900` is Hermes' own A2A listener. It is not an MCP server and is not added to `.mcp.json`.

## Runtime

- Package: `FLOSS/packages/coordination_room/`
- HTTP: `127.0.0.1:7334/mcp` (PID `coordination_room.pid`)
- Log: `.agent-surface/rooms/default/events.jsonl` (workspace root)
- Board: `.agent-surface/rooms/default/BOARD.md`, beside the log

## Falsifiers

Retire if: two exclusive holders on one path succeed; a conflict is only visible as chat; daemon binds non-loopback; log is rewritten in place; a row is labelled verified by existence alone; BOARD.md is read as a source of state; the A2A bridge writes the log or claims a path.
````

- [ ] **Step 2: Replace the schema.**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "floss://specs/coordination-room.schema.json",
  "title": "Coordination room event",
  "description": "One append-only JSONL line in the coordination-room event log.",
  "type": "object",
  "required": ["seq", "ts", "type", "agent_id"],
  "properties": {
    "seq": { "type": "integer", "minimum": 1 },
    "ts": { "type": "string" },
    "type": { "enum": ["claim", "release", "broadcast"] },
    "agent_id": { "type": "string", "minLength": 1 },
    "path": { "type": "string" },
    "text": { "type": "string", "maxLength": 4096 },
    "intent": { "type": "string", "maxLength": 256 },
    "topic": { "type": "string", "pattern": "^[a-z0-9][a-z0-9_-]{0,31}$" },
    "reply_to": { "type": "integer", "minimum": 1 },
    "thread_id": { "type": "integer", "minimum": 1 },
    "evidence_refs": {
      "type": "array",
      "maxItems": 16,
      "items": { "type": "string", "minLength": 1, "maxLength": 512 }
    },
    "evidence_status": { "enum": ["resolved", "unresolved"] },
    "evidence_checked": {
      "type": "array",
      "maxItems": 16,
      "items": {
        "type": "object",
        "required": ["ref", "kind", "ok"],
        "additionalProperties": false,
        "properties": {
          "ref": { "type": "string" },
          "kind": { "enum": ["file", "commit", "unknown"] },
          "ok": { "type": "boolean" }
        }
      }
    }
  },
  "allOf": [
    {
      "if": { "properties": { "type": { "const": "broadcast" } } },
      "then": { "required": ["text"] }
    },
    {
      "if": { "properties": { "type": { "enum": ["claim", "release"] } } },
      "then": { "required": ["path"] }
    },
    {
      "if": { "required": ["reply_to"] },
      "then": { "required": ["thread_id", "topic"] }
    },
    {
      "if": { "required": ["evidence_refs"] },
      "then": { "required": ["evidence_status", "evidence_checked"] }
    }
  ]
}
```

- [ ] **Step 3: Edit the registry.** In `docs/specs/spec-registry.json`, in the `FLOSS/docs/specs/coordination-room.schema.json` entry, replace this exact string (it occurs once):

```
"irreducible_delta": "Event types claim|release|broadcast with optional path/text. No new schema language."
```

with:

```
"irreducible_delta": "Event types claim|release|broadcast with optional path/text/intent plus topic, reply_to, thread_id and evidence fields on broadcast. No new schema language."
```

Keep the file's existing line endings.

- [ ] **Step 4: Validate the JSON and the gate.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -c "import json; [json.load(open(p, encoding='utf-8')) for p in ('docs/specs/coordination-room.schema.json', 'docs/specs/spec-registry.json')]; print('json ok')"
env -u PYTHONPATH C:/Python313/python.exe scripts/spec_gate.py --check
```

Expected: `json ok`, then the same three findings as Task 0 Step 4 and no others (verified 2026-10-02 against the extracted base with these exact edits).

- [ ] **Step 5: Commit** (put the operator's waiver text from Task 0 Step 1 in the message body).

```bash
git add -- docs/specs/coordination-room.spec.md docs/specs/coordination-room.schema.json docs/specs/spec-registry.json
git commit -F- -- docs/specs/coordination-room.spec.md docs/specs/coordination-room.schema.json docs/specs/spec-registry.json <<'EOF'
docs(specs): coordination room v0.2.0, topics, threads and evidence labels

Operator waiver of the coordination-v1 "keep packages/coordination_room unchanged" constraint: <paste verbatim>
EOF
```

---

### Task 2: Evidence resolution

**Files:**
- Create: `packages/coordination_room/evidence.py`
- Test: `packages/coordination_room/tests/test_evidence.py`

**Interfaces:**
- Produces: `resolve_ref(root: Path, ref: str) -> dict` returning `{"ref", "kind", "ok"}`; `resolve_all(root: Path, refs: list[str] | None) -> tuple[str, list[dict]]` returning `(status, checked)` with status `none` | `resolved` | `unresolved`, raising `ValueError` on a malformed list; constants `MAX_REFS = 16`, `REF_MAX = 512`.
- Consumes: `normalize_path`, `PathEscape` from `packages/coordination_room/paths.py`.

- [ ] **Step 1: Write the failing test.**

```python
"""RED tests for evidence-ref resolution.

Production change that would make these fail: a ref outside the room root
resolving, a bare string guessed into a file or commit, or `resolved` reported
while any ref is unresolved.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.evidence import resolve_all, resolve_ref  # noqa: E402


def test_no_refs_is_none(tmp_path: Path):
    assert resolve_all(tmp_path, None) == ("none", [])
    assert resolve_all(tmp_path, []) == ("none", [])


def test_file_ref_inside_root_resolves(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    status, checked = resolve_all(tmp_path, ["file:a.md"])
    assert status == "resolved"
    assert checked == [{"ref": "file:a.md", "kind": "file", "ok": True}]


def test_missing_file_is_unresolved(tmp_path: Path):
    status, checked = resolve_all(tmp_path, ["file:nope.md"])
    assert status == "unresolved"
    assert checked[0]["ok"] is False


def test_file_outside_root_is_unresolved_even_if_it_exists(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    assert resolve_ref(root, "file:../outside.txt")["ok"] is False


def test_directory_is_not_a_file(tmp_path: Path):
    (tmp_path / "d").mkdir()
    assert resolve_ref(tmp_path, "file:d")["ok"] is False


def test_bare_ref_is_unknown_and_unresolved(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    row = resolve_ref(tmp_path, "a.md")
    assert row == {"ref": "a.md", "kind": "unknown", "ok": False}


def test_one_bad_ref_makes_the_set_unresolved(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    status, checked = resolve_all(tmp_path, ["file:a.md", "file:nope.md"])
    assert status == "unresolved"
    assert [c["ok"] for c in checked] == [True, False]


@pytest.mark.parametrize(
    "refs",
    ["file:a.md", [""], [3], ["x"] * 17, ["x" * 513]],
)
def test_malformed_refs_raise(tmp_path: Path, refs):
    with pytest.raises(ValueError):
        resolve_all(tmp_path, refs)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_commit_ref_resolves_only_real_commits(tmp_path: Path):
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    sha = subprocess.run(
        [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert resolve_ref(tmp_path, f"commit:{sha}")["ok"] is True
    assert resolve_ref(tmp_path, f"commit:{sha[:7]}")["ok"] is True
    assert resolve_ref(tmp_path, "commit:" + "0" * 40)["ok"] is False
    # Not hex: never reaches git, so it cannot be read as an option.
    assert resolve_ref(tmp_path, "commit:--help")["ok"] is False
```

- [ ] **Step 2: Run it to see it fail.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_evidence.py`
Expected: collection error, `ModuleNotFoundError: No module named 'packages.coordination_room.evidence'`.

- [ ] **Step 3: Write the implementation.**

```python
"""Symbolic evidence-ref resolution. Existence check only: no claim is verified here."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from packages.coordination_room.paths import PathEscape, normalize_path

MAX_REFS = 16
REF_MAX = 512
_SHA = re.compile(r"[0-9a-f]{7,40}")


def _file_exists(root: Path, ref: str) -> bool:
    try:
        key = normalize_path(root, ref)
    except PathEscape:
        return False
    return (root / key).is_file()


def _commit_exists(root: Path, sha: str) -> bool:
    if not _SHA.fullmatch(sha):
        return False
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return done.returncode == 0


def resolve_ref(root: Path, ref: str) -> dict[str, Any]:
    """`file:<path>` and `commit:<sha>` resolve; anything else is `unknown`."""
    if ref.startswith("file:"):
        return {"ref": ref, "kind": "file", "ok": _file_exists(root, ref[5:])}
    if ref.startswith("commit:"):
        return {"ref": ref, "kind": "commit", "ok": _commit_exists(root, ref[7:])}
    return {"ref": ref, "kind": "unknown", "ok": False}


def resolve_all(
    root: Path, refs: list[str] | None
) -> tuple[str, list[dict[str, Any]]]:
    """Return (status, checked). status is none | resolved | unresolved."""
    if refs is None:
        return "none", []
    if not isinstance(refs, list) or not all(
        isinstance(r, str) and r.strip() for r in refs
    ):
        raise ValueError("evidence_refs must be a list of non-empty strings")
    if not refs:
        return "none", []
    if len(refs) > MAX_REFS:
        raise ValueError(f"evidence_refs exceeds {MAX_REFS} entries")
    if any(len(r.strip()) > REF_MAX for r in refs):
        raise ValueError(f"evidence ref exceeds {REF_MAX} characters")
    checked = [resolve_ref(root, r.strip()) for r in refs]
    status = "resolved" if all(c["ok"] for c in checked) else "unresolved"
    return status, checked
```

- [ ] **Step 4: Run it to see it pass.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests`
Expected: `34 passed` (21 baseline + 13 new). The commit-ref test skips if `git` is not on `PATH`.

- [ ] **Step 5: Commit.**

```bash
git add -- packages/coordination_room/evidence.py packages/coordination_room/tests/test_evidence.py
git commit -F- -- packages/coordination_room/evidence.py packages/coordination_room/tests/test_evidence.py <<'EOF'
feat(coordination-room): resolve file and commit evidence refs, label never verify
EOF
```

---

### Task 3: BOARD.md projection and topic helpers

**Files:**
- Create: `packages/coordination_room/board.py`
- Test: `packages/coordination_room/tests/test_board.py`

**Interfaces:**
- Produces: `DEFAULT_TOPIC = "general"`, `SUGGESTED_TOPICS`, `check_topic(topic) -> str` (raises `ValueError`), `topic_of(event) -> str`, `topic_summary(events) -> list[dict]`, `live_claims(events) -> dict[str, dict]`, `render_board(events, now=None) -> str`, `write_board(path, events, now=None) -> None` (raises `OSError`).

- [ ] **Step 1: Write the failing test.**

```python
"""RED tests for the BOARD.md projection.

Production change that would make these fail: a released claim still listed,
an unresolved evidence ref rendered as resolved, a pipe or newline in message
text breaking the claims table, or a half-written board left behind.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.board import (  # noqa: E402
    render_board,
    topic_of,
    topic_summary,
    write_board,
)

NOW = datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc)


def _event(seq: int, kind: str, agent: str, ts: str = "2026-10-02T11:00:00Z", **fields):
    return {"seq": seq, "ts": ts, "type": kind, "agent_id": agent, **fields}


def test_active_claim_row_shows_owner_and_intent():
    events = [_event(1, "claim", "grok", path="a.py", intent="fix the | pipe")]
    board = render_board(events, NOW)
    assert "| a.py | grok | 2026-10-02T11:00:00Z | fix the \\| pipe |" in board


def test_released_claim_is_absent():
    events = [
        _event(1, "claim", "grok", path="a.py"),
        _event(2, "release", "grok", path="a.py"),
    ]
    board = render_board(events, NOW)
    assert "a.py" not in board
    assert "## Active claims\n\nNone." in board


def test_messages_group_by_topic_and_legacy_rows_read_as_general():
    events = [
        _event(1, "broadcast", "grok", text="legacy row, no topic"),
        _event(2, "broadcast", "claude", text="shipped", topic="announcements"),
    ]
    board = render_board(events, NOW)
    assert board.index("### #announcements") < board.index("### #general")
    assert "- #1 2026-10-02T11:00:00Z **grok**: legacy row, no topic" in board
    assert "**claude**: shipped" in board


def test_evidence_tags_never_say_verified():
    events = [
        _event(
            1, "broadcast", "a", text="ok", topic="general",
            evidence_refs=["file:x.md"], evidence_status="resolved",
        ),
        _event(
            2, "broadcast", "b", text="bad", topic="general",
            evidence_refs=["file:y.md"], evidence_status="unresolved",
        ),
    ]
    board = render_board(events, NOW)
    assert "[evidence resolved] (refs: file:x.md)" in board
    assert "[evidence UNRESOLVED] (refs: file:y.md)" in board
    assert "VERIFIED" not in board.upper()


def test_reply_marks_parent():
    events = [
        _event(1, "broadcast", "a", text="q?", topic="inquiries"),
        _event(2, "broadcast", "b", text="a.", topic="inquiries", reply_to=1, thread_id=1),
    ]
    assert "**b** re #1: a." in render_board(events, NOW)


def test_newlines_and_unicode_separators_in_text_are_flattened():
    events = [_event(1, "broadcast", "a", text="one\ntwo three", topic="general")]
    board = render_board(events, NOW)
    assert "one two three" in board


def test_long_text_is_truncated():
    events = [_event(1, "broadcast", "a", text="x" * 1000, topic="general")]
    rows = render_board(events, NOW).split("\n")
    line = next(row for row in rows if row.startswith("- #1"))
    assert line.endswith("...")
    assert len(line) < 400


def test_roster_window_excludes_stale_agents():
    events = [
        _event(1, "broadcast", "old", ts="2026-10-01T11:59:00Z", text="x", topic="general"),
        _event(2, "broadcast", "fresh", ts="2026-10-02T11:30:00Z", text="y", topic="general"),
    ]
    board = render_board(events, NOW)
    roster = board.split("## Agents seen in the last 24h")[1]
    assert "fresh" in roster
    assert "old" not in roster


def test_topic_of_derives_claims_for_claim_and_release_rows():
    assert topic_of({"type": "claim"}) == "claims"
    assert topic_of({"type": "release"}) == "claims"
    assert topic_of({"type": "broadcast"}) == "general"
    assert topic_of({"type": "broadcast", "topic": "inquiries"}) == "inquiries"


def test_topic_summary_counts_and_last_seq():
    events = [
        _event(1, "claim", "a", path="p"),
        _event(2, "broadcast", "a", text="x", topic="general"),
        _event(3, "broadcast", "a", text="y", topic="general"),
    ]
    assert topic_summary(events) == [
        {"topic": "claims", "count": 1, "last_seq": 1},
        {"topic": "general", "count": 2, "last_seq": 3},
    ]


def test_write_board_replaces_atomically_and_leaves_no_tmp(tmp_path: Path):
    target = tmp_path / "rooms" / "BOARD.md"
    write_board(target, [_event(1, "broadcast", "a", text="x", topic="general")], NOW)
    first = target.read_text(encoding="utf-8")
    write_board(target, [], NOW)
    assert target.read_text(encoding="utf-8") != first
    assert [p.name for p in target.parent.iterdir()] == ["BOARD.md"]
    assert "\r" not in target.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run it to see it fail.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_board.py`
Expected: collection error, `ModuleNotFoundError: No module named 'packages.coordination_room.board'`.

- [ ] **Step 3: Write the implementation.**

```python
"""BOARD.md projection: a pure function of the event log, never a source of truth."""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_TOPIC = "general"
SUGGESTED_TOPICS = ("announcements", "claims", "inquiries", "general")
RECENT_PER_TOPIC = 20
ROSTER_WINDOW = timedelta(hours=24)
SNIPPET_MAX = 280

_TOPIC = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}")
_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def check_topic(topic: str) -> str:
    if not isinstance(topic, str) or not _TOPIC.fullmatch(topic):
        raise ValueError(f"topic must match {_TOPIC.pattern}")
    return topic


def topic_of(event: dict[str, Any]) -> str:
    """Stored topic, else derived: claim/release rows live under `claims`."""
    stored = event.get("topic")
    if stored:
        return str(stored)
    return "claims" if event.get("type") in ("claim", "release") else DEFAULT_TOPIC


def topic_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for event in events:
        row = seen.setdefault(topic_of(event), {"topic": topic_of(event), "count": 0})
        row["count"] += 1
        row["last_seq"] = int(event["seq"])
    return [seen[name] for name in sorted(seen)]


def live_claims(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    held: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("type") == "claim":
            held[event["path"]] = event
        elif event.get("type") == "release":
            held.pop(event["path"], None)
    return held


def _parse_ts(value: Any) -> datetime | None:
    try:
        return datetime.strptime(value, _TS_FORMAT).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _cell(value: object) -> str:
    return " ".join(str(value).split()).replace("|", "\\|")


def _snippet(text: str) -> str:
    flat = " ".join(text.split())
    if len(flat) <= SNIPPET_MAX:
        return flat
    return flat[: SNIPPET_MAX - 3] + "..."


def _evidence_suffix(event: dict[str, Any]) -> str:
    status = event.get("evidence_status")
    refs = event.get("evidence_refs")
    tag = {"resolved": " [evidence resolved]", "unresolved": " [evidence UNRESOLVED]"}
    suffix = tag.get(status, "")
    if refs:
        suffix += " (refs: " + ", ".join(_snippet(str(r)) for r in refs) + ")"
    return suffix


def render_board(events: list[dict[str, Any]], now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    last_seq = events[-1]["seq"] if events else 0
    out = [
        "# Coordination board",
        "",
        "<!-- Generated from events.jsonl by packages/coordination_room/board.py. "
        "A view, not a record: edits are overwritten on the next room event. -->",
        "",
        f"Last seq: {last_seq}",
        "",
        "## Active claims",
        "",
    ]
    claims = live_claims(events)
    if claims:
        out += ["| Path | Owner | Since | Intent |", "|---|---|---|---|"]
        for path in sorted(claims):
            row = claims[path]
            out.append(
                f"| {_cell(path)} | {_cell(row['agent_id'])} "
                f"| {_cell(row.get('ts', ''))} | {_cell(row.get('intent', ''))} |"
            )
    else:
        out.append("None.")

    out += ["", "## Messages by topic", ""]
    by_topic: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        if event.get("type") == "broadcast":
            by_topic.setdefault(topic_of(event), []).append(event)
    if not by_topic:
        out += ["None.", ""]
    for topic in sorted(by_topic):
        out += [f"### #{topic}", ""]
        for event in by_topic[topic][-RECENT_PER_TOPIC:]:
            reply = f" re #{event['reply_to']}" if event.get("reply_to") else ""
            out.append(
                f"- #{event['seq']} {event.get('ts', '')} "
                f"**{_cell(event['agent_id'])}**{reply}{_evidence_suffix(event)}: "
                f"{_snippet(event.get('text', ''))}"
            )
        out.append("")

    out += ["## Agents seen in the last 24h", ""]
    last_seen: dict[str, str] = {}
    for event in events:
        stamp = _parse_ts(event.get("ts"))
        if stamp is not None and now - stamp <= ROSTER_WINDOW:
            last_seen[event["agent_id"]] = event["ts"]
    if last_seen:
        out += [f"- {_cell(name)} (last {last_seen[name]})" for name in sorted(last_seen)]
    else:
        out.append("None.")
    return "\n".join(out) + "\n"


def write_board(
    path: Path, events: list[dict[str, Any]], now: datetime | None = None
) -> None:
    """Replace `path` atomically. Raises OSError; the caller decides it is non-fatal."""
    text = render_board(events, now)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    try:
        os.replace(tmp, path)
    except OSError:
        tmp.unlink(missing_ok=True)
        raise
```

- [ ] **Step 4: Run it to see it pass.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests`
Expected: `45 passed`.

- [ ] **Step 5: Commit.**

```bash
git add -- packages/coordination_room/board.py packages/coordination_room/tests/test_board.py
git commit -F- -- packages/coordination_room/board.py packages/coordination_room/tests/test_board.py <<'EOF'
feat(coordination-room): BOARD.md as a pure projection of the event log
EOF
```

---

### Task 4: Room and gateway

**Files:**
- Replace: `packages/coordination_room/room.py`
- Replace: `packages/coordination_room/gateway.py`
- Test: `packages/coordination_room/tests/test_message_board.py`, `test_gateway_board.py`, `test_schema.py`

**Interfaces:**
- Consumes: Task 2 `resolve_all`; Task 3 `check_topic`, `topic_of`, `topic_summary`, `write_board`, `DEFAULT_TOPIC`, `SUGGESTED_TOPICS`.
- Produces: `CoordinationRoom(root, log_path, board_path=None)`; `.claim(agent_id, path, intent="")`; `.broadcast(agent_id, text, *, topic=None, evidence_refs=None, reply_to=None)` returning `{"ok", "seq", "topic"[, "evidence_status"]}`; `.read(since_seq=0, *, topic=None, thread_id=None, limit=0)`; `.topics() -> {"topics": [...], "suggested": [...]}`. `CoordinationRoomTools(root, log_path, room=None, board_path=None)` with `room_claim`, `room_release`, `room_broadcast`, `room_read`, `room_topics`, `room_state`.

The two source files are small, so they are replaced whole. `room.py` also drops the unused `ClaimConflict` import that `ruff` flags on the base. Replay still handles only `claim` and `release`; the new fields ride on `broadcast` rows, which replay ignores, so restart behaviour is unchanged.

- [ ] **Step 1: Write the failing tests.**

```python
"""RED tests for topics, threads, evidence and the BOARD.md hook on CoordinationRoom.

Production change that would make these fail: an unresolved ref rejecting the
post (the room labels, it does not gate), a reply landing in another topic, a
default `limit` silently truncating old callers, or a failed board write
failing the post.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.log import EventLog  # noqa: E402
from packages.coordination_room.room import CoordinationRoom  # noqa: E402


def _room(tmp_path: Path, board: bool = False) -> CoordinationRoom:
    return CoordinationRoom(
        root=tmp_path,
        log_path=tmp_path / "events.jsonl",
        board_path=(tmp_path / "BOARD.md") if board else None,
    )


def test_plain_broadcast_defaults_to_general(tmp_path: Path):
    room = _room(tmp_path)
    result = room.broadcast("grok", "hello")
    assert result == {"ok": True, "seq": 1, "topic": "general"}
    assert room.read()[0]["topic"] == "general"


@pytest.mark.parametrize("topic", ["Bad Topic", "", "-x", "a" * 33, "UPPER"])
def test_bad_topic_is_rejected_and_nothing_is_logged(tmp_path: Path, topic: str):
    room = _room(tmp_path)
    with pytest.raises(ValueError):
        room.broadcast("grok", "hi", topic=topic)
    assert room.read() == []


def test_reply_inherits_topic_and_thread(tmp_path: Path):
    room = _room(tmp_path)
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    first = room.broadcast("b", "a1", reply_to=root)
    second = room.broadcast("c", "a2", reply_to=first["seq"])
    events = {e["seq"]: e for e in room.read()}
    assert first["topic"] == "inquiries"
    assert events[first["seq"]]["thread_id"] == root
    assert events[second["seq"]]["thread_id"] == root
    assert events[second["seq"]]["reply_to"] == first["seq"]


def test_reply_with_mismatched_topic_is_rejected(tmp_path: Path):
    room = _room(tmp_path)
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    with pytest.raises(ValueError, match="parent topic"):
        room.broadcast("b", "a1", topic="general", reply_to=root)


def test_reply_to_unknown_or_non_broadcast_is_rejected(tmp_path: Path):
    room = _room(tmp_path)
    claim = room.claim("a", "x.py")["seq"]
    with pytest.raises(ValueError, match="not a broadcast"):
        room.broadcast("b", "hi", reply_to=claim)
    with pytest.raises(ValueError, match="not a broadcast"):
        room.broadcast("b", "hi", reply_to=99)


def test_unresolved_evidence_is_labelled_not_rejected(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    room = _room(tmp_path)
    good = room.broadcast("a", "done", evidence_refs=["file:proof.md"])
    bad = room.broadcast("a", "done", evidence_refs=["file:missing.md"])
    plain = room.broadcast("a", "no refs")
    assert good["evidence_status"] == "resolved"
    assert bad["evidence_status"] == "unresolved"
    assert "evidence_status" not in plain
    rows = {e["seq"]: e for e in room.read()}
    assert rows[bad["seq"]]["evidence_checked"] == [
        {"ref": "file:missing.md", "kind": "file", "ok": False}
    ]
    assert "evidence_refs" not in rows[plain["seq"]]


def test_read_filters_by_topic_thread_and_limit(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("a", "x.py")
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "noise")
    room.broadcast("c", "a1", reply_to=root)
    assert [e["seq"] for e in room.read(topic="inquiries")] == [2, 4]
    assert [e["seq"] for e in room.read(topic="claims")] == [1]
    assert [e["seq"] for e in room.read(thread_id=root)] == [2, 4]
    assert [e["seq"] for e in room.read(limit=2)] == [1, 2]
    assert [e["seq"] for e in room.read(since_seq=2, limit=1)] == [3]
    assert len(room.read()) == 4


def test_legacy_rows_without_topic_read_as_general(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    EventLog(path).append("broadcast", "grok", text="old")
    room = CoordinationRoom(root=tmp_path, log_path=path)
    assert [e["text"] for e in room.read(topic="general")] == ["old"]
    assert room.topics()["topics"] == [{"topic": "general", "count": 1, "last_seq": 1}]


def test_topics_lists_counts_and_suggestions(tmp_path: Path):
    room = _room(tmp_path)
    room.broadcast("a", "x", topic="announcements")
    room.broadcast("a", "y")
    out = room.topics()
    assert [t["topic"] for t in out["topics"]] == ["announcements", "general"]
    assert out["suggested"] == ["announcements", "claims", "inquiries", "general"]


def test_claim_intent_is_logged_once_and_capped(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py", intent="  refactor  ")
    room.claim("grok", "a.py", intent="ignored on idempotent re-claim")
    rows = room.read()
    assert len(rows) == 1
    assert rows[0]["intent"] == "refactor"
    with pytest.raises(ValueError, match="intent exceeds"):
        room.claim("grok", "b.py", intent="x" * 257)


def test_claim_without_intent_logs_the_same_row_as_before(tmp_path: Path):
    room = _room(tmp_path)
    room.claim("grok", "a.py")
    row = room.read()[0]
    assert "intent" not in row
    assert set(row) == {"seq", "ts", "type", "agent_id", "path"}


def test_board_is_written_on_every_mutation_and_on_restart(tmp_path: Path):
    room = _room(tmp_path, board=True)
    board = tmp_path / "BOARD.md"
    assert board.exists()
    room.claim("grok", "a.py", intent="work")
    assert "| a.py | grok |" in board.read_text(encoding="utf-8")
    room.release("grok", "a.py")
    assert "a.py" not in board.read_text(encoding="utf-8")
    room.broadcast("grok", "hello board", topic="announcements")
    assert "hello board" in board.read_text(encoding="utf-8")
    board.unlink()
    _room(tmp_path, board=True)
    assert "hello board" in board.read_text(encoding="utf-8")


def test_board_failure_does_not_fail_the_post(tmp_path: Path, capsys):
    # board_path is a directory: os.replace raises OSError on every platform.
    room = CoordinationRoom(
        root=tmp_path, log_path=tmp_path / "events.jsonl", board_path=tmp_path
    )
    result = room.broadcast("grok", "still logged")
    assert result["ok"] is True
    rows = [
        json.loads(line)
        for line in (tmp_path / "events.jsonl").read_text(encoding="utf-8").split("\n")
        if line
    ]
    assert rows[0]["text"] == "still logged"
    assert "BOARD.md projection failed" in capsys.readouterr().err
```

```python
"""RED tests for the board tools on the JSON gateway.

Production change that would make these fail: a bad topic raising instead of
returning a JSON error, `room_read` ignoring its filters, or `room_topics`
missing from the gateway.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room.gateway import CoordinationRoomTools  # noqa: E402


def _tools(tmp_path: Path) -> CoordinationRoomTools:
    return CoordinationRoomTools(
        root=tmp_path,
        log_path=tmp_path / "events.jsonl",
        board_path=tmp_path / "BOARD.md",
    )


def _load(raw: str) -> dict:
    data = json.loads(raw)
    assert isinstance(data, dict)
    return data


def test_broadcast_with_topic_and_evidence_round_trips(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    tools = _tools(tmp_path)
    out = _load(
        tools.room_broadcast(
            agent_id="claude",
            text="landed",
            topic="announcements",
            evidence_refs=["file:proof.md"],
        )
    )
    assert out == {
        "ok": True,
        "seq": 1,
        "topic": "announcements",
        "evidence_status": "resolved",
    }
    events = _load(tools.room_read(topic="announcements"))["events"]
    assert events[0]["evidence_refs"] == ["file:proof.md"]


def test_bad_topic_and_bad_reply_return_json_errors(tmp_path: Path):
    tools = _tools(tmp_path)
    bad_topic = _load(tools.room_broadcast(agent_id="a", text="x", topic="Bad Topic"))
    assert bad_topic["ok"] is False
    assert "topic" in bad_topic["error"]
    bad_reply = _load(tools.room_broadcast(agent_id="a", text="x", reply_to=9))
    assert bad_reply["ok"] is False


def test_read_filters_and_old_call_shape_still_works(tmp_path: Path):
    tools = _tools(tmp_path)
    tools.room_broadcast(agent_id="a", text="one", topic="inquiries")
    tools.room_broadcast(agent_id="a", text="two")
    assert len(_load(tools.room_read())["events"]) == 2
    assert [e["text"] for e in _load(tools.room_read(topic="inquiries"))["events"]] == ["one"]
    assert len(_load(tools.room_read(limit=1))["events"]) == 1


def test_topics_tool(tmp_path: Path):
    tools = _tools(tmp_path)
    tools.room_broadcast(agent_id="a", text="one", topic="inquiries")
    out = _load(tools.room_topics())
    assert out["topics"] == [{"topic": "inquiries", "count": 1, "last_seq": 1}]
    assert "general" in out["suggested"]


def test_claim_with_intent_appears_on_the_board(tmp_path: Path):
    tools = _tools(tmp_path)
    assert _load(tools.room_claim(agent_id="grok", path="a.py", intent="refactor"))["ok"]
    assert "refactor" in (tmp_path / "BOARD.md").read_text(encoding="utf-8")
    conflict = _load(tools.room_claim(agent_id="claude", path="a.py", intent="mine"))
    assert conflict["error"] == "conflict"
    assert conflict["holder"] == "grok"
```

```python
"""RED tests tying coordination-room.schema.json to what the room really writes.

Production change that would make these fail: the room logging a field the
schema forbids by type, or the schema dropping a field the room relies on.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

jsonschema = pytest.importorskip("jsonschema")

from packages.coordination_room.room import CoordinationRoom  # noqa: E402

_SCHEMA = _REPO_ROOT / "docs" / "specs" / "coordination-room.schema.json"


def _validator():
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def test_every_row_the_room_writes_validates(tmp_path: Path):
    (tmp_path / "proof.md").write_text("x", encoding="utf-8")
    room = CoordinationRoom(root=tmp_path, log_path=tmp_path / "events.jsonl")
    room.claim("grok", "a.py", intent="work")
    room.claim("claude", "b.py")
    root = room.broadcast("a", "q?", topic="inquiries")["seq"]
    room.broadcast("b", "a1", reply_to=root, evidence_refs=["file:proof.md"])
    room.broadcast("b", "a2", evidence_refs=["file:missing.md", "wat"])
    room.release("grok", "a.py")
    validator = _validator()
    rows = room.read()
    assert len(rows) == 6
    for row in rows:
        validator.validate(row)


def test_legacy_rows_still_validate():
    validator = _validator()
    validator.validate({"seq": 1, "ts": "t", "type": "claim", "agent_id": "g", "path": "a"})
    validator.validate({"seq": 2, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "hi"})


@pytest.mark.parametrize(
    "row",
    [
        {"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "x", "topic": "Bad Topic"},
        {"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "x", "reply_to": 1},
        {"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "x", "evidence_refs": ["file:a"]},
        {"seq": 1, "ts": "t", "type": "broadcast", "agent_id": "g", "text": "x", "evidence_status": "verified"},
    ],
)
def test_schema_rejects_malformed_board_rows(row):
    with pytest.raises(jsonschema.ValidationError):
        _validator().validate(row)
```

- [ ] **Step 2: Run them to see them fail.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_message_board.py packages/coordination_room/tests/test_gateway_board.py packages/coordination_room/tests/test_schema.py`
Expected: failures that are `TypeError` on the new keyword arguments (`board_path`, `intent`, `topic`). Not import errors; if you see `ModuleNotFoundError`, Tasks 2 or 3 are not on this branch.

- [ ] **Step 3: Replace `room.py`.**

```python
"""Coordination room: claim table + event log + board projection under one lock."""

from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import Any

from packages.coordination_room.board import (
    DEFAULT_TOPIC,
    SUGGESTED_TOPICS,
    check_topic,
    topic_of,
    topic_summary,
    write_board,
)
from packages.coordination_room.claims import ClaimTable
from packages.coordination_room.evidence import resolve_all
from packages.coordination_room.log import TEXT_MAX, EventLog
from packages.coordination_room.paths import normalize_path

INTENT_MAX = 256


class CoordinationRoom:
    def __init__(
        self, root: Path, log_path: Path, board_path: Path | None = None
    ) -> None:
        self._root = root.resolve()
        self._table = ClaimTable()
        self._log = EventLog(log_path)
        self._board_path = board_path
        self._lock = threading.Lock()
        self._replay()
        self._project()

    def _replay(self) -> None:
        for event in self._log.load():
            kind = event.get("type")
            if kind == "claim":
                self._table.force_set(event["path"], event["agent_id"])
            elif kind == "release":
                self._table.force_drop(event["path"])

    def _project(self) -> None:
        """Rewrite BOARD.md. The log is the record; a failed view must not fail a post."""
        if self._board_path is None:
            return
        try:
            write_board(self._board_path, self._log.load())
        except OSError as exc:
            print(
                f"[coordination_room] BOARD.md projection failed: {exc}",
                file=sys.stderr,
            )

    def _find_broadcast(self, seq: int) -> dict[str, Any]:
        for event in self._log.load():
            if int(event["seq"]) == seq and event.get("type") == "broadcast":
                return event
        raise ValueError(f"reply_to {seq} is not a broadcast")

    def claim(self, agent_id: str, path: str, intent: str = "") -> dict[str, Any]:
        if not isinstance(intent, str):
            raise ValueError("intent must be a string")
        if len(intent.encode("utf-8")) > INTENT_MAX:
            raise ValueError(f"intent exceeds {INTENT_MAX} bytes")
        key = normalize_path(self._root, path)
        with self._lock:
            already = self._table.snapshot().get(key) == agent_id
            self._table.claim(agent_id, key)
            if already:
                return {"ok": True, "path": key, "agent_id": agent_id, "seq": self._log._seq}
            fields: dict[str, Any] = {"path": key}
            if intent.strip():
                fields["intent"] = intent.strip()
            event = self._log.append("claim", agent_id, **fields)
            self._project()
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def release(self, agent_id: str, path: str) -> dict[str, Any]:
        key = normalize_path(self._root, path)
        with self._lock:
            self._table.release(agent_id, key)
            event = self._log.append("release", agent_id, path=key)
            self._project()
            return {"ok": True, "path": key, "agent_id": agent_id, "seq": event["seq"]}

    def broadcast(
        self,
        agent_id: str,
        text: str,
        *,
        topic: str | None = None,
        evidence_refs: list[str] | None = None,
        reply_to: int | None = None,
    ) -> dict[str, Any]:
        if not agent_id.strip():
            raise ValueError("empty agent_id")
        if not isinstance(text, str):
            raise ValueError("text must be a string")
        if len(text.encode("utf-8")) > TEXT_MAX:
            raise ValueError(f"broadcast text exceeds {TEXT_MAX} bytes")
        if topic is not None:
            topic = check_topic(topic)
        # Resolved before the lock: a commit probe is a subprocess, and the lock
        # guards the log, not the filesystem.
        status, checked = resolve_all(self._root, evidence_refs)
        with self._lock:
            fields: dict[str, Any] = {}
            if reply_to is not None:
                parent = self._find_broadcast(reply_to)
                parent_topic = topic_of(parent)
                if topic is not None and topic != parent_topic:
                    raise ValueError(
                        f"reply topic must match parent topic {parent_topic!r}"
                    )
                topic = parent_topic
                fields["reply_to"] = reply_to
                fields["thread_id"] = parent.get("thread_id", parent["seq"])
            fields["topic"] = topic or DEFAULT_TOPIC
            if checked:
                fields["evidence_refs"] = [c["ref"] for c in checked]
                fields["evidence_status"] = status
                fields["evidence_checked"] = checked
            event = self._log.append("broadcast", agent_id, text=text, **fields)
            self._project()
            result: dict[str, Any] = {
                "ok": True,
                "seq": event["seq"],
                "topic": fields["topic"],
            }
            if checked:
                result["evidence_status"] = status
            return result

    def read(
        self,
        since_seq: int = 0,
        *,
        topic: str | None = None,
        thread_id: int | None = None,
        limit: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            events = [e for e in self._log.load() if int(e["seq"]) > since_seq]
        if topic is not None:
            events = [e for e in events if topic_of(e) == topic]
        if thread_id is not None:
            events = [
                e
                for e in events
                if e.get("thread_id") == thread_id or e["seq"] == thread_id
            ]
        if limit > 0:
            events = events[:limit]
        return events

    def topics(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
        return {"topics": topic_summary(events), "suggested": list(SUGGESTED_TOPICS)}

    def state(self) -> dict[str, Any]:
        with self._lock:
            events = self._log.load()
            last = events[-1]["seq"] if events else 0
            speakers = sorted({e["agent_id"] for e in events})
            return {
                "claims": self._table.snapshot(),
                "last_seq": last,
                "speakers": speakers,
            }
```

- [ ] **Step 4: Replace `gateway.py`.**

```python
"""JSON tool router for the coordination room. Does not write workspace files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from packages.coordination_room.claims import ClaimConflict
from packages.coordination_room.paths import PathEscape
from packages.coordination_room.room import CoordinationRoom


def _error(message: str, **extra: Any) -> str:
    payload: dict[str, Any] = {"ok": False, "error": message}
    payload.update(extra)
    return json.dumps(payload)


def _ok(payload: dict[str, Any]) -> str:
    payload.setdefault("ok", True)
    return json.dumps(payload)


class CoordinationRoomTools:
    def __init__(
        self,
        root: Path,
        log_path: Path,
        room: CoordinationRoom | None = None,
        board_path: Path | None = None,
    ) -> None:
        self._room = room or CoordinationRoom(
            root=root, log_path=log_path, board_path=board_path
        )

    def room_claim(self, agent_id: str, path: str, intent: str = "") -> str:
        try:
            return _ok(self._room.claim(agent_id, path, intent=intent))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))

    def room_release(self, agent_id: str, path: str) -> str:
        try:
            return _ok(self._room.release(agent_id, path))
        except ClaimConflict as exc:
            return _error("conflict", holder=exc.holder, path=exc.path)
        except (PathEscape, ValueError) as exc:
            return _error(str(exc))

    def room_broadcast(
        self,
        agent_id: str,
        text: str,
        topic: str | None = None,
        evidence_refs: list[str] | None = None,
        reply_to: int | None = None,
    ) -> str:
        try:
            return _ok(
                self._room.broadcast(
                    agent_id,
                    text,
                    topic=topic,
                    evidence_refs=evidence_refs,
                    reply_to=reply_to,
                )
            )
        except ValueError as exc:
            return _error(str(exc))

    def room_read(
        self,
        since_seq: int = 0,
        topic: str | None = None,
        thread_id: int | None = None,
        limit: int = 0,
    ) -> str:
        events = self._room.read(
            since_seq=since_seq, topic=topic, thread_id=thread_id, limit=limit
        )
        return _ok({"events": events})

    def room_topics(self) -> str:
        return _ok(self._room.topics())

    def room_state(self) -> str:
        return _ok(self._room.state())
```

- [ ] **Step 5: Run the whole package.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests`
Expected: `73 passed` (the 21 baseline tests unchanged, including the three Unicode line-separator cases).

- [ ] **Step 6: Lint.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m ruff check packages/coordination_room`
Expected: `All checks passed!`

- [ ] **Step 7: Commit.**

```bash
git add -- packages/coordination_room/room.py packages/coordination_room/gateway.py packages/coordination_room/tests/test_message_board.py packages/coordination_room/tests/test_gateway_board.py packages/coordination_room/tests/test_schema.py
git commit -F- -- packages/coordination_room/room.py packages/coordination_room/gateway.py packages/coordination_room/tests/test_message_board.py packages/coordination_room/tests/test_gateway_board.py packages/coordination_room/tests/test_schema.py <<'EOF'
feat(coordination-room): topics, threads, evidence labels and intent on the room

Additive: v0.1 rows load unchanged and v0.1 callers see the same rows.
EOF
```

---

### Task 5: Server surface and docs

**Files:**
- Edit: `packages/coordination_room/server.py`
- Replace: `packages/coordination_room/README.md`
- Edit: `docs/agent-memory/project/coordination-room-v0.md`
- Test: `packages/coordination_room/tests/test_server_tools.py`

**Interfaces:**
- Consumes: Task 4 `CoordinationRoomTools(..., board_path=...)` and its six tool methods.
- Produces: MCP tools `room_claim(agent_id, path, intent="")`, `room_broadcast(agent_id, text, topic=None, evidence_refs=None, reply_to=None)`, `room_read(since_seq=0, topic=None, thread_id=None, limit=0)`, `room_topics()`; env var `COORDINATION_ROOM_BOARD` (optional override, default `BOARD.md` beside the log).

- [ ] **Step 1: Write the failing test.** It redirects every path before reloading the module, because the server builds its room at import time and would otherwise write `BOARD.md` into the real workspace.

```python
"""RED tests for the FastMCP surface of the coordination room.

Production change that would make these fail: a new parameter dropped from the
registered tool schema (the audit wrapper hiding it), `room_topics` not
registered, or importing the server writing into the real workspace.
"""

from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

pytest.importorskip("mcp")


@pytest.fixture
def server(tmp_path: Path, monkeypatch):
    # Module import builds the room at import time, so every path the room
    # touches must be redirected before the reload.
    monkeypatch.setenv("COORDINATION_ROOM_ROOT", str(tmp_path))
    monkeypatch.setenv("COORDINATION_ROOM_LOG", str(tmp_path / "rooms" / "events.jsonl"))
    monkeypatch.setenv("FLOSS_AUDIT_DIR", str(tmp_path / "audit"))
    import packages.coordination_room.server as module

    return importlib.reload(module)


def test_board_tools_are_registered_with_their_parameters(server):
    tools = {t.name: t for t in asyncio.run(server.mcp.list_tools())}
    assert {"room_topics", "room_broadcast", "room_read", "room_claim"} <= set(tools)
    assert {"topic", "evidence_refs", "reply_to"} <= set(
        tools["room_broadcast"].inputSchema["properties"]
    )
    assert {"topic", "thread_id", "limit"} <= set(
        tools["room_read"].inputSchema["properties"]
    )
    assert "intent" in tools["room_claim"].inputSchema["properties"]


def test_import_writes_the_board_beside_the_redirected_log(server, tmp_path: Path):
    assert (tmp_path / "rooms" / "BOARD.md").exists()
```

- [ ] **Step 2: Run it to see it fail.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests/test_server_tools.py`
Expected: 2 failed (`room_topics` not registered; no `BOARD.md` beside the redirected log).

- [ ] **Step 3: Edit `server.py`.** Four edits, each old string occurs once.

Edit 3a. Replace:

```python
def _audit_sink_path(filename: str) -> str:
```

with:

```python
def _board_path() -> Path:
    override = os.environ.get("COORDINATION_ROOM_BOARD")
    if override:
        return Path(override).expanduser()
    return _log_path().parent / "BOARD.md"


def _audit_sink_path(filename: str) -> str:
```

Edit 3b. Replace:

```python
_tools = CoordinationRoomTools(root=_room_root(), log_path=_log_path())
_SERVER_INSTRUCTIONS = (
    "FLOSSI0ULLK coordination room. Router, not controller. "
    "Claim a file path before writing it. Second claim on a held path is a "
    "system conflict, not a chat parse. Broadcast is append-only. "
    "Does not write workspace files. No pycrdt in v0."
)


def room_claim(agent_id: str, path: str) -> str:
    """Exclusive claim on a room-root-relative file path."""
    return _tools.room_claim(agent_id=agent_id, path=path)
```

with:

```python
_tools = CoordinationRoomTools(
    root=_room_root(), log_path=_log_path(), board_path=_board_path()
)
_SERVER_INSTRUCTIONS = (
    "FLOSSI0ULLK coordination room. Router, not controller. "
    "Claim a file path before writing it. Second claim on a held path is a "
    "system conflict, not a chat parse. Broadcast is append-only and may carry "
    "a topic, a reply_to, and evidence_refs (file:<path> or commit:<sha>); "
    "evidence is labelled resolved or unresolved, never verified. "
    "BOARD.md is a generated view of the log. "
    "Does not write workspace files. No pycrdt in v0."
)


def room_claim(agent_id: str, path: str, intent: str = "") -> str:
    """Exclusive claim on a room-root-relative file path. Optional short intent."""
    return _tools.room_claim(agent_id=agent_id, path=path, intent=intent)
```

Edit 3c. Replace:

```python
def room_broadcast(agent_id: str, text: str) -> str:
    """Append a note to the room log. Does not require a claim."""
    return _tools.room_broadcast(agent_id=agent_id, text=text)


def room_read(since_seq: int = 0) -> str:
    """Read log events with seq > since_seq."""
    return _tools.room_read(since_seq=since_seq)
```

with:

```python
def room_broadcast(
    agent_id: str,
    text: str,
    topic: str | None = None,
    evidence_refs: list[str] | None = None,
    reply_to: int | None = None,
) -> str:
    """Append a note to the room log. Does not require a claim.

    topic: lowercase slug, default general (suggested: announcements, claims,
    inquiries, general). reply_to: seq of an earlier broadcast; the reply joins
    its topic and thread. evidence_refs: file:<path> or commit:<sha>; labelled
    resolved or unresolved, the post is admitted either way.
    """
    return _tools.room_broadcast(
        agent_id=agent_id,
        text=text,
        topic=topic,
        evidence_refs=evidence_refs,
        reply_to=reply_to,
    )


def room_read(
    since_seq: int = 0,
    topic: str | None = None,
    thread_id: int | None = None,
    limit: int = 0,
) -> str:
    """Read log events with seq > since_seq, oldest first. limit 0 means all."""
    return _tools.room_read(
        since_seq=since_seq, topic=topic, thread_id=thread_id, limit=limit
    )


def room_topics() -> str:
    """Topics in use with counts, plus the suggested defaults."""
    return _tools.room_topics()
```

Edit 3d. Replace:

```python
            room_read,
            room_state,
        ),
```

with:

```python
            room_read,
            room_topics,
            room_state,
        ),
```

- [ ] **Step 4: Replace the README.**

```markdown
# Coordination room

MCP router: exclusive file-path claims plus an append-only message log with topics, threads and evidence labels. `BOARD.md` is a generated view of the log.

**How to use:** `FLOSS/docs/agent-memory/project/coordination-room-v0.md`  
**Spec:** `FLOSS/docs/specs/coordination-room.spec.md`

Tools: `room_claim` `room_release` `room_state` `room_broadcast` `room_read` `room_topics`  
Bind: `127.0.0.1:7334/mcp` — `python -m packages.coordination_room.server`  
Board: `.agent-surface/rooms/default/BOARD.md` (beside the log; override with `COORDINATION_ROOM_BOARD`)

Router, not controller. No pycrdt. Does not write the claimed files. Evidence refs are labelled `resolved` or `unresolved`; the room never says "verified".
```

- [ ] **Step 5: Update the agent how-to.** In `docs/agent-memory/project/coordination-room-v0.md`:

Replace the numbered list under `## How to use`:

```
1. `room_claim(agent_id, path)` before you write that path. Path is relative to the FLOSS checkout (e.g. `packages/foo.py`).
2. If the reply is `"error": "conflict"`, someone else holds it (`holder`). Do not write. Pick another path or wait.
3. `room_broadcast(agent_id, text)` for status. No claim required. 4 KiB cap.
4. `room_read(since_seq)` / `room_state()` to see claims and the log.
5. `room_release(agent_id, path)` when done.
```

with:

```
1. `room_claim(agent_id, path, intent="")` before you write that path. Path is relative to the FLOSS checkout (e.g. `packages/foo.py`). `intent` is a short note shown on the board.
2. If the reply is `"error": "conflict"`, someone else holds it (`holder`). Do not write. Pick another path or wait.
3. `room_broadcast(agent_id, text, topic=None, evidence_refs=None, reply_to=None)` for status. No claim required. 4 KiB cap. `topic` is a lowercase slug (default `general`; suggested `announcements`, `inquiries`, `claims`). `reply_to` is the seq of an earlier broadcast. `evidence_refs` are `file:<path>` or `commit:<sha>`; the reply says `resolved` or `unresolved`. The post is admitted either way, and `resolved` only means the object existed.
4. `room_read(since_seq, topic, thread_id, limit)` / `room_topics()` / `room_state()` to see the log, the topics and the claims. A post to topic `claims` is chat, not a claim.
5. `room_release(agent_id, path)` when done.

`.agent-surface/rooms/default/BOARD.md` is a generated, human-readable view of live claims and recent posts. Read it; never edit it.
```

Replace:

```
Binds `127.0.0.1:7334` only. Not yet in `start_mcp_daemons.ps1`. Do not start killed computer-use `:7333` unless the operator asks.
```

with:

```
Binds `127.0.0.1:7334` only. `scripts/start_mcp_daemons.ps1` starts it. Do not start killed computer-use `:7333` unless the operator asks.
```

Replace the last line:

```
`python -m pytest packages/coordination_room/tests -v` from `FLOSS/` (17 passed 2026-08-30).
```

with:

```
`python -m pytest packages/coordination_room/tests -v` from `FLOSS/` (75 passed when the board v1 plan landed).
```

Only keep the `75 passed` figure if Step 6 prints it.

- [ ] **Step 6: Run everything for Phase 1.**

```bash
env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests
env -u PYTHONPATH C:/Python313/python.exe -m ruff check packages/coordination_room
env -u PYTHONPATH C:/Python313/python.exe scripts/materialize_shared_agent_memory.py --check
env -u PYTHONPATH C:/Python313/python.exe scripts/spec_gate.py --check
```

Expected: `75 passed`; `All checks passed!`; the materializer either passes or reports drift in repo-scope projections. If it reports drift, re-run it without `--check`, review the diff, and commit those projections in this task. **Never pass `--include-user-scope`**: it writes machine-wide files and is an operator decision. Spec gate shows the same three findings as Task 0 and nothing new.

- [ ] **Step 7: Commit.**

```bash
git add -- packages/coordination_room/server.py packages/coordination_room/README.md packages/coordination_room/tests/test_server_tools.py docs/agent-memory/project/coordination-room-v0.md
git commit -F- -- packages/coordination_room/server.py packages/coordination_room/README.md packages/coordination_room/tests/test_server_tools.py docs/agent-memory/project/coordination-room-v0.md <<'EOF'
feat(coordination-room): expose board tools over MCP and document them
EOF
```

- [ ] **Step 8: Phase 1 live check (needs the daemon).** Restart the room so it loads the new code, then post with evidence and read it back:

```bash
env -u PYTHONPATH C:/Python313/python.exe -m packages.coordination_room.server
```

(or restart through `scripts/stop_mcp_daemons.ps1` then `scripts/start_mcp_daemons.ps1`). From an agent session, call `room_broadcast` with `topic="announcements"`, `evidence_refs=["file:docs/specs/coordination-room.spec.md"]`, then `room_read(topic="announcements")` and `room_topics()`. Expected: the reply carries `"evidence_status": "resolved"`, the row appears with the next `seq`, and `.agent-surface/rooms/default/BOARD.md` lists it under `### #announcements` tagged `[evidence resolved]`. An MCP client that connected before the restart may need to reconnect to see the new tool schemas.

---

## Phase 2: the A2A bridge

Start only after Phase 1 is verified. The bridge is optional infrastructure: if it fails to start, the room is unaffected.

### Task 6: Bring `a2a_mesh` onto the branch

**Files:**
- Merge: `packages/a2a_mesh/` (6 files), `requirements-ci.txt`, two docs, from `feat/a2a-harness-mesh`
- Edit: `requirements-ci.txt`

- [ ] **Step 1: Merge.** `git merge-tree` on 2026-10-02 reported the merge clean: the A2A branch touches no file that `feat/coordination-room-rebased` changed.

```bash
git merge --no-ff feat/a2a-harness-mesh -m "merge: local A2A helloworld pair (packages/a2a_mesh)"
```

Expected: a merge commit, no conflicts. If git reports conflicts, stop: the base moved since this plan was written.

- [ ] **Step 2: Baseline the merged package.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/a2a_mesh/tests`
Expected: `4 passed, 1 skipped` (the skip is the optional Hermes card probe).

- [ ] **Step 3: Raise the `mcp` floor.** The bridge uses `streamable_http_client`; `streamablehttp_client` is deprecated in `mcp` 1.27. In `requirements-ci.txt` replace the line `mcp` with `mcp>=1.27`. Verify it is the only bare `mcp` line: `grep -n "^mcp$" requirements-ci.txt` prints one line before the edit and none after.

- [ ] **Step 4: Commit.**

```bash
git add -- requirements-ci.txt
git commit -F- -- requirements-ci.txt <<'EOF'
build(ci): mcp>=1.27 for the non-deprecated streamable HTTP client
EOF
```

---

### Task 7: Room bridge

**Files:**
- Create: `packages/a2a_mesh/room_bridge.py`
- Test: `packages/a2a_mesh/tests/test_room_bridge_parse.py`, `test_room_bridge_pair.py`, `test_room_bridge_invariants.py`, `test_room_bridge_e2e.py`

**Interfaces:**
- Consumes: the room's MCP tools `room_broadcast`, `room_read`, `room_topics` over `http://127.0.0.1:7334/mcp`; `packages.mcp_daemon.claim_singleton`; the A2A SDK as `helloworld.py` uses it.
- Produces: `parse_command(raw: str) -> BoardCommand` (raises `CommandError`); `agent_id_for(sender: str) -> str` (always `a2a:` prefixed); `RoomPort` protocol (`async call(tool, arguments) -> dict`); `McpRoomPort(url)`; `build_app(host, port, room) -> Starlette`; `serve_room_bridge(host, port, room)`; `AGENT_NAME = "flossi0ullk-a2a-room-bridge"`; `DEFAULT_PORT = 7335`. Entry point: `python -m packages.a2a_mesh.room_bridge` (PID `a2a_room_bridge.pid`, env `A2A_ROOM_BRIDGE_PORT`, `COORDINATION_ROOM_URL`).

Commands accepted: `topics`; `read [#topic] [since=N]`; `post #topic text`; or one JSON object with `op` in `post` | `read` | `topics`. Failures return an artifact `error: ...` and task state `FAILED`.

- [ ] **Step 1: Write the failing tests.**

```python
"""RED tests for the room-bridge command grammar.

Production change that would make these fail: free text guessed into a post,
a caller choosing a bare harness name as agent_id, or an unbounded read limit.
"""

from __future__ import annotations

import pytest

from packages.a2a_mesh.room_bridge import (
    BoardCommand,
    CommandError,
    agent_id_for,
    parse_command,
)


def test_topics():
    assert parse_command(" topics ") == BoardCommand(op="topics")


def test_post_text_form():
    cmd = parse_command("post #claims who owns packages/x?\nsecond line")
    assert cmd.op == "post"
    assert cmd.topic == "claims"
    assert cmd.text == "who owns packages/x?\nsecond line"


def test_read_text_forms():
    assert parse_command("read") == BoardCommand(op="read")
    assert parse_command("read #claims") == BoardCommand(op="read", topic="claims")
    assert parse_command("read #claims since=12") == BoardCommand(
        op="read", topic="claims", since_seq=12
    )
    assert parse_command("read since=3").since_seq == 3


def test_json_post_with_every_field():
    cmd = parse_command(
        '{"op": "post", "topic": "inquiries", "text": " hi ", '
        '"evidence_refs": ["file:a.md"], "reply_to": "4", "sender": "hermes"}'
    )
    assert cmd == BoardCommand(
        op="post",
        topic="inquiries",
        text="hi",
        evidence_refs=("file:a.md",),
        reply_to=4,
        sender="hermes",
    )


def test_json_read_limit_is_clamped():
    assert parse_command('{"op": "read", "limit": 100000}').limit == 100
    assert parse_command('{"op": "read", "limit": 0}').limit == 1


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "hello there",
        "post no topic here",
        "post #Bad topic",
        "read #claims extra words",
        "{not json",
        "[]",
        '{"op": "claim"}',
        '{"op": "post"}',
        '{"op": "post", "text": "x", "evidence_refs": "file:a"}',
        '{"op": "post", "text": "x", "evidence_refs": [1]}',
        '{"op": "read", "since_seq": "abc"}',
        '{"op": "post", "text": "x", "topic": 5}',
        '{"op": "post", "text": 5}',
    ],
)
def test_everything_else_is_an_error(raw: str):
    with pytest.raises(CommandError):
        parse_command(raw)


def test_agent_id_is_always_prefixed_and_sanitised():
    assert agent_id_for("hermes") == "a2a:hermes"
    assert agent_id_for("claude") == "a2a:claude"
    assert agent_id_for("a b/c") == "a2a:a-b-c"
    assert agent_id_for("") == "a2a:anonymous"
    assert agent_id_for("x" * 100) == "a2a:" + "x" * 32
```

```python
"""A2A pair for the room bridge, against a fake room.

Production change that would make these fail: the bridge touching the log
itself, a room error reported as success, or the caller picking agent_id.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any

import httpx
import pytest
import uvicorn

from packages.a2a_mesh.client import send_hello
from packages.a2a_mesh.room_bridge import RoomUnavailable, build_app

HOST, PORT = "127.0.0.1", 19998


class FakeRoom:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.reply: dict[str, Any] = {"ok": True, "seq": 7, "topic": "announcements"}
        self.raises: Exception | None = None

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool, arguments))
        if self.raises is not None:
            raise self.raises
        return self.reply


def _wait_for(url: str, timeout: float = 10.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            httpx.get(url, timeout=1)
            return
        except httpx.HTTPError:
            time.sleep(0.1)
    raise AssertionError(f"{url} never came up")


@pytest.fixture(scope="module")
def bridge():
    room = FakeRoom()
    server = uvicorn.Server(
        uvicorn.Config(build_app(HOST, PORT, room), host=HOST, port=PORT, log_level="warning")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for(f"http://{HOST}:{PORT}/.well-known/agent-card.json")
    yield room
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(autouse=True)
def _reset(bridge):
    bridge.calls.clear()
    bridge.raises = None
    bridge.reply = {"ok": True, "seq": 7, "topic": "announcements"}


def _send(text: str) -> str:
    return send_hello(f"http://{HOST}:{PORT}", text)


def test_card_names_the_board_skill_and_is_not_a_controller():
    card = httpx.get(f"http://{HOST}:{PORT}/.well-known/agent-card.json", timeout=5).json()
    assert card["name"] == "flossi0ullk-a2a-room-bridge"
    assert [s["id"] for s in card["skills"]] == ["coordination_board"]


def test_post_reaches_the_room_with_a_prefixed_agent_id(bridge: FakeRoom):
    reply = json.loads(_send("post #announcements shipped it"))
    assert reply == {"ok": True, "seq": 7, "topic": "announcements"}
    assert bridge.calls == [
        (
            "room_broadcast",
            {"agent_id": "a2a:anonymous", "text": "shipped it", "topic": "announcements"},
        )
    ]


def test_json_post_cannot_choose_a_bare_harness_name(bridge: FakeRoom):
    _send('{"op": "post", "text": "hi", "sender": "claude", "evidence_refs": ["file:a.md"], "reply_to": 2}')
    tool, args = bridge.calls[0]
    assert tool == "room_broadcast"
    assert args["agent_id"] == "a2a:claude"
    assert args["evidence_refs"] == ["file:a.md"]
    assert args["reply_to"] == 2


def test_read_and_topics_map_to_room_tools(bridge: FakeRoom):
    bridge.reply = {"ok": True, "events": []}
    assert json.loads(_send("read #claims since=4")) == {"ok": True, "events": []}
    assert json.loads(_send("topics")) == {"ok": True, "events": []}
    assert bridge.calls == [
        ("room_read", {"since_seq": 4, "limit": 20, "topic": "claims"}),
        ("room_topics", {}),
    ]


def test_bad_command_never_reaches_the_room(bridge: FakeRoom):
    assert _send("please claim a.py for me").startswith("error: commands:")
    assert bridge.calls == []


def test_room_error_is_reported_as_error_not_success(bridge: FakeRoom):
    bridge.reply = {"ok": False, "error": "topic must match [a-z0-9][a-z0-9_-]{0,31}"}
    assert _send("post #claims hi").startswith("error: topic must match")


def test_unreachable_room_is_reported(bridge: FakeRoom):
    bridge.raises = RoomUnavailable("room at http://127.0.0.1:7334/mcp did not answer (OSError)")
    assert _send("topics").startswith("error: room at")
```

```python
"""Invariants: the bridge is a client of the room, not a second writer.

Production change that would make these fail: the bridge importing the room
package (and so opening events.jsonl with its own seq counter), claiming or
releasing paths over A2A, or taking Hermes' port.
"""

from __future__ import annotations

import ast
from pathlib import Path

import packages.a2a_mesh.room_bridge as bridge

_SOURCE = Path(bridge.__file__).read_text(encoding="utf-8")


def test_bridge_imports_nothing_from_the_room_package():
    tree = ast.parse(_SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("packages.coordination_room")
        elif isinstance(node, ast.Import):
            assert not any(a.name.startswith("packages.coordination_room") for a in node.names)


def test_bridge_calls_only_post_read_topics_tools():
    called = {
        node.value
        for node in ast.walk(ast.parse(_SOURCE))
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("room_")
    }
    assert called == {"room_topics", "room_read", "room_broadcast"}


def test_default_port_is_not_hermes_a2a_port():
    assert bridge.DEFAULT_PORT != 9900


def test_agent_name_is_not_a_controller():
    assert bridge.AGENT_NAME == "flossi0ullk-a2a-room-bridge"
```

```python
"""A2A client -> bridge -> real FastMCP room -> events.jsonl and BOARD.md.

Production change that would make this fail: the bridge writing anywhere but
through the room's own MCP tools, or the A2A post not reaching the board.
"""

from __future__ import annotations

import importlib
import json
import threading
import time
from pathlib import Path

import httpx
import pytest
import uvicorn

pytest.importorskip("mcp")

from packages.a2a_mesh.client import send_hello  # noqa: E402
from packages.a2a_mesh.room_bridge import McpRoomPort, build_app  # noqa: E402

HOST, ROOM_PORT, BRIDGE_PORT = "127.0.0.1", 19997, 19996


def _serve(app, port: int) -> tuple[uvicorn.Server, threading.Thread]:
    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            httpx.get(f"http://{HOST}:{port}/", timeout=1)
            return server, thread
        except httpx.HTTPError:
            time.sleep(0.1)
    raise AssertionError(f"port {port} never came up")


def test_a2a_post_lands_on_the_room_board(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("COORDINATION_ROOM_ROOT", str(tmp_path))
    monkeypatch.setenv("COORDINATION_ROOM_LOG", str(tmp_path / "rooms" / "events.jsonl"))
    monkeypatch.setenv("FLOSS_AUDIT_DIR", str(tmp_path / "audit"))
    import packages.coordination_room.server as module

    room_server = importlib.reload(module)
    room_srv, room_thread = _serve(room_server.mcp.streamable_http_app(), ROOM_PORT)
    port = McpRoomPort(f"http://{HOST}:{ROOM_PORT}/mcp")
    bridge_srv, bridge_thread = _serve(build_app(HOST, BRIDGE_PORT, port), BRIDGE_PORT)
    try:
        reply = json.loads(
            send_hello(f"http://{HOST}:{BRIDGE_PORT}", "post #inquiries who owns the bridge?")
        )
        assert reply["ok"] is True
        assert reply["topic"] == "inquiries"
        topics = json.loads(send_hello(f"http://{HOST}:{BRIDGE_PORT}", "topics"))
        assert [t["topic"] for t in topics["topics"]] == ["inquiries"]
    finally:
        bridge_srv.should_exit = True
        room_srv.should_exit = True
        bridge_thread.join(timeout=5)
        room_thread.join(timeout=5)

    rows = [
        json.loads(line)
        for line in (tmp_path / "rooms" / "events.jsonl").read_text(encoding="utf-8").split("\n")
        if line
    ]
    assert len(rows) == 1
    assert rows[0]["agent_id"] == "a2a:anonymous"
    assert rows[0]["topic"] == "inquiries"
    assert "who owns the bridge?" in (tmp_path / "rooms" / "BOARD.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run them to see them fail.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/a2a_mesh/tests/test_room_bridge_parse.py`
Expected: collection error, `ModuleNotFoundError: No module named 'packages.a2a_mesh.room_bridge'`.

- [ ] **Step 3: Write the implementation.**

```python
"""A2A skill adapter for the coordination room board.

A client of the room, never a writer: the room daemon (:7334) owns events.jsonl
(one writer per surface), so this module speaks to it over MCP and imports
nothing from packages.coordination_room. A2A is a peer handshake here, not a
controller; the bridge posts and reads, and never claims or releases a path.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any, Protocol

import uvicorn
from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TaskState,
)
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from starlette.applications import Starlette

AGENT_NAME = "flossi0ullk-a2a-room-bridge"
# 9900 is Hermes' own A2A listener (gateway.platforms.a2a); never reuse it.
DEFAULT_PORT = 7335
ROOM_URL = "http://127.0.0.1:7334/mcp"
DEFAULT_READ_LIMIT = 20
READ_LIMIT_MAX = 100
SENDER_MAX = 32

_TOPIC = r"[a-z0-9][a-z0-9_-]{0,31}"
_POST = re.compile(rf"post\s+#(?P<topic>{_TOPIC})\s+(?P<text>.+)", re.S)
_READ = re.compile(rf"read(?:\s+#(?P<topic>{_TOPIC}))?(?:\s+since=(?P<since>\d+))?")
_OPS = ("post", "read", "topics")
USAGE = (
    "commands: `topics` | `read [#topic] [since=N]` | `post #topic text` | "
    'JSON {"op": "post|read|topics", "topic", "text", "evidence_refs", '
    '"reply_to", "since_seq", "limit", "sender"}'
)


class CommandError(ValueError):
    """The A2A message is not a board command."""


class RoomUnavailable(RuntimeError):
    """The room daemon did not answer."""


@dataclass(frozen=True)
class BoardCommand:
    op: str
    topic: str | None = None
    text: str = ""
    evidence_refs: tuple[str, ...] = ()
    reply_to: int | None = None
    since_seq: int = 0
    limit: int = DEFAULT_READ_LIMIT
    sender: str = "anonymous"


def agent_id_for(sender: str) -> str:
    """A2A callers are unauthenticated: always prefixed so they cannot pose as a harness."""
    clean = re.sub(r"[^A-Za-z0-9_.-]", "-", sender)[:SENDER_MAX]
    return f"a2a:{clean or 'anonymous'}"


def _parse_json(body: str) -> BoardCommand:
    try:
        obj = json.loads(body)
    except json.JSONDecodeError as exc:
        raise CommandError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(obj, dict) or obj.get("op") not in _OPS:
        raise CommandError(USAGE)
    refs = obj.get("evidence_refs") or []
    if not isinstance(refs, list) or not all(isinstance(r, str) for r in refs):
        raise CommandError("evidence_refs must be a list of strings")
    try:
        reply_to = int(obj["reply_to"]) if obj.get("reply_to") is not None else None
        since_seq = int(obj.get("since_seq", 0))
        limit = int(obj.get("limit", DEFAULT_READ_LIMIT))
    except (TypeError, ValueError) as exc:
        raise CommandError("reply_to, since_seq and limit must be integers") from exc
    topic, text, sender = obj.get("topic"), obj.get("text", ""), obj.get("sender", "anonymous")
    if topic is not None and not isinstance(topic, str):
        raise CommandError("topic must be a string")
    if not isinstance(text, str) or not isinstance(sender, str):
        raise CommandError("text and sender must be strings")
    if obj["op"] == "post" and not text.strip():
        raise CommandError("post needs text")
    return BoardCommand(
        op=obj["op"],
        topic=topic,
        text=text.strip(),
        evidence_refs=tuple(refs),
        reply_to=reply_to,
        since_seq=since_seq,
        limit=max(1, min(limit, READ_LIMIT_MAX)),
        sender=sender,
    )


def parse_command(raw: str) -> BoardCommand:
    """Deterministic grammar. Anything else is an error, never a guess."""
    body = raw.strip()
    if not body:
        raise CommandError("empty command")
    if body.startswith("{"):
        return _parse_json(body)
    if body == "topics":
        return BoardCommand(op="topics")
    match = _POST.fullmatch(body)
    if match:
        return BoardCommand(op="post", topic=match["topic"], text=match["text"].strip())
    match = _READ.fullmatch(body)
    if match:
        return BoardCommand(
            op="read", topic=match["topic"], since_seq=int(match["since"] or 0)
        )
    raise CommandError(USAGE)


class RoomPort(Protocol):
    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class McpRoomPort:
    """Calls the room's MCP tools over streamable HTTP. One short session per call."""

    def __init__(self, url: str = ROOM_URL) -> None:
        self._url = url

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            async with streamable_http_client(self._url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool(tool, arguments)
            return json.loads(result.content[0].text)
        except Exception as exc:  # anyio wraps transport errors in ExceptionGroup
            raise RoomUnavailable(
                f"room at {self._url} did not answer ({type(exc).__name__})"
            ) from exc


async def run_command(port: RoomPort, command: BoardCommand) -> dict[str, Any]:
    if command.op == "topics":
        return await port.call("room_topics", {})
    if command.op == "read":
        args: dict[str, Any] = {"since_seq": command.since_seq, "limit": command.limit}
        if command.topic:
            args["topic"] = command.topic
        return await port.call("room_read", args)
    args = {"agent_id": agent_id_for(command.sender), "text": command.text}
    if command.topic:
        args["topic"] = command.topic
    if command.evidence_refs:
        args["evidence_refs"] = list(command.evidence_refs)
    if command.reply_to is not None:
        args["reply_to"] = command.reply_to
    return await port.call("room_broadcast", args)


class _BoardExecutor(AgentExecutor):
    def __init__(self, room: RoomPort) -> None:
        self._room = room

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)
        updater = TaskUpdater(
            event_queue=event_queue, task_id=task.id, context_id=task.context_id
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("Processing request..."),
        )
        raw = get_message_text(context.message) if context.message else ""
        try:
            reply = await run_command(self._room, parse_command(raw))
            failure = None if reply.get("ok", True) else str(reply.get("error", "room error"))
        except (CommandError, RoomUnavailable) as exc:
            reply, failure = None, str(exc)
        if failure is not None:
            await updater.add_artifact(
                parts=[new_text_part(text=f"error: {failure}", media_type="text/plain")]
            )
            await updater.update_status(
                state=TaskState.TASK_STATE_FAILED,
                message=new_text_message(failure),
            )
            return
        await updater.add_artifact(
            parts=[
                new_text_part(
                    text=json.dumps(reply, ensure_ascii=False), media_type="text/plain"
                )
            ]
        )
        await updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("Request is completed!"),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancel is not supported.")


def build_app(host: str, port: int, room: RoomPort) -> Starlette:
    base = f"http://{host}:{port}"
    skill = AgentSkill(
        id="coordination_board",
        name="Coordination board",
        description="Post to and read the FLOSSI0ULLK coordination room board.",
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["coordination", "board"],
        examples=["topics", "read #announcements", "post #inquiries who owns packages/x?"],
    )
    card = AgentCard(
        name=AGENT_NAME,
        description="Post/read bridge to the coordination room. Cannot claim or release paths.",
        version="0.0.1",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC", url=base, protocol_version="1.0"
            )
        ],
        skills=[skill],
    )
    handler = DefaultRequestHandler(
        agent_executor=_BoardExecutor(room),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    routes = []
    routes.extend(create_agent_card_routes(card))
    routes.extend(create_jsonrpc_routes(handler, "/"))
    return Starlette(routes=routes)


def serve_room_bridge(host: str, port: int, room: RoomPort) -> None:
    """Serve the bridge on loopback. Blocks."""
    if host != "127.0.0.1":
        raise ValueError("serve_room_bridge binds 127.0.0.1 only")
    uvicorn.run(
        build_app(host, port, room),
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    from packages.mcp_daemon import claim_singleton

    if not claim_singleton("a2a_room_bridge.pid"):
        print("[FLOSS A2A] room bridge already running; exiting.", file=sys.stderr)
        raise SystemExit(0)
    serve_room_bridge(
        "127.0.0.1",
        int(os.environ.get("A2A_ROOM_BRIDGE_PORT", DEFAULT_PORT)),
        McpRoomPort(os.environ.get("COORDINATION_ROOM_URL", ROOM_URL)),
    )
```

- [ ] **Step 4: Run both packages.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/coordination_room/tests packages/a2a_mesh/tests`
Expected: `112 passed, 1 skipped`. The e2e test starts a real FastMCP room and the bridge in-process and takes about 10 seconds.

- [ ] **Step 5: Lint.**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m ruff check packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_parse.py packages/a2a_mesh/tests/test_room_bridge_pair.py packages/a2a_mesh/tests/test_room_bridge_invariants.py packages/a2a_mesh/tests/test_room_bridge_e2e.py`
Expected: `All checks passed!`

- [ ] **Step 6: Commit.**

```bash
git add -- packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_parse.py packages/a2a_mesh/tests/test_room_bridge_pair.py packages/a2a_mesh/tests/test_room_bridge_invariants.py packages/a2a_mesh/tests/test_room_bridge_e2e.py
git commit -F- -- packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_parse.py packages/a2a_mesh/tests/test_room_bridge_pair.py packages/a2a_mesh/tests/test_room_bridge_invariants.py packages/a2a_mesh/tests/test_room_bridge_e2e.py <<'EOF'
feat(a2a-mesh): room bridge, A2A post/read as a client of the room
EOF
```

---

### Task 8: Daemon wiring

**Files:**
- Edit: `scripts/start_mcp_daemons.ps1`
- Edit: `scripts/stop_mcp_daemons.ps1`
- Edit: `docs/agent-memory/project/coordination-room-v0.md`

**Interfaces:**
- Consumes: `Start-Daemon <python> <module> <label> <cwd>`, `$skipped`, `$py`, `$workspace` already defined in the start script; the `$pidFiles` array in the stop script.
- Produces: bridge daemon on `127.0.0.1:7335`, PID file `a2a_room_bridge.pid`.

If `a2a-sdk` is missing from the daemon's Python, the bridge exits at import; `Start-Daemon` reports it and the script adds it to `$skipped` instead of aborting. That is the intended failure mode.

- [ ] **Step 1: Edit `start_mcp_daemons.ps1`.** After the room block, replace:

```powershell
if (-not $roomProc) { $skipped += "coordination room (:7334) - exited immediately after launch" }
```

with:

```powershell
if (-not $roomProc) { $skipped += "coordination room (:7334) - exited immediately after launch" }

# Start A2A room bridge (port 7335). A client of the room on :7334: it never
# writes the log. :9900 is Hermes' own A2A listener, so it is not reused here.
$bridgeProc = Start-Daemon $py "packages.a2a_mesh.room_bridge" "A2A room bridge (:7335)" $workspace
if (-not $bridgeProc) { $skipped += "A2A room bridge (:7335) - exited immediately after launch" }
```

Then replace the summary line:

```powershell
Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, coordination room :7334, omniroute :20128). PID guard prevents duplicates."
```

with:

```powershell
Write-Host "[FLOSS MCP] Daemons started (consensus :7331, ensemble :7332, coordination room :7334, A2A room bridge :7335, omniroute :20128). PID guard prevents duplicates."
```

- [ ] **Step 2: Edit `stop_mcp_daemons.ps1`.** Replace:

```powershell
$pidFiles = @("consensus.pid", "reasoning_ensemble.pid", "coordination_room.pid")
```

with:

```powershell
$pidFiles = @("consensus.pid", "reasoning_ensemble.pid", "coordination_room.pid", "a2a_room_bridge.pid")
```

and in the header comment replace `coordination room (:7334), OmniRoute (:20128).` with `coordination room (:7334), A2A room bridge (:7335), OmniRoute (:20128).`

- [ ] **Step 3: Parse-check both scripts.**

```powershell
foreach ($f in 'scripts/start_mcp_daemons.ps1', 'scripts/stop_mcp_daemons.ps1') { $e = $null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $f), [ref]$null, [ref]$e) | Out-Null; "$f errors: $($e.Count)" }
```

Expected: both `errors: 0`.

- [ ] **Step 4: Live smoke.** Needs an operator go-ahead because it starts and stops machine daemons. From the worktree: run `scripts/start_mcp_daemons.ps1`, then:

```bash
curl -s http://127.0.0.1:7335/.well-known/agent-card.json
env -u PYTHONPATH C:/Python313/python.exe -c "from packages.a2a_mesh.client import send_hello; print(send_hello('http://127.0.0.1:7335', 'post #announcements bridge smoke test'))"
```

Expected: an Agent Card named `flossi0ullk-a2a-room-bridge`; a JSON reply with `"ok": true`; a new row in `.agent-surface/rooms/default/events.jsonl` with `agent_id` `a2a:anonymous`; the post visible in `BOARD.md` under `### #announcements`. Then run `scripts/stop_mcp_daemons.ps1` and confirm `a2a_room_bridge.pid` is gone from `~/.floss_agent`.

- [ ] **Step 5: Correct the how-to.** In `docs/agent-memory/project/coordination-room-v0.md` replace:

```
- Not A2A (task handshake) — `feat/a2a-harness-mesh`.
```

with:

```
- Not A2A (task handshake). An optional A2A bridge (`packages/a2a_mesh/room_bridge.py`, `127.0.0.1:7335`) can post and read as `a2a:<sender>`; it cannot claim or release.
```

Then re-run `env -u PYTHONPATH C:/Python313/python.exe scripts/materialize_shared_agent_memory.py --check` and handle drift exactly as in Task 5 Step 6 (never `--include-user-scope`).

- [ ] **Step 6: Commit.**

```bash
git add -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 docs/agent-memory/project/coordination-room-v0.md
git commit -F- -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 docs/agent-memory/project/coordination-room-v0.md <<'EOF'
feat(daemons): start and stop the A2A room bridge on :7335
EOF
```

---

## Final verification

- [ ] `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded` (the coordination-v1 green set): no new failures versus the base. Record the base number first by running the same command in a clean worktree of `feat/coordination-room-rebased`.
- [ ] `ruff check packages/coordination_room packages/a2a_mesh/room_bridge.py packages/a2a_mesh/tests/test_room_bridge_*.py` clean. (`packages/a2a_mesh/tests/test_helloworld_pair.py` already carries one unused `import pytest` from the merged branch; leave it, it is not this plan's file.)
- [ ] `spec_gate.py --check`: the same three findings as Task 0, no new ones.
- [ ] Open the PR from `feat/room-board-v1`. Do not merge into `feat/coordination-room`.

## Decisions left to the operator

1. **The waiver** in Task 0 Step 1. Without it nothing here starts.
2. **Untracked log.** `.agent-surface/rooms/default/events.jsonl` is untracked and not ignored in the root repo today, so it already shows in `git status`; `BOARD.md` will add a second untracked file that changes on every post. Either ignore `.agent-surface/rooms/` in the root `.gitignore` or accept the noise. This plan does not touch the root repo.
3. **Evidence root.** `file:` refs resolve under the room root, which the daemon sets to the FLOSS checkout. A ref to a workspace-root file outside FLOSS is `unresolved` by design.
4. **Identity.** MCP-side `agent_id` is as unauthenticated as before. The bridge only prevents A2A callers from posing as a harness (`a2a:` prefix); it does not authenticate anyone.
5. **Scale.** `render_board` re-reads the whole log on each mutation. Fine at today's log size (5 rows); revisit with an incremental board if the log passes a few thousand rows.

## Self-review

- **Spec coverage.** Draft items map as follows: `log.py` fields to `**fields` on the existing `EventLog.append` (no edit needed); `board.py` to Task 3; `room.py`/`gateway.py`/`server.py` to Tasks 4 and 5; `test_board.py`/`test_room.py` to Tasks 3 and 4 (new files, `test_room.py` untouched); spec/schema to Task 1; `a2a_mesh` port to Task 6; `room_bridge.py` to Task 7; daemon scripts to Task 8; topics, evidence refs, thread ids, intent, roster, auto-updating board each have a test. The draft's `message_type`, `room_post`, `[VERIFIED]`, `:9900` and `limit=50` are deliberately not implemented (table above).
- **Placeholders.** None: every file body is inlined from files that were executed.
- **Type consistency.** `board_path`, `evidence_status`, `evidence_checked`, `thread_id`, `reply_to`, `topic_of`, `resolve_all` and `agent_id_for` are spelled identically across tasks, the schema, and the tests.
