#!/usr/bin/env python3
"""orient_probe.py — FLOSSI0ULLK orientation probe.

Emits a deterministic markdown packet describing which canonical artifacts are
present, fresh, and cheap to read. No mutation. No network. Stdlib only.

Designed to be the mandatory Step 0 of the flossi0ullk-orient skill. Run from
the repo root:

    python FLOSS/scripts/orient_probe.py --query "task in one line"

Exit codes:
    0  probe succeeded (packet emitted)
    2  probe ran but flagged a blocking issue (e.g. lock file present)
    3  invalid invocation

Output is intentionally compact (target: well under 500 tokens).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Canonical entry points declared by the orient skill. Keep in sync with
# references/entry-points.md.
CANONICAL_FILES: list[tuple[str, str, str]] = [
    # (path, tier, one-line purpose)
    (".agent-surface/context/CONTEXT_L0.md", "T1", "Cheap re-orientation context"),
    (".agent-surface/context/CONTEXT_L1.md", "T2", "Deeper re-orientation context"),
    ("INDEX.md", "T1", "Repo-root map"),
    ("FLOSS/CLAUDE.md", "T1", "Agent operating notes"),
    ("FLOSS/FLOSSI0ULLK_Master_Metaprompt_v1_3_1_Kernel.md", "T1*", "Governing principles (only if relevant)"),
    ("FLOSS/scripts/context_router.py", "T1.5", "Query -> corpus roots"),
    ("FLOSS/docs/architecture/CONTEXT_DAEMON_ARCHITECTURE.md", "T2", "Intake/filewatch arch"),
    ("FLOSS/docs/superpowers/plans/2026-04-19-filewatch-metaharness.md", "T2", "Filewatch metaharness plan"),
    ("FLOSS/scripts/watch_intake.py", "T2", "Intake watcher"),
    ("FLOSS/scripts/process_intake_events.py", "T2", "Intake event processor"),
]

EVENTS_DIR = ".agent-surface/events"
LOCK_DIRS = [".agent-surface/events/locks", ".agent-surface/context"]  # *.lock; events/locks = confirmed writer convention (watch_intake/process_intake_events lock_file())
STALENESS_DAYS_L0 = 14


@dataclass
class FileStatus:
    path: str
    tier: str
    purpose: str
    present: bool
    size: Optional[int] = None
    mtime: Optional[float] = None
    sha256_prefix: Optional[str] = None

    @property
    def age_days(self) -> Optional[float]:
        if self.mtime is None:
            return None
        return (time.time() - self.mtime) / 86400.0

    @property
    def stale_l0(self) -> bool:
        return (
            self.path.endswith("CONTEXT_L0.md")
            and self.age_days is not None
            and self.age_days > STALENESS_DAYS_L0
        )


def sha256_prefix(path: Path, *, nbytes: int = 1 << 20) -> str:
    """Return first 12 hex chars of sha256 over up to nbytes of file content."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(nbytes))
    return h.hexdigest()[:12]


def stat_file(path: Path, *, tier: str, purpose: str) -> FileStatus:
    rel = str(path)
    if not path.exists():
        return FileStatus(path=rel, tier=tier, purpose=purpose, present=False)
    try:
        st = path.stat()
        return FileStatus(
            path=rel,
            tier=tier,
            purpose=purpose,
            present=True,
            size=st.st_size,
            mtime=st.st_mtime,
            sha256_prefix=sha256_prefix(path),
        )
    except OSError as exc:
        return FileStatus(
            path=rel,
            tier=tier,
            purpose=f"{purpose} (stat error: {exc})",
            present=False,
        )


def events_queue_depth(root: Path) -> Optional[int]:
    events = root / EVENTS_DIR
    if not events.is_dir():
        return None
    try:
        return sum(1 for _ in events.iterdir())
    except OSError:
        return None


def lock_files(root: Path) -> list[str]:
    found: list[str] = []
    for rel in LOCK_DIRS:
        d = root / rel
        if not d.is_dir():
            continue
        try:
            found.extend(f"{rel}/{p.name}" for p in d.iterdir() if p.suffix == ".lock")
        except OSError:
            continue
    return sorted(found)


