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
import contextlib
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml

import skill_projection_staging as staging

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_MANIFEST_PATH = REPO_ROOT / "shared-skill-surface.json"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "skills"
MANAGED_MARKER = ".flossi0ullk-managed.json"
# Written into every marker and checked before any removal. One constant for
# both, because the pruner deciding ownership by comparing against a second
# copy of this string is how the two would drift apart.
MANAGED_BY = "FLOSSI0ULLK shared skill surface"
# A marker being published is first written under this prefix and then swapped
# into place; it is never part of a skill's payload.
MARKER_TEMP_PREFIX = ".flossi0ullk-marker-"
REMOVING_PREFIX = ".flossi0ullk-removing-"
# A skill's name becomes `<target root>/<name>`, so it is one path component
# (LSI-A5): no separator, no `..`, no absolute path.
SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_ASIDE_RE = re.compile(re.escape(REMOVING_PREFIX) + r"[0-9a-f]{16}-(?P<base>.+)$")
# Files that USING a skill generates rather than changing it: running a skill's
# Python script writes __pycache__ into the installed copy, and desktop shells
# drop folder metadata. Counted as payload, they marked a skill EVOLVED for
# ever and blocked every update from the shared base.
GENERATED_DIRS = frozenset({"__pycache__"})
GENERATED_FILES = frozenset({".DS_Store", "Thumbs.db", "desktop.ini"})
GENERATED_SUFFIXES = (".pyc", ".pyo")


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
    if not SKILL_NAME_RE.match(frontmatter["name"]) or ".." in frontmatter["name"]:
        raise SkillSurfaceError(
            f"{skill_md}: skill `name` {frontmatter['name']!r} must be a single path "
            "component (letters, digits, `.`, `_`, `-`; no separator, no `..`): it "
            "becomes <target root>/<name>"
        )
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

    The shared resolver expands native environment syntax and `~`, then rejects
    unresolved variable tokens instead of joining them literally to the workspace.
    The import is deferred because the agent-surface module imports this skill
    module at load time. Keep expansion in the existing shared helper.
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

    The main-reference manifest declares `~/.codex/skills` as user scope. A plain
    run excludes that target; only `--include-user-scope` permits writing it.

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
    skill: dict[str, Any],
    manifest_version: str,
    workspace_root: Path,
    *,
    installed_files: dict[str, str],
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
        # WHAT WAS INSTALLED: the digest of every payload file's bytes. The
        # baseline that tells a change in the shared base (safe to apply) from
        # a change made where the skill is installed (a harness's learning,
        # never overwritten). See install_skill_projection.
        "installed_files": dict(sorted(installed_files.items())),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def payload_digests(directory: Path) -> dict[str, str]:
    """sha256 of every payload file's BYTES under `directory`, by relative path.

    Bytes, not text. The snapshot this replaces read files in universal-newline
    mode, so a CRLF script compared equal to its LF source and a broken copy was
    blessed as current (fourth external audit, F7); and it decoded every file as
    UTF-8, so a harness that added an image to a skill crashed the refresh. The
    marker, and a marker being published, are not payload.
    """

    def refuse(error: OSError) -> None:
        # os.walk's default is to skip what it cannot list. A partial digest
        # can compare equal to a baseline and license removing content it
        # never saw, so an unreadable directory is an error, not a gap.
        raise error

    digests: dict[str, str] = {}
    for root, dirnames, filenames in os.walk(directory, onerror=refuse):
        base = Path(root)
        for dirname in list(dirnames):
            full = base / dirname
            rel = full.relative_to(directory).as_posix()
            if dirname in GENERATED_DIRS:
                dirnames.remove(dirname)
            elif _is_link(full):
                # A link is payload AS a link. Following one read files
                # outside the skill, and a loop a harness left inside one could
                # hang or raise on Python 3.12. Its target text is recorded
                # and nothing is read through it.
                digests[rel] = "link:" + os.readlink(full)
                dirnames.remove(dirname)
        for filename in filenames:
            full = base / filename
            rel = full.relative_to(directory).as_posix()
            if rel == MANAGED_MARKER or rel.startswith(MARKER_TEMP_PREFIX):
                continue
            if _is_generated(rel):
                continue
            if full.is_symlink():
                digests[rel] = "link:" + os.readlink(full)
            else:
                digests[rel] = hashlib.sha256(full.read_bytes()).hexdigest()
    return dict(sorted(digests.items()))


