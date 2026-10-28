# Internal reviews of this round's response: verbatim

Per [`../README.md`](../README.md): the prompt as sent and the return as
received, taken from the session transcript. The only edits are removing the
harness wrapper (task-notification tags, usage counters and agent ids) and
reversing its XML escaping. Nothing inside a prompt or a return is altered,
including claims in the returns that did not hold; `RESULT.md` gives each
item's disposition.

Both reviews ran in parallel on `b011298`. Their accepted findings, together
with the author's own pass, became `176c8c2`.

## 1. `b011298`, 2026-09-29

The preservation fix for the fourth audit's F5, F6 and F7.

Reviewer: `caveman:cavecrew-reviewer`.

### Prompt

````text
Review commit `b011298` in the git worktree C:/~shit/FLOSS/.worktrees/pr41-salvage (use `git -C "C:/~shit/FLOSS/.worktrees/pr41-salvage" show b011298`). Do not modify any file, do not use git stash, do not commit or push. Python: `C:/Python313/python.exe` with PYTHONPATH cleared, from the worktree: `PYTHONPATH= C:/Python313/python.exe -m pytest -q -p no:cacheprovider scripts/tests/test_shared_skill_surface_scope.py`. Scratch files only under C:/Users/kalis/AppData/Local/Temp/claude/C---shit/9c834986-63b7-46f0-83a1-33a7c558f045/scratchpad/rev. Never write into real skill roots (~/.codex/skills, ~/.claude/skills, C:/~shit/.claude/skills, hermes skills, etc.); use tmp dirs only.

The commit message explains it in full. In short, `scripts/materialize_shared_skill_surface.py` installs skill directories into shared roots and prunes withdrawn ones. The operator's rule: a skill changed where it is installed (harnesses evolve their skills) is never overwritten or deleted; it is surfaced as a `KEEP` line and `--check` still passes. Implemented with a per-file byte-digest baseline (`installed_files`) in each projection's marker, three-way comparison (installed / baseline / source), ownership checked first, markers published via temp file + os.replace (`publish_marker`), and RuntimeError added to path-resolution guards.

Directions, not a filter — report anything, introduced or pre-existing, inside or outside these:
- The decision table in `install_skill_projection`: walk every branch. Is there any path where content that differs from what this workspace installed gets removed or overwritten? Any path where a legitimate shared-base update can never reach an unmodified install? Any state that loops (drift reported every run but never resolvable by a write run)?
- `publish_marker`: temp file creation, os.replace semantics on Windows and POSIX when the destination is a symlink, a hardlink, read-only, open by another process; cleanup on failure; the temp file appearing in a concurrent `payload_digests` read or in a harness's skill discovery.
- `payload_digests`: symlinks inside a payload (followed? loops?), directory symlinks, unreadable files (OSError handling at every call site?), very large trees, case-only renames on Windows, empty directories (not digested — does that matter?).
- The UPDATE path: re-read before remove; what if `remove_path` or `copytree` fails midway; what is left and how does the next run classify it (could it become UNMANAGED forever)?
- The INSTALL/UPDATE failure cleanup that removes a freshly copied directory when the marker can't be published: can that ever remove something that was not freshly copied by this run?
- Legacy adoption: adopting any legacy marker whose payload equals the shared base — could that take over another workspace's legacy projection, and does that matter?
- Pruner: the owned-withdrawn branch; `read_managed_marker(child).get(...)` after `projection_owned_by` — can it be None there (TOCTOU)?
- Message and exit-code consumers: anything that parses `CHECK DRIFT`, `PLAN  WRITE`, `WROTE`, or depends on drift semantics (grep scripts/, hooks/, packages/, .github/).
- The tests added in this commit (search "Fourth external audit"): for each, name the production change that would make it fail. Could any pass while the behaviour is broken? Are the symlink/hardlink tests meaningful on Windows?

Report in three buckets; all three required; a bare "no issues" is not a result.
1. DEFECTS — one line each: `path:line: severity: problem. fix.`
2. OBSERVATIONS — unsure, or judged safe with the reason, so the judgement can be checked.
3. CHECKED AND CLEAN — each area checked, one line on how.
````

### Return

````text
## DEFECTS

