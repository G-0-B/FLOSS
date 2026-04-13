# ADR-MCP-ORCHESTRATOR — MCP Server as Consensus Gate Orchestration Hub

| Field        | Value                                              |
|--------------|----------------------------------------------------|
| **Status**   | **Accepted** (amended 2026-04-12 — see Amendment section below) |
| **Date**     | 2025-06-15 (proposed); 2026-04-12 (amended, accepted) |
| **Authors**  | Anthony (project owner), FLOSSI0ULLK contributors  |
| **Deciders** | Anthony                                            |

---

## Amendment — 2026-04-12 (promotes Status from Proposed to Accepted)

The ADR is accepted in principle — the gateway exists and has passed live
end-to-end testing with real Cerebras + Groq voters (see
`C:\Users\kalis\.floss_agent\hook.log`). However, the **implemented shape
diverges from the Proposed shape in five load-bearing ways**, all of which
tighten rather than loosen the original decision drivers. This amendment is
the authoritative description of what was built; the Decision section below
is preserved as the original 2025-06-15 proposal for historical readability.

Read the rest of this ADR as "2025-06-15 plan" and this section as
"2026-04-12 reality." The gap between them is the project's learning.

### Divergence 1 — State substrate: cell source chain, not in-memory dicts

**Proposed:** `ConsensusGateServer` dataclass holding `claims`, `votes`,
`decisions`, `voter_configs` as in-memory Python dicts, with SQLite as a
hypothetical v2.

**Shipped:** Stateless `GatewayTools`
(`packages/metacoordinator_mcp/tools.py:74`) whose only state is a
`CellDirectory` (`packages/source_chain/cell.py`) — a file-based,
append-only source chain that maps 1:1 onto Holochain source chain actions.
Every Claim, Vote, and Decision is a JSON entry on disk under
`<base_dir>/cells/<dna_hash>/source_chain/<sha256>.json`, linked by
`previous_hash`. Entry names are the SHA256 of their canonical serialization,
writes are atomic via `open(path, "x")`, and topological order is recovered
by walking previous_hash links (no sequential prefixes).

**Why the change:** The "v1 in-memory → v2 maybe SQLite" plan kicked the
Holochain-compatibility problem down the road. Going straight to a
cell-shaped on-disk chain means Phase 1 (live Holochain) requires zero
structural rework — each file on disk becomes a source chain action with
the same hash-linked topology and the same author-DID attribution. This
also collapses the "ephemeral state on restart" bullet from the original
Negative consequences list: consensus rounds are now durable evidence, not
scratch memory, which matters for voter provenance audits.

### Divergence 2 — Tool surface: 6 tools, not 5; override removed; read queries added

**Proposed tool list:** `submit_claim`, `run_consensus_round`, `cast_vote`,
`read_decision`, `override_decision`.

**Shipped tool list** (`packages/metacoordinator_mcp/server.py:38-98`):

| Tool                  | vs. Proposal                  | Notes                                                              |
|-----------------------|-------------------------------|--------------------------------------------------------------------|
| `submit_claim`        | as proposed                   | Appends a Claim entry; does NOT fan out to voters — see Divergence 3 |
| `cast_vote`           | as proposed                   | Appends a Vote entry under the voter's DID                          |
| `run_consensus_round` | as proposed, explicitly invoked | Only path that calls voters — see Divergence 3                     |
| `get_decision`        | renamed from `read_decision`  | Scans chain for newest matching decision entry                      |
| `get_chain_context`   | **new**                       | Read-only windowed chain query for LLM voter context                |
| `list_pending`        | **new**                       | Returns claims with no matching decision entry                      |
| ~~`override_decision`~~ | **removed**                 | Governance overrides are themselves Claims (see below)              |

**Why the changes:**

- `get_chain_context` and `list_pending` fell out naturally from the
  file-based source chain — once state lives on disk as typed entries,
  read queries are trivial. Voters benefit from seeing prior chain activity
  before casting a weight, and external agents can discover which claims
  still need votes without polling individual `get_decision` calls.
