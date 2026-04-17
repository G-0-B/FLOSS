"""Hashline-style deterministic edit verification helpers.

This is a practical spike, not a full omniscient diff engine.

Given the hook payload plus the current file contents, we verify whether the
edit intent appears to have landed where expected and render hashlined evidence
for later consensus and trace review. A pre-write checkpoint can provide an
exact expected post-image so stale/intervened writes do not look clean.

Status levels:
  - VERIFIED: strong evidence the intended landing is present
  - UNVERIFIED: the intended landing is present, but ambiguity remains
  - MISMATCH: strong evidence the intended landing failed
  - SKIPPED / ERROR: unsupported tool shape or unreadable file
"""

from __future__ import annotations

import base64
import hashlib
import json
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HASHLINE_ID_CHARS = 6
MAX_HASHLINE_RENDER_LINES = 4
MAX_MATCHES = 2
MAX_LINE_PREVIEW_CHARS = 140
CHECKPOINT_SCHEMA_VERSION = "0.1.0"
CHECKPOINT_FILENAME_HASH_CHARS = 12


def _short_hash(text: str) -> str:
    """Return a short stable token for display-oriented hashline identifiers."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    token = base64.b32encode(digest).decode("ascii").rstrip("=")
    return token[:HASHLINE_ID_CHARS]


def _sha256_text(text: str) -> str:
    """Return the full SHA-256 hex digest for a UTF-8 text payload."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _utcnow_iso() -> str:
    """Return the current UTC time in a stable Z-suffixed timestamp format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _resolve_file_path(file_path: str) -> str:
    """Return a normalized absolute path string for checkpoint signatures."""
    return str(Path(file_path).resolve(strict=False))


def _canonical_tool_name(tool_name: str) -> str:
    """Normalize a tool name into the lowercase routing key used by hashline."""
    return (tool_name or "").strip().lower()


def _string_value(value: Any) -> str:
    """Coerce arbitrary tool payload values into stable string content."""
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _canonical_edit(edit: dict[str, Any]) -> dict[str, str]:
    """Normalize a replace-style edit payload into plain string fields."""
    return {
        "old_string": _string_value(edit.get("old_string", "")),
        "new_string": _string_value(edit.get("new_string", "")),
    }


def _canonical_tool_intent(
    tool_name: str,
    tool_input: dict[str, Any],
) -> dict[str, Any]:
    """Reduce tool input to the deterministic fields relevant for verification."""
    tool = _canonical_tool_name(tool_name)
    if tool in {"edit", "replace"}:
        return _canonical_edit(tool_input)
    if tool in {"write", "write_file"}:
        return {
            "content": _string_value(tool_input.get("content", "")),
        }
    if tool == "multiedit":
        edits = tool_input.get("edits") or []
        if not isinstance(edits, list):
            edits = []
        return {
            "edits": [
                _canonical_edit(edit) for edit in edits if isinstance(edit, dict)
            ],
        }
    try:
        return json.loads(json.dumps(tool_input, sort_keys=True, default=str))
    except TypeError:
        return {"raw_tool_input": str(tool_input)}


def build_tool_signature(
    file_path: str,
    tool_name: str,
    tool_input: dict[str, Any],
) -> str:
    """Hash the file path plus canonicalized tool intent into a stable signature."""
    payload = {
        "tool_name": _canonical_tool_name(tool_name),
        "file_path": _resolve_file_path(file_path),
        "intent": _canonical_tool_intent(tool_name, tool_input),
    }
    serialized = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _checkpoint_filename(signature: str) -> str:
    """Build a sortable checkpoint filename from a signature prefix and UTC stamp."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return f"{stamp}-{signature[:CHECKPOINT_FILENAME_HASH_CHARS]}.json"


