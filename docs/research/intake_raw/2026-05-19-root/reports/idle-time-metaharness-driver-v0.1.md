# Idle-Time Metaharness Driver (ITMD) v0.1 — Design Spec

```yaml
id: idle-time-metaharness-driver
version: "0.1.0"
kind: design_spec
status: Draft
truth_status: ⚠️ Specified — design only; not yet built or piloted
date: 2026-05-07
project: FLOSSI0ULLK
canonical_path_proposal: FLOSS/docs/research/idle-time-metaharness-driver-v0.1.md
adr_promotion_target: ADR-12 (or next available) — pending pilot results
referenced_by:
  - strategic-context-memo-ecosystem-signals-v0.1.md (action items #1–#7 are seed work)
  - re-bicameralization_integration_brief_v1.0.md (NK-AD-001 binds this design)
references:
  - FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md (six-harness composition)
  - FLOSS/docs/architecture/AGENTIC_OPERATING_MODEL.md
  - FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md
  - FLOSS/docs/superpowers/specs/2026-04-12-local-agent-node-design.md (Layer 4.5 — ✅ Verified)
  - FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md
  - FLOSS/scripts/watch_intake.py
  - FLOSS/scripts/process_intake_events.py
  - FLOSS/scripts/autonomous_synthesis_loop.py
  - FLOSSI0ULLK-Architecture-Spec-v0.1 §5 (control loop), §6.3 (Claim Truth Model), §7 (Seam priority)
  - Project-Spine-FLOSSIOULLK_v0.5 §5 (Plane A/B boundary), §7 (provenance packet), §10 (ACI), §3.2 (friction tiers)
  - ADR-Suite v2.0 (hand-verified 2026-04-26) — voter roster, analog vote model
  - re-bicameralization brief NK-AD-001 (autoprompt-divergence invariant)
intake_doctrine: filter-through-not-out
classification: orchestration_overlay
```

---

## 0. One-line summary

A heartbeat-driven driver that wakes on a cadence, generates Claim drafts from a leverage-ranked backlog, dispatches them through the existing ✅ Verified Layer 4.5 consensus gateway to Cerebras / Groq / Mistral / Flowith (and optionally Claude / Gemini / Codex via separate channels), collects outputs into a human-review queue under explicit cost caps and ACI blast-radius limits, and continuously regenerates a single resumption page so the human steward can triage everything that happened while away in one read.

---

## 1. Problem Statement

| Item | Status |
|---|---|
| Subscription compute available | Cerebras (free tier), Groq (free tier), Mistral (paid), Flowith (?), Claude Pro (Opus 4.7 + 1M context + xhigh effort), Codex CLI, Gemini |
| Compute actually consumed when human is absent | ≈0% — system waits for typed prompts |
| Loss | Subscription spend burns whether used or not; free tier quotas reset daily whether used or not; the `autonomous_synthesis_loop.py` exists but is not driven on a cadence |
| What's missing | An active producer in front of the passive Layer 4.5 router that generates Claims when no human is typing |

**Goal:** make the system run continuously against a backlog when no human is present, while preserving every existing FLOSSI0ULLK invariant.

**Non-goal:** automating the human steward out of the loop. The control loop's Step 1 (clarify intent), Step 7 (promote to ADR), and the −1 veto in Step 4 stay human (per Architecture Spec §5).

---

## 2. Hard Constraints (Non-negotiable)

These are inherited from existing canon. Violating any one of them invalidates this design.

