from __future__ import annotations

import argparse
from collections.abc import Sequence
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

from .checkpoint import (
    Checkpoint,
    CheckpointIntegrityError,
    append_checkpoint,
    load_latest_checkpoint,
)
from .git_capture import (
    CaptureDrift,
    CaptureEvidenceError,
    CaptureUnverifiable,
    SecretPolicy,
    capture_planes,
)
from .github_projection import Evidence, render_check_summary, render_stop_merge_comment
from .manifest import inventory_change_universe, manifest_digest
from .models import (
    CapsuleRecord,
    PlaneId,
    PlaneRecord,
    ResultStatus,
    canonical_json_bytes,
)
from .restore import PlaneRestoreResult, VerificationRecord, restore_and_verify
from .seal import (
    CapsuleVerificationError,
    provenance_root,
    seal_capsule,
    verify_checksums,
)

_CAPSULE_DIRNAME = "capsule"
_CAPSULE_RECORD = "capsule.json"
_CHECKPOINT_FILE = "checkpoints.jsonl"
_MANIFEST_FILE = "manifest.json"
_VERIFICATION_FILE = "verification.json"
_CHECK_SUMMARY_FILE = "check-summary.json"
_STOP_MERGE_FILE = "stop-merge-comment.md"
_ARTIFACTS_DIR = "artifacts"
_SHA_PATTERN_LENGTHS = {40, 64}
_SAFE_STATE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
)
_RENDER_PHASES = {"projection-rendered"}
_INVENTORY_PHASES = {"inventory-complete", *_RENDER_PHASES}
_VERIFY_PHASES = {"verification-complete", *_INVENTORY_PHASES}
_STATUS_COMMAND = "python scripts/preservation_spine.py status --capsule STATE_DIR"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="preservation_spine",
        description="Local-only repository preservation-capsule commands.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    capture_parser = subparsers.add_parser(
        "capture",
        help="Capture six local preservation planes.",
    )
    capture_parser.add_argument("--repo", required=True)
    capture_parser.add_argument("--remote-main-sha", required=True)
    capture_parser.add_argument("--pr-head-sha", required=True)
    capture_parser.add_argument("--output", required=True)
    capture_parser.set_defaults(handler=_handle_capture)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a sealed capsule in a clean room.",
    )
    verify_parser.add_argument("--capsule", required=True)
    verify_parser.add_argument("--restore", required=True)
    verify_parser.add_argument("--forbid-root", required=True, action="append")
    verify_parser.set_defaults(handler=_handle_verify)

    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Inventory a verified capsule locally.",
    )
    inventory_parser.add_argument("--capsule", required=True)
    inventory_parser.set_defaults(handler=_handle_inventory)

    render_parser = subparsers.add_parser(
        "render-github",
        help="Render local Markdown and JSON evidence projections.",
    )
    render_parser.add_argument("--capsule", required=True)
    render_parser.add_argument("--output", required=True)
    render_parser.add_argument(
        "--absolute-core-status",
        default=ResultStatus.BLOCKED.value,
        choices=[status.value for status in ResultStatus],
    )
    render_parser.add_argument(
        "--regression-core-status",
        default=ResultStatus.BLOCKED.value,
        choices=[status.value for status in ResultStatus],
    )
    render_parser.set_defaults(handler=_handle_render_github)

    status_parser = subparsers.add_parser(
        "status",
        help="Report checkpoint chain status.",
    )
    status_parser.add_argument("--capsule", required=True)
    status_parser.set_defaults(handler=_handle_status)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    namespace = build_parser().parse_args(list(argv) if argv is not None else None)
    try:
        return int(namespace.handler(namespace))
    except (
        CapsuleVerificationError,
        CheckpointIntegrityError,
        CaptureEvidenceError,
        ValueError,
    ) as exc:
        _emit_error(str(exc))
        return 1
    except Exception:
        _emit_error("local-only salvage command failed")
        return 1


