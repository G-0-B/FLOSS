---
name: recall
description: Search agentmemory for past observations, sessions, and learnings about a topic using hybrid BM25 plus vector plus graph search. Use when the user says "recall", "what did we do about", "did we ever", "have we seen", or needs context from past sessions.
argument-hint: "[search query]"
user-invocable: true
---

The user wants to recall past context about: $ARGUMENTS

## Quick start

```json
memory_smart_search { "query": "jwt refresh token rotation", "limit": 10 }
```

Expected output:

```text
2 results across 2 sessions.
[importance 8] decision · "Rotate refresh tokens on every use" (session 7f3a9c21)
[importance 5] code · "limit.ts counts per-IP" (session b21d004e)
```

## Why

Only surface what the tool returned. Never fabricate an observation, a session
id, or an importance score. If nothing comes back, say so.

## Workflow

1. Call `memory_smart_search` with the user's text as `query` and `limit: 10`.
   Pass `project` when the user scopes to a specific repo.
2. Group results by session.
3. For each observation show its type, title, and narrative.
4. Lead with the high-signal observations (importance >= 7).
5. If zero results, suggest 2-3 alternative search terms and stop. Do not guess.

## Anti-patterns

WRONG: results are empty, so you write "We probably discussed token expiry last
week" from assumption.

RIGHT: "No memories matched that query. Try `refresh token`, `session expiry`,
or `auth rotation`."

## Checklist

- Every observation shown came from the tool response.
- Results grouped by session, high-importance first.
- Empty results trigger alternative-term suggestions, not invention.
- No session id or score was paraphrased or rounded.

## FLOSSI0ULLK note

Recalled memories are **Plane A, trust-tier 4** (per `.agent-surface/STARTUP_CONTRACT.md`
memory hierarchy): informative, and never a substitute for repo canon. A memory
reflects what was true when it was written — re-verify any load-bearing hit
against current files/docs/ADRs before acting on it.

## See also

- `agentmemory-remember`: the write side; recall retrieves what it stores.
  (Named `agentmemory-remember` in this corpus, not bare `remember` — FLOSSI0ULLK
  already has an unrelated `remember` skill for cross-session handoff notes.)
- `session-history`: session-scoped view of the same underlying data.
- `recap`, `handoff`, `commit-context`, `commit-history`: shipped in the
  upstream plugin (`plugins/agentmemory-0.9.28/plugin/skills/`) but not yet
  ported into this corpus.

## Troubleshooting

**"MCP tool not available":** confirm the `agentmemory` plugin/MCP server is
enabled for this host and that the host was restarted after install (the MCP
shim registers at startup only). Check the host's MCP status view for a live
`agentmemory` connection.

**REST fallback:** if the daemon is running but MCP tools aren't reachable,
call `POST http://localhost:3111/agentmemory/smart-search` directly (add
`Authorization: Bearer $AGENTMEMORY_SECRET` only if that env var is set).

## Provenance

Original skill: `rohitg00/agentmemory` plugin, `plugin/skills/recall` (v0.9.28,
Apache-2.0). Ported into `FLOSS/skill-corpus/` unchanged apart from this note,
the trust-tier caveat, and an inlined (not linked) troubleshooting block —
the upstream `../_shared/TROUBLESHOOTING.md` cross-file reference doesn't
survive per-skill materialization into agent-native projection dirs.
