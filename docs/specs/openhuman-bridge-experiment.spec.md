# OpenHuman ↔ FLOSSI0ULLK Bridge Experiment

**Status:** ⚠️ Specified (bounded file-precursor experiment)
**Target:** OpenHuman Core Architecture & FLOSSI0ULLK Layer 4.5 (Consensus Gateway)

**Observed scope:** ✅ Verified by
`packages/metacoordinator_mcp/tests/test_openhuman_bridge.py` — Claim/Vote schema
mapping, local content-address generation, two separately constructed Votes, and
gateway Decision aggregation.

**Unproven scope:** ⚠️ Specified — Holochain publication, peer gossip or retrieval,
entry signatures, read-time hash verification, tamper rejection, and decentralized
transport are not exercised by this experiment.

## 1. Abstract
OpenHuman provides a sovereign, local-first intelligence and memory tree for the
*individual*. FLOSSI0ULLK is designed to provide an agent-centric coordination
layer for the *commons*.

This experiment exercises a narrower precursor seam: one OpenHuman-shaped agent
maps a memory into a FLOSSI0ULLK `Claim`; two agents author valid `Vote` objects;
and the gateway aggregates those votes. It does not publish to a shared DHT or
exercise independent retrieval or cryptographic verification.

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

Instead of sending the claim to a central server, the OpenHuman agent appends it
to its own local `CellDirectory` source chain.

The current test then passes the Claim ID in memory to the second fixture. It does
not perform file synchronization, Holochain gossip, or peer retrieval.

**Content addressing:**
`CellDirectory.append_entry()` saves the Claim as canonical JSON under a filename
derived from its `SHA256` digest. The experiment independently recomputes that
digest after reading the entry and confirms it matches the returned address.
`CellDirectory.read_chain()` does not currently enforce that check, and entries
are not signed here, so this experiment makes no tamper-rejection or signature
guarantee.

## 4. The Validation (Yumeichan / Consensus)

A second OpenHuman-shaped fixture (Agent B) is given the Claim ID and constructs
its own Vote. The experiment does not invoke an LLM or inspect an external memory
store; the rationale is deterministic test data.

Agent B generates a `Vote`:
- **Weight**: Float between `[-0.999, +0.999]` representing support, opposition, or abstention.
- **Rationale**: The reasoning behind the vote.
- **Voter Identity**: `did:key:zOpenHuman2...`

This Vote is appended to Agent B's local source chain. The test passes both voter
functions directly to the FLOSSI0ULLK gateway, which aggregates them into a
`Decision`; no gossip path is exercised.

## 5. Experiment Objectives

1. **Serialize**: Successfully convert an OpenHuman memory into a valid FLOSSI0ULLK `Claim`.
2. **Store**: Persist the claim in a `CellDirectory` and recompute its local
   content address.
3. **Validate**: Have two agent fixtures generate valid `Vote` objects against
   the Claim ID.
4. **Resolve**: Aggregate the interaction into a terminal `Decision` (e.g., `Outcome.APPROVED`).

✅ Verified by the cited test: the file precursor supports schema mapping, local
content-address generation, separately constructed Vote records, and Decision
aggregation. ⚠️ Specified, not proven here: a verifiable shared commons requires
peer transport/retrieval plus enforced signatures and read-time integrity checks.
