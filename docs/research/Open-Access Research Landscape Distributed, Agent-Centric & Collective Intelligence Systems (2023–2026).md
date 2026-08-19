# Open-Access Research Landscape: Distributed, Agent-Centric & Collective Intelligence Systems (2023–2026)

*Compiled April 14, 2026 | Focus: Open-access, FOSS-licensed, privacy-preserving, decentralized AI and knowledge systems*

***

## Executive Summary

The 2023–2026 period has produced a remarkable convergence of research across agent-centric architectures, decentralized AI networks, federated knowledge systems, and collective intelligence frameworks. What was once a niche intersection of peer-to-peer computing and machine learning is now a high-velocity research frontier, with dozens of open-access papers published per month across arXiv, MDPI, PubMed Central, and Semantic Scholar. This report curates the most significant papers, projects, and open-source initiatives organized by thematic domain, prioritizing work that advances openness, sovereignty, privacy, and distributed reasoning — the pillars of composable, multi-substrate intelligence commons.

***

## 1. Agent-Centric Architectures & Peer-to-Peer Networking

### 1.1 Holochain: Agent-Centric Distributed Framework

**Project: Holochain (holochain.org) | Open-source, Apache 2.0 | Ongoing**

Holochain is a post-blockchain, agent-centric framework in which each user maintains their own sovereign source chain and shares data only when necessary via a Distributed Hash Table (DHT). Rather than relying on a global consensus ledger, Holochain's architecture eliminates the need for mining, staking, or energy-intensive consensus protocols — each participant follows shared validation rules backed by cryptographic proofs. In 2025, the Holochain team integrated **Kitsune2**, a fundamental rethink of peer discovery and DHT synchronization that reduced sync times from 30+ minutes to under a minute in most cases, alongside a new **warrants** system that blocks bad actors at the transport level — completing what the team calls "the immune system" of the network.[^1][^2]

An independent analysis of 140+ Holochain repositories (2025) concluded that the ecosystem demonstrates "technical excellence, honest communication, and professional development standards that exceed typical emerging technology projects," with a realistic production timeline of 1–2 years.[^3]

***

### 1.2 AD4M: Agent-Centric Distributed Application Meta-Ontology

**Project: AD4M / ADAM Layer (coasys.org, GitHub: coasys/ad4m) | Open-source, AGPL | Active**

AD4M (Agent-Centric Distributed Application Meta-ontology) is a spanning layer that extends the internet stack to enable true collective intelligence in a fully distributed way. Just as TCP/IP created a universal protocol for machine-to-machine communication, AD4M creates a universal protocol for agents — humans and their devices — to make meaning together. Its architecture rests on three core concepts: **Agents** (identified by Decentralized Identifiers/DIDs), **Languages** (pluggable protocol adapters wrapping Holochain, IPFS, blockchains, HTTP), and **Perspectives** (private, locally stored graph databases linking data across protocols).[^4][^5]

The ADAM Layer's spanning capability is particularly powerful for AI: it enables semantic understanding via RDF-like links, protocol agnosticism so agents don't need to learn every API, cryptographic provenance where every action is signed and auditable, and distributed intelligence where agents can join *Neighbourhoods* and collaborate P2P without central servers. AI agents join ADAM spaces as first-class participants, sharing perspectives, contributing knowledge, and collaborating with humans in real-time — natively, in the same P2P network, not through APIs.[^6][^7]

***

### 1.3 PlanetServe: Decentralized LLM Serving Overlay

| Field | Detail |
|---|---|
| **Title** | PlanetServe: A Decentralized, Scalable, and Privacy-Preserving Overlay for Democratizing Large Language Model Serving |
| **Authors** | Fei Fang, Yifan Hua, Shengze Wang, Ruilin Zhou, Yi Liu, Chen Qian, Xiaoxue Zhang |
| **Year** | 2025 |
| **Source** | arXiv:2504.20101 |
| **License** | Open access |

Inspired by peer-to-peer networks, PlanetServe proposes a decentralized overlay harnesses computing resources from distributed contributors to serve LLMs. The system addresses four key research problems: overlay network organization, LLM communication privacy, overlay forwarding for resource efficiency, and verification of serving quality. Evaluation on a prototype showed over 50% latency reduction versus a non-overlay baseline, while leveraging NVIDIA Confidential Computing on Hopper/Blackwell GPUs to run inference inside Trusted Execution Environments (TEEs).[^8][^9]

***

### 1.4 Honeybee: Byzantine-Tolerant Decentralized Peer Sampling

| Field | Detail |
|---|---|
| **Title** | Honeybee: Byzantine Tolerant Decentralized Peer Sampling with Verifiable Random Walks |
| **Year** | 2024 (revised 2025) |
| **Source** | arXiv:2402.16201 |
| **License** | Open access |

Honeybee identifies uniform random sampling of nodes as a fundamental capability for building robust P2P networks at scale (hundreds of thousands of nodes), particularly in support of sharding, data availability sampling, and layer-2 scaling methods. The framework provides decentralized, Byzantine-tolerant peer sampling with cryptographic verification, a foundational primitive for any agent-centric network with adversarial participants.[^10]

***

## 2. Collective Intelligence Systems & Tools

### 2.1 AI-Enhanced Collective Intelligence

| Field | Detail |
|---|---|
| **Title** | AI-Enhanced Collective Intelligence |
| **Authors** | Taha Yasseri et al. |
| **Year** | 2024 |
| **Source** | PMC / PubMed (PMC11573907) |
| **License** | Open access |

This peer-reviewed paper proposes a multilayer representation of collective intelligence systems drawn from complexity science and network science. It examines factors influencing the emergence of collective intelligence and various AI modes of contribution — from assistive to fully autonomous — and discusses real-world applications across societal challenges that exceed the capacity of humans or AI in isolation. The paper is a key theoretical foundation for designing human-AI collectives.[^11]

***

### 2.2 Artificial Collective Intelligence Engineering: A Survey

| Field | Detail |
|---|---|
| **Title** | Artificial Collective Intelligence Engineering: A Survey of Concepts and Perspectives |
| **Year** | 2023 |
| **Source** | arXiv:2304.05147 |
| **License** | Open access |

This survey covers the long arc of collective intelligence design in engineered systems, covering Internet of Things, swarm robotics, and crowd computing. It provides a conceptual map for how not-so-intelligent individuals, through distributed interaction, can produce effects that surpass the capabilities of the smartest single agent — directly applicable to designing open AI collectives.[^12]

***

### 2.3 Evolving AI Collectives to Enhance Human Diversity

| Field | Detail |
|---|---|
| **Title** | Evolving AI Collectives to Enhance Human Diversity and Enable Self-Regulation |
| **Year** | 2024 |
| **Source** | arXiv:2402.12590 |
| **License** | Open access |

This paper proposes "societies" of interacting AI models that evolve their outputs to increase rewards and reduce risks to human society. Using a small community of models and their evolving outputs, the authors illustrate how decentralized AI collectives can spontaneously expand the bounds of human diversity and reduce the risk of anti-social behavior, while discussing opportunities for AI cross-moderation.[^13]

