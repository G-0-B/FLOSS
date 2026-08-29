# Local A2A Harness Mesh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove a local A2A pair, turn on Hermes as the first native A2A peer, and leave the MCP mesh as the tool/context plane for Claude Code, Antigravity, Grok, and Perplexity.

**Architecture:** A2A is advertisement and task delegation between peers, not a controller. MCP (root `.mcp.json`) stays source of truth for tools. Layer 4.5 remains a Claim/Vote router; A2A never bypasses it. Non-native harnesses get optional adapters later, not ASAP rewrites.

**Tech Stack:** Python 3.13, pytest, official `a2a-sdk` (a2a-python), Hermes `gateway.platforms.a2a` (port 9900), existing MCP daemons on 7331/7332.

**Research:** Grok workflow `deep-research` 2026-08-29 (Partial). Full report: session workflow scratch. Digested policy: `docs/research/2026-05-22-open-distributed-intelligence-digestion.md` — MCP now, A2A later as handshake.

**Working directory:** Paths relative to `C:\~shit\FLOSS` unless prefixed with `../`. Commit in the FLOSS repo.

**Run tests with:** `C:\Python313\python.exe -m pytest packages/a2a_mesh/tests -v` from `C:\~shit\FLOSS` after Task 1 lands the package.

## Global Constraints

- Do not replace `.mcp.json` or Layer 4.5 with A2A.
- Do not treat A2A as a commanding orchestrator.
- Do not invert Hermes into a controller; it stays an MCP client of consensus/ensemble.
- Do not wire GongRzhe/A2A-MCP-Server (archived 2026-03-03).
- Do not require consensus/provenance repair (operator: foundational issues in-flight).
- Production A2A wants HTTPS; local loopback JSON-RPC on 127.0.0.1 is the v0 interop gate.
- Agent Card well-known path: `GET /.well-known/agent-card.json`.
- Bindings: JSON-RPC is the tutorial default; do not invent a fourth binding.
- Computer-use gateway (`:7333`) is out of this plan; it joins start/stop scripts later.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `packages/a2a_mesh/helloworld.py` | Loopback Agent Card + JSON-RPC executor | Create |
| `packages/a2a_mesh/client.py` | Card resolve + SendMessage | Create |
| `packages/a2a_mesh/tests/test_helloworld_pair.py` | Spec-minimum interop gate | Create |
| `packages/a2a_mesh/tests/test_invariants.py` | A2A does not replace MCP / does not decide | Create |
| `../.hermes.md` or operator note in this plan Task 2 | Hermes A2A enablement (config, not code) | Operator |
| `docs/research/2026-08-29-a2a-harness-mesh-research.md` | Pointer to research result + harness matrix | Create (short) |

Do not add an A2A server to `.mcp.json`. That file is MCP only.

---

### Task 1: Local helloworld pair (spec-minimum gate)

Prove two Python processes can discover a card and SendMessage on loopback. Independent of any harness.

**Files:**
- Create: `packages/a2a_mesh/helloworld.py`
- Create: `packages/a2a_mesh/client.py`
- Create: `packages/a2a_mesh/__init__.py`
- Create: `packages/a2a_mesh/tests/test_helloworld_pair.py`
- Modify: `requirements.txt` only if `a2a-sdk` is missing (pin the version the test imports).

**Interfaces:**
- Consumes: official `a2a-sdk` Agent Card routes + JSON-RPC routes
- Produces: `serve_helloworld(host: str, port: int) -> None`, `send_hello(base_url: str, text: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
"""Spec-minimum A2A pair: card GET then SendMessage."""

from __future__ import annotations

import threading
import time

import httpx
import pytest

from packages.a2a_mesh.client import send_hello
from packages.a2a_mesh.helloworld import serve_helloworld

HOST, PORT = "127.0.0.1", 19999


def test_agent_card_is_served_at_well_known():
    t = threading.Thread(
        target=serve_helloworld, kwargs={"host": HOST, "port": PORT}, daemon=True
    )
    t.start()
    time.sleep(0.4)
    r = httpx.get(f"http://{HOST}:{PORT}/.well-known/agent-card.json", timeout=5)
    assert r.status_code == 200
    card = r.json()
    assert "name" in card
    assert "supportedInterfaces" in card or "url" in card


def test_send_hello_round_trips():
    t = threading.Thread(
        target=serve_helloworld, kwargs={"host": HOST, "port": PORT}, daemon=True
    )
    t.start()
    time.sleep(0.4)
    text = send_hello(f"http://{HOST}:{PORT}", "ping")
    assert isinstance(text, str)
    assert len(text) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest packages/a2a_mesh/tests/test_helloworld_pair.py -v`
Expected: FAIL with `ModuleNotFoundError: packages.a2a_mesh` or import of `serve_helloworld`

- [ ] **Step 3: Write minimal implementation**

