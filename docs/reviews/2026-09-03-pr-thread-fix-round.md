# PR Review-Thread Fix Round — 2026-09-03

Operator directive: audit every live review thread on all active PRs, plan fixes
test-first, iterate the plan with other agents until sound, implement with green
tests, re-review commits cross-agent, push once per branch, then reply+resolve.
No back-and-forth of failing fixes on the GitHub threads themselves.

## 1. Source state [V]

Thread query via GraphQL `reviewThreads(first:100)` on 2026-09-03 (~04:00 UTC),
raw JSON at `$LOCALAPPDATA/Temp/threads-{41,43,59,61}.json`, live-thread bodies
at `live-bodies-{43,59,61}.md` (43 compacted to `live-bodies-43-compact.md` by
stripping `<details>` analysis chains).

| PR | total | resolved | unresolved | of which outdated | **live** |
|----|-------|----------|------------|-------------------|----------|
| 43 `feat/preservation-spine-standalone` | 44 | 8 | 36 | 4 | **32** |
| 59 `fix/pr43-unclassified-durability` | 3 | 0 | 3 | 1 | **2** |
| 61 `codex/sweettest-substrate-bridge` | 1 | 0 | 1 | 0 | **1** |
| 41 `reconcile/pr38-salvage-20260817` | 272 | 64 | 36 | 35 | **1** (operator-triaged, no action) |
| dependabot 63/58/57/56/54/48/45 | 0 threads each | — | — | — | **0** |

Heads audited against: PR43 `4daefa0`, PR59 `7edd1c8`, PR61 `c925ed1`
(all pushed 2026-09-01; bodies in `_pr43_fresh`, `_pr59_fresh`,
`_codex_sweettest_substrate_bridge` worktrees).

## 2. Already fixed by pushed commits — reply + resolve, no code

| # | Thread | Evidence |
|---|--------|----------|
| F1 | PR43 `bACIb` P1 full-index @git_capture.py:326 | Both diff invocations carry `--full-index` (lines 325, 334 on `4daefa0`) [V, grep; auditor sa-0 CONFIRMED] |
| F2 | PR43 `bjThG` P1 ext-diff @git_capture.py:326 | Both invocations carry `--no-ext-diff` (lines 323, 332; commit `89187d0`) [V, grep; auditor sa-0 CONFIRMED] |
| F3 | PR43 `bjThH` P1 opaque-planes @restore.py:471 | 43-B (`b5722c4`) split authenticated/releasable; no `_verification_inventory_eligible` remnants in cli.py; inventory gate cli.py:332 + render gate cli.py:397 on `_verification_authenticated` [V, grep; auditor sa-0 CONFIRMED] |

Rule: re-run the named test slice green on the fix worktree, then reply with
SHA + mechanism, then resolve. Reply BEFORE resolve.

## 3. PR43 fixes (TDD: failing test first per item)

### Batch A — capture determinism (git_capture.py)
| # | Thread | Fix | Failing test first |
|---|--------|-----|--------------------|
| A1 | `d-mPm` P1 textconv | Add `--no-textconv` to staged + unstaged invocations | Configure `diff.<driver>.textconv` returning constant text; assert `staged.diff` still records the real change |
| A2 | `d-mPr` P1 noprefix | Add `--src-prefix=a/ --dst-prefix=b/` to both invocations | Set `diff.noprefix=true` + staged edit; assert inventory does not raise `diff header is malformed` |
| A3 | `bb2dB` P1 split-index | Fail closed (`CaptureDrift`) when index has `link` extension without backing `sharedindex` file present | Synthetic split-index repo; assert capture raises instead of silently partial index |
| A4 | `bcDRf` P1 ambient GIT_* | Strip `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY` (and `GIT_WORK_TREE`) from capture subprocess env | Set `GIT_DIR` to another repo; assert capsule history matches `--repo`, not the intruder |
| A5 | `d-oiD` Major separators | Normalize `-`/`_` in marker AND stem before comparison (`api-key.txt`, `id-rsa` must redact) [V valid: `_marker_in_stem` is bare `marker in stem`, `api_key` never matches `api-key`; auditor sa-0 CONFIRMED via live run, incl. `ID-RSA` bypass. Bonus: `_split_segments` (git_capture.py:38) is dead code — delete in the same commit] | Parametric cases `api-key.txt`, `id-rsa`, `my-private-key.pem` → True; keep `docs/seed.md`-class dir-prefix cases False. Also update the now-stale `is_secret` docstring (still describes separator-bounded behavior) |
| A6 | `bdJsD` P1 non-UTF-8 paths | Reversible JSON-safe byte encoding for undecodable path bytes (no surrogates into `canonical_json_bytes`) | Repo with `\xff\xfe` filename; assert capture completes and inventory round-trips the name |
| A7 | `bjThI` P1 non-NFC | Fail closed BEFORE state-dir creation when a valid non-NFC path is present (or encode per A6 if the same mechanism covers it — decide in implementation; prefer one mechanism) | Decomposed `e\u0301.txt` repo; assert clean error, no sealed-but-checkpointless state dir |

