# PR 38 Preservation Capsule Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reversible slice of the PR #38 salvage spine: six-plane local capture, authenticated capsule verification, complete change-universe inventory, resumable checkpoints, and sanitized GitHub-facing evidence projections without mutating PR #38.

**Architecture:** A small standard-library Python package under `packages/salvage_spine/` owns deterministic models, Git capture, sealing, restoration, manifest inventory, and rendering. A thin registered script exposes the CLI. Runtime capsules live outside the workspace beneath `C:\~shit\_pr38_salvage_capsules\pr38\`, keyed by a generated state ID; tracked schemas, tests, and a proposed stop-merge template define the contract. Only sanitized projections may be copied into `.agent-surface/`. GitHub is a projection surface in this slice: no workflow, PR comment, Draft transition, branch rewrite, or required-check mutation occurs.

**Tech Stack:** Python 3.11+ standard library, Git CLI, pytest, JSON Schema draft 2020-12 documents, SHA-256, Git bundles, Markdown/JSON projections.

## Global Constraints

- Preserve remote main, remote PR #38, local committed history, local index, local tracked worktree, and local untracked/ignored inventory as six separately identified planes.
- Never reset, stash, rebase, squash, force-push, delete, clean, or otherwise mutate a source checkout.
- The capsule destination must be outside every captured source worktree.
- Secret-bearing content is excluded from ordinary artifacts and represented only by redacted metadata.
- Capture must prove before/after equality or fail closed as drifted.
- Clean-room restoration must pass before any PR containment action can be proposed as ready.
- Every captured change atom has exactly one manifest owner; unclassified atoms remain preserved and ineligible.
- `PASS`, `FAIL`, `BLOCKED`, and `SKIPPED` retain their scoped meanings; there is no global green field.
- GitHub checks and comments expose evidence but confer no architectural, canonical, or symbolic authority.
- ADR, integrity-zome, consensus-gateway, canonical-promotion, deletion, and protected-config changes remain outside this slice.
- Existing failures on the locked baseline are reported as absolute failures even when reconstruction adds no regression.

## File Structure

- Create `packages/salvage_spine/__init__.py`: public package version and exports.
- Create `packages/salvage_spine/models.py`: immutable capture, plane, command, and result records.
- Create `packages/salvage_spine/git_capture.py`: read-only Git interrogation and six-plane capture.
- Create `packages/salvage_spine/seal.py`: deterministic JSON, checksums, provenance root, and verification.
- Create `packages/salvage_spine/restore.py`: empty-repository bundle restore and identity comparison.
- Create `packages/salvage_spine/manifest.py`: complete-universe atom inventory and ownership validation.
- Create `packages/salvage_spine/github_projection.py`: sanitized check summaries and proposed comment rendering.
- Create `packages/salvage_spine/checkpoint.py`: append-only resumability records.
- Create `packages/salvage_spine/cli.py`: command parser and orchestration.
- Create `packages/salvage_spine/tests/`: unit and temporary-repository integration tests.
- Create `scripts/pr38_salvage.py`: minimal CLI entry point.
- Modify `docs/specs/spec-registry.json`: register only the new gated script.
- Create `docs/superpowers/specs/pr38-capsule.schema.json`: capsule metadata contract.
- Create `docs/superpowers/specs/pr38-salvage-manifest.schema.json`: inventory and classification contract.
- Create `docs/superpowers/specs/pr38-checkpoint.schema.json`: continuation contract.
- Create `docs/superpowers/templates/pr38-stop-merge-comment.md`: proposed, non-canonical comment template.
- Create `C:\~shit\_pr38_salvage_capsules\pr38\` only at runtime; never place capsule payloads inside a captured workspace or commit them.

---

### Task 1: Contract Schemas and Deterministic Model Types

**Files:**
- Create: `docs/superpowers/specs/pr38-capsule.schema.json`
- Create: `docs/superpowers/specs/pr38-salvage-manifest.schema.json`
- Create: `docs/superpowers/specs/pr38-checkpoint.schema.json`
- Create: `packages/salvage_spine/__init__.py`
- Create: `packages/salvage_spine/models.py`
- Test: `packages/salvage_spine/tests/test_models.py`

**Interfaces:**
- Produces: `ResultStatus`, `PlaneId`, `PlaneRecord`, `CapsuleRecord`, and `canonical_json_bytes(value: object) -> bytes`.
- Consumes: no earlier task interfaces.

- [ ] **Step 1: Write failing model tests**

```python
from dataclasses import FrozenInstanceError
import pytest

