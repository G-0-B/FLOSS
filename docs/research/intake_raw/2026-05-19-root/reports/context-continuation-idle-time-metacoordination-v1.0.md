# Context Continuation Artifact — Idle-Time Metacoordination Thread

```yaml
id: context-continuation-idle-time-metacoordination
version: "1.0.0"
kind: context_continuation_artifact
status: active
truth_status: ⚠️ Specified — artifacts produced are design + runnable code; none yet piloted
date: 2026-05-11
project: FLOSSI0ULLK
precedence: "Synthesis/continuation doc — Level 10 per Spine v0.5 §1. For enforcement load Kernel v1.3.1 + Spine v0.5 + ADR-Suite v2.0."
thread_span: "5 user turns — strategic-memo audit → idle-compute request → code delivery"
intake_doctrine: filter-through-not-out
supersedes: []
upgrade_path:
  - "When heartbeat.py is piloted, replace this with a pilot-results continuation"
rollback_plan: "Discard; no downstream dependencies. Artifacts in /outputs stand alone."
provenance_packet_required: true
```

---

## 0. How to use this artifact

This is the **resume surface** for the idle-time metacoordination work thread. If
you (any agent — Claude, Codex, Gemini, future self/other) are picking this up
cold, read this top-to-bottom once. It is the rationale companion to four
deliverables sitting in the conversation's output channel.

**Loading order for a cold resume:**
1. This artifact (thread state + open decisions)
2. `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` (current canon — layer status, north-star test, doc-budget rule)
3. ADR-Suite v2.0 (analog vote model, voter roster, Layer 4.5 ✅ Verified)
4. The four deliverables below, as needed

---

## 1. What this thread was

The user wants **constantly re-iterating metacoordination** that consumes idle
subscription + free-tier compute (Cerebras / Groq / Mistral / Flowith via the
Layer 4.5 gateway; Claude Pro / Codex / Gemini as separate surfaces) while they
are not at the keyboard manually driving. Subscriptions and free quotas burn
unused because the system waits for typed prompts.

The thread also carried a prior sub-thread: a multi-turn audit of an external
strategic synthesis ("HI_ROI_NAO" / Goertzel + Meadows + FOSS-landscape ROI
analysis), which produced a strategic-context memo before the idle-compute
request arrived.

---

## 2. Deliverables produced (all in conversation output channel)

| Artifact | Status | What it is | Disposition |
|---|---|---|---|
| `strategic-context-memo-ecosystem-signals-v0.1.md` | Draft | Redline of the HI_ROI_NAO synthesis — four-tag scheme (`[VERIFY]` / `[DOWNGRADE]` / `[MERGE]` / `[COMPOSE-CHECK]`); classifies external ecosystem facts vs FLOSSI0ULLK capability claims | Intake material for `FLOSS/docs/research/` — human steward gate to promote |
| `idle-time-metaharness-driver-v0.1.md` | **Superseded** | 24KB design spec for the idle-compute loop | **Do not file as a doc.** Violated CLAUDE.md doc-budget rule. The implementation it described already existed. Treat as thinking-scratch; if prose is wanted, fold a short section into `FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md` |
| `heartbeat.py` | Runnable, syntax-checked, unpiloted | Thin scheduler composing existing scripts in rotation; STOP-file gate; per-tick + daily round caps; writes `RESUMPTION.md` | Drop into `FLOSS/scripts/`. Test with `--once` behind a STOP file first |
| `heartbeat_slate.py` | Runnable, syntax-checked, unpiloted | Dynamic-slate generator — replaces the hardcoded 5-item list in `poll_high_roi_actions.py` with candidates from real backlog sources | Drop into `FLOSS/scripts/`. Not yet wired into `poll_high_roi_actions.py` — see Open Decision #1 |

---

## 3. The key correction that defines this thread

My first response to the idle-compute request (the v0.1 ITMD spec) was **wrong
in two specific ways**, and the correction is load-bearing for anyone resuming:

1. **"The missing Heartbeat Producer" already existed.** `poll_high_roi_actions.py`
   is exactly that pattern — candidate slate → submit Claims → run consensus
   through the gateway → rank by `tally_mean`/`tally_variance` → write JSON+MD.
   The only genuine gaps were (a) dynamic slate generation and (b) a scheduler.
2. **The spec doc itself was a doc-explosion failure.** CLAUDE.md now carries an
   explicit doc-budget discipline rule naming doc-explosion as the dominant
   failure mode across three project iterations. A 24KB standalone spec for
   something that should have been a section in an existing plan *is* that
   failure mode.

