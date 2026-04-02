# ADR-009 — MemeGraph Protocol Module

**Status:** Accepted
**Date:** February 24 2026

**Context:** MemeGraph_Protocol_Integration_v0.2.md defines meme lineage tracking with Git + Holochain + Semantic CRDT.

**Decision:** Add as FLOSSI U module for knowledge attribution.
Separate stable hashing from semantics; granular phrase-level attribution.

**Consequences:**
- Enables verifiable meme evolution.
- Critique: 1M ops/sec CRDTs need real benchmarks.
- Signed Confidence: +0.90 (novel, but untested at scale)
- Provenance: MemeGraph doc + this thread
