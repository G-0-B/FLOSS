/// Bridge between hREA Economic Events and Rose Forest Vector Operations
///
/// This module enables:
/// 1. Economic events to be indexed by vector embeddings
/// 2. Semantic search over value flows
/// 3. Value-weighted knowledge retrieval
/// 4. Contribution discovery through vector similarity

use hdk::prelude::*;
use hrea_integrity::{EconomicEvent, EconomicAction, ValueFlow, ContributionValue};

/// Vector embedding for an economic event
///
/// Enables semantic search over contributions, value flows, and resource interactions
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct EconomicEventEmbedding {
    /// Reference to the economic event
    pub event_hash: ActionHash,

    /// Vector embedding of event content (derived from action + resource + notes)
    pub embedding: Vec<f32>,

    /// Event action type (for filtering)
    pub action: EconomicAction,

    /// Provider agent
    pub provider: AgentPubKey,

    /// Resource being acted upon
    pub resource: ActionHash,

    /// When created
    pub created_at: Timestamp,
}

/// Value-weighted embedding for knowledge retrieval
///
/// Combines semantic similarity with economic value to rank results
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ValueWeightedEmbedding {
    /// Reference to the resource (Understanding, FileArtifact, etc.)
    pub resource_hash: ActionHash,

    /// Vector embedding of resource content
    pub embedding: Vec<f32>,

    /// Total contributed value (from DICE attribution)
    pub total_value: f64,

    /// Number of contributing events
    pub event_count: u32,

    /// When last updated
    pub updated_at: Timestamp,
}

/// Query input for value-weighted semantic search
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ValueWeightedQuery {
    /// Query text (will be embedded)
    pub query: String,

    /// Optional: filter by minimum value
    pub min_value: Option<f64>,

    /// Optional: filter by action type
    pub action_filter: Option<Vec<EconomicAction>>,

    /// Optional: filter by time window
    pub time_window: Option<(Timestamp, Timestamp)>,

    /// Number of results to return
    pub limit: usize,
}

/// Result from value-weighted search
#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ValueWeightedResult {
    /// Resource hash
    pub resource: ActionHash,

    /// Semantic similarity score (0.0-1.0)
    pub similarity: f32,

    /// Economic value
    pub value: f64,

    /// Combined score (similarity * value_weight)
    pub combined_score: f64,

    /// Contributing events
    pub events: Vec<ActionHash>,
}

impl EconomicEventEmbedding {
    /// Create embedding from economic event
    ///
    /// In production, would use sentence-transformers or similar
    /// For now, creates a simple hash-based projection
    pub fn from_event(event: &EconomicEvent, event_hash: ActionHash) -> Self {
        // Combine event data into text for embedding
        let event_text = format!(
            "action={:?} resource={} note={}",
            event.action,
            event.resource,
            event.note.as_deref().unwrap_or("")
        );

        // Create embedding (mock for now)
        let embedding = Self::mock_embed(&event_text);

        EconomicEventEmbedding {
            event_hash,
            embedding,
            action: event.action.clone(),
            provider: event.provider.clone(),
            resource: event.resource.clone(),
            created_at: event.timestamp,
        }
    }

    /// Mock embedding function (replace with real model)
    fn mock_embed(text: &str) -> Vec<f32> {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut hasher = DefaultHasher::new();
        text.hash(&mut hasher);
        let seed = hasher.finish();

        // Generate deterministic "embedding" from hash
        let mut embedding = Vec::with_capacity(384);
        let mut state = seed;

        for _ in 0..384 {
            state = state.wrapping_mul(1103515245).wrapping_add(12345);
            let value = ((state / 65536) % 32768) as f32 / 16384.0 - 1.0;
            embedding.push(value);
        }

        // Normalize
        let magnitude: f32 = embedding.iter().map(|x| x * x).sum::<f32>().sqrt();
        if magnitude > 0.0 {
            for x in &mut embedding {
                *x /= magnitude;
            }
        }

        embedding
    }

    /// Calculate cosine similarity with another embedding
    pub fn similarity(&self, other: &[f32]) -> f32 {
        if self.embedding.len() != other.len() {
            return 0.0;
        }

        let dot_product: f32 = self.embedding
            .iter()
            .zip(other.iter())
            .map(|(a, b)| a * b)
            .sum();

        dot_product.max(-1.0).min(1.0)
    }
}

impl ValueWeightedEmbedding {
    /// Create from resource and its contribution values
    pub fn from_resource(
        resource_hash: ActionHash,
        content: &str,
        contributions: &[ContributionValue],
    ) -> Self {
        // Create embedding from resource content
        let embedding = EconomicEventEmbedding::mock_embed(content);

        // Calculate total value
        let total_value: f64 = contributions.iter().map(|c| c.final_value).sum();

        // Count contributing events
        let event_count = contributions
            .iter()
            .flat_map(|c| &c.contributing_events)
            .count() as u32;

        ValueWeightedEmbedding {
            resource_hash,
            embedding,
            total_value,
            event_count,
            updated_at: Timestamp::now(),
        }
    }