from packages.salvage_spine.models import PlaneId, PlaneRecord, canonical_json_bytes


def test_plane_record_is_immutable_and_json_is_deterministic():
    record = PlaneRecord(plane_id=PlaneId.REMOTE_MAIN, subject_id="abc", digest="0" * 64)
    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}\n'
    with pytest.raises(FrozenInstanceError):
        record.digest = "1" * 64
```

- [ ] **Step 2: Run the test and confirm the import fails**

Run: `python -m pytest packages/salvage_spine/tests/test_models.py -q`

Expected: FAIL because `packages.salvage_spine.models` does not exist.

- [ ] **Step 3: Implement immutable types and canonical serialization**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import json
from typing import Any


class ResultStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class PlaneId(StrEnum):
    REMOTE_MAIN = "remote-main"
    REMOTE_PR = "remote-pr38"
    LOCAL_HISTORY = "local-history"
    LOCAL_INDEX = "local-index"
    LOCAL_TRACKED = "local-tracked"
    LOCAL_UNTRACKED = "local-untracked-ignored"


@dataclass(frozen=True)
class PlaneRecord:
    plane_id: PlaneId
    subject_id: str
    digest: str


def canonical_json_bytes(value: Any) -> bytes:
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
```

Complete `CapsuleRecord` with explicit `schema_version`, `state_id`, `repository`, `captured_at`, `planes`, `exclusions`, and `status` fields. Encode the same required fields and `additionalProperties: false` in the three schemas.

- [ ] **Step 4: Run model tests**

Run: `python -m pytest packages/salvage_spine/tests/test_models.py -q`

Expected: PASS.

- [ ] **Step 5: Commit the contract types**

```bash
git add docs/superpowers/specs/pr38-*.schema.json packages/salvage_spine/__init__.py packages/salvage_spine/models.py packages/salvage_spine/tests/test_models.py
git commit -m "feat: define PR38 salvage capsule contracts"
```

### Task 2: Read-Only Git Snapshot and Drift Guard

**Files:**
- Create: `packages/salvage_spine/git_capture.py`
- Test: `packages/salvage_spine/tests/test_git_capture.py`

**Interfaces:**
- Consumes: `PlaneId`, `PlaneRecord`, `canonical_json_bytes` from Task 1.
- Produces: `run_git(repo: Path, *args: str) -> bytes`, `snapshot_subject(repo: Path) -> SubjectSnapshot`, and `assert_unchanged(before, after) -> None`.

- [ ] **Step 1: Write a failing temporary-repository drift test**

```python
from pathlib import Path
import subprocess
import pytest

from packages.salvage_spine.git_capture import CaptureDrift, assert_unchanged, snapshot_subject


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_snapshot_detects_ref_and_worktree_drift(tmp_path):
    repo = tmp_path / "repo"
    git(tmp_path, "init", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-m", "seed")
    before = snapshot_subject(repo)
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    after = snapshot_subject(repo)
    with pytest.raises(CaptureDrift):
        assert_unchanged(before, after)
```

- [ ] **Step 2: Run the drift test**

Run: `python -m pytest packages/salvage_spine/tests/test_git_capture.py::test_snapshot_detects_ref_and_worktree_drift -q`

Expected: FAIL because the capture module does not exist.

- [ ] **Step 3: Implement byte-preserving Git interrogation**

Use `subprocess.run([...], check=True, capture_output=True)` without a shell. Snapshot these byte streams: `rev-parse HEAD`, `show-ref --head`, `rev-parse --verify refs/stash`, `status --porcelain=v2 -z --ignored`, `diff --binary --cached`, `diff --binary`, `ls-files -v -z`, and the SHA-256 of the active index file. Treat an absent stash as `None`, not an error.

