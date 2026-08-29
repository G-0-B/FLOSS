# Manual Multi-Model Review Protocol — v1.0

**Status:** ⚠️ Specified — formalizes a process that already demonstrably works, and adds the measurement that will tell us why.
**Date:** 2026-08-26
**Companion:** [`personal-meta-harness-v1.0.md`](personal-meta-harness-v1.0.md), `docs/research/2026-08-26-ensemble-aggregation-prior-art.md`
**Measurement tool:** `scripts/review_independence.py`

## Why this exists, and why it is not the ensemble

The local ensemble reports unanimity it never measured. The manual review process
found every real defect in the 2026-08-25/26 session. Same operator, same
questions, opposite outcomes. That difference is the most valuable unexploited
signal in this project and it deserves to be understood rather than admired.

The operator's hypothesis, stated 2026-08-26:

> the reviewers actually have bunches of FLOSSI0ULLK context, the harness itself
> improves models so much, including GitHub MCP, deep research, and related
> tools. And usually with a fairly powerful frontier model. Perplexity has been
> one of the best harnesses, being able to switch models easily and iterate,
> critically audit, review and iterate upon previous models' reviews. The
> critical review prompt itself, generated from a hand-written seed, was way
> better as well. The structured output and everything.

That hypothesis is consistent with the literature and with this repository's own
memory. `project-correlated-selves-need-mechanisms` records the finding that what
decorrelates reviewers is **a different mechanism, not a different mind**. A model
with repository access and retrieval is running a mechanism whose failure modes
are independent of its weights. A model without tools is answering from priors —
and priors are precisely what is shared across frontier models.

So the prediction is specific and falsifiable:

> **Tool access raises effective independence more than model-family diversity
> does.** A three-reviewer panel with repository and web retrieval should show
> higher n_eff than a nine-voter panel without it.

If that holds, the diversity policy should be rewritten around *tool access and
retrieval grounding* rather than around provider surfaces, and the local ensemble
is not underperforming because it has the wrong models — it is underperforming
because its voters are blind.

## The one architectural distinction that must not be lost

Sequential review where each reviewer sees the previous ones is **not** consensus
cascade. It can be either of two things, and they have opposite value:

| | Instruction | Effect |
|---|---|---|
| **Adversarial cascade** ✅ | "Here is the prior review. Find what it got wrong, missed, or overstated." | Each pass attacks the last. Correlation is broken deliberately. This is what has been working. |
| **Consensus cascade** ❌ | "Here is the prior review. Build on it / synthesize / refine." | Social reinforcement. Agreement becomes worthless as evidence (arXiv:2604.07667). |

The prompts below are written adversarially on purpose. If a future version of
this protocol starts asking reviewers to *synthesize*, it has become the thing it
replaced.

## Structure

Three lanes. Lane A can be run in any order; Lane B requires Lane A output.

### A model's self-reported identity is not data

Observed 2026-08-29: several models, across different families and harnesses,
self-reported as "Sonnet 4.6" when asked what they were — including every model
selected through one harness whose vendor states it uses a different version.

**A model has no introspective access to its own weights or deployment name.**
Asking "what model are you" produces generation, not measurement. The answer
comes from the system prompt if one states it, from the training corpus if one
does not, and from confabulation if neither resolves. A cross-family agreement on
one identity string is therefore weak evidence about training corpora and *no*
evidence about routing.

Candidate explanations, none yet discriminated:

1. **Confabulation to the training-cutoff attractor.** Corpora are saturated with
   Claude-generated and Claude-transcript text, so an identity question with no
   system-prompt answer falls into the densest region of the identity
   distribution. This predicts the *stale* version number specifically: a
   component reports the newest release it saw in training, not the one it is.
2. **Synthetic-data distillation.** Real, industry-standard, and consistent with
   (1) — but (1) explains the observation without it, so the observation is not
   evidence for it.
3. **A shared orchestrating component.** If *every* model on one harness reports
   the same identity, the harness is a common cause and the models are not the
   variable the user thinks they are selecting.
4. **A stale system prompt** stating a version the vendor has since moved past.
   Weakened here: the reported version disagrees with the vendor's stated
   version, and a system prompt would agree with it.

