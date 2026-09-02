# Polyglot Evolving Plugin and Materializer — Design

```yaml
id: "flossi0ullk-polyglot-evolving-plugin-materializer"
version: "0.1.0"
date: "2026-09-01"
authored_local: "2026-09-01T21:21:47.2366418-04:00"
authored_utc: "2026-09-02T01:21:47.2438319Z"
status: "Operator-selected topology; written-spec review required; not implemented"
truth_status: "⚠️ Specified"
base_commit: "a15f5f321d9a98a2553040f1d740d72e531724c8"
branch_observed: "feat/coordination-room"
governed_by: "ADR-18 Prior-Art & Reuse Gate"
canonical_promotion: false
```

## Intent and decision

FLOSSI0ULLK needs one installable identity that makes the shared skill corpus,
task-time skill discovery, MCP services, hook adapters, and later governed
harness evolution available across heterogeneous agent clients. It must not
replace Git-governed sources with a generated package, silently rewrite user
configuration, or let model-generated changes promote themselves.

**Selected decision:** materialize one physical polyglot plugin directory named
`flossi0ullk-evolution`. The directory carries both the published Agent Plugins
1.0.0 layout and the current OpenAI plugin layout. Shared components exist once
where their formats agree; dialect-specific manifests and MCP serializations
coexist as separate generated files.

The package is one distribution artifact and one provenance subject. It is not
the source of truth. The existing repository manifests, skill corpus, code,
governance, and human decisions remain upstream authority.

This design integrates, but does not rename as ADR-18:

- the noncanonical Antigravity materializer reuse plan;
- the task-time skill-reminder design;
- current Agent Plugins and OpenAI plugin contracts;
- the existing agent, hook, and skill materializers; and
- the governed skill/harness evolution research.

ADR-18 is only the accepted prior-art and reuse gate governing this work.

## Verified evidence and corrected claims

- ✅ **Verified:** Agent Plugins 1.0.0 defines a plugin as one directory with
  root `plugin.json`, fixed `skills/`, and optional root `mcp.json`.
- ✅ **Verified:** Agent Plugins §4.2 shows non-core siblings such as `LICENSE`,
  `CHANGELOG.md`, and a client extension directory in the standard layout.
- ✅ **Verified:** Agent Plugins §7 states that v1 defines exactly two component
  types and that other component types are outside v1 and do not affect
  conformance.
- ✅ **Verified:** the Agent Plugins `plugin.json` and `mcp.json` schemas are
  closed. This constrains the contents of those two documents, not every sibling
  file in the plugin directory.
- ✅ **Verified:** OpenAI's current package contract uses
  `.codex-plugin/plugin.json` and may discover `skills/`, `hooks/hooks.json`, and
  `.mcp.json` at the same plugin root.
- ✅ **Verified:** official OpenAI administration documentation recognizes both
  native OpenAI plugins and Agent Plugins 1.0 packages as marketplace sources.
- ✅ **Verified:** official Codex hook documentation now specifies
  `UserPromptSubmit`, including nonblocking `additionalContext`. The older
  documentation-level Codex blocker in the task-time reminder design is stale.
- ✅ **Verified:** AllAgents tag `v1.13.4` exists and its pinned source supports
  skills, hooks, MCP servers, and Codex plugin manifests. The observed npm latest
  version on 2026-09-01 was `1.13.5`; upgrading is a separate reuse-gate decision.
- ✅ **Verified:** current repo-scope agent, hook, and skill materializer
  `--check` runs all exited `0` on 2026-09-01. User-scope targets were skipped
  without `--include-user-scope`.
- ✅ **Verified:** a noncanonical combined-directory fixture passed the installed
  OpenAI plugin validator and the Agent Plugins 1.0.0 JSON schemas pinned at
  specification commit `ff8ab5e392cc87bd88d87c060815a87490e51003`.
- ⚠️ **Specified:** a conformant Agent Plugins loader should ignore the OpenAI
  files because it discovers its supported components only at fixed locations.
  The schema and layout checks support this, but a real client-load trace is
  still required.
- ❌ **Blocked:** official documentation does not establish loader precedence
  when a directory contains both root `plugin.json` and
  `.codex-plugin/plugin.json`. A real OpenAI install/load probe must prove which
  dialect is selected before the package can be promoted.

Corrections to supplied reviews:

- Agent Plugins 1.0.0 is the published target; 1.1.0 is a working draft.
- Agent Plugins does not standardize hooks in v1.
- in-toto structures attestations but does not itself sign them or establish a
  trust root.
- no SLSA level is claimed without a defined builder, threat model, provenance
  producer, and verification policy.
- `fcntl.flock()` is not the Windows-compatible concurrency answer.
- `uv.lock` cannot pin the Node-distributed AllAgents dependency.
- OPA/Rego remains a possible future policy engine, not a justified dependency
  for the current bounded rule set.
- estimates such as “one command,” “three lines,” or “zero cost” are not
  verification evidence.

Primary external references:

- [Agent Plugins Specification 1.0.0](https://github.com/agentplugins/agent-plugins-spec/blob/main/spec/1.0.0.md)
- [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins)
- [OpenAI plugin management](https://learn.chatgpt.com/docs/enterprise/plugin-management)
- [Codex hooks](https://learn.chatgpt.com/docs/hooks)
- [AllAgents v1.13.4 source](https://github.com/EntityProcess/allagents/tree/046f26c450bc4d451c95034b4bac82bf4677419a)

## Authority and source boundaries

The proposed package assembly descriptor is
`FLOSS/shared-plugin-surface.json`. It owns only package identity, component
selection, dialect versions, output location, and validation policy. It refers
to rather than duplicates these authorities:

| Concern | Authoritative input |
| --- | --- |
| MCP services | workspace `.mcp.json` plus `FLOSS/shared-agent-surface.json` |
| hook policy | `FLOSS/shared-hook-surface.json` |
| skill membership and metadata | `FLOSS/shared-skill-surface.json` |
| skill contents | `FLOSS/skill-corpus/*` |
| runtime and architecture constraints | repository canon and accepted ADRs |
| human approval | exact bounded operator decision artifact |

`shared-plugin-surface.json` is only proposed by this document. Creating it as
a canonical source or registering it as canonical requires a separate explicit
operator confirmation. No generated plugin manifest, package, registry,
materialization receipt, model review, or runtime observation outranks Git
canon.

The package output is staging/distribution state. It must carry a generated
banner or receipt reference and must never be hand-edited.

## Physical package layout

```text
plugins/flossi0ullk-evolution/
├── plugin.json                    # Agent Plugins 1.0.0 manifest
├── mcp.json                       # Agent Plugins 1.0.0 MCP dialect
├── .codex-plugin/
│   └── plugin.json                # OpenAI native manifest
├── .mcp.json                      # OpenAI MCP dialect
├── skills/                        # one shared physical skill tree
│   └── <skill>/SKILL.md
├── hooks/
│   ├── hooks.json                 # OpenAI default hook discovery
│   └── <package-local scripts>
├── scripts/                       # package-local launch and validation helpers
├── provenance/
│   ├── materialization-receipt.json
│   └── capability-matrix.json
├── LICENSE
└── README.md
```

The output path above follows OpenAI's repo marketplace convention. Its use as a
generated staging directory, marketplace source, or committed distribution
artifact must be selected explicitly in the implementation plan; none is
implied by this design.

### Manifest separation

Root `plugin.json` contains only fields permitted by the Agent Plugins 1.0.0
schema. It never receives OpenAI fields such as `skills`, `hooks`,
`mcpServers`, `apps`, or `interface`.

`.codex-plugin/plugin.json` contains only fields accepted by the current OpenAI
contract. The first package version relies on default `hooks/hooks.json`
discovery rather than requiring a `hooks` manifest field. This keeps the package
compatible with the installed validator while preserving documented runtime
behavior.

Shared descriptive values are rendered from the package assembly descriptor.
They are not maintained independently in two manifests.

No reverse-domain Agent Plugins extension namespace is claimed until namespace
control is verified. Dialect coexistence does not require one.

### Shared skills

Both dialects discover immediate children of `skills/` containing `SKILL.md`.
The materializer copies each selected skill once and verifies its content hash
against the canonical corpus. Dialect-specific generated skill metadata may be
placed only in locations already allowed by the underlying Agent Skills
contract and must not change shared instructions.

The plugin includes the task-time discovery dependencies, including
`using-superpowers`, only when the package validator proves every referenced
skill exists exactly once.

### Twin MCP serializations

`mcp.json` and `.mcp.json` express the same admitted server subset but have
different schemas. They are generated from one normalized intermediate model
and compared semantically in tests.

The package must not blindly copy the workspace MCP map. A server is admitted
only when its transport, command, arguments, environment, working directory,
secret handling, and package containment are representable in both selected
dialects. Unsupported servers receive an explicit blocked reason in the
capability matrix; they are not silently weakened or omitted from reports.

Secrets never enter either packaged MCP file. Client- or operator-mediated
secret injection remains outside the package.

### Hooks

Hooks are an OpenAI/native component, not an Agent Plugins v1 component. The
Agent Plugins loader should ignore `hooks/`; the OpenAI loader discovers
`hooks/hooks.json`.

The task-time skill reminder is advisory and must always exit without blocking
prompt delivery. Policy hooks that can deny tools remain separate from reminder
hooks and retain the hard-stop and consent boundaries of the workspace.

Installing or enabling the plugin does not imply hook trust. OpenAI skips
untrusted plugin hooks until the user reviews and trusts the current definition.
The materializer must not bypass that control.

## Materializer architecture

The existing three materializers remain bounded owners of their current
surfaces. A new plugin materializer composes their normalized outputs rather
than absorbing their implementation:

```text
canonical manifests + skill corpus
  -> normalize and select package components
  -> render both dialects into a staging directory
  -> validate manifests, paths, skills, hooks, and semantic MCP equivalence
  -> compute deterministic inventory and output hashes
  -> compare with installed or staged package
  -> plan / check / apply through one journaled transaction
  -> emit materialization receipt
```

### Command contract

The coordinator exposes explicit modes:

- `plan`: read-only target inventory and exact diff; default mode;
- `check`: read-only convergence and validation gate; nonzero on drift or
  invalidity;
- `apply`: mutate only the exact selected package target after operator scope
  selection;
- `rollback`: restore the immediately preceding journaled package version and
  verify it.

Existing materializer CLI behavior remains compatible until a separately tested
migration changes it. A plain existing materializer run must not silently gain
new user-scope effects.

### Concurrency and transaction model

The first implementation uses an exclusive-create lock file with process,
host, start-time, command, and source-commit identity. It does not use
POSIX-only `fcntl`. Stale-lock recovery is explicit and evidence-bearing; an
age threshold alone never steals a live lock.

All files render into a transaction-specific staging directory. Each target
replacement is atomic where the host filesystem supports it. Because a
multi-file package cannot be assumed globally atomic, the coordinator records a
write-ahead journal, replaces files in deterministic order, and restores the
pre-write content on any failure. Failure to restore is fail-closed and reported
as a recovery incident.

User-scope configuration, marketplace installation, plugin cache updates, and
hook trust are separate operations. They require target selection and explicit
operator consent; package generation alone authorizes none of them.

### Materialization receipt

Each run records:

- receipt schema version, run id, timestamp, mode, host platform, and tool
  version;
- source Git commit and dirty-state disclosure;
- input paths and content hashes;
- dependency names, versions, commit pins, package integrity values, and
  licenses;
- selected component and target identities;
- generated file inventory and hashes;
- validator identities, versions, commands, exit codes, and evidence paths;
- exact diff hash and result (`clean`, `drift`, `applied`, `rolled_back`,
  `refused`, or `recovery_failed`);
- consent scope when a governed mutation was actually authorized; and
- known limitations and unresolved capability cells.

The receipt is evidence, not truth or approval. Existing provenance packets may
content-address the receipt rather than creating a competing top-level
provenance authority.

## Task-time skill discovery integration

The task-time reminder design remains the detailed ranking, privacy, exact-once,
and behavioral-evaluation contract. This integration changes its packaging and
Codex evidence state:

- Codex `UserPromptSubmit` response shape is now ✅ **Verified from official
  documentation**.
- Codex runtime delivery, placement, privacy, and exact-once behavior remain
  ⚠️ **Specified** until a plugin-installed local probe records them.
- The reminder script and hook declaration become package-local generated
  components under `hooks/`.
- The hook reads the package's generated skill registry or an explicitly
  bound workspace registry; it never searches arbitrary user files.
- `using-superpowers` remains always included, with no more than three ranked
  candidates and the existing output caps.
- Session-start orientation keeps a compact skill-index fallback for harnesses
  without a verified prompt event.

The reminder does not prove a skill was read or followed. Invocation, file-read,
and outcome evidence remain distinct.

## Governed skill and harness evolution

Evolution applies to four candidate classes:

1. skill instructions and support assets;
2. task-time discovery/ranking policy;
3. harness adapters, hook mappings, and package projections; and
4. materializer validation, transaction, and recovery behavior.

No candidate edits canonical inputs in place. The loop is:

```text
bounded observation
  -> candidate in isolated branch/worktree
  -> unchanged baseline + candidate evaluation
  -> symbolic validators and conformance probes
  -> multi-model review with raw verdicts and analog votes [-1.0, +1.0]
  -> preserved dissent and conflict classification
  -> explicit human accept / revise / reject decision
  -> Git landing
  -> deterministic rematerialization
```

Runtime `Action` telemetry and model self-report are discovery signals only.
Promotion requires admitted evidence, evaluation receipts, complete raw voter
responses, an explicit human decision, and normal Git review. Polarized votes
are conflicts for human resolution, not consensus by averaging.

Harness evolution must optimize more than task success. Evaluations include
correctness, regression, token/context cost, latency, privacy, permission
pressure, accessibility, reversibility, dissent preservation, and cross-harness
behavior. A candidate that improves one harness by silently weakening another
is rejected or target-scoped.

## Conformance and promotion gates

The physical polyglot directory is not promoted until every enabled target has
a versioned capability row and the applicable gates pass:

| Gate | Required evidence | Current state |
| --- | --- | --- |
| Agent `plugin.json` schema | official 1.0.0 schema validation | ✅ probe passed |
| Agent `mcp.json` schema | official 1.0.0 schema validation | ✅ probe passed |
| OpenAI manifest validator | installed validator over same directory | ✅ probe passed |
| shared skill validation | both loaders see the same expected skill hashes | ⚠️ Specified |
| extra-file tolerance | validator/client ignores the other dialect without error or execution | ⚠️ validators passed; client traces pending |
| dialect precedence | OpenAI loads `.codex-plugin/plugin.json`; Agent client loads root `plugin.json` | ❌ Blocked pending direct load probes |
| twin MCP equivalence | normalized server maps compare equal | ⚠️ Specified |
| hook trust | hook is skipped before trust and delivered after bounded trust | ❌ Blocked pending install probe |
| AllAgents adapter | pinned version imports and projects without clobbering unmanaged content | ❌ Blocked pending fixture probe |
| idempotency | second materialization produces zero-byte diff and identical receipt subject hashes | ⚠️ Specified |
| rollback | injected mid-transaction failure restores every pre-write hash | ⚠️ Specified |
| clean clone | package reproduces without `.toilet`, caches, or undeclared user state | ⚠️ Specified |

“Every validator” means every validator and loader named in the enabled target
matrix at its exact pinned version. It cannot mean every present or future
client. Adding a target adds a required conformance row before that target can
be called supported.

## Implementation decomposition

This umbrella design intentionally decomposes into independently reviewable
implementation plans:

1. **Polyglot package assembler and conformance fixture.** Add the minimal
   assembly descriptor, deterministic layout, dual validators, and direct loader
   probes. No installation or production hooks.
2. **Task-time reminder packaging.** Update the reminder evidence baseline,
   package its disabled hook, and run target-specific privacy/exact-once probes.
3. **Journaled materializer coordination.** Add plan/check/apply/rollback,
   locking, recovery, and receipts without changing canonical policy ownership.
4. **Evolution evaluation loop.** Admit skill and harness candidates only after
   the first three workstreams produce stable baselines and receipts.

Each workstream receives its own RED/GREEN tests, bounded authorization, review,
and commit. A later workstream cannot be used to conceal a failure in an earlier
one.

## Rollout and rollback

1. Keep the package output noncanonical and uninstalled.
2. Preregister the conformance fixture, expected file inventory, and loader
   outcomes.
3. Generate the package with hooks disabled.
4. Run schemas and local validators, then direct Agent Plugins and OpenAI loader
   probes in isolated state.
5. Run the pinned AllAgents projection probe and compare unmanaged bytes.
6. Produce the capability matrix and materialization receipt.
7. Present the exact marketplace/config/hook-trust effects for separate operator
   consent.
8. Install only the consented target, read back loaded dialect/components, and
   immediately exercise rollback.
9. Enable the reminder only through its independent activation and evaluation
   gate.

Rollback disables the package target, restores the immediately preceding
journaled package/config state, reads back the relevant loader inventory, and
retains all evidence. It never deletes evidence or hand-edits generated files.

## Acceptance criteria

- One physical directory passes both selected manifest/MCP validators without
  weakening either schema.
- Each loader selects its intended manifest and ignores rather than executes or
  rejects the other dialect's files.
- Shared skills exist once and have identical content hashes from both loader
  views.
- The two MCP documents derive from one normalized model and are semantically
  equivalent for every admitted server.
- Unsupported or nonportable MCP servers are reported with reasons.
- Hooks remain untrusted/disabled until an explicit target-bounded decision.
- Reminder failure never blocks prompt submission or records prompt content.
- Package generation never changes user/global configuration.
- Apply requires explicit mode, target, and user-scope authorization where
  applicable.
- Concurrent or failed runs cannot silently interleave or leave an unreported
  partial package.
- A second unchanged run is byte-idempotent.
- Rollback restores all pre-write hashes under injected failures.
- Every support claim names an exact harness/loader and version with evidence.
- Evolution candidates preserve baselines, raw voter verdicts, analog votes,
  dissent, and the operator decision.
- No candidate, receipt, package, audit, or model vote promotes itself or
  bypasses Holochain integrity validation.
- No artifact is called canonical, SLSA-compliant, verified-effective, or
  universally portable without claim-local evidence and the required human
  decision.

## Design provenance

The design was written from repository and external evidence observed on
2026-09-01/02 at base commit
`a15f5f321d9a98a2553040f1d740d72e531724c8`. The worktree contained unrelated
operator/agent changes; this design does not adopt or modify them.

| Input or probe artifact | SHA-256 |
| --- | --- |
| Antigravity materializer reuse plan v2.1 | `02f9bed3f8b38cb4a7e8735e19dbdac1946ea9689e1f15e883b440cfc54ee202` |
| supplied multi-model audit | `630c65105af7b5d2d991ab5e9f01c8d3d418f3ee5acc3657d9e5b82de5186713` |
| supplied OpenAI plugin documentation paste | `605face331e44ea6befdc54c63b3d1e560f0595635db9083a20b9bbd19554e18` |
| task-time reminder design observed | `ef08fc3bcbebcff074678509ea3ee756b6b24d10f3da57a960bf4c32b04ae6ef` |
| probe Agent `plugin.json` | `d324a2812c6c68369d2bba6366098a319232ec103ddd58a8f05bf9e82c3716e0` |
| probe Agent `mcp.json` | `1788697eb2d3aa1caa8da59a62331a92529e24885f0e7151418f915000fbf7fd` |
| probe OpenAI manifest | `869e3426adcf4e3e01587de216417d1fc9a9244753649123aae010902ea6da39` |
| probe OpenAI `.mcp.json` | `d8e397af03b5b032f21d0aa967086f0c78b33c87b76f2e9898ae0a144df7de02` |
| probe `hooks/hooks.json` | `78922a784ee78e9e50587e93628cd3b9d4dfbe49087adc4514e6781cea38cbb9` |
| probe skill | `4d53eaac8899ad4cb951f51ad9f6a022e2562976385d5bd388bead9aed77aea6` |
| installed OpenAI plugin validator | `7a75b3339396402ad9a40ddc1e037e01c54e71a53a3bfb22a01b1ca235c50206` |

Probe commands and outcomes:

```text
codex-cli 0.128.0
python .../plugin-creator/scripts/validate_plugin.py <polyglot-fixture>
  -> exit 0; Plugin validation passed

Agent Plugins 1.0.0 plugin.schema.json at
ff8ab5e392cc87bd88d87c060815a87490e51003 against root plugin.json
  -> PASS

Agent Plugins 1.0.0 mcp.schema.json at
ff8ab5e392cc87bd88d87c060815a87490e51003 against root mcp.json
  -> PASS
```

The probe fixture is retained as noncanonical evidence at
`.toilet/polyglot-plugin-validator-probe-2026-09-01`. Validator success proves
document compatibility only. It does not yet prove loader precedence, hook
delivery, marketplace installation, or runtime safety.
