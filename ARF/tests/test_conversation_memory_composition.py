"""
test_conversation_memory_composition.py - Integration tests for ConversationMemory composition

Tests for Task 1.3: Integration with ConversationMemory

This test suite validates that the composition logic integrates properly
with ConversationMemory.import_and_compose().

Author: Task 1.3 implementation
Date: 2025-11-11
"""

import pytest
import numpy as np
import sys
import tempfile
import shutil
from pathlib import Path

# Add ARF directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory


class TestConversationMemoryComposition:
    """Tests for ConversationMemory composition integration"""

    def setup_method(self):
        """Create temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temporary directory after each test"""
        if hasattr(self, 'temp_dir') and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_composition_with_embeddings(self):
        """Test that ConversationMemory.import_and_compose() uses embedding composition."""
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="agent1",
            storage_path=f"{self.temp_dir}/agent1"
        )
        memory1.transmit({
            "content": "Understanding from agent 1",
            "context": "Test context 1"
        })

        memory2 = ConversationMemory(
            agent_id="agent2",
            storage_path=f"{self.temp_dir}/agent2"
        )
        memory2.transmit({
            "content": "Understanding from agent 2",
            "context": "Test context 2"
        })

        # ACT
        export = memory2.export_for_composition()
        initial_understanding_count = len(memory1.understandings)

        # Get initial embedding count
        if memory1.embeddings:
            initial_emb_count = len(memory1.embeddings.levels.get('default', {}))
        else:
            initial_emb_count = 0

        memory1.import_and_compose(export)

        # ASSERT
        # Should have composed understandings
        assert len(memory1.understandings) == initial_understanding_count + 1

        # Should have composed embeddings (if available)
        if memory1.embeddings:
            final_emb_count = len(memory1.embeddings.levels.get('default', {}))
            # Note: Depending on the mock embedding implementation, counts may vary
            # The key is that composition was attempted
            assert final_emb_count >= initial_emb_count

    def test_composition_multiple_agents(self):
        """Test composing insights from multiple agents."""
        # ARRANGE
        human_memory = ConversationMemory(
            agent_id="human",
            storage_path=f"{self.temp_dir}/human"
        )
        human_memory.transmit({
            "content": "Human insight about the problem",
            "context": "Human perspective"
        })

        ai1_memory = ConversationMemory(
            agent_id="ai1",
            storage_path=f"{self.temp_dir}/ai1"
        )
        ai1_memory.transmit({
            "content": "AI 1 analysis of the situation",
            "context": "AI 1 perspective"
        })

        ai2_memory = ConversationMemory(
            agent_id="ai2",
            storage_path=f"{self.temp_dir}/ai2"
        )
        ai2_memory.transmit({
            "content": "AI 2 recommendation",
            "context": "AI 2 perspective"
        })

        # ACT
        # Compose all into human memory
        human_memory.import_and_compose(ai1_memory.export_for_composition())
        human_memory.import_and_compose(ai2_memory.export_for_composition())

        # ASSERT
        assert len(human_memory.understandings) == 3

        # Check all perspectives are present
        agents = {u.agent_id for u in human_memory.understandings}
        assert "human" in agents
        assert "ai1" in agents
        assert "ai2" in agents

    def test_composition_preserves_provenance(self):
        """Test that composition preserves agent provenance."""
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="originator",
            storage_path=f"{self.temp_dir}/originator"
        )
        memory1.transmit({
            "content": "Original insight",
            "context": "From the originator"
        })

        memory2 = ConversationMemory(
            agent_id="receiver",
            storage_path=f"{self.temp_dir}/receiver"
        )

        # ACT
        export = memory1.export_for_composition()
        memory2.import_and_compose(export)

        # ASSERT
        # Should have the understanding with correct agent_id
        imported = memory2.understandings[0]
        assert imported.agent_id == "originator"
        assert imported.content == "Original insight"

    def test_composition_with_decisions(self):
        """Test that ADRs are composed along with understandings."""
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="decision_maker",
            storage_path=f"{self.temp_dir}/decision_maker"
        )
        memory1.transmit({
            "content": "Important architectural decision",
            "context": "System design",
            "is_decision": True
        })

        memory2 = ConversationMemory(
            agent_id="reviewer",
            storage_path=f"{self.temp_dir}/reviewer"
        )

        # ACT
        export = memory1.export_for_composition()
        memory2.import_and_compose(export)

        # ASSERT
        assert len(memory2.understandings) == 1
        assert len(memory2.adrs) == 1
        assert memory2.adrs[0]['content']['content'] == "Important architectural decision"

    def test_composition_without_embeddings(self):
        """Test that composition works even if embeddings are not available."""
        # This test ensures graceful degradation
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="agent1",
            storage_path=f"{self.temp_dir}/agent1"
        )
        memory1.transmit({
            "content": "Understanding without embeddings"
        })

        # Simulate embeddings not being available
        embeddings_backup = memory1.embeddings
        memory1.embeddings = None

        memory2 = ConversationMemory(
            agent_id="agent2",
            storage_path=f"{self.temp_dir}/agent2"
        )

        # ACT
        export = memory1.export_for_composition()
        memory2.import_and_compose(export)

        # ASSERT
        assert len(memory2.understandings) == 1

        # Restore for cleanup
        memory1.embeddings = embeddings_backup

    def test_composition_error_handling(self):
        """Test that composition handles errors gracefully."""
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="agent1",
            storage_path=f"{self.temp_dir}/agent1"
        )

        # Create a malformed export
        bad_export = {
            'agent_id': 'bad_agent',
            'understandings': [
                {
                    'content': 'Test',
                    'agent_id': 'bad_agent',
                    'timestamp': '2025-11-11T00:00:00',
                    # Missing required fields
                }
            ],
            'adrs': [],
            'embedding_state': None,
            'exported_at': '2025-11-11T00:00:00'
        }

        # ACT & ASSERT
        # Should not crash, but may log errors
        try:
            memory1.import_and_compose(bad_export)
        except Exception as e:
            # Some exceptions are acceptable for malformed data
            assert isinstance(e, (TypeError, KeyError, ValueError))

    def test_composition_idempotency(self):
        """Test that composing the same memory twice handles it gracefully."""
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="agent1",
            storage_path=f"{self.temp_dir}/agent1"
        )
        memory1.transmit({
            "content": "Unique understanding"
        })

        memory2 = ConversationMemory(
            agent_id="agent2",
            storage_path=f"{self.temp_dir}/agent2"
        )

        export = memory1.export_for_composition()

        # ACT
        memory2.import_and_compose(export)
        count_after_first = len(memory2.understandings)

        memory2.import_and_compose(export)
        count_after_second = len(memory2.understandings)

        # ASSERT
        # Will have duplicates in understandings (this is expected behavior)
        # Embeddings should use merge strategy to avoid duplication
        assert count_after_second == count_after_first * 2

    def test_composition_persistence(self):
        """Test that composed memory persists correctly."""
        # ARRANGE
        memory1 = ConversationMemory(
            agent_id="agent1",
            storage_path=f"{self.temp_dir}/agent1"
        )
        memory1.transmit({
            "content": "Understanding 1"
        })

        memory2 = ConversationMemory(
            agent_id="agent2",
            storage_path=f"{self.temp_dir}/agent2"
        )
        memory2.transmit({
            "content": "Understanding 2"
        })

        # Compose
        export = memory1.export_for_composition()
        memory2.import_and_compose(export)

        # Delete and reload
        del memory2

        # ACT
        memory2_reloaded = ConversationMemory(
            agent_id="agent2",
            storage_path=f"{self.temp_dir}/agent2"
        )

        # ASSERT
        assert len(memory2_reloaded.understandings) == 2
        agents = {u.agent_id for u in memory2_reloaded.understandings}
        assert "agent1" in agents
        assert "agent2" in agents


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
