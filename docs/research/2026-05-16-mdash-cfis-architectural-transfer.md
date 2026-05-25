# MDASH → CFIS Architectural Transfer

**Date:** 2026-05-16
**Type:** Research synthesis, ADR-candidate seed
**Truth status:** ⚠️ Specified — six concrete CFIS v0.4 upgrade proposals derived from external empirical validation; none built or piloted in FLOSSI0ULLK yet
**Source intake:** `FLOSS/archive/intake_raw/2026-05-14_mdash_cfis_perplexity_dump.md` (Perplexity multi-section corpus dump, ingested 2026-05-16)
**Related canon:** CFIS v0.3 (pre-canon at workspace root); META_COORDINATION_KERNEL_v4.0 §16 (consensus voter cohort); ADR-10 (analog vote model)
**Subsumes/extends:** Wave-3 items deferred to CFIS Phase 0 (PLURALISTIC-EPISTEMOLOGY, TRANSLATION-ENTROPY-MEASUREMENT, CONFLICT-RESOLUTION); inputs to ADR-CFIS-01/02/03 reconsideration

---

## One-line summary

Microsoft's MDASH announcement on 2026-05-12 — a 100+ specialized-agent multi-model security harness that scored 88.45% on CyberGym (top of the public leaderboard) and produced 16 real Windows CVEs in one Patch Tuesday — empirically validates the architecture class CFIS proposes, and yields six concrete upgrade candidates for CFIS v0.4.

---

## Why this matters for FLOSSI0ULLK

MDASH's central design principle is **"the harness is the product, the model is one input"** — directly parallel to the FLOSSI0ULLK metaharness doctrine and the Layer 4.5 passive-router gateway. Microsoft ran this architecture-class on production-scale proprietary code and proved that:

- A 5-stage pipeline (Prepare → Scan → Validate → Dedup → Prove) outperforms single-model approaches by ~5 points on CyberGym
- The next-place entry on the CyberGym leaderboard (~83.1%) was **Claude Mythos Preview** — the same model implicated in the March 2026 Anthropic CMS leak (resonance_mechanism_v2.md §0.3, the P5 violation case study). Harness ~5pts > frontier model alone.
- 96% recall on 5 years of CLFS MSRC cases and 100% on tcpip.sys MSRC cases were achievable with **generally available models**, not proprietary ones — meaning the architectural advantage transfers to FLOSS substrates

This converts the metaharness doctrine from ⚠️ Specified toward ✅ Verified-by-analogue. FLOSSI0ULLK's voter-roster diversity policy (≥3 providers, ≥4 model families per ADR-Suite v2.0) is the same shape as MDASH's "ensemble of diverse models" property #1.

---

## The six concrete upgrades for CFIS v0.4

### 1. Divergence Stress-Test Agent (DST-A) — make T4 epistemically stronger, not just administratively recorded

MDASH principle: when an auditor flags something and the debater cannot refute it, the finding's credibility goes **up**. Disagreement is signal.

CFIS v0.3 currently treats Tier 4 (incommensurable divergence) as an endpoint — preserve via RDF-star Named Graphs and stop. Add a **DST-A** as a mandatory P3 sub-process: actively attempt to dissolve every proposed T4 into T2 (covariance via translation error). DST-A **failure-to-dissolve** is the primary validation signal that the divergence is genuine. Q-score impact of preserving T4 increases proportional to DST-A confidence.

Maps to: ADR-CFIS-03 (invariants as triples) — extends the encoding with a DST-A audit field.

### 2. Auditor / Debater / Prover triad per protocol step

MDASH principle: 100+ specialized agents > one prompt asked to do everything. Auditor doesn't reason like debater doesn't reason like prover.

CFIS's four-process meta-coordinator (P1-P4) is already this shape at the *process* level but the spec doesn't enforce specialization *within* each process. Define dedicated agent roles with narrow mandates:

| CFIS step | Auditor | Debater | Prover |
|---|---|---|---|
| 2: Frame translation | Translator-A produces translation in frame vocabulary | Challenger-A finds where translation fails / over-asserts | `[auth:trained]` rep confirms |
| 3: Covariant detection | Pattern-A identifies structural relationships surviving across frames | Skeptic-A finds frames where it doesn't | Q-Scorer (deterministic) |
| 4: Contravariant detection | Inverter-A identifies what flips | Devil's-Advocate-A argues it doesn't | LSM-Override trigger |
| 5: Divergence preservation | DST-A (#1 above) | — | RDF-star encoder |

Bonus: the Challenger-A and Skeptic-A roles ARE the machine-checkable instantiation of the LSM-Override protocol. No separate override mechanism needed if disagreement is built into every step.

### 3. Prove Gate between Q-score and Tier-1/2 certification

MDASH principle: a candidate finding that isn't proven is just triage backlog. Q-score alone is statistical agreement, not proof — two frames might agree for incompatible reasons (the "frame cousin" problem CFIS v0.3 names).

Insert a **Prove Gate** between Q > 0.70 and Tier-1/Tier-2 certification. A claim entering the gate must demonstrate:

1. **Non-vacuous prediction** — at least one frame's prediction is *materially different* from what naïve generalization would yield (rules out vacuous invariants)
2. **Falsifiability per frame** — at least one frame recognizes a falsification condition as meaningful
3. **Non-frame-cousin agreement** — the claim's cross-frame survival isn't due to shared CLC axioms (apply the Frame Sufficiency Gate logic at the *claim* level, not just the frame-set level)

Maps to: extends ADR-CFIS-02 (meta-frame claims) — the Prove Gate is the operational test for meta-frame validity.

### 4. Frame Context Plugin (FCP) — make `[auth:lived]` knowledge injectable

MDASH principle: the CLFS proving plugin embeds filesystem invariants the foundation model cannot internalize. Plugins inject domain knowledge at the point of need, rather than expecting the model to learn it.

CFIS v0.3 §3.4 identifies the analogous problem: "LLMs can output grammatically correct frame-translations while missing the embodied nuance that makes a frame's apparent contradiction productive." The MDASH-shaped answer: don't make the LLM learn the embodied nuance — make it injectable.

Define an **FCP interface**. For each of the 7 pilot frames, an `[auth:lived]` or `[auth:trained]` representative authors a structured YAML/SDNA object containing:

- The frame's 3 registered blindspots in machine-readable form
- Canonical examples of category errors that `[auth:structural]` agents commonly make in this frame
- Trusted transformation patterns (concept in Frame X → Frame Y with caveats)

When any `[auth:structural]` agent processes a claim involving Frame F2 (Indigenous long-horizon relational), it auto-loads the F2 FCP before generating output. The community authors the plugin, not the AI.

Operational note: this is also a tangible work-unit for the **frame recruitment** task in working-todo §C (T5, flagged "HIGHEST risk — social, not technical"). Authoring an FCP is concrete enough that prospective frame representatives can engage without first internalizing the full CFIS spec.

### 5. Model Invariant Layer (MIL) — make the model-agnostic surface explicit

MDASH principle: when a new model arrives, A/B-testing is one config flip. Customer investments (plugins, configurations, calibrations) carry over because the targeting / validation / dedup / prove stages are model-agnostic by construction.

CFIS already aspires to this at the Holochain/AD4M layer but doesn't formally protect it. Designate a **MIL** — the subset of CFIS components that are model-agnostic by construction:

- CLC matrix computation (pure logic)
- Q-score formula (deterministic math)
- Frame Sufficiency Gate (boolean check)
- RDF-star divergence encoding (data structure)
- Authority tier assignment (social protocol)
- Prove Gate predicates from #3 above

Everything else (translation quality, pattern matching, debater performance) is expected to vary by model. The MIL survives any model upgrade. Non-MIL components are where A/B testing happens.

Engineering implication: MIL components are the first things deployed, the last things changed, and the things that get the most thorough governance documentation. Maps directly to the **Now / Later / Never** designation work — MIL = Now; auditor/debater/prover quality = Later (model-dependent calibration).

### 6. The architecture itself is now Now-ready, not because Microsoft says so

MDASH did not propose the architecture — it executed one. The 16 patched CVEs, 88.45% CyberGym, 96/100% MSRC recall numbers are ground-truth proof-of-work for the architecture-class. Per the FLOSSI0ULLK governance test (external empirical validation before Now-designation), this is sufficient evidence to designate the **Auditor/Debater/Prover triad + domain plugins + model-agnostic harness** as **Now**-ready for FLOSSI0ULLK piloting.

The 3 Wave-3 items already subsumed by CFIS (PLURALISTIC-EPISTEMOLOGY, TRANSLATION-ENTROPY-MEASUREMENT, CONFLICT-RESOLUTION) gain a concrete implementation path via this transfer.

---

## What this does NOT claim

- MDASH does not validate CFIS Tier 1 invariant detection — only the multi-agent harness architecture underneath
- The dual-use risk is structural: same architecture that finds defender bugs finds attacker zero-days. The institutional backstop legitimizing Microsoft's use (MSRC, Patch Tuesday, three-team accountability chain) does NOT transfer to FLOSSI0ULLK automatically. A separate ADR-THREAT-MODEL pass (Wave-3 item #2, 7/13 votes) is required before deploying the prove-stage at the FLOSSI0ULLK consensus gateway.
- The Claude Mythos Preview score (~83.1% on CyberGym) is reported via MDASH's blog post; not independently verified against Anthropic's public statements. Treat as Verified-External for MDASH leaderboard position, Specified for the model-identity attribution.

---

## Next actions

| # | Action | Owner | Gate |
|---|---|---|---|
| 1 | Add DST-A, Auditor/Debater/Prover triad, Prove Gate, FCP, MIL as candidate inputs to CFIS v0.4 ADR-CFIS-01/02/03 | Whoever drives CFIS v0.4 | After CFIS v0.3 canon promotion (working-todo §A.2) |
| 2 | File ADR candidate for A2A/MCP unified entity card track (carried from IBM "After Mythos" continuation packet, now additionally motivated by MDASH ecosystem context — MCP donated to Linux Foundation Dec 2025, three converging open agent standards) | Strategy track | Timeline-sensitive (spec is solidifying now per ecosystem reports) |
| 3 | Submit consensus claim validating this synthesis as v0.4 input | Strategy track | Requires `[auth:trained]` rep confirmation for each subsumed Wave-3 item |
| 4 | Update voter cohort spec to explicitly reference MDASH ensemble property — diversity policy already aligned (≥3 providers, ≥4 families), worth a §16 footnote in META_COORDINATION_KERNEL_v4.0 | Gateway maintainer | When v4.1 work begins |

---

## External sources

- [Defense at AI speed: Microsoft's new multi-model agentic security system (Microsoft Security Blog, 2026-05-12)](https://www.microsoft.com/en-us/security/blog/2026/05/12/defense-at-ai-speed-microsofts-new-multi-model-agentic-security-system-tops-leading-industry-benchmark/)
- [Microsoft's MDASH AI System Finds 16 Windows Flaws (The Hacker News)](https://thehackernews.com/2026/05/microsofts-mdash-ai-system-finds-16.html)
- [SiliconANGLE coverage including Claude Mythos Preview CyberGym positioning](https://siliconangle.com/2026/05/13/microsofts-agentic-security-system-mdash-uncovers-four-critical-windows-rce-flaws/)
- [DARPA AIxCC results, Team Atlanta lineage](https://www.darpa.mil/news/2025/aixcc-results)
- [CyberGym benchmark](https://www.cybergym.io)

Internal provenance: this doc is the v0.4-input distillation from `FLOSS/archive/intake_raw/2026-05-14_mdash_cfis_perplexity_dump.md`, which is a Perplexity multi-section corpus dump containing (1) CFIS v0.3 cross-corpus synthesis, (2) LeCun *Path Towards AMI* deep-read, (3) JEPA ecosystem update (AMI Labs $1.03B raise, V-JEPA 2, VL-JEPA, LeWM), (4) MDASH announcement copy, (5) CFIS-strategic-transfer analysis. Sections 1-3 are reference material already cited elsewhere; sections 4-5 are the load-bearing content captured here.
