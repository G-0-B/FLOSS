---
title: PR 38 Preserve-First Salvage and Verification Spine
kind: design_spec
status: Proposed
truth_status: Specified
date: 2026-07-13
canonical: false
scope: PR 38 preservation, salvage, reconstruction, and verification
approval: User-approved design direction on 2026-07-13
---

# PR 38 Preserve-First Salvage and Verification Spine

## Status and authority

⚠️ **Specified — design proposal, not canonical architecture.** This document records an approved execution direction and its safety contract. It does not promote itself or any referenced artifact to canonical status, modify an ADR, authorize integrity-zome changes, or authorize consensus-gateway changes.

The prime directive remains unchanged: logic validates; neural systems assist. Multi-model review may advise reconstruction decisions, but it cannot establish symbolic truth or substitute for Holochain integrity validation.

## Outcome

Recover the valuable work around PR #38 without losing, flattening, or misrepresenting any of these distinct states:

1. remote `main`;
2. the remote PR #38 head and history;
3. the local committed history;
4. the local index;
5. the local tracked working tree;
6. the local untracked and ignored-file inventory.

Reconstruction occurs in a clean worktree from an exact remote-main commit. Every salvaged change atom retains provenance to its source plane, source commit where one exists, before/after blobs, modes, and exact diff digest. File or commit classification is the default; hunk-level classification is reserved for mixed-purpose files, protected boundaries, and provenance disputes. Verification reports only what was observed for the exact subject and environment.

## Verified starting observations

The following are point-in-time observations from the 2026-07-13 audit. They are evidence inputs, not permanent project claims.

| Observation | Truth status | Evidence |
|---|---|---|
| Remote `main` was `e8e71d4d29fac049e40db28ffb82d43d5592a158` after fetch. | ✅ Verified | `git fetch origin main`; `git rev-parse origin/main` |
| Remote PR #38 head was `085ed40861f6dfa3e1fea280ef7ed2a8321ee2ca`. | ✅ Verified | Live PR and Git inspection during the audit |
| The primary local object database did not contain that PR head commit, so preservation must fetch and restore-test it before containment. | ✅ Verified | `git cat-file -e '085ed408...^{commit}'` returned absent on 2026-07-13 |
| The original local branch head was `061807c413b26dca3e2dcb8cfab171aed23adc15`, with 11 commits beyond its tracking ref and uncommitted files. | ✅ Verified | `git status --short --branch`; branch log; worktree inspection |
| A clean worktree at remote `main` passed 145 focused Python tests. | ✅ Verified | `python -m pytest packages/orchestrator packages/source_chain packages/metacoordinator_mcp packages/activity_log/tests -q` |
| That same clean remote-main worktree failed the spec gate on 10 unregistered governed artifacts. | ✅ Verified | `python scripts/spec_gate.py` |
| PR #38 contained unresolved review threads and was not ready for direct merge. | ✅ Verified | Live PR inspection during the audit |
| Rust Sweettest migration and current consent/substrate-bridge scenarios were not present in the audited states. This does not reopen the already-complete MVP Phase 0 substrate-viability gate. | ✅ Verified | Repository search; `docs/architecture/OPERATOR_PRIMER.md` current-state correction |

These observations must be refreshed before implementation. SHAs are anchors for preservation, not assumptions that remotes have stopped moving.

## Non-negotiable safety contract

Before changing the PR lifecycle or reconstructing its work:

- preserve all six source planes independently;
- do not delete files, branches, worktrees, or the PR;
- do not reset, stash, rebase, squash, or force-push the source states;
- do not modify the original dirty checkout;
- do not claim a clean tree when untracked files were omitted from evidence;
- do not cross any repository hard stop without fresh, explicit human confirmation;
- do not allow advisory model consensus to bypass symbolic validation;
- do not mark a load-bearing claim Verified without a reproducible evidence path.

If preservation cannot be proved, salvage stops.

## Six-plane preservation contract

### Plane A: remote main

Record the fetched remote URL, ref, exact commit SHA, commit object, and fetch timestamp. The reconstruction branch starts from this exact SHA, not from an ambiguous moving branch name.

### Plane B: remote PR #38

Preserve the complete reachable Git history in a bundle. Also record the PR URL, number, base SHA, head SHA, commit list, changed-file list, review-thread state, check state, and patch series. The PR remains open until snapshot verification and the salvage manifest are complete.

### Plane C: local committed history

