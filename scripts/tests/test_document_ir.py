"""
Unit tests for FLOSSI0ULLK DocumentIR & TransformMap.
Verifies layout-aware block representation, coordinate provenance, and invertible transformation replay.
Part of Phase 1 (Task 1.2) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import hashlib
import sys
import unicodedata
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from document_ir import (
    Block,
    TransformMap,
    DocumentIR,
    build_canonical_document_ir
)


def test_block_serialization_and_hash():
    text = "Cortical neurons exhibit apoptosis under stress."
    slice_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    block = Block(
        block_id="blk-001",
        page_num=1,
        kind="paragraph",
        bbox=(50.0, 100.0, 450.0, 150.0),
        char_range=(0, len(text)),
        raw_slice_hash=slice_hash,
        text=text
    )
    
    d = block.to_dict()
    assert d["block_id"] == "blk-001"
    assert d["page_num"] == 1
    assert d["kind"] == "paragraph"
    assert d["bbox"] == [50.0, 100.0, 450.0, 150.0]
    assert d["char_range"] == [0, len(text)]
    assert d["raw_slice_hash"] == slice_hash
    assert d["text"] == text
    
    recovered = Block.from_dict(d)
    assert recovered == block


def test_transform_map_offsets():
    # Simulate a hyphen break merge at canonical offset 20
    # Before offset 20: identity [0, 0]
    # At raw index 20: 'co-\n' (4 chars) merged into 'co' (2 chars) -> canonical loses 2 chars
    # Anchor point: canonical offset 22 corresponds to raw offset 24
    t_map = TransformMap(
        canonical_to_raw_char=[[0, 0], [22, 24]],
        transform_steps=["hyphen_break_merge"],
        implementation_hash="test-v1"
    )
    
    # Offsets before merge
    assert t_map.map_canonical_offset(10) == 10
    assert t_map.map_raw_offset(10) == 10
    
    # Offsets at anchor
    assert t_map.map_canonical_offset(22) == 24
    assert t_map.map_raw_offset(24) == 22
    
    # Offsets after anchor
    assert t_map.map_canonical_offset(30) == 32
    assert t_map.map_raw_offset(32) == 30
    
    # Span mapping
    assert t_map.map_canonical_span(5, 30) == (5, 32)


def test_build_canonical_document_ir_with_nfc_and_hyphenation():
    raw_bytes = b"Raw dummy PDF or text container content"
    # Create text with decomposed unicode (e + combining acute) and hyphen break
    decomposed_e = "e\u0301"  # NFD: 2 code points
    raw_text = f"The compo-\nund exhibits activit{decomposed_e} in cortical assays."
    
    raw_blocks = [
        {
            "block_id": "blk-p1-01",
            "page_num": 1,
            "kind": "paragraph",
            "bbox": [10.0, 20.0, 300.0, 100.0],
            "raw_char_range": [0, len(raw_text)]
        }
    ]
    
    doc_ir = build_canonical_document_ir(
        raw_bytes=raw_bytes,
        decoded_text=raw_text,
        raw_blocks=raw_blocks,
        parser_metadata={"parser_id": "docling", "version": "2.0.1"},
        merge_hyphen_breaks=True
    )
    
    # Verify hyphen break was merged: "compo-\nund" -> "compound"
    assert "compound" in doc_ir.canonical_text
    assert "compo-\nund" not in doc_ir.canonical_text
    
    # Verify NFC normalization: 'e\u0301' -> 'é' (U+00E9, 1 code point)
    assert "\u00e9" in doc_ir.canonical_text
    
    # Verify integrity
    valid, errors = doc_ir.verify_integrity()
    assert valid, f"Integrity check failed: {errors}"
    
    # Check slice extraction
    c_slice = doc_ir.get_canonical_slice(4, 12)
    assert c_slice == "compound"
    
    # Check block query
    blocks = doc_ir.get_blocks_for_canonical_span(4, 12)
    assert len(blocks) == 1
    assert blocks[0].block_id == "blk-p1-01"


def test_document_ir_json_roundtrip():
    raw_bytes = b"Sample document"
    text = "Section 1: Introduction\nThis is a test paragraph."
    raw_blocks = [
        {
            "block_id": "b-0",
            "page_num": 1,
            "kind": "heading",
            "bbox": [0.0, 0.0, 100.0, 20.0],
            "char_range": [0, 23]
        },
        {
            "block_id": "b-1",
            "page_num": 1,
            "kind": "paragraph",
            "bbox": [0.0, 25.0, 500.0, 60.0],
            "char_range": [24, len(text)]
        }
    ]
    
    doc_ir = build_canonical_document_ir(
        raw_bytes=raw_bytes,
        decoded_text=text,
        raw_blocks=raw_blocks,
        parser_metadata={"parser_id": "test_parser", "version": "1.0"},
        merge_hyphen_breaks=False
    )
    
    json_str = doc_ir.to_json()
    recovered = DocumentIR.from_json(json_str)
    
    assert recovered.raw_artifact_sha256 == doc_ir.raw_artifact_sha256
    assert recovered.canonical_text_sha256 == doc_ir.canonical_text_sha256
    assert len(recovered.blocks) == len(doc_ir.blocks)
    assert recovered.blocks[0].block_id == "b-0"
    assert recovered.blocks[1].block_id == "b-1"
    
    valid, errors = recovered.verify_integrity()
    assert valid, f"Recovered integrity failed: {errors}"


def test_document_ir_tamper_detection():
    raw_bytes = b"Legitimate bytes"
    text = "Original honest statement."
    raw_blocks = [
        {
            "block_id": "b-0",
            "page_num": 1,
            "kind": "paragraph",
            "bbox": [0.0, 0.0, 100.0, 50.0],
            "char_range": [0, len(text)]
        }
    ]
    
    doc_ir = build_canonical_document_ir(
        raw_bytes=raw_bytes,
        decoded_text=text,
        raw_blocks=raw_blocks
    )
    
    # Tamper with canonical text
    doc_ir.canonical_text = "Tampered malicious statement."
    valid, errors = doc_ir.verify_integrity()
    assert not valid
    assert any("Canonical text SHA256 mismatch" in e for e in errors)
