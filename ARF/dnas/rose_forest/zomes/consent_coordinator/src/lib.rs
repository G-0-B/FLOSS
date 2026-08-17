//! # Consent Gate Protocol — Coordinator Zome
//!
//! Application-call surface for ADR-12 ConsentPayload / ConsentDecision
//! records. This zome is intentionally separate from the existing
//! `rose_forest` coordinator: linking two integrity crates into one
//! coordinator produced duplicate Holochain export symbols, so each
//! integrity zome gets its own coordinator dependency.
//!
//! Spec references:
//! - `FLOSS/docs/specs/consent-payload.spec.md`
//! - `FLOSS/docs/adr/ADR-12-consent-gate-protocol.md`
//!
//! Current enforcement:
//! - Creates and retrieves ConsentPayload / ConsentDecision entries.
//! - Links pattern-hash anchors to payloads and payloads to decisions.
//! - Enforces `scope_granted ⊆ consent_scope` on the create-decision path.
//!
//! Still pending:
//! - DID ↔ action-header binding.
//! - action-time gating for downstream governed-pattern operations.

use consent_integrity::{
    BlastRadius, ConsentDecision, ConsentPayload, ConsentScope, EntryTypes as ConsentEntryTypes,
    LinkTypes as ConsentLinkTypes, Outcome, PatternType, RefusalMode,
};
use hdk::prelude::*;

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateConsentPayloadInput {
    pub payload_id: String,
    pub pattern_id: String,
    pub pattern_type: PatternType,
    pub pattern_hash: String,
    pub proposer_did: String,
    pub recipient_did: String,
    pub blast_radius: BlastRadius,
    pub consent_scope: Vec<ConsentScope>,
    pub refusal_modes: Option<Vec<RefusalMode>>,
    pub refusable_until: Option<Timestamp>,
    pub parent_consent_id: Option<ActionHash>,
    pub rationale: Option<String>,
    pub submitted_at: Option<Timestamp>,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct CreateConsentDecisionInput {
    pub decision_id: String,
    pub payload_action_hash: ActionHash,
    pub decider_did: String,
    pub outcome: Outcome,
    pub scope_granted: Vec<ConsentScope>,
    pub rationale: Option<String>,
    pub counter_frame_ref: Option<ActionHash>,
    pub expires_at: Option<Timestamp>,
    pub decided_at: Option<Timestamp>,
}

fn default_refusal_modes() -> Vec<RefusalMode> {
    vec![
        RefusalMode::Reject,
        RefusalMode::BoundedAccept,
        RefusalMode::TouristObserve,
        RefusalMode::CounterPropose,
    ]
}

fn ensure_scope_subset(granted: &[ConsentScope], requested: &[ConsentScope]) -> ExternResult<()> {
    for scope in granted {
        if !requested.contains(scope) {
            return Err(wasm_error!(WasmErrorInner::Guest(format!(
                "E_SCOPE_NOT_REQUESTED: scope_granted contains {:?}, but the referenced ConsentPayload did not request it",
                scope
            ))));
        }
    }
    Ok(())
}

fn ensure_outcome_scope_relation(
    outcome: &Outcome,
    granted: &[ConsentScope],
    requested: &[ConsentScope],
) -> ExternResult<()> {
    let grants_every_requested_scope = requested.iter().all(|scope| granted.contains(scope));

    if matches!(outcome, Outcome::Accepted) && !grants_every_requested_scope {
        return Err(wasm_error!(WasmErrorInner::Guest(
            "E_ACCEPTED_SCOPE_INCOMPLETE: outcome=Accepted MUST grant every requested scope; \
             use BoundedAccept to grant a narrower scope"
                .into()
        )));
    }

    if matches!(outcome, Outcome::BoundedAccept) && grants_every_requested_scope {
        return Err(wasm_error!(WasmErrorInner::Guest(
            "E_BOUNDED_NOT_NARROWED: outcome=BoundedAccept MUST grant fewer scopes than \
             requested; use Accepted to grant the full requested scope"
                .into()
        )));
    }

    Ok(())
}

#[hdk_extern]
pub fn create_consent_payload(input: CreateConsentPayloadInput) -> ExternResult<ActionHash> {
    let pattern_hash = input.pattern_hash.clone();
    let payload = ConsentPayload {
        payload_id: input.payload_id,
        pattern_id: input.pattern_id,
        pattern_type: input.pattern_type,
        pattern_hash: input.pattern_hash,
        proposer_did: input.proposer_did,
        recipient_did: input.recipient_did,
        blast_radius: input.blast_radius,
        consent_scope: input.consent_scope,
        refusal_modes: input.refusal_modes.unwrap_or_else(default_refusal_modes),
        refusable_until: input.refusable_until,
        parent_consent_id: input.parent_consent_id,
        rationale: input.rationale,
        submitted_at: input.submitted_at.unwrap_or(sys_time()?),
    };
    let hash = create_entry(ConsentEntryTypes::ConsentPayload(payload))?;
    let pattern_path = Path::from(format!("consent_pattern:{pattern_hash}"));
    create_link(
        pattern_path.path_entry_hash()?,
        hash.clone(),
        ConsentLinkTypes::PatternHashToPayload,
        (),
    )?;
    Ok(hash)
}

#[hdk_extern]
pub fn get_consent_payload(hash: ActionHash) -> ExternResult<Option<ConsentPayload>> {
    match get(hash, GetOptions::default())? {
        Some(record) => record
            .entry()
            .to_app_option::<ConsentPayload>()
            .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string()))),
        None => Ok(None),
    }
}

