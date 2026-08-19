---
id: project-metaharness-doctrine
type: project
created: '2026-05-18'
status: active
applies_to:
- any-agent
source: legacy_claude_memory
legacy_filename: project_metaharness_doctrine.md
title: Six-harness metaharness operating doctrine
legacy_description: Canon/Context/Execution/Consensus/Reflection/Publish — the formal
  layering for composing FLOSSI0ULLK agent surfaces
origin_session_id: 567c823f-3cba-4d75-866d-600bd4286e6f
---

`FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md` (v0.1.0, status Active, 2026-04-17) defines the doctrine for composing all FLOSSI0ULLK harnesses. It is the policy layer, not another super-agent.

**Why:** Without it, multiple agents hand-edited generated views, premium tokens got burned on reviewer swarms, disagreement got flattened into fake consensus, and transient insights polluted canon.

**The six harnesses:**
1. **Canon** — shared truth via `shared-{agent,context,skill,hook}-surface.json` + ADRs/specs/architecture. Never hand-edit generated views; manifests are canonical.
2. **Context** — `scripts/context_router.py`, generated `CONTEXT_L0/L1.md`, Serena memories, portable skills. Route corpus first, then retrieve inside it.
3. **Execution** — Claude/Codex as primary editor, OpenCode secondary, Serena as understanding-substrate (not decider). One primary writer per concrete change set.
4. **Consensus** — `hook_pre_write.py` + `hook_post_write.py` + `hook_bg_round.py` + hashline pre/post-image verification + voter rosters across Groq/Cerebras/Mistral/Flowith. Cheap heterogeneous review first; escalate to premium only when blast radius justifies.
5. **Reflection** — `~/.floss_agent/hook.log` + traces/consensus/. Optimize harnesses, not weights.
6. **Publish** — Radicle first (dev-plane), GitHub second (mirror), Holochain later (runtime truth).

**Diversity policy:** nontrivial polls span ≥3 provider surfaces and ≥4 model families. Multiple endpoints of the same family ≠ independence. Preserve dissent and variance as signal.

**How to apply:**
- Don't propose "one omni-agent that carries every context" — the doctrine explicitly forbids it.
- Don't hand-edit `.agent-surface/agents/*` or other materialized views — find and edit the manifest.
- Don't promote transient insights into canon. Promotion needs evidence (consensus passes, traces, repeated work).
- When choosing voters/reviewers, check provider+family diversity before launching the round.
- For substantive edits, the loop is: route → load smallest L0/L1 view → choose one executor → land via materialized config → trigger hooks → cheap consensus → traces → promote only durables.

**Companion:** `AGENTIC_OPERATING_MODEL.md` (broader stack), `HOLISTIC_ARCHITECTURE.md` (macro), `CONTEXT_DAEMON_ARCHITECTURE.md` (compression doctrine), `2026-04-16-forward-momentum-radicle-meta-harnesses.md` (sequenced near-term work).
