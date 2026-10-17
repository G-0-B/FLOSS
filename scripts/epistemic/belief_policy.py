"""
FLOSSI0ULLK Deterministic Belief Update Policy.
Maps EntailmentAssessments to updated or retracted BeliefStates, emitting append-only ledger events.
Part of Phase 2 (Task 2.3) of local-ingestion-semantic-extraction-pipeline v1.2.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional, Literal, Any

from .event_ledger import EpistemicEvent, create_epistemic_event
from entailment_gate import EntailmentAssessment
from claim_candidate import ClaimVersion

BeliefDisposition = Literal[
    "ACTIVE_BELIEF",
    "PROVISIONAL",
    "SUSPENDED",
    "CONTRADICTED",
    "SUPERSEDED",
    "RETRACTED"
]


@dataclass
class BeliefState:
    """Time-indexed epistemic status and analog confidence for a claim."""
    claim_id: str
    claim_version: int
    disposition: BeliefDisposition
    signed_confidence: float  # in [-0.999, +0.999] per ADR-10
    active: bool
    last_assessment_id: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_version": self.claim_version,
            "disposition": self.disposition,
            "signed_confidence": self.signed_confidence,
            "active": self.active,
            "last_assessment_id": self.last_assessment_id,
            "updated_at": self.updated_at,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BeliefState:
        return cls(
            claim_id=str(data["claim_id"]),
            claim_version=int(data.get("claim_version", 1)),
            disposition=data.get("disposition", "PROVISIONAL"),
            signed_confidence=float(data.get("signed_confidence", 0.0)),
            active=bool(data.get("active", False)),
            last_assessment_id=data.get("last_assessment_id"),
            updated_at=str(data.get("updated_at", "")),
            rationale=str(data.get("rationale", "")),
        )


class BeliefUpdatePolicy:
    """Deterministic policy governing belief updates from entailment assessments."""

    POLICY_ID = "policy:belief-update-v1.2"
    POLICY_HASH = "v1.2.0-deterministic-agm"

    def apply_assessment(
        self,
        current_state: Optional[BeliefState],
        claim: ClaimVersion,
        assessment: EntailmentAssessment
    ) -> tuple[BeliefState, EpistemicEvent]:
        """
        Transitions the claim's epistemic belief state based on the 2-axis assessment,
        emitting a content-addressed BELIEF_REVISED event.
        """
        now_ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state = assessment.state

        if state == "SUPPORTED":
            new_disposition: BeliefDisposition = "ACTIVE_BELIEF"
            confidence = 0.850
            is_active = True
            rat = f"Supported by evidence atoms: {', '.join(assessment.evidence_atom_ids)}"
        elif state == "CONTRADICTED":
            new_disposition = "CONTRADICTED"
            confidence = -0.900
            is_active = False
            rat = f"Refuted by evidence: {assessment.rationale}"
        elif state == "CONFLICTING":
            new_disposition = "SUSPENDED"
            confidence = 0.000
            is_active = False
            rat = f"Evidential conflict detected: {assessment.rationale}"
        else:  # INSUFFICIENT
            new_disposition = "SUSPENDED"
            confidence = 0.000
            is_active = False
            rat = f"Insufficient evidential warrant: {assessment.rationale}"

        new_belief = BeliefState(
            claim_id=claim.claim_id,
            claim_version=claim.claim_version,
            disposition=new_disposition,
            signed_confidence=confidence,
            active=is_active,
            last_assessment_id=assessment.assessment_id,
            updated_at=now_ts,
            rationale=rat
        )

        prev_id = f"belief:{claim.claim_id}@v{current_state.claim_version}" if current_state else "belief:initial"
        curr_id = f"belief:{claim.claim_id}@v{claim.claim_version}"

        event = create_epistemic_event(
            event_type="BELIEF_REVISED",
            actor=self.POLICY_ID,
            inputs=[f"claim:{claim.claim_id}@v{claim.claim_version}", f"assessment:{assessment.assessment_id}", prev_id],
            outputs=[curr_id],
            policy_hash=self.POLICY_HASH,
            rationale_refs=assessment.evidence_atom_ids,
            authority_tier="non_authoritative",
            payload={"disposition": new_disposition, "signed_confidence": confidence, "state": state},
            occurred_at=now_ts
        )

        return new_belief, event
