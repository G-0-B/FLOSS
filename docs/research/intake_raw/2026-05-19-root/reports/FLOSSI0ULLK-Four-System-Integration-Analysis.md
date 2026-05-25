# FLOSSI0ULLK Four-System Integration Analysis

```yaml
id: "flossi0ullk-four-system-integration"
version: "1.0.0"
kind: "integration_analysis"
status: "Proposed"
truth_status: "Specified"
updated: "2026-04-03"
evidence_sources:
  - "Meta Harness paper (arXiv:2603.28052, Stanford IRIS + MIT, 2026-03-30)"
  - "oh-my-openagent GitHub (code-yeongyu, 47.5k stars)"
  - "oh-my-codex GitHub (Yeachan-Heo, 2.8k stars, trending)"
  - "oh-my-claudecode GitHub (Yeachan-Heo)"
  - "Claude Code source leak analysis (2026-03-31)"
  - "FLOSSI0ULLK Master Metaprompt v1.3.1"
  - "OpenClaw docs and multi-agent architecture"
  - "LiteLLM provider docs"
upgrade_path: "ADR review -> pilot integration -> validate -> promote"
rollback_plan: "Each integration seam is independently reversible"
license: "Compassion Clause + Apache-2.0/GPL-compatible"
```

---

## 0. Why Four Systems

The meta-orchestration space has converged on a shared problem: the LLM is frozen, all intelligence lives in the surrounding code (the "harness"), and optimizing that harness is now the highest-leverage engineering work. Four systems attack this from four different angles. None solves it completely. Together they cover the full surface.

| System | Created By | What It Wraps | Core Innovation | What It Lacks |
|---|---|---|---|---|
| **Meta Harness** | Stanford IRIS + MIT (Lee, Khattab, Finn) | Any LLM (frozen) | Automated harness optimization via 10M-token full-trace inspection | Runtime orchestration, governance, multi-agent coordination |
| **omo (oh-my-openagent)** | code-yeongyu | OpenCode (Go terminal agent) | 11 specialized agents, 48 hooks, Hashline, Boulder persistence | Git-based isolation, automated optimization, provenance/governance |
| **OMX (oh-my-codex) / OMC** | Yeachan-Heo | Codex CLI / Claude Code | Git worktree agent isolation, mixed-provider teams, portable orchestration | Deep agent specialization, symbolic validation, governance |
| **FLOSSI0ULLK MetaCoordinator** | Anthony (human) + multi-AI collective | OpenClaw + LiteLLM | Ternary consensus, ADR governance, symbolic-first, Claim Truth Model | Production hook system, background parallelism, git-based isolation |

The integration thesis: FLOSSI0ULLK adopts patterns from all three, contributes governance back to all three, and Meta Harness optimizes the combined system automatically.

---

## 1. Meta Harness (Stanford IRIS Lab + MIT)

**Paper:** "Meta-Harness: End-to-End Optimization of Model Harnesses" (arXiv:2603.28052)
**Authors:** Yoonho Lee, Roshen Nair, Qizheng Zhang, Kangwook Lee, Omar Khattab, Chelsea Finn
**GitHub:** stanford-iris-lab/meta-harness-tbench2-artifact (discovered harness only; search system not yet open-sourced)

### 1.1 Formal Framework

A harness H is a stateful program wrapping a frozen LLM M that determines what context M sees at each step. The optimization objective:

```
H* = argmax_H  E_{x ~ X} [ r(tau, x) ]
```

where tau ~ p_M(H, x) is the rollout trajectory and r scores the outcome. This is policy search in code space — the harness IS the policy.

### 1.2 Core Innovation: Full-Trace File Access

The proposer agent (Opus 4.6 with max reasoning) gets unrestricted filesystem access to a growing archive of all prior candidates' source code, execution traces, and evaluation scores. Key statistics per iteration:

- Median 82 files accessed
- 41% source code, 40% execution traces, 19% scores/numerical
- ~10M tokens of diagnostic information per optimization step

This is 3 orders of magnitude beyond prior systems:

| System | Feedback Budget | Optimization Target |
|---|---|---|
| DSPy/MIPROv2 | ~3K tokens | Prompts + demonstrations |
| TextGrad | ~15K tokens | Text variables |
| OpenEvolve/AlphaEvolve | ~22K tokens | Code mutations |
| Trace/OptoPrime | ~26K tokens | Execution graphs |
| **Meta Harness** | **~10M tokens** | **Complete harness implementations** |

