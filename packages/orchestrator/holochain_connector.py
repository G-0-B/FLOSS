"""
Holochain Conductor Connector for FLOSSIOULLK Rose Forest.

Provides a Python interface to the Holochain conductor WebSocket API,
enabling ConversationMemory to persist Understandings as RoseNodes
and retrieve them via vector search.

Protocol: The Holochain conductor uses msgpack-encoded messages over WebSocket.
Each request is a msgpack array: [request_id, request_body]
Each response is a msgpack array: [response_type, response_body]

Requires: websockets, msgpack
"""

import asyncio
import struct
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

try:
    import msgpack
except ImportError:
    msgpack = None  # type: ignore

try:
    import websockets
    from websockets.legacy.client import WebSocketClientProtocol
except ImportError:
    websockets = None  # type: ignore

logger = logging.getLogger("holochain_connector")


@dataclass
class RoseNodeInput:
    """Input for add_knowledge zome call."""
    content: str
    embedding: list[float]
    license: str = "MIT"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class SearchInput:
    """Input for vector_search zome call."""
    query_embedding: list[float]
    k: int = 5


@dataclass
class SearchResult:
    """Result from vector_search zome call."""
    hash: bytes
    score: float
    content: str


class HolochainError(Exception):
    """Error from Holochain conductor."""
    pass


class HolochainConnector:
    """
    Async connector to a running Holochain conductor.

    Usage:
        connector = HolochainConnector(app_ws_url="ws://localhost:PORT")
        await connector.connect(installed_app_id="rose_forest")
        hash = await connector.add_knowledge(RoseNodeInput(...))
        results = await connector.vector_search(SearchInput(...))
        await connector.close()
    """

    def __init__(self, app_ws_url: str = "ws://localhost:8888"):
        if msgpack is None:
            raise ImportError("msgpack is required: pip install msgpack")
        if websockets is None:
            raise ImportError("websockets is required: pip install websockets")

        self.app_ws_url = app_ws_url
        self._ws: Optional[WebSocketClientProtocol] = None
        self._call_id = 0
        self._cell_id: Optional[list] = None
        self._zome_name = "rose_forest"

    async def connect(self, installed_app_id: str = "rose_forest"):
        """Connect to the conductor app WebSocket and resolve the cell ID."""
        logger.info(f"Connecting to {self.app_ws_url}")
        self._ws = await websockets.connect(self.app_ws_url)

        # Get app info to resolve cell_id
        app_info = await self._app_request("app_info", None)
        if app_info is None:
            raise HolochainError("No app info returned — is the app installed?")

        # Extract cell_id from the first role
        cell_info = app_info.get("cell_info", {})
        for role_name, cells in cell_info.items():
            for cell in cells:
                if "provisioned" in cell:
                    self._cell_id = cell["provisioned"]["cell_id"]
                    logger.info(f"Resolved cell_id for role '{role_name}'")
                    return

        raise HolochainError(f"No provisioned cell found in app '{installed_app_id}'")

    async def close(self):
        """Close the WebSocket connection."""
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def add_knowledge(self, input: RoseNodeInput) -> bytes:
        """
        Create a RoseNode in the DHT.

        Returns the ActionHash of the created entry.
        """
        payload = {
            "content": input.content,
            "embedding": input.embedding,
            "license": input.license,
            "metadata": input.metadata,
        }
        result = await self._call_zome("add_knowledge", payload)
        return bytes(result) if result else b""

    async def vector_search(self, input: SearchInput) -> list[SearchResult]:
        """
        Search for RoseNodes by embedding similarity.

        Returns a list of SearchResult sorted by score descending.
        """
        payload = {
            "query_embedding": input.query_embedding,
            "k": input.k,
        }
        results = await self._call_zome("vector_search", payload)
        return [
            SearchResult(
                hash=bytes(r["hash"]) if isinstance(r["hash"], list) else r["hash"],
                score=r["score"],
                content=r["content"],
            )
            for r in (results or [])
        ]

    async def budget_status(self) -> dict:
        """Get current agent budget status."""
        return await self._call_zome("budget_status", None)

    # ── Internal Protocol ────────────────────────────────

    async def _call_zome(self, fn_name: str, payload: Any) -> Any:
        """Make a zome call to the coordinator zome."""
        if self._cell_id is None:
            raise HolochainError("Not connected — call connect() first")

        zome_call_payload = msgpack.packb(payload) if payload is not None else msgpack.packb(None)

        request = {
            "type": "call_zome",
            "data": {
                "cell_id": self._cell_id,
                "zome_name": self._zome_name,
                "fn_name": fn_name,
                "payload": zome_call_payload,
                "provenance": self._cell_id[1],  # agent pubkey
                "cap_secret": None,
            },
        }
        return await self._app_request("call_zome", request["data"])

    async def _app_request(self, method: str, params: Any) -> Any:
        """
        Send a request to the conductor app interface.

        The Holochain app WebSocket protocol (0.4.x):
        Request: msgpack({type: "request", id: N, data: {type: METHOD, data: PARAMS}})
        Response: msgpack({type: "response", id: N, data: RESULT})
        """
        if not self._ws:
            raise HolochainError("WebSocket not connected")

        self._call_id += 1
        request_id = self._call_id

        # Build the request envelope
        request_msg = msgpack.packb({
            "id": request_id,
            "type": "request",
            "data": msgpack.packb({
                "type": method,
                "data": msgpack.packb(params) if params is not None else None,
            }),
        })

        await self._ws.send(request_msg)
        response_raw = await self._ws.recv()

        response = msgpack.unpackb(response_raw, raw=False)

        if response.get("type") == "response":
            data = response.get("data")
            if isinstance(data, bytes):
                data = msgpack.unpackb(data, raw=False)

            if isinstance(data, dict) and data.get("type") == "error":
                raise HolochainError(f"Conductor error: {data.get('data', 'unknown')}")

            # Unpack nested msgpack in response data
            if isinstance(data, dict) and "data" in data:
                inner = data["data"]
                if isinstance(inner, bytes):
                    return msgpack.unpackb(inner, raw=False)
                return inner
            return data
        else:
            raise HolochainError(f"Unexpected response type: {response.get('type')}")


