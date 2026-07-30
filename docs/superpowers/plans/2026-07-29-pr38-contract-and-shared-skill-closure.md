# PR #38 Contract and Shared-Skill Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close four reproduced PR #38 contract defects and promote the tested FLOSSI0ULLK orientation skill v0.3.4 through the canonical generated shared surface.

**Architecture:** Repair the symbolic evaluation contract independently from runtime gateway behavior. Centralize validated evidence-DAG traversal in the provenance package, keep prompt formatting and bounds in the gateway, and update generated skill projections only from canonical corpus bytes. Every implementation task uses a red-green test cycle and an exact task-level review gate.

**Tech Stack:** Python 3.13, pytest, jsonschema Draft 2020-12, PyNaCl, JCS/BLAKE3 provenance helpers, Markdown/JSON skill corpus, GitHub CLI.

## Global Constraints

- Frozen implementation base: `705f555977e118c075ec0cccc2910bd2f5fe134a`.
- Cloudflare is excluded and must not be modified or claimed fixed.
- No ADR, integrity-zome, `.mcp.json`, `.claude/settings.json`, `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` edits.
- Preserve the user-owned `.serena/project.yml` modification.
- No production-code edit may precede its failing regression test.
- Preserve existing provenance validation, maximum evidence depth 8, cycle rejection, vote semantics, and legacy one-argument voter compatibility.
- Voter context exposes metadata only, never referenced file contents; maximum 32 non-packet refs and 4,096 rendered characters.
- Evaluation artifact hashes use `sha256("FLOSS:provenance-eval:<id>:artifact:<n>")` in lowercase hexadecimal.
- `D` and `B` plus 43 base64url characters are both valid signing AIDs.
- Canonical orient `SKILL.md` must have SHA-256 `491A2B37B9CF73A3FCDF7FCA5D9CEF0B0E81D8B62A10DA40238E0EF695B266EE`.
- Generated projections are never hand-edited.
- Push only by non-force fast-forward after an exact frozen-diff review.
- Resolve only `PRRT_kwDOPkAi3s6UmelA`, `PRRT_kwDOPkAi3s6UmelE`, `PRRT_kwDOPkAi3s6UmelH`, and `PRRT_kwDOPkAi3s6UmelJ`, and only after direct readback proves closure.

---

### Task 1: Repair the Provenance Evaluation Contract

**Files:**
- Create: `tests/test_provenance_eval_contract.py`
- Modify: `evals/provenance_packet_validation/dev.jsonl`
- Modify: `evals/provenance_packet_validation/heldout.jsonl`
- Modify: `evals/provenance_packet_validation/rubric.json`
- Modify: `docs/specs/provenance-packet.spec.md`

**Interfaces:**
- Consumes: `docs/specs/provenance-packet.schema.json`, both JSONL splits, and the rubric's symbolic `crypto_facts` contract.
- Produces: 30 schema-valid packet fixtures, deterministic artifact hashes, and one consistent `[DB]` AID contract across machine and narrative surfaces.

- [ ] **Step 1: Write the failing contract tests**

Create `tests/test_provenance_eval_contract.py` with helpers and assertions equivalent to:

