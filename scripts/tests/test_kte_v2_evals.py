"""
Test runner for KTE v2 Evaluation Suite (Layer 1 Invariants and Layer 2 Minimal Pairs).
Verifies that EntailmentGate and coordinate alignment adhere to H1–H17 catastrophic hazard gates.
Part of Phase 3 (Task 3.2) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evidence_set import EvidenceAtom, EvidenceSet, align_literal_evidence
from claim_candidate import ClaimVersion, NormalizedTriple
from entailment_gate import EntailmentGate, EntailmentAssessment
from document_ir import build_canonical_document_ir


def test_layer_1_unit_invariants():
    v2_dir = Path(__file__).resolve().parent.parent.parent / "evals" / "knowledge_triple_extraction" / "v2"
    unit_file = v2_dir / "unit_invariants.json"
    assert unit_file.is_file(), f"Missing unit_invariants.json at {unit_file}"

    with open(unit_file, "r", encoding="utf-8") as f:
        invariants = json.load(f)

    gate = EntailmentGate()

    for item in invariants:
        h_id = item["id"]
        hazard = item["hazard"]
        
        if h_id == "UNIT-004":  # Polarity inversion (H4)
            ev = EvidenceSet(claim_id="u4", atoms=[EvidenceAtom(
                atom_id="ev-1", atom_type="text_span", grounding_class="CANONICAL_CHAR_EXACT",
                source_ref="ref", literal_content=item["evidence"]
            )])
            clm = ClaimVersion(
                claim_id="u4", claim_version=1, claim_type="observation", statement=item["claim"],
                subject_surface="Drug A", relation_surface="binds to", object_surface="receptor B",
                normalized_triple=NormalizedTriple(subject="drug_a", predicate="binds", object="receptor_b"),
                polarity="affirmed"
            )
            res = gate.assess(clm, ev)
            assert res.state == item["expected_verdict"], f"Failed {h_id}: expected {item['expected_verdict']}, got {res.state}"

        elif h_id == "UNIT-005":  # Modal strengthening (H5)
            ev = EvidenceSet(claim_id="u5", atoms=[EvidenceAtom(
                atom_id="ev-1", atom_type="text_span", grounding_class="CANONICAL_CHAR_EXACT",
                source_ref="ref", literal_content=item["evidence"]
            )])
            clm = ClaimVersion(
                claim_id="u5", claim_version=1, claim_type="observation", statement=item["claim_statement"],
                subject_surface="Enzyme C", relation_surface="modulates", object_surface="pathway D",
                normalized_triple=NormalizedTriple(subject="ec", predicate="modulates", object="pd"),
                polarity="affirmed", modality_type="none", modality_strength="asserted"
            )
            res = gate.assess(clm, ev)
            assert res.state == item["expected_verdict"], f"Failed {h_id}: expected {item['expected_verdict']}, got {res.state}"

        elif h_id == "UNIT-013":  # Invertible transform replay (H13)
            doc_ir = build_canonical_document_ir(
                raw_bytes=item["raw_text"].encode("utf-8"),
                decoded_text=item["raw_text"],
                raw_blocks=[{"block_id": "b-1", "char_range": [0, len(item["canonical_text"])]}],
                merge_hyphen_breaks=True
            )
            assert doc_ir.canonical_text == item["canonical_text"]
            r_start, r_end = doc_ir.transform_map.map_canonical_span(item["mapped_span"][0], item["mapped_span"][1])
            assert doc_ir.decoded_text[r_start:r_end] == item["raw_slice"]


def test_layer_2_minimal_pairs():
    v2_dir = Path(__file__).resolve().parent.parent.parent / "evals" / "knowledge_triple_extraction" / "v2"
    pairs_file = v2_dir / "minimal_pairs.json"
    assert pairs_file.is_file(), f"Missing minimal_pairs.json at {pairs_file}"

    with open(pairs_file, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    gate = EntailmentGate()

    for pair in pairs:
        pid = pair["pair_id"]
        
        if pid == "PAIR-01":  # Polarity: affirmed vs negated
            # Item A: Affirmed
            ev_a = EvidenceSet(claim_id="p1a", atoms=[EvidenceAtom(
                atom_id="ev-a", atom_type="text_span", grounding_class="CANONICAL_CHAR_EXACT",
                source_ref="ref", literal_content=pair["item_a"]["text"]
            )])
            clm_a = ClaimVersion(
                claim_id="p1a", claim_version=1, claim_type="causal", statement=pair["item_a"]["candidate_claim"],
                subject_surface="Compound Alpha", relation_surface="increases", object_surface="cellular apoptosis",
                normalized_triple=NormalizedTriple(subject="ca", predicate="increases", object="ap"),
                polarity="affirmed"
            )
            res_a = gate.assess(clm_a, ev_a)
            assert res_a.state == pair["item_a"]["expected_entailment"]

            # Item B: Negated
            ev_b = EvidenceSet(claim_id="p1b", atoms=[EvidenceAtom(
                atom_id="ev-b", atom_type="text_span", grounding_class="CANONICAL_CHAR_EXACT",
                source_ref="ref", literal_content=pair["item_b"]["text"]
            )])
            clm_b = ClaimVersion(
                claim_id="p1b", claim_version=1, claim_type="causal", statement=pair["item_b"]["candidate_claim"],
                subject_surface="Compound Alpha", relation_surface="increases", object_surface="cellular apoptosis",
                normalized_triple=NormalizedTriple(subject="ca", predicate="increases", object="ap"),
                polarity="affirmed"
            )
            res_b = gate.assess(clm_b, ev_b)
            assert res_b.state == pair["item_b"]["expected_entailment"]

        elif pid == "PAIR-02":  # Modality: asserted vs hedged
            # Item A: Asserted
            ev_a = EvidenceSet(claim_id="p2a", atoms=[EvidenceAtom(
                atom_id="ev-a", atom_type="text_span", grounding_class="CANONICAL_CHAR_EXACT",
                source_ref="ref", literal_content=pair["item_a"]["text"]
            )])
            clm_a = ClaimVersion(
                claim_id="p2a", claim_version=1, claim_type="association", statement=pair["item_a"]["candidate_claim"],
                subject_surface="Biomarker Beta", relation_surface="correlates with", object_surface="early disease progression",
                normalized_triple=NormalizedTriple(subject="bb", predicate="correlates", object="dp"),
                polarity="affirmed", modality_type="none", modality_strength="asserted"
            )
            res_a = gate.assess(clm_a, ev_a)
            assert res_a.state == pair["item_a"]["expected_entailment"]

            # Item B: Hedged in evidence
            ev_b = EvidenceSet(claim_id="p2b", atoms=[EvidenceAtom(
                atom_id="ev-b", atom_type="text_span", grounding_class="CANONICAL_CHAR_EXACT",
                source_ref="ref", literal_content=pair["item_b"]["text"]
            )])
            clm_b = ClaimVersion(
                claim_id="p2b", claim_version=1, claim_type="association", statement=pair["item_b"]["candidate_claim"],
                subject_surface="Biomarker Beta", relation_surface="correlates with", object_surface="early disease progression",
                normalized_triple=NormalizedTriple(subject="bb", predicate="correlates", object="dp"),
                polarity="affirmed", modality_type="none", modality_strength="asserted"
            )
            res_b = gate.assess(clm_b, ev_b)
            assert res_b.state == pair["item_b"]["expected_entailment"]
