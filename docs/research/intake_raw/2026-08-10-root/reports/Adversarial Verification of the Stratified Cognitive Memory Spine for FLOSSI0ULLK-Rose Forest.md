# Adversarial Verification of the "Stratified Cognitive Memory Spine" for FLOSSI0ULLK / Rose Forest

## TL;DR
- **The core novelty claim survives adversarial scrutiny, but narrowly and with one important reframing.** No single existing system integrates all four commitments — (1) a cognitional-level *status ladder with enforced legal transitions*, (2) *operation-indexed retrieval contracts*, (3) *prospective registers* as first-class forward-looking structures, and (4) *cross-level defeat propagation*. **Verdict: the "exists nowhere integrated" claim is VERIFIED** — but each *individual* piece is well-precedented, and two systems (NARS, OpenCog/Hyperon) get closer than the conversation credited, so the honest claim is "novel *integration and cognitional-level typing*," not "novel components."
- **The right formal engine is a typed-graph state machine with write-time invariants, not a DEL/Kripke runtime.** Dynamic Epistemic Logic and multi-agent AGM are verification/planning tools that suffer Kripke-model explosion; justification logic (`t:φ` evidence terms) is the closest formal cousin to warrant-tracking and should inform the *edge schema*, but should not be run as a model checker in the hot path.
- **Build the smallest artifact: the status ladder is largely already Verified in the FLOSS repo; prospective registers are genuinely absent and are the highest-value NOW build.** Do NOT build the fourteen-operation spine yet (NEVER-until-proven); start with four classical levels + edges + a hard status ladder enforced by the integrity zome, and add open-question/open-intention entry types. If the spine merely duplicates NARS/Hyperon, adopt their evidence semantics rather than reinventing them.

---

## Key Findings

**1. Repo state is VERIFIED (via subagent; direct fetch was robots-blocked and is flagged).** The repository at `github.com/G-0-B/FLOSS` exists, is public, GPL-3.0 (GitHub-detected; prose claims a "Compassion Clause + Apache-2.0/GPL" licence — a conflict to resolve), 254 commits, last updated Jul 11 2026, owner `G-0-B` linked to `kalisam` (Anthony Garrett). It is overwhelmingly a **documentation/spec repo, not a running system** — its own README states "MVP Phase 0 substrate viability is complete; Phase 1 next," and the SDD repeatedly self-labels architecture "aspirational."

**2. Confirmed FLOSS components (partial spine implementations):**
- **Claim Truth Model** (Verified/Specified/Aspirational/Unverified) — VERIFIED in the Kernel doc §4. This is a partial status ladder (labels without enforced legal transitions).
- **Ternary consensus gateway** (+1/0/−1) — VERIFIED (Kernel §5; "passive-router MCP consensus gateway" in `packages/`). This is the yea/nay/perchance judgment operation. The specific "ADR-10 v2.0 / 32/32 tests passing" claim is NOT fully confirmed — ADR-10 exists, but "32/32" was not found (repo cites "38 passing unit tests" for a different layer). Flag as Unverified.
- **Provenance Packet** (timestamp, author_agent, claim_type, evidence, risks/benefits) — VERIFIED (Kernel §8).
- **Holochain integrity/coordinator + consent zomes** — VERIFIED in docs (`ARF/Cargo.toml`: integrity, coordinator, consent_integrity, consent_coordinator).
- **Two-Plane architecture** (Plane A dev coordination cannot bypass Plane B validation) — VERIFIED (Kernel §7). Structurally isomorphic to "neural never bypasses symbolic validator."
- **KERI** — VERIFIED as *specified but explicitly not implemented* (SDD Layer 0).
- **EWMA reputation, adversarial testing framework, reviewer≠writer invariant R-VD-1** — NOT FOUND in accessible files (likely in blocked ADR-suite/orchestrator source). Flag as Unverified-in-repo.
- **agentmemory shared-context bus** — shared-context memory substrate VERIFIED; exact "agentmemory" branding not confirmed.

**3. The four-column adversarial novelty matrix.** Columns: (i) epistemic stratification by producing operation + status ladder with *enforced* legal transitions; (ii) operation-indexed retrieval contracts; (iii) prospective registers; (iv) cross-level defeat propagation.

