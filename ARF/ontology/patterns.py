"""
Pattern Library for ARF.
Defines standard interaction patterns and logic to match them.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class InteractionPattern:
    """
    Represents a reusable interaction pattern.
    """

    name: str
    description: str
    structure: List[str]  # Steps or phases of the pattern
    keywords: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "structure": self.structure,
            "keywords": self.keywords,
        }


# Standard Patterns Registry
SOCRATIC_METHOD = InteractionPattern(
    name="Socratic Method",
    description="A form of cooperative argumentative dialogue between individuals, based on asking and answering questions to stimulate critical thinking.",
    structure=[
        "Teacher asks a probing question.",
        "Student provides an initial answer.",
        "Teacher asks a follow-up question exposing a contradiction or gap.",
        "Student refines the answer.",
        "Cycle repeats until insight is reached.",
    ],
    keywords=["why", "how", "define", "example", "contradiction", "suppose"],
)

DEBATE = InteractionPattern(
    name="Debate",
    description="A formal discussion on a particular topic in a public meeting or legislative assembly, in which opposing arguments are put forward.",
    structure=[
        "Proponent states a thesis.",
        "Opponent provides a counter-argument.",
        "Proponent rebuts the counter-argument.",
        "Opponent provides a closing statement.",
        "Proponent provides a closing statement.",
    ],
    keywords=["argue", "disagree", "however", "point", "counter", "evidence"],
)

CONSENSUS_BUILDING = InteractionPattern(
    name="Consensus Building",
    description="A process used to generate widespread agreement within a group.",
    structure=[
        "Identify the problem.",
        "Brainstorm solutions.",
        "Discuss pros and cons of each.",
        "Synthesize a proposal.",
        "Call for consensus (vote or voice).",
    ],
    keywords=["agree", "proposal", "compromise", "synthesis", "solution", "vote"],
)

STANDARD_PATTERNS = {
    "socratic": SOCRATIC_METHOD,
    "debate": DEBATE,
    "consensus": CONSENSUS_BUILDING,
}


class PatternMatcher:
    """
    Matches interaction patterns in conversation history.
    """

    def __init__(self, patterns: Dict[str, InteractionPattern] = None):
        self.patterns = patterns or STANDARD_PATTERNS

    def match(self, conversation_text: str) -> List[Dict[str, Any]]:
        """
        Identifies patterns in the given text.
        Returns a list of matches with confidence scores.
        """
        matches = []
        text_lower = conversation_text.lower()

        for key, pattern in self.patterns.items():
            score = 0.0
            # Simple keyword matching for now
            hits = 0
            for kw in pattern.keywords:
                if kw in text_lower:
                    hits += 1

            if pattern.keywords:
                score = hits / len(pattern.keywords)

            # Boost score if pattern name is mentioned
            if pattern.name.lower() in text_lower:
                score = max(score, 0.8)

            if score > 0.3:  # Threshold
                matches.append(
                    {
                        "pattern": pattern.name,
                        "confidence": score,
                        "details": pattern.description,
                    }
                )

        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches
