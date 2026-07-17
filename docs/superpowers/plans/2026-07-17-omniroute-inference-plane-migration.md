# OmniRoute Inference Plane + MCP Daemon Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the per-session MCP process sprawl (4× `npx januscope` Node procs + Python servers spawned fresh, uncontrolled, per agent) and the scattered `litellm` call sites into a **centralized persistent Plane A inference/tool plane**: OmniRoute as the one OpenAI-compatible model daemon, and the two FLOSSI0ULLK Python MCP servers as persistent PID-guarded HTTP daemons — reversibly, behind evidence gates.

**Architecture:** OmniRoute runs headless as a single background HTTP daemon (`:20128`) that all model calls route to via its OpenAI-compatible endpoint, keeping voters.py's existing fan-out + WEIGHT/RATIONALE parsing untouched (OmniRoute is a passthrough, not a replacement for consensus/ensemble logic). The consensus + reasoning-ensemble MCP servers convert from per-client stdio spawns to persistent `streamable-http` daemons bound to `127.0.0.1` with a PID-singleton guard, carrying the JanuScope lens `instructions:` injection inside `FastMCP(instructions=...)` and an in-server audit append. JanuScope stays (globally pinned) only for the external serena + agentmemory servers.

**Tech Stack:** Python 3.13 (`C:\Python313\python.exe`, `PYTHONPATH=C:/~shit/FLOSS`), `mcp` SDK 1.27.0 (FastMCP, supports `sse` + `streamable-http`), OmniRoute (Node.js, `npm i -g omniroute`), JanuScope (Node.js), `httpx` for OpenAI-compatible calls. Native Windows — **not WSL2**.

---

## Context

**Why this change:** Each agent session currently spawns 4 `npx -y januscope@latest` Node processes (each doing an npm version-check/re-download) plus the Python MCP servers via bare `mcp.run()` stdio — a one-process-per-client model with no PID guard and no shutdown handling. With multiple concurrent agents this produces 12+ Node + 6+ Python processes that never die and sit spinning on idle stdin, and (for the reasoning ensemble) multiple processes hammering the same local Ollama. The operator's stated pain (2026-07-17): *"each agent spawns 4 node.js and python scripts without process control, async eating CPU like cray cray."* Drivers confirmed: **process consolidation (primary)**, token-cost compression, and free-tier provider access.

**Origin:** External audit artifact `FLOSS-INFRA-2026-07-17-v1.0` (`.toilet/2026-7-17_OMNIROUTE_ARCHITECTURE_UPGRADE_MIGRATION.md`, by "Perplexity External Reality Scout"), audited against GitHub commit `e8e71d4d`. The local tree is ~14 commits ahead; this plan is corrected against the **verified local state** (see "Audit corrections" below) and the workspace's evidence-gate discipline (installation ≠ adoption; verify before deleting working infra).

**Intended outcome:** One persistent OmniRoute model daemon + two persistent PID-guarded MCP daemons, replacing the per-session spawn storm; `litellm` retired from the hot path once OmniRoute is proven equivalent; guardrail injection + audit preserved.

> **Plan-file location note:** the plan-mode harness requested `C:\Users\kalis\.claude\plans\…`, but an administrator write-policy confines writes to `C:\~shit`. This plan is therefore saved at the writing-plans skill's canonical in-workspace path instead.

---

## Audit corrections (verified against local tree — the executor MUST honor these)

| Audit claim | Reality (verified) | Consequence for this plan |
| --- | --- | --- |
| Lens yamls exist only outside git | **False** — all 4 `.mcp/lenses/*.yaml` + both `.mcp.json` are git-tracked & clean | The audit's "Stage 2: track lens configs" is **already done — skipped**. |
| Servers run in WSL2 → bind `0.0.0.0` | **False** — native Windows `C:\Python313`. | Bind **`127.0.0.1`**, never `0.0.0.0` (avoids needless network exposure). |
| Delete `server.py`/`mcp_server.py` into OmniRoute (audit Stage 4) | Those encode FLOSSI0ULLK consensus/ensemble domain logic OmniRoute has no equivalent for | **Non-goal.** OmniRoute replaces the *litellm router layer only*; the domain servers stay (daemonized). |
| Fusion judge must be customizable before migrating | Migration keeps voters.py's own fan-out + parsing; OmniRoute is an OpenAI-compatible passthrough | Fusion is **not a dependency**. Do not block on it. |
| SDK may need upgrade for HTTP | `mcp` 1.27.0 already supports `sse` + `streamable-http` | No SDK bump needed. |

**Also verified:** hooks (`hook_post_write.py`, `hook_bg_round.py`, `heartbeat.py`) import `GatewayTools`/`voters` **in-process as a library** — they do NOT go through the MCP servers. Daemonizing the servers therefore cannot break the autonomous path. But the hooks DO call `litellm` transitively via `voters.py`, so Stage 3's voter-transport change affects them — Stage 3 tests must include a hook-path smoke.

---

## Non-goals

- Deleting `server.py` / `mcp_server.py` (they stay as daemons).
- Replacing the consensus gate or reasoning-ensemble logic with OmniRoute Fusion (discards analog-vote semantics).
- Binding any daemon to `0.0.0.0` or a non-loopback interface.
- Removing JanuScope for serena / agentmemory (external tools; keep pinned).
- Touching Holochain wiring (`holochain_connector.py` remains unused — out of scope).

---

## Target architecture

```
Agent session  ──.mcp.json──┐
                            ├── serena                 -> januscope (PINNED) -> uvx serena   [stdio, external]
                            ├── agentmemory            -> januscope (PINNED) -> npx agentmemory[stdio, external]
                            ├── flossiullk-consensus   -> http://127.0.0.1:7331/mcp  ┐ persistent PID-guarded
                            └── flossiullk-reasoning   -> http://127.0.0.1:7332/mcp  ┘ FastMCP streamable-http daemons

model calls (voters.py, transport.py, autonomous_synthesis_loop.py, major_consolidation_sweep.py)
      └── httpx POST -> http://127.0.0.1:20128/v1/chat/completions  (OmniRoute headless daemon, OpenAI-compatible)
                              └── routes to groq / cerebras / mistral / openrouter / free providers, + compression
```

Startup: OmniRoute daemon + the two MCP daemons are launched once at logon (Windows Scheduled Task as `MSI\kalis`, per the `.hermes.md` heartbeat convention) — not per session.

---

## File structure

| Path | Create/Modify | Responsibility |
| --- | --- | --- |
| `FLOSS/packages/mcp_daemon.py` | Create | Shared daemon bootstrap: PID-singleton guard, signal cleanup, loopback bind, audit-append hook. Reused by both servers. |
| `FLOSS/packages/metacoordinator_mcp/server.py` | Modify (`__main__` + `_create_mcp`) | Use daemon bootstrap; pass lens `instructions` into `FastMCP`. |
| `FLOSS/packages/reasoning_ensemble/mcp_server.py` | Modify (`__main__` + `_create_mcp`) | Same. |
| `FLOSS/packages/omniroute_client.py` | Create | Single OpenAI-compatible completion + embedding helper (httpx) targeting OmniRoute; reused by all model call sites. |
| `FLOSS/packages/metacoordinator_mcp/voters.py` | Modify (3 `completion()` sites) | Route via `omniroute_client` behind `FLOSS_MODEL_BACKEND` flag; keep all parsing. |
| `FLOSS/packages/reasoning_ensemble/transport.py` | Modify (`_litellm_generate`, `_cloud_embed_fn`) | Same flag-gated routing. |
| `FLOSS/scripts/autonomous_synthesis_loop.py`, `major_consolidation_sweep.py` | Modify | Route through `omniroute_client`. |
| `.mcp.json` (root + `FLOSS/.mcp.json`) | Modify | Pin januscope; convert the 2 Python servers to `url` daemon entries. |
| `FLOSS/scripts/start_mcp_daemons.ps1` | Create | Launch OmniRoute + both MCP daemons idempotently; register Scheduled Task. |
| `FLOSS/scripts/probe_omniroute.py` | Create (temp, gate) | Verify OmniRoute serves each roster model OpenAI-compatibly. |
| `FLOSS/packages/tests/test_omniroute_client.py`, `test_mcp_daemon.py` | Create | Unit tests for the client + daemon guard. |
| `FLOSS/docs/adr/ADR-19-omniroute-inference-plane.md` | Create | Records the router-layer + daemon-plane decision; System blast radius; consensus-gated. |

---

## Stage 0 — Pin JanuScope (immediate CPU relief, independent, ~5 min)

