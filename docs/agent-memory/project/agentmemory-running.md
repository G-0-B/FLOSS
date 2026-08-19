---
id: project-agentmemory-running
type: project
created: '2026-05-19'
status: active
applies_to:
- any-agent
source: codex_session
title: agentmemory is a live root operator surface and local memory server
---

`AGENTMEMORY.md` at the workspace root is a live operator surface for the local
agentmemory service, not raw intake. It belongs beside `AGENTS.md`, `CLAUDE.md`,
and `GEMINI.md` because it documents a cross-agent runtime service.

Verified in this session:

- Health endpoint: `http://localhost:3111/agentmemory/health` returned
  `status: healthy`, service version `0.9.21`, worker version `0.11.6`.
- Viewer endpoint: `http://localhost:3113` returned HTTP 200.
- Upstream GitHub license: Apache-2.0 via `gh api repos/rohitg00/agentmemory`.
- Root MCP now includes `agentmemory` behind JanuScope lens
  `.mcp/lenses/agentmemory.yaml`, and mirrors/projections are materialized from
  the shared agent surface.
- REST `remember` smoke test succeeded with memory id
  `mem_mpdbgjou_c85a7e13b6f4`. Immediate `smart-search` did not return it,
  likely because indexing is asynchronous; do not count search persistence as
  verified yet.
- Later Claude REST adapter-test wrote memory id `mem_mpebqux9_d9ae5dbe18e4`
  and recalled it by smart-search. Codex re-ran the same REST search on
  2026-05-20 and recalled that same id, so REST-level cross-session recall is
  verified. MCP tool-use remains unverified until a new MCP-aware session calls
  `memory_smart_search`.

Authority boundary:

- agentmemory is Plane A memory/recall infrastructure.
- Repository-owned canonical memory remains under `FLOSS/docs/agent-memory/`
  and is projected outward by `materialize_shared_agent_memory.py`.
- Recalled agentmemory content should become load-bearing only after promotion
  through shared memory markdown, working todo, spec/ADR, or consensus claim.

Reuse-ledger entry `0012 agentmemory` has license, local server health, rollback,
provenance, REST write/search, and REST cross-session recall evidence, but
remains `investigate` until a real MCP tool call from at least one agent is
verified and the upstream contact gate lands.
