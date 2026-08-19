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


MUTABLE_GENERATED_PATH_PREFIXES = (
    ".agent-surface/",
    ".claude/",
    ".gemini/",
    ".vibe/",
    "opworkers/.opencode/",
)
MUTABLE_GENERATED_EXACT_PATHS = {
    "FLOSS/.mcp.json",
    "FLOSS/docs/agent-memory/MEMORY.md",
    "FLOSS/docs/agent-memory/CHATGPT_MEMORY_EXPORT.md",
    "opworkers/opencode.jsonc",
    "vibe-floss.ps1",
}


def _iter_packet_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.json") if path.is_file())


def _normalize_ref_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _resolve_workspace_ref(ref: str, workspace_root: Path) -> Path:
    path = Path(ref)
    if path.is_absolute():
        return path
    return workspace_root / ref


def _is_mutable_generated_ref(path: str) -> bool:
    normalized = _normalize_ref_path(path)
    if normalized in MUTABLE_GENERATED_EXACT_PATHS:
        return True
    return any(
        normalized.startswith(prefix)
        or f"/{prefix}" in normalized
        for prefix in MUTABLE_GENERATED_PATH_PREFIXES
    )


def _artifact_mismatches(packet: dict[str, Any], workspace_root: Path) -> list[str]:
    mismatches: list[str] = []
    for entry in packet.get("a", []) or []:
        for ref in entry.get("artifact_refs", []) or []:
            if not isinstance(ref, dict):
                continue
            raw_path = ref.get("path")
            expected = ref.get("sha256")
            if not isinstance(raw_path, str) or not isinstance(expected, str):
                continue
            path = _resolve_workspace_ref(raw_path, workspace_root)
            if path.exists() and provenance.sha256_file(path) != expected:
                mismatches.append(raw_path)
    return sorted(set(mismatches))


def _packet_sequence(packet: dict[str, Any] | None) -> int:
    if not packet:
        return -1
    try:
        return int(packet.get("s", -1))
    except (TypeError, ValueError):
        return -1


def _packet_claim_types(packet: dict[str, Any] | None) -> set[str]:
    if not packet:
        return set()
    return {
        str(entry.get("claim_type"))
        for entry in packet.get("a", []) or []
        if isinstance(entry, dict) and entry.get("claim_type")
    }


def _packet_artifact_paths(packet: dict[str, Any] | None) -> set[str]:
    if not packet:
        return set()
    paths: set[str] = set()
    for entry in packet.get("a", []) or []:
        if not isinstance(entry, dict):
            continue
        for ref in entry.get("artifact_refs", []) or []:
            if isinstance(ref, dict) and isinstance(ref.get("path"), str):
                paths.add(_normalize_ref_path(ref["path"]))
    return paths


def _find_newer_valid_packet(
    record: dict[str, Any],
    valid_records: list[dict[str, Any]],
) -> str | None:
    packet = record.get("_packet")
    if not isinstance(packet, dict):
        return None
    agent_id = packet.get("i")
    sequence = _packet_sequence(packet)
    claim_types = _packet_claim_types(packet)
    artifact_paths = _packet_artifact_paths(packet)
    if not agent_id or sequence < 0 or not claim_types or not artifact_paths:
        return None

    for candidate in valid_records:
        candidate_packet = candidate.get("_packet")
        if not isinstance(candidate_packet, dict):
            continue
        if candidate_packet.get("i") != agent_id:
            continue
        if _packet_sequence(candidate_packet) <= sequence:
            continue
        if not (claim_types & _packet_claim_types(candidate_packet)):
            continue
        if not (artifact_paths & _packet_artifact_paths(candidate_packet)):
            continue
        digest = candidate.get("packet_digest")
        if isinstance(digest, str):
            return digest
    return None


def _classify_record(
    record: dict[str, Any],
    *,
    valid_records: list[dict[str, Any]],
    workspace_root: Path,
) -> None:
    if record["ok"]:
        record["audit_status"] = "valid"
        return

    errors = set(record.get("errors", []))
    record["audit_status"] = "invalid"
    if errors != {"E_PROVENANCE_ARTIFACT_HASH_MISMATCH"}:
        return

    superseded_by = _find_newer_valid_packet(record, valid_records)
    if superseded_by:
        record["audit_status"] = "superseded"
        record["superseded_reason"] = "newer_valid_packet"
        record["superseded_by"] = superseded_by
        return

    packet = record.get("_packet")
    if not isinstance(packet, dict):
        return
    mismatches = _artifact_mismatches(packet, workspace_root)
    record["artifact_mismatches"] = mismatches
    if mismatches and all(_is_mutable_generated_ref(path) for path in mismatches):
        record["audit_status"] = "superseded"
        record["superseded_reason"] = "mutable_generated_artifact_drift"


def audit_packets(
    provenance_root: Path,
    *,
    workspace_root: Path,
) -> tuple[int, list[dict[str, Any]], list[str]]:
    """Return invalid count, machine records, and human narrative lines."""

    records: list[dict[str, Any]] = []
    lines: list[str] = []
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
            "_packet": result.packet,
        }
        records.append(record)

    valid_records = [record for record in records if record["ok"]]
    for record in records:
        _classify_record(
            record,
            valid_records=valid_records,
            workspace_root=workspace_root,
        )
        if record["audit_status"] == "valid":
            lines.extend(record["narrative_lines"])
        elif record["audit_status"] == "superseded":
            lines.append(
                "[SUPERSEDED] "
                f"{record['path']} :: "
                f"{record.get('superseded_reason', 'unknown')} :: "
                f"{';'.join(record['errors'])}"
            )
        else:
            lines.append(f"[INVALID] {record['path']} :: {';'.join(record['errors'])}")

    invalid_count = sum(1 for record in records if record["audit_status"] == "invalid")
    for record in records:
        record.pop("_packet", None)
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
