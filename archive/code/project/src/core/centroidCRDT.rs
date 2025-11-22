// src/core/centroid_crdt.rs
use std::collections::HashMap;
use serde::{Serialize, Deserialize};
use hdk::prelude::*;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VersionVector {
    versions: HashMap<AgentPubKey, u64>,
}

impl VersionVector {
    pub fn new() -> Self {
        Self {
            versions: HashMap::new(),
        }
    }

    pub fn increment(&mut self, agent: AgentPubKey) {
        let count = self.versions.entry(agent).or_insert(0);
        *count += 1;
    }

    pub fn merge(&mut self, other: &VersionVector) {
        for (agent, &version) in other.versions.iter() {
            let current = self.versions.entry(agent.clone()).or_insert(0);
            if version > *current {
                *current = version;
            }
        }
    }

    pub fn dominates(&self, other: &VersionVector) -> bool {
        for (agent, &version) in other.versions.iter() {
            match self.versions.get(agent) {
                Some(&my_version) if my_version < version => return false,
                None => return false,
                _ => {}
            }
        }
        true
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CentroidCRDT {
    pub centroid: Vec<f32>,
    pub count: u64,
    pub version_vector: VersionVector,
    pub timestamp: u64,
}

impl CentroidCRDT {
    pub fn new(centroid: Vec<f32>) -> Self {
        Self {
            centroid,
            count: 1,
            version_vector: VersionVector::new(),
            timestamp: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .expect("Time went backwards")
                .as_millis() as u64,
        }
    }

    pub fn merge(&mut self, other: &CentroidCRDT) -> bool {
        if self.version_vector.dominates(&other.version_vector) {
            return false; // No merge needed, we're dominant
        }
        
        if other.version_vector.dominates(&self.version_vector) {
            // Other dominates us, replace our state
            self.centroid = other.centroid.clone();
            self.count = other.count;
            self.version_vector = other.version_vector.clone();
            self.timestamp = other.timestamp;
            return true;
        }
        
        // Concurrent updates, perform weighted merge
        let total_count = self.count + other.count;
        let self_weight = self.count as f32 / total_count as f32;
        let other_weight = other.count as f32 / total_count as f32;
        
        for (i, val) in self.centroid.iter_mut().enumerate() {
            if i < other.centroid.len() {
                *val = *val * self_weight + other.centroid[i] * other_weight;
            }
        }
        
        self.count = total_count;
        self.version_vector.merge(&other.version_vector);
        self.timestamp = std::cmp::max(self.timestamp, other.timestamp);
        
        true
    }
    
    pub fn calculate_displacement(&self, other: &CentroidCRDT) -> f32 {
        let mut sum_squared = 0.0;
        
        for (i, val) in self.centroid.iter().enumerate() {
            if i < other.centroid.len() {
                let diff = val - other.centroid[i];
                sum_squared += diff * diff;
            }
        }
        
        sum_squared.sqrt()
    }
    
    pub fn update(&mut self, agent: AgentPubKey, vector: &[f32]) {
        let new_count = self.count + 1;
        let weight = 1.0 / new_count as f32;
        let old_weight = (new_count - 1) as f32 / new_count as f32;
        
        for (i, c) in self.centroid.iter_mut().enumerate() {
            if i < vector.len() {
                *c = *c * old_weight + vector[i] * weight;
            }
        }
        
        self.count = new_count;
        self.version_vector.increment(agent);
        self.timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("Time went backwards")
            .as_millis() as u64;
    }
}
