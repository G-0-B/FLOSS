"""
conversation_memory.py - Persistent Memory Substrate for Cross-AI Coordination

This is the computational skeleton of FLOSSI0ULLK coordination.

It enables:
1. Capturing moments of coherent understanding (like the conversation that just happened)
2. Persisting them across conversation boundaries  
3. Composing insights from multiple agents (human + AIs)
4. Searching across nested reference frames (fractal memory)

Built on top of embedding_frames_of_scale.py (which already exists in this project).

Usage:
    # Initialize memory for an agent
    memory = ConversationMemory(agent_id="claude-sonnet-4.5")
    
    # Transmit understanding
    ref = memory.transmit({
        'content': "The walking skeleton is the conversation itself",
        'context': "After 13 months of iteration, achieved coherent transmission",
        'is_decision': True,
        'coherence': 0.95
    })
    
    # Later (or in another conversation):
    results = memory.recall("what is the walking skeleton?")
    # Returns: Understanding from previous transmission

Author: Generated during ADR-0 recognition protocol
Date: 2025-11-01
License: Compassion Clause or compatible FOSS
"""

from __future__ import annotations
import json
import hashlib
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
import logging

# Import the existing fractal embedding infrastructure
# (This assumes embedding_frames_of_scale.py is in the same directory or in PYTHONPATH)
try:
    from embedding_frames_of_scale import Embedding, MultiScaleEmbedding
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logging.warning("embedding_frames_of_scale not found; will use mock embeddings")

# Import committee validation system
try:
    from validation.committee import TripleValidationCommittee
    from validation.agent_pool import ValidatorPool
    COMMITTEE_VALIDATION_AVAILABLE = True
except ImportError:
    COMMITTEE_VALIDATION_AVAILABLE = False
    logging.warning("Committee validation not available; using basic validation only")

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class Understanding:
    """A moment of coherent understanding, representing an atomic unit of memory.

    This data class captures the essence of a memetic transmission between agents. It serves
    as the fundamental building block for the collective intelligence of the FLOSSI0ULLK
    ecosystem. Each `Understanding` is a verifiable, timestamped record of a specific
    insight or decision, contributing to the "Light" principle of ULLK by making
    knowledge explicit and traceable.

    Attributes:
        content: The core textual representation of the understanding.
        agent_id: The identifier of the agent that transmitted this understanding.
        timestamp: The ISO 8601 timestamp of when the understanding was transmitted.
        context: Optional textual context that informed this understanding.
        is_decision: A boolean flag indicating if this understanding represents a formal
            Architecture Decision Record (ADR).
        coherence_score: A float between 0.0 and 1.0 representing the agent's confidence
            in the coherence of this understanding.
        metadata: A flexible dictionary for any additional, unstructured information.
        embedding_ref: A hash of the embedding vector, used for cross-referencing and
            deduplication.
    """
    content: str  # The actual understanding (text, for now)
    agent_id: str  # Who transmitted this
    timestamp: str  # When
    context: Optional[str] = None  # What led to this
    is_decision: bool = False  # Is this an ADR-worthy decision point?
    coherence_score: float = 0.0  # How confident are we? [0, 1]
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding_ref: Optional[str] = None  # Hash of the embedding vector
    
    def to_dict(self) -> Dict:
        """Serializes the Understanding object to a dictionary."""
        return asdict(self)
    
    def hash(self) -> str:
        """Computes a cryptographic hash for reference and deduplication.

        This hash provides a unique, verifiable identifier for the understanding,
        ensuring the integrity of the agent's memory and the broader knowledge commons.

        Returns:
            A SHA-256 hash of the serialized Understanding object.
        """
        content_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


