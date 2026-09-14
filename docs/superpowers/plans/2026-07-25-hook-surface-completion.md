# Hook Surface Completion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Bring every harness's hooks under the shared hook surface, wire agentmemory into the hooks where it earns its cost, and relocate hook scripts out of `scripts/` into a dedicated `FLOSS/hooks/` — in that order, because the move invalidates hook approvals and must happen once, last.

**Architecture:** `shared-hook-surface.json` stays canonical; `materialize_shared_hook_surface.py` gains two capabilities it lacks today (YAML round-trip writing, per-target event-name mapping). agentmemory is reached from hooks via a short-lived MCP stdio client on the detached path only.

**Tech Stack:** Python 3.13, pytest, `ruamel.yaml`, existing hook + materializer scripts.

---

## Findings that shape this plan (all verified, 2026-07-25)

**Hooks are not absent.** Claude and Gemini have managed hooks that fire today (`hook_pre_write`/`hook_post_write` ran on this session's own edits). The gaps are Codex (unmanaged), Hermes (none), OpenCode (disabled).

**Codex** — event vocabulary matches Claude (`PreToolUse`/`PostToolUse`/`SessionStart`), but the file is shaped `{"hooks": {…}}` and each hook is pinned by `trusted_hash` in `~/.codex/config.toml` under `[hooks.state.'C:\~shit\.codex\hooks.json:<event>:0:0']`. The current `.codex/hooks.json` is **hand-written, untracked, and trusted** — changing its bytes forces a re-trust.

**Hermes** — hooks live in `config.yaml` under a `hooks:` key (the *same file* the MCP target writes), events are snake_case (`pre_tool_call`, `post_tool_call`), and approval is gated by `~/.hermes/shell-hooks-allowlist.json` which records `script_mtime_at_approval`. `hooks_auto_accept` is currently `false`, and a non-TTY gateway cannot prompt.

**Wire compatibility** — the existing hook scripts read `tool_name` / `tool_input` from stdin JSON, which is exactly Hermes's payload shape. Hermes also accepts Claude-Code-style `{"decision":"block","reason":…}` stdout. **No hook rewrite is needed for Hermes.**

**agentmemory call path** — port 3111 (`iii.exe`) returned 404 on every probed REST/JSON-RPC path (`/health`, `/api/*`, `/rpc`, `/openapi.json`, POST variants). A full MCP stdio handshake against `@agentmemory/mcp/bin.mjs` completed in **240 ms**. Therefore: hooks talk to agentmemory over short-lived MCP stdio, and only on paths that are already detached or already slow. Never on `hook_post_write`'s documented <100 ms fast path.

**Both Codex and Hermes pin hooks** (content hash / script mtime). Moving the scripts invalidates both. Doing the move LAST makes that a single re-approval event.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `scripts/materialize_shared_hook_surface.py` | Hook projection to all targets | Modify (YAML writer, event map) |
| `shared-hook-surface.json` | Canonical hook manifest | Modify (codex, hermes targets) |
| `hooks/agentmemory_client.py` | Minimal MCP-stdio client for hooks | Create |
| `hooks/hook_pre_write.py`, `hook_post_write.py`, `hook_bg_round.py`, `session_start_inject.py` | Relocated hook scripts | Move (Task 6) |
| `tests/test_hook_surface.py` | Hook materializer + agentmemory client tests | Create |

---

### Task 1: Adopt the Codex hooks target (byte-identical, no re-trust)

**Acceptance:** materialized `.codex/hooks.json` is **byte-identical** to the current hand-written file, so `trusted_hash` stays valid and Codex does not prompt.

- [ ] Record the current file's sha256 and exact bytes before touching anything.
- [ ] Add a `codex` target to `shared-hook-surface.json`: `enabled: true`, `settings_path: ".codex/hooks.json"`, and a marker indicating the payload is wrapped in a top-level `hooks` key (Claude's `settings.json` carries `hooks` alongside unrelated keys; Codex's file is *only* hooks).
- [ ] Teach `merge_hook_payload` / the writer to emit the wrapped shape for this target.
- [ ] Materialize with `--check` first. If it reports DRIFT, diff and adjust the manifest until it reports OK — **do not** write a differing file.
- [ ] Verify sha256 unchanged and that `[hooks.state]` entries in `~/.codex/config.toml` still match.
- [ ] Commit.

### Task 2: Hook materializer — YAML writing + event-name mapping

- [ ] Write failing tests: a target with `format: yaml` writes YAML; a target with an `event_map` renames events; unmapped events for that target are omitted rather than passed through raw.
- [ ] Add `format: json|yaml` support, using `ruamel.yaml` configured exactly as the MCP writer does (`preserve_quotes=True`, `indent(mapping=2, sequence=4, offset=2)`, `width=4096`) — a bare `YAML()` reflows the whole Hermes document.
- [ ] Add `event_map` support (per-target event renaming).
- [ ] Reuse `hermes_gateway_alive` from `materialize_shared_agent_surface` rather than writing a second liveness check — import it, don't duplicate.
- [ ] Commit.

### Task 3: Add the Hermes hooks target

- [ ] Add a `hermes_workspace` hook target: `scope: repo`, `config_path: .toilet/hermes/config.yaml`, `format: yaml`, `event_map: {PreToolUse: pre_tool_call, PostToolUse: post_tool_call}`, writing under the top-level `hooks:` key.
- [ ] `SessionStart` has no clean Hermes equivalent — omit it for Hermes rather than inventing a mapping. Say so in the manifest `reason` field.
- [ ] Preserve everything else in `config.yaml` (this is the same file the MCP target writes — the merge must be additive and comment-preserving).
- [ ] Refuse to write when the gateway is live, same as the MCP target.
- [ ] Verify with `--check`, then `--dry-run`, then a real write; confirm `mcp_servers` and `custom_providers` are untouched and comments survive.
- [ ] Commit.

### Task 4: agentmemory client for hooks

- [ ] Create `hooks/agentmemory_client.py`: a minimal, dependency-free MCP stdio client exposing `save(text, concepts)` and `recall(query, limit)`. Hard timeout (default 5 s), fails **silently and non-fatally** — a memory outage must never break a hook or block a write.
- [ ] Resolve the server via absolute `node` + `bin.mjs` paths (npm `.cmd` shims break under env-filtering harnesses — this is why the agentmemory lens uses absolute paths).
- [ ] Tests: successful save/recall against a stub server; timeout path returns cleanly; unreachable server returns cleanly; malformed response returns cleanly. **No test may depend on the live agentmemory server.**
- [ ] Commit.

### Task 5: Wire agentmemory into the opportune hook paths

Three places earn it; nowhere else.

- [ ] **`hook_bg_round.py`** (already detached, already slow) — after a consensus round resolves, save the outcome: claim id, outcome, mean weight, variance, voter roster. This is the highest-value one: consensus decisions are exactly the durable, cross-session signal agentmemory exists for.
- [ ] **`session_start_inject.py`** — recall the few most relevant recent memories and include them in the injected contract. Budget: 240 ms handshake is acceptable here, but hard-cap total added latency and degrade silently on timeout.
- [ ] **`hook_post_write.py`** — only on the **detached** branch (never the <100 ms fast path), record a terse observation for substantive edits that were accepted.
- [ ] Do **not** add memory writes to `hook_pre_write.py` — it is latency-critical and has nothing durable to say.
- [ ] Tests for each, with the client stubbed.
- [ ] Commit.

### Task 6: Move hook scripts to `FLOSS/hooks/` (LAST)

- [ ] `git mv` the four scripts (plus `agentmemory_client.py` if not already there) from `scripts/` to `hooks/`.
- [ ] Update `hook_scripts` paths in `shared-hook-surface.json`.
- [ ] Fix any internal imports/paths (`hook_post_write` spawns `hook_bg_round` by path — verify).
- [ ] Regenerate every projection; confirm no config still references `scripts/hook_`.
- [ ] Grep the whole workspace for stale `scripts/hook_` references, including outside the repo.
- [ ] Commit.

### Task 7: Trigger-verification (the operator asked for this explicitly)

Regenerating and inspecting is not enough — prove each hook actually fires.

- [ ] **Claude:** already proven this session (`~/.floss_agent/hook.log` shows pre/post entries from live edits). Capture a fresh log line as evidence.
- [ ] **Codex:** trigger a real file write through Codex and confirm a corresponding `hook.log` entry appears.
- [ ] **Hermes:** trigger a real tool call through Hermes and confirm the hook fires; note that this needs the allowlist approval or `hooks_auto_accept`.
- [ ] For each: record the actual log evidence in the report. A hook that is configured but does not fire is a failure of this task.
- [ ] Document the re-approval steps the operator must take after the Task 6 move (Codex re-trust, Hermes re-approve).

---

## Done when

- `python FLOSS/scripts/refresh_agent_surfaces.py --check` exits 0, all steps clean.
- Codex and Hermes hooks are generated from the manifest, not hand-maintained.
- Each of the three harnesses has a captured log line proving its hook fired.
- Consensus outcomes land in agentmemory automatically.
- No config anywhere references `FLOSS/scripts/hook_`.

## Operator notes

- After Task 6, **Codex will require re-trusting** its three hooks and **Hermes will require re-approving** its shell hooks (mtime changed). This is one deliberate event, not a bug.
- Hermes `hooks_auto_accept` is `false` and a non-TTY gateway cannot prompt. Approve once at a TTY, or flip that setting knowingly — it is a security control and this plan does not flip it for you.
