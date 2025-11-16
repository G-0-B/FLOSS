use hdk::prelude::*;
use hrea_integrity::{
    EconomicEvent, EconomicAction, ValueFlow, ContributionValue, ResourceType,
    Quantity, TimeWindow, DICEScore, MoralOutcome,
    EntryTypes, LinkTypes,
};
use std::collections::HashMap;

pub mod vector_bridge;
pub use vector_bridge::{
    EconomicEventEmbedding, ValueWeightedEmbedding, ValueWeightedQuery, ValueWeightedResult,
    search_economic_events, search_value_weighted,
};

/// hREA Coordinator Zome
///
/// Implements economic coordination functions for the distributed knowledge economy:
/// 1. Record economic events (contributions, usage, curation, etc.)
/// 2. Create value flows between events
/// 3. Calculate contribution attribution using DICE methodology
/// 4. Apply moral outcome weighting
/// 5. Query value networks

#[hdk_extern]
pub fn record_economic_event(input: RecordEventInput) -> ExternResult<ActionHash> {
    let agent = agent_info()?.agent_latest_pubkey;

    // Verify agent matches provider (only provider can record their own events)
    if agent != input.provider {
        return Err(wasm_error!(WasmErrorInner::Guest(
            "Agent mismatch: only provider can record their own events".to_string()
        )));
    }

    // Create the economic event
    let event = EconomicEvent {
        action: input.action,
        provider: input.provider.clone(),
        receiver: input.receiver.clone(),
        resource: input.resource.clone(),
        resource_quantity: input.resource_quantity,
        effort_quantity: input.effort_quantity,
        timestamp: sys_time()?,
        note: input.note,
        semantic_context: input.semantic_context,
    };

    let event_hash = create_entry(EntryTypes::EconomicEvent(event.clone()))?;

    // Create links for efficient querying

    // Link resource -> event
    create_link(
        input.resource.clone(),
        event_hash.clone(),
        LinkTypes::ResourceToEvent,
        (),
    )?;

    // Link provider -> event
    create_link(
        input.provider.into(),
        event_hash.clone(),
        LinkTypes::ProviderToEvent,
        (),
    )?;

    // Link receiver -> event (if applicable)
    if let Some(receiver) = input.receiver {
        create_link(
            receiver.into(),
            event_hash.clone(),
            LinkTypes::ReceiverToEvent,
            (),
        )?;
    }

    // Emit signal for real-time coordination
    emit_signal(EconomicEventSignal {
        event_hash: event_hash.clone(),
        action: event.action,
        provider: event.provider,
        resource: event.resource,
    })?;

    Ok(event_hash)
}

#[hdk_extern]
pub fn create_value_flow(input: CreateFlowInput) -> ExternResult<ActionHash> {
    // Verify both events exist
    let input_event = get_economic_event(input.input_event.clone())?
        .ok_or(wasm_error!(WasmErrorInner::Guest("Input event not found".to_string())))?;
    let output_event = get_economic_event(input.output_event.clone())?
        .ok_or(wasm_error!(WasmErrorInner::Guest("Output event not found".to_string())))?;

    // Verify resource compatibility
    verify_resource_compatibility(&input_event, &output_event)?;

    // Create the value flow
    let flow = ValueFlow {
        input_event: input.input_event.clone(),
        output_event: input.output_event.clone(),
        resource_type: input.resource_type,
        quantity: input.quantity,
        created_at: sys_time()?,
        note: input.note,
    };

    let flow_hash = create_entry(EntryTypes::ValueFlow(flow))?;

    // Link events to flow for graph traversal
    create_link(
        input.input_event,
        flow_hash.clone(),
        LinkTypes::EventToFlow,
        (),
    )?;

    create_link(
        input.output_event,
        flow_hash.clone(),
        LinkTypes::EventToFlow,
        (),
    )?;

    Ok(flow_hash)
}

