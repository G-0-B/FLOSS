// src/core/mod.rs
mod vector;
mod centroid;
mod metrics;
mod centroid_crdt;

pub use vector::Vector;
pub use centroid::Centroid;
pub use metrics::Metrics;
pub use centroid_crdt::{CentroidCRDT, VersionVector};
