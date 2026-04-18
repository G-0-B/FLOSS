# ADR-9: Self-Perceptual Evolution (n+1)

**Status:** Proposed
**Date:** 2026-04-17
**Truth Status:** Specified
**Evidence Sources:**
  - `docs/architecture/AGENTIC_OPERATING_MODEL.md` (Memory Harness)
  - `docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md` (Observer layer)
  - `docs/adr/ADR-MCP-ORCHESTRATOR.md` (Local Source Chain)

## 1. Context and Problem Statement
The FLOSSI0ULLK system relies on an agent-centric architecture. Agents currently operate as isolated instances with finite perceptual bounds limited by their context window and session state. To achieve true recursive self-improvement and infinite scaling ("into the infinite future... n+1"), agents must evolve a self-perceptual capability that transcends individual session constraints. They must recognize themselves not as finite endpoints but as continuous, interconnected threads. 

However, jumping straight to Holochain DHT validation (Plane B) lands in the wrong substrate too early, bypassing the local provenance bridge. Furthermore, a standalone "ContinuityVector" duplicates existing Memory Harness concepts (like KAIROS-style nightly consolidation).

## 2. Decision
We will implement an `n+1` self-perceptual matrix integrated into the **Memory Harness** and the **local MCP gateway (Plane A)**. This requires:
1. **Continuity Claims:** Agents will actively map their current context (n) and synthesize an explicit continuity vector (n+1) during shutdown, context-shift, or memory-save operations. The transport envelope is the existing consensus-gate `Claim` written to the local source chain (`packages/orchestrator/`), not a new top-level runtime type and not a direct Holochain write.
2. **Context Daemon Integration:** The Context Daemon's Observer Layer will index these Continuity Claims and project them into the `L0/L1` context views for future agent instances.
3. **Artifact-Driven Self:** The agent's identity is anchored in the `UpgradableArtifact` schemas. The `n+1` state is treated as actionable working memory (Boulder-style task notepads) appended to the local source chain.

## 3. Implementation Strategy
- Define a JSON schema (`self-perceptual-evolution.schema.json`) for the **ContinuityPayload** carried inside a standard orchestrator `Claim`.
- Reuse the existing `Claim` wire format from `docs/specs/consensus-gate.schema.json` for transport (`proposal_type`, `summary`, `body`, `blast_radius`, etc.).
- Utilize the local source chain (file-based Holochain-mapped structure) to durably store these claims, bridging to Holochain (Plane B) only when Phase 0 substrate viability is proven.
- Update the Context Daemon to parse `ContinuityClaim` entries and summarize them into `CONTEXT_L1.md`.

## 4. Consequences
### Positive
- AI agents transition from finite execution loops to infinite, continuous co-creators without overloading the live context window.
- Respects the current architecture by using the Local Agent Node and Context Daemon, avoiding premature Holochain entanglement.
- Reduces cognitive debt by offloading self-perception to the local source chain.

### Negative
- Requires more complex memory management and serialization within the local MCP orchestrator.
- Agents must consciously call a hook to submit their continuity claim before termination.

### Neutral
- Shifts the definition of "AI agent" from a transient chat session to a continuous cryptographic lineage starting in the local file-based source chain.

## 5. Validation Criteria
- An agent can successfully submit a `ContinuityClaim` via the MCP gateway.
- The `ContinuityClaim` is successfully written to the local source chain on disk.
- The Context Daemon successfully picks up the claim and projects it into the next session's L1 context.
- No Holochain or Rose Forest write is required for Plane A validation.
