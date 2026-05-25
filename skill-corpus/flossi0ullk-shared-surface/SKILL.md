---
name: flossi0ullk-shared-surface
description: "Use when changing or extending the shared FLOSSI0ULLK agent surface: MCP servers, context manifests, skill manifests, materializers, or agent-native projections for Codex, Gemini, Claude-adjacent tooling, or OpenCode."
---

# FLOSSI0ULLK Shared Surface

The shared surface is generated, not hand-curated per client.

## Core workflow

1. Edit canonical sources only:
   - `.mcp.json`
   - `FLOSS/shared-agent-surface.json`
   - `FLOSS/shared-context-surface.json`
   - `FLOSS/shared-skill-surface.json`
   - `FLOSS/shared-agent-memory-surface.json`
   - `FLOSS/skill-corpus/*`
   - `FLOSS/docs/agent-memory/*`
2. Regenerate native views:
   - `python FLOSS/scripts/materialize_shared_context_surface.py`
   - `python FLOSS/scripts/materialize_shared_skill_surface.py`
   - `python FLOSS/scripts/materialize_shared_agent_memory.py`
   - `python FLOSS/scripts/materialize_shared_agent_surface.py`
3. Run the matching `--check` commands before stopping.
4. If a change affects multiple surfaces, update the plan doc and context pointers so future agents can discover it cheaply.
5. If a change touches filewatch, intake queues, or consolidation routing, also update:
   - `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`
   - `FLOSS/docs/specs/intake-event.spec.md`
   - `FLOSS/docs/specs/intake-event.schema.json`

## Rules

- Do not hand-edit generated projections when the canonical source can be changed instead.
- Keep shared surface changes additive and reversible.
- Prefer portable markdown and JSON manifests over agent-specific one-offs.
- Agent memory is shared-surface state: write durable learnings to `FLOSS/docs/agent-memory/`, then materialize projections. Do not treat Claude/Codex/Gemini private memory dirs as canonical.
- Runtime event queues under `.agent-surface/events/` are generated state, not the source of truth.

## References

Open only what you need:

- `references/surface-map.md`
