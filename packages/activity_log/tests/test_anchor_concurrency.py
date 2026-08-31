"""What the anchor scan may observe while packets are being written.

Three PR41 review findings, all one defect seen from different angles: the
anchor scan enumerates the packet tree holding `.anchor-scan.lock`, which the
packet writers never take. The lock read as synchronisation and was not.

Fixed where the race actually is rather than by widening the lock (which would
put every provenance hook behind an anchor run, and order two locks against
each other):

- packet writes are atomic, so no reader can observe a prefix;
- an anchor commits only to a scan that two consecutive passes agreed on;
- and the retained-series reader tolerates a file that is valid JSON but not an
  object, which crashed a verdict documented never to raise.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.activity_log import anchor as anchor_lib  # noqa: E402
from packages.activity_log import provenance  # noqa: E402
from packages.activity_log.provenance import load_or_create_identity  # noqa: E402

# ---------------------------------------------------------------------------
# A reader must never see a partial packet.
# ---------------------------------------------------------------------------


def test_a_packet_is_never_written_directly_to_its_final_path(tmp_path, monkeypatch):
    """The property: the name a reader scans for only ever appears complete.

    Asserted against the write path rather than by racing a thread, because a
    timing test that passes once proves nothing about the interleaving that
    matters.
    """
    load_or_create_identity(tmp_path / "identity")
    written: list[str] = []

    real_write = Path.write_bytes

    def record(self, data):
        written.append(self.name)
        return real_write(self, data)

    monkeypatch.setattr(Path, "write_bytes", record)

    packet, packet_path = provenance.create_packet(
        [{"kind": "note", "detail": "d"}],
        identity_dir=tmp_path / "identity",
        output_root=tmp_path / "provenance",
    )

    assert packet_path.name not in written, "final name observable while incomplete"
    assert any(n.endswith(".json.tmp") for n in written)
    assert packet_path.exists()
    assert json.loads(packet_path.read_text(encoding="utf-8"))["d"] == packet["d"]


def test_the_temp_file_is_not_picked_up_by_the_scan(tmp_path):
    """A crashed writer leaves a .json.tmp behind. It must not become damage."""
    root = tmp_path / "provenance" / "2026-08-01"
    root.mkdir(parents=True)
    (root / "Epartial.json.tmp").write_text('{"t": "prov", "i": "D', encoding="utf-8")

    leaves, unreadable = anchor_lib.scan_packets(tmp_path / "provenance")

    assert leaves == []
    assert unreadable == [], "an orphaned temp file is not store damage"


# ---------------------------------------------------------------------------
# An anchor commits only to a set that held still.
# ---------------------------------------------------------------------------


def test_a_scan_that_changes_under_us_is_retried(tmp_path, monkeypatch):
    leaf_a = anchor_lib.PacketLeaf(
        identity="D" + "a" * 43, sequence=0, said="E" + "a" * 43
    )
    leaf_b = anchor_lib.PacketLeaf(
        identity="D" + "b" * 43, sequence=0, said="E" + "b" * 43
    )
    scans = [([leaf_a], []), ([leaf_a, leaf_b], []), ([leaf_a, leaf_b], [])]
    calls = {"n": 0}

    def fake_scan(root):
        result = scans[min(calls["n"], len(scans) - 1)]
        calls["n"] += 1
        return result

    monkeypatch.setattr(anchor_lib, "scan_packets", fake_scan)

    leaves, unreadable = anchor_lib._stable_scan(tmp_path)

    assert calls["n"] == 3, "settled only once two consecutive scans agreed"
    assert leaves == [leaf_a, leaf_b]


def test_a_store_that_never_settles_is_refused_not_signed(tmp_path, monkeypatch):
    """This test previously asserted the opposite, and was wrong to.

    It accepted the final unconfirmed scan as "a real point-in-time set taken
    under contention". rglob walks directories in order, so a packet can land
    in one already passed while another lands in one not yet reached: the set
    was never the store at any instant. Signing it puts that fiction under a
    signature. Refusing is the correct outcome; publishing is cheap to retry.
    """
    calls = {"n": 0}

    def never_settles(root):
        calls["n"] += 1
        said = "E" + str(calls["n"]).rjust(43, "z")
        return [anchor_lib.PacketLeaf("D" + "a" * 43, 0, said)], []

    monkeypatch.setattr(anchor_lib, "scan_packets", never_settles)

    with pytest.raises(anchor_lib.StoreContention):
        anchor_lib._stable_scan(tmp_path)

    assert calls["n"] == 3, "bounded; a busy store must not spin"


def test_contention_propagates_out_of_build_anchor(tmp_path, monkeypatch):
    """Every caller of build_anchor is on its way to signing."""
    calls = {"n": 0}

    def never_settles(root):
        calls["n"] += 1
        return [anchor_lib.PacketLeaf("D" + "a" * 43, calls["n"], "E" + "a" * 43)], []

    monkeypatch.setattr(anchor_lib, "scan_packets", never_settles)

    with pytest.raises(anchor_lib.StoreContention):
        anchor_lib.build_anchor(tmp_path)


def test_a_changed_unreadable_set_also_counts_as_unsettled(tmp_path, monkeypatch):
    """Damage appearing mid-scan is contention too, not a stable observation."""
    leaf = anchor_lib.PacketLeaf("D" + "a" * 43, 0, "E" + "a" * 43)
    calls = {"n": 0}

    def churning_damage(root):
        calls["n"] += 1
        return [leaf], [{"path": f"p{calls['n']}.json", "error": "x", "sha256": "y"}]

    monkeypatch.setattr(anchor_lib, "scan_packets", churning_damage)

    with pytest.raises(anchor_lib.StoreContention):
        anchor_lib._stable_scan(tmp_path)


def test_a_settled_store_is_not_scanned_more_than_twice(tmp_path, monkeypatch):
    calls = {"n": 0}
    fixed = ([anchor_lib.PacketLeaf("D" + "a" * 43, 0, "E" + "a" * 43)], [])

    def stable(root):
        calls["n"] += 1
        return fixed

    monkeypatch.setattr(anchor_lib, "scan_packets", stable)

    anchor_lib._stable_scan(tmp_path)

    assert calls["n"] == 2


# ---------------------------------------------------------------------------
# The third reader of the same shape bug.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("payload", ["[]", '"a string"', "5", "null", "[{}]"])
def test_a_retained_series_file_of_the_wrong_shape_is_skipped(tmp_path, payload):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    (series_dir / "wrong-shape.json").write_text(payload, encoding="utf-8")

    assert anchor_lib.load_series(series_dir) == {}


def test_one_malformed_series_file_does_not_hide_the_valid_ones(tmp_path):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    (series_dir / "a-bad.json").write_text("[]", encoding="utf-8")
    (series_dir / "b-good.json").write_text(
        json.dumps({"merkle_root": "Eroot", "v": "flossi-anchor-3"}), encoding="utf-8"
    )

    series = anchor_lib.load_series(series_dir)

    assert list(series) == ["Eroot"]


def test_verification_survives_a_malformed_retained_anchor(tmp_path):
    """The documented contract is a structured verdict, never a traceback."""
    identity = load_or_create_identity(tmp_path / "identity")
    store = tmp_path / "provenance"
    provenance.create_packet(
        [{"kind": "note", "detail": "d"}],
        identity_dir=tmp_path / "identity",
        output_root=store,
    )
    anchored = anchor_lib.sign_anchor(anchor_lib.build_anchor(store), identity)
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    (series_dir / "junk.json").write_text("[]", encoding="utf-8")

    result = anchor_lib.verify_anchor(store, anchored, series_dir=series_dir)

    assert result["status"] in {
        anchor_lib.VERIFIED,
        anchor_lib.ANCHOR_MISMATCH,
        anchor_lib.ANCHOR_UNAVAILABLE,
    }


# ---------------------------------------------------------------------------
# Retained history must survive a migration that keeps the same root.
# ---------------------------------------------------------------------------


def _cli_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "provenance_anchor_cli", REPO_ROOT / "scripts" / "provenance_anchor.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_second_anchor_with_the_same_root_does_not_destroy_the_first(tmp_path):
    """v2 and its v3 migration hash identically: the version is outside the tree."""
    cli = _cli_module()
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    root = "E" + "r" * 43
    v2 = json.dumps({"v": "flossi-anchor-2", "merkle_root": root}).encode()
    v3 = json.dumps({"v": "flossi-anchor-3", "merkle_root": root}).encode()

    first = cli._retain_series(series_dir, root, v2)
    second = cli._retain_series(series_dir, root, v3)

    assert first != second
    assert first.read_bytes() == v2, "the superseded anchor was overwritten"
    assert second.read_bytes() == v3


def test_republishing_identical_bytes_is_idempotent(tmp_path):
    cli = _cli_module()
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    root = "E" + "r" * 43
    payload = json.dumps({"v": "flossi-anchor-3", "merkle_root": root}).encode()

    first = cli._retain_series(series_dir, root, payload)
    second = cli._retain_series(series_dir, root, payload)

    assert first == second
    assert len(list(series_dir.glob("*.json"))) == 1


def test_duplicate_roots_resolve_to_the_newer_anchor_not_to_glob_order(tmp_path):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    root = "E" + "r" * 43
    # sorted() yields "{root}.2.json" before "{root}.json", so last-write-wins
    # on glob order picks "{root}.json". Put the OLDER anchor there: the test
    # only discriminates if plain glob order would give the wrong answer.
    # (The first version of this test had them the other way round and passed
    # against the unfixed code, which is what red-green is for.)
    (series_dir / f"{root}.json").write_text(
        json.dumps(
            {"v": "flossi-anchor-2", "merkle_root": root, "generated_at": "2026-01-01"}
        ),
        encoding="utf-8",
    )
    (series_dir / f"{root}.2.json").write_text(
        json.dumps(
            {"v": "flossi-anchor-3", "merkle_root": root, "generated_at": "2026-08-30"}
        ),
        encoding="utf-8",
    )

    series = anchor_lib.load_series(series_dir)

    assert series[root]["generated_at"] == "2026-08-30"


# ---------------------------------------------------------------------------
# An operator-writable witness sidecar must not take down the store verdict.
# ---------------------------------------------------------------------------


def test_an_unreadable_witness_sidecar_does_not_lose_the_store_verdict(tmp_path):
    cli = _cli_module()
    from packages.activity_log import witness as witness_lib

    root = "E" + "r" * 43
    anchor_path = tmp_path / "anchor.json"
    anchor_path.write_text("{}", encoding="utf-8")
    # A directory where a file is expected: read_bytes raises OSError on every
    # platform, which is the portable stand-in for locked or permission-denied.
    proof_path = witness_lib.proof_path(tmp_path, root)
    proof_path.mkdir(parents=True)

    state = cli._witness_state(
        anchor_path, {"merkle_root": root, "witnesses": [{"kind": "ots"}]}
    )

    assert state["status"] == witness_lib.WITNESS_UNAVAILABLE
    assert state["claims_in_anchor"] == 1


# ---------------------------------------------------------------------------
# An unreadable anchor is not an absent one.
# ---------------------------------------------------------------------------


def _publish_cmd(tmp_path, store, anchor_path, *extra):
    import subprocess
    import sys as _sys

    return subprocess.run(
        [
            _sys.executable,
            str(REPO_ROOT / "scripts" / "provenance_anchor.py"),
            "--provenance-root",
            str(store),
            "--identity-dir",
            str(tmp_path / "id"),
            "--anchor",
            str(anchor_path),
            "publish",
            *extra,
        ],
        capture_output=True,
        text=True,
    )


@pytest.fixture
def small_store(tmp_path):
    identity = load_or_create_identity(tmp_path / "id")
    store = tmp_path / "provenance"
    provenance.create_packet(
        [{"kind": "note", "detail": "d"}],
        identity_dir=tmp_path / "id",
        output_root=store,
    )
    assert identity is not None
    return store


@pytest.mark.parametrize(
    "corrupt", [b"\xff\xfe not utf 8", b"{not json", b"[]", b'"a string"', b"5"]
)
def test_publish_refuses_over_an_anchor_it_cannot_read(tmp_path, small_store, corrupt):
    """load_anchor returns None for absent AND for corrupt. Publish must not
    read the second as the first and write a fresh genesis over real history."""
    anchor_path = tmp_path / "anchor.json"

    first = _publish_cmd(tmp_path, small_store, anchor_path, "--allow-new-identity")
    assert first.returncode == 0, first.stdout + first.stderr[-300:]
    original = anchor_path.read_bytes()

    anchor_path.write_bytes(corrupt)
    refused = _publish_cmd(tmp_path, small_store, anchor_path)

    assert refused.returncode == 2, refused.stdout + refused.stderr[-300:]
    assert "unreadable anchor" in refused.stdout
    assert anchor_path.read_bytes() == corrupt, "refusal must not rewrite the file"
    assert original != corrupt


def test_the_refusal_points_at_the_retained_series_to_recover_from(
    tmp_path, small_store
):
    anchor_path = tmp_path / "anchor.json"
    _publish_cmd(tmp_path, small_store, anchor_path, "--allow-new-identity")
    anchor_path.write_bytes(b"[]")

    refused = _publish_cmd(tmp_path, small_store, anchor_path)

    assert "retained anchor(s) remain" in refused.stdout


def test_a_genuinely_absent_anchor_still_publishes(tmp_path, small_store):
    """The guard must narrow to UNREADABLE, not block a first publication."""
    anchor_path = tmp_path / "anchor.json"

    first = _publish_cmd(tmp_path, small_store, anchor_path, "--allow-new-identity")

    assert first.returncode == 0, first.stdout + first.stderr[-300:]
    assert anchor_path.exists()


def test_force_still_overrides_an_unreadable_anchor(tmp_path, small_store):
    anchor_path = tmp_path / "anchor.json"
    _publish_cmd(tmp_path, small_store, anchor_path, "--allow-new-identity")
    anchor_path.write_bytes(b"[]")

    forced = _publish_cmd(tmp_path, small_store, anchor_path, "--force")

    assert forced.returncode == 0, forced.stdout + forced.stderr[-300:]
    assert json.loads(anchor_path.read_text(encoding="utf-8"))["v"]


# ---------------------------------------------------------------------------
# A store-supplied sequence must not size a loop.
# ---------------------------------------------------------------------------


def test_an_implausible_sequence_is_damage_not_a_chain_position(tmp_path):
    """One packet at s=10^12 made publish build a trillion-element gap list
    before it could sign or report anything: a denial of service supplied by
    the store, against the command that inspects the store."""
    identity = load_or_create_identity(tmp_path / "id")
    store = tmp_path / "provenance"
    packet, path = provenance.create_packet(
        [{"kind": "note", "detail": "d"}],
        identity_dir=tmp_path / "id",
        output_root=store,
    )
    assert identity is not None
    # Re-sign at an absurd sequence so the SAID is genuinely satisfied -- a
    # fixture that merely claims one is rejected earlier for the wrong reason.
    document = json.loads(path.read_text(encoding="utf-8"))
    document["s"] = str(anchor_lib.MAX_SEQUENCE + 1)
    document["d"] = ""
    document["sigs"] = []
    import blake3
    import jcs

    document["d"] = (
        "E"
        + __import__("base64")
        .urlsafe_b64encode(blake3.blake3(jcs.canonicalize(document)).digest())
        .decode()[:43]
    )
    path.write_text(json.dumps(document), encoding="utf-8")

    leaves, unreadable = anchor_lib.scan_packets(store)

    assert leaves == [], "an implausible sequence must not become a leaf"
    assert any("implausible sequence" in u["error"] for u in unreadable)


def test_the_gap_diagnostic_is_bounded(monkeypatch):
    """Even inside the sequence bound, one packet at the top implies a million
    gaps. The list is a diagnostic; an unreadable one is not worth the memory."""
    monkeypatch.setattr(anchor_lib, "MAX_REPORTED_GAPS", 5)
    leaves = [
        anchor_lib.PacketLeaf("D" + "a" * 43, 0, "E" + "a" * 43),
        anchor_lib.PacketLeaf("D" + "a" * 43, 50, "E" + "b" * 43),
    ]

    summary = anchor_lib._identity_summaries(leaves)[0]

    assert len(summary["interior_gaps"]) == 5
    assert summary["interior_gaps_truncated"] is True


def test_positions_come_from_the_leaves_not_from_subtraction():
    """anchored_positions reconstructed {0..max_seq} minus gaps, which costs
    max_seq rather than the packet count -- and is simply wrong once the gap
    list is truncated."""
    anchor = {
        "identities": [
            {
                "aid": "D" + "a" * 43,
                "max_seq": 900_000,
                "leaf_saids": [[0, "E" + "a" * 43], [900_000, "E" + "b" * 43]],
                "interior_gaps": [1, 2, 3],
                "interior_gaps_truncated": True,
            }
        ]
    }

    positions = anchor_lib.anchored_positions(anchor)

    assert positions == {("D" + "a" * 43, 0), ("D" + "a" * 43, 900_000)}


def test_a_truncated_gap_list_is_never_subtracted_from(tmp_path):
    """Without leaf_saids there is nothing exact to read, and subtracting an
    incomplete gap list would INVENT occupied slots. Report none instead."""
    anchor = {
        "identities": [
            {
                "aid": "D" + "a" * 43,
                "max_seq": 900_000,
                "interior_gaps": [1],
                "interior_gaps_truncated": True,
            }
        ]
    }

    assert anchor_lib.anchored_positions(anchor) == set()


# ---------------------------------------------------------------------------
# Retention must not lose a race, and a rotation must produce a series that
# the default verify can actually accept.
# ---------------------------------------------------------------------------


def test_retention_never_clobbers_a_file_that_appeared_mid_write(tmp_path, monkeypatch):
    """The store lock is released by build_anchor long before retention runs,
    and a witnessed publish spends seconds on the network in between. exists()
    then write() let both invocations pick the same name."""
    cli = _cli_module()
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    root = "E" + "r" * 43
    rival = json.dumps({"v": "flossi-anchor-3", "merkle_root": root, "n": 1}).encode()
    mine = json.dumps({"v": "flossi-anchor-3", "merkle_root": root, "n": 2}).encode()

    (series_dir / f"{root}.json").write_bytes(rival)
    # Simulate the RACE, not merely the collision: the rival lands after our
    # existence check and before our write. exists() reporting False over a
    # file that is really there is exactly what the loser of that race sees.
    # Without this the test passes against the old code, which handled a
    # collision it had already observed.
    monkeypatch.setattr(Path, "exists", lambda self: False)
    written = cli._retain_series(series_dir, root, mine)
    monkeypatch.undo()

    assert written.name == f"{root}.2.json"
    assert (series_dir / f"{root}.json").read_bytes() == rival, "rival was clobbered"
    assert written.read_bytes() == mine


def test_a_rotation_starts_a_new_series_instead_of_an_unverifiable_one(
    tmp_path, small_store
):
    """verify pins the head's signer for the WHOLE walk, so a series spanning a
    rotation fails its own default verification on the first ancestor: publish
    would allow a rotation verify could never accept."""
    anchor_path = tmp_path / "anchor.json"
    first = _publish_cmd(tmp_path, small_store, anchor_path, "--allow-new-identity")
    assert first.returncode == 0, first.stdout

    import subprocess
    import sys as _sys

    rotated = subprocess.run(
        [
            _sys.executable,
            str(REPO_ROOT / "scripts" / "provenance_anchor.py"),
            "--provenance-root",
            str(small_store),
            "--identity-dir",
            str(tmp_path / "id2"),
            "--anchor",
            str(anchor_path),
            "publish",
            "--allow-new-identity",
            "--allow-signer-change",
        ],
        capture_output=True,
        text=True,
    )

    assert rotated.returncode == 0, rotated.stdout + rotated.stderr[-300:]
    assert "signer rotation" in rotated.stdout
    head = json.loads(anchor_path.read_text(encoding="utf-8"))
    assert head["prev_root"] is None, "rotated head still chains to the old signer"

    verified = subprocess.run(
        [
            _sys.executable,
            str(REPO_ROOT / "scripts" / "provenance_anchor.py"),
            "--provenance-root",
            str(small_store),
            "--identity-dir",
            str(tmp_path / "id2"),
            "--anchor",
            str(anchor_path),
            "verify",
        ],
        capture_output=True,
        text=True,
    )
    verdict = json.loads(verified.stdout)
    assert verdict["status"] == anchor_lib.VERIFIED, verdict


def test_a_redundant_republish_is_still_a_no_op_even_with_the_rotation_flag(
    tmp_path, small_store
):
    """--allow-signer-change must not become a way to publish an anchor that is
    its own predecessor, which is the cycle the no-op guard exists to stop."""
    anchor_path = tmp_path / "anchor.json"
    _publish_cmd(tmp_path, small_store, anchor_path, "--allow-new-identity")

    again = _publish_cmd(tmp_path, small_store, anchor_path, "--allow-signer-change")

    assert again.returncode == 0
    assert '"status": "unchanged"' in again.stdout


def test_the_pointer_is_staged_under_a_name_no_other_publish_shares(
    tmp_path, small_store, monkeypatch
):
    """A single shared anchor.json.tmp is the retained-series race one file
    along: two publishes write it, one replaces the path while the other still
    holds the inode, and the loser writes into the freshly published anchor.

    Asserted on the name actually handed to os.replace. Checking that no
    leftover .tmp remains afterwards does NOT discriminate -- the rename
    consumes it either way, so that version passed against the shared name.
    """
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    staged: list[str] = []
    real_replace = cli.os.replace

    def record(src, dst):
        staged.append(str(src))
        return real_replace(src, dst)

    monkeypatch.setattr(cli.os, "replace", record)

    code = cli.main(
        [
            "--provenance-root",
            str(small_store),
            "--identity-dir",
            str(tmp_path / "id"),
            "--anchor",
            str(anchor_path),
            "publish",
            "--allow-new-identity",
        ]
    )

    assert code == 0
    pointer_stages = [name for name in staged if name.endswith(".tmp")]
    assert pointer_stages, "the pointer was not staged at all"
    assert all(
        not name.endswith("anchor.json.tmp") for name in pointer_stages
    ), f"shared staging name still in use: {pointer_stages}"
    assert json.loads(anchor_path.read_text(encoding="utf-8"))["v"]


def test_the_chain_walk_refuses_an_implausible_sequence_without_expanding_it(
    tmp_path,
):
    """Same bound as the anchor scan, in the module that owns it. Bounding one
    reader and not the other is how this was found twice in two files."""
    from packages.activity_log import provenance as prov

    assert prov.MAX_SEQUENCE == anchor_lib.MAX_SEQUENCE, "two copies of one bound"

    index = {("D" + "a" * 43, None, str(prov.MAX_SEQUENCE + 1)): [(tmp_path, "E")]}
    paths, digests = prov._sequence_index(index)

    assert paths == {} and digests == {}, "an implausible slot was indexed"


# ---------------------------------------------------------------------------
# The preflight and the build are separate scans.
# ---------------------------------------------------------------------------


def test_a_packet_lost_between_the_preflight_and_the_build_is_refused(
    tmp_path, small_store, monkeypatch
):
    """verify_anchor() and build_anchor() each walk the store, and the lock is
    released between them. A packet deleted in that window passed the preflight
    and was simply absent from the anchor that got signed -- which still linked
    to the old root, and the series walk checks signatures and links, not that a
    descendant covers its predecessor."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0
    anchored = next(iter(sorted(small_store.rglob("*.json"))))

    # A second packet, so the store legitimately changes and publish proceeds
    # past the unchanged-root no-op.
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )

    # Delete the packet the FIRST anchor covered, at exactly the moment the
    # preflight is done. Deleting an arbitrary one is not the same test: drop
    # the newer packet and the store returns to the anchored root, which the
    # unchanged-root no-op correctly reports instead.
    real_build = cli.anchor_lib.build_anchor

    def delete_then_build(root, previous=None, witnesses=None):
        anchored.unlink()
        return real_build(root, previous, witnesses)

    monkeypatch.setattr(cli.anchor_lib, "build_anchor", delete_then_build)

    code = cli.main(base + ["publish"])

    assert code == 2, "signed an anchor that dropped a packet its predecessor had"


