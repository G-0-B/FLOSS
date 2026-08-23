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


def test_cli_flow_capture_verify_stops_before_inventory_when_blocked(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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
        == 1
    )
    verify_stdout = json.loads(capsys.readouterr().out)
    assert verify_stdout["phase"] == "verification-complete"
    assert verify_stdout["status"] == ResultStatus.BLOCKED.value
    assert verify_stdout["inventory_eligible"] is False
    assert verify_stdout["verification_digest"]
    assert not (state_dir / "manifest.json").exists()

    assert main(["inventory", "--capsule", str(state_dir)]) == 1
    assert "inventory-eligible" in capsys.readouterr().err

    assert main(["status", "--capsule", str(state_dir)]) == 1
    final_status = json.loads(capsys.readouterr().out)
    assert final_status["phase"] == "verification-complete"
    assert final_status["next_safe_command"].startswith(
        "python scripts/preservation_spine.py status"
    )


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
        == 1
    )
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
        == 1
    )
    second = json.loads(capsys.readouterr().out)
    assert second["phase"] == "verification-complete"
    assert second["idempotent"] is True
    assert second["status"] == ResultStatus.BLOCKED.value
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
