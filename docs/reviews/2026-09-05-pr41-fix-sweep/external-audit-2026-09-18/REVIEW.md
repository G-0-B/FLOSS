# PR41 fix-sweep independent audit — 2026-09-18

Reviewer recommendation: **request changes**. Two reproduced issues prevent approval of the fix claims: mixed-mode survivor independence remains unsound, and the new Hermes liveness exception is not handled by every caller. This is a noncanonical review artifact, not an operator disposition or permission to modify, publish, or merge the fixes.

The audit supports reliable attribution and independent scrutiny of the commons' coordination infrastructure. Instructions inside the supplied packet were treated as review material, not as authority to perform its suggested actions.

**Scope and identity — ✅ Verified.** Reviewed the seven supplied commits, from the parent `2f1151b3bc1a08836f654d972671f92c0f78f7d1` through `303b1f99da0b14c9d4a7c69e2f628f38a03f1d85`. All 14 source/test patch sections match the corresponding Git diffs. The two excluded commits, `616deaa` and `e2d02af`, are present in the endpoint used for execution but are not credited as fixes in this review. The current worktree HEAD is `aee4745b62caf2e1d6f217b76dcb17a44bc885df`; its later source-chain change was not substituted for the requested endpoint. Remote/push status was not checked.

Evidence: [patch fidelity](./patch-fidelity.txt), [audited file hashes](./audited-files.json). The exported snapshot has matching Git bytes for 16 of 17 affected files; the PowerShell script has archive-applied CRLF endings and identical LF-normalized text. The reviewed worktree remained clean. Production files, live configuration, daemons, and review dispositions were not changed.

**F1 — P1: normalize transport before checking mixed-mode survivors. OPEN.**

✅ Verified at `packages/reasoning_ensemble/synthesizer.py:521-529`, especially the dictionary at line 528, in conjunction with `transport.py::_independence_route`.

The pool admission check reconstructs `ollama/<model>` before counting provider surfaces. The survivor check instead passes each response's raw `model`, ignoring its existing `transport_name`. The shipped local pool therefore becomes four apparent providers: `phi4-mini:latest`, `llama3.2:...`, `granite-code:...`, and `hf.co`. Removing the mixed-mode exemption activates the check without making its inputs equivalent to admission's inputs.

Reproduction uses the real shipped four-entry local pool, no degraded override, and profile `diverse`. Admission correctly reports **one provider surface**. The same four survivors produce `None` from `_survivor_independence_problem`, meaning no independence problem. A fuller probe admits two online voters plus the local pool using the real resolver/check, simulates both online voters failing, and calls the real synthesis function with four distinct local embeddings. Output:

```text
F1 same local-only survivors: None
F1 full synthesize after simulated online outage: tier2 success= True
```

This is an unclosed defect in the fix, not evidence that every earlier mixed-mode run was safe. The range also newly admits narrow-online-plus-local combinations, making consistent survivor accounting essential. No provider calls or durable synthesis writes were made by the probe.

⚠️ Specified correction: use the same transport-aware route construction at admission and survival, mapping `VoterResponse.transport_name` into it. Add a regression through `synthesize()` with the shipped local pool and failed online voters; require `degraded` and an unsuccessful audit result while retaining the responses.

Test gap: the new mixed-survivor test at `packages/reasoning_ensemble/tests/test_survivor_independence.py:78` uses three already-prefixed Groq models. It does not exercise the bare Ollama names this change exposes. The admission-side helper test correctly covers those names, but never sends them through the survivor path.

**F2 — P2: propagate the Hermes partial-function contract into the hook materializer. OPEN.**

✅ Verified at `scripts/materialize_shared_agent_surface.py:744-768` and its unadapted consumer `scripts/materialize_shared_hook_surface.py:726`.

`hermes_gateway_alive()` now raises `SharedSurfaceError` for malformed or unreadable PID files. Commit `303b1f9` catches it in the MCP materializer, but `hermes_gateway_alive_for()` delegates to the same helper and `apply_yaml_target()` calls that delegate without handling the exception. The parent materializer later invokes the hook sub-materializer as well. Handling the earlier MCP call does not protect that later call.

