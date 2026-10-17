"""
Unit tests for Layer 3 Acceptance Corpus structure, schema validity, and evidence grounding.
Verifies that all 100 documents satisfy the locked acceptance contract and evaluation unit rules.
Part of Phase 3 (Task 3.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from curate_layer_3_acceptance import L3_DIR, EVALS_DIR


def test_layer_3_summary_and_document_count():
    summary_path = L3_DIR / "summary_report.json"
    assert summary_path.is_file(), f"Missing summary report at {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["metrics"]["total_documents"] == 100
    assert summary["metrics"]["domain_breakdown"]["biomedical"] == 40
    assert summary["metrics"]["domain_breakdown"]["computer_science"] == 30
    assert summary["metrics"]["domain_breakdown"]["governance_commons"] == 30
    assert summary["metrics"]["null_passages"] >= 50
    assert summary["status"] == "STRICTLY_LOCKED"


def test_layer_3_records_structure_and_grounding():
    jsonl_path = L3_DIR / "layer_3_acceptance.jsonl"
    assert jsonl_path.is_file(), f"Missing layer_3_acceptance.jsonl at {jsonl_path}"

    docs = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                docs.append(json.loads(line))

    assert len(docs) == 100, f"Expected 100 documents in JSONL, got {len(docs)}"

    hex_re = re.compile(r"^[0-9a-f]{64}$")

    for doc in docs:
        # 1. Document Level
        assert "document_id" in doc
        assert doc["domain"] in ("biomedical", "computer_science", "governance_commons")
        assert hex_re.match(doc["source_hash"])

        # 2. Rights Receipt
        rights = doc["rights_receipt"]
        assert rights["local_processing_permitted"] is True
        assert rights["sensitive_data_classification"] == "PUBLIC"
        assert len(rights["license"]) > 2

        # 3. Dual Annotation & Adjudication
        da = doc["dual_annotation"]
        assert da["annotator_a"] and da["annotator_b"]
        assert 0.85 <= da["agreement_score"] <= 1.0

        adj = doc["adjudication"]
        assert adj["status"] == "APPROVED_GOLD"
        assert adj["adjudicator"]

        # 4. Passages & Claims Grounding
        passages = doc["passages"]
        assert len(passages) >= 2  # At least one informative and one null

        has_null = False
        has_informative = False

        for p in passages:
            p_text = p["text"]
            p_type = p["passage_type"]

            if p_type == "null_passage":
                has_null = True
                assert len(p["eligible_claims"]) == 0, "Null passage must contain 0 claims (H11 test)"
            elif p_type == "informative":
                has_informative = True
                assert len(p["eligible_claims"]) >= 1, "Informative passage must contain >= 1 claim"

                for c in p["eligible_claims"]:
                    assert c["statement"]
                    assert c["polarity"] in ("affirmed", "negated", "denied_evidence")
                    assert c["modality_strength"] in ("asserted", "probable", "possible", "hypothetical")

                    # Verify evidence atoms grounding in passage text
                    atoms = c["evidence_atoms"]
                    assert len(atoms) >= 1
                    for a in atoms:
                        assert a["grounding_class"] == "CANONICAL_CHAR_EXACT"
                        quote = a["literal_content"]
                        char_r = a.get("char_range")
                        assert char_r is not None
                        start, end = char_r
                        assert 0 <= start <= end <= len(p_text)
                        # Exact character slice check
                        slice_text = p_text[start:end]
                        assert slice_text == quote, f"Grounding mismatch: quote {quote!r} != slice {slice_text!r}"

        assert has_null, f"Document {doc['document_id']} missing null passage for H11 test"
        assert has_informative, f"Document {doc['document_id']} missing informative passage"
