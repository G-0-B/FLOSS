from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from packages.preservation_spine import cli as cli_module
from packages.preservation_spine.cli import main
from packages.preservation_spine.checkpoint import load_latest_checkpoint
from packages.preservation_spine.models import ResultStatus, canonical_json_bytes
from packages.preservation_spine.tests.test_github_projection import _verification
from packages.preservation_spine.tests.test_seal_restore import git


def _write_and_commit(repo: Path, name: str, content: bytes, message: str) -> str:
    (repo / name).parent.mkdir(parents=True, exist_ok=True)
    (repo / name).write_bytes(content)
    git(repo, "add", "--", name)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD").stdout.strip().decode("ascii")


def _build_repo(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    git(tmp_path, "init", str(repo))
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    main_sha = _write_and_commit(repo, "main.txt", b"main\n", "main")
    pr_sha = _write_and_commit(repo, "pr.txt", b"pr\n", "pr")
    _write_and_commit(repo, "local.txt", b"local\n", "local")
    (repo / "staged.bin").write_bytes(b"staged\n")
    git(repo, "add", "--", "staged.bin")
    (repo / "local.txt").write_bytes(b"local changed\n")
    (repo / "ordinary.tmp").write_bytes(b"ordinary untracked\n")
    return repo, main_sha, pr_sha


def _repo_snapshot(repo: Path) -> tuple[bytes, bytes]:
    return (
        git(repo, "status", "--porcelain=v2", "-z", "--ignored").stdout,
        (repo / ".git" / "index").read_bytes(),
    )


def test_cli_exposes_only_local_commands(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "capture" in output
    assert "verify" in output
    assert "inventory" in output
    assert "render-github" in output
    assert "status" in output
    assert "mark-draft" not in output
    assert "post-comment" not in output


def test_capture_rejects_ref_names_and_nonlowercase_shas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, _, _ = _build_repo(tmp_path)
    output = tmp_path / "capsule-state-1"

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                "HEAD",
                "--pr-head-sha",
                "ABCDEF0123456789ABCDEF0123456789ABCDEF01",
                "--output",
                str(output),
            ]
        )
        == 1
    )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "sha" in captured.err.lower()
    assert not output.exists()


def test_capture_lists_tracked_secrets_in_exclusions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A tracked path redacted by the secret policy must appear in the
    top-level capsule exclusions.  Regression: the reader looked under
    'local-tracked-worktree' while the plane is 'local-tracked', so
    tracked secrets were silently omitted from capsule.json."""
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    _write_and_commit(repo, "api_key.txt", b"hunter2\n", "secret")
    state_dir = tmp_path / "capsule-state-secret"

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()

    # Isolate the tracked plane: empty every other plane's exclusion list
    # so only local-tracked/metadata.json can supply the secret.  (In a
    # full capsule the index plane duplicates the same list, which masks
    # the dead read path.)
    capsule_root = state_dir / "capsule"
    for plane in ("local-index", "local-untracked-ignored"):
        metadata_path = capsule_root / plane / "metadata.json"
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        payload["secret_path_exclusions"] = []
        metadata_path.write_text(json.dumps(payload), encoding="utf-8")

    assert "api_key.txt" in cli_module._excluded_paths(capsule_root)

    record = json.loads((state_dir / "capsule.json").read_text(encoding="utf-8"))
    assert "api_key.txt" in record["exclusions"]


def test_inventory_refuses_unverified_capsule(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    state_dir = tmp_path / "capsule-state-raw"
    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["inventory", "--capsule", str(state_dir)]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "verification" in captured.err.lower()


def test_capture_refuses_output_inside_source_repository(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    output = repo / "capsule-state"

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(output),
            ]
        )
        == 1
    )
    assert not output.exists()
    assert "outside" in capsys.readouterr().err


def test_cli_flow_capture_verify_authenticated_but_not_releasable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A real capsule with design-ineligible planes (opaque/redacted) is
    authenticated (inventory-eligible) but not releasable (containment-blocked).
    Inventory and render-github should succeed; containment_eligible is False."""
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    before = _repo_snapshot(repo)
    state_dir = tmp_path / "capsule-state-1"

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    after_capture = _repo_snapshot(repo)
    assert after_capture == before
    capture_stdout = json.loads(capsys.readouterr().out)
    assert capture_stdout["phase"] == "capture-complete"
    assert capture_stdout["state_id"].startswith("capsule-")

    checkpoint = load_latest_checkpoint(state_dir / "checkpoints.jsonl")
    assert checkpoint.phase == "capture-complete"
    assert checkpoint.verification_digest is None
    assert checkpoint.next_safe_command.startswith(
        "python scripts/preservation_spine.py verify"
    )

    assert main(["status", "--capsule", str(state_dir)]) == 1
    status_after_capture = json.loads(capsys.readouterr().out)
    assert status_after_capture["next_safe_command"].startswith(
        "python scripts/preservation_spine.py verify"
    )
    assert status_after_capture["phase"] == "capture-complete"
    assert status_after_capture["blockers"] == ["verification-pending"]

    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(state_dir / "nested-restore"),
                "--forbid-root",
                str(repo),
            ]
        )
        == 1
    )
    assert "overlaps" in capsys.readouterr().err
    assert not (state_dir / "nested-restore").exists()

    restore_root = tmp_path / "restore"
    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(restore_root),
                "--forbid-root",
                str(repo),
            ]
        )
        == 0
    )
    verify_stdout = json.loads(capsys.readouterr().out)
    assert verify_stdout["phase"] == "verification-complete"
    assert verify_stdout["status"] == ResultStatus.BLOCKED.value
    assert verify_stdout["inventory_eligible"] is True
    assert verify_stdout["containment_eligible"] is False
    assert verify_stdout["verification_digest"]

    # Inventory should now succeed (authenticated), even though containment is blocked.
    assert main(["inventory", "--capsule", str(state_dir)]) == 0
    capsys.readouterr()

    assert main(["status", "--capsule", str(state_dir)]) == 0
    final_status = json.loads(capsys.readouterr().out)
    assert final_status["phase"] == "inventory-complete"