**Lesson for resume:** read the actual code before specifying. The infrastructure
is more complete than prose descriptions suggest. Compose, don't greenfield.

---

## 4. What already exists (verified by reading the actual scripts)

The FLOSSI0ULLK workspace already has a working event-driven metacoordination
substrate. Confirmed by direct read of 17 uploaded scripts:

- **`poll_high_roi_actions.py`** — runs a strategic slate through the gateway
  with a configurable voter profile (`diverse` default), ranks results, writes
  to `.agent-surface/polls/`. Hardcoded 5-candidate slate.
- **`autonomous_synthesis_loop.py`** — scans `docs/research/`, `docs/vision/`,
  `_reference/` for unprocessed markdown; LLM "fractal semantic extraction" to
  `docs/knowledge_log/staging/` (Plane A). `--commit` appends to source chain
  (human-gated). Default model `groq/llama-3.1-8b-instant`.
- **`watch_intake.py`** — polling filewatch; emits normalized IntakeEvents to
  `.agent-surface/events/incoming/`. Already has `--loop` + `--interval-seconds`
  + debounce. Excludes `AGENTS.md`/`CLAUDE.md`/`GEMINI.md`/`INDEX.md` from intake.
- **`process_intake_events.py`** — consumes the event queue; classifies
  `recommended_actions` (`consider_canon_promotion`, `review_trace_drift`,
  `refresh_shared_skills`, etc.); writes `QUEUE_SUMMARY.md`. No LLM calls.
- **`hook_pre_write.py` / `hook_post_write.py` / `hook_bg_round.py`** — the
  Claude Code / Gemini CLI hook chain: pre-write checkpoint → post-write Claim
  submission → DETACHED background consensus round → traces to
  `~/.floss_agent/traces/consensus/`. Substantive-path filter is `/packages/**`
  with `.py/.rs/.toml` extensions; this filter IS the spam-prevention layer.
- **`context_router.py`** — keyword-scores queries against
  `shared-context-surface.json` corpora; cheap re-orientation.
- **`materialize_shared_*.py`** — project shared surfaces (hooks, skills, agent
  surface) into agent-native artifacts with `--check` drift detection.
- **`smoke_test_inference.py` / `smoke_test_voters.py` / `smoke_test_gateway.py`**
  — Cerebras + Groq inference, voter pipeline, full gateway loop. The gateway
  smoke test confirms the `submit → vote → decide → read → idempotency` loop.

---

## 5. Hard constraints (non-negotiable — inherited from canon)

These bind any continuation of this work:

| ID | Constraint | Source |
|---|---|---|
| C1 | Autoprompt divergence — loop output never substitutes for the user's voice; no external messages/PRs/canon edits as user | NK-AD-001 (re-bicameralization brief) |
| C2 | Plane A only — loop publishes to review queues; promotion to Plane B canon requires human steward gate | Spine v0.5 §5 |
| C3 | ACI blast-radius tiers — read/search/test/draft/propose-ADR allowed; merge/push/send disallowed without approval + CI proof | Spine v0.5 §10.2 |
| C4 | Forbidden-promotion rule — external benchmark/capability never restated as FLOSSI0ULLK capability without measurement | strategic-context memo §1 |
| C5 | Layer 4.5 gateway stays a passive router — heartbeat is producer-side only | ADR-10 v2.0 |
| C6 | Symbolic First — loop output is neural assistance; symbolic validators decide | prime directive |
| C7 | Single STOP file (`.agent-surface/heartbeat/STOP`) halts all loops; checked as literal first action every tick | heartbeat.py implements this |
| C8 | Per-provider / daily round caps — `FLOSS_DAILY_ROUND_CAP` env var, default 60; `MAX_ROUNDS_PER_TICK` = 6 | heartbeat.py implements this |
| C9 | Phase 0 substrate tasks outrank all other backlog until Phase 0 exits | CLAUDE.md current focus |
| C10 | Provenance packet on every output; no packet → context only | Spine v0.5 §7 |
| C11 | **North-star load-bearing test** — every work item declares how it advances universal flourishing; "I forgot to ask" → reject the move | CLAUDE.md (newly added) |
| C12 | **Doc-budget discipline** — before adding a new `.md`, check if the thought belongs in an existing doc; doc-explosion is the empirical dominant failure mode | CLAUDE.md (newly added) |

