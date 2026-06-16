# FLOSSI0ULLK Project Overview

## Purpose
FLOSSI0ULLK (Free Libre Open Source Singularity of Infinite Overflowing Unconditional Love Light and Knowledge) is a Holochain-based decentralized knowledge commons. It's an agent-centric, verifiable knowledge system for scientific discovery, ethical AI alignment, and distributed intelligence coordination.

## Tech Stack
- **Holochain 0.4.4** (hdi 0.5.1, hdk 0.4.1): Agent-centric DHT substrate
- **Rust**: Integrity + coordinator zomes (WASM target)
- **Python**: Orchestrator, CLI, embedding pipeline, conversation memory
- **TypeScript**: Tryorama integration tests (vitest)
- **Nix**: Dev environment via Holonix (flake.nix)
- **JSON Schema (draft 2020-12)**: Entry type specs with AJV validation

## Key Architecture
- **Integrity Zome** (`ARF/dnas/rose_forest/zomes/integrity/`): Entry types (RoseNode, KnowledgeEdge, BudgetEntry, ThoughtCredential), validation rules, link types (AllNodes, Edge)
- **Coordinator Zome** (`ARF/dnas/rose_forest/zomes/coordinator/`): 9 extern functions (add_knowledge, vector_search, link_edge, budget_status, create_thought_credential, assert_triple, query_triples, get_triple_record, get_predicates)
- **Budget System**: Agent-local RU tracking via source chain queries, 100 RU/24h window
- **Python Orchestrator** (`packages/orchestrator/holochain_connector.py`): Async WebSocket connector to Holochain conductor (Rose Forest DNA). Infinity Bridge has a separate connector at `ARF/in.finite-nrg/infinity-bridge/orchestrator/holochain_connector.py`.

## Core Principles
1. **Symbolic-First**: Logic validates, neural assists. Never the reverse.
2. **Spec-Driven Development (SDD)**: Spec → tests → code
3. **Agent-Centricity**: Identity, not servers, is the organizing principle
4. **Now/Later/Never**: Ship simplest thing solving validated pain today.

## Current State (as of 2026-04)

- Phase 0 MVP complete: DNA compiles to WASM, runs in conductor, Tryorama tests pass
- 4 entry types with validation, 9 coordinator functions (add_knowledge, vector_search, link_edge, budget_status, create_thought_credential, assert_triple, query_triples, get_triple_record, get_predicates)
- Budget tracking via source chain (not DHT links)
- JSON Schema specs for all entry types
- Branch: `lappytop` with PR #25 open (ADR batch + substrate bridge + Seam 1 consensus gate + signed gradient)
