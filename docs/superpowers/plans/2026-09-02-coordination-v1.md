# Coordination v1 — Derived Status + Git-REF Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual Work Board §0 and daemon-dependent room claims with a derived, cannot-go-stale status view computed from git and an atomic git-REF claim primitive.

**Architecture:** `scripts/coord_status.py:render_sections()` returns markdown; `orient_probe.py` loads it via `importlib` (extend, not a new entry). Claims are `refs/agent-claims/<kind>/<id>` via `git update-ref <new> <old>` CAS. Enforcement is a **separate** `is_claim_blocked` predicate (do not widen `is_substantive`). Offline by default; `--online` is an **added** probe flag, not present today.

**Tech Stack:** Python 3.13 stdlib-only on the probe path; Git 2.54+; PowerShell for daemon wiring.

## Global Constraints

- Probe path is stdlib-only, no network, no mutation. `gh pr list` only behind `--online` (D7). That flag **does not exist yet** — Task 5 adds it; do not assume it.
- Execute **all** implementation from an isolated worktree: `git worktree add .worktrees/coord-v1 -b feat/coord-v1 feat/coordination-room`. Do not implement in `C:/~shit/FLOSS` while it has ~55 foreign dirty files (B11). `scripts/orient_probe.py` is already dirty there.
- New-file commits: `git add -- <paths> && git commit -F- -- <paths>` (B10). Never `git commit -m` after a broad add. Never `commit --` an untracked path without `add` first.
- `scripts/` is not a package (`__init__.py` absent). Load modules with `importlib.util.spec_from_file_location`. `FLOSS_ROOT = Path(__file__).resolve().parents[2]` from `scripts/tests/`.
- `git -C C:/~shit/FLOSS` pathspecs have **no** `FLOSS/` prefix (B1).
- Hook coverage 3/6; Codex uncovered (D5). Reach drives M1-first.
- Evidence lives in `docs/reviews/2026-09-02-coordination-v1-design/` (D6). Workspace `.agent-surface` is `C:/~shit/.agent-surface` = `FLOSS` parent (C10).
- Keep `packages/coordination_room/` unchanged (0-line vs rebased). 17 tests remain green.
- Do **not** start Task 1 until Task 0 is APPROVED or a written operator waiver exists in the review directory (S1). No silent skip.
- Green set every verify step (from FLOSS root):
  `env -u PYTHONPATH C:/Python313/python.exe -m pytest -q packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded`

---

### Task 0: Consensus decision gate (S1 / B12)

**Files:**
- Create: `docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md` (record of claim_id / waiver)

**Interfaces:**
- Consumes: `packages.metacoordinator_mcp.server.submit_claim` **or** MCP tool `submit_claim`. There is **no** `packages.metacoordinator_mcp.client`.
- Signature: `submit_claim(proposer, proposal_type, summary, body, blast_radius, evidence=None) -> str`
- `evidence` items use `ref` (not `path`/`url`). Types: `spec | commit | adr | test | url | provenance_packet`.
- System/SpecChange/AdrChange fail-closed without provenance (`E_GOVERNED_PROVENANCE_REQUIRED`).

- [ ] **Step 1: Submit the claim (real API, no placeholders)**

From FLOSS root, `FLOSS_MODEL_BACKEND=litellm` (do not route voters through OmniRoute):

```python
from packages.metacoordinator_mcp.server import submit_claim
print(submit_claim(
    proposer="hermes-coord-v1",
    proposal_type="SpecChange",
    summary="Coordination v1: derived status via orient_probe + git-REF claims",
    body="Design docs/superpowers/specs/2026-09-02-coordination-v1-design.md. CAS proof in docs/reviews/2026-09-02-coordination-v1-design/cas-proof-report.md.",
    blast_radius="System",
    evidence=[
        {"type": "spec", "ref": "docs/superpowers/specs/2026-09-02-coordination-v1-design.md"},
        {"type": "commit", "ref": "a43f59cdb7f3d2882bc889cf98a5f6c3036968f8"},
        {"type": "test", "ref": "docs/reviews/2026-09-02-coordination-v1-design/cas-proof-report.md"},
    ],
))
```

