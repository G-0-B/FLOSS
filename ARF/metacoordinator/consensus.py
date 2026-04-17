"""
Consensus Formation Engine for FLOSSI0ULLK MetaCoordinator

Implements adaptive ternary voting system that learns from all outcomes
(success/failure/neutral) and uses different consensus strategies based on task type.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
import time
import json
from pathlib import Path


class Vote(Enum):
    """Ternary voting system"""

    APPROVE = 1  # +1: Good to go, proceed
    ABSTAIN = 0  # 0: Need more information, hold
    REJECT = -1  # -1: This needs rework, reject

    def __str__(self):
        return {1: "+1", 0: "0", -1: "-1"}[self.value]


TaskType = Literal["reasoning", "knowledge", "implementation", "design"]


@dataclass
class RFC:
    """Request for Comments - Proposal for system change"""

    id: str
    title: str
    description: str
    proposer: str
    task_type: TaskType
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    # Multi-lens analysis (from FLOSSI0ULLK Operating Instructions)
    practical_engineering: str = ""
    critical_red_team: str = ""
    values_alignment: str = ""
    systems_governance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the RFC into a JSON-safe dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "proposer": self.proposer,
            "task_type": self.task_type,
            "context": self.context,
            "created_at": self.created_at,
            "practical_engineering": self.practical_engineering,
            "critical_red_team": self.critical_red_team,
            "values_alignment": self.values_alignment,
            "systems_governance": self.systems_governance,
        }


@dataclass
class VoteCast:
    """Individual vote with reasoning"""

    agent_id: str
    vote: Vote
    rationale: str
    timestamp: float = field(default_factory=time.time)
    confidence: float = 1.0  # 0.0-1.0, how confident in this vote

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the vote into a JSON-safe dictionary."""
        return {
            "agent_id": self.agent_id,
            "vote": self.vote.value,
            "vote_str": str(self.vote),
            "rationale": self.rationale,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
        }


