# ADR-19: OmniRoute Inference Plane + MCP Daemon Migration

**Date:** 2026-07-17
**Status:** Accepted (operator-consented, consensus-pending)
**Blast Radius:** System
**Truth Status:** Verified (Stages 0–3.5 implemented + tested; equivalence run closed 2026-07-26 — see Evidence, incl. two disclosed caveats)

**Consensus ratification: BLOCKED, not pending.** A System-radius `AdrChange` claim fails closed with `E_GOVERNED_PROVENANCE_REQUIRED` unless it carries `provenance_packet` evidence containing a `consent_ref.decision_action_hash`. No such convention exists yet: across 105 provenance packets in `.agent-surface/provenance/`, zero carry a `consent_ref`. `entry_has_consent()` only checks the field is a non-empty string — it does not resolve the hash — so the gate is trivially satisfiable by any value, which is precisely why it should not be satisfied ad hoc. Choosing what `decision_action_hash` anchors to is consent-gate design (ADR-12), and ADR-5's standing rule forbids starting that work silently. **Operator decision required.**

## Context

Each agent session (Claude Code, Codex, Gemini, OpenCode) was spawning 4 `npx -y januscope@latest` Node.js processes — each performing an npm registry version-check and potential re-download before any useful work. The two FLOSSI0ULLK Python MCP servers (consensus gateway + reasoning ensemble) used bare `mcp.run()` with stdio transport: a one-process-per-client model with no PID guard and no shutdown handling. With multiple concurrent agents this produced 12+ Node + 6+ Python processes that never died and sat spinning on idle stdin. The reasoning ensemble additionally hammered the same local Ollama server when multiple instances ran.

The operator stated pain (2026-07-17): *"each agent spawns 4 node.js and python scripts without process control, async eating CPU like cray cray."*

An external audit artifact (`.toilet/2026-7-17_OMNIROUTE_ARCHITECTURE_UPGRADE_MIGRATION.md`, by Perplexity External Reality Scout) proposed a migration. The audit had several factual errors (WSL2 assumption, lens configs untracked, deleting domain servers into OmniRoute) — corrected in the implementation plan at `docs/superpowers/plans/2026-07-17-omniroute-inference-plane-migration.md`.

## Decision

1. **Pin JanuScope globally** (`npm install -g januscope`) — eliminates `npx -y` version-check overhead on every spawn. JanuScope stays for external tools (serena, agentmemory) where we have no control over the downstream process.

2. **Daemonize both Python MCP servers** as persistent PID-guarded HTTP daemons on `127.0.0.1`:
   - Consensus gateway: `:7331/mcp` (streamable-http)
   - Reasoning ensemble: `:7332/mcp` (streamable-http)
   - Shared `packages/mcp_daemon.py` provides `claim_singleton()` (PID guard), `audit_appender()` (defense-in-depth audit), `run_http_daemon()` (loopback bind + transport).
   - Lens instruction injection moves from JanuScope YAML into `FastMCP(instructions=...)` — delivered to clients on `initialize`.
   - Windows-native `_pid_alive()` via `ctypes.OpenProcess` (os.kill unreliable on Windows).

3. **OmniRoute as the model-call plane** (flag-gated, reversible):
   - `FLOSS_MODEL_BACKEND=litellm` (default) | `omniroute`
   - Shared `packages/omniroute_client.py` provides OpenAI-compatible `completion()` + `embedding()` via httpx.
   - All 8 litellm call sites branch on the env flag. All parsing logic (`_strip_thinking`, `_parse_weight`, `_parse_rationale`) unchanged.
   - LiteLLM stays as the default until a live equivalence run proves OmniRoute is equivalent across all roster models.

4. **Boot-time launcher** (`scripts/start_mcp_daemons.ps1`) starts both daemons idempotently at logon via Windows Scheduled Task as `MSI\kalis`.

## Non-goals

