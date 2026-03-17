# ARF Integration Points

**Version**: 1.1 (Phase 5 Post-Merge)
**Date**: 2025-11-14
**Status**: ACTIVE

---

## Overview

This document maps the integration points between Phase 4 components and establishes clear contracts for cross-component communication. Understanding these integration points is essential for extending the system or adding new components.

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer (4.2)                   │
│  ┌─────────┬─────────┬──────────┬─────────────┐    │
│  │ memory  │ swarm   │ ontology │ benchmark   │    │
│  └────┬────┴────┬────┴─────┬────┴─────┬───────┘    │
└───────┼─────────┼──────────┼──────────┼────────────┘
        │         │          │          │
        ▼         ▼          ▼          ▼
┌───────────────────────────────────────────────────────┐
│              Application Layer                        │
│  ┌──────────┬──────────┬──────────┬──────────┐      │
│  │ Memory   │ Swarm    │ Ontology │ Benchmark│      │
│  │ Core     │ (4.1)    │ Validator│ Suite    │      │
│  └────┬─────┴────┬─────┴────┬─────┴────┬─────┘      │
└───────┼──────────┼──────────┼──────────┼────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
┌───────────────────────────────────────────────────────┐
│              Infrastructure Layer                     │
│  ┌──────────┬──────────┬──────────┬──────────┐      │
│  │ Bridge   │ Holochain│ Storage  │ Network  │      │
│  │ (4.3)    │ DHT      │ Backends │ Protocols│      │
│  └──────────┴──────────┴──────────┴──────────┘      │
└───────────────────────────────────────────────────────┘
```

---

## Integration Point 1: CLI → Core Libraries

### Purpose
Provide user-friendly command-line access to all core functionality with consistent UX.

### Contract

#### CLI Commands Map to Core Functions
```python
# arf memory transmit "..." →
ConversationMemory.transmit(understanding)

# arf memory recall --query "..." →
ConversationMemory.recall(query)

# arf swarm query "..." →
PonySwarm.run(query)

# arf ontology validate "(s, p, o)" →
OntologyValidator.validate(triple)

# arf benchmark run --suite swarm →
BenchmarkSuite.run_benchmarks(suite_name)
```

#### Interface Requirements
- **Exit Codes**: 0=success, 1=error, 130=interrupt
- **Output Formats**: Human-readable (default) + JSON (--json flag)
- **Error Handling**: All exceptions caught and converted to user messages
- **Logging**: Controlled via --verbose/-v and --quiet/-q flags

#### Integration Files
- `ARF/cli/main.py` - Entry point and CLI framework
- `ARF/cli/memory.py` - Memory command integration
- `ARF/cli/swarm.py` - Swarm command integration
- `ARF/cli/ontology.py` - Ontology command integration
- `ARF/cli/benchmark.py` - Benchmark command integration

### Example: Adding a New CLI Command

```python
# 1. Create new subcommand file: ARF/cli/new_feature.py
import typer
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from your_module import YourFeature  # Import core library

app = typer.Typer(help="New feature operations")

