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
import sys
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
