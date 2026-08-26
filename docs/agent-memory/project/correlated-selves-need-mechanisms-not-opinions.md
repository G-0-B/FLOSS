# Correlated selves need mechanisms, not more opinions

**Date:** 2026-08-26
**Status:** ✅ Verified for model panels (arXiv:2605.29800, 2606.27288); ⚠️ Specified for the sequential-self case
**Related:** `docs/research/2026-08-26-ensemble-aggregation-prior-art.md`, `docs/governance/personal-meta-harness-v1.0.md`

## The measured result

Nine frontier LLM judges across seven model families carry about **two
independent votes** (Kish n_eff = 2.18). The best single judge matches or beats
the whole panel. Restricting to one judge per family made independence *worse*
(n_eff 1.93). Same-family error correlation is barely above cross-family — 0.437
vs 0.389 — and the three most-correlated pairs in the panel were all
cross-family. Better aggregation closes at most 11% of the gap even with oracle
labels. The bottleneck is the inputs, not the algorithm.

## The transfer that matters here

`personal-meta-harness-v1.0.md` already records that multi-agent coordination and
multi-operator-across-time coordination are structurally identical — same
architecture, different scale. If that identity holds, the correlation finding
transfers, and it is unflattering:

- **Me-now and me-after-compaction are near-perfectly correlated voters.** Same
  weights, same prompt, same repository. "Have a fresh session double-check it"
  buys close to n_eff = 1. It feels like a second opinion and is not one.
- **Anthony-today and Anthony-Tuesday are highly correlated too.** The Consensus
  row of the personal harness is therefore its weakest row, for a measurable
  reason rather than a stylistic one.
- **What actually decorrelates is a different *mechanism*, not a different mind
  or a different day.** A test, a gate, an external anchor, a compiler, a
  third-party mirror. These fail for reasons unrelated to any agent's weights or
  mood, so their errors are genuinely independent of ours.

This session is its own evidence. Every real defect was found by an external
review or a mechanism. None was found by a fresh agent reasoning again about the
same code — including when that agent was told to be adversarial.

## What this predicts about durable memory

Across the compaction boundary in this session, what transferred usefully was
**self-enforcing**: failing tests, blocking gates, named failure modes with
instance counts, commit messages carrying the *why*. What did not transfer was
**prose requiring a reader**: intentions, plans, next-step lists — those had to be
re-derived.

So "save everything" is the wrong rule, and the repository's own doc-explosion
history (dominant failure mode across three iterations) already said so. The
sharper version:

> **Save what enforces itself. Index what does not. Prune the rest.**

A test is a memory that reads itself. A doc is a memory that needs a volunteer.
Both are worth having; only one survives an agent who is in a hurry.

## Do not

Read this as "panels are useless" or "don't ask for review". Panels caught real
things here. Read it as: **agreement is not evidence, a second opinion from a
correlated source is not independence, and the strongest thing you can build for
your future self is a constraint rather than a note.**
