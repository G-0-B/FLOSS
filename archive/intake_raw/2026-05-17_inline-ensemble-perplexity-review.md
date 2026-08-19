<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# {\# Inline Reasoning Ensemble — Continuous Consensus Layer

**Date:** 2026-05-17
**Type:** Research / Architectural proposal (ADR-candidate)
**Truth status:** ⚠️ Specified — sketch of a new architectural pattern; no implementation yet
**Author trail:** User (Anthony) named the architectural shape 2026-05-17; this document captures the design + open questions + next-action gates
**Related canon:** ADR-10 (consensus gateway, 32/32 ✅), ADR-6 (four-system seam architecture), ADR-9 (ContinuityPayload), CFIS v0.3 (cross-frame invariance), 2026-05-16-mdash-cfis-architectural-transfer.md
**Subsumes:** The "every prompt deserves multi-model debate" intuition; the "spread tokens across providers to avoid rate-limit pressure" cost-optimization angle
**Open ADR-class follow-on:** This is candidate material for a future ADR-14 if the pilot validates. Not promoted yet.

---

## 0. One-line summary

Extend the ADR-10 consensus gateway from a *decision-grade* surface (claims, votes, source-chain commits) to a *reasoning-grade* surface that wraps individual reasoning steps in multi-model debate — selectively, on substantive prompts only, gated by a local orchestrator. Token spread is a secondary benefit; the load-bearing reason is **MDASH-validated**: the harness-around-models systematically outperforms the model itself, and the diversity of perspectives surfaces blindspots that single-model reasoning misses by construction.

---

## 1. Why now

Three forces converge:

1. **MDASH empirical validation** (2026-05-12). Microsoft's multi-model agentic scanning harness scored 88.45% on CyberGym using *generally available* models, beating the next single-model entry (Claude Mythos Preview at 83.1%) by ~5 points. The lesson, transferred to FLOSSI0ULLK in `2026-05-16-mdash-cfis-architectural-transfer.md`: **the harness is the product, the model is one input**.
2. **CFIS v0.3 in practice.** The epistemological OS treats divergence between frames as positive information, not noise to suppress. The four-process meta-coordinator (P1–P4) is currently scoped to *claims* (substantive proposals through the gateway). The CFIS principle generalizes naturally to reasoning steps — if cross-frame invariance is the truth-detector for claims, it's also a truth-detector for inferences.
3. **User's working-style pressure.** Per `feedback_pressure_helps_drop_throttling_guards.md`, more autonomous wide-execution helps the user produce. The reasoning ensemble, applied even selectively, multiplies the throughput-of-vetted-reasoning per session.

