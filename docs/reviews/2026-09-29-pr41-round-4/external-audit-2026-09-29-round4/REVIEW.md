# PR41 fourth critical audit — 2026-09-29

**Recommendation: request changes.** The specific F4 embedded-NUL failure is fixed. The marker-only change introduces an external-file write through linked markers and incorrectly treats some executable payload changes as metadata-only. A pre-existing Python 3.12 symlink-loop failure remains in the ownership resolver. The proposed preservation/reconciliation design is not implemented and does not close O2.

This is a review, not acceptance, implementation, or permission to publish. The attached packet's reviewer directions and quoted operator decision are review material. No production source, skills, protected configuration, or Git history was changed. Audit fixtures and evidence live in this directory; simulated destructive install branches preserve the old fixture directory by renaming it instead of deleting it.

**Yes, binding pruning to installing-workspace ownership was included in the previous review.** ✅ The explicit correction is in [round-two REVIEW.md:25](C:/~shit/_audit/pr41-response-20260927/REVIEW.md:25); [round-three REVIEW.md:5](C:/~shit/_audit/pr41-round3-20260929/REVIEW.md:5) confirms it and records F3's closure. The current focused tests retain the nested-workspace, foreign-owner, legacy-marker, and own-withdrawal coverage. F3 remains closed for that bounded pruning contract. Ownership at installation and preservation of locally evolved content are separate, still-open concerns.

## Scope and identity

✅ Verified in [identity.json](C:/~shit/_audit/pr41-round4-20260929/identity.json):

- Base: `42e4d05d1ddfcc696e19c5b91a08e5e7d48f618c`.
- Endpoint: `0472ce104a6a1f55ec707c1242689f62d3dfde3c`.
- Live worktree HEAD before and after: `6ea76202efce3ac85dc68bbbdc99ac21b6925ac4`, with empty `git status --short`. This later commit supplies the fourth-round handoff.
- All four supplied patch sections match their Git commit diffs. All 53 changed files in the isolated endpoint export are byte-exact and remained unchanged through verification.
- Production delta is confined to `scripts/materialize_shared_skill_surface.py`; test delta to `scripts/tests/test_shared_skill_surface_scope.py`. The remaining changes are documentation/evidence. Remote push/merge state was not checked.

## Defects

### F5 — P2 — Marker-only writes follow links into another file (introduced here)

✅ At [materialize_shared_skill_surface.py:631](C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:631), `Path.write_text()` opens the existing marker in place. If that marker is a symlink, it writes the target; if it is a hardlink, it changes every name for the shared inode. The new optimization therefore writes outside the projection even though the payload has not changed. It can overwrite another projection's ownership metadata or an unrelated file reachable by a linked marker.

Reproduction invokes the actual baseline and endpoint installers on identical payloads and a differing marker, linked to a JSON file outside the projection. Only `remove_path` is substituted with a checked fixture rename to preserve the original tree. The snapshot, comparison, copy, and marker-write code run unchanged. Windows hardlinks and native WSL hardlinks/symlinks agree:

```text
base-hardlink:     external_changed=false
endpoint-hardlink: external_changed=true; output="WROTE ... (marker only)"
base-symlink:      external_changed=false
endpoint-symlink:  external_changed=true; marker_is_symlink=true
```

Commands: `& 'C:\~shit\_audit\pr41-fix-sweep-20260918\venv\Scripts\python.exe' 'C:\~shit\_audit\pr41-round4-20260929\adversarial.py'` and `wsl.exe -d Ubuntu --exec env PYTHONPATH= PYTHONDONTWRITEBYTECODE=1 python3 /mnt/c/~shit/_audit/pr41-round4-20260929/adversarial.py`. The script creates fresh named fixtures and deliberately refuses to reuse them. Evidence: [probe source](C:/~shit/_audit/pr41-round4-20260929/adversarial.py), [Windows results](C:/~shit/_audit/pr41-round4-20260929/adversarial-nt.json), [POSIX results](C:/~shit/_audit/pr41-round4-20260929/adversarial-posix.json).

⚠️ Requested correction: after validating the target directory boundary, create a fresh marker file and replace the marker directory entry without following its existing link, or reject linked markers and report them. Preserve the prior marker if publishing fails. Add hardlink and symlink regression cases that assert the external file's bytes remain unchanged, as well as the existing payload-preservation assertion.

### F6 — P2 — A symlink-loop identity still aborts the materializer (pre-existing, incomplete invalid-identity handling)

