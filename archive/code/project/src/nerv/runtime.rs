// src/nerv/runtime.rs
use crate::core::{Metrics, CentroidCRDT};
use crate::sharding::ShardManager;
use crate::error::ShardError;
use crate::network::CircuitBreaker;
use super::synchrony::NeurosynchronyManager;
use super::evolution::EvolutionManager;
use super::replication::{ReplicationManager, ModelUpdate};
use super::versioning::VersioningManager;
use std::sync::Arc;
use std::time::Duration;

pub struct NervConfig {
    pub sync_interval_ms: u64,
    pub evolution_interval_ms: u64,
    pub replication_interval_ms: u64,
    pub versioning_interval_ms: u64,
    pub max_drift_tolerance_ms: u64,
    pub merge_threshold: f32,
    pub max_participants_per_round: u32,
}

impl Default for NervConfig {
    fn default() -> Self {
        Self {
            sync_interval_ms: 500,        // 500ms for neurosynchrony
            evolution_interval_ms: 5000,   // 5 seconds for evolution (CRDT merges)
            replication_interval_ms: 3600000, // 1 hour for federated learning rounds
            versioning_interval_ms: 10000, // 10 seconds for version updates
            max_drift_tolerance_ms: 500,   // 500ms max drift tolerance
            merge_threshold: 0.01,         // 0.01 Euclidean distance for merge threshold
            max_participants_per_round: 100, // Max 100 participants per federated round
        }
    }
}

pub struct NervRuntime {
    config: NervConfig,
    metrics: Arc<Metrics>,
    circuit_breaker: CircuitBreaker,
    neurosynchrony: NeurosynchronyManager,
    evolution: EvolutionManager,
    replication: ReplicationManager,
    versioning: VersioningManager,
    shard_manager: Arc<ShardManager>,
}

impl NervRuntime {
    pub fn new(
        config: NervConfig, 
        metrics: Arc<Metrics>,
        shard_manager: Arc<ShardManager>
    ) -> Self {
        let circuit_breaker = CircuitBreaker::new();
        
        let neurosynchrony = NeurosynchronyManager::new(
            config.sync_interval_ms,
            config.max_drift_tolerance_ms,
            Arc::clone(&metrics)
        );
        
        let evolution = EvolutionManager::new(
            config.evolution_interval_ms,
            config.merge_threshold,
            Arc::clone(&metrics)
        );
        
        let replication = ReplicationManager::new(
            config.replication_interval_ms,
            config.max_participants_per_round,
            Arc::clone(&metrics)
        );
        
        let versioning = VersioningManager::new(
            config.versioning_interval_ms,
            Arc::clone(&metrics)
        );
        
        Self {
            config,
            metrics,
            circuit_breaker,
            neurosynchrony,
            evolution,
            replication,
            versioning,
            shard_manager,
        }
    }
    
    pub async fn start(&self) -> Result<(), ShardError> {
        // Start all NERV components
        self.metrics.record("nerv_runtime_start", 1);
        
        // Start neurosynchrony manager
        self.neurosynchrony.start().await?;
        
        // Start evolution manager
        self.evolution.start().await?;
        
        // Start replication manager
        self.replication.start().await?;
        
        // Start versioning manager
        self.versioning.start().await?;
        
        Ok(())
    }
    
    pub async fn stop(&self) -> Result<(), ShardError> {
        // Stop all NERV components
        self.metrics.record("nerv_runtime_stop", 1);
        
        // Stop neurosynchrony manager
        self.neurosynchrony.stop().await?;
        
        // Stop evolution manager
        self.evolution.stop().await?;
        
        // Stop replication manager
        self.replication.stop().await?;
        
        // Stop versioning manager
        self.versioning.stop().await?;
        
        Ok(())
    }
    
    pub async fn process_centroid_update(&self, centroid: &CentroidCRDT) -> Result<(), ShardError> {
        if !self.circuit_breaker.allow_operation().await? {
            return Err(ShardError::CircuitBreakerOpen);
        }
        
        // Process through the NERV pipeline
        self.metrics.start_operation("centroid_update_processing");
        
        // 1. Neurosynchrony: Broadcast the update to other nodes
        self.neurosynchrony.broadcast_update(centroid).await?;
        
        // 2. Evolution: Update local centroids
        self.evolution.process_centroid_update(centroid).await?;
        
        // 3. Versioning: Record the update in the version history
        self.versioning.record_update(centroid).await?;
        
        self.metrics.end_operation("centroid_update_processing");
        
        Ok(())
    }
    
    pub async fn process_model_update(&self, model_update: &ModelUpdate) -> Result<(), ShardError> {
        if !self.circuit_breaker.allow_operation().await? {
            return Err(ShardError::CircuitBreakerOpen);
        }
        
        // Process the model update through the replication manager
        self.metrics.start_operation("model_update_processing");
        
        // Submit the model update to the replication manager
        self.replication.receive_model_update(model_update.clone()).await?;
        
        self.metrics.end_operation("model_update_processing");
        
        Ok(())
    }
    
    pub async fn sync_state(&self) -> Result<(), ShardError> {
        if !self.circuit_breaker.allow_operation().await? {
            return Err(ShardError::CircuitBreakerOpen);
        }
        
        self.metrics.start_operation("nerv_sync_state");
        
        // Synchronize state across all NERV components
        self.neurosynchrony.sync_state().await?;
        self.evolution.sync_state().await?;
        self.replication.sync_state().await?;
        self.versioning.sync_state().await?;
        
        // Sync shards through the shard manager
        self.shard_manager.sync_shards().await?;
        
        self.metrics.end_operation("nerv_sync_state");
        
        Ok(())
    }
    
    pub async fn handle_drift_detected(&self, drift_ms: u64) -> Result<(), ShardError> {
        self.metrics.record("neurosynchrony_drift_detected", drift_ms);
        
        if drift_ms > self.config.max_drift_tolerance_ms {
            // Trigger immediate reconciliation
            self.sync_state().await?;
        }
        
        Ok(())
    }
    
    pub async fn start_federated_learning_round(&self) -> Result<(), ShardError> {
        if !self.circuit_breaker.allow_operation().await? {
            return Err(ShardError::CircuitBreakerOpen);
        }
        
        self.metrics.start_operation("federated_learning_round");
        
        // Start a federated learning round through the replication manager
        self.replication.start_federated_round().await?;
        
        self.metrics.end_operation("federated_learning_round");
        
        Ok(())
    }
}