def _handle_capture(args: argparse.Namespace) -> int:
    repo = _existing_directory(Path(args.repo), field_name="repo")
    remote_main_sha = _validated_sha(args.remote_main_sha, field_name="remote_main_sha")
    pr_head_sha = _validated_sha(args.pr_head_sha, field_name="pr_head_sha")
    state_dir = _state_directory(Path(args.output), repo=repo)
    capsule_root = state_dir / _CAPSULE_DIRNAME

    try:
        records = capture_planes(
            repo,
            remote_main_sha,
            pr_head_sha,
            capsule_root,
            SecretPolicy.default(),
        )
        _validated_state_id(state_dir.name)
        capsule_root_hash = seal_capsule(capsule_root)
        precomputed_manifest = inventory_change_universe(capsule_root)
        state_id = _validated_state_id(str(precomputed_manifest["state_id"]))
        _write_bytes(
            state_dir / _CAPSULE_RECORD,
            canonical_json_bytes(
                CapsuleRecord(
                    schema_version="1.0.0",
                    state_id=state_id,
                    repository=repo.name,
                    captured_at=_utc_now(),
                    planes=tuple(records),
                    exclusions=_excluded_paths(capsule_root),
                    status=_capsule_status(records),
                )
            ),
        )
    except Exception:
        # No genesis checkpoint has been written yet, so the output dir
        # is untracked and safe to remove.  This prevents a partial
        # capsule from blocking a re-run.
        import shutil

        shutil.rmtree(state_dir, ignore_errors=True)
        raise
    checkpoint = Checkpoint(
        schema_version="1.0.0",
        sequence=0,
        previous_digest=None,
        state_id=state_id,
        phase="capture-complete",
        input_shas={
            "remote_main": remote_main_sha,
            "pr_head": pr_head_sha,
        },
        capsule_root=capsule_root_hash,
        manifest_digest=manifest_digest(precomputed_manifest),
        verification_digest=None,
        completed_actions=("captured-six-planes", "sealed-capsule"),
        blockers=("verification-pending",),
        human_decisions=("preserve-read-only-first",),
        next_safe_command=(
            "python scripts/preservation_spine.py verify --capsule STATE_DIR "
            "--restore CLEAN_ROOM_DIR --forbid-root SOURCE_ROOT"
        ),
        recovery_command=_STATUS_COMMAND,
        digest=None,
    )
    append_checkpoint(state_dir / _CHECKPOINT_FILE, checkpoint)
    _emit_json(
        {
            "state_id": state_id,
            "phase": checkpoint.phase,
            "capsule_root": checkpoint.capsule_root,
            "next_safe_command": checkpoint.next_safe_command,
        }
    )
    return 0