- `override_decision` was removed because it would have introduced a
  privileged write path that directly contradicts the passive-router
  property (root `CLAUDE.md`: "it does not decide outcomes or command
  voters"). An override should itself be a new Claim — of `proposal_type`
  `AdrChange` or similar — that goes through its own consensus round. The
  policy for overriding a decision thus stays uniform with the policy for
  making any other decision: write it to the chain, let voters weigh in.

### Divergence 3 — `submit_claim` is passive; `run_consensus_round` is explicit and separate

**Proposed (Pattern A in the Decision section):** `run_consensus_round`
would be the server's primary mode — fan out to all registered voters with
`asyncio.gather()`, tally, return decision. Treated as the normal path for
every multi-model round triggered by a claim submission.

**Shipped:** `submit_claim` writes the Claim entry and returns a `claim_id`
**immediately**, with no voting, no side effects beyond the one append.
`run_consensus_round(claim_id)` is a **completely separate** tool that must
be explicitly invoked, and which then:

1. Reads the claim from the chain (or errors `E_CLAIM_NOT_FOUND`).
2. Refuses to re-run if a decision already exists (`E_ALREADY_DECIDED`) —
   mandatory on an append-only chain, because a stale re-run would produce
   duplicate votes with conflicting weights and confuse anyone tallying.
3. Lazy-imports `voters.py` on first call so test harnesses that never
   exercise this path never need `litellm` installed — the sync/async and
   dependency-weight costs are paid only by the code path that actually
   hits the network.
4. Calls the pure `decide(claim, voters)` from `consensus_gate.py`
   synchronously (see Divergence 4).
5. Appends each Vote under the voter's own DID, then the Decision under
   the `"metacoordinator"` system DID.

The live end-to-end pipeline crosses the submit→round seam via a **detached
subprocess**: `scripts/hook_post_write.py` (the PostToolUse hook) calls
`submit_claim` inline inside its ~100 ms budget, then `Popen`s
`scripts/hook_bg_round.py` with `DETACHED_PROCESS | CREATE_NO_WINDOW` on
Windows (`start_new_session=True` on POSIX) so the consensus round runs
entirely off the user's critical path.

**Why the change:** This is the "router not controller" framing from the
root `CLAUDE.md` taken literally. Pattern A conflated "a Claim arrived" with
"it's time to vote" — but those are two different decisions, often made by
different agents, and worth auditing separately. Splitting them means any
agent (human, hook, Claude, Horde.AI, a Holochain integrity zome) can drop
a Claim onto the chain without implicitly committing to who votes on it or
when. The consensus round becomes a discrete, idempotent, individually
auditable operation. This also makes recovery trivial: if the bg round
crashes, the Claim is still on the chain and can be re-run by calling
`run_consensus_round` manually; nothing has to be reconstructed from
volatile state.

### Divergence 4 — Synchronous `decide()`, no `asyncio.gather()` bypass

**Proposed:** Use `asyncio.gather()` to fan out to voters in parallel, then
call `tally()` directly to bypass the sync-only `decide()` signature. Listed
in the original Negative consequences as a mitigation for the "sync Voter
interface" limitation.

**Shipped:** `run_consensus_round` calls `decide(claim, voters)` **synchronously**
(`tools.py:298`). Voters are plain sync callables, each making its own
blocking `litellm.completion()` call. A full 3-voter round takes ~6–8
seconds wall-clock (observed hook.log latencies: 6146 ms, 6597 ms, 7452 ms,
8414 ms), entirely acceptable because the whole round runs in the detached
background subprocess from Divergence 3 — the user never waits for it.

**Why the change:** The `asyncio.gather() + tally()` bypass was a premature
optimization. Moving to parallel would complicate the sync/async boundary
(voters.py would need to be async, which means test harnesses need
`pytest-asyncio`, which means the "lazy import to skip litellm in tests"
trick gets harder) without material user benefit, because the whole round
is already off the critical path. The simpler shape actually satisfies the
"preserve core purity" decision driver (#1) by a wider margin than the
proposal assumed: `decide()` and `tally()` remain pure, sync, and trivially
testable, and the MCP server adds zero async machinery on top.

### Divergence 5 — Vote model: analog [−0.999, +0.999] with per-blast-radius thresholds

**Proposed:** The ADR was silent on the specific weight domain and tally
threshold logic — it described `Voter = Callable[[Claim], Vote]` and
treated `tally()` as a pure function without pinning down what vote weights
or acceptance thresholds actually look like. The prototype orchestrator
that existed at the time of the 2025-06-15 proposal used a coarse
placeholder — effectively a {−1, 0, +1} ternary — which was enough to
exercise the signatures but not enough to express variance as a
first-class signal.

**Shipped:** The orchestrator core (`packages/orchestrator/claim_schema.py`,
`consensus_gate.py`, `test_consensus_gate.py`) was extended in the same
pass that built the gateway, implementing the full analog vote model from
`docs/specs/consensus-gate.spec.md` §4.3. Concretely:

- **`CERTAINTY_LIMIT = 0.999`** defines the closed interval `[−0.999, +0.999]`
  as the valid `Vote.weight` domain. Absolute ±1.0 is deliberately forbidden
  because absolute certainty is incompatible with the consensus model —
  every vote must leave room for update. `_parse_weight()` in `voters.py`
  clamps naive ±1.0 output from models back into the open-at-the-extremes
  domain rather than erroring.
- **Per-blast-radius tally thresholds** (`APPROVE_THRESHOLD`,
  `REJECT_THRESHOLD` dicts in `claim_schema.py`): Local claims approve at
  mean ≥ +0.30, Module at ≥ +0.50, System at ≥ +0.60, Substrate at ≥ +0.85.
  Threshold escalates with blast radius so a high-stakes change needs
  a stronger consensus than a local one.
- **New `CONFLICT` outcome** on the `Outcome` enum, alongside `APPROVED`,
  `DEFERRED`, `REJECTED`, `OVERRIDDEN`. Used when the tally mean sits in
  the undecided band but variance is high enough that voters were not
  merely abstaining — they actively disagreed.
- **`QUORUM_MIN`, `POLARIZATION_THRESHOLD`, `OVERRIDE_ALLOWED`** constants
  wire these thresholds into `decide()`'s accept/reject/defer/conflict
  logic without hardcoding any numbers inside the function body.

**Why the change:** The analog model is what the spec actually called for
(§4.3); the placeholder ternary could not have expressed variance `0.009`
vs `0.309` as distinguishable signals. Without analog weights, the live
E2E runs below would all look the same — every round would round to
either +1, 0, or −1 per voter, and the Decision surface would lose exactly
the nuance that makes a multi-model consensus gate more informative than
a single-model call. Bundling the implementation with the gateway work
means the first live round ran against real math rather than against the
placeholder.

**API surface was preserved:** `Voter = Callable[[Claim], Vote]` is
unchanged; `decide()` and `tally()` kept their signatures. This is why the
metacoordinator_mcp package compiled against the extended core without a
single import change — the "preserve core purity" decision driver (#1)
still holds, but *purity* here means "the interface is pure and stable
while the semantics have become richer." That is a stronger property than
"nothing changed" — it is the testable guarantee that downstream callers
never had to know the core was rebuilt underneath them.

### Live E2E evidence (as of 2026-04-12)

The pipeline has been exercised end-to-end with a real voter roster
(Cerebras Llama 3.1 8B + Groq GPT-OSS 20B + Groq Qwen3 32B):

- Hook log: `C:\Users\kalis\.floss_agent\hook.log`
- Example successful round: claim `019d849c-31a9-7860-94e0-821569737984` →
  APPROVED, mean +0.933, variance 0.009, 7452 ms — triggered by edit to
  `packages/orchestrator/__init__.py`.
- Example successful round: claim `019d849c-5465-76c4-8b15-f25dab2a3b26` →
  APPROVED, mean +0.600, variance 0.020, 6146 ms — triggered by edit to
  `packages/source_chain/__init__.py`.
- Example DEFERRED round: claim `019d8457-5a0a-7d41-865f-4f9a49d33fe9` →
  mean +0.267, variance 0.309 (one voter at −0.50). Confirms voters
  discriminate on content rather than rubber-stamping.

### Files of record

| File | Role |
|------|------|
| `packages/metacoordinator_mcp/tools.py` | `GatewayTools` — stateless handlers for the 6 MCP tools |
| `packages/metacoordinator_mcp/server.py` | FastMCP wrapper binding the tools to stdio transport |
| `packages/metacoordinator_mcp/voters.py` | LiteLLM voter adapters; default roster built by `build_default_voters` |
| `packages/source_chain/cell.py` | `CellDirectory` — file-based append-only source chain |
| `packages/orchestrator/consensus_gate.py` | `decide()` / `tally()` — signatures unchanged from proposal; internally extended to the analog vote model (Divergence 5) |
| `packages/orchestrator/claim_schema.py` | Dataclasses for Claim / Vote / Decision — extended with `CERTAINTY_LIMIT`, per-blast-radius tally thresholds, `CONFLICT` outcome (Divergence 5) |
| `packages/orchestrator/test_consensus_gate.py` | Unit tests covering the analog tally thresholds and the `CONFLICT` branch |
| `scripts/hook_post_write.py` | PostToolUse hook: calls `submit_claim` inline, spawns bg round |
| `scripts/hook_bg_round.py` | Detached subprocess: calls `run_consensus_round` |
| `.claude/settings.json` (root + `FLOSS/`) | Wires the PostToolUse hook to `Write\|Edit\|MultiEdit` |
| `.mcp.json` (root + `FLOSS/`) | Declares the `flossiullk-consensus` MCP server for session-scoped launches |

### What this amendment does NOT change

The original decision drivers (preserve core purity, multi-client access,
multi-model voting, incremental complexity, Anthony's Option B directive)
all still hold — this amendment tightens them. The Alternatives Considered
section (Option A thin wrapper, Option C REST) remains rejected on the
same grounds. The boundary with Holochain (Seam 2 in ADR-6) is unchanged:
the MCP server still only imports `claim_schema` and `consensus_gate` from
the orchestrator package, and Holochain integration remains an orthogonal
concern that may consume these tools independently.

---

## Context

### Problem Statement

FLOSSI0ULLK requires a multi-model AI orchestration layer where every participating
model both **proposes** claims and **votes** on them. The consensus gate
(`packages/orchestrator/`) already provides the core logic for this, but it exists
as a standalone Python library with no network-facing interface. We need to expose
it as a service that Claude Code, other MCP clients, and eventually Holochain
agents can interact with.

### Current State

- **Consensus gate** (`packages/orchestrator/`) has a clean, minimal API:
  - `Voter = Callable[[Claim], Vote]` — any callable that scores a claim
  - All types (`Claim`, `Vote`, `Decision`) are JSON-serializable via `dataclasses.asdict()`
  - `tally(votes: list[Vote]) -> Decision` is a **pure function** (no side effects)
  - `decide(claim: Claim, voters: list[Voter]) -> Decision` is **stateless** (calls voters, then tally)
- **32/32 tests passing** on Python 3.13.1 — the core is stable
- **LiteLLM** provides a unified API for routing to multiple model providers
  (Anthropic, OpenAI, Gemini, DeepSeek, Ollama) via a single `completion()` call
- **MCP (Model Context Protocol)** is the emerging standard for tool-use between
  AI models and external services

### Decision Drivers

1. **Preserve core purity** — consensus gate must remain stateless and testable
2. **Multi-client access** — Claude Code, VS Code agents, CLI tools, future Holochain
   agents all need to participate in consensus rounds
3. **Multi-model voting** — a single round should fan out to N models in parallel
4. **Incremental complexity** — v1 can use in-memory state; persistence is v2
5. **Anthony's directive** — Option B (MCP Server as Orchestration Hub with LiteLLM
   routing inside) was explicitly approved over Option A (thin MCP wrapper + external
   orchestration)

---

## Decision

Build **`packages/metacoordinator-mcp/`** as an MCP server that wraps the consensus
gate and adds orchestration capabilities via LiteLLM.

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  MCP Clients (Claude Code, VS Code, CLI, etc.)      │
└──────────────────────┬──────────────────────────────┘
                       │ MCP Protocol (stdio/SSE)
                       ▼
┌─────────────────────────────────────────────────────┐
│  metacoordinator-mcp                                │
│  ┌───────────────────────────────────────────────┐  │
│  │ ConsensusGateServer                           │  │
│  │  - claims: dict[str, Claim]                   │  │
│  │  - votes: dict[str, list[Vote]]               │  │
│  │  - decisions: dict[str, Decision]             │  │
│  │  - voter_configs: dict[str, VoterConfig]      │  │
│  └───────────┬───────────────┬───────────────────┘  │
│              │               │                      │
│  ┌───────────▼───────┐ ┌────▼──────────────────┐   │
│  │ consensus_gate.py │ │ make_litellm_voter()  │   │
│  │  tally()          │ │  LiteLLM completion() │   │
│  │  decide()         │ │  asyncio.gather()     │   │
│  └───────────────────┘ └───────────────────────┘   │
│              │                    │                  │
│  ┌───────────▼────────────────────▼─────────────┐   │
│  │ claim_schema.py (Claim, Vote, Decision)      │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### MCP Tools Exposed (5 total)

| Tool                   | Description                                         | Core Function Used    |
|------------------------|-----------------------------------------------------|-----------------------|
| `submit_claim`         | Register a new claim for voting                     | Claim constructor     |
| `run_consensus_round`  | Execute a full multi-model vote on a claim           | tally() + gather()    |
| `cast_vote`            | Submit an individual vote from an external caller    | Vote constructor      |
| `read_decision`        | Retrieve the decision for a given claim              | dict lookup           |
| `override_decision`    | Manually override a decision (admin/governance)      | Decision constructor  |

### Voting Patterns

**Pattern A — Server-Orchestrated (multi-model rounds):**

```python
# Server holds registered LiteLLM voters
voters = [make_litellm_voter(cfg) for cfg in voter_configs.values()]

# Fan out to all models in parallel, collect votes
votes = await asyncio.gather(*[voter(claim) for voter in voters])

# Pure tally — bypasses decide() to avoid sync limitation
decision = tally(votes)
```

Key insight: We bypass `decide()` and call `tally()` directly. This lets us use
`asyncio.gather()` for parallel model invocation while keeping `tally()` pure.

**Pattern B — Caller-Orchestrated (external vote collection):**

```python
# External callers submit votes one at a time via cast_vote
votes_for_claim = votes_store[claim_id]
votes_for_claim.append(incoming_vote)

# When quorum is met, server tallies
if len(votes_for_claim) >= quorum:
    decision = tally(votes_for_claim)
```

Both patterns use the **same `tally()` function** — the only difference is who
collects the votes.

### State Management (v1)

```python
@dataclass
class ConsensusGateServer:
    claims: dict[str, Claim] = field(default_factory=dict)
    votes: dict[str, list[Vote]] = field(default_factory=dict)
    decisions: dict[str, Decision] = field(default_factory=dict)
    voter_configs: dict[str, VoterConfig] = field(default_factory=dict)
```

- **v1**: In-memory dicts — state lost on restart (acceptable for development)
- **v2** (optional): SQLite backend behind the same interface — swap storage without
  touching MCP tools or consensus logic

### Boundary with Holochain

The Holochain connector is **orthogonal** to this MCP server. The MCP server only
imports:
- `claim_schema.py` — data types
- `consensus_gate.py` — `tally()` and `decide()`

Holochain integration (Seam 2 in ADR-6) is a separate concern that may consume
MCP tools or import the same core modules independently.

---

## Consequences

### Positive

- **Clean separation**: MCP server wraps but never modifies consensus gate core
- **Zero regression risk**: Existing 32/32 tests remain unaffected — new package,
  new test suite
- **Universal access**: Any MCP-compatible client can participate in consensus rounds
- **Model-agnostic**: LiteLLM handles provider routing; adding a new model is a
  config change, not a code change
- **Testable in isolation**: `ConsensusGateServer` can be unit-tested without MCP
  transport, LiteLLM voters can be mocked

### Negative

- **Ephemeral state**: In-memory storage means state is lost on server restart
  (acceptable for v1 — consensus rounds are short-lived by design)
- **Sync Voter interface**: The core `Voter = Callable[[Claim], Vote]` signature
  is synchronous, which limits direct use with async I/O (mitigated by the
  `asyncio.gather() + tally()` pattern that bypasses `decide()`)
- **Additional deployment surface**: One more process to run alongside the core
  orchestrator

### Risks

| Risk                                  | Likelihood | Impact | Mitigation                                    |
|---------------------------------------|------------|--------|-----------------------------------------------|
| Python MCP SDK instability on Windows | Medium     | Medium | Pin SDK version, test on Windows CI           |
| LiteLLM version breaking changes      | Low        | Medium | Pin version, wrap in adapter layer            |
| Slow model responses causing timeouts | Medium     | Low    | Configurable watchdog timeout per voter       |
| State loss during active consensus    | Low        | Low    | Rounds complete in seconds; retry is cheap    |

---

## Alternatives Considered

### Option A — Thin MCP Wrapper + External Orchestration

MCP server only exposes `tally()` and `decide()` as passthrough tools. All
orchestration (model routing, vote collection, quorum logic) lives in the caller.

**Rejected because:** Pushes complexity to every client. Each MCP client would need
to independently implement LiteLLM routing, parallel voting, and quorum tracking.
Violates DRY across the ecosystem.

### Option C — REST API Instead of MCP

Standard HTTP/REST server with OpenAPI spec.

**Rejected because:** MCP is the native protocol for Claude Code and emerging AI
tool ecosystems. REST would require bridging for the primary use case. MCP can
always be wrapped in REST later if needed (not vice versa without friction).

---

## References

- **Audit**: `Folders/flossi0ullk-orchestration/AUDIT.md` — full API surface analysis
  of consensus gate, all type signatures, test coverage
- **ADR-6**: Four-system integration strategy — Seam 1 = Consensus Gate, defines
  the boundary this MCP server sits on
- **MCP Specification**: https://modelcontextprotocol.io — protocol definition,
  transport options (stdio, SSE), tool schema format
- **LiteLLM Documentation**: https://docs.litellm.ai — unified completion API,
  supported providers, async usage patterns
- **Python MCP SDK**: https://github.com/modelcontextprotocol/python-sdk — server
  implementation reference

---

## Implementation Notes

> These are non-normative hints for the implementer — see DESIGN.md (forthcoming)
> for the full specification.

1. Start with `mcp.server.Server` from the Python SDK, stdio transport
2. Implement `ConsensusGateServer` as a plain dataclass — no framework dependencies
3. `make_litellm_voter(config: VoterConfig) -> Voter` is the only LiteLLM touchpoint
4. Each MCP tool handler is a thin adapter: parse args → call server method → return JSON
5. Tests: mock LiteLLM responses, test ConsensusGateServer in isolation, then MCP
   integration tests with in-process client
