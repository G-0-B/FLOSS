"""RED tests for evidence-ref resolution.

Production change that would make these fail: a ref outside the room root
resolving, a bare string guessed into a file or commit, `resolved` reported
while any ref is unresolved, a file's digest written into the shared log, or
one post's lookups running past their time budget.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_THIS_DIR = Path(__file__).parent
_REPO_ROOT = _THIS_DIR.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from packages.coordination_room import evidence  # noqa: E402
from packages.coordination_room.evidence import resolve_all, resolve_ref  # noqa: E402


def test_no_refs_is_none(tmp_path: Path):
    assert resolve_all(tmp_path, None) == ("none", [])
    assert resolve_all(tmp_path, []) == ("none", [])


def test_file_ref_inside_root_resolves_and_publishes_no_digest(tmp_path: Path):
    """A hash of an untracked file, a `.env` for one, would put a fingerprint
    of it into a log every agent reads. Existence is all a file ref records."""
    (tmp_path / ".env").write_bytes(b"TOKEN=hunter2")
    status, checked = resolve_all(tmp_path, ["file:.env"])
    assert status == "resolved"
    assert checked == [{"ref": "file:.env", "kind": "file", "ok": True}]


def test_missing_file_is_unresolved(tmp_path: Path):
    status, checked = resolve_all(tmp_path, ["file:nope.md"])
    assert status == "unresolved"
    assert checked == [{"ref": "file:nope.md", "kind": "file", "ok": False}]


def test_file_outside_root_is_unresolved_even_if_it_exists(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    assert resolve_ref(root, "file:../outside.txt")["ok"] is False


def test_directory_is_not_a_file(tmp_path: Path):
    (tmp_path / "d").mkdir()
    assert resolve_ref(tmp_path, "file:d")["ok"] is False


def test_bare_ref_is_unknown_and_unresolved(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    row = resolve_ref(tmp_path, "a.md")
    assert row == {"ref": "a.md", "kind": "unknown", "ok": False}


def test_one_bad_ref_makes_the_set_unresolved(tmp_path: Path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    status, checked = resolve_all(tmp_path, ["file:a.md", "file:nope.md"])
    assert status == "unresolved"
    assert [c["ok"] for c in checked] == [True, False]


@pytest.mark.parametrize(
    "refs",
    ["file:a.md", [""], [3], ["x"] * 17, ["x" * 513]],
    ids=["not-a-list", "empty-string", "not-a-string", "too-many", "too-long"],
)
def test_malformed_refs_raise(tmp_path: Path, refs):
    with pytest.raises(ValueError):
        resolve_all(tmp_path, refs)


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_commit_ref_resolves_only_real_commits_and_pins_the_full_oid(tmp_path: Path):
    git = ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run([*git, "init", "-q"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    sha = subprocess.run(
        [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    assert resolve_ref(tmp_path, f"commit:{sha}") == {
        "ref": f"commit:{sha}",
        "kind": "commit",
        "ok": True,
        "oid": sha,
    }
    # A short sha is stored with the full object id it named at lookup time.
    assert resolve_ref(tmp_path, f"commit:{sha[:7]}")["oid"] == sha
    # git accepts upper-case hex; so does the room.
    assert resolve_ref(tmp_path, f"commit:{sha.upper()}")["oid"] == sha
    missing = resolve_ref(tmp_path, "commit:" + "0" * 40)
    assert missing == {"ref": "commit:" + "0" * 40, "kind": "commit", "ok": False}
    # Not hex: never reaches git, so it cannot be read as an option.
    assert resolve_ref(tmp_path, "commit:--help")["ok"] is False


def test_a_slow_commit_lookup_is_unresolved_not_an_error(tmp_path: Path, monkeypatch):
    def too_slow(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="git", timeout=kwargs["timeout"])

    monkeypatch.setattr(evidence.subprocess, "run", too_slow)
    assert resolve_ref(tmp_path, "commit:" + "a" * 40) == {
        "ref": "commit:" + "a" * 40,
        "kind": "commit",
        "ok": False,
    }


def test_lookups_past_the_budget_are_skipped_not_waited_for(tmp_path: Path, monkeypatch):
    """Sixteen commit refs at the per-ref timeout would hold a caller for half
    a minute. Once the post's budget is spent, the rest are recorded unresolved
    without asking git at all; a file check costs nothing and still runs."""
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    calls = []
    monkeypatch.setattr(evidence, "LOOKUP_BUDGET_SECONDS", 0.0)
    monkeypatch.setattr(evidence.subprocess, "run", lambda *a, **k: calls.append(a) or 1 / 0)
    status, checked = resolve_all(tmp_path, ["commit:" + "a" * 40, "file:a.md"])
    assert calls == []
    assert status == "unresolved"
    assert [c["ok"] for c in checked] == [False, True]