### 1.3 Results

- Online text classification: +7.7pp over ACE baseline, 4x fewer context tokens
- IMO-level math: +4.7pp average, transfers to 5 unseen models
- TerminalBench-2: 76.4% pass rate (Opus 4.6), #2 among all agents
- 10x fewer evaluations than OpenEvolve/TTT-Discover to match accuracy, then surpasses by 10+ points

### 1.4 The Iteration 7 Breakthrough

TerminalBench-2 iterations 1-6: local code fixes and regressions. Iteration 7: the proposer pivoted from modifying the control loop to adding information BEFORE the loop — an environment bootstrap snapshot (working directory, file listing, available tools, package managers, memory). This "additive rather than subtractive" insight is invisible to compressed-feedback systems because they lack the trace data to diagnose why early exploration turns are wasted.

Ablation confirms the ceiling: scores-only feedback reaches 34.6%, scores-plus-summary reaches 34.9% (essentially identical), full-filesystem reaches significantly higher. The ~0.3pp gap between the first two IS the ceiling of local optimization. Full traces break through it.

### 1.5 The Video Presenter's Critique (Claim Truth: Specified — reasonable interpretation, not paper's conclusion)

The 4pp improvement ceiling may represent code-level optimization (tweaking existing harness structure) rather than topological optimization (discovering entirely new harness architectures). The presenter argues this is because statistical optimization over a statistical core (LLM at non-zero temperature) requires massive data and will plateau without neuro-symbolic scaling — formal solvers (Lean 4, homotopy type theory) providing structured search spaces.

This critique directly validates FLOSSI0ULLK's Symbolic-First Architecture: "Symbolic Layer (primary), Neural Layer (assistive), Neural NEVER bypasses symbolic validator." The implication: Meta Harness + symbolic validation could break the 4pp ceiling.

### 1.6 Relevance to FLOSSI0ULLK

- MetaLoop IS a Meta Harness. The November 2025 MetaLoop implementation roadmap describes the same loop: propose -> evaluate -> store traces -> learn -> repeat.
- Cerebras Scout's 10M-token context window is architecturally necessary, not nice-to-have. Meta Harness's full-trace principle requires it.
- The harness optimization objective (argmax E[R(H)]) can be applied to the MetaCoordinator itself: optimize agent-model routing, consensus thresholds, hook configurations, and prompt variants as harness parameters.

---

## 2. omo (oh-my-openagent / Sisyphus)

**Repo:** github.com/code-yeongyu/oh-my-openagent
**Stars:** 47.5k | **Downloads:** 1.5M+ | **Language:** TypeScript on Bun | **Files:** ~1,268, ~160k LOC
**Base Platform:** OpenCode (Go-based terminal AI coding agent)
**Author:** code-yeongyu

### 2.1 Architecture: Plugin for OpenCode

omo is an OpenCode plugin, not a standalone system. It transforms OpenCode's single-agent chat interface into a multi-agent workforce. Installation: `npx clawhub@latest install oh-my-openagent` or via the OpenCode plugin system. Config at `~/.config/opencode/oh-my-opencode.jsonc`.

### 2.2 The 11 Agents (4 Personality Groups)

**Group 1 — Communicators (Claude / Kimi / GLM):** Instruction-following, mechanics-driven prompts.

| Agent | Role | Key Constraint |
|---|---|---|
| Sisyphus | Main orchestrator/CTO, ~1,100-line prompt, 32K thinking budget | Opus 4.6 (max). Hardest agent to run locally. |
| Atlas | Todo-list orchestrator, dual-prompt (auto-detects model family) | |
| Prometheus | Interview-mode planner, Socratic questioning before plan | |
| Metis | Pre-planning consultant, higher temperature for creative gaps | |

**Group 2 — GPT-Native (GPT-5.3/5.4):** Principle-driven, autonomous execution.

| Agent | Role | Key Constraint |
|---|---|---|
| Hephaestus | Deep autonomous worker, fires 2-5 parallel explore agents | **No fallback chain. Requires GPT access.** |
| Oracle | Read-only architecture consultant, "last resort" debugger | Restricted from write/delegate tools |
| Momus | Ruthless plan reviewer, strict OK-or-reject gate | Tool restrictions keep it review-only |

