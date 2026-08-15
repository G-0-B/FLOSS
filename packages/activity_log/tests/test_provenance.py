from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = FLOSS_ROOT.parent
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))


def _resign_packet(packet, *, identity_dir: Path) -> bytes:
    from packages.activity_log import provenance

    identity = provenance.load_or_create_identity(identity_dir)
    packet["d"] = provenance._said_digest(packet)
    packet["sigs"] = [provenance.SIGNATURE_PLACEHOLDER]
    packet["v"] = provenance._version_with_size(packet)
    packet["sigs"] = []
    packet["d"] = provenance._said_digest(packet)
    signature = identity.signing_key.sign(provenance._signing_bytes(packet)).signature
    packet["sigs"] = ["0B" + provenance._b64url_encode(signature)]
    return provenance.canonical_bytes(packet) + b"\n"


def test_payload_entry_rejects_sha256_with_trailing_newline():
    from packages.activity_log import provenance

    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-11T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [{"path": "artifact.txt", "sha256": "a" * 64 + "\n"}],
        "evidence_refs": [{"type": "test", "ref": "unit"}],
        "risks": [],
        "benefits": [],
        "next_action": "none",
    }

    assert provenance._payload_entry_errors([entry]) == [
        "E_PROVENANCE_ARTIFACT_REF_INVALID"
    ]


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

    monkeypatch.setattr(provenance.SigningKey, "generate", staticmethod(slow_generate))

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

    def _entry(**overrides):
        base = {
            "claim_type": "proposal",
            "truth_status": "specified",
            "source_systems": ["unit-test"],
            "created_at": "2026-06-13T00:00:00Z",
            "human_collision_node": "unit-test",
            "artifact_refs": [],
            "evidence_refs": [],
            "risks": [],
            "benefits": [],
            "next_action": "noop",
        }
        base.update(overrides)
        return base

    # Child carries a real non-packet (test) root.
    _child, child_path = provenance.create_packet(
        [_entry(evidence_refs=[{"type": "test", "ref": "hashline:VERIFIED"}])],
        identity_dir=tmp_path / "child_id",
        output_root=out,
        prior_digest=None,
    )
    rel = child_path.resolve().relative_to(tmp_path.resolve()).as_posix()
    # Parent: separate identity, genesis, references the child as its only
    # evidence (NO direct non-packet root of its own).
    _parent, parent_path = provenance.create_packet(
        [
            _entry(
                created_at="2026-06-13T00:00:01Z",
                evidence_refs=[
                    {
                        "type": "provenance_packet",
                        "ref": rel,
                        "sha256": provenance.sha256_file(child_path),
                    }
                ],
            )
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


def test_zero_padded_signed_successor_sequence_is_rejected(tmp_path, monkeypatch):
    """A signed successor cannot alias canonical sequence 1 as string 01."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "identity"
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-15T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [],
        "evidence_refs": [{"type": "test", "ref": "unit"}],
        "risks": [],
        "benefits": [],
        "next_action": "prior",
    }
    provenance.create_packet(
        [entry],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    successor, successor_path = provenance.create_packet(
        [{**entry, "created_at": "2026-08-15T00:00:01Z", "next_action": "next"}],
        identity_dir=identity_dir,
        output_root=output_root,
    )
    assert successor["s"] == "1"
    successor["s"] = "01"
    successor_path.write_bytes(_resign_packet(successor, identity_dir=identity_dir))

    result = provenance.validate_packet(
        successor_path,
        workspace_root=tmp_path,
        provenance_root=output_root,
    )

    assert result.ok is False
    assert result.errors == ["E_PROVENANCE_SEQUENCE_INVALID"]


@pytest.mark.parametrize("sequence", ["0", "1", "10", "99999999999999999999"])
def test_canonical_decimal_sequence_forms_are_accepted(sequence):
    from packages.activity_log import provenance

    assert provenance._SEQUENCE_RE.fullmatch(sequence) is not None


def test_same_agent_same_prior_and_sequence_fork_is_rejected(tmp_path, monkeypatch):
    """Two valid signed successors at one chain position are both rejected."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "id"
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-11T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [],
        "evidence_refs": [{"type": "test", "ref": "unit"}],
        "risks": [],
        "benefits": [],
        "next_action": "prior",
    }
    prior, _prior_path = provenance.create_packet(
        [entry],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    first, first_path = provenance.create_packet(
        [{**entry, "created_at": "2026-08-11T00:00:01Z", "next_action": "first"}],
        identity_dir=identity_dir,
        output_root=output_root,
    )
    second = json.loads(json.dumps(first))
    second["a"][0]["next_action"] = "second"
    second_bytes = _resign_packet(second, identity_dir=identity_dir)
    second_path = first_path.with_name(f"{second['d']}.json")
    second_path.write_bytes(second_bytes)

    assert first["i"] == second["i"] == prior["i"]
    assert first["p"] == second["p"] == prior["d"]
    assert first["s"] == second["s"] == "1"
    assert first["d"] != second["d"]

    results = [
        provenance.validate_packet(
            path, workspace_root=tmp_path, provenance_root=output_root
        )
        for path in (first_path, second_path)
    ]

    assert [(result.ok, result.errors) for result in results] == [
        (False, ["E_PROVENANCE_CHAIN_FORK"]),
        (False, ["E_PROVENANCE_CHAIN_FORK"]),
    ]


def test_same_position_fork_rejects_sibling_that_cites_other_as_evidence(
    tmp_path, monkeypatch
):
    """Sibling evidence cannot make one side of a valid fork pass."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "id"
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-11T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [],
        "evidence_refs": [{"type": "test", "ref": "unit"}],
        "risks": [],
        "benefits": [],
        "next_action": "prior",
    }
    prior, _prior_path = provenance.create_packet(
        [entry],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    first, first_path = provenance.create_packet(
        [{**entry, "created_at": "2026-08-11T00:00:01Z", "next_action": "first"}],
        identity_dir=identity_dir,
        output_root=output_root,
    )
    second = json.loads(json.dumps(first))
    second["a"][0]["next_action"] = "second"
    first_ref = first_path.resolve().relative_to(tmp_path.resolve()).as_posix()
    second["a"][0]["evidence_refs"].append(
        {
            "type": "provenance_packet",
            "ref": first_ref,
            "sha256": provenance.sha256_file(first_path),
        }
    )
    second_bytes = _resign_packet(second, identity_dir=identity_dir)
    second_path = first_path.with_name(f"{second['d']}.json")
    second_path.write_bytes(second_bytes)

    assert first["i"] == second["i"] == prior["i"]
    assert first["p"] == second["p"] == prior["d"]
    assert first["s"] == second["s"] == "1"
    assert first["d"] != second["d"]

    results = [
        provenance.validate_packet(
            path, workspace_root=tmp_path, provenance_root=output_root
        )
        for path in (first_path, second_path)
    ]

    assert [(result.ok, result.errors) for result in results] == [
        (False, ["E_PROVENANCE_CHAIN_FORK"]),
        (False, ["E_PROVENANCE_CHAIN_FORK"]),
    ]


def test_public_eight_wrapper_root_uses_independent_competitor_depth(
    tmp_path, monkeypatch
):
    """A deep caller cannot spend an independently valid competitor's budget."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "fork-id"

    def entry(created_at, next_action, evidence_refs):
        return {
            "claim_type": "proposal",
            "truth_status": "specified",
            "source_systems": ["unit-test"],
            "created_at": created_at,
            "human_collision_node": "unit-test",
            "artifact_refs": [],
            "evidence_refs": evidence_refs,
            "risks": [],
            "benefits": [],
            "next_action": next_action,
        }

    direct_root = [{"type": "test", "ref": "unit"}]
    _child, child_path = provenance.create_packet(
        [entry("2026-08-11T00:00:00Z", "child", direct_root)],
        identity_dir=tmp_path / "child-id",
        output_root=output_root,
        prior_digest=None,
    )
    provenance.create_packet(
        [entry("2026-08-11T00:00:01Z", "prior", direct_root)],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    first, first_path = provenance.create_packet(
        [entry("2026-08-11T00:00:02Z", "first", direct_root)],
        identity_dir=identity_dir,
        output_root=output_root,
    )
    second = json.loads(json.dumps(first))
    second["a"][0]["next_action"] = "second"
    child_ref = child_path.resolve().relative_to(tmp_path.resolve()).as_posix()
    second["a"][0]["evidence_refs"].append(
        {
            "type": "provenance_packet",
            "ref": child_ref,
            "sha256": provenance.sha256_file(child_path),
        }
    )
    second_bytes = _resign_packet(second, identity_dir=identity_dir)
    second_path = first_path.with_name(f"{second['d']}.json")
    second_path.write_bytes(second_bytes)
    chain_position = (first["i"], first["p"], first["s"])

    wrapped_path = first_path
    for index in range(8):
        wrapped_ref = (
            wrapped_path.resolve().relative_to(tmp_path.resolve()).as_posix()
        )
        _wrapper, wrapped_path = provenance.create_packet(
            [
                entry(
                    f"2026-08-11T00:01:{index:02d}Z",
                    f"wrapper-{index}",
                    [
                        {
                            "type": "provenance_packet",
                            "ref": wrapped_ref,
                            "sha256": provenance.sha256_file(wrapped_path),
                        }
                    ],
                )
            ],
            identity_dir=tmp_path / f"wrapper-{index}-id",
            output_root=output_root,
            prior_digest=None,
        )

    top_level = [
        provenance.validate_packet(
            path, workspace_root=tmp_path, provenance_root=output_root
        )
        for path in (first_path, second_path)
    ]
    competitor_depth0 = provenance.validate_packet(
        second_path,
        workspace_root=tmp_path,
        provenance_root=output_root,
        _ignored_chain_position=chain_position,
    )
    competitor_depth8 = provenance.validate_packet(
        second_path,
        workspace_root=tmp_path,
        provenance_root=output_root,
        _depth=8,
        _ignored_chain_position=chain_position,
    )
    wrapper_root = provenance.validate_packet(
        wrapped_path, workspace_root=tmp_path, provenance_root=output_root
    )

    observed = {
        "top_level": [(result.ok, result.errors) for result in top_level],
        "competitor_depth0": (competitor_depth0.ok, competitor_depth0.errors),
        "competitor_depth8": (competitor_depth8.ok, competitor_depth8.errors),
        "wrapper_root": (wrapper_root.ok, wrapper_root.errors),
    }
    assert observed == {
        "top_level": [
            (False, ["E_PROVENANCE_CHAIN_FORK"]),
            (False, ["E_PROVENANCE_CHAIN_FORK"]),
        ],
        "competitor_depth0": (True, []),
        "competitor_depth8": (
            False,
            ["E_PROVENANCE_RECURSION_DEPTH_EXCEEDED"],
        ),
        "wrapper_root": (
            False,
            ["E_PROVENANCE_CHAIN_FORK", "E_PROVENANCE_ROOT_REQUIRED"],
        ),
    }, observed


@pytest.mark.parametrize(
    "sibling_kind",
    [
        "unreadable",
        "malformed",
        "forged",
        "bad-digest",
        "discontinuous",
        "invalid-payload",
    ],
)
def test_invalid_same_position_sibling_does_not_poison_valid_packet(
    tmp_path, monkeypatch, sibling_kind
):
    """A file drop is not a fork unless the sibling independently validates."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "id"
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-11T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [],
        "evidence_refs": [{"type": "test", "ref": "unit"}],
        "risks": [],
        "benefits": [],
        "next_action": "prior",
    }
    prior, _prior_path = provenance.create_packet(
        [entry],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    valid, valid_path = provenance.create_packet(
        [{**entry, "created_at": "2026-08-11T00:00:01Z", "next_action": "valid"}],
        identity_dir=identity_dir,
        output_root=output_root,
    )
    sibling_path = valid_path.with_name(f"000-{sibling_kind}.json")

    if sibling_kind == "unreadable":
        sibling_path.write_text("{", encoding="utf-8")
    elif sibling_kind == "malformed":
        sibling_path.write_text(
            json.dumps({"i": valid["i"], "p": prior["d"], "s": "1"}),
            encoding="utf-8",
        )
    elif sibling_kind == "forged":
        sibling = json.loads(json.dumps(valid))
        sibling["a"][0]["next_action"] = "forged"
        sibling["d"] = "E" + ("f" * 43)
        sibling_path.write_bytes(provenance.canonical_bytes(sibling) + b"\n")
    else:
        sibling = json.loads(json.dumps(valid))
        sibling["a"][0]["next_action"] = sibling_kind
        if sibling_kind == "bad-digest":
            _resign_packet(sibling, identity_dir=identity_dir)
            sibling["d"] = "E" + ("b" * 43)
            identity = provenance.load_or_create_identity(identity_dir)
            sibling["sigs"] = []
            signature = identity.signing_key.sign(
                provenance._signing_bytes(sibling)
            ).signature
            sibling["sigs"] = ["0B" + provenance._b64url_encode(signature)]
            sibling_bytes = provenance.canonical_bytes(sibling) + b"\n"
        else:
            if sibling_kind == "discontinuous":
                sibling["s"] = "3"
            else:
                del sibling["a"][0]["claim_type"]
            sibling_bytes = _resign_packet(sibling, identity_dir=identity_dir)
        sibling_path = valid_path.with_name(f"{sibling['d']}.json")
        sibling_path.write_bytes(sibling_bytes)

    result = provenance.validate_packet(
        valid_path, workspace_root=tmp_path, provenance_root=output_root
    )
    sibling_result = provenance.validate_packet(
        sibling_path, workspace_root=tmp_path, provenance_root=output_root
    )

    assert result.ok is True, result.errors
    assert sibling_result.ok is False


def test_duplicate_copy_of_exact_digest_is_not_a_fork(tmp_path, monkeypatch):
    """The same signed packet at a second path remains duplicate evidence."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "id"
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-08-11T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [],
        "evidence_refs": [{"type": "test", "ref": "unit"}],
        "risks": [],
        "benefits": [],
        "next_action": "prior",
    }
    provenance.create_packet(
        [entry],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    _packet, packet_path = provenance.create_packet(
        [{**entry, "created_at": "2026-08-11T00:00:01Z", "next_action": "valid"}],
        identity_dir=identity_dir,
        output_root=output_root,
    )
    duplicate_path = output_root / "duplicate" / packet_path.name
    duplicate_path.parent.mkdir()
    duplicate_path.write_bytes(packet_path.read_bytes())

    results = [
        provenance.validate_packet(
            path, workspace_root=tmp_path, provenance_root=output_root
        )
        for path in (packet_path, duplicate_path)
    ]

    assert [(result.ok, result.errors) for result in results] == [
        (True, []),
        (True, []),
    ]


@pytest.mark.parametrize(
    ("sequence", "expected_error"),
    [
        ("4", "E_PROVENANCE_SEQUENCE_DISCONTINUOUS"),
        ("not-decimal", "E_PROVENANCE_SEQUENCE_INVALID"),
    ],
)
def test_genesis_packet_requires_zero_decimal_sequence(
    tmp_path, monkeypatch, sequence, expected_error
):
    """A signed packet with no prior must be canonical genesis sequence zero."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    output_root = tmp_path / ".agent-surface" / "provenance"
    identity_dir = tmp_path / "id"
    packet, packet_path = provenance.create_packet(
        [
            {
                "claim_type": "proposal",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-08-11T00:00:00Z",
                "human_collision_node": "unit-test",
                "artifact_refs": [],
                "evidence_refs": [{"type": "test", "ref": "unit"}],
                "risks": [],
                "benefits": [],
                "next_action": "none",
            }
        ],
        identity_dir=identity_dir,
        output_root=output_root,
        prior_digest=None,
    )
    packet["s"] = sequence
    packet_path.write_bytes(_resign_packet(packet, identity_dir=identity_dir))

    result = provenance.validate_packet(
        packet_path, workspace_root=tmp_path, provenance_root=output_root
    )

    assert result.ok is False
    assert expected_error in result.errors


def test_payload_entry_missing_required_field_is_invalid(tmp_path, monkeypatch):
    """A packet whose entry omits required v1.4 fields is invalid even with consent + a root.

    Guards the governed hard block: validate_packet().ok must not pass for a
    malformed entry that carries only consent_ref + a non-packet evidence root.
    """
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    out = tmp_path / ".agent-surface" / "provenance"
    _p, path = provenance.create_packet(
        [
            {
                # claim_type / truth_status / source_systems / next_action /
                # risks / benefits all omitted on purpose.
                "created_at": "2026-06-13T00:00:00Z",
                "consent_ref": {"decision_action_hash": "uhCAk" + ("a" * 32)},
                "evidence_refs": [{"type": "test", "ref": "x"}],
            }
        ],
        identity_dir=tmp_path / "id",
        output_root=out,
        prior_digest=None,
    )
    result = provenance.validate_packet(
        path, workspace_root=tmp_path, provenance_root=out
    )
    assert result.ok is False
    assert any(e.startswith("E_PROVENANCE_ENTRY_FIELD_MISSING") for e in result.errors)


def test_payload_entry_malformed_artifact_ref_is_invalid(tmp_path, monkeypatch):
    """An entry with all required fields present but a malformed artifact_ref is invalid."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    out = tmp_path / ".agent-surface" / "provenance"
    _p, path = provenance.create_packet(
        [
            {
                "claim_type": "proposal",
                "truth_status": "specified",
                "source_systems": ["unit-test"],
                "created_at": "2026-06-13T00:00:00Z",
                "human_collision_node": "unit-test",
                # Bad sha256 (not 64-hex) — must be rejected.
                "artifact_refs": [{"path": "FLOSS/x.md", "sha256": "deadbeef"}],
                "evidence_refs": [{"type": "test", "ref": "x"}],
                "risks": [],
                "benefits": [],
                "next_action": "noop",
            }
        ],
        identity_dir=tmp_path / "id",
        output_root=out,
        prior_digest=None,
    )
    result = provenance.validate_packet(
        path, workspace_root=tmp_path, provenance_root=out
    )
    assert result.ok is False
    assert "E_PROVENANCE_ARTIFACT_REF_INVALID" in result.errors


@pytest.mark.parametrize(
    ("field_name", "expected_error"),
    [
        ("artifact_refs", "E_PROVENANCE_ENTRY_FIELD_MISSING:artifact_refs"),
        ("evidence_refs", "E_PROVENANCE_ENTRY_FIELD_MISSING:evidence_refs"),
    ],
)
def test_signed_packet_with_non_list_reference_field_returns_structured_invalid(
    tmp_path, monkeypatch, field_name, expected_error
):
    """A signed malformed list field is invalid without escaping as TypeError."""
    from packages.activity_log import provenance

    monkeypatch.setattr(provenance, "WORKSPACE_ROOT", tmp_path)
    out = tmp_path / ".agent-surface" / "provenance"
    entry = {
        "claim_type": "proposal",
        "truth_status": "specified",
        "source_systems": ["unit-test"],
        "created_at": "2026-06-13T00:00:00Z",
        "human_collision_node": "unit-test",
        "artifact_refs": [],
        "evidence_refs": [{"type": "test", "ref": "x"}],
        "risks": [],
        "benefits": [],
        "next_action": "noop",
    }
    entry[field_name] = 1
    _packet, path = provenance.create_packet(
        [entry],
        identity_dir=tmp_path / "id",
        output_root=out,
        prior_digest=None,
    )

    result = provenance.validate_packet(
        path, workspace_root=tmp_path, provenance_root=out
    )

    assert result.ok is False
    assert expected_error in result.errors
