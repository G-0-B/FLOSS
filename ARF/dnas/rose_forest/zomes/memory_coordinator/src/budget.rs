use hdk::prelude::*;
use rose_forest_integrity::BudgetEntry;

// Memory operation costs (VVS spec requirements)
pub const COST_TRANSMIT_UNDERSTANDING: f32 = 1.0;
pub const COST_RECALL_UNDERSTANDINGS: f32 = 0.1;
pub const COST_COMPOSE_MEMORIES: f32 = 5.0;
pub const COST_VALIDATE_TRIPLE: f32 = 2.0;

// Budget configuration
pub const MAX_RU_PER_WINDOW: f32 = 100.0;
pub const BUDGET_WINDOW_SECONDS: u64 = 86400; // 24 hours

/// Consume budget for an operation
/// Returns an error if insufficient budget is available
pub fn consume_budget(agent: &AgentPubKey, cost: f32) -> ExternResult<()> {
    let mut budget_state = get_budget_state(agent)?;

    if budget_state.remaining_ru < cost {
        return Err(wasm_error!(WasmErrorInner::Guest(
            format!(
                "E_BUDGET_EXCEEDED: need {:.2} RU, have {:.2} RU. Budget resets at {:?}",
                cost,
                budget_state.remaining_ru,
                budget_state.window_start.as_seconds() + BUDGET_WINDOW_SECONDS
            )
        )));
    }

    budget_state.remaining_ru -= cost;
    update_budget_entry(agent, budget_state.remaining_ru, budget_state.window_start)?;
    Ok(())
}

/// Get current budget state for an agent
pub fn get_budget_state(agent: &AgentPubKey) -> ExternResult<BudgetState> {
    let now = sys_time()?;
    let agent_address = agent.clone();

    let path = Path::from(format!("agent_budget.{}", agent_address));
    let links = get_links(
        GetLinksInputBuilder::try_new(path.path_entry_hash()?, LinkTypes::AgentBudget)?.build()
    )?;

    let mut latest_budget: Option<BudgetEntry> = None;
    let mut latest_timestamp: Option<Timestamp> = None;

    for link in links {
        if let Some(record) = get(link.target.clone(), GetOptions::default())? {
            if let Some(budget_entry) = record.entry().to_app_option::<BudgetEntry>()? {
                if latest_timestamp.is_none() || budget_entry.window_start > latest_timestamp.unwrap() {
                    latest_budget = Some(budget_entry);
                    latest_timestamp = Some(budget_entry.window_start);
                }
            }
        }
    }

    match latest_budget {
        Some(budget) if (now.as_seconds() - budget.window_start.as_seconds()) < BUDGET_WINDOW_SECONDS => {
            Ok(BudgetState {
                agent: agent_address,
                remaining_ru: budget.remaining_ru,
                window_start: budget.window_start,
            })
        }
        _ => {
            // Initialize or reset budget
            let new_budget = BudgetState {
                agent: agent_address,
                remaining_ru: MAX_RU_PER_WINDOW,
                window_start: now,
            };
            create_budget_entry(agent, new_budget.remaining_ru, new_budget.window_start)?;
            Ok(new_budget)
        }
    }
}

fn create_budget_entry(agent: &AgentPubKey, remaining_ru: f32, window_start: Timestamp) -> ExternResult<ActionHash> {
    let budget_entry = BudgetEntry {
        agent: agent.clone(),
        remaining_ru,
        window_start,
    };
    let hash = create_entry(&budget_entry)?;
    let path = Path::from(format!("agent_budget.{}", agent.clone()));
    create_link(path.path_entry_hash()?, hash.clone(), LinkTypes::AgentBudget, ())?;
    Ok(hash)
}

fn update_budget_entry(agent: &AgentPubKey, remaining_ru: f32, window_start: Timestamp) -> ExternResult<ActionHash> {
    let budget_entry = BudgetEntry {
        agent: agent.clone(),
        remaining_ru,
        window_start,
    };
    let hash = create_entry(&budget_entry)?;
    let path = Path::from(format!("agent_budget.{}", agent.clone()));
    create_link(path.path_entry_hash()?, hash.clone(), LinkTypes::AgentBudget, ())?;
    Ok(hash)
}

pub struct BudgetState {
    pub agent: AgentPubKey,
    pub remaining_ru: f32,
    pub window_start: Timestamp,
}
