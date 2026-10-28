# Internal reviews: the PR41 review-thread fixes

One review so far. The prompt and the return are verbatim, with one change: the
notification that delivered the return had HTML-escaped `<` and `>`, and those
are restored. A parallel OmniRoute review did not run, because that server was
not connected in this session.

## 1. Review of `332bc6e..6809053`

**Reviewer:** `cavecrew-reviewer` subagent, with the repository. Bash was limited
to `git diff`, `git log` and `git show`, so nothing was executed and its
red/green calls are static traces.
**Range:** `332bc6e..6809053`: the spec, the registry backfill, the tests and the
code for six findings from the PR review threads.
**Prompt:** the three-bucket form (defects, observations, checked and clean),
with "a prior is a direction, not a filter".

### Prompt

```text
Review a commit range in the git worktree at C:/~shit/FLOSS/.worktrees/pr41-salvage (branch reconcile/pr38-salvage-20260817). Range: 332bc6e..6809053 (4 commits: spec 332bc6e, registry backfill 1c25856, tests c02c735, code 6809053). Use `git diff 332bc6e..6809053 -- <path>` and read the files; run commands from that directory. Python is `C:/Python313/python.exe` with PYTHONPATH cleared (env -u PYTHONPATH).

What the range does (each clause is in docs/specs/local-surface-invariants.spec.md, docs/specs/reasoning-ensemble-synthesizer.spec.md section 2.10, docs/governance/manual-review-protocol-v1.0.md MRP-K1):
1. packages/reasoning_ensemble/synthesizer.py: degenerate_voters() now applies DEGENERATE_TRUNCATION_RATIO (0.4 x panel median) before calling an unterminated response truncated.
2. scripts/review_independence.py: kish_neff() refuses only a negative mean phi (was <= 0), so a mean of exactly 0 gives n_eff = k.
3. scripts/materialize_shared_hook_surface.py: resolve_target_hooks() raises HookSurfaceError when two declared source events map to one native event name.
4. scripts/materialize_shared_agent_surface.py: new assert_repo_scope_stays_inside(), called for the antigravity, codex/codex_user and hermes targets, so a scope "repo" target must resolve inside the workspace.
5. scripts/materialize_shared_skill_surface.py: new remove_if_unchanged(directory, baseline): renames the installed skill directory to a hidden sibling (REMOVING_PREFIX + token + name), digests the renamed copy, deletes it if it equals the baseline, otherwise renames it back and returns a reason. Used by prune_stale_projections (write branch) and by the UPDATE path in install_skill_projection. A rename that fails (open file on Windows) keeps the copy. A superseded doctored-digest test was removed.
6. packages/mcp_daemon.py: _reclaim_claim_cli() now holds _claim_guard(pid_path) across both snapshots and both removals via a new _reclaim_claim_guarded(); TimeoutError/OSError/ImportError print NOT_RECLAIMED and return 1.

Report in THREE buckets, and fill all three:
1. DEFECTS: anything wrong, whether this range introduced it or it was already there in the code you read. Do not filter to what the range introduced; a prior is a direction, not a filter.
2. OBSERVATIONS: things below that bar: risks, untested cases, anything misleading even if safe. When you judge something safe, say why, so the judgement can be checked.
3. CHECKED AND CLEAN: each area you examined and found nothing in, with the evidence.
A bare "no issues" is not a result.

Where to look first:
- remove_if_unchanged: the hidden aside name sits inside a shared skill root that harnesses scan. Could a failure leave a stranded copy that something treats as a skill, or that the pruner then mishandles? What if os.rename succeeds but payload_digests raises, or the restore rename fails? Does the pruner's own `child.name in expected` / marker / ownership logic handle an aside copy correctly (projection_owned_by, baseline check)? What about a skill whose NAME is long, or a name collision with the aside prefix? Does drift_found/KEEP reporting stay consistent in --check, --dry-run and write modes (check and dry-run must not rename anything)?
- The UPDATE path: after remove_if_unchanged returns None the code copies the new payload. If that copy fails, is anything lost that was not provably the shared base?
- assert_repo_scope_stays_inside: does resolve() on a Windows junction/symlink inside the workspace make a legitimately in-repo path look outside it? Is `scope` read the same way target_in_scope reads it?
- _reclaim_claim_cli: is there any caller or script (scripts/start_mcp_daemons.ps1, stop_mcp_daemons.ps1) that relied on the old unguarded behaviour, or could the guard deadlock when those scripts already hold it?
- The tests: do the new tests in c02c735 actually fail without the fix and for the stated reason? Is any test source-text-only? Do the source-structure tests in packages/tests/test_mcp_daemon.py still assert something real?
- Anything in the spec text that the code does not do, or that the tests do not enforce.
```

