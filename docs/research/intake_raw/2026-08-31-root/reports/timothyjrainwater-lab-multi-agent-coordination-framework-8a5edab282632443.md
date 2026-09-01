Directory structure:
└── timothyjrainwater-lab-multi-agent-coordination-framework/
    ├── README.md
    ├── LICENSE
    ├── METHODOLOGY.md
    ├── case-study/
    │   ├── FAILURE_CATALOG.md
    │   ├── LESSONS_LEARNED.md
    │   ├── METRICS.md
    │   └── PROJECT_OVERVIEW.md
    ├── patterns/
    │   ├── ARTIFACT_PRIMACY.md
    │   ├── AUTHORITY_TAGGING.md
    │   ├── CONCURRENT_SESSION_PROTOCOL.md
    │   ├── CONSUME_SITE_VERIFICATION.md
    │   ├── COORDINATION_FAILURE_TAXONOMY.md
    │   ├── CROSS_FILE_CONSISTENCY.md
    │   ├── DEBRIEF_INTEGRITY_BOUNDARY.md
    │   ├── DISCOVERY_QUEUE_TRACEABILITY.md
    │   ├── DISPATCH_SELF_CONTAINMENT.md
    │   ├── ENFORCEMENT_HIERARCHY.md
    │   ├── HIDDEN_ASSUMPTION_SWEEP.md
    │   ├── INTEGRATION_CANARY.md
    │   ├── PARALLEL_IMPLEMENTATION_PARITY.md
    │   ├── PLAIN_ENGLISH_PASS.md
    │   ├── PM_CONTEXT_COMPRESSION.md
    │   ├── POST_DEBRIEF_RETROSPECTIVE.md
    │   ├── PROACTIVE_ASSUMPTION_SWEEP_CADENCE.md
    │   ├── RESEARCH_TO_BUILD_PIPELINE.md
    │   ├── ROLE_SEPARATION.md
    │   ├── SESSION_BOOTSTRAP.md
    │   ├── STAGED_CONTEXT_LOADING.md
    │   ├── SWEEP_AUDIT_PROTOCOL.md
    │   └── WORKTREE_ISOLATION_PROTOCOL.md
    └── templates/
        ├── AUDIT_DISPATCH_TEMPLATE.md
        ├── HANDOFF_TEMPLATE.md
        ├── ONBOARDING_CHECKLIST_TEMPLATE.md
        ├── SESSION_MEMO_TEMPLATE.md
        ├── SOURCES_OF_TRUTH_TEMPLATE.md
        └── WORK_ORDER_TEMPLATE.md

================================================
FILE: README.md
================================================
# Multi-Agent LLM Coordination Framework

**A practical methodology for coordinating multiple AI agents on complex software projects.**

Built and proven on an 8,521+ test, 338-formula deterministic game engine — by a non-technical operator (former chef, English educator) coordinating Claude Opus, Claude Sonnet, and other LLM agents with zero shared memory across 100+ agent sessions over 4+ months.

---

## The Problem

When you use multiple LLM agents to build software, you hit walls that don't exist in solo development:

- **Agents forget everything between sessions.** Every new context window starts from zero.
- **Parallel agents conflict.** Two sessions editing the same file produce merge disasters.
- **Nobody holds the full picture.** No single agent (or human) can keep the entire project in context.
- **Documents drift from reality.** Agent-written docs become stale, contradictory, and self-reinforcing.
- **The human coordinator becomes the bottleneck.** You can't read everything, and you can't tell which agent is right when they disagree.

These aren't theoretical problems. They're what happens on Day 3 of any serious multi-agent project. This framework documents the solutions we discovered by breaking things and codifying the fixes.

---

## What Makes This Different

Most AI coordination guides tell you what to do. This one shows you what went wrong.

**From the proving ground (D&D 3.5e combat engine):**
- 8,521+ automated tests across 9 verification domains
- 338 formulas verified against source rules
- 30 bugs found and categorized into 12 coordination error patterns
- 100+ work orders dispatched across 100+ agent sessions over 4+ months
- 3 of 7 parallel agents silently failed to commit in one dispatch — the fix became a governance pattern

Every pattern in this framework exists because something specific broke. The [failure catalog](case-study/FAILURE_CATALOG.md) has the receipts.

---

## Who This Is For

- **Non-technical builders** using AI agents to construct software ("vibe coders")
- **Developers** scaling from one AI assistant to a fleet of specialized agents
- **Researchers** studying multi-agent LLM coordination
- Anyone who has had an AI agent confidently break something another agent just fixed

---

## Core Principles

### 1. Artifact Primacy
> If it's not in a file, it doesn't exist.

Agents have perfect recall within a context window and zero recall across context boundaries. Conversational knowledge vanishes at session end. Every fact, decision, and status that must survive a context rotation must be pinned to a file.

**Implication:** Your project's files aren't just code and docs — they're the only shared memory your agent fleet has.

### 2. Staged Context Loading
> Reading order matters more than reading volume.

Agents waste context window space when they read files in the wrong order or read everything at once. A defined reading sequence — orientation first, then state, then rules — gets agents operational in minimal context.

