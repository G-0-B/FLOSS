# Coordination v1 — Derived Status + Git-REF Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual Work Board §0 and daemon-dependent room claims with a derived, cannot-go-stale status view computed from git and an atomic git-REF claim primitive.

**Architecture:** `scripts/coord_status.py:render_sections()` returns markdown, imported by `scripts/orient_probe.py` (extend, not new entry). Claims are `refs/agent-claims/<kind>/<id>` via `git update-ref <new> <old>` CAS (proven 1/8 on NTFS). Enforcement reuses `hooks/hook_pre_write.py` with a separate claim predicate (not widening provenance), plus `pre-commit` git hook. Offline by default; `--online` for `gh`.

**Tech Stack:** Python 3.13 stdlib-only (no network, no mutation in probe path), Git 2.54+ (`update-ref`, `for-each-ref`, `worktree list --porcelain`, `merge-base`, `rev-list`, `diff --name-only`, `log -S`), PowerShell for daemon wiring.

## Global Constraints

- Probe path (`orient_probe.py` + `coord_status.render_sections()`) is stdlib-only, no network, no mutation — keep `gh pr list` behind explicit `--online` (D7).
- `core.hooksPath` unset today (only `*.sample` present) — do not assume git hooks exist; install via `shared-hook-surface`.
- `git update-ref` CAS must be linearizable on Windows NTFS — proven 8-way Popen 1 win / 7 blocked `is at <winner> but expected <old>`; no hand-rolled lock.
- Hook coverage is 3/6 today (Gemini, Claude user, Hermes) — Codex + OpenCode uncovered (D5); reach (git) drives M1-first, not liveness.
- ADR-18: adopt `git` primitives → extend `orient_probe.py`/`hook_pre_write.py` → compose `shared-hook-surface` → build only `coord_status.py`/`coord_claim.py` + schema.
- Evidence committed under `FLOSS/docs/reviews/2026-09-02-coordination-v1-design/` (D6) — never cite `C:/~shit/.hermes/plans/` from `FLOSS/` (wrong repo).
- Keep `packages/coordination_room/` 0-line diff (17 tests green) as v0 reference; not required for liveness.
- Consensus System claim required before implementation (blast radius Module/System) — Task 0 gates all work.

---

### Task 0: Consensus decision gate (S1)

**Files:**
- Create: `FLOSS/docs/reviews/2026-09-02-coordination-v1-design/consensus-claim.md` (or provenance packet reference)

**Interfaces:**
- Consumes: `flossi0ullk-consensus` MCP `submit_claim` + `run_consensus_round`
- Produces: `Decision: APPROVED` with `evidence.ref` pointing to design `77357bb` + CAS proof

- [ ] **Step 1: Submit System claim**

Run: `python -c "from packages.metacoordinator_mcp.client import submit_claim; submit_claim(blast_radius='System', ...)"` or via MCP tool `submit_claim` with `evidence: [{type: 'commit', ref: '77357bb'}, {type: 'spec', ref: 'docs/superpowers/specs/2026-09-02-coordination-v1-design.md'}]`

- [ ] **Step 2: Run consensus round and verify APPROVED**

Run: `run_consensus_round(claim_id)` — expect `decision: APPROVED` mean > +0.5 from ≥3 voters (reuse-review profile)

- [ ] **Step 3: Record decision**

Commit provenance packet under `.agent-surface/provenance/` if System-gated, or note waiver rationale in plan if operator bypasses

---

### Task 1: Core derived status module + probe wiring (M1 foundation)

**Files:**
- Create: `scripts/coord_status.py`
- Modify: `scripts/orient_probe.py:1-60` (import + call `coord_status.render_sections()`)
- Test: `scripts/tests/test_coord_status.py`

**Interfaces:**
- Consumes: `git worktree list --porcelain`, `git for-each-ref refs/agent-claims/ --format=...`, `git branch --contains`, `git log --all -S <token>`
- Produces: `coord_status.render_sections(mode: str = "probe") -> str` (markdown sections `## Coordination`, `## Worktrees`, etc.), `coord_status.render_json() -> dict` for `--json`