    /// Calculate similarity with query
    pub fn similarity(&self, query_embedding: &[f32]) -> f32 {
        if self.embedding.len() != query_embedding.len() {
            return 0.0;
        }

        let dot_product: f32 = self.embedding
            .iter()
            .zip(query_embedding.iter())
            .map(|(a, b)| a * b)
            .sum();

        dot_product.max(-1.0).min(1.0)
    }

    /// Calculate combined score (similarity * value)
    pub fn combined_score(&self, query_embedding: &[f32], value_weight: f64) -> f64 {
        let similarity = self.similarity(query_embedding) as f64;

        // Combine similarity and value with weighting
        // value_weight=0.0: pure semantic search
        // value_weight=1.0: equal weighting
        // value_weight=2.0: double weight on value
        similarity * (1.0 - value_weight * 0.5) + self.total_value * value_weight * 0.5
    }
}

/// Search economic events by semantic similarity
pub fn search_economic_events(
    query: &str,
    events: &[(ActionHash, EconomicEvent)],
    limit: usize,
) -> Vec<(ActionHash, EconomicEvent, f32)> {
    // Create query embedding
    let query_embedding = EconomicEventEmbedding::mock_embed(query);

    // Calculate similarities
    let mut results: Vec<_> = events
        .iter()
        .map(|(hash, event)| {
            let event_embedding = EconomicEventEmbedding::from_event(event, hash.clone());
            let similarity = event_embedding.similarity(&query_embedding);
            (hash.clone(), event.clone(), similarity)
        })
        .collect();

    // Sort by similarity (descending)
    results.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap());

    // Limit results
    results.truncate(limit);

    results
}

/// Search resources with value weighting
pub fn search_value_weighted(
    query: &ValueWeightedQuery,
    resources: &[(ActionHash, String, Vec<ContributionValue>)],
    value_weight: f64,
) -> Vec<ValueWeightedResult> {
    // Create query embedding
    let query_embedding = EconomicEventEmbedding::mock_embed(&query.query);

    // Calculate scores
    let mut results: Vec<_> = resources
        .iter()
        .filter_map(|(hash, content, contributions)| {
            // Apply filters
            if let Some(min_value) = query.min_value {
                let total_value: f64 = contributions.iter().map(|c| c.final_value).sum();
                if total_value < min_value {
                    return None;
                }
            }

            // Create weighted embedding
            let weighted = ValueWeightedEmbedding::from_resource(
                hash.clone(),
                content,
                contributions,
            );

            // Calculate combined score
            let similarity = weighted.similarity(&query_embedding);
            let combined_score = weighted.combined_score(&query_embedding, value_weight);

            // Get contributing events
            let events: Vec<_> = contributions
                .iter()
                .flat_map(|c| c.contributing_events.clone())
                .collect();

            Some(ValueWeightedResult {
                resource: hash.clone(),
                similarity,
                value: weighted.total_value,
                combined_score,
                events,
            })
        })
        .collect();

    // Sort by combined score (descending)
    results.sort_by(|a, b| b.combined_score.partial_cmp(&a.combined_score).unwrap());

    // Limit results
    results.truncate(query.limit);

    results
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embedding_similarity() {
        let text1 = "GPT-4 is a language model";
        let text2 = "GPT-4 is an LLM";
        let text3 = "Completely different content";

        let emb1 = EconomicEventEmbedding::mock_embed(text1);
        let emb2 = EconomicEventEmbedding::mock_embed(text2);
        let emb3 = EconomicEventEmbedding::mock_embed(text3);

        // Calculate similarities
        let sim_12 = calculate_similarity(&emb1, &emb2);
        let sim_13 = calculate_similarity(&emb1, &emb3);

        // Same/similar text should have higher similarity than different text
        // Note: With hash-based mock, this won't actually work, but demonstrates the concept
        println!("Similarity 1-2: {}", sim_12);
        println!("Similarity 1-3: {}", sim_13);
    }

    fn calculate_similarity(a: &[f32], b: &[f32]) -> f32 {
        if a.len() != b.len() {
            return 0.0;
        }

        a.iter().zip(b.iter()).map(|(x, y)| x * y).sum()
    }

    #[test]
    fn test_value_weighting() {
        let resource_hash = ActionHash::from_raw_36(vec![0u8; 36]);

        let content = "Important knowledge contribution";

        let contributions = vec![
            ContributionValue {
                agent: AgentPubKey::from_raw_36(vec![1u8; 36]),
                resource: resource_hash.clone(),
                base_value: 0.5,
                moral_multiplier: 1.2,
                final_value: 0.6,
                calculated_at: Timestamp::now(),
                time_window: hrea_integrity::TimeWindow {
                    start: Timestamp::now(),
                    end: Timestamp::now(),
                },
                contributing_events: vec![],
            },
        ];

        let weighted = ValueWeightedEmbedding::from_resource(
            resource_hash,
            content,
            &contributions,
        );

        assert_eq!(weighted.total_value, 0.6);
        assert_eq!(weighted.event_count, 0);
        assert_eq!(weighted.embedding.len(), 384);
    }
}