```python
class CaptureDrift(RuntimeError):
    pass


def assert_unchanged(before: SubjectSnapshot, after: SubjectSnapshot) -> None:
    if before != after:
        raise CaptureDrift("source state changed during capture")
```

- [ ] **Step 4: Add tests for clean index, absent stash, ignored paths, and conflict-stage rendering**

Create each case in an isolated temporary repository; never point unit tests at `C:\~shit\FLOSS`.

- [ ] **Step 5: Run the capture tests and commit**

Run: `python -m pytest packages/salvage_spine/tests/test_git_capture.py -q`

Expected: PASS.

```bash
git add packages/salvage_spine/git_capture.py packages/salvage_spine/tests/test_git_capture.py
git commit -m "feat: add read-only git capture guard"
```

### Task 3: Six-Plane Capture with Secret Exclusion

**Files:**
- Modify: `packages/salvage_spine/git_capture.py`
- Test: `packages/salvage_spine/tests/test_git_capture.py`

**Interfaces:**
- Consumes: Task 2 snapshots and raw Git execution.
- Produces: `capture_planes(repo, remote_main_sha, pr_head_sha, destination, secret_policy) -> tuple[PlaneRecord, ...]`.

- [ ] **Step 1: Write failing tests for destination safety and secret exclusion**

```python
def test_capture_rejects_destination_inside_source(repo_fixture, tmp_path):
    with pytest.raises(ValueError, match="outside the source worktree"):
        capture_planes(repo_fixture, "HEAD", "HEAD", repo_fixture / "capsule", SecretPolicy.default())


def test_secret_named_file_is_redacted_not_copied(repo_fixture, tmp_path):
    secret = repo_fixture / ".env"
    secret.write_text("TOKEN=do-not-copy\n", encoding="utf-8")
    records = capture_planes(repo_fixture, "HEAD", "HEAD", tmp_path / "capsule", SecretPolicy.default())
    assert not any(path.name == ".env" for path in (tmp_path / "capsule").rglob("*"))
    manifest = json.loads((tmp_path / "capsule/local-untracked-ignored/manifest.json").read_text())
    assert manifest[0]["inclusion"] == "redacted"
```

- [ ] **Step 2: Run the two tests and confirm failure**

Run: `python -m pytest packages/salvage_spine/tests/test_git_capture.py -k "destination or secret" -q`

Expected: FAIL because `capture_planes` and `SecretPolicy` are undefined.

- [ ] **Step 3: Implement six plane writers**

Write each plane to its own directory. Use `git bundle create` for remote-main, remote-PR, and local-history refs; copy the index as `index.raw`; write binary diffs without decoding; and inventory tracked, untracked, and ignored files with path, kind, mode, size, SHA-256, and inclusion reason. Screen names case-insensitively for `.env`, `secret`, `token`, `credential`, `api_key`, `.key`, and key-recovery patterns. Do not inspect or persist secret contents after classification.

- [ ] **Step 4: Prove source immutability around capture**

Call `snapshot_subject()` before and after all writes and call `assert_unchanged()`. Add a test that mutates a source file from a test hook between planes and expects `CaptureDrift`.

- [ ] **Step 5: Run capture tests and commit**

Run: `python -m pytest packages/salvage_spine/tests/test_git_capture.py -q`

Expected: PASS.

```bash
git add packages/salvage_spine/git_capture.py packages/salvage_spine/tests/test_git_capture.py
git commit -m "feat: capture six salvage source planes"
```

### Task 4: Capsule Seal and Clean-Room Restoration

**Files:**
- Create: `packages/salvage_spine/seal.py`
- Create: `packages/salvage_spine/restore.py`
- Test: `packages/salvage_spine/tests/test_seal_restore.py`

**Interfaces:**
- Consumes: captured plane directories and records from Task 3.
- Produces: `seal_capsule(root: Path) -> str`, `verify_checksums(root: Path) -> None`, and `restore_and_verify(root: Path, temp_root: Path) -> VerificationRecord`.

