//! # Consent Gate Protocol — Integrity Zome
//!
//! Implements `ConsentPayload` + `ConsentDecision` entry types for ADR-12.
//!
//! First substrate-side enforcement slice for pluralistic, polycentric,
//! user-authored consent. This zome registers the consent entries and enforces
//! deterministic shape rules the LLM layer cannot evade. Cross-entry and
//! action-time checks are intentionally split to the coordinator / follow-up
//! substrate bridge work because they need chain reads or downstream action
//! context.
//!
//! ## Authored under SDD discipline
//!
//! - **Schema:** `FLOSS/docs/specs/consent-payload.schema.json` (draft-2020-12)
//! - **Spec:** `FLOSS/docs/specs/consent-payload.spec.md` (§"Validation rules
//!   and current enforcement status" — this file implements deterministic
//!   single-entry shape rules; cross-entry enforcement is documented below as
//!   coordinator / must-get follow-up work)
//! - **ADR:** `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md`
//! - **Citation anchor (philosophical):** Laukkonen et al. 2026 §"The Paternalism
//!   Problem" — consented guidance vs technocratic imposition distinction
//! - **Citation anchor (technical):** CFIS v0.3 §"4-tier authority" +
//!   §"LSM-Override" (`FLOSS/docs/architecture/CFIS_v0.3.md`)
//! - **Citation anchor (formal):** `resonance_mechanism_v2.md` §P3 selective
//!   coupling function
//!
//! ## Authored with holochain-agent-skill as canonical HDI reference
//!
//! This file is the **first real adapter_test exercise** of the
//! holochain-agent-skill (ledger entry 0013) since its 2026-05-17 install —
//! see 2026-05-19 demotion + reinstatement consensus claims for context.
//! Specific patterns applied from the skill's Patterns.md + Pitfalls Checklist:
//!
//! - Entry structs do NOT carry `agent_pub_key` or `created_at` fields
//!   (these live in the action header, queryable via `must_get_action`)
//! - All `Option<T>` fields on entry types use `#[serde(default)]` for
//!   forward-compatible schema evolution
//! - `validate()` is purely deterministic — no `get()`, `get_links()`,
//!   `agent_info()`, `sys_time()` calls
//! - Validation dispatch uses `op.flattened::<EntryTypes, LinkTypes>()`
//!
//! ## Version skew note (surfaced by skill on first invocation)
//!
//! Workspace pins `hdi = "=0.5.1"`. Skill teaches HDI 0.7.1 / HDK 0.6.1.
//! This file targets the workspace version to compile against current
//! infrastructure. Future workspace-version bump (open work-item) will need
//! API migration; the structural patterns here are version-neutral and should
//! survive the bump unchanged.

use hdi::prelude::*;
use serde::{Deserialize, Serialize};

// =============================================================================
// SECTION 1: Enum types matching consent-payload.schema.json
// =============================================================================

/// Class of memetic pattern being offered for consent.
///
/// Per ConsentPayload.schema.json `pattern_type` enum. `kernel` and
/// `constitution` are inherently Substrate-class per ADR-12 §6 — the
/// integrity zome enforces this in `validate_consent_payload`.
#[derive(Serialize, Deserialize, Clone, PartialEq, Eq, Debug, SerializedBytes)]
pub enum PatternType {
    Kernel,
    Adr,
    FrameTranslation,
    VoterPersona,
    Constitution,
    Claim,
    Skill,
    MemoryEntry,
    Other,
}

/// Mirrors consensus-gate blast-radius semantics. Substrate-class is
/// non-overridable once consent is given (per ADR-12 §6).
#[derive(Serialize, Deserialize, Clone, PartialEq, Eq, Debug, SerializedBytes)]
pub enum BlastRadius {
    Local,
    Module,
    System,
    Substrate,
}

