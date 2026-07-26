from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[2]


def load_hook_surface_module():
    if str(FLOSS_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(FLOSS_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "shared_hook_surface_under_test",
        FLOSS_ROOT / "scripts" / "materialize_shared_hook_surface.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["shared_hook_surface_under_test"] = module
    spec.loader.exec_module(module)
    return module


def _write_hook_script(tmp_path: Path, relative: str) -> None:
    script_path = tmp_path / relative
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("# hook script\n", encoding="utf-8")


def test_hooks_only_target_emits_wrapped_shape_without_unrelated_keys(tmp_path):
    surface = load_hook_surface_module()

    _write_hook_script(tmp_path, "FLOSS/scripts/hook_pre_write.py")

    manifest_path = tmp_path / "FLOSS" / "shared-hook-surface.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": "0.1.0",
        "workspace_id": "test-workspace",
        "workspace_name": "Test Workspace",
        "rules": [],
        "hook_scripts": ["FLOSS/scripts/hook_pre_write.py"],
        "targets": {
            "codex": {
                "enabled": True,
                "settings_path": ".codex/hooks.json",
                "payload_shape": "hooks_only",
                "hooks": {
                    "PreToolUse": [
                        {
                            "matcher": "Write|Edit|MultiEdit",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python hook_pre_write.py",
                                }
                            ],
                        }
                    ]
                },
            }
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    # Simulate a pre-existing hand-authored hooks.json so we can assert the
    # writer does NOT carry unrelated keys forward -- unlike the merge-based
    # `claude`/`gemini` targets, a `payload_shape: hooks_only` target's whole
    # file content must be exactly `{"hooks": {...}}`.
    codex_hooks_path = tmp_path / ".codex" / "hooks.json"
    codex_hooks_path.parent.mkdir(parents=True, exist_ok=True)
    codex_hooks_path.write_text(
        json.dumps({"hooks": {}, "unrelated_setting": "should-not-survive"}),
        encoding="utf-8",
    )

    output_dir = tmp_path / ".agent-surface" / "hooks"

    results, drift_found = surface.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
        check=False,
        dry_run=False,
    )

    assert drift_found is True
    assert any("WROTE" in line and "hooks.json" in line for line in results)

    written = json.loads(codex_hooks_path.read_text(encoding="utf-8"))

    assert set(written.keys()) == {"hooks"}
    assert "unrelated_setting" not in written
    assert written == {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python hook_pre_write.py",
                        }
                    ],
                }
            ]
        }
    }


def test_hooks_only_payload_helper_ignores_existing_content():
    surface = load_hook_surface_module()

    existing = {
        "hooks": {"PreToolUse": [{"matcher": "*", "hooks": []}]},
        "some_other_codex_setting": True,
    }
    target_cfg = {
        "payload_shape": "hooks_only",
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python session_start_inject.py",
                        }
                    ],
                }
            ]
        },
    }

    payload = surface.build_target_payload(existing, target_cfg)

    assert payload == {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python session_start_inject.py",
                        }
                    ],
                }
            ]
        }
    }


def test_merge_shape_target_still_preserves_unrelated_settings_keys():
    surface = load_hook_surface_module()

    existing = {
        "permissions": {"allow": ["Bash"]},
        "hooks": {"PreToolUse": [{"matcher": "old", "hooks": []}]},
    }
    target_cfg = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [{"type": "command", "command": "python hook.py"}],
                }
            ]
        }
    }

    payload = surface.build_target_payload(existing, target_cfg)

    assert payload["permissions"] == {"allow": ["Bash"]}
    assert payload["hooks"]["PreToolUse"][0]["matcher"] == "Write|Edit|MultiEdit"


# ---------------------------------------------------------------------------
# Capability B: `event_map` per target
# ---------------------------------------------------------------------------


