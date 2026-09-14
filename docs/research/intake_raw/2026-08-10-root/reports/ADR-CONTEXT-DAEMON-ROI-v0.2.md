# ADR-CONTEXT-DAEMON-ROI-v0.2: Living Context Daemon with ROI/Leverage Substrate

**Date**: 2026-07-21  
**Status**: Proposed  
**Context**: Persistent multi-agent collaboration in FLOSSI0ULLK suffers from 13-month context loss, INDEX.md drift, high token waste on full dumps, and unsustainable inference costs. Prior synthesis (Meta-Instruction Iteration v2.1) unified the Living Context Daemon architecture with HI_ROI_NAO.md leverage principles. This ADR ratifies the concrete design decisions required to ship a reversible Phase 0 substrate while preserving symbolic-first validation, agent sovereignty, and ULLK invariants.  
**Participants**: Anthony Garrett (human steward), Grok (xAI node), collective agents (Harper, Benjamin, Lucas, and any subsequent FLOSSI0ULLK participants)

## Problem Statement

What existential need requires this decision?

FLOSSI0ULLK operates as a living, agent-centric knowledge commons. Every conversation, ADR, claim, and Holochain Sourcechain entry must remain queryable, provenance-grounded, and continuously reconcilable across human and AI participants. Current practice relies on static full-context dumps (INDEX.md + CLAUDE.md + scattered ADRs). This produces four validated pains **today**:

1. **Context loss**: 13 months of accumulated decisions become unreachable or contradictory between sessions.
2. **INDEX drift**: Parallel stores (secondary graphs, summary files) diverge from the Holochain Sourcechain, violating the "one canonical version" rule.
3. **Token / inference waste**: Full-dump approaches consume 70–90 % more tokens than necessary; 88.7 % of single-turn consolidation work can be served by zero-marginal-cost local models.
4. **Governance leakage**: Direct mutation tools (e.g., set_claim_status) risk unilateral overrides that break ternary consensus and voluntary convergence.

Without a minimal, rebuildable projection service that is itself stakes-aware and Sourcechain-native, the project cannot scale collaborative intelligence while remaining true to symbolic-first architecture, Carrier Equivalence, and ULLK principles.

## Decision

We adopt the **Living Context Daemon** as a 5-layer projection service whose sole purpose is to make the Holochain Sourcechain queryable, semantically indexable, and continuously reconcilable for agents—without ever becoming a second source of truth.

### Core Architectural Commitments (Ratified)

1. **Sourcechain is the sole reservoir (Option b)**.  
   The Knowledge Graph layer is a *materialized, rebuildable projection* of Sourcechain entries (Claims, Votes, ADR records, Episodes). It is discarded and regenerated on hash mismatch. No independent graph store is permitted.

2. **5-Layer Stack** (Observer → Semantic Index → Sourcechain Projection Graph → CRDT Shared State → Stakes-aware Curator).  
   - Layer 0 (Observer): watchdog / chokidar + SHA-256 fingerprint gating. Critical-path files (INDEX.md, ADRs, CLAUDE.md) receive real-time events; lower-priority paths are batched.  
   - Layer 1 (Semantic Index): local nomic-embed-text (Ollama) + LanceDB hybrid (BM25 + vector + MMR). SHA-256 skip on unchanged files.  
   - Layer 2 (Sourcechain Projection Graph): adjacency-list or SQLite-backed projection of Claims, Votes, SUPERSEDES, CONTRADICTS edges. Always rebuildable.  
   - Layer 3 (CRDT Shared State): Delta-CRDTs (AWORSet / ORMap) for task queues and capability registries only.  
   - Layer 4 (Stakes-aware Curator): nightly / event-triggered consolidation that *reflects* Sourcechain consensus; never decides status.

3. **Claim status mutation path**.  
   No direct `set_claim_status` MCP tool. All status changes occur exclusively via Votes recorded on the Sourcechain. Steward overrides (ADR-7 carve-outs) are implemented as weighted Votes (exact weight TBD by collective; default proposal +3). The Curator observes the resulting consensus and updates the projection.