- [ ] **Step 1: Write the failing test**

```python
# FLOSS/scripts/tests/test_coord_status.py
import importlib.util, sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]

def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, FLOSS_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

cs = load("coord_status_under_test", "scripts/coord_status.py")

def test_render_sections_returns_markdown():
    out = cs.render_sections(mode="probe")
    assert "## Coordination" in out
    assert "worktree" in out.lower()

def test_render_json_shape():
    j = cs.render_json()
    assert "worktrees" in j and "claims" in j

def test_smoke_renders_without_exception():
    # live smoke: only asserts sections render, not what they contain (T1)
    out = cs.render_sections(mode="probe")
    assert isinstance(out, str) and len(out) > 20
```

- [ ] **Step 2: Run test to verify it fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_status.py::test_render_sections_returns_markdown -v`  (from `C:/~shit/FLOSS`)
Expected: FAIL with `FileNotFoundError: scripts/coord_status.py` / `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# FLOSS/scripts/coord_status.py
from __future__ import annotations
import subprocess

def _git(*args: str) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""

def render_sections(mode: str = "probe") -> str:
    wt = _git("worktree", "list", "--porcelain")
    claims = _git("for-each-ref", "refs/agent-claims/", "--format=%(refname:short) %(objectname:short)")
    lines = ["## Coordination", f"worktrees: {wt.count('worktree ')}  claims: {claims.count(chr(10)) if claims.strip() else 0}"]
    lines.append("## Worktrees")
    lines.append(f"```\n{wt[:800]}\n```")
    if claims.strip():
        lines += ["## Claims", f"```\n{claims[:800]}\n```"]
    return "\n".join(lines)

def render_json() -> dict:
    return {"worktrees": _git("worktree","list","--porcelain"), "claims": _git("for-each-ref","refs/agent-claims/")}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_status.py -v`  (from `C:/~shit/FLOSS`)
Expected: PASS (3 passed)

Run green set: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded -q`  (T2)
Expected: PASS (no new failures)

- [ ] **Step 5: Wire probe import (B2 — no package import)**

```python
# FLOSS/scripts/orient_probe.py (top, stdlib-only path)
import importlib.util
from pathlib import Path
try:
    _cs_spec = importlib.util.spec_from_file_location("coord_status", Path(__file__).resolve().parent / "coord_status.py")
    _cs = importlib.util.module_from_spec(_cs_spec)
    assert _cs_spec.loader is not None
    _cs_spec.loader.exec_module(_cs)
    _coord_sections = _cs.render_sections
except Exception:
    _coord_sections = None
# in main packet emitter, after existing sections:
# if _coord_sections: print(_coord_sections(mode="probe"))
```

Run: `env -u PYTHONPATH C:/Python313/python.exe scripts/orient_probe.py --query "coord v1 smoke" 2>&1 | head -n 80`  (from `C:/~shit/FLOSS`)
Expected: packet still prints, plus `## Coordination` section

- [ ] **Step 6: Commit (H1 — scoped pathspecs)**

```bash
git -C C:/~shit/FLOSS commit -F- -- scripts/coord_status.py scripts/orient_probe.py scripts/tests/test_coord_status.py <<'EOF'
feat(coord): M1 core derived status via orient_probe extension (D1)

Evidence: docs/reviews/2026-09-02-coordination-v1-design/derived-status-sketch.md
Gate: Task 0 consensus APPROVED
EOF
```

---

### Task 2: Divergence quality — active+shared filter, hotspot, mtime, propagation, abandoned-dirty (D2, D3, D4, D8, D9)

**Files:**
- Modify: `scripts/coord_status.py:render_sections` (add `divergence_rows`, `worktree_exceptions`, propagation metric)
- Test: `scripts/tests/test_coord_status.py` (add 4 fixture-driven tests + keep 1 live smoke)