def _render_exact_expected_post(
    tool_name: str,
    intent: dict[str, Any],
    pre_text: str | None,
) -> tuple[str | None, str]:
    """Derive the exact expected post-image when the tool payload makes it possible."""
    tool = _canonical_tool_name(tool_name)

    if tool in {"write", "write_file"}:
        return (
            _string_value(intent.get("content", "")),
            "Exact post-image derived from full file content payload.",
        )

    if pre_text is None:
        return (
            None,
            "Pre-write file text unavailable; exact post-image could not be derived.",
        )

    if tool in {"edit", "replace"}:
        old_string = _string_value(intent.get("old_string", ""))
        new_string = _string_value(intent.get("new_string", ""))
        if not old_string:
            return (
                None,
                "Exact post-image unavailable because the old snippet was empty.",
            )
        old_count = pre_text.count(old_string)
        if old_count != 1:
            return (
                None,
                "Exact post-image unavailable because the old snippet matched "
                f"{old_count} times in the pre-write file.",
            )
        return (
            pre_text.replace(old_string, new_string, 1),
            "Exact post-image derived from the pre-write checkpoint and replace "
            "payload.",
        )

    if tool == "multiedit":
        edits = intent.get("edits") or []
        if not isinstance(edits, list) or not edits:
            return (
                None,
                "Exact post-image unavailable because the multi-edit payload "
                "was empty.",
            )
        current = pre_text
        for idx, edit in enumerate(edits, start=1):
            if not isinstance(edit, dict):
                return (
                    None,
                    "Exact post-image unavailable because sub-edit "
                    f"{idx} was not an object.",
                )
            old_string = _string_value(edit.get("old_string", ""))
            new_string = _string_value(edit.get("new_string", ""))
            if not old_string:
                return (
                    None,
                    "Exact post-image unavailable because sub-edit "
                    f"{idx} had an empty old snippet.",
                )
            old_count = current.count(old_string)
            if old_count != 1:
                return (
                    None,
                    "Exact post-image unavailable because sub-edit "
                    f"{idx} matched {old_count} times in the pre-write file.",
                )
            current = current.replace(old_string, new_string, 1)
        return (
            current,
            "Exact post-image derived by replaying the multi-edit payload on the "
            "pre-write checkpoint.",
        )

    return (
        None,
        f"Exact post-image unavailable for unsupported tool {tool_name!r}.",
    )