```python
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "evals" / "provenance_packet_validation"
SCHEMA = json.loads(
    (ROOT / "docs" / "specs" / "provenance-packet.schema.json").read_text(
        encoding="utf-8"
    )
)
HEX64 = re.compile(r"^[a-f0-9]{64}$")


def load_rows(name: str) -> list[dict]:
    return [
        json.loads(line)
        for line in (MODULE / name).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def expected_hash(row_id: str, artifact_index: int) -> str:
    seed = f"FLOSS:provenance-eval:{row_id}:artifact:{artifact_index}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def artifact_refs(row: dict) -> list[dict]:
    return [
        ref
        for entry in row["input"]["packet"]["a"]
        for ref in entry.get("artifact_refs", [])
    ]


def test_split_sizes_and_unique_ids():
    rows = load_rows("dev.jsonl") + load_rows("heldout.jsonl")
    assert len(load_rows("dev.jsonl")) == 20
    assert len(load_rows("heldout.jsonl")) == 10
    assert len({row["id"] for row in rows}) == 30


def test_every_packet_satisfies_machine_schema():
    validator = Draft202012Validator(SCHEMA)
    for row in load_rows("dev.jsonl") + load_rows("heldout.jsonl"):
        errors = sorted(validator.iter_errors(row["input"]["packet"]), key=str)
        assert not errors, (row["id"], [error.message for error in errors])


def test_artifact_hashes_are_deterministic_lowercase_hex():
    for row in load_rows("dev.jsonl") + load_rows("heldout.jsonl"):
        for index, ref in enumerate(artifact_refs(row)):
            assert HEX64.fullmatch(ref["sha256"])
            assert ref["sha256"] == expected_hash(row["id"], index)


def test_crypto_facts_match_artifact_mismatch_goldens():
    for row in load_rows("dev.jsonl") + load_rows("heldout.jsonl"):
        mismatch = "E-ARTIFACT-HASH-MISMATCH" in row["golden"]["defects"]
        assert row["input"]["crypto_facts"][
            "artifact_hashes_match_workspace"
        ] is (not mismatch)


def test_b_prefixed_aid_matches_schema_production_contract():
    row = next(row for row in load_rows("dev.jsonl") if row["id"] == "ppv-dev-007")
    assert row["input"]["packet"]["i"].startswith("B")
    assert row["golden"] == {"status": "valid", "defects": ["PPV-OK"]}
    rubric = json.loads((MODULE / "rubric.json").read_text(encoding="utf-8"))
    assert "[DB]" in rubric["defect_codes"]["E-I-SHAPE"]
    spec = (ROOT / "docs" / "specs" / "provenance-packet.spec.md").read_text(
        encoding="utf-8"
    )
    assert "`D` or `B`" in spec
```

Also assert every `crypto_facts` value is a boolean and the rubric explains
that these values are symbolic oracle inputs rather than a production replay
claim.

- [ ] **Step 2: Run the focused tests and preserve RED**

Run:

```powershell
python -m pytest tests/test_provenance_eval_contract.py -q
```

Expected: failures for malformed artifact hashes, schema validation, the
`ppv-dev-007` golden, and narrative/rubric `[DB]` wording.

- [ ] **Step 3: Apply deterministic fixture regeneration**

Mechanically rewrite only `artifact_refs[*].sha256` in both JSONL files:

```python
for row in rows:
    for index, ref in enumerate(artifact_refs(row)):
        ref["sha256"] = expected_hash(row["id"], index)
```

Preserve row order, key order, one compact JSON object per line, UTF-8, and one
trailing newline. For `ppv-dev-007`, set:

```json
{"status":"valid","defects":["PPV-OK"]}
```

and update its rationale to state that `B` is a valid non-transferable signing
AID under the executable `[DB]` contract.

Update the rubric:

- `E-I-SHAPE` means the AID does not match
  `^[DB][A-Za-z0-9_-]{43}$`.
- The crypto-facts paragraph explicitly says facts are counterfactual oracle
  inputs for adversarial rows and do not claim every row is replayable through
  the production cryptographic validator.

Update the prose spec AID row to say:

```text
`D` or `B` + 43-char base64url Ed25519 verify key; `D` is transferable and
`B` is non-transferable, and both are valid signing identifiers in v1.4.
```

- [ ] **Step 4: Run focused and related tests**

Run:

```powershell
python -m pytest tests/test_provenance_eval_contract.py -q
python -m pytest packages/activity_log/tests packages/metacoordinator_mcp/tests -q
git diff --check
```

Expected: all pass and no whitespace errors.

- [ ] **Step 5: Commit the isolated task**

Stage only the five Task 1 files and commit:

```text
fix: repair provenance evaluation contracts
```

---

### Task 2: Render Validated Evidence DAGs and Skip Persisted OMO Voters

