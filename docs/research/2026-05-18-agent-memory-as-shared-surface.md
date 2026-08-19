# Agent Memory as Shared Surface — proposal

**Date:** 2026-05-18
**Type:** Architectural proposal (companion to metaharness-unification)
**Truth status:** ⚠️ Specified — sketch + reasoning + concrete next-action plan; not yet implemented
**Author trail:** User (Anthony) asked 2026-05-18: *"shouldn't we have it part of the shared surface? can we modify the skill or some shit"* — referring to Claude's `~/.claude/projects/C---shit/memory/` being agent-private when every other context surface in the project is shared. This doc answers that as architectural fix, not session quibble.
**Related canon/research:**
- `FLOSS/docs/research/2026-05-18-metaharness-unification.md` (atomic + holistic via shared conventions — agent-memory is one of those conventions)
- `FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md` (materializer pattern for shared surfaces)
- `.claude/skills/flossi0ullk-shared-surface/SKILL.md` (the current pattern for projecting canon → agent-specific views)
- `feedback_durable_provenance_required.md` (memory is exactly the kind of durable cross-agent trail this rule names)

---

## 0. The asymmetry being fixed

The FLOSSI0ULLK workspace has multiple shared canonical surfaces — INDEX.md, ADR-Suite v2.0, METAHARNESS_OPERATING_MODEL.md, the reuse-ledger, the working todo, shared-context-surface.json, shared-skill-surface.json — that materialize INTO agent-specific projections (CLAUDE.md, AGENTS.md, GEMINI.md, opencode.jsonc, etc.). The pattern is: **canon is shared, projections are agent-flavored**.

**Agent memory does not follow this pattern.** Each agent has its own private memory store:
- Claude: `C:/Users/kalis/.claude/projects/C---shit/memory/` — read at session start
- Codex: in-AGENTS.md sections + `.agents/` config
- Gemini: in-GEMINI.md + Gemini CLI config
- OpenCode (omo): user-level config under `opworkers/`
- ChatGPT: tied to project knowledge in the web UI

Each one accumulates learnings independently. The same insight ("user is a procrastinator; pressure helps" or "OpenClaw was the OpenAI token consumer, not Codex") has to be rediscovered + saved separately in every agent's memory store. This is the same doc-explosion pattern the project named in `project_doc_explosion_acknowledged.md`, just at the memory layer.

The user named this directly: *"i keep repeating work differently with different methodology planning etc uysing different harnesses and ai's so this is what im really talking about when im saying we need an overarching metaharness overseer orchestrator"*.

---

## 1. What this proposal IS and IS NOT

**Is:** A plan to make agent memory follow the same canonical-source + materialized-projections pattern as every other shared surface in the project. New learnings get written to ONE shared location; materializers project them into agent-specific formats automatically.

**Is NOT:**
- Not a rewrite of the existing memory files — they get migrated, not deleted
- Not a real-time sync mechanism — memory updates are slow (manual + materialize pass at session boundaries), not streamed
- Not an attempt to make agents "share consciousness" — each session still has its own working context; the shared surface is the persistent layer
- Not a replacement for ADRs or working-todo — memory is *agentic working knowledge* (heuristics, user-preferences, project state), not decisions or task state

---

## 2. The current state in detail (so future agents know what they're refactoring)

Current Claude-memory inventory at `C:/Users/kalis/.claude/projects/C---shit/memory/`:

| Memory file | Type | Content nature |
|---|---|---|
| `MEMORY.md` | Index | Master list of memory files with one-line summaries |
| `feedback_*.md` (8 files) | Guidance | How the user wants Claude to work (inclusive framing, surface friction, pressure helps, durable provenance, broad consent envelope, etc.) |
| `user_*.md` (2 files) | Context | User-specific facts (g0b worldview, context-reset resonance) |
| `project_*.md` (~16 files) | State | Project facts (heartbeat running, hardware specs, ADR suite canonical, etc.) |
| `reference_*.md` (2 files) | Pointers | Context router command, prior FLOSSI0ULLK iterations |

