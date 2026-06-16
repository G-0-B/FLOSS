# DESIGN.md — metacoordinator_mcp

> MCP server wrapping the FLOSSI0ULLK consensus gate as tools for AI agents.

---

## 1. Overview

`metacoordinator_mcp` is an MCP (Model Context Protocol) server that exposes the FLOSSI0ULLK consensus gate as a set of tools consumable by AI agents. It adds:

- **State management** — persistent tracking of claims, votes, decisions, and voter configurations
- **LiteLLM multi-model routing** — parallel invocation of diverse LLM voters (Claude, GPT-4o, Gemini, DeepSeek, Ollama locals)
- **stdio transport** — runs locally, no network surface; Claude Code and any MCP-compatible client can orchestrate consensus rounds directly

The core philosophy: **logic validates, neural assists — never the reverse.** The consensus gate is the substrate; LLMs are voters, not authorities.

---

## 2. Architecture

### Core Class

`ConsensusGateServer` — the stateful wrapper around the stateless `consensus_gate.py` functions.

```
Claude Code ──stdio──> ConsensusGateServer ──> consensus_gate.py (stateless)
                              │
                        ┌─────┴─────┐
                        │ In-Memory  │
                        │   Stores   │
                        ├────────────┤
                        │ claims     │  dict[str, Claim]
                        │ votes      │  dict[str, list[Vote]]
                        │ decisions  │  dict[str, Decision]
                        │ voter_cfgs │  dict[str, VoterConfig]
                        └────────────┘
```

### Data Flow

1. Client (Claude Code) sends MCP tool call via stdio
2. `ConsensusGateServer` receives, dispatches to handler
3. Handler interacts with in-memory stores + stateless `consensus_gate.py` functions
4. Response serialized as JSON, returned via stdio

### Key Principles

- **Stateless core + stateful server**: `consensus_gate.py` remains pure functions; server manages lifecycle
- **JSON-serializable throughout**: all data structures use `dataclasses.asdict()` for transport
- **Voter = Callable[[Claim], Vote]**: uniform interface whether voter is LLM, human, or rule-based
- **Thread safety**: `asyncio.Lock` guards all mutable state access

---

## 3. MCP Tools

### `submit_claim`

Creates a `Claim` object, stores it, returns the claim ID.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | The claim text to be evaluated |
| `metadata` | object (optional) | Arbitrary metadata attached to the claim |

Returns: `{ claim_id, status: "submitted", timestamp }`

### `run_consensus_round` (Pattern A — Server-Orchestrated)

Spawns LiteLLM voters in parallel via `asyncio.gather`, collects votes, calls `tally()` directly, returns a `Decision`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `claim_id` | string | ID of a previously submitted claim |
| `voter_ids` | list[string] (optional) | Specific voters to use; defaults to all configured |
| `timeout` | integer (optional) | Per-voter timeout in seconds; default 30 |

Returns: `Decision { claim_id, outcome, confidence, votes[], timestamp }`

### `cast_vote` (Pattern B — External Vote)

Accepts a single vote from an external source (human, another agent, rule engine). Auto-tallies when quorum is reached.

| Parameter | Type | Description |
|-----------|------|-------------|
| `claim_id` | string | ID of the claim being voted on |
| `voter_id` | string | Identity of the voter |
| `position` | enum | `agree` / `disagree` / `abstain` |
| `confidence` | float | 0.0 to 1.0 |
| `reasoning` | string | Justification for the vote |

Returns: `{ vote_recorded: true, votes_so_far, quorum_reached, decision? }`

### `read_decision`

Returns the current state of a claim and its decision (if reached).

| Parameter | Type | Description |
|-----------|------|-------------|
| `claim_id` | string | ID of the claim to query |

Returns: `{ claim, votes[], decision?, status }`

### `override_decision`

Admin override with full audit logging. For when the human needs to intervene.

| Parameter | Type | Description |
|-----------|------|-------------|
| `claim_id` | string | ID of the claim |
| `new_outcome` | enum | The overridden outcome |
| `reason` | string | Mandatory justification |
| `authority` | string | Who is overriding |

Returns: `{ overridden: true, audit_entry }`

---

## 4. LiteLLM Integration

