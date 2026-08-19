# Cryptographically Verifiable Context Artifacts for AI-to-AI and Human-AI-Human Co-Evolution

## Executive Summary

This report synthesizes the current state of research and practical methodology for constructing a **plausibly highest-functioning, comprehensive, evolving context artifact** — a portable, cryptographically verifiable unit of knowledge that can be passed between AI models (AI-to-AI) and between humans and AI (human-AI-human) to enable continuous, verified co-evolution. The artifact must carry cryptographic provenance of sources and timestamps, be encoded in a concise token-efficient format, and be amenable to iterative prompting loops that upgrade the artifact's fidelity over successive exchanges. Key flagged resources for the human-to-AI-to-human phase are explicitly marked throughout.

***

## Part I: The Context Artifact Problem

The core challenge: current AI-to-AI exchanges are **ephemeral and unverified**. State evaporates between sessions, and no standard mechanism asserts when information entered the artifact, from which source, or whether it has been tampered with. Multi-agent architectures need a shared, persistent, and trustworthy substrate — not just a longer prompt.[^1]

The ideal artifact must satisfy six simultaneous structural properties: it must be *self-describing*, *cryptographically bound* to sources, *token-efficient*, *human-readable*, *machine-traversable*, and *evolutionarily stable* across model handoffs. Current research confirms no single existing format satisfies all six simultaneously. The solution is therefore a **composed architecture** that layers existing open standards.[^2]

Three parallel research tracks converge to address this:
- **Cryptographic provenance standards** (C2PA, Atlas, MAIF, zkVM)
- **Token-efficient interchange formats** (ObjectGraph, TRON, Markdown-KV, YAML)
- **Co-evolution methodologies** (data-prompt co-evolution, EvoSkills, NOVA loop, SuperBrain)

***

## Part II: Cryptographic Provenance — The Trust Foundation

### C2PA: The Leading Open Provenance Standard

The Coalition for Content Provenance and Authenticity (C2PA), governed by the Linux Foundation Joint Development Foundation, defines the most mature open standard for cryptographic content provenance. C2PA encodes provenance through a **manifest** containing *assertions* about origin: who created content, when, how, and from which source ingredients. Multiple assertions are grouped into a *claim* and cryptographically signed with keys authenticated by standard PKI.[^3][^4]

Key properties for context artifact use:
- Manifests form a **directed acyclic graph** — if ingredient assets also carry C2PA manifests, full provenance lineage is preserved across transformations[^3]
- Google (C2PA steering member since 2024), Adobe, Microsoft, BBC, Arm, Intel, and Truepic are founding/steering members, giving the standard production credibility[^5][^6]
- C2PA v2.1 (2024) tightens tamper-resistance against a broader range of attacks[^6]

🔖 **FLAG (Human-AI-Human):** C2PA's *Content Credentials* concept is directly applicable to human-generated source documents fed into the artifact pipeline. Humans can attach C2PA-signed credentials to their contributions, creating a verifiable human-to-artifact provenance chain.[^7]

### MAIF: The AI-Native Artifact Container

**Multimodal Artifact File Format (MAIF)** is the most directly relevant format for the AI-to-AI artifact paradigm. Proposed by Narajala, Bhatt, et al. (Nov 2025), MAIF is an AI-native container that unifies text, images, audio, sensor data, and serialized models with semantic embeddings, cryptographic provenance, and granular access control in a single portable unit.[^8][^9]

MAIF's hierarchical block architecture (inspired by ISO BMFF/MP4) comprises:
- **Header block**: file identifier, version, global root hash (tamper-evident), manifest pointer
- **Modality blocks**: text, image/video, audio, sensor streams, ONNX-serialized AI models
- **Semantic Layer block**: dense multimodal embeddings, knowledge-graph fragments, embedded HNSW index for retrieval
- **Security Metadata block**: cryptographic proofs (block hashes, digital signatures), access control lists (ACLs)

MAIF achieves **up to 225× semantic compression** while preserving semantic fidelity through novel cross-modal attention and cryptographic binding algorithms. Production benchmarks show 2,720.7 MB/s ultra-high-speed streaming with enterprise-grade security. MAIF transforms data from passive storage into an *active trust enforcement mechanism* — the artifact monitors its own integrity.[^9][^10][^11]

🔖 **FLAG (Human-AI-Human):** MAIF's Semantic Layer block (knowledge-graph fragments + embeddings) is directly useful for human-authored knowledge, enabling a human to contribute verified semantic content that AI models can retrieve without re-processing the full artifact.

### Atlas: ML Pipeline Provenance

**Atlas** (Spoczynski, Melara, Szyller — Intel, 2025) provides fully attestable ML pipelines using open supply-chain provenance specifications (SLSA, SBOM/SPDX 3.0, CycloneDX 1.6). Every artifact ingested or produced by an ML pipeline is cryptographically hashed; the provenance chain maintains verifiable links between artifacts; Trusted Execution Environments (Intel TDX, AMD SEV-SNP) protect pipeline integrity.[^12][^13]

