from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FLOSS_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = FLOSS_ROOT.parent
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))


def test_self_application_genesis_packet_validates(tmp_path, monkeypatch):
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    identity_dir = tmp_path / ".floss_agent" / "identity"
    output_root = tmp_path / ".agent-surface" / "provenance"
    artifact = tmp_path / "FLOSS" / "docs" / "specs" / "provenance-packet.spec.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        "# Provenance Packet Spec\n\nGenesis handoff.\n", encoding="utf-8"
    )

    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["claude-opus-4-7", "codex-local"],
        "created_at": "2026-05-24T10:00:00Z",
        "human_collision_node": "anthony",
        "artifact_refs": [provenance.artifact_ref(artifact, workspace_root=tmp_path)],
        "evidence_refs": [{"type": "spec", "ref": "provenance-spine-v1.4"}],
        "risks": [],
        "benefits": ["validates its own genesis handoff"],
        "next_action": "begin pilot",
    }

    packet, packet_path = provenance.create_packet(
        [entry],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )

    assert packet_path.exists()
    assert packet["v"].startswith("FLOSSI10JSON")
    assert int(packet["v"][-7:-1], 16) == len(provenance.canonical_bytes(packet))
    assert packet["t"] == "prov"
    assert packet["d"].startswith("E")
    assert len(packet["d"]) == 44
    assert packet["i"].startswith("D")
    assert packet["s"] == "0"
    assert packet["p"] is None
    assert packet["sigs"][0].startswith("0B")

    result = provenance.validate_packet(packet_path, workspace_root=tmp_path)

    assert result.ok is True
    assert result.packet_digest == packet["d"]
    assert result.narrative_lines == [
        (
            "[2026-05-24T10:00:00Z] "
            f"{packet['i']} \u25c7 proposal -> "
            "FLOSS/docs/specs/provenance-packet.spec.md "
            "\u00b7 evidence: 1 refs \u00b7 governed: no \u00b7 signature: ok"
        )
    ]


def test_forged_signature_fails_validation(tmp_path, monkeypatch):
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("original", encoding="utf-8")
    packet, packet_path = provenance.create_packet(
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
                "evidence_refs": [{"type": "test", "ref": "unit"}],
                "risks": [],
                "benefits": [],
                "next_action": "none",
            }
        ],
        identity_dir=tmp_path / "identity",
        output_root=tmp_path / "packets",
    )
    packet["a"][0]["next_action"] = "tampered"
    packet_path.write_text(json.dumps(packet), encoding="utf-8")

    result = provenance.validate_packet(packet_path, workspace_root=tmp_path)

    assert result.ok is False
    assert result.errors == ["E_PROVENANCE_SIGNATURE_INVALID"]


def test_prior_digest_must_resolve_to_existing_packet(tmp_path, monkeypatch):
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("content", encoding="utf-8")
    packet, packet_path = provenance.create_packet(
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
                "evidence_refs": [{"type": "test", "ref": "unit"}],
                "risks": [],
                "benefits": [],
                "next_action": "none",
            }
        ],
        identity_dir=tmp_path / "identity",
        output_root=tmp_path / "packets",
        prior_digest="E" + ("a" * 43),
    )

    result = provenance.validate_packet(packet_path, workspace_root=tmp_path)

    assert packet["p"] == "E" + ("a" * 43)
    assert result.ok is False
    assert "E_PROVENANCE_PRIOR_NOT_FOUND" in result.errors


def test_long_linear_prior_chain_is_not_evidence_recursion(tmp_path, monkeypatch):
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("content", encoding="utf-8")
    output_root = tmp_path / "packets"
    identity_dir = tmp_path / "identity"

    packet_path = None
    for index in range(10):
        _packet, packet_path = provenance.create_packet(
            [
                {
                    "claim_type": "proposal",
                    "truth_status": "specified",
                    "source_systems": ["unit-test"],
                    "created_at": f"2026-05-24T10:{index:02d}:00Z",
                    "human_collision_node": "anthony",
                    "artifact_refs": [
                        provenance.artifact_ref(artifact, workspace_root=tmp_path)
                    ],
                    "evidence_refs": [{"type": "test", "ref": "unit"}],
                    "risks": [],
                    "benefits": [],
                    "next_action": "none",
                }
            ],
            identity_dir=identity_dir,
            output_root=output_root,
        )

    assert packet_path is not None
    result = provenance.validate_packet(packet_path, workspace_root=tmp_path)

    assert result.ok is True
    assert "E_PROVENANCE_RECURSION_DEPTH_EXCEEDED" not in result.errors


def test_concurrent_first_packet_creation_converges_on_one_identity(
    tmp_path, monkeypatch
):
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    original_generate = provenance.SigningKey.generate

    def slow_generate():
        time.sleep(0.02)
        return original_generate()

    monkeypatch.setattr(
        provenance.SigningKey, "generate", staticmethod(slow_generate)
    )

    worker_count = 12
    identity_dir = tmp_path / "identity"
    output_root = tmp_path / "packets"
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("content", encoding="utf-8")

    def packet_entry(index: int) -> dict[str, object]:
        return {
            "claim_type": "proposal",
            "truth_status": "specified",
            "source_systems": ["unit-test"],
            "created_at": f"2026-06-13T12:{index:02d}:00Z",
            "human_collision_node": "anthony",
            "artifact_refs": [
                provenance.artifact_ref(artifact, workspace_root=tmp_path)
            ],
            "evidence_refs": [{"type": "test", "ref": "identity-race"}],
            "risks": [],
            "benefits": [],
            "next_action": "none",
        }

    def create_one(index: int) -> dict[str, object]:
        packet, _packet_path = provenance.create_packet(
            [packet_entry(index)],
            identity_dir=identity_dir,
            output_root=output_root,
        )
        return packet

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        packets = list(executor.map(create_one, range(worker_count)))

    ordered = sorted(packets, key=lambda packet: int(packet["s"]))

    assert len({packet["i"] for packet in packets}) == 1
    assert sum(1 for packet in packets if packet["p"] is None) == 1
    assert [int(packet["s"]) for packet in ordered] == list(range(worker_count))
    assert ordered[0]["p"] is None
    for previous, current in zip(ordered, ordered[1:]):
        assert current["p"] == previous["d"]


