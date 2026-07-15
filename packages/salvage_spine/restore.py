"""Clean-room restoration and scoped verification of sealed salvage capsules."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess

from .models import (
    PlaneEligibility,
    PlaneId,
    PlaneRecord,
    PlaneSensitivity,
    PlaneVerification,
    ResultStatus,
    canonical_json_bytes,
)
from .seal import (
    CapsuleVerificationError,
    _atomic_write_fixed,
    _hash_regular_file,
    _read_regular_bytes,
    _walk_regular_files,
    provenance_root,
    verify_checksums,
)

_HISTORY_PLANES = (
    PlaneId.REMOTE_MAIN,
    PlaneId.REMOTE_PR,
    PlaneId.LOCAL_HISTORY,
)


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_COUNT": "0",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


@dataclass(frozen=True)
class PlaneRestoreResult:
    """Scoped evidence for one restored or authenticated capture plane."""

    plane_id: PlaneId
    subject_id: str
    status: ResultStatus
    commit_match: bool | None
    tree_match: bool | None
    parent_match: bool | None
    mode_path_match: bool | None
    object_reachability: bool | None
    tree_id: str | None
    parents_digest: str | None
    mode_path_digest: str | None
    evidence_digest: str
    artifact_digests: tuple[tuple[str, str], ...]
    artifact_match: bool | None
    payload_digest: str | None
    payload_count: int | None
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class VerificationRecord:
    """Aggregate clean-room evidence without a global-green authority claim."""

    schema_version: str
    authentication: str
    provenance_root: str
    status: ResultStatus
    checksum_status: ResultStatus
    planes: tuple[PlaneRestoreResult, ...]
    commit_match: bool
    tree_match: bool
    artifact_match: bool
    blockers: tuple[str, ...]


def _run_git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            env=_git_environment(),
            shell=False,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise CapsuleVerificationError("clean-room Git verification failed") from exc


def _run_git_all_output(repo: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            env=_git_environment(),
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        raise CapsuleVerificationError("clean-room Git verification failed") from exc
    return result.stdout + b"\n" + result.stderr


def _initialize_bare(repo: Path, object_format: str) -> None:
    try:
        subprocess.run(
            [
                "git",
                "init",
                "--bare",
                f"--object-format={object_format}",
                "--initial-branch=master",
                "--template=",
                str(repo),
            ],
            check=True,
            capture_output=True,
            env=_git_environment(),
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        raise CapsuleVerificationError(
            "clean-room repository initialization failed"
        ) from exc


def _verify_repository_layout(repository: Path) -> None:
    repository_root = repository.resolve(strict=True)
    queries = (
        ("rev-parse", "--absolute-git-dir"),
        ("rev-parse", "--git-common-dir"),
        ("rev-parse", "--git-path", "objects"),
    )
    for query in queries:
        try:
            rendered = _run_git(repository, *query).strip().decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CapsuleVerificationError("effective Git path is not UTF-8") from exc
        effective = Path(rendered)
        if not effective.is_absolute():
            effective = repository / effective
        try:
            resolved = effective.resolve(strict=True)
        except OSError as exc:
            raise CapsuleVerificationError("effective Git path is unavailable") from exc
        if resolved != repository_root and not resolved.is_relative_to(repository_root):
            raise CapsuleVerificationError(
                "effective Git path escapes the plane destination"
            )


def _canonical_json(path: Path) -> dict[str, object] | list[object]:
    try:
        content = _read_regular_bytes(path)
        value = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CapsuleVerificationError("capsule metadata is malformed") from exc
    if content != canonical_json_bytes(value):
        raise CapsuleVerificationError("capsule metadata is not canonical JSON")
    if not isinstance(value, (dict, list)):
        raise CapsuleVerificationError("capsule metadata has an invalid shape")
    return value


def _safe_relative(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise CapsuleVerificationError("capsule inventory path is invalid")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CapsuleVerificationError("capsule inventory path is not UTF-8") from exc
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or value != path.as_posix():
        raise CapsuleVerificationError("capsule inventory path is unsafe")
    return path


def _disposition_record(
    plane_id: PlaneId,
    subject_id: str,
    digest: str,
    metadata: dict[str, object],
) -> PlaneRecord:
    try:
        return PlaneRecord(
            plane_id=plane_id,
            subject_id=subject_id,
            digest=digest,
            sensitivity=PlaneSensitivity(metadata["sensitivity"]),
            eligibility=PlaneEligibility(metadata["eligibility"]),
            verification=PlaneVerification(metadata["verification"]),
            status=ResultStatus(metadata["status"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CapsuleVerificationError("plane disposition metadata is invalid") from exc


def _plane_evidence_digest(plane_root: Path) -> str:
    digest = hashlib.sha256(b"salvage-restore-plane-evidence-v1\0")
    files = sorted(
        _walk_regular_files(plane_root, excluded_root_names=frozenset()),
        key=lambda path: path.relative_to(plane_root).as_posix().encode("utf-8"),
    )
    for path in files:
        relative = path.relative_to(plane_root).as_posix().encode("utf-8")
        content = _read_regular_bytes(path)
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def _list_bundle_heads(bundle: Path) -> tuple[tuple[str, str], ...]:
    try:
        output = subprocess.run(
            ["git", "bundle", "list-heads", str(bundle)],
            check=True,
            capture_output=True,
            env=_git_environment(),
            shell=False,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise CapsuleVerificationError("history bundle is unreadable") from exc
    heads: list[tuple[str, str]] = []
    for line in output.splitlines():
        fields = line.decode("ascii", errors="strict").split(" ", 1)
        if len(fields) != 2:
            raise CapsuleVerificationError("history bundle head is malformed")
        heads.append((fields[0], fields[1]))
    return tuple(heads)


def _parse_tree(tree_bytes: bytes) -> tuple[tuple[str, str, str, bytes], ...]:
    entries: list[tuple[str, str, str, bytes]] = []
    for item in tree_bytes.split(b"\0"):
        if not item:
            continue
        try:
            header, path = item.split(b"\t", 1)
            mode, object_type, object_id = header.decode("ascii").split(" ")
        except (ValueError, UnicodeDecodeError) as exc:
            raise CapsuleVerificationError("restored Git tree is malformed") from exc
        if mode not in {"100644", "100755", "120000", "160000"}:
            raise CapsuleVerificationError("restored Git tree has an unsupported mode")
        if b"\0" in path or not path:
            raise CapsuleVerificationError("restored Git tree path is invalid")
        entries.append((mode, object_type, object_id, path))
    if len({entry[3] for entry in entries}) != len(entries):
        raise CapsuleVerificationError("restored Git tree has duplicate paths")
    return tuple(entries)


def _reachable_dependency_blockers(repo: Path, subject_id: str) -> tuple[str, ...]:
    blockers: set[str] = set()
    blob_ids: set[str] = set()
    seen_trees: set[str] = set()
    commits = _run_git(repo, "rev-list", subject_id).splitlines()
    if not commits:
        raise CapsuleVerificationError("restored history has no reachable commits")
    for commit in commits:
        commit_id = commit.decode("ascii")
        tree_id = (
            _run_git(repo, "rev-parse", f"{commit_id}^{{tree}}").strip().decode("ascii")
        )
        if tree_id in seen_trees:
            continue
        seen_trees.add(tree_id)
        tree_bytes = _run_git(repo, "ls-tree", "-rz", "-r", "--full-tree", commit_id)
        for mode, object_type, object_id, _ in _parse_tree(tree_bytes):
            if mode == "160000":
                blockers.add("submodule-repository-missing")
            elif object_type == "blob":
                blob_ids.add(object_id)
    for object_id in sorted(blob_ids):
        try:
            size = int(_run_git(repo, "cat-file", "-s", object_id).strip())
        except ValueError as exc:
            raise CapsuleVerificationError("restored blob size is malformed") from exc
        if size > 1024:
            continue
        content = _run_git(repo, "cat-file", "blob", object_id)
        if content.startswith(b"version https://git-lfs.github.com/spec/v1\n"):
            blockers.add("lfs-media-missing")
    return tuple(sorted(blockers))


def _tree_evidence(
    repo: Path, subject_id: str
) -> tuple[str, str, str, tuple[str, ...]]:
    commit = _run_git(repo, "cat-file", "-p", subject_id)
    lines = commit.splitlines()
    tree_lines = [line for line in lines if line.startswith(b"tree ")]
    if len(tree_lines) != 1:
        raise CapsuleVerificationError("restored commit tree identity is malformed")
    tree_id = tree_lines[0].split(b" ", 1)[1].decode("ascii")
    parents = [line.split(b" ", 1)[1] for line in lines if line.startswith(b"parent ")]
    parents_digest = hashlib.sha256(b"\n".join(parents) + b"\n").hexdigest()
    tree_bytes = _run_git(repo, "ls-tree", "-rz", "-r", "--full-tree", subject_id)
    entries = _parse_tree(tree_bytes)
    mode_path = b"".join(
        mode.encode("ascii")
        + b"\0"
        + object_type.encode("ascii")
        + b"\0"
        + object_id.encode("ascii")
        + b"\0"
        + path
        + b"\0"
        for mode, object_type, object_id, path in entries
    )
    mode_path_digest = hashlib.sha256(mode_path).hexdigest()
    blockers = _reachable_dependency_blockers(repo, subject_id)
    return tree_id, parents_digest, mode_path_digest, blockers


def _restore_history_plane(
    capsule: Path,
    restore_root: Path,
    plane_id: PlaneId,
) -> PlaneRestoreResult:
    plane_root = capsule / plane_id.value
    identity_value = _canonical_json(plane_root / "identity.json")
    if not isinstance(identity_value, dict):
        raise CapsuleVerificationError("history identity metadata is invalid")
    identity = identity_value
    if identity.get("plane_id") != plane_id.value:
        raise CapsuleVerificationError("history plane identity is inconsistent")
    subject_id = identity.get("subject_id")
    object_format = identity.get("object_format")
    bundle_ref = identity.get("bundle_ref")
    expected_identity_keys = {
        "bundle_ref",
        "bundle_scope",
        "eligibility",
        "object_format",
        "plane_id",
        "schema_version",
        "sensitivity",
        "status",
        "subject_id",
        "verification",
    }
    expected_id_length = {"sha1": 40, "sha256": 64}
    if (
        set(identity) != expected_identity_keys
        or not isinstance(subject_id, str)
        or not isinstance(object_format, str)
        or object_format not in {"sha1", "sha256"}
        or len(subject_id) != expected_id_length.get(object_format, 0)
        or any(character not in "0123456789abcdef" for character in subject_id)
        or bundle_ref != "refs/heads/master"
        or identity.get("bundle_scope") != "destination-owned-exact-ref"
        or identity.get("schema_version") != "1"
    ):
        raise CapsuleVerificationError("history plane identity is malformed")
    try:
        refs_bytes = _read_regular_bytes(plane_root / "refs.txt")
    except CapsuleVerificationError as exc:
        raise CapsuleVerificationError("history refs metadata is missing") from exc
    if refs_bytes != f"{subject_id} {bundle_ref}\n".encode("ascii"):
        raise CapsuleVerificationError("history refs metadata does not match identity")
    evidence_digest = _plane_evidence_digest(plane_root)
    disposition = _disposition_record(plane_id, subject_id, evidence_digest, identity)
    bundle = plane_root / "repository.bundle"
    destination = restore_root / plane_id.value
    destination.mkdir()
    repository = destination / "repository.git"
    _initialize_bare(repository, object_format)
    _verify_repository_layout(repository)

    heads = _list_bundle_heads(bundle)
    if heads != ((subject_id, bundle_ref),):
        raise CapsuleVerificationError("history bundle subject does not match identity")
    _run_git(repository, "bundle", "verify", str(bundle))
    try:
        subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "-c",
                "protocol.file.allow=always",
                "fetch",
                "--no-write-fetch-head",
                "--no-tags",
                str(bundle),
                f"{bundle_ref}:refs/heads/master",
            ],
            check=True,
            capture_output=True,
            env=_git_environment(),
            shell=False,
        )
    except subprocess.CalledProcessError as exc:
        raise CapsuleVerificationError("history bundle restore failed") from exc
    _verify_repository_layout(repository)

    restored_subject = _run_git(repository, "rev-parse", "refs/heads/master").strip()
    if restored_subject.decode("ascii") != subject_id:
        raise CapsuleVerificationError(
            "restored history subject does not match identity"
        )
    restored_format = _run_git(
        repository, "rev-parse", "--show-object-format=storage"
    ).strip()
    if restored_format.decode("ascii") != object_format:
        raise CapsuleVerificationError("restored history object format does not match")
    refs = _run_git(repository, "show-ref").splitlines()
    if refs != [f"{subject_id} refs/heads/master".encode("ascii")]:
        raise CapsuleVerificationError("restored history has unexpected refs")
    _run_git(repository, "fsck", "--strict", "--no-reflogs")
    unreachable = _run_git_all_output(
        repository, "fsck", "--no-reflogs", "--unreachable"
    )
    if b"unreachable " in unreachable or b"dangling " in unreachable:
        raise CapsuleVerificationError(
            "restored history contains unexpected unreachable objects"
        )
    tree_id, parents_digest, mode_path_digest, blockers = _tree_evidence(
        repository, subject_id
    )
    resolved_tree = _run_git(repository, "rev-parse", f"{subject_id}^{{tree}}").strip()
    if resolved_tree.decode("ascii") != tree_id:
        raise CapsuleVerificationError("restored tree identity does not match commit")
    plane_blockers = {"opaque-preservation-ineligible", *blockers}
    return PlaneRestoreResult(
        plane_id=plane_id,
        subject_id=subject_id,
        status=disposition.status,
        commit_match=True,
        tree_match=True,
        parent_match=True,
        mode_path_match=True,
        object_reachability=True,
        tree_id=tree_id,
        parents_digest=parents_digest,
        mode_path_digest=mode_path_digest,
        evidence_digest=evidence_digest,
        artifact_digests=(),
        artifact_match=None,
        payload_digest=None,
        payload_count=None,
        blockers=tuple(sorted(plane_blockers)),
    )


def _metadata_for_plane(plane_root: Path) -> dict[str, object]:
    value = _canonical_json(plane_root / "metadata.json")
    if not isinstance(value, dict):
        raise CapsuleVerificationError("plane metadata is invalid")
    return value


def _manifest_facts(
    manifest: list[object], *, allowed_inclusions: frozenset[str]
) -> tuple[set[str], dict[str, dict[str, object]]]:
    redacted_paths: set[str] = set()
    entries: dict[str, dict[str, object]] = {}
    required_fields = {"inclusion", "kind", "mode", "path", "reason", "sha256", "size"}
    for raw_entry in manifest:
        if not isinstance(raw_entry, dict) or set(raw_entry) != required_fields:
            raise CapsuleVerificationError("manifest entry is invalid")
        relative = _safe_relative(raw_entry.get("path"))
        relative_name = relative.as_posix()
        if relative_name in entries:
            raise CapsuleVerificationError(
                "untracked inventory contains duplicate paths"
            )
        inclusion = raw_entry.get("inclusion")
        if not isinstance(inclusion, str) or inclusion not in allowed_inclusions:
            raise CapsuleVerificationError("manifest inclusion is not verifiable")
        if inclusion == "redacted":
            if (
                raw_entry.get("kind") != "redacted"
                or raw_entry.get("mode") is not None
                or raw_entry.get("size") is not None
                or raw_entry.get("sha256") is not None
            ):
                raise CapsuleVerificationError("redacted manifest metadata is invalid")
            redacted_paths.add(relative_name)
        elif inclusion == "copied":
            mode = raw_entry.get("mode")
            size = raw_entry.get("size")
            digest = raw_entry.get("sha256")
            if (
                raw_entry.get("kind") != "file"
                or not isinstance(mode, int)
                or isinstance(mode, bool)
                or mode < 0
                or mode > 0o7777
                or not isinstance(size, int)
                or isinstance(size, bool)
                or size < 0
                or not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise CapsuleVerificationError("copied manifest metadata is invalid")
        entries[relative_name] = raw_entry
    return redacted_paths, entries


def _secret_exclusions(metadata: dict[str, object]) -> tuple[str, ...]:
    value = metadata.get("secret_path_exclusions")
    if not isinstance(value, list):
        raise CapsuleVerificationError("secret exclusion metadata is invalid")
    exclusions = tuple(_safe_relative(item).as_posix() for item in value)
    if len(set(exclusions)) != len(exclusions) or list(exclusions) != sorted(
        exclusions, key=lambda item: item.encode("utf-8")
    ):
        raise CapsuleVerificationError("secret exclusion metadata is inconsistent")
    return exclusions


def _require_manifest_disposition(
    metadata: dict[str, object], redacted_paths: set[str]
) -> None:
    exclusions = set(_secret_exclusions(metadata))
    if exclusions != redacted_paths:
        raise CapsuleVerificationError(
            "manifest disposition exclusions are inconsistent"
        )
    expected = (
        ("redacted", "ineligible", "unverifiable-redacted", "BLOCKED")
        if redacted_paths
        else ("ordinary", "eligible", "byte-equality", "PASS")
    )
    actual = (
        metadata.get("sensitivity"),
        metadata.get("eligibility"),
        metadata.get("verification"),
        metadata.get("status"),
    )
    if actual != expected:
        raise CapsuleVerificationError("manifest disposition metadata is inconsistent")


def _validate_untracked_payload(
    plane_root: Path, metadata: dict[str, object]
) -> tuple[str, str, int]:
    value = _canonical_json(plane_root / "manifest.json")
    if not isinstance(value, list):
        raise CapsuleVerificationError("untracked inventory is invalid")
    redacted_paths, entries = _manifest_facts(
        value, allowed_inclusions=frozenset({"copied", "redacted"})
    )
    _require_manifest_disposition(metadata, redacted_paths)
    copied_paths = {
        path for path, entry in entries.items() if entry["inclusion"] == "copied"
    }
    payload_root = plane_root / "payload"
    try:
        payload_root.lstat()
    except FileNotFoundError:
        payload_files: tuple[Path, ...] = ()
    except OSError as exc:
        raise CapsuleVerificationError("payload universe is unavailable") from exc
    else:
        payload_files = tuple(
            _walk_regular_files(payload_root, excluded_root_names=frozenset())
        )
    actual_paths = {
        path.relative_to(payload_root).as_posix(): path for path in payload_files
    }
    if set(actual_paths) != copied_paths:
        raise CapsuleVerificationError(
            "copied payload universe does not match manifest"
        )
    evidence: list[dict[str, str]] = []
    for relative_name in sorted(copied_paths, key=lambda item: item.encode("utf-8")):
        entry = entries[relative_name]
        payload = actual_paths[relative_name]
        digest = _hash_regular_file(payload)
        try:
            size = payload.lstat().st_size
        except OSError as exc:
            raise CapsuleVerificationError("copied payload is unavailable") from exc
        if entry.get("size") != size or entry.get("sha256") != digest:
            raise CapsuleVerificationError("copied payload metadata does not match")
        evidence.append({"path": relative_name, "sha256": digest})
    manifest_digest = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    payload_digest = hashlib.sha256(canonical_json_bytes(evidence)).hexdigest()
    return manifest_digest, payload_digest, len(evidence)


def _validate_artifact_plane(capsule: Path, plane_id: PlaneId) -> PlaneRestoreResult:
    plane_root = capsule / plane_id.value
    metadata = _metadata_for_plane(plane_root)
    evidence_digest = _plane_evidence_digest(plane_root)
    payload_digest: str | None = None
    payload_count: int | None = None
    if plane_id is PlaneId.LOCAL_INDEX:
        try:
            index_bytes = _read_regular_bytes(plane_root / "index.raw")
            staged_diff = _read_regular_bytes(plane_root / "staged.diff")
        except CapsuleVerificationError as exc:
            raise CapsuleVerificationError(
                "index preservation artifacts are missing"
            ) from exc
        _secret_exclusions(metadata)
        index_digest = hashlib.sha256(index_bytes).hexdigest()
        if metadata.get("index_sha256") != index_digest:
            raise CapsuleVerificationError("preserved index identity does not match")
        subject_id = index_digest
        artifact_digests = (
            ("index.raw", index_digest),
            ("staged.diff", hashlib.sha256(staged_diff).hexdigest()),
        )
    elif plane_id is PlaneId.LOCAL_TRACKED:
        try:
            diff = _read_regular_bytes(plane_root / "unstaged.diff")
        except CapsuleVerificationError as exc:
            raise CapsuleVerificationError("tracked worktree diff is missing") from exc
        manifest = _canonical_json(plane_root / "manifest.json")
        if not isinstance(manifest, list):
            raise CapsuleVerificationError("tracked inventory is invalid")
        redacted_paths, _ = _manifest_facts(
            manifest,
            allowed_inclusions=frozenset({"metadata-only", "redacted", "excluded"}),
        )
        _require_manifest_disposition(metadata, redacted_paths)
        subject_id = hashlib.sha256(diff).hexdigest()
        artifact_digests = (
            (
                "manifest.json",
                hashlib.sha256(canonical_json_bytes(manifest)).hexdigest(),
            ),
            ("unstaged.diff", subject_id),
        )
    else:
        subject_id, payload_digest, payload_count = _validate_untracked_payload(
            plane_root, metadata
        )
        artifact_digests = (("manifest.json", subject_id),)
    disposition = _disposition_record(plane_id, subject_id, evidence_digest, metadata)
    artifact_match = bool(artifact_digests) and all(
        len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
        for _, digest in artifact_digests
    )
    if payload_count is not None:
        artifact_match = (
            artifact_match
            and payload_digest is not None
            and len(payload_digest) == 64
            and payload_count >= 0
        )
    if not artifact_match:
        raise CapsuleVerificationError("artifact verification evidence is incomplete")
    blockers: set[str] = set()
    if disposition.status is ResultStatus.BLOCKED:
        blockers.add(
            "opaque-preservation-ineligible"
            if plane_id is PlaneId.LOCAL_INDEX
            else "redacted-evidence-ineligible"
        )
    return PlaneRestoreResult(
        plane_id=plane_id,
        subject_id=subject_id,
        status=disposition.status,
        commit_match=None,
        tree_match=None,
        parent_match=None,
        mode_path_match=None,
        object_reachability=None,
        tree_id=None,
        parents_digest=None,
        mode_path_digest=None,
        evidence_digest=evidence_digest,
        artifact_digests=artifact_digests,
        artifact_match=artifact_match,
        payload_digest=payload_digest,
        payload_count=payload_count,
        blockers=tuple(sorted(blockers)),
    )


def _assert_outside_roots(
    destination: Path, capsule: Path, forbidden_roots: tuple[Path, ...]
) -> None:
    destination_resolved = destination.resolve(strict=False)
    capsule_resolved = capsule.resolve(strict=True)
    if destination_resolved == capsule_resolved or destination_resolved.is_relative_to(
        capsule_resolved
    ):
        raise ValueError("restore destination must be outside the capsule")
    for forbidden_root in forbidden_roots:
        if (
            destination_resolved == forbidden_root
            or destination_resolved.is_relative_to(forbidden_root)
        ):
            raise ValueError("restore destination must be outside every forbidden root")


def _assert_plain_restore_directory(destination: Path) -> None:
    try:
        metadata = destination.lstat()
    except OSError as exc:
        raise ValueError("restore destination is unavailable") from exc
    attributes = getattr(metadata, "st_file_attributes", 0)
    if stat.S_ISLNK(metadata.st_mode) or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise ValueError("restore destination must not be an alias")
    if not stat.S_ISDIR(metadata.st_mode):
        raise ValueError("restore destination must be a directory")


def _validate_restore_destination(
    capsule: Path,
    temp_root: Path,
    forbidden_roots: Iterable[Path],
) -> tuple[Path, tuple[Path, ...]]:
    destination = Path(temp_root).resolve(strict=False)
    try:
        resolved_forbidden = tuple(
            Path(root).resolve(strict=True) for root in forbidden_roots
        )
    except OSError as exc:
        raise ValueError("forbidden root is unavailable") from exc
    if not resolved_forbidden:
        raise ValueError("at least one forbidden root is required")
    if any(not root.is_dir() for root in resolved_forbidden):
        raise ValueError("forbidden root must be a directory")
    _assert_outside_roots(destination, capsule, resolved_forbidden)
    if destination.exists() or destination.is_symlink():
        raise ValueError("restore destination must not already exist")
    return destination, resolved_forbidden


def restore_and_verify(
    root: Path,
    temp_root: Path,
    *,
    forbidden_roots: Iterable[Path],
) -> VerificationRecord:
    """Restore sealed history independently and return scoped evidence."""

    capsule_path = Path(root)
    verify_checksums(capsule_path)
    capsule = capsule_path.resolve(strict=True)
    destination, resolved_forbidden = _validate_restore_destination(
        capsule, temp_root, forbidden_roots
    )
    local_root = provenance_root(capsule)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination, resolved_forbidden = _validate_restore_destination(
        capsule, destination, resolved_forbidden
    )
    destination.mkdir(exist_ok=False)
    _assert_outside_roots(destination, capsule, resolved_forbidden)
    _assert_plain_restore_directory(destination)

    results: list[PlaneRestoreResult] = []
    for plane_id in _HISTORY_PLANES:
        _assert_outside_roots(destination, capsule, resolved_forbidden)
        _assert_plain_restore_directory(destination)
        results.append(_restore_history_plane(capsule, destination, plane_id))
    for plane_id in (
        PlaneId.LOCAL_INDEX,
        PlaneId.LOCAL_TRACKED,
        PlaneId.LOCAL_UNTRACKED,
    ):
        results.append(_validate_artifact_plane(capsule, plane_id))

    blockers = tuple(
        sorted({blocker for result in results for blocker in result.blockers})
    )
    status = (
        ResultStatus.BLOCKED
        if blockers or any(result.status is ResultStatus.BLOCKED for result in results)
        else ResultStatus.PASS
    )
    record = VerificationRecord(
        schema_version="1",
        authentication="local-unanchored",
        provenance_root=local_root,
        status=status,
        checksum_status=ResultStatus.PASS,
        planes=tuple(results),
        commit_match=all(
            result.commit_match is True for result in results[: len(_HISTORY_PLANES)]
        ),
        tree_match=all(
            result.tree_match is True for result in results[: len(_HISTORY_PLANES)]
        ),
        artifact_match=all(
            result.artifact_match is True for result in results[len(_HISTORY_PLANES) :]
        ),
        blockers=blockers,
    )
    verify_checksums(capsule)
    _atomic_write_fixed(capsule, "verification.json", canonical_json_bytes(record))
    return record