def test_reverify_after_payload_mutation_reports_stale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Re-running verify after a sealed payload file changed (with
    verification.json untouched) must NOT re-attest the old result.
    Regression lock-in: the idempotent path re-runs verify_checksums and
    reports verification-stale."""
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    state_dir = tmp_path / "capsule-state-stale"
    capture_args = [
        "capture",
        "--repo",
        str(repo),
        "--remote-main-sha",
        main_sha,
        "--pr-head-sha",
        pr_sha,
        "--output",
        str(state_dir),
    ]
    assert main(capture_args) == 0
    capsys.readouterr()
    restore_one = tmp_path / "restore-one"
    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(restore_one),
                "--forbid-root",
                str(repo),
            ]
        )
        == 0
    )
    capsys.readouterr()

    # Tamper with a sealed payload file, leaving verification.json alone.
    staged_diff = state_dir / "capsule" / "local-index" / "staged.diff"
    assert staged_diff.is_file()
    with staged_diff.open("ab") as handle:
        handle.write(b"tampered\n")

    restore_two = tmp_path / "restore-two"
    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(restore_two),
                "--forbid-root",
                str(repo),
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["phase"] == "verification-stale"


def test_inventory_rejects_verification_with_unbound_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Extra fields added to verification.json after verification must not
    be silently discarded: inventory recomputes the bound digest from known
    fields while render-github would copy the raw file including the
    unvalidated field.  The loader must reject unknown fields outright."""
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    state_dir = tmp_path / "capsule-state-unbound"
    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()
    restore_root = tmp_path / "restore"
    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(restore_root),
                "--forbid-root",
                str(repo),
            ]
        )
        == 0
    )
    capsys.readouterr()

    verification_path = state_dir / "capsule" / "verification.json"
    payload = json.loads(verification_path.read_text(encoding="utf-8"))
    payload["source_absolute_path"] = str(repo)
    payload["planes"][0]["extra_diagnostic"] = "unvalidated"
    verification_path.write_text(json.dumps(payload), encoding="utf-8")

    assert main(["inventory", "--capsule", str(state_dir)]) != 0


