#!/usr/bin/env python3
"""
Infinity Bridge CLI
Command-line interface for bridge operations: discovery, subscription, and streaming
"""
import asyncio
import sys
import os
import argparse
import json
from typing import Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from mcp_server import InfinityBridgeMCPServer, BridgeStream, MockBridgeStream
from discovery import BridgeDiscovery, MockBridgeDiscovery, BridgeInfo
from holochain_connector import HolochainConnector, MockHolochainConnector, BridgeRegistration


class InfinityBridgeCLI:
    """CLI for Infinity Bridge operations"""

    def __init__(self, conductor_url: str = "ws://localhost:8888", mock: bool = False):
        """
        Initialize CLI

        Args:
            conductor_url: Holochain conductor URL
            mock: Use mock implementations for testing
        """
        self.conductor_url = conductor_url
        self.mock = mock
        self.server: Optional[InfinityBridgeMCPServer] = None
        self.connector: Optional[HolochainConnector] = None

    async def initialize(self):
        """Initialize server and connector"""
        if not self.server:
            self.server = InfinityBridgeMCPServer(
                conductor_url=self.conductor_url,
                mock=self.mock
            )
            await self.server.start()

        if not self.connector:
            if self.mock:
                self.connector = MockHolochainConnector(conductor_url=self.conductor_url)
            else:
                self.connector = HolochainConnector(conductor_url=self.conductor_url)
            await self.connector.connect()

    async def cleanup(self):
        """Cleanup resources"""
        if self.server:
            await self.server.stop()
        if self.connector:
            await self.connector.disconnect()

    async def cmd_discover(self, args):
        """Discover all bridges"""
        await self.initialize()

        print("\n🔍 Discovering bridges...\n")
        bridges = self.server.discovery.list_bridges()

        if not bridges:
            print("No bridges found.")
            return

        print(f"Found {len(bridges)} bridge(s):\n")

        for i, bridge in enumerate(bridges, 1):
            print(f"{i}. {bridge.bridge_id}")
            print(f"   Capabilities: {', '.join(bridge.capabilities)}")
            print(f"   Transport: {', '.join(bridge.transport)}")
            print(f"   Endpoint: {bridge.endpoint}")
            print(f"   Timestamp: {bridge.timestamp}")
            print()

        if args.json:
            output = [
                {
                    "bridge_id": b.bridge_id,
                    "capabilities": b.capabilities,
                    "transport": b.transport,
                    "endpoint": b.endpoint,
                    "timestamp": b.timestamp.isoformat(),
                }
                for b in bridges
            ]
            print(json.dumps(output, indent=2))

    async def cmd_search(self, args):
        """Search bridges by capability"""
        await self.initialize()

        capability = args.capability
        print(f"\n🔍 Searching for bridges with capability: {capability}\n")

        bridges = await self.server.discovery.discover_by_capability(capability)

        if not bridges:
            print(f"No bridges found with capability '{capability}'.")
            return

        print(f"Found {len(bridges)} bridge(s):\n")

        for i, bridge in enumerate(bridges, 1):
            print(f"{i}. {bridge.bridge_id}")
            print(f"   Endpoint: {bridge.endpoint}")
            print()

        if args.json:
            output = [
                {
                    "bridge_id": b.bridge_id,
                    "capabilities": b.capabilities,
                    "endpoint": b.endpoint,
                }
                for b in bridges
            ]
            print(json.dumps(output, indent=2))

    async def cmd_resources(self, args):
        """List MCP resources"""
        await self.initialize()

        print("\n📋 Available MCP Resources:\n")
        resources = await self.server.list_resources()

        if not resources:
            print("No resources available.")
            return

        for i, resource in enumerate(resources, 1):
            print(f"{i}. {resource['uri']}")
            print(f"   Name: {resource['name']}")
            print(f"   Description: {resource['description']}")
            print(f"   Type: {resource['mime_type']}")
            print()

        if args.json:
            print(json.dumps(resources, indent=2))

    async def cmd_subscribe(self, args):
        """Subscribe to a bridge stream"""
        await self.initialize()

        bridge_id = args.bridge_id
        stream_type = args.stream_type

        print(f"\n📡 Subscribing to {bridge_id}/{stream_type}...\n")

        # Mock stream for testing
        if self.mock:
            async def mock_subscribe(bid: str, stype: str):
                bridge = self.server.discovery.get_bridge(bid)
                if bridge:
                    stream = MockBridgeStream(bridge, stype)
                    await stream.connect()
                    return stream
                return None

            self.server.subscribe_to_stream = mock_subscribe

        stream = await self.server.subscribe_to_stream(bridge_id, stream_type)

        if not stream:
            print(f"✗ Failed to subscribe to {bridge_id}/{stream_type}")
            return

        print(f"✓ Connected to {stream.bridge.bridge_id}")
        print(f"\nReading {args.samples} sample(s)...\n")

        samples = await stream.read_n(args.samples)

        print(f"✓ Received {len(samples)} sample(s)\n")

        for i, sample in enumerate(samples, 1):
            peak_amplitude = max(sample.frequencies) if sample.frequencies else 0
            peak_idx = sample.frequencies.index(peak_amplitude) if sample.frequencies and peak_amplitude > 0 else 0
            freq_hz = peak_idx * (sample.sample_rate_hz / 2) / len(sample.frequencies) if sample.frequencies else 0

            print(f"Sample {i}:")
            print(f"  Timestamp: {sample.timestamp_ns} ns")
            print(f"  Sample Rate: {sample.sample_rate_hz} Hz")
            print(f"  Bins: {len(sample.frequencies)}")
            print(f"  Peak Frequency: {freq_hz:.1f} Hz")
            print(f"  Peak Amplitude: {peak_amplitude:.2f}")
            print()

        if args.json:
            output = [
                {
                    "bridge_id": s.bridge_id,
                    "stream_type": s.stream_type,
                    "timestamp_ns": s.timestamp_ns,
                    "sample_rate_hz": s.sample_rate_hz,
                    "frequencies": s.frequencies[:10] if not args.full else s.frequencies,  # Truncate for readability
                }
                for s in samples
            ]
            print(json.dumps(output, indent=2))

        await stream.close()

    async def cmd_register(self, args):
        """Register a bridge in DHT"""
        await self.initialize()

        print(f"\n📝 Registering bridge: {args.bridge_id}...\n")

        registration = BridgeRegistration(
            bridge_id=args.bridge_id,
            capabilities=args.capabilities.split(","),
            transport=args.transport.split(","),
            endpoint=args.endpoint,
            signature=bytes.fromhex(args.signature) if args.signature else b"\x00" * 64,
            timestamp=datetime.now()
        )

        success = await self.connector.register_bridge(registration)

        if success:
            print(f"✓ Bridge registered successfully")
            print(f"  ID: {registration.bridge_id}")
            print(f"  Capabilities: {', '.join(registration.capabilities)}")
            print(f"  Endpoint: {registration.endpoint}")
        else:
            print(f"✗ Failed to register bridge")

    async def cmd_streams(self, args):
        """Get streams for a bridge"""
        await self.initialize()

        bridge_id = args.bridge_id
        print(f"\n📋 Getting streams for {bridge_id}...\n")

        streams = await self.connector.get_bridge_streams(bridge_id)

        if not streams:
            print(f"No streams found for bridge '{bridge_id}'.")
            return

        print(f"Found {len(streams)} stream(s):\n")

        for i, stream in enumerate(streams, 1):
            print(f"{i}. {stream.get('stream_type', 'unknown')}")
            metadata = stream.get('metadata', {})
            for key, value in metadata.items():
                print(f"   {key}: {value}")
            print()

        if args.json:
            print(json.dumps(streams, indent=2))

    async def cmd_ping(self, args):
        """Ping Holochain conductor"""
        await self.initialize()

        print("\n🏓 Pinging conductor...\n")

        success = await self.connector.ping()

        if success:
            print("✓ Conductor responding")
        else:
            print("✗ Conductor not responding")

    async def cmd_info(self, args):
        """Show bridge information"""
        await self.initialize()

        bridge_id = args.bridge_id
        print(f"\n📊 Bridge Information: {bridge_id}\n")

        bridge = self.server.discovery.get_bridge(bridge_id)

        if not bridge:
            print(f"Bridge '{bridge_id}' not found.")
            return

        print(f"ID: {bridge.bridge_id}")
        print(f"Capabilities: {', '.join(bridge.capabilities)}")
        print(f"Transport: {', '.join(bridge.transport)}")
        print(f"Endpoint: {bridge.endpoint}")
        print(f"Timestamp: {bridge.timestamp}")

        if bridge.holochain_hash:
            print(f"DHT Hash: {bridge.holochain_hash}")

        # Get streams
        streams = await self.connector.get_bridge_streams(bridge_id)
        if streams:
            print(f"\nStreams ({len(streams)}):")
            for stream in streams:
                print(f"  - {stream.get('stream_type', 'unknown')}")

        if args.json:
            output = {
                "bridge_id": bridge.bridge_id,
                "capabilities": bridge.capabilities,
                "transport": bridge.transport,
                "endpoint": bridge.endpoint,
                "timestamp": bridge.timestamp.isoformat(),
                "streams": streams,
            }
            print(json.dumps(output, indent=2))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Infinity Bridge CLI - Discover and interact with bridges",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s discover                            # Discover all bridges
  %(prog)s search acoustic_20hz_20khz          # Search by capability
  %(prog)s subscribe acoustic-esp32-001 acoustic/spectrum --samples 10
  %(prog)s resources                           # List MCP resources
  %(prog)s register my-bridge "acoustic_20hz_20khz,fft_1024" tcp tcp://192.168.1.100:9999
  %(prog)s info acoustic-esp32-001             # Show bridge info
  %(prog)s ping                                # Ping conductor

