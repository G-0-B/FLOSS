---
id: project-fable5-cowork-metaplanner-window
type: project
created: '2026-06-12'
status: active
applies_to:
- any-agent
title: Cowork (Fable 5) is the master metaplanner until 2026-06-22; Claude Code (Opus) executes
---

Anthony's directive (2026-06-12): **Cowork is the primary Fable 5
agent-orchestration-manager** — the "master overarching metaplanner" that
authors plans of action and delegation structures, which Claude Code sessions
running Opus-class models then execute. Rationale: Anthropic gives **2× usage
limits via Cowork**, and Fable 5 consumes **2× normal tokens** — so the
expensive model's leverage goes into planning, the cheaper executors into
doing.

**Hard deadline: Fable 5 plan access ends 2026-06-22.** After that Anthropic
moves it to paid credits only. Anthony is maximizing the window "to cultivate
flossioullks as much as possible."

**Why:** Token economics decide surface assignment, not preference. The same
session-limit failures that killed two workflow analysts on 2026-06-12 showed
subagent fan-out from Fable 5 is doubly expensive — inline work or delegated
execution is the pattern.

**How to apply:**
- In Cowork/Fable 5 sessions: bias toward plans, specs, delegation packets,
  and decision records that a cheaper executor can run cold. Avoid burning
  Fable 5 on mechanical edits or broad subagent fan-outs.
- In Claude Code/Opus sessions: look for Cowork-authored plans (working todo,
  docs/superpowers/plans/, continuation packets) before improvising.
- After 2026-06-22: re-evaluate — this doctrine is window-scoped, not
  permanent. See [[project-continuation-artifact-map-2026-06-12]] for the
  alignment-pass context it landed in.
- Doctrine is also recorded in FLOSS/CLAUDE.md "Inference Posture".
