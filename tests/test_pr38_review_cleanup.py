"""Regression coverage for PR38 Task 1 review corrections."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
from unittest.mock import call, patch

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


def _ast_to_data(node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        if type(node.value) in {str, int, float, bool} or node.value is None:
            return node.value
        raise AssertionError(f"Unsupported constant: {type(node.value).__name__}")

    if isinstance(node, ast.Dict):
        assert all(key is not None for key in node.keys), "Dict unpacking is unsupported"
        return {
            _ast_to_data(key): _ast_to_data(value)
            for key, value in zip(node.keys, node.values)
        }

    if isinstance(node, ast.List):
        return [_ast_to_data(element) for element in node.elts]

    if isinstance(node, ast.Tuple):
        return tuple(_ast_to_data(element) for element in node.elts)

    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.USub, ast.UAdd))
        and isinstance(node.operand, ast.Constant)
        and type(node.operand.value) in {int, float}
    ):
        return -node.operand.value if isinstance(node.op, ast.USub) else node.operand.value

    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and isinstance(node.left, ast.Constant)
        and type(node.left.value) is str
        and isinstance(node.right, ast.Constant)
        and type(node.right.value) is int
        and 0 <= node.right.value <= 4096
    ):
        return node.left.value * node.right.value

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "isoformat"
        and not node.args
        and not node.keywords
        and isinstance(node.func.value, ast.Call)
        and isinstance(node.func.value.func, ast.Attribute)
        and node.func.value.func.attr == "now"
        and not node.func.value.keywords
        and len(node.func.value.args) == 1
        and isinstance(node.func.value.func.value, ast.Name)
        and node.func.value.func.value.id == "datetime"
        and isinstance(node.func.value.args[0], ast.Attribute)
        and node.func.value.args[0].attr == "utc"
        and isinstance(node.func.value.args[0].value, ast.Name)
        and node.func.value.args[0].value.id == "timezone"
    ):
        return "2026-07-26T00:00:00+00:00"

    raise AssertionError(f"Unsupported AST node: {type(node).__name__}")


def _extract_valid_capability_from_source(source: ast.Module) -> dict[str, object]:
    main_functions = [
        node
        for node in source.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    assert len(main_functions) == 1, "Expected exactly one main() function"

    def main_scope_nodes(nodes):
        for node in nodes:
            yield node
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)
            ):
                continue
            yield from main_scope_nodes(ast.iter_child_nodes(node))

    assignments = [
        node
        for node in main_scope_nodes(main_functions[0].body)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "valid_capability"
            for target in node.targets
        )
    ]
    assert len(assignments) == 1, (
        "Expected exactly one direct valid_capability assignment in main()"
    )
    capability = _ast_to_data(assignments[0].value)
    assert isinstance(capability, dict), "valid_capability must be a dict"
    return capability


def _extract_smoke_valid_capability() -> dict[str, object]:
    source = ast.parse(SMOKE_SCRIPT_PATH.read_text(encoding="utf-8"))
    return _extract_valid_capability_from_source(source)


def test_smoke_script_valid_capability_satisfies_schema() -> None:
    capability = _extract_smoke_valid_capability()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    jsonschema.validate(capability, schema)


def test_smoke_fixture_rejects_unsupported_executable_ast() -> None:
    with pytest.raises(AssertionError, match="Unsupported AST node"):
        _ast_to_data(ast.parse("read_credentials()").body[0].value)


def test_smoke_fixture_requires_one_direct_main_assignment() -> None:
    source = ast.parse(
        """
def main():
    valid_capability = {}
    valid_capability = {}
"""
    )

    with pytest.raises(AssertionError, match="exactly one"):
        _extract_valid_capability_from_source(source)


def test_smoke_fixture_ignores_module_level_decoy_assignment() -> None:
    source = ast.parse(
        """
valid_capability = {"source": "module"}
def main():
    with open("fixture"):
        valid_capability = {"source": "main"}
