"""Contract checks for porting the approved skill preservation flow to main."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


def load(name):
    scripts = ROOT / "scripts"
    sys.path.insert(0, str(scripts))
    spec = importlib.util.spec_from_file_location(name, scripts / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def manifest():
    return json.loads((ROOT / "shared-skill-surface.json").read_text(encoding="utf-8"))


def home_env(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return home


def test_native_environment_path_resolves(tmp_path, monkeypatch):
    helper = load("materialize_shared_agent_surface")
    monkeypatch.setenv("C04_PORT_ROOT", str(tmp_path / "external"))
    raw = "%C04_PORT_ROOT%/skills" if os.name == "nt" else "$C04_PORT_ROOT/skills"
    assert helper.resolve_manifest_path(tmp_path / "workspace", raw) == tmp_path / "external/skills"


def test_unresolved_environment_path_rejected(tmp_path, monkeypatch):
    helper = load("materialize_shared_agent_surface")
    monkeypatch.delenv("C04_PORT_ABSENT", raising=False)
    raw = "%C04_PORT_ABSENT%/skills" if os.name == "nt" else "$C04_PORT_ABSENT/skills"
    with pytest.raises(helper.SharedSurfaceError, match="undefined environment"):
        helper.resolve_manifest_path(tmp_path, raw)


def test_unresolvable_user_target_skipped_repo_target_fails(tmp_path, monkeypatch):
    helper = load("materialize_shared_agent_surface")
    subject = load("materialize_shared_skill_surface")
    monkeypatch.delenv("C04_PORT_ABSENT", raising=False)
    raw = "%C04_PORT_ABSENT%/skills" if os.name == "nt" else "$C04_PORT_ABSENT/skills"
    data = {"targets": {"outside": {"enabled": True, "scope": "user", "install_path": raw}}}
    skipped = []
    assert subject.build_target_roots(data, tmp_path, skipped=skipped) == {}
    assert any("unresolvable" in line for line in skipped)
    data["targets"]["outside"]["scope"] = "repo"
    with pytest.raises(helper.SharedSurfaceError, match="undefined environment"):
        subject.build_target_roots(data, tmp_path)


def test_enabled_main_targets_have_explicit_scopes():
    enabled = {name: cfg for name, cfg in manifest()["targets"].items() if cfg.get("enabled")}
    assert enabled
    assert all(cfg.get("scope") in {"repo", "user"} for cfg in enabled.values())


def test_default_scope_excludes_actual_main_home_target(tmp_path, monkeypatch):
    subject = load("materialize_shared_skill_surface")
    home = home_env(monkeypatch, tmp_path)
    workspace = tmp_path / "workspace"
    data = manifest()
    roots = subject.build_target_roots(data, workspace)
    writable = subject.writable_targets(data, roots, include_user_scope=False)
    assert Path(roots["codex"]) == home / ".codex/skills"
    assert "codex" not in writable
    assert set(writable) == {"claude", "gemini", "opencode"}
    assert all(Path(path).is_relative_to(workspace) for path in writable.values())
    assert not list(home.iterdir())


def test_legacy_unscoped_home_fails_closed(tmp_path, monkeypatch):
    subject = load("materialize_shared_skill_surface")
    home = home_env(monkeypatch, tmp_path)
    data = copy.deepcopy(manifest())
    data["targets"]["codex"].pop("scope", None)
    with pytest.raises(subject.SkillSurfaceError, match="outside"):
        subject.build_target_roots(data, tmp_path / "workspace")
    assert not list(home.iterdir())


def test_existing_relative_absolute_and_tilde_paths(tmp_path, monkeypatch):
    helper = load("materialize_shared_agent_surface")
    home = home_env(monkeypatch, tmp_path)
    workspace = tmp_path / "workspace"
    assert helper.resolve_manifest_path(workspace, "local/skills") == workspace / "local/skills"
    assert helper.resolve_manifest_path(workspace, str(home / "skills")) == home / "skills"
    assert helper.resolve_manifest_path(workspace, "~/skills") == home / "skills"


@pytest.mark.skipif(os.name != "nt", reason="approved first-publication backend is Windows-only")
def test_actual_main_corpus_cli_flow_retains_existing_projections(tmp_path, monkeypatch, capsys):
    subject = load("materialize_shared_skill_surface")
    home = home_env(monkeypatch, tmp_path)
    workspace = tmp_path / "workspace"
    source = workspace / "FLOSS/skill-corpus"
    shutil.copytree(ROOT / "skill-corpus", source)
    output = workspace / ".agent-surface/skills"
    data = manifest()
    argv = [str(ROOT / "scripts/materialize_shared_skill_surface.py"),
            "--workspace-root", str(workspace), "--manifest", str(ROOT / "shared-skill-surface.json"),
            "--output-dir", str(output)]

    def cli(*flags):
        monkeypatch.setattr(sys, "argv", argv + list(flags))
        status = subject.main()
        return status, capsys.readouterr().out

    status, text = cli("--check")
    assert status == 1, text
    assert not output.exists()
    assert not list(home.iterdir())
    status, text = cli()
    assert status == 0, text
    roots = subject.build_target_roots(data, workspace)
    registry = json.loads((output / "skill-registry.json").read_text())
    names = {entry["skill_name"] for entry in registry["skills"]}
    assert len(names) == len(data["skills"])
    installed = []
    for name in ("claude", "gemini", "opencode"):
        for skill_name in names:
            target = Path(roots[name]) / skill_name
            assert (target / subject.MANAGED_MARKER).is_file()
            installed.append(target)
    assert len(installed) == len(data["skills"]) * 3
    assert not list(home.iterdir())
    status, text = cli("--check")
    assert status == 0, text

    before = {str(path): path.read_bytes() for root in installed for path in root.rglob("*") if path.is_file()}
    first = data["skills"][0]
    source_skill = workspace / first["path"] / "SKILL.md"
    source_skill.write_bytes(source_skill.read_bytes() + b"\nSynthetic source change: retain installed learning.\n")
    status, text = cli()
    assert status == 1 and "UPDATE_DEFERRED" in text, text
    assert all(Path(path).read_bytes() == body for path, body in before.items())
    status, text = cli("--check")
    assert status == 1 and "UPDATE_DEFERRED" in text, text
    assert all(Path(path).read_bytes() == body for path, body in before.items())
    assert not list(home.iterdir())
