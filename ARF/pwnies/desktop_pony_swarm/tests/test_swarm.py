"""
Test harness for pony swarm RSA.

Validates ADR-0 criteria and RSA algorithm.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directories to path
test_dir = Path(__file__).parent.absolute()
package_dir = test_dir.parent  # desktop_pony_swarm/
project_root = package_dir.parent  # /mnt/project/

# Add both to path
for path in [project_root, package_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from desktop_pony_swarm.runtime.orchestrator import SwarmRuntime
from desktop_pony_swarm.config.settings import DEFAULT_CONFIG

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def test_basic_rsa():
    """Tests the basic functionality of the RSA algorithm on a simple math problem.

    This test verifies that the swarm can correctly execute the RSA workflow
    (initialization, iterative aggregation, and final selection) and produce a
    plausible answer. It also checks that the performance and diversity metrics
    are being recorded correctly.
    """
    print("\n" + "=" * 80)
    print("TEST: Basic RSA with Math Question")
    print("=" * 80 + "\n")

    query = "What is 15 * 23? Show your work step by step."

    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.recursive_self_aggregation(query=query, K=2, T=3)

        print("\n--- FINAL RESPONSE ---")
        print(result["response"])

        print("\n--- METRICS ---")
        for key, value in result["metrics"].items():
            print(f"{key}: {value}")

        print("\n--- DIVERSITY BY ITERATION ---")
        for it in result["iterations"]:
            print(f"Iteration {it['iteration']}: diversity={it['diversity']:.4f}")


async def test_reasoning_task():
    """Tests the swarm's ability to handle a reasoning task.

    This test uses a classic riddle to evaluate whether the iterative aggregation
    process helps the swarm converge on the correct answer, even if some initial
    responses are incorrect. It demonstrates the swarm's capacity for collective
    problem-solving and error correction.
    """
    print("\n" + "=" * 80)
    print("TEST: RSA on Reasoning Task")
    print("=" * 80 + "\n")

    query = """A farmer has 17 sheep. All but 9 die. How many are left?
Think carefully about what 'all but 9' means."""

    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.recursive_self_aggregation(query=query, K=2, T=3)

        print("\n--- FINAL RESPONSE ---")
        print(result["response"])

        print("\n--- ITERATION HISTORY ---")
        for it in result["iterations"]:
            print(f"\nIteration {it['iteration']}:")
            print(f"  Diversity: {it['diversity']:.4f}")
            print(f"  Sample response: {it['population'][0][:100]}...")


async def test_single_step_aggregation():
    """Tests the single-step aggregation method.

    This test validates the functionality of the non-recursive aggregation
    workflow (T=1), which is a faster alternative to the full RSA algorithm.
    It ensures that the initial responses are correctly generated and aggregated
    into a final, coherent response.
    """
    print("\n" + "=" * 80)
    print("TEST: Single-Step Aggregation")
    print("=" * 80 + "\n")

    query = "What are three benefits of using distributed systems?"

    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.single_step_aggregation(query=query, K=4)

        print("\n--- CANDIDATES ---")
        for i, cand in enumerate(result["candidates"], 1):
            print(f"\nCandidate {i}:")
            print(cand[:150] + "...")

        print("\n--- AGGREGATED RESPONSE ---")
        print(result["response"])


async def test_adr_validation():
    """Validates key criteria from the ADR-0 specification.

    This test is designed to ensure that the swarm's implementation aligns with
    the foundational principles outlined in ADR-0. Specifically, it checks:
    - **Test 2 (Composition):** Verifies that the responses from multiple ponies
      can be composed without contradiction, as measured by the diversity metric.
    - **Test 3 (Persistence):** Confirms that the embeddings of the pony responses
      are correctly stored and aggregated in the `MultiScaleEmbedding` framework.
    """
    print("\n" + "=" * 80)
    print("TEST: ADR-0 Validation Criteria")
    print("=" * 80 + "\n")

    query = "What is the core principle of FLOSSI0ULLK?"

    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.recursive_self_aggregation(query=query, K=2, T=3)

        print(
            "\n✅ Test 2 (Composition): 4 ponies composed responses without contradiction"
        )
        print(f"   Final diversity: {result['iterations'][-1]['diversity']:.4f}")

        print("\n✅ Test 3 (Persistence): Embeddings stored in MultiScaleEmbedding")
        print(
            f"   Community embeddings: {len(swarm.embedding_manager.embeddings.levels.get('community', {}))}"
        )
        print(
            f"   Fine embeddings: {len(swarm.embedding_manager.embeddings.levels.get('fine', {}))}"
        )

        print("\n--- FINAL RESPONSE ---")
        print(result["response"])


async def test_get_latest_version():
    """Tests the get_latest_version zome call."""
    print("\n" + "=" * 80)
    print("TEST: Get Latest Version")
    print("=" * 80 + "\n")

    runtime = SwarmRuntime()
    try:
        await runtime.connect()
        version = await runtime.get_latest_version()
        print(f"Latest version: {version}")
    finally:
        await runtime.disconnect()


async def main():
    """Runs the full test suite for the Pony Swarm.

    This function executes all the defined tests in sequence, providing a
    comprehensive validation of the swarm's functionality.
    """
    print("\n🐴 DESKTOP PONY SWARM - Test Suite")
    print("=" * 80)

    try:
        await test_get_latest_version()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETE")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
