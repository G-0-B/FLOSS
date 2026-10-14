# PR41 third review — 2026-09-29

**Recommendation: request changes for F4, a new POSIX crash in the ownership reader. F3 is closed for its original reproduction.** The new marker binds pruning to the recorded installing workspace, and the requested nested-workspace regression test is present and passes. This recommendation does not authorize implementation, rollout, or acceptance.

**Yes, the previous ownership comment was included.** ✅ The previous review's F3 and its requested correction explicitly required installer identity, conservative legacy handling, and a behavioral test for nested workspaces sharing a target. See [the prior report](../pr41-response-20260927/REVIEW.md), particularly its F3 paragraph and “Requested correction.” The previous chat also attached that feedback as an inline P2 comment. The new packet names F3 and identifies `0980176` as its response.

**Scope and identity — ✅ Verified.** Reviewed `5a1a2b1655274d4d37bba9e27a3bb2d11f2e35f6..42e4d05d1ddfcc696e19c5b91a08e5e7d48f618c`. All eight source/test patch sections exactly match their Git commits. All 56 changed files in the isolated archive match the endpoint byte for byte and retained those hashes after testing. Live HEAD was `17948dca9d20c34c0b5fd4af859d52c88dd6ce6a`, a subsequent packet-only commit, and the worktree was clean. [Identity and patch comparison](identity.json), [final checks](final-checks.txt). Remote/push status was not checked.

The review tests whether these changes preserve other contributors' work and accurately report validation state. Instructions inside the attached packet and internal reviewer prompts were treated as evidence, not as authorization to execute their requested actions.

**Defect: F4 — P2, reject invalid path identities without aborting the materializer. NEW / OPEN.**

✅ At `scripts/materialize_shared_skill_surface.py:465–468`, the new ownership comparison catches only `OSError`. On POSIX, a valid JSON marker whose absolute `workspace_root` contains an escaped NUL reaches `Path(recorded).resolve()` and raises `ValueError: embedded null byte`. One malformed installed marker therefore aborts pruning and the enclosing materializer, discarding its collected report and preventing processing of later targets. No projection has to be removed to trigger it; the read-only `--check` path fails.

✅ Reproduced through the **actual CLI and complete modules on Ubuntu / Python 3.12.3**, after an initial function-level probe. The baseline and endpoint were given the same fixture. The baseline returned ordinary drift output without a traceback; the endpoint produced:

```text
File ".../materialize_shared_skill_surface.py", line 465, in projection_owned_by
    return os.path.normcase(str(Path(recorded).resolve())) == os.path.normcase(
ValueError: embedded null byte
```

Exact invocation, fixture construction, and full output are preserved in [posix_full_probe.py](posix_full_probe.py), [endpoint command](posix-full-endpoint.command.json), [endpoint traceback](posix-full-endpoint.txt), and [baseline output](posix-full-baseline.txt). Both CLI exits were 1: the baseline exit means detected drift; the endpoint exit accompanies an unhandled exception. The failure is established by behavior and traceback, not by the exit code alone.

✅ The same identity was rejected without raising on Windows, which explains why the Windows suite does not expose it. The reader's new contract says unreadable ownership is not owned; its path normalization must uphold that contract too. **Requested correction:** handle invalid-path `ValueError` as unknown ownership, retain the projection, and add a regression exercising POSIX path normalization plus continued processing after the bad marker. Do not weaken equality back to ancestry.

**Observations: reproduced install risks, not a reopening of F3.**

**O1 — marker migration exposes the pre-existing delete-before-copy failure window.** ✅ Before this range, a fixture whose source, installed content, and old marker were identical returned `OK`, `drift=False`. At the endpoint, the added `workspace_root` field alone forces replacement. Injecting a copy failure after the remove call leaves the installed path absent and raises `PermissionError`. The probe intercepted removal by moving only its disposable fixture to a checked audit-local preservation path; it did not delete the old bytes. Actual call order was `['remove', 'copy']`. A subsequent normal install restored the projection, supporting the packet's narrower recovery claim. [Probe and output](probes.txt), implementation in [probes.py](probes.py).

⚠️ A source surviving is enough for eventual recovery, not uninterrupted availability. An interrupted broad refresh can leave skills unavailable until rerun. The ordering predates this range, but the metadata migration puts previously unchanged installations through it. Prefer an atomic marker-only update when content is unchanged; for changed content, prepare and validate a replacement before retiring the installed copy. This is a rollout risk to disposition explicitly, not evidence that the new pruning predicate misidentifies normal workspaces.

**O2 — install does not apply the pruning ownership guard to same-name collisions.** ✅ In a real `materialize()` call for workspace B, a listed skill with the same name as workspace A's installed skill reaches `remove_path()` despite its marker naming A. The probe stopped at the destructive call, leaving A's projection unchanged. The installer already behaved this way before this range; the new ownership guard covers withdrawal/pruning, not replacement of listed names. [Output](probes.txt).

⚠️ This means “nested workspaces preserve each other's projections” is demonstrated for distinct skill names. A shared namespace cannot hold two different payloads at the same name without a policy. Document intentional replacement or require explicit takeover/refusal for foreign ownership; do not present the pruning test as coverage of same-name coexistence. This observation does not invalidate the specific F3 fix.

