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
3. the current local branch, its additional commits, and its dirty working tree.

Reconstruction occurs in a clean worktree from an exact remote-main commit. Every adopted path or hunk retains provenance to its source state and source commit. Verification reports what was actually observed at each evidence level and cannot label ordinary unit-test success as Phase 0 proof.

## Verified starting observations

The following are point-in-time observations from the 2026-07-13 audit. They are evidence inputs, not permanent project claims.

| Observation | Truth status | Evidence |
|---|---|---|
| Remote `main` was `e8e71d4d29fac049e40db28ffb82d43d5592a158` after fetch. | ✅ Verified | `git fetch origin main`; `git rev-parse origin/main` |
| Remote PR #38 head was `085ed40861f6dfa3e1fea280ef7ed2a8321ee2ca`. | ✅ Verified | Live PR and Git inspection during the audit |
| The original local branch head was `061807c413b26dca3e2dcb8cfab171aed23adc15`, with 11 commits beyond its tracking ref and uncommitted files. | ✅ Verified | `git status --short --branch`; branch log; worktree inspection |
| A clean worktree at remote `main` passed 145 focused Python tests. | ✅ Verified | `python -m pytest packages/orchestrator packages/source_chain packages/metacoordinator_mcp packages/activity_log/tests -q` |
| That same clean remote-main worktree failed the spec gate on 10 unregistered governed artifacts. | ✅ Verified | `python scripts/spec_gate.py` |
| PR #38 contained unresolved review threads and was not ready for direct merge. | ✅ Verified | Live PR inspection during the audit |
| Sweettest-based Phase 0 proof was not present in the audited states. | ✅ Verified | Repository search and Holochain test-surface inspection |

These observations must be refreshed before implementation. SHAs are anchors for preservation, not assumptions that remotes have stopped moving.

## Non-negotiable safety contract

Before changing the PR lifecycle or reconstructing its work:

- preserve all three states independently;
- do not delete files, branches, worktrees, or the PR;
- do not reset, stash, rebase, squash, or force-push the source states;
- do not modify the original dirty checkout;
- do not claim a clean tree when untracked files were omitted from evidence;
- do not cross any repository hard stop without fresh, explicit human confirmation;
- do not allow advisory model consensus to bypass symbolic validation;
- do not mark a load-bearing claim Verified without a reproducible evidence path.

If preservation cannot be proved, salvage stops.

## Three-state preservation contract

### State A: remote main

Record the fetched remote URL, ref, exact commit SHA, commit object, and fetch timestamp. The reconstruction branch starts from this exact SHA, not from an ambiguous moving branch name.

### State B: remote PR #38

Preserve the complete reachable Git history in a bundle. Also record the PR URL, number, base SHA, head SHA, commit list, changed-file list, review-thread state, check state, and patch series. The PR remains open until snapshot verification and the salvage manifest are complete.

### State C: local branch plus dirty state

Preserve the branch ref and reachable history in a bundle. Preserve tracked working-tree and index changes as binary-safe patches. Inventory every untracked path with size and SHA-256; copy untracked contents to the snapshot only when the snapshot destination is outside the source worktree and secret screening permits it.

The local state is not represented adequately by a commit SHA alone.

### Snapshot artifact set

Each snapshot directory contains:

```text
snapshot.json
refs.txt
commits.txt
history.bundle
status.porcelain-v2.z
index.patch.binary
worktree.patch.binary
untracked-manifest.json
untracked/                 # only screened, copied files
checksums.sha256
verification.json
```

`snapshot.json` records repository identity, source path, state class, refs, SHAs, timestamps, Git version, capture commands, exclusions, and operator. `checksums.sha256` covers all immutable snapshot payloads. `verification.json` records bundle verification, checksum verification, patch applicability checks where safe, and any blocked checks.

Secrets, credentials, and machine-specific private configuration must not be copied into durable artifacts. Their existence may be represented by a redacted manifest entry with a salted content fingerprint only when useful and safe.

## Salvage manifest

The salvage manifest is machine-readable JSON and has a human-readable rendered view. Every changed path receives exactly one primary disposition. When a file contains multiple separable concerns, ownership is assigned at hunk or line-range granularity.

Required fields per item:

