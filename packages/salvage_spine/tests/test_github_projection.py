from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from packages.salvage_spine.checkpoint import Checkpoint
from packages.salvage_spine.manifest import manifest_digest
from packages.salvage_spine.models import PlaneId, ResultStatus, canonical_json_bytes
from packages.salvage_spine.restore import PlaneRestoreResult, VerificationRecord
from packages.salvage_spine.github_projection import (
    Evidence,
    render_check_summary,
    render_stop_merge_comment,
)


def _plane(
    plane_id: PlaneId,
    *,
    status: ResultStatus = ResultStatus.PASS,
    blockers: tuple[str, ...] = (),
) -> PlaneRestoreResult:
    return PlaneRestoreResult(
        plane_id=plane_id,
        subject_id=(plane_id.value.replace("-", ""))[:12].ljust(40, "a"),
        status=status,
        commit_match=True,
        tree_match=True,
        parent_match=True,
        mode_path_match=True,
        object_reachability=True,
        tree_id="b" * 40,
        parents_digest="c" * 64,
        mode_path_digest="d" * 64,
        evidence_digest="e" * 64,
        artifact_digests=(("artifact.json", "f" * 64),),
        artifact_match=True,
        payload_digest="1" * 64,
        payload_count=1,
        blockers=blockers,
    )


def _manifest(
    *,
    classification_state: str = "classified",
    primary_lane: str = "preservation-admin",
    disposition: str | None = "park",
) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "state_id": "capsule-state-1",
        "capsule_root": "a" * 64,
        "atoms": [
            {
                "atom_id": "atom-a",
                "source_plane": PlaneId.LOCAL_TRACKED.value,
                "source_commit": "b" * 40,
                "path_before": "before.txt",
                "path_after": "after.txt",
                "blob_before": "c" * 40,
                "blob_after": "d" * 40,
                "mode_before": "100644",
                "mode_after": "100644",
                "exact_diff_digest": "e" * 64,
            }
        ],
        "items": [
            {
                "item_id": "item-a",
                "revision_id": "revision-a",
                "atom_ids": ["atom-a"],
                "primary_lane": primary_lane,
                "classification_state": classification_state,
                "disposition": disposition,
                "required_gate_ids": [],
                "dependencies": [],
                "blockers": [],
                "required_profiles": [],
                "replacement_item_id": None,
                "notes": "Locally inventoried capsule evidence; no salvage intent inferred.",
            }
        ],
    }


def _verification(
    *,
    status: ResultStatus = ResultStatus.PASS,
    blockers: tuple[str, ...] = (),
) -> VerificationRecord:
    return VerificationRecord(
        schema_version="1",
        authentication="local-unanchored",
        provenance_root="a" * 64,
        status=status,
        checksum_status=ResultStatus.PASS,
        planes=tuple(_plane(plane_id) for plane_id in PlaneId),
        commit_match=True,
        tree_match=True,
        artifact_match=True,
        blockers=blockers,
    )


def _checkpoint(
    verification: VerificationRecord,
    manifest: dict[str, object],
    *,
    verification_digest: str | None = None,
    next_safe_command: str = "python -m pytest packages/salvage_spine/tests -q",
    blockers: tuple[str, ...] = (),
) -> Checkpoint:
    return Checkpoint(
        schema_version="1.0.0",
        sequence=2,
        previous_digest="9" * 64,
        state_id="capsule-state-1",
        phase="projection-ready",
        input_shas={
            "remote_main": "1" * 40,
            "pr_head": "2" * 40,
        },
        capsule_root=verification.provenance_root,
        manifest_digest=manifest_digest(manifest),
        verification_digest=verification_digest,
        completed_actions=(
            "captured-six-planes",
            "sealed-capsule",
            "restore-verified",
            "manifest-inventoried",
        ),
        blockers=blockers,
        human_decisions=("preserve-read-only-first",),
        next_safe_command=next_safe_command,
        recovery_command="python scripts/pr38_salvage.py status --latest",
        digest=None,
    )


def _evidence(
    *,
    verification_status: ResultStatus = ResultStatus.PASS,
    absolute_core_status: ResultStatus = ResultStatus.PASS,
    regression_core_status: ResultStatus = ResultStatus.PASS,
    classification_state: str = "classified",
    primary_lane: str = "preservation-admin",
    checkpoint_blockers: tuple[str, ...] = (),
    verification_blockers: tuple[str, ...] = (),
    next_safe_command: str = "python -m pytest packages/salvage_spine/tests -q",
    evidence_locations: dict[str, str] | None = None,
) -> Evidence:
    verification = _verification(
        status=verification_status,
        blockers=verification_blockers,
    )
    manifest = _manifest(
        classification_state=classification_state,
        primary_lane=primary_lane,
        disposition=None if classification_state == "captured" else "park",
    )
    bound_digest = None
    if verification_status is not ResultStatus.BLOCKED:
        bound_digest = hashlib.sha256(canonical_json_bytes(verification)).hexdigest()
    checkpoint = _checkpoint(
        verification,
        manifest,
        verification_digest=bound_digest,
        next_safe_command=next_safe_command,
        blockers=checkpoint_blockers,
    )
    return Evidence(
        verification=verification,
        checkpoint=checkpoint,
        manifest=manifest,
        absolute_core_status=absolute_core_status,
        regression_core_status=regression_core_status,
        evidence_locations=evidence_locations
        or {
            "verification": "artifacts/verification.json",
            "manifest": "artifacts/manifest.json",
            "checkpoint": "artifacts/checkpoints.jsonl",
        },
    )


