"""
Swarm embedding manager using MultiScaleEmbedding framework.

Integrates with ../embedding_frames_of_scale.py
"""

from importlib import import_module
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List

import numpy as np

# Add parent directory to path to import embedding_frames_of_scale
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
embedding_module = import_module("embedding_frames_of_scale")
Embedding = embedding_module.Embedding
MultiScaleEmbedding = embedding_module.MultiScaleEmbedding

logger = logging.getLogger(__name__)


class SwarmEmbeddingManager:
    """Manages the hierarchical embeddings for the pony swarm.

    This class provides a specialized interface to the `MultiScaleEmbedding`
    framework, tailored for the needs of the Recursive Self-Aggregation (RSA)
    algorithm. It organizes embeddings into two primary levels:
    - **'fine'**: Represents the individual responses of each pony agent.
    - **'community'**: Represents the aggregated, collective knowledge of the swarm
      at each iteration.

    This hierarchical structure is a direct implementation of the "fractal memory"
    concept, allowing for the analysis of both individual contributions and the
    emergent, collective intelligence of the swarm. It is essential for tracking
    provenance, measuring diversity, and enabling "Federated Reasoning."

    Attributes:
        embeddings: An instance of `MultiScaleEmbedding` to store the hierarchical
            embedding data.
        iteration_history: A dictionary that tracks the responses generated at
            each iteration of the RSA algorithm.
    """

    def __init__(self):
        """Initializes the SwarmEmbeddingManager."""
        self.embeddings = MultiScaleEmbedding()
        self.iteration_history: Dict[int, List[Dict[str, Any]]] = {}

        logger.debug("Initialized SwarmEmbeddingManager with MultiScaleEmbedding")

    def add_pony_response(
        self,
        pony_id: str,
        iteration: int,
        response: str,
        vector: np.ndarray | list,
        metadata: Dict[str, Any] = None,
    ):
        """Stores the embedding of an individual pony's response.

        This method adds a new embedding to the 'fine' level of the hierarchical
        structure, representing a single pony's contribution at a specific
        iteration.

        Args:
            pony_id: The unique identifier of the pony agent.
            iteration: The RSA iteration number.
            response: The textual response from the pony.
            vector: The embedding vector of the response.
            metadata: Optional dictionary for additional provenance information.
        """
        # Convert list to numpy array if needed
        if isinstance(vector, list):
            vector = np.array(vector)

        embedding_id = f"{pony_id}_t{iteration}"

        self.embeddings.add_embedding(
            level="fine",
            embedding_id=embedding_id,
            vector=vector,
            metadata={
                "pony_id": pony_id,
                "iteration": iteration,
                "response_text": response[:100],  # First 100 chars
                "timestamp": metadata.get("timestamp") if metadata else None,
                **(metadata or {}),
            },
        )

        # Track in history
        if iteration not in self.iteration_history:
            self.iteration_history[iteration] = []

        self.iteration_history[iteration].append(
            {"pony_id": pony_id, "embedding_id": embedding_id, "response": response}
        )

    def aggregate_to_community(self, iteration: int, pony_ids: List[str]):
        """Aggregates individual pony embeddings into a community-level embedding.

        This method creates a coarse-grained embedding that represents the
        collective knowledge of the swarm at a given iteration. It does this by
        summing the 'fine'-level embeddings of the participating ponies, in
        accordance with the principles of multi-scale embedding.

        Args:
            iteration: The RSA iteration number to aggregate.
            pony_ids: A list of the pony IDs that contributed to this iteration.
        """
        community_id = f"community_t{iteration}"

        # Check if community level already exists
        if "community" not in self.embeddings.levels:
            # First aggregation - create community level
            grouping = {
                community_id: [f"{pony_id}_t{iteration}" for pony_id in pony_ids]
            }

            self.embeddings.add_coarse_level(
                coarse_level="community", fine_level="fine", grouping=grouping
            )
        else:
            # Community level exists - just add this iteration's aggregation
            # We need to temporarily create grouping for just this iteration
            fine_ids = [f"{pony_id}_t{iteration}" for pony_id in pony_ids]

            # Get vectors and aggregate manually
            vectors = []
            children_meta = []
            for fine_id in fine_ids:
                try:
                    emb = self.embeddings.get_embedding("fine", fine_id)
                    vectors.append(emb.vector)
                    children_meta.append({"id": fine_id, "metadata": emb.metadata})
                except KeyError:
                    logger.warning(f"Fine embedding {fine_id} not found")

            if vectors:
                # Aggregate using sum (MultiScaleEmbedding default)
                coarse_vector = np.sum(vectors, axis=0)

                # Add directly to community level
                self.embeddings.levels["community"][community_id] = Embedding(
                    vector=coarse_vector,
                    metadata={
                        "children": children_meta,
                        "source_level": "fine",
                        "iteration": iteration,
                    },
                )

    def get_diversity_metric(self, iteration: int) -> float:
        """Calculates the semantic diversity of the pony responses at a given iteration.

        This metric is crucial for understanding the health and exploratory
        capacity of the swarm. Higher diversity indicates that the ponies are
        generating a wider range of ideas, which can lead to more creative and
        robust solutions. The calculation is based on the average pairwise
        cosine distance between the response embeddings.

        Args:
            iteration: The RSA iteration number to analyze.

        Returns:
            A float between 0.0 and 1.0, where higher values indicate greater
            diversity.
        """
        if iteration not in self.iteration_history:
            return 0.0

        # Get all embeddings for this iteration
        embeddings = []
        for entry in self.iteration_history[iteration]:
            emb_id = entry["embedding_id"]
            try:
                emb = self.embeddings.get_embedding("fine", emb_id)
                embeddings.append(emb.vector)
            except KeyError:
                continue

        if len(embeddings) < 2:
            return 0.0

        # Calculate average pairwise cosine distance
        embeddings = np.array(embeddings)
        n = len(embeddings)

        total_distance = 0.0
        count = 0

        for i in range(n):
            for j in range(i + 1, n):
                # Cosine distance = 1 - cosine_similarity
                # Normalize vectors first
                vec_i = embeddings[i] / (np.linalg.norm(embeddings[i]) + 1e-10)
                vec_j = embeddings[j] / (np.linalg.norm(embeddings[j]) + 1e-10)
                cos_sim = np.dot(vec_i, vec_j)
                cos_dist = 1 - cos_sim
                total_distance += cos_dist
                count += 1

        return total_distance / count if count > 0 else 0.0

    def query_similar(
        self, query_vector: np.ndarray, level: str = "fine", top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """Finds the most semantically similar responses to a given query vector.

        This function enables the swarm to reference its past knowledge, a key
        capability for reducing "Cognitive Debt" and building upon prior work.

        Args:
            query_vector: The embedding vector of the query.
            level: The embedding level to search within ('fine' or 'community').
            top_k: The number of similar responses to return.

        Returns:
            A list of dictionaries, each containing a similar response and its
            metadata, sorted by similarity.
        """
        # Get all embeddings at level
        try:
            all_embeddings = self.embeddings.get_all_embeddings(level)
        except KeyError:
            return []

        if not all_embeddings:
            return []

        # Normalize query vector
        query_norm = query_vector / (np.linalg.norm(query_vector) + 1e-10)

        # Calculate similarities
        similarities = []
        for emb_id, emb in all_embeddings.items():
            vec = emb.vector
            vec_norm = vec / (np.linalg.norm(vec) + 1e-10)
            sim = np.dot(query_norm, vec_norm)  # Cosine similarity
            similarities.append((sim, emb_id, emb))

        # Sort and return top-k
        similarities.sort(reverse=True, key=lambda x: x[0])

        return [
            {"similarity": sim, "embedding_id": emb_id, "metadata": emb.metadata}
            for sim, emb_id, emb in similarities[:top_k]
        ]
