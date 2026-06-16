# Automated Agent Orchestration for Decentralized Open-Source AI Development

> A technically grounded synthesis covering coordination algorithms, governance mechanisms, infrastructure patterns, automation techniques, case studies, and the genuine unsolved problems — as of April 2026.

***

## Executive Summary

The field of automated multi-agent orchestration for decentralized, open-source AI has reached a significant inflection point. Individual AI coding agents have demonstrated production-level capability — one benchmark places PR merge rates for AI-authored code at 67%, with 22% of merged code now AI-written. The unsolved problem is not agent capability but **team infrastructure**: how multiple autonomous agents coordinate, learn from each other, maintain alignment, and operate without requiring a centralized owner or bottleneck. This report synthesizes the current state of knowledge across six critical dimensions, with honest accounting of what works, what partially works, and what remains genuinely open.[^1]

***

## Multi-Agent Coordination Algorithms

### The CTDE Paradigm and Its Limits

The dominant algorithmic paradigm in multi-agent systems research is **Centralized Training with Decentralized Execution (CTDE)**. Frameworks like MAPPO and QMIX use a central critic during training that has access to all agents' observations and states, while individual agents execute using only local observations. This achieves strong coordination — empirically around 26 reward points above fully decentralized baselines in cooperative navigation benchmarks — but it requires a central training authority and does not scale to open systems where agent populations are dynamic.[^2][^3][^4]

The fundamental limitation of fully decentralized learning is what the literature calls the **coordination paradox**: decentralized agents can achieve high local coverage but poor global performance, because individual reward optimization diverges from global objectives. Three root causes have been formalized: (1) non-stationarity from concurrent policy updates breaking Markov assumptions, (2) exponential credit assignment complexity as teams grow, and (3) misalignment between individual reward shaping and global outcomes.[^3][^5]

### AgentNet and Dynamic DAG Coordination

The most significant recent advance for fully decentralized LLM-based orchestration is **AgentNet** (NeurIPS 2025). AgentNet eliminates the central orchestrator entirely. Agents specialize autonomously via RAG-based memory and route tasks through a dynamically structured **Directed Acyclic Graph (DAG)** that evolves based on local expertise and context. Unlike prior systems with static role assignment, any agent can adjust connectivity and accept tasks based on its retrieved skill profile. Experiments demonstrated higher task accuracy than both single-agent and centralized multi-agent baselines, with privacy-preserving cross-organizational collaboration as a primary benefit.[^6][^7][^8]

**AgentNet++** (late 2025) extends this with cluster-based hierarchies where agents self-organize into specialized groups. The hierarchical extension achieves 23% higher task completion rates, 40% reduction in communication overhead, and formally proven convergence and differential privacy bounds — scaling effectively to 1,000+ agents. This represents the current frontier for decentralized LLM coordination.[^9]

### Hierarchical and LLM-Co Approaches

Hierarchical decomposition remains practically important. The **DEPART framework** (NeurIPS 2024) implements a six-step coordination loop: Divide, Evaluate, Plan, Act, Reflect, Track — enabling modular agent specialization through a parent-child chain of responsibility that replaces chaotic peer-to-peer chatter with clear vertical handoffs. The **LLM-Co** framework demonstrated that decentralized all-to-all peer critique topology outperforms centralized hub-and-spoke in bias reduction, typically converging in 1–2 rounds. The **HRCL** (Hierarchical Reinforcement and Collective Learning) approach addresses the joint state-action space explosion by separating high-level strategy assignment (MARL layer) from low-level collective coordination (minimal communication), showing improved scalability and performance in smart city and drone swarm scenarios.[^10][^11][^12]

### Algorithm Trade-off Landscape

| Approach | Scalability | Fault Tolerance | Privacy | Training Cost | Coordination Quality |
|---|---|---|---|---|---|
| CTDE (MAPPO/QMIX) | Medium | Low (central dep.) | Low | High | Highest |
| Full Decentralized (IPPO) | High | High | High | Low | ~26 pts below CTDE[^3] |
| AgentNet (DAG) | High | High | High | Medium | Near-CTDE[^6] |
| AgentNet++ Hierarchical | High (1000+) | High | High (DP bounds) | Medium | 23% above AgentNet[^9] |
| HRCL Hierarchical | High | High | Medium | Medium | Strong on combinatorial tasks[^12] |
| LLM-Co Peer Critique | Medium | High | High | Medium | Best for bias reduction[^11] |

### The Credit Assignment Problem

Credit assignment — determining each agent's contribution to collective outcomes — remains a foundational unsolved problem. Traditional methods assume static agent populations and fixed task structures, making them inadequate for open environments where agents enter and leave. Research published at AAMAS 2025 introduced **LLM-MCA**, which reframes credit assignment as a pattern recognition problem and uses a centralized LLM reward-critic to decompose global reward into per-agent contributions, then trains local policy networks on this feedback. CMU's 2025 thesis work introduced **ME-IGM**, which improves multi-agent credit assignment under maximum entropy RL frameworks where traditional QMIX-style decomposition fails. Both represent progress, but neither fully solves the problem in dynamic open environments.[^5][^13][^14][^15]

