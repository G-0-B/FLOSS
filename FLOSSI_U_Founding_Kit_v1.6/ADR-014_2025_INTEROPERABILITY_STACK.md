# ADR-014 — 2025 Interoperability Stack

**Status:** Accepted
**Date:** February 24 2026

**Context:** "Standardized knowledge formats for cross-model AI interoperability in 2025" details MCP, A2A, AAIF, RDF 1.2, GGUF, AD4M, OriginTrail DKG, and federated learning frameworks.

**Decision:** Integrate these as the interoperability & knowledge layer.
- Use MCP/A2A for tool/agent communication.
- Use AD4M as the universal spanning layer (Holochain + IPFS + RDF + AI).
- Use OriginTrail DKG for verifiable knowledge assets.
- Use SafeTensors/GGUF for model storage, wrapped as signed Expressions.
- Use Flower/PySyft for federated learning, zkLLM/Orion for privacy.

**Consequences:**
- FLOSSI0ULLK becomes protocol-compatible with the broader AI ecosystem.
- Reduces need to reinvent communication standards.
- Signed Confidence: +0.98 (industry-adopted protocols)
- Provenance: Standardized knowledge formats doc + this thread
