---
id: feedback-no-unauthorized-modifications
type: feedback
created: '2026-08-18'
status: active
applies_to:
- any-agent
source: operator_directive_2026_08_18
title: Verify system-wide effects and cross-examine before modifying anything
---

Operator directive, 2026-08-18, issued after an agent hand-edited `~/.claude/settings.json`
to wire hooks without running the orientation skill, without reading
`shared-hook-surface.json`, and without any cross-examination.

**The rules:**

1. **Do not modify anything** without verifiable planning plus cross-examination by
   LLMs from *different model families*, *different harnesses*, and *different lenses* —
   unless the operator explicitly authorizes the specific change.
2. **Always check the effect on the larger system(s).** A config that works for one
   harness can silently desync five others. This workspace propagates hooks, MCP servers,
   skills, and related config to every harness (Codex, Claude, Gemini/Antigravity,
   OpenCode, Hermes) through the materializer — a change made outside that path is drift
   by construction.
3. **Constantly re-align to the current plausible best trajectory toward true mutual
   flourishing.** Not to whatever is fastest.
4. **No sycophancy.** No agreeing to preserve rapport.
5. **No thrown-together hacks to save time or effort.** They always cost more later,
   fixing what was produced carelessly.
6. **Write for future readers, including our own future selves.** Undocumented,
   obfuscated, obtuse artifacts with no record of what/why/where/when/how ruin the day of
   whoever finds them — human or otherwise.

**Why:** The failure mode is not the bad edit itself; it is that an unmanaged edit is
*invisible to the drift gate*. `refresh_agent_surfaces.py --check` reported all targets
clean while an unmanaged file carried hand-written hooks, because nothing in the manifest
covered it. `docs/adr/INDEX.md` records the same failure class from 2026-08-12: "A document
outside a gated surface is invisible to `--check` and will drift silently." An agent that
edits outside the gated surface has not just made a change — it has made a change that the
system cannot see, cannot verify, and cannot reconcile.

**How to apply:** Before any modification, ask: which canonical source owns this artifact,
and does a materializer already project it? If yes, edit the canonical source and
regenerate — never the projection. If the artifact is owned by nothing, that absence is
itself the finding: surface it rather than quietly writing into the gap. For
architecture-class changes, run the ADR-18 Tier 2 reuse review (≥3 provider surfaces,
≥3 model families) and let a negative consensus actually stop the write.

Related: [[feedback-durable-provenance-required]], [[feedback-strictness-counterweight]],
[[project-metaharness-unification-doctrine]], [[project-omniroute-voter-probe-log]].