```json
{
  "id": "stable-item-id",
  "path": "repo/relative/path",
  "hunk_ranges": ["optional source line or diff identifiers"],
  "primary_lane": "lane-id",
  "disposition": "adopt|revise|park|reject|hard-stop",
  "source_state": "remote-main|pr38|local-branch|local-dirty",
  "source_commits": ["full-sha"],
  "patch_ids": ["stable-patch-id"],
  "hard_stop_class": "none|adr|integrity-zome|consensus-gateway|canon|config|deletion",
  "dependencies": ["other-item-id"],
  "blockers": ["plain-language blocker"],
  "required_tests": ["verification-step-id"],
  "truth_status": "verified|specified|aspirational|blocked",
  "notes": "bounded rationale"
}
```

Rules:

- one and only one primary lane owns each path or hunk;
- cross-lane dependencies are explicit and do not create duplicate ownership;
- `adopt` means eligible for reconstruction, not already validated;
- `revise` requires a replacement design or patch before adoption;
- `park` preserves the material without putting it on the merge path;
- `reject` requires a reason and does not authorize deletion of the source;
- `hard-stop` identifies work requiring separate explicit confirmation;
- generated files are linked to their generators and are not independently salvaged unless necessary for reproducibility;
- patch IDs supplement source SHAs; they never replace commit provenance.

### Initial lane taxonomy

The implementation pass must refine this table against the complete diff before moving code.

| Lane | Typical scope | Default disposition |
|---|---|---|
| `preservation-admin` | snapshots, manifests, PR containment evidence | Adopt first |
| `commons-gateway` | read-only Commons Gateway work | Independent reconstruction candidate |
| `activity-log-provenance` | provenance identity and packet handling | Reconstruct with regression evidence |
| `evals-verification` | evaluation and verification tooling | Revise around the verification spine |
| `research-intake` | research notes and intake digestion | Preserve, then curate separately |
| `openhuman-bridge` | OpenHuman bridge experiment | Revise against current specs |
| `yumeichan-contract` | schema/spec and thin-client contract | Split from ADR and gateway changes |
| `knowledge-triple` | contract reconciliation | Split ordinary docs/code from hard stops |
| `holochain-integrity` | consent or provenance integrity logic | Hard stop |
| `consensus-gateway` | voter profiles and gateway decision logic | Hard stop |
| `machine-and-generated` | local config, generated projections, synthesis | Park or regenerate |
| `local-eleven` | commits unique to the local branch | Independent queue; never assumed part of PR #38 |

## Reconstruction algorithm

1. Refresh remote refs and record the exact candidate base SHA.
2. Capture and verify all three snapshots.
3. Build the complete salvage manifest from commit, path, hunk, review, and dependency evidence.
4. Obtain explicit confirmation for any hard-stop lane before touching it. Absence of confirmation means the lane remains parked.
5. Create a new clean worktree and branch at the recorded remote-main SHA.
6. Assert the reconstruction worktree is clean, including untracked files.
7. Adopt atomic commits with `git cherry-pick -x` when the entire commit belongs to one lane and passes review.
8. For mixed commits, extract only manifest-owned paths or hunks. Record the source SHA and stable patch ID. Add commit trailers:

   ```text
   Salvaged-From: <source-state> <full-source-sha>
   Salvage-Item: <manifest-item-id>
   Source-Patch-Id: <stable-patch-id>
   ```

9. Run the lane’s required checks before and after each bounded reconstruction unit.
10. Keep each commit single-purpose and each eventual PR independently reviewable.
11. Stop on provenance ambiguity, unexpected tree dirtiness, dependency drift, or evidence mismatch.

No reconstruction step mutates the source PR branch or the original local checkout.

## PR containment

After—and only after—snapshot checksums, bundle verification, and a complete first-pass manifest exist, PR #38 may be marked Draft and receive a stop-merge comment linking to the preservation record and reconstruction queue.

Containment does not mean closure, deletion, force-push, or history rewriting. The PR remains a reviewable source artifact until its salvage dispositions have been accepted and the human owner explicitly chooses its final lifecycle state.

## Verification spine

The verification spine is one Python entry point executed in the repository’s pinned Nix environment. It emits structured evidence and has explicit profiles:

