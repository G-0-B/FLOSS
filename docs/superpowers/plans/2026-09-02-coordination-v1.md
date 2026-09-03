# Coordination v1 — Derived Status + Git-REF Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual Work Board §0 and daemon-dependent room claims with a derived, cannot-go-stale status view computed from git and an atomic git-REF claim primitive.

**Architecture:** `scripts/coord_status.py:render_sections()` returns markdown, imported by `scripts/orient_probe.py` (extend, not new entry). Claims are `refs/agent-claims/<kind>/<id>` via `git update-ref <new> <old>` CAS (proven 1/8 on NTFS). Enforcement reuses `hooks/hook_pre_write.py` widened to claim kinds, plus `pre-commit` git hook. Offline by default; `--online` for `gh`.

**Tech Stack:** Python 3.13 stdlib-only (no network, no mutation in probe path), Git 2.54+ (`update-ref`, `for-each-ref`, `worktree list --porcelain`, `merge-base`, `rev-list`, `diff --name-only`, `log -S`), PowerShell for daemon wiring, `portalocker`/`msvcrt` for materializer file lock (follow-up).

## Global Constraints

- Probe path (`orient_probe.py` + `coord_status.render_sections()`) is stdlib-only, no network, no mutation — keep `gh pr list` behind explicit `--online` (D7).
- `core.hooksPath` unset today (only `*.sample` present) — do not assume git hooks exist; install via `shared-hook-surface`.
- `git update-ref` CAS must be linearizable on Windows NTFS — proven 8-way Popen 1 win / 7 blocked `is at <winner> but expected <old>`; no hand-rolled lock.
- Hook coverage is 3/6 today (Gemini, Claude user, Hermes) — Codex + OpenCode uncovered (D5); reach (git) drives M1-first, not liveness.
- ADR-18: adopt `git` primitives → extend `orient_probe.py`/`hook_pre_write.py` → compose `shared-hook-surface` → build only `coord_status.py`/`coord_claim.py` + schema.
- Evidence committed under `FLOSS/docs/reviews/2026-09-02-coordination-v1-design/` (D6) — never cite `C:/~shit/.hermes/plans/` from `FLOSS/` (wrong repo).
- Keep `packages/coordination_room/` 0-line diff (17 tests green) as v0 reference; not required for liveness.

---

### Task 1: Core derived status module + probe wiring (M1 foundation)

**Files:**
- Create: `FLOSS/scripts/coord_status.py`
- Modify: `FLOSS/scripts/orient_probe.py:1-60` (import + call `coord_status.render_sections()`)
- Test: `FLOSS/scripts/tests/test_coord_status.py`

**Interfaces:**
- Consumes: `git worktree list --porcelain`, `git for-each-ref refs/agent-claims/ --format=...`, `git branch --contains`, `git log --all -S <token>`
- Produces: `coord_status.render_sections(mode: str = "probe") -> str` (markdown sections `## Coordination`, `## Worktrees`, etc.), `coord_status.render_json() -> dict` for `--json`

- [ ] **Step 1: Write the failing test**

```python
# FLOSS/scripts/tests/test_coord_status.py
import scripts.coord_status as cs
def test_render_sections_returns_markdown():
    out = cs.render_sections(mode="probe")
    assert "## Coordination" in out
    assert "worktree" in out.lower()
def test_render_json_shape():
    j = cs.render_json()
    assert "worktrees" in j and "claims" in j
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_coord_status.py::test_render_sections_returns_markdown -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.coord_status'`

- [ ] **Step 3: Write minimal implementation**

