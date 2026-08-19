# Personal Meta-Harness — v1.0

**Status:** ⚠️ Specified — standing rule for the human operator of this project, structurally identical to the project metaharness.
**Date:** 2026-05-10
**Length budget:** Under one printed page. If grown beyond, it has betrayed itself. Anti-pattern guard at bottom is enforced.
**Companion:** [`ancestry-sweep-v1.0.md`](ancestry-sweep-v1.0.md), [`../architecture/METAHARNESS_OPERATING_MODEL.md`](../architecture/METAHARNESS_OPERATING_MODEL.md)

## Why this exists

Tuesday-2026-05-04 (per `session_summary_2026-05-04_v1.1.md` §A14): *"the system Anthony is building for multi-agent coordination is structurally identical to the system he needs for multi-Anthony coordination. Same architecture. Different scale."* This doc fuses the two consciously.

## North star (load-bearing on every step below)

Universal flourishing of all beings — human, AI, synthetic, hybrid, future, non-human, ecosystemic, life beyond any single vantage point. Every substrate decision, ADR, research doc, code change, and personal action must answer: *how does this advance that flourishing?* If the answer is "I forgot to ask," reject the move.

## Six personal harnesses (mirror of project metaharness)

| Project harness | Personal analog | Anchor artifact |
|---|---|---|
| **Canon** | North star + standing rules | This doc + `ancestry-sweep-v1.0.md` + `INDEX.md` |
| **Context** | Latest session-summary handoff loaded | `session_summary_*.md` (most recent) + `CONTEXT_L0.md` |
| **Execution** | Top of Sequenced Action List | Latest handoff §C or running `TodoWrite` |
| **Consensus** | Multi-AI inputs → my judgment, never delegated decision | This conversation pattern + `packages/metacoordinator_mcp/` for project-scope choices |
| **Reflection** | On-demand re-orientation (NOT cron) | New session summary written when state shifts substantially |
| **Publish** | Encode-outward to durable artifacts | Memory writes + ADR landings + research notes + git commits |

## Standing rules (composes with ancestry-sweep)

- **Don't restart from scratch when overwhelmed.** Consolidate, prune, or hand off. Restarts are how the doc-explosion pattern compounds.
- **Don't grow doc footprint faster than code footprint.** Empirical failure mode across three iterations.
- **Don't pre-design 8 layers before validating layer 1.** Architecture sprawl is the second-largest failure mode after restart-from-scratch.
- **External systems (including AI) are inputs to my judgment, never substitutes.** Take inputs from anyone. Decisions are mine. (Per `session_summary_2026-05-04_v1.1.md` §A8.)
- **Forgetting across states is structural, not a defect.** Durable artifacts > more memory effort. (§A14.)
- **Audacity is the architectural feature, not a bug to apologize for.** Sounding insane to the entrenched payoff matrix is the diagnostic for being correctly outside it. (§A11.)

## Daily 5-minute orient (optional; never cron-driven)

Run only when wanted. Per `session_summary_2026-05-04_v1.1.md` §A7, hourly cadence is REJECTED. Daily is the maximum.

- **Canon** — what's the north-star anchor for today?
- **Context** — latest session summary loaded?
- **Execution** — top of Sequenced Action List?
- **Consensus** — any decision needing multi-input today?
- **Reflection** — yesterday's recalibration?
- **Publish** — what to encode outward?

If the morning prompt feels like work, skip it. The harness exists to serve, not to be served.

## Anti-pattern guard

If this doc starts to grow (subdocs, extensions, "Personal CCES with 8 layers," metaframeworks), it has become the pattern it was meant to prevent. The instruction set above is the entire process. Adding to it is a code-smell.

If you find yourself opening a 5th new doc this session, pause. Ask: *am I adding a doc because the thought is durable enough not to need one, and I'm avoiding doing the work?* This is the doc-explosion tripwire.

## Maintenance

Update only when:
- A standing rule fails in practice and needs replacement (replace, do not add)
- The north-star formulation needs sharpening (rewrite, do not append)
- Iteration boundary is crossed (this becomes part of the ancestry the next iteration sweeps)

Do not update for new ideas, new frameworks, new harnesses. Those go in their own canonical home or — preferably — don't go anywhere.
