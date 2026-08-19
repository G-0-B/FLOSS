# Context Router Routing Policy

```yaml
id: "2026-05-22-context-router-routing-policy"
date: "2026-05-22"
type: "routing_policy"
status: "Prototype implemented"
truth_status:
  implementation: "Verified by focused tests"
  production_retrieval: "Specified"
  vector_database: "Not introduced"
```

## Purpose

This policy applies the RAGRoute lesson locally: choose the corpus first, then
retrieve inside that corpus. The goal is better context hygiene without adding a
large vector database or new runtime dependency.

The router is a selector, not an authority layer. Canonical truth still lives in
the canonical docs, ADRs, source-chain evidence, code, and validated memory
surfaces.

## Route Lanes

| Lane | Route label | Use when the query asks about |
|---|---|---|
| `canon` | canonical authority | Current project truth, phase state, ADRs, specs, kernel, governance, operator orientation. |
| `architecture` | architecture and operating model | System design, metaharness structure, runtime planes, context daemon, Holochain/Radicle stack. |
| `code` | implementation and tests | Functions, packages, scripts, tests, bugs, refactors, and live implementation details. |
| `source-chain` | source-chain provenance | Claims, votes, consensus evidence, hashline/head state, provenance, and decision records. |
| `agent-memory` | shared agent memory | AGENTMEMORY, user preferences, durable recall, cross-agent projections, and shared memory surfaces. |
| `serena-memory` | serena codebase memory | Serena-specific codebase memory, onboarding, LSP, conventions, and local repo style. |
| `research` | research intake and synthesis | Active research digestion, paper/report synthesis, external project comparison, RAGRoute, DecentMem, DAMCS, AD4M fit checks. |
| `reference` | published reference library | Last-resort books, PDFs, textbooks, published papers, and broad external background. |
| `skills` | agent workflow skills | Portable skill instructions and shared skill-surface materialization. |
| `traces` | runtime traces and logs | Hook logs, consensus traces, latency/debug evidence, and retrospective runtime analysis. |

## Scoring Model

`FLOSS/scripts/context_router.py` uses only manifest data from
`FLOSS/shared-context-surface.json`.

- Query and manifest terms are normalized to lowercase alphanumeric tokens.
- `route_intents` are the strongest signal: multi-token exact match +180,
  single-token exact match +120, partial token overlap +20.
- `keywords` remain a secondary signal: multi-token exact match +120,
  single-token exact match +80, partial token overlap +35.
- Corpus id, URI, and summary overlap add +15 per overlapping token.
- Corpus `priority` remains a stable tie-breaker and cold-start default, not a
  substitute for specific route evidence.

This intentionally lets a query like "decision claim vote provenance" route to
`source-chain` instead of `canon`, while a query like "ADR decision authority"
still routes to `canon`.

## Non-Goals

- No global vector database in this prototype.
- No embedding calls or external services.
- No automatic canon promotion from retrieval output.
- No merging of memory, source-chain, and canon truth boundaries.

## Operational Checks

Run focused tests after changing router policy:

```powershell
python -m pytest FLOSS/scripts/tests/test_context_router.py -q
```

Run representative routes:

```powershell
python FLOSS/scripts/context_router.py "RAGRoute arxiv open distributed intelligence research report" --format markdown --limit 4
python FLOSS/scripts/context_router.py "decision claim vote consensus provenance" --format markdown --limit 4
python FLOSS/scripts/context_router.py "AGENTMEMORY durable recall shared memory user preference" --format markdown --limit 4
```