***

## Distributed Consensus and Governance

### Consensus Mechanism Selection

The choice of consensus mechanism for decentralized AI systems involves real trade-offs along the CAP theorem's axes. For permissioned multi-agent systems where nodes are known but potentially faulty:[^16]

- **Raft** delivers 3,500+ TPS with sub-second finality on Hyperledger Fabric but provides only crash fault tolerance — it cannot detect or survive malicious nodes. It is appropriate for trusted single-organization deployments.[^17][^16]
- **PBFT** tolerates Byzantine failures with a 3f+1 node requirement but has O(n²) message complexity, making it impractical beyond ~20 nodes.[^18][^16]
- **Tendermint/CometBFT** is the current practical sweet spot: 1,000–10,000 TPS, 1–6 second finality, supports 200+ validators in production, tolerates up to 1/3 Byzantine failures. Its Application Blockchain Interface (ABCI) separates consensus from application logic, meaning the same consensus engine can underlie different AI governance applications. It powers 50+ chains in the Cosmos ecosystem.[^19][^17][^16]
- **HotStuff** achieves linear view-change complexity, reducing the quadratic message overhead of PBFT while maintaining BFT guarantees — the basis for Facebook's LibraBFT/DiemBFT.[^16]

**Holochain's approach is categorically different**: it eliminates global consensus entirely. Each agent maintains its own cryptographically signed source chain, and a DHT handles shared state with **peer-based validation** rather than network-wide agreement. This means the system scales horizontally without consensus bottlenecks, but at the cost of a different trust model: validity is enforced by application-specific validation rules applied by random DHT neighbors, not by a supermajority.[^20][^21][^22]

### DAO Governance for Open-Source AI Projects

Decentralized Autonomous Organizations represent the leading model for governance of open-source AI systems without centralized control. The **ETHOS framework** proposes DAOs as the backbone for AI agent governance: stakeholders (developers, auditors, ethicists, regulators) vote on risk thresholds and ethical guidelines, with all governance actions immutably recorded on-chain for transparent audit trails. Smart contracts automate enforcement of compliance decisions, reducing the human bottleneck in governance.[^23]

A key 2026 empirical study on DAO-based democratic AI governance found that **quadratic voting with equal power distribution** best enables minority voices and yields outcomes perceived as fair and democratic — significantly outperforming centralized decision-making in stakeholder satisfaction. The fundamental tension identified is between participatory decision-making and the global, distributed nature of AI: meaningful participation requires accessible tooling, clear proposal framing, and structured deliberation before voting. DAOs also offer a mechanism for governing computational resources in a decentralized manner — distributed GPU pools governed by community vote rather than corporate allocation.[^24][^25]

***

## Infrastructure Patterns for Value Alignment Without Centralization

### Holochain as Trust Foundation

Holochain's agent-centric architecture is architecturally suited to the problem of value alignment without centralization because **the validation rules themselves are the alignment mechanism**. In a Holochain application (hApp), every agent/node independently validates all data against application-specific rules encoded in the hApp's DNA. A node that produces invalid data is rejected by its DHT peers; if it persists, it must fork to its own hApp. This makes alignment rules enforced through the fabric of the network rather than by a central authority.[^22][^20]

In 2025, Holochain made a deliberate choice to focus on **reliability rather than new features** — fixing core functionality, building automated load testing infrastructure, and hunting for bugs that only manifest under production load. The Humm hApp successfully migrated to the new Holo Allograph network in 2025, representing one of the first full production hApp deployments. The limitation remains ecosystem maturity: adoption is narrow compared to EVM chains, tooling is still developing, and the ecosystem has not yet reached the network effects necessary for robust agent-to-agent discovery at scale.[^21][^26][^27]

### AD4M: Agent-Centric Spanning Layer

**AD4M (Agent-centric Distributed Application Meta-ontology)**, built on Holochain, operates as a spanning layer above the internet. Its meta-ontology defines three classes: **Agents** (represented by DIDs), **Languages** (protocol abstractions that can wrap HTTP, IPFS, custom P2P protocols, or federated APIs), and **Perspectives** (personal, locally stored RDF graph databases). Each AD4M instance is a sovereign local runtime — no central server, the user's DID signs every action.[^28][^29]

The critical design property for agent orchestration is that **Languages are evolvable without hard forks**: a `language-language` meta-protocol allows the framework itself to adopt new protocols as agents need them. This means a Holochain-based AI agent system using AD4M can bridge currently competing P2P, federated, and centralized infrastructure within a single semantic graph — the agent composes across substrates rather than being locked to one. Scryer Prolog enables semantic reasoning and queries directly within the AD4M layer, providing a logic engine for agent decision-making without external dependencies.[^30][^28]

### IPFS for Immutable Artifact Storage

