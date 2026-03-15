use hdk::prelude::*;
use rose_forest_integrity::{BudgetEntry, EntryTypes, LinkTypes};

// Bio-aware budget parameters based on the manifesto
// Represents a unit of cognitive output, calibrated to the idea of ~3 major cognitive pulses per day
pub const COST_ADD_KNOWLEDGE: f32 = 33.0;
// Represents a unit of cognitive linking, a less intensive action
pub const COST_LINK_EDGE: f32 = 3.0;
// Represents the cost of creating a significant thoughtform
pub const COST_CREATE_THOUGHT_CREDENTIAL: f32 = 10.0;

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

/// Persist a budget snapshot to the source chain (and link for future cross-agent queries).
fn save_budget_entry(agent: &AgentPubKey, remaining_ru: f32, window_start: Timestamp) -> ExternResult<ActionHash> {
    let budget_entry = BudgetEntry { agent: agent.clone(), remaining_ru, window_start };
    let hash = create_entry(EntryTypes::BudgetEntry(budget_entry))?;
    let path = Path::from(format!("agent_budget.{}", agent.clone()));
    create_link(path.path_entry_hash()?, hash.clone(), LinkTypes::AgentBudget, ())?;
    Ok(hash)
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct BudgetState {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}
