"""The anchor must catch what per-chain sequence gaps cannot.

`provenance.py` enumerates INTERIOR deletion by exact sequence number. It cannot
see head truncation (the chain just ends sooner) and it cannot see a
single-packet identity being wiped (nothing survives to be gapped against). On
the live store 96 of 99 identities are single-packet, so the existing mechanism
covers about 3% of identities and zero head truncations.

These tests are written around that boundary: each one names the attack, and the
status assertions distinguish loss from growth, because an anchor that cried
wolf on every honest session would be turned off within a week.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import anchor as anchor_lib  # noqa: E402
from packages.activity_log.provenance import load_or_create_identity  # noqa: E402


def _packet(identity: str, sequence: int, said: str) -> dict:
    return {"t": "prov", "i": identity, "s": str(sequence), "d": said}


def _write(root: Path, subdir: str, name: str, packet: dict) -> Path:
    target = root / subdir
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{name}.json"
    path.write_text(json.dumps(packet), encoding="utf-8")
    return path


@pytest.fixture
def store(tmp_path):
    """Two chains: one four-deep, one single-packet. Both shapes matter."""
    root = tmp_path / "provenance"
    long_aid = "D" + "a" * 43
    solo_aid = "D" + "b" * 43
    for n in range(4):
        _write(root, "2026-08-01", f"long{n}", _packet(long_aid, n, f"E{'l' * 42}{n}"))
    _write(root, "2026-08-02", "solo", _packet(solo_aid, 0, "E" + "s" * 43))
    return root


@pytest.fixture
def identity(tmp_path):
    return load_or_create_identity(tmp_path / "identity")


@pytest.fixture
def anchored(store, identity):
    return anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)


def _status(store, anchored, **kw):
    return anchor_lib.verify_anchor(store, anchored, **kw)


# ---------------------------------------------------------------------------
# The two attacks sequence gaps cannot see.
# ---------------------------------------------------------------------------


def test_head_truncation_is_detected(store, anchored):
    """Delete the top of a chain. No gap is created; the chain just ends."""
    (store / "2026-08-01" / "long3.json").unlink()

    result = _status(store, anchored)
    assert result["status"] == anchor_lib.TRUNCATION_DETECTED
    assert result["findings"]["head_regressions"] == [
        {"aid": "D" + "a" * 43, "anchored_max_seq": 3, "current_max_seq": 2}
    ]
    assert len(result["findings"]["missing_anchored_heads"]) == 1
    assert result["findings"]["packet_delta"] == -1


def test_wiping_a_single_packet_identity_is_detected(store, anchored):
    """96 of 99 live identities are this shape. Nothing survives to be gapped."""
    (store / "2026-08-02" / "solo.json").unlink()

    result = _status(store, anchored)
    assert result["status"] == anchor_lib.TRUNCATION_DETECTED
    assert result["findings"]["vanished_identities"] == ["D" + "b" * 43]


def test_removing_a_head_while_adding_a_packet_is_still_truncation(store, anchored):
    """Equal counts must not launder a loss.

    Deleting one head and adding one unrelated packet leaves packet_delta at 0,
    so any check that compared counts would report nothing.
    """
    (store / "2026-08-01" / "long3.json").unlink()
    _write(store, "2026-08-03", "new", _packet("D" + "c" * 43, 0, "E" + "n" * 43))

    result = _status(store, anchored)
    assert result["status"] == anchor_lib.TRUNCATION_DETECTED
    assert result["findings"]["packet_delta"] == 0


# ---------------------------------------------------------------------------
# Loss must be loud; growth must not be.
# ---------------------------------------------------------------------------


def test_growth_alone_is_stale_not_truncation(store, anchored):
    """The common case between runs. Crying wolf here gets the gate turned off."""
    _write(store, "2026-08-03", "new", _packet("D" + "c" * 43, 0, "E" + "n" * 43))

    result = _status(store, anchored)
    assert result["status"] == anchor_lib.ANCHOR_STALE
    assert result["findings"]["packet_delta"] == 1
    assert result["findings"]["vanished_identities"] == []


def test_stale_is_not_a_pass(store, anchored):
    """A stale anchor is a distinct outcome from a verified one, at the exit code."""
    _write(store, "2026-08-03", "new", _packet("D" + "c" * 43, 0, "E" + "n" * 43))

    result = _status(store, anchored)
    assert anchor_lib.EXIT_CODES[result["status"]] != 0
    assert anchor_lib.EXIT_CODES[result["status"]] != anchor_lib.EXIT_CODES[
        anchor_lib.TRUNCATION_DETECTED
    ]


def test_an_unchanged_store_verifies(store, anchored):
    assert _status(store, anchored)["status"] == anchor_lib.VERIFIED


def test_interior_deletion_is_reported_without_claiming_truncation(store, anchored):
    """Sequence gaps already own this case; do not overstate what we detected."""
    (store / "2026-08-01" / "long1.json").unlink()

    result = _status(store, anchored)
    assert result["status"] == anchor_lib.ANCHOR_MISMATCH
    assert result["findings"]["head_regressions"] == []
    assert result["findings"]["missing_anchored_heads"] == []


# ---------------------------------------------------------------------------
# An unauthenticated anchor is no anchor.
# ---------------------------------------------------------------------------


def test_a_tampered_anchor_is_unavailable_not_a_mismatch(store, anchored):
    """Editing the anchor must not look like the STORE changed."""
    tampered = dict(anchored)
    tampered["packet_count"] = 1

    result = _status(store, tampered)
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert result["note"] == anchor_lib.UNAVAILABLE_NOTE


def test_a_missing_anchor_is_never_a_pass(store):
    result = anchor_lib.verify_anchor(store, None)
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert anchor_lib.EXIT_CODES[result["status"]] == 3
    assert "NOT a pass" in result["note"]


def test_an_unsigned_anchor_is_rejected(store, identity):
    unsigned = anchor_lib.build_anchor(store)
    assert _status(store, unsigned)["status"] == anchor_lib.ANCHOR_UNAVAILABLE


def test_a_pinned_signer_must_match(store, anchored):
    """Pinning is the real root of trust; a fresh key can sign a fresh series."""
    result = _status(store, anchored, expected_signer="D" + "z" * 43)
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert "was pinned" in result["reason"]

    assert (
        _status(store, anchored, expected_signer=anchored["signer"])["status"]
        == anchor_lib.VERIFIED
    )


def test_the_signature_covers_the_identity_summaries(store, anchored):
    """Not just the root: the per-identity heads are the truncation evidence."""
    tampered = json.loads(json.dumps(anchored))
    tampered["identities"][0]["max_seq"] = 0

    assert anchor_lib.anchor_signature_problem(tampered) is not None


# ---------------------------------------------------------------------------
# Set-commitment properties.
# ---------------------------------------------------------------------------


def test_the_root_is_independent_of_enumeration_order(store, identity):
    """Two verifiers reading the same packets must derive the same root."""
    leaves, _ = anchor_lib.scan_packets(store)
    forward = anchor_lib._root_of(leaves)
    backward = anchor_lib._root_of(list(reversed(leaves)))
    assert forward != backward, (
        "sanity: _root_of is order-sensitive, which is why scan_packets sorts"
    )
    again, _ = anchor_lib.scan_packets(store)
    assert anchor_lib._root_of(again) == forward


def test_a_packet_moved_to_the_root_stays_in_the_set(store, anchored):
    """A fixed `*/*.json` glob would have dropped it silently.

    That would hand an attacker a way to shrink the commitment without deleting
    anything, so scan_packets uses rglob and the moved packet must still count.
    """
    moved = store / "2026-08-01" / "long3.json"
    moved.rename(store / "long3.json")

    assert _status(store, anchored)["status"] == anchor_lib.VERIFIED


def test_a_leaf_binds_position_not_just_the_digest():
    """An inclusion proof must say WHERE a packet sat, not merely that it existed."""
    base = anchor_lib.leaf_preimage("D" + "a" * 43, 3, "E" + "x" * 43)
    assert base != anchor_lib.leaf_preimage("D" + "a" * 43, 4, "E" + "x" * 43)
    assert base != anchor_lib.leaf_preimage("D" + "b" * 43, 3, "E" + "x" * 43)
    assert base == anchor_lib.leaf_preimage("D" + "a" * 43, "3", "E" + "x" * 43)


def test_leaf_and_interior_hashes_are_domain_separated():
    """Without separation an interior node can be presented as a leaf."""
    assert anchor_lib.LEAF_TAG != anchor_lib.NODE_TAG
    one = anchor_lib.merkle_root([b"a"])
    two = anchor_lib.merkle_root([b"a", b"b"])
    assert one != two
    assert anchor_lib.merkle_root([]) != one


def test_the_empty_tree_has_its_own_root():
    """"No packets" must never be confusable with a real commitment."""
    assert anchor_lib.merkle_root([]) == "E" + "0" * 43


def test_an_odd_leaf_count_is_promoted_not_duplicated(store, identity):
    """Duplicating the last node instead of promoting it enables a forgery."""
    three = anchor_lib.merkle_root([b"a", b"b", b"c"])
    four = anchor_lib.merkle_root([b"a", b"b", b"c", b"c"])
    assert three != four


# ---------------------------------------------------------------------------
# Damage is frozen, not hidden.
# ---------------------------------------------------------------------------


def test_known_gaps_and_duplicates_are_recorded_in_the_anchor(tmp_path, identity):
    """So later damage cannot be laundered as pre-existing."""
    root = tmp_path / "provenance"
    aid = "D" + "a" * 43
    for n in (0, 1, 3):
        _write(root, "2026-08-01", f"p{n}", _packet(aid, n, f"E{'p' * 42}{n}"))
    _write(root, "2026-08-01", "dupe", _packet(aid, 1, "E" + "q" * 43))

    summary = anchor_lib.build_anchor(root)["identities"][0]
    assert summary["interior_gaps"] == [2]
    assert summary["duplicate_seqs"] == [1]
    assert summary["max_seq"] == 3
    assert summary["count"] == 4


def test_two_occupants_of_a_head_slot_are_both_recorded(tmp_path):
    """The live store already has slots with two occupants."""
    root = tmp_path / "provenance"
    aid = "D" + "a" * 43
    _write(root, "2026-08-01", "one", _packet(aid, 0, "E" + "1" * 43))
    _write(root, "2026-08-01", "two", _packet(aid, 0, "E" + "2" * 43))

    heads = anchor_lib.build_anchor(root)["identities"][0]["head_saids"]
    assert len(heads) == 2, "flattening a fork would anchor it as a single head"


# ---------------------------------------------------------------------------
# Malformed input must neither wedge the run nor vanish.
# ---------------------------------------------------------------------------


def test_a_malformed_packet_is_named_not_skipped(store):
    (store / "2026-08-01" / "broken.json").write_text("{not json", encoding="utf-8")

    _leaves, unreadable = anchor_lib.scan_packets(store)
    assert [entry["path"] for entry in unreadable] == ["2026-08-01/broken.json"]


def test_a_packet_with_a_non_integer_sequence_is_named(store):
    _write(store, "2026-08-01", "weird", {"t": "prov", "i": "D", "s": "x", "d": "E"})

    _leaves, unreadable = anchor_lib.scan_packets(store)
    assert any("non-integer sequence" in entry["error"] for entry in unreadable)


def test_a_non_packet_json_file_is_ignored_silently(store, anchored):
    """Not every JSON file under the store is a packet; that is not damage."""
    (store / "2026-08-01" / "notes.json").write_text('{"t": "other"}', encoding="utf-8")

    _leaves, unreadable = anchor_lib.scan_packets(store)
    assert unreadable == []
    assert _status(store, anchored)["status"] == anchor_lib.VERIFIED


def test_a_missing_store_does_not_raise(tmp_path):
    leaves, unreadable = anchor_lib.scan_packets(tmp_path / "nope")
    assert leaves == []
    assert unreadable == []


# ---------------------------------------------------------------------------
# The anchor series is itself a chain.
# ---------------------------------------------------------------------------


def test_each_anchor_chains_to_its_predecessor(store, identity):
    first = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    _write(store, "2026-08-03", "new", _packet("D" + "c" * 43, 0, "E" + "n" * 43))
    second = anchor_lib.build_anchor(store, first)

    assert first["prev_root"] is None
    assert second["prev_root"] == first["merkle_root"]
    assert second["prev_generated_at"] == first["generated_at"]
    assert second["merkle_root"] != first["merkle_root"]
