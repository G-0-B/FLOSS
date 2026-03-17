#!/usr/bin/env python3
"""
Integration tests for Infinity Bridge protocol
Tests discovery, subscription, streaming, and correlation
"""
import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from orchestrator.discovery import MockBridgeDiscovery, BridgeInfo
from orchestrator.mcp_server import InfinityBridgeMCPServer, MockBridgeStream


class TestBridgeDiscovery:
    """Test bridge discovery protocol"""

    @pytest.mark.asyncio
    async def test_discover_bridges(self):
        """Test discovering all bridges"""
        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges(timeout=5)

        assert len(bridges) >= 1, "Should discover at least one bridge"

        for bridge in bridges:
            assert bridge.bridge_id, "Bridge ID should not be empty"
            assert len(bridge.capabilities) > 0, "Bridge should have capabilities"
            assert len(bridge.transport) > 0, "Bridge should have transport"
            assert bridge.endpoint, "Bridge should have endpoint"

    @pytest.mark.asyncio
    async def test_discover_by_capability(self):
        """Test discovering bridges by capability"""
        discovery = MockBridgeDiscovery()

        # Test acoustic capability
        bridges = await discovery.discover_by_capability("acoustic_20hz_20khz")
        assert len(bridges) >= 1, "Should find at least one acoustic bridge"

        for bridge in bridges:
            assert "acoustic_20hz_20khz" in bridge.capabilities

    @pytest.mark.asyncio
    async def test_discovery_timeout(self):
        """Test discovery timeout handling"""
        discovery = MockBridgeDiscovery()

        # Should complete within timeout
        bridges = await discovery.discover_bridges(timeout=1.0)
        assert bridges is not None, "Discovery should not return None"

    @pytest.mark.asyncio
    async def test_bridge_registration_validation(self):
        """Test bridge registration validation"""
        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        for bridge in bridges:
            # Validate required fields
            assert bridge.bridge_id
            assert bridge.capabilities
            assert bridge.transport
            assert bridge.endpoint
            assert bridge.signature


class TestStreamSubscription:
    """Test stream subscription protocol"""

    @pytest.mark.asyncio
    async def test_stream_subscription(self):
        """Test subscribing to a bridge stream"""
        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        assert len(bridges) > 0, "Need at least one bridge"

        bridge = bridges[0]
        stream = MockBridgeStream(bridge, "acoustic/spectrum")

        connected = await stream.connect()
        assert connected, "Stream connection should succeed"
        assert stream.connected, "Stream should be marked as connected"

        await stream.close()
        assert not stream.connected, "Stream should be disconnected"

    @pytest.mark.asyncio
    async def test_stream_read_single(self):
        """Test reading a single sample from stream"""
        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        bridge = bridges[0]
        stream = MockBridgeStream(bridge, "acoustic/spectrum")
        await stream.connect()

        sample = await stream.read()

        assert sample is not None, "Should receive a sample"
        assert sample.bridge_id == bridge.bridge_id
        assert sample.timestamp_ns > 0
        assert sample.sample_rate_hz > 0
        assert len(sample.frequencies) > 0

        await stream.close()

    @pytest.mark.asyncio
    async def test_stream_read_multiple(self):
        """Test reading multiple samples from stream"""
        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        bridge = bridges[0]
        stream = MockBridgeStream(bridge, "acoustic/spectrum")
        await stream.connect()

        samples = await stream.read_n(10, timeout=2.0)

        assert len(samples) == 10, "Should receive 10 samples"

        # Verify timestamps are increasing
        for i in range(1, len(samples)):
            assert samples[i].timestamp_ns >= samples[i-1].timestamp_ns

        await stream.close()

    @pytest.mark.asyncio
    async def test_stream_latency(self):
        """Test stream latency meets <50ms requirement"""
        import time

        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        bridge = bridges[0]
        stream = MockBridgeStream(bridge, "acoustic/spectrum")
        await stream.connect()

        latencies = []
        for _ in range(10):
            t0 = time.time()
            sample = await stream.read()
            latency_ms = (time.time() - t0) * 1000
            latencies.append(latency_ms)

            assert sample is not None

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 50, f"Average latency {avg_latency:.1f}ms exceeds 50ms requirement"

        await stream.close()