### Return

```text
Scope: Bash is limited to `git diff`/`log`/`show` under this agent's rules, so nothing was executed. Red/green calls are static traces of 332bc6e vs 6809053. Confirm with `env -u PYTHONPATH C:/Python313/python.exe -m pytest <file> -k <name>` against a 332bc6e checkout.

## DEFECTS

`C:/~shit/FLOSS/.worktrees/pr41-salvage/packages/reasoning_ensemble/synthesizer.py:644`: 🟡 risk (pre-existing): `if not text` only catches `""`. Whitespace-only `"   "` passes, reaches `scored` (L852), and is flagged at L872-876 as "ends mid-sentence at 0 chars … truncated". SYN-D4 says empty responses are not flagged here. Fix: `if r.response.strip() and not r.error` at L852.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/packages/tests/test_mcp_daemon.py:1241`: 🟡 test gap (range): LSI-B1 says both removals run under the guard. Test creates no claim or sidecar, so `_reclaim_claim_if_unchanged` never runs. Moving the removal outside the `with` at `mcp_daemon.py:1123` still passes. OSError/ImportError branches (`mcp_daemon.py:1125-1132`) are untested; only TimeoutError (L1292). Fix: seed claim+sidecar, assert guard held when the removal runs.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/tests/test_shared_agent_surface_mcp.py:779`: 🟡 test gap (range): LSI-A1 names relative, `~`, and `%VAR%` forms. All four new tests use absolute paths only.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_agent_surface.py:1800`: 🟡 bug (range): LSI-A1 says "raised before anything is written". Mirrors (L1800), context pack (L1812), gemini (L1843), opencode (L1854), vibe (L1884-1935) all write before the codex (L1950) and hermes (L2004) containment checks. A repo-scope hermes escape therefore fails after codex config was already rewritten. Fix: resolve and assert every target in a pre-pass.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_agent_surface.py:1843`: 🟡 risk (pre-existing): security. Writes to a machine-wide path from an in-repo manifest with no opt-in. Gemini settings, opencode settings/instruction, vibe config/agents_dir/launcher, mcp_mirrors, and context_pack_path all do `workspace_root / <manifest path>`. None are scope-gated or containment-checked. An absolute manifest path replaces the base and writes wherever it points. LSI-A1 says "every materializer that writes a path named in a manifest". Fix: route through `resolve_manifest_path` + `assert_repo_scope_stays_inside`; treat absent scope as repo for these.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_hook_surface.py:430`: 🟡 bug (range): LSI-A2 says an event with no hooks takes no part. `definitions == []` still reaches the collision check at L434. `{"PreToolUse": [], "PostToolUse": [...]}` both mapped to one name now raises `HookSurfaceError`. Pre-fix, empty-first was harmless. Fix: `if not definitions: continue` before L434. No test covers the empty-list case.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_hook_surface.py:841`: 🟡 risk (pre-existing): `assert_repo_scope_stays_inside` returns on OSError, so the containment check is skipped. Skill and agent versions raise. Low likelihood, but it fails open. Fix: raise.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_hook_surface.py:1039`: 🟡 bug (pre-existing): registry and index are written (L1039-1051), and earlier targets are written, before the containment assert at L1070. Refusal leaves partial writes. Same fix as agent L1800.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:305`: 🟡 risk (pre-existing): security. Frontmatter `name` is unvalidated and used as a path component (`target_root / name`, L853). `../x`, `a/b`, or an absolute name makes INSTALL write outside the target root, with a marker. Source is in-repo, but `upstream_candidates` imports are in scope. Fix: reject names not matching `^[A-Za-z0-9][A-Za-z0-9._-]*$` in `resolve_skill_entry`.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:583`: 🟡 risk (range): a stranded aside of an in-manifest skill is misreported and displaced. A crash, Ctrl-C, or non-OSError between the rename (L587) and restore/removal (L597/L600) leaves the live name absent and the copy at the hidden aside. Next run: prune prints KEEP "withdrawn from the manifest" (L783-786), then install prints INSTALL at the live name (L870) in the same run. Only learned copies (aside ≠ baseline) misreport, so the window is narrow. Spec LSI-A4(d) "ordinary withdrawn projection" is the source of the wrong label. Pre-fix, the same interruption left the live copy intact. Fix: prune maps `REMOVING_PREFIX` children back to their base name; if the base is in `expected` and the live name is absent, rename back before install.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:593`: 🟡 risk (range): `payload_digests(aside)` OSError (unreadable file, or path too long after the 39-char aside prefix) is reported as "it changed while being checked" (L608). Blocked rename at L591 is labelled `EVOLVED` in the UPDATE path (L976-978). Wrong label sends the operator to reconcile a change that never happened. Fix: distinct reason per failure.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:597`: 🟡 risk (range): `remove_path(aside)` is unwrapped. On Windows a scanner handle taken after the rename raises PermissionError, which escapes and aborts the whole run (`main()` has no handler). The partially deleted aside keeps its marker and is reported "changed where installed" (L783-786) on every later run. Never cleaned; needs hand deletion. A non-OSError from L593 skips the restore the same way. Fix: try/except around L597; restore on any exception.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:597`: 🟡 risk (range): the docstring says "the window is a rename and a read". Wrong. On Linux/macOS an fd held across the rename still writes into the aside. A learning written between the digest (L593) and removal (L597) is deleted with it. Windows blocks rename on open handles, so this is POSIX only.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:764`: 🟡 risk (pre-existing): comment says a marker that changed since the ownership check is treated as no baseline. Code re-reads the marker and checks only that it parses. `workspace_root` is not rechecked (ownership checked once, L720). Fix: re-run `projection_owned_by` on the re-read marker, or drop the claim.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:788`: 🟡 risk (range): `--check` and `--dry-run` report DRIFT (L789, L795; install L950) for removals and updates the write run cannot clear while the rename is blocked (open handle, AV). Write run prints KEEP with drift False. Every `--check` then exits 1 until the handle is released. Check never probes renameability. Fix: write run exits non-zero on a blocked removal, or check reports blocked paths as KEEP.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:971`: 🔴 bug (range, data loss): the new comment "safe to remove, since the shared base's history holds it" is false when source edits are uncommitted. Baseline is the source at last install. Sequence: edit S1 → refresh (copy = S1, uncommitted) → edit S2 → refresh. Copy equals baseline, source moved, UPDATE removes the copy. S1 exists nowhere else. Normal edit/refresh loop loses an uncommitted revision. Fix: drop the justification. Keep the old payload aside as a backup, or refuse removal when source is uncommitted.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:995`: 🟡 risk (pre-existing): failed-copy and failed-marker cleanup `remove_path(target_dir)` (L995, L1005) deletes everything under the dir. Comment at L991 says "everything under target_dir was created by this copy". False if a harness writes into the fresh copy before the L1005 publish fails. Fix: remove only paths listed in `source`.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/tests/test_shared_skill_surface_scope.py:1465`: 🟡 test defect (range): `test_a_learning_written_after_the_update_comparison_is_not_deleted` passes pre-fix. Old UPDATE branch re-reads `target_dir` after the first digest, so a write after the first digest is caught by that second read. It never hits the window the fix closes. Commit c02c735 claims all new tests are red pre-fix. Fix: fire the write between the old second read and removal, or drop the claim.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/tests/test_shared_skill_surface_scope.py:1516`: 🟡 test defect (range): `test_a_copy_stranded_aside_is_pruned_like_any_withdrawn_projection` fails pre-fix only at `module.REMOVING_PREFIX` (AttributeError). The behaviour it asserts (remove unchanged withdrawn copy, keep changed) already existed. Not red for the stated reason.

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:600`: 🟡 test gap (range): untested: restore-rename failure (L600, "kept as …"); UPDATE + blocked rename (L974; LSI-A4(c) covers prune only); check/dry-run never renaming (L788-796, L944-952); stranded aside whose base is in `expected` (L715).

