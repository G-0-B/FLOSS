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
        """Serialize the multi-scale embedding structure to a dictionary.

        Returns
        -------
        Dict[str, Any]
            Nested dictionary mapping level names to embedding ID dicts,
            each containing ``'vector'`` (as list) and ``'metadata'``.
        """
        result: Dict[str, Any] = {}
        for level_name, embeddings in self.levels.items():
            result[level_name] = {}
            for emb_id, emb in embeddings.items():
                result[level_name][emb_id] = {
                    'vector': emb.vector.tolist(),
                    'metadata': emb.metadata,
                }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any], aggregator: Callable[[Iterable[np.ndarray]], np.ndarray] | None = None) -> 'MultiScaleEmbedding':
        """Deserialize a MultiScaleEmbedding from a dictionary.

        Parameters
        ----------
        data:
            Dictionary produced by :meth:`to_dict`.
        aggregator:
            Optional aggregator callable.  Defaults to sum.

        Returns
        -------
        MultiScaleEmbedding
            Reconstructed instance with all levels and embeddings restored.
        """
        mse = cls(aggregator=aggregator)
        for level_name, embeddings in data.items():
            mse.levels[level_name] = {}
            for emb_id, emb_data in embeddings.items():
                vector = np.array(emb_data['vector'])
                metadata = emb_data.get('metadata', {})
                mse.levels[level_name][emb_id] = Embedding(vector=vector, metadata=metadata)
        return mse

    def __repr__(self) -> str:
        return f"MultiScaleEmbedding(levels={list(self.levels.keys())})"