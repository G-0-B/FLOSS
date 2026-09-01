from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from pathlib import PureWindowsPath
from typing import Callable

from packages.preservation_spine.models import (
    PlaneEligibility,
    PlaneId,
    PlaneRecord,
    PlaneSensitivity,
    PlaneVerification,
    ResultStatus,
    canonical_json_bytes,
)


class CaptureEvidenceError(RuntimeError):
    """Base class for failed source-state equality evidence."""


class CaptureDrift(CaptureEvidenceError):
    """Raised when the source repository changes during a capture."""


class CaptureUnverifiable(CaptureEvidenceError):
    """Raised when redaction makes requested byte equality unprovable."""


@dataclass(frozen=True)
class SecretPolicy:
    """Path-name rules that redact likely secret-bearing files before reads."""

    markers: tuple[str, ...]

    @classmethod
    def default(cls) -> SecretPolicy:
        """Return the conservative default secret-name policy."""

        return cls(
            markers=(
                ".env",
                "secret",
                "token",
                "credential",
                "api_key",
                "private_key",
                "private-key",
                ".key",
                "id_rsa",
                "id_ed25519",
                "keystore",
                "recovery",
                "seed",
                "mnemonic",
            )
        )

    def is_secret(self, relative_path: str) -> bool:
        """Classify a relative path without reading its filesystem target."""

        folded = relative_path.casefold()
        return any(marker.casefold() in folded for marker in self.markers)


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


@dataclass(frozen=True)
class _InventoryState:
    tracked_paths: tuple[str, ...]
    untracked_paths: tuple[str, ...]
    ignored_paths: tuple[str, ...]
    digest: str


@dataclass(frozen=True)
class _PlaneDisposition:
    sensitivity: PlaneSensitivity
    eligibility: PlaneEligibility
    verification: PlaneVerification
    status: ResultStatus

    def metadata(self) -> dict[str, str]:
        return {
            "eligibility": self.eligibility.value,
            "sensitivity": self.sensitivity.value,
            "status": self.status.value,
            "verification": self.verification.value,
        }


_ORDINARY_DISPOSITION = _PlaneDisposition(
    sensitivity=PlaneSensitivity.ORDINARY,
    eligibility=PlaneEligibility.ELIGIBLE,
    verification=PlaneVerification.BYTE_EQUALITY,
    status=ResultStatus.PASS,
)
_OPAQUE_DISPOSITION = _PlaneDisposition(
    sensitivity=PlaneSensitivity.OPAQUE_SENSITIVE,
    eligibility=PlaneEligibility.INELIGIBLE,
    verification=PlaneVerification.OPAQUE_PRESERVED,
    status=ResultStatus.BLOCKED,
)
_REDACTED_DISPOSITION = _PlaneDisposition(
    sensitivity=PlaneSensitivity.REDACTED,
    eligibility=PlaneEligibility.INELIGIBLE,
    verification=PlaneVerification.UNVERIFIABLE_REDACTED,
    status=ResultStatus.BLOCKED,
)


def _git_environment() -> dict[str, str]:
    """Environment for read-only capture queries, with Git routing stripped.

    Copying os.environ wholesale let ambient GIT_* routing variables override
    the repository chosen by `git -C`. Under a Git hook -- which is exactly
    where a capture is plausibly triggered -- GIT_DIR, GIT_INDEX_FILE and
    GIT_OBJECT_DIRECTORY are all set. History and index queries would then read
    a DIFFERENT repository while worktree paths still came from `--repo`,
    producing a hybrid capsule that claims to preserve the requested source and
    does not. restore.py already strips these; capture did not.

    Deliberately NOT setting GIT_CONFIG_GLOBAL=/dev/null or
    GIT_CONFIG_NOSYSTEM the way restore does. Restore builds a clean room and
    wants Git's behaviour to be independent of the machine. Capture is the
    opposite: it must read the source checkout AS CONFIGURED, because
    core.autocrlf, gitattributes and clean/smudge filters are part of what the
    bytes on disk actually are. Stripping routing is about pointing at the right
    repository; it is not a licence to reinterpret its contents.
    """
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"
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


