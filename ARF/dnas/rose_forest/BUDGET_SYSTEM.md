# Budget System - Resource-Bounded Autonomy

## Overview

The Budget System implements resource-bounded autonomy for the Rose Forest DNA, enabling agents to operate within defined resource constraints with graceful degradation under scarcity.

## Design Principles

1. **Resource Units (RU)** - All operations consume measurable resource units
2. **Bounded Operations** - No operation can exceed available budget
3. **Graceful Degradation** - Clear error messages when budget is insufficient
4. **Automatic Replenishment** - 24-hour budget windows with automatic reset
5. **Bio-aware Constraints** - Costs calibrated to natural cognitive rhythms

## Architecture

### BudgetEngine

The `BudgetEngine` is the core component that manages resource allocation:

```rust
pub struct BudgetEngine;

impl BudgetEngine {
    /// Reserve resource units for an operation
    pub fn reserve_ru(agent: &AgentPubKey, amount: f32) -> ExternResult<()>

    /// Allocate additional budget to an agent
    pub fn allocate_budget(agent: &AgentPubKey, amount: f32) -> ExternResult<()>

    /// Get current budget status
    pub fn get_status(agent: &AgentPubKey) -> ExternResult<BudgetState>

    /// Check if agent has sufficient budget
    pub fn has_budget(agent: &AgentPubKey, amount: f32) -> ExternResult<bool>
}
```

### Budget State

Each agent has a budget state tracked on the DHT:

```rust
pub struct BudgetState {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}
```

## Operation Costs

### Rose Forest Coordinator Operations

| Operation | Cost (RU) | Description |
|-----------|-----------|-------------|
| `add_knowledge` | 33.0 | Major cognitive output (~3 per day) |
| `link_edge` | 3.0 | Cognitive linking (less intensive) |
| `create_thought_credential` | 10.0 | Significant thoughtform creation |

### Memory Coordinator Operations

| Operation | Cost (RU) | Description |
|-----------|-----------|-------------|
| `transmit_understanding` | 3.0 | 1.0 (transmit) + 2.0 (validate) |
| `recall_understandings` | 0.1 per result | Lightweight read operation |
| `compose_memories` | 5.0 | Memory composition from another agent |
| `validate_triple` | 2.0 | Knowledge triple validation |

## Budget Configuration

- **Daily Budget**: 100 RU per 24-hour window
- **Window Duration**: 86,400 seconds (24 hours)
- **Maximum Allocation**: 200 RU (2x normal budget, capped)

### Bio-aware Calibration

The budget is calibrated to human cognitive capacity:
- 100 RU per day reflects natural cognitive limits
- 3 major cognitive operations per day (33 RU each)
- Allows for ~10 thoughtform creations (10 RU each)
- Or ~30 edge links (3 RU each)
- Or ~1000 memory recalls (0.1 RU each)

## Usage Examples

### Checking Budget Status

```rust
#[hdk_extern]
pub fn budget_status(_: ()) -> ExternResult<BudgetState> {
    let agent_key = agent_info()?.agent_latest_pubkey;
    BudgetEngine::get_status(&agent_key)
}
```

### Consuming Budget in Operations

```rust
#[hdk_extern]
pub fn transmit_understanding(input: UnderstandingInput) -> ExternResult<ActionHash> {
    let agent_key = agent_info()?.agent_latest_pubkey;

    // Check and consume budget
    let total_cost = COST_TRANSMIT_UNDERSTANDING + COST_VALIDATE_TRIPLE;
    consume_budget(&agent_key, total_cost)?;

    // Perform operation...
}
```

### Handling Insufficient Budget

```rust
// When budget is insufficient, operations fail with clear error:
// Error: E_INSUFFICIENT_RU: need 33.00 RU, have 5.00 RU.
// Budget resets at 1730764800
```

## Graceful Degradation

The system provides graceful degradation through:

1. **Pre-flight Checks** - Budget checked before operation starts
2. **Clear Error Messages** - Detailed information about budget state
3. **Reset Information** - Users informed when budget will replenish
4. **No Silent Failures** - All budget violations return errors
5. **Operation Atomicity** - No partial operations on budget failure

## Budget Replenishment

### Automatic Window Reset

- Budget automatically resets to 100 RU after 24 hours
- Window start timestamp tracked per agent
- No manual intervention required

### Manual Allocation

Agents can be granted additional budget:

```rust
// Allocate 50 RU to an agent
BudgetEngine::allocate_budget(&agent_key, 50.0)?;
```

**Note**: Allocations are capped at 200 RU (2x normal budget) to prevent abuse.

## Integration with VVS Spec

This implementation fulfills the VVS (Virtual Verifiable Singularity) specification requirements:

1. ✅ **Autonomy Budgets** - Per-agent resource limits
2. ✅ **Risk-weighted Quotas** - Operations have different costs based on impact
3. ✅ **Auto-halt on Overrun** - Operations fail when budget exhausted
4. ✅ **Self-escalation** - Clear error signals for budget violations
5. ✅ **No Human Approval** - Fully autonomous operation within bounds

## Testing

Comprehensive tests are available in `tests/budget_test.rs`:

- Basic budget consumption
- Multiple operations
- Over-budget scenarios
- Memory coordinator integration
- Budget replenishment
- BudgetEngine methods
- Graceful degradation
- Operation cost verification

Run tests with:
```bash
cargo test --test budget_test
```

## Success Metrics

✅ **All operations check budget** - Every write operation verifies budget before execution

✅ **Agents cannot exceed budget** - Budget enforcement prevents over-limit operations

✅ **Budget replenishment system works** - Automatic 24-hour window reset

✅ **Tests for over-budget scenarios** - Comprehensive test coverage including failure cases

## Error Handling

### Budget Exceeded Error

```
E_BUDGET_EXCEEDED: need 33.00 RU, have 5.00 RU.
Budget resets at 1730764800
```

### Insufficient RU Error

```
E_INSUFFICIENT_RU: need 33.00 RU, have 5.00 RU.
Budget resets at 1730764800
```

Both errors provide:
- Required RU amount
- Current RU balance
- Reset timestamp

## Future Enhancements

Potential improvements for the budget system:

1. **Adaptive Budgets** - Adjust based on reputation or stake
2. **Budget Markets** - Trade RU between agents
3. **Priority Queuing** - Allow operations to wait for budget
4. **Budget Analytics** - Track usage patterns and optimization
5. **Multi-tier Budgets** - Different limits for different operation classes

## References

- VVS Spec: `../rose_forest_virtual_verifiable_singularity_vvs_spec_v_1^0.md`
- Budget Implementation: `zomes/coordinator/src/budget.rs`
- Memory Budget: `zomes/memory_coordinator/src/budget.rs`
- Tests: `tests/budget_test.rs`
