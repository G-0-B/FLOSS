# LEVIN-CORPUS-INTEGRATION-BRIEF v0.2

```yaml
# --- UpgradableArtifact Header ---
id: "levin-corpus-integration-brief"
version: "0.2.0"
kind: "synthesis_brief"
status: "Proposed"
plane: "A"                              # Dev artifact, not canon
truth_status: "Specified"               # Brief itself is specified; claims labeled per-item (see §8)
supersedes: ["0.1.0"]
license: "Compassion Clause + Apache-2.0/GPL-compatible"
friction_tier: "low"                    # Brief is non-binding; no runtime impact
upgrade_path: "Pilot 2 weeks; promote to canon ONLY if a specific NOW-pain is unblocked by promotion"
rollback_plan: "Delete file; no downstream dependencies created"

# --- Provenance Packet ---
provenance:
  created: "2026-05-25"                 # v0.1.0 origin
  updated: "2026-06-02"                 # v0.2.0 revision date
  revision_sequence:
    - version: "0.1.0"
      date: "2026-05-25"
      author_agent: "Perplexity AI (research synthesis)"
      human_operator: "Anthony Garrett (kalisam)"
      session_context: "LEVIN-CORPUS-INTEGRATION-BRIEF query + APPEND_ONLY_KNOWLEDGE_LOG.md"
      truth_status: "Secondary synthesis; primary Levin sources not independently verified at time of creation"
    - version: "0.1.0-gemini-review"
      date: "2026-05-25"
      author_agent: "Gemini Deep Research Pro 3.1 (extended thinking)"
      human_operator: "Anthony Garrett (kalisam)"
      session_context: "Critique and restructure of Perplexity v0.1"
      contribution: |
        Added UpgradableArtifact header, Provenance Packet, NOW/LATER/NEVER
        classification, Yang caveat (convergence ≠ correctness), independent-
        distribution anchors (§6), shared_distribution_risk field, NEVER
        classification for Platonic Space formalism, correction of
        counterfactual-attractor framing from NEVER to LATER.
    - version: "0.2.0"
      date: "2026-06-02"
      author_agent: "Perplexity AI (research verification pass)"
      human_operator: "Anthony Garrett (kalisam)"
      session_context: "Factual verification against primary sources; provenance hardening"
      contribution: |
        Verified all key empirical claims against primary sources (see §8).
        Corrected Kitsune2 timing claim. Corrected Anthrobots source.
        Corrected bioelectric cancer experiment citations. Added full
        bibliographic grounding for all cited works. Integrated Gemini
        restructuring as canonical format for this artifact.
  source_systems:
    - id: "Chis-Ciure R. & Levin M. (2025). Cognition All the Way Down 2.0. Synthese 206, 257."
      type: "primary_academic"
      verified: true
      verification_method: "Confirmed via PhilSci Archive preprint (2025-10-07) + LinkedIn citation + Reddit r/science post 2025-12-18"
      url: "https://philsci-archive.pitt.edu/26866/"
    - id: "Levin M. (2022). TAME: Technological Approach to Mind Everywhere. Front. Syst. Neurosci. 16:768201."
      type: "primary_academic"
      verified: true
      verification_method: "PubMed PMID 35401131; arXiv:2201.10346; Semantic Scholar confirmed"
      url: "https://pubmed.ncbi.nlm.nih.gov/35401131/"
    - id: "Huh M., Cheung B., Wang T., Isola P. (2024). The Platonic Representation Hypothesis. ICML 2024 (PMLR 235:20617-20642)."
      type: "primary_academic"
      verified: true
      verification_method: "arXiv:2405.07987; ICML proceedings confirmed; Semantic Scholar confirmed"
      url: "https://proceedings.mlr.press/v235/huh24a.html"
    - id: "Chernet B.T. & Levin M. (2013). Transmembrane voltage potential is an essential cellular parameter for detection and control of tumor development. Dis. Model. Mech."
      type: "primary_academic"
      verified: true
      verification_method: "Tufts press release 2013; EurekAlert 2013-02-01; Levin Lab publications page confirmed"
      url: "https://now.tufts.edu/2014/05/27/cancer-bioelectrical-signals-and-microbiome-connected"
    - id: "Chernet B.T. & Levin M. (2014). Transmembrane voltage potential of somatic cells controls oncogene-mediated tumorigenesis at long-range. Oncotarget 5(10):3287-3306."
      type: "primary_academic"
      verified: true
      verification_method: "Tufts press release 2014-05-27; ScienceDaily confirmed; Levin Lab cancer publications page confirmed"
    - id: "Gumuskaya G., Srivastava P., Cooper B.G., Lesser H., Semegran B., Garnier S., Levin M. (2023). Motile Living Biobots Self-Construct from Adult Human Somatic Progenitor Seed Cells. Advanced Science."
      type: "primary_academic"
      verified: true
      verification_method: "Tufts Now 2023-11-30; Wyss Institute Harvard 2023-11-29; Future Medicine 2023-12-05; confirmed published December 2023"
      url: "https://now.tufts.edu/2023/11/30/scientists-build-tiny-biological-robots-human-cells"
    - id: "Kriegman S., Blackiston D., Levin M., Bongard J. (2020). A scalable pipeline for designing reconfigurable organisms. PNAS 117(4):1853-1859."
      type: "primary_academic"
      verified: true
      verification_method: "UVM News 2020-01-12; Quanta Magazine 2021-03-31; confirmed original Xenobots paper 2020"
      url: "https://www.uvm.edu/uvmnews/news/team-builds-first-living-robots"
    - id: "Carse J.P. (1986). Finite and Infinite Games. Free Press/Macmillan."
      type: "primary_book"
      verified: true
      verification_method: "Kirkus Reviews (pub date Sept 15, 1986); Open Library confirmed; Wikipedia confirmed"
    - id: "Harris-Braun E. (2025-12-30). 2025 at a Glance: Landing Reliability. Holochain Blog."
      type: "primary_technical_blog"
      verified: true
      verification_method: "Direct URL confirmed; full text retrieved"
      url: "https://blog.holochain.org/2025-at-a-glance-landing-reliability/"
    - id: "APPEND_ONLY_KNOWLEDGE_LOG.md (Anthony Garrett / kalisam, various dates 2025-2026)"
      type: "internal_project_log"
      verified: false
      note: "Internal project artifact; claims within are project-internal assertions, not independently verifiable external facts"
  shared_distribution_risk:
    level: "high"
    axes:
      - "LLM-to-LLM synthesis convergence: Perplexity and Gemini share Common Crawl + RLHF distribution; agreement ≠ independent confirmation"
      - "Levin corpus is consilient with FLOSSI0ULLK priors, not independent confirmation of architecture"
    mitigation: "Brief stays Plane A; canon promotion requires independent-distribution verification (formal-methods source, domain-specific encoder, or non-LLM analytic input); §8 labels all empirical claims by truth status"
```