Atlas's three-stage verification: (1) validate digital signatures match expected parties; (2) inspect transformation metadata for TEE-backed attestations; (3) validate lineage by tracing the provenance chain. This directly addresses the AI context artifact problem: each version of the evolving artifact can be attested back to its originating pipeline stage.[^12]

### Unified Evidentiary Framework (arXiv 2026)

A 2026 paper from the legal-cryptographic domain proposes a unified proof object for AI-generated content:[^14]

\[ \pi = (\sigma, \omega, \zeta, \lambda) \]

Where \(\sigma\) is a cryptographic provenance manifest, \(\omega\) is a robust watermark detection score, \(\zeta\) is a zero-knowledge attestation, and \(\lambda\) is a laundering descriptor summarizing transformations applied to the artifact since generation. This tuple structure maps well to a context artifact header that must survive adversarial conditions.[^14]

### Zero-Knowledge Compilation Provenance

For software artifacts, **zkVM-based provenance** (Ron & Monperrus, 2026) compiles source with zero-knowledge virtual machines, producing both the compiled output and a cryptographic proof attesting compilation was performed on claimed source with claimed compiler. Applied to context artifacts: each distillation pass can carry a zk-proof that the summarization process was faithfully executed, binding the compressed artifact back to its sources without exposing full source content.[^15]

### d3cipher / LockStock: Agent-Level Provenance

For agentic operations within the artifact exchange pipeline, the d3cipher LockStock system implements **hash-chained agent identity**, where every agent action is backed by a mathematically verifiable causal history. Features include: (a) autonomic per-action credential invalidation via Autonomic Atomic Agentic Authentication (AAAA); (b) 6-pass verification kernel (sequence integrity, chain linkage, hash recomputation, matrix evolution, live stamp verification, payload seal); (c) causal audit trail with no clock dependency; (d) MLS-based agent-to-agent E2E encryption.[^16]

***

## Part III: Token-Efficient Interchange Formats

Cryptographic provenance alone is insufficient — the artifact must fit within practical context windows and minimize cost per iteration. Research in 2025–2026 has systematically benchmarked formats.

### Format Benchmark Summary

| Format | Token Efficiency | Nested Data Accuracy | Best Use Case | Key Refs |
|--------|-----------------|---------------------|--------------|---------|
| **ObjectGraph** | 60–95% reduction vs baseline | No accuracy loss (p>0.05) | Agent document traversal | [^2][^17] |
| **Markdown-KV** | ~50% vs JSON | Highest (60.7%) | Human-readable KV pairs | [^18] |
| **YAML** | ~16% vs JSON | 62.1% nested | Nested structured config | [^18] |
| **TRON** | Up to 27% vs JSON | Within 14pp of JSON | Agentic tool schemas | [^19] |
| **TOON** | 18–28% vs JSON | 43–47.5% | Simple flat data | [^19][^18] |
| **Markdown Table** | ~62% vs JSON | 51.9% | Tabular display | [^18] |
| **JSON** | Baseline | 52.3% | Universal compatibility | [^20] |

### ObjectGraph: The Highest-Efficiency Candidate

**ObjectGraph** (arXiv 2026) reconceives document structure as a typed knowledge graph traversable by LLM agents. It formalizes six structural properties no existing format satisfies simultaneously and proves ObjectGraph satisfies all six. Empirical evaluation across 5 document classes and 8 task types shows **60–95% token reduction with no statistically significant accuracy degradation**. Crucially, ObjectGraph's *Progressive Disclosure Model* allows agents to query only the subgraph they need, avoiding full document prefill — directly compatible with MAIF's hierarchical block structure.[^17][^2]

🔖 **FLAG (Human-AI-Human):** ObjectGraph's human-authored and human-readable property means the artifact remains legible to human participants in the human-AI-human loop without requiring a parser.

### Compiled AI: Amortized Token Costs

**Compiled AI** (arXiv 2026) demonstrates that pre-compiling LLM generation logic into deterministic code artifacts achieves **57× token reduction at 1,000 transactions** compared to runtime inference. Break-even occurs at ~17 transactions. For an iterative prompting loop that reuses the same context artifact structure repeatedly, pre-compiling the artifact schema and distillation pipeline dramatically reduces per-iteration cost.[^21]

### Context Caching: KV State Preservation

Agentic workload research (arXiv 2026) finds that with effective context caching, **84.6–99.5% of input tokens are reused across turns**, making decode-dominated workloads the standard rather than repeated full-context prefill. The implication: the context artifact's stable sections (provenance headers, established knowledge, prior-session summaries) should be architected to maximize cache hit rates, with only the *delta layer* injected fresh per iteration.[^1]