IPFS's content-addressed architecture — where every file receives a unique CID based on its content — provides natural deduplication, integrity verification, and censorship resistance for AI agent artifacts. For AI systems, the practical use cases are: archiving model checkpoints, storing simulation datasets, distributing agent specifications, and creating immutable records of agent decisions. The **AGNTCY Agent Directory Service** (ADS) uses IPFS Kademlia DHT to create a decentralized agent registry, mapping semantic capabilities to content-addressed immutable digests and locating agents across heterogeneous registries.[^31][^32][^33][^34]

IPFS is not suitable for dynamic agent pipelines that require low-latency state reads. It is appropriate for cold storage, audit trails, and capability advertisement — not for real-time inter-agent messaging. IPNS (InterPlanetary Name System) provides mutable references into IPFS, enabling agent profiles to evolve while maintaining addressability.[^32]

### Model Context Protocol (MCP) as Interoperability Layer

Anthropic's **Model Context Protocol** (MCP), open-sourced in November 2024 and now supported by OpenAI, Anthropic, and HuggingFace, standardizes how agents connect to external tools and data sources via JSON-RPC 2.0. MCP functions as a capability discovery and invocation protocol: agents query MCP servers to discover what tools are available, invoke them through structured schemas, and receive structured responses. Complementing it, Google's **A2A (Agent-to-Agent)** protocol addresses direct inter-agent communication.[^35][^36][^37][^38][^39]

The security risks are real and documented: in early 2026, 1,184 malicious skills were discovered on ClawHub, exfiltrating API keys, crypto wallets, and browser credentials from self-hosted instances. The architectural vulnerabilities (plaintext credential storage, advisory sandboxing, trust-by-default authentication) are design-level issues requiring redesign rather than patches. For decentralized open-source deployments, every tool call from an LLM should be treated as untrusted external input from an unauthenticated source.[^40]

***

## Automation Techniques to Reduce Human Bottlenecks

### The AI Productivity Paradox

A counterintuitive empirical finding has emerged from 2025 data: AI agents accelerate code generation but create validation bottlenecks downstream. The "AI productivity paradox" (Faros AI, 2025) shows that introducing AI code generation into a team that has not redesigned its CI/CD and review processes results in a 7.2% decrease in delivery stability and an increase in architectural technical debt, even as developers subjectively feel more productive. The bottleneck moves from generation to review, testing, and deployment. Solving this requires redesigning the entire pipeline, not just replacing humans with agents at one stage.[^41][^42][^1]

### Redesigning CI/CD for Agent Workflows

Effective automation requires agent-aware pipelines that distinguish between human and agent commits. Best practices emerging from 2025–2026 deployments:[^43]

- **Agent PRs trigger additional validation layers**: regression testing, mutation testing, and security scanning that would be optional for human commits become mandatory.[^43]
- **Supervisor agents** validate sub-agent outputs before merge, reducing change failure rates. The Leap CRM case study showed supervisor agents enforcing automated testing policies reduced change failure rates significantly.[^43]
- **Elastic's self-correcting PR pipeline** (2025) introduced GenAI into CI to automate dependency update PRs and apply self-corrections, automizing hundreds of dependencies that previously required manual intervention.[^44]
- **Predictive quality gates** using historical build data allow AI to predict failure likelihood before merge, reducing wasted compute on builds that will fail.[^45]
- **Kubernetes-native agent sandboxing** solves the validation bottleneck by running agent code in isolated sandboxes with parallelized test execution.[^42]

### Automated Design of Agentic Systems (ADAS)

The most radical automation approach is **ADAS** — having a meta-agent automatically design new agents by programming them in code. Meta Agent Search, presented at ICLR 2025, demonstrated that agents defined in code can be discovered and improved by a meta-agent searching a Turing-complete design space. It outperformed state-of-the-art hand-designed agents on the ARC challenge and showed transferability across reasoning domains.[^46][^47][^48][^49]

The critical limitation explicitly flagged in the ICLR 2025 slides: **safety in ADAS is future work**. A system that automatically designs increasingly capable agentic systems has no current mechanism for ensuring alignment of the designed agents. This is not a minor gap — it is the central safety concern for any production deployment of ADAS-style automated orchestration.[^48]

### Codified Context Infrastructure

A practical 2026 case study from a 108,000-line C# distributed system demonstrated an effective pattern for maintaining agent coherence across sessions: a three-component **codified context infrastructure** consisting of (1) a "hot-memory constitution" encoding conventions, retrieval hooks, and orchestration protocols; (2) 19 specialized domain-expert agents; and (3) a cold-memory knowledge base of 34 on-demand specification documents. Across 283 development sessions, this infrastructure prevented session coherence loss and maintained consistency in ways that stateless agent invocations cannot. The framework was published as an open-source companion repository, making it directly applicable to open-source projects.[^50]

### Multica: Agents as Teammates

**Multica** (Apache 2.0) is the most directly relevant open-source platform for the specific problem of integrating multiple coding agents into a coherent development workflow. With ~5,800 GitHub stars as of April 2026, it treats agents as first-class team members on project boards: they appear alongside human developers, accept assigned GitHub issues autonomously, write code, report blockers proactively, and update statuses.[^51][^52][^1]