def _handle_verify(args: argparse.Namespace) -> int:
    state_dir = _existing_state_dir(Path(args.capsule))
    checkpoint_path = state_dir / _CHECKPOINT_FILE
    latest = _load_checkpoint(state_dir)
    verification_path = state_dir / _CAPSULE_DIRNAME / _VERIFICATION_FILE
    if latest.phase in _VERIFY_PHASES and verification_path.is_file():
        digest = _verification_digest(verification_path)
        if latest.verification_digest == digest:
            # Re-verify the capsule BYTES before short-circuiting.
            #
            # The digest above covers verification.json only. Changing a sealed
            # payload file while leaving that record untouched used to take this
            # shortcut and re-report the old `verification-complete` -- the
            # verify command itself attesting to a capsule that had changed
            # since the attestation was made. For a preservation tool that is
            # the worst possible failure: not missing damage, but certifying it
            # as absent.
            try:
                verify_checksums(state_dir / _CAPSULE_DIRNAME)
            except CapsuleVerificationError as exc:
                _emit_json(
                    {
                        "phase": "verification-stale",
                        "status": ResultStatus.BLOCKED.value,
                        "inventory_eligible": False,
                        "verification_digest": digest,
                        "idempotent": False,
                        "error": str(exc),
                        "detail": (
                            "the recorded verification still matches, but the "
                            "sealed capsule no longer does; re-run verify "
                            "without reusing the checkpoint"
                        ),
                        "next_safe_command": _STATUS_COMMAND,
                    }
                )
                return 1
            existing = _load_verification(state_dir)
            authenticated = _verification_authenticated(existing)
            releasable = _verification_releasable(existing)
            _emit_json(
                {
                    "phase": "verification-complete",
                    "status": existing.status.value,
                    "inventory_eligible": authenticated,
                    "containment_eligible": releasable,
                    "verification_digest": digest,
                    "idempotent": True,
                    "next_safe_command": latest.next_safe_command,
                }
            )
            return 0 if authenticated else 1

    restore_root = _new_directory_target(Path(args.restore))
    forbidden_roots = tuple(
        _existing_directory(Path(value), field_name="forbid_root")
        for value in args.forbid_root
    )
    for forbidden_root in (*forbidden_roots, state_dir):
        if _paths_overlap(restore_root, forbidden_root):
            raise ValueError("clean-room destination overlaps a forbidden root")
    result = restore_and_verify(
        state_dir / _CAPSULE_DIRNAME,
        restore_root,
        forbidden_roots=(*forbidden_roots, state_dir),
    )
    verification_digest = hashlib.sha256(canonical_json_bytes(result)).hexdigest()
    authenticated = _verification_authenticated(result)
    releasable = _verification_releasable(result)
    if authenticated:
        next_safe = "python scripts/preservation_spine.py inventory --capsule STATE_DIR"
        blockers = () if releasable else result.blockers
    else:
        next_safe = _STATUS_COMMAND
        blockers = result.blockers
    checkpoint = Checkpoint(
        schema_version="1.0.0",
        sequence=latest.sequence + 1,
        previous_digest=latest.digest,
        state_id=latest.state_id,
        phase="verification-complete",
        input_shas=dict(latest.input_shas),
        capsule_root=latest.capsule_root,
        manifest_digest=latest.manifest_digest,
        verification_digest=verification_digest,
        completed_actions=(
            *_without_action(latest.completed_actions, "restore-verified"),
            "restore-verified",
        ),
        blockers=blockers,
        human_decisions=tuple(latest.human_decisions),
        next_safe_command=next_safe,
        recovery_command=_STATUS_COMMAND,
        digest=None,
    )
    append_checkpoint(checkpoint_path, checkpoint)
    _emit_json(
        {
            "phase": checkpoint.phase,
            "status": result.status.value,
            "inventory_eligible": authenticated,
            "containment_eligible": releasable,
            "verification_digest": verification_digest,
            "next_safe_command": checkpoint.next_safe_command,
        }
    )
    return 0 if authenticated else 1