`C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/review_independence.py:152`: 🟡 bug (range, spec MRP-K1): `mean_phi < 0` on a float sum. A mathematically zero mean with non-dyadic phi can sum negative. IEEE: `0.3 + -0.1 + -0.2 = -2.78e-17`, so refused. Report then prints "Mean pairwise phi is -0.000 … Almost certainly the MATCHER". The test (`scripts/tests/test_review_independence.py:152`) uses dyadic 0.0 only and misses it. Fix: `mean_phi < -1e-12`.

❓ `C:/~shit/FLOSS/.worktrees/pr41-salvage/scripts/materialize_shared_skill_surface.py:567`: which harness scanners actually skip dot-prefixed skill dirs? Docstring says "that have been read" with no citation. If any scanner loads a stranded `.flossi0ullk-removing-*` copy, a duplicate skill name appears during the crash window. Need evidence.

## OBSERVATIONS

- `materialize_shared_skill_surface.py:34` (also agent `:65`, hook `:25`): in this worktree `REPO_ROOT.parent` is `C:/~shit/FLOSS/.worktrees`. Containment boundary and default output (`.agent-surface/skills`) sit one level above the worktree. Sibling worktrees pass containment. Pre-existing layout.
- `materialize_shared_skill_surface.py:593-597`: aside adds 39 chars to every descendant path. Current skill names max 45 chars, longest live path ~190 < 260 MAX_PATH. Safe for the current manifest; deep payloads near 221 chars now fail digest (see L593 misreport).
- `materialize_shared_skill_surface.py:481`: `payload_digests` reads whole files with `read_bytes` (pre-existing memory cost on large assets).
- `materialize_shared_skill_surface.py:600`: on POSIX the restore rename can replace an empty directory created in the window. Harmless: non-empty fails with ENOTEMPTY.
- Concurrency: materializers take no lock. Two worktrees sharing `~/.codex/skills` with `--include-user-scope` can interleave. The aside protocol assumes the name is not re-taken; a failed restore then strands the copy. `filelock.guarded` exists and is unused here.
- `synthesizer.py:856`: even-count median is the upper-middle element. Example `[50,60,300,400]`: threshold 120 vs 72 with mean-of-middles, so a 110-char unterminated whole answer is flagged. Spec says "median". Median uses raw length (L852-856), flag uses stripped (L872). Pre-existing.
- `synthesizer.py` SYN-D1 check `"</" not in lowered`: any closing-looking tag suppresses the flag. Matches spec's literal "no closing tag". Pre-existing.
- `mcp_daemon.py:1123`: default 5 s guard wait blocks start/stop scripts. NOT_RECLAIMED then reads as "claimed by another process first" (`start_mcp_daemons.ps1` ~L262, `stop_mcp_daemons.ps1` ~L160). A print failure after a successful reclaim prints NOT_RECLAIMED though the claim is gone (conservative direction).
- `mcp_daemon.py:1135`: `_reclaim_claim_guarded` runs unguarded if called directly; nothing enforces it. Only caller is L1123.
- `materialize_shared_agent_surface.py:1761` and hook `:817`: refusal aborts the whole step, not one target. Fail-closed is correct; blast radius is wide.
- `materialize_shared_agent_surface.py:1509`: generated vibe launcher writes `~/.vibe/trusted_folders.toml` on every launch. Generated output, not a materializer write, outside LSI-A1 as written.