def _shared_index_files(repo: Path) -> list[Path]:
    """Backing files an index may depend on under `core.splitIndex`.

    With splitIndex enabled, `.git/index` is a stub -- 186 bytes in a two-file
    repository -- carrying a `link` extension that points at
    `$GIT_DIR/sharedindex.<oid>`, which holds the actual entries. Copying
    index.raw on its own therefore preserved a pointer to a file the capsule
    does not contain, and the staged diff is not a substitute: it does not carry
    conflict-stage entries or index extensions.

    Returned so they can be copied beside index.raw and restored together.
    """
    raw = run_git(repo, "rev-parse", "--path-format=absolute", "--git-dir")
    git_dir = Path(raw.rstrip(b"\r\n").decode("utf-8", errors="surrogateescape"))
    return sorted(path for path in git_dir.glob("sharedindex.*") if path.is_file())


def _index_path(repo: Path) -> Path:
    raw_path = run_git(
        repo,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "index",
    )
    return Path(raw_path.rstrip(b"\r\n").decode("utf-8", errors="surrogateescape"))


def _diff_with_exclusions(
    repo: Path,
    *base_args: str,
    exclude_paths: tuple[str, ...] = (),
) -> bytes:
    if not exclude_paths:
        return run_git(repo, *base_args)
    pathspecs = (".", *(f":(exclude){path}" for path in exclude_paths))
    return run_git(repo, *base_args, "--", *pathspecs)


def snapshot_subject(
    repo: Path,
    *,
    exclude_paths: tuple[str, ...] = (),
) -> SubjectSnapshot:
    """Capture the Git state needed to prove that a source stayed unchanged."""

    index_digest = hashlib.sha256(_index_path(repo).read_bytes()).hexdigest()
    return SubjectSnapshot(
        head=run_git(repo, "rev-parse", "HEAD"),
        refs=run_git(repo, "show-ref", "--head"),
        stash=_optional_stash(repo),
        index_sha256=index_digest,
        status=run_git(repo, "status", "--porcelain=v2", "-z", "--ignored"),
        # --full-index is load-bearing, not cosmetic. Without it Git abbreviates
        # the `index` line object names to 7 characters, and `_diff_atoms` only
        # records an id of length 40 or 64 -- so every ordinary text change
        # captured both blob identities as null. A preservation capsule whose
        # whole purpose is reconstructable provenance was silently recording
        # none. Verified against git 2.54: without the flag `blob_before` and
        # `blob_after` are None; with it they are the real SHAs.
        staged_diff=_diff_with_exclusions(
            repo,
            "diff",
            "--no-ext-diff",
            "--binary",
            "--full-index",
            "--cached",
            exclude_paths=exclude_paths,
        ),
        unstaged_diff=_diff_with_exclusions(
            repo,
            "diff-files",
            "--no-ext-diff",
            "--binary",
            "--full-index",
            exclude_paths=exclude_paths,
        ),
        tracked_flags=run_git(repo, "ls-files", "-v", "-z"),
    )


def assert_unchanged(before: SubjectSnapshot, after: SubjectSnapshot) -> None:
    """Fail closed unless every captured byte and digest is unchanged."""

    if before != after:
        raise CaptureDrift("source state changed during capture")


def _repository_root(repo: Path) -> Path:
    raw_root = run_git(repo, "rev-parse", "--path-format=absolute", "--show-toplevel")
    return Path(
        raw_root.rstrip(b"\r\n").decode("utf-8", errors="surrogateescape")
    ).resolve(strict=True)


def _validate_destination(source_root: Path, destination: Path) -> None:
    destination_root = destination.resolve(strict=False)
    if destination_root == source_root or source_root in destination_root.parents:
        raise ValueError("destination must be outside the source worktree")


def _decode_paths(raw_paths: bytes) -> tuple[str, ...]:
    decoded_paths: list[str] = []
    seen_paths: set[str] = set()
    for raw_path in raw_paths.split(b"\0"):
        if not raw_path:
            continue
        relative_path = raw_path.decode("utf-8", errors="surrogateescape")
        if relative_path.endswith("/"):
            relative_path = relative_path[:-1]
        canonical_path = _safe_relative_path(relative_path).as_posix()
        if canonical_path in seen_paths:
            raise ValueError(
                f"duplicate repository path after canonicalization: {canonical_path!r}"
            )
        seen_paths.add(canonical_path)
        decoded_paths.append(canonical_path)
    return tuple(decoded_paths)


