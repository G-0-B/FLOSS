"""
FLOSSI0ULLK Document Parser Routing Module.
Dispatches incoming documents through pre-parse quarantine to appropriate parser adapters,
producing verified DocumentIR instances with coordinate provenance.
Part of Phase 1 (Task 1.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path
from typing import Optional, Any, Literal

from rights_envelope import DocumentQuarantine, SecurityDisposition, RightsEnvelope
from document_ir import DocumentIR, build_canonical_document_ir

ParserEngine = Literal["docling", "pymupdf", "pypdf", "native_text", "auto"]


class ParserRouter:
    """Routes documents to format-specific adapters while enforcing security and rights gates."""

    def __init__(self, quarantine: Optional[DocumentQuarantine] = None):
        self.quarantine = quarantine or DocumentQuarantine()

    def parse_file(
        self,
        file_path: str | Path,
        rights_envelope: Optional[RightsEnvelope] = None,
        preferred_engine: ParserEngine = "auto"
    ) -> tuple[DocumentIR, SecurityDisposition]:
        """
        Inspects file, runs pre-parse quarantine checks, and routes to parser adapter.
        Raises PermissionError if rights or security quarantine fails.
        """
        path = Path(file_path).resolve()
        disposition, verified_rights = self.quarantine.audit_file(path, rights=rights_envelope)
        if disposition.sandbox_status != "CLEARED":
            raise PermissionError(
                f"Document quarantined by security policy: {', '.join(disposition.quarantine_reasons)}"
            )

        raw_bytes = path.read_bytes()
        ext = path.suffix.lower()

        return self.parse_bytes(
            raw_bytes=raw_bytes,
            filename=path.name,
            ext=ext,
            disposition=disposition,
            preferred_engine=preferred_engine
        )

    def parse_bytes(
        self,
        raw_bytes: bytes,
        filename: str,
        ext: str,
        disposition: Optional[SecurityDisposition] = None,
        preferred_engine: ParserEngine = "auto"
    ) -> tuple[DocumentIR, SecurityDisposition]:
        """Parses in-memory bytes into verified DocumentIR."""
        if disposition is None:
            sha256 = hashlib.sha256(raw_bytes).hexdigest()
            disposition = SecurityDisposition(
                file_path=filename,
                file_size_bytes=len(raw_bytes),
                raw_artifact_sha256=sha256,
                is_symlink=False,
                mime_type="application/octet-stream",
                sandbox_status="CLEARED"
            )

        ext = ext.lower()
        if not ext.startswith("."):
            ext = "." + ext

        if ext == ".pdf":
            decoded_text, raw_blocks, metadata = self._parse_pdf(raw_bytes, preferred_engine)
        elif ext in (".md", ".markdown", ".txt", ".json", ".csv"):
            decoded_text, raw_blocks, metadata = self._parse_text(raw_bytes, ext)
        else:
            # Fallback text decoding
            decoded_text, raw_blocks, metadata = self._parse_text(raw_bytes, ext)

        doc_ir = build_canonical_document_ir(
            raw_bytes=raw_bytes,
            decoded_text=decoded_text,
            raw_blocks=raw_blocks,
            parser_metadata=metadata,
            merge_hyphen_breaks=True
        )

        return doc_ir, disposition

    def _parse_pdf(
        self,
        raw_bytes: bytes,
        preferred_engine: ParserEngine
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
        """Parses PDF bytes using PyMuPDF (fitz) or fallback."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=raw_bytes, filetype="pdf")
            
            full_text_parts = []
            raw_blocks = []
            current_raw_char = 0

            for page_idx, page in enumerate(doc, start=1):
                # get_text("blocks") returns tuples: (x0, y0, x1, y1, text, block_no, block_type)
                # block_type 0 = text, 1 = image
                page_blocks = page.get_text("blocks")
                for b in page_blocks:
                    x0, y0, x1, y1, text, b_no, b_type = b[:7]
                    text_str = text or ""
                    if not text_str.strip():
                        continue

                    # Determine block kind
                    kind = "paragraph"
                    if len(text_str.strip()) < 80 and (text_str.isupper() or text_str.strip().endswith(":")):
                        kind = "heading"

                    b_len = len(text_str)
                    char_range = [current_raw_char, current_raw_char + b_len]
                    current_raw_char += b_len
                    full_text_parts.append(text_str)

                    raw_blocks.append({
                        "block_id": f"p{page_idx:02d}-b{b_no:03d}",
                        "page_num": page_idx,
                        "kind": kind,
                        "bbox": [float(x0), float(y0), float(x1), float(y1)],
                        "raw_char_range": char_range,
                    })

            full_decoded_text = "".join(full_text_parts)
            metadata = {
                "parser_id": "pymupdf",
                "version": getattr(fitz, "__version__", "1.24+"),
                "pages": len(doc),
            }
            return full_decoded_text, raw_blocks, metadata

        except ImportError:
            # Fallback to plain decoding if PyMuPDF unavailable
            return self._parse_text(raw_bytes, ".pdf")

    def _parse_text(
        self,
        raw_bytes: bytes,
        ext: str
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
        """Parses plain text, markdown, or code documents into structured paragraphs."""
        try:
            decoded_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            decoded_text = raw_bytes.decode("latin-1", errors="replace")

        # Split into paragraphs by double newlines
        paragraphs = re.split(r"(\r?\n\s*\r?\n)", decoded_text)
        raw_blocks = []
        char_idx = 0

        for idx, part in enumerate(paragraphs):
            part_len = len(part)
            if part.strip():
                kind = "paragraph"
                stripped = part.strip()
                if stripped.startswith("#") or (len(stripped) < 80 and "\n" not in stripped and (stripped.isupper() or stripped.endswith(":"))):
                    kind = "heading"
                
                raw_blocks.append({
                    "block_id": f"blk-{len(raw_blocks):03d}",
                    "page_num": 1,
                    "kind": kind,
                    "bbox": [0.0, float(len(raw_blocks) * 20), 500.0, float((len(raw_blocks) + 1) * 20)],
                    "raw_char_range": [char_idx, char_idx + part_len]
                })
            char_idx += part_len

        metadata = {
            "parser_id": "native_text",
            "version": "1.0.0",
            "extension": ext
        }
        return decoded_text, raw_blocks, metadata