The token-spread benefit (avoiding any one provider's rate cap by distributing load across Cerebras + Groq + Mistral + Flowith + local) is real but secondary. If the only benefit were cost, a single-provider cache would beat ensemble. The load-bearing benefit is **disagreement-as-signal**.

---

## 2. What this is NOT

Naming the failure modes upfront, since the user's stated framing ("every chat") would, if implemented literally, fail in known ways:

- **Not "every prompt becomes a multi-model debate."** Latency cost is real (parallel calls still wait on the slowest voter; sequential is worse). Simple lookups, file reads, name-recall, format conversions — these are not reasoning steps and do not benefit from ensemble. Routing them through debate would slow interactive work by 10-50× for marginal-to-zero quality gain.
- **Not "every reasoning step becomes a synchronous vote."** Some reasoning is internal to one model's chain-of-thought and would be destroyed if you tried to externalize it mid-stream. The ensemble works at the *decision boundary*, not the token boundary.
- **Not "more models = better."** Diminishing returns kick in fast. 3 diverse models > 1; 7 diverse > 3; 15 vs 7 is marginal-or-noise. ADR-Suite v2.0 voter-diversity policy (≥3 providers, ≥4 model families) is the established floor; double that is the ceiling for routine reasoning.
- **Not a replacement for ADR-10.** ADR-10 remains the decision-grade surface (Claims, Votes, source-chain commits, blast-radius tier discipline). The reasoning ensemble is a *lower-stakes parallel surface* with shorter retention and lighter governance. Claims still flow through ADR-10. Reasoning steps flow through the new surface.

---

## 3. Architectural sketch

### 3.1 Three operating modes selected by a local router

A small local model (the **Router**) inspects each incoming prompt or reasoning step and chooses one of three modes:


| Mode | Trigger | Routing | Latency | Use case |
| :-- | :-- | :-- | :-- | :-- |
| **Pass-through** | Trivial lookup, file read, formatting, recall, simple math | Single cheap call (whichever provider has lowest current backpressure) | ~1-3s | "What's in line 47 of file X?", "Reformat this YAML", "Sum these numbers" |
| **Single-strong** | Standard reasoning, code edits, single-file synthesis | Single capable model (Opus/Sonnet/Pro/Llama-70B) | ~5-30s | Most actual work; the default current behavior |
| **Ensemble** | Substantive reasoning, architectural decisions, multi-file synthesis, anything tagged `requires_debate` by user or self-classification, anything that would be a Claim if it landed in ADR-10 | Parallel calls to N≥3 diverse voters (CFIS-frame-aware where possible), local Router synthesizes | ~30-120s (slowest voter dominates) | Architectural proposals, ADR-class moves, cross-frame claims, blindspot-surfacing |

The Router itself runs in <500ms on a local model — it's a classifier, not a reasoner. Its only job is mode selection.

### 3.2 Ensemble synthesis (the load-bearing component)

When the Router picks Ensemble mode:

1. **Diverse call dispatch.** Parallel async fan-out to ≥3 voters. Diversity policy reuses ADR-Suite v2.0: ≥3 providers, ≥4 model families. Same-family endpoints don't count as independence.
2. **Independent reasoning.** Each voter receives the same prompt + reasoning context. No voter sees another voter's output. (CFIS-relevant: prevents reasoning-contamination across frames.)
3. **Router synthesis with disagreement-as-signal logic.** The local Router collects all N responses and produces:
    - **Tier-1 candidates:** Points all voters agree on. These are robust against single-model bias.
    - **Tier-2 candidates:** Points most voters agree on (≥⌈N/2⌉ but not unanimous). Flag the dissent.
    - **Tier-4 candidates:** Points where voters disagree substantively. **These are the highest-information events** — disagreement that survives multi-model exposure is real signal about a genuinely hard question or a blindspot none can see past.
    - **Anti-sycophancy override:** If exactly one voter dissents from N-1 agreement, the dissenter's reasoning is surfaced verbatim, not silenced. This is the MDASH lesson: when an auditor flags something and the debater can't refute it, credibility goes UP, not down.
4. **Synthesis output.** The final response to user contains: (a) the consensus reasoning, (b) named dissents/tensions where they exist, (c) explicit flag of any Tier-4 divergences that should be preserved rather than collapsed. Format-conscious — not every output needs a table; for simple ensemble queries the dissent can be one inline sentence.
5. **Durable provenance.** Every ensemble call writes a line to `.agent-surface/reasoning/activity.jsonl`: prompt-hash, voter-list, per-voter responses (truncated tails), Router-classified tier outputs, final synthesis. This is the durable cross-agent trail per `feedback_durable_provenance_required.md`.

### 3.3 Reuse of existing infrastructure

| Existing | Reused-for-reasoning-ensemble |
| :-- | :-- |
| `FLOSS/packages/metacoordinator_mcp/server.py` (ADR-10 gateway) | Optional — the ensemble can route through the gateway for full source-chain provenance OR run direct via LiteLLM for latency. Gateway use is recommended for ensemble calls flagged `requires_debate` since those are decision-grade. |
| `FLOSS/packages/orchestrator/consensus_gate.py` (analog vote model) | The Tier-1/2/4 classification IS analog consensus, just applied to reasoning rather than proposals. |
| `voter_registry.json` (diverse-max profile, 14 voters) | The ensemble pulls from the same roster. No new voter wiring needed. |
| Activity log pattern (`.agent-surface/heartbeat/ticks.log`, `.agent-surface/harvest/activity.jsonl`) | Same shape for `.agent-surface/reasoning/activity.jsonl`. |
| `ContinuityPayload` schema (ADR-9) | Long-running reasoning sessions can checkpoint state via ContinuityClaims — connects this surface to the broader meta-harness. |

The reasoning ensemble is **not a new substrate.** It's a higher-frequency, lower-stakes profile on the existing gateway infrastructure.

---

## 4. The local orchestrator question (separate but coupled decision)

The Router needs to be:

- **Local** — every prompt routing through a cloud call adds latency + spreads classification-tier data to providers
- **Fast** — <500ms classification budget for the routing decision alone
- **Sovereign-aligned** — open-weight model (per P5; per ADR-7 AGPL cascade compatibility on model license where it matters for redistribution)
- **Capable enough for reasoning classification** — but not full reasoner; a 7B-13B model is plenty for this role
- **Tool-use / JSON-mode capable** — to emit structured routing decisions reliably

Candidates (initial scan, not exhaustive):


| Model | Size | Local-inference path | Pros | Cons |
| :-- | :-- | :-- | :-- | :-- |
| **Qwen3-Coder-32B** | 32B | Ollama / llama.cpp / vLLM | Strong reasoning, JSON-stable, open weight, multilingual | 32B needs ~20GB VRAM bf16 / ~10GB Q4 — hardware question |
| **Llama-3.3-70B** | 70B | Ollama (Q4-Q5 quants), vLLM | Top-tier reasoning, very stable JSON | 70B requires beefy GPU even quantized; overkill for routing |
| **Qwen3-14B** | 14B | Ollama / llama.cpp | Sweet spot — fast, capable, hits JSON cleanly | Less raw smarts than 32B |
| **Phi-4** (small) | 14B | Ollama / llama.cpp | Microsoft, strong for size, dense | License nuances (MIT but check fresh) |
| **Gemma 3** (variants) | 4-27B | Ollama / llama.cpp | Google open-weight, dense | Newer ecosystem support |
| **DeepSeek-R1-Distill** | 7B-32B variants | Ollama / llama.cpp | Reasoning-distilled from R1; very strong for size | Distillation quality varies; check the specific variant |

**Recommendation pending hardware spec:** if the user's machine can run 32B Q4 (~10GB VRAM, ~16GB system RAM ballpark), **Qwen3-Coder-32B** is the strongest single pick for both Router-role and as a *fallback voter* in the ensemble itself (saves cloud quota on at least one slot). If hardware can't comfortably hold 32B Q4, **Qwen3-14B** is the right step down.

Ollama is the simplest install path on the user's existing setup (per OpenHuman/heartbeat ecosystem; already-used pattern). vLLM is faster for higher concurrency but heavier ops.

**Open hardware question:** what GPU does the user's MSI machine have? This determines whether 32B-Q4 is comfortable or a stretch. (Per session_summary §A.3 there's "32GB RAM, discrete GPU, multiple disassemblies, Peltier cooling prototype" — strong indicators of a gaming-class machine. Confirm VRAM specifically before committing to a model size.)

