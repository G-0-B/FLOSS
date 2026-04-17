"""
Background consensus-round runner for the Claude Code PostToolUse hook.

Spawned DETACHED by `hook_post_write.py` after it submits a Claim. Runs the
full `run_consensus_round` against the local gateway (which calls Cerebras +
Groq voters via LiteLLM) and logs the outcome. Never produces stdout/stderr
because the parent hook has already exited and nobody is reading — everything
goes to FLOSS_AGENT_DIR/hook.log.

Invocation:
    python hook_bg_round.py <claim_id>

Exits 0 on success, 1 on any failure (makes no difference to the caller —
the hook that spawned this process has already returned).
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
LOG_FILE = AGENT_DIR / "hook.log"
TRACE_DIR = AGENT_DIR / "traces" / "consensus"


def log(msg: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")
    except Exception:
        pass


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_trace(claim_id: str, payload: dict) -> None:
    try:
        TRACE_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        path = TRACE_DIR / f"{stamp}-{claim_id}.json"
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass


def main() -> int:
    started_at = utcnow_iso()
    if len(sys.argv) < 2:
        log("[bg] no claim_id argument")
        return 1
    claim_id = sys.argv[1]
    profile = os.environ.get("FLOSS_VOTER_PROFILE", "balanced").strip() or "balanced"
    roster: list[dict] = []

    # Load .env so CEREBRAS_API_KEY / GROQ_API_KEY reach litellm. The hook
    # runs in a detached process group — it does NOT inherit Claude Code's
    # env, so we have to rehydrate from the repo's .env file ourselves.
    try:
        from dotenv import load_dotenv

        env_path = REPO_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except Exception:  # noqa: BLE001
        log(f"[bg] dotenv load failed (continuing):\n{traceback.format_exc()}")

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    try:
        from packages.metacoordinator_mcp.tools import GatewayTools
    except Exception:  # noqa: BLE001
        log(
            f"[bg] GatewayTools import failed for {claim_id}:\n{traceback.format_exc()}"
        )
        write_trace(
            claim_id,
            {
                "claim_id": claim_id,
                "started_at": started_at,
                "finished_at": utcnow_iso(),
                "profile": profile,
                "roster": roster,
                "error": "GatewayTools import failed",
            },
        )
        return 1

    try:
        from packages.metacoordinator_mcp.voters import describe_default_roster

        roster = describe_default_roster(profile=profile)
        enabled = [
            f"{item['name']}={item['model']}" for item in roster if item["enabled"]
        ]
        disabled = [
            f"{item['name']} ({item['reason']})"
            for item in roster
            if not item["enabled"]
        ]
        if enabled:
            log(f"[bg] {claim_id} roster[{profile}] enabled: " + " | ".join(enabled))
        if disabled:
            log(f"[bg] {claim_id} roster[{profile}] disabled: " + " | ".join(disabled))
    except Exception:  # noqa: BLE001
        log(
            f"[bg] roster introspection failed for {claim_id}:\n{traceback.format_exc()}"
        )

    try:
        dna_hash = os.environ.get("FLOSS_DNA_HASH", "0" * 64)
        gw = GatewayTools(base_dir=AGENT_DIR, dna_hash=dna_hash)
    except Exception:  # noqa: BLE001
        log(f"[bg] GatewayTools init failed for {claim_id}:\n{traceback.format_exc()}")
        write_trace(
            claim_id,
            {
                "claim_id": claim_id,
                "started_at": started_at,
                "finished_at": utcnow_iso(),
                "profile": profile,
                "roster": roster,
                "error": "GatewayTools init failed",
            },
        )
        return 1

    t0 = time.perf_counter()
    try:
        result_str = gw.run_consensus_round(claim_id)
        result = json.loads(result_str)
    except Exception:  # noqa: BLE001
        log(
            f"[bg] run_consensus_round crashed for {claim_id}:\n{traceback.format_exc()}"
        )
        write_trace(
            claim_id,
            {
                "claim_id": claim_id,
                "started_at": started_at,
                "finished_at": utcnow_iso(),
                "profile": profile,
                "roster": roster,
                "error": "run_consensus_round crashed",
            },
        )
        return 1
    dt = time.perf_counter() - t0
    trace_payload = {
        "claim_id": claim_id,
        "started_at": started_at,
        "finished_at": utcnow_iso(),
        "duration_ms": round(dt * 1000, 3),
        "profile": profile,
        "roster": roster,
        "result": result,
    }

    if "error" in result:
        log(f"[bg] {claim_id} ERROR after {dt*1000:.0f}ms: {result['error']}")
        write_trace(claim_id, trace_payload)
        return 1

    outcome = result.get("outcome", "?")
    mean = result.get("tally_mean")
    var = result.get("tally_variance")
    per_voter = " | ".join(
        f"{v['voter']}={v['weight']:+.2f}" for v in result.get("votes", [])
    )
    mean_str = f"{mean:+.3f}" if isinstance(mean, (int, float)) else "?"
    var_str = f"{var:.3f}" if isinstance(var, (int, float)) else "?"
    log(
        f"[bg] {claim_id} {outcome} mean={mean_str} var={var_str} "
        f"({dt*1000:.0f}ms) — {per_voter}"
    )
    write_trace(claim_id, trace_payload)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        log(f"[bg] top-level crash:\n{traceback.format_exc()}")
        sys.exit(1)
