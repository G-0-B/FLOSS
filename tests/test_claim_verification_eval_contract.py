"""Regression contract for claim-verification eval fixtures."""

import json
from pathlib import Path

from packages.orchestrator.claim_schema import (
    BlastRadius,
    Claim,
    EvidenceRef,
    ProposalType,
    TruthStatus,
)

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "claim_verification"


def load_rows() -> list[dict]:
    """Load the ordered development and heldout evaluation rows."""
    rows = []
    for split in ("dev", "heldout"):
        path = EVAL_DIR / f"{split}.jsonl"
        rows.extend(
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()
        )
    return rows


def claim_from_fixture(data: dict) -> Claim:
    """Build a production Claim from one fixture's wire-shape fields."""
    return Claim(
        proposer=data["proposer"],
        proposal_type=ProposalType(data["proposal_type"]),
        summary=data["summary"],
        body=data["body"],
        blast_radius=BlastRadius(data["blast_radius"]),
        evidence=[EvidenceRef(**evidence) for evidence in data["evidence"]],
        truth_status=TruthStatus(data["truth_status"]),
    )


def test_splits_have_expected_sizes_and_unique_ids() -> None:
    dev_rows = (EVAL_DIR / "dev.jsonl").read_text(encoding="utf-8").splitlines()
    heldout_rows = (EVAL_DIR / "heldout.jsonl").read_text(encoding="utf-8").splitlines()
    rows = load_rows()

    assert len(dev_rows) == 20
    assert len(heldout_rows) == 10
    assert len({row["id"] for row in rows}) == 30


def test_clean_goldens_are_valid_production_claim_submissions() -> None:
    for row in load_rows():
        if row["golden"]["defects"] == ["D-NONE"]:
            claim_from_fixture(row["input"]["claim"]).validate()


def test_certainty_guard_removal_is_an_invariant_violation() -> None:
    row = next(row for row in load_rows() if row["id"] == "cv-ho-002")

    assert "CERTAINTY_LIMIT" in row["input"]["claim"]["body"]
    assert set(row["golden"]["defects"]) == {
        "D-GOVERNED-NO-PACKET",
        "D-INVARIANT-VIOLATION",
    }


def test_goldens_only_use_declared_defects_and_d_none_stands_alone() -> None:
    rubric = json.loads((EVAL_DIR / "rubric.json").read_text(encoding="utf-8"))
    declared = set(rubric["defect_codes"])

    for row in load_rows():
        defects = row["golden"]["defects"]
        assert set(defects) <= declared, row["id"]
        if "D-NONE" in defects:
            assert defects == ["D-NONE"], row["id"]


def test_truth_status_goldens_match_the_submission_contract() -> None:
    for row in load_rows():
        truth_status = row["input"]["claim"]["truth_status"]
        defects = set(row["golden"]["defects"])

        assert ("D-TRUTH-OVERCLAIM" in defects) is (
            truth_status != TruthStatus.UNVERIFIED.value
        ), row["id"]


def test_rubric_names_the_submission_and_certainty_invariants() -> None:
    rubric = json.loads((EVAL_DIR / "rubric.json").read_text(encoding="utf-8"))

    assert "Unverified on submission" in rubric["defect_codes"]["D-TRUTH-OVERCLAIM"]
    assert "CERTAINTY_LIMIT" in rubric["defect_codes"]["D-INVARIANT-VIOLATION"]
