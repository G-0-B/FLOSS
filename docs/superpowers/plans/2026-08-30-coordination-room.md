# Coordination Room Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land a loopback MCP file-claim room so two agents cannot silently share a path, with an append-only broadcast log.

**Architecture:** In-process exclusive ClaimTable plus JSONL EventLog behind FastMCP on 127.0.0.1:7334. Router, not controller. Compose computer-use lease shape; do not reuse that table.

**Tech Stack:** Python 3.13, pytest, existing FastMCP / `packages.mcp_daemon` HTTP helper.

## Global Constraints

- Bind 127.0.0.1 only. Port 7334. Do not start `:7333`. Do not touch consensus/provenance.
- File paths only. No pycrdt. No task claims. No start_mcp_daemons.ps1.
- Claim conflict is a table error, not a chat parse.
- Event log is the only durable mutation.

---

### Task 1: PathNorm + ClaimTable + EventLog + Gateway + tests

**Files:**
- Create: `packages/coordination_room/{__init__,paths,claims,log,room,gateway,server}.py`
- Create: `packages/coordination_room/tests/{test_paths,test_claims,test_room,test_gateway}.py`
- Create: `docs/specs/coordination-room.spec.md` + `.schema.json`
- Modify: `.mcp.json` (workspace + FLOSS), `shared-agent-surface.json`, `docs/specs/spec-registry.json`

**Interfaces:**
- Produces: `normalize_path(root, path) -> str`, `ClaimTable.claim/release/snapshot`, `EventLog.append/load`, `CoordinationRoom.claim/release/broadcast/read/state`, JSON gateway methods matching those names.

Operator executed this plan inline 2026-08-30 (yes-to-everything).
