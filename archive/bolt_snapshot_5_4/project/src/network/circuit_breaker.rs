// src/network/circuit_breaker.rs
use std::sync::Arc;
use tokio::sync::RwLock;
use std::time::{Duration, Instant};

#[derive(Debug)]
pub struct CircuitBreaker {
    state: Arc<RwLock<CircuitState>>,
    config: CircuitBreakerConfig,
}

#[derive(Debug, Clone)]
pub struct CircuitBreakerConfig {
    pub failure_threshold: u32,
    pub reset_timeout: Duration,
    pub half_open_max_attempts: u32,
}

#[derive(Debug)]
enum CircuitState {
    Closed { failures: u32 },
    Open { since: Instant },
    HalfOpen { attempts: u32, successes: u32 },
}

impl CircuitBreaker {
    pub fn new() -> Self {
        Self {
            state: Arc::new(RwLock::new(CircuitState::Closed { failures: 0 })),
            config: CircuitBreakerConfig {
                failure_threshold: 5,
                reset_timeout: Duration::from_secs(60),
                half_open_max_attempts: 3,
            },
        }
    }

    pub async fn allow_operation(&self) -> Result<bool, hdk::prelude::HdkError> {
        let state = self.state.read().await;
        match *state {
            CircuitState::Closed { .. } => Ok(true),
            CircuitState::Open { since } => {
                if since.elapsed() > self.config.reset_timeout {
                    drop(state);
                    self.half_open().await?;
                    Ok(true)
                } else {
                    Ok(false)
                }
            }
            CircuitState::HalfOpen { attempts, .. } => {
                Ok(attempts < self.config.half_open_max_attempts)
            }
        }
    }

    async fn half_open(&self) -> Result<(), hdk::prelude::HdkError> {
        let mut state = self.state.write().await;
        *state = CircuitState::HalfOpen { attempts: 0, successes: 0 };
        Ok(())
    }
    
    pub async fn record_success(&self) -> Result<(), hdk::prelude::HdkError> {
        let mut state = self.state.write().await;
        match *state {
            CircuitState::Closed { .. } => {
                // Already closed, nothing to do
            },
            CircuitState::HalfOpen { attempts, successes } => {
                if successes + 1 >= self.config.half_open_max_attempts {
                    // Enough successes, close the circuit
                    *state = CircuitState::Closed { failures: 0 };
                } else {
                    // Still in half-open state
                    *state = CircuitState::HalfOpen {
                        attempts,
                        successes: successes + 1,
                    };
                }
            },
            CircuitState::Open { .. } => {
                // Shouldn't be recording success if open, but just in case
                *state = CircuitState::HalfOpen { attempts: 1, successes: 1 };
            }
        }
        Ok(())
    }
    
    pub async fn record_failure(&self) -> Result<(), hdk::prelude::HdkError> {
        let mut state = self.state.write().await;
        match *state {
            CircuitState::Closed { failures } => {
                if failures + 1 >= self.config.failure_threshold {
                    // Too many failures, open the circuit
                    *state = CircuitState::Open { since: Instant::now() };
                } else {
                    // Still in closed state, increment failures
                    *state = CircuitState::Closed { failures: failures + 1 };
                }
            },
            CircuitState::HalfOpen { .. } => {
                // Any failure in half-open state opens the circuit again
                *state = CircuitState::Open { since: Instant::now() };
            },
            CircuitState::Open { since } => {
                // Already open, update the timestamp
                *state = CircuitState::Open { since: Instant::now() };
            }
        }
        Ok(())
    }
    
    pub async fn reset(&self) -> Result<(), hdk::prelude::HdkError> {
        let mut state = self.state.write().await;
        *state = CircuitState::Closed { failures: 0 };
        Ok(())
    }
}