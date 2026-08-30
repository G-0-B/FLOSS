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
from packages.activity_log import provenance  # noqa: E402
from packages.activity_log.provenance import load_or_create_identity  # noqa: E402


def _packet(identity: str, sequence: int, said: str = "") -> dict:
    """A packet whose SAID is actually SATISFIED, not merely claimed.

    These fixtures used to assert an arbitrary `d`. That worked only because
    scan_packets trusted the header, which is the defect a reviewer found: a
    129-byte header-only stub reproduced the leaf of a 585-byte signed packet.
    Now that the SAID is recomputed, a fixture with a made-up digest is
    correctly treated as unreadable — so the fixtures have to be real.

    The `said` argument is retained and ignored so call sites keep reading as
    "this packet, at this position"; the digest is derived from the content.
    """

    packet = {
        "v": provenance.VERSION_PLACEHOLDER,
        "t": "prov",
        "d": provenance.SAID_PLACEHOLDER,
        "i": identity,
        "s": str(sequence),
        "p": None,
        "a": [{"note": said or f"{identity}:{sequence}"}],
        "sigs": [],
    }
    packet["d"] = provenance._said_digest(packet)
    return packet


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


# ---------------------------------------------------------------------------
# Review findings from docs/reviews/2026-08-29-model-identity-anomoly.
# Each test names the group and the number of reviewers that raised it.
# ---------------------------------------------------------------------------


def test_g1_the_signature_binds_the_claimed_signer(store, identity):
    """G1, 4 reviewers. `signer` was outside the signed bytes.

    With the identity excluded from the pre-image, any valid signature could be
    re-attributed to any signer value by editing one field -- duplicate-signature
    key selection. The signature attested the claims and not who made them.
    """
    signed = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    assert anchor_lib.anchor_signature_problem(signed) is None

    forged = dict(signed)
    forged["signer"] = "D" + "z" * 43
    assert anchor_lib.anchor_signature_problem(forged) is not None
    assert _status(store, forged)["status"] == anchor_lib.ANCHOR_UNAVAILABLE


def test_g20_an_unsupported_anchor_version_is_refused(store, anchored):
    """G20. The version field was written and never read.

    A v1 anchor was signed over a different pre-image -- without `signer` -- so
    handing it to v2 rules is not a downgrade, it is a category error.
    """
    old = dict(anchored)
    old["v"] = "flossi-anchor-1"
    result = _status(store, old)
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert "not supported" in result["reason"]


def test_g4_interior_deletion_with_net_growth_is_not_stale(store, anchored):
    """G4, 4 reviewers, reproduced before the fix.

    ANCHOR_STALE was `len(leaves) > packet_count` under a comment claiming
    "nothing anchored has gone". Deleting an interior packet while adding two
    others therefore reported honest growth.
    """
    (store / "2026-08-01" / "long1.json").unlink()
    _write(store, "2026-08-03", "n1", _packet("D" + "c" * 43, 0, "E" + "n" * 43))
    _write(store, "2026-08-03", "n2", _packet("D" + "d" * 43, 0, "E" + "m" * 43))

    result = _status(store, anchored)
    assert result["findings"]["packet_delta"] == 1, "net growth, as in the report"
    assert result["status"] != anchor_lib.ANCHOR_STALE
    assert result["status"] == anchor_lib.ANCHOR_MISMATCH
    assert result["findings"]["missing_anchored_positions"] == [
        {"aid": "D" + "a" * 43, "sequence": 1}
    ]


def test_g4_genuine_growth_is_still_stale(store, anchored):
    """The subset check must not turn every honest session into an alarm."""
    _write(store, "2026-08-03", "n1", _packet("D" + "c" * 43, 0, "E" + "n" * 43))

    result = _status(store, anchored)
    assert result["status"] == anchor_lib.ANCHOR_STALE
    assert result["findings"]["missing_anchored_positions"] == []