- [ ] **Step 1: Write failing tamper and restore tests**

```python
def test_checksum_tamper_fails(captured_capsule):
    seal_capsule(captured_capsule)
    (captured_capsule / "remote-main/refs.txt").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(CapsuleVerificationError):
        verify_checksums(captured_capsule)


def test_clean_room_restore_matches_commit_and_tree(captured_capsule, tmp_path):
    seal_capsule(captured_capsule)
    result = restore_and_verify(captured_capsule, tmp_path / "restore")
    assert result.status == ResultStatus.PASS
    assert result.commit_match is True
    assert result.tree_match is True
```

- [ ] **Step 2: Run the tests and confirm failure**

Run: `python -m pytest packages/salvage_spine/tests/test_seal_restore.py -q`

Expected: FAIL because sealing and restoration modules do not exist.

- [ ] **Step 3: Implement deterministic checksums and provenance root**

Sort paths by UTF-8 byte order, exclude only `checksums.sha256`, `provenance-root.json`, and `verification.json` from the checksum input, and reject symlinks escaping the capsule. Hash the canonical checksum listing into `provenance-root.json`. Record authentication as `local-unanchored` in this slice; do not call it externally anchored.

- [ ] **Step 4: Implement empty-repository restoration**

Initialize a new bare repository beneath `temp_root`, verify each bundle, fetch its refs, and compare expected commit, tree, parent, mode, path-casing, and screened raw-file digests. Return `BLOCKED` when referenced LFS media or submodule repositories are absent; never silently pass.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest packages/salvage_spine/tests/test_seal_restore.py -q`

Expected: PASS.

```bash
git add packages/salvage_spine/seal.py packages/salvage_spine/restore.py packages/salvage_spine/tests/test_seal_restore.py
git commit -m "feat: seal and restore-test salvage capsules"
```

### Task 5: Complete Change-Universe Manifest

**Files:**
- Create: `packages/salvage_spine/manifest.py`
- Test: `packages/salvage_spine/tests/test_manifest.py`

**Interfaces:**
- Consumes: verified capsule metadata and Git object identities.
- Produces: `inventory_change_universe(capsule: Path) -> dict`, `validate_manifest(data: dict) -> list[str]`, and `manifest_digest(data: dict) -> str`.

- [ ] **Step 1: Write failing ownership and classification tests**

```python
def test_every_atom_has_exactly_one_owner():
    data = manifest_fixture()
    data["items"].append({**data["items"][0], "item_id": "duplicate-owner"})
    errors = validate_manifest(data)
    assert "atom atom-1 has 2 owners" in errors


def test_captured_atom_has_null_disposition():
    data = manifest_fixture()
    data["items"][0]["classification_state"] = "captured"
    data["items"][0]["disposition"] = "salvage"
    assert "captured item must have null disposition" in validate_manifest(data)
```

- [ ] **Step 2: Run manifest tests and confirm failure**

Run: `python -m pytest packages/salvage_spine/tests/test_manifest.py -q`

Expected: FAIL because the manifest module does not exist.

- [ ] **Step 3: Implement commit/file-first inventory**

Generate stable atom IDs from source plane, source commit or content digest, path before/after, blob before/after, mode before/after, and exact diff digest. Preserve rename and case-only rename identity. Default new atoms to `classification_state: captured` and `disposition: null`; do not infer salvage intent.

- [ ] **Step 4: Implement graph validation**

Reject duplicate ownership, missing atoms, cyclic `requires` or `generated_by` edges, classified items without one of `salvage|revise|park|reject`, revise items without a replacement, and required-gate actions without scope-bound gate IDs.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest packages/salvage_spine/tests/test_manifest.py -q`

Expected: PASS.

```bash
git add packages/salvage_spine/manifest.py packages/salvage_spine/tests/test_manifest.py
git commit -m "feat: inventory PR38 salvage change universe"
```

### Task 6: Resumable Checkpoints

**Files:**
- Create: `packages/salvage_spine/checkpoint.py`
- Test: `packages/salvage_spine/tests/test_checkpoint.py`

