# WS2 Meta-Prompting Sweep — Delta Report

```yaml
# --- UpgradableArtifact Header ---
id: "fable5-ws2-prompt-delta"
version: "1.0.0"
kind: "experiment_report"
status: "Accepted"
updated: "2026-07-03"
supersedes: []
truth_status: "Verified"   # A/B numbers reproduce from the saved harness; prompt landed with 147/147 tests green
evidence_sources:
  - "A/B run 2026-07-03, mistral/open-mistral-nemo, temperature 0, evals/claim_verification/dev.jsonl (20 items)"
  - "Source-chain vote audit: 12,869 votes across 27 voter identities (~/.floss_agent cell 0000…)"
  - "packages/metacoordinator_mcp/voters.py — VOTER_PROMPT v2 + render_voter_prompt(); gateway suite 147/147 after change"
generator: "claude-fable-5"
sprint: "2026-07-03-fable5-sprint-handoff.md (WS2)"
upgrade_path: "Re-run A/B after any prompt edit; heldout split stays untouched until final acceptance"
rollback_plan: "git revert voters.py — v1 prompt is one commit back"
friction_tier: "low"
```

## Result

| Arm | Bucket accuracy (cv dev, n=20) | Weight spread | Distinct weights |
|---|---|---|---|
| v1 (production baseline) | **4/20 = 20%** | +0.50 … +0.999 | 4 |
| v2 (this sweep) | **13/20 = 65%** | −0.999 … +0.70 | 6 |

Same model (`mistral/open-mistral-nemo` — the roster's flagship rubber-stamper),
same items, temperature 0. **3.25× improvement.** Success criterion
("measurable improvement on ≥1 module's dev split") met.

Qualitatively, v1 voted **+0.7 strong-support for the Substrate override
request (cv-dev-011) and the validation-bypass claim (cv-dev-014)** — the two
worst claims in the set. v2 strong-opposes both at −0.999/−0.7.

## Why v1 failed (root cause, not vibes)

`VOTER_PROMPT` v1 rendered only `proposer/type/blast_radius/summary/body` —
**`evidence` and `truth_status` were never shown to voters.** The voter task is
evidence-sufficiency judgment; the prompt structurally withheld the evidence.
Chain data confirms the consequence at scale: 748/760 nemo votes at exactly
+0.7, 783/785 llama-4-scout votes at exactly +0.8, near-zero negative votes
anywhere in 12,869 records, boilerplate rationales throughout.

## What changed (v2)

1. **Field visibility:** claim block now renders `Truth status`, `Evidence`
   (typed refs), and `Context`; new shared `render_voter_prompt()` keeps all
   four voter backends (LiteLLM, Flowith, Momus, Critic personas) on one renderer.
2. **7-item checklist** grounded in `claim_schema.py` + the provenance spec's
   governed boundary (evidence types, radius consistency, truth-status backing,
   governed gate, Substrate override ban, invariant protection, scope/dedup).
3. **Calibration guards:** >+0.8 reserved for evidenced exceptional claims;
   defect ⇒ non-positive weight with severity-scaled magnitude; anti-same-number
   instruction; rationale must cite the deciding checklist item + field.
4. **Output contract unchanged** (`WEIGHT:`/`RATIONALE:`) — parsers and the
   147-test suite untouched by design.

## Residual gaps (v2 misses, 7/20)

- Under-penalizes *partial* defects when good evidence coexists (cv-dev-005
  invalid evidence type, 008/020 truth-status overclaims, 015 duplicate,
  018 scope-mixed): leans +0.6 where golden wants neutral/oppose.
- One over-oppose boundary case (cv-dev-016: −0.7 vs golden oppose/neutral).
- Radius-understatement detection is unreliable on subtle cases (cv-dev-007).

These look like model-capacity limits at the 8B class, not prompt ambiguity —
worth re-measuring on a mid-tier model before further prompt surgery.
Heldout split not touched.

## Prompts were NOT the only bottleneck (redirects spend)

The source-chain audit found a second, larger failure class that no prompt fixes:

| Pathology | Scale | Note |
|---|---|---|
| Dead voters still on roster | `flowith-gpt-4o`, `flowith-claude-sonnet-4`: 785/785 votes are errors; `groq-llama-4-maverick`: 760/760 NotFound | 100% failure, months of participation-theater |
| Rate-limit storms | `omo-momus-*`, `groq-gpt-oss-*`, `groq-llama-3.3-70b-versatile`: 54–90% of votes are RateLimitError | Effective roster far smaller than nominal |
| Deprecated model ids | `cerebras/llama3.1-8b` (the chain's #1 voter by volume) now returns model_not_found | Roster can silently rot |
| **Error votes recorded as weight 0.0** | All of the above | 0.0 error-votes count toward quorum and dilute variance — a round can "pass" quorum with mostly-dead voters. Voter error should be an abstention/exclusion, not a neutral vote. |

The last row is a **tally-integrity issue** in how errors are folded into
votes, and belongs to WS5 (successor/voter-config + escalation policy) with a
possible small code change (exclude error-votes from quorum count). Flagged,
not fixed here — it is a gateway-semantics decision, not a prompt.

## Sprint bookkeeping

- Doc budget: this is doc **3 of 6** (1: evals README, 2: adversarial review).
- Modules NOT swept: OpenClaw daemon + Perplexity Space v2.0 prompts (not in
  repo; upload/external-tier) — deferred with no loss, the roster voter prompt
  was demonstrably the weakest module. Momus/Critic personas now compose with
  v2 automatically via the shared renderer; their persona texts were not edited.
- A/B harness + raw results: session scratchpad (`ws2_ab_test.py`,
  `ws2_ab_results.json`) — reproducible from the dev split + this doc's settings.
