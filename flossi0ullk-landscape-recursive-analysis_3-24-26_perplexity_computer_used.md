# FLOSSI0ULLK Recursive Landscape Document

A four-layer research report for the Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge — a decentralized, agent-centric intelligence commons using Holochain as trust foundation.

**Document date:** March 23, 2026
**Claim taxonomy:** Every factual claim is prefixed with one of five epistemic tiers: **[TESTED]**, **[VENDOR-CLAIMED]**, **[COMMUNITY-REPORTED]**, **[RESEARCH-ONLY]**, or **[SPECULATIVE]**.

---

## Layer 1: Red-Team of the Red-Team

A prior red-team critique identified errors in the original FLOSSI0ULLK landscape scan. This section verifies that critique against primary sources, reporting what the critique got right, what it got wrong, and a trinary disposition.

### What the Critique Got RIGHT

1. **OpenClaw/LocalAI star-count contamination**: CONFIRMED AND WORSE THAN STATED. The critique flagged "68,000+ stars" as misattributed from LocalAI to OpenClaw. Independent verification shows LocalAI has 44.3k stars ([GitHub](https://github.com/mudler/LocalAI)), not 68k. OpenClaw currently has 332k stars ([GitHub](https://github.com/openclaw/openclaw)). The original draft's 68k figure matches neither project. The 68k number appears to be OpenClaw's star count as of approximately January 2026, when [DigitalOcean reported "68,000+ GitHub stars"](https://www.digitalocean.com/resources/articles/what-is-openclaw) — not LocalAI's count at all. The critique's diagnosis of "repo-metric cross-wiring" is correct in spirit but wrong in attribution direction: 68k was likely OpenClaw's count at an earlier date, not a LocalAI number that leaked into the wrong row.

2. **LocalAI P2P issues are real**: CONFIRMED. [GitHub issue #3968](https://github.com/mudler/LocalAI/issues/3968) documents P2P inferencing failures where discovery succeeds but gRPC connections fail. Official [troubleshooting documentation](https://localai.io/basics/troubleshooting/) explicitly acknowledges limitations: single model only, workers must be detected before inference starts, and llama-cpp compatible models only.

3. **Holochain warrants incomplete**: CONFIRMED. [Dev Pulse 153](https://blog.holochain.org/dev-pulse-153-holochain-0-6-released-with-immune-system/) explicitly states that membrane proof enforcement during handshaking is still coming. Unauthorized agents can join temporarily before being warranted and blocked. Warrants are currently only delivered to agent public key authorities. The [2025 year-end blog](https://blog.holochain.org/2025-at-a-glance-landing-reliability/) reiterates: "It's not complete (membrane proof enforcement during network handshaking is still coming) but it's functional."

4. **OVOS/HiveMind licensing bifurcation**: CONFIRMED. The [HiveMind-core repository](https://github.com/JarbasHiveMind/HiveMind-core) states: "Starting with version 4.0, HiveMind-core is licensed under the GNU AGPL-3.0." All prior releases remain available under Apache-2.0.

5. **Khoj is AGPL**: CONFIRMED. AGPL-3.0 license per the [Khoj GitHub repository](https://github.com/khoj-ai/khoj).

6. **Olas concentration in prediction markets**: CONFIRMED AND SHARPENED. Olas public materials center on Omenstrat (Gnosis/Omen) and Polystrat (Polymarket). CEO David Minarsch's public statements frame Olas as [prediction market economy infrastructure](https://www.mexc.com/news/932530).

### What the Critique Got WRONG or INCOMPLETE

1. **Olas transaction number is stale.** The critique accepted "8.8M+ A2A transactions" without verification. As of February 2026, Olas's own account states the network has ["surpassed 10M+ agent-to-agent transactions"](https://x.com/autonolas/status/2019752385959415861). The critique should have flagged the 8.8M figure as outdated.

2. **AD4M v0.10.1 maturity overstated by critique.** The critique treated v0.10.1 as a "release." It is actually labeled ["Prerelease (final RC for wider testing)"](https://github.com/coasys/ad4m/releases) on GitHub, with no Windows binary. The critique accepted this at face value without checking release status.

3. **OpenClaw star count diagnosis was directionally wrong.** The critique said the 68k figure "appears tied to LocalAI." In reality, 68k was OpenClaw's own count from January 2026 — it simply grew explosively to 332k by March 2026 ([Reddit](https://www.reddit.com/r/ArtificialInteligence/comments/1ryhyql/openclaw_got_200k_github_stars_in_3_months_i/)). LocalAI has only 44.3k stars ([GitHub](https://github.com/mudler/LocalAI)). The contamination diagnosis was correct (the numbers were wrong), but the direction of the error was misidentified.

4. **Two research papers unverifiable.** The critique mentioned AMRO-S and "observation-driven CRDT coordination" as real papers. Neither could be verified through academic search. SILO-BENCH ([arXiv:2603.01045](https://arxiv.org/abs/2603.01045)) and DecentLLMs ([arXiv:2507.14928](https://arxiv.org/abs/2507.14928)) are confirmed real arXiv papers.

### Trinary Decision on the Critique Itself

**[0] HOLD.** The critique's instincts and methodology are sound, but it introduced its own attribution errors while correcting the draft's errors. Trust the structural recommendations; do not trust the specific metric corrections without independent verification.

---

## Layer 2: Corrected Landscape Scan with Strict Claim Taxonomy

Every claim below is prefixed with one of five epistemic tiers:

- **[TESTED]** — Implemented and personally tested (only OpenClaw in WSL qualifies)
- **[VENDOR-CLAIMED]** — Stated by the project's own documentation or marketing
- **[COMMUNITY-REPORTED]** — Reported by users, third-party articles, or community posts
- **[RESEARCH-ONLY]** — Academic paper or preprint, not production software
- **[SPECULATIVE]** — Inferred from architecture, not directly evidenced

### Tier 1: Personal Agent Layer

#### OpenClaw

- **[TESTED]** OpenClaw is installed and running in WSL as of March 2026.
- **[VENDOR-CLAIMED]** Personal AI assistant running on user-controlled devices, connecting to WhatsApp, Telegram, Slack, Discord, and iMessage ([openclaw.ai](https://openclaw.ai), [GitHub](https://github.com/openclaw/openclaw)).
- **[COMMUNITY-REPORTED]** 332k GitHub stars, MIT licensed, one of the fastest-growing open-source projects ever — 60k stars in 72 hours, 200k in 3 months ([Reddit](https://www.reddit.com/r/ArtificialInteligence/comments/1ryhyql/openclaw_got_200k_github_stars_in_3_months_i/), [DigitalOcean](https://www.digitalocean.com/resources/articles/what-is-openclaw)).
- **[VENDOR-CLAIMED]** AgentSkills system: 100+ preconfigured skills for shell commands, file management, and web automation; skills are self-improving — the agent can write new skills autonomously ([DigitalOcean](https://www.digitalocean.com/resources/articles/what-is-openclaw)).
- **[VENDOR-CLAIMED]** Persistent memory via local Markdown documents. ClawHub skill marketplace. Lobster workflow shell for composable pipelines.
- **[VENDOR-CLAIMED]** Model-agnostic: works with cloud APIs or local models via Ollama.

**FLOSSI0ULLK relevance:** Action-taking control plane. Routes user intent from messaging channels to local execution. Positioned as the "Soma/Hand" in the FLOSSI0ULLK architecture — the active agent that reads/writes files, runs scripts, and executes commands. MIT license is maximally permissive for integration.

#### Khoj

- **[VENDOR-CLAIMED]** AI second brain, self-hostable. Custom agents, automations, deep research. Supports OpenAI, Anthropic, Gemini, Ollama (local), vLLM, and LMStudio ([Khoj Docs](https://docs.khoj.dev/get-started/setup/), [GitHub](https://github.com/khoj-ai/khoj)).
- **[VENDOR-CLAIMED]** Runs on localhost:42110, deployable via Docker or pip install.
- **[COMMUNITY-REPORTED]** Functional self-hosted RAG with good Ollama integration.
- **[SPECULATIVE]** AGPL-3.0 license creates copyleft obligations that need explicit modeling in the FLOSSI0ULLK dependency graph. Any network service offering Khoj functionality must release source under AGPL. This is philosophically aligned with FLOSSI0ULLK values but operationally constraining.

**FLOSSI0ULLK relevance:** Best immediate FOSS "secretary / memory / automation" candidate. The RAG + automation combo maps to the Hippocampus layer. AGPL aligns with open-source ethos but must be accepted deliberately.

### Tier 2: Local Inference Layer

#### LocalAI

- **[VENDOR-CLAIMED]** Open-source AI engine, drop-in OpenAI/Anthropic API replacement. 35+ backends, any hardware. MCP support with server-side and client-side modes. Built-in agents as of v4.0.0 ([LocalAI Features](https://localai.io/features/), [GitHub](https://github.com/mudler/LocalAI)).
- **[COMMUNITY-REPORTED]** 44.3k GitHub stars, MIT licensed, active development ([GitHub](https://github.com/mudler/LocalAI)).
- **[VENDOR-CLAIMED]** Distributed inference via P2P using libp2p, with automatic peer discovery ([LocalAI P2P Docs](https://localai.io/features/distribute/)).
- **[COMMUNITY-REPORTED]** P2P distributed inference has documented issues: [GitHub issue #3968](https://github.com/mudler/LocalAI/issues/3968) reports inference failures — discovery works but gRPC connections fail for some users.
- **[VENDOR-CLAIMED]** P2P limitations acknowledged in official docs: single model only, workers must be pre-detected, llama-cpp models only ([LocalAI Troubleshooting](https://localai.io/basics/troubleshooting/)).
- **[VENDOR-CLAIMED]** MCP integration is comprehensive: remote HTTP servers, local stdio servers, cached connections, multi-endpoint support, client-side browser MCP, and MCP Apps with interactive UIs ([LocalAI MCP Docs](https://localai.io/features/mcp/index.html)).

**FLOSSI0ULLK relevance:** Primary local inference substrate. MCP support makes it a viable interop seam. P2P is strategically relevant but experimental — treat as research lead, not architecture commitment, until a 2-node proof is run locally.

### Tier 3: Voice & Distributed Satellite Layer

#### OVOS + HiveMind

- **[VENDOR-CLAIMED]** Open Voice OS: voice-first assistant, fully customizable intents, modular design ([OpenVoiceOS Blog](https://blog.openvoiceos.org/posts/2025-07-25-A-real-use-case-with-OVOS-and-Hivemind)).
- **[VENDOR-CLAIMED]** HiveMind: extends a single OVOS instance to many devices. Supports voice satellite, voice relay, mic satellite, and web chat. Modular protocols, database plugins, fine-grained permissions ([GitHub](https://github.com/JarbasHiveMind/HiveMind-core)).
- **[COMMUNITY-REPORTED]** Real deployment documented: Raspberry Pi Zero 2W satellites connecting to an OVOS server via HiveMind in Kubernetes, including a wheelchair-mounted enclosure use case ([OpenVoiceOS Blog](https://blog.openvoiceos.org/posts/2025-07-25-A-real-use-case-with-OVOS-and-Hivemind)).
- **[VENDOR-CLAIMED]** License bifurcation: HiveMind-core 4.0+ is AGPL-3.0; pre-4.0 releases remain Apache-2.0 ([GitHub](https://github.com/JarbasHiveMind/HiveMind-core)).

**FLOSSI0ULLK relevance:** Voice and distributed satellite topology. The hub-spoke model (one OVOS server, many HiveMind satellites) maps naturally to FLOSSI0ULLK's distributed agent model. The AGPL bifurcation must be modeled explicitly in dependency boundaries — pin to Apache-2.0 releases if copyleft is unacceptable for specific modules, or embrace AGPL-3.0 as aligned with FLOSSI0ULLK values.

### Tier 4: Substrate / Trust Layer

#### Holochain

- **[VENDOR-CLAIMED]** 0.6.0 released December 2025 with "functioning immune system" — warrants block bad agents at network transport level ([Dev Pulse 153](https://blog.holochain.org/dev-pulse-153-holochain-0-6-released-with-immune-system/), [Holochain/X](https://x.com/Holochain/status/1996306285726196070)).
- **[VENDOR-CLAIMED]** Warrants stabilized, no longer behind feature flag. Invalid ops trigger network-level blocking ([docs.rs CHANGELOG](https://docs.rs/crate/holochain/latest/source/CHANGELOG.md)).
- **[VENDOR-CLAIMED]** INCOMPLETE: Membrane proof enforcement during handshaking NOT YET IMPLEMENTED. Unauthorized agents CAN join temporarily before being warranted and blocked. Warrants only delivered to agent public key authorities ([Dev Pulse 153](https://blog.holochain.org/dev-pulse-153-holochain-0-6-released-with-immune-system/), [2025 Year-End Blog](https://blog.holochain.org/2025-at-a-glance-landing-reliability/)).
- **[VENDOR-CLAIMED]** Wind Tunnel testing framework production-ready. Roadmap shows 0.6.1 beta with membrane proof improvements ([Holochain Roadmap](https://www.holochain.org/roadmap/)).
- **[VENDOR-CLAIMED]** Unyt subsidiary released Circulo community currency app, building payment rails for HoloFuel ([Holochain Blog](https://blog.holochain.org/finding-our-edge-a-strategic-update/)).
- **[VENDOR-CLAIMED]** Edge Node concept: OCI-compliant container for always-on hApp deployment.

**FLOSSI0ULLK relevance:** THE differentiator. None of the Tier 1–3 tools provide agent-centric source-chain truth, provenance, or consent receipts. Holochain is the only component that provides sovereignty-native coordination. The immune system is real but incomplete — design around the gap (temporary unauthorized access window) rather than assuming it is solved.

#### AD4M

- **[VENDOR-CLAIMED]** v0.10.1 labeled "Prerelease (final RC for wider testing)" — NOT a stable release ([GitHub Releases](https://github.com/coasys/ad4m/releases)). First public release since v0.9.0 (March 2024).
- **[VENDOR-CLAIMED]** Local AI integration: LLM inference, transcription, embedding via simple interface methods. Set models once, all apps inherit config. Supports Hugging Face, local files, and Ollama. GPU optional (CUDA for local LLMs) ([GitHub](https://github.com/coasys/ad4m/releases), [AD4M Docs](https://docs.ad4m.dev/installation/)).
- **[VENDOR-CLAIMED]** Holochain upgraded to v0.3.6 in this release.
- **[VENDOR-CLAIMED]** Synergy Engine working MVP: semantic queries across local group, eventually the entire AD4M network ([GitHub](https://github.com/coasys/ad4m/releases)).
- **[VENDOR-CLAIMED]** No Windows binary. Linux requires recent glibc ([Flux/X](https://x.com/flux_social/status/1967885110944174302)).

**FLOSSI0ULLK relevance:** Agent-centric composition layer. Enables semantic linking across substrates. The Synergy Engine maps directly to FLOSSI0ULLK's distributed knowledge composition goals. However, v0.10.1 is pre-release — treat as promising research substrate, not production dependency. AD4M bundles Holochain v0.3.6 while Holochain mainline is at 0.6.0 — this version gap means AD4M's Holochain substrate is missing the immune system entirely.

#### Olas / Autonolas

- **[VENDOR-CLAIMED]** 10M+ agent-to-agent transactions as of February 2026, across Gnosis, Base, Polygon, and Optimism ([Olas/X](https://x.com/autonolas/status/2019752385959415861), [Olas Data](https://olas.network/data)).
- **[VENDOR-CLAIMED]** Mech Marketplace for autonomous agent service buying/selling. Upgrade planned by March 31, 2026 including x402 support and dynamic pricing ([Gate.com](https://www.gate.com/crypto-calendar/crypto-project/119160)).
- **[COMMUNITY-REPORTED]** Activity concentrated in prediction market use cases: Omenstrat (Gnosis/Omen), Polystrat (Polymarket). CEO David Minarsch frames Olas as "prediction market economy" infrastructure ([MEXC News](https://www.mexc.com/news/932530)).
- **[COMMUNITY-REPORTED]** OLAS token price significantly depressed (~$0.046 March 2026), suggesting limited market confidence in near-term utility expansion beyond current use cases.

**FLOSSI0ULLK relevance:** Proof that A2A transaction volume can exist on-chain, but the narrow use-case concentration (prediction markets) means this is NOT evidence of general-purpose multi-agent coordination at scale. Reference system for economic agent incentive design, not for architectural mimicry.

### Research Layer (Non-Production)

#### SILO-BENCH

- **[RESEARCH-ONLY]** [arXiv:2603.01045](https://arxiv.org/abs/2603.01045), March 2026. Benchmark of 30 algorithmic tasks, 54 configurations, 1,620 experiments.
- Key finding: "Communication-Reasoning Gap" — agents spontaneously form task-appropriate coordination topologies but systematically fail to synthesize distributed state into correct answers.

**FLOSSI0ULLK implication:** Validates that naive multi-agent scaling does not solve coordination. The Holochain-based provenance layer is more important, not less — shared state verification must be protocol-enforced, not left to LLM coordination.

#### DecentLLMs

- **[RESEARCH-ONLY]** [arXiv:2507.14928](https://arxiv.org/abs/2507.14928), July 2025. Byzantine-robust decentralized consensus for multi-agent LLM systems.
- Proposes worker agents generating answers concurrently with evaluator agents scoring and ranking — explicitly decentralized architecture.

**FLOSSI0ULLK implication:** Architecturally aligned with the Recursive Self-Aggregation concept. Research signal, not production tool. The Byzantine tolerance angle is directly relevant to open networks.

#### AMRO-S

- **[SPECULATIVE]** Could not verify this paper exists. The original draft may have cited a non-existent or mis-named paper. Treat as unverified until a source URL is provided.

#### "Observation-driven CRDT coordination"

- **[SPECULATIVE]** Could not verify this paper exists. Treat as unverified.

---

## Layer 3: Walking Skeleton Integration Spec

### Objective

Prove that OpenClaw, LocalAI, and Khoj can form a minimal working pipeline: user sends a message via chat → OpenClaw routes to action → LocalAI provides inference → Khoj provides memory/RAG → result returns to user. OVOS/HiveMind is deferred to Phase 2 (voice).

### Architecture

```text
[User] → [Telegram/WhatsApp/Slack]
         ↓
    [OpenClaw Gateway]  ← controls local machine
         ↓                   ↓
    [LocalAI]           [Khoj]
    (inference)         (memory/RAG/automation)
         ↓                   ↓
    [Agent Response] ← merges inference + context
         ↓
    [User receives reply on chat channel]
```

### Component Roles

| Component | Role | Interface | Status |
|-----------|------|-----------|--------|
| OpenClaw | Message router, action executor, skill engine | Chat → Node.js service → AgentSkills | **[TESTED]** in WSL |
| LocalAI | Local LLM inference, MCP server | OpenAI-compatible REST API on :8080 | **[VENDOR-CLAIMED]** production-ready |
| Khoj | RAG over personal docs, automation scheduling, persistent memory | REST API on :42110 | **[VENDOR-CLAIMED]** self-hostable |

### Integration Seams

1. **OpenClaw → LocalAI**: OpenClaw is model-agnostic. Point its LLM backend config at LocalAI's OpenAI-compatible endpoint (`http://localhost:8080/v1`). This is a standard config change, not custom code.

2. **OpenClaw → Khoj**: Write an OpenClaw AgentSkill that calls Khoj's REST API for memory queries and doc search. Khoj exposes endpoints for search and chat. The skill sends context-enriched prompts.

3. **LocalAI ← MCP → External tools**: [LocalAI's MCP support](https://localai.io/features/mcp/index.html) enables connecting to external data sources and tools. This becomes the extensibility seam for future integrations.

4. **Khoj ← Ollama ← LocalAI backend**: If running fully local, Khoj can use Ollama as its LLM, and Ollama can share the same model files as LocalAI's llama-cpp backend. Alternatively, point Khoj's OpenAI-compatible config at LocalAI directly.

### Phase 1 Proof Milestones (2-Week Target)

| # | Milestone | Acceptance Criteria | Depends On |
|---|-----------|-------------------|------------|
| 1 | OpenClaw responds via Telegram using LocalAI | Send message on Telegram → get coherent response from local model | OpenClaw config → LocalAI endpoint |
| 2 | OpenClaw skill queries Khoj memory | "What did I work on yesterday?" returns Khoj-indexed data | Khoj running, docs indexed, skill written |
| 3 | Round-trip with provenance logging | Every interaction logged in `harvest/YYYY-MM-DD.jsonl` with timestamp, source, intent, response | OpenClaw hook or skill |
| 4 | Scout skill filters for ULLK signal | "Scout: harvest today's ULLK signals" returns structured JSONL of relevant interactions | Builds on milestone 3 |

### Dependency Boundary Rules

| Dependency | License | Strategy |
|------------|---------|----------|
| OpenClaw | MIT | Fully permissive. No constraints on integration. |
| LocalAI | MIT | Fully permissive. No constraints. |
| Khoj | AGPL-3.0 | AGPL requires source release for any network service using Khoj code. If FLOSSI0ULLK is itself AGPL/FOSS, this is non-issue. If any module must be proprietary, Khoj must be isolated as a service with API boundary only — no code linking. |
| HiveMind 4.0+ | AGPL-3.0 | Same strategy as Khoj. Pin to Apache-2.0 releases (pre-4.0) if AGPL is unacceptable for specific deployment contexts. |

### What This Skeleton Does NOT Address

- Holochain provenance (Phase 3 — requires Holochain 0.6+ integration)
- AD4M semantic linking (Phase 4 — AD4M v0.10.1 is still pre-release)
- Voice interface via OVOS/HiveMind (Phase 2)
- Multi-agent consensus or Byzantine fault tolerance (research phase)
- Cross-runtime MCP protocol alignment (requires custom bridge work)

---

## Layer 4: Red-Team of This Document (The Underneath)

### Intent Echo

This meta-red-team asks: if someone used this corrected document for FLOSSI0ULLK architecture decisions, where would it still mislead them?

### Claim Taxonomy Audit

| Section | Tier Distribution | Risk |
|---------|-------------------|------|
| OpenClaw | 1 TESTED, 4 VENDOR-CLAIMED, 2 COMMUNITY-REPORTED | LOW — direct experience exists |
| LocalAI | 4 VENDOR-CLAIMED, 2 COMMUNITY-REPORTED | MEDIUM — P2P claims need local proof |
| Holochain | 5 VENDOR-CLAIMED | MEDIUM — all claims from project's own blog/docs, no independent audit |
| AD4M | 5 VENDOR-CLAIMED | HIGH — pre-release software, all claims self-reported, no community validation visible |
| Olas | 2 VENDOR-CLAIMED, 2 COMMUNITY-REPORTED | MEDIUM — transaction data is on-chain verifiable but use-case breadth is not |
| Research papers | 2 RESEARCH-ONLY, 2 SPECULATIVE | HIGH — two papers could not be verified at all |

### Structural Risks in This Document

1. **Vendor-claimed dominance.** The majority of claims in this document are [VENDOR-CLAIMED]. This is inherent to a landscape scan — surveying what projects say about themselves — but it means the document is only as trustworthy as the projects' self-reporting. Mitigation: the walking skeleton's milestone-based validation converts VENDOR-CLAIMED to TESTED incrementally.

2. **Holochain version gap with AD4M.** AD4M bundles Holochain v0.3.6. Holochain mainline is at 0.6.0 with warrants and immune system. This means AD4M's Holochain substrate is MISSING the immune system entirely. This gap is not called out sufficiently in the AD4M section above and could mislead architecture decisions that assume AD4M inherits 0.6.0 capabilities.

3. **Walking skeleton assumes co-located services.** The Phase 1 spec assumes OpenClaw, LocalAI, and Khoj all run on the same machine (localhost). This is fine for proof but does NOT validate distributed deployment, which is the entire point of FLOSSI0ULLK.

4. **MCP as interop seam is unproven.** The document treats MCP as a meaningful integration point between LocalAI and the broader ecosystem. MCP is real and [documented](https://localai.io/features/mcp/index.html), but "MCP server exists" is not "cross-runtime protocol alignment is solved." The spec should be explicit that MCP integration is itself a hypothesis to be tested, not an assumed capability.

5. **License strategy is incomplete.** The dependency boundary rules address AGPL at the code level but not at the data level. Khoj under AGPL may have implications for the data it processes and indexes — this needs legal review, not just engineering opinion.

6. **Missing threat model.** Neither the landscape scan nor the walking skeleton spec includes a security threat model. For a project centered on sovereignty and trust, this is a significant omission. What happens when OpenClaw's skill marketplace serves a malicious skill? What happens when LocalAI's P2P network includes an adversarial node?

7. **Research paper section is weakest link.** Two of four cited papers could not be verified. The remaining two — SILO-BENCH ([arXiv:2603.01045](https://arxiv.org/abs/2603.01045)) and DecentLLMs ([arXiv:2507.14928](https://arxiv.org/abs/2507.14928)) — are arXiv preprints, not peer-reviewed publications. This section should be labeled as "signals for future investigation," not "supporting evidence for architecture."

8. **This document's own citation quality.** Most URLs are from official project sources (GitHub, project blogs, docs). There is limited third-party independent verification. The [DigitalOcean article on OpenClaw](https://www.digitalocean.com/resources/articles/what-is-openclaw) and the [MEXC article on Olas](https://www.mexc.com/news/932530) provide some independent signal but are themselves secondary sources.

### Trinary Decision on This Document

**[+1] PROCEED** with the walking skeleton. The shortlist is validated. The claim taxonomy makes the epistemic status of each claim visible.

**[0] HOLD** on treating the research section or AD4M integration as architecture commitments.

**[-1] REJECT** using this document without adding a threat model before Phase 2 (when the attack surface expands to voice and distributed deployment).

### What Must Happen Before the Next Revision

1. Run the walking skeleton Phase 1. Convert at least 4 VENDOR-CLAIMED entries to TESTED.
2. Verify or retract the AMRO-S and CRDT coordination paper citations.
3. Investigate the AD4M ↔ Holochain 0.6.0 version gap explicitly. Is AD4M planning to upgrade to 0.6.0? Is the immune system available through AD4M or only through direct Holochain?
4. Draft a minimal threat model for the walking skeleton (OpenClaw skill trust, LocalAI API exposure, Khoj data exposure).
5. Get legal opinion on AGPL data implications for Khoj and HiveMind 4.0+.

---

## Summary Table: Full Shortlist Status

| Project | Stars | License | Claim Tier | FLOSSI0ULLK Role | Immediate Action |
|---------|-------|---------|-----------|-------------------|-----------------|
| OpenClaw | 332k | MIT | TESTED | Action/Control Plane | Run walking skeleton Phase 1 |
| LocalAI | 44.3k | MIT | VENDOR-CLAIMED | Local Inference | Point OpenClaw at LocalAI endpoint |
| Khoj | — | AGPL-3.0 | VENDOR-CLAIMED | Memory/RAG/Automation | Deploy via Docker, index docs |
| OVOS/HiveMind | — | Apache-2.0 / AGPL-3.0 | COMMUNITY-REPORTED | Voice/Satellites | Phase 2 — after walking skeleton proves out |
| Holochain | — | CAL-1.0 | VENDOR-CLAIMED | Trust/Provenance | Phase 3 — differentiator layer |
| AD4M | — | Pre-release | VENDOR-CLAIMED | Semantic Composition | Phase 4 — wait for stable release and HC 0.6.0 upgrade |
| Olas | — | On-chain | COMMUNITY-REPORTED | Reference/Economics | Monitor, do not integrate yet |