Configuration:
  Use --conductor to specify Holochain conductor URL (default: ws://localhost:8888)
  Use --mock for testing without real Holochain conductor
        """
    )

    parser.add_argument(
        "--conductor",
        default="ws://localhost:8888",
        help="Holochain conductor URL (default: ws://localhost:8888)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock implementations for testing"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Discover command
    parser_discover = subparsers.add_parser("discover", help="Discover all bridges")
    parser_discover.set_defaults(func=lambda cli, args: cli.cmd_discover(args))

    # Search command
    parser_search = subparsers.add_parser("search", help="Search bridges by capability")
    parser_search.add_argument("capability", help="Capability to search for")
    parser_search.set_defaults(func=lambda cli, args: cli.cmd_search(args))

    # Resources command
    parser_resources = subparsers.add_parser("resources", help="List MCP resources")
    parser_resources.set_defaults(func=lambda cli, args: cli.cmd_resources(args))

    # Subscribe command
    parser_subscribe = subparsers.add_parser("subscribe", help="Subscribe to bridge stream")
    parser_subscribe.add_argument("bridge_id", help="Bridge ID")
    parser_subscribe.add_argument("stream_type", help="Stream type (e.g., acoustic/spectrum)")
    parser_subscribe.add_argument("--samples", type=int, default=10, help="Number of samples to read (default: 10)")
    parser_subscribe.add_argument("--full", action="store_true", help="Include full frequency data in JSON output")
    parser_subscribe.set_defaults(func=lambda cli, args: cli.cmd_subscribe(args))

    # Register command
    parser_register = subparsers.add_parser("register", help="Register a bridge in DHT")
    parser_register.add_argument("bridge_id", help="Bridge ID")
    parser_register.add_argument("capabilities", help="Comma-separated capabilities")
    parser_register.add_argument("transport", help="Comma-separated transports")
    parser_register.add_argument("endpoint", help="Bridge endpoint (e.g., tcp://192.168.1.100:9999)")
    parser_register.add_argument("--signature", help="Signature (hex)", default=None)
    parser_register.set_defaults(func=lambda cli, args: cli.cmd_register(args))

    # Streams command
    parser_streams = subparsers.add_parser("streams", help="Get streams for a bridge")
    parser_streams.add_argument("bridge_id", help="Bridge ID")
    parser_streams.set_defaults(func=lambda cli, args: cli.cmd_streams(args))

    # Ping command
    parser_ping = subparsers.add_parser("ping", help="Ping Holochain conductor")
    parser_ping.set_defaults(func=lambda cli, args: cli.cmd_ping(args))

    # Info command
    parser_info = subparsers.add_parser("info", help="Show bridge information")
    parser_info.add_argument("bridge_id", help="Bridge ID")
    parser_info.set_defaults(func=lambda cli, args: cli.cmd_info(args))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Create CLI instance
    cli = InfinityBridgeCLI(conductor_url=args.conductor, mock=args.mock)

    # Run command
    try:
        asyncio.run(args.func(cli, args))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        if os.getenv("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        asyncio.run(cli.cleanup())


if __name__ == "__main__":
    main()
