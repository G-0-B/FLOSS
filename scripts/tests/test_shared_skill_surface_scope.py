"""Scope gating and path portability for the shared skill surface.

Regression cover for three PR41 review findings against this materializer:

1. It had no scope gate at all, while its two siblings did -- and two of its
   targets write outside the repository (`~/.codex/skills` and the Hermes skills
   directory). A plain `refresh_agent_surfaces.py` with no `--include-user-scope`
   therefore rewrote machine-wide state from a repo-scope run.
2. `resolve_install_path` expanded `~` but not `%VAR%`/`$VAR`, so the Hermes
   target hardcoded one machine's absolute Windows path. On POSIX that string is
   not absolute, so it was joined to the workspace and materialization created a
   literal `C:/Users/kalis/...` tree inside the repo.
3. Fourteen skill entries used a backslash separator. On POSIX `pathlib` treats
   it as a literal filename character, so `resolve_skill_entry` raised
   `SkillSurfaceError` and the whole skill step failed before writing anything.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "materialize_shared_skill_surface.py"
MANIFEST_PATH = REPO_ROOT / "shared-skill-surface.json"


def env_ref(name: str) -> str:
    """Reference an environment variable in this platform's own dialect.

    `os.path.expandvars` expands `%VAR%` only on Windows and `$VAR` only on
    POSIX. The production manifest keeps `%LOCALAPPDATA%` because that target is
    Windows-only by nature and is skipped elsewhere; this test is about the
    expansion mechanism, so it has to ask in the local dialect.
    """
    return f"%{name}%" if os.name == "nt" else f"${name}"


def load_module():
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "shared_skill_surface_under_test", MODULE_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def manifest_with(targets: dict) -> dict:
    return {"manifest_version": "test", "targets": targets, "skills": []}


def test_user_scope_targets_are_skipped_without_the_opt_in(tmp_path):
    module = load_module()
    manifest = manifest_with(
        {
            "repo_target": {
                "enabled": True,
                "install_path": ".claude/skills",
                "scope": "repo",
            },
            "user_target": {
                "enabled": True,
                "install_path": str(tmp_path / "elsewhere"),
                "scope": "user",
            },
        }
    )
    roots = module.build_target_roots(manifest, tmp_path)
    skipped: list[str] = []
    writable = module.writable_targets(
        manifest, roots, include_user_scope=False, skipped=skipped
    )

    assert "repo_target" in writable
    assert "user_target" not in writable
    assert any("user_target" in line for line in skipped)


def test_user_scope_targets_are_written_with_the_opt_in(tmp_path):
    module = load_module()
    manifest = manifest_with(
        {
            "user_target": {
                "enabled": True,
                "install_path": str(tmp_path / "elsewhere"),
                "scope": "user",
            },
        }
    )
    roots = module.build_target_roots(manifest, tmp_path)
    writable = module.writable_targets(manifest, roots, include_user_scope=True)

    assert "user_target" in writable


def test_the_registry_does_not_change_with_the_scope_flag(tmp_path):
    """A generated artifact must not depend on a runtime flag.

    If the scope gate filtered the roots that go into the registry, a plain
    refresh and a user-scope refresh would each call the other's output drift.
    """
    module = load_module()
    manifest = manifest_with(
        {
            "user_target": {
                "enabled": True,
                "install_path": str(tmp_path / "elsewhere"),
                "scope": "user",
            },
        }
    )
    roots = module.build_target_roots(manifest, tmp_path)
    assert "user_target" in roots


def test_a_repo_scope_target_may_not_resolve_outside_the_workspace(tmp_path):
    module = load_module()
    manifest = manifest_with(
        {
            "sneaky": {
                "enabled": True,
                "install_path": str(tmp_path.parent / "outside"),
                "scope": "repo",
            },
        }
    )
    with pytest.raises(module.SkillSurfaceError, match="declares scope 'repo'"):
        module.build_target_roots(manifest, tmp_path)


def test_install_paths_expand_environment_variables(tmp_path, monkeypatch):
    module = load_module()
    monkeypatch.setenv("SKILL_SURFACE_TEST_HOME", str(tmp_path / "appdata"))
    manifest = manifest_with(
        {
            "hermes_like": {
                "enabled": True,
                "install_path": f"{env_ref('SKILL_SURFACE_TEST_HOME')}/hermes/skills",
                "scope": "user",
            },
        }
    )
    roots = module.build_target_roots(manifest, tmp_path)

    resolved = Path(roots["hermes_like"])
    assert resolved == (tmp_path / "appdata" / "hermes" / "skills")
    assert "%" not in str(resolved) and "$" not in str(resolved)


def test_an_unresolvable_user_target_is_skipped_not_fatal(tmp_path, monkeypatch):
    """A POSIX run has no %LOCALAPPDATA%; that must not take the step down."""
    module = load_module()
    monkeypatch.delenv("SKILL_SURFACE_TEST_UNSET", raising=False)
    manifest = manifest_with(
        {
            "repo_target": {
                "enabled": True,
                "install_path": ".claude/skills",
                "scope": "repo",
            },
            "windows_only": {
                "enabled": True,
                "install_path": f"{env_ref('SKILL_SURFACE_TEST_UNSET')}/skills",
                "scope": "user",
            },
        }
    )
    skipped: list[str] = []
    roots = module.build_target_roots(manifest, tmp_path, skipped=skipped)

    assert "repo_target" in roots
    assert "windows_only" not in roots
    assert any("windows_only" in line for line in skipped)


def test_skill_paths_with_backslashes_still_resolve(tmp_path):
    module = load_module()
    skill_dir = tmp_path / "corpus" / "example"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: example\ndescription: example skill\n---\n\nbody\n",
        encoding="utf-8",
    )

    entry = {"path": "corpus" + chr(92) + "example"}
    resolved = module.resolve_skill_entry(tmp_path, entry)

    assert Path(resolved["resolved_path"]) == skill_dir
    assert resolved["skill_name"] == "example"


def test_the_shipped_manifest_uses_portable_separators_and_declares_scope():
    """The manifest itself, not just the code that reads it."""
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    offenders = [
        skill["path"]
        for skill in manifest["skills"]
        if chr(92) in str(skill.get("path", ""))
    ]
    assert not offenders, f"backslash separators are not portable: {offenders}"

    for name, cfg in manifest["targets"].items():
        if not cfg.get("enabled"):
            continue
        install_path = str(cfg.get("install_path", ""))
        assert cfg.get("scope") in {"repo", "user"}, f"{name} must declare a scope"
        if cfg.get("scope") == "repo":
            continue
        assert not install_path.startswith("C:/"), (
            f"{name} hardcodes an absolute Windows path; use a platform variable"
        )
