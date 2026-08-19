---
name: claude-reflect
description: Self-learning capture system. Hooks detect correction patterns ("no, use X", "actually...", "use X not Y") and queue them; user runs /reflect to review and apply queued learnings to CLAUDE.md files. Use when the user mentions remembering something for future sessions, after a feature lands, or when context is about to compact with queued items.
---

# Claude Reflect — Self-Learning Capture

Two-stage system that helps Claude Code (and FLOSSI0ULLK harness-mates) learn from user corrections.

## How It Works

**Stage 1: Capture (Automatic via hooks)**
Hooks detect correction patterns and queue them to `~/.claude/learnings-queue.json`.

**Stage 2: Process (Manual via slash command)**
User runs `/reflect` to review and apply queued learnings to CLAUDE.md or `FLOSS/docs/agent-memory/` files.

## Source plugin

Full plugin (hooks, scripts, commands) is installed at:
`C:\Users\kalis\.claude\plugins\cache\claude-reflect-marketplace\claude-reflect\3.1.0\`

This skill projection just describes the user-facing surface; the actual capture loop runs inside Claude Code via the marketplace plugin. For cross-harness propagation (Codex, Gemini, OpenCode), upstream the capture pattern as a separate hook per harness — track as a meta-workflow follow-up.

## Available Commands

| Command | Purpose |
|---------|---------|
| `/reflect` | Process queued learnings with human review |
| `/reflect --scan-history` | Scan past sessions for missed learnings |
| `/reflect --dry-run` | Preview changes without applying |
| `/reflect-skills` | Discover skill candidates from repeating patterns |
| `/skip-reflect` | Discard all queued learnings |
| `/view-queue` | View pending learnings without processing |

## When to remind the user

- They complete a feature or meaningful work unit
- They make corrections you should remember for future sessions
- They explicitly say "remember this" or similar
- Context is about to compact and queue has items

## Correction detection patterns (what the hook watches for)

High-confidence:
- Tool rejections (user stops an action with guidance)
- "no, use X" / "don't use Y"
- "actually..." / "I meant..."
- "use X not Y" / "X instead of Y"
- "remember:" (explicit marker)

## Learning destinations

| Destination | Use for |
|---|---|
| `~/.claude/CLAUDE.md` | Global learnings (model names, general patterns) |
| `./CLAUDE.md` (project) | Project-specific learnings (conventions, tools, structure) |
| `./CLAUDE.local.md` | Personal learnings (machine-specific, gitignored) |
| `./.claude/rules/*.md` | Modular rules with optional path-scoping |
| `~/.claude/rules/*.md` | Global modular rules |
| `~/.claude/projects/<project>/memory/*.md` | Auto memory (low-confidence, exploratory) |
| `commands/*.md` | Skill improvements (corrections during skill execution) |

## FLOSSI0ULLK-specific destinations (additional to upstream)

Promote captured learnings to these surfaces when the learning is durable and cross-agent:

| Destination | Use for |
|---|---|
| `FLOSS/docs/agent-memory/feedback/*.md` | Cross-agent feedback memories (the canonical projection materializes to `.agent-surface/memory/AGENT_MEMORY.md`) |
| `FLOSS/docs/agent-memory/project/*.md` | Project-state memories that survive across sessions |
| `FLOSS/docs/agent-memory/user/*.md` | User profile / role / preferences |
| `FLOSS/CLAUDE.md` / workspace `CLAUDE.md` | Project orientation updates that need to ride at session start |
| `FLOSS/docs/research/<date>-<topic>.md` | When the learning is research-grade and load-bearing for multi-agent work |

For substrate-level decisions captured this way, prefer routing through the consensus gateway (`flossiullk-consensus` MCP) and emitting a provenance packet rather than overwriting CLAUDE.md silently.

## Example interaction

```
User: no, use gpt-5.1 not gpt-5 for reasoning tasks
[hook silently queues this to ~/.claude/learnings-queue.json]

(later, end of session)
You: I noticed a few corrections this session. Want to run /reflect to review?
User: /reflect
[command opens the queue, shows each candidate with proposed destination, asks for accept/edit/reject]
```

## Boundary

- This is **opportunistic capture** — it catches things the user said in passing.
- It is NOT a replacement for explicit memory writes via `FLOSS/docs/agent-memory/`.
- It is NOT a replacement for ADR updates when the correction is architectural.
- For correction tracking that needs cross-agent surface, materialize the learning into `FLOSS/docs/agent-memory/` (which the materializer projects out to all harnesses) rather than relying on a single harness's queue.

## Provenance

Original skill: `community/claude-reflect` v3.1.0. Adapted for FLOSSI0ULLK: added the `FLOSS/docs/agent-memory/*` destination table + the substrate-routing boundary so correction capture doesn't bypass consensus / provenance for load-bearing changes.
