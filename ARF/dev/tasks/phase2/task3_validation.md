# Task 2.3: Integrate Ontology Validation with Conversation Memory

**Phase**: 2 (Foundation)
**Estimated Time**: 5 hours
**Complexity**: MEDIUM
**Dependencies**: Task 2.1 (Base Ontology) MUST complete first
**Parallelizable**: Yes (with Task 2.2 after 2.1 completes)

---

## 🎯 Objective

Integrate the ontology validation layer with `ConversationMemory` to ensure NO data enters the system without passing semantic validation. This enforces the symbolic-first architecture.

---

## 📍 Context

From ACTION_PLAN (Week 1):
> "Add validation to existing vector zome: Before any vector storage, validate symbolic triple. If validation fails, reject."

**Critical Principle**:
> "No embedding can be stored without a valid triple." - SUCCESS CRITERIA #1

This task bridges the symbolic (ontology) and neural (embeddings) layers.

---

## ✅ Acceptance Criteria

1. **Add triple extraction to ConversationMemory**
   - Extract subject-predicate-object from understanding content
   - Use simple heuristics or pattern matching (no LLM required for now)
   - Fall back to default types if extraction fails

2. **Validate before storing**
   - Call ontology validation before adding to memory
   - Reject invalid understandings with clear error message
   - Log validation failures

3. **Update transmit() method**
   - Extract triple from understanding
   - Validate triple against ontology
   - Only store if validation passes
   - Return validation result to caller

4. **Add validation bypass for bootstrap**
   - Optional `skip_validation` parameter for initial data loading
   - Default: validation enabled
   - Log when validation skipped

5. **Tests**
   - Valid understanding accepted
   - Invalid understanding rejected
   - Validation error messages clear
   - Bypass works when needed
   - Coverage ≥80%

6. **Metrics**
   - Track validation pass/fail rate
   - Log rejected understandings for analysis

---

## 🔧 Implementation Guidance

### Step 1: Add Triple Extraction

Update `ARF/conversation_memory.py`:

```python
from typing import Optional, Dict, Any, Tuple

class ConversationMemory:
    # ... existing code ...

    def _extract_triple(self, understanding: Dict[str, Any]) -> Optional[Tuple[str, str, str]]:
        """
        Extract a (subject, predicate, object) triple from understanding content.

        Uses simple heuristics to identify semantic structure. For production,
        this could use LLM-based extraction with committee validation.

        Args:
            understanding: The understanding dict to extract from

        Returns:
            (subject, predicate, object) tuple, or None if extraction fails

        Examples:
            >>> memory._extract_triple({'content': 'Claude Sonnet 4.5 improves upon Sonnet 4'})
            ('Claude-Sonnet-4.5', 'improves_upon', 'Sonnet-4')

            >>> memory._extract_triple({'content': 'GPT-4 is a large language model'})
            ('GPT-4', 'is_a', 'LLM')
        """
        content = understanding.get('content', '')

        if not content:
            return None

        # Simple pattern matching for common structures
        # Pattern 1: "X is a Y"
        import re
        is_a_pattern = r'(\w+(?:-\w+)*)\s+is\s+an?\s+(\w+(?:\s+\w+)*)'
        match = re.search(is_a_pattern, content, re.IGNORECASE)
        if match:
            subject = match.group(1).replace(' ', '-')
            obj = match.group(2).replace(' ', '-')
            return (subject, 'is_a', obj)

        # Pattern 2: "X improves Y" or "X improves upon Y"
        improves_pattern = r'(\w+(?:-\w+)*)\s+improves(?:\s+upon)?\s+(\w+(?:-\w+)*)'
        match = re.search(improves_pattern, content, re.IGNORECASE)
        if match:
            return (match.group(1), 'improves_upon', match.group(2))

        # Pattern 3: "X can do Y" / "X is capable of Y"
        capable_pattern = r'(\w+(?:-\w+)*)\s+(?:can|is capable of)\s+(\w+)'
        match = re.search(capable_pattern, content, re.IGNORECASE)
        if match:
            return (match.group(1), 'capable_of', match.group(2))

        # Default: treat as entity with generic relation
        # Subject = agent_id, predicate = stated, object = content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return (self.agent_id, 'stated', f"understanding_{content_hash}")
```