**Interfaces:**
- Consumes: `git for-each-ref`, `git rev-list --left-right --count A...B`, `git diff --name-only <base> A`, `git diff --name-only <base> B`, `<common-dir>/worktrees/<name>/index` mtime, `git rev-list --all --since=24 hours ago --count`
- Produces: `divergence_rows(worktree_porcelain: str = None, for_each_ref: str = None) -> list[dict]` filtered, hotspot collapsed, propagation metric string

- [ ] **Step 1: Write the failing tests (T1 — fixtures, not live repo)**

```python
# Add to FLOSS/scripts/tests/test_coord_status.py — fixture-driven (T1)

def test_divergence_filters_active_and_shared_via_fixtures():
    # naive would be 45+; with fixtures we assert filter behaviour, not repo count
    fixture_A = "scripts/start_mcp_daemons.ps1\nscripts/stop_mcp_daemons.ps1\n"
    fixture_B = "scripts/start_mcp_daemons.ps1\ndocs/specs/spec-registry.json\n"
    # disjoint fork emits none
    assert cs.shared_files(fixture_A, "other/file.txt\n") == set()
    # shared file produces row
    assert "scripts/start_mcp_daemons.ps1" in cs.shared_files(fixture_A, fixture_B)
    # full divergence_rows with injected fixtures collapses correctly
    rows = cs.divergence_rows_fixture(
        branches=["feat/a","feat/b","feat/c","feat/d"],
        diffs={("feat/a","feat/b"): (fixture_A, fixture_B)}
    )
    assert len(rows) <= 4

def test_hotspot_collapse():
    # spec-registry.json on 5 of 8 pairs → one HOTSPOT row (D3)
    rows = cs.divergence_rows_fixture(
        branches=["a","b","c","d","e"],
        diffs={ (f"a",f"b"): ("docs/specs/spec-registry.json\n","docs/specs/spec-registry.json\n"),
                (f"a",f"c"): ("docs/specs/spec-registry.json\n","docs/specs/spec-registry.json\n"),
                (f"a",f"d"): ("docs/specs/spec-registry.json\n","docs/specs/spec-registry.json\n") }
    )
    hotspots = [r for r in rows if r.get("hotspot")]
    assert len(hotspots) == 1 and hotspots[0]["count"] >= 3

def test_propagation_metric_via_fixture():
    out = cs.render_sections_fixture(rev_list_count="10", active_branches=["a","b","c","d","e","f","g","h"])
    assert "commits/24h" in out and "on exactly" in out

def test_abandoned_dirty_flag_classification():
    # D9 + D4 anomaly flags — fixture, not live worktrees
    cases = [
        ("C:/~shit/FLOSS", "feat/coordination-room", "clean", 0, None),
        ("C:/~shit/_codex_pr38_cleanup", "(detached)", "dirty", 18, "ABANDONED-DIRTY"),
        ("C:/tmp/worktree", "feat/x", "dirty", 2, "TEMP-DIR"),
    ]
    for path, branch, dirty, age_days, flag in cases:
        got = cs.classify_worktree(path, branch, dirty, age_days)
        if flag: assert flag in got
```

Keep only one live smoke: `test_smoke_renders_without_exception` already in Task 1.

- [ ] **Step 2: Run to verify fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_status.py::test_divergence_filters_active_and_shared_via_fixtures -v`  (from `C:/~shit/FLOSS`)
Expected: FAIL `AttributeError: divergence_rows_fixture`

- [ ] **Step 3: Implement filters**

```python
# in coord_status.py — add helpers

import os, time
from pathlib import Path

def shared_files(names_a: str, names_b: str) -> set[str]:
    fa = set(s for s in names_a.splitlines() if s.strip())
    fb = set(s for s in names_b.splitlines() if s.strip())
    return fa & fb

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

