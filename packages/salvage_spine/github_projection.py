"""Sanitized GitHub-facing projections for PR38 preservation evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import unicodedata
from typing import Mapping
from urllib.parse import unquote

from .checkpoint import Checkpoint
from .manifest import _PROTECTED_LANES, manifest_digest, validate_manifest
from .models import PlaneId, ResultStatus, canonical_json_bytes
from .restore import PlaneRestoreResult, VerificationRecord

PRESERVATION_CHECK_NAME = "Preservation capsule — restore-tested evidence"
CORE_CHECK_NAME = "Core engineering checks — scoped evidence only"
_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "superpowers"
    / "templates"
    / "pr38-stop-merge-comment.md"
)
_TEMPLATE_KEYS = frozenset(
    {
        "readiness_line",
        "preservation_status",
        "preservation_title",
        "core_status",
        "core_title",
        "absolute_status",
        "regression_status",
        "remote_main_sha",
        "pr_head_sha",
        "capsule_root",
        "manifest_digest",
        "verification_digest",
        "unclassified_count",
        "hard_stop_count",
        "blockers_list",
        "next_safe_command",
        "checkpoint_sequence",
        "checkpoint_digest",
        "evidence_links",
    }
)
_STATUS_RANK = {
    ResultStatus.PASS: 0,
    ResultStatus.SKIPPED: 1,
    ResultStatus.BLOCKED: 2,
    ResultStatus.FAIL: 3,
}
_BIDI_AND_FORMAT = {
    "Cf",
}
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_PATH_RE = re.compile(
    r"(?i)(?:[a-z]:\\|\\\\[a-z0-9._$ -]+\\|/(?:users|home|root|var|tmp)/)"
)
_TOKEN_RE = re.compile(
    r"(?i)\b(?:bearer\s+\S+|(?:token|secret|password|credential|api[_-]?key)\s*[:=]\s*\S+)"
)
_UNSAFE_COMMAND_RE = re.compile(
    r"(?i)\b(?:gh|curl|invoke-webrequest|start-bitstransfer|merge|close|draft|push|reset|clean|stash|checkout|switch)\b"
)
_SAFE_COMMAND_RE = re.compile(r"[A-Za-z0-9._/\- =]+\Z")
_HEX_RE = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
_SCHEME_RE = re.compile(r"(?i)^[a-z][a-z0-9+.-]*://")
_LABEL_RE = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")
_URL_RE = re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://\S+")
_AUTOLINK_RE = re.compile(r"<[^>\n]+>")
_MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]\n]*\]\([^\)\n]*\)")
_PRIVATE_KEY_RE = re.compile(r"(?i)-{2,}\s*begin [a-z0-9 _-]*private key\s*-{2,}")
_SAFE_LOCATION_SEGMENT_RE = re.compile(r"[a-z0-9][a-z0-9._-]*\Z")
_SAFE_LOCATION_EXTENSIONS = frozenset({"json", "jsonl", "log", "md", "sha256", "txt"})
_EXPECTED_PLANE_IDS = tuple(PlaneId)


@dataclass(frozen=True)
class Evidence:
    """Scoped, local evidence used to render read-only GitHub projections."""

    verification: VerificationRecord
    checkpoint: Checkpoint
    manifest: dict[str, object]
    absolute_core_status: ResultStatus
    regression_core_status: ResultStatus
    evidence_locations: Mapping[str, str]


@dataclass(frozen=True)
class _PreparedEvidence:
    verification: VerificationRecord
    checkpoint: Checkpoint
    manifest: dict[str, object]
    preservation_status: ResultStatus
    core_status: ResultStatus
    absolute_core_status: ResultStatus
    regression_core_status: ResultStatus
    remote_main_sha: str
    pr_head_sha: str
    manifest_digest: str
    verification_digest: str | None
    computed_verification_digest: str
    unclassified_count: int
    hard_stop_count: int
    blockers: tuple[str, ...]
    next_safe_command: str
    evidence_locations: tuple[tuple[str, str], ...]


class ProjectionValidationError(ValueError):
    """Projection evidence is malformed, contradictory, or unsafe to render."""


def render_check_summary(evidence: Evidence) -> dict:
    """Render the scoped core-check projection for locked local evidence."""

    prepared = _prepare_evidence(evidence)
    title = (
        "Scoped core evidence: absolute "
        f"{prepared.absolute_core_status.value}; same-environment regression "
        f"{prepared.regression_core_status.value}."
    )
    preservation_title = (
        "Restore-tested local evidence is bound to locked inputs."
        if prepared.preservation_status is ResultStatus.PASS
        else "Restore-tested local evidence remains incomplete or blocked."
    )
    return {
        "name": CORE_CHECK_NAME,
        "status": prepared.core_status.value,
        "title": title,
        "preservation": {
            "name": PRESERVATION_CHECK_NAME,
            "status": prepared.preservation_status.value,
            "title": preservation_title,
        },
        "dimensions": {
            "absolute": {
                "status": prepared.absolute_core_status.value,
                "scope": "locked local evidence",
            },
            "same_environment_regression": {
                "status": prepared.regression_core_status.value,
                "scope": "same-environment regression evidence",
            },
        },
        "locked_shas": {
            "remote_main": prepared.remote_main_sha,
            "pr_head": prepared.pr_head_sha,
        },
        "digests": {
            "capsule_root": prepared.checkpoint.capsule_root,
            "manifest": prepared.manifest_digest,
            "verification": prepared.verification_digest,
        },
        "counts": {
            "unclassified": prepared.unclassified_count,
            "hard_stop": prepared.hard_stop_count,
        },
        "blockers": list(prepared.blockers),
        "next_safe_command": prepared.next_safe_command,
        "checkpoint": {
            "sequence": prepared.checkpoint.sequence,
            "digest": prepared.checkpoint.digest,
        },
        "evidence_locations": dict(prepared.evidence_locations),
    }


def render_stop_merge_comment(evidence: Evidence) -> str:
    """Render the proposed non-canonical stop-merge notice."""

    prepared = _prepare_evidence(evidence)
    template = _read_template()
    readiness = _readiness_line(prepared)
    replacements = {
        "readiness_line": readiness,
        "preservation_status": prepared.preservation_status.value,
        "preservation_title": (
            "Restore-tested local evidence is bound to locked inputs."
            if prepared.preservation_status is ResultStatus.PASS
            else "Restore-tested local evidence remains incomplete or blocked."
        ),
        "core_status": prepared.core_status.value,
        "core_title": (
            "Scoped core evidence is reported without global verification language."
        ),
        "absolute_status": prepared.absolute_core_status.value,
        "regression_status": prepared.regression_core_status.value,
        "remote_main_sha": prepared.remote_main_sha,
        "pr_head_sha": prepared.pr_head_sha,
        "capsule_root": prepared.checkpoint.capsule_root,
        "manifest_digest": prepared.manifest_digest,
        "verification_digest": prepared.verification_digest or "unbound",
        "unclassified_count": str(prepared.unclassified_count),
        "hard_stop_count": str(prepared.hard_stop_count),
        "blockers_list": _bullet_lines(prepared.blockers),
        "next_safe_command": prepared.next_safe_command,
        "checkpoint_sequence": str(prepared.checkpoint.sequence),
        "checkpoint_digest": prepared.checkpoint.digest or "unbound",
        "evidence_links": _render_links(prepared.evidence_locations),
    }
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    if "{{" in rendered or "}}" in rendered:
        raise ValueError("template placeholders do not match renderer contract")
    return rendered


def _prepare_evidence(evidence: Evidence) -> _PreparedEvidence:
    if not isinstance(evidence, Evidence):
        raise TypeError("evidence must be an Evidence")
    if not isinstance(evidence.verification, VerificationRecord):
        raise ProjectionValidationError("verification must be a VerificationRecord")
    if not isinstance(evidence.checkpoint, Checkpoint):
        raise ProjectionValidationError("checkpoint must be a Checkpoint")
    for field_name, value in (
        ("absolute_core_status", evidence.absolute_core_status),
        ("regression_core_status", evidence.regression_core_status),
        ("verification.status", evidence.verification.status),
    ):
        if not isinstance(value, ResultStatus):
            raise ProjectionValidationError(f"{field_name} must be a ResultStatus")
    if not isinstance(evidence.manifest, dict):
        raise ProjectionValidationError("manifest must be an object")

    manifest_errors = validate_manifest(evidence.manifest)
    if manifest_errors:
        raise ProjectionValidationError("manifest evidence is invalid")
    computed_manifest_digest = manifest_digest(evidence.manifest)
    if evidence.checkpoint.manifest_digest != computed_manifest_digest:
        raise ProjectionValidationError(
            "manifest digest does not match checkpoint binding"
        )
    manifest_state_id = evidence.manifest.get("state_id")
    if evidence.checkpoint.state_id != manifest_state_id:
        raise ProjectionValidationError("manifest state_id does not match checkpoint")
    manifest_capsule_root = evidence.manifest.get("capsule_root")
    if evidence.checkpoint.capsule_root != manifest_capsule_root:
        raise ProjectionValidationError(
            "manifest capsule_root does not match checkpoint"
        )

    computed_verification_digest = hashlib.sha256(
        canonical_json_bytes(evidence.verification)
    ).hexdigest()
    if evidence.checkpoint.capsule_root != evidence.verification.provenance_root:
        raise ProjectionValidationError(
            "capsule root does not match verification provenance root"
        )
    if evidence.checkpoint.verification_digest not in {
        None,
        computed_verification_digest,
    }:
        raise ProjectionValidationError(
            "verification digest does not match verification payload"
        )
    _validate_verification_record(evidence.verification)

    remote_main_sha = _require_sha(
        evidence.checkpoint.input_shas.get("remote_main"),
        "checkpoint.input_shas.remote_main",
    )
    pr_head_sha = _require_sha(
        evidence.checkpoint.input_shas.get("pr_head"),
        "checkpoint.input_shas.pr_head",
    )
    next_safe_command = _sanitize_command(evidence.checkpoint.next_safe_command)
    evidence_locations = _normalize_locations(evidence.evidence_locations)
    blockers = _combined_blockers(evidence)
    unclassified_count = _unclassified_count(evidence.manifest)
    hard_stop_count = _hard_stop_count(evidence.manifest)
    if unclassified_count:
        blockers.add("unclassified-items-pending")
    if hard_stop_count:
        blockers.add("protected-lane-work-pending")

    preservation_status = _preservation_status(evidence, computed_verification_digest)
    core_status = _combine_statuses(
        evidence.absolute_core_status,
        evidence.regression_core_status,
    )
    if preservation_status in {ResultStatus.FAIL, ResultStatus.BLOCKED}:
        blockers.add(
            "restore-check-failed"
            if preservation_status is ResultStatus.FAIL
            else "restore-check-blocked"
        )
    elif evidence.checkpoint.verification_digest is None:
        blockers.add("verification-digest-unbound")

    return _PreparedEvidence(
        verification=evidence.verification,
        checkpoint=evidence.checkpoint,
        manifest=evidence.manifest,
        preservation_status=preservation_status,
        core_status=core_status,
        absolute_core_status=evidence.absolute_core_status,
        regression_core_status=evidence.regression_core_status,
        remote_main_sha=remote_main_sha,
        pr_head_sha=pr_head_sha,
        manifest_digest=computed_manifest_digest,
        verification_digest=evidence.checkpoint.verification_digest,
        computed_verification_digest=computed_verification_digest,
        unclassified_count=unclassified_count,
        hard_stop_count=hard_stop_count,
        blockers=tuple(sorted(blockers, key=lambda item: item.encode("utf-8"))),
        next_safe_command=next_safe_command,
        evidence_locations=evidence_locations,
    )


def _preservation_status(
    evidence: Evidence,
    computed_verification_digest: str,
) -> ResultStatus:
    if evidence.checkpoint.blockers or evidence.verification.blockers:
        return ResultStatus.BLOCKED
    if _unclassified_count(evidence.manifest) or _hard_stop_count(evidence.manifest):
        return ResultStatus.BLOCKED
    if evidence.verification.status is ResultStatus.FAIL:
        return ResultStatus.FAIL
    if evidence.verification.status in {ResultStatus.BLOCKED, ResultStatus.SKIPPED}:
        return ResultStatus.BLOCKED
    if evidence.verification.checksum_status is not ResultStatus.PASS:
        return ResultStatus.FAIL
    if not (
        evidence.verification.commit_match
        and evidence.verification.tree_match
        and evidence.verification.artifact_match
    ):
        return ResultStatus.FAIL
    plane_statuses = {plane.status for plane in evidence.verification.planes}
    if ResultStatus.FAIL in plane_statuses:
        return ResultStatus.FAIL
    if plane_statuses != {ResultStatus.PASS}:
        return ResultStatus.BLOCKED
    if any(plane.blockers for plane in evidence.verification.planes):
        return ResultStatus.BLOCKED
    if evidence.checkpoint.verification_digest != computed_verification_digest:
        return ResultStatus.BLOCKED
    return ResultStatus.PASS


def _combine_statuses(*statuses: ResultStatus) -> ResultStatus:
    return max(statuses, key=lambda status: _STATUS_RANK[status])


def _unclassified_count(manifest: dict[str, object]) -> int:
    items = manifest.get("items")
    if not isinstance(items, list):
        raise ValueError("manifest items must be an array")
    return sum(
        1
        for item in items
        if isinstance(item, dict) and item.get("classification_state") == "captured"
    )


def _hard_stop_count(manifest: dict[str, object]) -> int:
    items = manifest.get("items")
    if not isinstance(items, list):
        raise ValueError("manifest items must be an array")
    return sum(
        1
        for item in items
        if isinstance(item, dict) and item.get("primary_lane") in _PROTECTED_LANES
    )


def _combined_blockers(evidence: Evidence) -> set[str]:
    combined = set()
    for raw in tuple(evidence.verification.blockers) + tuple(
        evidence.checkpoint.blockers
    ):
        sanitized = _sanitize_text(raw)
        if sanitized:
            combined.add(sanitized)
    return combined


def _sanitize_text(value: object) -> str:
    if not isinstance(value, str):
        raise ProjectionValidationError("rendered text inputs must be strings")
    normalized = _normalize_unsafe_scalar(value)
    if _contains_unsafe_text(normalized):
        return "[redacted-unsafe-text]"
    normalized = _CONTROL_RE.sub(" ", normalized)
    normalized = "".join(
        (
            " "
            if unicodedata.category(character) in _BIDI_AND_FORMAT
            or character in "<>[](){}|`"
            else character
        )
        for character in normalized
    )
    normalized = _TOKEN_RE.sub("[redacted-secret]", normalized)
    normalized = _PATH_RE.sub("[redacted-path]", normalized)
    normalized = re.sub(
        r"(?i)\b(?:gh|curl|invoke-webrequest)\b.*", "[redacted-unsafe-text]", normalized
    )
    normalized = normalized.replace("://", " ")
    normalized = " ".join(normalized.split())
    return normalized.strip() or "[redacted-unsafe-text]"


def _sanitize_command(value: object) -> str:
    if not isinstance(value, str):
        raise ProjectionValidationError("next_safe_command must be a string")
    normalized = _normalize_unsafe_scalar(value)
    if (
        _contains_unsafe_text(normalized)
        or _SCHEME_RE.match(normalized)
        or _PATH_RE.search(normalized)
        or "?" in normalized
        or "#" in normalized
        or "%" in normalized
    ):
        raise ProjectionValidationError(
            "next_safe_command must not contain remote or absolute paths"
        )
    if _UNSAFE_COMMAND_RE.search(value):
        raise ProjectionValidationError(
            "next_safe_command contains an unsafe or mutating command"
        )
    if not _SAFE_COMMAND_RE.fullmatch(normalized):
        raise ProjectionValidationError(
            "next_safe_command contains unsupported characters"
        )
    return _sanitize_text(normalized)


def _normalize_locations(locations: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for label, location in sorted(locations.items(), key=lambda item: item[0]):
        if not isinstance(label, str) or not _LABEL_RE.fullmatch(label):
            raise ProjectionValidationError("evidence location label is invalid")
        normalized.append((label, _sanitize_location(location)))
    if not normalized:
        raise ProjectionValidationError("at least one evidence location is required")
    return tuple(normalized)


def _sanitize_location(location: object) -> str:
    if not isinstance(location, str):
        raise ProjectionValidationError("evidence location must be a string")
    normalized = _normalize_unsafe_scalar(location)
    if _contains_unsafe_text(normalized):
        raise ProjectionValidationError("evidence location scheme is unsafe")
    if any(
        token in normalized
        for token in (
            "#",
            "?",
            "@",
            "://",
            "`",
            "<",
            ">",
            "[",
            "]",
            "(",
            ")",
            "!",
            "'",
            '"',
        )
    ):
        raise ProjectionValidationError("evidence location path is unsafe")
    if "\\" in normalized or "\\\\" in normalized or _PATH_RE.search(normalized):
        raise ProjectionValidationError(
            "evidence location must be relative and non-private"
        )
    if ":" in normalized:
        raise ProjectionValidationError("evidence location path is unsafe")
    if "%" in normalized:
        raise ProjectionValidationError("evidence location path is unsafe")
    path = PurePosixPath(normalized)
    windows_path = PureWindowsPath(normalized)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or any(part in {".", ".."} for part in path.parts)
        or not normalized
        or normalized != path.as_posix()
    ):
        raise ProjectionValidationError("evidence location path is unsafe")
    if any(not _SAFE_LOCATION_SEGMENT_RE.fullmatch(part) for part in path.parts):
        raise ProjectionValidationError("evidence location path is unsafe")
    suffix = path.suffix.lower().lstrip(".")
    if suffix not in _SAFE_LOCATION_EXTENSIONS:
        raise ProjectionValidationError("evidence location extension is unsafe")
    return normalized


def _require_sha(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not _HEX_RE.fullmatch(value):
        raise ProjectionValidationError(
            f"{field_name} must be a locked lowercase digest"
        )
    return value


def _read_template() -> str:
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    placeholders = set(re.findall(r"\{\{([a-z0-9_]+)\}\}", template))
    if placeholders != _TEMPLATE_KEYS:
        raise ProjectionValidationError(
            "template placeholders do not match renderer contract"
        )
    lowered = template.lower()
    if "gh pr" in lowered or "curl " in lowered or "invoke-webrequest" in lowered:
        raise ProjectionValidationError("template contains remote API commands")
    return template


def _readiness_line(prepared: _PreparedEvidence) -> str:
    ready = (
        prepared.preservation_status is ResultStatus.PASS
        and prepared.absolute_core_status is ResultStatus.PASS
        and prepared.regression_core_status is ResultStatus.PASS
        and prepared.unclassified_count == 0
        and prepared.hard_stop_count == 0
        and not prepared.blockers
    )
    if ready:
        return (
            "PRESERVATION PASSED ON LOCKED LOCAL EVIDENCE. "
            "Containment still requires explicit human authorization."
        )
    return (
        "NOT READY FOR CONTAINMENT. "
        "Scoped evidence remains incomplete, blocked, or not fully classified."
    )


def _bullet_lines(values: tuple[str, ...]) -> str:
    if not values:
        return "- none"
    return "\n".join(f"- {value}" for value in values)


def _render_links(locations: tuple[tuple[str, str], ...]) -> str:
    return "\n".join(
        f"- {label.replace('_', ' ').title()}: [{location}]({location})"
        for label, location in locations
    )


def _normalize_unsafe_scalar(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    for _ in range(4):
        decoded = unquote(normalized)
        decoded = unicodedata.normalize("NFKC", decoded)
        if decoded == normalized:
            break
        normalized = decoded
    return normalized


def _contains_unsafe_text(value: str) -> bool:
    return bool(
        _URL_RE.search(value)
        or _AUTOLINK_RE.search(value)
        or _MARKDOWN_LINK_RE.search(value)
        or _PRIVATE_KEY_RE.search(value)
        or _CONTROL_RE.search(value)
        or _SCHEME_RE.match(value)
    )


def _validate_verification_record(verification: VerificationRecord) -> None:
    if not isinstance(verification.checksum_status, ResultStatus):
        raise ProjectionValidationError(
            "verification.checksum_status must be a ResultStatus"
        )
    _require_exact_bool(verification.commit_match, "verification.commit_match")
    _require_exact_bool(verification.tree_match, "verification.tree_match")
    _require_exact_bool(verification.artifact_match, "verification.artifact_match")
    if not isinstance(verification.planes, tuple):
        raise ProjectionValidationError("verification planes must be a tuple")

    seen: set[PlaneId] = set()
    for plane in verification.planes:
        if not isinstance(plane, PlaneRestoreResult):
            raise ProjectionValidationError(
                "verification plane must be a PlaneRestoreResult"
            )
        if not isinstance(plane.plane_id, PlaneId):
            raise ProjectionValidationError("verification plane_id is invalid")
        if plane.plane_id in seen:
            raise ProjectionValidationError("verification plane_id is duplicated")
        seen.add(plane.plane_id)
        if not isinstance(plane.status, ResultStatus):
            raise ProjectionValidationError("verification plane status is invalid")
        if not isinstance(plane.blockers, tuple):
            raise ProjectionValidationError("verification plane blockers are invalid")
        if any(not isinstance(blocker, str) for blocker in plane.blockers):
            raise ProjectionValidationError("verification plane blockers are invalid")
    if tuple(sorted(seen, key=lambda plane_id: plane_id.value)) != tuple(
        sorted(_EXPECTED_PLANE_IDS, key=lambda plane_id: plane_id.value)
    ):
        raise ProjectionValidationError("verification plane set is incomplete")


def _require_exact_bool(value: object, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ProjectionValidationError(f"{field_name} must be a bool")


__all__ = [
    "CORE_CHECK_NAME",
    "Evidence",
    "PRESERVATION_CHECK_NAME",
    "render_check_summary",
    "render_stop_merge_comment",
]
