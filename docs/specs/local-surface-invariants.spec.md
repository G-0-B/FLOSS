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
  - "FLOSS/skill-corpus/superpowers-brainstorming/scripts/server.cjs"
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

- a. The refusal is made before any write. Every target is resolved and checked first,
  so a refused run leaves nothing half written.
- b. A manifest path with no `scope` field (the agent surface's mirrors, context
  pack, gemini, opencode and vibe targets) is treated as repo scope.
- c. A check that cannot resolve a path refuses. It does not skip.

*Why:* `scope` is a declaration and the path is a fact. Trusting the first lets a
repo-scope run rewrite machine-wide configuration that nobody opted into.

**LSI-A2. Event-map injectivity.** Within one target, two source events that both
carry hooks must not map to the same native event name. Resolution fails and names
both source events and the native name. A source event with no hooks, and an event
absent from the map, take no part in the check: an empty definition list neither
raises nor replaces a non-empty one mapped to the same name. An empty list is still
emitted when nothing else claims the name, because generated configs rely on empty
arrays to clear an event.

*Why:* assigning the second over the first drops one set of hooks from the generated
file with nothing reporting it.

**LSI-A3. Preservation.** A managed skill projection whose payload differs from the
baseline recorded when it was installed is never overwritten, removed or adopted by
a materializer run. It is kept, surfaced as a `KEEP` line, and not counted as drift
by `--check`. (The operator's rule of 2026-09-29: skills a harness evolved are to be
propagated back to the shared base, not replaced by it.)

Equality with the baseline proves that no harness changed the copy. It does not
preserve source revisions: a revision the operator replaced in the source without
committing it is the operator's to keep.

**LSI-A4. Verified removal.** The comparison with the baseline that licenses an
update or a removal is made on the copy *after* it has been taken out of its
discoverable position, and not before. Concretely:

- a. The projection is renamed to a sibling name nobody writes to, and the renamed
  copy is compared with the baseline.
- b. If it equals the baseline it is deleted. If it differs, it is renamed back, kept
  and surfaced as changed, and the run reports no drift for it.
- c. If it cannot be renamed (an open file on Windows, for example) it is kept and
  surfaced as in use. If the renamed copy cannot be read it is put back and surfaced
  as unreadable. Changed, in use and unreadable are reported distinctly, because the
  operator's next step differs for each. A copy that cannot be verified in isolation
  is not removed.
- d. A copy stranded aside by a crash is picked up by the next run. If its base name
  is a listed skill and the live name is absent, it is put back before anything is
  installed. Otherwise it is an ordinary withdrawn projection: removed if unchanged,
  reported if not.
- e. An exception of any kind between the rename and the end of verification,
  including an interruption, puts the copy back. A copy that was verified and then
  could not be fully deleted is reported with the location of what remains, and does
  not abort the run.
- f. The window is narrowed, not closed. On POSIX a process that holds a file open
  across the rename still writes into the renamed copy, and a write landing between
  verification and deletion is deleted with it. Windows refuses to rename a directory
  with open files (c). `--check` cannot know that a rename would be refused, so it
  reports the content drift that a write run may then keep.
- g. The aside name begins with a dot. Codex's loader skips dot-directories (read in
  `rust-v0.128.0`); the other harnesses' scanners have not been read, so a copy
  stranded by a crash may be discovered by them as a second skill.

*Why:* comparing and then removing leaves a window in which a harness can write a
learning that no longer matches the baseline, after the decision was already taken.

**LSI-A5. Skill names are single path components.** A skill's frontmatter `name` must
match `^[A-Za-z0-9][A-Za-z0-9._-]*$`. A name containing a path separator or `..`, or
an absolute path, is refused before anything is written, because the name becomes
`<target root>/<name>`.

**LSI-A6. A failed install removes only what is provably its own.**

- a. After a failed copy the directory is removed whole. This call created it (the
  copy refuses an existing destination), and a file the failed write left truncated
  is its own, so it is not required to equal the shared base.
- b. After a failed marker publish the copy had completed, so the directory is
  removed only if every file in it equals the shared base's file at that path.
  Anything else, such as a file a harness wrote into the fresh copy in the
  meantime, is kept and surfaced.

## Part B. MCP daemon claims

**LSI-B1. Reclaim holds the guard across the pair.** `--reclaim-claim` takes the
claim snapshot and the identity-sidecar snapshot, and performs both removals, while
holding the claim guard that `--release-claim` and `--record-identity` hold. If the
guard cannot be taken, for any reason, the verdict is `NOT_RECLAIMED`, the exit status
is 1, and nothing is removed.

*Why:* two snapshots taken outside the guard can pair the old claim with a
replacement launcher's sidecar, and the removal that follows can delete a live
daemon's identity record.

## Part C. Local companion servers

**LSI-C1. The bootstrap page reflects no request-supplied value, and its embedded
JSON cannot close its script element.** The brainstorming companion's
`server.cjs` serves a bootstrap page that stores the session key in
`sessionStorage`.

