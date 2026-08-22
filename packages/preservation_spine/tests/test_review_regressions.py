"""Regressions for PR43 review findings, each reproduced before being fixed.

Every case here was confirmed against the real code or real `git` output first;
none is taken from the review text alone. Where a review claim did not survive
checking, that is recorded at the test rather than silently dropped.
"""

from __future__ import annotations

import subprocess

import pytest

from packages.preservation_spine import github_projection, manifest
from packages.preservation_spine.models import PlaneId

SOURCE_DIGEST = "0" * 64


def _git(repo, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True
    ).stdout


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")
    return root


def _stage_change(repo, name: str) -> None:
    (repo / name).write_text("original\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    (repo / name).write_text("changed\n", encoding="utf-8")
    _git(repo, "add", "-A")


# ---------------------------------------------------------------------------
# Provenance was silently null without --full-index
# ---------------------------------------------------------------------------


def test_abbreviated_index_lines_would_lose_blob_provenance(repo):
    """Documents WHY --full-index is required, by showing the failure.

    Git abbreviates `index` object names to 7 characters by default, and
    `_diff_atoms` only records ids of length 40 or 64. So without the flag every
    ordinary text change captured both blob identities as null -- a preservation
    capsule recording no provenance, which is the one thing it exists to record.
    """
    _stage_change(repo, "plain.txt")

    without = _git(repo, "diff", "--binary", "--cached")
    atom = manifest._diff_atoms(without, PlaneId.LOCAL_INDEX, SOURCE_DIGEST)[0]
    assert atom["blob_before"] is None
    assert atom["blob_after"] is None

    with_flag = _git(repo, "diff", "--binary", "--full-index", "--cached")
    atom = manifest._diff_atoms(with_flag, PlaneId.LOCAL_INDEX, SOURCE_DIGEST)[0]
    assert atom["blob_before"] is not None
    assert atom["blob_after"] is not None
    assert len(atom["blob_after"]) in {40, 64}


def test_capture_asks_for_full_index_on_both_planes():
    """The flag must be on the real capture, not only on this test's commands."""
    source = (
        manifest.__file__.rsplit("manifest.py", 1)[0] + "git_capture.py"
    )
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    assert text.count('"--full-index"') == 2, (
        "both the staged (diff --cached) and unstaged (diff-files) captures "
        "must request full object ids"
    )


# ---------------------------------------------------------------------------
# Paths containing spaces aborted the entire capture
# ---------------------------------------------------------------------------


def test_a_path_with_a_space_parses(repo):
    """Git does NOT quote an ordinary space.

    `diff --git a/a b.txt b/a b.txt` is one valid header with four
    space-separated words. Splitting on every space raised "diff header is
    malformed", and because `capture` calls `inventory_change_universe`
    immediately, the whole capture aborted after leaving a partial state
    directory. Not a corner case: this repository tracks 186 such paths.
    """
    _stage_change(repo, "a b.txt")

    content = _git(repo, "diff", "--binary", "--full-index", "--cached")
    assert b"diff --git a/a b.txt b/a b.txt" in content

    atoms = manifest._diff_atoms(content, PlaneId.LOCAL_INDEX, SOURCE_DIGEST)
    assert [atom["path_after"] for atom in atoms] == ["a b.txt"]
    assert atoms[0]["blob_after"] is not None


def test_a_space_path_does_not_break_the_unified_header(repo):
    """The `---`/`+++` lines gain a trailing TAB when the path has a space.

    The unified format allows `<path>TAB<timestamp>`, and Git emits the tab
    whenever the path would otherwise be ambiguous. Leaving it attached made
    `_safe_manifest_path` reject the path as unsafe, because a tab is not
    printable -- a second, distinct bug in the same area, reachable only for
    paths with spaces.
    """
    _stage_change(repo, "a b.txt")
    content = _git(repo, "diff", "--binary", "--full-index", "--cached")

    assert b"--- a/a b.txt\t" in content, "fixture must actually exercise the tab"
    atoms = manifest._diff_atoms(content, PlaneId.LOCAL_INDEX, SOURCE_DIGEST)
    assert atoms[0]["path_before"] == "a b.txt"


def test_mixed_space_and_plain_paths_in_one_diff(repo):
    (repo / "plain.txt").write_text("original\n", encoding="utf-8")
    (repo / "a b.txt").write_text("original\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    (repo / "plain.txt").write_text("changed\n", encoding="utf-8")
    (repo / "a b.txt").write_text("changed\n", encoding="utf-8")
    _git(repo, "add", "-A")

    content = _git(repo, "diff", "--binary", "--full-index", "--cached")
    atoms = manifest._diff_atoms(content, PlaneId.LOCAL_INDEX, SOURCE_DIGEST)
    assert sorted(atom["path_after"] for atom in atoms) == ["a b.txt", "plain.txt"]
    assert all(atom["blob_after"] is not None for atom in atoms)


# ---------------------------------------------------------------------------
# The all-zero object id is "absent", not a blob
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("width", [40, 64])
def test_all_zero_object_id_is_not_recorded_as_a_blob(width):
    """Git's sentinel for a nonexistent side is the right length, so a length
    check alone accepted forty zeroes as a real blob identity."""
    zeros = "0" * width
    real = "a" * width
    content = (
        b"diff --git a/x.bin b/x.bin\n"
        + f"index {zeros}..{real} 100644\n".encode()
        + b"Binary files /dev/null and b/x.bin differ\n"
    )
    atom = manifest._diff_atoms(content, PlaneId.LOCAL_INDEX, SOURCE_DIGEST)[0]
    assert atom["blob_before"] is None, "the absent side must stay null"
    assert atom["blob_after"] == real


# ---------------------------------------------------------------------------
# Percent-encoding bypassed the mutating-command guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "probe", ["git push", "git %70ush", "git %70%75%73%68", "git PUSH"]
)
def test_mutating_commands_are_rejected_however_they_are_spelled(probe):
    """`_UNSAFE_COMMAND_RE` was matched against the RAW value while every other
    guard inspected the normalized one, and normalization percent-decodes. So
    `git push` was rejected and `git %70ush` was accepted, then rendered into
    the projection as `git push`."""
    with pytest.raises(github_projection.ProjectionValidationError):
        github_projection._sanitize_command(probe)


@pytest.mark.parametrize("probe", ["git status", "git fetch"])
def test_read_only_commands_still_pass(probe):
    """The fix must not reject the commands the projection is for."""
    assert github_projection._sanitize_command(probe) == probe


# ---------------------------------------------------------------------------
# A failed write must not join the sealed universe
# ---------------------------------------------------------------------------


def test_leftover_pending_output_is_not_sealed(tmp_path):
    """`.{name}.pending-{hex}` files are left behind by a FAILED atomic write --
    the docstring says so. They were walked into `checksums.sha256` on the next
    successful seal, becoming authenticated payload that `verify_checksums` then
    required to exist forever."""
    from packages.preservation_spine import seal

    assert seal._is_pending_output(".manifest.json.pending-" + "0" * 32)
    assert not seal._is_pending_output("manifest.json")
    assert not seal._is_pending_output("checksums.sha256")

    root = tmp_path / "capsule"
    root.mkdir()
    (root / "payload.txt").write_text("real\n", encoding="utf-8")
    (root / (".manifest.json.pending-" + "0" * 32)).write_text("x", encoding="utf-8")

    walked = {path.name for path in seal._walk_regular_files(root)}
    assert "payload.txt" in walked
    assert not any(name.startswith(".manifest.json.pending-") for name in walked)


# ---------------------------------------------------------------------------
# A half-written intent must not wedge the checkpoint
# ---------------------------------------------------------------------------


def test_failed_intent_write_leaves_nothing_behind(tmp_path, monkeypatch):
    """Both public entry points call `_recover_pending_append` first, which
    raises on a truncated intent -- so a fragment froze `append_checkpoint` and
    `load_latest_checkpoint` for that path until an operator deleted it."""
    from packages.preservation_spine import checkpoint

    path = tmp_path / "chain.jsonl"
    intent_path = checkpoint._intent_path(path)

    # The intent's own contents are irrelevant here; what matters is that the
    # write fails partway. Stub the payload so the test does not depend on the
    # intent dataclass, then make the write itself blow up.
    monkeypatch.setattr(checkpoint, "_intent_payload", lambda _intent: {"a": 1})

    def boom(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(checkpoint, "_write_exact_descriptor", boom)

    with pytest.raises(OSError):
        checkpoint._write_pending_intent(path, object())

    assert not intent_path.exists(), (
        "a failed intent write must clean up after itself, or the next "
        "append and the next load both fail forever"
    )
