// src/nerv/mod.rs
mod runtime;
mod synchrony;
mod evolution;
mod replication;
mod versioning;

pub use runtime::NervRuntime;
pub use synchrony::NeurosynchronyManager;
pub use evolution::EvolutionManager;
pub use replication::{ReplicationManager, ModelUpdate, ModelMetadata, ModelMetrics, AggregationResult};
pub use versioning::VersioningManager;