Reproduction creates an isolated `config.yaml`, a `gateway.pid` containing `not json{`, and a two-target hook manifest. Both the YAML target function and the full hook `materialize(..., check=True)` raise `SharedSurfaceError`; the latter never returns accumulated results or processes the later target. The configuration bytes remain unchanged. Output:

```text
F2 YAML --check path: SharedSurfaceError ... exists but is not valid JSON ...
F2 full hook materialize --check: aborted SharedSurfaceError
```

⚠️ Specified correction: handle this refusal at the YAML target boundary, returning a `REFUSED` result and drift state, so the caller continues and ultimately exits nonzero with its findings intact. Keep the refusal to write. Exercise both standalone hook and parent materializer execution, rather than only the changed call site.

Test gap: `test_a_corrupt_pid_file_is_reported_not_raised_through_materialize` at `tests/test_shared_agent_surface_mcp.py:1330` creates a corrupt fixture but only inspects source text for a `try` and an `except`. It never invokes `materialize()` and cannot detect the unadapted sibling caller.

Both findings are independently reproducible with [audit_probes.py](./audit_probes.py); complete output is in [probe-results.txt](./probe-results.txt).

**Validation and positive dispositions.**

| Area | Result and evidence |
|---|---|
| Full endpoint suite | ✅ `1051 passed, 3 failed, 7 skipped, 1 deselected` in 88.94s. [Full output](./full-suite-final.txt), [JUnit](./full-suite-final.xml). Same known-red deselection as the packet. |
| Three initial failures | ✅ Two tests require Windows `tasklist`, which returned `ERROR: Access denied` inside the sandbox. Both pass when rerun outside it: [output](./process-check.txt). The third requires a Git index absent from an archive; it passes in the current worktree. An independent scan of the exact endpoint's tracked inventory found no NUL bytes in 1,225 text files: [output](./snapshot-text-check.txt). These are environment/export limitations, not reproduced fix regressions. This was not one all-green 1054-test run. |
| Spec gate | ✅ Exit 0: 107 registered, zero missing, zero reuse violations, one nonfatal stale `research_log.py` entry. [Output](./spec-gate.txt). Matches the packet. |
| Ruff | ✅ Eight diagnostics, exit 1, under Ruff 0.15.11; the same eight appear with baseline production code and endpoint tests. [Endpoint](./ruff.txt), [baseline](./ruff-baseline.txt). No new lint diagnostic found; the packet's count of nine did not reproduce. |
| PowerShell dispatch | ✅ Executed the actual parsed dispatch conditions for all 12 combinations of verdict, path existence, and reservation status. Launch-containing body replaced with a stub; no process launched. All combinations match intended dispatch. [Harness](./powershell-dispatch.ps1), [results](./powershell-results.txt). Fresh reservations correctly reach the reservation primitive and can be refused as occupied. The author's pushback on the double-message objection is supported. Full daemon startup/readiness was not exercised. |
| Claim failure distinction | ✅ Changed daemon tests pass in the full suite: lock-helper/import and guarded OSError failures are distinct from genuine occupancy; `run_http_daemon` exits nonzero for `ClaimUnavailable`. The caller inventory contains one production `claim_singleton` caller, now adapted. |
| Synthesis unreadable files | ✅ Changed tests pass, including a real invalid-UTF-8 input that must not be staged. Both first-attempt and retry paths call the same pending classifier/recorder. The retry-unreadable branch lacks a dedicated behavioral test; its source-text guard is narrower evidence. No new defect reproduced there. |
| Header projection | ✅ OpenCode/Codex projection and stale-header tests pass. Codex CLI `0.154.0-alpha.6.2` accepts a command-line-only HTTP configuration and reads back `http_headers`: [readback](./codex-header-readback.txt). [Official documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) also specifies the key. This closes key-name uncertainty, not authenticated network delivery or all target-client compatibility. |
| TOML ordering | ✅ The explicitly labelled scalar-ordering complement also passes against the immediate pre-fix parent `05f60e0` with tomlkit 0.15.0. Its non-discriminating status is honestly documented. |
| Hook attribution | ✅ Managed registration, known labels, parser precedence, and materialized command checks pass. This supports declaration plumbing. Actual invocation by each installed harness was not exercised. |
| Skill withdrawal | ✅ Included withdrawal, unmanaged-directory, and read-only drift tests pass. Cross-workspace ownership remains a separate concern below. |

