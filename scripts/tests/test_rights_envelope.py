"""
Unit tests for FLOSS/scripts/rights_envelope.py.
Tests RightsEnvelope validation, DocumentQuarantine limits, symlink detection, and rights checking.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rights_envelope import RightsEnvelope, DocumentQuarantine, SecurityDisposition

def test_rights_envelope_validation():
    # Valid envelope
    env = RightsEnvelope(
        raw_artifact_sha256="abc123",
        copyright_status="CC_BY",
        local_processing_permitted=True,
        sensitive_data_classification="PUBLIC"
    )
    ok, violations = env.validate_for_ingestion()
    assert ok is True
    assert violations == []

    # Prohibited local processing
    env_prohibited = RightsEnvelope(
        raw_artifact_sha256="abc123",
        local_processing_permitted=False
    )
    ok, violations = env_prohibited.validate_for_ingestion()
    assert ok is False
    assert any("prohibited" in v for v in violations)

    # Restricted PII data
    env_pii = RightsEnvelope(
        raw_artifact_sha256="abc123",
        sensitive_data_classification="PII"
    )
    ok, violations = env_pii.validate_for_ingestion()
    assert ok is False
    assert any("PII" in v for v in violations)

def test_document_quarantine_valid_file():
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        f.write(b"# Test Document\n\nSome content.")
        temp_path = f.name

    try:
        disp, env = DocumentQuarantine.audit_file(temp_path)
        assert disp.sandbox_status == "CLEARED"
        assert disp.mime_type == "text/markdown"
        assert disp.is_symlink is False
        assert len(disp.raw_artifact_sha256) == 64
        assert env is not None
        assert env.raw_artifact_sha256 == disp.raw_artifact_sha256
    finally:
        os.remove(temp_path)

def test_document_quarantine_nonexistent_file():
    disp, env = DocumentQuarantine.audit_file("nonexistent_file_path_12345.md")
    assert disp.sandbox_status == "QUARANTINED"
    assert any("does not exist" in r for r in disp.quarantine_reasons)
    assert env is None

def test_document_quarantine_disallowed_extension():
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
        f.write(b"fake binary")
        temp_path = f.name

    try:
        disp, env = DocumentQuarantine.audit_file(temp_path)
        assert disp.sandbox_status == "QUARANTINED"
        assert any("Disallowed file extension" in r for r in disp.quarantine_reasons)
    finally:
        os.remove(temp_path)