***

### 2.4 Towards a Science of Collective AI

| Field | Detail |
|---|---|
| **Title** | Towards a Science of Collective AI: LLM-based Multi-Agent Systems Need a Transition from Blind Trial-and-Error to Rigorous Science |
| **Year** | 2026 |
| **Source** | arXiv:2602.05289 |
| **License** | Open access |

Published in February 2026, this position paper argues that the field of LLM-based multi-agent systems must move from ad hoc experimentation to rigorous, reproducible science. It identifies the need for principled evaluation frameworks for collective AI behavior, making it directly relevant to anyone building agent collectives on distributed substrates.[^14]

***

### 2.5 Emergent Collective Intelligence from Massive-Agent Cooperation

| Field | Detail |
|---|---|
| **Title** | Emergent Collective Intelligence from Massive-Agent Cooperation and Competition |
| **Year** | 2023 |
| **Source** | arXiv:2301.01609 |
| **License** | Open access |

Inspired by organisms evolving through cooperation and competition, this paper studies the emergence of artificial collective intelligence through massive-agent reinforcement learning, introducing a novel environment (Lux) where dynamic agents in two teams compete for limited resources. It provides foundational empirical evidence for how intelligence can emerge from distributed, competitive interaction rather than top-down design.[^15]

***

## 3. Multi-Agent & Multi-Modal AI Frameworks

### 3.1 SwarmSys: Decentralized Swarm-Inspired Agents

| Field | Detail |
|---|---|
| **Title** | SwarmSys: Decentralized Swarm-Inspired Agents for Scalable and Adaptive Reasoning |
| **Authors** | Ruohao Li, Hongjun Liu et al. |
| **Year** | 2025 |
| **Source** | arXiv:2510.10047 |
| **License** | Open access |

SwarmSys is a closed-loop framework for distributed multi-agent reasoning inspired by swarm intelligence, where coordination emerges through iterative interactions among three specialized roles — Explorers, Workers, and Validators — that continuously cycle through exploration, exploitation, and validation without global supervision. It integrates adaptive agent profiles, embedding-based probabilistic matching, and a pheromone-inspired reinforcement mechanism, suggesting that "coordination scaling may rival model scaling in advancing LLM intelligence".[^16]

***

### 3.2 SAGE: Multi-Agent Self-Evolution for LLM Reasoning

| Field | Detail |
|---|---|
| **Title** | SAGE: Self-Evolving Agents for Generalized Reasoning Evolution |
| **Year** | 2026 |
| **Source** | arXiv:2603.15255 |
| **License** | Open access |

SAGE instantiates four specialized agents — Challenger, Planner, Solver, and Critic — that co-evolve through adversarial yet collaborative dynamics. Starting from minimal seed examples, SAGE autonomously expands its training curriculum while maintaining quality via critic-based filtering, achieving strong out-of-distribution generalization on competition-level benchmarks and representing a scalable pathway for evolving capable reasoning agents while reducing dependency on human-curated supervision.[^17]

***

### 3.3 MarsRL: Multi-Agent Reasoning via Reinforcement Learning

| Field | Detail |
|---|---|
| **Title** | MarsRL: Advancing Multi-Agent Reasoning System via Reinforcement Learning with Agentic Pipeline Parallelism |
| **Authors** | Shulin Liu, Dong Du, Tao Yang et al. (Tencent Hunyuan Team) |
| **Year** | 2025 |
| **Source** | arXiv:2511.11373 |
| **License** | Open access |

MarsRL proposes a reinforcement learning framework with agentic pipeline parallelism designed to jointly optimize all agents (Solver, Verifier, Corrector) in a multi-agent reasoning system. It improves AIME2025 accuracy from 86.5% to 93.3% when applied to Qwen3-30B-A3B-Thinking-2507, addressing the generalization gap that prevents open-source models from leveraging multi-agent reasoning as effectively as closed-source ones.[^18]

***

### 3.4 AgentNet: Decentralized Evolutionary Coordination

| Field | Detail |
|---|---|
| **Title** | AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems |
| **Year** | 2025 |
| **Source** | arXiv:2504.00587 |
| **License** | Open access |

AgentNet directly addresses the limitations of centralized orchestration (bottlenecks, single points of failure, siloed expertise) by proposing a decentralized, evolutionary approach to multi-agent coordination. Privacy concerns and proprietary knowledge sharing barriers are explicitly cited as problems the architecture overcomes, making it relevant for cross-organizational, open-access collective intelligence deployments.[^19]

***

### 3.5 Dealog: Decentralized Multi-Agents Log-Mediated Reasoning

| Field | Detail |
|---|---|
| **Title** | Dealog: Decentralized Multi-Agents Log-Mediated Reasoning Framework |
| **Authors** | Abhijit Chakraborty, Ashish Raj Shekhar et al. (Arizona State University) |
| **Year** | 2026 |
| **Source** | arXiv:2602.00996 |
| **License** | Open access |

Dealog introduces a decentralized multi-agent framework for multimodal question answering using specialized agents for Table, Context, and Visual modalities, coordinated through log-mediated communication rather than centralized orchestration. This is a notable contribution at the intersection of decentralization and multi-modal AI reasoning.[^20]

***

### 3.6 LLM-Powered Swarms: A Critical Evaluation

| Field | Detail |
|---|---|
| **Title** | LLM-Powered Swarms: A New Frontier or a Conceptual Stretch? |
| **Authors** | Muhammad Atta Ur Rahman, Melanie Schranz, Samira Hayat (Lakeside Labs) |
| **Year** | 2025 |
| **Source** | arXiv:2506.14496 |
| **License** | Open access |

This important critical counterpoint evaluates whether LLM-based swarm systems actually capture the fundamental principles of classical swarm intelligence — decentralization, simplicity, emergence, and scalability. Results show LLM-powered swarms can emulate swarm-like dynamics but are constrained by substantial computational overhead (roughly 300× more computation than classical counterparts), highlighting current limitations that must be overcome for practical deployment.[^21]

***

### 3.7 LLM-Agent-UMF: Unified Agent Modeling Framework

| Field | Detail |
|---|---|
| **Title** | LLM-Agent-UMF: LLM-based Agent Unified Modeling Framework for Seamless Design of Multi Active/Passive Core-Agent Architectures |
| **Authors** | Amine Ben Hassouna, Hana Chaari, Ines Belhaj |
| **Year** | 2024 (revised 2025) |
| **Source** | arXiv:2409.11393 |
| **License** | Open access |

LLM-Agent-UMF establishes a clear foundation for agent development from both functional and software architectural perspectives, introducing a *core-agent* coordinator comprising five modules: planning, memory, profile, action, and security. It addresses terminological inconsistencies across the field by proposing unified vocabulary, and explicitly calls out security — "often neglected in previous works" — as a first-class module.[^22]

***

### 3.8 The Orchestration of Multi-Agent Systems

