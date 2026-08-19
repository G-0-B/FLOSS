# Inline Reasoning Ensemble — Continuous Consensus Layer

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
|---|---|---|---|---|
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
|---|---|
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
|---|---|---|---|---|
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
|---|---|
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
- **Per-call cost on Cerebras/Groq (free tier):** $0. Distributing across these is pure quota-management upside.
- **Per-call cost on premium APIs:** Real $. The ensemble should NOT default to Opus + GPT-5 + Pro all at once for routine work — that's 3× the cost for marginal benefit. The diverse-max profile mixes premium with free-tier exactly for this reason.

**Practical cost discipline:**
- Ensemble: 3-5 free-tier voters + 0-1 premium voter, NOT 7 premium voters
- Single-strong: use whichever premium-tier subscription has most remaining quota today
- Pass-through: free-tier or local model only

A pure-local ensemble (3-5 local model calls in parallel) becomes possible once the local Router is set up — that's $0/call ensemble for routine reasoning. Latency on a single GPU is the limit (queues serialize), but for sequential local-ensemble most prompts <60s is achievable on a capable consumer GPU.

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

| # | Action | Owner | Gate / dependency |
|---|---|---|---|
| 1 | **Confirm local hardware** — GPU model + VRAM. Bash command: `nvidia-smi` (Linux/WSL) or `wmic path win32_VideoController get name,adapterram` (Windows PS) | Tony | None — quick |
| 2 | **Install Ollama + pull candidate Router model** (Qwen3-14B or Qwen3-Coder-32B depending on #1) | Tony | After #1 |
| 3 | **Prototype the Router as a Python module** (`FLOSS/packages/reasoning_ensemble/router.py`): takes a prompt, returns `{mode: pass_through|single_strong|ensemble, reason: str, voter_count: int}`. Uses Ollama HTTP API for local-call shape. | Tony or delegate | After #2 |
| 4 | **MCP tool wrapper** (`mcp__reasoning_ensemble__deliberate`) that takes a prompt + optional `force_mode`, returns the synthesized response + Tier-4 divergences if any. Reuses the consensus gateway voter logic. | Tony | After #3 |
| 5 | **Skill counterpart** (`.claude/skills/reasoning-ensemble/SKILL.md`) for the user-invokable `/ensemble` slash-command path. | Tony or delegate | After #4 |
| 6 | **Activity log spec** — `.agent-surface/reasoning/activity.jsonl` schema. One-line shape; mirror the harvest activity log convention. | Tony or delegate | Parallel with #3 |
| 7 | **7-day pilot + measurement** — run the ensemble selectively for a week, log every Tier-4 divergence, measure how many produced course-corrections vs. how many were noise. | Tony | After #4-5 |
| 8 | **ADR-14 promotion decision** — based on pilot data, promote to ADR or archive as "good idea that didn't validate." | Tony + consensus claim | After #7 |

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

## 12. External research update — 2026-05-17 (v0.2 upgrade)

User received an external Perplexity-synthesis review of this proposal that added empirical backing from two recent papers and three concrete architectural upgrades. Integrating below; the original §0-11 is preserved as v0.1 — these are *additive*, not superseding. Source artifact intake: `C:/~shit/Inline Reasoning Ensemble — Continuous Consensu.md` (archived after integration).

### 12.1 New empirical evidence

**Multi-Stream LLMs** (Max Planck / ETH Zurich, 2026-05-12) — training models with parallel reasoning streams (one generating output, one auditing simultaneously) reduces end-to-end latency by 40%+ AND improves accuracy on LogicNLI from 61.5% → 65.65% at 1.7B scale. The audit stream catches errors the main stream generates in real time, before completion. Architectural validation of within-model audit-while-generating as distinct from multi-model debate.

**Multi-Model Consensus Reasoning Engine** (arXiv, January 2026) — supervised consensus over 3 heterogeneous LLMs (Llama-3-8B, Mistral-7B, Qwen2-7B) beats best single model by **4.6 points** and majority vote by **8.1 points** on math/commonsense/science/truthfulness benchmarks. The decisive finding: **Graph Attention Networks propagating along similarity edges, amplifying minority-but-coherent answer clusters**, outperform all other meta-models. Semantic agreement and clustering are the highest-signal features — not model confidence, not lexical overlap. Trained with ~3,200 labeled questions on a single GPU in <2 hours.

Both directly validate the architecture proposed in §3. The second one prescribes a concrete upgrade.

### 12.2 Upgrade A — Router uses semantic similarity to past activity log

The §3.1 Router classifier should not just ask "is this prompt substantive?" — it should ask "**has there been Tier-4 divergence on closely related prompts in this session?**" If `.agent-surface/reasoning/activity.jsonl` contains prior Tier-4 events on prompts with cosine similarity > 0.7 to the incoming prompt, **bias toward Ensemble** even if the standalone classifier would say single-strong. Adjacent disagreement is predictive of future disagreement.

Implementation cost: one cosine-similarity call against the last ~10 logged prompts. Cheap; the Router already reads the activity log.

### 12.3 Upgrade B — Cluster-based Tier classification (not vote-count-based)

The §3.2 Router synthesis described counting votes. The consensus research shows this is leaving signal on the table. The right architecture is:

1. **Embed each voter's response** using a local sentence-transformer (SBERT or E5-base — both run on GPU alongside the main models)
2. **Pairwise similarity matrix** across all N voter responses
3. **Agglomerative clustering** (cosine distance, average linkage) finds response clusters
4. **Tier classification is cluster-based:**
    - **Tier-1:** All responses in one cluster (high within-cluster similarity)
    - **Tier-2:** Two clusters, one dominant (≥⌈N/2⌉)
    - **Tier-4:** Two clusters of roughly equal size, OR a small minority cluster with **high internal coherence** despite being outnumbered

**The minority-but-coherent case is the critical one.** The consensus research found that small clusters of mutually-reinforcing responses are correct surprisingly often on hard questions — especially truthfulness (the myth case study: most models reproduced the myth; the small but tightly coherent cluster gave the accurate answer). This is CFIS Tier-4 stated empirically: **the smallest cluster sometimes contains the highest-quality signal**.

Later refinement: a Graph Attention Network over the voter similarity graph, pretrained on the activity log as a labeled corpus, becomes the most accurate meta-model. Bootstrap cost is modest per the consensus paper (~3,200 questions, single GPU, <2 hours). Not v0.1; v0.2 once enough activity log accumulates.

### 12.4 Upgrade C — Multi-stream parallel auditing as a third complementary mechanism

The multi-stream paper suggests a third mode the original proposal didn't consider: **within-model parallel auditing**. Running a fine-tuned multi-stream model generates an audit stream simultaneously with the answer stream, reducing first-token latency to ~0 in benchmarks. This is NOT a replacement for multi-model ensemble — it catches different errors:

| Mechanism | CFIS Process | Error class caught |
|---|---|---|
| Multi-model ensemble | P1 Invariant Detection, P3 Divergence Preservation | Inter-frame disagreement; blindspot exposure |
| Multi-stream audit | P2 Covariance Tracking | Intra-frame inconsistency; self-contradiction |
| Prove Gate (from MDASH transfer) | P4 Quality Scoring | Claims that score high but fail dynamic testing |

A full implementation uses all three. v0.1 starts with the ensemble (no fine-tuning required). Multi-stream is a **Later** item once the local model surface supports stream-format fine-tuning. The pattern slots into ADR-9 (continuity) as well: the audit stream's running coherence-check IS an internal continuity-of-reasoning signal.

### 12.5 Anti-sycophancy override — add the coherence guard

§3.2 step 3 said *"if exactly one voter dissents from N-1 agreement, the dissenter's reasoning is surfaced verbatim, not silenced."* That's directionally correct but needs a guard: a minority response with **low internal coherence** (fragmented reasoning, high within-cluster variance, low reasoning-quality score) is noise, not Tier-4 signal.

**Guard rule:** surface a dissenting voter's reasoning verbatim only if its response passes a reasoning-quality threshold (≥0.6 on a verifier score combining logical coherence, internal consistency, completeness). Below threshold, the dissent is logged to the activity file but NOT surfaced in the synthesis output.

Aphorism: *the minority is right sometimes; the minority that can't explain itself is not.*

The reasoning-quality verifier itself can be the local Router model with a separate scoring prompt — runs in <1s per voter response.

### 12.6 CFIS integration — frame-cousin detection emerges from the activity log

Cross-link to ADR-CFIS-03 (Invariants as Triples) in the CFIS v0.3 spec: the voter similarity graph from §12.3 above IS the machine-readable form of the **CLC independence matrix for AI-level frame assessment**. When two voters always cluster together across many prompts (persistent co-cluster frequency over time), those voters are **frame cousins** — they share a hidden meta-assumption.

The activity log, after weeks of ensemble calls, gives empirical frame-cousin detection without manually computing CLC positions for AI voters. Two voters with >70% co-cluster rate over ≥50 prompts are flagged as frame-cousins; the diversity policy (per ADR-Suite v2.0 ≥3 providers, ≥4 model families) should treat frame-cousin pairs as the same "vote" for ensemble independence purposes.

This is a Later refinement once activity log has ≥50 ensemble calls logged. Until then, model-family heuristic stands.

### 12.7 Hardware-conditional Router recommendation (revised)

| VRAM | Recommended Router | Rationale |
|---|---|---|
| **≥16GB (confirmed: RTX 4090 Laptop has 16GB)** | **v0.1 EMPIRICAL PICK 2026-05-18: `phi4-mini:latest` (2.5GB)** — side-by-side calibration showed gemma3:12b-it-qat at 100% accuracy (11/11) but 40-87s/call (CPU offload at 31%/69% when mxbai also loaded), vs phi4-mini at 100% on 4-case sample at ~10s warm-call, fits fully on GPU, leaves VRAM for ensemble voter slots. Set `FLOSS_ROUTER_MODEL=gemma3:12b-it-qat` to revert. Qwen3-32B Q4 (20GB) reserved for ensemble voter slots, not Router. | Router needs latency-priority over reasoning-depth; phi4-mini's smaller param count offset by structured system prompt + JSON-format request. |
| 10-16GB | Qwen3-14B Q5/Q8 or Qwen3-Coder-14B | Strong JSON, fast inference |
| <10GB | Qwen3-14B Q4 | Capable for routing; some reasoning degradation |

**Ollama version note:** Qwen3 family had a tool-call hallucination bug at Ollama ≤0.9.2. Current install is **0.9.6** — fixed. No CLI upgrade required.

### 12.8 Revised next-action sequence (replaces §9 table)

| # | Action | Change | Status |
|---|---|---|---|
| 1 | `nvidia-smi` hardware check | — | ✅ DONE 2026-05-17 — RTX 4090 Laptop 16GB confirmed |
| 2 | Ollama server + Router model | Use already-pulled **gemma3:12b-it-qat** for v0.1 Router; gemma3:27b/Qwen3-32B available for ensemble voter slots | ✅ Ollama running; first Router test done (gemma3:12b returned valid JSON, classification needs few-shot tuning) |
| 3 | **Add embedding model** for cluster-based Tier classification | **NEW per §12.3** | TODO — `ollama pull mxbai-embed-large` or use `nomic-embed-text` |
| 4 | Router module `FLOSS/packages/reasoning_ensemble/router.py` | **Upgrade: cluster-similarity Tier logic (§12.3) + activity-log-similarity bias (§12.2) + reasoning-quality threshold guard (§12.5)** | TODO |
| 5 | MCP tool wrapper `mcp__reasoning_ensemble__deliberate` | — | TODO |
| 6 | Activity log schema | **Upgrade: include per-voter embeddings (truncated) + cluster assignments + reasoning-quality scores** | TODO |
| 7 | Skill counterpart `/ensemble` slash command | — | TODO |
| 8 | 7-day pilot + measurement | Measure Tier-4 course-correction rate AND frame-cousin emergence (§12.6) | TODO |
| 9 | ADR-14 promotion decision | — | TODO |
| 10 | **Multi-stream audit prototype** (Upgrade C / §12.4) | **NEW** — Later item, requires local model fine-tuning surface | TODO (Later) |

### 12.9 What does NOT change

- §2 What This Is NOT — same failure modes still apply; the upgrades sharpen the mitigations, not the boundaries
- §6 Selectivity discipline — non-negotiable
- §7 Cost model — same
- §10 Anti-sycophancy pushback — same; §12.5 sharpens the override mechanic but the principle stands

### 12.10 Provenance for the upgrade

- **External source artifact:** `C:/~shit/Inline Reasoning Ensemble — Continuous Consensu.md` (Perplexity-generated synthesis review, 2026-05-17)
- **Cited papers in the external review:** Multi-Stream LLMs (Max Planck / ETH Zurich, 2026-05-12) and Multi-Model Consensus Reasoning Engine (arXiv, January 2026)
- **Source artifact disposition:** Archive to `FLOSS/archive/intake_raw/2026-05-17_inline-ensemble-perplexity-review.md` after integration of these upgrades, per intake-mouth → research convention. The load-bearing content lives in this §12; the original Perplexity output is reference, not canon.

---

## 11. Provenance + cross-refs

- **This file** lives at `FLOSS/docs/research/2026-05-17-inline-reasoning-ensemble.md` per intake-mouth → research convention.
- **Trigger:** User prompt 2026-05-17 (after consensus-gateway and MDASH context in the prior turns).
- **Cross-refs:** ADR-Suite v2.0 (especially ADR-10 + ADR-6 + ADR-9), CFIS v0.3 spec at workspace root, `2026-05-16-mdash-cfis-architectural-transfer.md`, `feedback_pressure_helps_drop_throttling_guards.md`, `feedback_durable_provenance_required.md`, `project_metaharness_doctrine.md`.
- **Future-agent reading list:** Read in this order — (1) the ADR-Suite v2.0 to understand the canonical consensus-gateway shape, (2) the MDASH transfer doc to see the MDASH-CFIS architectural-class alignment, (3) this doc for the inline-ensemble proposal, (4) `.agent-surface/reasoning/activity.jsonl` (once it exists) for empirical pilot data.
- **Activity log integration target:** when the Router/ensemble lands, every invocation appends to `.agent-surface/reasoning/activity.jsonl` for durable cross-agent provenance per the standing rule from `feedback_durable_provenance_required.md`.