Preserve the branch ref, `refs/stash`, complete reachable history, commit/tree/parent OIDs, merge parents, and configured upstream in a self-contained bundle.

### Plane D: local index

Preserve the index byte-for-byte together with any shared index, conflict stages, intent-to-add entries, skip-worktree/assume-unchanged flags, sparse-checkout state, and an independently rendered staged binary diff. Recheck this plane at capture time even when the current index appears clean.

### Plane E: local tracked worktree

Preserve a binary-safe Git diff plus screened raw-file bytes and SHA-256 digests. Record line-ending and attribute configuration because Git normalization can differ from the bytes on disk.

### Plane F: local untracked and ignored inventory

Inventory every untracked and ignored path with type, size, SHA-256 where safe, and an explicit inclusion or exclusion reason. Copy contents only when the snapshot destination is outside the source worktree and secret screening permits it. Necessary sensitive material belongs in an encrypted local quarantine or an explicit `not-reconstructable` exclusion, never in the ordinary packet.

These planes are layered through parent identifiers and sealed independently. A commit SHA or a single combined "dirty" plane is not adequate.

### Snapshot artifact set

Each snapshot directory contains:

```text
snapshot.json
refs.txt
commits.txt
history.bundle
status.porcelain-v2.z
index.raw
index-metadata.json
index.patch.binary
worktree.patch.binary
tracked-raw-manifest.json
tracked-raw/              # only screened, copied files
untracked-manifest.json
untracked/                 # only screened, copied files
ignored-manifest.json
filesystem-metadata.json
checksums.sha256
provenance-root.json
verification.json
```

`snapshot.json` records repository identity, source path, plane hierarchy, refs, SHAs, tree/parent OIDs, timestamps, Git version, relevant Git configuration, capture commands, exclusions, and operator. `checksums.sha256` covers all immutable payloads. The checksum root is signed or placed in an authenticated provenance packet whose digest is anchored independently; replacing payloads and their checksum file together must be detectable.

Capture is quiesced or guarded by before/after equality checks over refs, stash, index hash, status digest, and source-file hashes. `verification.json` records those checks, bundle verification, checksum verification, and a clean-room restore into an empty repository. Restored commits, trees, refs, modes, path casing, and raw-file hashes must match before PR containment or reconstruction. The procedure fails closed if submodules or LFS appear without their referenced repositories or media.

Secrets, credentials, and machine-specific private configuration must not be copied into durable artifacts. Their existence may be represented by a redacted manifest entry with a salted content fingerprint only when useful and safe.

## Salvage manifest

The salvage manifest is machine-readable JSON with a human-readable rendered view. It first inventories the complete change universe, then classifies progressively around one to three selected outcomes and their dependency cones. Commit or file atoms are the default. A file is split into exact diff atoms only when it mixes concerns, crosses a protected boundary, or has disputed provenance. Unselected atoms remain visibly captured and unclassified; they are ineligible for reconstruction rather than being forced through expensive pseudo-precision.

Disposition, authorization, verification, materialization, integration, and claim truth are independent axes. A model vote cannot populate a human authorization field, and a disposition cannot imply verification.

Required fields per change atom and salvage item include:

```json
{
  "item_id": "stable-item-id",
  "revision_id": "content-bound-revision-id",
  "atom_ids": ["source-plane-bound-atom-id"],
  "path_before": "repo/relative/path-or-null",
  "path_after": "repo/relative/path-or-null",
  "blob_before": "git-oid-or-null",
  "blob_after": "git-oid-or-content-digest",
  "mode_before": "git-mode-or-null",
  "mode_after": "git-mode-or-null",
  "exact_diff_digest": "sha256",
  "primary_lane": "lane-id",
  "classification_state": "captured|classified",
  "disposition": null,
  "source_planes": ["pr38", "local-committed"],
  "source_commits": ["full-sha"],
  "patch_ids": ["supplemental-stable-patch-id"],
  "atomic_group_id": "optional-group-id",
  "required_gate_ids": ["scope-bound-human-gate-id"],
  "dependencies": [{"type": "requires|generated_by|conflicts_with|supersedes", "item": "other-item-id"}],
  "blockers": ["plain-language blocker"],
  "required_profiles": ["verification-profile-id"],
  "replacement_item_id": "required-for-revise-or-null",
  "notes": "bounded rationale"
}
```

Rules:

- every captured atom has one and only one owner; no atom may be silently omitted or multiply owned;
- `classification_state=captured` requires a null disposition; `classified` requires exactly one of `salvage`, `revise`, `park`, or `reject`;
- cross-lane dependencies are explicit and do not create duplicate ownership;
- `salvage` means eligible for reconstruction after dependencies, gates, and verification are satisfied, not already validated;
- `revise` requires a replacement design or patch before salvage;
- `park` preserves the material without putting it on the merge path;
- `reject` requires a reason and does not authorize deletion of the source;
- hard stops are separate scope-bound gates, never a fifth disposition;
- generated files are linked to their generators and are not independently salvaged unless necessary for reproducibility;
- patch IDs supplement exact source-plane, blob, mode, parent, and diff identity; they never replace them;
- `requires` and `generated_by` are acyclic between atomic groups; a parked or rejected dependency blocks its dependents unless a replacement exists;
- changes to an item revision, target base, action, or scope stale prior verification and invalidate prior approval;
- truth status belongs to explicit evidence-backed claims, not to mutable file disposition;
- no global `green` field exists: preservation, coverage, reconstruction readiness, and each verification profile report independently.

### Initial lane taxonomy

The implementation pass must refine this table against the complete diff before moving code.

| Lane | Typical scope | Default disposition |
|---|---|---|
| `preservation-admin` | snapshots, manifests, PR containment evidence | Salvage first |
| `commons-gateway` | read-only Commons Gateway work | Independent reconstruction candidate |
| `activity-log-provenance` | provenance identity and packet handling | Reconstruct with regression evidence |
| `evals-verification` | evaluation and verification tooling | Revise around the verification spine |
| `research-intake` | research notes and intake digestion | Preserve, then curate separately |
| `openhuman-bridge` | OpenHuman bridge experiment | Revise against current specs |
| `yumeichan-contract` | schema/spec and thin-client contract | Split from ADR and gateway changes |
| `knowledge-triple` | contract reconciliation | Split ordinary docs/code from hard stops |
| `holochain-integrity` | consent or provenance integrity logic | No default disposition; human gate required for action |
| `consensus-gateway` | voter profiles and gateway decision logic | No default disposition; human gate required for action |
| `machine-and-generated` | local config, generated projections, synthesis | Park or regenerate |
| `local-eleven` | commits unique to the local branch | Independent queue; never assumed part of PR #38 |

## Reconstruction algorithm

1. Refresh remote refs and lock the exact candidate base/head SHAs.
2. Quiesce mutating agents, hooks, and watchers or prove before/after capture equality.
3. Capture all six planes, authenticate the checksum root, restore the capsule into an empty repository, and compare OIDs, modes, paths, refs, and screened raw bytes.
4. Inventory the complete change universe without forcing immediate disposition.
5. Select one to three desired outcomes and trace their smallest dependency cones.
6. Classify the selected cones progressively: commit/file first; exact diff atoms only for mixed, protected, or disputed changes.
7. Obtain explicit confirmation for any hard-stop action. Absence of confirmation leaves the item ineligible; it does not change its disposition.
8. Create a new clean worktree and branch at the recorded remote-main SHA, then assert it is clean including untracked files.
9. Salvage atomic commits with `git cherry-pick -x` when the entire commit belongs to one lane and passes review. Record merge mainline explicitly for merge commits.
10. For mixed commits, extract only manifest-owned atoms. Record source plane, source SHA and parents, pre/post blob OIDs, modes, exact diff digest, supplemental patch ID, rename/case decision, and commit trailers:

   ```text
   Salvaged-From: <source-plane> <full-source-sha-or-content-digest>
   Salvage-Item: <manifest-item-id>
   Source-Patch-Id: <stable-patch-id>
   ```

11. Run the lane’s required checks before and after each bounded reconstruction unit.
12. Keep each commit single-purpose and each eventual PR independently reviewable.
13. Emit an append-only checkpoint after each phase with state ID, input SHAs, evidence hashes, completed actions, next safe command, abort/recovery command, blockers, and human decisions.
14. Stop on provenance ambiguity, unexpected tree dirtiness, dependency drift, evidence mismatch, stale approval, or checkpoint failure.

No reconstruction step mutates the source PR branch or the original local checkout.

## PR containment

After—and only after—the six-plane capsule passes clean-room restoration and the manifest represents the complete change universe, PR #38 may be marked Draft and receive a stop-merge comment linking to the preservation record and reconstruction queue. Full disposition of every preserved atom is not required for containment; unclassified atoms remain visibly preserved and ineligible.