### Cross-Lingual Token Arbitrage

A 2026 middleware study shows that pre-flight prompt rewriting (cross-lingual translation to English + compact `[CONTEXT]/[TASK]` format) reduces prompt tokens by **34–47%** with accuracy unchanged or improved. This is applicable to the artifact's human-language sections when targeting multilingual deployments.[^22]

***

## Part IV: Co-Evolution Methodologies

### Data-Prompt Co-Evolution (Living Test Set)

**Data-Prompt Co-Evolution** (Lee & Kahng, 2025–2026) operationalizes the principle that a *living test set* and prompt instructions should evolve in tandem. The interactive system guides developers to: discover edge cases; articulate rationales for desired behavior; iteratively evaluate revised prompts against a growing test set. Applied to context artifacts: each iteration adds new verified test cases to the artifact's evaluation layer, and the artifact's instruction/schema evolves to reflect newly discovered edge cases.[^23][^24]

🔖 **FLAG (Human-AI-Human):** The data-prompt co-evolution methodology is a direct template for the human-AI-human loop: humans discover edge cases, AI generates candidate instruction refinements, humans validate — forming a bidirectional Living Artifact.[^25]

### EvoSkills: Cross-Model Portable Skill Packages

**EvoSkills** (arXiv 2026) couples a Skill Generator that iteratively refines multi-file skill packages with a Surrogate Verifier that co-evolves to provide actionable feedback. Key finding: *agents create better skills than human-curated ones* because they capture reasoning patterns and tool-use strategies that agents actually need. Self-evolved skills transfer across model families — Claude-evolved skills transferred to six additional model families improve performance by +36 to +44 percentage points. This demonstrates that context artifacts encoding evolved skills are portable across model substrates.[^26]

### NOVA: The Generate-Verify-Accumulate-Retrain Loop

The **NOVA framework** (arXiv 2026) formalizes the "generate, verify, accumulate, retrain" loop as an adaptive sampling process over a knowledge space. NOVA identifies failure modes: contamination, forgetting, exploration failure, and acceptance failure. Critically, **human guidance can break the autonomous exploration barrier** — when a human changes the sampling distribution to include valid artifacts outside the previous support, the reachable valid set strictly expands. This validates the human-in-the-loop role in the iterative artifact upgrade cycle.[^27]

🔖 **FLAG (Human-AI-Human):** NOVA's human guidance mechanism is the theoretical grounding for *why* human-AI-human loops outperform fully autonomous AI-AI loops — humans expand the exploration frontier.

### Multi-Agent Evolve: LLM Self-Improvement via Co-evolution

**Multi-Agent Evolve** (Chen et al., 2025) instantiates a Proposer, Solver, and Judge from a single LLM co-evolving through a self-rewarding loop, without external verifiers or human-curated data. Applied to artifact management: a multi-agent system can propose distillation candidates, solve the compression problem, and judge quality — all generating cryptographically chained action records via MAIF or d3cipher primitives.[^28]

### Dual-Helix Co-Evolutionary Prompt Optimization

**Helix** (arXiv 2026) implements a dual-helix co-evolutionary multi-agent system for prompt optimization and question reformulation. Two populations — prompt variants and question reformulations — co-evolve together, each improving the other. This directly applies to context artifact schema evolution: the artifact's retrieval interface and its content evolve in lockstep.[^29]

### AIBuildAI-2: Self-Updating Knowledge System

**AIBuildAI-2** (arXiv 2026) demonstrates a knowledge-enhanced agent with an *evolving* knowledge system: after each run, a knowledge-builder agent distills experience into a structured takeaway appended to the bottom-level knowledge set, incrementally updating high-level knowledge instructions. This is the operational template for the context artifact's *evolution layer* — each AI-to-AI or human-AI exchange produces a verified distillation that updates the artifact.[^30]

***

## Part V: Attribution and Human Content Integration

### Sovereign Context Protocol (SCP)

**SCP** (Panchigar, Rush, Canabarro — arXiv March 2026) is an open-source protocol inspired by Anthropic's MCP that standardizes how LLMs connect to *creator-owned* human-generated data, with every access event logged, licensed, and attributable. SCP defines six core methods:[^31]
1. Creator profiles
2. Semantic search
3. Content retrieval
4. Trust/value scoring
5. Authenticity verification
6. Access auditing

SCP exposes both REST and MCP-compatible interfaces, making it immediately composable with existing agent frameworks. It introduces a log-proportional revenue model ensuring creators receive attribution when their content enters the AI training or inference pipeline.[^32][^31]

🔖 **FLAG (Human-AI-Human):** SCP is the primary protocol for the human-to-AI direction of the human-AI-human artifact loop. Human contributors can register content through SCP with verified attribution, and the artifact's provenance header can embed SCP access logs as its human-provenance layer.

