"""Run a durable high-ROI action poll through the local consensus gateway.

This script turns a short strategic slate into real Claims, runs consensus
through the gateway using a configured voter profile, records the outcomes on
the local source chain, and writes a reusable poll summary to disk.

Default usage:
    python FLOSS/scripts/poll_high_roi_actions.py

By default this uses the `balanced` profile. Use `--profile diverse` or
`--profile diverse-max` only when the extra provider breadth is worth the
token budget.
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
DYNAMIC_SLATE_PATH = WORKSPACE_ROOT / ".agent-surface" / "heartbeat" / "next_slate.json"
DYNAMIC_SLATE_MAX_AGE_SECONDS = 3600  # accept slate up to 1 hour old

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.metacoordinator_mcp.tools import GatewayTools  # noqa: E402
from packages.metacoordinator_mcp.voters import (  # noqa: E402
    build_default_voters,
    describe_default_roster,
)
from packages.activity_log import Action, append_action  # noqa: E402


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _workspace_rel(path_value: object) -> str:
    path = Path(str(path_value))
    try:
        if path.is_absolute():
            return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        pass
    return path.as_posix()


def _duration_since(started_at: str) -> tuple[str, float]:
    ended_at = datetime.now(timezone.utc).isoformat()
    try:
        start_dt = datetime.fromisoformat(started_at)
        end_dt = datetime.fromisoformat(ended_at)
        return ended_at, round((end_dt - start_dt).total_seconds(), 3)
    except (TypeError, ValueError):
        return ended_at, 0.0


def emit_poll_action(payload: dict[str, Any], started_at: str) -> None:
    """Tee a completed high-ROI poll into the global Action log."""
    ended_at, duration = _duration_since(started_at)
    results = payload.get("results", [])
    enabled_roster = [
        item for item in payload.get("roster", [])
        if isinstance(item, dict) and item.get("enabled")
    ]
    json_path = payload.get("json_path")
    markdown_path = payload.get("markdown_path")
    staging_paths = [
        _workspace_rel(path)
        for path in (json_path, markdown_path)
        if path
    ]

    append_action(Action(
        action_id=f"poll-{payload.get('poll_stamp', utc_stamp())}",
        kind="high_roi_poll",
        harness="poll_high_roi_actions.py",
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        success=True,
        inputs={
            "profile": payload.get("profile"),
            "poll_stamp": payload.get("poll_stamp"),
            "roster_enabled": [
                {"name": item.get("name"), "model": item.get("model")}
                for item in enabled_roster
            ],
        },
        outputs={
            "result_count": len(results),
            "top_slug": results[0].get("slug") if results else None,
            "json_path": _workspace_rel(json_path) if json_path else None,
            "markdown_path": _workspace_rel(markdown_path) if markdown_path else None,
        },
        llm_calls=[{
            "model": item.get("model"),
            "provider": item.get("provider", item.get("name")),
            "prompt_hash": "",
            "response_hash": "",
            "duration_seconds": 0.0,
            "error": None,
        } for item in enabled_roster],
        staging_paths=staging_paths,
    ))


def _load_dynamic_slate() -> list[dict[str, Any]] | None:
    """Return the heartbeat-generated dynamic slate if fresh, else None.

    Reads `.agent-surface/heartbeat/next_slate.json` produced by
    `heartbeat_slate.py`. Accepts the slate if its file mtime is within
    DYNAMIC_SLATE_MAX_AGE_SECONDS. Falls back to None (and the static
    baseline below) on any read/parse/age failure — fail-safe to the
    hardcoded slate rather than failing the poll.
    """
    if not DYNAMIC_SLATE_PATH.exists():
        return None
    try:
        age_seconds = (
            datetime.now(timezone.utc).timestamp()
            - DYNAMIC_SLATE_PATH.stat().st_mtime
        )
        if age_seconds > DYNAMIC_SLATE_MAX_AGE_SECONDS:
            return None
        payload = json.loads(DYNAMIC_SLATE_PATH.read_text(encoding="utf-8"))
        candidates = payload.get("poll_compatible", [])
        if not isinstance(candidates, list) or not candidates:
            return None
        # Minimal shape check: every candidate must have the keys the poll
        # uses. Anything malformed → discard the whole slate, fall back to
        # static. Don't half-trust a corrupted dynamic source.
        required_keys = {"slug", "proposal_type", "summary", "body", "evidence"}
        for c in candidates:
            if not isinstance(c, dict) or not required_keys.issubset(c.keys()):
                return None
        return candidates
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def candidate_claims() -> list[dict[str, Any]]:
    """Return the slate to poll. Prefers the dynamic slate when present and
    fresh; falls back to the hardcoded strategic baseline below.

    The dynamic slate (produced by heartbeat_slate.py) reflects what is
    actually accumulating in the workspace (filewatch events, staging
    backlog, etc.). The static slate below is the strategic baseline that
    runs when nothing newer has been generated — never deleted, always
    available as a safe fallback.
    """
    dynamic = _load_dynamic_slate()
    if dynamic is not None:
        return dynamic

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
    started_at = datetime.now(timezone.utc).isoformat()

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
    emit_poll_action(payload, started_at)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a durable high-ROI action poll")
    parser.add_argument(
        "--profile", default="balanced", help="Voter profile to use (default: balanced)"
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
