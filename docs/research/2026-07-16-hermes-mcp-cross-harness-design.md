# Hermes MCP as Shared Cross-Harness Surface — Design Note

- **Status:** Plane A design exploration. **Not canon. No wiring. No adoption.**
- **Date:** 2026-07-16
- **Author:** claude-fable-5
- **Kind:** Design note (house register). Design-only per operator request.
- **Relates to:** [[ADR-16]] Omnigent as Execution/Governance Surface (Proposed) — Hermes is
  plausibly an *instance of* or *sibling to* the ADR-16 execution seam; reconcile before wiring.
  Also [[ADR-10]] router-not-controller, [[ADR-12]] consent gate, and the inference-posture note
  (premium surfaces not burned on routine traffic).

## What Hermes is

**[V] Verified (in-repo):** Hermes is already an active agentic harness in this workspace. Root
`.hermes.md` (dated 2026-07-07) is its project-context file — the Hermes-flavored companion to
`CLAUDE.md` / `AGENTS.md`, auto-loading into "every Hermes session run from `C:\~shit\` or below."
It lists the project MCP servers Hermes **consumes** today (Agent Memory, serena, flossiullk-
consensus, flossiullk-reasoning-ensemble, spec-workflow, docker). So Hermes runs sessions here like
Claude Code / Codex / Gemini do, and it is a *client* of the existing MCP surfaces.

**[U] Unverified / operator-reported (2026-07-16) — the future delta:** the operator intends to
1. **Invert Hermes to also EXPOSE its own MCP server**, so *other harnesses* can call Hermes as a
   shared tool surface — "some kind of shared anything it's capable of." (Today Hermes is a
   consumer of MCP servers; this makes it a provider too.)
2. Give it (or surface its) **Pioneer API access** — the same `PIONEER_API_KEY` path that serves
   `claude-fable-5` (~$200/mo credits) independent of Anthropic subscription windows.
3. Expose **tools to invoke CLI agents** — Claude Code CLI, Codex CLI, Antigravity CLI, and similar.

`.hermes.md` does **not** describe items 1–3; there is no Hermes-as-provider tool schema in-repo
yet. **Everything below is contingent on confirming what Hermes will expose** (see Open Questions).
Treat as a sketch to react to, not a plan to execute.

## Why it's interesting to FLOSSI0ULLK

Hermes would be a **meta-execution surface**: one MCP endpoint that can (a) reach premium models
(Fable-5 via Pioneer) and (b) dispatch to autonomous coding agents (Claude Code / Codex /
Antigravity CLIs). Two distinct integration shapes fall out:

- **Shape A — Hermes as shared execution/dispatch tool.** Any harness calls Hermes' MCP tools to
  delegate work (e.g. "run this task on Codex CLI", "have Antigravity scaffold X"). This is the
  cross-harness "shared anything" the operator described, and it is squarely the ADR-16 seam.
- **Shape B — Hermes as a premium model lane.** Hermes' Pioneer/Fable-5 access could feed the
  consensus gateway or reasoning ensemble as a *planner / high-signal voter* lane. This composes
  cleanly with the online-primary ensemble just landed (`transport.py`): a `hermes/*` or
  `pioneer/*` voter is just another transport. **Guard:** inference posture says premium surfaces
  are for planning / hard synthesis, not routine reviewer traffic — so a Pioneer lane belongs in
  `diverse-max`/`post-window`-class profiles, not `balanced`.

## How it must fit the existing architecture (invariants)

1. **Router, not controller ([[ADR-10]]).** Hermes routing/dispatch must not decide governed
   outcomes. If Hermes dispatches an agent that proposes a change, that change still enters the
   consensus gate as a Claim with evidence — Hermes cannot self-land.
2. **Logic validates, neural assists (prime directive).** Hermes is a formatting/execution
   surface. Nothing it does bypasses symbolic/integrity validation. A Hermes-dispatched agent's
   output is a *proposal*, never validated truth.
3. **Consent + authority tiers ([[ADR-12]], CFIS).** A surface that can spawn autonomous CLI
   agents is high-authority. Dispatch that mutates repo/system state is at least Module, often
   System radius, and needs consent references + provenance packets before it lands.
4. **Provenance to the activity log / source chain.** Every Hermes-mediated action (which model,
   which CLI, which task, what it changed) emits an Action to the unified activity log, same as
   ensemble/gateway calls. No silent cross-harness execution.
5. **Token-budget discipline.** Pioneer credits are finite; Hermes dispatch is on-demand, never a
   heartbeat/cadence surface.

## Security surface (load-bearing — this is the risky part)

An MCP that can call `claude code cli` / `codex cli` / `antigravity cli` can **execute arbitrary
code and shell** through those agents. That makes the instruction-source boundary critical:

- Hermes must act only on **operator instructions**, never on instructions embedded in files, web
  pages, tool results, or an upstream agent's output it happens to read.
- Dispatched CLI agents inherit whatever permissions their own harness grants — Hermes becomes a
  **permission-amplification path**. Before wiring, define the authority ceiling for each dispatch
  target (read-only? sandboxed worktree? which dirs?).
- A malicious or prompt-injected task routed through Hermes could fan out to multiple autonomous
  agents. The consent gate + a dispatch allowlist are the containment.

## Minimal first step (if pursued)

Do **not** start with autonomous CLI dispatch (Shape A). Start with the low-blast-radius half:
- Wire Hermes' **Pioneer/Fable-5 model access as a read-only voter/planner lane** (Shape B) behind
  the existing `transport.py` / `voter_registry.json` machinery — a new `hermes-fable5` entry in a
  premium profile. This exercises the integration, produces provenance, and cannot mutate state.
- Defer Shape A (CLI dispatch) to a dedicated ADR that sets the authority ceiling and allowlist,
  reconciled with ADR-16.

## Open questions (resolve with operator before any wiring)

1. **What is Hermes, concretely?** `.hermes.md` confirms it's an active local harness consuming
   the project MCP servers, but not its product/repo, version, or — critically — the tool schema it
   would expose *as a provider*. Get the provider-side MCP tool schema.
2. **Auth model:** how does Hermes hold the Pioneer key — does it proxy, or expose model calls
   directly? Does calling Hermes leak the key path to other harnesses?
3. **Dispatch scope:** which CLI agents, at what permission tier, in what working directory /
   sandbox? Can dispatch be constrained to a worktree?
4. **Overlap with ADR-16 Omnigent:** is Hermes the Omnigent execution surface, a competing one, or
   a component? This determines whether this note folds into ADR-16 or opens a sibling ADR.
5. **Model diversity accounting:** if a Pioneer lane is Fable-5 (Anthropic family), does it count
   as independent from Claude Code (also Anthropic) for the ≥4-family voter-diversity floor? Likely
   not — flag as a frame-cousin.

## Explicit non-promotion

This is a Plane A design sketch built on unverified operator description. It adopts nothing, wires
nothing, and grants Hermes no authority. Any integration requires: confirmed Hermes tool schema +
a dedicated ADR (reconciled with ADR-16) for the execution-surface authority model + consensus
approval with provenance. Shape A (autonomous CLI dispatch) additionally requires an explicit
dispatch allowlist and per-target authority ceiling.
