"""Tests for CellDirectory — the file-based source chain writer (spec §3.1)."""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.source_chain import cell as cell_module  # noqa: E402
from packages.source_chain.cell import CellDirectory, CellDirectoryError  # noqa: E402

DNA_HASH = "a" * 64  # 64-char hex string simulating a real dna_hash


def make_cell(tmp_dir: str) -> CellDirectory:
    return CellDirectory(base_dir=Path(tmp_dir), dna_hash=DNA_HASH)


def test_append_returns_entry_hash():
    """append_entry() returns a 64-char lowercase hex SHA256 digest."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry(
            entry_type="genesis",
            author_did="did:key:ztest",
            content={"hello": "world"},
        )
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


def test_entry_file_exists_after_append():
    """The entry file is written at cells/<dna_hash>/source_chain/<hash>.json."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("claim", "did:key:ztest", {"foo": "bar"})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        assert entry_path.exists()


def test_entry_file_has_canonical_fields():
    """Entry file contains id, type, author_did, previous_hash, timestamp, content."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("vote", "did:key:ztest", {"weight": 0.999})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        data = json.loads(entry_path.read_bytes())
        assert data["type"] == "vote"
        assert data["author_did"] == "did:key:ztest"
        assert data["content"]["weight"] == 0.999
        assert "id" in data
        assert "timestamp" in data
        assert "previous_hash" in data


def test_first_entry_has_null_previous_hash():
    """Genesis entry has previous_hash=null."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("genesis", "did:key:ztest", {})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        data = json.loads(entry_path.read_bytes())
        assert data["previous_hash"] is None


def test_subsequent_entry_links_to_previous():
    """Each entry's previous_hash is the hash of the immediately prior entry."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h1 = cell.append_entry("genesis", "did:key:ztest", {"n": 1})
        h2 = cell.append_entry("claim", "did:key:ztest", {"n": 2})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h2}.json"
        data = json.loads(entry_path.read_bytes())
        assert data["previous_hash"] == h1


def test_append_reads_head_after_lock_acquisition():
    """append_entry() links to the latest head visible once the lock is held."""
    with tempfile.TemporaryDirectory() as tmp:
        base_dir = Path(tmp)
        seed = CellDirectory(base_dir=base_dir, dna_hash=DNA_HASH)
        genesis_hash = seed.append_entry("genesis", "did:key:ztest", {"n": 1})

        class RaceCell(CellDirectory):
            def __init__(self, base_dir: Path, dna_hash: str) -> None:
                super().__init__(base_dir=base_dir, dna_hash=dna_hash)
                self.injected_hash: str | None = None

            def _acquire_lock(self) -> None:
                if self.injected_hash is None:
                    helper = CellDirectory(base_dir=base_dir, dna_hash=DNA_HASH)
                    self.injected_hash = helper.append_entry(
                        "claim",
                        "did:key:zhelper",
                        {"n": 2},
                    )
                return super()._acquire_lock()

        cell = RaceCell(base_dir=base_dir, dna_hash=DNA_HASH)
        h3 = cell.append_entry("vote", "did:key:ztest", {"n": 3})
        entry_path = base_dir / "cells" / DNA_HASH / "source_chain" / f"{h3}.json"
        data = json.loads(entry_path.read_bytes())
        assert cell.injected_hash is not None
        assert data["previous_hash"] == cell.injected_hash
        assert data["previous_hash"] != genesis_hash


def test_release_lock_only_removes_owned_lock():
    """A non-owner must not be able to delete another writer's lock file."""
    with tempfile.TemporaryDirectory() as tmp:
        owner = make_cell(tmp)
        owner._acquire_lock()

        intruder = make_cell(tmp)
        intruder._lock_token = "not-the-owner"
        intruder._release_lock()

        lock_path = Path(tmp) / "cells" / DNA_HASH / ".lock"
        assert lock_path.exists()

        owner._release_lock()
        assert not lock_path.exists()


