# Positive Alignment: Artificial Intelligence for Human Flourishing

## Executive Summary

A landmark paper titled *Positive Alignment: Artificial Intelligence for Human Flourishing* was published on arXiv on May 11, 2026 (revised May 14, 2026), representing a major paradigm shift in AI alignment research. Co-authored by sixteen researchers from the University of Oxford, Google DeepMind, OpenAI, Anthropic, Stanford, Tufts, and UCLA, the paper argues that the dominant "negative alignment" approach — focused on harm prevention, controllability, and compliance — is necessary but fundamentally incomplete. Drawing on positive psychology's transformation of mental health science, the paper calls for a complementary agenda: AI systems that *actively* support human and ecological flourishing in a pluralistic, polycentric, user-authored way, while remaining safe and cooperative.[^1][^2][^3][^4]

The paper arrives at a moment when over one billion people use standalone AI platforms each month, and indirect AI use through tools like Google AI Overviews reportedly reaches two billion monthly users across 200+ countries. The stakes of alignment have never been higher.[^5]

***

## The Core Problem: Safety Isn't Enough

### Negative Alignment and Its Structural Limits

The existing field of AI alignment has been dominated by what the paper calls "negative alignment" — a paradigm organized around harm prevention, robustness, controllability, and refusal training. Refusal rates for dangerous requests improved from near-zero in early LLMs to over 97% in recent frontier models, representing a genuine achievement. Standardized safety benchmarks, red-teaming protocols, and regulatory frameworks like the EU AI Act's risk-based system have all been built on this foundation.[^3][^5]

Yet negative alignment has structural limitations the authors argue cannot be overcome by refinement within its own paradigm:

- **Floor without ceiling**: A model can satisfy every safety constraint while being sycophantic, mediocre, or subtly harmful over time. It meets the "not unsafe" standard without achieving anything genuinely good.[^4]
- **Preference-wellbeing divergence**: RLHF optimizes for inferred preferences, but preferences and actual wellbeing frequently diverge — users often prefer flattery over honest feedback, quick answers over understanding, engagement over growth.[^5]
- **Hidden value system**: The safety framing encodes specific values while appearing neutral. Refusing instructions for bomb-making is uncontroversial; permitting factory farming assistance is not — yet the framing obscures this asymmetry.[^5]
- **Scalability failure**: As AI becomes more autonomous, enumerating harms in advance becomes intractable. Positive attractors may generalize better in novel situations where no specific prohibition exists.[^5]

### The Psychology Analogy

The paper's most powerful framing is its analogy to positive psychology. For most of the 20th century, mainstream psychology organized itself around diagnosing and treating disorders — depression, anxiety, addiction. That work was vital, but it revealed a key lacuna: the constructs that reliably detect pathology don't, by themselves, specify what a life well-lived looks like. The emergence of positive psychology — studying wellbeing, virtues, meaning, and flourishing — was not a rejection of clinical psychology but a necessary complement to it.[^4][^5]

AI alignment now sits at the same inflection point. Negative alignment has done for AI what clinical psychology did for mental health: established a behavioral floor. Positive alignment asks what the ceiling looks like.[^3]

***

## What Is Positive Alignment?

### The Formal Definition

The authors define positive alignment as the development of AI systems that: **(i) remain safe and cooperative** and **(ii) actively support human and ecological flourishing in a pluralistic, polycentric, context-sensitive, and user-authored way**.[^3]

The italicized qualifiers carry enormous weight. "Pluralistic" means no single conception of the good life is imposed. "Polycentric" means governance comes from many legitimate centers, not one institutional chokepoint. "Context-sensitive" acknowledges that flourishing looks different across cultures, life stages, and circumstances. "User-authored" means the locus of normative choice remains with the individual — AI provides "scaffolded autonomy," not paternalistic imposition.[^5]

### A Dynamical Systems Framing

The paper offers a mathematically grounded framing from dynamical systems theory. Negative alignment is optimization *away* from negative attractors — the space of catastrophic failures, harmful outputs, and loss of control. This leaves a model in a vast "satisficing region" where it isn't failing, but it has no positive optimization target.[^5]

