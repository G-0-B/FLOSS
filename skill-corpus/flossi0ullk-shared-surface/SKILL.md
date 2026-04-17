---
name: flossi0ullk-shared-surface
description: Use when changing or extending the shared FLOSSI0ULLK agent surface: MCP servers, context manifests, skill manifests, materializers, or agent-native projections for Codex, Gemini, Claude-adjacent tooling, or OpenCode.
---

# FLOSSI0ULLK Shared Surface

The shared surface is generated, not hand-curated per client.

## Core workflow

1. Edit canonical sources only:
   - `.mcp.json`
   - `FLOSS/shared-agent-surface.json`
   - `FLOSS/shared-context-surface.json`
   - `FLOSS/shared-skill-surface.json`
   - `FLOSS/skill-corpus/*`
2. Regenerate native views:
   - `python FLOSS/scripts/materialize_shared_context_surface.py`
   - `python FLOSS/scripts/materialize_shared_skill_surface.py`
   - `python FLOSS/scripts/materialize_shared_agent_surface.py`
3. Run the matching `--check` commands before stopping.
4. If a change affects multiple surfaces, update the plan doc and context pointers so future agents can discover it cheaply.

## Rules

- Do not hand-edit generated projections when the canonical source can be changed instead.
- Keep shared surface changes additive and reversible.
- Prefer portable markdown and JSON manifests over agent-specific one-offs.

## References

Open only what you need:

- `references/surface-map.md`

