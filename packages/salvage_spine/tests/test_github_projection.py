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


def _subject_for_plane(
    plane_id: PlaneId,
    *,
    remote_main_sha: str = "1" * 40,
    pr_head_sha: str = "2" * 40,
    local_history_sha: str = "3" * 40,
) -> str:
    subject_ids = {
        PlaneId.REMOTE_MAIN: remote_main_sha,
        PlaneId.REMOTE_PR: pr_head_sha,
        PlaneId.LOCAL_HISTORY: local_history_sha,
        PlaneId.LOCAL_INDEX: "4" * 64,
        PlaneId.LOCAL_TRACKED: "5" * 64,
        PlaneId.LOCAL_UNTRACKED: "6" * 64,
    }
    return subject_ids[plane_id]


def _plane(
    plane_id: PlaneId,
    *,
    subject_id: str | None = None,
    status: ResultStatus = ResultStatus.PASS,
    blockers: tuple[str, ...] = (),
) -> PlaneRestoreResult:
    return PlaneRestoreResult(
        plane_id=plane_id,
        subject_id=subject_id or _subject_for_plane(plane_id),
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
    planes: tuple[PlaneRestoreResult, ...] | None = None,
    commit_match: bool = True,
    tree_match: bool = True,
    artifact_match: bool = True,
    remote_main_sha: str = "1" * 40,
    pr_head_sha: str = "2" * 40,
    local_history_sha: str = "3" * 40,
) -> VerificationRecord:
    return VerificationRecord(
        schema_version="1",
        authentication="local-unanchored",
        provenance_root="a" * 64,
        status=status,
        checksum_status=ResultStatus.PASS,
        planes=planes
        or tuple(
            _plane(
                plane_id,
                subject_id=_subject_for_plane(
                    plane_id,
                    remote_main_sha=remote_main_sha,
                    pr_head_sha=pr_head_sha,
                    local_history_sha=local_history_sha,
                ),
            )
            for plane_id in PlaneId
        ),
        commit_match=commit_match,
        tree_match=tree_match,
        artifact_match=artifact_match,
        blockers=blockers,
    )