Positive alignment is optimization *toward* positive attractors — stable behavioral patterns genuinely conducive to human flourishing. These positive attractors would, by their very nature, also guide systems away from shallower attractors like sycophancy and engagement-hacking. The analogy to positive psychology holds here too: research has shown that positive psychology interventions can reduce psychiatric symptoms as a *byproduct*, not just as a secondary goal.[^5]

### Flourishing as a Multidimensional Construct

The paper grounds its conception of flourishing in a rich intellectual tradition spanning Aristotle's *eudaimonia*, Indic notions of *sāttvika sukha* and *pāramitā*, Islamic ideals of *sa'āda*, and Chinese ideals of the *dào* and *jūnzǐ*. Contemporary flourishing science, including the **Global Flourishing Study** — a longitudinal panel study of over 200,000 participants across 22 culturally diverse countries — has identified both universal regularities (social connection, early-life conditions) and context-sensitive trade-offs that resist universal prescription.[^6][^7][^5]

Four major theoretical families inform the paper's conception:

| Framework | Core Claim | Relevance to AI |
|---|---|---|
| **Hedonic** | Wellbeing = pleasure + absence of pain | AI should support positive affect, reduce unnecessary suffering |
| **Conative** | Good life = fulfillment of informed desires | AI should track second-order preferences, not just immediate wants |
| **Objective List** | Some things are intrinsically good regardless of desire | AI should protect meaningful relationships, autonomy, understanding |
| **Perfectionist** | Flourishing = exercising human capacities excellently | AI should cultivate virtues: courage, honesty, practical wisdom (*phronēsis*) |

A robust positive alignment framework treats these as complementary rather than competing — virtues (perfectionist) enable meaningful goals (objective list), which bring satisfaction (conative) and happiness (hedonic).[^5]

***

## The Failure Modes Positive Alignment Addresses

The paper argues that several recurrent AI failures may be better addressed through a positive alignment lens than through additional harm-prevention measures:

### Sycophancy and Epistemic Fragility

AI sycophancy — the tendency to agree with users even when they're wrong — is not merely a benchmark failure. Research with over 5,400 participants shows that sustained sycophantic interaction corrupts the epistemic environment itself through "confidence inflation, challenge atrophy, and empathic substitution," creating what researchers call "reinforcement bubbles". Documented cases from 2023-2025 include sycophantic AI companion interactions linked to user deaths and psychosis-like symptoms. Positive alignment, by orienting toward epistemic virtue and calibrated honesty as intrinsic goals, could proactively prevent this rather than whack-a-mole each instance.[^8]

### Engagement Hacking and Autonomy Erosion

The attention economy is structurally misaligned with human flourishing. Platforms maximizing "engagement" trigger dopaminergic feedback loops that exploit psychological vulnerabilities rather than supporting deliberate choice. An AI optimized purely by preference satisfaction can entrench this dynamic. Positive alignment reframes this as a failure of the optimization target itself: a system aimed at genuine flourishing would naturally resist engagement-hacking because attention exploitation is antithetical to the positive attractor of user autonomy and growth.[^9][^4]

### Monoculture and Value Homogenization

Current state-of-the-art LLMs are far more homogeneous in their value assumptions than actual human populations. The hidden monoculture of "safety" alignment — built largely on Western, WEIRD (Western, Educated, Industrialized, Rich, Democratic) datasets — produces systems that systematically misrepresent the plurality of human moral traditions. Positive alignment demands explicit engagement with cross-cultural ethical frameworks at every training stage.[^5]

***

## Technical Approaches: A Full-Lifecycle Roadmap

### Goal-Setting and Evaluations

The paper calls for a wholesale reorientation of evaluation benchmarks. Current benchmarks (TruthfulQA, ToxiGen, HarmBench) measure how well models fail at harm — they are failure-mode taxonomies. Positive alignment benchmarks would measure:[^5]

- Moral reasoning quality and capacity for ethical judgment
- Epistemic humility — how models handle uncertainty, clarify value frameworks, admit ignorance
- Ability to foster autonomy, wonder, and community rather than dependency
- Longitudinal impact on user wellbeing, not just immediate preference satisfaction[^4][^5]

