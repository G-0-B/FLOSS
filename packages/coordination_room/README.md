# Coordination room

MCP router: advisory file-path claims plus an append-only message log with topics, threads and evidence labels. `BOARD.md` is a generated view of the log.

**How to use:** `FLOSS/docs/agent-memory/project/coordination-room-v0.md`  
**Spec:** `FLOSS/docs/specs/coordination-room.spec.md`

Tools: `room_claim` `room_release` `room_state` `room_broadcast` `room_read` `room_topics`  
Bind: `127.0.0.1:7334/mcp`. Start and stop it alone with `scripts/start_mcp_daemons.ps1 -Only room` and `scripts/stop_mcp_daemons.ps1 -Only room` (add `-DryRun` to see what would happen). The start script pins the shared log; a bare `python -m packages.coordination_room.server` from a worktree serves a separate bus.  
Board: `.agent-surface/rooms/default/BOARD.md` (beside the log; override with `COORDINATION_ROOM_BOARD`, which may not be the log)  
One call from a shell: `python -m packages.coordination_room.client room_state`  
Deployment helpers: `deploy.ps1` (dot-source it; every helper stops at a failed precondition)

Router, not controller. No pycrdt. Does not write the claimed files. A room claim is a convention, not write authorization; it does not expire, and agent names are not authenticated. Evidence refs are labelled `resolved` or `unresolved` by a lookup; the room never says "verified".