def _is_generated(rel: str) -> bool:
    parts = rel.split("/")
    return (
        any(part in GENERATED_DIRS for part in parts[:-1])
        or parts[-1] in GENERATED_FILES
        or parts[-1].endswith(GENERATED_SUFFIXES)
    )


def _copy_payload(source_dir: Path, target_dir: Path) -> None:
    # symlinks=True: a link is copied as a link, matching how payload_digests
    # records it. Copying the target's content instead would make every
    # install with a link compare different from its source for ever.
    legacy_ignore = shutil.ignore_patterns(
        *GENERATED_DIRS, *GENERATED_FILES, *(f"*{s}" for s in GENERATED_SUFFIXES)
    )

    def ignore_generated(directory: str, names: list[str]) -> set[str]:
        legacy = legacy_ignore(directory, names)
        ignored: set[str] = set()
        isjunction = getattr(os.path, "isjunction", None)
        if os.name == "nt" and isjunction is None:
            return legacy
        for name in names:
            path = Path(directory) / name
            try:
                # Junction copying/cleanup needs its own ownership repair.
                # Preserve its old filter: newly including it could traverse it.
                if isjunction and isjunction(path):
                    if name in legacy:
                        ignored.add(name)
                    continue
                is_directory = path.is_dir()
            except OSError:
                # Do not introduce an error before copytree creates its target.
                if name in legacy:
                    ignored.add(name)
                continue
            if (is_directory and name in GENERATED_DIRS) or (
                not is_directory and _is_generated(name)
            ):
                ignored.add(name)
        return ignored

    shutil.copytree(source_dir, target_dir, symlinks=True, ignore=ignore_generated)


def publish_marker(target_dir: Path, content: str) -> None:
    """Publish a marker as a NEW file swapped into place, never through a link.

    Writing the existing marker in place followed it: a marker that was a
    symlink wrote its target, and one that was a hard link rewrote every name
    for that file -- possibly another projection's marker (fourth external
    audit, F5). The temporary file is created exclusively, and os.replace swaps
    the directory entry, replacing a link rather than following it. On any
    failure the previous marker is left exactly as it was.
    """

    if _is_link(target_dir) or not target_dir.is_dir():
        raise OSError(f"{target_dir} is not a plain directory; marker not written")
    handle, temporary = tempfile.mkstemp(
        dir=target_dir, prefix=MARKER_TEMP_PREFIX, suffix=".tmp"
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary, target_dir / MANAGED_MARKER)
    except BaseException:
        # Retain a failed temporary marker; it is excluded from payload digests.
        raise


def _is_link(path: Path) -> bool:
    """A symlink, or on Windows a junction. Neither is ever written through."""

    isjunction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or bool(isjunction and isjunction(path))


