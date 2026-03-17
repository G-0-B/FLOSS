use hdi::prelude::*;
use serde::{Deserialize, Serialize};

/// hREA (Holochain Resource-Event-Agent) Integrity Zome
///
/// Implements the Resource-Event-Agent (REA) ontology for economic coordination,
/// using the ValueFlows vocabulary. Tracks value creation, transfer, and attribution
/// across the distributed knowledge ecosystem.
///
/// Core Principles:
/// - Every contribution is an economic event
/// - Value flows are transparent and traceable
/// - Attribution follows the DICE (Decentralized Impact-weighted Contribution Evaluation) methodology
/// - Moral outcomes modulate economic incentives

/// Economic Action Types from ValueFlows
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub enum EconomicAction {
    /// Initial creation of a resource
    Create,
    /// Enhancement or improvement of existing resource
    Improve,
    /// Organization, metadata addition, categorization
    Curate,
    /// Provide pinning/hosting service
    Pin,
    /// Replicate to new location/gateway
    Mirror,
    /// Verify integrity, validate correctness
    Verify,
    /// Reference in other work
    Cite,
    /// Consume or download
    Use,
    /// Create derivative work
    Derive,
    /// Transfer ownership/control
    Transfer,
    /// Remove or deprecate
    Remove,
}

/// Resource Types in the knowledge economy
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub enum ResourceType {
    /// General knowledge artifacts
    Knowledge,
    /// ML model parameters
    ModelWeights,
    /// Training or test datasets
    Dataset,
    /// Computational processing
    Computation,
    /// Data storage/pinning
    Storage,
    /// Network transfer capacity
    Bandwidth,
    /// Curation and organization
    Curation,
    /// Validation and verification
    Verification,
}

/// Quantity measurement
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct Quantity {
    /// Numeric value
    pub value: f64,

    /// Unit of measurement (bytes, hours, RU, etc.)
    pub unit: String,
}

/// Economic Event - fundamental unit of value tracking
///
/// Records an economic action performed by an agent on a resource
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct EconomicEvent {
    /// What action was performed
    pub action: EconomicAction,

    /// Agent who performed the action
    pub provider: AgentPubKey,

    /// Agent who benefits (if applicable)
    pub receiver: Option<AgentPubKey>,

    /// Reference to the resource (FileArtifact, Understanding, etc.)
    pub resource: ActionHash,

    /// Quantity of resource affected
    pub resource_quantity: Quantity,

    /// Effort invested (time, energy, etc.)
    pub effort_quantity: Option<Quantity>,

    /// When this event occurred
    pub timestamp: Timestamp,

    /// Optional context/notes
    pub note: Option<String>,

    /// Link to AD4M perspective for semantic context
    pub semantic_context: Option<String>,
}

/// Value Flow - tracks value transfer between events
///
/// Represents how value created in one event flows to another,
/// enabling attribution across complex value networks
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ValueFlow {
    /// Source economic event
    pub input_event: ActionHash,

    /// Destination economic event
    pub output_event: ActionHash,

    /// Type of resource flowing
    pub resource_type: ResourceType,

    /// Quantity flowing
    pub quantity: Quantity,

    /// When this flow was created
    pub created_at: Timestamp,

    /// Optional note
    pub note: Option<String>,
}

/// Contribution Value - result of DICE attribution
///
/// Calculated value attributed to an agent for their contributions
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ContributionValue {
    /// Agent receiving attribution
    pub agent: AgentPubKey,

    /// Resource being valued
    pub resource: ActionHash,

    /// Base value before moral weighting
    pub base_value: f64,

    /// Moral outcome multiplier (0.0 = harmful, 1.0 = neutral, >1.0 = beneficial)
    pub moral_multiplier: f64,

    /// Final attributed value (base_value * moral_multiplier)
    pub final_value: f64,

    /// When this attribution was calculated
    pub calculated_at: Timestamp,

    /// Time window used for calculation
    pub time_window: TimeWindow,

    /// Links to economic events that contributed to this value
    pub contributing_events: Vec<ActionHash>,
}

/// Time Window for value calculation
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct TimeWindow {
    /// Start timestamp
    pub start: Timestamp,

    /// End timestamp
    pub end: Timestamp,
}

