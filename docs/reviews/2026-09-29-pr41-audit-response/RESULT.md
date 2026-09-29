# RESULT: PR41 third review

**Packet:** [`PACKET.md`](PACKET.md), range `5a1a2b1` … `42e4d05`
**External review:** independent audit, 2026-09-29:
[`external-audit-2026-09-29/REVIEW.md`](external-audit-2026-09-29/REVIEW.md)
**Audit recommendation:** request changes, on one new finding (F4). F3 is
closed for its original reproduction.
**Author response:** `9a23477`, and `69c4cbd` from the internal review of it

## Operator decision

**PENDING.** This file records the author's dispositions. It is not the
operator's decision. One observation below (O2) needs a policy decision that is
the operator's to make, and it is marked as such.

## Dispositions

| Item | Audit | Author disposition |
|---|---|---|
| **F4:** a marker whose absolute `workspace_root` contains a NUL raises `ValueError` from `resolve()` on POSIX, aborting the pruner and the materializer, `--check` included | P2, reproduced on Ubuntu / Python 3.12 through the real CLI | **Accepted, fixed** in `9a23477`. Resolution moved into `recorded_workspace()`, which catches `ValueError` as well as `OSError` and returns "no usable identity". Equality is unchanged, still exact and not ancestry. The regression runs through `materialize()`. The bad marker sorts first, the workspace's own withdrawn projection after it must still be pruned, and the bad one must be kept and reported. It mirrors POSIX `realpath` on every platform by patching `os.path.realpath`. **Also checked natively:** the same fixture under WSL Ubuntu / Python 3.12.3 raises `ValueError: embedded null byte` in `posixpath.realpath` before the fix, and after it reports `KEEP` for the bad marker and `DRIFT` for the withdrawn one. See [`posix-f4-check/`](posix-f4-check/). |
| **O1:** the marker migration puts every unchanged skill through the pre-existing delete-before-copy window | observation, reproduced with an injected copy failure | **Fixed for the migration** in `9a23477`. When the installed files equal the source and only the marker differs, only the marker is rewritten, and the skill is never taken down. That is the case the migration creates. **Not fixed:** delete-before-copy for real content changes. It predates this PR, the source survives, and the next run restores the projection. A staged copy inside a shared skill root could be discovered as a skill by a harness mid-install, so the fix needs more thought than a swap. Recorded as a known rollout risk. |
| **O2:** install replaces a listed skill whose installed marker names another workspace | observation, reproduced up to the destructive call | **Needs an operator decision.** It predates this range: the ownership guard covers pruning, not install. `9a23477` narrows the destructive half when payloads are identical, since only the marker is rewritten, but the new marker then names this workspace. So ownership still transfers silently. The pruning tests cover distinct skill names only, and are not presented as coverage of same-name coexistence. The options are set out under [O2](#o2-same-name-collisions-the-operators-call). |
| **O3:** `os.replace` in `packages/activity_log/provenance.py` raised `PermissionError: [WinError 5]` in two tests | observation, unchanged code | **Not reproduced here.** Both tests passed 6 of 6 runs each, 12 runs in total. Root cause is not established, and these are not called sandbox failures. The code is untouched by this PR. Filed as a separate task: confirm the cause, and if it is a transient Windows lock, add a bounded retry in one shared helper. |
| **O4:** a present-but-invalid identity and a moved workspace stay silently unowned; only a missing identity produced `KEEP` | observation | **Fixed** in `9a23477`. An unusable identity (missing, relative, empty, not a string, unresolvable) and one naming a workspace root that cannot be found both produce `KEEP` lines. That second line was reworded in `69c4cbd`; see the internal review below. They are never removed and not drift. A live other workspace's projection stays silent. `KEEP` lines say "left in place", so a grep for "removed" finds only removals. |
| UNC and 8.3 aliases, case-insensitive POSIX volumes, harness invocation, Hermes process identity, header support, authenticated delivery, daemon readiness | unverified | **Remain unverified.** The auditor confirmed that a real Windows junction resolves to one owner for writing and reading. |

## O2: same-name collisions, the operator's call

Two workspaces that both list a skill named `x` share one directory,
`<root>/x`, in a shared user-scope root, and one directory can hold only one
payload. Today the last workspace to refresh wins, silently. The possible
policies:

1. **Keep last-writer-wins, and say so.** Document it and report the takeover
   as its own line when the old marker named a different workspace that still
   exists. This is the least disruptive, and it makes the transfer visible.
2. **Refuse and report.** A listed skill whose installed marker names a
   different, existing workspace is not replaced. It is reported as a conflict
   and counted as drift until a human resolves it. A legacy marker, or one
   naming a workspace that no longer exists, can still be taken over, because
   otherwise the marker migration and moved workspaces could never converge.
   This is the safest, but two workspaces that both want `x` will show drift
   indefinitely.
3. **Namespace per workspace.** Install as `x` only when unclaimed, and
   otherwise as a workspace-qualified name. This avoids both problems, but
   harnesses then see two copies of the skill under different names.

**Author's recommendation: option 1 now, option 2 if more than one workspace on
a machine is expected to install user-scope skills.** Today every checkout on
this machine either fails to resolve the skill paths from its default root
(those under `FLOSS/.worktrees/`, `C:/pr38t1`, the agent-orchestrator
worktrees) or resolves to the same workspace root, `C:/~shit` (the
`C:/~shit/_*` worktrees). So in practice there is one identity, and a
collision needs an explicit `--workspace-root` pointing somewhere else.
Nothing is implemented until the operator chooses.

## Internal review of the response

One subagent reviewed `9a23477` with the three-bucket prompt. A parallel
review through OmniRoute did not run, because the session had expired. Prompt
and return are verbatim in [`internal-reviews.md`](internal-reviews.md).

| Item | Reviewer | Disposition |
|---|---|---|
| The "no longer exists" `KEEP` line: `os.path.exists` is also False for an unmounted drive or an unreachable network path | observation | **Accepted, fixed** in `69c4cbd`, and treated as more than readability. The line invited deleting the projection by hand, so an unmounted drive could lead an operator to delete a live workspace's skill. It now says the workspace "cannot be found from here (moved, deleted, or not mounted)", and to remove the projection only once that workspace is known to be gone. The test requires the new wording and rejects the old invitation. |
| The test's `os.path.realpath` patch may not reach `Path.resolve()` on 3.12 | observation | **Checked; it does.** On 3.12, `resolve()` calls `self._flavour.realpath`, and `_flavour` is the `os.path` module, looked up at call time. On 3.13 it calls `os.path.realpath` directly. The red run raised `ValueError` through the patch, and the native WSL check raised it from `posixpath.realpath` itself. |
| The marker-only rewrite transfers ownership of a foreign projection with identical content | observation | Part of **O2**, the operator's call above. It is no worse than before: delete-then-copy transferred ownership too. |
| Line-ending-only differences compare equal, because files are read in universal-newline mode | observation | Pre-existing semantics of the snapshot comparison. The marker-only path keeps the installed line endings where the old path would have copied the source's. Harmless for skill text. No action. |
| "The marker is atomically flushed before function return" | checked-clean line | **Not accurate:** a plain `write_text` is not atomic. The code does not rely on it. A torn marker reads as unowned, and the next run rewrites it; the comment in the code says so. |

The review reported no defects. Its most useful item came from the
observations bucket and was rated a readability concern. As in the first
round, it took a second look to see the consequence.

## Test discrimination

The audit ran the packet's new and rewritten tests against the pre-response
production code: 24 failed and 1 passed. The one pass is the own-withdrawal
guard, which is labelled as a guard. The join test's first failure is on the
changed signature, as the packet said. The remaining 23 exercise the changed
behaviour.

`9a23477`'s 8 new cases were each written first and run against the unfixed
code. `ValueError: embedded null byte` twice (F4). No `KEEP` line five times:
four unusable identities and one workspace that no longer exists. The install
took the skill down for a marker-only change once. The existing
foreign-workspace test changed in two ways. It now creates the other workspace,
since a missing one is now reported. It also asserts silence outright, where it
previously asserted only that nothing was removed.

## Validation

After `69c4cbd`, on the author's machine: **1107 passed, 7 skipped,
1 deselected**. Lint over code paths is unchanged at 8, spec_gate is OK, and
`git diff --check` over `scripts/` is clean. The audit's own run of the
endpoint before this fix was 1096 passed with 3 failures: the two O3
replacement errors and the Git-index test, which needs a Git index the archive
lacks. That is not one all-green run in a second environment.

## Evidence

`external-audit-2026-09-29/` carries the audit's 41 top-level files,
credential-scanned and content-identical to `_audit/pr41-round3-20260929/`.
Two differ byte-wise once committed: `baseline.xml` and `full-suite.xml`,
normalized from CRLF to LF. That count was checked by comparing each staged
blob against `_audit/`.
The large reproduction artefacts stay behind: the exported snapshot, the
baseline code, the fixtures and the pytest directories. One link in its
`REVIEW.md` points to the previous audit's folder by its `_audit/` name. The
same file is in the repository at
[`../2026-09-05-pr41-fix-sweep/external-audit-2026-09-27/REVIEW.md`](../2026-09-05-pr41-fix-sweep/external-audit-2026-09-27/REVIEW.md).

`posix-f4-check/` holds the author's native POSIX check: the probe and its
output.
