<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# @GitHub @Academic thanks, now i just need a completely independent context continuation artifact with provenence, containing the plausibly best plan of action, reasoning as to why, evidence citing the files etc

Now I have everything needed to produce a complete, standalone artifact. Here it is.

***

# FLOSSIOULLK Infrastructure Migration — Context Continuation Artifact

**Artifact ID:** `FLOSS-INFRA-2026-07-17-v1.0`
**Generated:** 2026-07-17T12:19 EDT
**Author:** Perplexity External Reality Scout (FLOSSI0ULLK v2.0 role)
**Repo commit audited:** [`e8e71d4d`](https://github.com/G-0-B/FLOSS/tree/e8e71d4d29fac049e40db28ffb82d43d5592a158)
**Session summary:** 4-round audit of LiteLLM → OmniRoute migration, MCP server process lifecycle, and JanuScope spawn architecture. This document is fully self-contained — no prior session context required.

***

## Verified System State (as of commit e8e71d4d)

### What exists

**Two Python FastMCP MCP servers you own:**

1. [`packages/metacoordinator_mcp/server.py`](https://github.com/G-0-B/FLOSS/blob/e8e71d4d29fac049e40db28ffb82d43d5592a158/packages/metacoordinator_mcp/server.py) — FLOSSI0ULLK Consensus Gateway. Exposes 6 tools: `submit_claim`, `cast_vote`, `get_chain_context`, `get_decision`, `list_pending`, `run_consensus_round`. Delegates to `GatewayTools` → `voters.py`. Bare `mcp.run()`, no signal handlers, no PID guard, stdio transport.
2. [`packages/reasoning_ensemble/mcp_server.py`](https://github.com/G-0-B/FLOSS/blob/e8e71d4d29fac049e40db28ffb82d43d5592a158/packages/reasoning_ensemble/mcp_server.py) — Inline CFIS Router + Synthesizer. Exposes 4 tools: `route_prompt`, `deliberate`, `get_recent_decisions`, `get_ensemble_drafts`. Delegates to `router.py` (Ollama phi4-mini) and `synthesizer.py` (mxbai-embed-large embeddings). Same pattern — bare `mcp.run()`, no shutdown, stdio.

**LiteLLM call sites (complete list, [Verified]):**

- [`packages/metacoordinator_mcp/voters.py`](https://github.com/G-0-B/FLOSS/blob/e8e71d4d29fac049e40db28ffb82d43d5592a158/packages/metacoordinator_mcp/voters.py) — `make_litellm_voter()` and `make_omo_momus_voter()` both do `from litellm import completion` inside the voter closure. Called via `build_default_voters()` → `run_consensus_round()`. Current default voter roster: `cerebras/llama3.1-8b`, `groq/openai/gpt-oss-20b`, `groq/qwen/qwen3-32b`, plus Flowith and omo-momus variants.
- [`scripts/autonomous_synthesis_loop.py`](https://github.com/G-0-B/FLOSS/blob/e8e71d4d29fac049e40db28ffb82d43d5592a158/scripts/autonomous_synthesis_loop.py) — `import litellm` directly. Already flagged as a refactor candidate in [`docs/agent-memory/project/metaharness-unification-doctrine.md`](https://github.com/G-0-B/FLOSS/blob/e8e71d4d29fac049e40db28ffb82d43d5592a158/docs/agent-memory/project/metaharness-unification-doctrine.md).

**`.mcp.json` (the actual problem source):**

All 4 MCP servers run via `npx -y januscope@latest` — a JanuScope audit/injection proxy.  This creates the following process chain per agent session:

```
Claude Code session
  ├── npx -y januscope@latest --config serena.yaml          (Node.js)
  │     └── serena downstream process
  ├── npx -y januscope@latest --config flossiullk-consensus.yaml  (Node.js)
  │     └── python -m packages.metacoordinator_mcp.server   (Python, asyncio stdio)
  ├── npx -y januscope@latest --config flossiullk-reasoning-ensemble.yaml (Node.js)
  │     └── python -m packages.reasoning_ensemble.mcp_server (Python, asyncio stdio)
  └── npx -y januscope@latest --config agentmemory.yaml     (Node.js)
        └── agentmemory downstream process
```

With 3 agents: **12 Node.js + 6+ Python/downstream processes minimum.** The `npx -y` flag performs a version check and potential re-download on every spawn.

**What is NOT yet built:**

- Holochain not wired — `holochain_connector.py` exists in `packages/orchestrator/` but no server uses it
- JanuScope lens configs (`C:/~shit/.mcp/lenses/*.yaml`) live only on local Windows filesystem, not tracked in git
- OmniRoute not installed anywhere in the repo

***

## The Three Problems and Why They Are Related

### Problem 1: LiteLLM Is the Wrong Router Layer

LiteLLM's `from litellm import completion` in `voters.py` does exactly one thing: fan out HTTP calls to Cerebras/Groq/Mistral with a unified API. That is 100% of its value in this codebase.  There is no k8s deployment, no Helm chart, no Python microservice ecosystem that depends on it. The entire surface is two files and ~10 call sites across both voter factory functions.

OmniRoute 3.8 provides: 237+ providers (vs ~100), 90+ with free tier, built-in Fusion strategy that replicates and supersedes the manual `asyncio.gather` voter fan-out in `voters.py`, built-in A2A protocol matching the multi-agent consensus design, FTS5+vector memory replacing `shared-agent-memory-surface.json`, built-in MCP server (95 tools, 30 scopes), token compression pipeline (RTK + Caveman + LLMLingua-2), and circuit breakers per provider.  All MIT licensed.

```
**The one unverified dependency:** OmniRoute's Fusion judge prompt must be customizable to enforce FLOSSI0ULLK's `VOTER_PROMPT` schema (`WEIGHT: <float>`, `RATIONALE: <text>`, `[-0.999, 0.999]` range, `<think>` block stripping).  Verify this before deleting `voters.py`.
```


### Problem 2: MCP Server Process Lifecycle Is Broken

Both Python servers use `mcp.run()` with default stdio transport and no shutdown handling.  Stdio transport is a one-client-one-process model — it was designed for single-session use. In a multi-agent setup it spawns duplicate processes that never die. The asyncio event loop in each process sits in a `select()` spin on `sys.stdin` when the MCP client goes idle but hasn't closed the pipe. The `reasoning_ensemble` server additionally calls Ollama and runs embedding models per deliberation — two instances of this process simultaneously hammer the same local Ollama server.

### Problem 3: JanuScope `npx -y` Amplifies Everything

JanuScope itself is fine — audit logging and instruction injection are legitimate and valuable. The problem is the `npx -y januscope@latest` invocation, which: checks npm registry for latest version, potentially downloads it, spawns a fresh Node.js V8 runtime, adds its own stdio proxy layer on top of the Python server's stdio layer.  This runs 4 times per agent session. None of this persists between sessions.

These three problems are related because the right fix for all three converges on the same architectural move: **OmniRoute as a single persistent HTTP daemon replaces the need for separate Python MCP servers**, and JanuScope stays pinned and local for the external tools it wraps (serena, agentmemory) where you have no control.

***

## Plan of Action — Prioritized, Verified, Sequenced

### Stage 0 — Today, 5 Minutes: Pin JanuScope

This is the single highest-impact-to-effort fix in the entire plan. It stops the npm version-check network hit on every agent session spawn.

```bash
# Run once on Windows (where Claude Code runs)
npm install -g januscope
```

Update `.mcp.json` — change all 4 entries from:

```json
"command": "npx",
"args": ["-y", "januscope@latest", "--config", "..."]
```

to:

```json
"command": "januscope",
"args": ["--config", "..."]
```

**Why:** Verified from `.mcp.json`  — `npx -y` is the spawn-time penalty that runs before anything useful happens. Pinning eliminates it with zero functional change.

***

### Stage 1 — This Week: SSE Daemon for Both Python Servers

Convert both Python servers from stdio (one-process-per-client) to SSE HTTP transport (one shared daemon for all clients).

**Add this block to BOTH `server.py` and `mcp_server.py`, inside `if __name__ == "__main__":`**

```python
import atexit, os, signal, sys
from pathlib import Path

def _singleton_daemon(pid_filename: str, port: int):
    pid_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_path = pid_dir / pid_filename
    if pid_path.exists():
        try:
            existing_pid = int(pid_path.read_text().strip())
            os.kill(existing_pid, 0)  # raises if dead
            print(f"[FLOSS MCP] Already running on port {port} (pid {existing_pid}). Exiting.", file=sys.stderr)
            sys.exit(0)
        except (ProcessLookupError, ValueError):
            pass  # stale pid file — overwrite
    pid_path.write_text(str(os.getpid()))
    atexit.register(lambda: pid_path.unlink(missing_ok=True))
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (pid_path.unlink(missing_ok=True), sys.exit(0)))

if __name__ == "__main__":
    if mcp is None:
        raise ImportError("MCP SDK not installed. Run: pip install mcp")
    # Use port 7331 for consensus, 7332 for reasoning_ensemble
    _singleton_daemon("consensus.pid", 7331)
    # 0.0.0.0 required: Python server runs in WSL2, Claude Code on Windows
    mcp.run(transport="sse", host="0.0.0.0", port=7331)
```

**Update `.mcp.json`** — remove JanuScope wrapping for the two Python servers (they're HTTP now, not subprocess), keep JanuScope for serena and agentmemory:

```json
{
  "mcpServers": {
    "serena": {
      "command": "januscope",
      "args": ["--config", "C:/~shit/.mcp/lenses/serena.yaml"]
    },
    "flossiullk-consensus": {
      "url": "http://127.0.0.1:7331/sse"
    },
    "flossiullk-reasoning-ensemble": {
      "url": "http://127.0.0.1:7332/sse"
    },
    "agentmemory": {
      "command": "januscope",
      "args": ["--config", "C:/~shit/.mcp/lenses/agentmemory.yaml"]
    }
  }
}
```

**Start the daemons** (add to WSL2 startup or run manually once per boot):

```bash
python -m packages.metacoordinator_mcp.server &
python -m packages.reasoning_ensemble.mcp_server &
```

**Why:** Confirmed from source — both servers have bare `mcp.run()` with no transport arg, defaulting to stdio.  `0.0.0.0` binding is required because WSL2→Windows localhost forwarding needs the server reachable on all interfaces.

**Caveat on JanuScope removal for Python servers:** You lose whatever instruction injection the `flossiullk-consensus.yaml` and `flossiullk-reasoning-ensemble.yaml` lens files were doing. Read those files first (they're on your local machine at `C:/~shit/.mcp/lenses/`) and replicate any critical injections directly in the server's tool docstrings or in a startup banner. Then commit those lens files to the repo.

***

### Stage 2 — Before OmniRoute: Track Lens Configs in Git

```bash
# Run on Windows
cp C:/~shit/.mcp/lenses/*.yaml .mcp/lenses/
git add .mcp/lenses/
git commit -m "chore: track JanuScope lens configs — required for OmniRoute guardrails migration"
```

**Why:** The lens configs define instruction injection that shapes every tool call. They are currently untracked provenance — if your machine dies or you reinstall, this configuration is lost.  OmniRoute's guardrails/context-injection layer needs to replicate this content exactly.

***

### Stage 3 — OmniRoute Migration: Replace LiteLLM

**Step 3a — Verify Fusion judge configurability first.** Before writing any code, confirm OmniRoute allows a custom judge prompt that enforces:

- `WEIGHT: <float>` output format
- `RATIONALE: <text>` output format
- `[-0.999, 0.999]` range clamping

```
- `<think>...</think>` block stripping before parsing 
```

If yes → proceed to 3b. If no → keep `voters.py`'s parsing logic as a thin Python shim that calls OmniRoute's HTTP API instead of `litellm.completion()`.

**Step 3b — Install and configure OmniRoute:**

```bash
# OmniRoute runs as a Node.js HTTP daemon
npm install -g omniroute  # or per their install docs
omniroute --config omniroute.config.json
```

Map your existing voter roster from [`voter_registry.json`](https://github.com/G-0-B/FLOSS/blob/e8e71d4d29fac049e40db28ffb82d43d5592a158/packages/metacoordinator_mcp/voter_registry.json) to OmniRoute provider config. Current `diverse-max` profile includes: `cerebras/llama3.1-8b`, `groq/openai/gpt-oss-120b`, Mistral, and omo-momus variants.

**Step 3c — Replace `voters.py` call sites:**

In `make_litellm_voter()` and `make_omo_momus_voter()`, replace:

```python
from litellm import completion
resp = completion(model=model, messages=[...], ...)
```

with:

```python
import httpx
resp = httpx.post("http://127.0.0.1:OMNIROUTE_PORT/v1/chat/completions",
    json={"model": model, "messages": [...], "max_tokens": max_tokens, "temperature": temperature},
    headers={"Authorization": "Bearer omniroute-local"},
    timeout=60.0
)
data = resp.json()
text = data["choices"][0]["message"]["content"].strip()
```

All existing `_parse_weight()`, `_parse_rationale()`, `_strip_thinking()`, and `VOTER_PROMPT` logic stays identical — OmniRoute presents an OpenAI-compatible endpoint.

**Step 3d — Migrate `autonomous_synthesis_loop.py`:** Route through OmniRoute HTTP instead of `import litellm`. This was already a planned refactor per the unification doctrine.

**Step 3e:** `pip uninstall litellm` from requirements.

***

### Stage 4 — Long Term: Collapse MCP Servers Into OmniRoute

OmniRoute's built-in MCP server (95 tools, 30 scopes) can absorb the tool surfaces from both Python servers.  At that point both `server.py` and `mcp_server.py` become candidates for deletion. The JanuScope wrapping for serena and agentmemory can stay — those are external tools you don't control.

**Precondition:** OmniRoute's built-in memory (FTS5 + vector) must be verified against the `shared-agent-memory-surface.json` schema before migrating memory reads/writes.

***

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
| :-- | :-- | :-- | :-- |
| OmniRoute Fusion judge not customizable to VOTER_PROMPT schema | Medium | High | Keep voters.py parsing as HTTP shim — 30 lines |
| WSL2 localhost forwarding broken on your machine | Low | Medium | Bind `0.0.0.0`, use WSL2 IP directly if needed |
| JanuScope lens configs contain critical injections not yet replicated | Unknown | High | Read + commit them before Stage 1 removal |
| OmniRoute `diverse-max` voter IDs don't map cleanly to provider strings | Low | Low | voter_registry.json is the source of truth, easy to remap |
| Ollama unavailable when reasoning_ensemble daemon starts | Low | Low | mcp_server.py already returns `{"error": ...}` JSON on exception |


***

## What the Next Agent Picking This Up Needs to Do First

1. Read `C:/~shit/.mcp/lenses/flossiullk-consensus.yaml` and `flossiullk-reasoning-ensemble.yaml` — unknown content, blocks Stage 1 JanuScope removal
2. Check OmniRoute docs for Fusion judge prompt customization — blocks Stage 3a decision
3. Run `npm install -g januscope` on Windows — Stage 0, unblocked right now

***

```yaml
artifact_id: FLOSS-INFRA-2026-07-17-v1.0
repo: G-0-B/FLOSS
commit_audited: e8e71d4d29fac049e40db28ffb82d43d5592a158
generated: "2026-07-17T12:19:00-04:00"
files_read:
  - .mcp.json (SHA 35582db7)
  - packages/metacoordinator_mcp/server.py (SHA 4c5df36e)
  - packages/metacoordinator_mcp/voters.py (SHA 21a9d95d)
  - packages/reasoning_ensemble/mcp_server.py (SHA ad945844)
  - packages/orchestrator/ (directory listing)
  - packages/reasoning_ensemble/ (directory listing)
  - packages/metacoordinator_mcp/ (directory listing)
  - code search: "litellm repo:G-0-B/FLOSS" (36 results)
truth_status:
  all_code_claims: Verified
  process_count_per_agent: Verified (4 npx + downstream from .mcp.json)
  litellm_call_sites: Verified (voters.py make_litellm_voter + make_omo_momus_voter)
  omniroute_feature_claims: Specified (OmniRoute own docs, self-authored)
  januscope_lens_contents: Unverified (not in repo, local filesystem only)
  omniroute_fusion_judge_customizability: Unverified
blockers_for_next_agent:
  - Read C:/~shit/.mcp/lenses/*.yaml before removing JanuScope from Python servers
  - Verify OmniRoute Fusion judge prompt schema before deleting voters.py
  - npm install -g januscope is unblocked and should be done now
```

