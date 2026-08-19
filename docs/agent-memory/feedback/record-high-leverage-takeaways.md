---
id: feedback-record-high-leverage-takeaways
type: feedback
created: '2026-05-19'
status: active
applies_to:
- any-agent
title: Always record high-leverage takeaways with provenance — co-learn with future selves and others
description: User explicit standing rule 2026-05-19. Anytime a session surfaces a learning, pattern, anti-pattern, or generalizable rule, it MUST be captured durably with provenance so future selves + other agents + the broader collective can compound on it rather than re-learn it.
---

User explicit guidance 2026-05-19: *"anytime high leverage takeaways come up make sure it is recorded with provenence and etc somewhgere we sho8uld always be learning and sharing that learning to compound or colearning with our future selves and others"*

**Why:** The project's whole architectural premise is decentralized coordination across human/AI/synthetic agents over time. The user has 14+ months of consistent output relying on durable artifacts (per `feedback-durable-provenance-required.md`). Session-level learnings that don't land in canonical memory/research/ADR surfaces evaporate when the session ends — exactly the context-reset problem the user named in `user-context-reset-resonance.md`. The substrate's value compounds only when learnings compound. A non-recorded takeaway is the same shape as the doc-explosion failure mode: present but not findable, true but not reusable.

**How to apply:**

1. **Recognize high-leverage takeaways in-session.** Markers: a rule that generalizes beyond the immediate case ("X ≠ Y" patterns); an anti-pattern named and avoided; a calibration result that changes a default; a user-correction that sharpens a prior memory; a cross-agent drift event with a structural fix; a successful polycentric loop where the substrate caught something.

2. **Choose the right durable surface for each takeaway:**
   - **`FLOSS/docs/agent-memory/feedback/`** — user-guidance rules, working-style preferences, how-to-collaborate patterns
   - **`FLOSS/docs/agent-memory/project/`** — project-state facts (canon promotions, ADR landings, version bumps, hardware specs)
   - **`FLOSS/docs/agent-memory/user/`** — user-specific facts (worldview, foundational context)
   - **`FLOSS/docs/agent-memory/reference/`** — pointers (commands, prior iterations)
   - **`FLOSS/docs/research/`** — substantive analyses, alignment maps, architectural proposals (longer than a memory entry; one topic)
   - **`FLOSS/docs/adr/`** — decisions with cross-component consequences
   - **`FLOSS/docs/specs/`** — formal contracts that bind code/behavior
   - **Working-todo §I (rolling 30-day window)** — operational landings + consensus-claim hashes
   - **Consensus claim through the gateway** — when the takeaway is shared contextual state worth multi-voter validation; durable on source chain with hash provenance
   - **Activity log `.agent-surface/activity.jsonl`** — when the takeaway is operational (Action records)

3. **Always include provenance:**
   - WHEN: timestamp / session date
   - WHO: the agent that surfaced it; the user prompt that triggered it if applicable
   - WHY: motivation + the situation that produced it
   - CROSS-REFS: linked specs, ADRs, prior memory entries, consensus claim hashes

4. **Apply retroactively when discovered.** If reviewing prior work surfaces a takeaway that should have been captured at the time but wasn't, save it now with explicit "captured retroactively 20XX-XX-XX" provenance. The take-away is more important than perfect timestamps.

5. **Compound on prior takeaways, don't duplicate.** Before saving a new memory entry, search existing memory + working-todo §I + recent research docs for adjacent ones. If a prior entry exists, refine IT rather than create a new file. Duplicate memory entries fragment the signal the same way doc-explosion fragments architectural truth.

6. **Cross-agent visibility is non-negotiable.** Per `feedback-durable-provenance-required.md` and the agent-memory-as-shared-surface migration, memory entries live in the canonical `FLOSS/docs/agent-memory/` source and are materialized to Claude/Codex/Gemini/OpenCode/ChatGPT views. New entries MUST go to the canonical source, not the projected views, so other agents see them.

7. **Examples from the session that produced this memory (recent applications of this rule):**
   - "Installation ≠ adoption" rule emerged from 2026-05-19 demotion of ledger entry 0013 → captured in working-todo §I + consensus claim 019e412d (durable on source chain). Could additionally land as a project memory if it becomes a recurring class of correction; for now the consensus claim + INDEX.md row + ledger entry note are sufficient.
   - Adopt-tier-canon vs investigate-tier-inventory distinction within reuse-ledger → captured in refined `feedback-pressure-helps-drop-throttling-guards.md` memory + consensus claim 019e40f8.
   - Cross-agent alignment loop pattern (user flags → Codex executes → Claude integrates → consensus publishes) → captured in working-todo §I 2026-05-19 entry + claim 019e40c0. Could earn its own project memory entry if it recurs as a standing operational pattern.
