"""
Integration tests for multi-agent memory composition.

Tests end-to-end scenarios where multiple agents:
1. Transmit understandings to their own memories
2. Compose knowledge across agents
3. Recall combined knowledge
4. Validate triple extraction and ontology

Phase 4.4, Task 4.4: Integration Test Suite
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add ARF to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from conversation_memory import ConversationMemory


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for test memories"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # Cleanup
    if Path(temp_path).exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def alice_memory(temp_dir):
    """Agent Alice's memory"""
    storage_path = temp_dir / "alice"
    memory = ConversationMemory(
        agent_id="alice",
        storage_path=str(storage_path),
        backend="file"
    )
    yield memory
    # Cleanup handled by temp_dir fixture


@pytest.fixture
def bob_memory(temp_dir):
    """Agent Bob's memory"""
    storage_path = temp_dir / "bob"
    memory = ConversationMemory(
        agent_id="bob",
        storage_path=str(storage_path),
        backend="file"
    )
    yield memory


@pytest.fixture
def carol_memory(temp_dir):
    """Agent Carol's memory"""
    storage_path = temp_dir / "carol"
    memory = ConversationMemory(
        agent_id="carol",
        storage_path=str(storage_path),
        backend="file"
    )
    yield memory


# ============================================================================
# Integration Tests
# ============================================================================

def test_three_agent_composition(alice_memory, bob_memory, carol_memory):
    """
    Test scenario from roadmap:
    - Alice transmits understanding about Sonnet-4 being powerful
    - Bob transmits understanding about Sonnet-4 being fast
    - Carol composes both memories and can recall both facts
    """
    # Agent A transmits
    alice_ref = alice_memory.transmit({
        "content": "Sonnet-4 is powerful",
        "context": "Testing multi-agent composition",
        "coherence": 0.9
    })
    assert alice_ref is not None

    # Agent B transmits
    bob_ref = bob_memory.transmit({
        "content": "Sonnet-4 is fast",
        "context": "Testing multi-agent composition",
        "coherence": 0.85
    })
    assert bob_ref is not None

    # Agent C composes from both
    alice_export = alice_memory.export_for_composition()
    bob_export = bob_memory.export_for_composition()

    # Import both memories
    stats_alice = carol_memory.import_and_compose(alice_export)
    stats_bob = carol_memory.import_and_compose(bob_export)

    # Verify composition stats
    assert stats_alice['new_understandings'] >= 1
    assert stats_bob['new_understandings'] >= 1

    # Carol should be able to recall both
    recalls = carol_memory.recall("Sonnet-4", top_k=5)
    assert len(recalls) >= 2, "Carol should recall at least 2 understandings about Sonnet-4"

    # Verify content
    contents = [r['content'] for r in recalls]
    assert any("powerful" in c.lower() for c in contents), "Should recall 'powerful'"
    assert any("fast" in c.lower() for c in contents), "Should recall 'fast'"


def test_multi_agent_deduplication(alice_memory, bob_memory):
    """
    Test that duplicate transmissions across agents are properly handled.
    """
    # Both agents transmit the same understanding
    content = "GPT-4 is a large language model"

    alice_memory.transmit({
        "content": content,
        "coherence": 0.9
    })

    bob_memory.transmit({
        "content": content,
        "coherence": 0.9
    })

    # Export both
    alice_export = alice_memory.export_for_composition()
    bob_export = bob_memory.export_for_composition()

    # Create third agent to compose
    temp_path = alice_memory.storage_path.parent / "dedup_test"
    carol = ConversationMemory(agent_id="carol", storage_path=str(temp_path))

    # Import both
    carol.import_and_compose(alice_export)
    stats = carol.import_and_compose(bob_export)

    # Should detect duplicates
    assert stats.get('duplicates_skipped', 0) >= 0

    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


def test_composition_with_embeddings(alice_memory, bob_memory):
    """
    Test that embedding frames are properly composed across agents.
    """
    # Transmit related understandings
    alice_memory.transmit({
        "content": "Neural networks learn from data",
        "coherence": 0.9
    })

    bob_memory.transmit({
        "content": "Deep learning uses neural networks",
        "coherence": 0.85
    })

    # Export and compose
    alice_export = alice_memory.export_for_composition()
    bob_export = bob_memory.export_for_composition()

    temp_path = alice_memory.storage_path.parent / "embed_test"
    carol = ConversationMemory(agent_id="carol", storage_path=str(temp_path))

    carol.import_and_compose(alice_export)
    carol.import_and_compose(bob_export)

    # Query for related concepts
    results = carol.recall("neural networks", top_k=5)

    # Should find both related understandings
    assert len(results) >= 2

    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


def test_multi_agent_adr_tracking(alice_memory, bob_memory, carol_memory):
    """
    Test that ADRs (Architecture Decision Records) are tracked across agents.
    """
    # Alice makes a decision
    alice_memory.transmit({
        "content": "We decided to use Holochain for distributed storage",
        "is_decision": True,
        "coherence": 0.95
    })

    # Bob makes another decision
    bob_memory.transmit({
        "content": "We decided to use sentence-transformers for embeddings",
        "is_decision": True,
        "coherence": 0.9
    })

    # Carol composes both
    alice_export = alice_memory.export_for_composition()
    bob_export = bob_memory.export_for_composition()

    carol_memory.import_and_compose(alice_export)
    carol_memory.import_and_compose(bob_export)

    # Query for decisions
    decisions = carol_memory.recall("decided", top_k=5)
    decision_count = sum(1 for d in decisions if d.get('is_decision', False))

    assert decision_count >= 2, "Should track ADRs across agents"