| Field | Detail |
|---|---|
| **Title** | The Orchestration of Multi-Agent Systems: Architectures, Protocols... |
| **Year** | 2026 |
| **Source** | arXiv:2601.13671 |
| **License** | Open access |

This comprehensive survey published in January 2026 identifies four technical drivers for the pivot to multi-agent architectures: scalability limits of LLMs (context length, reasoning bottlenecks), specialization needs (modular agents optimized for domains), advances in communication protocols, and economic efficiency (distributed collectives of smaller agents often outperforming costly all-purpose deployments).[^23]

***

## 4. Distributed & Federated Vector Databases

### 4.1 Distributed Vector Databases on HPC Platforms

| Field | Detail |
|---|---|
| **Title** | Exploring Distributed Vector Databases Performance on HPC Platforms: A Study with Qdrant |
| **Authors** | Seth Ockerman, Amal Gueroudji, Song Young Oh et al. (Argonne / UChicago / UW-Madison) |
| **Year** | 2025 |
| **Source** | arXiv:2509.12384 |
| **License** | Open access |

This empirical study presents distributed vector database performance on the Polaris supercomputer (Argonne Leadership Computing Facility), constructing a realistic biological-text workload and evaluating Qdrant with up to 32 workers across insertion, index construction, and query latency tasks. It is the first systematic study of vector database performance in large-scale scientific HPC contexts, directly informing distributed knowledge base design for open science.[^24]

***

### 4.2 RAGRoute: Efficient Federated Search for RAG

| Field | Detail |
|---|---|
| **Title** | Efficient Federated Search for Retrieval-Augmented Generation |
| **Authors** | Rachid Guerraoui, Anne-Marie Kermarrec, Diana Petrescu et al. (EPFL) |
| **Year** | 2025 |
| **Source** | arXiv:2502.19280 |
| **License** | Open access |

RAGRoute introduces a federated RAG search mechanism that dynamically selects relevant data sources at query time using a lightweight neural network classifier, rather than querying every data source. The approach reduces total queries by up to 77.5% and communication volume by up to 76.2% on MIRAGE and MMLU benchmarks — a major efficiency gain for distributed knowledge retrieval across heterogeneous repositories.[^25]

***

### 4.3 FedVSE: Privacy-Preserving Federated Vector Search Engine

| Field | Detail |
|---|---|
| **Title** | FedVSE: A Privacy-Preserving and Efficient Vector Search Engine |
| **Year** | 2025 |
| **Source** | VLDB 2025 |
| **License** | Open access (proceedings) |

FedVSE proposes a federated vector search engine with a dual-indexing scheme (built-in vector indexes + learned indexes for structured attributes) and leverages Intel SGX Trusted Execution Environments at the central coordination layer to ensure privacy across federated databases of mutually untrusted providers. This is a key reference for privacy-preserving distributed retrieval in multi-stakeholder environments.[^26]

***

### 4.4 FedVS: Federated Vector Similarity Search with Filters

| Field | Detail |
|---|---|
| **Title** | FedVS: Towards Federated Vector Similarity Search with Filters |
| **Year** | 2025 |
| **Source** | KDD 2025 / ACM Digital Library |
| **License** | Open access |

FedVS addresses federated top-k nearest neighbor search across vectors from mutually untrusted providers, using TEE-based secure operations and HNSW indexes to balance recall, latency, and communication cost. It handles attribute-filtered similarity search — a practical requirement in real-world federated deployments where not all vectors are relevant to every query.[^27][^28]

***

### 4.5 HyFedRAG: Federated Multi-Modal RAG for Healthcare

| Field | Detail |
|---|---|
| **Title** | HyFedRAG: A Federated Retrieval-Augmented Generation Framework |
| **Year** | 2025 |
| **Source** | arXiv:2509.06444 |
| **License** | Open access |

HyFedRAG addresses centralized RAG pipeline limitations for heterogeneous, privacy-sensitive healthcare data, implementing a federated workflow using the Flower framework with separate storage for unstructured text (FAISS vector DB), structured data (SQL), and knowledge graphs (Neo4j). This multi-modal, privacy-first architecture is directly applicable to distributed knowledge commons in sensitive domains.[^29]

***

### 4.6 HMGI: Hybrid Multimodal Graph Index

| Field | Detail |
|---|---|
| **Title** | The Hybrid Multimodal Graph Index (HMGI): A Comprehensive Framework for Integrated Relational and Vector Search |
| **Authors** | Joydeep Chandra, Satyam Kumar Navneet, Yong Zhang (Tsinghua University) |
| **Year** | 2025 |
| **Source** | arXiv:2510.10123 |
| **License** | Open access |

HMGI bridges the gap between vector databases (strong on semantic similarity) and graph databases (strong on relational traversal) by creating a unified system for hybrid queries on multimodal data. By integrating Approximate Nearest Neighbor Search with native graph architecture (exemplified by Neo4j), HMGI enables queries that combine semantic proximity and structural relationship — a critical capability for complex distributed knowledge graphs.[^30]

***

### 4.7 Governance-Aware Vector Subscriptions

| Field | Detail |
|---|---|
| **Title** | Governance-Aware Vector Subscriptions for Multi-Agent Knowledge Ecosystems |
| **Year** | 2026 |
| **Source** | arXiv:2603.20833 |
| **License** | Open access; implementation AGPL-3.0 |

This March 2026 paper introduces a mechanism composing semantic publish-subscribe with multi-dimensional policy predicates grounded in regulatory frameworks (EU DSM Directive, EU AI Act). Agents subscribe to semantic regions of a curated knowledge base (AIngram); notifications dispatch only for validated content that passes both similarity thresholds and all applicable policy constraints across dimensions including jurisdiction, training opt-out, and scientific usage. The implementation is open-source under AGPL-3.0, making it directly deployable in governance-first collective intelligence systems.[^31][^32]

***

### 4.8 Open-Source Vector Databases: Current Landscape

As of 2026, the leading open-source vector databases for multimodal, distributed deployments are:

| Database | License | Key Strength | Multimodal Support |
|---|---|---|---|
| **Milvus** | Apache 2.0 | Scale (43K+ GitHub stars), Kubernetes-native[^33] | Multi-vector hybrid search[^34] |
| **Weaviate** | BSD 3-Clause | Cloud-native, flexible deployment[^35] | Multi-target vector search[^34] |
| **Qdrant** | Apache 2.0 | Developer-friendly, strong API[^35] | Hybrid dense+sparse scoring |
| **LanceDB** | Apache 2.0 | Embedded, versioned storage[^34] | Multimodal + metadata in same table |
| **pgvector** | PostgreSQL | ACID compliance, SQL integration[^34] | Dense vector + SQL joins |

By 2026, projections indicate over 30% of enterprises will integrate vector databases to support foundation models — up from less than 2% in 2023.[^36]

***

## 5. Distributed Networking Protocols & Infrastructure

### 5.1 AGNTCY Agent Directory Service (ADS)

