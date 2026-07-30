"""Regression contract for provenance-packet validation eval fixtures."""

import base64
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from packages.activity_log.provenance import _public_key_from_aid


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "evals" / "provenance_packet_validation"


def load_rows() -> list[dict]:
    """Load the ordered development and heldout evaluation rows."""
    rows = []
    for split in ("dev", "heldout"):
        path = EVAL_DIR / f"{split}.jsonl"
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())
    return rows


def test_splits_have_expected_sizes_and_unique_ids() -> None:
    dev_rows = (EVAL_DIR / "dev.jsonl").read_text(encoding="utf-8").splitlines()
    heldout_rows = (EVAL_DIR / "heldout.jsonl").read_text(encoding="utf-8").splitlines()
    rows = load_rows()

    assert len(dev_rows) == 20
    assert len(heldout_rows) == 10
    assert len({row["id"] for row in rows}) == 30


def test_every_packet_satisfies_the_provenance_schema_or_its_intended_schema_golden() -> None:
    schema = json.loads(
        (ROOT / "docs" / "specs" / "provenance-packet.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = Draft202012Validator(schema)

    schema_defect_by_top_level_field = {
        "v": "E-V-SHAPE",
        "t": "E-T-NOT-PROV",
        "d": "E-D-SHAPE",
        "i": "E-I-SHAPE",
        "sigs": "E-SIG-SHAPE",
        "a": "E-PAYLOAD-MISSING-FIELD",
    }

    for row in load_rows():
        errors = sorted(validator.iter_errors(row["input"]["packet"]), key=str)
        for error in errors:
            field = next(iter(error.absolute_path), None)
            expected_defect = schema_defect_by_top_level_field.get(field)
            assert expected_defect in row["golden"]["defects"], (
                f"{row['id']}: unexpected schema error {error.message}"
            )


def test_artifact_hashes_are_deterministic_lowercase_sha256() -> None:
    for row in load_rows():
        artifact_number = 0
        for payload in row["input"]["packet"]["a"]:
            for artifact in payload["artifact_refs"]:
                artifact_number += 1
                expected = hashlib.sha256(
                    f"FLOSS:provenance-eval:{row['id']}:artifact:{artifact_number}".encode(
                        "utf-8"
                    )
                ).hexdigest()
                assert artifact["sha256"] == expected


def test_crypto_facts_are_booleans() -> None:
    for row in load_rows():
        for fact in row["input"]["crypto_facts"].values():
            assert type(fact) is bool, row["id"]


def test_artifact_mismatch_goldens_exactly_match_false_facts() -> None:
    for row in load_rows():
        expects_mismatch = "E-ARTIFACT-HASH-MISMATCH" in row["golden"]["defects"]
        assert expects_mismatch is (
            row["input"]["crypto_facts"]["artifact_hashes_match_workspace"] is False
        ), row["id"]


def test_ppv_dev_007_accepts_a_nontransferable_signing_aid() -> None:
    row = next(row for row in load_rows() if row["id"] == "ppv-dev-007")
    aid = row["input"]["packet"]["i"]

    assert row["golden"] == {"status": "valid", "defects": ["PPV-OK"]}
    assert "valid non-transferable signing AID" in row["rationale"]
    assert bytes(_public_key_from_aid(aid)) == base64.urlsafe_b64decode(aid[1:] + "=")


def test_rubric_documents_the_db_aid_contract_and_oracle_facts() -> None:
    rubric = json.loads((EVAL_DIR / "rubric.json").read_text(encoding="utf-8"))

    assert "^[DB][A-Za-z0-9_-]{43}$" in rubric["defect_codes"]["E-I-SHAPE"]
    assert "counterfactual oracle" in rubric["crypto_facts_contract"]


def test_prose_spec_documents_both_valid_signing_aid_prefixes() -> None:
    spec_lines = (ROOT / "docs" / "specs" / "provenance-packet.spec.md").read_text(
        encoding="utf-8"
    ).splitlines()
    aid_row = next(line for line in spec_lines if line.startswith("| `i` |"))

    assert (
        aid_row
        == "| `i` | string | `D` or `B` + 43-char base64url Ed25519 verify key; "
        "`D` is transferable and `B` is non-transferable, and both are valid "
        "signing identifiers in v1.4. |"
    )
