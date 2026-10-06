---
name: agentmemory-remember
description: Save an insight, decision, or learning to agentmemory's long-term storage with searchable concept tags. Use when the user says "remember this in agentmemory", "save this to memory", "note that" (in a memory context), or wants to preserve knowledge for future sessions via the memory MCP. Distinct from the cross-session handoff `remember` skill.
argument-hint: "[what to remember]"
user-invocable: true
---

The user wants to save this to long-term memory: $ARGUMENTS

## Quick start

> **STOP — do not copy the shape below as literal arguments.** It is a schema
> illustration with placeholder text, NOT a call to make. Every field must be
> filled from the actual conversation you are in. This has gone wrong: on
> 2026-07-26 an agent saved a previous version of this example verbatim (a JWT
> refresh-token fact about a file that does not exist in this workspace) as
> real project knowledge, then reported success. It had to be deleted.

```json
memory_save {
  "content": "<the actual insight, in the user's own phrasing, from THIS conversation>",
  "concepts": "<2-5 specific lowercased phrases that would retrieve it later>",
  "files": "<real repo-relative paths you actually touched, or omit>"
}
```

**Before calling:** name, out loud, which turn of the conversation the content
came from. If you cannot point at one, you have nothing to save — say so
instead of calling the tool.

**After calling:** read the response back. Confirm `concepts` is non-empty and
matches what you intended, and that `content` is your text rather than markup
or a truncated fragment. A malformed save is unretrievable and silently
useless.

## Why

A memory is only as useful as the terms that retrieve it. Tag with specific
concepts so a future `recall` finds it, and preserve the user's own phrasing.

## Workflow

1. Pull the core insight, decision, or fact out of `$ARGUMENTS`.
2. Extract 2-5 lowercased concept phrases. Prefer specific over generic
   (`consensus-gate-thresholds` beats `governance`).
3. Extract referenced file paths (absolute or repo-relative). Empty if none.
4. Call `memory_save` with `content`, `concepts` (comma-separated string), and
   `files` (comma-separated string).
5. Confirm the save and echo the concepts so the user knows the retrieval terms.

## Anti-patterns

WRONG: `concepts: "stuff, code, notes"` (generic tags nothing can find later).

RIGHT: `concepts: "consensus-gate-thresholds, analog-vote-weights"` (specific, retrievable).

WRONG: saving any example text from this file, or from any other skill's docs,
as though it were project knowledge. If the content you are about to save also
appears in a skill's markdown, you are copying an illustration — stop.

WRONG: saving because you were asked to "remember this" but the conversation
was compressed or you cannot locate the actual insight. Report that you have
nothing concrete to save. An empty result is recoverable; a fabricated memory
poisons every future recall and must be hunted down and deleted.

## Checklist

- Content preserves the user's phrasing, not a paraphrase.
- Concepts are specific, lowercased, 2-5 items.
- File paths are real references, not guesses.
- Confirmation echoes the exact concepts tagged.

## FLOSSI0ULLK note — naming and scope

This skill is named `agentmemory-remember`, not bare `remember`, because this
corpus already has a `remember` skill (cross-session handoff note written to
`.remember/remember.md` — no MCP call, just a markdown file). The two solve
different problems:

| | `remember` (existing) | `agentmemory-remember` (this skill) |
|---|---|---|
| Target | `.remember/remember.md` file | agentmemory long-term store (via `memory_save`) |
| Scope | Cross-*session* handoff, forward-looking, <20 lines | Durable, searchable insight/decision/pattern |
| Retrieval | Next session reads the file directly | Future `recall` / `memory_smart_search` |

**Plane A only:** a saved memory is a recall candidate, not canon. If what
you're saving is load-bearing (an architecture decision, a contract change),
promote it to an ADR or spec through the normal gate — don't treat this save
as sufficient on its own. Never save secrets, keys, or unredacted sensitive data.

## See also

- `recall`: retrieve what you save here (the pair to this skill).
- `forget`: remove a memory you saved by mistake.
- `remember`: the unrelated cross-session handoff-note skill — see table above.

## Troubleshooting

**"MCP tool not available":** confirm the `agentmemory` plugin/MCP server is
enabled for this host and that the host was restarted after install (the MCP
shim registers at startup only). Check the host's MCP status view for a live
`agentmemory` connection.

**REST fallback:** if the daemon is running but MCP tools aren't reachable,
call `POST http://localhost:3111/agentmemory/remember` directly (add
`Authorization: Bearer $AGENTMEMORY_SECRET` only if that env var is set).

## Provenance

Original skill: `rohitg00/agentmemory` plugin, `plugin/skills/remember`
(v0.9.28, Apache-2.0), renamed `agentmemory-remember` to avoid colliding with
FLOSSI0ULLK's pre-existing `remember` handoff-note skill. Ported unchanged
otherwise apart from this note and an inlined troubleshooting block (the
upstream `../_shared/TROUBLESHOOTING.md` cross-file reference doesn't survive
per-skill materialization).