/// Authorization gradient. Higher scopes imply lower scopes for the same
/// `pattern_hash` (read_only < integrate < propagate < bind).
#[derive(Serialize, Deserialize, Clone, PartialEq, Eq, Debug, SerializedBytes)]
pub enum ConsentScope {
    ReadOnly,
    Integrate,
    Propagate,
    Bind,
}

/// Refusal-mode options per ADR-12 §4. `tourist_observe` operationalizes
/// the CFIS `[auth:tourist]` authority tier. `counter_propose` converts
/// CFIS Tier-4 divergence into a substrate-level operation by routing the
/// counter through the consensus gateway as a new Claim.
#[derive(Serialize, Deserialize, Clone, PartialEq, Eq, Debug, SerializedBytes)]
pub enum RefusalMode {
    Reject,
    BoundedAccept,
    TouristObserve,
    CounterPropose,
}

/// ConsentDecision outcome. `accepted` grants full requested scope;
/// `bounded_accept` narrows it; `tourist_observe` per CFIS; `counter_propose`
/// adds a counter-frame reference; `rejected` declines entirely.
#[derive(Serialize, Deserialize, Clone, PartialEq, Eq, Debug, SerializedBytes)]
pub enum Outcome {
    Accepted,
    BoundedAccept,
    TouristObserve,
    CounterPropose,
    Rejected,
}

// =============================================================================
// SECTION 2: Entry types — ConsentPayload + ConsentDecision
// =============================================================================

/// A request offered to an agent to load, integrate, propagate, or bind a
/// memetic pattern. Written by the proposer; awaits a `ConsentDecision`
/// from the recipient.
///
/// Note: `agent_pub_key`-style fields (proposer/recipient identity) live as
/// String DIDs (KERI AID / AD4M DID / Holochain AgentPubKey b64) on the
/// entry because they may span substrates. The action header captures the
/// actual writer. Writer ↔ proposer/recipient DID binding is not enforced in
/// this first slice because that requires an explicit cross-substrate identity
/// mapping; it remains a follow-up rule in the spec.
///
/// Note: `submitted_at` is captured here as Timestamp because it carries
/// schema-meaningful semantics (the deadline `refusable_until` is computed
/// relative to it). For pure "when was this written" the action header is
/// authoritative; this field is the proposer's stated intent timestamp.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ConsentPayload {
    /// UUID v7 (time-sortable) unique per consent request
    pub payload_id: String,

    /// Stable identifier of the pattern being offered (ADR hash, kernel
    /// version tag, frame id, voter persona name, claim id, etc.)
    pub pattern_id: String,

    /// Class of memetic pattern. `Kernel` and `Constitution` are
    /// Substrate-class by default.
    pub pattern_type: PatternType,

    /// SHA-256 (64-char hex) reference to the exact payload content
    pub pattern_hash: String,

    /// DID of who is offering — KERI AID, AD4M DID, or Holochain AgentPubKey b64
    pub proposer_did: String,

    /// DID of who is being asked. For collective consent, use a group DID.
    pub recipient_did: String,

    /// Mirrors consensus gate blast-radii. Substrate-class consent is
    /// non-overridable once given (per ADR-12 §6).
    pub blast_radius: BlastRadius,

    /// Authorization gradient (non-empty per validation rule 1)
    pub consent_scope: Vec<ConsentScope>,

    /// Which refusal options the recipient has. All four allowed by default
    /// (per ADR-12 §4); constraining requires Substrate-class authorization.
    #[serde(default = "default_refusal_modes")]
    pub refusal_modes: Vec<RefusalMode>,

    /// ISO-8601 timestamp by which recipient must decide. None = open-ended.
    #[serde(default)]
    pub refusable_until: Option<Timestamp>,

    /// For hierarchical patterns (e.g. constitution → derived claim).
    /// Action hash reference to parent ConsentPayload.
    #[serde(default)]
    pub parent_consent_id: Option<ActionHash>,

    /// Optional context explaining the consent request
    #[serde(default)]
    pub rationale: Option<String>,

    /// Proposer-stated submission time (schema-meaningful for refusable_until
    /// computation). Action header is authoritative for cryptographic "when
    /// written" but this is the semantic intent timestamp.
    pub submitted_at: Timestamp,
}