### Batch B — verification binding (cli.py, github_projection.py, restore.py)
| # | Thread | Fix | Failing test first |
|---|--------|-----|--------------------|
| B1 | `bcDRa` P1 idempotent verify | Re-run `verify_checksums` + provenance-root comparison before taking the idempotent shortcut | Mutate sealed payload after verify; re-run `verify`; assert nonzero exit / drift, not stale `verification-complete` |
| B2 | `d-mPt` P1 + `d-oh_` minor unbound fields | Require raw `verification.json` bytes to equal canonical JSON of the bound schema before accept/copy | Add unknown field to `verification.json` post-verify; assert inventory rejects and render does not copy it |
| B3 | `bAGPt` Major sanitize_command | Match `_UNSAFE_COMMAND_RE` against `normalized` as well as `value` | Parametric `%70ush` + every verb in `_UNSAFE_COMMAND_RE` |
| B4 | `bdJsF` P2 + `bjTat` Major exclusions dir | Read `capsule_root / PlaneId.LOCAL_TRACKED.value / metadata.json` (one thread, one fix, reply to both) [auditor sa-0 CONFIRMED: `local-tracked-worktree` appears exactly once in the package — the stale read at cli.py:617; all writers use `PlaneId.LOCAL_TRACKED.value`] | Tracked-secret capsule; assert `exclusions` lists it |
| B5 | `bAGPd` minor restore-verified dedupe | Strip-then-append in `_handle_restore_verified` like inventory/render handlers | Re-verify; assert single `restore-verified` + no stale `manifest-inventoried` |

### Batch C — error-contract hardening
| # | Thread | Fix | Failing test first |
|---|--------|-----|--------------------|
| C1 | `bAGPi` minor resolve race | Wrap `path.resolve(strict=True)`; map `OSError` → `CaptureDrift` | Fault-inject disappearing parent; assert `CaptureDrift`, not bare `OSError` |
| C2 | `bAGPy` minor octal range | Reject `\400`+ escapes with `CapsuleVerificationError` before `bytearray.append` | Tampered capsule with `\400`; assert CVE, not `ValueError` |
| C3 | `bAGP6` minor bundle head | Map `UnicodeDecodeError` on head lines → `CapsuleVerificationError` | Non-ASCII ref bundle; assert CVE |
| C4 | `bAGQF` minor Windows open | Wrap lines 129–132 re-raise in `CapsuleVerificationError` | Simulate `OSError` on Windows path (monkeypatch); assert CVE type |
| C5 | `bAGQB` trivial message | Plane-neutral duplicate-path message (keep `duplicate paths` substring for test:1017) | Existing test stays green |

### Batch D — checkpoint durability (checkpoint.py + tests)
| # | Thread | Fix | Failing test first |
|---|--------|-----|--------------------|
| D1 | `bAGPB` minor input_shas | Immutable hashable representation that `asdict` supports (e.g. tuple-of-pairs normalized at construction + serializer updated), or document why dict is safe with regression test proving digest cannot be invalidated post-construction | Mutation-attempt + hashability + serialization round-trip tests |
| D2 | `bAGPE` minor dir fsync | Parent-dir fsync on POSIX after checkpoint/intent create/remove | Fault-inject dir-fsync; assert durability path taken (test at OS level with tmp_path; assert no crash on Windows skip) |
| D3 | `bAGPJ` minor fd leak | try/except around `os.fdopen` closing raw descriptor on failure | Force `fdopen` raise; assert fd closed (no `/proc/self/fd` leak / no LOCK_EX held) |
| D4 | `bAGQO` test blank-line | Build payload from valid genesis + empty line; assert specific message | Test fails before (hits contract error first), passes after |
| D5 | `bAGQU` test fsync | Fail ONLY the append fsync so rollback can complete; assert boundary restored | Test asserts restored boundary, not just message match |

