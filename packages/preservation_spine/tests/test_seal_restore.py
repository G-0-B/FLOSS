from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import subprocess

import pytest

from packages.preservation_spine.git_capture import SecretPolicy, capture_planes
from packages.preservation_spine.models import PlaneId, ResultStatus, canonical_json_bytes
from packages.preservation_spine.restore import (
    _list_bundle_heads,
    restore_and_verify,
)
from packages.preservation_spine.seal import (
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


def _make_junction(link: Path, target: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction primitive is unavailable")
    result = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        check=False,
        capture_output=True,
        shell=False,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        pytest.skip(f"junction creation unavailable: {message}")


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


def filesystem_snapshot(root: Path) -> tuple[tuple[str, ...], dict[str, bytes]]:
    directories = tuple(
        sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_dir()
        )
    )
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
    return directories, files


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


def test_bundle_head_with_non_ascii_ref_maps_to_capsule_error(
    tmp_path: Path,
) -> None:
    """A bundle containing a non-ASCII ref name must raise
    CapsuleVerificationError like every other failure in the helper —
    not a bare UnicodeDecodeError callers do not catch."""
    repo = tmp_path / "repo"
    git(tmp_path, "init", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    _write_and_commit(repo, "a.txt", b"one\n", "seed")
    git(repo, "branch", "tête")
    bundle = tmp_path / "heads.bundle"
    git(repo, "bundle", "create", str(bundle), "--all")

    with pytest.raises(CapsuleVerificationError):
        _list_bundle_heads(bundle)


@pytest.mark.skipif(os.name != "nt", reason="Windows path/handle mode regression")
def test_windows_open_failure_maps_to_capsule_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An OSError from the Windows handle→descriptor conversion must surface
    as CapsuleVerificationError like every other failure in the helper —
    callers catch only the capsule type, so a raw OSError would escape
    unclassified."""
    import msvcrt

    seal_module = importlib.import_module("packages.preservation_spine.seal")
    payload = tmp_path / "payload.bin"
    payload.write_bytes(b"evidence\n")

    def boom(*args: object, **kwargs: object) -> int:
        raise OSError("simulated open_osfhandle failure")

    monkeypatch.setattr(msvcrt, "open_osfhandle", boom)
    with pytest.raises(CapsuleVerificationError):
        with seal_module._open_regular_nofollow(payload):
            pass


@pytest.mark.skipif(os.name != "nt", reason="Windows path/handle mode regression")
def test_windows_executable_hash_read_and_seal_use_stable_identity(
    tmp_path: Path,
) -> None:
    capsule = tmp_path / "capsule-executable"
    capsule.mkdir()
    payload = capsule / "build-script.exe"
    content = b"disposable executable evidence\n"
    payload.write_bytes(content)
    seal_module = importlib.import_module("packages.preservation_spine.seal")

    path_state = payload.lstat()
    with seal_module._open_regular_nofollow(payload) as stream:
        handle_state = os.fstat(stream.fileno())

    assert stat.S_IFMT(path_state.st_mode) == stat.S_IFREG
    assert stat.S_IFMT(handle_state.st_mode) == stat.S_IFREG
    assert stat.S_IMODE(path_state.st_mode) == 0o777
    assert stat.S_IMODE(handle_state.st_mode) == 0o666
    assert (
        path_state.st_dev,
        path_state.st_ino,
        path_state.st_nlink,
        path_state.st_size,
        path_state.st_mtime_ns,
        path_state.st_file_attributes,
        path_state.st_reparse_tag,
    ) == (
        handle_state.st_dev,
        handle_state.st_ino,
        handle_state.st_nlink,
        handle_state.st_size,
        handle_state.st_mtime_ns,
        handle_state.st_file_attributes,
        handle_state.st_reparse_tag,
    )

    assert (
        seal_module._hash_regular_file(payload) == hashlib.sha256(content).hexdigest()
    )
    assert seal_module._read_regular_bytes(payload) == content
    seal_capsule(capsule)
    verify_checksums(capsule)


@pytest.mark.skipif(os.name == "nt", reason="POSIX full-mode identity contract")
def test_posix_identity_retains_permission_bits(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.write_bytes(b"mode identity\n")
    before = payload.lstat()
    payload.chmod(stat.S_IMODE(before.st_mode) ^ stat.S_IXUSR)
    after = payload.lstat()
    seal_module = importlib.import_module("packages.preservation_spine.seal")

    assert stat.S_IFMT(before.st_mode) == stat.S_IFMT(after.st_mode)
    assert before.st_mode != after.st_mode
    assert seal_module._node_identity(before) != seal_module._node_identity(after)
    assert seal_module._file_identity(before) != seal_module._file_identity(after)


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


def test_seal_rejects_capsule_root_junction(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    alias = tmp_path / "capsule-root-junction"
    _make_junction(alias, capsule)

    with pytest.raises(CapsuleVerificationError, match="reparse"):
        seal_capsule(alias)

    assert not (capsule / "checksums.sha256").exists()


def test_seal_rejects_internal_junction_without_traversing_target(
    tmp_path: Path,
) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    outside = tmp_path / "junction-target"
    outside.mkdir()
    secret = outside / "secret.txt"
    secret.write_bytes(b"junction-secret-must-not-be-read\n")
    _make_junction(capsule / "internal-junction", outside)

    with pytest.raises(CapsuleVerificationError, match="reparse"):
        seal_capsule(capsule)

    assert secret.read_bytes() == b"junction-secret-must-not-be-read\n"
    assert not (capsule / "checksums.sha256").exists()


def test_seal_rejects_preexisting_checksum_hardlink_without_overwrite(
    tmp_path: Path,
) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    sentinel = tmp_path / "checksum-sentinel.txt"
    sentinel.write_bytes(b"outside-checksum-sentinel\n")
    try:
        os.link(sentinel, capsule / "checksums.sha256")
    except OSError as exc:
        pytest.skip(f"hardlink creation unavailable: {exc}")

    with pytest.raises(CapsuleVerificationError, match="hardlink"):
        seal_capsule(capsule)

    assert sentinel.read_bytes() == b"outside-checksum-sentinel\n"


def test_restore_rejects_preexisting_verification_hardlink_without_overwrite(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    sentinel = tmp_path / "verification-sentinel.txt"
    sentinel.write_bytes(b"outside-verification-sentinel\n")
    try:
        os.link(sentinel, capsule / "verification.json")
    except OSError as exc:
        pytest.skip(f"hardlink creation unavailable: {exc}")

    with pytest.raises(CapsuleVerificationError, match="hardlink"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-verification-hardlink",
            forbidden_roots={repo},
        )

    assert sentinel.read_bytes() == b"outside-verification-sentinel\n"
    assert not (tmp_path / "restore-verification-hardlink").exists()


def test_seal_fails_closed_when_payload_path_is_substituted_before_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    target = capsule / "remote-main" / "refs.txt"
    preserved = tmp_path / "preserved-refs.txt"
    outside = tmp_path / "substitution-target.txt"
    outside.write_bytes(b"outside-substitution-bytes\n")
    seal_module = importlib.import_module("packages.preservation_spine.seal")
    original_hash = seal_module._hash_regular_file
    substituted = False

    def substitute_before_hash(path: Path) -> str:
        nonlocal substituted
        if path == target and not substituted:
            target.rename(preserved)
            try:
                os.link(outside, target)
            except OSError as exc:
                pytest.skip(f"hardlink substitution unavailable: {exc}")
            substituted = True
        return original_hash(path)

    monkeypatch.setattr(seal_module, "_hash_regular_file", substitute_before_hash)

    with pytest.raises(CapsuleVerificationError, match="hardlink|changed"):
        seal_capsule(capsule)

    assert substituted is True
    assert outside.read_bytes() == b"outside-substitution-bytes\n"
    assert not (capsule / "checksums.sha256").exists()


def test_seal_parent_swap_cannot_redirect_pending_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction swap regression")
    capsule, _, _ = captured_capsule(tmp_path)
    external = tmp_path / "seal-swap-external"
    external.mkdir()
    preserved = tmp_path / "seal-swap-preserved"
    seal_module = importlib.import_module("packages.preservation_spine.seal")
    original_open = seal_module.os.open
    attempted = False

    def swap_before_pending_open(path: object, *args: object, **kwargs: object) -> int:
        nonlocal attempted
        rendered = Path(path)  # type: ignore[arg-type]
        if rendered.name.startswith(".checksums.sha256.pending-") and not attempted:
            attempted = True
            capsule.rename(preserved)
            _make_junction(capsule, external)
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(seal_module.os, "open", swap_before_pending_open)

    with pytest.raises((CapsuleVerificationError, OSError)):
        seal_capsule(capsule)

    assert attempted is True
    assert filesystem_snapshot(external) == ((), {})


@pytest.mark.parametrize("object_format", ["sha1", "sha256"])
def test_clean_room_restore_is_exact_for_each_history_plane(
    tmp_path: Path, object_format: str
) -> None:
    capsule, repo, expected = captured_capsule(tmp_path, object_format=object_format)
    before = artifact_tree(capsule, exclude_seal=True)
    provenance_root = seal_capsule(capsule)

    result = restore_and_verify(
        capsule,
        tmp_path / f"restore-{object_format}",
        forbidden_roots={repo},
    )

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
    copied_payload_evidence = canonical_json_bytes(
        [
            {
                "path": "ordinary.tmp",
                "sha256": hashlib.sha256(b"ordinary untracked\n").hexdigest(),
            }
        ]
    )
    untracked = artifacts[PlaneId.LOCAL_UNTRACKED]
    assert untracked.payload_count == 1
    assert (
        untracked.payload_digest == hashlib.sha256(copied_payload_evidence).hexdigest()
    )
    assert all(plane.artifact_match is True for plane in result.planes[3:])
    assert artifact_tree(capsule, exclude_seal=True) == before


def test_restore_rejects_identity_bundle_mismatch_and_keeps_partial_evidence(
    tmp_path: Path,
) -> None:
    capsule, repo, expected = captured_capsule(tmp_path)
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
        restore_and_verify(capsule, restore_root, forbidden_roots={repo})

    assert (restore_root / "remote-main" / "repository.git").is_dir()


def test_restore_rejects_destination_inside_capsule_before_writes(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    destination = capsule / "restore"

    with pytest.raises(ValueError, match="outside the capsule"):
        restore_and_verify(capsule, destination, forbidden_roots={repo})

    assert not destination.exists()


def test_restore_rejects_destination_inside_forbidden_source_before_writes(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    destination = repo / "restore-inside-source"

    with pytest.raises(ValueError, match="forbidden root"):
        restore_and_verify(capsule, destination, forbidden_roots={repo})

    assert not destination.exists()


def test_restore_rejects_empty_forbidden_roots_before_writes(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    destination = tmp_path / "restore-without-source-boundary"

    with pytest.raises(ValueError, match="at least one forbidden root"):
        restore_and_verify(capsule, destination, forbidden_roots=())

    assert not destination.exists()


def test_restore_rejects_destination_through_source_junction_before_writes(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    source_alias = tmp_path / "source-junction"
    _make_junction(source_alias, repo)
    destination = source_alias / "restore-through-junction"

    with pytest.raises(ValueError, match="forbidden root"):
        restore_and_verify(capsule, destination, forbidden_roots={repo})

    assert not destination.exists()


def test_restore_rejects_capsule_root_symlink_before_writes(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    alias = tmp_path / "capsule-alias"
    try:
        alias.symlink_to(capsule, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    destination = tmp_path / "restore-alias"

    with pytest.raises(CapsuleVerificationError, match="symlink"):
        restore_and_verify(alias, destination, forbidden_roots={repo})

    assert not destination.exists()


def test_restore_root_swap_before_first_plane_mkdir_creates_no_external_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction swap regression")
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    restore_root = tmp_path / "restore-root-swap"
    preserved = tmp_path / "restore-root-swap-preserved"
    external = tmp_path / "restore-root-swap-external"
    external.mkdir()
    original_mkdir = Path.mkdir
    attempted = False

    def swap_before_mkdir(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal attempted
        if path == restore_root / "remote-main" and not attempted:
            attempted = True
            restore_root.rename(preserved)
            _make_junction(restore_root, external)
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", swap_before_mkdir)

    with pytest.raises((CapsuleVerificationError, OSError, ValueError)):
        restore_and_verify(capsule, restore_root, forbidden_roots={repo})

    assert attempted is True
    assert filesystem_snapshot(external) == ((), {})


def test_restore_parent_swap_before_root_mkdir_creates_no_external_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction swap regression")
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    parent = tmp_path / "restore-parent-swap"
    parent.mkdir()
    restore_root = parent / "restore"
    preserved = tmp_path / "restore-parent-swap-preserved"
    external = tmp_path / "restore-parent-swap-external"
    external.mkdir()
    original_mkdir = Path.mkdir
    attempted = False

    def swap_before_mkdir(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal attempted
        if path == restore_root and not attempted:
            attempted = True
            parent.rename(preserved)
            _make_junction(parent, external)
        original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", swap_before_mkdir)

    with pytest.raises((CapsuleVerificationError, OSError, ValueError)):
        restore_and_verify(capsule, restore_root, forbidden_roots={repo})

    assert attempted is True
    assert filesystem_snapshot(external) == ((), {})


def test_restore_plane_swap_after_mkdir_creates_no_external_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction swap regression")
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    restore_root = tmp_path / "restore-plane-swap"
    plane_root = restore_root / "remote-main"
    preserved = tmp_path / "restore-plane-swap-preserved"
    external = tmp_path / "restore-plane-swap-external"
    external.mkdir()
    original_mkdir = Path.mkdir
    attempted = False

    def swap_after_mkdir(path: Path, *args: object, **kwargs: object) -> None:
        nonlocal attempted
        original_mkdir(path, *args, **kwargs)
        if path == plane_root and not attempted:
            attempted = True
            plane_root.rename(preserved)
            _make_junction(plane_root, external)

    monkeypatch.setattr(Path, "mkdir", swap_after_mkdir)

    with pytest.raises((CapsuleVerificationError, OSError, ValueError)):
        restore_and_verify(capsule, restore_root, forbidden_roots={repo})

    assert attempted is True
    assert filesystem_snapshot(external) == ((), {})


def test_restore_repository_swap_before_git_init_creates_no_external_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction swap regression")
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    restore_root = tmp_path / "restore-repository-init-swap"
    repository = restore_root / "remote-main" / "repository.git"
    preserved = tmp_path / "restore-repository-init-swap-preserved"
    external = tmp_path / "restore-repository-init-swap-external"
    external.mkdir()
    restore_module = importlib.import_module("packages.preservation_spine.restore")
    original_run = restore_module.subprocess.run
    attempted = False

    def swap_before_git_init(*args: object, **kwargs: object) -> object:
        nonlocal attempted
        command = args[0]
        if (
            isinstance(command, list)
            and command[:2] == ["git", "init"]
            and not attempted
        ):
            attempted = True
            repository.mkdir(exist_ok=True)
            repository.rename(preserved)
            _make_junction(repository, external)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(restore_module.subprocess, "run", swap_before_git_init)

    with pytest.raises((CapsuleVerificationError, OSError, ValueError)):
        restore_and_verify(capsule, restore_root, forbidden_roots={repo})

    assert attempted is True
    assert filesystem_snapshot(external) == ((), {})


def test_restore_repository_swap_before_fetch_cannot_write_external_git_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.name != "nt":
        pytest.skip("Windows junction swap regression")
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    restore_root = tmp_path / "restore-repository-fetch-swap"
    repository = restore_root / "remote-main" / "repository.git"
    preserved = tmp_path / "restore-repository-fetch-swap-preserved"
    external = tmp_path / "restore-repository-fetch-swap-external.git"
    git(tmp_path, "init", "--bare", str(external))
    before = filesystem_snapshot(external)
    restore_module = importlib.import_module("packages.preservation_spine.restore")
    original_run = restore_module.subprocess.run
    attempted = False

    def swap_before_fetch(*args: object, **kwargs: object) -> object:
        nonlocal attempted
        command = args[0]
        if isinstance(command, list) and "fetch" in command and not attempted:
            attempted = True
            repository.rename(preserved)
            _make_junction(repository, external)
        return original_run(*args, **kwargs)

    monkeypatch.setattr(restore_module.subprocess, "run", swap_before_fetch)

    with pytest.raises((CapsuleVerificationError, OSError, ValueError)):
        restore_and_verify(capsule, restore_root, forbidden_roots={repo, external})

    assert attempted is True
    assert filesystem_snapshot(external) == before


def test_restore_cross_checks_refs_and_identity_scope(tmp_path: Path) -> None:
    capsule, repo, expected = captured_capsule(tmp_path)
    refs = capsule / "remote-main" / "refs.txt"
    refs.write_bytes(
        f"{expected[PlaneId.REMOTE_PR]} refs/heads/master\n".encode("ascii")
    )
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="refs metadata"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-refs-mismatch",
            forbidden_roots={repo},
        )

    refs.write_bytes(
        f"{expected[PlaneId.REMOTE_MAIN]} refs/heads/master\n".encode("ascii")
    )
    identity_path = capsule / "remote-main" / "identity.json"
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    identity["bundle_scope"] = "unapproved-broad-scope"
    identity_path.write_bytes(canonical_json_bytes(identity))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="identity"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-scope-mismatch",
            forbidden_roots={repo},
        )


@pytest.mark.parametrize(
    "variable",
    [
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
    ],
)
def test_restore_sanitizes_git_path_redirection_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    external = tmp_path / f"external-{variable.lower()}"
    external.mkdir()
    (external / "sentinel.txt").write_bytes(b"must-remain-only-entry\n")
    redirected = external / ("index" if variable == "GIT_INDEX_FILE" else "target")
    if variable != "GIT_INDEX_FILE":
        redirected.mkdir()
    before = filesystem_snapshot(external)
    monkeypatch.setenv(variable, str(redirected))

    result = restore_and_verify(
        capsule,
        tmp_path / f"restore-{variable.lower()}",
        forbidden_roots={repo, external},
    )

    assert result.status is ResultStatus.BLOCKED
    assert filesystem_snapshot(external) == before


def test_restore_sanitizes_git_config_injection_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    external = tmp_path / "external-config-injection"
    external.mkdir()
    (external / "sentinel.txt").write_bytes(b"config-injection-sentinel\n")
    before = filesystem_snapshot(external)
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.repositoryformatversion")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "999")

    result = restore_and_verify(
        capsule,
        tmp_path / "restore-config-injection",
        forbidden_roots={repo, external},
    )

    assert result.status is ResultStatus.BLOCKED
    assert filesystem_snapshot(external) == before


def test_bundle_head_inspection_isolated_from_callers_linked_worktree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    bundle = capsule / "remote-main" / "repository.bundle"
    caller = tmp_path / "caller-linked-worktree"
    git(repo, "worktree", "add", "--detach", str(caller), "HEAD")
    common_git = Path(
        git(caller, "rev-parse", "--path-format=absolute", "--git-common-dir")
        .stdout.strip()
        .decode("utf-8")
    )
    before = filesystem_snapshot(common_git)
    before_mtime = common_git.stat().st_mtime_ns
    restore_module = importlib.import_module("packages.preservation_spine.restore")
    original_run = restore_module.subprocess.run
    invocation: dict[str, object] = {}

    def observe_bundle_inspection(command: list[str], *args: object, **kwargs: object):
        if command[:3] == ["git", "bundle", "list-heads"]:
            invocation["cwd"] = kwargs.get("cwd")
            invocation["optional_locks"] = kwargs["env"].get("GIT_OPTIONAL_LOCKS")
        return original_run(command, *args, **kwargs)

    monkeypatch.chdir(caller)
    monkeypatch.setenv("GIT_OPTIONAL_LOCKS", "1")
    monkeypatch.setattr(restore_module.subprocess, "run", observe_bundle_inspection)

    heads = restore_module._list_bundle_heads(bundle)

    assert heads
    assert Path(invocation["cwd"]).resolve() == bundle.parent.resolve()
    assert invocation["optional_locks"] == "0"
    assert filesystem_snapshot(common_git) == before
    assert common_git.stat().st_mtime_ns == before_mtime


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

    result = restore_and_verify(
        capsule, tmp_path / "restore-secret", forbidden_roots={repo}
    )
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


def test_redacted_manifest_cannot_be_promoted_to_pass_by_resealed_metadata(
    tmp_path: Path,
) -> None:
    _, repo, _ = captured_capsule(tmp_path)
    (repo / ".env").write_bytes(b"TOKEN=redacted-untracked\n")
    capsule = tmp_path / "capsule-redacted-promotion"
    head = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    capture_planes(repo, head, head, capsule, SecretPolicy.default())
    metadata_path = capsule / "local-untracked-ignored" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(
        {
            "eligibility": "eligible",
            "sensitivity": "ordinary",
            "status": "PASS",
            "verification": "byte-equality",
        }
    )
    metadata_path.write_bytes(canonical_json_bytes(metadata))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="manifest disposition"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-redacted-promotion",
            forbidden_roots={repo},
        )


def test_untracked_payload_rejects_unowned_extra_file(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    extra = capsule / "local-untracked-ignored" / "payload" / "unowned.bin"
    extra.write_bytes(b"unowned payload bytes\n")
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="payload universe"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-unowned-payload",
            forbidden_roots={repo},
        )


def test_untracked_payload_rejects_duplicate_manifest_owner(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    manifest_path = capsule / "local-untracked-ignored" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.append(dict(manifest[0]))
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="duplicate paths"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-duplicate-payload",
            forbidden_roots={repo},
        )


def test_untracked_payload_rejects_copied_entry_with_nonfile_kind(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    manifest_path = capsule / "local-untracked-ignored" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[0]["kind"] = "redacted"
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="copied manifest metadata"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-invalid-copied-kind",
            forbidden_roots={repo},
        )


def test_untracked_payload_rejects_missing_copied_file(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    payload = capsule / "local-untracked-ignored" / "payload" / "ordinary.tmp"
    payload.rename(tmp_path / "preserved-ordinary.tmp")
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="payload universe"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-missing-payload",
            forbidden_roots={repo},
        )


def test_untracked_payload_rejects_hardlink_alias(tmp_path: Path) -> None:
    capsule, _, _ = captured_capsule(tmp_path)
    payload = capsule / "local-untracked-ignored" / "payload" / "ordinary.tmp"
    preserved = tmp_path / "preserved-payload.tmp"
    payload.rename(preserved)
    try:
        os.link(preserved, payload)
    except OSError as exc:
        pytest.skip(f"hardlink creation unavailable: {exc}")

    with pytest.raises(CapsuleVerificationError, match="hardlink"):
        seal_capsule(capsule)

    assert preserved.read_bytes() == b"ordinary untracked\n"


def test_lfs_pointer_without_media_returns_blocked(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path, lfs_pointer=True)
    seal_capsule(capsule)

    result = restore_and_verify(
        capsule, tmp_path / "restore-lfs", forbidden_roots={repo}
    )

    assert result.status is ResultStatus.BLOCKED
    assert "lfs-media-missing" in result.blockers
    assert not any("large.bin" in blocker for blocker in result.blockers)


def test_historical_lfs_pointer_without_media_returns_blocked(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path, historical_lfs_pointer=True)
    seal_capsule(capsule)

    result = restore_and_verify(
        capsule,
        tmp_path / "restore-historical-lfs",
        forbidden_roots={repo},
    )

    assert result.status is ResultStatus.BLOCKED
    assert "lfs-media-missing" in result.blockers
    assert not any("historical-large.bin" in blocker for blocker in result.blockers)


def test_gitlink_without_submodule_repository_returns_blocked(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path, gitlink=True)
    seal_capsule(capsule)

    result = restore_and_verify(
        capsule, tmp_path / "restore-gitlink", forbidden_roots={repo}
    )

    assert result.status is ResultStatus.BLOCKED
    assert "submodule-repository-missing" in result.blockers
    assert not any("nested-module" in blocker for blocker in result.blockers)
    tracked = next(
        plane for plane in result.planes if plane.plane_id is PlaneId.LOCAL_TRACKED
    )
    assert tracked.status is ResultStatus.BLOCKED
    assert tracked.artifact_match is True
    assert tracked.blockers == ("excluded-evidence-ineligible",)


def test_excluded_manifest_status_and_reason_must_agree(tmp_path: Path) -> None:
    capsule, repo, _ = captured_capsule(tmp_path, gitlink=True)
    manifest_path = capsule / "local-tracked" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    excluded = next(entry for entry in manifest if entry["inclusion"] == "excluded")
    excluded["reason"] = "tracked-worktree-inventory"
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="excluded manifest metadata"):
        restore_and_verify(
            capsule,
            tmp_path / "restore-excluded-reason-mismatch",
            forbidden_roots={repo},
        )


@pytest.mark.parametrize("inclusion", ["eligible", "copied", "error", "failed"])
def test_tracked_manifest_rejects_every_unsupported_inclusion_state(
    tmp_path: Path, inclusion: str
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    manifest_path = capsule / "local-tracked" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[0]["inclusion"] = inclusion
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    seal_capsule(capsule)

    with pytest.raises(CapsuleVerificationError, match="inclusion is not verifiable"):
        restore_and_verify(
            capsule,
            tmp_path / f"restore-unsupported-{inclusion}",
            forbidden_roots={repo},
        )


def test_tracked_metadata_only_is_the_only_eligible_manifest_state(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)

    result = restore_and_verify(
        capsule,
        tmp_path / "restore-tracked-metadata-only",
        forbidden_roots={repo},
    )

    tracked = next(
        plane for plane in result.planes if plane.plane_id is PlaneId.LOCAL_TRACKED
    )
    assert tracked.status is ResultStatus.PASS
    assert tracked.blockers == ()


def test_tracked_redacted_manifest_state_is_explicitly_blocked(tmp_path: Path) -> None:
    _, repo, _ = captured_capsule(tmp_path)
    _write_and_commit(repo, ".env", b"TOKEN=committed\n", "tracked secret")
    (repo / ".env").write_bytes(b"TOKEN=changed\n")
    capsule = tmp_path / "capsule-tracked-redacted"
    head = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    capture_planes(repo, head, head, capsule, SecretPolicy.default())
    seal_capsule(capsule)

    result = restore_and_verify(
        capsule,
        tmp_path / "restore-tracked-redacted",
        forbidden_roots={repo},
    )

    tracked = next(
        plane for plane in result.planes if plane.plane_id is PlaneId.LOCAL_TRACKED
    )
    assert tracked.status is ResultStatus.BLOCKED
    assert tracked.blockers == ("redacted-evidence-ineligible",)


def test_untracked_excluded_manifest_state_is_explicitly_blocked(
    tmp_path: Path,
) -> None:
    _, repo, _ = captured_capsule(tmp_path)
    outside = tmp_path / "untracked-link-target.txt"
    outside.write_bytes(b"must-not-be-copied\n")
    link = repo / "untracked-link"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")
    capsule = tmp_path / "capsule-untracked-excluded"
    head = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    capture_planes(repo, head, head, capsule, SecretPolicy.default())
    seal_capsule(capsule)

    result = restore_and_verify(
        capsule,
        tmp_path / "restore-untracked-excluded",
        forbidden_roots={repo},
    )

    untracked = next(
        plane for plane in result.planes if plane.plane_id is PlaneId.LOCAL_UNTRACKED
    )
    assert untracked.status is ResultStatus.BLOCKED
    assert untracked.artifact_match is True
    assert untracked.payload_count == 1
    assert untracked.blockers == ("excluded-evidence-ineligible",)


def test_verification_json_is_deterministic_and_contains_no_absolute_paths(
    tmp_path: Path,
) -> None:
    capsule, repo, _ = captured_capsule(tmp_path)
    seal_capsule(capsule)
    result = restore_and_verify(
        capsule,
        tmp_path / "restore-deterministic",
        forbidden_roots={repo},
    )
    first = (capsule / "verification.json").read_bytes()

    assert first == canonical_json_bytes(result)
    assert str(repo).encode("utf-8") not in first
    assert str(capsule).encode("utf-8") not in first

    second_result = restore_and_verify(
        capsule,
        tmp_path / "restore-deterministic-2",
        forbidden_roots={repo},
    )
    assert (capsule / "verification.json").read_bytes() == first
    assert second_result == result