If this returns `E_GOVERNED_PROVENANCE_REQUIRED`, attach a validated provenance packet with `consent_ref` (operator explicit go) and resubmit. Do not invent `client.py`.

- [ ] **Step 2: Round + record**

Run `run_consensus_round` on the claim_id. Write `docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md` with claim_id, mean, decision.

If operator waives: write the waiver in that same file (who, when, why) and **stop Task 0**. Do not treat absence of a round as APPROVED.

- [ ] **Step 3: Commit (B10)**

```bash
git add -- docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md
git commit -F- -- docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md <<'EOF'
docs(coord): record coordination-v1 consensus decision or waiver
EOF
```

---

### Task 1: Core derived status module + probe wiring (M1)

**Files:**
- Create: `scripts/coord_status.py`
- Modify: `scripts/orient_probe.py` (isolated worktree copy only)
- Test: `scripts/tests/test_coord_status.py`

**Interfaces:**
- Produces: `render_sections(mode: str = "probe") -> str`, `render_json() -> dict`

- [ ] **Step 1: Failing test** (importlib, not `import scripts`)

```python
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
    out = cs.render_sections(mode="probe")
    assert isinstance(out, str) and len(out) > 20
```

- [ ] **Step 2: Run — expect fail**

From FLOSS (or worktree) root:
`env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_status.py::test_render_sections_returns_markdown -v`
Expected: FAIL (`FileNotFoundError` / missing module)

- [ ] **Step 3: Minimal impl**

```python
# scripts/coord_status.py
from __future__ import annotations
import subprocess
from pathlib import Path

def _git(*args: str, cwd: Path | None = None) -> str:
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd)
    return r.stdout if r.returncode == 0 else ""

def render_sections(mode: str = "probe") -> str:
    wt = _git("worktree", "list", "--porcelain")
    claims = _git("for-each-ref", "refs/agent-claims/", "--format=%(refname:short) %(objectname:short)")
    n_wt = wt.count("worktree ")
    n_cl = len([ln for ln in claims.splitlines() if ln.strip()])
    lines = ["## Coordination", f"worktrees: {n_wt}  claims: {n_cl}", "## Worktrees", f"```\n{wt[:800]}\n```"]
    if claims.strip():
        lines += ["## Claims", f"```\n{claims[:800]}\n```"]
    return "\n".join(lines)

def render_json() -> dict:
    return {"worktrees": _git("worktree", "list", "--porcelain"), "claims": _git("for-each-ref", "refs/agent-claims/")}
```

- [ ] **Step 4: Tests + green set**

`env -u PYTHONPATH C:/Python313/python.exe -m pytest scripts/tests/test_coord_status.py -v`
Then the green-set command from Global Constraints.

- [ ] **Step 5: Probe load — fail loud if file exists (C9)**

In `orient_probe.py`, after argparse setup / before emit:

```python
import importlib.util
from pathlib import Path
_cs_path = Path(__file__).resolve().parent / "coord_status.py"
_coord_sections = None
if _cs_path.exists():
    _cs_spec = importlib.util.spec_from_file_location("coord_status", _cs_path)
    _cs = importlib.util.module_from_spec(_cs_spec)
    assert _cs_spec.loader is not None
    _cs_spec.loader.exec_module(_cs)  # no bare except — load errors must surface
    _coord_sections = _cs.render_sections
# after existing sections:
if _coord_sections:
    print(_coord_sections(mode="probe"))
```

Do **not** wrap in `except Exception: _coord_sections = None`.

- [ ] **Step 6: Commit (B10 + B11)**

Only in the isolated worktree. Do not commit the dirty primary `orient_probe.py`.

```bash
git add -- scripts/coord_status.py scripts/orient_probe.py scripts/tests/test_coord_status.py
git commit -F- -- scripts/coord_status.py scripts/orient_probe.py scripts/tests/test_coord_status.py <<'EOF'
feat(coord): M1 core derived status via orient_probe extension (D1)
EOF
```