def test_event_map_renames_events():
    surface = load_hook_surface_module()

    target_cfg = {
        "event_map": {"PreToolUse": "pre_tool_call", "PostToolUse": "post_tool_call"},
        "hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": []}],
            "PostToolUse": [{"matcher": "*", "hooks": []}],
        },
    }

    mapped = surface.resolve_target_hooks(target_cfg)

    assert set(mapped.keys()) == {"pre_tool_call", "post_tool_call"}
    assert mapped["pre_tool_call"] == target_cfg["hooks"]["PreToolUse"]
    assert mapped["post_tool_call"] == target_cfg["hooks"]["PostToolUse"]


def test_event_map_omits_event_absent_from_map():
    surface = load_hook_surface_module()

    # SessionStart is present in the manifest hooks but absent from this
    # target's event_map -- it must be dropped, not passed through raw.
    target_cfg = {
        "event_map": {"PreToolUse": "pre_tool_call"},
        "hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": []}],
            "SessionStart": [{"matcher": "*", "hooks": []}],
        },
    }

    mapped = surface.resolve_target_hooks(target_cfg)

    assert set(mapped.keys()) == {"pre_tool_call"}
    assert "SessionStart" not in mapped


def test_no_event_map_preserves_events_unchanged():
    surface = load_hook_surface_module()

    target_cfg = {
        "hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": []}],
            "SessionStart": [{"matcher": "*", "hooks": []}],
        }
    }

    mapped = surface.resolve_target_hooks(target_cfg)

    assert mapped == target_cfg["hooks"]
    assert mapped is not target_cfg["hooks"]  # returns a copy, not the same object


def test_event_map_wired_through_build_target_payload_for_hooks_only_shape():
    surface = load_hook_surface_module()

    target_cfg = {
        "payload_shape": "hooks_only",
        "event_map": {"PreToolUse": "pre_tool_call"},
        "hooks": {
            "PreToolUse": [{"matcher": "*", "hooks": []}],
            "SessionStart": [{"matcher": "*", "hooks": []}],
        },
    }

    payload = surface.build_target_payload({}, target_cfg)

    assert payload == {"hooks": {"pre_tool_call": [{"matcher": "*", "hooks": []}]}}


def test_event_map_wired_through_build_target_payload_for_merge_shape():
    surface = load_hook_surface_module()

    existing = {"hooks": {"pre_tool_call": [{"matcher": "old", "hooks": []}]}}
    target_cfg = {
        "event_map": {"PreToolUse": "pre_tool_call"},
        "hooks": {
            "PreToolUse": [{"matcher": "Write|Edit|MultiEdit", "hooks": []}],
            "SessionStart": [{"matcher": "*", "hooks": []}],
        },
    }

    payload = surface.build_target_payload(existing, target_cfg)

    assert payload["hooks"] == {
        "pre_tool_call": [{"matcher": "Write|Edit|MultiEdit", "hooks": []}]
    }
    assert "SessionStart" not in payload["hooks"]
    assert "session_start" not in payload["hooks"]


# ---------------------------------------------------------------------------
# Capability A: `format: json | yaml` per target
# ---------------------------------------------------------------------------


def _canonical_yaml_text(raw_yaml: str) -> str:
    """Round-trip `raw_yaml` once through the exact ruamel config the
    materializer uses, so a fixture is already in the writer's canonical
    formatting before a test diffs it against the writer's output.
    """
    ruamel_yaml = pytest.importorskip("ruamel.yaml")
    yaml_rt = ruamel_yaml.YAML()
    yaml_rt.preserve_quotes = True
    yaml_rt.indent(mapping=2, sequence=4, offset=2)
    yaml_rt.width = 4096
    doc = yaml_rt.load(raw_yaml)
    buffer = io.StringIO()
    yaml_rt.dump(doc, buffer)
    return buffer.getvalue()


_YAML_FIXTURE_RAW = """\
# workspace config
name: test-harness  # inline comment
mcp_servers:
  foo:
    command: foo-cmd
    args:
      - --bar
    # a comment inside the mapping
unrelated_settings:
  nested: true
  items:
    - alpha
    - beta
hooks:
  pre_tool_call:
    - matcher: old
      hooks: []
"""


