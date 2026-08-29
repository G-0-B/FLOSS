# A2A Harness Mesh — Research Pointer (2026-08-29)

```yaml
id: "2026-08-29-a2a-harness-mesh-research"
date: "2026-08-29"
type: "research_pointer"
status: "Partial — distillation of session deep-research; not a second grand synthesis"
plan: "docs/superpowers/plans/2026-08-29-a2a-harness-mesh.md"
prior_policy: "docs/research/2026-05-22-open-distributed-intelligence-digestion.md"
```

Short pointer so the next session does not re-derive the harness matrix. Full session report: Grok workflow scratch `report.md` (2026-08-29, Status: Partial). Implementation plan: [`docs/superpowers/plans/2026-08-29-a2a-harness-mesh.md`](../superpowers/plans/2026-08-29-a2a-harness-mesh.md).

## Policy (complementary layers)

**Verified in-repo (2026-05-22 digestion):** MCP now as the tool/context plane; A2A later as an inter-agent handshake/task plane — not a replacement for MCP or source-chain / symbolic validation. Layered, not merged.

**Partial (2026-08-29 research):** Official A2A materials treat A2A and MCP the same way (peers / tasks vs tools / resources). Live FLOSSI0ULLK coding-harness mesh remains MCP (root `.mcp.json`). Do not add A2A to `.mcp.json`; do not treat A2A as a controller.

## Native surfaces (named harnesses)

None of Claude Code, Antigravity, Grok, or Perplexity natively serve or consume Linux Foundation A2A. Hermes is the exception (bidirectional).

| Harness | Native A2A | Native MCP | Other native | Notes |
|---|---|---|---|---|
| Claude Code | No | stdio (default) and HTTP | — | Project scope → repo-root `.mcp.json` |
| Google Antigravity | No | stdio / remote Streamable HTTP, SSE, websocket | — | Workspace `.agents/mcp_config.json` |
| Grok Build | No | stdio and HTTP; merges Claude/Cursor/`.mcp.json` | ACP over JSON-RPC stdio (`grok agent stdio`) | Remote MCP Tools: Streaming HTTP/SSE; custom connectors reject localhost/private URLs |
| Hermes Agent | Yes — Agent Card `GET /.well-known/agent-card.json`; JSON-RPC `POST /`; default port 9900 | `mcp_servers` stdio or HTTP | ACP via `hermes acp` | `gateway.platforms.a2a` in `~/.hermes/config.yaml` |
| Perplexity | No | Remote Streamable HTTP MCP server (+ local stdio package) | — | Inbound MCP tool for other clients, not an A2A agent |

Truth-status: harness rows are from inspected first-party docs in the 2026-08-29 pass (**Partial** — this workspace did not re-run live binary probes). Do not promote unverified harness support to Verified.

## Adapters (optional later — not this plan)

| Bridge | Role | Plan stance |
|---|---|---|
| orbital-command-centre (`occ-a2a`) | Wrap Grok (`grok -p`) / Antigravity (`agy -p`) as A2A | Optional later; YAGNI until concrete peer-task need |
| vbcherepanov/a2abridge | MCP-stdio agents → A2A peers; directory `127.0.0.1:7777` | Optional later for Claude Code; author-claimed IDE list not re-verified here |
| GongRzhe/A2A-MCP-Server | — | Do not use (archived 2026-03-03) |
| firstintent/a2a-bridge | A2A + ACP daemon | Hermes outbound listed v0.2 — not this plan |

## ASAP shape (this plan only)

1. Local Python helloworld pair (Agent Card + JSON-RPC on loopback).
2. Hermes as first native A2A peer; keep it an MCP client of Layer 4.5 (not a controller).
3. Claude Code / Antigravity / Grok / Perplexity stay on MCP for tools.
4. Adapters only when a concrete peer-task need appears.

Out of scope here: mapping A2A Task state onto ADR-12 ConsentPayload; counting an A2A remote toward ≥3 surfaces / ≥4 families; OmniRoute `/.well-known/agent.json` claim (unverified vs ADR-19).