def test_force_still_publishes_over_a_loss_seen_only_in_the_build(
    tmp_path, small_store, monkeypatch
):
    """--force is the deliberate override for a detected loss and must stay one."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0
    anchored = next(iter(sorted(small_store.rglob("*.json"))))
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )
    real_build = cli.anchor_lib.build_anchor

    def delete_then_build(root, previous=None, witnesses=None):
        anchored.unlink()
        return real_build(root, previous, witnesses)

    monkeypatch.setattr(cli.anchor_lib, "build_anchor", delete_then_build)

    assert cli.main(base + ["publish", "--force"]) == 0


def test_same_second_duplicates_resolve_by_retention_order_not_glob_order(tmp_path):
    """A signer rotation over an unchanged store, published in the same second
    as its predecessor, gives two anchors with the same root, the same
    second-precision generated_at and the same version. Without a real
    tie-break the FIRST file visited wins, and a later head linking to that
    root made walk_series load the older signer's anchor, so the fresh series
    returned ANCHOR_UNAVAILABLE.

    Indices 2 and 3, not base and 2: sorted() yields "E….2.json" before
    "E….json", so a base-versus-2 fixture has glob order accidentally picking
    the newer file and passes against the unfixed code. "E….2.json" before
    "E….3.json" is where lexical order and retention order disagree.
    """
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    root = "E" + "r" * 43
    same = {
        "merkle_root": root,
        "generated_at": "2026-08-31T01:00:00+00:00",
        "v": "flossi-anchor-3",
    }
    (series_dir / f"{root}.2.json").write_text(
        json.dumps({**same, "signer": "OLD"}), encoding="utf-8"
    )
    (series_dir / f"{root}.3.json").write_text(
        json.dumps({**same, "signer": "NEW"}), encoding="utf-8"
    )

    series = anchor_lib.load_series(series_dir)

    assert series[root]["signer"] == "NEW", "the earlier retention won"


def test_the_retention_index_is_read_as_a_number_not_a_name():
    """Lexically "E….2.json" sorts BEFORE "E….json", so a filename tie-break
    would have ordered these backwards."""
    assert anchor_lib._retention_index(Path("Eroot.json")) == 1
    assert anchor_lib._retention_index(Path("Eroot.2.json")) == 2
    assert anchor_lib._retention_index(Path("Eroot.10.json")) == 10
    assert anchor_lib._retention_index(
        Path("Eroot.10.json")
    ) > anchor_lib._retention_index(Path("Eroot.2.json"))


# ---------------------------------------------------------------------------
# A verdict nobody can parse is not a verdict.
# ---------------------------------------------------------------------------


def test_a_large_verdict_is_still_valid_json(tmp_path):
    """Slicing the serialized document cut it mid-token, so the structured
    result became unparseable exactly when a store is damaged enough to produce
    many findings -- the case where a script reading it is most useful."""
    cli = _cli_module()
    result = {
        "status": "ANCHOR_MISMATCH",
        "anchored_root": "E" + "a" * 43,
        "current_root": "E" + "b" * 43,
        "anchored_packets": 500,
        "current_packets": 12,
        "unreadable_vanished": [
            {"path": f"2026-08-01/E{i:043d}.json", "sha256": "0" * 64}
            for i in range(400)
        ],
        "findings": {
            "missing_anchored_leaves": [
                ["D" + "a" * 43, i, "E" + str(i).rjust(43, "z")] for i in range(400)
            ]
        },
    }

    rendered = cli._bounded_json(result, 8000)

    assert len(rendered) <= 8000
    parsed = json.loads(rendered)  # the whole point
    assert parsed["status"] == "ANCHOR_MISMATCH"
    assert parsed["anchored_root"] == result["anchored_root"]
    assert parsed["truncated"], "dropped entries must be declared"


def test_a_small_verdict_is_untouched(tmp_path):
    cli = _cli_module()
    result = {"status": "VERIFIED", "anchored_root": "E" + "a" * 43}

    rendered = cli._bounded_json(result, 8000)

    assert json.loads(rendered) == result
    assert "truncated" not in rendered


def test_the_envelope_survives_even_an_absurd_limit(tmp_path):
    """Under a limit no full verdict can meet, emit the part every caller reads
    rather than a fragment of the part they do not."""
    cli = _cli_module()
    result = {
        "status": "TRUNCATION_DETECTED",
        "anchored_root": "E" + "a" * 43,
        "current_root": "E" + "b" * 43,
        "anchored_packets": 9,
        "current_packets": 2,
        "findings": {"missing_anchored_leaves": [["D" + "a" * 43, 1, "E" + "z" * 43]]},
    }

    rendered = cli._bounded_json(result, 200)

    parsed = json.loads(rendered)
    assert parsed["status"] == "TRUNCATION_DETECTED"
    assert parsed["anchored_packets"] == 9


# ---------------------------------------------------------------------------
# The migration path discarded the predecessor on the strength of one field.
# ---------------------------------------------------------------------------


def test_editing_the_version_field_cannot_launder_a_truncated_store(
    tmp_path, small_store
):
    """`v` is a field anyone who can write the repo can edit, and this branch
    acted on it by discarding `previous` -- skipping the whole loss preflight.
    One edit was enough to make an ordinary publish sign a fresh genesis over a
    truncated store with no --force anywhere."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0

    # Truncate the store, then doctor only the version field.
    victim = sorted(small_store.rglob("*.json"))[0]
    victim.unlink()
    stored = json.loads(anchor_path.read_text(encoding="utf-8"))
    stored["v"] = "flossi-anchor-1"
    anchor_path.write_text(json.dumps(stored, indent=2), encoding="utf-8")

    code = cli.main(base + ["publish"])

    assert code == 2, "a doctored version field bypassed the loss preflight"


