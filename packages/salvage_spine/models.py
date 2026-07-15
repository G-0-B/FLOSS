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


@dataclass(frozen=True)
class PlaneRecord:
    """Content identity for one captured source plane."""

    plane_id: PlaneId
    subject_id: str
    digest: str


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
            record.plane_id
            for record in self.planes
            if isinstance(record, PlaneRecord)
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
