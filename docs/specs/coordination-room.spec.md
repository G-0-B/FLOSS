# Coordination Room — File-Claim MCP Router

```yaml
id: "coordination-room-spec"
version: "0.1.0"
kind: "spec"
status: "Active"
created: "2026-08-30"
truth_status: "Specified; unit tests Verified on landing"
schema: "coordination-room.schema.json"
approval: "Operator yes-to-everything 2026-08-30"
```

## What this is

A Plane A **router** for concurrent coding agents. File-level exclusive claims plus an append-only broadcast log, exposed as MCP tools. It does not write the claimed files, merge CRDT bytes, or decide truth.

Compose the computer-use **lease shape** (one exclusive holder). Do not share that table. Do not build an AgentOS. No pycrdt in v0 (AgentRoom measured coordination tools, not the CRDT, as the load-bearing step).

## Claim unit

Normalized file path relative to the room root. One exclusive holder. Same-agent re-claim is idempotent. Second agent gets `conflict` plus the holder id.

## Tools

`room_claim` | `room_release` | `room_state` | `room_broadcast` | `room_read`

Broadcast does not require a claim. `text` max 4096 bytes.

## Runtime

- Package: `FLOSS/packages/coordination_room/`
- HTTP: `127.0.0.1:7334/mcp` (PID `coordination_room.pid`)
- Log: `.agent-surface/rooms/default/events.jsonl` (workspace root)

## Falsifiers

Retire if: two exclusive holders on one path succeed; a conflict is only visible as chat; daemon binds non-loopback; log is rewritten in place.
