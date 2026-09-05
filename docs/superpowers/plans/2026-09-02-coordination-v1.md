# Coordination v1 — Derived Status + Git-REF Claims Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace manual Work Board §0 and daemon-dependent room claims with a derived, cannot-go-stale status view computed from git and an atomic git-REF claim primitive.

**Architecture:** `scripts/coord_status.py:render_sections()` returns markdown; `orient_probe.py` loads it via `importlib` (extend, not a new entry). Claims are `refs/agent-claims/<kind>/<id>` via `git update-ref <new> <old>` CAS. Enforcement is a **separate** `is_claim_blocked` predicate (do not widen `is_substantive`). Offline by default; `--online` is an **added** probe flag, not present today.

**Tech Stack:** Python 3.13 stdlib-only on the probe path; Git 2.54+; PowerShell for daemon wiring.

## Global Constraints

- Probe path is stdlib-only, no network, no mutation. `gh pr list` only behind `--online` (D7). That flag **does not exist yet** — Task 5 adds it; do not assume it.
- Execute **all** implementation from an isolated worktree based on **`feat/coordination-room-rebased`** (N2), not `feat/coordination-room`:
  ```bash
  APPROVED_DOCS_COMMIT=$(git log -1 --format=%H -- docs/superpowers/specs/2026-09-02-coordination-v1-design.md docs/superpowers/plans/2026-09-02-coordination-v1.md docs/reviews/2026-09-02-coordination-v1-design)
  git worktree add .worktrees/coord-v1 -b feat/coord-v1 feat/coordination-room-rebased
  git -C .worktrees/coord-v1 checkout "$APPROVED_DOCS_COMMIT" -- docs/superpowers/specs/2026-09-02-coordination-v1-design.md docs/superpowers/plans/2026-09-02-coordination-v1.md docs/reviews/2026-09-02-coordination-v1-design
  git -C .worktrees/coord-v1 commit -m "docs(coord): import approved coordination-v1 design and evidence" -- docs/superpowers/specs/2026-09-02-coordination-v1-design.md docs/superpowers/plans/2026-09-02-coordination-v1.md docs/reviews/2026-09-02-coordination-v1-design
  ```
  Rebased already has `_repo_relative` (resolved+lowercase) **and** `:7334` `Start-Daemon` wiring. `feat/coordination-room` has neither; Task 4 would edit a superseded hook. Importing the exact approved document snapshots closes the otherwise missing design/evidence lineage without merging primary's 11 unrelated unique commits.
- Do not implement in `C:/~shit/FLOSS` while it has ~55 foreign dirty files (B11). `scripts/orient_probe.py` is dirty there (N7): resolve and reconcile it through the Pre-Task Gate; isolation alone only defers the conflict.
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

## Pre-Task Gate — Resolve Dirty Probe (N7)

Before creating the implementation worktree, run:

```bash
git status --short -- scripts/orient_probe.py
git diff -- scripts/orient_probe.py
```

At review time the primary checkout has an uncommitted `scripts/orient_probe.py` modification. Identify its owner from the coordination room/session ledger. The owner/operator must choose:

1. **Land + reconcile:** commit it on primary, then cherry-pick that exact commit into `feat/coord-v1`; or
2. **Discard:** owner/operator explicitly discards it after reviewing the diff.

Deferral blocks Task 1 because Task 1 edits the same file. Do not silently copy or overwrite it. A pre-Task-3 claim is impossible because the primitive does not exist yet. After worktree creation, verify `git diff <primary-probe-commit> -- scripts/orient_probe.py` is empty for the land path, or record the discard decision.

---

## Task 0 — Consensus decision gate (S1) — ❌ BLOCKED on consent anchor

**Files:**
- Create only when state changes: `docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md`

**Verified gate state (2026-09-03):**
- `packages/metacoordinator_mcp/tools.py:772-776` requires valid `provenance_packet` evidence with `consent_ref` for this `System` + `SpecChange` claim.
- `docs/adr/ADR-12-consent-gate-protocol.md:19` says the `decision_action_hash` anchor remains undefined/unresolved.
- `docs/agent-memory/project/adr19-ratification-deferred-to-consent-gate.md:14-20` records the operative prohibition: do not substitute a git commit, session id, or placeholder merely because the current validator only checks non-empty text.

**Interfaces (after unblock):**
- `packages.metacoordinator_mcp.server.submit_claim(proposer, proposal_type, summary, body, blast_radius, evidence=None) -> str`; there is no `client.py`.
- Evidence items use `ref`. A valid `provenance_packet` entry carrying a real `consent_ref.decision_action_hash` is mandatory in addition to spec/commit/test evidence.
- Voter rounds use `FLOSS_MODEL_BACKEND=litellm`, never OmniRoute.

- [ ] **Step 1: Resolve the consent anchor through ADR-12**

Obtain a source-chain decision action hash under the ratified consent-gate protocol. Operator chat approval, a waiver note, a commit SHA, and a session ID are **not** substitutes. If this artifact does not exist, record `❌ BLOCKED — E_GOVERNED_PROVENANCE_REQUIRED / consent anchor undefined` and stop. Do not call `submit_claim`; its failure is deterministic.

- [ ] **Step 2: Create and validate provenance packet**

Using the repo's `packages.activity_log.provenance.create_packet` / `artifact_ref` workflow, create a packet for the exact approved design/plan commit with `consent_ref.decision_action_hash=<real source-chain action hash>`. Validate the packet and artifact paths from workspace root (`C:/~shit`, so refs begin `FLOSS/...`). Add it as:

```python
{"type": "provenance_packet", "ref": "<validated workspace-relative packet path>"}
```

Do not invent the packet path or anchor.

- [ ] **Step 3: Submit, round, and record**

Submit the `SpecChange` / `System` claim with spec, current design commit, CAS test report, and validated provenance packet evidence. The body must include TWO decisions: (1) the holder-identity contract (proposal: unique per-session `FLOSS_AGENT_ID`); (2) the force-drop actor policy (proposal: `force=True` allowed only to the current holder or an operator-named force list; default deny otherwise). Record the list verbatim in the decision; the launcher publishes it via `FLOSS_CLAIM_FORCE_LIST` (Task 4 documents the variable in `RUNTIME_SURFACES.md`). Run `run_consensus_round`; write claim id, evidence refs, mean/variance/outcome, and both accepted contracts to `consensus-decision.md`.

No waiver path: the standing System consensus gate outranks execution convenience. Tasks 1–5 remain blocked until the decision is `APPROVED`. If identity is not resolved by the decision, M2/Task 4 remains blocked even if M1 is approved separately.

