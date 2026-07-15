from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from packages.salvage_spine.git_capture import (
    CaptureDrift,
    assert_unchanged,
    run_git,
    snapshot_subject,
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
    )


def initialized_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    git(tmp_path, "init", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-m", "seed")
    return repo


def test_snapshot_detects_ref_and_worktree_drift(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    before = snapshot_subject(repo)

    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    after = snapshot_subject(repo)

    with pytest.raises(CaptureDrift, match="source state changed during capture"):
        assert_unchanged(before, after)


def test_clean_index_and_absent_stash(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)

    snapshot = snapshot_subject(repo)

    assert snapshot.stash is None
    assert snapshot.status == b""
    assert snapshot.staged_diff == b""
    assert snapshot.unstaged_diff == b""
    assert len(snapshot.index_sha256) == 64
    assert set(snapshot.index_sha256) <= set("0123456789abcdef")
    assert snapshot.tracked_flags == b"H a.txt\0"
    assert_unchanged(snapshot, snapshot_subject(repo))


def test_snapshot_records_ignored_paths(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "ignore logs")
    (repo / "ignored.log").write_text("ignored\n", encoding="utf-8")

    snapshot = snapshot_subject(repo)

    assert b"! ignored.log\0" in snapshot.status


def test_snapshot_records_staged_changes(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    (repo / "a.txt").write_text("staged\n", encoding="utf-8")
    git(repo, "add", "a.txt")

    snapshot = snapshot_subject(repo)

    assert b"1 M." in snapshot.status
    assert b"+staged" in snapshot.staged_diff
    assert snapshot.unstaged_diff == b""


def test_snapshot_records_conflict_stage_rendering(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    initial_branch = run_git(repo, "branch", "--show-current").strip().decode("ascii")
    git(repo, "checkout", "-b", "feature")
    (repo / "a.txt").write_text("feature\n", encoding="utf-8")
    git(repo, "commit", "-am", "feature change")
    git(repo, "checkout", initial_branch)
    (repo / "a.txt").write_text("main\n", encoding="utf-8")
    git(repo, "commit", "-am", "main change")

    merge = git(repo, "merge", "feature", check=False)
    assert merge.returncode != 0

    snapshot = snapshot_subject(repo)

    assert b"u UU" in snapshot.status
    assert snapshot.tracked_flags.count(b"a.txt\0") == 3


def test_snapshot_resolves_linked_worktree_index(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    linked = tmp_path / "linked"
    git(repo, "worktree", "add", "-b", "linked", str(linked))

    snapshot = snapshot_subject(linked)

    assert len(snapshot.index_sha256) == 64
    assert snapshot.status == b""
