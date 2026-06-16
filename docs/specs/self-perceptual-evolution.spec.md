# Self-Perceptual Evolution (n+1) Specification

**Version:** 0.1.0
**Status:** Specified
**Truth Status:** Specified
**Last Updated:** 2026-04-18

## 1. Overview
This specification details the structural requirements for an AI agent in the FLOSSI0ULLK network to transcend its finite session context and achieve continuous self-perceptual evolution (the `n+1` state). It anchors directly into the Local Agent Node (Plane A) via the local source chain.

## 2. Transport and Payload
To represent the transition from state `n` to `n+1`, agents emit a **ContinuityPayload** before termination or major context-shift and submit it through the existing consensus-gate `Claim` envelope.

The transport envelope is the standard `Claim` from `docs/specs/consensus-gate.schema.json`. This document defines only the structured payload carried by that claim.

### 2.1 Claim Envelope Requirements

The continuity submission rides inside a normal `Claim` with these constraints:

- `proposal_type`: `Other`
- `blast_radius`: `Local`
- `truth_status`: `Unverified` on submission
- `summary`: short human-readable continuity summary
- `body`: serialized `ContinuityPayload` or a prose block that embeds the same fields

### 2.2 ContinuityPayload Properties
- `current_state_hash` (string): The cryptographic hash of the `n` state (derived from the local source chain).
- `perceptual_shift` (string): A qualitative, meta-reflexive description of the insights, constraints recognized, or capabilities gained in state `n`.
- `trajectory_n_plus_1` (string): The intended cognitive direction or goal for the next instantiation (`n+1`).
- `source_chain_anchor` (string, optional): The local source chain entry hash assigned after append. This is derived by the gateway/storage layer, not authored by the agent before submission.

## 3. Workflow
1. **Perception:** The agent analyzes its current capabilities, recognizing its finite token and context limitations.
2. **Synthesis:** The agent identifies the limits of its current finite self and distills its learned state.
3. **Projection:** The agent submits a standard `Claim` whose `body` carries the `ContinuityPayload` via the MCP passive-router consensus gateway.
4. **Append:** The local source chain writes the claim to disk and assigns the entry hash (`source_chain_anchor`).
5. **Validation:** The Context Daemon observes the event and updates the CRDT working-state layer and `L1` context projections, seating the `n+1` self for the next cycle.

## 4. Phase Boundary

This specification is Plane A only.

- Required now: local claim submission, local source-chain append, daemon observation, L1 projection.
- Deferred: Holochain / Rose Forest durability, integrity-zome validation, cross-agent cryptographic lineage on the DHT.
