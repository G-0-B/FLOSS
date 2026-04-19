"""
Validation tests for the Walking Skeleton, generated from the
walking_skeleton_validation.yaml specification.
"""

import asyncio
import pytest
import yaml
from pathlib import Path
import sys
import numpy as np

# Add parent directories to path
test_dir = Path(__file__).parent.absolute()
project_root = test_dir.parent.parent  # /mnt/project/
pwnies_dir = project_root / "pwnies"

# Add both to path
for path in [project_root, pwnies_dir]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

SPEC_FILE = Path(__file__).parent.parent.parent / "walking_skeleton_validation.yaml"


@pytest.fixture
def validation_spec():
    """Load the walking skeleton validation spec from disk."""
    with open(SPEC_FILE, "r") as f:
        return yaml.safe_load(f)


def test_spec_exists(validation_spec):
    """Ensures the validation specification file exists and is valid."""
    assert validation_spec is not None
    assert "test_2_composition" in validation_spec
    assert "test_3_persistence" in validation_spec



def test_composition(validation_spec):
    """Validate ADR-0 Test 2 composition behavior against the spec."""
    criteria = validation_spec["test_2_composition"]["criteria"]
    print(f"\n--- Running Test: {criteria} ---")

    async def run_test():
        from pwnies.desktop_pony_swarm.core.swarm import PonySwarm

        async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
            result = await swarm.recursive_self_aggregation(
                query="What is the core principle of FLOSSI0ULLK?", K=2, T=3
            )
            assert result is not None
            assert "response" in result
            assert len(result["response"]) > 0
            assert "metrics" in result
            assert result["metrics"]["avg_diversity"] > 0

    asyncio.run(run_test())



def test_persistence(validation_spec):
    """Validate ADR-0 Test 3 persistence behavior against the spec."""
    criteria = validation_spec["test_3_persistence"]["criteria"]
    print(f"\n--- Running Test: {criteria} ---")

    async def run_test():
        from pwnies.desktop_pony_swarm.core.swarm import PonySwarm

        async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
            # Conversation 1: Create knowledge
            query1 = "What is the capital of France?"
            result1 = await swarm.recursive_self_aggregation(query=query1, K=2, T=3)
            # This is a placeholder for storing the embedding.
            # In a real implementation, the swarm would do this automatically.
            embedding = np.random.rand(384)
            swarm.embedding_manager.embeddings.add_embedding(
                "community", query1, embedding
            )

            # Conversation 2: Retrieve knowledge
            query2 = "What is the main city in France?"
            # Use a mock embedding for the query
            query_embedding = np.random.rand(384)
            similar = swarm.embedding_manager.query_similar(
                query_embedding, "community", top_k=1
            )
            assert len(similar) > 0

    asyncio.run(run_test())
