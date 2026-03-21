/// Pure-Rust vector operations for Rose Forest semantic search.
///
/// Extracted from `archive/old_project/src/core/vector.rs` with Holochain
/// dependencies removed.  This module provides only the math needed by the
/// coordinator zome's `vector_search` function.

/// A thin wrapper around `Vec<f32>` that provides distance and similarity
/// operations used by the Rose Forest knowledge graph.
pub struct Vector {
    pub data: Vec<f32>,
}

impl Vector {
    /// Create a new Vector from raw float data.
    pub fn new(data: Vec<f32>) -> Self {
        Self { data }
    }

    /// Cosine similarity between two vectors.
    ///
    /// Returns a value in [-1.0, 1.0].  Returns 0.0 if either vector has
    /// zero magnitude (avoids division by zero).
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

    /// Euclidean distance between two vectors.
    pub fn distance(&self, other: &Vector) -> f32 {
        self.data.iter()
            .zip(other.data.iter())
            .map(|(a, b)| (a - b).powi(2))
            .sum::<f32>()
            .sqrt()
    }

    /// Normalize the vector to unit length in-place.
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
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cosine_identical_vectors() {
        let a = Vector::new(vec![1.0, 0.0, 0.0]);
        let b = Vector::new(vec![1.0, 0.0, 0.0]);
        assert!((a.cosine_similarity(&b) - 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_cosine_orthogonal_vectors() {
        let a = Vector::new(vec![1.0, 0.0]);
        let b = Vector::new(vec![0.0, 1.0]);
        assert!(a.cosine_similarity(&b).abs() < 1e-6);
    }

    #[test]
    fn test_cosine_opposite_vectors() {
        let a = Vector::new(vec![1.0, 0.0]);
        let b = Vector::new(vec![-1.0, 0.0]);
        assert!((a.cosine_similarity(&b) + 1.0).abs() < 1e-6);
    }

    #[test]
    fn test_cosine_zero_vector_returns_zero() {
        let a = Vector::new(vec![0.0, 0.0]);
        let b = Vector::new(vec![1.0, 1.0]);
        assert_eq!(a.cosine_similarity(&b), 0.0);
    }

    #[test]
    fn test_distance() {
        let a = Vector::new(vec![0.0, 0.0]);
        let b = Vector::new(vec![3.0, 4.0]);
        assert!((a.distance(&b) - 5.0).abs() < 1e-6);
    }

    #[test]
    fn test_normalize() {
        let mut v = Vector::new(vec![3.0, 4.0]);
        v.normalize();
        let mag: f32 = v.data.iter().map(|x| x.powi(2)).sum::<f32>().sqrt();
        assert!((mag - 1.0).abs() < 1e-6);
    }
}
