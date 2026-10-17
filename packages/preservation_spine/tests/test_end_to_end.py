from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess

import pytest

from packages.preservation_spine.checkpoint import load_latest_checkpoint
from packages.preservation_spine.cli import main
from packages.preservation_spine.models import PlaneId, ResultStatus
from packages.preservation_spine.seal import provenance_root


@dataclass(frozen=True)
class _RepositoryFixture:
    origin: Path
    repo: Path
    shared_sha: str
    main_sha: str
    pr_sha: str
    local_sha: str
    remote_url: bytes
    secret: bytes


@dataclass(frozen=True)
class _Invocation:
    returncode: int
    stdout: dict[str, object] | None
    stderr: str


@dataclass(frozen=True)
class _ExpectedLocalDeltas:
    staged_diff: bytes
    tracked_unstaged_diff: bytes


@dataclass(frozen=True)
class _DirectorySnapshot:
    root_identity: tuple[int, int, int, int, bytes]
    entries: tuple[tuple[str, tuple[int, int, int, int, bytes]], ...]


@dataclass(frozen=True)
class _SourceSnapshot:
    repository_identity: tuple[int, int, int, int, bytes]
    git_marker_identity: tuple[int, int, int, int, bytes]
    git_directory: _DirectorySnapshot
    git_common_directory: _DirectorySnapshot
    head_file: tuple[int, int, int, int, bytes]
    head_sha: bytes
    refs: bytes
    index: tuple[int, int, int, int, bytes]
    config: tuple[int, int, int, int, bytes]
    worktree: tuple[tuple[str, tuple[int, int, int, int, bytes]], ...]


_STAGED_PATH = "staged.txt"
_STAGED_CONTENT = b"staged content\n"
_TRACKED_PATH = "local.txt"
_TRACKED_INDEX_CONTENT = b"local committed content\n"
_TRACKED_WORKTREE_CONTENT = b"tracked unstaged content\n"


def _run(*command: str, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        check=True,
        capture_output=True,
        shell=False,
    )


def _git(repo: Path, *args: str) -> bytes:
    return _run("git", "-C", str(repo), *args).stdout


def _required_local_deltas(repo: Path) -> _ExpectedLocalDeltas:
    staged_names = _git(repo, "diff", "--cached", "--name-only", "-z")
    tracked_names = _git(repo, "diff-files", "--name-only", "-z")
    assert staged_names == _STAGED_PATH.encode("utf-8") + b"\0"
    assert tracked_names == _TRACKED_PATH.encode("utf-8") + b"\0"
    assert (repo / _STAGED_PATH).read_bytes() == _STAGED_CONTENT
    assert _git(repo, "show", f":{_STAGED_PATH}") == _STAGED_CONTENT
    assert (repo / _TRACKED_PATH).read_bytes() == _TRACKED_WORKTREE_CONTENT
    assert _git(repo, "show", f":{_TRACKED_PATH}") == _TRACKED_INDEX_CONTENT

    # Must mirror git_capture.capture_planes exactly, --full-index included.
    # Without the flag Git abbreviates the `index` line and the capture records
    # null blob identities; this expectation is what proves the capture keeps
    # real provenance, so it has to ask for the same bytes.
    staged_diff = _git(repo, "diff", "--binary", "--full-index", "--cached")
    tracked_unstaged_diff = _git(repo, "diff-files", "--binary", "--full-index")
    assert b"diff --git a/staged.txt b/staged.txt\n" in staged_diff
    assert b"+staged content\n" in staged_diff
    assert b"diff --git a/local.txt b/local.txt\n" in tracked_unstaged_diff
    assert b"-local committed content\n" in tracked_unstaged_diff
    assert b"+tracked unstaged content\n" in tracked_unstaged_diff
    return _ExpectedLocalDeltas(
        staged_diff=staged_diff,
        tracked_unstaged_diff=tracked_unstaged_diff,
    )


