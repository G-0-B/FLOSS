"""
Parameter Sweep for RSA Algorithm Optimization.

Performs grid search over N, K, T parameters to find optimal configurations
for different query complexities.

Phase 4.1: Performance Optimization
"""

import asyncio
import time
import logging
import json
import itertools
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.benchmark_suite import BenchmarkSuite, BenchmarkQuery, BenchmarkResult

logger = logging.getLogger(__name__)


@dataclass
class ParameterConfig:
    """Represents a single configuration of RSA parameters for testing.

    Attributes:
        N: The number of pony agents in the swarm.
        K: The aggregation size (how many responses to sample).
        T: The number of refinement iterations.
    """

    N: int  # Number of ponies
    K: int  # Aggregation size
    T: int  # Number of iterations

    def __str__(self):
        """Provides a string representation of the configuration."""
        return f"N={self.N},K={self.K},T={self.T}"

    def is_valid(self) -> bool:
        """Checks if the parameter combination is valid (K <= N)."""
        # K must be <= N
        if self.K > self.N:
            return False
        # All must be positive
        if self.N < 1 or self.K < 1 or self.T < 1:
            return False
        return True


@dataclass
class SweepResult:
    """Stores the aggregated results from testing a single parameter configuration.

    Attributes:
        config: The `ParameterConfig` that was tested.
        complexity: The complexity level of the queries used for the test.
        avg_latency: The average time taken to get a response.
        avg_diversity: The average semantic diversity of the responses.
        avg_quality: The average quality score of the responses.
        total_time: The total time taken for the test run.
        num_queries: The number of queries used in the test.
    """

    config: ParameterConfig
    complexity: str
    avg_latency: float
    avg_diversity: float
    avg_quality: float
    total_time: float
    num_queries: int

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the sweep result to a dictionary."""
        return {
            "N": self.config.N,
            "K": self.config.K,
            "T": self.config.T,
            "complexity": self.complexity,
            "avg_latency": self.avg_latency,
            "avg_diversity": self.avg_diversity,
            "avg_quality": self.avg_quality,
            "total_time": self.total_time,
            "num_queries": self.num_queries,
        }


class ParameterSweep:
    """Performs a grid search over RSA parameters to find optimal configurations.

    This class is a key tool for the "Evolution" and "Specification-Driven
    Development" (SDD) principles of the project. It systematically benchmarks
    different combinations of the RSA parameters (N, K, T) to identify the
    most effective and efficient configurations for various types of tasks.
    The results of this sweep can be used to inform the `AdaptiveParameterSelector`,
    ensuring that the swarm operates optimally.
    """

    def __init__(self, use_mock: bool = True):
        """Initializes the ParameterSweep.

        Args:
            use_mock: If True, uses mock inference for fast testing. Using real
                inference is significantly slower and more costly.
        """
        self.use_mock = use_mock
        self.suite = BenchmarkSuite(use_mock=use_mock)
        self.results: List[SweepResult] = []
        logger.info(
            f"Initialized ParameterSweep [{'MOCK' if use_mock else 'REAL'} mode]"
        )

    def generate_configs(
        self,
        N_values: List[int] = None,
        K_values: List[int] = None,
        T_values: List[int] = None,
    ) -> List[ParameterConfig]:
        """Generates a list of all valid parameter combinations for the sweep.

        The method filters out invalid combinations where the aggregation size (K)
        is greater than the number of ponies (N).

        Args:
            N_values: A list of N values to test. Defaults to [2, 4, 6, 8].
            K_values: A list of K values to test. Defaults to [1, 2, 3].
            T_values: A list of T values to test. Defaults to [1, 2, 3, 4].

        Returns:
            A list of valid `ParameterConfig` objects to be tested.
        """
        if N_values is None:
            N_values = [2, 4, 6, 8]
        if K_values is None:
            K_values = [1, 2, 3]
        if T_values is None:
            T_values = [1, 2, 3, 4]

        # Generate all combinations
        all_combos = itertools.product(N_values, K_values, T_values)

        # Filter to valid configurations
        configs = []
        for N, K, T in all_combos:
            config = ParameterConfig(N=N, K=K, T=T)
            if config.is_valid():
                configs.append(config)

        logger.info(f"Generated {len(configs)} valid parameter configurations")
        return configs

    async def test_config(
        self, config: ParameterConfig, queries: List[BenchmarkQuery]
    ) -> SweepResult:
        """Tests a single parameter configuration against a set of benchmark queries.

        This method runs a given `ParameterConfig` through a list of queries of the
        same complexity, and then aggregates the performance metrics (latency,
        diversity, quality) into a `SweepResult`.

        Args:
            config: The `ParameterConfig` to test.
            queries: A list of `BenchmarkQuery` objects to run the test against.

        Returns:
            A `SweepResult` object containing the aggregated metrics for the
            tested configuration.
        """
        logger.info(f"Testing config: {config}")

        results = []
        start_time = time.time()

        async with self.suite.__class__(use_mock=self.use_mock) as suite:
            for query in queries:
                result = await suite.run_single_benchmark(
                    query, N=config.N, K=config.K, T=config.T
                )
                results.append(result)

        total_time = time.time() - start_time

        # Compute aggregate metrics
        avg_latency = sum(r.latency for r in results) / len(results)
        avg_diversity = sum(r.diversity for r in results) / len(results)

        # Quality score based on keyword matching
        quality_scores = [
            r.quality_score(q.expected_keywords) for r, q in zip(results, queries)
        ]
        avg_quality = sum(quality_scores) / len(quality_scores)

        sweep_result = SweepResult(
            config=config,
            complexity=queries[0].complexity if queries else "unknown",
            avg_latency=avg_latency,
            avg_diversity=avg_diversity,
            avg_quality=avg_quality,
            total_time=total_time,
            num_queries=len(results),
        )

        self.results.append(sweep_result)

        logger.info(
            f"  Config {config}: "
            f"latency={avg_latency:.2f}s, "
            f"diversity={avg_diversity:.4f}, "
            f"quality={avg_quality:.2%}"
        )

        return sweep_result

    async def run_sweep(
        self,
        complexity: str = "micro",
        N_values: List[int] = None,
        K_values: List[int] = None,
        T_values: List[int] = None,
        max_configs: int = None,
    ) -> List[SweepResult]:
        """Runs a full parameter sweep for a specific query complexity level.

        This method orchestrates the entire sweep process: it generates a set of
        parameter configurations, runs tests for each one against a benchmark
        suite of a given complexity, and collects the results.

        Args:
            complexity: The complexity level of queries to test against
                ("micro", "medium", or "large").
            N_values: A list of N values to test.
            K_values: A list of K values to test.
            T_values: A list of T values to test.
            max_configs: An optional limit on the number of configurations to test,
                useful for quick checks.

        Returns:
            A list of `SweepResult` objects, one for each tested configuration.
        """
        logger.info(f"Starting parameter sweep for {complexity} queries")

        # Get queries for this complexity
        queries = self.suite.get_queries_by_complexity(complexity)

        # Generate configurations
        configs = self.generate_configs(N_values, K_values, T_values)

        # Limit if requested
        if max_configs and len(configs) > max_configs:
            logger.info(f"Limiting to {max_configs} configurations")
            configs = configs[:max_configs]

        # Test each configuration
        results = []
        for i, config in enumerate(configs, 1):
            logger.info(f"Progress: {i}/{len(configs)}")
            result = await self.test_config(config, queries)
            results.append(result)

        return results

    def find_pareto_frontier(
        self, results: List[SweepResult] = None
    ) -> List[SweepResult]:
        """Identifies the Pareto-optimal configurations from a set of sweep results.

        A configuration is considered Pareto-optimal if there is no other
        configuration that is better in terms of both latency (lower is better)
        and quality (higher is better). This helps to identify the set of
        most efficient configurations that represent the best trade-offs.

        Args:
            results: A list of `SweepResult` objects to analyze. If not provided,
                the instance's own results are used.

        Returns:
            A list of `SweepResult` objects that are on the Pareto frontier.
        """
        if results is None:
            results = self.results

        pareto_frontier = []

        for candidate in results:
            is_dominated = False

            # Check if any other config dominates this one
            for other in results:
                if other == candidate:
                    continue

                # Other dominates if it's better in latency AND quality
                if (
                    other.avg_latency <= candidate.avg_latency
                    and other.avg_quality >= candidate.avg_quality
                    and (
                        other.avg_latency < candidate.avg_latency
                        or other.avg_quality > candidate.avg_quality
                    )
                ):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto_frontier.append(candidate)

        logger.info(f"Found {len(pareto_frontier)} Pareto-optimal configurations")
        return pareto_frontier

    def find_best_config(
        self, metric: str = "latency", results: List[SweepResult] = None
    ) -> SweepResult:
        """Finds the single best configuration based on a specific metric.

        Args:
            metric: The metric to optimize for ("latency", "diversity", or "quality").
            results: A list of `SweepResult` objects to analyze.

        Returns:
            The `SweepResult` for the configuration that performs best on the
            specified metric.
        """
        if results is None:
            results = self.results

        if not results:
            raise ValueError("No results to analyze")

        if metric == "latency":
            return min(results, key=lambda r: r.avg_latency)
        elif metric == "diversity":
            return max(results, key=lambda r: r.avg_diversity)
        elif metric == "quality":
            return max(results, key=lambda r: r.avg_quality)
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def save_results(self, filename: str = "sweep_results.json"):
        """Saves the sweep results to a JSON file.

        Args:
            filename: The name of the file to save the results to.
        """
        output_path = Path(__file__).parent / filename

        data = {
            "timestamp": time.time(),
            "mode": "mock" if self.use_mock else "real",
            "total_configs": len(self.results),
            "results": [r.to_dict() for r in self.results],
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved results to {output_path}")
        return output_path

    def generate_report(self, results: List[SweepResult] = None) -> str:
        """Generates a human-readable report summarizing the sweep results.

        The report includes the best configurations for latency and quality, as
        well as the full list of Pareto-optimal configurations.

        Args:
            results: A list of `SweepResult` objects to include in the report.

        Returns:
            A string containing the formatted report.
        """
        if results is None:
            results = self.results

        if not results:
            return "No results to report"

        report = []
        report.append("\n" + "=" * 80)
        report.append("PARAMETER SWEEP REPORT")
        report.append("=" * 80)
        report.append(f"Mode: {'MOCK' if self.use_mock else 'REAL INFERENCE'}")
        report.append(f"Total Configurations: {len(results)}")

        # Best by latency
        best_latency = self.find_best_config("latency", results)
        report.append(f"\n✓ BEST LATENCY: {best_latency.config}")
        report.append(f"  Latency: {best_latency.avg_latency:.2f}s")
        report.append(f"  Quality: {best_latency.avg_quality:.2%}")
        report.append(f"  Diversity: {best_latency.avg_diversity:.4f}")

        # Best by quality
        best_quality = self.find_best_config("quality", results)
        report.append(f"\n✓ BEST QUALITY: {best_quality.config}")
        report.append(f"  Quality: {best_quality.avg_quality:.2%}")
        report.append(f"  Latency: {best_quality.avg_latency:.2f}s")
        report.append(f"  Diversity: {best_quality.avg_diversity:.4f}")

        # Pareto frontier
        pareto = self.find_pareto_frontier(results)
        report.append(f"\n✓ PARETO FRONTIER ({len(pareto)} configurations):")
        for config_result in sorted(pareto, key=lambda r: r.avg_latency):
            report.append(
                f"  {config_result.config}: "
                f"latency={config_result.avg_latency:.2f}s, "
                f"quality={config_result.avg_quality:.2%}"
            )

        report.append("\n" + "=" * 80)

        return "\n".join(report)


async def main():
    """Defines the command-line interface for running the parameter sweep."""
    import argparse

    parser = argparse.ArgumentParser(description="Run parameter sweep for Pony Swarm")
    parser.add_argument(
        "--complexity",
        choices=["micro", "medium", "large"],
        default="micro",
        help="Complexity level to test",
    )
    parser.add_argument(
        "--max-configs", type=int, help="Limit number of configs (for quick testing)"
    )
    parser.add_argument("--real", action="store_true", help="Use real Horde.AI (slow)")
    parser.add_argument(
        "--output", default="sweep_results.json", help="Output JSON file"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    sweep = ParameterSweep(use_mock=not args.real)

    # Run sweep
    results = await sweep.run_sweep(
        complexity=args.complexity, max_configs=args.max_configs
    )

    # Save results
    sweep.save_results(args.output)

    # Print report
    print(sweep.generate_report(results))


if __name__ == "__main__":
    asyncio.run(main())
