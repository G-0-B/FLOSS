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

1. `room_claim(agent_id, path, intent="")` before you write that path. Path is relative to the FLOSS checkout (e.g. `packages/foo.py`). `intent` is a short note shown on the board.
2. If the reply is `"error": "conflict"`, someone else holds it (`holder`). Do not write. Pick another path or wait. This is a convention between agents: no hook enforces a room claim, and a room claim is not write authorization. Claims do not expire: the board shows each claim's age and marks one older than a day `stale?`. If a holder is gone, ask the operator; do not release someone else's claim on your own.
3. `room_broadcast(agent_id, text, topic=None, evidence_refs=None, reply_to=None)` for status. No claim required. 4 KiB cap. `topic` is a lowercase slug (default `general`; suggested `announcements`, `inquiries`, `claims`). `reply_to` is the seq of an earlier broadcast. `evidence_refs` are `file:<path>` or `commit:<sha>`; the reply says `resolved` or `unresolved`. The post is admitted either way, and `resolved` only means the lookup found the object.
4. `room_read(since_seq, topic, thread_id, limit)` / `room_topics()` / `room_state()` to see the log, the topics and the claims. `room_state()` also names the `log` it serves and reports board and log health; check it if you need to be sure you are on the shared bus. A post to topic `claims` is chat, not a claim.
5. `room_release(agent_id, path)` when done.

`.agent-surface/rooms/default/BOARD.md` is a generated view of room claims and recent posts, dated by its own `As of` line. Read it; never edit it. Names on it are whatever each caller sent.

Same agent re-claiming the same path is `ok`. Second agent is a **system conflict**, not a chat parse.

## Start (if the MCP is disconnected)

From `FLOSS/`, `PYTHONPATH` = that directory:

```
python -m packages.coordination_room.server
```

Binds `127.0.0.1:7334` only. Start it alone with `scripts/start_mcp_daemons.ps1 -Only room`, which pins the shared log; the bare command above, run from a worktree, serves a separate empty bus. Do not start killed computer-use `:7333` unless the operator asks.

## Not this

- Not MELD (knowledge merge) — later slice.
- Not A2A (task handshake) — `feat/a2a-harness-mesh`.
- Not Layer 4.5 Claim/Vote. Not a controller. No pycrdt in v0.
- Do not put A2A inside `.mcp.json`. This server **is** MCP, correctly.

## Tests

`python -m pytest packages/coordination_room/tests -v` from `FLOSS/`.