1. **scripts/materialize_shared_skill_surface.py:670: Critical data safety race — TOCTOU bug allows AttributeError crash in pruner.** Between `projection_owned_by(child, owner_root)` (line 619) and `read_managed_marker(child).get("installed_files")` (line 670), the marker file could be deleted or corrupted by a concurrent process, causing `read_managed_marker` to return `None` and trigger `AttributeError` on the `.get()` call. Fix: read marker once in `projection_owned_by`, pass it to pruner branch, and guard `.get()` with None check; or call `read_managed_marker` once at line 619 and reuse it throughout the loop.

2. **scripts/materialize_shared_skill_surface.py:449-455: RuntimeError from symlink loops in skill payload not guarded — refresh can crash.** `payload_digests` uses `rglob` which follows symlinks, then calls `path.read_bytes()` on each. If a harness adds a symlink loop inside a skill directory (e.g., circular parent-child links), `read_bytes()` will raise `RuntimeError` (Python 3.12+) or hang indefinitely. This is unguarded at call sites (lines 740, 761, 672, 857). Fix: add `try/except (OSError, RuntimeError)` around `read_bytes()` in payload_digests, or detect and skip symlinks.

## OBSERVATIONS

1. **Line 740 — source directory unreadable between digest and use:** `source = payload_digests(source_dir)` at line 740 is unguarded. If the shared-base skill directory becomes read-only or inaccessible between this call and `serialize_marker` (line 741), an `OSError` will propagate and crash the run. Unlikely in practice (source is under version control), but **theoretically possible on network drives or concurrent symlink/permission changes**. **Judged safe:** source directory is a known, controlled location under `FLOSS/skill-corpus/` and shouldn't be modified during a refresh; a read failure here correctly signals a fatal condition.

2. **Lines 452-475 — `publish_marker` on Windows symlink edge case:** `os.replace(temporary, target_dir / MANAGED_MARKER)` on Windows with a symlink destination. Windows `os.replace` does not follow symlinks (replaces the entry), tested by `test_a_marker_rewrite_never_writes_through_a_symlink`. Verified correct via junctions check in `_is_link`. **Judged clean:** semantics confirmed by tests.

3. **Line 857 — re-read during UPDATE race:** If `payload_digests(target_dir)` raises `OSError` on the re-read immediately before `remove_path`, the exception is caught and `unchanged` is set to `False`, causing the update to be abandoned and the install kept as EVOLVED. This is the safe choice. **Judged correct:** race is handled by abandoning the unsafe operation.

4. **Partial copytree failure (line 870):** If `shutil.copytree` fails mid-way after `remove_path` succeeds, the directory is incomplete. Since no marker is published, it's read as UNMANAGED on the next run and never adopted. **Judged safe by design:** the marker-required-for-ownership rule prevents silent data loss.

5. **Withdrawn skill with no baseline (lines 670–688):** If `baseline` is `None` (old marker with no `installed_files` field) and the withdrawn skill directory is unreadable, OSError is caught at line 673 and it's kept. **Judged clean:** baseline validation at line 670 and error handling at 673 are separate and correct.

## CHECKED AND CLEAN

1. **Decision table in `install_skill_projection` (lines 697–882):** All six cases (installed==source, installed==baseline!=source, source==baseline!=installed, all differ, no baseline) are correctly classified and handled without overwriting; EVOLVED and CONFLICT cases explicitly kept. No path found where legitimate updates can't reach unmodified installs.

2. **publish_marker atomicity and link handling (lines 452–475):** Temp file creation with exclusive flags, `os.replace` swapping directory entries (not following links), cleanup on failure with `contextlib.suppress`, skip in `payload_digests`. Tested by `test_a_marker_rewrite_never_writes_through_a_hardlink` and symlink test. Design is sound.

3. **Workspace ownership verification (projection_owned_by, recorded_workspace):** RuntimeError now caught alongside OSError and ValueError (lines 556–557, 577); recorded workspace resolved and compared case-insensitively; _same_workspace decoupled for reuse. Handles F4 (NUL byte) and F6 (symlink loop in workspace_root). **Note:** bug at line 670 is orthogonal (TOCTOU, not ownership logic).

4. **Marker field validation (_valid_baseline, serialize_marker):** Baseline is a dict[str, str], validated before use; serialize_marker adds `installed_files` with sorted keys for determinism; legacy markers without `workspace_root` are adopted only when payload matches source byte-for-byte. No takeover of foreign legacy projections.

5. **Exit codes and --check semantics:** `--check` returns 1 iff drift_found is True; KEEP lines (local harness changes) do not set drift_found, so --check passes as designed. Pruner removes only withdrawn projections with matching baseline; pruner removes only when drift_found=True, which correctly signals to main(). Tests confirm withdrawal removal and --check pass on KEEP scenarios.
````

