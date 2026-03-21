use hdk::prelude::*;
use rose_forest_integrity::{BudgetEntry, EntryTypes};

// Bio-aware budget parameters based on the manifesto
// Represents a unit of cognitive output, calibrated to the idea of ~3 major cognitive pulses per day
pub const COST_ADD_KNOWLEDGE: f32 = 33.0;
// Represents a unit of cognitive linking, a less intensive action
pub const COST_LINK_EDGE: f32 = 3.0;
// Represents the cost of creating a significant thoughtform
pub const COST_CREATE_THOUGHT_CREDENTIAL: f32 = 10.0;

// Memory operation costs (VVS spec requirements)
// Cost to transmit an understanding to the DHT
pub const COST_TRANSMIT_UNDERSTANDING: f32 = 1.0;
// Cost per result when recalling understandings
pub const COST_RECALL_UNDERSTANDINGS: f32 = 0.1;
// Cost to compose memories from another agent
pub const COST_COMPOSE_MEMORIES: f32 = 5.0;
// Cost to validate a knowledge triple
pub const COST_VALIDATE_TRIPLE: f32 = 2.0;

// Total cognitive budget per window, reflecting the idea of a daily cognitive capacity
pub const MAX_RU_PER_WINDOW: f32 = 100.0;
// A 24-hour window for budget replenishment, aligning with natural human cycles
pub const BUDGET_WINDOW_SECONDS: i64 = 86400;

pub fn consume_budget(agent: &AgentPubKey, cost: f32) -> ExternResult<()> {
    let mut budget_state = get_budget_state(agent)?;

    if budget_state.remaining_ru < cost {
        return Err(wasm_error!(WasmErrorInner::Guest("E_BUDGET_EXCEEDED: Agent budget exceeded.".into())));
    }

    budget_state.remaining_ru -= cost;
    save_budget_entry(agent, budget_state.remaining_ru, budget_state.window_start)?;
    Ok(())
}

pub fn get_budget_state(agent: &AgentPubKey) -> ExternResult<BudgetState> {
    let now = sys_time()?;
    let agent_address = agent.clone();

    // Query local source chain for the latest BudgetEntry.
    // This is correct for agent-local state: source chain order guarantees
    // the last BudgetEntry is the most recent, avoiding the bug where
    // DHT-based get_links returned multiple entries with the same window_start
    // and non-deterministic ordering.
    let filter = ChainQueryFilter::new().include_entries(true);
    let records = query(filter)?;

    let mut latest_budget: Option<BudgetEntry> = None;
    // Iterate in reverse (most recent source chain action first)
    for record in records.iter().rev() {
        if let Some(budget_entry) = record.entry()
            .to_app_option::<BudgetEntry>()
            .ok()       // treat deserialization errors (non-BudgetEntry types) as None
            .flatten()
        {
            if budget_entry.agent == agent_address {
                latest_budget = Some(budget_entry);
                break;
            }
        }
    }

    let now_secs = now.as_seconds_and_nanos().0;

    match latest_budget {
        Some(budget) if (now_secs - budget.window_start.as_seconds_and_nanos().0) < BUDGET_WINDOW_SECONDS => {
            Ok(BudgetState { agent: agent_address, remaining_ru: budget.remaining_ru, window_start: budget.window_start })
        },
        _ => {
            // Fresh or expired budget — no entry created until actually consumed.
            // This avoids the previous bug where get_budget_state created a 100 RU
            // entry that competed with the real consumed-budget entry.
            Ok(BudgetState { agent: agent_address, remaining_ru: MAX_RU_PER_WINDOW, window_start: now })
        }
    }
}

/// Persist a budget snapshot to the agent's source chain.
/// Budget is agent-local state — the source chain is the authoritative record.
/// No DHT links needed; we query the source chain directly in get_budget_state.
fn save_budget_entry(agent: &AgentPubKey, remaining_ru: f32, window_start: Timestamp) -> ExternResult<ActionHash> {
    let budget_entry = BudgetEntry { agent: agent.clone(), remaining_ru, window_start };
    let hash = create_entry(EntryTypes::BudgetEntry(budget_entry))?;
    Ok(hash)
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct BudgetState {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}

/// BudgetEngine manages resource units (RU) for autonomous operations
/// Implements resource-bounded autonomy with graceful degradation
pub struct BudgetEngine;

impl BudgetEngine {
    /// Reserve resource units (RU) for an operation
    /// Returns an error if insufficient budget is available
    pub fn reserve_ru(agent: &AgentPubKey, amount: f32) -> ExternResult<()> {
        let budget_state = get_budget_state(agent)?;

        if budget_state.remaining_ru >= amount {
            consume_budget(agent, amount)?;
            Ok(())
        } else {
            Err(wasm_error!(WasmErrorInner::Guest(
                format!(
                    "E_INSUFFICIENT_RU: need {:.2} RU, have {:.2} RU. Budget resets at {:?}",
                    amount,
                    budget_state.remaining_ru,
                    budget_state.window_start.as_seconds() + BUDGET_WINDOW_SECONDS
                )
            )))
        }
    }

    /// Allocate additional budget to an agent
    pub fn allocate_budget(agent: &AgentPubKey, amount: f32) -> ExternResult<()> {
        let budget_state = get_budget_state(agent)?;
        let new_total = budget_state.remaining_ru + amount;
        let capped_total = new_total.min(MAX_RU_PER_WINDOW * 2.0);
        save_budget_entry(agent, capped_total, budget_state.window_start)?;
        Ok(())
    }

    /// Get current budget status for an agent
    pub fn get_status(agent: &AgentPubKey) -> ExternResult<BudgetState> {
        get_budget_state(agent)
    }

    /// Check if an agent has sufficient budget for an operation
    pub fn has_budget(agent: &AgentPubKey, amount: f32) -> ExternResult<bool> {
        let budget_state = get_budget_state(agent)?;
        Ok(budget_state.remaining_ru >= amount)
    }
}