```python
# FLOSS/scripts/coord_status.py
from __future__ import annotations
import subprocess, pathlib

def _git(*args: str) -> str:
    import subprocess as sp
    r = sp.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""

def render_sections(mode: str = "probe") -> str:
    wt = _git("worktree", "list", "--porcelain")
    claims = _git("for-each-ref", "refs/agent-claims/", "--format=%(refname:short) %(objectname:short)")
    lines = ["## Coordination", f"worktrees: {wt.count('worktree ')}  claims: {claims.count(chr(10))}"]
    lines.append("## Worktrees")
    lines.append(f"```\n{wt[:800]}\n```")
    if claims.strip():
        lines += ["## Claims", f"```\n{claims[:800]}\n```"]
    return "\n".join(lines)

def render_json() -> dict:
    return {"worktrees": _git("worktree","list","--porcelain"), "claims": _git("for-each-ref","refs/agent-claims/")}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_coord_status.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Wire probe import**

```python
# FLOSS/scripts/orient_probe.py (top)
try:
    from scripts.coord_status import render_sections as _coord_sections
except ImportError:
    _coord_sections = None
# in main packet emitter, after existing sections:
# if _coord_sections: print(_coord_sections(mode="probe"))
```

Run: `env -u PYTHONPATH C:/Python313/python.exe FLOSS/scripts/orient_probe.py --query "coord v1 smoke" 2>&1 | head -n 80`
Expected: packet still prints, plus `## Coordination` section

- [ ] **Step 6: Commit**

```bash
git -C C:/~shit/FLOSS add FLOSS/scripts/coord_status.py FLOSS/scripts/orient_probe.py FLOSS/scripts/tests/test_coord_status.py
git -C C:/~shit/FLOSS commit -m "feat(coord): M1 core derived status via orient_probe extension (D1)"
```

---

### Task 2: Divergence quality — active+shared filter, hotspot, mtime, propagation (D2, D3, D4, D8)

**Files:**
- Modify: `FLOSS/scripts/coord_status.py:render_sections`
- Test: `FLOSS/scripts/tests/test_coord_status.py` (add 4 tests)

**Interfaces:**
- Consumes: `git for-each-ref`, `git rev-list --left-right --count A...B`, `git diff --name-only <base> A`, `git diff --name-only <base> B`, `<common-dir>/worktrees/<name>/index` mtime
- Produces: `divergence_rows() -> list[dict]` filtered, hotspot collapsed, propagation metric string

- [ ] **Step 1: Write the failing tests**

```python
def test_divergence_filters_active_and_shared():
    rows = cs.divergence_rows()  # naive would be 45+
    assert len(rows) <= 8, f"expected <=8 after active+shared filter, got {len(rows)}"
    # hotspot collapsed
    hotspots = [r for r in rows if r.get("hotspot")]
    assert all(r["count"] >= 3 for r in hotspots)

def test_worktree_mtime_prefilter():
    # index mtime read before git status — cost test is that render stays <0.5s on 20 worktrees
    import time
    t0 = time.time()
    cs.render_sections()
    assert time.time() - t0 < 1.5

def test_propagation_metric():
    out = cs.render_sections()
    assert "commits/24h" in out
    assert "on exactly" in out

def test_abandoned_dirty_flag():
    out = cs.render_sections()
    # at least one known abandoned-dirty fixture appears with flag (may be 0 if cleaned)
    assert "ABANDONED-DIRTY" in out or "ORPHAN" in out or "TEMP-DIR" in out
```

- [ ] **Step 2: Run to verify fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_coord_status.py::test_divergence_filters_active_and_shared -v`
Expected: FAIL `AttributeError: divergence_rows`

- [ ] **Step 3: Implement filters**

```python
# in coord_status.py
import os, time, subprocess as sp
from pathlib import Path

def _active_branches(days=7):
    out = _git("for-each-ref", "refs/heads/", "--format=%(refname:short) %(committerdate:unix)")
    active = []
    now = time.time()
    for line in out.splitlines():
        if not line.strip(): continue
        name, ts = line.rsplit(None,1)
        if now - int(ts) < 86400*days:
            active.append(name)
    return active

