# Task 1.3: Implement Composition Logic in MultiScaleEmbedding

**Phase**: 1 (Quick Wins)
**Estimated Time**: 6 hours
**Complexity**: MEDIUM
**Dependencies**: None (but benefits from Task 1.2 completing)
**Parallelizable**: Yes

---

## 🎯 Objective

Implement embedding composition logic to merge embeddings from multiple `MultiScaleEmbedding` instances while preserving semantic coherence. This enables multi-agent memory composition as specified in ADR-0.

---

## 📍 Context

The `ConversationMemory.import_and_compose()` method needs to merge embeddings from multiple agents. Currently there's a TODO (line 285):

```python
if self.embeddings and other_memory_export['embedding_state']:
    # TODO: This requires implementing composition logic in MultiScaleEmbedding
    logger.warning("Embedding composition not yet implemented; understandings imported but not embedded")
```

**Use Case** (from ADR-0):
When multiple AI agents (Claude, GPT, human) each have their own memory, they should be able to compose their understandings into a collective intelligence while preserving provenance and avoiding duplication.

---

## ✅ Acceptance Criteria

1. **Implement compose() method in MultiScaleEmbedding**
   - Signature: `def compose(self, other: 'MultiScaleEmbedding', strategy: str = 'merge') -> None`
   - Merges embeddings from `other` into `self`
   - Handles duplicate keys intelligently
   - Preserves semantic integrity

2. **Support multiple composition strategies**
   - `'merge'`: Add new items, skip duplicates (default)
   - `'average'`: Average embeddings for duplicate keys
   - `'append'`: Keep both under different keys (e.g., "key", "key_2")

3. **Handle dimension mismatches**
   - Raise clear error if dimensions don't match
   - Don't allow composition of incompatible embeddings

4. **Update ConversationMemory to use it**
   - Remove TODO at line 285
   - Actually compose embeddings during import_and_compose()
   - Log composition statistics

5. **Tests**
   - Test merge strategy (no duplicates)
   - Test average strategy (duplicate handling)
   - Test append strategy (preserve all data)
   - Test dimension mismatch error
   - Test empty embeddings composition
   - Test composition is commutative/associative where expected
   - Coverage ≥80%

6. **Documentation**
   - Docstring explaining each strategy
   - Examples for each use case
   - Type hints

---

## 🔧 Implementation Guidance

### Step 1: Design Composition Semantics

**Key Questions:**
1. What does it mean to "compose" embeddings?
   - We're building collective intelligence from multiple agents
   - Each agent has embedded their understandings
   - We want to search across all understandings

2. How to handle duplicates?
   - **Problem**: Two agents might embed the same concept
   - **Solution**: Detect via cosine similarity, then decide:
     - Merge: Keep first, ignore second (assume identical)
     - Average: Blend both perspectives (consensus)
     - Append: Keep both (preserve diverse perspectives)

3. What's the return value?
   - Modify `self` in-place (like dict.update())
   - Return self for chaining

### Step 2: Implement compose() Method

Add to `MultiScaleEmbedding` class in `ARF/embedding_frames_of_scale.py`:

```python
def compose(
    self,
    other: 'MultiScaleEmbedding',
    strategy: str = 'merge',
    similarity_threshold: float = 0.95
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

    if self.dimension != other.dimension:
        raise ValueError(
            f"Dimension mismatch: self has {self.dimension}, other has {other.dimension}"
        )

    valid_strategies = ['merge', 'average', 'append']
    if strategy not in valid_strategies:
        raise ValueError(f"Invalid strategy '{strategy}'. Must be one of {valid_strategies}")

    # Execute strategy
    if strategy == 'merge':
        self._compose_merge(other, similarity_threshold)
    elif strategy == 'average':
        self._compose_average(other, similarity_threshold)
    elif strategy == 'append':
        self._compose_append(other)

    return self

def _compose_merge(self, other: 'MultiScaleEmbedding', threshold: float) -> None:
    """Merge strategy: add new items, skip duplicates."""
    for key, embedding in other.items():
        # Check if we already have a similar embedding
        is_duplicate = False
        for existing_key, existing_emb in self.items():
            similarity = np.dot(embedding, existing_emb)
            if similarity > threshold:
                logger.debug(f"Skipping '{key}' (duplicate of '{existing_key}', sim={similarity:.3f})")
                is_duplicate = True
                break

        if not is_duplicate:
            # Add with original key (may overwrite exact key match)
            self.add(key, embedding)
            logger.debug(f"Added '{key}' from composition")

def _compose_average(self, other: 'MultiScaleEmbedding', threshold: float) -> None:
    """Average strategy: blend embeddings for duplicates."""
    for key, embedding in other.items():
        # Find most similar existing embedding
        best_match = None
        best_similarity = 0.0

        for existing_key, existing_emb in self.items():
            similarity = np.dot(embedding, existing_emb)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = existing_key

        if best_match and best_similarity > threshold:
            # Average with best match
            existing_emb = self.get(best_match)
            averaged = (existing_emb + embedding) / 2
            # Renormalize
            averaged = averaged / np.linalg.norm(averaged)
            self.add(best_match, averaged)
            logger.debug(f"Averaged '{key}' with '{best_match}' (sim={best_similarity:.3f})")
        else:
            # Add as new item
            self.add(key, embedding)
            logger.debug(f"Added '{key}' (no match found)")

def _compose_append(self, other: 'MultiScaleEmbedding') -> None:
    """Append strategy: keep all items with unique keys."""
    for key, embedding in other.items():
        # Ensure unique key
        unique_key = key
        counter = 2
        while unique_key in self:
            unique_key = f"{key}_{counter}"
            counter += 1

        self.add(unique_key, embedding)
        if unique_key != key:
            logger.debug(f"Added '{key}' as '{unique_key}' (key conflict)")
```