| System (authors, year) | (i) Status ladder | (ii) Retrieval contracts | (iii) Prospective registers | (iv) Defeat propagation |
|---|---|---|---|---|
| **TMS/JTMS** (Doyle 1979), **ATMS** (de Kleer 1986) | No (belief in/out, one level) | No | No | **Yes (belief level only)** |
| **BDI** (Bratman; Rao–Georgeff 1991); Jason/JaCaMo | Partial (B/D/I distinct, no warrant gate) | No | **Yes (intentions persist)** | No |
| **IBIS** (Rittel) / ADR practice | Partial (issue/position/argument types) | No | Partial (open issues) | No |
| **SOAR / ACT-R** | No (function-typed, not level-typed) | Partial (cue-based) | No (goals not warrant-bearing) | No |
| **CoALA** (Sumers, Yao, Narasimhan & Griffiths 2023, TMLR) | No (episodic/semantic/procedural, no persistence-semantics distinction) | Partial (retrieval as action) | No | No |
| **Zep/Graphiti** (Rasmussen et al. 2025) | No (bi-temporal validity ≠ cognitional status) | Partial (episode/entity/community tiers) | No | Partial (fact invalidation, not defeat) |
| **NARS/OpenNARS** (Wang 2006–) | Partial (NAL-1..9 *capability* levels; evidence-based (f,c) truth) | Partial (budget/attention) | **Yes (goals + questions first-class)** | Partial (revision, not level-crossing defeat) |
| **OpenCog/Hyperon AtomSpace** (Goertzel et al. 2023) | Partial (typed atoms, TruthValues, ECAN) | Partial (attention allocation) | **Yes (goal atoms)** | Partial (PLN revision) |
| **ASPIC+ / DeLP / Dung AF** | No (argument status, not cognitional level) | No | No | **Yes (undercut/rebut/undermine)** |
| **DEL epistemic planners** (Bolander; Wan et al.) | No | No | Partial (goals) | No |
| **Justification logic** (Artemov) | Partial (evidence terms `t:φ`) | No | No | No |
| **PROV / nanopublications / micropublications** | Partial (assertion+provenance+publication typing) | No | No | Partial (support/challenge) |
| **"Missing Knowledge Layer"** (Roynard 2026, arXiv:2604.11364) | **Partial-strong (4 layers w/ distinct persistence: supersession/decay/revision-gated/ephemeral)** | Partial (per-layer routing) | **Yes (prospective memory primitives in Rust impl)** | Partial (supersession, not cross-level defeat) |

**No single row has all four columns filled with "Yes."** The closest integrators are NARS and Hyperon (evidence + prospective), and Roynard 2026 (typed persistence + prospective primitives), but none enforce a *cognitional-level status ladder with legal transitions* AND *operation-indexed retrieval contracts* AND *cross-level defeat propagation* together.

**4. Lonergan-specific computational work: essentially absent.** Searches for "Lonergan computational / cognitional structure AI" return only *ethics/philosophy-of-technology* essays (Word on Fire; Notre Dame Church Life Journal applying the "transcendental precepts" to AI ethics) — NO computational cognition implementation. This strongly supports the originality of the *Lonergan-indexed* framing specifically, while the mechanisms it would implement are all precedented.

---

## Details

### Task 1 — Adversarial novelty verification (primary)

**The claim is defensible because each named lineage genuinely lacks specific pieces, and the *conjunction* appears nowhere.** But the adversarial duty is to state where the conversation *undersold* the prior art:

- **NARS is a stronger counterexample than "chunks carry no warrant."** NARS is precisely a system where every belief carries an evidence-grounded truth value `(f, c)` = (frequency, confidence), where frequency `f = w⁺/w` is the proportion of positive evidence and confidence `c = n/(n+k)` (with `k ≥ 1` a "personality parameter") increases monotonically as evidence accumulates — so confidence directly encodes *amount of evidence*. Goals and questions are **first-class statements** alongside beliefs (concept memory aggregates beliefs + goals + questions). Its revision rule prevents double-counting of evidence (the "stamp" mechanism) — a genuine warrant-discipline. What NARS lacks vs. the spine: (a) a *cognitional-level* status ladder (its NAL-1..9 are *capability* layers, not experience→understanding→judgment→decision deposits with *legal promotion gates*); (b) operation-indexed retrieval *contracts* that exclude strata by operational state; (c) explicit cross-*level* defeat propagation (revision is within-term). **Adopt-don't-rebuild signal: NARS's (f,c) evidence semantics and stamp-based double-counting prevention are exactly the "sentinel/self-grading" discipline the spine wants — borrow them.** OpenNARS and ONA are open-source (MIT/AGPL family).