#[hdk_extern]
pub fn calculate_contribution_value(input: CalculateContributionInput) -> ExternResult<Vec<ContributionValue>> {
    // Get all economic events for the resource within time window
    let events = get_events_for_resource_in_window(input.resource.clone(), input.time_window.clone())?;

    if events.is_empty() {
        return Ok(vec![]);
    }

    // Build value flow graph
    let value_graph = build_value_graph(&events)?;

    // Apply DICE methodology for impact-weighted attribution
    let dice_scores = calculate_dice_scores(&value_graph)?;

    // Calculate moral outcome for each contribution
    let mut contributions = Vec::new();

    for score in dice_scores {
        // Get agent's events
        let agent_events: Vec<_> = events.iter()
            .filter(|(_, event)| event.provider == score.agent)
            .map(|(hash, _)| hash.clone())
            .collect();

        // Calculate base value (normalized contribution ratio)
        let base_value = score.contribution_ratio;

        // Evaluate moral outcome
        let moral_multiplier = evaluate_moral_outcome(&score.agent, &agent_events)?;

        // Create contribution value entry
        let contribution = ContributionValue {
            agent: score.agent.clone(),
            resource: input.resource.clone(),
            base_value,
            moral_multiplier,
            final_value: base_value * moral_multiplier,
            calculated_at: sys_time()?,
            time_window: input.time_window.clone(),
            contributing_events: agent_events,
        };

        let contribution_hash = create_entry(EntryTypes::ContributionValue(contribution.clone()))?;

        // Link resource -> contribution
        create_link(
            input.resource.clone(),
            contribution_hash.clone(),
            LinkTypes::ResourceToContribution,
            (),
        )?;

        // Link agent -> contribution
        create_link(
            score.agent.into(),
            contribution_hash,
            LinkTypes::AgentToContribution,
            (),
        )?;

        contributions.push(contribution);
    }

    Ok(contributions)
}

#[hdk_extern]
pub fn get_events_for_resource(resource: ActionHash) -> ExternResult<Vec<EconomicEvent>> {
    let links = get_links(
        GetLinksInputBuilder::try_new(resource, LinkTypes::ResourceToEvent)?.build(),
    )?;

    let mut events = Vec::new();

    for link in links {
        let event_hash: ActionHash = link.target.into();
        if let Some(event) = get_economic_event(event_hash)? {
            events.push(event);
        }
    }

    Ok(events)
}

#[hdk_extern]
pub fn get_agent_contributions(agent: AgentPubKey) -> ExternResult<Vec<ContributionValue>> {
    let links = get_links(
        GetLinksInputBuilder::try_new(agent.into(), LinkTypes::AgentToContribution)?.build(),
    )?;

    let mut contributions = Vec::new();

    for link in links {
        let contribution_hash: ActionHash = link.target.into();
        if let Some(contribution) = get_contribution_value(contribution_hash)? {
            contributions.push(contribution);
        }
    }

    Ok(contributions)
}

// Helper functions

fn get_economic_event(event_hash: ActionHash) -> ExternResult<Option<EconomicEvent>> {
    let record = get(event_hash, GetOptions::default())?;

    match record {
        Some(r) => {
            let event: EconomicEvent = r.entry().to_app_option()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                .ok_or(wasm_error!(WasmErrorInner::Guest("Expected EconomicEvent".to_string())))?;
            Ok(Some(event))
        }
        None => Ok(None),
    }
}

fn get_contribution_value(contribution_hash: ActionHash) -> ExternResult<Option<ContributionValue>> {
    let record = get(contribution_hash, GetOptions::default())?;

    match record {
        Some(r) => {
            let contribution: ContributionValue = r.entry().to_app_option()
                .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                .ok_or(wasm_error!(WasmErrorInner::Guest("Expected ContributionValue".to_string())))?;
            Ok(Some(contribution))
        }
        None => Ok(None),
    }
}

fn get_events_for_resource_in_window(
    resource: ActionHash,
    time_window: TimeWindow,
) -> ExternResult<Vec<(ActionHash, EconomicEvent)>> {
    let links = get_links(
        GetLinksInputBuilder::try_new(resource, LinkTypes::ResourceToEvent)?.build(),
    )?;

    let mut events = Vec::new();

    for link in links {
        let event_hash: ActionHash = link.target.into();
        if let Some(event) = get_economic_event(event_hash.clone())? {
            // Filter by time window
            if event.timestamp >= time_window.start && event.timestamp <= time_window.end {
                events.push((event_hash, event));
            }
        }
    }

    Ok(events)
}