fn default_refusal_modes() -> Vec<RefusalMode> {
    vec![
        RefusalMode::Reject,
        RefusalMode::BoundedAccept,
        RefusalMode::TouristObserve,
        RefusalMode::CounterPropose,
    ]
}

/// An agent's explicit decision on a `ConsentPayload`. Written by the
/// recipient (or a group's quorum mechanism for collective DIDs).
/// Append-only on source chain.
#[hdk_entry_helper]
#[derive(Clone, PartialEq)]
pub struct ConsentDecision {
    /// UUID v7 unique per decision
    pub decision_id: String,

    /// Action-hash reference to the ConsentPayload being decided on. This
    /// is stronger than a UUID lookup — the hash binds the decision to a
    /// specific cryptographic commitment.
    pub payload_action_hash: ActionHash,

    /// Decider DID (string, cross-substrate). Action header captures the
    /// Holochain agent who wrote this; this field captures the substrate-
    /// agnostic identity claim.
    pub decider_did: String,

    /// Per ADR-12 §4 refusal modes + `Accepted` as full-scope grant.
    pub outcome: Outcome,

    /// Subset of the ConsentPayload's consent_scope actually granted.
    /// MUST be a subset (validation rule 5). Empty iff outcome=Rejected
    /// (validation rule 6).
    pub scope_granted: Vec<ConsentScope>,

    /// Required when outcome != Accepted (validation rule 8). The "why"
    /// behind the bound, refusal, or counter-frame.
    #[serde(default)]
    pub rationale: Option<String>,

    /// If outcome=CounterPropose: action hash of the counter-frame Claim
    /// in the consensus gateway. Required when outcome=CounterPropose
    /// (validation rule 7).
    #[serde(default)]
    pub counter_frame_ref: Option<ActionHash>,

    /// If consent is time-bounded. None = permanent grant.
    #[serde(default)]
    pub expires_at: Option<Timestamp>,

    /// Decider's stated decision-time semantic timestamp.
    pub decided_at: Timestamp,
}

// =============================================================================
// SECTION 3: Entry + link type registration
// =============================================================================

#[hdk_entry_types]
#[unit_enum(UnitEntryTypes)]
pub enum EntryTypes {
    ConsentPayload(ConsentPayload),
    ConsentDecision(ConsentDecision),
}

#[hdk_link_types]
pub enum LinkTypes {
    /// Anchor → all ConsentPayloads with a given pattern_hash (for
    /// "who has been offered this pattern?" queries from outside the
    /// validation path — coordinator zome territory)
    PatternHashToPayload,
    /// ConsentPayload → ConsentDecision (the decision answers the payload)
    PayloadToDecision,
    /// Anchor → all decisions by a decider_did (for "what has this agent
    /// consented to?" reverse-index)
    DeciderToDecision,
}

// =============================================================================
// SECTION 4: Validation — deterministic single-entry rules from
// consent-payload.spec.md §"Validation rules and current enforcement status".
// Cross-entry rules that require resolving another action are explicitly
// documented in Section 5.
// =============================================================================