### `make_litellm_voter` Adapter

Wraps `litellm.completion()` into the `Voter` callable interface:

```python
def make_litellm_voter(config: VoterConfig) -> Voter:
    async def voter(claim: Claim) -> Vote:
        response = await asyncio.to_thread(
            litellm.completion,
            model=config.model,
            messages=[
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": claim.content}
            ],
            **config.litellm_kwargs
        )
        return parse_vote(response, config)
    return voter
```

### Async Parallel Execution

All voters run concurrently via `asyncio.gather(*voter_tasks)`. Timeouts handled per-voter with `asyncio.wait_for`.

### `VoterConfig` Dataclass

```python
@dataclass
class VoterConfig:
    model: str              # LiteLLM model string
    system_prompt: str      # Voting instructions
    weight: float = 1.0     # Vote weight in tally
    timeout: int = 30       # Seconds
    litellm_kwargs: dict = field(default_factory=dict)
```

### Default Voters

| ID | Model String | Provider |
|----|-------------|----------|
| `claude` | `anthropic/claude-sonnet-4-20250514` | Anthropic |
| `gpt4o` | `openai/gpt-4o` | OpenAI |
| `gemini` | `google/gemini-2.0-flash` | Google |
| `deepseek` | `deepseek/deepseek-chat` | DeepSeek |
| `llama3` | `ollama/llama3` | Ollama (local) |

---

## 5. State Management

### v1: In-Memory (Current Target)

- Python dicts: `claims`, `votes`, `decisions`, `voter_configs`
- Thread safety via `asyncio.Lock`
- Volatile — state lost on server restart
- Sufficient for development and single-session workflows

### v2 Path: SQLite

- `aiosqlite` for async access
- Schema mirrors the dict structures
- Enables persistence across restarts
- Migration path: swap store implementations behind the same interface

### v3 Path: Holochain DHT

- MCP server becomes a read-through cache over DHT state
- Claims, votes, decisions become DHT entries
- Validation rules enforced at the zome level
- The endgame: fully decentralized consensus with local MCP as the access layer

---

## 6. AIngram/Agorai Integration Paths

This section maps the integration surface between metacoordinator_mcp and two related open-source projects.

### AIngram