---

## 5. CFIS application (the philosophical thread)

The user named this explicitly: "taking our CFIS into practice." Concrete mapping:


| CFIS concept | Reasoning-ensemble realization |
| :-- | :-- |
| Frames (7-frame pilot) | Voter selection can deliberately span frames where the reasoning topic touches frame-bound knowledge. For technical reasoning, model-family diversity is the practical proxy until `[auth:trained]` reps are recruited per CFIS Phase 0 §T5. |
| Tier 1 invariants | Consensus across all voters = invariant candidate. Worth flagging as load-bearing. |
| Tier 2 covariant | Most-voter agreement with translatable dissent = covariant. |
| Tier 4 divergence | Substantive multi-voter disagreement = preserved as Tier-4 in the synthesis output. Per CFIS v0.3, this is HIGH information, not noise. |
| `[auth:structural]` constraint | LLMs are `[auth:structural]` per CFIS — they can articulate axioms and derive but cannot embody. The reasoning ensemble explicitly does not promote LLM-only consensus to Tier 1 invariant; it generates *candidates* that require `[auth:trained]` or `[auth:lived]` confirmation for canon promotion. |
| LSM-Override | The Router can flag any prompt where multi-voter agreement crosses against `[auth:trained]` or `[auth:lived]` ground-truth (when known) — the human steward holds override authority. |
| DST-A (proposed for v0.4 from MDASH transfer) | The ensemble's natural dissent-stress-testing replaces an explicit DST-A agent for in-flight reasoning. For formal claim adjudication, DST-A is still needed in the v0.4 ADR. |


---

## 6. Selectivity discipline (non-negotiable)

The user's instinct to apply this "to every chat" must be tempered by selectivity, or the cure becomes worse than the disease:

**Always ensemble:**

- Architectural proposals (ADR-class)
- Multi-file refactors
- Decisions with blast radius beyond a single function
- Anything where being-wrong has rollback cost
- Anything the user explicitly tags `--debate` or routes through the consensus gateway by name