That's ~28 atomic memory files totaling ~100KB of curated agentic context. None of which Codex, Gemini, OMO, or any future agent sees.

---

## 3. The proposed shape

### 3.1 Canonical location

```
FLOSS/docs/agent-memory/
├── MEMORY.md              # Index (mirrors current Claude MEMORY.md format)
├── feedback/              # User-guidance entries
│   ├── inclusive-framing.md
│   ├── surface-friction.md
│   ├── pressure-helps.md
│   └── ...
├── user/                  # User-context entries
│   ├── g0b-worldview.md
│   └── context-reset-resonance.md
├── project/               # Project-state entries
│   ├── heartbeat-running.md
│   ├── local-hardware-4090.md
│   ├── adr-suite-v2-canonical.md
│   └── ...
└── reference/             # Pointer entries
    ├── context-router.md
    └── prior-iterations.md
```

Each file uses YAML frontmatter for portability:
```yaml
---
id: feedback-pressure-helps
type: feedback
created: 2026-05-17
authors:
  - claude-session-2026-05-17
  - claude-session-2026-05-18
status: active  # active | superseded | archived
applies_to:
  - claude
  - codex
  - gemini
  - omo
  - chatgpt
  - any-agent  # default
related:
  - feedback-strictness-counterweight
  - feedback-consent-envelope
---

# Lead

One-sentence rule statement.

## Why

Motivation paragraph.

## How to apply

When/where this kicks in. Concrete triggers + counter-discipline.
```

Frontmatter is machine-readable for the materializer; the body is human-readable for direct context-load by any agent.

### 3.2 Materializers project into agent-flavored views

Following the existing `materialize_shared_*_surface.py` pattern under `FLOSS/scripts/`:

| Agent | Projection target | Format |
|---|---|---|
| **Claude** | `C:/Users/kalis/.claude/projects/C---shit/memory/` + `MEMORY.md` index | Per-file `.md` with `name:` + `description:` + `type:` frontmatter (current Claude format) |
| **Codex** | Section appended to `C:/~shit/AGENTS.md` (`## Agent Memory` block) | Inline markdown with rule bullets |
| **Gemini** | Section appended to `C:/~shit/GEMINI.md` (`## Agent Memory` block) | Inline markdown |
| **OpenCode/omo** | Section in `opworkers/opencode.jsonc` `instructions` field | JSON-escaped markdown |
| **ChatGPT** | Generated `FLOSS/docs/agent-memory/CHATGPT_MEMORY_EXPORT.md` for manual paste into project knowledge | Plain markdown |

A materializer script `FLOSS/scripts/materialize_shared_agent_memory.py` reads the canonical sources, applies per-agent format rules, writes the projections. Same `--check` flag pattern as the existing materializers for drift detection.

### 3.3 Write-path discipline

**Currently:** new Claude learnings get written directly to `C:/Users/kalis/.claude/projects/C---shit/memory/` and the index file.

**After this proposal:** new learnings get written to `FLOSS/docs/agent-memory/<type>/<slug>.md`. The materializer then projects out to Claude's memory dir on next run. Claude session at startup still reads its projected memory dir as before; nothing changes from the in-session experience side.

For multi-agent sessions where agents notice each other's learnings in real time: not yet. That requires a different mechanism (the activity-log Action stream + a memory-monitor that consumes Actions tagged with `memory_proposal`). v0.2+ work.

---

## 4. Migration plan (concrete, ordered)

