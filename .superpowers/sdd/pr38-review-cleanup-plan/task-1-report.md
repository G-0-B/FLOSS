# PR38 cleanup Task 1 — implementation report

## Status

✅ Complete. The non-runtime review corrections were implemented on
`codex/pr38-review-cleanup` in the assigned worktree. No protected runtime or
integrity-zome files were changed.

## TDD evidence

The initial focused test run failed as expected before implementation:

- missing required capability proof was accepted;
- unknown top-level and nested proof fields were accepted;
- the semantic validator module did not exist;
- TogetherAI key configuration helper did not exist.

After the implementation, `python -m pytest tests/test_pr38_review_cleanup.py -q`
passed: **9 passed**. The suite covers required proof shape, unknown top-level
and nested fields, ordered/inverted analog bounds, preservation of an uppercase
TogetherAI key, legacy-key fallback behavior, and an empty sweep making no
external LLM call. The key tests use a case-sensitive mapping because Windows
environment-variable names are case-insensitive and cannot otherwise represent
both spellings at once.

## Implementation

- Hardened the Yumeichan capability schema with closed top-level and proof
  objects; a required Ed25519/RFC 8785 digest proof; and explicit statements
  that schema validation does not verify signatures.
- Added the small reusable `validate_capability()` semantic validator. It
  applies the existing schema and rejects inverted threshold bounds.
- Corrected the Watch and provenance specs, including the explicit ⚠️ Specified
  `300 seconds (5 minutes)` deterministic-action-timestamp BudgetEntry window.
  No Rust implementation or test evidence was claimed or changed.
- Corrected the project-name glossary alias and unassigned the stale Steward
  Vote ADR-13 references, preserving ADR-13 for Yumeichan Watch.
- Preserved an existing uppercase `TOGETHERAI_API_KEY`; a non-empty lowercase
  legacy spelling is copied only when the canonical spelling is absent.
- Registered the currently gated PR38 artifacts required for the spec-gate
  audit at this task head.

## Verification

All commands were run from `C:\~shit\_codex_pr38_cleanup`:

```text
python -m pytest tests/test_pr38_review_cleanup.py -q
# 9 passed

python scripts/spec_gate.py --check
# SPEC-GATE OK: 99 registered, 0 missing; 7 stale non-fatal entries

ruff check scripts/major_consolidation_sweep.py scripts/yumeichan_watch_capabilities.py tests/test_pr38_review_cleanup.py
# All checks passed

python -m json.tool docs/specs/yumeichan-watch-capabilities.schema.json
python -m json.tool docs/specs/spec-registry.json
git diff --check
# all exit 0
```

## Self-review

- Scope is confined to the brief-authorized documentation, registry, script,
  new validator, test, and this report.
- The pre-existing `.serena/project.yml` modification was not edited or staged.
- `spec_gate.py --check` reports pre-existing stale registry entries as
  non-fatal. In this linked-worktree layout it calculates `WORKSPACE_ROOT` as
  the parent directory, so the newly added validator is also reported stale
  until these changes are present at `C:\~shit\FLOSS`; the command still
  reports zero missing gated artifacts and exits successfully.
