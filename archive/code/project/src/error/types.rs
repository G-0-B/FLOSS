use thiserror::Error;
use std::time::Duration;

#[derive(Debug, Error)]
pub enum ShardError {
    #[error("Shard migration failed: {context}")]
    MigrationFailed {
        context: String,
        #[source]
        source: Box<dyn std::error::Error + Send + Sync>,
    },

    #[error("Circuit breaker is open")]
    CircuitBreakerOpen,

    #[error("Operation timed out after {duration:?}")]
    Timeout {
        duration: Duration,
        operation: String,
    },

    #[error("Holochain error: {0}")]
    Holochain(#[from] hdk::prelude::HdkError),
}