/// Top-level validation callback. Dispatches to per-entry-type validators
/// + per-op-type post-checks. Pure / deterministic — no DHT reads.
#[hdk_extern]
pub fn validate(op: Op) -> ExternResult<ValidateCallbackResult> {
    match op.flattened::<EntryTypes, LinkTypes>()? {
        FlatOp::StoreEntry(store) => match store {
            OpEntry::CreateEntry { app_entry, .. } => match app_entry {
                EntryTypes::ConsentPayload(payload) => validate_consent_payload(&payload),
                EntryTypes::ConsentDecision(decision) => validate_consent_decision(&decision),
            },
            // ConsentPayload / ConsentDecision are append-only governance
            // records: a decision is superseded by authoring a NEW entry (with a
            // fresh consent decision), never by mutating an existing one.
            // Accepting an update would let a recorded consent be silently
            // replaced on the DHT without a new decision. Reject the update.
            OpEntry::UpdateEntry { .. } => Ok(ValidateCallbackResult::Invalid(
                "E_CONSENT_APPEND_ONLY: ConsentPayload/ConsentDecision entries are \
                 append-only and cannot be updated — author a new entry instead"
                    .to_string(),
            )),
            _ => Ok(ValidateCallbackResult::Valid),
        },
        // This integrity zome governs only the two append-only consent entry
        // types, so any update/delete action routed here concerns one of them.
        // Both are forbidden — consent history is immutable.
        FlatOp::RegisterUpdate(_) => Ok(ValidateCallbackResult::Invalid(
            "E_CONSENT_APPEND_ONLY: ConsentPayload/ConsentDecision entries cannot be updated"
                .to_string(),
        )),
        FlatOp::RegisterDelete(_) => Ok(ValidateCallbackResult::Invalid(
            "E_CONSENT_APPEND_ONLY: ConsentPayload/ConsentDecision entries cannot be deleted"
                .to_string(),
        )),
        _ => Ok(ValidateCallbackResult::Valid),
    }
}

/// Validate a ConsentPayload against the deterministic payload rules from the
/// spec's current enforcement-status table:
//
// Note: this fn is `pub` so the unit-test module at the bottom of this file
// can exercise the validation rules directly without a Holochain conductor.
// Per the holochain-agent-skill's pure-validate invariant, validate_*
// functions take entry references + return ExternResult, which means they're
// trivially testable as pure Rust.
/// 1. `pattern_hash` is 64-char lowercase hex (SHA-256 format)
/// 2. `consent_scope` is non-empty
/// 3. `proposer_did` and `recipient_did` are non-empty
/// 9. `pattern_type ∈ {Kernel, Constitution}` with `blast_radius < Substrate`
///    is rejected — these are inherently substrate-class
///
/// Rules 4, 10 (subset checks + action-time enforcement) are out of
/// validation-scope here because they require either reading the referenced
/// ConsentPayload from chain (forbidden in validate()) or post-validation
/// action-layer enforcement (a coordinator-zome concern).
pub fn validate_consent_payload(payload: &ConsentPayload) -> ExternResult<ValidateCallbackResult> {
    // Rule 1: pattern_hash is SHA-256 format (64 hex chars, lowercase)
    if payload.pattern_hash.len() != 64 {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_PATTERN_HASH_FORMAT: pattern_hash length {} (expected 64 SHA-256 hex chars)",
            payload.pattern_hash.len()
        )));
    }
    if !payload
        .pattern_hash
        .chars()
        .all(|c| c.is_ascii_hexdigit() && (c.is_ascii_digit() || c.is_ascii_lowercase()))
    {
        return Ok(ValidateCallbackResult::Invalid(
            "E_PATTERN_HASH_FORMAT: pattern_hash contains non-lowercase-hex characters".into(),
        ));
    }

    // Rule 2: consent_scope is non-empty
    if payload.consent_scope.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_CONSENT_SCOPE_EMPTY: consent_scope MUST contain at least one of \
             [ReadOnly, Integrate, Propagate, Bind]"
                .into(),
        ));
    }

    // Rule 3: proposer_did and recipient_did are non-empty
    if payload.proposer_did.trim().is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_PROPOSER_DID_EMPTY".into(),
        ));
    }
    if payload.recipient_did.trim().is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_RECIPIENT_DID_EMPTY".into(),
        ));
    }

    // Rule 9: Kernel / Constitution patterns MUST be Substrate-class.
    // Reasoning: these are the heaviest binding-class patterns; offering
    // them at a lower blast radius would let them bind without the
    // Substrate-class consensus threshold (0.85 per ADR-Suite v2.0). This is
    // ADR-12 §6 substrate-layer enforcement.
    if matches!(
        payload.pattern_type,
        PatternType::Kernel | PatternType::Constitution
    ) && !matches!(payload.blast_radius, BlastRadius::Substrate)
    {
        return Ok(ValidateCallbackResult::Invalid(
            "E_SUBSTRATE_CLASS_REQUIRED: ConsentPayload with pattern_type=Kernel or Constitution \
             MUST have blast_radius=Substrate (ADR-12 §6 invariant)"
                .into(),
        ));
    }

    // Rule additional: refusal_modes is non-empty when explicitly provided.
    // (Default value via #[serde(default)] is the full 4-mode list, so this
    // only triggers if a caller explicitly passes an empty Vec.)
    if payload.refusal_modes.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_REFUSAL_MODES_EMPTY: refusal_modes MUST contain at least one of \
             [Reject, BoundedAccept, TouristObserve, CounterPropose] — constraining \
             refusal options to none violates ADR-12 §4 user-authored-autonomy invariant"
                .into(),
        ));
    }

    Ok(ValidateCallbackResult::Valid)
}