Stops the npm version-check/re-download on every server spawn. Helps *now*, before the bigger migration; serena + agentmemory keep pinned januscope permanently.

### Task 0.1: Install januscope globally

- [ ] **Step 1: Install** — `npm install -g januscope` (Windows). Expected `added N packages`; verify `januscope --version`.

- [ ] **Step 2: Point all 4 `.mcp.json` entries at the pinned binary** — in BOTH `C:/~shit/.mcp.json` and `C:/~shit/FLOSS/.mcp.json`, change every server from `"command":"npx","args":["-y","januscope@latest","--config",".../<name>.yaml"]` to `"command":"januscope","args":["--config",".../<name>.yaml"]`. (The two Python entries are re-pointed again in Stage 1.)

- [ ] **Step 3: Verify** — restart one MCP-aware session; servers still connect; Task Manager shows a `januscope` node process, no `npx`, no npm version-check.

- [ ] **Step 4: Commit (both repos hold `.mcp.json`)**
```bash
git -C C:/~shit add .mcp.json && git -C C:/~shit commit -m "mcp: pin januscope (drop npx -y version-check on every spawn)"
git -C C:/~shit/FLOSS add .mcp.json && git -C C:/~shit/FLOSS commit -m "mcp: pin januscope (drop npx -y version-check on every spawn)"
```

---

## Stage 1 — Daemonize the two Python MCP servers (persistent, PID-guarded, injection + audit preserved)

### Task 1.1: Shared daemon bootstrap module

**Files:** Create `FLOSS/packages/mcp_daemon.py`; Test `FLOSS/packages/tests/test_mcp_daemon.py`

- [ ] **Step 1: Write the failing test**
```python
# FLOSS/packages/tests/test_mcp_daemon.py
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages import mcp_daemon

def test_stale_pid_is_overwritten(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "x.pid").write_text("999999999")  # almost-certainly-dead pid
    assert mcp_daemon.claim_singleton("x.pid") is True
    assert (tmp_path / "x.pid").read_text().strip() == str(os.getpid())

def test_live_pid_blocks_second_claim(tmp_path, monkeypatch):
    monkeypatch.setenv("FLOSS_AGENT_DIR", str(tmp_path))
    (tmp_path / "y.pid").write_text(str(os.getpid()))  # our pid = alive
    assert mcp_daemon.claim_singleton("y.pid") is False
```

- [ ] **Step 2: Run to verify it fails** — `C:\Python313\python.exe -m pytest FLOSS/packages/tests/test_mcp_daemon.py -v` → FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write `mcp_daemon.py`**
```python
"""Shared daemon bootstrap for FLOSSI0ULLK Python MCP servers.

Converts per-client stdio spawns into one persistent PID-guarded HTTP daemon.
Bind 127.0.0.1 ONLY (native Windows; never expose to the network). Carries the
former JanuScope lens instruction injection (passed into FastMCP) and appends a
per-tool-call audit line to the same janus-*-audit.jsonl sink the lens used.
"""
from __future__ import annotations
import atexit, json, os, signal, sys
from datetime import datetime, timezone
from pathlib import Path


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        return False
    except PermissionError:
        return True  # exists, owned by someone else


def claim_singleton(pid_filename: str) -> bool:
    """Return True if this process now owns the daemon slot, False if one is live."""
    pid_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
    pid_dir.mkdir(parents=True, exist_ok=True)
    pid_path = pid_dir / pid_filename
    if pid_path.exists():
        try:
            existing = int(pid_path.read_text().strip())
            if _pid_alive(existing):
                return False
        except ValueError:
            pass  # stale/corrupt -> overwrite
    pid_path.write_text(str(os.getpid()))
    atexit.register(lambda: pid_path.unlink(missing_ok=True))
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (pid_path.unlink(missing_ok=True), sys.exit(0)))
    return True


def audit_appender(sink: str):
    """Return callable(tool_name, payload) that appends one JSONL audit line."""
    sink_path = Path(sink)
    def _append(tool_name: str, payload: dict) -> None:
        try:
            sink_path.parent.mkdir(parents=True, exist_ok=True)
            row = {"ts": datetime.now(timezone.utc).isoformat(), "tool": tool_name, "payload": payload}
            with sink_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass  # audit is best-effort defense-in-depth, never fatal
    return _append


def run_http_daemon(mcp, *, pid_filename: str, port: int) -> None:
    """Claim the singleton slot, then serve FastMCP over streamable-http on loopback."""
    if not claim_singleton(pid_filename):
        print(f"[FLOSS MCP] already running on :{port}; exiting.", file=sys.stderr)
        sys.exit(0)
    mcp.run(transport="streamable-http", host="127.0.0.1", port=port)
```

