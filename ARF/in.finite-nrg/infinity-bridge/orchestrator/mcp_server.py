"""
Infinity Bridge MCP Server
Exposes bridges as MCP resources for AI agents
"""
import asyncio
import json
import struct
from typing import List, Dict, Optional, AsyncIterator
from dataclasses import dataclass
import socket
from discovery import BridgeDiscovery, BridgeInfo, MockBridgeDiscovery


@dataclass
class StreamSample:
    """A single sample from a bridge stream"""
    bridge_id: str
    stream_type: str
    timestamp_ns: int
    sample_rate_hz: int
    frequencies: List[float]
    raw_data: Optional[bytes] = None


class BridgeStream:
    """Manages a subscription to a bridge data stream"""

    def __init__(self, bridge: BridgeInfo, stream_type: str):
        """
        Initialize bridge stream

        Args:
            bridge: Bridge information
            stream_type: Type of stream (e.g., "acoustic/spectrum")
        """
        self.bridge = bridge
        self.stream_type = stream_type
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.sample_buffer = []

    async def connect(self) -> bool:
        """Connect to bridge stream"""
        try:
            # Parse endpoint (e.g., "tcp://192.168.1.101:9999")
            if self.bridge.endpoint.startswith("tcp://"):
                endpoint = self.bridge.endpoint[6:]  # Remove "tcp://"
                host, port = endpoint.rsplit(":", 1)
                port = int(port)

                # Create TCP socket
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(5.0)

                # Connect
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.socket.connect,
                    (host, port)
                )

                # Send subscription request
                request = {
                    "type": "subscribe",
                    "stream": self.stream_type
                }
                self.socket.send(json.dumps(request).encode() + b"\n")

                self.connected = True
                print(f"[BridgeStream] Connected to {self.bridge.bridge_id}/{self.stream_type}")
                return True

        except Exception as e:
            print(f"[BridgeStream] Connection failed: {e}")
            self.connected = False
            return False

    async def read(self) -> Optional[StreamSample]:
        """
        Read next sample from stream

        Returns:
            StreamSample or None if connection closed
        """
        if not self.connected:
            return None

        try:
            # Read packet header (simplified protocol)
            # Format: [timestamp:8][sample_rate:4][data_len:4][data:N]
            header = await self._recv_exact(16)
            if header is None:
                return None

            timestamp_ns = struct.unpack("<Q", header[0:8])[0]
            sample_rate_hz = struct.unpack("<I", header[8:12])[0]
            data_len = struct.unpack("<I", header[12:16])[0]

            # Read data payload
            data = await self._recv_exact(data_len)
            if data is None:
                return None

            # Parse frequency spectrum (array of f32)
            num_freqs = data_len // 4
            frequencies = []
            for i in range(num_freqs):
                freq = struct.unpack("<f", data[i*4:(i+1)*4])[0]
                frequencies.append(freq)

            sample = StreamSample(
                bridge_id=self.bridge.bridge_id,
                stream_type=self.stream_type,
                timestamp_ns=timestamp_ns,
                sample_rate_hz=sample_rate_hz,
                frequencies=frequencies,
                raw_data=data
            )

            return sample

        except Exception as e:
            print(f"[BridgeStream] Read error: {e}")
            return None

    async def _recv_exact(self, num_bytes: int) -> Optional[bytes]:
        """Receive exactly `num_bytes` bytes from the socket.

        Returns None if the connection is closed before the requested
        bytes are received.
        """
        if not self.socket:
            return None

        loop = asyncio.get_event_loop()
        chunks = bytearray()

        while len(chunks) < num_bytes:
            remaining = num_bytes - len(chunks)
            try:
                chunk = await loop.run_in_executor(None, self.socket.recv, remaining)
            except Exception as e:
                print(f"[BridgeStream] Socket recv error: {e}")
                return None

            if not chunk:
                # Connection closed
                return None

            chunks.extend(chunk)

        return bytes(chunks)

    async def read_n(self, n: int, timeout: float = 10.0) -> List[StreamSample]:
        """
        Read N samples from stream

        Args:
            n: Number of samples to read
            timeout: Total timeout in seconds

        Returns:
            List of samples (may be less than n if timeout)
        """
        samples = []
        start_time = asyncio.get_event_loop().time()

        while len(samples) < n:
            if (asyncio.get_event_loop().time() - start_time) > timeout:
                print(f"[BridgeStream] Timeout reading samples ({len(samples)}/{n})")
                break

            sample = await self.read()
            if sample:
                samples.append(sample)
            else:
                await asyncio.sleep(0.01)

        return samples

    async def stream(self) -> AsyncIterator[StreamSample]:
        """
        Stream samples continuously

        Yields:
            StreamSample objects
        """
        while self.connected:
            sample = await self.read()
            if sample:
                yield sample
            else:
                break

    async def close(self):
        """Close stream connection"""
        if self.socket:
            self.socket.close()
            self.socket = None
        self.connected = False


