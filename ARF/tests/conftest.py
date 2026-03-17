"""
Shared pytest fixtures for ARF test suite.

Provides common test utilities, mocks, and temporary resources
for unit and integration tests.

Phase 4 Post-Merge Enhancement
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Generator
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory


@pytest.fixture(scope="session")
def temp_test_root() -> Generator[Path, None, None]:
    """
    Session-scoped temporary directory for all tests.

    Automatically cleaned up after test session completes.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="arf_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_data_dir(temp_test_root: Path) -> Generator[Path, None, None]:
    """
    Function-scoped temporary directory for test data.

    Each test gets its own isolated directory.
    """
    test_dir = temp_test_root / f"test_{pytest.current_test_name}"
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    # Cleanup after test
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def mock_memory(temp_data_dir: Path) -> ConversationMemory:
    """
    Create a ConversationMemory instance for testing.

    Uses temporary storage that's automatically cleaned up.
    """
    return ConversationMemory(
        agent_id="test_agent",
        storage_path=str(temp_data_dir / "memory.json")
    )


@pytest.fixture
def mock_memory_alice(temp_data_dir: Path) -> ConversationMemory:
    """Create ConversationMemory for agent 'alice'."""
    return ConversationMemory(
        agent_id="alice",
        storage_path=str(temp_data_dir / "memory_alice.json")
    )


@pytest.fixture
def mock_memory_bob(temp_data_dir: Path) -> ConversationMemory:
    """Create ConversationMemory for agent 'bob'."""
    return ConversationMemory(
        agent_id="bob",
        storage_path=str(temp_data_dir / "memory_bob.json")
    )


@pytest.fixture
def mock_memory_carol(temp_data_dir: Path) -> ConversationMemory:
    """Create ConversationMemory for agent 'carol'."""
    return ConversationMemory(
        agent_id="carol",
        storage_path=str(temp_data_dir / "memory_carol.json")
    )


@pytest.fixture
def sample_understanding():
    """Sample understanding data for testing."""
    return {
        "content": "Claude Sonnet 4 is a large language model.",
        "metadata": {
            "source": "test",
            "timestamp": "2025-11-14T00:00:00Z",
        }
    }


@pytest.fixture
def sample_understandings():
    """Multiple sample understandings for testing."""
    return [
        {
            "content": "GPT-4 is a language model by OpenAI.",
            "metadata": {"source": "test1"},
        },
        {
            "content": "Claude is a language model by Anthropic.",
            "metadata": {"source": "test2"},
        },
        {
            "content": "LLMs use transformer architecture.",
            "metadata": {"source": "test3"},
        },
    ]


# Swarm fixtures (optional - only if swarm is available)
try:
    from pwnies.desktop_pony_swarm.core.swarm import PonySwarm
    from pwnies.desktop_pony_swarm.core.adaptive_params import RSAParams

    @pytest.fixture
    def mock_swarm_config():
        """Mock configuration for PonySwarm testing."""
        return {
            "N": 2,  # Small for fast tests
            "K": 1,
            "T": 2,
            "use_mock": True,  # Use mock Horde client for tests
        }

    @pytest.fixture
    def mock_swarm(mock_swarm_config):
        """Create a PonySwarm instance with test configuration."""
        # Note: Actual creation would depend on PonySwarm API
        # This is a placeholder that tests can override
        return None

    @pytest.fixture
    def sample_rsa_params():
        """Sample RSA parameters for testing."""
        return RSAParams(N=4, K=2, T=3)

except ImportError:
    # Swarm not available - skip swarm fixtures
    pass


# Bridge fixtures (optional - only if bridge is available)
try:
    from in_finite_nrg.infinity_bridge.orchestrator.discovery import BridgeDiscovery

    @pytest.fixture
    def mock_bridge_config():
        """Mock configuration for Infinity Bridge testing."""
        return {
            "use_mock": True,
            "timeout": 1.0,
        }

    @pytest.fixture
    def mock_bridge_discovery(mock_bridge_config):
        """Create a mock BridgeDiscovery for testing."""
        return BridgeDiscovery(use_mocks=True)

except ImportError:
    # Bridge not available - skip bridge fixtures
    pass


# Holochain fixtures (for integration tests)
@pytest.fixture
def mock_holochain_conductor():
    """
    Mock Holochain conductor for testing.

    Returns a mock object that simulates conductor operations
    without requiring actual Holochain installation.
    """
    class MockConductor:
        def __init__(self):
            self.entries = {}

        def create_entry(self, entry_type: str, content: dict):
            entry_hash = f"mock_hash_{len(self.entries)}"
            self.entries[entry_hash] = {
                "type": entry_type,
                "content": content,
            }
            return entry_hash

        def get_entry(self, entry_hash: str):
            return self.entries.get(entry_hash)

        def query_entries(self, entry_type: str):
            return [
                (hash, entry)
                for hash, entry in self.entries.items()
                if entry["type"] == entry_type
            ]

    return MockConductor()


@pytest.fixture(autouse=True)
def reset_logging():
    """
    Reset logging configuration between tests.

    Prevents log spam from accumulating across tests.
    """
    import logging
    # Clear all handlers from root logger
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    yield

    # Cleanup after test
    for handler in root.handlers[:]:
        root.removeHandler(handler)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_swarm: marks tests that require pony swarm"
    )
    config.addinivalue_line(
        "markers", "requires_bridge: marks tests that require infinity bridge"
    )
    config.addinivalue_line(
        "markers", "requires_holochain: marks tests that require Holochain conductor"
    )


# Helper to track current test name
@pytest.fixture(autouse=True)
def track_test_name(request):
    """Track the current test name for fixture use."""
    pytest.current_test_name = request.node.name
    yield
    pytest.current_test_name = None