- [ ] **Step 4: Run to verify pass** — `pytest FLOSS/packages/tests/test_mcp_daemon.py -v` → 2 passed.

- [ ] **Step 5: Commit**
```bash
git -C C:/~shit/FLOSS add packages/mcp_daemon.py packages/tests/test_mcp_daemon.py
git -C C:/~shit/FLOSS commit -m "mcp: add shared PID-guarded HTTP daemon bootstrap"
```

### Task 1.2: Wire both servers to the daemon bootstrap + carry lens injection

**Files:** Modify `FLOSS/packages/metacoordinator_mcp/server.py`, `FLOSS/packages/reasoning_ensemble/mcp_server.py`

- [ ] **Step 1: Pass the lens instruction text into FastMCP** — in each `_create_mcp()`, add a module constant `_SERVER_INSTRUCTIONS = """…"""` with the EXACT `instructions:` block from the matching lens, and pass `FastMCP(name=..., instructions=_SERVER_INSTRUCTIONS)`. This is delivered to clients on `initialize`, replicating JanuScope's injection.

  Consensus text (verbatim from `.mcp/lenses/flossiullk-consensus.yaml`):
  ```
  FLOSSIØULLK Consensus Gateway — passive router, not a controller.

  Invariants you MUST honor when using these tools:
  - Vote weights are analog floats in [-0.999, +0.999]. Never use ±1.0.
  - The gateway does not decide outcomes; it routes Claims to voters and
    appends Decisions. Treat outcomes as data, not directives.
  - blast_radius selection:
      Local     = routine, single-module change. APPROVE threshold 0.30.
      Module    = config/spec change spanning files. APPROVE 0.50.
      System    = cross-module architectural shift. APPROVE 0.60.
      Substrate = invariant-touching, OVERRIDE FORBIDDEN. APPROVE 0.85.
  - Every Claim is durable on the source chain. Submit only what you
    would commit to permanent provenance.
  - Voters are LLMs with different cognitive styles (model family +
    persona). Variance > polarization_threshold returns CONFLICT
    requiring human resolution, not more votes.
  ```
  Reasoning-ensemble text (verbatim from `.mcp/lenses/flossiullk-reasoning-ensemble.yaml`): the `FLOSSI0ULLK Reasoning Ensemble — reasoning aid, not authority.` block.

- [ ] **Step 2: Replace the `__main__` block in both servers**
  Consensus (`port 7331`, `consensus.pid`):
  ```python
  if __name__ == "__main__":
      if mcp is None:
          raise ImportError("MCP SDK not installed. Run: pip install mcp")
      from packages.mcp_daemon import run_http_daemon
      run_http_daemon(mcp, pid_filename="consensus.pid", port=7331)
  ```
  Ensemble (`port 7332`, `reasoning_ensemble.pid`): identical, with those two values.

- [ ] **Step 3: Start each daemon and verify endpoint + singleton**
  ```powershell
  $env:PYTHONPATH="C:/~shit/FLOSS"; C:\Python313\python.exe -m packages.metacoordinator_mcp.server
  $env:PYTHONPATH="C:/~shit/FLOSS"; C:\Python313\python.exe -m packages.reasoning_ensemble.mcp_server
  ```
  Verify tools list:
  ```powershell
  curl.exe -sS -X POST http://127.0.0.1:7331/mcp -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
  ```
  Expected: JSON-RPC listing `submit_claim, cast_vote, get_chain_context, get_decision, list_pending, run_consensus_round`. A SECOND launch of the same server prints `already running on :7331; exiting.` and exits 0.

- [ ] **Step 4: Commit**
```bash
git -C C:/~shit/FLOSS add packages/metacoordinator_mcp/server.py packages/reasoning_ensemble/mcp_server.py
git -C C:/~shit/FLOSS commit -m "mcp: run consensus + ensemble as persistent loopback HTTP daemons with injected instructions"
```

