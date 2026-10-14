---
name: session-history
description: Show what happened in recent past sessions on this project as a clean timeline. Use when the user asks "what did we do last time", "session history", "past sessions", or wants an overview of previous work.
user-invocable: true
---

The user wants an overview of recent sessions on this project.

## Quick start

```json
memory_sessions { "limit": 20 }
```

Expected output:

```text
7f3a9c2 · app · 2026-06-07 09:00 · completed · 14 obs
  - decision: Rotate refresh tokens on every use
b21d004 · app · 2026-06-05 14:00 · completed · 9 obs
  - code: limit.ts counts per-IP
```

## Why

Only show sessions and observations the tool returned. An empty history is a
real answer, never a cue to invent past work.

## Workflow

1. Call `memory_sessions` with `limit: 20` for a meaningful window.
2. Present in reverse chronological order: session id (first 8), project, start
   time, status.
3. For sessions with observations, show the key highlights (type plus title).
4. Note the total observation count per session.
5. When a session summary exists, surface its title and the key decisions.

## Anti-patterns

WRONG: the tool returns two sessions, you describe "several sessions of steady
progress" and add ones you remember from the conversation.

RIGHT: show exactly the two sessions returned, each with its real id, status, and
observation count.

## Checklist

- Every session shown came from the tool response.
- Order is reverse-chronological.
- Per-session observation counts match the response.
- No session or highlight was invented or merged.

## See also

- `recall`: search across all sessions by topic.
- `recap`, `handoff`: same underlying data (grouped-by-date rollup / jump to
  most-recent), shipped in the upstream plugin but not yet ported into this
  corpus — ask if you want them added.

## Troubleshooting

**"MCP tool not available":** confirm the `agentmemory` plugin/MCP server is
enabled for this host and that the host was restarted after install (the MCP
shim registers at startup only). Check the host's MCP status view for a live
`agentmemory` connection.

**REST fallback:** if the daemon is running but MCP tools aren't reachable,
call `GET http://localhost:3111/agentmemory/session/start` or the sessions
listing endpoint directly (add `Authorization: Bearer $AGENTMEMORY_SECRET`
only if that env var is set).

## Provenance

Original skill: `rohitg00/agentmemory` plugin, `plugin/skills/session-history`
(v0.9.28, Apache-2.0). Ported into `FLOSS/skill-corpus/` unchanged apart from
this note and an inlined troubleshooting block in place of the upstream
`../_shared/TROUBLESHOOTING.md` cross-file reference. Not to be confused with
`session-report` (already in this corpus), which is a Claude-Code-specific
token-usage/spend retrospective — different data source, different purpose.
