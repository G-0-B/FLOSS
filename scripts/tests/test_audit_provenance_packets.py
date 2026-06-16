from __future__ import annotations

import sys
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[2]
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))

from packages.activity_log import provenance  # noqa: E402
from scripts.audit_provenance_packets import audit_packets  # noqa: E402


def test_audit_packets_emits_narrative_for_valid_packet(tmp_path, monkeypatch):
    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("audit", encoding="utf-8")
    output_root = tmp_path / ".agent-surface" / "provenance"
    packet, _path = provenance.create_packet(
        [
            {
                "claim_type": "proposal",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:00:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(artifact, workspace_root=tmp_path)
                ],
                "evidence_refs": [{"type": "test", "ref": "audit"}],
                "risks": [],
                "benefits": [],
                "next_action": "audit",
            }
        ],
        identity_dir=tmp_path / "identity",
        output_root=output_root,
    )

    invalid_count, records, lines = audit_packets(output_root, workspace_root=tmp_path)

    assert invalid_count == 0
    assert records[0]["packet_digest"] == packet["d"]
    assert records[0]["audit_status"] == "valid"
    assert lines == records[0]["narrative_lines"]
    assert "proposal -> artifact.txt" in lines[0]


def test_audit_packets_classifies_mutable_generated_hash_drift_as_superseded(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / ".agent-surface" / "context" / "CONTEXT_L0.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("old generated projection", encoding="utf-8")
    output_root = tmp_path / ".agent-surface" / "provenance"
    packet, _path = provenance.create_packet(
        [
            {
                "claim_type": "shared_surface_projection",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:00:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(artifact, workspace_root=tmp_path)
                ],
                "evidence_refs": [{"type": "test", "ref": "audit"}],
                "risks": [],
                "benefits": [],
                "next_action": "audit",
            }
        ],
        identity_dir=tmp_path / "identity",
        output_root=output_root,
        prior_digest=None,
    )
    artifact.write_text("new generated projection", encoding="utf-8")

    invalid_count, records, lines = audit_packets(output_root, workspace_root=tmp_path)

    assert invalid_count == 0
    assert records[0]["packet_digest"] == packet["d"]
    assert records[0]["ok"] is False
    assert records[0]["audit_status"] == "superseded"
    assert records[0]["superseded_reason"] == "mutable_generated_artifact_drift"
    assert "E_PROVENANCE_ARTIFACT_HASH_MISMATCH" in records[0]["errors"]
    assert lines == [
        (
            f"[SUPERSEDED] {records[0]['path']} :: "
            "mutable_generated_artifact_drift :: "
            "E_PROVENANCE_ARTIFACT_HASH_MISMATCH"
        )
    ]


def test_audit_packets_keeps_canonical_hash_drift_invalid(tmp_path, monkeypatch):
    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / "FLOSS" / "docs" / "specs" / "canon.spec.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("old canon", encoding="utf-8")
    output_root = tmp_path / ".agent-surface" / "provenance"
    packet, _path = provenance.create_packet(
        [
            {
                "claim_type": "SpecChange",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:00:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(artifact, workspace_root=tmp_path)
                ],
                "evidence_refs": [{"type": "test", "ref": "audit"}],
                "risks": [],
                "benefits": [],
                "next_action": "audit",
            }
        ],
        identity_dir=tmp_path / "identity",
        output_root=output_root,
        prior_digest=None,
    )
    artifact.write_text("new canon", encoding="utf-8")

    invalid_count, records, lines = audit_packets(output_root, workspace_root=tmp_path)

    assert invalid_count == 1
    assert records[0]["packet_digest"] == packet["d"]
    assert records[0]["audit_status"] == "invalid"
    assert lines == [
        f"[INVALID] {records[0]['path']} :: E_PROVENANCE_ARTIFACT_HASH_MISMATCH"
    ]


def test_audit_packets_classifies_older_packet_covered_by_newer_valid_packet_as_superseded(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / "FLOSS" / "scripts" / "materializer.py"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("old implementation", encoding="utf-8")
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "identity"
    older_packet, _older_path = provenance.create_packet(
        [
            {
                "claim_type": "shared_surface_projection",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:00:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(artifact, workspace_root=tmp_path)
                ],
                "evidence_refs": [{"type": "test", "ref": "audit-old"}],
                "risks": [],
                "benefits": [],
                "next_action": "audit old",
            }
        ],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    artifact.write_text("new implementation", encoding="utf-8")
    newer_packet, _newer_path = provenance.create_packet(
        [
            {
                "claim_type": "shared_surface_projection",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:05:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(artifact, workspace_root=tmp_path)
                ],
                "evidence_refs": [{"type": "test", "ref": "audit-new"}],
                "risks": [],
                "benefits": [],
                "next_action": "audit new",
            }
        ],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )

    invalid_count, records, lines = audit_packets(output_root, workspace_root=tmp_path)

    by_digest = {record["packet_digest"]: record for record in records}
    assert invalid_count == 0
    assert by_digest[older_packet["d"]]["audit_status"] == "superseded"
    assert by_digest[older_packet["d"]]["superseded_reason"] == "newer_valid_packet"
    assert by_digest[older_packet["d"]]["superseded_by"] == newer_packet["d"]
    assert by_digest[newer_packet["d"]]["audit_status"] == "valid"
    assert any(line.startswith("[SUPERSEDED]") for line in lines)