| ID | Constraint | Source |
|---|---|---|
| C1 | Loop output never substitutes for the user's voice. No external messages, no edits to canon, no PR/issue comments as user. | NK-AD-001 (re-bicameralization brief) |
| C2 | Loop publishes only to a Plane A review queue. Promotion to Plane B canon requires human steward gate. | Spine v0.5 §5 (authority boundary) |
| C3 | Loop respects ACI blast-radius tiers. Read / search / test / draft / propose-ADR allowed. Merge / push / send / modify-canon disallowed without explicit approval + CI proof. | Spine v0.5 §10.2 |
| C4 | Loop output classified Verified-External vs Specified-Internal vs Aspirational. No auto-promotion across the line. | Strategic context memo §1 (forbidden-promotion rule) |
| C5 | Layer 4.5 gateway remains a passive router. ITMD is producer-side only. Gateway logic is unchanged. | ADR-10 v2.0 |
| C6 | Symbolic First. Loop output is *neural assistance*; symbolic validators decide what is true. The driver does not bypass validation. | Prime directive |
| C7 | Single STOP file (`.agent-surface/heartbeat/STOP`) halts all loops within one cycle. No exceptions. No flags, no overrides, no "important task in flight" delays. | New (this spec) |
| C8 | Per-provider daily token / request budget. Halt-that-provider on cap. Never spend over cap. | New (this spec) — required for non-coercion of user attention later |
| C9 | Phase 0 substrate viability tasks (Rose Forest compile, Tryorama scenarios, ConversationMemory↔MultiScaleEmbedding, ADR-0 Test #4) outrank all other backlog items until Phase 0 exits. | CLAUDE.md / AGENTS.md / GEMINI.md current focus |
| C10 | Provenance packet on every output (timestamp, author_agent, source_systems, claim_type, evidence, risks, benefits, next_action). No packet → context only, not actionable. | Spine v0.5 §7 |

---

## 3. Architecture (Seven Components, Mostly Existing)

```
┌──────────────────────────────────────────────────────────────────────┐
│                        IDLE-TIME METAHARNESS DRIVER                  │
│                                                                      │
│   ┌─────────────────┐                                                │
│   │ 1. Heartbeat    │   cron / systemd / PicoClaw-style daemon       │
│   │    Scheduler    │   default cadence: 15 min                      │
│   │                 │   reads .agent-surface/heartbeat/STOP first    │
│   └────────┬────────┘                                                │
│            │ tick                                                    │
│            ▼                                                         │
│   ┌─────────────────┐                                                │
│   │ 2. Backlog      │   sources:                                     │
│   │    Manager      │   - .agent-surface/events/ (filewatch intake)  │
│   │                 │   - strategic memo action items                │
│   │                 │   - open Phase 0 blockers                      │
│   │                 │   - ADR-Suite gaps                             │
│   │                 │   - re-bicameralization brief next-steps       │
│   │                 │   ranks by: leverage × tractability × phase    │
│   └────────┬────────┘                                                │
│            │ top-K tasks                                             │
│            ▼                                                         │
│   ┌─────────────────┐                                                │
│   │ 3. Heartbeat    │   *** NEW COMPONENT ***                        │
│   │    Producer     │   for each task:                               │
│   │                 │     - assemble context from CONTEXT_L0/L1      │
│   │                 │     - construct Claim draft                    │
│   │                 │     - attach provenance packet (C10)           │
│   │                 │     - select voter cohort (≥3 providers,       │
│   │                 │                            ≥4 model families)  │
│   └────────┬────────┘                                                │
│            │ Claim + voter list                                      │
│            ▼                                                         │
│   ┌─────────────────┐                                                │
│   │ 4. Layer 4.5    │   ✅ Verified — 32/32 tests, ADR-10 v2.0       │
│   │    Gateway      │   passive router; appends to source chain;     │
│   │    (existing)   │   does not decide outcomes                     │
│   └────────┬────────┘                                                │
│            │ analog votes [-1.0, +1.0] from voters                   │
│            ▼                                                         │
│   ┌─────────────────┐                                                │
│   │ 5. Cost Tracker │   per-provider daily budget                    │
│   │                 │   per-task token spend logged                  │
│   │                 │   provider auto-disabled at cap                │
│   │                 │   re-enabled at midnight (provider-local TZ)   │
│   └────────┬────────┘                                                │
│            ▼                                                         │
│   ┌─────────────────┐                                                │
│   │ 6. Review Queue │   outbox/pending-review/<task-id>/             │
│   │                 │     - claim.json                               │
│   │                 │     - votes.json                               │
│   │                 │     - synthesis.md                             │
│   │                 │     - provenance.yaml                          │
│   │                 │   *** STOPS HERE *** until human triage        │
│   └────────┬────────┘                                                │
│            ▼                                                         │
│   ┌─────────────────┐                                                │
│   │ 7. Resumption   │   single .agent-surface/context/RESUMPTION.md  │
│   │    Surface      │   X completed, Y in review, Z blocked          │
│   │                 │   $ spent per provider                         │
│   │                 │   last heartbeat timestamp                     │
│   │                 │   top 5 review-queue items by leverage         │
│   └─────────────────┘                                                │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────────┐
              │ HUMAN STEWARD (you, when back)   │
              │ reads RESUMPTION.md → triages    │
              │ review queue → promotes survivors│
              │ to Plane B canon via control     │
              │ loop Step 7                      │
              └──────────────────────────────────┘
```

---

## 4. Component Specs

### 4.1 Heartbeat Scheduler

- **Implementation candidates:** (a) `cron` — simplest, host-native, no Docker dependency; (b) `systemd` user service — better restart semantics; (c) PicoClaw-style heartbeat daemon adapted from the verified-external Sipeed project — overkill for v0.1 but already battle-tested.
- **Default cadence:** 15 minutes. Configurable in `.agent-surface/heartbeat/config.yaml`.
- **First action every tick:** check `.agent-surface/heartbeat/STOP`. If present, exit immediately. No work done. (Constraint C7.)
- **Second action every tick:** check `.agent-surface/heartbeat/PAUSE-<provider>` files. If present, exclude that provider from this tick's voter cohort.
- **Note:** Your terminal log showed `semgrep-wrapper: Docker daemon not reachable`. Recommend cron or systemd path for v0.1; revisit Docker once daemon is fixed.

### 4.2 Backlog Manager

- **Source 1:** `.agent-surface/events/` — existing filewatch queue. Many observers, one writer per surface (per filewatch plan).
- **Source 2:** Strategic context memo action items (the seven from the prior memo).
- **Source 3:** Open Phase 0 blockers from CLAUDE.md / GEMINI.md / AGENTS.md (Rose Forest compile, Tryorama, ConversationMemory↔MultiScaleEmbedding, ADR-0 Test #4 — note Test #4 is now passed per orient output, so this list is shorter than the docs suggest).
- **Source 4:** ADR-Suite gaps — specifically ADR-Suite v2.0 reconciliation drift items.
- **Source 5:** Re-bicameralization brief next-steps (NK-AD-001/002/003, DKVP paraphier metadata, darwin loss terms).
- **Ranking function (initial proposal):**
  ```
  score(task) = leverage(task) × tractability(task) × phase_weight(task)

  where:
    phase_weight = 10 if Phase 0 blocker, 3 if redline action item, 1 otherwise
    leverage = subjective 1–5 (set by human at task-creation; default 3)
    tractability = 1 if can complete in single heartbeat, 0.5 if multi-heartbeat, 0.1 if requires human input mid-task
  ```
- **Ranking is provisional** — calibrate against actual pilot data per ADR-10 v2.0 analog-vote calibration plan.

### 4.3 Heartbeat Producer (NEW — the missing piece)

- **Input:** top-K tasks from backlog manager (default K = number of available providers ÷ 2, so each task gets a redundant voter pair).
- **For each task:**
  1. Assemble context: load `CONTEXT_L0.md` always; `CONTEXT_L1.md` if task tagged `needs_l1`; route via `python FLOSS/scripts/context_router.py "<query>" --format markdown --limit 4` for task-specific context.
  2. Construct Claim draft: typed assertion per ADR-10 wire format. Include task description, context, success criterion, blast-radius tier.
  3. Attach provenance packet (C10) — fully populated; refuse to dispatch on missing field.
  4. Select voter cohort: enforce diversity policy from METAHARNESS_OPERATING_MODEL — ≥3 provider surfaces, ≥4 model families. Same-family endpoints don't count as independence.
  5. Set claim_type to one of {observed_fact, repo_assumption, proposal, target} per Spine §7.
- **Output:** Claim + voter list, dispatched via existing Layer 4.5 gateway interface.

### 4.4 Layer 4.5 Gateway Dispatch — UNCHANGED

Use existing `FLOSS/packages/metacoordinator_mcp/server.py` interface. Hashline pre/post-write verification stays in place. Source chain append-only guarantee unchanged. ITMD is producer-side overlay only.

### 4.5 Cost / Rate-Limit Tracker

- **Per-provider config in `.agent-surface/heartbeat/budgets.yaml`:**
  ```yaml
  providers:
    cerebras:
      daily_token_cap: 500000        # 50% of free tier headroom
      requests_per_minute: 10
      reset_tz: UTC
    groq:
      daily_token_cap: 500000
      requests_per_minute: 30
      reset_tz: UTC
    mistral:
      daily_token_cap: 200000
      requests_per_minute: 5
      reset_tz: UTC
    flowith:
      daily_token_cap: ?              # set after measuring one day
      requests_per_minute: ?
  ```
- **Behavior:** track per-tick token spend; on cap → write `.agent-surface/heartbeat/PAUSE-<provider>` (cleared at reset_tz midnight); continue with remaining providers.
- **Cap policy:** initial default = 50% of measured/estimated subscription cap, leaving headroom for interactive sessions. Tune after week 1.
- **Halt-all condition:** if all providers paused, write `.agent-surface/heartbeat/STOP-NEEDS-HUMAN` (distinct from STOP — indicates no work possible, not user STOP). Resumption page surfaces this prominently.

### 4.6 Review Queue

- **Path:** `outbox/pending-review/<UTC-timestamp>-<task-id>/`
- **Files per task:**
  - `claim.json` — original Claim wire format
  - `votes.json` — analog votes from each voter, including text rationale
  - `synthesis.md` — proposed deliverable (analysis, draft ADR, benchmark output, etc.)
  - `provenance.yaml` — full provenance packet
  - `triage.md` — empty placeholder for human notes
- **Triage actions (human, on return):** `accept` (move to canon path per task), `revise` (kick back with notes for next heartbeat), `reject` (move to `outbox/rejected/` with reason), `archive` (low-value, keep for record).
- **No automatic promotion** under any condition in v0.1. (C2, C4.)

### 4.7 Resumption Surface

- **Path:** `.agent-surface/context/RESUMPTION.md` (alongside CONTEXT_L0.md per existing context daemon architecture).
- **Regenerated:** every heartbeat, append-only log of changes; full state in single file ≤ 200 lines.
- **Schema:**
  ```markdown
  # FLOSSI0ULLK Resumption Surface
  Last update: <ISO timestamp>
  Last heartbeat: <ISO timestamp>
  Heartbeat status: ACTIVE | PAUSED | STOPPED | NEEDS_HUMAN

  ## Today's compute spend
  - Cerebras: X tokens / Y cap (Z%)
  - Groq: ...
  - Mistral: ...
  - Flowith: ...

  ## Review queue (top 5 by leverage)
  1. <task-title> — <leverage-score> — <link>
  ...

  ## Completed since last human session
  - <count> tasks accepted/auto-archived
  - <count> tasks rejected
  - <count> tasks blocked (need human input)

  ## Blocked items (need human input mid-task)
  - <task-title> — <reason> — <link>
  ```
- **Reading discipline:** the user reads RESUMPTION.md *first* on return. One page. If anything else is required to know the state of the system, the resumption surface has failed and gets fixed.

---

## 5. Failure Modes & Mitigations

| Failure mode | Likelihood | Mitigation |
|---|---|---|
| Loop produces 100s of low-quality drafts that swamp triage | High | Cost cap C8 limits volume; leverage-ranking concentrates spend; if review queue > N entries, scheduler auto-pauses (`STOP-NEEDS-HUMAN`) until depth drops below threshold. |
| Loop drifts from Phase 0 priority | Medium | Backlog ranking C9 phase_weight = 10 for Phase 0; review monthly. |
| Cost caps blown due to provider pricing change | Medium | Tracker checks per-tick spend against cap; conservative 50% default leaves margin; weekly review. |
| Loop publishes to canon by accident | Should be impossible by C2/C5 | Review queue is a separate filesystem path; promotion requires explicit human action; CI gate (Spine v0.5 §12) refuses commits to canon paths from the loop's user/agent identity. |
| Human can't tell what loop did while away | High without resumption surface | Resumption surface (component 7) is the explicit answer; if it's not legible, fix it before iterating loop. |
| Voter providers all return garbage on a task | Medium | Diversity policy (≥3 providers, ≥4 model families) catches single-provider failure; if all-negative votes, task gets marked `needs_human_review` with vote text attached. |
| Loop violates NK-AD-001 by drafting in user's voice | Should be impossible by prompt design | Heartbeat producer prompts include explicit "you are producing artifacts attributed to <agent-id>, not to the human steward" framing; lints check output for first-person from user. |
| STOP file ignored due to bug | Catastrophic | STOP check is the literal first line of every heartbeat; unit test required; if STOP file exists for >24hr without removal, separate watchdog kills the daemon. |

---

## 6. Pilot Plan (7 days)

| Day | Activity | Success metric |
|---|---|---|
| 0 | Set budgets, verify Layer 4.5 gateway operational, seed backlog with 7 strategic-memo action items + open Phase 0 blockers, write STOP file *before* enabling cron | All preconditions checked; STOP file in place |
| 1 | Remove STOP, enable cron at 30-min cadence (conservative), monitor first 8 cycles | No errors; first review-queue items present; cost-tracker numbers sane |
| 2–3 | Tighten cadence to 15 min if stable; review queue triage daily | Review queue depth ≤ 20; human triage time ≤ 30 min/day |
| 4 | First mid-pilot review: are outputs useful? Drift from Phase 0? Cost on track? | Decision: continue / adjust / kill |
| 5–6 | Continue with adjustments | Same metrics |
| 7 | Final review: produce ITMD-pilot-results.md with measured compute consumption, output utility breakdown (accepted/revised/rejected/archived ratios), human triage time, surprises | Decision: promote to ADR-12, iterate to v0.2, or shelve |

**Kill criteria (any one triggers immediate STOP):**
- Loop produces a single artifact that violates NK-AD-001 (substitutes for user's voice).
- Loop publishes anything to Plane B canon without explicit human approval.
- Cost cap blown on any provider.
- Review queue depth exceeds 100 with human unable to triage.

---

## 7. What This Does NOT Do (Out of Scope for v0.1)

- **Does not generate new tasks autonomously.** All backlog items originate from human-curated sources (memos, ADRs, brief next-steps, filewatch intake). v0.2 may add task-generation rules; v0.1 does not.
- **Does not modify the Layer 4.5 gateway.** Producer-side only.
- **Does not handle multi-heartbeat tasks.** Tasks must complete in one heartbeat or be marked `needs_human_review`. v0.2 may add task-state machines.
- **Does not coordinate across multiple human stewards.** Single-steward assumption. Multi-steward governance is a separate ADR.
- **Does not run on Layer 0 substrate.** Layer 0 is ❌ Blocked / ⚠️ Specified per current canon. ITMD is a Plane A overlay; when Layer 0 ships, the producer migrates into a Holochain DNA-backed scheduler in v1.0.

---

## 8. Open Questions / Unknowns

1. What's Flowith's actual rate limit and cost model? Need direct check before setting budget.
2. Should Claude Pro / Codex / Gemini be voters, or only consulted via separate non-gateway channels? Argues for separate channel — they're not the same wire format. Provisional: keep them out of the gateway voter cohort for v0.1; use them as separate human-summoned reviewers when triage requires.
3. Does the existing `autonomous_synthesis_loop.py` have any state assumptions that conflict with this driver? Needs direct file read before integration.
4. Where does the resumption surface live in mobile / Claude Code interfaces? May need a `/resume` slash command to surface RESUMPTION.md cheaply.
5. What's the right cadence after pilot week 1? 15-min default may be too aggressive for free tiers; 30-min may waste capacity. Calibrate empirically.

---

## 9. Compliance Check (5-box)

| Box | Status | Note |
|---|---|---|
| Accuracy & Safety | ✅ | All ten hard constraints (C1–C10) explicitly mapped to canon source; STOP gate, cost caps, ACI, autoprompt-divergence all enforced; pilot has explicit kill criteria. |
| Actionable usefulness | ✅ | Composes existing infrastructure (Layer 4.5 ✅, autonomous_synthesis_loop, filewatch) plus one new component (heartbeat producer); 7-day pilot plan with measurable success criteria; budgets and config schemas concrete enough to copy-paste. |
| Clarity | ✅ | One-line summary; ASCII architecture diagram; per-component spec; failure-mode table; pilot plan; out-of-scope list. |
| Continuation of context | ✅ | Grounded in current canon (CLAUDE/AGENTS/GEMINI.md, ADR-Suite v2.0 analog vote model, Spine v0.5 Plane A/B + ACI + provenance, Architecture Spec v0.1 control loop, METAHARNESS six-harness model); honors prior memo's forbidden-promotion rule and re-bicameralization brief's NK-AD-001. |
| Sycophancy-resistance | ✅ | Explicit out-of-scope section names what this does NOT do; does not claim level-1 leverage; does not assume the autonomous_synthesis_loop.py state model fits without verification; flags Phase 0 priority must outrank ITMD's own work; pilot includes explicit kill criteria including immediate STOP on canon violation. |

---

*Layer 4.5 already routes. The driver makes it iterate.*
*Plane A produces; Plane B validates; the human steward decides.*
*STOP is a one-byte file. That is the whole governance surface.*