def build_pre_write_checkpoint(
    file_path: str,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    pre_text: str | None,
    source_exists: bool,
    hook_event_name: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    """Build the persisted checkpoint payload captured before a file write lands."""
    intent = _canonical_tool_intent(tool_name, tool_input)
    expected_post_text, expected_reason = _render_exact_expected_post(
        tool_name,
        intent,
        pre_text,
    )
    signature = build_tool_signature(file_path, tool_name, tool_input)
    normalized_file_path = _resolve_file_path(file_path)
    checkpoint = {
        "schema_version": CHECKPOINT_SCHEMA_VERSION,
        "created_at": _utcnow_iso(),
        "signature": signature,
        "tool_name": _canonical_tool_name(tool_name),
        "file_path": normalized_file_path,
        "hook_event_name": hook_event_name or "",
        "session_id": session_id or "",
        "source_exists": bool(source_exists),
        "pre_write_sha256": _sha256_text(pre_text) if pre_text is not None else None,
        "pre_write_hashlines": (
            render_hashlines(pre_text) if pre_text is not None else []
        ),
        "intent": intent,
        "exact_expected_post_sha256": (
            _sha256_text(expected_post_text) if expected_post_text is not None else None
        ),
        "exact_expected_post_hashlines": (
            render_hashlines(expected_post_text)
            if expected_post_text is not None
            else []
        ),
        "exact_expected_post_available": expected_post_text is not None,
        "exact_expected_post_reason": expected_reason,
        "consumed_at": None,
    }
    return checkpoint


def write_pre_write_checkpoint(
    checkpoint_dir: str | Path,
    checkpoint: dict[str, Any],
) -> Path:
    """Persist a pre-write checkpoint payload to disk and return its path."""
    directory = Path(checkpoint_dir)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / _checkpoint_filename(checkpoint["signature"])
    target.write_text(
        json.dumps(checkpoint, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return target


def claim_pre_write_checkpoint(
    checkpoint_dir: str | Path,
    file_path: str,
    tool_name: str,
    tool_input: dict[str, Any],
) -> dict[str, Any] | None:
    """Mark the latest matching checkpoint consumed and return its payload."""
    directory = Path(checkpoint_dir)
    if not directory.exists():
        return None

    signature = build_tool_signature(file_path, tool_name, tool_input)
    candidates = sorted(
        directory.glob(f"*-{signature[:CHECKPOINT_FILENAME_HASH_CHARS]}.json"),
        reverse=True,
    )
    for candidate in candidates:
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(payload, dict):
            continue
        if payload.get("signature") != signature:
            continue
        if payload.get("consumed_at"):
            continue
        payload["consumed_at"] = _utcnow_iso()
        try:
            candidate.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except Exception:  # noqa: BLE001
            continue
        payload["_checkpoint_path"] = str(candidate)
        return payload
    return None


def render_hashlines(
    text: str,
    *,
    start_line: int = 1,
    max_lines: int = MAX_HASHLINE_RENDER_LINES,
) -> list[str]:
    """Render stable per-line fingerprints for a bounded slice of text."""
    lines = text.splitlines()
    rendered: list[str] = []
    for idx, line in enumerate(lines[:max_lines], start=start_line):
        preview = line[:MAX_LINE_PREVIEW_CHARS]
        rendered.append(f"{idx}#{_short_hash(line)}| {preview}")
    if len(lines) > max_lines:
        rendered.append(f"... [{len(lines) - max_lines} more lines omitted]")
    return rendered


def _line_starts(text: str) -> list[int]:
    """Return the starting offset for each line in a text buffer."""
    starts = [0]
    for idx, ch in enumerate(text):
        if ch == "\n":
            starts.append(idx + 1)
    return starts


def _line_for_offset(starts: list[int], offset: int) -> int:
    """Resolve a character offset to its 1-based line number."""
    return bisect_right(starts, offset)


def _span_label(start_line: int, end_line: int) -> str:
    """Format a single-line or range label for matched snippets."""
    if start_line == end_line:
        return str(start_line)
    return f"{start_line}-{end_line}"


def find_snippet_matches(
    file_text: str,
    snippet: str,
    *,
    max_matches: int = MAX_MATCHES,
) -> list[dict[str, Any]]:
    """Locate up to `max_matches` snippet occurrences with line-based evidence."""
    if not snippet:
        return []

    starts = _line_starts(file_text)
    file_lines = file_text.splitlines()
    matches: list[dict[str, Any]] = []
    search_from = 0

    while len(matches) < max_matches:
        offset = file_text.find(snippet, search_from)
        if offset < 0:
            break
        start_line = _line_for_offset(starts, offset)
        end_offset = offset + max(len(snippet) - 1, 0)
        end_line = _line_for_offset(starts, end_offset)
        excerpt = "\n".join(file_lines[start_line - 1 : end_line])
        matches.append(
            {
                "start_line": start_line,
                "end_line": end_line,
                "span": _span_label(start_line, end_line),
                "hashlines": render_hashlines(excerpt, start_line=start_line),
            }
        )
        search_from = offset + 1

    return matches


def _verify_replace_like(
    file_text: str,
    *,
    old_string: str,
    new_string: str,
) -> dict[str, Any]:
    """Verify replace-style edits by comparing old and new snippet presence."""
    old_matches = find_snippet_matches(file_text, old_string)
    new_matches = find_snippet_matches(file_text, new_string)
    old_present = bool(old_matches) if old_string else False
    new_present = bool(new_matches) if new_string else False

    if new_present and (not old_present or old_string == new_string):
        status = "VERIFIED"
        reason = "New snippet landed and the old snippet is no longer present."
    elif new_present and old_present:
        status = "UNVERIFIED"
        reason = "New snippet landed, but the old snippet is still present elsewhere."
    elif old_present and not new_present:
        status = "MISMATCH"
        reason = "Old snippet is still present and the new snippet is absent."
    else:
        status = "MISMATCH"
        reason = "Neither the old nor the new snippet could be located after the write."

    return {
        "kind": "replace-like",
        "status": status,
        "reason": reason,
        "old_present": old_present,
        "new_present": new_present,
        "expected_old_hashlines": render_hashlines(old_string) if old_string else [],
        "expected_new_hashlines": render_hashlines(new_string) if new_string else [],
        "matched_old": old_matches,
        "matched_new": new_matches,
    }


def _verify_write_like(file_text: str, *, expected_content: str) -> dict[str, Any]:
    """Verify full-file write operations against the expected content payload."""
    exact_match = file_text == expected_content
    status = "VERIFIED" if exact_match else "MISMATCH"
    reason = (
        "File content matches the tool payload exactly."
        if exact_match
        else "File content differs from the tool payload after the write."
    )
    return {
        "kind": "write-like",
        "status": status,
        "reason": reason,
        "expected_sha256": _sha256_text(expected_content),
        "actual_sha256": _sha256_text(file_text),
        "expected_hashlines": render_hashlines(expected_content),
        "actual_hashlines": render_hashlines(file_text),
    }


def _verify_multiedit(file_text: str, *, edits: list[dict[str, Any]]) -> dict[str, Any]:
    """Verify each sub-edit in a multiedit payload and summarize the outcome."""
    checks = [
        _verify_replace_like(
            file_text,
            old_string=(edit.get("old_string", "") or ""),
            new_string=(edit.get("new_string", "") or ""),
        )
        for edit in edits
    ]
    mismatch_count = sum(1 for check in checks if check["status"] == "MISMATCH")
    unverified_count = sum(1 for check in checks if check["status"] == "UNVERIFIED")
    verified_count = sum(1 for check in checks if check["status"] == "VERIFIED")

    if mismatch_count:
        status = "MISMATCH"
    elif unverified_count:
        status = "UNVERIFIED"
    else:
        status = "VERIFIED"

    reason = (
        f"{verified_count}/{len(checks)} verified, "
        f"{unverified_count} unverified, "
        f"{mismatch_count} mismatched sub-edits."
    )
    return {
        "kind": "multiedit",
        "status": status,
        "reason": reason,
        "subchecks": checks,
    }


def _assess_pre_write_checkpoint(
    file_text: str,
    checkpoint: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Compare the current file with the claimed pre-write checkpoint evidence."""
    if not checkpoint:
        return None

    actual_sha256 = _sha256_text(file_text)
    exact_expected_post_sha256 = checkpoint.get("exact_expected_post_sha256")
    pre_write_sha256 = checkpoint.get("pre_write_sha256")
    exact_available = bool(checkpoint.get("exact_expected_post_available")) and bool(
        exact_expected_post_sha256
    )

    if exact_available and actual_sha256 == exact_expected_post_sha256:
        status = "MATCHED_EXACT_POST"
        reason = (
            "Current file matches the exact post-image derived from the pre-write "
            "checkpoint."
        )
    elif exact_available and pre_write_sha256 and actual_sha256 == pre_write_sha256:
        status = "MATCHED_PRE_IMAGE"
        reason = (
            "Current file still matches the pre-write checkpoint; the intended "
            "write did not land."
        )
    elif exact_available:
        status = "DIVERGED_FROM_EXACT_POST"
        reason = (
            "Current file diverged from the exact post-image derived from the "
            "pre-write checkpoint; stale or intervening write likely."
        )
    else:
        status = "NO_EXACT_POST_IMAGE"
        reason = checkpoint.get("exact_expected_post_reason") or (
            "No exact post-image was available from the pre-write checkpoint."
        )

    return {
        "signature": checkpoint.get("signature"),
        "tool_name": checkpoint.get("tool_name"),
        "file_path": checkpoint.get("file_path"),
        "session_id": checkpoint.get("session_id"),
        "created_at": checkpoint.get("created_at"),
        "consumed_at": checkpoint.get("consumed_at"),
        "source_exists": checkpoint.get("source_exists"),
        "status": status,
        "reason": reason,
        "pre_write_sha256": pre_write_sha256,
        "pre_write_hashlines": checkpoint.get("pre_write_hashlines") or [],
        "exact_expected_post_available": exact_available,
        "exact_expected_post_sha256": exact_expected_post_sha256,
        "exact_expected_post_hashlines": (
            checkpoint.get("exact_expected_post_hashlines") or []
        ),
        "exact_expected_post_reason": checkpoint.get("exact_expected_post_reason"),
        "checkpoint_path": checkpoint.get("_checkpoint_path"),
    }


def verify_tool_edit(
    file_path: str,
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    pre_checkpoint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify that the current file state matches the intent of a write tool call."""
    path = Path(file_path)
    try:
        file_text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "ERROR",
            "reason": f"{type(exc).__name__}: {exc}",
            "tool_name": tool_name,
            "file_path": str(path),
            "checks": [],
            "file_sha256": None,
            "checkpoint": None,
        }

    tool = (tool_name or "").strip().lower()
    if tool in {"edit", "replace"}:
        check = _verify_replace_like(
            file_text,
            old_string=(tool_input.get("old_string", "") or ""),
            new_string=(tool_input.get("new_string", "") or ""),
        )
        status = check["status"]
        reason = check["reason"]
        checks = [check]
    elif tool in {"write", "write_file"}:
        check = _verify_write_like(
            file_text,
            expected_content=(tool_input.get("content", "") or ""),
        )
        status = check["status"]
        reason = check["reason"]
        checks = [check]
    elif tool == "multiedit":
        edits = tool_input.get("edits") or []
        if not isinstance(edits, list):
            return {
                "status": "ERROR",
                "reason": (
                    "MultiEdit payload did not contain a list-valued `edits` " "field."
                ),
                "tool_name": tool_name,
                "file_path": str(path),
                "checks": [],
                "file_sha256": _sha256_text(file_text),
            }
        check = _verify_multiedit(file_text, edits=edits)
        status = check["status"]
        reason = check["reason"]
        checks = [check]
    else:
        return {
            "status": "SKIPPED",
            "reason": f"Unsupported tool for deterministic verification: {tool_name}",
            "tool_name": tool_name,
            "file_path": str(path),
            "checks": [],
            "file_sha256": _sha256_text(file_text),
            "checkpoint": None,
        }

    checkpoint_result = _assess_pre_write_checkpoint(file_text, pre_checkpoint)
    if checkpoint_result and checkpoint_result["status"] == "MATCHED_EXACT_POST":
        status = "VERIFIED"
        reason = checkpoint_result["reason"]
    elif checkpoint_result and checkpoint_result["status"] in {
        "MATCHED_PRE_IMAGE",
        "DIVERGED_FROM_EXACT_POST",
    }:
        status = "MISMATCH"
        reason = checkpoint_result["reason"]

    return {
        "status": status,
        "reason": reason,
        "tool_name": tool_name,
        "file_path": str(path),
        "checks": checks,
        "file_sha256": _sha256_text(file_text),
        "checkpoint": checkpoint_result,
    }


def _append_hashline_block(
    lines: list[str], heading: str, hashlines: list[str]
) -> None:
    """Append a titled fingerprint block when hashline evidence is present."""
    if not hashlines:
        return
    lines.append(heading)
    lines.extend(hashlines)


def _append_match_block(
    lines: list[str],
    heading: str,
    matches: list[dict[str, Any]],
) -> None:
    """Append matched snippet locations together with their hashline evidence."""
    if not matches:
        return
    lines.append(heading)
    for match in matches:
        lines.append(f"- lines {match['span']}")
        lines.extend(match["hashlines"])


def _append_checkpoint_section(lines: list[str], checkpoint: dict[str, Any]) -> None:
    """Render the pre-write checkpoint section of the verification report."""
    if not checkpoint:
        return

    lines.append("")
    lines.append("Pre-write checkpoint:")
    metadata_fields = [
        ("signature", "Signature"),
        ("created_at", "Created"),
        ("consumed_at", "Consumed"),
        ("session_id", "Session"),
    ]
    for key, label in metadata_fields:
        value = checkpoint.get(key)
        if value:
            lines.append(f"{label}: {value}")

    lines.append(f"Assessment: {checkpoint.get('status', 'UNKNOWN')}")
    lines.append(
        f"Reason: {checkpoint.get('reason', 'No checkpoint reason recorded.')}"
    )

    digest_fields = [
        ("pre_write_sha256", "Pre-write SHA256"),
        ("exact_expected_post_sha256", "Exact expected post SHA256"),
    ]
    for key, label in digest_fields:
        value = checkpoint.get(key)
        if value:
            lines.append(f"{label}: {value}")

    exact_post_reason = checkpoint.get("exact_expected_post_reason")
    if exact_post_reason:
        lines.append(f"Exact post-image basis: {exact_post_reason}")

    _append_hashline_block(
        lines,
        "Pre-write fingerprint:",
        checkpoint.get("pre_write_hashlines") or [],
    )
    _append_hashline_block(
        lines,
        "Exact expected post fingerprint:",
        checkpoint.get("exact_expected_post_hashlines") or [],
    )


def _append_check_section(
    lines: list[str],
    idx: int,
    check: dict[str, Any],
) -> None:
    """Render one verification sub-check and its evidence blocks."""
    lines.append("")
    lines.append(
        f"Check {idx}: {check.get('kind', 'unknown')} -> "
        f"{check.get('status', 'UNKNOWN')}"
    )
    lines.append(f"Reason: {check.get('reason', 'No reason recorded.')}")

    _append_hashline_block(
        lines,
        "Expected old fingerprint:",
        check.get("expected_old_hashlines") or [],
    )
    _append_hashline_block(
        lines,
        "Expected new fingerprint:",
        check.get("expected_new_hashlines") or [],
    )
    _append_match_block(lines, "Matched new locations:", check.get("matched_new") or [])
    _append_match_block(lines, "Matched old locations:", check.get("matched_old") or [])

    for sub_idx, subcheck in enumerate(check.get("subchecks") or []):
        if sub_idx >= 3:
            break
        lines.append(
            f"Subcheck {sub_idx + 1}: {subcheck.get('status', 'UNKNOWN')} - "
            f"{subcheck.get('reason', 'No reason recorded.')}"
        )

    _append_hashline_block(
        lines,
        "Expected file fingerprint:",
        check.get("expected_hashlines") or [],
    )
    _append_hashline_block(
        lines,
        "Actual file fingerprint:",
        check.get("actual_hashlines") or [],
    )


def render_verification_section(result: dict[str, Any]) -> str:
    """Render a compact human-readable verification report section."""
    lines = [
        "VERIFICATION (Hashline spike):",
        f"Status: {result.get('status', 'UNKNOWN')}",
        f"Reason: {result.get('reason', 'No reason recorded.')}",
    ]
    file_sha = result.get("file_sha256")
    if file_sha:
        lines.append(f"File SHA256: {file_sha}")

    _append_checkpoint_section(lines, result.get("checkpoint") or {})
    for idx, check in enumerate(result.get("checks", []), start=1):
        _append_check_section(lines, idx, check)

    return "\n".join(lines)
