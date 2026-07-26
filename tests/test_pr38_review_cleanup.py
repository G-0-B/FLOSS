"""Regression coverage for PR38 Task 1 review corrections."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import jsonschema
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "docs" / "specs" / "yumeichan-watch-capabilities.schema.json"


def valid_capability() -> dict[str, object]:
    return {
        "capability_id": "uhCAk",
        "grantor_pubkey": "grantor-key",
        "grantee_pubkey": "grantee-key",
        "capability_type": "AFFECTIVE_MEMORY_READ",
        "analog_threshold_bounds": [-0.5, 0.8],
        "ttl_seconds": 60,
        "issued_at": "2026-07-26T00:00:00Z",
        "proof": {
            "algorithm": "Ed25519",
            "canonicalization": "RFC8785",
            "payload_digest": "a" * 64,
            "signature": "base64-ed25519-signature",
        },
    }


def test_capability_schema_requires_ed25519_proof() -> None:
    capability = valid_capability()
    capability.pop("proof")

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(capability, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda capability: capability.update({"unexpected": True}),
        lambda capability: capability["proof"].update({"unexpected": True}),
    ],
)
def test_capability_schema_rejects_unknown_top_level_and_nested_fields(mutate) -> None:
    capability = valid_capability()
    mutate(capability)

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(capability, json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def test_semantic_validator_accepts_ordered_threshold_bounds() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    validate_capability(valid_capability())


def test_semantic_validator_rejects_inverted_threshold_bounds() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    capability = valid_capability()
    capability["analog_threshold_bounds"] = [0.8, -0.5]

    with pytest.raises(jsonschema.ValidationError, match="minimum must not exceed maximum"):
        validate_capability(capability)


def test_uppercase_togetherai_key_is_preserved() -> None:
    from scripts import major_consolidation_sweep

    environment = {"TOGETHERAI_API_KEY": "uppercase", "togetherai_API_key": "legacy"}
    with patch.object(major_consolidation_sweep.os, "environ", environment):
        major_consolidation_sweep.configure_togetherai_api_key()
        assert environment["TOGETHERAI_API_KEY"] == "uppercase"


@pytest.mark.parametrize(
    ("legacy", "expected"), [("legacy", "legacy"), ("", None)])
def test_legacy_togetherai_key_is_copied_only_when_appropriate(legacy, expected) -> None:
    from scripts import major_consolidation_sweep

    environment = {"togetherai_API_key": legacy}
    with patch.object(major_consolidation_sweep.os, "environ", environment):
        major_consolidation_sweep.configure_togetherai_api_key()
        assert environment.get("TOGETHERAI_API_KEY") == expected


def test_empty_sweep_never_makes_an_external_llm_call() -> None:
    from scripts import major_consolidation_sweep

    with (
        patch.object(major_consolidation_sweep, "get_target_files", return_value=[]),
        patch.object(major_consolidation_sweep.litellm, "completion") as completion,
    ):
        major_consolidation_sweep.main()

    completion.assert_not_called()