---

### Task 2: Divergence quality (D2 D3 D4 D8 D9) — real functions, fixtures (C7 C8 T1)

**Files:** Modify `scripts/coord_status.py`; extend `scripts/tests/test_coord_status.py`

**Interfaces:**
- `shared_files(names_a: str, names_b: str) -> set[str]`
- `classify_worktree(path: str, branch: str, dirty: str, age_days: int, parent_merged: bool = False) -> list[str]`
- `divergence_rows_fixture(diffs: dict[tuple[str,str], tuple[str,str]]) -> list[dict]`
- `render_sections_fixture(*, rev_list_count: str, active_n: int) -> str`
- Live `divergence_rows()` uses `_active_branches(7)` + `git diff --name-only`

- [ ] **Step 1: Failing tests (fixtures; thresholds match design)**

```python
def test_shared_files_disjoint_emits_none():
    assert cs.shared_files("a.txt\n", "b.txt\n") == set()

def test_shared_files_intersect():
    assert "scripts/start_mcp_daemons.ps1" in cs.shared_files(
        "scripts/start_mcp_daemons.ps1\nstop.txt\n",
        "scripts/start_mcp_daemons.ps1\ndocs/specs/spec-registry.json\n",
    )

def test_hotspot_collapse_keeps_other_pairs():
    diffs = {
        ("a", "b"): ("docs/specs/spec-registry.json\n", "docs/specs/spec-registry.json\n"),
        ("a", "c"): ("docs/specs/spec-registry.json\n", "docs/specs/spec-registry.json\n"),
        ("a", "d"): ("docs/specs/spec-registry.json\n", "docs/specs/spec-registry.json\n"),
        ("e", "f"): ("scripts/foo.py\n", "scripts/foo.py\n"),
    }
    rows = cs.divergence_rows_fixture(diffs)
    hot = [r for r in rows if r.get("hotspot")]
    others = [r for r in rows if not r.get("hotspot")]
    assert len(hot) == 1 and hot[0]["count"] >= 3
    assert any(r.get("a") == "e" for r in others)

def test_propagation_metric_via_fixture():
    out = cs.render_sections_fixture(rev_list_count="10", active_n=8)
    assert "commits/24h" in out and "on exactly" in out

def test_classify_worktree_thresholds():
    # 18d dirty is NOT abandoned (threshold 30d). 48d dirty is.
    assert "ABANDONED-DIRTY" not in cs.classify_worktree("C:/~shit/_codex_pr38_cleanup", "x", "dirty", 18)
    assert "ABANDONED-DIRTY" in cs.classify_worktree("C:/~shit/_codex_pr38_salvage_design", "x", "dirty", 48)
    # ORPHAN = detached AND parent merged, not merely dirty
    assert "ORPHAN" not in cs.classify_worktree("C:/~shit/_dep46", "(detached)", "dirty", 2, parent_merged=False)
    assert "ORPHAN" in cs.classify_worktree("C:/~shit/_dep46", "(detached)", "clean", 2, parent_merged=True)
    assert "TEMP-DIR" in cs.classify_worktree("C:/Users/kalis/AppData/Local/Temp/claude/pr41-wt", "x", "clean", 1)
```

- [ ] **Step 2: Run — expect fail** (`AttributeError` on missing helpers)

- [ ] **Step 3: Implement (not comments)**

