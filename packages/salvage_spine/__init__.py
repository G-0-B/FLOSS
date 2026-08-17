"""Preserve-first contracts for the PR #38 salvage spine."""

from .models import (
    CapsuleRecord,
    PlaneEligibility,
    PlaneId,
    PlaneRecord,
    PlaneSensitivity,
    PlaneVerification,
    ResultStatus,
    canonical_json_bytes,
)
from .restore import PlaneRestoreResult, VerificationRecord, restore_and_verify
from .seal import CapsuleVerificationError, seal_capsule, verify_checksums

__all__ = [
    "CapsuleRecord",
    "CapsuleVerificationError",
    "PlaneEligibility",
    "PlaneId",
    "PlaneRecord",
    "PlaneRestoreResult",
    "PlaneSensitivity",
    "PlaneVerification",
    "ResultStatus",
    "VerificationRecord",
    "canonical_json_bytes",
    "restore_and_verify",
    "seal_capsule",
    "verify_checksums",
]

__version__ = "0.1.0"
