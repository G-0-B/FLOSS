"""
Test script for Autonomous Budgeting.
"""
import sys
import shutil
from pathlib import Path
import logging


# Ensure ARF is in path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ARF.governance.budget import BudgetManager, BudgetConfig, BudgetExceededError
from ARF.conversation_memory import ConversationMemory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_DIR = Path("./test_memory_budget")

def setup_module():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir()

def teardown_module():
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)

def test_budget_manager():
    print("\n=== Testing BudgetManager ===")
    config = BudgetConfig(max_tokens_per_session=100)
    manager = BudgetManager("test-agent", storage_path=str(TEST_DIR), config=config)
    
    # Initial check
    manager.check_budget()
    print("✓ Initial check passed")
    
    # Record usage
    manager.record_usage(50)
    assert manager.state.tokens_used == 50
    print("✓ Usage recording passed")
    
    # Check warning (implied by log, but we check state)
    manager.check_budget()
    
    # Exceed budget
    manager.record_usage(60) # Total 110
    assert manager.state.tokens_used == 110
    
    try:
        manager.check_budget()
        assert False, "Should have raised BudgetExceededError"
    except BudgetExceededError as e:
        print(f"✓ Correctly raised error: {e}")

def test_memory_integration():
    print("\n=== Testing ConversationMemory Integration ===")
    # Use a fresh directory for this agent
    agent_dir = TEST_DIR / "memory_agent"
    
    # Initialize memory
    memory = ConversationMemory(agent_id="budget-agent", storage_path=str(agent_dir))
    
    # Configure a tight budget for testing
    memory.budget_manager.config.max_tokens_per_session = 50
    
    # Transmit small content (approx 5 tokens)
    memory.transmit({'content': "Short message."})
    used = memory.budget_manager.state.tokens_used
    print(f"Used after 1st msg: {used}")
    assert used > 0
    
    # Transmit large content to exceed budget
    long_msg = "A" * 400 # ~100 tokens
    try:
        memory.transmit({'content': long_msg})
        # The usage is recorded AFTER transmission, so this one might succeed 
        # if the check happens before. 
        # But the NEXT one should fail.
        print("Transmitted long message (budget exceeded during this op)")
    except BudgetExceededError:
        print("Blocked immediately (unexpected but acceptable)")
        
    # Now budget should be blown
    try:
        memory.transmit({'content': "Another message."})
        assert False, "Should be blocked by budget"
    except BudgetExceededError as e:
        print(f"✓ Correctly blocked by budget: {e}")

if __name__ == "__main__":
    setup_module()
    try:
        test_budget_manager()
        test_memory_integration()
    finally:
        teardown_module()
