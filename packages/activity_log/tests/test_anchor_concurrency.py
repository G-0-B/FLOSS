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


def test_a_store_under_constant_write_pressure_still_produces_an_anchor(
    tmp_path, monkeypatch
):
    """Never settling must degrade to a real point-in-time set, not an exception."""
    calls = {"n": 0}

    def never_settles(root):
        calls["n"] += 1
        said = "E" + str(calls["n"]).rjust(43, "z")
        return [anchor_lib.PacketLeaf("D" + "a" * 43, 0, said)], []

    monkeypatch.setattr(anchor_lib, "scan_packets", never_settles)

    leaves, unreadable = anchor_lib._stable_scan(tmp_path)

    assert len(leaves) == 1
    assert calls["n"] == 3, "bounded; a busy store must not spin"


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
