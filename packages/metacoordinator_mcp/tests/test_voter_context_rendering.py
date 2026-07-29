"""Regression tests for PR38 review thread PRRT_kwDOPkAi3s6UUuKj.

`run_consensus_round` must pass validated provenance-packet metadata into
each voter's prompt as the `context` slot, so a governed System/Substrate
claim that already cleared the hard provenance gate does not look
context-empty to voters (and does not get force-non-positive by the
calibrated checklist item 4).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[3]
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))

from packages.activity_log import provenance  # noqa: E402
from packages.metacoordinator_mcp.tools import GatewayTools  # noqa: E402
from packages.metacoordinator_mcp.voters import render_voter_prompt  # noqa: E402
from packages.orchestrator.claim_schema import (  # noqa: E402
    BlastRadius,
    Claim,
    EvidenceRef,
    ProposalType,
)

DNA_HASH = "c" * 64


def _make_gateway(base_dir: str, workspace_root: Path) -> GatewayTools:
    return GatewayTools(
        base_dir=Path(base_dir),
        dna_hash=DNA_HASH,
        workspace_root=workspace_root,
    )


def _make_governed_packet(
    workspace_root: Path,
    output_root: Path,
    *,
    nested_evidence_ref: str = "docs/specs/provenance-packet.spec.md",
) -> tuple[dict, dict]:
    artifact = workspace_root / "FLOSS" / "docs" / "specs" / "provenance-packet.spec.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("spec", encoding="utf-8")
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-05-24T10:00:00Z",
        "human_collision_node": "anthony",
        "artifact_refs": [
            provenance.artifact_ref(artifact, workspace_root=workspace_root)
        ],
        "evidence_refs": [{"type": "spec", "ref": nested_evidence_ref}],
        "risks": [],
        "benefits": [],
        "next_action": "submit claim",
        "consent_ref": {"decision_action_hash": "uhCAk" + ("a" * 32)},
    }
    packet, path = provenance.create_packet(
        [entry],
        identity_dir=workspace_root / ".floss_agent" / "identity",
        output_root=output_root,
    )
    ref = {
        "type": "provenance_packet",
        "ref": str(path.relative_to(workspace_root).as_posix()),
        "sha256": provenance.sha256_file(path),
    }
    return ref, packet


def _claim_with_packet_ref(ref: dict) -> Claim:
    """Build a minimal governed Claim carrying a single provenance_packet ref."""
    return Claim(
        proposer="claude",
        proposal_type=ProposalType.SPEC_CHANGE,
        summary="governed spec change",
        body="body under test",
        blast_radius=BlastRadius.SYSTEM,
        evidence=[
            EvidenceRef(
                type=ref["type"],
                ref=ref["ref"],
                sha256=ref.get("sha256"),
            )
        ],
    )


def test_render_voter_context_returns_none_when_no_packet_evidence(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        gw = _make_gateway(tmp, tmp_path)
        claim = Claim(
            proposer="claude",
            proposal_type=ProposalType.CODE_CHANGE,
            summary="local",
            body="body",
            blast_radius=BlastRadius.LOCAL,
            evidence=[EvidenceRef(type="test", ref="unit")],
        )
        assert gw._render_voter_context(claim) == "(none)"


def test_render_voter_context_exposes_digest_consent_and_nested_evidence(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        ref, packet = _make_governed_packet(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
        )
        gw = _make_gateway(tmp, tmp_path)
        claim = _claim_with_packet_ref(ref)
        context = gw._render_voter_context(claim)

    assert context != "(none)"
    # Every field the review comment named must appear in the voter-visible context.
    assert "packet digest=" in context
    assert packet["d"] in context
    assert "consent_ref=uhCAk" in context
    assert "nested_evidence=" in context
    assert "[spec] docs/specs/provenance-packet.spec.md" in context


def test_render_voter_prompt_surfaces_context_in_prompt_body(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        ref, _packet = _make_governed_packet(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
        )
        gw = _make_gateway(tmp, tmp_path)
        claim = _claim_with_packet_ref(ref)
        context = gw._render_voter_context(claim)
        prompt = render_voter_prompt(claim, context)

    # The prompt's Context: slot must carry the rendered digest/consent — not "(none)".
    assert "Context:      packet digest=" in prompt
    assert "consent_ref=uhCAk" in prompt
    # Guardrail: we must not have regressed the legacy path.
    default_prompt = render_voter_prompt(claim)
    assert "Context:      (none)" in default_prompt


def test_run_consensus_round_threads_context_into_voter_callable(tmp_path):
    """End-to-end: run_consensus_round must pass rendered context to each voter."""
    captured_contexts: list[str] = []

    def approving_voter(claim, context="(none)"):
        from packages.orchestrator.claim_schema import Vote

        captured_contexts.append(context)
        return Vote(
            voter="ctx-probe",
            weight=0.7,
            rationale="captured context for regression assertion",
        )

    def factory():
        return [approving_voter]

    with tempfile.TemporaryDirectory() as tmp:
        ref, packet = _make_governed_packet(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
        )
        gw = GatewayTools(
            base_dir=Path(tmp),
            dna_hash=DNA_HASH,
            voter_factory=factory,
            workspace_root=tmp_path,
        )
        submit_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="SpecChange",
                summary="governed spec change",
                body="body under test",
                blast_radius="System",
                evidence=[ref],
            )
        )
        assert "claim_id" in submit_result, submit_result
        round_result = json.loads(gw.run_consensus_round(submit_result["claim_id"]))

    assert "error" not in round_result, round_result
    assert captured_contexts, "voter was not invoked"
    ctx = captured_contexts[0]
    assert ctx != "(none)"
    assert "packet digest=" in ctx
    assert packet["d"] in ctx
    assert "consent_ref=uhCAk" in ctx


def test_run_consensus_round_still_calls_legacy_one_arg_voter(tmp_path):
    """Backward compat: pre-PR38 test harness voters with (claim) only must still work."""
    calls: list[Claim] = []

    def legacy_voter(claim):  # noqa: ANN001 — deliberately 1-arg
        from packages.orchestrator.claim_schema import Vote

        calls.append(claim)
        return Vote(
            voter="legacy-probe",
            weight=0.6,
            rationale="legacy 1-arg voter still receives claim",
        )

    def factory():
        return [legacy_voter]

    with tempfile.TemporaryDirectory() as tmp:
        gw = GatewayTools(
            base_dir=Path(tmp),
            dna_hash=DNA_HASH,
            voter_factory=factory,
            workspace_root=tmp_path,
        )
        submit_result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="CodeChange",
                summary="local change",
                body="body",
                blast_radius="Local",
                evidence=[{"type": "test", "ref": "unit"}],
            )
        )
        assert "claim_id" in submit_result, submit_result
        round_result = json.loads(gw.run_consensus_round(submit_result["claim_id"]))

    assert "error" not in round_result, round_result
    assert calls, "legacy voter was not invoked"
