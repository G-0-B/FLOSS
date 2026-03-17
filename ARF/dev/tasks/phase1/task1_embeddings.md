# Task 1.1: Replace Mock Embeddings with Real Sentence Transformers

**Phase**: 1 (Quick Wins)
**Estimated Time**: 4 hours
**Complexity**: LOW
**Dependencies**: None
**Parallelizable**: Yes

---

## 🎯 Objective

Replace the hash-based mock embedding implementation in `ConversationMemory._encode_text()` with real semantic embeddings using the `sentence-transformers` library.

---

## 📍 Context

Currently, `conversation_memory.py` uses a simple hash-based projection to generate "embeddings" for testing purposes. This works for basic functionality but doesn't provide semantic search capability. Real embeddings will enable meaningful similarity-based recall.

**Current Implementation** (lines 298-320 in `ARF/conversation_memory.py`):
```python
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
    embedding = np.random.randn(384)

    # Normalize to unit length (common in semantic embeddings)
    embedding = embedding / np.linalg.norm(embedding)

    return embedding
```

---

## ✅ Acceptance Criteria

1. **Install sentence-transformers dependency**
   - Add `sentence-transformers>=2.2.0` to a requirements file or document installation
   - Verify it installs cleanly

2. **Replace _encode_text() implementation**
   - Use `SentenceTransformer('all-MiniLM-L6-v2')` model (384-dim embeddings)
   - Maintain same return type: `np.ndarray`
   - Preserve dimension: 384
   - Preserve normalization: L2-normalized vectors

3. **Add model caching**
   - Load model once, reuse across calls
   - Store as class attribute to avoid repeated downloads

4. **Maintain backward compatibility**
   - Keep method signature identical
   - All existing tests must still pass
   - No changes to public API

5. **Performance requirements**
   - Encoding time: <100ms per text (reasonable for sentence-transformers)
   - First call may be slower due to model loading - acceptable

6. **Tests**
   - Update existing tests if they check exact embedding values
   - Add new test verifying semantic similarity (e.g., "dog" and "puppy" should be similar)
   - Ensure coverage ≥80%

---

## 🔧 Implementation Guidance

### Step 1: Install Dependency

