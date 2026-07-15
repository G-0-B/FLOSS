from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from packages.salvage_spine.models import (
    CapsuleRecord,
    PlaneEligibility,
    PlaneId,
    PlaneRecord,
    PlaneSensitivity,
    PlaneVerification,
    ResultStatus,
    canonical_json_bytes,
)

OPAQUE_PLANE_IDS = (
    PlaneId.REMOTE_MAIN,
    PlaneId.REMOTE_PR,
    PlaneId.LOCAL_HISTORY,
    PlaneId.LOCAL_INDEX,
)
LOCAL_MUTABLE_PLANE_IDS = (PlaneId.LOCAL_TRACKED, PlaneId.LOCAL_UNTRACKED)


def opaque_plane(plane_id: PlaneId, index: int = 0) -> PlaneRecord:
    return PlaneRecord(
        plane_id=plane_id,
        subject_id=f"subject-{plane_id.value}",
        digest=f"{index:x}" * 64,
        sensitivity=PlaneSensitivity.OPAQUE_SENSITIVE,
        eligibility=PlaneEligibility.INELIGIBLE,
        verification=PlaneVerification.OPAQUE_PRESERVED,
        status=ResultStatus.BLOCKED,
    )


def ordinary_local_plane(plane_id: PlaneId, index: int = 4) -> PlaneRecord:
    return PlaneRecord(
        plane_id=plane_id,
        subject_id=f"subject-{plane_id.value}",
        digest=f"{index:x}" * 64,
        sensitivity=PlaneSensitivity.ORDINARY,
        eligibility=PlaneEligibility.ELIGIBLE,
        verification=PlaneVerification.BYTE_EQUALITY,
        status=ResultStatus.PASS,
    )


def redacted_local_plane(plane_id: PlaneId, index: int = 4) -> PlaneRecord:
    return PlaneRecord(
        plane_id=plane_id,
        subject_id=f"subject-{plane_id.value}",
        digest=f"{index:x}" * 64,
        sensitivity=PlaneSensitivity.REDACTED,
        eligibility=PlaneEligibility.INELIGIBLE,
        verification=PlaneVerification.UNVERIFIABLE_REDACTED,
        status=ResultStatus.BLOCKED,
    )


def valid_planes() -> tuple[PlaneRecord, ...]:
    return tuple(
        (
            opaque_plane(plane_id, index)
            if plane_id in OPAQUE_PLANE_IDS
            else ordinary_local_plane(plane_id, index)
        )
        for index, plane_id in enumerate(PlaneId)
    )


def capsule_schema() -> dict[str, object]:
    spec_root = Path(__file__).resolve().parents[3] / "docs" / "superpowers" / "specs"
    return json.loads(
        (spec_root / "pr38-capsule.schema.json").read_text(encoding="utf-8")
    )


def test_plane_record_is_immutable_and_json_is_deterministic():
    record = PlaneRecord(
        plane_id=PlaneId.REMOTE_MAIN,
        subject_id="abc",
        digest="0" * 64,
        sensitivity=PlaneSensitivity.OPAQUE_SENSITIVE,
        eligibility=PlaneEligibility.INELIGIBLE,
        verification=PlaneVerification.OPAQUE_PRESERVED,
        status=ResultStatus.BLOCKED,
    )

    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}\n'
    with pytest.raises(FrozenInstanceError):
        record.digest = "1" * 64


def test_contract_enums_cover_scoped_values():
    assert [status.value for status in ResultStatus] == [
        "PASS",
        "FAIL",
        "BLOCKED",
        "SKIPPED",
    ]
    assert [plane.value for plane in PlaneId] == [
        "remote-main",
        "remote-pr38",
        "local-history",
        "local-index",
        "local-tracked",
        "local-untracked-ignored",
    ]
    assert [value.value for value in PlaneSensitivity] == [
        "ordinary",
        "opaque-sensitive",
        "redacted",
    ]
    assert [value.value for value in PlaneEligibility] == [
        "eligible",
        "ineligible",
    ]
    assert [value.value for value in PlaneVerification] == [
        "byte-equality",
        "opaque-preserved",
        "unverifiable-redacted",
    ]


