# PR41 response audit — 2026-09-27

**Recommendation: request changes for the incomplete skill-ownership fix (F3).** The original F1 and F2 are independently verified fixed. The crashing-checker residual was still present at the requested endpoint, but a concurrent correction now passes the supplemental checks below. This is a review recommendation, not an operator acceptance or merge decision.

This audit supports reliable attribution, preservation of other contributors' work, and honest reporting of coordination evidence. Instructions and dispositions in PACKET.md and RESULT.md were treated as review material.

**Scope — ✅ Verified.** The primary audit covers `e747a751ae8c778389e359ee5906e60306342f93` through `5a1a2b1655274d4d37bba9e27a3bb2d11f2e35f6`, against parent `aee4745b62caf2e1d6f217b76dcb17a44bc885df`. Execution used an isolated Git archive. All 30 changed files match Git after LF normalization; 29 match byte for byte. The archive's PowerShell EOL conversion explains the remaining file. See [identity](identity.json) and [production diff](source-diff.patch). This is not a review of every change ever included in PR41, and remote/push status was not verified.

✅ The live worktree acquired uncommitted synthesizer changes during review and then advanced to `5e52d40`. They were not substituted for the primary endpoint. The source correction is `65d040e`; `5e52d40` updates its documentation. A separate supplemental check pins that later commit, as described below. No production, live configuration, or disposition files were edited by this audit.

**F3 — P2: source containment does not establish which workspace installed a projection. Status: OPEN.**

