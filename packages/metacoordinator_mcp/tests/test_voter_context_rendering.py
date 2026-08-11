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

import pytest

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


def _claim_with_packet_refs(refs: list[dict]) -> Claim:
    """Build a minimal governed Claim carrying provenance-packet refs."""
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
            for ref in refs
        ],
    )


def _claim_with_packet_ref(ref: dict) -> Claim:
    """Build a minimal governed Claim carrying one provenance-packet ref."""
    return _claim_with_packet_refs([ref])


def _packet_entry(
    workspace_root: Path,
    *,
    evidence_refs: list[dict],
    created_at: str = "2026-05-24T10:00:00Z",
    consent_hash: str = "uhCAk" + ("a" * 32),
) -> dict:
    """Build a complete packet entry with a real artifact for validation."""
    artifact = workspace_root / "FLOSS" / "docs" / "specs" / "packet-artifact.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("packet artifact", encoding="utf-8")
    return {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": created_at,
        "human_collision_node": "anthony",
        "artifact_refs": [
            provenance.artifact_ref(artifact, workspace_root=workspace_root)
        ],
        "evidence_refs": evidence_refs,
        "risks": [],
        "benefits": [],
        "next_action": "submit claim",
        "consent_ref": {"decision_action_hash": consent_hash},
    }


def _packet_ref(path: Path, workspace_root: Path) -> dict:
    """Return a provenance-packet evidence reference for a written packet."""
    return {
        "type": "provenance_packet",
        "ref": str(path.relative_to(workspace_root).as_posix()),
        "sha256": provenance.sha256_file(path),
    }


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


def test_render_voter_context_traverses_real_signed_child_packet(tmp_path):
    """A valid root may render a child's non-packet evidence exactly once."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        _child, child_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "child-only.md"}],
                )
            ],
            identity_dir=tmp_path / "child-identity",
            output_root=output_root,
            prior_digest=None,
        )
        child_ref = _packet_ref(child_path, tmp_path)
        root, root_path = provenance.create_packet(
            [_packet_entry(tmp_path, evidence_refs=[child_ref])],
            identity_dir=tmp_path / "root-identity",
            output_root=output_root,
            prior_digest=None,
        )
        assert provenance.validate_packet(
            root_path, workspace_root=tmp_path, provenance_root=output_root
        ).ok

        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(root_path, tmp_path))
        )

    assert root["d"] in context
    assert "[spec] child-only.md" in context


def test_render_voter_context_deduplicates_shared_child_evidence(tmp_path):
    """A child cited twice contributes its validated metadata once."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        _child, child_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "shared-child.md"}],
                )
            ],
            identity_dir=tmp_path / "child-identity",
            output_root=output_root,
            prior_digest=None,
        )
        child_ref = _packet_ref(child_path, tmp_path)
        _root, root_path = provenance.create_packet(
            [_packet_entry(tmp_path, evidence_refs=[child_ref, child_ref])],
            identity_dir=tmp_path / "root-identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(root_path, tmp_path))
        )

    assert context.count("[spec] shared-child.md") == 1