**Files:**
- Modify: `packages/activity_log/provenance.py`
- Modify: `packages/metacoordinator_mcp/tools.py`
- Modify: `packages/metacoordinator_mcp/tests/test_voter_context_rendering.py`
- Modify: `packages/metacoordinator_mcp/tests/test_tools.py`

**Interfaces:**
- Produces:

```python
def validated_non_packet_evidence_refs(
    packet_or_path: Path | str | dict[str, Any],
    *,
    workspace_root: Path | str | None = None,
    provenance_root: Path | str | None = None,
    max_depth: int = 8,
    max_refs: int = 32,
) -> tuple[list[dict[str, str]], bool]:
    """Return stable validated non-packet metadata and whether it was truncated."""
```

- `_collect_provenance_state()` additionally preserves each validated top-level
  packet's resolved path for the renderer.
- `_known_voter_name()` recognizes LiteLLM, Flowith, OMO Momus, and OMO Critic
  closure prefixes.

- [ ] **Step 1: Write failing evidence-DAG tests**

Extend `test_voter_context_rendering.py` with real signed packet fixtures that:

1. create a child packet carrying `[spec] docs/specs/provenance-packet.spec.md`;
2. create a valid root packet whose only evidence ref is that child packet;
3. submit/render the root and assert the voter context includes the child's
   non-packet spec ref;
4. cite the same child twice and assert the ref appears once;
5. create 33 direct non-packet refs and assert the result contains a truncation
   marker, at most 32 rendered refs, no newline injection, and at most 4,096
   characters;
6. present an invalid/cyclic/depth-failing packet and assert no derived child
   evidence is rendered.

The test must use production `create_packet()` and `validate_packet()` helpers
for valid rows; do not monkeypatch the validator for the main child-DAG test.

- [ ] **Step 2: Write failing deferred-retry tests**

In `test_tools.py`, create named no-network voter closures:

```python
critic.__name__ = "omo_critic_voter_critic-probe"
momus.__name__ = "omo_momus_voter_momus-probe"
```

Pass existing votes for `critic-probe` and `momus-probe` to
`_collect_new_votes()`. Assert neither closure is invoked and no new vote is
returned. Preserve the existing test proving a legacy one-argument voter is
invoked when it has no persisted vote.

- [ ] **Step 3: Run both focused RED slices**

Run:

```powershell
python -m pytest packages/metacoordinator_mcp/tests/test_voter_context_rendering.py -q
python -m pytest packages/metacoordinator_mcp/tests/test_tools.py -q
```

Expected: child evidence remains absent and OMO closures are invoked despite
persisted votes.

- [ ] **Step 4: Implement validated traversal in the provenance package**

Implement `validated_non_packet_evidence_refs()` with:

- an initial `validate_packet()` requirement;
- the same workspace resolution and `max_depth=8` boundary;
- an active-path digest set for cycle rejection;
- a visited-packet set for shared-child deduplication;
- stable first-seen order;
- metadata copies containing only `type`, `ref`, and optional `sha256`;
- early stop at `max_refs`;
- `ValueError` carrying validation errors when the supplied root is invalid.

Do not read any referenced non-packet content.

- [ ] **Step 5: Implement bounded context formatting**

Change `_collect_provenance_state()` to return `(packet, resolved_path)` pairs
internally. In `_render_voter_context()`:

- call `validated_non_packet_evidence_refs()` on the validated path;
- sanitize carriage returns, newlines, tabs, and repeated whitespace in every
  rendered value;
- cap individual values before assembly;
- render at most 32 refs;
- cap the complete context at 4,096 characters;
- append a deterministic `[truncated]` marker within the bound;
- preserve digest, consent, direct-root, and `(none)` behavior.

Any traversal exception yields no derived context for that packet; it must not
weaken `submit_claim()` validation.

- [ ] **Step 6: Implement OMO retry recognition**

Extend `_known_voter_name()` with:

