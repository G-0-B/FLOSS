"""
Offline tests for the Holochain connector.

These tests verify the data transformation logic without requiring
a running Holochain conductor. The full integration test requires
a conductor with the rose_forest hApp installed.
"""

import json
import pytest
from packages.orchestrator.holochain_connector import (
    RoseNodeInput,
    SearchInput,
    SearchResult,
    understanding_to_rose_node,
)


class TestRoseNodeInput:
    def test_basic_construction(self):
        node = RoseNodeInput(
            content="Test content",
            embedding=[0.1, 0.2, 0.3],
            license="MIT",
            metadata={"model_id": "test", "model_card_hash": "sha256:abc"},
        )
        assert node.content == "Test content"
        assert node.license == "MIT"
        assert len(node.embedding) == 3

    def test_default_license(self):
        node = RoseNodeInput(content="x", embedding=[1.0])
        assert node.license == "MIT"

    def test_default_metadata(self):
        node = RoseNodeInput(content="x", embedding=[1.0])
        assert node.metadata == {}


class TestUnderstandingConversion:
    def test_basic_conversion(self):
        understanding = {
            "content": "The walking skeleton is the conversation itself",
            "source": "conversation_memory",
            "agent_id": "claude-test",
        }
        embedding = [0.1] * 128

        result = understanding_to_rose_node(
            understanding=understanding,
            embedding=embedding,
            model_id="test-model",
            model_card_hash="sha256:deadbeef",
        )

        assert isinstance(result, RoseNodeInput)
        assert result.content == understanding["content"]
        assert result.embedding == embedding
        assert result.license == "MIT"
        assert result.metadata["model_id"] == "test-model"
        assert result.metadata["model_card_hash"] == "sha256:deadbeef"
        assert result.metadata["source"] == "conversation_memory"
        assert result.metadata["agent_id"] == "claude-test"

    def test_fallback_to_description(self):
        understanding = {
            "description": "Fallback content",
        }
        result = understanding_to_rose_node(understanding, [0.0])
        assert result.content == "Fallback content"

    def test_custom_license(self):
        result = understanding_to_rose_node(
            {"content": "x"}, [0.0], license="Apache-2.0"
        )
        assert result.license == "Apache-2.0"

    def test_metadata_carries_level(self):
        understanding = {"content": "x", "level": "level_2"}
        result = understanding_to_rose_node(understanding, [0.0])
        assert result.metadata["level"] == "level_2"


class TestSearchResult:
    def test_construction(self):
        result = SearchResult(hash=b"\x00" * 39, score=0.95, content="found it")
        assert result.score == 0.95
        assert result.content == "found it"
        assert len(result.hash) == 39


class TestSerializationCompat:
    """Verify that Python data structures serialize in a way compatible with the zome."""

    def test_rose_node_json_shape(self):
        """The JSON shape should match what the zome's AddNodeInput expects."""
        node = RoseNodeInput(
            content="Test",
            embedding=[0.1, 0.2],
            license="MIT",
            metadata={"model_id": "test", "model_card_hash": "sha256:abc"},
        )
        # Simulate what would be msgpack-encoded
        payload = {
            "content": node.content,
            "embedding": node.embedding,
            "license": node.license,
            "metadata": node.metadata,
        }
        # Must have these exact keys (matches Rust struct field names)
        assert set(payload.keys()) == {"content", "embedding", "license", "metadata"}
        # Embedding should be a list of floats
        assert all(isinstance(v, float) for v in payload["embedding"])
        # Metadata values should all be strings
        assert all(isinstance(v, str) for v in payload["metadata"].values())

    def test_search_input_json_shape(self):
        """The JSON shape should match what the zome's SearchInput expects."""
        search = SearchInput(query_embedding=[0.1, 0.2], k=5)
        payload = {
            "query_embedding": search.query_embedding,
            "k": search.k,
        }
        assert set(payload.keys()) == {"query_embedding", "k"}
        assert isinstance(payload["k"], int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
