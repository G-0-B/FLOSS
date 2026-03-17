"""
Tests for embedding_frames_of_scale serialization functionality.

This test suite verifies the to_dict() and from_dict() methods of MultiScaleEmbedding,
ensuring perfect round-trip serialization and proper error handling.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from embedding_frames_of_scale import Embedding, MultiScaleEmbedding


class TestMultiScaleEmbeddingSerialization:
    """Test serialization and deserialization of MultiScaleEmbedding."""

    def test_to_dict_basic(self):
        """Test that to_dict() produces expected structure."""
        mse = MultiScaleEmbedding()
        mse.add_embedding('fine', 'node1', np.array([1.0, 2.0, 3.0]))
        mse.add_embedding('fine', 'node2', np.array([4.0, 5.0, 6.0]))

        data = mse.to_dict()

        # Check structure
        assert 'levels' in data
        assert 'is_default_aggregator' in data
        assert 'fine' in data['levels']
        assert 'node1' in data['levels']['fine']
        assert 'node2' in data['levels']['fine']

        # Check vector serialization
        assert data['levels']['fine']['node1']['vector'] == [1.0, 2.0, 3.0]
        assert data['levels']['fine']['node2']['vector'] == [4.0, 5.0, 6.0]

    def test_to_dict_with_metadata(self):
        """Test that metadata is preserved in to_dict()."""
        mse = MultiScaleEmbedding()
        metadata = {'agent_id': 'test', 'timestamp': '2025-01-01'}
        mse.add_embedding('fine', 'node1', np.array([1.0, 2.0]), metadata)

        data = mse.to_dict()

        assert data['levels']['fine']['node1']['metadata'] == metadata

    def test_to_dict_empty(self):
        """Test that to_dict() works on empty MultiScaleEmbedding."""
        mse = MultiScaleEmbedding()
        data = mse.to_dict()

        assert data['levels'] == {}
        assert 'is_default_aggregator' in data

    def test_from_dict_round_trip_basic(self):
        """Test that serialization round-trip preserves state."""
        # ARRANGE
        original = MultiScaleEmbedding()
        original.add_embedding('fine', 'item1', np.random.randn(384))
        original.add_embedding('fine', 'item2', np.random.randn(384))

        # ACT
        serialized = original.to_dict()
        restored = MultiScaleEmbedding.from_dict(serialized)

        # ASSERT
        assert list(restored.levels.keys()) == list(original.levels.keys())
        for level in original.levels.keys():
            assert set(restored.levels[level].keys()) == set(original.levels[level].keys())
            for emb_id in original.levels[level].keys():
                original_vec = original.get_embedding(level, emb_id).vector
                restored_vec = restored.get_embedding(level, emb_id).vector
                assert np.allclose(original_vec, restored_vec)

    def test_from_dict_round_trip_with_metadata(self):
        """Test that metadata is preserved in round-trip."""
        # ARRANGE
        original = MultiScaleEmbedding()
        metadata = {'agent': 'test', 'context': 'important'}
        original.add_embedding('fine', 'node1', np.array([1.0, 2.0]), metadata)

        # ACT
        serialized = original.to_dict()
        restored = MultiScaleEmbedding.from_dict(serialized)

        # ASSERT
        restored_emb = restored.get_embedding('fine', 'node1')
        assert restored_emb.metadata == metadata
        assert np.allclose(restored_emb.vector, np.array([1.0, 2.0]))

    def test_from_dict_empty(self):
        """Test deserialization of empty embeddings."""
        original = MultiScaleEmbedding()
        serialized = original.to_dict()
        restored = MultiScaleEmbedding.from_dict(serialized)

        assert len(restored.levels) == 0

    def test_from_dict_multiple_levels(self):
        """Test round-trip with multiple levels."""
        # ARRANGE
        original = MultiScaleEmbedding()
        original.add_embedding('fine', 'n1', np.array([1.0, 2.0]))
        original.add_embedding('fine', 'n2', np.array([3.0, 4.0]))

        # Add coarse level
        original.add_coarse_level('coarse', 'fine', {'c1': ['n1', 'n2']})

        # ACT
        serialized = original.to_dict()
        restored = MultiScaleEmbedding.from_dict(serialized)

        # ASSERT
        assert set(restored.levels.keys()) == {'fine', 'coarse'}

        # Check fine level
        assert np.allclose(
            restored.get_embedding('fine', 'n1').vector,
            np.array([1.0, 2.0])
        )

        # Check coarse level
        coarse_emb = restored.get_embedding('coarse', 'c1')
        expected_coarse = np.array([1.0, 2.0]) + np.array([3.0, 4.0])
        assert np.allclose(coarse_emb.vector, expected_coarse)

    def test_from_dict_invalid_data_not_dict(self):
        """Test that invalid data raises clear errors."""
        with pytest.raises(TypeError, match="Expected dict"):
            MultiScaleEmbedding.from_dict("not a dict")

    def test_from_dict_missing_levels_field(self):
        """Test error when 'levels' field is missing."""
        with pytest.raises(ValueError, match="Missing required field: 'levels'"):
            MultiScaleEmbedding.from_dict({})

    def test_from_dict_levels_not_dict(self):
        """Test error when 'levels' is not a dict."""
        with pytest.raises(TypeError, match="Expected 'levels' to be dict"):
            MultiScaleEmbedding.from_dict({'levels': 'not a dict'})

    def test_from_dict_embeddings_not_dict(self):
        """Test error when embeddings at a level are not a dict."""
        with pytest.raises(TypeError, match="Expected embeddings at level"):
            MultiScaleEmbedding.from_dict({
                'levels': {'fine': 'not a dict'}
            })

    def test_from_dict_missing_vector(self):
        """Test error when embedding data is missing vector field."""
        with pytest.raises(ValueError, match="Missing 'vector' field"):
            MultiScaleEmbedding.from_dict({
                'levels': {
                    'fine': {
                        'node1': {'metadata': {}}
                    }
                }
            })

    def test_from_dict_invalid_vector_type(self):
        """Test error when vector is not list or ndarray."""
        with pytest.raises(TypeError, match="Invalid vector type"):
            MultiScaleEmbedding.from_dict({
                'levels': {
                    'fine': {
                        'node1': {'vector': 'not a list'}
                    }
                }
            })

    def test_from_dict_invalid_metadata_type(self):
        """Test error when metadata is not a dict."""
        with pytest.raises(TypeError, match="Expected metadata"):
            MultiScaleEmbedding.from_dict({
                'levels': {
                    'fine': {
                        'node1': {
                            'vector': [1.0, 2.0],
                            'metadata': 'not a dict'
                        }
                    }
                }
            })

    def test_from_dict_float_precision(self):
        """Test that float precision is maintained within reasonable tolerance."""
        original = MultiScaleEmbedding()
        # Use specific float values that might have precision issues
        vec = np.array([0.1, 0.2, 0.3, 1.0/3.0, np.pi], dtype=np.float32)
        original.add_embedding('fine', 'test', vec)

        serialized = original.to_dict()
        restored = MultiScaleEmbedding.from_dict(serialized)

        restored_vec = restored.get_embedding('fine', 'test').vector

        # Check with appropriate tolerance for float32
        assert np.allclose(vec, restored_vec, rtol=1e-6, atol=1e-8)

    def test_from_dict_large_embeddings(self):
        """Test round-trip with large embedding collections."""
        original = MultiScaleEmbedding()

        # Add many embeddings
        for i in range(100):
            vec = np.random.randn(384).astype(np.float32)
            original.add_embedding('fine', f'node_{i}', vec)

        serialized = original.to_dict()
        restored = MultiScaleEmbedding.from_dict(serialized)

        # Verify all embeddings match
        assert len(restored.levels['fine']) == 100
        for i in range(100):
            original_vec = original.get_embedding('fine', f'node_{i}').vector
            restored_vec = restored.get_embedding('fine', f'node_{i}').vector
            assert np.allclose(original_vec, restored_vec, rtol=1e-6)

    def test_from_dict_with_ndarray_input(self):
        """Test that from_dict() can handle numpy arrays directly (not just lists)."""
        data = {
            'levels': {
                'fine': {
                    'node1': {
                        'vector': np.array([1.0, 2.0, 3.0]),
                        'metadata': {}
                    }
                }
            },
            'is_default_aggregator': True
        }

        restored = MultiScaleEmbedding.from_dict(data)
        vec = restored.get_embedding('fine', 'node1').vector
        assert np.allclose(vec, np.array([1.0, 2.0, 3.0]))

    def test_from_dict_missing_metadata(self):
        """Test that missing metadata field defaults to empty dict."""
        data = {
            'levels': {
                'fine': {
                    'node1': {
                        'vector': [1.0, 2.0]
                    }
                }
            }
        }

        restored = MultiScaleEmbedding.from_dict(data)
        emb = restored.get_embedding('fine', 'node1')
        assert emb.metadata == {}


class TestEmbeddingClass:
    """Test the Embedding dataclass."""

    def test_embedding_creation(self):
        """Test basic embedding creation."""
        vec = np.array([1.0, 2.0, 3.0])
        emb = Embedding(vector=vec)

        assert np.array_equal(emb.vector, vec)
        assert emb.metadata == {}

    def test_embedding_with_metadata(self):
        """Test embedding with metadata."""
        vec = np.array([1.0, 2.0])
        meta = {'source': 'test'}
        emb = Embedding(vector=vec, metadata=meta)

        assert emb.metadata == meta

    def test_embedding_validates_ndarray(self):
        """Test that Embedding requires numpy array."""
        with pytest.raises(TypeError, match="vector must be a numpy.ndarray"):
            Embedding(vector=[1.0, 2.0])

    def test_embedding_validates_1d(self):
        """Test that Embedding requires 1D array."""
        with pytest.raises(ValueError, match="vector must be one‑dimensional"):
            Embedding(vector=np.array([[1.0, 2.0], [3.0, 4.0]]))


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
