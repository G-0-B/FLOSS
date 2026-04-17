"""
ARF CLI - Benchmark subcommands

Benchmarking operations for performance testing and optimization.
All commands support --json output mode for scripting.

Examples:
    arf benchmark --suite swarm --iterations 10
    arf benchmark --suite memory --iterations 5 --json
    arf benchmark list-suites
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory

try:
    from pwnies.desktop_pony_swarm.core.swarm import PonySwarm

    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False

app = typer.Typer(help="Benchmarking operations")
console = Console()


@app.command()
def run(
    suite: str = typer.Option(
        "memory", "--suite", "-s", help="Benchmark suite: memory, swarm, or all"
    ),
    iterations: int = typer.Option(
        10, "--iterations", "-i", help="Number of iterations"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Runs a specified benchmark suite to test the performance of the ARF.

    This command is a key tool for "Reality Validation," providing a way to
    empirically measure the performance of the system's core components, such as
    the `ConversationMemory` and the `PonySwarm`. The results of these benchmarks
    are essential for identifying performance bottlenecks, tracking improvements,
    and ensuring that the system meets its operational requirements.
    """
    try:
        results = {}

        if suite in ("memory", "all"):
            if not json_output:
                console.print("[cyan]Running memory benchmark...[/cyan]")
            results["memory"] = _benchmark_memory(iterations, json_output)

        if suite in ("swarm", "all"):
            if not SWARM_AVAILABLE:
                error_msg = "Swarm benchmark unavailable: pony swarm module not found"
                if json_output:
                    print(json.dumps({"success": False, "error": error_msg}))
                else:
                    console.print(f"[red]Error:[/red] {error_msg}")
                sys.exit(1)

            if not json_output:
                console.print("[cyan]Running swarm benchmark...[/cyan]")
            results["swarm"] = _benchmark_swarm(iterations, json_output)

        if suite not in ("memory", "swarm", "all"):
            error_msg = f"Unknown suite: {suite}. Available: memory, swarm, all"
            if json_output:
                print(json.dumps({"success": False, "error": error_msg}))
            else:
                console.print(f"[red]Error:[/red] {error_msg}")
            sys.exit(1)

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "suite": suite,
                        "iterations": iterations,
                        "results": results,
                    }
                )
            )
        else:
            console.print("\n[bold green]Benchmark Complete[/bold green]")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _benchmark_memory(iterations: int, json_output: bool) -> dict:
    """Benchmark memory operations"""
    results = {
        "transmit_times": [],
        "recall_times": [],
    }

    if not json_output:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        )
        progress.start()
        task = progress.add_task("Memory benchmark", total=iterations * 2)
    else:
        progress = None
        task = None

    # Create test memory
    memory = ConversationMemory(agent_id="benchmark")

    # Benchmark transmit
    for i in range(iterations):
        start = time.time()
        memory.transmit(
            {
                "content": f"Benchmark test {i}",
                "coherence": 0.9,
            },
            skip_validation=True,
        )
        elapsed = time.time() - start
        results["transmit_times"].append(elapsed)

        if progress:
            progress.advance(task)

    # Benchmark recall
    for i in range(iterations):
        start = time.time()
        memory.recall(f"test {i}", top_k=5)
        elapsed = time.time() - start
        results["recall_times"].append(elapsed)

        if progress:
            progress.advance(task)

    if progress:
        progress.stop()

    # Calculate statistics
    import statistics

    results["transmit_avg"] = statistics.mean(results["transmit_times"])
    results["transmit_median"] = statistics.median(results["transmit_times"])
    results["recall_avg"] = statistics.mean(results["recall_times"])
    results["recall_median"] = statistics.median(results["recall_times"])

    if not json_output:
        table = Table(title="Memory Benchmark Results")
        table.add_column("Operation", style="cyan")
        table.add_column("Avg Time (ms)", style="green")
        table.add_column("Median (ms)", style="green")

        table.add_row(
            "transmit",
            f"{results['transmit_avg'] * 1000:.2f}",
            f"{results['transmit_median'] * 1000:.2f}",
        )
        table.add_row(
            "recall",
            f"{results['recall_avg'] * 1000:.2f}",
            f"{results['recall_median'] * 1000:.2f}",
        )

        console.print(table)

    return results


def _benchmark_swarm(iterations: int, json_output: bool) -> dict:
    """Benchmark swarm operations"""
    results = {
        "query_times": [],
        "diversity_scores": [],
    }

    if not json_output:
        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console,
        )
        progress.start()
        task = progress.add_task("Swarm benchmark", total=iterations)
    else:
        progress = None
        task = None

    # Benchmark queries
    queries = [
        "What is 47 * 89?",
        "Explain recursion",
        "Write a haiku about AI",
    ]

    async def run_benchmarks():
        async with PonySwarm(num_ponies=4, use_mock=True) as swarm:
            for i in range(iterations):
                query = queries[i % len(queries)]
                start = time.time()

                result = await swarm.recursive_self_aggregation(
                    query=query, K=2, T=2  # Reduced for benchmarking
                )

                elapsed = time.time() - start
                results["query_times"].append(elapsed)

                if result.get("iterations"):
                    final_iter = result["iterations"][-1]
                    results["diversity_scores"].append(final_iter.get("diversity", 0))

                if progress:
                    progress.advance(task)

    asyncio.run(run_benchmarks())

    if progress:
        progress.stop()

    # Calculate statistics
    import statistics

    results["query_avg"] = statistics.mean(results["query_times"])
    results["query_median"] = statistics.median(results["query_times"])
    if results["diversity_scores"]:
        results["diversity_avg"] = statistics.mean(results["diversity_scores"])

    if not json_output:
        table = Table(title="Swarm Benchmark Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Avg Query Time", f"{results['query_avg']:.2f}s")
        table.add_row("Median Query Time", f"{results['query_median']:.2f}s")
        if results.get("diversity_avg"):
            table.add_row("Avg Diversity", f"{results['diversity_avg']:.4f}")

        console.print(table)

    return results


@app.command(name="list-suites")
def list_suites():
    """Lists the available benchmark suites.

    This command provides a simple way to discover the available benchmark suites
    and their current status, promoting transparency and ease of use for developers
    and testers.
    """
    suites = [
        ("memory", "Conversation memory operations", "Available"),
        (
            "swarm",
            "Pony swarm performance",
            "Available" if SWARM_AVAILABLE else "Unavailable",
        ),
        ("all", "All benchmark suites", "Available"),
    ]

    table = Table(title="Benchmark Suites")
    table.add_column("Suite", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Status", style="green")

    for name, desc, status in suites:
        table.add_row(name, desc, status)

    console.print(table)
    sys.exit(0)


if __name__ == "__main__":
    app()
