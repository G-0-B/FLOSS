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


def _tier2_entry(probe):
    return {
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


@pytest.mark.parametrize(
    "probe",
    [
        {"status": "passed"},
        {"status": "passed", "detail": ""},
        {"status": "passed", "detail": "   ", "date": "2026-08-25"},
        {"status": "passed", "detail": "ran it"},
        {"status": "passed", "detail": "ran it", "date": "not-a-date"},
        "probed:",
        "probed:    ",
        "PROBED:",
    ],
)
def test_a_passed_probe_without_evidence_does_not_count(gate, probe):
    """`status: passed` is an assertion, not evidence of one.

    Accepting the object form left `detail` and `date` optional, so
    `{"status": "passed"}` discharged the tier-2 anti-gaming obligation without
    saying what was exercised or when. The string form had the same hole: the
    bare prefix `probed:` carried no payload.

    This is the same defect as the placeholder probes, the stringified reviewer
    metadata, and the prose reviewer before them — a check satisfied by naming
    the conclusion rather than showing the work.
    """
    fails, _warns = gate._reuse_problems("x.md", _tier2_entry(probe))
    assert any("direct probe" in f for f in fails), f"{probe!r} must not count"


@pytest.mark.parametrize(
    "probe",
    [
        {"status": "passed", "detail": "ran --check live", "date": "2026-08-25"},
        "probed: ran --check live 2026-08-25, fail-closed path verified",
    ],
)
def test_a_probe_with_evidence_counts(gate, probe):
    fails, _warns = gate._reuse_problems("x.md", _tier2_entry(probe))
    assert fails == [], fails


def test_probe_object_schema_demands_what_the_gate_demands(gate, schema):
    """Schema and enforcement must agree on what a passed probe has to carry.

    Every previous instance of this drift was found in review rather than here.
    """
    probe = schema["properties"]["candidates"]["items"]["properties"]["probe"]
    obj = next(form for form in probe["oneOf"] if form.get("type") == "object")
    assert set(obj["required"]) == {"status", "detail", "date"}
    assert obj["properties"]["detail"]["minLength"] >= 1
    assert obj["properties"]["date"]["format"] == "date"
    assert set(obj["properties"]["status"]["enum"]) == set(gate.PROBE_STATUSES)


@pytest.mark.parametrize(
    "bad_date",
    [20260825, "20260825", "2026-8-25", "2026/08/25", " 2026-08-25 ", None, True],
)
def test_every_date_field_rejects_untyped_or_compact_forms(gate, bad_date):
    """One helper, three fields, because this is the fourth date defect here.

    `str(20260825)` is `"20260825"`, which `date.fromisoformat()` happily
    accepts as 2026-08-25 — so a JSON number, and the compact string form,
    both cleared a check advertising `YYYY-MM-DD`. The same stringify-then-parse
    shape was fixed in `reviewer.date` and `probe.date` separately; fixing it a
    third time in isolation would have guaranteed a fourth.
    """
    assert gate._iso_date_problems("x.md: field", bad_date), f"{bad_date!r} must fail"


def test_a_dashed_iso_date_passes(gate):
    assert gate._iso_date_problems("x.md: field", "2026-08-25") == []


@pytest.mark.parametrize("bad_date", [20260825, "20260825", "2026-8-25"])
def test_reuse_search_date_uses_the_shared_date_rule(gate, bad_date):
    entry = {
        "tier": 1,
        "reuse": {
            "capability": "c",
            "search_date": bad_date,
            "candidates": [{"name": "n", "truth_status": "Verified"}],
            "verdict": "extend",
            "irreducible_delta": "d",
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("search_date" in f for f in fails), fails


def test_registration_guidance_is_a_command_that_actually_works(gate, tmp_path):
    """`--add` requires `--tier`, so guidance omitting it sent operators in circles."""
    note = gate.advisory_note("FLOSS/scripts/spec_gate.py")
    guidance = note or gate._registration_hint("FLOSS/scripts/unregistered_example.py")
    assert "--tier" in guidance, guidance


@pytest.mark.parametrize(
    "window", ["999999", 999999.9, True, None, "soon", [], {"days": 5}]
)
def test_evidence_window_must_be_a_real_integer(gate, window):
    """A coerced window silently widens the freshness gate, or crashes the audit.

    `int("999999")` and `int(999999.9)` both succeed, so a schema-invalid value
    let arbitrarily old prior art pass `--check`; `int("soon")` raised ValueError
    out of the audit instead of producing a reuse violation. Same untyped-input
    class as the dates and the probe fields.
    """
    entry = {
        "tier": 1,
        "reuse": {
            "capability": "c",
            "search_date": "2020-01-01",
            "candidates": [{"name": "n", "truth_status": "Verified"}],
            "verdict": "extend",
            "irreducible_delta": "d",
            "evidence_window_days": window,
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("evidence_window_days" in f for f in fails), fails


def test_a_valid_window_still_governs_freshness(gate):
    entry = {
        "tier": 1,
        "reuse": {
            "capability": "c",
            "search_date": "2020-01-01",
            "candidates": [{"name": "n", "truth_status": "Verified"}],
            "verdict": "extend",
            "irreducible_delta": "d",
            "evidence_window_days": 30,
        },
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("stale" in f for f in fails), fails


# ---------------------------------------------------------------------------
# The gate must not be openable by the field that decides whether it applies.
# ---------------------------------------------------------------------------


def _tier_entry(**overrides) -> dict:
    entry = {
        "tier": 2,
        "reuse": {
            "capability": "c",
            "search_date": "2026-08-25",
            "candidates": [
                {"name": "thing", "truth_status": "Verified", "probe": "probed: ran it"}
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
    entry.update(overrides)
    return entry


@pytest.mark.parametrize("tier", ["2", "1", 3, 0, -1, 2.0, True, None])
def test_a_malformed_tier_fails_instead_of_exempting(gate, tier):
    """A typo in `tier` must not waive every reuse, reviewer and probe check.

    `if tier not in (1, 2): return [], []` treated a hand-edited `"2"` or `3`
    exactly like an absent tier, so a schema-invalid value silently exempted a
    new architecture artifact from a fail-closed gate.
    """
    fails, _warns = gate._reuse_problems("x.md", {"tier": tier})
    assert fails, f"tier {tier!r} was exempted rather than rejected"
    assert "tier" in fails[0]


def test_an_absent_tier_is_still_the_grandfather_exemption(gate):
    """100 of the 104 registry entries predate ADR-18 and carry no tier."""
    assert gate._reuse_problems("x.md", {}) == ([], [])
    assert gate._reuse_problems("x.md", {"spec": "something"}) == ([], [])


@pytest.mark.parametrize("emergency", ["false", "true", "no", 1, 0, [], {}])
def test_a_non_boolean_emergency_does_not_waive_the_reuse_block(gate, emergency):
    """`entry.get("emergency")` was a truthiness test.

    The string "false" -- schema-invalid, and the most likely way a human writes
    it wrong -- read as an active emergency and downgraded a wholly missing
    reuse block to a warning that `--check` exits 0 on.
    """
    fails, warns = gate._reuse_problems("x.md", {"tier": 2, "emergency": emergency})
    assert fails, f"emergency={emergency!r} waived the gate"
    assert not warns


def test_a_real_emergency_still_downgrades_to_a_warning(gate):
    fails, warns = gate._reuse_problems("x.md", {"tier": 2, "emergency": True})
    assert fails == []
    assert warns and "retrospective" in warns[0]


def test_emergency_false_is_not_an_emergency(gate):
    fails, warns = gate._reuse_problems("x.md", {"tier": 2, "emergency": False})
    assert fails == ["x.md: tier 2 artifact has no reuse block"]
    assert warns == []


# ---------------------------------------------------------------------------
# Evidence cannot predate the event it records.
# ---------------------------------------------------------------------------


def test_a_future_reviewer_date_is_rejected(gate):
    entry = _tier_entry()
    entry["reuse"]["reviewer"]["date"] = "2099-01-01"
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("future" in f for f in fails), fails


def test_a_future_probe_date_is_rejected(gate):
    entry = _tier_entry()
    entry["reuse"]["candidates"][0]["probe"] = {
        "status": "passed",
        "detail": "ran it",
        "date": "2099-01-01",
    }
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("future" in f for f in fails), fails


def test_search_date_keeps_its_own_future_message(gate):
    """search_date opts out of the shared rule only to keep a richer message."""
    entry = _tier_entry()
    entry["reuse"]["search_date"] = "2099-01-01"
    fails, _warns = gate._reuse_problems("x.md", entry)
    assert any("cannot predate its own search" in f for f in fails), fails


def test_every_date_field_shares_one_future_rule(gate):
    """Generic, not per-instance: the helper is the single place it is enforced.

    Three date fields existed and two of them accepted 2099. Asserting the
    helper directly means a fourth date field added later inherits the rule
    instead of needing its own test.
    """
    assert gate._iso_date_problems("d", "2099-01-01")
    assert gate._iso_date_problems("d", "2020-01-01") == []
    assert gate._iso_date_problems("d", "2099-01-01", allow_future=True) == []


# ---------------------------------------------------------------------------
# The reviewer record must not be swappable after the review.
# ---------------------------------------------------------------------------


def test_a_record_can_be_pinned_to_its_content(gate, tmp_path, monkeypatch):
    """Existence was the only check, so a record could be replaced wholesale.

    An external audit named this exact shape on this project's own multi-model
    attribution: "an unsigned attestation by an unknown key". A pointer that
    resolves is not evidence that the thing it points at is what was reviewed.
    """
    record = REPO_ROOT / "docs" / "specs" / "reuse-gate.spec.md"
    digest = gate.record_digest(record)
    assert digest is not None and len(digest) == 64

    reviewer = {
        "surfaces": ["a", "b", "c"],
        "families": ["w", "x", "y", "z"],
        "record": "docs/specs/reuse-gate.spec.md",
        "record_sha256": digest,
        "outcome": "APPROVED",
        "date": "2026-08-26",
    }
    assert gate._reviewer_problems("x.md", reviewer) == []

    wrong = dict(reviewer)
    wrong["record_sha256"] = "0" * 64
    problems = gate._reviewer_problems("x.md", wrong)
    assert problems and "no longer matches" in problems[0]


def test_an_unpinned_record_is_unaffected(gate):
    """Fail-open by design.

    Tightening a validator against existing history without enumerating what
    breaks is the b0de2fe mistake, recorded as CF-1. Entries with no
    `record_sha256` keep working; new entries should pin.
    """
    reviewer = {
        "surfaces": ["a", "b", "c"],
        "families": ["w", "x", "y", "z"],
        "record": "docs/specs/reuse-gate.spec.md",
        "outcome": "APPROVED",
        "date": "2026-08-26",
    }
    assert gate._reviewer_problems("x.md", reviewer) == []


@pytest.mark.parametrize("bad", ["ABC", "z" * 64, 123, True, "0" * 63, ""])
def test_a_malformed_pin_is_rejected(gate, bad):
    reviewer = {
        "surfaces": ["a", "b", "c"],
        "families": ["w", "x", "y", "z"],
        "record": "docs/specs/reuse-gate.spec.md",
        "record_sha256": bad,
        "outcome": "APPROVED",
        "date": "2026-08-26",
    }
    problems = gate._reviewer_problems("x.md", reviewer)
    assert problems, f"{bad!r} was accepted as a digest"


def test_the_digest_is_line_ending_normalised(gate, tmp_path):
    """Or the pin would verify only on the machine that wrote it.

    `.gitattributes` declares `*.md text eol=lf`, so a Windows worktree file
    differs byte-for-byte from the blob git stores. CF-8 is exactly this failure
    one layer down: a published hash that verifies only for the author.
    """
    crlf = tmp_path / "crlf.md"
    lf = tmp_path / "lf.md"
    crlf.write_bytes(b"line one\r\nline two\r\n")
    lf.write_bytes(b"line one\nline two\n")

    assert gate.record_digest(crlf) == gate.record_digest(lf)


def test_an_unreadable_record_cannot_satisfy_a_pin(gate):
    reviewer = {
        "surfaces": ["a", "b", "c"],
        "families": ["w", "x", "y", "z"],
        "record": "docs/specs/does-not-exist.md",
        "record_sha256": "a" * 64,
        "outcome": "APPROVED",
        "date": "2026-08-26",
    }
    problems = gate._reviewer_problems("x.md", reviewer)
    assert any("could not be read" in p or "does not exist" in p for p in problems)


# --- ADR-18 coverage reporting -------------------------------------------
#
# Defect #5, found 2026-09-01 and the reason these tests exist: the gate is
# fail-closed *inside an opt-in scope*. An omitted tier is an exemption, so
# `SPEC-GATE OK` was compatible with the reuse gate firing on 9 of 109
# registered artifacts. Running the gate felt like compliance because nothing
# reported how little it had examined. A gate that prints a verdict without a
# coverage number is an unfalsifiable claim of compliance.


def test_reuse_coverage_counts_tiers_and_grandfathering(gate):
    entries = {
        "a.md": {"spec": "x", "tier": 1},
        "b.md": {"spec": "x", "tier": 2},
        "c.md": {"spec": "x"},
        "d.md": {"spec": "x", "grandfathered": "deadbeef"},
    }
    cov = gate.reuse_coverage(entries)
    assert cov["total"] == 4
    assert cov["tiered"] == 2
    assert cov["untiered"] == 2
    assert cov["untiered_not_grandfathered"] == 1
    assert cov["percent"] == 50


def test_reuse_coverage_is_empty_safe(gate):
    cov = gate.reuse_coverage({})
    assert cov["total"] == 0
    assert cov["tiered"] == 0
    assert cov["percent"] == 0


def test_reuse_coverage_matches_the_real_registry(gate):
    """The reported number must be derived, never a hand-maintained constant."""
    entries = gate.load_registry().get("entries", {})
    cov = gate.reuse_coverage(entries)
    expected_tiered = sum(1 for e in entries.values() if e.get("tier") in (1, 2))
    assert cov["tiered"] == expected_tiered
    assert cov["total"] == len(entries)
    assert cov["tiered"] + cov["untiered"] == cov["total"]


def test_check_reports_coverage_on_both_the_pass_and_fail_paths(gate, capsys):
    """A red gate still has to say how much it looked at.

    The early `return 1` for unregistered artifacts must not skip the coverage
    line -- a failing gate is exactly when its blind spots matter most.
    """
    gate.run_check()
    out = capsys.readouterr().out
    assert "SPEC-GATE COVERAGE:" in out
    coverage_line = next(
        line for line in out.splitlines() if line.startswith("SPEC-GATE COVERAGE:")
    )
    verdict_index = next(
        (
            i
            for i, line in enumerate(out.splitlines())
            if line.startswith("SPEC-GATE OK") or line.startswith("SPEC-GATE FAIL")
        ),
        None,
    )
    assert verdict_index is not None, "run_check printed no verdict"
    assert out.splitlines().index(coverage_line) < verdict_index


# --- R6: accepted-but-not-implemented is a third ungated class --------------
#
# spec_gate validates that evidence exists for artifacts that were BUILT.
# Nothing validates that artifacts get built for decisions that were ACCEPTED.
# ADR-20:589 lists six such promises, `filelock` adoption among them, accepted
# 2026-08-25 after a four-auditor meta-audit and still undone eight days later
# while the hand-rolled lock accrued review rounds. Invisible to every other
# gate by construction, so the gate here is: count them and print the number.


def test_deferred_promises_finds_accepted_but_not_implemented_headings(gate, tmp_path):
    adr = tmp_path / "adr"
    adr.mkdir()
    (adr / "ADR-90-thing.md").write_text(
        "# ADR-90\n\n### Accepted but not implemented here\n\nA, B, and C.\n",
        encoding="utf-8",
    )
    (adr / "ADR-91-other.md").write_text(
        "# ADR-91\n\n### Deferred (LATER)\n\nSomething.\n", encoding="utf-8"
    )
    (adr / "ADR-92-clean.md").write_text(
        "# ADR-92\n\n## Decision\n\nDone and shipped.\n", encoding="utf-8"
    )
    found = dict(gate.deferred_promises(adr))
    assert "ADR-90-thing.md" in found
    assert "ADR-91-other.md" in found
    assert "ADR-92-clean.md" not in found


def test_deferred_promises_is_empty_safe(gate, tmp_path):
    assert gate.deferred_promises(tmp_path / "nope") == []


def test_deferred_promises_finds_the_real_adr_20_section(gate):
    """The instance this gate exists for must be found by it."""
    found = dict(gate.deferred_promises())
    assert "ADR-20-provenance-validator-reconciliation.md" in found


def test_check_reports_ungated_promises_alongside_coverage(gate, capsys):
    gate.run_check()
    out = capsys.readouterr().out
    assert "SPEC-GATE PROMISES:" in out


# --- R2: an omitted tier stops being an exemption ---------------------------
#
# Measured 2026-09-01: 109 registered artifacts, 9 tiered, 100 untiered, of
# which 43 were explicitly grandfathered and 57 were simply never decided.
# spec_gate's own message said the rule out loud -- "an omitted tier is an
# exemption, not a default" -- so the reuse gate reached 8% of the registry
# while reporting OK. Absence of a decision now IS the failure; the 57 carry an
# explicit `tier_exempt` reason recording that they were never assessed, which
# is the honest label rather than a claim that they are fine.


def _entry(**kw):
    base = {"spec": "x"}
    base.update(kw)
    return base


def test_an_entry_with_no_tier_decision_at_all_is_a_problem(gate):
    problems = gate.tier_decision_problems({"a.md": _entry()})
    assert len(problems) == 1
    assert "a.md" in problems[0]


def test_a_tier_satisfies_the_decision(gate):
    assert gate.tier_decision_problems({"a.md": _entry(tier=1)}) == []
    assert gate.tier_decision_problems({"a.md": _entry(tier=2)}) == []


def test_an_explicit_exemption_reason_satisfies_the_decision(gate):
    entries = {"a.md": _entry(tier_exempt="not architecture-class; docs only")}
    assert gate.tier_decision_problems(entries) == []


def test_an_empty_exemption_reason_does_not_satisfy_it(gate):
    """`tier_exempt: ""` is an omitted tier wearing a hat."""
    assert len(gate.tier_decision_problems({"a.md": _entry(tier_exempt="")})) == 1
    assert len(gate.tier_decision_problems({"a.md": _entry(tier_exempt=True)})) == 1


def test_grandfathering_still_satisfies_the_decision(gate):
    entries = {"a.md": _entry(grandfathered="deadbeef")}
    assert gate.tier_decision_problems(entries) == []


def test_the_real_registry_has_no_undecided_entries_left(gate):
    """The 2026-09-02 sweep must have covered all 57, not most of them."""
    entries = gate.load_registry().get("entries", {})
    assert gate.tier_decision_problems(entries) == []


def test_check_fails_closed_on_an_undecided_entry(gate, monkeypatch, capsys):
    real = gate.load_registry()
    poisoned = dict(real)
    poisoned["entries"] = dict(real.get("entries", {}))
    poisoned["entries"]["docs/specs/invented-undecided.md"] = {"spec": "x"}
    monkeypatch.setattr(gate, "load_registry", lambda: poisoned)
    assert gate.run_check() == 1
    assert "invented-undecided.md" in capsys.readouterr().out
