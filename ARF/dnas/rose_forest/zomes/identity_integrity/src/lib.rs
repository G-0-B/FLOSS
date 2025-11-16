use hdi::prelude::*;
use serde::{Deserialize, Serialize};

/// KERI-Holochain Identity Bridge
///
/// This integrity zome implements the bridge between KERI Autonomous Identifiers (AIDs)
/// and Holochain agent keys, enabling cryptographic identity that spans across
/// Holochain, AD4M, and external systems.
///
/// Architecture:
/// - KERI provides: Key Event Logs (KEL), rotation, witnesses, global identity
/// - Holochain provides: Agent-centric DHT, validation, source chains
/// - Bridge provides: Bidirectional mapping with cryptographic proofs

/// KERI Autonomous Identifier (AID)
///
/// Self-certifying identifier derived from inception key.
/// Format: "EBfdI8wr0A_F..." (Base64 of public key)
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct AutonomousIdentifier {
    /// The AID string (self-certifying identifier)
    pub aid: String,

    /// Current public key (may rotate)
    pub current_public_key: Vec<u8>,

    /// Inception public key (never changes)
    pub inception_public_key: Vec<u8>,

    /// Sequence number of current key state
    pub sequence: u64,

    /// Reference to Key Event Log
    pub kel_hash: Option<ActionHash>,

    /// Creation timestamp
    pub created_at: Timestamp,
}

/// Key Event Log Entry
///
/// Immutable record of key lifecycle events (inception, rotation, delegation, revocation)
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct KeyEventLog {
    /// The AID this log belongs to
    pub aid: String,

    /// Ordered list of key events
    pub events: Vec<KeyEvent>,

    /// Last updated timestamp
    pub updated_at: Timestamp,
}

/// Individual Key Event
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct KeyEvent {
    /// Event type
    pub event_type: KeyEventType,

    /// Sequence number
    pub sequence: u64,

    /// Previous event digest
    pub previous_event_digest: Option<String>,

    /// Keys involved in this event
    pub keys: Vec<Vec<u8>>,

    /// Witness signatures (for KERI witness network)
    pub witness_signatures: Vec<String>,

    /// Event timestamp
    pub timestamp: Timestamp,

    /// Event data (serialized JSON)
    pub data: String,
}

/// Key Event Types from KERI protocol
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug)]
pub enum KeyEventType {
    /// Inception event (creates AID)
    Inception,
    /// Rotation event (changes keys)
    Rotation,
    /// Interaction event (non-establishment)
    Interaction,
    /// Delegated inception
    DelegatedInception,
    /// Delegated rotation
    DelegatedRotation,
}

/// Bridge between KERI AID and Holochain AgentPubKey
///
/// This "seal" cryptographically binds a Holochain agent to a KERI identity,
/// enabling cross-system provenance tracking.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct IdentitySeal {
    /// The KERI AID
    pub aid: String,

    /// The Holochain agent public key
    pub agent_pubkey: AgentPubKey,

    /// Signature of agent_pubkey signed by KERI private key
    /// Proves: "I, KERI identity X, control Holochain agent Y"
    pub keri_signature: Vec<u8>,

    /// Signature of AID signed by Holochain agent key
    /// Proves: "I, Holochain agent Y, am controlled by KERI identity X"
    pub agent_signature: Vec<u8>,

    /// When this seal was created
    pub sealed_at: Timestamp,

    /// Reference to the Key Event that authorized this seal
    pub authorizing_event: ActionHash,
}

/// AD4M Language Address
///
/// Points to an AD4M Language for semantic interoperability
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct LanguageAddress {
    /// DNA hash of the AD4M language
    pub dna_hash: String,

    /// Specific expression hash within that language
    pub expression_hash: String,
}

/// AD4M Perspective Hash
///
/// References an AD4M Perspective (agent's semantic view)
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct PerspectiveHash {
    /// Hash/ID of the perspective
    pub hash: String,

    /// Optional human-readable name
    pub name: Option<String>,
}

/// Semantic Context for AD4M integration
///
/// Defines how to interpret metadata and establish shared meaning
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct SemanticContext {
    /// Schema definition (RDF, JSON-LD, SHACL, etc.)
    pub schema: String,

    /// References to shared ontologies
    pub ontology_refs: Vec<String>,

    /// Interpretation rules (how to parse metadata)
    pub interpretation_rules: Vec<InterpretationRule>,
}

/// Rule for interpreting semantic data
#[derive(Serialize, Deserialize, Clone, PartialEq, Debug, SerializedBytes)]
pub struct InterpretationRule {
    /// Rule identifier
    pub id: String,

    /// Rule type (validation, transformation, inference)
    pub rule_type: String,

    /// Rule content (executable or declarative)
    pub content: String,
}

/// Validation functions
impl AutonomousIdentifier {
    /// Validate AID format
    pub fn validate(&self) -> Result<(), String> {
        // AID should start with derivation code (e.g., "E" for Ed25519)
        if self.aid.is_empty() || !self.aid.starts_with('E') {
            return Err("Invalid AID format: must start with derivation code".to_string());
        }

        // Sequence must be monotonically increasing
        if self.sequence == 0 {
            return Err("Sequence must be > 0".to_string());
        }

        // Keys must be non-empty
        if self.current_public_key.is_empty() || self.inception_public_key.is_empty() {
            return Err("Keys cannot be empty".to_string());
        }

        Ok(())
    }
}

impl IdentitySeal {
    /// Validate seal integrity
    pub fn validate(&self) -> Result<(), String> {
        // Both signatures must be present
        if self.keri_signature.is_empty() || self.agent_signature.is_empty() {
            return Err("Seal must have both KERI and agent signatures".to_string());
        }

        // TODO: Actual cryptographic verification would happen here
        // For now, basic structural validation

        Ok(())
    }
}

// Entry type definitions
#[hdk_entry_defs]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    AutonomousIdentifier(AutonomousIdentifier),
    KeyEventLog(KeyEventLog),
    IdentitySeal(IdentitySeal),
}

// Link types for identity queries
#[hdk_link_types]
pub enum LinkTypes {
    /// Link from AgentPubKey to IdentitySeal
    AgentToSeal,
    /// Link from AID to IdentitySeal
    AIDToSeal,
    /// Link from AID to KeyEventLog
    AIDToKEL,
    /// Link from IdentitySeal to AutonomousIdentifier
    SealToAID,
    /// Link from AID anchor path to AutonomousIdentifier entry
    AIDPathToEntry,
}

/// Validation callback
pub fn validate_create_entry_identity_integrity(entry: EntryTypes) -> ExternResult<ValidateCallbackResult> {
    match entry {
        EntryTypes::AutonomousIdentifier(aid) => {
            match aid.validate() {
                Ok(_) => Ok(ValidateCallbackResult::Valid),
                Err(e) => Ok(ValidateCallbackResult::Invalid(e)),
            }
        }
        EntryTypes::IdentitySeal(seal) => {
            match seal.validate() {
                Ok(_) => Ok(ValidateCallbackResult::Valid),
                Err(e) => Ok(ValidateCallbackResult::Invalid(e)),
            }
        }
        EntryTypes::KeyEventLog(_) => {
            // KEL validation would verify event chain integrity
            // For now, accept
            Ok(ValidateCallbackResult::Valid)
        }
    }
}
