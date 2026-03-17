# ARF CLI - FLOSSI0ULLK Agent Runtime Framework

A unified command-line interface for all ARF operations following Unix philosophy.

## Installation

```bash
# From the ARF directory
cd /path/to/FLOSS/ARF
pip install -e .
```

This installs the `arf` command globally.

## Quick Start

```bash
# Show help
arf --help

# Show version
arf version

# Show system info
arf info
```

## Commands

### Memory Operations

```bash
# Transmit understanding
arf memory transmit "GPT-4 is a large language model"

# Recall understandings
arf memory recall "LLM" --agent alice

# Show memory statistics
arf memory stats --agent alice

# Export memory
arf memory export --agent alice --output alice.json

# Compose memories from multiple agents
arf memory compose --agent main --with alice --with bob
```

### Swarm Operations

```bash
# Query the pony swarm
arf swarm query "What is 47 * 89?"

# Custom parameters (N=ponies, K=aggregation size, T=iterations)
arf swarm query "Explain recursion" --ponies 6 --iterations 4

# Show swarm info
arf swarm info
```

### Ontology Operations

```bash
# Validate a knowledge triple
arf ontology validate "(GPT-4, is_a, LLM)"

# List known predicates
arf ontology list-predicates

# Infer from triple
arf ontology infer "(GPT-4.5, improves_upon, GPT-4)"

# Show ontology info
arf ontology info
```

### Benchmarking

```bash
# Run memory benchmark
arf benchmark run --suite memory --iterations 10

# Run swarm benchmark
arf benchmark run --suite swarm --iterations 5

# Run all benchmarks
arf benchmark run --suite all

# List available suites
arf benchmark list-suites
```

## JSON Output Mode

All commands support `--json` for machine-readable output:

```bash
# Get JSON output
arf memory recall "test" --json

# Pipe to jq for processing
arf memory recall "test" --json | jq '.results[0].content'

# Use in scripts
COUNT=$(arf memory stats --json | jq '.understandings')
echo "Memory has $COUNT understandings"
```

## Common Options

- `--json`: Output as JSON for scripting
- `--agent AGENT_ID`: Specify agent ID (memory commands)
- `--backend BACKEND`: Specify backend: `file` or `holochain`
- `--verbose`, `-v`: Enable verbose output
- `--quiet`, `-q`: Suppress output except errors

## Exit Codes

- `0`: Success
- `1`: General error
- `130`: Interrupted by user (SIGINT)

## Testing

Run the integration test suite:

```bash
# Run all CLI tests
bash tests/test_cli.sh

# Run with verbose output
bash tests/test_cli.sh --verbose
```

## Man Page

View the manual page:

```bash
man ./man/arf.1
```

## Architecture

The CLI is structured as:

```
cli/
├── __init__.py       # Package initialization
├── main.py           # Main entry point and app setup
├── memory.py         # Memory subcommands
├── swarm.py          # Swarm subcommands
├── ontology.py       # Ontology subcommands
└── benchmark.py      # Benchmark subcommands
```

Each module is independently testable and follows the same pattern:
1. Accept arguments via Typer
2. Support `--json` output mode
3. Return appropriate exit codes
4. Use Rich for human-readable output

## Development

The CLI follows SDD (Specification-Driven Development) principles:

- **Code serves the spec**: Implementation follows roadmap exactly
- **Constitutional requirement**: Every library MUST have a CLI
- **Unix philosophy**: Composable, pipeable, transparent
- **Dual output modes**: Human-readable and JSON for automation

## Success Metrics (from Roadmap)

✅ All core operations accessible via CLI
✅ Exit codes follow Unix conventions (0=success)
✅ JSON output mode for all commands
✅ Man pages / help documentation
✅ Integration test coverage

## Examples from Roadmap

All examples from the Phase 4.2 roadmap are supported:

```bash
# Memory operations
arf memory transmit "GPT-4 is a LLM"
arf memory recall --agent alice --query "LLM"
arf memory compose --agent alice --with bob

# Swarm operations
arf swarm query "What is 47 * 89?" --ponies 4

# Ontology operations
arf ontology validate "(GPT-4, is_a, LLM)"
arf ontology infer --triple "(GPT-4.5, improves_upon, GPT-4)"

# Benchmarking
arf benchmark --suite swarm --iterations 10
```

## Next Steps

- Phase 4.4: Integration test suite (automated CI/CD)
- Phase 6: Metrics and observability
- Phase 7: Advanced inference engine

## Contributing

This CLI is part of the FLOSSI0ULLK project. See the main README for contribution guidelines.

## License

Compassion Clause or compatible FOSS license.
