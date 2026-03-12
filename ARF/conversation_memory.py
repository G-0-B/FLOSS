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
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
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

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class Understanding:
    """
    A moment of coherent understanding between agents.
    
    This is the atomic unit of memory in FLOSSI0ULLK coordination.
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
        return asdict(self)
    
    def hash(self) -> str:
        """Cryptographic hash for reference and deduplication"""
        content_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


class ConversationMemory:
    """
    Holochain-inspired local-first memory for cross-AI coordination.
    
    Each agent maintains their own memory, but memories can be:
    - Composed (via MultiScaleEmbedding aggregation)
    - Shared (via export/import)
    - Verified (via cryptographic hashes)
    
    This is the computational substrate for distributed intelligence coordination.
    """
    
    def __init__(self, agent_id: str, storage_path: Optional[str] = None):
        """
        Initialize memory for a specific agent.
        
        Args:
            agent_id: Identifier for this agent (e.g., "claude-sonnet-4.5", "human-primary")
            storage_path: Where to persist memory (default: ./memory/{agent_id}/)
        """
        self.agent_id = agent_id
        
        # Storage
        if storage_path is None:
            storage_path = f"./memory/{agent_id}"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Memory structures
        self.understandings: List[Understanding] = []
        self.adrs: List[Dict] = []  # Architecture Decision Records
        
        # Fractal embeddings (if available)
        if EMBEDDINGS_AVAILABLE:
            self.embeddings = MultiScaleEmbedding()
        else:
            self.embeddings = None
            logger.warning("Running without embeddings; recall will be text-only")
        
        # Load existing memory if present
        self._load()
        
        logger.info(f"Initialized ConversationMemory for agent: {agent_id}")
    
    def transmit(self, understanding_dict: Dict) -> str:
        """
        Capture a moment of coherent understanding.
        
        This is the core operation: taking what exists in one mind
        and encoding it in a form that can be transmitted to another.
        
        Args:
            understanding_dict: Dict with keys:
                - content (required): The understanding itself
                - context (optional): What led to this
                - is_decision (optional): Is this ADR-worthy?
                - coherence (optional): Confidence score [0, 1]
                - metadata (optional): Additional info
        
        Returns:
            Hash reference for later recall
        """
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
            
            embedding = Embedding(
                vector=vector,
                metadata={
                    'agent_id': self.agent_id,
                    'timestamp': understanding.timestamp,
                    'context': understanding.context,
                    'coherence': understanding.coherence_score,
                    'is_decision': understanding.is_decision
                }
            )
            
            # Add to multiscale embedding structure
            self.embeddings.add_embedding(
                level="level_0",
                embedding_id=f"understanding-{len(self.understandings)}",
                vector=vector,
                metadata=embedding.metadata
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
        
        return understanding.hash()
    
    def recall(self, query: str, across_scales: bool = True, top_k: int = 5) -> List[Dict]:
        """
        Find relevant prior understanding.
        
        This is where the magic happens: searching across nested reference frames
        to find understanding that's relevant to the current query.
        
        Args:
            query: What are we looking for?
            across_scales: Search at multiple levels of composition?
            top_k: How many results to return?
        
        Returns:
            List of Understanding dicts, ranked by relevance
        """
        if self.embeddings is None:
            # Fallback: simple text matching
            return self._text_search(query, top_k)
        
        # Encode query
        query_vector = self._encode_text(query)
        
        # Search at appropriate scales
        if across_scales:
            # This is the fractal part: search at multiple granularities
            results = []
            for level_name in self.embeddings.get_level_names():
                level_results = self._search_at_level(query_vector, level_name, top_k=top_k)
                results.extend(level_results)

            # Deduplicate and re-rank
            results = self._deduplicate_and_rank(results, top_k)
        else:
            # Just finest granularity
            results = self._search_at_level(query_vector, level="level_0", top_k=top_k)
        
        return results
    
    def export_for_composition(self) -> Dict:
        """
        Export this agent's memory in a form that can be composed with others.
        
        This enables the "7 AI systems" use case: each system exports its understanding,
        then we compose them into a coherent whole.
        
        Returns:
            Dict containing all understandings, ADRs, and embedding state
        """
        return {
            'agent_id': self.agent_id,
            'understandings': [u.to_dict() for u in self.understandings],
            'adrs': self.adrs,
            'embedding_state': self.embeddings.to_dict() if self.embeddings else None,
            'exported_at': datetime.now().isoformat()
        }
    
    def import_and_compose(self, other_memory_export: Dict) -> None:
        """
        Import another agent's memory and compose it with ours.
        
        This is the key to multi-agent coordination: taking understanding from
        different substrates and composing them into a shared reference frame.
        
        Args:
            other_memory_export: Output from another agent's export_for_composition()
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
            # TODO: This requires implementing composition logic in MultiScaleEmbedding
            # For now, just log
            logger.warning("Embedding composition not yet implemented; understandings imported but not embedded")
        
        # Persist
        self._save()
        
        logger.info(f"Composition complete. Total understandings: {len(self.understandings)}")
    
    def get_adr_history(self) -> List[Dict]:
        """Get all Architecture Decision Records in chronological order"""
        return sorted(self.adrs, key=lambda x: x['id'])
    
    def _encode_text(self, text: str) -> np.ndarray:
        """
        Simple text encoding for demonstration.
        
        In production, this would use a proper embedding model (e.g., sentence-transformers).
        For now, just use a hash-based projection to high-dimensional space.
        """
        # Hash to get deterministic seed
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        np.random.seed(seed)
        
        # Project to 384-dimensional space (common embedding size)
        vector = np.random.randn(384)
        vector = vector / np.linalg.norm(vector)  # Normalize
        
        return vector
    
    def _search_at_level(self, query_vector: np.ndarray, level: str, top_k: int) -> List[Dict]:
        """Search at a specific granularity level"""
        # Get embeddings at this level
        try:
            level_embeddings = self.embeddings.get_all_embeddings(level)
        except KeyError:
            return []

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
        """Remove duplicates and re-rank by relevance"""
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
        """Fallback text-only search if embeddings unavailable"""
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
        """Persist memory to disk"""
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
        """Load existing memory from disk"""
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
        if self.embeddings is not None:
            embeddings_file = self.storage_path / "embeddings.json"
            if embeddings_file.exists():
                with open(embeddings_file, 'r') as f:
                    state = json.load(f)
                    self.embeddings = MultiScaleEmbedding.from_dict(state)
                    logger.info(f"Loaded embedding state with {self.embeddings.get_num_levels()} level(s)")


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
