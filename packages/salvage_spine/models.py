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
    sensitivity: PlaneSensitivity
    eligibility: PlaneEligibility
    verification: PlaneVerification
    status: ResultStatus

    def __post_init__(self) -> None:
        """Prevent sensitive or unverifiable preservation from claiming success."""

        if not isinstance(self.plane_id, PlaneId):
            raise ValueError("plane_id must be a PlaneId")
        disposition_types = (
            ("sensitivity", self.sensitivity, PlaneSensitivity),
            ("eligibility", self.eligibility, PlaneEligibility),
            ("verification", self.verification, PlaneVerification),
            ("status", self.status, ResultStatus),
        )
        for field_name, value, expected_type in disposition_types:
            if not isinstance(value, expected_type):
                raise ValueError(f"{field_name} must be a {expected_type.__name__}")
        disposition = (
            self.sensitivity,
            self.eligibility,
            self.verification,
            self.status,
        )
        opaque_disposition = (
            PlaneSensitivity.OPAQUE_SENSITIVE,
            PlaneEligibility.INELIGIBLE,
            PlaneVerification.OPAQUE_PRESERVED,
            ResultStatus.BLOCKED,
        )
        ordinary_disposition = (
            PlaneSensitivity.ORDINARY,
            PlaneEligibility.ELIGIBLE,
            PlaneVerification.BYTE_EQUALITY,
            ResultStatus.PASS,
        )
        redacted_disposition = (
            PlaneSensitivity.REDACTED,
            PlaneEligibility.INELIGIBLE,
            PlaneVerification.UNVERIFIABLE_REDACTED,
            ResultStatus.BLOCKED,
        )
        opaque_planes = {
            PlaneId.REMOTE_MAIN,
            PlaneId.REMOTE_PR,
            PlaneId.LOCAL_HISTORY,
            PlaneId.LOCAL_INDEX,
        }
        if self.plane_id in opaque_planes:
            if disposition != opaque_disposition:
                raise ValueError(
                    "inherently opaque planes require opaque, ineligible, "
                    "preserved, BLOCKED disposition"
                )
        elif disposition not in {ordinary_disposition, redacted_disposition}:
            raise ValueError(
                "local mutable planes require ordinary byte-equality PASS or "
                "redacted unverifiable BLOCKED disposition"
            )


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

        if not isinstance(self.status, ResultStatus):
            raise ValueError("status must be a ResultStatus")
        if any(not isinstance(record, PlaneRecord) for record in self.planes):
            raise ValueError("planes must contain exactly one record for every PlaneId")
        for record in self.planes:
            PlaneRecord.__post_init__(record)
        expected = set(PlaneId)
        actual = [record.plane_id for record in self.planes]
        if (
            len(self.planes) != len(expected)
            or any(not isinstance(plane_id, PlaneId) for plane_id in actual)
            or len(set(actual)) != len(actual)
            or set(actual) != expected
        ):
            raise ValueError("planes must contain exactly one record for every PlaneId")
        if self.status is ResultStatus.PASS and any(
            plane.status is not ResultStatus.PASS
            or plane.eligibility is not PlaneEligibility.ELIGIBLE
            for plane in self.planes
        ):
            raise ValueError(
                "capsule PASS requires every plane to PASS and be eligible"
            )


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