def test_yaml_target_writes_valid_yaml(tmp_path):
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    config_path = tmp_path / "config.yaml"
    config_path.write_text(_canonical_yaml_text(_YAML_FIXTURE_RAW), encoding="utf-8")

    target_cfg = {
        "format": "yaml",
        "event_map": {"PreToolUse": "pre_tool_call", "PostToolUse": "post_tool_call"},
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {"type": "command", "command": "python hook_pre_write.py"}
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {"type": "command", "command": "python hook_post_write.py"}
                    ],
                }
            ],
        },
    }

    message, changed = surface.apply_yaml_target(
        config_path, target_cfg, check=False, dry_run=False
    )

    assert "WROTE" in message
    assert changed is True

    ruamel_yaml = pytest.importorskip("ruamel.yaml")
    reloaded = ruamel_yaml.YAML().load(config_path.read_text(encoding="utf-8"))
    assert set(reloaded["hooks"].keys()) == {"pre_tool_call", "post_tool_call"}
    assert reloaded["hooks"]["pre_tool_call"][0]["matcher"] == "Write|Edit|MultiEdit"


def test_yaml_fixture_round_trips_apart_from_hook_block(tmp_path):
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    fixture_text = _canonical_yaml_text(_YAML_FIXTURE_RAW)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(fixture_text, encoding="utf-8")

    target_cfg = {
        "format": "yaml",
        "event_map": {"PreToolUse": "pre_tool_call", "PostToolUse": "post_tool_call"},
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {"type": "command", "command": "python hook_pre_write.py"}
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {"type": "command", "command": "python hook_post_write.py"}
                    ],
                }
            ],
            # Absent from event_map -- must not leak into the yaml target.
            "SessionStart": [
                {
                    "matcher": "*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python session_start_inject.py",
                        }
                    ],
                }
            ],
        },
    }

    message, changed = surface.apply_yaml_target(
        config_path, target_cfg, check=False, dry_run=False
    )
    assert changed is True
    result_text = config_path.read_text(encoding="utf-8")

    # `hooks:` is the last top-level key in the fixture, so everything
    # before it is untouched content that must survive byte-for-byte --
    # comments, unrelated top-level keys, and nested comments included.
    boundary = fixture_text.index("hooks:\n")
    assert result_text[:boundary] == fixture_text[:boundary]
    assert "# workspace config" in result_text
    assert "name: test-harness  # inline comment" in result_text
    assert "# a comment inside the mapping" in result_text
    assert "unrelated_settings:" in result_text
    assert "nested: true" in result_text

    assert "SessionStart" not in result_text
    assert "session_start" not in result_text

    ruamel_yaml = pytest.importorskip("ruamel.yaml")
    reloaded = ruamel_yaml.YAML().load(result_text)
    assert set(reloaded["hooks"].keys()) == {"pre_tool_call", "post_tool_call"}


def test_yaml_true_noop_round_trip_is_byte_identical(tmp_path):
    """The ruamel config's whole point: a no-op merge must not reflow the
    document. This is what the Hermes `config.yaml` case (Task 3) depends
    on -- a bare `ruamel.yaml.YAML()` measurably reflows an entire
    unrelated 726-line document on a no-op change.
    """
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    fixture_text = _canonical_yaml_text(_YAML_FIXTURE_RAW)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(fixture_text, encoding="utf-8")

    # Target hooks already match exactly what's on disk (pre_tool_call with
    # matcher "old" and an empty hooks list) -- a genuine no-op.
    target_cfg = {
        "format": "yaml",
        "event_map": {"PreToolUse": "pre_tool_call"},
        "hooks": {"PreToolUse": [{"matcher": "old", "hooks": []}]},
    }

    message, changed = surface.apply_yaml_target(
        config_path, target_cfg, check=False, dry_run=False
    )

    assert changed is False
    assert "OK" in message
    assert config_path.read_text(encoding="utf-8") == fixture_text