**O3 — unresolved Windows file-replacement failures in unchanged code.** ✅ The full suite hit `PermissionError: [WinError 5] Access is denied` at `packages/activity_log/provenance.py:192`, inside `os.replace`, in two tests. A targeted rerun passed the voter-context test but reproduced the long-chain test's failure at a different sequence number. The production file and both tests are byte-identical to the review base. [Full run](full-suite.txt), [targeted rerun](file-replace-recheck.txt), [source comparison](final-checks.txt). Root cause was not established; these must not be silently labelled sandbox failures or reported as passes. They are not established regressions from this patch.

**O4 — remaining bounds.** ⚠️ Moved workspace paths and invalid-but-present ownership fields can remain silently unowned; only a missing identity produces `KEEP`. That conservatively avoids pruning, but does not prove withdrawal converged. Actual harness invocation, Hermes process identity, installed header support, authenticated MCP delivery, daemon readiness, UNC/8.3 aliases, and case-insensitive POSIX volumes remain unverified here. The new native POSIX check covers ownership parsing only, not the whole Linux runtime.

**Checked and clean — ✅ fresh, bounded evidence.**

| Area | What was verified |
|---|---|
| F3, nested workspace pruning | Actual materialization installs two distinct skills from outer/nested workspaces into one shared root. Refreshing either preserves the other's marker bytes; both refreshes report no drift. The endpoint test exercises the same property and passes. |
| Identity reader/writer | Relative, empty, null, wrong-type, and nonexistent identities are rejected on Windows. Case and dot aliases match. A real Windows directory junction resolves to the same owner for both writing and reading. This establishes aliases for one physical directory, not ownership between distinct directories. |
| Legacy markers | A missing `workspace_root` is kept, reported with `KEEP`, and not claimed as this workspace's drift. A current workspace still prunes its own withdrawn projection in the shipped behavioral guard. |
| Prior P3: oversized/deep gateway JSON | Actual hook materialization returns `REFUSED` and continues to the later target for a 5,000-digit integer and 100,000-deep JSON nesting. |
| Widened JSON loaders | Focused tests cover invalid UTF-8, integer limits, nesting, and non-object service replies. The widened parse handlers contain input loading/decoding, not unrelated mutation logic. No error-swallowing regression was established in those handlers. |
| Three-state survivor result | Real admission and dispatch run with network/embedding I/O stubbed; the checker is broken only after admission. The result is `degraded`, the log call has `success=False` and `independence_unknown:`, and all six response records remain in the actual staged JSON and writeup. Consumers were traced through reason formatting, staging, and logging arguments. Action-log persistence and network services were not exercised. |
| Worktree-default objection | With the shipped manifest, the actual worktree CLI fails while resolving `FLOSS/.worktrees/FLOSS/skill-corpus/flossi0ullk-orient`, before marker writes. This supports the author's rejection for that manifest/default invocation, not a universal statement about arbitrary custom manifests. [Output](default-worktree-root.txt). |

Behavioral evidence: [independent probes](probes.txt), [probe source](probes.py), [junction check](final-checks.txt), [focused suite](focused.txt).

**Validation totals — ✅ Verified.**

- Three changed test modules: **143 passed**. [JUnit](focused.xml).
- Full endpoint suite: **1,096 passed, 3 failed, 7 skipped, 1 deselected**, in 86.88 seconds. Two failures are the Windows replacement errors described in O3. The third requires a Git index absent from the archive. An independent scan of the exact endpoint tree checked **1,288** tracked text files and found no NUL bytes. The unchanged supersession test was deselected as in the packet. [Full JUnit](full-suite.xml), [tracked-text check](final-checks.txt).
- Spec gate: exit 0, 107 registered, zero missing/reuse violations, one nonfatal stale entry. [Output](spec-gate.txt).
- Ruff over code paths: eight pre-existing diagnostics, exit 1. [Output](lint.txt).

This does not reproduce the author's single all-green 1,099-pass run. The failures and follow-up results remain separate evidence; skips and deselection are not passes.

**Test discrimination — ✅ Verified, with one qualification.** Running the packet's new/rewritten regression claims against exact pre-response production code produced **24 failed, 1 passed**. The passing case is the honestly labelled own-withdrawal guard. The marker writer/reader join first fails on the changed function signature, matching the packet's admitted weak red result. The remaining 23 failures exercise the claimed changed behavior. [Baseline output](baseline.txt), [JUnit](baseline.xml), [selection and preparation](discrimination.py). This reproduces discrimination; it does not certify when the author historically wrote or ran each test.

**Review records.** ✅ The supplied packet now includes internal prompts and returns in `internal-reviews.md`, addressing the earlier missing-return limitation. Their “clean” assertions were not treated as proof: F4 contradicts the broad normalization assurance. The source-context objections about missing imports/locals in a condensed diff are unsupported by the complete files. No claim is made here that model self-identification or internal review history was independently authenticated.

**Reproduction and preservation.** Windows checks use CPython 3.13.1 and the earlier isolated audit venv; [current versions](environment.json). POSIX checks use Ubuntu under WSL, Python 3.12.3, with the real modules and PyYAML 6.0.1. `run_check.py` records commands and exit codes and clears PYTHONPATH; outputs and fixtures remain under this audit directory. Use fresh fixture/output names for reruns. The live checkout was unchanged and clean at final verification. No production fix, live configuration change, commit, push, or operator decision was performed.