def test_render_voter_context_bounds_and_sanitizes_many_refs(tmp_path):
    """Voter context is bounded, injection-safe, and explicitly truncates."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        refs = [
            {"type": "spec", "ref": f"doc-{index}\n\t injected.md"}
            for index in range(33)
        ]
        _packet, packet_path = provenance.create_packet(
            [_packet_entry(tmp_path, evidence_refs=refs)],
            identity_dir=tmp_path / "identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert "[truncated]" in context
    assert context.count("[spec]") == 32
    assert "\n" not in context
    assert "\r" not in context
    assert "\t" not in context
    assert len(context) <= 4096


def test_render_voter_context_preserves_packet_metadata_when_evidence_is_oversized(
    tmp_path,
):
    """Evidence truncation cannot erase the packet digest or consent hash."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        refs = [
            {"type": "spec", "ref": f"doc-{index}-{'x' * 500}.md"}
            for index in range(32)
        ]
        packet, packet_path = provenance.create_packet(
            [_packet_entry(tmp_path, evidence_refs=refs)],
            identity_dir=tmp_path / "identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert len(context) <= 4096
    assert "[truncated]" in context
    assert packet["d"] in context
    assert "uhCAk" + ("a" * 32) in context


def test_render_voter_context_marks_an_individually_shortened_reference(tmp_path):
    """A sliced evidence identity must be visibly marked as incomplete."""
    long_ref = f"docs/{'x' * 260}.md"
    with tempfile.TemporaryDirectory() as tmp:
        ref, packet = _make_governed_packet(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
            nested_evidence_ref=long_ref,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(ref)
        )

    assert packet["d"] in context
    assert f"[spec] {long_ref[:240]}" in context
    assert long_ref not in context
    assert "[truncated]" in context


def test_render_voter_context_reserves_both_signed_packet_headers(tmp_path):
    """Earlier optional evidence cannot suppress a later packet header."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        packets: list[dict] = []
        packet_refs: list[dict] = []
        consent_hashes = ["consent-one-hash", "consent-two-hash"]
        for packet_index, consent_hash in enumerate(consent_hashes):
            refs = [
                {
                    "type": "spec",
                    "ref": (
                        f"packet-{packet_index}-doc-{ref_index}\n\r\t"
                        f"{'x' * 500}.md"
                    ),
                }
                for ref_index in range(16)
            ]
            packet, packet_path = provenance.create_packet(
                [
                    _packet_entry(
                        tmp_path,
                        evidence_refs=refs,
                        consent_hash=consent_hash,
                    )
                ],
                identity_dir=tmp_path / f"identity-{packet_index}",
                output_root=output_root,
                prior_digest=None,
            )
            packets.append(packet)
            packet_refs.append(_packet_ref(packet_path, tmp_path))

        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_refs(packet_refs)
        )

    assert len(context) <= 4096
    assert "[truncated]" in context
    for packet, consent_hash in zip(packets, consent_hashes):
        assert packet["d"] in context
        assert consent_hash in context
    assert "\n" not in context
    assert "\r" not in context
    assert "\t" not in context


def test_render_voter_context_fails_closed_when_packet_headers_exceed_bound(tmp_path):
    """Unbounded top-level packet lists cannot imply partial metadata coverage."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        packet_refs: list[dict] = []
        for packet_index in range(17):
            consent_hash = f"consent-{packet_index:02d}-" + ("c" * 149)
            _packet, packet_path = provenance.create_packet(
                [
                    _packet_entry(
                        tmp_path,
                        evidence_refs=[
                            {"type": "spec", "ref": f"packet-{packet_index}.md"}
                        ],
                        consent_hash=consent_hash,
                    )
                ],
                identity_dir=tmp_path / f"overflow-identity-{packet_index}",
                output_root=output_root,
                prior_digest=None,
            )
            packet_refs.append(_packet_ref(packet_path, tmp_path))

        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_refs(packet_refs)
        )

    assert context == "[packet metadata exceeds 4096-character voter context limit]"
    assert len(context) <= 4096


def test_render_voter_context_fails_closed_on_oversized_consent_hash(tmp_path):
    """A valid oversized mandatory hash cannot be rendered as a partial value."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        consent_hash = "c" * 201
        _packet, packet_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "oversized-hash.md"}],
                    consent_hash=consent_hash,
                )
            ],
            identity_dir=tmp_path / "identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert context == "[packet metadata exceeds per-value voter context limit]"
    assert consent_hash not in context
    assert consent_hash[:160] not in context


def test_render_voter_context_fails_closed_when_consent_hash_changes_on_sanitize(
    tmp_path,
):
    """Mandatory signed metadata must never be normalized into a new identity."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        consent_hash = "consent-part-1\n\tconsent-part-2"
        _packet, packet_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "exact-consent.md"}],
                    consent_hash=consent_hash,
                )
            ],
            identity_dir=tmp_path / "identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert context == (
        "[packet mandatory metadata cannot be represented exactly in voter context]"
    )
    assert "consent-part-1" not in context
    assert "consent-part-2" not in context


def test_render_voter_context_fails_closed_on_non_printable_consent_hash(tmp_path):
    """Schema-valid control characters cannot enter the voter prompt unchanged."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        consent_hash = "consent-part-1\x00consent-part-2"
        _packet, packet_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "control-consent.md"}],
                    consent_hash=consent_hash,
                )
            ],
            identity_dir=tmp_path / "identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert context == (
        "[packet mandatory metadata cannot be represented exactly in voter context]"
    )
    assert "consent-part-1" not in context
    assert "consent-part-2" not in context


def test_render_voter_context_deduplicates_before_unique_ref_budget(tmp_path):
    """Repeated metadata cannot crowd out a later unique evidence ref."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        duplicate = {"type": "spec", "ref": "duplicate.md"}
        refs = [dict(duplicate) for _ in range(32)]
        refs.append({"type": "spec", "ref": "later-unique.md"})
        _packet, packet_path = provenance.create_packet(
            [_packet_entry(tmp_path, evidence_refs=refs)],
            identity_dir=tmp_path / "identity",
            output_root=output_root,
            prior_digest=None,
        )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert context.count("[spec] duplicate.md") == 1
    assert context.count("[spec] later-unique.md") == 1
    assert "[truncated]" not in context