```python
def shared_files(names_a: str, names_b: str) -> set[str]:
    fa = {s for s in names_a.splitlines() if s.strip()}
    fb = {s for s in names_b.splitlines() if s.strip()}
    return fa & fb

def classify_worktree(path: str, branch: str, dirty: str, age_days: int, parent_merged: bool = False) -> list[str]:
    flags = []
    if dirty == "dirty" and age_days >= 30:
        flags.append("ABANDONED-DIRTY")
    if branch in ("(detached)", "detached") and parent_merged:
        flags.append("ORPHAN")
    p = path.replace("\\", "/")
    if "/Temp/" in p or "/tmp/" in p or p.lower().find("/temp/") >= 0:
        flags.append("TEMP-DIR")
    return flags

def divergence_rows_fixture(diffs: dict) -> list[dict]:
    rows = []
    hotspot_counts: dict[str, int] = {}
    for (a, b), (na, nb) in diffs.items():
        shared = shared_files(na, nb)
        if not shared:
            continue
        rows.append({"a": a, "b": b, "shared": sorted(shared)})
        for f in shared:
            hotspot_counts[f] = hotspot_counts.get(f, 0) + 1
    hot_files = {f for f, c in hotspot_counts.items() if c >= 3}
    out = []
    seen_hot = set()
    for r in rows:
        hs = [f for f in r["shared"] if f in hot_files]
        if hs:
            top = hs[0]
            if top not in seen_hot:
                out.append({"hotspot": top, "count": hotspot_counts[top]})
                seen_hot.add(top)
            continue
        out.append(r)
    return out

def render_sections_fixture(*, rev_list_count: str, active_n: int) -> str:
    return f"## Coordination                    {rev_list_count} commits/24h, {rev_list_count} on exactly 1 of {active_n} active branches\n"
```

Live `divergence_rows()` must call the same `shared_files` / hotspot collapse. Mtime prefilter: read `<git-common-dir>/worktrees/<name>/index` mtime; only `git status --porcelain` worktrees that are recent or already flagged dirty. Do not assert wall-clock in tests.

- [ ] **Step 4: Tests + green set**

- [ ] **Step 5: Commit**

```bash
git add -- scripts/coord_status.py scripts/tests/test_coord_status.py
git commit -F- -- scripts/coord_status.py scripts/tests/test_coord_status.py <<'EOF'
feat(coord): D2/D3/D4/D8/D9 filters, hotspot, abandoned-dirty, fixtures
EOF
```

---

### Task 3: Git-REF claims — exclusive create, 2×ttl, UTC, workspace audit (C5 C6 C10)

**Files:**
- Create: `scripts/coord_claim.py`, `docs/specs/coordination-claims.schema.json`
- Test: `scripts/tests/test_coord_claim_cas.py`

**Interfaces:**
- `claim(kind, id, holder, ttl=3600) -> tuple[bool, str]` — create with `old=ZERO`; steal fails
- `release(kind, id, holder) -> bool` — holder only
- `is_expired(kind, id) -> bool` — `age > ttl`
- `force_drop(kind, id, holder, force=False) -> bool` — non-force only if `age >= 2*ttl`; `force=True` + audit
- `race_claim(...)` — capture `expected_old` **once**, launch all `Popen` before any wait
- Audit log: `C:/~shit/.agent-surface/coord/claims.jsonl` (`REPO_ROOT.parent`, not FLOSS)

- [ ] **Step 1: Failing tests**

```python
cc = load("coord_claim_under_test", "scripts/coord_claim.py")

def test_create_and_release():
    ok, _ = cc.claim("path", "test/claim-cas-1", holder="hermes-test", ttl=60)
    assert ok
    ok2, holder = cc.claim("path", "test/claim-cas-1", holder="other", ttl=60)
    assert not ok2 and holder == "hermes-test"  # steal must fail (C5)
    assert cc.release("path", "test/claim-cas-1", holder="hermes-test")

def test_8way_cas_same_expected_old():
    results = cc.race_claim("branch", "race-8", ttl=60, racers=8)
    wins = sum(1 for ok, _ in results if ok)
    assert wins == 1
    cc.force_drop("branch", "race-8", holder="any", force=True)

def test_ttl_expired_and_2x_force_drop():
    cc.claim("path", "test/ttl-1", holder="alice", ttl=1)
    import time; time.sleep(1.2)
    assert cc.is_expired("path", "test/ttl-1")
    assert not cc.force_drop("path", "test/ttl-1", holder="bob", force=False)  # not yet 2×ttl
    assert cc.force_drop("path", "test/ttl-1", holder="bob", force=True)
    assert cc.audit_log_contains("test/ttl-1", "force_drop")
```

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement**

