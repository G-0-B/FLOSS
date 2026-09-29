"""Materialize the shared FLOSSI0ULLK skill surface into generated artifacts.

Canonical source of truth:
  - `FLOSS/shared-skill-surface.json`
  - `FLOSS/skill-corpus/*`

Generated artifacts:
  - `.agent-surface/skills/SKILL_INDEX.md`
  - `.agent-surface/skills/skill-registry.json`
  - agent-native skill projections for configured targets such as:
    - `%USERPROFILE%/.codex/skills/flossi0ullk-*`
    - `.claude/skills/flossi0ullk-*`
    - `.gemini/skills/flossi0ullk-*`
    - `opworkers/.opencode/skills/flossi0ullk-*`
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-skill-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "skills"
MANAGED_MARKER = ".flossi0ullk-managed.json"
# Written into every marker and checked before any removal. One constant for
# both, because the pruner deciding ownership by comparing against a second
# copy of this string is how the two would drift apart.
MANAGED_BY = "FLOSSI0ULLK shared skill surface"


class SkillSurfaceError(Exception):
    """Raised for manifest, source, or projection errors."""


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SkillSurfaceError(f"Missing manifest: {path}") from exc
    # ValueError covers JSONDecodeError, invalid UTF-8 and an integer past the
    # digit limit; deep nesting raises RecursionError.
    except (ValueError, RecursionError) as exc:
        raise SkillSurfaceError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise SkillSurfaceError(f"Expected JSON object in {path}")
    if not isinstance(payload.get("skills"), list):
        raise SkillSurfaceError(f"{path} must contain a list-valued `skills` field")
    return payload


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SkillSurfaceError(f"Missing file: {path}") from exc


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = read_text(skill_md)
    if not text.startswith("---\n"):
        raise SkillSurfaceError(f"{skill_md} must start with YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise SkillSurfaceError(f"{skill_md} must contain closing YAML frontmatter")
    raw_frontmatter = parts[1]
    try:
        payload = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        raise SkillSurfaceError(
            f"Invalid YAML frontmatter in {skill_md}: {exc}"
        ) from exc

    if not isinstance(payload, dict):
        raise SkillSurfaceError(f"{skill_md} frontmatter must parse to a YAML mapping")

    name = payload.get("name")
    description = payload.get("description")
    if not isinstance(name, str) or not isinstance(description, str):
        raise SkillSurfaceError(
            f"{skill_md} frontmatter must include string `name` and `description`"
        )
    return {"name": name, "description": description}


def resolve_skill_entry(workspace_root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise SkillSurfaceError(
            "Every skill entry must contain a non-empty string `path`"
        )
    # Normalize separators before joining. A manifest entry written as
    # `FLOSS/skill-corpus\superpowers-brainstorming` is a single literal
    # filename component on POSIX -- pathlib does not treat a backslash as a
    # separator there -- so resolve_skill_entry raised SkillSurfaceError and the
    # whole skill step failed on Linux and macOS before any projection was
    # written. The manifest is fixed too; this keeps one bad entry from taking
    # the step down again.
    skill_dir = (workspace_root / raw_path.replace("\\", "/")).resolve()
    skill_md = skill_dir / "SKILL.md"
    if not skill_dir.is_dir():
        raise SkillSurfaceError(f"Skill path is not a directory: {skill_dir}")
    frontmatter = parse_frontmatter(skill_md)
    resolved = dict(entry)
    resolved["resolved_path"] = str(skill_dir)
    resolved["skill_name"] = frontmatter["name"]
    resolved["description"] = frontmatter["description"]
    resolved["files"] = collect_source_snapshot(skill_dir)
    return resolved


def collect_source_snapshot(skill_dir: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(skill_dir.rglob("*")):
        if path.is_dir():
            continue
        rel = path.relative_to(skill_dir).as_posix()
        snapshot[rel] = path.read_text(encoding="utf-8")
    return snapshot


def resolve_install_path(workspace_root: Path, raw_path: str) -> Path:
    """Resolve a target's `install_path` through the one shared resolver.

    This used to be `Path(raw_path).expanduser()` plus a workspace join, which
    expands `~` but NOT `%LOCALAPPDATA%`/`$VAR`. A manifest path like
    `%LOCALAPPDATA%/hermes/skills` is not absolute before expansion, so it was
    joined to the workspace and the materializer created a literal
    `<workspace>/%LOCALAPPDATA%/hermes/skills` tree. The hermes target dodged
    that only by hardcoding one machine's absolute Windows path, which on POSIX
    is not absolute either and produced a literal `C:/Users/kalis/...` directory
    inside the repo.

    `resolve_manifest_path` in the sibling agent-surface module already handles
    `~`, `%VAR%`, and `$VAR`, and fails loudly on an undefined variable rather
    than passing the literal through. Imported lazily for the same reason
    `materialize_shared_hook_surface.resolve_target_path` does it lazily: the
    agent-surface module imports the hook module at load time, and routing all
    three through one resolver is worth more than avoiding the deferred import.
    """
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from materialize_shared_agent_surface import (  # noqa: E402
        resolve_manifest_path,
    )

    return resolve_manifest_path(workspace_root, raw_path)


def skill_target_in_scope(
    target_name: str, target_cfg: dict[str, Any], include_user_scope: bool
) -> bool:
    """Repo-scope targets always; user-scope targets only on the explicit opt-in.

    This module had no scope gate at all while its siblings did, and two of its
    targets write outside the repository -- `~/.codex/skills` and the Hermes
    skills directory. An ordinary `refresh_agent_surfaces.py` with no
    `--include-user-scope` therefore rewrote machine-wide state from a
    repo-scope run, which is exactly the hole that was closed for the hook and
    agent surfaces.

    A target with no declared `scope` is treated as `repo`, matching the
    sibling modules.
    """
    scope = str(target_cfg.get("scope", "repo")).strip().lower() or "repo"
    if scope not in {"repo", "user"}:
        raise SkillSurfaceError(
            f"Target {target_name!r} declares unknown scope {scope!r}; "
            "expected 'repo' or 'user'"
        )
    return scope == "repo" or include_user_scope


def assert_repo_scope_stays_inside(
    target_name: str, target_cfg: dict[str, Any], resolved: Path, workspace_root: Path
) -> None:
    """A `scope: "repo"` target must resolve inside the workspace.

    The declared scope and the resolved path have to agree, or `scope: "repo"`
    plus an absolute install path would be a way to write user-scope locations
    from a run that never asked for user scope.
    """
    if str(target_cfg.get("scope", "repo")).strip().lower() not in {"", "repo"}:
        return
    root = workspace_root.resolve()
    try:
        resolved.resolve().relative_to(root)
    except ValueError:
        raise SkillSurfaceError(
            f"Target {target_name!r} declares scope 'repo' but its install_path "
            f"resolves to {resolved}, outside {root}. Writing outside the "
            'repository is user scope: declare `"scope": "user"` and pass '
            "--include-user-scope."
        ) from None


def build_target_roots(
    manifest: dict[str, Any],
    workspace_root: Path,
    *,
    skipped: list[str] | None = None,
) -> dict[str, str]:
    """Resolved roots for every enabled target, scope-independent.

    Deliberately NOT filtered by `--include-user-scope`: these roots go into the
    generated registry, and a generated artifact whose contents depend on a
    runtime flag would drift back and forth between a plain refresh and a
    user-scope one, with `--check` calling each of them dirty in turn. The flag
    decides what gets WRITTEN (`writable_targets` below), not what the manifest
    says exists.
    """
    targets = manifest.get("targets", {})
    if not isinstance(targets, dict):
        raise SkillSurfaceError("Manifest `targets` must be a JSON object")
    if skipped is None:
        skipped = []

    roots: dict[str, str] = {}
    for target_name, target_cfg in targets.items():
        if not isinstance(target_cfg, dict):
            raise SkillSurfaceError(f"Target {target_name!r} must be a JSON object")
        if not target_cfg.get("enabled"):
            continue
        install_path = target_cfg.get("install_path")
        if not isinstance(install_path, str) or not install_path.strip():
            raise SkillSurfaceError(
                f"Enabled target {target_name!r} must define `install_path`"
            )
        try:
            resolved = resolve_install_path(workspace_root, install_path)
        except Exception as exc:  # SharedSurfaceError from the shared resolver
            # A user-scope target whose variable is undefined on this platform
            # is skipped, not fatal: a POSIX run has no %LOCALAPPDATA%, and the
            # whole skill step failing there would take every repo-scope
            # projection down with it. A repo-scope target still raises.
            if str(target_cfg.get("scope", "repo")).strip().lower() == "user":
                skipped.append(f"skip {target_name}: unresolvable here ({exc})")
                continue
            raise
        assert_repo_scope_stays_inside(
            target_name, target_cfg, resolved, workspace_root
        )
        roots[target_name] = str(resolved)
    return roots


def writable_targets(
    manifest: dict[str, Any],
    target_roots: dict[str, str],
    *,
    include_user_scope: bool,
    skipped: list[str] | None = None,
) -> dict[str, str]:
    """The subset of resolved roots this run is allowed to write."""
    if skipped is None:
        skipped = []
    targets = manifest.get("targets", {})
    writable: dict[str, str] = {}
    for target_name, root in target_roots.items():
        target_cfg = targets.get(target_name) or {}
        if skill_target_in_scope(target_name, target_cfg, include_user_scope):
            writable[target_name] = root
        else:
            skipped.append(
                f"skip {target_name}: user-scope target "
                "(pass --include-user-scope to write it)"
            )
    return writable


def build_registry(
    manifest: dict[str, Any], workspace_root: Path, target_roots: dict[str, str]
) -> dict[str, Any]:
    skills: list[dict[str, Any]] = []
    for entry in manifest["skills"]:
        if not isinstance(entry, dict):
            raise SkillSurfaceError("Every skill entry must be a JSON object")
        resolved = resolve_skill_entry(workspace_root, entry)
        resolved["install_targets"] = {
            target_name: str(Path(root) / resolved["skill_name"])
            for target_name, root in target_roots.items()
        }
        skills.append(resolved)

    return {
        "manifest_version": manifest.get("manifest_version", "?"),
        "workspace_id": manifest.get("workspace_id", "workspace"),
        "workspace_name": manifest.get("workspace_name", "workspace"),
        "portable_skill_root": manifest.get(
            "portable_skill_root", "FLOSS/skill-corpus"
        ),
        "rules": manifest.get("rules", []),
        "upstream_candidates": manifest.get("upstream_candidates", []),
        "targets": manifest.get("targets", {}),
        "target_roots": target_roots,
        "skills": skills,
    }


def build_index(registry: dict[str, Any]) -> str:
    lines = [
        "# Shared Skill Index",
        "",
        f"Workspace: `{registry['workspace_name']}`",
        f"Workspace ID: `{registry['workspace_id']}`",
        f"Manifest version: `{registry['manifest_version']}`",
        "",
        "## Operating Rules",
        "",
    ]
    for rule in registry.get("rules", []):
        lines.append(f"- {rule}")
    lines.extend(
        [
            "",
            "## Skills",
            "",
        ]
    )
    for skill in registry["skills"]:
        lines.extend(
            [
                f"### `{skill['skill_name']}`",
                f"- Category: `{skill.get('category', 'uncategorized')}`",
                f"- Summary: {skill.get('summary', '')}",
                f"- Description: {skill['description']}",
                f"- Source: `{skill['resolved_path']}`",
            ]
        )
        install_targets = skill.get("install_targets", {})
        if install_targets:
            lines.append("- Install targets:")
            for target_name, target_path in install_targets.items():
                lines.append(f"  - `{target_name}`: `{target_path}`")
        upstreams = skill.get("upstreams", [])
        if upstreams:
            lines.append("- Upstreams:")
            for upstream in upstreams:
                lines.append(f"  - `{upstream}`")
        lines.append("")

    upstreams = registry.get("upstream_candidates", [])
    if upstreams:
        lines.extend(
            [
                "## Upstream Candidates",
                "",
            ]
        )
        for upstream in upstreams:
            lines.append(
                f"- `{upstream.get('id', '?')}`: {upstream.get('repo', '?')} - {upstream.get('role', '')}"
            )
        lines.append("")

    lines.extend(
        [
            "## Generated By",
            "",
            "- `FLOSS/scripts/materialize_shared_skill_surface.py`",
        ]
    )
    return "\n".join(lines)


def check_or_write(
    path: Path, content: str, *, check: bool, dry_run: bool
) -> tuple[str, bool]:
    changed = True
    if path.exists():
        changed = path.read_text(encoding="utf-8") != content
    if check:
        return (f"CHECK {'DRIFT' if changed else 'OK'} {path}", changed)
    if dry_run:
        return (f"PLAN  {'WRITE' if changed else 'KEEP'} {path}", changed)
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return (f"WROTE {path}", changed)
    return (f"OK    {path}", changed)


def check_or_write_json(
    path: Path, payload: dict[str, Any], *, check: bool, dry_run: bool
) -> tuple[str, bool]:
    content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    return check_or_write(path, content, check=check, dry_run=dry_run)


def serialize_marker(
    skill: dict[str, Any], manifest_version: str, workspace_root: Path
) -> str:
    payload = {
        "managed_by": MANAGED_BY,
        "manifest_version": manifest_version,
        "source_path": skill["resolved_path"],
        "skill_name": skill["skill_name"],
        # WHO INSTALLED THIS, recorded rather than inferred. See
        # projection_owned_by: source ancestry cannot tell a workspace from one
        # nested inside it.
        "workspace_root": str(workspace_root.resolve()),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def read_managed_marker(child: Path) -> dict[str, Any] | None:
    """The marker, if it is one this materializer wrote; otherwise None."""

    try:
        marker = json.loads((child / MANAGED_MARKER).read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError):
        return None
    if not isinstance(marker, dict) or marker.get("managed_by") != MANAGED_BY:
        return None
    return marker


def projection_owned_by(child: Path, owner_root: Path) -> bool:
    """True only if the marker names `owner_root` as the installing workspace.

    Ownership has to be CHECKED, not assumed from the marker's existence:
    user-scope roots such as ~/.codex/skills are shared by every checkout on
    the machine, so a skill absent from THIS manifest may be a live skill
    another workspace installed.

    It used to be checked by source ANCESTRY -- ours if `source_path` resolved
    under `owner_root`. That separates sibling workspaces and nothing else: a
    checkout nested inside another workspace has every source under the outer
    root, so refreshing the outer workspace claimed and pruned the nested one's
    live projections. Containment is not installation. The marker now records
    the installing workspace's root, and only an exact match is ours.

    Anything that cannot prove ownership -- unreadable, not an object, wrong
    `managed_by`, no `workspace_root`, a relative one (which would resolve
    against whatever directory the run started in), or one the OS cannot
    resolve -- is not ours. Leaving a stale directory is recoverable; deleting
    a live one is not.
    """

    marker = read_managed_marker(child)
    if marker is None:
        return False
    recorded = recorded_workspace(marker)
    if recorded is None:
        return False
    try:
        owner = owner_root.resolve()
    except (OSError, ValueError):
        return False
    return os.path.normcase(str(recorded)) == os.path.normcase(str(owner))


def recorded_workspace(marker: dict[str, Any]) -> Path | None:
    """The installing workspace a marker names, resolved; None if unusable.

    ValueError as well as OSError: on POSIX an absolute identity containing a
    NUL raises ValueError from resolve(), and catching only OSError let one
    such marker abort the pruner and the materializer around it, `--check`
    included. Windows resolves the same string without raising, which is why
    the Windows suite never saw it. Found by the third external audit (F4).
    """

    recorded = marker.get("workspace_root")
    if not isinstance(recorded, str) or not Path(recorded).is_absolute():
        return None
    try:
        return Path(recorded).resolve()
    except (OSError, ValueError):
        return None


def prune_stale_projections(
    target_name: str,
    target_root: Path,
    expected: set[str],
    *,
    check: bool,
    dry_run: bool,
    owner_root: Path,
) -> tuple[list[str], bool]:
    """Remove managed projections whose skill has left the manifest.

    The materializer only ever visited skills still IN the registry, so a
    withdrawn or renamed skill kept its installed directory forever and
    `--check` reported no drift -- the one signal an operator would act on said
    the surface matched the manifest while agents went on discovering and
    executing instructions that had been deliberately retracted. Renames were
    the worst shape: the new name installs beside the old one and both are
    live.

    ONLY directories carrying MANAGED_MARKER are touched. Everything else under
    the target root belongs to the operator or another tool, and this
    materializer has no business deleting it -- the marker is what makes the
    removal safe, and it is why enumerating here is possible at all.
    """

    results: list[str] = []
    drift_found = False
    if not target_root.exists():
        return results, drift_found

    for child in sorted(target_root.iterdir()):
        if not child.is_dir() or child.name in expected:
            continue
        if not (child / MANAGED_MARKER).is_file():
            # Unmanaged. Not ours, and silence is the correct behaviour.
            continue
        if not projection_owned_by(child, owner_root):
            # MANAGED, BUT NOT BY US. The first version stopped at the marker's
            # existence, so on a shared user-scope root it planned to remove
            # another workspace's live projection whenever this manifest
            # happened not to list that skill. Found by the external audit.
            #
            # Two kinds of foreign projection are never removed but ARE said
            # out loud, because a withdrawn skill lingering in silence is the
            # defect this pruner exists for, and either kind may be this
            # workspace's own:
            #   - no usable identity: written before markers recorded one, or
            #     recording something that is not an absolute, resolvable
            #     path. No workspace can prove it owns this.
            #   - an identity naming a workspace that no longer exists: moved
            #     or deleted, so no run will ever prune it.
            # A live other workspace's projection is simply someone else's,
            # and silence is right.
            marker = read_managed_marker(child)
            if marker is not None:
                recorded = recorded_workspace(marker)
                if recorded is None:
                    results.append(
                        f"KEEP  {target_name}: {child.name} has a managed marker "
                        f"with no usable installing-workspace identity (missing "
                        f"or invalid); ownership unknown, left in place (delete "
                        f"it by hand if it is stale)"
                    )
                elif not os.path.exists(recorded):
                    results.append(
                        f"KEEP  {target_name}: {child.name} was installed by "
                        f"{recorded}, which no longer exists; left in place "
                        f"(delete it by hand if it is stale)"
                    )
            continue
        drift_found = True
        if check:
            results.append(
                f"DRIFT {target_name}: {child.name} is an installed managed "
                f"projection with no skill in the manifest (withdrawn or renamed)"
            )
        elif dry_run:
            results.append(f"would remove {target_name}: {child.name} (stale)")
        else:
            remove_path(child)
            results.append(f"removed {target_name}: {child.name} (stale)")
    return results, drift_found


def install_skill_projection(
    target_name: str,
    skill: dict[str, Any],
    target_root: Path,
    manifest_version: str,
    *,
    check: bool,
    dry_run: bool,
    workspace_root: Path,
) -> tuple[list[str], bool]:
    target_dir = target_root / skill["skill_name"]
    source_dir = Path(skill["resolved_path"])
    results: list[str] = []
    drift_found = False
    expected_snapshot = dict(skill["files"])
    expected_snapshot[MANAGED_MARKER] = serialize_marker(
        skill, manifest_version, workspace_root
    )

    actual_snapshot: dict[str, str] = {}
    if target_dir.exists():
        for path in sorted(target_dir.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(target_dir).as_posix()
            actual_snapshot[rel] = path.read_text(encoding="utf-8")

    changed = actual_snapshot != expected_snapshot
    if check:
        return ([f"CHECK {'DRIFT' if changed else 'OK'} {target_dir}"], changed)
    if dry_run:
        return (
            [f"PLAN  {'WRITE' if changed else 'KEEP'} {target_name}:{target_dir}"],
            changed,
        )
    if not changed:
        return ([f"OK    {target_dir}"], False)

    def without_marker(snapshot: dict[str, str]) -> dict[str, str]:
        return {rel: text for rel, text in snapshot.items() if rel != MANAGED_MARKER}

    if without_marker(actual_snapshot) == without_marker(expected_snapshot):
        # ONLY THE MARKER DIFFERS: rewrite it in place, never take the skill
        # away. The path below deletes the projection before copying the source
        # back, so a run interrupted between the two leaves the skill missing
        # until the next one. That ordering predates the `workspace_root`
        # field, but adding the field changed every installed marker and so
        # put every unchanged skill through that window once. Found by the
        # third external audit (O1). A plain write, not a temp-and-replace:
        # a marker torn mid-write reads as unowned, which is safe, and the
        # next run rewrites it.
        (target_dir / MANAGED_MARKER).write_text(
            expected_snapshot[MANAGED_MARKER],
            encoding="utf-8",
        )
        return ([f"WROTE {target_dir} (marker only)"], True)

    remove_path(target_dir)
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    (target_dir / MANAGED_MARKER).write_text(
        expected_snapshot[MANAGED_MARKER],
        encoding="utf-8",
    )
    results.append(f"WROTE {target_dir}")
    drift_found = True
    return results, drift_found


def materialize(
    workspace_root: Path,
    manifest_path: Path,
    output_dir: Path,
    *,
    check: bool,
    dry_run: bool,
    include_user_scope: bool = False,
) -> tuple[list[str], bool]:
    manifest = load_manifest(manifest_path)
    skipped: list[str] = []
    target_roots = build_target_roots(manifest, workspace_root, skipped=skipped)
    registry = build_registry(manifest, workspace_root, target_roots)
    writable = writable_targets(
        manifest,
        target_roots,
        include_user_scope=include_user_scope,
        skipped=skipped,
    )
    index = build_index(registry)

    results: list[str] = list(skipped)
    drift_found = False

    registry_path = output_dir / "skill-registry.json"
    message, changed = check_or_write_json(
        registry_path, registry, check=check, dry_run=dry_run
    )
    results.append(message)
    drift_found = drift_found or changed

    index_path = output_dir / "SKILL_INDEX.md"
    message, changed = check_or_write(index_path, index, check=check, dry_run=dry_run)
    results.append(message)
    drift_found = drift_found or changed

    expected_names = {skill["skill_name"] for skill in registry["skills"]}
    for target_name, root in writable.items():
        target_root = Path(root)
        # Prune BEFORE installing. A rename drops the old name and adds the new
        # one in the same manifest edit, and pruning afterwards would be racing
        # a directory this run has just written.
        messages, changed = prune_stale_projections(
            target_name,
            target_root,
            expected_names,
            check=check,
            dry_run=dry_run,
            owner_root=workspace_root,
        )
        results.extend(messages)
        drift_found = drift_found or changed
        for skill in registry["skills"]:
            messages, changed = install_skill_projection(
                target_name,
                skill,
                target_root,
                registry["manifest_version"],
                check=check,
                dry_run=dry_run,
                workspace_root=workspace_root,
            )
            results.extend(messages)
            drift_found = drift_found or changed

    return results, drift_found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize the FLOSSI0ULLK shared skill surface"
    )
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--include-user-scope",
        action="store_true",
        help=(
            'also write targets declaring `"scope": "user"`, which live '
            "outside the repository (e.g. ~/.codex/skills)"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results, drift_found = materialize(
        workspace_root=args.workspace_root.resolve(),
        manifest_path=args.manifest.resolve(),
        output_dir=args.output_dir.resolve(),
        check=args.check,
        dry_run=args.dry_run,
        include_user_scope=args.include_user_scope,
    )
    for line in results:
        print(line)
    if args.check and drift_found:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
