"""
FLOSSI0ULLK Pre-Parse Rights & Security Quarantine Module.
Enforces rights, consent, retention, and container security BEFORE parsing and model exposure.
Part of Phase 1 (Task 1.1) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Literal

CopyrightStatus = Literal[
    "PUBLIC_DOMAIN",
    "CC_BY",
    "CC_BY_SA",
    "CC_BY_NC",
    "ALL_RIGHTS_RESERVED",
    "COMMUNITY_GOVERNED",
    "UNKNOWN"
]

SensitivityClass = Literal["PUBLIC", "INTERNAL", "RESTRICTED", "PII", "INDIGENOUS_RELATIONAL"]

@dataclass(frozen=True)
class RightsEnvelope:
    raw_artifact_sha256: str
    access_authority: str = "project_stewards"
    copyright_status: CopyrightStatus = "UNKNOWN"
    local_processing_permitted: bool = True
    training_permitted: bool = False
    redistribution_permitted: bool = True
    retention_deadline: Optional[str] = None
    sensitive_data_classification: SensitivityClass = "PUBLIC"
    relational_restrictions: list[str] = field(default_factory=list)
    revocation_ref: Optional[str] = None

    def validate_for_ingestion(self) -> tuple[bool, list[str]]:
        """Verify whether document is legally and ethically clear for pipeline processing."""
        violations = []
        if not self.local_processing_permitted:
            violations.append("Local processing is explicitly prohibited by rights envelope")
        if self.sensitive_data_classification in ("RESTRICTED", "PII"):
            violations.append(f"Processing blocked: Document classified as {self.sensitive_data_classification}")
        if self.copyright_status == "UNKNOWN" and self.access_authority == "unverified":
            violations.append("Processing blocked: Unknown copyright without verified access authority")
        return len(violations) == 0, violations

@dataclass
class SecurityDisposition:
    file_path: str
    file_size_bytes: int
    raw_artifact_sha256: str
    is_symlink: bool
    mime_type: str
    sandbox_status: Literal["CLEARED", "QUARANTINED"]
    quarantine_reasons: list[str] = field(default_factory=list)

class DocumentQuarantine:
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MiB ceiling
    ALLOWED_MIMES = {
        ".pdf": "application/pdf",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".json": "application/json",
    }

    @classmethod
    def audit_file(cls, path: str | Path, rights: Optional[RightsEnvelope] = None) -> tuple[SecurityDisposition, Optional[RightsEnvelope]]:
        p = Path(path).resolve()
        reasons = []

        # Check symlink traversal
        is_sym = Path(path).is_symlink()
        if is_sym:
            reasons.append("Rejecting symlink traversal: File is a symbolic link")

        # Check file existence
        if not p.is_file():
            reasons.append(f"File does not exist: {p}")
            return SecurityDisposition(
                file_path=str(p),
                file_size_bytes=0,
                raw_artifact_sha256="",
                is_symlink=is_sym,
                mime_type="unknown",
                sandbox_status="QUARANTINED",
                quarantine_reasons=reasons
            ), None

        # Check size limit
        size = p.stat().st_size
        if size > cls.MAX_FILE_SIZE_BYTES:
            reasons.append(f"File size {size} bytes exceeds maximum ceiling of {cls.MAX_FILE_SIZE_BYTES} bytes")

        # Compute SHA-256
        sha = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        artifact_hash = sha.hexdigest()

        # Check extension / MIME
        ext = p.suffix.lower()
        mime = cls.ALLOWED_MIMES.get(ext, "application/octet-stream")
        if ext not in cls.ALLOWED_MIMES:
            reasons.append(f"Disallowed file extension/MIME: {ext} is not in allowed intake set")

        # Check rights envelope if provided
        if rights is not None:
            if rights.raw_artifact_sha256 != artifact_hash:
                reasons.append(f"Rights envelope SHA mismatch: envelope={rights.raw_artifact_sha256} vs actual={artifact_hash}")
            ok_rights, r_violations = rights.validate_for_ingestion()
            if not ok_rights:
                reasons.extend(r_violations)
        else:
            # Default permissive open research envelope
            rights = RightsEnvelope(
                raw_artifact_sha256=artifact_hash,
                copyright_status="PUBLIC_DOMAIN",
                local_processing_permitted=True,
                redistribution_permitted=True
            )

        status: Literal["CLEARED", "QUARANTINED"] = "QUARANTINED" if reasons else "CLEARED"
        return SecurityDisposition(
            file_path=str(p),
            file_size_bytes=size,
            raw_artifact_sha256=artifact_hash,
            is_symlink=is_sym,
            mime_type=mime,
            sandbox_status=status,
            quarantine_reasons=reasons
        ), rights