- a. The page embeds the server's own token, not the `key` query value. The two are
  equal once the check has passed, so behavior is unchanged, but no string taken
  from the request reaches the response.
- b. The embedded JSON is escaped for HTML: `<`, `>`, `&`, U+2028 and U+2029 are
  written as `\uXXXX` escapes, so no key value can end the script element or the
  string literal.

*Why:* CodeQL (`js/reflected-xss`, high) reported the reflection on PR #41. The
earlier triage (`72f0240`) judged it unreachable by an attacker, because the value
must equal the secret token, and that still holds. This is hardening, not a
vulnerability fix: it makes the sink safe on its own terms instead of depending on
a guard a few lines above it.

## Conformance

| Clause | Test |
|---|---|
| LSI-A1 | `tests/test_shared_agent_surface_mcp.py::test_a_repo_scoped_target_may_not_resolve_outside_the_workspace`, `::test_a_repo_scoped_antigravity_target_may_not_resolve_outside_the_workspace`, `::test_a_repo_scoped_hermes_target_may_not_resolve_outside_the_workspace`, `::test_a_repo_scoped_target_inside_the_workspace_is_still_written`, `::test_every_written_form_of_an_outside_path_is_refused` (relative, `~`, env variable), `::test_unscoped_manifest_paths_may_not_leave_the_workspace`, `::test_a_refused_target_leaves_every_other_target_unwritten`; hook: `scripts/tests/test_shared_hook_surface.py::test_a_refused_target_leaves_the_registry_unwritten`, `::test_a_scope_check_that_cannot_resolve_refuses`; skill: `scripts/tests/test_shared_skill_surface_scope.py` |
| LSI-A2 | `scripts/tests/test_shared_hook_surface.py::test_two_events_mapped_to_one_native_name_are_refused_not_overwritten`, `::test_a_collision_among_events_the_target_does_not_declare_is_not_an_error`, `::test_an_event_with_no_hooks_takes_no_part_in_the_collision_check` |
| LSI-A3 | `scripts/tests/test_shared_skill_surface_scope.py`: the `EVOLVED`, `CONFLICT`, `DIVERGED`, foreign, unmanaged and withdrawn-with-changes tests |
| LSI-A4 a, b | `scripts/tests/test_shared_skill_surface_scope.py::test_a_learning_written_after_the_pruner_digests_is_not_deleted`, `::test_a_learning_written_after_the_update_comparison_is_not_deleted` |
| LSI-A4 c | `scripts/tests/test_shared_skill_surface_scope.py::test_an_installed_copy_that_cannot_be_taken_aside_is_kept`, `::test_a_blocked_rename_on_update_is_reported_as_in_use_not_evolved`, `::test_an_unreadable_copy_is_reported_as_unreadable_not_changed` |
| LSI-A4 d | `scripts/tests/test_shared_skill_surface_scope.py::test_a_copy_stranded_aside_is_pruned_like_any_withdrawn_projection`, `::test_a_stranded_copy_of_a_listed_skill_is_put_back_before_install` |
| LSI-A4 e | `scripts/tests/test_shared_skill_surface_scope.py::test_an_interrupted_verification_puts_the_copy_back`, `::test_a_copy_that_cannot_be_put_back_is_kept_and_named`, `::test_a_copy_that_cannot_be_fully_deleted_is_reported_not_raised` |
| LSI-A4 check | `scripts/tests/test_shared_skill_surface_scope.py::test_check_and_dry_run_never_rename` |
| LSI-A5 | `scripts/tests/test_shared_skill_surface_scope.py::test_a_skill_name_that_is_not_a_single_path_component_is_refused` |
| LSI-A6 a | `scripts/tests/test_shared_skill_surface_scope.py::test_a_copy_that_fails_midway_leaves_nothing_half_installed` |
| LSI-A6 b | `scripts/tests/test_shared_skill_surface_scope.py::test_a_failed_marker_publish_does_not_delete_what_a_harness_wrote`, `::test_a_failed_marker_publish_with_nothing_extra_leaves_nothing_behind` |
| LSI-C1 | `scripts/tests/test_brainstorm_bootstrap_page.py::test_a_key_cannot_close_the_script_element`, `::test_line_separators_are_escaped`, `::test_an_ordinary_key_round_trips` (skipped when `node` is absent) |
| LSI-B1 | `packages/tests/test_mcp_daemon.py::test_the_reclaim_cli_takes_both_snapshots_under_the_claim_guard`, `::test_reclaim_removes_both_records_while_holding_the_guard`, `::test_a_guard_that_cannot_be_taken_is_not_a_reclaim`, `::test_a_guard_failure_that_is_not_a_timeout_is_not_a_reclaim` |

## Not covered by this spec

Which harness may evolve a skill, where proposals for upstream propagation live, and
the granularity of the recorded baseline are operator decisions that remain open
(see `docs/reviews/2026-09-29-pr41-round-4/RESULT.md`). Nothing here decides them.
