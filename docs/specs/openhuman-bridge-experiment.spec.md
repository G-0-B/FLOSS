# OpenHuman ↔ FLOSSI0ULLK Bridge Experiment

**Status:** ⚠️ Specified (Proof of Concept)
**Target:** OpenHuman Core Architecture & FLOSSI0ULLK Layer 4.5 (Consensus Gateway)

## 1. Abstract
OpenHuman provides a sovereign, local-first intelligence and memory tree for the *individual*. FLOSSI0ULLK provides a cryptographic, agent-centric coordination layer for the *commons*.

This experiment proves the integration seam between the two: allowing an OpenHuman agent to publish a specific memory claim to a shared Holochain-backed DHT, and allowing a separate OpenHuman agent to independently retrieve, evaluate, and verify that claim without relying on a centralized server.

## 2. The Seam (Data Mapping)

OpenHuman stores its data locally (SQLite/Markdown). To share a memory, the OpenHuman agent formats it as a FLOSSI0ULLK `Claim`.

**Mapping:**
- **OpenHuman Memory Event** → `Claim.body`
- **Memory Context/Tags** → `Claim.summary`
- **OpenHuman Agent Identity** → `Claim.proposer` (e.g., `did:key:zOpenHuman1...`)
- **Action Type** → `ProposalType.OTHER` (Semantic memory assertion)
- **Scope** → `BlastRadius.MODULE` (Peer-to-Peer shared knowledge)

The claim is submitted to the FLOSSI0ULLK `CellDirectory` (the file-based precursor to the Holochain DHT).

## 3. The Channel (CellDirectory)

Instead of sending the claim to a central server (e.g., a Discord bot or a central database), the OpenHuman agent appends it to its own local `CellDirectory` source chain. 

Holochain's gossip protocol (simulated in Layer 4.5 via file synchronization and the passive-router consensus gateway) broadcasts this claim to peers.

**Cryptographic Provenance:**
The claim is saved as a JSON file named by the `SHA256` hash of its canonical serialization. This guarantees that no other agent can modify the OpenHuman's memory without breaking the cryptographic signature.

## 4. The Validation (Yumeichan / Consensus)

A second OpenHuman node (Agent B) receives the claim. 
Instead of blindly accepting it, Agent B uses its own local LLM model to evaluate the claim against its own memories.

Agent B generates a `Vote`:
- **Weight**: Float between `[-0.999, +0.999]` representing support, opposition, or abstention.
- **Rationale**: The reasoning behind the vote.
- **Voter Identity**: `did:key:zOpenHuman2...`

This vote is appended to Agent B's source chain and gossiped back. The FLOSSI0ULLK gateway aggregates the votes into a `Decision`.

## 5. Experiment Objectives

1. **Serialize**: Successfully convert an OpenHuman memory into a valid FLOSSI0ULLK `Claim`.
2. **Store**: Persist the claim in a `CellDirectory` without schema errors.
3. **Validate**: Have a secondary agent generate a valid `Vote` against the claim.
4. **Resolve**: Aggregate the interaction into a terminal `Decision` (e.g., `Outcome.APPROVED`).

This proves that isolated personal AIs can form a verifiable, secure knowledge commons.
