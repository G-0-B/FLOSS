"""
Adaptive Parameter Selection for RSA Algorithm.

Automatically selects optimal N, K, T parameters based on query complexity.

Phase 4.1: Performance Optimization
"""

import re
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RSAParams:
    """A data class for storing the parameters of the RSA algorithm.

    Attributes:
        N: The number of pony agents in the swarm.
        K: The aggregation size (how many responses to sample).
        T: The number of refinement iterations.
    """
    N: int  # Number of ponies
    K: int  # Aggregation size
    T: int  # Number of iterations

    def __str__(self):
        """Provides a string representation of the parameters."""
        return f"RSAParams(N={self.N}, K={self.K}, T={self.T})"


class ComplexityEstimator:
    """Estimates the complexity of a user query to inform parameter selection.

    This class uses a set of heuristics to analyze a query and assign it a
    complexity score. This score is then used to select the most appropriate
    (and resource-efficient) parameters for the RSA algorithm. This process
    contributes to "Cognitive Liberation" by avoiding unnecessary computation
    for simple queries, while dedicating more resources to complex ones.

    Heuristics include:
    - Query length and structure.
    - Presence of keywords indicating mathematical, reasoning, or creative tasks.
    """

    # Keyword patterns for different complexity levels
    MATH_KEYWORDS = [
        'calculate', 'compute', 'multiply', 'divide', 'add', 'subtract',
        'sum', 'difference', 'product', 'quotient', 'equals', 'solve',
        r'\d+\s*[+\-*/]\s*\d+',  # Basic arithmetic expressions
        r'\b\d+\b',  # Numbers
    ]

    REASONING_KEYWORDS = [
        'explain', 'why', 'how', 'because', 'therefore', 'thus',
        'compare', 'contrast', 'analyze', 'evaluate', 'justify',
        'reason', 'logic', 'argument', 'conclusion', 'premise',
        'if', 'then', 'when', 'would', 'should', 'could'
    ]

    CREATIVE_KEYWORDS = [
        'write', 'create', 'design', 'imagine', 'story', 'narrative',
        'poem', 'essay', 'article', 'describe', 'invent', 'compose',
        'generate', 'brainstorm', 'explore', 'multiple approaches',
        'various ways', 'different methods', 'consider all'
    ]

    def __init__(self):
        """Initializes the ComplexityEstimator."""
        self.compiled_patterns = {
            'math': [re.compile(p, re.IGNORECASE) for p in self.MATH_KEYWORDS],
            'reasoning': [re.compile(p, re.IGNORECASE) for p in self.REASONING_KEYWORDS],
            'creative': [re.compile(p, re.IGNORECASE) for p in self.CREATIVE_KEYWORDS],
        }

    def estimate_complexity(self, query: str) -> float:
        """Estimates the complexity of a query on a scale from 0 to 100.

        The scoring is based on a combination of query length, sentence
        structure, and the presence of keywords that suggest different types
        of cognitive tasks.

        Args:
            query: The user's query string.

        Returns:
            A float representing the estimated complexity score (0-100).
        """
        score = 0.0

        # Base complexity from length
        char_count = len(query)
        word_count = len(query.split())
        sentence_count = len(re.split(r'[.!?]+', query))

        # Length-based scoring
        if char_count < 50:
            score += 5
        elif char_count < 150:
            score += 20
        elif char_count < 300:
            score += 40
        else:
            score += 60

        # Word count
        if word_count < 10:
            score += 0
        elif word_count < 25:
            score += 10
        elif word_count < 50:
            score += 20
        else:
            score += 30

        # Sentence structure
        if sentence_count > 3:
            score += 15  # Multiple sentences suggest complexity

        # Keyword matching
        math_matches = sum(
            1 for pattern in self.compiled_patterns['math']
            if pattern.search(query)
        )
        reasoning_matches = sum(
            1 for pattern in self.compiled_patterns['reasoning']
            if pattern.search(query)
        )
        creative_matches = sum(
            1 for pattern in self.compiled_patterns['creative']
            if pattern.search(query)
        )

        # Math keywords reduce complexity (well-defined problems)
        if math_matches > 0:
            score -= 10

        # Reasoning keywords increase complexity
        if reasoning_matches > 2:
            score += 15
        elif reasoning_matches > 0:
            score += 5

        # Creative keywords significantly increase complexity
        if creative_matches > 2:
            score += 30
        elif creative_matches > 0:
            score += 15

        # Clamp to 0-100 range
        score = max(0, min(100, score))

        logger.debug(
            f"Complexity estimation: score={score:.1f}, "
            f"chars={char_count}, words={word_count}, sentences={sentence_count}, "
            f"math={math_matches}, reasoning={reasoning_matches}, creative={creative_matches}"
        )

        return score