## CHECKED AND CLEAN

- Check and dry-run never rename: prune returns at L788-796 and install at L944-952, before `remove_if_unchanged` (L800) and the UPDATE block (L974).
- Pruner classifies an aside correctly: `child.name in expected` (L715) can't match `.flossi0ullk-removing-…`. Marker survives rename, so `projection_owned_by` (L623-651) and baseline (L768) work on it. Links skipped at L715; install returns LINKED at L865 before any rename.
- Rename refused → copy kept, no removal: `test_an_installed_copy_that_cannot_be_taken_aside_is_kept` (L1486) red pre-fix (old code removes it).
- Write after digest, prune path: L1435 red pre-fix (old removes on first digest).
- Restore rename cannot clobber a non-empty directory (ENOTEMPTY on POSIX, fails on existing name on Windows).
- UPDATE `assert baseline is not None` (L973) holds: action UPDATE set only after the `baseline is None` return (L918-926).
- UPDATE copy-failure: removed copy was verified equal to baseline (L593) before deletion. Loss only via the L995/L1005 window above.
- Agent `assert_repo_scope_stays_inside` (L1761): `scope` read matches `target_in_scope` (`str(...).strip().lower()`). Missing scope raises in `target_in_scope` first, so the `""` default is unreachable on any call path. Junction/symlink: `resolve()` follows links, so a repo path traversing a link to outside is refused. Intended, since the write would land outside. Workspace root resolved on both sides, so a junctioned checkout root does not false-positive. `relative_to` is case-insensitive on Windows. Tests at L779/810/830 red pre-fix (traced); L854 is a positive control.
- Skill assert (L199-219): default "repo" matches `skill_target_in_scope` (L190). `build_target_roots` (L222-269) runs before any write, so the skill module refuses atomically. Real manifest repo targets are relative (`shared-skill-surface.json` L45-57).
- Hook assert (L817-848): real manifest repo targets are relative (`shared-hook-surface.json` L71, 233, 276, 404).
- Hook collision only sees events present in `target_hooks`. Undeclared-event test (L578) is correct. Both `resolve_target_hooks` call sites (L586, L803) covered. Test L553 red pre-fix (overwrite, no raise).
- Daemon guard deadlock: `guarded` is re-entrant (`filelock.py` L271-331, RLock + depth), so `_reclaim_claim_if_unchanged` → `reclaim_if_unchanged` (L334) nests cleanly. Scripts call the CLI as a fresh process and hold no OS lock across it. Locks release on exit. Python fds are non-inheritable, so the daemon child does not inherit the guard. No deadlock.
- Daemon script contract: scripts use `2>$null` and parse the last stdout line. Still RECLAIMED/NOT_RECLAIMED. Old traceback path also produced no RECLAIMED. No script-visible change.
- Daemon exception order: TimeoutError (an OSError subclass) caught first. ImportError from the `guarded` import inside the generator is raised at `__enter__` within the `with`, caught at L1130.
- Daemon tests: L1241 red pre-fix (guard entered 0 times). L1292 red pre-fix (old removes the stale record, code 0). Test at L1220-1240 runs the real guard in a child process, exercising msvcrt/fcntl end to end. Positive.
- Source-structure: L864 retargeted to `_reclaim_claim_guarded`; sidecar-before-claim ordering assert is real. L1158 is weak: only literal `unlink(missing_ok=True)` is checked, so `unlink()` or `os.remove` pass. Observation only.
- Synthesizer: `DEGENERATE_TRUNCATION_RATIO = 0.4` (L841) matches the spec table. `<` matches "below". No division by zero (`r.response` truthy → median ≥ 1). SYN-D1/D3 unchanged. L255 red pre-fix (358 < 399, unterminated). L272 is a control, green pre-fix by design.
- Independence: `report` returns 2 on refusal (L466); test L152 asserts 0, so it discriminates. `build_matrix` returns `(keys, vectors)`, so `[1]` is right. Test vectors `[1,1,0,0]`, `[1,0,1,0]`, `[1,0,0,1]` have covariance exactly 0, mean 0.0, n_eff 3. Red pre-fix.
- Registry backfill (`1c25856`): no code reads `grandfathered` (`git grep`). `spec_gate.py` L494-500 treats absent tier as an exemption. Clean.
- Not re-read: the pre-existing LSI-A3 tests (EVOLVED/CONFLICT/DIVERGED/foreign/unmanaged). Only L1163 and L1188 were checked.

totals: 1🔴 19🟡 1❓
```