### Task 1.3: Point `.mcp.json` at the daemons; keep januscope for external servers

**Files:** Modify `C:/~shit/.mcp.json` and `C:/~shit/FLOSS/.mcp.json`

- [ ] **Step 1: Convert the two Python entries to `url` daemons**
```json
{
  "mcpServers": {
    "serena": { "command": "januscope", "args": ["--config", "C:/~shit/.mcp/lenses/serena.yaml"] },
    "flossiullk-consensus": { "type": "http", "url": "http://127.0.0.1:7331/mcp" },
    "flossiullk-reasoning-ensemble": { "type": "http", "url": "http://127.0.0.1:7332/mcp" },
    "agentmemory": { "command": "januscope", "args": ["--config", "C:/~shit/.mcp/lenses/agentmemory.yaml"] }
  }
}
```
(If the client rejects `type:"http"`, run the daemon with `transport="sse"` and use `{ "type":"sse", "url":"http://127.0.0.1:7331/sse" }`.)

- [ ] **Step 2: Verify a fresh session attaches, does not spawn** — with the daemons up, start a new agent session: consensus + ensemble tools available, **no new python process** for them; a second session spawns none either; the client shows the injected `instructions`.

- [ ] **Step 3: Commit both repos**
```bash
git -C C:/~shit add .mcp.json && git -C C:/~shit commit -m "mcp: connect consensus+ensemble via persistent HTTP daemon urls"
git -C C:/~shit/FLOSS add .mcp.json && git -C C:/~shit/FLOSS commit -m "mcp: connect consensus+ensemble via persistent HTTP daemon urls"
```

### Task 1.4: Boot-time launcher (Scheduled Task, `MSI\kalis`)

**Files:** Create `FLOSS/scripts/start_mcp_daemons.ps1`

- [ ] **Step 1: Write the launcher (idempotent — PID guard makes re-runs safe)**
```powershell
# FLOSS/scripts/start_mcp_daemons.ps1 — start OmniRoute + both MCP daemons if not already up.
$py = "C:\Python313\python.exe"; $env:PYTHONPATH = "C:/~shit/FLOSS"
Start-Process -WindowStyle Hidden $py "-m packages.metacoordinator_mcp.server"
Start-Process -WindowStyle Hidden $py "-m packages.reasoning_ensemble.mcp_server"
# OmniRoute (enabled in Stage 4): Start-Process -WindowStyle Hidden "omniroute" "--no-open"
```

- [ ] **Step 2: Register a logon Scheduled Task**
```powershell
schtasks /Create /TN "FLOSS-MCP-Daemons" /TR "powershell -WindowStyle Hidden -File C:\~shit\FLOSS\scripts\start_mcp_daemons.ps1" /SC ONLOGON /RU "MSI\kalis" /RL LIMITED /F
```
Expected `SUCCESS`. Verify `schtasks /Run /TN "FLOSS-MCP-Daemons"` starts the daemons; re-running creates no duplicates (PID guard).

- [ ] **Step 3: Commit**
```bash
git -C C:/~shit/FLOSS add scripts/start_mcp_daemons.ps1
git -C C:/~shit/FLOSS commit -m "mcp: boot-time launcher + scheduled task for daemons"
```

---

## Stage 2 — SKIP (already satisfied)

The audit's "track lens configs in git" is **already done**: `.mcp/lenses/{serena,flossiullk-consensus,flossiullk-reasoning-ensemble,agentmemory}.yaml` are git-tracked and clean (`git ls-files` confirms). No action.

---

## Stage 3 — OmniRoute as the model-call plane (replace litellm, evidence-gated)

### Task 3.1: Install + configure OmniRoute headless

- [ ] **Step 1: Install and seed config** — `npm install -g omniroute`; `omniroute setup --non-interactive`. Expected install ok; `~/.omniroute/` created. Note `omniroute --version`.
- [ ] **Step 2: Add provider keys from `FLOSS/.env`** — GROQ / CEREBRAS / MISTRAL / OPENROUTER, via `omniroute setup --non-interactive --add-provider --provider <p> --api-key <k>` (or dashboard Providers once). Create a local API key; store as `OMNIROUTE_API_KEY` in `FLOSS/.env` (+ key name in `.env.example`).
- [ ] **Step 3: Run headless and confirm endpoint**
  ```powershell
  Start-Process -WindowStyle Hidden "omniroute" "--no-open"
  curl.exe -sS http://127.0.0.1:20128/v1/models -H "Authorization: Bearer $env:OMNIROUTE_API_KEY"
  ```
  Expected a JSON model list (use `PORT=20128 DASHBOARD_PORT=20129 omniroute --no-open` if split-port needed).