def test_missing_file_yaml_target_does_not_fabricate_file(tmp_path):
    surface = load_hook_surface_module()

    config_path = tmp_path / "does-not-exist" / "config.yaml"
    target_cfg = {
        "format": "yaml",
        "hooks": {"PreToolUse": [{"matcher": "*", "hooks": []}]},
    }

    message, changed = surface.apply_yaml_target(
        config_path, target_cfg, check=False, dry_run=False
    )

    assert "SKIP" in message
    assert changed is False
    assert not config_path.exists()


def test_missing_file_yaml_target_skipped_via_materialize_without_drift(tmp_path):
    surface = load_hook_surface_module()

    _write_hook_script(tmp_path, "FLOSS/scripts/hook_pre_write.py")

    manifest_path = tmp_path / "FLOSS" / "shared-hook-surface.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": "0.1.0",
        "workspace_id": "test-workspace",
        "workspace_name": "Test Workspace",
        "rules": [],
        "hook_scripts": ["FLOSS/scripts/hook_pre_write.py"],
        "targets": {
            "hermes": {
                "enabled": True,
                "settings_path": "config.yaml",
                "format": "yaml",
                "event_map": {"PreToolUse": "pre_tool_call"},
                "hooks": {
                    "PreToolUse": [{"matcher": "*", "hooks": []}],
                },
            }
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    output_dir = tmp_path / ".agent-surface" / "hooks"

    results, drift_found = surface.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
        check=False,
        dry_run=False,
    )

    assert not (tmp_path / "config.yaml").exists()
    assert any("SKIP" in line and "config.yaml" in line for line in results)


def test_default_format_is_json_and_existing_targets_unaffected(tmp_path):
    surface = load_hook_surface_module()

    target_cfg = {
        "enabled": True,
        "settings_path": "settings.json",
        "hooks": {"PreToolUse": [{"matcher": "*", "hooks": []}]},
    }

    assert target_cfg.get("format", "json") == "json"
    # No `format` key at all is exactly what claude/gemini/codex declare
    # today -- build_target_payload must not require it.
    payload = surface.build_target_payload({}, target_cfg)
    assert payload["hooks"]["PreToolUse"] == [{"matcher": "*", "hooks": []}]


# ---------------------------------------------------------------------------
# Task 3: Hermes liveness guard (reused from materialize_shared_agent_surface)
# ---------------------------------------------------------------------------


def _hermes_target_cfg() -> dict:
    return {
        "format": "yaml",
        "event_map": {"PreToolUse": "pre_tool_call", "PostToolUse": "post_tool_call"},
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {"type": "command", "command": "python hook_pre_write.py"}
                    ],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit",
                    "hooks": [
                        {"type": "command", "command": "python hook_post_write.py"}
                    ],
                }
            ],
        },
    }


def test_hermes_gateway_alive_for_reuses_sibling_liveness_check(tmp_path):
    """`hermes_gateway_alive_for` must delegate to
    `materialize_shared_agent_surface.hermes_gateway_alive` rather than
    reimplementing it -- this is the same liveness guard the MCP Hermes
    target relies on, and there must be exactly one implementation of "is a
    Hermes gateway alive for this home directory".
    """
    surface = load_hook_surface_module()

    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    config_path = hermes_dir / "config.yaml"

    # No gateway.pid at all -- not a Hermes home, or the gateway never ran.
    assert surface.hermes_gateway_alive_for(config_path) is None

    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid()}), encoding="utf-8"
    )
    assert surface.hermes_gateway_alive_for(config_path) == os.getpid()


def test_yaml_target_refuses_write_when_gateway_pid_is_live(tmp_path):
    """A running gateway rewrites its own config.yaml on shutdown, which
    would clobber a write made underneath it -- so a live `gateway.pid` in
    the target's directory must block the write entirely, not just flag
    drift. The fixture stands in for a live Hermes gateway; `os.getpid()` is
    guaranteed alive without needing to actually spawn one.
    """
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    config_path = hermes_dir / "config.yaml"
    fixture_text = _canonical_yaml_text(_YAML_FIXTURE_RAW)
    config_path.write_text(fixture_text, encoding="utf-8")
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid()}), encoding="utf-8"
    )

    message, changed = surface.apply_yaml_target(
        config_path, _hermes_target_cfg(), check=False, dry_run=False
    )

    assert message.startswith("REFUSED")
    assert str(os.getpid()) in message
    assert changed is True
    # The file must be byte-unchanged -- the whole point of the guard.
    assert config_path.read_text(encoding="utf-8") == fixture_text