### Batch E — trivial/lint (one commit)
`bAGPY` salvage wording (2 sites) · `bAGQZ` raw string · `bcC4V` sorted `__all__`
(verify RUF022 is actually enabled first — if not, still sort, harmless).

### Design items — consensus BEFORE implementation
| # | Thread | Decision needed |
|---|--------|-----------------|
| D-D1 | `bb2c_` P1 tracked bytes | **Store full worktree bytes** (capsule format change, size blast radius) vs **downgrade `byte-equality` claim** to hash-recorded + document EOL/smudge limit. Lean: downgrade + disclose; full-byte preservation is a format v2 decision for a follow-up PR, not a review fix. |
| D-D2 | `bb2c8` P1 stash | **Bundle `refs/stash` + reachable stash commits** into local-history plane vs **fail closed when stash present** vs **document as limit**. Lean: bundle (refspec add, bounded work); fail-closed breaks normal repos. |

## 4. PR59 fixes (checkpoint.py, on `_pr59_fresh` rebased over new PR43 tip)

| # | Thread | Fix | Failing test first |
|---|--------|-----|--------------------|
| S1 | `bjUQe` P1 racy unlink | 59-A does NOT retain identity [auditor sa-1, exact mechanism]: fd opened `:912`, fstat `:918`, size check `:924-928`, but **fd closed at `:932`, `os.unlink(path)` by name at `:934`** — no `st_nlink` check (contrast `seal.py:84`), no ino/dev capture. `_locked_directory` only guards directory identity, takes no exclusive lock — concurrent creator/writer inside the same dir is unblocked. Fix bar: hold fd through removal (flock + re-fstat) or ino/dev recheck + link-count before unlink; extend flock discipline to the write path if writers are non-cooperating. The same file does identity correctly at `_read_stream_bytes:559-569` / `_append_bytes:600-601` — follow that pattern. | Concurrent-writer simulation: writer appends genesis between fstat and unlink; assert no record loss (or drift reported, never silent loss) |
| S2 | `d-kra` P1 truncated log | CONFIRMED on append path [auditor sa-1]: `_discard_unpublished_genesis:882-899` unlinks silently → `append_checkpoint:164-189` falls to genesis branch `:181-189`, sequence-0 accepted. Load path `:202-208` same discard then bare `FileNotFoundError` (wrong type, should be `CheckpointIntegrityError`); `_parse_chain:368` "file is empty" now unreachable for no-intent case. **Refined lean (auditor): pure fail-closed breaks 59-A's legitimate crash window** (create-then-crash-before-intent, `:478-479`): fail closed in the discard path UNLESS the current call created the file itself — thread a just-created flag from the `O_CREAT|O_EXCL` site (or write intent alongside creation so "no intent" positively means "never legitimately empty"). Fix the load-path error type in the same commit. | Truncate committed log to 0; assert integrity error + `append_checkpoint` refuses genesis-0; separate test: create-crash-no-intent window still recovers |

Note: S2 is a follow-up critique OF 59-A itself — the fix introduced the hole.
No defensiveness; fix it in the same file before pushing.

## 5. PR61 fix (on `_codex_sweettest_substrate_bridge`)

| # | Thread | Fix | Failing test first |
|---|--------|-----|--------------------|
| R1 | `d-i9D` P2 DNA staleness | CONFIRMED [auditor sa-1]: guard (`lib.rs:17-50`) checks `.dna` existence + 4 WASMs existence/size; staleness comment at `:26-28` but no mtime/hash comparison anywhere. Two-stage [auditor]: **ship mtime gate now** (DNA mtime ≥ newest WASM mtime + repack message; near-zero code, right cost for P2 dev-time guard), **file WASM-bytes-vs-embedded-hash comparison as hardening follow-up** (`DnaFile` already loaded at `:52`; content-addressed, no clock dependence; same-second rebuilds can slip mtime). | Touch WASM newer than DNA; assert guard fails with repack message |

