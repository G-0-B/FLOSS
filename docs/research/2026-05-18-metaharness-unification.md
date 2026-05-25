# Meta-harness Unification — Atomic + Holistic via Shared Conventions

**Date:** 2026-05-18
**Type:** Research / Architectural reconciliation (ADR-candidate companion to ADR-14 Inline Reasoning Ensemble)
**Truth status:** ⚠️ Specified — inventory of existing harnesses + unification plan; not yet implemented as a refactor
**Author trail:** User (Anthony) named the pattern 2026-05-18 ("we need an overarching metaharness overseer orchestrator centralized agent-centric thing but not just holistic but atomic"). This doc reframes the ask as **unification of existing harnesses via shared conventions**, NOT as construction of a new orchestrator class.
**Related canon/research:**
  - `2026-05-17-inline-reasoning-ensemble.md` (per-Claude-prompt Router pattern — the *atomic* primitive)
  - `2026-05-16-mdash-cfis-architectural-transfer.md` (the "harness is the product, model is one input" principle)
  - `FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md` (the six-harness composition — Canon/Context/Execution/Consensus/Reflection/Publish)
  - `FLOSS/docs/architecture/AGENTIC_OPERATING_MODEL.md`
  - ADR-Suite v2.0 §13 governance-gap backlog
**Subsumes / clarifies:** The user's `[every chat / every chain of thought]` framing from the Inline Reasoning Ensemble origin prompt 2026-05-17.

---

## 0. The pattern being named, in one sentence

The FLOSSI0ULLK project has accumulated **8+ executable harnesses** over the past months, each correct in isolation but each invented with a slightly different methodology — different staging dir, different activity-log shape (or none), different LLM call path, different provenance convention. The repeated work is not in the *function* of each harness but in the *re-invention of the surrounding scaffolding* every time a new one ships. This is the meta-scaffold reproduction of the doc-explosion failure mode named in `project_doc_explosion_acknowledged.md`.

---

## 1. The pushback on "build an overseer"

The user's instinct to build an overarching meta-harness is correct as a *problem statement* and wrong as a *solution shape*. Building a new orchestrator class would be the failure mode itself — yet another script with yet another staging convention and yet another activity-log schema, alongside the existing ones. The "different methodology each time" pattern reproduces, with one more file added to the inventory.

**The correct move is unification of the existing harnesses via shared conventions**, not new construction. The meta-orchestration kernel already exists in pieces — the heartbeat scheduler + Layer 4.5 consensus gateway + Router (Inline Reasoning Ensemble) + activity log triad. The work is making the existing scripts CONFORM to a shared atomic interface, then letting the heartbeat compose them at the holistic layer.

This is the same shape as the reuse ledger: inventory before construction. Identify what already exists, find the duplicated scaffolding, refactor toward shared abstractions, build only the *gaps* in the shared abstractions — never a new whole.

---

## 2. Existing harness inventory

| # | Harness | Function | Staging dir | Activity log | LLM call path | Status |
|---|---|---|---|---|---|---|
| 1 | `heartbeat.py` | Cron-style scheduler composing other scripts on cadence | — (composes) | `.agent-surface/heartbeat/ticks.log` + global `Action` | — (delegates) | ✅ Running 24/7 via Servy |
| 2 | `poll_high_roi_actions.py` | Strategic claim ranking via consensus gateway | `.agent-surface/polls/` | global `Action` | **Consensus gateway** (Layer 4.5) | ✅ Verified |
| 3 | `autonomous_synthesis_loop.py` | Markdown → fractal semantic extraction | `docs/knowledge_log/staging/` | global `Action` | **LiteLLM direct** | ✅ Working |
| 4 | `harvest_reuse_ledger.py` (2026-05-17) | Fork URL → ledger-entry-shaped YAML draft | `.agent-surface/harvest/staging/` | `.agent-surface/harvest/activity.jsonl` + global `Action` | **Gemini CLI subprocess** | ✅ 66 drafts produced |
| 5 | `watch_intake.py` + `process_intake_events.py` | Polling filewatch + queue consolidator | `.agent-surface/events/incoming/` | — | No LLM | ✅ Specified |
| 6 | `heartbeat_slate.py` | Dynamic slate generator for #2 | — (feeds #2) | — | No LLM | ✅ Working |
| 7 | `reasoning_ensemble/router.py` (2026-05-18) | Per-prompt mode classifier | — | `.agent-surface/reasoning/activity.jsonl` + global `Action` | **Ollama HTTP direct** | ✅ v0.1 calibrated 100% |
| 8 | `backfill_kalisam_fork.py` (2026-05-18) | One-time data fixup | — (in-place) | — | No LLM (gh API only) | ✅ Done |