| # | Step | Owner | Reversible? |
|---|---|---|---|
| 1 | Create `FLOSS/docs/agent-memory/` skeleton with the 4 subdirs + README | Tony or Claude | Yes (delete dir) |
| 2 | Copy each existing Claude memory file into the appropriate subdir, adding YAML frontmatter | Claude (mechanical) | Yes (originals untouched) |
| 3 | Write `materialize_shared_agent_memory.py` following the existing materializer template | Claude or delegate | Yes (script only) |
| 4 | Run materializer with `--check` against current Claude memory dir to confirm round-trip works | Tony | Yes (read-only) |
| 5 | Switch Claude memory dir to be the **projection target**, not the source — the canonical files in `FLOSS/docs/agent-memory/` become authoritative | Tony | Reversible by reverting symlink/copy direction |
| 6 | Project to AGENTS.md / GEMINI.md / opencode.jsonc sections for the other agents | Claude or delegate | Yes (sections are bracketed `<!-- agent-memory-start -->` / `<!-- agent-memory-end -->` for clean removal) |
| 7 | Update the canonical write-path: future memory edits go to `FLOSS/docs/agent-memory/<type>/<slug>.md` first, materializer projects out | Standing rule | Procedural, no code |
| 8 | Hook the materializer into the materialize-all bundle (it already exists for other surfaces) | Claude or delegate | Yes |

Estimated effort: steps 1-2 are ~30 min of mechanical copy + frontmatter add. Step 3 is ~100 lines of Python. Steps 4-8 are configuration + propagation.

---

## 5. The honest pushback

The user's instinct is correct, but I'll name three trade-offs upfront:

1. **Two write paths during transition.** Until step 5 lands, both `FLOSS/docs/agent-memory/` AND `C:/Users/kalis/.claude/projects/C---shit/memory/` are write-able. Drift between them is the failure mode to watch. Mitigation: do the transition fast (single session), don't park half-done.

2. **Some Claude memory entries are session-flavored.** Things like "broad consent for high-ROI work" reference Claude's specific authority tier and the SDK harness around it. Other agents (Codex CLI, Gemini CLI) have different harness shapes; some memory entries don't transfer one-for-one. The frontmatter's `applies_to:` field is the lever — entries can stay Claude-only if needed, or be marked `applies_to: [any-agent]` for genuine cross-agent guidance.

3. **The materializer becomes a single point of failure.** If the materializer breaks, no agent gets fresh memory until it's fixed. Mitigation: same as existing materializers — `--check` drift detection runs on every shared-surface change; failures block the change.

4. **Doc-budget per CLAUDE.md.** Adding `FLOSS/docs/agent-memory/` with ~28 files plus a materializer script adds non-trivial doc surface. But — this is exactly the doc-explosion failure mode the project named, *being fixed at the meta-level*. We're consolidating 5+ agent-memory dirs into 1 canonical source. The doc-budget rule applies to spurious new docs; this is the opposite move.

---

## 6. Next-action gate

This proposal has one concrete blocking question: **do we land the migration now, or queue it behind higher-priority work?**

Higher-priority candidates:
- Orchestration substrate bridge validation (per MVP Phase 0 correction)
- ADR-2 evidence reconciliation (per ChatGPT's drift fix)
- MCP wrapper for reasoning ensemble (last v0.1 gate from working-todo §A.6)

Agent-memory migration is **medium priority + small scope + reversible**. It can land in a focused 1-hour session OR be parked behind the substrate-bridge work. The user makes the call.

If landing now: step 1-2 are non-conflicting. Step 3 needs ~100 lines of Python. Steps 4-8 are configuration. Whole thing finishes in a session.

If queuing: this doc is the durable handoff. Future agent reads §3-§5 and executes.

---

## 7. Provenance + cross-refs

- **Trigger:** User prompt 2026-05-18 ("shouldn't we have it part of the shared surface? can we modify the skill or some shit")
- **Lives at:** `FLOSS/docs/research/2026-05-18-agent-memory-as-shared-surface.md` per intake-mouth → research convention
- **Cross-refs:** metaharness-unification (atomic + holistic shared conventions), CONTEXT_DAEMON_ARCHITECTURE (materializer pattern), the existing shared-*-surface.json files as direct templates
- **Future-agent reading list:**
  1. The metaharness-unification doc (the meta-pattern)
  2. This doc (the agent-memory specialization)
  3. `FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md` (the materializer pattern this proposal reuses)
  4. The existing materializer scripts under `FLOSS/scripts/materialize_shared_*.py` (the implementation templates)