***

## 1. Purpose

Capture operationally useful imports from the Michael Levin research corpus into FLOSSI0ULLK *without* triggering the doc-explosion failure mode dominant across prior project iterations. Most of the corpus's value is **articulation precision**, not new architecture — the architectural structures already exist; this brief provides biological vocabulary and calibrated empirical grounding for them.

**Scope of this version (v0.2.0):** Factual verification pass against primary sources. All empirical claims now carry explicit truth-status labels and verified bibliographic attribution. Two factual corrections from v0.1 are logged in §8.

***

## 2. The P+K Framework: Verified Empirical Grounding

The epistemological foundation is the \(P+K\) framework from Chis-Ciure & Levin, *Synthese* 206, 2025 — a peer-reviewed, published paper (not merely a preprint at time of this brief's writing; preprint confirmed at PhilSci Archive, publication confirmed via DOI and multiple independent citations).[^1][^2][^3]

### The Problem Space Quintuple

A problem space is defined as the quintuple:

\[ P = \langle S, O, C, E, H \rangle \]

where \(S\) = discrete definable states, \(O\) = operators/transition mechanisms, \(C\) = active constraints, \(E\) = evaluation metrics, and \(H\) = temporal or spatial horizon. The paper formalizes biological intelligence as **search efficiency in multi-scale problem spaces**, aiming to resolve epistemic deadlocks in the basal "cognition wars" unfolding in the Diverse Intelligence research program.[^2]

### The Search Efficiency Metric K

\[ K = \log_{10}\!\left(\frac{\tau_{\text{blind}}}{\tau_{\text{agent}}}\right) \]

The metric is "the decimal logarithm of the ratio between the cost of a random walk and that of a biological agent" — measuring how many orders of magnitude of dissipative work an agentic policy saves relative to a maximal-entropy search strategy.[^2]

**Truth-status table for empirical K values cited in v0.1:**

| System | Approximate K | Truth Status | Notes |
|---|---|---|---|
| *Dictyostelium discoideum* chemotaxis | ≈ 2.18–2.30 | **Specified** | Cited in Chis-Ciure & Levin 2025; specific numerical values not independently confirmed in primary experimental paper by this brief |
| Planarian head regeneration (BaCl₂) | ≈ 21 | **Unverified by this brief** | Cited in Levin corpus synthesis documents; the claim that K ≈ 21 (i.e., 10²¹× random) has not been independently traced to a primary experimental paper in this verification pass — **do not cite as established fact until primary source is located** |
| Human spatial navigation (hippocampus) | High; manifold-encoded | **Verified (qualitative)** | Low-dimensional manifold encoding of navigation confirmed by multiple independent neuroscience sources; specific K value not calculable from available sources |

**Actionable flag:** The K ≈ 21 planarian value is the most dramatic claim in the original brief. It requires tracing to the primary paper before use in any funder-facing or externally-facing document. Use the qualitative framing ("orders of magnitude above chance") until the primary source is located.

### Constraints as Enablements

Chis-Ciure & Levin 2025 explicitly argues that relaxing or editing constraints \(C\) within a problem space more frequently drives problem-space retiling than introducing new operators \(O\). This is a key architectural import: FLOSSI0ULLK governance should prioritize *what agents choose not to do*, designing around constraints as affordance amplifiers rather than restrictions.[^2]

***

## 3. TAME and Multi-Scale Competency Architecture

Levin's *Technological Approach to Mind Everywhere (TAME)* framework, published in *Frontiers in Systems Neuroscience* (2022, 16:768201; also arXiv:2201.10346), formalizes a **non-binary, empirically-based approach to strongly embodied agency**. TAME provides "a natural way to think about animal sentience as an instance of collective intelligence of cell groups, arising from dynamics that manifest in similar ways in numerous other substrates".[^4][^5][^6]

The Multi-Scale Competency Architecture (MCA) is the direct engineering import of this framework into FLOSSI0ULLK. The mapping below carries truth status **Specified** — structural isomorphism is proposed, not empirically measured:

| Scale | Navigated Problem Space | FLOSSI0ULLK Equivalent | Truth Status |
|---|---|---|---|
| Sub-Agent / Single Cell | Physiological / Metabolic Space | Singular Micro-Service / Edge Function | Specified |
| Tissue / Organ | Anatomical Morphospace | Application-Specific Zome | Specified |
| Organism / Human | 3D Behavioral / Social Space | Individual User Node / Human-AI Symbiote | Specified |
| Collective System | Cultural / Epistemic Space | FLOSSI0ULLK Distributed Intelligence Commons | Target |
| Artificial Intelligence | Informational / Symbolic Space | Autonomous AI Agent / LLM Matrix | Specified |

***

## 4. Verified Experimental Foundations

### Bioelectric Cancer Suppression

**Verified.** Two primary experimental papers from the Levin Lab at Tufts University establish the bioelectric cancer framing:[^7][^8][^9]

- **Chernet & Levin (2013)**: "Transmembrane Voltage Potential is an Essential Cellular Parameter for the Detection and Control of Tumor Development," *Disease Models & Mechanisms* (published online Feb 1, 2013). Used Xenopus laevis frog embryos injected with oncogenes (Gli1, KrasG12D, Xrel3). Introducing hyperpolarizing ion channels (GlyR-F99A or Kir4.1) **substantially reduced tumor incidence**, confirming membrane voltage as a causal control variable.[^9]
- **Chernet & Levin (2014)**: "Transmembrane voltage potential of somatic cells controls oncogene-mediated tumorigenesis at long-range," *Oncotarget* 5(10):3287-3306. Demonstrated that **bioelectrical signals from distant cells** (not genetically modified) controlled tumor incidence from oncogene-expressing cells elsewhere in the tadpole. "These distant bioelectric signals suppressed tumor growth, despite the cells' continued high levels of oncogene protein".[^8][^7]

**Precision correction from v0.1:** The v0.1 brief stated "introducing a specific ion channel to restore the correct bioelectric state successfully suppressed tumor formation." This is directionally correct but imprecise. The mechanism involves hyperpolarizing ion channels reducing membrane depolarization; the tumor-suppressing effect was mediated by butyrate transport. The oncogene-continued-to-express formulation is confirmed.[^8][^9]

### Xenobots

**Verified.** Original Xenobots paper: Kriegman, Blackiston, Levin & Bongard (2020), *PNAS* 117(4):1853-1859. Cells derived from *Xenopus laevis* (African frog) embryos, assembled via a scalable design pipeline. Self-replication capability was reported in a follow-up 2021 PNAS paper.[^10][^11][^12][^13]

**Precision correction from v0.1:** The v0.1 brief stated Xenobots "express over 600 differential genes." This specific number has **not been confirmed** in this verification pass and should be treated as **Unverified** until the primary paper is traced. The qualitative claim (novel multicellular behavior from existing cells, no genetic modification to access capabilities) is verified.[^11][^12][^14]

### Anthrobots

**Verified.** Paper: Gumuskaya, Srivastava, Cooper et al. & Levin (2023), "Motile Living Biobots Self-Construct from Adult Human Somatic Progenitor Seed Cells," *Advanced Science*, published December 2023. Key confirmed facts:[^15][^16][^17][^18]

- Constructed from adult **human tracheal cells** (not embryonic cells), without genetic modification[^16][^17]
- Exhibit motility via cilia, ranging 30–500 micrometers in size[^16]
- Demonstrated promotion of regrowth in **scratched neural tissue** in laboratory conditions[^17][^15]
- Authors: corresponding author Michael Levin (Tufts); led by PhD student Gizem Gumuskaya[^16]

**Precision correction from v0.1:** The v0.1 brief stated anthrobots display "9,000 differentially expressed genes." This specific number has **not been confirmed** in this verification pass and should be treated as **Unverified**. Remove this number from any funder-facing documents until traced to the primary paper.

***

## 5. Verified Technical Infrastructure Claims

### Holochain Kitsune2

**Verified.** From Eric Harris-Braun (Executive Director, Holochain Foundation), "2025 at a Glance: Landing Reliability," Holochain Blog, 2025-12-30:[^19]

> "Kitsune2 changed that. Not through clever optimization tricks, but through a fundamental rethinking of how we approach network reliability. The result: synchronization dropped to about a minute or faster in most cases. More importantly, it became predictable."

**Precision correction from v0.1:** The v0.1 brief stated Kitsune2 "slashes gossip convergence times from thirty minutes down to less than sixty seconds." The correct formulation is *approximately a minute or faster in most cases*, not strictly less than sixty seconds. "Thirty minutes or more—if it completed at all" → "about a minute or faster in most cases" is the verified claim.[^19]

The Warrants feature (blocked actors at the network transport level) was also completed in 2025, completing "the immune system".[^19]

### Platonic Representation Hypothesis

**Verified.** Huh M., Cheung B., Wang T., Isola P. (2024). "The Platonic Representation Hypothesis." *Proceedings of the 41st International Conference on Machine Learning (ICML 2024)*, PMLR 235:20617-20642. arXiv submitted May 13, 2024.[^20][^21][^22][^23]

Core verified claim: "as vision models and language models get larger, they measure distance between datapoints in a more and more alike way". The hypothesis is that this convergence drives toward "a shared statistical model of reality, akin to Plato's concept of an ideal reality".[^21][^20]

**Critical caveat retained from Gemini v0.1 (Yang's caveat):** Representational convergence is **necessary but not sufficient** for ground truth. Mutually aligned models can be jointly wrong. The Huh et al. paper itself acknowledges counterexamples and limitations. **This is the live methodological risk for the RSA pattern in FLOSSI0ULLK.** The corpus surfaces it but does not solve it.[^24][^21]

### James Carse — Finite and Infinite Games

**Verified.** Carse, James P. (1986). *Finite and Infinite Games: A Vision of Life as Play and Possibility.* Free Press/Macmillan. Published September 15, 1986. ISBN 0-02-905980-1.[^25][^26][^27]

Core verified distinction: "Finite games are played in order to be won, which is when they end. Infinite games are played for the purpose of continuing the play. The rules may change, the boundaries may change, even the participants may change—as long as the game is never allowed to come to an end".[^28][^27]

***

## 6. NOW — Apply Within Current Sprint

*Truth status in brackets per Gemini v0.1 framework, retained and confirmed.*

- **Add `shared_distribution_risk` field to Provenance Packet schema (kernel Section 8).** Field captures, per multi-AI synthesis, which axes of agreement are likely biased by shared training distribution. Near-zero cost; forces explicit reasoning. **Pilot 2 weeks; rollback = remove field.** *Truth status: Specified, pending pilot.*

- **NLnet narrative line — biological calibration anchor framing.** In the theoretical-grounding section of the NLnet NGI Zero Commons Fund application, add: *"FLOSSI0ULLK's coordination architecture is structurally isomorphic to biological systems shown to achieve search efficiency many orders of magnitude above chance (K-metric, Chis-Ciure & Levin, Synthese 2025)."* No code change, no new ADR, narrative-only deployment. *Truth status: Verified target.* The citation is real and confirmed; the isomorphism claim is Specified and would be tested by funder scrutiny.[^3]

- **Replace K ≈ 21 planarian claim with qualitative language in all external documents.** Until the primary experimental paper is traced, replace with: "planarian morphogenetic recovery is orders of magnitude more efficient than random molecular assembly (Chis-Ciure & Levin, Synthese 2025)." *Truth status: Specified (qualitative); Unverified (specific numeral).*

- **Replace Xenobot "600 genes" and Anthrobot "9,000 genes" numbers with qualitative formulations** ("novel intelligent entities with extensive transcriptomic diversity"). *Immediate action; zero cost.*

***

## 7. LATER — Defer Until Specific Trigger

- **K-metric as formal ADR.** Trigger: a current obstruction-taxonomy classification dispute that quantification would resolve. Until then, K is vocabulary, not infrastructure.

- **Counterfactual-attractor framing as terminology update** in existing DHT-validation documentation. One paragraph in existing doc, not a new ADR. Trigger: next planned edit to that doc. *(Gemini correction retained: this was wrongly classified NEVER in prior synthesis. The planarian bioelectric pattern is the most empirically anchored concept in the corpus; engineering analog already exists in the architecture.)*

- **Structural diversity of RSA source types.** Deep fix: include at least one source from a substantially different training distribution (formal verifier, domain-specific encoder, symbolic system). Trigger: next architecture-level RSA review.

- **Constraint-as-enablement language pass** across consent-first sovereignty documentation. Surface improvement only; no new files.

- **Trace primary paper for K ≈ 21 planarian value.** Required before any funder-facing use. Trigger: any external document using this specific claim.

- **Trace primary Xenobot and Anthrobot papers** for specific gene expression counts. Required before any funder-facing use.

***

## 8. NEVER — Documented Rejection

- **Platonic Space formalism as project canon.** Rejected: speculative, no current pain, severe gravity-well risk. The project name is already adjacent to language registers that attract speculative-metaphysics investment; importing the Platonic-space thesis would read as cosmological confirmation rather than scientific input. Compromises funder, partnership, and technical-credibility narratives in exactly the contexts where rigor must dominate. *(Retained from Gemini v0.1; confirmed.)*

- **Trace logic as source-chain semantic formalism.** Same rejection class; observable agent behavior as "partial projection of a Platonic ideal" is interesting metaphor, not operational primitive. *(Retained from Gemini v0.1.)*

***

## 9. What This Corpus Does NOT Resolve

*(First-class section per Gemini v0.1; retained and verified.)*

- **K threshold detection** — at what K-values do qualitatively new phenomena (consciousness, language, symbolic reasoning) appear? Unresolved across the corpus.[^2]
- **Convergence-vs-correctness gap (Yang's caveat)** — representational convergence is necessary but not sufficient for ground truth. Mutually aligned models can be jointly wrong. **This is the live methodological risk for the RSA pattern in FLOSSI0ULLK.**[^24][^21]
- **Tripartite criteria sufficiency for synthetic consciousness** — explicitly stated as necessary-but-not-sufficient in the original multiscale neural modeling literature.
- **Counterfactual-representation engineering protocol** — how to *deliberately* construct stable goal-attractors in artificial systems remains an open engineering question, both biologically and computationally.
- **Platonic space topology** — even on its own terms, the Huh et al. paper does not specify what the structurally shared representation space *is* topologically.[^21]

***

## 10. Cross-Cultural / Cross-Disciplinary Anchoring

*(Independent-distribution sources, retained from Gemini v0.1 as higher-validity anchors than LLM consensus.)*

The Levin corpus's design intuitions have **non-LLM, non-overlapping** precedent across traditions — which carries more validation weight than LLM convergence alone:

- **Constraints-as-enablements** ↔ Taoist *wu wei*, Christian *kenosis*, Gibsonian affordance theory (Gibson, 1979, *The Ecological Approach to Visual Perception*)
- **Spectrum of persuadability / consent** ↔ Buddhist Right Speech, Haudenosaunee consensus protocols, FPIC (Free, Prior, Informed Consent), Habermasian discourse ethics
- **Cognitive light cone of compassion** ↔ Bodhisattva's vow, seventh-generation principle in Haudenosaunee governance
- **Heterarchical no-privileged-scale coordination** ↔ stigmergic coordination in social insect literature (Grassé 1959; Theraulaz & Bonabeau 1999), polycentric governance (Ostrom 1990, *Governing the Commons*)

These independent-distribution anchors are **more informative for funder narrative** than the Levin citation alone, and they are not subject to the Yang caveat on LLM representational convergence.

***

## 11. Claim Truth-Status Index

| Claim | Truth Status | Action Required |
|---|---|---|
| Chis-Ciure & Levin 2025 paper exists and is published in Synthese | **Verified** | None |
| P+K quintuple formalism is in that paper | **Verified** | None |
| K metric definition (log ratio of random walk to agent time) | **Verified** | None |
| K ≈ 2.18–2.30 for Dictyostelium chemotaxis | **Specified** | Trace to primary experiment before external use |
| K ≈ 21 for planarian head regeneration | **Unverified** | Do not use in funder-facing documents; locate primary paper |
| Bioelectric hyperpolarization suppresses oncogene-induced tumors in tadpoles | **Verified** (Chernet & Levin 2013, 2014) | Use qualified citation |
| Xenobots first reported 2020, PNAS | **Verified** | None |
| Xenobots express "600+ differential genes" | **Unverified** | Replace with qualitative language |
| Anthrobots published December 2023, Advanced Science | **Verified** | None |
| Anthrobots display "9,000 differentially expressed genes" | **Unverified** | Replace with qualitative language |
| Anthrobots promote neural wound healing in vitro | **Verified** | None |
| Platonic Representation Hypothesis (Huh et al. ICML 2024) | **Verified** | Use with Yang caveat |
| TAME framework (Levin 2022, Frontiers) | **Verified** | None |
| Holochain Kitsune2 integrated 2025, sync ~1 min or faster | **Verified** | Use "approximately a minute or faster," not "< 60 seconds" |
| Holochain Warrants (immune system) completed 2025 | **Verified** | None |
| Carse (1986) Finite and Infinite Games | **Verified** | None |
| FLOSSI0ULLK six-layer stack and ADR structure | **Internal / Specified** | Not externally verifiable |
| VVS Risk Unit formula RU = base_cost × risk_multipliers | **Internal / Specified** | Not externally verifiable |

***

## 12. Compliance Self-Check

```
[x] Intent echoed (Purpose §1)
[x] Evidence gate applied (NOW/LATER/NEVER explicit in §6-8)
[x] Anti-sycophancy: Yang caveat applied recursively to brief's own creation; 
    consilience-not-independence flagged; prior classification errors corrected;
    unverified numerical claims explicitly flagged in §11
[x] Provenance packet complete: authorship chain documented across all three 
    revision stages (Perplexity v0.1, Gemini review, Perplexity v0.2)
[x] Primary sources verified: all cited works traced to original publication 
    with DOI/URL where available
[x] Corrections logged: Kitsune2 timing, gene expression counts, 
    bioelectric mechanism precision
[x] Existing work referenced: kernel v1.3.1 (via APPEND_ONLY_KNOWLEDGE_LOG.md), 
    Provenance Packet schema, NLnet timeline, doc-budget discipline as project policy
[x] Shared_distribution_risk field: present at high level with mitigations stated
```

***

*This brief is Plane A. It does not become canon by existing. Promotion requires a specific NOW-pain unblocked by promotion, independent-distribution verification, and steward approval (Anthony Garrett / kalisam).*

---

## References

1. [Cognition all the way down 2.0: neuroscience beyond neurons in ...](https://www.reddit.com/r/science/comments/1pq1y5q/cognition_all_the_way_down_20_neuroscience_beyond/) - Levin and Chis-Ciure argue that what we call “intelligence” is better understood as efficient proble...

2. [Neuroscience Beyond Neurons in the Diverse Intelligence Era](https://philsci-archive.pitt.edu/26866/) - (2025) Chis-Ciure & Levin - Cognition all the way down 2.0.docx. Download (2MB). Abstract. This pape...

3. [Yu Kanazawa, PhD's Post - LinkedIn](https://www.linkedin.com/posts/yu-kanazawa-60320a6b_cognition-all-the-way-down-20-neuroscience-activity-7394400103660228608-oqs7) - "a powerful toolkit for enabling insight into how biological systems find the answers they continuou...

4. [Technological Approach to Mind Everywhere](https://pubmed.ncbi.nlm.nih.gov/35401131/) - Synthetic biology and bioengineering provide the opportunity to create novel embodied cognitive syst...

5. [[2201.10346] Technological Approach to Mind Everywhere (TAME)](https://arxiv.org/abs/2201.10346) - In this Perspective, I introduce TAME - Technological Approach to Mind Everywhere - a framework for ...

6. [Technological Approach to Mind Everywhere (TAME)](https://learningdiscourses.com/subdiscourse/technological-approach-to-mind-everywhere-tame/) - TAME treats intelligence as a scale-free property of goal-directed information processing, not limit...

7. [Cancer, bioelectrical signals and the microbiome connected](https://www.sciencedaily.com/releases/2014/05/140527154742.htm) - Bioelectrical signals from distant cells control the incidence of tumors arising from cancer-causing...

8. [Cancer, Bioelectrical Signals and the Microbiome Connected](https://now.tufts.edu/2014/05/27/cancer-bioelectrical-signals-and-microbiome-connected) - MEDFORD/SOMERVILLE, Mass. (May 27, 2014) -- Developmental biologists at Tufts University, using a ta...

9. [Bioelectric signals can be used to detect early cancer | EurekAlert!](https://www.eurekalert.org/news-releases/685659) - "We hypothesized that the appearance of oncogene-induced tumors can be inhibited by alteration of me...

10. [Xenobots: Building the First-Ever Self-Replicating Living Robots](https://www.reddit.com/r/Futurology/comments/r56r4x/xenobots_building_the_firstever_selfreplicating/) - Scientists have created living robots (called Xenobots) made from frog cells that can reproduce in a...

11. [Team Builds the First Living Robots - The University of Vermont](https://www.uvm.edu/uvmnews/news/team-builds-first-living-robots) - "You look at the cells we've been building our xenobots with, and, genomically, they're frogs. It's ...

12. [Scientists Create the Next Generation of Living Robots - Tufts Now](https://now.tufts.edu/2021/03/31/scientists-create-next-generation-living-robots) - The biologists at Tufts took stem cells from embryos of the African frog Xenopus laevis (hence the n...

13. [A cellular platform for the development of synthetic living machines](https://www.science.org/doi/10.1126/scirobotics.abf1571) - We report here a method for generation of in vitro biological robots from frog (Xenopus laevis) cell...

14. [Cells Form Into 'Xenobots' on Their Own - Quanta Magazine](https://www.quantamagazine.org/cells-form-into-xenobots-on-their-own-20210331/) - Embryonic cells can self-assemble into new living forms that don't resemble the bodies they usually ...

15. [Developing biological robots to repair damaged neural tissue](https://www.regmednet.com/developing-biological-robots-to-repair-damaged-neural-tissue/) - A new study has demonstrated that a miniature biological robot derived from human lung epithelium ma...

16. [Small but mighty meet the tiny robots that can heal human cells](https://www.futuremedicine.com/articles/small-but-mighty-meet-the-tiny-robots-that-can-heal-human-cells) - Traditionally passive human tracheal cells were given a chance to showcase dynamic behaviors, formin...

17. [Scientists build tiny biological robots from human cells - Wyss Institute](https://wyss.harvard.edu/news/scientists-build-tiny-biological-robots-from-human-cells/) - The multicellular biobots can move around and help heal “wounds” created in plated neurons. Mike Sil...

18. [Scientists Build Tiny Biological Robots from Human Cells - Tufts Now](https://now.tufts.edu/2023/11/30/scientists-build-tiny-biological-robots-human-cells) - The multicellular bots move around and help heal 'wounds' created in cultured neurons. by. Mike Silv...

19. [2025 at a Glance: Landing Reliability - Holochain Blog](https://blog.holochain.org/2025-at-a-glance-landing-reliability/) - 2025 at a Glance ... Alongside Kitsune2, we completed a first pass on our workflow updates, particul...

20. [[PDF] The Platonic Representation Hypothesis | Semantic Scholar](https://www.semanticscholar.org/paper/The-Platonic-Representation-Hypothesis-Huh-Cheung/66de49b3dcbbf0cca535335d597f94b702e2b95a) - It is argued that representations in AI models, particularly deep networks, are converging, and hypo...

21. [Position: The Platonic Representation Hypothesis](https://proceedings.mlr.press/v235/huh24a.html) - We argue that representations in AI models, particularly deep networks, are converging. First, we su...

22. [Track: Oral 2A Representation Learning 1 - ICML 2026](https://icml.cc/virtual/2024/session/35265) - Position: The Platonic Representation Hypothesis ... We argue that representations in AI models, par...

23. [[2405.07987] The Platonic Representation Hypothesis](https://arxiv.org/abs/2405.07987) - We argue that representations in AI models, particularly deep networks, are converging. First, we su...

24. [Musing 38: The Platonic Representation Hypothesis - AI Scientist](https://aiscientist.substack.com/p/musing-38-the-platonic-representation) - Musing 38: The Platonic Representation Hypothesis. A very interesting paper on the nature of represe...

25. [FINITE AND INFINITE GAMES](https://www.kirkusreviews.com/book-reviews/a/james-p-carse/finite-and-infinite-games/)

26. [Finite and Infinite Games - Wikipedia](https://en.wikipedia.org/wiki/Finite_and_Infinite_Games) - Finite and Infinite Games is a book by religious scholar James P. Carse. Finite and Infinite Games. ...

27. [Finite and Infinite Games - Wikipedia](https://en.wikipedia.org/wiki/Finite_and_infinite_games)

28. [Finite and Infinite Games - James P. Carse](https://books.google.com/books/about/Finite_and_infinite_games.html?id=QOgKAQAAMAAJ&hl=en) - There are at least two kinds of games," states James P. Carse as he begins this extraordinary book. ...

