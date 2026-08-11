# PR #38 Contract and Shared-Skill Closure Design

**Date:** 2026-07-29
**Status:** ⚠️ Specified design; branch implementation is evidenced by the tests named below, while merge and deployment status remain external
**Approval record:** The operator approved PR #38 cleanup and shared-skill
evolution; Cloudflare was explicitly excluded. The earlier `1, 2, 3, 5`
response referred to a different action list and does not map to the Included
numbering below. Included item 4 was treated as PR-cleanup work, not as a
separately numbered approval.
**Frozen starting head:** `705f555977e118c075ec0cccc2910bd2f5fe134a`

## Purpose

Close four reproduced PR #38 contract defects and promote the already
pressure-tested FLOSSI0ULLK orientation skill into the canonical generated
shared surface. Preserve the consensus gateway's router-not-controller role,
the provenance validator's existing authority, legacy voter compatibility,
and every failed or partial review attempt.

## Scope

### Included

1. Repair the provenance-packet evaluation corpus so all packet fields satisfy
   the machine schema unless the row's golden defect intentionally targets that
   field.
2. Reconcile the `B`-prefixed AID contradiction in favor of the behavior already
   shared by the JSON Schema and production validator: both `D` and `B`
   44-character AIDs are valid signing identifiers.
3. Render non-packet evidence roots reachable through validated child
   provenance packets into voter context.
4. Prevent already-recorded OMO Momus and Critic voters from being reinvoked on
   deferred retries.
5. Promote the exact tested orientation-skill v0.3.4 content from the private
   Codex projection into `skill-corpus/flossi0ullk-orient/`, update its corpus
   changelog, and regenerate every enabled native projection from that canonical
   source.
6. Bind task review and whole-branch review to exact base/head commit pairs,
   push only by non-force fast-forward, and resolve only the four reproduced
   review threads after their defects are independently closed.

### Excluded

- Cloudflare account/build configuration.
- ADR edits or canon promotion.
- Holochain integrity-zome logic.
- Consensus thresholds, vote weights, provider rosters, and outcome semantics.
- Unrelated refactors in `packages/metacoordinator_mcp`.
- Deleting or cleaning the preserved `.serena/project.yml` modification.

## Authority and Invariants

### Provenance evaluation corpus

The evaluation module is a symbolic reasoning corpus. Its rubric explicitly
provides `crypto_facts` because text models cannot execute JCS, BLAKE3, Ed25519,
or workspace artifact rehashing. The packet remains structurally meaningful,
but the supplied crypto booleans are the module's oracle inputs; some adversarial
rows, such as a self-referential evidence cycle with a supposedly valid digest,
cannot be emitted as a literally executable signed packet.

The repair therefore:

- replaces every malformed artifact `sha256` with a deterministic, lowercase,
  64-character hexadecimal value;
- preserves each row's intended `artifact_hashes_match_workspace` truth value;
- preserves fixed field lengths, so the structural size of each artifact hash
  does not change;
- validates all 30 packet objects against
  `docs/specs/provenance-packet.schema.json`;
- checks every golden defect against an explicit mutation or supplied
  `crypto_facts` value;
- documents that the oracle facts are counterfactual inputs rather than a claim
  that every adversarial packet can be replayed through the production
  cryptographic validator.

The generated value for artifact index `n` in row `id` is:

```text
sha256(UTF-8("FLOSS:provenance-eval:<id>:artifact:<n>")).hexdigest()
```

This is deterministic and reproducible. Rows whose intended defect is
`E-ARTIFACT-HASH-MISMATCH` retain `artifact_hashes_match_workspace=false`;
other rows retain `true`.

### AID reconciliation

The current executable contract is:

```text
^[DB][A-Za-z0-9_-]{43}$
```

`docs/specs/provenance-packet.schema.json` and
`packages/activity_log/provenance.py::_public_key_from_aid()` both implement
this contract. The prose spec, evaluation rubric, and `ppv-dev-007` golden
currently contradict it. The repair changes those three narrative/evaluation
surfaces; it does not change production validation.

### Validated evidence-DAG rendering

Validation remains the authority. Rendering must not make an invalid packet
usable and must not read arbitrary evidence content.

For each top-level `provenance_packet` evidence reference:

1. Resolve and hash-check it exactly as `_collect_provenance_state()` does.
2. Require `provenance.validate_packet()` to succeed.
3. Traverse only child references whose type is `provenance_packet`.
4. Resolve each child beneath the existing workspace rules and require that
   child validation succeeds before using any child metadata.
5. Carry an active-path digest set for cycle defense and enforce the validator's
   existing maximum depth of 8.
6. Collect only metadata from non-packet evidence references: type, ref, and
   optional SHA-256. Never read or embed referenced file contents.
7. Deduplicate while preserving first-seen order.
8. Bound the voter-visible result to 32 evidence references and 4,096
   characters. Emit an explicit truncation marker when either bound is reached.
9. On validation, resolution, or traversal failure, omit the affected packet's
   derived context rather than weakening the submission gate.

The existing packet digest and consent-decision hash remain visible. Direct
non-packet evidence behavior remains unchanged. Because the digest and consent
decision hash are signed identity-bearing metadata, rendering fails closed with
a deterministic whole-context sentinel if whitespace sanitization would change
either exact value or if either value contains non-printable characters; it
never substitutes a normalized or transport-unsafe identity.

### Deferred voter retries

`_known_voter_name()` must recognize every named closure emitted by the current
voter builders:

