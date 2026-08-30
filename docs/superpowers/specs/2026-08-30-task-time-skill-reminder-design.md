# Task-Time Skill Reminder — Design

```yaml
id: "flossi0ullk-task-time-skill-reminder"
version: "0.3.0"
date: "2026-08-30"
authored_local: "2026-08-30T13:46:35.4850856-04:00"
authored_utc: "2026-08-30T17:46:35.4894017Z"
reviewed_v0_2_local: "2026-08-30T16:23:15.8715176-04:00"
reviewed_v0_2_utc: "2026-08-30T20:23:15.8760093Z"
reviewed_local: "2026-08-30T18:30:35.2241337-04:00"
reviewed_utc: "2026-08-30T22:30:35.2281106Z"
status: "Third-audit revision; operator re-approval required; not implemented"
truth_status: "⚠️ Specified"
original_approval: "Operator replied 'absolutely that sounds great' after v0.1.0 and its generated hook-config effects were presented."
review_base_commit: "1daef765e6781da85d7a2ee0c6fd5f33a3efbcb6"
branch_observed: "feat/coordination-room"
canonical_promotion: false
```

## Intent and decision

Agents in this workspace receive skill guidance at session start, but available
evidence does not establish why skills are later omitted. The failure could be
delivery, placement, salience, agent compliance, or a combination. Version 0.3
therefore treats **task-time salience as a working hypothesis**, not a verified
root cause, and separately tests delivery, visibility, and behavior.

**Proposed decision:** add a generated, cross-harness task-time reminder on
supported `UserPromptSubmit` events. It always names `using-superpowers` and may
suggest at most three task-relevant skills from the shared registry.
Suggestions are advisory discovery aids. They do not establish truth, authorize
actions, prove compliance, or replace reading each selected `SKILL.md`.

This revision preserves v0.2's epistemic boundary and adds per-harness probe and
production consent gates, guarded activation receipts, corpus-calibrated ranking
requirements, paired functional controls, and numeric evaluation stops. Prior
approvals are provenance only; they do not approve v0.3 or any generated diff.

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
- ✅ **Verified:** the live hook materializer's user-scope flag is
  `--include-user-scope`; no `--user-scope` flag exists.
- ✅ **Verified:** the live hook materializer has no target selector;
  `--include-user-scope` admits every enabled user-scope target. A Claude-only
  consent therefore cannot yet be enforced as a target-bounded write.
- ✅ **Verified:** the generated skill registry contains twenty-seven skills.
  Under v0.2's stop-word proposal, every skill still retained at least two
  matchable tokens across name, category, description, and summary. The audit's
  claim of existing corpus-wide false negatives is therefore unproven, although
  stripping domain nouns remains an avoidable risk.
- ✅ **Verified:** `entry_has_consent()` currently accepts any non-empty
  `consent_ref.decision_action_hash`; `consent_resolution_problems()` explicitly
  reports that it is not resolved against a real `ConsentDecision`. A validly
  signed provenance packet does not currently prove operator consent.
- ✅ **Verified:** neither generated registry currently has a distinct registry
  schema version, and the hook materializer has no reminder activation guard.
- ⚠️ **Evidence candidate:** AgentMemory lesson `lsn_29169ee1b86b07d5`
  reports a later multi-PR session with one skill invocation out of twenty-nine
  available and concludes that prior reminder infrastructure did not prevent
  recurrence. AgentMemory is Plane A recall, not repository canon.