- [ ] **Step 4: Scoped commit**

```bash
git add -- docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md
git commit -F- -- docs/reviews/2026-09-02-coordination-v1-design/consensus-decision.md <<'EOF'
docs(coord): record coordination-v1 governed consensus decision
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

Live `divergence_rows()` must call the same `shared_files` / hotspot collapse. Mtime prefilter: read `<git-common-dir>/worktrees/<name>/index` mtime; only `git status --porcelain` worktrees that are recent or already flagged dirty. Do not assert wall-clock in tests. Do **not** implement `SHARED-INDEX`: pure Git has no “another agent active in this same checkout” signal, and the live motivating case has no duplicate branch worktree. Active claim holders appear in the separate claim section after M2.

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
- `repo_relative_path(path, repo_root=REPO_ROOT) -> str | None` — resolve, contain, POSIX, lowercase; outside repo returns `None`
- `encode_claim_id(kind, raw_id, repo_root=REPO_ROOT) -> str` — canonicalize then injectively percent-encode unsafe UTF-8 bytes
- `claim_ref(kind, raw_id, repo_root=REPO_ROOT) -> str` — build ref, run `git check-ref-format`, raise `ClaimIdError` on failure
- `claim(kind, raw_id, holder=None, ttl=3600, repo_root=REPO_ROOT) -> tuple[bool, str]` — holder defaults from the Task-0-approved identity source (proposal: `FLOSS_AGENT_ID`); missing identity is `E_AGENT_ID_MISSING`; exclusive create; same-holder refresh; different-holder reclaim only after `2×ttl`. `ttl=3600` is a PROPOSAL — Task 0 confirms the default (design open question: 1h/4h/24h); change the default to the decided value before M2
- `release(kind, raw_id, holder, repo_root=REPO_ROOT) -> bool` — holder only
- `is_expired(kind, raw_id, repo_root=REPO_ROOT) -> bool` — `age > ttl`
- `force_drop(kind, raw_id, actor, force=False, expected_sha=None, repo_root=REPO_ROOT) -> bool` — `actor` is who performs the drop; blob supplies `old_holder`; non-force only if `age >= 2*ttl`; delete CAS uses `expected_sha` when supplied; every successful drop audited. `force=True` authorization reads `force_list()` (below); any other actor with `force=True` returns False and audits the denial
- `force_list() -> list[str]` — reads `FLOSS_CLAIM_FORCE_LIST` env (comma-separated holder ids), default `[]`. Split on ",", strip each, drop empties. The launcher populates it from the Task-0 decision doc; Task 4 documents the variable in `RUNTIME_SURFACES.md`. No env → only the current holder may force
- `race_claim(kind, base_id, holder, ttl=60, racers=8, repo_root=REPO_ROOT)` — holder owns all race blobs (same TTL); capture `expected_old` **once**, launch all `Popen` before any wait
- Audit log default: `C:/~shit/.agent-surface/coord/claims.jsonl` (`REPO_ROOT.parent`, not FLOSS); tests inject a temp path
- Test-support seams (exact names; signatures pinned by the tests below, implement exactly): `ZERO = "0"*40`; `_run(*git_args, repo_root=REPO_ROOT, input=None) -> CompletedProcess` (text mode, `input` passed as stdin); `_update_ref(ref, new_sha, expected_old, repo_root) -> CompletedProcess` — routes ALL `update-ref` writes; on stderr matching `File exists|Another git process` retries up to 3× with ~50ms jitter, then returns the last result; `current_sha(kind, raw_id, repo_root) -> str | None`; `current_holder(kind, raw_id, repo_root) -> str | None`; `is_expired(...)` (above); `AUDIT_LOG` module path; `_utc_now() -> datetime` (UTC); `audit_log_contains(raw_id, event, log_path) -> bool`; `ClaimIdError`

- [ ] **Step 1: Failing tests**

```python
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[2]

def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, FLOSS_ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

cc = load("coord_claim_under_test", "scripts/coord_claim.py")

def git(repo, *args, **kwargs):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                       text=True, **kwargs)
    assert r.returncode == 0, r.stderr
    return r

@pytest.fixture
def tmp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir(exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", str(repo)], check=True,
                   capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"],
                   check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "--allow-empty", "-m", "init"],
                   check=True, capture_output=True)
    return repo

def init_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-b", "main", str(path)], check=True,
                   capture_output=True)
    return path

def test_claim_default_holder_missing_env_fails_closed(tmp_repo, monkeypatch):
    monkeypatch.delenv("FLOSS_AGENT_ID", raising=False)
    assert cc.claim("path", "docs/x.md", None, 60, tmp_repo) == (False, "E_AGENT_ID_MISSING")

def test_release_and_is_expired_on_missing_or_corrupt_are_false_not_stealable(tmp_repo):
    assert cc.release("path", "docs/absent.md", "alice", tmp_repo) is False
    assert cc.is_expired("path", "docs/absent.md", tmp_repo) is False
    ref = cc.claim_ref("path", "docs/corrupt.md", tmp_repo)
    bad = cc._run("hash-object", "-w", "--stdin", repo_root=tmp_repo, input="{nope")
    cc._run("update-ref", ref, bad.stdout.strip(), cc.ZERO, repo_root=tmp_repo)
    assert cc.release("path", "docs/corrupt.md", "alice", tmp_repo) is False
    assert cc.is_expired("path", "docs/corrupt.md", tmp_repo) is False

def test_create_is_exclusive_and_release_is_holder_only(tmp_repo):
    raw = "docs/specs/spec-registry.json"
    assert cc.claim("path", raw, "alice", 60, tmp_repo)[0]
    assert cc.claim("path", raw, "bob", 60, tmp_repo) == (False, "alice")
    assert not cc.release("path", raw, "bob", tmp_repo)
    assert cc.release("path", raw, "alice", tmp_repo)

@pytest.mark.parametrize("raw", [
    "docs/specs/spec-registry.json", "scripts/foo.lock",
    "docs/a b.md", "docs/x..y.md",
])
def test_encoded_path_refs_pass_git_authority(raw, tmp_repo):
    ref = cc.claim_ref("path", raw, tmp_repo)
    assert cc._run("check-ref-format", ref, repo_root=tmp_repo).returncode == 0

