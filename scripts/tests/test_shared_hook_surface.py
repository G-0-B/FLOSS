from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

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