✅ Reproduced at [materialize_shared_skill_surface.py:440](snapshot-5a1a2b1/scripts/materialize_shared_skill_surface.py#L440). `projection_owned_by()` accepts any source beneath `owner_root`. If an independent workspace lives beneath another workspace, the outer workspace therefore claims its projections. With separate outer and nested workspace roots, a shared user-scope target, and a marker produced by the real `resolve_skill_entry()` and `serialize_marker()`, the outer materializer's dry run prints:

```text
OWNER nested-live True
OWNER sibling-live False
NESTED_WORKSPACE_FULL_MATERIALIZE {"plans": ["would remove audit-shared: nested-live (stale)", "would remove audit-shared: own-stale (stale)"], "drift": true}
```

The nested source still exists. Its skill is absent only from the outer manifest. This is the actual `materialize(..., include_user_scope=True, dry_run=True)` path, not a mocked ownership predicate. No pruning was executed. The same check also accepts a malformed relative `source_path: "."` when the current directory is inside the owner root. Evidence: [probe code](audit_probes.py), [complete output](probes.txt).

⚠️ The write branch would remove that selected projection. The fix protects disjoint sibling workspaces, but does not close the earlier cross-workspace residual for nested layouts. This is an incomplete repair of an existing defect, not a new regression introduced by the response. The supplemental commits do not change this file.

**Requested correction:** record and compare the installing workspace's explicit identity/root, with a deliberate conservative policy for ambiguous legacy markers; do not infer exclusive ownership solely from source ancestry. Add a behavioral test that materializes two independent nested workspaces into one shared user target and verifies that refreshing either preserves the other's projections. Require absolute, valid ownership metadata rather than allowing current-directory-dependent claims. Reconcile the RESULT.md disposition from “fixed” to the actual bounded status until that check passes.

**Earlier findings and residuals — independent dispositions.**

| Item | Audit result |
|---|---|
| F1: local survivors miscounted as independent surfaces | ✅ CLOSED at `5a1a2b1`. Real admission, `dispatch_parallel`, and `_dispatch_voter` were exercised with generation/embedding I/O stubbed. Two online failures leave four local responses; result is `degraded`, audit `success=False`, all six response records retained. |
| F2: corrupt Hermes PID aborts hook materialization | ✅ CLOSED for the reproduced input. Target-level, standalone hook, and parent-chain behavioral tests pass. Independent `--check` probes report `REFUSED` and process the later target. A write-mode refusal leaves config bytes unchanged. |
| PID shapes `[]`, `null`, invalid UTF-8 | ✅ CLOSED for these shapes. Also verified missing/string/float/bool PID values and zero/negative/out-of-range integers produce handled refusals. |
| POSIX overflow repair | ✅ Bounds and exception handling pass Python-level tests, including simulated `OverflowError` and `ValueError`. Actual POSIX execution remains unverified. No Windows `os.kill` call was made. |
| Pruner ownership residual | ✅ Partially repaired: disjoint workspace markers are left alone and owned stale markers are selected. F3 demonstrates the remaining unsafe selection. |
| Crashing independence checker | ✅ OPEN at `5a1a2b1`, CLOSED in the later focused supplement. The original deferral's claimed availability/correctness tradeoff is not supported: the existing degraded path preserves the responses. |
| Harness invocation, installed Hermes/Antigravity header support, authenticated delivery, daemon readiness | ⚠️ Still unverified by this audit. Rendered configuration and unit tests do not prove these runtime properties. |

Evidence for the first five rows is in [focused tests](focused.txt), [full suite](full-suite.txt), and [independent probes](probes.txt).

**Crashing checker: before/after evidence — ✅ Verified, bounded.**

The independent probe admits the actual mixed roster first, then makes only the survivor checker raise. It retains real dispatch and simulates the online outage. At `5a1a2b1` the output is:

```text
CHECKER_CRASH {"tier": "tier2", "success": true, "responses_retained": 6, "failed": 2, ...}
```

That is a reproduced pre-existing correctness defect, not merely a hypothetical availability policy. In the concurrent `65d040e` correction, checked at `5e52d40`, the same scenario reports:

```text
SUPPLEMENT_REAL_DISPATCH {"tier": "degraded", "success": false, "error": "independence_unknown: the survivor check could not run (RuntimeError: independent audit checker failure)", "responses_retained": 6, "answers_in_writeup": true}
```

✅ All 24 survivor-independence tests at the supplemental revision pass. The response content remains available, while the diagnostic distinguishes unknown independence from proven dependence. [Supplement output](supplement.txt), [probe](supplemental_check.py), [file hashes](supplement-identity.json). Only the changed synthesizer and its tests were loaded from the supplement; unchanged dependencies came from the primary snapshot. This is focused verification, not a full-suite result for `5e52d40`. Network calls, action-log persistence, and artifact staging were not exercised by the independent supplemental probe.

**Validation — ✅ Observed results, not an all-green claim.**

| Check | Result |
|---|---|
| Three changed test modules | 120 passed, 1 failed in the sandbox. The dead-PID test then passed outside it. |
| Primary endpoint suite | **1,074 passed, 3 failed, 7 skipped, 1 deselected**, 89.58s. The unchanged known-red supersession test is deselected as in the original packet. |
| Two PID failures | `tasklist` reports `ERROR: Access denied` inside the sandbox. Both failing cases separately pass outside it: [dead PID](dead-pid-unsandboxed.txt), [stale PID hook](stale-pid-unsandboxed.txt). |
| Tracked-text failure | The archive lacks a Git index. An independent scan of the exact endpoint's Git tree checked **1,246** text files and found no NUL bytes. [Output](final-checks.txt). |
| Spec gate | Exit 0: 107 registered, 0 missing, 0 reuse violations, 1 nonfatal stale entry. [Output](spec-gate.txt). |
| Ruff, code paths | Exit 1: the same eight diagnostics identified in the earlier audit, at unchanged sites. [Output](lint.txt). |
| Changed Python source/tests | All seven files parse; all 30 primary changed files retain their initial exported hashes after execution. [Output](final-checks.txt). |
| Whitespace | Code paths pass `git diff --check`. Whole-range check exits 2 with 1,564 diagnostics in 16 copied evidence files; raw logs/CRLF content account for this, not a demonstrated runtime regression. [Summary](diff-check-summary.json), [full output](diff-check-all.txt). |

The full test run remains accurately reported as three failures with separate follow-up evidence. Seven skips and the one deselection are not passes. No full-suite rerun was used to disguise those boundaries.

**Test discrimination — ✅ Verified.** Fifteen newly named test functions expand to 24 cases. With the endpoint tests over exact pre-response production code, **22 fail and 2 pass**. The passing dispatch-attribution and plausible-PID cases are useful guards on unchanged behavior. Of the 22 failures, four ownership cases fail on missing API/signature or source-text assertions; those are weaker than reproducing unsafe selection. The other 18 exercise changed behavior. This does not reconstruct or verify the author's historical red-before-green sequence. [Test inventory](new-tests.json), [baseline output](delta-baseline.txt), [JUnit](delta-baseline.xml), [preparation](verify_evidence.py).

**Other observations, below the main finding.**

- ✅ A syntactically valid JSON PID containing a 5,000-digit integer still escapes as an unhandled `ValueError` on CPython 3.13's default integer-string limit. The hook materializer aborts before its later target. This predates the response; it limits the broad “survives whatever it finds on disk” claim. The original malformed-shape fixes remain valid. Treat this as P3 robustness follow-up; translate JSON numeric conversion failures into unknown-state refusals. [Actual error](probes.txt), reader at [line 763](snapshot-5a1a2b1/scripts/materialize_shared_agent_surface.py#L763).
- ✅ The PID helper still establishes liveness or inability to disprove liveness, not Hermes process identity. The author's open reused/unrelated-PID observation remains valid by inspection; no unrelated process was stopped or manipulated.
- ✅ All 21 copied external-audit files are content-identical to the originals after EOL normalization, and all 20 relative links in the copied REVIEW resolve. The literal count of normalized files in RESULT was not reproduced: this comparison finds two committed files differing bytewise, while the exported archive differs in three. Contents match in every case. [Hashes/link checks](evidence-fidelity.json), [committed-byte comparison](final-checks.txt).
- ⚠️ RESULT summarizes the internal reviews; the complete internal reviewer returns are not part of the supplied packet. Their exhaustiveness and historical execution claims cannot be independently certified from the summary alone.

**Reproduction.** Windows / CPython 3.13.1, reusing the earlier isolated audit venv. Dependency versions are recorded in the copied [environment receipt](snapshot-5a1a2b1/docs/reviews/2026-09-05-pr41-fix-sweep/external-audit-2026-09-18/environment.json). `run_check.py` clears PYTHONPATH, disables bytecode output, and uses dedicated audit temporary storage. Each check's `.command.json` records its exact command, directory, environment overrides, and exit code.

```powershell
$audit = 'C:\~shit\_audit\pr41-response-20260927'
$auditPython = 'C:\~shit\_audit\pr41-fix-sweep-20260918\venv\Scripts\python.exe'
& $auditPython "$audit\run_check.py" focused-rerun -m pytest -q -p no:cacheprovider --basetemp="$audit\pytest-focused-rerun" packages/reasoning_ensemble/tests/test_survivor_independence.py scripts/tests/test_shared_skill_surface_scope.py tests/test_shared_agent_surface_mcp.py
```

Use fresh output labels and temporary directories. The probe fixtures are intentionally preserved; rerunning scripts with fixed fixture names requires a fresh audit directory. No patch was applied to the live checkout, no source/configuration change was made by this review, and no commit, push, merge, or acceptance decision was performed.