def test_encoding_is_injective_and_encodes_dot_and_percent(tmp_repo):
    raw = ["scripts/foo.lock", "scripts/foo%2Elock", "docs/x..y.md", "docs/x.y.md"]
    encoded = [cc.encode_claim_id("path", p, tmp_repo) for p in raw]
    assert len(encoded) == len(set(encoded))
    assert "%2E" in encoded[0] and "%25" in encoded[1]

def test_outside_repo_path_is_illegal_not_conflict(tmp_repo):
    assert cc.claim("path", "C:/other/foo.py", "alice", 60, tmp_repo) == (False, "E_ILLEGAL_ID")

def test_windows_reserved_names_are_illegal_not_conflict(tmp_repo):
    assert cc.claim("branch", "aux", "alice", 60, tmp_repo) == (False, "E_ILLEGAL_ID")
    assert cc.claim("path", "docs/con", "alice", 60, tmp_repo) == (False, "E_ILLEGAL_ID")
    assert cc.claim("path", "docs/con.md", "alice", 60, tmp_repo)[0]  # con%2Emd is legal
    assert cc.claim("path", "docs/console.md", "alice", 60, tmp_repo)[0]

def test_malformed_blob_is_data_error_not_absent(tmp_repo):
    ref = cc.claim_ref("path", "docs/corrupt.md", tmp_repo)
    bad = cc._run("hash-object", "-w", "--stdin", repo_root=tmp_repo, input="{nope")
    cc._run("update-ref", ref, bad.stdout.strip(), cc.ZERO, repo_root=tmp_repo)
    assert cc.claim("path", "docs/corrupt.md", "bob", 60, tmp_repo) == (False, "E_CLAIM_DATA")

def test_force_drop_corrupt_blob_denied_and_audited(tmp_repo, tmp_path, monkeypatch):
    audit_log = tmp_path / "claims.jsonl"
    monkeypatch.setattr(cc, "AUDIT_LOG", audit_log)
    ref = cc.claim_ref("path", "docs/corrupt.md", tmp_repo)
    bad = cc._run("hash-object", "-w", "--stdin", repo_root=tmp_repo, input="{nope")
    cc._run("update-ref", ref, bad.stdout.strip(), cc.ZERO, repo_root=tmp_repo)
    assert cc.force_drop("path", "docs/corrupt.md", actor="bob", force=True, repo_root=tmp_repo) is False
    assert cc.audit_log_contains("docs/corrupt.md", "E_CLAIM_DATA", audit_log)

def test_lock_contention_retries_update_ref(tmp_repo, monkeypatch):
    real = cc._run
    n = {"update": 0}
    def scripted(*a, **k):
        if a and a[0] == "update-ref":
            n["update"] += 1
            if n["update"] <= 2:
                return subprocess.CompletedProcess(a, 128, "", "fatal: Unable to create '.git/refs.lock': File exists")
        return real(*a, **k)
    monkeypatch.setattr(cc, "_run", scripted)
    assert cc.claim("path", "docs/retry.md", "alice", 60, tmp_repo)[0]
    assert n["update"] == 3

def test_8way_cas_same_expected_old(tmp_repo):
    results = cc.race_claim("branch", "race-8", "racer", 60, 8, tmp_repo)
    assert sum(1 for ok, _ in results if ok) == 1

def test_unauthorized_force_true_is_denied_and_audited(tmp_repo, tmp_path, monkeypatch):
    audit_log = tmp_path / "claims.jsonl"
    monkeypatch.setattr(cc, "AUDIT_LOG", audit_log)
    monkeypatch.delenv("FLOSS_CLAIM_FORCE_LIST", raising=False)
    assert cc.claim("path", "docs/live.md", "alice", 3600, tmp_repo)[0]
    assert not cc.force_drop("path", "docs/live.md", actor="mallory", force=True, repo_root=tmp_repo)
    assert cc.current_holder("path", "docs/live.md", tmp_repo) == "alice"
    assert cc.audit_log_contains("docs/live.md", "force_drop_denied", audit_log)

def test_authorized_force_list_allows_non_holder_before_2x_ttl(tmp_repo, tmp_path, monkeypatch):
    audit_log = tmp_path / "claims.jsonl"
    monkeypatch.setattr(cc, "AUDIT_LOG", audit_log)
    monkeypatch.setenv("FLOSS_CLAIM_FORCE_LIST", " op ,,root ")
    assert cc.force_list() == ["op", "root"]
    assert cc.claim("path", "docs/live.md", "alice", 3600, tmp_repo)[0]
    assert cc.force_drop("path", "docs/live.md", actor="op", force=True, repo_root=tmp_repo)
    assert cc.current_holder("path", "docs/live.md", tmp_repo) is None

def test_stale_reclaimer_cannot_delete_concurrent_refresh(tmp_repo, monkeypatch):
    now = [datetime(2026, 9, 3, tzinfo=timezone.utc)]
    monkeypatch.setattr(cc, "_utc_now", lambda: now[0])
    assert cc.claim("path", "docs/live.md", "alice", 10, tmp_repo)[0]
    stale_sha = cc.current_sha("path", "docs/live.md", tmp_repo)
    now[0] += timedelta(seconds=21)
    assert cc.claim("path", "docs/live.md", "alice", 10, tmp_repo)[0]  # refresh changes SHA/time
    assert not cc.force_drop("path", "docs/live.md", actor="bob", expected_sha=stale_sha, repo_root=tmp_repo)
    assert cc.current_holder("path", "docs/live.md", tmp_repo) == "alice"

def test_reclaim_only_after_2x_ttl_is_audited(tmp_repo, tmp_path, monkeypatch):
    now = [datetime(2026, 9, 3, tzinfo=timezone.utc)]
    audit_log = tmp_path / "claims.jsonl"
    monkeypatch.setattr(cc, "_utc_now", lambda: now[0])
    monkeypatch.setattr(cc, "AUDIT_LOG", audit_log)
    assert cc.claim("path", "docs/stale.md", "alice", 10, tmp_repo)[0]
    now[0] += timedelta(seconds=11)
    assert cc.is_expired("path", "docs/stale.md", tmp_repo)
    assert cc.claim("path", "docs/stale.md", "bob", 10, tmp_repo) == (False, "alice")
    now[0] += timedelta(seconds=10)
    assert cc.claim("path", "docs/stale.md", "bob", 10, tmp_repo)[0]
    assert cc.audit_log_contains("docs/stale.md", "force_drop", audit_log)
```

Each test module defines a local `tmp_repo` fixture: `git init -b main`, configure test name/email, make one empty commit, and create referenced parent directories. Import `datetime`, `timedelta`, and `timezone` in the test. Production code exposes one `_utc_now()` seam returning `datetime.now(timezone.utc)`; tests monkeypatch it. Do not sleep.

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement these invariants**

```python
_SAFE = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")