def _safe_relative_path(relative_path: str) -> PurePosixPath:
    relative = PurePosixPath(relative_path)
    windows_relative = PureWindowsPath(relative_path)
    if (
        not relative_path
        or "\\" in relative_path
        or relative.is_absolute()
        or not relative.parts
        or ".." in relative.parts
        or relative_path != relative.as_posix()
        or windows_relative.is_absolute()
        or bool(windows_relative.drive)
    ):
        raise ValueError(f"unsafe repository-relative path: {relative_path!r}")
    return relative


def _worktree_path(repo: Path, relative_path: str) -> Path:
    relative = _safe_relative_path(relative_path)
    return repo.joinpath(*relative.parts)


def _kind_for_mode(mode: int) -> str:
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "special"


def _has_symlink_parent(repo: Path, path: Path) -> bool:
    relative_parent = path.parent.relative_to(repo)
    current = repo
    for part in relative_parent.parts:
        current /= part
        try:
            if stat.S_ISLNK(current.lstat().st_mode):
                return True
        except FileNotFoundError:
            return False
    return False


def _read_regular_file(
    repo: Path, relative_path: str
) -> tuple[bytes | None, dict[str, object]]:
    path = _worktree_path(repo, relative_path)
    try:
        before = path.lstat()
    except FileNotFoundError:
        return None, {
            "kind": "missing",
            "mode": None,
            "size": None,
            "sha256": None,
            "inclusion": "excluded",
            "reason": "missing-from-worktree",
        }

    kind = _kind_for_mode(before.st_mode)
    mode = stat.S_IMODE(before.st_mode)
    if kind == "symlink":
        return None, {
            "kind": kind,
            "mode": mode,
            "size": None,
            "sha256": None,
            "inclusion": "excluded",
            "reason": "symlink-not-followed",
        }
    if kind != "file":
        return None, {
            "kind": kind,
            "mode": mode,
            "size": None,
            "sha256": None,
            "inclusion": "excluded",
            "reason": "special-file-not-copied",
        }
    if _has_symlink_parent(repo, path):
        return None, {
            "kind": kind,
            "mode": mode,
            "size": None,
            "sha256": None,
            "inclusion": "excluded",
            "reason": "symlink-parent-not-followed",
        }
    resolved = path.resolve(strict=True)
    source_root = repo.resolve(strict=True)
    if resolved == source_root or source_root not in resolved.parents:
        return None, {
            "kind": kind,
            "mode": mode,
            "size": None,
            "sha256": None,
            "inclusion": "excluded",
            "reason": "outside-source-not-followed",
        }

    content = path.read_bytes()
    after = path.lstat()
    stable_fields = [
        "st_dev",
        "st_ino",
        "st_mode",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ]
    if hasattr(before, "st_birthtime_ns") and hasattr(after, "st_birthtime_ns"):
        stable_fields.append("st_birthtime_ns")
    if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
        raise CaptureDrift("source state changed during capture")
    return content, {
        "kind": kind,
        "mode": mode,
        "size": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "inclusion": "eligible",
        "reason": "content-read",
    }