## 2. `b011298`, 2026-09-29, through OmniRoute

The same commit's changed functions, sent to a different model family. The
prompt carried the complete functions, with helper docstrings elided and the
module's imports and constants listed, so that the reviewer would not report
the elisions as defects, as happened in round 3.

Combo `static-best-free`, served by `pollinations/openai/gpt-5.4-nano`.

### Prompt

````text
[system]
You are a senior Python reviewer. Report in three buckets, all required: 1. DEFECTS (introduced or pre-existing; one line each: location: severity: problem. fix.) 2. OBSERVATIONS (unsure or judged safe; say why safe so the judgement can be checked) 3. CHECKED AND CLEAN (each area you checked, one line on how). A bare 'no issues' is not a result. The code below is COMPLETE for the functions shown; docstrings of helpers are elided. Module imports: argparse, contextlib, hashlib, json, os, shutil, sys, tempfile, pathlib.Path, typing.Any, yaml. MANAGED_MARKER='.flossi0ullk-managed.json', MANAGED_BY='FLOSSI0ULLK shared skill surface', MARKER_TEMP_PREFIX='.flossi0ullk-marker-'. serialize_marker(skill, version, workspace_root, *, installed_files) returns a JSON string with managed_by, manifest_version, source_path, skill_name, workspace_root (resolved str) and installed_files (sorted dict). read_managed_marker(dir) returns the parsed marker dict if managed_by matches, else None, catching OSError/ValueError/RecursionError. remove_path(p) unlinks a file or symlink, or rmtree's a real directory. Do not report names listed here as undefined. Begin by naming the model you are.

[user]
Context: skill directories are installed into roots such as ~/.codex/skills that several harnesses and workspaces share. RULE: a skill that has changed where it is installed must never be overwritten or deleted (harnesses evolve skills from use); it is surfaced as a KEEP line and --check still passes. --check fails only for what a write run would change. A per-file sha256 baseline in each projection's marker (installed_files) lets the code tell a shared-base change (safe to update) from a local change (keep). Markers are published via a temp file plus os.replace so a symlinked or hardlinked marker is never written through.

Directions, not a filter: walk every branch of install_skill_projection and find any path where content that differs from what this workspace installed gets removed or overwritten; any path where a shared-base update can never reach an unmodified install; any state that is reported as drift every run but a write run can never resolve; what happens if copytree or remove_path fails midway (what is left, how is it classified next run); whether the failure cleanup can ever delete something this run did not create; publish_marker on Windows and POSIX when the destination is a symlink, hardlink, read-only or open elsewhere; payload_digests with symlinks, symlink loops or unreadable files inside a payload.