@pytest.mark.parametrize("check,dry_run", [(True, False), (False, True)])
def test_yaml_target_refuses_under_check_and_dry_run_too(tmp_path, check, dry_run):
    """The liveness guard must fire before the check/dry-run branch, so an
    operator learns about the blocker from a dry `--check` pass, not only
    when a real write already failed.
    """
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    config_path = hermes_dir / "config.yaml"
    fixture_text = _canonical_yaml_text(_YAML_FIXTURE_RAW)
    config_path.write_text(fixture_text, encoding="utf-8")
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid()}), encoding="utf-8"
    )

    message, changed = surface.apply_yaml_target(
        config_path, _hermes_target_cfg(), check=check, dry_run=dry_run
    )

    assert message.startswith("REFUSED")
    assert changed is True
    assert config_path.read_text(encoding="utf-8") == fixture_text


def test_yaml_target_writes_when_gateway_pid_is_stale(tmp_path):
    """A `gateway.pid` naming a process that is no longer running must NOT
    block the write -- only an actually-live gateway is a clobber risk.
    """
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    hermes_dir = tmp_path / "hermes"
    hermes_dir.mkdir()
    config_path = hermes_dir / "config.yaml"
    fixture_text = _canonical_yaml_text(_YAML_FIXTURE_RAW)
    config_path.write_text(fixture_text, encoding="utf-8")
    # An implausibly large PID: on Windows, `tasklist /FI "PID eq N"` for a
    # nonexistent PID returns a non-empty "no tasks match" message (not an
    # error and not empty output), which `_pid_alive` correctly reads as
    # "not alive" rather than failing closed.
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": 99999999}), encoding="utf-8"
    )

    message, changed = surface.apply_yaml_target(
        config_path, _hermes_target_cfg(), check=False, dry_run=False
    )

    assert "WROTE" in message
    assert changed is True
    assert "REFUSED" not in message


def test_materialize_reports_refused_for_live_gateway_and_leaves_file_untouched(
    tmp_path,
):
    """End-to-end through `materialize()`: a live-gateway-blocked Hermes-like
    target must surface a REFUSED line, report drift, and leave the on-disk
    config byte-unchanged.
    """
    pytest.importorskip("ruamel.yaml")
    surface = load_hook_surface_module()

    _write_hook_script(tmp_path, "FLOSS/scripts/hook_pre_write.py")
    _write_hook_script(tmp_path, "FLOSS/scripts/hook_post_write.py")

    hermes_dir = tmp_path / ".toilet" / "hermes"
    hermes_dir.mkdir(parents=True)
    config_path = hermes_dir / "config.yaml"
    fixture_text = _canonical_yaml_text(_YAML_FIXTURE_RAW)
    config_path.write_text(fixture_text, encoding="utf-8")
    (hermes_dir / "gateway.pid").write_text(
        json.dumps({"pid": os.getpid()}), encoding="utf-8"
    )

    manifest_path = tmp_path / "FLOSS" / "shared-hook-surface.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": "0.1.0",
        "workspace_id": "test-workspace",
        "workspace_name": "Test Workspace",
        "rules": [],
        "hook_scripts": [
            "FLOSS/scripts/hook_pre_write.py",
            "FLOSS/scripts/hook_post_write.py",
        ],
        "targets": {
            "hermes_workspace": {
                "enabled": True,
                "settings_path": ".toilet/hermes/config.yaml",
                **_hermes_target_cfg(),
            }
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    output_dir = tmp_path / ".agent-surface" / "hooks"

    results, drift_found = surface.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=output_dir,
        check=False,
        dry_run=False,
    )

    assert drift_found is True
    assert any(line.startswith("REFUSED") and "config.yaml" in line for line in results)
    assert config_path.read_text(encoding="utf-8") == fixture_text
