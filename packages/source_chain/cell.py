"""
CellDirectory — file-based source chain for a single Holochain Cell.

Mirrors Holochain source chain primitives exactly (spec §3.1):
  - One directory per Cell (agent × DNA combination)
  - Entries named by SHA256 of their canonical serialization
  - Topological ordering via previous_hash links only (no sequential prefixes)
  - Atomic writes via .lock file using open(path, "x") — O_CREAT|O_EXCL semantics
    on all platforms (Linux, macOS, Windows) without any platform-specific imports

Layout:
    <base_dir>/cells/<dna_hash>/
        head.json                       # {"head": "<latest_entry_hash>"}
        source_chain/<hash>.json        # one file per entry, filename = SHA256
        memory/working/
        memory/episodic/
        memory/semantic/

This is a Phase 0 precursor. When Holochain is live, each file becomes a
source chain action with zero structural rework required.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from packages.orchestrator.serialization import canonical_serialize, entry_hash as _entry_hash


_LOCK_TIMEOUT = 5.0  # seconds before waiters give up and surface a lock timeout


class CellDirectoryError(Exception):
    """Raised for cell-protocol violations (lock timeout, corrupt head, etc.)."""


class CellDirectory:
    """File-based source chain for one agent × DNA Cell.

    Thread-unsafe between OS processes — use append_entry() from a single
    process at a time, or rely on the .lock file for cross-process safety.
    """

    def __init__(self, base_dir: Path, dna_hash: str) -> None:
        self._cell_dir = base_dir / "cells" / dna_hash
        self._chain_dir = self._cell_dir / "source_chain"
        self._head_path = self._cell_dir / "head.json"
        self._lock_path = self._cell_dir / ".lock"
        self._lock_token: Optional[str] = None
        self._ensure_dirs()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def head_hash(self) -> Optional[str]:
        """Return the hash of the most-recently appended entry, or None."""
        if not self._head_path.exists():
            return None
        return json.loads(self._head_path.read_text(encoding="utf-8"))["head"]

    def append_entry(
        self,
        entry_type: str,
        author_did: str,
        content: dict[str, Any],
        previous_hash: Optional[str] = None,
    ) -> str:
        """Append a new entry to the source chain under an exclusive file lock.

        The entry filename is the SHA256 hex digest of the entry's canonical
        serialization. This is the same hash that Holochain uses as the
        action address, ensuring zero rework at migration time.

        Args:
            entry_type: One of "genesis", "claim", "vote", "decision", "memory".
            author_did: The DID of the authoring agent (e.g. "did:key:z...").
            content: Arbitrary JSON-serializable dict.
            previous_hash: Override automatic previous_hash. Use only for genesis
                           entries; omit for all normal appends.

        Returns:
            64-character lowercase hex SHA256 digest (the entry's filename stem).
        """
        self._acquire_lock()
        try:
            prev = previous_hash if previous_hash is not None else self.head_hash()
            entry: dict[str, Any] = {
                "id": str(self._new_uuid()),
                "type": entry_type,
                "author_did": author_did,
                "previous_hash": prev,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "content": content,
            }
            # canonical_serialize produces byte-identical output across Python/Rust/TS.
            # The SHA256 of those bytes IS the filename — no separate hashing step.
            serialized = canonical_serialize(entry)
            h = _entry_hash(entry)
            entry_path = self._chain_dir / f"{h}.json"
            entry_path.write_bytes(serialized)
            self._head_path.write_text(
                json.dumps({"head": h}, separators=(",", ":")),
                encoding="utf-8",
            )
        finally:
            self._release_lock()

        return h

    def read_chain(self, limit: Optional[int] = 50) -> list[dict[str, Any]]:
        """Return source chain entries in reverse-chronological order (newest first).

        Traverses via previous_hash links starting from head. Stops at the
        genesis entry (previous_hash=null) or when `limit` is reached.

        Args:
            limit: Maximum number of entries to return. Pass None to traverse
                the full visible chain from head to genesis.
        """
        head = self.head_hash()
        if head is None:
            return []

        results: list[dict[str, Any]] = []
        current: Optional[str] = head
        while current and (limit is None or len(results) < limit):
            path = self._chain_dir / f"{current}.json"
            if not path.exists():
                break
            data = json.loads(path.read_bytes())
            results.append(data)
            current = data.get("previous_hash")
        return results

    # ------------------------------------------------------------------
    # Lock helpers — cross-platform atomic file creation
    # ------------------------------------------------------------------

    def _acquire_lock(self) -> None:
        """Acquire .lock via atomic open("x") — blocks up to _LOCK_TIMEOUT seconds.

        open(path, "x") maps to O_CREAT|O_EXCL on POSIX and CreateFile with
        CREATE_NEW on Windows. Both raise FileExistsError if the file exists,
        making this genuinely atomic without any platform-specific imports.

        Lock timeout is advisory only: waiters do NOT delete an existing lock
        based solely on age, because a slow but still-live writer is
        indistinguishable from a crashed one without heartbeats. If the timeout
        elapses, callers receive a CellDirectoryError and can decide how to
        recover out-of-band.
        """
        deadline = time.monotonic() + _LOCK_TIMEOUT
        while True:
            try:
                token = str(uuid.uuid4())
                with open(self._lock_path, "x", encoding="utf-8") as fd:
                    fd.write(token)
                self._lock_token = token
                return
            except FileExistsError:
                try:
                    age = time.time() - self._lock_path.stat().st_mtime
                except FileNotFoundError:
                    continue  # another waiter cleared it between our checks
                if time.monotonic() >= deadline:
                    raise CellDirectoryError(
                        f"Timed out acquiring lock on {self._lock_path} after "
                        f"{_LOCK_TIMEOUT}s (existing lock age={age:.1f}s). "
                        "Investigate the holding process before manual cleanup."
                    )
                time.sleep(0.05)

    def _release_lock(self) -> None:
        """Release our .lock file if we still own it."""
        try:
            if self._lock_token is None:
                return
            if self._lock_path.read_text(encoding="utf-8") == self._lock_token:
                self._lock_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass
        finally:
            self._lock_token = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_dirs(self) -> None:
        """Create the cell directory tree on first access."""
        self._chain_dir.mkdir(parents=True, exist_ok=True)
        for sub in ("working", "episodic", "semantic"):
            (self._cell_dir / "memory" / sub).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _new_uuid() -> uuid.UUID:
        """Return a UUID v7 (time-sortable) — uses stdlib uuid7 on Python 3.14+,
        falls back to an inline RFC 9562 §5.7 implementation."""
        uuid7 = getattr(uuid, "uuid7", None)
        if uuid7 is not None:
            return uuid7()
        ts_ms = int(time.time() * 1000) & ((1 << 48) - 1)
        rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
        rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
        v = (ts_ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
        return uuid.UUID(int=v)
