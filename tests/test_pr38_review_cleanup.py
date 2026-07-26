"""Regression coverage for PR38 Task 1 review corrections."""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path
import re
from unittest.mock import patch

import jsonschema
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "docs" / "specs" / "yumeichan-watch-capabilities.schema.json"
SMOKE_SCRIPT_PATH = REPO_ROOT / "scripts" / "smoke_test_gateway.py"


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


def test_smoke_script_valid_capability_satisfies_schema() -> None:
    source = ast.parse(SMOKE_SCRIPT_PATH.read_text(encoding="utf-8"))
    assignment = next(
        node
        for node in ast.walk(source)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "valid_capability"
            for target in node.targets
        )
    )

    class _FakeDatetime:
        @classmethod
        def now(cls, _timezone):
            return cls()

        def isoformat(self):
            return "2026-07-26T00:00:00+00:00"

    capability = eval(
        compile(ast.Expression(assignment.value), str(SMOKE_SCRIPT_PATH), "eval"),
        {
            "datetime": _FakeDatetime,
            "timezone": type("Timezone", (), {"utc": object()}),
        },
    )
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    jsonschema.validate(capability, schema)


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


@pytest.mark.parametrize(
    ("non_finite_bound", "bound_position", "expected_message"),
    [
        (math.nan, 0, "must be finite"),
        (math.nan, 1, "must be finite"),
        (math.inf, 0, None),
        (math.inf, 1, None),
        (-math.inf, 0, None),
        (-math.inf, 1, None),
    ],
    ids=[
        "nan-minimum",
        "nan-maximum",
        "positive-infinity-minimum",
        "positive-infinity-maximum",
        "negative-infinity-minimum",
        "negative-infinity-maximum",
    ],
)
def test_semantic_validator_rejects_non_finite_threshold_bounds(
    non_finite_bound, bound_position, expected_message
) -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    capability = valid_capability()
    bounds = [-0.5, 0.8]
    bounds[bound_position] = non_finite_bound
    capability["analog_threshold_bounds"] = bounds

    with pytest.raises(jsonschema.ValidationError, match=expected_message):
        validate_capability(capability)


@pytest.mark.parametrize(
    "proof",
    [
        {"canonicalization": "RFC8785", "payload_digest": "a" * 64, "signature": "sig"},
        {
            "algorithm": "RSA",
            "canonicalization": "RFC8785",
            "payload_digest": "a" * 64,
            "signature": "sig",
        },
        {
            "algorithm": "Ed25519",
            "canonicalization": "JCS",
            "payload_digest": "a" * 64,
            "signature": "sig",
        },
        {
            "algorithm": "Ed25519",
            "canonicalization": "RFC8785",
            "payload_digest": "not-a-sha256-digest",
            "signature": "sig",
        },
        {
            "algorithm": "Ed25519",
            "canonicalization": "RFC8785",
            "payload_digest": "a" * 64,
            "signature": "",
        },
    ],
    ids=[
        "missing-nested-member",
        "wrong-algorithm",
        "wrong-canonicalization",
        "malformed-digest",
        "empty-signature",
    ],
)
def test_semantic_validator_rejects_invalid_proof_shape(proof) -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    capability = valid_capability()
    capability["proof"] = proof

    with pytest.raises(jsonschema.ValidationError):
        validate_capability(capability)


def test_uppercase_togetherai_key_is_preserved() -> None:
    from scripts import major_consolidation_sweep

    environment = {"TOGETHERAI_API_KEY": "uppercase", "togetherai_API_key": "legacy"}
    with patch.object(major_consolidation_sweep.os, "environ", environment):
        major_consolidation_sweep.configure_togetherai_api_key()
        assert environment["TOGETHERAI_API_KEY"] == "uppercase"


def test_empty_existing_uppercase_togetherai_key_is_preserved() -> None:
    from scripts import major_consolidation_sweep

    environment = {"TOGETHERAI_API_KEY": "", "togetherai_API_key": "legacy"}
    with patch.object(major_consolidation_sweep.os, "environ", environment):
        major_consolidation_sweep.configure_togetherai_api_key()
        assert environment["TOGETHERAI_API_KEY"] == ""


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


