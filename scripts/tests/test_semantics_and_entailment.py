"""
Unit tests for FLOSS/scripts/evidence_set.py, claim_candidate.py, and entailment_gate.py.
Verifies multi-atom evidence alignment, ClaimVersion schema, and 2-axis EntailmentAssessment.
Part of Phase 2 (Tasks 2.1 & 2.2) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add scripts directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from document_ir import DocumentIR, Block, TransformMap, build_canonical_document_ir
from evidence_set import EvidenceAtom, EvidenceSet, align_literal_evidence
from claim_candidate import ClaimVersion, NormalizedTriple, AttributionNode
from entailment_gate import EntailmentGate, EntailmentAssessment


def test_evidence_atom_promotability():
    atom_exact = EvidenceAtom(
        atom_id="ev-01",
        atom_type="text_span",
        grounding_class="CANONICAL_CHAR_EXACT",
        source_ref="sha256-abc",
        char_range=(0, 20),
        literal_content="Valid evidence span",
        alignment_status="EXACT"
    )
    assert atom_exact.is_promotable()

    atom_approx = EvidenceAtom(
        atom_id="ev-02",
        atom_type="text_span",
        grounding_class="APPROXIMATE",
        source_ref="sha256-abc",
        literal_content="Approximate span",
        alignment_status="APPROXIMATE"
    )
    assert not atom_approx.is_promotable()

    atom_unaligned = EvidenceAtom(
        atom_id="ev-03",
        atom_type="text_span",
        grounding_class="UNALIGNED",
        source_ref="sha256-abc",
        alignment_status="UNALIGNED"
    )
    assert not atom_unaligned.is_promotable()


def test_align_literal_evidence():
    text = "The hippocampus regulates episodic memory formation in mammalian cortex."
    doc_ir = build_canonical_document_ir(
        raw_bytes=text.encode("utf-8"),
        decoded_text=text,
        raw_blocks=[{"block_id": "b-1", "char_range": [0, len(text)]}],
        merge_hyphen_breaks=False
    )

    # 1. Exact match
    atom = align_literal_evidence("episodic memory formation", doc_ir)
    assert atom.grounding_class == "CANONICAL_CHAR_EXACT"
    assert atom.alignment_status == "EXACT"
    assert atom.char_range == (26, 51)
    assert atom.block_id == "b-1"

    # 2. Fuzzy match
    atom_fuzzy = align_literal_evidence("episodic memory formation in cortex", doc_ir)
    assert atom_fuzzy.grounding_class in ("CANONICAL_CHAR_EXACT", "APPROXIMATE")

    # 3. Unaligned match
    atom_none = align_literal_evidence("completely unrelated quantum physics", doc_ir)
    assert atom_none.grounding_class == "UNALIGNED"
    assert atom_none.alignment_status == "UNALIGNED"


def test_claim_version_serialization():
    triple = NormalizedTriple(
        subject="urn:entity:compound_x",
        predicate="inhibits",
        object="urn:entity:cellular_apoptosis"
    )
    claim = ClaimVersion(
        claim_id="clm-001",
        claim_version=1,
        claim_type="causal",
        statement="Compound X inhibits cellular apoptosis.",
        subject_surface="Compound X",
        relation_surface="inhibits",
        object_surface="cellular apoptosis",
        normalized_triple=triple,
        polarity="affirmed",
        modality_strength="asserted",
        attribution_chain=[AttributionNode(speaker="Study Team Alpha", kind="study_report")]
    )

    ok, violations = claim.validate_claim()
    assert ok, f"Claim validation failed: {violations}"

    json_str = claim.to_json()
    recovered = ClaimVersion.from_json(json_str)
    assert recovered.claim_id == "clm-001"
    assert recovered.statement == claim.statement
    assert recovered.normalized_triple.predicate == "inhibits"
    assert len(recovered.attribution_chain) == 1
    assert recovered.attribution_chain[0].speaker == "Study Team Alpha"


def test_entailment_gate_supported():
    gate = EntailmentGate()
    evidence_text = "Compound X significantly reduces cellular apoptosis in cortical neurons."
    atom = EvidenceAtom(
        atom_id="ev-01",
        atom_type="text_span",
        grounding_class="CANONICAL_CHAR_EXACT",
        source_ref="ref-123",
        literal_content=evidence_text,
        alignment_status="EXACT"
    )
    ev_set = EvidenceSet(claim_id="clm-01", atoms=[atom])

    claim = ClaimVersion(
        claim_id="clm-01",
        claim_version=1,
        claim_type="causal",
        statement="Compound X reduces cellular apoptosis.",
        subject_surface="Compound X",
        relation_surface="reduces",
        object_surface="cellular apoptosis",
        normalized_triple=NormalizedTriple(subject="urn:cx", predicate="reduces", object="urn:ca"),
        polarity="affirmed",
        modality_strength="asserted"
    )

    assessment = gate.assess(claim, ev_set)
    assert assessment.state == "SUPPORTED"
    assert assessment.support is True
    assert assessment.refutation is False


def test_entailment_gate_contradicted_polarity():
    gate = EntailmentGate()
    # Evidence says DOES NOT increase
    evidence_text = "Compound X does not increase cellular apoptosis in mammalian trials."
    atom = EvidenceAtom(
        atom_id="ev-01",
        atom_type="text_span",
        grounding_class="CANONICAL_CHAR_EXACT",
        source_ref="ref-123",
        literal_content=evidence_text,
        alignment_status="EXACT"
    )
    ev_set = EvidenceSet(claim_id="clm-02", atoms=[atom])

    # Claim falsely asserts affirmative increase
    claim = ClaimVersion(
        claim_id="clm-02",
        claim_version=1,
        claim_type="causal",
        statement="Compound X increases cellular apoptosis.",
        subject_surface="Compound X",
        relation_surface="increases",
        object_surface="cellular apoptosis",
        normalized_triple=NormalizedTriple(subject="urn:cx", predicate="increases", object="urn:ca"),
        polarity="affirmed",
        modality_strength="asserted"
    )

    assessment = gate.assess(claim, ev_set)
    assert assessment.state == "CONTRADICTED"
    assert assessment.support is False
    assert assessment.refutation is True
    assert "H4 failure: Polarity inversion" in assessment.rationale


def test_entailment_gate_insufficient_modality_strengthening():
    gate = EntailmentGate()
    # Evidence contains epistemic hedge "may"
    evidence_text = "Compound X may modulate cellular apoptosis under specific conditions."
    atom = EvidenceAtom(
        atom_id="ev-01",
        atom_type="text_span",
        grounding_class="CANONICAL_CHAR_EXACT",
        source_ref="ref-123",
        literal_content=evidence_text,
        alignment_status="EXACT"
    )
    ev_set = EvidenceSet(claim_id="clm-03", atoms=[atom])

    # Claim unlawfully strengthens to unhedged assertion
    claim = ClaimVersion(
        claim_id="clm-03",
        claim_version=1,
        claim_type="causal",
        statement="Compound X modulates cellular apoptosis.",
        subject_surface="Compound X",
        relation_surface="modulates",
        object_surface="cellular apoptosis",
        normalized_triple=NormalizedTriple(subject="urn:cx", predicate="modulates", object="urn:ca"),
        polarity="affirmed",
        modality_type="none",
        modality_strength="asserted"
    )

    assessment = gate.assess(claim, ev_set)
    assert assessment.state == "INSUFFICIENT"
    assert assessment.support is False
    assert assessment.refutation is False
    assert "H5 failure: Hedged evidence unlawfully strengthened" in assessment.rationale


def test_entailment_gate_conflicting_evidence():
    gate = EntailmentGate()
    # Two conflicting evidence atoms: one affirms, one negates
    atom_pos = EvidenceAtom(
        atom_id="ev-01",
        atom_type="text_span",
        grounding_class="CANONICAL_CHAR_EXACT",
        source_ref="ref-123",
        literal_content="Compound X increases cellular apoptosis in in-vitro assays.",
        alignment_status="EXACT"
    )
    atom_neg = EvidenceAtom(
        atom_id="ev-02",
        atom_type="text_span",
        grounding_class="CANONICAL_CHAR_EXACT",
        source_ref="ref-123",
        literal_content="Compound X does not increase cellular apoptosis in in-vivo models.",
        alignment_status="EXACT"
    )
    ev_set = EvidenceSet(claim_id="clm-04", atoms=[atom_pos, atom_neg])

    claim = ClaimVersion(
        claim_id="clm-04",
        claim_version=1,
        claim_type="causal",
        statement="Compound X increases cellular apoptosis.",
        subject_surface="Compound X",
        relation_surface="increases",
        object_surface="cellular apoptosis",
        normalized_triple=NormalizedTriple(subject="urn:cx", predicate="increases", object="urn:ca"),
        polarity="affirmed",
        modality_strength="asserted"
    )

    assessment = gate.assess(claim, ev_set)
    assert assessment.state == "CONFLICTING"
    assert assessment.support is True
    assert assessment.refutation is True
    assert "Conflicting evidence atoms" in assessment.rationale
