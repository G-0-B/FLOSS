from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from packages.salvage_spine.models import (
    CapsuleRecord,
    PlaneId,
    PlaneRecord,
    ResultStatus,
    canonical_json_bytes,
)


def valid_planes():
    return tuple(
        PlaneRecord(
            plane_id=plane_id,
            subject_id=f"subject-{plane_id.value}",
            digest=f"{index:x}" * 64,
        )
        for index, plane_id in enumerate(PlaneId)
    )


def test_plane_record_is_immutable_and_json_is_deterministic():
    record = PlaneRecord(
        plane_id=PlaneId.REMOTE_MAIN,
        subject_id="abc",
        digest="0" * 64,
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


def test_capsule_record_serializes_nested_enums_deterministically():
    record = CapsuleRecord(
        schema_version="1.0.0",
        state_id="state-1",
        repository="C:/repo",
        captured_at="2026-07-14T00:00:00Z",
        planes=valid_planes(),
        exclusions=("secret.env",),
        status=ResultStatus.PASS,
    )

    assert canonical_json_bytes(record).endswith(b'"status":"PASS"}\n')
    with pytest.raises(FrozenInstanceError):
        record.state_id = "state-2"


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
    capsule = json.loads((spec_root / "pr38-capsule.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads(
        (spec_root / "pr38-salvage-manifest.schema.json").read_text(encoding="utf-8")
    )
    checkpoint = json.loads(
        (spec_root / "pr38-checkpoint.schema.json").read_text(encoding="utf-8")
    )

    assert capsule["$schema"].endswith("2020-12/schema")
    assert capsule["additionalProperties"] is False
    assert len(capsule["properties"]["planes"]["allOf"]) == 6
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
    assert checkpoint["properties"]["input_shas"]["additionalProperties"][
        "pattern"
    ] == "^(?:[0-9a-f]{40}|[0-9a-f]{64})$"
