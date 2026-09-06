from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

import packages.preservation_spine.git_capture as git_capture_module
from packages.preservation_spine.git_capture import (
    CaptureDrift,
    CaptureEvidenceError,
    CaptureUnverifiable,
    SecretPolicy,
    _decode_paths,
    _inventory_state,
    _read_regular_file,
    _require_preservable_paths,
    assert_unchanged,
    capture_planes,
    run_git,
    snapshot_subject,
)
from packages.preservation_spine.models import (
    PlaneEligibility,
    PlaneId,
    PlaneSensitivity,
    PlaneVerification,
    ResultStatus,
)


def git(
    repo: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
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


def initialized_repo_with_object_format(
    tmp_path: Path,
    object_format: str,
    *,
    name: str = "repo",
) -> Path:
    probe = tmp_path / f"object-format-probe-{object_format}"
    capability = git(
        tmp_path,
        "init",
        "--bare",
        f"--object-format={object_format}",
        str(probe),
        check=False,
    )
    if capability.returncode != 0:
        message = capability.stderr.decode("utf-8", errors="replace").strip()
        if object_format == "sha256":
            pytest.skip(f"installed Git lacks SHA-256 repository support: {message}")
        pytest.fail(f"Git lacks required {object_format} repository support: {message}")
    repo = tmp_path / name
    git(
        tmp_path,
        "init",
        f"--object-format={object_format}",
        str(repo),
    )
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "a.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    git(repo, "commit", "-m", "seed")
    return repo


def artifact_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_decode_paths_canonicalizes_only_terminal_directory_markers() -> None:
    raw_paths = b"tracked.txt\0untracked/nested.txt\0ignored-directory/\0"

    assert _decode_paths(raw_paths) == (
        "tracked.txt",
        "untracked/nested.txt",
        "ignored-directory",
    )


@pytest.mark.parametrize(
    "raw_paths",
    (
        b"/\0",
        b"./\0",
        b"../escape/\0",
        b"nested/../../escape/\0",
        b"/absolute\0",
        b"C:/absolute\0",
        b"nested//file.txt\0",
        b"nested\\file.txt\0",
    ),
)
def test_decode_paths_rejects_unsafe_or_empty_paths(raw_paths: bytes) -> None:
    with pytest.raises(ValueError, match="unsafe repository-relative path"):
        _decode_paths(raw_paths)


@pytest.mark.parametrize(
    "raw_paths",
    (
        b"ignored-directory/\0ignored-directory\0",
        b"ignored-directory\0ignored-directory/\0",
        b"ordinary.txt\0ordinary.txt\0",
    ),
)
def test_decode_paths_rejects_duplicate_canonical_forms(raw_paths: bytes) -> None:
    with pytest.raises(ValueError, match="duplicate repository path"):
        _decode_paths(raw_paths)


@pytest.mark.parametrize(
    ("first_category", "second_category"),
    (
        ("tracked", "untracked"),
        ("tracked", "ignored"),
        ("untracked", "ignored"),
    ),
)
@pytest.mark.parametrize("relative_path", ("collision.txt", ".env"))
@pytest.mark.parametrize(
    ("first_suffix", "second_suffix"),
    (("", ""), ("", "/"), ("/", "")),
)
def test_inventory_rejects_cross_stream_canonical_collisions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    first_category: str,
    second_category: str,
    relative_path: str,
    first_suffix: str,
    second_suffix: str,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / relative_path).write_text("collision\n", encoding="utf-8")
    streams = {"tracked": b"", "untracked": b"", "ignored": b""}
    streams[first_category] = f"{relative_path}{first_suffix}\0".encode()
    streams[second_category] = f"{relative_path}{second_suffix}\0".encode()
    categories_by_args = {
        ("ls-files", "-z"): "tracked",
        ("ls-files", "--others", "--exclude-standard", "-z"): "untracked",
        (
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        ): "ignored",
    }

    def synthetic_run_git(repo_arg: Path, *args: str) -> bytes:
        assert repo_arg == repo
        return streams[categories_by_args[args]]

    monkeypatch.setattr(git_capture_module, "run_git", synthetic_run_git)

    with pytest.raises(ValueError, match="duplicate repository path"):
        git_capture_module._inventory_state(repo, SecretPolicy.default())