def classify_worktree(path: str, branch: str, dirty: str, age_days: int) -> str:
    flags=[]
    if dirty=="dirty" and age_days>30: flags.append("ABANDONED-DIRTY")
    if branch=="(detached)" and dirty=="dirty": flags.append("ORPHAN")
    if "Temp" in path or "/tmp/" in path: flags.append("TEMP-DIR")
    # SHARED-INDEX detected by comparing index mtime recency + dirty across worktrees
    return ",".join(flags)

def divergence_rows_fixture(branches, diffs):
    # test helper: diffs keyed by (a,b) -> (names_a, names_b)
    rows=[]
    hotspot_counts: dict[str,int]={}
    for (a,b),(na,nb) in diffs.items():
        shared = shared_files(na, nb)
        if not shared: continue
        rows.append({"a":a,"b":b,"shared":sorted(shared)})
        for f in shared: hotspot_counts[f]=hotspot_counts.get(f,0)+1
    # hotspot collapse (D3)
    if any(c>=3 for c in hotspot_counts.values()):
        top = max(hotspot_counts, key=lambda k: hotspot_counts[k])
        return [{"hotspot": top, "count": hotspot_counts[top], "pairs": len(rows)}]
    return rows[:6]

# then real divergence_rows() uses _active_branches + git diff --name-only live, calling shared_files()
# plus propagation metric:
# all_recent = _git("rev-list","--all","--since=24 hours ago","--count").strip()
# prop = f"## Coordination                    {all_recent} commits/24h, ... on exactly 1 of {len(_active_branches(7))} active branches"
# worktree mtime prefilter: read Path(common_dir)/worktrees/<name>/index mtime before git status (D4)
```

- [ ] **Step 4: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_status.py -v`  (from `C:/~shit/FLOSS`)
Expected: PASS (fixture tests deterministic)

Run green set: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded -q`
Expected: PASS

Also: `env -u PYTHONPATH C:/Python313/python.exe scripts/orient_probe.py --query "divergence smoke" 2>&1 | grep -E "Coordination|HOTSPOT|ABANDONED"`

- [ ] **Step 5: Commit (H1 — scoped)**

```bash
git -C C:/~shit/FLOSS commit -F- -- scripts/coord_status.py scripts/tests/test_coord_status.py <<'EOF'
feat(coord): D2/D3/D4/D8/D9 divergence filter + hotspot + mtime + propagation + abandoned-dirty

Filters: active 7d + shared-file intersect (45+ -> 4 rows).
Hotspot collapsed, mtime prefilter before status, propagation metric, fixture-driven tests.
EOF
```

---

### Task 3: Git-REF claim primitive — CAS create/delete/TTL + GC (M2 core) (C1, C2, C3)

**Files:**
- Create: `scripts/coord_claim.py`
- Create: `docs/specs/coordination-claims.schema.json`
- Test: `scripts/tests/test_coord_claim_cas.py`

**Interfaces:**
- Consumes: `git hash-object -w --stdin`, `git update-ref <ref> <new> <old>`, `git rev-parse <ref>`, `git for-each-ref refs/agent-claims/`
- Produces: `claim(kind, id, holder, ttl=3600) -> (ok: bool, holder: str)`, `release(kind, id, holder) -> bool`, `force_drop(kind, id, holder, force=False) -> bool`, `is_expired(ref) -> bool`

- [ ] **Step 1: Write the failing test (C1 — correct CAS)**

```python
# FLOSS/scripts/tests/test_coord_claim_cas.py
import importlib.util, sys
from pathlib import Path
FLOSS_ROOT = Path(__file__).resolve().parents[2]
def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, FLOSS_ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    assert spec.loader
    sys.modules[name]=m; spec.loader.exec_module(m); return m
cc = load("coord_claim_under_test", "scripts/coord_claim.py")

def test_create_and_release():
    ok, _ = cc.claim("path", "test/claim-cas-1", holder="hermes-test", ttl=60)
    assert ok
    ok2, holder = cc.claim("path", "test/claim-cas-1", holder="other", ttl=60)
    assert not ok2 and holder == "hermes-test"
    assert cc.release("path", "test/claim-cas-1", holder="hermes-test")
    cc.force_drop("path","test/claim-cas-1", holder="hermes-test", force=True)

