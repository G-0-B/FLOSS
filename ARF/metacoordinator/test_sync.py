import time
import sys
import os

# Add the parent directory to sys.path to import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metacoordinator.context_sync import ContextSyncEngine


def test_basic_sync():
    print("\n--- Testing Basic Synchronization ---")
    engine = ContextSyncEngine()

    # 1. Register Agents
    print("Registering agents...")
    agent_a = engine.register_agent("Agent_A")
    agent_b = engine.register_agent("Agent_B")

    # 2. Agent A updates context
    print("\nAgent A updates 'project_status'...")
    engine.broadcast_update("project_status", "Phase 1 Complete", "Agent_A")

    # 3. Verify Agent B received it
    val_b = agent_b.read_context("project_status")
    print(f"Agent B sees 'project_status': {val_b['value'] if val_b else 'None'}")

    assert val_b is not None
    assert val_b["value"] == "Phase 1 Complete"
    assert val_b["source"] == "Agent_A"
    print("SUCCESS: Agent B received update from Agent A.")


def test_late_joiner():
    print("\n--- Testing Late Joiner ---")
    engine = ContextSyncEngine()

    # Agent A starts and sets context
    agent_a = engine.register_agent("Agent_A")
    engine.broadcast_update("global_config", {"mode": "strict"}, "Agent_A")

    # Agent C joins later
    print("Agent C joining late...")
    agent_c = engine.register_agent("Agent_C")

    # Verify Agent C gets existing context
    val_c = agent_c.read_context("global_config")
    print(f"Agent C sees 'global_config': {val_c['value'] if val_c else 'None'}")

    assert val_c is not None
    assert val_c["value"] == {"mode": "strict"}
    print("SUCCESS: Late joining Agent C received existing context.")


def test_conflict_resolution():
    print("\n--- Testing Conflict Resolution (Simulation) ---")
    engine = ContextSyncEngine()

    # We manually simulate a conflict by creating two updates with close timestamps
    # In the engine.broadcast_update, it's serial, so we test the logic function directly.

    update_1 = {
        "value": "Value 1",
        "source": "Agent_A",
        "timestamp": 1000,
        "version": 1,
    }

    update_2 = {
        "value": "Value 2",
        "source": "Agent_B",
        "timestamp": 1001,  # Later timestamp
        "version": 1,
    }

    winner = engine.resolve_conflicts("test_key", [update_1, update_2])
    print(f"Conflict between t=1000 and t=1001. Winner source: {winner['source']}")

    assert winner["source"] == "Agent_B"
    print("SUCCESS: Last-Write-Wins resolved correctly.")


if __name__ == "__main__":
    try:
        test_basic_sync()
        test_late_joiner()
        test_conflict_resolution()
        print("\nALL TESTS PASSED.")
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
