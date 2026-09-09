use holochain::prelude::{ActionHash, Timestamp};
use rose_forest_sweettest::{
    await_two_agent_consistency, consent_zome, setup_two_agent_app, BlastRadius, ConsentDecision,
    ConsentPayload, ConsentScope, CreateConsentDecisionInput, CreateConsentPayloadInput, Outcome,
    PatternType, RefusalMode,
};
use std::time::{SystemTime, UNIX_EPOCH};

fn now_timestamp() -> Timestamp {
    let micros = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock must be after the Unix epoch")
        .as_micros()
        .try_into()
        .expect("current time must fit in Holochain's microsecond timestamp");
    Timestamp::from_micros(micros)
}

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
    let payload_input = payload_input("018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0301", requested.clone());
    let payload_before = now_timestamp();
    let payload_hash: ActionHash = app.conductors[0]
        .call(&alice_zome, "create_consent_payload", payload_input)
        .await;
    let payload_after = now_timestamp();

    let alice_payload: Option<ConsentPayload> = app.conductors[0]
        .call(&alice_zome, "get_consent_payload", payload_hash.clone())
        .await;
    let alice_payload = alice_payload.expect("Alice must retrieve her payload");
    assert_eq!(
        alice_payload.payload_id,
        "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0301"
    );
    assert_eq!(alice_payload.pattern_id, "ADR-12");
    assert_eq!(alice_payload.pattern_type, PatternType::Adr);
    assert_eq!(alice_payload.pattern_hash, "a".repeat(64));
    assert_eq!(alice_payload.proposer_did, "did:floss:alice");
    assert_eq!(alice_payload.recipient_did, "did:floss:bob");
    assert_eq!(alice_payload.blast_radius, BlastRadius::System);
    assert_eq!(alice_payload.consent_scope, requested);
    assert_eq!(
        alice_payload.refusal_modes,
        vec![
            RefusalMode::Reject,
            RefusalMode::BoundedAccept,
            RefusalMode::TouristObserve,
            RefusalMode::CounterPropose,
        ]
    );
    assert_eq!(alice_payload.refusable_until, None);
    assert_eq!(alice_payload.parent_consent_id, None);
    assert_eq!(
        alice_payload.rationale.as_deref(),
        Some("Sweettest consent coverage")
    );
    assert!(alice_payload.submitted_at >= payload_before);
    assert!(alice_payload.submitted_at <= payload_after);

    await_two_agent_consistency(&app).await;

    let bob_payload: Option<ConsentPayload> = app.conductors[1]
        .call(&bob_zome, "get_consent_payload", payload_hash.clone())
        .await;
    assert_eq!(bob_payload, Some(alice_payload));

    let decision_input = accepted_decision_input(
        "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0302",
        payload_hash.clone(),
        requested.clone(),
    );
    let decision_before = now_timestamp();
    let decision_hash: ActionHash = app.conductors[1]
        .call(&bob_zome, "create_consent_decision", decision_input)
        .await;
    let decision_after = now_timestamp();

    await_two_agent_consistency(&app).await;

    let alice_decision: Option<ConsentDecision> = app.conductors[0]
        .call(&alice_zome, "get_consent_decision", decision_hash.clone())
        .await;
    let alice_decision = alice_decision.expect("Alice must retrieve Bob's decision");
    assert_eq!(
        alice_decision.decision_id,
        "018f6d7a-7f2c-7aa1-a2b1-7b3a3f0e0302"
    );
    assert_eq!(alice_decision.payload_action_hash, payload_hash.clone());
    assert_eq!(alice_decision.decider_did, "did:floss:bob");
    assert_eq!(alice_decision.outcome, Outcome::Accepted);
    assert_eq!(alice_decision.scope_granted, requested);
    assert_eq!(alice_decision.rationale, None);
    assert_eq!(alice_decision.counter_frame_ref, None);
    assert_eq!(alice_decision.expires_at, None);
    assert!(alice_decision.decided_at >= decision_before);
    assert!(alice_decision.decided_at <= decision_after);

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

    let decisions_before: Vec<(ActionHash, ConsentDecision)> = app.conductors[1]
        .call(
            &bob_zome,
            "get_consent_decisions_for_payload",
            payload_hash.clone(),
        )
        .await;
    assert!(
        decisions_before.is_empty(),
        "new payload must have no decision links before the rejected call"
    );

    let app_entries_before = app.conductors[1]
        .raw_handle()
        .dump_full_cell_state(app.bob.cell_id(), None)
        .await
        .expect("Bob's authored source chain must be inspectable before the rejection")
        .source_chain_dump
        .records
        .iter()
        .filter(|record| record.entry.is_some())
        .count();

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

    // Links are secondary indexes. Also inspect Bob's authored source chain so
    // a coordinator bug cannot hide an orphan ConsentDecision behind a missing
    // link. A rejected call must add no app-entry action at all.
    let after_dump = app.conductors[1]
        .raw_handle()
        .dump_full_cell_state(app.bob.cell_id(), None)
        .await
        .expect("Bob's authored source chain must be inspectable after the rejection");
    let app_entries_after = after_dump
        .source_chain_dump
        .records
        .iter()
        .filter(|record| record.entry.is_some())
        .count();
    assert_eq!(
        app_entries_after, app_entries_before,
        "rejected call must not author an orphan ConsentDecision entry"
    );
}