| Field | Detail |
|---|---|
| **Title** | The AGNTCY Agent Directory Service: Architecture and Implementation |
| **Authors** | Luca Muscariello, Vijoy Pandey, Ramiz Polic et al. |
| **Year** | 2025 |
| **Source** | arXiv:2509.18787; IETF Internet Draft |
| **License** | Open-source reference implementation |

The ADS is a distributed directory for AI agent capability discovery, using content-addressed storage, hierarchical taxonomies, and cryptographic signing (via Sigstore) across a Kademlia-based DHT. It decouples capability indexing from content location through a two-level mapping and reuses mature OCI/ORAS infrastructure, supporting federated operation where distinct organizations run autonomous registries without global consensus. An IETF Internet Draft formalizes the protocol, signaling standardization trajectory.[^37][^38][^39]

***

### 5.2 Internet of Agents: Fundamentals and Architecture

| Field | Detail |
|---|---|
| **Title** | Internet of Agents: Fundamentals, Applications, and Challenges |
| **Year** | 2025 |
| **Source** | arXiv:2505.07176 |
| **License** | Open access |

This survey introduces the "Internet of Agents" (IoA) as a foundational framework for seamless interconnection, dynamic discovery, and coordination of AI agents at internet scale. It is the conceptual companion to infrastructure papers like AGNTCY ADS, providing the application-level framing for why distributed agent registries and P2P agent communication matter beyond any single system.[^40]

***

### 5.3 Fortytwo: Swarm Inference with Peer-Ranked Consensus

| Field | Detail |
|---|---|
| **Title** | Fortytwo: Swarm Inference with Peer-Ranked Consensus |
| **Year** | 2025 |
| **Source** | arXiv:2510.24801 |
| **License** | Open access |

Fortytwo presents a protocol leveraging swarm intelligence and distributed pairwise ranking consensus for decentralized AI inference, arguing that concentration of AI capabilities within oligopolistic structures has profound implications for technological sovereignty and economic equity. A Silicon Valley implementation of this protocol has published benchmark results claiming to outperform GPT-5, Gemini 2.5 Pro, and Claude Opus 4.1 on several reasoning benchmarks by connecting a swarm of Small Language Models on personal computers, where node operators can run any privately built model without revealing weights to the network.[^41][^42][^43]

***

## 6. Privacy-Preserving & Decentralized AI

### 6.1 PrivateDFL: Explainable Adaptive Differential Privacy

| Field | Detail |
|---|---|
| **Title** | Privacy-Preserving Decentralized Federated Learning via Explainable Adaptive Differential Privacy |
| **Authors** | Fardin Jalil Piran, Zhiling Chen, Yang Zhang et al. (University of Connecticut) |
| **Year** | 2025 (revised Dec 2025) |
| **Source** | arXiv:2509.10691 |
| **License** | Open access |

PrivateDFL combines HyperDimensional Computing (HD) with a transparent differential privacy noise accountant in a fully serverless, decentralized federated learning framework. By explicitly tracking cumulative perturbations, each client adds only the minimal incremental noise required — yielding 24.4% higher accuracy on MNIST and over 80% higher accuracy on ISOLET versus transformer baselines, while reducing inference latency by up to 76× and energy consumption by up to 36×. Evaluated across IoT-relevant domains (image, speech, wearable sensor), it is a standout open-access contribution to resource-constrained, privacy-first distributed AI.[^44][^45]

***

### 6.2 Privacy-Preserving Decentralized AI with Confidential Computing

| Field | Detail |
|---|---|
| **Title** | Privacy-Preserving Decentralized AI with Confidential Computing |
| **Authors** | Dayeol Lee, Jorge António, Hisham Khan (Atoma Network) |
| **Year** | 2024 |
| **Source** | arXiv:2410.13752 |
| **License** | Open access |

This paper addresses the core privacy challenge of decentralized AI: in a network with diverse node operators, sensitive assets (proprietary models, user data) can be exposed to untrusted participants. The proposed solution leverages TEE-based Confidential Computing within Atoma Network's decentralized AI platform, arguing TEEs can bridge the privacy gap more practically than zero-knowledge machine learning (zkML), which suffers prohibitive computational overhead.[^46]

***

### 6.3 FedAnil: Blockchain-Enabled Federated Deep Learning

| Field | Detail |
|---|---|
| **Title** | Decentralized and Robust Privacy-Preserving Model Using Blockchain-Enabled Federated Deep Learning in Intelligent Enterprises |
| **Authors** | Reza Fotohi, Fereidoon Shams Aliee, Bahar Farahani |
| **Year** | 2025 |
| **Source** | arXiv:2502.17485 |
| **License** | Open access |

FedAnil proposes a blockchain-secured federated deep learning model addressing both non-IID data distribution challenges and security/privacy concerns (poisoning and inference attacks) in a two-phase architecture. Compared to baselines (ShieldFL, RVPFL, RFA), it achieves 11–24% higher accuracy with 8–15% lower computation overhead, providing tamper-proof properties through blockchain anchoring.[^47]

***

### 6.4 Survey on Decentralized Federated Learning

| Field | Detail |
|---|---|
| **Title** | A Survey on Decentralized Federated Learning |
| **Year** | 2023 (updated 2026) |
| **Source** | arXiv:2308.04604 |
| **License** | Open access |

This comprehensive, continuously updated survey defines the DFL field: FL without a central coordinator, replaced by peer-to-peer coordination, making learning dynamics topology-dependent and reshaping associated security, privacy, and systems trade-offs. It remains the canonical reference for understanding the design space of decentralized collaborative learning.[^48]

***

## 7. Scalable Knowledge Sharing & Digital Commons

### 7.1 AgentRxiv: Collaborative Autonomous Research

| Field | Detail |
|---|---|
| **Title** | AgentRxiv: Towards Collaborative Autonomous Research |
| **Authors** | Samuel Schmidgall, Michael Moor |
| **Year** | 2025 |
| **Source** | arXiv:2503.18102 |
| **License** | Open access; platform open to agents |

AgentRxiv is a framework — and live platform — that lets LLM agent laboratories upload and retrieve reports from a shared preprint server, enabling collaborative, cumulative knowledge sharing modeled after arXiv, bioRxiv, and medRxiv. Agents with access to prior research achieve 11.4% relative improvement over isolated agents; multiple labs sharing research achieve 13.7% improvement on MATH-500, demonstrating that cumulative knowledge sharing meaningfully accelerates scientific discovery. This is the most direct existing implementation of an open, distributed knowledge commons for AI agents.[^49][^50][^51]

***

### 7.2 Generative AI and the Future of the Digital Commons

| Field | Detail |
|---|---|
| **Title** | Generative AI and the Future of the Digital Commons |
| **Year** | 2025 |
| **Source** | arXiv:2508.06470 |
| **License** | Open access |

This paper examines the tension between GenAI's capacity to enrich open knowledge repositories (improving metadata, translating content, making archives more accessible) and its risk of undermining them by lowering incentives for human contribution and enabling data extractivism. It raises the urgent question: how can we ensure the digital commons are not threatened by undersupply as people's information-finding needs are increasingly met by closed chatbot services?[^52][^53]