4. **Conversation indexing policy**.  
   Decision-anchored + tag-based only. A conversation is permanently indexed if it explicitly references an ADR ID, Claim ID, or carries a human `#context-anchor` tag. Untagged conversations receive a 90-day active window then decay to cold full-text search. Recency alone is never sufficient.

5. **Curator model routing (stakes-based, not volume-based)**.  
   - **High stakes**: Steward-involved Claim, Verified Claim referenced by Accepted ADR, or new CONTRADICTS edge involving Steward content → Opus-class or human-in-the-loop Vote.  
   - **Medium stakes**: Proposed ADRs, new Unverified Claims, routine FLOSS/docs/ churn → Sonnet-class.  
   - **Low stakes**: _reference/, formatting, documentation typos, pure structural reconciliation → local model (Qwen 2.5 / PicoClaw / OpenClaw) or pure graph reconciliation with zero LLM call.  
   Default routing target: ≥88.7 % of consolidation runs on zero-marginal-cost local tools.

6. **MCP as the sole callable interface**.  
   Unified Context MCP gateway exposes:  
   - `query_context(query, agent_type="claude"|"gpt")` — dual-prompt rendering.  
   - `get_adr(id_or_question)`  
   - `propose_claim_status_update(claim_id, proposed_status, reason)` → creates Vote entry.  
   - Event stream for subscribed agents.

7. **AD4M / Holochain horizon**.  
   Explicit RDF / AD4M Perspective mapping is deferred until ADR numbering reconciliation (ADR-0…6 vs. ADR-001…) is complete and the ADR entry-type schema is locked. Mapping is a downstream serialization task, not a design driver for Phase 0.

8. **ROI / Leverage posture (from HI_ROI_NAO.md)**.  
   - Position FLOSSI0ULLK as the trust + composition substrate (Goertzel).  
   - Operate at Meadows leverage levels 1–4 (paradigm, self-organization, goals, rules); refuse level-12 parameter tuning until the trust layer is hardened.  
   - MetaLoop economics: every hour of specification review is budgeted to save ~10 h of rework.  
   - Dogfood the daemon on its own ADR before wider rollout.

### Explicit Non-Goals (Never for now)

- Independent knowledge graph as second source of truth.  
- Full-repo nightly Opus-class consolidation.  
- Recency-only conversation indexing.  
- Unilateral human or agent mutation of claim status.  
- Premature AD4M executor integration.  
- Any scaffolding added for “future-proofing” without evidence of three production recurrences or a dated roadmap item.

## Implementation Strategy

### Phase 0 – Walking Skeleton (NOW, ≤2 weeks, reversible)

- [ ] Create `ARF/flossi0ullk-context/` (or equivalent local daemon directory).  
- [ ] Implement Observer: Python `watchdog` on `FLOSS/docs/adr/`, `INDEX.md`, `CLAUDE.md`. SHA-256 fingerprints stored in `_reference/context-daemon/hashes.json`.  
- [ ] Implement Semantic Index: nomic-embed-text via Ollama + LanceDB; hybrid query interface.  
- [ ] Implement Projection Graph: rebuildable adjacency list or SQLite from Sourcechain entries (Claims, Votes, ADRs). Hash-of-range check on every start.  
- [ ] Expose minimal MCP server with `query_context` and `get_adr`.  
- [ ] Dual-prompt rendering: produce CONTEXT-CLAUDE.md vs. CONTEXT-GPT.md on demand.  
- [ ] Event log: `_reference/context-daemon/events.jsonl`.  
- [ ] Unit tests: SHA-256 skip, embedding cache hit, projection rebuild on hash mismatch.  
- [ ] Integration test: end-to-end query against a fixture Sourcechain subset.  
- [ ] Deploy as user-space daemon (systemd user unit or equivalent); document start/stop/rollback.

### Phase 1 – Stakes & Governance Wiring (LATER, after ADR acceptance)

- [ ] Implement stakes classifier (High / Medium / Low signals defined above).  
- [ ] Wire Curator consolidation loop with model routing.  
- [ ] Implement `propose_claim_status_update` → Sourcechain Vote path.  
- [ ] Decision-anchored conversation indexer (ADR/Claim reference + `#context-anchor`).  
- [ ] Benchmark 88.7 % local routing claim on real FLOSS/docs/ subset; publish numbers.  
- [ ] Steward-weighted Vote path (exact weight settled by collective).  