### AD4M + Holochain: Agent-Centric Substrate

The **Agent-centric Distributed Application Meta-Ontology (AD4M/ADAM)** defines three classes: Agents, Languages, and Perspectives — a spanning layer that enables many-to-many mappings between user interfaces and existing web technologies. Agents communicate by creating **cryptographically signed Expressions** using AD4M Languages; private, locally stored graph databases (Perspectives) associate data across Languages. AD4M now includes a **built-in MCP server** enabling direct AI agent interaction.[^33][^34]

For the context artifact architecture: AD4M's Perspective (local knowledge graph) maps directly to the artifact's Semantic Layer; its signed Expressions are the provenance unit; Holochain provides the distributed hash table (DHT) for tamper-evident storage and validation rule enforcement.[^35][^36]

🔖 **FLAG (Human-AI-Human):** AD4M's agent-centric model where humans are full agents — not just users — makes it the optimal substrate for human-AI-human artifact handoffs. Human perspectives and AI perspectives are symmetrically represented.

### Science Context Protocol (SCP-Science)

A second SCP — **Science Context Protocol** (arXiv Dec 2025) — provides a universal specification for describing and invoking scientific resources spanning software tools, models, datasets, and physical instruments. It enables secure, large-scale collaboration between heterogeneous AI systems and human researchers while enhancing reproducibility. Directly relevant for research-grade context artifacts where the knowledge corpus includes scientific literature.[^37]

🔖 **FLAG (Human-AI-Human):** Science Context Protocol is the primary integration point for verified academic sources entering the artifact's knowledge layer, ensuring full lineage from primary literature to compressed artifact.

***

## Part VI: Proposed Artifact Architecture

Based on the synthesized research, the **Optimal Verifiable Context Artifact (OVCA)** is a layered composite structure:

### OVCA Layer Stack

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 0: PROVENANCE HEADER                             │
│  - C2PA manifest (origin assertions, PKI signatures)    │
│  - Atlas lineage chain (TEE-attested transformation log)│
│  - Timestamps: cryptographic (not wall-clock dependent) │
│  - π-tuple: (σ, ω, ζ, λ) per unified evidentiary frame │
├─────────────────────────────────────────────────────────┤
│  LAYER 1: STABLE KNOWLEDGE CORE (cache-optimized)       │
│  - ObjectGraph typed knowledge graph (60-95% token red) │
│  - YAML-structured settled facts + source citations     │
│  - MAIF Semantic Layer: embeddings + HNSW index         │
│  - SCP access log (human-generated content attribution) │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: DELTA LAYER (per-iteration fresh injection)   │
│  - New verified findings (Markdown-KV, ~50% token sav.) │
│  - EvoSkills-style distilled skill packages             │
│  - Living test set (data-prompt co-evolution)           │
│  - NOVA accumulation: verified + flagged items          │
├─────────────────────────────────────────────────────────┤
│  LAYER 3: EVOLUTION METADATA                            │
│  - Iteration counter + session hash chain               │
│  - d3cipher/LockStock agent action audit trail          │
│  - Dual-helix schema evolution log                      │
│  - Human validation signatures (SCP / AD4M Expressions) │
├─────────────────────────────────────────────────────────┤
│  LAYER 4: HUMAN INTERFACE LAYER (H-AI-H bridge)         │
│  - Human-readable ObjectGraph summary                   │
│  - Creator attribution index (SCP profiles)             │
│  - Shared Mental Model section (team/task/interaction)  │
│  - XIL-ADR cycle log (human feedback + rationales)      │
└─────────────────────────────────────────────────────────┘
```

### Artifact Identity and Versioning

Each OVCA version receives a **content-addressed hash identity** (collision-resistant, as in Atlas) plus a **sequential chain link** (as in d3cipher), creating an immutable lineage: `OVCA_v(n)` cryptographically links to `OVCA_v(n-1)`. Any tampering breaks the chain. The provenance header carries the full transformation history per the Atlas three-stage verification model.[^16][^12]

### Token Budget Management

Following compiled AI principles: the OVCA schema is compiled once and amortized across iterations. Per-turn injection targets only the delta layer. With 84–99% KV cache reuse for the stable core, effective new tokens per iteration converge toward just the delta. Target budget allocation:[^21][^1]

| Section | Format | Token Share |
|---------|--------|-------------|
| Provenance Header | YAML + hash | ~5% |
| Stable Knowledge Core | ObjectGraph | ~30% |
| Delta Layer | Markdown-KV | ~40% |
| Evolution Metadata | YAML | ~10% |
| Human Interface Layer | Markdown prose | ~15% |

***

## Part VII: Iterative Shared Prompting Methodology (AI-to-AI)

The planned iterative shared prompting loop follows the NOVA generate-verify-accumulate cycle combined with EvoSkills co-evolutionary verification:[^26][^27]

### Phase 1 — Initialization
1. Bootstrap OVCA_v0 with seed knowledge, empty provenance chain, compiled schema
2. Sign with initial C2PA manifest (timestamp, source assertions, creator profile)
3. Register human-generated inputs via SCP (if any) with access log entry
4. Compute ObjectGraph representation of knowledge core

### Phase 2 — AI-to-AI Exchange Iteration
1. **Propose**: Model A receives OVCA_v(n), generates distilled delta (new findings, refined skills, test cases)
2. **Verify**: Surrogate Verifier (Helix/EvoSkills pattern) evaluates delta against living test set
3. **Attest**: Delta passes through Atlas-style TEE attestation; zk-proof generated
4. **Accumulate**: Verified delta appended to knowledge core; provenance chain extended
5. **Re-compress**: ObjectGraph re-indexes; token budget enforced; redundant nodes pruned
6. **Chain**: `OVCA_v(n+1)` = `OVCA_v(n)` hash + delta hash → signed new manifest
7. **Transmit**: OVCA_v(n+1) passed to Model B with full chain visible in header

Each iteration's **verification step** is the critical quality gate — unverified deltas are flagged, not discarded, following NOVA's distinction between contamination and forgetting failure modes.[^27]

### Phase 3 — Human-AI-Human Bridge

🔖 **FLAG (Human-AI-Human):** The following methodology synthesizes resources explicitly flagged throughout this report:

**Outbound (AI → Human):**
- OVCA Human Interface Layer (Layer 4) renders the current artifact in human-readable ObjectGraph summary
- SCP attribution index gives humans visible credit for their contributions
- Shared Mental Model section (from human-AI augmentation research) explicitly names: What is our goal? What are the AI's limitations? Who does what?[^38]
- XIL-ADR cycle log (Explanatory Interactive Machine Learning) records human feedback rationales for each revision[^39]

**Inbound (Human → AI):**
- Human validates or refutes delta items in the living test set (data-prompt co-evolution)[^24]
- Human registers new source documents via SCP (creator profile + authenticity verification)[^31]
- Human-authored Expressions signed via AD4M and appended to the Evolution Metadata layer[^33]
- Human exploration guidance (NOVA): human expands the sampling distribution to valid artifacts AI could not autonomously reach[^27]
- Human assigns trust/value scores via SCP scoring method — these propagate to the artifact's knowledge graph edge weights[^31]

**Loop Closure:**
- After human review, a new OVCA_v(n+1) is generated incorporating human-validated items
- Human signature is embedded in the C2PA manifest as a verified assertion (human-as-creator provenance)[^3]
- The resulting artifact carries a verifiable mixed-provenance chain: AI-generated sections attested by Atlas/zkVM + human-generated sections attested by SCP/C2PA

***

## Part VIII: Flagged Resources for Human-AI-Human Phase

The following resources were identified as directly applicable to the human-to-AI-to-human artifact methodology and are flagged for the next research iteration:

| Resource | Relevance | Source |
|----------|-----------|--------|
| **Data-Prompt Co-Evolution** (Lee & Kahng 2025) | Living test set as human-AI artifact scaffold | [^24][^25] |
| **Sovereign Context Protocol (SCP)** | Human content attribution, access logging, trust scoring | [^31][^32] |
| **AD4M / ADAM Layer** (Coasys) | Agent-centric signed Expressions, human-AI symmetric agents | [^33][^34] |
| **XIL-ADR** (Explanatory Interactive ML, PMC 2023) | Human-in-loop cyclic artifact refinement with rationale logging | [^39] |
| **NOVA Framework** (arXiv 2026) | Formalizes human guidance expansion of AI exploration frontier | [^27] |
| **Human-AI Augmentation: From Augmentation to Symbiosis** (arXiv 2026) | Shared Mental Models + co-adaptation theory | [^38] |
| **HADA Architecture** (arXiv 2026) | Role-specific human stakeholder agents in multi-agent pipeline | [^40] |
| **C2PA Content Credentials v2.1** | Human-generated content provenance standard | [^6][^7] |
| **Science Context Protocol (SCP-Science)** | Verified academic sources integration into artifact | [^37][^41] |
| **SuperBrain / Collective Intelligence** (MIT SQI) | Human-LLM dyads as collective intelligence unit | [^42][^43] |
| **HAI-Co² Framework** | Preference-based human-AI co-construction via natural language | [^44] |
| **Incentivized Symbiosis** (arXiv 2024) | Web3/blockchain-based human-AI social contract with enforceable rules | [^45] |
| **Creative Intelligence Loop (CIL)** (arXiv 2025) | Sociotechnical framework for responsible human-AI co-creation | [^46] |
| **A-Mem: Agentic Memory** (NeurIPS 2025) | Zettelkasten-style interconnected memory network, 33–50% token budget | [^47][^48] |
| **EvoSkills** (arXiv 2026) | Cross-model portable skill packages with co-evolutionary verification | [^26][^49] |

***

## Part IX: Open Research Gaps and Risk Flags

**Gap 1 — No end-to-end verified AI-to-AI artifact standard exists today.** MAIF, C2PA, and Atlas each address parts of the problem but have not been integrated into a single composable stack. The OVCA architecture proposed here is a synthesis, not a currently deployed system.[^9][^12][^3]

**Gap 2 — Token efficiency vs. provenance overhead trade-off.** Cryptographic metadata (hashes, signatures, manifests) consumes tokens. ObjectGraph's 60–95% compression provides budget headroom, but the provenance header must be carefully tuned to avoid consuming the savings. Compiled-AI amortization is the primary mitigation.[^2][^21]

**Gap 3 — MCP security surface.** A study of 67,057 MCP servers found widespread conditions enabling server hijacking and invocation manipulation. Any artifact pipeline using MCP as a transport must implement per-user scoped authorization and provenance tracking across agent workflows.[^50][^51]

**Gap 4 — Long-term poisoning via persistent memory.** MAIF's authors explicitly flag that persistent, non-ephemeral storage introduces short-term and long-term poisoning attack vectors. The artifact's accumulation layer must incorporate anomaly detection (MAIF's behavioral anomaly analysis feature) and periodic human re-validation cycles (XIL-ADR evolution stage).[^10][^39][^9]

**Gap 5 — Human cognitive overhead in H-AI-H loops.** Research on shared mental models finds humans are psychologically ill-equipped to evaluate AI accuracy without structured scaffolding. The Human Interface Layer (Layer 4) must be explicitly designed to support human calibration — not just display results — using XAI techniques surfacing the AI's internal reasoning at decision points.[^38]

**Gap 6 — TOON/TRON multi-turn stability.** Benchmarks show TOON cascades on multi-turn parsing failures and collapses parallel tool-call output for most models. For the iterative artifact loop, ObjectGraph or Markdown-KV are more robust choices than TOON for the delta layer.[^19][^18][^2]

***

## Conclusion

The research landscape in mid-2026 has produced all the necessary components for a cryptographically verifiable, token-efficient, co-evolving context artifact — but no single system yet integrates them. The optimal path forward is to **compose**: MAIF for the container format and semantic compression, C2PA for content provenance manifests, Atlas for ML pipeline lineage attestation, ObjectGraph for token-efficient knowledge encoding, SCP for human attribution, and AD4M/Holochain as the distributed trust substrate. The iterative prompting loop follows the NOVA generate-verify-accumulate architecture, with human guidance as the exploration expander and data-prompt co-evolution as the living-test-set quality gate. For the human-AI-human phase, the XIL-ADR cyclic refinement methodology, Shared Mental Model design (from augmentation-to-symbiosis research), and SCP access auditing together provide a rigorous and attribution-preserving bridge between human and machine participants.

---

## References

1. [Agentic AI Workload Characteristics - arXiv](https://arxiv.org/html/2605.26297v1) - Our study shows that agentic workloads are not simply long-prompt workloads: with effective context ...

2. [1 Introduction - arXiv](https://arxiv.org/html/2604.27820v1) - evaluate schema representation formats (YAML, Markdown, JSON, TOON) for file-native agentic systems....

3. [A Framework for Cryptographic Verifiability of End-to-End AI Pipelines](https://arxiv.org/html/2503.22573v1) - In this paper, we propose a framework for complete verifiable AI pipelines, identifying key componen...

4. [C2PA: Overview](https://spec.c2pa.org) - An open technical standard providing publishers, creators, and consumers the ability to trace the or...

5. [Adobe co-founds the Coalition for Content Provenance and ...](https://blog.adobe.com/en/publish/2021/02/22/adobe-continues-content-authenticity-commitment-founder-c2pa-standards-org) - With MSFT, Truepic, Arm, Intel and the BBC, Adobe founded the Coalition for Content Provenance and A...

6. [How we're increasing transparency for gen AI content with the C2PA](https://blog.google/innovation-and-ai/products/google-gen-ai-content-transparency-c2pa/) - The latest C2PA provenance technology aims to help people better understand how a particular piece o...

7. [Content Authenticity Initiative - Wikipedia](https://en.wikipedia.org/wiki/Content_Authenticity_Initiative)

8. [MAIF: Enforcing AI Trust and Provenance with an Artifact-Centric ...](https://arxiv.org/html/2511.15097v2) - We propose an artifact-centric AI agent paradigm where behavior is driven by persistent, verifiable ...

9. [MAIF: Multimodal Artifact File Format - Emergent Mind](https://www.emergentmind.com/topics/multimodal-artifact-file-format-maif) - MAIF is an AI-native file container that unifies text, images, audio, and sensor data with cryptogra...

10. [Vineeth Sai Narajala's Post - LinkedIn](https://www.linkedin.com/posts/vineethsai_maif-enforcing-ai-trust-and-provenance-with-activity-7399589888741814272-RnZ9) - MAIF (Multimodal Artifact File Format)—an AI-native container that turns data from passive storage i...

11. [MAIF: Enforcing AI Trust and Provenance with an Artifact-Centric ...](https://chatpaper.com/zh-CN/chatpaper/paper/211394) - The paper proposes the Multimodal Artifact File Format (MAIF), an artifact-centric AI agent paradigm...

12. [Atlas: A Framework for ML Lifecycle Provenance & Transparency](https://arxiv.org/html/2502.19567v1) - Atlas leverages open specifications for data and software supply chain provenance to collect verifia...

13. [A Framework for ML Lifecycle Provenance & Transparency](https://arxiv.org/abs/2502.19567) - The rapid adoption of open source machine learning (ML) datasets and models exposes today's AI appli...

14. [Verifiable Provenance and Watermarking for Generative AI - arXiv](https://arxiv.org/html/2605.21002v1) - This article presents a unified evidentiary framework that maps cryptographic content provenance, ro...

15. [[2602.11887] Verifiable Provenance of Software Artifacts with Zero ...](https://arxiv.org/abs/2602.11887) - We propose a novel approach to verifiable provenance based on compiling software with zero-knowledge...

16. [[Technical Cofounder] Cryptographic provenance layer for AI agents](https://www.reddit.com/r/cofounderhunt/comments/1sdkge6/technical_cofounder_cryptographic_provenance/) - Every agent action has a mathematically verifiable causal history. Compliance reports (SOC 2, HIPAA,...

17. [[PDF] ObjectGraph: From Document Injection to Knowledge Traversal - arXiv](https://arxiv.org/pdf/2604.27820.pdf) - task types demonstrating 60–95% token reduction without accuracy ... Reducing cost of. LLM agents wi...

18. [TOON Benchmarks - Improving Agents](https://www.improvingagents.com/blog/toon-benchmarks/) - Results from tests looking at how well LLMs understand Token-Oriented Object Notation (TOON) compare...

19. [A Benchmark Study of Token-Optimized Formats in Agentic AI Systems](https://arxiv.org/abs/2605.29676) - Large language models in Agentic AI systems consume tool schemas and execution results and emit tool...

20. [A Benchmark Study of Token-Optimized Formats in Agentic AI Systems](https://arxiv.org/html/2605.29676v1) - Across all implementations, JSON is the universal exchange format within Agentic AI. Current practic...

21. [Compiled AI: Deterministic Code Generation for LLM-Based ... - arXiv](https://arxiv.org/html/2604.05150v1) - We study compiled AI, a paradigm in which large language models generate executable code artifacts d...

22. [Cross-Lingual Token Arbitrage: Optimizing Code Agent Context ...](https://arxiv.org/html/2606.03618v1) - AI-assisted coding agents are bottlenecked by input-token cost. Two pathologies of raw human input d...

23. [Data-Prompt Co-Evolution: Growing Test Sets to Refine LLM Behavior](https://arxiv.org/html/2510.12728v3) - Interactive machine learning (IML) has long shown that humans and models can co-adapt through iterat...

24. [Data-Prompt Co-Evolution: Growing Test Sets to Refine LLM Behavior](https://arxiv.org/abs/2510.12728) - It guides application developers to discover edge cases, articulate rationales for desired behavior,...

25. [Data-Model Co-Evolution: Growing Test Sets to Refine LLM Behavior](https://www.catalyzex.com/paper/data-model-co-evolution-growing-test-sets-to) - A user study shows our workflow helps participants refine instructions systematically and specify am...

26. [EvoSkills: Self-Evolving Agent Skills via Co-Evolutionary Verification](https://arxiv.org/html/2604.01687v1) - Agents must orchestrate a coherent procedure across multiple steps and artifacts: decomposing goals,...

27. [NOVA: Fundamental Limits of Knowledge Discovery Through AI - arXiv](https://arxiv.org/html/2605.15219v2) - We introduce the NOVA framework, which models the common “generate, verify, accumulate, retrain” loo...

28. [Multi-Agent Evolve: LLM Self-Improve through Co-evolution - arXiv](https://arxiv.org/html/2510.23595v1) - Reinforcement Learning (RL) has demonstrated significant potential in enhancing the reasoning capabi...

29. [A Dual-Helix Co-Evolutionary Multi-Agent System for Prompt ... - arXiv](https://arxiv.org/html/2603.19732v1) - Abstract. Automated prompt optimization (APO) aims to improve large language model performance by re...

30. [A Knowledge-Enhanced Agent for Automatically Building AI Models](https://arxiv.org/html/2605.27873v1) - The knowledge system is initialized by crawling, deduplicating, and cleaning AI-development-related ...

31. [Sovereign Context Protocol: An Open Attribution Layer for Human ...](https://arxiv.org/abs/2603.27094) - SCP defines six core methods (creator profiles, semantic search, content retrieval, trust/value scor...

32. [New Protocol Aims to Make AI Models Pay Up for Using Your Content](https://www.machinebrief.com/news/new-protocol-aims-to-make-ai-models-pay-up-for-using-your-co-hz7f)

33. [ADAM - The substrate for collective intelligence - Coasys](https://coasys.org/adam) - Conceptually, AD4M Agents are modelled as something that can speak and that can listen. Agents commu...

34. [coasys/ad4m: Agent-centric social network and ... - GitHub](https://github.com/coasys/ad4m) - MCP Server (AI Agent Integration). AD4M includes a built-in MCP (Model Context Protocol) server that...

35. [hApps Spotlight: Flux - Holochain Blog](https://blog.holochain.org/happs-spotlight-flux/) - Flux is built on AD4M, which is an agent-centric framework for decentralized social applications. Th...

36. [Papers - Holochain](https://www.holochain.org/papers/) - We present a scalable, agent-centric distributed computing platform. We use a formalism to character...

37. [SCP: Accelerating Discovery with a Global Web of Autonomous ...](https://arxiv.org/abs/2512.24189) - We introduce SCP: the Science Context Protocol, an open-source standard designed to accelerate disco...

38. [From Augmentation to Symbiosis: A Review of Human-AI ... - arXiv](https://arxiv.org/html/2601.06030v1) - This paper offers a concise, 60-year synthesis of human-AI collaboration, from Licklider's “man-comp...

39. [Explanatory Interactive Machine Learning - PMC - PubMed - NIH](https://pubmed.ncbi.nlm.nih.gov/PMC10119840) - puts humans and machines into a loop which aims to remedy potential biases in an AI-based system and...

40. [HADA: Human-AI Agent Decision Alignment Architecture - arXiv](https://arxiv.org/html/2506.04253v1) - Artifact 3.6 closes the design loop by specifying how the logical roles enumerated in Artifact 3.2 a...

41. [Introducing Science Context Protocol (SCP) for AI Experimentation](https://www.linkedin.com/posts/eugeneeruslanov_scp-accelerating-discovery-with-a-global-activity-7415538095783239681-_6qf) - A new open standard called Science Context Protocol (SCP) lets AI agents plan, run, and repeat real ...

42. [Collective Intelligence](https://sqi.mit.edu/research/missions/collective-intelligence) - This Mission approaches how we can optimize human-AI group decision making. How can we create super-...

43. [Superclass Brain: Collective AI - Emergent Mind](https://www.emergentmind.com/topics/superclass-brain) - Superclass Brain is a meta-system that unifies human-LLM dyads into a collective intelligence capabl...

44. [Problem Solving Through Human-AI Preference-Based Cooperation](https://arxiv.org/html/2408.07461v4) - A novel framework for human-AI cooperative problem solving that builds on preference-based learning ...

45. [Incentivized Symbiosis: A Paradigm for Human-Agent Coevolution](https://arxiv.org/html/2412.06855v3) - ... loop is central to human-AI coevolution. They describe it as a cyclical process: users' choices ...

46. [The Workflow as Medium: A Framework for Navigating Human-AI Co ...](https://arxiv.org/html/2511.18182v1) - This paper introduces the Creative Intelligence Loop (CIL), a novel socio-technical framework for re...

47. [NeurIPS Poster A-Mem: Agentic Memory for LLM Agents](https://neurips.cc/virtual/2025/poster/119020) - Inspired by the Zettelkasten method, our system allows memories to actively generate their own conte...

48. [A-Mem: Agentic Memory for LLM Agents | OpenReview](https://openreview.net/forum?id=FiM0M8gcct) - Results showed A-Mem achieves comparable or superior performance to baselines while using only 33-50...

49. [Automated AI Skill Generation via Expert Knowledge Distillation - arXiv](https://arxiv.org/html/2605.31264v1) - We describe the artifact contract, generation workflow, correction lifecycle, deployment surface, an...

50. [[2511.20920] Securing the Model Context Protocol (MCP) - arXiv](https://arxiv.org/abs/2511.20920) - The aim is to help organizations ensure that unvetted code does not run outside a sandbox, tools are...

51. [A First Look at the Security Issues in the Model Context Protocol ...](https://arxiv.org/abs/2510.16558) - We analyze 67,057 servers across six public registries and identify widespread conditions enabling s...

