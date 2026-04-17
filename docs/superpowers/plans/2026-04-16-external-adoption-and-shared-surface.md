# External Adoption And Shared Agent Surface

Date: 2026-04-16
Status: Active
Owner: FLOSSI0ULLK superpowers / local agent node workstream

## Purpose

Capture the highest-leverage external systems already sitting in `kalisam` forks,
so FLOSSI0ULLK stops rebuilding solved layers in isolation, and define the
lowest-risk path toward a shared agent surface across Claude Code, Gemini CLI,
OpenCode, and future peers.

## Immediate Reality

- `Claude Code` is authenticated and already sees `flossiullk-consensus`.
- `OpenCode` is already wired to the same local consensus MCP.
- `Gemini CLI` is authenticated and now sees the same project MCP via
  `C:\~shit\.gemini\settings.json`.
- `Mistral Vibe` is now installed and project-scoped through generated
  `.vibe/config.toml`, `.vibe/agents/flossi0ullk-explore.toml`, and
  `vibe-floss.ps1`, with shared skills and MCP sourced from canon.
- `Serena` is installed, project-scoped via `FLOSS/.serena/project.yml`, and
  registered on the shared MCP surface for Claude, Gemini, and OpenCode.
- `Flowith` has a live programmatic LLM surface: the local credential file at
  `~/.flowith/credentials.json` successfully authenticated a direct call to
  `https://edge.flowith.io/external/use/llm` on 2026-04-16.
- A minimal shared context surface now exists in canonical form via
  `FLOSS/shared-context-surface.json`, with a generated bootstrap view and a
  small corpus router script.
- The shared context surface now also generates additive compressed context
  views at `.agent-surface/context/CONTEXT_L0.md` and `CONTEXT_L1.md`, so
  agents can load cheap briefings before opening richer canonical docs.
- The context-daemon architecture is now promoted into canon at
  `FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md`.
- A minimal shared skill surface now exists in canonical form via
  `FLOSS/shared-skill-surface.json`, backed by portable skills in
  `FLOSS/skill-corpus/` and a generated shared index.
- The current waste pattern is not lack of models. It is fragmentation of
  skills, MCP configuration, plugins, hooks, and memory surfaces across agents.

## Highest-Gain Imports Right Now

- `Serena`
  - Role: shared code-intelligence substrate with semantic retrieval, symbol-aware
    editing, and LSP-backed navigation.
  - Take: add it to the shared MCP surface for terminal agents while keeping
    `.serena/` as the project-owned configuration and memory substrate.

- `Flowith`
  - Role: subscription-backed multi-model API surface that can route to GPT,
    Gemini, Claude, and DeepSeek families through one endpoint.
  - Take: use it as a voter provider and research/critique lane before building
    any larger FlowithOS bridge.

- `Free-LLM`
  - Role: provider catalog, not framework.
  - Take: mine it for supported low-cost/free inference surfaces and wire only
    those that have real credentials or clear strategic value.

- `caveman`
  - Role: token-compression utility for agent output and session-start context.
  - Take: mine the compression heuristics and `caveman-compress` workflow for
    generated low-token views, but keep canonical docs human-readable and
    editable.

## Fresh Fork Triage

Newest forks checked on April 16, 2026 against the current FLOSSI0ULLK state:

- `kalisam/OpenViking`
  - Why it matters: strongest current fit for the shared context and memory layer.
  - Current take: import the ideas and examples first, especially the filesystem
    context model and Claude/OpenCode memory plugin patterns, before considering
    runtime adoption.

- `kalisam/symphonium`
  - Why it matters: most relevant new fork for long-horizon work routing and
    autonomous implementation runs.
  - Current take: mine the work-packet / proof-of-work model after the shared
    skill and context surfaces are less fragmented.

- `kalisam/nanobot`
  - Why it matters: unusually small agent runtime with mature MCP, skill, and
    channel support.
  - Current take: mine for lightweight runtime and provider-interface patterns,
    not as a replacement for the current local source-chain + consensus stack.

- `kalisam/ExtendingSkillX`
  - Why it matters: strongest new fork for automatic skill distillation and
    hierarchical skill knowledge bases.
  - Current take: treat it as the likely model for later shared-skill KB work,
    not as a phase-zero import.

## Recent External Forks Worth Mining

### Adopt first

- `kalisam/OpenViking` (fork of `volcengine/OpenViking`, updated 2026-04-16)
  - Relevance: filesystem-native context database, tiered loading, recursive
    retrieval, and concrete Claude/OpenCode memory plugin examples.
  - Take: best current template for the shared context substrate above local
    files and below Holochain.