```bash
nix develop -c python scripts/verify.py --profile preservation
nix develop -c python scripts/verify.py --profile core
nix develop -c python scripts/verify.py --profile phase0
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

Its public check name must say **Core checks — not Phase 0 proof**.

#### `phase0`

Includes every required `core` check plus Holochain-native proof. At minimum, it requires a Sweettest scenario with two independent agents that demonstrates publish, independent verification, query visibility, fork visibility where specified, and rejection of prohibited or invalid operations by integrity validation.

Until those tests exist and pass, `phase0` returns `BLOCKED` or `FAIL`; it cannot silently skip the missing proof and return success.

### Result semantics

Each step returns one of:

- `PASS`: the required command ran successfully and its assertions passed;
- `FAIL`: the command or assertion ran and failed;
- `BLOCKED`: the check could not run because a required capability or prerequisite is absent;
- `SKIPPED`: allowed only for steps declared optional by the selected profile.

An overall profile passes only when every required step is `PASS`. `BLOCKED` is never green. A passing `core` profile makes no claim about `phase0`.

### Evidence record

Every run emits JSON containing:

```text
schema_version
repository identity and commit SHA
dirty flag and porcelain digest
profile and runner version
environment and dependency fingerprints
start and finish timestamps
step id, command, cwd, duration, exit code, and result
stdout and stderr SHA-256 digests
bounded, sanitized output tails
artifact paths and digests
overall summary
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

## Failure and recovery rules

- Snapshot verification failure: stop before containment or reconstruction.
- Manifest coverage gap: stop adoption for the affected path or hunk.
- Dirty reconstruction tree: capture diagnostics and stop; do not auto-clean.
- Cherry-pick conflict: abort only the in-progress cherry-pick in the reconstruction worktree after recording diagnostics; do not alter source states.
- Baseline failure: classify it as pre-existing, introduced, blocked, or unknown using commit-pinned evidence. Never relabel it as passing.
- Hard-stop discovery: park the item and request explicit confirmation.
- Provenance mismatch: reject the candidate commit until source identity is resolved.
- Secret detection: exclude and redact; never persist the secret to evidence or memory.

## Acceptance criteria

The preserve-first design is ready for implementation planning when:

1. all three source states have named, checksum-verifiable snapshot procedures;
2. the manifest schema can assign every changed path or hunk exactly once;
3. each lane names dependencies, hard stops, and required verification;
4. reconstruction is guaranteed to start from an exact clean remote-main SHA;
5. atomic and mixed-commit provenance rules are unambiguous;
6. PR containment cannot precede verified preservation;
7. `preservation`, `core`, and `phase0` cannot be confused in commands, statuses, or CI labels;
8. missing Sweettest proof makes `phase0` non-green;
9. dirty-tree release evidence fails closed;
10. no step silently authorizes an ADR, integrity-zome, consensus-gateway, canonical, deletion, or protected-config change.

## Proposed implementation sequence

This is ordering, not implementation authorization.

1. Snapshot format, capture scripts, and verification tests.
2. Salvage-manifest schema, coverage checker, and rendered report.
3. Verified capture of the three live source states.
4. PR containment after preservation proof.
5. Verification-runner skeleton and JSON evidence schema.
6. `core` profile wired to existing repository checks, preserving known failures honestly.
7. Lane-by-lane reconstruction through small branches and reviewable PRs.
8. Sweettest Phase 0 scenario as a separately approved Holochain slice.
9. `phase0` profile enabled only when its symbolic proof is present.

## Non-goals

This design does not:

- merge, close, rewrite, or delete PR #38;
- decide the final disposition of every changed file without the manifest audit;
- modify canonical architecture or ADRs;
- change integrity-zome or consensus-gateway logic;
- claim Phase 0 verification from Python, Rust unit, Worker, or packaging tests alone;
- treat LLM agreement as truth;
- fold the 11 local-only commits into PR #38 by assumption;
- clean or normalize the original dirty checkout.

## Design rationale

The essential improvement is to make preservation and verification first-class products rather than incidental setup. A branch can be rebuilt; missing provenance, flattened local state, and falsely global green checks are much harder to recover from. This design therefore makes reconstruction downstream of verified capture, assigns ownership at path or hunk granularity, and separates ordinary engineering health from Holochain-native proof.
