// src/core/vector.rs
use serde::{Serialize, Deserialize};
use hdk::prelude::*;

#[hdk_entry(id = "vector")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Vector {
    pub id: String,
    pub data: Vec<f32>,
    pub metadata: VectorMetadata,
    pub timestamp: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VectorMetadata {
    pub dimension: usize,
    pub cluster_id: Option<String>,
    pub owner: AgentPubKey,
}

impl Vector {
    pub fn new(data: Vec<f32>, owner: AgentPubKey) -> Self {
        Self {
            id: nanoid::nanoid!(),
            data,
            metadata: VectorMetadata {
                dimension: data.len(),
                cluster_id: None,
                owner,
            },
            timestamp: sys_time().expect("Could not get system time"),
        }
    }

    pub fn distance(&self, other: &Vector) -> f32 {
        self.data.iter()
            .zip(other.data.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f32>()
            .sqrt()
    }
    
    pub fn cosine_similarity(&self, other: &Vector) -> f32 {
        let dot_product: f32 = self.data.iter()
            .zip(other.data.iter())
            .map(|(a, b)| a * b)
            .sum();
            
        let self_magnitude: f32 = self.data.iter()
            .map(|a| a.powi(2))
            .sum::<f32>()
            .sqrt();
            
        let other_magnitude: f32 = other.data.iter()
            .map(|b| b.powi(2))
            .sum::<f32>()
            .sqrt();
            
        if self_magnitude == 0.0 || other_magnitude == 0.0 {
            return 0.0;
        }
        
        dot_product / (self_magnitude * other_magnitude)
    }
    
    pub fn merge(&self, other: &Vector, weight: f32) -> Vector {
        let other_weight = 1.0 - weight;
        let merged_data: Vec<f32> = self.data.iter()
            .zip(other.data.iter())
            .map(|(a, b)| a * weight + b * other_weight)
            .collect();
            
        let mut new_vector = self.clone();
        new_vector.data = merged_data;
        new_vector.id = nanoid::nanoid!();
        new_vector.timestamp = sys_time().expect("Could not get system time");
        
        new_vector
    }
    
    pub fn normalize(&mut self) {
        let magnitude: f32 = self.data.iter()
            .map(|a| a.powi(2))
            .sum::<f32>()
            .sqrt();
            
        if magnitude > 0.0 {
            for val in self.data.iter_mut() {
                *val /= magnitude;
            }
        }
    }
    
    pub fn to_point_2d(&self) -> [u32; 2] {
        // Convert first two dimensions to u32 coordinates for Hilbert curve
        let scale_factor = 1000.0; // Scale to get more precision
        
        let x = if self.data.len() > 0 {
            ((self.data[0] + 1.0) * 0.5 * scale_factor) as u32
        } else {
            0
        };
        
        let y = if self.data.len() > 1 {
            ((self.data[1] + 1.0) * 0.5 * scale_factor) as u32
        } else {
            0
        };
        
        [x, y]
    }
}
