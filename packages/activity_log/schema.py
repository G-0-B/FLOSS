"""Activity-log schema + append helper.

Single canonical write target: `.agent-surface/activity.jsonl`
One JSON object per line. Append-only. Plane A.

Per `2026-05-18-metaharness-unification.md` §3.1 / §3.2 / §7. v0.1-experimental
schema; the `schema_version` field lets us iterate without retroactively
rewriting prior log lines.

Backpressure handling per the unification doc §7 question 3: best-effort write
with a short timeout, log to stderr on failure, never raise. Activity log is
observability, not correctness.
"""

from __future__ import annotations

import json
import os
import sys
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

SCHEMA_VERSION = "0.1-experimental"

# Lazy import-time path resolution. Allows override via env var for tests.
_WORKSPACE_ROOT_OVERRIDE = os.environ.get("FLOSS_WORKSPACE_ROOT")
if _WORKSPACE_ROOT_OVERRIDE:
    WORKSPACE_ROOT = Path(_WORKSPACE_ROOT_OVERRIDE).resolve()
else:
    # __file__ → activity_log/schema.py → activity_log/ → packages/ → FLOSS/ → workspace
    WORKSPACE_ROOT = Path(__file__).resolve().parents[3]

ACTIVITY_LOG = WORKSPACE_ROOT / ".agent-surface" / "activity.jsonl"


@dataclass
class Action:
    """One agentic action across any harness."""

    action_id: str  # e.g., "harvest-0042", "synth-doc-XYZ.md", "router-decision-<hash>"
    kind: (
        str  # harvest | synthesis | poll | filewatch | router_decision | ensemble | ...
    )
    harness: str  # Which script/module emitted this (e.g., "harvest_reuse_ledger.py")
    started_at: str  # UTC ISO
    ended_at: str
    duration_seconds: float
    success: bool
    inputs: dict  # Triggering inputs (truncated where verbose)
    outputs: dict  # Paths produced, decision values, claim_id, etc.
    llm_calls: list[dict] = field(default_factory=list)
    # Per LLM call: {"model": str, "provider": str, "prompt_hash": str,
    #                "response_hash": str, "duration_seconds": float,
    #                "tokens_in": int, "tokens_out": int, "error": str|None}
    routing_decision: Optional[dict] = None
    # If Router was invoked: {"mode": str, "reason": str, "confidence": float}
    provenance_path: Optional[str] = None  # Sidecar JSON path if any
    provenance_packet_id: Optional[str] = None  # KERI-shaped packet digest (`d`)
    provenance_hash: Optional[str] = None  # SHA-256 of packet sidecar bytes
    staging_paths: list[str] = field(default_factory=list)
    error: Optional[str] = None
    schema_version: str = SCHEMA_VERSION


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def prompt_hash(text: str) -> str:
    """16-char SHA-256 prefix — stable identifier for prompts/responses."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def append_action(action: Action) -> bool:
    """Append one Action to the global activity log.

    Best-effort. Returns True on success, False on any failure (with stderr log).
    Never raises — activity log failure must not block the calling harness.
    """
    try:
        ACTIVITY_LOG.parent.mkdir(parents=True, exist_ok=True)
        record = asdict(action)
        with ACTIVITY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return True
    except OSError as e:
        print(
            f"[activity_log] WARN: failed to append {action.action_id}: {e}",
            file=sys.stderr,
        )
        return False
    except Exception as e:  # noqa: BLE001
        print(
            f"[activity_log] WARN: unexpected error appending {action.action_id}: "
            f"{type(e).__name__}: {e}",
            file=sys.stderr,
        )
        return False


def tail_actions(n: int = 50, kind_filter: Optional[str] = None) -> list[dict]:
    """Read the last N actions from the global log. Optional filter by kind."""
    if not ACTIVITY_LOG.exists():
        return []
    try:
        lines = ACTIVITY_LOG.read_text(encoding="utf-8").strip().splitlines()
    except OSError:
        return []
    out: list[dict] = []
    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if kind_filter and rec.get("kind") != kind_filter:
            continue
        out.append(rec)
        if len(out) >= n:
            break
    return list(reversed(out))


def quick_action(
    kind: str,
    harness: str,
    inputs: dict,
    outputs: dict,
    success: bool,
    started_at: str,
    action_id: Optional[str] = None,
    **extras: Any,
) -> Action:
    """Convenience constructor for the common case.

    Computes duration_seconds = now - started_at. action_id auto-generated
    from kind + hash(inputs) if not provided.
    """
    end = utc_iso()
    try:
        start_dt = datetime.fromisoformat(started_at)
        end_dt = datetime.fromisoformat(end)
        duration = (end_dt - start_dt).total_seconds()
    except (ValueError, TypeError):
        duration = 0.0

    if action_id is None:
        action_id = (
            f"{kind}-{prompt_hash(json.dumps(inputs, sort_keys=True, default=str))}"
        )

    return Action(
        action_id=action_id,
        kind=kind,
        harness=harness,
        started_at=started_at,
        ended_at=end,
        duration_seconds=round(duration, 3),
        success=success,
        inputs=inputs,
        outputs=outputs,
        **extras,
    )
