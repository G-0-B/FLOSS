<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Decentralized AI Projects and Research: A Comprehensive Overview

Based on extensive research, I've identified numerous decentralized AI projects and research efforts that align with your vision of peer-to-peer collaborative verifiable knowledge stores for global use. Here's a comprehensive analysis of the current landscape:

## Core Decentralized AI Frameworks

### **Federated Learning Platforms**

**OpenFL**  is a Linux Foundation project that provides a Python-based framework for federated learning, allowing organizations to train ML models on sensitive data without sharing it. It has been successfully deployed in one of the world's largest healthcare federations across 71 sites on 6 continents.[^1]

**Flower**  emerged as the top-performing open-source federated learning framework, scoring 84.75% in comprehensive evaluations. It's highly customizable and framework-agnostic, supporting PyTorch, TensorFlow, and other ML libraries.[^2]

**PySyft**  by OpenMined enables privacy-preserving machine learning through federated learning, secure multi-party computation, and differential privacy. It extends PyTorch and TensorFlow to enable secure, decentralized model training.[^3][^4]

**FedML**  provides a unified platform for federated learning with support for simulation, cross-silo, and cross-device scenarios. It's backed by TensorOpera AI and offers both open-source libraries and commercial MLOps platforms.[^5][^6]

**TensorFlow Federated (TFF)**  by Google provides both Federated Core (FC) API for distributed computations and Federated Learning (FL) API for high-level model training.[^7]

### **Decentralized AI Networks**

**Bittensor**  operates as a decentralized AI network using TAO tokens to incentivize AI model development across specialized subnets. It employs Yuma Consensus to evaluate AI contributions, with over 64 active subnets focusing on different AI tasks.[^8][^9][^10][^11]

**BeeAI**  is the first open-source agent-to-agent platform powered by the Agent Communication Protocol (ACP), enabling developers to build, discover, and compose AI agents across different frameworks.[^12]

**Cortex**  provides a public blockchain supporting on-chain AI model execution within smart contracts, bringing AI functionality to decentralized applications.[^13]

## Peer-to-Peer Data and Knowledge Sharing

### **Blockchain-Based Knowledge Systems**

**OriginTrail's Decentralized Knowledge Graph (DKG)**  creates verifiable, ownable Knowledge Assets using blockchain and cryptographic proofs. Each Knowledge Asset is an NFT containing structured knowledge that can be referenced via Uniform Asset Locators (UALs).[^14]

**Ocean Protocol**  tokenizes datasets and data services, creating a decentralized marketplace where data providers can monetize their data through datatokens while consumers access diverse datasets for AI training.[^15][^16]

### **Distributed Storage for AI**

**IPFS (InterPlanetary File System)** integration with AI shows significant promise. IPFS provides content-addressed storage where data is identified by unique content identifiers (CIDs), enabling deduplication, versioning, and distributed access. Research shows IPFS can save up to 60% bandwidth for video content and provides strong security through immutable resources.[^17][^18]

**Swarm (Ethereum)**  offers decentralized storage and content distribution with persistent storage incentives and the SWAP protocol for bandwidth sharing. It operates as a distributed immutable store of chunks (DISC) using Kademlia topology.[^19][^20]

**Codex**  acts as a decentralized durability engine, creating distributed archives of durable knowledge through peer-to-peer networks, offering cost-efficient and immutable data storage.[^21]

### **P2P Protocols and Networks**

**Hypercore Protocol**  provides distributed data structures including Hyperdrives for file archives and Hyperbees for key/value databases. Built on append-only logs, it offers versioning and cryptographic verification.[^22][^23]

**Dat Protocol**  enables peer-to-peer hypermedia sharing with public-key addressing, signed updates, and versioning capabilities. It's particularly useful for sharing and archiving large datasets.[^24][^25]

**WebTorrent**  brings BitTorrent functionality to web browsers using WebRTC, enabling direct peer-to-peer file sharing without plugins or extensions.[^26][^27]

## Verifiable Computation and Privacy

### **Privacy-Preserving Computation**

**Nillion**  represents a breakthrough in "blind computation," allowing secure processing of encrypted data without decryption. It uses multi-party computation (MPC) and homomorphic encryption to enable privacy-preserving AI inference and data analytics.[^28][^29][^30]

