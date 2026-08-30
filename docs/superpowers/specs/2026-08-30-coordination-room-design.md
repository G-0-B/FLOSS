# Coordination Room v0 — Design

```yaml
date: "2026-08-30"
status: "Approved (operator: yes to everything)"
slice: "file-claim coordination room, not MELD merge"
```

Plane A **router**, not a controller. Answers who may write a path and what peers just said. Does not write workspace files, merge bytes, or adjudicate truth.

## Architecture

- Package: `FLOSS/packages/coordination_room/`
- Bind: `127.0.0.1:7334/mcp` only. Do not start killed `:7333`. Do not touch consensus/provenance.
- Claim unit: file path relative to room root (FLOSS checkout unless `COORDINATION_ROOM_ROOT` set).
- Tools: `room_claim`, `room_release`, `room_state`, `room_broadcast`, `room_read`.
- Durable log: workspace `.agent-surface/rooms/default/events.jsonl`.
- v0 no: pycrdt, task claims, desktop leases, `start_mcp_daemons.ps1`.

## Components

- **PathNorm** — root-relative posix key; reject `..` escape.
- **ClaimTable** — one exclusive holder per path (lease-shaped, not the computer-use table).
- **EventLog** — append-only JSONL; `claim` / `release` / `broadcast`; monotonic `seq`.
- **Gateway** — JSON tools over FastMCP. Replay log into ClaimTable on boot.

## Conflict

Second `room_claim` on a held path returns `conflict` + holder id at the table. Same agent re-claim is idempotent `ok`. Broadcast does not require a claim. `text` cap 4096 bytes.

## Testing

Unit tests for PathNorm, ClaimTable, log replay, gateway JSON. No live daemon required for the suite.

## MCP wire

Add `flossiullk-coordination-room` HTTP `http://127.0.0.1:7334/mcp` to root and FLOSS `.mcp.json` and `shared-agent-surface.json` vibe list. Daemon is opt-in; tests do not start it.