Containment does not mean closure, deletion, force-push, or history rewriting. The PR remains a reviewable source artifact until its salvage dispositions have been accepted and the human owner explicitly chooses its final lifecycle state.

## Verification spine

The verification spine is one Python entry point that emits structured evidence. Host and pinned-Nix executions are distinct evidence environments; they are never compared as if interchangeable. Nix receives a timeboxed cold-bootstrap preflight before it becomes required for a lane; the default stop condition is 15 minutes or two failed bootstraps, after which the Nix lane reports `BLOCKED` pending review.

```bash
python scripts/verify.py --profile preservation
python scripts/verify.py --profile core
nix develop -c python scripts/verify.py --profile sweettest-migration
nix develop -c python scripts/verify.py --profile consent-e2e
nix develop -c python scripts/verify.py --profile substrate-bridge
```

The command names are specified here; their implementation is a later, test-driven slice.

### Evidence levels

#### `preservation`

Proves only that required source snapshots were captured and can be verified: refs resolve, bundles verify, checksums match, manifests cover expected paths, and exclusions are explicit.

#### `core`

Runs ordinary engineering and governance checks:

- clean-tree policy appropriate to the evidence mode;
- spec gate;
- focused and repository-defined Python tests;
- Rust format, clippy, and workspace tests;
- WASM build and DNA packaging checks;
- Worker typecheck and tests where that package is in scope;
- schema and manifest validation;
- provenance consistency checks.

Its public check name must say **Core engineering checks — scoped evidence only**.

#### Claim-specific Holochain profiles

`sweettest-migration`, `consent-e2e`, and `substrate-bridge` are separate profiles. Each proves only its named claim and declares the exact native scenarios it requires. A conductor-boot smoke test is insufficient; a meaningful scenario must be able to fail against a deliberately invalid fixture and must exercise the applicable integrity rejection path.

Missing native proof makes only the affected profile `BLOCKED` or `FAIL`. It does not retroactively reopen the already-verified MVP Phase 0 substrate-viability milestone. `docs/architecture/OPERATOR_PRIMER.md` is authoritative for that phase correction.

### Result semantics

Each step returns one of:

- `PASS`: the required command ran successfully and its assertions passed;
- `FAIL`: the command or assertion ran and failed;
- `BLOCKED`: the check could not run because a required capability or prerequisite is absent;
- `SKIPPED`: allowed only for steps declared optional by the selected profile.

An overall profile passes only when every required step is `PASS`. `BLOCKED` is never green. Every result exposes two dimensions: absolute status for the command, and regression status against the exact same command and environment on the locked baseline. “No regression from a red baseline” is never presented as green.

### Evidence record

Every run emits JSON containing:

```text
schema_version
repository identity, commit SHA, and tree OID
dirty flag and porcelain digest
manifest revision, dependency-closure digest, and approval-set digest
profile definition digest and runner version
environment and dependency fingerprints
start and finish timestamps
step id, command, cwd, duration, exit code, and result
stdout and stderr SHA-256 digests
bounded, sanitized output tails
artifact paths and digests
absolute result and same-environment regression result
counts of blocked, stale, unclassified, parked, rejected, and falsified claims
```

Release-grade evidence fails closed when the tree is dirty. Developer mode may report dirty-tree diagnostics, but its output is visibly non-release and cannot be promoted by renaming the artifact.

Runtime evidence may live under `.agent-surface/verification/`; CI uploads the same schema as an immutable artifact. Logs are redacted before persistence. Evidence records observations and provenance, not canonical truth.

## Human and symbolic gates

The runner may automate checks but cannot automate away authority:

- ADR changes require explicit human confirmation and normal ADR governance;
- integrity-zome changes require explicit human confirmation and symbolic tests;
- consensus-gateway logic changes require explicit human confirmation;
- canonical promotion requires explicit human confirmation;
- deletion remains prohibited unless separately authorized under repository policy;
- advisory model votes are recorded as advice, with provider/model independence metadata, never as validation proof.

Every human approval binds the exact item revision, change atoms, intended action, reconstruction base, scope digest, and policy digest. Any content, base, action, or scope change invalidates that approval. Model agreement cannot satisfy a human gate.

## Failure and recovery rules

