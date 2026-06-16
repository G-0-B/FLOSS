"""
ARF CLI - Ontology subcommands

Ontology validation and inference operations.
All commands support --json output mode for scripting.

Examples:
    arf ontology validate "(GPT-4, is_a, LLM)"
    arf ontology infer --triple "(GPT-4.5, improves_upon, GPT-4)"
    arf ontology list-predicates --json
"""

import json
import re
import sys
from pathlib import Path
from typing import Tuple

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


app = typer.Typer(help="Ontology operations")
console = Console()


def parse_triple(triple_str: str) -> Tuple[str, str, str]:
    """Parses a string representation of a knowledge triple.

    This utility function is used by the CLI commands to convert a user-provided
    string in the format "(subject, predicate, object)" into a tuple of three
    strings.

    Args:
        triple_str: The string to parse.

    Returns:
        A tuple containing the subject, predicate, and object.

    Raises:
        ValueError: If the string is not in the expected format.
    """
    # Match pattern: (subject, predicate, object)
    pattern = r"\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)"
    match = re.match(pattern, triple_str.strip())

    if not match:
        raise ValueError(
            "Invalid triple format: "
            f"{triple_str}. Expected: (subject, predicate, object)"
        )

    return (
        match.group(1).strip(),
        match.group(2).strip(),
        match.group(3).strip(),
    )


@app.command()
def validate(
    triple: str = typer.Argument(
        ..., help="Triple to validate: (subject, predicate, object)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Validates a knowledge triple against the shared ontology.

    This command provides a direct way to check if a semantic statement in the
    form of a (subject, predicate, object) triple is consistent with the
    project's defined ontology. It is a key tool for ensuring the coherence and
    integrity of the knowledge base, in line with the "Light" and "Knowledge"
    principles.
    """
    try:
        # Parse triple
        subject, predicate, obj = parse_triple(triple)

        # Create a temporary memory instance for validation
        ConversationMemory = _get_conversation_memory()
        memory = ConversationMemory(agent_id="validator", validate_ontology=True)

        # Validate using the internal method
        is_valid, error_msg, _ = memory.validate_triple((subject, predicate, obj))

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "valid": is_valid,
                        "triple": {
                            "subject": subject,
                            "predicate": predicate,
                            "object": obj,
                        },
                        "error": error_msg,
                    }
                )
            )
        else:
            if is_valid:
                console.print("[green]✓ Valid triple[/green]")
                console.print(f"  Subject: {subject}")
                console.print(f"  Predicate: {predicate}")
                console.print(f"  Object: {obj}")
            else:
                console.print("[red]✗ Invalid triple[/red]")
                console.print(f"  Error: {error_msg}")
                console.print(f"  Triple: ({subject}, {predicate}, {obj})")

        sys.exit(0 if is_valid else 1)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command()
def infer(
    triple: str = typer.Argument(
        ..., help="Triple for inference: (subject, predicate, object)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Performs inference based on a given knowledge triple.

    This command is a placeholder for the future symbolic reasoning capabilities
    of the ARF. Currently, it validates the provided triple and, if valid,
    stores it in the conversation memory for later processing by a full-fledged
    inference engine. This serves as a forward-looking interface for the project's
    long-term "Knowledge" and "Federated Reasoning" goals.
    """
    try:
        # Parse triple
        subject, predicate, obj = parse_triple(triple)

        # For now, just validate (full inference in Phase 7)
        ConversationMemory = _get_conversation_memory()
        memory = ConversationMemory(agent_id="inference", validate_ontology=True)
        is_valid, error_msg, _ = memory.validate_triple((subject, predicate, obj))

        if not is_valid:
            if json_output:
                print(
                    json.dumps(
                        {
                            "success": False,
                            "error": f"Invalid triple: {error_msg}",
                        }
                    )
                )
            else:
                console.print("[red]✗ Cannot infer from invalid triple[/red]")
                console.print(f"  Error: {error_msg}")
            sys.exit(1)

        # Store as understanding (inference engine will process later)
        content = f"{subject} {predicate.replace('_', ' ')} {obj}"
        ref = memory.transmit({"content": content})

        if json_output:
            print(
                json.dumps(
                    {
                        "success": True,
                        "triple": {
                            "subject": subject,
                            "predicate": predicate,
                            "object": obj,
                        },
                        "stored_ref": ref,
                        "note": "Full inference engine coming in Phase 7",
                    }
                )
            )
        else:
            console.print("[green]✓ Triple validated and stored[/green]")
            console.print(f"  ({subject}, {predicate}, {obj})")
            console.print("  [dim]Note: Full inference engine coming in Phase 7[/dim]")

        sys.exit(0)

    except Exception as e:
        if json_output:
            print(json.dumps({"success": False, "error": str(e)}))
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@app.command(name="list-predicates")
def list_predicates(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Lists all the known predicates in the shared ontology.

    This command provides a simple way to discover the valid relationships that can
    be used in knowledge triples. It is a practical tool for developers and users
    who are working with the ontology, promoting transparency and ease of use.
    """
    # Known predicates (synchronized with ontology_integrity/src/lib.rs)
    predicates = [
        "is_a",
        "part_of",
        "related_to",
        "has_property",
        "improves_upon",
        "capable_of",
        "trained_on",
        "evaluated_on",
        "stated",
    ]

    if json_output:
        print(
            json.dumps(
                {
                    "success": True,
                    "count": len(predicates),
                    "predicates": predicates,
                }
            )
        )
    else:
        table = Table(title="Known Ontology Predicates")
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Predicate", style="green")

        for i, pred in enumerate(predicates, 1):
            table.add_row(str(i), pred)

        console.print(table)

    sys.exit(0)


@app.command()
def info():
    """Displays high-level information about the ontology system.

    This command provides a status overview of the ontology system, including the
    backend in use, the number of known predicates, and the status of the
    inference engine. It is a convenient way to get a quick snapshot of the
    ontology's configuration.
    """
    table = Table(title="Ontology System Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Backend", "File (Holochain integration in progress)")
    table.add_row("Validation", "Active")
    table.add_row("Predicates", "9 base predicates")
    table.add_row("Inference Engine", "Phase 7 (planned)")

    console.print(table)
    console.print("\n[dim]For full symbolic reasoning, see Phase 7 roadmap[/dim]")

    sys.exit(0)


if __name__ == "__main__":
    app()