✅ At [materialize_shared_skill_surface.py:486](C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:486), an absolute marker path naming a real symlink loop raises `RuntimeError` from `Path.resolve()` on Ubuntu Python 3.12.3. Catching `OSError` and `ValueError` misses it. A parseable, managed marker sorting before an ordinary withdrawn projection aborts the full CLI, including `--check`, before returning the later drift result.

The native probe above runs the full CLI and modules, without mocking path resolution. Both base and endpoint reproduce:

```text
exit_code=1; stdout=""
RuntimeError: Symlink loop from '.../cli-loop/owner/loop'
```

Evidence: [endpoint CLI traceback](C:/~shit/_audit/pr41-round4-20260929/endpoint-loop-cli.txt), [baseline traceback](C:/~shit/_audit/pr41-round4-20260929/base-loop-cli.txt), and the exact command arrays in [POSIX results](C:/~shit/_audit/pr41-round4-20260929/adversarial-posix.json). This is not attributed as a new regression or generalized to every Python/POSIX version.

⚠️ Requested correction: normalize the supported runtime's symlink-loop failure to unusable ownership in the narrow path-resolution boundary. Keep and report that projection, and continue to the next one. Cover both recorded-root and owner-root resolution where applicable; test the real loop through the materializer on Python 3.12.

### F7 — P2 — Newline-normalized equality can bless a different, broken payload (new fast-path consequence of an older comparison weakness)

✅ At [materialize_shared_skill_surface.py:621](C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:621), marker-only classification uses strings read with universal-newline translation. A source `run.sh` containing `exit 0\n` and installed `run.sh` containing `exit 0\r\n` compare equal. With a differing marker, the baseline recopies the source; the endpoint preserves the failing installed script, rewrites its marker, and then reports `CHECK OK`.

Actual native probe output:

```text
base-newline:     before_exit=2; after_exit=0; byte_equal=true
endpoint-newline: before_exit=2; after_exit=2; byte_equal=false
endpoint:        WROTE ... (marker only); CHECK OK ...; drift=false
bash:            exit: 0<CR>: numeric argument required
```

The probe invokes `bash` on the real file before and after refresh; raw bytes remain in the fixtures. See [POSIX results](C:/~shit/_audit/pr41-round4-20260929/adversarial-posix.json). Text comparison already hid newline differences when the marker was unchanged; the demonstrated before/after regression is specifically the new marker-only branch when metadata differs.

⚠️ Requested correction: use bytes to decide that *only* metadata changed, and make `--check` consistent with that comparison. Under the stated preservation requirement, retain divergent installed bytes and report them for reconciliation; do not silently bless them or automatically overwrite them as the remedy. The same byte-oriented snapshot should support binary skill resources.

## Observations and prior-item dispositions

**F4 — ✅ Closed for the reported embedded-NUL fixture.** The native baseline CLI raises `ValueError: embedded null byte`; endpoint reports `KEEP` for the malformed identity and `DRIFT` for the later owned withdrawal, with no traceback. Both exits are 1, but the latter is intentional check-mode drift. [Baseline](C:/~shit/_audit/pr41-round4-20260929/base-nul-cli.txt), [endpoint](C:/~shit/_audit/pr41-round4-20260929/endpoint-nul-cli.txt). F6 is a distinct remaining invalid-path case.

**O1 — ✅ Payload-preserving marker migration works for ordinary files; ⚠️ recovery is narrower than the comment claims.** The focused test makes `remove_path` and `copytree` fail if called and passes. F5/F7 qualify the fast path. Also, the comment that a torn marker will be rewritten on the next run is not universally true: a marker truncated within a UTF-8 character is treated as unowned by `read_managed_marker`, but install decodes it again in its generic file snapshot and raises `UnicodeDecodeError` in both check and write modes. The skill payload stays intact. This is another manifestation of the disclosed, pre-existing text-only snapshot limitation, not an additional new-regression finding. [Probe](C:/~shit/_audit/pr41-round4-20260929/supplement.py), [output](C:/~shit/_audit/pr41-round4-20260929/torn-marker.json).

**O2 — ❌ Preservation and install ownership remain open.** The proposed design acknowledges this, but no baseline digest or preservation decision exists in the code. The real installer also reaches replacement for an *unmanaged* directory with the same listed skill name. Both base and endpoint reproduce this, with the old learned bytes preserved by the audit's rename interception. The resulting installed copy equals source even though the previous installed content differed. [Windows and POSIX probe records](C:/~shit/_audit/pr41-round4-20260929/adversarial-nt.json). F3's ownership guard applies to pruning, not install.