**Interfaces:**
- Consumes: capsule, manifest, and verification digests.
- Produces: `append_checkpoint(path: Path, checkpoint: Checkpoint) -> None` and `load_latest_checkpoint(path: Path) -> Checkpoint`.

- [ ] **Step 1: Write a failing append-only chain test**

```python
def test_checkpoint_chain_detects_rewrite(tmp_path):
    path = tmp_path / "checkpoints.jsonl"
    append_checkpoint(path, checkpoint("capture-complete"))
    append_checkpoint(path, checkpoint("restore-complete"))
    lines = path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace("capture-complete", "altered")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with pytest.raises(CheckpointIntegrityError):
        load_latest_checkpoint(path)
```

- [ ] **Step 2: Run the test and confirm failure**

Run: `python -m pytest packages/salvage_spine/tests/test_checkpoint.py -q`

Expected: FAIL because the checkpoint module does not exist.

- [ ] **Step 3: Implement chained JSONL checkpoints**

Each record contains `sequence`, `previous_digest`, `state_id`, `phase`, input SHAs, capsule root, manifest digest, completed actions, blockers, human decisions, `next_safe_command`, and `recovery_command`. Compute the record digest over canonical JSON excluding its own digest field.

- [ ] **Step 4: Run tests and commit**

Run: `python -m pytest packages/salvage_spine/tests/test_checkpoint.py -q`

Expected: PASS.

```bash
git add packages/salvage_spine/checkpoint.py packages/salvage_spine/tests/test_checkpoint.py
git commit -m "feat: add salvage continuation checkpoints"
```

### Task 7: GitHub Projection Without GitHub Mutation

**Files:**
- Create: `packages/salvage_spine/github_projection.py`
- Create: `docs/superpowers/templates/pr38-stop-merge-comment.md`
- Test: `packages/salvage_spine/tests/test_github_projection.py`

**Interfaces:**
- Consumes: capsule verification, manifest coverage, and checkpoint records.
- Produces: `render_check_summary(evidence: Evidence) -> dict` and `render_stop_merge_comment(evidence: Evidence) -> str`.

- [ ] **Step 1: Write failing scope-language tests**

```python
def test_core_check_name_cannot_imply_global_success():
    summary = render_check_summary(evidence_fixture(core="PASS", preservation="PASS"))
    assert summary["name"] == "Core engineering checks — scoped evidence only"
    assert "verified" not in summary["title"].lower()


def test_comment_refuses_readiness_without_clean_room_restore():
    text = render_stop_merge_comment(evidence_fixture(restore="FAIL"))
    assert "NOT READY FOR CONTAINMENT" in text
    assert "mark this PR Draft" not in text
```

- [ ] **Step 2: Run projection tests and confirm failure**

Run: `python -m pytest packages/salvage_spine/tests/test_github_projection.py -q`

Expected: FAIL because the projection module does not exist.

- [ ] **Step 3: Implement sanitized projections**

Use these exact public names: `Preservation capsule — restore-tested evidence` and `Core engineering checks — scoped evidence only`. Report absolute and same-environment regression dimensions separately. The proposed comment includes locked SHAs, capsule root, manifest digest, unclassified count, hard-stop count, blockers, next safe command, and a statement that GitHub controls do not confer authority.

- [ ] **Step 4: Add the proposed non-canonical template**

The template must begin with `PROPOSED STOP-MERGE NOTICE — DO NOT POST BEFORE PRESERVATION PASSES` and contain no remote API command. It links only sanitized evidence locations; it never links local secret-bearing paths.

- [ ] **Step 5: Run tests and commit**

Run: `python -m pytest packages/salvage_spine/tests/test_github_projection.py -q`

Expected: PASS.

```bash
git add packages/salvage_spine/github_projection.py packages/salvage_spine/tests/test_github_projection.py docs/superpowers/templates/pr38-stop-merge-comment.md
git commit -m "feat: render scoped GitHub salvage evidence"
```

### Task 8: CLI Integration and Spec-Gate Registration

