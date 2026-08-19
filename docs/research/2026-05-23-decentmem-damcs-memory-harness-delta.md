---
id: "2026-05-23-decentmem-damcs-memory-harness-delta"
title: "DecentMem / DAMCS Memory-Harness Delta"
date: "2026-05-23"
type: "research_delta"
status: "Specified - comparison only; not adoption"
truth_status:
  paper_presence: "Verified"
  repo_canon_mapping: "Verified"
  implementation_decision: "Not performed"
  adoption: "Not performed"
compared_sources:
  - "AGENTMEMORY.md"
  - "FLOSS/docs/agent-memory/MEMORY.md"
  - "FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md"
  - "DecentMem arXiv:2605.22721"
  - "DAMCS arXiv:2502.05453 and project/code pages"
---

# DecentMem / DAMCS Memory-Harness Delta

This note maps two decentralized memory patterns against FLOSSI0ULLK's current
memory harness. It is a comparison artifact only. It does not adopt DecentMem,
DAMCS, their code, or their evaluation claims as FLOSSI0ULLK architecture.

## Source Claims Checked

**DecentMem.** The arXiv paper "Self-Evolving Multi-Agent Systems via
Decentralized Memory" was submitted on 2026-05-21. It argues that centralized
shared memory creates coordination overhead, privacy pressure, and loss of agent
diversity. Its proposed pattern is per-agent dual-pool memory: an exploitation
pool of consolidated trajectories and an exploration pool of LLM-generated
candidates for unseen contexts, reweighted online from staged judge feedback.

**DAMCS.** The arXiv paper "LLM-Powered Decentralized Generative Agents with
Adaptive Hierarchical Knowledge Graph for Cooperative Planning" was submitted
on 2025-02-08. Its project page and code are public. DAMCS combines
Decentralized Adaptive Knowledge Graph Memory with a Structured Communication
System, so agents keep their own memories while sharing selected information for
cooperative planning.

## FLOSSI0ULLK Baseline

The current local harness already separates memory surfaces:

- `AGENTMEMORY.md` describes the local `agentmemory` service as Plane A
  cross-model persistent memory: useful for recall, search, federation, and
  tool-facing memory operations, but not canonical truth.
- `FLOSS/docs/agent-memory/` is the repo-owned durable agent-memory tree.
  Agent-native files are generated projections; ADRs, specs, source-chain
  records, and canonical docs remain the promotion path for load-bearing state.
- `CONTEXT_DAEMON_ARCHITECTURE.md` defines the larger context infrastructure:
  observer layer, semantic index, bi-temporal graph, CRDT working state, and
  curator loop. Several pieces are walking skeletons; the full daemon, graph,
  CRDT layer, and curator loop are still Specified, not live.

The correct reading is not "add a shared memory brain." It is: keep per-agent
memory local by default, share selectively, and promote only through explicit
provenance and validation gates.

## Comparison Matrix

| Axis | DecentMem | DAMCS | FLOSSI0ULLK current | Delta |
|---|---|---|---|---|
| Memory ownership | Each agent owns its own memory pools rather than writing to one central repository. | Each agent maintains its own memory while cooperating through communication. | Repo canon owns truth; `agentmemory` owns local recall/federation; generated projections serve agents. | Add an explicit per-agent memory boundary contract so future harness work does not collapse local memory into canon. |
| Memory shape | Dual pool: consolidated past trajectories plus generated candidates for unseen contexts. | Hierarchical adaptive knowledge graph memory. | Four-tier local memory in `agentmemory`; repo memory tree is markdown-backed; Context Daemon graph layer is Specified. | Treat raw episodes and consolidated summaries as separate evidence classes; use graph memory as an index/projection, not source of truth. |
| Selective sharing | Privacy and diversity are motivation for decentralization; sharing is not the primary abstraction in the abstract. | Structured communication reduces redundant sharing and keeps agents aware of relevant progress. | No blanket sharing rule; promotion through docs/specs/ADRs/source-chain; `team_share`/mesh-style tools remain Plane A capability. | Add a Selective Sharing Gate: every cross-agent memory projection needs scope, reason, provenance, and conflict handling. |
| Knowledge-graph memory | Not the central design in the checked abstract. | Central design: adaptive hierarchical KG memory for planning and cooperation. | Context Daemon bi-temporal graph is Specified; KnowledgeTriple/semantic memory direction exists but is not the live canonical memory engine. | Run any KG-memory experiment as a derived graph from repo/source-chain evidence, not as an opaque write target. |
| Retrieval policy | Per-agent pool selection and online reweighting. | Retrieval from hierarchical memory plus communication protocol. | `context_router.py` routes corpus first; `agentmemory` provides hybrid local recall; canon remains file/source-chain backed. | Route before retrieval, then retrieve within corpus or agent scope. Do not global-vectorize all memory as the first move. |
| Privacy and provenance | Critiques centralized memory for privacy pressure and diversity collapse. | Limits redundant communication through structured messages. | Agent memory rules preserve repo canon and generated projections; source-chain/provenance are separate from recall. | Make privacy/provenance metadata mandatory for future shared-memory records. |
| Contradiction handling | Not established as a FLOSSI0ULLK-ready mechanism from the checked source. | Not a substitute for symbolic validation. | Context Daemon curator layer is intended to consolidate, prune, and surface contradictions; not fully live. | Contradictions should land as claims/conflicts for curator or source-chain review, not be silently merged by a memory engine. |
| Working state | Focuses self-evolving MAS memory, not CRDT working state. | Cooperative environment has agents coordinating through memory and communication. | Context Daemon CRDT working-state layer is Specified. | Per-agent memory can inform CRDT state, but should not replace shared task-state semantics. |
| Promotion to canon | No direct fit; it is a memory optimization framework. | No direct fit; it is a cooperation framework. | Promotion path is markdown/spec/ADR/source-chain with truth-status discipline. | Preserve "memory can suggest, canon must verify." |

