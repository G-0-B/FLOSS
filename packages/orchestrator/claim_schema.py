"""
Claim / Vote / Decision schemas for the FLOSSI0ULLK Consensus Gate.

Implements the data model from docs/specs/consensus-gate.spec.md.
Dataclasses (not Pydantic) to match existing orchestrator style.
See docs/adr/ADR-6-four-system-integration.md for context.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ProposalType(str, Enum):
    CODE_CHANGE = "CodeChange"
    CONFIG_CHANGE = "ConfigChange"
    SPEC_CHANGE = "SpecChange"
    ADR_CHANGE = "AdrChange"
    OTHER = "Other"


class BlastRadius(str, Enum):
    LOCAL = "Local"
    MODULE = "Module"
    SYSTEM = "System"
    SUBSTRATE = "Substrate"


class TruthStatus(str, Enum):
    UNVERIFIED = "Unverified"
    SPECIFIED = "Specified"
    VERIFIED = "Verified"
    VALIDATED = "Validated"


class Outcome(str, Enum):
    APPROVED = "APPROVED"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"


# Quorum minimums per blast radius (from spec §4.3)
QUORUM_MIN: dict[BlastRadius, int] = {
    BlastRadius.LOCAL: 1,
    BlastRadius.MODULE: 2,
    BlastRadius.SYSTEM: 3,
    BlastRadius.SUBSTRATE: 3,
}

# Whether human override is permitted per blast radius (from spec §4.3)
OVERRIDE_ALLOWED: dict[BlastRadius, bool] = {
    BlastRadius.LOCAL: True,
    BlastRadius.MODULE: True,
    BlastRadius.SYSTEM: True,
    BlastRadius.SUBSTRATE: False,
}


def _utcnow_iso() -> str:
    """ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """UUID v4 (v7 stdlib support lands in Py 3.14). Still unique + time-correlated enough."""
    return str(uuid.uuid4())


@dataclass(frozen=True)
class EvidenceRef:
    type: str  # "spec" | "test" | "adr" | "url" | "commit"
    ref: str


@dataclass
class Claim:
    """A proposed change submitted to the consensus gate."""

    proposer: str
    proposal_type: ProposalType
    summary: str
    body: str
    blast_radius: BlastRadius
    evidence: list[EvidenceRef] = field(default_factory=list)
    truth_status: TruthStatus = TruthStatus.UNVERIFIED
    id: str = field(default_factory=_new_id)
    submitted_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Enforce spec invariants INV-001 through INV-005."""
        if not self.proposer:
            raise ValueError("E_CLAIM_INVALID_SCHEMA: proposer required")
        if not (1 <= len(self.summary) <= 200):
            raise ValueError("E_CLAIM_INVALID_SCHEMA: summary must be 1..200 chars")
        if not self.body:
            raise ValueError("E_CLAIM_INVALID_SCHEMA: body required")
        if self.truth_status != TruthStatus.UNVERIFIED:
            raise ValueError(
                "E_CLAIM_INVALID_SCHEMA: truth_status must be Unverified on submission"
            )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["proposal_type"] = self.proposal_type.value
        d["blast_radius"] = self.blast_radius.value
        d["truth_status"] = self.truth_status.value
        return d


@dataclass
class Vote:
    """A single voter's ternary evaluation of a Claim."""

    voter: str
    vote: int  # -1, 0, +1
    rationale: str
    voted_at: str = field(default_factory=_utcnow_iso)

    def validate(self) -> None:
        """Enforce spec invariants INV-002, INV-005."""
        if self.vote not in (-1, 0, 1):
            raise ValueError(f"E_VOTE_INVALID_RANGE: {self.vote} not in (-1, 0, +1)")
        if not self.voter:
            raise ValueError("E_VOTE_INVALID_SCHEMA: voter required")
        if not (1 <= len(self.rationale) <= 1000):
            raise ValueError("E_VOTE_INVALID_SCHEMA: rationale must be 1..1000 chars")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Decision:
    """Aggregated outcome of all Votes for a Claim."""

    claim_id: str
    outcome: Outcome
    votes: list[Vote]
    decided_at: str = field(default_factory=_utcnow_iso)
    adr_ref: Optional[str] = None
    override_by: Optional[str] = None

    def validate(self) -> None:
        """Enforce spec invariant INV-009."""
        if self.outcome == Outcome.OVERRIDDEN and not self.override_by:
            raise ValueError("E_OVERRIDE_NOT_HUMAN: OVERRIDDEN requires override_by")

    def to_dict(self) -> dict[str, Any]:
        d = {
            "claim_id": self.claim_id,
            "outcome": self.outcome.value,
            "votes": [v.to_dict() for v in self.votes],
            "decided_at": self.decided_at,
        }
        if self.adr_ref is not None:
            d["adr_ref"] = self.adr_ref
        if self.override_by is not None:
            d["override_by"] = self.override_by
        return d