def test_multi_entry_narrative_emits_one_line_per_entry(tmp_path, monkeypatch):
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    packet, _path = provenance.create_packet(
        [
            {
                "claim_type": "proposal",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:00:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(first, workspace_root=tmp_path)
                ],
                "evidence_refs": [{"type": "test", "ref": "unit"}],
                "risks": [],
                "benefits": [],
                "next_action": "first",
            },
            {
                "claim_type": "target",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-05-24T10:01:00Z",
                "human_collision_node": "anthony",
                "artifact_refs": [
                    provenance.artifact_ref(second, workspace_root=tmp_path)
                ],
                "evidence_refs": [
                    {"type": "test", "ref": "unit"},
                    {"type": "adr", "ref": "ADR-003"},
                ],
                "risks": [],
                "benefits": [],
                "next_action": "second",
                "consent_ref": {"decision_action_hash": "uhCAk" + ("a" * 32)},
            },
        ],
        identity_dir=tmp_path / "identity",
        output_root=tmp_path / "packets",
    )

    lines = provenance.narrative_lines(packet)

    assert len(lines) == 2
    assert "proposal -> first.txt" in lines[0]
    assert "governed: no" in lines[0]
    assert "target -> second.txt" in lines[1]
    assert "evidence: 2 refs" in lines[1]
    assert "governed: yes" in lines[1]


def test_dag_root_satisfied_by_valid_child_packet(tmp_path, monkeypatch):
    """Root requirement is across the DAG: a packet may delegate it to a valid child."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    out = tmp_path / ".agent-surface" / "provenance"
    # Child carries a real non-packet (test) root.
    _child, child_path = provenance.create_packet(
        [
            {
                "created_at": "2026-06-13T00:00:00Z",
                "evidence_refs": [{"type": "test", "ref": "hashline:VERIFIED"}],
            }
        ],
        identity_dir=tmp_path / "child_id",
        output_root=out,
        prior_digest=None,
    )
    rel = child_path.resolve().relative_to(tmp_path.resolve()).as_posix()
    # Parent: separate identity, genesis, references the child as its only
    # evidence (NO direct non-packet root of its own).
    _parent, parent_path = provenance.create_packet(
        [
            {
                "created_at": "2026-06-13T00:00:01Z",
                "evidence_refs": [
                    {
                        "type": "provenance_packet",
                        "ref": rel,
                        "sha256": provenance.sha256_file(child_path),
                    }
                ],
            }
        ],
        identity_dir=tmp_path / "parent_id",
        output_root=out,
        prior_digest=None,
    )
    result = provenance.validate_packet(
        parent_path, workspace_root=tmp_path, provenance_root=out
    )
    assert result.ok is True, result.errors


def test_packet_with_no_root_in_dag_is_invalid(tmp_path, monkeypatch):
    """A packet whose evidence DAG has no non-packet root is rejected."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    out = tmp_path / ".agent-surface" / "provenance"
    _packet, packet_path = provenance.create_packet(
        [{"created_at": "2026-06-13T00:00:00Z"}],  # no evidence_refs at all
        identity_dir=tmp_path / "id",
        output_root=out,
        prior_digest=None,
    )
    result = provenance.validate_packet(
        packet_path, workspace_root=tmp_path, provenance_root=out
    )
    assert result.ok is False
    assert "E_PROVENANCE_ROOT_REQUIRED" in result.errors


def test_discontinuous_prior_sequence_is_rejected(tmp_path, monkeypatch):
    """A packet whose prior sequence does not directly precede it is invalid."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    out = tmp_path / ".agent-surface" / "provenance"
    idd = tmp_path / "id"
    root_ref = [{"type": "test", "ref": "x"}]
    c0, _ = provenance.create_packet(
        [{"created_at": "2026-06-13T00:00:00Z", "evidence_refs": root_ref}],
        identity_dir=idd,
        output_root=out,
    )
    provenance.create_packet(  # s=1, p=c0
        [{"created_at": "2026-06-13T00:00:01Z", "evidence_refs": root_ref}],
        identity_dir=idd,
        output_root=out,
    )
    # c2 is forced to point back at the genesis (s=0) while its own s=2.
    _c2, c2_path = provenance.create_packet(
        [{"created_at": "2026-06-13T00:00:02Z", "evidence_refs": root_ref}],
        identity_dir=idd,
        output_root=out,
        prior_digest=c0["d"],
    )
    result = provenance.validate_packet(
        c2_path, workspace_root=tmp_path, provenance_root=out
    )
    assert result.ok is False
    assert "E_PROVENANCE_SEQUENCE_DISCONTINUOUS" in result.errors
