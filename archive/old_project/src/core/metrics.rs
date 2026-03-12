// src/core/metrics.rs
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct Metrics {
    metrics: Arc<Mutex<HashMap<String, Vec<u64>>>>,
    timestamps: Arc<Mutex<HashMap<String, Instant>>>,
    thresholds: Arc<Mutex<HashMap<String, u64>>>,
}

#[derive(Debug, Clone)]
pub enum ThresholdAction {
    TriggerResync,
    ImmediateReconciliation,
    AlertOperators,
    ReduceParticipantSet,
}

impl Metrics {
    pub fn new() -> Self {
        let mut thresholds = HashMap::new();
        // Define default thresholds
        thresholds.insert("neurosynchrony_latency".to_string(), 500); // ms
        thresholds.insert("crdt_merge_divergence".to_string(), 10); // 0.01 as integer (x1000)
        thresholds.insert("node_availability".to_string(), 95); // percentage
        thresholds.insert("federated_aggregation_latency".to_string(), 600000); // 10 minutes in ms

        Self {
            metrics: Arc::new(Mutex::new(HashMap::new())),
            timestamps: Arc::new(Mutex::new(HashMap::new())),
            thresholds: Arc::new(Mutex::new(thresholds)),
        }
    }

    pub fn record(&self, key: &str, value: u64) {
        let mut metrics = self.metrics.lock().unwrap();
        metrics.entry(key.to_string())
            .or_insert_with(Vec::new)
            .push(value);
        
        // Check if threshold is exceeded
        if let Some(threshold) = self.get_threshold(key) {
            if value > threshold {
                self.handle_threshold_exceeded(key, value);
            }
        }
    }

    pub fn start_operation(&self, key: &str) {
        let mut timestamps = self.timestamps.lock().unwrap();
        timestamps.insert(key.to_string(), Instant::now());
    }

    pub fn end_operation(&self, key: &str) {
        let timestamps = self.timestamps.lock().unwrap();
        if let Some(start) = timestamps.get(key) {
            let duration = start.elapsed().as_millis() as u64;
            self.record(key, duration);
        }
    }
    
    pub fn set_threshold(&self, key: &str, value: u64) {
        let mut thresholds = self.thresholds.lock().unwrap();
        thresholds.insert(key.to_string(), value);
    }
    
    pub fn get_threshold(&self, key: &str) -> Option<u64> {
        let thresholds = self.thresholds.lock().unwrap();
        thresholds.get(key).cloned()
    }
    
    pub fn handle_threshold_exceeded(&self, key: &str, value: u64) {
        let action = match key {
            "neurosynchrony_latency" => ThresholdAction::TriggerResync,
            "crdt_merge_divergence" => ThresholdAction::ImmediateReconciliation,
            "node_availability" => ThresholdAction::AlertOperators,
            "federated_aggregation_latency" => ThresholdAction::ReduceParticipantSet,
            _ => return, // No action for unknown metrics
        };
        
        // Handle the action (placeholder implementation)
        match action {
            ThresholdAction::TriggerResync => {
                // Trigger re-sync logic would go here
                eprintln!("Neurosynchrony latency exceeded threshold: {}ms. Triggering re-sync.", value);
            }
            ThresholdAction::ImmediateReconciliation => {
                // Immediate reconciliation logic would go here
                eprintln!("CRDT merge divergence exceeded threshold: {}. Initiating immediate reconciliation.", value);
            }
            ThresholdAction::AlertOperators => {
                // Alert logic would go here
                eprintln!("Node availability below threshold: {}%. Alerting operators.", value);
            }
            ThresholdAction::ReduceParticipantSet => {
                // Reduce participant set logic would go here
                eprintln!("Federated aggregation latency exceeded threshold: {}ms. Reducing participant set.", value);
            }
        }
    }
    
    pub fn get_average(&self, key: &str) -> Option<f64> {
        let metrics = self.metrics.lock().unwrap();
        if let Some(values) = metrics.get(key) {
            if !values.is_empty() {
                let sum: u64 = values.iter().sum();
                return Some(sum as f64 / values.len() as f64);
            }
        }
        None
    }
}