def _commit_file(repo: Path, path: str, content: bytes, message: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    _git(repo, "add", "--", path)
    _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD").decode("ascii").strip()


def _build_repository(
    tmp_path: Path, *, linked_worktree: bool = False
) -> _RepositoryFixture:
    origin = tmp_path / "origin.git"
    repo = tmp_path / ("primary" if linked_worktree else "source")
    _run("git", "init", "--bare", "--initial-branch=main", str(origin))
    _run("git", "init", "--initial-branch=main", str(repo))
    _git(repo, "config", "user.email", "task9@example.invalid")
    _git(repo, "config", "user.name", "Task 9")
    _git(repo, "remote", "add", "origin", str(origin))

    shared_sha = _commit_file(
        repo,
        ".gitignore",
        b".env\nignored/\n",
        "shared ignore policy",
    )
    _git(repo, "checkout", "-b", "pr38")
    pr_sha = _commit_file(repo, "pr.txt", b"divergent pr content\n", "pr change")
    _git(repo, "push", "origin", "HEAD:refs/pull/38/head")

    _git(repo, "checkout", "main")
    main_sha = _commit_file(
        repo,
        "main.txt",
        b"divergent main content\n",
        "main change",
    )
    _git(repo, "push", "--set-upstream", "origin", "main")

    _git(repo, "checkout", "pr38")
    local_sha = _commit_file(
        repo,
        "local.txt",
        b"local committed content\n",
        "local only change",
    )
    if linked_worktree:
        primary = repo
        _git(primary, "checkout", "main")
        repo = tmp_path / "source"
        _git(primary, "worktree", "add", str(repo), "pr38")

    (repo / _STAGED_PATH).write_bytes(_STAGED_CONTENT)
    _git(repo, "add", "--", _STAGED_PATH)
    (repo / _TRACKED_PATH).write_bytes(_TRACKED_WORKTREE_CONTENT)
    (repo / "ordinary.txt").write_bytes(b"ordinary untracked content\n")
    (repo / "ignored").mkdir()
    (repo / "ignored" / "cache.bin").write_bytes(b"ignored content\n")
    secret = b"TASK9_SUPER_SECRET_DO_NOT_COPY\n"
    (repo / ".env").write_bytes(secret)

    assert (
        _git(repo, "merge-base", main_sha, pr_sha).decode("ascii").strip() == shared_sha
    )
    assert (
        _git(origin, "rev-parse", "refs/heads/main").decode("ascii").strip() == main_sha
    )
    assert (
        _git(origin, "rev-parse", "refs/pull/38/head").decode("ascii").strip() == pr_sha
    )
    assert _git(repo, "rev-parse", "HEAD").decode("ascii").strip() == local_sha
    remote_url = _git(repo, "remote", "get-url", "origin")
    assert "://" not in remote_url.decode("utf-8")
    return _RepositoryFixture(
        origin=origin,
        repo=repo,
        shared_sha=shared_sha,
        main_sha=main_sha,
        pr_sha=pr_sha,
        local_sha=local_sha,
        remote_url=remote_url,
        secret=secret,
    )


def _path_identity(path: Path) -> tuple[int, int, int, int, bytes]:
    metadata = path.lstat()
    file_type = stat.S_IFMT(metadata.st_mode)
    if stat.S_ISREG(metadata.st_mode):
        content = path.read_bytes()
    elif stat.S_ISLNK(metadata.st_mode):
        content = os.readlink(path).encode("utf-8", errors="surrogateescape")
    else:
        content = b""
    return (
        metadata.st_dev,
        metadata.st_ino,
        file_type,
        stat.S_IMODE(metadata.st_mode),
        content,
    )


def _tree_snapshot(
    root: Path, *, excluded_roots: frozenset[str] = frozenset()
) -> tuple[tuple[str, tuple[int, int, int, int, bytes]], ...]:
    entries: list[tuple[str, tuple[int, int, int, int, bytes]]] = []
    for path in sorted(root.rglob("*"), key=lambda value: value.as_posix()):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in excluded_roots:
            continue
        entries.append((relative.as_posix(), _path_identity(path)))
    return tuple(entries)


def _resolved_git_path(repo: Path, *args: str) -> Path:
    raw_path = _git(repo, "rev-parse", "--path-format=absolute", *args)
    return Path(
        raw_path.rstrip(b"\r\n").decode("utf-8", errors="surrogateescape")
    ).resolve(strict=True)


def _directory_snapshot(root: Path) -> _DirectorySnapshot:
    return _DirectorySnapshot(
        root_identity=_path_identity(root),
        entries=_tree_snapshot(root),
    )


def _source_snapshot(repo: Path) -> _SourceSnapshot:
    git_marker = repo / ".git"
    git_directory = _resolved_git_path(repo, "--git-dir")
    git_common_directory = _resolved_git_path(repo, "--git-common-dir")
    return _SourceSnapshot(
        repository_identity=_path_identity(repo),
        git_marker_identity=_path_identity(git_marker),
        git_directory=_directory_snapshot(git_directory),
        git_common_directory=_directory_snapshot(git_common_directory),
        head_file=_path_identity(_resolved_git_path(repo, "--git-path", "HEAD")),
        head_sha=_git(repo, "rev-parse", "HEAD"),
        refs=_git(repo, "show-ref", "--head"),
        index=_path_identity(_resolved_git_path(repo, "--git-path", "index")),
        config=_path_identity(_resolved_git_path(repo, "--git-path", "config")),
        worktree=_tree_snapshot(repo, excluded_roots=frozenset({".git"})),
    )


def _invoke(capsys: pytest.CaptureFixture[str], arguments: list[str]) -> _Invocation:
    returncode = main(arguments)
    streams = capsys.readouterr()
    stdout = json.loads(streams.out) if streams.out else None
    assert stdout is None or isinstance(stdout, dict)
    return _Invocation(returncode=returncode, stdout=stdout, stderr=streams.err)


def _all_file_bytes(root: Path) -> bytes:
    return b"".join(
        path.read_bytes()
        for path in sorted(root.rglob("*"), key=lambda value: value.as_posix())
        if path.is_file()
    )


@pytest.mark.parametrize("linked_worktree", [False, True], ids=["normal", "linked"])
def test_real_end_to_end_flow_preserves_evidence_and_fails_closed(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    linked_worktree: bool,
) -> None:
    fixture = _build_repository(tmp_path, linked_worktree=linked_worktree)
    assert (fixture.repo / ".git").is_file() is linked_worktree
    expected_deltas = _required_local_deltas(fixture.repo)
    state_dir = tmp_path / "task9-state"
    restore_dir = tmp_path / "clean-room"
    projection_dir = tmp_path / "github-projection"
    source_before = _source_snapshot(fixture.repo)
    origin_before = _tree_snapshot(fixture.origin)
    origin_refs_before = _git(fixture.origin, "show-ref")

    capture = _invoke(
        capsys,
        [
            "capture",
            "--repo",
            str(fixture.repo),
            "--remote-main-sha",
            fixture.main_sha,
            "--pr-head-sha",
            fixture.pr_sha,
            "--output",
            str(state_dir),
        ],
    )
    verify = _invoke(
        capsys,
        [
            "verify",
            "--capsule",
            str(state_dir),
            "--restore",
            str(restore_dir),
            "--forbid-root",
            str(fixture.repo),
            "--forbid-root",
            str(fixture.origin),
        ],
    )
    inventory = _invoke(capsys, ["inventory", "--capsule", str(state_dir)])
    render = _invoke(
        capsys,
        [
            "render-github",
            "--capsule",
            str(state_dir),
            "--output",
            str(projection_dir),
        ],
    )
    status_result = _invoke(capsys, ["status", "--capsule", str(state_dir)])

    assert _source_snapshot(fixture.repo) == source_before
    assert _tree_snapshot(fixture.origin) == origin_before
    assert _git(fixture.repo, "remote", "get-url", "origin") == fixture.remote_url
    assert (
        _git(fixture.repo, "rev-parse", "HEAD").decode("ascii").strip()
        == fixture.local_sha
    )
    assert (
        _git(fixture.origin, "rev-parse", "refs/heads/main").decode("ascii").strip()
        == fixture.main_sha
    )
    assert (
        _git(fixture.origin, "rev-parse", "refs/pull/38/head").decode("ascii").strip()
        == fixture.pr_sha
    )

    assert capture.returncode == 0
    assert capture.stdout is not None
    capsule = state_dir / "capsule"
    capsule_record = json.loads((state_dir / "capsule.json").read_text("utf-8"))
    plane_records = {record["plane_id"]: record for record in capsule_record["planes"]}
    assert set(plane_records) == {plane.value for plane in PlaneId}
    assert {path.name for path in capsule.iterdir() if path.is_dir()} == {
        plane.value for plane in PlaneId
    }
    assert plane_records[PlaneId.REMOTE_MAIN.value]["subject_id"] == fixture.main_sha
    assert plane_records[PlaneId.REMOTE_PR.value]["subject_id"] == fixture.pr_sha
    assert plane_records[PlaneId.LOCAL_HISTORY.value]["subject_id"] == fixture.local_sha
    assert capsule_record["status"] == ResultStatus.BLOCKED.value

    opaque_planes = {
        PlaneId.REMOTE_MAIN.value,
        PlaneId.REMOTE_PR.value,
        PlaneId.LOCAL_HISTORY.value,
        PlaneId.LOCAL_INDEX.value,
    }
    for plane_id in opaque_planes:
        assert plane_records[plane_id] == {
            **plane_records[plane_id],
            "eligibility": "ineligible",
            "sensitivity": "opaque-sensitive",
            "status": ResultStatus.BLOCKED.value,
            "verification": "opaque-preserved",
        }
    assert plane_records[PlaneId.LOCAL_TRACKED.value] == {
        **plane_records[PlaneId.LOCAL_TRACKED.value],
        "eligibility": "eligible",
        "sensitivity": "ordinary",
        "status": ResultStatus.PASS.value,
        "verification": "byte-equality",
    }
    assert plane_records[PlaneId.LOCAL_UNTRACKED.value] == {
        **plane_records[PlaneId.LOCAL_UNTRACKED.value],
        "eligibility": "ineligible",
        "sensitivity": "redacted",
        "status": ResultStatus.BLOCKED.value,
        "verification": "unverifiable-redacted",
    }

    captured_staged_diff = (
        capsule / PlaneId.LOCAL_INDEX.value / "staged.diff"
    ).read_bytes()
    captured_tracked_unstaged_diff = (
        capsule / PlaneId.LOCAL_TRACKED.value / "unstaged.diff"
    ).read_bytes()
    assert captured_staged_diff == expected_deltas.staged_diff
    assert captured_tracked_unstaged_diff == expected_deltas.tracked_unstaged_diff

    local_manifest = json.loads(
        (capsule / PlaneId.LOCAL_UNTRACKED.value / "manifest.json").read_text("utf-8")
    )
    entries = {entry["path"]: entry for entry in local_manifest}
    assert entries["ordinary.txt"]["inclusion"] == "copied"
    assert entries["ignored/cache.bin"]["inclusion"] == "copied"
    assert entries[".env"]["inclusion"] == "redacted"

    verification_path = capsule / "verification.json"
    verification = json.loads(verification_path.read_text("utf-8"))
    verification_digest = hashlib.sha256(verification_path.read_bytes()).hexdigest()
    verified_checkpoint = load_latest_checkpoint(state_dir / "checkpoints.jsonl")
    assert verified_checkpoint.input_shas == {
        "remote_main": fixture.main_sha,
        "pr_head": fixture.pr_sha,
    }
    assert capture.stdout["capsule_root"] == verified_checkpoint.capsule_root
    assert capsule_record["state_id"] == verified_checkpoint.state_id
    assert verified_checkpoint.capsule_root == provenance_root(capsule)
    assert verified_checkpoint.capsule_root == verification["provenance_root"]
    assert verified_checkpoint.verification_digest == verification_digest
    assert verification["checksum_status"] == ResultStatus.PASS.value
    assert verification["commit_match"] is True
    assert verification["tree_match"] is True
    assert verification["artifact_match"] is True
    assert verification["status"] == ResultStatus.BLOCKED.value
    assert verification["blockers"] == [
        "opaque-preservation-ineligible",
        "redacted-evidence-ineligible",
    ]
    restored_planes = {plane["plane_id"]: plane for plane in verification["planes"]}
    for plane_id in opaque_planes:
        assert restored_planes[plane_id]["status"] == ResultStatus.BLOCKED.value
        assert restored_planes[plane_id]["blockers"] == [
            "opaque-preservation-ineligible"
        ]
    assert restored_planes[PlaneId.LOCAL_TRACKED.value]["status"] == (
        ResultStatus.PASS.value
    )
    assert restored_planes[PlaneId.LOCAL_TRACKED.value]["blockers"] == []
    assert restored_planes[PlaneId.LOCAL_UNTRACKED.value]["status"] == (
        ResultStatus.BLOCKED.value
    )
    assert restored_planes[PlaneId.LOCAL_UNTRACKED.value]["blockers"] == [
        "redacted-evidence-ineligible"
    ]
    index_artifact_digests = dict(
        restored_planes[PlaneId.LOCAL_INDEX.value]["artifact_digests"]
    )
    tracked_artifact_digests = dict(
        restored_planes[PlaneId.LOCAL_TRACKED.value]["artifact_digests"]
    )
    assert (
        index_artifact_digests["staged.diff"]
        == hashlib.sha256(expected_deltas.staged_diff).hexdigest()
    )
    assert (
        tracked_artifact_digests["unstaged.diff"]
        == hashlib.sha256(expected_deltas.tracked_unstaged_diff).hexdigest()
    )

    assert verify.returncode == 0
    assert verify.stderr == ""
    assert verify.stdout == {
        "inventory_eligible": True,
        "containment_eligible": False,
        "next_safe_command": "python scripts/preservation_spine.py inventory --capsule STATE_DIR",
        "phase": "verification-complete",
        "status": ResultStatus.BLOCKED.value,
        "verification_digest": verification_digest,
    }
    # Inventory now succeeds — the capsule is authenticated even though
    # containment is blocked by design-ineligible planes.
    assert inventory.returncode == 0
    assert inventory.stderr == ""
    assert inventory.stdout is not None
    assert inventory.stdout["phase"] == "inventory-complete"
    # Render-github also succeeds and produces a stop-merge file.
    assert render.returncode == 0
    assert render.stderr == ""
    assert render.stdout is not None
    assert render.stdout["phase"] == "projection-rendered"
    # The stop-merge comment must say NOT READY (containment blocked).
    comment_path = projection_dir / "stop-merge-comment.md"
    assert comment_path.is_file()
    comment_text = comment_path.read_text("utf-8")
    assert "NOT READY" in comment_text
    assert status_result.returncode == 0
    assert status_result.stderr == ""
    assert status_result.stdout["phase"] == "projection-rendered"

    checkpoint_records = [
        json.loads(line)
        for line in (state_dir / "checkpoints.jsonl").read_text("utf-8").splitlines()
    ]
    assert [record["sequence"] for record in checkpoint_records] == [0, 1, 2, 3]
    assert [record["phase"] for record in checkpoint_records] == [
        "capture-complete",
        "verification-complete",
        "inventory-complete",
        "projection-rendered",
    ]
    assert checkpoint_records[0]["previous_digest"] is None
    assert checkpoint_records[1]["previous_digest"] == checkpoint_records[0]["digest"]
    assert checkpoint_records[1]["verification_digest"] == verification_digest
    assert checkpoint_records[1]["blockers"] == [
        "opaque-preservation-ineligible",
        "redacted-evidence-ineligible",
    ]

    state_bytes = _all_file_bytes(state_dir)
    restore_bytes = _all_file_bytes(restore_dir)
    command_bytes = json.dumps(
        [
            capture.stdout,
            verify.stdout,
            inventory.stdout,
            render.stdout,
            status_result.stdout,
            capture.stderr,
            verify.stderr,
            inventory.stderr,
            render.stderr,
            status_result.stderr,
        ],
        sort_keys=True,
    ).encode("utf-8")
    for evidence_bytes in (state_bytes, restore_bytes, command_bytes):
        assert fixture.secret not in evidence_bytes
        for private_path in (tmp_path, fixture.repo, fixture.origin, state_dir):
            assert str(private_path).encode("utf-8") not in evidence_bytes
            assert private_path.as_posix().encode("utf-8") not in evidence_bytes

    assert _source_snapshot(fixture.repo) == source_before
    assert _tree_snapshot(fixture.origin) == origin_before
    assert _git(fixture.repo, "remote", "get-url", "origin") == fixture.remote_url
    assert _git(fixture.origin, "show-ref") == origin_refs_before


@pytest.mark.parametrize("linked_worktree", [False, True], ids=["normal", "linked"])
def test_source_snapshot_detects_hidden_git_directory_mutation(
    tmp_path: Path,
    linked_worktree: bool,
) -> None:
    fixture = _build_repository(tmp_path, linked_worktree=linked_worktree)
    before = _source_snapshot(fixture.repo)

    mutation = _resolved_git_path(fixture.repo, "--git-dir")
    (mutation / "TASK9_UNMONITORED_MUTATION").write_bytes(b"hidden mutation\n")

    assert _source_snapshot(fixture.repo) != before


@pytest.mark.parametrize("missing_state", ["staged", "tracked-unstaged"])
def test_required_local_delta_probe_rejects_missing_state(
    tmp_path: Path,
    missing_state: str,
) -> None:
    fixture = _build_repository(tmp_path)
    assert _required_local_deltas(fixture.repo)
    if missing_state == "staged":
        _git(fixture.repo, "reset", "--", _STAGED_PATH)
    else:
        (fixture.repo / _TRACKED_PATH).write_bytes(_TRACKED_INDEX_CONTENT)

    with pytest.raises(AssertionError):
        _required_local_deltas(fixture.repo)