```python
def payload_digests(directory: Path) -> dict[str, str]:
    digests = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(directory).as_posix()
        if rel == MANAGED_MARKER or rel.startswith(MARKER_TEMP_PREFIX):
            continue
        digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests

def publish_marker(target_dir: Path, content: str) -> None:
    if _is_link(target_dir) or not target_dir.is_dir():
        raise OSError(f"{target_dir} is not a plain directory; marker not written")
    handle, temporary = tempfile.mkstemp(dir=target_dir, prefix=MARKER_TEMP_PREFIX, suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temporary, target_dir / MANAGED_MARKER)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise

def _is_link(path: Path) -> bool:
    isjunction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or bool(isjunction and isjunction(path))

def _valid_baseline(value):
    if not isinstance(value, dict):
        return None
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
        return None
    return value

def _same_workspace(recorded: Path, workspace_root: Path) -> bool:
    try:
        owner = workspace_root.resolve()
    except (OSError, ValueError, RuntimeError):
        return False
    return os.path.normcase(str(recorded)) == os.path.normcase(str(owner))

def recorded_workspace(marker):
    recorded = marker.get("workspace_root")
    if not isinstance(recorded, str) or not Path(recorded).is_absolute():
        return None
    try:
        return Path(recorded).resolve()
    except (OSError, ValueError, RuntimeError):
        return None

def install_skill_projection(target_name, skill, target_root, manifest_version, *, check, dry_run, workspace_root):
    name = skill["skill_name"]
    target_dir = target_root / name
    source_dir = Path(skill["resolved_path"])
    source = payload_digests(source_dir)
    expected = serialize_marker(skill, manifest_version, workspace_root, installed_files=source)
    def keep(status, why):
        return ([f"KEEP  {target_name}: {name} {status}: {why}"], False)
    baseline = None
    if _is_link(target_dir):
        return keep("LINKED", "the installed skill directory is a link; nothing is written through it")
    if not target_dir.exists():
        action = "INSTALL"
    elif not target_dir.is_dir():
        return keep("NOT_A_DIRECTORY", "...")
    else:
        try:
            installed = payload_digests(target_dir)
        except OSError as exc:
            return keep("UNREADABLE", f"({exc})")
        marker_path = target_dir / MANAGED_MARKER
        marker = read_managed_marker(target_dir)
        if marker is None:
            if marker_path.exists() or marker_path.is_symlink():
                return keep("UNKNOWN_MARKER", "...")
            return keep("UNMANAGED", "...not adopted or replaced")
        if "workspace_root" not in marker:
            if installed != source:
                return keep("DIVERGED", "legacy marker, no baseline, differs")
            action = "ADOPT"
        else:
            recorded = recorded_workspace(marker)
            if recorded is None:
                return keep("UNKNOWN_OWNER", "...")
            if not _same_workspace(recorded, workspace_root):
                return keep("FOREIGN", f"installed by {recorded}")
            baseline = _valid_baseline(marker.get("installed_files"))
            if installed == source:
                action = None if marker == json.loads(expected) else "REBASELINE"
            elif baseline is None:
                return keep("DIVERGED", "no baseline, differs")
            elif installed == baseline:
                action = "UPDATE"
            elif source == baseline:
                return keep("EVOLVED", "changed where installed")
            else:
                return keep("CONFLICT", "changed in both")
    if action is None:
        if check: return ([f"CHECK OK {target_dir}"], False)
        if dry_run: return ([f"PLAN  KEEP {target_name}:{target_dir}"], False)
        return ([f"OK    {target_dir}"], False)
    if check:
        return ([f"CHECK DRIFT {target_dir} ({action})"], True)
    if dry_run:
        return ([f"PLAN  WRITE {target_name}:{target_dir} ({action})"], True)
    if action in {"ADOPT", "REBASELINE"}:
        try:
            publish_marker(target_dir, expected)
        except OSError as exc:
            return ([f"FAILED {target_name}: {name} marker not published ({exc})"], True)
        return ([f"WROTE {target_dir} (marker only: {action})"], True)
    if action == "UPDATE":
        try:
            unchanged = payload_digests(target_dir) == baseline
        except OSError:
            unchanged = False
        if not unchanged:
            return keep("EVOLVED", "changed during this refresh; update abandoned")
        remove_path(target_dir)
    shutil.copytree(source_dir, target_dir)
    try:
        publish_marker(target_dir, expected)
    except OSError as exc:
        remove_path(target_dir)
        return ([f"FAILED {target_name}: {name} not installed ({exc})"], True)
    return ([f"WROTE {target_dir} ({action})"], True)

# In the pruner, for a withdrawn projection already judged owned by projection_owned_by(child, owner_root), which reads the marker:
        baseline = _valid_baseline(read_managed_marker(child).get("installed_files"))
        try:
            installed = payload_digests(child)
        except OSError as exc:
            results.append(f"KEEP ... could not be read ({exc})"); continue
        if baseline is None or installed != baseline:
            results.append("KEEP ... withdrawn but changed or unbaselined; kept for review"); continue
        drift_found = True
        if check: results.append("DRIFT ...")
        elif dry_run: results.append("would remove ...")
        else: remove_path(child); results.append("removed ...")
```
````

### Return

````text
Model: **python review** (senior Python reviewer)

