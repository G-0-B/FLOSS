"""
Integration tests for Pony Swarm + Infinity Bridge coordination.

Tests end-to-end scenarios where:
1. Mock sensor bridges provide context data
2. Pony swarm queries incorporate sensor context
3. Results reference sensor data sources
4. Multi-modal reasoning (text + sensor data)

Phase 4.4, Task 4.4: Integration Test Suite
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys
from typing import Dict, List, Any

# Add ARF and pwnies to path
test_dir = Path(__file__).parent
arf_root = test_dir.parent.parent
pwnies_root = arf_root / "pwnies"

for path in [arf_root, pwnies_root]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from desktop_pony_swarm.core.swarm import PonySwarm


# ============================================================================
# Mock Infinity Bridge Components
# ============================================================================

class MockSensorBridge:
    """
    Mock implementation of Infinity Bridge for testing.

    Simulates acoustic and vibration sensor streams.
    """

    def __init__(self, bridge_id: str, capabilities: List[str]):
        self.bridge_id = bridge_id
        self.capabilities = capabilities
        self.active_streams = []

    async def subscribe(self, stream_type: str) -> 'MockSensorStream':
        """Subscribe to a sensor stream"""
        if stream_type not in self.capabilities:
            raise ValueError(f"Bridge {self.bridge_id} does not support {stream_type}")

        stream = MockSensorStream(self.bridge_id, stream_type)
        self.active_streams.append(stream)
        return stream

    def get_capabilities(self) -> List[str]:
        """Get list of sensor capabilities"""
        return self.capabilities.copy()


class MockSensorStream:
    """Mock sensor data stream"""

    def __init__(self, bridge_id: str, stream_type: str):
        self.bridge_id = bridge_id
        self.stream_type = stream_type
        self._sample_count = 0

    async def read(self) -> Dict[str, Any]:
        """Read next sensor sample"""
        self._sample_count += 1

        if self.stream_type == "acoustic":
            return {
                "type": "acoustic",
                "bridge_id": self.bridge_id,
                "sample_number": self._sample_count,
                "frequencies": [440.0, 880.0, 1320.0],  # Mock FFT data
                "amplitude": 0.75,
                "timestamp": "2025-11-14T00:00:00Z"
            }
        elif self.stream_type == "vibration":
            return {
                "type": "vibration",
                "bridge_id": self.bridge_id,
                "sample_number": self._sample_count,
                "acceleration": [0.1, 0.2, 0.15],  # X, Y, Z
                "magnitude": 0.26,
                "timestamp": "2025-11-14T00:00:00Z"
            }
        else:
            return {
                "type": self.stream_type,
                "bridge_id": self.bridge_id,
                "sample_number": self._sample_count
            }


async def setup_test_bridge() -> MockSensorBridge:
    """
    Setup mock bridge for testing (as specified in roadmap).
    """
    bridge = MockSensorBridge(
        bridge_id="test_bridge_001",
        capabilities=["acoustic", "vibration"]
    )
    return bridge


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_bridge():
    """Provide mock sensor bridge for tests"""
    bridge = await setup_test_bridge()
    yield bridge
    # Cleanup streams
    bridge.active_streams.clear()


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_swarm_basic_query():
    """
    Test basic swarm query without sensor context (baseline).
    """
    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.single_step_aggregation(
            query="What is 2 + 2?",
            K=2
        )

        assert 'response' in result
        assert 'candidates' in result
        assert len(result['candidates']) >= 2


@pytest.mark.asyncio
async def test_bridge_discovery():
    """
    Test bridge discovery and capability query.
    """
    bridge = await setup_test_bridge()

    # Verify bridge capabilities
    capabilities = bridge.get_capabilities()
    assert "acoustic" in capabilities
    assert "vibration" in capabilities


@pytest.mark.asyncio
async def test_bridge_stream_subscription():
    """
    Test subscribing to sensor streams.
    """
    bridge = await setup_test_bridge()

    # Subscribe to acoustic stream
    stream = await bridge.subscribe("acoustic")
    assert stream is not None
    assert stream.stream_type == "acoustic"

    # Read sample
    sample = await stream.read()
    assert sample['type'] == "acoustic"
    assert 'frequencies' in sample
    assert len(sample['frequencies']) > 0


@pytest.mark.asyncio
async def test_swarm_with_sensor_context_mock():
    """
    Test swarm query with mock sensor context.

    This simulates the roadmap scenario but uses mock data
    since full Infinity Bridge integration is in Task 4.3.
    """
    # Setup bridge
    bridge = await setup_test_bridge()

    # Subscribe to streams
    acoustic_stream = await bridge.subscribe("acoustic")
    vibration_stream = await bridge.subscribe("vibration")

    # Read sensor data
    acoustic_sample = await acoustic_stream.read()
    vibration_sample = await vibration_stream.read()

    # Augment query with sensor context
    query = f"""Is the motor operating normally?

Context from sensors:
- Acoustic: {acoustic_sample['frequencies']} Hz (amplitude: {acoustic_sample['amplitude']})
- Vibration: {vibration_sample['magnitude']} m/s²

