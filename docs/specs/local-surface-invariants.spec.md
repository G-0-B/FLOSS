# Local Surface Invariants

```yaml
id: "local-surface-invariants"
status: "Specified 2026-10-14; clauses written before the tests and code that satisfy them"
truth_status: "⚠️ Specified. Each clause names the test that enforces it; a clause with no test is marked."
governs:
  - "FLOSS/scripts/materialize_shared_agent_surface.py"
  - "FLOSS/scripts/materialize_shared_hook_surface.py"
  - "FLOSS/scripts/materialize_shared_skill_surface.py"
  - "FLOSS/packages/mcp_daemon.py"
registry: "FLOSS/docs/specs/spec-registry.json"
```

## Why this exists

The spec registry holds a one-line stub for each materializer ("Skill manifest ->
per-client skill projections"). That is the minimum the spec gate asks for. It does
not say what a materializer must never do, so the invariants below were first
written down as review findings against code that already existed. Each clause is
numbered so a test can cite it, and each was found violated by review of PR #41.

Process, per the project's spec-driven rule: the clause is written, then the test
that the clause defines, then the code. A review finding that has no clause here
gets one before it gets a fix.

## Part A. Materializers

**LSI-A1. Repo-scope containment.** A target declared `scope: "repo"` must resolve
inside the workspace root, however its path is written: relative, absolute, `~`, or
through an environment variable. A repo-scoped target that resolves outside the
workspace is an error that names the target and the resolved path, raised before
anything is written. A `scope: "user"` target is unaffected and stays gated by
`--include-user-scope`. Applies to every materializer that writes a path named in a
manifest.

*Why:* `scope` is a declaration and the path is a fact. Trusting the first lets a
repo-scope run rewrite machine-wide configuration that nobody opted into.

**LSI-A2. Event-map injectivity.** Within one target, two source events that both
carry hooks must not map to the same native event name. Resolution fails and names
both source events and the native name. A source event with no hooks, and an event
absent from the map, take no part in the check.

*Why:* assigning the second over the first drops one set of hooks from the generated
file with nothing reporting it.

**LSI-A3. Preservation.** A managed skill projection whose payload differs from the
baseline recorded when it was installed is never overwritten, removed or adopted by
a materializer run. It is kept, surfaced as a `KEEP` line, and not counted as drift
by `--check`. (The operator's rule of 2026-09-29: skills a harness evolved are to be
propagated back to the shared base, not replaced by it.)

**LSI-A4. Verified removal.** The comparison with the baseline that licenses an
update or a removal is made on the copy *after* it has been taken out of its
discoverable position, and not before. Concretely:

- a. The projection is renamed to a sibling name nobody writes to, and the renamed
  copy is compared with the baseline.
- b. If it equals the baseline it is deleted. If it differs, it is renamed back, kept
  and surfaced, and the run reports no drift for it.
- c. If it cannot be renamed (an open file on Windows, for example) it is kept and
  surfaced. A copy that cannot be verified in isolation is not removed.
- d. A copy stranded aside by a crash is an ordinary withdrawn projection to the next
  run: removed if unchanged, reported if not.

*Why:* comparing and then removing leaves a window in which a harness can write a
learning that no longer matches the baseline, after the decision was already taken.

## Part B. MCP daemon claims

**LSI-B1. Reclaim holds the guard across the pair.** `--reclaim-claim` takes the
claim snapshot and the identity-sidecar snapshot, and performs both removals, while
holding the claim guard that `--release-claim` and `--record-identity` hold. If the
guard cannot be taken, the verdict is `NOT_RECLAIMED`, the exit status is 1, and
nothing is removed.

*Why:* two snapshots taken outside the guard can pair the old claim with a
replacement launcher's sidecar, and the removal that follows can delete a live
daemon's identity record.

## Conformance

| Clause | Test |
|---|---|
| LSI-A1 | `tests/test_shared_agent_surface_mcp.py::test_a_repo_scoped_target_may_not_resolve_outside_the_workspace`, `::test_a_repo_scoped_antigravity_target_may_not_resolve_outside_the_workspace`, `::test_a_repo_scoped_hermes_target_may_not_resolve_outside_the_workspace`, `::test_a_repo_scoped_target_inside_the_workspace_is_still_written`; hook and skill: `scripts/tests/test_shared_hook_surface.py`, `scripts/tests/test_shared_skill_surface_scope.py` |
| LSI-A2 | `scripts/tests/test_shared_hook_surface.py::test_two_events_mapped_to_one_native_name_are_refused_not_overwritten`, `::test_a_collision_among_events_the_target_does_not_declare_is_not_an_error` |
| LSI-A3 | `scripts/tests/test_shared_skill_surface_scope.py`: the `EVOLVED`, `CONFLICT`, `DIVERGED`, foreign, unmanaged and withdrawn-with-changes tests |
| LSI-A4 a, b | `scripts/tests/test_shared_skill_surface_scope.py::test_a_learning_written_after_the_pruner_digests_is_not_deleted`, `::test_a_learning_written_after_the_update_comparison_is_not_deleted` |
| LSI-A4 c | `scripts/tests/test_shared_skill_surface_scope.py::test_an_installed_copy_that_cannot_be_taken_aside_is_kept` |
| LSI-A4 d | `scripts/tests/test_shared_skill_surface_scope.py::test_a_copy_stranded_aside_is_pruned_like_any_withdrawn_projection` |
| LSI-B1 | `packages/tests/test_mcp_daemon.py::test_the_reclaim_cli_takes_both_snapshots_under_the_claim_guard`, `::test_a_guard_that_cannot_be_taken_is_not_a_reclaim` |

## Not covered by this spec

Which harness may evolve a skill, where proposals for upstream propagation live, and
the granularity of the recorded baseline are operator decisions that remain open
(see `docs/reviews/2026-09-29-pr41-round-4/RESULT.md`). Nothing here decides them.