def test_anchored_positions_reconstructs_the_committed_set(tmp_path):
    """max_seq plus interior_gaps already describe the occupied slots."""
    root = tmp_path / "provenance"
    aid = "D" + "a" * 43
    for n in (0, 1, 3):
        _write(root, "d", f"p{n}", _packet(aid, n, f"E{'p' * 42}{n}"))

    positions = anchor_lib.anchored_positions(anchor_lib.build_anchor(root))
    assert positions == {(aid, 0), (aid, 1), (aid, 3)}


# ---------------------------------------------------------------------------
# G5 — the prev_root walk, and the series it needs to walk over.
# ---------------------------------------------------------------------------


def _series(tmp_path, anchors):
    d = tmp_path / "series"
    d.mkdir(parents=True, exist_ok=True)
    for a in anchors:
        (d / f"{a['merkle_root']}.json").write_text(
            json.dumps(a), encoding="utf-8"
        )
    return d


def test_g5_the_walk_reaches_genesis(store, identity, tmp_path):
    """G5, 4 reviewers. prev_root was written and never read."""
    first = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    _write(store, "2026-08-03", "n1", _packet("D" + "c" * 43, 0, "E" + "n" * 43))
    second = anchor_lib.sign_anchor(
        anchor_lib.build_anchor(store, first), identity
    )

    result = anchor_lib.verify_anchor(
        store, second, series_dir=_series(tmp_path, [first, second])
    )
    assert result["status"] == anchor_lib.VERIFIED
    assert result["series"]["reached_genesis"] is True
    assert result["series"]["length"] == 2
    assert result["series"]["problems"] == []


def _two_anchors(store, identity):
    """Two anchors with DIFFERENT roots.

    The store has to change between them. Anchoring an unchanged store twice
    yields root == prev_root, which the walk correctly calls a cycle -- a real
    property worth knowing, and not what these tests are about.
    """
    first = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    _write(store, "2026-08-03", "grow", _packet("D" + "c" * 43, 0, "E" + "n" * 43))
    second = anchor_lib.sign_anchor(
        anchor_lib.build_anchor(store, first), identity
    )
    assert second["merkle_root"] != first["merkle_root"]
    assert second["prev_root"] == first["merkle_root"]
    return first, second


def test_g5_a_missing_ancestor_is_not_verified(store, identity, tmp_path):
    """A store that matches its anchor, over a history with a hole in it."""
    first, second = _two_anchors(store, identity)

    result = anchor_lib.verify_anchor(
        store, second, series_dir=_series(tmp_path, [second])
    )
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert "series breaks" in result["reason"]


def test_g5_a_tampered_ancestor_is_not_verified(store, identity, tmp_path):
    """Every link is signature-checked, not just the head."""
    first, second = _two_anchors(store, identity)
    tampered = json.loads(json.dumps(first))
    tampered["packet_count"] = 1

    result = anchor_lib.verify_anchor(
        store, second, series_dir=_series(tmp_path, [tampered, second])
    )
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert "does not verify" in result["reason"]


def test_g5_a_signed_cycle_is_reported_as_a_cycle(store, identity):
    """Signed, so the walk gets past the signature check and reaches the loop."""
    built = anchor_lib.build_anchor(store)
    built["prev_root"] = built["merkle_root"]
    looped = anchor_lib.sign_anchor(built, identity)
    assert anchor_lib.anchor_signature_problem(looped) is None

    walk = anchor_lib.walk_series(looped, {looped["merkle_root"]: looped})
    assert walk["reached_genesis"] is False
    assert any("cycle" in p for p in walk["problems"]), walk["problems"]


def test_g5_anchoring_an_unchanged_store_twice_self_references(store, identity):
    """Worth pinning: it is why the helper above mutates the store.

    prev_root then equals merkle_root, and the walk reports a cycle rather than
    a one-link history. Publishing an identical anchor is a no-op that should
    not look like progress.
    """
    first = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    second = anchor_lib.build_anchor(store, first)
    assert second["prev_root"] == second["merkle_root"]


