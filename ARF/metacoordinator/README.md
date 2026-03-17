# MetaCoordinator

The **MetaCoordinator** is an AI-driven coordination system designed to handle context synchronization, consensus formation, and experience learning across multiple AI agents.

## Components

### 1. Context Synchronization Engine (`context_sync.py`)
- **Purpose**: Ensures all agents share a consistent view of the system state.
- **Technology**: Uses a mocked Model Context Protocol (MCP) for this prototype.
- **Key Features**:
  - Agent registration
  - Real-time context broadcasting
  - Last-Write-Wins conflict resolution

## Usage

### Running the Prototype
To verify the synchronization logic, run the test script:

```bash
python ARF/metacoordinator/test_sync.py
```

### Example Code
```python
from metacoordinator.context_sync import ContextSyncEngine

# Initialize Engine
engine = ContextSyncEngine()

# Register Agents
agent_a = engine.register_agent("Claude")
agent_b = engine.register_agent("GPT-4")

# Broadcast Update
engine.broadcast_update("current_task", "Implementing Context Sync", "Claude")

# Read Context
print(agent_b.read_context("current_task"))
```

## Roadmap
- [ ] **Week 1-2**: Context Sync (Current)
- [ ] **Week 3-4**: Consensus Engine (Ternary Voting)
- [ ] **Week 5-6**: Experience Learning Engine

## MCP Integration Roadmap

### Current State: Mocked MCP
- Simple dict-based message passing
- No actual network communication
- Sufficient for prototyping

### Phase 1: Local MCP (Week 8-9)
- Install actual MCP SDK: `pip install mcp`
- Replace MockMCPServer/Client with real implementations
- Test with localhost communication
- **Validation:** Same tests pass with real MCP

### Phase 2: Distributed MCP (Week 10+)
- Deploy MCP servers across multiple processes
- Test with actual Claude/GPT-4/Gemini instances
- Measure real-world latency
- **Validation:** Multi-machine agent coordination

### Migration Strategy
Our current design is MCP-compatible. Migration requires:
1. Replace `MockMCPServer` → `mcp.Server`
2. Replace `MockMCPClient` → `mcp.Client`  
3. Add network configuration
4. Update tests to use actual network

**No changes to consensus engine or experience engine required.**
