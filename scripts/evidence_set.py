"""
FLOSSI0ULLK Evidence Grounding & Coordinate System Module.
Defines typed EvidenceAtom and EvidenceSet with deterministic alignment to DocumentIR.
Part of Phase 2 (Task 2.1) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import difflib
import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal, Any, Sequence

from document_ir import DocumentIR, Block

GroundingClass = Literal[
    "RAW_BYTE_EXACT",
    "SOURCE_TEXT_EXACT",
    "CANONICAL_CHAR_EXACT",
    "TRANSFORM_MAPPED",
    "OCR_REGION_GROUNDED",
    "STRUCTURE_GROUNDED",
    "APPROXIMATE",
    "UNALIGNED"
]

PROMOTABLE_GROUNDINGS: set[GroundingClass] = {
    "RAW_BYTE_EXACT",
    "SOURCE_TEXT_EXACT",
    "CANONICAL_CHAR_EXACT",
    "TRANSFORM_MAPPED",
    "OCR_REGION_GROUNDED",
    "STRUCTURE_GROUNDED"
}

AtomType = Literal[
    "text_span",
    "table_cell",
    "figure_region",
    "equation",
    "metadata_field"
]

AlignmentStatus = Literal[
    "EXACT",
    "MAPPED",
    "APPROXIMATE",
    "MULTIPLE_CANDIDATES",
    "UNALIGNED"
]


@dataclass(frozen=True)
class EvidenceAtom:
    """A grounded, typed observational evidence element supporting a claim."""
    atom_id: str
    atom_type: AtomType
    grounding_class: GroundingClass
    source_ref: str  # canonical SHA-256 or document identifier
    block_id: Optional[str] = None
    char_range: Optional[tuple[int, int]] = None  # [start, end) in canonical text
    literal_content: str = ""
    bbox: Optional[tuple[float, float, float, float]] = None
    page_num: Optional[int] = None
    ocr_engine: Optional[str] = None
    ocr_confidence: Optional[float] = None
    alignment_status: AlignmentStatus = "EXACT"
    candidate_char_ranges: list[tuple[int, int]] = field(default_factory=list)

    def is_promotable(self) -> bool:
        """Only promotable groundings and unambiguous alignment qualify for knowledge promotion."""
        return (
            self.grounding_class in PROMOTABLE_GROUNDINGS
            and self.alignment_status in ("EXACT", "MAPPED")
        )

    def verify_grounding(self, doc_ir: DocumentIR) -> tuple[bool, list[str]]:
        """Verifies that the atom faithfully reproduces its claim against the DocumentIR."""
        violations = []
        if self.source_ref != doc_ir.canonical_text_sha256 and self.source_ref != doc_ir.raw_artifact_sha256:
            violations.append(
                f"Source reference mismatch: atom points to {self.source_ref}, doc has {doc_ir.canonical_text_sha256}"
            )

        if self.char_range:
            start, end = self.char_range
            if start < 0 or end > len(doc_ir.canonical_text) or start > end:
                violations.append(f"Char range [{start}, {end}) is out of bounds for doc canonical text")
            else:
                slice_text = doc_ir.canonical_text[start:end]
                if self.grounding_class == "CANONICAL_CHAR_EXACT" and slice_text != self.literal_content:
                    violations.append(
                        f"Canonical slice disagreement: literal_content={self.literal_content!r} vs slice={slice_text!r}"
                    )
        elif self.grounding_class in ("CANONICAL_CHAR_EXACT", "RAW_BYTE_EXACT", "SOURCE_TEXT_EXACT"):
            violations.append(f"Grounding class {self.grounding_class} requires char_range but none provided")

        return len(violations) == 0, violations

    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "atom_type": self.atom_type,
            "grounding_class": self.grounding_class,
            "source_ref": self.source_ref,
            "block_id": self.block_id,
            "char_range": list(self.char_range) if self.char_range else None,
            "literal_content": self.literal_content,
            "bbox": list(self.bbox) if self.bbox else None,
            "page_num": self.page_num,
            "ocr_engine": self.ocr_engine,
            "ocr_confidence": self.ocr_confidence,
            "alignment_status": self.alignment_status,
            "candidate_char_ranges": [list(r) for r in self.candidate_char_ranges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceAtom:
        char_r = data.get("char_range")
        bbox = data.get("bbox")
        cand_ranges = [tuple(r) for r in data.get("candidate_char_ranges", [])]
        return cls(
            atom_id=str(data["atom_id"]),
            atom_type=data.get("atom_type", "text_span"),
            grounding_class=data.get("grounding_class", "CANONICAL_CHAR_EXACT"),
            source_ref=str(data["source_ref"]),
            block_id=data.get("block_id"),
            char_range=(int(char_r[0]), int(char_r[1])) if char_r else None,
            literal_content=str(data.get("literal_content", "")),
            bbox=(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])) if bbox else None,
            page_num=int(data["page_num"]) if data.get("page_num") is not None else None,
            ocr_engine=data.get("ocr_engine"),
            ocr_confidence=float(data["ocr_confidence"]) if data.get("ocr_confidence") is not None else None,
            alignment_status=data.get("alignment_status", "EXACT"),
            candidate_char_ranges=cand_ranges,
        )


@dataclass
class EvidenceSet:
    """An aggregation of typed evidence atoms supporting a candidate claim."""
    claim_id: str
    atoms: list[EvidenceAtom] = field(default_factory=list)
    primary_quote: str = ""

    def is_grounded(self) -> bool:
        """Returns True if the set has at least one atom and all atoms are promotable."""
        return len(self.atoms) > 0 and all(a.is_promotable() for a in self.atoms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "atoms": [a.to_dict() for a in self.atoms],
            "primary_quote": self.primary_quote,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceSet:
        atoms = [EvidenceAtom.from_dict(a) for a in data.get("atoms", [])]
        return cls(
            claim_id=str(data["claim_id"]),
            atoms=atoms,
            primary_quote=str(data.get("primary_quote", "")),
        )


def align_literal_evidence(
    literal_quote: str,
    doc_ir: DocumentIR,
    atom_id: str = "ev-01",
    preferred_block_id: Optional[str] = None
) -> EvidenceAtom:
    """
    Deterministically aligns a literal text quotation against a DocumentIR.
    Returns an EvidenceAtom with the strongest verified grounding class.
    """
    quote_clean = literal_quote.strip()
    canon_text = doc_ir.canonical_text
    source_ref = doc_ir.canonical_text_sha256

    if not quote_clean:
        return EvidenceAtom(
            atom_id=atom_id,
            atom_type="text_span",
            grounding_class="UNALIGNED",
            source_ref=source_ref,
            alignment_status="UNALIGNED",
            literal_content=""
        )

    # 1. Exact match in canonical text
    occurrences = []
    start_pos = 0
    while True:
        idx = canon_text.find(quote_clean, start_pos)
        if idx == -1:
            break
        occurrences.append((idx, idx + len(quote_clean)))
        start_pos = idx + 1

    if len(occurrences) == 1:
        start, end = occurrences[0]
        blocks = doc_ir.get_blocks_for_canonical_span(start, end)
        primary_block = blocks[0] if blocks else None
        return EvidenceAtom(
            atom_id=atom_id,
            atom_type="text_span",
            grounding_class="CANONICAL_CHAR_EXACT",
            source_ref=source_ref,
            block_id=primary_block.block_id if primary_block else None,
            char_range=(start, end),
            literal_content=quote_clean,
            bbox=primary_block.bbox if primary_block else None,
            page_num=primary_block.page_num if primary_block else 1,
            alignment_status="EXACT"
        )
    elif len(occurrences) > 1:
        # Multiple occurrences
        # If preferred_block_id is provided, try to disambiguate
        matched_block = None
        chosen_range = None
        if preferred_block_id:
            for start, end in occurrences:
                blocks = doc_ir.get_blocks_for_canonical_span(start, end)
                for b in blocks:
                    if b.block_id == preferred_block_id:
                        matched_block = b
                        chosen_range = (start, end)
                        break
                if matched_block:
                    break

        if matched_block and chosen_range:
            return EvidenceAtom(
                atom_id=atom_id,
                atom_type="text_span",
                grounding_class="CANONICAL_CHAR_EXACT",
                source_ref=source_ref,
                block_id=matched_block.block_id,
                char_range=chosen_range,
                literal_content=quote_clean,
                bbox=matched_block.bbox,
                page_num=matched_block.page_num,
                alignment_status="EXACT",
                candidate_char_ranges=occurrences
            )
        else:
            first_start, first_end = occurrences[0]
            blocks = doc_ir.get_blocks_for_canonical_span(first_start, first_end)
            return EvidenceAtom(
                atom_id=atom_id,
                atom_type="text_span",
                grounding_class="CANONICAL_CHAR_EXACT",
                source_ref=source_ref,
                block_id=blocks[0].block_id if blocks else None,
                char_range=occurrences[0],
                literal_content=quote_clean,
                bbox=blocks[0].bbox if blocks else None,
                page_num=blocks[0].page_num if blocks else 1,
                alignment_status="MULTIPLE_CANDIDATES",
                candidate_char_ranges=occurrences
            )

    # 2. Check if matched in raw decoded text and map through transform_map
    if doc_ir.decoded_text:
        raw_idx = doc_ir.decoded_text.find(quote_clean)
        if raw_idx != -1:
            raw_end = raw_idx + len(quote_clean)
            c_start = doc_ir.transform_map.map_raw_offset(raw_idx)
            c_end = doc_ir.transform_map.map_raw_offset(raw_end)
            blocks = doc_ir.get_blocks_for_canonical_span(c_start, c_end)
            return EvidenceAtom(
                atom_id=atom_id,
                atom_type="text_span",
                grounding_class="TRANSFORM_MAPPED",
                source_ref=source_ref,
                block_id=blocks[0].block_id if blocks else None,
                char_range=(c_start, c_end),
                literal_content=quote_clean,
                bbox=blocks[0].bbox if blocks else None,
                page_num=blocks[0].page_num if blocks else 1,
                alignment_status="MAPPED"
            )

    # 3. Fuzzy matching via word-anchored and windowed SequenceMatcher
    words = quote_clean.split()
    best_ratio = 0.0
    best_span = (0, 0)

    if len(words) >= 2:
        first_word = words[0]
        last_word = words[-1]
        for m_start in re.finditer(re.escape(first_word), canon_text):
            s = m_start.start()
            search_bound = min(len(canon_text), s + int(len(quote_clean) * 2.5))
            for m_end in re.finditer(re.escape(last_word), canon_text[s:search_bound]):
                e = s + m_end.end()
                span_text = canon_text[s:e]
                r = difflib.SequenceMatcher(None, span_text, quote_clean).ratio()
                if r > best_ratio:
                    best_ratio = r
                    best_span = (s, e)

    # If word anchoring didn't find high confidence, check sliding window of length len(quote_clean)
    if best_ratio < 0.75:
        target_len = len(quote_clean)
        first_token = words[0] if words else quote_clean[:6]
        start_candidates = [m.start() for m in re.finditer(re.escape(first_token[:4]), canon_text)]
        if not start_candidates:
            start_candidates = range(0, len(canon_text) - target_len + 1, max(1, target_len // 4))

        for sc in start_candidates:
            ec = min(len(canon_text), sc + target_len)
            window = canon_text[sc:ec]
            r = difflib.SequenceMatcher(None, window, quote_clean).ratio()
            if r > best_ratio:
                best_ratio = r
                best_span = (sc, ec)

    if best_ratio >= 0.75:
        blocks = doc_ir.get_blocks_for_canonical_span(best_span[0], best_span[1])
        return EvidenceAtom(
            atom_id=atom_id,
            atom_type="text_span",
            grounding_class="APPROXIMATE",
            source_ref=source_ref,
            block_id=blocks[0].block_id if blocks else None,
            char_range=best_span,
            literal_content=quote_clean,
            bbox=blocks[0].bbox if blocks else None,
            page_num=blocks[0].page_num if blocks else 1,
            alignment_status="APPROXIMATE"
        )

    # 4. Unaligned fallback
    return EvidenceAtom(
        atom_id=atom_id,
        atom_type="text_span",
        grounding_class="UNALIGNED",
        source_ref=source_ref,
        alignment_status="UNALIGNED",
        literal_content=quote_clean
    )