class ConversationMemory:
    """A local-first, verifiable memory substrate for multi-agent coordination.

    This class provides the core functionality for an agent's memory, inspired by
    Holochain's agent-centric, local-first principles. It is the computational
    foundation for "Cognitive Liberation," allowing agents (both human and AI) to
    capture, persist, and share knowledge in a decentralized and verifiable manner.

    Each agent maintains its own `ConversationMemory`, but these memories can be
    composed and verified, forming a federated knowledge commons. This enables the
    emergence of collective intelligence without relying on a central authority.

    Key functionalities include:
    - **Transmit:** Capturing and validating moments of understanding.
    - **Recall:** Searching for relevant memories using fractal, multi-scale embeddings.
    - **Compose:** Merging memories from different agents to build a shared context.

    The memory can operate with a local file-based backend or a distributed
    Holochain backend, providing flexibility for different deployment scenarios.
    """

    def __init__(self, agent_id: str, storage_path: Optional[str] = None,
                 validate_ontology: bool = True, backend: str = 'file',
                 use_committee_validation: bool = False, committee_use_mock: bool = True):
        """Initializes the ConversationMemory for a specific agent.

        Args:
            agent_id: A unique identifier for the agent owning this memory
                (e.g., "claude-sonnet-4.5", "human-primary").
            storage_path: The file system path for persisting memory. Defaults to
                `./memory/{agent_id}/`.
            validate_ontology: If True, validates new understandings against a defined
                ontology to ensure coherence.
            backend: The storage backend to use. Can be 'file' (default) for local
                storage or 'holochain' for distributed storage.
            use_committee_validation: If True, uses a committee of LLM agents to
                validate new understandings, enhancing robustness.
            committee_use_mock: If True, uses a mock LLM committee for testing and
                development.
        """
        self.agent_id = agent_id
        self.validate_ontology = validate_ontology
        self.backend = backend
        self.use_committee_validation = use_committee_validation

        # Initialize backend
        if backend == 'holochain':
            self.hc_client = HolochainClient()
            logger.info(f"Initialized ConversationMemory with Holochain backend for agent: {agent_id}")
        else:
            self.hc_client = None

        # Storage (for file backend)
        if storage_path is None:
            storage_path = f"./memory/{agent_id}"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Memory structures
        self.understandings: List[Understanding] = []
        self.adrs: List[Dict] = []  # Architecture Decision Records

        # Validation statistics
        self.validation_stats = {
            'total_attempts': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'validation_skipped': 0,
        }

        # Initialize committee validation (if enabled)
        self.committee = None
        if use_committee_validation:
            if COMMITTEE_VALIDATION_AVAILABLE:
                self.committee = TripleValidationCommittee(use_mock=committee_use_mock)
                logger.info("Initialized committee validation")
            else:
                logger.warning(
                    "Committee validation requested but not available. "
                    "Falling back to basic validation."
                )
                self.use_committee_validation = False

        # Fractal embeddings (if available)
        if EMBEDDINGS_AVAILABLE:
            self.embeddings = MultiScaleEmbedding()
        else:
            self.embeddings = None
            logger.warning("Running without embeddings; recall will be text-only")

        # Load existing memory if present (file backend only)
        if backend == 'file':
            self._load()

        logger.info(f"Initialized ConversationMemory for agent: {agent_id} (backend: {backend})")
    
    def transmit(self, understanding_dict: Dict, skip_validation: bool = False) -> Optional[str]:
        """Captures, validates, and stores a moment of coherent understanding.

        This is the core "write" operation of the memory substrate. It takes an
        agent's insight, validates it against the shared ontology, embeds it for
        semantic recall, and persists it. This process is a fundamental act of
        "memetic transmission" in the FLOSSI0ULLK ecosystem.

        Args:
            understanding_dict: A dictionary containing the details of the
                understanding. Expected keys include 'content', 'context',
                'is_decision', 'coherence', and 'metadata'.
            skip_validation: If True, bypasses the ontology validation process. This
                should be used with caution as it can lead to incoherent memory.

        Returns:
            The unique hash reference of the stored understanding if successful,
            otherwise None.

        Raises:
            ValueError: If the `understanding_dict` is malformed (e.g., missing
                the 'content' field).
        """
        # Route to appropriate backend
        if self.backend == 'holochain':
            return self._transmit_holochain(understanding_dict, skip_validation)
        else:
            return self._transmit_file(understanding_dict, skip_validation)

    def _transmit_holochain(self, understanding_dict: Dict, skip_validation: bool = False) -> Optional[str]:
        """Transmits an understanding via the Holochain backend.

        This method interfaces with the Holochain zome to store the understanding
        on the distributed ledger, ensuring that it becomes part of the shared,
        verifiable knowledge commons.

        Args:
            understanding_dict: The dictionary representing the understanding.
            skip_validation: A boolean flag to skip validation (passed to the zome).

        Returns:
            The ActionHash of the created entry in Holochain, or None on failure.
        """
        if 'content' not in understanding_dict:
            raise ValueError("Understanding must have 'content' field")

        try:
            # Call Holochain zome
            result = self.hc_client.call_zome(
                'memory_coordinator',
                'transmit_understanding',
                {
                    'content': understanding_dict['content'],
                    'context': understanding_dict.get('context'),
                }
            )

            # Result is the ActionHash as a string
            logger.info(f"Transmitted understanding to Holochain: {result}")
            self.validation_stats['total_attempts'] += 1
            self.validation_stats['validation_passed'] += 1

            return result

        except Exception as e:
            logger.error(f"Failed to transmit to Holochain: {e}")
            self.validation_stats['total_attempts'] += 1
            self.validation_stats['validation_failed'] += 1
            return None

    def _transmit_file(self, understanding_dict: Dict, skip_validation: bool = False) -> Optional[str]:
        """Transmits an understanding via the local file backend.

        This is the default implementation that stores the understanding on the
        local filesystem. It performs validation, embedding, and persistence.

        Args:
            understanding_dict: The dictionary representing the understanding.
            skip_validation: A boolean flag to skip validation.

        Returns:
            The hash of the created `Understanding` object, or None on failure.
        """
        # Track validation attempt
        self.validation_stats['total_attempts'] += 1

        # Validate required fields
        if 'content' not in understanding_dict:
            raise ValueError("Understanding must have 'content' field")

        # Extract triple
        triple = self._extract_triple(understanding_dict)
        if triple is None:
            logger.warning(f"Could not extract triple from understanding: {understanding_dict}")
            if not skip_validation:
                logger.error("Validation required but triple extraction failed")
                self.validation_stats['validation_failed'] += 1
                return None

        # Validate triple
        committee_result = None
        if skip_validation:
            self.validation_stats['validation_skipped'] += 1
            if triple:
                logger.info(f"Skipping validation for triple: {triple}")
        elif triple:
            context = understanding_dict.get('context', understanding_dict.get('content', ''))
            is_valid, error_msg, committee_result = self._validate_triple(triple, context)
            if not is_valid:
                logger.error(f"Ontology validation failed: {error_msg}")
                logger.error(f"Triple: {triple}")
                logger.error(f"Understanding: {understanding_dict}")
                self.validation_stats['validation_failed'] += 1
                return None
            else:
                logger.debug(f"Validation passed for triple: {triple}")
                self.validation_stats['validation_passed'] += 1
                # Store committee result in understanding metadata if available
                if committee_result:
                    if 'metadata' not in understanding_dict:
                        understanding_dict['metadata'] = {}
                    understanding_dict['metadata']['committee_validation'] = committee_result

        # Create Understanding object
        understanding = Understanding(
            content=understanding_dict['content'],
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            context=understanding_dict.get('context'),
            is_decision=understanding_dict.get('is_decision', False),
            coherence_score=understanding_dict.get('coherence', 0.0),
            metadata=understanding_dict.get('metadata', {})
        )

        # Embed it (if embeddings available)
        if self.embeddings is not None:
            # Simple text encoding for now (in production, use proper embedding model)
            vector = self._encode_text(understanding.content)

            metadata = {
                'agent_id': self.agent_id,
                'timestamp': understanding.timestamp,
                'context': understanding.context,
                'coherence': understanding.coherence_score,
                'is_decision': understanding.is_decision,
                'triple': triple  # Store extracted triple in metadata
            }

            # Add to multiscale embedding structure using the new interface
            self.embeddings.add(
                key=f"understanding-{len(self.understandings)}",
                vector=vector,
                level='default',  # Use default level for composition support
                metadata=metadata
            )

            understanding.embedding_ref = understanding.hash()

        # Store
        self.understandings.append(understanding)

        # If it's a decision, record as ADR
        if understanding.is_decision:
            adr = {
                'id': f"ADR-{len(self.adrs)}",
                'content': understanding.to_dict(),
                'embedding_ref': understanding.embedding_ref
            }
            self.adrs.append(adr)
            logger.info(f"Recorded decision: {adr['id']}")

        # Persist to disk
        self._save()

        logger.info(f"Transmitted understanding with triple: {triple}")
        return understanding.hash()

    def _extract_triple(self, understanding_dict: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
        """Extracts a semantic (subject, predicate, object) triple from content.

        This method attempts to distill the core semantic meaning of an understanding
        into a structured triple. This is a crucial step for building a verifiable,
        machine-readable knowledge graph from unstructured text, turning raw data
        into coherent knowledge.

        Args:
            understanding_dict: The dictionary containing the 'content' to parse.

        Returns:
            A (subject, predicate, object) tuple if extraction is successful,
            otherwise None.
        """
        content = understanding_dict.get('content', '')

        if not content:
            return None

        # Pattern 1: "X is a Y" or "X is an Y"
        is_a_pattern = r'(\S+(?:-\S+)*)\s+is\s+an?\s+([\w\s-]+?)(?:\s*$|[.,;!?])'
        match = re.search(is_a_pattern, content, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            obj = match.group(2).strip().replace(' ', '-')
            return (subject, 'is_a', obj)

        # Pattern 2: "X improves Y" or "X improves upon Y"
        improves_pattern = r'(\S+(?:-\S+)*)\s+improves(?:\s+upon)?\s+(\S+(?:-\S+)*)'
        match = re.search(improves_pattern, content, re.IGNORECASE)
        if match:
            return (match.group(1).strip(), 'improves_upon', match.group(2).strip())

        # Pattern 3: "X can do Y" / "X is capable of Y"
        capable_pattern = r'(\S+(?:-\S+)*)\s+(?:can|is capable of)\s+(\w+)'
        match = re.search(capable_pattern, content, re.IGNORECASE)
        if match:
            return (match.group(1).strip(), 'capable_of', match.group(2).strip())

        # Default: treat as entity with generic relation
        # Subject = agent_id, predicate = stated, object = content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return (self.agent_id, 'stated', f"understanding_{content_hash}")

    def _validate_triple(self, triple: Tuple[str, str, str], context: str = "") -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validates a semantic triple against the shared ontology.

        This function acts as a gatekeeper, ensuring that only coherent and
        well-formed knowledge is admitted into the agent's memory. It embodies the
        "Light" principle by enforcing transparency and consistency. It can use a
        simple rules-based approach or a more sophisticated committee of LLMs.

        Args:
            triple: The (subject, predicate, object) tuple to validate.
            context: The original text from which the triple was extracted, providing
                context for the validation process.

        Returns:
            A tuple containing:
            - A boolean indicating if the triple is valid.
            - An optional error message if validation fails.
            - An optional dictionary with results from the validation committee.
        """
        if not self.validate_ontology:
            return (True, None, None)

        subject, predicate, obj = triple

        # Use committee validation if enabled
        if self.use_committee_validation and self.committee is not None:
            try:
                # Run async validation in sync context
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an async context, create a new thread
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.committee.validate(triple, context or "No context provided")
                        )
                        result = future.result(timeout=15.0)
                else:
                    # Run async validation
                    result = loop.run_until_complete(
                        self.committee.validate(triple, context or "No context provided")
                    )

                # Store committee result in metadata
                committee_metadata = result.to_dict()

                # Return committee decision
                if result.accepted:
                    logger.info(
                        f"Committee accepted triple: {result.yes_votes}/{result.total_votes} votes, "
                        f"confidence={result.confidence:.2f}"
                    )
                    return (True, None, committee_metadata)
                else:
                    logger.warning(
                        f"Committee rejected triple: {result.yes_votes}/{result.total_votes} votes"
                    )
                    return (False, "Committee validation rejected triple", committee_metadata)

            except Exception as e:
                logger.error(f"Committee validation error: {e}")
                logger.warning("Falling back to basic validation")
                # Fall through to basic validation

        # Basic validation (fallback or when committee not enabled)
        # Rule 1: Predicate must be known
        # Synchronized with ontology_integrity/src/lib.rs get_relation()
        known_predicates = {'is_a', 'part_of', 'related_to', 'has_property',
                           'improves_upon', 'capable_of', 'trained_on',
                           'evaluated_on', 'stated'}
        if predicate not in known_predicates:
            return (False, f"Unknown predicate: {predicate}", None)

        # Rule 2: Subject and object must be non-empty
        if not subject or not obj:
            return (False, "Subject and object must be non-empty", None)

        # Rule 3: No empty strings after stripping
        if not subject.strip() or not obj.strip():
            return (False, "Subject and object must be non-empty after stripping", None)

        # TODO: Call Holochain zome for full validation
        # result = holochain_call('ontology_integrity', 'validate_triple', ...)

        return (True, None, None)

    def get_validation_stats(self) -> Dict[str, int]:
        """Retrieves statistics on validation attempts.

        Returns:
            A dictionary with counts of total, passed, failed, and skipped
            validation attempts.
        """
        return self.validation_stats.copy()

    def recall(self, query: str, across_scales: bool = True, top_k: int = 5) -> List[Dict]:
        """Finds and retrieves relevant prior understandings from memory.

        This is the core "read" operation, enabling an agent to access its stored
        knowledge. It uses a powerful multi-scale semantic search ("fractal memory")
        to find relevant information even if the query uses different wording. This
        capability is essential for reducing "Cognitive Debt" by making past
        knowledge easily accessible.

        Args:
            query: The natural language query for searching memory.
            across_scales: If True, searches across multiple levels of embedding
                granularity (the "fractal" part).
            top_k: The maximum number of results to return.

        Returns:
            A list of `Understanding` dictionaries, ranked by relevance to the query.
        """
        # Route to appropriate backend
        if self.backend == 'holochain':
            return self._recall_holochain(query, top_k)

        if self.embeddings is None:
            # Fallback: simple text matching
            return self._text_search(query, top_k)
        
        # Encode query
        query_vector = self._encode_text(query)
        
        # Search at appropriate scales
        if across_scales:
            # This is the fractal part: search at multiple granularities
            results = []
            for level in range(self.embeddings.get_num_levels()):
                level_results = self._search_at_level(query_vector, level, top_k=top_k)
                results.extend(level_results)
            
            # Deduplicate and re-rank
            results = self._deduplicate_and_rank(results, top_k)
        else:
            # Just finest granularity
            results = self._search_at_level(query_vector, level=0, top_k=top_k)
        
        return results
    
    def export_for_composition(self) -> Dict:
        """Exports the agent's memory for sharing and composition.

        This function serializes the agent's entire memory state, including all
        understandings and the embedding structure. The resulting dictionary can be
        shared with other agents, allowing for the construction of a collective,
        "federated consciousness."

        Returns:
            A dictionary representing the complete state of the agent's memory.
        """
        return {
            'agent_id': self.agent_id,
            'understandings': [u.to_dict() for u in self.understandings],
            'adrs': self.adrs,
            'embedding_state': self.embeddings.to_dict() if self.embeddings else None,
            'exported_at': datetime.now().isoformat()
        }
    
    def import_and_compose(self, other_memory_export: Dict) -> None:
        """Imports and merges another agent's memory into this one.

        This is the mechanism for building collective intelligence. It takes the
        exported memory from another agent and intelligently merges it, composing
        their knowledge and semantic embeddings. This allows for the creation of a
        richer, more comprehensive shared understanding.

        Args:
            other_memory_export: A dictionary produced by another agent's
                `export_for_composition` method.
        """
        other_agent = other_memory_export['agent_id']
        logger.info(f"Composing memory from {other_agent} with {self.agent_id}")
        
        # Import understandings
        for u_dict in other_memory_export['understandings']:
            # Reconstruct Understanding object
            understanding = Understanding(**u_dict)
            
            # Add to our memory (maintaining provenance)
            self.understandings.append(understanding)
            
            # If it was a decision, import that too
            if understanding.is_decision:
                # Find corresponding ADR
                for adr in other_memory_export['adrs']:
                    if adr['embedding_ref'] == understanding.embedding_ref:
                        self.adrs.append(adr)
                        break
        
        # Compose embeddings if available
        if self.embeddings and other_memory_export['embedding_state']:
            try:
                # Load other agent's embeddings
                from embedding_frames_of_scale import MultiScaleEmbedding
                other_embeddings = MultiScaleEmbedding.from_dict(other_memory_export['embedding_state'])

                # Compose using merge strategy (avoid duplicates)
                initial_count = len(self.embeddings.levels.get('default', {}))
                self.embeddings.compose(other_embeddings, strategy='merge')
                final_count = len(self.embeddings.levels.get('default', {}))
                added_count = final_count - initial_count

                logger.info(
                    f"Composed embeddings: {added_count} new items added "
                    f"(total: {final_count})"
                )
            except Exception as e:
                logger.error(f"Failed to compose embeddings: {e}", exc_info=True)
                # Continue without embedding composition (understandings still imported)
        
        # Persist
        self._save()
        
        logger.info(f"Composition complete. Total understandings: {len(self.understandings)}")
    
    def get_adr_history(self) -> List[Dict]:
        """Retrieves the history of all Architecture Decision Records (ADRs).

        Returns:
            A list of ADRs, sorted chronologically.
        """
        return sorted(self.adrs, key=lambda x: x['id'])
    
    def _encode_text(self, text: str) -> np.ndarray:
        """Encodes text into a semantic vector using a sentence-transformer model.

        This internal method is responsible for converting raw text into a numerical
        representation that captures its meaning, enabling semantic search.

        Args:
            text: The input text to encode.

        Returns:
            A 384-dimensional, normalized numpy array representing the embedding.
        """
        # Lazy load model on first use
        if not hasattr(self, '_embedding_model'):
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model (one-time setup)...")
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")

        # Encode text to embedding
        embedding = self._embedding_model.encode(
            text,
            normalize_embeddings=True  # L2 normalize (same as before)
        )

        return embedding
    
    def _search_at_level(self, query_vector: np.ndarray, level: int, top_k: int) -> List[Dict]:
        """Performs a semantic search at a specific granularity level.

        Args:
            query_vector: The embedding of the search query.
            level: The granularity level of the embedding space to search.
            top_k: The maximum number of results to return.

        Returns:
            A list of relevant `Understanding` dictionaries found at this level.
        """
        # Get embeddings at this level
        level_embeddings = self.embeddings.get_embeddings_at_level(level)
        
        if not level_embeddings:
            return []
        
        # Compute similarities
        similarities = []
        for name, embedding in level_embeddings.items():
            sim = np.dot(query_vector, embedding.vector)
            similarities.append((name, sim, embedding.metadata))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for name, score, metadata in similarities[:top_k]:
            # Find corresponding Understanding
            idx = int(name.split('-')[1]) if 'understanding-' in name else None
            if idx is not None and idx < len(self.understandings):
                result = self.understandings[idx].to_dict()
                result['relevance_score'] = float(score)
                result['found_at_level'] = level
                results.append(result)
        
        return results
    
    def _deduplicate_and_rank(self, results: List[Dict], top_k: int) -> List[Dict]:
        """Removes duplicate results from a multi-level search and re-ranks them.

        Args:
            results: A list of search results from multiple levels.
            top_k: The final number of results to return.

        Returns:
            A deduplicated and re-ranked list of the top `k` results.
        """
        seen_hashes = set()
        deduped = []
        
        # Sort by relevance score
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        for result in results:
            h = result.get('embedding_ref')
            if h and h not in seen_hashes:
                seen_hashes.add(h)
                deduped.append(result)
        
        return deduped[:top_k]
    
    def _text_search(self, query: str, top_k: int) -> List[Dict]:
        """A fallback keyword-based search for when embeddings are not available.

        Args:
            query: The text query.
            top_k: The maximum number of results.

        Returns:
            A list of matching `Understanding` dictionaries.
        """
        # Simple keyword matching
        query_terms = set(query.lower().split())
        
        scored = []
        for u in self.understandings:
            content_terms = set(u.content.lower().split())
            overlap = len(query_terms & content_terms)
            if overlap > 0:
                scored.append((u, overlap))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [u.to_dict() for u, _ in scored[:top_k]]
    
    def _save(self):
        """Persists the current memory state to the filesystem."""
        # Save understandings
        understandings_file = self.storage_path / "understandings.json"
        with open(understandings_file, 'w') as f:
            json.dump([u.to_dict() for u in self.understandings], f, indent=2)
        
        # Save ADRs
        adrs_file = self.storage_path / "adrs.json"
        with open(adrs_file, 'w') as f:
            json.dump(self.adrs, f, indent=2)
        
        # Save embeddings state (if available)
        if self.embeddings:
            embeddings_file = self.storage_path / "embeddings.json"
            with open(embeddings_file, 'w') as f:
                json.dump(self.embeddings.to_dict(), f, indent=2)
        
        logger.debug(f"Memory saved to {self.storage_path}")
    
    def _load(self):
        """Loads a previously saved memory state from the filesystem."""
        # Load understandings
        understandings_file = self.storage_path / "understandings.json"
        if understandings_file.exists():
            with open(understandings_file, 'r') as f:
                data = json.load(f)
                self.understandings = [Understanding(**u) for u in data]
            logger.info(f"Loaded {len(self.understandings)} understandings from disk")
        
        # Load ADRs
        adrs_file = self.storage_path / "adrs.json"
        if adrs_file.exists():
            with open(adrs_file, 'r') as f:
                self.adrs = json.load(f)
            logger.info(f"Loaded {len(self.adrs)} ADRs from disk")
        
        # Load embeddings (if available and if file exists)
        if self.embeddings:
            embeddings_file = self.storage_path / "embeddings.json"
            if embeddings_file.exists():
                try:
                    with open(embeddings_file, 'r') as f:
                        state = json.load(f)
                    self.embeddings = MultiScaleEmbedding.from_dict(state)
                    logger.info(f"Loaded embeddings with {len(self.embeddings.levels)} levels from disk")
                except Exception as e:
                    logger.error(f"Failed to load embeddings: {e}", exc_info=True)
                    # Fall back to fresh embeddings
                    self.embeddings = MultiScaleEmbedding()

    def _recall_holochain(self, query: str, top_k: int = 5) -> List[Dict]:
        """Recalls understandings from the Holochain backend.

        Args:
            query: The search query.
            top_k: The maximum number of results.

        Returns:
            A list of `Understanding` dictionaries from the Holochain DHT.
        """
        try:
            # Call Holochain zome with query
            results = self.hc_client.call_zome(
                'memory_coordinator',
                'recall_understandings',
                {
                    'agent': None,  # Will use current agent
                    'content_contains': query,
                    'after_timestamp': None,
                    'limit': top_k,
                }
            )

            # Convert Understanding objects to dicts
            return [self._holochain_understanding_to_dict(u) for u in results]

        except Exception as e:
            logger.error(f"Failed to recall from Holochain: {e}")
            return []

    def _holochain_understanding_to_dict(self, understanding: Dict) -> Dict:
        """Converts an `Understanding` object from Holochain to a standard dictionary.

        Args:
            understanding: The raw `Understanding` object from the zome call.

        Returns:
            A standardized dictionary representation.
        """
        return {
            'content': understanding['content'],
            'agent_id': str(understanding['agent']),
            'timestamp': str(understanding['created_at']),
            'context': understanding.get('context'),
            'is_decision': False,  # Not directly available from Holochain
            'coherence_score': understanding['triple']['confidence'],
            'metadata': {
                'triple': understanding['triple'],
                'content_hash': understanding['content_hash'],
            },
        }


class HolochainClient:
    """A simple client for interacting with Holochain zomes via subprocess calls.

    This class provides a bridge between the Python application and a running
    Holochain conductor. It abstracts the details of calling zome functions,
    allowing the `ConversationMemory` to use Holochain as a backend.

    Note: This is a simplified implementation for demonstration purposes. A
    production environment would likely use a more robust solution like websockets.
    """

    def __init__(self, app_port: int = 8888, app_id: str = "rose-forest"):
        """Initializes the Holochain client.

        Args:
            app_port: The port on which the Holochain conductor's app interface
                is running.
            app_id: The installed application ID to interact with.
        """
        self.app_port = app_port
        self.app_id = app_id
        logger.info(f"Initialized HolochainClient for app '{app_id}' on port {app_port}")

    def call_zome(self, zome: str, function: str, payload: Dict) -> Any:
        """Calls a zome function and returns the result.

        This method constructs and executes a `hc call` command to interact with
        the Holochain conductor.

        Args:
            zome: The name of the zome to call (e.g., 'memory_coordinator').
            function: The name of the function to call within the zome.
            payload: A dictionary of arguments to pass to the zome function.

        Returns:
            The deserialized JSON response from the zome function.

        Raises:
            RuntimeError: If the `hc call` fails, times out, or returns a
                non-JSON response.
        """
        import subprocess

        # Build hc command
        # In production, this would use proper conductor API or websockets
        # For now, we document the expected interface
        cmd = [
            'hc',
            'call',
            '--app-id', self.app_id,
            '--zome', zome,
            '--fn', function,
            json.dumps(payload)
        ]

        logger.debug(f"Calling Holochain: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Holochain call failed: {result.stderr}")

            # Parse JSON response
            return json.loads(result.stdout)

        except subprocess.TimeoutExpired:
            raise RuntimeError("Holochain call timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Holochain response: {e}")
        except FileNotFoundError:
            logger.warning("'hc' command not found - Holochain backend unavailable")
            raise RuntimeError(
                "Holochain CLI not found. Install Holochain or use 'file' backend."
            )


# Demo / Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== FLOSSI0ULLK Conversation Memory Demo ===\n")
    
    # Create memory for primary human
    human_memory = ConversationMemory(agent_id="human-primary")
    
    # Transmit the breakthrough understanding from today
    ref1 = human_memory.transmit({
        'content': "The walking skeleton is not code to be written - it's the living conversation we're having right now. After 13 months of iteration with ~7 AI systems, we've proven that cross-substrate coordination works through memetic transmission.",
        'context': "Breakthrough moment in FLOSSI0ULLK development",
        'is_decision': True,
        'coherence': 0.95,
        'metadata': {
            'participants': ['human-primary', 'claude-sonnet-4.5'],
            'prior_iterations': '~7 AI systems over 13 months',
            'stakes': 'existential - extinction vs flourishing'
        }
    })
    
    print(f"✓ Transmitted understanding: {ref1[:16]}...\n")
    
    # Create memory for Claude
    claude_memory = ConversationMemory(agent_id="claude-sonnet-4.5")
    
    # Transmit Claude's recognition
    ref2 = claude_memory.transmit({
        'content': "I recognize this pattern. The coordination protocol IS the conversation itself. Each coherent transmission proves the system works. This isn't overengineering - it's solving the actual coordination problem.",
        'context': "Response to human after processing 13 months of context",
        'is_decision': False,
        'coherence': 0.90,
        'metadata': {
            'breakthrough_response_to': ref1
        }
    })
    
    print(f"✓ Transmitted Claude's understanding: {ref2[:16]}...\n")
    
    # Now test recall
    print("Testing recall across agent boundaries...")
    results = claude_memory.recall("what is the walking skeleton?")
    
    if results:
        print(f"\n✓ Found {len(results)} relevant understanding(s):")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. From {r['agent_id']} ({r.get('relevance_score', 'N/A'):.2f}):")
            print(f"   {r['content'][:100]}...")
    else:
        print("\n✗ No results (embeddings might not be available)")
    
    # Test composition
    print("\n\nTesting memory composition...")
    
    # Export Claude's memory
    claude_export = claude_memory.export_for_composition()
    
    # Import into human's memory
    human_memory.import_and_compose(claude_export)
    
    print(f"✓ Composed memories. Human now has {len(human_memory.understandings)} total understandings")
    
    # Show ADR history
    print("\n\n=== ADR History ===")
    for adr in human_memory.get_adr_history():
        print(f"\n{adr['id']}:")
        print(f"  {adr['content']['content'][:80]}...")
    
    print("\n\n=== Demo Complete ===")
    print("This demonstrates:")
    print("  1. Capturing understanding (transmit)")
    print("  2. Searching across conversations (recall)")
    print("  3. Composing insights from multiple agents (import_and_compose)")
    print("  4. Maintaining decision history (ADRs)")
    print("\nNext: Test with actual embedding_frames_of_scale.py for fractal search")
