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
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
import logging
import numpy as np

from ARF.ontology.predicates import (
    IS_A, IMPROVES_UPON, CAPABLE_OF, STATED, VALID_PREDICATES
)

# Import the existing fractal embedding infrastructure
try:
    from embedding_frames_of_scale import Embedding, MultiScaleEmbedding
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logging.warning("embedding_frames_of_scale not found; will use mock embeddings")

# Import committee validation system
try:
    from ARF.validation.committee import TripleValidationCommittee
    from ARF.validation.agent_pool import ValidatorPool
    COMMITTEE_VALIDATION_AVAILABLE = True
except ImportError:
    COMMITTEE_VALIDATION_AVAILABLE = False
    logging.warning("Committee validation not available; using basic validation only")

# Import Pattern Matcher
try:
    from ARF.ontology.patterns import PatternMatcher
    PATTERNS_AVAILABLE = True
except ImportError:
    PATTERNS_AVAILABLE = False
    logging.warning("PatternMatcher not available")

# Import Budget Manager
try:
    from ARF.governance.budget import BudgetManager, BudgetExceededError
    BUDGET_AVAILABLE = True
except ImportError:
    BUDGET_AVAILABLE = False
    logging.warning("BudgetManager not available")

logger = logging.getLogger(__name__)

@dataclass
class Understanding:
    """A moment of coherent understanding, representing an atomic unit of memory."""
    content: str
    agent_id: str
    timestamp: str
    context: Optional[str] = None
    is_decision: bool = False
    coherence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding_ref: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Return this Understanding as a plain dict (via dataclasses.asdict)."""
        return asdict(self)

    def to_hash_dict(self) -> Dict:
        """Return the stable identity payload used for provenance hashes."""
        payload = self.to_dict()
        payload.pop('embedding_ref', None)
        return payload

    def hash(self) -> str:
        content_str = json.dumps(self.to_hash_dict(), sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()


class ConversationMemory:
    """A local-first, verifiable memory substrate for multi-agent coordination."""

    def __init__(self, agent_id: str, storage_path: Optional[str] = None,
                 validate_ontology: bool = True, backend: str = 'file',
                 use_committee_validation: bool = False, committee_use_mock: bool = True):
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
        self.adrs: List[Dict] = []

        # Validation statistics
        self.validation_stats = {
            'total_attempts': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'validation_skipped': 0,
        }

        # Initialize committee validation
        self.committee = None
        if use_committee_validation:
            if COMMITTEE_VALIDATION_AVAILABLE:
                self.committee = TripleValidationCommittee(use_mock=committee_use_mock)
                logger.info("Initialized committee validation")
            else:
                logger.warning("Committee validation requested but not available.")
                self.use_committee_validation = False

        # Fractal embeddings
        if EMBEDDINGS_AVAILABLE:
            self.embeddings = MultiScaleEmbedding()
        else:
            self.embeddings = None
            logger.warning("Running without embeddings; recall will be text-only")

        # Load existing memory
        if backend == 'file':
            self._load()

        # Initialize Pattern Matcher
        if PATTERNS_AVAILABLE:
            self.pattern_matcher = PatternMatcher()
        else:
            self.pattern_matcher = None

        # Initialize Budget Manager
        if BUDGET_AVAILABLE:
            self.budget_manager = BudgetManager(agent_id, storage_path=str(self.storage_path))
        else:
            self.budget_manager = None

        # Load triple patterns
        self.patterns = {}
        try:
            config_path = Path(__file__).parent / "config" / "triple_patterns.yaml"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    self.patterns = config.get('patterns', {})
                    logger.info(f"Loaded {len(self.patterns)} triple extraction patterns")
            else:
                logger.warning(f"Pattern config not found at {config_path}, using defaults")
        except Exception as e:
            logger.error(f"Failed to load pattern config: {e}")

        logger.info(f"Initialized ConversationMemory for agent: {agent_id} (backend: {backend})")
    
    def transmit(self, understanding_dict: Dict, skip_validation: bool = False) -> Optional[str]:
        if self.backend == 'holochain':
            return self._transmit_holochain(understanding_dict, skip_validation)
        else:
            return self._transmit_file(understanding_dict, skip_validation)

    def _prepare_understanding_for_storage(
        self, understanding_dict: Dict[str, Any], skip_validation: bool = False
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[str, str, str]], Optional[str]]:
        """Normalize understanding metadata and preflight validation before persistence."""
        prepared = dict(understanding_dict)
        metadata = dict(prepared.get('metadata', {}))
        prepared['metadata'] = metadata

        triple = self._extract_triple(prepared)
        if triple is None:
            logger.warning(f"Could not extract triple from understanding: {understanding_dict}")
            if not skip_validation:
                logger.error("Validation required but triple extraction failed")
                self.validation_stats['validation_failed'] += 1
                return None, None, None

        validation_mode = 'skipped' if skip_validation else 'passed'
        if skip_validation:
            if triple:
                logger.info(f"Skipping validation for triple: {triple}")
        elif triple:
            raw_content = prepared.get('content', '')
            provided_context = prepared.get('context', '')
            full_context = f"Content: {raw_content}\nContext: {provided_context}"

            is_valid, error_msg, committee_result = self._validate_triple(triple, full_context)
            if not is_valid:
                logger.error(f"Ontology validation failed: {error_msg}")
                self.validation_stats['validation_failed'] += 1
                return None, None, None

            logger.debug(f"Validation passed for triple: {triple}")
            if committee_result:
                metadata['committee_validation'] = committee_result

        if self.pattern_matcher:
            full_text = f"{prepared.get('content', '')} {prepared.get('context', '')}"
            detected_patterns = self.pattern_matcher.match(full_text)
            if detected_patterns:
                metadata['patterns'] = detected_patterns
                logger.info(f"Detected patterns: {[p['pattern'] for p in detected_patterns]}")

        return prepared, triple, validation_mode

    def _record_validation_outcome(self, validation_mode: Optional[str]) -> None:
        """Update validation counters after a successful persistence operation."""
        if validation_mode == 'passed':
            self.validation_stats['validation_passed'] += 1
        elif validation_mode == 'skipped':
            self.validation_stats['validation_skipped'] += 1

    def _build_holochain_payload(self, understanding_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Return the subset of understanding fields supported by the Holochain zome API."""
        payload = {
            'content': understanding_dict['content'],
            'context': understanding_dict.get('context'),
            'perspectives': understanding_dict.get('perspectives'),
            'semantic_context': understanding_dict.get('semantic_context'),
            'language_address': understanding_dict.get('language_address'),
        }
        return {key: value for key, value in payload.items() if value is not None}

    def _transmit_holochain(self, understanding_dict: Dict, skip_validation: bool = False) -> Optional[str]:
        if self.budget_manager:
            self.budget_manager.check_budget()

        self.validation_stats['total_attempts'] += 1

        if 'content' not in understanding_dict:
            raise ValueError("Understanding must have 'content' field")

        prepared_understanding, triple, validation_mode = self._prepare_understanding_for_storage(
            understanding_dict, skip_validation
        )
        if prepared_understanding is None:
            return None

        try:
            result = self.hc_client.call_zome(
                'memory_coordinator',
                'transmit_understanding',
                self._build_holochain_payload(prepared_understanding)
            )
            logger.info(f"Transmitted understanding to Holochain with triple: {triple}")
            self._record_validation_outcome(validation_mode)
            
            # Record usage (approximate)
            if self.budget_manager:
                tokens = len(prepared_understanding['content']) // 4
                self.budget_manager.record_usage(tokens)
                
            return result
        except Exception as e:
            logger.error(f"Failed to transmit to Holochain: {e}")
            self.validation_stats['validation_failed'] += 1
            return None

    def _transmit_file(self, understanding_dict: Dict, skip_validation: bool = False) -> Optional[str]:
        if self.budget_manager:
            self.budget_manager.check_budget()

        self.validation_stats['total_attempts'] += 1

        if 'content' not in understanding_dict:
            raise ValueError("Understanding must have 'content' field")

        prepared_understanding, triple, validation_mode = self._prepare_understanding_for_storage(
            understanding_dict, skip_validation
        )
        if prepared_understanding is None:
            return None

        understanding = Understanding(
            content=prepared_understanding['content'],
            agent_id=self.agent_id,
            timestamp=datetime.now().isoformat(),
            context=prepared_understanding.get('context'),
            is_decision=prepared_understanding.get('is_decision', False),
            coherence_score=prepared_understanding.get('coherence', 0.0),
            metadata=prepared_understanding.get('metadata', {})
        )

        if self.embeddings is not None:
            vector = self._encode_text(understanding.content)
            metadata = {
                'agent_id': self.agent_id,
                'timestamp': understanding.timestamp,
                'context': understanding.context,
                'coherence': understanding.coherence_score,
                'is_decision': understanding.is_decision,
                'triple': triple
            }
            self.embeddings.add(
                key=f"understanding-{len(self.understandings)}",
                vector=vector,
                level='default',
                metadata=metadata
            )
            understanding.embedding_ref = understanding.hash()

        self.understandings.append(understanding)

        if understanding.is_decision:
            adr = {
                'id': f"ADR-{len(self.adrs)}",
                'content': understanding.to_dict(),
                'embedding_ref': understanding.embedding_ref
            }
            self.adrs.append(adr)
            logger.info(f"Recorded decision: {adr['id']}")

        self._save()
        logger.info(f"Transmitted understanding with triple: {triple}")
        self._record_validation_outcome(validation_mode)
        
        # Record usage (approximate)
        if self.budget_manager:
            tokens = len(understanding.content) // 4
            self.budget_manager.record_usage(tokens)
            
        return understanding.hash()

    def _extract_triple(self, understanding_dict: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
        content = understanding_dict.get('content', '')
        if not content:
            return None

        if self.patterns:
            for name, pattern in self.patterns.items():
                regex = pattern.get('regex')
                predicate = pattern.get('predicate')
                
                if regex and predicate:
                    match = re.search(regex, content, re.IGNORECASE)
                    if match:
                        if len(match.groups()) >= 2:
                            subject = match.group(1).strip()
                            obj = match.group(2).strip()
                            
                            if predicate == IS_A:
                                obj = obj.replace(' ', '-')
                                
                            return (subject, predicate, obj)

        # Fallback patterns use non-overlapping token classes to avoid regex backtracking.
        subject_pattern = r'([^\s-]+(?:-[^\s-]+)*)'
        hyphenated_word_pattern = r'[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)*'

        is_a_pattern = rf'{subject_pattern}\s+is\s+an?\s+({hyphenated_word_pattern}(?:\s+{hyphenated_word_pattern})*)(?:\s*$|[.,;!?])'
        match = re.search(is_a_pattern, content, re.IGNORECASE)
        if match:
            subject = match.group(1).strip()
            obj = match.group(2).strip().replace(' ', '-')
            return (subject, IS_A, obj)

        improves_pattern = rf'{subject_pattern}\s+improves(?:\s+upon)?\s+{subject_pattern}'
        match = re.search(improves_pattern, content, re.IGNORECASE)
        if match:
            return (match.group(1).strip(), IMPROVES_UPON, match.group(2).strip())

        capable_pattern = rf'{subject_pattern}\s+(?:can|is capable of)\s+([A-Za-z0-9_]+)'
        match = re.search(capable_pattern, content, re.IGNORECASE)
        if match:
            return (match.group(1).strip(), CAPABLE_OF, match.group(2).strip())

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return (self.agent_id, STATED, f"understanding_sha256:{content_hash}")

    def _validate_triple(self, triple: Tuple[str, str, str], context: str = "") -> Tuple[bool, Optional[str], Optional[Dict]]:
        if not self.validate_ontology:
            return (True, None, None)

        subject, predicate, obj = triple

        if self.use_committee_validation and self.committee is not None:
            try:
                # robustly handle async execution from sync context
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    # We are already in an event loop. 
                    # Ideally we should await, but this is a sync method.
                    # We can't easily block here without nesting loops (which is bad).
                    # For now, we'll log a warning and fallback to basic validation
                    # or try to schedule it (but we need the result now).
                    logger.warning("Cannot run sync committee validation inside an existing event loop. Falling back to basic validation.")
                    raise RuntimeError("Existing event loop detected")
                else:
                    # No running loop, safe to use asyncio.run
                    result = asyncio.run(
                        self.committee.validate(triple, context or "No context provided")
                    )

                committee_metadata = result.to_dict()

                if result.accepted:
                    logger.info(f"Committee accepted triple: {result.yes_votes}/{result.total_votes}")
                    return (True, None, committee_metadata)
                else:
                    logger.warning(f"Committee rejected triple: {result.yes_votes}/{result.total_votes}")
                    return (False, "Committee validation rejected triple", committee_metadata)

            except Exception as e:
                logger.error(f"Committee validation error: {e}")
                logger.warning("Falling back to basic validation")

        # Basic validation
        if predicate not in VALID_PREDICATES:
            return (False, f"Unknown predicate: {predicate}", None)

        if not subject or not obj:
            return (False, "Subject and object must be non-empty", None)

        if not subject.strip() or not obj.strip():
            return (False, "Subject and object must be non-empty after stripping", None)

        return (True, None, None)

    def get_validation_stats(self) -> Dict[str, int]:
        return self.validation_stats.copy()

    def recall(self, query: str, across_scales: bool = True, top_k: int = 5) -> List[Dict]:
        if self.backend == 'holochain':
            return self._recall_holochain(query, top_k)

        if self.embeddings is None:
            return self._text_search(query, top_k)
        
        query_vector = self._encode_text(query)
        
        if across_scales:
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
        return {
            'agent_id': self.agent_id,
            'understandings': [u.to_dict() for u in self.understandings],
            'adrs': self.adrs,
            'embedding_state': self.embeddings.to_dict() if self.embeddings else None,
            'exported_at': datetime.now().isoformat()
        }
    
    def import_and_compose(self, other_memory_export: Dict) -> None:
        other_agent = other_memory_export['agent_id']
        logger.info(f"Composing memory from {other_agent} with {self.agent_id}")
        
        for u_dict in other_memory_export['understandings']:
            understanding = Understanding(**u_dict)
            self.understandings.append(understanding)
            
            if understanding.is_decision:
                for adr in other_memory_export['adrs']:
                    if adr['embedding_ref'] == understanding.embedding_ref:
                        self.adrs.append(adr)
                        break
        
        if self.embeddings and other_memory_export['embedding_state']:
            try:
                from embedding_frames_of_scale import MultiScaleEmbedding
                other_embeddings = MultiScaleEmbedding.from_dict(other_memory_export['embedding_state'])
                self.embeddings.compose(other_embeddings, strategy='merge')
            except Exception as e:
                logger.error(f"Failed to compose embeddings: {e}", exc_info=True)
        
        self._save()
        logger.info(f"Composition complete. Total understandings: {len(self.understandings)}")
    
    def get_adr_history(self) -> List[Dict]:
        return sorted(self.adrs, key=lambda x: x['id'])
    
    def _encode_text(self, text: str) -> np.ndarray:
        if not hasattr(self, '_embedding_model'):
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformers model (one-time setup)...")
            self._embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")

        embedding = self._embedding_model.encode(text, normalize_embeddings=True)
        return embedding
    
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
            idx = int(name.split('-')[1]) if 'understanding-' in name else None
            if idx is not None and idx < len(self.understandings):
                result = self.understandings[idx].to_dict()
                result['relevance_score'] = float(score)
                result['found_at_level'] = level
                results.append(result)
        return results
    
    def _deduplicate_and_rank(self, results: List[Dict], top_k: int) -> List[Dict]:
        seen_hashes = set()
        deduped = []
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        for result in results:
            h = result.get('embedding_ref')
            if h and h not in seen_hashes:
                seen_hashes.add(h)
                deduped.append(result)
        return deduped[:top_k]
    
    def _text_search(self, query: str, top_k: int) -> List[Dict]:
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
        understandings_file = self.storage_path / "understandings.json"
        with open(understandings_file, 'w') as f:
            json.dump([u.to_dict() for u in self.understandings], f, indent=2)
        
        adrs_file = self.storage_path / "adrs.json"
        with open(adrs_file, 'w') as f:
            json.dump(self.adrs, f, indent=2)
        
        if self.embeddings:
            embeddings_file = self.storage_path / "embeddings.json"
            with open(embeddings_file, 'w') as f:
                json.dump(self.embeddings.to_dict(), f, indent=2)
        logger.debug(f"Memory saved to {self.storage_path}")
    
    def _load(self):
        understandings_file = self.storage_path / "understandings.json"
        if understandings_file.exists():
            with open(understandings_file, 'r') as f:
                data = json.load(f)
                self.understandings = [Understanding(**u) for u in data]
            logger.info(f"Loaded {len(self.understandings)} understandings from disk")
        
        adrs_file = self.storage_path / "adrs.json"
        if adrs_file.exists():
            with open(adrs_file, 'r') as f:
                self.adrs = json.load(f)
            logger.info(f"Loaded {len(self.adrs)} ADRs from disk")
        
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
                    self.embeddings = MultiScaleEmbedding()

    def _recall_holochain(self, query: str, top_k: int = 5) -> List[Dict]:
        try:
            results = self.hc_client.call_zome(
                'memory_coordinator',
                'recall_understandings',
                {
                    'agent': None,
                    'content_contains': query,
                    'after_timestamp': None,
                    'limit': top_k,
                }
            )
            return [self._holochain_understanding_to_dict(u) for u in results]
        except Exception as e:
            logger.error(f"Failed to recall from Holochain: {e}")
            return []

    def _holochain_understanding_to_dict(self, understanding: Dict) -> Dict:
        metadata = dict(understanding.get('metadata', {}))
        metadata.update({
            'triple': understanding['triple'],
            'content_hash': understanding['content_hash'],
        })
        for key in ('perspectives', 'semantic_context', 'language_address'):
            if understanding.get(key) is not None:
                metadata[key] = understanding.get(key)

        return {
            'content': understanding['content'],
            'agent_id': str(understanding.get('agent', understanding.get('agent_id', self.agent_id))),
            'timestamp': str(understanding.get('created_at', understanding.get('timestamp', ''))),
            'context': understanding.get('context'),
            'is_decision': bool(understanding.get('is_decision', metadata.get('is_decision', False))),
            'coherence_score': understanding.get(
                'coherence_score',
                understanding.get('coherence', understanding['triple']['confidence'])
            ),
            'metadata': metadata,
            'embedding_ref': understanding.get('embedding_ref'),
        }


class HolochainClient:
    """A simple client for interacting with Holochain zomes."""

    def __init__(self, app_port: int = 8888, app_id: str = "rose-forest"):
        self.app_port = app_port
        self.app_id = app_id
        logger.info(f"Initialized HolochainClient for app '{app_id}' on port {app_port}")

    def call_zome(self, zome: str, function: str, payload: Dict) -> Any:
        import subprocess
        cmd = [
            'hc', 'call',
            '--app-id', self.app_id,
            '--zome', zome,
            '--fn', function,
            json.dumps(payload)
        ]
        logger.debug(f"Calling Holochain: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Holochain call failed: {result.stderr}")
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Holochain call timed out")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse Holochain response: {e}")
        except FileNotFoundError:
            logger.warning("'hc' command not found - Holochain backend unavailable")
            raise RuntimeError("Holochain CLI not found.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== FLOSSI0ULLK Conversation Memory Demo ===\n")
    human_memory = ConversationMemory(agent_id="human-primary")
    ref1 = human_memory.transmit({
        'content': "The walking skeleton is not code to be written - it's the living conversation we're having right now.",
        'context': "Breakthrough moment",
        'is_decision': True,
        'coherence': 0.95
    })
    print(f"✓ Transmitted understanding: {ref1[:16]}...\n")
