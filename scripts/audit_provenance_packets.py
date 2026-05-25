"""Validate and narrate provenance packets under `.agent-surface/provenance`.

The audit feed is intentionally human-legible: one line per payload entry when a
packet validates, one error line per invalid packet when it does not.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

FLOSS_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = FLOSS_ROOT.parent
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))

from packages.activity_log import provenance  # noqa: E402


def _iter_packet_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def audit_packets(
    provenance_root: Path,
    *,
    workspace_root: Path,
) -> tuple[int, list[dict[str, Any]], list[str]]:
    """Return invalid count, machine records, and human narrative lines."""

    records: list[dict[str, Any]] = []
    lines: list[str] = []
    invalid_count = 0
    for path in _iter_packet_paths(provenance_root):
        result = provenance.validate_packet(
            path,
            workspace_root=workspace_root,
            provenance_root=provenance_root,
        )
        rel_path = path.resolve().relative_to(workspace_root.resolve()).as_posix()
        record = {
            "path": rel_path,
            "ok": result.ok,
            "packet_digest": result.packet_digest,
            "errors": result.errors,
            "narrative_lines": result.narrative_lines,
        }
        records.append(record)
        if result.ok:
            lines.extend(result.narrative_lines)
        else:
            invalid_count += 1
            lines.append(f"[INVALID] {rel_path} :: {';'.join(result.errors)}")
    return invalid_count, records, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=WORKSPACE_ROOT,
        help="Workspace root that artifact refs resolve against.",
    )
    parser.add_argument(
        "--provenance-root",
        type=Path,
        default=WORKSPACE_ROOT / ".agent-surface" / "provenance",
        help="Packet directory to scan.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable audit records instead of narrative lines.",
    )
    args = parser.parse_args(argv)

    invalid_count, records, lines = audit_packets(
        args.provenance_root,
        workspace_root=args.workspace_root,
    )
    if args.json:
        print(json.dumps(records, indent=2, ensure_ascii=False))
    else:
        for line in lines:
            print(line)
    return 1 if invalid_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