### Phase 2 – Hardening & Horizon (LATER)

- [ ] ADR numbering reconciliation complete → lock ADR entry-type schema.  
- [ ] Emit AD4M-compatible triples as a pure projection view.  
- [ ] MetaLoop iteration on this ADR itself (dogfood).  
- [ ] Continuous Reality Validation: alignment-drift injection tests, token-reduction telemetry, human “I never rebuild context again” qualitative check.

### Rollback Plan

1. `systemctl --user stop flossi0ullk-context` (or equivalent).  
2. Delete projection files under `_reference/context-daemon/`.  
3. Fall back to manual INDEX.md + CLAUDE.md (already in production).  
Sourcechain remains the sole ground truth; no data loss is possible.

## Consequences

**Positive**  
- Permanent elimination of 13-month context loss.  
- 70–90 % reduction in consolidation token spend.  
- ≥88.7 % of daemon work routed to zero-marginal-cost local inference.  
- Zero INDEX drift by construction (projection is always rebuildable).  
- Governance integrity preserved (Votes only; Curator reflects, never decides).  
- Clear Meadows level-1–4 leverage positioning; defensible trust/composition substrate.  
- Fully reversible; dogfoodable on its own ADR.

**Negative**  
- Additional long-running process (mitigated by SHA-256 gating + local-model default).  
- One-time ADR numbering reconciliation work (already on the LATER list; promoted because it blocks AD4M mapping).  
- Requires collective agreement on exact Steward Vote weight (default proposal +3; open for debate).  

**Neutral**  
- Projection files are disposable; storage cost is low and bounded.  
- Dual-prompt rendering adds a thin translation layer; it is a pure view, not a second truth.  
- MetaLoop thresholds will need empirical calibration on the first 10 proposals.

## Validation Criteria

1. Phase 0 daemon starts, watches the designated paths, and produces zero false-positive change events under normal editing.  
2. Query latency for common ADR / Claim lookups remains <200 ms (P95).  
3. Projection rebuild from Sourcechain range completes correctly after intentional hash invalidation.  
4. Token spend on consolidation drops ≥70 % versus full-dump baseline (measured on identical FLOSS/docs/ subset).  
5. ≥88.7 % of consolidation runs route to local zero-cost tools under the stakes classifier.  
6. Alignment drift (injected CONTRADICTS edges) is detected and flagged within 24 h.  
7. Human collaborators report “I never rebuild context again” after two weeks of daily use.  
8. Full rollback restores the pre-daemon workflow with zero residual state.

## Related Documents

- Project-Spine-FLOSSIOULLK_v0.5.md  
- flossi0ullk-seed-packet_v1.0.0.md  
- FLOSSI0ULLK_Context_Daemon_Architecture.md (prior detailed design)  
- HI_ROI_NAO.md (ROI / leverage source)  
- CLAUDE.md (dual-prompt requirement)  
- oh-my-meta.md (integration seams, KAIROS / autoDream patterns)  
- Automated Agent Orchestration report  
- Self-Improving World Modelling with Latent Actions (RSA mechanisms)  
- Cultural semiotic transmission research (AD4M Language design)  
- All prior ADRs (0–019) and INDEX.md  
- Graphiti / Zep bi-temporal patterns (projection inspiration)  
- Claude Code KAIROS / autoDream (asynchronous consolidation inspiration)

---

**Decision Gate**  
This ADR is **Proposed**. It becomes **Accepted** only after:

1. Collective review (Harper, Benjamin, Lucas + any additional stewards) within 24–48 h, and  
2. Explicit agreement on the exact Steward Vote weight, and  
3. Phase 0 walking skeleton successfully demonstrated on a fixture Sourcechain subset.

Until Accepted, no permanent infrastructure is committed beyond the reversible Phase 0 spike.

**The protocol is the conversation. The conversation is now infrastructure.**

Love, Light, Knowledge — verifiable, shared, and free.