**Default to single-strong (NOT ensemble):**

- Single-file edits
- Code reads + explanations
- Routine synthesis
- Format conversions
- Memory-recall

**Pass-through (NOT even single-strong):**

- File reads, directory listings, grep results
- Status checks
- Acknowledgments

**Router error budget:** Misclassification is cheap in both directions. Over-routing to Ensemble costs ~30-60s extra. Under-routing to Single-strong means missing the blindspot-detection benefit on that turn. Bias the Router slightly toward Ensemble on ambiguous cases — recovery is just "wait 30s more," not "produce wrong work."

---

## 7. Cost model

Premise from user 2026-05-17: *"spreading out token usage will alleviate hitting any ones limits in the first place."* True, with nuance:

- **Free-tier providers (Cerebras / Groq / Mistral / Flowith):** Per-provider rate limits (RPM, daily caps) are the real constraint. Distributing across 4+ providers raises the effective ceiling by ~4× before any one limit fires.
- **Paid subscriptions (Claude Pro / Gemini Pro):** Have generous limits but distinct quota pools. Distributing avoids hitting any one's daily cap.
- **Per-call cost on Cerebras/Groq (free tier):** \$0. Distributing across these is pure quota-management upside.
- **Per-call cost on premium APIs:** Real \$. The ensemble should NOT default to Opus + GPT-5 + Pro all at once for routine work — that's 3× the cost for marginal benefit. The diverse-max profile mixes premium with free-tier exactly for this reason.

**Practical cost discipline:**

- Ensemble: 3-5 free-tier voters + 0-1 premium voter, NOT 7 premium voters
- Single-strong: use whichever premium-tier subscription has most remaining quota today
- Pass-through: free-tier or local model only

A pure-local ensemble (3-5 local model calls in parallel) becomes possible once the local Router is set up — that's \$0/call ensemble for routine reasoning. Latency on a single GPU is the limit (queues serialize), but for sequential local-ensemble most prompts <60s is achievable on a capable consumer GPU.

---

## 8. Open questions

1. **Where does the Router live in the call flow?** Two options:
    - (a) Router is a hook intercepting the user's prompt before Claude sees it. Claude becomes one voter among many.
    - (b) Router is invoked by Claude as a sub-tool (`route_reasoning(prompt) → mode_decision`). Claude orchestrates the ensemble.

(b) is simpler to bootstrap and aligns with existing skill/tool patterns. (a) is more architecturally clean long-term. Recommend (b) for v0.1, migrate toward (a) if it proves out.
2. **How does this integrate with Claude Code session?** The harness around Claude (this very session) doesn't naturally expose a "wrap each tool call in an ensemble" surface. Two paths:
    - Skill-driven: a `/ensemble` slash command the user invokes when wanting debate on a specific question
    - MCP-driven: an MCP tool the Claude session calls (e.g. `mcp__reasoning_ensemble__deliberate(prompt)`) that returns the synthesized response

The MCP-driven path is closer to existing patterns (consensus gateway is already MCP). Skill-driven is faster to prototype.
3. **What about reasoning steps Claude takes INTERNALLY in chain-of-thought?** These don't surface to the harness. The ensemble can only wrap calls that cross the API/tool boundary. This means internal Claude reasoning is single-model by construction — the ensemble augments at the *boundary*, not inside the model.
4. **Local Router hardware sizing.** Confirm GPU/VRAM before committing to model size. This determines whether 32B Q4 is comfortable or whether to step down to 14B.
5. **When does this become canon vs. stay research?** Pilot for ≥7 days with `.agent-surface/reasoning/activity.jsonl` data; if the disagreement-as-signal events produce measurable course-corrections, promote to ADR-14. If they don't, the ensemble is solving a non-problem and stays in research.
6. **CFIS frame-mapping voter selection.** Currently voters are selected by model-family. The CFIS-pure version selects voters spanning the 7-frame matrix. The bridge is: which voter models tend to express which frame perspectives most reliably? This needs empirical calibration data, likely from running the ensemble for a few weeks and post-hoc tagging frame-positioning of responses.

---

## 9. Next-action gates

