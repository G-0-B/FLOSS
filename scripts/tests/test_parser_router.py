"""
Unit tests for FLOSS/scripts/parser_router.py.
Verifies format routing, quarantine enforcement, and verified DocumentIR production.
Part of Phase 1 (Task 1.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rights_envelope import RightsEnvelope
from parser_router import ParserRouter


def test_parse_markdown_text():
    router = ParserRouter()
    content = "# Chapter 1: Foundations\n\nStigmergy enables decentralized swarm coordination.\n\n# Chapter 2: Methods"
    raw_bytes = content.encode("utf-8")
    
    doc_ir, disposition = router.parse_bytes(
        raw_bytes=raw_bytes,
        filename="notes.md",
        ext=".md"
    )
    
    assert disposition.sandbox_status == "CLEARED"
    assert len(doc_ir.blocks) == 3
    assert doc_ir.blocks[0].kind == "heading"
    assert doc_ir.blocks[1].kind == "paragraph"
    assert "Stigmergy enables" in doc_ir.canonical_text
    
    valid, errors = doc_ir.verify_integrity()
    assert valid, f"Integrity failed: {errors}"


def test_quarantine_rejection_on_file():
    router = ParserRouter()
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
        f.write(b"malicious payload")
        temp_path = f.name
        
    try:
        with pytest.raises(PermissionError) as exc_info:
            router.parse_file(temp_path)
        assert "quarantined by security policy" in str(exc_info.value)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_rights_envelope_rejection():
    router = ParserRouter()
    env = RightsEnvelope(
        raw_artifact_sha256="abc",
        local_processing_permitted=False
    )
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Controlled internal memo")
        temp_path = f.name
        
    try:
        with pytest.raises(PermissionError) as exc_info:
            router.parse_file(temp_path, rights_envelope=env)
        assert "quarantined by security policy" in str(exc_info.value)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_parse_synthetic_pdf():
    import fitz  # PyMuPDF
    # Create a small 1-page PDF
    pdf_doc = fitz.open()
    page = pdf_doc.new_page(width=595, height=842)
    page.insert_text((50, 72), "SCIENTIFIC MEMORANDUM:", fontsize=14)
    page.insert_text((50, 110), "Cellular apoptosis increases under elevated oxidative stress in cortical assays.", fontsize=11)
    
    pdf_bytes = pdf_doc.write()
    pdf_doc.close()
    
    router = ParserRouter()
    doc_ir, disposition = router.parse_bytes(
        raw_bytes=pdf_bytes,
        filename="memo.pdf",
        ext=".pdf"
    )
    
    assert disposition.sandbox_status == "CLEARED"
    assert len(doc_ir.blocks) >= 1
    assert "apoptosis" in doc_ir.canonical_text
    
    valid, errors = doc_ir.verify_integrity()
    assert valid, f"PDF DocumentIR failed integrity: {errors}"
