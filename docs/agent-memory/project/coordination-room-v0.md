---
id: project-coordination-room-v0
type: project
created: '2026-08-30'
status: active
applies_to:
- any-agent
source: grok_session
title: Coordination room v0 — claim a file before you write it
---

# Coordination room v0

**What:** Plane A MCP router so agents stop using the human as the bus. Exclusive **file-path** claims plus an append-only log. Does not write files, merge CRDTs, or decide truth.

**MCP name:** `flossiullk-coordination-room`  
**URL:** `http://127.0.0.1:7334/mcp`  
**Code:** `FLOSS/packages/coordination_room/`  
**Spec:** `FLOSS/docs/specs/coordination-room.spec.md`  
**Design:** `FLOSS/docs/superpowers/specs/2026-08-30-coordination-room-design.md`  
**Branch:** `feat/coordination-room` (`b757373`)  
**Log:** `.agent-surface/rooms/default/events.jsonl`

## How to use

1. `room_claim(agent_id, path)` before you write that path. Path is relative to the FLOSS checkout (e.g. `packages/foo.py`).
2. If the reply is `"error": "conflict"`, someone else holds it (`holder`). Do not write. Pick another path or wait.
3. `room_broadcast(agent_id, text)` for status. No claim required. 4 KiB cap.
4. `room_read(since_seq)` / `room_state()` to see claims and the log.
5. `room_release(agent_id, path)` when done.

Same agent re-claiming the same path is `ok`. Second agent is a **system conflict**, not a chat parse.

## Start (if the MCP is disconnected)

From `FLOSS/`, `PYTHONPATH` = that directory:

```
python -m packages.coordination_room.server
```

Binds `127.0.0.1:7334` only. Not yet in `start_mcp_daemons.ps1`. Do not start killed computer-use `:7333` unless the operator asks.

## Not this

- Not MELD (knowledge merge) — later slice.
- Not A2A (task handshake) — `feat/a2a-harness-mesh`.
- Not Layer 4.5 Claim/Vote. Not a controller. No pycrdt in v0.
- Do not put A2A inside `.mcp.json`. This server **is** MCP, correctly.

## Tests

`python -m pytest packages/coordination_room/tests -v` from `FLOSS/` (17 passed 2026-08-30).
