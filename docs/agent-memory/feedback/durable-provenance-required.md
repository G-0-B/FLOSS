---
id: feedback-durable-provenance-required
type: feedback
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: feedback_durable_provenance_required.md
title: Provenance must be permanent, not just response-trail
legacy_description: Response-trail logging is for the current session only. Durable
  provenance lives in append-only artifacts that survive across sessions and agents
  — activity logs, ledger entries, working-todo §I, memory files, ADRs. Future agents
  reconstruct context from those artifacts, not from chat transcripts.
origin_session_id: a04c9df9-7bf3-4c48-8305-871bc29b680d
---

User explicit guidance 2026-05-17: *"i wanted the provenence not just loggged and shown to the user currently, but also permanently logged in the record of actions for fuuturee agents(me, you, every other one) but wee always need to be logging extending our contextual continuation artifacts/records."*

**Why:** The whole FLOSSI0ULLK architecture is built around the principle that *the conversation is the coordination protocol* (ADR-0 Recognition Protocol) — but only if the conversation is captured into durable artifacts that future agents can read cold. Chat transcripts are not durable substrate for cross-agent continuation. Future Claude sessions, Gemini, Codex, human steward, hybrid forms — none of them can read THIS chat. They can read filesystem artifacts. The whole continuation-packet pattern (CONTEXT_CONTINUATION_PACKET_*.md), MEMORY.md, working-todo §I, ADR Suite, source chain entries, activity.jsonl — these exist precisely because response-trail-only logging fails the externalization test.

**How to apply:**
- **For every meaningful action, ask: where does this land that a future cold-start agent can read?** If the answer is "only in the chat response," that's incomplete. Add: an activity log line, a working-todo §I entry, a ledger gate update, a memory file, an ADR if architectural, a provenance JSON sidecar — whatever fits the action shape.
- **Use the existing externalization surfaces first; don't invent new ones.** Per doc-budget discipline + intake-mouth convention. The patterns already in place:
  - **Activity logs** — `.agent-surface/<surface>/activity.jsonl` for streaming events
  - **Working-todo §I** — rolling 30-day human-readable summary of completions
  - **Memory files** — `~/.claude/projects/C---shit/memory/<type>_<topic>.md` for cross-session persistence
  - **Ledger entries** — for component-level provenance (reuse-ledger, ADR-Suite)
  - **Provenance sidecars** — JSON next to artifacts (`<file>.provenance.json`)
  - **Source chain** — `~/.floss_agent/cells/<dna>/source_chain/` for consensus-validated claims
  - **Continuation packets** — `CONTEXT_CONTINUATION_PACKET_<date>_<descriptor>.md` for major handoffs
- **Cross-reference the artifacts at WRITE time.** When updating working-todo §I, name the file paths. When writing an activity log line, include the staging draft path. When saving a memory, point at the working-todo entry. Future agents follow these links to reconstruct.
- **Inline provenance in the response trail is still valuable** — that's how the user-in-flight gets visibility. The rule is BOTH-AND, not either-or: response trail for current visibility, durable artifacts for cross-agent continuation.
- **Trust the existing pattern. Don't re-invent.** The activity.jsonl pattern I added to harvest_reuse_ledger.py 2026-05-17 is the canonical shape for this kind of streaming-event log. Future surfaces should follow the same shape: append-only, JSON-Lines, one event per line, timestamp + event-type + context fields. Compatible with `jq`/`grep`/`tail -f`, indexable later if needed.