# M1: Windows reserved device basenames (case-insensitive, with or without
# extension) pass check-ref-format but fail update-ref — reject explicitly.
_RESERVED = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
)

def _encode_component(component: str) -> str:
    # urllib.parse.quote(safe="") is NOT sufficient: it leaves '.' unescaped.
    return "".join(chr(b) if b in _SAFE else f"%{b:02X}" for b in component.encode("utf-8")) or "%00"

def repo_relative_path(path, repo_root=REPO_ROOT):
    root = Path(repo_root).resolve()
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    try:
        return p.resolve().relative_to(root).as_posix().lower()
    except (OSError, ValueError):
        return None

def encode_claim_id(kind, raw_id, repo_root=REPO_ROOT):
    if kind not in {"path", "branch", "worktree"}:
        raise ClaimIdError(kind)
    if kind == "path":
        canonical = repo_relative_path(raw_id, repo_root)
        if canonical is None:
            raise ClaimIdError(raw_id)
    elif kind == "worktree":
        # Filesystem path on Windows (NTFS case-insensitive): lowercase,
        # git-canonical when the path lives in a repo (so symlinked spellings
        # of one checkout file one id — hook lookup always uses toplevel),
        # else lexical normpath (also strips trailing separators).
        import posixpath
        candidate = Path(str(raw_id).replace("\\", "/"))
        if candidate.exists():
            r = _run("rev-parse", "--show-toplevel", repo_root=str(candidate if candidate.is_dir() else candidate.parent))
            if r.returncode == 0:
                canonical = r.stdout.strip().replace("\\", "/").lower()
            else:
                canonical = posixpath.normpath(str(raw_id).replace("\\", "/")).lower()
        else:
            canonical = posixpath.normpath(str(raw_id).replace("\\", "/")).lower()
        if not canonical or canonical == ".":
            raise ClaimIdError(raw_id)
    else:  # branch: git refs are case-sensitive — preserve exact case.
        # Do NOT lower() or casefold() branch names: Feature/X != feature/x,
        # and casefold() would additionally collapse Straße -> strasse.
        canonical = str(raw_id).replace("\\", "/")
    return "/".join(_encode_component(part) for part in canonical.split("/"))

def claim_ref(kind, raw_id, repo_root=REPO_ROOT):
    ref = f"refs/agent-claims/{kind}/{encode_claim_id(kind, raw_id, repo_root)}"
    if _run("check-ref-format", ref, repo_root=repo_root).returncode != 0:
        raise ClaimIdError(raw_id)
    # M1: check-ref-format is necessary but NOT sufficient on Windows —
    # reserved device names as *exact* path components pass it yet fail
    # update-ref with Invalid argument. `con.md` encodes to `con%2Emd` and
    # is legal; a component that is exactly CON/PRN/AUX/NUL/COM1-9/LPT1-9
    # (e.g. branch `aux`, path `docs/con`) is not.
    for part in ref.split("/")[3:]:
        if part.upper() in _RESERVED:
            raise ClaimIdError(raw_id)
    return ref
