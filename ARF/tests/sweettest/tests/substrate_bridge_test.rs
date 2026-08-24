use holochain::prelude::{ActionHash, AgentPubKey, Record, Timestamp};
use rose_forest_sweettest::{
    await_two_agent_consistency, mutated_missing_hash, rose_zome, setup_two_agent_app,
    AssertTripleInput, KnowledgeTriple, QueryTriplesInput, TripleResult,
};
use std::collections::{BTreeMap, BTreeSet};
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

#[tokio::test(flavor = "multi_thread")]
async fn criterion_1_publish_returns_resolvable_action_hash() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new("holochain", "is_a", "distributed_framework", 0.95),
        )
        .await;
    let record: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", hash.clone())
        .await;
    let record = record.expect("published triple must resolve by returned action hash");
    let triple = record
        .entry()
        .to_app_option::<KnowledgeTriple>()
        .expect("published entry must decode")
        .expect("published entry must be present");

    assert_eq!(record.action_address(), &hash);
    assert_eq!(triple.subject, "holochain");
    assert_eq!(triple.predicate, "is_a");
    assert_eq!(triple.object, "distributed_framework");
    assert!((triple.confidence - 0.95).abs() < f32::EPSILON);
}

#[tokio::test(flavor = "multi_thread")]
async fn criterion_2_provenance_returns_author_timestamp_and_signature() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let before = now_timestamp();
    let hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new("rose", "has_property", "provenance", 0.91),
        )
        .await;
    let after = now_timestamp();
    let record: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", hash)
        .await;
    let record = record.expect("published triple must retain a record");
    let triple = record
        .entry()
        .to_app_option::<KnowledgeTriple>()
        .expect("published entry must decode")
        .expect("published entry must be present");

    assert!(record.action().timestamp() >= before);
    assert!(record.action().timestamp() <= after);
    assert_eq!(record.action().author(), app.alice.agent_pubkey());
    assert_eq!(record.signed_action().signature.0.len(), 64);
    assert_eq!(triple.subject, "rose");
    assert_eq!(triple.predicate, "has_property");
    assert_eq!(triple.object, "provenance");
    assert!((triple.confidence - 0.91).abs() < f32::EPSILON);
    assert_eq!(triple.source, *app.alice.agent_pubkey());
}

#[tokio::test(flavor = "multi_thread")]
async fn criterion_3_bob_verifies_alices_content_and_provenance() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let bob_zome = rose_zome(&app.bob);
    let hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new("alice", "relates_to", "interoperable_truth", 0.97),
        )
        .await;
    let alice_record: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", hash.clone())
        .await;
    let alice_record = alice_record.expect("Alice must resolve her assertion");

    await_two_agent_consistency(&app).await;

    let bob_record: Option<Record> = app.conductors[1]
        .call(&bob_zome, "get_triple_record", hash)
        .await;
    let bob_record = bob_record.expect("Bob must independently resolve Alice's assertion");
    let alice_triple = alice_record
        .entry()
        .to_app_option::<KnowledgeTriple>()
        .expect("Alice entry must decode")
        .expect("Alice entry must be present");
    let bob_triple = bob_record
        .entry()
        .to_app_option::<KnowledgeTriple>()
        .expect("Bob entry must decode")
        .expect("Bob entry must be present");

    assert_eq!(bob_record.action_address(), alice_record.action_address());
    assert_eq!(bob_record.action().author(), alice_record.action().author());
    assert_eq!(
        bob_record.action().timestamp(),
        alice_record.action().timestamp()
    );
    assert_eq!(
        bob_record.signed_action().signature,
        alice_record.signed_action().signature
    );
    assert_eq!(bob_triple, alice_triple);
}

#[tokio::test(flavor = "multi_thread")]
async fn criterion_3b_missing_hash_returns_none() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new("absence", "related_to", "presence", 0.9),
        )
        .await;
    let missing_hash = mutated_missing_hash(&hash);
    let real: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", hash)
        .await;
    let missing: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", missing_hash)
        .await;

    assert!(real.is_some(), "the unmodified hash must still resolve");
    assert!(missing.is_none(), "a mutated action hash must not resolve");
}