def _handle_inventory(args: argparse.Namespace) -> int:
    state_dir = _existing_state_dir(Path(args.capsule))
    latest = _load_checkpoint(state_dir)
    verification = _load_verification(state_dir)
    verification_digest = hashlib.sha256(canonical_json_bytes(verification)).hexdigest()
    if latest.verification_digest != verification_digest:
        raise ValueError("inventory requires a bound verification digest")
    if not _verification_authenticated(verification):
        raise ValueError("inventory requires an authenticated verification record (checksums bound, no FAIL planes)")

    manifest_path = state_dir / _MANIFEST_FILE
    manifest = inventory_change_universe(state_dir / _CAPSULE_DIRNAME)
    digest = manifest_digest(manifest)
    if latest.phase in _INVENTORY_PHASES and manifest_path.is_file():
        existing = manifest_path.read_bytes()
        if (
            existing == canonical_json_bytes(manifest)
            and latest.manifest_digest == digest
        ):
            _emit_json(
                {
                    "phase": "inventory-complete",
                    "manifest_digest": digest,
                    "idempotent": True,
                    "next_safe_command": latest.next_safe_command,
                }
            )
            return 0

    _write_bytes(manifest_path, canonical_json_bytes(manifest))
    checkpoint = Checkpoint(
        schema_version="1.0.0",
        sequence=latest.sequence + 1,
        previous_digest=latest.digest,
        state_id=latest.state_id,
        phase="inventory-complete",
        input_shas=dict(latest.input_shas),
        capsule_root=latest.capsule_root,
        manifest_digest=digest,
        verification_digest=verification_digest,
        completed_actions=(
            *_without_action(latest.completed_actions, "manifest-inventoried"),
            "manifest-inventoried",
        ),
        blockers=(),
        human_decisions=tuple(latest.human_decisions),
        next_safe_command=(
            "python scripts/preservation_spine.py render-github --capsule STATE_DIR "
            "--output RENDER_DIR"
        ),
        recovery_command=_STATUS_COMMAND,
        digest=None,
    )
    append_checkpoint(state_dir / _CHECKPOINT_FILE, checkpoint)
    _emit_json(
        {
            "phase": checkpoint.phase,
            "manifest_digest": digest,
            "next_safe_command": checkpoint.next_safe_command,
        }
    )
    return 0


def _handle_render_github(args: argparse.Namespace) -> int:
    state_dir = _existing_state_dir(Path(args.capsule))
    latest = _load_checkpoint(state_dir)
    verification = _load_verification(state_dir)
    manifest = _load_json_object(state_dir / _MANIFEST_FILE)
    digest = manifest_digest(manifest)
    if latest.manifest_digest != digest:
        raise ValueError("render-github requires an inventoried manifest")
    if not _verification_authenticated(verification):
        raise ValueError(
            "render-github requires an authenticated verification record (checksums bound, no FAIL planes)"
        )

    evidence = Evidence(
        verification=verification,
        checkpoint=latest,
        manifest=manifest,
        absolute_core_status=ResultStatus(args.absolute_core_status),
        regression_core_status=ResultStatus(args.regression_core_status),
        evidence_locations={
            "verification": f"{_ARTIFACTS_DIR}/{_VERIFICATION_FILE}",
            "manifest": f"{_ARTIFACTS_DIR}/{_MANIFEST_FILE}",
            "checkpoint": f"{_ARTIFACTS_DIR}/{_CHECKPOINT_FILE}",
        },
    )
    summary = render_check_summary(evidence)
    comment = render_stop_merge_comment(evidence)

    output_dir = _new_directory_target(Path(args.output))
    if _paths_overlap(output_dir, state_dir):
        raise ValueError("render output overlaps the capsule state")
    artifacts_dir = output_dir / _ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=False)
    _copy_exact(
        state_dir / _CAPSULE_DIRNAME / _VERIFICATION_FILE,
        artifacts_dir / _VERIFICATION_FILE,
    )
    _copy_exact(state_dir / _MANIFEST_FILE, artifacts_dir / _MANIFEST_FILE)
    _copy_exact(state_dir / _CHECKPOINT_FILE, artifacts_dir / _CHECKPOINT_FILE)
    _write_bytes(output_dir / _CHECK_SUMMARY_FILE, canonical_json_bytes(summary))
    _write_bytes(
        output_dir / _STOP_MERGE_FILE,
        (
            comment.encode("utf-8")
            if comment.endswith("\n")
            else (comment + "\n").encode("utf-8")
        ),
    )
    checkpoint = Checkpoint(
        schema_version="1.0.0",
        sequence=latest.sequence + 1,
        previous_digest=latest.digest,
        state_id=latest.state_id,
        phase="projection-rendered",
        input_shas=dict(latest.input_shas),
        capsule_root=latest.capsule_root,
        manifest_digest=latest.manifest_digest,
        verification_digest=latest.verification_digest,
        completed_actions=(
            *_without_action(latest.completed_actions, "github-projection-rendered"),
            "github-projection-rendered",
        ),
        blockers=tuple(latest.blockers),
        human_decisions=tuple(latest.human_decisions),
        next_safe_command=_STATUS_COMMAND,
        recovery_command=_STATUS_COMMAND,
        digest=None,
    )
    append_checkpoint(state_dir / _CHECKPOINT_FILE, checkpoint)
    _emit_json(
        {
            "phase": checkpoint.phase,
            "status": summary["status"],
            "next_safe_command": checkpoint.next_safe_command,
        }
    )
    return 0


