use serde::{Serialize, Deserialize};
use hdk::prelude::*;
use std::collections::HashSet;

#[hdk_entry(id = "centroid")]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Centroid {
    pub id: String,
    pub vector: Vec<f32>,
    pub level: u8,
    pub cluster_size: u32,
    pub responsible_agents: HashSet<AgentPubKey>,
    pub version: u64,
}

impl Centroid {
    pub fn new(vector: Vec<f32>, level: u8) -> Self {
        Self {
            id: nanoid::nanoid!(),
            vector,
            level,
            cluster_size: 0,
            responsible_agents: HashSet::new(),
            version: 0,
        }
    }

    pub fn update(&mut self, vector: &[f32]) {
        let weight = 1.0 / (self.cluster_size + 1) as f32;
        for (c, v) in self.vector.iter_mut().zip(vector.iter()) {
            *c = *c * (1.0 - weight) + v * weight;
        }
        self.cluster_size += 1;
        self.version += 1;
    }
}