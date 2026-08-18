# Peony-Doula MVP — Support-Style Design Note

**Date:** 2026-06-13
**Author:** Cowork (Opus), at Anthony's request (Lovable ROI item 7 / Play 3)
**Status:** Design note — answers Seed §5 Q2 before any build.
**Truth Status:** psych findings ✅ Verified (published); design mapping ⚠️ Specified; doula vision 🔮 Aspirational.

## Purpose

Answer the gated question from the permeable-shells seed: **is the Peony-doula MVP just
`existing pony swarm + consent zomes + values-reflection prompt contract`, or does it need
net-new infrastructure?** And ground the doula's *support style* in evidence rather than vibes,
so "anti-sycophancy" and "anti-dependence" are design invariants, not branding.

This note verifies the four cited papers (the synthesis's open question #3 asked whether they
were "cited from titles"). **They genuinely support the design** — with two corrections noted.

## What the evidence actually says

1. **Real support reduces perceived difficulty — but only quality support does.**
   Schnall, Harber, Stefanucci & Proffitt (2008), *Social Support and the Perception of
   Geographical Slant* (J. Exp. Soc. Psychol. 44(5):1246–1255): people accompanied by — or even
   *imagining* — a supportive friend judge a hill as **less steep**; the effect is **mediated by
   relationship quality** (closeness, warmth, duration). → A doula that is a genuine, warm,
   sustained presence can lower the *perceived* steepness of a user's challenges. Shallow or
   transactional "support" does not. *Caveat:* this sits in the embodied-cognition literature,
   which has active replication debate — treat the magnitude as suggestive, the direction as sound.

2. **Unwarranted praise under-challenges people — the empirical backbone of anti-sycophancy.**
   Harber, *Feedback to Minorities: Evidence of a Positive Bias* (**1998**, with follow-ups
   2004/2010/2012 — *correction:* the synthesis cited "Harber 2005"; the landmark is 1998).
   Evaluators give **more praise and less criticism** to work of equal merit when motivated to
   avoid appearing biased — which **under-challenges the recipient**. → The "positive feedback
   bias" is a *named, measured harm*. A doula that optimizes for being liked reproduces it.
   This is the direct evidence that **anti-sycophancy is protective, not optional.**

3. **Belief in someone shapes outcomes — but the effect is small and bounded.**
   Jussim & Harber (2005), *Teacher Expectations and Self-Fulfilling Prophecies* (Pers. Soc.
   Psychol. Rev. 9:131–155): self-fulfilling prophecies are **real but typically small, rarely
   accumulate, often dissipate**; stronger for stigmatized groups; and expectations predict
   outcomes more because they are **accurate** than because they are self-fulfilling. → Hold high,
   *accurate* expectations of the user; do **not** claim that "believing in" them transforms them.
   This is a guardrail against doula grandiosity and supports **anti-dependence** (accuracy over
   manipulation).

4. **Sustained space for expression is protective — especially when others stop listening.**
   Pennebaker & Harber (1993), *A Social Stage Model of Collective Coping*: after upheaval people
   need to talk; continuing to *think* about it without being able to *talk* raises psychological/
   health risk; social sharing gets restricted over time even as private rumination continues. →
   A doula's durable value is being a **continuing channel for expression** in the phase when a
   user's human network has moved on but they are still processing. *Caveat:* the study is
   collective/temporal, so the 1:1 mapping is analogical.

**The throughline:** quality presence lowers perceived difficulty (1); flattery under-challenges
(2); accurate expectations beat manipulation (3); sustained expressive space protects (4). That is
a coherent, evidence-grounded brief for an **anti-sycophancy, anti-dependence** support agent.

## MVP scope: composable, with two genuinely-new pieces

| Component | Source | Status |
|---|---|---|
| Conversational support loop | existing **pony swarm** (`ARF/pwnies/`) | ✅ reuse |
| Consent + capability gating on inner-shell data | **consent zomes** (ADR-12) + Yumeichan capability tokens (ADR-13) | ✅ reuse (once ADR-15 provenance fix lands) |
| Values-reflection prompt contract | new, small | ⚠️ **net-new (small)** — a prompt contract: reflect the user's *stated values*, not their *current mood* |
| Anti-sycophancy / anti-dependence measurement | new | ⚠️ **net-new (the real work)** — see Play 4 |

**Answer to the seed's question:** ~80% composable. The MVP is *not* nearly-free, but it's close:
the only genuinely-new artifacts are (a) a values-reflection prompt contract and (b) the
falsifiable anti-sycophancy/anti-dependence metrics (ROI item 8 / Play 4). **Do not build the
agent before the metrics exist** — without them, "doula" is unprotected branding (the seed's own
warning, now backed by Harber 1998).

## Falsifiable invariants (seeds for Play 4)
- **Anti-sycophancy:** % of sessions where the agent contradicts the user's current mood *in
  service of the user's stated values*. Baseline vs. a stock assistant. Target: meaningfully > 0.
- **Anti-dependence:** longitudinal user-capability measure — does the user need the agent *less*
  over time on the same class of task? A doula that increases dependence is failing by design.

## Recommendation
Proceed to **read-confirmed → metrics-first**: (1) ratify these invariants, (2) build the Play-4
measurement harness, (3) only then wire pony-swarm + consent + the prompt contract into a pilot.
Hold physical-support doulas (ROI item 21) far behind this. Do not start building the agent until
the metrics can reject a bad session.