```python
for prefix in (
    "litellm_voter_",
    "flowith_voter_",
    "omo_momus_voter_",
    "omo_critic_voter_",
):
```

Do not change vote weights, tallying, provider construction, or post-invocation
duplicate rejection.

- [ ] **Step 7: Run focused and package verification**

Run:

```powershell
python -m pytest packages/metacoordinator_mcp/tests/test_voter_context_rendering.py -q
python -m pytest packages/metacoordinator_mcp/tests/test_tools.py -q
python -m pytest packages/activity_log/tests packages/metacoordinator_mcp/tests packages/orchestrator/tests tests/test_pr38_review_cleanup.py -q
python scripts/smoke_test_voters.py
git diff --check
```

If the smoke script requires unavailable external credentials, record the exact
output as blocked and do not reinterpret it as a unit-test failure.

- [ ] **Step 8: Commit the isolated task**

Stage only the four Task 2 files and commit:

```text
fix: render validated voter evidence DAGs
```

---

### Task 3: Promote Orient v0.3.4 Through the Shared Skill Surface

**Files:**
- Create: `tests/test_shared_orient_skill_contract.py`
- Modify: `skill-corpus/flossi0ullk-orient/SKILL.md`
- Modify: `skill-corpus/flossi0ullk-orient/CHANGELOG.md`
- Operational readback only: enabled projection directories outside the PR
  worktree

**Interfaces:**
- Consumes: private tested file
  `C:\Users\kalis\.codex\skills\flossi0ullk-orient\SKILL.md`.
- Produces: canonical `SKILL.md` with exact SHA-256
  `491A2B37B9CF73A3FCDF7FCA5D9CEF0B0E81D8B62A10DA40238E0EF695B266EE`
  and byte-identical enabled projections.

- [ ] **Step 1: Write the failing canonical-skill test**

Create `tests/test_shared_orient_skill_contract.py`:

```python
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill-corpus" / "flossi0ullk-orient" / "SKILL.md"
CHANGELOG = ROOT / "skill-corpus" / "flossi0ullk-orient" / "CHANGELOG.md"
EXPECTED = "491A2B37B9CF73A3FCDF7FCA5D9CEF0B0E81D8B62A10DA40238E0EF695B266EE"


def test_canonical_orient_skill_is_pressure_tested_v034():
    raw = SKILL.read_bytes()
    text = raw.decode("utf-8")
    assert hashlib.sha256(raw).hexdigest().upper() == EXPECTED
    assert "version: 0.3.4" in text
    for required in (
        "Mandatory response/output skeleton",
        "Fact: <observed artifact or output>",
        "documentation examples: <excluded list | none>",
        "Durable-write disposition",
        "OmniRoute attempt (repeat only for each actual request)",
        "successful independent families:",
        "CONFLICT — human resolution",
    ):
        assert required in text


def test_corpus_changelog_records_every_evolution_step():
    text = CHANGELOG.read_text(encoding="utf-8")
    for version in ("0.3.0", "0.3.1", "0.3.2", "0.3.3", "0.3.4"):
        assert f"## {version}" in text
```

- [ ] **Step 2: Run the test and preserve RED**

Run:

```powershell
python -m pytest tests/test_shared_orient_skill_contract.py -q
```

Expected: canonical source is v0.2.0 and the hash/changelog assertions fail.

- [ ] **Step 3: Promote exact bytes to the branch canonical corpus**

First verify the private file hash with `Get-FileHash`. Use `apply_patch` to
make the branch corpus `SKILL.md` byte-identical to that private file. Update
the separate corpus changelog with the v0.3.0 through v0.3.4 evolution history
already embedded in `SKILL.md`.

Run:

```powershell
Get-FileHash C:\Users\kalis\.codex\skills\flossi0ullk-orient\SKILL.md -Algorithm SHA256
Get-FileHash skill-corpus\flossi0ullk-orient\SKILL.md -Algorithm SHA256
python -m pytest tests/test_shared_orient_skill_contract.py -q
git diff --check
```

Both hashes must equal `EXPECTED`.

