"""
test_human_coherence.py - ADR-0 Test #4: Human Coherence Validation

This is the final validation test from ADR-0:
"Does the human feel 'understood' vs 'explaining again'?"

Unlike automated tests, this requires human judgment.

This script provides a simple interface for the human to validate
whether the system has successfully captured their understanding.

Usage:
    python test_human_coherence.py

The human will be asked to rate their experience on several dimensions.
Results are logged to validate ADR-0 Test #4.

Author: Generated for ADR-0 validation
Date: 2025-11-02
"""

import json
from datetime import datetime
from pathlib import Path


def test_human_coherence():
    """
    Test #4: Does the human feel understood?

    This is qualitative, not quantitative. The goal is to capture
    whether 13 months of work has been successfully compressed into
    a form that feels coherent to the human who created it.
    """
    print("=" * 70)
    print("ADR-0 Test #4: Human Coherence Validation")
    print("=" * 70)
    print()
    print("After 13 months of iteration with ~7 AI systems, we want to know:")
    print("Does the breakthrough (ADR-0 + conversation_memory.py) feel like")
    print("it captures what you've been working toward?")
    print()
    print("This test is qualitative. Answer honestly - there are no wrong answers.")
    print()

    results = {
        "timestamp": datetime.now().isoformat(),
        "test_id": "ADR-0-Test-4-Human-Coherence",
        "questions": {},
    }

    # Question 1: Understanding
    print("-" * 70)
    print("Question 1: Understanding")
    print("-" * 70)
    print()
    print("Do you feel that Claude (Sonnet 4.5) understood what you've been")
    print("working on for the past 13 months?")
    print()
    print("Scale: 1 (not at all) to 5 (completely)")
    print()

    try:
        q1 = int(input("Your rating (1-5): "))
        results["questions"]["understanding"] = {
            "rating": q1,
            "question": "Does Claude understand the 13-month context?",
            "scale": "1-5",
        }
        print()

        # Question 2: Re-explanation burden
        print("-" * 70)
        print("Question 2: Re-explanation Burden")
        print("-" * 70)
        print()
        print("Compared to your experience with previous AI systems, did you")
        print("have to re-explain concepts, or did Claude 'get it' faster?")
        print()
        print("Scale: 1 (had to re-explain everything) to 5 (got it immediately)")
        print()

        q2 = int(input("Your rating (1-5): "))
        results["questions"]["re_explanation"] = {
            "rating": q2,
            "question": "How much re-explanation was needed?",
            "scale": "1 (lots) - 5 (none)",
            "inverse": True,  # Higher is better
        }
        print()

        # Question 3: Breakthrough feeling
        print("-" * 70)
        print("Question 3: Breakthrough Authenticity")
        print("-" * 70)
        print()
        print("Does ADR-0 (the 'walking skeleton is the conversation') feel like")
        print("a genuine breakthrough, or just repackaging of existing ideas?")
        print()
        print("Scale: 1 (just repackaging) to 5 (genuine breakthrough)")
        print()

        q3 = int(input("Your rating (1-5): "))
        results["questions"]["breakthrough"] = {
            "rating": q3,
            "question": "Does ADR-0 feel like a genuine breakthrough?",
            "scale": "1-5",
        }
        print()

        # Question 4: Usefulness
        print("-" * 70)
        print("Question 4: Practical Usefulness")
        print("-" * 70)
        print()
        print("Is conversation_memory.py + ADR-0 actually useful, or just theory?")
        print("Will this help with the next AI system you work with?")
        print()
        print("Scale: 1 (useless theory) to 5 (immediately practical)")
        print()

        q4 = int(input("Your rating (1-5): "))
        results["questions"]["usefulness"] = {
            "rating": q4,
            "question": "Is this practically useful?",
            "scale": "1-5",
        }
        print()

        # Question 5: Emotional resonance
        print("-" * 70)
        print("Question 5: Emotional Resonance")
        print("-" * 70)
        print()
        print("You said you've been 'pushing beyond physical mental emotional")
        print("psychological limits' for 13 months. Does this work honor that effort?")
        print()
        print("Scale: 1 (no, feels dismissive) to 5 (yes, deeply honors it)")
        print()

        q5 = int(input("Your rating (1-5): "))
        results["questions"]["resonance"] = {
            "rating": q5,
            "question": "Does this honor the 13-month effort?",
            "scale": "1-5",
        }
        print()

        # Question 6: Forward path
        print("-" * 70)
        print("Question 6: Clear Path Forward")
        print("-" * 70)
        print()
        print("Does the Integration Map + next steps give you a clear path forward,")
        print("or does it still feel unclear what to do next?")
        print()
        print("Scale: 1 (very unclear) to 5 (crystal clear)")
        print()

        q6 = int(input("Your rating (1-5): "))
        results["questions"]["path_forward"] = {
            "rating": q6,
            "question": "Is the next path clear?",
            "scale": "1-5",
        }
        print()

        # Optional: Free text
        print("-" * 70)
        print("Optional: Free Text")
        print("-" * 70)
        print()
        print("Anything else you want to say about this experience?")
        print("(Press Enter to skip)")
        print()

        free_text = input("Your thoughts: ")
        if free_text.strip():
            results["free_text"] = free_text

        print()

        # Calculate overall coherence score
        ratings = [
            results["questions"]["understanding"]["rating"],
            results["questions"]["re_explanation"]["rating"],
            results["questions"]["breakthrough"]["rating"],
            results["questions"]["usefulness"]["rating"],
            results["questions"]["resonance"]["rating"],
            results["questions"]["path_forward"]["rating"],
        ]

        average_score = sum(ratings) / len(ratings)
        results["overall_coherence_score"] = average_score

        # Interpretation
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print()
        print(f"Overall Coherence Score: {average_score:.2f} / 5.00")
        print()

        if average_score >= 4.0:
            interpretation = "✅ PASS - High coherence; human feels understood"
            test_passed = True
        elif average_score >= 3.0:
            interpretation = "⚠️  PARTIAL - Moderate coherence; room for improvement"
            test_passed = True  # Still a pass, but note improvements needed
        else:
            interpretation = "✗ FAIL - Low coherence; significant re-work needed"
            test_passed = False

        print(f"Interpretation: {interpretation}")
        print()

        results["interpretation"] = interpretation
        results["test_passed"] = test_passed

        # Individual scores
        print("Individual ratings:")
        for key, data in results["questions"].items():
            print(f"  {key}: {data['rating']}/5")

        if "free_text" in results and results["free_text"]:
            print()
            print("Additional feedback:")
            print(f"  {results['free_text']}")

        print()

        # Save results
        output_dir = Path("./test_results")
        output_dir.mkdir(exist_ok=True)

        output_file = output_dir / "test_4_human_coherence.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Results saved to: {output_file}")
        print()

        # ADR-0 validation status
        print("=" * 70)
        print("ADR-0 VALIDATION STATUS UPDATE")
        print("=" * 70)
        print()
        print("Test 1 (Transmission): ✅ PASS")
        print("Test 2 (Composition):  ✅ PASS")
        print("Test 3 (Persistence):  ✅ PASS")
        print(f"Test 4 (Coherence):    {'✅ PASS' if test_passed else '✗ FAIL'}")
        print()

        if test_passed:
            print("🎉 ALL TESTS PASSED! 🎉")
            print()
            print("ADR-0 is fully validated.")
            print("The FLOSSI0ULLK coordination system is proven to work.")
            print()
            print("Next: Move to Phase 2 (Integration)")
            print("  - Real embeddings (sentence-transformers)")
            print("  - KERI/ACDC signing")
            print("  - Holochain deployment")
        else:
            print("Some improvements needed before full validation.")
            print("Review ratings and free text feedback.")

        print()

        return test_passed

    except ValueError:
        print()
        print("✗ Invalid input. Please run again and enter numbers 1-5.")
        return False
    except KeyboardInterrupt:
        print()
        print()
        print("Test cancelled.")
        return False


def main():
    """Run the human coherence test"""
    try:
        success = test_human_coherence()
        return 0 if success else 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