"""
    )

    assert _extract_valid_capability_from_source(source) == {"source": "main"}


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

    validate_capability(
        valid_capability(),
        now=datetime(2026, 7, 26, 0, 0, 30, tzinfo=timezone.utc),
    )


def test_semantic_validator_rejects_expired_capability() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    with pytest.raises(jsonschema.ValidationError, match="expired"):
        validate_capability(
            valid_capability(),
            now=datetime(2026, 7, 26, 0, 1, 1, tzinfo=timezone.utc),
        )


def test_semantic_validator_rejects_future_issued_capability() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    with pytest.raises(jsonschema.ValidationError, match="future"):
        validate_capability(
            valid_capability(),
            now=datetime(2026, 7, 25, 23, 59, 59, tzinfo=timezone.utc),
        )


def test_semantic_validator_accepts_timezone_aware_injected_now() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    eastern = timezone(-timedelta(hours=4))
    validate_capability(
        valid_capability(),
        now=datetime(2026, 7, 25, 20, 0, 30, tzinfo=eastern),
    )


def test_semantic_validator_accepts_unexpired_capability() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    validate_capability(
        valid_capability(),
        now=datetime(2026, 7, 26, 0, 0, 59, tzinfo=timezone.utc),
    )


def test_semantic_validator_rejects_naive_injected_now() -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    with pytest.raises(jsonschema.ValidationError, match="timezone-aware"):
        validate_capability(
            valid_capability(),
            now=datetime(2026, 7, 26, 0, 0, 30),
        )


@pytest.mark.parametrize(
    "issued_at",
    ["not-an-instant", "2026-07-26T00:00:00"],
    ids=["malformed", "naive"],
)
def test_semantic_validator_rejects_unusable_issued_at(issued_at: str) -> None:
    from scripts.yumeichan_watch_capabilities import validate_capability

    capability = valid_capability()
    capability["issued_at"] = issued_at

    with pytest.raises(jsonschema.ValidationError, match="timezone-aware"):
        validate_capability(
            capability,
            now=datetime(2026, 7, 26, 0, 0, 30, tzinfo=timezone.utc),
        )


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


def test_consolidation_retry_failure_is_not_appended_or_marked() -> None:
    from scripts import major_consolidation_sweep

    source_path = REPO_ROOT / "retry-failure.md"
    rate_limit_failure = "LLM Extraction Failed for chunk 1: RateLimitError"
    retry_failure = "LLM Extraction Failed for chunk 1: 429 retry exhausted"

    with (
        patch.object(
            major_consolidation_sweep, "get_target_files", return_value=[source_path]
        ),
        patch.object(
            major_consolidation_sweep, "load_processed_files", return_value=set()
        ),
        patch.object(
            major_consolidation_sweep,
            "extract_and_synthesize",
            side_effect=[rate_limit_failure, retry_failure],
        ) as extract,
        patch.object(major_consolidation_sweep, "append_to_vision") as append,
        patch.object(major_consolidation_sweep, "mark_processed") as mark,
        patch.object(major_consolidation_sweep, "load_dotenv"),
        patch.object(major_consolidation_sweep.litellm, "completion") as completion,
        patch.object(major_consolidation_sweep.time, "sleep") as sleep,
    ):
        major_consolidation_sweep.main()

    assert extract.call_count == 2
    append.assert_not_called()
    mark.assert_not_called()
    completion.assert_not_called()
    sleep.assert_called_once_with(60)


def test_consolidation_successful_retry_is_appended_and_marked_once() -> None:
    from scripts import major_consolidation_sweep

    source_path = REPO_ROOT / "retry-success.md"
    rate_limit_failure = "LLM Extraction Failed for chunk 1: 429"
    retry_success = "Retry synthesis succeeded."

    with (
        patch.object(
            major_consolidation_sweep, "get_target_files", return_value=[source_path]
        ),
        patch.object(
            major_consolidation_sweep, "load_processed_files", return_value=set()
        ),
        patch.object(
            major_consolidation_sweep,
            "extract_and_synthesize",
            side_effect=[rate_limit_failure, retry_success],
        ) as extract,
        patch.object(major_consolidation_sweep, "append_to_vision") as append,
        patch.object(major_consolidation_sweep, "mark_processed") as mark,
        patch.object(major_consolidation_sweep, "load_dotenv"),
        patch.object(major_consolidation_sweep.litellm, "completion") as completion,
        patch.object(major_consolidation_sweep.time, "sleep") as sleep,
    ):
        major_consolidation_sweep.main()

    assert extract.call_count == 2
    append.assert_called_once_with(source_path, retry_success)
    mark.assert_called_once_with(str(source_path.resolve()))
    completion.assert_not_called()
    assert sleep.call_args_list == [call(60), call(5)]


def test_consolidation_hard_error_remains_skipped_without_retry_or_side_effects() -> None:
    from scripts import major_consolidation_sweep

    source_path = REPO_ROOT / "hard-error.md"
    hard_failure = "LLM Extraction Failed for chunk 1: authentication failed"

    with (
        patch.object(
            major_consolidation_sweep, "get_target_files", return_value=[source_path]
        ),
        patch.object(
            major_consolidation_sweep, "load_processed_files", return_value=set()
        ),
        patch.object(
            major_consolidation_sweep,
            "extract_and_synthesize",
            return_value=hard_failure,
        ) as extract,
        patch.object(major_consolidation_sweep, "append_to_vision") as append,
        patch.object(major_consolidation_sweep, "mark_processed") as mark,
        patch.object(major_consolidation_sweep, "load_dotenv"),
        patch.object(major_consolidation_sweep.litellm, "completion") as completion,
        patch.object(major_consolidation_sweep.time, "sleep") as sleep,
    ):
        major_consolidation_sweep.main()

    extract.assert_called_once()
    append.assert_not_called()
    mark.assert_not_called()
    completion.assert_not_called()
    sleep.assert_not_called()


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
