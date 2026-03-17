"""
Infinity Bridge Discovery Module
Discovers bridges via Holochain DHT and manages connections
"""
import asyncio
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import websockets


@dataclass
class BridgeInfo:
    """Information about a discovered bridge"""
    bridge_id: str
    capabilities: List[str]
    transport: List[str]
    endpoint: str
    signature: bytes
    timestamp: datetime
    holochain_hash: Optional[str] = None


class BridgeDiscovery:
    """Discovers and manages Infinity Bridges via Holochain DHT"""

    def __init__(self, conductor_url: str = "ws://localhost:8888"):
        """
        Initialize bridge discovery

        Args:
            conductor_url: WebSocket URL of Holochain conductor
        """
        self.conductor_url = conductor_url
        self.discovered_bridges: Dict[str, BridgeInfo] = {}
        self.websocket = None

    async def connect(self) -> bool:
        """Connect to Holochain conductor"""
        try:
            self.websocket = await websockets.connect(self.conductor_url)
            print(f"[BridgeDiscovery] Connected to conductor at {self.conductor_url}")
            return True
        except Exception as e:
            print(f"[BridgeDiscovery] Failed to connect: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Holochain conductor"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def discover_bridges(self, timeout: float = 5.0) -> List[BridgeInfo]:
        """
        Discover all registered bridges from DHT

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered bridges
        """
        if not self.websocket:
            if not await self.connect():
                return []

        try:
            # Call Holochain zome function: discover_bridges
            request = {
                "type": "zome_call",
                "data": {
                    "cell_id": ["infinity_bridge", "registry"],
                    "zome_name": "registry",
                    "fn_name": "discover_bridges",
                    "payload": None,
                    "provenance": "agent_key_placeholder",
                }
            }

            # Send request
            await self.websocket.send(json.dumps(request))

            # Wait for response with timeout
            response_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )

            response = json.loads(response_str)

            # Parse bridge registrations
            bridges = []
            if response.get("type") == "success":
                for reg in response.get("data", []):
                    bridge = BridgeInfo(
                        bridge_id=reg["bridge_id"],
                        capabilities=reg["capabilities"],
                        transport=reg["transport"],
                        endpoint=reg["endpoint"],
                        signature=bytes.fromhex(reg["signature"]) if isinstance(reg["signature"], str) else reg["signature"],
                        timestamp=datetime.fromisoformat(reg.get("timestamp", datetime.now().isoformat())),
                        holochain_hash=reg.get("hash")
                    )
                    bridges.append(bridge)
                    self.discovered_bridges[bridge.bridge_id] = bridge

            print(f"[BridgeDiscovery] Discovered {len(bridges)} bridges")
            return bridges

        except asyncio.TimeoutError:
            print(f"[BridgeDiscovery] Discovery timed out after {timeout}s")
            return []
        except Exception as e:
            print(f"[BridgeDiscovery] Discovery error: {e}")
            return []

    async def discover_by_capability(self, capability: str, timeout: float = 5.0) -> List[BridgeInfo]:
        """
        Discover bridges with specific capability

        Args:
            capability: Capability to search for (e.g., "acoustic_20hz_20khz")
            timeout: Discovery timeout in seconds

        Returns:
            List of matching bridges
        """
        if not self.websocket:
            if not await self.connect():
                return []

        try:
            request = {
                "type": "zome_call",
                "data": {
                    "cell_id": ["infinity_bridge", "registry"],
                    "zome_name": "registry",
                    "fn_name": "discover_by_capability",
                    "payload": capability,
                    "provenance": "agent_key_placeholder",
                }
            }

            await self.websocket.send(json.dumps(request))
            response_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout
            )

            response = json.loads(response_str)

            bridges = []
            if response.get("type") == "success":
                for reg in response.get("data", []):
                    bridge = BridgeInfo(
                        bridge_id=reg["bridge_id"],
                        capabilities=reg["capabilities"],
                        transport=reg["transport"],
                        endpoint=reg["endpoint"],
                        signature=bytes.fromhex(reg["signature"]) if isinstance(reg["signature"], str) else reg["signature"],
                        timestamp=datetime.fromisoformat(reg.get("timestamp", datetime.now().isoformat())),
                        holochain_hash=reg.get("hash")
                    )
                    bridges.append(bridge)
                    self.discovered_bridges[bridge.bridge_id] = bridge

            print(f"[BridgeDiscovery] Found {len(bridges)} bridges with capability '{capability}'")
            return bridges

        except Exception as e:
            print(f"[BridgeDiscovery] Capability search error: {e}")
            return []

    def get_bridge(self, bridge_id: str) -> Optional[BridgeInfo]:
        """Get cached bridge info by ID"""
        return self.discovered_bridges.get(bridge_id)

    def list_bridges(self) -> List[BridgeInfo]:
        """List all cached bridges"""
        return list(self.discovered_bridges.values())

    async def wait_for_bridge(self, bridge_id: str, timeout: float = 30.0, poll_interval: float = 2.0) -> Optional[BridgeInfo]:
        """
        Wait for a specific bridge to appear

        Args:
            bridge_id: Bridge ID to wait for
            timeout: Maximum wait time in seconds
            poll_interval: Time between discovery attempts

        Returns:
            BridgeInfo if found, None if timeout
        """
        start_time = asyncio.get_event_loop().time()

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            bridges = await self.discover_bridges(timeout=poll_interval)

            for bridge in bridges:
                if bridge.bridge_id == bridge_id:
                    print(f"[BridgeDiscovery] Found bridge '{bridge_id}'")
                    return bridge

            await asyncio.sleep(poll_interval)

        print(f"[BridgeDiscovery] Bridge '{bridge_id}' not found after {timeout}s")
        return None


