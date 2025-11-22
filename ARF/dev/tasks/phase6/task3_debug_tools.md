# Task 6.3: Debugging Tooling

**Phase**: 6 (Observability)
**Priority**: Low
**Goal**: Create CLI tools for debugging distributed systems.

## Objective
Provide developers with easy-to-use CLI commands to inspect the internal state of agents, replay conversations, and visualize the ontology.

## Requirements
1.  **CLI Extensions**:
    - Add `arf debug` subcommand group.
2.  **Features**:
    - `arf debug memory`: Dump memory state, show embeddings.
    - `arf debug replay`: Replay a session step-by-step (simulated).
    - `arf debug ontology`: Visualize the knowledge graph (e.g., export to DOT/SVG).
    - `arf debug trace`: Run a query with verbose tracing output.

## Implementation Steps
1.  Update `ARF/cli/main.py` (or create `ARF/cli/debug.py`).
2.  Implement `memory_dump` command.
3.  Implement `replay_session` command using `ConversationMemory` history.
4.  Implement `visualize_ontology` using `networkx` or similar (optional).

## Success Criteria
- [ ] `arf debug memory` shows JSON dump of agent memory.
- [ ] `arf debug replay` can re-run a sequence of inputs.
- [ ] Tools are accessible via the main `arf` CLI.
