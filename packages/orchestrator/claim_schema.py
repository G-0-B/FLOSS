"""
Claim / Vote / Decision schemas for the FLOSSI0ULLK Consensus Gate.

Implements the data model from docs/specs/consensus-gate.spec.md.
Dataclasses (not Pydantic) to match existing orchestrator style.
See docs/adr/ADR-6-four-system-integration.md for context.
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class ProposalType(str, Enum):
    """Category of change a Claim proposes (spec §4.1)."""

    CODE_CHANGE = "CodeChange"
    CONFIG_CHANGE = "ConfigChange"
    SPEC_CHANGE = "SpecChange"
    ADR_CHANGE = "AdrChange"
    OTHER = "Other"


class BlastRadius(str, Enum):
    """Scope of impact; drives quorum and override rules (spec §4.3)."""

    LOCAL = "Local"
    MODULE = "Module"
    SYSTEM = "System"
    SUBSTRATE = "Substrate"


class TruthStatus(str, Enum):
    """Truth-model label applied to Claims (spec §4.2). Claims submit as Unverified."""

    UNVERIFIED = "Unverified"
    SPECIFIED = "Specified"
    VERIFIED = "Verified"
    VALIDATED = "Validated"


class Outcome(str, Enum):
    """Terminal outcome of a Decision (spec §4.5)."""

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

EVIDENCE_TYPES: frozenset[str] = frozenset({"spec", "test", "adr", "url", "commit"})


def _utcnow_iso() -> str:
    """ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """Return a new UUID v7 string (INV-001, spec §3.1).

    Uses :func:`uuid.uuid7` when available (Python 3.14+) and falls back to an
    inline RFC 9562 §5.7 implementation otherwise. v7 is time-sortable, which
    the consensus gate relies on for ADR ordering.
    """
    uuid7 = getattr(uuid, "uuid7", None)
    if uuid7 is not None:
        return str(uuid7())
    # RFC 9562 §5.7 UUIDv7: 48-bit unix_ts_ms | 4-bit ver(0b0111) | 12-bit rand_a
    #                       | 2-bit var(0b10) | 62-bit rand_b
    ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    v = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return str(uuid.UUID(int=v))