### Step 2: Add Ontology Validation Integration

```python
import subprocess
import json

class ConversationMemory:
    # ... existing code ...

    def __init__(self, agent_id: str, storage_path: Optional[Path] = None,
                 validate_ontology: bool = True):
        """
        Initialize conversation memory.

        Args:
            agent_id: Unique identifier for this agent
            storage_path: Where to persist memory (default: ~/.flossi0ullk/{agent_id})
            validate_ontology: Whether to validate against ontology (default: True)
        """
        self.agent_id = agent_id
        self.validate_ontology = validate_ontology
        # ... rest of init ...

    def _validate_triple(self, triple: Tuple[str, str, str]) -> Tuple[bool, Optional[str]]:
        """
        Validate a triple against the ontology.

        Args:
            triple: (subject, predicate, object) tuple

        Returns:
            (is_valid, error_message) tuple
        """
        if not self.validate_ontology:
            return (True, None)

        subject, predicate, obj = triple

        # For now, use simple validation rules
        # In production, this would call Holochain ontology zome

        # Rule 1: Predicate must be known
        known_predicates = {'is_a', 'part_of', 'improves_upon', 'capable_of',
                           'trained_on', 'evaluated_on', 'stated'}
        if predicate not in known_predicates:
            return (False, f"Unknown predicate: {predicate}")

        # Rule 2: Subject and object must be non-empty
        if not subject or not obj:
            return (False, "Subject and object must be non-empty")

        # Rule 3: Confidence checks would go here

        # TODO: Call Holochain zome for full validation
        # result = holochain_call('ontology_integrity', 'validate_triple', ...)

        return (True, None)
```

### Step 3: Update transmit() Method

```python
def transmit(self, understanding: Dict[str, Any], skip_validation: bool = False) -> Optional[UnderstandingRef]:
    """
    Transmit an understanding across conversation boundaries.

    The understanding must pass ontology validation before being stored.

    Args:
        understanding: Dict with 'content' and optional 'context'
        skip_validation: Skip ontology validation (use with caution)

    Returns:
        UnderstandingRef if stored successfully, None if validation failed

    Raises:
        ValueError: If understanding is malformed
    """
    if 'content' not in understanding:
        raise ValueError("Understanding must have 'content' field")

    # Extract triple
    triple = self._extract_triple(understanding)
    if triple is None:
        logger.warning(f"Could not extract triple from understanding: {understanding}")
        if not skip_validation:
            logger.error("Validation required but triple extraction failed")
            return None

    # Validate triple
    if not skip_validation and triple:
        is_valid, error_msg = self._validate_triple(triple)
        if not is_valid:
            logger.error(f"Ontology validation failed: {error_msg}")
            logger.error(f"Triple: {triple}")
            logger.error(f"Understanding: {understanding}")
            return None
        else:
            logger.debug(f"Validation passed for triple: {triple}")

    # Store understanding (existing code)
    ref = UnderstandingRef(
        timestamp=time.time(),
        content_hash=hashlib.sha256(
            json.dumps(understanding, sort_keys=True).encode()
        ).hexdigest(),
        agent_id=self.agent_id
    )

    # Add to understandings
    self.understandings.append({
        'ref': ref,
        'understanding': understanding,
        'triple': triple,  # Store extracted triple
    })

    # Embed if embeddings enabled
    if self.embeddings:
        content_text = str(understanding.get('content', ''))
        embedding = self._encode_text(content_text)
        self.embeddings.add(ref.content_hash, embedding)

    # Persist
    self._save()

    logger.info(f"Transmitted understanding with triple: {triple}")
    return ref
```

### Step 4: Add Validation Metrics

