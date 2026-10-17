"""
FLOSSI0ULLK Document Ingestion Substrate Module.
Defines DocumentIR (Canonical Intermediate Representation) and TransformMap.
Enforces layout-aware block representation, coordinate provenance, and invertible transformation replay.
Part of Phase 1 (Task 1.2) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Literal, Sequence

BlockKind = Literal[
    "paragraph",
    "heading",
    "table",
    "caption",
    "figure",
    "equation",
    "metadata",
    "code",
    "list_item"
]

@dataclass(frozen=True)
class Block:
    """A layout-grounded structural unit within a document."""
    block_id: str
    page_num: int
    kind: BlockKind
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    char_range: tuple[int, int]  # zero-based, half-open [start, end) in canonical_text
    raw_slice_hash: str  # sha256 hex digest of canonical_text[start:end] encoded in UTF-8
    text: str = ""  # optional literal content of block

    def to_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "page_num": self.page_num,
            "kind": self.kind,
            "bbox": list(self.bbox),
            "char_range": list(self.char_range),
            "raw_slice_hash": self.raw_slice_hash,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Block:
        bbox = data.get("bbox", [0.0, 0.0, 0.0, 0.0])
        char_range = data.get("char_range", [0, 0])
        return cls(
            block_id=str(data["block_id"]),
            page_num=int(data.get("page_num", 1)),
            kind=data.get("kind", "paragraph"),
            bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])),
            char_range=(int(char_range[0]), int(char_range[1])),
            raw_slice_hash=str(data.get("raw_slice_hash", "")),
            text=str(data.get("text", "")),
        )


@dataclass
class TransformMap:
    """
    Deterministic piecewise-linear coordinate mapping between canonical text and raw decoded text.
    canonical_to_raw_char stores anchor points [[c_i, r_i], ...].
    Between anchor i and anchor i+1, delta is linear: r = r_i + (c - c_i).
    """
    canonical_to_raw_char: list[list[int]] = field(default_factory=lambda: [[0, 0]])
    transform_steps: list[str] = field(default_factory=lambda: ["nfc_normalization"])
    implementation_hash: str = "v1.2.0-utf8-nfc"

    def map_canonical_offset(self, c_offset: int) -> int:
        """Map canonical code-point offset to raw decoded code-point offset."""
        if not self.canonical_to_raw_char:
            return c_offset
        # Find the latest anchor where c_i <= c_offset
        best_c, best_r = self.canonical_to_raw_char[0]
        for c_i, r_i in self.canonical_to_raw_char:
            if c_i <= c_offset:
                best_c, best_r = c_i, r_i
            else:
                break
        return best_r + (c_offset - best_c)

    def map_raw_offset(self, r_offset: int) -> int:
        """Map raw decoded code-point offset to canonical code-point offset."""
        if not self.canonical_to_raw_char:
            return r_offset
        best_c, best_r = self.canonical_to_raw_char[0]
        for c_i, r_i in self.canonical_to_raw_char:
            if r_i <= r_offset:
                best_c, best_r = c_i, r_i
            else:
                break
        return max(0, best_c + (r_offset - best_r))

    def map_canonical_span(self, c_start: int, c_end: int) -> tuple[int, int]:
        """Map canonical [start, end) span to raw decoded [start, end) span."""
        return self.map_canonical_offset(c_start), self.map_canonical_offset(c_end)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_to_raw_char": self.canonical_to_raw_char,
            "transform_steps": self.transform_steps,
            "implementation_hash": self.implementation_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TransformMap:
        return cls(
            canonical_to_raw_char=data.get("canonical_to_raw_char", [[0, 0]]),
            transform_steps=data.get("transform_steps", ["nfc_normalization"]),
            implementation_hash=data.get("implementation_hash", "v1.2.0-utf8-nfc"),
        )


@dataclass
class DocumentIR:
    """
    Canonical Intermediate Representation of an ingested document.
    Serves as the immutable grounding coordinate substrate for all candidate extractions.
    """
    raw_artifact_sha256: str
    decoded_text_sha256: str
    canonical_text_sha256: str
    canonicalizer_version: str
    parser_metadata: dict[str, Any]
    blocks: list[Block]
    transform_map: TransformMap
    decoded_text: str = ""
    canonical_text: str = ""

    def get_canonical_slice(self, start: int, end: int) -> str:
        """Extract a half-open code-point slice [start, end) from canonical text."""
        if start < 0 or end > len(self.canonical_text) or start > end:
            raise IndexError(f"Span [{start}, {end}) is out of bounds for canonical text (len {len(self.canonical_text)})")
        return self.canonical_text[start:end]

    def get_blocks_for_canonical_span(self, start: int, end: int) -> list[Block]:
        """Find all blocks intersecting with [start, end)."""
        overlapping = []
        for block in self.blocks:
            b_start, b_end = block.char_range
            if max(start, b_start) < min(end, b_end):
                overlapping.append(block)
        return overlapping

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Validate hashes, coordinate bounds, and slice hashes."""
        violations = []
        
        # Verify text hashes if text is populated
        if self.decoded_text:
            actual_decoded_hash = hashlib.sha256(self.decoded_text.encode("utf-8")).hexdigest()
            if actual_decoded_hash != self.decoded_text_sha256:
                violations.append(
                    f"Decoded text SHA256 mismatch: recorded {self.decoded_text_sha256}, actual {actual_decoded_hash}"
                )
        
        if self.canonical_text:
            actual_canonical_hash = hashlib.sha256(self.canonical_text.encode("utf-8")).hexdigest()
            if actual_canonical_hash != self.canonical_text_sha256:
                violations.append(
                    f"Canonical text SHA256 mismatch: recorded {self.canonical_text_sha256}, actual {actual_canonical_hash}"
                )
        
        # Verify block integrity
        canon_len = len(self.canonical_text) if self.canonical_text else None
        for block in self.blocks:
            b_start, b_end = block.char_range
            if b_start < 0 or b_end < b_start:
                violations.append(f"Block {block.block_id} has invalid char range [{b_start}, {b_end})")
            elif canon_len is not None and b_end > canon_len:
                violations.append(f"Block {block.block_id} range [{b_start}, {b_end}) exceeds canonical text length {canon_len}")
            
            if self.canonical_text and b_end <= canon_len:
                actual_slice = self.canonical_text[b_start:b_end]
                actual_hash = hashlib.sha256(actual_slice.encode("utf-8")).hexdigest()
                if actual_hash != block.raw_slice_hash:
                    violations.append(
                        f"Block {block.block_id} slice hash mismatch: recorded {block.raw_slice_hash}, actual {actual_hash}"
                    )
                if block.text and block.text != actual_slice:
                    violations.append(f"Block {block.block_id} text content disagrees with canonical slice")
        
        return len(violations) == 0, violations

    def to_dict(self, include_full_text: bool = True) -> dict[str, Any]:
        d = {
            "raw_artifact_sha256": self.raw_artifact_sha256,
            "decoded_text_sha256": self.decoded_text_sha256,
            "canonical_text_sha256": self.canonical_text_sha256,
            "canonicalizer_version": self.canonicalizer_version,
            "parser_metadata": self.parser_metadata,
            "blocks": [b.to_dict() for b in self.blocks],
            "transform_map": self.transform_map.to_dict(),
        }
        if include_full_text:
            d["decoded_text"] = self.decoded_text
            d["canonical_text"] = self.canonical_text
        return d

    def to_json(self, indent: int = 2, include_full_text: bool = True) -> str:
        return json.dumps(self.to_dict(include_full_text=include_full_text), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DocumentIR:
        blocks = [Block.from_dict(b) for b in data.get("blocks", [])]
        transform_map = TransformMap.from_dict(data.get("transform_map", {}))
        return cls(
            raw_artifact_sha256=str(data["raw_artifact_sha256"]),
            decoded_text_sha256=str(data["decoded_text_sha256"]),
            canonical_text_sha256=str(data["canonical_text_sha256"]),
            canonicalizer_version=str(data.get("canonicalizer_version", "v1.2.0-utf8-nfc")),
            parser_metadata=dict(data.get("parser_metadata", {})),
            blocks=blocks,
            transform_map=transform_map,
            decoded_text=str(data.get("decoded_text", "")),
            canonical_text=str(data.get("canonical_text", "")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> DocumentIR:
        return cls.from_dict(json.loads(json_str))


def build_canonical_document_ir(
    raw_bytes: bytes,
    decoded_text: str,
    raw_blocks: list[dict[str, Any]],
    parser_metadata: Optional[dict[str, Any]] = None,
    canonicalizer_version: str = "v1.2.0-utf8-nfc",
    merge_hyphen_breaks: bool = True
) -> DocumentIR:
    """
    Constructs a verified DocumentIR instance from raw decoded text and parsed blocks.
    Executes versioned NFC normalization and optional hyphen break merging,
    while constructing the exact invertible TransformMap.
    """
    raw_artifact_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    decoded_text_sha256 = hashlib.sha256(decoded_text.encode("utf-8")).hexdigest()
    
    # 1. Normalize line endings and perform Unicode NFC normalization
    # Track character adjustments if decomposed characters merge
    transform_steps = ["nfc_normalization"]
    
    # We construct canonical text step-by-step to track anchor points
    # Anchor format: [canonical_offset, raw_offset]
    anchors: list[list[int]] = [[0, 0]]
    
    # Check if NFC normalization alters length
    nfc_text = unicodedata.normalize("NFC", decoded_text)
    
    # If hyphen break merging is requested:
    final_canonical_text = nfc_text
    if merge_hyphen_breaks:
        transform_steps.append("hyphen_break_merge")
        # Find patterns like word-\nword and merge them, recording offset shifts
        # Regex: r'(\b[A-Za-z]+)-\r?\n([A-Za-z]+\b)'
        parts = []
        last_raw_idx = 0
        last_canon_idx = 0
        curr_anchors = [[0, 0]]
        
        pattern = re.compile(r"([A-Za-z]+)-\r?\n([A-Za-z]+)")
        for m in pattern.finditer(nfc_text):
            # Text before match
            pre_start, pre_end = last_raw_idx, m.start()
            segment = nfc_text[pre_start:pre_end]
            parts.append(segment)
            last_canon_idx += len(segment)
            
            # The match itself: e.g. "pre-\npost" -> "prepost"
            w1, w2 = m.group(1), m.group(2)
            merged = w1 + w2
            parts.append(merged)
            
            # Anchor right after the merged word:
            # canonical advances by len(merged), raw advances by len(m.group(0))
            last_canon_idx += len(merged)
            last_raw_idx = m.end()
            
            curr_anchors.append([last_canon_idx, last_raw_idx])
            
        parts.append(nfc_text[last_raw_idx:])
        final_canonical_text = "".join(parts)
        anchors = curr_anchors
    else:
        # If no regex mutations, check if simple NFC length differs
        if len(nfc_text) != len(decoded_text):
            # Build detailed character-by-character anchors
            c_idx, r_idx = 0, 0
            anchors = [[0, 0]]
            for char in decoded_text:
                nfc_char = unicodedata.normalize("NFC", char)
                c_idx += len(nfc_char)
                r_idx += len(char)
                anchors.append([c_idx, r_idx])
        else:
            anchors = [[0, 0]]

    canonical_text_sha256 = hashlib.sha256(final_canonical_text.encode("utf-8")).hexdigest()
    
    t_map = TransformMap(
        canonical_to_raw_char=anchors,
        transform_steps=transform_steps,
        implementation_hash=canonicalizer_version
    )
    
    # Build verified blocks
    built_blocks: list[Block] = []
    for rb in raw_blocks:
        b_id = str(rb.get("block_id", f"blk-{len(built_blocks):03d}"))
        page = int(rb.get("page_num", 1))
        kind = rb.get("kind", "paragraph")
        bbox = tuple(rb.get("bbox", (0.0, 0.0, 0.0, 0.0)))
        
        # If block provides raw char range, map it to canonical
        raw_range = rb.get("raw_char_range")
        if raw_range:
            c_start = t_map.map_raw_offset(raw_range[0])
            c_end = t_map.map_raw_offset(raw_range[1])
        else:
            c_start = int(rb.get("char_range", [0, 0])[0])
            c_end = int(rb.get("char_range", [0, 0])[1])
            
        c_start = max(0, min(c_start, len(final_canonical_text)))
        c_end = max(c_start, min(c_end, len(final_canonical_text)))
        
        block_text = final_canonical_text[c_start:c_end]
        raw_slice_hash = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
        
        built_blocks.append(
            Block(
                block_id=b_id,
                page_num=page,
                kind=kind,
                bbox=bbox,
                char_range=(c_start, c_end),
                raw_slice_hash=raw_slice_hash,
                text=block_text
            )
        )
        
    doc_ir = DocumentIR(
        raw_artifact_sha256=raw_artifact_sha256,
        decoded_text_sha256=decoded_text_sha256,
        canonical_text_sha256=canonical_text_sha256,
        canonicalizer_version=canonicalizer_version,
        parser_metadata=parser_metadata or {"parser_id": "generic_baseline", "version": "1.0.0"},
        blocks=built_blocks,
        transform_map=t_map,
        decoded_text=decoded_text,
        canonical_text=final_canonical_text
    )
    
    valid, errors = doc_ir.verify_integrity()
    if not valid:
        raise ValueError(f"Built DocumentIR failed self-integrity verification: {errors}")
        
    return doc_ir