@dataclass(frozen=True)
class EvidenceRef:
    """Typed reference to supporting evidence for a Claim (spec §4.1)."""

    type: str  # "spec" | "test" | "adr" | "url" | "commit"
    ref: str

    def validate(self) -> None:
        """Enforce a minimal provenance shape for supporting evidence."""
        if not isinstance(self.type, str) or not self.type.strip():
            raise ValueError("E_EVIDENCE_INVALID_SCHEMA: evidence.type required")
        if self.type not in EVIDENCE_TYPES:
            raise ValueError(
                "E_EVIDENCE_INVALID_SCHEMA: evidence.type must be one of "
                + ", ".join(sorted(EVIDENCE_TYPES))
            )
        if not isinstance(self.ref, str) or not self.ref.strip():
            raise ValueError("E_EVIDENCE_INVALID_SCHEMA: evidence.ref required")


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

    def _validate_evidence(self) -> None:
        """Reject malformed evidence payloads before routing or serialization."""
        if not isinstance(self.evidence, list):
            raise ValueError("E_CLAIM_INVALID_SCHEMA: evidence must be a list")
        for idx, evidence in enumerate(self.evidence):
            if not isinstance(evidence, EvidenceRef):
                raise ValueError(
                    f"E_CLAIM_INVALID_SCHEMA: evidence[{idx}] must be an EvidenceRef"
                )
            try:
                evidence.validate()
            except ValueError as exc:
                raise ValueError(
                    f"E_CLAIM_INVALID_SCHEMA: evidence[{idx}] is invalid"
                ) from exc

    def validate(self) -> None:
        """Enforce spec invariants INV-001 through INV-005.

        Checks type/format of wire-format fields (id, submitted_at, enums) before
        checking content invariants, so bad inputs fail fast rather than leaking
        into QUORUM_MIN / .value / ADR-filename construction downstream.
        """
        # INV-001 (spec §3.1): id MUST be a valid UUID v7 (time-sortable).
        try:
            claim_uuid = uuid.UUID(self.id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError("E_CLAIM_INVALID_SCHEMA: id must be a valid UUID") from exc
        if claim_uuid.version != 7:
            raise ValueError(
                f"E_CLAIM_INVALID_SCHEMA: id must be UUID v7, got v{claim_uuid.version}"
            )
        if not isinstance(self.proposal_type, ProposalType):
            raise ValueError(
                "E_CLAIM_INVALID_SCHEMA: proposal_type must be a ProposalType member"
            )
        if not isinstance(self.blast_radius, BlastRadius):
            raise ValueError(
                "E_CLAIM_INVALID_SCHEMA: blast_radius must be a BlastRadius member"
            )
        try:
            datetime.fromisoformat(self.submitted_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                "E_CLAIM_INVALID_SCHEMA: submitted_at must be ISO 8601"
            ) from exc
        if not self.proposer:
            raise ValueError("E_CLAIM_INVALID_SCHEMA: proposer required")
        if not (1 <= len(self.summary) <= 200):
            raise ValueError("E_CLAIM_INVALID_SCHEMA: summary must be 1..200 chars")
        if not self.body:
            raise ValueError("E_CLAIM_INVALID_SCHEMA: body required")
        self._validate_evidence()
        if self.truth_status != TruthStatus.UNVERIFIED:
            raise ValueError(
                "E_CLAIM_INVALID_SCHEMA: truth_status must be Unverified on submission"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Claim to a plain dict (enums rendered as their .value strings)."""
        self.validate()
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
        if isinstance(self.vote, bool) or not isinstance(self.vote, int):
            raise ValueError(f"E_VOTE_INVALID_RANGE: {self.vote} not in (-1, 0, +1)")
        if self.vote not in (-1, 0, 1):
            raise ValueError(f"E_VOTE_INVALID_RANGE: {self.vote} not in (-1, 0, +1)")
        if not self.voter:
            raise ValueError("E_VOTE_INVALID_SCHEMA: voter required")
        if not (1 <= len(self.rationale) <= 1000):
            raise ValueError("E_VOTE_INVALID_SCHEMA: rationale must be 1..1000 chars")

    def to_dict(self) -> dict[str, Any]:
        """Serialize Vote to a plain dict."""
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
        """Enforce wire-format invariants before serializing or storing a decision."""
        try:
            claim_uuid = uuid.UUID(self.claim_id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise ValueError(
                "E_DECISION_INVALID_SCHEMA: claim_id must be a valid UUID"
            ) from exc
        if claim_uuid.version != 7:
            raise ValueError(
                f"E_DECISION_INVALID_SCHEMA: claim_id must be UUID v7, got v{claim_uuid.version}"
            )
        if not isinstance(self.outcome, Outcome):
            raise ValueError(
                "E_DECISION_INVALID_SCHEMA: outcome must be an Outcome member"
            )
        if not isinstance(self.votes, list):
            raise ValueError("E_DECISION_INVALID_SCHEMA: votes must be a list")
        for idx, vote in enumerate(self.votes):
            if not isinstance(vote, Vote):
                raise ValueError(
                    f"E_DECISION_INVALID_SCHEMA: votes[{idx}] must be a Vote"
                )
            vote.validate()
        try:
            datetime.fromisoformat(self.decided_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as exc:
            raise ValueError(
                "E_DECISION_INVALID_SCHEMA: decided_at must be ISO 8601"
            ) from exc
        if self.outcome == Outcome.OVERRIDDEN and not self.override_by:
            raise ValueError("E_OVERRIDE_NOT_HUMAN: OVERRIDDEN requires override_by")
        if self.outcome != Outcome.OVERRIDDEN and self.override_by is not None:
            raise ValueError(
                "E_DECISION_INVALID_SCHEMA: override_by only allowed for OVERRIDDEN"
            )

    def to_dict(self) -> dict[str, Any]:
        """Serialize Decision to a plain dict (outcome as .value; optional fields omitted when None)."""
        self.validate()
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
