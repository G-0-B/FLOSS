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
import shutil
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
        assert not install_path.startswith(
            "C:/"
        ), f"{name} hardcodes an absolute Windows path; use a platform variable"


def test_a_withdrawn_skill_projection_is_removed(tmp_path):
    """The materializer visited only skills still IN the registry, so a
    withdrawn or renamed skill kept its installed directory forever and
    --check reported no drift -- the one signal an operator acts on said the
    surface matched the manifest while agents went on discovering and running
    instructions that had been deliberately retracted."""
    module = load_module()

    root = tmp_path / "skills"
    stale = root / "retired-skill"
    stale.mkdir(parents=True)
    (stale / "SKILL.md").write_text("old instructions", encoding="utf-8")
    (stale / module.MANAGED_MARKER).write_text(
        _owned_marker(tmp_path / "workspace", "retired-skill"), encoding="utf-8"
    )

    messages, drift = module.prune_stale_projections(
        "codex",
        root,
        {"still-here"},
        check=False,
        dry_run=False,
        owner_root=tmp_path / "workspace",
    )

    assert drift is True
    assert not stale.exists()
    assert any("retired-skill" in m for m in messages)


def test_an_unmanaged_directory_is_never_removed(tmp_path):
    """The marker is what makes the removal safe. Anything without it belongs
    to the operator or another tool, and this materializer has no business
    deleting it."""
    module = load_module()

    root = tmp_path / "skills"
    theirs = root / "someone-elses-skill"
    theirs.mkdir(parents=True)
    (theirs / "SKILL.md").write_text("not ours", encoding="utf-8")

    messages, drift = module.prune_stale_projections(
        "codex",
        root,
        {"still-here"},
        check=False,
        dry_run=False,
        owner_root=tmp_path / "workspace",
    )

    assert drift is False
    assert theirs.exists()
    assert messages == []


def test_check_reports_a_stale_projection_as_drift(tmp_path):
    """--check must fail on it rather than silently agreeing the surface is
    current; that silence is the whole defect."""
    module = load_module()

    root = tmp_path / "skills"
    stale = root / "retired-skill"
    stale.mkdir(parents=True)
    (stale / module.MANAGED_MARKER).write_text(
        _owned_marker(tmp_path / "workspace", "retired-skill"), encoding="utf-8"
    )

    messages, drift = module.prune_stale_projections(
        "codex",
        root,
        set(),
        check=True,
        dry_run=False,
        owner_root=tmp_path / "workspace",
    )

    assert drift is True
    assert stale.exists(), "--check must not mutate"
    assert any("DRIFT" in m for m in messages)


def _owned_marker(workspace: Path, skill_name: str) -> str:
    """A marker as serialize_marker writes it, installed by `workspace`."""
    return json.dumps(
        {
            "managed_by": "FLOSSI0ULLK shared skill surface",
            "manifest_version": "test",
            "source_path": str((workspace / "skills" / skill_name).resolve()),
            "skill_name": skill_name,
            "workspace_root": str(workspace.resolve()),
        }
    )


def test_a_projection_owned_by_another_workspace_is_never_removed(tmp_path):
    """External audit residual. The pruner checked that a marker EXISTED, not
    whose it was. On a shared user-scope root such as ~/.codex/skills, two
    checkouts install side by side, and a skill absent from THIS manifest was
    selected for removal even when another workspace had installed it -- so
    refreshing one workspace could delete another's live instructions.

    A projection is ours to remove only if its marker names this workspace as
    the one that installed it."""
    module = load_module()

    root = tmp_path / "skills"
    theirs = root / "their-skill"
    theirs.mkdir(parents=True)
    # A LIVE other workspace: one that exists. A marker naming a workspace
    # that is gone is reported (see the moved-workspace test); a live one is
    # simply someone else's, and silence is right.
    (tmp_path / "other-workspace").mkdir()
    (theirs / module.MANAGED_MARKER).write_text(
        _owned_marker(tmp_path / "other-workspace", "their-skill"), encoding="utf-8"
    )

    for check, dry_run in ((True, False), (False, True), (False, False)):
        messages, drift = module.prune_stale_projections(
            "codex",
            root,
            set(),
            check=check,
            dry_run=dry_run,
            owner_root=tmp_path / "this-workspace",
        )
        assert (
            theirs.exists()
        ), f"another workspace's projection was removed ({check=}, {dry_run=})"
        assert drift is False, "someone else's projection is not this workspace's drift"
        assert messages == [], messages


