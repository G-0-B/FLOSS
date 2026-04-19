"""
Agent Pool for Validation Committee.
Manages a pool of LLM agents that can act as validators.
"""

from typing import List
from dataclasses import dataclass
import random


@dataclass
class ValidatorResponse:
    """Response from a single validator."""

    agent_id: str
    approved: bool
    confidence: float
    reasoning: str


class Validator:
    """Abstract base class for a validator agent."""

    def __init__(self, agent_id: str, model: str):
        self.agent_id = agent_id
        self.model = model

    async def validate_triple(self, triple: tuple, context: str) -> ValidatorResponse:
        """Validates a triple against the context."""
        raise NotImplementedError


class MockValidator(Validator):
    """A mock validator for testing purposes."""

    async def validate_triple(self, triple: tuple, context: str) -> ValidatorResponse:
        """Simulates validation with random or deterministic logic."""
        # Deterministic mock logic for testing
        subject, predicate, obj = triple

        # Simulate rejection of "nonsense"
        if (
            "nonsense" in subject.lower()
            or "nonsense" in obj.lower()
            or "nonsense" in context.lower()
        ):
            return ValidatorResponse(
                agent_id=self.agent_id,
                approved=False,
                confidence=0.9,
                reasoning="Detected nonsense content.",
            )

        # Simulate rejection of unknown predicates (redundant with basic check but good for testing)
        if predicate == "unknown_predicate":
            return ValidatorResponse(
                agent_id=self.agent_id,
                approved=False,
                confidence=0.95,
                reasoning="Unknown predicate.",
            )

        # Default approval
        return ValidatorResponse(
            agent_id=self.agent_id,
            approved=True,
            confidence=0.8 + (random.random() * 0.15),
            reasoning="Triple appears consistent with context.",
        )


class ValidatorPool:
    """Manages a pool of validators."""

    def __init__(self, use_mock: bool = True):
        self.validators: List[Validator] = []
        if use_mock:
            self._init_mock_pool()

    def _init_mock_pool(self):
        """Initializes a diverse pool of mock validators."""
        self.validators = [
            MockValidator("validator-1", "mock-gpt-4"),
            MockValidator("validator-2", "mock-claude-3"),
            MockValidator("validator-3", "mock-llama-3"),
            MockValidator("validator-4", "mock-mistral"),
            MockValidator("validator-5", "mock-gemini"),
        ]

    def get_committee(self, size: int = 3) -> List[Validator]:
        """Selects a random committee of validators."""
        if size > len(self.validators):
            size = len(self.validators)
        return random.sample(self.validators, size)
