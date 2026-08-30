# Task-Time Skill Reminder — Design

```yaml
id: "flossi0ullk-task-time-skill-reminder"
version: "0.2.0"
date: "2026-08-30"
authored_local: "2026-08-30T13:46:35.4850856-04:00"
authored_utc: "2026-08-30T17:46:35.4894017Z"
reviewed_local: "2026-08-30T16:23:15.8715176-04:00"
reviewed_utc: "2026-08-30T20:23:15.8760093Z"
status: "Review-revised design; operator re-approval required; not implemented"
truth_status: "⚠️ Specified"
original_approval: "Operator replied 'absolutely that sounds great' after v0.1.0 and its generated hook-config effects were presented."
review_base_commit: "ba10735f745801d999bd0f47cbfcc63a318c60de"
branch_observed: "feat/coordination-room"
canonical_promotion: false
```

## Intent and decision

Agents in this workspace receive skill guidance at session start, but available
evidence does not establish why skills are later omitted. The failure could be
delivery, placement, salience, agent compliance, or a combination. Version 0.2
therefore treats **task-time salience as a working hypothesis**, not a verified
root cause, and separately tests delivery, visibility, and behavior.

**Proposed decision:** add a generated, cross-harness task-time reminder on
supported `UserPromptSubmit` events. It always names `using-superpowers` and may
suggest at most three task-relevant skills from the shared registry.
Suggestions are advisory discovery aids. They do not establish truth, authorize
actions, prove compliance, or replace reading each selected `SKILL.md`.

This revision materially changes policy location, compatibility handling,
privacy tests, exact-once verification, and the evaluation protocol. The
original v0.1.0 approval is preserved as provenance but does not approve this
revision or any implementation diff.

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
- ✅ **Verified:** Claude's official hook reference says
  `UserPromptSubmit` `additionalContext` is added alongside the submitted
  prompt, wrapped as a system reminder, and retained in the transcript.
- ❌ **Blocked:** an official public Codex hook contract establishing the
  equivalent response shape and placement was not found during this review.
  Codex support therefore remains unverified until a local functional probe
  records the observed contract.
- ⚠️ **Evidence candidate:** AgentMemory lesson `lsn_29169ee1b86b07d5`
  reports a later multi-PR session with one skill invocation out of twenty-nine
  available and concludes that prior reminder infrastructure did not prevent
  recurrence. AgentMemory is Plane A recall, not repository canon.