```python
from __future__ import annotations
import json, subprocess, time
from datetime import datetime, timezone
from pathlib import Path

ZERO = "0" * 40
REPO_ROOT = Path(__file__).resolve().parents[1]          # FLOSS/
WORKSPACE_ROOT = REPO_ROOT.parent                        # C:/~shit
AUDIT_LOG = WORKSPACE_ROOT / ".agent-surface" / "coord" / "claims.jsonl"

def _run(*a, cwd=None):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=cwd or REPO_ROOT)

def claim_json(holder, kind, id, ttl=3600) -> str:
    payload = json.dumps({
        "holder": holder, "kind": kind, "id": id,
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ttl": ttl,
    })
    r = subprocess.run(["git", "hash-object", "-w", "--stdin"], input=payload, capture_output=True, text=True, cwd=REPO_ROOT)
    return r.stdout.strip()

def _blob(kind, id) -> dict | None:
    ref = f"refs/agent-claims/{kind}/{id}"
    r = _run("cat-file", "-p", ref)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None

def claim(kind, id, holder, ttl=3600):
    ref = f"refs/agent-claims/{kind}/{id}"
    sha = claim_json(holder, kind, id, ttl)
    r0 = _run("rev-parse", "--verify", ref)
    if r0.returncode != 0:
        r = _run("update-ref", ref, sha, ZERO)  # exclusive create
        return (r.returncode == 0, holder if r.returncode == 0 else "conflict")
    data = _blob(kind, id) or {}
    existing = data.get("holder", "unknown")
    if existing != holder:
        return False, existing  # steal fails
    r = _run("update-ref", ref, sha, r0.stdout.strip())  # same-holder refresh
    return (r.returncode == 0, holder)

def release(kind, id, holder):
    data = _blob(kind, id)
    if not data:
        return True
    if data.get("holder") != holder:
        return False
    ref = f"refs/agent-claims/{kind}/{id}"
    cur = _run("rev-parse", ref).stdout.strip()
    r = _run("update-ref", "-d", ref, cur)
    return r.returncode == 0

def _age_and_ttl(kind, id) -> tuple[float, int] | None:
    data = _blob(kind, id)
    if not data:
        return None
    created = datetime.strptime(data["created"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - created).total_seconds()
    return age, int(data.get("ttl", 3600))

def is_expired(kind, id) -> bool:
    at = _age_and_ttl(kind, id)
    return bool(at and at[0] > at[1])

def force_drop(kind, id, holder, force=False) -> bool:
    at = _age_and_ttl(kind, id)
    if not at:
        return False
    age, ttl = at
    if not force and age < 2 * ttl:
        return False
    ref = f"refs/agent-claims/{kind}/{id}"
    cur = _run("rev-parse", ref).stdout.strip()
    r = _run("update-ref", "-d", ref, cur)
    if r.returncode == 0:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG.open("a", encoding="utf-8").write(json.dumps({
            "op": "force_drop", "ref": ref, "holder": holder,
            "force": force, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }) + "\n")
    return r.returncode == 0

def audit_log_contains(id, op) -> bool:
    if not AUDIT_LOG.exists():
        return False
    return any(op in line and id in line for line in AUDIT_LOG.read_text(encoding="utf-8").splitlines())

def race_claim(kind, base_id, ttl=60, racers=8):
    ref = f"refs/agent-claims/{kind}/{base_id}"
    r = _run("rev-parse", "--verify", ref)
    expected = r.stdout.strip() if r.returncode == 0 else ZERO
    shas = [claim_json(f"racer-{i}", kind, base_id, ttl) for i in range(racers)]
    procs = [subprocess.Popen(["git", "-C", str(REPO_ROOT), "update-ref", ref, sha, expected],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for sha in shas]
    out = []
    for p in procs:
        err = p.communicate()[1]
        out.append((p.returncode == 0, err))
    return out
```

Schema: `docs/specs/coordination-claims.schema.json` — required `holder, kind, id, created, ttl`; `kind` enum `worktree|branch|path`.

