"""Backfill provenance packets for the 2026-05-25 stabilization sweep commits.

One packet per commit, signed with a session-scoped identity, capturing post-state
artifact sha256 refs (pre-state is recoverable from git history via the prior_digest
chain, since each commit's parent commit gives the pre-state).

Per ADR-12 + provenance-packet.spec.md v1.4. Commits without provenance evidence
that touch SUBSTRATE/SYSTEM blast-radius normally hard-block at the consensus
gateway; this backfill closes that gap retroactively for the 2026-05-25 sweep.

Usage: python scripts/backfill_stabilization_provenance.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from packages.activity_log.provenance import artifact_ref, create_packet  # noqa: E402

# Identity scoped to this session; lives under .agent-surface so it's
# shared across agents working in this workspace.
IDENTITY_DIR = REPO.parent / ".agent-surface" / "identity" / "stabilization-2026-05-25"
PROVENANCE_ROOT = REPO.parent / ".agent-surface" / "provenance"

COMMITS = [
    {
        "sha": "7e6d4e5",
        "subject": "substrate: land ADR-12 consent gate + Holochain 0.6/HDI 0.7 migration",
        "claim_type": "substrate_change",
        "blast_radius": "Substrate",
        "proposal_type": "spec_change",
        "evidence_refs": [
            {"type": "adr", "ref": "docs/adr/ADR-12-consent-gate-protocol.md"},
            {"type": "spec", "ref": "docs/specs/consent-payload.spec.md"},
            {"type": "test", "ref": "ARF/dnas/rose_forest/zomes/consent_integrity/src/lib.rs"},
            {"type": "commit", "ref": "7e6d4e5"},
        ],
        "risks": [
            "Holochain 0.6/HDI 0.7 migration may break previously-passing tests in the excluded pre-migration zomes (hrea_*, identity_*, memory_coordinator, ontology_integrity, infinity_bridge) when they are eventually re-migrated.",
            "ADR-12 claims 'locally verified' but action-time gating, DID/header hardening, and cross-frame validation remain pending before promotion to Accepted.",
        ],
        "benefits": [
            "Substrate-level consent gate now exists in version control rather than only the working tree.",
            "Holochain 0.6 line aligns with the canonical holochain-agent-skill reference.",
            "consent_integrity has 10 native unit tests covering all ADR-12 invariants.",
        ],
        "next_action": "Install hc CLI (cargo install holochain_cli --version 0.6.1) and run consent_gate.test.ts tryorama scenarios for end-to-end DHT round-trip evidence.",
    },
    {
        "sha": "8bfd4f8",
        "subject": "adr: land ADR-Suite v2.0 + reconcile INDEX (ADR-9..12, permanent numbers for 10/11)",
        "claim_type": "adr_change",
        "blast_radius": "System",
        "proposal_type": "adr_change",
        "evidence_refs": [
            {"type": "adr", "ref": "docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md"},
            {"type": "adr", "ref": "docs/adr/INDEX.md"},
            {"type": "commit", "ref": "8bfd4f8"},
        ],
        "risks": [
            "Pending file renames flagged (ADR-MCP-ORCHESTRATOR.md -> ADR-10, ADR-N-IPFS -> ADR-11) leave dual references in canon.",
            "ADR-2 evidence drift preserved verbatim, not silently rewritten — must be patched as separate work.",
        ],
        "benefits": [
            "Canonical ADR set now matches v2.0 suite (ADR-0..12) with friction tier + truth status on every row.",
            "Permanent numbers assigned to MCP-ORCHESTRATOR (ADR-10) and IPFS (ADR-11).",
        ],
        "next_action": "Schedule cosmetic file renames + ADR-2 evidence patch as follow-up commits.",
    },
    {
        "sha": "1deb072",
        "subject": "provenance: land activity_log + provenance-packet spec + gateway hard-block boundary",
        "claim_type": "substrate_change",
        "blast_radius": "Substrate",
        "proposal_type": "spec_change",
        "evidence_refs": [
            {"type": "spec", "ref": "docs/specs/provenance-packet.spec.md"},
            {"type": "spec", "ref": "docs/specs/consensus-gate.spec.md"},
            {"type": "test", "ref": "packages/activity_log/tests/test_provenance.py"},
            {"type": "test", "ref": "packages/metacoordinator_mcp/tests/test_provenance_gateway.py"},
            {"type": "commit", "ref": "1deb072"},
        ],
        "risks": [
            "Gateway hard-block boundary for SYSTEM/SUBSTRATE + ADR/CONFIG/SPEC changes is enforced from now on — prior un-packeted claims fail-closed against this rule.",
        ],
        "benefits": [
            "Activity log unification (U1/U2/U3 of metaharness unification) lands; provenance packet schema v1.4 is the durable evidence layer.",
            "INV-015 in consensus-gate.spec adds provenance_packet evidence validation.",
        ],
        "next_action": "M2 (this backfill) emits packets for the 10 stabilization commits so they meet the new boundary retroactively.",
    },
    {
        "sha": "5e8f345",
        "subject": "docs: stabilize doc landscape — architecture v0.1-v4.0 + governance + 33 research + 7 specs + agent-memory",
        "claim_type": "doc_landscape_stabilization",
        "blast_radius": "System",
        "proposal_type": "spec_change",
        "evidence_refs": [
            {"type": "adr", "ref": "docs/adr/FLOSSI0ULLK-ADR-Suite-v2.0.md"},
            {"type": "spec", "ref": "docs/specs/heartbeat-runtime-budget.spec.md"},
            {"type": "spec", "ref": "docs/specs/intake-event.spec.md"},
            {"type": "commit", "ref": "5e8f345"},
        ],
        "risks": [
            "154 files landed in one commit; future blame searches will hit this bulk commit rather than the original author of each doc.",
            "Doc-explosion pattern acknowledged; doc-budget discipline applies going forward, not retroactively to canon already authored.",
        ],
        "benefits": [
            "Doc landscape no longer lives only in working tree; the 46 agent-memory files, 33 research drops, 9 architecture docs, 7 specs, and 2 governance docs all survive a working-tree reset.",
        ],
        "next_action": "Apply doc-budget discipline (default position: do not add a doc) to all future doc work.",
    },
    {
        "sha": "d649c59",
        "subject": "ops: land reasoning ensemble + operational scripts + shared surfaces + OMO Momus voter",
        "claim_type": "ops_module_addition",
        "blast_radius": "Module",
        "proposal_type": "code_change",
        "evidence_refs": [
            {"type": "spec", "ref": "docs/specs/reasoning-ensemble-router.spec.md"},
            {"type": "spec", "ref": "docs/specs/reasoning-ensemble-synthesizer.spec.md"},
            {"type": "test", "ref": "scripts/tests/test_global_activity_wiring.py"},
            {"type": "test", "ref": "scripts/tests/test_heartbeat_budget.py"},
            {"type": "commit", "ref": "d649c59"},
        ],
        "risks": [
            "Heartbeat (paused via STOP file) and autonomous synthesis (capped) are now version-controlled but still require runtime-budget verification before resume per A.1 in working-todo.",
            "Mistral + OMO Momus voters add diversity but increase per-round Groq spend.",
        ],
        "benefits": [
            "Reasoning ensemble Router + Synthesizer + MCP server now durable.",
            "Cross-harness AI roster materializer ships across Codex/Claude/Gemini/OpenCode.",
            "Five activity-log tee points wired into unified .agent-surface/activity.jsonl.",
        ],
        "next_action": "Verify heartbeat-runtime-budget.spec.md matches code before deleting .agent-surface/heartbeat/STOP (Phase 4 P4.2).",
    },
    {
        "sha": "51b56b4",
        "subject": "stabilize: catch up intake relocations, .bak cleanup, FLOSSI_U lift-out, archive preservation",
        "claim_type": "cleanup",
        "blast_radius": "Local",
        "proposal_type": "code_change",
        "evidence_refs": [
            {"type": "commit", "ref": "51b56b4"},
            {"type": "adr", "ref": "FLOSS/CLAUDE.md"},
        ],
        "risks": [],
        "benefits": [
            "FLOSSI_U lift-out, 2026-05-19 intake relocation, and stale .bak file deletions are now reflected in the version graph.",
        ],
        "next_action": "No action; cleanup commit complete.",
    },
    {
        "sha": "32535fa",
        "subject": "state: snapshot knowledge_log/staging + .claude/.serena IDE memories",
        "claim_type": "state_preservation",
        "blast_radius": "Local",
        "proposal_type": "code_change",
        "evidence_refs": [
            {"type": "commit", "ref": "32535fa"},
        ],
        "risks": [
            "112 synthesis drafts in docs/knowledge_log/staging/ are NOT canon — committing them as a snapshot does not promote them.",
        ],
        "benefits": [
            "Review queue survives a working-tree reset.",
        ],
        "next_action": "Phase 4 P4.1 triages the 178 review-queue items.",
    },
    {
        "sha": "02b1348",
        "subject": "archive: preserve 2026-04-15 session-continuation transcript",
        "claim_type": "archive",
        "blast_radius": "Local",
        "proposal_type": "code_change",
        "evidence_refs": [
            {"type": "commit", "ref": "02b1348"},
        ],
        "risks": [],
        "benefits": [
            "Loose root transcript moved to archive/intake_raw/session-transcripts/ rather than deleted.",
        ],
        "next_action": "Future session transcripts should land in archive/intake_raw/session-transcripts/ directly.",
    },
    {
        "sha": "f820fc9",
        "subject": "intake: stage 2026-05-25 root drops (7 files) + digestion map",
        "claim_type": "intake_digestion",
        "blast_radius": "Module",
        "proposal_type": "code_change",
        "evidence_refs": [
            {"type": "spec", "ref": "docs/research/2026-05-25-root-intake-digestion.md"},
            {"type": "url", "ref": ".agent-surface/intake/root-intake-moves-2026-05-25.json"},
            {"type": "commit", "ref": "f820fc9"},
        ],
        "risks": [
            "ADR-003 root-drop and Terabox upload .cfg left at root, handled separately.",
        ],
        "benefits": [
            "Levin Corpus + ODI Research Scan now under git, ready for distillation in P2.4/P2.5.",
        ],
        "next_action": "Phase 2 P2.4 distills Levin Corpus -> CCES implications; P2.5 distills ODI Scan -> landscape delta.",
    },
    {
        "sha": "94dc3de",
        "subject": "adr: replace ADR-3 with amended v1.1.0 (Accepted + Empirical Grounding); archive v1.0.0",
        "claim_type": "adr_change",
        "blast_radius": "System",
        "proposal_type": "adr_change",
        "evidence_refs": [
            {"type": "adr", "ref": "docs/adr/ADR-3-metaprompt-kernelization.md"},
            {"type": "url", "ref": "archive/adr-versions/ADR-3-metaprompt-kernelization_v1.0.0_2026-01-12.md"},
            {"type": "url", "ref": "https://arxiv.org/abs/2507.09089"},
            {"type": "url", "ref": "https://www.gitclear.com/ai_assistant_code_quality_2025_research"},
            {"type": "url", "ref": "https://arxiv.org/abs/2506.08872"},
            {"type": "commit", "ref": "94dc3de"},
        ],
        "risks": [
            "Empirical Grounding citations are external; require periodic re-verification (METR Feb 2026 follow-up was abandoned — see ADR-3 §EG-1 limitations).",
        ],
        "benefits": [
            "ADR-3 promoted PROPOSED -> ACCEPTED with traceable empirical grounding from 4 independent studies.",
        ],
        "next_action": "No action; ADR-3 stabilized at v1.1.0.",
    },
]


def changed_files_for_commit(sha: str) -> list[str]:
    """Return workspace-relative paths of files changed by the given commit."""

    result = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", sha],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        # git show emits paths relative to the git repo root (FLOSS).
        # The provenance artifact_ref expects workspace-relative paths (relative
        # to FLOSS's parent — workspace root C:\~shit\). Map by prefixing FLOSS/.
        paths.append(f"FLOSS/{line}")
    return paths


def main() -> int:
    written: list[tuple[str, Path]] = []
    skipped: list[str] = []

    for spec in COMMITS:
        sha = spec["sha"]
        changed = changed_files_for_commit(sha)

        artifact_refs = []
        for rel in changed:
            abs_path = REPO.parent / rel
            if abs_path.exists() and abs_path.is_file():
                try:
                    artifact_refs.append(artifact_ref(abs_path, workspace_root=REPO.parent))
                except (OSError, ValueError) as e:
                    skipped.append(f"  ! {rel}: {e}")
            # Files deleted by the commit are not present in working tree;
            # post-state sha256 is N/A. Skip them for artifact_refs; they're
            # still tracked via the git commit ref in evidence.

        if not artifact_refs:
            skipped.append(f"  ! commit {sha}: no current artifacts to hash")
            continue

        # Cap artifact_refs at 100 per packet to keep packet size sane; if a
        # commit touched more files, list the top 100 + a count.
        capped = artifact_refs[:100]
        capped_note = ""
        if len(artifact_refs) > 100:
            capped_note = f" (capped from {len(artifact_refs)} files)"

        entry = {
            "claim_type": spec["claim_type"],
            "truth_status": "Specified",
            "source_systems": [
                "git",
                "claude-code-sonnet-4.7-stabilization-sweep-2026-05-25",
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "human_collision_node": "kalisam",
            "artifact_refs": capped,
            "evidence_refs": spec["evidence_refs"],
            "risks": spec["risks"],
            "benefits": spec["benefits"],
            "next_action": spec["next_action"],
            "prov_o_activity_id": f"commit:{sha}",
            "in_toto_predicate_type": f"https://flossi0ullk.local/predicates/{spec['proposal_type']}",
            "blast_radius": spec["blast_radius"],
            "proposal_type": spec["proposal_type"],
            "commit_subject": spec["subject"] + capped_note,
        }

        try:
            # Use prior_digest=None (explicit genesis) for each backfill so
            # they're independent genesis-tier packets, not a chained sequence.
            # Backfilled commits are logically parallel events; chaining them
            # would only constrain the validator depth (default max_depth=8)
            # without adding evidential value.
            packet, packet_path = create_packet(
                [entry],
                identity_dir=IDENTITY_DIR,
                output_root=PROVENANCE_ROOT,
                prior_digest=None,
            )
            written.append((sha, packet_path))
        except Exception as e:  # noqa: BLE001 — surface backfill failures loudly
            skipped.append(f"  ! commit {sha}: create_packet failed: {e}")

    print("BACKFILL SUMMARY")
    print(f"  written: {len(written)}")
    for sha, path in written:
        rel = path.relative_to(REPO.parent).as_posix()
        print(f"    {sha} -> {rel}")
    if skipped:
        print(f"  skipped: {len(skipped)}")
        for line in skipped:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