### Step 3: Update ConversationMemory

In `ARF/conversation_memory.py`, update the import_and_compose() method (around line 285):

```python
# BEFORE:
if self.embeddings and other_memory_export['embedding_state']:
    # TODO: This requires implementing composition logic in MultiScaleEmbedding
    logger.warning("Embedding composition not yet implemented; understandings imported but not embedded")

# AFTER:
if self.embeddings and other_memory_export['embedding_state']:
    try:
        # Load other agent's embeddings
        from embedding_frames_of_scale import MultiScaleEmbedding
        other_embeddings = MultiScaleEmbedding.from_dict(other_memory_export['embedding_state'])

        # Compose using merge strategy (avoid duplicates)
        initial_count = len(self.embeddings)
        self.embeddings.compose(other_embeddings, strategy='merge')
        added_count = len(self.embeddings) - initial_count

        logger.info(
            f"Composed embeddings: {added_count} new items added "
            f"(total: {len(self.embeddings)})"
        )
    except Exception as e:
        logger.error(f"Failed to compose embeddings: {e}", exc_info=True)
        # Continue without embedding composition (understandings still imported)
```

---

## 🧪 Testing Checklist

### Test 1: Merge Strategy (No Duplicates)
```python
def test_compose_merge_no_duplicates():
    """Test merge strategy with completely different embeddings."""
    # ARRANGE
    emb1 = MultiScaleEmbedding()
    emb1.add("concept_a", np.random.randn(384))

    emb2 = MultiScaleEmbedding()
    emb2.add("concept_b", np.random.randn(384))

    # ACT
    emb1.compose(emb2, strategy='merge')

    # ASSERT
    assert len(emb1) == 2
    assert "concept_a" in emb1
    assert "concept_b" in emb1
```

### Test 2: Merge Strategy (With Duplicates)
```python
def test_compose_merge_with_duplicates():
    """Test merge strategy skips near-duplicate embeddings."""
    # ARRANGE
    shared_embedding = np.random.randn(384)
    shared_embedding = shared_embedding / np.linalg.norm(shared_embedding)

    emb1 = MultiScaleEmbedding()
    emb1.add("concept", shared_embedding)

    emb2 = MultiScaleEmbedding()
    # Add very similar embedding (should be detected as duplicate)
    similar = shared_embedding + np.random.randn(384) * 0.01
    similar = similar / np.linalg.norm(similar)
    emb2.add("same_concept", similar)

    # ACT
    emb1.compose(emb2, strategy='merge', similarity_threshold=0.95)

    # ASSERT
    # Should still be 1 (duplicate was skipped)
    assert len(emb1) == 1
```

### Test 3: Average Strategy
```python
def test_compose_average():
    """Test average strategy blends similar embeddings."""
    # ARRANGE
    emb_a = np.array([1.0, 0.0, 0.0])
    emb_b = np.array([0.0, 1.0, 0.0])

    emb1 = MultiScaleEmbedding(dimension=3)
    emb1.add("concept", emb_a)

    emb2 = MultiScaleEmbedding(dimension=3)
    emb2.add("concept", emb_b)

    # ACT
    emb1.compose(emb2, strategy='average', similarity_threshold=0.0)

    # ASSERT
    result = emb1.get("concept")
    # Should be average of [1,0,0] and [0,1,0], then normalized
    expected = np.array([1.0, 1.0, 0.0])
    expected = expected / np.linalg.norm(expected)
    assert np.allclose(result, expected)
```

### Test 4: Append Strategy
```python
def test_compose_append():
    """Test append strategy keeps all items."""
    # ARRANGE
    emb1 = MultiScaleEmbedding()
    emb1.add("concept", np.random.randn(384))

    emb2 = MultiScaleEmbedding()
    emb2.add("concept", np.random.randn(384))  # Same key, different embedding

    # ACT
    emb1.compose(emb2, strategy='append')

    # ASSERT
    assert len(emb1) == 2  # Both kept
    assert "concept" in emb1
    assert "concept_2" in emb1  # Second one renamed
```

