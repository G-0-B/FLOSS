"""Run a durable high-ROI action poll through the local consensus gateway.

This script turns a short strategic slate into real Claims, runs consensus
through the gateway using a configured voter profile, records the outcomes on
the local source chain, and writes a reusable poll summary to disk.

Default usage:
    python FLOSS/scripts/poll_high_roi_actions.py

By default this uses the `diverse` profile, which is intended for planning
polls where correlated bias matters more than raw voter count.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
ENV_PATH = REPO_ROOT / ".env"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / ".agent-surface" / "polls"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.metacoordinator_mcp.tools import GatewayTools  # noqa: E402
from packages.metacoordinator_mcp.voters import (  # noqa: E402
    build_default_voters,
    describe_default_roster,
)


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def candidate_claims() -> list[dict[str, Any]]:
    shared_evidence = [
        {"type": "spec", "ref": "docs/architecture/METAHARNESS_OPERATING_MODEL.md"},
        {
            "type": "spec",
            "ref": "docs/superpowers/plans/2026-04-16-forward-momentum-radicle-meta-harnesses.md",
        },
    ]
    return [
        {
            "slug": "provider-diversity-policy",
            "proposal_type": "ConfigChange",
            "summary": "Prioritize provider-diversity policy and heterogeneous planning rosters next",
            "body": (
                "The next highest-ROI actionable item should be hardening the consensus harness "
                "against correlated bias by adopting a provider-diverse strategic poll roster, "
                "documenting the anti-correlation policy, and using that roster for planning and "
                "prioritization rounds before wider automation."
            ),
            "evidence": shared_evidence,
        },
        {
            "slug": "radicle-bridge-spike",
            "proposal_type": "CodeChange",
            "summary": "Prioritize the Radicle bridge proof-of-concept next",
            "body": (
                "The next highest-ROI actionable item should be the Radicle bridge spike: create or "
                "update a real artifact on the Radicle dev-plane, link it into the local source chain, "
                "and verify the linkage from another peer so the collaboration substrate is proven end "
                "to end."
            ),
            "evidence": shared_evidence
            + [
                {"type": "adr", "ref": "docs/adr/ADR-8-radicle-dev-substrate.md"},
            ],
        },
        {
            "slug": "memory-harness-layout",
            "proposal_type": "SpecChange",
            "summary": "Prioritize the filesystem memory harness layout next",
            "body": (
                "The next highest-ROI actionable item should be creating the memory harness filesystem "
                "layout: lightweight index, topic files, task notepads, verification notes, and a "
                "nightly consolidation skeleton so interruption recovery stops burning tokens."
            ),
            "evidence": shared_evidence,
        },
        {
            "slug": "hashline-verification",
            "proposal_type": "CodeChange",
            "summary": "Prioritize deterministic edit verification next",
            "body": (
                "The next highest-ROI actionable item should be a Hashline-style deterministic edit "
                "verification spike so structural edits can be checked for landing on the intended "
                "targets before they are trusted by later automation."
            ),
            "evidence": shared_evidence,
        },
        {
            "slug": "structural-consensus-hook",
            "proposal_type": "CodeChange",
            "summary": "Prioritize a structural-change consensus hook next",
            "body": (
                "The next highest-ROI actionable item should be the structural-change consensus hook: "
                "detect meaningful package-level edits, classify blast radius more explicitly, and "
                "route those edits through policy-aware cheap review before trust is increased."
            ),
            "evidence": shared_evidence,
        },
    ]


def build_markdown_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# High-ROI Action Poll",
        "",
        f"- Poll stamp: `{payload['poll_stamp']}`",
        f"- Profile: `{payload['profile']}`",
        "",
        "## Enabled Roster",
        "",
    ]
    for item in payload["roster"]:
        if item.get("enabled"):
            lines.append(f"- `{item['name']}` -> `{item['model']}`")
    lines.extend(
        [
            "",
            "## Ranked Actions",
            "",
            "| Rank | Candidate | Outcome | Mean | Variance | Claim ID |",
            "|---|---|---:|---:|---:|---|",
        ]
    )
    for idx, result in enumerate(payload["results"], start=1):
        mean = result["decision"].get("tally_mean")
        variance = result["decision"].get("tally_variance")
        mean_str = f"{mean:+.3f}" if isinstance(mean, (int, float)) else "?"
        var_str = f"{variance:.3f}" if isinstance(variance, (int, float)) else "?"
        lines.append(
            f"| {idx} | {result['summary']} | {result['decision']['outcome']} | "
            f"{mean_str} | {var_str} | `{result['claim_id']}` |"
        )

    lines.extend(
        [
            "",
            "## Top Dissents",
            "",
        ]
    )
    for result in payload["results"]:
        negative_votes = [
            vote
            for vote in result["decision"].get("votes", [])
            if vote.get("weight", 0.0) < 0.0
        ]
        if not negative_votes:
            continue
        strongest = min(negative_votes, key=lambda vote: vote.get("weight", 0.0))
        lines.append(f"### `{result['slug']}`")
        lines.append(
            f"- `{strongest['voter']}` `{strongest['weight']:+.3f}`: {strongest['rationale']}"
        )
        lines.append("")

    return "\n".join(lines)


def run_poll(profile: str, output_dir: Path) -> dict[str, Any]:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

    dna_hash = os.environ.get("FLOSS_DNA_HASH", "0" * 64)
    base_dir = Path(os.environ.get("FLOSS_AGENT_DIR", Path.home() / ".floss_agent"))
    gateway = GatewayTools(
        base_dir=base_dir,
        dna_hash=dna_hash,
        voter_factory=lambda: build_default_voters(profile=profile),
    )

    roster = describe_default_roster(profile=profile)
    enabled = [item for item in roster if item["enabled"]]
    if not enabled:
        raise RuntimeError(f"No enabled voters for profile {profile!r}")

    stamp = utc_stamp()
    results: list[dict[str, Any]] = []

    for candidate in candidate_claims():
        claim_result = json.loads(
            gateway.submit_claim(
                proposer="roi-poll",
                proposal_type=candidate["proposal_type"],
                summary=candidate["summary"],
                body=candidate["body"],
                blast_radius="Local",
                evidence=candidate["evidence"],
            )
        )
        if "error" in claim_result:
            raise RuntimeError(
                f"submit_claim failed for {candidate['slug']}: {claim_result['error']}"
            )
        claim_id = claim_result["claim_id"]
        decision = json.loads(gateway.run_consensus_round(claim_id))
        if "error" in decision:
            raise RuntimeError(
                f"run_consensus_round failed for {candidate['slug']}: {decision['error']}"
            )
        results.append(
            {
                "slug": candidate["slug"],
                "summary": candidate["summary"],
                "claim_id": claim_id,
                "entry_hash": claim_result["entry_hash"],
                "decision": decision,
            }
        )

    results.sort(
        key=lambda item: (
            float(item["decision"].get("tally_mean", -999.0)),
            -float(item["decision"].get("tally_variance", 999.0)),
        ),
        reverse=True,
    )

    payload = {
        "poll_stamp": stamp,
        "profile": profile,
        "roster": roster,
        "results": results,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stamp}-high-roi-actions.json"
    md_path = output_dir / f"{stamp}-high-roi-actions.md"
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md_path.write_text(build_markdown_summary(payload), encoding="utf-8")
    payload["json_path"] = str(json_path)
    payload["markdown_path"] = str(md_path)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a durable high-ROI action poll")
    parser.add_argument(
        "--profile", default="diverse", help="Voter profile to use (default: diverse)"
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run_poll(profile=args.profile, output_dir=args.output_dir.resolve())
    print(f"Poll stamp:   {payload['poll_stamp']}")
    print(f"Profile:      {payload['profile']}")
    print(f"JSON output:  {payload['json_path']}")
    print(f"MD output:    {payload['markdown_path']}")
    print("")
    print("Ranked actions:")
    for idx, result in enumerate(payload["results"], start=1):
        mean = result["decision"].get("tally_mean")
        variance = result["decision"].get("tally_variance")
        mean_str = f"{mean:+.3f}" if isinstance(mean, (int, float)) else "?"
        var_str = f"{variance:.3f}" if isinstance(variance, (int, float)) else "?"
        print(
            f"{idx}. {result['slug']} "
            f"outcome={result['decision']['outcome']} mean={mean_str} var={var_str}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