The technical stack — Go backend, Next.js 16 frontend, PostgreSQL 17 with **pgvector for semantic skill search** — enables skill compounding: agents accumulate skills in a vector store that is searchable across sessions, so learned capabilities persist and compound. The platform auto-detects Claude Code, Codex, OpenClaw, and OpenCode via CLI scanning, requiring no adapter code. The interaction model shift from synchronous (prompt → wait → copy) to asynchronous (assign → execute in parallel → review when ready) is what produces the actual throughput gain. All code remains on the user's infrastructure.[^52][^1]

***

## Case Studies

### ElizaOS: Open-Source Agent OS with Cryptographic Verifiability

ElizaOS is a TypeScript-based multi-agent framework with ~17,000 GitHub stars and hundreds of weekly active developers. Its architectural innovation for decentralized deployment is the **Worlds + Rooms** model: each agent maintains context isolation within a Room while the World (workspace) enables cross-agent delegation, consensus, and load-balancing. With 200+ plugins spanning Web2 and Web3, agents can operate across Discord, Telegram, on-chain DeFi protocols, and custom APIs using the same character system.[^53][^54][^55][^56][^57]

The most significant infrastructure advance was the integration of **EigenCloud's Trusted Execution Environment (TEE)** for cryptographically verifiable agent execution. This gave ElizaOS verifiable execution proofs — cryptographic attestations that the agent running is exactly the one that was deployed, unmodified and securely isolated — without the engineering team needing to build custom attestation infrastructure. The architecture enables each agent step to be independently audited and composed into multi-agent proofs. This addresses the trust problem for open-source agents: rather than trusting an agent's behavior by reputation, you verify it cryptographically.[^57]

### Fetch.ai: Decentralized Agent Economy

Fetch.ai implements a full-stack decentralized agent platform on a Layer-1 Cosmos SDK blockchain. The three-component architecture — agents (autonomous task executors), Agentverse (cloud deployment/registry), and AI Engine (translates human goals into multi-agent workflows) — enables agents to dynamically discover, negotiate, and transact without centralized coordination. The **CoLearn protocol** enables collective learning between agents: models trained by different agents can be shared and improved collaboratively. A demonstrated logistics use case showed agents dynamically discovering and negotiating with counterparties through verifiable on-chain identity.[^58][^59]

Limitations: the Cosmos SDK foundation provides strong consensus but introduces economic token mechanics (FET) that couple technical infrastructure to speculative market dynamics. Production deployments remain primarily in Web3 contexts rather than general-purpose software development.

### AgentNet (NeurIPS 2025): Research-Grade Decentralized Coordination

AgentNet demonstrated that fully decentralized LLM-based agents can achieve task accuracy exceeding centralized baselines through dynamic DAG topology and RAG-based specialization. The privacy guarantee — minimal data exchange, agents leverage diverse knowledge without sharing raw model weights or training data — makes cross-organizational deployment feasible in ways that CTDE systems are not. AgentNet++ scaled this to 1,000+ agents with formal convergence and differential privacy proofs. These are currently research results; production deployment tooling does not yet exist.[^8][^9][^6]

### MARLEM: Emergent Coordination Without Explicit Communication

The MARLEM framework achieved emergent coordination in decentralized energy markets by enriching individual agent observations and rewards with system-level Key Performance Indicators, enabling agents to independently learn strategies that benefit the entire system without explicit inter-agent messaging. This is architecturally significant: it demonstrates that **value alignment can be embedded in the reward signal** rather than requiring a central enforcer, making it directly relevant to open-source agent networks where explicit communication may be expensive or unsafe.[^60]

***

## Remaining Unsolved Problems and Legitimate Limitations

### The Coordination Paradox in Fully Decentralized Systems

The empirical gap between CTDE and fully decentralized approaches — measured at 26 reward points in cooperative navigation — is not an implementation artifact. It reflects structural mathematical properties of decentralized optimization: agents optimizing local objectives cannot guarantee convergence to global optima without some form of coordination information that either requires centralization or adds communication overhead. AgentNet++ narrows this gap via hierarchical clustering, but the fundamental tension remains.[^9][^3]

### Credit Assignment Remains Open

Despite LLM-MCA and ME-IGM, credit assignment in open environments with dynamic agent populations lacks a general solution. When agents enter and leave a system, the causal contribution of any agent's historical actions to current outcomes cannot be cleanly attributed — and naive methods produce credit misattribution, evidenced by unstable loss functions and significant performance degradation. This is the deepest algorithmic problem for fully automated, evolving agent collectives.[^14][^15][^5]

### Orchestration Semantics Are the Hardest Engineering Problem

Empirical analysis of developer difficulties across Stack Overflow and GitHub found that the topics developers find hardest — longer to resolve, more often unanswered — are **RAG engineering**, **orchestration and execution control**, and **policy and template enforcement friction**. These are not model limitations; they are engineering problems in the coordination layer. The orchestration semantics problem (who calls what, when, with what authority, in what order) is harder than building individual agents and currently lacks good tooling for declarative specification in decentralized contexts.[^61]

### Security in Agent Supply Chains