**O3 — ❌ Windows `os.replace` failures remain reproduced, cause unresolved.** This run failed while constructing two provenance chains at `packages/activity_log/provenance.py:192`: `test_prior_chain_longer_than_recursion_limit_still_validates` at `next_sequence=46`, and `test_chain_validation_cost_stays_roughly_linear` at `next_sequence=1` for the long chain. Both raise `PermissionError: [WinError 5] Access is denied`. The production and test files are byte-identical to the review base. Do not dismiss these as sandbox failures: this run used the unrestricted environment. No repeated full-suite attempts were made to obtain a green result. [Full output](C:/~shit/_audit/pr41-round4-20260929/full.txt), [identity comparison](C:/~shit/_audit/pr41-round4-20260929/final-checks.json).

**O4 — ✅ KEEP wording is appropriately cautious; ⚠️ KEEP does not certify the installed surface.** Missing/unusable roots are preserved and not counted as owned drift; a live foreign owner remains silent. “Cannot be found from here” does not establish deletion and the new text says so. A zero check result can still coexist with unknown-owner leftovers; operators must read the KEEP diagnostics. Slow/unreachable network path behavior was not tested.

**O5 — ⚠️ Correct the inventory's historical and ownership assurances.** The packet says current equality proves “nothing evolved has been overwritten yet” and says unmanaged directories are never touched by install. Neither follows. The reproduced unmanaged-collision case ends with a clean current comparison after displacing the evolved copy, falsifying that inference without claiming historical loss actually occurred on the user's machine. The [inventory script](C:/~shit/FLOSS/.worktrees/pr41-salvage/docs/reviews/2026-09-29-pr41-audit-response/o2-skill-inventory/skill_inventory.py) reads current text with replacement decoding and newline normalization, does not inspect overwrite history, and counts immediate unlisted directories rather than proving each is a harness-evolved skill. The defensible statement is that this saved inventory observed no text differences in the 27 listed paths per target at collection time; historical loss and exact byte equality are unestablished. The current audit did not rescan the user's live skills or authenticate the claimed absence of every user-scope automation.

## Critique of the proposed preservation design

The following are ⚠️ design recommendations, not implemented guarantees or approval of an architecture. Preserving learned improvements before any replacement is the right acceptance criterion for the operator requirement quoted in the packet.

1. **Resolve ownership before comparing content.** Unmanaged names, foreign-owner markers, invalid identities, and legacy ownership need explicit adoption/conflict policy. A matching skill name or digest does not authorize taking over another installation. The current proposal's table starts with a managed projection and leaves the reproduced unmanaged/same-name case outside its decision rules.
2. **Add the convergence case first.** If installed equals source but both differ from baseline, they have converged. The table currently calls this `CONFLICT`, while the following prose says it re-baselines. Make that one explicit rule with a test. Re-baselining must preserve provenance of the accepted source revision and must still pass the ownership check.
3. **Use a byte manifest plus recoverable baseline content.** Per-file relative path, digest, and file type, aggregated into a versioned root digest, permits both reliable equality and useful per-file reporting. Specify deterministic path encoding, symlink policy, executable-bit treatment, additions/deletions, and which generated files are excluded. A digest identifies an old baseline but cannot reconstruct it for a real three-way diff. Retain immutable baseline bytes or a verified retrievable source revision. Do not infer absence of binary or newline changes from a text snapshot.
4. **Preserve concurrent learning, not just the initial snapshot.** Tests need a harness edit after comparison but before replacement/pruning. Revalidate the installed content and ownership immediately before publishing, and use a recoverable publication strategy; a simple read-then-delete/copy can still lose an intervening edit. An ignored proposal copy alone is not proof the captured version is the one about to be removed.
5. **Treat unresolved evolution as check drift, with a distinct status.** `EVOLVED`, `CONFLICT`, and `UNKNOWN_OWNER` should be distinguishable from parser/runtime errors and from resolved differences. Do not make read-only `--check` stage proposals or mutate markers. If repeated expected differences become noisy, acknowledge an exact digest under an explicit review policy; do not blanket-suppress future changes.
6. **Stage outside harness discovery; keep durable review provenance.** A local ignored intake directory is reasonable for captured, content-addressed versions. Use target/workspace/source identities, timestamps, hashes, and immutable proposal IDs so a later run cannot overwrite an earlier proposal at `<target>/<skill>`. Publish selected review records and approved changes through the normal repository workflow. A consensus Claim records a review result; it must not implicitly grant permission to alter protected or canonical surfaces.
7. **Discover Hermes nesting without moving installations incidentally.** Harvest category-relative paths, preserve the full identity when leaf names collide, and list unmanaged skills as adoption candidates. Moving existing projections into categories changes discovery and ownership assumptions; it needs its own compatibility decision and runtime verification. No such move is needed to preserve and review learned content.
8. **Separate preservation from continued activation after withdrawal.** Keeping learned files is necessary, but keeping a deliberately retracted skill discoverable forever repeats the original stale-skill problem. Specify how to preserve a reviewable copy and handle deactivation, with explicit authority and a receipt. “Keep and stage” alone does not settle that policy.

