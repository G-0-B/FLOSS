from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


class CaptureDrift(RuntimeError):
    """Raised when the source repository changes during a capture."""


@dataclass(frozen=True)
class SubjectSnapshot:
    """Immutable read-only snapshot of source-repository state."""

    head: bytes
    refs: bytes
    stash: bytes | None
    index_sha256: str
    status: bytes
    staged_diff: bytes
    unstaged_diff: bytes
    tracked_flags: bytes


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return environment


def run_git(repo: Path, *args: str) -> bytes:
    """Run a read-only Git query and return its standard output unchanged."""

    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        shell=False,
        env=_git_environment(),
    )
    return completed.stdout


def _optional_stash(repo: Path) -> bytes | None:
    completed = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "refs/stash"],
        check=False,
        capture_output=True,
        shell=False,
        env=_git_environment(),
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _index_path(repo: Path) -> Path:
    raw_path = run_git(
        repo,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "index",
    )
    return Path(raw_path.rstrip(b"\r\n").decode("utf-8", errors="surrogateescape"))


def snapshot_subject(repo: Path) -> SubjectSnapshot:
    """Capture the Git state needed to prove that a source stayed unchanged."""

    index_digest = hashlib.sha256(_index_path(repo).read_bytes()).hexdigest()
    return SubjectSnapshot(
        head=run_git(repo, "rev-parse", "HEAD"),
        refs=run_git(repo, "show-ref", "--head"),
        stash=_optional_stash(repo),
        index_sha256=index_digest,
        status=run_git(repo, "status", "--porcelain=v2", "-z", "--ignored"),
        staged_diff=run_git(repo, "diff", "--binary", "--cached"),
        unstaged_diff=run_git(repo, "diff", "--binary"),
        tracked_flags=run_git(repo, "ls-files", "-v", "-z"),
    )


def assert_unchanged(before: SubjectSnapshot, after: SubjectSnapshot) -> None:
    """Fail closed unless every captured byte and digest is unchanged."""

    if before != after:
        raise CaptureDrift("source state changed during capture")