### Test 5: Dimension Mismatch
```python
def test_compose_dimension_mismatch():
    """Test that dimension mismatch raises error."""
    emb1 = MultiScaleEmbedding(dimension=128)
    emb2 = MultiScaleEmbedding(dimension=384)

    with pytest.raises(ValueError, match="Dimension mismatch"):
        emb1.compose(emb2)
```

### Test 6: ConversationMemory Integration
```python
def test_conversation_memory_composition():
    """Test that ConversationMemory.import_and_compose() uses embedding composition."""
    # ARRANGE
    memory1 = ConversationMemory(agent_id="agent1")
    memory1.transmit({"content": "Understanding from agent 1"})

    memory2 = ConversationMemory(agent_id="agent2")
    memory2.transmit({"content": "Understanding from agent 2"})

    # ACT
    export = memory2.export_for_composition()
    initial_emb_count = len(memory1.embeddings)
    memory1.import_and_compose(export)

    # ASSERT
    # Should have composed embeddings
    assert len(memory1.embeddings) > initial_emb_count
    # Should have both understandings
    assert len(memory1.understandings) == 2
```

---

## 📊 Performance Benchmarks

```python
def benchmark_composition():
    """Measure composition performance."""
    # Create large embeddings
    emb1 = MultiScaleEmbedding()
    for i in range(500):
        emb1.add(f"concept_{i}", np.random.randn(384))

    emb2 = MultiScaleEmbedding()
    for i in range(500):
        emb2.add(f"concept_{i+250}", np.random.randn(384))  # 250 overlap

    # Benchmark merge
    import time
    start = time.perf_counter()
    emb1.compose(emb2, strategy='merge')
    elapsed = time.perf_counter() - start

    print(f"Composed 500+500 embeddings in {elapsed*1000:.2f}ms")
    # Should be <5 seconds (O(n*m) similarity checks are expensive)
    assert elapsed < 5.0
```

---

## 🚫 Out of Scope

Do NOT do these:
- ❌ Implement hierarchical composition
- ❌ Add conflict resolution UI
- ❌ Optimize similarity search (use brute force for now)
- ❌ Add composition versioning
- ❌ Support partial composition
- ❌ Add undo/rollback
- ❌ GPU acceleration

---

## 📝 Completion Checklist

Before reporting done:
- [ ] `compose()` method implemented
- [ ] Three strategies work correctly (merge, average, append)
- [ ] Dimension mismatch detected and raises error
- [ ] ConversationMemory updated to use composition
- [ ] TODO comment removed
- [ ] Warning about "not yet implemented" removed
- [ ] All tests pass
- [ ] Composition tests cover all strategies
- [ ] Edge cases tested (empty, duplicates, etc.)
- [ ] Coverage ≥80%
- [ ] Type hints complete
- [ ] Docstrings with examples
- [ ] Performance acceptable (<5s for 1000 embeddings)
- [ ] Completion report created

---

## 🐛 Troubleshooting

**Issue: Composition too slow**
- Profile to find bottleneck
- Likely: O(n²) similarity checks
- Optimization (future): Use approximate nearest neighbor (FAISS, Annoy)
- For now: Document performance characteristics

**Issue: Averaging changes semantic meaning**
- This is expected - averaging is lossy
- Document when to use each strategy:
  - Merge: When you trust both agents equally
  - Average: When you want consensus
  - Append: When you want all perspectives preserved

**Issue: Duplicate detection misses near-duplicates**
- Adjust similarity_threshold (default 0.95)
- Lower threshold = more aggressive deduplication
- Higher threshold = preserve more items

**Issue: Composition not commutative**
- This is expected for 'merge' strategy (first wins)
- Document the behavior
- Use 'average' if commutativity is required

---

## 📋 Files to Modify

- `ARF/embedding_frames_of_scale.py` - Add compose() and helper methods
- `ARF/conversation_memory.py` - Use compose() in import_and_compose()
- `ARF/tests/test_embedding_frames.py` - Add composition tests
- `ARF/tests/test_conversation_memory.py` - Add integration tests
- `ARF/dev/completion/phase1_task3.md` - Create completion report

---

## 🎓 Success Metrics

Task is successful when:
1. ✅ Multi-agent composition works end-to-end
2. ✅ All three strategies implemented and tested
3. ✅ No duplicate embeddings with merge strategy
4. ✅ ConversationMemory composes correctly
5. ✅ Performance acceptable for typical use (<1000 embeddings)
6. ✅ Clear documentation of strategy trade-offs

---

**Ready to implement? Follow the base_prompt.md workflow and get started! 🚀**