def _inventory_state(repo: Path, secret_policy: SecretPolicy) -> _InventoryState:
    tracked_paths = _decode_paths(run_git(repo, "ls-files", "-z"))
    untracked_paths = _decode_paths(
        run_git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    )
    ignored_paths = _decode_paths(
        run_git(
            repo,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        )
    )
    categories: dict[str, str] = {}
    for category, paths in (
        ("tracked", tracked_paths),
        ("untracked", untracked_paths),
        ("ignored", ignored_paths),
    ):
        for path in paths:
            if path in categories:
                raise ValueError(
                    "duplicate repository path across inventory categories"
                )
            categories[path] = category
    fingerprints: list[dict[str, object]] = []
    for relative_path in sorted(categories):
        path = _worktree_path(repo, relative_path)
        if secret_policy.is_secret(relative_path):
            try:
                metadata = path.lstat()
            except FileNotFoundError:
                fingerprints.append(
                    {
                        "category": categories[relative_path],
                        "classification": "redacted",
                        "path": relative_path,
                        "state": "missing",
                    }
                )
            else:
                fingerprints.append(
                    {
                        "birth_ns": getattr(metadata, "st_birthtime_ns", None),
                        "category": categories[relative_path],
                        "changed_ns": metadata.st_ctime_ns,
                        "classification": "redacted",
                        "device": metadata.st_dev,
                        "inode": metadata.st_ino,
                        "kind": _kind_for_mode(metadata.st_mode),
                        "mode": metadata.st_mode,
                        "modified_ns": metadata.st_mtime_ns,
                        "path": relative_path,
                        "size": metadata.st_size,
                    }
                )
            continue

        _, metadata = _read_regular_file(repo, relative_path)
        try:
            path_stat = path.lstat()
        except FileNotFoundError:
            path_stat = None
        fingerprints.append(
            {
                "category": categories[relative_path],
                "birth_ns": (
                    getattr(path_stat, "st_birthtime_ns", None) if path_stat else None
                ),
                "changed_ns": path_stat.st_ctime_ns if path_stat else None,
                "classification": "permitted",
                "device": path_stat.st_dev if path_stat else None,
                "inode": path_stat.st_ino if path_stat else None,
                "metadata": metadata,
                "modified_ns": path_stat.st_mtime_ns if path_stat else None,
                "path": relative_path,
            }
        )
    return _InventoryState(
        tracked_paths=tracked_paths,
        untracked_paths=untracked_paths,
        ignored_paths=ignored_paths,
        digest=hashlib.sha256(canonical_json_bytes(fingerprints)).hexdigest(),
    )


def _redacted_entry(
    relative_path: str, *, reason: str = "secret-name"
) -> dict[str, object]:
    return {
        "path": relative_path,
        "kind": "redacted",
        "mode": None,
        "size": None,
        "sha256": None,
        "inclusion": "redacted",
        "reason": reason,
    }


def _tracked_gitlinks(repo: Path) -> set[str]:
    gitlinks: set[str] = set()
    for record in run_git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if not record:
            continue
        prefix, raw_path = record.split(b"\t", 1)
        if prefix.startswith(b"160000 "):
            gitlinks.add(raw_path.decode("utf-8", errors="surrogateescape"))
    return gitlinks


def _tracked_manifest(
    repo: Path,
    tracked_paths: tuple[str, ...],
    secret_policy: SecretPolicy,
) -> list[dict[str, object]]:
    gitlinks = _tracked_gitlinks(repo)
    manifest: list[dict[str, object]] = []
    for relative_path in tracked_paths:
        if secret_policy.is_secret(relative_path):
            manifest.append(_redacted_entry(relative_path))
            continue
        if relative_path in gitlinks:
            manifest.append(
                {
                    "path": relative_path,
                    "kind": "gitlink",
                    "mode": 0o160000,
                    "size": None,
                    "sha256": None,
                    "inclusion": "excluded",
                    "reason": "gitlink-not-followed",
                }
            )
            continue
        _, metadata = _read_regular_file(repo, relative_path)
        metadata["path"] = relative_path
        if metadata["inclusion"] == "eligible":
            metadata["inclusion"] = "metadata-only"
            metadata["reason"] = "tracked-worktree-inventory"
        manifest.append(metadata)
    return sorted(manifest, key=lambda entry: str(entry["path"]))


def _untracked_manifest_and_payload(
    repo: Path,
    untracked_paths: tuple[str, ...],
    ignored_paths: tuple[str, ...],
    plane_root: Path,
    secret_policy: SecretPolicy,
) -> list[dict[str, object]]:
    path_reasons = {
        **{path: "untracked" for path in untracked_paths},
        **{path: "ignored" for path in ignored_paths},
    }
    manifest: list[dict[str, object]] = []
    payload_root = plane_root / "payload"
    for relative_path in sorted(path_reasons):
        if secret_policy.is_secret(relative_path):
            manifest.append(_redacted_entry(relative_path))
            continue
        content, metadata = _read_regular_file(repo, relative_path)
        metadata["path"] = relative_path
        if content is not None:
            relative = _safe_relative_path(relative_path)
            payload_path = payload_root.joinpath(*relative.parts)
            payload_path.parent.mkdir(parents=True, exist_ok=True)
            payload_path.write_bytes(content)
            metadata["inclusion"] = "copied"
            metadata["reason"] = path_reasons[relative_path]
        manifest.append(metadata)
    return manifest


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical_json_bytes(value))