/// Validate a ConsentDecision against the deterministic decision rules from the
/// spec's current enforcement-status table:
/// 5. `scope_granted` is non-empty iff outcome != Rejected (deferred: full
///    subset-check against the referenced ConsentPayload requires reading
///    chain, forbidden here; we enforce the contradiction-free invariant
///    instead and defer subset enforcement to the coordinator layer)
/// 6. outcome=Rejected ⟹ `scope_granted == []`
/// 7. outcome=CounterPropose ⟹ `counter_frame_ref` is Some
/// 8. outcome != Accepted ⟹ `rationale` is Some + non-empty
///
/// Rules 1-3 (well-formed UUIDs, hash references) are partially structural —
/// `payload_action_hash` is typed as ActionHash so HDI handles the format;
/// `decision_id` UUID format is not validated here (deferred to coordinator).
fn validate_consent_decision(decision: &ConsentDecision) -> ExternResult<ValidateCallbackResult> {
    // Rule 3 (decider): decider_did is non-empty
    if decision.decider_did.trim().is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_DECIDER_DID_EMPTY".into(),
        ));
    }

    // Rule 6: outcome=Rejected ⟹ scope_granted is empty
    if matches!(decision.outcome, Outcome::Rejected) && !decision.scope_granted.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_REJECTED_WITH_SCOPE: outcome=Rejected MUST have empty scope_granted; \
             granting any scope contradicts rejection (ADR-12 §4)"
                .into(),
        ));
    }

    // Rule 5 (contradiction-free side): outcome != Rejected ⟹ scope_granted
    // MUST be non-empty. Full subset-check against the referenced payload's
    // consent_scope happens in the coordinator zome (would require DHT read).
    if !matches!(decision.outcome, Outcome::Rejected) && decision.scope_granted.is_empty() {
        return Ok(ValidateCallbackResult::Invalid(format!(
            "E_NON_REJECT_EMPTY_SCOPE: outcome={:?} with empty scope_granted is contradictory — \
             accepted/bounded/tourist/counter outcomes MUST grant at least one scope",
            decision.outcome
        )));
    }

    // Rule 7: outcome=CounterPropose ⟹ counter_frame_ref is Some
    if matches!(decision.outcome, Outcome::CounterPropose) && decision.counter_frame_ref.is_none() {
        return Ok(ValidateCallbackResult::Invalid(
            "E_COUNTER_WITHOUT_REF: outcome=CounterPropose MUST include counter_frame_ref \
             pointing to the counter-frame Claim in the consensus gateway (ADR-12 §4)"
                .into(),
        ));
    }

    // Rule 8: outcome != Accepted ⟹ rationale is Some + non-empty
    if !matches!(decision.outcome, Outcome::Accepted) {
        match &decision.rationale {
            None => {
                return Ok(ValidateCallbackResult::Invalid(format!(
                    "E_NONACCEPT_NO_RATIONALE: outcome={:?} MUST include rationale \
                     (ADR-12 §4 — refusal-modes require explanation to preserve \
                     epistemic accountability)",
                    decision.outcome
                )));
            }
            Some(r) if r.trim().is_empty() => {
                return Ok(ValidateCallbackResult::Invalid(format!(
                    "E_NONACCEPT_EMPTY_RATIONALE: outcome={:?} rationale is whitespace-only",
                    decision.outcome
                )));
            }
            _ => {}
        }
    }

    Ok(ValidateCallbackResult::Valid)
}

