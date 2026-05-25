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
    assert lines == records[0]["narrative_lines"]
    assert "proposal -> artifact.txt" in lines[0]