class AdaptiveParameterSelector:
    """Selects optimal RSA parameters based on estimated query complexity.

    This class acts as a meta-controller for the RSA algorithm, dynamically
    adjusting its parameters (N, K, T) to match the difficulty of the task at
    hand. This ensures that the swarm operates efficiently, dedicating more
    computational resources to complex problems and fewer to simple ones.
    This adaptive capability is a key feature of the "Evolution" principle,
    allowing the system to intelligently allocate its resources.
    """

    # Default parameter configurations for different complexity levels
    # These can be updated based on parameter sweep results
    DEFAULT_CONFIGS = {
        'simple': RSAParams(N=2, K=1, T=2),      # Fast, minimal overhead
        'medium': RSAParams(N=4, K=2, T=3),      # Balanced (original default)
        'complex': RSAParams(N=6, K=3, T=4),     # High quality, slower
    }

    def __init__(
        self,
        configs: Optional[Dict[str, RSAParams]] = None,
        complexity_thresholds: Optional[Dict[str, float]] = None
    ):
        """Initializes the AdaptiveParameterSelector.

        Args:
            configs: An optional dictionary to override the default parameter
                configurations for each complexity level.
            complexity_thresholds: An optional dictionary to override the default
                thresholds for classifying a query as 'simple', 'medium', or
                'complex'.
        """
        self.estimator = ComplexityEstimator()

        # Use custom configs or defaults
        self.configs = configs or self.DEFAULT_CONFIGS.copy()

        # Complexity thresholds
        self.thresholds = complexity_thresholds or {
            'simple': 20.0,   # complexity < 20: simple
            'medium': 60.0,   # 20 <= complexity < 60: medium
            # complexity >= 60: complex
        }

        logger.info(f"Initialized AdaptiveParameterSelector with configs: {self.configs}")

    def select_parameters(self, query: str) -> RSAParams:
        """Selects the optimal RSA parameters for a given query.

        This method first estimates the query's complexity and then selects the
        pre-configured set of parameters that best matches that complexity level.

        Args:
            query: The user's query string.

        Returns:
            An `RSAParams` object containing the selected N, K, and T values.
        """
        # Estimate complexity
        complexity = self.estimator.estimate_complexity(query)

        # Select configuration based on thresholds
        if complexity < self.thresholds['simple']:
            config_level = 'simple'
        elif complexity < self.thresholds['medium']:
            config_level = 'medium'
        else:
            config_level = 'complex'

        params = self.configs[config_level]

        logger.info(
            f"Selected {config_level} config for query (complexity={complexity:.1f}): {params}"
        )

        return params

    def update_config(self, level: str, params: RSAParams):
        """Updates the parameter configuration for a specific complexity level.

        This allows for the dynamic tuning of the selector, for example, based on
        the results of automated parameter sweeps.

        Args:
            level: The complexity level to update ('simple', 'medium', or 'complex').
            params: The new `RSAParams` to use for this level.
        """
        if level not in self.configs:
            raise ValueError(f"Unknown complexity level: {level}")

        old_params = self.configs[level]
        self.configs[level] = params

        logger.info(f"Updated {level} config: {old_params} -> {params}")

    def get_config_summary(self) -> Dict[str, Any]:
        """Retrieves a summary of the current parameter configurations and thresholds.

        Returns:
            A dictionary summarizing the selector's current settings.
        """
        return {
            'configs': {
                level: {'N': p.N, 'K': p.K, 'T': p.T}
                for level, p in self.configs.items()
            },
            'thresholds': self.thresholds
        }


# Singleton instance for easy access
_default_selector = None


def get_default_selector() -> AdaptiveParameterSelector:
    """Gets the default, singleton instance of the AdaptiveParameterSelector.

    Returns:
        The singleton `AdaptiveParameterSelector` instance.
    """
    global _default_selector
    if _default_selector is None:
        _default_selector = AdaptiveParameterSelector()
    return _default_selector


def select_parameters_for_query(query: str) -> RSAParams:
    """A convenience function to select RSA parameters for a query.

    This function uses the default singleton selector to estimate the query's
    complexity and return the appropriate parameters.

    Args:
        query: The user's query string.

    Returns:
        An `RSAParams` object with the selected N, K, and T values.
    """
    selector = get_default_selector()
    return selector.select_parameters(query)


# Example usage and testing
if __name__ == "__main__":
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test queries
    test_queries = [
        "What is 47 * 89?",
        "Explain the concept of recursion using a simple analogy.",
        "Write a short story about a robot learning to appreciate art. Consider multiple narrative approaches and explore the themes of consciousness and creativity.",
        "Calculate 256 + 384",
        "Compare and contrast Python and JavaScript in terms of syntax, performance, and use cases.",
        "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How much does the ball cost?",
    ]

    selector = AdaptiveParameterSelector()

    print("\n" + "="*80)
    print("ADAPTIVE PARAMETER SELECTION - TEST")
    print("="*80)

    for query in test_queries:
        print(f"\nQuery: {query[:70]}...")
        params = selector.select_parameters(query)
        complexity = selector.estimator.estimate_complexity(query)
        print(f"Complexity: {complexity:.1f}/100")
        print(f"Selected: {params}")

    print("\n" + "="*80)
