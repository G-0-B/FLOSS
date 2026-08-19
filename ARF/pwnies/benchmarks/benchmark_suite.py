"""
Benchmark Suite for Pony Swarm Performance Testing.

Implements three complexity tiers:
- Micro: Simple arithmetic (baseline)
- Medium: Reasoning and logic
- Large: Creative and complex tasks

Phase 4.1: Performance Optimization
"""

import asyncio
from importlib import import_module
import time
import logging
import statistics
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
if __package__ in {None, ""}:
    PonySwarm = import_module("desktop_pony_swarm.core.swarm").PonySwarm
else:
    PonySwarm = import_module(
        f"{__package__.split('.', 1)[0]}.desktop_pony_swarm.core.swarm"
    ).PonySwarm

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkQuery:
    """Represents a single benchmark query with its expected characteristics.

    Attributes:
        query: The text of the query.
        complexity: The complexity level ("micro", "medium", "large").
        expected_latency: The target latency in seconds for this query.
        description: A brief description of the query's purpose.
        expected_keywords: A list of keywords expected in a high-quality response.
    """

    query: str
    complexity: str  # "micro", "medium", "large"
    expected_latency: float  # Target latency in seconds
    description: str = ""
    expected_keywords: List[str] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    """Stores the results from a single benchmark run.

    Attributes:
        query: The query that was run.
        complexity: The complexity level of the query.
        latency: The time taken to generate the response, in seconds.
        response: The final response from the swarm.
        diversity: The average semantic diversity of the responses.
        num_generations: The total number of language model generations.
        params: The RSA parameters (N, K, T) used for the run.
        timestamp: The time the benchmark was completed.
    """

    query: str
    complexity: str
    latency: float
    response: str
    diversity: float
    num_generations: int
    params: Dict[str, int]
    timestamp: float = field(default_factory=time.time)

    def meets_target(self, target_latency: float) -> bool:
        """Checks if the measured latency meets the target latency.

        Args:
            target_latency: The target latency to compare against.

        Returns:
            True if the latency is within the target, False otherwise.
        """
        return self.latency <= target_latency

    def quality_score(self, expected_keywords: List[str]) -> float:
        """Calculates a simple quality score based on the presence of expected keywords.

        Args:
            expected_keywords: A list of keywords to check for in the response.

        Returns:
            A float between 0.0 and 1.0 representing the quality score.
        """
        if not expected_keywords:
            return 1.0

        response_lower = self.response.lower()
        matches = sum(1 for kw in expected_keywords if kw.lower() in response_lower)
        return matches / len(expected_keywords)