Use the official Python quickstart pattern (`create_agent_card_routes`, `create_jsonrpc_routes`, `DefaultRequestHandler`, `InMemoryTaskStore`). Client: `A2ACardResolver` then `SendMessage`. Bind `127.0.0.1` only. Name the agent `flossi0ullk-a2a-helloworld`. Do not attach it to the consensus gateway.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest packages/a2a_mesh/tests/test_helloworld_pair.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/a2a_mesh requirements.txt
git commit -m "feat: local A2A helloworld pair on loopback"
```

---

### Task 2: Invariant tests (A2A is not the tool bus)

**Files:**
- Create: `packages/a2a_mesh/tests/test_invariants.py`

**Interfaces:**
- Consumes: Task 1 module
- Produces: tests that fail if someone registers A2A inside `.mcp.json` as if it were MCP

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[4]  # workspace root C:\~shit


def test_root_mcp_json_has_no_a2a_server_key():
    data = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    names = set(data.get("mcpServers", {}))
    assert "a2a" not in {n.lower() for n in names}
    assert "flossiullk-a2a" not in names


def test_helloworld_agent_name_is_not_controller():
    from packages.a2a_mesh.helloworld import AGENT_NAME

    assert AGENT_NAME == "flossi0ullk-a2a-helloworld"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest packages/a2a_mesh/tests/test_invariants.py -v`
Expected: FAIL until `AGENT_NAME` exists; MCP key test should already PASS

- [ ] **Step 3: Export `AGENT_NAME` from helloworld.py**

```python
AGENT_NAME = "flossi0ullk-a2a-helloworld"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest packages/a2a_mesh/tests/test_invariants.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add packages/a2a_mesh
git commit -m "test: A2A mesh does not enter .mcp.json"
```

---

### Task 3: Hermes as first native A2A peer (config, not a new protocol)

Hermes already serves `GET /.well-known/agent-card.json` and JSON-RPC `POST /` on default port 9900 when `gateway.platforms.a2a` is enabled.

**Files:**
- Modify: operator `~/.hermes/config.yaml` (user scope — do not commit secrets)
- Create: `packages/a2a_mesh/tests/test_hermes_card_optional.py` (skip if Hermes down)

**Interfaces:**
- Consumes: live Hermes if present
- Produces: skip-or-pass probe, never a hard CI fail when Hermes is off

- [ ] **Step 1: Write the optional probe**

```python
import os
import pytest
import httpx

HERMES = os.environ.get("FLOSS_HERMES_A2A", "http://127.0.0.1:9900")


@pytest.mark.skipif(
    os.environ.get("FLOSS_PROBE_HERMES_A2A") != "1",
    reason="set FLOSS_PROBE_HERMES_A2A=1 when Hermes A2A is running",
)
def test_hermes_serves_agent_card():
    r = httpx.get(f"{HERMES}/.well-known/agent-card.json", timeout=5)
    assert r.status_code == 200
    card = r.json()
    assert "name" in card
```

- [ ] **Step 2: Run without env — expect SKIP**

Run: `python -m pytest packages/a2a_mesh/tests/test_hermes_card_optional.py -v`
Expected: SKIPPED

- [ ] **Step 3: Operator enables Hermes A2A**

In `~/.hermes/config.yaml`, enable `gateway.platforms.a2a` (default 9900). Restart Hermes. Do not point Hermes at consensus as a *controller*. Keep existing MCP client entries for `flossiullk-consensus` / ensemble.

- [ ] **Step 4: Probe with env**

Run: `$env:FLOSS_PROBE_HERMES_A2A=1; python -m pytest packages/a2a_mesh/tests/test_hermes_card_optional.py -v`
Expected: PASS if Hermes is up; FAIL only means config/process, not a protocol rewrite

- [ ] **Step 5: Commit tests only**

```bash
git add packages/a2a_mesh/tests/test_hermes_card_optional.py
git commit -m "test: optional Hermes A2A agent-card probe"
```

---

### Task 4: Research pointer (so the next session does not re-derive)

**Files:**
- Create: `docs/research/2026-08-29-a2a-harness-mesh-research.md`

This is a short distillation (not a second grand synthesis). Table: Claude Code / Antigravity / Grok / Hermes / Perplexity native A2A vs MCP. Policy: complementary layers. Adapters (OCC, a2abridge) listed as **optional later**, not this plan's implementation.

- [ ] **Step 1: Write the distillation** (copy harness table + complementary-layer rule from the 2026-08-29 research result)
- [ ] **Step 2: Link this plan from the distillation**
- [ ] **Step 3: Commit**

```bash
git add docs/research/2026-08-29-a2a-harness-mesh-research.md
git commit -m "docs: A2A harness mesh research pointer"
```

Do not implement orbital-command-centre or a2abridge in this plan. Concrete peer-task need first.

---

## Out of scope (separate plans if needed)

- OCC wrap of Grok (`occ-a2a --agent grok`) and Antigravity (`agy -p`)
- a2abridge directory on `127.0.0.1:7777` for Claude Code
- Mapping A2A Task state onto ADR-12 ConsentPayload
- Counting an A2A remote as a voter toward ≥3 surfaces / ≥4 families
- OmniRoute `/.well-known/agent.json` claim (unverified vs ADR-19)

## Self-review

- Spec coverage: local pair, Hermes peer, MCP stays, no controller, no archived bridge — each has a task. Adapters deferred on purpose (YAGNI).
- Placeholders: none of TBD / implement later / similar to Task N.
- Types: `serve_helloworld`, `send_hello`, `AGENT_NAME` used consistently.