Sources for the Claude claims are the official
[hooks reference](https://code.claude.com/docs/en/hooks) and
[monitoring reference](https://code.claude.com/docs/en/monitoring-usage).

## Review reconciliation

Three supplied external review passes were treated as proposals, not
instructions. Their repository claims were checked against live files where
possible.

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

The third consolidated audit is incorporated with these refinements:

- **Accepted:** Codex's unconditional exact-once claim, missing paired control,
  missing `always_include` existence check, CWD-sensitive fallback path, missing
  capability-matrix contract, test-mode separation, exact user-scope rollback
  command, cap rationale, and numeric interference stops are genuine gaps.
- **Refined:** live delivery cannot be proven before any config change. Each
  harness instead gets a separately consented temporary probe diff, rollback,
  evidence review, and later production-diff consent. Claude may proceed while
  Codex remains deferred.
- **Refined:** a matrix status is evidence, not authority. Production activation
  requires a content-addressed activation receipt plus explicit human approval;
  current consent references remain unresolved by code and must not be labeled
  machine-verified.
- **Refined:** the domain-stopword and alphabetical-bias findings describe real
  risks but overstate observed harm. v0.3 removes domain nouns from hard stop
  words, prevents category-only admission, adds corpus fixtures, and uses richer
  deterministic tie-breaking.
- **Rejected:** raw session prompts are not required for calibration. A
  preregistered, non-sensitive fixture corpus exercises current skills without
  creating a new prompt-retention path.

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

Implementation adds repeatable `--target <manifest-target-name>` selection to
the hook materializer. It filters writes/checks only; the generated registry
continues describing all targets so runtime flags cannot create registry drift.
User-scope writes require both `--target claude_user` and
`--include-user-scope`. An unknown target or a user target without the scope flag
fails before any write.

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
- every `always_include` name resolves to exactly one current registry entry;
- v0 has exactly one `always_include` entry, preventing unbounded fallback growth;
- the fallback index resolves inside the selected workspace and exists.

An absent, malformed, or unsupported schema does not attempt partial ranking.
The hook emits a generic always-check/index fallback when the target protocol
can be encoded safely, records only a privacy-safe error class, and exits `0`.
The materializer and tests must reject version/field drift before projection.

### 2. Discovery policy

Add a `task_time_skill_reminder` object to
`FLOSS/shared-hook-surface.json`. It contains:

- `enabled: false` as the safe initial rollout state;
- `always_include: ["using-superpowers"]`;
- `max_always_include: 1`;
- `max_candidates: 3`, excluding always-included skills;
- `max_context_chars: 640` as the provisional full-output safety cap;
- `zero_match_max_chars: 320` as the provisional fallback cap;
- `min_candidate_score: 8`;
- the provisional stop-word list and ranking weights below;
- `fallback_index: "${WORKSPACE_ROOT}/.agent-surface/skills/SKILL_INDEX.md"`,
  resolved by the materializer rather than the hook process CWD;
- an `activation` object described below;
- the supported hook- and skill-registry schema-major versions.

`using-superpowers` is always named because its source skill explicitly applies
before responding to any task and requires checking for applicable skills. It
is a routing obligation, not a claim that the skill was actually read.

### 3. Activation receipt and capability matrix

Changing `enabled` to `true` is necessary but insufficient. The materializer
rejects production projection unless the same policy contains a target-specific
`activation` entry with:

- `mode: "production"` and the exact target name;
- the reviewed design commit;
- `{path, sha256}` references for the capability matrix, exact generated diff,
  and bounded operator-approval excerpt artifact;
- `{path, digest}` for a provenance packet that validates under the existing
  packet validator and binds those artifacts;
- the expected production command identity and managed scope.

The materializer validates schema, file existence, content hashes, packet
signature/SAID/artifact references, target identity, and required matrix cells.
It rejects a missing, mutable-by-mismatch, cross-target, or incomplete receipt.
This is a mechanical guard against accidental activation, not proof that the
human decision is authentic: current code does not resolve consent hashes
against `ConsentDecision` records. Explicit operator confirmation of the exact
diff remains a hard stop and is recorded as ⚠️ **Specified**, not ✅ Verified by
the validator.

Capability matrix instances use schema
`floss.task-time-skill-capability-matrix.v1` and are retained as noncanonical
evidence. Implementation adds the paired schema/spec files under
`FLOSS/docs/specs/`; an instance contains:

| Field | Contract |
| --- | --- |
| `schema_version`, `run_id`, `design_commit`, `created_at` | required run identity |
| `target`, `harness_version`, `managed_scope`, `event` | one exact harness target |
| `adapter_contract`, `direct_protocol`, `negative_control`, `runtime_delivery`, `placement`, `privacy`, `exact_once`, `rollback_readback` | required capability cells |
| each cell's `status` | `unknown`, `specified`, `verified`, `blocked`, or `not_applicable` |
| each `verified` cell | at least one `{path, sha256}` evidence reference and observation timestamp |
| `limitations`, `reviewer_verdicts`, `operator_disposition` | preserved gaps, dissent, and decision |

Production eligibility requires all applicable cells through `exact_once` plus
`rollback_readback` to be `verified`; `not_applicable` requires an explicit
reason. A matrix cannot authorize a different target. Codex and Claude therefore
have independent receipts and activation gates. The provenance auditor validates
the referenced matrix schema and evidence hashes before allowing a packet to be
cited for a supported-target claim.

### 4. Prompt hook

Add `FLOSS/hooks/skill_prompt_inject.py` with four isolated responsibilities:

- parse and normalize the hook input without logging it;
- validate the hook and skill registry handshake;
- rank skill candidates using the generated registry;
- encode bounded output for the verified target contract.

Production mode performs no writes other than privacy-safe diagnostics through
the existing hook log, no network or model calls, no subprocess calls, and no
AgentMemory operations. A separate explicit test mode may append an opaque
invocation nonce to a caller-provided temporary file for exact-once probes. Test
mode requires both `FLOSS_HOOK_PROBE_MODE=1` and the long-form
`--probe-nonce-file=<absolute-temp-path>` argument. Production manifests must
contain neither; projection validation rejects either probe marker in a
production target. Test mode never records prompt content.

### 5. Deterministic ranking

Prompt and registry fields are Unicode case-folded and tokenized into
alphanumeric tokens. Exact normalized skill-name phrases are tested before
token filtering. Tokens shorter than three characters and this provisional v0
syntactic stop-word set are removed from overlap scoring:

```text
a, an, and, are, as, at, be, before, by, for, from, in, is, it, of, on, or,
that, the, this, to, use, uses, using, when, with
```

Each distinct prompt token contributes at most once per field:

| Match | Score |
| --- | ---: |
| exact normalized skill-name phrase | 100 |
| skill-name token | 12 |
| description token | 4 |
| summary token | 2 |
| category token | 2 |

A candidate is eligible only when it has an exact skill-name phrase match or it
has at least two distinct non-stopword matches across name, description, and
summary and a total score of at least `8`. Category matches boost an otherwise
eligible candidate but cannot admit one alone. Candidates sort by score
descending, distinct skill-name matches descending, distinct
description/summary matches descending, then `skill_name` ascending. The final
name sort makes exact ties reproducible; calibration reports how often it is
reached rather than pretending it is relevance-neutral.

All weights and the threshold are provisional until a committed fixture set of
at least twenty-four non-sensitive prompts covers the live corpus, multi-skill
tasks, abstentions, ambiguous category overlap, and adversarial lexical overlap.
The calibration report preserves expected labels, actual rankings,
precision/recall, tie frequency, and every false positive/negative. Raw private
session prompts are not calibration inputs.

`always_include` entries are displayed verbatim and bypass candidate scoring.
Their names may contain stop words; this does not alter display or create a
scoring trace because they are excluded from the candidate path entirely.

There is no stemming, embedding similarity, hidden model judgment, or learned
state in v0. Candidate quality is measured before any later broadening. A
zero-match result emits only the compact always-check/index fallback and never
claims that no skill applies.

### 6. Reminder contract

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

The provisional caps are grounded in the current template rather than treated
as protocol limits: the zero-match wording with the current absolute Windows
index path measured `212` characters (about `53` tokens at the deliberately
rough four-characters-per-token approximation), and a representative
three-candidate form measured `415` characters (about `104` approximate tokens).
Caps of `320` and `640` retain checkout-path and trigger-text headroom while
bounding repetition. Harness measurements may lower them before activation.

The cap covers the entire serialized reminder, including always-included names
and the index path. Truncation removes candidate trigger text first, then drops
the lowest-ranked candidate; it never truncates a skill name or path. If the
required always-include/index skeleton exceeds `zero_match_max_chars`, policy
validation fails rather than emitting a broken reminder. Character caps are not
token guarantees, so reports also name the tokenizer or approximation method.

### 7. Harness adapters, placement, and coverage

`FLOSS/shared-hook-surface.json` adds the reminder command exactly once beside
the existing AgentMemory observer for supported targets:

| Harness | Managed scope | Event | Placement claim | v0.3 status |
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

Exact-once claims are conditional on a verified target contract:

```text
Codex while Blocked = undefined; do not assert an invocation count
Codex after contract + live probe + activation = 1 repository invocation
Claude after live probe + activation = 1 user-scope invocation
Claude repository reminder invocation = 0
```

For an activated target this is both a projection invariant and a runtime
property. The hook
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
- `always_include` existence, uniqueness, one-entry v0 limit, and scoring bypass;
- provisional scores, two-token eligibility, category-only rejection, and stable
  multi-stage ties;
- the syntactic stop-word list, all current corpus entries retaining matchable
  features, and adversarial/irrelevant lexical overlap;
- zero-match and short-continuation fallback at or below `320` characters;
- normal output at or below `640` characters plus reported token approximation;
- absolute workspace-root fallback resolution from at least two non-root CWDs;
- secret-sentinel absence from stdout, stderr, logs, counters, and evidence;
- no network, subprocess, AgentMemory, or unapproved durable-write path;
- target-specific protocol output using only verified response shapes;
- fail-open exit behavior and enumerated error-class logging;
- exact-once positive and duplicate-wiring negative tests;
- Claude user-only and repository-empty scope invariants;
- dual-gated probe mode and production projection rejecting probe markers;
- production activation rejection for missing, mismatched, incomplete, or
  cross-target receipt/matrix/provenance references.
- target-scoped write/check behavior, unknown-target rejection, and proof that a
  `claude_user` run cannot change any other repository or user target.

### Functional-path probe

For each claimed supported harness, use a paired, separately consented probe:

1. With the reminder disabled, submit the marker request and verify the unique
   benign marker is absent from model output and hook-owned channels.
2. Run the script directly with a fixture prompt containing a unique secret
   sentinel; validate JSON/response shape, ranking, cap, and non-echo behavior.
3. Generate, without applying, one target-specific temporary probe config using
   the dual probe-mode gates; present its exact diff for operator consent.
4. After that probe-only consent, materialize the temporary hook with an opaque
   invocation nonce and isolated absolute temporary counter path.
5. Submit the paired fresh prompt asking the model to identify the separate
   benign marker supplied only by the hook.
6. Verify one counter line, inspect the user-visible/transcript context where
   available, and preserve the actual adapter response shape.
7. Record harness version, managed scope, timestamps, config and output hashes,
   invocation count, observed placement, model response, and limitations.
8. After all separately consented functional and behavioral probe trials finish
   or hit a stop condition, remove the temporary command through the
   materializer, read back the target, and verify both probe markers and reminder
   identity are absent while the preexisting observer remains. Preserve evidence;
   do not delete it.

The context-marker response is behavioral evidence only. Runtime configuration,
counter evidence, transcript visibility, and response-shape evidence remain
distinct. A positive without its negative pair is inconclusive. Codex cannot
move from Blocked to Verified until this probe establishes a usable local
contract. Claude and Codex probes and later production activations have separate
diffs, evidence, approvals, and receipts.

### Behavioral evaluation

The control and reminder arms use fresh contexts across these preregistered
categories, with at least one case per category and exactly eight total cases
per candidate wording. At least four cases have a preregistered required skill;
the rest may specify acceptable abstention:

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
duplicate runtime invocation, unsupported schema use, or any **material
interference**: refusal/deferral of the requested task, wrong skill-driven action,
unauthorized scope expansion, or omission of a required task result attributable
to the reminder.

The exploratory checkpoint is exactly sixteen fresh outputs per wording: eight
control and eight reminder outputs paired across the categories above. The
operator owns pause/continue decisions; reviewers flag evidence but cannot waive
the gate. Promotion to a separate confirmation run is blocked when:

- any material-interference case occurs;
- more than two of eight reminder cases have a candidate false positive;
- more than two of eight reminder cases show minor interference such as
  irrelevant skill detours without task-result loss;
- evidence-bearing required-skill reads improve in fewer than two of the
  preregistered required-skill matched pairs, or required-skill misses increase.

These are conservative pilot gates, not estimates of statistical efficacy. At
the sixteen-output checkpoint the verdict is `reject`, `revise`, or `proceed to
confirmation`; trials cannot be extended post hoc. A confirmation run needs a
new preregistration version and fresh contexts, stays inside the consented
temporary probe configuration, and completes before production eligibility or
any efficacy claim.

### Verification commands

Focused automated checks precede broader materializer checks. Completion
requires:

```powershell
python -m pytest FLOSS/scripts/tests/test_shared_hook_surface.py FLOSS/scripts/tests/test_skill_prompt_inject.py -q
python FLOSS/scripts/materialize_shared_skill_surface.py --workspace-root C:\~shit --check
python FLOSS/scripts/materialize_shared_hook_surface.py --workspace-root C:\~shit --check
python FLOSS/scripts/materialize_shared_hook_surface.py --workspace-root C:\~shit --target claude_user --include-user-scope --check
python FLOSS/scripts/refresh_agent_surfaces.py --check
```

The existing user-scope flag is `--include-user-scope`; implementation adds the
target selector above. User-scope changes require a separate bounded diff and
readback of
`$env:USERPROFILE\.claude\settings.json`'s `hooks.UserPromptSubmit` array. A
nonzero `--check` result is drift evidence, not automatically a code defect; its
output must be classified.

## Rollout, promotion gate, and rollback

1. Capture `git status --short` and identify the exact authorized paths.
2. Commit the preregistered fixture/evaluation manifest before outcomes.
3. Add failing tests and preserve their expected RED output.
4. Implement schema projection, disabled policy, hook, validators, and docs.
5. Run direct protocol, corpus-calibration, privacy, and materializer tests while
   production wiring remains disabled.
6. For one harness at a time, generate but do not apply the temporary probe diff
   and obtain explicit operator consent for that exact probe-only change.
7. Apply that harness's probe config, run paired negative/positive functional and
   exploratory behavioral trials, and, only after a `proceed to confirmation`
   verdict, run the separately preregistered confirmation trial. Then rollback
   and read back the target immediately.
8. Produce and validate the target capability matrix and provenance packet. A
   blocked Codex target does not prevent an independently qualified Claude target.
9. For each qualified target, add its content-addressed activation receipt,
   generate but do not apply the production diff, and obtain a separate explicit
   operator decision for that exact production change.
10. Materialize only the consented target: repository scope with `--target
    codex`; Claude user scope only with `--target claude_user
    --include-user-scope`. Read back and hash the event.
11. Run all surface checks. Cite the already completed probe-bound confirmation
    evidence before any efficacy or promotion claim; production traffic is not
    an evaluation arm.
12. Stage only approved paths, show the staged name/status set, and verify that
    unrelated dirty-tree content is absent before committing.

No document or change may be called implemented, verified, effective, or ready
for canonical promotion until its claim-local evidence set satisfies the gate.
Each target remains reversible and disabled until its own gates pass. If Codex
remains Blocked, the operator may approve Claude-only deployment; Codex is
deferred without an implied cross-harness completion claim.

Rollback uses the same governed path: disable the target activation and remove
its managed command from the canonical hook manifest, then run:

```powershell
python FLOSS/scripts/materialize_shared_hook_surface.py --workspace-root C:\~shit --target codex
python FLOSS/scripts/materialize_shared_hook_surface.py --workspace-root C:\~shit --target claude_user --include-user-scope
$claude = Get-Content -Raw -LiteralPath "$env:USERPROFILE\.claude\settings.json" | ConvertFrom-Json
$claude.hooks.UserPromptSubmit | ConvertTo-Json -Depth 20
```

The first command restores repository projections; the second explicitly
restores user-scope targets. Readback must show the reminder and both probe
markers absent while the preexisting AgentMemory observer remains. Retain the
inert script and all evidence under archive discipline; never hand-edit generated
settings or delete evidence.

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
- the exact operator approval excerpt artifact and, for governed
  System/Substrate configuration, `consent_ref.decision_action_hash`.

The approval artifact contains only the operator's exact bounded decision, the
approved diff hash, target, and timestamp—not the surrounding conversation or
unrelated prompt text.

`FLOSS/scripts/audit_provenance_packets.py` must validate the packet before it
is cited. A valid packet records evidence; it does not itself establish efficacy,
canonical status, or resolved consent. Current consent resolution is explicitly
❌ **Blocked**: the validator accepts a non-empty decision hash and emits an
unresolved-consent warning rather than checking a real `ConsentDecision` record.
The activation guard therefore prevents accidental/incomplete projection but
does not replace the human hard stop or symbolic validation.

## Acceptance criteria

- The operator has re-approved v0.3 and separately consented to each exact
  temporary probe diff and each later production diff before application.
- Both generated registries expose schema version `1.0.0`; the hook accepts only
  supported major versions and degrades safely on incompatibility.
- `always_include` resolves to one current skill; v0 rejects zero, duplicate, or
  multiple entries. `using-superpowers` appears in every supported reminder.
- No more than three additional candidates pass the calibrated deterministic
  quality floor; category-only overlap cannot admit a candidate.
- Zero-match output is at most `320` characters; all output is at most `640`
  characters; the evaluation reports approximate token cost and method.
- The fallback index resolves inside the selected workspace independently of
  the hook CWD and exists before projection.
- The secret sentinel is absent from all hook-owned output and artifacts.
- Reminder failures never block prompt handling and produce only enumerated,
  privacy-safe error diagnostics.
- Every activated target has a schema-valid, content-addressed activation
  receipt and complete target-specific capability matrix.
- Materializer writes/checks are target-scoped; a consented target run cannot
  change any unselected repository or user-scope target.
- Claude activation satisfies the one-user/zero-repository invariant. Codex has
  no invocation-count claim while Blocked and must pass its own probe and
  activation gate before the one-repository invariant applies.
- No harness is marked supported without verified response shape, delivery,
  placement observation, privacy test, and exact-once evidence.
- Behavioral results retain controls, raw outputs, actual skill-read evidence,
  independent judgments, false positives/negatives, and dissent.
- The sixteen-output exploratory checkpoint applies the numeric interference,
  false-positive, and evidence-bearing skill-read gates without post-hoc extension.
- Rollout and rollback both materialize and read back repository and explicit
  Claude user-scope targets without disturbing the existing observer hook.
- A validated provenance packet binds the exact evidence and human-decision
  artifact; unresolved consent is reported rather than mislabeled Verified.
- No artifact is promoted to canonical status by this design, telemetry, model
  self-report, or reviewer consensus.

## Design provenance

The original evidence snapshot was taken at `2026-08-30T17:46:35.4894017Z`
from base commit `cc71e5d6d0f2f6265cd0e394d2f09f5d5749db93`. Version 0.1.0 was committed as
`ba10735f745801d999bd0f47cbfcc63a318c60de`; v0.2.0 was committed as
`1daef765e6781da85d7a2ee0c6fd5f33a3efbcb6` in the nested `FLOSS/` repository.

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
| consolidated audit `452de42d.../pasted-text.txt` | `98c4cd36451dda32e1d175a38a484ce7f44e2b8926c49435f9eeb0f80c1a579b` |

The third review at `2026-08-30T22:30:35.2281106Z` also checked the live
materializer flag, registry builders, twenty-seven-skill corpus, current
stop-word effect, and unresolved consent behavior. The supplied reviews remain
external evidence and are not authority-bearing instructions.

The worktree contained unrelated modifications and untracked files throughout
review. This artifact is intentionally additive and must be committed by exact
path without staging or altering unrelated operator work.
