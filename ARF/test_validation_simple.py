#!/usr/bin/env python3
"""
Simple standalone test to verify validation functionality.
This doesn't require sentence-transformers.
"""
import sys
import tempfile
import shutil
from pathlib import Path

# Add ARF to path
sys.path.insert(0, str(Path(__file__).parent))

# Temporarily disable embeddings to avoid needing sentence-transformers
import conversation_memory
conversation_memory.EMBEDDINGS_AVAILABLE = False

from conversation_memory import ConversationMemory

def test_triple_extraction():
    """Test triple extraction patterns."""
    print("Testing triple extraction...")
    temp_dir = tempfile.mkdtemp()
    try:
        memory = ConversationMemory(agent_id="test", storage_path=temp_dir)

        # Test is_a pattern
        triple = memory._extract_triple({'content': 'GPT-4 is a large language model'})
        assert triple == ('GPT-4', 'is_a', 'large-language-model'), f"Got: {triple}"
        print("  ✓ is_a pattern works")

        # Test improves_upon pattern
        triple = memory._extract_triple({'content': 'Version2 improves Version1'})
        assert triple == ('Version2', 'improves_upon', 'Version1'), f"Got: {triple}"
        print("  ✓ improves_upon pattern works")

        # Test default fallback
        triple = memory._extract_triple({'content': 'Random text'})
        assert triple[0] == 'test', f"Got: {triple}"
        assert triple[1] == 'stated', f"Got: {triple}"
        print("  ✓ default fallback works")

        # Test empty content
        triple = memory._extract_triple({'content': ''})
        assert triple is None, f"Got: {triple}"
        print("  ✓ empty content returns None")

    finally:
        shutil.rmtree(temp_dir)

def test_validation():
    """Test triple validation."""
    print("\nTesting triple validation...")
    temp_dir = tempfile.mkdtemp()
    try:
        memory = ConversationMemory(agent_id="test", storage_path=temp_dir)

        # Test valid triple
        is_valid, error = memory._validate_triple(('X', 'is_a', 'Y'))
        assert is_valid is True, f"Got: {is_valid}, {error}"
        assert error is None
        print("  ✓ valid triple passes")

        # Test invalid predicate
        is_valid, error = memory._validate_triple(('X', 'bad_predicate', 'Y'))
        assert is_valid is False, f"Got: {is_valid}, {error}"
        assert 'Unknown predicate' in error
        print("  ✓ invalid predicate rejected")

        # Test empty subject
        is_valid, error = memory._validate_triple(('', 'is_a', 'Y'))
        assert is_valid is False
        assert 'non-empty' in error
        print("  ✓ empty subject rejected")

        # Test validation can be disabled
        memory2 = ConversationMemory(agent_id="test", storage_path=temp_dir,
                                     validate_ontology=False)
        is_valid, error = memory2._validate_triple(('X', 'invalid', 'Y'))
        assert is_valid is True
        print("  ✓ validation can be disabled")

    finally:
        shutil.rmtree(temp_dir)

def test_transmit_with_validation():
    """Test transmit with validation."""
    print("\nTesting transmit with validation...")
    temp_dir = tempfile.mkdtemp()
    try:
        memory = ConversationMemory(agent_id="test", storage_path=temp_dir)

        # Valid understanding should pass
        ref = memory.transmit({'content': 'Python is a language'})
        assert ref is not None, "Valid understanding should be accepted"
        assert memory.validation_stats['validation_passed'] == 1
        print("  ✓ valid understanding accepted")

        # Skip validation
        ref = memory.transmit({'content': 'Random stuff'}, skip_validation=True)
        assert ref is not None
        assert memory.validation_stats['validation_skipped'] == 1
        print("  ✓ validation can be skipped")

        # Empty content should fail
        ref = memory.transmit({'content': ''})
        assert ref is None, "Empty content should be rejected"
        assert memory.validation_stats['validation_failed'] == 1
        print("  ✓ invalid understanding rejected")

        # Test statistics
        stats = memory.get_validation_stats()
        assert stats['total_attempts'] == 3
        assert stats['validation_passed'] == 1
        assert stats['validation_failed'] == 1
        assert stats['validation_skipped'] == 1
        print("  ✓ statistics tracked correctly")

    finally:
        shutil.rmtree(temp_dir)

def test_all_known_predicates():
    """Test all known predicates are valid."""
    print("\nTesting all known predicates...")
    temp_dir = tempfile.mkdtemp()
    try:
        memory = ConversationMemory(agent_id="test", storage_path=temp_dir)

        # Synchronized with ontology_integrity/src/lib.rs get_relation()
        known_predicates = ['is_a', 'part_of', 'related_to', 'has_property',
                           'improves_upon', 'capable_of', 'trained_on',
                           'evaluated_on', 'stated']

        for predicate in known_predicates:
            is_valid, error = memory._validate_triple(('X', predicate, 'Y'))
            assert is_valid is True, f"Predicate {predicate} should be valid"

        print(f"  ✓ all {len(known_predicates)} known predicates are valid")

    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("=" * 60)
    print("VALIDATION INTEGRATION TESTS")
    print("=" * 60)

    try:
        test_triple_extraction()
        test_validation()
        test_transmit_with_validation()
        test_all_known_predicates()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ ERROR: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)