def _resolved_commit(repo: Path, revision: str) -> str:
    return (
        run_git(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
        .strip()
        .decode("ascii")
    )


def _storage_object_format(repo: Path) -> str:
    """Return the source repository's object storage format without mutation."""

    return (
        run_git(repo, "rev-parse", "--show-object-format=storage")
        .strip()
        .decode("ascii")
    )


def _write_history_plane(
    repo: Path,
    plane_root: Path,
    plane_id: PlaneId,
    subject_id: str,
    object_format: str,
    disposition: _PlaneDisposition,
) -> None:
    plane_root.mkdir()
    bundle_source = plane_root / "source.git"
    captured_ref = "refs/heads/master"
    subprocess.run(
        [
            "git",
            "init",
            "--bare",
            f"--object-format={object_format}",
            "--initial-branch=master",
            "--template=",
            str(bundle_source),
        ],
        check=True,
        capture_output=True,
        shell=False,
        env=_git_environment(),
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(bundle_source),
            "-c",
            "protocol.file.allow=always",
            "fetch",
            "--no-write-fetch-head",
            "--no-tags",
            str(repo),
            f"{subject_id}:{captured_ref}",
        ],
        check=True,
        capture_output=True,
        shell=False,
        env=_git_environment(),
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(bundle_source),
            "bundle",
            "create",
            str(plane_root / "repository.bundle"),
            captured_ref,
        ],
        check=True,
        capture_output=True,
        shell=False,
        env=_git_environment(),
    )
    (plane_root / "refs.txt").write_bytes(
        f"{subject_id} {captured_ref}\n".encode("utf-8")
    )
    _write_json(
        plane_root / "identity.json",
        {
            **disposition.metadata(),
            "bundle_ref": captured_ref,
            "bundle_scope": "destination-owned-exact-ref",
            "object_format": object_format,
            "plane_id": plane_id.value,
            "schema_version": "1",
            "subject_id": subject_id,
        },
    )