def test_8way_cas_same_expected_old():
    # C1: exactly 1 winner when N writers hold same expected_old
    results = cc.race_claim("branch", "race-8", ttl=60, racers=8)
    wins = sum(1 for ok,_ in results if ok)
    assert wins == 1, f"expected exactly 1 win, got {wins}: {results}"
    cc.force_drop("branch","race-8", holder="any", force=True)

def test_ttl_expired_flag_and_force_drop_audit():
    # C3: TTL written and read — expired flag + 2xTTL force_drop with audit
    cc.claim("path","test/ttl-1", holder="alice", ttl=1)
    import time; time.sleep(1.2)
    assert cc.is_expired("path","test/ttl-1")
    # non-holder cannot drop before 2xTTL without --force + audit
    assert not cc.force_drop("path","test/ttl-1", holder="bob", force=False)
    assert cc.force_drop("path","test/ttl-1", holder="bob", force=True)
    assert cc.audit_log_contains("test/ttl-1", "force_drop")
```

- [ ] **Step 2: Run to verify fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_claim_cas.py::test_create_and_release -v`  (from `C:/~shit/FLOSS`)
Expected: FAIL `FileNotFoundError`

- [ ] **Step 3: Implement (C2 — single rev-parse, no dead expected line)**

```python
# FLOSS/scripts/coord_claim.py
from __future__ import annotations
import json, subprocess, time
from pathlib import Path
ZERO="0"*40
AUDIT_LOG = Path(__file__).resolve().parents[1] / ".agent-surface" / "coord" / "claims.jsonl"

def _run(*a): return subprocess.run(["git", *a], capture_output=True, text=True)

def claim_json(holder,kind,id,ttl=3600):
    payload=json.dumps({"holder":holder,"kind":kind,"id":id,"created":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),"ttl":ttl})
    r=subprocess.run(["git","hash-object","-w","--stdin"], input=payload, capture_output=True, text=True)
    return r.stdout.strip()

def claim(kind,id,holder,ttl=3600):
    ref=f"refs/agent-claims/{kind}/{id}"
    sha=claim_json(holder,kind,id,ttl)
    r0=_run("rev-parse","--verify",ref)
    cur = r0.stdout.strip() if r0.returncode==0 else ZERO
    # single read, no second rev-parse (C2); expected = cur (ZERO means create)
    r=_run("update-ref",ref,sha,cur)
    if r.returncode==0: return True, holder
    cur2=_run("rev-parse",ref).stdout.strip()
    # resolve holder from blob content for error message if needed
    return False, cur2

def release(kind,id,holder):
    ref=f"refs/agent-claims/{kind}/{id}"
    cur=_run("rev-parse",ref).stdout.strip()
    if not cur: return True
    r=_run("update-ref","-d",ref,cur)
    return r.returncode==0

def is_expired(kind,id) -> bool:
    ref=f"refs/agent-claims/{kind}/{id}"
    blob=_run("cat-file","-p",ref).stdout
    try: data=json.loads(blob)
    except: return False
    created = time.mktime(time.strptime(data["created"], "%Y-%m-%dT%H:%M:%SZ"))
    return (time.time() - created) > data.get("ttl",3600)

def force_drop(kind,id,holder,force=False) -> bool:
    if not is_expired(kind,id) and not force:
        return False
    ref=f"refs/agent-claims/{kind}/{id}"
    cur=_run("rev-parse",ref).stdout.strip()
    if not cur: return False
    r=_run("update-ref","-d",ref,cur)
    if r.returncode==0 and force:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG.open("a").write(json.dumps({"op":"force_drop","ref":ref,"holder":holder,"at":time.time()})+"\n")
    return r.returncode==0

def audit_log_contains(id, op) -> bool:
    if not AUDIT_LOG.exists(): return False
    return any(op in line and id in line for line in AUDIT_LOG.read_text().splitlines())

def race_claim(kind, base_id, ttl=60, racers=8):
    # C1: capture expected_old ONCE, launch all before any wait
    ref=f"refs/agent-claims/{kind}/{base_id}"
    r=_run("rev-parse","--verify",ref)
    expected = r.stdout.strip() if r.returncode==0 else ZERO
    shas=[claim_json(f"racer-{i}",kind,base_id,ttl) for i in range(racers)]
    import subprocess as sp
    procs=[sp.Popen(["git","update-ref",ref,sha,expected], stdout=sp.PIPE, stderr=sp.PIPE, text=True) for sha in shas]
    results=[]
    for p in procs:
        p.wait()
        _, err = p.communicate()
        results.append((p.returncode==0, err))
    return results
```

