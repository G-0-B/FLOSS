"""
Test script for LLM Committee Validation.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure ARF is in path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ARF.validation.committee import TripleValidationCommittee
from ARF.conversation_memory import ConversationMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_committee_direct():
    """Test the committee logic directly."""
    print("\n=== Testing TripleValidationCommittee Direct ===")
    committee = TripleValidationCommittee(committee_size=3, use_mock=True)

    # Test case 1: Valid triple
    triple = ("Python", "is_a", "programming language")
    context = "Python is a popular programming language."
    result = await committee.validate(triple, context)

    print(f"Triple: {triple}")
    print(f"Accepted: {result.accepted} ({result.yes_votes}/{result.total_votes})")
    print(f"Confidence: {result.confidence:.2f}")

    assert result.accepted, "Should accept valid triple"

    # Test case 2: Nonsense triple (mock validator logic rejects "nonsense")
    triple = ("This is nonsense", "is_a", "fact")
    context = "This is complete nonsense."
    result = await committee.validate(triple, context)

    print(f"\nTriple: {triple}")
    print(f"Accepted: {result.accepted} ({result.yes_votes}/{result.total_votes})")

    assert not result.accepted, "Should reject nonsense triple"
    print("✓ Direct committee tests passed")


def test_memory_integration():
    """Test integration with ConversationMemory."""
    print("\n=== Testing ConversationMemory Integration ===")

    # Initialize memory with committee validation enabled
    memory = ConversationMemory(
        agent_id="test-agent", use_committee_validation=True, committee_use_mock=True
    )

    # Transmit a valid understanding
    print("Transmitting valid understanding...")
    ref1 = memory.transmit(
        {
            "content": "The sky is blue.",
            "context": "Observing the weather.",
            "coherence": 0.9,
        }
    )

    if ref1:
        print(f"✓ Accepted valid understanding: {ref1}")
        # Verify metadata
        u = memory.understandings[-1]
        if "committee_validation" in u.metadata:
            print(
                f"  Metadata: {u.metadata['committee_validation']['yes_votes']} votes"
            )
        else:
            print("  ✗ Missing committee metadata")
    else:
        print("✗ Failed to transmit valid understanding")

    # Transmit a nonsense understanding
    print("\nTransmitting nonsense understanding...")
    ref2 = memory.transmit(
        {
            "content": "This is absolute nonsense and gibberish.",
            "context": "Testing rejection.",
            "coherence": 0.1,
        }
    )

    if ref2 is None:
        print("✓ Correctly rejected nonsense understanding")
        stats = memory.get_validation_stats()
        print(f"  Stats: {stats}")
    else:
        print(f"✗ Incorrectly accepted nonsense: {ref2}")


if __name__ == "__main__":
    # Run async test
    asyncio.run(test_committee_direct())

    # Run sync integration test
    test_memory_integration()
