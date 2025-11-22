# Task 6.1: Distributed Tracing

**Phase**: 6 (Observability)
**Priority**: High
**Goal**: Implement OpenTelemetry integration for cross-component tracing.

## Objective
Enable full visibility into the lifecycle of a request (e.g., `memory.transmit` or `swarm.query`) as it flows through the system components (Python, Holochain, Rust).

## Requirements
1.  **OpenTelemetry Integration**:
    - Add `opentelemetry-api` and `opentelemetry-sdk` to Python dependencies.
    - Configure a tracer provider.
2.  **Instrumentation**:
    - Instrument `ConversationMemory` methods (`transmit`, `recall`, `compose`).
    - Instrument `PonySwarm` methods.
    - Instrument `HolochainClient` calls.
3.  **Context Propagation**:
    - Ensure trace IDs are passed to Holochain zome calls (if possible via metadata) and preserved.
4.  **Visualization**:
    - Support exporting traces to a standard backend (Jaeger or console for dev).

## Implementation Steps
1.  Create `ARF/observability/tracing.py` to handle setup.
2.  Add decorators (e.g., `@traced`) to key methods in `conversation_memory.py` and `swarm.py`.
3.  Update `HolochainClient` to inject trace context into zome calls.
4.  Verify traces appear in the exporter.

## Success Criteria
- [ ] `memory.transmit` generates a trace with spans for validation, embedding, and storage.
- [ ] Trace IDs are consistent across a single operation.
- [ ] Traces can be viewed or logged.
