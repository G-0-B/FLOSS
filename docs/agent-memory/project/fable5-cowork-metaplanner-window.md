---
id: project-fable5-cowork-metaplanner-window
type: project
created: '2026-06-12'
status: active
applies_to:
- any-agent
title: Fable-5 access restored (2026-07-03); sprint executed; post-window escalation policy now governs
---

## UPDATE 2026-07-04 — access RESTORED; second window executed and closed cleanly

**Fable 5 access returned:** `claude-fable-5` was directly invocable in Claude
Code on 2026-07-03/04 and executed the full **Fable 5 sprint** (packet
`docs/superpowers/plans/2026-07-03-fable5-sprint-handoff.md`): WS0 repo
verification, 90 eval items + 52 Pioneer seed, VOTER_PROMPT v2 (measured
20%→65%), 10-finding adversarial review, post-window voter profile, ADR-17.
Subscription access ends **~2026-07-09**, then pay-per-credit.

**Post-window is no longer improvised — it is policy:** successor
adversarial/verification role = `omo-critic` on `cerebras/gpt-oss-120b`
(`post-window` profile, live-validated 2026-07-04 with zero Fable calls);
Fable 5 credits spend only on escalation triggers E1–E5 per
`docs/superpowers/plans/2026-07-fable5-sprint-ws5-successor-policy.md`
(weekly budget number pending Anthony). This window was used exactly as the
durable principle below prescribes: compile-time artifact extraction on the
capable surface, execution structured for cheaper ones.

## UPDATE 2026-06-13 — window closed early by external event (superseded 2026-07-04)

**US government action caused Anthropic to pull back public Fable 5 access; it is
on hold "for now" (Anthony, 2026-06-13).** The "until 2026-06-22" Fable window
below is therefore **moot** — Fable-as-metaplanner is unavailable ahead of
schedule, not on the planned date.

**What survives (the durable principle, Fable-independent):** put planning
leverage on the most capable *available* surface and delegate execution to a
cheaper-per-task one. Concretely now:
- **Cowork (running Opus-class, 2× usage limits)** = the metaplanner /
  orchestration-manager surface — plans of action, delegation packets, outreach
  (it is actively running the OpenHuman/TinyHumans outreach thread, see
  [[project-continuation-artifact-map-2026-06-12]] and the 2026-06-13 Cowork
  continuation packet at workspace root).
- **Claude Code (Opus-class)** = high-rigor executor (it landed the 2026-06-12
  alignment pass + the PR #36 review fixes).
The token-economics logic is unchanged; only the Fable model is gone.

**Don't act out of scarcity.** Anthony's framing: "everyone needs to stop acting
out of fear and start acting out of love." The pullback is a constraint to route
around, not a reason to rush sloppy work. Keep the verify-before-claim discipline
(it caught a wrong "critical" bot fix on PR #36).

---

## Original directive (2026-06-12) — preserved; Fable specifics now moot

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
