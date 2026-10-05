# Coordination room board v1 — revision 5 audit

Date: 2026-10-04. Status: noncanonical review evidence; audit in progress.

**Provisional disposition: Phase 1 has no newly identified implementation blocker; numeric error handling still needs correction before Phase 2.** Deployment checks and the three-stage green-set comparison are running. This file is saved early under the operator's receipt-first instruction and will be completed before the final response.

## Identity, scope, and method

- ✅ **Verified:** the exact [plan snapshot](plan-revision-5.md) has SHA-256 `f2a8392e874a6f90c6818657fccc0050625da518fb09860dff0d58c68b8d1752`. The [reconstruction](rebuild.py) checks this pin and uses the requested Git objects. [Extraction manifest](extraction-r5.json).
- ✅ **Verified:** baseline, rollback checkpoint, and Phase 1 are byte-identical to round 4. Phase 2 changes exactly `room_bridge.py`, `test_room_bridge_parse.py`, and `test_room_bridge_pair.py`; 1,428 other files match. [Byte comparison](r4-byte-comparison.json), [plan diff](plan-r4-r5.diff).
- ⚠️ **Scope:** evaluation only. No project implementation or runtime approval is supplied. Tests use archive fixtures and scratch runtime paths inside the workspace.

## Round-four dispositions

| Finding | Current disposition | Evidence / boundary |
|---|---|---|
| R4-01 | Pending independent execution. | ⚠️ The plan replaces tail arithmetic with event correlation and a startup lower bound. |
| R4-02 | **Partially closed.** | ✅ Fractions, booleans and nonfinite values now produce a normal error artifact and zero room calls. Very large JSON integer literals still produce internal errors; see R5-01. [Numeric receipt](number-results.json). |
| R4-03 | Pending independent execution. | ⚠️ The helper now compares the target token exactly. |

## R5-01 — P2, before Phase 2: large JSON integer literals bypass the normal error artifact

**Locations:** plan 3513–3517 (`json.loads` catches only `JSONDecodeError`), 3495–3510 (`_integer`), and the executor's `CommandError` boundary. Continuation of R4-02, not a Phase 1 blocker.

✅ **Verified:** on Python 3.13.1 with its default 4,300-digit conversion limit, `{"op":"post","text":"x","reply_to":` followed by 4,301 decimal digits and `}` raises plain `ValueError` inside `json.loads`, before `_integer` can range-check it. The real scratch A2A HTTP path returns `InternalError`, JSON-RPC `-32603`, including the Python conversion-limit message. It does not return an `error: ...` artifact with FAILED task state. The room recorder receives zero calls. The same defect reproduces for `since_seq` and `limit`, for a negative 4,301-digit literal, and for a 10,000-digit literal. [142 parser and 142 HTTP cases](number-results.json), [tracebacks](number-output.txt), [reproducer](audit-numbers.py).

✅ **Verified controls:** 4,300-digit JSON integers are rejected with `CommandError`; large quoted decimal strings and `read since=` values take the normal error path. Ordinary integers, supported decimal strings, the `2**53` boundary, and in-range limit clamping still work. Fractions, booleans, signs in strings, Unicode digits, lists and objects do not reach the room. [Numeric receipt](number-results.json).

**Improvement:** translate decoder integer-conversion failures into `CommandError`, or impose a bounded integer decoder; retain the interpreter's resource limit. Add HTTP closure cases for over-limit positive and negative JSON integers in all three fields. Require the usual error artifact, FAILED state, and zero room calls.

## Verification and evidence limits

⚠️ **Pending:** completion and per-case comparison of base, Phase 1 and Phase 2; both-shell deployment closure and edge checks. No production lifecycle rehearsal, Linux run, live Hermes operation or real rollback commit is implied by these scratch tests.