/// Moral Outcome Evaluation
///
/// Assesses the ethical impact of contributions to modulate economic incentives
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub enum MoralOutcome {
    /// Causes harm (multiplier: 0.0)
    Harmful {
        severity: f64, // 0.0-1.0
        reason: String,
    },
    /// Ethically neutral (multiplier: 1.0)
    Neutral,
    /// Creates benefit (multiplier: 1.0-1.5)
    Beneficial {
        impact: f64, // 0.0-1.0
        benefits: Vec<String>,
    },
}

/// DICE (Decentralized Impact-weighted Contribution Evaluation) Score
///
/// Intermediate calculation for contribution attribution
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct DICEScore {
    /// Agent being scored
    pub agent: AgentPubKey,

    /// Raw impact score (page-rank-like algorithm)
    pub impact_score: f64,

    /// Normalized contribution ratio (sums to 1.0 across all contributors)
    pub contribution_ratio: f64,

    /// Events contributing to this score
    pub events: Vec<ActionHash>,
}

// Validation functions

impl EconomicEvent {
    pub fn validate(&self) -> Result<(), String> {
        // Validate quantities
        if self.resource_quantity.value < 0.0 {
            return Err("Resource quantity cannot be negative".to_string());
        }

        if let Some(ref effort) = self.effort_quantity {
            if effort.value < 0.0 {
                return Err("Effort quantity cannot be negative".to_string());
            }
        }

        // Validate resource reference exists (would be checked in coordinator)
        // For now, just verify it's not empty
        // The actual resource validation happens in the coordinator zome

        Ok(())
    }
}

impl ValueFlow {
    pub fn validate(&self) -> Result<(), String> {
        // Validate quantity
        if self.quantity.value < 0.0 {
            return Err("Flow quantity cannot be negative".to_string());
        }

        // Input and output events must be different
        if self.input_event == self.output_event {
            return Err("Value flow cannot be circular (same input/output)".to_string());
        }

        Ok(())
    }
}

impl ContributionValue {
    pub fn validate(&self) -> Result<(), String> {
        // Base value should be non-negative
        if self.base_value < 0.0 {
            return Err("Base value cannot be negative".to_string());
        }

        // Moral multiplier should be reasonable (0.0 to 1.5)
        if self.moral_multiplier < 0.0 || self.moral_multiplier > 1.5 {
            return Err("Moral multiplier out of range [0.0, 1.5]".to_string());
        }

        // Final value should match calculation
        let expected = self.base_value * self.moral_multiplier;
        if (self.final_value - expected).abs() > 0.01 {
            return Err("Final value doesn't match base * multiplier".to_string());
        }

        // Time window should be valid
        if self.time_window.end <= self.time_window.start {
            return Err("Invalid time window: end must be after start".to_string());
        }

        Ok(())
    }
}

// Entry type definitions
#[hdk_entry_defs]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    EconomicEvent(EconomicEvent),
    ValueFlow(ValueFlow),
    ContributionValue(ContributionValue),
}

// Link types for hREA queries
#[hdk_link_types]
pub enum LinkTypes {
    /// Link from resource to economic events
    ResourceToEvent,
    /// Link from agent to events they provided
    ProviderToEvent,
    /// Link from agent to events they received
    ReceiverToEvent,
    /// Link from event to value flows
    EventToFlow,
    /// Link from resource to contribution values
    ResourceToContribution,
    /// Link from agent to their contribution values
    AgentToContribution,
}

/// Validation callback
pub fn validate_create_entry_hrea(entry: EntryTypes) -> ExternResult<ValidateCallbackResult> {
    match entry {
        EntryTypes::EconomicEvent(event) => {
            match event.validate() {
                Ok(_) => Ok(ValidateCallbackResult::Valid),
                Err(e) => Ok(ValidateCallbackResult::Invalid(e)),
            }
        }
        EntryTypes::ValueFlow(flow) => {
            match flow.validate() {
                Ok(_) => Ok(ValidateCallbackResult::Valid),
                Err(e) => Ok(ValidateCallbackResult::Invalid(e)),
            }
        }
        EntryTypes::ContributionValue(value) => {
            match value.validate() {
                Ok(_) => Ok(ValidateCallbackResult::Valid),
                Err(e) => Ok(ValidateCallbackResult::Invalid(e)),
            }
        }
    }
}
