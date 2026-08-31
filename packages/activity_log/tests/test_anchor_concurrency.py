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