# ── Convenience Functions ────────────────────────────

def understanding_to_rose_node(
    understanding: dict,
    embedding: list[float],
    model_id: str = "all-MiniLM-L6-v2",
    model_card_hash: str = "sha256:placeholder",
    license: str = "MIT",
) -> RoseNodeInput:
    """
    Convert a ConversationMemory Understanding to a RoseNode input.

    Args:
        understanding: dict with at least 'content' key (from ConversationMemory)
        embedding: the vector embedding of the content
        model_id: identifier of the embedding model used
        model_card_hash: SHA-256 hash of the model card
        license: SPDX license identifier

    Returns:
        RoseNodeInput ready for add_knowledge()
    """
    content = understanding.get("content", "")
    if not content and "description" in understanding:
        content = understanding["description"]

    metadata = {
        "model_id": model_id,
        "model_card_hash": model_card_hash,
    }

    # Carry over any extra metadata from the understanding
    for key in ("source", "agent_id", "timestamp", "level"):
        if key in understanding:
            metadata[key] = str(understanding[key])

    return RoseNodeInput(
        content=content,
        embedding=embedding,
        license=license,
        metadata=metadata,
    )


async def round_trip_demo(app_ws_url: str = "ws://localhost:8888"):
    """
    Demonstrate a full round-trip:
    1. Create a mock Understanding (as from ConversationMemory)
    2. Convert to RoseNode and write to Holochain
    3. Retrieve via vector_search
    4. Verify content matches

    Requires a running Holochain conductor with rose_forest hApp installed.
    """
    import random

    # Mock understanding from ConversationMemory
    understanding = {
        "content": "The walking skeleton is the conversation itself — "
                   "a carrier signal bridging human meaning and machine state.",
        "source": "conversation_memory",
        "agent_id": "claude-demo",
        "level": "level_0",
    }

    # Mock embedding (in production, use a real embedder)
    embedding = [random.uniform(-1, 1) for _ in range(128)]

    # Convert to RoseNode input
    node_input = understanding_to_rose_node(
        understanding=understanding,
        embedding=embedding,
        model_id="mock-embed-128d",
        model_card_hash="sha256:demo_round_trip_test",
    )

    # Connect and write
    connector = HolochainConnector(app_ws_url=app_ws_url)
    try:
        await connector.connect()

        print(f"Writing Understanding as RoseNode...")
        action_hash = await connector.add_knowledge(node_input)
        print(f"  → ActionHash: {action_hash.hex()[:24]}...")

        # Check budget
        budget = await connector.budget_status()
        print(f"  → Budget remaining: {budget.get('remaining_ru', '?')} RU")

        # Search for it
        print(f"Searching via vector_search...")
        results = await connector.vector_search(
            SearchInput(query_embedding=embedding, k=1)
        )

        if results:
            top = results[0]
            print(f"  → Found: score={top.score:.4f}")
            print(f"  → Content matches: {top.content == understanding['content']}")
            assert top.content == understanding["content"], "Content mismatch!"
            assert top.score > 0.99, f"Expected near-perfect match, got {top.score}"
            print("✓ Round-trip verified!")
        else:
            print("✗ No results returned")

    finally:
        await connector.close()


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8888"
    print(f"Running round-trip demo against {url}")
    print("(Requires running Holochain conductor with rose_forest hApp)\n")

    asyncio.run(round_trip_demo(url))
