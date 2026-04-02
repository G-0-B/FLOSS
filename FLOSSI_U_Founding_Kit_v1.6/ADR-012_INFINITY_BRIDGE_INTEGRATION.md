# ADR-012 — Infinity Bridge Integration

**Status:** Accepted
**Date:** February 24 2026

**Context:** COMPLETE_SPECIFICATION.md defines an agent-centric sensor network (Infinity Bridge) for discovery/subscription/analysis of multi-spectrum sensors.

**Decision:** Integrate Infinity Bridge as the perception & sensing layer.
Use Holochain DHT for discovery, MCP URIs for subscription, correlation engine for analysis. Adapt for video/audio/EMG/HRV streams.

**Consequences:**
- Provides pluggable sensor backbone for FLOSSI0ULLK hardware nodes (Atomic Pi, ESP32s, FPGAs).
- Enables verifiable sensor data with provenance.
- Signed Confidence: +0.96 (solid spec, implementation pending)
- Provenance: Infinity Bridge System docs + this thread