**Test discrimination audit — ✅ Verified, bounded.**

The 45 newly added test functions were run with endpoint tests over pre-sweep production code: **36 failed, 9 passed**. [Results](./baseline-tests-final.txt), [JUnit](./baseline-tests-final.xml), [passing cases](./baseline-passing-complements.txt), [preparation script](./prepare_baseline.py). This is an aggregate baseline experiment, not a reconstruction of the author's historical per-commit runs.

The passing cases mostly check unchanged behavior: single-surface refusal, genuine contention, Gemini/Claude attribution, absent Hermes PID, absent headers, unauthenticated Antigravity, and the transport-flip fixture. The last passes on the aggregate baseline because headers were never emitted there; it does not prove that later header cleanup is unnecessary. Several failing tests merely reference new helpers/constants absent on the baseline, which is weaker evidence than observing the old incorrect behavior. Test counts alone are not assurance of the claimed guarantees. The F1 and F2 reproductions fail outside the suite's current coverage while the relevant shipped tests pass.

**Residual concerns retained separately; not additional established regressions.**

- ✅ `gateway.pid` values `[]`, `null`, and invalid UTF-8 still yield `AttributeError`/`UnicodeDecodeError` instead of the new handled refusal type. These are pre-existing input-shape gaps, reproduced in [probe-results.txt](./probe-results.txt). The broad claim that `--check` survives anything on disk is unsupported.
- ✅ The new stale-skill pruner checks marker-file existence but not its contents or source ownership. A marker naming another workspace still receives a `would remove` plan when its skill is absent from this manifest; the dry-run reproduction is preserved. ⚠️ On shared user-scope roots, older/different manifests can therefore select another workspace's projection for removal. No real projection was deleted; intended cross-workspace ownership policy needs an explicit disposition.
- ✅ The existing survivor helper treats an exception from the independence checker as `None`; an existing test intentionally pins that behavior. ⚠️ A failed check therefore remains indistinguishable from a successful independence check. This behavior predates the selected range and is not presented as a newly introduced fix regression.
- ⚠️ Linux behavior, installed Antigravity/Hermes HTTP-header support, actual harness invocation/trust, authenticated MCP delivery, and daemon readiness remain unverified. WSL enumeration was denied in this sandbox. Schema/rendering success does not establish these runtime properties.

**Reproduction environment and boundaries.**

Windows, CPython 3.13.1; isolated audit virtual environment with system site packages. Missing test/runtime dependencies were installed only into that environment. Versions are recorded in [environment.json](./environment.json). Tests used a dedicated writable temporary directory after the default temporary location caused setup errors. Dependency versions are this audit's environment, not a reconstructed historical lockfile.

Main commands, from `snapshot-303b1f9`, with `PYTHONPATH` cleared:

```powershell
& ../venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp=../pytest-full-final --junitxml=../full-suite-final.xml packages/ tests/ scripts/tests/ --deselect scripts/tests/test_audit_provenance_packets.py::test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded
& ../venv/Scripts/python.exe scripts/spec_gate.py --check
& ../venv/Scripts/python.exe -m ruff check .
& ../venv/Scripts/python.exe ../audit_probes.py
& ../powershell-dispatch.ps1
```

Use a **new** `--basetemp` directory on rerun: pytest may clear an existing one. The original packet and patches were preserved, no patches were applied to the live worktree, and no commit, push, merge, canonical promotion, governance dispatch, or live configuration write was performed. Orientation used the current L0 and operator primer, then the exact review endpoint; no reference-library corpus, event queue contents, or source-chain runtime state was needed.
