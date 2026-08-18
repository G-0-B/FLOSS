from __future__ import annotations

import json
import inspect
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[3]
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))

from packages.activity_log import provenance  # noqa: E402
from packages.metacoordinator_mcp.tools import GatewayTools  # noqa: E402

DNA_HASH = "c" * 64


def make_gateway(
    tmp: str,
    workspace_root: Path,
    *,
    provenance_root: Path | None = None,
) -> GatewayTools:
    kwargs = {
        "base_dir": Path(tmp),
        "dna_hash": DNA_HASH,
        "workspace_root": workspace_root,
    }
    if provenance_root is not None:
        kwargs["provenance_root"] = provenance_root
    return GatewayTools(**kwargs)


def _packet_evidence(
    workspace_root: Path,
    output_root: Path,
    *,
    governed: bool = False,
    identity_dir: Path | None = None,
    evidence_refs: list[dict] | None = None,
    next_action: str = "submit claim",
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
        "evidence_refs": (
            evidence_refs
            if evidence_refs is not None
            else [{"type": "test", "ref": "gateway-provenance"}]
        ),
        "risks": [],
        "benefits": [],
        "next_action": next_action,
    }
    if governed:
        entry["consent_ref"] = {"decision_action_hash": "uhCAk" + ("a" * 32)}
    packet, path = provenance.create_packet(
        [entry],
        identity_dir=identity_dir or workspace_root / ".floss_agent" / "identity",
        output_root=output_root,
    )
    return {
        "type": "provenance_packet",
        "ref": str(path.relative_to(workspace_root).as_posix()),
        "sha256": provenance.sha256_file(path),
    }, packet


def _submit_governed(gateway: GatewayTools, evidence: dict) -> dict:
    return json.loads(
        gateway.submit_claim(
            proposer="claude",
            proposal_type="SpecChange",
            summary="system spec",
            body="body",
            blast_radius="System",
            evidence=[evidence],
        )
    )


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


def test_gateway_accepts_packet_beneath_explicit_provenance_root(tmp_path):
    assert "provenance_root" in inspect.signature(GatewayTools).parameters

    with tempfile.TemporaryDirectory() as tmp:
        provenance_root = tmp_path / "local-agent" / "provenance"
        evidence, _packet = _packet_evidence(
            tmp_path,
            provenance_root / "nested-agent-domain",
            governed=True,
            identity_dir=tmp_path / "nested-agent-identity",
        )
        gateway = make_gateway(
            tmp,
            tmp_path,
            provenance_root=provenance_root,
        )

        result = _submit_governed(gateway, evidence)

    assert "claim_id" in result


@pytest.mark.parametrize("ref_style", ["prefix-collision", "traversal", "absolute"])
def test_gateway_rejects_top_level_packet_outside_default_root(tmp_path, ref_style):
    with tempfile.TemporaryDirectory() as tmp:
        outside_root = tmp_path / ".agent-surface" / "provenance-evil"
        evidence, _packet = _packet_evidence(
            tmp_path,
            outside_root,
            governed=True,
            identity_dir=tmp_path / f"identity-{ref_style}",
        )
        packet_path = tmp_path / evidence["ref"]
        if ref_style == "absolute":
            evidence["ref"] = str(packet_path.resolve())
        elif ref_style == "traversal":
            suffix = packet_path.relative_to(outside_root)
            evidence["ref"] = (
                Path(".agent-surface/provenance") / ".." / "provenance-evil" / suffix
            ).as_posix()

        result = _submit_governed(make_gateway(tmp, tmp_path), evidence)

    assert "error" in result
    assert "E_PROVENANCE_PACKET_OUTSIDE_ROOT" in result["error"]


def test_gateway_rejects_symlink_escape_from_default_root(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        outside_root = tmp_path / "outside-provenance"
        evidence, _packet = _packet_evidence(
            tmp_path,
            outside_root,
            governed=True,
            identity_dir=tmp_path / "symlink-identity",
        )
        packet_path = tmp_path / evidence["ref"]
        link = tmp_path / ".agent-surface" / "provenance" / "linked"
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(outside_root, target_is_directory=True)
        except (NotImplementedError, OSError) as exc:
            pytest.skip(f"directory symlinks unavailable: {exc}")
        evidence["ref"] = (
            (link / packet_path.relative_to(outside_root))
            .relative_to(tmp_path)
            .as_posix()
        )

        result = _submit_governed(make_gateway(tmp, tmp_path), evidence)

    assert "error" in result
    assert "E_PROVENANCE_PACKET_OUTSIDE_ROOT" in result["error"]


def test_gateway_rejects_nested_packet_outside_default_root(tmp_path):
    with tempfile.TemporaryDirectory() as tmp:
        child_evidence, _child = _packet_evidence(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance-evil",
            identity_dir=tmp_path / "child-identity",
        )
        root_evidence, _root = _packet_evidence(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
            governed=True,
            identity_dir=tmp_path / "root-identity",
            evidence_refs=[child_evidence],
        )

        result = _submit_governed(make_gateway(tmp, tmp_path), root_evidence)

    assert "error" in result
    assert "E_PROVENANCE_PACKET_OUTSIDE_ROOT" in result["error"]


def test_one_gateway_cannot_accept_same_position_histories_from_split_roots(
    tmp_path,
):
    with tempfile.TemporaryDirectory() as tmp:
        identity_a = tmp_path / "identity-a"
        provenance.load_or_create_identity(identity_a)
        identity_b = tmp_path / "identity-b"
        identity_b.mkdir(parents=True)
        for name in ("private.key", "public.key", "aid"):
            shutil.copy2(identity_a / name, identity_b / name)

        first_evidence, first = _packet_evidence(
            tmp_path,
            tmp_path / ".agent-surface" / "provenance",
            governed=True,
            identity_dir=identity_a,
            next_action="first history",
        )
        second_evidence, second = _packet_evidence(
            tmp_path,
            tmp_path / "temporary" / "provenance",
            governed=True,
            identity_dir=identity_b,
            next_action="second history",
        )
        assert (first["i"], first["p"], first["s"]) == (
            second["i"],
            second["p"],
            second["s"],
        )
        assert first["d"] != second["d"]

        gateway = make_gateway(tmp, tmp_path)
        accepted = _submit_governed(gateway, first_evidence)
        rejected = _submit_governed(gateway, second_evidence)

    assert "claim_id" in accepted
    assert "error" in rejected
    assert "E_PROVENANCE_PACKET_OUTSIDE_ROOT" in rejected["error"]