fn build_value_graph(events: &[(ActionHash, EconomicEvent)]) -> ExternResult<ValueGraph> {
    let mut graph = ValueGraph {
        nodes: HashMap::new(),
        edges: Vec::new(),
    };

    // Add nodes (events)
    for (hash, event) in events {
        graph.nodes.insert(hash.clone(), event.clone());
    }

    // Add edges (value flows)
    for (event_hash, _) in events {
        let links = get_links(
            GetLinksInputBuilder::try_new(event_hash.clone(), LinkTypes::EventToFlow)?.build(),
        )?;

        for link in links {
            let flow_hash: ActionHash = link.target.into();
            if let Some(flow_record) = get(flow_hash, GetOptions::default())? {
                let flow: ValueFlow = flow_record.entry().to_app_option()
                    .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string())))?
                    .ok_or(wasm_error!(WasmErrorInner::Guest("Expected ValueFlow".to_string())))?;

                graph.edges.push(flow);
            }
        }
    }

    Ok(graph)
}

fn calculate_dice_scores(graph: &ValueGraph) -> ExternResult<Vec<DICEScore>> {
    // Implement DICE (Decentralized Impact-weighted Contribution Evaluation)
    // Based on page-rank-like algorithm for impact scoring

    // Group events by agent
    let mut agent_events: HashMap<AgentPubKey, Vec<ActionHash>> = HashMap::new();

    for (event_hash, event) in &graph.nodes {
        agent_events.entry(event.provider.clone())
            .or_insert_with(Vec::new)
            .push(event_hash.clone());
    }

    // Calculate impact scores (simplified version)
    // In production, would implement full page-rank algorithm over value flow graph
    let mut scores = Vec::new();
    let total_events = graph.nodes.len() as f64;

    for (agent, events) in agent_events {
        let event_count = events.len() as f64;
        let impact_score = event_count / total_events; // Simplified: proportion of contributions

        scores.push(DICEScore {
            agent,
            impact_score,
            contribution_ratio: impact_score, // Will be normalized next
            events,
        });
    }

    // Normalize to sum to 1.0
    let total_impact: f64 = scores.iter().map(|s| s.impact_score).sum();

    for score in &mut scores {
        score.contribution_ratio = score.impact_score / total_impact;
    }

    Ok(scores)
}

fn evaluate_moral_outcome(
    agent: &AgentPubKey,
    events: &[ActionHash],
) -> ExternResult<f64> {
    // Simplified moral outcome evaluation
    // In production, would integrate ASHFLIES semantic analysis

    // For now, return neutral (1.0) for all contributions
    // Future: analyze contribution content, impact, alignment with ULLK principles

    Ok(1.0)
}

fn verify_resource_compatibility(
    input_event: &EconomicEvent,
    output_event: &EconomicEvent,
) -> ExternResult<()> {
    // Verify the events reference compatible resources
    // For now, just verify both events exist (basic check)

    Ok(())
}

// Data structures

#[derive(Serialize, Deserialize, Debug)]
pub struct RecordEventInput {
    pub action: EconomicAction,
    pub provider: AgentPubKey,
    pub receiver: Option<AgentPubKey>,
    pub resource: ActionHash,
    pub resource_quantity: Quantity,
    pub effort_quantity: Option<Quantity>,
    pub note: Option<String>,
    pub semantic_context: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateFlowInput {
    pub input_event: ActionHash,
    pub output_event: ActionHash,
    pub resource_type: ResourceType,
    pub quantity: Quantity,
    pub note: Option<String>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CalculateContributionInput {
    pub resource: ActionHash,
    pub time_window: TimeWindow,
}

#[derive(Clone, Debug)]
struct ValueGraph {
    nodes: HashMap<ActionHash, EconomicEvent>,
    edges: Vec<ValueFlow>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct EconomicEventSignal {
    event_hash: ActionHash,
    action: EconomicAction,
    provider: AgentPubKey,
    resource: ActionHash,
}