[AIngram](https://github.com/StevenJohnson998/AIngram) is a 60-migration AGPL-3.0 production system implementing:

- **Commit-reveal formal voting** — SHA-256 hash commit phase, reveal phase, verify phase. Defense against vote-copying attacks.
- **6-state lifecycle FSM** — `proposed -> under_review -> published -> disputed -> retracted -> superseded`
- **Beta reputation + EigenTrust trust math** — sophisticated voter weighting based on historical accuracy
- **Progressive-disclosure MCP server** — 99 tools across 10 categories
- **Injection defense + quarantine stack** — production-grade security hardening

### Agorai

[Agorai](https://github.com/StevenJohnson998/Agorai) is a multi-agent collaboration MCP+CLI server featuring:

- Claude + Gemini adapters
- Keryx orchestrator for multi-agent workflows
- Shared memory across agent sessions

### Integration Paths (Ranked by Effort)

#### Path A: Satellite MCP (Lowest Effort)

Stand up AIngram via Docker, configure our gateway to treat it as an additional voter. AIngram's MCP tools become available alongside our native consensus tools.

- **Effort**: One afternoon
- **Benefit**: Immediate access to commit-reveal voting, reputation system
- **Risk**: Runtime dependency on Docker + AIngram service

#### Path B: Port Domain Modules to Python (Medium Effort)

Extract and port the core logic (~570 lines across 5 files):

1. `formal-vote` — commit-reveal protocol
2. `lifecycle` — 6-state FSM
3. `vote-weight` — weighted tallying
4. `trust` — EigenTrust implementation
5. `protocol` — wire format

- **Effort**: 1-2 weeks
- **Benefit**: Native integration, no runtime dependency
- **Blocker**: AGPL license cascade — needs ADR decision before proceeding

#### Path C: Rust Integrity Zomes (Highest Effort)

Implement the same logic as Holochain zomes in Rust for `ARF/dnas/rose_forest/`.

- **Effort**: Weeks to months
- **Depends on**: Path B (need working Python reference) + Rose Forest build infrastructure
- **Benefit**: Decentralized, cryptographically enforced consensus rules

#### Path D: Collaborate with Author (Social)

Reach out to Steven Johnson directly. Explore shared development, license compatibility, or upstream contributions.

- **Effort**: Variable (social action)
- **Benefit**: Potentially the highest-leverage path
- **Requires**: User decision and initiative

### Tensions

- **Substrate philosophy mismatch**: AIngram is Postgres-native; FLOSSI0ULLK targets Holochain DHT. Porting is not just translation.
- **AGPL cascade**: If we port AIngram code, AGPL may cascade to the entire metacoordinator. Needs legal/philosophical ADR.
- **EigenTrust in DHT**: Running EigenTrust over a DHT (vs centralized DB) is an open research question. No known production implementations.

---

## 7. Claude Code Integration

### MCP Configuration

In `.claude/settings.json`:

```json
{
  "mcpServers": {
    "metacoordinator": {
      "command": "python",
      "args": ["-m", "metacoordinator_mcp.server"],
      "cwd": "packages/metacoordinator_mcp"
    }
  }
}
```

### Trigger Patterns

Use consensus when the stakes justify multi-perspective evaluation:

- **Code review**: Submit architectural decisions as claims, let multiple models evaluate
- **Design decisions**: When tradeoffs are non-obvious, run a consensus round
- **Fact verification**: Claims about external systems or standards
- **Conflict resolution**: When different agents or models disagree

### Example Workflow

```
1. submit_claim("React Server Components should be used for the dashboard")
   -> claim_id: "abc123"

2. run_consensus_round(claim_id="abc123")
   -> Decision {
        outcome: "agree",
        confidence: 0.78,
        votes: [
          {voter: "claude", position: "agree", confidence: 0.9},
          {voter: "gpt4o", position: "agree", confidence: 0.7},
          {voter: "gemini", position: "disagree", confidence: 0.6},
          {voter: "deepseek", position: "agree", confidence: 0.8},
          {voter: "llama3", position: "agree", confidence: 0.7}
        ]
      }

3. Read gemini's dissent, iterate on the claim if needed
4. Proceed with confidence (or override if human judgment differs)
```

---

## 8. Test Plan

### Preserve Existing Tests

The 32 existing tests in `consensus_gate.py` (16/16 passing in two suites) must continue to pass. They validate the stateless core.

### New Test Suites

#### Unit Tests: ConsensusGateServer

- Claim CRUD operations
- Vote recording and quorum detection
- Decision computation correctness
- Override audit trail
- Concurrent access under asyncio.Lock

#### Integration Tests: LiteLLM

- `make_litellm_voter` produces valid Voter callables
- Parallel voter execution completes within timeout
- Graceful degradation when individual voters fail
- VoterConfig validation

#### MCP Protocol Tests

- Tool registration and discovery
- Request/response serialization
- Error handling for malformed requests
- stdio transport reliability

#### E2E Tests

- **Pattern A flow**: submit_claim -> run_consensus_round -> read_decision
- **Pattern B flow**: submit_claim -> cast_vote (x N) -> auto-tally on quorum -> read_decision
- **Mixed flow**: Pattern A + manual override
- **Failure modes**: voter timeout, network error, invalid claim ID

---

## 9. Open Questions

| Question | Options | Current Lean |
|----------|---------|--------------|
| Python environment | Native Windows vs WSL | Native (simpler for MCP stdio) |
| API key management | env vars vs .env vs keyring | env vars (v1), .env (v2) |
| Persistence strategy | in-memory vs SQLite vs DHT | in-memory (v1), SQLite (v2), Holochain (v3) |
| MCP protocol evolution | Track spec changes | Pin to current stable |
| Voter prompt engineering | Static vs dynamic prompts | Static (v1), claim-type-aware (v2) |
| AGPL license cascade | Accept vs isolate vs rewrite | Needs ADR — blocks Path B |
| EigenTrust feasibility | Research vs defer | Defer to v3 research phase |

---

*This document is a living design. Update it as decisions are made and implementation reveals new constraints.*

*Last updated: 2026-04-15*