- `litellm_voter_`
- `flowith_voter_`
- `omo_momus_voter_`
- `omo_critic_voter_`

Recognition is only a pre-invocation optimization for voters whose vote is
already persisted. Vote validation, duplicate rejection after invocation, and
legacy one-argument voter support remain unchanged.

### Shared orientation skill

The private Codex v0.3.4 file is evidence, not authority. Promotion is:

1. Verify its command-measured SHA-256 is
   `491A2B37B9CF73A3FCDF7FCA5D9CEF0B0E81D8B62A10DA40238E0EF695B266EE`.
2. Apply those exact `SKILL.md` bytes to the canonical corpus.
3. Add v0.3.0 through v0.3.4 entries to the corpus `CHANGELOG.md`.
4. Run the canonical materializer; do not hand-edit projections.
5. Verify enabled Codex, Claude, Gemini, OpenCode, and Hermes projections match
   the canonical `SKILL.md` byte-for-byte.
6. Run the full shared-surface `--check`.

The disabled Cowork/Claude Desktop target remains a documented manual
distribution path and is not silently marked materialized.

## Testing Strategy

### Evaluation contract tests

- Exactly 20 dev and 10 heldout rows parse.
- Every packet validates against the JSON Schema.
- Every artifact hash matches `^[a-f0-9]{64}$`.
- Deterministic regeneration produces the committed hash values.
- Each declared crypto fact has the expected boolean type.
- `ppv-dev-007` is valid with `PPV-OK`.
- The rubric and prose spec both state `[DB]`.
- Each artifact-mismatch golden corresponds to
  `artifact_hashes_match_workspace=false`; all other rows are true.

### Gateway tests

- A top-level packet whose only non-packet root is in a valid child exposes that
  root in voter context.
- A shared child referenced twice is rendered once.
- A child cycle or depth overflow never produces voter-visible derived evidence.
- More than 32 roots or 4,096 characters produces a deterministic truncation
  marker and stays within the bound.
- A schema-valid signed consent hash containing whitespace that sanitization
  would change produces the exactness sentinel and no partial metadata.
- A schema-valid signed consent hash containing non-printable control characters
  produces the same sentinel and no partial metadata.
- Existing direct-root rendering remains unchanged.
- A persisted OMO Critic vote prevents a second provider invocation.
- A persisted OMO Momus vote prevents a second provider invocation.
- Legacy one-argument voters still run.

### Shared-surface tests

- Canonical and private v0.3.4 hashes match before materialization.
- Every enabled projection hash matches canonical after materialization.
- `materialize_shared_skill_surface.py --check` passes.
- `refresh_agent_surfaces.py --check` passes or reports a separately evidenced,
  pre-existing non-skill failure; no drift is hidden.

## Review and Landing

Each implementation task receives a fresh implementer and fresh task reviewer.
The final reviewer receives the complete diff from
`705f555977e118c075ec0cccc2910bd2f5fe134a` to the final head. Review must lead
with spec compliance, provenance safety, regression behavior, and generated
surface authority.

Before push:

- all focused and package tests pass;
- the exact four reproduced defects have direct passing probes;
- the diff contains only authorized files;
- remote PR head still equals the local task base or is an ancestor of the
  final local head;
- push is a non-force fast-forward.

After push, read back the remote head, checks, and review-thread states. Resolve
only:

- `PRRT_kwDOPkAi3s6UmelA`
- `PRRT_kwDOPkAi3s6UmelE`
- `PRRT_kwDOPkAi3s6UmelH`
- `PRRT_kwDOPkAi3s6UmelJ`

Cloudflare failure does not block this approved slice and is not claimed fixed.

## Cross-Family Adversarial Review Provenance

Failed or partial attempts are preserved and are not votes:

- Gemini 3.1 Pro: timeout.
- Cohere unqualified catalog ID: HTTP 400 invalid model.
- Qwen unqualified catalog ID: HTTP 400 ambiguous model.
- Gemini 2.5 Flash: HTTP 404 retired endpoint.
- Qwen via Bluesminds: timeout.

Successful independent-family responses:

| Family/model | Analog vote | Accepted findings | Rejected findings |
|---|---:|---|---|
| Cohere `command-a-03-2025` | `-0.75` | Bound recursion; test mixed-version projections; avoid unintended evidence exposure | Generic deployment claims without repo evidence |
| Gemini `gemini-3-flash-preview` | `+0.842` | Verify exact private/canonical bytes; exhaust depth bounds | None material |
| Mistral `mistral-small-latest` | `-0.921` | Deterministic fixture generation; atomic commit/readback; freeze exact skill bytes | Invented helper APIs and tests that do not match this repository |
| Qwen `qwen3.6-27b` | `-0.87` | Integration-test voter visibility; prove duplicate calls are skipped | Cloudflare migration criticism, because Cloudflare is unchanged and excluded |

The responses are polarized advisory evidence, not a gateway Decision or
canonical truth. The human's explicit instruction to execute the bounded slice
resolves whether work proceeds; the concrete falsifiers above remain binding.

## Success Criteria

The slice is complete only when:

1. All four reproduced defects are closed by tests that failed before their
   corresponding implementation.
2. The full relevant package suites pass.
3. Every enabled shared-skill projection matches the canonical v0.3.4 bytes.
4. A fresh whole-branch reviewer returns both spec-compliance and quality
   approval on the exact base/head diff.
5. The remote PR head and four thread states are read back after push.
6. No claim says Cloudflare, attacker-level Tryorama coverage, or any unrelated
   backlog item was fixed.
