# WS5 — Successor Handoff + Fable 5 Credit Escalation Policy

```yaml
# --- UpgradableArtifact Header ---
id: "fable5-ws5-successor-policy"
version: "1.0.0"
kind: "operating_policy"
status: "Proposed"   # policy live pending Anthony's budget number; config already landed
updated: "2026-07-04"
supersedes: []
truth_status: "Verified"   # config landed, 147/147 tests green, live smoke round completed 2026-07-04
evidence_sources:
  - "packages/metacoordinator_mcp/voter_registry.json — post-window profile + dead-id remediation"
  - "Live smoke round 2026-07-04: 6/6 voters, 0 errors, 0 Fable calls, APPROVED mean +0.642 var 0.007, 25.1s"
  - "WS2 chain audit (12,869 votes) + liveness probes 2026-07-04 (8 live ids across 4 surfaces)"
generator: "claude-fable-5"
sprint: "2026-07-03-fable5-sprint-handoff.md (WS5)"
upgrade_path: "Anthony sets the weekly credit budget; revisit triggers after first month of escalation logs"
rollback_plan: "git revert voter_registry.json (prior roster one commit back); policy doc is advisory until budget set"
friction_tier: "medium"   # roster config; no consensus-semantics change
```

## 1. Successor role assignment

**The adversarial/verification role Fable 5 held moves to `omo-critic-gpt-oss-120b`
on `cerebras/gpt-oss-120b`** — the strongest liveness-verified retained model,
wrapped in the existing Critic persona (config-only: the `omo-critic-*` name
prefix routes the persona; zero code changed for the handoff).

Why this host: cerebras sits on a separate rate pool from groq (whose storms
produced 54–90% error-vote rates in the WS2 audit), it is the *only* live
cerebras id (probed 2026-07-04), and 120B-class is the largest retained model
on any keyed surface.

## 2. Post-window roster (`post-window` profile, aliases: `successor`)

| Voter | Model | Surface | Family |
|---|---|---|---|
| `omo-critic-gpt-oss-120b` (verifier) | cerebras/gpt-oss-120b | Cerebras | GPT-OSS |
| `groq-qwen3-32b` | groq/qwen/qwen3-32b | Groq | Qwen |
| `groq-llama-4-scout` | groq/meta-llama/llama-4-scout-17b-16e | Groq | Llama |
| `mistral-devstral-small` | mistral/devstral-small-2507 | Mistral | Mistral |
| `mistral-open-mistral-nemo` | mistral/open-mistral-nemo | Mistral | Mistral |
| `flowith-gemini-2.5-flash` | flowith/gemini-2.5-flash | Flowith | Gemini |

Diversity policy satisfied: **4 provider surfaces, 5 model families** (≥3/≥4 required).
All six ids liveness-verified 2026-07-04 (flowith via its 800-vote functional history).
Every voter runs VOTER_PROMPT v2 (WS2), which the smoke round confirmed produces
checklist-citing rationales on all five families.

### Dead-id remediation (landed with this profile)

| Change | Reason |
|---|---|
| `cerebras/llama3.1-8b` → `cerebras/gpt-oss-120b` in all 7 profiles | Old id returns model_not_found (probed); it was the chain's #1 voter by volume — every default-profile round was silently one voter short |
| `groq-llama-4-maverick` removed from diverse-max | 760/760 chain votes are NotFoundError |
| `flowith-gpt-4o`, `flowith-claude-sonnet-4` removed from diverse-max | 785/785 error-votes each |

Test expectations updated; suite 147/147 green.

## 3. Acceptance evidence (success criterion)

Live round, 2026-07-04, `post-window` profile, synthetic Local CodeChange claim:
6/6 voters returned real votes (zero `[voter error]`), outcome **APPROVED**,
mean **+0.642**, variance **0.007**, 25.1s, **zero Fable 5 / Anthropic calls**
(roster contains no such surface by construction). Weights ranged 0.55–0.80 —
inside the v2 calibration band for a routine clean claim, no rubber-stamp
clustering. The packet's formal criterion ("one full round post-window")
re-runs this after day 7; mechanics are proven now.

## 4. Escalation criteria — what earns a Fable 5 credit

Post-window, Fable 5 is invoked **only** when a trigger below fires. Everything
else runs on the successor roster.

| # | Trigger | Threshold | Fable task |
|---|---|---|---|
| E1 | **Consensus CONFLICT** at System/Substrate radius | `variance > θ_polarization` (0.40 / 0.25) on a governed claim | Adjudication memo: name the crux, propose the smallest decidable sub-claim |
| E2 | **Persistent deadlock** at Substrate | DEFERRED twice consecutively on the same claim (\|mean\| inside the dead band) | Same as E1 |
| E3 | **Security-sensitive diff** | Touches integrity zomes, consent semantics (ADR-12 surface), hashline, or provenance validation paths | One adversarial review pass pre-merge |
| E4 | **Eval regression** | Any WS1 module dev-split score drops > 10 percentage points after a prompt/roster/model change | Root-cause + revised artifact |
| E5 | **ADR-tier decision** | New ADR, or supersession/amendment of an Accepted ADR | Adversarial review of the draft (not authorship) |

**Non-triggers (explicitly):** routine claim voting, doc summaries, intake
digestion, any task a retained model already meets the WS1 ≥80% rubric bar on,
and anything whose only justification is "want a better answer."

**Budget:** `FABLE5_WEEKLY_CREDIT_BUDGET = ⟨Anthony sets⟩` credits/week, hard
cap. When exhausted mid-week, triggers queue to next week (E3 security items
jump the queue). Every escalation is logged as a source-chain claim tagged
`escalation_trigger: E<n>` with the credit cost — the log is the dataset for
revising this table after month one.

## 5. Recommended follow-up (out of WS5 scope — needs its own claim)

**Error votes must stop counting toward quorum.** Today a voter exception is
recorded as `weight 0.0` + `[voter error]` rationale, which *satisfies quorum*
and dilutes variance — the WS2 audit shows rounds where most "votes" were
errors. Proposal (gateway-semantics change, Module radius, small diff in
`decide()`/vote collection): exclude votes whose rationale carries the error
marker from both quorum count and tally statistics; a round below quorum after
exclusion returns DEFERRED with reason `insufficient_live_voters`. This is a
consensus-semantics change → route as its own claim with tests, not a config edit.

## 6. Sprint bookkeeping

Doc **4 of 6**. Config diff: `voter_registry.json` + 3 test expectation lines.
Orient self-audit: T2 (registry + voters.py roster code + liveness probes);
no `_reference/`; roster change is config per packet scope; source chain
untouched (smoke round used pure `tally()`, no chain write).