**Duplicated scaffolding patterns (the pre-U2/U3 problem this doc fixed):**
- **4 different staging-dir conventions**: `.agent-surface/<subsystem>/staging/`, `.agent-surface/<subsystem>/` (no /staging), `docs/knowledge_log/staging/`, `.agent-surface/events/incoming/`
- **3 different activity-log shapes**: per-subsystem `.jsonl` (harvest, reasoning), per-subsystem `.log` (heartbeat ticks), or none at all (poll, synthesis, intake)
- **4 different LLM call paths**: consensus gateway, LiteLLM direct, Gemini CLI subprocess, Ollama HTTP
- **Provenance**: paired JSON sidecar (harvest), inline JSON payload (synthesis), none (poll, intake, ticks)

Every new harness reinvents 3-4 of these. That's the user-named failure pattern.

---

## 3. The three unification abstractions

### 3.1 Atomic interface: `Action`

Every agentic action — whether invoked by a heartbeat tick, a Claude session tool-call, a filewatch event, or a manual CLI run — is an `Action` with this shape:

```python
@dataclass
class Action:
    action_id: str           # e.g., "harvest-0042" or "synth-doc-XYZ.md"
    kind: str                # harvest | synthesis | poll | filewatch | router_decision | ...
    started_at: str          # UTC ISO
    ended_at: str
    duration_seconds: float
    inputs: dict             # what triggered it (target, prompt, file, ...)
    outputs: dict            # paths produced, decision made, claim_id, ...
    llm_calls: list[dict]    # per-call: model, provider, prompt_hash, response_hash, duration
    routing_decision: dict | None  # if Router was invoked: mode, reason, confidence
    success: bool
    error: str | None
    provenance_path: str | None    # path to sidecar JSON (if any), or null
    staging_paths: list[str]       # paths to any drafts staged for review
```

Every existing harness already produces a subset of these fields; the unification is **emitting them in this shape, to a single activity log**, instead of each harness having its own log shape. Backwards-compatible — current per-subsystem logs can continue, AND a wrapper writes the unified Action to the global log.

### 3.2 Holistic surface: single activity log at `.agent-surface/activity.jsonl`

One append-only JSONL file at the workspace level, one Action per line, written by every harness via a tiny shared helper module. This becomes:

- The Plane-A audit trail (Spine v0.5 §7 provenance per action)
- The data source for the future `consolidate_review_queue.py` script that rolls up all staging dirs
- The training corpus for empirical frame-cousin detection (per Inline Reasoning Ensemble v0.2 §12.6)
- The empirical input for the heartbeat's day-summary "what happened" surface

