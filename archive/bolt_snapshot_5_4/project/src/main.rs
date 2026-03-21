use std::sync::Arc;
use std::time::Duration;

use amazon_rose_forest::{
    core::Metrics,
    sharding::{ShardManager, HilbertCurve},
    nerv::{NervRuntime, NervConfig},
};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting Amazon Rose Forest with NERV Runtime...");
    
    // Initialize metrics
    let metrics = Arc::new(Metrics::new());
    
    // Initialize ShardManager
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
    nerv_runtime.start().await.unwrap();
    
    println!("NERV Runtime started successfully!");
    
    // Keep the application running
    loop {
        tokio::time::sleep(Duration::from_secs(1)).await;
        
        // Periodically sync state
        if let Err(e) = nerv_runtime.sync_state().await {
            eprintln!("Error syncing state: {:?}", e);
        }
    }
    
    // This code is unreachable, but included for completeness
    // nerv_runtime.stop().await.unwrap();
    // println!("NERV Runtime stopped successfully!");
    
    Ok(())
}