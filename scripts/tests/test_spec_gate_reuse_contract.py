"""The reuse gate's schema and its enforcement must not drift apart.

This repository has now produced the same defect four times: a specification is
edited, a nearby constant is treated as the implementation of it, and a
*different* constant somewhere else turns out to be the thing with actual force.

  1. `spec_gate.GATED_SURFACES` drifted from the registry's `gated_surfaces`
     field, and the registry field turned out to be documentation only.
  2. The v1.5 D3 evidence-type widening reached the spec, the JSON Schema and
     `claim_schema.EVIDENCE_TYPES`, but missed `_EVIDENCE_REF_TYPES` in
     `provenance.py` -- the set `validate_packet` actually enforced.
  3. Candidate validation stringified its fields, so `{"name": 7,
     "truth_status": "Trusted"}` satisfied a schema requiring a string name and
     a three-value enum.
  4. Tightening `reuse.reviewer` to a structured object left the schema still
     declaring a string, so for one commit NO reviewer value could satisfy both
     the declared schema and the fail-closed runtime gate.

Every one of those was caught by an external reviewer rather than by the repo.
These tests make the fifth one fail here instead.

`scripts/tests/` is exempt from the spec gate, so this file needs no registry
entry -- see EXEMPT_SEGMENTS.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "docs" / "specs" / "reuse-gate.schema.json"


def _load_spec_gate():
    spec = importlib.util.spec_from_file_location(
        "spec_gate_under_test", REPO_ROOT / "scripts" / "spec_gate.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gate():
    return _load_spec_gate()


@pytest.fixture(scope="module")
def schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_required_reuse_keys_match_the_schema(gate, schema):
    assert set(gate.REUSE_REQUIRED_KEYS) == set(schema["required"])


def test_candidate_contract_matches_the_schema(gate, schema):
    candidate = schema["properties"]["candidates"]
    assert candidate["minItems"] == 1, "an empty search is not a search"
    item = candidate["items"]
    assert set(item["required"]) == {"name", "truth_status"}
    assert (
        tuple(item["properties"]["truth_status"]["enum"]) == gate.REUSE_TRUTH_STATUSES
    )


def test_reviewer_is_declared_as_the_object_that_is_enforced(gate, schema):
    """The fourth instance of the drift. A string here made the gate unsatisfiable."""
    reviewer = schema["properties"]["reviewer"]
    assert reviewer["type"] == "object", (
        "spec_gate rejects every non-object reviewer; a schema declaring a "
        "string leaves no value that satisfies both"
    )
    assert set(reviewer["required"]) == set(gate.REVIEWER_REQUIRED_KEYS)
    assert reviewer["properties"]["surfaces"]["minItems"] == gate.REVIEWER_MIN_SURFACES
    assert reviewer["properties"]["families"]["minItems"] == gate.REVIEWER_MIN_FAMILIES


def test_reviewer_prose_is_refused(gate):
    problems = gate._reviewer_problems("x.md", "reviewed by the panel, all good")
    assert problems, "prose must not satisfy an independence requirement"


def test_reviewer_needs_distinct_surfaces_and_families(gate):
    duplicated = {
        "surfaces": ["groq", "groq", "groq"],
        "families": ["gpt", "gpt", "gpt", "gpt"],
        "record": "docs/specs/reuse-gate.spec.md",
        "outcome": "APPROVED",
        "date": "2026-08-25",
    }
    problems = gate._reviewer_problems("x.md", duplicated)
    assert any("distinct" in p for p in problems)


def test_reviewer_record_must_resolve(gate):
    problems = gate._reviewer_problems(
        "x.md",
        {
            "surfaces": ["groq", "mistral", "nvidia"],
            "families": ["gpt", "qwen", "deepseek", "llama"],
            "record": "docs/specs/does-not-exist.md",
            "outcome": "APPROVED",
            "date": "2026-08-25",
        },
    )
    assert any("does not exist" in p for p in problems)


def test_a_complete_reviewer_record_passes(gate):
    assert (
        gate._reviewer_problems(
            "x.md",
            {
                "surfaces": ["groq", "mistral", "nvidia"],
                "families": ["gpt", "qwen", "deepseek", "llama"],
                "record": "docs/specs/reuse-gate.spec.md",
                "outcome": "APPROVED",
                "date": "2026-08-25",
            },
        )
        == []
    )


def test_grandfathering_is_pinned_to_content(gate, tmp_path, monkeypatch):
    """A path-only exemption would cover text nobody has read.

    The exemption records the sha256 of the version that was grandfathered. Any
    edit to the artifact must lapse it, which is the moment the deferred review
    becomes due.
    """
    rel = "FLOSS/docs/specs/reuse-gate.spec.md"
    assert rel in gate.REVIEWER_GRANDFATHERED
    assert gate._is_reviewer_grandfathered(rel), (
        "the pinned hash no longer matches the file on disk -- if the edit was "
        "intentional, run the deferred reuse-review poll and remove the entry "
        "rather than re-pinning it"
    )
    monkeypatch.setitem(gate.REVIEWER_GRANDFATHERED, rel, "0" * 64)
    assert not gate._is_reviewer_grandfathered(rel)