#[tokio::test(flavor = "multi_thread")]
async fn criterion_4_bob_discovers_by_subject_and_predicate_without_hash() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let bob_zome = rose_zome(&app.bob);
    let hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new("holochain", "supports", "agent_centric_apps", 0.94),
        )
        .await;
    let published_record: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", hash.clone())
        .await;
    let published_record = published_record.expect("Alice must resolve the published triple");
    let published_triple = published_record
        .entry()
        .to_app_option::<KnowledgeTriple>()
        .expect("published entry must decode")
        .expect("published entry must be present");

    await_two_agent_consistency(&app).await;

    let by_subject: Vec<TripleResult> = app.conductors[1]
        .call(
            &bob_zome,
            "query_triples",
            QueryTriplesInput::subject("holochain"),
        )
        .await;
    let by_predicate: Vec<TripleResult> = app.conductors[1]
        .call(
            &bob_zome,
            "query_triples",
            QueryTriplesInput::predicate("supports"),
        )
        .await;

    let subject_result = by_subject
        .iter()
        .find(|result| result.hash == hash)
        .expect("Bob's subject query must contain Alice's returned action hash");
    let predicate_result = by_predicate
        .iter()
        .find(|result| result.hash == hash)
        .expect("Bob's predicate query must contain Alice's returned action hash");
    for result in [subject_result, predicate_result] {
        assert_eq!(result.hash, hash);
        assert_eq!(result.subject, published_triple.subject);
        assert_eq!(result.predicate, published_triple.predicate);
        assert_eq!(result.object, published_triple.object);
        assert!((result.confidence - published_triple.confidence).abs() < f32::EPSILON);
        assert_eq!(result.author, *app.alice.agent_pubkey());
        assert_eq!(result.author, published_triple.source);
        assert_eq!(result.created_at, published_triple.created_at);
    }
}

#[tokio::test(flavor = "multi_thread")]
async fn criterion_5_conflicting_triples_remain_fork_visible() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let bob_zome = rose_zome(&app.bob);
    let alice_hash: ActionHash = app.conductors[0]
        .call(
            &alice_zome,
            "assert_triple",
            AssertTripleInput::new("claim", "contradicts", "affirmed", 0.7),
        )
        .await;
    let bob_hash: ActionHash = app.conductors[1]
        .call(
            &bob_zome,
            "assert_triple",
            AssertTripleInput::new("claim", "contradicts", "disputed", 0.7),
        )
        .await;

    await_two_agent_consistency(&app).await;

    let results: Vec<TripleResult> = app.conductors[0]
        .call(
            &alice_zome,
            "query_triples",
            QueryTriplesInput::subject("claim"),
        )
        .await;
    let visible: BTreeMap<String, AgentPubKey> = results
        .into_iter()
        .filter(|result| {
            result.subject == "claim"
                && result.predicate == "contradicts"
                && (result.object == "affirmed" || result.object == "disputed")
        })
        .map(|result| (result.object, result.author))
        .collect();

    assert_ne!(alice_hash, bob_hash);
    assert_eq!(visible.len(), 2);
    assert_eq!(visible.get("affirmed"), Some(app.alice.agent_pubkey()));
    assert_eq!(visible.get("disputed"), Some(app.bob.agent_pubkey()));
}

#[tokio::test(flavor = "multi_thread")]
async fn criterion_6_distinct_agents_have_equal_publish_query_and_verify_access() {
    let app = setup_two_agent_app().await;
    let alice_zome = rose_zome(&app.alice);
    let bob_zome = rose_zome(&app.bob);
    let input = AssertTripleInput::new("alice", "related_to", "bob", 0.88);
    let alice_hash: ActionHash = app.conductors[0]
        .call(&alice_zome, "assert_triple", input.clone())
        .await;
    let bob_hash: ActionHash = app.conductors[1]
        .call(&bob_zome, "assert_triple", input)
        .await;

    await_two_agent_consistency(&app).await;

    let alice_results: Vec<TripleResult> = app.conductors[0]
        .call(
            &alice_zome,
            "query_triples",
            QueryTriplesInput::predicate("related_to"),
        )
        .await;
    let bob_results: Vec<TripleResult> = app.conductors[1]
        .call(
            &bob_zome,
            "query_triples",
            QueryTriplesInput::predicate("related_to"),
        )
        .await;
    let alice_set: BTreeSet<ActionHash> = alice_results
        .into_iter()
        .map(|result| result.hash)
        .collect();
    let bob_set: BTreeSet<ActionHash> = bob_results.into_iter().map(|result| result.hash).collect();
    let expected: BTreeSet<ActionHash> =
        [alice_hash.clone(), bob_hash.clone()].into_iter().collect();
    let alice_from_bob: Option<Record> = app.conductors[1]
        .call(&bob_zome, "get_triple_record", alice_hash)
        .await;
    let bob_from_alice: Option<Record> = app.conductors[0]
        .call(&alice_zome, "get_triple_record", bob_hash)
        .await;

    assert_ne!(app.alice.agent_pubkey(), app.bob.agent_pubkey());
    assert_eq!(alice_set, expected);
    assert_eq!(bob_set, expected);
    assert!(alice_from_bob.is_some());
    assert!(bob_from_alice.is_some());
}