- [ ] **Step 4: Commit the canonical source independently**

Stage only the Task 3 test and two corpus files and commit:

```text
feat: promote orient skill v0.3.4
```

- [ ] **Step 5: Materialize live projections from the current canonical checkout**

This operational step runs only after Task 3 review approval.

The active `C:\~shit\FLOSS` checkout contains substantial unrelated user work,
so preserve every existing path and stage nothing there. Apply the exact
reviewed Task 3 `SKILL.md` and `CHANGELOG.md` bytes to the corresponding clean
canonical files in that checkout, recording pre/post hashes. Then run its
current materializer so its newer manifest, including Hermes, remains the
authority:

```powershell
python C:\~shit\FLOSS\scripts\materialize_shared_skill_surface.py --workspace-root C:\~shit
python C:\~shit\FLOSS\scripts\materialize_shared_skill_surface.py --workspace-root C:\~shit --check
```

The materializer's remove-and-recreate behavior for managed projection
directories is explicitly authorized by the human's approval of item 5.
Do not touch any unrelated dirty file.

- [ ] **Step 6: Verify every enabled projection by bytes**

Read the live manifest's enabled targets and compare each projected
`flossi0ullk-orient/SKILL.md` hash to the canonical hash. Required enabled
targets are Codex, Claude, Gemini, OpenCode, and Hermes. Record Cowork as
disabled/manual, not materialized.

Run the live shared-surface check available in that checkout. If the aggregate
runner reports unrelated pre-existing drift, preserve its output and prove the
skill-only materializer is clean.

---

### Task 4: Frozen Whole-Branch Review and PR Readback

**Files:**
- No production edits unless the final reviewer proves a defect.
- Append-only SDD ledger and review packages under this plan's ignored
  `.superpowers/sdd/` workspace.

**Interfaces:**
- Consumes: exact diff from
  `705f555977e118c075ec0cccc2910bd2f5fe134a` to final local head.
- Produces: review verdict, test evidence, remote fast-forward, and exact thread
  readback.

- [ ] **Step 1: Run complete local verification**

Run every focused command from Tasks 1–3 plus:

```powershell
python -m pytest packages tests/test_pr38_review_cleanup.py -q
git diff --check 705f555977e118c075ec0cccc2910bd2f5fe134a..HEAD
git diff --name-status 705f555977e118c075ec0cccc2910bd2f5fe134a..HEAD
git status --short
```

Confirm `.serena/project.yml` remains the only ambient change outside committed
task files.

- [ ] **Step 2: Obtain independent cross-family adversarial review**

Send the exact review package, not a prose summary, to at least three successful
independent model families through OmniRoute. Preserve every failed/partial
attempt and require valid analog votes in `[-0.999,+0.999]`. Treat polarization
as conflict requiring human adjudication, never as a majority override.

- [ ] **Step 3: Obtain a fresh-agent whole-branch review**

The reviewer must return both:

```text
SPEC COMPLIANCE: PASS | FAIL
TASK QUALITY: PASS | FAIL
ORIGINAL FOUR DEFECTS CLOSED: YES | NO
SAFE TO PUSH: YES | NO
```

Any load-bearing finding receives one TDD fix dispatch and one scoped
re-review.

- [ ] **Step 4: Verify remote ancestry and push**

Read the live PR head immediately before push. Require it to equal the task base
or be an ancestor of the final local head. Push the current commit chain by
non-force fast-forward to
`working/2026-06-16-adr-cleanup-reconverge`.

- [ ] **Step 5: Resolve only the four proven review threads**

Resolve the four authorized thread IDs only after the remote head includes the
fixes. Query all review threads afterward and record total and unresolved IDs.

- [ ] **Step 6: Final readback**

Read back:

- remote head SHA;
- PR state and mergeability;
- all check states;
- the four thread states;
- enabled projection hashes;
- local worktree status.

Cloudflare may remain failed and must be reported as excluded, not as a blocker
silently fixed by this slice.