def test_capture_canonicalizes_ignored_directory_marker(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    (repo / ".gitignore").write_text("ignored-directory/\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "ignore directory")
    (repo / "ignored-directory").mkdir()
    git(repo / "ignored-directory", "init")
    raw_ignored = run_git(
        repo,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
    )
    assert raw_ignored == b"ignored-directory/\0"

    first_records = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        tmp_path / "capsule-one",
        SecretPolicy.default(),
    )
    second_records = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        tmp_path / "capsule-two",
        SecretPolicy.default(),
    )

    first_manifest = json.loads(
        (
            tmp_path / "capsule-one" / "local-untracked-ignored" / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    second_manifest = json.loads(
        (
            tmp_path / "capsule-two" / "local-untracked-ignored" / "manifest.json"
        ).read_text(encoding="utf-8")
    )
    matching = [
        entry for entry in first_manifest if entry["path"] == "ignored-directory"
    ]
    assert first_records == second_records
    assert first_manifest == second_manifest
    assert len(matching) == 1
    assert matching[0]["kind"] == "directory"
    assert matching[0]["inclusion"] == "excluded"
    assert matching[0]["reason"] == "special-file-not-copied"
    assert matching[0]["size"] is None
    assert matching[0]["sha256"] is None
    assert isinstance(matching[0]["mode"], int)
    assert all(entry["path"] != "ignored-directory/" for entry in first_manifest)
    assert not (
        tmp_path
        / "capsule-one"
        / "local-untracked-ignored"
        / "payload"
        / "ignored-directory"
    ).exists()


def test_capture_rejects_destination_inside_source(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)

    with pytest.raises(
        ValueError, match="destination must be outside the source worktree"
    ):
        capture_planes(repo, "HEAD", "HEAD", repo / "capsule", SecretPolicy.default())

    assert not (repo / "capsule").exists()


def test_secret_named_file_is_redacted_not_copied(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    secret = repo / ".env"
    secret.write_text("TOKEN=do-not-copy\n", encoding="utf-8")
    destination = tmp_path / "capsule"

    records = capture_planes(repo, "HEAD", "HEAD", destination, SecretPolicy.default())

    assert not any(path.name == ".env" for path in destination.rglob("*"))
    manifest = json.loads(
        (destination / "local-untracked-ignored" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    entry = next(item for item in manifest if item["path"] == ".env")
    assert entry["inclusion"] == "redacted"
    assert entry["reason"] == "secret-name"
    assert entry["size"] is None
    assert entry["sha256"] is None
    record = next(item for item in records if item.plane_id is PlaneId.LOCAL_UNTRACKED)
    assert record.sensitivity is PlaneSensitivity.REDACTED
    assert record.eligibility is PlaneEligibility.INELIGIBLE
    assert record.verification is PlaneVerification.UNVERIFIABLE_REDACTED
    assert record.status is ResultStatus.BLOCKED
    assert len(records) == len(PlaneId)
    assert any(item.status is ResultStatus.PASS for item in records)
    metadata = json.loads(
        (destination / "local-untracked-ignored" / "metadata.json").read_text(
            encoding="utf-8"
        )
    )
    assert metadata["sensitivity"] == "redacted"
    assert metadata["eligibility"] == "ineligible"
    assert metadata["verification"] == "unverifiable-redacted"
    assert metadata["status"] == "BLOCKED"


def test_history_preserves_historical_env_only_as_blocked_opaque_payload(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    historical_secret = b"TOKEN=historical-secret\x00bytes\n"
    (repo / ".env").write_bytes(historical_secret)
    git(repo, "add", ".env")
    git(repo, "commit", "-m", "historical environment")
    historical_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    git(repo, "update-index", "--force-remove", ".env")
    git(repo, "commit", "-m", "remove environment from current tree")
    destination = tmp_path / "capsule"

    records = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        destination,
        SecretPolicy.default(),
    )

    history = next(
        record for record in records if record.plane_id is PlaneId.LOCAL_HISTORY
    )
    assert history.sensitivity is PlaneSensitivity.OPAQUE_SENSITIVE
    assert history.eligibility is PlaneEligibility.INELIGIBLE
    assert history.verification is PlaneVerification.OPAQUE_PRESERVED
    assert history.status is ResultStatus.BLOCKED
    metadata = json.loads(
        (destination / "local-history" / "identity.json").read_text(encoding="utf-8")
    )
    assert metadata["sensitivity"] == "opaque-sensitive"
    assert metadata["eligibility"] == "ineligible"
    assert metadata["verification"] == "opaque-preserved"
    assert metadata["status"] == "BLOCKED"
    restored = tmp_path / "restored-history"
    git(
        tmp_path,
        "clone",
        str(destination / "local-history" / "repository.bundle"),
        str(restored),
    )
    assert git(restored, "show", f"{historical_sha}:.env").stdout == historical_secret


def test_index_preserves_staged_secret_path_and_oid_only_as_blocked_opaque_payload(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    staged_secret = b"TOKEN=staged-secret\x00bytes\n"
    (repo / ".env").write_bytes(staged_secret)
    git(repo, "add", ".env")
    stage_line = git(repo, "ls-files", "--stage", "--", ".env").stdout
    staged_oid = stage_line.split()[1].decode("ascii")
    index_path = Path(
        git(repo, "rev-parse", "--path-format=absolute", "--git-path", "index")
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    index_before = index_path.read_bytes()
    destination = tmp_path / "capsule"

    records = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        destination,
        SecretPolicy.default(),
    )

    index_record = next(
        record for record in records if record.plane_id is PlaneId.LOCAL_INDEX
    )
    assert index_record.sensitivity is PlaneSensitivity.OPAQUE_SENSITIVE
    assert index_record.eligibility is PlaneEligibility.INELIGIBLE
    assert index_record.verification is PlaneVerification.OPAQUE_PRESERVED
    assert index_record.status is ResultStatus.BLOCKED
    index_payload = destination / "local-index" / "index.raw"
    assert index_payload.read_bytes() == index_before
    assert b".env" in index_payload.read_bytes()
    assert bytes.fromhex(staged_oid) in index_payload.read_bytes()
    assert (
        staged_secret not in (destination / "local-index" / "staged.diff").read_bytes()
    )
    metadata = json.loads(
        (destination / "local-index" / "metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["sensitivity"] == "opaque-sensitive"
    assert metadata["eligibility"] == "ineligible"
    assert metadata["verification"] == "opaque-preserved"
    assert metadata["status"] == "BLOCKED"
    restored = tmp_path / "restored-index"
    git(
        tmp_path,
        "clone",
        str(destination / "local-history" / "repository.bundle"),
        str(restored),
    )
    restored_index = Path(
        git(
            restored,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "index",
        )
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    restored_index.write_bytes(index_payload.read_bytes())
    restored_stage = git(restored, "ls-files", "--stage", "--", ".env").stdout
    assert restored_stage.split()[1].decode("ascii") == staged_oid
    assert restored_stage.rstrip(b"\r\n").endswith(b"\t.env")


def test_capture_writes_six_exact_source_planes(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    (repo / ".gitignore").write_text("*.log\n", encoding="utf-8")
    git(repo, "add", ".gitignore")
    git(repo, "commit", "-m", "ignore logs")
    (repo / "a.txt").write_bytes(b"staged\x00bytes\n")
    git(repo, "add", "a.txt")
    (repo / "a.txt").write_bytes(b"unstaged\x00bytes\n")
    (repo / "notes.txt").write_bytes(b"ordinary untracked\n")
    (repo / "ignored.log").write_bytes(b"ordinary ignored\n")
    before = snapshot_subject(repo)
    index_path = Path(
        git(repo, "rev-parse", "--path-format=absolute", "--git-path", "index")
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    index_before = index_path.read_bytes()
    destination = tmp_path / "capsule"

    records = capture_planes(repo, "HEAD", "HEAD", destination, SecretPolicy.default())

    assert tuple(record.plane_id for record in records) == tuple(PlaneId)
    assert len({record.digest for record in records}) == len(PlaneId)
    for record in records:
        assert (destination / record.plane_id.value).is_dir()
        assert len(record.digest) == 64
    assert (destination / "remote-main" / "repository.bundle").is_file()
    assert (destination / "remote-pr" / "repository.bundle").is_file()
    assert (destination / "local-history" / "repository.bundle").is_file()
    assert (destination / "local-index" / "index.raw").read_bytes() == index_before
    assert (
        destination / "local-index" / "staged.diff"
    ).read_bytes() == before.staged_diff
    assert (
        destination / "local-tracked" / "unstaged.diff"
    ).read_bytes() == before.unstaged_diff
    assert (
        destination / "local-untracked-ignored" / "payload" / "notes.txt"
    ).read_bytes() == b"ordinary untracked\n"
    assert (
        destination / "local-untracked-ignored" / "payload" / "ignored.log"
    ).read_bytes() == b"ordinary ignored\n"
    assert index_path.read_bytes() == index_before
    assert_unchanged(before, snapshot_subject(repo))
    source_path_bytes = str(repo.resolve()).encode("utf-8")
    assert all(
        source_path_bytes not in artifact.read_bytes()
        for artifact in destination.rglob("*")
        if artifact.is_file()
    )


def test_capture_records_are_deterministic(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    (repo / "ordinary.txt").write_bytes(b"same bytes\n")

    first = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        tmp_path / "capsule-one",
        SecretPolicy.default(),
    )
    second = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        tmp_path / "capsule-two",
        SecretPolicy.default(),
    )

    assert first == second


def test_history_bundles_do_not_expose_unrelated_divergent_refs(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    main_branch = git(repo, "branch", "--show-current").stdout.strip().decode("ascii")
    main_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    git(repo, "checkout", "-b", "feature")
    (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
    git(repo, "add", "feature.txt")
    git(repo, "commit", "-m", "feature")
    feature_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    git(repo, "checkout", main_branch)
    destination = tmp_path / "capsule"

    capture_planes(repo, main_sha, feature_sha, destination, SecretPolicy.default())

    main_heads = git(
        repo,
        "bundle",
        "list-heads",
        str(destination / "remote-main" / "repository.bundle"),
    ).stdout.splitlines()
    pr_heads = git(
        repo,
        "bundle",
        "list-heads",
        str(destination / "remote-pr" / "repository.bundle"),
    ).stdout.splitlines()
    history_heads = git(
        repo,
        "bundle",
        "list-heads",
        str(destination / "local-history" / "repository.bundle"),
    ).stdout.splitlines()
    assert len(main_heads) == 1
    assert main_heads[0].startswith(main_sha.encode("ascii") + b" ")
    assert len(pr_heads) == 1
    assert pr_heads[0].startswith(feature_sha.encode("ascii") + b" ")
    assert len(history_heads) == 1
    assert history_heads[0].startswith(main_sha.encode("ascii") + b" ")


def test_unreferenced_ancestor_remote_bundles_restore_exact_requested_heads(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    remote_main_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    (repo / "pr-only.txt").write_text("pr\n", encoding="utf-8")
    git(repo, "add", "pr-only.txt")
    git(repo, "commit", "-m", "pr generation")
    remote_pr_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    (repo / "local-only.txt").write_text("local\n", encoding="utf-8")
    git(repo, "add", "local-only.txt")
    git(repo, "commit", "-m", "local generation")
    local_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    ref_oids = {
        line.split(b" ", 1)[0].decode("ascii")
        for line in git(repo, "show-ref").stdout.splitlines()
    }
    assert remote_main_sha not in ref_oids
    assert remote_pr_sha not in ref_oids
    before = snapshot_subject(repo)
    index_path = Path(
        git(repo, "rev-parse", "--path-format=absolute", "--git-path", "index")
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    index_before = index_path.read_bytes()
    destination = tmp_path / "capsule"

    records = capture_planes(
        repo,
        remote_main_sha,
        remote_pr_sha,
        destination,
        SecretPolicy.default(),
    )

    expected = {
        PlaneId.REMOTE_MAIN: remote_main_sha,
        PlaneId.REMOTE_PR: remote_pr_sha,
        PlaneId.LOCAL_HISTORY: local_sha,
    }
    restored_roots: dict[PlaneId, Path] = {}
    for plane_id, expected_sha in expected.items():
        bundle = destination / plane_id.value / "repository.bundle"
        heads = git(repo, "bundle", "list-heads", str(bundle)).stdout.splitlines()
        assert len(heads) == 1
        assert heads[0].startswith(expected_sha.encode("ascii") + b" ")
        record = next(record for record in records if record.plane_id is plane_id)
        assert record.subject_id == expected_sha
        restored = tmp_path / f"restored-{plane_id.value}"
        git(tmp_path, "clone", str(bundle), str(restored))
        assert git(restored, "rev-parse", "HEAD").stdout.strip() == expected_sha.encode(
            "ascii"
        )
        restored_roots[plane_id] = restored

    assert not (restored_roots[PlaneId.REMOTE_MAIN] / "pr-only.txt").exists()
    assert not (restored_roots[PlaneId.REMOTE_MAIN] / "local-only.txt").exists()
    assert (
        git(
            restored_roots[PlaneId.REMOTE_MAIN],
            "cat-file",
            "-e",
            f"{remote_pr_sha}^{{commit}}",
            check=False,
        ).returncode
        != 0
    )
    assert (restored_roots[PlaneId.REMOTE_PR] / "pr-only.txt").is_file()
    assert not (restored_roots[PlaneId.REMOTE_PR] / "local-only.txt").exists()
    assert (
        git(
            restored_roots[PlaneId.REMOTE_PR],
            "cat-file",
            "-e",
            f"{local_sha}^{{commit}}",
            check=False,
        ).returncode
        != 0
    )
    assert (restored_roots[PlaneId.LOCAL_HISTORY] / "local-only.txt").is_file()
    assert index_path.read_bytes() == index_before
    assert_unchanged(before, snapshot_subject(repo))


@pytest.mark.parametrize("object_format", ["sha1", "sha256"])
def test_exact_ancestor_capture_preserves_source_object_format_deterministically(
    tmp_path: Path,
    object_format: str,
) -> None:
    repo = initialized_repo_with_object_format(tmp_path, object_format)
    remote_main_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    (repo / "pr-only.txt").write_text("pr\n", encoding="utf-8")
    git(repo, "add", "pr-only.txt")
    git(repo, "commit", "-m", "pr generation")
    remote_pr_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    (repo / "local-only.txt").write_text("local\n", encoding="utf-8")
    git(repo, "add", "local-only.txt")
    git(repo, "commit", "-m", "local generation")
    local_sha = git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")
    refs_before = git(repo, "show-ref", "--head").stdout
    ref_oids = {
        line.split(b" ", 1)[0].decode("ascii") for line in refs_before.splitlines()
    }
    assert remote_main_sha not in ref_oids
    assert remote_pr_sha not in ref_oids
    before = snapshot_subject(repo)
    index_path = Path(
        git(repo, "rev-parse", "--path-format=absolute", "--git-path", "index")
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    index_before = index_path.read_bytes()

    first_destination = tmp_path / "capsule-one"
    first = capture_planes(
        repo,
        remote_main_sha,
        remote_pr_sha,
        first_destination,
        SecretPolicy.default(),
    )
    second_destination = tmp_path / "capsule-two"
    second = capture_planes(
        repo,
        remote_main_sha,
        remote_pr_sha,
        second_destination,
        SecretPolicy.default(),
    )

    assert first == second
    assert artifact_tree(first_destination) == artifact_tree(second_destination)
    expected = {
        PlaneId.REMOTE_MAIN: remote_main_sha,
        PlaneId.REMOTE_PR: remote_pr_sha,
        PlaneId.LOCAL_HISTORY: local_sha,
    }
    for plane_id, expected_sha in expected.items():
        plane_root = first_destination / plane_id.value
        identity = json.loads(
            (plane_root / "identity.json").read_text(encoding="utf-8")
        )
        assert identity["object_format"] == object_format
        bundle = plane_root / "repository.bundle"
        heads = git(repo, "bundle", "list-heads", str(bundle)).stdout.splitlines()
        assert len(heads) == 1
        assert heads[0].startswith(expected_sha.encode("ascii") + b" ")
        restored = tmp_path / f"restored-{object_format}-{plane_id.value}"
        git(tmp_path, "clone", str(bundle), str(restored))
        assert git(restored, "rev-parse", "HEAD").stdout.strip() == expected_sha.encode(
            "ascii"
        )

    assert (
        git(
            tmp_path / f"restored-{object_format}-remote-main",
            "cat-file",
            "-e",
            f"{remote_pr_sha}^{{commit}}",
            check=False,
        ).returncode
        != 0
    )
    assert (
        git(
            tmp_path / f"restored-{object_format}-remote-pr",
            "cat-file",
            "-e",
            f"{local_sha}^{{commit}}",
            check=False,
        ).returncode
        != 0
    )
    assert git(repo, "show-ref", "--head").stdout == refs_before
    assert index_path.read_bytes() == index_before
    assert_unchanged(before, snapshot_subject(repo))


def test_sha256_partial_capture_remains_without_source_mutation(tmp_path: Path) -> None:
    repo = initialized_repo_with_object_format(tmp_path, "sha256")
    before = snapshot_subject(repo)
    refs_before = git(repo, "show-ref", "--head").stdout
    index_path = Path(
        git(repo, "rev-parse", "--path-format=absolute", "--git-path", "index")
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    index_before = index_path.read_bytes()
    destination = tmp_path / "partial-capsule"

    def stop_after_first_plane(plane_id: PlaneId) -> None:
        raise RuntimeError(f"injected stop after {plane_id.value}")

    with pytest.raises(RuntimeError, match="injected stop after remote-main"):
        capture_planes(
            repo,
            "HEAD",
            "HEAD",
            destination,
            SecretPolicy.default(),
            _between_planes=stop_after_first_plane,
        )

    partial = destination / "remote-main"
    assert (partial / "repository.bundle").is_file()
    assert not (partial / "source.git").exists()
    identity = json.loads(
        (partial / "identity.json").read_text(encoding="utf-8")
    )
    assert identity["object_format"] == "sha256"
    assert not (destination / "remote-pr").exists()
    assert git(repo, "show-ref", "--head").stdout == refs_before
    assert index_path.read_bytes() == index_before
    assert_unchanged(before, snapshot_subject(repo))


def test_default_secret_patterns_are_case_insensitive(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    secret_paths = (
        ".ENV.local",
        "my-TOKEN.txt",
        "my-credential.json",
        "API_KEY.txt",
        "private.KEY",
        "wallet-recovery.txt",
        "seed-phrase.txt",
        "wallet-mnemonic.md",
    )
    for relative in secret_paths:
        (repo / relative).write_bytes(b"must never enter capsule\n")
    destination = tmp_path / "capsule"

    capture_planes(repo, "HEAD", "HEAD", destination, SecretPolicy.default())

    manifest = json.loads(
        (destination / "local-untracked-ignored" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    entries = {item["path"]: item for item in manifest}
    assert set(secret_paths) <= entries.keys()
    for relative in secret_paths:
        assert entries[relative]["inclusion"] == "redacted"
        assert entries[relative]["size"] is None
        assert entries[relative]["sha256"] is None
        assert not (
            destination / "local-untracked-ignored" / "payload" / relative
        ).exists()


def test_tracked_secret_diff_with_pathspec_metacharacters_is_excluded(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    relative = ".env.prod.local"
    secret = repo / relative
    secret.write_bytes(b"non-secret committed baseline\n")
    git(repo, "add", relative)
    git(repo, "commit", "-m", "tracked secret-shaped path")
    staged_secret = b"STAGED-SECRET-MUST-NOT-LEAK\n"
    unstaged_secret = b"UNSTAGED-SECRET-MUST-NOT-LEAK\n"
    secret.write_bytes(staged_secret)
    git(repo, "add", relative)
    secret.write_bytes(unstaged_secret)
    destination = tmp_path / "capsule"

    records = capture_planes(repo, "HEAD", "HEAD", destination, SecretPolicy.default())

    artifact_bytes = [
        path.read_bytes() for path in destination.rglob("*") if path.is_file()
    ]
    assert all(staged_secret.strip() not in content for content in artifact_bytes)
    assert all(unstaged_secret.strip() not in content for content in artifact_bytes)
    manifest = json.loads(
        (destination / "local-tracked" / "manifest.json").read_text(encoding="utf-8")
    )
    entry = next(item for item in manifest if item["path"] == relative)
    assert entry["inclusion"] == "redacted"
    assert entry["size"] is None
    assert entry["sha256"] is None
    record = next(item for item in records if item.plane_id is PlaneId.LOCAL_TRACKED)
    assert record.sensitivity is PlaneSensitivity.REDACTED
    assert record.eligibility is PlaneEligibility.INELIGIBLE
    assert record.verification is PlaneVerification.UNVERIFIABLE_REDACTED
    assert record.status is ResultStatus.BLOCKED
    metadata = json.loads(
        (destination / "local-tracked" / "metadata.json").read_text(encoding="utf-8")
    )
    assert metadata["sensitivity"] == "redacted"
    assert metadata["eligibility"] == "ineligible"
    assert metadata["verification"] == "unverifiable-redacted"
    assert metadata["status"] == "BLOCKED"


def test_missing_tracked_secret_path_is_redacted_and_blocked(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    secret = repo / ".env"
    secret.write_bytes(b"committed secret\n")
    git(repo, "add", ".env")
    git(repo, "commit", "-m", "track secret-shaped path")
    secret.replace(tmp_path / "held-secret")

    records = capture_planes(
        repo,
        "HEAD",
        "HEAD",
        tmp_path / "capsule",
        SecretPolicy.default(),
    )

    tracked = next(
        record for record in records if record.plane_id is PlaneId.LOCAL_TRACKED
    )
    assert tracked.sensitivity is PlaneSensitivity.REDACTED
    assert tracked.status is ResultStatus.BLOCKED


def test_required_byte_equality_fails_closed_for_redacted_mutable_path(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    (repo / ".env").write_bytes(b"same-length-secret-a\n")

    with pytest.raises(
        CaptureUnverifiable,
        match="redacted mutable paths prevent byte-equality verification",
    ):
        capture_planes(
            repo,
            "HEAD",
            "HEAD",
            tmp_path / "capsule",
            SecretPolicy.default(),
            require_byte_equality=True,
        )

    assert (tmp_path / "capsule" / "local-untracked-ignored").is_dir()


def test_same_size_restored_mtime_secret_mutation_cannot_pass_byte_equality(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    secret = repo / ".env"
    original = b"same-length-secret-a\n"
    replacement = b"same-length-secret-b\n"
    assert len(original) == len(replacement)
    secret.write_bytes(original)
    original_stat = secret.stat()
    mutated = False

    def mutate_and_restore_mtime(_plane_id: PlaneId) -> None:
        nonlocal mutated
        if mutated:
            return
        secret.write_bytes(replacement)
        os.utime(
            secret,
            ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns),
        )
        mutated = True

    with pytest.raises(CaptureEvidenceError):
        capture_planes(
            repo,
            "HEAD",
            "HEAD",
            tmp_path / "capsule",
            SecretPolicy.default(),
            require_byte_equality=True,
            _between_planes=mutate_and_restore_mtime,
        )

    assert secret.read_bytes() == replacement
    assert secret.stat().st_size == original_stat.st_size
    assert secret.stat().st_mtime_ns == original_stat.st_mtime_ns
    artifact_bytes = [
        path.read_bytes()
        for path in (tmp_path / "capsule").rglob("*")
        if path.is_file()
    ]
    assert all(replacement not in content for content in artifact_bytes)


def test_capture_does_not_follow_untracked_symlink(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside secret\n")
    link = repo / "ordinary-link"
    try:
        link.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"symlinks unavailable: {error}")
    destination = tmp_path / "capsule"

    capture_planes(repo, "HEAD", "HEAD", destination, SecretPolicy.default())

    manifest = json.loads(
        (destination / "local-untracked-ignored" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    entry = next(item for item in manifest if item["path"] == "ordinary-link")
    assert entry["kind"] == "symlink"
    assert entry["inclusion"] == "excluded"
    assert entry["reason"] == "symlink-not-followed"
    assert not (
        destination / "local-untracked-ignored" / "payload" / "ordinary-link"
    ).exists()
    assert (
        b"outside secret"
        not in (destination / "local-untracked-ignored" / "manifest.json").read_bytes()
    )


def test_capture_detects_source_drift_between_planes(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    mutated = False

    def mutate_after_first_plane(plane_id: PlaneId) -> None:
        nonlocal mutated
        if not mutated:
            (repo / "a.txt").write_text(
                f"mutated after {plane_id.value}\n", encoding="utf-8"
            )
            mutated = True

    with pytest.raises(CaptureDrift, match="source state changed during capture"):
        capture_planes(
            repo,
            "HEAD",
            "HEAD",
            tmp_path / "capsule",
            SecretPolicy.default(),
            _between_planes=mutate_after_first_plane,
        )


def test_capture_detects_untracked_content_drift_at_same_path(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    untracked = repo / "ordinary.txt"
    untracked.write_bytes(b"before-content\n")
    mutated = False

    def mutate_untracked_after_first_plane(plane_id: PlaneId) -> None:
        nonlocal mutated
        if not mutated:
            untracked.write_bytes(b"after-content!\n")
            mutated = True

    with pytest.raises(CaptureDrift, match="source state changed during capture"):
        capture_planes(
            repo,
            "HEAD",
            "HEAD",
            tmp_path / "capsule",
            SecretPolicy.default(),
            _between_planes=mutate_untracked_after_first_plane,
        )


def test_capture_rejects_symlink_alias_into_source(tmp_path: Path) -> None:
    repo = initialized_repo(tmp_path)
    alias = tmp_path / "repo-alias"
    try:
        alias.symlink_to(repo, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"directory symlinks unavailable: {error}")

    with pytest.raises(
        ValueError, match="destination must be outside the source worktree"
    ):
        capture_planes(
            repo,
            "HEAD",
            "HEAD",
            alias / "capsule",
            SecretPolicy.default(),
        )


def test_capture_from_subdirectory_still_rejects_worktree_destination(
    tmp_path: Path,
) -> None:
    repo = initialized_repo(tmp_path)
    nested = repo / "nested"
    nested.mkdir()

    with pytest.raises(
        ValueError, match="destination must be outside the source worktree"
    ):
        capture_planes(
            nested,
            "HEAD",
            "HEAD",
            repo / "sibling-capsule",
            SecretPolicy.default(),
        )

    assert not (repo / "sibling-capsule").exists()


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


@pytest.mark.parametrize("linked_worktree", [False, True])
def test_snapshot_preserves_index_when_stat_cache_is_stale(
    tmp_path: Path,
    linked_worktree: bool,
) -> None:
    repo = initialized_repo(tmp_path)
    subject = repo
    if linked_worktree:
        subject = tmp_path / "linked"
        git(repo, "worktree", "add", "-b", "linked-stale-stat", str(subject))

    index_path = Path(
        git(
            subject,
            "rev-parse",
            "--path-format=absolute",
            "--git-path",
            "index",
        )
        .stdout.rstrip(b"\r\n")
        .decode("utf-8", errors="surrogateescape")
    )
    index_before = index_path.read_bytes()
    tracked_path = subject / "a.txt"
    tracked_stat = tracked_path.stat()
    os.utime(
        tracked_path,
        ns=(tracked_stat.st_atime_ns, tracked_stat.st_mtime_ns + 2_000_000_000),
    )

    first = snapshot_subject(subject)
    index_after_first = index_path.read_bytes()
    second = snapshot_subject(subject)

    assert index_after_first == index_before
    assert index_path.read_bytes() == index_before
    assert_unchanged(first, second)


def test_diff_ignores_external_diff_tool(tmp_path: Path) -> None:
    """An external diff tool configured in .gitattributes or gitconfig
    must not leak into captured diff bytes.  --no-ext-diff forces real
    git diff output so the capsule records reconstructable blobs, not
    arbitrary helper program output."""
    repo = initialized_repo(tmp_path)
    # Stage a change so staged_diff has content to capture.
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    git(repo, "add", "a.txt")
    # Create an unstaged change too.
    (repo / "b.txt").write_text("unstaged\n", encoding="utf-8")
    git(repo, "add", "b.txt")
    git(repo, "commit", "-m", "second")
    (repo / "b.txt").write_text("changed\n", encoding="utf-8")

    # Configure an external diff tool that would corrupt the output.
    git(repo, "config", "diff.external", "echo external-diff-output")

    snapshot = snapshot_subject(repo)

    # The captured diffs must be real git diff output, not the echo helper.
    assert b"external-diff-output" not in snapshot.staged_diff
    assert b"external-diff-output" not in snapshot.unstaged_diff
    # And they must contain real diff content (blob hashes, not helper text).
    assert b"diff --git" in snapshot.staged_diff or snapshot.staged_diff == b""
    assert b"diff --git" in snapshot.unstaged_diff


def test_capture_ignores_ambient_git_routing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ambient GIT_DIR/GIT_INDEX_FILE/GIT_OBJECT_DIRECTORY must not redirect
    capture queries.  Under a Git hook these point at another repository;
    _git_environment strips every GIT_* variable so `git -C --repo` wins."""
    repo = initialized_repo(tmp_path)
    intruder = tmp_path / "intruder"
    git(tmp_path, "init", str(intruder))
    git(intruder, "config", "user.email", "test@example.invalid")
    git(intruder, "config", "user.name", "Test")
    (intruder / "evil.txt").write_text("evil\n", encoding="utf-8")
    git(intruder, "add", "evil.txt")
    git(intruder, "commit", "-m", "intruder")

    monkeypatch.setenv("GIT_DIR", str(intruder / ".git"))
    monkeypatch.setenv("GIT_INDEX_FILE", str(intruder / ".git" / "index"))
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", str(intruder / ".git" / "objects"))

    # The snapshot runs under the poisoned environment (the behavior under
    # test).  Witness heads are read after undo() because the test helper
    # inherits os.environ and would otherwise resolve through GIT_DIR too.
    snapshot = snapshot_subject(repo)

    monkeypatch.undo()
    expected_head = git(repo, "rev-parse", "HEAD").stdout
    intruder_head = git(intruder, "rev-parse", "HEAD").stdout
    assert snapshot.head == expected_head
    assert snapshot.head != intruder_head


def test_staged_diff_ignores_textconv_helpers(tmp_path: Path) -> None:
    """A configured diff.<driver>.textconv helper must not rewrite captured
    diff bytes.  --no-ext-diff does NOT disable textconv: without
    --no-textconv a helper returning identical text for both blobs makes
    staged.diff empty while snapshots still compare equal."""
    repo = initialized_repo(tmp_path)
    (repo / "doc.txt").write_text("real content\n", encoding="utf-8")
    git(repo, "add", "doc.txt")
    (repo / ".gitattributes").write_text("*.txt diff=constdriver\n", encoding="utf-8")
    git(repo, "config", "diff.constdriver.textconv", "echo constant")
    (repo / "doc.txt").write_text("changed content\n", encoding="utf-8")
    git(repo, "add", "doc.txt")

    snapshot = snapshot_subject(repo)

    assert b"constant" not in snapshot.staged_diff
    assert b"changed content" in snapshot.staged_diff


def test_staged_diff_uses_stable_prefixes(tmp_path: Path) -> None:
    """diff.noprefix / diff.mnemonicPrefix must not break header parsing.
    _split_diff_header requires a/ b/ prefixes; explicit --src-prefix/--dst-prefix
    keeps capture deterministic regardless of repo config."""
    repo = initialized_repo(tmp_path)
    (repo / "f.txt").write_text("one\n", encoding="utf-8")
    git(repo, "add", "f.txt")
    git(repo, "commit", "-m", "add f")
    (repo / "f.txt").write_text("two\n", encoding="utf-8")
    git(repo, "add", "f.txt")
    git(repo, "config", "diff.noprefix", "true")

    snapshot = snapshot_subject(repo)

    assert b"diff --git a/f.txt b/f.txt" in snapshot.staged_diff


def test_split_index_backing_file_is_bundled(tmp_path: Path) -> None:
    """Under core.splitIndex the index is a stub pointing at
    $GIT_DIR/sharedindex.<oid>.  The capsule must bundle that backing
    file beside index.raw (with its sha256 in metadata), not a dangling
    pointer."""
    repo = initialized_repo(tmp_path)
    git(repo, "update-index", "--split-index")
    backing = sorted((repo / ".git").glob("sharedindex.*"))
    assert backing, "test setup: expected git to split the index"

    capture_planes(repo, "HEAD", "HEAD", tmp_path / "capsule", SecretPolicy.default())

    import json

    plane = tmp_path / "capsule" / "local-index"
    metadata = json.loads((plane / "metadata.json").read_text(encoding="utf-8"))
    assert (plane / "index.raw").exists()
    recorded = {entry["name"]: entry["sha256"] for entry in metadata["shared_index_files"]}
    assert [shared.name for shared in backing] == sorted(recorded)
    for shared in backing:
        copied = plane / shared.name
        assert copied.exists()
        assert recorded[shared.name] == hashlib.sha256(shared.read_bytes()).hexdigest()


def test_split_index_with_unpreservable_backing_file_fails_closed(
    tmp_path: Path,
) -> None:
    """A sharedindex.* entry that is not a plain file (here: swapped for a
    directory; a symlink to elsewhere is the same branch) cannot be
    faithfully bundled — capture must fail closed, not record a stub
    index.raw with no backing."""
    repo = initialized_repo(tmp_path)
    git(repo, "update-index", "--split-index")
    backing = sorted((repo / ".git").glob("sharedindex.*"))
    assert backing, "test setup: expected git to split the index"
    victim = backing[0]
    victim.unlink()
    victim.mkdir()

    with pytest.raises(CaptureDrift):
        capture_planes(repo, "HEAD", "HEAD", tmp_path / "capsule", SecretPolicy.default())


def test_surrogate_path_is_unpreservable() -> None:
    """A path with undecodable bytes (surrogateescape residue) cannot be
    represented in the UTF-8 JSON capsule — it must fail closed, not reach
    canonical_json_bytes as an unclassified UnicodeEncodeError."""
    with pytest.raises(CaptureDrift):
        _require_preservable_paths(("a\udcff.txt",))


def test_inventory_with_undecodable_names_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The preservable-paths gate must sit INSIDE _inventory_state, before
    the fingerprints are canonicalized: otherwise a surrogate-bearing
    name dies as an unclassified UnicodeEncodeError at digest time.
    (The git boundary is stubbed because Windows cannot host undecodable
    filenames; only ls-files output is faked, everything else is real.)"""
    repo = initialized_repo(tmp_path)
    real_run_git = git_capture_module.run_git

    def fake_run_git(repo_arg: Path, *args: str) -> bytes:
        # Only the tracked inventory (`ls-files -z`, no --others) carries
        # the undecodable name. Other ls-files variants stay empty so we
        # don't trip the duplicate-across-categories guard first.
        if args[:2] == ("ls-files", "-z"):
            return b"\xff\xfe\x00"
        if args and args[0] == "ls-files":
            return b""
        return real_run_git(repo_arg, *args)

    monkeypatch.setattr(git_capture_module, "run_git", fake_run_git)
    with pytest.raises(CaptureDrift):
        _inventory_state(repo, SecretPolicy.default())


def test_resolve_race_during_file_read_maps_to_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A worktree path vanishing between lstat and resolve (concurrent
    source mutation) must surface as CaptureDrift — not a bare OSError
    that callers catching CaptureEvidenceError would miss."""
    from pathlib import Path as _Path

    repo = initialized_repo(tmp_path)
    (repo / "victim.txt").write_text("here\n", encoding="utf-8")

    def vanishing(self: Path, *args: object, **kwargs: object) -> Path:
        raise FileNotFoundError("simulated concurrent deletion")

    monkeypatch.setattr(_Path, "resolve", vanishing)
    with pytest.raises(CaptureDrift):
        _read_regular_file(repo, "victim.txt")


def test_non_nfc_path_fails_closed_before_state_dir(tmp_path: Path) -> None:
    """A valid non-NFC name passes capture validation but the manifest
    contract requires NFC — capture must fail closed with a typed error
    BEFORE creating the state directory, not seal planes it can never
    inventory."""
    repo = initialized_repo(tmp_path)
    # Decomposed e + combining acute (explicit escapes: a literal é here
    # would be the NFC form and would not exercise the branch).
    (repo / "é.txt").write_text("decomposed\n", encoding="utf-8")

    with pytest.raises(CaptureDrift):
        capture_planes(repo, "HEAD", "HEAD", tmp_path / "capsule", SecretPolicy.default())
    assert not (tmp_path / "capsule").exists()


@pytest.mark.parametrize(
    ("relative_path", "expected_secret"),
    [
        (".env", True),
        (".env.local", True),
        (".env.prod.local", True),
        ("my-token.txt", True),
        ("config/api_key.yaml", True),
        ("wallet-seed.txt", True),
        ("secrets.txt", True),
        ("credentials.json", True),
        ("mnemonic.txt", True),
        ("keystore.jks", True),
        ("seed.txt", True),
        ("private.key", True),
        ("id_rsa", True),
        # Separator variants: markers use underscores, filenames use dashes.
        ("api-key.txt", True),
        ("id-rsa", True),
        ("my-private-key.pem", True),
        # Directory components do not redact: marker must be in the stem.
        ("config/env/settings.py", False),
        ("docs/patterns-guide.md", False),  # stem has no marker substring
        # The old whole-path substring policy also redacted these via the
        # stem, and still does.  This is the fail-closed default.
        ("docs/seed.md", True),
        ("seedling.md", True),
        ("README.md", False),
        ("src/main.py", False),
    ],
)
def test_secret_policy_path_component_match(
    relative_path: str, expected_secret: bool
) -> None:
    """Markers match the filename stem (substring), exact components,
    dotfile prefixes, and suffixes — but never directory components.
    Over-redaction is the intended fail-closed default."""
    policy = SecretPolicy.default()
    assert policy.is_secret(relative_path) is expected_secret
