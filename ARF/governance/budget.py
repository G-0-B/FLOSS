"""
Autonomous Budgeting System.
Tracks and limits resource usage (tokens, cost) for agents.
"""
import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

logger = logging.getLogger(__name__)

@dataclass
class BudgetConfig:
    """Configuration for budget limits."""
    max_tokens_per_session: int = 100000
    max_cost_per_session: float = 5.0  # USD
    warning_threshold: float = 0.8

@dataclass
class BudgetState:
    """Current state of budget usage."""
    tokens_used: int = 0
    estimated_cost: float = 0.0
    
    def to_dict(self):
        return asdict(self)

class BudgetExceededError(Exception):
    """Raised when budget limits are exceeded."""
    pass

class BudgetManager:
    """
    Manages resource budget for an agent.
    """
    def __init__(self, agent_id: str, storage_path: Optional[str] = None, config: BudgetConfig = None):
        self.agent_id = agent_id
        self.config = config or BudgetConfig()
        
        if storage_path is None:
            storage_path = f"./memory/{agent_id}"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.state_file = self.storage_path / "budget.json"
        
        self.state = self._load_state()
        logger.info(f"Initialized BudgetManager for {agent_id}. Used: {self.state.tokens_used} tokens.")

    def check_budget(self):
        """
        Checks if the budget allows for further operations.
        Raises BudgetExceededError if limits are reached.
        """
        if self.state.tokens_used >= self.config.max_tokens_per_session:
            raise BudgetExceededError(f"Token limit exceeded: {self.state.tokens_used}/{self.config.max_tokens_per_session}")
        
        if self.state.estimated_cost >= self.config.max_cost_per_session:
            raise BudgetExceededError(f"Cost limit exceeded: ${self.state.estimated_cost}/${self.config.max_cost_per_session}")

        # Check warnings
        token_ratio = self.state.tokens_used / self.config.max_tokens_per_session
        if token_ratio >= self.config.warning_threshold:
            logger.warning(f"Budget warning: {token_ratio*100:.1f}% of token limit used.")

    def record_usage(self, tokens: int, cost: float = 0.0):
        """
        Records resource usage.
        """
        self.state.tokens_used += tokens
        self.state.estimated_cost += cost
        self._save_state()
        logger.debug(f"Recorded usage: +{tokens} tokens. Total: {self.state.tokens_used}")

    def reset(self):
        """Resets the budget state."""
        self.state = BudgetState()
        self._save_state()
        logger.info("Budget reset.")

    def _load_state(self) -> BudgetState:
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return BudgetState(**data)
            except Exception as e:
                logger.error(f"Failed to load budget state: {e}")
        return BudgetState()

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state.to_dict(), f, indent=2)