// =============================================================================
// SECTION 5: Deferred validations (documented, not yet enforced here)
// =============================================================================
//
// These rules from consent-payload.spec.md §"Validation rules and current
// enforcement status" require chain
// reads or action-header inspection beyond what the integrity zome can do
// in a single validate() call:
//
// - Rule 4 (`ConsentDecision.payload_action_hash` references an existing
//   ConsentPayload on the recipient's source chain). This requires
//   `must_get_action()`, which IS allowed in validate() per HDI 0.5+, but
//   adds complexity + cross-action dependency. Deferred to v0.2.
//
// - Rule 5 full subset check (`scope_granted ⊆ consent_scope`) — same
//   reason: requires resolving the referenced ConsentPayload to compare
//   scope sets. Coordinator-zome enforcement on the action-call path is
//   the right shape; the integrity zome here catches the contradiction
//   patterns (Rule 6, Rule 5-side, Rule 7, Rule 8).
//
// - Rule 10 (action-time enforcement: no action that acts on a pattern
//   with `blast_radius ∈ {System, Substrate}` may proceed without a
//   matching ConsentDecision in the actor's source chain). This is a
//   coordinator-zome-level invariant — the integrity zome here governs the
//   shape of the consent records; the coordinator governs the application
//   of consent gates to downstream actions. Tracking as open work in
//   ADR-12 §7 + spec §"Validation status".
//
// =============================================================================
// SECTION 6: Test scaffolding (Sweettest)
// =============================================================================
//
// Rust unit tests below cover the deterministic shape rules. Tryorama scenarios
// live in `ARF/tests/tryorama/consent_gate.test.ts`, but still require a local
// `hc`/`holochain` toolchain to pack and execute the hApp. Coverage targets:
//   - Happy path: ConsentPayload create → ConsentDecision create (Accepted)
//   - Refusal path: Rejected outcome with empty scope_granted (passes)
//   - Refusal path: Rejected with scope_granted (E_REJECTED_WITH_SCOPE)
//   - Counter-frame: CounterPropose without ref (E_COUNTER_WITHOUT_REF)
//   - Substrate-class: Kernel pattern with Local blast_radius
//     (E_SUBSTRATE_CLASS_REQUIRED)
//   - Empty scope: ConsentPayload with consent_scope=[] (E_CONSENT_SCOPE_EMPTY)
//   - Schema-evolution: deserializing a ConsentPayload missing the
//     `parent_consent_id` field (must succeed via #[serde(default)])

#[cfg(test)]
mod tests {
    use super::*;

    fn timestamp() -> Timestamp {
        Timestamp::from_micros(1_000_000)
    }

    fn action_hash() -> ActionHash {
        ActionHash::from_raw_36(vec![7_u8; 36])
    }

    fn valid_payload() -> ConsentPayload {
        ConsentPayload {
            payload_id: "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0001".into(),
            pattern_id: "ADR-12".into(),
            pattern_type: PatternType::Adr,
            pattern_hash: "a".repeat(64),
            proposer_did: "did:floss:proposer".into(),
            recipient_did: "did:floss:recipient".into(),
            blast_radius: BlastRadius::System,
            consent_scope: vec![ConsentScope::ReadOnly, ConsentScope::Integrate],
            refusal_modes: default_refusal_modes(),
            refusable_until: None,
            parent_consent_id: None,
            rationale: Some("ADR-12 implementation test payload".into()),
            submitted_at: timestamp(),
        }
    }