def test_a_marker_that_cannot_prove_ownership_is_left_alone(tmp_path):
    """Unparseable, empty, or missing source_path: none of those prove the
    projection is ours, and deleting on an unproven claim is the failure this
    guards. Leaving a stale directory is recoverable; deleting a live one is
    not."""
    module = load_module()

    root = tmp_path / "skills"
    for name, marker in (
        ("unparseable", "not json{"),
        ("empty-object", "{}"),
        ("no-source", json.dumps({"managed_by": "FLOSSI0ULLK shared skill surface"})),
        (
            "wrong-owner",
            json.dumps({"managed_by": "someone else", "source_path": str(tmp_path)}),
        ),
    ):
        victim = root / name
        victim.mkdir(parents=True)
        (victim / module.MANAGED_MARKER).write_text(marker, encoding="utf-8")

    messages, drift = module.prune_stale_projections(
        "codex", root, set(), check=False, dry_run=False, owner_root=tmp_path
    )

    assert drift is False
    assert sorted(p.name for p in root.iterdir()) == sorted(
        ["unparseable", "empty-object", "no-source", "wrong-owner"]
    )


def _workspace_with_skills(root: Path, names: list[str]) -> Path:
    for name in names:
        skill = root / "skills" / name
        skill.mkdir(parents=True, exist_ok=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: a test skill\n---\nbody\n",
            encoding="utf-8",
        )
    return root


def _refresh(module, workspace: Path, listed: list[str], shared: Path) -> list[str]:
    """One real materialize() run of `workspace` into a shared user-scope root."""
    manifest = workspace / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "manifest_version": "test",
                "targets": {
                    "shared": {
                        "enabled": True,
                        "install_path": str(shared),
                        "scope": "user",
                    }
                },
                "skills": [{"path": f"skills/{name}"} for name in listed],
            }
        ),
        encoding="utf-8",
    )
    messages, _drift = module.materialize(
        workspace,
        manifest,
        workspace / "out",
        check=False,
        dry_run=False,
        include_user_scope=True,
    )
    return messages


def test_refreshing_either_of_two_nested_workspaces_keeps_the_others_projections(
    tmp_path,
):
    """Second external audit, F3. Ownership was source ANCESTRY: a projection
    was ours if its source lived anywhere under our root. That protects
    sibling workspaces but not nested ones -- a checkout inside another
    workspace has every source under the outer root, so refreshing the outer
    workspace selected the nested one's live projections for removal whenever
    its own manifest did not list them.

    Driven through materialize(), with markers written by the real
    serializer, into one shared user-scope root."""
    module = load_module()
    outer = _workspace_with_skills(tmp_path / "outer", ["outer-skill"])
    nested = _workspace_with_skills(outer / "checkouts" / "nested", ["nested-skill"])
    shared = tmp_path / "shared-user-skills"

    _refresh(module, outer, ["outer-skill"], shared)
    _refresh(module, nested, ["nested-skill"], shared)
    assert (shared / "outer-skill").is_dir()
    assert (shared / "nested-skill").is_dir()

    _refresh(module, nested, ["nested-skill"], shared)
    assert (shared / "outer-skill").is_dir(), "nested refresh removed its parent's"

    _refresh(module, outer, ["outer-skill"], shared)
    assert (shared / "nested-skill").is_dir(), "outer refresh removed a nested one's"


