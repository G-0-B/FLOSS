---
name: remember
description: Save a tight cross-session handoff note to .remember/remember.md so the next session — same agent or different — picks up cleanly. Use at the end of a working session, before context compaction, or whenever the user says to remember state for next time.
---

# Remember — Cross-Session Handoff Note

Write a forward-looking handoff note. Use your knowledge of this session — you were here. Write in first person ("I").

## Where to write

**FLOSSI0ULLK workspace path:** `C:\~shit\.remember\remember.md` (overwrite).

Why this path: `C:\~shit\` is the workspace root that every FLOSSI0ULLK harness (Claude Code, Codex, Gemini CLI, OpenCode, Vibe) sees. Writing here means *any* next session — not just same-harness — finds the handoff. The `.remember/` dir is conventional across the marketplace skill ecosystem.

If the workspace root is different (you're working in a separate FLOSSI0ULLK-derived repo), write to `{workspace_root}/.remember/remember.md`.

## Format

```
# Handoff

## State
{What's done, what's not. Files, commits, decisions. 2-4 lines max.}

## Next
{What to pick up. Priority order. 1-3 items.}

## Context
{Non-obvious gotchas, blockers, preferences from this session. Skip if nothing.}
```

## Rules

- Under 20 lines total
- Specific: file paths, commit SHAs, branch names, MR numbers
- Forward-looking — the next session doesn't care about the journey
- Cite provenance packets when state was published (`E<digest>` short refs are fine)
- If nothing meaningful to hand off, write: "No active work."
- If a Phase 2/3/4-style resumption packet already exists, reference its path rather than duplicating its contents

## Boundary

- This is *cross-session* memory. For mid-session task tracking, use TaskCreate.
- For durable cross-conversation memory (user preferences, project facts), use `FLOSS/docs/agent-memory/`, not this handoff.
- For load-bearing claims that need consensus or substrate validation, emit a provenance packet via `packages/activity_log/provenance.py` and then reference it here.

## After writing

Say "Saved." when done — nothing else. Do not narrate.

## Provenance

Original skill: `claude-plugins-official/remember` (v0.5.0). Adapted for FLOSSI0ULLK: workspace root pinned to `C:\~shit\`, provenance-packet integration noted, boundary with TaskCreate + agent-memory + provenance packets clarified.