    fn valid_decision() -> ConsentDecision {
        ConsentDecision {
            decision_id: "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0002".into(),
            payload_action_hash: action_hash(),
            decider_did: "did:floss:recipient".into(),
            outcome: Outcome::Accepted,
            scope_granted: vec![ConsentScope::ReadOnly],
            rationale: None,
            counter_frame_ref: None,
            expires_at: None,
            decided_at: timestamp(),
        }
    }

    fn invalid_reason(result: ValidateCallbackResult) -> String {
        match result {
            ValidateCallbackResult::Invalid(reason) => reason,
            other => panic!("expected Invalid, got {other:?}"),
        }
    }

    #[test]
    fn valid_payload_passes_shape_validation() {
        let result = validate_consent_payload(&valid_payload()).unwrap();

        assert!(matches!(result, ValidateCallbackResult::Valid));
    }

    #[test]
    fn payload_rejects_non_lowercase_sha256_hash() {
        let mut payload = valid_payload();
        payload.pattern_hash = "A".repeat(64);

        let reason = invalid_reason(validate_consent_payload(&payload).unwrap());

        assert!(reason.contains("E_PATTERN_HASH_FORMAT"));
    }

    #[test]
    fn payload_rejects_empty_scope() {
        let mut payload = valid_payload();
        payload.consent_scope.clear();

        let reason = invalid_reason(validate_consent_payload(&payload).unwrap());

        assert!(reason.contains("E_CONSENT_SCOPE_EMPTY"));
    }

    #[test]
    fn payload_requires_dids() {
        let mut payload = valid_payload();
        payload.proposer_did = " ".into();

        let reason = invalid_reason(validate_consent_payload(&payload).unwrap());

        assert!(reason.contains("E_PROPOSER_DID_EMPTY"));
    }

    #[test]
    fn kernel_payload_must_be_substrate_class() {
        let mut payload = valid_payload();
        payload.pattern_type = PatternType::Kernel;
        payload.blast_radius = BlastRadius::Local;

        let reason = invalid_reason(validate_consent_payload(&payload).unwrap());

        assert!(reason.contains("E_SUBSTRATE_CLASS_REQUIRED"));
    }

    #[test]
    fn valid_accepted_decision_passes_shape_validation() {
        let result = validate_consent_decision(&valid_decision()).unwrap();

        assert!(matches!(result, ValidateCallbackResult::Valid));
    }

    #[test]
    fn rejected_decision_must_not_grant_scope() {
        let mut decision = valid_decision();
        decision.outcome = Outcome::Rejected;
        decision.rationale = Some("No consent granted".into());

        let reason = invalid_reason(validate_consent_decision(&decision).unwrap());

        assert!(reason.contains("E_REJECTED_WITH_SCOPE"));
    }

    #[test]
    fn non_rejected_decision_must_grant_some_scope() {
        let mut decision = valid_decision();
        decision.scope_granted.clear();

        let reason = invalid_reason(validate_consent_decision(&decision).unwrap());

        assert!(reason.contains("E_NON_REJECT_EMPTY_SCOPE"));
    }

    #[test]
    fn counter_proposal_requires_counter_frame_ref() {
        let mut decision = valid_decision();
        decision.outcome = Outcome::CounterPropose;
        decision.rationale = Some("Counter-frame preserves Tier-4 divergence".into());

        let reason = invalid_reason(validate_consent_decision(&decision).unwrap());

        assert!(reason.contains("E_COUNTER_WITHOUT_REF"));
    }

    #[test]
    fn non_accepted_decision_requires_rationale() {
        let mut decision = valid_decision();
        decision.outcome = Outcome::TouristObserve;

        let reason = invalid_reason(validate_consent_decision(&decision).unwrap());

        assert!(reason.contains("E_NONACCEPT_NO_RATIONALE"));
    }
}
