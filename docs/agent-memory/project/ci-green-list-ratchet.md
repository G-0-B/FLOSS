---
id: project-ci-green-list-ratchet
type: project
created: '2026-08-21'
status: active
applies_to:
- any-agent
source: measured_baseline_2026_08_21
title: CI gates on a measured green list, not the whole suite — widen it, never narrow it
---

`.github/workflows/python-ci.yml` (PR #44) does not gate on the full pytest suite,
because the full suite is red and gating on red produces a required check everyone
learns to ignore.

Baseline measured on `origin/main @ c1f51ac`, 2026-08-21 — not estimated, not recalled:

| Scope | Result |
|---|---|
| Full suite | **77 failed**, 459 passed, 7 skipped |
| `packages/` | 223 passed |
| `tests/` | 88 passed |
| `scripts/tests/` | 1 failed, 35 passed |
| Proposed green set | **346 passed, 1 deselected, ~14s** |

The green set is not "these three directories are clean" -- `scripts/tests/`
has one known-red test in it. 223 + 88 + 35 = 346 passing, with
`test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded`
deselected **by name** in `.github/workflows/python-ci.yml`, reason recorded
beside it. Deselecting one named test is a stated exception; describing the
directory as green would not be true.

Every failure but one is under `ARF/` — 20 in `test_conversation_memory.py`, 19 in
`test_embedding_composition.py`, 18 in `test_embedding_frames.py`, and a tail.

**The contract:** `green-set` is required and covers `packages/ tests/ scripts/tests/`.
`full-suite-advisory` runs everything with `continue-on-error` and uploads a report.
When a directory goes green in the advisory job, move it into `GREEN_PATHS`. The list
only ever widens. Narrowing it to make a PR pass is the failure mode this design exists
to prevent — if you are tempted, the honest move is to mark the PR red and say why.

**Do not** add `ARF/` to the green set expecting it to pass. See
[[project-conversation-memory-embedding-api-mismatch]] for why that tree is red.

Related: [[project-truth-label-canon]], [[feedback-no-unauthorized-modifications]].
