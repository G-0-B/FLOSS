use amazon_rose_forest::{
    core::Metrics,
    nerv::{NervRuntime, NervConfig, ModelUpdate, ModelMetadata, ModelMetrics},
    error::ShardError,
    sharding::ShardManager,
};
use hdk::prelude::*;
use std::sync::Arc;

#[tokio::test]
async fn test_model_update_lifecycle() -> Result<(), Box<dyn std::error::Error>> {
    // Initialize metrics
    let metrics = Arc::new(Metrics::new());
    
    // Initialize ShardManager with default config
    let shard_config = amazon_rose_forest::sharding::manager::ShardConfig {
        dimensions: 2,
        max_shard_size: 1000,
        min_shard_size: 100,
        hilbert_order: 10,
        sync_timeout_ms: 5000,
        merge_interval_ms: 10000,
        merge_threshold: 0.01,
    };
    
    let shard_manager = Arc::new(ShardManager::new(shard_config, Arc::clone(&metrics)));
    
    // Initialize NERV Runtime
    let nerv_config = NervConfig::default();
    let nerv_runtime = NervRuntime::new(
        nerv_config,
        Arc::clone(&metrics),
        Arc::clone(&shard_manager)
    );
    
    // Start NERV Runtime
    nerv_runtime.start().await?;
    
    // Create a test model update
    let agent_pubkey = AgentPubKey::from_raw_39(vec![0; 39])?;
    let model_update = ModelUpdate {
        weights: vec![0.1, 0.2, 0.3, 0.4, 0.5],
        bias: 0.01,
        version: 1,
        metadata: ModelMetadata {
            timestamp: sys_time()?,
            metrics: ModelMetrics {
                loss: 0.05,
                accuracy: 0.95,
                samples_count: 1000,
            },
            agent_id: agent_pubkey,
        },
    };
    
    // Process the model update
    nerv_runtime.process_model_update(&model_update).await?;
    
    // Start a federated learning round
    nerv_runtime.start_federated_learning_round().await?;
    
    // Stop NERV Runtime
    nerv_runtime.stop().await?;
    
    Ok(())
}