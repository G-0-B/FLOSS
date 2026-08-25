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


def test_reviewer_record_must_be_a_file_inside_the_repository(gate):
    """`exists()` alone accepted directories and paths outside the checkout.

    `.` is a directory that exists; `/etc/passwd` exists on most hosts and is
    not a poll record. An evidence pointer that can resolve to either is not
    evidence, it is a truthy string with extra steps.
    """
    base = {
        "surfaces": ["groq", "mistral", "nvidia"],
        "families": ["gpt", "qwen", "deepseek", "llama"],
        "outcome": "APPROVED",
        "date": "2026-08-25",
    }
    for bad in (".", "docs", "../../etc/passwd", "/etc/passwd", "C:/Windows/win.ini"):
        problems = gate._reviewer_problems("x.md", {**base, "record": bad})
        assert problems, f"{bad!r} must not satisfy the evidence gate"


def test_reviewer_outcome_and_date_must_be_typed(gate):
    """Same defect as the candidate fields, repeated one function later.

    `str(7).strip()` is non-empty, so `{"outcome": 7, "date": 20260825}` cleared
    a check whose whole purpose was to establish that a review happened.
    """
    base = {
        "surfaces": ["groq", "mistral", "nvidia"],
        "families": ["gpt", "qwen", "deepseek", "llama"],
        "record": "docs/specs/reuse-gate.spec.md",
    }
    problems = gate._reviewer_problems("x.md", {**base, "outcome": 7, "date": 20260825})
    assert any("outcome" in p for p in problems)
    assert any("date" in p for p in problems)

    malformed = gate._reviewer_problems(
        "x.md", {**base, "outcome": "APPROVED", "date": "25-08-2026"}
    )
    assert any("date" in p for p in malformed), "date must parse as YYYY-MM-DD"


REGISTRY_SCHEMA_PATH = REPO_ROOT / "docs" / "specs" / "spec-registry.schema.json"
REGISTRY_PATH = REPO_ROOT / "docs" / "specs" / "spec-registry.json"


@pytest.fixture(scope="module")
def registry_schema():
    return json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_registry_schema_admits_every_key_the_registry_uses(registry_schema, registry):
    """The fifth instance of the drift, and the first found in the registry itself.

    The entry schema set `additionalProperties: false` over spec/spec_ref/
    grandfathered, so adding `tier` and `reuse` made the canonical registry
    invalid against its own declared schema. Any consumer that validates would
    reject exactly the entries the reuse gate depends on.
    """
    entry_schema = registry_schema["properties"]["entries"]["additionalProperties"]
    declared = set(entry_schema.get("properties", {}))
    used = set()
    for entry in registry["entries"].values():
        used.update(entry.keys())
    assert used <= declared, f"registry uses undeclared keys: {sorted(used - declared)}"


def test_registry_schema_points_at_the_reuse_block_schema(registry_schema):
    entry_schema = registry_schema["properties"]["entries"]["additionalProperties"]
    reuse = entry_schema["properties"]["reuse"]
    assert "reuse-gate.schema.json" in json.dumps(reuse), (
        "the reuse block has its own schema; the registry should reference it "
        "rather than restate or ignore it"
    )


@pytest.mark.parametrize(
    "probe",
    ["not probed: unavailable", "pending", "done", "TBD", "", "   ", "n/a"],
)
def test_placeholder_probes_do_not_count_as_direct_probes(gate, probe):
    """Anti-gaming requires POSITIVE evidence, not the absence of one prefix.

    Counting any truthy string that does not literally start with `not_probed`
    meant `"probe": "done"` satisfied the tier-2 compose/build requirement.
    """
    entry = {
        "tier": 2,
        "reuse": {
            "capability": "c",
            "search_date": "2026-08-25",
            "candidates": [
                {"name": "thing", "truth_status": "Verified", "probe": probe}
            ],
            "verdict": "build",
            "irreducible_delta": "d",
            "reviewer": {
                "surfaces": ["groq", "mistral", "nvidia"],
                "families": ["gpt", "qwen", "deepseek", "llama"],
                "record": "docs/specs/reuse-gate.spec.md",
                "outcome": "APPROVED",
                "date": "2026-08-25",
            },
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("direct probe" in f for f in fails), f"{probe!r} must not count"


def test_a_positive_probe_counts(gate):
    entry = {
        "tier": 2,
        "reuse": {
            "capability": "c",
            "search_date": "2026-08-25",
            "candidates": [
                {
                    "name": "thing",
                    "truth_status": "Verified",
                    "probe": "probed: ran --check live 2026-08-25, fail-closed path verified",
                }
            ],
            "verdict": "build",
            "irreducible_delta": "d",
            "reviewer": {
                "surfaces": ["groq", "mistral", "nvidia"],
                "families": ["gpt", "qwen", "deepseek", "llama"],
                "record": "docs/specs/reuse-gate.spec.md",
                "outcome": "APPROVED",
                "date": "2026-08-25",
            },
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert not any("direct probe" in f for f in fails), fails


def test_a_structured_probe_satisfies_every_check_not_just_the_probe_rule(gate):
    """The probe rule accepting a shape the field rule rejects is not acceptance.

    `_is_direct_probe` was taught the documented object form while the generic
    candidate field check still required `probe` to be a string, so a structured
    probe satisfied neither the schema nor `--check`. The earlier test only
    asserted the absence of the 'direct probe' message and passed anyway; it was
    too narrow. Assert the WHOLE result.
    """
    entry = {
        "tier": 2,
        "reuse": {
            "capability": "c",
            "search_date": "2026-08-25",
            "candidates": [
                {
                    "name": "thing",
                    "truth_status": "Verified",
                    "probe": {
                        "status": "passed",
                        "detail": "ran it",
                        "date": "2026-08-25",
                    },
                }
            ],
            "verdict": "build",
            "irreducible_delta": "d",
            "reviewer": {
                "surfaces": ["groq", "mistral", "nvidia"],
                "families": ["gpt", "qwen", "deepseek", "llama"],
                "record": "docs/specs/reuse-gate.spec.md",
                "outcome": "APPROVED",
                "date": "2026-08-25",
            },
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert fails == [], fails


def test_a_malformed_structured_probe_is_still_rejected(gate):
    """Accepting the object shape must not mean accepting any object."""
    entry = {
        "tier": 1,
        "reuse": {
            "capability": "c",
            "search_date": "2026-08-25",
            "candidates": [
                {
                    "name": "thing",
                    "truth_status": "Verified",
                    "probe": {"status": "maybe", "detail": 7},
                }
            ],
            "verdict": "extend",
            "irreducible_delta": "d",
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("probe" in f for f in fails), fails


def test_a_structured_probe_counts(gate):
    entry = {
        "tier": 2,
        "reuse": {
            "capability": "c",
            "search_date": "2026-08-25",
            "candidates": [
                {
                    "name": "thing",
                    "truth_status": "Verified",
                    "probe": {
                        "status": "passed",
                        "detail": "ran it",
                        "date": "2026-08-25",
                    },
                }
            ],
            "verdict": "build",
            "irreducible_delta": "d",
            "reviewer": {
                "surfaces": ["groq", "mistral", "nvidia"],
                "families": ["gpt", "qwen", "deepseek", "llama"],
                "record": "docs/specs/reuse-gate.spec.md",
                "outcome": "APPROVED",
                "date": "2026-08-25",
            },
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert not any("direct probe" in f for f in fails), fails
