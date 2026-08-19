"""
Dynamic-slate generator for high-ROI action polling.

The existing `poll_high_roi_actions.py` carries a hardcoded 5-candidate slate.
That is useful as a stable baseline poll but unsuitable for a heartbeat loop
that wants to surface what's actually accumulating in the workspace right now.

This module produces candidate Claims from real backlog sources:
  - .agent-surface/events/processed/   (recent filewatch events)
  - ~/.floss_agent/traces/consensus/   (recent voter traces — dissent surfaces)
  - FLOSS/docs/knowledge_log/staging/  (synthesis drafts awaiting human review)
  - FLOSS/docs/research/ recent drops  (intake that hasn't been distilled)

Each candidate Claim respects the same shape `poll_high_roi_actions` expects:
    {
      "slug": str,                  # short identifier
      "proposal_type": str,         # one of CodeChange / SpecChange / ConfigChange / ResearchAction
      "summary": str,               # ≤120 chars headline
      "body": str,                  # full text the voters evaluate
      "evidence": list[dict],       # {"type": ..., "ref": ...} entries
      "flourishing_rationale": str, # required per CLAUDE.md north-star test
    }

The `flourishing_rationale` field is new — not in the original poll script's
schema. It exists so the heartbeat loop can refuse candidates that can't
answer "what does this enable?". `poll_high_roi_actions.py` will need a small
patch to accept and ignore it, or this module's `to_poll_candidate()` helper
strips it before submission.

Usage (standalone):
    python FLOSS/scripts/heartbeat_slate.py
        --max-candidates 5
        --output .agent-surface/heartbeat/next_slate.json

Usage (importable):
    from heartbeat_slate import build_dynamic_slate
    candidates = build_dynamic_slate(max_candidates=5)
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = REPO_ROOT.parent
EVENTS_PROCESSED = WORKSPACE_ROOT / ".agent-surface" / "events" / "processed"
TRACES_DIR = Path(os.environ.get(
    "FLOSS_AGENT_DIR", Path.home() / ".floss_agent"
)) / "traces" / "consensus"
STAGING_DIR = REPO_ROOT / "docs" / "knowledge_log" / "staging"
RESEARCH_DIR = REPO_ROOT / "docs" / "research"
RECENT_HOURS = 48
SHARED_EVIDENCE = [
    {"type": "spec", "ref": "docs/architecture/METAHARNESS_OPERATING_MODEL.md"},
    {"type": "spec", "ref": "CLAUDE.md (north-star load-bearing test)"},
]


@dataclass
class Candidate:
    slug: str
    proposal_type: str
    summary: str
    body: str
    evidence: list[dict[str, str]]
    flourishing_rationale: str

    def to_poll_candidate(self) -> dict[str, Any]:
        """Strip the flourishing_rationale so poll_high_roi_actions accepts it.

        The rationale is required for HEARTBEAT acceptance; the poll script
        doesn't need to know about it. We keep it on the Candidate so the
        slate generator can refuse rationale-less candidates upstream.
        """
        return {
            "slug": self.slug,
            "proposal_type": self.proposal_type,
            "summary": self.summary,
            "body": self.body,
            "evidence": list(self.evidence),
        }


def utc_now_minus_hours(hours: int) -> datetime:
    return datetime.now(timezone.utc).timestamp() - (hours * 3600)


def recent_files(directory: Path, pattern: str, hours: int) -> list[Path]:
    """Return files modified within the last `hours`, newest first."""
    if not directory.exists():
        return []
    cutoff = utc_now_minus_hours(hours)
    out = []
    for path in directory.rglob(pattern):
        try:
            if path.stat().st_mtime >= cutoff:
                out.append(path)
        except OSError:
            continue
    return sorted(out, key=lambda p: p.stat().st_mtime, reverse=True)


# ---------------------------------------------------------------------------
# Source 1: filewatch processed events with recommended_actions
# ---------------------------------------------------------------------------

def candidates_from_processed_events(limit: int = 3) -> list[Candidate]:
    """Synthesize candidates from recent filewatch processed events.

    Looks for `recommended_actions` that flag follow-up work:
      - "consider_canon_promotion" — root intake awaiting digestion
      - "refresh_shared_skills"    — skill manifest changes
      - "review_trace_drift"       — anomalous voter traces
    """
    out: list[Candidate] = []
    seen_actions: set[str] = set()
    files = recent_files(EVENTS_PROCESSED, "*.json", RECENT_HOURS)

    for path in files[:50]:  # bounded look-back
        if len(out) >= limit:
            break
        try:
            evt = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        actions = evt.get("recommended_actions", [])
        rel = evt.get("rel_path") or evt.get("abs_path") or path.name
        for action in actions:
            if action in seen_actions:
                continue
            if action == "consider_canon_promotion":
                seen_actions.add(action)
                out.append(Candidate(
                    slug=f"promote-{Path(rel).stem[:30]}",
                    proposal_type="SpecChange",
                    summary=f"Consider canon promotion: {Path(rel).name}",
                    body=(
                        f"Filewatch flagged {rel} as a root-intake artifact "
                        f"that may merit promotion into FLOSS/docs/. Evaluate "
                        f"the artifact's evidence quality and current canon "
                        f"alignment before promoting. Plane A advisory only — "
                        f"actual promotion requires human steward action."
                    ),
                    evidence=SHARED_EVIDENCE + [{"type": "url", "ref": rel}],
                    flourishing_rationale=(
                        "Substrate-enabling: keeps intake from rotting at the "
                        "workspace root, preserving Provenance (Knowledge)."
                    ),
                ))
            elif action == "review_trace_drift":
                seen_actions.add(action)
                out.append(Candidate(
                    slug="review-trace-drift",
                    proposal_type="Other",
                    summary="Review recent consensus trace drift",
                    body=(
                        "Filewatch flagged anomalous patterns in recent "
                        "voter traces. Review the trace directory for "
                        "unexpected dissent, error rates, or provider failure "
                        "modes that may indicate degraded voter quality."
                    ),
                    evidence=SHARED_EVIDENCE + [
                        {"type": "url", "ref": str(TRACES_DIR)}
                    ],
                    flourishing_rationale=(
                        "Substrate-enabling: degraded voter quality directly "
                        "compromises Coordination (P5). Catching drift early "
                        "preserves resonance-network integrity."
                    ),
                ))
            elif action == "refresh_shared_skills":
                seen_actions.add(action)
                out.append(Candidate(
                    slug="refresh-shared-skills",
                    proposal_type="ConfigChange",
                    summary="Verify shared skill surface still consistent",
                    body=(
                        "A skill-surface manifest change was observed. "
                        "Run materialize_shared_skill_surface.py --check to "
                        "verify no drift between manifest and projected "
                        "agent-native skill copies."
                    ),
                    evidence=SHARED_EVIDENCE + [{"type": "url", "ref": rel}],
                    flourishing_rationale=(
                        "Substrate-enabling: keeps the shared agent surface "
                        "consistent so all participating agents have the same "
                        "operational view (Light)."
                    ),
                ))
    return out


# ---------------------------------------------------------------------------
# Source 2: synthesis drafts in staging — propose commit reviews
# ---------------------------------------------------------------------------

def candidates_from_staged_drafts(limit: int = 2) -> list[Candidate]:
    """When synthesis drafts pile up, propose a review pass."""
    if not STAGING_DIR.exists():
        return []
    drafts = list(STAGING_DIR.glob("*_draft.json"))
    if len(drafts) < 3:
        return []
    # Only propose this when the queue is genuinely accumulating.
    sample_names = ", ".join(d.name for d in drafts[:3])
    return [Candidate(
        slug="review-synthesis-staging",
        proposal_type="Other",
        summary=f"Review {len(drafts)} synthesis drafts pending commit",
        body=(
            f"The synthesis staging directory has accumulated {len(drafts)} "
            f"draft extractions awaiting human review (e.g., {sample_names}). "
            f"Recommend a triage pass to either accept (commit to source "
            f"chain) or reject (move to archive)."
        ),
        evidence=SHARED_EVIDENCE + [
            {"type": "url", "ref": str(STAGING_DIR.relative_to(WORKSPACE_ROOT))}
        ],
        flourishing_rationale=(
            "Substrate-enabling: prevents Plane A → Plane B back-pressure. "
            "Unreviewed drafts mean the synthesis loop is producing without "
            "the human-gated promotion that preserves Coordination integrity."
        ),
    )][:limit]


# ---------------------------------------------------------------------------
# Source 3: stable baseline — always include at least one architecture poll
# ---------------------------------------------------------------------------

def baseline_candidates() -> list[Candidate]:
    """The hardcoded baseline from poll_high_roi_actions.py, kept as fallback.

    These are the candidates that should always be in the slate if dynamic
    sources produce too few. Mirror the existing static list verbatim so the
    heartbeat behaves identically to poll_high_roi_actions when nothing new
    is happening.
    """
    return [
        Candidate(
            slug="radicle-bridge-spike",
            proposal_type="CodeChange",
            summary="Prioritize the Radicle bridge proof-of-concept next",
            body=(
                "The next highest-ROI actionable item should be the Radicle "
                "bridge spike: create or update a real artifact on the "
                "Radicle dev-plane, link it into the local source chain, "
                "and verify the linkage from another peer so the "
                "collaboration substrate is proven end to end."
            ),
            evidence=SHARED_EVIDENCE + [
                {"type": "adr", "ref": "docs/adr/ADR-8-radicle-dev-substrate.md"}
            ],
            flourishing_rationale=(
                "Substrate-enabling: A0 dev-plane sovereignty (P5) cannot be "
                "claimed while the bridge is unproven. This is Phase 0."
            ),
        ),
        Candidate(
            slug="hashline-verification",
            proposal_type="CodeChange",
            summary="Prioritize deterministic edit verification next",
            body=(
                "Deterministic edit verification so structural edits can be "
                "checked for landing on the intended targets before they are "
                "trusted by later automation."
            ),
            evidence=SHARED_EVIDENCE,
            flourishing_rationale=(
                "Substrate-enabling: prevents silent edit drift (Knowledge), "
                "directly supports the no-stale-landings hashline pattern "
                "already in metacoordinator_mcp/hashline.py."
            ),
        ),
        Candidate(
            slug="memory-harness-layout",
            proposal_type="SpecChange",
            summary="Prioritize the filesystem memory harness layout next",
            body=(
                "Create the memory harness filesystem layout: lightweight "
                "index, topic files, task notepads, verification notes, and "
                "a nightly consolidation skeleton so interruption recovery "
                "stops burning tokens."
            ),
            evidence=SHARED_EVIDENCE,
            flourishing_rationale=(
                "Substrate-enabling: directly reduces per-session re-orientation "
                "cost, freeing attention for substrate work (Love — non-coercion "
                "of contributor attention)."
            ),
        ),
    ]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def build_dynamic_slate(max_candidates: int = 5) -> list[Candidate]:
    """Assemble the next slate from all sources, capped at max_candidates.

    Prioritization:
      1. Filewatch-driven candidates first (real new signal)
      2. Staging-driven candidates second (back-pressure relief)
      3. Baseline candidates to fill remaining slots
    """
    out: list[Candidate] = []
    seen_slugs: set[str] = set()

    def add(c: Candidate) -> None:
        if c.slug in seen_slugs:
            return
        if not c.flourishing_rationale.strip():
            # Refuse rationale-less candidates per CLAUDE.md north-star test.
            return
        out.append(c)
        seen_slugs.add(c.slug)

    for c in candidates_from_processed_events(limit=3):
        add(c)
        if len(out) >= max_candidates:
            return out

    for c in candidates_from_staged_drafts(limit=2):
        add(c)
        if len(out) >= max_candidates:
            return out

    for c in baseline_candidates():
        add(c)
        if len(out) >= max_candidates:
            return out

    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a dynamic candidate slate for high-ROI polling."
    )
    parser.add_argument("--max-candidates", type=int, default=5)
    parser.add_argument(
        "--output",
        type=Path,
        default=WORKSPACE_ROOT / ".agent-surface" / "heartbeat" / "next_slate.json",
        help="Where to write the generated slate (JSON).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = build_dynamic_slate(max_candidates=args.max_candidates)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidates": [asdict(c) for c in candidates],
        "poll_compatible": [c.to_poll_candidate() for c in candidates],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(candidates)} candidates to {args.output}")
    for c in candidates:
        print(f"  - {c.slug} ({c.proposal_type}) — {c.summary[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