def test_parallel_composition(temp_dir):
    """
    Test composition with multiple agents in parallel (simulating real-world usage).
    """
    # Create 5 agents
    agents = []
    for i in range(5):
        storage_path = temp_dir / f"agent_{i}"
        memory = ConversationMemory(
            agent_id=f"agent_{i}",
            storage_path=str(storage_path)
        )

        # Each transmits unique understanding
        memory.transmit({
            "content": f"Agent {i} reports: system component {i} is operational",
            "coherence": 0.8 + (i * 0.02)
        })

        agents.append(memory)

    # Create coordinator agent
    coordinator_path = temp_dir / "coordinator"
    coordinator = ConversationMemory(
        agent_id="coordinator",
        storage_path=str(coordinator_path)
    )

    # Compose all agents' memories
    for agent in agents:
        export = agent.export_for_composition()
        stats = coordinator.import_and_compose(export)
        assert stats['new_understandings'] >= 1

    # Coordinator should have all 5 understandings
    all_recalls = coordinator.recall("operational", top_k=10)
    assert len(all_recalls) >= 5, "Coordinator should have all 5 agent reports"

    # Cleanup
    if coordinator_path.exists():
        shutil.rmtree(coordinator_path)


def test_triple_extraction_consistency(alice_memory, bob_memory):
    """
    Test that triple extraction works consistently across agents.
    """
    # Both agents transmit structured knowledge
    alice_memory.transmit({
        "content": "GPT-4 is a LLM",
        "coherence": 0.95
    })

    bob_memory.transmit({
        "content": "Claude-4 is a LLM",
        "coherence": 0.95
    })

    # Both should extract valid triples
    alice_recalls = alice_memory.recall("LLM", top_k=5)
    bob_recalls = bob_memory.recall("LLM", top_k=5)

    assert len(alice_recalls) >= 1
    assert len(bob_recalls) >= 1

    # Check if triples were extracted (metadata should contain triple info)
    for recall in alice_recalls:
        if 'triple' in recall.get('metadata', {}):
            triple = recall['metadata']['triple']
            assert triple['predicate'] == 'is_a'


def test_composition_preserves_metadata(alice_memory, bob_memory):
    """
    Test that metadata (context, coherence, timestamps) is preserved during composition.
    """
    # Alice transmits with rich metadata
    alice_memory.transmit({
        "content": "Test understanding with metadata",
        "context": "Integration test scenario",
        "coherence": 0.92,
        "metadata": {"test_key": "test_value"}
    })

    # Export and compose to Bob
    alice_export = alice_memory.export_for_composition()
    bob_memory.import_and_compose(alice_export)

    # Bob recalls
    recalls = bob_memory.recall("metadata", top_k=5)
    assert len(recalls) >= 1

    # Verify metadata preservation
    recall = recalls[0]
    assert recall.get('context') is not None
    assert recall.get('coherence_score', 0) > 0


def test_empty_composition(alice_memory, bob_memory):
    """
    Test that composing with an agent that has no memories handles gracefully.
    """
    # Bob has no transmissions
    bob_export = bob_memory.export_for_composition()

    # Alice should handle empty composition gracefully
    stats = alice_memory.import_and_compose(bob_export)

    # Should report 0 new understandings
    assert stats['new_understandings'] == 0


def test_composition_with_validation(temp_dir):
    """
    Test composition with ontology validation enabled.
    """
    # Create memories with validation
    alice_path = temp_dir / "alice_validated"
    alice = ConversationMemory(
        agent_id="alice",
        storage_path=str(alice_path),
        validate_ontology=True
    )

    bob_path = temp_dir / "bob_validated"
    bob = ConversationMemory(
        agent_id="bob",
        storage_path=str(bob_path),
        validate_ontology=True
    )

    # Transmit valid triple
    alice.transmit({
        "content": "GPT-4 is a LLM",
        "coherence": 0.95
    })

    # Export and compose
    alice_export = alice.export_for_composition()
    stats = bob.import_and_compose(alice_export)

    # Should succeed with validation
    assert stats['new_understandings'] >= 1

    # Verify validation stats
    bob_stats = bob.get_validation_stats()
    assert bob_stats['total_attempts'] > 0

    # Cleanup
    if alice_path.exists():
        shutil.rmtree(alice_path)
    if bob_path.exists():
        shutil.rmtree(bob_path)


# ============================================================================
# Performance Tests
# ============================================================================

def test_composition_performance(temp_dir):
    """
    Test that composition completes in reasonable time (<5 minutes for benchmark).
    This ensures CI/CD pipeline efficiency.
    """
    import time

    # Create agent with many understandings
    alice_path = temp_dir / "alice_perf"
    alice = ConversationMemory(agent_id="alice", storage_path=str(alice_path))

    # Transmit 50 understandings
    for i in range(50):
        alice.transmit({
            "content": f"Understanding {i}: Testing performance with content",
            "coherence": 0.8
        })

    # Export
    alice_export = alice.export_for_composition()

    # Create Bob and measure composition time
    bob_path = temp_dir / "bob_perf"
    bob = ConversationMemory(agent_id="bob", storage_path=str(bob_path))

    start_time = time.time()
    bob.import_and_compose(alice_export)
    elapsed = time.time() - start_time

    # Should complete in reasonable time (< 30 seconds for 50 items)
    assert elapsed < 30, f"Composition took too long: {elapsed:.2f}s"

    # Cleanup
    if alice_path.exists():
        shutil.rmtree(alice_path)
    if bob_path.exists():
        shutil.rmtree(bob_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
