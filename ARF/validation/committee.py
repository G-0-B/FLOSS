"""
Committee Validation Logic.
Orchestrates the voting process for knowledge triples.
"""

import asyncio
from typing import List, Tuple, Dict
from dataclasses import dataclass, asdict
import logging

from .agent_pool import ValidatorPool, ValidatorResponse

logger = logging.getLogger(__name__)


@dataclass
class CommitteeResult:
    """Result of a committee vote."""

    accepted: bool
    yes_votes: int
    no_votes: int
    total_votes: int
    confidence: float
    reasoning: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


class TripleValidationCommittee:
    """
    A committee of LLM agents that validates knowledge triples.
    Uses a consensus mechanism (e.g., majority vote) to accept or reject triples.
    """

    def __init__(
        self, pool_size: int = 5, committee_size: int = 3, use_mock: bool = True
    ):
        self.pool = ValidatorPool(use_mock=use_mock)
        self.committee_size = committee_size
        logger.info(f"Initialized TripleValidationCommittee (size={committee_size})")

    async def validate(
        self, triple: Tuple[str, str, str], context: str
    ) -> CommitteeResult:
        """
        Validates a triple by polling a committee of validators.

        Args:
            triple: The (subject, predicate, object) tuple.
            context: The context string.

        Returns:
            A CommitteeResult object.
        """
        committee = self.pool.get_committee(self.committee_size)

        # Run validations concurrently
        tasks = [v.validate_triple(triple, context) for v in committee]
        responses: List[ValidatorResponse] = await asyncio.gather(*tasks)

        # Tally votes
        yes_votes = 0
        no_votes = 0
        total_confidence = 0.0
        reasons = []

        for r in responses:
            if r.approved:
                yes_votes += 1
            else:
                no_votes += 1
            total_confidence += r.confidence
            reasons.append(f"{r.agent_id}: {r.reasoning}")

        # Consensus logic: Simple majority for now
        # In production, could use supermajority (e.g. 2/3)
        threshold = self.committee_size / 2
        accepted = yes_votes > threshold

        avg_confidence = total_confidence / len(responses) if responses else 0.0

        return CommitteeResult(
            accepted=accepted,
            yes_votes=yes_votes,
            no_votes=no_votes,
            total_votes=len(responses),
            confidence=avg_confidence,
            reasoning=reasons,
        )
