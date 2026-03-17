"""
Data models for LLM committee validation system.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime
from enum import Enum


class VoteDecision(Enum):
    """Validator vote decision."""
    YES = "YES"
    NO = "NO"
    ABSTAIN = "ABSTAIN"


@dataclass
class Vote:
    """Individual validator's vote on a triple."""
    validator_id: str
    decision: VoteDecision
    confidence: float  # 0.0-1.0
    reasoning: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        """Validate vote data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if isinstance(self.decision, str):
            self.decision = VoteDecision(self.decision)


@dataclass
class ValidationResult:
    """Result of committee validation for a triple."""
    accepted: bool
    confidence: float  # 0.0-1.0, mean confidence of YES votes
    votes: List[Vote]
    consensus_ratio: float  # Ratio of agreeing votes
    total_votes: int
    yes_votes: int
    no_votes: int
    abstain_votes: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    duration_ms: Optional[float] = None  # Validation duration in milliseconds

    @property
    def has_consensus(self) -> bool:
        """Check if validation achieved consensus (≥3/5)."""
        return self.yes_votes >= 3

    @property
    def is_unanimous(self) -> bool:
        """Check if all validators agreed."""
        return self.yes_votes == self.total_votes or self.no_votes == self.total_votes

    @property
    def mean_confidence(self) -> float:
        """Calculate mean confidence across all votes."""
        if not self.votes:
            return 0.0
        return sum(v.confidence for v in self.votes) / len(self.votes)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'accepted': self.accepted,
            'confidence': self.confidence,
            'consensus_ratio': self.consensus_ratio,
            'total_votes': self.total_votes,
            'yes_votes': self.yes_votes,
            'no_votes': self.no_votes,
            'abstain_votes': self.abstain_votes,
            'timestamp': self.timestamp,
            'duration_ms': self.duration_ms,
            'has_consensus': self.has_consensus,
            'is_unanimous': self.is_unanimous,
            'mean_confidence': self.mean_confidence,
            'votes': [
                {
                    'validator_id': v.validator_id,
                    'decision': v.decision.value,
                    'confidence': v.confidence,
                    'reasoning': v.reasoning,
                    'timestamp': v.timestamp
                }
                for v in self.votes
            ]
        }


@dataclass
class ValidatorConfig:
    """Configuration for a validator agent."""
    validator_id: str
    model_name: str = "claude-3-5-sonnet-20241022"  # Default to Sonnet
    temperature: float = 0.3  # Lower temperature for more consistent validation
    max_tokens: int = 500
    use_mock: bool = False  # Use mock LLM for testing
    timeout_seconds: float = 10.0

    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {self.temperature}")


@dataclass
class ConsensusMetrics:
    """Metrics tracking committee validation performance."""
    total_validations: int = 0
    accepted: int = 0
    rejected: int = 0
    consensus_achieved: int = 0
    unanimous_decisions: int = 0
    mean_confidence: float = 0.0
    mean_duration_ms: float = 0.0
    false_positives: int = 0  # Tracked if ground truth available
    false_negatives: int = 0  # Tracked if ground truth available

    @property
    def acceptance_rate(self) -> float:
        """Calculate acceptance rate."""
        if self.total_validations == 0:
            return 0.0
        return self.accepted / self.total_validations

    @property
    def consensus_rate(self) -> float:
        """Calculate consensus achievement rate."""
        if self.total_validations == 0:
            return 0.0
        return self.consensus_achieved / self.total_validations

    @property
    def unanimity_rate(self) -> float:
        """Calculate unanimous decision rate."""
        if self.total_validations == 0:
            return 0.0
        return self.unanimous_decisions / self.total_validations

    @property
    def false_positive_rate(self) -> float:
        """Calculate false positive rate (if ground truth available)."""
        total_negatives = self.rejected + self.false_positives
        if total_negatives == 0:
            return 0.0
        return self.false_positives / total_negatives

    @property
    def false_negative_rate(self) -> float:
        """Calculate false negative rate (if ground truth available)."""
        total_positives = self.accepted + self.false_negatives
        if total_positives == 0:
            return 0.0
        return self.false_negatives / total_positives

    def update(self, result: ValidationResult):
        """Update metrics with a new validation result."""
        self.total_validations += 1

        if result.accepted:
            self.accepted += 1
        else:
            self.rejected += 1

        if result.has_consensus:
            self.consensus_achieved += 1

        if result.is_unanimous:
            self.unanimous_decisions += 1

        # Update running mean confidence
        self.mean_confidence = (
            (self.mean_confidence * (self.total_validations - 1) + result.confidence)
            / self.total_validations
        )

        # Update running mean duration
        if result.duration_ms:
            self.mean_duration_ms = (
                (self.mean_duration_ms * (self.total_validations - 1) + result.duration_ms)
                / self.total_validations
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'total_validations': self.total_validations,
            'accepted': self.accepted,
            'rejected': self.rejected,
            'consensus_achieved': self.consensus_achieved,
            'unanimous_decisions': self.unanimous_decisions,
            'mean_confidence': self.mean_confidence,
            'mean_duration_ms': self.mean_duration_ms,
            'acceptance_rate': self.acceptance_rate,
            'consensus_rate': self.consensus_rate,
            'unanimity_rate': self.unanimity_rate,
            'false_positive_rate': self.false_positive_rate,
            'false_negative_rate': self.false_negative_rate,
        }
