use holochain::prelude::ActionHash;
use rose_forest_sweettest::{
    await_two_agent_consistency, consent_zome, setup_two_agent_app, BlastRadius, ConsentDecision,
    ConsentPayload, ConsentScope, CreateConsentDecisionInput, CreateConsentPayloadInput, Outcome,
    PatternType,
};

fn payload_input(payload_id: &str, scopes: Vec<ConsentScope>) -> CreateConsentPayloadInput {
    CreateConsentPayloadInput {
        payload_id: payload_id.into(),
        pattern_id: "ADR-12".into(),
        pattern_type: PatternType::Adr,
        pattern_hash: "a".repeat(64),
        proposer_did: "did:floss:alice".into(),
        recipient_did: "did:floss:bob".into(),
        blast_radius: BlastRadius::System,
        consent_scope: scopes,
        refusal_modes: None,
        refusable_until: None,
        parent_consent_id: None,
        rationale: Some("Sweettest consent coverage".into()),
        submitted_at: None,
    }
}

fn accepted_decision_input(
    decision_id: &str,
    payload_action_hash: ActionHash,
    scopes: Vec<ConsentScope>,
) -> CreateConsentDecisionInput {
    CreateConsentDecisionInput {
        decision_id: decision_id.into(),
        payload_action_hash,
        decider_did: "did:floss:bob".into(),
        outcome: Outcome::Accepted,
        scope_granted: scopes,
        rationale: None,
        counter_frame_ref: None,
        expires_at: None,
        decided_at: None,
    }
}

#[tokio::test(flavor = "multi_thread")]
async fn consent_payload_and_accepted_decision_are_cross_agent_visible() {
    let app = setup_two_agent_app().await;
    let alice_zome = consent_zome(&app.alice);
    let bob_zome = consent_zome(&app.bob);
    let requested = vec![ConsentScope::ReadOnly, ConsentScope::Integrate];
    let payload_hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "create_consent_payload",
            payload_input("018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0301", requested.clone()),
        )
        .await;

    let alice_payload: Option<ConsentPayload> = app.conductors[0]
        .call(&alice_zome, "get_consent_payload", payload_hash.clone())
        .await;
    let alice_payload = alice_payload.expect("Alice must retrieve her payload");
    assert_eq!(alice_payload.pattern_type, PatternType::Adr);
    assert_eq!(alice_payload.consent_scope, requested);

    await_two_agent_consistency(&app).await;

    let bob_payload: Option<ConsentPayload> = app.conductors[1]
        .call(&bob_zome, "get_consent_payload", payload_hash.clone())
        .await;
    assert_eq!(bob_payload, Some(alice_payload));

    let decision_hash: ActionHash = app.conductors[1]
        .call(
            &bob_zome,
            "create_consent_decision",
            accepted_decision_input(
                "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0302",
                payload_hash.clone(),
                requested.clone(),
            ),
        )
        .await;

    await_two_agent_consistency(&app).await;

    let alice_decision: Option<ConsentDecision> = app.conductors[0]
        .call(&alice_zome, "get_consent_decision", decision_hash.clone())
        .await;
    let alice_decision = alice_decision.expect("Alice must retrieve Bob's decision");
    assert_eq!(alice_decision.payload_action_hash, payload_hash.clone());
    assert_eq!(alice_decision.decider_did, "did:floss:bob");
    assert_eq!(alice_decision.outcome, Outcome::Accepted);
    assert_eq!(alice_decision.scope_granted, requested);

    let decisions: Vec<(ActionHash, ConsentDecision)> = app.conductors[0]
        .call(
            &alice_zome,
            "get_consent_decisions_for_payload",
            payload_hash,
        )
        .await;
    let (linked_hash, linked_decision) = decisions
        .iter()
        .find(|(hash, _)| hash == &decision_hash)
        .expect("payload decision links must contain Bob's action hash");
    assert_eq!(linked_hash, &decision_hash);
    assert_eq!(linked_decision, &alice_decision);
}

#[tokio::test(flavor = "multi_thread")]
async fn consent_rejects_unrequested_scope_without_creating_a_decision() {
    let app = setup_two_agent_app().await;
    let alice_zome = consent_zome(&app.alice);
    let bob_zome = consent_zome(&app.bob);
    let payload_hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "create_consent_payload",
            payload_input(
                "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0303",
                vec![ConsentScope::ReadOnly],
            ),
        )
        .await;

    await_two_agent_consistency(&app).await;

    let error = app.conductors[1]
        .call_fallible::<_, ActionHash>(
            &bob_zome,
            "create_consent_decision",
            accepted_decision_input(
                "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0304",
                payload_hash.clone(),
                vec![ConsentScope::ReadOnly, ConsentScope::Bind],
            ),
        )
        .await
        .expect_err("scope not requested by the payload must fail closed");
    assert!(
        error.to_string().contains("E_SCOPE_NOT_REQUESTED"),
        "expected E_SCOPE_NOT_REQUESTED, got: {error}"
    );

    await_two_agent_consistency(&app).await;

    let decisions: Vec<(ActionHash, ConsentDecision)> = app.conductors[0]
        .call(
            &alice_zome,
            "get_consent_decisions_for_payload",
            payload_hash,
        )
        .await;
    assert!(
        decisions.is_empty(),
        "rejected call must not create a decision link"
    );
}
