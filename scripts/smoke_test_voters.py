"""
Smoke test: run a real Claim through the consensus gate with Cerebras + Groq as voters.

Proves end-to-end that the sovereign inference stack drives the existing
`decide()` pipeline: Claim → LiteLLM voters → Vote (weight + rationale) →
tally → Decision.

Run:
    C:/Python313/python.exe FLOSS/scripts/smoke_test_voters.py

Exits 0 on success, 1 on any failure (import, voter crash, validation error,
unparseable weights, quorum shortfall, etc.).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = REPO_ROOT / ".env"

if not ENV_PATH.exists():
    print(f"FAIL: {ENV_PATH} not found", file=sys.stderr)
    sys.exit(1)

load_dotenv(ENV_PATH)

# Make `packages.*` importable when running the script directly.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.metacoordinator_mcp.voters import build_default_voters  # noqa: E402
from packages.orchestrator.claim_schema import (  # noqa: E402
    BlastRadius,
    Claim,
    ProposalType,
)
from packages.orchestrator.consensus_gate import decide  # noqa: E402


def main() -> int:
    print("=" * 72)
    print("FLOSSIØULLK voter smoke test — real Claim → real voters → real Decision")
    print(f"Keys loaded from: {ENV_PATH}")
    print("=" * 72)

    claim = Claim(
        proposer="smoke-test",
        proposal_type=ProposalType.CODE_CHANGE,
        summary="Add per-voter timeout to LiteLLM voter adapter",
        body=(
            "Wrap the `completion()` call in make_litellm_voter with a 30 s "
            "timeout so a hung provider cannot stall the consensus round. On "
            "timeout, return a neutral 0.0 Vote with '[voter timeout]' as the "
            "rationale, identical to the existing exception path. This is a "
            "local-scope change: voters.py only, no schema or gate changes, "
            "fully backward compatible with the current Voter callable."
        ),
        blast_radius=BlastRadius.LOCAL,
    )

    print(f"\nClaim id:      {claim.id}")
    print(f"Proposer:      {claim.proposer}")
    print(f"Type:          {claim.proposal_type.value}")
    print(f"Blast radius:  {claim.blast_radius.value}")
    print(f"Summary:       {claim.summary}")
    print()

    try:
        voters = build_default_voters()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: build_default_voters() raised {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"Voters built:  {len(voters)}")
    for v in voters:
        print(f"  - {v.__name__}")
    print()

    t0 = time.perf_counter()
    try:
        decision = decide(claim, voters)
    except Exception as exc:  # noqa: BLE001
        dt = time.perf_counter() - t0
        print(
            f"FAIL: decide() raised {type(exc).__name__} after {dt*1000:.0f} ms: {exc}",
            file=sys.stderr,
        )
        return 1
    dt = time.perf_counter() - t0

    print(f"Consensus round complete in {dt*1000:.0f} ms")
    print("-" * 72)
    for vote in decision.votes:
        marker = "ERROR" if vote.rationale.startswith("[voter") else "OK   "
        print(f"[{marker}] {vote.voter:28s}  weight={vote.weight:+.3f}")
        print(f"         rationale: {vote.rationale[:200]}")
    print("-" * 72)
    print(f"Outcome:        {decision.outcome.value}")
    if decision.tally_mean is not None:
        print(f"Tally mean:     {decision.tally_mean:+.4f}")
    if decision.tally_variance is not None:
        print(f"Tally variance: {decision.tally_variance:.4f}")
    print("=" * 72)

    # Success criteria:
    #   - every voter returned a Vote (decide() enforces this via validate())
    #   - at least one voter produced a non-error rationale (proves the
    #     WEIGHT/RATIONALE format parsed correctly from real model output)
    real_votes = [v for v in decision.votes if not v.rationale.startswith("[voter")]
    if not real_votes:
        print("FAIL: every voter returned an error rationale", file=sys.stderr)
        return 1
    if len(real_votes) < len(decision.votes):
        print(
            f"PARTIAL: {len(real_votes)}/{len(decision.votes)} voters returned "
            "parseable output — stack is live but one provider is degraded."
        )
    else:
        print(
            f"PASS: all {len(decision.votes)} voters returned parseable "
            "WEIGHT/RATIONALE output. Sovereign consensus gate is LIVE."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
