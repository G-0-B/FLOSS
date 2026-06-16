---
id: project-januscope-wired
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_januscope_wired.md
title: JanuScope wired in front of both MCP servers
legacy_description: Local MCP policy proxy (giancarloerra/JanuScope v0.4.2) wraps
  the consensus gateway and Serena MCPs via stdio child-process pattern. Adds audit
  logging + instruction injection at the JSON-RPC layer. AGPL-3.0 compatible with
  ADR-7. Takes effect on next Claude Code session start.
origin_session_id: e871691c-2013-4bde-b604-e6c52730ed65
---

## What's wired

`C:/~shit/.mcp.json` now launches both MCP servers via `npx -y januscope@latest --config <lens.yaml>` instead of directly. Lens configs live at `C:/~shit/.mcp/lenses/`:

| MCP | Lens | Adds |
|---|---|---|
| `flossiullk-consensus` (our gateway) | `flossiullk-consensus.yaml` | Audit logging to `.agent-surface/heartbeat/janus-consensus-audit.jsonl` + ~900-char instruction injection (analog-vote/passive-router/blast-radius/CONFLICT invariants) |
| `serena` (LSP code intelligence) | `serena.yaml` | Audit to `.agent-surface/heartbeat/janus-serena-audit.jsonl` + symbol-aware-preferred operational heuristics |

Pre-JanuScope `.mcp.json` preserved at `C:/~shit/.mcp.json.pre-januscope.bak`.

## What JanuScope does (relevant subset for our wiring)

- **stdio child-process proxy**: Claude Code → JanuScope → real MCP server. Pure JSON-RPC pass-through with policy overlays. No daemon, no port, no persistent state beyond optional audit JSONL.
- **`instructions`**: appends policy text to every tool's description. LLM sees the invariants without re-deriving them from cold context.
- **`audit`**: JSONL log of every tool call (defense-in-depth observability — the gateway already writes claims/votes/decisions to the source chain; this gives us a second observer at the transport layer).
- Other overlays unused in our lenses for now: `block` (filter tool names), `sqlGuard` (reject SQL mutations), `redact` (regex/field-path PII scrubbing), `dbSchema` (pre-inject DB metadata into tool descriptions — this is where the documented "84% token reduction" comes from, but only applies to DB-backed MCPs which we don't have yet).

## When we add DB-backed MCPs

JanuScope's marquee feature (84% token reduction on DB MCPs via schema pre-injection) is queued for whenever we wire up Postgres/MySQL/Mongo MCPs. The pattern is established; lens templates ship with JanuScope as bundled lenses (`januscope lenses list`).

## License + ADR-7 status

AGPL-3.0-only (open source) OR commercial license available. AGPL-3.0 is ADR-7-compatible (matches our copyleft cascade stance).

## Activation

Takes effect on **next Claude Code session start**. Current session continues with pre-JanuScope MCP launches (no disruption to in-flight work).

## How to inspect / verify

- View audit logs: `cat C:/~shit/.agent-surface/heartbeat/janus-{consensus,serena}-audit.jsonl`
- Bundled lens library: `npx -y januscope@latest lenses list`
- Roll back: `cp C:/~shit/.mcp.json.pre-januscope.bak C:/~shit/.mcp.json`
- Bypass for one session: edit `.mcp.json` to point directly at the original `command`