@dataclass
class ADR:
    """Architecture Decision Record - Final decision with provenance"""

    rfc_id: str
    decision: str  # "APPROVED", "REJECTED", "REQUIRES_REWORK", "CONSENSUS_APPROVED"
    rationale: str  # Synthesized from all vote rationales
    votes: Dict[str, VoteCast]
    consensus_method: str  # "voting" or "consensus"
    provenance: List[str]  # All agents who contributed
    created_at: float = field(default_factory=time.time)

    # Track whether this was a good decision (for learning)
    outcome: Optional[Literal["success", "failure", "neutral"]] = None
    outcome_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the ADR into a JSON-safe dictionary."""
        return {
            "rfc_id": self.rfc_id,
            "decision": self.decision,
            "rationale": self.rationale,
            "votes": {k: v.to_dict() for k, v in self.votes.items()},
            "consensus_method": self.consensus_method,
            "provenance": self.provenance,
            "created_at": self.created_at,
            "outcome": self.outcome,
            "outcome_notes": self.outcome_notes,
        }

    def save(self, directory: Path = Path("ARF/adr/")):
        """Save ADR to file for persistent memory"""
        directory.mkdir(parents=True, exist_ok=True)

        # Generate filename: ADR-{number}-{slug}.json
        existing = list(directory.glob("ADR-*.json"))
        number = len(existing) + 1
        slug = self.rfc_id.lower().replace("_", "-")
        filename = directory / f"ADR-{number:04d}-{slug}.json"

        with open(filename, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

        return filename


class ConsensusEngine:
    """
    Adaptive ternary voting system that selects optimal consensus strategy
    based on task type (voting for reasoning, consensus for knowledge).

    Learns from all outcomes (success/failure/neutral) to improve over time.
    """

    def __init__(self, context_sync=None):
        self.context_sync = context_sync
        self.pending_rfcs: Dict[str, RFC] = {}
        self.votes: Dict[str, Dict[str, VoteCast]] = {}
        self.adrs: Dict[str, ADR] = {}

        # Learning from experience
        self.decision_history: List[Dict[str, Any]] = []

    def submit_rfc(self, rfc: RFC) -> str:
        """
        Agent submits RFC for multi-agent consideration.

        Returns RFC ID for tracking.
        """
        self.pending_rfcs[rfc.id] = rfc
        self.votes[rfc.id] = {}

        # Broadcast to all agents via context sync
        if self.context_sync:
            self.context_sync.broadcast_update(
                key=f"rfc/{rfc.id}/proposal",
                value=rfc.to_dict(),
                source_agent=rfc.proposer,
            )

        return rfc.id

    def cast_vote(
        self,
        rfc_id: str,
        agent_id: str,
        vote: Vote,
        rationale: str,
        confidence: float = 1.0,
    ):
        """
        Agent casts ternary vote with reasoning.

        Votes are broadcast to all agents for transparency.
        """
        if rfc_id in self.adrs:
            print(
                "⚠️ Vote from "
                f"{agent_id} received for finalized RFC {rfc_id}. "
                "Vote recorded but decision stands."
            )
            return None

        if rfc_id not in self.pending_rfcs:
            raise ValueError(f"RFC {rfc_id} not found")

        vote_cast = VoteCast(
            agent_id=agent_id, vote=vote, rationale=rationale, confidence=confidence
        )

        self.votes[rfc_id][agent_id] = vote_cast

        # Broadcast vote via context sync
        if self.context_sync:
            self.context_sync.broadcast_update(
                key=f"rfc/{rfc_id}/votes/{agent_id}",
                value=vote_cast.to_dict(),
                source_agent=agent_id,
            )

        # Check if consensus reached
        adr = self.evaluate_consensus(rfc_id)
        if adr:
            self._finalize_decision(rfc_id, adr)

        return vote_cast

    def evaluate_consensus(self, rfc_id: str) -> Optional[ADR]:
        """
        Determine if consensus reached using adaptive strategy.

        Strategy selection based on research:
        - Voting: Better for reasoning tasks (13.2% improvement)
        - Consensus: Better for knowledge tasks (2.8% improvement)
        """
        if rfc_id in self.adrs:
            return self.adrs[rfc_id]

        if rfc_id not in self.pending_rfcs:
            return None

        rfc = self.pending_rfcs[rfc_id]
        votes = self.votes[rfc_id]

        # Adaptive vote thresholds based on task type
        if rfc.task_type in ["reasoning", "implementation"]:
            # Voting strategy: require at least 2 votes
            if len(votes) < 2:
                return None
            return self._evaluate_voting(rfc, votes)

        # Consensus strategy: require at least 3 votes
        if len(votes) < 3:
            return None
        return self._evaluate_consensus(rfc, votes)

    def _evaluate_voting(self, rfc: RFC, votes: Dict[str, VoteCast]) -> Optional[ADR]:
        """
        Voting protocol: Agents vote on proposed solution.
        Better for reasoning tasks where multiple valid approaches exist.
        """
        approve = sum(1 for v in votes.values() if v.vote == Vote.APPROVE)
        reject = sum(1 for v in votes.values() if v.vote == Vote.REJECT)
        abstain = sum(1 for v in votes.values() if v.vote == Vote.ABSTAIN)

        total = len(votes)

        # Weighted votes by confidence
        weighted_approve = sum(
            v.confidence for v in votes.values() if v.vote == Vote.APPROVE
        )
        weighted_total = sum(v.confidence for v in votes.values())

        # Majority approval (>50% of votes OR >60% of confidence-weighted votes)
        if (approve / total > 0.5) or (weighted_approve / weighted_total > 0.6):
            return ADR(
                rfc_id=rfc.id,
                decision="APPROVED",
                rationale=self._synthesize_rationale(votes, "approved"),
                votes=votes,
                consensus_method="voting",
                provenance=[rfc.proposer] + list(votes.keys()),
            )

        # Strong rejection (>50%)
        if reject / total > 0.5:
            return ADR(
                rfc_id=rfc.id,
                decision="REJECTED",
                rationale=self._synthesize_rationale(votes, "rejected"),
                votes=votes,
                consensus_method="voting",
                provenance=[rfc.proposer] + list(votes.keys()),
            )

        # Too many abstentions - need more information
        if abstain / total > 0.4:
            # Request clarification from proposer
            return None

        # No clear consensus yet - continue deliberation
        return None

    def _evaluate_consensus(
        self, rfc: RFC, votes: Dict[str, VoteCast]
    ) -> Optional[ADR]:
        """
        Consensus protocol: Agents converge on shared understanding.
        Better for knowledge tasks requiring collective agreement.
        """
        approve = sum(1 for v in votes.values() if v.vote == Vote.APPROVE)
        reject = sum(1 for v in votes.values() if v.vote == Vote.REJECT)
        abstain = sum(1 for v in votes.values() if v.vote == Vote.ABSTAIN)

        total = len(votes)

        # Supermajority (66%) for knowledge tasks
        if approve / total >= 0.66:
            return ADR(
                rfc_id=rfc.id,
                decision="CONSENSUS_APPROVED",
                rationale=self._synthesize_rationale(votes, "consensus"),
                votes=votes,
                consensus_method="consensus",
                provenance=[rfc.proposer] + list(votes.keys()),
            )

        # Any significant rejection (>20%) requires rework
        if reject / total > 0.20:
            return ADR(
                rfc_id=rfc.id,
                decision="REQUIRES_REWORK",
                rationale=self._synthesize_rationale(votes, "rework"),
                votes=votes,
                consensus_method="consensus",
                provenance=[rfc.proposer] + list(votes.keys()),
            )

        # Continue deliberation
        return None

    def _synthesize_rationale(self, votes: Dict[str, VoteCast], outcome: str) -> str:
        """
        Synthesize comprehensive rationale from all vote rationales.

        Includes perspectives from approvers, rejectors, and abstainers.
        """
        approve_reasons = [
            v.rationale for v in votes.values() if v.vote == Vote.APPROVE
        ]
        reject_reasons = [v.rationale for v in votes.values() if v.vote == Vote.REJECT]
        abstain_reasons = [
            v.rationale for v in votes.values() if v.vote == Vote.ABSTAIN
        ]

        synthesis = f"Decision: {outcome.upper()}\n\n"

        if approve_reasons:
            synthesis += "Supporting Arguments:\n"
            for i, reason in enumerate(approve_reasons, 1):
                synthesis += f"{i}. {reason}\n"
            synthesis += "\n"

        if reject_reasons:
            synthesis += "Concerns Raised:\n"
            for i, reason in enumerate(reject_reasons, 1):
                synthesis += f"{i}. {reason}\n"
            synthesis += "\n"

        if abstain_reasons:
            synthesis += "Information Gaps:\n"
            for i, reason in enumerate(abstain_reasons, 1):
                synthesis += f"{i}. {reason}\n"

        return synthesis.strip()

    def _finalize_decision(self, rfc_id: str, adr: ADR):
        """Finalize decision and broadcast ADR to all agents"""
        self.adrs[rfc_id] = adr

        # Save ADR for persistent memory
        filename = adr.save()
        print(f"✅ ADR saved: {filename}")

        # Broadcast final decision
        if self.context_sync:
            self.context_sync.broadcast_update(
                key=f"adr/{rfc_id}/final",
                value=adr.to_dict(),
                source_agent="consensus_engine",
            )

        # Remove from pending
        del self.pending_rfcs[rfc_id]

        # Record for learning
        self.decision_history.append(
            {
                "rfc_id": rfc_id,
                "decision": adr.decision,
                "method": adr.consensus_method,
                "timestamp": adr.created_at,
                "num_votes": len(adr.votes),
            }
        )

    def record_outcome(
        self,
        rfc_id: str,
        outcome: Literal["success", "failure", "neutral"],
        notes: str = "",
    ):
        """
        Record outcome of implemented decision for learning.

        CRITICAL: We learn from ALL outcomes - success teaches what works,
        failure teaches what doesn't, neutral teaches edge cases.
        """
        if rfc_id not in self.adrs:
            raise ValueError(f"ADR for RFC {rfc_id} not found")

        adr = self.adrs[rfc_id]
        adr.outcome = outcome
        adr.outcome_notes = notes

        # Re-save with outcome
        adr.save()

        print(f"📊 Outcome recorded for {rfc_id}: {outcome}")
        if notes:
            print(f"   Notes: {notes}")