The existing per-subsystem `.jsonl` files stay (they're useful for narrow debugging) but the **global activity log is the canonical write target** — per-subsystem logs become projections.

### 3.3 Routing convention: every LLM call goes through `router.classify()` first

Every harness that makes an LLM call wraps it with:

```python
from FLOSS.packages.reasoning_ensemble.router import classify
decision = classify(prompt, force_mode=None)
if decision.mode == "pass_through":
    response = cheap_single_call(prompt, provider="cerebras")
elif decision.mode == "single_strong":
    response = primary_provider_call(prompt)
elif decision.mode == "ensemble":
    response = ensemble_synthesize(prompt, voters=[...])  # not yet implemented; #5 on §A.6
```

This is the *atomic* in "atomic + holistic" — every LLM call routes through the Router. Latency cost: ~10s warm with phi4-mini per current calibration. Trivial pass_through cases (file reads, format conversions) don't go through the Router — they don't involve LLMs at all.

**Critical:** the Router's decisions get logged to the global activity log. Over weeks, this becomes the empirical CFIS frame-cousin map (Inline Reasoning Ensemble v0.2 §12.6) — which voter models tend to cluster together, which prompts triggered Tier-4 divergence, which mode misclassifications correlated with downstream issues.

---

## 4. Refactor migration path (concrete, ordered)

Per ledger-before-construction discipline + anti-vision-accumulation guard:

| # | Step | Effort | Reversible? |
|---|---|---|---|
| 1 | **Define the shared `Action` schema** in `FLOSS/packages/activity_log/schema.py` + write the global `append_action()` helper | ~50 LOC | Yes — adds new module, doesn't touch existing |
| 2 | **Wire the global activity log into `router.py`** while preserving the reasoning subsystem log | ~10 LOC | Yes — append-only operation |
| 3 | **Wire global activity log into `harvest_reuse_ledger.py`** (tee from harvest activity to global) | ~10 LOC | Yes |
| 4 | **Wire global activity log into `heartbeat.py`** — emit one Action per work-item invocation | ~20 LOC | Yes — additive |
| 5 | **Wire global activity log into `poll_high_roi_actions.py` and `autonomous_synthesis_loop.py`** — emit Actions per poll and extraction | ~30 LOC | Yes |
| 6 | **Refactor `autonomous_synthesis_loop.py` to route LLM call through Router** — currently calls LiteLLM directly; should `classify()` first | ~30 LOC + retest | Yes — keeps fallback to direct LiteLLM if Router unavailable |
| 7 | **Build the staging-roll-up script** `FLOSS/scripts/review_queue.py` that scans all `.agent-surface/*/staging/` + `docs/knowledge_log/staging/` and emits a unified review queue | ~150 LOC | Yes — read-only roll-up |
| 8 | **Document the unified shape** in `FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md` §X (new section) — declare the atomic+holistic conventions as canonical | Update existing doc | Yes — doc edit |
| 9 | **Pilot for 7 days** — observe global activity log; iterate the Action schema if usage reveals gaps | Time, not effort | Schema-versioning preserves backward compat |
| 10 | **Promote to ADR-15** (or merge with ADR-14 Inline Reasoning Ensemble as a v2.0 of that ADR) once empirical data validates | Governance gate | Yes — research → ADR is the canonical promotion path |

Steps 1-5 and 7-8 landed on 2026-05-18 as additive wiring and documentation. Step 6 remains the substantive routing refactor; step 9 is the empirical pilot before ADR promotion.

---

## 5. What this does NOT include (anti-vision-accumulation guards)

- **NOT a new top-level orchestrator class.** The heartbeat IS the holistic composer. We extend its tick-loop to emit unified Actions, not replace it.
- **NOT a new consensus mechanism.** ADR-10 v2.0 analog vote at the Layer 4.5 gateway is the canonical decision-grade surface. The reasoning ensemble (per the Inline Reasoning Ensemble proposal) is a lower-stakes reasoning surface, NOT a competitor to claims.
- **NOT a CFIS pilot.** CFIS Phase 0 has its own 8-week timeline (working-todo §C). The empirical frame-cousin detection from §3.3 above feeds CFIS later — it does NOT replace the frame-recruitment work.
- **NOT a new staging convention** that supersedes the existing ones. Existing dirs stay; the unification is the global *activity log*, not a forced migration of where drafts land. The roll-up script (step 7) reconciles diverse locations into a single review queue.
- **NOT a forced rewrite of working scripts.** Each refactor step is additive — the existing call path stays as the fallback. If `append_action()` raises, the script continues with its old per-subsystem log. Plane A discipline preserved.

---

## 6. Connection to existing canon

| Canon document | This proposal relates by |
|---|---|
| **METAHARNESS_OPERATING_MODEL.md** (six-harness composition) | This is the *implementation layer* under that operating model. Canon/Context/Execution/Consensus/Reflection/Publish are the abstract roles; the unification described here makes each role conform to a shared `Action` shape. |
| **AGENTIC_OPERATING_MODEL.md** | Same — abstract roles, this proposal makes them concrete via the schema. |
| **ADR-10 v2.0** (consensus gateway) | Unchanged. Decision-grade work still routes through the gateway. The unified Action schema records gateway-routed work in the same shape as direct-LLM work, so the global activity log captures both. |
| **Inline Reasoning Ensemble v0.2** (proposal in `2026-05-17-...md`) | This proposal extends the Router pattern from "wraps Claude session prompts" to "wraps every LLM call across all scripts." Synergistic — same atomic primitive at different scopes. |
| **MDASH → CFIS Architectural Transfer** | The unification IS the MDASH "harness is the product" principle applied to FLOSSI0ULLK's existing harnesses, not just to consensus claims. |
| **CFIS v0.3** (pre-canon at workspace root) | The global activity log becomes the empirical input for AI-level CLC independence matrix (frame-cousin detection over time). Feeds CFIS Phase 0 task T4 (divergence schema deployment). |
| **Spine v0.5 §7 (provenance per action)** | Every Action has explicit provenance fields. This proposal makes Spine v0.5 §7 enforced-by-schema rather than convention. |

---

## 7. Honest open questions

1. **Schema versioning.** Is `Action` v1.0 stable enough to commit to, or should the first ~7-day pilot use a v0.1-experimental schema with explicit `schema_version` field? Recommend the latter — preserves room to iterate without retroactively rewriting log entries.
2. **Activity log size.** At ~14 LLM calls per Claude session × 10 sessions/week + heartbeat tick activity ≈ 1k-5k lines/week. Manageable for grep/tail. After 6 months that's ~100k-300k lines (~20-60MB). Plan: rotate by month into `.agent-surface/activity-YYYY-MM.jsonl`, keep current month at top-level path.
3. **Backpressure handling.** If `append_action()` blocks on disk I/O during a hot path, the action's primary work shouldn't be delayed. Recommend: best-effort write with a short timeout, log to stderr on failure, continue. Activity log is observability, not correctness.
4. **What about CLAUDE's own internal reasoning?** Currently: invisible to the harness. The unified activity log captures TOOL CALLS Claude makes (Bash, Edit, Read, etc.) but not Claude's chain-of-thought between calls. This is the same boundary as named in Inline Reasoning Ensemble §8 question 3 — the ensemble augments at the API boundary, not inside the model. Accept the boundary.
5. **Is this two docs (this + the Inline Reasoning Ensemble) or one merged proposal?** They cover different scopes (per-script-call vs per-Claude-prompt) but share the Router primitive. Recommend: keep separate research docs, merge to one ADR (ADR-14 Inline Reasoning Ensemble + Metaharness Unification) at the promotion gate. The merged ADR is the canonical artifact; the research docs become its background sections.

---

## 8. Provenance + next moves

- **This file:** `FLOSS/docs/research/2026-05-18-metaharness-unification.md`
- **Trigger:** User prompt 2026-05-18 + `autonomous_synthesis_loop.py` reading as motivating evidence of duplicated scaffolding patterns
- **Cross-refs above.**
- **Activity-log integration:** when the unification ships, this doc becomes obsolete-as-architecture but stays as historical record of the reasoning.

**Concrete next moves** (in addition to the working-todo §A.6 sequence):

| # | Action | Owner | Status |
|---|---|---|---|
| U1 | Build `FLOSS/packages/activity_log/schema.py` + `append_action()` helper | Tony or Claude-delegate | ✅ Done 2026-05-18 |
| U2 | Wire global activity log tee into `synthesizer.py` and `router.py` | Tony or Claude-delegate | ✅ Done 2026-05-18 |
| U3 | Wire global activity log into `heartbeat.py`, `harvest_reuse_ledger.py`, `poll_high_roi_actions.py`, and `autonomous_synthesis_loop.py` | Tony or Claude-delegate | ✅ Done 2026-05-18 |
| U4 | Build `FLOSS/scripts/review_queue.py` roll-up | Tony or Gemini-delegate | ✅ Done 2026-05-18 — reports 178 queued items |
| U5 | Update `METAHARNESS_OPERATING_MODEL.md` with the unified conventions section | Tony | ✅ Done 2026-05-18 |
| U6 | 7-day pilot + ADR promotion decision | Tony + consensus claim | TODO |

These slot into working-todo as new §A.7 — see the §A.6 Inline Reasoning Ensemble work-stream for the natural sequencing (Router exists → activity log unification → synthesizer + MCP wrapper → pilot).