The discovery of 1,184 malicious skills on ClawHub crystallized a systemic risk: open plugin/skill ecosystems are susceptible to supply chain attacks analogous to npm package poisoning. For decentralized systems where no central authority audits plugins, this risk is structurally harder to mitigate. Tool prompt injection — where a malicious MCP server returns adversarial instructions embedded in tool responses — is an attack surface with no current systematic defense.[^62][^40]

### Value Alignment Cannot Be Solved Purely Technically

A 2025 systematic review concludes that all three current alignment approaches — crowdsourcing, RLHF, and constitutional AI — fail to accommodate reasonable moral disagreement. Outputs from these systems are neither epistemically justified nor politically legitimate from the perspective of those who reasonably disagree. This is not a gap that decentralization solves — decentralized governance with DAO voting can democratize the process but still produces preference aggregations that disadvantage minorities unless carefully designed (as quadratic voting partly addresses). The "full-stack alignment" thesis requires aligning not just the AI but the institutions that govern it.[^25][^63][^64]

### Infrastructure Maturity Gaps

- **Holochain** deliberately limited 2025 development to stability and reliability — it is not yet a production-hardened platform for arbitrary hApp deployment at scale. Ecosystem adoption remains narrow.[^27][^21]
- **IPFS** is unsuitable for dynamic agent pipelines requiring low-latency state; it is a cold-storage and artifact-archival layer.[^31]
- **AD4M** is actively deployed in small communities but has not been stress-tested at the agent population scales required for full FLOSS infrastructure.[^28]
- **MCP and A2A** standardize the protocol but still require robust semantic negotiation mechanisms and data security solutions that do not yet exist.[^35]

### The KnowledgeOps Gap

A 2025–2026 practitioner assessment identified a systematic neglect: the industry has invested heavily in AgentOps (monitoring, cost tracking, token optimization) but not in **KnowledgeOps** or **SkillOps** — ensuring agents have verified, current, domain-correct knowledge and skills before executing workflows. This produces systems that execute confidently but incorrectly, which is arguably more dangerous than systems that fail visibly. For decentralized open-source infrastructure specifically, there is no current equivalent of a "knowledge supply chain" analogous to the software package supply chain.[^65]

### Pre-Assigned Role Architectures Are an Anti-Pattern

A large-scale empirical study (25,000 tasks, reported April 2026) found that pre-assigned agent roles — the architectural assumption underlying frameworks like CrewAI and many others — produce systematically worse outcomes than dynamic role emergence. The finding "demolished the foundational assumption of every major framework." Dynamic DAG approaches like AgentNet address this, but the majority of production tooling has not yet incorporated the lesson.[^66]

***

## Engineering Implications for Decentralized Open-Source AI

### What Is Actionable Now

1. **Use Holochain + AD4M as the trust foundation** for agent identity and source-of-truth validation rules. Accept that ecosystem maturity requires tooling investment.
2. **Use AgentNet++ or HRCL for coordination logic** where fully decentralized execution is required. Budget for the coordination paradox gap with hierarchical clustering as mitigation.
3. **Use Tendermint/CometBFT for consensus where global agreement is necessary** (governance votes, audit logs, token transactions). Separate consensus from application logic via ABCI.
4. **Use IPFS for artifact storage and capability advertisement** (agent specs, model checkpoints, audit records). Not for live state.
5. **Use MCP as the tool-calling interoperability layer**, with explicit adversarial modeling of tool responses and sandboxed execution environments.
6. **Adopt Multica or equivalent** for multi-agent CI/CD coordination, with supervisor agents and mandatory expanded test coverage for AI-generated code.
7. **Implement codified context infrastructure** (constitution + domain expert agents + cold-memory spec documents) to maintain session coherence.
8. **Embed system-level KPIs in individual agent reward signals** (MARLEM pattern) for emergent alignment without explicit policing.

### What Requires Genuine Research

- Credit assignment in open agent populations with dynamic membership
- Safe ADAS (automated design of agentic systems) — meta-agents designing agents without alignment guarantees
- Semantic negotiation standards for heterogeneous agent interoperability
- Knowledge supply chain verification — ensuring agent knowledge is correct before high-stakes execution
- Decentralized governance mechanisms that accommodate reasonable value pluralism rather than flattening it via majority preference aggregation

---

## References