def test_acquire_lock_times_out_without_deleting_stale_lock():
    """Waiters should time out rather than force-delete an aged lock file."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        lock_path = Path(tmp) / "cells" / DNA_HASH / ".lock"
        lock_path.write_text("stale-owner", encoding="utf-8")
        stale_at = time.time() - 30
        os.utime(lock_path, (stale_at, stale_at))

        original_timeout = cell_module._LOCK_TIMEOUT
        cell_module._LOCK_TIMEOUT = 0.01
        try:
            try:
                cell._acquire_lock()
                raise AssertionError("Expected CellDirectoryError")
            except CellDirectoryError:
                pass
        finally:
            cell_module._LOCK_TIMEOUT = original_timeout

        assert lock_path.exists()
        assert lock_path.read_text(encoding="utf-8") == "stale-owner"


def test_head_json_updated_after_append():
    """head.json always points to the latest entry hash."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h1 = cell.append_entry("genesis", "did:key:ztest", {})
        h2 = cell.append_entry("claim", "did:key:ztest", {"x": 1})
        head_path = Path(tmp) / "cells" / DNA_HASH / "head.json"
        head_data = json.loads(head_path.read_text())
        assert head_data["head"] == h2
        assert head_data["head"] != h1


def test_head_hash_returns_none_for_empty_chain():
    """head_hash() returns None when the chain has no entries."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        assert cell.head_hash() is None


def test_head_hash_matches_latest():
    """head_hash() returns the hash of the most-recently appended entry."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("genesis", "did:key:ztest", {})
        assert cell.head_hash() == h


def test_read_chain_returns_entries_newest_first():
    """read_chain() returns entries from newest to oldest (reverse chronological)."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        cell.append_entry("genesis", "did:key:ztest", {"n": 1})
        cell.append_entry("claim", "did:key:ztest", {"n": 2})
        cell.append_entry("vote", "did:key:ztest", {"n": 3})
        entries = cell.read_chain(limit=10)
        assert len(entries) == 3
        assert entries[0]["content"]["n"] == 3
        assert entries[1]["content"]["n"] == 2
        assert entries[2]["content"]["n"] == 1


def test_read_chain_respects_limit():
    """read_chain(limit=2) returns only the 2 most recent entries."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        for i in range(5):
            cell.append_entry("memory", "did:key:ztest", {"i": i})
        entries = cell.read_chain(limit=2)
        assert len(entries) == 2
        assert entries[0]["content"]["i"] == 4
        assert entries[1]["content"]["i"] == 3


def test_entry_filename_is_hash_of_raw_bytes():
    """The entry file's stem is the SHA256 of its raw bytes (canonical_serialize output).

    Verified by re-hashing the raw file bytes — NOT by re-parsing through json.loads
    (which would risk float round-trip drift). Raw bytes are the ground truth.
    """
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("claim", "did:key:ztest", {"check": True, "n": 42})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        raw = entry_path.read_bytes()
        recomputed = hashlib.sha256(raw).hexdigest()
        assert recomputed == h


def test_memory_subdirs_created():
    """memory/working, memory/episodic, memory/semantic exist after first append."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        cell.append_entry("genesis", "did:key:ztest", {})
        cell_dir = Path(tmp) / "cells" / DNA_HASH
        assert (cell_dir / "memory" / "working").is_dir()
        assert (cell_dir / "memory" / "episodic").is_dir()
        assert (cell_dir / "memory" / "semantic").is_dir()


def test_entry_filename_is_hash_of_raw_bytes_with_float():
    """Hash-filename invariant holds even when content contains floats."""
    with tempfile.TemporaryDirectory() as tmp:
        cell = make_cell(tmp)
        h = cell.append_entry("vote", "did:key:ztest", {"weight": 0.999})
        entry_path = Path(tmp) / "cells" / DNA_HASH / "source_chain" / f"{h}.json"
        raw = entry_path.read_bytes()
        recomputed = hashlib.sha256(raw).hexdigest()
        assert recomputed == h


# ---------------------------------------------------------------------------
# CLI runner
# ---------------------------------------------------------------------------


def _run_all():
    tests = [
        test_append_returns_entry_hash,
        test_entry_file_exists_after_append,
        test_entry_file_has_canonical_fields,
        test_first_entry_has_null_previous_hash,
        test_subsequent_entry_links_to_previous,
        test_append_reads_head_after_lock_acquisition,
        test_release_lock_only_removes_owned_lock,
        test_acquire_lock_times_out_without_deleting_stale_lock,
        test_head_json_updated_after_append,
        test_head_hash_returns_none_for_empty_chain,
        test_head_hash_matches_latest,
        test_read_chain_returns_entries_newest_first,
        test_read_chain_respects_limit,
        test_entry_filename_is_hash_of_raw_bytes,
        test_memory_subdirs_created,
        test_entry_filename_is_hash_of_raw_bytes_with_float,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL  {t.__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
