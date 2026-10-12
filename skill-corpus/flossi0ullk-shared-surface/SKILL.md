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
2. Regenerate native views with the single runner:
   - `python FLOSS/scripts/refresh_agent_surfaces.py`
   - Add `--include-user-scope` to also write `~/.codex/config.toml` and the
     AppData Hermes home. A live Hermes gateway is refused, not clobbered.
   - `--only <step>` runs one step; `--list` names them. The six individual
     materializers still work standalone.
3. Run `python FLOSS/scripts/refresh_agent_surfaces.py --check` before stopping.
   A step reporting exit 1 under `--check` means drift **or** a step error —
   read that step's own output above the summary to tell them apart.
4. If a change affects multiple surfaces, update the plan doc and context pointers so future agents can discover it cheaply.
5. If a change touches filewatch, intake queues, or consolidation routing, also update:
   - `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md`
   - `FLOSS/docs/specs/intake-event.spec.md`
   - `FLOSS/docs/specs/intake-event.schema.json`

## Rules

- Do not hand-edit generated projections when the canonical source can be changed instead.
- **`.mcp.json` is the single source of truth for MCP servers.** Never hand-edit a harness config (Codex, Hermes, OpenCode, Gemini, Vibe) — change `.mcp.json` and re-run the runner. Hand-editing is what produced the 2026-07-24 six-surface drift, after the propagator had been silently crashing for a week.
- **Materializers resolve the wrong root from a worktree.** They derive the workspace root as the script checkout's parent. From a worktree nested under `FLOSS/.worktrees/` or a sibling at the workspace root, the root is wrong and canonical sources may be absent.
  - From a worktree, run a materializer only with `--check` or `--dry-run`, never to write.
  - On reported DRIFT, read the path column before regenerating. Paths outside the expected workspace, or inside another checkout, mean wrong root, not drift.
  - The memory materializer treats a missing canonical source as zero entries and plans to overwrite the user-wide memory index with a heading-only file. As of 2026-10-12 it has no `--include-user-scope` gate (the check was a grep of `scripts/materialize_shared_agent_memory.py`), so it always writes user scope. Re-check this before relying on it.
- Keep shared surface changes additive and reversible.
- Prefer portable markdown and JSON manifests over agent-specific one-offs.
- Agent memory is shared-surface state: write durable learnings to `FLOSS/docs/agent-memory/`, then materialize projections. Do not treat Claude/Codex/Gemini private memory dirs as canonical.
- Runtime event queues under `.agent-surface/events/` are generated state, not the source of truth.

## References

Open only what you need:

- `references/surface-map.md`