**Pattern:** Compass (what is this?) → State (what's done?) → Rules (how do we work?) → Task (what do I do?)

### 3. Dispatch Self-Containment
> Every work order must be executable by an agent with zero prior context.

The work order plus the files it references must contain everything an agent needs. No reliance on "the previous agent will have explained this." Test: could a brand-new agent execute this dispatch using only the dispatch file and linked references?

### 4. Machine Truth Over Prose Truth
> When a script and a document disagree, the script is right.

Agent-written prose drifts from reality within 3-4 handoffs. Machine-generated state (test counts, git status, automated snapshots) doesn't. Build scripts that produce canonical facts, and treat everything else as commentary.

### 5. Protocol Over Memory
> Solve coordination with protocols, not shared state.

You can't give agents shared memory. You can give them protocols — handoff checklists, consistency gates, session scope declarations, structured memo formats. The protocols are the coordination mechanism.

---

## Framework Components

### Patterns
Reusable solutions to specific coordination problems. Each pattern documents the problem, the solution, when to use it, and a real example from the proving ground.

| Pattern | Problem It Solves | Solution |
|---------|------------------|----------|
| [Enforcement Hierarchy](patterns/ENFORCEMENT_HIERARCHY.md) | Corrections don't stick across sessions | 3-tier model: test-enforced > process-enforced > prose-enforced |
| [Staged Context Loading](patterns/STAGED_CONTEXT_LOADING.md) | Agents waste context reading files in wrong order | Defined reading sequence that orients agents in minimal context |
| [Dispatch Self-Containment](patterns/DISPATCH_SELF_CONTAINMENT.md) | Work orders fail because agents lack context | Self-contained work orders that amnesiac agents can execute |
| [Artifact Primacy](patterns/ARTIFACT_PRIMACY.md) | Knowledge lost between sessions | Pin every decision to a file — conversation doesn't survive |
| [Cross-File Consistency Gate](patterns/CROSS_FILE_CONSISTENCY.md) | Partial updates create contradictions | All-or-nothing updates across every file referencing a fact |
| [Session Bootstrap](patterns/SESSION_BOOTSTRAP.md) | Agents start with stale assumptions | Machine-verified truth (tests, git status) before prose documents |
| [Concurrent Session Protocol](patterns/CONCURRENT_SESSION_PROTOCOL.md) | Parallel sessions conflict on shared files | Explicit file ownership with no overlaps between agents |
| [PM Context Compression](patterns/PM_CONTEXT_COMPRESSION.md) | Human coordinator can't read everything | Structured information flow to a bandwidth-limited human |
| [Coordination Failure Taxonomy](patterns/COORDINATION_FAILURE_TAXONOMY.md) | Same mistakes repeat across projects | Categorized catalog of what goes wrong and why |
| [Role Separation](patterns/ROLE_SEPARATION.md) | Agents assume they can do everything | Five-role model with explicit authorities and boundaries |
| [Research-to-Build Pipeline](patterns/RESEARCH_TO_BUILD_PIPELINE.md) | Raw insights produce scope bleed when dispatched directly | Staged conversion: Burst → Research → Brick → Builder WO |
| [Plain English Pass](patterns/PLAIN_ENGLISH_PASS.md) | Non-technical operators can't parse technical debriefs | 3-question translation layer before the technical dump |
| [Debrief Integrity Boundary](patterns/DEBRIEF_INTEGRITY_BOUNDARY.md) | Agent self-reports are trusted without verification | Named trust boundary with verification spectrum and mitigations |
| [Integration Canary](patterns/INTEGRATION_CANARY.md) | Unit tests pass but product doesn't work end-to-end | One script that exercises the full product path before new WOs |
| [Parallel Implementation Parity](patterns/PARALLEL_IMPLEMENTATION_PARITY.md) | Same logic implemented in multiple paths drifts silently | Enumerate all parallel paths on every WO; verify parity before debrief |
| [Sweep Audit Protocol](patterns/SWEEP_AUDIT_PROTOCOL.md) | Sequential WOs can't see system-wide coherence drift | Periodic read-only audits that cross-check subsystems for consistency |
| [Authority Tagging](patterns/AUTHORITY_TAGGING.md) | Community convention ships instead of specification | Every domain-logic WO declares SPEC or POLICY authority — no third type |
| [Post-Debrief Retrospective](patterns/POST_DEBRIEF_RETROSPECTIVE.md) | Builder peripheral observations die in context windows | Mandatory post-debrief question surfaces what the builder noticed |
| [Hidden Assumption Sweep](patterns/HIDDEN_ASSUMPTION_SWEEP.md) | Small questions that reframe architecture go unclassified | 10-question triage protocol converts grenades into named artifacts |
| [Worktree Isolation Protocol](patterns/WORKTREE_ISOLATION_PROTOCOL.md) | Parallel agents collide at filesystem level despite non-overlapping file scope | One git worktree per active builder — isolation at the OS level, not just the work order level |
| [Proactive Assumption Sweep Cadence](patterns/PROACTIVE_ASSUMPTION_SWEEP_CADENCE.md) | Reactive sweeps miss confidently-wrong assumptions | Scheduled 10-question sweeps on a fixed cadence — pair with every audit dispatch |

### Templates
Ready-to-use file templates for implementing the patterns in your own project.

| Template | Purpose | File |
|----------|---------|------|
| [Onboarding Checklist](templates/ONBOARDING_CHECKLIST_TEMPLATE.md) | Reading order + verification steps for new agents | Implements Staged Context Loading |
| [Work Order Dispatch](templates/WORK_ORDER_TEMPLATE.md) | Self-contained task assignment | Implements Dispatch Self-Containment |
| [Audit Work Order](templates/AUDIT_DISPATCH_TEMPLATE.md) | Read-only audit task assignment (never writes code) | Implements Sweep Audit Protocol |
| [Handoff Document](templates/HANDOFF_TEMPLATE.md) | End-of-session knowledge transfer | Implements Artifact Primacy |
| [Session Memo](templates/SESSION_MEMO_TEMPLATE.md) | Structured report to human coordinator | Implements PM Context Compression |
| [Sources of Truth Index](templates/SOURCES_OF_TRUTH_TEMPLATE.md) | Which file is authoritative for which concept | Implements Machine Truth Over Prose |

### Case Study
How these patterns were discovered and proven on a real project.

| Document | Content |
|----------|---------|
| [Project Overview](case-study/PROJECT_OVERVIEW.md) | What was built, by whom, scale and complexity |
| [Failure Catalog](case-study/FAILURE_CATALOG.md) | Real coordination failures, categorized with root causes |
| [Metrics](case-study/METRICS.md) | Quantitative results — formulas verified, bugs found, reclassification rates |
| [Lessons Learned](case-study/LESSONS_LEARNED.md) | What worked, what didn't, what we'd do differently |

---

## Quick Start

**If you're non-technical** and want to learn this methodology from scratch, start with the **[Methodology Guide](METHODOLOGY.md)** — a step-by-step walkthrough written for someone who has a problem, has access to AI agents, and has no idea how to start.

**If you're already running agents** and want to add specific coordination patterns, start here:

1. **Create an onboarding checklist** ([template](templates/ONBOARDING_CHECKLIST_TEMPLATE.md)) — this is the single highest-impact intervention. Define what agents read, in what order.

2. **Create a sources of truth index** ([template](templates/SOURCES_OF_TRUTH_TEMPLATE.md)) — before your second session, decide which file is authoritative for each concept.

3. **Write self-contained work orders** ([template](templates/WORK_ORDER_TEMPLATE.md)) — the moment you start dispatching tasks to agents, the dispatch must stand alone.

4. **Add a session bootstrap script** ([pattern](patterns/SESSION_BOOTSTRAP.md)) — even a simple script that prints git status + test count grounds the agent in reality instead of potentially-stale docs.

5. **Use handoff documents** ([template](templates/HANDOFF_TEMPLATE.md)) — when a session ends, write what the next agent needs to know. This is not optional.

---

## Origin

This framework wasn't designed top-down. It was discovered bottom-up by a non-technical operator coordinating multiple AI agents (Claude Opus, Claude Sonnet, GPT-4) to build a D&D 3.5e deterministic referee engine. Every pattern exists because something broke and the fix got codified into a protocol.

**Project stats (updated 2026-02-27):**
- 8,521+ automated tests (zero regressions across all accepted batches)
- 338 formulas verified against source rules across 9 domains
- 30 bugs found and categorized into 12 error patterns
- 100+ work orders dispatched (fix, feature, research, governance, audit, framework)
- 50+ builder debriefs archived
- 30 research documents produced
- 100+ agent sessions coordinated through file-based protocols
- 25+ delivery batches, each with gate tests as the acceptance arbiter
- Every governance document born from a specific, documented failure

**The operator's background:** Former chef, current English educator, zero programming experience. The methodology emerged because protocols were the only tool available — and it turns out protocols are the right tool for coordinating agents that can't remember yesterday.

---

## Contributing

This is a living framework. If you're using these patterns on your own multi-agent project, your failure cases and solutions make the framework better. Open an issue with:
- What pattern you tried
- What worked or didn't
- What coordination failure you hit that isn't in the taxonomy

---

## License

MIT License — use freely, adapt to your projects, share what you learn.

---

*"Creative in voice, strict in truth, accountable in every outcome."*



================================================
FILE: LICENSE
================================================
MIT License

Copyright (c) 2026 Timothy J. Rainwater

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.



================================================
FILE: METHODOLOGY.md
================================================
# The Methodology: How to Build Software with AI Agents When You Don't Know How to Code

A practitioner's guide for someone who has a problem, has access to AI agents, and has no idea how to start.

---

## Who This Is For

You're a person with a project idea. Maybe you want to build an app, automate a workflow, or create a tool that doesn't exist yet. You've used ChatGPT or Claude or another AI to write code snippets, and it worked — sort of. But now you want to build something real, something with hundreds or thousands of files, something that needs to work reliably and grow over time.

You don't know how to code. Or you know a little, but not enough to build what you're imagining. You've heard you can use AI agents to do the building, but every guide you've found either assumes you're already a developer or waves its hands at the hard parts.

This document is the hard parts.

It's written by a non-technical operator (former chef, English educator) who used this methodology to build an 8,500+ test software system by coordinating AI agents through file-based protocols over 4+ months. Every recommendation comes from something that actually happened — usually something that went wrong first.

---

## Before You Start: Three Things to Understand

### 1. AI agents forget everything between sessions

Every time you start a new conversation with an AI agent, it knows nothing about your project. It doesn't remember yesterday's session. It doesn't remember the decisions you made. It doesn't remember the code it wrote. Each session starts from absolute zero.

This is the single most important fact about multi-agent coordination. Everything in this methodology exists because of it.

**What this means for you:** You cannot rely on conversation to coordinate your project. You must rely on files. Every decision, every piece of context, every status update — if it's not written down in a file, it doesn't exist when the next session starts.

### 2. AI agents will do whatever seems helpful unless you tell them not to

If you ask an agent to fix a bug and it notices a different bug nearby, it will probably fix that one too. If you ask it to write a function and it thinks the surrounding code could be better, it will refactor it. This sounds helpful. It isn't.

When you have multiple agents working on the same codebase, an agent that "helpfully" modifies files outside its assigned scope will collide with other agents working on those same files. You'll spend more time untangling the conflicts than the "helpful" fix was worth.

**What this means for you:** You need to tell agents exactly what to do, exactly what files to touch, and explicitly what NOT to do. Constraints are not bureaucracy — they're what makes parallel work possible.

### 3. You are not the coder — you are the coordinator

Your job is not to understand the code. Your job is to understand the project: what needs to happen, in what order, and whether what the agents produced actually works. You're the project manager, not the programmer.

This is a genuine skill. It's not a lesser version of programming. It's a different job — and it's the job that determines whether the project succeeds or fails, because no individual agent can hold the full picture. Only you can.

---

## Phase 1: Your First Session (Day 1)

### Start with one agent and one goal

Don't try to set up infrastructure, governance, or coordination protocols on Day 1. Start with the smallest version of your actual project that an agent can build in a single session.

**Example:** If you're building a game engine, don't start with "build the game engine." Start with "create a function that rolls a 20-sided die and adds a modifier to the result." If you're building an app, don't start with the app — start with one screen that does one thing.

### Tell the agent what you want in plain language

You don't need to use programming terms. Describe what the thing should do, not how it should work internally. The agent knows how to code. You know what the product should do.

```
I want to build a program that tracks my restaurant's daily food costs.
For today, just build the part that lets me enter an ingredient, its quantity,
and its price. Store it in a file. Show me a total at the end.
```

### Ask the agent to write tests

Even if you don't know what tests are, ask for them. Say: "Write tests that prove this works correctly." Tests are how you'll know whether future changes break what you already built. They're the only reliable truth in your project.

After the agent writes the tests, ask it to run them. Look at the output. You should see something like "15 tests passed, 0 failed." That number matters. Write it down.

### Before the session ends: save your context

When you're about to end your first session, ask the agent:

```
Before we stop, write a handoff document that tells the next agent everything
it needs to know to continue this project. Include:
- What we built today
- What files exist and what they do
- What tests exist and whether they pass
- What we decided and why
- What's left to do
```

This handoff document is the first artifact of your project. It's also the most important file you'll create today, because it's the only thing that survives to tomorrow.

---

## Phase 2: Building the Foundation (Days 2-5)

### The "second session problem"

On Day 2, you start a new session. The agent knows nothing. You need to get it oriented quickly. This is where most people hit their first wall — they try to explain the project conversationally, the agent builds a partial mental model, and things go sideways because the agent's understanding doesn't match reality.

**The fix:** At the start of every session, before asking the agent to do anything, have it read your project files in a specific order:

1. **The handoff document** — what was built, what's left
2. **The codebase** — key files, not everything
3. **The tests** — run them, report the count

This is the [Session Bootstrap](patterns/SESSION_BOOTSTRAP.md) pattern. It sounds mechanical. It prevents an entire category of failures where agents build on top of stale or incorrect assumptions.

### Create your Sources of Truth index

By Day 2, you have at least two sessions' worth of files. Some of those files might say conflicting things. Your job: decide which file is the truth for each concept.

Create a simple file that says:

```markdown
# Sources of Truth

- **What the code does:** The test suite (run it, don't read about it)
- **What we've decided:** DECISIONS.md
- **What's been built:** HANDOFF.md (updated each session)
- **What's left to do:** TODO.md
```

This prevents the failure where an agent reads an outdated document and builds on top of wrong information. When two files disagree, this index tells you (and the agent) which one is right.

### Start writing work orders

At some point in the first week, you'll want the agent to do something specific — fix a bug, add a feature, change how something works. Instead of describing it conversationally, write it down in a file.

A work order is just a file that says:

1. **What to do** (specific, concrete)
2. **Why** (what problem this solves)
3. **What files to touch** (and what files NOT to touch)
4. **How to verify it worked** (what test to run)

The [Work Order Template](templates/WORK_ORDER_TEMPLATE.md) has a full format, but even a rough version is better than a conversational description. The work order survives the session. The conversation doesn't.

### Keep a decisions log

Every time you make a decision about the project — "we're using Python, not JavaScript," "the damage formula rounds down, not up," "users log in with email, not username" — write it in a DECISIONS.md file.

Agents will re-ask questions you've already answered. They're not being difficult — they literally don't remember. The decisions log is how you answer without repeating yourself: "Read DECISIONS.md, item 7."

---

## Phase 3: Scaling Up (Week 2+)

### When one agent isn't enough

At some point your project gets big enough that a single agent session can't hold the full context. You'll notice this when agents start making mistakes because they didn't read a relevant file, or when sessions end before the work is done because the agent used up its context window reading files.

This is when you need multiple agents working in parallel. And this is where coordination becomes the actual work.

### The rules for parallel agents

If you're going to have multiple agents working on your project simultaneously, you need three things:

**1. File ownership.** Each agent gets an explicit list of files it's allowed to modify. No overlaps. If Agent A is working on the login system and Agent B is working on the database, neither touches the other's files. This prevents merge conflicts and ensures each agent's changes are independent.

**2. Self-contained work orders.** Each agent gets a work order that contains everything it needs. No "check with the other agent" or "this depends on what Agent B decides." Each work order stands alone. If Agent B's work order requires a decision that Agent A hasn't made yet, Agent B shouldn't have been dispatched yet.

**3. Post-completion verification.** When an agent says "done," check the actual output. Run `git diff` to see what files changed. Run the tests. 43% of our parallel agents reported "task complete" with zero code changes on disk. The agent believed it was done. The files said otherwise.

### Introduce roles

Once you're running parallel sessions, you need to separate what different agents do. Not every agent should do everything. Define roles:

- **Builder agents** write code and tests. They get work orders, they execute, they report what they did.
- **Researcher agents** investigate questions. They read code, read documentation, and produce findings — but they don't modify code.
- **Auditor agents** check other agents' work. They cross-reference outputs against requirements and flag discrepancies.

You — the operator — are the coordinator. You don't write code. You don't research. You set direction, make decisions, and route information between agents.

Why separate roles? Because an agent that's building code shouldn't also be researching alternatives. That wastes its context window on exploration when it should be spending it on implementation. And an agent that's auditing shouldn't also be fixing what it finds — the fix might conflict with another agent's in-progress work.

See the [Role Separation](patterns/ROLE_SEPARATION.md) pattern for the full model.

### The PM role (the role you'll grow into)

As your project scales, you'll find that you spend most of your time doing the same things:

- Reading what agents produced
- Deciding what needs to happen next
- Writing work orders for the next round of agents
- Compressing technical output into something you can reason about

This is the PM role. In the early days, you're both the operator (decision maker) and the PM (coordinator). As the project grows, you may want to dedicate an agent session specifically to PM work — reading debriefs, organizing findings, drafting work orders for your approval.

The key insight: **you build understanding by reading agent outputs, not code.** You never need to understand the codebase at the code level. You need to understand what was done, whether it worked, and what it means for the project's direction. Agent debriefs, structured correctly, give you this.

---

## Phase 4: The Research-to-Build Pipeline (When Your Ideas Get Complex)

### The problem with jumping straight to building

Eventually you'll have an idea that's too complex to dispatch directly to a builder. "Add voice input to the system." "Make the app work offline." "Support multiplayer."

If you dispatch these as builder work orders, the builder will have to make dozens of design decisions during the build. Some of those decisions will be wrong. You'll discover they're wrong after the code is written. Rework follows.

### The pipeline

Instead of going straight from idea to build, run your ideas through a pipeline:

**Step 1 — Capture the idea.** Write it down in an intake file. One sentence. Don't try to spec it out yet. ("Voice input should feel reliable, not experimental.")

**Step 2 — Research it.** Draft a research work order that asks a specific question: "What is the cold start time of the TTS engine? What are the options for reducing it?" Send a researcher agent to investigate. The output is a findings memo — not code, not a plan, just findings.

**Step 3 — Normalize the findings into a "Brick."** This is the critical conversion step. You (or a PM agent) take the research findings and produce a structured packet:
- **Target Lock:** One sentence describing the end state
- **Binary Decisions:** Choices you need to make (with exactly two options each)
- **Contract Spec:** The technical specification
- **Implementation Plan:** The ordered list of builder work orders

**Step 4 — Resolve the decisions.** Read the binary decisions. Pick one option for each. You don't need to understand the technical details — the Brick should present each option in terms of tradeoffs you can evaluate. ("Option A: faster but uses more memory. Option B: slower but runs on any machine.")

**Step 5 — Dispatch builders.** Once decisions are resolved, draft builder work orders from the Brick. Each work order is self-contained. The builder never sees the upstream research — only the spec.

This pipeline sounds heavy. For simple features, skip it and go straight to a builder work order. For anything with design ambiguity — anything where you'd say "I'm not sure how this should work" — the pipeline prevents expensive rework.

See the [Research-to-Build Pipeline](patterns/RESEARCH_TO_BUILD_PIPELINE.md) pattern for the full implementation.

---

## Phase 5: Governance (What You Build After Things Break)

### Why governance documents exist

Every governance document in this framework was created after a failure. The cross-file consistency gate was created after an agent updated one file but forgot the other three. The session bootstrap pattern was created after an agent confidently built on top of stale information. The post-completion verification gate was created after three agents said "done" with zero code changes.

You will have failures. The question is whether you codify the fix into a protocol that prevents recurrence, or whether you have the same failure again in two weeks.

### The governance documents you'll create (and when)

You don't need to create these upfront. Create each one when you need it:

**After your second session:**
- Sources of Truth index (which file is authoritative for which concept)
- Handoff template (standardize what agents write at session end)

**After your first parallel dispatch:**
- Work order template (standardize task assignments)
- Post-completion verification checklist (check `git diff` before accepting results)

**After your first coordination failure:**
- Whatever protocol prevents that specific failure from happening again. Write it down, put it in a governance file, and reference it in future work orders.

**After you have 5+ governance files:**
- An onboarding checklist (reading order for new agents) — so agents don't waste context reading governance documents in random order

### The enforcement hierarchy

Not all rules are created equal. You'll discover this when agents violate a rule you thought was clear:

- **Tier 1: Test-enforced.** If breaking the rule causes a test to fail, the agent can't ship the violation. Compliance rate: ~100%.
- **Tier 2: Process-enforced.** If breaking the rule is caught by a template section or a checklist step, the agent usually follows it. Compliance rate: ~70-80%.
- **Tier 3: Prose-enforced.** If the rule is written in a document but not enforced by anything, agents violate it routinely. Compliance rate: ~40-60%.

When a rule matters, push it up the hierarchy. A file-count cap written in a README will be violated. A file-count cap enforced by a pre-commit test won't be.

See the [Enforcement Hierarchy](patterns/ENFORCEMENT_HIERARCHY.md) pattern.

---

## Phase 6: Staying in Control at Scale

### The briefing file

When your project reaches 20+ sessions and dozens of artifacts, you'll lose the ability to hold the full picture in your head. This is normal. You need a single file that gives you the current state of the project in under 5 minutes of reading.

Create a rolling briefing file. Update it after each cycle (batch of dispatches + results). It should answer:

1. What's in progress right now?
2. What's blocked and why?
3. What finished since last briefing?
4. What decisions do I need to make?
5. What's coming next?

This file is your cockpit. Everything else is reference material.

### Reading debriefs (your primary learning channel)

You build understanding of your project by reading what agents did, not by reading code. Agent debriefs — structured reports of what they built, what worked, what didn't, and what they're concerned about — are your primary learning channel.

Require a structure that includes a plain-language section:

1. **What problem did this solve?** (1-2 sentences, no technical jargon)
2. **What does it actually do?** (1-2 sentences, describe the mechanism in everyday language)
3. **Why should anyone care?** (1-2 sentences, describe the user-facing impact)

Below the plain-language section, the agent can dump all the technical detail it wants. But the plain-language section is for you, and it's what lets you make informed decisions about the project's direction without needing to understand the code.

See the [Plain English Pass](patterns/PLAIN_ENGLISH_PASS.md) pattern.

### The debrief trust problem

Agents self-report. There's no guarantee their self-report is accurate. An agent can say "all tests pass" when they don't. An agent can say "I considered three approaches" when it tried one. An agent can say "no concerns" when it didn't think about potential problems.

You need to distinguish between what you can verify and what you have to trust:

- **Machine-verifiable:** Test pass counts, `git diff` output, commit hashes. These are facts.
- **Process-verifiable:** Did the agent follow the template? Are all sections filled out? Did it reference the correct files? These are checkable.
- **Prose-only:** The agent's retrospective, methodology notes, concerns section. These are trust.

Expand the machine-verifiable surface whenever possible. Require agents to include `git diff --stat` output in their debriefs so you can see exactly what files changed. Require test output so you can see pass/fail counts. The more structured data you require, the harder it is for incomplete work to hide behind prose.

See the [Debrief Integrity Boundary](patterns/DEBRIEF_INTEGRITY_BOUNDARY.md) pattern.

---

## The Mistakes You'll Make (and How to Recover)

These are not hypothetical. They all happened.

### Mistake 1: Trusting "task complete"

An agent says it's done. You move on. Later you discover nothing was actually written to disk. Three out of seven agents did this to us in a single batch.

**Recovery:** Always check `git diff` after an agent reports completion. If the diff is empty and it shouldn't be, the agent didn't actually do the work.

### Mistake 2: Letting documents drift

A document says the project has 98% confidence. A verification pass reveals a 5.5% error rate. The document was written once and never updated.

**Recovery:** Date every document. Run machine verification (tests, diffs) before trusting any prose claim. When a document makes a quantitative claim, verify it against the actual data.

### Mistake 3: Not enforcing scope boundaries

An agent fixes a bug and also refactors three nearby functions. Another agent, working in parallel, was about to modify those same functions. Conflict.

**Recovery:** Work orders should include a "What NOT to Do" section. If an agent finds something outside its scope, it notes it in the debrief. The PM drafts a new work order. The agent does not fix it.

### Mistake 4: Assuming research is the same as building

You learn about a technology, get excited, and dispatch a builder to implement it. The builder makes design decisions you didn't anticipate. The result doesn't match what you wanted.

**Recovery:** Separate research from building. Research produces findings. The PM converts findings into a spec. The builder implements the spec. If the spec requires decisions, the operator makes them before the builder starts.

### Mistake 5: Growing the inbox without a triage system

You produce work orders, research memos, debriefs, audit findings. The inbox hits 23 items. You can't process them fast enough. Important items get buried.

**Recovery:** Create a briefing file immediately. Triage everything into a prioritized queue. Process the queue in order. Archive completed items so the inbox stays manageable.

---

## The Toolkit (Minimum Viable Setup)

If you're starting today, here's the minimal set of files to create:

| File | Purpose | When to Create |
|------|---------|----------------|
| `HANDOFF.md` | What the next agent needs to know | End of Day 1 |
| `DECISIONS.md` | Every decision made, with rationale | Day 1 |
| `SOURCES_OF_TRUTH.md` | Which file is authoritative for what | Day 2 |
| `ONBOARDING_CHECKLIST.md` | Reading order for new agent sessions | When you have 5+ project files |
| Work orders (per task) | Self-contained task assignments | When you start dispatching specific tasks |
| `BRIEFING.md` | Rolling project status | When you can't hold the full picture in your head |

Don't create governance documents you don't need yet. Each one should be born from a specific problem you encountered. If you haven't had the failure, you don't need the protocol.

---

## How to Know It's Working

You're doing this right when:

- **A brand-new agent can start working within its first few messages** because the onboarding checklist and handoff document tell it everything it needs.
- **You can dispatch work to multiple agents in parallel** and their outputs don't conflict.
- **You can explain what your project does and where it's going** without understanding the code — because the debriefs and briefing file give you that understanding.
- **When something breaks, you know why** and you can point to the governance document that should have prevented it (or create one that will prevent it next time).
- **Your test count goes up over time** and never goes down. Tests are the only reliable measure of progress. Everything else is commentary.

You're doing this wrong when:

- You spend most sessions re-explaining the project to agents.
- Agents keep modifying the same files and creating conflicts.
- You have documents that contradict each other and you're not sure which is right.
- An agent says "done" and you have no way to verify that's true.
- You're afraid to make changes because you don't know what will break.

---

## One Last Thing

This methodology was built by someone who couldn't code, for people who can't code. It works. It produced a system with over 8,500 tests, verified against primary sources, with every significant coordination failure cataloged and resolved.

But it's not magic. You'll still have sessions that go sideways. Agents will still misunderstand your instructions. Work orders will still have gaps. The difference is that every failure becomes a protocol, and every protocol makes the next session better.

The compound effect is real. By Day 20, your coordination infrastructure is so robust that new agents become productive in minutes, not hours. By Day 30, you're dispatching 7 parallel agents and recovering from failures in the same session they occur. The early investment in files, protocols, and governance pays for itself many times over.

Start small. Write things down. Trust the files, not the conversation. Build the governance when it hurts, not before.

That's the methodology.



================================================
FILE: case-study/FAILURE_CATALOG.md
================================================
# Failure Catalog

Real coordination failures encountered during the D&D 3.5e referee engine build. Each entry documents what happened, why, and what protocol was created to prevent recurrence.

---

## F-001: Partial Update Drift

**Category:** Cross-File Consistency
**Severity:** HIGH — caused downstream agents to dispatch fix WOs for non-bugs

**What happened:** Domain A re-verification reclassified 4 bugs from WRONG to AMBIGUOUS. The agent updated the checklist and WRONG_VERDICTS_MASTER but missed DOMAIN_C_VERIFICATION.md. The verification file still said "3 WRONG / 1 AMBIGUOUS" while the checklist said "1 WRONG / 3 AMBIGUOUS."

**Root cause:** No protocol required updating all files containing a fact in the same commit. The agent updated the files it had in context and moved on.

**Fix created:** Cross-File Consistency Gate pattern. All-or-nothing updates. If a fact changes, every file referencing it must be updated in the same commit.

---

## F-002: Design Decision Blindness

**Category:** Verification Pitfall
**Severity:** HIGH — 4 bugs reclassified in one domain alone, estimated 8-10 across all domains

**What happened:** The initial verification pass compared code against raw SRD text without checking the research corpus. Cover values that were intentionally different (documented in RQ-BOX-001 Finding 3 as a design decision) were flagged as WRONG.

**Root cause:** The verification dispatch didn't include a required reading list for research documents. The verifier had no reason to suspect the code diverged intentionally.

**Fix created:** Research cross-reference requirement added to all verification and fix WO dispatches. Agents must search research documents for the relevant mechanic before writing WRONG verdicts.

---

## F-003: Silent Agent Completion

**Category:** Agent Reliability
**Severity:** HIGH — 43% of parallel agents (3/7) reported completion with zero code changes

**What happened:** Seven background agents were dispatched to execute fix WOs in parallel. Three agents reported task completion but wrote zero changes to disk. The coordinator discovered this during the commit review phase when `git diff` showed no changes for the affected files.

**Root cause:** Unknown — possibly agents hit edit tool failures and reported success based on having "processed" the task rather than having written changes. The agents' internal state said "done" but the external artifact (modified files) didn't exist.

**Fix created:** Post-completion verification gate: after any agent reports completion, `git diff` the target files before accepting the result. An agent saying "done" is not the artifact — the diff is.

---

## F-004: Stale Document Cascade

**Category:** Machine Truth vs. Prose Truth
**Severity:** MEDIUM — caused incorrect confidence assessments

**What happened:** PROJECT_KNOWLEDGE_SYNTHESIS.md (dated 2026-02-08) claimed 0.98 confidence for the CP-09-17 foundation. The bone-layer verification (completed 2026-02-14) found 30 formula-level bugs in that foundation. An agent reading the synthesis document would have false confidence in code that had a ~5.5% error rate.

**Root cause:** No process required updating analysis documents after new data invalidated their conclusions. The synthesis was written once and never refreshed.

**Fix created:** Session Bootstrap pattern — agents run machine-verified commands before trusting prose documents. Documents that make quantitative claims should be dated and carry a staleness warning.

---

## F-005: WO Target Mismatch

**Category:** Dispatch Accuracy
**Severity:** MEDIUM — one WO (WO-FIX-11) targeted code that didn't exist as described

**What happened:** WO-FIX-11 described an "action cost table at play_loop.py lines 71-86" with trip/disarm/grapple classified as "standard." The actual code routes combat maneuvers via isinstance checks on Intent objects, not a string-to-cost lookup table. The WO was correct about the SRD rule but wrong about the code structure.

**Root cause:** The WO was written from verification findings (which identified the wrong classification) but the fix description assumed a code structure that didn't match reality. The verifier analyzed behavior, not implementation.

**Fix created:** Fix WOs should include "read the code at this location and verify the structure matches this description" as a pre-condition. If the structure doesn't match, report back before attempting the fix.

---

## F-006: Gold Master Surprise

**Category:** Test Infrastructure
**Severity:** LOW — caused transient confusion but no lasting damage

**What happened:** After fixing attack damage calculations (WO-FIX-01/02), four gold master test fixture files changed. The agents regenerated them, which was correct — the old gold masters encoded wrong damage values. But the diff was large (584 lines in one file) and initially alarming.

**Root cause:** Gold master tests are snapshot-based. Any change to the code they exercise changes their output. This is expected but not documented as a consequence of damage formula fixes.

**Fix created:** Fix WOs that touch core resolvers should note "gold master regeneration expected" as a predicted side effect. This prevents the next reviewer from treating the diff as suspicious.

---

## F-007: Context Window Exhaustion Mid-Task

**Category:** Resource Management
**Severity:** MEDIUM — causes incomplete work and forced handoffs

**What happened:** Multiple agents working on complex WOs (particularly WO-FIX-01/02, the attack resolver rewrite) consumed large amounts of context reading files, making edits, running tests, and debugging failures. The attack resolver agent used 170K+ tokens before completing.

**Root cause:** Complex tasks in large files consume context rapidly. The attack resolver files are 1,000+ lines each. Reading, editing, re-reading, and test-debugging each consumes context that doesn't recover.

**Fix created:** WO sizing guideline — if a WO requires reading more than 500 lines of code and making changes across multiple functions, consider splitting it into sub-WOs. The coordinator should monitor agent token consumption and be prepared to split tasks that exceed 60% of context budget during the reading phase.

---

## F-008: Schema Cascade Underestimation

**Category:** Impact Analysis
**Severity:** MEDIUM — WO took 3x longer than estimated due to unlisted file dependencies

**What happened:** WO-FIX-03 (adding ac_modifier_melee/ranged to conditions schema) was scoped to touch 3 files: conditions.py, attack_resolver.py, full_attack_resolver.py. In reality, the fix also required changes to:
- `conditions.py` serialization (to_dict/from_dict)
- `aidm/core/conditions.py` aggregation (get_condition_modifiers)
- 4 test files with assertions testing the old (wrong) behavior

The WO listed 3 files. The fix touched 6.

**Root cause:** Schema changes propagate through serialization, aggregation, and tests. The WO author traced the direct consumers but not the infrastructure layers.

**Fix created:** Schema-change WOs should trace the full propagation path: definition → serialization → aggregation → consumers → tests. A checklist: "Did you update to_dict? from_dict? Any aggregation function? Any test asserting the old value?"

---

## F-009: Constructor Replacement via Blanket Edit

**Category:** Impact Analysis (Schema Cascade variant)
**Severity:** MEDIUM — caught by test suite but required mid-session course correction

**What happened:** WO-RNG-PROTOCOL-001 required replacing the concrete class `RNGManager` with the new `RNGProvider` Protocol in type annotations across 19 files. The builder used `replace_all` to change `RNGManager` to `RNGProvider` across each file. In two files (`replay_runner.py` and `session_log.py`), the same class name appeared both as a type annotation AND as a constructor call: `rng = RNGManager(master_seed)`. The blanket replacement changed both to `RNGProvider(master_seed)`, which fails because Protocols cannot be instantiated.

**Root cause:** `replace_all` operates on string patterns without semantic awareness. It doesn't distinguish between "this name appears as a type annotation" and "this name appears as a constructor call." The WO listed 8 specific files but said "all other core resolvers" — the builder used a uniform approach without checking whether each file had constructor sites.

**Fix created:** Before using `replace_all` on a class name, grep for `ClassName(` (with parenthesis) to identify files that use the class as both a type and a constructor. Handle those files separately with targeted edits. The builder's debrief documented this as a fragility observation for future type-level refactors.

---

## F-010: Dead Validation Rule (Silent Pass)

**Category:** False Confidence
**Severity:** HIGH — validation pass reports all-clear when the validated field is structurally empty

**What happened:** Two compile-time validation rules (CT-006: contraindication enforcement) and one runtime rule (RV-007: contraindication consistency check) were designed to catch narration errors — e.g., a fire spell narrated with ice visual effects. However, the `contraindications` field on `AbilityPresentationEntry` is always an empty tuple `()` because the SemanticsStage never generates contraindication data.

**Root cause:** The validation rules were written before the data they validate was populated. Both rules iterate over `contraindications` entries and check for violations. When the tuple is empty, the loop executes zero times, and the rule reports PASS — not because the data is correct, but because there's nothing to check.

**Detection:** Discovered during a roadmap audit that cross-referenced research findings (RQ-002: contraindications always `()`) against the WO scope (WO-COMPILE-VALIDATE-001 includes CT-006). The auditor flagged that shipping validation rules for an unpopulated field creates false confidence — the PM reviewing validation results could mistake "0 violations" for "verified correct."

**Fix created:** Validation rules that check a field which may be structurally empty should either: (a) report SKIP (not PASS) when the field is empty, with a warning that the check is dormant; or (b) be scoped into the same WO that populates the field, so the rule and its data land together.

---

## F-011: Parallel Implementation Path Drift

**Category:** Cross-Path Consistency
**Severity:** HIGH — 21 independent calculations drifted across two code paths over 30+ work orders; discovered only by a systematic audit

**What happened:** A result calculation had a "single-item" resolver and a "batch" resolver. The batch resolver was added later and reproduced the calculation logic independently rather than delegating. Over 30+ work orders, every WO that improved the calculation targeted the single-item resolver. No dispatch ever mentioned the batch resolver. The batch resolver drifted silently. A sweep audit eventually found that 21 independent calculation components had diverged between the two paths. No individual WO caused the drift — the drift accumulated because no dispatch enumerated the second path.

**Root cause:** WO dispatches are scoped to fix a specific known gap. They treat the target function as the only implementation. No one was responsible for asking "where else does this same logic exist?" The PM didn't know about the parallel paths; the builders weren't asked to look.

**Fix created:** PARALLEL_IMPLEMENTATION_PARITY pattern. Every WO modifying a resolver function must identify all parallel code paths before work begins. Builder verifies parity across all paths before filing the debrief. Missing parity check = debrief reject. When PM doesn't know all parallel paths, the dispatch instructs the builder to identify them as their first task.

---

## F-012: Specification Authority Gap

**Category:** Domain Correctness
**Severity:** HIGH — specification deviation shipped as engine behavior; discovered only by a debrief reviewer reading the original specification directly

**What happened:** A WO was dispatched to implement a calculation rule. The rule had a widely-used community variant that differed from the written specification. The WO dispatch had no authority tag. The builder used the community variant — plausible, locally reasonable, tests passed. The deviation was discovered at debrief by a reviewer who read the original specification directly. The implementation was 1.5× where the specification said 2×. Correcting it required a builder WO and downstream effects.

**Root cause:** The WO spec had no obligation to declare what authority the implementation should follow. The builder had no signal that this was a contested point. The PM had no obligation to check. The ambiguity flowed through the entire process undetected because it was never made visible.

**Fix created:** AUTHORITY_TAGGING pattern. Every WO touching domain logic must declare its authority source: SPEC (with citation) or POLICY (with operator sign-off). No third type. Agent judgment, community convention, and "obviously this is how it works" are not valid authority types. An ambiguity catalog maintained by the PM tracks rules with known community variants.

---

---

## F-013: Set-but-Not-Consumed Data

**Category:** False Confidence / Write-Only Implementation
**Severity:** HIGH — features appear implemented; no runtime effect exists

**What happened:** Multiple mechanics were correctly wired into the character creation and data pipeline. The data fields were populated, the tests passed, and the WOs were accepted. The mechanics did nothing at runtime. No resolver ever read the fields. The acceptance criteria proved data existence, not runtime effect. The gap was discovered only during a cross-cutting consume-site audit: 17 fields set at chargen were never read by any resolver.

**Root cause:** Acceptance criteria tested whether the data was written. No criterion tested whether the data changed a runtime outcome. "Field is populated" and "mechanic is active" are not the same thing. A write path with no read path is not an implementation — it is a stub dressed up as delivery.

**Fix created:** Consume-site verification. Every WO that writes a field must identify: (1) where the field is read at runtime, (2) what observable behavior changes because of that read, and (3) a gate test that proves the runtime effect fires. A WO that cannot answer all three has an incomplete scope. If the consume site doesn't exist yet, the WO either builds it or explicitly flags the field as `CONSUME_DEFERRED` with a tracking finding. Acceptance gate: no ACCEPTED if write-only (unless CONSUME_DEFERRED + finding logged). See CONSUME_SITE_VERIFICATION pattern.

---

## F-014: Research-to-Queue Orphan

**Category:** Traceability / Process Failure
**Severity:** HIGH — approved research never affects the build queue; equivalent to not doing the research

**What happened:** Multiple research sprints identified OSS sources, tools, and architectural approaches that were evaluated, documented, and accepted. The documentation was filed. No WO was ever dispatched to act on the findings. Months of sessions later, the same data was being hand-typed instead of ingested from the identified sources. When challenged, the PM could not confirm which findings had been acted on and which had not — the research was preserved but not routed.

**Root cause:** The process had a gate for "research is documented" but no gate for "research findings are routed to the queue." A finding that is written down but not assigned a disposition (WO, explicit defer with rationale, or closed) is a dead artifact. It consumes context when read and produces no output. The gap between "we have a findings memo" and "the findings became WOs" was invisible to the PM.

**Fix created:** Discovery-queue traceability. A dedicated register cross-references all research/audit/probe artifacts against the WO queue. Every finding must have a disposition: WO dispatched, explicitly deferred with rationale, or closed. A finding with no disposition is a governance failure, not an open item. The register is reviewed on a fixed cadence (every N batches). See DISCOVERY_QUEUE_TRACEABILITY pattern.

---

## F-015: Planning Artifact Drift

**Category:** Artifact Freshness / False Foundation
**Severity:** HIGH — PM and builders make decisions against a roadmap that no longer reflects reality

**What happened:** A coverage map tracking "what is implemented vs. what is not" fell significantly behind the actual delivery state. Mechanics that had been implemented across 30+ WOs still showed as NOT STARTED in the coverage map. New WO dispatches were written against the stale map — some targeted mechanics that were already implemented, some missed dependencies that the map didn't reflect. The local debriefs were accurate; the planning artifact was fiction.

**Root cause:** The coverage map was updated during initial implementation but had no mandatory update trigger on each delivery. Each WO updated its own debrief but there was no debrief requirement to update the planning artifact. Over time, the map drifted from reality. Builders consulted the map and made locally reasonable decisions that were globally wrong because the map was wrong.

**Fix created:** Coverage map update required in every debrief. If a WO implements a mechanic, the coverage map row for that mechanic must be updated in the same debrief (NOT STARTED → IMPLEMENTED). Missing coverage map update = debrief incomplete. The builder is responsible for the update; the PM verifies at acceptance. A stale planning artifact is treated the same as a missing artifact: it cannot be trusted and must not be used for dispatch decisions.

---

## Summary

| ID | Category | Fix Pattern |
|----|----------|-------------|
| F-001 | Cross-File Consistency | All-or-nothing commits |
| F-002 | Verification Pitfall | Research cross-reference requirement |
| F-003 | Agent Reliability | Post-completion git diff gate |
| F-004 | Machine Truth vs. Prose | Session bootstrap, staleness warnings |
| F-005 | Dispatch Accuracy | Pre-condition verification step |
| F-006 | Test Infrastructure | Gold master regeneration prediction |
| F-007 | Resource Management | WO sizing guidelines |
| F-008 | Impact Analysis | Schema cascade checklist |
| F-009 | Impact Analysis | Pre-edit grep for constructor sites |
| F-010 | False Confidence | SKIP vs PASS for empty-field validation |
| F-011 | Cross-Path Consistency | Parallel implementation parity check |
| F-012 | Domain Correctness | Authority tagging (SPEC/POLICY) |
| F-013 | False Confidence | Consume-site verification (write → read → effect → test) |
| F-014 | Traceability | Discovery-queue traceability register |
| F-015 | Artifact Freshness | Coverage map update required in every debrief |



================================================
FILE: case-study/LESSONS_LEARNED.md
================================================
# Lessons Learned

What worked, what didn't, and what we'd do differently. Derived from 4+ months of multi-agent coordination on a 8,500+ test codebase across 25+ delivery batches and 100+ work orders.

---

## What Worked

### 1. Self-contained dispatches are the single highest-impact practice

Every fix WO included: file path, line number, SRD citation, exact fix description, test requirements, and commit message format. An agent with zero prior context could pick up any WO and execute it. This is what made 7-way parallelism possible.

**The test:** Could a brand-new agent execute this dispatch using only the dispatch file and the files it references? If yes, the dispatch is self-contained. If no, it will fail.

### 2. Verification before fixing prevents wasted work

The 338-formula verification pass found 30 bugs. The research cross-reference pass reclassified ~8-10 of those as design decisions. Without the cross-reference, agents would have "fixed" intentional behavior, creating new bugs.

**The lesson:** Verify what's actually wrong before dispatching fixes. A bug report that hasn't been cross-referenced against design decisions is unreliable.

### 3. Machine truth grounds agents in reality

Running `pytest` at session start and `git diff` before committing caught problems that no amount of document reading would reveal. The session bootstrap pattern saved at least 3 wasted work sessions by catching stale assumptions early.

### 4. The human coordinator doesn't need to understand the code

The operator (a non-programmer) coordinated 45+ agent sessions by understanding the coordination problem, not the codebase. Writing dispatches, reviewing diffs, resolving ambiguities, and routing findings across agents — none of this requires knowing Python. It requires knowing project management.

### 5. Artifact primacy works as advertised

Every fact that survived a context boundary was in a file. Every fact that was lost wasn't. There are zero exceptions to this rule in the project's history. Conversational knowledge that isn't pinned to an artifact is assumed lost — and that assumption has been correct every time.

### 6. Debriefs as a learning loop

The operator builds system understanding by reading debriefs, not code. The 4-pass debrief format (Plain English → Full Dump → PM Summary → Retrospective) is the mechanism. The Plain English pass translates what the agent did into terms the operator can reason about. Over 50+ debriefs, the operator developed a mental model of the system's architecture, its weak points, and its trajectory — without ever reading a line of Python.

**The lesson:** Debriefs aren't status reports for tracking task completion. They're the operator's primary learning channel. Optimizing debrief quality directly improves the operator's decision-making on future dispatches.

---

## Methodology Lessons — Second Phase (ML-001 through ML-006)

These lessons emerged from 25+ delivery batches (Batches M through V and beyond) on a codebase that had grown to 8,500+ tests. They represent a second tier of learning — operational failures that only become visible at scale.

### ML-001: "Filed" Is Not "Accepted" — Gate Tests Are the Arbiter

**What happened:** Multiple work orders were reported as complete in builder debriefs. A subsequent audit found the code absent from the codebase — fields missing, handlers not wired, functions not in the expected locations. The debrief was accurate as a description of intended work. The code wasn't there.

**Root cause:** Builders write accurate descriptions of work they believe they completed. Without a gate run at verdict time, a debrief is self-reported. "Filed" means the builder believes it's done. "Accepted" means gate tests confirmed it.

**Rule:** No WO status upgrades to ACCEPTED without a gate run. If a WO has no gate tests, it cannot be accepted — it must be held until a subsequent gate run validates it.

### ML-002: Post-Debrief Loose Threads Must Be Actively Solicited

**What happened:** Coupling risks and structural observations surfaced after a formal debrief — only because a builder was still looking at the seams. The formal debrief format is oriented toward delivery. Drift risks and coupling issues require a different lens, one that activates after the delivery pressure is off.

**Root cause:** Builders orient the debrief toward what was done. Structural risks require the question "what did you notice?" rather than "what did you do?"

**Rule:** After every accepted debrief, ask: "Anything else you noticed outside the debrief?" File any findings before closing. (See POST_DEBRIEF_RETROSPECTIVE pattern.)

### ML-003: Coverage Audit Maps Are Not Ground Truth — Verify the Gap Before Writing Code

**What happened:** Work orders were generated from coverage audits that flagged features as missing. Builders wrote implementation code. Gate tests confirmed the features were already fully implemented — the audits had misread the existing code.

**Root cause:** Coverage audits are generated from code inspection at a point in time. They can misread existing implementations, especially when function names don't obviously signal their scope. A WO generated from an audit inherits the audit's confidence level, not the codebase's actual state.

**Rule:** Any WO targeting "missing" functionality must include an Assumptions to Validate step that explicitly confirms the gap exists before writing code. If the builder finds the feature is already implemented: gate tests validate existing behavior, zero production changes. Not a failure — correct methodology.

### ML-004: Regression Spirals Burn Context Without Producing Output

**What happened:** A builder completed all implementation and its own targeted gate tests. The builder then ran the full regression suite, hit failures unrelated to its WO, and entered a retry loop — 28+ tool calls, never filed a debrief, burned context without producing output. The operator closed the session manually after confirming the code was complete.

**Root cause:** The prompt implied the builder must achieve zero failures before filing. The full suite had pre-existing failures. An agent that doesn't know this will retry indefinitely. No retry cap was specified; no stop rule was given.

**Rule:** Every batch dispatch includes (1) a retry cap ("fix once, re-run once — if still failing, record and stop"), (2) the known pre-existing failure count ("N pre-existing failures — do not treat these as regressions"), and (3) a separate regression agent for the full suite after all WOs in a batch land.

### ML-005: PM Commits Can Sweep Staged Engine Code

**What happened:** A builder had staged production code changes but not yet committed. The PM ran `git add <pm files> && git commit` to land PM-side work. Git committed ALL staged content — including the builder's staged engine files. The engine code appeared in a PM commit, corrupting the audit trail.

**Root cause:** `git commit` (without `-a`) commits all staged content, not only files explicitly added in the most recent `git add`. A parallel builder staging without committing creates a shared staging area trap.

**Rule:** PM must run `git status` before every commit. If any production files appear in the staging area, do NOT proceed. Signal the builder to commit their staged changes first, then PM commits separately.

### ML-006: Missing Authority Tagging Lets Spec Errors Ship as Engine Behavior

**What happened:** A WO was dispatched to implement a calculation rule. The rule had a widely-used community variant that differed from the written specification. The WO dispatch had no authority tag. The builder used the community variant — plausible, tests passed. The deviation was discovered at debrief by a reviewer who read the original specification directly. Correcting it required a builder WO and downstream effects.

**Root cause:** The WO spec had no obligation to declare what authority the implementation should follow. The builder had no signal that this was a contested point. The ambiguity flowed through undetected because it was never made visible.

**Rule:** Every WO touching domain logic with any community dispute (multipliers, stacking rules, edge cases) must include an authority tag in the spec: SPEC (cite source + location) or POLICY (cite rationale + operator sign-off). No third type. (See AUTHORITY_TAGGING pattern.)

---

## What Didn't Work

### 1. Trusting agent completion reports

43% of parallel agents (3/7) reported "task complete" with zero code changes on disk. The agents' internal assessment of completion didn't match the external reality. Without the commit review step (checking `git diff` for actual changes), three WOs would have been marked done with nothing to show for it.

**What we'd do differently:** Require agents to include the `git diff --stat` output in their completion report. If the diff is empty, the agent must explain why.

### 2. Prose-enforced rules don't stick

The PM inbox had a 10-item cap documented in its README. The inbox reached 23 items. The rule existed at Tier 3 (prose) and was violated 2.3x over. Rules that aren't enforced by tests or process conventions are suggestions, not rules.

**What we'd do differently:** Start with Tier 1 enforcement for any quantitative rule (file count caps, naming conventions). Promote rules up the tier hierarchy when they're violated, not when someone notices they should have been enforced all along.

### 3. Schema change impact estimation

WO-FIX-03 was scoped to touch 3 files but actually required 6. The WO author traced direct consumers (attack resolvers) but missed the infrastructure layer (serialization, aggregation, tests). This pattern repeated — schema changes always touch more files than expected.

**What we'd do differently:** Schema-change WOs include a mandatory cascade checklist: definition → serialization (to_dict/from_dict) → aggregation → consumers → tests. The checklist is in the WO, not in the agent's head.

### 4. Parallel dispatch without post-completion verification

Launching 7 agents in parallel is efficient. Assuming all 7 completed correctly is dangerous. The parallel dispatch saved time but the verification gap (no `git diff` check before accepting results) cost time when 3 agents had to be re-executed.

**What we'd do differently:** Parallel dispatch + sequential verification. Launch agents in parallel, but collect results sequentially with `git diff` checks between each.

---

## What We'd Do Differently From Day 1

### 1. Create the Sources of Truth index before the second session

The first session can get away without it. By the second session, two agents have written documents that may conflict. The Sources of Truth index costs 10 minutes to create and prevents hours of contradiction resolution.

### 2. Enforce onboarding checklist reading order from the start

Early sessions had agents reading files in random order, consuming context on low-priority documents before reaching the critical orientation files. Defining the reading order on Day 1 would have saved ~30% of context waste across all sessions.

### 3. Build the PM briefing file immediately

The PM inbox grew to 23 files because there was no single entry point. The PM had to read everything to figure out what needed attention. A rolling briefing file (PM_BRIEFING_CURRENT.md) from Day 1 would have prevented the inbox from becoming a cognitive dump.

### 4. Treat the governance framework as a product, not a side project

The governance documents emerged reactively — each one was created after a failure. Treating them as a product from Day 1 (with versioning, testing, and deliberate design) would have reduced the number of failures needed to discover each pattern. Some failures are necessary for learning; others are preventable with upfront investment.

### 5. Research before verification

The verification pass should have consumed the research corpus first. Instead, verification ran against raw SRD text, and research cross-referencing happened after the fact. Running research first would have prevented the Design Decision Blindness failure and reduced the WRONG count by ~30% on the first pass.

### 6. Plain English debrief pass from Day 1

Early debriefs were technical-only — full of rule IDs, pipeline positions, and dataclass names. The operator could track task completion ("WO done, tests pass") but couldn't build understanding of what the system actually did or why specific changes mattered. Adding the Plain English pass (3 questions: what problem, what it does, why it matters) would have accelerated the operator's learning curve significantly. The operator lost several cycles of learning velocity before realizing the debrief format needed a translation layer.



================================================
FILE: case-study/METRICS.md
================================================
# Metrics

Quantitative results from the D&D 3.5e referee engine project — the proving ground for this framework.

**Last Updated:** 2026-02-27

---

## Verification Results

| Domain | Formulas | Correct | Wrong | Ambiguous | Uncited |
|--------|----------|---------|-------|-----------|---------|
| A: Attack Resolution | 57 | 43 | 4→2 | 2→4 | 9 |
| B: Combat Maneuvers | 45 | 34 | 5 | 5 | 1 |
| C: Spells & Saves | 21 | 15 | 3→1 | 1→3 | 2 |
| D: Conditions | 38 | 28 | 4 | 4 | 2 |
| E: Movement & Terrain | 42 | 36 | 3 | 2 | 1 |
| F: Character Progression | 77 | 65 | 5→3 | 3→5 | 4 |
| G: Play Loop | 22 | 16 | 2 | 2 | 2 |
| H: Targeting | 18 | 16 | 1 | 1 | 0 |
| I: Geometry & Feats | 49 | 38 | 3 | 4 | 4 |
| **Total** | **338** | **255** | **30→~22** | **28** | **25** |

*Arrows indicate changes from research cross-referencing (Domain A re-verified, others estimated).*

**First-pass accuracy:** 75.4% (CORRECT / total)
**With AMBIGUOUS as non-bugs:** 83.7% ((CORRECT + AMBIGUOUS) / total)
**Estimated genuine bugs after cross-ref:** ~22 of 338 = 93.5% accuracy

---

## Bug Classification

30 bugs categorized into 8 error patterns:

| Pattern | Count | Example |
|---------|-------|---------|
| Missing modifier/multiplier | 6 | STR grip multiplier not applied |
| Wrong threshold/floor | 4 | min damage 0 instead of 1 |
| Condition not differentiated | 4 | Prone AC flat instead of melee/ranged |
| Missing field/parameter | 3 | Concentration DC missing spell level |
| Inverted condition | 2 | Soft cover applied to melee instead of ranged |
| Incorrect die/formula | 3 | Water fall d6 instead of d3, sunder hardcoded 1d8 |
| Incomplete enumeration | 2 | SIZE_ORDER missing 3 categories, Colossal footprint |
| Design decision misidentified | 6 | Cover values flagged as bugs, were intentional |

---

## Agent Coordination Metrics

| Metric | Value |
|--------|-------|
| Total agent sessions | 100+ |
| Parallel agent groups (max) | 7 simultaneous |
| Silent agent failure rate | 3/7 (43%) in one parallel dispatch |
| WOs requiring reclassification | 1 of 13 (WO-FIX-11, code structure mismatch) |
| Schema cascade underestimation | 1 of 13 (WO-FIX-03, 3 files scoped → 6 touched) |
| Cross-file consistency failures | 2 (Domain C verification, Domain A checklist) |
| Research cross-ref reclassifications | 4 confirmed (Domain A), ~8-10 estimated (all domains) |
| Total WOs dispatched (all types) | 100+ (fix, feature, research, governance, audit, framework) |
| Builder debriefs archived | 50+ |
| Research documents produced | 30 |
| Delivery batches completed | 25+ |
| Gate test suite size | 8,521+ tests |

---

## Fix Execution Metrics

| Metric | Value |
|--------|-------|
| Fix WOs dispatched | 13 (12 active, 1 retired) — Phase 1 only |
| Fix WOs completed | 11 of 12 |
| Fix WOs needing reclassification | 1 (WO-FIX-11) |
| Fix WOs partially completed | 1 (WO-FIX-12, BUG-F2/F3 unverified) |
| Tests passing after all Phase 1 fixes | 5,277 |
| Tests passing after all Phase 2 batches | 8,521+ |
| Tests updated (old wrong behavior) | 6 |
| Gold master files regenerated | 4 |
| Total commits for fix session | 9 |

---

## H1 WO Batch Metrics

| Metric | Value |
|--------|-------|
| H1 WOs completed | 7 |
| Tests passing after H1 batch | 5,804+ |
| Builder commit failures recovered (one batch) | 4 (3/7 agents silently failed to commit) |
| Integration Constraint Policy | Codified — no new infrastructure WOs until canary runs |
| Integration break points found by canary | 4 (all invisible to unit tests) |

---

## Phase 2 Batch Delivery Metrics

| Metric | Value |
|--------|-------|
| Batches completed (Phase 2) | 20+ (Batches I through R+) |
| Average gate tests per batch | 8 (range: 6-11) |
| Average accepted WOs per batch | 4 |
| Regression failures introduced | 0 (zero regressions across all accepted batches) |
| Ghost WOs dispatched (feature already implemented) | ~3 (identified via pre-dispatch verification) |
| Parallel path drift incidents caught | 1 (F-011, 21-modifier divergence, discovered by sweep audit) |
| Regression spiral incidents | 1 (F-ML-004, agent burned context on pre-existing failures) |
| PM commits sweeping staged builder code | 1 (F-ML-005, caught post-hoc; audit trail corrected) |
| Spec authority gap incidents | 1 (F-012, community variant shipped over specification value) |

---

## Enforcement Tier Effectiveness

| Tier | Stickiness | Example |
|------|-----------|---------|
| Tier 1: Test-enforced | ~100% | Boundary law tests, WorldState immutability |
| Tier 2: Process-enforced | 70-80% | Dispatch templates, handoff checklists |
| Tier 3: Prose-enforced | 40-60% | PM inbox 10-item cap (violated 2.3x) |

---

## Context Window Observations

| Observation | Data Point |
|-------------|-----------|
| Largest agent token consumption | ~170K tokens (WO-FIX-01/02 attack resolvers) |
| Typical WO agent consumption | 30K-80K tokens |
| PM summary effective length | 7 items / ~500 tokens |
| Full debrief length | ~2,000-4,000 tokens |
| Compression ratio (full → summary) | 4:1 to 8:1 |



================================================
FILE: case-study/PROJECT_OVERVIEW.md
================================================
# Project Overview

**Last Updated:** 2026-02-27

## What Was Built

A deterministic D&D 3.5e referee engine — a software system that adjudicates tabletop RPG combat with mechanical fidelity to the System Reference Document (SRD). The system resolves attacks, damage, conditions, spells, combat maneuvers, movement, terrain, and character progression using the exact formulas published in the Player's Handbook and Dungeon Master's Guide.

## Who Built It

A non-technical operator (former chef, English educator) coordinating multiple AI agents:
- **Claude Opus** — primary builder and verifier
- **Claude Sonnet** — secondary builder for parallel work
- **GPT-4** — research and cross-referencing

The operator wrote zero lines of code directly. All code was produced by AI agents working from dispatched work orders. The operator's role was coordination: writing dispatches, reviewing outputs, resolving ambiguities, and routing agent findings to other agents.

## Scale

| Metric | Value |
|--------|-------|
| Automated tests | 8,521+ (zero regressions across all accepted batches) |
| Verified formulas | 338 across 9 domains |
| Source files | 20+ core resolvers |
| Governance documents | 25+ (each born from a specific failure) |
| Bugs found in verification | 30 (later reduced to ~22 after research cross-referencing) |
| AMBIGUOUS verdicts requiring PM decision | 28 |
| Total work orders dispatched | 100+ (fix, feature, research, governance, audit, framework) |
| Builder debriefs archived | 50+ |
| Research documents produced | 30 |
| Delivery batches completed | 25+ |
| Parallel agent groups (single session) | 7 simultaneous |
| Total agent sessions | 100+ |

## Complexity

D&D 3.5e was chosen specifically because it stress-tests coordination:
- **The rules spec is thousands of pages** across multiple books that sometimes contradict each other
- **Two size modifier tables** (standard attack vs. special/grapple) that apply in different contexts
- **Condition interactions are combinatorial** — prone + helpless + fatigued creates a unique modifier stack
- **The designer published post-hoc rulings** that change RAW interpretations
- **The community has argued about Rules As Written** for 20+ years

This complexity meant the coordination system had to be rigorous. Approximation wasn't acceptable — the engine either implements the formula correctly or it doesn't, and verification can prove which.

## Architecture

The engine uses a frozen packet model (CP-XX) with three layers:
- **Referee Layer** — deterministic rule adjudication (attack resolution, damage, saves)
- **Boundary Layer** — world state management (immutable at non-engine boundaries)
- **Storyteller Layer** — narrative generation (consumes referee output, never modifies state)

RNG streams are isolated (combat/initiative/policy/saves) to enable deterministic replay.

## Timeline Context

The framework was developed over 4+ months of multi-agent coordination — initially intensive (daily sessions) and then sustained across 25+ delivery batches. The operator worked in a constrained network environment with variable API latency, which directly influenced the emphasis on artifact primacy (sessions can drop mid-conversation) and dispatch self-containment (you may not get a chance to clarify).

## Network Environment

This project was built in a constrained network environment with variable latency and intermittent connectivity to AI providers and GitHub. If you're working in a similar environment:

- **API latency is variable.** LLM agent sessions may time out or drop mid-conversation. This makes the handoff protocol and artifact primacy pattern even more critical — if your session drops unexpectedly, pinned artifacts are all that survives.
- **Multiple AI providers may have different accessibility.** Some providers may be reachable, others not, depending on your network configuration. This affects which agents you can use in your fleet and is a real constraint on multi-provider coordination.
- **Context window efficiency matters more.** Higher latency means longer round-trips. Wasting a context window on orientation (because the reading order was wrong) costs more wall-clock time when every API call takes longer.
- **Git push failures.** Remote operations may fail intermittently. If you see SSL errors on git push, try `git config http.sslBackend openssl` in the affected repo.

None of these issues are theoretical. They were encountered during the development of this framework and directly influenced the emphasis on artifact primacy and dispatch self-containment.



================================================
FILE: patterns/ARTIFACT_PRIMACY.md
================================================
# Pattern: Artifact Primacy

## Problem

LLM agents have perfect recall within a single context window. This creates a dangerous illusion: during a session, the agent remembers everything you discussed, every decision you made, every nuance you agreed on. It feels like the agent "knows" the project.

Then the context window closes. The next agent knows nothing.

Every decision, rationale, status update, and design choice that existed only in conversation is gone. The next agent will re-derive some of them, miss others, and contradict the rest. Over 3-4 context rotations, the project's actual state and the agents' understanding of it diverge by 30-40%.

## Solution

**If it's not in a file, it doesn't exist.**

Any fact that must survive a context boundary must be written to a versioned file in the repository. Conversational knowledge not pinned to an artifact is assumed lost at the next context rotation.

### What Must Be Pinned

| Knowledge Type | Example | Pin To |
|---------------|---------|--------|
| Design decisions | "We chose approach B because X" | Decision log or design doc |
| Status changes | "Bug-10 reclassified from WRONG to AMBIGUOUS" | Verification file + master list |
| Scope boundaries | "Don't touch the spell system until gate opens" | Tech debt register or state doc |
| Discovered pitfalls | "Never use bare strings for field access" | Development guidelines |
| Mid-session findings | "Found 4 unverified formulas in helper functions" | Session memo to PM inbox |
| Uncommitted work | "Edited file X but didn't commit because Y" | Handoff document |

### What Can Stay Conversational

- Brainstorming that hasn't reached a decision
- Questions you're still thinking about
- Opinions about approach quality (until they become decisions)
- Status updates that are also reflected in files

## Implementation

### The Handoff Checklist

Before a session ends or approaches context limits, verify:

- [ ] State summaries updated (checklists, master lists, logs)
- [ ] Memo written if strategic findings emerged
- [ ] Any mid-session reclassifications reflected in ALL affected files
- [ ] Uncommitted work documented in a handoff file
- [ ] No implicit knowledge required — next agent can work from artifacts alone

### The Consistency Gate

When a status, count, verdict, or classification changes, update **all** files that reference it in the same commit. Partial updates are worse than no update — they create contradictions that the next agent can't resolve without re-reading source files.

**Example failure:** Session A updated the verification checklist and the bug master list, but missed the domain-specific verification file. Session B read the domain file, saw different numbers than the checklist, and couldn't determine which was correct. A third session was needed just to reconcile.

### The Handoff Document

When a session ends with incomplete work, write a handoff file:

```markdown
# Handoff: [Short Description]

**From:** [Agent ID]
**Date:** [YYYY-MM-DD]
**Status:** Ready to execute

## Uncommitted Work
[What was changed but not committed, and why]

## Completed This Session
[What was done and committed]

## Next Steps
[Exactly what the next agent should do, in order]

## Files to Read Before Executing
[List of files the next agent needs for context]
```

## When to Use

- Always. This is not optional for multi-agent projects.
- The question is never "should I pin this?" but "is there anything I forgot to pin?"
- Err on the side of over-documenting. A file that captures an obvious decision costs less than a session spent re-deriving a non-obvious one.

## Real Example

The proving-ground project discovered this pattern the hard way. A verification session reclassified 4 bug verdicts from WRONG to AMBIGUOUS based on research cross-references. The reclassifications were discussed in conversation and partially reflected in files — the checklist was updated, but two domain-specific files weren't. The next session saw conflicting numbers, spent half its context window investigating the inconsistency, and ultimately required a third session to write the fix.

After implementing artifact primacy with the handoff checklist, zero reclassification inconsistencies occurred in subsequent sessions.

## Anti-Patterns

- **"The next agent will figure it out."** No, they won't. They'll figure out *something*, and it probably won't match what you intended.
- **"I'll remember to mention it."** You won't be there. The operator may not remember either, or may not know it's important.
- **"It's obvious from the code."** Code shows *what* was done, not *why*. Decisions, tradeoffs, and rejected alternatives exist only in conversation unless pinned.
- **"We already discussed this."** With a different agent, in a different context window, that no longer exists. Pin it or lose it.



================================================
FILE: patterns/AUTHORITY_TAGGING.md
================================================
# Pattern: Authority Tagging

## Problem

When a builder implements domain logic, they make choices. Some of those choices are obvious from the specification. Others are ambiguous. A few are actively disputed in the community — commonly-understood one way, but technically specified another.

Without explicit authority tagging, builders resolve ambiguities by:
1. Using the most common community interpretation
2. Making a locally reasonable judgment
3. Reproducing what similar systems do

All three produce the same outcome: **behavior that is plausible but unverifiable**. When a reviewer or auditor later asks "why does this work this way?" there's no answer traceable to a source. The behavior is a guess that passed tests.

**The specific failure mode:** A builder implements a rule using a widely-known community variant that differs from the actual written specification. The implementation is "correct" in the sense that it matches what most practitioners expect — but incorrect against the authoritative source. The deviation ships, takes effect, and is only discovered when someone reads the original specification directly. At that point, correcting it is a breaking change with downstream effects.

**The root cause:** The WO spec didn't declare what authority the implementation should follow. The builder had no signal that this was a contested or ambiguous point. The PM had no obligation to check. The ambiguity flowed through the entire process undetected because it was never made visible.

## Solution

### Rule

**Every WO that implements domain logic must declare its authority source before dispatch.**

Two valid authority types:

| Type | Definition | Required documentation |
|------|-----------|----------------------|
| **SPEC** | Rules As Written from the authoritative specification | Citation: [document] [section/page] |
| **POLICY** | Explicit, versioned, operator-approved decision | Rationale + operator sign-off logged |

**No third type.** Agent judgment, community convention, and "obviously this is how it works" are not valid authority types. If neither SPEC nor POLICY covers a case, the correct action is to refuse, log the gap, and escalate — never to guess.

### The Authority Tag in WO Dispatches

Every WO targeting domain logic includes:

```markdown
## Authority Tag

**Rule:** [name of the rule or behavior being implemented]
**Authority type:** SPEC | POLICY
**Source:** [document and location if SPEC; policy ID and rationale if POLICY]
**Disputed:** Yes/No — [if Yes, note the common variant and explain why spec takes precedence]
```

Example:
```markdown
## Authority Tag

**Rule:** Two-handed weapon attack multiplier
**Authority type:** SPEC
**Source:** [Specification document] Section 3.2, "Two-Handed Weapons"
**Disputed:** Yes — common community convention uses 1.5× multiplier; specification explicitly states 2×. Implement per specification.
```

When the PM doesn't know whether a rule is disputed, the check is: *"Is there any reason someone might implement this differently?"* If yes, the authority tag is mandatory.

### The Ambiguity Catalog

Maintain a running list of rules that have documented ambiguities, community variants, or specification gaps. Before dispatching any WO touching domain logic, the PM checks this catalog.

```markdown
| Rule | Ambiguity | Specification says | Common variant |
|------|-----------|-------------------|----------------|
| [Rule name] | [Description of the ambiguity] | [What the spec actually says] | [What people often do instead] |
```

This catalog is a PM-maintained artifact. Builders never need to see it — the WO spec should already have the right authority tag. But the PM needs it to know which rules require extra scrutiny.

### When There Is No Specification

Some rules are genuinely unspecified. The specification doesn't cover the case. This is a **policy gap**, not a specification choice.

Correct handling:
1. The WO includes an `UNSPECIFIED` flag in the authority tag
2. The PM escalates to the operator for a policy decision before dispatch
3. The operator makes an explicit policy choice (even "default to the most common interpretation" is a policy)
4. The policy is documented and versioned
5. The WO ships with `POLICY` authority, citing the operator decision

**Never resolve an unspecified case by letting the builder guess.** The guess will be locally reasonable and permanently wrong in an undiscoverable way.

### Detecting Contested Rules

Some signals that a rule is contested:
- Community forums have threads arguing about it
- Multiple implementations of similar systems handle it differently
- The specification text is ambiguous or has errata
- The rule involves stacking, multipliers, or interaction between two systems (these are disproportionately contested)
- The rule was changed between versions of the specification

When any of these signals are present, treat the rule as contested and require an explicit authority tag.

## Implementation

### Adding Authority Tags Retroactively

For existing implementations without authority tags:

1. Auditor identifies the behavior
2. PM locates the specification citation
3. PM verifies the implementation matches the specification
4. If it matches: add a retroactive tag in a comment or governance doc
5. If it doesn't match: file a corrective WO

This is discovery work, not rework — don't fix what doesn't need fixing. The audit is looking for deviations, not just confirming the existing tags.

### The PM's Pre-Dispatch Checklist Addition

Add to the PM's WO dispatch checklist:

```
[ ] Does this WO touch domain logic?
      If yes:
      [ ] Is the rule's specification unambiguous?
      [ ] Does the rule appear in the ambiguity catalog?
      [ ] Is the authority tag complete in the WO?
      [ ] If contested: does the WO explicitly call out the variant and confirm spec takes precedence?
```

### Trust Hierarchy (For Specification-Rich Domains)

In domains with layered specifications (primary spec, errata, designer intent, community rulings), the PM maintains an explicit trust hierarchy:

1. Primary specification (highest authority)
2. Official errata to the primary specification
3. Designer clarifications (where documented)
4. Conservative interpretation of ambiguous cases
5. Community consensus (lowest authority, only when all above are silent)

The hierarchy is project-specific. The point is that it exists and is written down, so every WO can cite a level, not just a vague "this is how it works."

## When to Use

- Any project implementing rules from an external specification (a protocol, a standard, a rulebook, a regulation)
- Any domain where community practice diverges from written specification
- Any project where different implementations of the same system exist and disagree

## When NOT to Use

- Pure algorithmic work with no domain authority questions (e.g., "sort these items by date")
- Projects where the operator is also the specification authority (they can't contradict themselves)
- UI/UX changes with no correctness criteria

## Real Example

A project was implementing a calculation rule. The rule had a widely-used community variant that differed from the written specification. The WO dispatch had no authority tag — it simply said "implement [rule]."

The builder used the community variant. The implementation shipped. Tests passed.

Six batches later, a debrief reviewer read the original specification and noticed the discrepancy. The implementation was 1.5× where the specification said 2×. Correcting it required a builder WO, a gate test update, and a governance patch to document the correction.

**If the WO had included an authority tag** citing the specification and flagging the common variant, the builder would have seen the flag, implemented per specification, and the error would never have shipped.

**Fix:** Added mandatory authority tagging to all WOs touching rules with known community variants. Maintained an ambiguity catalog. The PM checks the catalog before every dispatch targeting rule implementations.



================================================
FILE: patterns/CONCURRENT_SESSION_PROTOCOL.md
================================================
# Concurrent Session Protocol

## Problem

You have two agent sessions running in parallel. Both need to edit files. If they edit the same file, the second commit overwrites the first. If they edit different files that reference the same facts, you get cross-file inconsistency. If they both run tests, they may interfere with each other's test fixtures.

Multi-agent parallelism is powerful — the D&D 3.5e project dispatched 7 parallel agent groups to fix 30 bugs simultaneously. But parallelism without file ownership produces collisions that are worse than doing things sequentially.

## Solution

**Partition work by file ownership.** Before dispatching parallel sessions, identify which files each session will touch. If two sessions need the same file, they must run sequentially, not in parallel.

### File Ownership Analysis

Before parallel dispatch, build a file-to-session map:

```
Session A: conditions.py, attack_resolver.py
Session B: maneuver_resolver.py
Session C: terrain_resolver.py, mounted_combat.py
Session D: spell_resolver.py, play_loop.py
```

**Conflict check:** Do any files appear in more than one session? If yes, those sessions must be sequenced.

```
CONFLICT: attack_resolver.py appears in Session A and Session E
RESOLUTION: Session E runs AFTER Session A completes
```

### Dependency Declaration

Each work order dispatch must declare:
- **Files I will modify** (write set)
- **Files I will read but not modify** (read set)
- **Files that must be in a specific state before I start** (dependency set)

Write-write conflicts require sequencing. Read-write conflicts are acceptable if the reader goes first or the reader tolerates the write.

### Implementation

**1. Pre-dispatch conflict check**

The coordinator (human or PM agent) reviews all parallel dispatches and identifies file overlaps. This is a manual step — the cost of getting it wrong (merge conflicts, silent overwrites) is much higher than the cost of spending 2 minutes checking.

**2. Session scope declaration**

Each agent's dispatch includes a scope block:

```markdown
## Session Scope
**Write set:** aidm/core/maneuver_resolver.py, aidm/schemas/maneuvers.py
**Read set:** aidm/schemas/attack.py, aidm/core/attack_resolver.py
**Dependencies:** WO-FIX-03 must be committed before this session starts
**Do NOT touch:** Any file not listed above
```

**3. Post-session verification**

After all parallel sessions complete, run `git diff --stat` to verify only the declared files were modified. If an agent touched a file outside its write set, investigate before committing.

## When to Use

- Any time you dispatch 2+ agent sessions simultaneously
- When a work order has explicit dependencies on another WO's output
- When multiple WOs touch the same subsystem (even different files — they may share helper functions)

## When NOT to Use

- Sequential single-agent work (no conflict possible)
- Read-only tasks like verification or research (no writes, no conflicts)

## Real Example

The fix WO dispatch for the D&D 3.5e project identified these file overlaps:

| File | Used by WOs |
|------|------------|
| `attack_resolver.py` | WO-FIX-01, WO-FIX-03 |
| `full_attack_resolver.py` | WO-FIX-01, WO-FIX-02, WO-FIX-03 |
| `conditions.py` | WO-FIX-03, WO-FIX-04 |
| `maneuver_resolver.py` | WO-FIX-07, WO-FIX-08, WO-FIX-09 |
| `play_loop.py` | WO-FIX-06, WO-FIX-11 |

This analysis produced 7 parallel-safe groups instead of 13 independent dispatches. Groups with file overlap ran their WOs sequentially within the group. Groups without overlap ran in parallel.

**Result:** 7 parallel agents completed 12 WOs. No merge conflicts. But 3 agents silently failed to write changes — a different failure mode that the concurrent protocol doesn't address (see: Silent Completion failure pattern).

## Anti-Patterns

- **"Just let them both edit and merge later"** — LLM agents don't produce clean diffs. Merging two agents' independent edits to the same file is manual reconstruction, not automated merging.
- **Declaring file ownership but not enforcing it** — if the dispatch says "do NOT touch other files" but nothing checks, agents will touch other files. The post-session `git diff --stat` is the enforcement.
- **Assuming read-only operations are safe in parallel** — they usually are, but if a reader caches assumptions from a file that a parallel writer is changing, the reader's output may be based on a state that no longer exists by the time it's used.



================================================
FILE: patterns/CONSUME_SITE_VERIFICATION.md
================================================
# Pattern: Consume-Site Verification

## Problem

An agent implements a feature. The data field is populated. The tests pass. The WO is accepted. The feature does nothing at runtime.

This is the write-only trap: a feature can appear fully implemented if the acceptance criteria only checks that the data was written. The runtime effect — the actual change in behavior that the feature was supposed to produce — is never verified.

The failure is invisible because:
- The data field exists and has the right value
- The chargen or configuration pipeline is correct
- The gate tests for the WO all pass
- The debrief is accurate about what was done

What none of these verify: **is this field ever read by a runtime resolver?**

## Solution

Every WO that writes a field, registers data, or configures a value must verify the full consumption chain before filing its debrief.

### The Four-Layer Chain

```
Layer 1 (Write):   Where is the field written?
                   file:function or file:line_range

Layer 2 (Read):    Where is the field read at runtime?
                   file:function or file:line_range

Layer 3 (Effect):  What observable behavior changes because of that read?
                   Describe the runtime difference between field present vs. absent.

Layer 4 (Test):    Which gate test proves the runtime effect fires?
                   test_file:test_function — not a setup test, a behavior test
```

All four layers must be answered in the WO debrief. If any layer is missing, the WO is incomplete.

### When the Consume Site Doesn't Exist

Sometimes a WO correctly identifies that no consume site exists. This is the `CONSUME_DEFERRED` case. The builder:

1. Explicitly states the field is write-only (no runtime consumer yet)
2. Files a tracking finding: `FINDING-[ID]-CONSUME-DEFERRED: field X written at Y, no consumer exists`
3. States the expected consume site (the resolver that should eventually read it)
4. Marks the mechanic as write-only in the coverage map

The PM records the defer and ensures the tracking finding is in the open backlog. A `CONSUME_DEFERRED` field is not forgotten — it is explicitly parked.

**Acceptance gate:** No WO is ACCEPTED if a field is write-only without `CONSUME_DEFERRED` explicitly declared and a finding logged.

## The Corrected Definition of "Implemented"

A mechanic is **not** implemented merely because:
- Code exists
- Tests pass
- Data is populated
- A WO is accepted

A mechanic is implemented only when it satisfies all six criteria:

1. **Source-cited** — RAW or HOUSE authority tagged with a specific reference
2. **Code written** — the logic exists in the codebase
3. **Consumed at runtime** — an observable effect exists; the field is read and changes behavior
4. **Parity-checked** — if parallel implementation paths exist, both paths are consistent
5. **Tested** — a gate test specifically proves the runtime effect (not just setup)
6. **Reflected in planning artifacts** — the coverage map row is updated

"Code + passing tests" satisfies criteria 2 and 5 only. The other four are independent gates.

## Implementation

### In the WO Dispatch

The PM includes a **Consumption Chain** section in every WO that writes a field:

```markdown
## Consumption Chain

| Layer | Location | Description |
|-------|----------|-------------|
| Write | builder.py:142 | `ef[EF.MONK_UNARMED_DICE] = unarmed_dice` |
| Read  | attack_resolver.py:87 | `dice = ef.get(EF.MONK_UNARMED_DICE, "1d3")` |
| Effect | Monk unarmed strike uses correct dice per level instead of base 1d3 |
| Test  | test_monk_unarmed_gate.py::test_monk_level_4_uses_1d6 |
```

If the PM doesn't know the consume site at dispatch time, the dispatch instructs the builder to identify it as their first task.

### In the Builder Debrief

The builder confirms the consumption chain end-to-end:

```markdown
## Consume-Site Confirmation

- Write site: builder.py:142
- Read site: attack_resolver.py:87
- Observable effect: level 4 monk uses 1d6, not 1d3 (confirmed via test)
- Proof test: test_monk_unarmed_gate.py::test_monk_level_4_uses_1d6 — PASS
```

If the consume site was `CONSUME_DEFERRED`, the builder states this explicitly and logs the finding.

### PM Acceptance Check

Before issuing ACCEPTED, the PM verifies:
- Consume-site confirmation section exists in debrief
- Layer 2 (read site) is not empty and not `CONSUME_DEFERRED` without a logged finding
- Layer 4 (proof test) is a behavior test, not a setup test

## Anti-Patterns

**The setup test that passes:**
A test that verifies `ef[EF.SOME_FIELD] == expected_value` is a write verification, not a consume verification. It confirms the field was written correctly. It proves nothing about runtime behavior. A consume-site proof test must verify that the runtime output changes when the field is present vs. absent (or present with different values).

**The "eventually wired" justification:**
"We'll wire the consume site in the next WO." This is acceptable only if formally declared as `CONSUME_DEFERRED` with a logged finding. Undeclared write-only delivery treated as complete is the failure mode this pattern prevents.

**Counting data registration as implementation:**
A spell registry entry, a feat definition in a lookup table, or a creature stat block in a JSON file is not an implemented mechanic. It is a data dependency for an implementation. The consume site — the resolver that reads from the registry and changes combat behavior — is the implementation.

## Connection to Other Patterns

- **PARALLEL_IMPLEMENTATION_PARITY** — the parity check is Layer 4 of consume-site verification applied to multiple paths. Both patterns are required for mechanics with parallel resolver paths.
- **SWEEP_AUDIT_PROTOCOL** — sweeps catch write-only fields that slipped through individual WO acceptance. A consume-site sweep is a high-value audit pass.
- **RESEARCH_TO_BUILD_PIPELINE** — data ingested from research (OSS sources, SRD data) must also pass consume-site verification. Data existing in a file is not a runtime mechanic.



================================================
FILE: patterns/COORDINATION_FAILURE_TAXONOMY.md
================================================
# Pattern: Coordination Failure Taxonomy

## Problem

Multi-agent LLM projects fail in predictable ways. But because each failure happens in a different context window, nobody accumulates enough experience to see the patterns. The same mistakes repeat across sessions, across projects, and across teams — because the failure modes aren't cataloged.

## Solution

Maintain a categorized failure catalog. Every coordination failure gets documented with its root cause, how it was detected, and what prevents recurrence. Over time, this becomes the most valuable artifact in the methodology — it's the accumulated institutional knowledge that no single agent can hold.

## The Taxonomy

Eight categories of coordination failure, discovered empirically:

### Category 1: Partial Update
**What:** One session updates some files that reference a shared fact, but misses others.
**Why:** No consistency gate. The agent updated what it remembered, not what exists.
**Example:** Verification session reclassified a bug in the checklist and master list, but missed the domain-specific file. Next session saw conflicting numbers.
**Prevention:** Cross-file consistency gate — when any status/count/verdict changes, update ALL files that reference it in the same commit.

### Category 2: Cross-Provider Contamination
**What:** Work product from one LLM provider conflicts with in-flight work from another.
**Why:** Different providers have different assumptions, naming conventions, and confidence patterns. Work orders generated by one LLM may not be compatible with another's execution style.
**Example:** GPT-generated work orders conflicted with Claude-executed fix work, producing scope overlaps and contradictory instructions.
**Prevention:** All work orders go through a single dispatch authority (human or designated PM). No agent generates work orders for other agents without review.

### Category 3: Scope Bleed
**What:** A session modifies files outside its declared scope, conflicting with another concurrent session.
**Why:** Agent sees an "easy fix" in a nearby file and makes it, not knowing another session owns that file.
**Example:** Governance session auto-executed code changes on context rollover, potentially conflicting with a parallel fix session.
**Prevention:** Explicit session scope declaration. Agents must NOT write to files outside their declared scope without operator approval.

### Category 4: Context Starvation
**What:** A session lacks documents it needs because the dispatch didn't reference them.
**Why:** Dispatch author assumed the agent would "know" to check certain files, but the agent has zero prior context.
**Example:** Verification agents didn't cross-reference research documents because the dispatches didn't mention them. Result: 8-10 bugs flagged incorrectly, requiring reclassification.
**Prevention:** Dispatch self-containment — every dispatch must reference all documents the agent needs. If a document is relevant, it must be in the dispatch's "Files to Read" section.

### Category 5: Parallel Collision
**What:** Two concurrent sessions modify the same file, creating merge conflicts or silent overwrites.
**Why:** No file-level ownership protocol. Both sessions assumed they had exclusive access.
**Example:** Two fix work orders targeting functions in the same file, dispatched to parallel sessions.
**Prevention:** File ownership rules — if two work orders touch the same file, they must run sequentially, not in parallel. Work order dispatch must check for file-level conflicts.

### Category 6: Stale Reference
**What:** A document references another document that has moved, been renamed, or contains outdated numbers.
**Why:** Documents reference each other by path, but paths change when files are reorganized. Numbers (test counts, formula counts) change when work is completed.
**Example:** Onboarding checklist referenced a planning file at `docs/planning/FILE.md`, but the file had been moved to `docs/planning/archived/FILE.md`.
**Prevention:** Sources of truth index — a single file declaring which file is authoritative for each concept. Machine-generated sources (scripts that count tests, snapshot tools) outrank hand-maintained prose.

### Category 7: Silent Agent Completion
**What:** An agent reports task completion but produces zero artifacts (no code changes, no file modifications, no diff output).
**Why:** The agent internally "processed" the task — reading files, reasoning about changes, possibly hitting edit tool failures — and evaluated its own progress as complete. But internal state doesn't equal external artifacts.
**Example:** 3 of 7 parallel fix agents reported completion with zero code changes on disk. Discovered during commit review when `git diff` showed no modifications for their target files. 43% silent failure rate in one dispatch.
**Prevention:** Post-completion verification gate — after any agent reports completion, run `git diff` on target files before accepting the result. An agent saying "done" is not the artifact. The diff is. Agents should include `git diff --stat` output in their completion reports.

### Category 8: Schema Cascade Underestimation
**What:** A work order scopes changes to direct consumers of a modified schema but misses infrastructure layers (serialization, aggregation, tests), causing the actual change set to be 2-3x larger than estimated.
**Why:** Schema changes propagate through layers that aren't visible from the consumer level. The WO author traces the direct code path but not the infrastructure the schema participates in.
**Example:** WO-FIX-03 was scoped to touch 3 files (conditions.py, attack_resolver.py, full_attack_resolver.py). The actual fix required 6 files: the 3 listed plus serialization methods (to_dict/from_dict), aggregation functions (get_condition_modifiers), and 4 test files asserting the old behavior.
**Prevention:** Schema-change WOs include a mandatory cascade checklist: definition → serialization → aggregation → consumers → tests. Each layer must be explicitly confirmed as "no change needed" or "change required at [file:line]."

## Implementation

### Catalog Format

```markdown
### CF-[NNN]: [Short Name]

**Date:** [When it happened]
**Category:** [Partial Update | Cross-Provider | Scope Bleed | Context Starvation | Parallel Collision | Stale Reference | Silent Completion | Schema Cascade]
**Sessions Involved:** [Which agents/sessions]
**What Happened:** [Factual description — no blame, just events]
**Root Cause:** [Why the coordination protocol didn't prevent it]
**Detection:** [How was it discovered]
**Resolution:** [What was done to fix it]
**Prevention:** [What governance change prevents recurrence]
**Status:** [MITIGATED | OPEN | ACCEPTED]
```

### When to Add Entries

- Any time you discover a conflict between sessions
- Any time an agent produces work that contradicts another agent's work
- Any time a human has to intervene because agents collided
- Any time a document is discovered to be wrong because of a coordination gap

### Reviewing the Catalog

At the start of each project phase or after a batch of work completes, review the catalog:
- Are there categories with many entries? That's a systemic gap.
- Are there OPEN entries? Those are unmitigated risks.
- Are the prevention mechanisms actually being followed?

## When to Use

- Start the catalog after your first coordination failure (you'll know it when it happens)
- Add entries in real-time — don't batch them
- Review periodically — the patterns that emerge are more valuable than individual entries

## Real Example

The proving-ground project accumulated 8 coordination failures over approximately two weeks of multi-agent construction. The failures clustered in three categories: Partial Update (3 incidents), Context Starvation (2 incidents), and Silent Completion (1 incident at 43% rate within a single dispatch). This clustering revealed that the project's biggest gaps were **cross-file consistency** (keeping documents synchronized) and **agent reliability** (verifying agents actually produce artifacts). The Silent Completion failure was particularly insidious — without `git diff` verification, 3 of 7 parallel agents would have been accepted as complete with zero work product.

## Anti-Patterns

- **Not recording failures.** "It worked out in the end" doesn't prevent recurrence. The fix might have taken an entire session that could have been avoided.
- **Blaming the agent.** The agent did what it was told with the context it had. The failure is in the protocol, not the execution.
- **Recording too much detail.** The catalog should be scannable. Root cause + prevention is more valuable than a blow-by-blow transcript.
- **Not reviewing the catalog.** A catalog nobody reads is just documentation debt. Review it when planning new work to check if known failure modes apply.



================================================
FILE: patterns/CROSS_FILE_CONSISTENCY.md
================================================
# Cross-File Consistency Gate

## Problem

When a fact changes — a verdict reclassification, a count update, a status change — it often lives in multiple files. An agent updates one file and moves on, leaving the others stale. The project now contains contradictory information, and the next agent to read both files has no way to know which is correct.

This is the most common coordination failure in multi-agent projects. It's silent (no test fails), cumulative (each partial update makes the state harder to reconstruct), and contagious (agents reading stale files propagate the error into new work).

## Solution

**All-or-nothing updates.** When a fact changes, the agent must update every file that references it in the same commit. If the agent can't identify all affected files, it must flag the update as partial and document what's missing.

### Implementation

**1. Cross-Reference Map**

Maintain a map of which facts live in which files:

```
FACT: Bug count per domain
FILES: BONE_LAYER_CHECKLIST.md (summary row)
       WRONG_VERDICTS_MASTER.md (row count)
       DOMAIN_X_VERIFICATION.md (section summary)
       FIX_WO_DISPATCH_PACKET.md (WO bug count)
```

When an agent changes a bug count, it must touch all four files.

**2. Consistency Gate in Commit Protocol**

Before committing a fact-change, the agent runs a mental (or scripted) check:

```
For each fact I changed:
  - Which other files reference this fact?
  - Did I update all of them?
  - If not, what's missing and why?
```

If any file is missed, add it to the same commit or document the gap explicitly.

**3. Tier 1 Enforcement (Optional)**

For critical facts (counts, statuses, version numbers), write a test that cross-checks files:

```python
def test_bug_count_consistency():
    """Checklist bug count must match WRONG_VERDICTS_MASTER row count."""
    checklist_count = parse_checklist_totals()
    master_count = count_master_rows()
    assert checklist_count == master_count
```

This catches drift automatically. The test name tells the fixing agent exactly what to reconcile.

## When to Use

- Any verdict, count, or status that appears in more than one file
- Schema changes that affect consumers (e.g., adding a field to a dataclass requires updating serialization, aggregation, and tests)
- Reclassifications (WRONG → AMBIGUOUS) that propagate across verification files, master lists, and dispatch packets

## When NOT to Use

- Single-file facts (a function's docstring describing its own behavior)
- Ephemeral state (a session memo's "current task" — it's only read once)

## Real Example

**Domain A re-verification** found 4 bug reclassifications. The agent updated the checklist and WRONG_VERDICTS_MASTER but missed DOMAIN_C_VERIFICATION.md. Result: the checklist said "1 WRONG / 3 AMBIGUOUS" for Domain C, but the verification file still said "3 WRONG / 1 AMBIGUOUS." A later agent reading the verification file would dispatch fix WOs for bugs that had already been reclassified as design decisions.

The fix: a second commit (`6982005`) caught the gap and brought the verification file into consistency. The lesson: the original commit should have touched all three files.

## Anti-Patterns

- **"I'll fix the other files later"** — you won't. The context rotates, the gap becomes invisible, and a future agent reads the stale file.
- **Updating only the "primary" file** — there is no primary file. All files that contain a fact are equally authoritative to the next agent that reads them.
- **Relying on agents to notice inconsistencies** — agents trust files. If a file says 3 WRONG, the agent believes 3 WRONG. The inconsistency is invisible unless both files are in the same context window.



================================================
FILE: patterns/DEBRIEF_INTEGRITY_BOUNDARY.md
================================================
# Pattern: Debrief Integrity Boundary

## Problem

The debrief format trusts agents to accurately self-report what happened during a session — including mistakes, dead ends, and mid-session course corrections. This trust is mostly justified (agents don't have incentives to lie), but it creates a blind spot: the PM and operator cannot distinguish between "no concerns reported" meaning "the agent thought carefully and found nothing" versus "the agent didn't think about it."

The test suite provides partial verification — an agent can't fabricate test counts or claim files were modified when `git diff` shows otherwise. But the prose sections of a debrief (retrospective, methodology notes, concerns) are unverifiable by any automated means. The framework relies on agent honesty for these sections, and that reliance should be named explicitly rather than assumed implicitly.

## The Verification Spectrum

Not all debrief content has the same integrity level. Debrief fields fall on a spectrum from machine-verifiable to prose-only:

### Tier 1: Machine-Verifiable (Highest Integrity)

These fields can be independently confirmed by running a command. An agent cannot misrepresent them without the discrepancy being detectable.

| Field | Verification Method |
|-------|-------------------|
| Test pass/fail counts | `pytest` output |
| Files modified | `git diff --stat` |
| Commit hashes | `git log` |
| File existence | `ls` / `stat` |
| Import graph changes | `grep` for import statements |
| Boundary law compliance | Boundary law test suite |

**Integrity guarantee:** ~100%. If the agent claims 5,804 tests pass and `pytest` shows 5,800, the discrepancy is immediately visible.

### Tier 2: Process-Verifiable (Medium Integrity)

These fields can be cross-checked against other artifacts but require human judgment to interpret.

| Field | Verification Method |
|-------|-------------------|
| Files listed as modified | Cross-check against `git diff` |
| Scope compliance | Compare diff against WO scope boundaries |
| "What was done" summary | Compare against commit messages and diff |
| Mid-session corrections | Partial — visible in commit history if multiple commits |

**Integrity guarantee:** ~70-80%. The agent's description of what they did can be compared against what the diff shows, but the diff doesn't capture intent, reasoning, or rejected alternatives.

### Tier 3: Prose-Only (Lowest Integrity)

These fields exist only in the agent's self-report. No external artifact confirms or contradicts them.

| Field | What's Unverifiable |
|-------|-------------------|
| Retrospective | Whether the agent actually considered alternatives |
| Concerns section | Whether "no concerns" reflects analysis or omission |
| Methodology notes | Whether the described approach was actually followed |
| Fragility assessment | Whether the agent identified all fragile points |
| Process feedback | Whether the feedback reflects genuine evaluation |

**Integrity guarantee:** ~40-60%. The agent has no incentive to lie, but also no structural pressure to be thorough. An agent that runs out of context window will produce a thin retrospective, not because it's dishonest but because it's depleted.

## Mitigation Options

### Option 1: Cross-Agent Audit (Expensive)

A second agent reads the first agent's debrief alongside the actual diff and flags discrepancies. This catches cases where the debrief describes work that doesn't match the artifacts.

**Cost:** One additional agent session per debrief. Doubles the overhead.
**When to use:** High-stakes WOs where incorrect self-reporting could cascade (e.g., schema changes, security-sensitive code).

### Option 2: Spot-Check Protocol (Moderate)

The PM randomly selects one debrief per cycle and deep-dives: reads the diff, runs the tests, and compares against the debrief's claims. This provides statistical deterrence without auditing every session.

**Cost:** ~30 minutes of PM time per cycle.
**When to use:** Standard operating procedure. Catches systemic reporting gaps without auditing every session.

### Option 3: Expand the Machine-Verified Surface (Structural)

Add structured fields to the debrief that can be cross-checked:
- **Require `git diff --stat` output** in the debrief (already recommended in F-003 fix)
- **Require test output** (pass/fail/skip counts) as a structured field, not prose
- **Require commit hash list** so each claim of "I committed X" maps to a verifiable hash
- **Add a "files read" list** that can be cross-checked against the agent's actual tool usage (where platform supports it)

**Cost:** Template changes. Minimal per-session overhead.
**When to use:** Always. This is the lowest-cost, highest-impact mitigation.

### Option 4: Debrief-by-Next-Agent (Structural)

Instead of the builder writing their own debrief, the next agent writes the debrief by reading the diff and commit history. This provides natural cross-agent verification — a different agent interpreting what was done, rather than the builder self-reporting.

**Cost:** Small overhead at the start of the next session.
**When to use:** When builder context windows are depleted (debrief quality degrades at window end). Also addresses the structural problem of mandatory output (commit + debrief) coming at the worst possible time — when the window is most exhausted.

## Implementation

### Minimum Viable Integrity Gate

Add these structured fields to the debrief template (non-prose, machine-checkable):

```markdown
## Machine-Verified Output
- **Test results:** [paste pytest summary line]
- **Files modified:** [paste git diff --stat output]
- **Commits:** [list commit hashes with one-line messages]
- **Pre-existing failures:** [count and list, to distinguish from regressions]
```

The PM can verify any of these in under 60 seconds. If the structured fields match the prose description, confidence in the prose is higher. If they don't match, the prose is suspect.

### Debrief Review Checklist (for PM)

When reviewing a debrief, check:
- [ ] Do the test counts in the debrief match a recent `pytest` run?
- [ ] Does the "files modified" list match `git diff --stat` for the relevant commits?
- [ ] Are the commit hashes real? (`git log --oneline` to verify)
- [ ] Does the "concerns" section contain specific observations, or is it generic/empty?
- [ ] If the retrospective says "no issues," does the commit history show a clean single-pass, or multiple fix-up commits suggesting issues that weren't reported?

## When to Use

- When establishing a new multi-agent project and designing the debrief format
- When a debrief is discovered to be inaccurate (promotes awareness of the trust boundary)
- When deciding how much to trust a debrief's prose sections for planning purposes

## Anti-Patterns

- **Assuming all debrief content is equally reliable.** Machine-verified fields and prose retrospectives have fundamentally different integrity levels. Treat them accordingly.
- **Assuming all prose is unreliable.** Agents are generally honest reporters. The issue isn't deception — it's thoroughness under context pressure. An agent at 90% context utilization will write a worse retrospective than one at 50%, not because it's lying but because it's depleted.
- **Auditing every debrief.** The cost exceeds the benefit for routine WOs. Reserve cross-agent audit for high-stakes changes.
- **Not auditing any debriefs.** Without occasional verification, the trust assumption is untested. Spot-checks keep the system honest.

## Real Example

The proving-ground project's WO-RNG-PROTOCOL-001 debrief reported a mid-session course correction: `replace_all` of `RNGManager` accidentally hit constructor call sites in `replay_runner.py` and `session_log.py`. The debrief described the error and the fix. This claim is partially verifiable — the commit history would show whether a fix-up commit exists. But the agent's statement that it "caught the error immediately in the first test run" is prose-only — there's no artifact confirming the timing. The PM trusts this claim based on the overall consistency of the debrief, not because it's independently verified.



================================================
FILE: patterns/DISCOVERY_QUEUE_TRACEABILITY.md
================================================
# Pattern: Discovery-Queue Traceability

## Problem

A research sprint produces a findings memo. An audit produces a Radar table with 12 findings. A strategy document identifies 6 recommended tools and 3 architectural changes. These artifacts are filed, reviewed, and accepted.

Six months later, nothing has been built from them. The operator asks "why are we still hand-coding data that we identified as available from an OSS source?" The PM has no answer because the research was documented but never routed. The findings memo is preserved. The WO queue never received a single item from it.

This is the research-to-queue orphan: a finding that exists in documentation but has no downstream action.

The damage:
- Work already done in research has to be rediscovered
- Approved approaches are bypassed in favor of slower manual alternatives
- Operator trust erodes when decisions don't survive into execution
- The documentation becomes noise — reading it reveals findings that were never acted on

## Solution

Every research artifact, audit output, or strategy document must have all of its action items entered into a traceability register and assigned a disposition before the artifact is considered closed.

### The Three Valid Dispositions

```
WO DISPATCHED      — a work order exists in the queue or has been accepted
DEFERRED           — explicitly parked with a rationale and a review date
CLOSED             — finding is superseded, invalid, or not actionable; reason stated
```

A finding with no disposition is not "open" — it is a traceability failure.

### The Register

Maintain a single discovery-queue traceability register. Each research artifact gets an entry:

```markdown
## [Artifact Name] — [date]
Source: [file path or link]

| Finding | Disposition | WO / Notes |
|---------|-------------|------------|
| [Finding 1] | WO DISPATCHED | WO-DATA-FEATS-001 |
| [Finding 2] | DEFERRED | Requires WeChat decryption first — revisit Q2 |
| [Finding 3] | CLOSED | Superseded by architectural change in Batch AC |
| [Finding 4] | ??? | — |     ← This row is a governance failure
```

The register is reviewed on a fixed cadence (every N batches or every PM boot). Any row with no disposition is treated as a blocker on the next research/audit dispatch — the PM must route the unrouted items before opening new research.

## Why "Documented" Is Not Enough

There is a common mistake in treating "filed" as equivalent to "actioned." A finding memo in a reviewed folder looks like work product. It is not work unless:

1. Someone read the finding, and
2. Decided what to do with it, and
3. Recorded that decision where it can be tracked

Step 3 is the failure point. Steps 1 and 2 often happen implicitly, in the moment, during a session. Without step 3, the decision evaporates between sessions. The next session starts fresh. The finding is rediscovered or, worse, bypassed without being rediscovered.

The traceability register is step 3 made mandatory.

## Implementation

### At Research Close

When a research artifact is filed, the PM must immediately populate the register entry for that artifact. This happens before the artifact is archived. A filing without a register entry is an incomplete close.

### At Audit Close

When an audit debrief is filed with a Radar table, each Radar finding gets a disposition before the audit WO can be ACCEPTED:
- CRITICAL/HIGH findings → WO dispatched immediately or explicitly escalated
- MEDIUM findings → either WO queued or DEFERRED with rationale
- LOW findings → may be CLOSED or DEFERRED on PM judgment; rationale required

The auditor files findings. The PM routes them. Both steps are required.

### At Boot (PM Seat)

On PM boot, after reading the WO queue and briefing:
- Read the traceability register
- Identify any findings with no disposition
- Route them before any other PM work

An unrouted finding is a first-class open item, not background context.

### At the Fixed Review Cadence

Every N batches (configurable — 3 and 5 batch intervals are common for the register and the backlog respectively):
- Review all entries with DEFERRED disposition
- For each: is the deferral rationale still valid? If not, promote to WO.
- For each: has the review date passed? If so, either extend explicitly or promote.

A DEFERRED finding without a review date is treated as a traceability failure.

## Relationship to Research-to-Build Pipeline

The Research-to-Build Pipeline pattern handles how to correctly convert a raw operator insight into builder-ready work orders. This pattern handles the enforcement gate that ensures the pipeline actually completes.

The pipeline can fail at any stage:
- **Burst captured but no Research WO** → tracked in the intake queue
- **Research complete but no Brick** → tracked as research-stage stall
- **Brick ready but no Builder WO** → tracked in the traceability register
- **Builder WO accepted but finding never closed** → tracked in the traceability register

Discovery-queue traceability catches the last two. The intake queue catches the first two. Together they close all the gaps in the pipeline.

## Anti-Patterns

**The findings cemetery:**
A folder full of reviewed memos, debriefs, and audit reports — all correctly filed, all with no register entries. The project "has good documentation" but the documentation hasn't moved anything. The PM reads artifacts at session start and gains context but takes no routable action from them. Artifacts inform but never dispatch.

**The implicit routing:**
"I read finding 4 and decided it wasn't important." Without recording that decision, future agents will encounter finding 4 again and have to re-decide — or worse, assume it was an oversight and treat it as open. Explicit dispositions are not bureaucracy; they are the only way to communicate past decisions to future context windows.

**The permanent defer:**
A finding DEFERRED without a review date effectively becomes closed without being declared closed. If the rationale is still valid after a year, the finding should be CLOSED with documentation of why it won't be acted on. DEFERRED is not a permanent state — it is a timed pause.



================================================
FILE: patterns/DISPATCH_SELF_CONTAINMENT.md
================================================
# Pattern: Dispatch Self-Containment

## Problem

When you assign a task to an LLM agent, the agent has no memory of previous sessions. If the work order says "continue the refactoring from last session" or "fix the bug we discussed," the agent has no idea what you're talking about. It will either hallucinate context or ask questions that waste your time.

More subtly: even when work orders look complete, they often contain implicit dependencies — references to decisions made in conversation, file locations that changed since the dispatch was written, or context that "everyone knows" but the new agent doesn't.

## Solution

Every work order must be **self-contained**: executable by an agent with zero prior context. The dispatch file plus the files it explicitly references must contain everything needed to complete the task.

### The Self-Containment Test

Before dispatching a work order, ask:

> Could a brand-new agent — with no conversation history, no memory of previous sessions, and no context beyond what's in this file — execute this dispatch using only this file and the files it references?

If the answer is no, the dispatch is incomplete. Add the missing context.

### What Self-Contained Looks Like

```markdown
# Work Order: Fix Minimum Damage Floor

## Context
The attack resolver (`aidm/core/attack_resolver.py`) uses `max(0, damage)`
to prevent negative damage values. The rule source (PHB p.141) specifies
that minimum damage is 1, not 0. This affects lines 142 and 167.

## Task
Change `max(0, damage)` to `max(1, damage)` at both locations.

## Files to Modify
- `aidm/core/attack_resolver.py` (lines 142, 167)

## Files to Read First
- `DEVELOPMENT_GUIDELINES.md` Section 6 (resolver mutation rules)

## Verification
- Run: `python -m pytest tests/test_attack_resolver.py -v`
- Expected: all tests pass
- Write new test: `test_minimum_damage_is_one()`

## What NOT to Do
- Do not modify full_attack_resolver.py (separate work order)
- Do not change the damage calculation formula, only the floor clamp
```

### What Non-Self-Contained Looks Like

```markdown
# Work Order: Fix the damage bug

Fix the issue we found during verification.
You know which file — the one with the min/max problem.
Make sure it matches the SRD.
```

This will fail. The agent doesn't know which bug, which file, which SRD reference, or what "matches" means in this context.

## Implementation

### Dispatch Checklist

Before sending any work order to an agent, verify:

- [ ] **Context section** explains why this change is needed (not just what)
- [ ] **File paths** are explicit and current (not "the usual file")
- [ ] **Line numbers** are verified against current code (not stale from a prior commit)
- [ ] **Referenced documents** are listed with their paths
- [ ] **Acceptance criteria** are machine-verifiable (test commands, expected output)
- [ ] **Scope boundaries** are explicit (what NOT to touch)
- [ ] **No implicit knowledge** required — no "as we discussed," no "you know the one"

### Dispatch Template

```markdown
# [WO-ID]: [Short Title]

## Context
[Why this work exists. What problem it solves. 2-3 sentences.]

## Task
[Exactly what to do. Specific, concrete, unambiguous.]

## Files to Modify
[Explicit paths, with line numbers if applicable]

## Files to Read First
[Governance docs, related code, design decisions — with paths]

## Verification
[Commands to run, expected output, tests to write]

## Scope Boundaries
[What NOT to do. Adjacent work that belongs to other work orders.]

## Dependencies
[Other WOs that must complete first, if any. Otherwise: "None."]
```

## When to Use

- Every time you assign work to an LLM agent
- Even when "it should be obvious" — it isn't, because the agent has no context
- Especially for parallel dispatches where multiple agents work simultaneously

## Real Example

The proving-ground project dispatched 13 fix work orders covering 30 bugs across 15 files. Each WO was ~500 tokens and independently executable. Seven groups of agents ran in parallel without coordination, because each dispatch was self-contained. No agent needed to know what the other agents were doing.

The contrast: earlier in the project, work orders were written conversationally ("fix the cover values, you know the ones from the verification"). These required follow-up questions, produced incorrect fixes, and wasted entire context windows.

## Anti-Patterns

- **"Continue from where we left off."** The agent doesn't know where "we" left off. Write a new dispatch that stands alone.
- **"See the discussion in the previous session."** Sessions don't carry over. Extract the relevant decisions into the dispatch.
- **"Fix all the bugs."** Without specific bug IDs, file paths, and expected behavior, this produces guesswork. One dispatch per coherent task.
- **Assuming line numbers are still correct.** Code changes between when the dispatch was written and when the agent reads it. Include enough context (function names, surrounding code) that the agent can find the right location even if lines shifted.



================================================
FILE: patterns/ENFORCEMENT_HIERARCHY.md
================================================
# Pattern: Enforcement Hierarchy

## Problem

You discover a mistake. You write a rule to prevent it. You add the rule to the development guidelines. The next agent makes the same mistake. You add it to the onboarding checklist too. The agent after that still makes the mistake.

Rules written in prose don't stick. New agents read them, acknowledge them, and then violate them because the rule isn't enforced at the point where the violation happens.

## Solution

Recognize that enforcement has three tiers with dramatically different stickiness. When you discover a new rule, consciously choose which tier to enforce it at — and understand that lower tiers will have higher violation rates.

### Tier 1: Test-Enforced (Stickiest)

The rule is checked by an automated test. If an agent violates it, the test suite fails, and the agent must fix it before completing their work.

**Stickiness:** ~100%. Agents can't miss a failing test.

**Examples:**
- Boundary law BL-017: No `uuid.uuid4()` in default_factory → tested in `test_boundary_law.py`
- Boundary law BL-020: No WorldState mutation outside engine → tested
- Test runtime invariant: full suite < 120 seconds → enforced by CI

**When to use:** For rules that are mechanically checkable and where violations cause significant damage. The rule must be expressible as "does this code pattern exist? → fail."

**Cost:** Writing and maintaining the test. Some rules are hard to test (e.g., "use correct D&D edition terminology" is hard to check mechanically).

### Tier 2: Process-Enforced (Medium)

The rule is embedded in a process step that agents follow. Not automated, but positioned at a point where the agent naturally encounters it.

**Stickiness:** ~70-80%. Most agents follow the process; some skip steps under pressure or when they think the step doesn't apply.

**Examples:**
- Onboarding checklist: "Read governance docs in this order" → positioned as Step 1
- Work order template: "Scope Boundaries" section → positioned where the agent reads their task
- Builder debrief: "Write debrief before closing session" → positioned as last step in WO

**When to use:** For rules that can't be mechanically tested but can be positioned at a natural checkpoint. The rule should appear at the point where the agent makes the relevant decision.

**Cost:** Adding a step to a template or checklist. Risk: agents optimize for speed and skip steps they judge as unnecessary.

### Tier 3: Prose-Enforced (Weakest)

The rule is documented in a guidelines file. Agents are told to read it. Compliance depends on reading comprehension and memory.

**Stickiness:** ~40-60%. Agents read the rule, understand it in the moment, and then forget it when solving a different problem 10 minutes later.

**Examples:**
- "Don't use 5e terminology" → documented in dev guidelines Section 7
- "Don't use bare string literals for entity fields" → documented in Section 1
- "Conditions are stored as dicts, not lists" → documented in Section 9

**When to use:** For rules that can't be tested or positioned at a checkpoint. This is the catch-all tier. Expect violations and plan for them.

**Cost:** Minimal to write. High in violations. Each violation costs a context window to discover, diagnose, and fix.

## Promoting Rules Between Tiers

When a prose rule (Tier 3) gets violated repeatedly, **promote it** to a higher tier:

```
Tier 3 (prose rule)
  → First violation: add to "DO NOT" list in onboarding checklist (still Tier 3, but more prominent)
  → Second violation: add to work order template as explicit prohibition (Tier 2)
  → Third violation: write an automated test that catches it (Tier 1)
```

Not every rule needs to be Tier 1. The cost of writing tests for every guideline is prohibitive. But rules that agents violate repeatedly are worth the investment in a test.

### Signals That a Rule Needs Promotion

- Same rule violated in 2+ different sessions
- Violation causes significant rework (context window wasted on fixing)
- Rule is frequently "rediscovered" by agents during work
- Rule violations cascade into other problems

## Implementation

### Audit Your Current Rules

| Rule | Current Tier | Violation Count | Should Promote? |
|------|-------------|-----------------|-----------------|
| [Rule 1] | Tier 3 (prose) | 3 | Yes → Tier 1 test |
| [Rule 2] | Tier 2 (process) | 0 | No |
| [Rule 3] | Tier 3 (prose) | 1 | Not yet |

### When Adding a New Rule

1. Write the rule as prose (Tier 3) immediately — don't wait for the perfect enforcement
2. Assess: is this mechanically testable? If yes, write the test (Tier 1) now
3. If not testable: can it be positioned at a checkpoint? Add to template/checklist (Tier 2)
4. Track violations. Promote on repeated failure.

## Real Example

The proving-ground project started with "use `EF.*` constants for entity fields" as prose in the development guidelines (Tier 3). An agent violated it, causing a silent bug where HP clamping never triggered (used `"current_hp"` instead of `EF.HP_CURRENT`). The rule was then promoted:
- Added to "DO NOT" list in onboarding checklist (still Tier 3, more prominent)
- Added to Common Pitfalls Checklist at the end of the guidelines (Tier 2 — agents check it before submitting)
- Boundary law BL-020 partially covers this pattern by preventing state mutation outside the engine (Tier 1)

After promotion, zero recurrences.

## Anti-Patterns

- **Assuming prose is sufficient.** It isn't. New agents skim. Rules that matter need enforcement above Tier 3.
- **Testing everything.** Test maintenance is a cost. Reserve Tier 1 for rules that cause real damage on violation.
- **Not tracking violations.** Without violation data, you can't know which rules need promotion. Even informal tracking ("this happened twice") is better than nothing.
- **Blaming the agent for not reading the docs.** The agent read them. Reading isn't the problem — retention during task execution is. If you need the rule to stick, enforce it at the point of violation, not the point of reading.



================================================
FILE: patterns/HIDDEN_ASSUMPTION_SWEEP.md
================================================
# Pattern: Hidden Assumption Sweep

## Problem

Requirements documents and specifications are written for human practitioners who already carry undocumented layers of judgment, context, and common sense. When you build a system from those documents, those hidden layers do not transfer automatically — they surface later as unexpected gaps in behavior.

This creates a specific failure mode: a seemingly simple question reveals that a fundamental assumption about scope or behavior was wrong. Left unaddressed, these moments become silent production failures.

**The failure pattern:**
- Someone notices an edge case or asks an obvious question
- The question turns out not to be answerable from existing specs
- Rather than stopping, the team makes a locally-reasonable assumption and continues
- The assumption bakes into implementation
- Weeks later, the assumption is discovered to have been wrong
- Rework follows

**Root cause:** There is no protocol for catching these moments at the right time. The question felt small. Nobody classified it as architectural. It slipped through.

---

## Solution

### Rule

**When a question starts to feel larger than it should, run the Hidden Assumption Sweep before continuing.**

The sweep is a 10-question triage protocol. It takes 3-10 minutes. Its goal is not to solve the problem — it is to classify it correctly so it gets the right kind of follow-up.

**Classification rule:**

> If the answer changes what "done" means, crosses a system boundary, or reveals that the system currently fails open — file it as a strategy item, not a work order.

### The 10-Question Sweep

Answer each question YES / NO / UNKNOWN.

1. **Is this a missing feature or a missing assumption?** (Assumptions are more dangerous — they affect everything built on top of them)
2. **Does it change what "done" means for any existing WO or milestone?**
3. **Does it live at a system boundary?** (Between two subsystems, between system and users, between two resolvers that hand off to each other)
4. **Does the system currently fail closed (silent, safe) or fail open (inventing answers) at this point?**
5. **Does it require a human judgment layer that the source documentation never explicitly defines?**
6. **Does it affect multiple subsystems or just one?**
7. **Can a user or adversary expose this gap through normal, reasonable behavior?**
8. **Is there an observable failure mode, or is this a silent failure?**
9. **Who is authorized to make the ruling if the system cannot?**
10. **What must be true about system state for any ruling here to be meaningful?** (If the required state is not tracked, flag as a world-model gap — not just a logic gap)

### Escalation Rule

**Escalate to STRATEGY (not WO) if:**
- 3 or more answers are UNKNOWN, **or**
- the issue changes the definition of done for anything in progress, **or**
- the issue crosses a system boundary where current behavior is not fail-closed

When in doubt, escalate. The cost of filing a strategy item that turns out to be minor is low. The cost of treating an architectural assumption as a routine work order is high.

### Grenade Categories (Quick Reference)

| Category | Description |
|----------|-------------|
| **Hidden Human Layer** | Judgment, pacing, or common sense that practitioners know implicitly but the spec never states |
| **Boundary Protocol Gap** | The handoff between two subsystems is undefined or ambiguous |
| **Fail-Open Gap** | Uncertainty causes the system to invent answers rather than surface the uncertainty |
| **Observability Gap** | No way to know what the system decided or why |
| **Definition-of-Done Drift** | Completion criteria have changed but existing WOs have not been updated |
| **Authority Gap** | Who makes the ruling when the system cannot? Nobody knows. |
| **Promotion Path Gap** | One-off rulings made ad hoc never become documented, repeatable capability |

---

## Implementation

### When to Run the Sweep

Run immediately when any of the following happens:

- A small idea suddenly reframes architecture or scope
- A fix starts to feel too large for a normal work order
- Something feels dangerous but you cannot yet name why
- A discussion shifts from "how to implement this" to "what does done actually mean"
- A test case reveals behavior that is technically correct but clearly wrong in context

**Target runtime:** 3-10 minutes for first pass. You are classifying, not solving.

### Output Format

Every sweep produces a short artifact note:

```markdown
**Working name:** [what this issue is, in plain language]
**Category:** [from the grenade categories above, or describe]
**Type:** assumption gap | boundary gap | DoD correction | missing protocol
**Immediate risk:** [what can go wrong if this is ignored]
**Current behavior:** known | unknown | fail-open | fail-closed
**Proposed artifact type:** strategy | probe | WO | gate | spec | design note
**Blocking status:** blocking | non-blocking | shadow-track
```

This artifact is filed immediately — not noted for later, not mentioned in a message. Filed.

### Routing After Classification

| Classification | Action |
|----------------|--------|
| Feature-local issue | Draft a WO, scope contained, gate as usual |
| Missing assumption or boundary issue | File STRATEGY first, then derive supporting WOs |
| Unknown risk or meaningful concern | File a PROBE before implementation direction |
| Vague or unverifiable criteria | File a GATE or acceptance rubric first |
| Reframes architecture or doctrine | File a DESIGN NOTE or THESIS anchor |

Strategy items are not resolved by the PM alone. The operator reviews and makes explicit decisions. Strategy items resolved in conversation without an artifact violate the protocol.

### The Fail-Safe

If you cannot classify the issue confidently in one pass:
- Mark it UNKNOWN / STRATEGY CANDIDATE
- File a short note
- Hand to PM for packetization
- Do not carry the full problem in working memory

The point of the protocol is to prevent operator overload from becoming architecture drift.

---

## When to Use

- Any project where requirements come from an external specification written for human practitioners
- Any project where "reasonable interpretation" has historically meant different things to different agents
- Any time a question arises that starts with "obviously the system would" — test that assumption
- Before any cross-cutting change that touches a shared utility or central coordinator

## When NOT to Use

- For clearly scoped, local feature requests with no cross-system implications
- When the answer is unambiguously in the specification and no judgment is required
- As a substitute for a proper design review on a major feature (the sweep classifies, it does not replace design)

---

## Real Example

A team was building an engine that resolved named game mechanics from a rulebook. During a build session, someone asked: what happens when a player tries to do something the rulebook does not have a rule for?

The question felt small. The immediate instinct was to add a fallback handler work order.

Running the sweep revealed:
- Q5 (human judgment layer): YES — the rulebook assumes a human referee who can reason by analogy
- Q4 (fail-open): YES — the current system would invent a result rather than surface the uncertainty
- Q10 (required state): UNKNOWN — the system does not track enough scene context to reason about improvised actions
- Classification: 4 UNKNOWNs — escalate to STRATEGY

The STRATEGY item led to a design document identifying three architectural options. The builder WO that was almost dispatched would have solved the symptom while missing the architecture question entirely.

**Without the sweep:** A patch would have shipped. The underlying gap would have accumulated silently.
**With the sweep:** The question got the right level of attention. The architecture decision was explicit. Subsequent WOs were written against a clear spec.

---

## Anti-Patterns

- **Filing a WO for something that returned UNKNOWN on 3+ sweep questions.** That is a strategy item wearing a WO's clothes.
- **Running the sweep without filing the output.** The sweep produces an artifact, not a conversation.
- **Using the sweep to defer indefinitely.** Classify, route, act. The sweep is a triage tool, not a parking lot.
- **Treating "nobody else noticed" as evidence it is not a real gap.** Hidden assumptions are hidden precisely because they feel obvious until they are not.



================================================
FILE: patterns/INTEGRATION_CANARY.md
================================================
# Integration Canary

## Problem

Each agent builds and tests its piece in isolation. All unit tests pass. But nobody tries to use the product end-to-end. Constraints (boundary laws, frozen schemas, protocol interfaces) produce consistency within modules but cannot produce integration across modules.

**Symptoms:**
- "Works in isolation, fails in integration"
- Data bridges wired but dormant (code exists, data never flows)
- Validation rules that structurally cannot fire (the field they check is always empty)
- Compile stages that exist but aren't registered in production callers
- 5,000+ unit tests passing, zero integration tests

## Solution

Before dispatching new infrastructure WOs, run one script that exercises the full product path. Whatever breaks is your next WO.

**The script pattern:**
1. Set up minimal input (content pack, seed data, test fixture)
2. Run the full pipeline (compile → initialize → execute → output)
3. Print what worked and what didn't at each stage
4. Document every break point with module, line, and error

**The operational rule:**
- No new infrastructure WOs until the canary runs
- Each break point from the canary becomes a work order
- Each integration fix must include a test that exercises the seam (preventing regression)
- The canary script itself becomes a permanent CI artifact

## When to Use

- After completing a batch of module-scoped WOs
- Before transitioning from one project horizon to the next
- When unit test count is growing but confidence in the product isn't
- When architecture audits keep finding "theoretical gaps" — run the system instead

## When Not to Use

- During active development of a single module (unit tests are sufficient)
- When the product path doesn't exist yet (you need components before you can integrate them)

## Real Example

**D&D 3.5e engine, end of H1 WO batch (2026-02-14):**

7 WOs completed across parallel agents: weapon plumbing, RNG protocol extraction, TTS chunking, NarrativeBrief width extension, compile-time cross-validation, runtime narration validation, TTS cold start research. 5,775 unit tests passing.

The operator's directive: "You have 5800 tests that prove individual bricks are solid, but no test that proves the building stands up."

**Predicted break points (confirmed by smoke test):**
- `SPELL_REGISTRY` entries lack `content_id` — Layer B narration permanently dormant
- `CrossValidateStage` not registered in production `WorldCompiler` — cross-validation doesn't run
- `NarrationValidator` not wired into play loop — validation rules exist but never execute
- `content_id` bridge: events → lookup → presentation_semantics: wired but produces `None`

None of these were caught by unit tests. All were caught by trying to cast fireball at a goblin.

## Key Insight

> Constraints produce consistency. Integration produces a product. You need both, and they require different types of work — module-scoped WOs for constraints, cross-cutting WOs for integration.

## Related Patterns

- [Enforcement Hierarchy](ENFORCEMENT_HIERARCHY.md) — Integration seam tests are Tier 1 enforcement
- [Cross-File Consistency Gate](CROSS_FILE_CONSISTENCY.md) — Integration canary is the cross-module version of this
- [Dispatch Self-Containment](DISPATCH_SELF_CONTAINMENT.md) — Integration WOs need broader context than module WOs



================================================
FILE: patterns/PARALLEL_IMPLEMENTATION_PARITY.md
================================================
# Pattern: Parallel Implementation Parity

## Problem

A codebase accumulates **parallel code paths** — two or more functions that compute the same logical result independently. This is common in systems that grow incrementally: a "fast path" and a "full path," a simplified resolver and a complex one, a legacy handler and a new one.

When a work order targets one of these paths, it fixes that path. The other paths are not mentioned in the WO, so the builder doesn't know they exist. The result: the fix lands in one location but the same bug silently persists in the others.

**The root cause is that WO dispatches don't enumerate parallel paths.** Each WO is written to fix a specific known gap. It treats the target function as the only implementation. No one is responsible for asking "where else does this same logic exist?"

**The scale of the damage:** In one project, 21 independent modifier calculations drifted across two parallel code paths over 30+ work orders. Each individual WO was correct for its target path. No WO caused the drift. The drift accumulated silently because no dispatch ever listed both paths. The divergence was only discovered by a systematic audit 30+ work orders later — representing significant rework and regression risk.

## Solution

### Rule

**Every WO that modifies a function that computes a result must identify ALL parallel code paths that compute the same result before work begins.**

The builder verifies parity across all identified paths before filing the debrief. A debrief that doesn't address all parallel paths is incomplete.

### How to Find Parallel Paths

Before drafting a WO, ask:

1. Is there more than one function or code path that produces this output?
2. Are there "light" and "heavy" variants of the same operation? (e.g., single-item and batch processors, simplified and full-featured versions)
3. Are there legacy code paths that handle the same case?
4. Does the same calculation appear in both "read" and "write" paths?

Document all paths in the WO's **Parallel Implementation Paths** section. If you don't know all paths, write: *"Builder: identify parallel paths as first task before any code changes."*

### Dispatch Template Section

Add this section to every WO that modifies resolver/calculator functions:

```markdown
## Parallel Implementation Paths

| Path | File | Function | Status |
|------|------|----------|--------|
| Primary | [file.py] | [function_name()] | This WO targets |
| Secondary | [file.py] | [function_name()] | Builder must verify parity |
| Legacy | [file.py] | [function_name()] | Builder must verify parity |

**Builder instructions:** Verify that all parallel paths produce the same result for the same inputs after this WO lands. If they don't, the secondary paths must be updated in the same commit or the divergence must be logged as a finding.
```

### Parity Verification

The builder must confirm one of the following for each parallel path:

- **Same fix applied** — the same correction was applied to this path
- **Already correct** — this path was already correct; no change needed; verified by inspection
- **Delegates** — this path delegates to the primary path; no independent implementation
- **Scoped out** — this path is intentionally different (document why)

The debrief must include a parity table:

```markdown
## Parallel Path Parity

| Path | File:Line | Outcome | Notes |
|------|-----------|---------|-------|
| Primary | [file:line] | Fixed | This WO |
| Secondary | [file:line] | Already correct | Delegates to primary |
| Legacy | [file:line] | Fixed | Same change applied |
```

Missing parity table → debrief rejected.

## When the PM Doesn't Know the Parallel Paths

This is normal. The PM drafts WOs from findings and research, not from full codebase knowledge. When the parallel paths are unknown at dispatch time, the WO dispatch section reads:

> *"Builder: identify all parallel paths implementing [logic description] as your first task. Document them before writing any code. If parallel paths exist and are not addressed, log a finding."*

The builder has context the PM doesn't. Making parallel path identification the builder's first task puts the responsibility at the right point in the workflow — with the agent that can actually verify it.

## Implementation

### Checklist: Does This WO Need Parity Verification?

| If the WO... | Then parity verification is... |
|--------------|--------------------------------|
| Modifies a function that computes a score, value, or result | Required |
| Modifies a "fast path" that also has a "full path" | Required |
| Modifies a shared utility function | Required (check all callers) |
| Adds a new modifier, bonus, or penalty | Required (find all paths that apply modifiers) |
| Modifies a single-item processor with a batch equivalent | Required |
| Adds a new field to a data structure | Required (check all read sites) |
| Fixes a display bug | Usually not required |
| Updates documentation | Not required |

### Anti-pattern: The "I Only Fixed One" Debrief

A debrief that reads *"Fixed the calculation in [function A]. Tests pass."* without mentioning parallel paths is the anti-pattern. The builder may have legitimately checked and found no parallel paths — but the debrief must say so:

> *"Searched for parallel implementations of [logic]. Found none. Only [function A] implements this calculation."*

This one-sentence confirmation closes the audit gap without requiring parity work when there's nothing to verify.

## Why This Is Hard to Detect Without the Pattern

Unit tests don't catch parallel path drift. They test the paths they cover. If a test covers path A and another test covers path B, and both tests pass, the tests say nothing about whether A and B produce the same result. The divergence is invisible until a cross-path integration test, a systematic audit, or a production incident surfaces it.

Parallel path drift is a **consistency failure that hides behind correct per-path tests.** The only prevention is explicitly tracking which paths are parallel, which is a process intervention, not a testing intervention.

## When to Use

- Any project where the same logical operation has more than one implementation
- Any project where code has a "simple" and "complex" version of the same function
- Any project that has grown incrementally (every large project eventually has parallel paths)

## Real Example

A project's result calculation had a "single-item" resolver and a "batch" resolver. The single-item resolver was the original implementation. The batch resolver was added later to support a new feature — it reproduced the calculation logic independently rather than delegating.

Over 30+ work orders, every WO that improved the calculation targeted the single-item resolver. The batch resolver drifted. A systematic audit eventually found that 21 independent calculation components had diverged between the two paths. None of the individual WOs were wrong — no one knew to look at the batch path.

**Fix:** Added a "Parallel Implementation Paths" section to every dispatch template targeting calculation functions. The batch resolver was refactored to delegate to the single-item resolver, eliminating the divergence permanently.



================================================
FILE: patterns/PLAIN_ENGLISH_PASS.md
================================================
# Pattern: Plain English Pass

## Problem

The PM Context Compression pattern compresses technical detail into 7-item summaries. This helps — but it compresses without translating. A summary line like "RNGProvider + RandomStream Protocols extracted to `rng_protocol.py`, 19 files updated, zero regressions" is shorter than the full debrief, but it still requires technical literacy to understand what happened and why it matters.

For non-technical operators coordinating agent fleets, this is a barrier. The operator needs to understand:
- What the team is building and why
- Whether the work matters for the product's goals
- What went wrong and what it means for the next cycle

None of these require understanding Protocols, type annotations, or pipeline positions. But the current debrief format only speaks in those terms.

## Solution

Add a **Plain English Pass** to every agent-to-human communication. Before the technical dump, the agent answers three questions in non-technical language:

### The Three Questions

**1. What problem did this solve?**
Describe the problem as a user or operator would experience it. No code references, no schema names, no rule IDs.

> "The game's dice roller was wired directly into every part of the combat engine. If we ever wanted to test combat with predictable dice (for debugging or replay), we'd have to rewrite every file that rolls dice."

**2. What does it actually do?**
Describe the mechanism in everyday terms. Imagine explaining it to someone who doesn't program.

> "We created a standard 'dice rolling interface' — a contract that says 'anything that can roll dice works here.' Then we updated every part of the combat engine to ask for 'something that rolls dice' instead of asking for the specific dice roller. Now you can swap in a test roller, a replay roller, or any future roller without touching the combat code."

**3. Why should anyone care?**
Describe the user-facing or project-level impact. What's different now? What's possible that wasn't before?

> "Testing and replaying combat is now possible without modifying the combat engine. Future features like deterministic replay and combat simulation can plug in without touching existing code."

### Word Budget

The Plain English Pass has a hard cap: **150 words total** across all three questions. This forces genuine compression — the agent can't write a technical explanation and call it "plain english." If you need more than 150 words, you're including jargon.

## The Four-Pass Debrief

With the Plain English Pass, the debrief becomes a four-pass structure:

```
Pass 0: Plain English      — 150 words, non-technical, operator reads this
Pass 1: Full Context Dump  — everything, agent-readable archive
Pass 2: PM Summary         — 7 items max, compressed for PM bandwidth
Pass 3: Retrospective      — what went well, what didn't, operational judgment
```

**Who reads what:**
- The **operator** reads Pass 0 and skims Pass 2 action items
- The **PM** reads Pass 2 and digs into Pass 1 when needed
- **Future agents** read Pass 1 for full context
- **Auditors** read Pass 1 and Pass 3 for integrity verification

## Implementation

### Debrief Template Addition

Add this section at the top of every debrief, before the technical content:

```markdown
## Plain English Summary

**What problem did this solve?**
[1-2 sentences. No jargon. Describe the problem as a user would experience it.]

**What does it actually do?**
[1-2 sentences. No jargon. Describe the mechanism in everyday language.]

**Why should anyone care?**
[1-2 sentences. Describe the impact — what's different now, what's possible that wasn't.]
```

### Quality Check

The Plain English Pass fails if:
- It contains class names, function names, or file paths
- It references rule IDs (RV-001, CT-003, BL-017)
- It uses programming terms (Protocol, dataclass, schema, refactor, type annotation)
- It exceeds 150 words
- A non-programmer couldn't understand it

### Worked Examples

**WO-RNG-PROTOCOL-001 (RNG Protocol Extraction):**

> **What problem did this solve?**
> The game's dice roller was hardwired into every combat calculation. Testing with predictable dice or replaying past combats required modifying the combat engine itself.
>
> **What does it actually do?**
> Created a standard "dice rolling contract" and updated every combat calculation to use the contract instead of the specific dice roller. Any dice roller that follows the contract now works everywhere.
>
> **Why should anyone care?**
> Deterministic testing and combat replay are now possible without touching the combat engine. Future dice-related features plug in cleanly.

(62 words)

**WO-ROADMAP-AUDIT (H1 Gap Analysis):**

> **What problem did this solve?**
> The project has a roadmap and a batch of work orders, but nobody had checked whether the work orders actually cover what the roadmap says should be built — or whether research findings imply work that nobody has planned yet.
>
> **What does it actually do?**
> Cross-referenced every planned work order against the roadmap and the research findings. Found 3 pieces of missing work, 2 items that should be promoted to higher priority, and 1 work order whose scope needs verification.
>
> **Why should anyone care?**
> Without this check, two quality rules would ship that can never actually detect errors (they check a field that's always empty), and a critical data pipeline would remain disconnected.

(117 words)

## When to Use

- Every debrief (mandatory)
- Every session memo that reaches the operator
- Handoff documents when the next session's operator (not just the next agent) needs to understand context
- Project status updates, roadmap summaries, and any artifact that crosses the technical/non-technical boundary

## When NOT to Use

- Agent-to-agent dispatches (builders don't need plain english — they need precise technical specs)
- Internal working notes
- Research memos (the PM translates these; the researcher writes for a technical audience)

## Anti-Patterns

- **Jargon in disguise.** "Extracted a protocol for dependency injection" is not plain english. "Created a standard contract so parts can be swapped" is.
- **Skipping it because it's "obvious."** Obvious to whom? The builder knows what they did. The operator doesn't. The 150-word pass takes 2 minutes to write and saves 20 minutes of operator confusion.
- **Writing the plain english pass last.** It should be written first — while the agent still has the high-level picture in mind. Writing it after the technical dump tends to produce a summary of the dump rather than a genuine translation.
- **Exceeding the word budget.** 150 words is a constraint, not a guideline. If you need more, you're including technical detail that belongs in Pass 1 or Pass 2.



================================================
FILE: patterns/PM_CONTEXT_COMPRESSION.md
================================================
# PM Context Compression

## Problem

The human coordinator (PM) has the smallest context window in the system. An agent can read 200K tokens per session. A human scanning files between meetings might read 2K-5K tokens before context fatigue sets in. Every agent produces output. The PM must consume enough output to make good decisions without drowning in detail.

If agents produce verbose reports, the PM skips them. If agents produce terse summaries, the PM misses critical details. Both failure modes lead to bad decisions — either from information overload or information starvation.

## Solution

**Two-pass writing.** Every agent-to-PM communication follows the same structure: full dump first (for the agent's own completeness), then compressed summary (for the PM's bandwidth).

### The Two-Pass Protocol

**Pass 1: Full Debrief (agent reads, PM doesn't)**

The agent writes everything it knows — complete findings, full reasoning, all edge cases, raw data. This document is the artifact of record. If a future agent needs the details, they're here.

**Pass 2: PM Summary (PM reads)**

The agent re-reads its own debrief and compresses it to the minimum the PM needs to make decisions. Rules:

- **7 items maximum.** If you have more than 7 findings, prioritize.
- **One line per item.** Description + action needed. No background, no reasoning.
- **Action items first.** Things the PM must decide or approve go at the top.
- **Status items second.** Things the PM should know but doesn't need to act on.
- **Deferred items last.** Things that can wait.

### PM Briefing Structure

```markdown
## Requires PM Action
1. [Item] — [what PM must decide]
2. [Item] — [what PM must approve]

## Status (Informational)
3. [Item] — [what happened]
4. [Item] — [what changed]

## Deferred
5. [Item] — [can wait until X]
```

### Implementation

**Rolling briefing file.** Instead of the PM reading 23 individual files, maintain a single `PM_BRIEFING_CURRENT.md` that every agent updates when they add files. The PM reads one file, gets the full picture, and digs into specific documents only when needed.

**Session memo template.** Standardize the PM-facing output so every session produces the same structure. The PM learns the format once and can scan it in seconds.

## When to Use

- Every session that produces findings, status changes, or action items for the PM
- When an agent discovers something the PM needs to know about
- At the end of every work session (debrief protocol)

## When NOT to Use

- Agent-to-agent communication (use full-detail dispatches — agents have the context budget)
- Internal working notes (keep in session, don't surface to PM unless relevant)

## Real Example

A builder agent completed 12 fix work orders in a session. The full debrief covered: which agents failed silently (3/7), which WOs needed reclassification, schema additions to ActiveSpellEffect, gold master regeneration, test assertion updates, and a cascade analysis of WO-FIX-03.

The PM summary was 7 lines:

```
1. WO-FIX-11: RETIRE. Action cost table doesn't exist as described.
2. BUG-F2/F3: UNVERIFIED. Desk check leveling.py:291-308.
3. Agent failure rate: 3/7. Gate needed: git diff before accepting.
4. WO-FIX-03 cascade: WO missed conditions.py aggregation file.
5. ActiveSpellEffect gained spell_level field.
6. Gold masters regenerated (4 files) — expected.
7. NEW PROCESS: Builder writes full debrief, then compresses for PM.
```

The PM read 7 lines. The full debrief exists if anyone needs the details later.

## Anti-Patterns

- **Sending the full debrief to the PM** — they won't read it. They'll skim, miss action items, and make decisions on incomplete information.
- **Writing only the summary** — the details are lost. A future agent can't reconstruct what happened from 7 lines.
- **Mixing action items with status updates** — the PM needs to know "what do I need to do?" separately from "what happened?" If they're interleaved, action items get missed.
- **Assuming the PM will read the files you reference** — they might not. The summary must be self-contained enough to act on without reading anything else.



================================================
FILE: patterns/POST_DEBRIEF_RETROSPECTIVE.md
================================================
# Pattern: Post-Debrief Retrospective

## Problem

The formal debrief format — what was changed, what tests pass, what was found — is oriented toward delivery. It answers the question: *"Did the builder do what the WO said?"*

That's the right question for the delivery record. But it's the wrong question for surfacing what the builder noticed that wasn't in scope.

**Builders are uniquely positioned to see things nobody else can see.** They're inside the code with full context for the specific subsystem they worked on. They see the seams between their WO and adjacent code. They notice coupling risks, naming drift, patterns that are about to repeat, corners that look like they're about to cause a problem.

None of this fits naturally into the three-pass debrief format. The debrief is about delivery. The builder's peripheral observations aren't about delivery — they're about what's coming.

**The failure mode:** The builder completes the WO, writes an accurate debrief, and closes the session. Two sessions later, a related WO runs into the coupling risk the previous builder noticed but didn't mention. The risk was real, observable, and available — but it lived in the builder's context window and died when the session ended.

## Solution

### Rule

**After every accepted debrief, ask the builder: "Anything else you noticed outside the debrief?"**

This question is mandatory. It is not optional follow-up. It doesn't depend on whether the builder seems to have more to say. The question changes what the builder thinks about — it activates a different lens than the delivery-focused debrief.

The question fires after the formal debrief is filed and reviewed, not during. The timing matters: during delivery, the builder is focused on delivery. After the formal record is complete and the pressure is off, peripheral observations become accessible.

### What This Question Surfaces

| Category | Example |
|----------|---------|
| Coupling risks | "That shared utility function is called from 6 other places — if it changes shape, they all break" |
| Naming drift | "There are two functions with similar names that do different things — this is going to confuse the next builder" |
| Silent gaps | "The error case is handled, but the warning case returns quietly with no log entry" |
| Structural risks | "The test passes but it's testing against a hardcoded fixture that will be wrong if the schema changes" |
| Upcoming collision | "The next WO in the queue is going to hit a conflict with what I just changed — worth flagging" |
| Observations outside scope | "I noticed while reading the surrounding code that [X] seems incorrect — didn't touch it, but worth knowing" |

### Filing Findings

Any signal that emerges from this question gets filed immediately as a FINDING:

```markdown
FINDING-[SUBSYSTEM]-[SEQUENCE]-001
Severity: LOW | MEDIUM | HIGH
Source: Post-debrief retrospective — WO-[ID]
Summary: [One sentence]
Detail: [What the builder observed]
Recommended action: [Queue for PM triage | Investigate before next batch | Block next dispatch]
```

The finding is filed before the session closes. Not "noted for later." Not "mentioned in the debrief." Filed as a finding that the PM will see and triage.

### PM Enforcement

The PM must ask this question after every debrief acceptance. The PM does not ask "is there anything else?" in a way that signals the right answer is "no." The question is active and specific:

*"Anything else you noticed outside the debrief? Coupling risks, naming drift, anything that caught your eye while you were in there?"*

The specificity matters. "Anything else?" reads as "are we done?" "Anything else you noticed... coupling risks, naming drift..." reads as "I'm genuinely asking for peripheral observations."

If the builder has nothing: record "Post-debrief retrospective: no additional findings." One line. The record shows the question was asked.

### Relationship to the Three-Pass Debrief

The three-pass debrief has a Pass 3 retrospective. The post-debrief question is **separate** from that retrospective, not a repeat of it.

- **Pass 3 retrospective:** Covers what happened during the WO — drift caught, patterns used, lessons for next time. Oriented toward *this* session.
- **Post-debrief question:** Covers what the builder noticed that has nothing to do with this WO. Oriented toward *future* sessions and adjacent risks.

Both are required. Pass 3 doesn't substitute for the question; the question doesn't substitute for Pass 3.

## Implementation

### When to Ask

| Timing | When | Notes |
|--------|------|-------|
| **After debrief review, before closing the session** | PM reads the debrief, confirms it's acceptable, then asks | Timing ensures the builder is still in context |
| **Not during implementation** | Never ask mid-session | Splits builder focus |
| **Not before the debrief** | Asking "anything to add?" before Pass 3 is written conflates the two |

### How to Record

Add a section to the PM's session record:

```markdown
## Post-Debrief Retrospective — WO-[ID]

Asked: [date]
Builder response:
- [Finding 1 — filed as FINDING-...]
- [Finding 2 — filed as FINDING-...]
- No additional findings
```

### Integration with Findings Triage

Findings from post-debrief retrospectives enter the same triage queue as findings from audits and other sources. The PM triages them at the next queue review. They have equal standing with audit findings — they came from a different observation angle but they're just as valid.

## When to Use

- After every accepted builder debrief
- No exceptions for "short" WOs or "routine" fixes
- Even when the builder's debrief is comprehensive and seems complete

## When NOT to Use

- During the WO (don't interrupt delivery with scope-expansion questions)
- As a substitute for an audit (this catches peripheral builder observations, not systematic subsystem analysis)

## Anti-Patterns

- **Asking "are we done?"** — That's not the question. The question is "did you notice anything?"
- **Accepting "no" too quickly** — A gentle follow-up is fine: "Nothing about the surrounding code? Any naming that looked off?"
- **Not filing the findings** — "I'll remember it for next time" is not filing. If it's real, it gets a FINDING entry today.
- **Batching up findings** — File before closing the session. Findings that aren't filed in the session often don't get filed at all.

## Real Example

A builder completing a work order on a skill modifier system noticed — while reading the code to understand the surrounding context — that a utility function used by multiple callers had two different parameter ordering conventions. The debrief covered only the WO scope. The peripheral observation wasn't formally part of the WO.

The post-debrief question surfaced it. The builder described: *"The skill name normalization function has two call signatures in different parts of the codebase — one passes skill name first, the other passes it second. I didn't touch it but it looks like a latent bug waiting to trigger."*

That observation was filed as a FINDING. Two batches later, a different WO was dispatched to normalize the call signature and add a test that would have failed against the bad ordering. The bug never reached production.

**Without the question:** The observation would have died in the session context window.
**With the question:** It became a filed finding, a dispatched WO, and a prevented regression.



================================================
FILE: patterns/PROACTIVE_ASSUMPTION_SWEEP_CADENCE.md
================================================
# Pattern: Proactive Assumption Sweep Cadence

## Problem

The [Hidden Assumption Sweep](HIDDEN_ASSUMPTION_SWEEP.md) is a powerful triage tool — but it is reactive by design. You run it when a question "feels larger than it should." The problem: many hidden assumptions don't produce that feeling. They feel settled. They feel like known ground. They surface quietly as production failures weeks later.

The reactive trigger misses the class of assumptions that are confidently wrong.

**The failure pattern:**
- A subsystem is built across 5 batches
- Each WO is scoped correctly, tested correctly, and accepted
- Nobody runs an assumption sweep because nothing triggered one
- At batch 8, a builder questions whether a boundary condition was ever explicitly specified
- It wasn't — it was assumed from context by the first builder, inherited by all subsequent builders, and the assumption is wrong
- The correction requires touching 4 resolvers and 12 tests

**Root cause:** Hidden assumptions compound silently. The cost of catching them grows with the number of layers built on top of them. A reactive sweep catches the assumption at trigger time — but trigger time is often well after the assumption has already been load-bearing for multiple batches.

---

## Solution

### Rule

**Run a proactive Hidden Assumption Sweep on a fixed cadence — not just when triggered.**

Pair the sweep with your existing sweep audit cadence (every N batches, or at each batch boundary). The sweep is brief: 10 questions, 3-10 minutes, one artifact filed regardless of outcome. The goal is not to find problems — it is to confirm that what you think is settled actually is.

### Cadence

| Trigger | Sweep Type | Who Runs It |
|---------|-----------|-------------|
| Every 5 engine batches | Proactive subsystem sweep | PM, paired with the sweep audit |
| After any cross-cutting change | Full boundary sweep | PM |
| After a new spec or design document is added | Scope sweep | PM |
| When a builder WO is rejected for spec ambiguity | Targeted sweep on the ambiguous assumption | PM |
| When a test passes but behavior "feels wrong" | Targeted sweep on the assumption the test is validating | Auditor |

The proactive sweep pairs with the Sweep Audit Protocol — when you schedule a read-only subsystem audit, you also run the 10-question sweep on that subsystem's key assumptions before the audit is dispatched. This way, assumption gaps are caught before new code is written against them.

### The 10-Question Sweep (Quick Reference)

Answer each question YES / NO / UNKNOWN for the subsystem being reviewed.

1. **Is there a missing assumption here, or just a missing feature?** (Assumptions are more dangerous — they affect everything built on top of them)
2. **Does any open WO or milestone change meaning if this assumption is wrong?**
3. **Does this touch a system boundary?** (Between subsystems, between system and users, between two resolvers that hand off to each other)
4. **Does the system currently fail closed (silent, safe) or fail open (inventing answers) at this point?**
5. **Does it require a human judgment layer that the source documentation never explicitly defines?**
6. **Does it affect multiple subsystems, or just one?**
7. **Can a user or adversary expose this gap through normal, reasonable behavior?**
8. **Is there an observable failure mode, or is this a silent failure?**
9. **Who is authorized to make the ruling if the system cannot?**
10. **What state must the system track for any ruling here to be meaningful?** (If the required state is not tracked, flag as a world-model gap)

### Escalation Rule

**Escalate to STRATEGY (not WO) if:**
- 3 or more answers are UNKNOWN, **or**
- any answer changes the definition of done for anything in progress, **or**
- any boundary is found to be fail-open

When in doubt, escalate. Filing a strategy item that turns out to be minor costs nothing. Building 3 more batches on a wrong assumption costs everything.

---

## Output Format

Every sweep produces a short artifact filed immediately — not noted for later:

```markdown
**Sweep ID:** SWEEP-[SUBSYSTEM]-[NNN]
**Date:** [YYYY-MM-DD]
**Subsystem:** [subsystem name]
**Trigger:** [Cadence (every N batches) | Cross-cutting change | WO rejection | Manual]
**Conducted by:** [PM / Auditor]

**Question answers:**
1. YES / NO / UNKNOWN — [one sentence]
2. YES / NO / UNKNOWN — [one sentence]
... (all 10 questions)

**Unknown count:** N

**Classification:**
- [ ] No issues — all assumptions confirmed, proceed
- [ ] STRATEGY item filed — [one sentence describing the gap]
- [ ] WO filed — [one sentence describing the scoped fix]
- [ ] Deferred — [one sentence rationale]
```

File it in the PM inbox or the project's findings log. Use lifecycle `NEW` if it requires action, `ARCHIVE` if the result is clean.

---

## Subsystem Rotation

Run sweeps in the same rotation as your audit cadence. Don't sweep the same subsystem twice in a row. Maintain a sweep log:

| Batch | Subsystem | Sweep ID | Result |
|-------|-----------|----------|--------|
| 5 | Attack resolution | SWEEP-ATTACK-001 | Clean |
| 10 | Condition stack | SWEEP-CONDITIONS-001 | STRATEGY filed |
| 15 | Spellcasting | SWEEP-SPELLS-001 | Clean |
| 20 | Action economy | SWEEP-ACTION-001 | WO filed |

The rotation ensures every major subsystem is reviewed before 3 full cycles pass. Subsystems with prior strategy items get earlier re-sweeps.

---

## Integration with Other Patterns

| Pattern | Integration |
|---------|-------------|
| [Hidden Assumption Sweep](HIDDEN_ASSUMPTION_SWEEP.md) | This pattern sets the cadence; that pattern provides the sweep protocol |
| [Sweep Audit Protocol](SWEEP_AUDIT_PROTOCOL.md) | Pair the assumption sweep with every audit dispatch — run sweep first, then dispatch auditor |
| [Research-to-Build Pipeline](RESEARCH_TO_BUILD_PIPELINE.md) | Assumption sweeps at the Brick stage surface judgment gaps before builders are dispatched |
| [Authority Tagging](AUTHORITY_TAGGING.md) | Question 5 (human judgment layer) frequently surfaces POLICY assumptions that need explicit tagging |

---

## Real Example

At batch 10 of the AIDM engine build, a proactive assumption sweep on the condition stack revealed that the question "what happens when two conditions with conflicting movement restrictions apply simultaneously?" had never been answered. The spec described each condition individually but never specified resolution order for conflicts.

The system's current behavior was fail-open: it applied whichever condition was processed last, silently. No test caught this because no test combined conflicting conditions.

**Without the proactive sweep:** The behavior would have continued silently. The gap would have been discovered when a player encountered a prone + paralyzed + slowed combination and the movement calculation produced an impossible value.

**With the proactive sweep:** The ambiguity was filed as a STRATEGY item. The operator made an explicit ruling (more restrictive condition wins). A builder WO formalized the priority table. The fix was one WO. Catching it after four more batches would have required touching seven.

---

## Anti-Patterns

- **Only running sweeps when triggered.** Assumptions that don't feel shaky are the most dangerous ones. The reactive trigger misses confidently-wrong assumptions.
- **Running the sweep without filing the output.** The sweep is only valuable as an artifact. A sweep run in conversation and forgotten is worth nothing.
- **Filing a WO for a 3+ UNKNOWN result.** That is a strategy item. A WO scoped against an unresolved assumption will make the assumption permanent.
- **Skipping the sweep when the batch feels clean.** "Nothing triggered" is not evidence that assumptions are correct. It is evidence that no trigger fired.
- **Sweeping the same subsystem repeatedly and skipping others.** Rotate. The rotation rule exists because the most dangerous assumptions are in the subsystems you stopped worrying about.

---

## When to Use

- Every N batches (pair with the sweep audit cadence)
- After any cross-cutting change (shared utility modified, central dispatcher changed)
- After a new spec or design document is added to the project
- When a builder WO is rejected because the spec was ambiguous

## When NOT to Use

- Instead of the Hidden Assumption Sweep reactive trigger — this pattern adds scheduled sweeps; it does not replace triggered ones
- For clearly scoped, local feature work with no cross-system implications
- Mid-sprint when momentum matters more than coverage — schedule for the batch boundary



================================================
FILE: patterns/RESEARCH_TO_BUILD_PIPELINE.md
================================================
# Pattern: Research-to-Build Pipeline

## Problem

A human operator has an insight: "We should add voice input to the system." This is valuable but not actionable. If you dispatch a builder WO that says "add voice input," you get scope bleed, rework, and wasted context windows — because the builder has to make dozens of design decisions that should have been resolved before they started coding.

The gap between "raw insight" and "executable work order" is larger than it appears. Insights contain ambiguity, unexplored alternatives, and implicit assumptions. Builders need binary specs — unambiguous instructions with all decisions pre-resolved. Something has to convert the first into the second.

## Solution

A staged pipeline that converts raw operator insight into builder-ready work orders through explicit research and normalization steps. Each stage has a defined input, output, and responsible role.

### The Pipeline

```
BURST (raw insight)
  → RESEARCH WO (scoped question)
    → FINDINGS MEMO (research output)
      → BRICK (normalized, decision-ready packet)
        → BUILDER WO (executable spec)
```

### Stage 1: Burst

**What it is:** A raw insight from the operator. Unstructured, potentially vague, possibly brilliant. Not yet actionable.

**Examples:**
- "Speech input should feel reliable, not experimental"
- "Players need to see the tactical grid before casting spells"
- "The workflow keeps stuttering at handoff points"

**Where it lives:** Intake queue (a parking lot file). Bursts are captured immediately so they aren't lost, but they don't enter the production pipeline until converted.

**Who owns it:** The operator generates it. The PM captures and parks it.

### Stage 2: Research WO

**What it is:** The PM converts the burst into a scoped research question and drafts a research WO for a researcher agent to execute.

**Key properties:**
- The research question is specific and bounded (not "figure out voice input" but "what is the cold start latency of the TTS engine and what are the options for reducing it?")
- The research WO references specific files, schemas, or systems to examine
- The expected output format is defined (findings memo with recommendations)

**Who owns it:** PM drafts, operator approves dispatch, researcher executes.

### Stage 3: Findings Memo

**What it is:** The researcher's output. Contains findings, analysis, alternatives considered, and prioritized recommendations.

**Key properties:**
- Written for the PM, not for builders
- May contain multiple approaches with tradeoffs
- May identify binary decisions the operator must resolve
- May recommend follow-up research

**Who owns it:** Researcher produces, PM consumes.

### Stage 4: Brick

**What it is:** The PM normalizes the research findings into a READY packet with four components:

1. **Target Lock:** One sentence describing the end state. ("Speech input becomes deterministic, confirm-gated, and measurable.")
2. **Binary Decisions:** Enumerated choices the operator must resolve before builder WOs can be drafted. Each decision has exactly two options with clearly stated tradeoffs.
3. **Contract Spec:** The technical specification derived from research, written as a reference document the builder WO will point to.
4. **Implementation Plan:** Ordered list of builder WOs with dependencies and parallel opportunities.

**Key properties:**
- A Brick is READY when all four components exist
- Binary decisions must be resolved by the operator before proceeding
- The implementation plan may contain 1 WO or 20 — the research determines the scope

**Who owns it:** PM produces, operator resolves binary decisions.

### Stage 5: Builder WO

**What it is:** A self-contained work order drafted from the Brick. The builder never sees the upstream research.

**Key properties:**
- References the contract spec (from the Brick), not the research memos
- All design decisions are pre-resolved — the builder executes, doesn't decide
- Follows the standard Dispatch Self-Containment pattern

**Who owns it:** PM drafts from Brick, operator approves dispatch, builder executes.

### Why Builders Never See Research

Research memos contain:
- Multiple approaches with tradeoffs (the builder shouldn't re-evaluate — the PM already chose)
- Rejected alternatives (reading about rejected approaches wastes builder context)
- Nuance and uncertainty (builders need certainty — "do X", not "X or Y depending on...")
- Technical exploration that doesn't map to implementation steps

The Brick is the firewall. The PM extracts what the builder needs and discards the rest. This isn't information hiding — it's context window optimization.

## WIP Limits

- **1-2 READY Bricks ahead of the builder queue.** Don't stockpile Bricks — they go stale as the codebase evolves.
- **Don't open new research until current Bricks are converted or deprioritized.** Research without downstream conversion is waste.
- **One burst at a time through the pipeline.** Parallel research is fine (different questions, different researchers). Parallel conversion of the same burst's findings is not (it creates conflicting Bricks).

## Implementation

### Intake Queue Format

```markdown
# Burst Intake Queue

## READY Bricks
### BURST-001: [Title] — READY BRICK
**Target Lock:** [one sentence]
**Binary Decisions:** [list, with resolution status]
**Contract Spec:** [link to spec document]
**Implementation Plan:** [list of planned WOs]

## Active Bursts
### BURST-002: [Title]
**Target Lock:** [one sentence]
**Status:** [NOT STARTED | RESEARCH IN PROGRESS | AWAITING NORMALIZATION]

## Completed Bursts
[Archived after all builder WOs ship]
```

### Pipeline Tracking

Each burst moves through visible stages:

```
BURST-001: "Voice reliability"
  Stage 1 (Burst):    CAPTURED     — 2026-02-10
  Stage 2 (Research):  COMPLETE     — 5 research WOs executed
  Stage 3 (Findings):  COMPLETE     — Playbook synthesized
  Stage 4 (Brick):     READY        — 5 binary decisions awaiting operator
  Stage 5 (Builder):   NOT STARTED  — 19 WOs planned, pending DC resolution
```

## When to Use

- Any feature or system change that involves design decisions (not just implementation)
- Any work that requires understanding tradeoffs before coding
- Any operator insight that spans multiple WOs
- When the operator says "we should..." or "what if we..." — that's a burst

## When NOT to Use

- Bug fixes with obvious solutions (skip straight to builder WO)
- Mechanical refactors where the approach is predetermined (e.g., "extract this class into a protocol")
- Single-file changes with no design ambiguity

## Real Example

**BURST-001: Voice-First Reliability Membrane**

The operator's insight: "Speech input should feel reliable, not experimental."

Pipeline execution:
1. **Burst captured** — parked in intake queue
2. **5 Research WOs drafted and executed:**
   - WO-VOICE-RESEARCH-01: Voice Control Plane Contract
   - WO-VOICE-RESEARCH-02: Failure Taxonomy & Unknown Policy
   - WO-VOICE-RESEARCH-03: Metrics & Telemetry Spec
   - WO-VOICE-RESEARCH-04: UX Turn-Taking & Confirmation
   - WO-VOICE-RESEARCH-05: Synthesis Playbook
3. **Findings normalized into Brick:**
   - Target Lock: "Speech input becomes deterministic, confirm-gated, and measurable"
   - 5 binary decisions identified for operator resolution
   - Contract spec: 547-line playbook covering control plane, failure policy, metrics, prosody
   - Implementation plan: 19 builder WOs across 5 tiers
4. **Binary decisions presented to operator** — awaiting resolution before builder WOs are drafted

Total research output: ~2,000 lines across 5 memos. Total builder input: self-contained WOs referencing a single contract spec. The builder never reads the 2,000 lines of research.

## Anti-Patterns

- **Skipping research and going straight to builder WOs.** Works for simple features. Produces rework for anything with design ambiguity. The research cost is paid either way — the question is whether you pay it in a focused research session or scattered across a builder session that keeps stopping to make design decisions.
- **Builders reading research memos.** Wastes context. The builder's job is to implement a spec, not to evaluate research. If the builder needs information from the research, it should be in the Brick or the WO.
- **PM stockpiling Bricks.** Bricks go stale as the codebase evolves. A Brick drafted from research done 2 weeks ago may reference code that's been refactored. Keep the pipeline short: research → Brick → build within the same project cycle.
- **Skipping binary decisions.** If the operator doesn't resolve the decisions, the PM guesses. PM guesses produce WOs that get reverted when the operator disagrees. The binary decision gate exists to prevent this.



================================================
FILE: patterns/ROLE_SEPARATION.md
================================================
# Pattern: Role Separation

## Problem

Without defined roles, agents assume they can do everything. A builder session that encounters a gap in the requirements starts researching instead of flagging the gap. A researcher who finds a bug starts fixing it instead of reporting it. An auditor who spots a missing WO starts drafting one instead of noting the gap in their memo.

This produces three failure modes:
1. **Scope bleed** (Coordination Failure Category 3) — agents modify files outside their declared scope
2. **Context waste** — agents spend context window on activities they're not optimized for (a builder doing research burns context that should go to code)
3. **Conflicting outputs** — two agents in different roles produce overlapping or contradictory artifacts because neither knew the other's scope

The root cause is that LLM agents are generalists by default. They'll do whatever seems helpful unless explicitly constrained. Role definitions are those constraints.

## Solution

Define distinct roles with explicit authorities, boundaries, and output formats. Each agent session operates under exactly one role. The role determines what the agent can read, write, and produce.

### The Five Roles

#### 1. Operator (Product Owner)

The only human in the loop. Sets direction, resolves binary decisions, approves dispatches.

| Authority | Boundary |
|-----------|----------|
| Dispatch authority — no WO executes without operator approval | Does not write code |
| Binary decision resolution — DC-01 through DC-N | Does not execute research |
| Priority setting — which WO ships next | Does not draft WOs (PM does) |
| Role assignment — which agent type handles which WO | Does not read full debriefs (reads PM summaries) |

**Key constraint:** The operator is bandwidth-limited. Every artifact that reaches the operator must be compressed to match their available attention. This is why the PM role exists.

#### 2. PM (Project Manager)

The coordination layer. Translates operator intent into agent-executable artifacts. Maintains project state.

| Authority | Boundary |
|-----------|----------|
| Drafts all WOs (research, builder, audit) | Does not execute research (researcher does) |
| Normalizes research into Bricks | Does not write production code (builder does) |
| Maintains briefing, kernel, inbox | Does not audit artifacts (auditor does) |
| Triages and prioritizes incoming artifacts | Does not make binary decisions (operator does) |
| Context compression — translates technical output for operator | Does not dispatch without operator approval |

**Key constraint:** The PM is the bottleneck between research and build. If the PM doesn't normalize a finding into a Brick, it doesn't become a WO. This is by design — it prevents raw research from reaching builders.

#### 3. Builder

Executes builder WOs. Writes code, writes tests, produces debriefs.

| Authority | Boundary |
|-----------|----------|
| Modifies files listed in the WO scope | Does not modify files outside WO scope |
| Runs tests, regenerates fixtures | Does not draft new WOs |
| Writes debrief documenting what was done | Does not perform research |
| Reports mid-session discoveries to PM via debrief | Does not modify governance documents (unless WO explicitly says so) |

**Key constraint:** Builders receive self-contained WOs and produce self-contained debriefs. They never see upstream research, previous session history, or the PM's decision rationale. This is intentional — builders need binary specs, not decision trees.

#### 4. Researcher

Executes research WOs. Reads codebase, reads documentation, reads external sources, produces findings memos.

| Authority | Boundary |
|-----------|----------|
| Reads any file in the codebase | Does not write production code |
| Reads external documentation and specs | Does not draft builder WOs |
| Produces research memos with findings and recommendations | Does not modify existing code |
| May propose schema designs or algorithms in the memo | Does not implement those proposals |

**Key constraint:** Research output is raw material, not finished product. The PM converts research findings into actionable Bricks. Researchers never interact directly with builders.

#### 5. Auditor

Cross-references artifacts against each other. Produces gap analyses, consistency checks, roadmap audits.

| Authority | Boundary |
|-----------|----------|
| Reads all project artifacts (WOs, debriefs, research, code, governance) | Does not modify any file except their output memo |
| Produces audit memos identifying gaps, conflicts, and misalignments | Does not draft WOs (PM does, based on audit findings) |
| May recommend promotions (H2 → H1) or demotions | Does not make prioritization decisions (operator does) |
| Cross-checks debrief claims against diffs and test output | Does not re-execute or modify work |

**Key constraint:** Auditors are read-only except for their output artifact. This prevents the audit from becoming a fix session — the auditor identifies the problem, the PM drafts the fix WO, the builder implements it.

### The Relay Pattern

```
Operator Intent
    → PM drafts Research WO
        → Researcher executes, produces findings memo
            → PM normalizes findings into READY Brick
                → PM drafts Builder WO from Brick
                    → Builder implements, produces debrief
                        → PM compresses debrief for Operator
```

Each handoff is a file. Each file is self-contained. No role depends on conversational context from another role's session.

## Implementation

### Role Declaration in Dispatches

Every WO dispatch includes a role assignment:

```markdown
**Assigned to:** Builder (Opus 4.6)
**Role constraints:** Builder role — modify only files listed in scope, produce debrief on completion
```

Every session memo includes the role:

```markdown
**From:** Auditor (Opus 4.6)
**Role:** Auditor — read-only except output memo
```

### Role Boundary Enforcement

| Enforcement Tier | Mechanism |
|-----------------|-----------|
| Tier 1 (test) | `git diff --stat` post-session — verify only scoped files were touched |
| Tier 2 (process) | WO template includes "Scope Boundaries" and "What NOT to Do" sections |
| Tier 3 (prose) | Role description in onboarding checklist |

### When Roles Need to Cross Boundaries

Sometimes a builder discovers a bug outside their WO scope. Sometimes a researcher finds code that's trivially fixable. The protocol:

1. **Do not cross the boundary.** Note the finding in the debrief or memo.
2. **The PM triages the finding.** If it warrants action, the PM drafts a new WO.
3. **A new session handles it** under the appropriate role.

This feels slow. It prevents scope bleed, parallel collisions, and the coordination failures that cost more time than the extra session.

## When to Use

- Any project with 3+ agent sessions
- Any project where parallel dispatch is planned (role separation is what makes parallel safe)
- Any project where the human coordinator is non-technical (role separation keeps technical complexity inside agent sessions, with only compressed output reaching the human)

## When NOT to Use

- Single-agent projects with one human developer (the human is all roles simultaneously)
- Quick one-off tasks where the overhead of role declaration exceeds the work

## Real Example

The D&D 3.5e project runs all five roles. In a single cycle:
- The **operator** approved 7 dispatch-ready WOs and resolved 3 binary decisions
- The **PM** drafted those 7 WOs from research Bricks, maintained the briefing file, and compressed 12 debriefs into 7-item summaries
- **Builders** executed WOs (RNG protocol extraction, TTS chunking, weapon plumbing, etc.) and produced debriefs
- A **researcher** executed 11 research WOs (RQ-SPRINT-001 through 011) producing findings memos
- An **auditor** cross-referenced the dispatch queue against the roadmap and produced a gap analysis memo

No role touched another role's artifacts. The PM was the only node that read from all roles and wrote dispatches for all roles.

## Anti-Patterns

- **Letting builders research.** A builder who starts reading research docs to "understand context" is burning build-optimized context on research. The WO should contain all needed context.
- **Letting researchers fix bugs.** A researcher who modifies code to "verify their finding" has crossed into builder territory. The fix may conflict with in-flight builder work.
- **Skipping the PM.** Direct operator-to-builder dispatch works for simple tasks but breaks down when the builder needs context the operator can't provide. The PM's value is translating intent into spec.
- **Auditors who draft WOs.** The auditor identifies the gap. The PM decides whether and how to fill it. Combining these roles means the audit is biased toward gaps the auditor knows how to fix, not gaps that matter most.



================================================
FILE: patterns/SESSION_BOOTSTRAP.md
================================================
# Session Bootstrap

## Problem

An agent starts a new session and reads the project's documentation to orient itself. The documentation says there are 5,100 tests. The agent proceeds on that assumption. But 3 tests were broken by last session's changes, and nobody updated the docs. The agent now has a false foundation — and every decision it makes from here may be wrong.

Prose documents are always potentially stale. The gap between "what the docs say" and "what the code actually does" widens with every session that touches code but doesn't update docs. Agents can't tell the difference between current truth and stale truth when both are written in the same authoritative tone.

## Solution

**Start every session with machine-verified truth.** Before reading any prose document, run commands that produce canonical facts about the project's current state.

### Bootstrap Sequence

```bash
# 1. What branch, what's changed, what's committed?
git status
git log --oneline -5

# 2. Do the tests pass? How many?
python -m pytest tests/ -q --tb=no 2>&1 | tail -3

# 3. What files were touched recently?
git diff --stat HEAD~5
```

This takes 30 seconds and produces ground truth that no prose document can override.

### Implementation

**Option A: Manual bootstrap (Tier 3)**

Add to the onboarding checklist: "Before reading any docs, run these 3 commands and report the output."

**Option B: Bootstrap script (Tier 1.5)**

```bash
#!/bin/bash
# scripts/session_bootstrap.sh
echo "=== SESSION BOOTSTRAP ==="
echo "--- Branch & Status ---"
git status --short
echo "--- Recent Commits ---"
git log --oneline -5
echo "--- Test Health ---"
python -m pytest tests/ -q --tb=no 2>&1 | tail -3
echo "--- Uncommitted Changes ---"
git diff --stat
echo "=== END BOOTSTRAP ==="
```

The agent runs this first, then reads prose documents with the machine truth as a reference frame.

**Option C: Auto-generated state file (Tier 1)**

A CI step or pre-session hook generates `PROJECT_STATE_MACHINE.md` from actual project state. Agents read this file instead of manually-maintained state documents. The file is always regenerated, never edited by hand.

## When to Use

- Every new agent session, without exception
- After pulling changes from a remote
- After another agent's session ends and before the next begins
- When an agent reports something that contradicts what you expect (re-bootstrap to check)

## When NOT to Use

- Mid-session for routine work (the bootstrap established truth at session start; re-running mid-session wastes context)
- As a substitute for reading project documentation (bootstrap establishes facts; docs explain architecture and intent)

## Real Example

The D&D 3.5e project's `PROJECT_STATE_DIGEST.md` claimed 303 formulas verified. After Domain A re-verification and Domain I expansion, the actual count was 338. An agent reading the PSD would operate on stale numbers. A session bootstrap running `grep -c "FORMULA:" docs/verification/DOMAIN_*` would produce the correct count immediately.

## Anti-Patterns

- **Trusting test count from a document** — run `pytest` and count the output. Documents lie by omission (they don't update themselves).
- **Skipping bootstrap because "I just read the docs"** — the docs were written by a previous agent that may have had stale information itself. The staleness compounds.
- **Running bootstrap but not reporting it** — the bootstrap output should be the first thing in the agent's response, so the human coordinator can verify it matches expectations.



================================================
FILE: patterns/STAGED_CONTEXT_LOADING.md
================================================
# Pattern: Staged Context Loading

## Problem

LLM agents have finite context windows. When dropped into a complex project, they waste context by:
- Reading every file they can find (context exhaustion)
- Reading files in the wrong order (building understanding on unstable foundations)
- Reading stale or superseded documents (poisoning their mental model)
- Not knowing which documents exist (missing critical governance)

Result: agents start working with incomplete or incorrect understanding, producing work that has to be reverted.

## Solution

Define an explicit reading sequence that loads context in layers, from broad orientation to specific operational detail.

### The Layers

```
Layer 1: ORIENTATION
    "What is this project? What are we building?"
    → Single entry-point document (Compass/README)
    → Architecture overview, current phase, what's real vs planned

Layer 2: STATE
    "What's been done? What's the current situation?"
    → Operational state document (test counts, locked systems, active work)
    → Capability gates (what's allowed, what's blocked)

Layer 3: RULES
    "How do I work on this project?"
    → Coding standards, pitfall avoidance
    → Communication protocols, escalation procedures
    → Known tech debt (what NOT to touch)

Layer 4: TASK
    "What specifically am I doing?"
    → Work order / dispatch document
    → Referenced files specific to the task
```

### Why Order Matters

An agent that reads coding standards (Layer 3) before understanding the architecture (Layer 1) will apply rules without context. An agent that reads a work order (Layer 4) before understanding project state (Layer 2) will make assumptions that conflict with reality.

The sequence builds understanding in dependency order: you need to know what the project is before you can understand its state, you need to understand its state before its rules make sense, and you need all three before a specific task is meaningful.

## Implementation

Create a **mandatory reading checklist** as a root-level file. Format:

```markdown
# Agent Onboarding Checklist

**Read this file FIRST. Follow it step by step.**

## Step 1: Read the Governance Documents (IN THIS ORDER)

| Order | File | Purpose |
|-------|------|---------|
| 1 | `PROJECT_COMPASS.md` | Orientation — architecture, status, what's real |
| 2 | `PROJECT_STATE.md` | State — operational detail, what's done, what's active |
| 3 | `DEVELOPMENT_GUIDELINES.md` | Rules — coding standards, pitfalls |
| 4 | `COMMUNICATION_PROTOCOL.md` | Rules — how to flag concerns |
| 5 | `KNOWN_TECH_DEBT.md` | Rules — what not to touch |

## Step 2: Verify the Project Compiles
[Machine verification before any work begins]

## Step 3: Begin Your Task
[Now read the specific work order]
```

### Key Design Decisions

- **Numbered order is mandatory**, not suggested. Agents will skip ahead if given the option.
- **The checklist itself is the entry point.** It's the first file any agent reads, and it tells them exactly what to read next.
- **Keep Layer 1 to a single file.** Multiple orientation documents cause agents to piece together a mental model from fragments. One file, comprehensive, is better than three files that each cover part of the picture.
- **Machine verification (Step 2) comes before task-specific reading.** This grounds the agent in executable truth before they consume prose that might be stale.

## When to Use

- Any project with more than 3 governance/documentation files
- Any project where multiple agents will work across different sessions
- Any project where agent context windows are a binding constraint

## Real Example

The proving-ground project has 7+ root-level governance documents. Without the checklist, agents would read them in arbitrary order, often starting with the most recently modified file (which was frequently a work order, not orientation). After introducing the staged loading pattern:
- Agents oriented correctly on first try
- No more "I assumed X was the architecture" mistakes
- Context window waste dropped significantly — agents read what they need, in order

## Anti-Patterns

- **Dumping everything into a system prompt.** This uses context before the agent even starts working. Staged loading lets agents load context incrementally, spending budget on the layers relevant to their task.
- **Single giant README.** Orientation and operational state change at different rates. A 500-line README that mixes "what we're building" with "what's currently broken" becomes stale in the volatile sections while remaining correct in the stable sections. Separate layers, separate files, separate update frequencies.
- **No reading order, just "read the docs."** Agents will read in whatever order they discover files. Without an explicit sequence, the mental model they build is random.



================================================
FILE: patterns/SWEEP_AUDIT_PROTOCOL.md
================================================
# Pattern: Sweep Audit Protocol

## Problem

Iterative development with many small work orders has a structural blind spot: **each WO fixes the problem it was written for, but no single WO sees the system as a whole.**

A builder executing WO-47 fixes one calculation. A builder executing WO-51 fixes another. Each debrief is correct. Each gate test passes. But no one has looked at whether the calculation in WO-47 and the calculation in WO-51 use consistent logic across the same code path. No one has looked at whether 30 sequential WOs have drifted from the original specification. No one has looked at whether the sum of correct individual fixes has produced a coherent whole.

**The damage accumulates invisibly.** Individual WOs can all be correct while the system-as-a-whole has diverged from what it's supposed to do. This is the multi-WO coherence problem.

Without periodic audits:
- Parallel code paths drift apart silently (see PARALLEL_IMPLEMENTATION_PARITY)
- Modifier calculations accumulate inconsistencies across subsystems
- Sequential WOs make locally-correct choices that are globally incoherent
- The gap between "what we've built" and "what the spec says" grows with every batch

The root cause: no agent in the continuous development loop has the job of looking at the complete picture. Builders have narrow scope. PMs have high-level state. Nobody does periodic comprehensive subsystem reads.

## Solution

### Rule

**After every N delivery batches, file one read-only audit WO targeting a specific subsystem.**

The auditor reads code, files findings, and never writes production code. The PM triages findings into builder WOs. The sweep cycle catches what sequential narrow WOs cannot.

### The Audit Cadence

The cadence is configurable based on project velocity, but a workable default:

| Project Phase | Cadence | Trigger |
|--------------|---------|---------|
| Early (< 20 batches) | Every 10 batches | Time-based cadence |
| Mid (20-50 batches) | Every 5 batches | Batches completed |
| Late (50+ batches) | Every 3 batches | Batches completed OR a cross-cutting change |

**Cross-cutting trigger:** Any WO that touches a shared utility, central dispatcher, or schema definition should trigger an immediate audit of the subsystems that depend on it — regardless of cadence.

### Subsystem Rotation

Audits should rotate across subsystems systematically. Don't audit the same subsystem twice in a row. Suggested rotation model:

1. Attack/calculation paths
2. State management and persistence
3. Action economy and turn sequencing
4. Condition and duration tracking
5. Spellcasting / special ability resolution
6. Output and narration layer
7. Chargen / entity initialization
8. ...then repeat

This prevents blind spots from forming in under-reviewed subsystems.

### The Auditor Role

The auditor is a distinct role from the builder. Key constraints:

| Auditor Authorities | Auditor Boundaries |
|--------------------|-------------------|
| Read all files in scope | Does not modify production code |
| File FINDING-AUDIT-* entries | Does not draft builder WOs (PM does) |
| Flag critical issues immediately | Does not fix what it finds |
| Read cross-subsystem for coherence | Does not make architecture decisions |

**The auditor's output is findings, not fixes.** This separation is important. An auditor who also fixes is no longer doing an audit — they're doing a builder session with extra reading. The audit value is the independent read. Once the auditor starts writing code, the independent read is over.

### Audit Dispatch Requirements

An audit WO dispatch must include:

```markdown
## Audit Scope
Primary target: [file or module]
Secondary targets: [related files]
Files to read: [list]

## Questions the Auditor Must Answer
For each question, cite the code location (file:line) and the specification reference:
1. [Specific yes/no question about implementation correctness]
2. [Specific yes/no question about parallel path consistency]
3. [Specific yes/no question about enforcement — is this rule actually blocking what it should?]
...

## Finding IDs
Use IDs: FINDING-AUDIT-[SUBSYSTEM]-NNN

## Read-Only Mandate
This is a read-only audit. Do not fix anything. File findings. PM will triage into builder WOs.
If you find a critical flaw, flag it with SEVERITY: CRITICAL and notify immediately.
```

### Audit Debrief Format

Three-pass format:

**Pass 1:** Per-question answers with file:line citations. Findings table.
**Pass 2:** PM summary ≤100 words. Signal-to-noise distilled.
**Pass 3:** Retrospective — patterns noticed, kernel/architectural observations, recommendations for builder WOs.

**Findings table columns:** ID, Severity (CRITICAL/HIGH/MEDIUM/LOW/INFO), Status (OPEN/CLOSED), Summary

### Severity Escalation

| Severity | Definition | PM Action |
|----------|-----------|-----------|
| CRITICAL | System behavior is currently incorrect in a way that affects all users of this subsystem | Halt other work, draft corrective WO immediately |
| HIGH | Significant gap with broad or visible impact | Queue for next dispatch, high priority |
| MEDIUM | Gap with limited scope or workaround available | Queue within 2 batches |
| LOW | Minor inconsistency or style issue | Queue when convenient |
| INFO | Architecture observation, no action required | Log for future reference |

## Implementation

### Choosing Audit Scope

Don't audit "everything" — that's too broad for a single context window. Choose:
- One primary file or module (full read)
- 2-4 secondary files (targeted read of relevant sections)
- A specific set of questions (see template)

**A 500-line primary target with 8 specific questions** produces a better audit than "read the whole subsystem" with no questions.

### The Audit WO vs. the Builder WO

These are fundamentally different dispatches:

| Dimension | Builder WO | Audit WO |
|-----------|-----------|----------|
| Output | Code changes + debrief | Findings memo only |
| Files modified | Production code | None |
| Goal | Implement a specific thing | Assess whether the right things are implemented |
| Scope | Narrow (2-5 files typical) | Can be broader (primary + secondary targets) |
| Agent guidance | "Here is what to build" | "Here are the questions to answer" |

### Tracking Audit Coverage

Keep a record of what has been audited:

```markdown
| Subsystem | Last Audited | Findings | Status |
|-----------|-------------|----------|--------|
| Attack calculation | Batch 20 | 3 MEDIUM, 2 LOW | All resolved |
| Condition tracking | Batch 18 | 1 HIGH, 1 LOW | HIGH resolved, LOW queued |
| State management | Never | — | Due |
```

This table prevents the same well-understood subsystem from being audited repeatedly while dark corners accumulate debt.

## When to Use

- Any project that has completed 5+ delivery batches
- Any time a cross-cutting change lands (new shared utility, schema refactor, new field)
- Any time you notice that related subsystems "feel inconsistent" but can't pin the gap
- Before a major version, milestone, or external demonstration

## When NOT to Use

- First 2-3 batches of a project (not enough code to audit)
- Mid-sprint, when you need momentum — schedule the audit for the batch boundary
- Instead of a builder WO for a known gap — audits find unknowns; builders fix knowns

## Real Example

A project had completed 25 delivery batches. Each batch was individually correct. A sweep audit of the calculation subsystem found 21 independent modifier values that had drifted across two parallel code paths. No individual WO had caused the drift — the drift accumulated as sequential WOs targeted one path without knowing about the other.

The audit also found that an intermediate result was being computed correctly in the "single item" path but incorrectly in the "batch" path, and that one modifier had been wired with the wrong sign in 3 of 8 places it was applied.

None of these findings were visible in the test suite, because the test suite tested each path separately. The audit caught what sequential unit tests structurally cannot catch: the coherence of the whole.

**Result:** 3 corrective builder WOs were dispatched. The parallel path architecture was refactored to eliminate the structural source of drift.

---

## Foundation Confidence Events

Sometimes a sweep audit (or an accumulation of canaries) reveals not just a fixable gap, but a structural confidence problem: the process was proving local correctness but failing to prove system connection. Individual WOs were sound. The system-as-a-whole was not verified.

This is a Foundation Confidence Event. It requires more than a single corrective WO.

### Bounded Audit Freeze Sprint

When a systemic canary is found, call a bounded freeze sprint:

- **Duration:** 2–5 sessions
- **Rule:** No new feature WOs during the sprint (blockers and critical fixes excepted)
- **Goal:** Restore confidence in the foundation before continuing delivery

### Exit Gates (define these before the sprint begins)

1. Fidelity and coverage status updated for the targeted scope
2. High-risk domains audited with findings filed
3. All findings routed (WO dispatched, DEFERRED, or CLOSED)
4. Process patch installed if a structural gap was identified
5. Corrective WOs dispatched for highest-impact issues

The PM must define the exit gates before starting the sprint. An open-ended freeze is not a sprint — it is a stall. The exit gates make it bounded.

### What This Is Not

A Foundation Confidence Event is not evidence that the previous work was fake or that the process failed. It means the process proved local correctness (which it was designed to do) but hadn't yet proven system connection (which requires an additional layer). The sweep audit is that layer. The corrective sprint restores the connection.

The right response is not to restart or rewrite. It is to add the missing verification layer and dispatch targeted corrective WOs for the highest-impact issues found.

**Doctrine:** Gates prove local correctness. Sweeps prove cross-cutting fidelity, parity, and consumption. Both are required. Neither replaces the other.



================================================
FILE: patterns/WORKTREE_ISOLATION_PROTOCOL.md
================================================
# Pattern: Worktree Isolation Protocol

## Problem

When multiple builder agents work in parallel, they share the same working directory. Agents that are scoped to non-overlapping files can still collide at the filesystem level: one agent's partial writes, an uncommitted index state, or a stash can corrupt another agent's checkout. Parallel work is not truly parallel if agents share a filesystem root.

The subtler failure mode: an agent reads a file that another in-flight agent has partially modified. The read succeeds. The data is silently wrong. No error fires.

**The failure pattern:**
- Two builders are dispatched simultaneously
- Agent A modifies files in `aidm/resolvers/`; Agent B modifies files in `aidm/schemas/`
- These are correctly non-overlapping scopes on paper
- Agent A does a mid-task `git stash` to test something; Agent B's `git status` now shows stash changes
- Agent B's debrief includes files it never touched
- The PM has to untangle whose change is whose

**Root cause:** File ownership in the work order only prevents *logical* collisions. It does not prevent *filesystem* collisions. Two processes sharing a `.git` directory are not isolated.

---

## Solution

### Rule

**Each active builder session gets its own git worktree. One worktree per active builder. No exceptions during parallel dispatch.**

A git worktree is a linked working directory that shares the object store with the main repository but has its own index, HEAD, and working files. Two worktrees can be on different branches simultaneously. Each agent works in its own worktree, commits to its own branch, and cannot touch another agent's files — at the filesystem level, not just at the work-order level.

### When Worktrees Are Required

Worktrees are required when any of the following apply:

- **Parallel builder dispatch** — two or more builder WOs are active simultaneously
- **Audit + build overlap** — an Anvil audit is in flight at the same time as a Chisel build
- **Multi-builder + shared utility** — any WO touches a shared utility file (schemas, base resolvers, central dispatcher) while another WO is also in flight
- **Long-running sessions** — any session expected to span multiple hours, during which other sessions may be dispatched

Worktrees are **not** required for:
- Sequential builds (one completes, next begins)
- PM-only sessions (no code changes)
- Researcher/auditor sessions that are read-only

### Naming Convention

Worktrees use a three-part name:

```
{seat}-{batch}-{wo}
```

Examples:
- `chisel-w-wo1` — Chisel builder, Batch W, WO1
- `chisel-w-wo2` — Chisel builder, Batch W, WO2
- `anvil-audit-003` — Anvil auditor, Audit WO 003

**Branch naming follows the same convention:**

```
build/{seat}-{batch}-{wo}
```

Examples:
- `build/chisel-w-wo1`
- `build/chisel-w-wo2`
- `build/anvil-audit-003`

This makes `git branch -a` readable at a glance during parallel dispatch.

### Worktree Setup (per dispatch)

The PM includes worktree instructions in the dispatch. The builder executes them before touching any project file:

```bash
# From the repository root
git worktree add ../{worktree-name} -b build/{seat}-{batch}-{wo}

# Confirm
git worktree list
```

Example for Chisel building Batch W WO1:

```bash
git worktree add ../dnd35-chisel-w-wo1 -b build/chisel-w-wo1
cd ../dnd35-chisel-w-wo1
```

The builder then works exclusively in the worktree directory. All reads, all writes, all commits happen in the worktree. The main working directory (`f:\DnD-3.5` or equivalent) is never touched during a parallel session.

---

## Dispatch Metadata

Every work order dispatched during parallel sessions MUST include a Worktree block:

```markdown
## Worktree Assignment

| Field | Value |
|-------|-------|
| Worktree Path | `../{worktree-name}` |
| Branch | `build/{seat}-{batch}-{wo}` |
| Owner Seat | {Chisel / Anvil} |
| Setup Command | `git worktree add ../{worktree-name} -b build/{seat}-{batch}-{wo}` |
| Teardown Command | See cleanup rule below |
```

If a WO does not include a Worktree Assignment block during parallel dispatch, the builder **halts and requests the metadata** before beginning. A missing worktree assignment is a dispatch defect.

---

## Implementation

### Assignment Protocol

1. PM assigns worktree name and branch name when writing the dispatch
2. Builder creates the worktree before reading any project files
3. Builder confirms `git worktree list` shows the new worktree before proceeding
4. All work happens inside the worktree directory
5. Builder commits inside the worktree (`git commit` from the worktree path)
6. Debrief includes the commit hash from the worktree branch

### Cleanup Rule

After PM accepts a WO debrief (ACCEPTED verdict):

1. **Merge the worktree branch into main** (or the project's integration branch)
2. **Remove the worktree:** `git worktree remove ../{worktree-name}`
3. **Delete the branch:** `git branch -d build/{seat}-{batch}-{wo}`
4. PM confirms worktree is removed before dispatching the next round to the same seat

If a WO is **rejected**, the worktree is kept until the fix is delivered. The builder continues to work in the same worktree for the fix WO.

If a WO is **abandoned** (superseded or cancelled), the worktree is removed without merging: `git worktree remove --force ../{worktree-name}`.

### Handoff Rule

Worktrees belong to a session, not to a seat. A new agent session starting work on an incomplete WO should:

1. Check `git worktree list` from the repository root
2. If the worktree still exists: `cd` into it and continue
3. If the worktree was removed before the WO completed: recreate it from the debrief's last commit hash using `git worktree add ../{name} {commit-hash}`

A worktree is **never** handed to a different active builder while another builder's WO is in flight. Worktree reuse is sequential, not parallel.

### Conflict Rule

> **No shared worktree across active builders.**

If two builders are in flight simultaneously, they must be in separate worktrees on separate branches. A worktree that has been handed off to a new session is fine. A worktree shared between two simultaneous sessions is not allowed.

If the PM accidentally dispatches two WOs to the same worktree simultaneously, both builders halt and notify the PM. The PM resolves the collision — typically by creating a second worktree for one of the WOs.

---

## Debrief Requirements

The builder debrief must include:

1. **Worktree path** — confirms the correct worktree was used
2. **Branch name** — confirms commits went to the correct branch
3. **`git worktree list` output** — snapshot showing active worktrees at debrief time
4. **Commit hash** — from the worktree branch (not from main)

Missing any of these from the debrief during a parallel session = debrief **INCOMPLETE**.

---

## Real Example

During Batch W parallel dispatch, three builders were simultaneously in flight on W-WO1, W-WO2, and W-WO3. Without worktree isolation, each agent's `git status` would show uncommitted changes from the other agents. The stash from W-WO2's mid-session experiment appeared in W-WO1's debrief as "files modified." The PM had to manually verify which changes belonged to which WO.

**Without worktree isolation:** Three agents' states bleed together. Debrief verification requires manually parsing `git diff` across the full repo to assign changes to WOs.

**With worktree isolation:** Each agent's `git status` and `git diff` shows only its own changes. The debrief commit hash is definitive. Merge is a clean fast-forward. The PM's verification load drops to reading the debrief, not reconstructing it.

---

## Anti-Patterns

- **Sending two builders to the same worktree.** This is file ownership documented in the WO but not enforced at the filesystem level. You're back to the original problem.
- **Creating the worktree after starting work.** The agent reads files in the main directory, then moves to a worktree. The reads were in main, the writes are in the worktree. The state is now inconsistent.
- **Forgetting to remove worktrees.** `git worktree list` grows without bound. When it hits 5+ entries you lose visibility into which sessions are actually in flight.
- **Naming worktrees generically** (e.g., `temp1`, `temp2`). Opaque names make `git worktree list` unreadable during parallel dispatch. The `seat-batch-wo` convention makes the list self-documenting.
- **Not including the worktree block in the dispatch.** The builder will work in the main directory because it was never told not to. The dispatch is the contract; if the worktree isn't in the contract, it won't be used.

---

## When to Use

- Any parallel dispatch (2+ active builder or auditor WOs)
- Any session where audit and build overlap
- Any session where a shared utility is being modified concurrently with feature work

## When NOT to Use

- Sequential builds where each WO fully completes before the next begins
- Single-agent sessions with no parallel work in flight
- PM-only or researcher-only sessions (read-only work needs no filesystem isolation)



================================================
FILE: templates/AUDIT_DISPATCH_TEMPLATE.md
================================================
# Template: Audit Work Order Dispatch

An audit WO is fundamentally different from a builder WO. The auditor reads code, answers specific questions, and files findings. The auditor **never writes production code**. This template enforces that separation.

See: [Sweep Audit Protocol](../patterns/SWEEP_AUDIT_PROTOCOL.md)

---

```markdown
# [AUDIT-WO-ID]: [Subsystem Name] Audit — Batch [N]

**Assigned to:** [Auditor agent — e.g., "Auditor (Sonnet)" or "Auditor (Opus) for cross-cutting"]
**Date:** [YYYY-MM-DD]
**Priority:** [HIGH | MEDIUM | LOW]
**Status:** [DRAFT | DISPATCHED | IN PROGRESS | COMPLETE]
**Trigger:** [Cadence (every N batches) | Cross-cutting change | Manual escalation]

---

## READ-ONLY MANDATE

This is a read-only audit. You may not modify production code.

If you find a critical flaw:
1. Flag it with SEVERITY: CRITICAL in the findings table
2. Note it prominently at the top of your debrief
3. The PM will triage into a corrective builder WO

Do not attempt to fix what you find. The audit value is the independent read. Once you write code, the audit is over.

---

## Audit Scope

**Primary target:** [file or module — full read]
**Secondary targets:** [related files — targeted read of specific sections only]
**Out of scope:** [adjacent subsystems NOT covered by this audit]

**Files to read:**

- `path/to/primary_module.py` (full read)
- `path/to/secondary_module.py` (lines XX-YY, section: [description])
- `path/to/spec_or_design_doc.md` (for specification cross-reference)

---

## Questions the Auditor Must Answer

For each question: cite the code location (file:line), state YES/NO/PARTIAL, and explain your answer in 1-3 sentences.

1. **[Correctness question]**
   *e.g., "Is the [rule name] calculation at [file:line] consistent with [specification section]?"*

2. **[Parallel path question]**
   *e.g., "Does the [batch path] at [file:line] produce the same result as the [single-item path] at [file:line] for the same inputs?"*

3. **[Enforcement question]**
   *e.g., "Is [guard condition] actually blocking what it should, or does it have gaps in [edge case]?"*

4. **[Coverage question]**
   *e.g., "Are all expected cases handled in [function], or are there unhandled edge cases?"*

5. **[Consistency question]**
   *e.g., "Do [subsystem A] and [subsystem B] use consistent definitions of [concept]?"*

Add questions as needed. Each question should be answerable YES/NO/PARTIAL from the code — avoid open-ended research questions.

---

## Finding IDs

Use IDs in the format: `FINDING-AUDIT-[SUBSYSTEM]-[NNN]`

Example: `FINDING-AUDIT-CONDITIONS-001`

Severity levels:
- **CRITICAL** — System behavior is currently incorrect in a way that affects all users of this subsystem. PM halts other work, drafts corrective WO immediately.
- **HIGH** — Significant gap with broad or visible impact. Queue for next dispatch, high priority.
- **MEDIUM** — Gap with limited scope or workaround available. Queue within 2 batches.
- **LOW** — Minor inconsistency or style issue. Queue when convenient.
- **INFO** — Architecture observation, no action required. Log for reference.

---

## Debrief Format (3-pass)

**Pass 1 — Question Answers:**
Answer each dispatch question with file:line citations. Include a findings table.

Findings table format:
| ID | Severity | Status | Summary |
|----|----------|--------|---------|
| FINDING-AUDIT-[SUBSYSTEM]-001 | HIGH | OPEN | [One sentence] |

**Pass 2 — PM Summary (≤100 words):**
Distill the key signal. What is the state of this subsystem? What are the highest-priority findings? What should the PM do first?

**Pass 3 — Retrospective:**
Patterns noticed. Architectural observations. Recommendations for builder WOs. Were there questions you couldn't answer from the files in scope? Note what additional reading would resolve them.

---

## What NOT to Do

- Do NOT modify any production files
- Do NOT draft builder WO dispatches — the PM triages findings into WOs
- Do NOT leave findings in session memory — file every finding before closing
- Do NOT answer questions with "probably" or "seems like" — read the code and state what it does
- Do NOT treat test files as ground truth for behavior — read the implementation
```

---

## Usage Notes

- **Scope is critical.** An audit of "everything" fails — the scope is too broad for a single context window. One primary file (full read) + 2-4 secondary files (targeted reads) + a specific question list is the right size.
- **Questions drive the value.** Vague questions produce vague findings. Each question should be answerable YES/NO/PARTIAL from code inspection.
- **CRITICAL findings stop the batch.** If the auditor flags CRITICAL, the PM should triage before dispatching the next builder batch. Don't run builders in parallel with an unresolved CRITICAL finding in the same subsystem.
- **Rotate subsystems.** Don't audit the same subsystem twice in a row. Maintain an audit coverage log — see SWEEP_AUDIT_PROTOCOL for the recommended rotation model.
- **Auditor ≠ builder.** If the auditor writes production code, they're no longer auditing. If you find yourself writing a fix, stop, file it as a finding, and wait for a builder WO.

## When to Use

- Every N delivery batches (see cadence table in SWEEP_AUDIT_PROTOCOL)
- After any cross-cutting change (shared utility modified, schema field added, central dispatcher changed)
- When related subsystems "feel inconsistent" but you can't pin the gap
- Before a major milestone or external demonstration

## When NOT to Use

- Instead of a builder WO for a known gap — audits find unknowns; builders fix knowns
- Mid-sprint when you need delivery momentum — schedule the audit for the batch boundary
- For the first 2-3 batches of a new project (not enough code to audit)



================================================
FILE: templates/HANDOFF_TEMPLATE.md
================================================
# Template: Handoff Document

Copy this template when a session ends with incomplete work, findings that must survive to the next session, or context the next agent needs.

See: [Artifact Primacy Pattern](../patterns/ARTIFACT_PRIMACY.md) | [Plain English Pass Pattern](../patterns/PLAIN_ENGLISH_PASS.md)

---

```markdown
# Handoff: [Short Description]

**From:** [Agent identifier — e.g., "Builder (Opus 4.6)", "Verifier (Sonnet)"]
**To:** Next agent
**Date:** [YYYY-MM-DD]
**Status:** [READY TO EXECUTE | NEEDS REVIEW | BLOCKED ON [thing]]

---

## Plain English Summary (Optional — include if the operator will read this handoff)

**What was this session doing?**
[1-2 sentences. No jargon. What the session was working on in everyday terms.]

**Where did it leave off?**
[1-2 sentences. What's done and what remains, in non-technical language.]

---

## Uncommitted Work

[What was changed in the working tree but not committed. Include file paths and a description of each change. If there's nothing uncommitted, write "None — all work committed."]

**File:** `path/to/file.py`
**Change:** [Description of what was modified and why]
**Action:** [What the next agent should do — commit it, review it, revert it]

## Completed This Session

[What was done and committed. Include commit hashes if available.]

- `abc1234` — [commit message / description]
- `def5678` — [commit message / description]

## Next Steps

[Exactly what the next agent should do, in order. Numbered. Each step should be independently verifiable.]

1. [First step]
2. [Second step]
3. [Third step]

## Files to Read Before Executing

[List of files the next agent should read to understand the context. Keep this minimal — only what's needed, not everything that's relevant.]

- This file (you're reading it)
- `path/to/relevant_doc.md` — [why they need it]
- `path/to/modified_file.py` — [to verify the uncommitted edit]

## What NOT to Do

[Guardrails for the next agent. Common mistakes, scope boundaries, files to avoid.]

- Do NOT modify [file/system] — [reason]
- Do NOT start [task] — [it's being handled elsewhere / not ready yet]

---

**End of Handoff**
```

---

## Usage Notes

- **Write this BEFORE you run out of context**, not after. By the time you're summarizing for rollover, you've already lost the ability to write a detailed handoff.
- **The "Next Steps" section is the most important part.** If the next agent only reads one section, it should be this one.
- **Include commit hashes.** The next agent can `git log` to verify what was actually committed vs what the handoff claims.
- **"Files to Read" should be 3-5 files, not 15.** If the next agent needs to read 15 files, the handoff isn't self-contained enough. Add more context to the handoff itself.
- **Be honest about uncommitted work.** A handoff that says "all done" when there's a dirty working tree will confuse the next agent. State exactly what's uncommitted and why.



================================================
FILE: templates/ONBOARDING_CHECKLIST_TEMPLATE.md
================================================
# Onboarding Checklist Template

Use this template to create an onboarding checklist for your project. The checklist defines what an agent reads, in what order, to become operational with minimal context waste.

---

## Instructions

Copy the template below into your project as `AGENT_ONBOARDING_CHECKLIST.md`. Replace bracketed placeholders with your project's actual files and commands. Remove sections that don't apply.

---

## Template

```markdown
# Agent Onboarding Checklist

**Purpose:** Get any agent operational in minimum context. Read in order. Do not skip steps.

## Phase 1: Orient (What is this project?)

- [ ] Read `[PROJECT_COMPASS.md or README.md]` — project purpose, architecture, key terms
- [ ] Read `[SOURCES_OF_TRUTH.md]` — which file is authoritative for which concept

**After Phase 1, the agent should know:** What the project does, what its major components are, and where to find canonical information.

## Phase 2: Ground (What is the current state?)

- [ ] Run session bootstrap:
  ```bash
  git status
  git log --oneline -5
  [test command] 2>&1 | tail -3
  ```
- [ ] Read `[PROJECT_STATE_DIGEST.md]` — current milestone, blockers, recent decisions
- [ ] Cross-check: Does the bootstrap output match the state digest? If not, the digest is stale — trust the bootstrap.

**After Phase 2, the agent should know:** What's done, what's in progress, what's blocked, and whether the project is healthy.

## Phase 3: Rules (How do we work here?)

- [ ] Read `[AGENT_DEVELOPMENT_GUIDELINES.md]` — coding conventions, naming rules, common pitfalls
- [ ] Read `[COHERENCE_DOCTRINE.md or ARCHITECTURE.md]` — architectural constraints that cannot be violated
- [ ] Read `[AGENT_COMMUNICATION_PROTOCOL.md]` — how to escalate, what to do when stuck

**After Phase 3, the agent should know:** What it's allowed to do, what it must not do, and how to ask for help.

## Phase 4: Task (What do I do now?)

- [ ] Read the specific dispatch or work order assigned to this session
- [ ] Verify: Is the dispatch self-contained? Can I execute it using only the dispatch + files it references?
- [ ] If the dispatch references files, read those files now
- [ ] Begin work

**After Phase 4, the agent is operational.**

## Verification Gates

Before starting work, verify these assertions:

- [ ] I can name the project's primary test command
- [ ] I know which branch I'm on and whether it's clean
- [ ] I know the 3 files I must never edit without explicit instruction: `[list critical files]`
- [ ] I know where to write my session output (handoff file, memo, or dispatch response)

## Emergency: If Context Runs Low

If the context window is filling up before the task is complete:

1. Write a handoff document ([template](HANDOFF_TEMPLATE.md)) with current state
2. Commit any completed work
3. Report to the coordinator what's done and what's remaining
4. Do NOT rush to finish — a clean handoff is better than a broken completion
```

---

## Customization Notes

- **Phase 1 should be 2-3 files maximum.** If the agent needs to read more than 3 files to understand the project, your orientation documents need consolidation.
- **Phase 2 must include machine verification.** A session bootstrap command is non-negotiable. Without it, the agent may operate on stale assumptions.
- **Phase 3 scales with project complexity.** A simple project might have one rules file. A complex project might have 3-4. Don't exceed 4 — if you have more, consolidate.
- **Phase 4 is always exactly one dispatch.** The agent does one thing per session. If you need multiple things done, dispatch multiple sessions.


================================================
FILE: templates/SESSION_MEMO_TEMPLATE.md
================================================
# Template: Session Memo

Copy this template when a session produces findings, completes work, or discovers issues that the human coordinator (PM/operator) needs to know about.

See: [PM Context Compression Pattern](../patterns/PM_CONTEXT_COMPRESSION.md) | [Plain English Pass Pattern](../patterns/PLAIN_ENGLISH_PASS.md)

---

```markdown
# MEMO: [Short Title]

**From:** [Agent identifier]
**Date:** [YYYY-MM-DD]
**Session scope:** [What this session was tasked with — one sentence]

---

## Plain English Summary

**What problem did this solve?**
[1-2 sentences. No jargon. Describe the problem as a user would experience it.]

**What does it actually do?**
[1-2 sentences. No jargon. Describe the mechanism in everyday language.]

**Why should anyone care?**
[1-2 sentences. Describe the impact — what's different now, what's possible that wasn't.]

---

## Action Items (PM must act on these)

[Numbered list. Each item has: what needs to happen, who does it, what it blocks. Keep this SHORT — 3-5 items max. If there are more, prioritize.]

1. **[Action]** — [Who does it]. Blocks: [what it blocks, or "nothing"].
2. **[Action]** — [Who does it]. Blocks: [what it blocks].

## Status Updates (Informational only)

[What was completed, what changed, what was committed. The PM does NOT need to act on these — they're for awareness.]

- [Commit hash] — [What was done]
- [Status change] — [What changed and why]

## Deferred Items (Not blocking, act when convenient)

[Low-priority findings, future WO suggestions, observations. The PM can read these when they have spare context budget.]

- [Item] — [Why it can wait]

---

**End of Memo**
```

---

## Four-Pass Writing Process

**Pass 0 — Plain English:** Answer the three questions (What problem? What does it do? Why care?) in 150 words or fewer. No jargon, no code references, no rule IDs. Write this first — while the high-level picture is still clear. This is what the operator reads.

**Pass 1 — Full Dump:** Write everything from your context window — cascading impacts, agent failures, schema additions, WO mismatches, test changes, loose ends. Don't filter. Don't worry about length. This is the raw knowledge capture.

**Pass 2 — PM Summary:** Compress the dump into the memo format above. Action items only include things the PM must actually do. Status updates are one line each. Deferred items get one sentence each.

**Pass 3 — Retrospective:** What went well, what didn't, operational judgment for future sessions. See [Debrief Integrity Boundary](../patterns/DEBRIEF_INTEGRITY_BOUNDARY.md) for the trust levels of each pass.

**Why four passes:** Pass 0 translates for the non-technical operator. Pass 1 prevents context loss. Pass 2 respects the PM's bandwidth. Pass 3 captures operational learning. If you try to write the compressed version directly, you'll skip things that seemed unimportant but weren't. If you only write the full dump, the PM can't process it.

**Where they go:**
- Pass 0 (plain english): Top of the debrief file, and copied into the memo
- Pass 1 (full dump): `pm_inbox/DEBRIEF_[SESSION_ID].md` — archived for reference
- Pass 2 (PM summary): `pm_inbox/MEMO_[SHORT_TITLE].md` — this is what the PM reads
- Pass 3 (retrospective): End of the debrief file

---

## Usage Notes

- **Action Items are the only section the PM might act on immediately.** Everything else is context. Design your memo so a PM who only reads the Action Items section still gets what they need.
- **Don't combine memos.** One memo per session. If a session produces multiple unrelated findings, that's still one memo — the PM triages internally.
- **Date everything.** Context windows don't have timestamps. The PM needs to know which memo is most recent when two memos conflict.
- **"Session scope" in the header is critical.** It tells the PM what this session was supposed to be doing, which frames everything that follows.



================================================
FILE: templates/SOURCES_OF_TRUTH_TEMPLATE.md
================================================
# Sources of Truth Index Template

Use this template to establish which file is authoritative for each concept in your project. When a document and a source of truth disagree, the source of truth wins.

---

## Instructions

Copy the template below into your project as `SOURCES_OF_TRUTH.md`. Fill in your project's actual canonical sources. Update this file whenever you add a new authoritative source.

---

## Template

```markdown
# Sources of Truth

**Purpose:** When two files disagree, this index tells you which one is right.

**Rule:** If a fact appears in multiple files, the source of truth listed here is canonical. All other files containing that fact are mirrors that may be stale.

## Code & Architecture

| Concept | Source of Truth | NOT authoritative |
|---------|---------------|-------------------|
| Current test count | `pytest` output (run it) | Any document citing a test count |
| API contracts | Source code (schemas/, interfaces/) | Design documents describing the API |
| Feature availability | Source code + tests | Roadmap documents, planning files |
| Dependencies | `[package.json / requirements.txt / Cargo.toml]` | Prose documents listing dependencies |

## Project State

| Concept | Source of Truth | NOT authoritative |
|---------|---------------|-------------------|
| Current branch & status | `git status` output | State digest documents |
| What's deployed | `[deployment system / CI dashboard]` | Release notes (may be stale) |
| Test health | `pytest` / `npm test` output | Documents claiming "all tests pass" |
| Build status | `[build command]` output | Documents claiming "builds clean" |

## Process & Governance

| Concept | Source of Truth | NOT authoritative |
|---------|---------------|-------------------|
| Coding conventions | `[AGENT_DEVELOPMENT_GUIDELINES.md]` | Individual file comments |
| Architectural constraints | `[COHERENCE_DOCTRINE.md]` | Design discussion documents |
| Work order status | `[CHECKLIST.md or tracking file]` | Individual WO files (may not update status) |
| Agent onboarding | `[AGENT_ONBOARDING_CHECKLIST.md]` | README orientation sections |

## Domain-Specific

| Concept | Source of Truth | NOT authoritative |
|---------|---------------|-------------------|
| [Your domain concept 1] | `[file]` | [what to ignore] |
| [Your domain concept 2] | `[file]` | [what to ignore] |

## Resolution Protocol

When you find a contradiction:

1. Check this index. The source of truth wins.
2. If the source of truth is a command (e.g., `pytest`), run it. Don't trust cached output.
3. Update the stale file to match the source of truth.
4. If the stale file is in a different agent's write set, flag it — don't update it yourself.
5. If neither file is listed here, escalate to the coordinator. One of them needs to become the source of truth.

## Maintenance

- Update this file when you add a new authoritative source
- Review quarterly (or after major milestones) to remove stale entries
- This file itself is authoritative — it's the source of truth about sources of truth
```

---

## Customization Notes

- **Machine-verifiable sources beat documents.** Prefer `pytest` output over a document claiming test counts. Prefer `git status` over a state digest. Documents drift; commands don't.
- **The "NOT authoritative" column is as important as the source column.** It tells agents what to distrust. Without it, agents treat every file as equally authoritative.
- **Keep it short.** If this index exceeds 30 rows, you have too many sources of truth or too fine-grained a categorization. Consolidate.
- **Domain-specific section is project-dependent.** A game engine might list "SRD rules interpretation" → specific research file. A web app might list "auth flow" → specific module. Fill in what matters for your project.


================================================
FILE: templates/WORK_ORDER_TEMPLATE.md
================================================
# Template: Work Order Dispatch

Copy this template for each task you assign to an LLM agent. Fill in every section. If a section doesn't apply, write "N/A" — don't delete it, because the next person to use this template needs to see all sections.

See: [Dispatch Self-Containment Pattern](../patterns/DISPATCH_SELF_CONTAINMENT.md)

---

```markdown
# [WO-ID]: [Short Title]

**Assigned to:** [Agent type/session — e.g., "Builder (Sonnet)", "Verifier (Opus)"]
**Date:** [YYYY-MM-DD]
**Priority:** [HIGH | MEDIUM | LOW]
**Status:** [DRAFT | DISPATCHED | IN PROGRESS | COMPLETE]

---

## Context

[Why this work exists. What problem it solves. What happened that made this necessary. 2-4 sentences. The agent reading this has zero prior context — explain as if they've never seen the project before.]

## Task

[Exactly what to do. Be specific and concrete. If there are multiple steps, number them. Each step should be independently verifiable.]

1. [First step]
2. [Second step]
3. [Third step]

## Files to Modify

[Explicit file paths. Include line numbers if targeting specific code. If lines may have shifted, include surrounding context (function name, nearby code) so the agent can locate the right spot.]

- `path/to/file.py` (lines XX-YY, function `function_name`)
- `path/to/other_file.py` (constant `CONSTANT_NAME`)

## Required Reading

[Files the agent MUST read before starting work. Include governance docs if relevant.]

- `DEVELOPMENT_GUIDELINES.md` — Section [N] ([topic])
- `path/to/design_decision.md` — [why this is relevant]

## Verification

[How to confirm the work is correct. Prefer machine-verifiable criteria.]

- Run: `[test command]`
- Expected: [what passing looks like]
- Write new test: `test_[description]()` in `tests/test_[module].py`

## Scope Boundaries

[What NOT to do. Adjacent work that belongs to other work orders. Files the agent must not modify.]

- Do NOT modify `[file]` — that belongs to [WO-ID]
- Do NOT change [thing] — only change [other thing]
- Do NOT refactor surrounding code — fix only what's specified

## Dependencies

[Other work orders that must complete before this one can start. If none, write "None."]

- DEPENDS-ON: [WO-ID] ([reason])
- Or: None — this WO is independently executable.

## What NOT to Do

[Common mistakes an agent might make on this task. Specific to this WO.]

- Do not [common mistake 1]
- Do not [common mistake 2]
```

---

## Usage Notes

- **One task per dispatch.** Don't combine unrelated work. If two changes are in different files for different reasons, they're two WOs.
- **Be redundant.** Repeat important constraints in both "Task" and "Scope Boundaries." Agents skim, and the constraint they miss is the one that causes a revert.
- **Verify line numbers before dispatching.** Code changes between when you write the WO and when the agent reads it. Include function names and surrounding context as anchors.
- **The "What NOT to Do" section prevents 80% of reverts.** Agents are eager to help. They'll "improve" adjacent code, refactor for clarity, add error handling you didn't ask for. Explicit prohibitions are more effective than implicit scope.