```

All ref readers/writers (`claim`, `_blob`, `release`, `is_expired`, `force_drop`, `race_claim`, hook lookup) call `claim_ref`; none interpolate raw ids. Store both `raw_id` and `encoded_id` in the blob.

`claim()` algorithm:
1. Resolve holder under the Task-0-approved identity contract; missing/empty → `(False, "E_AGENT_ID_MISSING")`. Form/validate ref; on `ClaimIdError`, return `(False, "E_ILLEGAL_ID")`.
2. Read current SHA **once**. Missing → `_update_ref(<ref>, <new>, ZERO)`. All `update-ref` writes in `claim()` go through `_update_ref` (lock retry).
3. Existing blob unparseable (holder/created/ttl) → `(False, "E_CLAIM_DATA")` — fail closed, never treat corruption as absent.
4. Existing same holder → refresh with CAS against that SHA.
5. Existing different holder and age `< 2×ttl` → `(False, existing_holder)`.
6. Existing different holder and age `>= 2×ttl` → CAS-delete via `force_drop(..., actor=holder, expected_sha=current)` with audit, then exclusive-create with `ZERO`. If another writer wins the gap, return its holder/`conflict`; never overwrite.

`force_drop()` validates the ref, reads one current SHA/blob, checks any supplied `expected_sha` against that current SHA, enforces `2×ttl` unless `force=True` **from an authorized actor**, then deletes with the current SHA as expected-old. Authorization: `force=True` requires `actor == old_holder` or `actor` in the Task-0-approved force list; any other actor with `force=True` returns False and audits the denial. On success it appends a JSONL audit record containing raw id, encoded ref, `old_holder` from the blob, separate `actor`, force flag, age, and UTC timestamp. Malformed blob/time/ref returns `False` and audits the denial with the `E_CLAIM_DATA` code — explicit error, never "not claimed", never steal-able.

`race_claim()` forms the encoded ref once, captures the same expected-old before spawning, creates all blobs, launches all `Popen` calls, then waits. Cleanup deletes the encoded ref.

Schema: `docs/specs/coordination-claims.schema.json` — required `holder, kind, raw_id, encoded_id, created, ttl`; `kind` enum `worktree|branch|path`; UTC timestamp; positive TTL.

- [ ] **Step 4: Tests + green set.** Cleanup leftover `refs/agent-claims/test/*` after.

- [ ] **Step 5: Commit**

```bash
git add -- scripts/coord_claim.py docs/specs/coordination-claims.schema.json scripts/tests/test_coord_claim_cas.py
git commit -F- -- scripts/coord_claim.py docs/specs/coordination-claims.schema.json scripts/tests/test_coord_claim_cas.py <<'EOF'
feat(coord): M2 exclusive git-REF claims, 2xTTL force_drop, UTC, workspace audit
EOF
```

---

### Task 4: Enforcement — shared canonicalizer + fail-closed deny (N1/N3/N4/C9/H2)

**Files:** Modify `hooks/hook_pre_write.py` (import `importlib.util` and **`subprocess`**; load `scripts/coord_claim.py`; delegate `_repo_relative`; preserve `is_substantive` behavior while adapting its local leading slash; add functions + call from `main`; **do not widen** `SUBSTANTIVE_PATH_SEGMENTS` or provenance scope); modify `docs/architecture/RUNTIME_SURFACES.md` to document the approved identity source/launch requirement **and** the `FLOSS_CLAIM_FORCE_LIST` variable (launcher-populated from the Task-0 decision; no env → holder-only force); `shared-hook-surface.json` only if a specific JSON key is missing — show the exact snippet, do not “ensure flat” in prose.

**Interfaces:**
- `resolve_floss_worktree(path, hook_root) -> Path | None` — BOTH args required (no defaults). `git -C <file>` fails (rc=128) for file paths, so parent-walk: start at the path (or its parent if not a dir), ascend until `git -C <dir> rev-parse --show-toplevel` succeeds. Accept only when that repo's ABSOLUTE `--git-common-dir` (`rev-parse --path-format=absolute --git-common-dir`, resolved) equals the hook checkout's absolute common dir — raw `.git` == `.git` across unrelated repos, so relative compare is forbidden. First enclosing repo not FLOSS → `None`; no repo found → `None`. Returns the target's actual toplevel (sibling worktrees resolve to themselves). Callers must never substitute the hook checkout's root for the result
- `hook_pre_write._repo_relative(path, target_root)` resolves relative tool paths against `Path.cwd()`, then delegates the resulting absolute path to `coord_claim.repo_relative_path(path, target_root)` — no third case/containment normalizer; returned id has no leading slash
- `is_substantive(path, target_root)` forms `norm = "/" + (_repo_relative(path, target_root) or "").lstrip("/")` before its existing segment checks, preserving the rebased N2 behavior
- `extract_agent_id(payload) -> str | None` — implement the Task-0-approved contract; proposed default reads unique per-session `FLOSS_AGENT_ID`, never a static harness name
- `is_claim_blocked(path: str, agent_id: str, repo_root: Path) -> tuple[bool, str]` — `repo_root` is REQUIRED (no default): it must be the `resolve_floss_worktree` result for this target. A defaulted hook-checkout root would silently check the wrong worktree
- `is_write_allowed(path: str, agent_id: str) -> bool` — resolves the target root internally via `resolve_floss_worktree(path, REPO_ROOT)` (None → True, allow) then negates `is_claim_blocked`
- `deny_payload(holder: str) -> dict` — REQUIRED shape: `{"reason": str, "holder": str, "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}`. Extra harness-compatible keys are additive, never substitutes for `permissionDecision: deny`
- `main()` order: mutating-tool check → resolve target worktree (None → allow; crash → deny 2) → identity (missing → deny 2) → claim-check with target root → `is_substantive`. Deny or lookup/encoding error: print payload, **return 2**. `finish()` stays allow/exit 0. `_is_inside_repo` is NOT on the claim path

- [ ] **Step 1: Failing tests**

```python
import io
import json

import pytest

# Preamble FIRST (copy from Task 3 Step 1 verbatim before anything below):
# importlib, subprocess, sys, datetime/timedelta/timezone, Path,
# FLOSS_ROOT, load(), git(), tmp_repo, init_repo. The load() calls that
# follow need it; a contiguous copy must collect.

hp = load("hook_pre_write_under_test", "hooks/hook_pre_write.py")
cc = load("coord_claim_under_test2", "scripts/coord_claim.py")

def invoke(payload, monkeypatch):
    monkeypatch.setattr(hp.sys, "stdin", io.StringIO(json.dumps(payload)))
    return hp.main()

def write_payload(path):
    return {"tool_name": "write", "tool_input": {"file_path": str(path)}}

def test_resolve_floss_worktree_reaches_sibling_not_unrelated(tmp_repo, tmp_path):
    sibling = tmp_path / "sibling-wt"
    git(tmp_repo, "worktree", "add", "-b", "test/sibling", str(sibling))
    unrelated = init_repo(tmp_path / "unrelated")
    assert hp.resolve_floss_worktree(sibling / "docs/x.md", tmp_repo) == sibling.resolve()
    assert hp.resolve_floss_worktree(unrelated / "x.md", tmp_repo) is None

def test_hook_resolves_sibling_worktree_scopes_not_hook_checkout(tmp_repo, tmp_path, monkeypatch):
    # Hook checkout root != target worktree: scopes must come from the target.
    sibling = tmp_path / "sibling-wt"
    git(tmp_repo, "worktree", "add", "-b", "test/sibling-scope", str(sibling))
    (sibling / "docs").mkdir(exist_ok=True)
    target = sibling / "docs/x.md"
    target.write_text("x")
    assert cc.claim("branch", "test/sibling-scope", "alice", 3600, sibling)[0]
    authenticity = hp.resolve_floss_worktree(str(target), tmp_repo)
    assert authenticity == sibling.resolve()
    blocked, holder = hp.is_claim_blocked(str(target), "bob", authenticity)
    assert blocked and holder == "alice"

def test_is_write_allowed_negates_blocked(tmp_repo, monkeypatch):
    target = tmp_repo / "docs/z.md"
    target.parent.mkdir(exist_ok=True)
    target.write_text("z")
    monkeypatch.setattr(hp, "resolve_floss_worktree", lambda *a, **k: tmp_repo)
    assert hp.is_write_allowed(str(target), "alice") is True
    assert cc.claim("path", str(target), "alice", 3600, tmp_repo)[0]
    assert hp.is_write_allowed(str(target), "alice") is True
    assert hp.is_write_allowed(str(target), "bob") is False

def test_relative_tool_path_resolves_against_cwd_not_root(tmp_repo, monkeypatch):
    pkg = tmp_repo / "packages"
    pkg.mkdir(exist_ok=True)
    target = pkg / "prod.py"
    target.write_text("x")
    assert cc.claim("path", str(target), "alice", 3600, tmp_repo)[0]
    monkeypatch.chdir(pkg)
    blocked, holder = hp.is_claim_blocked("prod.py", "bob", tmp_repo)
    assert blocked and holder == "alice"

def test_null_holder_blob_is_data_error_not_absent(tmp_repo):
    ref = cc.claim_ref("path", "docs/null.md", tmp_repo)
    bad = cc._run("hash-object", "-w", "--stdin", repo_root=tmp_repo, input='{"holder": null}')
    cc._run("update-ref", ref, bad.stdout.strip(), cc.ZERO, repo_root=tmp_repo)
    assert hp.is_claim_blocked(str(tmp_repo / "docs/null.md"), "bob", tmp_repo) == (True, "E_CLAIM_DATA")

def test_hook_and_claim_use_same_canonical_id(tmp_repo):
    mixed = str(tmp_repo / "Docs" / "X Y.lock")
    lower = str(tmp_repo / "docs" / "x y.lock")
    assert hp._repo_relative(mixed, tmp_repo) == cc.repo_relative_path(lower, tmp_repo)
    assert cc.claim_ref("path", mixed, tmp_repo) == cc.claim_ref("path", lower, tmp_repo)

def test_rebased_substantive_semantics_survive_shared_normalizer(tmp_repo, monkeypatch):
    (tmp_repo / "nested").mkdir(exist_ok=True)
    monkeypatch.chdir(tmp_repo / "nested")
    assert hp._repo_relative("../packages/prod.py", tmp_repo) == "packages/prod.py"
    assert hp.is_substantive(str(tmp_repo / "packages" / "prod.py"), tmp_repo)
    assert hp.is_substantive(str(tmp_repo / "packages" / "tests" / ".." / "prod.py"), tmp_repo)
    assert not hp.is_substantive(str(tmp_repo / "packages" / "tests" / "x.py"), tmp_repo)

@pytest.mark.parametrize("kind,raw", [
    ("worktree", "C:/Users/A B/repo.lock"),
    ("branch", "feature/a b..lock"),
])
def test_non_path_claim_refs_are_legal_and_injective(kind, raw, tmp_repo):
    first = cc.claim_ref(kind, raw, tmp_repo)
    second = cc.claim_ref(kind, raw + "%", tmp_repo)
    assert first != second
    assert cc._run("check-ref-format", first, repo_root=tmp_repo).returncode == 0

def test_worktree_trailing_separator_is_same_checkout(tmp_repo):
    assert cc.claim_ref("worktree", "C:/wt/", tmp_repo) == cc.claim_ref("worktree", "C:/wt", tmp_repo)
    assert cc.claim_ref("worktree", "C:/wt/./x", tmp_repo) == cc.claim_ref("worktree", "C:/wt/x", tmp_repo)

def test_lower_not_casefold_avoids_unicode_collision(tmp_repo):
    assert cc.claim_ref("branch", "Straße", tmp_repo) != cc.claim_ref("branch", "Strasse", tmp_repo)
    assert cc.claim_ref("branch", "Feature/X", tmp_repo) != cc.claim_ref("branch", "feature/x", tmp_repo)
    # Path ids stay NTFS case-insensitive:
    assert cc.claim_ref("path", "Docs/X.md", tmp_repo) == cc.claim_ref("path", "docs/x.md", tmp_repo)

def test_hook_blocks_path_branch_and_worktree_claims(tmp_repo, monkeypatch):
    monkeypatch.setattr(hp, "current_branch", lambda root: "main")
    monkeypatch.setattr(hp, "current_worktree", lambda root: str(root.resolve()))
    target = tmp_repo / "docs/specs/spec-registry.json"
    for kind, raw in [("path", str(target)), ("branch", "main"), ("worktree", str(tmp_repo))]:
        assert cc.claim(kind, raw, "alice", 3600, tmp_repo)[0]
        blocked, holder = hp.is_claim_blocked(str(target), "bob", tmp_repo)
        assert blocked and holder == "alice"
        assert cc.release(kind, raw, "alice", tmp_repo)

def test_hook_fails_closed_outside_repo_and_on_lookup_exception(tmp_repo, monkeypatch):
    assert hp.is_claim_blocked("C:/other/foo.py", "bob", tmp_repo) == (True, "E_ILLEGAL_ID")
    monkeypatch.setattr(hp.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(OSError("spawn failed")))
    assert hp.is_claim_blocked(str(tmp_repo / "docs/x.md"), "bob", tmp_repo) == (True, "E_CLAIM_LOOKUP")

def test_missing_agent_identity_fails_closed_for_in_repo_write(tmp_repo, monkeypatch):
    monkeypatch.delenv("FLOSS_AGENT_ID", raising=False)
    monkeypatch.setattr(hp, "REPO_ROOT", tmp_repo)
    hp.EMIT_STDOUT_JSON = True
    assert invoke(write_payload(tmp_repo / "docs/x.md"), monkeypatch) == 2

def test_main_allows_unrelated_project_without_ref_lookup(tmp_repo, monkeypatch):
    # Resolution runs (returns None outside FLOSS); ref lookup must not.
    monkeypatch.setattr(hp, "resolve_floss_worktree", lambda *a, **k: None)
    monkeypatch.setattr(hp, "_claim_holder", lambda *a, **k: pytest.fail("ref lookup must not run"))
    assert invoke(write_payload("C:/other-project/packages/x.py"), monkeypatch) == 0

def test_main_sibling_worktree_bypass_closed(tmp_repo, tmp_path, monkeypatch):
    # External sibling worktree: old _is_inside_repo guard would allow; resolve-first must enforce.
    sibling = tmp_path / "sibling-main"
    git(tmp_repo, "worktree", "add", "-b", "test/sibling-main", str(sibling))
    (sibling / "docs").mkdir(exist_ok=True)
    target = sibling / "docs/y.md"
    target.write_text("y")
    monkeypatch.setenv("FLOSS_AGENT_ID", "bob")
    monkeypatch.setattr(hp, "REPO_ROOT", tmp_repo)
    hp.EMIT_STDOUT_JSON = True
    assert cc.claim("path", str(target), "alice", 3600, sibling)[0]
    assert invoke(write_payload(target), monkeypatch) == 2

def test_main_claim_deny_is_exit_2_and_json(tmp_repo, monkeypatch, capsys):
    monkeypatch.setenv("FLOSS_AGENT_ID", "bob")
    monkeypatch.setattr(hp, "REPO_ROOT", tmp_repo)
    hp.EMIT_STDOUT_JSON = True
    target = tmp_repo / "docs/x.md"
    assert cc.claim("path", str(target), "alice", 3600, tmp_repo)[0]
    assert invoke(write_payload(target), monkeypatch) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
```

- [ ] **Step 2: Run — expect missing imports/functions**

- [ ] **Step 3: Implement**

At module import, explicitly load `scripts/coord_claim.py` by file location (the `scripts` directory is not a package). Add both imports:

```python
import importlib.util
import subprocess  # N4: required by is_claim_blocked

_CC_PATH = Path(__file__).resolve().parents[1] / "scripts" / "coord_claim.py"
try:
    _CC_SPEC = importlib.util.spec_from_file_location("coord_claim_for_hook", _CC_PATH)
    _CC = importlib.util.module_from_spec(_CC_SPEC)
    assert _CC_SPEC.loader is not None
    sys.modules[_CC_SPEC.name] = _CC
    _CC_SPEC.loader.exec_module(_CC)
except Exception as _cc_exc:  # F8: missing/broken coord_claim must not crash the hook import
    log(f"[hook-pre] coord_claim load failed ({_cc_exc}); claim checks fail closed")
    _CC = None

def extract_agent_id(payload: dict) -> str | None:
    # Replace only if Task 0 approves a different shared identity contract.
    value = os.environ.get("FLOSS_AGENT_ID", "").strip()
    return value or None

def _repo_relative(path_str: str, repo_root: Path) -> str | None:
    candidate = Path(path_str).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate  # preserve existing hook input semantics
    return _CC.repo_relative_path(candidate, repo_root)

# In is_substantive(), preserve the leading slash expected by the existing
# SUBSTANTIVE_PATH_SEGMENTS / CANON_PATH_SEGMENTS constants:
#   rel = _repo_relative(path_str, target_root)
#   if rel is None: return False
#   norm = "/" + rel.lstrip("/")
```

Claim lookup checks scopes in deterministic broad-to-narrow order: current worktree, current branch (skip only a verified detached HEAD), then target path. Any claim held by another identity blocks the write; same-holder and absent refs continue to the next scope.

```python
class ClaimLookupError(RuntimeError):
    pass

def _git(*args, repo_root=REPO_ROOT):
    try:
        return subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ClaimLookupError(str(exc)) from exc

def resolve_floss_worktree(path_str: str, hook_root: Path) -> Path | None:
    # B1: git -C <file> fails for file paths — parent-walk from the path.
    # Defined AFTER _git / ClaimLookupError so a sequential copy does not NameError.
    candidate = Path(path_str).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    start = candidate if candidate.is_dir() else candidate.parent
    hook_common = _git("rev-parse", "--path-format=absolute", "--git-common-dir",
                       repo_root=hook_root)
    if hook_common.returncode != 0:
        raise ClaimLookupError(hook_common.stderr)
    hook_common_p = Path(hook_common.stdout.strip()).resolve()
    for d in [start, *start.parents]:
        top = _git("rev-parse", "--show-toplevel", repo_root=d)
        if top.returncode != 0:
            continue
        common = _git("rev-parse", "--path-format=absolute", "--git-common-dir",
                      repo_root=d)
        if common.returncode != 0:
            continue
        if Path(common.stdout.strip()).resolve() == hook_common_p:
            return Path(top.stdout.strip())
        return None  # first enclosing repo is not a FLOSS checkout
    return None

def current_worktree(repo_root=REPO_ROOT) -> str:
    # Resolve the ACTUAL top-level of the target checkout (sibling worktrees
    # have their own top-level). Never assume the hook script's checkout.
    r = _git("rev-parse", "--show-toplevel", repo_root=repo_root)
    if r.returncode != 0:
        raise ClaimLookupError(r.stderr)
    return r.stdout.strip()

def current_branch(repo_root=REPO_ROOT) -> str | None:
    r = _git("symbolic-ref", "--quiet", "--short", "HEAD", repo_root=repo_root)
    if r.returncode == 1:  # documented detached HEAD result
        return None
    if r.returncode != 0:
        raise ClaimLookupError(r.stderr)
    return r.stdout.strip()

def _claim_holder(kind: str, raw_id: str, repo_root=REPO_ROOT) -> str | None:
    ref = _CC.claim_ref(kind, raw_id, repo_root)  # may raise ClaimIdError
    r = _git("show-ref", "--verify", "--quiet", ref, repo_root=repo_root)
    if r.returncode == 1:
        return None
    if r.returncode != 0:
        raise ClaimLookupError(r.stderr)
    blob = _git("cat-file", "-p", ref, repo_root=repo_root)
    if blob.returncode != 0:
        raise ClaimLookupError(blob.stderr)
    try:
        data = json.loads(blob.stdout)
    except json.JSONDecodeError as exc:
        raise ClaimLookupError("E_CLAIM_DATA") from exc
    holder = data.get("holder") if isinstance(data, dict) else None
    if not isinstance(holder, str) or not holder:
        # Missing key, JSON null, empty, or non-string: corrupt, never absent.
        raise ClaimLookupError("E_CLAIM_DATA")
    return holder

def is_claim_blocked(path: str, agent_id: str, repo_root: Path) -> tuple[bool, str]:
    # repo_root is REQUIRED (no default) and must be the resolve_floss_worktree
    # result for this target. A defaulted hook-checkout root would silently
    # check the wrong worktree.
    if _CC is None:  # F8: coord_claim failed to load — fail closed
        return True, "E_CLAIM_LOOKUP"
    # Blocking-1: tool paths may be relative to the hook's cwd, NOT the repo
    # root. repo_relative_path joins repo_root, so a bare "prod.py" would file
    # as <root>/prod.py while the agent meant <cwd>/prod.py. Resolve against
    # cwd first (same rule as _repo_relative), then file the absolute path.
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    path = str(candidate)
    try:
        scopes = [("worktree", current_worktree(repo_root))]
        branch = current_branch(repo_root)
        if branch is not None:
            scopes.append(("branch", branch))
        scopes.append(("path", path))
        for kind, raw_id in scopes:
            holder = _claim_holder(kind, raw_id, repo_root)
            if holder is not None and holder != agent_id:
                return True, holder
        return False, ""
    except _CC.ClaimIdError:
        return True, "E_ILLEGAL_ID"
    except ClaimLookupError as exc:
        # F4: preserve explicit E_ codes (notably E_CLAIM_DATA from corrupt
        # blobs); anything else collapses to E_CLAIM_LOOKUP. Deny either way.
        code = str(exc) or "E_CLAIM_LOOKUP"
        return True, code if code.startswith("E_") else "E_CLAIM_LOOKUP"
    except (OSError, subprocess.SubprocessError):
        return True, "E_CLAIM_LOOKUP"
```

`is_write_allowed` negates the first tuple item. `deny_payload` retains both Claude/Hermes and Codex-compatible fields. In `main()`, resolve the target's FLOSS worktree FIRST — the old `_is_inside_repo` path-containment guard must not run before it, because sibling worktrees outside the hook checkout fail containment and would bypass enforcement (fail-open). `_is_inside_repo` stays untouched for the checkpoint path; the claim path uses common-dir identity instead:

```python
try:
    target_root = resolve_floss_worktree(file_path, REPO_ROOT)
except Exception:
    log(f"[hook-pre] worktree resolve crashed:\n{traceback.format_exc()}")
    sys.stderr.write("claim worktree resolution failed\n")
    return 2  # fail closed: resolution failure must never allow
if target_root is None:
    return finish()  # outside every FLOSS checkout: unrelated repositories stay out of scope
agent_id = extract_agent_id(payload)
if not agent_id:
    payload = deny_payload("E_AGENT_ID_MISSING")
    if EMIT_STDOUT_JSON:
        sys.stdout.write(json.dumps(payload) + "\n")
    else:
        sys.stderr.write(payload["reason"] + "\n")
    return 2
try:
    blocked, holder = is_claim_blocked(file_path, agent_id, target_root)
except Exception:  # claim subsystem must fail closed
    log(f"[hook-pre] claim lookup crashed:\n{traceback.format_exc()}")
    blocked, holder = True, "E_CLAIM_INTERNAL"
if blocked:
    payload = deny_payload(holder)
    if EMIT_STDOUT_JSON:
        sys.stdout.write(json.dumps(payload) + "\n")
    else:
        sys.stderr.write(payload["reason"] + "\n")
    return 2
# F1: the existing 1-arg call below MUST be updated — after the signature change
# a bare is_substantive(file_path) raises TypeError on every unclaimed write.
if not is_substantive(file_path, target_root):
    return finish()  # claim check passed; not provenance-worthy
# ... existing provenance/substantive handling continues unchanged
```

`SUBSTANTIVE_PATH_SEGMENTS` and provenance scope remain unchanged. `is_substantive` changes only its local leading-slash adaptation to preserve prior semantics. **Call-site update is mandatory, not optional:** the existing `if not is_substantive(file_path):` in `main()` (live hook ~L194, rebased base ~L211) must become `is_substantive(file_path, target_root)` — the new signature has no default, so the old call raises `TypeError` on every unclaimed write (crash, exit 1, no deny payload).

- [ ] **Step 4: Tests + `materialize_shared_hook_surface.py --check` + green set**

- [ ] **Step 5: Commit**

```bash
git add -- hooks/hook_pre_write.py scripts/tests/test_hook_claim_block.py docs/architecture/RUNTIME_SURFACES.md
git commit -F- -- hooks/hook_pre_write.py scripts/tests/test_hook_claim_block.py docs/architecture/RUNTIME_SURFACES.md <<'EOF'
feat(coord): fail-closed claim enforcement with shared path identity
EOF
```

---

### Task 5: Probe `--online`, verify inherited Grok wiring, partial board retirement (S2/D7/N2)

**Files:**
- Modify: `scripts/orient_probe.py` — **add** `--online` (it does not exist today; argparse is `--query/--root/--limit/--json` only)
- **Verify only:** `scripts/start_mcp_daemons.ps1` / `stop_mcp_daemons.ps1` — the `feat/coordination-room-rebased` base already carries Grok `:7334` `Start-Daemon`, PID, stop, and `COORDINATION_ROOM_LOG` wiring. Do not cherry-pick or duplicate it.
- Modify `docs/architecture/RUNTIME_SURFACES.md` only if its coordination-room pin is absent/stale on the rebased base; show the exact diff.
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

- [ ] **Step 3: Verify inherited daemon wiring + 17 room tests + green set**

On `feat/coordination-room-rebased`:

```bash
rg -n "7334|coordination_room" scripts/start_mcp_daemons.ps1 scripts/stop_mcp_daemons.ps1
```

Must show start on `:7334`, `coordination_room.pid`, stop coverage, and the workspace `.agent-surface/rooms/default/events.jsonl` pin. If any is absent, stop and reconcile against the rebased branch evidence; do not blindly cherry-pick. Then:

`env -u PYTHONPATH C:/Python313/python.exe -m pytest packages/coordination_room/tests -v` → 17 passed.

- [ ] **Step 4: Commit**

```bash
git add -- scripts/orient_probe.py docs/research/2026-05-15-working-todo-list.md
git add -- docs/architecture/RUNTIME_SURFACES.md  # only if changed after exact stale-pin proof
git commit -F- -- scripts/orient_probe.py docs/research/2026-05-15-working-todo-list.md docs/architecture/RUNTIME_SURFACES.md <<'EOF'
feat(coord): --online split and partial Work Board §0 retirement
EOF
```

---

## Self-Review

- [ ] D1–D9; DELTA-PLAN B1–B3/C1–C4/H1–H2/T1–T2/S1–S2; DELTA-PLAN-2 B10–B12/C5–C10; DELTA-3 N1–N7 carried in **this** text
- [ ] Base is `feat/coordination-room-rebased`; inherited `_repo_relative` and `:7334` wiring verified; no duplicate cherry-pick
- [ ] Dirty primary `scripts/orient_probe.py` resolved by owner/operator before Task 1
- [ ] One canonical path function; lowercased; illegal ref bytes injectively encoded; `git check-ref-format` authoritative
- [ ] Holder identity contract explicitly approved in Task 0; no undefined/static `agent_id`; missing identity fails closed for in-repo writes
- [ ] `claim()` distinguishes `E_ILLEGAL_ID`, reclaims only after `2×ttl`, and audits; hook lookup failures deny/exit 2
- [ ] `SHARED-INDEX` explicitly rejected as underivable from pure Git; no fake caller boolean; CAS test is `scripts/tests/test_coord_claim_cas.py`
- [ ] No `import scripts.`; no `FLOSS/` prefix on `git -C FLOSS` pathspecs
- [ ] New files: `add --` then `commit -F- --`; isolated worktree
- [ ] `claim()` exclusive create `old=ZERO`; steal fails
- [ ] `force_drop` 2×ttl; UTC parse; audit at workspace `.agent-surface`
- [ ] `is_substantive` not widened; deny is exit 2 + JSON payload
- [ ] Fixtures not live counts; green set each task
- [ ] Task 0 includes a validated provenance packet with a real ADR-12 consent action hash; no waiver/placeholder; decision is `APPROVED` before M1
- [ ] `--online` is added in Task 5, not assumed
- [ ] Self-review boxes stay **unchecked** until an implementer verifies each against the worktree

## Execution Handoff

Do **not** start Task 1 until the dirty-probe gate is reconciled **and** Task 0 has a valid provenance-backed `APPROVED` decision. Operator chat LGTM or a waiver is insufficient while ADR-12's consent anchor is unresolved.

**1. Subagent-Driven (recommended after LGTM)** — isolated worktree, one task per subagent
**2. Inline Execution** — same isolation, checkpoints

Which approach — after LGTM?