#[hdk_extern]
pub fn create_consent_decision(input: CreateConsentDecisionInput) -> ExternResult<ActionHash> {
    let payload = get_consent_payload(input.payload_action_hash.clone())?.ok_or_else(|| {
        wasm_error!(WasmErrorInner::Guest(
            "E_CONSENT_PAYLOAD_NOT_FOUND: payload_action_hash does not resolve to ConsentPayload"
                .into()
        ))
    })?;
    // Keep coordinator preflight as defense in depth for immediate caller
    // feedback; the integrity zome independently enforces the same relation
    // against the dependency-tracked valid payload record.
    ensure_scope_subset(&input.scope_granted, &payload.consent_scope)?;
    ensure_outcome_scope_relation(&input.outcome, &input.scope_granted, &payload.consent_scope)?;

    let payload_action_hash = input.payload_action_hash.clone();
    let decision = ConsentDecision {
        decision_id: input.decision_id,
        payload_action_hash: input.payload_action_hash,
        decider_did: input.decider_did,
        outcome: input.outcome,
        scope_granted: input.scope_granted,
        rationale: input.rationale,
        counter_frame_ref: input.counter_frame_ref,
        expires_at: input.expires_at,
        decided_at: input.decided_at.unwrap_or(sys_time()?),
    };
    let hash = create_entry(ConsentEntryTypes::ConsentDecision(decision))?;
    create_link(
        payload_action_hash,
        hash.clone(),
        ConsentLinkTypes::PayloadToDecision,
        (),
    )?;
    Ok(hash)
}

#[hdk_extern]
pub fn get_consent_decision(hash: ActionHash) -> ExternResult<Option<ConsentDecision>> {
    match get(hash, GetOptions::default())? {
        Some(record) => record
            .entry()
            .to_app_option::<ConsentDecision>()
            .map_err(|e| wasm_error!(WasmErrorInner::Guest(e.to_string()))),
        None => Ok(None),
    }
}

#[hdk_extern]
pub fn get_consent_decisions_for_payload(
    payload_hash: ActionHash,
) -> ExternResult<Vec<(ActionHash, ConsentDecision)>> {
    let links = get_links(
        LinkQuery::try_new(payload_hash, ConsentLinkTypes::PayloadToDecision)?,
        GetStrategy::default(),
    )?;
    let mut decisions = Vec::new();
    for link in links {
        let Some(target_hash) = link.target.into_action_hash() else {
            continue;
        };
        if let Some(decision) = get_consent_decision(target_hash.clone())? {
            decisions.push((target_hash, decision));
        }
    }
    Ok(decisions)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn accepted_requires_every_requested_scope() {
        let requested = vec![ConsentScope::ReadOnly, ConsentScope::Bind];
        let granted = vec![ConsentScope::ReadOnly];

        let result = ensure_outcome_scope_relation(&Outcome::Accepted, &granted, &requested);

        assert!(result.is_err());
        assert!(result
            .unwrap_err()
            .to_string()
            .contains("E_ACCEPTED_SCOPE_INCOMPLETE"));
    }

    #[test]
    fn accepted_allows_the_full_requested_scope_in_any_order() {
        let requested = vec![ConsentScope::ReadOnly, ConsentScope::Bind];
        let granted = vec![ConsentScope::Bind, ConsentScope::ReadOnly];

        assert!(ensure_outcome_scope_relation(&Outcome::Accepted, &granted, &requested).is_ok());
    }
}