def _handle_status(args: argparse.Namespace) -> int:
    state_dir = _existing_state_dir(Path(args.capsule))
    latest = _load_checkpoint(state_dir)
    blockers = list(latest.blockers)
    if latest.verification_digest is not None:
        verification_path = state_dir / _CAPSULE_DIRNAME / _VERIFICATION_FILE
        if not verification_path.is_file():
            blockers.append("verification-record-missing")
        elif _verification_digest(verification_path) != latest.verification_digest:
            blockers.append("verification-digest-mismatch")
        else:
            verification = _load_verification(state_dir)
            if verification.provenance_root != latest.capsule_root:
                blockers.append("verification-capsule-root-mismatch")
            if (
                latest.phase in _INVENTORY_PHASES
                and not _verification_authenticated(verification)
            ):
                blockers.append("verification-not-authenticated")
    if latest.phase in _INVENTORY_PHASES and latest.manifest_digest is not None:
        manifest_path = state_dir / _MANIFEST_FILE
        if not manifest_path.is_file():
            blockers.append("manifest-missing")
        else:
            manifest = _load_json_object(manifest_path)
            if manifest_digest(manifest) != latest.manifest_digest:
                blockers.append("manifest-digest-mismatch")
            if manifest.get("state_id") != latest.state_id:
                blockers.append("manifest-state-id-mismatch")
            if manifest.get("capsule_root") != latest.capsule_root:
                blockers.append("manifest-capsule-root-mismatch")
    if provenance_root(state_dir / _CAPSULE_DIRNAME) != latest.capsule_root:
        blockers.append("capsule-root-mismatch")

    _emit_json(
        {
            "phase": latest.phase,
            "sequence": latest.sequence,
            "next_safe_command": latest.next_safe_command,
            "blockers": sorted(set(blockers)),
        }
    )
    return 1 if blockers else 0


def _existing_state_dir(path: Path) -> Path:
    state_dir = _existing_directory(path, field_name="capsule")
    try:
        _existing_directory(state_dir / _CAPSULE_DIRNAME, field_name="sealed capsule")
    except (OSError, ValueError):
        raise ValueError("capsule state directory is missing its sealed capsule")
    return state_dir


def _state_directory(path: Path, *, repo: Path) -> Path:
    state_dir = _new_directory_target(path)
    if (
        state_dir.resolve(strict=False) == repo
        or repo in state_dir.resolve(strict=False).parents
    ):
        raise ValueError("output directory must be outside the source repository")
    state_dir.mkdir(parents=True, exist_ok=False)
    return state_dir


def _existing_directory(path: Path, *, field_name: str) -> Path:
    _assert_no_alias_chain(path)
    resolved = path.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"{field_name} must be a directory")
    return resolved


def _new_directory_target(path: Path) -> Path:
    if path.exists() or path.is_symlink():
        raise ValueError("output directory must not already exist")
    _assert_no_alias_chain(path.parent if path.parent != path else path)
    return path.resolve(strict=False)


def _paths_overlap(left: Path, right: Path) -> bool:
    left_resolved = left.resolve(strict=False)
    right_resolved = right.resolve(strict=False)
    return (
        left_resolved == right_resolved
        or left_resolved in right_resolved.parents
        or right_resolved in left_resolved.parents
    )


