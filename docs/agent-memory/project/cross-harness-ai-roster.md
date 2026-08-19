---
id: project-cross-harness-ai-roster
type: project
created: '2026-05-25'
status: active
applies_to:
  - any-agent
  - openwork
  - opencode
  - codex
  - claude
  - gemini
source: codex_session
title: Cross-harness AI roster and update packet are generated shared surfaces
---

FLOSSI0ULLK now has a central AI/harness roster surface:

- Canonical manifest: `FLOSS/shared-ai-roster-surface.json`
- Generated machine inventory: `.agent-surface/harness/ai-roster.json`
- Generated operator summary: `.agent-surface/harness/AI_ROSTER.md`
- Generated startup handoff: `.agent-surface/harness/HARNESS_UPDATE_PACKET.md`
- OpenWork default agent projection: `opworkers/.opencode/agents/openwork.md`

Use this when the user asks about coordinating Claude, ChatGPT/Codex, Gemini,
Kimi/Moonshot, Grok/x.ai, OpenWork/OpenCode, or other model/provider surfaces.
The JSON roster is the comprehensive provider/model listing. The markdown roster
is a readable summary.

The update packet is the central instruction payload for harnesses that cannot
directly consume the full manifest stack. It reminds agents to load `CONTEXT_L0`,
repo-owned shared memory, the roster, and `AGENTMEMORY.md`, and to treat
agentmemory recall as evidence candidates rather than canon.

Boundary to preserve:

- Repository canon wins over generated projections, source-chain evidence,
  verified provenance packets, and agentmemory recall.
- Load-bearing cross-agent handoffs that bind System/Substrate claims require
  provenance packet evidence and normal promotion through docs/specs/ADRs/claims.
- The shared roster is generated state; update the manifest or source configs
  first, then run `python FLOSS/scripts/materialize_shared_agent_surface.py`.