- Capsule verification or clean-room restoration failure: stop before containment or reconstruction.
- Manifest coverage gap: stop salvage for the affected dependency cone.
- Dirty reconstruction tree: capture diagnostics and stop; do not auto-clean.
- Cherry-pick conflict: abort only the in-progress cherry-pick in the reconstruction worktree after recording diagnostics; do not alter source states.
- Baseline failure: classify it as pre-existing, introduced, blocked, or unknown using commit-pinned, same-environment evidence. Never relabel “no regression” as passing.
- Hard-stop discovery: leave the action ineligible and request explicit confirmation; do not silently rewrite the item’s disposition.
- Provenance mismatch: block the candidate until source identity is resolved.
- Stale input: any changed subject tree, manifest revision, dependency closure, approval set, profile, or environment invalidates the prior verification result.
- Capture drift: any before/after mismatch in refs, stash, index, status, or source hashes restarts capture from a new state identifier.
- Secret detection: exclude and redact; never persist the secret to evidence or memory.
- Continuation failure: if a fresh agent cannot identify the next safe command and recovery command from the latest checkpoint, stop and repair the packet.
- Fatigue limit: after three consequential human decisions or about 30 minutes of hard-stop review, preserve state and pause instead of soliciting more protected decisions.

## Acceptance criteria

The preserve-first design is ready for implementation planning when:

1. all six source planes have named, authenticated, restore-tested capture procedures;
2. the manifest inventories the complete change universe and owns every selected change atom exactly once;
3. progressive commit/file/diff-atom classification and the unclassified-preserved state are unambiguous;
4. disposition, authorization, verification, integration, and truth claims are separate axes;
5. each lane names dependencies, hard stops, and required verification;
6. reconstruction is guaranteed to start from an exact clean remote-main SHA and tree;
7. merge-parent, blob, mode, rename/case, raw-byte, and mixed-commit provenance rules are unambiguous;
8. PR containment cannot precede authenticated clean-room restoration;
9. `preservation`, `core`, `sweettest-migration`, `consent-e2e`, and `substrate-bridge` cannot be confused in commands, statuses, or CI labels;
10. absolute and same-environment regression results are reported separately, with no global green field;
11. missing native proof makes only its named claim profile non-green and cannot rewrite completed MVP Phase 0 status;
12. dirty-tree release evidence fails closed;
13. a fresh agent can resume from a checkpoint without reconstructing this conversation;
14. no step silently authorizes an ADR, integrity-zome, consensus-gateway, canonical, deletion, or protected-config change.

## Proposed implementation sequence

This is ordering, not implementation authorization.

1. Capsule schema, capture scripts, authenticated checksum root, and clean-room restoration tests.
2. Verified capture and sealing of the six live source planes.
3. Complete change-universe inventory plus salvage-manifest schema, validator, and rendered report.
4. Selection of one to three desired outcomes and their minimum dependency cones.
5. PR containment after preservation and inventory proof.
6. Verification-runner skeleton, JSON evidence schema, and timeboxed host/Nix preflights.
7. `core` baseline matrix wired to existing repository checks, preserving absolute failures and regressions honestly.
8. One thin, reversible reconstruction slice with its verification and checkpoint before widening the queue.
9. Lane-by-lane reconstruction through small branches and reviewable PRs.
10. `sweettest-migration`, `consent-e2e`, and `substrate-bridge` as separately scoped, separately approved native-test slices when their claims enter scope.

## Non-goals

This design does not:

- merge, close, rewrite, or delete PR #38;
- force immediate disposition of every preserved atom before a selected outcome pulls it into scope;
- modify canonical architecture or ADRs;
- change integrity-zome or consensus-gateway logic;
- reopen or relabel the completed MVP Phase 0 substrate-viability milestone;
- claim Sweettest migration, consent e2e, or substrate-bridge proof from Python, Rust unit, Worker, packaging, or conductor-boot smoke tests alone;
- treat LLM agreement as truth;
- fold the 11 local-only commits into PR #38 by assumption;
- clean or normalize the original dirty checkout.

## Design rationale

The essential improvement is to make preservation, resumability, and claim-scoped verification first-class products rather than incidental setup. A branch can be rebuilt; missing provenance, flattened local state, stale approvals, and falsely global green checks are much harder to recover from. Reconstruction is therefore downstream of authenticated clean-room restoration, classification follows selected dependency cones at the coarsest honest granularity, and evidence remains separate from disposition and authority. The process expands only after one reversible slice proves that its bookkeeping supports recovery instead of becoming the project.
