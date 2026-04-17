"""
FastMCP server for the FLOSSIØULLK consensus gateway.

Exposes the 5 tools from spec §5.2 via the MCP protocol. The server is a
router/switch — it routes Claims to voters and appends results to the
file-based source chain. It does NOT decide outcomes or command voters.

Usage:
    python -m packages.metacoordinator_mcp.server

Environment variables:
    FLOSS_AGENT_DIR   Base directory for cell storage (default: ~/.floss_agent)
    FLOSS_DNA_HASH    64-char hex dna_hash for the active cell (default: zeros)
    FLOSS_VOTER_PROFILE  Built-in roster profile (`balanced` default; `fast`,
                         `flowith`, `subscriptions`, and `amplified` optional)
    FLOSS_VOTER_ROSTER   Full `name=model` roster override
    FLOSS_EXTRA_VOTERS   Extra `name=model` voters appended to the built-in profile
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise ImportError("MCP SDK not installed. Run: pip install mcp") from exc

from .tools import GatewayTools

BASE_DIR = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
DNA_HASH = os.environ.get("FLOSS_DNA_HASH", "0" * 64)

_gateway = GatewayTools(base_dir=BASE_DIR, dna_hash=DNA_HASH)

mcp = FastMCP("FLOSSIØULLK Consensus Gateway")


@mcp.tool()
def submit_claim(
    proposer: str,
    proposal_type: str,
    summary: str,
    body: str,
    blast_radius: str,
) -> str:
    """Submit a proposed change to the consensus gate.

    proposal_type: CodeChange | ConfigChange | SpecChange | AdrChange | Other
    blast_radius: Local | Module | System | Substrate
    Returns JSON with entry_hash and claim_id, or {"error": "..."} on failure.
    """
    return _gateway.submit_claim(proposer, proposal_type, summary, body, blast_radius)


@mcp.tool()
def cast_vote(claim_id: str, voter: str, weight: float, rationale: str) -> str:
    """Cast an analog vote on a pending Claim.

    weight: float in [-0.999, 0.999]. Positive = support, negative = oppose.
    Returns JSON with entry_hash, or {"error": "..."} on failure.
    """
    return _gateway.cast_vote(claim_id, voter, weight, rationale)


@mcp.tool()
def get_chain_context(limit: int = 20) -> str:
    """Return the most recent source chain entries for voter context.

    Returns JSON list, newest first. Use limit to stay within token budgets.
    """
    return _gateway.get_chain_context(limit)


@mcp.tool()
def get_decision(claim_id: str) -> str:
    """Return the Decision for a given claim_id, or null if not yet decided."""
    return _gateway.get_decision(claim_id)


@mcp.tool()
def list_pending() -> str:
    """List all Claims that have not yet received a Decision."""
    return _gateway.list_pending()


@mcp.tool()
def run_consensus_round(claim_id: str) -> str:
    """Run the active voter roster against a pending Claim and append the Decision.

    Resolves voters from the env-aware profile system in `voters.py`, calls every
    voter on the claim, appends each Vote to the chain, then appends the
    resulting Decision. Idempotent: a claim that already has a Decision returns
    {"error": "E_ALREADY_DECIDED"}.

    Returns JSON with the full Decision (outcome, votes, tally_mean,
    tally_variance), or {"error": "..."} on lookup / voter / tally failure.
    """
    return _gateway.run_consensus_round(claim_id)


if __name__ == "__main__":
    mcp.run()
