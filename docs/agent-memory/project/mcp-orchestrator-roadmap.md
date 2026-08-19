---
id: project-mcp-orchestrator-roadmap
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_mcp_orchestrator_roadmap.md
title: MCP orchestrator roadmap beyond voting
legacy_description: The consensus gateway is phase 1 (voting only). Phase 2 will expand
  to model-to-model collaboration; a centralized local LLM is likely to join the roster.
origin_session_id: 7a8fdf1c-cf5f-4d01-a344-82a0dec070b6
---

The MCP orchestrator shipped in commit 096b058 (packages/metacoordinator_mcp + packages/orchestrator + packages/source_chain) is explicitly **phase 1**: a passive-router consensus gateway that accepts Claims and Votes, runs analog [-0.999, +0.999] voting rounds against a Cerebras + Groq voter roster, and appends decisions to a file-based source chain.

Future scope the user has named (not yet designed, not yet authorized to build):
- **Phase 2 — model-to-model collaboration beyond voting**: the orchestrator will need to support richer protocols than WEIGHT+RATIONALE votes. Models should be able to exchange partial work, critique, delegate subtasks, and converge on shared artifacts — not just cast opinions on a fixed Claim.
- **Centralized local LLM likely to join the roster**: the user plans to run a local model (no vendor specified yet) that would participate alongside the Cerebras and Groq voters. Implications: the voter adapter layer should stay vendor-agnostic (it already does — `voters.py` uses pure LiteLLM env-var routing), and the loop should tolerate a mix of remote-fast and local-slower participants.

**Phase 1.5 status (verify against current commits before asserting):**
- Voter roster expanded to **Mistral + Cerebras + Groq + Flowith** (commit b8e34b2: "Add Mistral voters and canonicalize Vibe surface").
- **Hashline pre/post-write verification** landed in `packages/metacoordinator_mcp/hashline.py` — stale landings fail closed by deriving exact post-images from pre-write checkpoints (consensus harness rule).
- **ADR-9 continuity spec** added (commit ebd3df9, "Bootstrap consensus env and add ADR-9 continuity spec").
- Significant gateway hardening tail: `f9daa43`, `510bdad`, `0c14939` (consensus gate override provenance, hashline edge cases).
- **Diversity policy now codified** in `METAHARNESS_OPERATING_MODEL.md`: nontrivial polls span ≥3 provider surfaces and ≥4 model families; same-family endpoints don't count as independence.
- Vibe surface canonicalized; public landing page added; G-0-B/main merge integrated (commit 012682e).

How to apply:
- When touching the orchestrator or voter layer, preserve the passive-router invariant and the stateless CellDirectory-over-disk pattern — both are load-bearing for the eventual Holochain substrate mapping.
- Keep the voter adapter interface narrow and vendor-agnostic. Do not hardcode Cerebras/Groq assumptions into the gateway itself.
- Phase 2 work should not be bolted onto `consensus_gate.py`. A collaboration protocol is a different abstraction than a voting protocol; expect a sibling module, not an extension.
- The ADR-MCP-ORCHESTRATOR Divergence section is the pattern for documenting future shifts: when something diverges from the original proposal, amend the ADR with a new Divergence entry rather than rewriting history.