### Task 3.2: GATE — prove OmniRoute serves the roster before touching voters.py

**Files:** Create `FLOSS/scripts/probe_omniroute.py` (temporary; delete after)

- [ ] **Step 1:** Write a probe that, for each unique model in `packages/metacoordinator_mcp/voter_registry.json`, POSTs a 1-token prompt to `http://127.0.0.1:20128/v1/chat/completions` (Bearer `OMNIROUTE_API_KEY`) and reports OK/ERR + the served model-ID. (Mirror the structure of the 2026-07-16 roster probe.)
- [ ] **Step 2: Run + record mapping** — `C:\Python313\python.exe FLOSS/scripts/probe_omniroute.py`. **Gate:** every roster model resolves with the same `provider/model` string → migrate all; any that don't → keep on litellm via the flag (record in ADR); confirm WEIGHT/RATIONALE + `<think>` round-trip unchanged. **Never drop a model to make the migration cleaner.**
- [ ] **Step 3:** `rm FLOSS/scripts/probe_omniroute.py`.

### Task 3.3: Shared OmniRoute client (test-first)

**Files:** Create `FLOSS/packages/omniroute_client.py`; Test `FLOSS/packages/tests/test_omniroute_client.py`

- [ ] **Step 1: Write the failing test**
```python
# FLOSS/packages/tests/test_omniroute_client.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from packages import omniroute_client as oc

def test_completion_posts_openai_shape(monkeypatch):
    seen = {}
    class FakeResp:
        status_code = 200
        text = ""
        def json(self): return {"choices": [{"message": {"content": "WEIGHT: 0.5\nRATIONALE: ok"}}]}
    def fake_post(url, json=None, headers=None, timeout=None):
        seen.update(url=url, json=json, headers=headers); return FakeResp()
    monkeypatch.setattr(oc.httpx, "post", fake_post)
    monkeypatch.setenv("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1")
    monkeypatch.setenv("OMNIROUTE_API_KEY", "k")
    text = oc.completion("groq/openai/gpt-oss-20b", [{"role": "user", "content": "hi"}], max_tokens=8, temperature=0.1)
    assert text == "WEIGHT: 0.5\nRATIONALE: ok"
    assert seen["url"].endswith("/v1/chat/completions")
    assert seen["json"]["model"] == "groq/openai/gpt-oss-20b"
    assert seen["headers"]["Authorization"] == "Bearer k"
```

- [ ] **Step 2: Run to verify fail** — `pytest FLOSS/packages/tests/test_omniroute_client.py -v` → FAIL (no module).

- [ ] **Step 3: Implement `omniroute_client.py`**
```python
"""OpenAI-compatible client for the local OmniRoute daemon. One helper, reused
by every model call site so litellm can be retired from the hot path."""
from __future__ import annotations
import os
import httpx

def _base() -> str:
    return os.environ.get("OMNIROUTE_BASE_URL", "http://127.0.0.1:20128/v1").rstrip("/")

def _headers() -> dict:
    return {"Authorization": f"Bearer {os.environ.get('OMNIROUTE_API_KEY', 'omniroute-local')}",
            "Content-Type": "application/json"}

def completion(model: str, messages: list[dict], *, max_tokens: int = 2000,
               temperature: float = 0.1, timeout: float = 60.0) -> str:
    resp = httpx.post(f"{_base()}/chat/completions",
                      json={"model": model, "messages": messages,
                            "max_tokens": max_tokens, "temperature": temperature},
                      headers=_headers(), timeout=timeout)
    if resp.status_code >= 400:
        raise RuntimeError(f"OmniRoute HTTP {resp.status_code}: {resp.text[:200]!r}")
    return (resp.json()["choices"][0]["message"]["content"] or "").strip()

def embedding(model: str, text: str, *, timeout: float = 60.0) -> list[float]:
    resp = httpx.post(f"{_base()}/embeddings", json={"model": model, "input": [text]},
                      headers=_headers(), timeout=timeout)
    if resp.status_code >= 400:
        raise RuntimeError(f"OmniRoute embeddings HTTP {resp.status_code}: {resp.text[:200]!r}")
    return list(resp.json()["data"][0]["embedding"])
```

