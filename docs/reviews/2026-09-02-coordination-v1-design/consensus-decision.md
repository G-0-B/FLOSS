# Consensus decision record — coordination v1, M1 (Module)

**Recorded:** 2026-09-03 by Claude Opus 5 (Claude Code session), at operator direction to split the
claim and submit M1 at Module radius.

## Outcome

| | |
|---|---|
| `claim_id` | `01a06941-9ba6-7421-97ef-e7b2dc26824c` |
| `entry_hash` | `3be18963fcd7ae20c590847cd723830440a2b186d385afa289057dc1253bdf1a` |
| proposer | `claude-opus-5-coord-v1` |
| proposal type / radius | `SpecChange` / `Module` |
| **outcome** | **`DEFERRED`** |
| tally mean | `0.2875` (Module APPROVE threshold `0.50`) |
| tally variance | `0.08297` |
| decided at | `2026-09-03T21:51:59Z` |

**M1 is NOT approved. Task 1 does not start.** The plan's gate is unmet.

## Evidence submitted

- `FLOSS/docs/superpowers/specs/2026-09-02-coordination-v1-design.md` (spec)
- `FLOSS/docs/superpowers/plans/2026-09-02-coordination-v1.md` (spec)
- `c1a08f1e528dc29fa885c2d71b04908b4f90f345` (commit — design + plan at submission)
- `ff1f5c0201399d48f6be1d7c221cd41bacff7cf5` (commit — DELTA-4, the radius-split argument)
- `FLOSS/docs/reviews/2026-09-02-coordination-v1-design/cas-proof-report.md` (test)

## Why Module, and why that is not a bypass

`_is_governed_claim` (`packages/metacoordinator_mcp/tools.py`) gates System/Substrate crossed with
AdrChange/ConfigChange/SpecChange, so Module does not reach the provenance requirement. M1 was
submitted at Module because M1's actual radius is Module — one read-only module plus one rendered
section in an existing script, writing nothing, exposing no interface other components consume,
reversible by deleting a file.

**M2 and M3 remain System and remain BLOCKED.** ADR-12's `consent_ref.decision_action_hash` anchor
is undefined; `entry_has_consent` (`packages/activity_log/provenance.py:1414`) checks only that the
field is a non-empty string and resolves nothing. No placeholder anchor was created, requested, or
implied. The prohibition on substituting a commit SHA or session id stands untouched.

## The votes, and why this outcome should not be read as a judgment

| voter | weight | note |
|---|---|---|
| `groq-gpt-oss-120b` | **+0.60** | all checklist items pass; radius matches the change |
| `huggingface-deepseek-v4-flash` | **+0.55** | evidence, radius, truth-status pass; governed gate not applicable at Module |
| `mistral-devstral-small` | `0.0` | **`[voter error]`** — OmniRoute HTTP 400, `devstral-small-latest` not in the active live catalog |
| `nvidia-nemotron-super-49b` | `0.0` | **`[voter error]`** — OmniRoute HTTP 400, `nvidia/llama-3.3-nemotron-super-49b-v1` not available |

**Both voters that actually ran approved.** Their mean is `0.575`, above the Module threshold of
`0.50`. The recorded mean is `0.2875` because the two provider failures were tallied as votes of
zero.

The mechanism, verified in source:

- `packages/metacoordinator_mcp/voters.py:355` and `:426` append a failed voter as
  `Vote(weight=0.0, rationale="[voter error] ...")`.
- `packages/orchestrator/consensus_gate.py:51` computes `weights = [v.weight for v in votes]`,
  `n = len(weights)`, `mean = sum(weights) / n`.

So an unreachable provider is arithmetically indistinguishable from a voter that ran and returned
neutral. It lowers the mean toward zero **and** raises `n` for the quorum check — wrong in both
directions at once. **Infrastructure failure is being scored as disapproval.**

This is not a new condition. The 2026-08-24 campaign ran with two of six voters non-functional
throughout, and the ensemble's unanimity was consequently unmeasured
(`docs/research/2026-08-29-cross-audit-learnings.md`).

## Two further problems with this round

1. **It routed through OmniRoute.** The plan's Task 0 states voter rounds use
   `FLOSS_MODEL_BACKEND=litellm`, never OmniRoute. Both failures are OmniRoute HTTP 400s, so the
   round did not honour its own stated routing.
2. **It fails the project's diversity policy.** Two functional voters means two provider surfaces.
   Nontrivial polls require at least three provider surfaces and four model families; same-family
   endpoints do not count as independence.

## What was deliberately not done

- **The round was not re-run.** `run_consensus_round` is idempotent and returns `E_ALREADY_DECIDED`,
  but the point stands independently: re-running a decided claim after seeing an unfavourable
  number is outcome shopping, and the fix for a broken voter roster is to fix the roster, not to
  poll until it reads better.
- **The recorded outcome was not reinterpreted.** `DEFERRED` is what the chain says. The analysis
  above explains the number; it does not replace it.

## Recommended next step, for the operator

Repair the roster, then submit a **new** claim — not a re-run of this one. Either drop the two
unavailable models from the active profile, or point them at models present in the live catalog, so
a round reflects opinions rather than availability.

The scoring defect deserves its own fix independent of this claim: a failed voter should be
excluded from the tally and reported as an absence, not recorded as a zero. As written, any
provider outage biases every decision toward `DEFERRED`, and a large enough outage could push a
genuinely approved claim below threshold without a single voter disagreeing with it.
