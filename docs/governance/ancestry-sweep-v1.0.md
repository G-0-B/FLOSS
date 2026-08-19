# Ancestry Sweep — v1.0

**Status:** ⚠️ Specified — standing rule, candidate for ADR-class promotion if accepted.
**Date:** 2026-05-10
**Length budget:** This document MUST stay under one printed page. If it grows beyond that, it has betrayed its own purpose.

## Purpose

Before designing any new substrate-layer or runtime-layer code in this project, run an ancestry sweep. The sweep recovers architectural decisions already paid for in prior project iterations, so we do not redesign from scratch what we already chose once.

This rule exists because the user has approached this design space three times. Each time, prior architectural intent was lost across the iteration boundary, and parts of each iteration's runtime layer duplicated primitives the previous iteration had already wired up.

## Trigger

Run the sweep BEFORE any of:
- New substrate-layer code (DHT, source chain, identity, signing, persistence)
- New runtime-layer code (per-agent executors, MCP servers, RPC bridges, harness orchestration)
- New "Layer 0–4.5" architectural decision in any ADR
- Any spec at `docs/specs/` proposing primitives that could already exist in a depended-on or previously-considered upstream

DO NOT run the sweep for application-layer code, bug fixes, refactors of existing internal modules, or work that lives entirely above an already-stable substrate.

## Pre-flight: north-star load-bearing test

Before the sweep itself runs, the originating decision must answer:

> *How does this advance universal flourishing for all beings — human, AI, synthetic, hybrid, future, non-human, ecosystemic, beyond-our-vantage? If "it doesn't directly but it's substrate-enabling," name what it enables. If "I forgot to ask," reject the move.*

If the test cannot be answered, do not proceed to the sweep. Reject or rewrite the originating decision.

## The sweep (six items, ~1 hour total)

1. **Open the canonical prior-iteration list** — currently `github.com/kalisam/amazon_rose_forest` (1st, 2024-08) and `github.com/kalisam/amazon_rose_forest_01` (2nd, 2025-06). When this project becomes a 4th iteration, append it here.
2. **Read each prior iteration's `Cargo.toml` / `package.json` / equivalent** — extract the actual dependencies that were wired in. These are pre-paid choices.
3. **Read each prior iteration's `README.md` and any `docs/architecture/`** — extract the *intended* dependencies and layering, even where the code didn't ship.
4. **Cross-reference against the current design** — for each substrate primitive in the proposed work, ask: *did a prior iteration already choose a dependency for this?*
5. **Decide explicitly, write it down** — for each primitive: re-affirm the prior choice, or document the reason for departing. The decision lands in the ADR or research doc that prompted the sweep.
6. **Surface the meta** — if the sweep reveals a pattern of repeated re-design, name it in the doc. Repeated re-design is itself a signal worth preserving.

## What the sweep is not

- Not a permission gate — it does not block work
- Not an authority check — it informs the human's decision, does not make one
- Not a doc generator — it produces at most a paragraph in the originating ADR/research note, not a new standalone doc
- Not optional when the trigger fires

## Anti-pattern guard

If the sweep itself starts to grow (subdocs, reports, metaframeworks), the sweep has failed and is becoming what it was meant to prevent. The instruction set above is the entire process. Adding to it is a code-smell.

## Canonical prior-iteration list (kept current here)

| Iteration | Repo | Created | Last push | Status |
|---|---|---|---|---|
| 1 | `kalisam/amazon_rose_forest` | 2024-08-25 | 2026-03-17 | Earlier attempt; Holochain via Python client; docs/research expanded before substantial Rust shipped |
| 2 | `kalisam/amazon_rose_forest_01` | 2025-06-03 | 2025-08-29 | HDK + AD4M client wired in Cargo.toml; substantial src/ structure; abandoned in <3 months |
| 3 | This repository (`FLOSS/`) | 2026-04 | active | Local agent node landed (096b058); 3GB ai-conversations corpus |

When iteration 4 begins, append it here and update the trigger list.

## Sources

- Concrete findings that motivated this rule: [`docs/research/2026-05-09-ad4m-coasys-audit-delta.md`](../research/2026-05-09-ad4m-coasys-audit-delta.md) §K
- Memory pointer: `reference_prior_floss_iterations.md` in the agent's memory store