def test_sensitive_plane_disposition_is_explicit_and_blocked():
    record = PlaneRecord(
        plane_id=PlaneId.LOCAL_INDEX,
        subject_id="index-subject",
        digest="a" * 64,
        sensitivity=PlaneSensitivity.OPAQUE_SENSITIVE,
        eligibility=PlaneEligibility.INELIGIBLE,
        verification=PlaneVerification.OPAQUE_PRESERVED,
        status=ResultStatus.BLOCKED,
    )

    encoded = canonical_json_bytes(record)
    assert b'"sensitivity":"opaque-sensitive"' in encoded
    assert b'"eligibility":"ineligible"' in encoded
    assert b'"verification":"opaque-preserved"' in encoded
    assert encoded.endswith(
        b'"subject_id":"index-subject","verification":"opaque-preserved"}\n'
    )


def test_sensitive_or_unverifiable_plane_cannot_claim_pass_or_eligibility():
    with pytest.raises(ValueError, match="inherently opaque"):
        PlaneRecord(
            plane_id=PlaneId.LOCAL_HISTORY,
            subject_id="history",
            digest="b" * 64,
            sensitivity=PlaneSensitivity.OPAQUE_SENSITIVE,
            eligibility=PlaneEligibility.ELIGIBLE,
            verification=PlaneVerification.OPAQUE_PRESERVED,
            status=ResultStatus.PASS,
        )

    with pytest.raises(ValueError, match="local mutable planes"):
        PlaneRecord(
            plane_id=PlaneId.LOCAL_UNTRACKED,
            subject_id="redacted",
            digest="c" * 64,
            sensitivity=PlaneSensitivity.REDACTED,
            eligibility=PlaneEligibility.ELIGIBLE,
            verification=PlaneVerification.UNVERIFIABLE_REDACTED,
            status=ResultStatus.BLOCKED,
        )


def test_plane_record_requires_explicit_disposition() -> None:
    with pytest.raises(TypeError, match="missing 4 required positional arguments"):
        PlaneRecord(
            plane_id=PlaneId.LOCAL_HISTORY,
            subject_id="history",
            digest="d" * 64,
        )


def test_plane_record_rejects_raw_string_plane_id_bypass() -> None:
    with pytest.raises(ValueError, match="plane_id must be a PlaneId"):
        PlaneRecord(
            plane_id="local-tracked",  # type: ignore[arg-type]
            subject_id="raw-plane-id",
            digest="f" * 64,
            sensitivity=PlaneSensitivity.ORDINARY,
            eligibility=PlaneEligibility.ELIGIBLE,
            verification=PlaneVerification.BYTE_EQUALITY,
            status=ResultStatus.PASS,
        )


@pytest.mark.parametrize("plane_id", OPAQUE_PLANE_IDS)
def test_inherently_opaque_plane_rejects_ordinary_pass(plane_id: PlaneId) -> None:
    with pytest.raises(ValueError, match="inherently opaque"):
        ordinary_local_plane(plane_id)


@pytest.mark.parametrize("plane_id", LOCAL_MUTABLE_PLANE_IDS)
def test_local_mutable_plane_allows_only_complete_safe_dispositions(
    plane_id: PlaneId,
) -> None:
    assert ordinary_local_plane(plane_id).status is ResultStatus.PASS
    assert redacted_local_plane(plane_id).status is ResultStatus.BLOCKED

    with pytest.raises(ValueError, match="local mutable planes"):
        opaque_plane(plane_id)

    with pytest.raises(ValueError, match="local mutable planes"):
        PlaneRecord(
            plane_id=plane_id,
            subject_id="mixed",
            digest="e" * 64,
            sensitivity=PlaneSensitivity.REDACTED,
            eligibility=PlaneEligibility.ELIGIBLE,
            verification=PlaneVerification.UNVERIFIABLE_REDACTED,
            status=ResultStatus.PASS,
        )


def test_capsule_record_serializes_nested_enums_deterministically():
    record = CapsuleRecord(
        schema_version="1.0.0",
        state_id="state-1",
        repository="C:/repo",
        captured_at="2026-07-14T00:00:00Z",
        planes=valid_planes(),
        exclusions=("secret.env",),
        status=ResultStatus.BLOCKED,
    )

    assert canonical_json_bytes(record).endswith(b'"status":"BLOCKED"}\n')
    with pytest.raises(FrozenInstanceError):
        record.state_id = "state-2"


def test_capsule_record_cannot_pass_with_blocked_or_ineligible_plane() -> None:
    with pytest.raises(ValueError, match="PASS requires every plane"):
        CapsuleRecord(
            schema_version="1.0.0",
            state_id="unsafe-pass",
            repository="C:/repo",
            captured_at="2026-07-14T00:00:00Z",
            planes=valid_planes(),
            exclusions=(),
            status=ResultStatus.PASS,
        )


