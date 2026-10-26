"""Approved retained-genesis contract; production guards remain active."""

from dataclasses import replace
from pathlib import Path

import pytest

from packages.preservation_spine import checkpoint as cp
from packages.preservation_spine.models import canonical_json_bytes


@pytest.fixture
def first():
    return cp.Checkpoint(
        schema_version="1.0.0",
        sequence=0,
        previous_digest=None,
        state_id="retained-genesis",
        phase="capture-complete",
        input_shas={"remote_main": "1" * 40},
        capsule_root="3" * 64,
        manifest_digest="4" * 64,
        verification_digest=None,
        completed_actions=("captured-six-planes", "sealed-capsule"),
        blockers=("human-review-pending",),
        human_decisions=("preserve-first",),
        next_safe_command="synthetic-no-command",
        recovery_command="synthetic-no-command",
        digest=None,
    )


def pending_state(folder, first, content):
    target = folder / "checkpoints.jsonl"
    if content is not None:
        target.write_bytes(content)
        (folder / "initial-target.preimage").write_bytes(content)
    cp._write_pending_intent(target, cp._build_intent(target, b"", first))
    intent = cp._intent_path(target)
    (folder / "initial-intent.preimage").write_bytes(intent.read_bytes())
    return target, intent


def forbid_cleanup(monkeypatch, *paths):
    protected = {Path(p).resolve() for p in paths}
    original = cp.os.unlink

    def guarded(path, *args, **kwargs):
        if Path(path).resolve() in protected:
            raise AssertionError("automatic recovery cleanup was attempted")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(cp.os, "unlink", guarded)


@pytest.mark.parametrize("operation", ["load", "append"])
@pytest.mark.parametrize("state", ["missing", "empty", "partial"])
def test_incomplete_genesis_retains_target_and_intent(
    tmp_path, monkeypatch, first, operation, state
):
    content = (
        None
        if state == "missing"
        else b"" if state == "empty" else canonical_json_bytes(first)[:30]
    )
    target, intent = pending_state(tmp_path, first, content)
    before_intent = intent.read_bytes()
    forbid_cleanup(monkeypatch, target, intent)

    with pytest.raises(cp.CheckpointIntegrityError, match="deferred"):
        if operation == "load":
            cp.load_latest_checkpoint(target)
        else:
            cp.append_checkpoint(target, first)

    assert intent.read_bytes() == before_intent
    assert target.exists() == (content is not None)
    if content is not None:
        assert target.read_bytes() == content


def test_normal_public_append_and_load_still_work(tmp_path, first):
    target = tmp_path / "normal.jsonl"
    cp.append_checkpoint(target, first)
    second = replace(first, sequence=1, previous_digest=first.digest, digest=None)
    cp.append_checkpoint(target, second)
    assert cp.load_latest_checkpoint(target) == second


def test_complete_genesis_intent_reconciles_without_target_rewrite(tmp_path, first):
    content = canonical_json_bytes(first)
    target, intent = pending_state(tmp_path, first, content)
    assert cp.load_latest_checkpoint(target) == first
    assert target.read_bytes() == content
    assert not intent.exists()


def test_mature_prefix_partial_recovery_contract_is_unchanged(tmp_path, first):
    target = tmp_path / "mature.jsonl"
    prefix = canonical_json_bytes(first)
    second = replace(first, sequence=1, previous_digest=first.digest, digest=None)
    before = prefix + canonical_json_bytes(second)[:30]
    target.write_bytes(before)
    (tmp_path / "initial-target.preimage").write_bytes(before)
    cp._write_pending_intent(target, cp._build_intent(target, prefix, second))
    assert cp.load_latest_checkpoint(target) == first
    assert target.read_bytes() == prefix
    assert not cp._intent_path(target).exists()


def test_unauthenticated_genesis_tail_is_retained(tmp_path, monkeypatch, first):
    content = b"foreign unauthenticated bytes"
    target, intent = pending_state(tmp_path, first, content)
    before = intent.read_bytes()
    forbid_cleanup(monkeypatch, target, intent)
    with pytest.raises(cp.CheckpointIntegrityError, match="unauthenticated"):
        cp.load_latest_checkpoint(target)
    assert target.read_bytes() == content
    assert intent.read_bytes() == before


def test_legacy_target_cleanup_entrypoint_defers(tmp_path, monkeypatch):
    target = tmp_path / "legacy-empty.jsonl"
    target.write_bytes(b"")
    forbid_cleanup(monkeypatch, target)
    with cp._locked_directory(tmp_path):
        with pytest.raises(cp.CheckpointIntegrityError, match="deferred"):
            cp._remove_empty_checkpoint_file(target)
    assert target.read_bytes() == b""


def test_public_late_append_never_loses_its_record(tmp_path, monkeypatch, first):
    target, intent = pending_state(tmp_path, first, b"")
    original_intent = intent.read_bytes()
    original_remove = cp._remove_empty_checkpoint_file
    original_validate = cp._validated_file_state
    original_unlink = cp.os.unlink
    state = dict(depth=0, injected=False, committed=False)

    def removal_scope(path):
        state["depth"] += 1
        try:
            return original_remove(path)
        finally:
            state["depth"] -= 1

    def validate_then_append(path):
        metadata = original_validate(path)
        if (
            Path(path) == target
            and state["depth"] == 1
            and metadata.st_size == 0
            and not state["injected"]
        ):
            state["injected"] = True
            cp.append_checkpoint(target, first)
            assert cp.load_latest_checkpoint(target) == first
            state["committed"] = True
            (tmp_path / "committed-record.preimage").write_bytes(target.read_bytes())
        return metadata

    def deny_late_record_unlink(path, *args, **kwargs):
        if Path(path) == target and state["committed"]:
            raise AssertionError(
                "outer public loader attempted to unlink a valid public append"
            )
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(cp, "_remove_empty_checkpoint_file", removal_scope)
    monkeypatch.setattr(cp, "_validated_file_state", validate_then_append)
    monkeypatch.setattr(cp.os, "unlink", deny_late_record_unlink)
    with pytest.raises(cp.CheckpointIntegrityError, match="deferred"):
        cp.load_latest_checkpoint(target)

    # A repair may eliminate the scheduling window entirely. In that case it
    # must retain the original state; otherwise the actual committed record wins.
    if state["committed"]:
        assert cp.load_latest_checkpoint(target) == first
    else:
        assert target.read_bytes() == b""
        assert intent.read_bytes() == original_intent
