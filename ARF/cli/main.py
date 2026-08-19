#!/usr/bin/env python3
"""
ARF CLI - Main entry point

A unified command-line interface for all ARF operations following Unix philosophy:
- Composable subcommands
- Pipeable JSON output
- Human-readable output for debugging
- Exit codes follow Unix conventions (0=success)

Usage:
    arf memory transmit "GPT-4 is a LLM"
    arf memory recall --agent alice --query "LLM"
    arf swarm query "What is 47 * 89?" --ponies 4
    arf ontology validate "(GPT-4, is_a, LLM)"
    arf benchmark --suite swarm --iterations 10

SDD Constitutional Requirement:
Every library MUST have a CLI for observability and testing.
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

CLI_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = CLI_ROOT.parent

for bootstrap_path in (WORKSPACE_ROOT, CLI_ROOT):
    bootstrap_str = str(bootstrap_path)
    if bootstrap_str not in sys.path:
        sys.path.insert(0, bootstrap_str)

# Main app
app = typer.Typer(
    name="arf",
    help="ARF CLI - FLOSSI0ULLK Agent Runtime Framework",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()


def _register_subcommands() -> None:
    """Import and attach subcommand apps after local path bootstrap."""
    from cli.benchmark import app as benchmark_app
    from cli.memory import app as memory_app
    from cli.ontology import app as ontology_app
    from cli.swarm import app as swarm_app

    app.add_typer(memory_app, name="memory", help="Conversation memory operations")
    app.add_typer(swarm_app, name="swarm", help="Pony swarm operations")
    app.add_typer(ontology_app, name="ontology", help="Ontology operations")
    app.add_typer(benchmark_app, name="benchmark", help="Benchmarking operations")


_register_subcommands()


@app.command()
def version():
    """Display the ARF CLI version and Python runtime."""
    from cli import __version__

    table = Table(title="ARF CLI Version")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")

    table.add_row("ARF CLI", __version__)
    table.add_row("Python", sys.version.split()[0])

    console.print(table)
    sys.exit(0)


@app.command()
def info():
    """Display system information and the status of key dependencies."""
    # Gather system info
    info_data = {
        "arf_version": "0.1.0",
        "python_version": sys.version.split()[0],
        "installation_path": str(Path(__file__).parent.parent),
        "available_commands": ["memory", "swarm", "ontology", "benchmark"],
    }

    # Check for key dependencies
    try:
        import numpy  # noqa: F401

        info_data["numpy_available"] = True
    except ImportError:
        info_data["numpy_available"] = False

    try:
        import sentence_transformers  # noqa: F401

        info_data["embeddings_available"] = True
    except ImportError:
        info_data["embeddings_available"] = False

    # Pretty print
    table = Table(title="ARF System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    for key, value in info_data.items():
        table.add_row(key.replace("_", " ").title(), str(value))

    console.print(table)
    sys.exit(0)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Suppress output except errors"
    ),
):
    """Initialize CLI-wide context flags before any subcommand runs."""
    # Store in context for subcommands
    ctx.obj = {
        "verbose": verbose,
        "quiet": quiet,
    }


def cli_main():
    """Run the Typer app with centralized CLI error handling."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)  # Standard Unix exit code for SIGINT
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
