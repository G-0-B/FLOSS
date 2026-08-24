use holochain::prelude::{ActionHash, Record};
use rose_forest_sweettest::{rose_zome, setup_two_agent_app, AssertTripleInput, KnowledgeTriple};

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