def test_capsule_record_rejects_raw_string_status_bypass() -> None:
    with pytest.raises(ValueError, match="status must be a ResultStatus"):
        CapsuleRecord(
            schema_version="1.0.0",
            state_id="raw-pass",
            repository="C:/repo",
            captured_at="2026-07-14T00:00:00Z",
            planes=valid_planes(),
            exclusions=(),
            status="PASS",  # type: ignore[arg-type]
        )


def test_canonical_capture_capsule_validates_against_schema() -> None:
    record = CapsuleRecord(
        schema_version="1.0.0",
        state_id="captured-state",
        repository="C:/repo",
        captured_at="2026-07-14T00:00:00Z",
        planes=valid_planes(),
        exclusions=(),
        status=ResultStatus.BLOCKED,
    )
    schema = capsule_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    validator.validate(json.loads(canonical_json_bytes(record)))


def test_schema_rejects_inconsistent_plane_and_aggregate_dispositions() -> None:
    record = CapsuleRecord(
        schema_version="1.0.0",
        state_id="captured-state",
        repository="C:/repo",
        captured_at="2026-07-14T00:00:00Z",
        planes=valid_planes(),
        exclusions=(),
        status=ResultStatus.BLOCKED,
    )
    serialized = json.loads(canonical_json_bytes(record))
    validator = Draft202012Validator(capsule_schema(), format_checker=FormatChecker())

    serialized["planes"][0].update(
        {
            "sensitivity": "ordinary",
            "eligibility": "eligible",
            "verification": "byte-equality",
            "status": "PASS",
        }
    )
    with pytest.raises(ValidationError):
        validator.validate(serialized)

    serialized = json.loads(canonical_json_bytes(record))
    serialized["planes"][4].update(
        {
            "sensitivity": "redacted",
            "eligibility": "eligible",
            "verification": "unverifiable-redacted",
            "status": "BLOCKED",
        }
    )
    with pytest.raises(ValidationError):
        validator.validate(serialized)

    serialized = json.loads(canonical_json_bytes(record))
    del serialized["planes"][5]["verification"]
    with pytest.raises(ValidationError):
        validator.validate(serialized)

    serialized = json.loads(canonical_json_bytes(record))
    serialized["status"] = "PASS"
    with pytest.raises(ValidationError):
        validator.validate(serialized)


def test_capsule_record_rejects_missing_plane():
    with pytest.raises(ValueError, match="exactly one record for every PlaneId"):
        CapsuleRecord(
            schema_version="1.0.0",
            state_id="state-missing",
            repository="C:/repo",
            captured_at="2026-07-14T00:00:00Z",
            planes=valid_planes()[:-1],
            exclusions=(),
            status=ResultStatus.FAIL,
        )


def test_capsule_record_rejects_duplicate_plane():
    planes = valid_planes()
    duplicate = planes[:-1] + (planes[0],)

    with pytest.raises(ValueError, match="exactly one record for every PlaneId"):
        CapsuleRecord(
            schema_version="1.0.0",
            state_id="state-duplicate",
            repository="C:/repo",
            captured_at="2026-07-14T00:00:00Z",
            planes=duplicate,
            exclusions=(),
            status=ResultStatus.FAIL,
        )


def test_contract_schemas_are_strict_and_encode_state_rules():
    spec_root = Path(__file__).resolve().parents[3] / "docs" / "superpowers" / "specs"
    capsule = capsule_schema()
    manifest = json.loads(
        (spec_root / "pr38-salvage-manifest.schema.json").read_text(encoding="utf-8")
    )
    checkpoint = json.loads(
        (spec_root / "pr38-checkpoint.schema.json").read_text(encoding="utf-8")
    )

    assert capsule["$schema"].endswith("2020-12/schema")
    assert capsule["additionalProperties"] is False
    assert len(capsule["properties"]["planes"]["allOf"]) == 6
    assert set(capsule["$defs"]["planeRecord"]["required"]) == {
        "plane_id",
        "subject_id",
        "digest",
        "sensitivity",
        "eligibility",
        "verification",
        "status",
    }
    assert manifest["additionalProperties"] is False
    assert len(manifest["$defs"]["item"]["allOf"]) == 3
    assert manifest["$defs"]["nullableOid"]["pattern"] == (
        "^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
    )
    assert manifest["$defs"]["item"]["allOf"][2]["else"] == {
        "properties": {"replacement_item_id": {"type": "null"}}
    }
    assert checkpoint["additionalProperties"] is False
    assert len(checkpoint["allOf"]) == 2
    assert (
        checkpoint["properties"]["input_shas"]["additionalProperties"]["pattern"]
        == "^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
    )
