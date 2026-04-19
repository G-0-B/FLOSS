"""
ARF CLI - Swarm subcommands

Pony swarm operations using Recursive Self-Aggregation (RSA).
All commands support --json output mode for scripting.

Examples:
    arf swarm query "What is 47 * 89?" --ponies 4
    arf swarm query "Explain recursion" --iterations 3 --json
    arf swarm run --query "Complex reasoning task" --aggregation-size 2
"""

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console

CLI_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = CLI_ROOT.parent

for bootstrap_path in (WORKSPACE_ROOT, CLI_ROOT):
    bootstrap_str = str(bootstrap_path)
    if bootstrap_str not in sys.path:
        sys.path.insert(0, bootstrap_str)


def _get_swarm_runtime():
    """Import SwarmRuntime lazily after local path bootstrap."""
    try:
        from pwnies.desktop_pony_swarm.runtime.orchestrator import SwarmRuntime
    except ImportError:
        return None

    return SwarmRuntime


def _swarm_available() -> bool:
    """Report whether the optional swarm runtime dependency is importable."""
    return _get_swarm_runtime() is not None


app = typer.Typer(help="Pony swarm operations")
console = Console()


@app.command()
def query(
    question: str = typer.Argument(..., help="Query for the swarm"),
    ponies: int = typer.Option(
        4, "--ponies", "-n", help="Number of ponies (N parameter)"
    ),
    aggregation_size: int = typer.Option(
        2, "--aggregation-size", "-k", help="Aggregation size (K parameter)"
    ),
    iterations: int = typer.Option(
        3, "--iterations", "-t", help="Number of iterations (T parameter)"
    ),
    mock: bool = typer.Option(
        True, "--mock/--real", help="Use mock inference (default) or real Horde.AI"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Queries the pony swarm using the Recursive Self-Aggregation (RSA) algorithm.

    This command allows a user to pose a question or task to the swarm and receive
    a high-quality, synthesized response. It provides a direct interface to the
    collective intelligence of the ponies, allowing for the exploration of their
    emergent capabilities. The command's parameters (N, K, T) allow for fine-tuning
    the RSA process, enabling experimentation and optimization.
    """
    if not _swarm_available():
        error_msg = (
            "Pony swarm module not available. "
            "Install dependencies or check pwnies/ directory."
        )
        if json_output:
            print(json.dumps({"success": False, "error": error_msg}))
        else:
            console.print(f"[red]Error:[/red] {error_msg}")
        sys.exit(1)

    try:
        # Run async query
        result = asyncio.run(
            _run_swarm_query(
                question=question,
                num_ponies=ponies,
                K=aggregation_size,
                T=iterations,
                use_mock=mock,
                json_output=json_output,
            )
        )

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "query": question,
                        "response": result["response"],
                        "parameters": {
                            "N": ponies,
                            "K": aggregation_size,
                            "T": iterations,
                        },
                        "metrics": result.get("metrics", {}),
                        "is_crisis": result.get("is_crisis", False),
                    }
                )
            )
        else:
            console.print("\n[bold green]Response:[/bold green]")
            console.print(result["response"])
            console.print()

            if result.get("metrics"):
                metrics = result["metrics"]
                console.print(
                    f"[dim]Time: {metrics.get('total_time', 0):.2f}s | "
                    f"Generations: {metrics.get('total_generations', 0)} | "
                    f"Diversity: {metrics.get('avg_diversity', 0):.3f}[/dim]"
                )

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
    SwarmRuntime = _get_swarm_runtime()
    if SwarmRuntime is None:
        raise RuntimeError("Pony swarm module not available")
    runtime = SwarmRuntime()
    runtime.start()
    # This is a placeholder for the actual query.
    # The SwarmRuntime will need a query method that internally uses the managers.
    result = {"response": "This is a placeholder response from the SwarmRuntime."}
    runtime.stop()
    return result


if __name__ == "__main__":
    app()