class InfinityBridgeMCPServer:
    """
    MCP server for Infinity Bridge orchestration
    Exposes bridges as MCP resources
    """

    def __init__(self, conductor_url: str = "ws://localhost:8888", mock: bool = False):
        """
        Initialize MCP server

        Args:
            conductor_url: Holochain conductor URL
            mock: Use mock discovery for testing
        """
        if mock:
            self.discovery = MockBridgeDiscovery()
        else:
            self.discovery = BridgeDiscovery(conductor_url)

        self.active_streams: Dict[str, BridgeStream] = {}

    async def start(self):
        """Start MCP server"""
        print("[MCPServer] Starting Infinity Bridge MCP Server...")

        # Connect to Holochain
        if not await self.discovery.connect():
            print("[MCPServer] Warning: Could not connect to Holochain")

        # Discover bridges
        bridges = await self.discovery.discover_bridges()
        print(f"[MCPServer] Discovered {len(bridges)} bridges")

        # Register MCP resources
        for bridge in bridges:
            await self.register_bridge_resources(bridge)

    async def register_bridge_resources(self, bridge: BridgeInfo):
        """Register MCP resources for a bridge"""
        # Create resource URIs like: bridge://acoustic-esp32-001/acoustic/spectrum
        for capability in bridge.capabilities:
            resource_uri = f"bridge://{bridge.bridge_id}/{capability}"
            print(f"[MCPServer] Registered resource: {resource_uri}")

    async def subscribe_to_stream(self, bridge_id: str, stream_type: str) -> Optional[BridgeStream]:
        """
        Subscribe to a bridge stream

        Args:
            bridge_id: Bridge ID to subscribe to
            stream_type: Type of stream (e.g., "acoustic/spectrum")

        Returns:
            BridgeStream or None if failed
        """
        # Get bridge info
        bridge = self.discovery.get_bridge(bridge_id)
        if not bridge:
            print(f"[MCPServer] Bridge '{bridge_id}' not found")
            return None

        # Create stream
        stream_key = f"{bridge_id}/{stream_type}"
        if stream_key in self.active_streams:
            return self.active_streams[stream_key]

        stream = BridgeStream(bridge, stream_type)
        if await stream.connect():
            self.active_streams[stream_key] = stream
            return stream

        return None

    async def list_resources(self) -> List[Dict]:
        """List all available MCP resources"""
        resources = []

        for bridge in self.discovery.list_bridges():
            for capability in bridge.capabilities:
                resources.append({
                    "uri": f"bridge://{bridge.bridge_id}/{capability}",
                    "name": f"{bridge.bridge_id} - {capability}",
                    "description": f"Data stream from {bridge.bridge_id}",
                    "mime_type": "application/octet-stream"
                })

        return resources

    async def read_resource(self, uri: str, num_samples: int = 10) -> List[StreamSample]:
        """
        Read from an MCP resource

        Args:
            uri: Resource URI (e.g., "bridge://acoustic-esp32-001/acoustic/spectrum")
            num_samples: Number of samples to read

        Returns:
            List of samples
        """
        # Parse URI
        if not uri.startswith("bridge://"):
            return []

        parts = uri[9:].split("/", 1)
        if len(parts) != 2:
            return []

        bridge_id, stream_type = parts

        # Subscribe to stream
        stream = await self.subscribe_to_stream(bridge_id, stream_type)
        if not stream:
            return []

        # Read samples
        samples = await stream.read_n(num_samples)
        return samples

    async def stop(self):
        """Stop MCP server and close all streams"""
        print("[MCPServer] Stopping server...")

        # Close all active streams
        for stream in self.active_streams.values():
            await stream.close()

        self.active_streams.clear()

        # Disconnect from Holochain
        await self.discovery.disconnect()


# Mock stream for testing
class MockBridgeStream(BridgeStream):
    """Mock stream that generates synthetic data"""

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def read(self) -> Optional[StreamSample]:
        """Generate mock FFT spectrum"""
        import random
        import time

        # Generate synthetic spectrum with peak at 1kHz
        frequencies = []
        for i in range(512):  # 512 frequency bins
            # Add noise
            value = random.uniform(0.01, 0.1)

            # Add peak at bin ~23 (1kHz for 44.1kHz sample rate)
            if 20 <= i <= 26:
                value += random.uniform(5.0, 10.0)

            frequencies.append(value)

        sample = StreamSample(
            bridge_id=self.bridge.bridge_id,
            stream_type=self.stream_type,
            timestamp_ns=int(time.time() * 1e9),
            sample_rate_hz=44100,
            frequencies=frequencies
        )

        await asyncio.sleep(0.02)  # Simulate 50Hz update rate
        return sample


if __name__ == "__main__":
    # Test MCP server
    async def test_mcp_server():
        print("=== Infinity Bridge MCP Server Test ===")

        # Create server with mock discovery
        server = InfinityBridgeMCPServer(mock=True)

        # Start server
        await server.start()

        # List resources
        print("\nAvailable resources:")
        resources = await server.list_resources()
        for resource in resources:
            print(f"  - {resource['uri']}")

        # Read from a resource (using mock stream)
        print("\nReading from acoustic bridge...")
        uri = "bridge://acoustic-esp32-001/acoustic/spectrum"

        # Monkey-patch to use mock stream
        async def mock_subscribe(bridge_id: str, stream_type: str):
            bridge = server.discovery.get_bridge(bridge_id)
            if bridge:
                stream = MockBridgeStream(bridge, stream_type)
                await stream.connect()
                return stream
            return None

        server.subscribe_to_stream = mock_subscribe

        samples = await server.read_resource(uri, num_samples=5)
        print(f"Received {len(samples)} samples")
        for i, sample in enumerate(samples):
            peak_freq = max(sample.frequencies)
            peak_idx = sample.frequencies.index(peak_freq)
            freq_hz = peak_idx * (sample.sample_rate_hz / 2) / len(sample.frequencies)
            print(f"  Sample {i}: Peak at {freq_hz:.0f} Hz ({peak_freq:.2f})")

        # Stop server
        await server.stop()

    asyncio.run(test_mcp_server())
