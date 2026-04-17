import time
import threading
import sys
import os

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metacoordinator.context_sync import ContextSyncEngine


def test_concurrent_updates():
    """Test 10 agents updating context simultaneously"""
    print("\n--- Testing Concurrent Updates ---")
    engine = ContextSyncEngine()

    # Register 10 agents
    agents = [f"agent_{i}" for i in range(10)]
    for agent_id in agents:
        engine.register_agent(agent_id, ["reasoning", "knowledge"])

    # Concurrent updates to same key
    def update_worker(agent_id):
        for i in range(100):
            engine.broadcast_update(
                key="shared_counter", value=i, source_agent=agent_id
            )

    threads = [threading.Thread(target=update_worker, args=(a,)) for a in agents]

    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    duration = time.time() - start

    print(f"✅ 1000 concurrent updates completed in {duration:.2f}s")
    assert duration < 5.0, "Performance degradation detected"


def test_high_frequency_updates():
    """Test rapid updates from single agent"""
    print("\n--- Testing High Frequency Updates ---")
    engine = ContextSyncEngine()
    engine.register_agent("speed_test", ["benchmark"])

    start = time.time()
    for i in range(1000):
        engine.broadcast_update(f"key_{i}", i, "speed_test")
    duration = time.time() - start

    print(f"✅ 1000 sequential updates in {duration:.2f}s")
    assert duration < 2.0, "Latency too high"


def test_large_context():
    """Test with large context payloads"""
    print("\n--- Testing Large Context Payloads ---")
    engine = ContextSyncEngine()
    engine.register_agent("large_data", ["storage"])

    # 1MB payload
    large_value = "x" * (1024 * 1024)

    start = time.time()
    engine.broadcast_update("large_key", large_value, "large_data")
    duration = time.time() - start

    print(f"✅ 1MB payload broadcast in {duration:.2f}s")
    assert duration < 1.0, "Large payload handling too slow"


if __name__ == "__main__":
    try:
        test_concurrent_updates()
        test_high_frequency_updates()
        test_large_context()
        print("\n🎉 All stress tests passed!")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
