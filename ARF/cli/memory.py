"""
ARF CLI - Memory subcommands

Conversation memory operations following Unix philosophy.
All commands support --json output mode for scripting.

Examples:
    arf memory transmit "GPT-4 is a LLM"
    arf memory recall --agent alice --query "LLM"
    arf memory compose --agent alice --with bob
    arf memory stats --json
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.table import Table

CLI_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = CLI_ROOT.parent

for bootstrap_path in (WORKSPACE_ROOT, CLI_ROOT):
    bootstrap_str = str(bootstrap_path)
    if bootstrap_str not in sys.path:
        sys.path.insert(0, bootstrap_str)


def _get_conversation_memory():
    """Import ConversationMemory lazily after local path bootstrap."""
    from conversation_memory import ConversationMemory

    return ConversationMemory


app = typer.Typer(help="Conversation memory operations")
console = Console()


@app.command()
def transmit(
    content: str = typer.Argument(..., help="Understanding content to transmit"),
    agent: str = typer.Option("default", "--agent", "-a", help="Agent ID"),
    context: Optional[str] = typer.Option(
        None, "--context", "-c", help="Context for understanding"
    ),
    is_decision: bool = typer.Option(
        False, "--decision", "-d", help="Mark as decision (ADR)"
    ),
    coherence: float = typer.Option(
        0.0, "--coherence", help="Coherence score [0.0-1.0]"
    ),
    skip_validation: bool = typer.Option(
        False, "--skip-validation", help="Skip ontology validation"
    ),
    backend: str = typer.Option(
        "file", "--backend", "-b", help="Backend: file or holochain"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Transmits a moment of understanding to an agent's conversation memory.

    This command is the primary interface for adding new knowledge to the system.
    It allows for the creation of new `Understanding` objects, which can be
    optionally marked as architectural decisions (ADRs) and validated against
    the shared ontology. This command is a direct implementation of the "memetic
    transmission" concept central to the FLOSSI0ULLK ecosystem.
    """
    try:
        # Initialize memory
        ConversationMemory = _get_conversation_memory()
        memory = ConversationMemory(agent_id=agent, backend=backend)

        # Build understanding dict
        understanding = {
            "content": content,
            "coherence": coherence,
        }

        if context:
            understanding["context"] = context

        if is_decision:
            understanding["is_decision"] = True

        # Transmit
        ref = memory.transmit(understanding, skip_validation=skip_validation)

        if ref is None:
            if json_output:
                print(json.dumps({"success": False, "error": "Validation failed"}))
            else:
                console.print("[red]✗ Validation failed[/red]")
            sys.exit(1)

        # Output result
        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "ref": ref,
                        "agent": agent,
                        "content": content,
                    }
                )
            )
        else:
            console.print("[green]✓ Transmitted understanding[/green]")
            console.print(f"  Agent: {agent}")
            console.print(f"  Ref: {ref[:16]}...")
            if is_decision:
                console.print("  [bold]Marked as ADR[/bold]")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def recall(
    query: str = typer.Argument(..., help="Query to search for"),
    agent: str = typer.Option("default", "--agent", "-a", help="Agent ID"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
    backend: str = typer.Option(
        "file", "--backend", "-b", help="Backend: file or holochain"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Recalls relevant understandings from an agent's conversation memory.

    This command provides a way to search and retrieve knowledge that has been
    previously transmitted. It uses the multi-scale semantic search capabilities
    of the `ConversationMemory` to find the most relevant `Understanding` objects,
    helping to reduce "Cognitive Debt" by making past knowledge easily accessible.
    """
    try:
        # Initialize memory
        ConversationMemory = _get_conversation_memory()
        memory = ConversationMemory(agent_id=agent, backend=backend)

        # Recall
        results = memory.recall(query, top_k=top_k)

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "query": query,
                        "agent": agent,
                        "count": len(results),
                        "results": results,
                    }
                )
            )
        else:
            if not results:
                console.print(f"[yellow]No results found for query: {query}[/yellow]")
            else:
                console.print(
                    (
                        f"[green]Found {len(results)} result(s) "
                        f"for query: {query}[/green]\n"
                    )
                )

                for i, result in enumerate(results, 1):
                    console.print(
                        f"[bold cyan]{i}. From {result['agent_id']}[/bold cyan]"
                    )
                    if "relevance_score" in result:
                        console.print(f"   Relevance: {result['relevance_score']:.3f}")
                    console.print(f"   Content: {result['content']}")
                    if result.get("context"):
                        console.print(f"   Context: {result['context']}")
                    console.print()

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def compose(
    agent: str = typer.Option("default", "--agent", "-a", help="Target agent ID"),
    with_agents: List[str] = typer.Option(
        [], "--with", "-w", help="Source agent IDs to compose"
    ),
    backend: str = typer.Option(
        "file", "--backend", "-b", help="Backend: file or holochain"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Composes the memories from multiple source agents into a target agent.

    This command is a practical implementation of the "Federated Reasoning"
    principle. It allows for the creation of a collective intelligence by
    merging the knowledge of individual agents into a unified, more comprehensive
    memory. This is a key mechanism for building a shared understanding across
    the swarm.
    """
    try:
        if not with_agents:
            if json_output:
                print(
                    json.dumps(
                        {"success": False, "error": "No source agents specified"}
                    )
                )
            else:
                console.print(
                    "[red]Error: Specify at least one source agent with --with[/red]"
                )
            sys.exit(1)

        # Initialize target memory
        ConversationMemory = _get_conversation_memory()
        target_memory = ConversationMemory(agent_id=agent, backend=backend)

        # Compose from each source
        composed_count = 0
        for source_agent in with_agents:
            source_memory = ConversationMemory(agent_id=source_agent, backend=backend)
            export = source_memory.export_for_composition()
            target_memory.import_and_compose(export)
            composed_count += len(export["understandings"])

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "target_agent": agent,
                        "source_agents": with_agents,
                        "composed_understandings": composed_count,
                    }
                )
            )
        else:
            console.print(f"[green]✓ Composed memories into {agent}[/green]")
            console.print(f"  Sources: {', '.join(with_agents)}")
            console.print(f"  Understandings: {composed_count}")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def stats(
    agent: str = typer.Option("default", "--agent", "-a", help="Agent ID"),
    backend: str = typer.Option(
        "file", "--backend", "-b", help="Backend: file or holochain"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Displays statistics about an agent's conversation memory.

    This command provides observability into the state of an agent's memory,
    including the number of understandings, ADRs, and the results of validation
    attempts. This aligns with the "Light" principle of ULLK by making the
    internal state of the system transparent and auditable.
    """
    try:
        # Initialize memory
        ConversationMemory = _get_conversation_memory()
        memory = ConversationMemory(agent_id=agent, backend=backend)

        # Gather stats
        validation_stats = memory.get_validation_stats()
        num_understandings = len(memory.understandings)
        num_adrs = len(memory.adrs)

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "agent": agent,
                        "understandings": num_understandings,
                        "adrs": num_adrs,
                        "validation_stats": validation_stats,
                    }
                )
            )
        else:
            table = Table(title=f"Memory Statistics for {agent}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Understandings", str(num_understandings))
            table.add_row("ADRs", str(num_adrs))
            table.add_row("Total Validations", str(validation_stats["total_attempts"]))
            table.add_row("Passed", str(validation_stats["validation_passed"]))
            table.add_row("Failed", str(validation_stats["validation_failed"]))
            table.add_row("Skipped", str(validation_stats["validation_skipped"]))

            console.print(table)

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def export(
    agent: str = typer.Option("default", "--agent", "-a", help="Agent ID"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file (default: stdout)"
    ),
    backend: str = typer.Option(
        "file", "--backend", "-b", help="Backend: file or holochain"
    ),
):
    """Exports an agent's entire conversation memory to a JSON format.

    This command serializes the state of an agent's memory, including all
    understandings and the multi-scale embedding structure. The resulting output
    can be used for backup, analysis, or as the input for the `compose` command,
    enabling the sharing and merging of knowledge between agents.
    """
    try:
        # Initialize memory
        ConversationMemory = _get_conversation_memory()
        memory = ConversationMemory(agent_id=agent, backend=backend)

        # Export
        export_data = memory.export_for_composition()

        # Output
        json_str = json.dumps(export_data, indent=2)

        if output:
            Path(output).write_text(json_str)
            console.print(f"[green]✓ Exported memory to {output}[/green]")
        else:
            print(json_str)

        sys.exit(0)

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    app()
