"""
Test script for Pattern Library and Meaningful Mixing.
"""

import sys
from pathlib import Path
import logging

# Ensure ARF is in path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ARF.ontology.patterns import PatternMatcher, SOCRATIC_METHOD, DEBATE
from ARF.ontology.mixing import PatternMixer
from ARF.conversation_memory import ConversationMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_pattern_matching():
    print("\n=== Testing PatternMatcher ===")
    matcher = PatternMatcher()

    # Test Socratic
    text = "Why do you think that? Can you define your terms? Suppose we assume the opposite."
    matches = matcher.match(text)
    print(f"Text: '{text}'")
    print(f"Matches: {[m['pattern'] for m in matches]}")

    assert matches, "Should match something"
    assert matches[0]["pattern"] == "Socratic Method", "Should match Socratic Method"
    print("✓ Socratic matching passed")

    # Test Debate
    text = "I disagree with your point. However, the evidence suggests otherwise. My counter-argument is..."
    matches = matcher.match(text)
    print(f"Text: '{text}'")
    print(f"Matches: {[m['pattern'] for m in matches]}")

    assert matches, "Should match something"
    assert matches[0]["pattern"] == "Debate", "Should match Debate"
    print("✓ Debate matching passed")


def test_pattern_mixing():
    print("\n=== Testing PatternMixer ===")
    mixer = PatternMixer()

    mixed = mixer.mix(SOCRATIC_METHOD, DEBATE, strategy="interleave")
    print(f"Mixed Name: {mixed.name}")
    print(f"Mixed Structure (first 4 steps):")
    for step in mixed.structure[:4]:
        print(f"  {step}")

    assert "Socratic Method" in mixed.name
    assert "Debate" in mixed.name
    assert len(mixed.structure) >= len(SOCRATIC_METHOD.structure)
    print("✓ Pattern mixing passed")


def test_memory_integration():
    print("\n=== Testing ConversationMemory Integration ===")
    memory = ConversationMemory(agent_id="test-pattern-agent")

    # Transmit text that should trigger Socratic pattern
    # Keywords: why, define, suppose
    ref = memory.transmit(
        {
            "content": "Why do you think that? Can you define your terms? Suppose we assume the opposite.",
            "context": "Socratic dialogue about optics.",
            "coherence": 0.8,
        }
    )

    u = memory.understandings[-1]
    print(f"Stored Understanding Metadata: {u.metadata}")

    assert "patterns" in u.metadata, "Should have detected patterns"
    patterns = [p["pattern"] for p in u.metadata["patterns"]]
    assert "Socratic Method" in patterns, "Should have detected Socratic Method"
    print("✓ Memory integration passed")


if __name__ == "__main__":
    test_pattern_matching()
    test_pattern_mixing()
    test_memory_integration()