```python
class ConversationMemory:
    def __init__(self, ...):
        # ... existing init ...
        self.validation_stats = {
            'total_attempts': 0,
            'validation_passed': 0,
            'validation_failed': 0,
            'validation_skipped': 0,
        }

    def transmit(self, understanding, skip_validation=False):
        self.validation_stats['total_attempts'] += 1

        if skip_validation:
            self.validation_stats['validation_skipped'] += 1
        else:
            # ... validation logic ...
            if is_valid:
                self.validation_stats['validation_passed'] += 1
            else:
                self.validation_stats['validation_failed'] += 1
                return None

        # ... rest of transmit ...

    def get_validation_stats(self) -> Dict[str, int]:
        """Get validation statistics."""
        return self.validation_stats.copy()
```

---

## 🧪 Testing Checklist

### Test 1: Valid Understanding Accepted
```python
def test_transmit_valid_understanding(memory):
    understanding = {
        'content': 'Claude Sonnet 4.5 improves upon Sonnet 4'
    }

    ref = memory.transmit(understanding)

    assert ref is not None
    assert memory.validation_stats['validation_passed'] == 1
    assert memory.validation_stats['validation_failed'] == 0
```

### Test 2: Invalid Understanding Rejected
```python
def test_transmit_invalid_understanding(memory):
    understanding = {
        'content': 'X unknown_predicate Y'
    }

    ref = memory.transmit(understanding)

    assert ref is None  # Should be rejected
    assert memory.validation_stats['validation_failed'] == 1
```

### Test 3: Validation Bypass Works
```python
def test_validation_bypass(memory):
    understanding = {
        'content': 'Invalid content with bad structure'
    }

    # Should fail normally
    ref1 = memory.transmit(understanding, skip_validation=False)
    assert ref1 is None

    # Should succeed with bypass
    ref2 = memory.transmit(understanding, skip_validation=True)
    assert ref2 is not None
    assert memory.validation_stats['validation_skipped'] == 1
```

### Test 4: Triple Extraction
```python
def test_extract_triple_is_a():
    memory = ConversationMemory(agent_id="test")

    triple = memory._extract_triple({'content': 'GPT-4 is a large language model'})

    assert triple == ('GPT-4', 'is_a', 'large-language-model')
```

### Test 5: Statistics Tracking
```python
def test_validation_statistics(memory):
    # 2 valid, 1 invalid, 1 skipped
    memory.transmit({'content': 'A is a B'})
    memory.transmit({'content': 'C improves D'})
    memory.transmit({'content': 'X invalid Y'})
    memory.transmit({'content': 'anything'}, skip_validation=True)

    stats = memory.get_validation_stats()

    assert stats['total_attempts'] == 4
    assert stats['validation_passed'] == 2
    assert stats['validation_failed'] == 1
    assert stats['validation_skipped'] == 1
```

---

## 📝 Completion Checklist

- [ ] Triple extraction implemented
- [ ] Ontology validation integrated
- [ ] transmit() updated with validation
- [ ] Validation bypass parameter added
- [ ] Validation statistics tracked
- [ ] Error messages clear and helpful
- [ ] All tests pass
- [ ] Invalid understandings are rejected
- [ ] Valid understandings are accepted
- [ ] Coverage ≥80%
- [ ] Completion report created

---

## 🚫 Out of Scope

- ❌ LLM-based triple extraction (use simple patterns)
- ❌ Full Holochain integration (stub for now)
- ❌ Committee validation (single validator for now)
- ❌ Natural language query parsing
- ❌ SPARQL or complex queries

---

## 📋 Files to Modify

- `ARF/conversation_memory.py` - Add validation integration
- `ARF/tests/test_conversation_memory.py` - Add validation tests
- `ARF/dev/completion/phase2_task3.md` - Completion report

---

## 🎓 Success Metrics

1. ✅ **Zero invalid data enters system** - validation catches bad triples
2. ✅ Statistics show validation is working
3. ✅ Error messages help debug why validation failed
4. ✅ Performance impact minimal (<10ms per validation)
5. ✅ Ready for Phase 3 integration

---

**Wait for Task 2.1 to complete before starting! Can run in parallel with Task 2.2! 🚀**