def _valid_baseline(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        return None
    return value


def _describe_changes(now: dict[str, str], before: dict[str, str]) -> str:
    changed = sorted(
        rel for rel in set(now) | set(before) if now.get(rel) != before.get(rel)
    )
    shown = ", ".join(changed[:5])
    return shown + (f" and {len(changed) - 5} more" if len(changed) > 5 else "")


def remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def _put_back(aside: Path, directory: Path) -> bool:
    """Rename a copy taken aside back to its own name. False if it cannot be."""

    try:
        os.rename(aside, directory)
    except OSError:
        return False
    return True


def remove_if_unchanged(
    directory: Path, baseline: dict[str, str]
) -> tuple[str, str] | None:
    """Remove `directory` only if it is STILL exactly `baseline`, checked after
    it has been taken away. Returns None when removed, else `(status, why)`.

    Comparing and then removing leaves a window: a harness that writes a
    learning between the two matches the baseline no longer, but the decision
    was already taken, and the learning is deleted (PR41 review, P2). So the
    directory is renamed to a name nobody writes to, and only the renamed copy
    is verified and deleted. A late write by path now fails or lands outside
    it. If the copy changed, or could not be read, it is renamed back.

    The window is NARROWED, not closed (LSI-A4 f). On POSIX a process that
    holds a file open across the rename still writes into the renamed copy,
    and a write landing between the verification and the deletion is deleted
    with it. Windows refuses to rename a directory with open files, which is
    the IN_USE outcome.

    Statuses, kept distinct because the operator's next step differs:
      IN_USE      the rename was refused; nothing moved
      CHANGED     it no longer equals the baseline; put back
      UNREADABLE  the renamed copy could not be read; put back
      STUCK       verified, then could not be fully deleted; the remainder is
                  named, and the run continues

    The aside name is a sibling carrying the same marker, so a copy stranded by
    a crash is picked up by the next run (put back if it belongs to a listed
    skill, otherwise an ordinary withdrawn projection). It starts with a dot.
    Codex's loader skips dot-directories (read in rust-v0.128.0); the other
    harnesses' scanners have not been read, so a stranded copy may be
    discovered by them as a second skill until the next run.
    """

    already_aside = directory.name.startswith(REMOVING_PREFIX)
    aside = directory
    if not already_aside:
        aside = directory.with_name(
            f"{REMOVING_PREFIX}{secrets.token_hex(8)}-{directory.name}"
        )
        try:
            os.rename(directory, aside)
        except OSError as exc:
            # Open files block a rename on Windows. A copy that cannot be taken
            # aside cannot be verified in isolation, so it is left alone.
            return ("IN_USE", f"it could not be taken aside to be checked ({exc})")
    problem: OSError | None = None
    try:
        try:
            unchanged = payload_digests(aside) == baseline
        except OSError as exc:
            unchanged = False
            problem = exc
    except BaseException:
        # Anything else, an interruption included: the copy goes back.
        if not already_aside:
            _put_back(aside, directory)
        raise
    if unchanged:
        try:
            remove_path(aside)
        except OSError as exc:
            return (
                "STUCK",
                f"its verified copy could not be fully deleted ({exc}); the "
                f"remainder is at {aside}",
            )
        return None
    restored = already_aside or _put_back(aside, directory)
    if problem is not None:
        status, why = "UNREADABLE", f"the copy taken aside could not be read ({problem})"
    else:
        status, why = "CHANGED", "it changed while being checked"
    if not restored:
        why += f", and could not be put back at {directory}; kept as {aside}"
    return (status, why)


def _discard_failed_install(target_dir: Path, source: dict[str, str]) -> str | None:
    """Remove a directory a failed install left, but only what is provably the
    shared base (LSI-A6). None when removed or already gone, else why not.

    The cleanup used to assume everything under the directory came from the
    copy it had just made. A harness can write into a fresh install before the
    marker is published, and removing the directory deleted that.
    """

    if not target_dir.exists():
        return None
    try:
        present = payload_digests(target_dir)
    except OSError as exc:
        return f"it could not be read ({exc})"
    foreign = sorted(rel for rel, digest in present.items() if source.get(rel) != digest)
    if foreign:
        shown = ", ".join(foreign[:5]) + (
            f" and {len(foreign) - 5} more" if len(foreign) > 5 else ""
        )
        return f"it holds files that are not the shared base ({shown})"
    remove_path(target_dir)
    return None


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
    return _same_workspace(recorded, owner_root)


def _same_workspace(recorded: Path, workspace_root: Path) -> bool:
    try:
        owner = workspace_root.resolve()
    except (OSError, ValueError, RuntimeError):
        return False
    return os.path.normcase(str(recorded)) == os.path.normcase(str(owner))


def recorded_workspace(marker: dict[str, Any]) -> Path | None:
    """The installing workspace a marker names, resolved; None if unusable.

    Three exception types, each found by an audit on a platform the author's
    suite never ran on. On POSIX an absolute identity containing a NUL raises
    ValueError from resolve() (third external audit, F4), and on Python 3.12 a
    symlink loop raises RuntimeError (fourth, F6); catching only OSError let
    either abort the pruner and the materializer around it, `--check` included.
    Windows resolves both without raising.
    """

    recorded = marker.get("workspace_root")
    if not isinstance(recorded, str) or not Path(recorded).is_absolute():
        return None
    try:
        return Path(recorded).resolve()
    except (OSError, ValueError, RuntimeError):
        return None


def _staging_inventory(path: Path) -> dict:
    return staging.inventory_plain(path, generated_dirs=GENERATED_DIRS,
        generated_files=GENERATED_FILES, generated_suffixes=GENERATED_SUFFIXES,
        marker_name=MANAGED_MARKER, marker_temp_prefix=MARKER_TEMP_PREFIX)


def prune_stale_projections(
    target_name: str, target_root: Path, expected: set[str], *,
    check: bool, dry_run: bool, owner_root: Path,
) -> tuple[list[str], bool]:
    """Approved stabilization contract: inspect, never prune or restore a live name."""
    results = []
    try:
        staging._plain_ancestry(target_root)
        if not target_root.exists():
            return results, False
        for child in sorted(target_root.iterdir()):
            if _is_link(child) or not child.is_dir() or child.name in expected:
                continue
            if not projection_owned_by(child, owner_root):
                marker = read_managed_marker(child)
                if marker is not None:
                    recorded = recorded_workspace(marker)
                    if recorded is None:
                        results.append(f"KEEP  {target_name}: {child.name} installing-workspace identity unknown; retained")
                    elif not os.path.exists(recorded):
                        results.append(f"KEEP  {target_name}: {child.name} workspace {recorded} cannot be found (moved or not mounted); retained")
                continue
            stranded = _ASIDE_RE.match(child.name)
            if stranded is not None and stranded.group("base") in expected:
                results.append(f"RESTORE_DEFERRED {target_name}: {stranded.group('base')} retained at {child}; no recovery rename")
            else:
                results.append(f"PRUNE_DEFERRED {target_name}: {child.name} retained at {child}; no stale deletion")
    except OSError as exc:
        return ([f"FAILED {target_name}: pruning inspection: {exc}; no mutation"], True)
    return results, any("_DEFERRED " in line for line in results)


def install_skill_projection(
    target_name: str,
    skill: dict[str, Any],
    target_root: Path,
    manifest_version: str,
    *,
    check: bool,
    dry_run: bool,
    workspace_root: Path,
    staging_root: Path | None = None,
    discovery_roots: tuple[Path, ...] = (),
    qualification_cache: dict | None = None,
) -> tuple[list[str], bool]:
    """Install, update, or leave alone one skill's projection.

    THE OPERATOR'S RULE, 2026-09-29: a skill that has changed where it is
    installed is never overwritten. Harnesses -- Hermes especially, Codex too
    -- evolve their skills from use, and those changes are to be propagated
    back into the shared base, not replaced by it. So this never replaces,
    removes or adopts anything it cannot prove is exactly what this workspace
    installed. Everything else is left in place and SURFACED as a `KEEP` line,
    and -- same decision -- `--check` passes on it. The approved C04
    stabilization exception reports deferred UPDATE/prune/restoration nonzero;
    it never calls a preserved but unsynchronized copy clean.

    The proof is a baseline: the marker records the digest of every payload
    file's bytes as installed. With it the cases separate:

        installed == source               nothing to do, or re-baseline a stale marker
        installed == baseline != source   only the shared base moved: UPDATE
        source == baseline != installed   the harness changed it: EVOLVED, kept
        all three differ                  CONFLICT, kept
        no baseline, and they differ      DIVERGED, kept: nothing says which side moved

    Ownership is settled first, because a matching name or even matching
    content does not authorise taking over someone else's installation. Only
    a projection whose marker names this workspace is ever written. A legacy
    marker, from before markers recorded an owner, is ADOPTED only when its
    payload equals the shared base byte for byte: that is the migration that
    gives it an owner and a baseline. Another workspace's projection, an
    unmanaged directory with the same name, an unreadable marker and a linked
    directory are all kept and surfaced, never taken over.
    """

    name = skill["skill_name"]
    target_dir = target_root / name
    source_dir = Path(skill["resolved_path"])
    private = staging_root or workspace_root / ".agent-surface/harvest/skill-preparation"
    excluded = (*discovery_roots, target_root,
                workspace_root / ".agent-surface/skills",
                *(workspace_root / n for n in (".claude", ".agents", ".codex")),
                *(workspace_root / "FLOSS" / n for n in (".claude", ".agents", ".codex")))
    inventory = _staging_inventory
    try:
        pending = staging.pending_for_target(private, target_dir, workspace_root, inventory, MANAGED_MARKER)
        if pending:
            return pending, True
        # Do not install beside learning stranded by an earlier interrupted run.
        if not os.path.lexists(target_dir) and target_root.is_dir():
            for child in target_root.iterdir():
                match = _ASIDE_RE.match(child.name)
                if match and match.group("base") == name and projection_owned_by(child, workspace_root):
                    return ([f"RESTORE_DEFERRED {target_name}: {name} retained at {child}; INSTALL blocked"], True)
        source = payload_digests(source_dir)
    except OSError as exc:
        return ([f"FAILED {target_name}: {name} preparation inspection: {exc}"], True)
    expected = serialize_marker(
        skill, manifest_version, workspace_root, installed_files=source
    )

    def keep(status: str, why: str) -> tuple[list[str], bool]:
        return ([f"KEEP  {target_name}: {name} {status}: {why}"], False)

    baseline: dict[str, str] | None = None
    action: str | None
    if _is_link(target_dir):
        return keep(
            "LINKED",
            "the installed skill directory is a link; nothing is written through it",
        )
    if not target_dir.exists():
        action = "INSTALL"
    elif not target_dir.is_dir():
        return keep("NOT_A_DIRECTORY", f"{target_dir} is not a directory; left in place")
    else:
        try:
            installed = payload_digests(target_dir)
        except OSError as exc:
            return keep("UNREADABLE", f"the installed copy could not be read ({exc})")
        marker_path = target_dir / MANAGED_MARKER
        marker = read_managed_marker(target_dir)
        if marker is None:
            if marker_path.exists() or marker_path.is_symlink():
                return keep(
                    "UNKNOWN_MARKER",
                    "its marker is unreadable or was not written by this "
                    "materializer; left in place",
                )
            relation = "identical to" if installed == source else "different from"
            return keep(
                "UNMANAGED",
                f"an unmanaged directory with this name is installed, {relation} "
                f"the shared base; not adopted or replaced",
            )
        if "workspace_root" not in marker:
            if installed != source:
                return keep(
                    "DIVERGED",
                    f"a legacy marker with no baseline, and the installed copy "
                    f"differs from the shared base "
                    f"({_describe_changes(installed, source)}); kept for "
                    f"reconciliation",
                )
            action = "ADOPT"
        else:
            recorded = recorded_workspace(marker)
            if recorded is None:
                return keep(
                    "UNKNOWN_OWNER",
                    "its marker's recorded owner is unusable; left in place",
                )
            if not _same_workspace(recorded, workspace_root):
                return keep(
                    "FOREIGN", f"installed by {recorded}; not replaced or taken over"
                )
            baseline = _valid_baseline(marker.get("installed_files"))
            if installed == source:
                action = None if marker == json.loads(expected) else "REBASELINE"
            elif baseline is None:
                return keep(
                    "DIVERGED",
                    f"no baseline was recorded, and the installed copy differs "
                    f"from the shared base ({_describe_changes(installed, source)}); "
                    f"kept for reconciliation",
                )
            elif installed == baseline:
                action = "UPDATE"
            elif source == baseline:
                return keep(
                    "EVOLVED",
                    f"changed where installed "
                    f"({_describe_changes(installed, baseline)}); kept for "
                    f"reconciliation with the shared base",
                )
            else:
                return keep(
                    "CONFLICT",
                    f"changed where installed "
                    f"({_describe_changes(installed, baseline)}) and in the shared "
                    f"base ({_describe_changes(source, baseline)}); kept for "
                    f"reconciliation",
                )

    if action is None:
        if check:
            return ([f"CHECK OK {target_dir}"], False)
        if dry_run:
            return ([f"PLAN  KEEP {target_name}:{target_dir}"], False)
        return ([f"OK    {target_dir}"], False)
    if action == "UPDATE":
        metadata = target_dir.lstat()
        report = dict(outcome="UPDATE_DEFERRED", workspace_root=str(workspace_root.resolve()),
            target=str(target_dir), source_path=str(source_dir), source_digests=source,
            installed_digests=installed, baseline=baseline,
            observed_live_identity=dict(device=metadata.st_dev, inode=metadata.st_ino),
            source_byte_preservation="BYTES_NOT_FROZEN unless independently retained")
        detail = "read-only observation"
        if not check and not dry_run:
            try:
                staging.validate_private_root(private, (*excluded, source_dir))
                detail = f"report={staging.persist_deferred_report(private, report)}"
            except OSError as exc:
                detail = f"REPORT_NOT_WRITTEN: {exc}"
        return ([f"UPDATE_DEFERRED {target_name}: {name}; {json.dumps(report, sort_keys=True)}; {detail}; live name and bytes retained"], True)
    if action == "INSTALL":
        if sys.platform != "win32":
            return ([f"UNSUPPORTED {target_name}: {name} INSTALL backend unqualified on {sys.platform}; no publication planned"], True)
        try:
            staging.validate_private_root(private, (*excluded, source_dir))
        except OSError as exc:
            return ([f"FAILED {target_name}: {name} private preparation boundary: {exc}"], True)
    if check:
        return ([f"CHECK DRIFT {target_dir} ({action})"], True)
    if dry_run:
        return ([f"PLAN  WRITE {target_name}:{target_dir} ({action})"], True)

    if action in {"ADOPT", "REBASELINE"}:
        # Only the marker changes; the skill is never taken down for it.
        try:
            publish_marker(target_dir, expected)
        except OSError as exc:
            return (
                [
                    f"FAILED {target_name}: {name} marker not published ({exc}); "
                    f"the previous marker is untouched"
                ],
                True,
            )
        return ([f"WROTE {target_dir} (marker only: {action})"], True)

    try:
        text_files = skill.get("files")
        registry_observation = dict(status="NOT_PROVIDED", atomic_snapshot_qualified=False)
        if isinstance(text_files, dict) and all(isinstance(v, str) for v in text_files.values()):
            encoded = json.dumps(text_files, sort_keys=True, ensure_ascii=False).encode("utf-8")
            text_hashes = {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in text_files.items()}
            registry_observation.update(v1_files_sha256=hashlib.sha256(encoded).hexdigest(),
                status="V1_TEXT_HASHES_MATCH_SELECTED_FILES" if text_hashes == source else "V1_TEXT_DIFFERS_FROM_SELECTED_BYTE_INVENTORY")
        outcome, detail = staging.prepare_install(source_dir, target_dir, workspace_root,
            private, excluded, inventory, _copy_payload, expected, MANAGED_MARKER,
            MARKER_TEMP_PREFIX, publish_marker, qualification_cache, registry_observation)
        detail += f"; registry={registry_observation['status']}; atomic registry/install snapshot unqualified"
    except (OSError, ValueError) as exc:
        outcome, detail = ("UNSUPPORTED" if "UNSUPPORTED" in str(exc) else "FAILED"), str(exc)
    return ([f"{outcome} {target_name}: {name} {detail}"], True)


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
    # Sweep independent of the current manifest, so withdrawal/moves cannot
    # turn unresolved preparation into an unreported successful check.
    pending = staging.pending_for_target(
        workspace_root / ".agent-surface/harvest/skill-preparation", None,
        workspace_root, _staging_inventory, MANAGED_MARKER,
        tuple(Path(root) / skill["skill_name"] for root in target_roots.values() for skill in registry["skills"]),
    )
    results.extend(pending)
    drift_found = bool(pending)
    qualification_cache: dict = {}

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
                discovery_roots=tuple(Path(p) for p in target_roots.values()) + (output_dir,),
                qualification_cache=qualification_cache,
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
    try:
        results, drift_found = materialize(
            workspace_root=args.workspace_root.resolve(),
            manifest_path=args.manifest.resolve(),
            output_dir=args.output_dir.resolve(),
            check=args.check, dry_run=args.dry_run,
            include_user_scope=args.include_user_scope,
        )
    except (SkillSurfaceError, OSError, ValueError) as exc:
        print(f"FAILED skill surface: {exc}")
        return 1
    for line in results:
        print(line)
    failed = any(line.startswith(("FAILED", "UNSUPPORTED", "PENDING", "CONFLICT")) for line in results)
    deferred = any(line.startswith(("UPDATE_DEFERRED", "PRUNE_DEFERRED", "RESTORE_DEFERRED")) for line in results)
    return int(failed or (args.check and drift_found) or (deferred and not (args.dry_run and not args.check)))


if __name__ == "__main__":
    raise SystemExit(main())