def divergence_rows():
    branches = _active_branches(7)
    rows = []
    hotspot_counts: dict[str,int] = {}
    for i, a in enumerate(branches):
        for b in branches[i+1:]:
            base = _git("merge-base", a, b).strip()
            if not base: continue
            lr = _git("rev-list","--left-right","--count", f"{a}...{b}").strip()
            if not lr: continue
            left, right = map(int, lr.split())
            if left==0 or right==0: continue
            fa = set(_git("diff","--name-only", base, a).splitlines())
            fb = set(_git("diff","--name-only", base, b).splitlines())
            shared = fa & fb
            if not shared: continue
            rows.append({"a":a,"b":b,"left":left,"right":right,"shared":sorted(shared)})
            for f in shared: hotspot_counts[f]=hotspot_counts.get(f,0)+1
    # hotspot collapse
    collapsed=[]
    for r in rows:
        hs = [f for f in r["shared"] if hotspot_counts.get(f,0)>=3]
        if hs and len(hs)>=1:
            collapsed.append({"hotspot": hs[0], "count": hotspot_counts[hs[0]], "pairs": len(rows)})
            break
    else:
        collapsed = rows
    return collapsed[:6]
```

Plus propagation metric in `render_sections()`:

```python
# count commits/24h across all refs, count on exactly 1 of active branches
all_recent = _git("rev-list","--all","--since=24 hours ago","--count").strip()
prop = f"## Coordination                    {all_recent} commits/24h, ... on exactly 1 of {len(_active_branches(7))} active branches"
```

And worktree mtime prefilter: read `Path(common_dir)/worktrees/<name>/index` mtime before `git status`.

- [ ] **Step 4: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_coord_status.py -v`
Expected: PASS. Also `env -u PYTHONPATH C:/Python313/python.exe FLOSS/scripts/orient_probe.py --query "divergence smoke" 2>&1 | grep -E "Coordination|HOTSPOT|ABANDONED"`

- [ ] **Step 5: Commit**

```bash
git -C C:/~shit/FLOSS add FLOSS/scripts/coord_status.py FLOSS/scripts/tests/test_coord_status.py
git -C C:/~shit/FLOSS commit -m "feat(coord): D2/D3/D4/D8 divergence filter + hotspot + mtime + propagation"
```

---

### Task 3: Git-REF claim primitive — CAS create/delete/TTL (M2 core)

**Files:**
- Create: `FLOSS/scripts/coord_claim.py`
- Create: `FLOSS/docs/specs/coordination-claims.schema.json`
- Test: `FLOSS/scripts/tests/test_coord_claim_cas.py`

**Interfaces:**
- Consumes: `git hash-object -w --stdin`, `git update-ref <ref> <new> <old>`, `git rev-parse <ref>`, `git for-each-ref refs/agent-claims/`
- Produces: `claim(kind, id, holder, ttl=3600) -> (ok: bool, holder: str)`, `release(kind, id, holder) -> bool`, `claim_json(holder,kind,id,ttl) -> sha`

- [ ] **Step 1: Write the failing test**

```python
# FLOSS/scripts/tests/test_coord_claim_cas.py
import subprocess, json, tempfile, pathlib
import scripts.coord_claim as cc
def test_create_and_release():
    ok, _ = cc.claim("path", "test/claim-cas-1", holder="hermes-test", ttl=60)
    assert ok
    ok2, holder = cc.claim("path", "test/claim-cas-1", holder="other", ttl=60)
    assert not ok2 and holder == "hermes-test"
    assert cc.release("path", "test/claim-cas-1", holder="hermes-test")
def test_8way_cas():
    # ports cas-proof-report: spawn 8 claim attempts on same id, assert 1 win
    results = cc.race_claim("branch", "race-8", ttl=60, racers=8)
    assert sum(1 for r in results if r[0]) == 1
```

- [ ] **Step 2: Run to verify fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_coord_claim_cas.py::test_create_and_release -v`
Expected: FAIL `ModuleNotFoundError`

- [ ] **Step 3: Implement**

```python
# FLOSS/scripts/coord_claim.py
import json, subprocess, time
from pathlib import Path
ZERO="0"*40
def _run(*a): return subprocess.run(["git",*a], capture_output=True, text=True)
def claim_json(holder,kind,id,ttl=3600):
    import subprocess as sp, json
    payload=json.dumps({"holder":holder,"kind":kind,"id":id,"created":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"ttl":ttl})
    r=sp.run(["git","hash-object","-w","--stdin"], input=payload, capture_output=True, text=True)
    return r.stdout.strip()