def _assert_no_alias_chain(path: Path) -> None:
    candidate = path
    while True:
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            if candidate.parent == candidate:
                return
            candidate = candidate.parent
            continue
        except OSError as exc:
            raise ValueError("path is unavailable") from exc
        if stat.S_ISLNK(metadata.st_mode) or _is_reparse(metadata):
            raise ValueError("path must not use symlink or reparse aliases")
        if candidate.parent == candidate:
            return
        candidate = candidate.parent


def _is_reparse(metadata: os.stat_result) -> bool:
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _validated_sha(value: str, *, field_name: str) -> str:
    if len(value) not in _SHA_PATTERN_LENGTHS:
        raise ValueError(f"{field_name} must be a 40- or 64-character lowercase SHA")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a 40- or 64-character lowercase SHA")
    return value


def _validated_state_id(value: str) -> str:
    if not value or any(character not in _SAFE_STATE_CHARS for character in value):
        raise ValueError("state directory name must be a safe state ID")
    return value


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _capsule_status(records: Sequence[PlaneRecord]) -> ResultStatus:
    if all(record.status is ResultStatus.PASS for record in records):
        return ResultStatus.PASS
    if any(record.status is ResultStatus.FAIL for record in records):
        return ResultStatus.FAIL
    return ResultStatus.BLOCKED


def _excluded_paths(capsule_root: Path) -> tuple[str, ...]:
    excluded: set[str] = set()
    for metadata_path in (
        capsule_root / "local-index" / "metadata.json",
        capsule_root / "local-tracked-worktree" / "metadata.json",
        capsule_root / "local-untracked-ignored" / "metadata.json",
    ):
        if not metadata_path.is_file():
            continue
        payload = _load_json_object(metadata_path)
        value = payload.get("secret_path_exclusions", [])
        if isinstance(value, list):
            excluded.update(str(item) for item in value)
    return tuple(sorted(excluded))


