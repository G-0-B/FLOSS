# FOSS AI Personal Assistant Landscape: Validated Assessment for FLOSSIOULLK Compatibility

## Executive Summary

This report presents a fact-checked and corrected assessment of the Free/Libre Open Source AI personal assistant landscape as of March 2026, evaluated through the lens of FLOSSIOULLK (Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge) compatibility. The analysis validates claims from a prior landscape study, corrects factual errors, identifies five major blind-spot projects omitted from the original analysis, and provides updated FLOSSIOULLK compatibility tiering.

Key corrections include: OpenClaw's star count was severely stale (332k actual vs. 68k claimed); OVOS MCP/A2A support is planned but not yet implemented; n8n operates under a Sustainable Use License that does not qualify as open source by OSI standards; and Open WebUI adopted a custom BSD-3 license with branding restrictions that disqualify it from strict FOSS classification. Five major projects — Dify, OpenHands, Mem0, Jan, and AutoGPT — were entirely absent from the original landscape despite collectively representing over 475,000 GitHub stars.

---

## Tier 1: Highest FLOSSIOULLK Alignment

### OpenClaw — The Breakout Agent

**Corrected Star Count:** 332,221 stars (validated via GitHub API, March 23, 2026). The original landscape cited 68,000, which reflects the tool's state during its initial viral spike in late January 2026. By February 2026, the repository had [surpassed 100,000 stars](https://www.kdnuggets.com/openclaw-explained-the-free-ai-agent-tool-going-viral-already-in-2026), and a YouTube setup guide from March 12, 2026 referenced [over 140,000 stars](https://www.youtube.com/watch?v=R7VlQPmgIL4) at that time. The trajectory represents the fastest-growing open-source project in GitHub history according to [ByteByteGo](https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026).

