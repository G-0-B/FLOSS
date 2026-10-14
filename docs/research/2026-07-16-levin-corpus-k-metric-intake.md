# Levin-Corpus K-Metric + StatefulAgent — Intake & Deferral Note

- **Status:** Plane A intake. **Not canon. No adoption.**
- **Date:** 2026-07-16
- **Author:** claude-fable-5 (single-author chat synthesis; see provenance caveat)
- **Kind:** Comparison-only / deferral note (house register, cf. `2026-07-07-holo-rbi-synthesis-delta.md`)
- **Lineage:** extends `2026-06-08-instruction-and-levin-handoff-synthesis.md` and the Levin brief lineage relocated in the 2026-06-08 root-intake pass.

## What this records

A 2026-07-16 in-conversation Claude synthesis chain produced four artifacts (never landed on disk):
`LEVIN-CORPUS-INTEGRATION-BRIEF` v0.1 → v0.2, a "Finite Observation Framework" integration, and an
"Architecture Agent" response that self-labeled its output **GREENLIT**. The chain proposes:

1. **K-metric adoption.** `K = log10(tau_blind / tau_agent)`, borrowed from the Levin-corpus *Training
   Ecosystems* (Samanta, Hazan & Levin) Lotka-Volterra study and the *Cognition All the Way Down 2.0*
   P+K formalism, as FLOSSI0ULLK's **primary** substrate-neutral benchmark for coordination/learning
   capacity. For an LLM agent, `tau_blind` = expected cost of uniform-random selection over the valid
   action space; `tau_agent` = measured cost of the learned policy.
2. **StatefulAgent + Phase-1 sequencing.** A stateful agent (context retained across perturbations) plus
   a random-policy sampler, on the argument that habituation (declining `tau_agent` over repeated
   perturbations) is unmeasurable without cross-trial state — therefore memory *must* enter Phase 1.
3. Supporting engineering: consensus-based uncertainty quantification (no LLM self-report),
   probabilistic-trigger red-team checking, structural (not siloed-DB) meta-memory.

## Assessment (single-author; NOT a verdict of record)

The engineering translations are **plausible and worth keeping as an exploratory proxy**, but two
load-bearing claims are unverified and must not proceed to an ADR as-is:

- **CLAIM 1 (K as *primary*) is over-committed.** Transferring a metric from a 2-species ODE simulation
  to an LLM consensus network is an analogy, not a validated mapping. `tau_blind` as uniform-random
  action selection is a defensible *baseline* but its cost units (latency + tokens + error rate) are not
  commensurable with the simulation's recovery-time `tau` without argument. Treat K as **one candidate
  proxy among several**, not the primary benchmark.
- **CLAIM 2 conflates layers.** "The *simulation* needs cross-trial state to exhibit habituation" does
  not entail "the *production substrate* needs stateful memory built in Phase 1." The measurement
  harness needs state; the substrate sequencing is a separate decision that should not be forced by the
  metric's measurement requirements.

## Unverified figures (blocking — none checked against the actual paper in-repo)

- 90.6% recovery-time-sensitization / magnitude-habituation asymmetry
- 0.5% vs 5% noise thresholds (discrete number-learning fragility vs. trend robustness)
- 98.1% UMAP off-grid classification accuracy
- 3.1% number-learning / 30% sensitization prevalence over the ~220k-combination sweep

The source PDF is not open in-repo. These are load-bearing for any downstream design claim and are
recorded here as **claims, not facts**.

## Provenance caveat (the reason this is a deferral, not an adoption)

The proposal chain carried **zero source-chain provenance** and **self-graded its own output GREENLIT** —
precisely the sycophantic self-assessment the proposal itself warns against. Per the anti-sycophancy
mandate and the durable-provenance requirement, self-labeled greenlights do not constitute a decision.

### Adjudication trail (2026-07-16)

- **Reasoning ensemble (local Ollama voters): could not reach quorum — `tier=degraded` on all 3 attempts.**
  Ollama itself was healthy (9 models resident incl. all 4 voters + `mxbai-embed-large`). Root cause is
  **parallel-dispatch VRAM contention** on the laptop 4090: the ensemble fires 4× 3B voters + the embed
  model concurrently, which exceeds VRAM, so voters evict each other mid-load (`HTTP 500 embed_failed`) or
  stall (`TimeoutError`). Embedding yield across attempts: 0/4 → 1/4 → 0/4 (need ≥3 for cluster-based Tier
  classification). **No formal ensemble verdict exists.** Sub-quorum signal only: the two voters that did
  produce text (llama3.2-3b, granite-code-3b) both counseled *do not proceed without independent
  verification* and were skeptical of Claim 1 (K-as-primary) — directionally consistent with the consensus
  REJECTION below, but below the quorum threshold and therefore not a decision of record.
- **Consensus gateway (external voters): REJECTED the deferral claim on form.** Claim
  `019f6a2c-a965-72ca-b026-3480ed198f55` (entry_hash `fca02d14…`), blast_radius Module, proposal_type
  Other. Outcome **REJECTED**, tally_mean **−0.43**, variance 0.002 (coherent, not polarized). All three
  voters (groq-gpt-oss-20b, groq-qwen3-32b, cerebras-gpt-oss-120b) rejected for **empty evidence**;
  cerebras additionally flagged radius over-declaration (scope is a single local file → Local, not Module).
  The substance ("intake + defer") was **not** rejected — the claim was rejected for lacking an evidence
  anchor. The gate failing closed on an unevidenced provenance claim is the guardrail working as designed.

## What would let this proceed

1. Independently verify the four figures above against the actual *Training Ecosystems* paper.
2. Re-submit a **Local**-radius consensus claim citing **this file** (commit/URL) as the evidence anchor,
   to get the intake+defer substance adjudicated on the record.
3. Only after that: open a dedicated ADR for K-metric adoption (scoped as *proxy*, not *primary*) and a
   separate decision for Phase-1 statefulness sequencing. Do not fold both into one ADR.

## Explicit non-promotion

No portion of this note is canon. It does not adopt the K-metric, StatefulAgent, or any figure herein.
Promotion requires figure verification + a passing evidence-anchored consensus decision + a dedicated ADR.
