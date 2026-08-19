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
RESERVED_AGENT_SURFACE_SUBTREES = {
    ".agent-surface",
    ".agent-surface/events",
    ".agent-surface/shadows",
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

    for spec in default_watch_specs(workspace_root):
        for path in iter_domain_files(spec):
            if not should_include(path, workspace_root):
                continue
            try:
                info = path_info(path, workspace_root)
            except OSError:
                continue
            key = info["abs_path"]
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
                emit_event(
                    incoming_dir,
                    domain=spec.domain,
                    corpus_hint=spec.corpus_hint,
                    event_type="created",
                    payload=info,
                )
                emitted += 1
                continue
            if prior != fingerprint:
                emit_event(
                    incoming_dir,
                    domain=spec.domain,
                    corpus_hint=spec.corpus_hint,
                    event_type="modified",
                    payload=info,
                )
                emitted += 1

    for abs_path, prior in previous.items():
        if abs_path in current:
            continue
        emit_event(
            incoming_dir,
            domain=str(prior.get("watch_domain", "other")),
            corpus_hint=str(prior.get("corpus_hint", "reference")),
            event_type="deleted",
            payload={
                "abs_path": abs_path,
                "rel_path": prior.get("rel_path"),
            },
        )
        emitted += 1

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
