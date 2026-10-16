"""Bounded Windows retry around os.replace.

On Windows, os.replace (MoveFileExW with MOVEFILE_REPLACE_EXISTING) fails with
ERROR_ACCESS_DENIED whenever any other process holds an open handle on the
destination, whatever share mode that handle uses; a handle on the source
without FILE_SHARE_DELETE fails it with ERROR_SHARING_VIOLATION. File watchers
and scanners open freshly written files for well under a millisecond, so a
tight write loop (the per-identity chain state rewritten twice per packet)
loses the race now and then. These tests pin the retry contract: transient
failures are absorbed, persistent ones surface unchanged, POSIX is untouched.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

FLOSS_ROOT = Path(__file__).resolve().parents[3]
if str(FLOSS_ROOT) not in sys.path:
    sys.path.insert(0, str(FLOSS_ROOT))


def _flaky_replace(monkeypatch, module, failures: int | None):
    """Make os.replace raise PermissionError `failures` times, then work.

    `failures=None` fails every call. Returns the list of raised errors and a
    one-element call counter so tests can assert on both.
    """
    real_replace = os.replace
    raised: list[PermissionError] = []
    calls = [0]

    def fake_replace(src, dst):
        calls[0] += 1
        if failures is None or calls[0] <= failures:
            error = PermissionError(13, "Access is denied", str(src))
            raised.append(error)
            raise error
        real_replace(src, dst)

    monkeypatch.setattr(module.os, "replace", fake_replace)
    return raised, calls


def _src_and_dst(tmp_path: Path) -> tuple[Path, Path]:
    src = tmp_path / "state.json.tmp"
    dst = tmp_path / "state.json"
    dst.write_text("old", encoding="utf-8")
    src.write_text("new", encoding="utf-8")
    return src, dst


def test_transient_permission_error_is_retried_then_succeeds(tmp_path, monkeypatch):
    from packages.activity_log import atomic_replace

    monkeypatch.setattr(atomic_replace, "_IS_WINDOWS", True)
    sleeps: list[float] = []
    monkeypatch.setattr(atomic_replace.time, "sleep", sleeps.append)
    _raised, calls = _flaky_replace(monkeypatch, atomic_replace, failures=3)
    src, dst = _src_and_dst(tmp_path)

    atomic_replace.replace_with_retry(src, dst)

    assert dst.read_text(encoding="utf-8") == "new"
    assert not src.exists()
    assert calls[0] == 4
    assert sleeps == list(atomic_replace._RETRY_DELAYS_SECONDS[:3])
    assert sleeps == sorted(sleeps) and sleeps[0] < sleeps[-1], "backoff must grow"


def test_persistent_permission_error_surfaces_after_bounded_attempts(
    tmp_path, monkeypatch
):
    from packages.activity_log import atomic_replace

    monkeypatch.setattr(atomic_replace, "_IS_WINDOWS", True)
    sleeps: list[float] = []
    monkeypatch.setattr(atomic_replace.time, "sleep", sleeps.append)
    raised, calls = _flaky_replace(monkeypatch, atomic_replace, failures=None)
    src, dst = _src_and_dst(tmp_path)

    with pytest.raises(PermissionError) as excinfo:
        atomic_replace.replace_with_retry(src, dst)

    delays = atomic_replace._RETRY_DELAYS_SECONDS
    assert calls[0] == len(delays) + 1
    assert sleeps == list(delays)
    assert sum(delays) < 1.0, "the retry budget is for transient holds only"
    # The final attempt's own error surfaces, not a wrapper and not a success.
    assert excinfo.value is raised[-1]
    assert dst.read_text(encoding="utf-8") == "old"
    assert src.read_text(encoding="utf-8") == "new"


def test_non_permission_error_is_not_retried(tmp_path, monkeypatch):
    from packages.activity_log import atomic_replace

    monkeypatch.setattr(atomic_replace, "_IS_WINDOWS", True)
    sleeps: list[float] = []
    monkeypatch.setattr(atomic_replace.time, "sleep", sleeps.append)

    with pytest.raises(FileNotFoundError):
        atomic_replace.replace_with_retry(
            tmp_path / "missing.tmp", tmp_path / "state.json"
        )

    assert sleeps == []


def test_posix_does_not_retry(tmp_path, monkeypatch):
    from packages.activity_log import atomic_replace

    monkeypatch.setattr(atomic_replace, "_IS_WINDOWS", False)
    sleeps: list[float] = []
    monkeypatch.setattr(atomic_replace.time, "sleep", sleeps.append)
    raised, calls = _flaky_replace(monkeypatch, atomic_replace, failures=1)
    src, dst = _src_and_dst(tmp_path)

    with pytest.raises(PermissionError) as excinfo:
        atomic_replace.replace_with_retry(src, dst)

    assert excinfo.value is raised[0]
    assert calls[0] == 1
    assert sleeps == []


def test_chain_state_write_survives_transient_replace_failure(tmp_path, monkeypatch):
    """The provenance chain-state write is the site the PR41 audit saw fail."""
    from packages.activity_log import atomic_replace, provenance

    monkeypatch.setattr(atomic_replace, "_IS_WINDOWS", True)
    monkeypatch.setattr(atomic_replace.time, "sleep", lambda _seconds: None)
    _raised, calls = _flaky_replace(monkeypatch, atomic_replace, failures=2)
    path = tmp_path / "identity" / "Dagent.chain.json"

    provenance._write_state(path, {"next_sequence": 7, "head": "Ehead"})

    assert provenance._load_state(path) == {"next_sequence": 7, "head": "Ehead"}
    assert calls[0] == 3
