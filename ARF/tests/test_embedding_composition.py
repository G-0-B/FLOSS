"""
test_embedding_composition.py - Tests for MultiScaleEmbedding composition

Tests for Task 1.3: Implement Composition Logic in MultiScaleEmbedding

This test suite validates:
1. Merge strategy (add new, skip duplicates)
2. Average strategy (blend similar embeddings)
3. Append strategy (keep all with unique keys)
4. Dimension mismatch detection
5. Empty embeddings handling
6. Composition properties (where applicable)

Author: Task 1.3 implementation
Date: 2025-11-11
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add ARF directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from embedding_frames_of_scale import MultiScaleEmbedding


class TestComposeMergeStrategy:
    """Tests for merge strategy composition"""

    def test_compose_merge_no_duplicates(self):
        """Test merge strategy with completely different embeddings."""
        # ARRANGE
        emb1 = MultiScaleEmbedding()
        vec_a = np.random.randn(384)
        vec_a = vec_a / np.linalg.norm(vec_a)
        emb1.add("concept_a", vec_a)

        emb2 = MultiScaleEmbedding()
        vec_b = np.random.randn(384)
        vec_b = vec_b / np.linalg.norm(vec_b)
        emb2.add("concept_b", vec_b)

        # ACT
        emb1.compose(emb2, strategy='merge')

        # ASSERT
        assert len(emb1.levels.get('default', {})) == 2
        assert emb1.get("concept_a") is not None
        assert emb1.get("concept_b") is not None

    def test_compose_merge_with_duplicates(self):
        """Test merge strategy skips near-duplicate embeddings."""
        # ARRANGE
        shared_embedding = np.random.randn(384)
        shared_embedding = shared_embedding / np.linalg.norm(shared_embedding)

        emb1 = MultiScaleEmbedding()
        emb1.add("concept", shared_embedding)

        emb2 = MultiScaleEmbedding()
        # Add very similar embedding (should be detected as duplicate)
        similar = shared_embedding + np.random.randn(384) * 0.01
        similar = similar / np.linalg.norm(similar)
        emb2.add("same_concept", similar)

        # ACT
        emb1.compose(emb2, strategy='merge', similarity_threshold=0.95)

        # ASSERT
        # Should still be 1 (duplicate was skipped)
        assert len(emb1.levels.get('default', {})) == 1

    def test_compose_merge_exact_key_overwrites(self):
        """Test that merge with exact same key overwrites."""
        # ARRANGE
        emb1 = MultiScaleEmbedding()
        vec1 = np.array([1.0, 0.0, 0.0])
        emb1.add("concept", vec1)

        emb2 = MultiScaleEmbedding()
        vec2 = np.array([0.0, 1.0, 0.0])
        emb2.add("concept", vec2)

        # ACT
        emb1.compose(emb2, strategy='merge', similarity_threshold=0.0)

        # ASSERT
        assert len(emb1.levels.get('default', {})) == 1
        result = emb1.get("concept")
        # Should be the second vector (overwritten)
        assert np.allclose(result, vec2)


class TestComposeAverageStrategy:
    """Tests for average strategy composition"""

    def test_compose_average_similar_embeddings(self):
        """Test average strategy blends similar embeddings."""
        # ARRANGE
        # Use similar vectors that have positive dot product
        emb_a = np.array([1.0, 0.1, 0.0])
        emb_a = emb_a / np.linalg.norm(emb_a)
        emb_b = np.array([0.9, 0.2, 0.0])
        emb_b = emb_b / np.linalg.norm(emb_b)

        emb1 = MultiScaleEmbedding()
        emb1.add("concept", emb_a)

        emb2 = MultiScaleEmbedding()
        emb2.add("similar_concept", emb_b)

        # ACT
        # Use low threshold so these similar vectors will be averaged
        emb1.compose(emb2, strategy='average', similarity_threshold=0.5)

        # ASSERT
        result = emb1.get("concept")
        # Should be average of emb_a and emb_b, then normalized
        expected = (emb_a + emb_b) / 2
        expected = expected / np.linalg.norm(expected)
        assert np.allclose(result, expected, atol=0.01)

    def test_compose_average_dissimilar_adds_new(self):
        """Test average strategy adds dissimilar embeddings as new."""
        # ARRANGE
        emb1 = MultiScaleEmbedding()
        vec1 = np.array([1.0, 0.0, 0.0])
        emb1.add("concept_a", vec1)

        emb2 = MultiScaleEmbedding()
        vec2 = np.array([0.0, 0.0, 1.0])
        emb2.add("concept_b", vec2)

        # ACT
        emb1.compose(emb2, strategy='average', similarity_threshold=0.95)

        # ASSERT
        assert len(emb1.levels.get('default', {})) == 2
        assert emb1.get("concept_a") is not None
        assert emb1.get("concept_b") is not None


class TestComposeAppendStrategy:
    """Tests for append strategy composition"""

    def test_compose_append_keeps_all(self):
        """Test append strategy keeps all items."""
        # ARRANGE
        emb1 = MultiScaleEmbedding()
        vec1 = np.random.randn(384)
        emb1.add("concept", vec1)

        emb2 = MultiScaleEmbedding()
        vec2 = np.random.randn(384)
        emb2.add("concept", vec2)  # Same key, different embedding

        # ACT
        emb1.compose(emb2, strategy='append')

        # ASSERT
        assert len(emb1.levels.get('default', {})) == 2  # Both kept
        assert emb1.get("concept") is not None
        assert emb1.get("concept_2") is not None  # Second one renamed

    def test_compose_append_unique_keys(self):
        """Test append strategy with already unique keys."""
        # ARRANGE
        emb1 = MultiScaleEmbedding()
        emb1.add("concept_a", np.random.randn(384))

        emb2 = MultiScaleEmbedding()
        emb2.add("concept_b", np.random.randn(384))

        # ACT
        emb1.compose(emb2, strategy='append')

        # ASSERT
        assert len(emb1.levels.get('default', {})) == 2
        assert emb1.get("concept_a") is not None
        assert emb1.get("concept_b") is not None

    def test_compose_append_multiple_conflicts(self):
        """Test append strategy with multiple key conflicts."""
        # ARRANGE
        emb1 = MultiScaleEmbedding()
        emb1.add("concept", np.random.randn(384))
        emb1.add("concept_2", np.random.randn(384))

        emb2 = MultiScaleEmbedding()
        # Add two different concepts (can't have duplicate keys in one dict)
        emb2.add("concept", np.random.randn(384))
        emb2.add("other", np.random.randn(384))

        # ACT
        emb1.compose(emb2, strategy='append')

        # ASSERT
        # Should have: concept, concept_2 (from emb1), concept_3 (from emb2's "concept"), other (from emb2)
        assert len(emb1.levels.get('default', {})) == 4
        assert emb1.get("concept") is not None
        assert emb1.get("concept_2") is not None
        assert emb1.get("concept_3") is not None
        assert emb1.get("other") is not None


class TestComposeDimensionValidation:
    """Tests for dimension mismatch detection"""

    def test_compose_dimension_mismatch_raises_error(self):
        """Test that dimension mismatch raises error."""
        emb1 = MultiScaleEmbedding()
        emb1.add("a", np.random.randn(128))

        emb2 = MultiScaleEmbedding()
        emb2.add("b", np.random.randn(384))

        with pytest.raises(ValueError, match="Dimension mismatch"):
            emb1.compose(emb2)

    def test_compose_empty_to_nonempty_works(self):
        """Test composing empty embeddings into non-empty works."""
        emb1 = MultiScaleEmbedding()
        emb1.add("a", np.random.randn(384))

        emb2 = MultiScaleEmbedding()  # Empty

        # Should not raise error
        emb1.compose(emb2, strategy='merge')
        assert len(emb1.levels.get('default', {})) == 1

    def test_compose_nonempty_to_empty_works(self):
        """Test composing non-empty into empty works."""
        emb1 = MultiScaleEmbedding()  # Empty

        emb2 = MultiScaleEmbedding()
        emb2.add("a", np.random.randn(384))

        # Should not raise error
        emb1.compose(emb2, strategy='merge')
        assert len(emb1.levels.get('default', {})) == 1


class TestComposeEdgeCases:
    """Tests for edge cases and error handling"""

    def test_compose_invalid_strategy_raises_error(self):
        """Test that invalid strategy raises error."""
        emb1 = MultiScaleEmbedding()
        emb2 = MultiScaleEmbedding()

        with pytest.raises(ValueError, match="Invalid strategy"):
            emb1.compose(emb2, strategy='invalid')

    def test_compose_wrong_type_raises_error(self):
        """Test that composing with wrong type raises error."""
        emb1 = MultiScaleEmbedding()

        with pytest.raises(TypeError, match="Can only compose with MultiScaleEmbedding"):
            emb1.compose({"not": "an embedding"})

    def test_compose_empty_embeddings(self):
        """Test composition of two empty embeddings."""
        emb1 = MultiScaleEmbedding()
        emb2 = MultiScaleEmbedding()

        # Should not raise error
        emb1.compose(emb2, strategy='merge')
        assert len(emb1.levels.get('default', {})) == 0

    def test_compose_returns_self(self):
        """Test that compose returns self for chaining."""
        emb1 = MultiScaleEmbedding()
        emb1.add("a", np.random.randn(384))

        emb2 = MultiScaleEmbedding()
        emb2.add("b", np.random.randn(384))

        result = emb1.compose(emb2, strategy='merge')
        assert result is emb1


class TestCompositionProperties:
    """Tests for mathematical properties of composition"""

    def test_merge_adds_nonoverlapping(self):
        """Test that merge correctly adds all non-overlapping items."""
        emb1 = MultiScaleEmbedding()
        for i in range(5):
            emb1.add(f"concept_{i}", np.random.randn(384))

        emb2 = MultiScaleEmbedding()
        for i in range(5, 10):
            emb2.add(f"concept_{i}", np.random.randn(384))

        emb1.compose(emb2, strategy='merge')
        assert len(emb1.levels.get('default', {})) == 10

    def test_append_is_commutative_in_size(self):
        """Test that append strategy results in same total size regardless of order."""
        # Create two embeddings
        emb1a = MultiScaleEmbedding()
        emb1a.add("a", np.random.randn(384))
        emb1a.add("b", np.random.randn(384))

        emb2a = MultiScaleEmbedding()
        emb2a.add("c", np.random.randn(384))

        emb1b = MultiScaleEmbedding()
        emb1b.add("a", np.random.randn(384))
        emb1b.add("b", np.random.randn(384))

        emb2b = MultiScaleEmbedding()
        emb2b.add("c", np.random.randn(384))

        # Compose in both orders
        emb1a.compose(emb2a, strategy='append')
        emb2b.compose(emb1b, strategy='append')

        # Should have same total size
        assert len(emb1a.levels.get('default', {})) == len(emb2b.levels.get('default', {}))


class TestSerialization:
    """Tests for to_dict and from_dict methods"""

    def test_to_dict_and_from_dict_roundtrip(self):
        """Test that serialization and deserialization work."""
        emb1 = MultiScaleEmbedding()
        emb1.add("a", np.array([1.0, 2.0, 3.0]))
        emb1.add("b", np.array([4.0, 5.0, 6.0]))

        # Serialize
        data = emb1.to_dict()

        # Deserialize
        emb2 = MultiScaleEmbedding.from_dict(data)

        # Check contents match
        assert len(emb2.levels.get('default', {})) == 2
        assert np.allclose(emb2.get("a"), np.array([1.0, 2.0, 3.0]))
        assert np.allclose(emb2.get("b"), np.array([4.0, 5.0, 6.0]))

    def test_from_dict_preserves_metadata(self):
        """Test that metadata is preserved during serialization."""
        emb1 = MultiScaleEmbedding()
        emb1.add("a", np.array([1.0, 2.0, 3.0]), metadata={"source": "test"})

        data = emb1.to_dict()
        emb2 = MultiScaleEmbedding.from_dict(data)

        # Get the embedding object directly to check metadata
        emb_obj = emb2.levels['default']['a']
        assert emb_obj.metadata == {"source": "test"}


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