def test_reverification_dedupes_completed_actions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fresh re-verification (verification.json rebuilt, not the
    idempotent shortcut) must strip-then-append 'restore-verified' like
    the inventory/render handlers do — and drop the stale
    'manifest-inventoried' entry the new digest invalidates."""
    from packages.preservation_spine.checkpoint import load_latest_checkpoint

    repo, main_sha, pr_sha = _build_repo(tmp_path)
    state_dir = tmp_path / "capsule-state-redup"
    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()

    def run_verify(restore: Path) -> int:
        return main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(restore),
                "--forbid-root",
                str(repo),
            ]
        )

    assert run_verify(tmp_path / "restore-one") == 0
    capsys.readouterr()
    assert main(["inventory", "--capsule", str(state_dir)]) == 0
    capsys.readouterr()

    # Force a FRESH re-verification (not the idempotent shortcut) by
    # removing the record; the handler rebuilds and re-appends it.
    (state_dir / "capsule" / "verification.json").unlink()
    assert run_verify(tmp_path / "restore-two") == 0
    capsys.readouterr()

    actions = load_latest_checkpoint(state_dir / "checkpoints.jsonl").completed_actions
    assert actions.count("restore-verified") == 1
    assert "manifest-inventoried" not in actions


def test_blocked_verification_is_repeatable_without_rewriting_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    state_dir = tmp_path / "capsule-state-2"

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(tmp_path / "restore-two"),
                "--forbid-root",
                str(repo),
            ]
        )
        == 0
    )
    first = json.loads(capsys.readouterr().out)
    assert first["inventory_eligible"] is True
    assert first["containment_eligible"] is False
    capsys.readouterr()
    verification_before = (state_dir / "capsule" / "verification.json").read_bytes()
    checkpoints_before = (state_dir / "checkpoints.jsonl").read_bytes()

    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(tmp_path / "unused-repeat-restore"),
                "--forbid-root",
                str(repo),
            ]
        )
        == 0
    )
    second = json.loads(capsys.readouterr().out)
    assert second["phase"] == "verification-complete"
    assert second["idempotent"] is True
    assert second["status"] == ResultStatus.BLOCKED.value
    assert second["inventory_eligible"] is True
    assert second["containment_eligible"] is False
    assert (
        state_dir / "capsule" / "verification.json"
    ).read_bytes() == verification_before
    assert (state_dir / "checkpoints.jsonl").read_bytes() == checkpoints_before

    # A sealed payload byte changes while verification.json does NOT.
    #
    # The idempotent shortcut compared only verification.json's digest, so this
    # re-reported the old `verification-complete` -- the verify command
    # attesting to a capsule that had changed since the attestation. For a
    # preservation tool that is the worst failure available: not missing damage,
    # but certifying its absence.
    payloads = [
        path
        for path in (state_dir / "capsule").rglob("*")
        if path.is_file() and path.name not in {"verification.json"}
    ]
    assert payloads, "fixture must contain sealed payload files"
    victim = sorted(payloads)[0]
    victim.write_bytes(victim.read_bytes() + b"tampered")

    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(tmp_path / "unused-tampered-restore"),
                "--forbid-root",
                str(repo),
            ]
        )
        == 1
    )
    tampered = json.loads(capsys.readouterr().out)
    assert tampered["phase"] == "verification-stale", (
        "a changed capsule must not be re-attested as verification-complete; "
        f"got {tampered['phase']!r}"
    )
    assert tampered["idempotent"] is False
    assert tampered["inventory_eligible"] is False



def test_pass_flow_inventory_render_and_overlap_guards(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    state_dir = tmp_path / "pass-state"
    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(state_dir),
            ]
        )
        == 0
    )
    capsys.readouterr()
    captured = load_latest_checkpoint(state_dir / "checkpoints.jsonl")

    def pass_verification(capsule: Path, restore: Path, **_: object):
        record = replace(
            _verification(remote_main_sha=main_sha, pr_head_sha=pr_sha),
            provenance_root=captured.capsule_root,
        )
        (capsule / "verification.json").write_bytes(canonical_json_bytes(record))
        return record

    monkeypatch.setattr(cli_module, "restore_and_verify", pass_verification)
    assert (
        main(
            [
                "verify",
                "--capsule",
                str(state_dir),
                "--restore",
                str(tmp_path / "pass-restore"),
                "--forbid-root",
                str(repo),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["inventory", "--capsule", str(state_dir)]) == 0
    capsys.readouterr()

    checkpoint_path = state_dir / "checkpoints.jsonl"
    checkpoint = load_latest_checkpoint(checkpoint_path)
    manifest = json.loads((state_dir / "manifest.json").read_text(encoding="utf-8"))
    assert checkpoint.state_id == manifest["state_id"]
    assert "<" not in checkpoint.next_safe_command
    assert main(["status", "--capsule", str(state_dir)]) == 0
    assert json.loads(capsys.readouterr().out)["blockers"] == []

    failed_output = tmp_path / "failed-render"
    with monkeypatch.context() as scoped:
        scoped.setattr(
            cli_module,
            "render_check_summary",
            lambda evidence: (_ for _ in ()).throw(ValueError("invalid evidence")),
        )
        assert (
            main(
                [
                    "render-github",
                    "--capsule",
                    str(state_dir),
                    "--output",
                    str(failed_output),
                ]
            )
            == 1
        )
    capsys.readouterr()
    assert not failed_output.exists()

    inside_capsule = state_dir / "capsule" / "render-inside"
    assert (
        main(
            [
                "render-github",
                "--capsule",
                str(state_dir),
                "--output",
                str(inside_capsule),
            ]
        )
        == 1
    )
    assert "overlaps" in capsys.readouterr().err
    assert not inside_capsule.exists()

    source_artifacts = {
        "verification.json": (state_dir / "capsule" / "verification.json").read_bytes(),
        "manifest.json": (state_dir / "manifest.json").read_bytes(),
        "checkpoints.jsonl": checkpoint_path.read_bytes(),
    }
    source_artifact_digests = {
        name: hashlib.sha256(content).hexdigest()
        for name, content in source_artifacts.items()
    }
    output = tmp_path / "projection"
    assert (
        main(
            [
                "render-github",
                "--capsule",
                str(state_dir),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == {
        "next_safe_command": "python scripts/preservation_spine.py status --capsule STATE_DIR",
        "phase": "projection-rendered",
        "status": ResultStatus.BLOCKED.value,
    }

    projection_files = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert projection_files == {
        "artifacts/checkpoints.jsonl",
        "artifacts/manifest.json",
        "artifacts/verification.json",
        "check-summary.json",
        "stop-merge-comment.md",
    }
    for name, expected_bytes in source_artifacts.items():
        rendered_bytes = (output / "artifacts" / name).read_bytes()
        assert rendered_bytes == expected_bytes
        assert (
            hashlib.sha256(rendered_bytes).hexdigest() == source_artifact_digests[name]
        )

    artifact_checkpoint = load_latest_checkpoint(
        output / "artifacts" / "checkpoints.jsonl"
    )
    assert artifact_checkpoint == checkpoint
    summary_bytes = (output / "check-summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    assert summary_bytes == canonical_json_bytes(summary)
    assert summary["status"] == ResultStatus.BLOCKED.value
    assert summary["preservation"]["status"] == ResultStatus.BLOCKED.value
    assert summary["locked_shas"] == {
        "pr_head": pr_sha,
        "remote_main": main_sha,
    }
    assert summary["digests"] == {
        "capsule_root": checkpoint.capsule_root,
        "manifest": checkpoint.manifest_digest,
        "verification": checkpoint.verification_digest,
    }
    assert summary["checkpoint"] == {
        "digest": checkpoint.digest,
        "sequence": checkpoint.sequence,
    }
    assert summary["evidence_locations"] == {
        "checkpoint": "artifacts/checkpoints.jsonl",
        "manifest": "artifacts/manifest.json",
        "verification": "artifacts/verification.json",
    }

    comment = (output / "stop-merge-comment.md").read_text(encoding="utf-8")
    assert comment.startswith(
        "PROPOSED STOP-MERGE NOTICE — DO NOT POST BEFORE PRESERVATION PASSES\n"
    )
    for bound_value in (
        main_sha,
        pr_sha,
        checkpoint.capsule_root,
        checkpoint.manifest_digest,
        checkpoint.verification_digest,
    ):
        assert bound_value in comment
    assert "GitHub controls do not confer authority" in comment

    projection_checkpoint = load_latest_checkpoint(checkpoint_path)
    assert projection_checkpoint.sequence == checkpoint.sequence + 1
    assert projection_checkpoint.previous_digest == checkpoint.digest
    assert projection_checkpoint.phase == "projection-rendered"
    assert projection_checkpoint.capsule_root == checkpoint.capsule_root
    assert projection_checkpoint.manifest_digest == checkpoint.manifest_digest
    assert projection_checkpoint.verification_digest == checkpoint.verification_digest
    assert projection_checkpoint.blockers == checkpoint.blockers
    assert projection_checkpoint.next_safe_command == (
        "python scripts/preservation_spine.py status --capsule STATE_DIR"
    )


def test_script_help_matches_main_surface(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/preservation_spine.py", "--help"],
        cwd=Path(__file__).parents[3],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "capture" in result.stdout
    assert "render-github" in result.stdout
    assert "post-comment" not in result.stdout


def test_capture_drift_surfaces_real_exception_message(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CaptureDrift from capture_planes must reach the user with its real message, not 'local-only preservation command failed'."""
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    output = tmp_path / "capsule-state-drift"

    from packages.preservation_spine.git_capture import CaptureDrift

    def _raise_drift(*args: object, **kwargs: object) -> object:
        raise CaptureDrift("source state changed during capture")

    monkeypatch.setattr("packages.preservation_spine.cli.capture_planes", _raise_drift)

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(output),
            ]
        )
        == 1
    )

    captured = capsys.readouterr()
    assert "source state changed during capture" in captured.err
    assert "local-only preservation command failed" not in captured.err


def test_capture_cleans_up_output_dir_on_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """If capture fails before the genesis checkpoint is written, the
    output directory must be removed so a re-run is not blocked by
    a partial capsule."""
    repo, main_sha, pr_sha = _build_repo(tmp_path)
    output = tmp_path / "capsule-state-fail"

    from packages.preservation_spine.git_capture import CaptureDrift

    def _fail_capture(*args: object, **kwargs: object) -> object:
        raise CaptureDrift("injected failure after mkdir")

    monkeypatch.setattr("packages.preservation_spine.cli.capture_planes", _fail_capture)

    assert (
        main(
            [
                "capture",
                "--repo",
                str(repo),
                "--remote-main-sha",
                main_sha,
                "--pr-head-sha",
                pr_sha,
                "--output",
                str(output),
            ]
        )
        == 1
    )

    assert not output.exists(), "output dir must be removed on capture failure"
