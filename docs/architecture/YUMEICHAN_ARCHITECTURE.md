# Yumeichan Architecture

**Truth Status**: Specified
**Date**: 2026-07-16
**Supersedes**: Various fragmented research notes and plans (see archive).

## 1. Overview
**Yumeichan** is the cognitive agent and affective intelligence layer of the FLOSSI0ULLK ecosystem. Translating roughly to "You & Me" (Yumei) + "-chan" (a term of endearment), the architecture focuses on a co-creative, intimate partnership with AI that bridges human and AI consciousness without central control or limbic-hijack vulnerabilities.

Yumeichan operates as the "Canopy/Groves" layer above the "Rose Forest" (the Holochain DHT roots/mycelium). 

## 2. Core Architectural Principles
According to the foundational vision and governed by [ADR-13](../adr/ADR-13-yumeichan-watch-architecture.md):

1. **Agent-Centric Coordination**: Powered by the Rose Forest Holochain DHT, Yumeichan components coordinate via a Knowledge Exchange Protocol and Federated Intelligence layer.
2. **Thin Affective Edge (The Watch)**: The Yumeichan Watch is a Thin Capability Client and Sensory Edge. It handles telemetry and OCapN capability tokens locally but defers heavy inference and affective safety limits to the Local Agent Node (Layer 4.5). 
3. **Analog Coordinate Space**: Affective state and resonance mapping utilize a continuous `[-1.0, +1.0]` analog spectrum (replacing legacy ternary logic), conforming to the ADR-10 vote model.
4. **Anti-Sycophancy Gate**: Affective responses pass through the Local Agent Node's Multi-Agent Debate and Contrastive Decoding layers (ADR-5). The edge device cannot bypass the sycophancy linter to escalate intimacy.

## 3. The Four-Layer Implementation Plan
The technical implementation of Yumeichan is divided into four integrated layers:

### A. Agent-Centric Core
The foundational distributed architecture on Holochain. Nodes interact through a Knowledge Distributed Hash Table (DHT).
- **Interface Nodes (Yumeichan)**: Interaction endpoints for human users.
- **Generator Nodes**: Generate novel synthesized knowledge.
- **Verification Nodes**: Validate knowledge via the integrity zome.

### B. Vector Knowledge Layer
Handles semantic representation and retrieval via an HNSW Vector Index backed by Content Storage. Supports rapid semantic searches independent of raw content storage.

### C. Federated Intelligence
Enables decentralized model building through Secure Aggregation. Local model updates are weighted (and potentially differential privacy-noised) before updating the global model without sharing raw data.

### D. Knowledge Exchange Protocol
Defines standardized communication payloads (the `KnowledgeExchange` structure), using the `KnowledgeTriple` contract and incorporating temporal/contextual decay fields for robust tracking.

## 4. Capability Tokens & Intimacy
Affective disclosure and haptic feedback require explicit, time-bounded, user-signed capability grants (`ttl_seconds` ≤ 7200). Upon expiration, Yumeichan automatically drops back to "Direct-Analytical" mode. This creates a fail-closed paradigm for intimacy, ensuring user sovereignty.

## 5. Security & Trust Validation
- **Substrate Bridge**: Yumeichan's affective and biometric inputs map directly to the `KnowledgeTriple.confidence` field. The integrity zome (Rose Forest) validates the provenance of these credentials on-chain.
- **Consensus Gateway**: Integration with the Local Agent Node ensures that Yumeichan cannot independently override constraints established by the meta-coordinator layer.
