# FLOSS/hooks/

Hook scripts invoked by harnesses (Claude Code, Gemini CLI, Codex, Hermes) on
file-edit and session events. Never run these by hand and never edit a
harness config to point at them by hand — see "Generated, not hand-wired"
below.

## Scripts

- **`hook_pre_write.py`** — `PreToolUse`/`BeforeTool` on `Write|Edit|MultiEdit`
  (Claude, Codex, Hermes) / `write_file|replace` (Gemini). Snapshots the
  pre-write file image and stores a deterministic checkpoint under
  `FLOSS_AGENT_DIR/checkpoints/pre_write` so the post-write hook can detect
  stale/intervening writes. Latency-critical: no network calls, no
  agentmemory. Filters to substantive edits only (`packages/**/*.{py,rs,toml}`,
  skipping `tests/`, `__pycache__/`, `.venv/`, `venv/`, `archive/`).

- **`hook_post_write.py`** — `PostToolUse`/`AfterTool`, same matcher/tools as
  above. Fast path (<100 ms): builds a Claim from the edit (with a
  spec-gate advisory note for gated surfaces — `scripts/`, `docs/specs/`,
  `docs/adr/` — and a hashline verification against the pre-write
  checkpoint), submits it to the local consensus gateway, then spawns
  `hook_bg_round.py` DETACHED and returns. Makes no agentmemory call itself.

- **`hook_bg_round.py`** — spawned detached (not wired to any harness event
  directly) by `hook_post_write.py`. Runs the full consensus round
  (Cerebras + Groq via LiteLLM), logs the outcome, and — since it's already
  slow (~10 s) — saves the accepted-edit note and the resolved consensus
  outcome to agentmemory. This is the only one of the three write-path
  hooks that ever touches agentmemory.

- **`session_start_inject.py`** — `SessionStart` (Codex today; Claude/Gemini
  get orientation another way). Emits the `STARTUP_CONTRACT.md` content as
  `additionalContext`, plus a small, hard-capped (`<=1s`) best-effort
  agentmemory recall of a few recent decisions. Degrades silently to
  contract-only on any recall failure or timeout.

- **`agentmemory_client.py`** — minimal MCP-stdio client (`save`, `recall`)
  used by `hook_bg_round.py` and `session_start_inject.py`. No REST path
  exists for agentmemory; this speaks MCP-over-stdio to
  `@agentmemory/mcp/bin.mjs` via absolute `node` + script paths. Never
  raises, never blocks past its `timeout`, never writes to stdout.

## Shared stdin/stdout contract

- **stdin**: one JSON object with at least `tool_name`, `tool_input`
  (containing `file_path`/`filePath`/`path`/`target_file`), and
  `hook_event_name`. This is the Claude Code hook payload shape; Hermes
  emits the same `tool_name`/`tool_input` fields so no translation is
  needed for that harness.
- **stdout**: hooks that need a structured response emit `{}` by default,
  or (with `--stdout-json`, used by the Gemini target) a
  `hookSpecificOutput.additionalContext` string. **Never** write anything
  else to stdout — that's the channel the harness reads the hook protocol
  on. All diagnostics go to `FLOSS_AGENT_DIR/hook.log`
  (default `~/.floss_agent/hook.log`).
- **Exit code**: always `0`. Every script wraps `main()` in a top-level
  try/except that logs and still exits 0 — a hook must never block the
  user's edit, regardless of what goes wrong internally.

## Generated, not hand-wired

Every harness's hook config is **projected** from `FLOSS/shared-hook-surface.json`
by `scripts/materialize_shared_hook_surface.py` (part of
`scripts/refresh_agent_surfaces.py`). To change what fires, edit the
manifest and regenerate — never hand-edit `.claude/settings.json`,
`.gemini/settings.json`, `.codex/hooks.json`, or `.toilet/hermes/config.yaml`
directly; a hand edit will be silently overwritten (or, worse, drift
unnoticed) the next time the surface is materialized.

## Re-approval after the `scripts/` → `hooks/` move (2026-07-26)

Both Codex and Hermes pin hooks by content, so relocating these five
scripts and rewriting every generated command string invalidated existing
approvals. This was expected and is a one-time event.

- **Codex**: hook commands are pinned by `trusted_hash` in
  `C:\Users\kalis\.codex\config.toml` under
  `[hooks.state.'C:\~shit\.codex\hooks.json:<event>:0:0']` for each of
  `pre_tool_use`, `post_tool_use`, `session_start`. Trigger any real edit
  through Codex; it will refuse or prompt to re-trust the changed
  `.codex/hooks.json`. Approve the new hash at that prompt (or via
  whatever non-interactive re-trust flag the installed Codex CLI exposes)
  — do not hand-edit `config.toml`.
- **Hermes**: shell hooks require allowlist approval recorded in
  `~/.hermes/shell-hooks-allowlist.json` (keyed in part by
  `script_mtime_at_approval`). The move changed every script's mtime, so
  the existing approvals no longer match. `hooks_auto_accept` is `false`
  and a non-TTY gateway cannot prompt — the operator must trigger a real
  tool call through Hermes at an interactive TTY once, and approve the
  prompt there. Do not flip `hooks_auto_accept` to work around this.
- **Claude Code / Gemini**: no pinning — the regenerated `.claude/settings.json`
  / `.gemini/settings.json` take effect on the next hook invocation, no
  re-approval needed.