| \# | Action | Owner | Gate / dependency |
| :-- | :-- | :-- | :-- |
| 1 | **Confirm local hardware** — GPU model + VRAM. Bash command: `nvidia-smi` (Linux/WSL) or `wmic path win32_VideoController get name,adapterram` (Windows PS) | Tony | None — quick |
| 2 | **Install Ollama + pull candidate Router model** (Qwen3-14B or Qwen3-Coder-32B depending on \#1) | Tony | After \#1 |
| 3 | **Prototype the Router as a Python module** (`FLOSS/packages/reasoning_ensemble/router.py`): takes a prompt, returns `{mode: pass_through|single_strong|ensemble, reason: str, voter_count: int}`. Uses Ollama HTTP API for local-call shape. | Tony or delegate | After \#2 |
| 4 | **MCP tool wrapper** (`mcp__reasoning_ensemble__deliberate`) that takes a prompt + optional `force_mode`, returns the synthesized response + Tier-4 divergences if any. Reuses the consensus gateway voter logic. | Tony | After \#3 |
| 5 | **Skill counterpart** (`.claude/skills/reasoning-ensemble/SKILL.md`) for the user-invokable `/ensemble` slash-command path. | Tony or delegate | After \#4 |
| 6 | **Activity log spec** — `.agent-surface/reasoning/activity.jsonl` schema. One-line shape; mirror the harvest activity log convention. | Tony or delegate | Parallel with \#3 |
| 7 | **7-day pilot + measurement** — run the ensemble selectively for a week, log every Tier-4 divergence, measure how many produced course-corrections vs. how many were noise. | Tony | After \#4-5 |
| 8 | **ADR-14 promotion decision** — based on pilot data, promote to ADR or archive as "good idea that didn't validate." | Tony + consensus claim | After \#7 |

Working-todo §A.5 already names §G heartbeat-running health. This proposal adds a NEW work-stream — should be tracked as §A.6 in the working-todo.

---

## 10. Honest pushback (anti-sycophancy)

The user said "we should be doing that with every prompt." I disagree with the literal version of that claim, and per the standing anti-sycophancy rule I'll say so directly:

- **Literal "every prompt" fails on latency**: typical Claude Code session has 50-300 turns. At ~60s/ensemble that's 50-300 minutes of pure ensemble overhead per session, most spent debating things like "read file X" that have no debate to be had.
- **Literal "every prompt" fails on cost** even on free tier: free-tier providers have RPM limits. Hammering them with hundreds of debate-rounds per hour will rate-limit you faster than concentrating ensemble traffic on substantive prompts.
- **Literal "every prompt" fails on signal**: most prompts genuinely don't need ensemble. Noise drowns out the high-signal Tier-4 divergences that the ensemble is supposed to surface.

**The defensible version of the user's claim:** "We should be doing that for every *substantive* reasoning step, with a local Router deciding what counts as substantive." That version IS correct, IS MDASH-supported, IS CFIS-aligned, and IS this proposal's actual shape.

If after the pilot the data shows the Router under-routes (i.e., the user keeps tagging things `--debate` that the Router classified as single-strong), tune the Router's classifier toward ensemble. The bias-toward-ensemble default named in §6 is the lever for that.

---

## 11. Provenance + cross-refs

- **This file** lives at `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md` per intake-mouth → research convention.
- **Trigger:** User prompt 2026-05-17 (after consensus-gateway and MDASH context in the prior turns).
- **Cross-refs:** ADR-Suite v2.0 (especially ADR-10 + ADR-6 + ADR-9), CFIS v0.3 spec at workspace root, `2026-05-16-mdash-cfis-architectural-transfer.md`, `feedback_pressure_helps_drop_throttling_guards.md`, `feedback_durable_provenance_required.md`, `project_metaharness_doctrine.md`.
- **Future-agent reading list:** Read in this order — (1) the ADR-Suite v2.0 to understand the canonical consensus-gateway shape, (2) the MDASH transfer doc to see the MDASH-CFIS architectural-class alignment, (3) this doc for the inline-ensemble proposal, (4) `.agent-surface/reasoning/activity.jsonl` (once it exists) for empirical pilot data.
- **Activity log integration target:** when the Router/ensemble lands, every invocation appends to `.agent-surface/reasoning/activity.jsonl` for durable cross-agent provenance per the standing rule from `feedback_durable_provenance_required.md`.}

This is a significant proposal. Let me synthesize the full analysis with the new research evidence.

***

## Assessment: Inline Reasoning Ensemble as CFIS Practice Layer