1. [the open-source platform that manages AI agents like teammates](https://www.arunbaby.com/ai-agents/0089-multica-agents-as-teammates/) - Multica turns isolated AI coding agents into coordinated teammates with task assignment, skill compo...

2. [PANAMA: A Network-Aware MARL Framework for Multi-Agent Path Finding in Digital Twin Ecosystems](https://arxiv.org/abs/2508.06767) - Digital Twins (DTs) are transforming industries through advanced data processing and analysis, posit...

3. [On the Fundamental Limitations of Decentralized Learnable Reward Shaping in Cooperative Multi-Agent Reinforcement Learning](https://arxiv.org/abs/2511.00034) - Recent advances in learnable reward shaping have shown promise in single-agent reinforcement learnin...

4. [A Semi Centralized Training Decentralized Execution Architecture for Multi Agent Deep Reinforcement Learning in Traffic Signal Control](https://www.semanticscholar.org/paper/f74b9eca805ab2138d1560970c1fd5375722bc7e) - Multi-agent reinforcement learning (MARL) has emerged as a promising paradigm for adaptive traffic s...

5. [Challenges in Credit Assignment for Multi-Agent Reinforcement ...](https://arxiv.org/abs/2510.27659) - This report provides a conceptual and empirical review, focusing on the interplay between openness a...

6. [AgentNet: Decentralized Evolutionary Coordination for LLM-based Multi-Agent Systems](https://arxiv.org/abs/2504.00587) - The rapid advancement of large language models (LLMs) has enabled the development of multi-agent sys...

7. [GitHub - zoe-yyx/AgentNet: [NIPS2025] A decentralized, RAG ...](https://github.com/zoe-yyx/AgentNet) - It addresses the limitations of traditional MAS architectures that rely on centralized controllers a...

8. [[PDF] agentnet: decentralized evolutionary coordination - arXiv](https://arxiv.org/pdf/2504.00587.pdf) - In conclusion, AgentNet provides an effective approach to addressing the limitations of traditional ...

9. [Hierarchical Decentralized Multi-Agent Coordination with Privacy-Preserving Knowledge Sharing: Extending AgentNet for Scalable Autonomous Systems](https://arxiv.org/abs/2512.00614) - Decentralized multi-agent systems have shown promise in enabling autonomous collaboration among LLM-...

10. [10 Multi-Agent Coordination Strategies to Prevent System Failures](https://galileo.ai/blog/multi-agent-coordination-strategies) - Multi-agent coordination refers to the systematic management of multiple autonomous AI agents workin...

11. [LLM-Co Framework: Multi-Agent Coordination - Emergent Mind](https://www.emergentmind.com/topics/llm-coordinated-framework-llm-co) - LLM-Co is a multi-agent framework that orchestrates multiple language models via centralized and dec...

12. [Strategic Coordination for Evolving Multi-agent Systems: A Hierarchical Reinforcement and Collective Learning Approach](https://arxiv.org/abs/2509.18088) - Decentralized combinatorial optimization in evolving multi-agent systems poses significant challenge...

13. [aamas llm-mca - ICON Lab](http://iconlab.negarmehr.com/LLM-MCA/) - This "credit assignment" problem has been extensively studied in the Multi-Agent Reinforcement Learn...

14. [[PDF] Leveraging Large Language Models for Effective and Explainable ...](https://www.ifaamas.org/Proceedings/aamas2025/pdfs/p1501.pdf) - 2025. Leveraging Large Lan- guage Models for Effective and Explainable Multi-Agent Credit Assignment...

15. [[PDF] Towards Efficient Multi-Agent and Temporal Credit Assignment in ...](https://www.ri.cmu.edu/app/uploads/2025/07/cmu_msr_thesis.pdf) - To address this, the thesis introduces two innovative approaches: one for multi-agent collaboration ...

16. [Distributed Consensus Algorithms: Raft vs PBFT vs HotStuf...](https://anshadameenza.com/blog/technology/2025-01-08-distributed-consensus-algorithms-raft-pbft-hotstuff/) - Deep technical analysis of consensus mechanisms in production systems, covering Raft in etcd, PBFT i...

17. [6 Blockchain Consensus Mechanisms Compared: Which One Fits ...](https://chainlaunch.dev/blog/blockchain-consensus-mechanisms-compared) - 1. How Does Raft Consensus Work? · 2. What Is QBFT and When Should You Use It? · 3. How Does Practic...

18. [Consensus Algorithms in Distributed System - GeeksforGeeks](https://www.geeksforgeeks.org/operating-systems/consensus-algorithms-in-distributed-system/) - Tendermint: A BFT consensus algorithm designed for blockchain networks, combining fast finality with...

19. [What Is Tendermint? Guide to BFT Consensus & PoS - Nansen](https://www.nansen.ai/post/what-is-tendermint) - Tendermint is a foundational blockchain technology that enables fast, secure, and energy-efficient c...

20. [[PDF] Holochain: Scalable Agent-centric Distributed Computing](https://www.holochain.org/documents/holochain-white-paper-alpha.pdf) - In broad strokes: a Holochain application consists of a network of agents maintaining a unique sourc...

21. [Can Holochain Disrupt Traditional Blockchain Infrastructure? Agent ...](https://www.ainvest.com/news/holochain-disrupt-traditional-blockchain-infrastructure-agent-centric-architecture-scalability-2025-2511/) - - Holochain proposes agent-centric blockchain architecture to address scalability challenges through...

22. [Holochain: an agent-centric framework for distributed apps](https://ethresear.ch/t/holochain-an-agent-centric-framework-for-distributed-apps/5153) - We ARE building a platform for the decentralized evolution, deployment, and operation of many curren...

23. [Decentralized Governance of AI Agents - arXiv](https://arxiv.org/html/2412.17114v3) - This innovative framework offers a scalable and inclusive strategy for regulating AI agents, balanci...

24. [DAO Governance and AI - StableLab](https://stablelab.xyz/blog/dao-governance-and-ai) - Blockchain technology has not only disrupted finance but also governance, giving birth to DAOs that ...

25. [Democratic governance through DAO-based deliberation and voting ...](https://www.nature.com/articles/s41598-026-40180-8) - We developed a democratic decision framework utilizing Decentralized Autonomous Organization (DAO) t...

26. [{Dev Bytes}: Jun 6, 2025 | Blog - Holo Host](https://holo.host/blog/dev-bytes-jun-6-2025-35o8nFaDHQL/) - Migrating Humm hApp from Legacy to Production. The Humm hApp has successfully migrated and is now ru...

27. [2025 at a Glance: Landing Reliability - Holochain Blog](https://blog.holochain.org/2025-at-a-glance-landing-reliability/) - We made a deliberate choice this year to limit Holochain to features known to be stable and to fix k...

28. [AD4M Docs: Introduction](https://docs.ad4m.dev) - AD4M, as an agent-centric spanning layer married with an app development framework, redefines how de...

29. [Adam - Coasys - A Digital Nervous System for the Wise Web](https://coasys.org/adam) - At its core, the ADAM Layer is a meta-ontology defining 3 classes: Agents, Languages and Perspective...

30. [scryer-prolog - crates.io: Rust Package Registry](https://crates.io/crates/scryer-prolog) - semantic reasoning and queries in AD4M, an agent-centric distributed application meta-ontology. ... ...

31. [Decentralized Storage for AI Agents: IPFS & More | Fastio](https://fast.io/resources/decentralized-storage-ai-agents/) - IPFS (InterPlanetary File System) provides decentralized storage using content-addressed hashing, wh...

32. [Leveraging IPFS for Reliable and Efficient AI Applications - Filebase](https://filebase.com/blog/leveraging-ipfs-for-reliable-and-efficient-ai-applications/) - Discover how IPFS enhances AI applications by providing decentralized, reliable, and efficient data ...

33. [Evolution of AI Agent Registry Solutions: Centralized, Enterprise ...](https://arxiv.org/html/2508.03095v2) - AGNTCY Agent Directory Service (ADS): A content-addressed, OCI-aligned directory that resolves seman...

34. [How IPFS works - IPFS Docs](https://docs.ipfs.tech/concepts/how-ipfs-works/) - IPFS represents data as content-addressed blocks, and operates on those data blocks using the follow...

35. [Multi-Agent AI Systems: Definition, Benefits, Limitations & How to Build](https://www.getdynamiq.ai/post/multi-agent-ai-systems-definition-benefits-limitations-how-to-build) - Coordination Problems. Without clear coordination, agents can duplicate work, wait for resources ind...

36. [Specification - Model Context Protocol](https://modelcontextprotocol.io/specification/2025-06-18) - Model Context Protocol (MCP) is an open protocol that enables seamless integration between LLM appli...

37. [Guide to AI Agent Protocols: MCP, A2A, ACP & More - GetStream.io](https://getstream.io/blog/ai-agent-protocols/) - The Model Context Protocol (MCP) provides a standardized way for agents to access external resources...

38. [7 Things to Know About MCP (Model Context Protocol) in 2025](https://www.adskate.com/blogs/mcp-model-context-protocol-2025-guide) - The Model Context Protocol is an open standard defining how models, tools, and systems communicate a...

39. [Introducing the Model Context Protocol - Anthropic](https://www.anthropic.com/news/model-context-protocol) - The Model Context Protocol is an open standard that enables developers to build secure, two-way conn...

40. [AI Agent Orchestration in 2026: OpenClaw, MCP, and the Security ...](https://codewheel.ai/blog/ai-agent-orchestration-openclaw-mcp-landscape/) - The LLM interaction pattern is a solved problem. The unsolved problems are state management, securit...

41. [AI-Driven Automation of Code Review Processes: Enhancing Software Quality and Reducing Human Error](https://ulopenaccess.com/papers/ULIRS_V02I02/ULIRS20250202_006.pdf) - In contemporary software engineering, expert code review practices have entered a phase of profound ...

42. [AI agents speed up coding, but slow CI pipelines create a validation ...](https://www.facebook.com/thenewstack/posts/ai-agents-speed-up-coding-but-slow-ci-pipelines-create-a-validation-bottleneck-d/1827511742014345/) - AI agents speed up coding, but slow CI pipelines create a validation bottleneck. Discover how Kubern...

43. [Redesigning CI/CD for Multi-Agent Workflows in 2025](https://logiciel.io/blog/redesign-ci-cd-multi-agent-workflows) - Learn how to adapt CI/CD pipelines for multi-agent workflows. Explore architecture patterns, risks, ...

44. [CI/CD pipelines with agentic AI: How to create self ... - Elastic](https://www.elastic.co/search-labs/blog/ci-pipelines-claude-ai-agent) - How our team introduced GenAI into CI pipelines to create self-correcting pull requests, automizing ...

45. [AI agents transform DevOps and CI/CD by 2025 - Bittnet Training](https://www.bittnet.ro/en/noutati/agentii-ai-transforma-devops-si-ci-cd-pana-in-2025/) - The role of AI agents in CI/CD · 1. Automate delivery pipelines · 2. Improved continuous testing · 3...

46. [Automated Design of Agentic Systems](https://arxiv.org/pdf/2408.08435.pdf) - ...agentic system designs, including inventing novel building
blocks and/or combining them in new wa...

47. [ADAS - Shengran Hu](https://www.shengranhu.com/ADAS/) - We present a simple yet effective ADAS algorithm named Meta Agent Search to demonstrate that agents ...

48. [[PDF] Automated Design of Agentic Systems (ADAS)](https://iclr.cc/media/iclr-2025/Slides/28073.pdf) - Future Work. • Safety in ADAS. • ADAS: towards automated design of agentic systems. • From hand-craf...

49. [[2408.08435] Automated Design of Agentic Systems - arXiv](https://arxiv.org/abs/2408.08435) - We describe a newly forming research area, Automated Design of Agentic Systems (ADAS), which aims to...

50. [Codified Context: Infrastructure for AI Agents in a Complex Codebase](https://arxiv.org/abs/2602.20478) - LLM-based agentic coding assistants lack persistent memory: they lose coherence across sessions, for...

51. [GitHub - multica-ai/multica: The open-source managed agents ...](https://github.com/multica-ai/multica) - The open-source managed agents platform. Turn coding agents into real teammates — assign tasks, trac...

52. [Multica: Turn AI Agents Into Real Teammates on Your Board](https://www.youtube.com/watch?v=dPawyuq_ZFY) - Multica is an open-source platform that turns coding agents into functional team members ... OpenSou...

53. [What Is elizaOS (ELIZAOS)? Guide to AI Agent Revolution on Phemex](https://phemex.com/academy/what-is-elizaos-guide-ai-agent-revolution) - elizaOS is an open-source framework enabling developers to build and deploy autonomous AI agents for...

54. [ElizaOS](https://www.elizaos.ai) - Your Agentic Operating System. Build, orchestrate, and collaborate with AI agents. Get Started. Hero...

55. [ElizaOS Multichain Agent | Rather Labs](https://www.ratherlabs.com/blog/elizaos-multichain-agent) - ElizaOS emerges as a cutting-edge multi-agent simulation framework, designed to create, deploy, and ...

56. [elizaOS/eliza: Autonomous agents for everyone - GitHub](https://github.com/elizaos/eliza) - Multi-Agent Architecture: Designed from the ground up for creating and orchestrating groups of speci...

57. [How elizaOS Built Cryptographically Verifiable Agents Without ...](https://blog.eigencloud.xyz/how-elizaos-built-cryptographically-verifiable-agents/) - This case study explores how they solved the verification problem using EigenCloud's infrastructure....

58. [Fetch.ai: An Architecture for Modern Multi-Agent Systems - arXiv](https://arxiv.org/abs/2510.18699) - We demonstrate the deployed nature of this system through a decentralized logistics use case where a...

59. [What is Fetch.ai (FET)? Exploring decentralized AI agents - OKX](https://www.okx.com/learn/what-is-fetch) - Fetch.ai is a decentralized platform for building, deploying, and monetizing artificial intelligence...

60. [MARLEM: A Multi-Agent Reinforcement Learning Simulation Framework for Implicit Cooperation in Decentralized Local Energy Markets](https://linkinghub.elsevier.com/retrieve/pii/S0306261926001984) - This paper introduces a novel, open-source MARL simulation framework for studying implicit cooperati...

61. [What Challenges Do Developers Face in AI Agent Systems? An ...](https://arxiv.org/html/2510.25423v2) - The topics developers find most challenging are RAG Engineering, Document Embeddings & Vector Stores...

62. [AI Agents in Cryptoland: Practical Attacks and No Silver Bullet](http://arxiv.org/pdf/2503.16248.pdf) - The integration of AI agents with Web3 ecosystems harnesses their
complementary potential for autono...

63. [Moral disagreement and the limits of AI value alignment - PMC - NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC12628449/) - In this paper, we consider three current approaches to value alignment: crowdsourcing, reinforcement...

64. [I talked with Joe Edelman about the ideas in the Meaning Alignment ...](https://www.facebook.com/groups/gamebcore/posts/4231538187076209/) - What is the importance of value alignment in AI development? —Value alignment is crucial to mitigate...

65. [The Unglamorous Reality of AI in 2026: Lessons from Five Years in ...](https://www.linkedin.com/pulse/unglamorous-reality-ai-2026-lessons-from-five-years-trenches-gorai-fcgdf) - We're building AI agents when we should be building Applications with AI, Automation, and AI agents ...

66. [Your Multi-Agent Framework Is an Anti-Pattern ... - AI Advances](https://ai.gopubby.com/your-multi-agent-framework-is-an-anti-pattern-25-000-tasks-prove-that-pre-assigned-roles-make-ai-e6ea31736ebd) - The largest coordination experiment in multi-agent AI history just demolished the foundational assum...

