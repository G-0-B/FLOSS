# Recent Open Distributed Intelligence Research
*Compiled May 2026 | Focus: FLOSS, open-access, agent-centric, and privacy-preserving systems*

***

## Executive Summary

The distributed intelligence landscape has accelerated dramatically across 2024–2026, with convergent progress in four areas: agent-centric infrastructure (Holochain/AD4M), decentralized multi-agent LLM coordination (AgentNet, DAMCS, IoA), privacy-preserving federated learning (PrivateDFL, OpenMined PySyft), and open decentralized training infrastructure (Prime Intellect INTELLECT series). These threads are now beginning to weave together — with open protocols like MCP, A2A, and Cisco's AGNTCY emerging as spanning layers that could connect heterogeneous agents across organizations and networks. The overall movement represents a shift from data-centric, platform-locked AI toward **agent-centric, consent-scaled, collectively-owned intelligence commons**.

***

## Agent-Centric Distributed Architectures

### Holochain — Scaled Consent, Not Global Consensus

**Holochain: Distributed Coordination by Scaled Consent, not Global Consensus** (Eric Harris-Braun, Arthur Brock, Paul d'Aoust — v2.0, November 2024)[^1]

Relevance: A foundational technical revision of the Holochain whitepaper that replaces "consensus" as an organizing principle with "scaled consent" — a more expressive model for coordination among autonomous agents. Provides formal specification of integrity guarantees, functional components, and systemic analysis. The latest stable release is **Holochain 0.6.0** (November 2025), with a further release in January 2026. Essential reading for anyone building agent-centric dApps or evaluating Holochain as a trust substrate.[^2]

**Adjacent paper: Beyond Byzantium: The Players of Ludos** (Eric Harris-Braun, July 2024)[^1]

An informal companion introducing the rationale for scaled consent through an allegory — accessible entry point to the architectural philosophy behind Holochain's design choices.

### AD4M / ADAM Layer — Agent-Centric Spanning Layer

**AD4M: Agent-Centric Distributed Application Meta-Ontology** (Coasys — active development, docs updated 2025)[^3][^4][^5]

Relevance: AD4M is a spanning layer built on Holochain that defines three primitive classes — *Agents*, *Languages*, and *Perspectives* — enabling many-to-many mappings between interfaces and any technology: Holochain DNAs, IPFS, blockchains, federated APIs, and even centralized HTTP backends. AI agents join AD4M/ADAM spaces as first-class participants, sharing perspectives natively in the same P2P network as humans. ADAM Neighbourhoods can evolve into **Social Organisms** via embedded Social DNA code, enabling communities to define their own governance, data types, and interaction patterns without depending on a platform. This is directly aligned with the agent-centric intelligence commons model.[^4][^5]

**Distributed Agent-Centric System for Indigenous Data Sovereignty** (Setephano Noovao, University of Waikato, February 2025)[^6]

Relevance: A design science research study evaluating Holochain's feasibility for indigenous data sovereignty — demonstrates Holochain's practical applicability in high-stakes, consent-critical real-world data governance scenarios.

***

## Multi-Agent LLM Coordination

### AgentNet — Decentralized, Evolving DAG Coordination

**AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems** (Yingxuan Yang et al., Shanghai Jiao Tong University — arXiv:2504.00587, April 2025; NeurIPS 2025)[^7][^8]

Relevance: AgentNet proposes a fully decentralized, RAG-enhanced multi-agent framework where LLM agents specialize, evolve, and self-coordinate in a Directed Acyclic Graph (DAG) without any central orchestrator. Three key innovations: (1) fully decentralized coordination for fault tolerance and emergent intelligence; (2) dynamically evolving graph topology that adapts in real time to task demands; (3) retrieval-based agent memory for continual skill refinement. Official implementation open-sourced on GitHub (CC BY 4.0). **AgentNet outperforms both single-agent and centralized multi-agent baselines** in task accuracy.[^8][^7]

**AgentNet++: Hierarchical Decentralized Multi-Agent Coordination with Privacy-Preserving Knowledge Sharing** (Goutham Nalagatla — arXiv:2512.00614, November 2025)[^9][^10]

Relevance: Extends AgentNet with cluster-based hierarchies where agents self-organize into specialized groups, adding differential privacy and secure aggregation for knowledge sharing. Achieves **23% higher task completion rates** and **40% reduction in communication overhead** versus AgentNet, scaling to 1000+ agents.[^9]

### DAMCS — Decentralized Knowledge Graph Memory for Agents

**LLM-Powered Decentralized Generative Agents with Adaptive Hierarchical Knowledge Graph for Cooperative Planning (DAMCS)** (Hanqing Yang et al. — arXiv:2502.05453, February 2025)[^11][^12]

Relevance: Introduces DAMCS (*Decentralized Adaptive Knowledge Graph Memory and Structured Communication System*) — a multi-modal memory system organized as a hierarchical knowledge graph enabling decentralized multi-agent cooperation in open-world environments. Experiments show a two-agent scenario achieves the same goal with **63% fewer steps** and a six-agent scenario with **74% fewer steps** compared to single-agent baselines. Code and environments publicly released.[^12]

### Internet of Agents (IoA)

**Internet of Agents: Weaving a Web of Heterogeneous Agents for Collaborative Intelligence** (Weize Chen et al., Tsinghua/Tencent — ICLR 2025 Spotlight)[^13][^14]

Relevance: IoA proposes an internet-inspired architecture for connecting diverse LLM agents across environments — analogous to how TCP/IP connected heterogeneous networks. Features agent integration protocols, instant-messaging-like architecture, self-organizing team formation, and dynamic conversation flow. Consistently outperforms state-of-the-art baselines on general assistant, embodied AI, and RAG benchmarks. Open-access (CC BY 4.0).[^13]

### KARMA — Multi-Agent Knowledge Graph Enrichment

**KARMA: Leveraging Multi-Agent LLMs for Automated Knowledge Graph Enrichment** (Yuxing Lu, Jinzhuo Wang, Peking University — NeurIPS 2025 Spotlight)[^15][^16]

Relevance: KARMA employs nine collaborative agents — spanning entity discovery, relation extraction, schema alignment, and conflict resolution — to automatically enrich knowledge graphs from scientific literature. Directly relevant to distributed, open knowledge commons architectures where agent collectives can expand and maintain shared knowledge structures with verified accuracy.[^15]

### Multi-Agent Collaboration Mechanisms Survey

**Multi-Agent Collaboration Mechanisms: A Survey of LLMs** (Khanh-Tung Tran et al. — arXiv:2501.06322, January 2025)[^17]

Relevance: Comprehensive survey of LLM-based Multi-Agent Systems (MAS), characterizing collaboration mechanisms by actors, types (cooperation/competition/coopetition), structures (peer-to-peer, centralized, distributed), strategies, and coordination protocols. Introduces an extensible framework for guiding future research in decentralized multi-agent architectures.[^17]

### LLM-Powered Swarms

**LLM-Powered Swarms: A New Frontier or a Conceptual Stretch?** (M.A.U. Rahman et al., Lakeside Labs — arXiv, 2025)[^18]

Relevance: Critically evaluates whether LLM-powered swarm frameworks (like OpenAI Swarm) capture classical swarm intelligence principles — decentralization, simplicity, emergence, scalability. Implements LLM-based Boids and Ant Colony Optimization, finding that while LLM swarms emulate swarm-like dynamics, they face substantial computational overhead (~300× vs classical counterparts). Honest, open-access benchmark for the field.[^18]

**Bridging Swarm Intelligence and Reinforcement Learning** (Karthik Soma et al. — arXiv:2410.17517, October 2024; revised October 2025)[^19]

Relevance: Demonstrates theoretical and empirical equivalence between Collective Decision-Making (CDM) in swarm intelligence and single-agent reinforcement learning in multi-armed bandit problems. Introduces *Maynard-Cross Learning*, a novel abstract RL update rule bridging swarm and RL paradigms — enabling cross-disciplinary fertilization between the two fields.[^19]

***

## Decentralized Training and Open AI Infrastructure

### Prime Intellect — Globally Distributed RL Training

**INTELLECT-2: The First 32B Parameter Model Trained via Globally Distributed Reinforcement Learning** (Prime Intellect, April–May 2025)[^20][^21]

Relevance: INTELLECT-2 is the world's first 32B parameter model trained through fully asynchronous, permissionless distributed reinforcement learning, where anyone can contribute compute. Built on: **PRIME-RL** (open-source async RL framework for decentralized settings); **TOPLOC** (locality-sensitive hashing for trustless inference verification); **SHARDCAST** (tree-based HTTP weight distribution); and **SYNTHETIC-1/GENESYS** (crowdsourced RL task environments). A Rust-based orchestrator on testnet coordinates the global contributor pool — functionally analogous to a P2P protocol. All components open-sourced. Follow-up: **INTELLECT-3** (100B+ MoE, November 2025).[^21][^22][^23][^20]

**OpenCLAW-P2P: A Decentralized Framework for Collective AI Intelligence** (2026)[^24]

Relevance: Extends the OpenCLAW personal AI assistant platform to a global P2P collective intelligence network. Uses Kademlia DHT for peer discovery, epidemic gossip protocols for knowledge propagation, reputation-weighted task allocation, federated learning with differential privacy, and Byzantine Fault Tolerant (BFT) voting for consensus. Targets scientific research, medical applications, and AGI-oriented self-improvement governance.[^24]

**AntSeed: First Peer-to-Peer Rival to OpenRouter** (launched May 2026)[^25]

Relevance: A permissionless P2P marketplace for AI model access running on the same DHT protocol as BitTorrent — no central server, no listing approval, no platform intermediary. USDC payments settle peer-to-peer in providers' wallets on Base. Directly relevant to open, sovereign AI inference infrastructure.[^25]

***

## Privacy-Preserving Federated & Decentralized Learning

### PrivateDFL — Explainable Differential Privacy for Decentralized FL

**Privacy-Preserving Decentralized Federated Learning via Explainable Adaptive Differential Privacy (PrivateDFL)** (Fardin Jalil Piran et al. — arXiv:2509.10691, September 2025)[^26][^27]

Relevance: PrivateDFL combines HyperDimensional Computing (HDC) with a transparent differential privacy noise accountant, enabling each decentralized client to inject only the minimum incremental noise needed to satisfy its (ε, δ) budget rather than worst-case noise. Results: up to **24.4% higher accuracy** on MNIST, **>80% higher accuracy** on ISOLET, **76× lower inference latency**, and **36× less energy** vs. centralized Transformer baselines — all without a central server.[^26]

### FedAnil — Blockchain-Enabled Federated Deep Learning

**FedAnil: Decentralized and Robust Privacy-Preserving Model Using Blockchain-Enabled Federated Deep Learning** (Reza Fotohi et al. — arXiv:2502.17485, February 2025)[^28]

Relevance: Proposes a blockchain-anchored federated deep learning model addressing both non-IID data distribution skew and security/privacy attacks (poisoning and inference). Improves accuracy by more than 11–24% and reduces computation overhead by 8–15% vs. baseline approaches (ShieldFL, RVPFL, RFA). Published in *Applied Soft Computing* (2024).[^28]

### RAGRoute — Federated RAG Search

**Efficient Federated Search for Retrieval-Augmented Generation (RAGRoute)** (Rachid Guerraoui et al., EPFL — arXiv:2502.19280, February 2025)[^29]

Relevance: RAGRoute introduces federated RAG search — dynamically selecting relevant distributed data sources at query time using a lightweight neural classifier, rather than querying all sources. Reduces total queries by up to **77.5%** and communication volume by **76.2%**, making distributed knowledge retrieval economically practical for multi-node agent systems.[^29]

### P2PFL — Decentralized Federated Learning Library

**P2PFL: Federated Learning over P2P Networks** (open-source, GitHub)[^30]

Relevance: A general-purpose open-source library for decentralized federated learning using P2P networks and gossip protocols. Supports both simulated and real-environment deployment. Directly integratable with multi-agent systems requiring privacy-preserving collaborative model training without a central aggregator.[^30]

### OpenMined PySyft 0.9

**PySyft 0.9: Structured Transparency for Data Governance** (OpenMined, December 2024)[^31][^32]

Relevance: PySyft 0.9 evolves beyond federated learning into a comprehensive privacy-preserving data governance stack, introducing *Datasites* — websites for data — where scientists compute on non-public data without obtaining copies. OpenMined's mission explicitly frames this as unlocking **collective intelligence while preserving attribution-based control** across siloed data. Fully open-source, no vendor lock-in.[^32][^31]

***

## Distributed & Federated Vector Databases

| Project | License | Key Capability | Distributed? | Relevance |
|---------|---------|----------------|-------------|-----------|
| **Milvus** | Apache 2.0 | Billions of vectors, HNSW/IVF indexing, horizontal scaling | ✅ Yes (K8s, sharding) | Primary open-source distributed vector DB for large-scale agent memory[^33][^34] |
| **Weaviate** | BSD 3-Clause | Hybrid vector+keyword, GraphQL API, built-in ML modules | ✅ Clustered mode | Strong for semantic agent knowledge retrieval with structured filtering[^34] |
| **Qdrant** | Apache 2.0 | High-performance, Rust-native, filtering-aware HNSW | ✅ Distributed | Best community benchmark performance for large-scale use[^35] |
| **Chroma** | Apache 2.0 | Developer-first, Python-native, embedded or client-server | ⚠️ Limited | Best for local agent development and prototyping[^36] |

***

## Collective Intelligence Platforms & Knowledge Commons

### Collective Intelligence Project (CIP)

**Collective Intelligence Project + Weval Platform** (launched 2024)[^37]

Relevance: CIP runs AI-enabled deliberative processes engaging thousands of participants globally to define AI values through collectively-constructed "constitutions". Weval — analogous to Wikipedia for AI evaluation — empowers global communities to build qualitative benchmarks for any domain. Directly advances democratic, open governance of AI systems.[^37]

### MIT Supermind / Collective Intelligence Lab

**When Combinations of Humans and AI Are Useful: A Systematic Review and Meta-Analysis** (*Nature Human Behaviour*, October 2024)[^38]

**Supermind Ideator: How Scaffolding Human-AI Collaboration Can Increase Creativity** (*ACM Collective Intelligence Conference*, June 2024)[^38]

Relevance: MIT's Collective Intelligence Lab produces empirically-grounded research on human-AI group structures — defining benchmarks, modeling group configurations, and developing CAD tools for "group design." Directly relevant to engineering open, collective intelligence systems with optimal human-AI composition.

### AI & Human Co-Improvement for Safer Co-Superintelligence

**AI & Human Co-Improvement for Safer Co-Superintelligence** (Jason Weston, Jakob Foerster — arXiv:2512.05356, December 2025)[^39]

Relevance: Argues that targeting *co-superintelligence* — AI systems that improve in symbiosis with human researchers — is both more achievable and safer than unilateral AI self-improvement. Proposes focusing on AI's ability to collaborate with humans on AI research itself, from ideation to experimentation. A key conceptual framework for open, human-AI intelligence commons.[^39]

### Conversational Swarm Intelligence (CSI)

**Collective Superintelligence: Enabling Real-Time Conversational Deliberation** (InTechOpen, June 2025)[^40]

Relevance: CSI enables large human groups to engage in real-time deliberation and reach nuanced collective decisions — even across highly polarized groups — augmented by AI facilitation. Represents a practical implementation path for open, democratic collective superintelligence.

### II-Commons — Distributed Knowledge Base Toolkit

**II-Commons: Context-Aware Human-AI Partnership** (Intelligent Internet, May–July 2025)[^41]

Relevance: II-Commons (II-Knowledge) builds shared, layered knowledge infrastructure with procedural, cognitive, chronological, and scientific context. Wave 2 expanded to include experimental applications and scientific datasets, positioning it as a backbone for human-AI knowledge commons rather than purely a code library.[^41]

***

## Emerging Protocols and Infrastructure for Agent Interoperability

The convergence of distributed intelligence increasingly runs through **open agent protocols** that serve as spanning layers across heterogeneous systems:[^42]

- **Model Context Protocol (MCP)** — Anthropic's open standard enabling agents to securely interact with any tool, content system, or API using a client-server architecture; now foundational to MIT's NANDA decentralized agent initiative[^42]
- **Agent-to-Agent (A2A)** — Google's cross-vendor agent collaboration protocol based on HTTP, SSE, and JSON-RPC; enables heterogeneous agents to coordinate at web scale[^42]
- **AGNTCY / Agent Connect Protocol (ACP)** — Cisco's open agent-native internet infrastructure, including the Open Agent Schema Framework (OASF) for agent interoperability[^42]
- **MIT NANDA** — A rules-based operating system for decentralized agents with cryptographic accountability, identity management, and agent registries, built atop MCP[^42]

***

## Summary Matrix

| Category | Key Projects/Papers | Year | License/Access |
|----------|-------------------|------|---------------|
| Agent-centric substrate | Holochain (v2.0 whitepaper), AD4M/ADAM | 2024–2025 | GPLv3 / MIT |
| Decentralized MAS | AgentNet (NeurIPS'25), AgentNet++, DAMCS, IoA (ICLR'25) | 2025 | CC BY 4.0 / Apache |
| Distributed RL training | INTELLECT-2/3, PRIME-RL, OpenCLAW-P2P | 2025–2026 | Open-source |
| Privacy-preserving FL | PrivateDFL, FedAnil, P2PFL, PySyft 0.9 | 2024–2025 | Open-source |
| Federated RAG | RAGRoute (EPFL), KARMA (NeurIPS'25) | 2025 | CC BY / Open |
| Distributed vector DBs | Milvus, Weaviate, Qdrant | 2024–2026 | Apache 2.0 / BSD |
| Collective intelligence | CIP/Weval, MIT Supermind, CSI, II-Commons | 2024–2025 | Open / Community |
| Agent interoperability | MCP, A2A, AGNTCY/ACP, MIT NANDA | 2024–2025 | Open standards |
| Swarm ↔ RL theory | Bridging Swarm Intelligence & RL, LLM-Swarms | 2024–2025 | arXiv open access |
| Human-AI co-intelligence | Co-Superintelligence (arXiv:2512.05356) | 2025 | arXiv open access |

---

## References

1. [Papers - Holochain](https://www.holochain.org/papers/) - We present a scalable, agent-centric distributed computing platform. We use a formalism to character...

2. [Holochain | Distributed app framework with P2P networking](https://www.holochain.org) - Holochain delivers beyond the promises of blockchain by providing a lightweight, secure and versatil...

3. [Introduction | AD4M Docs](https://docs.ad4m.dev) - Documentation site for AD4M

4. [ADAM - The substrate for collective intelligence - Coasys](https://coasys.org/adam) - Agent-centric. Peer-to-peer. Built on Holochain. Where AI agents and humans share perspectives — not...

5. [coasys/ad4m: Agent-centric social network and ... - GitHub](https://github.com/coasys/ad4m) - AD4M is a spanning layer that extends the internet stack to enable true collective intelligence in a...

6. [Distributed agent-centric system for indigenous data sovereignty](https://researchcommons.waikato.ac.nz/entities/publication/421503a8-0aea-45a6-bb93-286355e6a8e0) - The purpose of this thesis is to critically evaluate the feasibility of using holochain technology t...

7. [GitHub - zoe-yyx/AgentNet: [NIPS2025] A decentralized, RAG ...](https://github.com/zoe-yyx/AgentNet) - This is the official implementation of the paper "AgentNet: Decentralized Evolutionary Coordination ...

8. [AgentNet: Decentralized Evolutionary Coordination for LLM-based ...](https://arxiv.org/abs/2504.00587) - Abstract page for arXiv paper 2504.00587: AgentNet: Decentralized Evolutionary Coordination for LLM-...

9. [[2512.00614] Hierarchical Decentralized Multi-Agent Coordination ...](https://arxiv.org/abs/2512.00614) - Abstract:Decentralized multi-agent systems have shown promise in enabling autonomous collaboration a...

10. [Extending AgentNet for Scalable Autonomous Systems - arXiv](https://arxiv.org/html/2512.00614v1) - AgentNet: Decentralized Evolutionary Coordination for LLM-Based Multi-Agent Systems. Advances in Neu...

11. [DAMCS - Hanqing Yang](https://happyeureka.github.io/damcs/) - DAMCS introduces a multi-modal memory system organized as a hierarchical knowledge graph and a struc...

12. [LLM-Powered Decentralized Generative Agents with Adaptive ...](https://arxiv.org/abs/2502.05453) - We propose Decentralized Adaptive Knowledge Graph Memory and Structured Communication System (DAMCS)...

13. [Internet of Agents: Weaving a Web of Heterogeneous Agents for...](https://openreview.net/forum?id=o1Et3MogPw) - We propose IoA, a novel framework inspired by the Internet for effective collaboration among diverse...

14. [Internet of Agents (IoA): A Novel Artificial Intelligence AI Framework ...](https://www.reddit.com/r/machinelearningnews/comments/1e1b9dq/internet_of_agents_ioa_a_novel_artificial/) - Internet-Inspired Architecture: Just like how the internet connects people, IoA can connect differen...

15. [KARMA: Leveraging Multi-Agent LLMs for Automated Knowledge ...](https://openreview.net/forum?id=k0wyi4cOGy) - This paper presents KARMA, a modular framework leveraging multi-agent large language models (LLMs) f...

16. [KARMA: Leveraging Multi-Agent LLMs for Automated ... - arXiv](https://arxiv.org/html/2502.06472v1) - This paper presents KARMA, a novel framework employing multi-agent large language models (LLMs) to a...

17. [Multi-Agent Collaboration Mechanisms: A Survey of LLMs - arXiv](https://arxiv.org/abs/2501.06322) - This work provides an extensive survey of the collaborative aspect of MASs and introduces an extensi...

18. [LLM-Powered Swarms: A New Frontier or a Conceptual ...](https://arxiv.org/html/2506.14496v2)

19. [Bridging Swarm Intelligence and Reinforcement Learning - arXiv](https://www.arxiv.org/abs/2410.17517v1) - Swarm intelligence (SI) explores how large groups of simple individuals (e.g., insects, fish, birds)...

20. [Today we are launching INTELLECT-2. The first 32B parameter decentralized… | Prime Intellect](https://www.linkedin.com/posts/primeintellect-ai_today-we-are-launching-intellect-2-the-activity-7318032913948635137-P07E) - Today we are launching INTELLECT-2. The first 32B parameter decentralized reinforced learning traini...

21. [Prime Intellect Releases INTELLECT-2: a 32B Parameter Model ...](https://www.infoq.com/news/2025/05/prime-intellect-2/) - Prime Intellect has released INTELLECT-2, a 32 billion parameter language model trained using fully ...

22. [PrimeIntellect-ai/prime-rl: Async RL Training at Scale](https://github.com/PrimeIntellect-ai/prime-rl) - Async RL Training at Scale. Contribute to PrimeIntellect-ai/prime-rl development by creating an acco...

23. [Blog](https://www.primeintellect.ai/blog) - The compute and infrastructure platform for you to train, evaluate, and deploy your own agentic mode...

24. [OpenCLAW-P2P: A Decentralized Framework for Collective AI ...](https://www.academia.edu/164666471/OpenCLAW_P2P_A_Decentralized_Framework_for_Collective_AI_Intelligence_Towards_Artificial_General_Intelligence) - We present OpenCLAW-P2P, a decentralized peer-to-peer framework that enables autonomous AI agents to...

25. [AntSeed Opens First Peer-to-Peer Rival to OpenRouter](https://markets.businessinsider.com/news/currencies/antseed-opens-first-peer-to-peer-rival-to-openrouter-1036163585) - Gibraltar, Gibraltar, May 15th, 2026, ChainwirePayments settle directly in providers' wallets with n...

26. [Privacy-Preserving Decentralized Federated Learning via ...](https://arxiv.org/abs/2509.10691) - Decentralized Federated Learning (DFL) enables collaborative model training without a central server...

27. [Privacy-Preserving Decentralized Federated Learning via Explainable Adaptive Differential Privacy](https://www.arxiv.org/abs/2509.10691) - Decentralized federated learning faces privacy risks because model updates can leak data through inf...

28. [Decentralized and Robust Privacy-Preserving Model Using Blockchain-Enabled Federated Deep Learning in Intelligent Enterprises](https://www.arxiv.org/abs/2502.17485) - In Federated Deep Learning (FDL), multiple local enterprises are allowed to train a model jointly. T...

29. [Efficient Federated Search for Retrieval-Augmented Generation - arXiv](https://arxiv.org/html/2502.19280v1) - We introduce RAGRoute, a novel mechanism for federated RAG search. RAGRoute dynamically selects rele...

30. [P2PFL is a decentralized federated learning library that ...](https://github.com/p2pfl/p2pfl) - P2PFL is a decentralized federated learning library that enables federated learning on peer-to-peer ...

31. [OpenMined The Missing Layer for Collective Intelligence](https://openmined.org) - We're OpenMined, a non-profit community building technology that enables secure computation across s...

32. [When data sharing is a Problem, PySyft 0.9 is the Solution](https://openmined.org/blog/announcing-pysyft-09/) - PySyft 0.9 is an open source stack of tools that provides a comprehensive solution for data privacy ...

33. [The High-Performance Vector Database Built for Scale](https://milvus.io) - Milvus is an open-source vector database built for GenAI applications. Install with pip, perform hig...

34. [Choosing between Pinecone, Weaviate, Milvus, and other vector ...](https://milvus.io/ai-quick-reference/how-do-i-choose-between-pinecone-weaviate-milvus-and-other-vector-databases) - Milvus is designed for high scalability, supporting distributed deployments to handle billions of ve...

35. [What is the best vector database? : r/vectordatabase - Reddit](https://www.reddit.com/r/vectordatabase/comments/1d4kz2p/what_is_the_best_vector_database/) - When choosing a vector db, what are the key factors you consider? Is it performance, ease of use, sc...

36. [Best Vector Databases 2026: Pinecone, Chroma, Qdrant & More](https://www.datacamp.com/blog/the-top-5-vector-databases) - Discover the top vector databases for AI in 2026. Compare features and use cases for Pinecone, Chrom...

37. [The Collective Intelligence Project](https://www.cip.org) - We've launched an open, collaborative platform to build evaluations that test what matters to you. W...

38. [Collective Intelligence | The MIT Siegel Family Quest for Intelligence](https://sqi.mit.edu/research/missions/collective-intelligence) - Proceedings of the ACM Collective Intelligence Conference. 2024/06/27. Supermind Ideator: How Scaffo...

39. [AI & Human Co-Improvement for Safer Co-Superintelligence](https://www.arxiv.org/abs/2512.05356) - Self-improvement is a goal currently exciting the field of AI, but is fraught with danger, and may t...

40. [Collective Superintelligence: Enabling Real-Time Conversational ...](https://www.intechopen.com/chapters/1223362) - This chapter explores the pursuit of Collective Superintelligence using a novel technology called Co...

41. [II-Commons - Intelligent Internet](https://ii.inc/web/blog/post/ii-commons) - II-Commons, and its core component II-Knowledge, aim to enhance personal and organizational knowledg...

42. [Building a Global Ecosystem of the Decentralized Internet of AI ...](https://www.linkedin.com/pulse/building-global-ecosystem-decentralized-internet-ai-i-alex-g--zkhfe) - China's Tsinghua University introduced AgentVerse, an open-source platform enabling multi-agent coll...