- **OpenCog/Hyperon AtomSpace** is a typed (meta)graph where atoms carry TruthValues, attention values (STI/LTI via ECAN economic attention allocation), and goal atoms — genuinely a "registries as views over one substrate" architecture (the spine's own commitment). What it lacks: an *enforced* status ladder with legal transitions (typing is permissive, not gated) and cognitional-level stratification. MeTTa/AtomSpace are open-source.

- **Truth-maintenance descendants** (JTMS/ATMS) own defeat propagation but at *belief level only* — confirmed by 2024 reformulation work (arXiv:2411.10197) explicitly relating TMS justifications to argumentation labels. The conversation's characterization here is accurate.

- **Computational argumentation** (ASPIC+, DeLP, Dung) is the *rigorous home of defeat*: three attack types (undermining/rebutting/undercutting), ambiguity propagation vs. blocking, team defeat. This is where cross-level defeat propagation should draw its formal semantics — but argumentation frameworks are flat w.r.t. cognitional level and have no prospective/retrieval-contract machinery.

- **LLM-agent memory (2024–2026)** is converging on adjacent problems but not the spine. Zep/Graphiti (Rasmussen et al. 2025, arXiv:2501.13956) gives bi-temporal validity + episode-level provenance + fact invalidation — *temporal* supersession, not *warrant-gated cognitional promotion*; it reports "superior performance (94.8% vs 93.4%)" over MemGPT on Deep Memory Retrieval and "up to 18.5%" accuracy improvement on LongMemEval "while simultaneously reducing response latency by 90%." CoALA (arXiv:2309.02427) is explicitly criticized by Roynard (arXiv:2604.11364) for naming semantic vs. episodic memory *without operationalizing distinct persistence semantics* — the very gap the spine's status ladder fills. Roynard's four-layer model (Knowledge/Memory/Wisdom/Intelligence with supersession/decay/revision-gated/ephemeral persistence) is the **closest published cousin to the status ladder**, and it ships companion Rust/Python implementations (486 and 338+ tests respectively) with prospective-memory primitives and *evidence-gated* (anti-sycophancy) wisdom promotion. This is a must-read prior-art anchor and partially threatens the novelty claim — but it is a *persistence-semantics* layering, not a *cognitional-operation* stratification with legal-transition switchboard.

**Overall Task-1 verdict: VERIFIED that no single integrated system has all four, with the explicit caveat that (a) every component is precedented, (b) NARS + Hyperon + Roynard-2026 are meaningfully closer than the conversation stated, and (c) the genuinely novel contributions are the *Lonergan-cognitional-level typing* and the *conjunction under an enforced switchboard*.**

### Task 2 — Epistemic logic mapping stress test

**Most implementable as a runtime memory engine: typed-graph state machine with logical invariants checked at write time.** Reasoning:

- **DEL with action models** is the conversation's proposed formal counterpart (product update ≈ status promotion). It is elegant but **not a runtime engine**: general DEL epistemic planning is *undecidable* (Bolander & Andersen); decidable fragments are PSPACE-hard to EXPSPACE; Kripke models explode with nesting depth. It is a *verification/planning* tool. Symbolic normal forms help offline (ACDFs for KD45ⁿ give singly-exponential representations and tractable satisfiability for the alternating fragment, per Wan et al.; BDD-based symbolic model checkers like the DEMO/SMCDEL line make bounded problems feasible) — useful for *proving properties of the switchboard*, not for serving retrieval.

- **Justification logic (Artemov)** is the closest formal match to warrant-tracking: it replaces `□φ` with `t:φ` where `t` is an explicit evidence term, and — critically — an *observer* level can distinguish factive from non-factive justifications by inspecting evidence-term structure (Artemov's Russell's-Prime-Minister / Red Barn analyses). This directly models the spine's **sentinel independence**: the object agent cannot tell good from bad warrant, but an observer analyzing evidence terms can. The "Semirings of Evidence" work (Baur & Studer, arXiv:2308.05506) makes evidence terms *computable* (trust/cost/probability semirings). **Recommendation: use justification-logic evidence terms as the schema for `evidencing` edges** — this partially closes the "classical epistemic logic is flat w.r.t. cognitional level" gap the conversation flagged, because evidence terms carry structure that bare modalities do not.

- **Defeasible/argumentation semantics** should govern the *defeat propagation* edges (ASPIC+ attack typology).

- **Lightweight epistemic filters for LLM agents (2024–2026)** do NOT change the feasibility of full DEL at runtime; they confirm the pragmatic path is bounded, symbolic, write-time-checked invariants rather than online model checking.

**Bottom line:** implement the spine as a state machine whose *transitions* are the legal promotions, whose *invariants* are checked at write time by the integrity zome (the switchboard), and whose *edge schema* borrows justification-logic evidence terms and ASPIC+ defeat types. Reserve DEL/ACDF machinery for offline verification of the switchboard's soundness.

### Task 3 — Map onto FLOSSI0ULLK (compose, don't greenfield)

Mapping the four novel pieces to repo state, with the NOW/LATER/NEVER evidence gate:

| Novel piece | Repo status | Ternary framing (−1 risk / 0 trade-off / +1 benefit) | Gate |
|---|---|---|---|
| **Status ladder** | **(a) Partially Verified** — Claim Truth Model (4 labels) + ternary gateway + Provenance Packet exist; what's missing is *enforced legal transitions* between statuses | −1: over-rigid gates block iteration; 0: must encode transition table in integrity zome; +1: turns labels into guarantees, kills silent promotion | **NOW** — add status-transition validation to existing integrity-zome entry types; smallest artifact, highest leverage |
| **Retrieval contracts** | **(b) Specified but unbuilt** — shared-context bus exists; operation-indexed exclusion does not | −1: premature contracts starve agents of context; 0: needs an operational-state field on queries; +1: prevents cross-contamination of strata | **LATER** — gate on a dated milestone or ≥3 demonstrated retrieval-leakage cases |
| **Prospective registers** | **(c) Genuinely absent** | −1: new entry types add schema surface; 0: modest zome work; +1: open questions/intentions become first-class, enabling forward-looking agency (the piece the whole field lacks) | **NOW** — add open-question / open-intention integrity-zome entry types |
| **Defeat propagation** | **(b) Specified but unbuilt** — provenance/evidence edges exist; cross-level defeat does not | −1: cascade bugs can mass-retract; 0: needs ASPIC+ semantics + careful propagation bounds; +1: automatic consistency under new counter-evidence | **LATER** — after status ladder + registers prove out; borrow ASPIC+ attack typology |

**Sentinel-independence seam:** the reviewer≠writer invariant (R-VD-1) and EWMA reputation are the natural home for warrant-checking independence — but they are **NOT FOUND in accessible repo files** (Unverified-in-repo). This is the anti-self-grading mechanism and should be treated as Specified-at-best until confirmed. KERI (already named in the stack, but Specified/not-implemented) is the right cryptographic-attestation substrate for tamper-evident warrant receipts *later*.

**Smallest-artifact path (the +1 recommendation):** Start exactly where the conversation itself recommends — **four classical Lonergan levels (experience → understanding → judgment → decision) + typed edges + a hard status ladder enforced by the integrity zome**, plus prospective-register entry types. This is a minimal extension of already-Verified components, not a greenfield.

### Task 4 — Open problems

- **(a) Consolidation without frequency-collapse.** 2025–2026 LLM-agent work (MemoryOS EMNLP 2025 heat-score promotion; EverMemOS engram lifecycle; Pink, Wu, Vo, Turek, Mu, Huth & Toneva, "Position: Episodic Memory is the Missing Piece for Long-Term LLM Agents," arXiv:2502.06975, which frames episodic memory around five properties — long-term storage, explicit reasoning, single-shot learning, instance-specific memories, and contextual memories; and Roynard's DreamCycle) all implement episodic→semantic promotion — but **all use frequency/recency/heat as the promotion signal**, which is *exactly the frequency-collapse the spine warns against* (frequency ≠ higher viewpoint). **Genuinely open:** no published system promotes on *cognitional* grounds (a genuine insight/higher viewpoint) rather than access statistics. Roynard's *evidence-gated* (not frequency-gated) wisdom promotion is the nearest principled alternative and explicitly motivated by anti-sycophancy.
- **(b) Sentinel independence / self-grading.** Robustly documented: self-preference bias in LLM-as-judge is real and architecture-persistent. Panickssery, Bowman & Feng ("LLM Evaluators Recognize and Favor Their Own Generations," NeurIPS 2024, arXiv:2404.13076) show "the strength of self-preference bias is linearly correlated with the LLM's self-recognition capability" (tested on GPT-4/GPT-3.5/Llama 2 with CNN/DailyMail and XSUM); Wataoka et al. (arXiv:2410.21819) tie it to output perplexity/familiarity. The mitigation literature (independent judges, debiasing, reviewer-model-family separation) directly supports the reviewer≠writer invariant. Justification logic gives the *formal* observer/object separation. KERI gives cryptographic attestation. **Partially addressed, engineering-ready — but no turnkey solution; the reviewer≠writer + evidence-term-inspection combination is sound and should be built.**
- **(c) Pruning by dependency liveness not age.** Mature CS precedent exists: *liveness-based garbage collection* (reachability ≠ liveness). Hirzel, Diwan & Henkel show "liveness accuracy reduces the reachable heap size by up to 62% for our benchmark programs" — directly transplantable to knowledge-graph pruning by dependency reachability rather than age. **Largely solved in principle; the open part is defining "liveness" for cognitional nodes** (a node is live if it supports an open question, an unfulfilled intention, or an undefeated judgment) — which is precisely what prospective registers + defeat edges would make computable.

---

## Recommendations

**Stage 1 (NOW — smallest artifacts, minimal-extension):**
1. Add a **status-transition table enforced in the integrity zome** (the switchboard): nothing → affirmed except via warrant check; nothing → decided except via evaluation; nothing → planned except from decision; every promotion writes a trace. This upgrades the already-Verified Claim Truth Model from labels to guarantees.
2. Add **open-question and open-intention integrity-zome entry types** (prospective registers). These are absent everywhere and are the highest-novelty, lowest-cost build.
3. Resolve the **licence conflict** (GPL-3.0 vs. prose "Compassion Clause + Apache/GPL") — a governance blocker.
4. Adopt **NARS-style (f,c) evidence semantics with stamp-based double-counting prevention** for the evidencing edges rather than inventing new warrant arithmetic.

**Stage 2 (LATER — gate on ≥3 cases or a dated milestone):**
5. Operation-indexed retrieval contracts — build only after demonstrated stratum-leakage cases.
6. Cross-level defeat propagation using ASPIC+ attack typology, with hard propagation bounds to prevent mass-retraction cascades.
7. Confirm/build the reviewer≠writer (R-VD-1) + EWMA sentinel seam; add KERI attestation for warrant receipts.

**Stage 3 (NEVER until the four-level version proves out):**
8. The full fourteen-operation spine. The conversation's own recommendation (start with four levels) is correct; the fourteen-type expansion is speculative and should be gated on the four-level version demonstrating value in production.

**Benchmarks that would change staging:** if BEAM-style contradiction-resolution / temporal-reasoning scores on the four-level version clear a threshold, promote defeat propagation to NOW; if prospective registers show no agent uptake in 3 milestones, demote them.

**Alternative architecture path (anti-sycophancy requirement):** If the goal is a *working* warrant-bearing agent memory in the near term rather than a Lonergan-faithful research artifact, **do not build the spine from scratch — fork OpenNARS or build on Hyperon AtomSpace** (both FLOSS, both already provide evidence-based truth values + first-class goals/questions + attention-based retrieval) and add *only* the two genuinely missing pieces: the cognitional-level status ladder and prospective-register typing. This would deliver most of the spine's value at a fraction of the build cost, at the price of adopting NARS/Hyperon's ontology rather than a clean Lonergan mapping. Ternary assessment: −1 (loses Lonergan purity, inherits large codebases), 0 (integration effort with Holochain substrate), +1 (evidence semantics, defeat/revision, and prospective structures come for free and are battle-tested).

---

## Caveats
- **Repo direct-fetch was robots-blocked; all repo claims are second-hand via a subagent that read GitHub HTML.** Files where EWMA/adversarial/R-VD-1/"32/32 tests"/"ADR-10 v2.0" would be confirmed were inaccessible — those specific claims are **Unverified-in-repo**, not refuted.
- **The pasted conversation's claims are LLM output under verification, not ground truth.** Multi-AI agreement was treated as suspect; each verdict rests on a primary-source check (arXiv papers, Stanford Encyclopedia, project docs).
- **The novelty verdict is sensitive to definition.** "Exists nowhere integrated" is VERIFIED for the *strict conjunction with cognitional-level typing*; it would be FALSE if relaxed to "a system with evidence-bearing beliefs + first-class goals + revision" (NARS, Hyperon both qualify).
- **Roynard 2026 (arXiv:2604.11364) is a very recent, single-author position paper with feasibility-only (not superiority) evidence** and heavy grey-literature citation — treat as a prior-art signal, not settled science.
- **Benchmark scores cited across the agent-memory literature (LongMemEval, LoCoMo) are under a documented governance crisis** (answer-key errors, judge leniency) — directional, not authoritative.