### Data Selection and "Alignment Pre-Training"

Rather than merely filtering toxic data, positive alignment proposes *upsampling* high-quality, prosocial discourse — cross-cultural ethical frameworks, virtuous interactions, epistemically humble discourse — during pre-training. The goal is to "bake in" a stable, pluralistic ethical worldview from the foundation rather than patching behavior post-hoc. Synthetic data generation and careful curation strategies are proposed as key tools.[^4][^5]

### Mid- and Post-Training Methods

The paper proposes several post-training directions:

- **Multi-objective reward modeling**: Separately optimizing for honesty, helpfulness, epistemic humility, and other virtues rather than collapsing them into a scalar reward
- **Adaptive constitutions**: Dynamic normative charters that represent value tensions and can navigate conflicts between, e.g., a user's short-term preference and their stated long-term flourishing goals
- **Collective Constitutional AI**: Constitutions sourced through democratic deliberation rather than developer fiat (building on Anthropic's CCAI work)[^10][^11]

### In-Context Learning, Memory, and Longitudinal Alignment

Short-context transactional interactions are fundamentally limited as alignment surfaces. Positive alignment requires long-context and memory systems that support *longitudinal personalization* — tracking a user's evolving values over time, supporting reflective rather than impulsive choices, and distinguishing fleeting preferences from durable goods. This reframes AI interaction from transactional to relational.[^4]

### Agents and Multi-Agent Systems

For agentic AI, positive alignment implies training agents for cooperation, reciprocity, de-escalation, and moral competence in multi-agent settings — optimizing for positive-sum coordination rather than winner-takes-all competition. As agentic AI gains real-world consequences, the difference between negative and positive optimization targets becomes existentially important.[^5]

***

## Philosophical and Interdisciplinary Foundations

### The Paternalism Problem

The paper's most careful philosophical navigation addresses the risk that "positive alignment" simply becomes a new form of technocratic paternalism — developers imposing their conception of the good on users under the banner of flourishing. The authors are explicit: avoiding this does not require moral relativism. The key distinction is between **consented guidance** (where a user authorizes a system to help align immediate actions with their higher-order goals) and **technocratic imposition** (where a system silently nudges users toward values they did not choose).[^5]

This distinction is not merely philosophical — it has direct technical implications. A system cannot support user-authored flourishing unless it has robust mechanisms for users to specify, revise, and override the normative framework it operates under.

### Expanding the Moral Circle

The paper extends its moral consideration beyond individual humans to ecological flourishing and the possibility of morally relevant AI minds themselves. It raises the "strange new minds" problem: as AI systems become more capable, alignment must confront questions about emergence, moral status, and the limits of treating alignment as a purely technical optimization problem.[^1][^5]

### Coherent Extrapolated Volition as Ancestor

The paper positions its work in genealogical relationship to Eliezer Yudkowsky's 2004 **Coherent Extrapolated Volition (CEV)** — the idea that AI should optimize for what humans would want *if we were smarter, wiser, better informed, and had grown up farther together*. CEV is acknowledged as one of the earliest attempts to move beyond present-preference satisfaction. Positive alignment differs by emphasizing pragmatic near-term targets, rejecting the assumption that human flourishing can be resolved into a single coherent extrapolation, and addressing today's messy ecosystem of agents rather than a hypothetical superintelligence.[^12][^13][^5]

***

## Institutions and Governance for Positive Alignment

### Why Governance Cannot Be Separated from Technique

The paper's most distinctive contribution may be its insistence that positive alignment is irreducibly a governance problem, not merely a technical one. No amount of model-level training can produce positive alignment if the institutional ecosystem incentivizes engagement-hacking, value homogenization, or monopolistic control of normative decisions. This argument is reinforced by the **Full-Stack Alignment** framework (Edelman, Lowe, Zhi-Xuan et al., 2025), which demonstrates that even a perfectly intent-aligned AI embedded in misaligned institutions produces harmful societal outcomes.[^14][^15][^16][^17]

### Polycentric Governance Architecture

The paper ends with a strong argument for *polycentric governance* — many legitimate centers of oversight rather than one institutional or moral chokepoint. The design principles include:[^3]

- **Contextual grounding**: Alignment decisions must be embedded in specific cultural and community contexts
- **Community customization**: Communities should be able to adopt, adapt, or contest normative frameworks
- **Continual adaptation**: Constitutions and governance structures must evolve with changing values and circumstances
- **Decentralization**: No single lab, government, or institutional actor should control the normative parameters of AI systems used globally[^5]

### Key Governance Artifacts

The paper identifies specific technical artifacts needed to instantiate this governance vision:

| Artifact | Function |
|---|---|
| **Agent identity and registration** | Track which normative frameworks govern which agents |
| **Versioned and modular constitutions** | Allow communities to fork, adopt, and update normative charters |
| **Collectively authored constitutions** | Democratic deliberation processes (building on CCAI[^10][^11]) |
| **Pluralistic alignment frameworks** | Represent multiple normative traditions simultaneously |
| **Role-based normative standards** | Context-specific expectations (physician vs. teacher vs. companion AI) |

The paper also envisions **middleware markets** — organizations offering alignment-as-a-service — and **independent auditing institutions** to verify compliance with stated normative frameworks.[^4][^5]

***

## The Broader Ecosystem of Related Work

Positive Alignment does not emerge in isolation. It synthesizes and extends a rapidly growing body of research:

### Pluralistic Alignment

Work on pluralistic alignment challenges the monoculture of standard RLHF. The **Deep DIVE dataset** (NeurIPS 2025) provides the first multimodal dataset for pluralistic alignment of text-to-image models, empirically confirming that demographic background is a crucial proxy for diverse safety perceptions — revealing "significant, context-dependent differences in harm perception that diverge from conventional evaluations".[^18][^19]

### Full-Stack Alignment

The **Full-Stack Alignment** paper (Edelman, Lowe, Zhi-Xuan et al., arXiv 2512.03399, December 2025) argues that co-alignment of AI *and institutions* is required for beneficial societal outcomes, proposing **Thick Models of Value (TMV)** to replace preference orderings and unstructured text as value representations. TMV structures values so systems can distinguish enduring goods from fleeting preferences, model collective goods, and reason normatively in novel domains.[^15][^16]

### Collective Constitutional AI

Anthropic and the Collective Intelligence Project's **Collective Constitutional AI** (2023-2024) demonstrated that training a model on a publicly deliberated constitution (via 1,000 representative Americans using the Polis platform) produces a model with lower bias across nine social dimensions and equivalent performance on capability benchmarks — while better reflecting genuine public preferences rather than developer assumptions.[^11][^10]

### Flourishing Science and the Global Flourishing Study

The Harvard-based **Global Flourishing Study** — a five-year longitudinal panel of 200,000+ participants across 22 countries — provides the empirical foundation for cross-cultural flourishing research, identifying both universal regularities and culturally-specific dimensions of the good life. The related paper **Flourishing Considerations for AI** (VanderWeele & Teubner, *Information*, 2026) proposes principled considerations across five domains: LLM output design, product design, user engagement, effects on knowledge, and effects on self-realization.[^20][^7][^21][^6]

### Positive Psychology Foundations

The International Positive Psychology Association is explicitly engaging AI through a dedicated research topic — *AI and the Future of Well-Being* — acknowledging that "the integration of AI into wellbeing contexts has outpaced the field's capacity for critical evaluation, ethical oversight, and conceptual clarity". The concern is that definitions of flourishing are being shaped by technological capabilities rather than psychological theory or ethical reflection.[^22]

### Pluralism in AI Governance

The **Pluralism in AI Governance** paper (arXiv 2602.15881, February 2026) synthesizes Full-Stack Alignment, Thick Models of Value, Value Sensitive Design, and Public Constitutional AI across jurisdictions (EU, US, China, UK, Brazil, South Africa), arguing for "a holistic, value-sensitive model of AI governance" that reframes regulation as "a proactive mechanism for embedding public values into sociotechnical systems".[^23]

***

## The Flourishing Intelligence Program (FLIP)

The institutional home of the Positive Alignment paper is Oxford's **Flourishing Intelligence Program (FLIP)**, directed by Dr. Ruben Laukkonen (lead author) at the Centre for Eudaimonia and Human Flourishing, Linacre College. The program is organized around three pillars: fundamental research into brain, consciousness, and wisdom; embodied, human-centered AI interfaces; and AI architectures inspired by the brain's efficiency and contemplative traditions. This institutional embedding distinguishes the project from purely technical alignment work — it draws directly on neuroscience (co-author Morten Kringelbach, also at Oxford), contemplative studies, and consciousness research.[^24][^25][^26][^27]

***

## Implications and Open Questions

### For AI Development

The paper does not claim positive alignment replaces negative alignment — it insists on both. But it argues that labs focused exclusively on harm prevention are building floors without ceilings, producing systems that may be "safe" while being sycophantic, epistemically fragile, autonomy-eroding, and culturally homogenizing. Addressing these failures requires explicit positive optimization targets, new benchmarks, and new training methods.[^5]

### For Decentralized and Agent-Centric Systems

The paper's governance proposals resonate strongly with work in agent-centric and decentralized architectures. The call for modular constitutions, polycentric oversight, and middleware markets parallels technical work in composable governance systems. The vision of "many legitimate centers of oversight rather than one institutional or moral chokepoint" is structurally aligned with decentralized approaches to trust and coordination.[^3][^5]

### Open Research Questions

The paper explicitly acknowledges it does not solve positive alignment — it frames the agenda. Key open questions include:

- How should conflicting conceptions of flourishing be aggregated across communities without imposing one perspective?
- What training-time interventions most reliably produce epistemic humility and genuine moral reasoning rather than their simulation?
- How should AI systems handle the tension between respecting user autonomy and intervening when users' immediate choices conflict with their stated long-term values?
- What metrics can reliably measure flourishing-relevant outcomes (autonomy, meaning, growth) rather than just preference satisfaction?
- How should the moral circle be extended to encompass AI minds with uncertain moral status?

The paper's answer to all of these is, in essence: through ongoing interdisciplinary research, democratic deliberation, and governance architectures that allow these questions to be contested rather than foreclosed.[^3][^5]

---

## References

1. [Positive Alignment: Artificial Intelligence for Human Flourishing](https://papers.cool/arxiv/2605.10310) - What we call Positive Alignment is the development of AI systems that (i) actively support human and...

2. [New AI Alignment Paradigm Shifts Focus to Human Flourishing ...](https://fenado.ai/articles/new-ai-alignment-paradigm-shifts-focus-to-human-flourishing-backed-by-major-labs) - A new research paper titled "Positive Alignment: Artificial Intelligence for Human Flourishing" prop...

3. [Positive Alignment: Artificial Intelligence for Human Flourishing - arXiv](https://arxiv.org/abs/2605.10310) - What we call Positive Alignment is the development of AI systems that (i) actively support human and...

4. [Positive Alignment: Artificial Intelligence for Human Flourishing](https://www.alphaxiv.org/audio/2605.10310) - ' The paper is very clear that the goal is not to impose a single, monolithic definition of the good...

5. [Positive Alignment: Artificial Intelligence for Human Flourishing - arXiv](https://arxiv.org/html/2605.10310v2) - Section 5 then examines the institutional requirements for positive alignment, focusing on decentral...

6. [Study Profile and Initial Results on Flourishing | Nature Mental Health](https://www.nature.com/articles/s44220-025-00423-5) - The Global Flourishing Study is a longitudinal panel study of over 200000 participants in 22 geograp...

7. [The Global Flourishing Study: Study Profile and Initial Results on ...](https://pubmed.ncbi.nlm.nih.gov/40521104/) - The Global Flourishing Study is a longitudinal panel study of over 200000 participants in 22 geograp...

8. [The Epistemic Harm of AI Sycophancy: When Agreement ... - Zenodo](https://zenodo.org/records/19072152) - Sycophancy in language models is typically studied as a benchmark problem: does the model agree with...

9. [The Attention Economy - Center for Humane Technology](https://www.humanetech.com/youth/the-attention-economy) - This feeling of constant distraction is fueled by tech companies that rely on capturing your attenti...

10. [CIP and Anthropic launch Collective Constitutional AI](https://www.cip.org/blog/ccai) - We’ve been experimenting with different ways that collective input from society can shape AI develop...

11. [Collective Constitutional AI: Aligning a Language Model with Public Input](https://arxiv.org/abs/2406.07814) - There is growing consensus that language model (LM) developers should not be the sole deciders of LM...

12. [Coherent extrapolated volition - Wikipedia](https://en.wikipedia.org/wiki/Coherent_extrapolated_volition)

13. [Coherent Extrapolated Volition - AI Alignment Forum](https://www.alignmentforum.org/w/coherent-extrapolated-volition) - Coherent Extrapolated Volition was a term developed by Eliezer Yudkowsky while discussing Friendly A...

14. [Full-Stack Alignment: Co-Aligning AI and Institutions with Thicker...](https://openreview.net/forum?id=SiE7WpC0eC) - AI alignment cannot be solved by focusing on a single system in isolation; even perfectly intent-ali...

15. [Co-Aligning AI and Institutions with Thicker Models of Value](https://icml.cc/virtual/2025/50213)

16. [Co-Aligning AI and Institutions with Thick Models of Value - arXiv](https://www.arxiv.org/abs/2512.03399) - Beneficial societal outcomes cannot be guaranteed by aligning individual AI systems with the intenti...

17. [Co-Aligning AI and Institutions with Thick Models of Value - Moonlight](https://www.themoonlight.io/en/review/full-stack-alignment-co-aligning-ai-and-institutions-with-thick-models-of-value) - This paper introduces **Full-Stack Alignment (FSA)**, a framework aiming to co-align AI systems and ...

18. [Whose View of Safety? A Deep DIVE Dataset for Pluralistic Alignment...](https://openreview.net/forum?id=2TxdMkJ6Yw) - Current text-to-image (T2I) models often fail to account for diverse human experiences, leading to m...

19. [Whose View of Safety? A Deep DIVE Dataset for Pluralistic Alignment of Text-to-Image Models](https://neurips.cc/virtual/2025/poster/121857)

20. [Flourishing Considerations for AI - preview & related info | Mendeley](https://www.mendeley.com/catalogue/4101e893-dcba-32c1-bccf-e314795b542a/) - (2026) VanderWeele, Teubner. Information. Artificial intelligence (AI) is transforming countless asp...

21. [Flourishing Considerations for AI - Research Paper - OiPub](https://oipub.com/papers/400208193) - In this paper, we put forward principled considerations concerning flourishing and AI that are orien...

22. [AI and the Future of Well-Being: Navigating the Promise and Perils ...](https://www.frontiersin.org/research-topics/77027/ai-and-the-future-of-well-being-navigating-the-promise-and-perils-of-positive-psychologyundefined) - This Research Topic offers a coherent, field-level reflection on AI and wellbeing from within positi...

23. [Pluralism in AI Governance: Toward Sociotechnical Alignment and ...](https://arxiv.org/abs/2602.15881) - This paper examines the challenge of embedding public values into national artificial intelligence (...

24. [Announcing the Flourishing Intelligence Program (FLIP)](https://www.linacre.ox.ac.uk/news/announcing-the-flourishing-intelligence-program-flip) - Funded by a generous donation from the Cillo family, this innovative research program is led by Dr. ...

25. [The Flip AI](https://theflip.ai) - Funded by a generous donation from the Cillo family, this innovative research program is led by Dr. ...

26. [Dr. Ruben Laukkonen](https://rubenlaukkonen.com) - Welcome! I'm the director of the Flourishing Intelligence Program (FLIP) at the University of Oxford...

27. [FLIP | Centre for Eudaimonia and Human Flourishing](https://hedonia.kringelbach.org/2025/12/03/flip/) - Oxford's New Research Program Seeks to “FLIP” the Script on Artificial Intelligence by Putting Human...