- [ ] **Step 4: Tests + green set.** Cleanup leftover `refs/agent-claims/test/*` after.

- [ ] **Step 5: Commit**

```bash
git add -- scripts/coord_claim.py docs/specs/coordination-claims.schema.json scripts/tests/test_coord_claim_cas.py
git commit -F- -- scripts/coord_claim.py docs/specs/coordination-claims.schema.json scripts/tests/test_coord_claim_cas.py <<'EOF'
feat(coord): M2 exclusive git-REF claims, 2xTTL force_drop, UTC, workspace audit
EOF
```

---

### Task 4: Enforcement — separate predicate + real deny (C9 H2)

**Files:** Modify `hooks/hook_pre_write.py` (add functions + call from `main`; **do not change** `is_substantive` / `SUBSTANTIVE_PATH_SEGMENTS`); `shared-hook-surface.json` only if a specific JSON key is missing — show the exact snippet, do not “ensure flat” in prose.

**Interfaces:**
- `normalize_repo_rel(path: str, repo_root: Path) -> str` — posix, relative to repo
- `is_claim_blocked(path: str, agent_id: str) -> tuple[bool, str]`
- `is_write_allowed(path: str, agent_id: str) -> bool`
- `deny_payload(holder: str) -> dict` for `--stdout-json`
- `main()` calls claim-check **before** `is_substantive`. Deny: print payload, **return 2**. `finish()` stays allow/exit 0.

- [ ] **Step 1: Failing test** (same `normalize_repo_rel` as claim ids)

```python
hp = load("hook_pre_write_under_test", "hooks/hook_pre_write.py")
cc = load("coord_claim_under_test2", "scripts/coord_claim.py")

def test_hook_blocks_claimed_path():
    rel = "docs/specs/spec-registry.json"
    cc.claim("path", rel, holder="alice", ttl=3600)
    abs_path = str(FLOSS_ROOT / rel)
    assert not hp.is_write_allowed(abs_path, "bob")
    blocked, holder = hp.is_claim_blocked(abs_path, "bob")
    assert blocked and holder == "alice"
    cc.force_drop("path", rel, holder="alice", force=True)
```

- [ ] **Step 2: Run — expect `AttributeError: is_write_allowed`**

- [ ] **Step 3: Implement**

```python
def normalize_repo_rel(path: str, repo_root: Path | None = None) -> str:
    root = (repo_root or REPO_ROOT).resolve()
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = root / p
    try:
        rel = p.resolve().relative_to(root)
    except ValueError:
        return Path(path).as_posix().lstrip("/")
    return rel.as_posix()

def is_claim_blocked(path: str, agent_id: str) -> tuple[bool, str]:
    rel = normalize_repo_rel(path)
    ref = f"refs/agent-claims/path/{rel}"
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", ref], capture_output=True, text=True)
    if r.returncode != 0:
        return False, ""
    blob = subprocess.run(["git", "-C", str(REPO_ROOT), "cat-file", "-p", ref], capture_output=True, text=True).stdout
    try:
        holder = json.loads(blob).get("holder", "unknown")
    except json.JSONDecodeError:
        holder = "unknown"
    if holder != agent_id:
        return True, holder
    return False, ""

def is_write_allowed(path: str, agent_id: str) -> bool:
    blocked, _ = is_claim_blocked(path, agent_id)
    return not blocked

def deny_payload(holder: str) -> dict:
    reason = f"conflict: holder={holder}"
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
        "decision": "block",
        "reason": reason,
    }

# in main(), after path extract, BEFORE is_substantive:
#   blocked, holder = is_claim_blocked(target_path, agent_id)
#   if blocked:
#       if EMIT_STDOUT_JSON:
#           sys.stdout.write(json.dumps(deny_payload(holder)) + "\n")
#       else:
#           sys.stderr.write(deny_payload(holder)["reason"] + "\n")
#       return 2
```

`is_substantive` / `SUBSTANTIVE_PATH_SEGMENTS` **unchanged**.

- [ ] **Step 4: Tests + `materialize_shared_hook_surface.py --check` + green set**

