<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# im currently using agentmemory, but i have mem0 and khoj but as potential projects to use and actually have siyuan installed already too, was playing with it a tiny bit as a floss replacement for obsidian months ago i forgot about

**Intent echoed:** You already have agentmemory running, mem0 and Khoj queued as potential projects, and SiYuan installed but mostly forgotten — let's map out how all four relate to each other and what you actually need to activate next.

***

## Your Actual Stack, Clarified

You're not starting from zero — you already have the core pieces. Here's the honest picture of what each tool does in your stack and how they interlock:

### agentmemory — Your Current Foundation

This is actually the strongest choice for your coding-agent workflow right now. It runs as an MCP server that silently captures everything your agent does via 12 lifecycle hooks (PreToolUse, PostToolUse, SessionEnd, etc.), then injects only ~1,900 relevant tokens into each new session. It uses a **hybrid BM25 + vector + knowledge graph** architecture entirely local, hitting **95.2% recall at top-5 on LongMemEval-S** — which outperforms mem0's cloud tier on benchmarks. Cost is roughly \$10/year using local embeddings via `@xenova/transformers`. Keep using this for your agent coding sessions.[^1][^2]

### mem0 — Personalization-First, But Expensive Tier for Graph

mem0 uses a dual-store model: vector DB for semantic search + knowledge graph for entity relationships. Its open-source core is solid but the graph memory features are increasingly pushed into the paid Pro tier. As of 2026, they replaced external graph store support with built-in entity linking in the open-source version. Good for: building **personalization agents** that need to remember *user preferences* across many sessions. Less ideal than agentmemory for your coding/orchestration workflow specifically.[^3][^4]

### Khoj — The Missing Link Between You, SiYuan, and OpenHuman

This is the one most worth activating now given your setup. Khoj is AGPL-3.0, self-hosted, and crucially — there's already an open GitHub issue proposing **SiYuan integration via SiYuan's SQL-like REST API**. Khoj indexes your existing markdown files and vaults for RAG, meaning it could sit *between* OpenHuman's `.md` output and your agent queries, giving you semantic search over everything you've accumulated. It's the glue layer.[^5]

### SiYuan — Already Installed, Massively Underutilized

You've been sleeping on this one. SiYuan has a full **kernel HTTP API at `localhost:6806`** that lets agents search, read, create, update, and delete blocks programmatically via `curl` or MCP. There's already a dedicated **SiYuan MCP server** (`@porkll/siyuan-mcp`) that drops straight into your MCP config. That means agentmemory + SiYuan MCP = your agent can *read and write directly into your SiYuan vault* as a long-form structured knowledge surface, while agentmemory handles session-level episodic recall. This is the combo you want.[^6][^7]

***

## Recommended Activation Order

Given what you already have installed:

1. **Immediately:** Add `@porkll/siyuan-mcp` to your MCP config — SiYuan is running, just needs to be wired to your agents.[^7][^6]
2. **This week:** Point Khoj at the folder OpenHuman writes `.md` files into — it becomes semantic search over your agent memory history.
3. **Later:** Evaluate whether mem0 adds anything your agentmemory + SiYuan combo doesn't already cover (it probably won't for your use case ).[^2]
4. **OpenHuman collaboration angle:** SiYuan + Khoj + agentmemory is a fully FLOSS stack that could be proposed to the OpenHuman team as a portable, Obsidian-free memory infrastructure.

***

## Architecture at a Glance

| Layer | Tool | Role | FLOSS? |
| :-- | :-- | :-- | :-- |
| Episodic / session memory | **agentmemory** (current) | Captures agent actions, injects context | ✅ MIT |
| Structured long-term KB | **SiYuan** (installed) | Block-level wiki, agent-writable via MCP | ✅ AGPL |
| Semantic search / RAG | **Khoj** (queued) | Indexes all `.md` vaults, answers questions | ✅ AGPL |
| Personalization memory | **mem0** (queued) | User-preference entity graph | ✅ Apache-2 (OSS core) |

The beautiful thing here is agentmemory handles *what happened*, SiYuan handles *what you know*, and Khoj handles *finding it* — three distinct memory layers  that map almost perfectly onto the working / long-term / retrieval architecture in the agent memory literature.[^8][^9]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^21][^22][^23][^24]</span>

<div align="center">⁂</div>

[^1]: https://github.com/rohitg00/agentmemory/blob/main/benchmark/COMPARISON.md

[^2]: https://www.aibuilderclub.com/blog/ai-coding-agent-memory-agentmemory

[^3]: https://mem0.ai/blog/state-of-ai-agent-memory-2026

[^4]: https://vectorize.io/articles/hindsight-vs-mem0

[^5]: https://github.com/khoj-ai/khoj/issues/1146

[^6]: https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/productivity/productivity-siyuan

[^7]: https://mcpmarket.com/server/siyuan

[^8]: https://arxiv.org/pdf/2502.12110.pdf

[^9]: https://pub.towardsai.net/i-gave-my-ai-agent-a-three-layer-memory-obsidian-heres-how-it-thinks-now-0aaa0fdbdbbd

[^10]: https://arxiv.org/pdf/2501.13956.pdf

[^11]: https://arxiv.org/html/2412.17029v1

[^12]: http://arxiv.org/pdf/2404.13501.pdf

[^13]: http://arxiv.org/pdf/2502.13843.pdf

[^14]: https://arxiv.org/html/2412.15266

[^15]: https://joss.theoj.org/papers/10.21105/joss.03065.pdf

[^16]: https://arxiv.org/pdf/2502.13965.pdf

[^17]: https://www.youtube.com/watch?v=F1Ihel8Dgqs

[^18]: https://machinelearningmastery.com/the-6-best-ai-agent-memory-frameworks-you-should-try-in-2026/

[^19]: https://vectorize.io/articles/best-ai-agent-memory-systems

[^20]: https://www.reddit.com/r/LangChain/comments/1lhr4ag/built_an_autonomous_ai_agent_with_langgraph/

[^21]: https://atlan.com/know/best-ai-agent-memory-frameworks-2026/

[^22]: https://www.digitalapplied.com/blog/ai-agent-memory-vector-graph-episodic-2026

[^23]: https://github.com/Shichun-Liu/Agent-Memory-Paper-List

[^24]: https://github.com/siyuan-note/siyuan