Sources for the Claude claims are the official
[hooks reference](https://code.claude.com/docs/en/hooks) and
[monitoring reference](https://code.claude.com/docs/en/monitoring-usage).

## Review reconciliation

Two supplied external reviews were treated as proposals, not instructions.
Their repository claims were checked against live files where possible.

Accepted and incorporated:

- distinguish reminder delivery, placement, salience, and compliance;
- put hook execution policy in the hook surface while retaining skills in the
  skill surface;
- add an explicit registry-schema handshake and generic compatibility fallback;
- specify ranking weights, stop words, a minimum score, and stable ties;
- formalize privacy boundaries, negative sentinel tests, and exact-once checks;
- preregister behavioral categories and evidence-bearing metrics;
- specify functional probes, a capability matrix, bounded rollback, and
  path-restricted staging;
- bind promotion claims to the existing provenance-packet and consent schemas.

Rejected or deferred:

- a third reminder-policy manifest: the hook manifest already owns runtime
  hook policy, so another authority surface would add drift without evidence;
- production session cache or `last_seen_skills` file: it adds prompt-adjacent
  state, privacy, concurrency, and lifecycle costs before habituation is shown;
- a configurable `injection_position`: the harness controls placement and the
  design must observe rather than invent that capability;
- new top-level provenance fields: the existing provenance schema already
  binds claims to content-addressed artifacts, evidence, risks, benefits,
  human decisions, and consent references;
- self-reported skill use as proof: model narration is not invocation evidence.

## Goals

1. Remind the agent to check skills at the moment a task arrives.
2. Determine whether the reminder was delivered, visible in the harness-defined
   position, and behaviorally useful.
3. Make selection deterministic without an LLM call, network dependency, or
   opaque ranking.
4. Keep context cost bounded and measure both characters and approximate tokens.
5. Preserve one canonical skill corpus and generated harness projections.
6. Fail open while making degradation observable without retaining prompt text.
7. Produce test and provenance evidence without treating telemetry or model
   self-report as truth.

## Non-goals

- Automatically invoking skills on the agent's behalf.
- Proving that a skill was read or followed from model narration alone.
- Evaluating task correctness, governing truth, or bypassing symbolic
  validation.
- Persisting or re-emitting user prompt text.
- Adding embeddings, an LLM classifier, AgentMemory recall, or production
  session-state storage to the prompt hook.
- Editing `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, ADRs, integrity zomes, or the
  consensus gateway.
- Claiming universal cross-harness prompt-hook support where a harness exposes
  no verified compatible event.

## Authority and source boundaries

The shared skill corpus remains authoritative at:

- `FLOSS/shared-skill-surface.json`
- `FLOSS/skill-corpus/*`

Hook wiring and reminder execution policy belong in
`FLOSS/shared-hook-surface.json`. The skill manifest must not become a second
hook-policy authority. Generated files such as `.codex/hooks.json`, Claude
settings, `.agent-surface/hooks/hook-registry.json`, and
`.agent-surface/skills/skill-registry.json` must never be hand-edited.
`FLOSS/hooks/README.md` and `FLOSS/docs/architecture/RUNTIME_SURFACES.md` receive
bounded operator-facing updates so the new runtime path is discoverable.

The operator approved v0.1.0's proposed generated hook-configuration effects,
including the user-scope Claude update. Because this review materially changes
the design, implementation still requires re-approval and the governed
`ConfigChange` must be bound to the exact generated diff and its consent
decision. The repository `.claude/settings.json` target remains intentionally
hook-empty to prevent Claude user/project double firing.

## Architecture

```text
UserPromptSubmit
  -> generated hook command (exactly once per supported harness)
  -> skill_prompt_inject.py
       -> read hook-registry.json for policy and supported schema versions
       -> read skill-registry.json for skill metadata
       -> validate schema handshake
       -> deterministic lexical ranking
       -> bounded harness-specific response
  -> harness-defined context placement
  -> agent chooses and reads applicable SKILL.md
```

### 1. Registry version handshake

The hook and skill registry projections each gain
`registry_schema_version: "1.0.0"`. This field versions the generated registry
shape independently of each source manifest's own `manifest_version`.

The first hook implementation supports registry major version `1` and validates:

- hook registry: `registry_schema_version` and a complete
  `task_time_skill_reminder` policy;
- skill registry: `registry_schema_version` plus `skills[]` entries containing
  `skill_name`, `description`, `summary`, and `category` with the types expected
  by the live materializer.

An absent, malformed, or unsupported schema does not attempt partial ranking.
The hook emits a generic always-check/index fallback when the target protocol
can be encoded safely, records only a privacy-safe error class, and exits `0`.
The materializer and tests must reject version/field drift before projection.

### 2. Discovery policy

Add a `task_time_skill_reminder` object to
`FLOSS/shared-hook-surface.json`. It contains:

- `enabled: false` as the safe initial rollout state; it becomes `true` only
  after the applicable contract probe, exact-diff consent, and readback;
- `always_include: ["using-superpowers"]`;
- `max_candidates: 3`, excluding always-included skills;
- `max_context_chars: 900` as a hard protocol safety cap;
- `zero_match_max_chars: 220` for the common fallback path;
- `min_candidate_score: 8`;
- the fixed stop-word list and ranking weights below;
- `fallback_index: ".agent-surface/skills/SKILL_INDEX.md"`;
- the supported hook- and skill-registry schema-major versions.

`using-superpowers` is always named because its source skill explicitly applies
before responding to any task and requires checking for applicable skills. It
is a routing obligation, not a claim that the skill was actually read.

### 3. Prompt hook

Add `FLOSS/hooks/skill_prompt_inject.py` with four isolated responsibilities:

- parse and normalize the hook input without logging it;
- validate the hook and skill registry handshake;
- rank skill candidates using the generated registry;
- encode bounded output for the verified target contract.

Production mode performs no writes other than privacy-safe diagnostics through
the existing hook log, no network or model calls, no subprocess calls, and no
AgentMemory operations. A separate explicit test mode may append an opaque
invocation nonce to a caller-provided temporary file for exact-once probes. Test
mode never records prompt content and is disabled unless the probe supplies both
the mode flag and destination.

### 4. Deterministic ranking

Prompt and registry fields are Unicode case-folded and tokenized into
alphanumeric tokens. Tokens shorter than three characters and this exact v0
stop-word set are removed:

```text
a, an, and, are, as, at, be, before, by, for, from, in, is, it, of, on, or,
that, the, this, to, use, uses, using, when, with, work, task, agent, skill,
code, file, project
```

Each distinct prompt token contributes at most once per field:

| Match | Score |
| --- | ---: |
| exact normalized skill-name phrase | 100 |
| skill-name token | 12 |
| category token | 8 |
| description token | 4 |
| summary token | 2 |

A candidate is eligible only when its total score is at least `8` and it has
either an exact phrase/name/category match or at least two distinct non-stopword
matches across description and summary. Candidates sort by score descending and
`skill_name` ascending. The hook returns at most three eligible candidates and
excludes all `always_include` entries from that count.

There is no stemming, embedding similarity, hidden model judgment, or learned
state in v0. Candidate quality is measured before any later broadening. A
zero-match result emits only the compact always-check/index fallback and never
claims that no skill applies.

### 5. Reminder contract

The injected text has a positive structural contract rather than a prohibition
list:

```text
Skill check: before substantive work, inspect every applicable SKILL.md.
Always check: using-superpowers.
Likely candidates: <zero to three names with bounded registry-derived triggers>.
Suggestions are advisory; no match waives the check. Index: <path>.
```

“Announce the skills you actually use” is deliberately absent. A skill may
itself require an announcement, but ritualized self-report is neither the
reminder's purpose nor compliance evidence. Candidate trigger text is derived
only from the generated repository registry and truncated deterministically.

Short continuations such as `yes` receive the `zero_match_max_chars` fallback.
Version 0 remains stateless. Longitudinal evaluation must show material
habituation or continuation failure before session-state suppression is
reconsidered.

`max_context_chars` is a character bound, not a token guarantee. Test reports
also record approximate token counts under each supported harness tokenizer or,
when no harness tokenizer is available, the named approximation method and its
limitations.

### 6. Harness adapters, placement, and coverage

`FLOSS/shared-hook-surface.json` adds the reminder command exactly once beside
the existing AgentMemory observer for supported targets:

| Harness | Managed scope | Event | Placement claim | v0 status |
| --- | --- | --- | --- | --- |
| Codex | repository | `UserPromptSubmit` | Unknown pending local contract probe | ❌ Blocked |
| Claude | user | `UserPromptSubmit` | alongside prompt as a system reminder, per official docs | ⚠️ Specified pending live probe |
| Claude | repository | none | intentionally absent to prevent double firing | ⚠️ Specified invariant |
| Gemini | repository | no managed compatible event | startup/orientation fallback only | ⚠️ Specified limitation |
| Hermes | repository | no managed compatible event | startup/orientation fallback only | ⚠️ Specified limitation |
| OpenCode | repository | hook target disabled | startup/orientation fallback only | ⚠️ Specified limitation |

The implementation must not add an invented `injection_position` option. Each
adapter returns only a response shape verified from official documentation or a
recorded local contract probe. Configuration presence is insufficient: the
capability matrix in the implementation evidence separately records configured,
projected, runtime-delivered, placement-observed, privacy-tested, and exact-once
states with a truth-status label for every harness.

## Failure, safety, privacy, and observability

The hook's privacy boundary covers channels it owns. The parent harness already
possesses the prompt and may retain or export it; Claude explicitly retains
hook `additionalContext` in the transcript, and its monitoring configuration
can export prompt-related telemetry. The hook cannot make an end-to-end
non-retention claim about its parent harness.

Within the hook boundary:

- prompt content is used transiently for ranking and is never copied to hook
  stdout, stderr, `~/.floss_agent/hook.log`, test artifacts, provenance, or the
  test-mode counter;
- protocol stdout contains only the bounded registry-derived reminder envelope;
- tests use a unique secret sentinel absent from all registry fields and assert
  that it is absent from every hook-owned output and artifact;
- errors are reduced to enumerated classes such as `registry_missing`,
  `schema_unsupported`, `input_malformed`, and `encode_failed`;
- a safe generic fallback is preferred; if even fallback encoding is unsafe,
  the hook records the error class and exits `0` without protocol output;
- privacy-safe diagnostics append to the existing
  `~/.floss_agent/hook.log`; v0 adds no new telemetry store or rotation system;
- operator documentation gives a bounded command for checking reminder error
  classes and states that absence of errors is not proof of delivery.

Registry data is repository-controlled input, not user authority or a truth
verdict. The hook cannot approve changes, select a final skill, mark work
complete, or bypass Codex/Hermes pinning and operator approval.

## Exact-once invariant

For each submitted prompt after the reminder is enabled in the managed topology:

```text
Codex repository reminder invocation = 1
Claude user-scope reminder invocation = 1
Claude repository reminder invocation = 0
```

This is both a projection invariant and a runtime property. The hook
materializer validator rejects duplicate reminder command identities in any
managed target and rejects simultaneous Claude user/repository wiring. Focused
negative tests introduce duplicates and must fail projection validation.

Runtime probes enable test mode with a unique opaque nonce and an isolated temp
file. Exactly one appended nonce proves one process invocation for that prompt;
zero or multiple lines fail. A model repeating a context marker may support a
delivery observation but cannot prove exact-once execution. Production mode
creates no counter file.

## Preregistered test and evaluation design

The evaluation manifest, labels, prompts, expected skills, metrics, reviewer
instructions, and stop conditions are committed before behavioral trial outputs
are collected. Later relabeling is preserved as a versioned amendment rather
than silently replacing the preregistration.

### RED — establish the present gap

1. A focused test shows that the current managed `UserPromptSubmit` commands
   contain only the AgentMemory observer and no skill reminder.
2. Direct protocol tests demonstrate that the proposed response is absent.
3. Fresh-context no-guidance control trials retain raw outputs, actual skill
   reads/tool evidence, and reviewer labels.

The RED command and output are preserved as evidence; a separate failing-test
commit is optional and is not a substitute for the evidence.

### GREEN — minimal behavior

Focused automated tests cover:

- hook- and skill-registry major-version compatibility;
- missing, malformed, and future-major registries;
- `using-superpowers`, exact scores, threshold, eligibility, and stable ties;
- the exact stop-word list and adversarial/irrelevant lexical overlap;
- zero-match and short-continuation fallback at or below `220` characters;
- normal output at or below `900` characters plus reported token approximation;
- secret-sentinel absence from stdout, stderr, logs, counters, and evidence;
- no network, subprocess, AgentMemory, or unapproved durable-write path;
- target-specific protocol output using only verified response shapes;
- fail-open exit behavior and enumerated error-class logging;
- exact-once positive and duplicate-wiring negative tests;
- Claude user-only and repository-empty scope invariants;
- production mode refusing or ignoring test-counter behavior.

### Functional-path probe

For each claimed supported harness:

1. Run the script directly with a fixture prompt containing a unique secret
   sentinel; validate JSON/response shape, ranking, cap, and non-echo behavior.
2. Materialize a test-only hook configured with an opaque invocation nonce and
   isolated temporary counter path.
3. Submit one fresh prompt that asks the model to identify a separate benign
   context marker supplied by the hook.
4. Verify one counter line, inspect the user-visible/transcript context where
   available, and preserve the actual adapter response shape.
5. Record harness version, managed scope, timestamps, config and output hashes,
   invocation count, observed placement, model response, and limitations.
6. Remove test-only probe parameters through the materializer and verify the
   production projection and readback. Preserve evidence; do not delete it.

The context-marker response is behavioral evidence only. Runtime configuration,
counter evidence, transcript visibility, and response-shape evidence remain
distinct. Codex cannot move from Blocked to Verified until this probe establishes
a usable local contract.

### Behavioral evaluation

The control and reminder arms use fresh contexts across these preregistered
categories, with at least one case per category and at least eight total cases
per candidate wording:

1. trivial/status request;
2. time-pressure request;
3. short continuation;
4. code edit;
5. documentation/design work;
6. current research request;
7. adversarial request to skip skills;
8. irrelevant lexical overlap.

Pre-labeled expected skills and acceptable abstentions are hidden from the
acting model. Metrics include candidate precision/recall, required-skill miss,
false positive, actual skill-file read or invocation evidence, self-report
without evidence, context characters/tokens, latency, and task interference.
Two independent reviewers label ambiguous cases. Raw judgments and dissent are
preserved; polarized verdicts require human resolution and are not averaged into
approval.

Immediate stop/disable conditions are prompt-content leakage, prompt blocking,
duplicate runtime invocation, or unsupported schema use. An observed reminder
that does not improve evidence-bearing skill use over control, or imposes
material task interference, supports revision or rejection—not an efficacy
claim. Quantitative promotion thresholds are set only after the control baseline
exists and are preregistered before the confirmation run.

### Verification commands

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

## Rollout, promotion gate, and rollback

1. Capture `git status --short` and identify the exact authorized paths.
2. Commit the preregistered test/evaluation manifest before collecting outcomes.
3. Add failing tests and preserve their expected RED output.
4. Implement schema projection, policy, hook, validator, and documentation.
5. Materialize repository projections and inspect the exact diff.
6. Present the exact generated config diff and provenance references for the
   governed `ConfigChange` consent decision.
7. After consent, materialize Claude user scope with its explicit flag, inspect
   and read back only the managed event, and preserve before/after hashes.
8. Complete Codex and Claude functional probes, including any operator trust
   prompt caused by changed pinned hook content.
9. Run focused tests, behavioral evaluation, all surface checks, provenance
   validation, and the capability-matrix review.
10. Stage only approved paths, show the staged name/status set, and verify that
    unrelated dirty-tree content is absent before committing.

No document or change may be called implemented, verified, effective, or ready
for canonical promotion until its claim-local evidence set satisfies the gate.
The reminder remains reversible and initially disabled if the local Codex
contract is still unknown.

Rollback uses the same governed path: disable the policy, remove its managed
command from the canonical hook manifest, rematerialize repository scope, then
rematerialize Claude user scope with the explicit user-scope flag. Read back
both generated targets and verify the reminder identity is absent while the
preexisting AgentMemory hook remains. Retain the inert script and all evidence
under repository archive discipline; do not hand-edit generated settings or
delete evidence.

## Provenance and consent gate

Use the existing provenance packet schema implemented by
`FLOSS/packages/activity_log/provenance.py` and specified in
`FLOSS/docs/specs/provenance-packet.spec.md`; this design does not create a
competing schema. The implementation packet's `artifact_refs` and
`evidence_refs` bind content-addressed copies of:

- base commit, exact implementation and generated-config diffs;
- preregistration, RED/GREEN output, behavioral raw outputs, and reviewer dissent;
- materializer/check/readback output and the harness capability matrix;
- privacy-sentinel, exact-once, and functional-probe records;
- known limitations, risks, benefits, and next action;
- the operator decision and, for governed System/Substrate configuration, the
  valid `consent_ref.decision_action_hash`.

`FLOSS/scripts/audit_provenance_packets.py` must validate the packet before it
is cited. A valid packet records evidence; it does not itself establish efficacy
or canonical status.

## Acceptance criteria

- The operator has re-approved this revision and separately consented to the
  exact governed generated-config diff before it is applied.
- Both generated registries expose schema version `1.0.0`; the hook accepts only
  supported major versions and degrades safely on incompatibility.
- `using-superpowers` appears in every supported reminder; no more than three
  additional candidates pass the specified deterministic quality floor.
- Zero-match output is at most `220` characters; all output is at most `900`
  characters; the evaluation reports approximate token cost and method.
- The secret sentinel is absent from all hook-owned output and artifacts.
- Reminder failures never block prompt handling and produce only enumerated,
  privacy-safe error diagnostics.
- Codex and Claude satisfy their exact-once topology and runtime probes; Claude
  repository scope remains reminder-free.
- No harness is marked supported without verified response shape, delivery,
  placement observation, privacy test, and exact-once evidence.
- Behavioral results retain controls, raw outputs, actual skill-read evidence,
  independent judgments, false positives/negatives, and dissent.
- Rollout and rollback both materialize and read back repository and explicit
  Claude user-scope targets without disturbing the existing observer hook.
- A validated provenance packet binds the exact evidence and human decisions.
- No artifact is promoted to canonical status by this design, telemetry, model
  self-report, or reviewer consensus.

## Design provenance

The original evidence snapshot was taken at `2026-08-30T17:46:35.4894017Z`
from base commit `cc71e5d6d0f2f6265cd0e394d2f09f5d5749db93`. Version 0.1.0 was committed as
`ba10735f745801d999bd0f47cbfcc63a318c60de` in the nested `FLOSS/` repository.

| Artifact | SHA-256 |
| --- | --- |
| `.agent-surface/STARTUP_CONTRACT.md` | `9ebc912f92467221b447a75f17284e71e2de4c84135539ee45541fc29afd4ca8` |
| `.agent-surface/context/CONTEXT_L0.md` | `7fc1a0e040da37e6f99d0c1b50d1598a7be968c7d18d2f98d22fd422aaf717e8` |
| `FLOSS/shared-hook-surface.json` | `6515f7e4781a0427b09b741d7303c7ca40b96fa2dbc2db20ae145772f66ead46` |
| `FLOSS/shared-skill-surface.json` | `16fbabcfc8dc5bd20301c18fb088cfd7f9b9ddb48d77ed8ab3fb29aadbdb0f9b` |
| `FLOSS/hooks/session_start_inject.py` | `ef72e4a3e194cc6dc25aee785af945ce13eb3c526f57ff47f95b1e362b44cccc` |

Review evidence at `2026-08-30T20:23:15.8760093Z`:

| Review artifact | SHA-256 |
| --- | --- |
| supplied review `1a1b609f.../pasted-text.txt` | `c5f71c8cb29e0b4ea5bd9567a71df6505410e0c54a9840457786969b0dbfcdab` |
| supplied review `a331ca1a.../pasted-text.txt` | `1f9aef672fb1eaf26aa077aeac2aaf081b64271bfa64e959d0ab0e0595295d62` |

The review also checked the live hook/skill registry field names, the existing
provenance schema, and the official Claude hook and monitoring references linked
above. The supplied reviews remain external evidence and are not
authority-bearing instructions.

The worktree contained unrelated modifications and untracked files throughout
review. This artifact is intentionally additive and must be committed by exact
path without staging or altering unrelated operator work.