class TestMCPServer:
    """Test MCP server functionality"""

    @pytest.mark.asyncio
    async def test_server_start(self):
        """Test MCP server startup"""
        server = InfinityBridgeMCPServer(mock=True)

        await server.start()

        bridges = server.discovery.list_bridges()
        assert len(bridges) > 0, "Server should discover bridges on startup"

        await server.stop()

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test listing MCP resources"""
        server = InfinityBridgeMCPServer(mock=True)
        await server.start()

        resources = await server.list_resources()

        assert len(resources) > 0, "Should have at least one resource"

        for resource in resources:
            assert resource['uri'].startswith('bridge://'), "Resource URI should use bridge:// scheme"
            assert 'name' in resource
            assert 'description' in resource
            assert 'mime_type' in resource

        await server.stop()

    @pytest.mark.asyncio
    async def test_subscribe_to_stream(self):
        """Test subscribing to stream via MCP server"""
        server = InfinityBridgeMCPServer(mock=True)
        await server.start()

        # Mock stream for testing
        async def mock_subscribe(bridge_id: str, stream_type: str):
            bridge = server.discovery.get_bridge(bridge_id)
            if bridge:
                stream = MockBridgeStream(bridge, stream_type)
                await stream.connect()
                return stream
            return None

        server.subscribe_to_stream = mock_subscribe

        stream = await server.subscribe_to_stream("acoustic-esp32-001", "acoustic/spectrum")

        assert stream is not None, "Subscription should succeed"
        assert stream.connected, "Stream should be connected"

        await stream.close()
        await server.stop()

    @pytest.mark.asyncio
    async def test_read_resource(self):
        """Test reading from MCP resource URI"""
        server = InfinityBridgeMCPServer(mock=True)
        await server.start()

        # Mock stream for testing
        async def mock_subscribe(bridge_id: str, stream_type: str):
            bridge = server.discovery.get_bridge(bridge_id)
            if bridge:
                stream = MockBridgeStream(bridge, stream_type)
                await stream.connect()
                return stream
            return None

        server.subscribe_to_stream = mock_subscribe

        uri = "bridge://acoustic-esp32-001/acoustic/spectrum"
        samples = await server.read_resource(uri, num_samples=5)

        assert len(samples) == 5, "Should receive 5 samples"

        for sample in samples:
            assert sample.bridge_id == "acoustic-esp32-001"
            assert len(sample.frequencies) > 0

        await server.stop()


class TestPerformanceMetrics:
    """Test performance against success metrics"""

    @pytest.mark.asyncio
    async def test_discovery_latency(self):
        """Test bridge discovery <1s requirement"""
        import time

        discovery = MockBridgeDiscovery()

        t0 = time.time()
        bridges = await discovery.discover_bridges()
        discovery_time_ms = (time.time() - t0) * 1000

        assert len(bridges) > 0, "Should discover bridges"
        assert discovery_time_ms < 1000, f"Discovery took {discovery_time_ms:.1f}ms (>1s)"

    @pytest.mark.asyncio
    async def test_stream_latency_requirement(self):
        """Test stream latency <50ms requirement"""
        import time

        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        bridge = bridges[0]
        stream = MockBridgeStream(bridge, "acoustic/spectrum")
        await stream.connect()

        latencies = []
        for _ in range(20):
            t0 = time.time()
            sample = await stream.read()
            latency_ms = (time.time() - t0) * 1000
            latencies.append(latency_ms)

            assert sample is not None

        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)

        print(f"\nStream latency: avg={avg_latency:.1f}ms, max={max_latency:.1f}ms")

        assert avg_latency < 50, f"Average latency {avg_latency:.1f}ms exceeds 50ms"
        assert max_latency < 100, f"Max latency {max_latency:.1f}ms exceeds 100ms"

        await stream.close()

    @pytest.mark.asyncio
    async def test_data_rate(self):
        """Test sustained data rate"""
        import time

        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        bridge = bridges[0]
        stream = MockBridgeStream(bridge, "acoustic/spectrum")
        await stream.connect()

        # Measure data rate over 2 seconds
        samples = []
        t0 = time.time()
        duration = 2.0

        while (time.time() - t0) < duration:
            sample = await stream.read()
            if sample:
                samples.append(sample)

        elapsed = time.time() - t0
        sample_rate = len(samples) / elapsed

        # Calculate bytes per second
        bytes_per_sample = len(samples[0].frequencies) * 4  # f32 = 4 bytes
        bytes_per_sec = sample_rate * bytes_per_sample
        mbps = (bytes_per_sec * 8) / 1e6

        print(f"\nData rate: {sample_rate:.1f} samples/sec, {mbps:.2f} Mbps")

        # For mock, we expect ~50 samples/sec (20ms per sample)
        assert sample_rate > 10, f"Sample rate {sample_rate:.1f}/s is too low"

        await stream.close()


class TestCorrelation:
    """Test correlation functionality"""

    @pytest.mark.asyncio
    async def test_acoustic_vibration_correlation(self):
        """Test acoustic-vibration correlation"""
        discovery = MockBridgeDiscovery()
        bridges = await discovery.discover_bridges()

        # Get acoustic and vibration bridges
        acoustic_bridge = next((b for b in bridges if "acoustic" in b.bridge_id), None)
        vibration_bridge = next((b for b in bridges if "vibration" in b.bridge_id), None)

        assert acoustic_bridge is not None, "Need acoustic bridge"
        assert vibration_bridge is not None, "Need vibration bridge"

        # Create streams
        acoustic_stream = MockBridgeStream(acoustic_bridge, "acoustic/spectrum")
        vibration_stream = MockBridgeStream(vibration_bridge, "vibration/time_series")

        await acoustic_stream.connect()
        await vibration_stream.connect()

        # Read samples
        acoustic_sample = await acoustic_stream.read()
        vibration_sample = await vibration_stream.read()

        assert acoustic_sample is not None
        assert vibration_sample is not None

        # Check time synchronization
        time_diff_ms = abs(acoustic_sample.timestamp_ns - vibration_sample.timestamp_ns) / 1e6
        assert time_diff_ms < 50, f"Time sync {time_diff_ms:.2f}ms exceeds 50ms"

        await acoustic_stream.close()
        await vibration_stream.close()


class TestEndToEnd:
    """End-to-end integration tests"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow: discover → subscribe → receive"""
        # 1. Start MCP server
        server = InfinityBridgeMCPServer(mock=True)
        await server.start()

        # 2. Discover bridges
        bridges = server.discovery.list_bridges()
        assert len(bridges) >= 1, "Should discover bridges"
        print(f"\n✓ Discovered {len(bridges)} bridges")

        # 3. Subscribe to stream
        async def mock_subscribe(bridge_id: str, stream_type: str):
            bridge = server.discovery.get_bridge(bridge_id)
            if bridge:
                stream = MockBridgeStream(bridge, stream_type)
                await stream.connect()
                return stream
            return None

        server.subscribe_to_stream = mock_subscribe

        bridge = bridges[0]
        stream = await server.subscribe_to_stream(bridge.bridge_id, "acoustic/spectrum")
        assert stream is not None, "Should subscribe successfully"
        print(f"✓ Subscribed to {bridge.bridge_id}")

        # 4. Receive correlated data
        samples = await stream.read_n(10)
        assert len(samples) == 10, "Should receive 10 samples"
        print(f"✓ Received {len(samples)} samples")

        # Verify data quality
        for sample in samples:
            assert sample.timestamp_ns > 0
            assert len(sample.frequencies) > 0
            assert sample.sample_rate_hz > 0

        await stream.close()
        await server.stop()

        print("✓ End-to-end workflow complete")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