## 6. PR41 — no code action

35/36 unresolved threads are `isOutdated=True` (stale lines, auto-superseded by
pushes). The single live thread (`byD7p`, Hermes patch verification) was
triaged BY THE OPERATOR on 2026-08-31 (false-evidence half closed, substantive
half honestly deferred pending a V4A parser). **Decision for Anthony:**
bulk-resolve the 35 stale threads, or leave them as archaeology. Not doing it
unilaterally — resolving others' threads is a review action.

## 7. Execution order + gates (binding)

1. **Plan review (this file) by other agents FIRST** — consensus claim with
   evidence (this file + thread JSON + heads); design items D-D1/D-D2/S2/R1
   need explicit verdicts. Executor does not implement until design verdicts land.
2. **Implement per batch, TDD**: failing test → fix → green. One commit per
   batch (A, B, C, D, E, S, R + design items separately). Work in the existing
   `_pr43_fresh` / `_pr59_fresh` / `_codex_sweettest_substrate_bridge` worktrees.
3. **Full suite green per branch** before any push (`pytest packages/preservation_spine/tests/ -q`; PR59 same; PR61 `cargo check --tests --locked` + fmt; no full sweettest re-run unless R1 touches runtime paths — it doesn't, guard only).
4. **Commit re-review by other agents** (diff review, different family preferred)
   — fix findings, re-verify, repeat until clean.
5. **Single push per branch**, then reply+resolve loop per thread (§2 + fixed
   items), re-query threads, confirm zero live-unresolved.
6. PR59 needs rebase onto final PR43 tip + force-with-lease again if PR43 moves.

## 8. Progress log

- 2026-09-03: plan written (commit `836caa4`). Live-thread inventory complete
  (35 + PR41 note). Nothing implemented, nothing pushed.
- 2026-09-03 ~21:05 UTC: consensus claim `01a06916` (Module/CodeChange,
  evidence: commit + spec + 3 PR urls) → round outcome **DEFERRED**
  (tally_mean 0.2875). Voter detail: groq-gpt-oss-120b +0.6 and
  huggingface-deepseek-v4-flash +0.55 (both form-checklist approvals, no
  substantive design review); mistral-devstral-small + nvidia-nemotron-super-49b
  errored to 0.0 (OmniRoute 400: model IDs not in live catalog).
  **Finding: consensus voter roster is stale** — two roster IDs no longer exist
  upstream. Gateway maintenance item, not a plan verdict. No implementation
  gate claimed from this round.
- 2026-09-03: direct frontier review via OmniRoute **blocked**: gemini-3.1-pro
  → 402 billing; pioneer/grok-4.5 → 404 sunset; nvidia/glm-5.2 → 400 not in
  catalog; combo routing needs provider/model prefix shape (400). Memory model
  IDs are stale; `best_combo_for_task(review)` recommends `floss-coding` but
  invocation shape unresolved. **Do not retry blind** — resolve via
  omniroute skills (`omniroute-gateway-ops`) or gateway roster refresh first.
- 2026-09-03: two independent auditor subagents dispatched (read-only):
  (sa-0) verify F1/F2/F3 + A5 + B4 verdicts on `_pr43_fresh`;
  (sa-1) verify S1/S2/R1 + opine on design leans on `_pr59_fresh` + PR61 tree.
  Results pending; they gate implementation alongside §7.1.
- 2026-09-03: auditors returned — **all 8 verdicts CONFIRMED**. sa-1 refined
  S2 (pure fail-closed breaks 59-A's crash window → creator-knows exception,
  adopted) and R1 (mtime now + hash follow-up, adopted); sa-0 found
  `_split_segments` dead (folded into A5). Ollama down (ensemble unavailable).
  Fresh evidence: git_capture + cli + e2e = **96 passed** on `4daefa0`.
  F1/F2/F3 replied (discussion_r3928735615/809/004) and resolved. PR43 live
  count re-queried: **29 live-unresolved (was 32)**. Plan §2–§5 updated.
  D-D1/D-D2 still lack external verdicts (consensus weak, OmniRoute blocked) —
  operator-confirmable leans; flagged in handoff.