def test_g5_genesis_alone_is_a_complete_series(store, anchored, tmp_path):
    result = anchor_lib.verify_anchor(
        store, anchored, series_dir=_series(tmp_path, [anchored])
    )
    assert result["status"] == anchor_lib.VERIFIED
    assert result["series"]["reached_genesis"] is True


def test_publish_must_not_launder_a_loss_into_the_new_baseline(tmp_path, identity):
    """Review finding: publish never checked the store against the anchor.

    An accidental truncation was written straight into the new baseline -- the
    next verify reported VERIFIED over a store that had lost packets, and the
    only record that anything went missing was the anchor being overwritten.
    This is the actionable half of the standing "republish over a truncated
    store returns VERIFIED" finding.
    """
    import subprocess

    store = tmp_path / "prov"
    (store / "d").mkdir(parents=True)
    aid = "D" + "a" * 43
    for n in range(4):
        _write(store, "d", f"p{n}", _packet(aid, n, f"E{'x' * 42}{n}"))
    anchor_path = tmp_path / "anchors" / "anchor.json"
    script = REPO_ROOT / "scripts" / "provenance_anchor.py"
    base = [
        sys.executable, str(script),
        "--provenance-root", str(store),
        "--identity-dir", str(tmp_path / "id"),
        "--anchor", str(anchor_path),
    ]

    first = subprocess.run(base + ["publish", "--allow-new-identity"],
                           capture_output=True, text=True)
    assert first.returncode == 0, first.stderr[-400:]

    (store / "d" / "p3.json").unlink()  # truncate the head

    refused = subprocess.run(base + ["publish"], capture_output=True, text=True)
    assert refused.returncode == 2, refused.stdout + refused.stderr[-300:]
    assert "refusing to publish" in refused.stdout
    assert "TRUNCATION_DETECTED" in refused.stdout
    # The refusal must name what is missing, not just decline.
    assert "head_regressions" in refused.stdout

    forced = subprocess.run(base + ["publish", "--force"], capture_output=True, text=True)
    assert forced.returncode == 0, "an operator who understands the loss can still proceed"
    assert "merkle_root" in forced.stdout


