"""Manual verification script for triple-extraction ontology patterns."""

import sys
from pathlib import Path
import logging

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory  # noqa: E402

logging.basicConfig(level=logging.INFO)


def test_patterns():
    """Verify the expected triples are extracted from representative sentences."""
    print("Initializing ConversationMemory...")
    memory = ConversationMemory(agent_id="test-verifier")

    # Test cases from YAML examples
    test_cases = [
        ("GPT-4 is a large language model", ("GPT-4", "is_a", "large-language-model")),
        (
            "Python is an interpreted language",
            ("Python", "is_a", "interpreted-language"),
        ),
        (
            "Sonnet 4.5 improves upon Sonnet 4",
            ("Sonnet 4.5", "improves_upon", "Sonnet 4"),
        ),
        ("Claude can write code", ("Claude", "capable_of", "write")),
        ("GPT-4 is capable of reasoning", ("GPT-4", "capable_of", "reasoning")),
    ]

    print(f"\nTesting {len(test_cases)} patterns...")
    passed = 0
    for content, expected in test_cases:
        print(f"\nInput: '{content}'")
        triple = memory._extract_triple({"content": content})
        print(f"Extracted: {triple}")

        if triple == expected:
            print("✅ PASS")
            passed += 1
        else:
            print(f"❌ FAIL (Expected {expected})")

    print(f"\nResult: {passed}/{len(test_cases)} passed")

    if passed == len(test_cases):
        print("Verification SUCCESS")
        sys.exit(0)
    else:
        print("Verification FAILED")
        sys.exit(1)


if __name__ == "__main__":
    test_patterns()
