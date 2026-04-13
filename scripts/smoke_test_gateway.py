"""
Smoke test: end-to-end gateway loop.

Drives GatewayTools through the full closed loop:
  1. submit_claim  — append Claim to chain
  2. list_pending  — confirm it shows up
  3. run_consensus_round  — real voters vote, Decision lands on chain
  4. get_decision  — read it back
  5. list_pending  — confirm it's no longer pending
  6. run_consensus_round again  — confirm E_ALREADY_DECIDED idempotency

Uses a fresh temp directory so it's hermetic and can run repeatedly without
polluting the real ~/.floss_agent cell.

Run:
    C:/Python313/python.exe FLOSS/scripts/smoke_test_gateway.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

if not ENV_PATH.exists():
    print(f"FAIL: {ENV_PATH} not found", file=sys.stderr)
    sys.exit(1)
load_dotenv(ENV_PATH)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.metacoordinator_mcp.tools import GatewayTools  # noqa: E402

DNA_HASH = "a" * 64


def line(ch: str = "=", n: int = 72) -> None:
    print(ch * n)


def pretty(label: str, payload: str) -> None:
    try:
        data = json.loads(payload)
        print(f"{label}:")
        print(json.dumps(data, indent=2)[:1200])
    except json.JSONDecodeError:
        print(f"{label}: {payload!r}")


def main() -> int:
    line()
    print("FLOSSIØULLK gateway end-to-end smoke test")
    print(f"Keys loaded from: {ENV_PATH}")
    line()

    with tempfile.TemporaryDirectory() as tmp:
        print(f"Cell base dir:   {tmp}")
        print(f"DNA hash:        {DNA_HASH}")
        gw = GatewayTools(base_dir=Path(tmp), dna_hash=DNA_HASH)

        # --- 1. submit_claim ------------------------------------------------
        line("-")
        print("STEP 1: submit_claim")
        submit_payload = gw.submit_claim(
            proposer="smoke-test",
            proposal_type="CodeChange",
            summary="Add per-voter timeout to LiteLLM voter adapter",
            body=(
                "Wrap completion() in make_litellm_voter with a 30 s timeout "
                "so a hung provider cannot stall the consensus round. Fall "
                "back to neutral 0.0 Vote with '[voter timeout]' rationale."
            ),
            blast_radius="Local",
        )
        pretty("submit_claim result", submit_payload)
        submit = json.loads(submit_payload)
        if "error" in submit:
            print(f"FAIL: submit_claim errored: {submit['error']}", file=sys.stderr)
            return 1
        claim_id = submit["claim_id"]
        print(f"\nclaim_id = {claim_id}")

        # --- 2. list_pending (should contain our claim) ---------------------
        line("-")
        print("STEP 2: list_pending (expect 1 pending)")
        pending = json.loads(gw.list_pending())
        print(f"pending count: {len(pending)}")
        if not any(p["claim_id"] == claim_id for p in pending):
            print("FAIL: submitted claim not visible in list_pending", file=sys.stderr)
            return 1
        print("  → submitted claim visible in pending list")

        # --- 3. run_consensus_round -----------------------------------------
        line("-")
        print("STEP 3: run_consensus_round (real voters — this calls Cerebras + Groq)")
        t0 = time.perf_counter()
        decision_payload = gw.run_consensus_round(claim_id)
        dt = time.perf_counter() - t0
        pretty("Decision", decision_payload)
        decision = json.loads(decision_payload)
        if "error" in decision:
            print(
                f"FAIL: run_consensus_round errored after {dt*1000:.0f} ms: {decision['error']}",
                file=sys.stderr,
            )
            return 1
        print(f"\nround latency: {dt*1000:.0f} ms")
        print(f"outcome:       {decision['outcome']}")
        if "tally_mean" in decision:
            print(f"tally mean:    {decision['tally_mean']:+.4f}")
        if "tally_variance" in decision:
            print(f"tally var:     {decision['tally_variance']:.4f}")
        print("per-voter:")
        for v in decision["votes"]:
            marker = "ERROR" if v["rationale"].startswith("[voter") else "OK   "
            print(f"  [{marker}] {v['voter']:28s}  weight={v['weight']:+.3f}")

        # --- 4. get_decision (read it back) ---------------------------------
        line("-")
        print("STEP 4: get_decision (read it back from the chain)")
        reread = json.loads(gw.get_decision(claim_id))
        if reread is None:
            print("FAIL: get_decision returned null for a just-decided claim", file=sys.stderr)
            return 1
        if reread["claim_id"] != claim_id or reread["outcome"] != decision["outcome"]:
            print("FAIL: re-read decision does not match written decision", file=sys.stderr)
            return 1
        print("  → round-trips cleanly (claim_id + outcome match)")

        # --- 5. list_pending (should NOT contain our claim anymore) ---------
        line("-")
        print("STEP 5: list_pending (expect our claim to be gone)")
        pending2 = json.loads(gw.list_pending())
        if any(p["claim_id"] == claim_id for p in pending2):
            print("FAIL: decided claim still in pending list", file=sys.stderr)
            return 1
        print(f"  → claim no longer pending (remaining pending: {len(pending2)})")

        # --- 6. idempotency: second run_consensus_round should refuse -------
        line("-")
        print("STEP 6: run_consensus_round AGAIN (expect E_ALREADY_DECIDED)")
        second = json.loads(gw.run_consensus_round(claim_id))
        if "error" not in second or "ALREADY_DECIDED" not in second["error"]:
            print(
                f"FAIL: second round should return E_ALREADY_DECIDED, got {second!r}",
                file=sys.stderr,
            )
            return 1
        print(f"  → {second['error']}")

    line()
    print("PASS: full submit → vote → decide → read → idempotency loop is LIVE.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
