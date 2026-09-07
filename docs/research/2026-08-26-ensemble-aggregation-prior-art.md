# Prior art: multi-model ensemble aggregation

Date: 2026-08-26
Status: ✅ Verified against primary sources (abstracts and full text as noted)
Purpose: ADR-18 reuse-gate evidence for the ensemble replacement, and correction
of two beliefs this repository has been operating on.

## Why this document exists

The ensemble had a measured defect — six syntheses, all reporting
`largest_cluster_fraction = 1.0`, corpus-wide similarity floor 0.791 against a
0.75 threshold — and the response was to start designing a replacement:
per-question ballots, an admission gate, a dissent-preserving tally. That design
was invented from scratch, in a repository whose own ADR-18 gate exists
specifically to stop that, by an agent that had spent the same session hardening
that gate.

This is the search that should have come first. It changes the design.

## The two findings that matter most

### 1. Model-family diversity does not buy independence

This repository's independence policy — "nontrivial polls span ≥3 provider
surfaces and ≥4 model families; same-family endpoints don't count as
independence" — rests on the premise that different families make different
mistakes. That premise has been measured and it does not hold.

Kohli (Apple), *Nine Judges, Two Effective Votes: Correlated Errors Undermine
LLM Evaluation Panels*, arXiv:2605.29800, 2026-05-28. Nine frontier judges
across seven families, three NLI datasets, 100 human annotations per item:

- **n_eff ≈ 2.18** (95% CI [2.07, 2.31]). Nine judges carry about two
  independent votes. Independence ratio 24.2%.
- **The best single judge matches or beats the full panel on every dataset.**
  MNLI 71.8% vs 72.0% panel (within noise); SNLI 84.2% vs 77.7%; AlphaNLI 91.2%
  vs 88.7%.
- **Same-family correlation is barely higher than cross-family.** Same-family
  φ ≈ 0.437, cross-family mean φ = 0.389 — a difference of 0.047. The three
  most-correlated pairs in the entire panel are all *cross-family*:
  Claude×Gemini 0.603, GPT-4o×Claude 0.588, Mistral×DeepSeek 0.564.
- **Restricting to one judge per family made it worse**: 7 judges, best in each
  family, n_eff *falls* to 1.93. The paper's words: "Family diversity alone does
  not recover independence."
- **Unanimity is nearly worthless as evidence.** 9.1% error rate on unanimous
  items, against ~0.02% predicted under independence.
- **Chain-of-thought increases correlation** (n_eff 1.94).
- Better aggregation does not rescue it: Dawid-Skene EM and accuracy-weighted
  voting close **at most 11%** of the gap *even with oracle access to gold
  labels*. "The bottleneck is correlated judges, not the aggregation algorithm."

The repository's diversity rule is therefore doing less than it claims. It is
not worthless — it is a cheap proxy that rules out the most obvious redundancy —
but it must stop being cited as establishing independence, and "≥4 families,
therefore independent" is not a valid inference.

### 2. Free-form answers are the worst case, and pairwise correlation cannot see it

Chen, *When Does Combining Language Models Help? A Co-Failure Ceiling on
Routing, Voting, and Mixture-of-Agents Across 67 Frontier Models*,
arXiv:2606.27288, 2026-06-25.

- For any policy whose output is one member model's answer, accuracy cannot
  exceed **1 − β**, where β is the rate at which *every* model is wrong on the
  same query. β is the ceiling, and the field rarely reports it.
- **Mean pairwise error correlation ρ cannot identify β.** Error laws with
  identical marginals and identical pairwise correlations can have different
  all-wrong rates. So a correlation-based diagnostic — including the Kish n_eff
  above, and including this repository's similarity-floor check — is necessary
  but not sufficient.
- Across 67 models from 21 providers, a calibrated single-factor model
  **underprices the all-wrong tail by ~2.5×** on open-ended mathematics
  (observed β 0.052 vs 0.023 modelled, 90% CI 1.7–3.4×). Execution-graded code:
  β 0.079.
- **Answer format, not subject, drives co-failure.** Re-asking the *same*
  GPQA-Diamond questions in free-response rather than multiple-choice form
  reopens the tail: β 0.127.
- "On checkable tasks in our pool, combining models rarely beats the single best
  model without a strong query-level routing signal. **Gains come from models
  failing on different questions, not from adding more models.**"

Every poll this repository runs is free-response prose on unresolvable
architecture questions. That is precisely the regime with the highest measured
co-failure and no ground truth to route on.

## Established methods, with the reuse ladder applied

