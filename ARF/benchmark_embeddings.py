"""
Performance benchmark for sentence-transformers embeddings.

This script tests the encoding speed of the new embedding implementation.
"""

import sys
import time
from pathlib import Path

import numpy as np

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def run_benchmark():
    """Benchmark model load time, encode speed, and basic semantic similarity.

    This keeps the local embedding path honest about latency and obvious
    semantic regressions.
    """
    from conversation_memory import ConversationMemory

    print("=== Embedding Performance Benchmark ===\n")

    # Initialize memory
    print("Initializing ConversationMemory...")
    memory = ConversationMemory(
        agent_id="benchmark-test", storage_path="./benchmark_temp"
    )

    # Test texts of varying lengths
    texts = [
        "Short text",
        "This is a medium length text for testing",
        " ".join(["Sample text"] * 10),  # ~20 words
        " ".join(["Sample text"] * 50),  # ~100 words
        " ".join(["Sample text"] * 100),  # ~200 words
    ]

    print(f"Testing with {len(texts)} texts of varying lengths...\n")

    # First encoding (includes model loading time)
    print("First encoding (includes model loading time):")
    start = time.perf_counter()
    first_emb = memory._encode_text(texts[0])
    first_time = time.perf_counter() - start
    print(f"  Time: {first_time:.3f}s")
    print(f"  Shape: {first_emb.shape}")
    print(f"  Normalized: {np.abs(np.linalg.norm(first_emb) - 1.0) < 1e-6}\n")

    # Subsequent encodings
    print("Subsequent encodings (model cached):")
    times = []
    for i, text in enumerate(texts[1:], 1):
        start = time.perf_counter()
        memory._encode_text(text)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"  Text {i} ({len(text.split())} words): {elapsed*1000:.2f}ms")

    avg_time = sum(times) / len(times)
    print(f"\nAverage encoding time (excluding first): {avg_time*1000:.2f}ms")

    # Check performance requirement
    if avg_time < 0.1:
        print(f"✓ Performance requirement MET (<100ms): {avg_time*1000:.2f}ms")
    else:
        print(f"✗ Performance requirement MISSED (>100ms): {avg_time*1000:.2f}ms")

    # Test semantic similarity
    print("\n=== Semantic Similarity Test ===")
    dog_emb = memory._encode_text("dog")
    puppy_emb = memory._encode_text("puppy")
    car_emb = memory._encode_text("car")

    dog_puppy_sim = np.dot(dog_emb, puppy_emb)
    dog_car_sim = np.dot(dog_emb, car_emb)

    print(f"Dog <-> Puppy similarity: {dog_puppy_sim:.4f}")
    print(f"Dog <-> Car similarity: {dog_car_sim:.4f}")

    if dog_puppy_sim > dog_car_sim:
        print("✓ Semantic similarity working correctly")
    else:
        print("✗ Semantic similarity not working as expected")

    # Cleanup
    import shutil

    if Path("./benchmark_temp").exists():
        shutil.rmtree("./benchmark_temp")

    print("\n=== Benchmark Complete ===")


if __name__ == "__main__":
    run_benchmark()
