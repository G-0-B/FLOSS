// src/sharding/migration.rs
use crate::core::Vector;
use crate::core::CentroidCRDT;
use serde::{Serialize, Deserialize};
use hdk::prelude::*;
use std::collections::HashMap;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct MigrationPlan {
    pub id: String,
    pub source_shard: String,
    pub target_shard: String,
    pub vectors: Vec<Vector>,
    pub centroids: Vec<CentroidCRDT>,
    pub status: MigrationStatus,
    pub created_at: u64,
    pub updated_at: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub enum MigrationStatus {
    Pending,
    InProgress { completed: usize, total: usize },
    Completed { success_count: usize, failure_count: usize },
    Failed { error: String },
}

impl MigrationPlan {
    pub fn new(source_shard: String, target_shard: String, vectors: Vec<Vector>, centroids: Vec<CentroidCRDT>) -> Self {
        let now = sys_time().expect("Could not get system time");
        Self {
            id: nanoid::nanoid!(),
            source_shard,
            target_shard,
            vectors,
            centroids,
            status: MigrationStatus::Pending,
            created_at: now,
            updated_at: now,
        }
    }

    pub fn update_progress(&mut self, completed: usize) {
        self.status = MigrationStatus::InProgress {
            completed,
            total: self.vectors.len(),
        };
        self.updated_at = sys_time().expect("Could not get system time");
    }

    pub fn complete(&mut self, success_count: usize, failure_count: usize) {
        self.status = MigrationStatus::Completed {
            success_count,
            failure_count,
        };
        self.updated_at = sys_time().expect("Could not get system time");
    }

    pub fn fail(&mut self, error: String) {
        self.status = MigrationStatus::Failed { error };
        self.updated_at = sys_time().expect("Could not get system time");
    }
    
    pub fn is_stale(&self, timeout_millis: u64) -> bool {
        let now = sys_time().expect("Could not get system time");
        now - self.updated_at > timeout_millis
    }
    
    pub fn to_entry(&self) -> ExternResult<Entry> {
        let entry = Entry::App(self.try_into()?);
        Ok(entry)
    }
    
    pub fn create_entry(&self) -> ExternResult<HeaderHash> {
        create_entry(self.to_entry()?)
    }
    
    pub fn update_entry(&self, original_hash: HeaderHash) -> ExternResult<HeaderHash> {
        update_entry(original_hash, self.to_entry()?)
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ShardStatus {
    pub id: String,
    pub vector_count: usize,
    pub centroids: Vec<CentroidCRDT>,
    pub last_update: u64,
    pub active_migrations: HashMap<String, String>, // migration_id -> target_shard
}

impl ShardStatus {
    pub fn new(id: String, centroids: Vec<CentroidCRDT>) -> Self {
        Self {
            id,
            vector_count: 0,
            centroids,
            last_update: sys_time().expect("Could not get system time"),
            active_migrations: HashMap::new(),
        }
    }
    
    pub fn add_migration(&mut self, migration_id: String, target_shard: String) {
        self.active_migrations.insert(migration_id, target_shard);
        self.last_update = sys_time().expect("Could not get system time");
    }
    
    pub fn remove_migration(&mut self, migration_id: &str) {
        self.active_migrations.remove(migration_id);
        self.last_update = sys_time().expect("Could not get system time");
    }
    
    pub fn update_vector_count(&mut self, count: usize) {
        self.vector_count = count;
        self.last_update = sys_time().expect("Could not get system time");
    }
    
    pub fn update_centroids(&mut self, centroids: Vec<CentroidCRDT>) {
        self.centroids = centroids;
        self.last_update = sys_time().expect("Could not get system time");
    }
}
