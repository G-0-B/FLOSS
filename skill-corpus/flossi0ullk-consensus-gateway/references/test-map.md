# Consensus Gateway Test Map

## Code surfaces

- `FLOSS/packages/metacoordinator_mcp/voters.py`
- `FLOSS/packages/metacoordinator_mcp/voter_registry.json`
- `FLOSS/packages/metacoordinator_mcp/tools.py`
- `FLOSS/packages/orchestrator/claim_schema.py`
- `FLOSS/packages/orchestrator/consensus_gate.py`
- `FLOSS/packages/source_chain/cell.py`
- `FLOSS/scripts/hook_bg_round.py`
- `FLOSS/scripts/hook_post_write.py`

## Verification commands

- `python FLOSS/packages/metacoordinator_mcp/tests/test_voters.py`
- `python FLOSS/packages/metacoordinator_mcp/tests/test_tools.py`
- `python FLOSS/scripts/smoke_test_voters.py`

## Evidence surfaces

- `%USERPROFILE%/.floss_agent/cells/.../source_chain`
- `%USERPROFILE%/.floss_agent/traces/consensus`
- `%USERPROFILE%/.floss_agent/hook.log`