- [ ] **Step 5: Commit**

```bash
git add -- hooks/hook_pre_write.py scripts/tests/test_hook_claim_block.py
git commit -F- -- hooks/hook_pre_write.py scripts/tests/test_hook_claim_block.py <<'EOF'
feat(coord): claim-block predicate + deny exit 2; is_substantive unchanged
EOF
```

---

### Task 5: Probe `--online`, Grok wiring, partial board retirement (S2 D7)

**Files:**
- Modify: `scripts/orient_probe.py` — **add** `--online` (it does not exist today; argparse is `--query/--root/--limit/--json` only)
- Modify: `scripts/start_mcp_daemons.ps1` / `stop_mcp_daemons.ps1` — merge Grok `:7334` `Start-Daemon` onto existing `$PSScriptRoot`/`$FLOSS_PYTHON` (today **0** `7334` hits). Show the actual diff hunk; do not “then merge” in prose.
- Modify: `docs/architecture/RUNTIME_SURFACES.md` — `COORDINATION_ROOM_LOG` pin to workspace intake mouth
- Modify: `docs/research/2026-05-15-working-todo-list.md` — replace **branch/worktree half of §0 only**; **keep PR table** until `--online` is verified

- [ ] **Step 1: Add `--online` to argparse; default off; `gh` only when set**

```python
parser.add_argument("--online", action="store_true", help="Include gh pr list (network). Default off.")
```

Default probe must not call `gh`. `--root` is the git repo passed to `os.chdir` — document FLOSS vs workspace.

- [ ] **Step 2: Verify split**

```
env -u PYTHONPATH C:/Python313/python.exe scripts/orient_probe.py --query "smoke" 2>&1 | findstr /i "Coordination"
env -u PYTHONPATH C:/Python313/python.exe scripts/orient_probe.py --query "smoke" --online 2>&1 | findstr /i "PR #"
```

Default: no PR section. `--online`: PR section present **or** explicit `[offline: gh failed]` — never silent.

- [ ] **Step 3: Daemon wiring + 17 room tests + green set**

`rg -n 7334 scripts/start_mcp_daemons.ps1` must hit after the merge.
`env -u PYTHONPATH C:/Python313/python.exe -m pytest packages/coordination_room/tests -v` → 17 passed.

- [ ] **Step 4: Commit**

```bash
git add -- scripts/orient_probe.py scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 docs/architecture/RUNTIME_SURFACES.md docs/research/2026-05-15-working-todo-list.md
git commit -F- -- scripts/orient_probe.py scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1 docs/architecture/RUNTIME_SURFACES.md docs/research/2026-05-15-working-todo-list.md <<'EOF'
feat(coord): --online split, :7334 daemon pin, partial Work Board §0 retirement
EOF
```

---

## Self-Review

- [ ] D1–D9 carried; DELTA-PLAN B1–B3/C1–C4/H1–H2/T1–T2/S1–S2 carried; DELTA-PLAN-2 B10–B12/C5–C10 carried in **this** text
- [ ] No `import scripts.`; no `FLOSS/` prefix on `git -C FLOSS` pathspecs
- [ ] New files: `add --` then `commit -F- --`; isolated worktree
- [ ] `claim()` exclusive create `old=ZERO`; steal fails
- [ ] `force_drop` 2×ttl; UTC parse; audit at workspace `.agent-surface`
- [ ] `is_substantive` not widened; deny is exit 2 + JSON payload
- [ ] Fixtures not live counts; green set each task
- [ ] Task 0 uses `server.submit_claim` or written waiver — no `client.py`, no `...`
- [ ] `--online` is added in Task 5, not assumed
- [ ] Self-review boxes stay **unchecked** until an implementer verifies each against the worktree

## Execution Handoff

Do **not** start Task 1 until operator LGTM **and** Task 0 is recorded.

**1. Subagent-Driven (recommended after LGTM)** — isolated worktree, one task per subagent
**2. Inline Execution** — same isolation, checkpoints

Which approach — after LGTM?
