"""
ARF CLI - Swarm subcommands

Pony swarm operations using Recursive Self-Aggregation (RSA).
All commands support --json output mode for scripting.

Examples:
    arf swarm query "What is 47 * 89?" --ponies 4
    arf swarm query "Explain recursion" --iterations 3 --json
    arf swarm run --query "Complex reasoning task" --aggregation-size 2
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from pwnies.desktop_pony_swarm.runtime.orchestrator import SwarmRuntime
    SWARM_AVAILABLE = True
except ImportError:
    SWARM_AVAILABLE = False

app = typer.Typer(help="Pony swarm operations")
console = Console()


@app.command()
def query(
    question: str = typer.Argument(..., help="Query for the swarm"),
    ponies: int = typer.Option(4, "--ponies", "-n", help="Number of ponies (N parameter)"),
    aggregation_size: int = typer.Option(2, "--aggregation-size", "-k", help="Aggregation size (K parameter)"),
    iterations: int = typer.Option(3, "--iterations", "-t", help="Number of iterations (T parameter)"),
    mock: bool = typer.Option(True, "--mock/--real", help="Use mock inference (default) or real Horde.AI"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Queries the pony swarm using the Recursive Self-Aggregation (RSA) algorithm.

    This command allows a user to pose a question or task to the swarm and receive
    a high-quality, synthesized response. It provides a direct interface to the
    collective intelligence of the ponies, allowing for the exploration of their
    emergent capabilities. The command's parameters (N, K, T) allow for fine-tuning
    the RSA process, enabling experimentation and optimization.
    """
    if not SWARM_AVAILABLE:
        error_msg = "Pony swarm module not available. Install dependencies or check pwnies/ directory."
        if json_output:
            print(json.dumps({"success": False, "error": error_msg}))
        else:
            console.print(f"[red]Error:[/red] {error_msg}")
        sys.exit(1)

    try:
        # Run async query
        result = asyncio.run(_run_swarm_query(
            question=question,
            num_ponies=ponies,
            K=aggregation_size,
            T=iterations,
            use_mock=mock,
            json_output=json_output,
        ))

        if json_output:
            print(json.dumps({
                "success": True,
                "query": question,
                "response": result['response'],
                "parameters": {
                    "N": ponies,
                    "K": aggregation_size,
                    "T": iterations,
                },
                "metrics": result.get('metrics', {}),
                "is_crisis": result.get('is_crisis', False),
            }))
        else:
            console.print(f"\n[bold green]Response:[/bold green]")
            console.print(result['response'])
            console.print()

            if result.get('metrics'):
                metrics = result['metrics']
                console.print(f"[dim]Time: {metrics.get('total_time', 0):.2f}s | "
                            f"Generations: {metrics.get('total_generations', 0)} | "
                            f"Diversity: {metrics.get('avg_diversity', 0):.3f}[/dim]")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


async def _run_swarm_query(
    question: str,
    num_ponies: int,
    K: int,
    T: int,
    use_mock: bool,
    json_output: bool,
):
    """Helper to run swarm query asynchronously"""
    runtime = SwarmRuntime()
    runtime.start()
    # This is a placeholder for the actual query.
    # The SwarmRuntime will need a query method that internally uses the managers.
    result = {"response": "This is a placeholder response from the SwarmRuntime."}
    runtime.stop()
    return result


if __name__ == "__main__":
    app()