def test_core_check_name_cannot_imply_global_success() -> None:
    summary = render_check_summary(_evidence())
    assert summary["name"] == "Core engineering checks — scoped evidence only"
    assert "verified" not in summary["title"].lower()
    assert "ready" not in summary["title"].lower()
    assert summary["preservation"]["name"] == (
        "Preservation capsule — restore-tested evidence"
    )


def test_comment_refuses_readiness_without_clean_room_restore() -> None:
    text = render_stop_merge_comment(_evidence(verification_status=ResultStatus.FAIL))
    assert "NOT READY FOR CONTAINMENT" in text
    assert "mark this PR Draft" not in text
    assert "GitHub controls do not confer authority" in text


def test_projection_requires_bound_verification_digest_before_preservation_pass() -> (
    None
):
    evidence = _evidence()
    unbound = Evidence(
        verification=evidence.verification,
        checkpoint=_checkpoint(
            evidence.verification,
            evidence.manifest,
            verification_digest=None,
        ),
        manifest=evidence.manifest,
        absolute_core_status=ResultStatus.PASS,
        regression_core_status=ResultStatus.PASS,
        evidence_locations=evidence.evidence_locations,
    )
    summary = render_check_summary(unbound)
    assert summary["preservation"]["status"] == ResultStatus.BLOCKED.value
    assert "preservation passed" not in render_stop_merge_comment(unbound).lower()


def test_projection_reports_absolute_and_same_environment_dimensions_separately() -> (
    None
):
    summary = render_check_summary(
        _evidence(
            absolute_core_status=ResultStatus.FAIL,
            regression_core_status=ResultStatus.PASS,
        )
    )
    dimensions = summary["dimensions"]
    assert dimensions["absolute"]["status"] == ResultStatus.FAIL.value
    assert dimensions["same_environment_regression"]["status"] == (
        ResultStatus.PASS.value
    )
    assert summary["status"] == ResultStatus.FAIL.value


def test_projection_renders_unclassified_and_protected_lane_counts() -> None:
    text = render_stop_merge_comment(
        _evidence(
            classification_state="captured",
            primary_lane="consensus-gateway",
            verification_status=ResultStatus.BLOCKED,
        )
    )
    assert "Unclassified items: 1" in text
    assert "Hard-stop items: 1" in text
    assert "NOT READY FOR CONTAINMENT" in text


def test_projection_is_deterministic_and_pure_for_pass_case(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import socket
    import subprocess

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no subprocess")),
    )
    monkeypatch.setattr(
        socket,
        "socket",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("no socket")),
    )

    evidence = _evidence()
    first_summary = render_check_summary(evidence)
    second_summary = render_check_summary(evidence)
    first_comment = render_stop_merge_comment(evidence)
    second_comment = render_stop_merge_comment(evidence)

    assert first_summary == second_summary
    assert first_comment == second_comment


def test_projection_sanitizes_markdown_html_paths_and_secret_like_strings() -> None:
    evidence = _evidence(
        checkpoint_blockers=(
            "<script>alert(1)</script>",
            "Bearer super-secret-token",
            r"C:\Users\kalis\secret.txt",
        ),
        evidence_locations={
            "verification": "artifacts/verification.json",
            "manifest": "artifacts/manifest.json",
            "checkpoint": "artifacts/checkpoints.jsonl",
        },
    )
    text = render_stop_merge_comment(evidence)
    assert "<script>" not in text
    assert "Bearer super-secret-token" not in text
    assert r"C:\Users\kalis\secret.txt" not in text
    assert "file://" not in text


@pytest.mark.parametrize(
    "unsafe_location",
    [
        "../private/verification.json",
        "file:///C:/secret.txt",
        r"C:\secret.txt",
        r"\\server\share\secret.txt",
        "https://example.invalid/projection",
    ],
)
def test_projection_rejects_traversal_and_url_scheme_locations(
    unsafe_location: str,
) -> None:
    with pytest.raises(ValueError, match="location|path|unsafe|scheme"):
        render_stop_merge_comment(
            _evidence(
                evidence_locations={
                    "verification": unsafe_location,
                    "manifest": "artifacts/manifest.json",
                    "checkpoint": "artifacts/checkpoints.jsonl",
                }
            )
        )


def test_template_is_proposed_noncanonical_and_has_no_remote_api_command() -> None:
    template = (
        Path(__file__).parents[3]
        / "docs"
        / "superpowers"
        / "templates"
        / "pr38-stop-merge-comment.md"
    ).read_text(encoding="utf-8")
    assert template.splitlines()[0] == (
        "PROPOSED STOP-MERGE NOTICE — DO NOT POST BEFORE PRESERVATION PASSES"
    )
    lowered = template.lower()
    assert "gh pr" not in lowered
    assert "curl " not in lowered
    assert "invoke-webrequest" not in lowered
    assert "non-canonical" in lowered