**Files:**
- Create: `packages/salvage_spine/cli.py`
- Create: `scripts/pr38_salvage.py`
- Create: `packages/salvage_spine/tests/test_cli.py`
- Modify: `docs/specs/spec-registry.json`

**Interfaces:**
- Consumes: all Task 1-7 interfaces.
- Produces commands `capture`, `verify`, `inventory`, `render-github`, and `status`.

- [ ] **Step 1: Write a failing CLI help and no-mutation test**

```python
def test_cli_exposes_only_local_commands(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "capture" in output
    assert "verify" in output
    assert "mark-draft" not in output
    assert "post-comment" not in output
```

- [ ] **Step 2: Run CLI tests and confirm failure**

Run: `python -m pytest packages/salvage_spine/tests/test_cli.py -q`

Expected: FAIL because the CLI does not exist.

- [ ] **Step 3: Implement explicit local-only commands**

`capture` requires `--repo`, `--remote-main-sha`, `--pr-head-sha`, and `--output`; it rejects moving ref names for the two SHA arguments. `verify` performs checksums and clean-room restoration. `inventory` refuses an unverified capsule. `render-github` writes Markdown and JSON files locally. `status` verifies the checkpoint chain and prints the next safe command.

- [ ] **Step 4: Add the thin script and registry entry**

```python
from packages.salvage_spine.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
```

Register `FLOSS/scripts/pr38_salvage.py` in `docs/specs/spec-registry.json` with the one-line spec: `Local-only preserve-first capture, verification, inventory, and evidence rendering for PR #38 salvage.`

- [ ] **Step 5: Run CLI and spec-gate checks**

Run: `python -m pytest packages/salvage_spine/tests/test_cli.py -q`

Expected: PASS.

Run: `python scripts/spec_gate.py --path scripts/pr38_salvage.py`

Expected: no unregistered-artifact warning for the new script. The repository-wide gate may still report pre-existing failures; record them separately.

- [ ] **Step 6: Commit CLI integration**

```bash
git add packages/salvage_spine/cli.py packages/salvage_spine/tests/test_cli.py scripts/pr38_salvage.py docs/specs/spec-registry.json
git commit -m "feat: add local PR38 salvage CLI"
```

### Task 9: End-to-End Temporary-Repository Proof

**Files:**
- Create: `packages/salvage_spine/tests/test_end_to_end.py`

**Interfaces:**
- Consumes: CLI from Task 8.
- Produces: a regression test proving capture, restore, inventory, projection, and continuation without touching a live remote.

- [ ] **Step 1: Write the end-to-end test**

Create a bare `origin`, a `main` commit, a divergent PR ref, a local-only commit, staged content, tracked unstaged content, one ordinary untracked file, one ignored file, and one `.env` exclusion. Invoke each CLI command through `main([...])`. Assert six planes, a passing restore record, complete atom ownership, a redacted secret entry, a chained checkpoint, and locally rendered GitHub summaries.

- [ ] **Step 2: Run the test and inspect the expected initial failure**

Run: `python -m pytest packages/salvage_spine/tests/test_end_to_end.py -q`

Expected: FAIL at the first missing integration behavior; fix only that behavior before rerunning.

- [ ] **Step 3: Make the minimal integration corrections**

Limit changes to the owning module. Do not add network calls, PR mutation commands, automatic cleanup, or broad workflow files.

- [ ] **Step 4: Run the complete salvage package suite**

Run: `python -m pytest packages/salvage_spine/tests -q`

Expected: PASS.

- [ ] **Step 5: Commit the end-to-end proof**

```bash
git add packages/salvage_spine/tests/test_end_to_end.py packages/salvage_spine
git commit -m "test: prove PR38 preservation capsule flow"
```

### Task 10: Live Readiness Audit Without Containment

