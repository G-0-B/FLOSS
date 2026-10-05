"""Symbolic evidence-ref resolution. A lookup result, not a verdict: no claim is verified here."""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path
from typing import Any

from packages.coordination_room.paths import PathEscape, normalize_path

MAX_REFS = 16
REF_MAX = 512
COMMIT_TIMEOUT_SECONDS = 2.0
# One post's lookups share this budget. Refs not reached in time are recorded
# as unresolved rather than making the caller wait.
LOOKUP_BUDGET_SECONDS = 5.0
_SHA = re.compile(r"[0-9a-f]{7,40}")
_OID = re.compile(r"[0-9a-f]{40,64}")


def _file_row(root: Path, ref: str) -> dict[str, Any]:
    """`ok` if a regular file under root. No digest: the log is shared, and a
    hash of an untracked file (a `.env`, say) would publish a fingerprint of
    it. Cite a commit when the evidence must be immutable."""
    row: dict[str, Any] = {"ref": ref, "kind": "file", "ok": False}
    try:
        row["ok"] = (root / normalize_path(root, ref[5:])).is_file()
    except (PathEscape, OSError):
        row["ok"] = False
    return row


def _commit_row(root: Path, ref: str, timeout: float) -> dict[str, Any]:
    """`ok` if the sha names exactly one commit; `oid` is its full object id."""
    row: dict[str, Any] = {"ref": ref, "kind": "commit", "ok": False}
    sha = ref[7:].lower()
    if not _SHA.fullmatch(sha) or timeout <= 0:
        return row
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return row
    oid = done.stdout.strip()
    if done.returncode == 0 and _OID.fullmatch(oid):
        row["ok"] = True
        row["oid"] = oid
    return row


def resolve_ref(root: Path, ref: str, timeout: float = COMMIT_TIMEOUT_SECONDS) -> dict[str, Any]:
    """`file:<path>` and `commit:<sha>` resolve; anything else is `unknown`."""
    if ref.startswith("file:"):
        return _file_row(root, ref)
    if ref.startswith("commit:"):
        return _commit_row(root, ref, timeout)
    return {"ref": ref, "kind": "unknown", "ok": False}


def resolve_all(
    root: Path, refs: list[str] | None
) -> tuple[str, list[dict[str, Any]]]:
    """Return (status, checked). status is none | resolved | unresolved."""
    if refs is None:
        return "none", []
    if not isinstance(refs, list) or not all(
        isinstance(r, str) and r.strip() for r in refs
    ):
        raise ValueError("evidence_refs must be a list of non-empty strings")
    if not refs:
        return "none", []
    if len(refs) > MAX_REFS:
        raise ValueError(f"evidence_refs exceeds {MAX_REFS} entries")
    if any(len(r.strip()) > REF_MAX for r in refs):
        raise ValueError(f"evidence ref exceeds {REF_MAX} characters")
    deadline = time.monotonic() + LOOKUP_BUDGET_SECONDS
    checked = [
        resolve_ref(
            root, r.strip(), min(COMMIT_TIMEOUT_SECONDS, deadline - time.monotonic())
        )
        for r in refs
    ]
    status = "resolved" if all(c["ok"] for c in checked) else "unresolved"
    return status, checked
