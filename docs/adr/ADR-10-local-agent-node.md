# ADR: MCP Server as Consensus Orchestration Hub

## Status
Accepted (2026-04-16)

## Date
2026-04-14

## Note
This ADR remains the accepted decision to expose the consensus/orchestration layer through MCP. The detailed mechanics have evolved since this draft was written:

- the active implementation now uses a file-based local source chain (`packages/source_chain/`)
- the active claim/vote model is analog rather than ternary
- current hook-triggered background rounds run through the local MCP gateway

For the current Phase 0 implementation details, read:
- `docs/superpowers/specs/2026-04-12-local-agent-node-design.md`
- `docs/architecture/AGENTIC_OPERATING_MODEL.md`

## Context

FLOSSI0ULLK (Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love, Light, and Knowledge) is a Holochain-based decentralized knowledge commons with symbolic-first validation and multi-agent coordination. The consensus gate (packages/orchestrator/) provides stateless claim validation through configurable voter functions, with 32/32 tests passing.

The system needs an orchestration layer that:
- Exposes the consensus gate to external AI agents (Claude Code, OpenCode, etc.)
- Routes claims to multiple LLM providers for parallel voting
- Maintains round state across asynchronous voting workflows
- Integrates cleanly with the existing Holochain four-system architecture (ADR-6)

Three integration patterns were evaluated:
1. **REST API wrapper** — Simple but requires custom client code per agent
2. **MCP Server as Orchestration Hub** — Standard protocol, native Claude Code support, tool-based interface
3. **Direct library embedding** — Tightest coupling, no network overhead, but locks out non-Python agents

## Decision

We will expose the consensus gate as an **MCP (Model Context Protocol) server** with **LiteLLM** for multi-model routing.

### Why MCP over REST
- MCP is the native integration protocol for Claude Code and compatible AI agents
- Tool-based interface maps naturally to consensus operations (submit_claim, cast_vote, read_decision)
- Built-in stdio transport eliminates port management and CORS configuration
- Growing ecosystem support across AI tooling

### Why LiteLLM over direct API calls
- Unified interface across 100+ LLM providers (OpenAI, Anthropic, Google, DeepSeek, Ollama)
- Consistent response format regardless of provider
- Built-in retry logic, fallbacks, and rate limiting
- Model aliasing simplifies voter configuration
- Anthony has paid API access across all major providers — LiteLLM lets every model participate

### Why in-memory state for v1
- Consensus rounds are short-lived (seconds to minutes)
- Stateless consensus gate functions remain pure — state lives in the server layer only
- Avoids premature persistence complexity
- SQLite upgrade path is straightforward for v2 if needed
- Thread safety via asyncio.Lock is sufficient for single-server deployment

### Architecture summary
- ConsensusGateServer class wraps the stateless consensus_gate.py functions
- In-memory stores: claims, votes, decisions, voter configurations
- MCP tool registry exposes 5 tools: submit_claim, run_consensus_round, cast_vote, read_decision, override_decision
- Two voting patterns supported:
  - **Pattern A** (server-orchestrated): Full round via run_consensus_round — server spawns LiteLLM voters, gathers votes via asyncio.gather(), calls tally() directly
  - **Pattern B** (incremental): External callers submit votes via cast_vote, server tallies on threshold
- make_litellm_voter adapter converts LiteLLM chat completions into Voter = Callable[[Claim], Vote]

## Consequences

### Positive
- Claude Code connects natively as MCP client — zero custom integration code
- Any MCP-compatible agent can participate in consensus rounds
- LiteLLM enables every model helps improve every other model philosophy
- Stateless core remains testable and pure (32 existing tests unaffected)
- Holochain connector remains orthogonal — MCP only needs claim_schema.py + consensus_gate.py

### Negative
- MCP ecosystem is still maturing — breaking changes possible
- In-memory state is lost on server restart (acceptable for v1)
- stdio transport limits deployment to local/co-located setups (SSE transport available for v2)
- Additional dependency on LiteLLM package

### Risks
- Python environment complexity on Windows (native vs WSL) — mitigated by testing both
- API key management across multiple providers needs a clean solution (env vars for v1)
- MCP protocol version drift — pin to stable release

## References
- ADR-6: Four-system integration architecture
- MCP specification: https://modelcontextprotocol.io
- LiteLLM docs: https://docs.litellm.ai
- Existing consensus gate: packages/orchestrator/consensus_gate.py
- Claim schema: packages/orchestrator/claim_schema.py