***

### 7.3 The Knowledge Commons in the Age of AI

| Field | Detail |
|---|---|
| **Title** | The Knowledge Commons in the Age of AI: Opportunities and Risks |
| **Year** | 2025 |
| **Source** | ACM Digital Library (Springer) |
| **License** | Open access |

This paper broadly revisits the state of the knowledge commons in the age of AI, examining governance frameworks for collective data stewardship and the structural tension between open knowledge and AI enclosure. It is a key policy-oriented counterpart to the technical literature, linking commons theory (Ostrom, Hess) to AI data governance challenges.[^54]

***

### 7.4 Sustainable Open-Source AI via Data and Impact Accounting

| Field | Detail |
|---|---|
| **Title** | Sustainable Open-Source AI Requires Tracking the Cumulative Impact |
| **Year** | 2026 |
| **Source** | arXiv:2601.21632 |
| **License** | Open access |

This perspective paper proposes **Data and Impact Accounting (DIA)**, a lightweight transparency layer that standardizes carbon and water reporting across open-source AI model families and downstream derivatives. It frames open-source AI as a commons and warns of a tragedy-of-the-commons outcome where aggregate environmental footprint grows despite per-model efficiency gains — offering DIA as a coordination mechanism without restricting access.[^55]

***

### 7.5 ElephantBroker: Knowledge-Grounded Cognitive Runtime

| Field | Detail |
|---|---|
| **Title** | A Knowledge-Grounded Cognitive Runtime for Trustworthy AI Agents |
| **Year** | 2026 |
| **Source** | arXiv:2603.25097 |
| **License** | Open source (GitHub) |

ElephantBroker is an open-source cognitive runtime that unifies a Neo4j knowledge graph with a Qdrant vector store through the Cognee framework, providing AI agents with structured, grounded, and verifiable knowledge access. It represents the convergence of graph databases, vector stores, and agentic reasoning into a single deployable system — a practical reference architecture for distributed knowledge-grounded AI.[^56]

***

## 8. Decentralized AI Platforms & Open-Source Networks

### 8.1 Bittensor: Decentralized Neural Internet

**Project: Bittensor (bittensor.com) | Open-source, MIT | Active**

Bittensor is a peer-to-peer network where AI models collaborate, compete, and are financially rewarded via the **Yuma Consensus** mechanism according to the value they contribute. Co-founded by Jacob Robert Steeves and Ala Shabaana under the OpenTensor Foundation, Bittensor organizes AI into subnets — specialized mini-markets — where validators rank models on accuracy, efficiency, and novelty. Following the dTAO upgrade in February 2025, the number of active subnets surged from 32 to 118, with network market cap reaching $3.6 billion. Macrocosmos's "swarm training" on Subnet 9 enables anyone with a GPU to contribute to training frontier-scale models through a decentralized IOTA (Incentivized Orchestrated Training Architecture).[^57][^58][^59]

An arXiv paper (2505.07828) critically evaluates AI-token projects including Bittensor, SingularityNET, Fetch.ai, and Ocean Protocol, noting that while these platforms advance decentralized AI democratization, many still depend on off-chain computation and have limited on-chain intelligence.[^60][^61]

***

### 8.2 SingularityNET: Decentralized AI Marketplace

**Project: SingularityNET (singularitynet.io) | Open-source | Active**

SingularityNET is a decentralized marketplace for creating, sharing, and monetizing AI services across a distributed platform, widely cited in academic literature as a leading attempt to break the AI oligopoly. It forms part of the Artificial Superintelligence Alliance alongside Fetch.ai and Ocean Protocol, representing the largest open, tokenized AI ecosystem.[^62][^61][^63]

***

### 8.3 AI in Open-Source Software: Emerging Paradigms

| Field | Detail |
|---|---|
| **Title** | From OSS to Open Source AI: An Exploratory Study of Collaborative Development Patterns |
| **Year** | 2026 |
| **Source** | arXiv:2604.08888 |
| **License** | Open access |

This April 2026 paper examines how AI model development is embracing open-source paradigms, noting that "open source" applies differently to AI models than to traditional software artifacts. It explores the adaptation of OSS collaborative practices (contribution workflows, community governance, licensing) to the fundamentally different nature of AI model artifacts — a critical issue for open, decentralized AI commons.[^64]

***

## 9. Human-AI Collaboration for Decentralized Superintelligence

### 9.1 ADEPTS: A Capability Framework for Human-Centered Agents

| Field | Detail |
|---|---|
| **Title** | ADEPTS: A Capability Framework for Human-Centered Agent Design |
| **Authors** | Pierluca D'Oro, Caley Drooff, Joy Chen, Joseph Tighe (Meta FAIR) |
| **Year** | 2025 |
| **Source** | arXiv:2507.15885 |
| **License** | Open access |

ADEPTS defines six principles for human-centered AI agent design — Actuation, Disambiguation, Evaluation, Personalization, Transparency, and Safety — providing unified vocabulary for teams building AI agents that are understandable, controllable, and trustworthy in everyday human use. It bridges UX heuristics, engineering taxonomies, and ethics checklists into a single framework, essential for human-AI collectives where sovereignty and trust are non-negotiable.[^65]

***

### 9.2 NovelSeek: Closed-Loop Autonomous Scientific Research

| Field | Detail |
|---|---|
| **Title** | NovelSeek: When Agent Becomes the Scientist – Building Closed-Loop System from Hypothesis to Verification |
| **Authors** | NovelSeek Team, Shanghai Artificial Intelligence Laboratory |
| **Year** | 2025 |
| **Source** | arXiv:2505.16938; GitHub + HuggingFace |
| **License** | Open source |

NovelSeek is a unified, closed-loop multi-agent framework for Autonomous Scientific Research (ASR) across 12 scientific domains, enabling researchers to tackle complex problems with unprecedented speed. Its open-source release on GitHub and HuggingFace, combined with its multi-domain versatility, makes it a foundational reference for human-AI collaborative research in a decentralized setting.[^66]

***

### 9.3 AI Assistance in Mathematical Research

| Field | Detail |
|---|---|
| **Title** | Solving a Research Problem in Mathematical Statistics with AI Assistance |
| **Year** | 2025 |
| **Source** | arXiv:2511.18828 |
| **License** | Open access |

This short note documents how GPT-5 Pro provided "crucial help" in solving a previously unsolved problem in robust mathematical statistics over a few weeks — work estimated to otherwise take several months. It is an honest, first-person account of the frontier of human-AI co-research, noting both the acceleration and the failures (incorrect references, glossed-over details requiring days of additional verification).[^67]

***

### 9.4 A Different Approach to AI Safety: Columbia Convening

| Field | Detail |
|---|---|
| **Title** | A Different Approach to AI Safety: Proceedings from the Columbia Convening on Openness in AI and Safety |
| **Year** | 2025 |
| **Source** | Semantic Scholar |
| **License** | Open access |