def test_a_workspace_still_prunes_its_own_withdrawn_projection(tmp_path):
    """Replaces a test that read materialize()'s SOURCE for the text
    `owner_root=workspace_root`, which could not see whether the owner passed
    was one the markers would match. This drives the real caller: install two
    skills, withdraw one, refresh. A guard on the join between the caller, the
    writer and the reader -- it passes before and after the identity fix."""
    module = load_module()
    workspace = _workspace_with_skills(tmp_path / "workspace", ["kept", "withdrawn"])
    shared = tmp_path / "shared-user-skills"

    _refresh(module, workspace, ["kept", "withdrawn"], shared)
    _refresh(module, workspace, ["kept"], shared)

    assert not (shared / "withdrawn").exists()
    assert (shared / "kept").is_dir()


def test_a_relative_workspace_identity_proves_nothing(tmp_path, monkeypatch):
    """A relative path resolves against the current directory, so ownership
    would depend on where the materializer happened to be run from. The audit
    showed `source_path: "."` claimed by any owner containing the cwd."""
    module = load_module()
    owner = tmp_path / "workspace"
    owner.mkdir()
    projection = tmp_path / "installed" / "relative-marker"
    projection.mkdir(parents=True)
    (projection / module.MANAGED_MARKER).write_text(
        json.dumps(
            {
                "managed_by": module.MANAGED_BY,
                "source_path": ".",
                "workspace_root": ".",
                "skill_name": "relative-marker",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(owner)

    assert not module.projection_owned_by(projection, owner)


def test_a_marker_without_workspace_identity_is_kept_and_reported(tmp_path):
    """Markers written before the identity field existed cannot say who
    installed them, so they are never removed. They ARE reported: the defect
    this pruner exists for was a withdrawn skill lingering silently, and a
    legacy marker from this workspace's own withdrawn skill is exactly that.
    Not drift, because this workspace cannot resolve it without a human."""
    module = load_module()
    workspace = tmp_path / "workspace"
    root = tmp_path / "skills"
    legacy = root / "legacy-skill"
    legacy.mkdir(parents=True)
    (legacy / module.MANAGED_MARKER).write_text(
        json.dumps(
            {
                "managed_by": module.MANAGED_BY,
                "manifest_version": "old",
                "source_path": str((workspace / "skills" / "legacy-skill").resolve()),
                "skill_name": "legacy-skill",
            }
        ),
        encoding="utf-8",
    )

    for check, dry_run in ((True, False), (False, True), (False, False)):
        messages, drift = module.prune_stale_projections(
            "codex",
            root,
            set(),
            check=check,
            dry_run=dry_run,
            owner_root=workspace,
        )
        assert legacy.exists(), f"a legacy marker was removed ({check=}, {dry_run=})"
        assert drift is False
        assert any(
            "legacy-skill" in m and "identity" in m for m in messages
        ), messages


def test_a_marker_this_materializer_writes_is_one_it_recognises_as_owned(tmp_path):
    """The join between the writer and the reader of the ownership claim.

    Three defects on this PR were a manifest and its reader disagreeing about
    what one end wrote. If serialize_marker and projection_owned_by ever
    diverge -- a renamed key, a changed managed_by string, an unresolved path
    -- every projection this workspace installed would silently become
    unprunable, and the withdrawal fix would stop working without a failure.
    """
    module = load_module()

    workspace = tmp_path / "workspace"
    source = workspace / "skills" / "real-skill"
    source.mkdir(parents=True)
    projection = tmp_path / "installed" / "real-skill"
    projection.mkdir(parents=True)
    (projection / module.MANAGED_MARKER).write_text(
        module.serialize_marker(
            {"skill_name": "real-skill", "resolved_path": str(source.resolve())},
            "test",
            workspace,
        ),
        encoding="utf-8",
    )

    assert module.projection_owned_by(projection, workspace)
    assert not module.projection_owned_by(projection, tmp_path / "elsewhere")
    # The parent contains the source too; containment is not installation.
    assert not module.projection_owned_by(projection, workspace.parent)


@pytest.mark.parametrize(
    "payload",
    [
        b"\xff\xfe not utf-8",
        b'{"skills": ' + b"9" * 5000 + b"}",
        b"[" * 100_000 + b"]" * 100_000,
    ],
    ids=["invalid-utf8", "integer-past-the-digit-limit", "nesting-past-the-recursion-limit"],
)
def test_an_unreadable_manifest_is_a_skill_surface_error(tmp_path, payload):
    """The same narrow `except json.JSONDecodeError` the gateway.pid fix
    widened, in this module's own manifest loader."""
    module = load_module()
    path = tmp_path / "manifest.json"
    path.write_bytes(payload)

    with pytest.raises(module.SkillSurfaceError):
        module.load_manifest(path)


# ---------------------------------------------------------------------------
# Third external audit: F4, O1 and O4.
# ---------------------------------------------------------------------------


def _posix_realpath(monkeypatch):
    """Make path resolution reject an embedded NUL the way POSIX does.

    On POSIX, os.path.realpath reaches os.lstat, which raises ValueError
    ("embedded null byte"). Windows resolution does not raise, which is why
    the Windows suite never saw F4. This reproduces the POSIX behaviour on
    every platform, and changes nothing where it already holds.
    """
    real = os.path.realpath

    def realpath(path, *args, **kwargs):
        if "\x00" in os.fspath(path):
            raise ValueError("embedded null byte")
        return real(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", realpath)


def _marker_with_identity(module, name: str, identity) -> str:
    return json.dumps(
        {"managed_by": module.MANAGED_BY, "skill_name": name, "workspace_root": identity}
    )


def test_an_identity_the_os_cannot_resolve_is_unknown_not_a_crash(
    tmp_path, monkeypatch
):
    """Third audit, F4. The comparison caught only OSError, and on POSIX an
    absolute identity containing a NUL raises ValueError from resolve(). One
    such marker aborted the pruner and the materializer around it, even in
    --check. Unreadable ownership is not ownership, and that has to hold in
    the path normalisation too."""
    _posix_realpath(monkeypatch)
    module = load_module()
    projection = tmp_path / "installed" / "bad-identity"
    projection.mkdir(parents=True)
    (projection / module.MANAGED_MARKER).write_text(
        _marker_with_identity(
            module, "bad-identity", str((tmp_path / "ws").resolve()) + "\x00tail"
        ),
        encoding="utf-8",
    )

    assert module.projection_owned_by(projection, tmp_path / "ws") is False


def test_a_marker_the_os_cannot_resolve_does_not_stop_the_refresh(
    tmp_path, monkeypatch
):
    """The consequence, through the real caller: the bad marker sorts first,
    and the workspace's own withdrawn projection after it must still be
    pruned, with the bad one kept and reported."""
    _posix_realpath(monkeypatch)
    module = load_module()
    workspace = _workspace_with_skills(tmp_path / "workspace", ["kept", "withdrawn"])
    shared = tmp_path / "shared-user-skills"
    _refresh(module, workspace, ["kept", "withdrawn"], shared)
    bad = shared / "a-bad-identity"
    bad.mkdir()
    (bad / module.MANAGED_MARKER).write_text(
        _marker_with_identity(
            module, "a-bad-identity", str(workspace.resolve()) + "\x00tail"
        ),
        encoding="utf-8",
    )

    messages = _refresh(module, workspace, ["kept"], shared)

    assert bad.is_dir(), "a marker nobody can resolve was removed"
    assert not (shared / "withdrawn").exists(), "processing stopped at the bad marker"
    assert any("a-bad-identity" in m and m.startswith("KEEP") for m in messages), messages


@pytest.mark.parametrize(
    "identity", [".", 42, "", None], ids=["relative", "number", "empty", "null"]
)
def test_a_marker_with_an_unusable_identity_is_kept_and_reported(tmp_path, identity):
    """Third audit, O4. Only a MISSING identity produced a KEEP line; one that
    was present but unusable was kept in silence. Both mean the same thing,
    ownership unknown, and a stale projection nobody can prune is the defect
    the pruner exists to surface."""
    module = load_module()
    root = tmp_path / "skills"
    child = root / "unusable"
    child.mkdir(parents=True)
    (child / module.MANAGED_MARKER).write_text(
        _marker_with_identity(module, "unusable", identity), encoding="utf-8"
    )

    messages, drift = module.prune_stale_projections(
        "codex", root, set(), check=False, dry_run=False, owner_root=tmp_path / "ws"
    )

    assert child.exists()
    assert drift is False
    assert any("unusable" in m and m.startswith("KEEP") for m in messages), messages


def test_a_marker_from_a_workspace_that_no_longer_exists_is_kept_and_reported(
    tmp_path,
):
    """Third audit, O4. A moved or deleted workspace leaves markers that name
    a root nobody can refresh from, so no run will ever prune them. They are
    kept, as any foreign projection is, but said out loud.

    Said carefully: os.path.exists is also False for an unmounted drive or an
    unreachable network path, so the line must not tell an operator the
    workspace is gone, nor invite them to delete a live workspace's skill."""
    module = load_module()
    root = tmp_path / "skills"
    orphan = root / "orphan"
    orphan.mkdir(parents=True)
    (orphan / module.MANAGED_MARKER).write_text(
        _owned_marker(tmp_path / "moved-away", "orphan"), encoding="utf-8"
    )

    messages, drift = module.prune_stale_projections(
        "codex", root, set(), check=False, dry_run=False, owner_root=tmp_path / "ws"
    )

    assert orphan.exists()
    assert drift is False
    assert any(
        "orphan" in m
        and m.startswith("KEEP")
        and "cannot be found" in m
        and "not mounted" in m
        and "delete it by hand" not in m
        for m in messages
    ), messages


def test_a_marker_only_change_never_takes_the_installed_skill_away(
    tmp_path, monkeypatch
):
    """Third audit, O1. Adding `workspace_root` changed every installed
    marker, and install replaced a projection by deleting it and copying the
    source back. So the migration put every unchanged skill through a window
    in which an interrupted run left it missing until the next one. When only
    the marker differs, only the marker is rewritten."""
    module = load_module()
    workspace = _workspace_with_skills(tmp_path / "workspace", ["steady"])
    skill = module.resolve_skill_entry(workspace, {"path": "skills/steady"})
    target_root = tmp_path / "installed"
    installed = target_root / "steady"
    shutil.copytree(skill["resolved_path"], installed)
    legacy = json.loads(module.serialize_marker(skill, "test", workspace))
    del legacy["workspace_root"]
    (installed / module.MANAGED_MARKER).write_text(json.dumps(legacy), encoding="utf-8")

    def refuse(*args, **kwargs):
        raise AssertionError("the installed skill was taken down for a marker change")

    monkeypatch.setattr(module, "remove_path", refuse)
    monkeypatch.setattr(module.shutil, "copytree", refuse)

    _messages, changed = module.install_skill_projection(
        "codex",
        skill,
        target_root,
        "test",
        check=False,
        dry_run=False,
        workspace_root=workspace,
    )

    assert changed is True
    marker = json.loads((installed / module.MANAGED_MARKER).read_text(encoding="utf-8"))
    assert marker["workspace_root"] == str(workspace.resolve())
    assert (installed / "SKILL.md").read_text(encoding="utf-8") == (
        Path(skill["resolved_path"]) / "SKILL.md"
    ).read_text(encoding="utf-8")
