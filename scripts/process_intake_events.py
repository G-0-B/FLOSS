"""Process normalized IntakeEvent queue files into summaries and follow-up hints."""

from __future__ import annotations

import argparse
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WORKSPACE_ROOT = REPO_ROOT.parent
DEFAULT_EVENT_ROOT = DEFAULT_WORKSPACE_ROOT / ".agent-surface" / "events"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_dirs(event_root: Path) -> None:
    for name in ("incoming", "processing", "processed", "failed", "locks"):
        (event_root / name).mkdir(parents=True, exist_ok=True)


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
            time.sleep(0.1)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
        yield path
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def queue_paths(event_root: Path) -> dict[str, Path]:
    return {
        "incoming": event_root / "incoming",
        "processing": event_root / "processing",
        "processed": event_root / "processed",
        "failed": event_root / "failed",
        "locks": event_root / "locks",
        "summary_json": event_root / "queue-summary.json",
        "summary_md": event_root / "QUEUE_SUMMARY.md",
    }


def claim_event_file(incoming_dir: Path, processing_dir: Path) -> Path | None:
    for path in sorted(incoming_dir.glob("*.json")):
        target = processing_dir / path.name
        try:
            path.replace(target)
            return target
        except FileNotFoundError:
            continue
    return None


def classify_actions(event: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    domain = event.get("watch_domain")
    rel_path = str(event.get("rel_path") or "")
    abs_path = str(event.get("abs_path") or "")

    if domain == "root-intake":
        actions.extend(["review_root_intake", "consider_canon_promotion"])
    if domain == "traces":
        actions.append("review_trace_drift")
    if domain in {"canon", "shared-surface"}:
        actions.append("refresh_context_views")
    if "skill-corpus" in rel_path or rel_path.endswith("shared-skill-surface.json"):
        actions.append("refresh_shared_skills")
    if (
        rel_path.endswith("shared-agent-surface.json")
        or rel_path.endswith("shared-hook-surface.json")
        or rel_path == ".mcp.json"
    ):
        actions.append("refresh_shared_agent_surface")
    if rel_path.endswith("shared-context-surface.json"):
        actions.append("refresh_context_views")
    if not actions and abs_path:
        actions.append("review_event")
    return sorted(dict.fromkeys(actions))


def enrich_event(event: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(event)
    enriched["recommended_actions"] = classify_actions(event)
    return enriched


def recent_processed(processed_dir: Path, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(processed_dir.glob("*.json"), reverse=True)[:limit]:
        try:
            items.append(load_json(path))
        except json.JSONDecodeError:
            continue
    return items


def build_summary(recent: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    by_domain: dict[str, int] = {}
    by_action: dict[str, int] = {}
    for event in recent:
        domain = str(event.get("watch_domain", "other"))
        by_domain[domain] = by_domain.get(domain, 0) + 1
        for action in event.get("recommended_actions", []):
            by_action[action] = by_action.get(action, 0) + 1

    summary_json = {
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "recent_count": len(recent),
        "by_domain": by_domain,
        "by_action": by_action,
        "recent": recent[:20],
    }
    lines = [
        "# Intake Queue Summary",
        "",
        f"Recent processed events: `{len(recent)}`",
        "",
        "## By Domain",
        "",
    ]
    for domain, count in sorted(by_domain.items()):
        lines.append(f"- `{domain}`: {count}")
    lines.extend(["", "## Recommended Actions", ""])
    for action, count in sorted(by_action.items()):
        lines.append(f"- `{action}`: {count}")
    lines.extend(["", "## Recent Events", ""])
    for event in recent[:10]:
        rel = event.get("rel_path") or event.get("abs_path")
        lines.append(
            f"- `{event.get('event_type')}` `{rel}` -> "
            f"{', '.join(event.get('recommended_actions', [])) or 'review_event'}"
        )
    return summary_json, "\n".join(lines) + "\n"


def process_once(event_root: Path, *, limit: int, summary_depth: int) -> int:
    ensure_dirs(event_root)
    paths = queue_paths(event_root)
    processed_count = 0

    while processed_count < limit:
        claimed = claim_event_file(paths["incoming"], paths["processing"])
        if claimed is None:
            break
        try:
            event = load_json(claimed)
            enriched = enrich_event(event)
            target = paths["processed"] / claimed.name
            write_json(target, enriched)
            claimed.unlink(missing_ok=True)
            processed_count += 1
        except Exception as exc:  # noqa: BLE001
            failed = paths["failed"] / claimed.name
            payload = {
                "error": str(exc),
                "source_file": str(claimed),
            }
            write_json(failed, payload)
            claimed.unlink(missing_ok=True)

    recent = recent_processed(paths["processed"], summary_depth)
    summary_json, summary_md = build_summary(recent)
    try:
        with lock_file(paths["locks"], "summary"):
            write_json(paths["summary_json"], summary_json)
            write_text(paths["summary_md"], summary_md)
    except TimeoutError as exc:
        failed_name = (
            f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-"
            "summary-lock-timeout.json"
        )
        write_json(
            paths["failed"] / failed_name,
            {
                "error": str(exc),
                "source": "process_intake_events.py",
                "stage": "summary",
                "recent_count": len(recent),
            },
        )

    return processed_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process IntakeEvent queue files into summaries and follow-up hints."
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help=f"Workspace root (default: {DEFAULT_WORKSPACE_ROOT})",
    )
    parser.add_argument(
        "--event-root",
        type=Path,
        default=DEFAULT_EVENT_ROOT,
        help=f"Queue root (default: {DEFAULT_EVENT_ROOT})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum events to process in one run (default: 50)",
    )
    parser.add_argument(
        "--summary-depth",
        type=int,
        default=100,
        help="How many processed events to include in summary rollups (default: 100)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    event_root = args.event_root.resolve()
    processed = process_once(
        event_root,
        limit=max(args.limit, 1),
        summary_depth=max(args.summary_depth, 1),
    )
    print(f"[process_intake_events] processed {processed} event(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