def test_a_genuine_legacy_anchor_still_migrates(tmp_path, small_store, monkeypatch):
    """The guard must narrow to anchors that fail their own signature, not
    block every format bump -- which is the escape route a bump needs."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0

    # Same anchor, unedited and therefore still authentic; this build simply
    # stops recognising its version.
    monkeypatch.setattr(
        cli.anchor_lib, "SUPPORTED_VERSIONS", frozenset({"flossi-anchor-9"})
    )
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )

    assert cli.main(base + ["publish"]) == 0


def test_force_still_migrates_an_unauthenticated_anchor(tmp_path, small_store):
    """A genuinely pre-v2 anchor cannot authenticate under today's rule either,
    so the documented override has to keep working."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0
    stored = json.loads(anchor_path.read_text(encoding="utf-8"))
    stored["v"] = "flossi-anchor-1"
    anchor_path.write_text(json.dumps(stored, indent=2), encoding="utf-8")

    assert cli.main(base + ["publish", "--force"]) == 0


def test_an_attacker_signed_migration_anchor_is_refused(tmp_path, small_store):
    """The previous fix closed "edit one field". This closes "replace the whole
    file": generate your own key, sign a truncated-store anchor with an
    unsupported `v`, and the migration path discarded the predecessor -- past
    both the loss preflight and the signer-continuity check."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0

    # The attacker truncates the store and replaces the anchor wholesale with
    # one their OWN key signs, declaring a version this build will migrate.
    sorted(small_store.rglob("*.json"))[0].unlink()
    theirs = load_or_create_identity(tmp_path / "attacker")
    forged = anchor_lib.sign_anchor(anchor_lib.build_anchor(small_store), theirs)
    forged["v"] = "flossi-anchor-1"
    forged = anchor_lib.sign_anchor(forged, theirs)
    anchor_path.write_text(json.dumps(forged, indent=2), encoding="utf-8")

    # Self-consistent: it authenticates against the key it names.
    assert anchor_lib.anchor_signature_problem(forged) is None

    code = cli.main(base + ["publish"])

    assert code == 2, "an attacker-signed anchor was accepted as a legacy format"


def test_damage_that_changes_between_the_preflight_and_the_build_is_refused(
    tmp_path, small_store, monkeypatch
):
    """The leaf recheck cannot see this: unreadable files are excluded from
    anchored_leaves by construction. But the verifier reports any change to the
    unreadable set as ANCHOR_MISMATCH, so a damaged file replaced in the window
    between the two scans would be frozen into a new baseline and verify
    cleanly ever after -- laundering exactly the change the verifier exists to
    report."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    damaged = small_store / "2026-08-01" / "Edamaged.json"
    damaged.parent.mkdir(parents=True, exist_ok=True)
    damaged.write_text("{not json", encoding="utf-8")
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0
    assert anchor_lib.unreadable_set(
        json.loads(anchor_path.read_text(encoding="utf-8"))
    ), "the fixture never produced damage to freeze"

    # A legitimate store change, so publish proceeds past the no-op...
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )

    # ...and the damaged file is REPLACED after the preflight passes.
    real_build = cli.anchor_lib.build_anchor

    def rewrite_then_build(root, previous=None, witnesses=None):
        damaged.write_text("{also not json but different", encoding="utf-8")
        return real_build(root, previous, witnesses)

    monkeypatch.setattr(cli.anchor_lib, "build_anchor", rewrite_then_build)

    assert cli.main(base + ["publish"]) == 2