**Files:**
- Runtime only: `C:\~shit\_pr38_salvage_capsules\pr38\` followed by the generated state ID
- Modify only if evidence exposes a defect: the smallest owning package/test file.

**Interfaces:**
- Consumes: complete local CLI and the exact refreshed source SHAs.
- Produces: a local, restore-tested capsule and manifest inventory; no GitHub mutation.

- [ ] **Step 1: Recheck live refs and source worktree state**

Run `git fetch origin main` and fetch PR #38 into a new namespaced local ref without checking it out. Record exact base/head SHAs and `git status --porcelain=v2 -z --ignored` digest. If any audited SHA changed, create a new state ID rather than overwriting earlier evidence.

- [ ] **Step 2: Capture to the ignored runtime surface**

Run in PowerShell after fetching PR #38 into `refs/salvage/pr38`:

```powershell
$main = git -c safe.directory=C:/~shit/FLOSS -C C:/~shit/FLOSS rev-parse origin/main
$pr = git -c safe.directory=C:/~shit/FLOSS -C C:/~shit/FLOSS rev-parse refs/salvage/pr38
$state = (Get-Date -Format 'yyyyMMddTHHmmss') + '-' + $main.Substring(0, 12) + '-' + $pr.Substring(0, 12)
$output = "C:/~shit/_pr38_salvage_capsules/pr38/$state"
python scripts/pr38_salvage.py capture --repo C:/~shit/FLOSS --remote-main-sha $main --pr-head-sha $pr --output $output
```

Expected: exit 0 with six plane digests and no source-state drift.

- [ ] **Step 3: Verify and inventory**

Run `verify`, then `inventory`, then `status` against the same state directory. Expected: preservation is `PASS`, every atom has one owner, all dispositions are initially null, and the next safe command is `render-github`.

- [ ] **Step 4: Render but do not post GitHub artifacts**

Run `render-github`. Inspect the proposed comment and check JSON for secrets, local private paths, global-verification language, and incorrect Phase 0 implications. Do not mark PR #38 Draft and do not post the comment in this task.

- [ ] **Step 5: Run regression and repository checks**

Run: `python -m pytest packages/salvage_spine/tests -q`

Expected: PASS.

Run: `python -m pytest packages/orchestrator packages/source_chain packages/metacoordinator_mcp packages/activity_log/tests -q`

Expected baseline: 145 tests passed as of 2026-07-13; report any current difference without hiding it.

Run: `python scripts/spec_gate.py`

Expected baseline: repository-wide FAIL on 10 pre-existing unregistered governed artifacts as of 2026-07-13. The new script must not add an eleventh failure.

- [ ] **Step 6: Commit only code or test corrections**

Never copy capsule payloads into the workspace or commit them. If no defect was found, make no empty commit.

## Explicit Follow-On Plans

This first slice deliberately does not combine independent systems. After its live capsule passes:

1. Write a verification-runner plan for `preservation`, `core`, `sweettest-migration`, `consent-e2e`, and `substrate-bridge` profiles with absolute/regression dimensions.
2. Write a reconstruction plan only after one to three desired outcomes and their dependency cones are selected from the manifest.
3. Write a GitHub projection plan only after sanitized artifact retention, repository permissions, and required-check policy are inspected live. That plan may upload evidence and publish checks, but cannot capture local planes.
4. Request explicit human confirmation before marking PR #38 Draft or posting the proposed stop-merge comment.
5. Keep ADR, integrity-zome, consensus-gateway, canonical-promotion, deletion, and protected-config work in separately authorized plans.

## Self-Review Record

- Spec coverage: this plan covers six-plane capture, source immutability, secret exclusion, authenticated local sealing, clean-room restoration, complete-universe inventory, one-owner validation, checkpoints, and GitHub projections. Verification profiles, reconstruction, and native Holochain scenarios are intentionally split into follow-on plans because each is an independent reviewable subsystem.
- Type consistency: plane IDs, statuses, capsule records, verification records, manifest digests, and checkpoint digests flow forward through named interfaces.
- Authority check: no task modifies PR #38, an ADR, integrity-zome logic, consensus-gateway logic, canonical status, protected configuration, or source checkout state.
- External-review correction: Perplexity’s useful GitHub mapping is represented, but its broad `truth_status: Verified` and “canonical template” language are not adopted. The template remains proposed and evidence claims remain scoped.