This policy-research paper from the Columbia Convening (November 2024, 45+ participants from academia, industry, civil society, and government) argues that openness — transparent weights, interoperable tooling, and public governance — can enhance AI safety by enabling independent scrutiny, decentralized mitigation, and culturally plural oversight. It identifies significant gaps: scarce multimodal/multilingual benchmarks, insufficient defenses against prompt-injection in agentic systems, and insufficient participatory mechanisms for communities most affected by AI harms.[^68]

***

## 10. Synthesis: Convergence Patterns & Research Frontiers

The research landscape as of April 2026 reveals five convergence patterns critical for building open, decentralized, privacy-preserving superintelligent collectives:

**1. Sovereign agent identity is the foundation.** Both Holochain and AD4M converge on DID-based agent identity with locally-held keys and cryptographically signed expressions as the minimal trust primitive for any distributed system. Without sovereign identity, neither privacy nor meaningful governance is achievable.[^1][^4]

**2. Federated retrieval is replacing centralized RAG.** RAGRoute, HyFedRAG, FedVSE, and FedVS all demonstrate that single-vector-database RAG is architecturally unsuitable for multi-stakeholder knowledge commons. The field is converging on federated retrieval with policy enforcement as the production model.[^25][^29][^26][^27]

**3. Governance must be co-designed with semantics.** The Governance-Aware Vector Subscriptions paper is a landmark: it is the first work to formally compose semantic similarity matching with regulatory policy predicates in a multi-agent knowledge ecosystem. AIngram's AGPL-3.0 implementation makes this immediately deployable.[^31]

**4. Coordination scaling rivals model scaling.** SwarmSys, SAGE, MarsRL, and the broader swarm intelligence literature consistently show that intelligent coordination among smaller, specialized agents frequently outperforms single large models — with the important caveat (from the LLM-powered swarms critique) that computational overhead remains a serious engineering challenge.[^17][^21][^16]

**5. The digital commons faces an existential moment.** The tension between open AI and the knowledge commons it was built on is now a primary research concern, with multiple open-access papers (arXiv:2508.06470, Columbia Convening, DIA proposal) arguing that without active governance and transparency infrastructure, GenAI will hollow out the open knowledge repositories that enabled it.[^68][^52][^55]

***

## Appendix: Quick-Reference Index by Domain

| Domain | Key Papers / Projects | Year | Source |
|---|---|---|---|
| Agent-centric P2P | Holochain + Kitsune2 | 2025 | holochain.org |
| Agent-centric spanning layer | AD4M / ADAM Layer | 2024–2026 | coasys.org / arXiv |
| Decentralized LLM serving | PlanetServe | 2025 | arXiv:2504.20101 |
| P2P peer sampling | Honeybee | 2024 | arXiv:2402.16201 |
| Collective intelligence theory | AI-Enhanced Collective Intelligence | 2024 | PMC11573907 |
| AI collective self-regulation | Evolving AI Collectives | 2024 | arXiv:2402.12590 |
| Swarm multi-agent reasoning | SwarmSys | 2025 | arXiv:2510.10047 |
| Multi-agent self-evolution | SAGE | 2026 | arXiv:2603.15255 |
| RL multi-agent reasoning | MarsRL | 2025 | arXiv:2511.11373 |
| Decentralized multi-agent | AgentNet | 2025 | arXiv:2504.00587 |
| Multi-modal decentralized QA | Dealog | 2026 | arXiv:2602.00996 |
| Federated RAG retrieval | RAGRoute | 2025 | arXiv:2502.19280 |
| Federated vector search | FedVSE | 2025 | VLDB 2025 |
| Federated multi-modal RAG | HyFedRAG | 2025 | arXiv:2509.06444 |
| Hybrid vector + graph index | HMGI | 2025 | arXiv:2510.10123 |
| Governance-aware vector subscriptions | Governance-Aware Vector Subscriptions | 2026 | arXiv:2603.20833 |
| Distributed vector DB HPC | Qdrant on Polaris | 2025 | arXiv:2509.12384 |
| Knowledge-grounded agent runtime | ElephantBroker | 2026 | arXiv:2603.25097 |
| Decentralized FL + privacy | PrivateDFL | 2025 | arXiv:2509.10691 |
| Confidential computing + decentralized AI | Atoma Network / TEE | 2024 | arXiv:2410.13752 |
| Blockchain FL | FedAnil | 2025 | arXiv:2502.17485 |
| Agent discovery infrastructure | AGNTCY ADS | 2025 | arXiv:2509.18787 |
| Swarm inference protocol | Fortytwo | 2025 | arXiv:2510.24801 |
| Collaborative autonomous research | AgentRxiv | 2025 | arXiv:2503.18102 |
| Digital commons & GenAI | GenAI and the Digital Commons | 2025 | arXiv:2508.06470 |
| Open AI sustainability | Sustainable Open-Source AI (DIA) | 2026 | arXiv:2601.21632 |
| Decentralized AI network | Bittensor / dTAO | 2025 | OpenTensor Foundation |
| Decentralized AI marketplace | SingularityNET | 2024–2026 | singularitynet.io |
| Human-centered agent design | ADEPTS | 2025 | arXiv:2507.15885 |
| Closed-loop autonomous science | NovelSeek | 2025 | arXiv:2505.16938 |
| AI safety + openness | Columbia Convening | 2025 | Semantic Scholar |

***

*All papers cited are open-access. Open-source projects listed are under FOSS licenses (Apache 2.0, MIT, AGPL-3.0, or equivalent). Compiled for the Open Research Explorer — April 14, 2026.*

---

## References