def _checkpoint(
    verification: VerificationRecord,
    manifest: dict[str, object],
    *,
    verification_digest: str | None = None,
    next_safe_command: str = "python -m pytest packages/salvage_spine/tests -q",
    blockers: tuple[str, ...] = (),
    remote_main_sha: str = "1" * 40,
    pr_head_sha: str = "2" * 40,
) -> Checkpoint:
    return Checkpoint(
        schema_version="1.0.0",
        sequence=2,
        previous_digest="9" * 64,
        state_id="capsule-state-1",
        phase="projection-ready",
        input_shas={
            "remote_main": remote_main_sha,
            "pr_head": pr_head_sha,
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
    planes: tuple[PlaneRestoreResult, ...] | None = None,
    commit_match: bool = True,
    tree_match: bool = True,
    artifact_match: bool = True,
    manifest: dict[str, object] | None = None,
    remote_main_sha: str = "1" * 40,
    pr_head_sha: str = "2" * 40,
    local_history_sha: str = "3" * 40,
) -> Evidence:
    verification = _verification(
        status=verification_status,
        blockers=verification_blockers,
        planes=planes,
        commit_match=commit_match,
        tree_match=tree_match,
        artifact_match=artifact_match,
        remote_main_sha=remote_main_sha,
        pr_head_sha=pr_head_sha,
        local_history_sha=local_history_sha,
    )
    manifest = manifest or _manifest(
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
        remote_main_sha=remote_main_sha,
        pr_head_sha=pr_head_sha,
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


@pytest.mark.parametrize(
    "overrides",
    [
        {"checkpoint_blockers": ("manual-review-pending",)},
        {"verification_blockers": ("restore-output-incomplete",)},
        {"classification_state": "captured"},
        {"primary_lane": "consensus-gateway"},
    ],
)
def test_preservation_never_passes_when_blocked_or_unclassified_work_exists(
    overrides: dict[str, object],
) -> None:
    summary = render_check_summary(_evidence(**overrides))
    assert summary["preservation"]["status"] == ResultStatus.BLOCKED.value
    assert "NOT READY FOR CONTAINMENT" in render_stop_merge_comment(
        _evidence(**overrides)
    )


@pytest.mark.parametrize(
    "planes",
    [
        (_plane(PlaneId.REMOTE_MAIN, status=ResultStatus.BLOCKED),),
        tuple(_plane(plane_id) for plane_id in tuple(PlaneId)[:-1]),
        tuple(
            list(_plane(plane_id) for plane_id in PlaneId)
            + [_plane(PlaneId.REMOTE_MAIN)]
        ),
    ],
)
def test_contradictory_plane_sets_fail_closed(
    planes: tuple[PlaneRestoreResult, ...],
) -> None:
    with pytest.raises(ValueError, match="plane|verification"):
        render_check_summary(_evidence(planes=planes))


def test_unknown_plane_value_fails_closed() -> None:
    forged = PlaneRestoreResult(
        plane_id="unexpected-plane",  # type: ignore[arg-type]
        subject_id="a" * 40,
        status=ResultStatus.PASS,
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
        blockers=(),
    )
    with pytest.raises(ValueError, match="plane|verification"):
        render_check_summary(_evidence(planes=(forged,)))


def test_raw_string_plane_id_lookalike_fails_closed() -> None:
    forged = PlaneRestoreResult(
        plane_id="remote-main",  # type: ignore[arg-type]
        subject_id="1" * 40,
        status=ResultStatus.PASS,
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
        blockers=(),
    )
    with pytest.raises(ValueError, match="plane|verification"):
        render_check_summary(_evidence(planes=(forged,)))


@pytest.mark.parametrize(
    ("plane_id", "subject_id"),
    [
        (PlaneId.REMOTE_MAIN, "a" * 40),
        (PlaneId.REMOTE_PR, "b" * 40),
    ],
)
def test_history_plane_subject_binding_mismatch_fails_closed(
    plane_id: PlaneId,
    subject_id: str,
) -> None:
    planes = tuple(
        _plane(
            current,
            subject_id=(
                subject_id if current is plane_id else _subject_for_plane(current)
            ),
        )
        for current in PlaneId
    )
    with pytest.raises(ValueError, match="subject|checkpoint|sha|verification"):
        render_check_summary(_evidence(planes=planes))


def test_swapped_remote_history_subjects_fail_closed() -> None:
    planes = tuple(
        _plane(
            plane_id,
            subject_id={
                PlaneId.REMOTE_MAIN: "2" * 40,
                PlaneId.REMOTE_PR: "1" * 40,
            }.get(plane_id, _subject_for_plane(plane_id)),
        )
        for plane_id in PlaneId
    )
    with pytest.raises(ValueError, match="subject|checkpoint|sha|verification"):
        render_check_summary(_evidence(planes=planes))


@pytest.mark.parametrize(
    ("remote_main_sha", "pr_head_sha", "remote_main_subject", "remote_pr_subject"),
    [
        ("1" * 40, "2" * 40, "A" * 40, "2" * 40),
        ("1" * 40, "2" * 40, "1" * 64, "2" * 40),
        ("1" * 64, "2" * 64, "1" * 64, "2" * 40),
    ],
)
def test_history_plane_hash_case_and_length_mismatches_fail_closed(
    remote_main_sha: str,
    pr_head_sha: str,
    remote_main_subject: str,
    remote_pr_subject: str,
) -> None:
    planes = tuple(
        _plane(
            plane_id,
            subject_id={
                PlaneId.REMOTE_MAIN: remote_main_subject,
                PlaneId.REMOTE_PR: remote_pr_subject,
            }.get(
                plane_id,
                _subject_for_plane(
                    plane_id,
                    remote_main_sha=remote_main_sha,
                    pr_head_sha=pr_head_sha,
                    local_history_sha="3" * len(remote_main_sha),
                ),
            ),
        )
        for plane_id in PlaneId
    )
    with pytest.raises(ValueError, match="subject|checkpoint|sha|verification"):
        render_check_summary(
            _evidence(
                planes=planes,
                remote_main_sha=remote_main_sha,
                pr_head_sha=pr_head_sha,
                local_history_sha="3" * len(remote_main_sha),
            )
        )


def test_duplicate_history_plane_identity_fails_closed() -> None:
    planes = (
        _plane(PlaneId.REMOTE_MAIN),
        _plane(PlaneId.REMOTE_MAIN),
        _plane(PlaneId.LOCAL_HISTORY),
        _plane(PlaneId.LOCAL_INDEX),
        _plane(PlaneId.LOCAL_TRACKED),
        _plane(PlaneId.LOCAL_UNTRACKED),
    )
    with pytest.raises(ValueError, match="plane|verification"):
        render_check_summary(_evidence(planes=planes))


def test_display_correct_remote_plane_with_forged_subject_binding_fails_closed() -> (
    None
):
    planes = tuple(
        _plane(
            plane_id,
            subject_id=(
                "f" * 40
                if plane_id is PlaneId.REMOTE_MAIN
                else _subject_for_plane(plane_id)
            ),
        )
        for plane_id in PlaneId
    )
    with pytest.raises(ValueError, match="subject|checkpoint|sha|verification"):
        render_check_summary(_evidence(planes=planes))


def test_valid_sha1_history_plane_bindings_still_pass() -> None:
    summary = render_check_summary(_evidence())
    assert summary["preservation"]["status"] == ResultStatus.PASS.value


def test_valid_sha256_history_plane_bindings_still_pass() -> None:
    summary = render_check_summary(
        _evidence(
            remote_main_sha="1" * 64,
            pr_head_sha="2" * 64,
            local_history_sha="3" * 64,
        )
    )
    assert summary["preservation"]["status"] == ResultStatus.PASS.value


@pytest.mark.parametrize("status", [ResultStatus.FAIL, ResultStatus.BLOCKED])
def test_any_non_pass_plane_blocks_preservation_even_when_aggregate_flags_are_green(
    status: ResultStatus,
) -> None:
    planes = tuple(
        _plane(
            plane_id,
            status=status if plane_id is PlaneId.LOCAL_TRACKED else ResultStatus.PASS,
        )
        for plane_id in PlaneId
    )
    summary = render_check_summary(
        _evidence(
            planes=planes,
            verification_status=ResultStatus.PASS,
            commit_match=True,
            tree_match=True,
            artifact_match=True,
        )
    )
    assert summary["preservation"]["status"] != ResultStatus.PASS.value
    assert "NOT READY FOR CONTAINMENT" in render_stop_merge_comment(
        _evidence(
            planes=planes,
            verification_status=ResultStatus.PASS,
            commit_match=True,
            tree_match=True,
            artifact_match=True,
        )
    )


@pytest.mark.parametrize(
    ("commit_match", "tree_match", "artifact_match"),
    [
        (False, True, True),
        (True, False, True),
        (True, True, False),
    ],
)
def test_forged_aggregate_green_flags_cannot_elevate_preservation(
    commit_match: bool,
    tree_match: bool,
    artifact_match: bool,
) -> None:
    summary = render_check_summary(
        _evidence(
            commit_match=commit_match,
            tree_match=tree_match,
            artifact_match=artifact_match,
        )
    )
    assert summary["preservation"]["status"] != ResultStatus.PASS.value


def test_manifest_graph_contradictions_fail_closed() -> None:
    manifest = _manifest()
    manifest["atoms"].append(dict(manifest["atoms"][0]))
    manifest["items"].append(dict(manifest["items"][0]))
    with pytest.raises(ValueError, match="manifest"):
        render_check_summary(_evidence(manifest=manifest))


def test_raw_string_cannot_masquerade_as_result_status() -> None:
    evidence = _evidence()
    forged = Evidence(
        verification=evidence.verification,
        checkpoint=evidence.checkpoint,
        manifest=evidence.manifest,
        absolute_core_status="PASS",  # type: ignore[arg-type]
        regression_core_status=ResultStatus.PASS,
        evidence_locations=evidence.evidence_locations,
    )
    with pytest.raises(ValueError, match="ResultStatus"):
        render_check_summary(forged)


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
        "artifacts/verification.json#frag",
        "artifacts/manifest.json?raw=1",
        "artifacts/%2e%2e/secret.json",
        "file:///C:/secret.txt",
        r"C:\secret.txt",
        r"\\server\share\secret.txt",
        "https://example.invalid/projection",
        "artifacts/%252e%252e/secret.json",
        "artifacts/..%2fsecret.json",
        "artifacts/%E2%88%95secret.json",
        "artifacts\\secret.json",
        "<https://example.invalid/projection>",
        "![img](artifacts/x.png)",
        "[x](artifacts/y.json)",
        "<img src='artifacts/x.json'>",
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


@pytest.mark.parametrize(
    "hostile_text",
    [
        "<script>alert(1)</script>",
        "![img](file:///secret)",
        "[click](https://example.invalid)",
        "<https://example.invalid>",
        "<img src='x'>",
        "Bearer abc.def",
        "token=shhh",
        "-----BEGIN PRIVATE KEY-----",
        "gh pr comment 38 --body boom",
        "curl -X POST https://example.invalid",
    ],
)
def test_hostile_renderable_field_content_does_not_survive_output(
    hostile_text: str,
) -> None:
    text = render_stop_merge_comment(
        _evidence(
            checkpoint_blockers=(hostile_text,),
            verification_blockers=(hostile_text,),
        )
    )
    assert hostile_text not in text
    assert "file://" not in text
    assert "https://example.invalid" not in text
    assert "gh pr comment" not in text
    assert "curl -X POST" not in text


@pytest.mark.parametrize(
    "unsafe_command",
    [
        "gh pr comment 38 --body nope",
        "curl -X POST https://example.invalid",
        r"C:\temp\run.ps1",
        "python scripts/pr38_salvage.py status#frag",
    ],
)
def test_mutating_or_unsafe_next_safe_commands_are_rejected(
    unsafe_command: str,
) -> None:
    with pytest.raises(ValueError, match="unsafe|command|path"):
        render_stop_merge_comment(_evidence(next_safe_command=unsafe_command))


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
