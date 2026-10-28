---
name: forget
description: Delete specific observations from agentmemory after showing them and getting explicit confirmation. Use when the user says "forget this", "delete memory", "remove that note", or wants to scrub specific data for privacy.
argument-hint: "[what to forget - session ID, file path, or search term]"
user-invocable: true
---

The user wants to remove data from agentmemory: $ARGUMENTS

## Quick start

```json
memory_smart_search { "query": "old api key in config", "limit": 20 }
```

Show the matches, get a yes, then:

```json
memory_governance_delete { "memoryIds": ["abc12345", "def67890"], "reason": "user privacy request" }
```

Expected output:

```text
Found 2 matching memories. Confirmed. Deleted 2 memories.
```

## Why

This is destructive and irreversible. Show exactly what will be deleted and get
an explicit yes before calling delete. Delete by memory ID, never a bare session.

## Workflow

1. Search with `memory_smart_search`, the user's text as `query`, `limit: 20`.
2. Show what matched: session ids, memory ids, titles. Ask for explicit
   confirmation. Do not proceed on silence or a vague "sure, whatever".
3. On confirmation, call `memory_governance_delete` with `memoryIds` (array or
   comma-separated string) and optional `reason` (default `plugin skill request`).
4. To drop a whole session, collect every memory id in that session from the
   search results and pass them all. The MCP does not accept a bare `sessionId`.
5. Report the deletion count back.

## Anti-patterns

WRONG: search returns matches, you immediately call `memory_governance_delete`
without showing them or waiting for a yes.

RIGHT: list the matches, ask "Delete these 2? (yes/no)", and only delete after
an explicit yes.

## Checklist

- Matches were shown to the user before any delete.
- An explicit yes was received, not assumed.
- `memoryIds` holds real ids from the search, never a bare `sessionId`.
- Final message states the actual count deleted.

## See also

- `agentmemory-remember`: the write side; forget is its undo.
- `recall`: find the exact memory id before deleting.

## Troubleshooting

**"MCP tool not available":** confirm the `agentmemory` plugin/MCP server is
enabled for this host and that the host was restarted after install (the MCP
shim registers at startup only). Check the host's MCP status view for a live
`agentmemory` connection.

**`memory_governance_delete` specifically missing:** it's a governance/coordination
tool, gated behind the extended tool set (`AGENTMEMORY_TOOLS=all`). Some connected
surfaces expose only the core ~8-9 tools. If it's absent, say so plainly — do not
substitute a different delete path or claim the deletion happened.

**REST fallback:** if the daemon is running but MCP tools aren't reachable,
search via `POST http://localhost:3111/agentmemory/smart-search`; there is no
documented REST delete endpoint in the base surface — treat REST-only hosts as
search/save/list only until confirmed otherwise.

## Provenance

Original skill: `rohitg00/agentmemory` plugin, `plugin/skills/forget` (v0.9.28,
Apache-2.0). Ported into `FLOSS/skill-corpus/` with the `remember` cross-ref
renamed to `agentmemory-remember` (see that skill's naming note), an added
caveat about `memory_governance_delete` availability varying by connected
surface, and an inlined troubleshooting block in place of the upstream
`../_shared/TROUBLESHOOTING.md` cross-file reference.