@app.command()
def do_something(
    param: str = typer.Argument(..., help="Parameter description"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Command description"""
    try:
        feature = YourFeature()
        result = feature.do_something(param)

        if json_output:
            import json
            print(json.dumps({"success": True, "result": result}))
        else:
            from rich.console import Console
            console = Console()
            console.print(f"[green]Result:[/green] {result}")

        sys.exit(0)
    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)

# 2. Register in ARF/cli/main.py
from cli import new_feature
app.add_typer(new_feature.app, name="new-feature")
```

---

## Integration Point 2: Swarm → Memory

### Purpose
Enable swarm to store query results in conversation memory for future recall.

### Contract

#### Swarm Stores Results
```python
# After swarm completes query
swarm_result = swarm.run(query)

# Optionally store in memory
if store_in_memory:
    memory = ConversationMemory(agent_id=swarm.agent_id)
    memory.transmit({
        "content": f"Query: {query}\nResult: {swarm_result}",
        "metadata": {
            "source": "pony_swarm",
            "N": swarm.N,
            "K": swarm.K,
            "T": swarm.T,
            "diversity": swarm_result.diversity,
        }
    })
```

#### Memory Provides Context to Swarm
```python
# Before running swarm
memory = ConversationMemory(agent_id=agent_id)
relevant_memories = memory.recall(query)

# Pass as context to swarm
swarm_result = swarm.run(
    query=query,
    context=[m.content for m in relevant_memories]
)
```

#### Integration Files
- `ARF/pwnies/desktop_pony_swarm/core/swarm.py` - Swarm implementation
- `ARF/conversation_memory.py` - Memory implementation
- `ARF/tests/integration/test_swarm_sensors.py` - Integration tests

### Example: Swarm with Memory Integration

```python
from conversation_memory import ConversationMemory
from pwnies.desktop_pony_swarm.core.swarm import PonySwarm

# Agent with memory
agent_id = "research_assistant"
memory = ConversationMemory(agent_id=agent_id)

# Recall relevant context
query = "What are the latest AI models?"
context = memory.recall(query, top_k=3)

# Run swarm with context
swarm = PonySwarm(N=4, K=2, T=3)
result = swarm.run(query, context=[c.content for c in context])

# Store result for future queries
memory.transmit({
    "content": result.final_answer,
    "metadata": {
        "query": query,
        "source": "pony_swarm",
        "timestamp": time.time(),
    }
})
```

---

## Integration Point 3: Bridge → MCP Protocol

### Purpose
Expose Infinity Bridge sensor streams via Model Context Protocol for agent consumption.

### Contract

#### Bridge Registration in DHT
```rust
// Holochain registry zome
#[hdk_entry_helper]
pub struct BridgeRegistration {
    pub bridge_id: String,
    pub capabilities: Vec<String>,  // ["acoustic_20hz_20khz", "fft_1024"]
    pub transport: Vec<String>,     // ["usb_hid", "tcp"]
    pub endpoint: String,
    pub signature: Signature,
}
```

#### MCP Resource Exposure
```python
# MCP server exposes bridges as resources
from mcp import MCPServer

server = MCPServer()

# Discover bridges
bridges = await discover_bridges()

# Expose each stream as MCP resource
for bridge in bridges:
    for stream_type in bridge.capabilities:
        resource_uri = f"bridge://{bridge.bridge_id}/{stream_type}"
        server.add_resource(resource_uri, bridge.get_stream(stream_type))
```

#### Integration Files
- `ARF/dnas/infinity_bridge/zomes/registry/src/lib.rs` - Holochain registry
- `ARF/in.finite-nrg/infinity-bridge/orchestrator/discovery.py` - Discovery service
- `ARF/in.finite-nrg/infinity-bridge/orchestrator/mcp_server.py` - MCP server
- `ARF/in.finite-nrg/infinity-bridge/tests/test_protocol.py` - Protocol tests

### Example: Agent Subscribing to Bridge Stream

```python
from infinity_bridge.orchestrator.discovery import discover_bridges
import asyncio

async def agent_with_sensors():
    # Discover available bridges
    bridges = await discover_bridges(timeout=5.0)

    # Find acoustic bridge
    acoustic_bridge = next(
        b for b in bridges
        if "acoustic_20hz_20khz" in b.capabilities
    )

    # Subscribe to spectrum stream
    stream = await acoustic_bridge.subscribe("acoustic/spectrum")

    # Read samples
    async for sample in stream:
        # Process sensor data
        frequencies = sample.frequencies
        amplitudes = sample.amplitudes

        # Use in agent reasoning
        if max(amplitudes) > THRESHOLD:
            await agent.alert("High acoustic activity detected")

asyncio.run(agent_with_sensors())
```

---

## Integration Point 4: Ontology → Memory Validation

### Purpose
Validate semantic triples during memory transmission to ensure knowledge graph consistency.

### Contract

#### Memory Calls Ontology Validator
```python
# In ConversationMemory.transmit()
def transmit(self, understanding: dict):
    # Extract triples from understanding
    triples = self._extract_triples(understanding["content"])

    # Validate each triple against ontology
    if self.validate_ontology:
        for triple in triples:
            is_valid = OntologyValidator.validate(triple)
            if not is_valid:
                raise ValidationError(f"Invalid triple: {triple}")

    # Store if validation passes
    self._store(understanding)
```

#### Ontology Provides Validation Rules
```python
class OntologyValidator:
    def validate(self, triple: tuple) -> bool:
        """
        Validate (subject, predicate, object) against ontology rules.

        Returns True if valid, False otherwise.
        """
        subject, predicate, object = triple

        # Check predicate exists in ontology
        if predicate not in self.predicates:
            return False

        # Check domain/range constraints
        pred_schema = self.predicates[predicate]
        if not self._check_domain(subject, pred_schema.domain):
            return False
        if not self._check_range(object, pred_schema.range):
            return False

        return True
```

#### Integration Files
- `ARF/conversation_memory.py` - Memory with validation hooks
- `ARF/dnas/rose_forest/zomes/ontology/src/lib.rs` - Ontology zome
- `ARF/tests/integration/test_ontology_pipeline.py` - Validation tests

### Example: Memory with Ontology Validation

```python
from conversation_memory import ConversationMemory
from ontology_validator import OntologyValidator

# Create memory with validation enabled
memory = ConversationMemory(
    agent_id="validated_agent",
    validate_ontology=True,
    ontology_validator=OntologyValidator()
)

# Valid triple: succeeds
try:
    memory.transmit({
        "content": "GPT-4 is_a LLM",
        "metadata": {"source": "test"}
    })
    print("✅ Valid triple accepted")
except ValidationError:
    pass

# Invalid triple: fails
try:
    memory.transmit({
        "content": "GPT-4 ate_a sandwich",  # Invalid predicate
        "metadata": {"source": "test"}
    })
except ValidationError as e:
    print(f"❌ Invalid triple rejected: {e}")
```

---

## Integration Point 5: Benchmark → All Components

### Purpose
Provide performance testing infrastructure for all major components.

### Contract

#### Benchmark Suite Organization
```python
class BenchmarkSuite:
    def run_benchmarks(self, suite_name: str) -> BenchmarkResults:
        """
        Run specified benchmark suite.

        Available suites:
        - memory: ConversationMemory operations
        - swarm: PonySwarm query performance
        - bridge: Infinity Bridge discovery/streaming
        - ontology: Ontology validation performance
        - all: All benchmarks
        """
```

#### Component Benchmark Interface
```python
# Each component should provide:
class ComponentBenchmark:
    def setup(self):
        """Initialize component for benchmarking."""

    def benchmark_operation(self, iteration: int):
        """Run single benchmark iteration."""

    def teardown(self):
        """Cleanup after benchmarking."""

    def get_metrics(self) -> dict:
        """Return performance metrics."""
        return {
            "latency_ms": self.latency,
            "throughput": self.throughput,
            "error_rate": self.error_rate,
        }
```

#### Integration Files
- `ARF/cli/benchmark.py` - CLI benchmark interface
- `ARF/pwnies/benchmarks/benchmark_suite.py` - Swarm benchmarks
- `ARF/pwnies/benchmarks/parameter_sweep.py` - Parameter optimization
- `ARF/pwnies/tests/test_performance.py` - Performance regression tests

### Example: Adding Component to Benchmark Suite

```python
# 1. Implement benchmark class
class MyComponentBenchmark:
    def __init__(self, iterations: int = 10):
        self.iterations = iterations
        self.latencies = []

    def run(self):
        from my_component import MyComponent

        component = MyComponent()

        for i in range(self.iterations):
            start = time.time()
            component.do_operation()
            end = time.time()
            self.latencies.append(end - start)

        return {
            "mean_latency_ms": statistics.mean(self.latencies) * 1000,
            "p95_latency_ms": statistics.quantiles(self.latencies, n=20)[18] * 1000,
            "p99_latency_ms": statistics.quantiles(self.latencies, n=100)[98] * 1000,
        }

# 2. Register in benchmark CLI
# In ARF/cli/benchmark.py, add to run() function:
if suite in ("my_component", "all"):
    results["my_component"] = MyComponentBenchmark(iterations).run()
```

---

## Integration Point 6: Integration Tests → All Components

### Purpose
Validate cross-component coordination and end-to-end scenarios.

### Contract

#### Test Organization
```
ARF/tests/integration/
├── __init__.py
├── conftest.py                      # Shared fixtures
├── test_multi_agent_memory.py       # Memory composition tests
├── test_swarm_sensors.py            # Swarm + Bridge integration
├── test_ontology_pipeline.py        # Memory + Ontology validation
└── test_holochain_python_bridge.py  # Holochain + Python integration
```

#### Shared Fixtures (conftest.py)
```python
import pytest

@pytest.fixture
def integration_environment():
    """Setup complete integration environment."""
    # Start Holochain conductor
    conductor = start_mock_conductor()

    # Deploy test DNAs
    conductor.deploy_dna("rose_forest")
    conductor.deploy_dna("infinity_bridge")

    # Setup test bridges
    bridges = setup_test_bridges()

    yield {
        "conductor": conductor,
        "bridges": bridges,
    }

    # Cleanup
    conductor.shutdown()
    cleanup_bridges(bridges)
```

#### Integration Test Pattern
```python
@pytest.mark.integration
async def test_full_pipeline(integration_environment):
    """Test complete data flow through all components."""
    env = integration_environment

    # 1. Bridge provides sensor data
    bridge = env["bridges"][0]
    sensor_data = await bridge.read_sample()

    # 2. Agent processes with swarm
    swarm = PonySwarm(N=4, K=2, T=3)
    analysis = swarm.run(
        f"Analyze sensor reading: {sensor_data}",
        context=[]
    )

    # 3. Store in memory with validation
    memory = ConversationMemory("agent", validate_ontology=True)
    memory.transmit({
        "content": analysis,
        "metadata": {"source": "swarm", "sensor": bridge.id}
    })

    # 4. Verify storage in Holochain
    entries = env["conductor"].query_entries("Understanding")
    assert len(entries) > 0
```

#### Integration Files
- `ARF/tests/integration/conftest.py` - Shared fixtures
- `ARF/tests/integration/README.md` - Integration test guide
- `.github/workflows/integration.yml` - CI/CD integration

---

## Testing Integration Points

### Unit Tests
Test individual components in isolation with mocked dependencies.

```python
# Test memory without real Holochain
def test_memory_transmit(mock_holochain_conductor):
    memory = ConversationMemory("test", conductor=mock_holochain_conductor)
    memory.transmit({"content": "test"})
    assert mock_holochain_conductor.entry_count > 0
```

### Integration Tests
Test component interactions with real or realistic mocks.

```python
# Test swarm + memory together
async def test_swarm_memory_integration():
    swarm = PonySwarm(N=2, K=1, T=2)
    memory = ConversationMemory("test")

    result = swarm.run("test query")
    memory.transmit({"content": result})

    recalled = memory.recall("test query")
    assert len(recalled) > 0
```

### End-to-End Tests
Test complete user workflows across all components.

```python
# Test CLI → Swarm → Memory → Holochain
def test_cli_end_to_end(tmp_path):
    # Run CLI command
    result = subprocess.run(
        ["arf", "swarm", "query", "test", "--store-memory"],
        capture_output=True,
    )
    assert result.returncode == 0

    # Verify storage
    result = subprocess.run(
        ["arf", "memory", "recall", "--query", "test", "--json"],
        capture_output=True,
    )
    data = json.loads(result.stdout)
    assert data["success"] is True
    assert len(data["understandings"]) > 0
```

---

## Extension Guidelines

### Adding a New Component

1. **Create core library** in `ARF/your_component/`
2. **Add CLI interface** in `ARF/cli/your_component.py`
3. **Register in CLI** in `ARF/cli/main.py`
4. **Add benchmarks** in `ARF/benchmarks/your_component.py`
5. **Add unit tests** in `ARF/tests/test_your_component.py`
6. **Add integration tests** in `ARF/tests/integration/test_your_component.py`
7. **Update this document** with new integration points

### Integration Checklist

- [ ] Component has clear API contract
- [ ] CLI integration follows existing patterns
- [ ] Benchmarks provide performance metrics
- [ ] Unit tests cover core functionality
- [ ] Integration tests validate cross-component use
- [ ] Documentation updated with examples
- [ ] Error handling follows project conventions
- [ ] Logging uses consistent format

---

## Common Integration Patterns

### Pattern 1: CLI → Core → Storage

```
User → CLI Command → Core Library → Storage Backend
  ↓       ↓              ↓               ↓
 "arf"  Parse args   Business logic   Holochain DHT
        Validate     Error handling   or JSON file
        Format output
```

### Pattern 2: Agent → Swarm → Memory → Ontology

```
Agent Query → Swarm Processing → Memory Storage → Ontology Validation
     ↓             ↓                   ↓                ↓
  "What is X?"  RSA algorithm    transmit()      validate_triple()
              N agents generate  Extract triples  Check constraints
              K selected         Store if valid   Return errors
```

### Pattern 3: Sensor → Bridge → Agent → Action

```
Physical Sensor → Bridge → MCP Protocol → Agent → Decision → Action
       ↓           ↓           ↓            ↓         ↓         ↓
   MEMS mic    USB HID     Resource URI  Context  Analysis  Command
   FFT processing  Registry  Subscribe   Reasoning           Output
```

---

## Troubleshooting Integration Issues

### Problem: CLI can't import core library

**Solution**: Check `sys.path.insert()` in CLI file:
```python
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### Problem: Tests can't find fixtures

**Solution**: Ensure `conftest.py` is in test directory or parent:
```
ARF/tests/
├── conftest.py          # Available to all tests
├── integration/
│   ├── conftest.py      # Additional fixtures for integration tests
│   └── test_*.py
```

### Problem: Component not in benchmark suite

**Solution**: Add to `ARF/cli/benchmark.py` run() function and list-suites command.

### Problem: Integration test hangs

**Solution**: Check for missing async/await or timeouts:
```python
# Add timeout to async operations
result = await asyncio.wait_for(operation(), timeout=5.0)
```

---

## Phase 5 Integration Points (IMPLEMENTED)

### Integration Point 7: Budget Engine → All Operations

**Purpose**: Resource-bounded autonomy for all Holochain operations

**Key Integrations**:
- Budget tracking for Rose Forest operations (add_knowledge, link_edge, etc.)
- Budget enforcement for Memory operations (transmit, validate, compose)
- Budget integration with Committee Validation (10 RU per validation)
- Budget tracking for Pattern Library operations (15 RU per pattern)

**Files**:
- `ARF/dnas/rose_forest/zomes/memory_coordinator/src/budget.rs`
- `ARF/dnas/rose_forest/BUDGET_SYSTEM.md`
- `ARF/cli/budget.py` (future)

### Integration Point 8: Committee Validation → Memory & Patterns

**Purpose**: Multi-agent consensus for triple and pattern validation

**Key Integrations**:
- Integration with ConversationMemory for triple validation
- Integration with Pattern Library for pattern quality validation
- Budget-aware validation (graceful degradation on low budget)
- Metrics tracking for false positive reduction

**Files**:
- `ARF/validation/committee.py`
- `ARF/validation/agent_pool.py`
- `ARF/validation/models.py`
- `ARF/conversation_memory.py` (committee integration)

### Integration Point 9: Pattern Library → Infinity Bridge

**Purpose**: Meaningful sensor mixing validation for Infinity Bridge

**Key Integrations**:
- 23+ validated patterns for sensor correlation
- 5 validation criteria (≥2 required)
- DHT-based pattern discovery and indexing
- Community contribution workflow

**Files**:
- `ARF/dnas/infinity_bridge/zomes/patterns/src/lib.rs`
- `ARF/dnas/infinity_bridge/zomes/patterns/README.md`
- `ARF/dnas/infinity_bridge/zomes/patterns/VERIFICATION.md`

**See**: `ARF/PHASE_5_INTEGRATION.md` for detailed integration patterns

### Planned for Phase 6

- **Distributed Tracing**: OpenTelemetry across all components
- **Metrics Dashboard**: Prometheus/Grafana integration
- **Debug Tooling**: Advanced debugging CLI commands
- **Pattern Discovery**: ML-based pattern mining from sensor data

---

## Related Documentation

- `ARF/PHASE_5_INTEGRATION.md` - **NEW**: Phase 5 detailed integration guide
- `ARF/ARCHITECTURE_OVERVIEW.md` - System architecture
- `ARF/dev/ROADMAP_PHASE4_PLUS.md` - Development roadmap
- `ARF/cli/README.md` - CLI usage guide
- `ARF/tests/integration/README.md` - Integration testing guide

---

**For FLOSSI0ULLK - Clear Integration Contracts**

*"The spec is the source of truth. Code serves the spec."*

---

**Version**: 1.1 (Phase 5 Update)
**Status**: ACTIVE
**Last Updated**: 2025-11-14
**Maintainer**: FLOSSI0ULLK Development Team
