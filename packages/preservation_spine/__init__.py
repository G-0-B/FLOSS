"""Preserve-first contracts for the repository preservation spine.

Six-plane capture (remote base, remote PR head, local commits, index,
tracked worktree, untracked/ignored inventory), sealed capsules, clean-room
restore, and scoped evidence rendering. Originated in the 2026-07 PR38
salvage; the contract is general to any risky repository operation.
"""

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
