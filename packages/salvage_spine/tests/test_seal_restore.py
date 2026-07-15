from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from packages.salvage_spine.git_capture import SecretPolicy, capture_planes
from packages.salvage_spine.models import PlaneId, ResultStatus, canonical_json_bytes
from packages.salvage_spine.restore import restore_and_verify
from packages.salvage_spine.seal import (
    CapsuleVerificationError,
    seal_capsule,
    verify_checksums,
)


def git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check,
        capture_output=True,
        shell=False,
    )


def _supports_object_format(tmp_path: Path, object_format: str) -> None:
    probe = tmp_path / f"probe-{object_format}.git"
    result = git(
        tmp_path,
        "init",
        "--bare",
        f"--object-format={object_format}",
        str(probe),
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        if object_format == "sha256":
            pytest.skip(f"installed Git lacks SHA-256 support: {message}")
        pytest.fail(f"Git lacks required {object_format} support: {message}")


def _write_and_commit(repo: Path, name: str, content: bytes, message: str) -> str:
    (repo / name).parent.mkdir(parents=True, exist_ok=True)
    (repo / name).write_bytes(content)
    git(repo, "add", "--", name)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")


def captured_capsule(
    tmp_path: Path,
    *,
    object_format: str = "sha1",
    historical_secret: bytes | None = None,
    historical_lfs_pointer: bool = False,
    lfs_pointer: bool = False,
    gitlink: bool = False,
) -> tuple[Path, Path, dict[PlaneId, str]]:
    _supports_object_format(tmp_path, object_format)
    repo = tmp_path / f"repo-{object_format}"
    git(tmp_path, "init", f"--object-format={object_format}", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    main_sha = _write_and_commit(repo, "main.txt", b"main\n", "main")
    if historical_secret is not None:
        _write_and_commit(repo, ".env", historical_secret, "historical secret")
        git(repo, "rm", ".env")
        git(repo, "commit", "-m", "remove historical secret")
    if historical_lfs_pointer:
        pointer = (
            b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + b"b" * 64 + b"\nsize 456\n"
        )
        _write_and_commit(
            repo, "historical-large.bin", pointer, "historical lfs pointer"
        )
        git(repo, "rm", "historical-large.bin")
        git(repo, "commit", "-m", "remove historical lfs pointer")
    pr_sha = _write_and_commit(repo, "pr.txt", b"pr\n", "pr")
    if lfs_pointer:
        pointer = (
            b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + b"a" * 64 + b"\nsize 123\n"
        )
        _write_and_commit(repo, "large.bin", pointer, "lfs pointer")
    if gitlink:
        git(
            repo,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{main_sha},nested-module",
        )
        git(repo, "commit", "-m", "gitlink")
    local_sha = _write_and_commit(repo, "local.txt", b"local\n", "local")
    (repo / "staged.bin").write_bytes(b"staged\x00bytes\n")
    git(repo, "add", "staged.bin")
    (repo / "local.txt").write_bytes(b"local changed\x00\n")
    (repo / "ordinary.tmp").write_bytes(b"ordinary untracked\n")
    capsule = tmp_path / f"capsule-{object_format}"
    capture_planes(
        repo,
        main_sha,
        pr_sha,
        capsule,
        SecretPolicy.default(),
    )
    return (
        capsule,
        repo,
        {
            PlaneId.REMOTE_MAIN: main_sha,
            PlaneId.REMOTE_PR: pr_sha,
            PlaneId.LOCAL_HISTORY: local_sha,
        },
    )


def artifact_tree(root: Path, *, exclude_seal: bool = False) -> dict[str, bytes]:
    excluded = {"checksums.sha256", "provenance-root.json", "verification.json"}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
        and (not exclude_seal or path.relative_to(root).as_posix() not in excluded)
    }


def test_seal_is_deterministic_idempotent_and_local_unanchored(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)

    first = seal_capsule(capsule)
    first_tree = artifact_tree(capsule)
    second = seal_capsule(capsule)

    assert second == first
    assert artifact_tree(capsule) == first_tree
    provenance = json.loads(
        (capsule / "provenance-root.json").read_text(encoding="utf-8")
    )
    assert provenance == {
        "algorithm": "sha256",
        "authentication": "local-unanchored",
        "checksum_listing": "checksums.sha256",
        "provenance_root": first,
        "schema_version": "1",
    }
    verify_checksums(capsule)


@pytest.mark.parametrize("mutation", ["bytes", "extra", "missing"])
def test_checksum_file_universe_tampering_fails(tmp_path: Path, mutation: str) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    target = capsule / "remote-main" / "refs.txt"
    if mutation == "bytes":
        target.write_bytes(b"tampered\n")
    elif mutation == "extra":
        (capsule / "unexpected.txt").write_bytes(b"extra\n")
    else:
        target.rename(tmp_path / "moved-refs.txt")

    with pytest.raises(CapsuleVerificationError):
        verify_checksums(capsule)


@pytest.mark.parametrize("mutation", ["malformed", "duplicate", "listing-tamper"])
def test_checksum_listing_tampering_fails(tmp_path: Path, mutation: str) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    listing = capsule / "checksums.sha256"
    original = listing.read_bytes()
    if mutation == "malformed":
        listing.write_bytes(b"not-json\n")
    elif mutation == "duplicate":
        first_line = original.splitlines(keepends=True)[0]
        listing.write_bytes(original + first_line)
    else:
        listing.write_bytes(original.replace(b"sha256", b"sha257", 1))

    with pytest.raises(CapsuleVerificationError):
        verify_checksums(capsule)


def test_seal_rejects_symlinks_without_following_targets(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    outside = tmp_path / "outside-secret.txt"
    outside.write_bytes(b"must not be read\n")
    link = capsule / "escape-link"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(CapsuleVerificationError, match="symlink"):
        seal_capsule(capsule)
    assert outside.read_bytes() == b"must not be read\n"
    assert not (capsule / "checksums.sha256").exists()


def test_seal_rejects_internal_symlink_without_following_target(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    target = capsule / "remote-main" / "refs.txt"
    original = target.read_bytes()
    link = capsule / "internal-link"
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    with pytest.raises(CapsuleVerificationError, match="symlink"):
        seal_capsule(capsule)

    assert target.read_bytes() == original
    assert not (capsule / "checksums.sha256").exists()


@pytest.mark.parametrize("object_format", ["sha1", "sha256"])
def test_clean_room_restore_is_exact_for_each_history_plane(
    tmp_path: Path, object_format: str
) -> None:
    capsule, _, expected = captured_capsule(tmp_path, object_format=object_format)
    before = artifact_tree(capsule, exclude_seal=True)
    provenance_root = seal_capsule(capsule)

    result = restore_and_verify(capsule, tmp_path / f"restore-{object_format}")

    assert result.status is ResultStatus.BLOCKED
    assert result.checksum_status is ResultStatus.PASS
    assert result.commit_match is True
    assert result.tree_match is True
    assert result.artifact_match is True
    assert result.provenance_root == provenance_root
    history = {item.plane_id: item for item in result.planes[:3]}
    assert set(history) == set(expected)
    for plane_id, subject_id in expected.items():
        plane = history[plane_id]
        assert plane.subject_id == subject_id
        assert plane.status is ResultStatus.BLOCKED
        assert plane.commit_match is True
        assert plane.tree_match is True
        assert plane.parent_match is True
        assert plane.mode_path_match is True
        assert plane.object_reachability is True
        restored_repo = (
            tmp_path / f"restore-{object_format}" / plane_id.value / "repository.git"
        )
        assert (
            git(restored_repo, "rev-parse", "refs/heads/master")
            .stdout.strip()
            .decode("ascii")
            == subject_id
        )
        assert (
            git(restored_repo, "rev-parse", "--show-object-format=storage")
            .stdout.strip()
            .decode("ascii")
            == object_format
        )
    ordered_history = list(expected.items())
    for index, (plane_id, _) in enumerate(ordered_history):
        restored_repo = (
            tmp_path / f"restore-{object_format}" / plane_id.value / "repository.git"
        )
        for _, descendant in ordered_history[index + 1 :]:
            assert git(
                restored_repo, "cat-file", "-e", descendant, check=False
            ).returncode
    artifacts = {item.plane_id: item for item in result.planes[3:]}
    assert dict(artifacts[PlaneId.LOCAL_INDEX].artifact_digests) == {
        "index.raw": hashlib.sha256(
            (capsule / "local-index" / "index.raw").read_bytes()
        ).hexdigest(),
        "staged.diff": hashlib.sha256(
            (capsule / "local-index" / "staged.diff").read_bytes()
        ).hexdigest(),
    }
    assert dict(artifacts[PlaneId.LOCAL_TRACKED].artifact_digests) == {
        "manifest.json": hashlib.sha256(
            (capsule / "local-tracked" / "manifest.json").read_bytes()
        ).hexdigest(),
        "unstaged.diff": hashlib.sha256(
            (capsule / "local-tracked" / "unstaged.diff").read_bytes()
        ).hexdigest(),
    }
    assert dict(artifacts[PlaneId.LOCAL_UNTRACKED].artifact_digests) == {
        "manifest.json": hashlib.sha256(
            (capsule / "local-untracked-ignored" / "manifest.json").read_bytes()
        ).hexdigest(),
    }
    assert artifact_tree(capsule, exclude_seal=True) == before


def test_restore_rejects_identity_bundle_mismatch_and_keeps_partial_evidence(
    tmp_path: Path,
) -> None:
    capsule, _, expected = captured_capsule(tmp_path)
    identity_path = capsule / "remote-main" / "identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    identity["subject_id"] = expected[PlaneId.REMOTE_PR]
    identity_path.write_bytes(canonical_json_bytes(identity))
    (capsule / "remote-main" / "refs.txt").write_bytes(
        f"{expected[PlaneId.REMOTE_PR]} refs/heads/master\n".encode("ascii")
    )
    seal_capsule(capsule)
    restore_root = tmp_path / "restore-mismatch"

    with pytest.raises(CapsuleVerificationError, match="subject"):
        restore_and_verify(capsule, restore_root)

    assert (restore_root / "remote-main" / "repository.git").is_dir()


def test_restore_rejects_destination_inside_capsule_before_writes(
    tmp_path: Path,
) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    destination = capsule / "restore"

    with pytest.raises(ValueError, match="outside the capsule"):
        restore_and_verify(capsule, destination)

    assert not destination.exists()


def test_restore_rejects_capsule_root_symlink_before_writes(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    alias = tmp_path / "capsule-alias"
    try:
        alias.symlink_to(capsule, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    destination = tmp_path / "restore-alias"

    with pytest.raises(CapsuleVerificationError, match="symlink"):
        restore_and_verify(alias, destination)

    assert not destination.exists()


def test_restore_cross_checks_refs_and_identity_scope(tmp_path: Path) -> None:
    capsule, _, expected = captured_capsule(tmp_path)
    refs = capsule / "remote-main" / "refs.txt"
    refs.write_bytes(
        f"{expected[PlaneId.REMOTE_PR]} refs/heads/master\n".encode("ascii")
    )
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="refs metadata"):
        restore_and_verify(capsule, tmp_path / "restore-refs-mismatch")

    refs.write_bytes(
        f"{expected[PlaneId.REMOTE_MAIN]} refs/heads/master\n".encode("ascii")
    )
    identity_path = capsule / "remote-main" / "identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    identity["bundle_scope"] = "unapproved-broad-scope"
    identity_path.write_bytes(canonical_json_bytes(identity))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="identity"):
        restore_and_verify(capsule, tmp_path / "restore-scope-mismatch")


def test_opaque_secret_evidence_remains_blocked_and_metadata_is_sanitized(
    tmp_path: Path,
) -> None:
    secret = b"TOKEN=historical-do-not-project\x00\n"
    capsule, repo, _ = captured_capsule(tmp_path, historical_secret=secret)
    staged_secret = b"TOKEN=staged-do-not-project\x00\n"
    (repo / ".env").write_bytes(staged_secret)
    git(repo, "add", ".env")
    # Recapture in a fresh destination so the exact index contains the secret object ID.
    capsule = tmp_path / "capsule-secret-index"
    head = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    capture_planes(repo, head, head, capsule, SecretPolicy.default())
    seal_capsule(capsule)

    result = restore_and_verify(capsule, tmp_path / "restore-secret")
    verification = (capsule / "verification.json").read_bytes()

    assert result.status is ResultStatus.BLOCKED
    assert result.artifact_match is True
    assert all(
        plane.status is ResultStatus.BLOCKED
        for plane in result.planes
        if plane.plane_id
        in {
            PlaneId.REMOTE_MAIN,
            PlaneId.REMOTE_PR,
            PlaneId.LOCAL_HISTORY,
            PlaneId.LOCAL_INDEX,
        }
    )
    assert secret not in verification
    assert staged_secret not in verification
    assert str(repo).encode("utf-8") not in verification
    assert b".env" not in verification


def test_lfs_pointer_without_media_returns_blocked(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path, lfs_pointer=True)
    seal_capsule(capsule)

    result = restore_and_verify(capsule, tmp_path / "restore-lfs")

    assert result.status is ResultStatus.BLOCKED
    assert "lfs-media-missing" in result.blockers
    assert not any("large.bin" in blocker for blocker in result.blockers)


def test_historical_lfs_pointer_without_media_returns_blocked(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path, historical_lfs_pointer=True)
    seal_capsule(capsule)

    result = restore_and_verify(capsule, tmp_path / "restore-historical-lfs")

    assert result.status is ResultStatus.BLOCKED
    assert "lfs-media-missing" in result.blockers
    assert not any("historical-large.bin" in blocker for blocker in result.blockers)


def test_gitlink_without_submodule_repository_returns_blocked(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path, gitlink=True)
    seal_capsule(capsule)

    result = restore_and_verify(capsule, tmp_path / "restore-gitlink")

    assert result.status is ResultStatus.BLOCKED
    assert "submodule-repository-missing" in result.blockers
    assert not any("nested-module" in blocker for blocker in result.blockers)


def test_verification_json_is_deterministic_and_contains_no_absolute_paths(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    result = restore_and_verify(capsule, tmp_path / "restore-deterministic")
    first = (capsule / "verification.json").read_bytes()

    assert first == canonical_json_bytes(result)
    assert str(repo).encode("utf-8") not in first
    assert str(capsule).encode("utf-8") not in first

    second_result = restore_and_verify(capsule, tmp_path / "restore-deterministic-2")
    assert (capsule / "verification.json").read_bytes() == first
    assert second_result == result
