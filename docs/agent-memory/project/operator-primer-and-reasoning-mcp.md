---
id: project-operator-primer-and-reasoning-mcp
type: project
created: '2026-05-19'
status: active
applies_to:
- any-agent
source: codex_session
title: Operator primer is the first human-readable map; reasoning ensemble MCP is registered
---

As of 2026-05-19, `FLOSS/docs/architecture/OPERATOR_PRIMER.md` is the
human-first "what is this / how do I use it" entry point for the local
FLOSSI0ULLK metaharness. It summarizes current phase status, runtime planes,
session-start flow, emergency controls, SDD discipline, and the current best
next moves.

The primer is part of shared context:

- `INDEX.md` lists it as canonical.
- `FLOSS/shared-context-surface.json` includes it in L0 context generation.
- `FLOSS/shared-agent-surface.json` includes it in shared context pointers and
  Vibe startup pointers.
- `.agent-surface/context/CONTEXT_L0.md`, `.agent-surface/CONTEXT_POINTERS.md`,
  and `.agent-surface/VIBE_STARTUP.md` are regenerated projections.

The reasoning ensemble MCP is also registered through the shared surface:

- root `.mcp.json` includes `flossiullk-reasoning-ensemble`
- `FLOSS/.mcp.json` is the generated mirror
- `.mcp/lenses/flossiullk-reasoning-ensemble.yaml` wraps the server through
  JanuScope
- generated Gemini, OpenCode, and Vibe configs include the server
- Vibe gives it a longer cold-start budget: `startup_timeout_sec = 120`,
  `tool_timeout_sec = 240`

Important boundary: the reasoning ensemble is reasoning-grade Plane A tooling.
It can route prompts and generate synthesis drafts; it does not submit consensus
Claims, cast Votes, or promote canon. Decision-grade moves still go through the
separate `flossiullk-consensus` MCP and source-chain path.