# Mock discovery for testing without Holochain
class MockBridgeDiscovery(BridgeDiscovery):
    """Mock discovery for testing"""

    def __init__(self):
        super().__init__()
        self.mock_bridges = [
            BridgeInfo(
                bridge_id="acoustic-esp32-001",
                capabilities=["acoustic_20hz_20khz", "fft_1024", "correlation_engine"],
                transport=["usb_hid", "tcp"],
                endpoint="tcp://192.168.1.101:9999",
                signature=b"\x00" * 64,
                timestamp=datetime.now()
            ),
            BridgeInfo(
                bridge_id="vibration-rp2040-001",
                capabilities=["vibration_0hz_1khz", "fft_2048"],
                transport=["tcp"],
                endpoint="tcp://192.168.1.102:9999",
                signature=b"\x00" * 64,
                timestamp=datetime.now()
            ),
        ]

    async def connect(self) -> bool:
        """Mock connection always succeeds"""
        return True

    async def discover_bridges(self, timeout: float = 5.0) -> List[BridgeInfo]:
        """Return mock bridges"""
        self.discovered_bridges = {b.bridge_id: b for b in self.mock_bridges}
        return self.mock_bridges

    async def discover_by_capability(self, capability: str, timeout: float = 5.0) -> List[BridgeInfo]:
        """Filter mock bridges by capability"""
        matching = [b for b in self.mock_bridges if capability in b.capabilities]
        return matching


if __name__ == "__main__":
    # Test discovery
    async def test_discovery():
        print("=== Infinity Bridge Discovery Test ===")

        # Use mock discovery for testing
        discovery = MockBridgeDiscovery()

        # Discover all bridges
        bridges = await discovery.discover_bridges()
        print(f"\nDiscovered {len(bridges)} bridges:")
        for bridge in bridges:
            print(f"  - {bridge.bridge_id}")
            print(f"    Capabilities: {', '.join(bridge.capabilities)}")
            print(f"    Endpoint: {bridge.endpoint}")

        # Discover by capability
        acoustic_bridges = await discovery.discover_by_capability("acoustic_20hz_20khz")
        print(f"\nAcoustic bridges: {len(acoustic_bridges)}")
        for bridge in acoustic_bridges:
            print(f"  - {bridge.bridge_id}")

    asyncio.run(test_discovery())