**Group 3 — Category-Spawned:**

| Agent | Role |
|---|---|
| Sisyphus-Junior | Dynamic executor, capability determined by spawning category |

**Group 4 — Utility Runners (cheapest/fastest):**

| Agent | Role |
|---|---|
| Explore | Contextual grep, codebase search. Fire 10 in parallel. |
| Librarian | External documentation research |
| Multimodal Looker | Vision analyst for images/PDFs |

### 2.3 The 48-Hook Lifecycle System

Five functional tiers:

1. **Session hooks (23):** Lifecycle events — session creation, idle detection, startup codebase map injection
2. **Tool-guard hooks (12):** Intercept execution — prevent overwrites, enforce no-AI-comment patterns, block dangerous operations
3. **Transform hooks (4):** Modify messages in-flight
4. **Continuation hooks (7):** Workflow continuity — Boulder enforcement (don't stop until all TODOs complete), Ralph Loop
5. **Skill hooks (2):** Task-specific behavior injection

### 2.4 8 Task Categories (Intent-Based Routing)

| Category | Purpose | Default Model |
|---|---|---|
| visual-engineering | Frontend, UI/UX | Gemini 3.1 Pro |
| ultrabrain | Hard logic, architecture | GPT-5.4 (xhigh) |
| deep | Complex multi-file coding | GPT-5.3 Codex |
| artistry | Creative approaches | Gemini -> Claude -> GPT |
| unspecified-high | General complex | Claude Opus |
| unspecified-low | General standard | Claude Sonnet |
| quick | Single-file changes | Claude Haiku |
| writing | Documentation, prose | Gemini Flash |

### 2.5 Unique Patterns

**Dual-Prompt Agents:** Claude and GPT require fundamentally different prompt architectures. Claude follows mechanics-driven prompts (detailed checklists, 1,100 lines). GPT follows principle-driven prompts (concise principles with XML structure). Agents like Prometheus auto-detect model family at runtime via `isGptModel()` and switch prompts. Give GPT a Claude prompt and it contradicts itself.

**Hashline (LINE#ID Content Hash):** Tags every line with a content hash (e.g., `11#VK| function hello() {`). If file changed since last read, hash won't match, edit rejected before corruption. Impact: Grok Code Fast 1 went from 6.7% to 68.3% success rate from this single change.

**Boulder System:** Tracks active work in `boulder.json`. Interrupted sessions resume exactly where stopped. Learnings persist in `.sisyphus/notepads/{plan-name}/` across five structured files: `learnings.md`, `decisions.md`, `issues.md`, `verification.md`, `problems.md`.

**Ultrawork (`ulw`):** Full autopilot — auto-planning, deep research, self-correction loops, parallel agents, zero intervention. The Ralph Loop (`/ulw-loop`) continues until 100% complete.

**6-Phase Config Pipeline:** Provider -> Plugin Components -> Agents (model resolution, overrides) -> Tools (26) -> MCPs (Exa websearch, context7 docs, grep_app GitHub search) -> Commands. Project config overrides user config via deep merge with Zod v4 validation.

---

## 3. OMX (oh-my-codex) + OMC (oh-my-claudecode)

**Repos:** github.com/Yeachan-Heo/oh-my-codex (OMX) | github.com/Yeachan-Heo/oh-my-claudecode (OMC)
**Stars:** OMX 2.8k (trending, +2,867 in 24 hours) | OMC newer
**Language:** TypeScript + Rust (omx-explore crate) | **Base Platform:** Codex CLI (OMX) / Claude Code (OMC)
**Author:** Yeachan-Heo

### 3.1 Architecture: Portable Orchestration Wrapper

OMX does NOT replace Codex — it wraps it. Same pattern ported to Claude Code as OMC. The orchestration logic is agent-agnostic; the prompts adapt to the underlying model. This is a fundamentally different philosophy from omo (which is tightly coupled to OpenCode).

The canonical workflow: `$deep-interview` (clarify intent) -> `$ralplan` (consensus planning) -> `$ralph` or `$team` (execute).

### 3.2 Agent Roles (Skill-Based, Not Fixed Agents)

OMX uses 30+ specialized prompts organized in five lanes rather than fixed agent instances:

| Lane | Roles |
|---|---|
| Build & Analysis | planner, architect, executor, debugger, verifier |
| Review | code-reviewer, security-reviewer, performance-reviewer |
| Domain | data-engineer, devops, frontend, backend |
| Product | product-manager, technical-writer |
| Coordination | team-leader, task-router |

Invoked via `/prompts:role-name` or `$skill-name` syntax.

### 3.3 Unique Patterns

**Git Worktree Isolation Per Worker (the killer feature):** Since v0.10.0, every team worker runs in an isolated git worktree by default. No flags needed.

```bash
$ omx team 3:executor "refactor auth module"
Team started: refactor-auth-module
workers: 3 (worktrees: automatic, detached)
```

Each worker: gets a dedicated worktree at `.omx/team/<n>/worktrees/worker-N`, commits to its own detached branch. The leader: continuously merges worker commits via auto-selected strategies (merge, cherry-pick, cross-worker rebase). On shutdown: worktrees rolled back, branches deleted. Zero manual intervention.

**Mixed-Provider Teams:**

```bash
OMX_TEAM_WORKER_CLI_MAP=codex,claude,gemini \
  omx team 3:executor "full-stack implementation"
```

Codex, Claude, and Gemini workers side-by-side, each in its own worktree. This IS the RSA swarm pattern with production git isolation.

**$ralplan Consensus Planning:** Planner -> Architect -> Critic pipeline before execution. Three-role structured consensus. Not binary (omo's Momus) and not ternary (FLOSSI0ULLK's +1/0/-1) — it's role-sequential: each role refines/challenges the previous role's output.

**$deep-interview (Socratic Clarification):** Intent classification happens upfront before any planning. Weighted dimensions measure clarity across the request. Keeps pressing on intent, non-goals, and decision boundaries before handing off. Maps to FLOSSI0ULLK kernel's "anti-sycophancy mandate: Never guess on critical specs. If ambiguous -> Decision = 0."

**OpenClaw Integration (Live):** `OMX_OPENCLAW_COMMAND=1` enables hook events (session-start, session-idle, ask-user-question, session-stop, session-end) routed through OpenClaw as a notification/command gateway. Reference implementation in `scripts/openclaw-gateway-demo.mjs`.

**oh-my-claudecode (OMC):** Same orchestration ported to Claude Code. Adds `omc ask claude/codex/gemini` for cross-provider queries, auto-resume daemon for rate limit recovery (`omc wait --start`), HUD presets for live observability. Published as npm package `oh-my-claude-sisyphus`.

**The Portable Pattern Itself:** Building the same orchestration across Codex, Claude Code, and potentially more base agents. The orchestration is the product, the base agent is interchangeable. This is the strongest alignment with FLOSSI0ULLK's "ride every model" philosophy.

### 3.4 Key Infrastructure

- **tmux-first runtime:** All coordination via tmux session management. Low-tech, works everywhere, no custom daemon needed for basic coordination.
- **5 MCP Servers:** Persistent memory, state management, research, and team coordination.
- **36 Skills + 33 Prompts:** Cataloged capabilities invoked by name.
- **HUD (Heads-Up Display):** Live observability panel showing agent status, task progress, resource usage.
- **Webhook notifications:** Discord, Slack, Telegram integration for team visibility.

---

## 4. Claude Code Leak Patterns (Tactical Extraction)

**Event:** March 31, 2026, Bun bundler included sourcemap in npm package v2.1.88. 512K lines of TypeScript, ~1,900 files exposed.

### 4.1 KAIROS (Not "Chyros" — Greek for "the right moment")

Persistent background agent architecture:

- **Tick engine:** Receives `<tick>` prompts on intervals, decides whether to act proactively
- **15-second blocking budget:** Anything longer deferred to avoid slowing user
- **Three-layer memory:**
  - Layer 1: Lightweight index (MEMORY.md, ~150 chars/entry) — always loaded
  - Layer 2: Topic files — fetched on-demand when relevant
  - Layer 3: Raw transcripts — only grep'd, never fully loaded
- **Nightly `autoDream` distillation:** Reconciles contradictions, converts tentative observations to verified facts
- **Append-only daily logs:** `logs/YYYY/MM/YYYY-MM-DD.md`

This three-layer architecture is the most battle-tested persistent memory design in production. Directly maps to FLOSSI0ULLK's Claim Truth Model: autoDream's "tentative -> verified" promotion IS the Unverified -> Verified transition.

### 4.2 Anti-Distillation Decoy Tools

When `ANTI_DISTILLATION_CC` enabled: fake tool definitions injected into system prompts, poisoning training data for competitors recording API traffic. Second layer (CONNECTOR_TEXT) buffers assistant text between tool calls with cryptographic signatures.

**FLOSSI0ULLK application:** Not poison data — but cryptographic provenance markers. Authentic FLOSSI0ULLK agents could carry verifiable signatures that distinguish them from impersonators in public channels. Aligns with KERI/ACDC signing already specified in the architecture.

### 4.3 Frustration Detection via Regex

Simple pattern matching (`wtf|shit|fucking broken|this sucks`) for product health telemetry. Not LLM-based, not behavior modification.

**FLOSSI0ULLK application:** Cheap deterministic pre-filter before burning tokens. When an agent is cycling/stuck, detect frustration-equivalent patterns (repeated error messages, identical retry sequences) and escalate to more expensive models or trigger consensus review. Cost: near zero. Savings: significant.

### 4.4 Coordinator Mode (Prompt-Based Orchestration)

One Claude spawning and managing multiple parallel worker Claudes entirely through system prompts, not code. Enables updating workflow behavior without redeployment.

**FLOSSI0ULLK application:** The MetaCoordinator's orchestration logic could be partially expressed as system prompts (updateable without code changes) rather than hardcoded in Python. This is the "harness as prompt" pattern.

---

## 5. Pattern Comparison Matrix

| Pattern | Meta Harness | omo | OMX/OMC | FLOSSI0ULLK | Claude Code |
|---|---|---|---|---|---|
| **Agent isolation** | N/A (single agent) | Process-based (tmux) | **Git worktree** | Specified (Holochain source chains) | Process-based |
| **Multi-model routing** | Single model (Opus) | 8 categories, dual-prompt | Mixed-provider teams | LiteLLM role-based | Single provider |
| **Planning/execution separation** | Proposer/evaluator split | Prometheus/Hephaestus | $ralplan -> $team | RFC -> ADR -> implement | Coordinator mode |
| **Consensus mechanism** | N/A | Momus binary (OK/reject) | $ralplan (role-sequential) | **Ternary (+1/0/-1)** | N/A |
| **Persistence** | Filesystem archive | Boulder (5 notepad files) | Git worktrees + state | ADR + ConversationMemory | **KAIROS 3-layer memory** |
| **Edit verification** | N/A | **Hashline (content hash)** | Git diff | Specified (symbolic-first) | Strict write discipline |
| **Governance/provenance** | N/A | N/A | N/A | **ADR + Claim Truth Model** | N/A |
| **Automated optimization** | **argmax E[R(H)] over code space** | N/A | N/A | MetaLoop (specified) | N/A |
| **Full-trace inspection** | **10M tokens, no summarization** | Hook logs | Team logs + integration reports | Specified (not built) | autoDream distillation |
| **Consent/safety** | N/A | Tool-guard hooks | N/A | **Consent-first, escape hatch** | Feature flags |
| **Background agents** | N/A | BackgroundManager | tmux workers | Specified (Chyros-equivalent) | **KAIROS tick engine** |
| **Hook/extensibility system** | N/A | **48 hooks, 5 tiers** | Hook events via OpenClaw | Not built | Internal feature flags |
| **Symbolic validation** | N/A | N/A | N/A | **Symbolic-first architecture** | Regex-based detection |
| **Portable across base agents** | N/A | OpenCode only | **Codex + Claude Code + more** | Agent-agnostic (via LiteLLM) | Claude only |

---

## 6. What FLOSSI0ULLK Should ADOPT

### From omo:

1. **Dual-prompt agent pattern.** Every MetaCoordinator agent carries Claude-style and GPT-style prompt variants. Auto-detect model family at runtime when LiteLLM routes to different providers for cost/latency. Eliminates prompt-model mismatch degradation.

2. **Hashline deterministic edit verification.** LINE#ID content hash as the verification layer between spec-generated code and filesystem writes. SDD says specs are source of truth — Hashline proves the spec's intent landed in the file. (6.7% -> 68.3% success rate speaks for itself.)

3. **48-hook lifecycle architecture.** Five-tier hooks (session, tool-guard, transform, continuation, skill) as behavioral extensibility points. Consensus checks, provenance logging, and safety gates inject via hooks without modifying core orchestration. Specifically: tool-guard hooks enforce symbolic-first validation before any neural-generated code is written.

4. **Boulder structured persistence.** Replace unstructured conversation logs with five-file notepad pattern (learnings, decisions, issues, verification, problems) per active task. `boulder.json` checkpoint maps to ADR-documented state.

5. **Ultrawork/Ralph Loop automation.** Gated by ternary consensus before each continuation cycle. The "escape hatch" is the -1 vote from any agent (human, symbolic validator, or safety layer).

### From OMX/OMC:

6. **Git worktree agent isolation.** Each agent in the swarm works on its own detached branch. Leader (MetaCoordinator) merges incrementally with conflict detection. For multi-PC deployment: each machine's agents commit to their worktree, central server handles merge coordination. This maps directly to Radicle's collaborative model.

7. **Mixed-provider team execution.** `OMX_TEAM_WORKER_CLI_MAP=codex,claude,gemini` as a pattern: define which providers each worker uses, run them in parallel, merge results. The LiteLLM config we built already has the providers — OMX's team command shows how to coordinate them.

8. **$ralplan consensus planning.** Planner -> Architect -> Critic as a structured pre-execution pipeline. Use BEFORE ternary voting — $ralplan generates the plan, ternary voting approves/holds/rejects it. Two-stage consensus.

9. **$deep-interview Socratic clarification.** Intent classification before action. Weighted clarity dimensions. Directly implements the kernel's "If ambiguous -> Decision = 0" as an interactive process rather than a static gate.

10. **OpenClaw gateway integration.** OMX already has `OMX_OPENCLAW_COMMAND=1` with hook events. This is a live integration seam — FLOSSI0ULLK's consensus engine can receive these events and respond through the same channel.

11. **The portable orchestration pattern.** Build coordination logic once, port across base agents. The MetaCoordinator should work whether the underlying agent is OpenClaw, Claude Code, Codex, or a local model on a Raspberry Pi.

### From Claude Code (KAIROS):

12. **Three-layer memory architecture.** Lightweight index (always loaded) -> topic files (on-demand) -> raw transcripts (grep-only). With nightly autoDream consolidation implementing Claim Truth Model's Unverified -> Verified promotion.

13. **Tick-based proactive agents.** 15-second blocking budget, decide-to-act-or-wait pattern. For MetaCoordinator: background consensus agent that monitors agent outputs and proactively flags potential issues without blocking execution.

14. **Frustration-equivalent detection.** Cheap regex/pattern matching to detect agent cycling, repeated failures, or resource exhaustion before escalating to expensive models or human attention.

### From Meta Harness:

15. **Full-trace, never-summarize principle.** Store complete execution traces, agent prompts, tool calls, and outcomes. Use Cerebras Scout 10M context to inspect rather than compress. Design for 60-70% of advertised context window for effective recall.

16. **Environment bootstrapping over control flow modification.** Optimize what MetaCoordinator knows at initialization (available agents, capabilities, costs, recent performance, active ADRs) rather than optimizing coordination logic.

17. **20+ prior candidate archive.** Maintain running archive of at least 20 prior MetaCoordinator configurations with full traces for pattern detection across iterations.

18. **Cross-run knowledge transfer.** Optimizations discovered for one FLOSSI0ULLK deployment available to the proposer optimizing another.

---

## 7. What FLOSSI0ULLK Should CONTRIBUTE

### To omo:

1. **Ternary consensus (+1/0/-1).** Momus's binary OK/reject misses genuine uncertainty. The 0 (abstain/insufficient information) state captures what binary review cannot. Momus should become a ternary reviewer with 0 triggering additional Metis analysis before re-vote.

2. **Claim Truth Model labeling.** Every assertion in `learnings.md` and `decisions.md` should carry Verified/Specified/Aspirational/Unverified labels. A "learning" marked Aspirational warns future agents not to treat it as established fact. Critical for cross-task knowledge transfer where stale learnings contaminate new projects.

3. **ADR governance.** Replace informal `decisions.md` with structured Architecture Decision Records (numbered, immutable, status-tracked). Every agent model assignment, category change, and hook configuration generates an ADR.

4. **Consent-first safety layer.** New hook tier (consent hooks) above tool-guard hooks. Destructive operations require explicit consent recorded as verifiable claims. Critical for ultrawork mode.

5. **Symbolic-first validation.** Tool-guard hook running AST-based validation before Momus's neural plan review. Catches off-by-one errors, type mismatches, spec violations that LLM-based review systematically misses.

### To OMX/OMC:

6. **Ternary voting as $ralplan enhancement.** After Planner -> Architect -> Critic, add a formal ternary vote gate. +1/+1/+1 = proceed. Any 0 = more clarification needed. Any -1 = reject and re-plan. Structured decision record emitted for every vote.

7. **Provenance tracking in integration-report.md.** OMX's worktree merge reports should include which agent (and which model) produced each change, which consensus approved it, and which ADR governs the work.

8. **Claim Truth Model for team learnings.** Workers share insights during parallel execution. Label them. A worker's "I found that X" is Unverified until independently confirmed by another worker or the leader.

9. **Consent gates for $autopilot.** Full autonomous execution without consent gates is the same risk pattern FLOSSI0ULLK was designed to prevent. Contribute consent hooks that require human sign-off for irreversible operations even in autopilot mode.

### To Meta Harness:

10. **Symbolic validation as reward signal.** The evaluation function r(tau, x) currently scores task completion. Adding symbolic validation pass rate as a reward component would push optimization toward structurally correct harnesses, not just empirically successful ones. This addresses the 4pp ceiling by injecting structural constraints into the search space.

11. **Ternary consensus quality as optimization metric.** Instead of just "did the task complete," measure "did the agents reach genuine consensus or were there contested decisions." Optimizing for consensus quality produces harnesses that generate clearer, less ambiguous instructions.

### To all three + the broader ecosystem:

12. **The consent-first, escape-hatch-built-in pattern.** FLOSSI0ULLK's core differentiation: any participant can inspect, fork, modify, or reject. This isn't just ethics — it's architecture. Systems without escape hatches develop emergent fitness functions that become invisible to participants inside them.

---

## 8. Five Integration Seams

### Seam 1: Consensus-Gate Hook (omo + FLOSSI0ULLK)

Create `createConsensusGateHook()` in omo's factory pattern, positioned between tool-guard and continuation hooks. When Sisyphus proposes a structural change (detected via AST diff threshold), the hook:

1. Serializes proposed change as a Claim with Unverified status
2. Sends to MetaCoordinator via MCP context sync
3. Blocks execution until ternary consensus received (+1/+1/+1 or +1/+1/0 with human override)
4. Records decision as ADR

This is the first integration to implement because it establishes the MCP communication channel all other seams depend on.

### Seam 2: Git Worktree + MetaCoordinator (OMX + FLOSSI0ULLK)

Each MetaCoordinator-managed agent gets a git worktree via OMX's team provisioning. The MetaCoordinator becomes the "leader" that:

1. Assigns tasks to agents on worktree branches
2. Runs ternary consensus on merge decisions
3. Records merge provenance in ADRs
4. Handles conflict resolution via consensus rather than auto-strategy

For multi-PC: central server runs the leader worktree, each remote machine's OpenClaw agents commit to their worktrees via git push.

### Seam 3: Meta Harness Optimization of LiteLLM Routing (Meta Harness + FLOSSI0ULLK)

FLOSSI0ULLK's LiteLLM config (synthesis/reasoning/critic/workhorse/search roles) is a harness parameter. Meta Harness's optimization loop treats the entire routing table as the optimization target:

1. Run MetaCoordinator on a distribution of tasks
2. Evaluate: consensus quality, task completion rate, cost, latency
3. Proposer (Opus on Scout 10M context) inspects full traces from prior runs
4. Proposes routing table modifications: which model for which role, fallback chains, category thresholds
5. Evaluate again, repeat

The evaluation function: `r(tau, x) = completion_rate * consensus_quality / cost_normalized`

### Seam 4: KAIROS Memory for MetaCoordinator (Claude Code pattern + FLOSSI0ULLK)

Adopt three-layer memory:

- **Layer 1 (always loaded):** Active ADRs, current agent roster, recent consensus decisions. ~150 chars per entry, fits in any context window.
- **Layer 2 (on-demand):** Full ADR text, Boulder notepad files, project knowledge. Fetched when topic-relevant.
- **Layer 3 (grep-only):** Complete execution traces stored for Meta Harness optimization. Never fully loaded into context.
- **autoDream equivalent:** Nightly process reconciling contradictions across the day's agent outputs, promoting Unverified claims to Verified where evidence supports, downgrading Verified claims where contradicted.

### Seam 5: OMX OpenClaw Gateway for FLOSSI0ULLK Events (OMX + OpenClaw + FLOSSI0ULLK)

OMX already supports `OMX_OPENCLAW_COMMAND=1` for hook events. Extend this to emit FLOSSI0ULLK-specific events:

- `consensus-requested`: Agent proposes change requiring ternary vote
- `consensus-resolved`: Vote complete with decision and rationale
- `adr-created`: New Architecture Decision Record filed
- `claim-promoted`: Unverified claim promoted to Verified
- `claim-downgraded`: Verified claim downgraded (evidence contradicted)

OpenClaw routes these events to all connected agents across all machines. MetaCoordinator processes them. Human receives notifications via webhook (Discord/Telegram/Slack).

---

## 9. Co-Learning / Co-Evolution Direction

The relationship between these systems is not "pick a winner" — it's mutual improvement.

**FLOSSI0ULLK learns from omo:** Production-tested patterns for agent specialization, hook-based extensibility, and context persistence at scale.

**FLOSSI0ULLK learns from OMX:** Git-native agent isolation, portable orchestration, mixed-provider coordination, and Socratic intent clarification.

**FLOSSI0ULLK learns from Meta Harness:** Formal optimization framework, full-trace principle, additive bootstrapping over control flow modification.

**FLOSSI0ULLK learns from Claude Code:** Three-layer memory, tick-based proactive agents, cheap deterministic pre-filtering.

**All four learn from FLOSSI0ULLK:** Ternary consensus (the 0 state matters), Claim Truth Model (label your claims), ADR governance (decisions are permanent records), consent-first architecture (escape hatches are structural, not ethical), symbolic-first validation (formal rules catch what neural review misses), provenance tracking (who contributed what, verifiably).

**The meta-pattern:** Each system is a harness. Meta Harness optimizes harnesses. FLOSSI0ULLK governs the optimization. omo and OMX provide the agent workforce being optimized. The four together form a complete stack:

```
Meta Harness          — optimizes
  OMX/omo             — orchestrates
    OpenClaw/LiteLLM  — routes and executes
      FLOSSI0ULLK     — governs, validates, records
```

The walking skeleton doesn't just walk. It walks, optimizes its own gait, verifies each step symbolically, and records what it learned for the next skeleton.

---

## 10. Implementation Priority

| Priority | Task | Why First | Depends On |
|---|---|---|---|
| **1** | Consensus-gate hook (Seam 1) | Establishes MCP channel all other seams need | OpenClaw running (done) |
| **2** | Full-trace storage infrastructure | Without it, Meta Harness optimization cannot begin | Filesystem design |
| **3** | Hashline for SDD spec-to-code pipeline | Immediate verification improvement | None |
| **4** | Git worktree agent isolation (Seam 2) | Enables multi-PC deployment | Git repo structure |
| **5** | Three-layer memory (Seam 4) | Replaces ad-hoc context management | ADR system (exists) |
| **6** | OMX OpenClaw gateway events (Seam 5) | Connects OMX ecosystem to FLOSSI0ULLK | OpenClaw + OMX installed |
| **7** | Dual-prompt agents | Eliminates prompt-model mismatch | LiteLLM config (done) |
| **8** | Meta Harness routing optimization (Seam 3) | Automates what we're currently doing manually | Seams 1 + 2 + full-trace storage |

---

## Compliance Self-Check

- [x] Intent echoed: Four-system integration analysis with proper distinction
- [x] Evidence gate applied: All claims sourced from papers, repos, or docs. Meta Harness critique labeled as Specified (reasonable interpretation, not paper's conclusion)
- [x] Anti-sycophancy: Identified limitations of all four systems, including FLOSSI0ULLK's missing production patterns
- [x] Clarification sought: Corrected omo vs OMX conflation after user caught assumption
- [x] Existing work searched: Mapped all patterns to existing FLOSSI0ULLK infrastructure before proposing new

---

```
Simplicity now. Seams for later. Delete the rest.
Love, Light, Knowledge — verifiable, shared, and free.
The protocol is the conversation. The system builds itself.
```