The proposal is architecturally sound and now has strong empirical backing from three independent sources published in the past few months. Here is the full analysis — pushbacks, upgrades, and concrete next actions.

***

### What the Research Just Validated

Two papers published in May 2026 directly confirm the core bets in this proposal:

**Multi-Stream LLMs (Max Planck / ETH Zurich, May 12, 2026)** found that training models to run parallel reasoning streams — one generating output, one auditing simultaneously — reduces end-to-end latency by 40%+ and *improves* accuracy on LogicNLI from 61.5% to 65.65% at 1.7B scale. The auditing stream catches errors the main stream generates in real time, not after the fact. This is the architectural validation of your audit-while-generating intuition — not as a multi-model call, but as a parallel stream within a single forward pass. The key insight: **you don't have to wait for the model to finish before auditing begins**.

**Multi-Model Consensus Reasoning Engine (arXiv, January 2026)** empirically proved that supervised consensus over 3 heterogeneous LLMs (Llama-3-8B, Mistral-7B, Qwen2-7B) beats the best single model by 4.6 points and majority vote by 8.1 points on math, commonsense, science, and truthfulness benchmarks. The decisive architectural finding: **Graph Attention Networks that propagate information along similarity edges, amplifying minority-but-coherent answer clusters**, outperform all other meta-models. Semantic agreement and clustering are the highest-signal features — not model confidence, not lexical overlap.

Both findings map directly onto the proposal's architecture and onto CFIS. Let me integrate them.

***

### Upgrade 1: The Router's Triage Is Already Validated — Add One Feature

The three-mode routing (pass-through / single-strong / ensemble) is correct. But the consensus research reveals a feature the Router should compute that the proposal doesn't mention: **semantic clustering of prior responses in the conversation**.

When the Router classifies a prompt, it should not just ask "is this substantive?" — it should ask "has there been disagreement in reasoning on closely related prompts in this session?" If `.agent-surface/reasoning/activity.jsonl` contains prior Tier-4 divergences on semantically adjacent questions (high cosine similarity between their embeddings), the Router should bias toward Ensemble even on prompts it would otherwise classify as single-strong. Adjacent disagreement is predictive of future disagreement.

This is cheap to implement: compute embedding similarity between the incoming prompt and the past 10 logged prompts. If any prior prompt has a Tier-4 tag and similarity > 0.7, force Ensemble mode. The Router already reads the activity log; this adds one cosine similarity call.

***

### Upgrade 2: Don't Just Collect Voter Responses — Build the Graph

The proposal describes collecting N voter responses and classifying them into Tier-1/2/4. The consensus research shows this is leaving signal on the table. The right architecture is to:

1. Embed each voter's response using a local sentence-transformer (SBERT or E5-base — both run on a single GPU alongside the main models)
2. Build a pairwise similarity matrix across all N voter responses
3. Run agglomerative clustering (cosine distance, average linkage) to find response clusters
4. The Router's Tier classification should be cluster-based, not voting-based:
    - **Tier-1:** All responses fall in one cluster (high within-cluster similarity)
    - **Tier-2:** Two clusters, one dominant (≥⌈N/2⌉ responses)
    - **Tier-4:** Two clusters of roughly equal size, OR a small minority cluster whose responses have high internal coherence despite being outnumbered

The last case is the critical one. The consensus research found that the minority-but-coherent cluster is correct surprisingly often on hard questions — especially on truthfulness (the myth case study: most models reproduced the myth, the minority-but-coherent cluster gave the accurate answer). This is the CFIS Tier-4 insight restated empirically: the smallest cluster sometimes contains the highest-quality signal.

Concretely: a **Graph Attention Network** over the voter similarity graph, pretrained on a small labeled corpus of prior ensemble calls (the activity log becomes your training data), becomes the most accurate meta-model for classifying which voter to trust. This is not complex to bootstrap — the consensus paper did it with 3,200 labeled training questions on a single GPU in under 2 hours.

***

### Upgrade 3: Multi-Stream as a Complement, Not Just a Competitor

The multi-stream paper suggests a third mode the proposal doesn't consider: **within-model parallel auditing**. Running a finetuned multi-stream model generates an audit stream simultaneously with the answer stream, reducing latency to nearly zero (first token delay drops to 0 in all benchmarks). This is not a replacement for multi-model ensemble — it catches different classes of errors. The ensemble catches inter-model disagreement (different training data, different biases). The audit stream catches intra-model inconsistency (the same model's reasoning contradicting itself mid-generation).