- `kalisam/DaerGoBam` (fork of `bytedance/deer-flow`, updated 2026-04-16)
  - Relevance: long-horizon super-agent harness with subagents, memory,
    sandboxes, skills, and message-gateway patterns.
  - Take: harvest orchestration patterns, not the whole framework.

- `kalisam/OURmirror` (fork of `FrkAk/mymir`, updated 2026-04-15)
  - Relevance: context network + retrieval interface + lifecycle
    `Brainstorm > Decompose > Refine > Plan > Execute > Track`.
  - Take: strong candidate for the retrieval and memory harness shape.

- `kalisam/Agorai` (updated 2026-04-15)
  - Relevance: shared multi-agent workspace with explicit disagreement,
    CLI + MCP bridge, and agent registration.
  - Take: best current template for cross-agent collaboration substrate above
    local files and below Holochain.

- `kalisam/symphonium` (fork of `openai/symphony`, updated 2026-04-15)
  - Relevance: isolated autonomous implementation runs with work-level proof.
  - Take: strongest current reference for the future execution/work-router layer.

- `kalisam/oh-my-codex` (updated 2026-04-04)
  - Relevance: portable orchestration ideas, mixed-provider teams, hooks,
    HUDs, worker routing.
  - Take: mine team-execution and cross-provider coordination patterns.

- `kalisam/context-engineering-kit` (updated 2026-04-09)
  - Relevance: portable skill substrate with low-token patterns across
    Claude Code, Gemini CLI, and others.
  - Take: harvest skill packaging and minimal-token context patterns.

- `kalisam/caveman` (fork of `JuliusBrussee/caveman`, updated 2026-04-15)
  - Relevance: prompt/skill-level token compression plus file-level context
    compression for always-loaded docs.
  - Take: use it as a projection/compression reference for L0/L1 context views,
    not as a reason to rewrite canonical source docs into compressed speech.

- `kalisam/holochain-agent-skill` (updated 2026-04-15)
  - Relevance: portable Holochain-specific skill corpus.
  - Take: direct import candidate for Holochain implementation work.

### Adopt second

- `kalisam/nanobot` (fork of `HKUDS/nanobot`, updated 2026-04-16)
  - Relevance: small readable agent runtime with native MCP, skills, channels,
    memory, and provider abstractions.
  - Take: mine for lightweight runtime ideas and plugin ergonomics.

- `kalisam/ExtendingSkillX` (fork of `zjunlp/SkillX`, updated 2026-04-16)
  - Relevance: automatic hierarchical skill KB construction from trajectories.
  - Take: strongest candidate for shared-skill distillation once the portable
    skill surface exists.

- `kalisam/hermaphroditey-agenty` (fork of `NousResearch/hermes-agent`, updated 2026-04-16)
  - Relevance: self-improving skill loop and cross-session persistence.
  - Take: learn from the learning loop, avoid importing a monolithic agent runtime.

- `kalisam/skillguard` (updated 2026-04-16)
  - Relevance: security scanning for agent skills.
  - Take: important once FLOSSI0ULLK starts sharing/importing more skills and plugins.

- `kalisam/Hybrid-ai-stack-intent-solutions` (updated 2026-04-16)
  - Relevance: routing between cheap/local and expensive/cloud models.
  - Take: useful heuristic reference for the optimization harness.

- `kalisam/SUPER_POWERED_PRODUCTIVITY-MCP` (updated 2026-04-16)
  - Relevance: task-system bridge via MCP.
  - Take: optional later bridge if task state should sync beyond local files.

## Shared Surface Strategy

Do not start with symlinks.

Symlinks are brittle across:

- Windows privilege / junction behavior
- tool-specific config semantics
- per-agent schema drift
- project-root detection differences

Use this shape instead:

1. Canonical source files
   - Root `.mcp.json` for shared MCP servers
   - Canonical shared-surface manifest later for hooks, skills, plugins, and policies

2. Materializers
   - Write native config artifacts for each agent from the canonical source
   - Example targets:
     - `.gemini/settings.json`
     - `.claude/settings.json`
     - `opworkers/opencode.jsonc`

3. Agent-native deltas stay local
   - Claude plugin enablement is not the same thing as Gemini extensions
   - Shared substrate should cover only the overlap unless explicitly widened

## Current Shared Surface

### Implemented now

- Shared MCP: `flossiullk-consensus`
  - Claude Code: visible
  - OpenCode: visible
  - Gemini CLI: visible