def _directory_digest(root: Path) -> str:
    """Hash sorted relative names and exact file bytes using a length-framed format."""

    digest = hashlib.sha256(b"salvage-plane-directory-v1\0")
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def capture_planes(
    repo: Path,
    remote_main_sha: str,
    pr_head_sha: str,
    destination: Path,
    secret_policy: SecretPolicy,
    *,
    require_byte_equality: bool = False,
    _between_planes: Callable[[PlaneId], None] | None = None,
) -> tuple[PlaneRecord, ...]:
    """Capture six planes; blocked records still preserve but cannot release."""

    repo = _repository_root(repo)
    _validate_destination(repo, destination)
    inventory_before = _inventory_state(repo, secret_policy)
    tracked_paths = inventory_before.tracked_paths
    untracked_paths = inventory_before.untracked_paths
    ignored_paths = inventory_before.ignored_paths
    secret_tracked_paths = tuple(
        path for path in tracked_paths if secret_policy.is_secret(path)
    )
    secret_untracked_paths = tuple(
        path
        for path in (*untracked_paths, *ignored_paths)
        if secret_policy.is_secret(path)
    )
    before = snapshot_subject(repo, exclude_paths=secret_tracked_paths)
    remote_main_id = _resolved_commit(repo, remote_main_sha)
    remote_pr_id = _resolved_commit(repo, pr_head_sha)
    local_history_id = _resolved_commit(repo, "HEAD")
    object_format = _storage_object_format(repo)
    index_bytes = _index_path(repo).read_bytes()
    shared_index_files = _shared_index_files(repo)
    tracked_manifest = _tracked_manifest(repo, tracked_paths, secret_policy)

    destination.mkdir(parents=True, exist_ok=False)
    subjects = {
        PlaneId.REMOTE_MAIN: remote_main_id,
        PlaneId.REMOTE_PR: remote_pr_id,
        PlaneId.LOCAL_HISTORY: local_history_id,
        PlaneId.LOCAL_INDEX: before.index_sha256,
        PlaneId.LOCAL_TRACKED: hashlib.sha256(before.unstaged_diff).hexdigest(),
        PlaneId.LOCAL_UNTRACKED: "pending-manifest",
    }
    dispositions = {
        PlaneId.REMOTE_MAIN: _OPAQUE_DISPOSITION,
        PlaneId.REMOTE_PR: _OPAQUE_DISPOSITION,
        PlaneId.LOCAL_HISTORY: _OPAQUE_DISPOSITION,
        PlaneId.LOCAL_INDEX: _OPAQUE_DISPOSITION,
        PlaneId.LOCAL_TRACKED: (
            _REDACTED_DISPOSITION if secret_tracked_paths else _ORDINARY_DISPOSITION
        ),
        PlaneId.LOCAL_UNTRACKED: (
            _REDACTED_DISPOSITION if secret_untracked_paths else _ORDINARY_DISPOSITION
        ),
    }
    records: list[PlaneRecord] = []

    for plane_id in PlaneId:
        plane_root = destination / plane_id.value
        if plane_id in {
            PlaneId.REMOTE_MAIN,
            PlaneId.REMOTE_PR,
            PlaneId.LOCAL_HISTORY,
        }:
            _write_history_plane(
                repo,
                plane_root,
                plane_id,
                subjects[plane_id],
                object_format,
                dispositions[plane_id],
            )
        elif plane_id is PlaneId.LOCAL_INDEX:
            plane_root.mkdir()
            (plane_root / "index.raw").write_bytes(index_bytes)
            # Under core.splitIndex, index.raw is only a link to these.
            for shared in shared_index_files:
                (plane_root / shared.name).write_bytes(shared.read_bytes())
            (plane_root / "staged.diff").write_bytes(before.staged_diff)
            _write_json(
                plane_root / "metadata.json",
                {
                    **dispositions[plane_id].metadata(),
                    "index_sha256": before.index_sha256,
                    "shared_index_files": [
                        {
                            "name": shared.name,
                            "sha256": hashlib.sha256(shared.read_bytes()).hexdigest(),
                        }
                        for shared in shared_index_files
                    ],
                    "secret_path_exclusions": list(secret_tracked_paths),
                },
            )
        elif plane_id is PlaneId.LOCAL_TRACKED:
            plane_root.mkdir()
            (plane_root / "unstaged.diff").write_bytes(before.unstaged_diff)
            _write_json(plane_root / "manifest.json", tracked_manifest)
            _write_json(
                plane_root / "metadata.json",
                {
                    **dispositions[plane_id].metadata(),
                    "secret_path_exclusions": list(secret_tracked_paths),
                },
            )
        else:
            plane_root.mkdir()
            manifest = _untracked_manifest_and_payload(
                repo,
                untracked_paths,
                ignored_paths,
                plane_root,
                secret_policy,
            )
            _write_json(plane_root / "manifest.json", manifest)
            _write_json(
                plane_root / "metadata.json",
                {
                    **dispositions[plane_id].metadata(),
                    "secret_path_exclusions": list(secret_untracked_paths),
                },
            )
            subjects[plane_id] = hashlib.sha256(
                canonical_json_bytes(manifest)
            ).hexdigest()

        disposition = dispositions[plane_id]
        records.append(
            PlaneRecord(
                plane_id=plane_id,
                subject_id=subjects[plane_id],
                digest=_directory_digest(plane_root),
                sensitivity=disposition.sensitivity,
                eligibility=disposition.eligibility,
                verification=disposition.verification,
                status=disposition.status,
            )
        )
        if _between_planes is not None:
            _between_planes(plane_id)

    after = snapshot_subject(repo, exclude_paths=secret_tracked_paths)
    inventory_after = _inventory_state(repo, secret_policy)
    assert_unchanged(before, after)
    if inventory_before != inventory_after:
        raise CaptureDrift("source state changed during capture")
    if require_byte_equality and (secret_tracked_paths or secret_untracked_paths):
        raise CaptureUnverifiable(
            "redacted mutable paths prevent byte-equality verification"
        )
    return tuple(records)
