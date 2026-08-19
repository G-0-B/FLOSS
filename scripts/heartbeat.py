"""
Heartbeat-driven idle-time metacoordination scheduler.

This is a thin composer over the scripts that already exist:
  - poll_high_roi_actions.py  — runs strategic polls through the gateway
  - autonomous_synthesis_loop.py — extracts knowledge from markdown corpora
  - watch_intake.py            — filewatch (already supports --loop separately)
  - process_intake_events.py   — consumes the filewatch queue

It does NOT introduce a new producer component. It rotates through existing
work-types on a cadence, respects a single STOP file, and writes a one-page
RESUMPTION.md so the human steward returns to a single readable surface.

Invariants honored:
  - STOP gate first action every tick (no exceptions, no "in-flight" delays)
  - Plane A only: writes to .agent-surface/heartbeat/ and the existing review
    queues; never publishes to canon, never pushes remote, never sends external
  - Universal-flourishing gate per CLAUDE.md north-star test: every tick logs
    which Phase 0 / substrate-enabling rationale justified running each work
    item, refusing to run an item with no answer
  - Substantive-path filter philosophy from hook_post_write.py: spam prevention
    is about WHAT is worth a round, not arbitrary token caps. We do cap rounds
    per tick as a backstop but the primary gate is slate quality.
  - Doc-budget discipline per CLAUDE.md: this script writes to existing surfaces
    (.agent-surface/heartbeat/, .agent-surface/polls/, .agent-surface/events/)
    and does not invent new doc paths.

Usage:
    # One tick (for testing):
    python FLOSS/scripts/heartbeat.py --once

    # Continuous (production):
    python FLOSS/scripts/heartbeat.py --loop --interval-seconds 900

    # Halt:
    touch C:/~shit/.agent-surface/heartbeat/STOP   # or:
    New-Item -Path .agent-surface/heartbeat/STOP -Force   # PowerShell

Exit codes:
    0  clean shutdown (STOP file or --once completed)
    1  configuration error (no .env, no budgets file)
    2  unrecoverable subprocess error (kept running after retry)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
HEARTBEAT_DIR = WORKSPACE_ROOT / ".agent-surface" / "heartbeat"
STOP_FILE = HEARTBEAT_DIR / "STOP"
BUDGETS_FILE = HEARTBEAT_DIR / "budgets.yaml"
TICK_LOG = HEARTBEAT_DIR / "ticks.log"
RESUMPTION_FILE = WORKSPACE_ROOT / ".agent-surface" / "context" / "RESUMPTION.md"
DYNAMIC_SLATE_PATH = HEARTBEAT_DIR / "next_slate.json"
POLL_STATE_FILE = HEARTBEAT_DIR / "poll_state.json"
SYNTHESIS_STAGING_DIR = REPO_ROOT / "docs" / "knowledge_log" / "staging"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import Action, append_action  # noqa: E402

# Default cadence: 10 minutes. The actual constraint is provider RATE limits
# (RPM), not daily token budgets — free tiers across Cerebras+Groq+Mistral
# offer millions of tokens/day that go unused if we sleep too long between
# ticks. 10 min × 144 ticks/day with 12 rounds/tick × 14 voters/round =
# ~24k voter calls/day, still well under per-provider RPM caps (~30 RPM).
DEFAULT_INTERVAL_SECONDS = 10 * 60

# Hard ceiling on rounds dispatched per tick. Backstop for the slate-quality
# primary gate. Doubled from the v0.1 conservative cap of 6 — the diverse-max
# profile uses 14 voters, so rate-limit pressure per round is higher; per-tick
# round cap of 12 lets the heartbeat consume genuine idle inference capacity.
MAX_ROUNDS_PER_TICK = 12

# Hard ceiling on consensus rounds per day across all ticks. This was reduced
# after the 2026-05-19 token-bleed diagnosis: repeated high-diversity polls can
# exhaust Groq daily TPD before human-facing consensus claims run.
#
# Spec: FLOSS/docs/specs/heartbeat-runtime-budget.spec.md
DEFAULT_DAILY_ROUND_CAP = 40
DEFAULT_HEARTBEAT_POLL_ROUND_COST = 5
DEFAULT_HEARTBEAT_CONFIRM_INTERVAL_TICKS = 72
DEFAULT_HEARTBEAT_WIDE_INTERVAL_TICKS = 72
DEFAULT_SYNTHESIS_STAGING_CAP = 25


@dataclass
class WorkItem:
    """One unit of work the heartbeat may invoke this tick."""
    name: str
    script: str               # path under FLOSS/scripts/
    args: list[str]
    flourishing_rationale: str  # required per CLAUDE.md north-star test
    timeout_seconds: int = 300

    def display(self) -> str:
        return f"{self.name}[{self.script}]"


@dataclass
class TickResult:
    started_at: str
    ended_at: str
    skipped: list[str] = field(default_factory=list)
    completed: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    rounds_dispatched_today: int = 0


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def ensure_dirs() -> None:
    HEARTBEAT_DIR.mkdir(parents=True, exist_ok=True)
    RESUMPTION_FILE.parent.mkdir(parents=True, exist_ok=True)


def log_tick_line(msg: str) -> None:
    """Append-only tick log. Best-effort; never raises."""
    try:
        ensure_dirs()
        with TICK_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{utc_iso()} {msg.rstrip()}\n")
    except Exception:
        pass


def emit_work_item_action(item: WorkItem, result: dict[str, Any]) -> None:
    """Tee one heartbeat work item result into the global Action log."""
    success = result.get("returncode") == 0
    error = result.get("error") if not success else None
    append_action(Action(
        action_id=f"heartbeat-{item.name}-{result.get('started_at', utc_iso())}",
        kind="heartbeat_work_item",
        harness="heartbeat.py",
        started_at=str(result.get("started_at", utc_iso())),
        ended_at=str(result.get("ended_at", utc_iso())),
        duration_seconds=float(result.get("duration_seconds", 0.0) or 0.0),
        success=success,
        inputs={
            "item": item.name,
            "script": item.script,
            "args": item.args,
            "rationale": item.flourishing_rationale,
            "timeout_seconds": item.timeout_seconds,
        },
        outputs={
            "returncode": result.get("returncode"),
            "stdout_tail": result.get("stdout_tail", ""),
            "stderr_tail": result.get("stderr_tail", ""),
        },
        error=error,
    ))


def stop_requested() -> bool:
    """Constraint C7 — single STOP file, checked as the literal first action."""
    return STOP_FILE.exists()


def load_daily_state() -> dict[str, Any]:
    """Track rounds-dispatched-today across heartbeat invocations."""
    state_file = HEARTBEAT_DIR / "daily_state.json"
    today = utc_date()
    if state_file.exists():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
            if data.get("date") == today:
                return data
        except Exception:
            pass
    return {"date": today, "rounds_today": 0, "ticks_today": 0}


def save_daily_state(state: dict[str, Any]) -> None:
    state_file = HEARTBEAT_DIR / "daily_state.json"
    try:
        state_file.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        log_tick_line(f"[error] daily_state save failed: {exc}")


def load_poll_state() -> dict[str, Any]:
    """Read high-ROI poll budget state. Missing/corrupt state is cold-start."""
    try:
        if POLL_STATE_FILE.exists():
            data = json.loads(POLL_STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_poll_state(state: dict[str, Any]) -> None:
    """Persist the last polled slate signature for no-change skip gating."""
    try:
        POLL_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        POLL_STATE_FILE.write_text(
            json.dumps(state, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception as exc:
        log_tick_line(f"[error] poll_state save failed: {exc}")


def compute_poll_slate_signature() -> str:
    """Return a stable signature for the slate that a high-ROI poll would use.

    The signature is intentionally based on `poll_compatible`, not timestamps,
    so regenerating the same slate does not trigger another voter round.
    """
    basis: Any = {"source": "static-baseline"}
    try:
        if DYNAMIC_SLATE_PATH.exists():
            payload = json.loads(DYNAMIC_SLATE_PATH.read_text(encoding="utf-8"))
            candidates = payload.get("poll_compatible")
            if isinstance(candidates, list) and candidates:
                basis = {"source": "dynamic", "poll_compatible": candidates}
    except (OSError, json.JSONDecodeError):
        basis = {"source": "unreadable-dynamic-fallback"}
    encoded = json.dumps(basis, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def env_flag(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def poll_profile_from_item(item: WorkItem) -> str:
    try:
        idx = item.args.index("--profile")
        return item.args[idx + 1]
    except (ValueError, IndexError):
        return "unknown"


def should_schedule_high_roi_poll(
    daily_state: dict[str, Any],
    *,
    profile: str,
    rounds_remaining: int,
) -> tuple[bool, str]:
    """Apply the heartbeat-runtime-budget spec before spending voter calls."""
    if env_flag("FLOSS_HEARTBEAT_DISABLE_POLLS"):
        return False, "FLOSS_HEARTBEAT_DISABLE_POLLS is set"

    expected_cost = int(
        os.environ.get(
            "FLOSS_HEARTBEAT_POLL_ROUND_COST",
            str(DEFAULT_HEARTBEAT_POLL_ROUND_COST),
        )
    )
    if rounds_remaining < expected_cost:
        return False, (
            f"daily round cap leaves {rounds_remaining} rounds, "
            f"expected poll cost is {expected_cost}"
        )

    signature = compute_poll_slate_signature()
    poll_state = load_poll_state()
    last_signature = poll_state.get("last_slate_signature")
    ticks_today = int(daily_state.get("ticks_today", 0))
    last_poll_tick = int(poll_state.get("last_poll_tick", -10**9))
    confirm_interval = int(
        os.environ.get(
            "FLOSS_HEARTBEAT_CONFIRM_INTERVAL_TICKS",
            str(DEFAULT_HEARTBEAT_CONFIRM_INTERVAL_TICKS),
        )
    )
    confirmation_due = (
        confirm_interval > 0
        and last_signature == signature
        and (ticks_today - last_poll_tick) >= confirm_interval
    )
    if last_signature == signature and not confirmation_due:
        return False, (
            "high-ROI slate unchanged since last poll "
            f"(profile would be {profile}); next confirmation in "
            f"{max(0, confirm_interval - (ticks_today - last_poll_tick))} ticks"
        )
    return True, (
        "slate changed"
        if last_signature != signature
        else f"unchanged slate confirmation interval reached for {profile}"
    )


def mark_high_roi_poll_completed(item: WorkItem, daily_state: dict[str, Any]) -> None:
    """Record the slate/profile that just consumed voter calls."""
    save_poll_state(
        {
            "last_slate_signature": compute_poll_slate_signature(),
            "last_poll_tick": int(daily_state.get("ticks_today", 0)),
            "last_poll_profile": poll_profile_from_item(item),
            "last_poll_at": utc_iso(),
        }
    )


def count_synthesis_staging_drafts() -> int:
    """Return how many unreviewed autonomous-synthesis drafts are waiting."""
    try:
        if not SYNTHESIS_STAGING_DIR.exists():
            return 0
        return sum(1 for _ in SYNTHESIS_STAGING_DIR.glob("*_draft.json"))
    except OSError as exc:
        log_tick_line(f"[error] synthesis staging count failed: {exc}")
        # Fail closed: an unreadable queue should not trigger more Groq calls.
        return DEFAULT_SYNTHESIS_STAGING_CAP


def should_schedule_autonomous_synthesis() -> tuple[bool, str]:
    """Gate Groq-backed synthesis by queue depth before adding more drafts."""
    if env_flag("FLOSS_HEARTBEAT_DISABLE_SYNTHESIS"):
        return False, "FLOSS_HEARTBEAT_DISABLE_SYNTHESIS is set"

    staging_cap = int(
        os.environ.get(
            "FLOSS_SYNTHESIS_STAGING_CAP",
            str(DEFAULT_SYNTHESIS_STAGING_CAP),
        )
    )
    staged_drafts = count_synthesis_staging_drafts()
    if staged_drafts >= staging_cap:
        return False, (
            f"synthesis staging queue has {staged_drafts} drafts; "
            f"cap is {staging_cap}"
        )
    return True, f"synthesis staging queue has {staged_drafts}/{staging_cap} drafts"


def get_work_rotation(daily_state: dict[str, Any]) -> list[WorkItem]:
    """
    The work rotation. Order matters: high-value substrate work first.

    Universal-flourishing rationale is REQUIRED per CLAUDE.md north-star test.
    "Substrate-enabling" is an acceptable answer; "I forgot to ask" is not.

    Each WorkItem must:
      - point at a real script that already exists
      - declare its flourishing rationale (not a vibe; what does it enable?)
      - have a finite timeout (no infinite hangs)
    """
    rotation: list[WorkItem] = []

    # 1. PROCESS INTAKE EVENTS — cheapest, no LLM calls, always safe to run.
    # Consumes the filewatch queue produced by watch_intake.py.
    rotation.append(WorkItem(
        name="process_intake",
        script=str(SCRIPTS_DIR / "process_intake_events.py"),
        args=["--limit", "50", "--summary-depth", "100"],
        flourishing_rationale=(
            "Substrate-enabling: keeps the filewatch queue from accumulating "
            "stale events, preserving observability (Light) and provenance "
            "(Knowledge) of what entered the workspace while away."
        ),
        timeout_seconds=120,
    ))

    # 2. DYNAMIC SLATE — regenerate the next_slate.json so the poll picks up
    # whatever is actually accumulating in the workspace right now. Cheap,
    # no LLM calls. Falls back to baseline candidates when there is no fresh
    # filewatch signal.
    rotation.append(WorkItem(
        name="heartbeat_slate",
        script=str(SCRIPTS_DIR / "heartbeat_slate.py"),
        args=["--max-candidates", "8"],
        flourishing_rationale=(
            "Substrate-enabling: ensures consensus rounds reflect current "
            "workspace state, not a fossilized hardcoded slate. CCES L5 "
            "(Collective Intelligence) demands the system attend to what's "
            "actually happening, not what was happening a month ago."
        ),
        timeout_seconds=60,
    ))

    # 3. HIGH-ROI ACTION POLL — uses gateway + voters. Real consensus rounds.
    # Costs free-tier quota. Gate by daily round budget.
    #
    # TOKEN-BUDGET RESTRUCTURE 2026-05-19 (user-flagged Groq daily-TPD bleed):
    # The original config used `diverse-max` (16 voters, 7 on Groq) every tick.
    # That produced ~1200 Groq calls/day and exhausted the Groq daily TPD cap,
    # which is why `groq-gpt-oss-20b` keeps rate-limiting in consensus rounds.
    #
    # Revised policy:
    #   - Default profile: `balanced` (3 voters, 2 on Groq) for routine ticks
    #     (5× reduction in Groq pressure vs diverse-max)
    #   - Wide-profile sweep: every N=72 ticks (~12 hours at 10-min interval),
    #     run a single diverse-max round for cross-frame breadth. Configurable
    #     via FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS.
    #   - Skip the poll entirely if no new intake events / no new claims
    #     since the last poll (state-staleness gate).
    #
    # Env overrides (set in .env or environment):
    #   FLOSS_HEARTBEAT_PROFILE         — default "balanced"; "diverse" or
    #                                     "diverse-max" for hotter routine
    #   FLOSS_HEARTBEAT_WIDE_PROFILE    — default "diverse-max"; what the
    #                                     periodic wide-sweep uses
    #   FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS — default 72 (every ~12 hours);
    #                                     set to 0 to disable periodic sweeps
    #
    # See: ADR-10 vote model, voter_registry.json profiles, this script's
    # daily_state.json for ticks_today / rounds_today bookkeeping.
    rounds_today = int(daily_state.get("rounds_today", 0))
    daily_cap = int(os.environ.get("FLOSS_DAILY_ROUND_CAP", DEFAULT_DAILY_ROUND_CAP))
    rounds_remaining = max(0, daily_cap - rounds_today)
    ticks_today = int(daily_state.get("ticks_today", 0))

    # Periodic wide-profile sweep: switches to diverse-max every Nth tick.
    wide_interval = int(
        os.environ.get(
            "FLOSS_HEARTBEAT_WIDE_INTERVAL_TICKS",
            str(DEFAULT_HEARTBEAT_WIDE_INTERVAL_TICKS),
        )
    )
    routine_profile = os.environ.get("FLOSS_HEARTBEAT_PROFILE", "balanced")
    wide_profile = os.environ.get("FLOSS_HEARTBEAT_WIDE_PROFILE", "diverse-max")
    use_wide_this_tick = wide_interval > 0 and ticks_today > 0 and (ticks_today % wide_interval == 0)
    poll_profile = wide_profile if use_wide_this_tick else routine_profile

    should_poll, poll_reason = should_schedule_high_roi_poll(
        daily_state,
        profile=poll_profile,
        rounds_remaining=rounds_remaining,
    )

    if should_poll:
        rotation.append(WorkItem(
            name=f"poll_high_roi_actions[{poll_profile}]",
            script=str(SCRIPTS_DIR / "poll_high_roi_actions.py"),
            args=["--profile", poll_profile],
            flourishing_rationale=(
                f"Substrate-enabling: surfaces ranked next-actions through "
                f"multi-voter consensus (profile={poll_profile}; "
                f"{'periodic wide-sweep tick' if use_wide_this_tick else 'routine balanced tick'}). "
                f"Budget gate: {poll_reason}. "
                f"Token-budget restructure 2026-05-19 cuts default Groq pressure "
                f"5× vs prior diverse-max-every-tick. Direct path to Phase 0 "
                f"substrate viability AND consumes idle inference capacity "
                f"productively (CCES L5/L7)."
            ),
            timeout_seconds=1200,  # higher-cap voters can be slower
        ))
    else:
        log_tick_line(f"[skip] poll_high_roi_actions — {poll_reason}")

    # 4. AUTONOMOUS SYNTHESIS — extracts insights from research/vision/_reference
    # to staging (NOT to source chain — that requires --commit gated by human).
    # This also uses Groq, so it has its own queue-depth backpressure. If the
    # staging queue is already full, more drafts reduce stewardship quality and
    # burn provider quota without creating immediate value.
    should_synthesize, synthesis_reason = should_schedule_autonomous_synthesis()
    if should_synthesize:
        rotation.append(WorkItem(
            name="autonomous_synthesis",
            script=str(SCRIPTS_DIR / "autonomous_synthesis_loop.py"),
            args=["--model", "groq/llama-3.3-70b-versatile", "--limit", "3"],
            flourishing_rationale=(
                "Substrate-enabling: distills knowledge from the research corpus "
                "into staged drafts (Plane A only) for later human-gated promotion. "
                "Preserves the filter-through-not-out doctrine (Knowledge). Higher-"
                "capability extraction model produces fewer hallucinations and "
                "richer summaries for the same wall-clock budget. "
                f"Budget gate: {synthesis_reason}."
            ),
            timeout_seconds=900,  # 3 files × 5 min budget per file
        ))
    else:
        log_tick_line(f"[skip] autonomous_synthesis — {synthesis_reason}")

    return rotation


def run_work_item(item: WorkItem) -> dict[str, Any]:
    """
    Invoke a work item as a subprocess with timeout.

    Returns a result dict with stdout/stderr/returncode/duration.
    Never raises — wraps all failures into the result dict.
    """
    started = time.perf_counter()
    started_iso = utc_iso()
    log_tick_line(f"[run] {item.display()} rationale=\"{item.flourishing_rationale[:80]}...\"")
    try:
        proc = subprocess.run(
            [sys.executable, item.script, *item.args],
            cwd=str(WORKSPACE_ROOT),
            capture_output=True,
            text=True,
            timeout=item.timeout_seconds,
            check=False,
        )
        duration = time.perf_counter() - started
        result = {
            "item": item.name,
            "script": item.script,
            "args": item.args,
            "rationale": item.flourishing_rationale,
            "started_at": started_iso,
            "ended_at": utc_iso(),
            "duration_seconds": round(duration, 2),
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-2000:] if proc.stderr else "",
        }
        emit_work_item_action(item, result)
        return result
    except subprocess.TimeoutExpired:
        duration = time.perf_counter() - started
        result = {
            "item": item.name,
            "started_at": started_iso,
            "ended_at": utc_iso(),
            "duration_seconds": round(duration, 2),
            "returncode": -1,
            "error": f"timeout after {item.timeout_seconds}s",
        }
        emit_work_item_action(item, result)
        return result
    except Exception as exc:  # noqa: BLE001
        duration = time.perf_counter() - started
        result = {
            "item": item.name,
            "started_at": started_iso,
            "ended_at": utc_iso(),
            "duration_seconds": round(duration, 2),
            "returncode": -2,
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        }
        emit_work_item_action(item, result)
        return result


def estimate_rounds_from_result(item_name: str, result: dict[str, Any]) -> int:
    """
    Estimate how many consensus rounds the work item dispatched.

    For now we approximate per-script:
      - poll_high_roi_actions.py runs exactly 5 rounds (its hardcoded slate)
      - process_intake_events.py runs 0 rounds (no LLM calls)
      - autonomous_synthesis_loop.py runs 1 LLM call per file × --limit
        (but those are not gateway rounds, just one-shot extractions; we
        count them as 0 against the daily round cap since they don't use
        the voter quorum)

    This is intentionally rough. Production should parse the actual output
    summaries. v0.1 prefers a coarse-but-honest estimate over precision.
    """
    if result.get("returncode") != 0:
        return 0
    if item_name.startswith("poll_high_roi_actions"):
        stdout = str(result.get("stdout_tail", ""))
        ranked_count = len(re.findall(r"(?m)^\d+\.\s+", stdout))
        if ranked_count:
            return ranked_count
        return int(
            os.environ.get(
                "FLOSS_HEARTBEAT_POLL_ROUND_COST",
                str(DEFAULT_HEARTBEAT_POLL_ROUND_COST),
            )
        )
    return 0


def write_resumption_page(tick: TickResult, daily_state: dict[str, Any]) -> None:
    """
    Regenerate the single-page resumption surface.

    Per CLAUDE.md doc-budget discipline: writes to the existing
    .agent-surface/context/ path, not a new doc tree.
    """
    daily_cap = int(os.environ.get("FLOSS_DAILY_ROUND_CAP", DEFAULT_DAILY_ROUND_CAP))
    rounds_today = int(daily_state.get("rounds_today", 0))
    ticks_today = int(daily_state.get("ticks_today", 0))

    # Count review-queue depth (where heartbeat outputs land).
    # poll_high_roi_actions writes to .agent-surface/polls/
    polls_dir = WORKSPACE_ROOT / ".agent-surface" / "polls"
    recent_polls = []
    if polls_dir.exists():
        recent_polls = sorted(polls_dir.glob("*-high-roi-actions.md"), reverse=True)[:5]

    # autonomous_synthesis writes to FLOSS/docs/knowledge_log/staging/
    staged_drafts = []
    if SYNTHESIS_STAGING_DIR.exists():
        staged_drafts = sorted(SYNTHESIS_STAGING_DIR.glob("*_draft.json"))

    lines = [
        "# FLOSSI0ULLK Resumption Surface",
        "",
        f"**Last heartbeat tick:** `{tick.ended_at}`",
        f"**Tick status:** {'STOPPED' if stop_requested() else 'ACTIVE'}",
        f"**Today (UTC {daily_state['date']}):** {ticks_today} ticks, "
        f"{rounds_today}/{daily_cap} consensus rounds dispatched",
        "",
        "## This tick",
        "",
    ]

    if tick.skipped:
        lines.append("**Skipped:**")
        for s in tick.skipped:
            lines.append(f"- {s}")
        lines.append("")

    if tick.completed:
        lines.append("**Completed work items:**")
        for c in tick.completed:
            rc = c.get("returncode", "?")
            dur = c.get("duration_seconds", "?")
            status = "✓" if rc == 0 else f"✗ rc={rc}"
            lines.append(f"- {status} `{c.get('item', '?')}` ({dur}s)")
        lines.append("")

    if tick.errors:
        lines.append("**Errors:**")
        for e in tick.errors:
            lines.append(f"- `{e.get('item', '?')}`: {e.get('error', 'unknown')}")
        lines.append("")

    lines.extend([
        "## Review queue",
        "",
        f"**Recent ROI polls** ({len(recent_polls)}):",
    ])
    for p in recent_polls:
        rel = p.relative_to(WORKSPACE_ROOT).as_posix()
        lines.append(f"- `{rel}`")

    lines.extend([
        "",
        f"**Synthesis drafts in staging** ({len(staged_drafts)}):",
    ])
    for d in staged_drafts[:10]:
        rel = d.relative_to(WORKSPACE_ROOT).as_posix()
        lines.append(f"- `{rel}`")
    if len(staged_drafts) > 10:
        lines.append(f"- ... and {len(staged_drafts) - 10} more")

    lines.extend([
        "",
        "## To resume",
        "",
        "1. Read this page. If anything else is required to know system state,"
        " the resumption surface has failed — fix it before iterating.",
        "2. Triage the review queue: accept / revise / reject / archive.",
        "3. For staged synthesis drafts, run "
        "`python FLOSS/scripts/autonomous_synthesis_loop.py --commit --dry-run`"
        " to preview; drop `--dry-run` when ready.",
        "4. To halt the loop: create `.agent-surface/heartbeat/STOP`."
        " To resume: delete it.",
        "",
        "## Constraints honored",
        "",
        "- Plane A only — no canon writes, no remote pushes, no external sends.",
        "- Universal-flourishing gate — every work item declares what it enables.",
        "- STOP file checked as literal first action every tick.",
        "- Daily round cap caps consensus-round spend across all ticks.",
        "- Synthesis backpressure skips Groq-backed extraction when staging is full.",
        "",
        "*Generated by `FLOSS/scripts/heartbeat.py` — Plane A overlay only.*",
    ])

    try:
        ensure_dirs()
        RESUMPTION_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        log_tick_line(f"[error] RESUMPTION.md write failed: {exc}")


def run_one_tick() -> TickResult:
    """Execute a single heartbeat tick. Honors STOP gate as first action."""
    tick = TickResult(started_at=utc_iso(), ended_at="")

    if stop_requested():
        log_tick_line("[stop] STOP file present — tick exiting without work")
        tick.ended_at = utc_iso()
        tick.skipped.append("ALL — STOP file present")
        write_resumption_page(tick, load_daily_state())
        return tick

    daily_state = load_daily_state()
    daily_state["ticks_today"] = int(daily_state.get("ticks_today", 0)) + 1

    rotation = get_work_rotation(daily_state)
    rounds_dispatched_this_tick = 0

    for item in rotation:
        # Re-check STOP between items so a long-running synthesis doesn't
        # block a steward who wants to halt.
        if stop_requested():
            log_tick_line(f"[stop] STOP file appeared mid-tick before {item.name}")
            tick.skipped.append(f"{item.name} — STOP appeared mid-tick")
            break

        # Per-tick rounds backstop.
        if rounds_dispatched_this_tick >= MAX_ROUNDS_PER_TICK:
            tick.skipped.append(
                f"{item.name} — per-tick round cap ({MAX_ROUNDS_PER_TICK}) hit"
            )
            log_tick_line(f"[skip] {item.name} — per-tick round cap hit")
            continue

        result = run_work_item(item)
        rounds_used = estimate_rounds_from_result(item.name, result)
        if result.get("returncode") == 0 and item.name.startswith("poll_high_roi_actions"):
            mark_high_roi_poll_completed(item, daily_state)
        rounds_dispatched_this_tick += rounds_used
        daily_state["rounds_today"] = (
            int(daily_state.get("rounds_today", 0)) + rounds_used
        )

        if result.get("returncode") == 0:
            tick.completed.append(result)
            log_tick_line(
                f"[ok] {item.name} {result['duration_seconds']}s "
                f"rounds=+{rounds_used} "
                f"(today: {daily_state['rounds_today']})"
            )
        else:
            tick.errors.append(result)
            log_tick_line(
                f"[err] {item.name} rc={result.get('returncode')} "
                f"err={result.get('error', '?')[:120]}"
            )

    tick.rounds_dispatched_today = int(daily_state.get("rounds_today", 0))
    tick.ended_at = utc_iso()
    save_daily_state(daily_state)
    write_resumption_page(tick, daily_state)
    return tick


def install_signal_handlers(state: dict[str, bool]) -> None:
    """Best-effort graceful shutdown on SIGINT/SIGTERM."""
    def _handler(signum: int, _frame: Any) -> None:
        state["stop"] = True
        log_tick_line(f"[signal] received {signum} — graceful shutdown requested")

    try:
        signal.signal(signal.SIGINT, _handler)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _handler)
    except (ValueError, OSError):
        # Some platforms / threads can't install signal handlers; non-fatal.
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FLOSSI0ULLK heartbeat scheduler — composes existing scripts."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--once", action="store_true", help="Run one tick and exit.")
    group.add_argument("--loop", action="store_true", help="Run continuously.")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help=f"Seconds between ticks (default: {DEFAULT_INTERVAL_SECONDS}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_dirs()
    log_tick_line(f"[startup] heartbeat scheduler starting "
                  f"mode={'loop' if args.loop else 'once'} "
                  f"interval={args.interval_seconds}s")

    shutdown_state = {"stop": False}
    install_signal_handlers(shutdown_state)

    if args.once:
        tick = run_one_tick()
        print(f"Tick complete: {len(tick.completed)} ok, "
              f"{len(tick.errors)} err, {len(tick.skipped)} skip")
        print(f"Resumption page: {RESUMPTION_FILE}")
        return 0

    # Loop mode.
    while not shutdown_state["stop"]:
        if stop_requested():
            log_tick_line("[stop] STOP file present at loop top — sleeping briefly")
            time.sleep(30)
            continue
        try:
            tick = run_one_tick()
            print(f"[{tick.ended_at}] tick: "
                  f"{len(tick.completed)} ok, "
                  f"{len(tick.errors)} err, "
                  f"{len(tick.skipped)} skip")
        except Exception:  # noqa: BLE001
            log_tick_line(f"[fatal] tick crashed:\n{traceback.format_exc()}")
            # Don't tight-loop on crash; back off.
            time.sleep(60)
            continue

        # Sleep in 5s chunks so STOP file / signals are seen quickly.
        slept = 0
        while slept < args.interval_seconds and not shutdown_state["stop"]:
            if stop_requested():
                log_tick_line("[stop] STOP file detected during sleep — exiting")
                return 0
            time.sleep(min(5, args.interval_seconds - slept))
            slept += 5

    log_tick_line("[shutdown] heartbeat scheduler exiting cleanly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