Add to `requirements.txt` (or create if doesn't exist):
```txt
sentence-transformers>=2.2.0
torch>=2.0.0  # Required by sentence-transformers
```

Test installation:
```bash
pip install sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; print('OK')"
```

### Step 2: Update _encode_text()

Replace the mock implementation with:

```python
def _encode_text(self, text: str) -> np.ndarray:
    """
    Encode text using sentence-transformers for semantic embeddings.

    Args:
        text: Input text to encode

    Returns:
        384-dimensional normalized embedding vector
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
```

### Step 3: Update Tests

**If tests check exact values** (they shouldn't for embeddings, but if they do):
```python
# OLD TEST (too specific)
def test_encode_deterministic():
    embedding1 = memory._encode_text("test")
    embedding2 = memory._encode_text("test")
    assert np.array_equal(embedding1, embedding2)  # May fail with sentence-transformers

# NEW TEST (check properties, not exact values)
def test_encode_deterministic():
    embedding1 = memory._encode_text("test")
    embedding2 = memory._encode_text("test")
    # Embeddings should be VERY similar (cosine sim ~1.0)
    similarity = np.dot(embedding1, embedding2)
    assert similarity > 0.99  # Allow tiny floating point differences
```

**Add semantic similarity test**:
```python
def test_semantic_similarity():
    """Test that semantically similar words have similar embeddings."""
    dog_emb = memory._encode_text("dog")
    puppy_emb = memory._encode_text("puppy")
    car_emb = memory._encode_text("car")

    # Dog and puppy should be similar
    dog_puppy_sim = np.dot(dog_emb, puppy_emb)
    assert dog_puppy_sim > 0.5  # Reasonably similar

    # Dog and car should be less similar
    dog_car_sim = np.dot(dog_emb, car_emb)
    assert dog_car_sim < dog_puppy_sim
```

### Step 4: Verify Dimension Consistency

```python
def test_embedding_dimensions():
    """Ensure embeddings maintain 384 dimensions."""
    texts = ["short", "a longer piece of text", ""]
    for text in texts:
        embedding = memory._encode_text(text)
        assert embedding.shape == (384,), f"Expected 384-dim, got {embedding.shape}"
        assert np.abs(np.linalg.norm(embedding) - 1.0) < 1e-6, "Embedding not normalized"
```

---

## 🧪 Testing Checklist

Run these commands to verify:

```bash
# Install dependencies
pip install sentence-transformers

# Run tests
cd /home/user/FLOSS/ARF
pytest tests/ -v -k "memory or embed" --cov=conversation_memory

# Should see:
# - All existing tests pass
# - New semantic similarity test passes
# - Coverage ≥ 80%
```

**Manual verification**:
```python
from conversation_memory import ConversationMemory

memory = ConversationMemory(agent_id="test")

# Test embedding
emb = memory._encode_text("The quick brown fox")
print(f"Embedding shape: {emb.shape}")  # (384,)
print(f"Normalized: {np.linalg.norm(emb)}")  # ~1.0

# Test semantic search
memory.transmit({"content": "Dogs are loyal pets"})
memory.transmit({"content": "Cars have four wheels"})
memory.transmit({"content": "Puppies are adorable"})

results = memory.recall("canine animals")
# Should retrieve dog/puppy related content
print(results)
```

---

## 📊 Performance Benchmarks

Run and report these:

```python
import time

# Benchmark encoding speed
texts = ["Sample text" * i for i in range(1, 11)]
times = []

for text in texts:
    start = time.perf_counter()
    memory._encode_text(text)
    elapsed = time.perf_counter() - start
    times.append(elapsed)

avg_time = sum(times) / len(times)
print(f"Average encoding time: {avg_time*1000:.2f}ms")

# Should be <100ms per text
assert avg_time < 0.1, f"Encoding too slow: {avg_time}s"
```

---

## 🚫 Out of Scope

Do NOT do these (save for later tasks):
- ❌ Changing embedding dimensions
- ❌ Using a different model (stick with all-MiniLM-L6-v2)
- ❌ Optimizing model loading time
- ❌ Adding GPU support
- ❌ Batch encoding optimization
- ❌ Modifying MultiScaleEmbedding class

---

## 📝 Completion Checklist

Before reporting done:
- [ ] `sentence-transformers` installed and working
- [ ] `_encode_text()` uses SentenceTransformer model
- [ ] Model is cached (loaded once)
- [ ] All existing tests pass
- [ ] New semantic similarity test added and passes
- [ ] Embedding dimensions verified (384)
- [ ] Embeddings are L2 normalized
- [ ] Performance benchmark run (<100ms average)
- [ ] No changes to public API
- [ ] Code follows style guide
- [ ] Completion report created

---

## 🐛 Troubleshooting

**Issue: torch installation fails**
```bash
# Use CPU-only version if needed
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**Issue: Model download fails**
```bash
# Pre-download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Issue: Tests fail with "embedding not deterministic"**
- Update tests to check similarity (>0.99) instead of exact equality
- sentence-transformers may have minor numerical variations

**Issue: Performance too slow**
- First call is slow (model loading) - this is expected
- Subsequent calls should be fast
- Profile with: `python -m cProfile -s cumtime script.py`

---

## 📋 Files to Modify

- `ARF/conversation_memory.py` - Update `_encode_text()` method
- `requirements.txt` - Add sentence-transformers dependency
- `ARF/tests/test_conversation_memory.py` - Update/add tests
- `ARF/dev/completion/phase1_task1.md` - Create completion report

---

## 🎓 Success Metrics

Task is successful when:
1. ✅ Semantic search actually works (similar texts cluster together)
2. ✅ All tests pass including new semantic similarity test
3. ✅ Performance is acceptable (<100ms per encoding)
4. ✅ No breaking changes to existing functionality
5. ✅ Code quality maintained (types, docs, style)

---

**Ready to implement? Follow the base_prompt.md workflow and get started! 🚀**
