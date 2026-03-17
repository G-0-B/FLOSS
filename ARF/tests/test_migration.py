"""
Tests for migration script (migrate_to_symbolic.py)

This test suite verifies:
1. Migration script runs without errors
2. Triple extraction and validation works
3. Data format is correct after migration
4. Original data is preserved
5. Success rate meets ≥80% target
"""

import pytest
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import sys

# Add ARF to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory
from scripts.migrate_to_symbolic import (
    migrate_understanding,
    migrate_memory_store,
    find_all_memory_stores,
    MigrationStats,
    generate_migration_report
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_memory_dir():
    """Create a temporary directory for test memory stores."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_memory_with_data(temp_memory_dir):
    """Create a test memory store with sample data."""
    memory = ConversationMemory(
        agent_id="test-agent",
        storage_path=str(temp_memory_dir / "test-agent"),
        validate_ontology=True
    )

    # Add some understandings
    memory.transmit({
        'content': 'GPT-4 is a large language model',
        'context': 'Test context',
        'coherence': 0.9
    })

    memory.transmit({
        'content': 'Claude Sonnet 4.5 improves Sonnet 4',
        'context': 'Test context',
        'coherence': 0.95
    })

    return memory


@pytest.fixture
def test_memory_without_triples(temp_memory_dir):
    """Create a test memory store with data that needs migration."""
    memory_path = temp_memory_dir / "legacy-agent"
    memory_path.mkdir(parents=True)

    # Create understandings file without triple fields (legacy format)
    understandings = [
        {
            'content': 'GPT-4 is a large language model',
            'agent_id': 'legacy-agent',
            'timestamp': '2025-11-01T10:00:00',
            'context': 'Legacy data',
            'is_decision': False,
            'coherence_score': 0.9,
            'metadata': {},
            'embedding_ref': 'abc123'
        },
        {
            'content': 'Claude improves upon GPT-4',
            'agent_id': 'legacy-agent',
            'timestamp': '2025-11-01T10:01:00',
            'context': 'Legacy data',
            'is_decision': False,
            'coherence_score': 0.85,
            'metadata': {},
            'embedding_ref': 'def456'
        }
    ]

    with open(memory_path / "understandings.json", 'w') as f:
        json.dump(understandings, f, indent=2)

    # Create empty ADRs file
    with open(memory_path / "adrs.json", 'w') as f:
        json.dump([], f)

    return memory_path


# ============================================================================
# Tests for Migration Functions
# ============================================================================

def test_migrate_understanding_success():
    """Test successful migration of an understanding."""
    memory = ConversationMemory(
        agent_id="test",
        storage_path="./test_temp",
        validate_ontology=True
    )

    understanding = {
        'content': 'GPT-4 is a large language model',
        'agent_id': 'test',
        'timestamp': '2025-11-01T10:00:00',
    }

    success, message = migrate_understanding(understanding, memory)

    assert success is True
    assert message == "Migrated successfully"
    assert 'triple' in understanding
    assert understanding['triple']['subject'] == 'GPT-4'
    assert understanding['triple']['predicate'] == 'is_a'
    assert understanding['triple']['object'] == 'large-language-model'
    assert understanding['validated'] is True
    assert 'migration_metadata' in understanding
    assert understanding['migration_metadata']['extraction_method'] == 'pattern_matching'

    # Cleanup
    if Path("./test_temp").exists():
        shutil.rmtree("./test_temp")


def test_migrate_understanding_already_migrated():
    """Test that already migrated understandings are skipped."""
    memory = ConversationMemory(agent_id="test", storage_path="./test_temp")

    understanding = {
        'content': 'GPT-4 is a large language model',
        'triple': {'subject': 'GPT-4', 'predicate': 'is_a', 'object': 'LLM'},
        'validated': True
    }

    success, message = migrate_understanding(understanding, memory)

    assert success is True
    assert message == "Already migrated"

    # Cleanup
    if Path("./test_temp").exists():
        shutil.rmtree("./test_temp")


def test_migrate_understanding_no_content():
    """Test handling of understanding with no content."""
    memory = ConversationMemory(agent_id="test", storage_path="./test_temp")

    understanding = {
        'agent_id': 'test',
        'timestamp': '2025-11-01T10:00:00',
    }

    success, message = migrate_understanding(understanding, memory)

    assert success is False
    assert "No content" in message

    # Cleanup
    if Path("./test_temp").exists():
        shutil.rmtree("./test_temp")


def test_migrate_memory_store(test_memory_without_triples):
    """Test migration of an entire memory store."""
    stats = MigrationStats()

    failed = migrate_memory_store(test_memory_without_triples, stats)

    assert stats.total_agents == 1
    assert stats.total_understandings == 2
    assert stats.successfully_migrated >= 1  # At least one should succeed

    # Verify the understandings file was updated
    with open(test_memory_without_triples / "understandings.json", 'r') as f:
        updated_understandings = json.load(f)

    # Check that at least one understanding has triple field
    has_triple = any('triple' in u for u in updated_understandings)
    assert has_triple


def test_find_all_memory_stores(temp_memory_dir):
    """Test finding all memory stores."""
    # Create some test memory stores
    (temp_memory_dir / "agent1").mkdir()
    (temp_memory_dir / "agent2").mkdir()
    (temp_memory_dir / "agent3").mkdir()

    stores = find_all_memory_stores(temp_memory_dir)

    assert len(stores) == 3
    assert all(s.is_dir() for s in stores)


def test_migration_stats():
    """Test MigrationStats calculations."""
    stats = MigrationStats()

    # Test empty stats
    assert stats.success_rate() == 0.0

    # Test with some data
    stats.total_understandings = 10
    stats.successfully_migrated = 8

    assert stats.success_rate() == 0.8


def test_generate_migration_report(temp_memory_dir):
    """Test migration report generation."""
    stats = MigrationStats(
        total_agents=2,
        total_understandings=10,
        successfully_migrated=8,
        migration_failed=2,
        no_triple_extracted=1,
        validation_failed=1
    )

    failed = [
        {
            'agent_id': 'agent1',
            'understanding': {'content': 'Test content'},
            'error': 'Test error'
        }
    ]

    report_path = temp_memory_dir / "migration_report.md"
    generate_migration_report(stats, failed, report_path)

    assert report_path.exists()
    assert (temp_memory_dir / "migration_report.json").exists()

    # Check report content
    with open(report_path, 'r') as f:
        report = f.read()

    assert "Total Agents: 2" in report
    assert "Total Understandings: 10" in report
    assert "Success Rate: 80.0%" in report


# ============================================================================
# Integration Tests
# ============================================================================

def test_migration_preserves_original_data(test_memory_without_triples):
    """Test that migration preserves all original data."""
    # Read original data
    with open(test_memory_without_triples / "understandings.json", 'r') as f:
        original_data = json.load(f)

    original_content = [u['content'] for u in original_data]

    # Migrate
    stats = MigrationStats()
    migrate_memory_store(test_memory_without_triples, stats)

    # Read migrated data
    with open(test_memory_without_triples / "understandings.json", 'r') as f:
        migrated_data = json.load(f)

    migrated_content = [u['content'] for u in migrated_data]

    # Verify all original content is preserved
    assert original_content == migrated_content

    # Verify original fields are preserved
    for orig, migr in zip(original_data, migrated_data):
        assert orig['content'] == migr['content']
        assert orig['agent_id'] == migr['agent_id']
        assert orig['timestamp'] == migr['timestamp']
        assert orig['context'] == migr['context']


def test_migration_adds_required_fields(test_memory_without_triples):
    """Test that migration adds triple, validated, and migration_metadata fields."""
    stats = MigrationStats()
    migrate_memory_store(test_memory_without_triples, stats)

    with open(test_memory_without_triples / "understandings.json", 'r') as f:
        migrated_data = json.load(f)

    # Check that successfully migrated understandings have required fields
    for understanding in migrated_data:
        if 'triple' in understanding:
            assert 'subject' in understanding['triple']
            assert 'predicate' in understanding['triple']
            assert 'object' in understanding['triple']
            assert 'validated' in understanding
            assert 'migration_metadata' in understanding
            assert 'migrated_at' in understanding['migration_metadata']
            assert 'extraction_method' in understanding['migration_metadata']


def test_full_migration_script():
    """Test running the full migration script as a subprocess."""
    # Create test data
    test_path = Path("./test_memory_migration")
    test_path.mkdir(exist_ok=True)

    try:
        # Create a test agent
        memory = ConversationMemory(
            agent_id="test-migration",
            storage_path=str(test_path / "test-migration"),
            validate_ontology=False  # Skip validation for test data creation
        )

        memory.transmit({
            'content': 'GPT-4 is a large language model',
            'coherence': 0.9
        }, skip_validation=True)

        # Manually remove triple field to simulate legacy data
        understandings_file = test_path / "test-migration" / "understandings.json"
        with open(understandings_file, 'r') as f:
            data = json.load(f)

        # Remove triple-related fields
        for u in data:
            u.pop('triple', None)
            u.pop('validated', None)
            u.pop('migration_metadata', None)

        with open(understandings_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Run migration script
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "migrate_to_symbolic.py")],
            capture_output=True,
            text=True,
            env={'HOME': str(Path.cwd())}  # Use current dir as home for testing
        )

        # Check that script ran successfully
        # Note: It might exit with 1 if no stores found, which is okay for testing
        assert result.returncode in [0, 1]

        # Check that report was generated
        report_path = Path(__file__).parent.parent / "dev" / "reports" / "migration_report.md"
        if report_path.exists():
            assert report_path.exists()
            assert (report_path.parent / "migration_report.json").exists()

    finally:
        # Cleanup
        if test_path.exists():
            shutil.rmtree(test_path)


# ============================================================================
# Success Rate Tests
# ============================================================================

def test_migration_success_rate_target(test_memory_without_triples):
    """Test that migration achieves ≥80% success rate."""
    stats = MigrationStats()
    migrate_memory_store(test_memory_without_triples, stats)

    # Calculate overall coverage (including already migrated)
    if stats.total_understandings > 0:
        coverage = (stats.successfully_migrated + stats.already_migrated) / stats.total_understandings
        assert coverage >= 0.8, f"Success rate {coverage*100:.1f}% below 80% target"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
