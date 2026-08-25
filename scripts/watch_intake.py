"""Polling-based intake watcher for the FLOSSI0ULLK metaharness.

Scans a small set of high-signal roots and emits normalized IntakeEvent files
into `.agent-surface/events/incoming/`. This is intentionally a walking
skeleton, not a long-lived daemon or semantic indexer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_EVENT_ROOT = DEFAULT_WORKSPACE_ROOT / ".agent-surface" / "events"
DEFAULT_STATE_PATH = DEFAULT_EVENT_ROOT / "watch-state.json"

TEXT_SUFFIXES = {
    ".json",
    ".jsonc",
    ".md",
    ".ps1",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

ROOT_INTAKE_SUFFIXES = {".html", ".md", ".txt"}
ROOT_INTAKE_EXCLUDE_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "INDEX.md",
    "favicon.svg",
    "index.html",
    "package-lock.json",
    "package.json",
    "styles.css",
    "vibe-floss.ps1",
}
ROOT_INTAKE_EXCLUDE_PREFIXES = {
    "deepsource-",
    "pr25-",
    "~shit",
}
LOCK_POLL_SECONDS = 0.1
DEFAULT_DEBOUNCE_SECONDS = 1.5
# Backpressure guard: if the incoming queue is deeper than this, the watcher
# stops emitting until process_intake_events.py drains it. Prevents unbounded
# feedback storms (2026-06-16/17 incident: 1.23M events accumulated).
MAX_INCOMING_QUEUE_DEPTH = 5000

# Sentinel: a withheld key whose state entry must be removed, not restored.
_DROP = object()
RESERVED_AGENT_SURFACE_SUBTREES = {
    ".agent-surface",
    ".agent-surface/events",
    ".agent-surface/shadows",
}
# Dependency and build trees. These are vendored or regenerable, never intake,
# and they are enormous: the `shared-surface` spec watches all of FLOSS/
# recursively, so a single unexcluded node_modules dominates the queue. The
# 2026-07-07 QUEUE_SUMMARY showed 99 of the last 100 processed events coming
# from FLOSS/workers/commons-gateway/node_modules/** alone. The 2026-06-16/17
# flood (1.23M events) had a different root cause — overlapping watch specs,
# fixed by first-spec-wins dedup — but this would have produced its own storm
# on the next run regardless. Directory-name match, so it prunes at any depth.
EXCLUDED_DIR_NAMES = {
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".svelte-kit",
    ".tox",
    ".venv",
    "__pycache__",
    "bower_components",
    "dist",
    "htmlcov",
    "node_modules",
    "site-packages",
    "target",
    "vendor",
    "venv",
}
EXCLUDED_FILE_SUFFIXES = {
    ".jsonl",
    ".pyc",
}


@dataclass(frozen=True)
class WatchSpec:
    domain: str
    corpus_hint: str
    mode: str
    root: Path


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def lock_file(lock_dir: Path, name: str, *, timeout_seconds: float = 5.0):
    lock_dir.mkdir(parents=True, exist_ok=True)
    path = lock_dir / f"{name}.lock"
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out acquiring lock: {path}")
            time.sleep(LOCK_POLL_SECONDS)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        yield path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def ensure_dirs(event_root: Path) -> None:
    for name in ("incoming", "processing", "processed", "failed", "locks"):
        (event_root / name).mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def load_state(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = load_json(path)
    state = data.get("files", {})
    return state if isinstance(state, dict) else {}


def save_state(path: Path, files_state: dict[str, dict[str, Any]]) -> None:
    write_json(
        path,
        {
            "updated_at": utcnow_iso(),
            "files": files_state,
        },
    )


def sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def path_info(path: Path, workspace_root: Path) -> dict[str, Any]:
    stat = path.stat()
    rel_path = None
    try:
        rel_path = path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        rel_path = None
    payload = {
        "abs_path": str(path.resolve()),
        "rel_path": rel_path,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }
    if path.suffix.lower() in TEXT_SUFFIXES and stat.st_size <= 2_000_000:
        payload["sha256"] = sha256_file(path)
    return payload


def iter_domain_files(spec: WatchSpec) -> Iterable[Path]:
    root = spec.root
    if not root.exists():
        return []
    if root.is_file():
        return [root]

    if spec.mode == "root-top-level":
        files: list[Path] = []
        for child in root.iterdir():
            if not child.is_file():
                continue
            if child.name in ROOT_INTAKE_EXCLUDE_NAMES:
                continue
            if any(
                child.name.startswith(prefix) for prefix in ROOT_INTAKE_EXCLUDE_PREFIXES
            ):
                continue
            if child.suffix.lower() in ROOT_INTAKE_SUFFIXES:
                files.append(child)
        return sorted(files)

    if spec.mode == "recursive":
        return sorted(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )

    return []


def default_watch_specs(workspace_root: Path) -> list[WatchSpec]:
    return [
        WatchSpec("root-intake", "research", "root-top-level", workspace_root),
        WatchSpec("canon", "canon", "recursive", workspace_root / "FLOSS" / "docs"),
        WatchSpec(
            "shared-surface",
            "skills",
            "recursive",
            workspace_root / "FLOSS" / "skill-corpus",
        ),
        WatchSpec(
            "shared-surface",
            "canon",
            "recursive",
            workspace_root / "FLOSS",
        ),
        WatchSpec(
            "traces",
            "traces",
            "recursive",
            Path.home() / ".floss_agent" / "traces" / "consensus",
        ),
        WatchSpec(
            "traces",
            "traces",
            "file",
            Path.home() / ".floss_agent" / "hook.log",
        ),
    ]


def should_include(path: Path, workspace_root: Path) -> bool:
    if path.name == "package-lock.json":
        return False
    rel_posix = None
    try:
        rel_posix = path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        rel_posix = None
    if rel_posix:
        if any(
            rel_posix == subtree or rel_posix.startswith(f"{subtree}/")
            for subtree in RESERVED_AGENT_SURFACE_SUBTREES
        ):
            return False
    if ".agent-surface" in path.parts:
        return False
    if ".git" in path.parts:
        return False
    # Prune dependency/build trees at any depth. Checked against the parent
    # parts only, so a file legitimately *named* e.g. "dist" is still watched.
    #
    # Matched against the path RELATIVE to the workspace, not the absolute one:
    # `path.parts` includes ancestors above the checkout, so a workspace living
    # under any directory that happens to be called `vendor`, `target`, `dist`
    # or `build` would exclude every file it watches and silently stop intake.
    # When the path is outside the workspace, rel_posix is None and there is
    # nothing meaningful to prune against, so the check is skipped — such paths
    # are already rejected by the subtree checks above.
    if rel_posix is not None:
        rel_parents = Path(rel_posix).parts[:-1]
        if EXCLUDED_DIR_NAMES.intersection(rel_parents):
            return False
    if path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return False
    if path.name.startswith("deepsource-"):
        return False
    if (
        path.resolve()
        == (
            workspace_root
            / "2026-04-15-102908-this-session-is-being-continued-from-a-previous-c.txt"
        ).resolve()
    ):
        return False
    return True


def emit_event(
    incoming_dir: Path,
    *,
    domain: str,
    corpus_hint: str,
    event_type: str,
    payload: dict[str, Any],
) -> Path:
    event = {
        "id": str(uuid.uuid4()),
        "observed_at": utcnow_iso(),
        "event_type": event_type,
        "watch_domain": domain,
        "source": "watch_intake.py",
        "corpus_hint": corpus_hint,
        **payload,
    }
    file_name = (
        f"{event['observed_at'].replace(':', '').replace('-', '')}"
        f"-{event['id']}.json"
    )
    path = incoming_dir / file_name
    write_json(path, event)
    return path


def scan_once(
    *,
    workspace_root: Path,
    event_root: Path,
    state_path: Path,
    emit_on_first_scan: bool,
    debounce_seconds: float,
) -> int:
    ensure_dirs(event_root)
    had_state = state_path.exists()
    previous = load_state(state_path)
    current: dict[str, dict[str, Any]] = {}
    emitted = 0
    incoming_dir = event_root / "incoming"
    now_ns = time.time_ns()

    # Backpressure guard (2026-07-07): never let the queue grow unboundedly.
    # Count with an early-exit scan so a flooded dir doesn't stall us.
    queue_depth = 0
    try:
        with os.scandir(incoming_dir) as entries:
            for _entry in entries:
                queue_depth += 1
                if queue_depth > MAX_INCOMING_QUEUE_DEPTH:
                    break
    except OSError:
        queue_depth = 0
    if queue_depth > MAX_INCOMING_QUEUE_DEPTH:
        print(
            f"[watch_intake] BACKPRESSURE: incoming queue > "
            f"{MAX_INCOMING_QUEUE_DEPTH} events; skipping emit this scan "
            f"(drain with process_intake_events.py)"
        )
        return 0

    # Remaining capacity for THIS scan.
    #
    # The depth check above runs once, before any emitting. On its own that
    # bounds the queue only at the moment the scan starts: at depth 4,999 a scan
    # that discovers 10,000 changes passed the guard and then emitted all of
    # them, recreating the exact flood the cap exists to prevent. This workspace
    # has an `incoming.flood-quarantine-20260616-17` directory from one such
    # event, so it is not hypothetical.
    #
    # Budget the emits instead. `_emit_within_budget` returns False once the cap
    # is reached, and what was withheld is reported rather than dropped silently
    # -- the files stay on disk and the next scan, after a drain, picks them up.
    emit_budget = max(0, MAX_INCOMING_QUEUE_DEPTH - queue_depth)
    withheld = 0
    # key -> the state entry to restore, or _DROP to remove the key entirely.
    # Applied just before save_state, NOT during the scan: `current` doubles as
    # the overlapping-spec dedup guard ("if key in current: continue"), so
    # mutating it mid-scan makes the same file be re-visited and re-withheld by
    # the next spec, inflating the counts and the queue.
    withheld_state: dict[str, Any] = {}

    def _emit_within_budget(**kwargs: Any) -> bool:
        nonlocal emit_budget, withheld
        if emit_budget <= 0:
            withheld += 1
            return False
        emit_event(**kwargs)
        emit_budget -= 1
        return True

    for spec in default_watch_specs(workspace_root):
        for path in iter_domain_files(spec):
            if not should_include(path, workspace_root):
                continue
            try:
                info = path_info(path, workspace_root)
            except OSError:
                continue
            key = info["abs_path"]
            # Overlapping-spec dedup (2026-07-07): the canon spec (FLOSS/docs)
            # and the broad shared-surface spec (FLOSS/) both visit the same
            # files. The fingerprint embeds watch_domain, so without this
            # first-spec-wins guard every overlapped file oscillates between
            # two fingerprints and emits a spurious "modified" event on every
            # scan — the root cause of the 2026-06-16/17 1.23M-event storm.
            if key in current:
                continue
            prior = previous.get(key)
            mtime_ns = int(info.get("mtime_ns") or 0)
            if debounce_seconds > 0 and (now_ns - mtime_ns) < int(
                debounce_seconds * 1_000_000_000
            ):
                if prior is not None:
                    current[key] = prior
                continue
            fingerprint = {
                "watch_domain": spec.domain,
                "corpus_hint": spec.corpus_hint,
                "size_bytes": info.get("size_bytes"),
                "mtime_ns": info.get("mtime_ns"),
                "sha256": info.get("sha256"),
                "rel_path": info.get("rel_path"),
            }
            current[key] = fingerprint
            if prior is None:
                if not had_state and not emit_on_first_scan:
                    continue
                if _emit_within_budget(
                    incoming_dir=incoming_dir,
                    domain=spec.domain,
                    corpus_hint=spec.corpus_hint,
                    event_type="created",
                    payload=info,
                ):
                    emitted += 1
                else:
                    # Withheld, so this file must NOT be recorded as seen --
                    # saved state is what the next scan diffs against. Leaving
                    # it in would mean the event is never emitted at all,
                    # turning backpressure into silent loss.
                    withheld_state[key] = _DROP
                continue
            if prior != fingerprint:
                if _emit_within_budget(
                    incoming_dir=incoming_dir,
                    domain=spec.domain,
                    corpus_hint=spec.corpus_hint,
                    event_type="modified",
                    payload=info,
                ):
                    emitted += 1
                else:
                    # Same reasoning as the created branch: keep the PRIOR
                    # fingerprint so the next scan still sees a difference.
                    withheld_state[key] = prior

    for abs_path, prior in previous.items():
        if abs_path in current:
            continue
        # Deletions are inferred from stored state, not from a directory walk,
        # so they never pass through should_include(). A state file written
        # before an exclusion rule existed will therefore emit a `deleted`
        # event for every now-excluded path — 2157 of 2487 on the first run
        # after EXCLUDED_DIR_NAMES landed, all node_modules. Filter here too.
        if not should_include(Path(abs_path), workspace_root):
            continue
        if _emit_within_budget(
            incoming_dir=incoming_dir,
            domain=str(prior.get("watch_domain", "other")),
            corpus_hint=str(prior.get("corpus_hint", "reference")),
            event_type="deleted",
            payload={
                "abs_path": abs_path,
                "rel_path": prior.get("rel_path"),
            },
        ):
            emitted += 1
        else:
            # Deletions are inferred from stored state. If a withheld deletion
            # were allowed to drop out of `current`, the saved state would lose
            # the path entirely and the deletion would never be reported. Carry
            # it forward; the next scan finds the file still absent and retries.
            withheld_state[abs_path] = prior

    for key, restore in withheld_state.items():
        if restore is _DROP:
            current.pop(key, None)
        else:
            current[key] = restore

    if withheld:
        print(
            f"[watch_intake] BACKPRESSURE: emitted {emitted} and withheld "
            f"{withheld} event(s) to stay within {MAX_INCOMING_QUEUE_DEPTH}; "
            f"drain with process_intake_events.py and re-scan"
        )

    with lock_file(event_root / "locks", "watch-state"):
        save_state(state_path, current)
    return emitted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit normalized IntakeEvent files for high-signal workspace changes."
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help=f"Workspace root to scan (default: {DEFAULT_WORKSPACE_ROOT})",
    )
    parser.add_argument(
        "--event-root",
        type=Path,
        default=DEFAULT_EVENT_ROOT,
        help=f"Queue root for incoming/processed events (default: {DEFAULT_EVENT_ROOT})",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        default=DEFAULT_STATE_PATH,
        help=f"Watcher state file (default: {DEFAULT_STATE_PATH})",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Poll continuously instead of running a single scan.",
    )
    parser.add_argument(
        "--emit-on-first-scan",
        action="store_true",
        help="Emit created events even when no prior watcher state exists.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=5.0,
        help="Polling interval when --loop is set (default: 5.0)",
    )
    parser.add_argument(
        "--debounce-seconds",
        type=float,
        default=DEFAULT_DEBOUNCE_SECONDS,
        help=(
            "Require files to remain unchanged for this many seconds before "
            f"emitting events (default: {DEFAULT_DEBOUNCE_SECONDS})"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace_root = args.workspace_root.resolve()
    event_root = args.event_root.resolve()
    state_path = args.state_path.resolve()

    if args.loop:
        while True:
            emitted = scan_once(
                workspace_root=workspace_root,
                event_root=event_root,
                state_path=state_path,
                emit_on_first_scan=args.emit_on_first_scan,
                debounce_seconds=max(args.debounce_seconds, 0.0),
            )
            print(f"[watch_intake] emitted {emitted} event(s)")
            time.sleep(max(args.interval_seconds, 0.25))
    else:
        emitted = scan_once(
            workspace_root=workspace_root,
            event_root=event_root,
            state_path=state_path,
            emit_on_first_scan=args.emit_on_first_scan,
            debounce_seconds=max(args.debounce_seconds, 0.0),
        )
        print(f"[watch_intake] emitted {emitted} event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