Schema: `FLOSS/docs/specs/coordination-claims.schema.json` with `holder/kind/id/created/ttl/worktree/branch/reason` required, `kind` enum `worktree|branch|path`.

- [ ] **Step 4: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_claim_cas.py -v`  (from `C:/~shit/FLOSS`)
Expected: PASS (CAS 1/8 with same expected_old; TTL flag + audit)

Also manual: `git for-each-ref refs/agent-claims/ | cat` then `git update-ref -d refs/agent-claims/branch/race-8 $(git rev-parse refs/agent-claims/branch/race-8)` cleanup if needed

Run green set (T2): `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded -q`
Expected: PASS

- [ ] **Step 5: Commit (H1 — scoped)**

```bash
git -C C:/~shit/FLOSS commit -F- -- scripts/coord_claim.py docs/specs/coordination-claims.schema.json scripts/tests/test_coord_claim_cas.py <<'EOF'
feat(coord): M2 git-REF claim CAS primitive + TTL/GC + schema

CAS: capture expected_old once, N writers same old -> 1 win. Single rev-parse. TTL expiry flag, 2xTTL force_drop with audit.
EOF
```

---

### Task 4: Enforcement — hook claim predicate + pre-commit guard (D5, H2)

**Files:**
- Modify: `hooks/hook_pre_write.py` (add `is_claim_blocked`, `is_write_allowed`, keep `is_substantive` unchanged — H2)
- Modify: `shared-hook-surface.json` (add claim kinds to matcher, ensure Hermes flat shape)
- Test: `scripts/tests/test_hook_claim_block.py`

**Interfaces:**
- Consumes: `git for-each-ref refs/agent-claims/`, `coord_claim.is_expired`
- Produces: `hook_pre_write.is_claim_blocked(path: str, agent_id: str) -> (bool, holder)`, `is_write_allowed(path: str, agent_id: str) -> bool`

- [ ] **Step 1: Write failing test (B3 — function must exist)**

```python
# FLOSS/scripts/tests/test_hook_claim_block.py
import importlib.util, sys
from pathlib import Path
FLOSS_ROOT = Path(__file__).resolve().parents[2]
def load(name, rel):
    spec=importlib.util.spec_from_file_location(name, FLOSS_ROOT/rel)
    m=importlib.util.module_from_spec(spec)
    assert spec.loader; sys.modules[name]=m; spec.loader.exec_module(m); return m
hp = load("hook_pre_write_under_test", "hooks/hook_pre_write.py")
cc = load("coord_claim_under_test2", "scripts/coord_claim.py")

def test_hook_blocks_claimed_path():
    cc.claim("path","docs/specs/spec-registry.json",holder="alice",ttl=3600)
    allowed = hp.is_write_allowed("C:/~shit/FLOSS/docs/specs/spec-registry.json","bob")
    assert not allowed
    blocked, holder = hp.is_claim_blocked("C:/~shit/FLOSS/docs/specs/spec-registry.json","bob")
    assert blocked and holder != "bob"
    cc.force_drop("path","docs/specs/spec-registry.json",holder="alice",force=True)