`heartbeat.py` and `heartbeat_slate.py` honor C1–C12. Notably C11 is a runtime
invariant: every `WorkItem` and `Candidate` carries a `flourishing_rationale`
field; the slate generator refuses rationale-less candidates.

---

## 6. Current canon state (as of thread, per uploaded CLAUDE.md / orient output)

- **Date / branch:** 2026-05-07 orient output, branch `master`
- **Recognition Protocol:** ✅ Validated — ADR-0 Test #4 (Human Coherence) passed
  2026-03-20; all four ADR-0 criteria Verified
- **Layer 4.5 (local agent node / consensus gateway):** ✅ Verified — 32/32 tests
  passing per ADR-10 (formerly ADR-MCP-ORCHESTRATOR)
- **Vote model:** analog float `[-1.0, +1.0]` — ternary formally superseded per
  ADR-10 v2.0
- **Voter roster:** Cerebras + Groq + Mistral + Flowith. Diversity policy: ≥3
  provider surfaces, ≥4 model families; same-family endpoints ≠ independence
- **Phase 0 (substrate viability) — current focus:**
  - Rose Forest DNA: ⚠️ compiles (upgraded per ADR-2 v2.0); full Tryorama suite
    unvalidated. Exit criterion: `cargo test` + 4 Tryorama scenarios passing
  - ConversationMemory ↔ MultiScaleEmbedding API mismatch — defensive
    normalization landed (`193729c`); underlying reconciliation open
- **ADR-Suite v2.0** hand-verified 2026-04-26; current set ADR-0, 0.1, 1–11
- **Architecture-Spec-v0.1** at workspace root awaiting promotion; deprecates
  the "four planes" framing; §6.1 still describes ternary voting (stale —
  superseded by ADR-10 analog model). Flagged for version-bump/archive
- **Known infra issue:** Docker daemon unreachable (`semgrep-wrapper` failed in
  terminal log). `heartbeat.py` deliberately uses cron/systemd path, no Docker
- **Doc-explosion** named the dominant failure mode across three iterations
  (`amazon_rose_forest`, `amazon_rose_forest_01`, current `FLOSS/`)
- **CCES (Co-Creative Evolution Stack)** — n+3 universal-flourishing framework,
  8 layers L0–L7; long-arc philosophical target, NOT a Phase 0 blocker

---

## 7. Open decisions (carried forward — none resolved)

| # | Decision | Detail | Default if unaddressed |
|---|---|---|---|
| 1 | Wire `heartbeat_slate.py` into `poll_high_roi_actions.py`? | `heartbeat_slate.py` writes `next_slate.json` but does not drive the poll script. Needs a ~1-line patch to `candidate_claims()` to read that file with fallback to hardcoded slate. Left out deliberately — it's the user's script, needs rollback-path decision | Poll keeps its hardcoded 5-item slate; dynamic slate unused |
| 2 | Daily round cap value | Default 60 is arbitrary. Real Cerebras/Groq free-tier headroom unknown until measured | Stays 60 via `FLOSS_DAILY_ROUND_CAP` |
| 3 | Heartbeat cadence | Default 900s (15 min) is arbitrary. Hooks already dispatch on file edits; heartbeat is for *idle* compute only | Stays 15 min |
| 4 | Claude Pro / Codex / Gemini — voters or separate channels? | Different wire format than the gateway voter cohort. Provisional: separate channels, human-summoned reviewers, not autonomous voters | Excluded from gateway voter cohort |
| 5 | Round-counting precision | `heartbeat.py` assumes `poll_high_roi_actions.py` = 5 rounds (true for hardcoded slate). When slate goes dynamic, must parse actual poll output | Coarse 5-round estimate |
| 6 | Strategic-context memo — promote, fold, or shelve? | It's intake material. Action items #1–#7 inside it were the seed backlog for the heartbeat | Stays unfiled in /outputs |
| 7 | ITMD v0.1 spec — discard or fold? | Superseded. If prose wanted, fold a short section into the filewatch-metaharness plan | Discard |

---

## 8. Recommended next move (single clear ask, per Spine v0.5 §7)

**Pilot `heartbeat.py` for one day, behind the STOP-file safety, then decide #1–#5
from measured data.**