@pytest.mark.parametrize("root_name", ["FLOSS", "_codex_pr38_cleanup"])
def test_spec_gate_normalizes_and_audits_named_and_linked_worktrees(
    tmp_path, monkeypatch, root_name
) -> None:
    from scripts import spec_gate

    repo_root = tmp_path / root_name
    script_path = repo_root / "scripts" / "probe.py"
    registry_path = repo_root / "docs" / "specs" / "spec-registry.json"
    script_path.parent.mkdir(parents=True)
    registry_path.parent.mkdir(parents=True)
    script_path.write_text("# gated probe\n", encoding="utf-8")
    registry_path.write_text('{"version": "test", "entries": {}}\n', encoding="utf-8")

    monkeypatch.setattr(spec_gate, "REPO_ROOT", repo_root)
    monkeypatch.setattr(spec_gate, "REGISTRY_PATH", registry_path)

    assert spec_gate._normalize(script_path) == "FLOSS/scripts/probe.py"
    assert spec_gate.run_check() == 1

    registry_path.write_text(
        '{"version": "test", "entries": {"FLOSS/docs/specs/spec-registry.json": {"spec": "registry"}, "FLOSS/scripts/probe.py": {"spec": "probe"}}}\n',
        encoding="utf-8",
    )
    assert spec_gate.run_check() == 0


@pytest.mark.parametrize("root_name", ["FLOSS", "_codex_pr38_cleanup"])
def test_spec_gate_advisory_command_resolves_in_all_worktree_layouts(
    tmp_path, monkeypatch, root_name
) -> None:
    from scripts import spec_gate

    repo_root = tmp_path / root_name
    advisory_target = repo_root / "scripts" / "advisory_target.py"
    physical_target = repo_root / "scripts" / "physical_target.py"
    script_entrypoint = repo_root / "scripts" / "spec_gate.py"
    registry_path = repo_root / "docs" / "specs" / "spec-registry.json"
    advisory_target.parent.mkdir(parents=True)
    registry_path.parent.mkdir(parents=True)
    advisory_target.write_text("# advisory target\n", encoding="utf-8")
    physical_target.write_text("# physical target\n", encoding="utf-8")
    script_entrypoint.write_text("# spec-gate entrypoint\n", encoding="utf-8")
    registry_path.write_text('{"version": "test", "entries": {}}\n', encoding="utf-8")

    monkeypatch.setattr(spec_gate, "REPO_ROOT", repo_root)
    monkeypatch.setattr(spec_gate, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(spec_gate, "__file__", str(script_entrypoint))

    advisory = spec_gate.advisory_note(advisory_target)
    assert advisory is not None
    command = advisory.rsplit("register it before it ossifies: ", 1)[1]
    command_match = re.fullmatch(
        r'python "(?P<script_path>[^"]+)" --add "(?P<add_path>[^"]+)" '
        r'--spec "<one-line intent>"',
        command,
    )
    assert command_match is not None
    emitted_script_path = Path(command_match["script_path"]).resolve()
    assert emitted_script_path == script_entrypoint.resolve()
    assert emitted_script_path.is_file()
    advisory_argument = command_match["add_path"]
    assert advisory_argument == "FLOSS/scripts/advisory_target.py"

    assert spec_gate.run_add(advisory_argument, "advisory target", None) == 0
    assert spec_gate.run_add("scripts/physical_target.py", "physical target", None) == 0
    assert spec_gate._normalize(tmp_path / "outside.py") is None
    assert spec_gate.run_add(str(tmp_path / "outside.py"), "outside", None) == 1

    entries = json.loads(registry_path.read_text(encoding="utf-8"))["entries"]
    assert set(entries) == {
        "FLOSS/scripts/advisory_target.py",
        "FLOSS/scripts/physical_target.py",
    }