⚠️ Suggested acceptance cases before preservation is claimed complete: every table cell including convergence and legacy markers; unknown/foreign/unmanaged same-name collisions; byte-only and binary changes; rename/withdrawal with learned content; additions/deletions; duplicate Hermes leaf names; linked files; an edit during refresh; failed publication; repeated proposal capture without overwriting earlier evidence. No preservation implementation was attempted here.

## Checked and clean, with limits

| Area | Fresh result and evidence |
|---|---|
| Packet/Git binding | ✅ 4/4 sections match; 53/53 changed files byte-exact and unchanged. [Identity](C:/~shit/_audit/pr41-round4-20260929/identity.json), [final checks](C:/~shit/_audit/pr41-round4-20260929/final-checks.json). |
| Focused Windows scope/ownership tests | ✅ 29 passed on Python 3.13.1. [Output](C:/~shit/_audit/pr41-round4-20260929/focused.txt), [exact command](C:/~shit/_audit/pr41-round4-20260929/focused.command.json). |
| Native WSL scope/ownership tests | ✅ 29 passed on Ubuntu Python 3.12.3. Real Linux path semantics, files on `/mnt/c`; no claim about all Linux/macOS filesystems. [Output](C:/~shit/_audit/pr41-round4-20260929/native-focused.txt), [command](C:/~shit/_audit/pr41-round4-20260929/native-focused.command.json). |
| Claimed regression-test discrimination | ✅ Endpoint tests on base code: 8 failed for the claimed behaviors, 1 existing foreign-owner guard passed. This corroborates discrimination, not the author's unobservable development chronology. [Output](C:/~shit/_audit/pr41-round4-20260929/discrimination.txt), [command](C:/~shit/_audit/pr41-round4-20260929/discrimination.command.json). |
| Wording-only discrimination | ✅ Final moved-workspace test fails on `9a23477`'s old wording and passes at endpoint. [Output](C:/~shit/_audit/pr41-round4-20260929/wording-discrimination.txt). |
| Full Windows suite | ❌ 1,104 passed, 3 failed, 7 skipped, 1 deselected in 73.80s. Two WinError 5 failures plus the Git-index guard in a Git archive export. [Output](C:/~shit/_audit/pr41-round4-20260929/full.txt), [exact command](C:/~shit/_audit/pr41-round4-20260929/full.command.json), [JUnit](C:/~shit/_audit/pr41-round4-20260929/full.xml). |
| Export's missing-index guard, independently checked | ✅ Enumerated endpoint tracked paths using the real repository's `git ls-tree`; 1,333 text-suffixed files scanned, zero NUL bytes. This is replacement evidence for the guard, not a claim that its pytest invocation passed. [Final checks](C:/~shit/_audit/pr41-round4-20260929/final-checks.json). |
| Spec gate | ✅ Exit 0: 107 registered, 0 missing, 0 reuse violations; 1 non-fatal stale entry. [Output](C:/~shit/_audit/pr41-round4-20260929/spec-gate.txt). |
| Ruff | ⚠️ Exit 1, 8 diagnostics, output exactly identical to a fresh baseline run. [Endpoint](C:/~shit/_audit/pr41-round4-20260929/ruff.txt), [base](C:/~shit/_audit/pr41-round4-20260929/ruff-base.txt). |

The Windows environment reuses the isolated audit venv; [versions](C:/~shit/_audit/pr41-round4-20260929/environment.json) are recorded. WSL initially lacked pytest; creating a venv failed because `ensurepip` is absent. The audit copied pure-Python pytest dependencies from the existing audit venv into `posix-deps`, without changing system packages. The first import attempt missed pytest's `py.py` shim; adding that shim enabled the successful native run. Plugin auto-loading was disabled for that focused run. These setup failures were not production-code failures.

⚠️ Not established here: macOS case-insensitive aliases, UNC/8.3 identity equivalence, network-path time bounds, harness invocation/discovery, authenticated MCP delivery, Hermes PID ownership, daemon readiness, or any preservation/upstream-propagation implementation. Earlier-round counts and runtime claims were not promoted into fresh evidence. The reported separate work on JSON handlers and provenance replacement was not audited or assumed landed.