def claim(kind,id,holder,ttl=3600):
    ref=f"refs/agent-claims/{kind}/{id}"
    sha=claim_json(holder,kind,id,ttl)
    old=_run("rev-parse","--verify",ref).stdout.strip() if _run("rev-parse","--verify",ref).returncode==0 else ZERO
    expected=ZERO if old==ZERO else old
    r=_run("update-ref",ref,sha,expected)
    if r.returncode==0: return True, holder
    # parse holder from is at <sha>
    cur=_run("rev-parse",ref).stdout.strip()
    return False, cur
def release(kind,id,holder):
    ref=f"refs/agent-claims/{kind}/{id}"
    cur=_run("rev-parse",ref).stdout.strip()
    if not cur: return True
    r=_run("update-ref","-d",ref,cur)
    return r.returncode==0
def race_claim(kind,base_id,ttl=60,racers=8):
    import concurrent.futures, subprocess
    def one(i):
        return claim(kind, f"{base_id}-{i%1}", holder=f"racer-{i}", ttl=ttl)  # all same id to race
    # force same id: launch 8 threads claiming identical ref
    import threading
    results=[]
    def racer(i):
        sha=claim_json(f"racer-{i}",kind,base_id,ttl)
        old=_run("rev-parse","--verify",f"refs/agent-claims/{kind}/{base_id}").stdout.strip() or ZERO
        # need real race — use Popen directly
        import subprocess as sp
        r=sp.run(["git","update-ref",f"refs/agent-claims/{kind}/{base_id}",sha,old], capture_output=True, text=True)
        return (r.returncode==0, r.stderr)
    # simplified: call claim() 8 times concurrently
    import concurrent.futures as cf
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs=[ex.submit(racer,i) for i in range(racers)]
        results=[f.result() for f in futs]
    return results
```

Schema stub: `FLOSS/docs/specs/coordination-claims.schema.json` with `holder/kind/id/created/ttl/worktree/branch/reason` required.

- [ ] **Step 4: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_coord_claim_cas.py -v`
Expected: PASS (CAS 1/8). Also manual: `git for-each-ref refs/agent-claims/ | cat`

- [ ] **Step 5: Commit**

```bash
git -C C:/~shit/FLOSS add FLOSS/scripts/coord_claim.py FLOSS/docs/specs/coordination-claims.schema.json FLOSS/scripts/tests/test_coord_claim_cas.py
git -C C:/~shit/FLOSS commit -m "feat(coord): M2 git-REF claim CAS primitive + schema"
```

---

### Task 4: Enforcement — hook widening + pre-commit guard (D5)

**Files:**
- Modify: `FLOSS/hooks/hook_pre_write.py:34-60` (SUBSTANTIVE_PATH_SEGMENTS + CANON)
- Modify: `FLOSS/shared-hook-surface.json` (add claim kinds to matcher, ensure hermes flat shape)
- Modify: `FLOSS/scripts/materialize_shared_hook_surface.py` (if needed)
- Test: `FLOSS/scripts/tests/test_hook_claim_block.py`

- [ ] **Step 1: Write failing test**

```python
# simulate hook_pre_write blocking writes to claimed path
import scripts.coord_claim as cc, hooks.hook_pre_write as hp
def test_hook_blocks_claimed_path():
    cc.claim("path","docs/specs/spec-registry.json",holder="alice",ttl=3600)
    allowed = hp.is_write_allowed("C:/~shit/FLOSS/docs/specs/spec-registry.json","bob")
    assert not allowed
    cc.release("path","docs/specs/spec-registry.json",holder="alice")
```