def test_the_cli_survives_an_anchor_path_outside_the_repository(tmp_path, identity):
    """`relative_to` RAISES outside the repo, and publish called it after writing.

    Every earlier run used the in-repo default and never reached this line, so
    the crash was invisible until a test used tmp_path.
    """
    import subprocess

    store = tmp_path / "prov"
    _write(store, "d", "p0", _packet("D" + "a" * 43, 0, "E" + "x" * 43))
    result = subprocess.run(
        [
            sys.executable, str(REPO_ROOT / "scripts" / "provenance_anchor.py"),
            "--provenance-root", str(store),
            "--identity-dir", str(tmp_path / "id"),
            "--anchor", str(tmp_path / "elsewhere" / "anchor.json"),
            "publish", "--allow-new-identity",
        ],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr[-500:]
    assert "Traceback" not in result.stderr


# ---------------------------------------------------------------------------
# Review round 2. The leaf must commit to content, not to self-declared headers.
# ---------------------------------------------------------------------------


def test_a_header_only_stub_cannot_reproduce_a_packets_leaf(store, identity):
    """The worst finding of the review, reproduced before the fix.

    The leaf was built from `t`/`i`/`s`/`d` read off the file, so a 129-byte
    stub asserting those four fields reproduced the leaf of a 585-byte signed
    packet exactly — signatures, payload, artifact refs and evidence all
    deleted, anchor still VERIFIED. That defeated the entire truncation
    guarantee: the commitment was to what a file said about itself.
    """
    anchored = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    assert _status(store, anchored)["status"] == anchor_lib.VERIFIED

    target = store / "2026-08-02" / "solo.json"
    real = json.loads(target.read_text(encoding="utf-8"))
    stub = {"t": "prov", "i": real["i"], "s": real["s"], "d": real["d"]}
    target.write_text(json.dumps(stub), encoding="utf-8")

    assert len(json.dumps(stub)) < len(json.dumps(real)), "the stub is smaller"
    result = _status(store, anchored)
    assert result["status"] != anchor_lib.VERIFIED
    assert result["unreadable_appeared"], "the gutted packet must be named"


def test_a_packet_that_only_claims_its_said_is_unreadable(tmp_path):
    """`d` is a digest over the packet's own content; claiming is not satisfying."""
    root = tmp_path / "prov"
    (root / "d").mkdir(parents=True)
    (root / "d" / "liar.json").write_text(
        json.dumps({"t": "prov", "i": "D" + "a" * 43, "s": "0", "d": "E" + "z" * 43}),
        encoding="utf-8",
    )

    leaves, unreadable = anchor_lib.scan_packets(root)
    assert leaves == []
    assert len(unreadable) == 1
    assert "SAID not satisfied" in unreadable[0]["error"]


def test_known_damage_is_frozen_rather_than_bricking_verification(tmp_path, identity):
    """The live store has three permanently damaged packets.

    Requiring an empty unreadable set would make it unverifiable forever, which
    is the b0de2fe mistake. The anchored set is the baseline; only a CHANGE is a
    finding.
    """
    root = tmp_path / "prov"
    (root / "d").mkdir(parents=True)
    _write(root, "d", "good", _packet("D" + "a" * 43, 0))
    (root / "d" / "damaged.json").write_text(
        json.dumps({"t": "prov", "i": "D" + "b" * 43, "s": "0", "d": "E" + "z" * 43}),
        encoding="utf-8",
    )

    anchored = anchor_lib.sign_anchor(anchor_lib.build_anchor(root), identity)
    assert anchored["unreadable"], "the damage is recorded in the anchor"
    assert (
        anchor_lib.verify_anchor(root, anchored)["status"] == anchor_lib.VERIFIED
    ), "known damage must not block verification"

    (root / "d" / "damaged.json").unlink()
    after = anchor_lib.verify_anchor(root, anchored)
    assert after["status"] != anchor_lib.VERIFIED
    assert after["unreadable_vanished"], "a deleted malformed packet must not pass silently"


def test_republishing_an_unchanged_store_is_a_no_op(tmp_path, identity):
    """Two identical publishes used to brick verification permanently.

    The series file is keyed by root, so republishing overwrote the predecessor
    with an anchor whose prev_root equals its own merkle_root; walk_series then
    reported a cycle and every later verify returned ANCHOR_UNAVAILABLE.
    """
    import subprocess

    store = tmp_path / "prov"
    _write(store, "d", "p0", _packet("D" + "a" * 43, 0))
    anchor_path = tmp_path / "anchors" / "anchor.json"
    base = [
        sys.executable, str(REPO_ROOT / "scripts" / "provenance_anchor.py"),
        "--provenance-root", str(store),
        "--identity-dir", str(tmp_path / "id"),
        "--anchor", str(anchor_path),
    ]

    assert subprocess.run(base + ["publish", "--allow-new-identity"]).returncode == 0
    second = subprocess.run(base + ["publish"], capture_output=True, text=True)
    assert second.returncode == 0
    assert json.loads(second.stdout)["status"] == "unchanged"

    verified = subprocess.run(base + ["verify"], capture_output=True, text=True)
    assert verified.returncode == 0, "a redundant publish must not brick verification"
    assert json.loads(verified.stdout)["status"] == anchor_lib.VERIFIED


def test_the_spec_states_the_signature_scope_the_code_implements():
    """Spec/code divergence on a signature rule is a verifier-breaking defect.

    The spec said `sig` and `signer` were both excluded while the code excluded
    only `sig`. A verifier written from the spec rejects every real anchor; one
    that implements the spec faithfully reintroduces the signer-substitution
    flaw. Pinned so the two cannot drift apart again silently.
    """
    spec = (REPO_ROOT / "docs" / "specs" / "provenance-anchor.spec.md").read_text(
        encoding="utf-8"
    )
    assert "**`sig` alone is excluded**" in spec

    probe = {"v": "x", "merkle_root": "r", "signer": "S", "sig": "0Bxx"}
    signed_bytes = anchor_lib.anchor_signing_bytes(probe)
    assert b"signer" in signed_bytes, "signer must be inside the pre-image"
    assert b'"sig"' not in signed_bytes, "a signature cannot cover itself"


def test_a_same_slot_substitution_with_growth_is_not_stale(store, identity):
    """Positions are a weaker proxy for what digests state exactly.

    Replacing a NON-HEAD packet with a different one at the same (identity,
    sequence) while the store also grows leaves every anchored position
    occupied, the count higher, and — before this fix — the verdict
    ANCHOR_STALE. The pre-publish guard permits STALE, so the loss would have
    been absorbed into the replacement anchor. That is the count-comparison
    defect one level up.
    """
    aid = "D" + "a" * 43
    target = store / "2026-08-01" / "long1.json"
    anchored = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    original = json.loads(target.read_text(encoding="utf-8"))

    target.write_text(json.dumps(_packet(aid, 1, "SWAPPED")), encoding="utf-8")
    _write(store, "2026-08-03", "extra", _packet("D" + "c" * 43, 0, "extra"))

    result = _status(store, anchored)
    assert result["findings"]["packet_delta"] == 1, "the store still grew"
    assert result["findings"]["missing_anchored_positions"] == [], (
        "every anchored position is still occupied — which is why positions "
        "alone could not see this"
    )
    assert result["status"] != anchor_lib.ANCHOR_STALE
    missing = result["findings"]["missing_anchored_leaves"]
    assert [m["said"] for m in missing] == [original["d"]]
    assert missing[0]["sequence"] == 1


def test_the_anchor_records_every_leaf_not_only_heads(store):
    built = anchor_lib.build_anchor(store)
    long_chain = next(
        e for e in built["identities"] if e["count"] == 4
    )
    assert len(long_chain["leaf_saids"]) == 4
    assert [pair[0] for pair in long_chain["leaf_saids"]] == [0, 1, 2, 3]
    # head_saids stays, and must agree with the tail of leaf_saids
    assert long_chain["head_saids"] == [long_chain["leaf_saids"][-1][1]]


def test_a_v2_anchor_is_refused_because_it_cannot_be_checked_exactly(store, identity):
    """v2 has no leaf_saids, so its subset check would silently be the weak one."""
    anchored = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    old = dict(anchored)
    old["v"] = "flossi-anchor-2"
    result = _status(store, old)
    assert result["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert "not supported" in result["reason"]


def test_invalid_utf8_is_unreadable_rather_than_a_crash(tmp_path):
    """`Path.read_text` raises UnicodeDecodeError, which is neither OSError nor
    JSONDecodeError — so one corrupt byte crashed both publish and verify with a
    traceback, breaking verify_anchor's documented never-raises contract for
    exactly the malformed input the unreadable set exists to report.
    """
    root = tmp_path / "prov"
    (root / "d").mkdir(parents=True)
    (root / "d" / "bad.json").write_bytes(
        b'{"t":"prov","i":"D","s":"0","d":"E\xff\xfe"}'
    )

    leaves, unreadable = anchor_lib.scan_packets(root)
    assert leaves == []
    assert len(unreadable) == 1
    assert "codec can't decode" in unreadable[0]["error"]
    # and the whole verdict path stays non-raising
    assert anchor_lib.verify_anchor(root, None)["status"] == (
        anchor_lib.ANCHOR_UNAVAILABLE
    )