**Holochain**  provides an agent-centric framework for peer-to-peer applications, offering an alternative to blockchain for distributed systems. Recent collaborations with Immu.ai focus on Digital Product Passports using Green Proof of Work.[^31][^32]

### **Decentralized Compute Infrastructure**

**Akash Network**  creates a decentralized cloud computing marketplace where users can rent idle GPU and CPU resources for AI workloads. It offers up to 90% cost reductions compared to traditional cloud providers and recently integrated NVIDIA Blackwell GPUs.[^33][^34][^35]

**Bacalhau**  provides compute-over-data capabilities, allowing processing where data is stored rather than moving data to compute resources. It supports Docker containers and WebAssembly for distributed computation.[^36][^37]

## Emerging Research Areas

### **Compute-Over-Data Protocols**

The compute-over-data paradigm  enables processing near data storage locations, reducing bandwidth requirements and improving privacy. Projects like Bacalhau and Lilypad are building on protocols like Filecoin to enable truly decentralized computation.[^38][^39][^36]

### **Collaborative AI Development**

**Petals**  enables distributed running of large language models like LLaMA-405B using BitTorrent-style networking, allowing users to contribute GPU resources for collaborative model serving.[^40]

**LlamaTor**  specifically focuses on decentralized AI model distribution via BitTorrent, creating and sharing torrent files for AI models to reduce dependence on centralized distribution.[^41]

### **P2P AI Model Sharing**

Research shows various approaches to AI model sharing via P2P networks, including torrent-based distribution  and blockchain-based incentive mechanisms for model contributions.[^42][^43][^44]

## Key Technical Components

### **Verifiable Knowledge Stores**

- **Content-addressed storage** (IPFS, Swarm) ensures data integrity through cryptographic hashing
- **Blockchain-anchored proofs** (OriginTrail DKG) provide verifiability and provenance
- **Distributed hash tables** enable efficient peer discovery and content routing


### **Federated AI Architectures**

- **Cross-silo federated learning** for organization-to-organization collaboration
- **Cross-device federated learning** for edge devices and smartphones
- **Hierarchical structures** combining multiple federation levels


### **Privacy-Preserving Technologies**

- **Secure multi-party computation (MPC)** for joint computation without data sharing
- **Homomorphic encryption** enabling computation on encrypted data
- **Differential privacy** adding calibrated noise to protect individual privacy


## Open Source Availability

Most identified projects are open source, including:

- All major federated learning frameworks (OpenFL, Flower, PySyft, FedML)
- P2P protocols (IPFS, Hypercore, Dat, WebTorrent)
- Blockchain-based AI networks (Bittensor's core protocol)
- Decentralized storage systems (Swarm, Codex)


## Current Limitations and Opportunities

While substantial progress exists in decentralized AI, key challenges remain:

- **Scalability** of cryptographic operations in privacy-preserving systems
- **Incentive alignment** for sustainable peer-to-peer collaboration
- **Standardization** of protocols for interoperability
- **User experience** barriers for non-technical users

The landscape shows remarkable convergence toward your vision of decentralized, verifiable, collaborative AI systems. Projects like OriginTrail's DKG most closely match the concept of verifiable knowledge stores, while federated learning frameworks provide the collaborative training infrastructure, and P2P protocols enable the distributed networking foundation.

This ecosystem appears ripe for integration and standardization efforts that could create truly global, open, and verifiable knowledge-sharing networks for AI systems.
<span style="display:none">[^100][^101][^45][^46][^47][^48][^49][^50][^51][^52][^53][^54][^55][^56][^57][^58][^59][^60][^61][^62][^63][^64][^65][^66][^67][^68][^69][^70][^71][^72][^73][^74][^75][^76][^77][^78][^79][^80][^81][^82][^83][^84][^85][^86][^87][^88][^89][^90][^91][^92][^93][^94][^95][^96][^97][^98][^99]</span>

<div style="text-align: center">⁂</div>

[^1]: https://openfl.io

[^2]: https://link.springer.com/10.1007/s13042-024-02234-z

[^3]: https://www.nivalabs.ai/blogs/federated-learning-with-pysyft-privacy-preserving-ai-models

[^4]: https://zilliz.com/ai-faq/what-is-pysyft-and-how-does-it-relate-to-federated-learning

[^5]: https://github.com/FedML-AI/FedML

[^6]: https://fedml.ai

[^7]: https://github.com/w3c/federated-learning-cg

[^8]: https://www.osl.com/hk-en/academy/article/bittensor-explained-how-tao-and-subnets-power-decentralized-ai

[^9]: https://www.chaincatcher.com/en/article/2161622

[^10]: https://shannonlow.substack.com/p/bittensor-a-decentralised-ecosystem

[^11]: https://www.ainvest.com/news/bittensor-launches-decentralized-ai-network-tao-token-90-subnets-2508/

[^12]: https://lfaidata.foundation/blog/2025/04/29/ai-workflows-get-new-open-source-tools-to-advance-document-intelligence-data-quality-and-decentralized-ai-with-ibms-contribution-of-3-projects-to-linux-foundation-ai-and-data/

[^13]: https://onchain.org/magazine/top-web3-ai-projects/

[^14]: https://origintrail.io/documents/Verifiable_Internet_for_Artificial_Intelligence_whitepaper_v3_pre_publication.pdf

[^15]: https://www.gemini.com/cryptopedia/ocean-protocol-web-3-0-ocean-market-ocean-token

[^16]: https://www.diadata.org/web3-ai-map/ocean/

[^17]: https://filebase.com/blog/leveraging-ipfs-for-reliable-and-efficient-ai-applications/

[^18]: https://www.siliconmechanics.com/news/5-advantages-of-interplanetary-file-system?b

[^19]: https://mainframe-swarm-guide.readthedocs.io/en/latest/introduction.html

[^20]: https://www.gate.com/learn/articles/what-is-swarm-all-you-need-to-know-about-bzz/3385

[^21]: https://blog.codex.storage/revolutionising-ai-with-decentralised-storage/

[^22]: https://hypercore-protocol.github.io/new-website/

[^23]: https://docs.pears.com/building-blocks/hypercore

[^24]: https://www.datprotocol.com

[^25]: https://anarc.at/blog/2018-09-10-sharing-and-archiving-data-sets-with-dat/

[^26]: https://webtorrent.io/faq

[^27]: https://github.com/webtorrent/webtorrent

[^28]: https://nillion.com

[^29]: https://academy.binance.com/en/articles/what-is-nillion-nil

[^30]: https://docs.nillion.com/what-is-nillion

[^31]: https://www.accessnewswire.com/newsroom/en/blockchain-and-cryptocurrency/immu.ai-and-holochain-foundation-announce-collaboration-to-advance-dig-977389

[^32]: https://www.youtube.com/watch?v=AOyyn51VMg8

[^33]: https://coinmarketcap.com/cmc-ai/akash-network/what-is/

[^34]: https://www.gate.com/learn/articles/what-is-akash-network-introduction-to-the-decentralized-cloud-service-platform/8086

[^35]: https://www.diadata.org/web3-ai-map/akash/

[^36]: https://docs.ipfs.tech/concepts/cod/

[^37]: https://bacalhau.org

[^38]: https://docs.filecoin.io/basics/what-is-filecoin/programming-on-filecoin

[^39]: https://filecointldr.io/article/decentralized-compute-what-it-unlocks-and-why-it-matters-now/

[^40]: https://github.com/bigscience-workshop/petals

[^41]: https://github.com/Nondzu/LlamaTor

[^42]: https://pinata.cloud/blog/the-future-of-p2p-ai-how-crypto-middleware-is-revolutionizing-inference-payments/

[^43]: https://www.reddit.com/r/AI_torrents/comments/1krdpa0/useful_resources_for_ai_torrents_opensource_model/

[^44]: https://www.youtube.com/watch?v=oixcf0euy-w

[^45]: https://arxiv.org/abs/2506.11451

[^46]: https://ieeexplore.ieee.org/document/9027490/

[^47]: https://www.semanticscholar.org/paper/f4346b4884fd34deec5737c82538255434a8b5b8

[^48]: https://www.semanticscholar.org/paper/999af2547725000bce505b657222eb6d7360e0a1

[^49]: https://dl.acm.org/doi/10.1145/3412569.3412571

[^50]: https://arxiv.org/abs/2302.12125

[^51]: https://dl.acm.org/doi/10.1145/3178315.3178328

[^52]: https://www.semanticscholar.org/paper/c801f969f687f442253183afccbef5dd605d2fbf

[^53]: https://www.semanticscholar.org/paper/34e1faf5c4ac06bdca38fe10024dba8116ebba9f

[^54]: https://ieeexplore.ieee.org/document/8716232/

[^55]: https://arxiv.org/pdf/2111.04287.pdf

[^56]: https://arxiv.org/pdf/2210.16651.pdf

[^57]: https://arxiv.org/pdf/2412.14566.pdf

[^58]: https://arxiv.org/html/2501.05450v1

[^59]: https://arxiv.org/html/2502.11464v1

[^60]: https://arxiv.org/pdf/2411.03887v2.pdf

[^61]: https://arxiv.org/html/2404.08079v1

[^62]: http://arxiv.org/pdf/2407.02461.pdf

[^63]: https://arxiv.org/pdf/2107.05252.pdf

[^64]: https://arxiv.org/pdf/2304.08322.pdf

[^65]: https://github.com/KOSASIH/DecentralizedAI/

[^66]: https://www.tandfonline.com/doi/full/10.1080/14703297.2025.2530118?src=

[^67]: https://sherpa.ai/blog/federated-learning-ai/

[^68]: https://peer-ai.eu/en/

[^69]: https://milvus.io/ai-quick-reference/what-are-the-common-architectures-used-in-federated-learning-systems

[^70]: https://www.forbes.com/sites/digital-assets/2025/02/28/deepseeks-lesson-the-future-of-ai-is-decentralized-and-open-source/

[^71]: https://optimusai.ai/classroom-ai-powered-peer-peer-collaborative-learning/

[^72]: https://jklst.org/index.php/home/article/view/172

[^73]: https://arxiv.org/abs/2405.18072

[^74]: https://arxiv.org/abs/2505.15962

[^75]: https://dl.acm.org/doi/10.1145/3502181.3535102

[^76]: https://www.semanticscholar.org/paper/5d8b041cbdfeeb2f059750bbc3a2dd5b5554a093

[^77]: https://publikationen.bibliothek.kit.edu/1000135146

[^78]: https://ieeexplore.ieee.org/document/10617374/

[^79]: https://www.mdpi.com/1999-5903/13/2/48

[^80]: https://www.semanticscholar.org/paper/a633b0bf453ce2de596175449bc8a19b20955ef9

[^81]: https://www.semanticscholar.org/paper/bf8400ee0cfbeab03cb1b87ed319dc0ab2d083ea

[^82]: https://s-rsa.com/index.php/agi/article/view/15417

[^83]: http://arxiv.org/pdf/2410.09124.pdf

[^84]: https://arxiv.org/pdf/2503.22573.pdf

[^85]: https://arxiv.org/pdf/2503.15550.pdf

[^86]: https://arxiv.org/pdf/2205.01081.pdf

[^87]: http://arxiv.org/pdf/2407.19775v1.pdf

[^88]: https://arxiv.org/pdf/2404.12623.pdf

[^89]: https://arxiv.org/html/2504.04794v1

[^90]: https://pmc.ncbi.nlm.nih.gov/articles/PMC10805810/

[^91]: https://arxiv.org/pdf/2407.19401.pdf

[^92]: https://pmc.ncbi.nlm.nih.gov/articles/PMC9133021/

[^93]: https://www.parangat.com/the-synergy-of-blockchain-and-ai-how-the-two-work-together/

[^94]: https://cheqd.io/blog/verifiable-ai-by-cheqd/

[^95]: https://aws.amazon.com/startups/learn/blockchain-and-generative-ai-fueling-innovation-within-the-digital-economy?lang=en-US

[^96]: https://www.apheris.com/resources/blog/top-7-open-source-frameworks-for-federated-learning

[^97]: https://world.org/blog/engineering/zkml-ai-thats-verifiable-private-and-right-on-your-phone

[^98]: https://cointelegraph.com/news/blockchain-ai-de-ai

[^99]: https://onlinelibrary.wiley.com/doi/10.1111/exsy.13131

[^100]: https://arxiv.org/abs/2402.06682

[^101]: https://petsymposium.org/popets/2025/popets-2025-0141.php

