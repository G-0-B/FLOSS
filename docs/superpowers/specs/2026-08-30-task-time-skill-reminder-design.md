# Task-Time Skill Reminder — Design

```yaml
id: "flossi0ullk-task-time-skill-reminder"
version: "0.1.0"
date: "2026-08-30"
authored_local: "2026-08-30T13:46:35.4850856-04:00"
authored_utc: "2026-08-30T17:46:35.4894017Z"
status: "Approved design; not implemented"
truth_status: "⚠️ Specified"
approval: "Operator replied 'absolutely that sounds great' after the design and generated hook-config effects were presented."
base_commit: "cc71e5d6d0f2f6265cd0e394d2f09f5d5749db93"
branch_observed: "feat/coordination-room"
canonical_promotion: false
```

## Intent and decision

Agents in this workspace receive a skill reminder at session start, but repeated
observations show that startup guidance alone does not reliably cause task-time
skill selection. The approved intervention is a compact, deterministic reminder
on every supported `UserPromptSubmit` event.

**Decision:** add a generated, cross-harness task-time reminder that always names
`using-superpowers` and suggests at most three task-relevant skills from the
shared registry. Suggestions are advisory discovery aids. They do not establish
truth, authorize actions, or replace reading the selected `SKILL.md`.

## Evidence baseline

- ✅ **Verified:** `.agent-surface/STARTUP_CONTRACT.md` already contains a
  prominent skill-invocation section.
- ✅ **Verified:** `.agent-surface/context/CONTEXT_L0.md` includes `skills` in
  route order but does not perform a task-time skill check.
- ✅ **Verified:** the managed Codex and Claude `UserPromptSubmit` path currently
  invokes AgentMemory's `prompt-submit.mjs`, which records the prompt but emits
  no skill-selection context.
- ✅ **Verified:** on 2026-08-30, both
  `materialize_shared_hook_surface.py --check` and
  `materialize_shared_skill_surface.py --check` reported their applicable
  projections as `CHECK OK`; user-scope targets were explicitly skipped by the
  default check.
- ⚠️ **Evidence candidate:** AgentMemory lesson `lsn_29169ee1b86b07d5`
  reports a later multi-PR session with one skill invocation out of twenty-nine
  available and concludes that prior reminder infrastructure did not prevent
  recurrence. AgentMemory is Plane A recall, not repository canon.

The failure is therefore classified as **task-time salience**, not missing skill
installation and not absent startup guidance.

## Goals

1. Remind the agent to check skills at the moment a task arrives.
2. Make the reminder relevant without an LLM call, network dependency, or
   opaque ranking.
3. Keep the prompt-time token cost bounded and predictable.
4. Preserve one canonical skill corpus and generated harness projections.
5. Fail open: reminder failure must never block a user prompt or tool execution.
6. Produce test and provenance evidence without treating telemetry as truth.

## Non-goals

- Automatically invoking skills on the agent's behalf.
- Proving that a skill was read or followed.
- Evaluating task correctness, governing truth, or bypassing symbolic
  validation.
- Persisting or re-emitting user prompt text.
- Adding embeddings, an LLM classifier, AgentMemory recall, or session-state
  storage to the prompt hook.
- Editing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, ADRs, integrity zomes, or the
  consensus gateway.
- Claiming universal cross-harness prompt-hook support where a harness exposes
  no compatible event.

## Authority and source boundaries

The shared skill source remains:

- `FLOSS/shared-skill-surface.json`
- `FLOSS/skill-corpus/*`

Hook wiring remains canonical in `FLOSS/shared-hook-surface.json`. Generated
files such as `.codex/hooks.json`, Claude settings, and
`.agent-surface/skills/skill-registry.json` must never be hand-edited.
`FLOSS/hooks/README.md` and `FLOSS/docs/architecture/RUNTIME_SURFACES.md` receive
bounded operator-facing updates so the new runtime path is discoverable.

The operator explicitly approved the generated hook-configuration effects,
including the user-scope Claude settings update required for Claude coverage.
The repository `.claude/settings.json` target remains intentionally hook-empty
to prevent Claude user/project double firing.

## Architecture

```text
UserPromptSubmit
  -> skill_prompt_inject.py
  -> read generated skill-registry.json
  -> deterministic lexical ranking
  -> bounded harness-specific additionalContext
  -> agent chooses and reads applicable SKILL.md
```