## 1. DEFECTS
- `install_skill_projection()`: **CRITICAL**: `payload_digests(target_dir)` hashes *everything* including hidden files/dirs; if the workspace-installed version intentionally differs via e.g. timestamps/metadata, `UPDATE/ADOPT` may never be reachable and will be reported as drift every run. **Fix:** restrict digested set to the payload files that are actually meant to be managed (e.g., only relative paths under a defined manifest, or exclude known volatile patterns).
- `install_skill_projection()`: **CRITICAL**: no explicit protection against symlink traversal inside `target_dir` during digesting and copying—`rglob("*")` + `is_file()` follows symlinks in Python semantics, and `copytree(source_dir, target_dir)` can dereference/copy symlink targets depending on platform/options. **Fix:** make `payload_digests()` and the copy step refuse symlinks (or treat them as distinct artifacts) by walking with `os.scandir`/`follow_symlinks=False`-style logic (manually), and use a controlled copy that preserves symlinks without dereferencing (or rejects them).
- `publish_marker()`: **HIGH**: `tempfile.mkstemp(dir=target_dir, ...)` creates the temp file inside the destination directory; on Windows, if the directory is on a different volume/link mode, the replace semantics can be problematic, and on some FS the replace may not be atomic across certain conditions. **Fix:** use `tempfile.NamedTemporaryFile(delete=False, dir=...)` (or keep mkstemp) but additionally verify on Windows that `os.replace` succeeds on the same filesystem; if not, fall back to copy+replace carefully.
- `publish_marker()`: **HIGH**: `_is_link(target_dir)` only checks `is_symlink` and junctions; it doesn’t consider hardlinks, reparse points other than junction, or cases where `target_dir` is a bind mount or other special. **Fix:** strengthen link/special-dir detection (Windows: use `os.stat` + reparse tag via `ctypes` where available; POSIX: detect with `os.lstat` and inode/parent resolution heuristics or disallow non-regular directories by policy).
- `install_skill_projection()`: **HIGH**: `remove_path(target_dir)` is called after a digest check, but there’s no re-check that the directory still matches expected/baseline before deletion; a concurrent process could modify between digest check and deletion. **Fix:** perform deletion only after re-validating (e.g., re-run digest after acquiring an inter-process lock) or use a lock file protocol under `target_dir`.
- `install_skill_projection()`: **MEDIUM**: `action=None if marker == json.loads(expected) else "REBASELINE"` compares full marker dict equality; marker dict ordering is irrelevant, but if `serialize_marker()` includes fields that can vary (resolved str for workspace_root, installed_files ordering already sorted, but other fields?), you could rebaseline every run. **Fix:** compare only the relevant fields (managed_by, manifest_version, installed_files) and normalize paths.
- `install_skill_projection()`: **MEDIUM**: `_valid_baseline()` silently returns `None` if `installed_files` contains non-`str` values; that will downgrade to `DIVERGED` even if differences are benign (e.g., dict values accidentally stored as other types). **Fix:** coerce to strings when safe, or fail with an explicit KEEP reason that indicates schema mismatch.
- `install_skill_projection()`: **MEDIUM**: `recorded_workspace(marker)` requires `Path(recorded).is_absolute()`; if the serialized marker uses an absolute resolved path but includes trailing spaces or casing differences, it will reject. **Fix:** strip and validate; store canonical absolute paths in `serialize_marker()`.

## 2. OBSERVATIONS (judged safe / needs confirmation)
- `publish_marker()`: **Mostly safe**: uses `mkstemp` + write + `os.replace` and suppresses unlink of temp on failure—this avoids partially-written marker files and ensures the destination marker is atomically replaced (no symlinked marker write-through).
- `install_skill_projection()`: **Safe with RULE intent**: the “changed where it is installed must never be overwritten” is implemented by detecting `source == baseline` and returning `KEEP ... EVOLVED` (for shared-base changes) rather than deleting/copying; only `UPDATE` (installed matches baseline) proceeds to overwrite.
- `install_skill_projection()` pruner snippet: **Safe in spirit**: withdrawn removals are gated by `baseline is not None and installed == baseline` (only remove if unmodified from known shared baseline).
- `payload_digests()`: **May be acceptable** if payloads are regular files without symlink tricks; it also correctly excludes marker + marker temp prefix, preventing self-referential digest churn. (But see defects about symlink handling.)

## 3. CHECKED AND CLEAN
- Walked the full control flow of `install_skill_projection()` for each `action` branch: `INSTALL`, `ADOPT`, `REBASELINE`, `UPDATE`, and early `KEEP` states; I found the overwrite/delete is only reachable after `installed == baseline` and after re-checking digests immediately before `remove_path(target_dir)`.
- Checked marker write behavior in `publish_marker()` for symlinked/hardlinked/readonly/open-elsewhere scenarios conceptually: it prevents writing through a symlinked destination dir and publishes via replace, but it still relies on `_is_link()` correctness and OS semantics.
- Checked failure-midway behavior: if `copytree()` fails after `remove_path()`, the target may be deleted and left absent; next run will likely fall back to `INSTALL` (which would overwrite). This is consistent with your rule only if `remove_path()` can’t run on shared-base-unmodified installs. Under concurrent failures, it could be problematic—needs locking/atomicity if strict.
````