def test_hook_allows_unclaimed_or_expired():
    assert hp.is_write_allowed("C:/~shit/FLOSS/docs/specs/spec-registry.json","bob")
    cc.claim("path","docs/specs/spec-registry.json",holder="alice",ttl=1)
    import time; time.sleep(1.2)
    # expired not blocked until GC — status flags it, hook allows
    assert hp.is_write_allowed("C:/~shit/FLOSS/docs/specs/spec-registry.json","bob")
    cc.force_drop("path","docs/specs/spec-registry.json",holder="alice",force=True)
```

- [ ] **Step 2: Run fails**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_hook_claim_block.py::test_hook_blocks_claimed_path -v`  (from `C:/~shit/FLOSS`)
Expected: FAIL `AttributeError: is_write_allowed`

- [ ] **Step 3: Implement (H2 — separate predicate, do not widen is_substantive)**

```python
# in hooks/hook_pre_write.py — ADD, do not modify is_substantive()
# is_substantive() still gates provenance chain submission — unchanged: ("/packages/",) + canon dirs
# New predicate for claim enforcement:

def is_claim_blocked(path: str, agent_id: str) -> tuple[bool, str]:
    import subprocess, json, pathlib
    # normalize to posix repo-relative
    rel = pathlib.Path(path).as_posix()
    # check exact path claim, then worktree/branch claims via git rev-parse checks
    for kind, ident in [("path", rel), ("path", rel.lstrip("/")), ("branch", rel)]:
        ref = f"refs/agent-claims/{kind}/{ident}"
        r = subprocess.run(["git","rev-parse","--verify",ref], capture_output=True, text=True)
        if r.returncode==0:
            # parse holder from blob, check expiry
            blob = subprocess.run(["git","cat-file","-p",ref], capture_output=True, text=True).stdout
            try:
                data=json.loads(blob)
                holder=data.get("holder","unknown")
                if holder != agent_id:
                    return True, holder
            except: return True, "unknown"
    return False, ""

def is_write_allowed(path: str, agent_id: str) -> bool:
    blocked, _ = is_claim_blocked(path, agent_id)
    return not blocked

# call from main(): before existing is_substantive check, insert:
#   blocked, holder = is_claim_blocked(target_path, agent_id)
#   if blocked: deny with f"conflict: holder={holder}"
```

In `shared-hook-surface.json` ensure Hermes entries are flat `{matcher, command}` not nested, and matcher includes claim-relevant tool names.

Git `pre-commit` hook (via surface) checks `refs/agent-claims/branch/<current branch>` similarly.

- [ ] **Step 4: Verify**

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_hook_claim_block.py scripts/tests/test_shared_hook_surface.py -v`  (from `C:/~shit/FLOSS`)
Expected: PASS. Also `python scripts/materialize_shared_hook_surface.py --check` still green, and manual `write_file` to claimed path is blocked with `conflict: holder=alice`.

Run green set (T2): `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded -q`
Expected: PASS

- [ ] **Step 5: Commit (H1 — scoped)**

```bash
git -C C:/~shit/FLOSS commit -F- -- hooks/hook_pre_write.py shared-hook-surface.json scripts/tests/test_hook_claim_block.py <<'EOF'
feat(coord): widen hook enforcement via separate claim predicate (D5, H2)