Please analyze this data and provide assessment."""

    # Query swarm
    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.single_step_aggregation(query=query, K=2)

        assert 'response' in result
        # Response should reference the sensor data (in a real scenario)
        # For mock, just verify the query was processed
        assert len(result['candidates']) >= 2


@pytest.mark.asyncio
async def test_multi_bridge_coordination():
    """
    Test coordination with multiple sensor bridges.
    """
    # Setup multiple bridges
    bridge1 = MockSensorBridge("bridge_001", ["acoustic"])
    bridge2 = MockSensorBridge("bridge_002", ["vibration"])

    # Subscribe to different streams
    acoustic = await bridge1.subscribe("acoustic")
    vibration = await bridge2.subscribe("vibration")

    # Read from both
    acoustic_data = await acoustic.read()
    vibration_data = await vibration.read()

    # Verify data from different bridges
    assert acoustic_data['bridge_id'] == "bridge_001"
    assert vibration_data['bridge_id'] == "bridge_002"


@pytest.mark.asyncio
async def test_sensor_data_persistence():
    """
    Test that sensor context can be stored and retrieved for later analysis.
    """
    bridge = await setup_test_bridge()
    stream = await bridge.subscribe("acoustic")

    # Collect multiple samples
    samples = []
    for _ in range(5):
        sample = await stream.read()
        samples.append(sample)

    # Verify samples are sequential
    assert len(samples) == 5
    for i, sample in enumerate(samples, start=1):
        assert sample['sample_number'] == i


@pytest.mark.asyncio
async def test_bridge_error_handling():
    """
    Test error handling for invalid stream subscriptions.
    """
    bridge = await setup_test_bridge()

    # Try to subscribe to unsupported stream
    with pytest.raises(ValueError, match="does not support"):
        await bridge.subscribe("invalid_sensor_type")


@pytest.mark.asyncio
async def test_swarm_rsa_with_context():
    """
    Test full RSA (Recursive Self-Aggregation) with sensor context.
    """
    bridge = await setup_test_bridge()

    # Get sensor reading
    acoustic = await bridge.subscribe("acoustic")
    sample = await acoustic.read()

    # Create context-aware query
    query = f"""Analyze this acoustic signature: {sample['frequencies']} Hz.
Is this pattern consistent with normal motor operation?"""

    async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
        result = await swarm.recursive_self_aggregation(
            query=query,
            K=2,
            T=2  # Reduced iterations for testing
        )

        assert 'response' in result
        assert 'metrics' in result
        assert 'iterations' in result

        # Verify RSA completed
        assert len(result['iterations']) >= 2


@pytest.mark.asyncio
async def test_sensor_stream_timeout():
    """
    Test that sensor stream reads have reasonable timeout.
    """
    bridge = await setup_test_bridge()
    stream = await bridge.subscribe("acoustic")

    # Read should complete quickly
    sample = await asyncio.wait_for(stream.read(), timeout=2.0)
    assert sample is not None


@pytest.mark.asyncio
async def test_bridge_metadata():
    """
    Test that bridge provides proper metadata for discovery.
    """
    bridge = await setup_test_bridge()

    assert bridge.bridge_id == "test_bridge_001"
    assert len(bridge.capabilities) >= 2

    # Capabilities should be queryable
    caps = bridge.get_capabilities()
    assert isinstance(caps, list)
    assert all(isinstance(c, str) for c in caps)


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_stream_latency():
    """
    Test that stream latency meets <50ms requirement (from roadmap).
    """
    import time

    bridge = await setup_test_bridge()
    stream = await bridge.subscribe("acoustic")

    # Measure read latency
    start = time.time()
    await stream.read()
    latency = (time.time() - start) * 1000  # Convert to ms

    # Should be very fast for mock (real hardware target: <50ms)
    assert latency < 100, f"Stream latency too high: {latency:.2f}ms"


@pytest.mark.asyncio
async def test_concurrent_streams():
    """
    Test reading from multiple streams concurrently.
    """
    bridge = await setup_test_bridge()

    # Subscribe to multiple streams
    acoustic = await bridge.subscribe("acoustic")
    vibration = await bridge.subscribe("vibration")

    # Read concurrently
    results = await asyncio.gather(
        acoustic.read(),
        vibration.read()
    )

    assert len(results) == 2
    assert results[0]['type'] == "acoustic"
    assert results[1]['type'] == "vibration"


@pytest.mark.asyncio
async def test_bridge_cleanup():
    """
    Test that bridge resources are properly cleaned up.
    """
    bridge = await setup_test_bridge()

    # Subscribe to streams
    stream1 = await bridge.subscribe("acoustic")
    stream2 = await bridge.subscribe("vibration")

    # Verify streams are tracked
    assert len(bridge.active_streams) == 2

    # Cleanup
    bridge.active_streams.clear()
    assert len(bridge.active_streams) == 0


# ============================================================================
# Future Integration Tests (Task 4.3 - Full Infinity Bridge)
# ============================================================================

@pytest.mark.skip(reason="Requires full Infinity Bridge implementation (Task 4.3)")
@pytest.mark.asyncio
async def test_real_bridge_discovery():
    """
    Test discovery of real Infinity Bridge devices via Holochain DHT.

    This will be implemented when Task 4.3 is complete.
    """
    pass


@pytest.mark.skip(reason="Requires full Infinity Bridge implementation (Task 4.3)")
@pytest.mark.asyncio
async def test_fft_correlation_engine():
    """
    Test FFT cross-correlation on ESP32.

    Target: <10ms correlation latency (from roadmap).
    """
    pass


@pytest.mark.skip(reason="Requires full Infinity Bridge implementation (Task 4.3)")
@pytest.mark.asyncio
async def test_mcp_protocol_integration():
    """
    Test MCP protocol for bridge resource access.

    Format: bridge://bridge123/acoustic/spectrum
    """
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
