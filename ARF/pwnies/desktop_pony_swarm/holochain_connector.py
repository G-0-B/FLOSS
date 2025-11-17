"""
Holochain Connector for Infinity Bridge
Provides real DHT connection for bridge registry operations
"""
import asyncio
import json
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import websockets


@dataclass
class BridgeRegistration:
    """Bridge registration data for DHT"""
    bridge_id: str
    capabilities: List[str]
    transport: List[str]
    endpoint: str
    signature: bytes
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "bridge_id": self.bridge_id,
            "capabilities": self.capabilities,
            "transport": self.transport,
            "endpoint": self.endpoint,
            "signature": self.signature.hex() if isinstance(self.signature, bytes) else self.signature,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BridgeRegistration":
        """Create from dictionary"""
        return cls(
            bridge_id=data["bridge_id"],
            capabilities=data["capabilities"],
            transport=data["transport"],
            endpoint=data["endpoint"],
            signature=bytes.fromhex(data["signature"]) if isinstance(data["signature"], str) else data["signature"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"],
        )


class HolochainConnector:
    """
    Connector for Holochain DHT operations
    Handles bridge registration and discovery via infinity_bridge DNA
    """

    def __init__(
        self,
        conductor_url: str = "ws://localhost:8888",
        app_port: int = 8888,
        cell_id: Optional[List[str]] = None,
        timeout: float = 10.0
    ):
        """
        Initialize Holochain connector

        Args:
            conductor_url: WebSocket URL of Holochain conductor
            app_port: App interface port (default: 8888)
            cell_id: [dna_hash, agent_pub_key] (auto-detected if None)
            timeout: Default timeout for operations in seconds
        """
        self.conductor_url = conductor_url
        self.app_port = app_port
        self.cell_id = cell_id or ["infinity_bridge", "agent_placeholder"]
        self.timeout = timeout
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.request_counter = 0

    async def connect(self) -> bool:
        """
        Connect to Holochain conductor

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.websocket = await asyncio.wait_for(
                websockets.connect(self.conductor_url),
                timeout=self.timeout
            )
            self.connected = True
            print(f"[HolochainConnector] Connected to {self.conductor_url}")
            return True
        except asyncio.TimeoutError:
            print(f"[HolochainConnector] Connection timeout to {self.conductor_url}")
            return False
        except Exception as e:
            print(f"[HolochainConnector] Connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Holochain conductor"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            self.connected = False
            print("[HolochainConnector] Disconnected")

    async def call_zome(
        self,
        zome_name: str,
        fn_name: str,
        payload: Any = None,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Call a zome function

        Args:
            zome_name: Name of the zome (e.g., "registry")
            fn_name: Name of the function (e.g., "register_bridge")
            payload: Function payload (will be JSON serialized)
            timeout: Timeout for this call (uses default if None)

        Returns:
            Response data or None if error
        """
        if not self.connected:
            if not await self.connect():
                return None

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        self.request_counter += 1

        # Construct zome call request
        request = {
            "id": request_id,
            "type": "app_request",
            "data": {
                "type": "call_zome",
                "data": {
                    "cell_id": self.cell_id,
                    "zome_name": zome_name,
                    "fn_name": fn_name,
                    "payload": payload,
                    "cap_secret": None,
                    "provenance": self.cell_id[1],  # agent_pub_key
                }
            }
        }

        try:
            # Send request
            await self.websocket.send(json.dumps(request))

            # Wait for response
            timeout_val = timeout or self.timeout
            response_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=timeout_val
            )

            response = json.loads(response_str)

            # Check for errors
            if response.get("type") == "error":
                error_msg = response.get("data", {}).get("message", "Unknown error")
                print(f"[HolochainConnector] Zome call error: {error_msg}")
                return None

            # Extract data
            if response.get("type") == "app_response":
                return response.get("data")

            return response

        except asyncio.TimeoutError:
            print(f"[HolochainConnector] Zome call timeout ({zome_name}.{fn_name})")
            return None
        except Exception as e:
            print(f"[HolochainConnector] Zome call failed: {e}")
            return None

    async def register_bridge(self, registration: BridgeRegistration) -> bool:
        """
        Register a bridge in the DHT

        Args:
            registration: Bridge registration data

        Returns:
            True if registration successful, False otherwise
        """
        payload = registration.to_dict()

        result = await self.call_zome(
            zome_name="registry",
            fn_name="register_bridge",
            payload=payload
        )

        if result:
            print(f"[HolochainConnector] Bridge registered: {registration.bridge_id}")
            return True
        else:
            print(f"[HolochainConnector] Failed to register bridge: {registration.bridge_id}")
            return False

    async def discover_bridges(self, timeout: Optional[float] = None) -> List[BridgeRegistration]:
        """
        Discover all registered bridges from DHT

        Args:
            timeout: Discovery timeout (uses default if None)

        Returns:
            List of bridge registrations
        """
        result = await self.call_zome(
            zome_name="registry",
            fn_name="discover_bridges",
            payload=None,
            timeout=timeout
        )

        if not result:
            return []

        # Parse response
        bridges = []
        bridge_list = result.get("data", result) if isinstance(result, dict) else result

        if not isinstance(bridge_list, list):
            # Handle case where result is wrapped
            if isinstance(bridge_list, dict) and "bridges" in bridge_list:
                bridge_list = bridge_list["bridges"]
            else:
                print(f"[HolochainConnector] Unexpected response format: {type(bridge_list)}")
                return []

        for bridge_data in bridge_list:
            try:
                # Extract registration data from DHT entry
                if isinstance(bridge_data, dict):
                    # Handle both direct entries and wrapped entries
                    entry_data = bridge_data.get("entry", bridge_data)
                    bridge = BridgeRegistration.from_dict(entry_data)
                    bridges.append(bridge)
            except Exception as e:
                print(f"[HolochainConnector] Failed to parse bridge entry: {e}")
                continue

        print(f"[HolochainConnector] Discovered {len(bridges)} bridges")
        return bridges

    async def discover_by_capability(
        self,
        capability: str,
        timeout: Optional[float] = None
    ) -> List[BridgeRegistration]:
        """
        Discover bridges with specific capability

        Args:
            capability: Capability to search for (e.g., "acoustic_20hz_20khz")
            timeout: Search timeout (uses default if None)

        Returns:
            List of matching bridge registrations
        """
        result = await self.call_zome(
            zome_name="registry",
            fn_name="discover_by_capability",
            payload=capability,
            timeout=timeout
        )

        if not result:
            return []

        # Parse response
        bridges = []
        bridge_list = result.get("data", result) if isinstance(result, dict) else result

        if not isinstance(bridge_list, list):
            if isinstance(bridge_list, dict) and "bridges" in bridge_list:
                bridge_list = bridge_list["bridges"]
            else:
                print(f"[HolochainConnector] Unexpected response format: {type(bridge_list)}")
                return []

        for bridge_data in bridge_list:
            try:
                entry_data = bridge_data.get("entry", bridge_data)
                bridge = BridgeRegistration.from_dict(entry_data)
                bridges.append(bridge)
            except Exception as e:
                print(f"[HolochainConnector] Failed to parse bridge entry: {e}")
                continue

        print(f"[HolochainConnector] Found {len(bridges)} bridges with capability '{capability}'")
        return bridges

    async def register_stream(
        self,
        bridge_id: str,
        stream_type: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Register a data stream for a bridge

        Args:
            bridge_id: Bridge ID
            stream_type: Type of stream (e.g., "acoustic/spectrum")
            metadata: Stream metadata

        Returns:
            True if registration successful, False otherwise
        """
        payload = {
            "bridge_id": bridge_id,
            "stream_type": stream_type,
            "metadata": metadata,
        }

        result = await self.call_zome(
            zome_name="registry",
            fn_name="register_stream",
            payload=payload
        )

        if result:
            print(f"[HolochainConnector] Stream registered: {bridge_id}/{stream_type}")
            return True
        else:
            print(f"[HolochainConnector] Failed to register stream: {bridge_id}/{stream_type}")
            return False

    async def get_bridge_streams(self, bridge_id: str) -> List[Dict[str, Any]]:
        """
        Get all streams for a bridge

        Args:
            bridge_id: Bridge ID

        Returns:
            List of stream metadata
        """
        result = await self.call_zome(
            zome_name="registry",
            fn_name="get_bridge_streams",
            payload=bridge_id
        )

        if not result:
            return []

        stream_list = result.get("data", result) if isinstance(result, dict) else result

        if isinstance(stream_list, list):
            print(f"[HolochainConnector] Found {len(stream_list)} streams for {bridge_id}")
            return stream_list
        else:
            return []

    async def ping(self) -> bool:
        """
        Ping the conductor to check connection

        Returns:
            True if ping successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            # Simple echo test
            test_msg = {"type": "ping", "id": str(uuid.uuid4())}
            await self.websocket.send(json.dumps(test_msg))

            response_str = await asyncio.wait_for(
                self.websocket.recv(),
                timeout=2.0
            )
            return True
        except:
            return False

    def __repr__(self) -> str:
        status = "connected" if self.connected else "disconnected"
        return f"HolochainConnector({self.conductor_url}, {status})"


# Mock connector for testing without Holochain
class MockHolochainConnector(HolochainConnector):
    """Mock connector for testing without real Holochain conductor"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mock_bridges: Dict[str, BridgeRegistration] = {}
        self.mock_streams: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(self) -> bool:
        """Mock connection always succeeds"""
        self.connected = True
        print("[MockHolochainConnector] Mock connection established")
        return True

    async def disconnect(self):
        """Mock disconnect"""
        self.connected = False

    async def register_bridge(self, registration: BridgeRegistration) -> bool:
        """Mock bridge registration"""
        self.mock_bridges[registration.bridge_id] = registration
        print(f"[MockHolochainConnector] Mock registered: {registration.bridge_id}")
        return True

    async def discover_bridges(self, timeout: Optional[float] = None) -> List[BridgeRegistration]:
        """Return mock bridges"""
        return list(self.mock_bridges.values())

    async def discover_by_capability(
        self,
        capability: str,
        timeout: Optional[float] = None
    ) -> List[BridgeRegistration]:
        """Filter mock bridges by capability"""
        return [
            bridge for bridge in self.mock_bridges.values()
            if capability in bridge.capabilities
        ]

    async def register_stream(
        self,
        bridge_id: str,
        stream_type: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Mock stream registration"""
        if bridge_id not in self.mock_streams:
            self.mock_streams[bridge_id] = []

        self.mock_streams[bridge_id].append({
            "stream_type": stream_type,
            "metadata": metadata,
        })
        return True

    async def get_bridge_streams(self, bridge_id: str) -> List[Dict[str, Any]]:
        """Get mock streams"""
        return self.mock_streams.get(bridge_id, [])

    async def ping(self) -> bool:
        """Mock ping always succeeds"""
        return self.connected


if __name__ == "__main__":
    # Test Holochain connector
    async def test_connector():
        print("=== Holochain Connector Test ===\n")

        # Use mock connector for testing
        connector = MockHolochainConnector()

        # Connect
        print("1. Connecting to Holochain...")
        if await connector.connect():
            print("✓ Connected\n")
        else:
            print("✗ Connection failed\n")
            return

        # Register a bridge
        print("2. Registering bridge...")
        registration = BridgeRegistration(
            bridge_id="test-esp32-001",
            capabilities=["acoustic_20hz_20khz", "fft_1024"],
            transport=["tcp"],
            endpoint="tcp://192.168.1.100:9999",
            signature=b"\x00" * 64,
            timestamp=datetime.now()
        )

        if await connector.register_bridge(registration):
            print("✓ Bridge registered\n")
        else:
            print("✗ Registration failed\n")

        # Discover bridges
        print("3. Discovering bridges...")
        bridges = await connector.discover_bridges()
        print(f"✓ Found {len(bridges)} bridges\n")

        for bridge in bridges:
            print(f"  Bridge: {bridge.bridge_id}")
            print(f"    Capabilities: {', '.join(bridge.capabilities)}")
            print(f"    Endpoint: {bridge.endpoint}\n")

        # Discover by capability
        print("4. Searching for acoustic capability...")
        acoustic = await connector.discover_by_capability("acoustic_20hz_20khz")
        print(f"✓ Found {len(acoustic)} acoustic bridges\n")

        # Register stream
        print("5. Registering stream...")
        if await connector.register_stream(
            "test-esp32-001",
            "acoustic/spectrum",
            {"sample_rate": 44100, "fft_size": 1024}
        ):
            print("✓ Stream registered\n")

        # Get streams
        print("6. Getting bridge streams...")
        streams = await connector.get_bridge_streams("test-esp32-001")
        print(f"✓ Found {len(streams)} streams\n")

        # Ping
        print("7. Pinging conductor...")
        if await connector.ping():
            print("✓ Ping successful\n")

        # Disconnect
        print("8. Disconnecting...")
        await connector.disconnect()
        print("✓ Disconnected\n")

        print("=== Test Complete ===")

    asyncio.run(test_connector())