def try_router(root: Path, query: str, *, limit: int) -> tuple[bool, str]:
    """Run context_router.py if present. Return (ran_ok, captured_output)."""
    script = root / "FLOSS/scripts/context_router.py"
    if not script.is_file():
        return False, "router script not found"
    python = shutil.which("python3") or shutil.which("python")
    if python is None:
        return False, "no python interpreter on PATH"
    try:
        result = subprocess.run(
            [python, str(script), query, "--format", "markdown", "--limit", str(limit)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"router invocation failed: {exc}"
    if result.returncode != 0:
        return False, f"router exited {result.returncode}: {result.stderr.strip()[:400]}"
    out = result.stdout.strip()
    # Keep the packet bounded — cap router output to ~40 lines.
    lines = out.splitlines()
    if len(lines) > 40:
        out = "\n".join(lines[:40]) + "\n... (truncated)"
    return True, out


def fmt_time(ts: Optional[float]) -> str:
    if ts is None:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts)) + "Z"


def render_markdown(
    *,
    query: str,
    statuses: list[FileStatus],
    queue_depth: Optional[int],
    locks: list[str],
    router_ran: bool,
    router_output: str,
) -> str:
    lines: list[str] = []
    lines.append("# FLOSSI0ULLK orientation packet")
    lines.append("")
    lines.append(f"- query: `{query or '(none)'}`")
    lines.append(f"- utc: `{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}`")
    if queue_depth is None:
        lines.append("- events queue: `(absent)`")
    else:
        lines.append(f"- events queue depth: `{queue_depth}`")
    if locks:
        lines.append(f"- **LOCKS PRESENT**: {', '.join(locks)} — wait before reading context.")
    lines.append("")
    lines.append("## Canonical artifacts")
    lines.append("")
    lines.append("| tier | present | age (d) | size | sha256 | path | note |")
    lines.append("| ---- | ------- | ------- | ---- | ------ | ---- | ---- |")
    for s in statuses:
        age = f"{s.age_days:.1f}" if s.age_days is not None else "-"
        size = f"{s.size}" if s.size is not None else "-"
        sha = s.sha256_prefix or "-"
        note_bits = []
        if s.stale_l0:
            note_bits.append(f"stale>{STALENESS_DAYS_L0}d")
        note = ",".join(note_bits) or s.purpose
        flag = "YES" if s.present else "MISSING"
        lines.append(f"| {s.tier} | {flag} | {age} | {size} | {sha} | `{s.path}` | {note} |")
    lines.append("")
    lines.append("## Router")
    lines.append("")
    if router_ran:
        lines.append("Ran. Output:")
        lines.append("")
        lines.append("```markdown")
        lines.append(router_output)
        lines.append("```")
    else:
        lines.append(f"Not run: {router_output}")
    lines.append("")
    lines.append("## Recommended reads (stop at lowest tier that answers the task)")
    lines.append("")
    present_by_tier: dict[str, list[str]] = {}
    for s in statuses:
        if s.present:
            present_by_tier.setdefault(s.tier, []).append(s.path)
    for tier in ("T1", "T1*", "T1.5", "T2"):
        if tier in present_by_tier:
            lines.append(f"- **{tier}**: " + ", ".join(f"`{p}`" for p in present_by_tier[tier]))
    if not present_by_tier:
        lines.append("- none of the declared canon is present — cold start; see entry-points.md.")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="FLOSSI0ULLK orientation probe")
    parser.add_argument("--query", default="", help="One-line task description")
    parser.add_argument("--root", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--limit", type=int, default=4, help="Router result limit")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of markdown")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root not a directory: {root}", file=sys.stderr)
        return 3

    os.chdir(root)

    statuses = [
        stat_file(Path(p), tier=tier, purpose=purpose)
        for (p, tier, purpose) in CANONICAL_FILES
    ]
    queue_depth = events_queue_depth(root)
    locks = lock_files(root)
    router_ran, router_output = try_router(root, args.query or "orient", limit=args.limit)

    if args.json:
        payload = {
            "query": args.query,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "events_queue_depth": queue_depth,
            "locks": locks,
            "router": {"ran": router_ran, "output": router_output},
            "files": [
                {
                    "path": s.path,
                    "tier": s.tier,
                    "present": s.present,
                    "size": s.size,
                    "mtime": s.mtime,
                    "age_days": s.age_days,
                    "sha256_prefix": s.sha256_prefix,
                    "purpose": s.purpose,
                }
                for s in statuses
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(
            render_markdown(
                query=args.query,
                statuses=statuses,
                queue_depth=queue_depth,
                locks=locks,
                router_ran=router_ran,
                router_output=router_output,
            )
        )

    return 2 if locks else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