- [ ] **Step 4: Run to verify pass** — `pytest FLOSS/packages/tests/test_omniroute_client.py -v` → PASS.
- [ ] **Step 5: Commit**
```bash
git -C C:/~shit/FLOSS add packages/omniroute_client.py packages/tests/test_omniroute_client.py
git -C C:/~shit/FLOSS commit -m "inference: add OpenAI-compatible OmniRoute client helper"
```

### Task 3.4: Flag-gated routing at every call site (hybrid, reversible)

Add `FLOSS_MODEL_BACKEND` env: `litellm` (default until proven) | `omniroute`.

**Files:** Modify `voters.py` (3 `completion()` closures), `transport.py` (`_litellm_generate`, `_cloud_embed_fn`), `scripts/autonomous_synthesis_loop.py`, `scripts/major_consolidation_sweep.py`

- [ ] **Step 1: In `voters.py`, wrap each completion closure**
```python
import os
if os.environ.get("FLOSS_MODEL_BACKEND", "litellm") == "omniroute":
    from packages.omniroute_client import completion as _omni
    text = _omni(model, messages, max_tokens=max_tokens, temperature=temperature)
else:
    from litellm import completion
    resp = completion(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
    text = (resp.choices[0].message.content or "").strip()
```
Keep `_strip_thinking` / `_parse_weight` / `_parse_rationale` unchanged. Apply to `make_litellm_voter`, `make_omo_momus_voter`, `make_omo_critic_voter`.

- [ ] **Step 2: `transport.py`** — `_litellm_generate` → when backend=omniroute call `omniroute_client.completion(model, [{"role":"user","content":prompt}], max_tokens=600, temperature=0.4)`. `_cloud_embed_fn` → `omniroute_client.embedding(model, text)` ONLY if Task 3.2 confirmed OmniRoute serves embeddings; otherwise leave on litellm/mistral-embed and note it.

- [ ] **Step 3:** `autonomous_synthesis_loop.py` + `major_consolidation_sweep.py` — same backend branch.

- [ ] **Step 4: Existing unit tests still green** — run `test_transport.py` + `test_voters.py`; default stays litellm so they pass unchanged.

- [ ] **Step 5: Commit**
```bash
git -C C:/~shit/FLOSS add packages/metacoordinator_mcp/voters.py packages/reasoning_ensemble/transport.py scripts/autonomous_synthesis_loop.py scripts/major_consolidation_sweep.py
git -C C:/~shit/FLOSS commit -m "inference: flag-gated OmniRoute routing at all litellm call sites (FLOSS_MODEL_BACKEND)"
```

### Task 3.5: Live equivalence run (litellm baseline vs OmniRoute)

- [ ] **Step 1: Baseline (litellm)** — `$env:FLOSS_MODEL_BACKEND="litellm"; C:\Python313\python.exe FLOSS/scripts/smoke_test_voters.py` → PASS; records votes/outcome.
- [ ] **Step 2: OmniRoute** — `$env:FLOSS_MODEL_BACKEND="omniroute"; …smoke_test_voters.py` → PASS; all voters parseable; no `[voter error]`; sane variance.
- [ ] **Step 3: Hook-path smoke** — trigger `hook_bg_round.py` with backend=omniroute on a throwaway claim; a full round completes via OmniRoute.
- [ ] **Step 4: Flip default** — set `FLOSS_MODEL_BACKEND=omniroute` in `FLOSS/.env` (+ `.env.example`). Commit `inference: default model backend to OmniRoute after equivalence check`.

### Task 3.6: Retire litellm from the hot path (evidence-gated)

- [ ] **Step 1:** Only after 3.5 is green across several days of real use, remove the litellm branches (or keep them as a documented fallback behind the flag). If OmniRoute embeddings were NOT confirmed in 3.2, keep the litellm/mistral-embed path for `_cloud_embed_fn`.
- [ ] **Step 2:** If fully removing: `pip uninstall litellm`, delete the branches, run the full test floor, commit `inference: retire litellm from hot path (OmniRoute proven)`.

---

## Stage 4 — Wire OmniRoute into the boot launcher + ADR/provenance