- Deleting `server.py` / `mcp_server.py` — they stay as daemons (they encode FLOSSI0ULLK consensus/ensemble domain logic OmniRoute has no equivalent for).
- Replacing the consensus gate or reasoning-ensemble logic with OmniRoute Fusion.
- Binding any daemon to `0.0.0.0` or a non-loopback interface.
- Removing JanuScope for serena / agentmemory.

## Evidence

| Stage | Commit | Verification |
|---|---|---|
| 0: Pin JanuScope | `b371d15` (root) | `januscope --version` → 0.4.4 |
| 1.1: mcp_daemon.py | `7a6acc8` | 4/4 TDD tests passing |
| 1.2: Daemonize servers | `3d47cfc` | Live smoke: initialize + tools/list + singleton guard |
| 1.3: .mcp.json HTTP urls | `01bdeb8` (root) | Both JSON valid |
| 1.4: Boot launcher | `e508fee` | Script created (Scheduled Task registration pending) |
| 3.3: OmniRoute client | `cf89501` | 3/3 TDD tests passing |
| 3.4: Flag-gated routing | `258f0db` | 70/70 tests passing |
| Roster fix: qwen3.6-27b | `47ed474` | Live consensus round: APPROVED +0.533, all 3 voters functional |
| 3.5 Step 3: hook-path | — | 2026-07-24: `hook_bg_round.py` with `FLOSS_MODEL_BACKEND=omniroute` on claim `019f9697-734b-7b32-bf86-b81798a9cb7c` — round completed 10.4 s, 3/3 voters parseable, no `[voter error]` |
| 3.5 Steps 1–2: equivalence | — | 2026-07-26: `scripts/smoke_test_voters.py` both backends. litellm → weights −0.400/−0.400/−0.400, mean −0.4000, var 0.0000, 10844 ms. omniroute → identical weights, mean −0.4000, var 0.0000, 7033 ms. Both PASS; OmniRoute faster |
| 3.5 Step 4: flip default | — | `FLOSS/.env` sets `FLOSS_MODEL_BACKEND=omniroute` — OmniRoute is the live default |

**Stage 3.5 is now closed.** Truth Status for Stage 3.5 upgrades from *pending* to *Verified*, with two disclosed caveats:

1. **Prompt-bleed on the OmniRoute path.** In the equivalence run, voter `groq-qwen3-32b` emitted a style-prompt fragment inside its `RATIONALE` text instead of a clean rationale. The `WEIGHT` parsed correctly and the tally matched baseline exactly, so equivalence holds — but this artifact is not root-caused and does not occur on the litellm path.
2. **Single claim shape.** Equivalence was demonstrated on one claim (evidence-empty, unanimously rejected). It establishes weight and tally agreement across backends; it is not a multi-claim equivalence corpus.

Scheduled Task registration for the boot launcher remains unverified.

## Operator Consent

Anthony (kalisam) explicitly consented to this ADR on 2026-07-17: *"i definately consent to the adr 19 decision to go forthwith."*

## Consequences

- **Process count reduction**: 12+ Node + 6+ Python per session → 1 OmniRoute + 2 Python daemons + 2 pinned JanuScope (serena/agentmemory).
- **CPU relief**: No more npm version-check storms, no more idle-stdin spin, no more duplicate Ollama calls.
- **Guardrail preservation**: Lens instructions delivered via `FastMCP(instructions=...)`; audit logging preserved via `audit_appender()`.
- **Reversibility**: `FLOSS_MODEL_BACKEND=litellm` restores the original path. `.mcp.json` can be reverted to subprocess mode. `mcp_daemon.py` is additive.

## Related

- Implementation plan: `docs/superpowers/plans/2026-07-17-omniroute-inference-plane-migration.md`
- ADR-10: Local Agent Node (passive-router MCP consensus gateway) — daemonizing does not change the router-not-controller invariant
- ADR-12: Consent Gate Protocol — this ADR is System blast radius, consent-gated per protocol
