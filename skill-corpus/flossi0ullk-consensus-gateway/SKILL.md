---
name: flossi0ullk-consensus-gateway
description: Use when working on the local consensus gateway, voter/provider rosters, post-write hooks, source-chain claim and vote handling, or verification flows for the FLOSSI0ULLK multi-model node.
---

# FLOSSI0ULLK Consensus Gateway

The gateway is a router and evidence surface, not a controller.

## Core workflow

1. Confirm which layer is changing:
   - `FLOSS/packages/metacoordinator_mcp`
   - `FLOSS/packages/orchestrator`
   - `FLOSS/packages/source_chain`
   - `FLOSS/scripts/hook_post_write.py`
   - `FLOSS/scripts/hook_bg_round.py`
2. If provider or roster behavior changes, update:
   - `FLOSS/packages/metacoordinator_mcp/voter_registry.json`
   - `FLOSS/packages/metacoordinator_mcp/voters.py`
   - `FLOSS/.env.example`
   - matching tests
3. Verify locally with the smallest relevant slice first.
4. Preserve claim, vote, and decision provenance in the source chain and traces.

## Verification floor

- `python FLOSS/packages/metacoordinator_mcp/tests/test_voters.py`
- `python FLOSS/packages/metacoordinator_mcp/tests/test_tools.py`
- `python FLOSS/scripts/smoke_test_voters.py`

## References

Open only what you need:

- `references/test-map.md`