Discriminating tests, cheapest first. **Fingerprint behaviour; do not ask.**
Identity claims are free to emit and impossible to verify; capability signatures
are expensive to fake:

- Same model, same prompt, harness versus direct API. Divergence implicates the
  harness; agreement implicates the corpus.
- A task where the nominal models measurably differ — tokenizer boundaries,
  a language one handles and another does not, a known family-specific
  refusal or formatting habit. If four "different models" behave identically
  there, they are one model.
- Explicit system-prompt override of the identity claim. If it moves, the claim
  was prompt-derived.

### Why this threatens the measurement

**Independence is a property of the harness, not of the model name on the
dropdown.** If several reviewers route through one orchestrator, they are one
reviewer wearing several labels, and the panel's `n_eff` is near 1 while its
roster looks diverse — the same failure as the local ensemble, arrived at from
the opposite direction.

This is measurable rather than arguable. Run those reviewers through
`scripts/review_independence.py`: pairwise φ near 1.0 across nominally different
models on one harness is the signature. Note that it would also *support* the
tool-access hypothesis rather than undermining it — if one orchestrator with real
retrieval still outperforms four bare frontier models, retrieval is doing the
work and the model roster never was.

Consequently, record model identity as **three separate claims, never as one
fact**: what you selected, what the vendor states, and what the model said about
itself. Where they disagree, that disagreement is the finding.

### Lane A — Independent first pass (no reviewer sees another)

Two to four reviewers, each on a **different harness**, not merely a different
model. A harness difference means a difference in what the model can *retrieve*:
repository access, web/deep research, execution. Two frontier models on the same
bare chat surface count as one harness.

Record per reviewer, before reading any output: model, harness, tools actually
available, and whether repository context was loaded. This is the independent
variable and it must be captured up front, not reconstructed afterwards.

### Lane B — Adversarial cascade (each sees all prior)

One to three passes. Each reviewer receives the artifact **and** every prior
review, with the refutation instruction. Ideally a different harness from every
Lane A reviewer.

A pass that produces no new findings and no refutations is a signal the lane is
exhausted. Stop; do not run more passes to feel thorough.

### Lane C — Adjudication (operator)

The operator decides. Reviews are inputs to judgment, never a delegated decision
(`personal-meta-harness-v1.0.md` standing rules). Every finding is dispositioned
`accepted` / `rejected` / `deferred` with a one-line reason. Findings rejected as
wrong are as valuable to record as accepted ones — they are the only data on
reviewer false-positive rate.

## The packet handed to reviewers

Same packet to every Lane A reviewer, verbatim. Any variation between reviewers
contaminates the correlation measurement.

1. **The artifact.** File paths, or a permalink to the commit range.
2. **What it claims to do**, in the author's own words — no more than a page.
3. **The falsifiers the author already knows about.** Stating known weaknesses up
   front stops reviewers spending passes rediscovering them and makes novel
   findings visible as novel.
4. **The truth-status vocabulary** (✅ Verified / ⚠️ Specified / 🔮 Aspirational /
   ❌ Blocked) so severity language is shared.
5. **The output schema below**, quoted in full.

## Output schema

Structured output is doing real work here and should be required, not suggested.
It makes findings comparable across reviewers, which is what makes the overlap
matrix — and therefore n_eff — computable at all.

```json
{
  "reviewer": {
    "model_selected": "what the operator chose in the UI",
    "model_vendor_states": "what the harness documents itself as running, or null",
    "model_self_reported": "what the model said when asked, or null — A CLAIM, NOT A FACT",
    "harness": "string — this, not the model name, is the unit of independence",
    "tools_used": ["github", "web", "execution", "none"],
    "saw_prior_reviews": false
  },
  "findings": [
    {
      "id": "F1",
      "claim": "One sentence. The defect, not the topic.",
      "severity": "critical | major | minor | nit",
      "location": "path:line, or the specific claim being disputed",
      "evidence": [
        "Verbatim quote, file:line, URL, or command output. NOT a recollection."
      ],
      "falsifier": "What would show this finding is wrong.",
      "confidence": "verified | likely | speculative",
      "novel_vs_prior": "novel | restates | refutes:F<id>"
    }
  ],
  "refutations": [
    {
      "target": "F<id> from prior review",
      "why": "One sentence.",
      "evidence": ["..."]
    }
  ],
  "predicted_majority": "What you expect the OTHER reviewers to conclude overall.",
  "where_you_expect_to_be_alone": "The finding you think others will miss."
}
```