### Task 4.1: Add OmniRoute to `start_mcp_daemons.ps1`
- [ ] Enable the `omniroute --no-open` line; verify a logon starts all three daemons; idempotency holds. Commit.

### Task 4.2: ADR-19 + consensus provenance (workspace convention)
Changes a shared invariant (model-router layer + MCP transport plane) → **System blast radius → ADR + consensus claim** (per `.hermes.md`: canon changes need spec/ADR + provenance).
- [ ] **Step 1:** Write `FLOSS/docs/adr/ADR-19-omniroute-inference-plane.md` (decision, options: keep-litellm / hybrid / full; consequences; the verified corrections). Update `FLOSS/docs/adr/INDEX.md` + root `INDEX.md`.
- [ ] **Step 2:** `submit_claim` (proposal_type=AdrChange, blast_radius=System) with evidence = ADR commit + passing smoke runs; `run_consensus_round`; record the decision id in the ADR. (System threshold 0.60; governed gate needs provenance_packet + consent ref — attach them.)
- [ ] **Step 3:** Commit ADR + INDEX rows.

---

## Risk register (corrected)

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| OmniRoute doesn't serve some roster model / different model-ID scheme | Medium | Medium | Task 3.2 gate maps every model first; keep unmapped on litellm via the flag. |
| OmniRoute embeddings absent/weak | Medium | Low | Keep `_cloud_embed_fn` on litellm/mistral-embed; embeddings are a small separable path. |
| Dropping JanuScope loses guardrail injection + audit | High if unhandled | Medium | Injection → `FastMCP(instructions=…)`; audit → `audit_appender`. Verify client sees instructions (Task 1.3 Step 2). |
| `.mcp.json` client rejects `type:"http"` | Low | Low | Fall back to `sse` transport + `type:"sse"`. |
| OmniRoute young project / breaking changes | Medium | Medium | Pin installed version; litellm stays behind the flag until 3.6; never uninstall before a real-use soak. |
| Scheduled Task wrong principal | Low | Low | `/RU "MSI\kalis"`; verify `schtasks /Query`. |
| Compression/free-provider config undocumented | Medium | Low | Post-migration spike; not on the critical path (core win is consolidation + OpenAI-compat routing). |

---

## End-to-end verification

1. **Process count:** with 2 concurrent sessions, Task Manager shows ONE `omniroute`, ONE consensus daemon, ONE ensemble daemon, and pinned `januscope` only for serena/agentmemory — not per-session multiples. (Was: 12+ Node + 6+ Python.)
2. **MCP daemons:** `curl tools/list` on `:7331/mcp` + `:7332/mcp` returns the expected tools; a second launch self-exits via PID guard; client shows injected `instructions`.
3. **Model plane:** `smoke_test_voters.py` PASSES with `FLOSS_MODEL_BACKEND=omniroute`; a live `run_consensus_round` and a live ensemble `deliberate` complete through OmniRoute with parseable output.
4. **Hooks unbroken:** a `hook_bg_round.py` round completes via OmniRoute in-process.
5. **Audit preserved:** `.agent-surface/heartbeat/janus-*-audit.jsonl` still receive tool-call rows (from the in-server appender).
6. **Provenance:** ADR-19 committed + a System-radius consensus decision recorded.

---

## Self-review notes

- **Spec coverage:** Stage 0 (janus pin), Stage 1 (daemonize + injection + audit + launcher), Stage 2 (already done), Stage 3 (OmniRoute install/gate/client/routing/equivalence/retire), Stage 4 (boot + ADR/provenance) — all map to the operator's drivers (consolidation primary; compression + free providers via OmniRoute; retained guardrails).
- **Reuse honored:** shared `mcp_daemon.py` (both servers), shared `omniroute_client.py` (all call sites), existing `_parse_weight`/`_strip_thinking`/`resolve_default_voter_specs` untouched, existing smoke tests as the equivalence harness.
- **Reversibility:** every model-routing change is behind `FLOSS_MODEL_BACKEND` with litellm as the default until proven; litellm is not uninstalled until a real-use soak (3.6).
- **Type consistency:** `claim_singleton(pid_filename)->bool`, `run_http_daemon(mcp,*,pid_filename,port)`, `omniroute_client.completion(model,messages,*,max_tokens,temperature,timeout)->str`, `.embedding(model,text)->list[float]` used consistently across tasks.