def test_cyclic_packet_traversal_returns_and_renders_no_evidence(
    tmp_path, monkeypatch
):
    """A cycle hidden beyond the ref budget invalidates all derived metadata."""
    root_path = tmp_path / "cycle-root.json"
    child_path = tmp_path / "cycle-child.json"
    root_path.write_text("{}", encoding="utf-8")
    child_path.write_text("{}", encoding="utf-8")

    root_packet = {
        "d": "cycle-root-digest",
        "a": [
            {
                "consent_ref": {"decision_action_hash": "cycle-consent-hash"},
                "evidence_refs": [
                    *[
                        {"type": "spec", "ref": f"cycle-leak-{index}.md"}
                        for index in range(33)
                    ],
                    {"type": "provenance_packet", "ref": child_path.name},
                ],
            }
        ],
    }
    child_packet = {
        "d": "cycle-child-digest",
        "a": [
            {
                "evidence_refs": [
                    {"type": "provenance_packet", "ref": root_path.name}
                ]
            }
        ],
    }

    def fake_validate(packet_or_path, **_kwargs):
        packet = (
            child_packet
            if Path(packet_or_path).name == child_path.name
            else root_packet
        )
        return provenance.PacketValidation(
            ok=True,
            packet_digest=packet["d"],
            packet=packet,
        )

    monkeypatch.setattr(provenance, "validate_packet", fake_validate)

    with pytest.raises(ValueError, match="E_PROVENANCE_CYCLE_DETECTED"):
        provenance.validated_non_packet_evidence_refs(
            root_path,
            workspace_root=tmp_path,
            max_refs=32,
        )

    with tempfile.TemporaryDirectory() as tmp:
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(
                {"type": "provenance_packet", "ref": root_path.name}
            )
        )

    assert "cycle-root-digest" in context
    assert "cycle-consent-hash" in context
    assert "nested_evidence=(none)" in context
    assert "cycle-leak" not in context


def test_render_voter_context_omits_child_evidence_when_root_is_invalid(tmp_path):
    """Invalid supplied packets cannot leak otherwise-valid child metadata."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        _child, child_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "do-not-render.md"}],
                )
            ],
            identity_dir=tmp_path / "child-identity",
            output_root=output_root,
            prior_digest=None,
        )
        _root, root_path = provenance.create_packet(
            [_packet_entry(tmp_path, evidence_refs=[_packet_ref(child_path, tmp_path)])],
            identity_dir=tmp_path / "root-identity",
            output_root=output_root,
            prior_digest=None,
        )
        broken = json.loads(root_path.read_text(encoding="utf-8"))
        broken["sigs"] = ["0B" + ("A" * 86)]
        root_path.write_text(json.dumps(broken), encoding="utf-8")
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(
                {
                    "type": "provenance_packet",
                    "ref": str(root_path.relative_to(tmp_path).as_posix()),
                }
            )
        )

    assert context == "(none)"
    assert "do-not-render.md" not in context


def test_render_voter_context_omits_child_evidence_when_depth_exceeds_limit(tmp_path):
    """Depth-invalid evidence DAGs cannot supply voter-visible child metadata."""
    with tempfile.TemporaryDirectory() as tmp:
        output_root = tmp_path / ".agent-surface" / "provenance"
        _packet, packet_path = provenance.create_packet(
            [
                _packet_entry(
                    tmp_path,
                    evidence_refs=[{"type": "spec", "ref": "too-deep.md"}],
                )
            ],
            identity_dir=tmp_path / "identity-0",
            output_root=output_root,
            prior_digest=None,
        )
        for depth in range(1, 10):
            _packet, packet_path = provenance.create_packet(
                [_packet_entry(tmp_path, evidence_refs=[_packet_ref(packet_path, tmp_path)])],
                identity_dir=tmp_path / f"identity-{depth}",
                output_root=output_root,
                prior_digest=None,
            )
        context = _make_gateway(tmp, tmp_path)._render_voter_context(
            _claim_with_packet_ref(_packet_ref(packet_path, tmp_path))
        )

    assert context == "(none)"
    assert "too-deep.md" not in context


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
