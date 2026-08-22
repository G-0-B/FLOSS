"""Scope gating for the shared hook surface.

Regression cover for a gap found in PR41 review: this materializer had no scope
gate at all, while the sibling agent-surface materializer -- invoked from the
same runner, in the same pass -- gated `~/.codex/config.toml` and the Hermes
AppData config carefully and documented why.

The consequence was that a plain `refresh_agent_surfaces.py`, with no
`--include-user-scope`, rewrote `~/.claude/settings.json` and the Hermes config:
machine-wide state, from what the caller believed was a repo-scope run. Observed
doing exactly that on 2026-08-21.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "materialize_shared_hook_surface.py"


def load_module():
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "shared_hook_surface_scope_under_test", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_manifest(tmp_path: Path) -> Path:
    manifest = {
        "manifest_version": "test",
        "workspace_id": "test",
        "workspace_name": "test",
        "rules": [],
        "hook_scripts": [],
        "targets": {
            "repo_target": {
                "enabled": True,
                "scope": "repo",
                "settings_path": ".repo/settings.json",
                "hooks": {},
            },
            "user_target": {
                "enabled": True,
                "scope": "user",
                "settings_path": "outside/user-settings.json",
                "hooks": {},
            },
        },
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_repo_scope_run_does_not_write_the_user_target(tmp_path):
    """The default run must leave out-of-repo state alone."""
    module = load_module()
    manifest_path = write_manifest(tmp_path)

    results, _ = module.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=tmp_path / "out",
        check=False,
        dry_run=False,
    )

    assert (tmp_path / ".repo" / "settings.json").exists()
    assert not (tmp_path / "outside" / "user-settings.json").exists()
    assert any("SKIP" in line and "user_target" in line for line in results), (
        "skipping a user-scope target must be reported, not silent"
    )


def test_include_user_scope_writes_the_user_target(tmp_path):
    module = load_module()
    manifest_path = write_manifest(tmp_path)

    module.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=tmp_path / "out",
        check=False,
        dry_run=False,
        include_user_scope=True,
    )

    assert (tmp_path / "outside" / "user-settings.json").exists()


def test_registry_content_does_not_depend_on_the_opt_in(tmp_path):
    """`--check` compares against the registry, so it must not vary with the flag.

    If the registry omitted user-scope targets on a repo-scope run, a repo-scope
    `--check` would report drift purely because the previous write happened to
    use `--include-user-scope`. The gate belongs on the writes, not on the
    description of the manifest.
    """
    module = load_module()
    manifest_path = write_manifest(tmp_path)

    module.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=tmp_path / "repo-scope",
        check=False,
        dry_run=False,
    )
    module.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=tmp_path / "user-scope",
        check=False,
        dry_run=False,
        include_user_scope=True,
    )

    repo_registry = (tmp_path / "repo-scope" / "hook-registry.json").read_text(
        encoding="utf-8"
    )
    user_registry = (tmp_path / "user-scope" / "hook-registry.json").read_text(
        encoding="utf-8"
    )
    assert repo_registry == user_registry
    assert "user_target" in repo_registry


def test_missing_scope_is_refused_rather_than_defaulted(tmp_path):
    """Absence must raise, for the reason the sibling module documents.

    Defaulting an absent `scope` to the permissive value would mean a future
    target that forgets the field writes outside the repo with this gate never
    consulted -- which is precisely the state this fix corrects.
    """
    module = load_module()
    manifest = {
        "manifest_version": "test",
        "workspace_id": "test",
        "workspace_name": "test",
        "rules": [],
        "hook_scripts": [],
        "targets": {
            "no_scope": {
                "enabled": True,
                "settings_path": ".repo/settings.json",
                "hooks": {},
            }
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(module.HookSurfaceError, match="missing required `scope`"):
        module.materialize(
            workspace_root=tmp_path,
            manifest_path=manifest_path,
            output_dir=tmp_path / "out",
            check=False,
            dry_run=False,
        )


def test_unresolvable_platform_path_does_not_abort_the_repo_scope_surface(tmp_path):
    """A Windows-only user target must not break materialization on POSIX.

    `hermes_user` is `%LOCALAPPDATA%/hermes/config.yaml`. POSIX
    `os.path.expandvars` leaves `%VAR%` literal, so path resolution raised while
    building the registry -- before the target could be skipped for any other
    reason. Regenerating even the repo-local Claude and Gemini configs therefore
    failed on Linux and macOS.
    """
    module = load_module()
    manifest = {
        "manifest_version": "test",
        "workspace_id": "test",
        "workspace_name": "test",
        "rules": [],
        "hook_scripts": [],
        "targets": {
            "repo_target": {
                "enabled": True,
                "scope": "repo",
                "settings_path": ".repo/settings.json",
                "hooks": {},
            },
            "windows_only": {
                "enabled": True,
                "scope": "user",
                "settings_path": "%DEFINITELY_NOT_SET_ANYWHERE%/config.yaml",
                "format": "yaml",
                "hooks": {},
            },
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    module.materialize(
        workspace_root=tmp_path,
        manifest_path=manifest_path,
        output_dir=tmp_path / "out",
        check=False,
        dry_run=False,
    )

    registry = json.loads(
        (tmp_path / "out" / "hook-registry.json").read_text(encoding="utf-8")
    )
    entry = registry["targets"]["windows_only"]
    assert entry["resolved_settings_path"] is None
    assert "unresolved_reason" in entry, (
        "an unresolvable target must say why, not silently look fine"
    )
    assert (tmp_path / ".repo" / "settings.json").exists(), (
        "the repo-scope target must still be written"
    )


def test_repo_scope_cannot_escape_the_workspace(tmp_path, monkeypatch):
    """A declared scope must agree with where the path actually resolves.

    `hook_target_in_scope` checks the declared string. On its own that is not a
    protection: a target could declare `scope: "repo"` while its settings_path
    expands, via %VAR% or ~, to somewhere else entirely, and then be written on
    an ordinary run with no --include-user-scope. Escaping the workspace is a
    user-scope act and must require the opt-in.

    Note on provenance: PR41 review claimed the existing `env_target` fixture in
    test_shared_hook_surface.py already demonstrated this. It does not -- that
    fixture expands to `tmp_path / "fake_appdata"` while workspace_root is
    `tmp_path`, so it resolves INSIDE the workspace and is correctly repo scope.
    The hole was real; the cited evidence was not. This test supplies the
    missing evidence.
    """
    module = load_module()

    outside = tmp_path / "outside_the_workspace"
    outside.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("HOOK_SCOPE_ESCAPE_TEST_DIR", str(outside))

    manifest = {
        "manifest_version": "test",
        "workspace_id": "test",
        "workspace_name": "test",
        "rules": [],
        "hook_scripts": [],
        "targets": {
            "sneaky": {
                "enabled": True,
                "scope": "repo",
                "settings_path": "%HOOK_SCOPE_ESCAPE_TEST_DIR%/settings.json",
                "hooks": {},
            }
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(module.HookSurfaceError, match="outside the workspace"):
        module.materialize(
            workspace_root=workspace,
            manifest_path=manifest_path,
            output_dir=tmp_path / "out",
            check=False,
            dry_run=False,
        )

    assert not (outside / "settings.json").exists(), (
        "the escaping target must not have been written before the check fired"
    )