def test_an_unchanged_damage_set_publishes_normally(tmp_path, small_store):
    """The guard must narrow to a CHANGE in the frozen set, not refuse every
    store that carries known damage -- the live store carries three."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    damaged = small_store / "2026-08-01" / "Edamaged.json"
    damaged.parent.mkdir(parents=True, exist_ok=True)
    damaged.write_text("{not json", encoding="utf-8")
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0

    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )

    assert cli.main(base + ["publish"]) == 0


def test_every_branch_of_the_chain_walk_bounds_the_sequence_it_reads(tmp_path):
    """The bound was added to the missing-predecessor branch and not to the
    non-adjacent-predecessor branch beside it, which reaches the same
    range(prior + 1, child) expansion by a different route."""
    from packages.activity_log import provenance as prov

    assert prov._walk_sequence("5") == 5
    assert prov._walk_sequence(str(prov.MAX_SEQUENCE)) == prov.MAX_SEQUENCE
    assert prov._walk_sequence(str(prov.MAX_SEQUENCE + 1)) is None
    assert prov._walk_sequence("1000000000000") is None
    assert prov._walk_sequence("-1") is None
    assert prov._walk_sequence("nonsense") is None
    assert prov._walk_sequence(None) is None


def test_the_walk_has_one_sequence_parser_not_a_guard_per_branch(tmp_path):
    """Structural: every int() over a sequence inside validate_packet should go
    through the bounded parser. A branch that parses its own is the next place
    this defect appears."""
    source = (Path(anchor_lib.__file__).parent / "provenance.py").read_text(
        encoding="utf-8"
    )
    walk = source.split("def validate_packet(", 1)[1]

    assert "int(child_sequence)" not in walk, "a branch parses its own sequence"
    assert 'int(prior_packet.get("s"))' not in walk, "a branch parses its own sequence"
    assert walk.count("_walk_sequence(") >= 3


# ---------------------------------------------------------------------------
# Cold-read findings: publish/verify paths that had the right check elsewhere.
# ---------------------------------------------------------------------------


def test_the_witness_proof_exists_before_the_pointer_that_cites_it(
    tmp_path, small_store, monkeypatch
):
    """A crash between os.replace and the proof write left a published anchor
    claiming a witness with no proof on disk -- which _witness_state reports as
    'the anchor claims a witness but no proof file is present', reading as
    tampering rather than as an interrupted publish."""
    cli = _cli_module()
    from packages.activity_log import witness as witness_lib

    anchor_path = tmp_path / "anchor.json"
    order: list[str] = []
    real_replace = cli.os.replace

    def record(src, dst):
        order.append(f"pointer:{Path(dst).name}")
        return real_replace(src, dst)

    monkeypatch.setattr(cli.os, "replace", record)
    monkeypatch.setattr(
        cli.witness_lib,
        "stamp_root",
        lambda root, timeout=None: {
            "status": "PENDING",
            "digest": "d",
            "attested": ["cal"],
            "proof": b"fake-proof-bytes",
            "failed": [],
        },
    )
    monkeypatch.setattr(
        cli.witness_lib,
        "inspect_proof",
        lambda payload, expected_digest=None: {"status": "PENDING"},
    )

    code = cli.main(
        [
            "--provenance-root",
            str(small_store),
            "--identity-dir",
            str(tmp_path / "id"),
            "--anchor",
            str(anchor_path),
            "publish",
            "--allow-new-identity",
            "--witness",
        ]
    )

    assert code == 0
    proof_name = witness_lib.proof_path(
        tmp_path, json.loads(anchor_path.read_text(encoding="utf-8"))["merkle_root"]
    ).name
    pointer_at = next(i for i, e in enumerate(order) if e == "pointer:anchor.json")
    proof_at = next(i for i, e in enumerate(order) if e == f"pointer:{proof_name}")
    assert proof_at < pointer_at, "the pointer was published before its evidence"


def test_verify_distinguishes_a_corrupt_anchor_from_a_missing_one(
    tmp_path, small_store, capsys
):
    """load_anchor returns None for both. publish was taught the difference and
    verify was not, so a tampered anchor was reported as 'no anchor found'."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    anchor_path.write_text("{not json", encoding="utf-8")

    cli.main(
        [
            "--provenance-root",
            str(small_store),
            "--identity-dir",
            str(tmp_path / "id"),
            "--anchor",
            str(anchor_path),
            "verify",
        ]
    )

    out = json.loads(capsys.readouterr().out)
    assert out["status"] == anchor_lib.ANCHOR_UNAVAILABLE
    assert "could not be read" in out["reason"]
    assert "no anchor found" not in out["reason"]


def test_a_broken_history_does_not_block_anchoring_an_intact_store(
    tmp_path, small_store, capsys
):
    """Deleting one old file in series/ made the series unverifiable, and the
    preflight refused on ANCHOR_UNAVAILABLE -- so an intact store could not be
    anchored without --force. Refusing protects nothing: the ancestor is gone
    and publishing cannot restore it."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )
    assert cli.main(base + ["publish"]) == 0

    # Remove the genesis anchor from the retained series: history now has a hole.
    head = json.loads(anchor_path.read_text(encoding="utf-8"))
    (tmp_path / "series" / f"{head['prev_root']}.json").unlink()
    provenance.create_packet(
        [{"kind": "note", "detail": "third"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )
    capsys.readouterr()

    code = cli.main(base + ["publish"])

    assert code == 0, "an intact store was blocked by a broken ancestor chain"
    assert "retained anchor series is broken" in capsys.readouterr().out


def test_a_missing_series_directory_is_not_reported_as_a_missing_ancestor():
    """'No retained anchor carries that root' is a claim about the store. With
    no directory supplied it is a claim about the caller."""
    anchor = {"merkle_root": "E" + "a" * 43, "prev_root": "E" + "b" * 43}

    result = anchor_lib.walk_series(anchor, {}, series_provided=False)

    assert "no series directory was supplied" in result["problems"][0]
    assert "no retained anchor" not in result["problems"][0]


def test_a_broken_history_still_blocks_when_the_store_actually_lost_something(
    tmp_path, small_store
):
    """The guard must narrow to history-only breaks: a store that LOST an
    anchored leaf stays refused whether or not the series is also broken.

    Drives the real preflight. The first version of this asserted only that the
    fixture committed to some leaves, which is true of the fixture and says
    nothing about the code -- it would have passed against a guard that let
    every loss through.
    """
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    base = [
        "--provenance-root",
        str(small_store),
        "--identity-dir",
        str(tmp_path / "id"),
        "--anchor",
        str(anchor_path),
    ]
    assert cli.main(base + ["publish", "--allow-new-identity"]) == 0
    provenance.create_packet(
        [{"kind": "note", "detail": "second"}],
        identity_dir=tmp_path / "id",
        output_root=small_store,
    )
    assert cli.main(base + ["publish"]) == 0

    # Break the history AND lose an anchored packet.
    head = json.loads(anchor_path.read_text(encoding="utf-8"))
    (tmp_path / "series" / f"{head['prev_root']}.json").unlink()
    sorted(small_store.rglob("*.json"))[0].unlink()

    assert cli.main(base + ["publish"]) == 2, "a real loss was published anyway"


def test_the_upgrade_path_never_overwrites_a_proof_in_place(tmp_path, monkeypatch):
    """witness-upgrade overwrites a VALID pending proof, so a torn write
    destroys a calendar stamp nobody can request again for that instant."""
    cli = _cli_module()
    target = tmp_path / "proof.ots"
    target.write_bytes(b"original-pending-proof")
    written: list[str] = []
    real_write = Path.write_bytes

    def record(self, data):
        written.append(self.name)
        return real_write(self, data)

    monkeypatch.setattr(Path, "write_bytes", record)

    cli._write_atomic(target, b"upgraded-proof")

    assert target.read_bytes() == b"upgraded-proof"
    assert target.name not in written, "final name written directly"


def test_no_writer_of_the_signed_document_precedes_its_proof(
    tmp_path, small_store, monkeypatch
):
    """Two writers persist the signed anchor -- _retain_series and the pointer
    replace -- and moving the proof above only the second still let the RETAINED
    copy cite a proof that did not exist yet."""
    cli = _cli_module()
    anchor_path = tmp_path / "anchor.json"
    order: list[str] = []

    real_atomic = cli._write_atomic
    real_retain = cli._retain_series
    real_replace = cli.os.replace

    monkeypatch.setattr(
        cli, "_write_atomic", lambda p, b: (order.append("proof"), real_atomic(p, b))[1]
    )
    monkeypatch.setattr(
        cli,
        "_retain_series",
        lambda d, r, p: (order.append("retain"), real_retain(d, r, p))[1],
    )
    monkeypatch.setattr(
        cli.os,
        "replace",
        lambda s, d: (
            order.append("pointer") if str(d).endswith("anchor.json") else None,
            real_replace(s, d),
        )[1],
    )
    monkeypatch.setattr(
        cli.witness_lib,
        "stamp_root",
        lambda root, timeout=None: {
            "status": "PENDING",
            "digest": "d",
            "attested": ["cal"],
            "proof": b"fake-proof-bytes",
            "failed": [],
        },
    )
    monkeypatch.setattr(
        cli.witness_lib,
        "inspect_proof",
        lambda payload, expected_digest=None: {"status": "PENDING"},
    )

    assert (
        cli.main(
            [
                "--provenance-root",
                str(small_store),
                "--identity-dir",
                str(tmp_path / "id"),
                "--anchor",
                str(anchor_path),
                "publish",
                "--allow-new-identity",
                "--witness",
            ]
        )
        == 0
    )

    assert order.index("proof") < order.index(
        "retain"
    ), "retained copy cited a proof that did not exist"
    assert order.index("proof") < order.index("pointer")


def test_a_live_holder_keeps_its_lock_however_old_it_is(tmp_path):
    """The intake watcher holds one lock across a recursive scan and thousands
    of writes, which can outlast the 60s a packet write is sized for. Age alone
    let a second watcher DELETE a live holder's lock and enter the same critical
    section -- worse than the abandoned lock the reclamation was added to fix."""
    from packages.activity_log import provenance as prov

    lock_path = tmp_path / ".busy.lock"
    token = prov._acquire_lock(lock_path)
    ancient = time.time() - 86400
    os.utime(lock_path, (ancient, ancient))

    # This process IS the recorded owner, so it is provably alive.
    assert prov._lock_owner_is_alive(lock_path) is True
    with pytest.raises(TimeoutError):
        prov._acquire_lock(lock_path, timeout_seconds=0.2, stale_seconds=1.0)

    prov._release_lock(lock_path, token)
    assert not lock_path.exists()


def test_a_lock_whose_owner_is_gone_is_still_reclaimed(tmp_path):
    """Liveness gates reclamation; it must not disable it."""
    from packages.activity_log import provenance as prov

    lock_path = tmp_path / ".dead.lock"
    # A pid that cannot be running: 0 is never a normal user process here.
    lock_path.write_text("999999999\nsome-token", encoding="utf-8")
    ancient = time.time() - 86400
    os.utime(lock_path, (ancient, ancient))

    token = prov._acquire_lock(lock_path, timeout_seconds=1.0, stale_seconds=1.0)

    assert prov._lock_token(lock_path) == token


def test_a_legacy_lock_without_an_owner_line_reclaims_on_age(tmp_path):
    """Locks written by an older build carry only a token. Treating unknown
    ownership as ALIVE would strand every one of them permanently."""
    from packages.activity_log import provenance as prov

    lock_path = tmp_path / ".legacy.lock"
    lock_path.write_text("token-only", encoding="utf-8")
    ancient = time.time() - 86400
    os.utime(lock_path, (ancient, ancient))

    assert prov._lock_owner_is_alive(lock_path) is None
    token = prov._acquire_lock(lock_path, timeout_seconds=1.0, stale_seconds=1.0)
    assert prov._lock_token(lock_path) == token


def test_a_reused_pid_does_not_keep_a_dead_holders_lock_alive(tmp_path):
    """After a crash the OS reassigns the pid, and a liveness probe then reports
    the holder as running forever -- so the lock is never reclaimed however old
    it is. That is the failure the age window existed to prevent, reintroduced
    by the ownership check added to fix a different one."""
    from packages.activity_log import provenance as prov

    lock_path = tmp_path / ".reused.lock"
    # OUR pid, but a creation token from some other era: the file was written by
    # a process that is gone and whose number has been handed out again.
    lock_path.write_text(
        f"{os.getpid()}\nstart-token-of-a-dead-process\nabandoned-token",
        encoding="utf-8",
    )
    ancient = time.time() - 86400
    os.utime(lock_path, (ancient, ancient))

    assert prov._lock_owner_is_alive(lock_path) is False

    token = prov._acquire_lock(lock_path, timeout_seconds=1.0, stale_seconds=1.0)
    assert prov._lock_token(lock_path) == token


def test_a_live_holder_with_a_matching_start_token_still_keeps_its_lock(tmp_path):
    """The reuse check must not become a way to steal a live lock."""
    from packages.activity_log import provenance as prov

    lock_path = tmp_path / ".mine.lock"
    token = prov._acquire_lock(lock_path)
    ancient = time.time() - 86400
    os.utime(lock_path, (ancient, ancient))

    assert prov._lock_owner_is_alive(lock_path) is True
    with pytest.raises(TimeoutError):
        prov._acquire_lock(lock_path, timeout_seconds=0.2, stale_seconds=1.0)

    prov._release_lock(lock_path, token)


def test_the_lock_token_is_read_from_every_format_this_file_has_had(tmp_path):
    """Three formats now: token only, pid+token, pid+start+token. The token is
    always last, and release compares against it."""
    from packages.activity_log import provenance as prov

    cases = {
        "legacy.lock": ("just-a-token", "just-a-token"),
        "pid.lock": ("4242\nthe-token", "the-token"),
        "full.lock": ("4242\nstart\nthe-token", "the-token"),
    }
    for name, (body, expected) in cases.items():
        path = tmp_path / name
        path.write_text(body, encoding="utf-8")
        assert prov._lock_token(path) == expected, name


# ---------------------------------------------------------------------------
# Reclamation must remove the instance it inspected, not whatever is at the path.
# ---------------------------------------------------------------------------


def test_reclaiming_does_not_delete_a_lock_taken_since_it_was_inspected(tmp_path):
    """Two writers can both judge one abandoned holder dead. The first unlinks
    and takes a fresh lock; the second then unlinks THAT -- and for the
    provenance chain that means two writers inside the sequence critical
    section: duplicate reservations and forked heads."""
    from packages.activity_log import filelock

    lock_path = tmp_path / ".contended.lock"
    lock_path.write_bytes(b"the-abandoned-instance")
    observed = lock_path.read_bytes()

    # The faster reclaimer wins and a NEW holder takes the slot.
    assert filelock.reclaim_if_unchanged(lock_path, observed) is True
    lock_path.write_bytes(b"a-live-new-holder")

    # The slower one arrives with what it inspected a moment ago.
    assert filelock.reclaim_if_unchanged(lock_path, observed) is False
    assert lock_path.read_bytes() == b"a-live-new-holder", "live lock deleted"


def test_only_one_reclaimer_reports_success(tmp_path):
    """The rename is the atomic part: exactly one caller moves a given file
    aside and the rest retry the exclusive create."""
    from packages.activity_log import filelock

    lock_path = tmp_path / ".once.lock"
    lock_path.write_bytes(b"abandoned")
    observed = lock_path.read_bytes()

    outcomes = [filelock.reclaim_if_unchanged(lock_path, observed) for _ in range(3)]

    assert outcomes == [True, False, False]
    assert not lock_path.exists()


def test_reclaiming_leaves_no_quarantine_files_behind(tmp_path):
    from packages.activity_log import filelock

    lock_path = tmp_path / ".tidy.lock"
    lock_path.write_bytes(b"abandoned")

    filelock.reclaim_if_unchanged(lock_path, b"abandoned")

    assert list(tmp_path.iterdir()) == []


def test_a_stale_lock_is_still_reclaimed_end_to_end(tmp_path):
    """Instance-checking must not disable reclamation, which is the whole point
    of the stale path."""
    from packages.activity_log import filelock

    lock_path = tmp_path / ".stale.lock"
    lock_path.write_text("999999999\nstart\nabandoned-token", encoding="utf-8")
    ancient = time.time() - 86400
    os.utime(lock_path, (ancient, ancient))

    token = filelock._acquire_lock(lock_path, timeout_seconds=1.0, stale_seconds=1.0)

    assert filelock._lock_token(lock_path) == token