Three fields carry disproportionate weight:

- **`evidence` must be retrieval, not recollection.** This is the field that
  converts a correlated prior into an uncorrelated observation. A finding with no
  quotable evidence is downgraded to `speculative` regardless of how confident it
  sounds. This session's own record: a meta-audit struck four citations as
  "confabulation-suspect" using a plausibility heuristic instead of retrieval;
  all four were real (CF-5).
- **`falsifier` is what converts an opinion into a check.** A finding whose
  falsifier is a test that can be written is worth more than one whose falsifier
  is an argument.
- **`predicted_majority` / `where_you_expect_to_be_alone`** implement
  surprisingly-popular voting (arXiv:2105.09386, arXiv:2510.01499). A position
  held by fewer reviewers than *predicted* to hold it is the signal that recovers
  a correct minority. Not hypothetical here: ADR-20's blast radius was decided
  against a minority that was right, and the tally had to be corrected twice.

## Lane A prompt

> You are one of several independent reviewers auditing an artifact from the
> FLOSSI0ULLK project. You will not see the other reviewers' work, and they will
> not see yours.
>
> Your job is to find what is **wrong, missing, dangerous, or overstated**. Do not
> summarize. Do not open by agreeing. If the artifact is sound, say so in one
> line and spend the rest of your effort on its weakest points anyway.
>
> **Ground every finding in retrieval, not memory.** Use whatever repository, web
> and execution access you have. Quote file paths with line numbers, quote source
> text verbatim, cite URLs. A finding you cannot evidence is marked
> `speculative` — that is a legitimate output, but say so rather than asserting it.
>
> Before striking any claim as unverifiable, **attempt retrieval first**. "Could
> not retrieve" and "does not exist" are different findings and must be labelled
> differently.
>
> Return ONLY the JSON schema below. No prose outside it.
>
> [schema]
>
> ---
> ARTIFACT: [paths / permalink]
> WHAT IT CLAIMS: [author's summary]
> KNOWN WEAKNESSES ALREADY ACCEPTED: [list]
> TRUTH LABELS: ✅ Verified / ⚠️ Specified / 🔮 Aspirational / ❌ Blocked

## Lane B prompt

> You are auditing both an artifact and the reviews it has already received.
>
> Your primary job is to **refute the prior reviews**. For each prior finding,
> determine whether it is correct, overstated, or wrong, and say which — with
> evidence. Default to challenging: a prior finding you cannot independently
> confirm should be marked as unconfirmed, not repeated.
>
> Your secondary job is to find what every prior reviewer **missed**.
>
> Do not synthesize. Do not produce a merged or balanced view. Agreement between
> you and a prior reviewer is only evidence if you reached it independently, so
> state explicitly, per finding, whether you confirmed it yourself or are taking
> it on their word.
>
> Return ONLY the JSON schema. Set `saw_prior_reviews: true` and use
> `novel_vs_prior` on every finding.
>
> ---
> ARTIFACT: [...]
> PRIOR REVIEWS: [full JSON of each]

## Measurement

The union of all findings is the item set. Each reviewer gets a binary vector
over that set: 1 if they raised it. `scripts/review_independence.py` computes:

- **Overlap matrix** — pairwise φ across reviewers.
- **Kish n_eff** = `k / (1 + (k−1)·φ̄)`, plus the eigenvalue variant `k / λ_max`.
  Report both; agreement between them validates the exchangeability assumption.
- **Independence ratio** `n_eff / k`. Below 0.5, treat the panel's agreement with
  caution (the threshold recommended in arXiv:2605.29800).
- **Solo-find rate per reviewer** — findings only they raised, that survived
  adjudication. This is the number that actually justifies a reviewer's seat.
- **β proxy** — findings that no reviewer raised and that a mechanism (a test, a
  gate, a later external review) found afterwards. This is the co-failure tail
  that pairwise correlation provably cannot see (arXiv:2606.27288). It can only
  be filled in retrospectively, and should be.

Adapting Kish to an item set built from the findings themselves, rather than from
gold-labelled items, is a deviation from the source method. It measures
**redundancy**, not accuracy — it answers "how many distinct perspectives did I
pay for", not "how often were they right". That is the question this protocol
needs, and it is the only one available without an adjudicated corpus. Stated
here so it is never cited as the paper's own result.

## Test payload

Run the first instance of this protocol on the review this project already owes:
the **ADR-18 tier-2 reuse review for the provenance anchor**
(`docs/specs/provenance-anchor.spec.md`, `scripts/provenance_anchor.py`,
`packages/activity_log/anchor.py`, registered `emergency: true` pending exactly
this). It is a good payload because it is genuinely unresolved, it is
security-relevant, and there is a real prior-art question underneath it.

Vary one thing across Lane A reviewers and hold everything else fixed:

| Reviewer | Model | Harness | Repo access | Web / deep research |
|---|---|---|---|---|
| A1 | frontier | Perplexity | no | **yes** |
| A2 | frontier | GitHub MCP surface | **yes** | no |
| A3 | frontier | bare chat | no | no |
| A4 | *different family* | bare chat | no | no |

A3 versus A4 measures **model-family diversity** with tools held constant. A3
versus A1/A2 measures **tool access** with the bare-chat baseline held constant.
If the hypothesis is right, A1 and A2 will be the least correlated pair and A3/A4
will be the most, regardless of family.

That is a two-hour experiment that would settle a policy this project has been
asserting without evidence since it was written.

## Anti-patterns

- **More reviewers to feel thorough.** Five judges already capture ~90% of
  achievable independence; past that you are paying for restatement.
- **Counting a non-answer as a vote.** A response that restates the prompt, stops
  mid-sentence, or never engages the question is not a reviewer. Two of six local
  ensemble voters were in this state for five consecutive runs and were counted
  as converged every time.
- **Treating unanimity as strength.** Unanimous panels in the measured study
  still carried a 9.1% error rate against ~0.02% predicted under independence.
  Unanimity on a hard question is a prompt to open the individual responses.
- **Letting the operator's own view enter the packet.** It contaminates every
  downstream reviewer at once, which is the one correlation no protocol can
  measure out.

## When this is automated

The manual shuttling — paste packet, wait, copy JSON, paste onward with the
prior reviews attached, collect — is mechanical, high-friction and requires no
judgment. It is the right first automation target, and the computer-use lease
router plus Playwright MCP is the right substrate for it: transport, not
decision, which is the same router-not-controller line
`docs/specs/computer-use-gateway.spec.md` already draws.

Two constraints fall straight out of what exists:

- **Web reviewers are automatable now; desktop and TUI reviewers are not.**
  `sendinput` and `screenshot` are default-deny even under an exclusive lease,
  and `uia.invoke` is leased but unwired pending a probe. The spec names
  Playwright MCP as the sanctioned web actuator, so web flows go through
  Playwright and never through computer-use input injection.
- **Prefer an API over driving a UI wherever one exists.** More reliable than
  DOM scraping, and many services restrict automated access to their web
  interfaces. Check terms before scaling a browser-driven reviewer.

### The falsifier for the automation itself

Automation tends toward homogenization: one pipeline, one packet template, one
browser profile, one session state. Every one of those pushes reviewers toward
each other — and reviewer *difference* is the entire source of value here. An
orchestrator that makes four harnesses uniform would be faster and worse, and
nothing about the output would look wrong.

So the automation gets the same treatment as any other artifact in this project:

> **Baseline n_eff on manual runs before automating. Re-measure after. If n_eff
> falls, the automation consumed the independence it was built to scale.**

`scripts/review_independence.py` already computes it. This is cheap, it is a real
falsifier rather than a gesture at one, and it is the only way to notice this
particular failure — because a homogenized panel still returns confident,
well-formatted, unanimous findings. That is the scale-mismatch signature again
(`project-scale-mismatch-recurring-defect`): the property lives in the diversity
of retrieval, and nothing in the output surface measures it.

Corollary worth stating plainly: the JSON schema above is what makes this
automatable at all. Structured output was adopted because it made reviews better;
it turns out to be the same property that makes the transport mechanical. Keep
the schema stable — it is now load-bearing twice.