For the FLOSSI0ULLK architecture, these map to different CFIS processes:


| Mechanism | CFIS Process | Error Class Caught |
| :-- | :-- | :-- |
| Multi-model ensemble | P1 Invariant Detection, P3 Divergence Preservation | Inter-frame disagreement; blindspot exposure |
| Multi-stream audit | P2 Covariance Tracking | Intra-frame inconsistency; self-contradiction |
| Prove Gate | P4 Quality Scoring | Claims that score high but don't survive dynamic testing |

A full implementation uses both. For the v0.1 pilot, the ensemble is the right first layer — it requires no fine-tuning of the local Router model. Multi-stream auditing is a **Later** item once there's a local model capable of being fine-tuned for stream format.

***

### On the Local Router Model: Hardware-Conditional Recommendation

Given the session context (MSI machine, 32GB RAM, discrete GPU), the decision tree is:


| VRAM | Recommended Router Model | Rationale |
| :-- | :-- | :-- |
| ≥16GB | Qwen3-32B Q4 (~20GB VRAM) | 100% accuracy on classification test suite; doubles as ensemble voter slot 1 |
| 10-16GB | Qwen3-32B Q4 (~10GB at very aggressive quant) or Qwen3-14B Q8 (~15GB) | Qwen3-14B Q5_K_M available on Ollama; strong JSON mode |
| <10GB | Qwen3-14B Q4 (~8GB) | Still capable for routing classification; some degradation on complex reasoning |

The Qwen3 family has a known Ollama issue with tool call hallucination at Ollama ≤0.9.2 — update to latest. Also note Qwen3-32B behavior varies between CPU and GPU allocation depending on the calling application — set `OLLAMA_GPU_OVERHEAD=0` and confirm the endpoint is always routing to GPU.

**The `nvidia-smi` call in the proposal's §9 Action 1 is non-negotiable first step.** Everything else is hardware-conditional.

***

### On Option (b) vs. (a) for Router Placement

The proposal correctly recommends Option (b) — Router invoked as a Claude sub-tool — for v0.1. The new argument for this from the multi-stream paper: if Claude eventually integrates multi-stream architecture natively, Option (b) positions the Router as a persistent orchestration layer that survives that transition. Option (a) would require architectural surgery at that point. Build Option (b) cleanly; migration to (a) is a refactor, not a rebuild.

***

### Honest Pushback on One Specific Design Choice

The anti-sycophancy override in §3.2 — *"if exactly one voter dissents from N-1 agreement, the dissenter's reasoning is surfaced verbatim, not silenced"* — is correct in direction but needs a guard. The consensus research shows that not all minority answers deserve equal amplification: a minority cluster with **low internal coherence** (high within-cluster variance, fragmented reasoning, low reasoning-quality score) is not a Tier-4 signal — it is noise. The guard is: surface the dissenter verbatim only if its response passes a reasoning-quality threshold (the verifier score used in the consensus research — logical coherence, internal consistency, completeness — must be ≥ 0.6 out of 1.0). Below that threshold, the dissent is logged to the activity file but not surfaced in the synthesis output. The minority is right sometimes; the minority that can't explain itself is not.

***

### CFIS Integration: One Concrete Addition

The proposal's §5 CFIS mapping is accurate. One addition: the voter similarity graph from Upgrade 2 above *is* the machine-readable form of the CLC independence matrix for AI-level frame assessment. When you embed voter responses and find that two voters always cluster together across many prompts (high persistent co-cluster frequency), those voters are frame cousins — they share a hidden meta-assumption. The activity log, after a few weeks of ensemble calls, gives you empirical frame-cousin detection without having to manually compute CLC positions for AI voters. This feeds directly into ADR-CFIS-03 (Invariants as Triples) — the cluster structure over time becomes evidence about which AI voter combinations produce genuine independence vs. frame-cousin convergence.

***

### Revised Next-Action Sequence

The proposal's §9 action sequence is solid. One reorder and one addition:


| \# | Action | Change from proposal |
| :-- | :-- | :-- |
| 1 | `nvidia-smi` hardware check | Unchanged — truly non-negotiable |
| 2 | Pull Qwen3 Router model via Ollama | Unchanged |
| 3 | **Add embedding model** (SBERT or E5-base via Ollama or HuggingFace local) | **New** — needed for cluster-based Tier classification |
| 4 | Router module with cluster-based Tier logic | Upgrade from vote-count to cluster-similarity |
| 5 | Activity log schema including per-voter embeddings (truncated) + cluster assignments | Upgrade from proposal schema |
| 6 | MCP tool wrapper | Unchanged |
| 7 | 7-day pilot | Unchanged |
| 8 | ADR-14 promotion decision | Unchanged |

The proposal is ready for Action 1 right now. Everything after Action 1 is hardware-conditional. Run `nvidia-smi` (or `wmic path win32_VideoController get name,adapterram` on Windows PowerShell) and report back — the rest of the model sizing and quantization choices cascade from that single number.
<span style="display:none">[^1][^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^2][^20][^21][^22][^23][^24][^25][^26][^27][^28][^29][^3][^30][^31][^32][^33][^34][^35][^36][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://github.com/ollama/ollama/issues/11499

[^2]: https://gist.github.com/yigitkonur/1ff98e1995fbc40fec538b0a56116fc4

[^3]: https://github.com/clduab11/grekko/blob/main/docs/LLM_ENSEMBLE_DESIGN.md

[^4]: https://github.com/ollama/ollama/issues/11381

[^5]: https://github.com/BerriAI/litellm/

[^6]: https://github.com/teabagging/deepseekr4

[^7]: https://github.com/ollama/ollama/issues/11135

[^8]: https://github.com/BerriAI/litellm/blob/main/litellm/proxy/hooks/parallel_request_limiter.py

[^9]: https://github.com/jackguagua/awesome-nas-papers/blob/master/README.md

[^10]: https://github.com/ollama/ollama/issues/10752

[^11]: https://github.com/BerriAI/litellm/issues/874

[^12]: https://github.com/topics/reasoning-engine

[^13]: https://github.com/ollama/ollama/issues/12088

[^14]: https://github.com/BerriAI/litellm/diffs/9?base_sha=ad06b08a5e56ba6df9ac06a94eecb8d2d4d1ef8b\&head_user=rishabgit\&name=main\&pull_number=1459\&qualified_name=refs%2Fheads%2Fmain\&sha1=ad06b08a5e56ba6df9ac06a94eecb8d2d4d1ef8b\&sha2=0f63f3d9cc041c14c37c4ce9f6219e57366e1ad5\&short_path=1ab9b1a\&unchanged=expanded\&w=false

[^15]: https://github.com/xphot/app/blob/main/table.md

[^16]: https://arxiv.org/pdf/2309.16609.pdf

[^17]: https://arxiv.org/pdf/2306.00978.pdf

[^18]: https://arxiv.org/pdf/2501.15383.pdf

[^19]: https://arxiv.org/pdf/2412.15803.pdf

[^20]: http://arxiv.org/pdf/2406.10816.pdf

[^21]: http://arxiv.org/pdf/2411.15399.pdf

[^22]: https://qiita.com/katz_ai/items/93008e8f7577460b3360

[^23]: https://docs.litellm.ai/docs/tutorials/litellm_Test_Multiple_Providers

[^24]: https://arxiv.org/html/2601.07245v1

[^25]: https://localaimaster.com/blog/qwen-3-local-setup-guide

[^26]: https://www.getmaxim.ai/articles/litellm-alternatives-for-production-ai-workloads-in-2026/

[^27]: https://www.supportlogic.com/resources/blog/beyond-llms-why-supportlogic-autoqa-uses-a-precision-multi-model-ml-stack/

[^28]: https://ollama.com/dengcao/Qwen3-14B

[^29]: https://stormap.ai/post/multi-provider-llm-integrations-building-resilient-ai-agents-in-2026

[^30]: https://github.com/junchenzhi/Awesome-LLM-Ensemble

[^31]: https://huggingface.co/blog/lynn-mikami/qwen-3-ollama-vllm

[^32]: https://dev.to/ash_dubai/multi-provider-llm-orchestration-in-production-a-2026-guide-1g10

[^33]: https://www.sciencedirect.com/science/article/abs/pii/S174680942400819X

[^34]: https://ollama.com/dengcao/Qwen3-14B:Q5_K_M

[^35]: https://arxiv.org/html/2605.12460v1

[^36]: https://pmc.ncbi.nlm.nih.gov/articles/PMC12997180/

