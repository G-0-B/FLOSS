# Reasoning-Ensemble MCP Server Spec

**Status:** ⚠️ Specified (post-hoc retrofit 2026-05-19)
**Truth status:** Reflects current `FLOSS/packages/reasoning_ensemble/mcp_server.py` v0.1 behavior; root `.mcp.json` registration added 2026-05-19; live client invocation still pending next-session verification
**Version:** 0.1.0
**Blast radius:** Module
**SDD discipline note:** Retrofit (same caveat as sibling specs).

---

## 0. What this is

FastMCP transport layer that exposes the Reasoning-Ensemble Router + Synthesizer as first-class MCP tools. Any MCP-aware client (Claude Code, Codex CLI, Gemini CLI, OpenCode, future agents) can invoke per-prompt classification + multi-model debate without shelling out to Python.

This server is **pure transport**. All business logic lives in `router.py` + `synthesizer.py`. This module is responsible only for:
- MCP framework registration
- Argument forwarding to underlying functions
- Result serialization to JSON
- Error handling (no exceptions cross the MCP boundary)

---

## 1. Tools exposed

### 1.1 `route_prompt(prompt, force_mode=None) -> str`

Calls `router.classify(prompt, force_mode)`. Returns a JSON string serialization of `RouterDecision` (see `reasoning-ensemble-router.spec.md` §1.4).

### 1.2 `deliberate(prompt, force_mode=None) -> str`

Full pipeline: route → if ensemble, synthesize. Returns a JSON string with:
- For all modes: `mode`, `router_decision`
- For `ensemble` mode additionally: `tier`, `synthesis_path`, `final_synthesis`, `voter_count`, `largest_cluster_fraction`, `minority_coherent_voters`
- For `pass_through` / `single_strong`: `note` field instructing caller to invoke their normal model surface

### 1.3 `get_recent_decisions(limit=10) -> str`

Reads `.agent-surface/reasoning/activity.jsonl` tail. Strips embeddings from response to keep payload manageable. Returns JSON array, newest first.

### 1.4 `get_ensemble_drafts(limit=5) -> str`

Lists most recent ensemble synthesis drafts from `.agent-surface/reasoning/ensemble/`. Each entry has filename + tier + voter count + cluster fraction + minority count + prompt preview + final synthesis preview + full file path.

---

## 2. Registration

### 2.1 `.mcp.json` template

```json
{
  "mcpServers": {
    "flossiullk-reasoning-ensemble": {
      "command": "python",
      "args": ["-m", "FLOSS.packages.reasoning_ensemble.mcp_server"]
    }
  }
}
```

Add to root `.mcp.json` alongside existing servers (`serena`, `flossiullk-consensus`). Recommend wrapping through JanuScope (matching the existing pattern at `C:/~shit/.mcp/lenses/`) once a `reasoning-ensemble.yaml` lens config exists.

### 2.2 Independence from consensus gateway

This server is intentionally separate from `metacoordinator_mcp` (the consensus gateway). The reasons:
- **Different stakes:** consensus gateway is decision-grade (Claims, Votes, source-chain commits, blast-radius tier discipline); reasoning ensemble is reasoning-grade (per-prompt routing/synthesis, shorter retention)
- **Different ratios:** consensus gateway runs N times per day for big decisions; reasoning ensemble runs M times per session for routing
- **Different failure modes:** consensus gateway down = no decisions; reasoning ensemble down = caller falls back to single-strong default (graceful)

Pulling them together would conflate stakes and produce confusing operational signals when one degrades.

---

## 3. Contracts

### 3.1 No exception leaks

All tool functions MUST catch exceptions internally and return a JSON `{"error": "..."}` payload. Never raise across the MCP boundary — the MCP framework converts uncaught exceptions to opaque protocol errors that clients can't debug.

### 3.2 Stateless

This module MUST NOT maintain in-process state across calls. All persistent state lives in `.agent-surface/reasoning/` (activity log + ensemble drafts) where the underlying modules manage it.

### 3.3 Plane A only

This MCP server inherits all Plane A constraints from `router.py` + `synthesizer.py`:
- No canonical-surface writes
- No remote pushes
- No consensus-gateway routing
- No cloud-API calls in the routing decision path

---

## 4. Operational notes

### 4.1 Cold-start cost

First call after server start triggers Ollama model load (~30-60s for phi4-mini + mxbai). MCP clients should be configured with timeout ≥120s for the first call after a fresh start.

### 4.2 Concurrency

FastMCP handles tool calls serially per-server-instance by default. For high-frequency routing (e.g., a session with many `pass_through` lookups), consider letting the caller cache RouterDecisions for identical prompts via `prompt_hash` lookup rather than re-routing every time.

### 4.3 Activity log integration

The MCP tools do NOT directly write to the activity log. The underlying Router and Synthesizer write to it. The MCP server only EXPOSES read access via `get_recent_decisions` + `get_ensemble_drafts`.

---

## 5. Open questions

1. **Streaming responses.** Current implementation is synchronous; clients wait for full ensemble (30-90s). FastMCP supports streaming; v0.2 should stream Router decisions + per-voter responses as they arrive.
2. **Cancellation.** No way to cancel a mid-flight ensemble call. Future: implement a `cancel(prompt_hash)` tool that signals the underlying ThreadPoolExecutor.
3. **Multi-instance coordination.** What happens if two MCP clients call `deliberate` on the same prompt simultaneously? Currently both run independently; both write separate drafts. Could be optimized to share work, but introduces shared-state complexity. Defer to v0.3.

---

## 6. SDD discipline going forward

Same protocol as `reasoning-ensemble-router.spec.md` §7.

---

## 7. Cross-refs

- **Code:** `FLOSS/packages/reasoning_ensemble/mcp_server.py`
- **Sibling specs:** `reasoning-ensemble-router.spec.md` + `reasoning-ensemble-synthesizer.spec.md`
- **Reference pattern:** `FLOSS/packages/metacoordinator_mcp/server.py` (consensus gateway MCP — same FastMCP framework, decision-grade)
- **Skill counterpart:** `FLOSS/skill-corpus/reasoning-ensemble/SKILL.md`
- **Unification doctrine:** `FLOSS/docs/research/2026-05-18-metaharness-unification.md`
- **Operator guide:** `FLOSS/docs/architecture/RUNTIME_SURFACES.md`
- **MCP framework:** `mcp.server.fastmcp.FastMCP`
- **JanuScope wrapping pattern:** `.mcp/lenses/{flossiullk-consensus,serena}.yaml`
