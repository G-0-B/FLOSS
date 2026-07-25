# MCP Surface Propagation + Unified Surface Runner — Design

**Date:** 2026-07-24
**Author:** Claude Code (Fable 5 → Opus 5 session), with operator
**Truth Status:** ⚠️ Specified (design approved, not yet implemented)
**Related:** `docs/superpowers/plans/2026-07-24-mcp-migration-fixup.md` (the incident that motivated this), ADR-19 (OmniRoute inference plane), `.claude/skills/flossi0ullk-shared-surface`

## Problem

MCP server configuration drifted across five harness surfaces (Claude Code, Codex ×2 config layers, Hermes ×2 homes, OpenCode), requiring a full session of manual repair on 2026-07-24. Every harness had a different, partly-broken view of the same four servers.

The drift was not caused by the absence of a propagation tool. **`materialize_shared_agent_surface.py` already owns MCP propagation** — it treats root `.mcp.json` as canonical and projects to Gemini, OpenCode, and Vibe. The real cause is that it has been **crashing since commit `01bdeb8` (2026-07-17)**:

```
SharedSurfaceError: Shared MCP server 'flossiullk-consensus'
cannot be projected to OpenCode without a `command` string
```

`convert_mcp_server_to_opencode` assumes every server is stdio. When consensus and ensemble moved to HTTP daemon URLs, the propagator began throwing on every run. Because it could not run, every harness was hand-edited, and the surfaces diverged.

Two secondary gaps compounded it:

1. **No Codex or Hermes targets exist at all.** Those two surfaces were never propagated, which is why they drifted worst (Codex could not even load its config; Hermes still had `npx -y` everywhere).
2. **No single entry point.** Six materializers must each be invoked by hand, so in practice none are run routinely.

## Goals

- Root `.mcp.json` is the single source of truth for MCP servers across every harness.
- A propagator that handles **both** stdio and HTTP transports.
- Codex and Hermes become managed targets.
- One command regenerates and verifies the entire shared agent surface.
- Running the propagator must **reproduce**, not revert, the verified-correct configuration established on 2026-07-24.

## Non-goals

- Changing which MCP servers exist, or their transports. This propagates the current verified state; it does not redesign it.
- Managing non-shared servers (`docker`, `node_repl`, `context7`, `openwork-*`, `chrome`). They stay untouched in each target.
- Replacing JanuScope lenses. Lenses remain the per-server policy/env layer; `.mcp.json` declares only how to reach a server.
- Runtime daemon health checks. The runner does projection only (operator decision, 2026-07-24).

## Core safety property

> **The propagator owns the managed server set and their transport fields. Everything else is preserved byte-for-byte where the format allows.**

Concretely, three nested levels of preservation:

1. **Unmanaged servers** in a target config (`docker`, `node_repl`, `context7`, `openwork-browser`, `chrome`, `openwork-ui`) are never touched.
2. **Unmanaged fields on a managed server** are preserved — e.g. Codex's `[mcp_servers.agentmemory.tools.memory_save] approval_mode = "approve"`, Hermes's `timeout`, and `startup_timeout_sec`. The propagator owns only the transport fields: `type`, `command`, `args`, `url`, `env`.
3. **Unrelated file content** — comments, key order, formatting — is preserved by using round-trip parsers (`tomlkit`, `ruamel.yaml`), not naive dump. This matters acutely for the Hermes `config.yaml`: 769 lines of unrelated settings plus a trailing commented-out `fallback_model` block that a PyYAML `safe_dump` round-trip would silently destroy.

## Architecture

### Part 1 — Repair the propagator

**File:** `FLOSS/scripts/materialize_shared_agent_surface.py`

1. **Extract `classify_transport(name, server) -> tuple[str, dict]`.** The Vibe converter (~line 415) already implements correct dispatch: a non-empty string `command` means stdio, a non-empty string `url` means http, neither is an error. Lift that into one shared helper and have every converter call it. This removes the duplicated, divergent transport logic that caused the bug.

2. **Rewrite `convert_mcp_server_to_opencode` on top of it:**
   - stdio → `{"command": [cmd, *args], "type": "local"}` (plus `env` when present)
   - http → `{"type": "remote", "url": url}`

   The `remote` shape is verified correct — `openwork-browser` and `chrome` already use it in the live OpenCode config, and it matches the config that worked on 2026-07-24.

3. **Fix an adjacent scope bug.** At ~line 1054 the OpenCode `agent_instruction_path` block is nested inside the `vibe_cfg` block and reads `opencode_cfg`. If Vibe is configured without OpenCode, `opencode_cfg` is `None` → `AttributeError`. It is in the code path being modified, so it moves into the OpenCode block. (In scope because we are editing this function; not general refactoring.)

### Part 2 — New targets

Both follow the existing per-target block pattern in `materialize()`: resolve path → load existing → build payload → `check_or_write` → append message, OR the drift flag.

**`codex` target** — TOML via `tomlkit`. Emits the discriminator verified on 2026-07-24:

```toml
[mcp_servers.<name>]
type = "stdio"              # + command, args, env
# or
type = "streamable_http"    # + url
```

A bare `url` key without `type` is rejected by Codex 0.128 with `url is not supported for stdio`; the discriminator is mandatory, not cosmetic.

**`hermes` target** — YAML via `ruamel.yaml` round-trip, writing under the existing `mcp_servers:` key:

```yaml
<name>:
  command: <cmd>            # stdio
  args: [...]
  env: {...}
# or
<name>:
  type: http                # HTTP
  url: http://127.0.0.1:PORT/mcp
```

Hermes supports HTTP natively (Streamable HTTP by default, `transport: sse` optional) — verified in `hermes-agent/tools/mcp_tool.py`.

**Hermes liveness guard.** Before writing any Hermes config, read `<home>/gateway.pid` and test whether that PID is alive. If it is, **refuse to write that target**, emit a clear message naming the PID, and mark the run as incomplete (not silently skipped). A live Hermes gateway rewrites its own config on shutdown and would clobber the projection. This encodes the hazard that was navigated manually on 2026-07-24.

### Part 3 — Target scoping

Each target block gains `scope: "repo" | "user"`.

`manifest["targets"]` is a flat dict dispatched by key, so the two Codex layers and two Hermes homes get **distinct target keys** rather than a nested instance list. This keeps the existing dispatch shape (one `if targets.get("<key>")` block per target) and lets each instance carry its own scope, name map, and overrides.

| Target key | Path | Scope | Writer |
|---|---|---|---|
| `gemini` | `.gemini/settings.json` | repo | json |
| `opencode` | `opworkers/opencode.jsonc` | repo | jsonc |
| `vibe` | `.vibe/config.toml` | repo | text |
| `codex` | `.codex/config.toml` | repo | tomlkit |
| `codex_user` | `~/.codex/config.toml` | user | tomlkit |
| `hermes_workspace` | `.toilet/hermes/config.yaml` | repo | ruamel |
| `hermes_user` | `%LOCALAPPDATA%/hermes/config.yaml` | user | ruamel |

Repo-scope targets run always. User-scope targets run only under `--include-user-scope`. A default run writes nothing outside the workspace root (`C:\~shit\`).

Note that `hermes_workspace` is scoped `repo` because it lives under the workspace root, even though `.toilet/` is untracked — scope governs *write surprise*, not git status. The liveness guard applies to both Hermes instances regardless of scope.

### Part 4 — Manifest additions

`FLOSS/shared-agent-surface.json` gains the `codex` and `hermes` target blocks. Two mechanisms both targets need:

- **`name_map`** — Hermes keys its server `Agent Memory`; `.mcp.json` calls it `agentmemory`. Without a mapping the propagator would create a duplicate server rather than update the existing one.
- **`overrides`** — per-server extra fields a target requires: Hermes's `enabled`/`timeout`, agentmemory's `AGENTMEMORY_URL`/`AGENTMEMORY_TOOLS` env. The Vibe path already has `deep_merge` + `substitute_templates` for exactly this; reuse it rather than inventing a second mechanism.

### Part 5 — The runner

**File:** `FLOSS/scripts/refresh_agent_surfaces.py`

Runs all six materializers in dependency order — agent-surface first (it owns MCP and the context pack), then context, skill, agent-memory, hook, ai-roster.

```
python FLOSS/scripts/refresh_agent_surfaces.py                        # regenerate repo scope
python FLOSS/scripts/refresh_agent_surfaces.py --check                # verify, no writes
python FLOSS/scripts/refresh_agent_surfaces.py --include-user-scope   # + user configs
python FLOSS/scripts/refresh_agent_surfaces.py --only skill           # single step
```

**Subprocess, not import.** Each materializer already exposes `main()` and a uniform CLI (`--check`, `--dry-run`, `--manifest`, `--workspace-root`). Invoking them as subprocesses keeps each independently runnable, avoids `sys.path`/global-state coupling between six scripts, and isolates a failure in one from aborting the rest. Cost is six process spawns — negligible against the clarity gained.

**Error handling:** continue on failure, aggregate results, print a summary table, exit non-zero if any step failed or reported drift. This matches the existing `--check` + drift → exit 1 convention shared by all six materializers.

## Testing

1. **Round-trip:** regenerate, then `--check` exits 0 with no drift.
2. **Fidelity (the test that matters):** after regeneration, every harness config still matches the verified-working state from 2026-07-24 — pinned `januscope` for serena/agentmemory, HTTP URLs for consensus/ensemble, correct per-target discriminators. If the propagator reverts any 2026-07-24 fix, the manifest is wrong and must be corrected before the work is considered done.
3. **Preservation:** unmanaged servers, unmanaged fields on managed servers, and file comments all survive a write. Explicitly assert the Hermes trailing `fallback_model` comment block and Codex's agentmemory `approval_mode` entries survive.
4. **Liveness guard:** with a live Hermes gateway PID, the Hermes target refuses to write and reports it.
5. **Scope:** a default run writes nothing outside the repository.

## Dependencies

`tomlkit` and `ruamel.yaml` — both already present in the Python 3.13 environment, neither currently used by repo scripts. If either is missing at runtime, the corresponding target must fail with a clear message rather than fall back to a mangling writer.

## Risks

| Risk | Mitigation |
|---|---|
| Propagator reverts the 2026-07-24 manual fixes | Fidelity test (#2) is the acceptance gate; `--check` and `--dry-run` before any real write |
| Live Hermes gateway clobbers the projection | Liveness guard refuses to write; operator restarts gateway and re-runs |
| Round-trip writer mangles a large config | `tomlkit`/`ruamel.yaml` preserve comments and order; preservation test (#3) asserts it |
| User-scope writes surprise the operator | Off by default; explicit `--include-user-scope` opt-in |