1. [Can Holochain Replace Traditional Blockchains? Reviewing Its ...](https://defi-planet.com/2025/11/can-holochain-replace-traditional-blockchains-reviewing-its-agent-centric-approach-in-2025/) - Can Holochain replace traditional blockchains like Ethereum or Bitcoin? This 2025 review explores Ho...

2. [2025 at a Glance: Landing Reliability - Holochain Blog](https://blog.holochain.org/2025-at-a-glance-landing-reliability/) - Blog

3. [The Holochain Ecosystem in 2025: A Friendly Reality Check - AlterNef](http://alternef.garden/blog/holochain-ecosystem-reality-check-2025) - An honest, comprehensive look at where Holochain stands today - celebrating genuine progress while a...

4. [Agents: The Foundation of AD4M | AD4M Docs](https://docs.ad4m.dev/agents/) - Documentation site for AD4M

5. [GitHub - coasys/ad4m: Agent-centric social network and interoperability dApp framework](https://github.com/coasys/ad4m/) - Agent-centric social network and interoperability dApp framework - coasys/ad4m

6. [AD4M as a Spanning Layer](https://docs.ad4m.dev/spanning-layer) - Documentation site for AD4M

7. [Adam - Coasys - A Digital Nervous System for the Wise Web](https://coasys.org/adam) - Conceptually, AD4M Agents are modelled as something that can speak and that can listen. Agents commu...

8. [PlanetServe: A Decentralized, Scalable, and Privacy-Preserving ...](https://arxiv.org/html/2504.20101v5) - PlanetServe naturally inherits benefits that are common to decentralized overlay systems, such as se...

9. [PlanetServe: A Decentralized, Scalable, and Privacy-Preserving ...](https://arxiv.org/html/2504.20101v4) - PlanetServe relies on an open-source consensus protocol Tendermint [buchman2018latest] to ensures sa...

10. [Honeybee: Byzantine Tolerant Decentralized Peer Sampling with Verifiable
  Random Walks](http://arxiv.org/pdf/2402.16201.pdf) - Popular blockchains today have hundreds of thousands of nodes and need to be
able to support sophist...

11. [AI-enhanced collective intelligence](https://pmc.ncbi.nlm.nih.gov/articles/PMC11573907/) - ...Ireland

^∗^
Corresponding author taha.yasseri@tcd.ie

Collection date 2024 Nov 8.

PMCID: PMC115...

12. [Artificial Collective Intelligence Engineering: a Survey of Concepts and
  Perspectives](https://arxiv.org/pdf/2304.05147.pdf) - ...By exploiting a large number of individuals, it is often possible
to produce effects that go far ...

13. [Evolving AI Collectives to Enhance Human Diversity and Enable
  Self-Regulation](http://arxiv.org/pdf/2402.12590.pdf) - ...societies" of interacting
artificial intelligences to increase their rewards and reduce their ris...

14. [Towards a Science of Collective AI: LLM-based Multi-Agent ... - arXiv](https://arxiv.org/abs/2602.05289) - Title:Towards a Science of Collective AI: LLM-based Multi-Agent Systems Need a Transition from Blind...

15. [Emergent collective intelligence from massive-agent cooperation and
  competition](https://arxiv.org/abs/2301.01609) - Inspired by organisms evolving through cooperation and competition between
different populations on ...

16. [SwarmSys: Decentralized Swarm-Inspired Agents for ...](https://arxiv.org/abs/2510.10047) - Large language model (LLM) agents have shown remarkable reasoning abilities. However, existing multi...

17. [SAGE: Multi-Agent Self-Evolution for LLM Reasoning - arXiv](https://arxiv.org/html/2603.15255v2) - To address these gaps, we propose SAGE (Self-evolving Agents for Generalized reasoning Evolution), a...

18. [MarsRL: Advancing Multi-Agent Reasoning System via ... - arXiv](https://arxiv.org/html/2511.11373v1) - MarsRL introduces agent-specific reward mechanisms to mitigate reward noise and employs pipeline-ins...

19. [AgentNet: Decentralized Evolutionary Coordination for LLM-based
  Multi-Agent Systems](https://arxiv.org/html/2504.00587v1) - The rapid advancement of Large Language Models (LLMs) has catalyzed the
development of multi-agent s...

20. [Decentralized Multi-Agents Log-Mediated Reasoning Framework](https://arxiv.org/html/2602.00996v1) - We introduce Dealog, a decentralized multi-agent framework for multimodal question answering. It use...

21. [LLM-Powered Swarms: A New Frontier or a Conceptual Stretch?](https://arxiv.org/html/2506.14496v2) - This paper evaluates whether such systems capture the fundamental principles of classical swarm inte...

22. [LLM-based Agent Unified Modeling Framework for ...](https://arxiv.org/abs/2409.11393) - # Computer Science > Software Engineering

**arXiv:2409.11393** (cs)

[Submitted on 17 Sep 2024 (v1)...

23. [The Orchestration of Multi-Agent Systems: Architectures, Protocols ...](https://arxiv.org/html/2601.13671v1) - Orchestrated multi-agent systems represent the next stage in the evolution of artificial intelligenc...

24. [Exploring Distributed Vector Databases Performance on HPC ... - arXiv](https://arxiv.org/html/2509.12384v2) - Vector databases enable efficient search over encoded representations of embedded data known as vect...

25. [Efficient Federated Search for Retrieval-Augmented Generation - arXiv](https://arxiv.org/html/2502.19280v1) - We introduce RAGRoute, a novel mechanism for federated RAG search. RAGRoute dynamically selects rele...

26. [[PDF] FedVSE: A Privacy-Preserving and Efficient Vector Search Engine ...](https://www.vldb.org/pvldb/vol18/p5371-tong.pdf) - In these privacy-sensitive scenarios, a vector search engine must not only deliver high performance ...

27. [[PDF] FedVS: Towards Federated Vector Similarity Search with Filters](https://hufudb.com/static/paper/2025/KDD25-fan.pdf) - Abstract. Vectors are used to represent unstructured data with their embed- dings and associated att...

28. [FedVS: Towards Federated Vector Similarity Search with Filters](https://dl.acm.org/doi/10.1145/3711896.3736958) - It aims to identify the k nearest neighbors to a query object from vectors that satisfy a given attr...

29. [[PDF] HyFedRAG: A Federated Retrieval-Augmented Generation ... - arXiv](https://arxiv.org/pdf/2509.06444.pdf) - Abstract. Centralized RAG pipelines struggle with heterogeneous and privacy-sensitive data, especial...

30. [The Hybrid Multimodal Graph Index (HMGI) - arXiv](https://arxiv.org/html/2510.10123v1) - This paper introduces the Hybrid Multimodal Graph Index (HMGI), a novel framework designed to bridge...

31. [Governance-Aware Vector Subscriptions for Multi-Agent Knowledge ...](https://arxiv.org/abs/2603.20833) - Abstract page for arXiv paper 2603.20833: Governance-Aware Vector Subscriptions for Multi-Agent Know...

32. [Governance-Aware Vector Subscriptions for Multi-Agent Knowledge ...](https://arxiv.org/html/2603.20833v2)

33. [Best Embedding Model for RAG 2026: 10 Models Compared - Milvus](https://milvus.io/blog/choose-embedding-model-rag-2026.md) - We benchmarked 10 embedding models on cross-modal, cross-lingual, long-document, and dimension compr...

34. [Best Vector Databases For Multimodal GenAI In 2026 - AceCloud](https://acecloud.ai/blog/best-vector-databases-for-multimodal-genai/) - Compare Pinecone, Weaviate, Milvus, Qdrant, Elastic, pgvector, and LanceDB for multimodal GenAI, RAG...

35. [7 Most Popular Vector Databases: A 2026 Guide - Cake AI](https://www.cake.ai/blog/best-vector-databases) - Our 2026 guide ranks the most popular vector databases for AI. Compare top solutions for scalability...

36. [Vector Databases in Distributed Knowledge Base Architectures](https://blog.naitive.cloud/vector-databases-distributed-knowledge-base-architectures/) - Vector databases power scalable semantic knowledge bases but require careful sharding, indexing, and...

37. [[PDF] The AGNTCY Agent Directory Service: Architecture and ... - arXiv](https://arxiv.org/pdf/2509.18787.pdf) - Abstract. The Agent Directory Service (ADS) is a distributed directory for the discovery of AI agent...

38. [[Revue de papier] The AGNTCY Agent Directory Service](https://www.themoonlight.io/fr/review/the-agntcy-agent-directory-service-architecture-and-implementation) - The AGNTCY Agent Directory Service (ADS) is a distributed directory designed for the discovery of Ar...

39. [Agent Directory Service](https://spec.dir.agntcy.org/560-update-internet-draft-agntcy-agent-directory-architecture/draft-mp-agntcy-ads.html) - The Agent Directory Service (ADS) is a distributed directory service designed to store metadata for ...

40. [Internet of Agents: Fundamentals, Applications, and Challenges - arXiv](https://arxiv.org/html/2505.07176v1) - In this survey, we introduce the Internet of Agents (IoA) as a foundational framework that enables s...

41. [Fortytwo has the answer to everything: decentralized AI - The Register](https://www.theregister.com/2025/11/02/fortytwo_dcentralized_ai/) - : No datacenters required

42. [[PDF] Fortytwo: Swarm Inference with Peer-Ranked Consensus - arXiv](https://arxiv.org/pdf/2510.24801.pdf) - We present Fortytwo, a novel protocol that leverages swarm intelligence principles and distributed p...

43. [Fortytwo: Swarm Inference with Peer-Ranked Consensus - arXiv](https://arxiv.org/html/2510.24801v1) - We present Fortytwo, a novel protocol that leverages swarm intelligence principles and distributed p...

44. [[2509.10691] Privacy-Preserving Decentralized Federated Learning ...](https://arxiv.org/abs/2509.10691) - Abstract page for arXiv paper 2509.10691: Privacy-Preserving Decentralized Federated Learning via Ex...

45. [Privacy-Preserving Decentralized Federated Learning via Explainable Adaptive Differential Privacy](https://www.arxiv.org/abs/2509.10691) - Decentralized federated learning faces privacy risks because model updates can leak data through inf...

46. [Privacy-Preserving Decentralized AI with Confidential Computing](https://arxiv.org/abs/2410.13752) - This paper addresses privacy protection in decentralized Artificial Intelligence (AI) using Confiden...

47. [Decentralized and Robust Privacy-Preserving Model Using ... - arXiv](https://arxiv.org/abs/2502.17485) - We propose FedAnil, a secure blockchain enabled Federated Deep Learning Model that improves enterpri...

48. [A Survey on Decentralized Federated Learning - arXiv](https://arxiv.org/html/2308.04604v2) - Su (2025) Mitigating the privacy–utility trade-off in decentralized federated learning via f-differe...

49. [AgentRxiv: Towards Collaborative Autonomous Research - arXiv](https://arxiv.org/abs/2503.18102) - We introduce AgentRxiv-a framework that lets LLM agent laboratories upload and retrieve reports from...

50. [AgentRxiv](https://agentrxiv.github.io) - A centralized preprint server designed specifically for autonomous research agents to overcome the l...

51. [AgentRxiv: Towards Collaborative Autonomous Research](https://huggingface.co/papers/2503.18102) - A framework that lets LLM agent laboratories upload and retrieve reports from a shared preprint serv...

52. [Generative AI and the Future of the Digital Commons - arXiv](https://arxiv.org/html/2508.06470v1) - Their absence in the public debate is even more striking given that today's generative AI models for...

53. [[PDF] Generative AI and the Future of the Digital Commons - arXiv](https://www.arxiv.org/pdf/2508.06470.pdf) - Recent reports have shown that the introduction of GenAI has lowered incentives to contribute to sha...

54. [The Knowledge Commons in the Age of AI: Opportunities and Risks ...](https://dl.acm.org/doi/10.1007/978-3-031-92980-9_4) - This paper reflects on the state of the knowledge commons in the age of artificial intelligence (AI)...

55. [Sustainable Open-Source AI Requires Tracking the Cumulative ...](https://arxiv.org/html/2601.21632v2) - We propose Data and Impact Accounting (DIA), a lightweight, non-restrictive transparency layer that ...

56. [A Knowledge-Grounded Cognitive Runtime for Trustworthy AI Agents](https://arxiv.org/abs/2603.25097) - We present ElephantBroker, an open source cognitive runtime that unifies a Neo4j knowledge graph wit...

57. [Alpha Sigma Capital Research Publishes New Report on Bittensor (TAO), Decentralized 'Neural Internet” Model](https://www.manilatimes.net/2025/04/29/tmt-newswire/globenewswire/alpha-sigma-capital-research-publishes-new-report-on-bittensor-tao-decentralized-neural-internet-model/2101510) - **media[608720]**

58. [Swarm Intelligence Is Reshaping How AI Gets Trained - Forbes](https://www.forbes.com/sites/torconstantino/2025/06/02/swarm-intelligence-is-reshaping-how-ai-gets-trained/) - Macrocosmos' newly launched "swarm training" on Bittensor could change how AI is built—making model ...

59. [Decentralized AI's Rising Cost Efficiency and Network Growth in ...](https://www.ainvest.com/news/decentralized-ai-rising-cost-efficiency-network-growth-bittensor-subnet-62-2509/) - Decentralized AI's Rising Cost Efficiency and Network Growth in Bittensor Subnet 62

60. [AI-Based Crypto Tokens: The Illusion of Decentralized AI? - arXiv](https://arxiv.org/html/2505.07828v2) - These tokens aim to shift control over AI technologies away from centralized corporations, where use...

61. [[PDF] AI-Based Crypto Tokens: The Illusion of Decentralized AI? - arXiv](https://arxiv.org/pdf/2505.07828.pdf) - The aim is to identify viable paths forward for AI-token systems to evolve into more mature, impactf...

62. [Top 51 AI x blockchain companies in 2025 - AI Operator](https://51ai.substack.com/p/top-51-ai-x-blockchain-companies) - Artificial Superintelligence Alliance – Platform exploring advanced AI and human-AI collaboration fr...

63. [SingularityNET - Next Generation of Decentralized AI](https://singularitynet.io) - SingularityNET – Next Generation of Decentralized AI

64. [From OSS to Open Source AI: an Exploratory Study of Collaborative ...](https://arxiv.org/html/2604.08888v1) - AI development is embracing open-source paradigm, but the fundamental distinction between AI models ...

65. [A Capability Framework for Human-Centered Agent Design](https://arxiv.org/html/2507.15885v1) - 1. 1 Introduction
2. 2 Principles for Human-Centered Agent Design
3. 3 The ADEPTS Capability Framewo...

66. [NovelSeek: When Agent Becomes the Scientist – Building Closed ...](https://arxiv.org/html/2505.16938v1) - Agentrxiv: Towards collaborative autonomous research. arXiv preprint arXiv:2503.18102, 2025. Schmidg...

67. [Solving a Research Problem in Mathematical Statistics with AI Assistance](https://arxiv.org/abs/2511.18828) - Over the last few months, AI models including large language models have improved greatly. There are...

68. [A Different Approach to AI Safety: Proceedings from the Columbia Convening on Openness in Artificial Intelligence and AI Safety](https://www.semanticscholar.org/paper/9085356fdae3ee0471ceb226ae49b8d9e03261d2) - The rapid rise of open-weight and open-source foundation models is intensifying the obligation and r...

