# Coordination room

MCP router: exclusive file-path claims + append-only broadcast log.

**How to use:** `FLOSS/docs/agent-memory/project/coordination-room-v0.md`  
**Spec:** `FLOSS/docs/specs/coordination-room.spec.md`

Tools: `room_claim` `room_release` `room_state` `room_broadcast` `room_read`  
Bind: `127.0.0.1:7334/mcp` — `python -m packages.coordination_room.server`

Router, not controller. No pycrdt. Does not write the claimed files.
