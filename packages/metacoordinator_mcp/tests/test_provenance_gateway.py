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

DNA_HASH = "c" * 64


def make_gateway(tmp: str, workspace_root: Path) -> GatewayTools:
    return GatewayTools(
        base_dir=Path(tmp),
        dna_hash=DNA_HASH,
        workspace_root=workspace_root,
    )


def _packet_evidence(
    workspace_root: Path, output_root: Path, *, governed: bool = False
):
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
        "evidence_refs": [{"type": "test", "ref": "gateway-provenance"}],
        "risks": [],
        "benefits": [],
        "next_action": "submit claim",
    }
    if governed:
        entry["consent_ref"] = {"decision_action_hash": "uhCAk" + ("a" * 32)}
    packet, path = provenance.create_packet(
        [entry],
        identity_dir=workspace_root / ".floss_agent" / "identity",
        output_root=output_root,
    )
    return {
        "type": "provenance_packet",
        "ref": str(path.relative_to(workspace_root).as_posix()),
        "sha256": provenance.sha256_file(path),
    }, packet


def test_system_spec_claim_requires_valid_packet_and_consent_ref(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        gw = make_gateway(tmp, tmp_path)
        result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="SpecChange",
                summary="system spec",
                body="body",
                blast_radius="System",
            )
        )

    assert "error" in result
    assert "E_GOVERNED_PROVENANCE_REQUIRED" in result["error"]


def test_gateway_accepts_governed_claim_with_valid_packet_and_consent(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        evidence, _packet = _packet_evidence(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
            governed=True,
        )
        gw = make_gateway(tmp, tmp_path)
        result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="SpecChange",
                summary="system spec",
                body="body",
                blast_radius="System",
                evidence=[evidence],
            )
        )

    assert "claim_id" in result
    assert "entry_hash" in result


def test_gateway_rejects_tampered_packet_evidence(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        evidence, packet = _packet_evidence(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
            governed=True,
        )
        packet_path = tmp_path / evidence["ref"]
        packet["a"][0]["next_action"] = "tampered"
        packet_path.write_text(json.dumps(packet), encoding="utf-8")
        evidence["sha256"] = provenance.sha256_file(packet_path)

        gw = make_gateway(tmp, tmp_path)
        result = json.loads(
            gw.submit_claim(
                proposer="claude",
                proposal_type="SpecChange",
                summary="system spec",
                body="body",
                blast_radius="System",
                evidence=[evidence],
            )
        )

    assert "error" in result
    assert "E_PROVENANCE_SIGNATURE_INVALID" in result["error"]