- Project-scoped Serena config and memories
  - Repo: `FLOSS/.serena/project.yml`
  - Status: present and ready for MCP registration
- Shared context registry and router
  - Canonical manifest: `FLOSS/shared-context-surface.json`
  - Generated bootstrap: `.agent-surface/context/CONTEXT_BOOTSTRAP.md`
  - Generated compressed views:
    - `.agent-surface/context/CONTEXT_L0.md`
    - `.agent-surface/context/CONTEXT_L1.md`
    - `.agent-surface/context/context-view-registry.json`
  - Routing script: `FLOSS/scripts/context_router.py`
- Shared skill corpus and registry
  - Canonical manifest: `FLOSS/shared-skill-surface.json`
  - Portable source skills: `FLOSS/skill-corpus/`
  - Generated index: `.agent-surface/skills/SKILL_INDEX.md`
  - Generated registry: `.agent-surface/skills/skill-registry.json`
  - Native projections:
    - Codex: `%USERPROFILE%/.codex/skills/flossi0ullk-*`
    - Claude: `.claude/skills/flossi0ullk-*`
    - Gemini: `.gemini/skills/flossi0ullk-*`
    - OpenCode: `opworkers/.opencode/skills/flossi0ullk-*`
- Shared hook policy surface
  - Canonical manifest: `FLOSS/shared-hook-surface.json`
  - Generated index: `.agent-surface/hooks/HOOK_INDEX.md`
  - Generated registry: `.agent-surface/hooks/hook-registry.json`
  - Native projections:
    - Claude: `.claude/settings.json` `PostToolUse` on `Write|Edit|MultiEdit`
    - Gemini: `.gemini/settings.json` `AfterTool` on `write_file|replace`
  - Shared execution path:
    - `FLOSS/scripts/hook_post_write.py`
    - `FLOSS/scripts/hook_bg_round.py`
- Shared Vibe surface
  - Canonical manifest target: `FLOSS/shared-agent-surface.json` `targets.vibe`
  - Generated config: `.vibe/config.toml`
  - Generated agents: `.vibe/agents/*.toml`
  - Generated launcher: `vibe-floss.ps1`
  - Shared inputs:
    - MCP from root `.mcp.json`
    - skills from `FLOSS/skill-corpus/`
- Metaharness operating doctrine
  - Canonical doc: `FLOSS/docs/architecture/METAHARNESS_OPERATING_MODEL.md`

### Next to converge

- Shared memory handoff format
- Shared agent registry / capability declaration

## Recommended Near-Term Build Order

1. Create a canonical shared-surface manifest in the workspace root.
   - Start with MCP servers only.
   - Keep it minimal and boring.

2. Add a materializer script.
   - Source: root `.mcp.json`
   - First target: `.gemini/settings.json`
   - Second target: `opworkers/opencode.jsonc`

3. Add Serena to the same shared MCP registry.
   - Use the terminal-agent launch shape with `--project-from-cwd`
   - Keep client-specific quirks out of `.serena/project.yml`

4. Create a shared skill corpus directory.
   - Store portable skill docs once.
   - Materialize or reference them into Claude/Gemini/OpenCode native locations.

5. Import or adapt the best external skill packs instead of rewriting them.
   - Start with `context-engineering-kit`
   - Then `holochain-agent-skill`
   - Add `skillguard` once import volume increases

6. Add Flowith as a first-class optional voter provider.
   - Prefer credential-file fallback over more env sprawl
   - Use profile/roster controls instead of hard-coding it into every round

7. Deepen the shared context surface.
   - Add more corpus-local examples and better query routing.
   - Keep the route order explicit and cheap.

8. Prototype a cross-agent collaboration layer.
   - Use `Agorai` ideas for agent registration and shared work packets.
   - Keep FLOSSI0ULLK provenance and source-chain logging as the truth layer.

## Retrieval Posture

Do not bulk-load `_reference/`.

Treat `_reference/` as a federated corpus:

- `docs/` = active canon
- `_reference/software-engineering` = published software-engineering books,
  papers, and implementation references
- `_reference/ai-ml` = published model, orchestration, memory, and agent
  research
- external forks = active implementation references and experiments

Retrieval should choose corpus first, then documents, then passages.

## Decision

For the current phase, FLOSSI0ULLK should:

- adopt external orchestration and context-management patterns aggressively,
  but not import whole frameworks blindly
- unify agent surfaces through generated native config, not symlinks
- keep Holochain and the local source chain as the provenance substrate
- preserve disagreement and plurality instead of collapsing all work into one
  base agent