## Recommended Deltas

### 1. Add a Memory Boundary Contract

Future memory harness specs should name the boundaries directly:

| Scope | Meaning | Allowed write path |
|---|---|---|
| `local_private` | Agent-local observations, scratch, preferences, or raw trajectories. | Agent-local store only. |
| `agent_shared` | Memory intentionally shared with selected agents or tools. | Shared projection with provenance and sharing policy. |
| `project_shared` | Durable operational memory relevant to the FLOSSI0ULLK workspace. | `FLOSS/docs/agent-memory/` or generated projections after review. |
| `canon_candidate` | Memory-derived claim that may affect architecture, implementation, or status. | Research note, spec draft, ADR draft, or source-chain claim. |
| `canonical` | Verified load-bearing state. | Canonical doc/ADR/spec/source-chain path only. |

Minimum metadata for shared records:

```yaml
memory_scope: "local_private | agent_shared | project_shared | canon_candidate | canonical"
source_agent: "<agent or tool identity>"
provenance: "<file, source-chain claim, tool transcript, or paper URL>"
valid_from: "YYYY-MM-DD or event id"
valid_until: "YYYY-MM-DD, event id, or null"
sharing_policy: "<who can read/reuse and why>"
conflict_policy: "<append contradiction, request verification, or block promotion>"
promotion_path: "<none | agent-memory | research-note | spec | ADR | source-chain>"
```

### 2. Add a Selective Sharing Gate

Per-agent memories should never auto-promote into project memory. Sharing must
answer four questions:

1. What exact memory is being shared?
2. Which agents or surfaces need it?
3. What source/provenance backs it?
4. What happens if another memory contradicts it?

This maps DAMCS-style structured communication into FLOSSI0ULLK without
importing DAMCS as a runtime dependency.

### 3. Treat KG Memory as a Derived Projection

DAMCS supports the case for graph-shaped memory, but FLOSSI0ULLK should keep the
graph derived from evidence. A future experiment can project a small slice of
`FLOSS/docs/agent-memory/`, ADR links, and source-chain claims into
KnowledgeTriple-style graph records with agent, source, time, and validity
edges. That experiment should be read-only or append-to-staging until the
Context Daemon graph and curator layers have validation tests.

### 4. Keep `agentmemory` in Plane A

The `agentmemory` service remains useful for local recall and federation, but
DecentMem/DAMCS do not change its adoption boundary. Its mesh/team/share tools
should stay Plane A experimental until MCP tool-use and boundary behavior are
verified. REST recall evidence is not enough to promote it to canonical memory.

## Non-Actions

- Do not replace `agentmemory` with DecentMem or DAMCS.
- Do not move repo-owned memory into an opaque vector or graph database.
- Do not auto-share all per-agent memory.
- Do not mark either paper/codebase as adopted.
- Do not let KG memory bypass ADR/spec/source-chain validation.

## Next Spec Candidates

1. `memory-boundary-contract.spec.md`: define memory scopes, metadata, sharing
   gates, and promotion paths.
2. `selective-sharing-gate.spec.md`: define cross-agent memory sharing rules,
   required provenance, and contradiction behavior.
3. KG-memory dry run: script or note that projects a bounded local corpus into
   KnowledgeTriple-style graph records for inspection only.

## Sources Checked

- [DecentMem arXiv:2605.22721](https://arxiv.org/abs/2605.22721)
- [DAMCS arXiv:2502.05453](https://arxiv.org/abs/2502.05453)
- [DAMCS project page](https://happyeureka.github.io/damcs/)
- [DAMCS current code repository](https://github.com/13RENDA/Mcrafter_LLM_Agent)
- [DAMCS legacy code repository](https://github.com/HappyEureka/mcrafter)