| Method | Reference | Fit here | Ladder |
|---|---|---|---|
| **Universal Self-Consistency (USC)** | Chen et al., arXiv:2311.17311 | Uses an LLM to select the most consistent answer among candidates. Designed exactly for free-form answers where answer extraction fails — our case. Matches standard self-consistency without needing similar answer formats. | **adopt** — closest single replacement for embedding clustering |
| **Mixture-of-Agents (MoA)** | Wang et al., arXiv:2406.04692 | Layered propose-then-aggregate. 65.1% AlpacaEval 2.0 with open models vs GPT-4o 57.5%. Implementation on PyPI as `mixture-llm`. | **adopt/extend** — but see Self-MoA caveat below |
| **LLM-Blender** (PairRanker + GenFuser) | Jiang et al., arXiv:2306.02561, ACL 2023 | Pairwise ranking then generative fusion. `pip install llm-blender`, GitHub `yuchenlin/LLM-Blender`. Requires a trained ranker. | **evaluate** — heavier than we need |
| **Optimal Weight (OW) / Inverse Surprisingly Popular (ISP)** | Ai et al., arXiv:2510.01499 | Training-free aggregation using first- and second-order information; provably mitigates majority-vote failure under mild assumptions. Descends from surprisingly-popular voting (Prelec), which recovers ground truth *even when experts are in the minority*. | **adopt** — directly targets our failure mode |
| **Surprisingly Popular voting** | Hosseini et al., arXiv:2105.09386 | Elicit each voter's answer *and its prediction of others' answers*; the option that beats its predicted popularity wins. Extended to rankings. | **adopt** — one extra prompt field |
| **Kish n_eff panel diagnostic** | arXiv:2605.29800 §3.3 | `n_eff = k / (1 + (k−1)·φ̄)` over binary error vectors; eigenvalue variant `k / λ_max`. Recommended as a **standard panel diagnostic**, with "if n_eff/k < 0.5, treat results with caution". | **adopt** — replaces our ad-hoc metric with a citable one |
| **Co-failure rate β + Clopper-Pearson bound** | arXiv:2606.27288 | Finite-sample certificate on the largest gain any voting scheme could deliver, computable *before* building the aggregator. | **adopt** — tells us whether a panel is worth running at all |

Live research specifically on preserving rather than collapsing disagreement,
which is what this repository actually wants:

- *Preserving Disagreement: Architectural Heterogeneity and Coherence Validation
  in Multi-Agent Policy Simulation*, arXiv:2604.26561 — names "artificial
  consensus" as the failure mode.
- *Beyond Consensus: Trace-Level Synthesis in Mixture of Agents*,
  arXiv:2605.29116 — compressing each agent's reasoning into a vote or a layered
  synthesis loses the thing worth having.
- *Minority Sentinel: When to Overturn Majority Voting in Multi-Agent LLM
  Debates*, arXiv:2606.29270 — majority voting rests on the Condorcet
  independent-errors assumption, which does not hold.
- *From Debate to Decision: Conformal Social Choice for Safe Multi-Agent
  Deliberation*, arXiv:2604.07667 — "agreement among agents is not evidence of
  correctness"; consensus-based stopping rules are unsafe when agents converge
  through social reinforcement.
- *Consensus is Strategically Insufficient: Reasoning-Trace Disagreement as a
  Knowledge-Representation Signal*, arXiv:2606.04223.
- *The Cost of Consensus: Isolated Self-Correction Prevails Over Unguided
  Homogeneous Multi-Agent Debate*, arXiv:2605.00914.
- *When Agents Disagree: The Selection Bottleneck in Multi-Agent LLM Pipelines*,
  arXiv:2603.20324 — heterogeneous MoA beats single models, homogeneous Self-MoA
  beats heterogeneous MoA; the contradiction is a selection problem.

## What this changes about the planned replacement

The ballot design was not wrong, but it was aimed at the wrong layer and it was
being invented rather than adopted.

**Keep, now with a citation instead of a hunch.** Eliciting structured positions
per question rather than clustering whole responses is the right direction — it
is what makes USC, OW/ISP and surprisingly-popular voting applicable at all.
Free-form prose is the format with the measured worst co-failure
(arXiv:2606.27288), so changing the elicitation format is a substantive
intervention, not cosmetics.

**Drop.** A hand-rolled agreement metric. `separation_diagnostics()` measures
whether the clustering threshold sits inside the observed similarity spread,
which is a real defect detector but an invented one. The literature's diagnostic
is n_eff, and the honest reading of arXiv:2606.27288 is that even n_eff is
insufficient — β is the quantity that bounds the achievable gain.

**Add, and this is the important one.** A diagnostic that can conclude *do not
run a panel*. Both papers point the same way: the best single judge frequently
beats the panel, adding judges past ~5 yields nothing, and gains come from models
failing on different questions rather than from more models. Nothing in the
current design can ever return "one strong model would be better here", and it
should be able to.

**Add.** Surprisingly-popular elicitation. One extra field per voter — *what do
you predict the others will say* — and the aggregation can recover a correct
minority position. On this repository's record that is not hypothetical: the
ADR-20 blast-radius question was decided against a minority that was right, and
the correction had to be made twice.

## Honest limits of this survey

- **Search, not systematic review.** Two discovery passes plus targeted arXiv
  queries. No exhaustiveness claim.
- **Abstract-level for most entries.** arXiv:2605.29800 was read in full;
  everything else is abstract plus the discovery snippet. Nothing here has been
  reproduced.
- **Transfer is unproven.** Both headline papers measure classification and
  preference tasks with gold labels. This repository asks unresolvable
  architecture questions with no ground truth, where β and n_eff cannot be
  computed without an adjudicated corpus. arXiv:2605.29800 names this explicitly:
  "The degree of inter-judge correlation may differ on open-ended generation
  evaluation or code review." The direction of the finding is very likely to
  transfer — arXiv:2606.27288's free-response result argues it gets *worse* —
  but the magnitude here is unmeasured.
- **This does not by itself satisfy ADR-18 tier 2.** It is a prior-art record
  gathered by one agent of one model family. The reuse gate's independent-review
  requirement is a separate obligation and remains outstanding — and, per finding
  1 above, that requirement's own independence premise now needs revisiting.

## The reusable lesson

The gate this repository built to prevent reinvention did not fire, because
nothing consults it at the moment a design starts — only at the moment a file is
registered. A reuse gate that runs at registration time catches the artifact and
misses the decision.

Recorded in the failure-mode register as CF-7.