Concrete first steps (PowerShell, from `C:\~shit`):
```powershell
# 1. Place the scripts
Copy-Item heartbeat.py, heartbeat_slate.py FLOSS\scripts\

# 2. Dry-test the slate generator (no LLM calls)
python FLOSS\scripts\heartbeat_slate.py --max-candidates 5

# 3. Test one tick behind STOP (should skip everything, write RESUMPTION.md)
New-Item -Path .agent-surface\heartbeat\STOP -Force
python FLOSS\scripts\heartbeat.py --once

# 4. Remove STOP, run one real tick
Remove-Item .agent-surface\heartbeat\STOP
python FLOSS\scripts\heartbeat.py --once

# 5. Read .agent-surface\context\RESUMPTION.md — confirm it's legible
# 6. If good: python FLOSS\scripts\heartbeat.py --loop --interval-seconds 900
```

Kill criteria (any one → create STOP file immediately):
- A produced artifact substitutes for the user's voice (C1 violation)
- Anything published to Plane B canon without human approval (C2 violation)
- Free-tier quota blown on any provider
- Review queue depth exceeds ~100 with human unable to triage

---

## 9. Provenance packet

```yaml
timestamp: 2026-05-11T00:00:00Z
author_agent: claude-opus-4.7
human_collision_node: Anthony Garrett (kalisam)
source_systems:
  - claude.ai conversation thread (5 user turns)
  - 17 uploaded FLOSSI0ULLK scripts (read directly)
  - uploaded canon: CLAUDE.md, AGENTS.md, GEMINI.md, Project-Spine v0.5,
    ADR docs, seed packets, context_compression_packet v1.1,
    re-bicameralization brief, resonance_mechanism_v2, Architecture-Spec-v0.1
claim_type: proposal
payload:
  summary: >
    Idle-time metacoordination thread. Produced a strategic-context memo
    (redline of an external ROI synthesis), then — after reading the actual
    workspace scripts — corrected an overspecified design spec and delivered
    two runnable composer scripts (heartbeat.py scheduler + heartbeat_slate.py
    dynamic-slate generator) that drive existing infrastructure on a cadence
    under STOP-gate, round-cap, and universal-flourishing-gate constraints.
  evidence:
    - "/outputs/heartbeat.py (syntax-checked, unpiloted)"
    - "/outputs/heartbeat_slate.py (syntax-checked, unpiloted)"
    - "/outputs/strategic-context-memo-ecosystem-signals-v0.1.md (draft)"
    - "/outputs/idle-time-metaharness-driver-v0.1.md (superseded — do not file)"
  risks:
    - "Scripts unpiloted — no runtime evidence yet"
    - "Round-counting is coarse (assumes 5 rounds/poll)"
    - "heartbeat_slate.py not yet wired into poll_high_roi_actions.py"
    - "Daily cap + cadence defaults are arbitrary, need empirical tuning"
    - "Compute-consumed-for-its-own-sake is a real anti-pattern; the
      review-queue-utility metric is the answer-by-measurement, not a guarantee"
  benefits:
    - "Composes existing verified infrastructure rather than greenfielding"
    - "Honors all 12 hard constraints incl. two newly-added CLAUDE.md rules"
    - "STOP file is a one-byte, one-tick-latency kill switch"
    - "Universal-flourishing gate is a runtime invariant, not a footnote"
    - "RESUMPTION.md gives single-page steward re-entry"
next_action: >
  Pilot heartbeat.py for one day behind the STOP-file safety; decide open
  questions #1–#5 from measured data. Or: request the
  poll_high_roi_actions.py patch (Open Decision #1) as a reviewable diff.
```

---

## 10. Compliance check (5-box)

| Box | Status | Note |
|---|---|---|
| Accuracy & Safety | ✅ | Thread state captured from actual artifacts + uploaded canon; no invented claims; superseded spec explicitly flagged as do-not-file |
| Actionable usefulness | ✅ | Open decisions table + single clear next ask + PowerShell pilot recipe + kill criteria |
| Clarity | ✅ | Loading order up front; the defining correction called out as its own section; deliverables table with disposition column |
| Continuation of context | ✅ | This artifact IS the continuation surface; grounds every claim in canon (Spine v0.5, ADR-Suite v2.0, CLAUDE.md incl. newly-added rules); provenance packet per Spine §7 |
| Sycophancy-resistance | ✅ | Preserves the thread's central correction (overspecification + doc-explosion failure) rather than smoothing it over; names compute-for-its-own-sake as a real anti-pattern; lists all 7 open decisions as unresolved rather than implying closure |
```
