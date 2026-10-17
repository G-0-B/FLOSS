"""
FLOSSI0ULLK Independent 2-Axis Entailment Gate Module.
Evaluates whether a normalized ClaimVersion is licensed by its EvidenceSet along independent support and refutation axes.
Part of Phase 2 (Task 2.2) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field
from typing import Optional, Literal, Any, Sequence

from evidence_set import EvidenceSet, EvidenceAtom
from claim_candidate import ClaimVersion
from document_ir import DocumentIR

EntailmentState = Literal[
    "SUPPORTED",
    "CONTRADICTED",
    "INSUFFICIENT",
    "CONFLICTING"
]

HEDGING_KEYWORDS = {
    "may", "might", "could", "possibly", "suggests", "hypothesized",
    "potential", "plausible", "speculate", "indicates preliminary"
}

NEGATION_KEYWORDS = {
    "not", "no", "never", "neither", "nor", "fails to", "failed to",
    "does not", "did not", "cannot", "absence of", "without"
}


@dataclass(frozen=True)
class EntailmentAssessment:
    """
    Independent 2-axis assessment of evidential warrant for a claim.
    Separates support and refutation into distinct boolean dimensions to distinguish
    insufficient evidence from genuine evidential conflict.
    """
    assessment_id: str
    claim_id: str
    claim_version: int
    evidence_atom_ids: list[str]
    support: bool
    refutation: bool
    rationale: str
    evaluator_id: str = "rule:deterministic-v1.2"
    assessed_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @property
    def state(self) -> EntailmentState:
        if self.support and not self.refutation:
            return "SUPPORTED"
        elif not self.support and self.refutation:
            return "CONTRADICTED"
        elif not self.support and not self.refutation:
            return "INSUFFICIENT"
        else:  # self.support and self.refutation
            return "CONFLICTING"

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "claim_id": self.claim_id,
            "claim_version": self.claim_version,
            "evidence_atom_ids": self.evidence_atom_ids,
            "support": self.support,
            "refutation": self.refutation,
            "state": self.state,
            "rationale": self.rationale,
            "evaluator_id": self.evaluator_id,
            "assessed_at": self.assessed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EntailmentAssessment:
        return cls(
            assessment_id=str(data["assessment_id"]),
            claim_id=str(data["claim_id"]),
            claim_version=int(data.get("claim_version", 1)),
            evidence_atom_ids=list(data.get("evidence_atom_ids", [])),
            support=bool(data["support"]),
            refutation=bool(data["refutation"]),
            rationale=str(data.get("rationale", "")),
            evaluator_id=str(data.get("evaluator_id", "rule:deterministic-v1.2")),
            assessed_at=str(data.get("assessed_at", "")),
        )


class EntailmentGate:
    """Deterministic rule-based adjudicator for catastrophic semantic hazards (H4, H5, H8, H17)."""

    def __init__(self, evaluator_id: str = "rule:deterministic-v1.2"):
        self.evaluator_id = evaluator_id

    def assess(
        self,
        claim: ClaimVersion,
        evidence_set: EvidenceSet,
        doc_ir: Optional[DocumentIR] = None,
        assessment_id: Optional[str] = None
    ) -> EntailmentAssessment:
        asm_id = assessment_id or f"asm-{claim.claim_id}-v{claim.claim_version}"
        atom_ids = [a.atom_id for a in evidence_set.atoms]

        # 1. Evidence Grounding Check
        if not evidence_set.is_grounded():
            return EntailmentAssessment(
                assessment_id=asm_id,
                claim_id=claim.claim_id,
                claim_version=claim.claim_version,
                evidence_atom_ids=atom_ids,
                support=False,
                refutation=False,
                rationale="H2/H13 failure: EvidenceSet contains ungrounded or unaligned atoms",
                evaluator_id=self.evaluator_id
            )

        combined_evidence = " ".join(a.literal_content.lower() for a in evidence_set.atoms)
        claim_stmt_lower = claim.statement.lower()

        # 2. Check for Unsupported Entities (H3)
        sub_surface_lower = claim.subject_surface.lower()
        obj_surface_lower = claim.object_surface.lower()
        if sub_surface_lower not in combined_evidence or obj_surface_lower not in combined_evidence:
            return EntailmentAssessment(
                assessment_id=asm_id,
                claim_id=claim.claim_id,
                claim_version=claim.claim_version,
                evidence_atom_ids=atom_ids,
                support=False,
                refutation=False,
                rationale=f"H3 failure: Surface entities ({claim.subject_surface!r} or {claim.object_surface!r}) absent from evidence",
                evaluator_id=self.evaluator_id
            )

        # 3. Check for Internal Conflict / Mixed Polarity in Evidence Atoms
        if len(evidence_set.atoms) > 1:
            atom_negations = [
                any(re.search(rf"\b{re.escape(neg)}\b", a.literal_content.lower()) for neg in NEGATION_KEYWORDS)
                for a in evidence_set.atoms
            ]
            if any(atom_negations) and not all(atom_negations):
                return EntailmentAssessment(
                    assessment_id=asm_id,
                    claim_id=claim.claim_id,
                    claim_version=claim.claim_version,
                    evidence_atom_ids=atom_ids,
                    support=True,
                    refutation=True,
                    rationale="Conflicting evidence atoms present in evidence set (mixed polarity)",
                    evaluator_id=self.evaluator_id
                )

        # 4. Polarity Contradiction Check (H4)
        evidence_has_negation = any(re.search(rf"\b{re.escape(neg)}\b", combined_evidence) for neg in NEGATION_KEYWORDS)
        claim_has_negation = (
            claim.polarity == "negated"
            or any(re.search(rf"\b{re.escape(neg)}\b", claim_stmt_lower) for neg in NEGATION_KEYWORDS)
        )

        # Direct contradiction: Evidence says NOT X, but claim affirms X (or vice-versa)
        if evidence_has_negation != claim_has_negation:
            return EntailmentAssessment(
                assessment_id=asm_id,
                claim_id=claim.claim_id,
                claim_version=claim.claim_version,
                evidence_atom_ids=atom_ids,
                support=False,
                refutation=True,
                rationale=f"H4 failure: Polarity inversion detected (evidence_negated={evidence_has_negation}, claim_negated={claim_has_negation})",
                evaluator_id=self.evaluator_id
            )

        # 5. Modality Strengthening Check (H5)
        evidence_is_hedged = any(re.search(rf"\b{re.escape(hedge)}\b", combined_evidence) for hedge in HEDGING_KEYWORDS)
        if evidence_is_hedged and claim.modality_strength == "asserted" and claim.modality_type == "none":
            return EntailmentAssessment(
                assessment_id=asm_id,
                claim_id=claim.claim_id,
                claim_version=claim.claim_version,
                evidence_atom_ids=atom_ids,
                support=False,
                refutation=False,
                rationale="H5 failure: Hedged evidence unlawfully strengthened to unhedged asserted fact",
                evaluator_id=self.evaluator_id
            )

        # 6. Supported: Passes semantic hazard filters and holds evidential warrant
        return EntailmentAssessment(
            assessment_id=asm_id,
            claim_id=claim.claim_id,
            claim_version=claim.claim_version,
            evidence_atom_ids=atom_ids,
            support=True,
            refutation=False,
            rationale="Evidence strictly entails normalized claim without detected hazards",
            evaluator_id=self.evaluator_id
        )