| Attribute | Validated Status |
|-----------|-----------------|
| License | MIT (confirmed via GitHub API) |
| Stars | 332,221 (March 23, 2026) |
| MCP Support | Community-built bridge exists ([openclaw-mcp](https://github.com/freema/openclaw-mcp/blob/main/README.md)); full native MCP client support is a [tracked feature request](https://github.com/openclaw/openclaw/issues/13248) but not yet in stable release |
| Model-Agnostic | Confirmed — supports any LLM via API key (OpenAI, Anthropic, local models) |
| Local-First | Confirmed — runs as local gateway, data stays on-device ([DigitalOcean](https://www.digitalocean.com/resources/articles/what-is-openclaw)) |
| Self-Improving | Confirmed — writes its own AgentSkills, 100+ preconfigured skills ([KDnuggets](https://www.kdnuggets.com/openclaw-explained-the-free-ai-agent-tool-going-viral-already-in-2026)) |
| Messaging Integration | WhatsApp, Telegram, Slack, Discord, Signal, iMessage ([ByteByteGo](https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026)) |

**Critical Update — Governance Transition:** On February 14, 2026, creator Peter Steinberger announced he would be joining OpenAI, and the project would transition to an open-source foundation ([ByteByteGo](https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026)). This is a significant governance event. While the MIT license provides strong legal protection against relicensing of existing code, the community should monitor whether the foundation maintains neutrality or becomes subject to OpenAI influence. The Steinberger-to-OpenAI pipeline mirrors historical patterns (e.g., Karpathy to OpenAI, back to independent) that FLOSSIOULLK should track carefully.

**Security Concerns:** Security researchers have raised concerns about the broad permissions the agent requires to function, and the skill repository still lacks rigorous vetting for malicious submissions ([ByteByteGo](https://blog.bytebytego.com/p/top-ai-github-repositories-in-2026)). For FLOSSIOULLK's sovereignty-first posture, this is a tangible risk vector: a self-improving agent that can write and execute code needs a provenance layer that OpenClaw currently lacks.

**FLOSSIOULLK Assessment:** OpenClaw scores highest on practical utility today — the MIT license, local-first architecture, model agnosticism, and massive ecosystem make it the strongest "Plane A" tool. However, it has zero Holochain integration, no CRDT-based state management, and no agent-centric identity layer. The governance transition adds uncertainty. Rating: **Plane A leader, Plane B gap remains total.**

---

### OVOS / HiveMind — Voice-First Distributed Architecture

**Corrected Claims:**

| Attribute | Original Claim | Validated Status |
|-----------|---------------|-----------------|
| License (OVOS) | Apache-2.0 | Confirmed Apache-2.0 (GitHub API) |
| License (HiveMind) | AGPL-3.0 | Confirmed AGPL-3.0 (GitHub API) |
| Stars (ovos-core) | Not specified | 268 (modest, niche project) |
| Stars (HiveMind-core) | Not specified | 14 (very small community) |
| EU Deployment | Claimed | Confirmed — COALA and WASABI EU projects deploy [OVOS + HiveMind Docker stack](https://community.openconversational.ai/t/blog-ovos-hivemind-in-the-manufacturing-industry/22021) for industrial voice assistants |
| MCP Support | Implied as current | **CORRECTION: Planned but NOT implemented.** OVOS blog from October 2025 explicitly states MCP, UTCP, and A2A are ["being explored"](https://blog.openvoiceos.org/posts/2025-10-24-protocol_interoperability) with personas as future participants |
| A2A Support | Implied as current | **CORRECTION: Under development** in ovos-persona-server, not production-ready |

The EU deployment story is real and significant. The [WASABI project](https://community.openconversational.ai/t/blog-ovos-hivemind-in-the-manufacturing-industry/22021) requires all experiments to run the OVOS Docker stack with HiveMind connectivity, Keycloak authentication, and RASA NLP, forming a complete industrial voice-assistant framework. This validates OVOS's architectural maturity for regulated, edge-deployed environments.

HiveMind's hierarchical transport protocol is architecturally interesting for FLOSSIOULLK: it defines clear rules for message routing across distributed networks, which maps to the kind of topology Holochain DHTs would eventually manage. The OVOS messagebus protocol is being formalized with [Pydantic models](https://blog.openvoiceos.org/posts/2025-10-24-protocol_interoperability), creating a typed schema that could theoretically bridge to AD4M perspectives.

**FLOSSIOULLK Assessment:** OVOS/HiveMind is the only project in this landscape with a distributed, voice-first architecture designed for satellite nodes — conceptually closest to what a Holochain-backed assistant network would look like. The AGPL license on HiveMind enforces reciprocity. However, the tiny community (14 stars) and the gap between stated protocol ambitions and actual implementation make this a research bet, not a production stack. Rating: **Architecturally aligned for Plane B, but pre-production.**

---

### LocalAI — Sovereign Inference Layer

| Attribute | Validated Status |
|-----------|-----------------|
| License | MIT (confirmed via GitHub API) |
| Stars | 44,268 (March 23, 2026) |
| P2P Federation | Confirmed — [distributed inference via libp2p](https://localai.io/features/distribute/), both federated (load-balanced) and worker (model sharding) modes |
| MCP Support | Not explicitly confirmed as native; functions primarily as an OpenAI-compatible API server |
| Agent System | Not a personal assistant framework; provides the inference backend |

LocalAI's [P2P networking](https://localai.io/features/p2p/) is confirmed and uses a shared token for secure, private communication between nodes. The `--p2p --federated` flag creates clusters that eliminate complex network configuration. This is production-usable but still marked as ["tech preview"](https://localai.io/features/distribute/) in official documentation.

**FLOSSIOULLK Assessment:** LocalAI is infrastructure, not an assistant. It serves as the sovereign inference substrate beneath any FLOSSIOULLK-aligned personal AI stack. The P2P federation via libp2p is the most Holochain-adjacent networking pattern in this landscape — both use DHT-style peer discovery for decentralized coordination. MIT license maximizes composability. Rating: **Essential infrastructure layer, not a standalone assistant.**

---

### Khoj — Knowledge-First Personal AI

| Attribute | Validated Status |
|-----------|-----------------|
| License | AGPL-3.0 (confirmed via GitHub API) |
| Stars | 33,589 (March 23, 2026) |
| Y Combinator | Confirmed — [YC company page](https://www.ycombinator.com/companies/khoj) lists Khoj as an applied AI company |
| RAG | Confirmed — searches across personal documents and the web ([Khoj.dev](https://khoj.dev)) |
| Automations | Confirmed — cron-based agents for scheduled tasks, research digests ([Khoj.dev](https://khoj.dev)) |
| Self-Hosting | Confirmed — desktop app, full self-hosted option |
| Multi-Model | Confirmed — supports Anthropic, OpenAI, HuggingFace, and more ([AI Agents List](https://aiagentslist.com/agents/khoj)) |

The team built personal AI assistance at Microsoft scale (tens of millions of DAU) before founding Khoj ([Y Combinator](https://www.ycombinator.com/companies/khoj)). The AGPL-3.0 license provides the strongest copyleft protection in this landscape, ensuring modifications must be shared — a value strongly aligned with FLOSSIOULLK's reciprocity principles.

**FLOSSIOULLK Assessment:** Khoj is the most FLOSSIOULLK-aligned project on licensing alone (AGPL-3.0 enforces reciprocity). The knowledge-first architecture (search + chat over personal docs) maps well to AD4M's perspective model. YC backing provides runway but introduces VC incentive structures that could conflict with sovereignty-first values over time. Rating: **Strong Plane A candidate, license is exemplary.**

---

## Tier 2: Partial Alignment / Specialized Use

### PAI (Personal AI Infrastructure) — Daniel Miessler's Framework

| Attribute | Validated Status |
|-----------|-----------------|
| License | MIT (confirmed via GitHub API) |
| Stars | 10,419 (March 23, 2026) |
| Nature | Conceptual framework + automation scripts, not a standalone assistant |

PAI provides a philosophy and reference architecture for personal AI infrastructure rather than a deployable product. Useful for alignment thinking within FLOSSIOULLK but not a production tool.

### Leon AI — Voice Assistant Framework

| Attribute | Validated Status |
|-----------|-----------------|
| License | MIT (confirmed via GitHub API) |
| Stars | 17,081 (March 23, 2026) |
| Status | Active repository, server-based voice assistant with skills system |

Leon is a conversational assistant that runs on a server and responds to voice/text. MIT licensed and self-hostable, but lacks the agentic capabilities, model agnosticism, and distributed architecture that define the current generation of AI assistants.

### PicoClaw — Ultra-Lightweight Edge Assistant

| Attribute | Validated Status |
|-----------|-----------------|
| License | MIT (confirmed via GitHub API) |
| Stars | 25,911 (March 23, 2026) |
| Memory Footprint | Under 10 MB RAM, boots in under 1 second on 0.6 GHz cores ([Reddit](https://www.reddit.com/r/HasambaShared/comments/1r1pov9/headline_picoclaw_ultralight_go_ai_assistant/)) |
| Architecture | Single Go binary, cross-platform (RISC-V, ARM64, x86) |
| Hardware Target | Devices as low as $10 ([LinkedIn](https://www.linkedin.com/posts/gaurav-desurakar_github-sipeedpicoclaw-tiny-fast-and-activity-7429913649105780736-5K2r)) |
| Comparison | [99% less memory than OpenClaw](https://delante.co/picoclaw/) |

PicoClaw is a real project with substantial traction — not the "early-stage experiment" the original landscape implied. It evolved from earlier Python/TypeScript projects through an AI-driven refactor into a compact Go runtime. Messaging integrations include Telegram and Discord. Independent benchmark data remains unavailable, and support for heavy on-device ML inference is unclear.

**FLOSSIOULLK Assessment:** PicoClaw is the edge-deployment story. For a FLOSSIOULLK mesh where every node — including $10 RISC-V boards — participates in the assistant network, PicoClaw provides the extreme-lightweight runtime. Combined with LocalAI's P2P federation, this could power the IoT fringe of a Holochain-backed assistant constellation.

### OpenJarvis — Stanford Research Platform

| Attribute | Validated Status |
|-----------|-----------------|
| License | Apache-2.0 (confirmed via GitHub API) |
| Origin | Stanford Hazy Research / [Scaling Intelligence Lab](https://scalingintelligence.stanford.edu/blogs/openjarvis/) |
| Key Finding | Local models handle [88.7% of single-turn queries](https://scalingintelligence.stanford.edu/blogs/openjarvis/) at interactive latencies |
| Architecture | Five primitives: Intelligence, Engine, Agents, Tools & Memory, Learning |
| Engine Backends | 10+ (Ollama, vLLM, SGLang, llama.cpp, MLX, Exo, LiteLLM, cloud providers) |
| Efficiency Focus | Energy, FLOPs, latency, dollar cost tracked as [first-class evaluation targets](https://open-jarvis.github.io/OpenJarvis/) |
| Learning Loop | Improves models using local trace data |

OpenJarvis is the most research-rigorous project in this landscape. The "Intelligence Per Watt" study validates what local-first advocates have claimed anecdotally: local inference is ready for the vast majority of personal AI use cases. The learning loop — improving models from local trace data — is the closest any project comes to FLOSSIOULLK's vision of self-improving, sovereign AI that gets smarter from your own data.

**FLOSSIOULLK Assessment:** OpenJarvis provides the academic validation and efficiency framework that FLOSSIOULLK needs. The "local by default, cloud only when necessary" design philosophy is perfectly aligned. Apache-2.0 is permissive. The primary limitation is that it's a research platform, not a consumer product. Rating: **Research foundation for Plane B efficiency claims.**

---

## Tier 3: Adjacent Tools (Not Standalone Assistants)

### n8n — Workflow Automation (NOT Open Source)

| Attribute | Validated Status |
|-----------|-----------------|
| License | Sustainable Use License — **NOT OSI-approved open source** |
| Stars | 180,703 (March 23, 2026) |
| Self-Declaration | n8n's own documentation states: ["according to the Open Source Initiative (OSI), open source licenses can't include limitations on use, so we do not call ourselves open source"](https://docs.n8n.io/sustainable-use-license/) |

**Critical Correction:** The original landscape classified n8n among FOSS tools. This is incorrect. The [Sustainable Use License](https://docs.n8n.io/sustainable-use-license/) restricts commercial redistribution: you cannot white-label n8n, host it for money, or embed it in a commercial product without a paid enterprise agreement ([Scalevise](https://scalevise.com/resources/n8n-automation-license-commercial-use/)). While the source code is publicly available and free for internal business use, the license fails the OSI Open Source Definition and the FSF Four Freedoms test.

For FLOSSIOULLK purposes, n8n is a useful automation tool that can orchestrate workflows between FOSS components, but it cannot be part of the sovereign stack itself. Any FLOSSIOULLK deployment using n8n commercially would need to either pay for an enterprise license or replace it with a truly FOSS alternative.

### AnythingLLM — Local RAG Desktop App

| Attribute | Validated Status |
|-----------|-----------------|
| License | MIT ([confirmed on website](https://anythingllm.com) and GitHub) |
| Stars | 56,638 (March 23, 2026) |
| Key Feature | All-in-one desktop app: chat with documents, AI agents, vector DB — fully local and offline |
| Self-Hosting | Desktop app runs entirely locally by default; nothing shared unless explicitly allowed |

AnythingLLM is a genuine MIT-licensed tool that provides a solid local RAG interface. It supports any LLM, any document format, and includes agent capabilities. For FLOSSIOULLK, it serves as a potential RAG frontend that could feed into a broader sovereign AI stack.

### Open WebUI — Model Interface (License Complicated)

| Attribute | Validated Status |
|-----------|-----------------|
| License | Custom BSD-3 with branding restrictions (v0.6.6+, April 2025) — **not OSI-approved** |
| Stars | 128,406 (March 23, 2026) |
| Legacy License | v0.6.5 and earlier: pure BSD-3-Clause (no restrictions) |
| Branding Requirement | Must retain "Open WebUI" branding in all deployments of 50+ users, or obtain enterprise license |

**Correction:** The original landscape listed Open WebUI among open-source tools without qualification. Since [v0.6.6 (April 2025)](https://openwebui.com/license/), the license includes a branding protection clause that disqualifies it from OSI-approved open source status. Open WebUI's own FAQ [acknowledges](https://openwebui.com/license/) this: "our new branding clause means Open WebUI v0.6.6+ isn't OSI-certified 'open source.'" For deployments under 50 users, branding removal is permitted. Contributors and small teams are unaffected in practice.

The community has responded by creating MIT-licensed forks from [v0.6.5](https://www.reddit.com/r/LocalLLaMA/comments/1pozd2k/anyone_else_in_a_stable_wrapper_mitlicensed_fork/). For FLOSSIOULLK, the v0.6.5 BSD-3 codebase remains fully FOSS-compatible, but tracking the upstream project requires accepting the branding constraint or forking.

---

## Blind Spots: Major Projects Missing from Original Landscape

The original analysis omitted five major projects that collectively represent over 475,000 GitHub stars. This section corrects that gap.

### AutoGPT — Autonomous Agent Pioneer (182,700 stars)

| Attribute | Status |
|-----------|--------|
| Stars | 182,700+ (largest AI agent repo on GitHub) |
| License | Source-available (custom license with restrictions) |
| Creator | Significant Gravitas |
| Key Feature | Build, deploy, and run continuous AI agents that automate complex workflows |

AutoGPT pioneered the autonomous agent paradigm in 2023 and remains the most-starred AI agent project on GitHub ([GitHub](https://github.com/significant-gravitas/autogpt)). It provides a platform for creating agents with task chaining, memory management, and API integrations. The project offers both self-hosted and cloud-hosted options. While enormously influential, its license and heavy cloud dependency limit FLOSSIOULLK alignment.

### Dify — Agentic Workflow Platform (134,145 stars)

| Attribute | Status |
|-----------|--------|
| Stars | 134,145 (March 23, 2026) |
| License | Modified Apache 2.0 with additional restrictions — **not standard FOSS** |
| MCP Support | Confirmed — [native MCP integration](https://dify.ai) for both consuming and publishing MCP services |
| Key Feature | Visual workflow builder, RAG pipelines, multi-LLM orchestration, plugin marketplace |
| Concern | [isitreallyfoss.com](https://isitreallyfoss.com/projects/dify/) rates Dify as "Not FOSS" due to custom license restrictions |

Dify's MCP integration is notable: it can both consume external MCP services and [publish Dify-built workflows as standard MCP servers](https://dify.ai), creating bidirectional interoperability. The visual workflow builder and RAG pipeline support are production-grade. However, Dify operates under a modified Apache 2.0 license with [additional conditions](https://github.com/langgenius/dify/blob/main/LICENSE) that restrict certain uses, and the project has been criticized for [misleading use of "open source" terminology](https://isitreallyfoss.com/projects/dify/). Dify has raised at least $2.5M from investors including Alibaba Cloud.

**FLOSSIOULLK Assessment:** Dify provides the most complete visual agent-building experience in this landscape, and its MCP interop is the most mature. But the license restrictions and VC/Alibaba funding make it a tool to learn from, not a foundation to build on. Rating: **Useful reference architecture, license disqualifies for sovereign stack.**

### OpenHands — AI Development Agent (69,616 stars)

| Attribute | Status |
|-----------|--------|
| Stars | 69,616 (March 23, 2026) |
| License | NOASSERTION (requires manual verification) |
| Focus | AI-driven software development agent |

OpenHands (formerly OpenDevin) is an AI agent specialized in software development tasks — writing code, fixing bugs, and automating development workflows. While not a general-purpose personal assistant, it represents the developer-tool branch of the autonomous agent tree. Relevant to FLOSSIOULLK's broader agent ecosystem vision.

### Jan — Offline ChatGPT Alternative (41,211 stars)

| Attribute | Status |
|-----------|--------|
| Stars | 41,211 (March 23, 2026) |
| License | NOASSERTION (requires verification) |
| Key Feature | Desktop app for offline LLM interaction |

Jan provides a clean, offline-first ChatGPT alternative that runs entirely on the user's hardware. It aligns with the local-first principle but lacks the agentic capabilities, automation, or distributed architecture needed for full FLOSSIOULLK integration.

### Mem0 — Universal Memory Layer (50,833 stars)

| Attribute | Status |
|-----------|--------|
| Stars | 50,833 (March 23, 2026) |
| License | Apache-2.0 (confirmed via GitHub API) |
| Key Feature | Intelligent memory layer for AI agents — compresses chat history, preserves context, enables personalization |
| Integrations | Works with OpenAI, LangGraph, CrewAI, Python, JS ([Mem0.ai](https://mem0.ai)) |
| Compliance | SOC 2 and HIPAA compliant with BYOK |
| Performance | Claims [26% higher response quality with 90% fewer tokens](https://mem0.ai) vs. OpenAI memory |

Mem0 is the most FLOSSIOULLK-relevant blind spot. It provides exactly what a sovereignty-first agent mesh needs: a universal, self-improving memory layer that sits between the user and any AI agent. The Apache-2.0 license is permissive. The "memory as a service" pattern maps directly to AD4M's perspective model — each agent maintains its own memory perspective that can be shared or kept private based on the user's sovereignty rules. BYOK (Bring Your Own Key) and HIPAA compliance indicate enterprise-grade data handling.

**FLOSSIOULLK Assessment:** Mem0 should be elevated to Tier 1 consideration. A sovereign AI stack needs a memory layer that is independent of any single model or assistant. Mem0's architecture — Apache-2.0, model-agnostic, self-improving — fills the gap between OpenClaw's task execution and Khoj's knowledge retrieval. Rating: **Critical infrastructure for Plane A and Plane B.**

---

## Corrected FLOSSIOULLK Compatibility Matrix

| Project | Stars | License | FOSS? | MCP | Local-First | Distributed | Plane A | Plane B Potential |
|---------|-------|---------|-------|-----|------------|-------------|---------|-------------------|
| OpenClaw | 332,221 | MIT | Yes | Community bridge | Yes | No | Leader | Low |
| Khoj | 33,589 | AGPL-3.0 | Yes | No | Yes | No | Strong | Medium |
| LocalAI | 44,268 | MIT | Yes | No | Yes | Yes (P2P) | Infra | High |
| OVOS/HiveMind | 268/14 | Apache/AGPL | Yes | Planned | Yes | Yes | Niche | Highest |
| Mem0 | 50,833 | Apache-2.0 | Yes | No | Partial | No | Strong | Medium |
| AnythingLLM | 56,638 | MIT | Yes | No | Yes | No | Moderate | Low |
| OpenJarvis | N/A | Apache-2.0 | Yes | No | Yes | No | Research | High |
| PicoClaw | 25,911 | MIT | Yes | No | Yes | No | Edge | Medium |
| Leon AI | 17,081 | MIT | Yes | No | Yes | No | Limited | Low |
| PAI | 10,419 | MIT | Yes | No | Conceptual | No | Framework | Low |
| n8n | 180,703 | SUL | **No** | Yes | Self-host | No | Tool only | Disqualified |
| Open WebUI | 128,406 | Custom BSD | **No (v0.6.6+)** | No | Yes | No | Tool only | Fork viable |
| Dify | 134,145 | Modified Apache | **No** | Yes (native) | Self-host | No | Reference | Disqualified |
| AutoGPT | 182,700 | Custom | **No** | No | Partial | No | Reference | Disqualified |
| OpenHands | 69,616 | Unclear | TBD | No | Partial | No | Dev tool | TBD |
| Jan | 41,211 | Unclear | TBD | No | Yes | No | Limited | Low |

---

## The Plane A / Plane B Gap Analysis

No project in this landscape delivers what FLOSSIOULLK's "Plane B" ultimately requires:

- **Holochain-native provenance:** Zero projects use Holochain for agent identity, trust, or data provenance. Every project relies on either centralized identity (API keys, OAuth) or no identity at all.
- **CRDT-based state:** Only OVOS/HiveMind's messagebus approaches distributed state, and it uses websockets rather than CRDTs. LocalAI's P2P uses libp2p but for inference routing, not state synchronization.
- **AD4M semantic interop:** No project implements AD4M perspectives, languages, or neighbourhoods. The closest conceptual analog is Mem0's memory layer, which could theoretically be modeled as an AD4M perspective.
- **Agent-centric identity:** Every project uses device-centric or service-centric identity. None implement agent-centric identity where the agent (not the server, not the device) is the sovereign unit.

The practical path forward is a layered approach:

1. **Plane A (now):** OpenClaw for task execution + Khoj for knowledge + LocalAI for sovereign inference + Mem0 for memory + PicoClaw for edge nodes
2. **Bridge (near-term):** MCP as the interop protocol between these components, with OVOS/HiveMind patterns informing the distributed topology
3. **Plane B (future):** Holochain DHTs replacing centralized coordination, AD4M perspectives replacing siloed memory stores, agent-centric identity replacing API keys

The 88.7% local query handling rate validated by [OpenJarvis/Stanford](https://scalingintelligence.stanford.edu/blogs/openjarvis/) confirms that the inference layer is ready for sovereignty. The gap is in the trust, identity, and coordination layers — which is precisely where Holochain and AD4M operate.

---

## Methodology

All GitHub statistics were validated via the GitHub REST API (`gh api repos/{owner}/{repo}`) on March 23, 2026. License classifications follow OSI definitions; projects labeled "NOASSERTION" by GitHub were verified against their LICENSE files where possible. Web sources were cross-referenced across multiple outlets. Claims about feature support (MCP, P2P, etc.) were validated against official documentation and project blogs rather than third-party summaries. The FLOSSIOULLK compatibility assessment applies the framework's core principles: sovereignty-first, local-first, copyleft-preferred, agent-centric, and Holochain-aligned.