### 1. Discovery policy

Add a small `discovery_policy.prompt_reminder` object to
`FLOSS/shared-skill-surface.json`. It defines:

- `enabled`: rollout switch;
- `always_include`: initially `["using-superpowers"]`;
- `max_candidates`: `3`, excluding always-included skills;
- `max_context_chars`: `900`;
- `fallback_index`: `.agent-surface/skills/SKILL_INDEX.md`;
- ranking field order: skill name, description, summary, category.

The policy is copied into the generated skill registry by the existing
materializer. The hook reads the registry; it does not reparse every skill file
on each prompt.

### 2. Prompt hook

Add `FLOSS/hooks/skill_prompt_inject.py` with three isolated responsibilities:

- parse and normalize the hook input;
- rank skill candidates using the generated registry;
- encode bounded output for the selected harness contract.

The script performs no writes, network calls, model calls, subprocess calls, or
AgentMemory operations. Diagnostics, if needed, go to the existing hook log and
never to protocol stdout.

### 3. Deterministic ranking

Ranking is deliberately simple and inspectable:

1. Case-fold and tokenize the current prompt.
2. Remove punctuation, tokens shorter than three characters, and a compact
   fixed stop-word set including frontmatter boilerplate such as `use` and
   `when`.
3. Score exact skill-name phrases highest, then token overlap with skill name,
   description, summary, and category in descending weight order.
4. Sort by score descending and skill name ascending for stable ties.
5. Return at most three positively scoring candidates, excluding
   `always_include` entries.

There is no stemming, embedding similarity, hidden model judgment, or learned
state in the first version. A zero-score result still emits the always-included
skill and the index pointer; it never states that no skill applies.

### 4. Reminder contract

The injected text has a positive structural contract rather than a prohibition
list:

```text
Skill check: before substantive work, inspect and load every applicable SKILL.md.
Always check: using-superpowers.
Likely candidates: <zero to three names with short trigger descriptions>.
Candidates are advisory; no match waives the check. Index: <path>.
Announce the skills you actually use.
```

The output must not quote or reproduce the user's prompt. Candidate descriptions
are truncated as necessary to keep the entire injected context at or below the
configured character cap.

Short continuation prompts such as `yes` still receive the always-included
check. Version 0 does not persist an earlier prompt merely to improve matching;
that would introduce unnecessary prompt storage and lifecycle complexity.

### 5. Harness adapters and coverage

`FLOSS/shared-hook-surface.json` adds the reminder command exactly once beside
the existing AgentMemory observer for:

| Harness | Event | v0 coverage |
| --- | --- | --- |
| Codex | `UserPromptSubmit` | ⚠️ Specified pending functional probe |
| Claude user scope | `UserPromptSubmit` | ⚠️ Specified pending functional probe |
| Gemini | no managed prompt-submit event | Startup/orientation fallback only |
| Hermes | no managed prompt-submit event | Startup/orientation fallback only |
| OpenCode | hook target disabled | Startup/orientation fallback only |

The implementation may pass an explicit target argument when Codex and Claude
require different JSON response shapes. Unknown harnesses receive no invented
compatibility claim. Configuration presence is not completion: each supported
harness needs a real functional-path probe proving that the reminder reaches
model context.

## Failure, safety, and privacy behavior

- Missing registry, malformed JSON, unknown skill, or encoding error: emit a
  compact always-check/fallback-index reminder when safe, otherwise exit `0`
  without blocking the prompt.
- Registry content is treated as generated data derived from repository-owned
  skills, never as user authority or a truth verdict.
- User prompt content stays in process memory only for ranking and is neither
  logged nor echoed by this hook.
- The hook cannot approve changes, select a final skill, mark work complete, or
  claim compliance.
- Existing exact-once protection remains load-bearing. The same reminder must
  not be declared in both Claude project and user scope.
- Codex/Hermes content pinning and operator approval behavior must not be
  bypassed or auto-accepted.

## Test design

### RED — establish the present gap

1. A focused test shows that the current managed `UserPromptSubmit` commands
   contain only the AgentMemory observer and no skill reminder.
2. Preserve the observed no-guidance behavior before adding the new command.
3. Run fresh-context control trials that tempt an agent to skip skill discovery;
   retain raw outputs rather than only aggregate labels.

### GREEN — minimal behavior

Add focused tests for:

- always including `using-superpowers`;
- exact candidate ordering and stable tie-breaking;
- zero-match fallback;
- short continuation prompts;
- malformed input and missing registry fail-open behavior;
- the `900`-character cap;
- absence of prompt text in output and logs;
- no network, subprocess, AgentMemory, or durable-write path;
- exact-once manifest wiring for Codex and Claude user scope;
- preservation of the intentionally empty Claude project-scope event;
- target-specific protocol output.

### REFACTOR and behavioral verification

Micro-test the reminder wording with a no-guidance control and at least five
fresh-context samples per candidate wording, manually reading every output.
Then run combined-pressure scenarios covering time pressure, trivialization
(`just answer quickly`), and continuation (`yes, proceed`). Preserve dissent,
false positives, false negatives, and rationalizations.

Focused automated checks precede broader materializer checks. Completion
requires:

```powershell
python -m pytest FLOSS/scripts/tests/test_shared_hook_surface.py FLOSS/scripts/tests/test_skill_prompt_inject.py -q
python FLOSS/scripts/materialize_shared_skill_surface.py --workspace-root C:\~shit --check
python FLOSS/scripts/materialize_shared_hook_surface.py --workspace-root C:\~shit --check
python FLOSS/scripts/refresh_agent_surfaces.py --check
```

User-scope projections require their explicit scope flag and a separate bounded
diff/readback. A nonzero `--check` result is drift evidence, not automatically a
code defect; its output must be classified.

## Rollout and rollback

1. Add failing tests and preserve their expected failures.
2. Implement the policy, hook, and canonical manifest wiring.
3. Materialize repository-scope projections and inspect the exact diff.
4. Materialize the already-approved Claude user-scope target separately and
   inspect/read back only the managed event.
5. Complete Codex and Claude functional probes, including any operator trust
   prompt caused by changed pinned hook content.
6. Run all surface checks and append implementation provenance.

Rollback is additive and recoverable: set the reminder policy to disabled,
remove its managed command from the canonical hook manifest, rematerialize, and
retain the inert script or move it through the repository's archive discipline.
Do not hand-edit generated settings and do not delete evidence.

## Acceptance criteria

- `using-superpowers` appears in every supported task-time reminder.
- No more than three additional deterministic candidates appear.
- The output is at most `900` characters and contains no echoed prompt text.
- Reminder failures never block prompt handling.
- Codex and Claude each wire the reminder exactly once.
- Claude project scope remains free of the reminder to prevent double firing.
- Gemini, Hermes, and OpenCode limitations are reported, not hidden.
- Focused tests, pressure trials, functional probes, and all relevant
  materializer checks have preserved outputs.
- A timestamped provenance packet produced through
  `FLOSS/packages/activity_log/provenance.py` binds the implementation diff,
  checks, functional probes, operator approval, and unresolved limitations;
  `FLOSS/scripts/audit_provenance_packets.py` validates the packet before it is
  cited as evidence.
- No artifact is promoted to canonical status by this design or its telemetry.

## Design provenance

Evidence snapshot taken at `2026-08-30T17:46:35.4894017Z` from base commit
`cc71e5d6d0f2f6265cd0e394d2f09f5d5749db93` in the nested `FLOSS/` Git
repository:

| Artifact | SHA-256 |
| --- | --- |
| `.agent-surface/STARTUP_CONTRACT.md` | `9ebc912f92467221b447a75f17284e71e2de4c84135539ee45541fc29afd4ca8` |
| `.agent-surface/context/CONTEXT_L0.md` | `7fc1a0e040da37e6f99d0c1b50d1598a7be968c7d18d2f98d22fd422aaf717e8` |
| `FLOSS/shared-hook-surface.json` | `6515f7e4781a0427b09b741d7303c7ca40b96fa2dbc2db20ae145772f66ead46` |
| `FLOSS/shared-skill-surface.json` | `16fbabcfc8dc5bd20301c18fb088cfd7f9b9ddb48d77ed8ab3fb29aadbdb0f9b` |
| `FLOSS/hooks/session_start_inject.py` | `ef72e4a3e194cc6dc25aee785af945ce13eb3c526f57ff47f95b1e362b44cccc` |

The worktree contained unrelated modifications and untracked files at design
time. This artifact is intentionally additive and must be committed by exact
path without staging or altering unrelated operator work.
