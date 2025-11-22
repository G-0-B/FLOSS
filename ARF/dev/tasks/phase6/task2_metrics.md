# Task 6.2: Metrics Dashboard

**Phase**: 6 (Observability)
**Priority**: Medium
**Goal**: Expose real-time metrics for production monitoring.

## Objective
Track key performance indicators (KPIs) like latency, error rates, and resource usage using Prometheus-compatible metrics.

## Requirements
1.  **Metrics Library**:
    - Use `prometheus_client` for Python.
2.  **Key Metrics**:
    - `arf_memory_transmit_total`: Counter
    - `arf_memory_recall_seconds`: Histogram
    - `arf_swarm_query_seconds`: Histogram
    - `arf_budget_tokens_used`: Gauge
    - `arf_ontology_validation_failures`: Counter
3.  **Exposition**:
    - Expose metrics endpoint (e.g., port 8000) or push gateway support.

## Implementation Steps
1.  Create `ARF/observability/metrics.py` to define global metrics.
2.  Instrument `ConversationMemory`, `BudgetManager`, and `PonySwarm` to update these metrics.
3.  Create a simple script to start a metrics server.

## Success Criteria
- [ ] Metrics endpoint returns valid Prometheus text format.
- [ ] Metrics update correctly after operations.
- [ ] Latency histograms capture distribution of timings.