class BenchmarkSuite:
    """Provides a comprehensive suite for testing the performance of the Pony Swarm.

    This class is a cornerstone of the project's "Specification-Driven Development"
    (SDD) and "Reality Validation" methodologies. It contains a curated set of
    benchmark queries across different complexity levels, allowing for rigorous
    and repeatable testing of the swarm's performance, quality, and efficiency.

    The suite can be used to:
    - Validate that the swarm meets its performance targets.
    - Compare the effectiveness of different RSA parameter configurations.
    - Track performance improvements or regressions over time.
    """

    # Benchmark queries organized by complexity
    MICRO_QUERIES = [
        BenchmarkQuery(
            query="What is 47 * 89?",
            complexity="micro",
            expected_latency=10.0,
            description="Simple arithmetic",
            expected_keywords=["4183", "4,183", "multiply"],
        ),
        BenchmarkQuery(
            query="Calculate 256 + 384",
            complexity="micro",
            expected_latency=10.0,
            description="Basic addition",
            expected_keywords=["640"],
        ),
        BenchmarkQuery(
            query="What is the square root of 144?",
            complexity="micro",
            expected_latency=10.0,
            description="Square root calculation",
            expected_keywords=["12"],
        ),
    ]

    MEDIUM_QUERIES = [
        BenchmarkQuery(
            query="Explain the concept of recursion using a simple analogy.",
            complexity="medium",
            expected_latency=15.0,
            description="Conceptual explanation",
            expected_keywords=["recursion", "function", "itself", "calls"],
        ),
        BenchmarkQuery(
            query=(
                "A bat and a ball cost $1.10 in total. The bat costs $1.00 "
                "more than the ball. How much does the ball cost?"
            ),
            complexity="medium",
            expected_latency=15.0,
            description="Classic reasoning puzzle",
            expected_keywords=["0.05", "5 cents", "five cents"],
        ),
        BenchmarkQuery(
            query="What are the key differences between Python and JavaScript?",
            complexity="medium",
            expected_latency=15.0,
            description="Comparative analysis",
            expected_keywords=["python", "javascript", "syntax", "typing"],
        ),
        BenchmarkQuery(
            query="How does a binary search algorithm work?",
            complexity="medium",
            expected_latency=15.0,
            description="Algorithm explanation",
            expected_keywords=["binary", "search", "divide", "sorted"],
        ),
    ]

    LARGE_QUERIES = [
        BenchmarkQuery(
            query=(
                "Write a short story (3-4 sentences) about a robot learning to "
                "appreciate art."
            ),
            complexity="large",
            expected_latency=20.0,
            description="Creative writing",
            expected_keywords=["robot", "art"],
        ),
        BenchmarkQuery(
            query=(
                "Design a solution for reducing traffic congestion in a large "
                "city. Consider multiple approaches."
            ),
            complexity="large",
            expected_latency=20.0,
            description="Complex problem-solving",
            expected_keywords=["traffic", "transport", "solution"],
        ),
        BenchmarkQuery(
            query=(
                "Explain quantum entanglement to a 10-year-old, then explain "
                "how it's used in quantum computing."
            ),
            complexity="large",
            expected_latency=20.0,
            description="Multi-part explanation",
            expected_keywords=["quantum", "entangle", "computing"],
        ),
    ]

    def __init__(self, use_mock: bool = True):
        """Initializes the BenchmarkSuite.

        Args:
            use_mock: If True, the suite will use mock pony agents for fast
                execution, which is useful for testing the benchmark logic
                itself. If False, it will use real inference, which is necessary
                for accurate performance measurement.
        """
        self.use_mock = use_mock
        self.results: List[BenchmarkResult] = []
        logger.info(
            f"Initialized BenchmarkSuite [{'MOCK' if use_mock else 'REAL'} mode]"
        )

    def get_all_queries(self) -> List[BenchmarkQuery]:
        """Returns a list of all benchmark queries in the suite."""
        return self.MICRO_QUERIES + self.MEDIUM_QUERIES + self.LARGE_QUERIES

    def get_queries_by_complexity(self, complexity: str) -> List[BenchmarkQuery]:
        """Returns a list of benchmark queries for a specific complexity level.

        Args:
            complexity: The complexity level to filter by ("micro", "medium",
                or "large").

        Returns:
            A list of `BenchmarkQuery` objects for the specified complexity level.
        """
        complexity = complexity.lower()
        if complexity == "micro":
            return self.MICRO_QUERIES
        if complexity == "medium":
            return self.MEDIUM_QUERIES
        if complexity == "large":
            return self.LARGE_QUERIES
        raise ValueError(f"Unknown complexity: {complexity}")

    async def run_single_benchmark(
        self, query: BenchmarkQuery, N: int = 4, K: int = 2, T: int = 3
    ) -> BenchmarkResult:
        """Runs a single benchmark query with a given set of RSA parameters.

        Args:
            query: The `BenchmarkQuery` to run.
            N: The number of pony agents to use.
            K: The aggregation size.
            T: The number of refinement iterations.

        Returns:
            A `BenchmarkResult` object containing the performance and quality
            metrics for the run.
        """
        logger.info(f"Running benchmark: {query.description} (N={N}, K={K}, T={T})")

        async with PonySwarm(num_ponies=N, use_mock=self.use_mock) as swarm:
            start_time = time.time()

            result = await swarm.recursive_self_aggregation(query=query.query, K=K, T=T)

            latency = time.time() - start_time

            benchmark_result = BenchmarkResult(
                query=query.query,
                complexity=query.complexity,
                latency=latency,
                response=result["response"],
                diversity=result["metrics"]["avg_diversity"],
                num_generations=result["metrics"]["total_generations"],
                params={"N": N, "K": K, "T": T},
            )

            self.results.append(benchmark_result)

            # Log results
            meets_target = benchmark_result.meets_target(query.expected_latency)
            quality = benchmark_result.quality_score(query.expected_keywords)

            logger.info(
                f"  ✓ Latency: {latency:.2f}s (target: {query.expected_latency}s) "
                f"{'✓' if meets_target else '✗'}"
            )
            logger.info(f"  ✓ Quality: {quality:.2%}")
            logger.info(f"  ✓ Diversity: {benchmark_result.diversity:.4f}")

            return benchmark_result

    async def run_suite(
        self,
        complexity_filter: Optional[str] = None,
        N: int = 4,
        K: int = 2,
        T: int = 3,
    ) -> Dict[str, Any]:
        """Runs the full benchmark suite or a filtered subset.

        This method orchestrates the execution of multiple benchmark queries and
        compiles the results into a summary dictionary.

        Args:
            complexity_filter: If provided, only runs queries of this complexity
                level.
            N: The number of pony agents to use for the suite.
            K: The aggregation size to use for the suite.
            T: The number of refinement iterations to use for the suite.

        Returns:
            A dictionary containing aggregated metrics and a list of the
            individual `BenchmarkResult` objects.
        """
        logger.info(
            f"Running benchmark suite (complexity={complexity_filter or 'all'})"
        )

        if complexity_filter:
            queries = self.get_queries_by_complexity(complexity_filter)
        else:
            queries = self.get_all_queries()

        suite_results = []

        for query in queries:
            result = await self.run_single_benchmark(query, N, K, T)
            suite_results.append(result)

        # Compute aggregate metrics
        latencies = [r.latency for r in suite_results]
        diversities = [r.diversity for r in suite_results]

        # Group by complexity
        by_complexity = {}
        for complexity in ["micro", "medium", "large"]:
            complexity_results = [
                r for r in suite_results if r.complexity == complexity
            ]
            if complexity_results:
                by_complexity[complexity] = {
                    "count": len(complexity_results),
                    "avg_latency": statistics.mean(
                        [r.latency for r in complexity_results]
                    ),
                    "max_latency": max(r.latency for r in complexity_results),
                    "avg_diversity": statistics.mean(
                        [r.diversity for r in complexity_results]
                    ),
                }

        summary = {
            "total_queries": len(suite_results),
            "params": {"N": N, "K": K, "T": T},
            "avg_latency": statistics.mean(latencies),
            "median_latency": statistics.median(latencies),
            "max_latency": max(latencies),
            "min_latency": min(latencies),
            "avg_diversity": statistics.mean(diversities),
            "by_complexity": by_complexity,
            "results": suite_results,
        }

        return summary

    def compare_baselines(
        self,
        baseline_results: List[BenchmarkResult],
        current_results: List[BenchmarkResult],
    ) -> Dict[str, Any]:
        """Compares a set of current benchmark results against a baseline set.

        This is useful for tracking performance changes over time and verifying
        that optimizations have had the intended effect.

        Args:
            baseline_results: A list of `BenchmarkResult` objects from a previous
                run to serve as the baseline.
            current_results: A list of `BenchmarkResult` objects from the current
                run.

        Returns:
            A dictionary containing the comparison metrics, including the
            percentage improvement in latency.
        """
        baseline_latencies = [r.latency for r in baseline_results]
        current_latencies = [r.latency for r in current_results]

        baseline_avg = statistics.mean(baseline_latencies)
        current_avg = statistics.mean(current_latencies)

        improvement = (baseline_avg - current_avg) / baseline_avg

        return {
            "baseline_avg_latency": baseline_avg,
            "current_avg_latency": current_avg,
            "improvement_pct": improvement * 100,
            "meets_30pct_target": improvement >= 0.30,
            "latency_reduction": baseline_avg - current_avg,
        }

    def generate_report(self, summary: Dict[str, Any]) -> str:
        """Generates a human-readable report from a benchmark summary.

        Args:
            summary: A summary dictionary produced by the `run_suite` method.

        Returns:
            A formatted string containing the benchmark report.
        """
        report = []
        report.append("\n" + "=" * 80)
        report.append("PONY SWARM BENCHMARK REPORT")
        report.append("=" * 80)
        report.append(
            f"\nParameters: N={summary['params']['N']}, "
            f"K={summary['params']['K']}, T={summary['params']['T']}"
        )
        report.append(f"Mode: {'MOCK' if self.use_mock else 'REAL INFERENCE'}")
        report.append(f"\nTotal Queries: {summary['total_queries']}")
        report.append(f"Average Latency: {summary['avg_latency']:.2f}s")
        report.append(f"Median Latency: {summary['median_latency']:.2f}s")
        report.append(
            f"Range: {summary['min_latency']:.2f}s - {summary['max_latency']:.2f}s"
        )
        report.append(f"Average Diversity: {summary['avg_diversity']:.4f}")

        report.append("\n" + "-" * 80)
        report.append("BY COMPLEXITY")
        report.append("-" * 80)

        for complexity, metrics in summary["by_complexity"].items():
            report.append(f"\n{complexity.upper()}:")
            report.append(f"  Queries: {metrics['count']}")
            report.append(f"  Avg Latency: {metrics['avg_latency']:.2f}s")
            report.append(f"  Max Latency: {metrics['max_latency']:.2f}s")
            report.append(f"  Avg Diversity: {metrics['avg_diversity']:.4f}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)


async def main():
    """Defines the command-line interface for running the benchmark suite."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Pony Swarm benchmarks")
    parser.add_argument(
        "--complexity",
        choices=["micro", "medium", "large"],
        help="Filter by complexity level",
    )
    parser.add_argument("--N", type=int, default=4, help="Number of ponies")
    parser.add_argument("--K", type=int, default=2, help="Aggregation size")
    parser.add_argument("--T", type=int, default=3, help="Number of iterations")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real Horde.AI (slow, default is mock mode)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    suite = BenchmarkSuite(use_mock=not args.real)
    summary = await suite.run_suite(
        complexity_filter=args.complexity, N=args.N, K=args.K, T=args.T
    )

    print(suite.generate_report(summary))


if __name__ == "__main__":
    asyncio.run(main())
