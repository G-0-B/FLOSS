"""Immutable data contracts shared by salvage-spine components."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import StrEnum
import json
from typing import Any


class ResultStatus(StrEnum):
    """Scoped result states; BLOCKED is intentionally not success."""

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    SKIPPED = "SKIPPED"


class PlaneId(StrEnum):
    """The six independently preserved source-state planes."""

    REMOTE_MAIN = "remote-main"
    REMOTE_PR = "remote-pr38"
    LOCAL_HISTORY = "local-history"
    LOCAL_INDEX = "local-index"
    LOCAL_TRACKED = "local-tracked"
    LOCAL_UNTRACKED = "local-untracked-ignored"


class PlaneSensitivity(StrEnum):
    """Whether a plane can be inspected as an ordinary projection artifact."""

    ORDINARY = "ordinary"
    OPAQUE_SENSITIVE = "opaque-sensitive"
    REDACTED = "redacted"


class PlaneEligibility(StrEnum):
    """Eligibility for ordinary projection or release."""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


class PlaneVerification(StrEnum):
    """The evidence available for a plane's mutable-byte identity."""

    BYTE_EQUALITY = "byte-equality"
    OPAQUE_PRESERVED = "opaque-preserved"
    UNVERIFIABLE_REDACTED = "unverifiable-redacted"


@dataclass(frozen=True)
class PlaneRecord:
    """Content identity for one captured source plane."""

    plane_id: PlaneId
    subject_id: str
    digest: str
    sensitivity: PlaneSensitivity = PlaneSensitivity.ORDINARY
    eligibility: PlaneEligibility = PlaneEligibility.ELIGIBLE
    verification: PlaneVerification = PlaneVerification.BYTE_EQUALITY
    status: ResultStatus = ResultStatus.PASS

    def __post_init__(self) -> None:
        """Prevent sensitive or unverifiable preservation from claiming success."""

        expected_verification = {
            PlaneSensitivity.ORDINARY: PlaneVerification.BYTE_EQUALITY,
            PlaneSensitivity.OPAQUE_SENSITIVE: PlaneVerification.OPAQUE_PRESERVED,
            PlaneSensitivity.REDACTED: PlaneVerification.UNVERIFIABLE_REDACTED,
        }[self.sensitivity]
        if self.verification is not expected_verification:
            raise ValueError("plane sensitivity and verification must agree")
        if self.sensitivity is not PlaneSensitivity.ORDINARY and (
            self.eligibility is not PlaneEligibility.INELIGIBLE
            or self.status is not ResultStatus.BLOCKED
        ):
            raise ValueError("sensitive planes must be blocked and ineligible")
        if self.sensitivity is PlaneSensitivity.ORDINARY and (
            self.eligibility is not PlaneEligibility.ELIGIBLE
            or self.status is not ResultStatus.PASS
        ):
            raise ValueError("ordinary planes must be passing and eligible")


@dataclass(frozen=True)
class CapsuleRecord:
    """Top-level metadata for a six-plane preservation capsule."""

    schema_version: str
    state_id: str
    repository: str
    captured_at: str
    planes: tuple[PlaneRecord, ...]
    exclusions: tuple[str, ...]
    status: ResultStatus

    def __post_init__(self) -> None:
        """Reject incomplete or ambiguous six-plane capsule metadata."""

        expected = set(PlaneId)
        actual = [
            record.plane_id for record in self.planes if isinstance(record, PlaneRecord)
        ]
        if (
            len(self.planes) != len(expected)
            or len(actual) != len(self.planes)
            or any(not isinstance(plane_id, PlaneId) for plane_id in actual)
            or len(set(actual)) != len(actual)
            or set(actual) != expected
        ):
            raise ValueError("planes must contain exactly one record for every PlaneId")


def canonical_json_bytes(value: object) -> bytes:
    """Serialize *value* as stable compact UTF-8 JSON plus one newline."""

    serializable: Any = asdict(value) if is_dataclass(value) else value
    rendered = json.dumps(
        serializable,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return (rendered + "\n").encode("utf-8")