def _load_json_object(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("required local JSON artifact is unreadable") from exc
    if not isinstance(data, dict):
        raise ValueError("required local JSON artifact must be an object")
    return data


def _load_checkpoint(state_dir: Path) -> Checkpoint:
    try:
        return load_latest_checkpoint(state_dir / _CHECKPOINT_FILE)
    except Exception as exc:
        raise CheckpointIntegrityError(
            "checkpoint chain is unavailable or invalid"
        ) from exc


def _load_verification(state_dir: Path) -> VerificationRecord:
    path = state_dir / _CAPSULE_DIRNAME / _VERIFICATION_FILE
    if not path.is_file():
        raise ValueError("verification record is missing")
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ValueError("required local JSON artifact is unreadable") from exc
    return _verification_record_from_bytes(content)


def _verification_record_from_bytes(content: bytes) -> VerificationRecord:
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("required local JSON artifact is unreadable") from exc
    if not isinstance(data, dict):
        raise ValueError("required local JSON artifact must be an object")
    try:
        record = VerificationRecord(
            schema_version=str(data["schema_version"]),
            authentication=str(data["authentication"]),
            provenance_root=str(data["provenance_root"]),
            status=ResultStatus(str(data["status"])),
            checksum_status=ResultStatus(str(data["checksum_status"])),
            planes=tuple(_plane_restore_result(item) for item in data["planes"]),
            commit_match=_required_bool(data["commit_match"]),
            tree_match=_required_bool(data["tree_match"]),
            artifact_match=_required_bool(data["artifact_match"]),
            blockers=tuple(str(item) for item in data["blockers"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("verification record is malformed") from exc
    if content != canonical_json_bytes(record):
        raise ValueError("verification record is not canonical JSON")
    return record


def _plane_restore_result(value: object) -> PlaneRestoreResult:
    if not isinstance(value, dict):
        raise ValueError("verification plane record is malformed")
    return PlaneRestoreResult(
        plane_id=PlaneId(str(value["plane_id"])),
        subject_id=str(value["subject_id"]),
        status=ResultStatus(str(value["status"])),
        commit_match=_optional_bool(value.get("commit_match")),
        tree_match=_optional_bool(value.get("tree_match")),
        parent_match=_optional_bool(value.get("parent_match")),
        mode_path_match=_optional_bool(value.get("mode_path_match")),
        object_reachability=_optional_bool(value.get("object_reachability")),
        tree_id=_optional_str(value.get("tree_id")),
        parents_digest=_optional_str(value.get("parents_digest")),
        mode_path_digest=_optional_str(value.get("mode_path_digest")),
        evidence_digest=str(value["evidence_digest"]),
        artifact_digests=tuple(
            (str(name), str(digest)) for name, digest in value["artifact_digests"]
        ),
        artifact_match=_optional_bool(value.get("artifact_match")),
        payload_digest=_optional_str(value.get("payload_digest")),
        payload_count=_optional_int(value.get("payload_count")),
        blockers=tuple(str(item) for item in value["blockers"]),
    )


def _required_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError("boolean field is malformed")


def _optional_bool(value: object) -> bool | None:
    if value is None or isinstance(value, bool):
        return value
    raise ValueError("boolean field is malformed")


def _optional_str(value: object) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise ValueError("string field is malformed")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError("integer field is malformed")


def _verification_digest(path: Path) -> str:
    # Restore writes verification.json as canonical_json_bytes(record); hash that form.
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ValueError("required local JSON artifact is unreadable") from exc
    record = _verification_record_from_bytes(content)
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def _verification_authenticated(verification: VerificationRecord) -> bool:
    """Evidence is authentic and bound to the capsule, but may have
    design-ineligible planes (opaque/redacted).  Sufficient for inventory
    and render-github — those commands produce evidence artifacts, not
    containment decisions."""
    if not (
        verification.checksum_status is ResultStatus.PASS
        and verification.commit_match
        and verification.tree_match
        and verification.artifact_match
        and bool(verification.planes)
    ):
        return False
    # Blockers must all be from the design-ineligible set — not from
    # actual verification failures (which would be FAIL, not BLOCKED).
    _ineligible_only = {
        "opaque-preservation-ineligible",
        "redacted-evidence-ineligible",
        "excluded-evidence-ineligible",
    }
    if verification.blockers and not all(
        b in _ineligible_only for b in verification.blockers
    ):
        return False
    for plane in verification.planes:
        if plane.status is ResultStatus.FAIL:
            return False
        if plane.blockers and not all(
            b in _ineligible_only for b in plane.blockers
        ):
            return False
    return True


def _verification_releasable(verification: VerificationRecord) -> bool:
    """All planes PASS with zero blockers — required for containment."""
    return (
        verification.status is ResultStatus.PASS
        and verification.checksum_status is ResultStatus.PASS
        and verification.commit_match
        and verification.tree_match
        and verification.artifact_match
        and not verification.blockers
        and bool(verification.planes)
        and all(
            plane.status is ResultStatus.PASS and not plane.blockers
            for plane in verification.planes
        )
    )


def _copy_exact(source: Path, destination: Path) -> None:
    _write_bytes(destination, source.read_bytes())


def _write_bytes(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() == content:
            return
        raise ValueError("local output already exists with different content")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _without_action(values: Sequence[str], action: str) -> tuple[str, ...]:
    return tuple(value for value in values if value != action)


def _emit_json(value: object) -> None:
    sys.stdout.write(canonical_json_bytes(value).decode("utf-8"))


def _emit_error(message: str) -> None:
    sys.stderr.write(_sanitized_message(message) + "\n")


def _sanitized_message(message: str) -> str:
    rendered = str(message).replace("\\", "/")
    if ":/" in rendered or rendered.startswith("//"):
        return "local-only salvage command failed"
    return rendered
