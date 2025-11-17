//! A module for Conflict-Free Replicated Data Types (CRDTs).

use hdk::prelude::*;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Centroid {
    pub vector: Vec<f32>,
    pub weight: u32,
}

impl Centroid {
    /// Merges another centroid into this one.
    pub fn merge(&mut self, other: &Centroid) {
        let total_weight = self.weight + other.weight;
        if total_weight == 0 {
            return;
        }

        for i in 0..self.vector.len() {
            self.vector[i] = (self.vector[i] * self.weight as f32 + other.vector[i] * other.weight as f32) / total_weight as f32;
        }
        self.weight = total_weight;
    }
}