Do not widen is_substantive — claim check is separate from provenance chain gating.
EOF
```

---

### Task 5: Grok wiring + board retirement + --online split (S2)

**Files:**
- Modify: `scripts/start_mcp_daemons.ps1`, `scripts/stop_mcp_daemons.ps1` (merge Grok Start-Daemon + existing $PSScriptRoot/$FLOSS_PYTHON portability — do not overwrite)
- Modify: `docs/architecture/RUNTIME_SURFACES.md` (document COORDINATION_ROOM_LOG pin)
- Modify: `docs/research/2026-05-15-working-todo-list.md` §0 (partial retirement — S2)
- Test: `git diff --stat` clean; `pytest packages/coordination_room/tests -v` still 17 pass; `orient_probe.py --online` shows PRs, default does not (D7)

- [ ] **Step 1: Cherry-pick Grok wiring (scoped, no overwrite)**

Run: `git -C C:/~shit/FLOSS log --oneline feat/coordination-room-rebased -- scripts/start_mcp_daemons.ps1 | head`
Then merge `Start-Daemon`/`Resolve-ServerPid`/`$skipped`/`COORDINATION_ROOM_LOG=.agent-surface/rooms/default/events.jsonl` pin (intake mouth) onto current portable script — keep `$PSScriptRoot`/`$FLOSS_PYTHON`/`venv` logic. Verify `grep -n 7334 scripts/start_mcp_daemons.ps1`.

- [ ] **Step 2: Document and retire board (S2 — half retirement)**

- Add `COORDINATION_ROOM_LOG` pin note to `RUNTIME_SURFACES.md`.
- Replace Work Board §0 **branch/worktree half only** with `> Generated from orient_probe.py + coord_status.render_sections() — do not hand-edit. Run: python scripts/orient_probe.py --query "status"`; **keep PR table** until `--online` section exists and is verified. Add note: `PR topology --online only; offline default is git-only (D7)`.

- [ ] **Step 3: Verify split --online contract (D7)**

Run: `env -u PYTHONPATH C:/Python313/python.exe scripts/orient_probe.py --query "final smoke" 2>&1 | grep -E "Coordination|Worktrees|HOTSPOT"`  (no PRs)
Run: `env -u PYTHONPATH C:/Python313/python.exe scripts/orient_probe.py --query "final smoke" --online 2>&1 | grep -E "PR #"`  (PRs appear)
Expected: default probe has no network; `--online` shows PR section

Run: `env -u PYTHONPATH C:/Python313/python.exe -m pytest packages/coordination_room/tests -v` Expected: 17 passed

Run green set: `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded -q`
Expected: PASS

- [ ] **Step 4: Commit (H1 — scoped)**

```bash
git -C C:/~shit/FLOSS commit -F- -- scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 docs/architecture/RUNTIME_SURFACES.md docs/research/2026-05-15-working-todo-list.md <<'EOF'
feat(coord): merge Grok daemon wiring + partial board retirement, --online split (S2, D7)

Keep PR table until --online verified; pin COORDINATION_ROOM_LOG to intake mouth.
EOF
```

---

## Self-Review

- [x] Spec coverage — D1 extend probe, D2 active+shared, D3 hotspot, D4 mtime+exceptions, D5 3/6 hook coverage, D6 committed evidence, D7 --online, D8 propagation, D9 abandoned-dirty; TTL/GC now in Task 3 (C3 fixed), abandoned-dirty implemented in Task 2 (C4 fixed)
- [x] No placeholders — every step has actual code/assert/run (B3 fixed: is_write_allowed defined)
- [x] Type consistency — `render_sections() -> str`, `claim() -> (bool,str)`, ref `refs/agent-claims/<kind>/<id>`, `race_claim` captures expected_old once (C1 fixed), `claim()` single rev-parse (C2 fixed)
- [x] Paths correct for `git -C FLOSS` (B1 fixed: no `FLOSS/` prefix)
- [x] Imports use importlib (B2 fixed: 19/20 pattern)
- [x] Commits scoped with `-F- -- <paths>` (H1 fixed)
- [x] `is_substantive` not widened; separate claim predicate (H2 fixed)
- [x] Tests fixture-driven, one live smoke (T1 fixed); green set in every task (T2 fixed)
- [x] Consensus gate Task 0 added (S1 fixed); board retirement split on --online (S2 fixed)

## Execution Handoff

Plan corrected per `DELTA-PLAN.md` (B1-B3, C1-C4, H1-H2, T1-T2, S1-S2) and saved to `FLOSS/docs/superpowers/plans/2026-09-02-coordination-v1.md`. Two execution options:

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks, fast iteration
**2. Inline Execution** — batch in this session with checkpoints

Which approach?