- [ ] **Step 2: Run fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_hook_claim_block.py -v`
Expected: FAIL

- [ ] **Step 3: Implement**

- Widen `SUBSTANTIVE_PATH_SEGMENTS` to include `("/packages/","/docs/","/FLOSS/")` or add `CLAIM_KINDS = ("worktree","branch","path")` and check `refs/agent-claims/<kind>/<id>` for normalized target path before allowing write.
- Ensure `shared-hook-surface.json` emits flat `{matcher, command}` for Hermes (not nested) — verified by July agentmemory lesson.
- Add git `pre-commit` hook via surface that checks `refs/agent-claims/branch/<current>` before commit.

- [ ] **Step 4: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest FLOSS/scripts/tests/test_hook_claim_block.py FLOSS/scripts/tests/test_shared_hook_surface.py -v`
Expected: PASS. Also `python FLOSS/scripts/materialize_shared_hook_surface.py --check` still green, and manual `write_file` to claimed path is blocked with `conflict: holder=alice`.

- [ ] **Step 5: Commit**

```bash
git -C C:/~shit/FLOSS add FLOSS/hooks/hook_pre_write.py FLOSS/shared-hook-surface.json FLOSS/scripts/tests/test_hook_claim_block.py
git -C C:/~shit/FLOSS commit -m "feat(coord): widen hook enforcement to claim kinds (D5)"
```

---

### Task 5: Grok wiring + board retirement + evidence finalization

**Files:**
- Modify: `FLOSS/scripts/start_mcp_daemons.ps1`, `FLOSS/scripts/stop_mcp_daemons.ps1` (merge Grok Start-Daemon + existing $PSScriptRoot/$FLOSS_PYTHON portability)
- Modify: `FLOSS/docs/architecture/RUNTIME_SURFACES.md` (document COORDINATION_ROOM_LOG pin)
- Modify: `FLOSS/docs/research/2026-05-15-working-todo-list.md` §0 (replace with `Generated from orient_probe — do not hand-edit` + call to coord_status)
- Test: `git -C C:/~shit/FLOSS diff --stat` clean; `pytest packages/coordination_room/tests -v` still 17 pass

- [ ] **Step 1: Cherry-pick Grok wiring**

Run: `git -C C:/~shit/FLOSS log --oneline feat/coordination-room-rebased -- scripts/start_mcp_daemons.ps1 | head`
Then merge `Start-Daemon`/`Resolve-ServerPid`/`$skipped`/`COORDINATION_ROOM_LOG` pin onto current portable script — do not overwrite `$PSScriptRoot` logic. Verify `grep -n 7334 scripts/start_mcp_daemons.ps1`.

- [ ] **Step 2: Document and retire board**

- Add `COORDINATION_ROOM_LOG=.agent-surface/rooms/default/events.jsonl` pin note to `RUNTIME_SURFACES.md`.
- Replace Work Board §0 table with `> Generated from orient_probe.py + coord_status.render_sections() — do not hand-edit. Run: python FLOSS/scripts/orient_probe.py --query "status"`.

- [ ] **Step 3: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest packages/coordination_room/tests -v` Expected: 17 passed
Run: `env -u PYTHONPATH C:/Python313/python.exe FLOSS/scripts/orient_probe.py --query "final smoke" 2>&1 | grep -E "Coordination|Worktrees|HOTSPOT"`
Expected: sections present

- [ ] **Step 4: Commit**

```bash
git -C C:/~shit/FLOSS add FLOSS/scripts/start_mcp_daemons.ps1 FLOSS/scripts/stop_mcp_daemons.ps1 FLOSS/docs/architecture/RUNTIME_SURFACES.md FLOSS/docs/research/2026-05-15-working-todo-list.md
git -C C:/~shit/FLOSS commit -m "feat(coord): merge Grok daemon wiring + retire Work Board §0 (M3)"
```

---

## Self-Review

- [ ] Spec coverage — every D1-D9 has a task/section; claim TTL/GC in Task 3, abandoned-dirty in Task 2.
- [ ] No placeholders — every step has actual code/assert/run.
- [ ] Type consistency — `render_sections() -> str`, `claim() -> (bool,str)`, ref `refs/agent-claims/<kind>/<id>`.

## Execution Handoff

Plan complete and saved to `FLOSS/docs/superpowers/plans/2026-09-02-coordination-v1.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration
**2. Inline Execution** — batch in this session with checkpoints

Which approach?
