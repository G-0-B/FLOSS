"""embedding_frames_of_scale
==============================

This module provides utilities for working with *multi‑scale* embeddings,
where each embedding lives at a particular level of granularity.  A
**frame of reference** in this context is a *matrix of matrices* – a
mapping from one level of detail to another.  Fine‑grained vectors
represent individual agents or sensors, while coarse‑grained vectors
represent communities or aggregates.  The relationships between these
levels are *fractal* and **self‑similar**: a coarse embedding is built
from the sum (or mean) of its constituent fine embeddings, and this
pattern can repeat recursively.

The research inspiration for this design comes from recent work on
multi‑scale node embeddings for graph modelling and generation, where
Milocco et al. (2025) propose that coarse (block‑node) embeddings
should be statistically consistent with the sum of the embeddings of
their constituent nodes【44685813190291†L48-L69】.  By encoding this
property directly into the embedding data structure, we support
hierarchical reference frames that can be composed, decomposed and
embedded within one another.  This mirrors how biological and
agentic systems use nested coordinate frames – from retinal
retinotopic maps to head‑centred and world‑centred representations –
to interpret sensory input【86986790368444†L132-L141】.

In the spirit of FLOSSI0ULLK values:

* **Love** – Each embedding retains provenance metadata about its
  origin and the agents that contributed to it; coarse embeddings are
  transparent aggregations rather than opaque averages.
* **Light** – Logging is used throughout to illuminate how
  embeddings are constructed and combined, aiding observability and
  accountability.
* **Knowledge** – Hierarchical embeddings support collective
  intelligence by allowing local knowledge to be aggregated into
  global summaries without losing the ability to drill back down.

The classes in this module are written with type hints, clear
docstrings and modest error handling to encourage reuse in a
distributed intelligence system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Iterable, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass
class Embedding:
    """Represents a single embedding vector along with optional metadata.

    Parameters
    ----------
    vector:
        A one‑dimensional numpy array containing the numeric embedding.
    metadata:
        Optional dictionary carrying provenance or descriptive information
        about this embedding (e.g. agent ID, timestamp, context).  This
        dictionary can be arbitrarily nested.  Storing metadata aligns
        with the FLOSSI0ULLK principle of **Love**, preserving the
        identity and agency of contributors.
    """
    vector: np.ndarray
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.vector, np.ndarray):
            raise TypeError("vector must be a numpy.ndarray")
        if self.vector.ndim != 1:
            raise ValueError("vector must be one‑dimensional")

class MultiScaleEmbedding:
    """Manages embeddings across multiple scales or reference frames.

    This class maintains a mapping from level identifiers (strings or
    integers) to dictionaries of embeddings.  It provides methods to
    add fine‑level embeddings and to generate coarser embeddings by
    aggregating finer ones.  A coarse embedding encapsulates the
    information of its child embeddings without discarding their
    individual contributions.  This supports fractal, recursive
    structures where a matrix of matrices emerges naturally from the
    relationships between levels.

    Attributes
    ----------
    levels:
        Dictionary mapping level identifiers to dictionaries of
        embeddings keyed by an embedding ID.  For example,
        ``levels['fine']['node_1']`` returns the ``Embedding`` object
        representing node 1 at the fine level.
    aggregator:
        Callable used to combine vectors when creating coarse
        embeddings.  By default it sums the vectors, consistent with
        the statistical requirements for multi‑scale embeddings
        proposed by Milocco et al. (2025)【44685813190291†L48-L69】.  An
        alternative aggregator (e.g. mean) can be supplied.

    Notes
    -----
    • When adding a coarse level, you must provide a grouping that
      specifies how fine IDs map to coarse IDs.  The aggregator is
      applied to the vectors of the fine embeddings belonging to the
      same coarse ID.
    • Metadata from the fine embeddings is merged into the coarse
      embedding's metadata under the key ``'children'``.  This
      preserves provenance and enables drilling down.
    • Logging at DEBUG level reports the construction of coarse
      embeddings and any issues encountered.
    """

    def __init__(self, aggregator: Callable[[Iterable[np.ndarray]], np.ndarray] | None = None) -> None:
        self.levels: Dict[str, Dict[str, Embedding]] = {}
        self.aggregator: Callable[[Iterable[np.ndarray]], np.ndarray] = (
            aggregator if aggregator is not None else self._default_aggregator
        )

    @staticmethod
    def _default_aggregator(vectors: Iterable[np.ndarray]) -> np.ndarray:
        """Default aggregator that sums vectors elementwise.

        This aggregator ensures that coarse embeddings are
        statistically consistent with the sum of their constituent
        embeddings【44685813190291†L48-L69】.
        """
        vectors = list(vectors)
        if not vectors:
            raise ValueError("No vectors provided for aggregation")
        result = np.sum(vectors, axis=0)
        return result

    def add_embedding(self, level: str, embedding_id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an embedding at a given level.

        Parameters
        ----------
        level:
            Identifier for the level (e.g. 'fine', 'coarse1').
        embedding_id:
            Unique key for this embedding within the level.
        vector:
            One‑dimensional numpy array representing the embedding.
        metadata:
            Optional dictionary with provenance info.  Defaults to empty.

        Raises
        ------
        ValueError
            If an embedding with the same ID already exists at the level.
        """
        if level not in self.levels:
            self.levels[level] = {}
        if embedding_id in self.levels[level]:
            raise ValueError(f"Embedding ID '{embedding_id}' already exists in level '{level}'")
        emb = Embedding(vector=vector, metadata=metadata or {})
        self.levels[level][embedding_id] = emb
        logger.debug("Added embedding %s at level %s", embedding_id, level)

    def add_coarse_level(self, coarse_level: str, fine_level: str, grouping: Dict[str, List[str]]) -> None:
        """Create a coarse level by aggregating fine‑level embeddings.

        Parameters
        ----------
        coarse_level:
            Name for the new coarse level.
        fine_level:
            Existing level from which to aggregate embeddings.
        grouping:
            Mapping from coarse embedding IDs to lists of fine IDs.  Each
            coarse ID will combine the vectors of its associated fine
            embeddings using the configured aggregator.

        Raises
        ------
        KeyError
            If ``fine_level`` does not exist or if a fine ID is missing.
        ValueError
            If ``coarse_level`` already exists.

        Notes
        -----
        This method constructs coarse embeddings by combining the
        vectors of the specified fine embeddings.  The metadata of
        these children is preserved in a list under the ``'children'``
        key of the coarse embedding's metadata.  If any fine IDs are
        missing, a KeyError is raised.
        """
        if fine_level not in self.levels:
            raise KeyError(f"Fine level '{fine_level}' does not exist")
        if coarse_level in self.levels:
            raise ValueError(f"Coarse level '{coarse_level}' already exists")
        self.levels[coarse_level] = {}
        fine_embeddings = self.levels[fine_level]
        for coarse_id, fine_ids in grouping.items():
            vectors = []
            children_meta: List[Dict[str, Any]] = []
            for fid in fine_ids:
                if fid not in fine_embeddings:
                    raise KeyError(f"Fine embedding ID '{fid}' not found in level '{fine_level}'")
                emb = fine_embeddings[fid]
                vectors.append(emb.vector)
                children_meta.append({
                    'id': fid,
                    'metadata': emb.metadata,
                })
            coarse_vector = self.aggregator(vectors)
            coarse_metadata = {
                'children': children_meta,
                'source_level': fine_level,
            }
            self.levels[coarse_level][coarse_id] = Embedding(vector=coarse_vector, metadata=coarse_metadata)
            logger.debug("Created coarse embedding %s at level %s from %d children", coarse_id, coarse_level, len(fine_ids))

    def get_embedding(self, level: str, embedding_id: str) -> Embedding:
        """Retrieve an embedding by level and ID.

        Parameters
        ----------
        level:
            Level identifier.
        embedding_id:
            ID of the embedding within the level.

        Returns
        -------
        Embedding
            The requested embedding.

        Raises
        ------
        KeyError
            If the level or embedding ID does not exist.
        """
        if level not in self.levels:
            raise KeyError(f"Level '{level}' does not exist")
        if embedding_id not in self.levels[level]:
            raise KeyError(f"Embedding ID '{embedding_id}' not found in level '{level}'")
        return self.levels[level][embedding_id]

    def get_all_embeddings(self, level: str) -> Dict[str, Embedding]:
        """Return all embeddings at a given level.

        Parameters
        ----------
        level:
            Level identifier.

        Returns
        -------
        Dict[str, Embedding]
            A dictionary mapping embedding IDs to embeddings.

        Raises
        ------
        KeyError
            If the level does not exist.
        """
        if level not in self.levels:
            raise KeyError(f"Level '{level}' does not exist")
        return self.levels[level].copy()

    def get_num_levels(self) -> int:
        """Return the number of levels currently defined."""
        return len(self.levels)

    def get_level_names(self) -> List[str]:
        """Return all level names in insertion order."""
        return list(self.levels.keys())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the multi-scale embedding to a dictionary.

        Converts all numpy arrays to lists for JSON serialization.
        Preserves all embedding metadata and level structure.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation suitable for JSON serialization.
        """
        serialized_levels = {}
        for level_name, embeddings in self.levels.items():
            serialized_levels[level_name] = {}
            for emb_id, embedding in embeddings.items():
                serialized_levels[level_name][emb_id] = {
                    'vector': embedding.vector.tolist(),
                    'metadata': embedding.metadata,
                }

        return {
            'levels': serialized_levels,
            'is_default_aggregator': self.aggregator == self._default_aggregator,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiScaleEmbedding':
        """Reconstruct a MultiScaleEmbedding instance from dictionary representation.

        This is the inverse of to_dict(), enabling serialization round-trips.

        Parameters
        ----------
        data:
            Dictionary produced by to_dict().

        Returns
        -------
        MultiScaleEmbedding
            New MultiScaleEmbedding instance with restored state.

        Raises
        ------
        ValueError
            If data is malformed or missing required fields.
        TypeError
            If data types don't match expected schema.

        Example
        -------
        >>> original = MultiScaleEmbedding()
        >>> original.add_embedding('fine', 'test', np.array([1.0, 2.0]))
        >>> serialized = original.to_dict()
        >>> restored = MultiScaleEmbedding.from_dict(serialized)
        >>> np.allclose(
        ...     original.get_embedding('fine', 'test').vector,
        ...     restored.get_embedding('fine', 'test').vector
        ... )
        True
        """
        # Validate input type
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        # Validate required fields
        if 'levels' not in data:
            raise ValueError("Missing required field: 'levels'")

        # Create instance with appropriate aggregator
        # For now, only support default aggregator in deserialization
        # Custom aggregators would need separate handling
        is_default = data.get('is_default_aggregator', True)
        if not is_default:
            logger.warning(
                "Custom aggregator detected but not supported in deserialization; "
                "using default aggregator"
            )

        instance = cls()

        # Restore embeddings at each level
        levels_data = data['levels']
        if not isinstance(levels_data, dict):
            raise TypeError(f"Expected 'levels' to be dict, got {type(levels_data).__name__}")

        for level_name, embeddings_dict in levels_data.items():
            if not isinstance(embeddings_dict, dict):
                raise TypeError(
                    f"Expected embeddings at level '{level_name}' to be dict, "
                    f"got {type(embeddings_dict).__name__}"
                )

            for emb_id, emb_data in embeddings_dict.items():
                # Validate embedding data structure
                if not isinstance(emb_data, dict):
                    raise TypeError(
                        f"Expected embedding data for '{emb_id}' to be dict, "
                        f"got {type(emb_data).__name__}"
                    )

                if 'vector' not in emb_data:
                    raise ValueError(f"Missing 'vector' field in embedding '{emb_id}' at level '{level_name}'")

                # Convert list back to numpy array
                vector_data = emb_data['vector']
                if isinstance(vector_data, list):
                    try:
                        vector = np.array(vector_data, dtype=np.float32)
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Failed to convert vector for '{emb_id}' at level '{level_name}': {e}"
                        ) from e
                elif isinstance(vector_data, np.ndarray):
                    vector = vector_data.astype(np.float32)
                else:
                    raise TypeError(
                        f"Invalid vector type for '{emb_id}' at level '{level_name}': "
                        f"expected list or ndarray, got {type(vector_data).__name__}"
                    )

                # Restore metadata (default to empty dict if not present)
                metadata = emb_data.get('metadata', {})
                if not isinstance(metadata, dict):
                    raise TypeError(
                        f"Expected metadata for '{emb_id}' to be dict, "
                        f"got {type(metadata).__name__}"
                    )

                # Add the embedding to the instance
                instance.add_embedding(level_name, emb_id, vector, metadata)

        logger.debug(
            "Deserialized MultiScaleEmbedding with %d levels",
            len(instance.levels)
        )

        return instance

    def __repr__(self) -> str:
        return f"MultiScaleEmbedding(levels={list(self.levels.keys())})"

    # =========================================================================
    # Dictionary-like interface for composition support
    # =========================================================================

    @property
    def dimension(self) -> int:
        """Get the dimension of embeddings in this instance.

        Returns the dimension of the first embedding found, or 0 if empty.
        Assumes all embeddings have the same dimension.
        """
        for level_embeddings in self.levels.values():
            for emb in level_embeddings.values():
                return len(emb.vector)
        return 0

    def items(self, level: str = 'default') -> Iterable[tuple[str, np.ndarray]]:
        """Iterate over (key, vector) pairs at a given level.

        Parameters
        ----------
        level:
            Level to iterate over. Defaults to 'default'.

        Yields
        ------
        tuple[str, np.ndarray]
            Pairs of (embedding_id, vector)
        """
        if level not in self.levels:
            return
        for emb_id, emb in self.levels[level].items():
            yield (emb_id, emb.vector)

    def add(self, key: str, vector: np.ndarray, level: str = 'default', metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an embedding with a simpler interface.

        This is a convenience method for the dictionary-like interface.

        Parameters
        ----------
        key:
            Identifier for the embedding
        vector:
            Embedding vector
        level:
            Level to add to. Defaults to 'default'.
        metadata:
            Optional metadata
        """
        if level not in self.levels:
            self.levels[level] = {}
        # Allow overwriting in this interface (unlike add_embedding)
        emb = Embedding(vector=vector, metadata=metadata or {})
        self.levels[level][key] = emb
        logger.debug("Added/updated embedding %s at level %s", key, level)

    def get(self, key: str, level: str = 'default') -> Optional[np.ndarray]:
        """Get an embedding vector by key.

        Parameters
        ----------
        key:
            Identifier for the embedding
        level:
            Level to retrieve from. Defaults to 'default'.

        Returns
        -------
        Optional[np.ndarray]
            The embedding vector, or None if not found
        """
        if level not in self.levels:
            return None
        emb = self.levels[level].get(key)
        return emb.vector if emb else None

    def __contains__(self, key: str, level: str = 'default') -> bool:
        """Check if a key exists at the given level.

        Parameters
        ----------
        key:
            Identifier to check
        level:
            Level to check in. Defaults to 'default'.

        Returns
        -------
        bool
            True if key exists at the level
        """
        return level in self.levels and key in self.levels[level]

    def __len__(self, level: str = 'default') -> int:
        """Get the number of embeddings at the given level.

        Parameters
        ----------
        level:
            Level to count. Defaults to 'default'.

        Returns
        -------
        int
            Number of embeddings at the level
        """
        return len(self.levels.get(level, {}))

    # =========================================================================
    # Composition methods
    # =========================================================================

    def compose(
        self,
        other: 'MultiScaleEmbedding',
        strategy: str = 'merge',
        similarity_threshold: float = 0.95,
        level: str = 'default'
    ) -> 'MultiScaleEmbedding':
        """
        Compose embeddings from another MultiScaleEmbedding instance.

        Merges embeddings from `other` into this instance according to the
        specified strategy. This enables multi-agent memory composition.

        Args:
            other: Another MultiScaleEmbedding instance to compose with
            strategy: Composition strategy - one of:
                - 'merge': Add new items, skip near-duplicates (default)
                - 'average': Average embeddings for near-duplicates
                - 'append': Keep all items with unique keys
            similarity_threshold: Cosine similarity threshold for duplicate detection
                (only used with 'merge' and 'average' strategies)
            level: Which level to compose. Defaults to 'default'.

        Returns:
            self (for method chaining)

        Raises:
            ValueError: If dimensions don't match or invalid strategy
            TypeError: If other is not MultiScaleEmbedding

        Example:
            >>> memory1 = MultiScaleEmbedding()
            >>> memory1.add("concept_a", embedding_a)
            >>> memory2 = MultiScaleEmbedding()
            >>> memory2.add("concept_b", embedding_b)
            >>> memory1.compose(memory2, strategy='merge')
            >>> len(memory1)  # Now contains both concepts
            2
        """
        # Validate inputs
        if not isinstance(other, MultiScaleEmbedding):
            raise TypeError(f"Can only compose with MultiScaleEmbedding, got {type(other)}")

        # Validate strategy first (before early return)
        valid_strategies = ['merge', 'average', 'append']
        if strategy not in valid_strategies:
            raise ValueError(f"Invalid strategy '{strategy}'. Must be one of {valid_strategies}")

        # Check if other has the level we're trying to compose
        if level not in other.levels:
            logger.debug(f"Other MultiScaleEmbedding has no level '{level}', nothing to compose")
            return self

        # Check dimensions if both have embeddings
        if self.dimension > 0 and other.dimension > 0:
            if self.dimension != other.dimension:
                raise ValueError(
                    f"Dimension mismatch: self has {self.dimension}, other has {other.dimension}"
                )

        # Execute strategy
        if strategy == 'merge':
            self._compose_merge(other, similarity_threshold, level)
        elif strategy == 'average':
            self._compose_average(other, similarity_threshold, level)
        elif strategy == 'append':
            self._compose_append(other, level)

        return self

    def _compose_merge(self, other: 'MultiScaleEmbedding', threshold: float, level: str) -> None:
        """Merge strategy: add new items, skip duplicates."""
        for key, embedding in other.items(level):
            # Check if we already have a similar embedding
            is_duplicate = False
            for existing_key, existing_emb in self.items(level):
                # Normalize vectors for cosine similarity
                emb_norm = embedding / (np.linalg.norm(embedding) + 1e-10)
                existing_norm = existing_emb / (np.linalg.norm(existing_emb) + 1e-10)
                similarity = np.dot(emb_norm, existing_norm)
                if similarity > threshold:
                    logger.debug(f"Skipping '{key}' (duplicate of '{existing_key}', sim={similarity:.3f})")
                    is_duplicate = True
                    break

            if not is_duplicate:
                # Add with original key (may overwrite exact key match)
                self.add(key, embedding, level)
                logger.debug(f"Added '{key}' from composition")

    def _compose_average(self, other: 'MultiScaleEmbedding', threshold: float, level: str) -> None:
        """Average strategy: blend embeddings for duplicates."""
        for key, embedding in other.items(level):
            # Find most similar existing embedding
            best_match = None
            best_similarity = 0.0

            for existing_key, existing_emb in self.items(level):
                # Normalize vectors for cosine similarity
                emb_norm = embedding / (np.linalg.norm(embedding) + 1e-10)
                existing_norm = existing_emb / (np.linalg.norm(existing_emb) + 1e-10)
                similarity = np.dot(emb_norm, existing_norm)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = existing_key

            if best_match and best_similarity > threshold:
                # Average with best match
                existing_emb = self.get(best_match, level)
                averaged = (existing_emb + embedding) / 2
                # Renormalize
                norm = np.linalg.norm(averaged)
                if norm > 1e-10:
                    averaged = averaged / norm
                self.add(best_match, averaged, level)
                logger.debug(f"Averaged '{key}' with '{best_match}' (sim={best_similarity:.3f})")
            else:
                # Add as new item
                self.add(key, embedding, level)
                logger.debug(f"Added '{key}' (no match found)")

    def _compose_append(self, other: 'MultiScaleEmbedding', level: str) -> None:
        """Append strategy: keep all items with unique keys."""
        for key, embedding in other.items(level):
            # Ensure unique key
            unique_key = key
            counter = 2
            while self.__contains__(unique_key, level):
                unique_key = f"{key}_{counter}"
                counter += 1

            self.add(unique_key, embedding, level)
            if unique_key != key:
                logger.debug(f"Added '{key}' as '{unique_key}' (key conflict)")

    # =========================================================================
    # Serialization methods
    # =========================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Export embeddings to a dictionary for serialization.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing all levels and embeddings
        """
        result = {}
        for level, embeddings in self.levels.items():
            result[level] = {}
            for emb_id, emb in embeddings.items():
                result[level][emb_id] = {
                    'vector': emb.vector.tolist(),
                    'metadata': emb.metadata
                }
        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MultiScaleEmbedding':
        """Load embeddings from a dictionary.

        Parameters
        ----------
        data:
            Dictionary from to_dict()

        Returns
        -------
        MultiScaleEmbedding
            New instance with loaded embeddings
        """
        mse = MultiScaleEmbedding()
        for level, embeddings in data.items():
            mse.levels[level] = {}
            for emb_id, emb_data in embeddings.items():
                vector = np.array(emb_data['vector'])
                metadata = emb_data.get('metadata', {})
                mse.levels[level][emb_id] = Embedding(vector=vector, metadata=metadata)
        logger.debug(f"Loaded MultiScaleEmbedding with {len(mse.levels)} level(s)")
        return mse