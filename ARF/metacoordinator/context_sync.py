"""Shared context synchronization primitives for metacoordinator tests."""

import time
from typing import Any, Dict, List, Optional

# --- Mock MCP Implementation ---
# Since the actual 'mcp' library is not available in the environment,
# we mock the necessary components to demonstrate the architecture.


class MockMCPClient:
    """Minimal in-memory MCP client used by the context sync prototype."""

    def __init__(self, agent_id: str, server: "MockMCPServer"):
        self.agent_id = agent_id
        self.server = server
        self.local_context: Dict[str, Any] = {}

    def update_context(self, context_update: Dict[str, Any]):
        """Receive context updates from the server."""
        # In a real implementation, this might involve merging strategies.
        # Here we just update/overwrite.
        for key, value in context_update.items():
            self.local_context[key] = value
        print(f"[{self.agent_id}] Context updated. Keys: {list(context_update.keys())}")

    def read_context(self, key: str) -> Optional[Any]:
        """Read a single context value from the local client cache."""
        return self.local_context.get(key)


class MockMCPServer:
    """Minimal in-memory MCP server that tracks connected mock clients."""

    def __init__(self):
        self.clients: Dict[str, MockMCPClient] = {}

    def connect(self, agent_id: str) -> MockMCPClient:
        """Create and register a mock client for the given agent id."""
        client = MockMCPClient(agent_id, self)
        self.clients[agent_id] = client
        return client


# --- Context Sync Engine ---


class ContextSyncEngine:
    """MCP-based context synchronization across agents"""

    def __init__(self):
        self.mcp_server = MockMCPServer()
        self.agents: Dict[str, MockMCPClient] = {}
        self.shared_context: Dict[str, Any] = {}

    def register_agent(self, agent_id: str, capabilities: List[str] = None):
        """Register a new agent in the coordination system"""
        if agent_id in self.agents:
            print(f"Agent {agent_id} already registered.")
            return self.agents[agent_id]

        client = self.mcp_server.connect(agent_id)
        self.agents[agent_id] = client

        # Sync current context to new agent
        if self.shared_context:
            client.update_context(self.shared_context)

        print(f"Agent {agent_id} registered.")
        return client

    def broadcast_update(self, key: str, value: Any, source_agent: str):
        """Broadcast context update to all agents"""

        # Create a versioned value wrapper
        current_val = self.shared_context.get(key)
        new_version = (current_val["version"] + 1) if current_val else 1

        update_packet = {
            "value": value,
            "source": source_agent,
            "timestamp": time.time(),
            "version": new_version,
        }

        self.shared_context[key] = update_packet

        # Distribute to all agents except source (source already knows)
        # In a real distributed system, we'd send to source too for confirmation,
        # but for this prototype, we skip it to reduce noise.
        for agent_id, client in self.agents.items():
            if agent_id != source_agent:
                client.update_context({key: update_packet})
                continue

            # Update source's local context directly to reflect the "server" state.
            client.local_context[key] = update_packet

    def handle_byzantine_update(self, key: str, value: Any, source_agent: str):
        """Detect and handle potentially malicious updates"""

        # Check if agent is registered
        if source_agent not in self.agents:
            raise ValueError(f"Unknown agent {source_agent} attempted update")

        # Check for anomalous update patterns
        if key in self.shared_context:
            prev = self.shared_context[key]

            # Detect rapid version increments (possible attack)
            time_delta = time.time() - prev["timestamp"]
            if time_delta < 0.1:  # <100ms between updates
                self._flag_suspicious_activity(source_agent, key)

        # Proceed with update if valid
        self.broadcast_update(key, value, source_agent)

    def _flag_suspicious_activity(self, agent_id: str, key: str):
        """Track potentially malicious behavior"""
        if not hasattr(self, "suspicious_activity"):
            self.suspicious_activity = {}

        if agent_id not in self.suspicious_activity:
            self.suspicious_activity[agent_id] = []

        self.suspicious_activity[agent_id].append(
            {"key": key, "timestamp": time.time(), "type": "rapid_update"}
        )

        # Quarantine agent if too many violations
        if len(self.suspicious_activity[agent_id]) > 10:
            self.quarantine_agent(agent_id)

    def quarantine_agent(self, agent_id: str):
        """Temporarily disable suspicious agent"""
        print(f"⚠️ Agent {agent_id} quarantined due to suspicious activity")
        if agent_id in self.agents:
            # In a real implementation we would disable the client.
            # For this mock, we can just mark it.
            self.agents[agent_id].quarantined = True

    def resolve_conflicts(
        self, key: str, conflicting_values: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use CRDT-like resolution for conflicts (Last-Write-Wins)"""
        if not conflicting_values:
            return None

        # Sort by timestamp descending
        # In real LWW, we'd use Lamport timestamps or vector clocks
        winner = max(conflicting_values, key=lambda x: x["timestamp"])
        return winner

    def get_global_context(self) -> Dict[str, Any]:
        """Return the full shared context map tracked by the sync engine."""
        return self.shared_context
